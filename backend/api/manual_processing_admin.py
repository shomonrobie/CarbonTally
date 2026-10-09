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

from fastapi import APIRouter, Depends, HTTPException, Query, Request
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
    COVERAGE_SELECTED_CLIENTS,
    SCOPE_PRECEDENCE,
    SCOPE_TYPES,
    CapacityExceededError,
    DuplicateActiveAllocationError,
    OrgContext,
    combine_entitlement,
    is_scope_type_valid,
)
from services.manual_processing_routing import ManualProcessingRouter

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


class ProcessorUpsert(BaseModel):
    """Assign/change the configured Processing Entity for one scope."""

    scope_type: str = Field(..., min_length=1)
    scope_id: str = Field(..., min_length=1)
    processing_entity_id: str = Field(..., min_length=1)
    active: bool = True
    reason: Optional[str] = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


async def require_manual_processing_admin(
    context: StaffContext = Depends(require_staff),
) -> StaffContext:
    """CarbonTally Admin: internal staff + the admin-grade permission."""
    require_internal_staff(context)
    ensure_staff_permission(context, ADMIN_PERMISSION)
    return context


async def _scope_entitlement(
    repos: RepositoryBundle, *, scope_type: str, scope_id: str
) -> dict:
    """Subscription entitlement of every organisation covered by one scope.

    The FIRST gate (PO decision): an organisation must be subscribed to a plan
    that includes Manual Processing. Entitlement is resolved server-side from the
    EXISTING commercial model (active subscription -> plan) — never from the
    request, so it cannot be spoofed and stale governance cannot bypass it.
    """
    organizations = await repos.manual_processing.organizations_in_scope(
        scope_type=scope_type, scope_id=scope_id
    )
    router = ManualProcessingRouter(repos)
    entitled: list[str] = []
    not_entitled: list[str] = []
    plan_codes: dict[str, Optional[str]] = {}
    for organization_id in organizations:
        decision = await router.entitlement_for(organization_id)
        plan_codes[organization_id] = decision.plan_code
        (entitled if decision.entitled else not_entitled).append(organization_id)
    return {
        "organizations": organizations,
        "entitled": bool(organizations) and not not_entitled,
        "organizations_entitled": entitled,
        "organizations_not_entitled": not_entitled,
        "plan_codes": plan_codes,
    }


async def _scope_context(
    repos: RepositoryBundle,
    *,
    scope_type: str,
    scope_id: str,
    organizations: list[str],
) -> OrgContext:
    """Resolve the REAL relationship context for one governance scope.

    CT-MP-SUB-003 (F-6 fix): a consultant scope's ``scope_id`` is a firm
    (``consultant_profiles.id``) or a relationship-grant id
    (``consultant_clients.id``) — NOT an organisation id. Using it as
    ``organization_id`` gave the governance resolver a wrong context. This maps
    the scope onto the real entities so most-specific-wins is evaluated correctly.
    """
    if scope_type == "organization":
        return OrgContext(organization_id=scope_id)
    if scope_type == "consultant_client":
        client = await repos.consultants.get_client(scope_id)
        if client is not None:
            return OrgContext(
                organization_id=str(client.organization_id),
                consultant_client_id=scope_id,
                consultant_firm_id=str(client.consultant_id),
            )
    # consultant_firm (or an unresolvable consultant_client): the firm scope
    # applies to its covered organisations.
    return OrgContext(
        organization_id=(organizations[0] if organizations else scope_id),
        consultant_firm_id=scope_id,
    )


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

    # SUBSCRIPTION IS THE FIRST GATE (PO decision). Enabling Manual Processing
    # for a scope whose organisations are not entitled is refused up front, so an
    # invalid grant cannot be created in the first place. (Entitlement is also
    # enforced at every read/route time, so a pre-existing/stale grant can never
    # bypass the rule.)
    if payload.enabled:
        entitlement = await _scope_entitlement(
            repos, scope_type=payload.scope_type, scope_id=payload.scope_id
        )
        if not entitlement["entitled"]:
            blocked = (
                entitlement["organizations_not_entitled"]
                or entitlement["organizations"]
            )
            await _audit(
                repos,
                action="manual_processing:grant_rejected_not_entitled",
                scope_type=payload.scope_type,
                scope_id=payload.scope_id,
                actor=context.profile.user_id,
                details={
                    "reason": "subscription does not include Manual Processing",
                    "organizations": entitlement["organizations"],
                    "organizations_not_entitled": blocked,
                },
                correlation_id=_request_id(request),
            )
            detail = (
                "Manual Processing requires the customer's subscribed plan to "
                "include it. Not entitled: " + ", ".join(blocked)
                if blocked
                else "No organisations are covered by this scope."
            )
            raise HTTPException(status_code=409, detail=detail)

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


@router.get("/state")
async def manual_processing_state(
    scope_type: str,
    scope_id: str,
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """The complete Manual Processing state for one scope (Admin control plane).

    Shows, without any frontend-supplied truth: the subscription entitlement of
    the covered organisations, the FIN-06 governance state (with the deciding
    scope level), the configured processor (both at THIS scope and the
    most-specific effective one), and the resulting effective answer. This is
    the same server-side decision routing uses.
    """
    if not is_scope_type_valid(scope_type):
        raise HTTPException(
            status_code=422, detail=f"scope_type must be one of {list(SCOPE_TYPES)}"
        )
    entitlement = await _scope_entitlement(
        repos, scope_type=scope_type, scope_id=scope_id
    )
    organizations = entitlement["organizations"]
    # CT-MP-SUB-003 (F-6): for a consultant scope the scope id is NOT an
    # organisation id, so the governance context is resolved from the REAL
    # relationship entities rather than reusing scope_id as an organisation.
    context = await _scope_context(
        repos, scope_type=scope_type, scope_id=scope_id, organizations=organizations
    )
    governance = await repos.manual_processing.effective_for_context(context)
    scope_processor = await repos.manual_processing.get_processor(
        scope_type=scope_type, scope_id=scope_id
    )
    router = ManualProcessingRouter(repos)
    routing = await router.resolve(organizations[0]) if organizations else None
    return {
        "scope_type": scope_type,
        "scope_id": scope_id,
        "organizations": organizations,
        "context": {
            "organization_id": context.organization_id,
            "consultant_client_id": context.consultant_client_id,
            "consultant_firm_id": context.consultant_firm_id,
        },
        "entitlement": {
            "entitled": entitlement["entitled"],
            "organizations_entitled": entitlement["organizations_entitled"],
            "organizations_not_entitled": entitlement["organizations_not_entitled"],
            "plan_codes": entitlement["plan_codes"],
        },
        "governance": {
            "enabled": governance.enabled,
            "source_level": governance.source_level,
            "source_scope_type": governance.source_scope_type,
            "source_scope_id": governance.source_scope_id,
            "default_off": governance.default_off,
        },
        "scope_processor": (
            {
                "processing_entity_id": scope_processor.processing_entity_id,
                "active": scope_processor.active,
                "reason": scope_processor.reason,
            }
            if scope_processor is not None
            else None
        ),
        "effective": (
            {
                "entitled": routing.entitled,
                "enabled": routing.enabled,
                "effective": routing.effective,
                "configured": routing.configured,
                "processing_entity_id": routing.processing_entity_id,
                "outcome": routing.outcome,
                "plan_code": routing.plan_code,
                "entitlement_source": routing.entitlement_source,
                "processor_scope_type": routing.processor_scope_type,
                "processor_scope_id": routing.processor_scope_id,
            }
            if routing is not None
            else None
        ),
        "precedence": list(SCOPE_PRECEDENCE),
    }


@router.get("/processors")
async def list_processors(
    scope_type: Optional[str] = None,
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """List the configured Manual Processing processors (admin only)."""
    if scope_type is not None and not is_scope_type_valid(scope_type):
        raise HTTPException(
            status_code=422, detail=f"scope_type must be one of {list(SCOPE_TYPES)}"
        )
    processors = await repos.manual_processing.list_processors(scope_type=scope_type)
    return {
        "processors": [
            {
                "scope_type": p.scope_type,
                "scope_id": p.scope_id,
                "processing_entity_id": p.processing_entity_id,
                "active": p.active,
                "reason": p.reason,
                "set_by": p.set_by,
                "set_at": p.set_at,
            }
            for p in processors
        ],
        "total": len(processors),
        "precedence": list(SCOPE_PRECEDENCE),
    }


@router.put("/processors")
async def upsert_processor(
    payload: ProcessorUpsert,
    request: Request,
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Assign/change the configured Processing Entity for one scope (admin only).

    Requires the applicable customer to be SUBSCRIPTION-ENTITLED (PO decision):
    a processor cannot be configured for a customer whose plan does not include
    Manual Processing. The Processing Entity must exist and be ACTIVE. Configuring
    a processor does NOT enable Manual Processing — enablement stays the separate
    governance decision.
    """
    if not is_scope_type_valid(payload.scope_type):
        raise HTTPException(
            status_code=422,
            detail=f"scope_type must be one of {list(SCOPE_TYPES)}",
        )
    entitlement = await _scope_entitlement(
        repos, scope_type=payload.scope_type, scope_id=payload.scope_id
    )
    if not entitlement["entitled"]:
        blocked = (
            entitlement["organizations_not_entitled"] or entitlement["organizations"]
        )
        await _audit(
            repos,
            action="manual_processing:processor_rejected_not_entitled",
            scope_type=payload.scope_type,
            scope_id=payload.scope_id,
            actor=context.profile.user_id,
            details={
                "processing_entity_id": payload.processing_entity_id,
                "organizations_not_entitled": blocked,
            },
            correlation_id=_request_id(request),
        )
        raise HTTPException(
            status_code=409,
            detail=(
                "A processor can only be configured for a customer whose "
                "subscribed plan includes Manual Processing."
            ),
        )

    entity = await repos.entities.get(payload.processing_entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="processing entity not found")
    if str(getattr(entity, "status", "")) != "active":
        raise HTTPException(status_code=409, detail="processing entity is not active")

    processor = await repos.manual_processing.set_processor(
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        processing_entity_id=payload.processing_entity_id,
        active=payload.active,
        reason=payload.reason,
        actor_id=context.profile.user_id,
    )
    await _audit(
        repos,
        action="manual_processing:processor_set",
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        actor=context.profile.user_id,
        details={
            "processing_entity_id": processor.processing_entity_id,
            "active": processor.active,
            "reason": payload.reason,
            "organizations": entitlement["organizations"],
        },
        correlation_id=_request_id(request),
    )
    return {
        "processor": {
            "scope_type": processor.scope_type,
            "scope_id": processor.scope_id,
            "processing_entity_id": processor.processing_entity_id,
            "active": processor.active,
            "reason": processor.reason,
            "set_by": processor.set_by,
            "set_at": processor.set_at,
        }
    }


@router.delete("/processors/{scope_type}/{scope_id}")
async def delete_processor(
    scope_type: str,
    scope_id: str,
    request: Request,
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Remove a scope's processor configuration (no destination => no routing)."""
    if not is_scope_type_valid(scope_type):
        raise HTTPException(
            status_code=422, detail=f"scope_type must be one of {list(SCOPE_TYPES)}"
        )
    removed = await repos.manual_processing.delete_processor(
        scope_type=scope_type, scope_id=scope_id
    )
    await _audit(
        repos,
        action="manual_processing:processor_removed",
        scope_type=scope_type,
        scope_id=scope_id,
        actor=context.profile.user_id,
        details={"removed": removed, "routing": "no_destination_configured"},
        correlation_id=_request_id(request),
    )
    return {"removed": removed}


# ===========================================================================
# CT-MP-SUB-003 — consultant-sponsored coverage + allocation control plane
# ===========================================================================
#
# The COMMERCIAL coverage (mode + selected capacity) is expressed by the
# consultant FIRM's own organisation subscription plan
# (features.consultant_manual_processing) and is configured through the existing
# Admin plan-management APIs — no parallel coverage/plan system exists. These
# endpoints expose the resulting state and manage the SELECTED-CLIENTS
# allocations. Admin authorization is the same FIN-06 admin gate.

class AllocationUpsert(BaseModel):
    """Allocate one eligible consultant client under selected-capacity coverage."""

    consultant_id: str = Field(..., min_length=1)
    organization_id: str = Field(..., min_length=1)
    reason: Optional[str] = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


@router.get("/coverage/{consultant_id}")
async def consultant_coverage(
    consultant_id: str,
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """The purchased coverage + allocation state for one consultant firm (admin)."""
    profile = await repos.consultants.get_profile_by_id(consultant_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="consultant not found")
    state = await ManualProcessingRouter(repos).coverage_state_for_firm(consultant_id)
    # F-11/NV-9 — resolve every referenced organisation name in ONE batched
    # lookup so the Admin UI can label clients by name instead of raw ids.
    referenced = set(state["eligible_clients"]) | {
        a["organization_id"] for a in state["allocations"]
    }
    names: dict = {}
    if referenced:
        orgs = await repos.organizations.get_many(sorted(referenced))
        names = {oid: getattr(orgs.get(oid), "name", None) for oid in referenced}
    return {
        "consultant_id": consultant_id,
        "company_name": getattr(profile, "company_name", None),
        "coverage": state,
        "client_names": names,
    }


@router.post("/coverage/allocations")
async def allocate_client(
    payload: AllocationUpsert,
    request: Request,
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Allocate one eligible client under SELECTED_CLIENTS coverage (admin only).

    Enforced server-side (never from the frontend):
      * the consultant firm must exist;
      * the firm must have ENABLED purchased coverage;
      * the coverage mode must be SELECTED_CLIENTS;
      * the firm must not be at capacity;
      * the target organisation must be an ACTIVE client of THIS firm
        (a forged/stale organisation id can never be allocated).
    """
    profile = await repos.consultants.get_profile_by_id(payload.consultant_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="consultant not found")

    router = ManualProcessingRouter(repos)
    state = await router.coverage_state_for_firm(payload.consultant_id)
    if not state["enabled"]:
        raise HTTPException(
            status_code=409,
            detail="This consultant has no purchased Manual Processing coverage.",
        )
    if state["mode"] != COVERAGE_SELECTED_CLIENTS:
        raise HTTPException(
            status_code=409,
            detail=(
                "Client allocations apply only to SELECTED_CLIENTS coverage; "
                "this consultant is on ALL_ELIGIBLE_CLIENTS."
            ),
        )
    available = state["available"]
    if available is not None and available <= 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "Consultant selected-client capacity is exhausted. Release an "
                "existing allocation or increase purchased capacity."
            ),
        )

    grant = await repos.consultants.get_client_by_org(
        payload.consultant_id, payload.organization_id
    )
    if grant is None or str(getattr(grant, "status", "") or "") != "active":
        raise HTTPException(
            status_code=403,
            detail=(
                "The organisation is not an eligible (active) client of this "
                "consultant; capacity cannot be allocated to it."
            ),
        )

    try:
        allocation = await repos.manual_processing.create_allocation(
            consultant_id=payload.consultant_id,
            consultant_client_id=str(grant.id),
            organization_id=payload.organization_id,
            reason=payload.reason,
            actor_id=context.profile.user_id,
            capacity=state["capacity"],
        )
    except DuplicateActiveAllocationError as exc:
        # F-7 — ONLY the expected duplicate refusal maps to 409.
        raise HTTPException(
            status_code=409,
            detail="The organisation already holds an active allocation from this consultant.",
        ) from exc
    except CapacityExceededError as exc:
        # F-9 — capacity was consumed by a concurrent request under the lock.
        raise HTTPException(
            status_code=409,
            detail=(
                "Consultant selected-client capacity is exhausted. Release an "
                "existing allocation or increase purchased capacity."
            ),
        ) from exc
    # Any other failure is a genuine server error and propagates unchanged (F-7).
    await _audit(
        repos,
        action="manual_processing:allocation_created",
        scope_type="consultant_firm",
        scope_id=payload.consultant_id,
        actor=context.profile.user_id,
        details={
            "organization_id": payload.organization_id,
            "consultant_client_id": str(grant.id),
            "allocation_id": allocation.id,
            "reason": payload.reason,
        },
        correlation_id=_request_id(request),
    )
    refreshed = await router.coverage_state_for_firm(payload.consultant_id)
    return {
        "allocation": {
            "id": allocation.id,
            "consultant_id": allocation.consultant_id,
            "organization_id": allocation.organization_id,
            "state": allocation.state,
            "allocated_at": allocation.allocated_at,
            "reason": allocation.reason,
        },
        "coverage": refreshed,
    }


@router.delete("/coverage/allocations/{allocation_id}")
async def release_client(
    allocation_id: str,
    request: Request,
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Release one active allocation (returns its capacity unit) — admin only."""
    released = await repos.manual_processing.release_allocation(
        allocation_id=allocation_id,
        reason=None,
        actor_id=context.profile.user_id,
    )
    if released is None:
        raise HTTPException(status_code=404, detail="active allocation not found")
    await _audit(
        repos,
        action="manual_processing:allocation_released",
        scope_type="consultant_firm",
        scope_id=released.consultant_id,
        actor=context.profile.user_id,
        details={
            "allocation_id": released.id,
            "organization_id": released.organization_id,
            "released_at": released.released_at,
        },
        correlation_id=_request_id(request),
    )
    return {
        "released": {
            "id": released.id,
            "consultant_id": released.consultant_id,
            "organization_id": released.organization_id,
            "state": released.state,
            "released_at": released.released_at,
        }
    }


@router.get("/clients/{organization_id}")
async def client_manual_processing_entitlement(
    organization_id: str,
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """The FULL Manual Processing commercial + operational state for one client.

    Deliberately does NOT collapse the concepts (PO spec §20): direct entitlement,
    consultant-sponsored entitlement, the consultant relationship, allocation
    state, FIN-06 governance, the configured PE and the resulting effective
    operational state are all reported separately.
    """
    router = ManualProcessingRouter(repos)
    direct = await router.direct_entitlement_for(organization_id)
    sponsored = await router.sponsored_entitlement_for(organization_id)
    combined = combine_entitlement(direct, sponsored)
    org_context = await repos.manual_processing.org_context_for_organization(
        organization_id
    )
    governance = await repos.manual_processing.effective_for_context(org_context)
    routing = await router.resolve(organization_id)
    return {
        "organization_id": organization_id,
        "direct": {
            "entitled": direct.entitled,
            "source": direct.source,
            "plan_code": direct.plan_code,
        },
        "sponsored": (
            {
                "entitled": sponsored.entitled,
                "firm_id": sponsored.firm_id,
                "mode": sponsored.mode,
                "reason": sponsored.reason,
                "allocated": sponsored.allocated,
                "available": sponsored.available,
                "over_allocated": sponsored.over_allocated,
            }
            if sponsored is not None
            else None
        ),
        "effective_entitlement": {
            "entitled": combined.entitled,
            "source": combined.source,
            "sponsored_mode": combined.sponsored_mode,
            "sponsored_reason": combined.sponsored_reason,
        },
        "relationship": {
            "consultant_client_id": org_context.consultant_client_id,
            "consultant_firm_id": org_context.consultant_firm_id,
        },
        "governance": {
            "enabled": governance.enabled,
            "source_level": governance.source_level,
            "source_scope_type": governance.source_scope_type,
            "source_scope_id": governance.source_scope_id,
        },
        "effective": {
            "entitled": routing.entitled,
            "enabled": routing.enabled,
            "effective": routing.effective,
            "configured": routing.configured,
            "processing_entity_id": routing.processing_entity_id,
            "outcome": routing.outcome,
            "entitlement_source": routing.entitlement_source,
        },
    }


@router.get("/organizations")
async def search_organizations(
    q: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    context: StaffContext = Depends(require_manual_processing_admin),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Searchable client-organisation lookup for the Manual Processing control plane.

    F-11 — operators must not have to type raw organisation UUIDs. This is a
    READ-ONLY, bounded, name-searchable lookup that reuses the EXISTING
    ``organizations.search`` repository method (CL-63) and the EXISTING Manual
    Processing admin gate (internal CarbonTally staff + ``can_manage_organizations``).

    No new authorization model, no schema change, no mutation: SELECTING a
    result performs no state change (the caller must issue a separate,
    server-validated action). Tenant scope is irrelevant here because the gate
    is the CarbonTally-internal admin control plane, not a customer surface.
    """
    rows, total = await repos.organizations.search(
        q=q, limit=limit, offset=offset, active_only=False
    )
    return {
        "organizations": [
            {
                "id": o.id,
                "name": o.name,
                "country": o.country,
                "is_active": o.is_active,
            }
            for o in rows
        ],
        "total": total,
        "limit": max(1, min(50, int(limit))),
        "offset": max(0, int(offset)),
        "q": q or "",
    }


