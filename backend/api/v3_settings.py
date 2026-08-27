"""V3 platform settings surface (N3 — configurable retention).

Retention is a CONFIGURABLE platform capability. The settings below are the
platform-wide retention policy (the RC2 ``system_settings`` columns). Only
CarbonTally internal staff with admin authority may read/write them.

No retention duration is invented here: unset values are returned as ``None``
and the UI renders "Not configured". Enforcement is a server-side concern —
this surface is configuration only.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    RepositoryBundle,
    get_repositories,
)
from auth import AuthUser, require_admin
from pydantic import BaseModel

router = APIRouter(prefix="/api/v3/settings", tags=["V3 — Platform Settings"])


class RetentionUpdate(BaseModel):
    audit_log_retention_days: Optional[int] = None
    data_retention_days: Optional[int] = None
    document_retention_days: Optional[int] = None
    backup_retention_days: Optional[int] = None


@router.get("/retention")
async def get_retention_settings(
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Return the configured platform retention policy (N3). Unset values are
    ``None`` — the UI must not invent durations."""
    return {"settings": await repos.settings.get_retention()}


@router.put("/retention")
async def update_retention_settings(
    payload: RetentionUpdate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Persist the configurable retention policy (server-side enforcement
    remains the platform's responsibility)."""
    for field in ("audit_log_retention_days", "data_retention_days",
                  "document_retention_days", "backup_retention_days"):
        value = getattr(payload, field)
        if value is not None and value < 0:
            raise HTTPException(
                status_code=422,
                detail=f"{field} must be a non-negative number of days",
            )
    return {
        "settings": await repos.settings.update_retention(
            audit_log_retention_days=payload.audit_log_retention_days,
            data_retention_days=payload.data_retention_days,
            document_retention_days=payload.document_retention_days,
            backup_retention_days=payload.backup_retention_days,
            updated_by=current_user.user_id,
        )
    }
