# backend/routes/waitlist.py
"""
Public waitlist endpoints.

CT-FINAL-03 (package 09 §5.3): ``waitlist`` carries prospect PII (name,
company, size, interests, email) and is now fail-closed — RLS enabled with ZERO
policies
(``supabase/migrations/20261028000000_ct_final_03_rls_security_remediation.sql``).
The browser no longer reads or writes the table directly:

* ``POST /api/waitlist/`` — the public landing-page signup (was a direct
  ``anon`` insert from ``frontend/src/BetaSignup.jsx``). Unauthenticated by
  design: a waitlist signup is a public action. The write is performed
  server-side with the ``service_role`` client.
* ``GET /api/waitlist/`` — the admin listing (was a direct authenticated read
  from ``admin/src/pages/admin/BetaManagement.js``), now behind
  ``require_admin()``.

The Flask-side ``/api/waitlist/invite`` flow used by the beta admin page is
unchanged; it is not a waitlist-table path.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone

from auth import AuthUser, require_admin
from database import get_supabase_client

router = APIRouter(prefix="/api/waitlist", tags=["Waitlist"])


class WaitlistRequest(BaseModel):
    email: EmailStr
    full_name: str | None = None
    company_name: str | None = None
    company_size: str | None = None
    interested_in: str | None = None
    source: str = "landing_page"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/")
async def add_to_waitlist(request: WaitlistRequest):
    """Add a prospect to the waitlist (public signup; server-side write)."""
    try:
        supabase = get_supabase_client()
        email = str(request.email).strip().lower()

        supabase.from_("waitlist").upsert(
            {
                "email": email,
                "full_name": request.full_name,
                "company_name": request.company_name,
                "company_size": request.company_size,
                "interested_in": request.interested_in,
                "source": request.source,
                "status": "pending",
                "updated_at": _now(),
            },
            on_conflict="email",
        ).execute()

        return {"success": True, "message": "Added to the waitlist"}
    except Exception as e:  # noqa: BLE001 - surfaced as a controlled API error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add to the waitlist: {str(e)}",
        )


@router.get("/")
async def get_waitlist(
    current_user: AuthUser = Depends(require_admin()),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List waitlist prospects (admin only)."""
    try:
        supabase = get_supabase_client()

        query = supabase.from_("waitlist").select("*", count="exact")
        if status_filter:
            query = query.eq("status", status_filter)
        if search:
            pattern = f"%{search}%"
            query = query.or_(
                f"email.ilike.{pattern},company_name.ilike.{pattern}"
            )

        result = (
            query.order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        return {
            "success": True,
            "data": result.data or [],
            "total": len(result.data or []),
        }
    except Exception as e:  # noqa: BLE001 - surfaced as a controlled API error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get the waitlist: {str(e)}",
        )
