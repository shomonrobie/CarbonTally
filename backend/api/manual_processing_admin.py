"""FIN-06 — CarbonTally Admin Manual Processing governance API.

ONLY CarbonTally Admin may read or change the governance plane. The gate is
enforced server-side (internal staff profile + the admin-grade
``can_manage_organizations`` permission) — never in the frontend. Every change is
recorded through the existing append-only audit infrastructure
(``repos.audit.record``, ``public.audit_logs``); no parallel audit system exists.

Disabling a scope also INVALIDATES queued work for the affected organisations
(batches whose status is ``open``): running batches (``in_progress``) are left
alone so an actively running job finishes safely, and no historical or completed
work is ever resurrected.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from api.dependencies import RepositoryBundle, get_repositories
from api.operations_auth import (
    StaffContext,
    ensure_staff_permission,
    require_internal_staff,
    require_staff,
)
from domain.audit import AuditEntry
from domain.manual_processing import (
    SCOPE_PRECEDENCE,
    SCOPE_TYPES,
    OrgContext,
    is_scope_type_valid,
)

router = APIRouter(
    prefix="/api/v3/admin/manual-processing",
    tags=["V3 — Admin: Manual Processing Governance (FIN-06)"],
)

#: The admin-grade permission that authorises the governance plane. This is an
#: EXISTING staff permission (no new permission vocabulary is invented); a
#: dedicated ``can_manage_manual_processing`` permission would be a PO decision.
ADMIN_PERMISSION = "can_manage_organizations"


class GrantUpsert(BaseModel):
    scope_type: str = Field(..., min_length=1)
    scope_id: str = Field(..., min_length=1)
    enabled: bool
    reason: Optional[str] = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


async def require_manual_processing_admin(
    context: StaffContext = Depends(require_staff),
) -> StaffContext:
    """CarbonTally Admin: internal staff + the admin-grade permission."""
    require_internal_staff(context)
    ensure_staff_permission(context, ADMIN_PERMISSION)
    return context


def _request_id(request: Request) -> Optional[str]:
    return request.headers.get("x-request-id") or request.headers.get("x-correlation-id")


@router.get("/grants")
async def list_grants(
    scope_type: Optional[str] = None,
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """List explicit governance rows (admin only)."""
    if scope_type is not None and not is_scope_type_valid(scope_type):
        raise HTTPException(
            status_code=422, detail=f"scope_type must be one of {list(SCOPE_TYPES)}"
        )
    grants = await repos.manual_processing.list_grants(scope_type=scope_type)
    return {
        "grants": [
            {
                "scope_type": g.scope_type,
                "scope_id": g.scope_id,
                "enabled": g.enabled,
                "reason": g.reason,
                "set_by": g.set_by,
                "set_at": g.set_at,
            }
            for g in grants
        ],
        "total": len(grants),
        "precedence": list(SCOPE_PRECEDENCE),
        "default": {"enabled": False, "source_level": "default"},
    }


@router.get("/effective/{organization_id}")
async def effective_for_organization(
    organization_id: str,
    consultant_client_id: Optional[str] = None,
    consultant_firm_id: Optional[str] = None,
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Admin diagnostic: the effective value + which scope level decided it."""
    effective = await repos.manual_processing.effective_for_context(
        OrgContext(
            organization_id=organization_id,
            consultant_client_id=consultant_client_id,
            consultant_firm_id=consultant_firm_id,
        )
    )
    return {
        "organization_id": organization_id,
        "enabled": effective.enabled,
        "source_level": effective.source_level,
        "source_scope_type": effective.source_scope_type,
        "source_scope_id": effective.source_scope_id,
        "default_off": effective.default_off,
    }


async def _audit(
    repos,
    *,
    action: str,
    scope_type: str,
    scope_id: str,
    actor: str,
    details: dict,
    correlation_id: Optional[str] = None,
) -> None:
    """Record one governance change through the EXISTING audit infrastructure."""
    await repos.audit.record(
        AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=correlation_id or scope_id,
            entity_type="manual_processing_grant",
            entity_id=scope_id,
            action=action,
            actor=actor,
            occurred_at=datetime.now(timezone.utc),
            changed_fields={"scope_type": scope_type, **details},
            ip_address=None,
        )
    )


@router.put("/grants")
async def upsert_grant(
    payload: GrantUpsert,
    request: Request,
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Enable/disable Manual Processing for exactly one scope (admin only).

    Precedence is most-specific-wins, so an explicit value on a specific scope
    overrides a broader grant. Disabling also invalidates QUEUED (``open``)
    manual batches for the affected organisations; running batches continue.
    """
    if not is_scope_type_valid(payload.scope_type):
        raise HTTPException(
            status_code=422, detail=f"scope_type must be one of {list(SCOPE_TYPES)}"
        )

    previous = next(
        (
            g
            for g in await repos.manual_processing.list_grants(
                scope_type=payload.scope_type
            )
            if g.scope_id == payload.scope_id
        ),
        None,
    )

    grant = await repos.manual_processing.set_grant(
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        enabled=payload.enabled,
        reason=payload.reason,
        actor_id=context.profile.user_id,
    )

    cancelled: list[str] = []
    if not payload.enabled:
        organizations = await repos.manual_processing.organizations_in_scope(
            scope_type=payload.scope_type, scope_id=payload.scope_id
        )
        queued = await repos.manual_processing.queued_batch_ids_for_organizations(
            organizations
        )
        for batch_id in queued:
            await repos.manual_extraction.cancel_batch(
                batch_id, context.profile.user_id
            )
            cancelled.append(batch_id)
        if cancelled:
            await _audit(
                repos,
                action="manual_processing:queued_batches_cancelled",
                scope_type=payload.scope_type,
                scope_id=payload.scope_id,
                actor=context.profile.user_id,
                details={
                    "cancelled_batches": cancelled,
                    "organizations": organizations,
                    "running_jobs_left_to_finish": True,
                },
                correlation_id=_request_id(request),
            )

    await _audit(
        repos,
        action="manual_processing:grant_set",
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        actor=context.profile.user_id,
        details={
            "previous_enabled": None if previous is None else previous.enabled,
            "new_enabled": grant.enabled,
            "source_level": "explicit",
            "reason": payload.reason,
            "cancelled_batches": cancelled,
        },
        correlation_id=_request_id(request),
    )

    return {
        "grant": {
            "scope_type": grant.scope_type,
            "scope_id": grant.scope_id,
            "enabled": grant.enabled,
            "reason": grant.reason,
            "set_by": grant.set_by,
            "set_at": grant.set_at,
        },
        "previous": {
            "enabled": None if previous is None else previous.enabled,
            "source_level": "explicit" if previous is not None else "default",
        },
        "cancelled_batches": cancelled,
        "running_jobs_left_to_finish": True,
    }


@router.delete("/grants/{scope_type}/{scope_id}")
async def delete_grant(
    scope_type: str,
    scope_id: str,
    request: Request,
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Remove an explicit governance row (the scope falls back to inheritance)."""
    if not is_scope_type_valid(scope_type):
        raise HTTPException(
            status_code=422, detail=f"scope_type must be one of {list(SCOPE_TYPES)}"
        )
    removed = await repos.manual_processing.delete_grant(
        scope_type=scope_type, scope_id=scope_id
    )
    await _audit(
        repos,
        action="manual_processing:grant_removed",
        scope_type=scope_type,
        scope_id=scope_id,
        actor=context.profile.user_id,
        details={"removed": removed, "falls_back_to": "inherited_or_default_deny"},
        correlation_id=_request_id(request),
    )
    return {"removed": removed}
