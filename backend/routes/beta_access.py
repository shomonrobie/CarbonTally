# backend/routes/beta_access.py
"""Self-service beta-access endpoints — CT-FINAL-03 (R-3, package 09 §4.2).

The legacy browser flow read and wrote ``beta_access_codes`` and ``beta_users``
directly through PostgREST. Both tables are now fail-closed — RLS enabled with
ZERO policies —
(``supabase/migrations/20261028000000_ct_final_03_rls_security_remediation.sql``),
so the flow is served here instead, with the authenticated **session** as the
only source of identity:

* no client-supplied email, user id or ``access_level`` is accepted, which is
  what removes the self-grant path package 09 §4.2 recorded (any authenticated
  user could previously insert/update their own ``beta_users`` row);
* a beta code is only redeemable by the address it was issued to;
* every write is performed server-side with the ``service_role`` client.

Endpoints
---------
``GET  /api/beta/me``      — is the signed-in caller a provisioned beta user?
``POST /api/beta/redeem``  — redeem a beta code: mark it used, provision the
                             caller's own ``beta_users`` row and activate their
                             ``waitlist`` entry.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from auth import AuthUser, require_auth
from database import get_supabase_client

router = APIRouter(prefix="/api/beta", tags=["Beta Access"])

#: The access level the legacy self-service signup granted. It is a server-side
#: constant here: the browser cannot choose its own access level any more.
BETA_ACCESS_LEVEL = "beta"


class RedeemRequest(BaseModel):
    beta_code: str = Field(min_length=1, max_length=128)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _caller_email(user: AuthUser) -> str:
    """The caller's verified session email (lower-cased) — never a client value."""
    email = (user.email or "").strip().lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The signed-in principal has no email address",
        )
    return email


def _as_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@router.get("/me")
async def get_beta_status(current_user: AuthUser = Depends(require_auth())):
    """Report whether the *caller's own* email is a provisioned beta user.

    Replaces the two legacy direct ``beta_users.select('email')`` reads in
    ``frontend/src/BetaLogin.jsx``. The lookup is server-side and keyed to the
    session email, so it cannot be used to enumerate the beta access list.
    """
    supabase = get_supabase_client()
    email = _caller_email(current_user)

    result = (
        supabase.from_("beta_users")
        .select("email, access_level")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    row = (result.data or [None])[0]

    return {
        "success": True,
        "is_beta_user": row is not None,
        "access_level": (row or {}).get("access_level"),
    }


@router.post("/redeem")
async def redeem_beta_code(
    payload: RedeemRequest,
    current_user: AuthUser = Depends(require_auth()),
):
    """Redeem a beta code for the signed-in caller (server-authoritative).

    Replaces the legacy ``BetaSignup.jsx`` writes (mark code used, insert the
    ``beta_users`` row, activate the ``waitlist`` entry). All three mutations
    are keyed to the verified session email; the ``user_id`` written is the
    caller's own session subject.
    """
    supabase = get_supabase_client()
    email = _caller_email(current_user)
    code = payload.beta_code.strip()

    result = (
        supabase.from_("beta_access_codes")
        .select("*")
        .eq("code", code)
        .limit(1)
        .execute()
    )
    code_row = (result.data or [None])[0]
    if not code_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid beta access code")

    code_status = (code_row.get("status") or "").lower()
    if code_status == "used":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This beta code has already been used")
    if code_status in ("expired", "revoked"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"This beta code is {code_status}")

    expires_at = _as_datetime(code_row.get("expires_at"))
    if expires_at is not None and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This beta code has expired")

    issued_to = (code_row.get("email") or "").strip().lower()
    if issued_to and issued_to != email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This beta access code was issued to a different email address",
        )

    now = _now()
    supabase.from_("beta_users").upsert(
        {
            "user_id": current_user.user_id,
            "email": email,
            "beta_code": code,
            "access_level": BETA_ACCESS_LEVEL,
            "last_active_at": now,
            "updated_at": now,
        },
        on_conflict="email",
    ).execute()

    supabase.from_("beta_access_codes").update(
        {"status": "used", "used_at": now, "updated_at": now}
    ).eq("id", code_row["id"]).execute()

    supabase.from_("waitlist").update(
        {"status": "active", "activated_at": now, "updated_at": now}
    ).eq("email", email).execute()

    return {"success": True, "provisioned": True, "access_level": BETA_ACCESS_LEVEL}
