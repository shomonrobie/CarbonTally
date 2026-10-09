"""CT-MP-SUB-004 — Manual Processing coverage surfaces (Customer / Consultant).

These endpoints EXPOSE the already-approved CT-PO-MP-SUB-003 commercial model to
the two audiences the PO-approved UI/UX specification
(``docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md``)
defines:

* Customer  — the caller's OWN organisation effective entitlement (org-scoped);
* Consultant — the caller's OWN firm purchased coverage + selected-client
  allocations (never another firm's data);
* Platform Admin — the full commercial + operational control plane, which
  already exists in ``api/manual_processing_admin.py`` (unchanged here).

No commercial rule, pricing, capacity tier, payment provider, persona or
parallel subscription table is introduced. Entitlement / eligibility / capacity
are decided by the SAME CT-MP-SUB-003 domain rules and the SAME repository
methods the Admin control plane and the automatic router use — these endpoints
only project (and, for ``SELECTED_CLIENTS``, mutate through the existing
``consultant_mp_allocations`` repository methods) that server-authoritative
state, scoped to the authenticated caller.

Authorization reuses the EXISTING chains (no new model):

* customer reads  → ``require_org_member()`` (exact-tenant path enforcement);
* consultant reads → ``require_consultant`` (active firm membership);
* consultant writes → ``require_consultant`` + the existing ``can_manage_clients``
  capability flag (the closest existing "manage my client portfolio" surface;
  no new permission is invented).

The browser is never authoritative: the consultant firm id and the customer
organisation id are resolved server-side, and every capacity/eligibility rule is
re-checked here before a write.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from api.consultant_auth import (
    ConsultantContext,
    ensure_consultant_permission,
    require_consultant,
)
from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, require_org_member
from domain.audit import AuditEntry
from domain.manual_processing import (
    COVERAGE_SELECTED_CLIENTS,
    CapacityExceededError,
    DuplicateActiveAllocationError,
)
from services.manual_processing_routing import ManualProcessingRouter

router = APIRouter(
    prefix="/api/v3",
    tags=["V3 — Manual Processing Coverage (CT-MP-SUB-003)"],
)


class AllocationRequest(BaseModel):
    """Allocate one eligible client to a firm's SELECTED_CLIENTS coverage."""

    organization_id: str = Field(..., min_length=1)
    reason: Optional[str] = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


def _request_id(request: Request) -> Optional[str]:
    return request.headers.get("x-request-id") or request.headers.get("x-correlation-id")


async def _audit(
    repos: RepositoryBundle,
    *,
    action: str,
    scope_id: str,
    actor: str,
    details: dict,
    correlation_id: Optional[str] = None,
) -> None:
    """Record one allocation change through the EXISTING audit infrastructure."""
    await repos.audit.record(
        AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=correlation_id or scope_id,
            entity_type="consultant_mp_allocation",
            entity_id=scope_id,
            action=action,
            actor=actor,
            occurred_at=datetime.now(timezone.utc),
            changed_fields=details,
            ip_address=None,
        )
    )


async def _names_by_id(repos: RepositoryBundle, organization_ids: list) -> dict:
    """Resolve organisation names in ONE query (NV-9 — no N+1 lookup).

    A missing/hidden organisation resolves to ``None`` (never a fabricated
    name), and a lookup failure is swallowed: a display name is never fatal to
    the coverage response.
    """
    ids = list(dict.fromkeys(str(i) for i in organization_ids if i))
    if not ids:
        return {}
    try:
        orgs = await repos.organizations.get_many(ids)
    except Exception:  # pragma: no cover - defensive: a name is never fatal
        return {}
    return {oid: getattr(orgs.get(oid), "name", None) for oid in ids}


# ---------------------------------------------------------------------------
# Customer — the caller's OWN organisation effective entitlement
# ---------------------------------------------------------------------------


@router.get("/organizations/{organization_id}/manual-processing")
async def customer_manual_processing(
    organization_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """The customer-visible Manual Processing service state for one organisation.

    ``require_org_member()`` enforces the exact-tenant path scope (F-05-R1), so a
    customer can only ever read their own organisation; the id is re-validated
    server-side and is never trusted from the browser.

    The response deliberately separates the commercial entitlement from the
    operational state (PO UI/UX §10) and exposes ONLY what a customer is
    authorised to see: it never reveals the consultant's purchased capacity,
    allocation counts, other clients, allocation ids or internal routing ids.
    """
    mp = ManualProcessingRouter(repos)
    combined = await mp.entitlement_for(organization_id)
    context = await repos.manual_processing.org_context_for_organization(organization_id)
    governance = await repos.manual_processing.effective_for_context(context)
    routing = await mp.resolve(organization_id)

    consultant_name: Optional[str] = None
    if combined.sponsored_entitled and combined.sponsored_firm_id:
        profile = await repos.consultants.get_profile_by_id(combined.sponsored_firm_id)
        consultant_name = getattr(profile, "company_name", None) if profile else None

    sources = [
        name
        for name, on in (
            ("direct", bool(combined.direct_entitled)),
            ("sponsored", bool(combined.sponsored_entitled)),
        )
        if on
    ]
    return {
        "organization_id": organization_id,
        "status": "available" if combined.entitled else "not_included",
        "coverage_sources": sources,
        "direct_entitled": bool(combined.direct_entitled),
        "sponsored_entitled": bool(combined.sponsored_entitled),
        "effective_entitled": bool(combined.entitled),
        # Authorised only because the caller IS the sponsored client org.
        "consultant": (
            {"company_name": consultant_name} if combined.sponsored_entitled else None
        ),
        "processing_mode": "manual" if combined.entitled else None,
        "governance": {"enabled": bool(governance.enabled)},
        "processing_entity": {
            "configured": bool(routing.configured),
            "processing_entity_id": (
                routing.processing_entity_id if routing.configured else None
            ),
        },
        # A commercially-entitled but not-yet-configured org must NOT read as
        # "not subscribed" (PO UI/UX §10).
        "operational_status": (
            "configured" if routing.configured else "not_yet_configured"
        ),
        "effective": {
            "enabled": bool(routing.enabled),
            "effective": bool(routing.effective),
            "outcome": routing.outcome,
        },
    }


# ---------------------------------------------------------------------------
# Consultant — the caller's OWN firm coverage (never another firm)
# ---------------------------------------------------------------------------


async def _consultant_coverage_payload(
    repos: RepositoryBundle, firm_id: str, company_name: Optional[str]
) -> dict:
    """The firm-scoped coverage projection shared by read + write responses."""
    state = await ManualProcessingRouter(repos).coverage_state_for_firm(firm_id)
    covered_ids = [
        a["organization_id"] for a in state["allocations"] if a["state"] == "active"
    ]
    # NV-9 — ONE batched name lookup for every referenced organisation (no N+1).
    all_org_ids = (
        list(state["eligible_clients"])
        + list(state["unallocated_eligible_clients"])
        + [a["organization_id"] for a in state["allocations"]]
    )
    names = await _names_by_id(repos, all_org_ids)
    allocations = []
    for a in state["allocations"]:
        allocations.append(
            {
                "id": a["id"],
                "organization_id": a["organization_id"],
                "name": names.get(str(a["organization_id"])),
                "state": a["state"],
                "reason": a["reason"],
                "allocated_at": a["allocated_at"],
                "released_at": a["released_at"],
            }
        )
    def _pair(ids: list) -> list:
        return [
            {"organization_id": oid, "name": names.get(str(oid))} for oid in ids
        ]

    return {
        "consultant_id": firm_id,
        "company_name": company_name,
        "enabled": state["enabled"],
        "mode": state["mode"],
        "capacity": state["capacity"],
        "allocated": state["allocated"],
        "available": state["available"],
        "over_allocated": state["over_allocated"],
        "plan_code": state["plan_code"],
        "plan_version": state["plan_version"],
        "eligible_clients": _pair(state["eligible_clients"]),
        "unallocated_eligible_clients": _pair(state["unallocated_eligible_clients"]),
        "covered_clients": _pair(covered_ids),
        "allocations": allocations,
    }


@router.get("/consultants/me/manual-processing/coverage")
async def consultant_manual_processing_coverage(
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """The caller's OWN firm Manual Processing coverage + allocations.

    The firm id is resolved from the authenticated consultant context
    (``require_consultant``) — never from the request — so a consultant can only
    ever see their own firm's purchased coverage, capacity and clients.
    """
    firm_id = str(context.firm_member.firm_id)
    return await _consultant_coverage_payload(
        repos, firm_id, getattr(context.profile, "company_name", None)
    )



@router.post("/consultants/me/manual-processing/allocations")
async def consultant_allocate_client(
    payload: AllocationRequest,
    request: Request,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Allocate one eligible client under the caller's firm SELECTED_CLIENTS coverage.

    Server-enforced (never the frontend) and scoped to the caller's OWN firm:
      * the firm must have ENABLED purchased coverage;
      * the coverage mode must be SELECTED_CLIENTS;
      * the firm must not be at capacity;
      * the target organisation must be an ACTIVE client of THIS firm
        (a forged/stale organisation id can never be allocated).
    """
    ensure_consultant_permission(context, "manage_clients")
    firm_id = str(context.firm_member.firm_id)
    actor = getattr(context.profile, "user_id", None) or firm_id

    mp = ManualProcessingRouter(repos)
    state = await mp.coverage_state_for_firm(firm_id)
    if not state["enabled"]:
        raise HTTPException(
            status_code=409,
            detail="Your firm has no purchased Manual Processing coverage.",
        )
    if state["mode"] != COVERAGE_SELECTED_CLIENTS:
        raise HTTPException(
            status_code=409,
            detail=(
                "Client allocations apply only to SELECTED_CLIENTS coverage; "
                "your firm is on ALL_ELIGIBLE_CLIENTS."
            ),
        )
    available = state["available"]
    if available is not None and available <= 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "Selected-client capacity is exhausted. Release an existing "
                "allocation or increase purchased capacity."
            ),
        )

    grant = await repos.consultants.get_client_by_org(firm_id, payload.organization_id)
    if grant is None or str(getattr(grant, "status", "") or "") != "active":
        raise HTTPException(
            status_code=403,
            detail=(
                "The organisation is not an eligible (active) client of your "
                "firm; capacity cannot be allocated to it."
            ),
        )

    try:
        allocation = await repos.manual_processing.create_allocation(
            consultant_id=firm_id,
            consultant_client_id=str(grant.id),
            organization_id=payload.organization_id,
            reason=payload.reason,
            actor_id=actor,
            capacity=state["capacity"],
        )
    except DuplicateActiveAllocationError as exc:
        # F-7 — ONLY the expected duplicate-active-allocation refusal is a 409.
        raise HTTPException(
            status_code=409,
            detail="This client already has an active sponsored coverage allocation.",
        ) from exc
    except CapacityExceededError as exc:
        # F-9 — capacity was consumed by a concurrent request under the lock.
        raise HTTPException(
            status_code=409,
            detail=(
                "Selected-client capacity is exhausted. Release an existing "
                "allocation or increase purchased capacity."
            ),
        ) from exc
    # Any other failure is a genuine server error: it propagates unchanged (500)
    # and is never reported to the consultant as a duplicate allocation (F-7).

    await _audit(
        repos,
        action="manual_processing:allocation_created",
        scope_id=firm_id,
        actor=actor,
        details={
            "allocation_id": allocation.id,
            "organization_id": payload.organization_id,
            "consultant_client_id": str(grant.id),
            "reason": payload.reason,
            "via": "consultant",
        },
        correlation_id=_request_id(request),
    )
    coverage = await _consultant_coverage_payload(
        repos, firm_id, getattr(context.profile, "company_name", None)
    )
    return {
        "allocation": {
            "id": allocation.id,
            "organization_id": allocation.organization_id,
            "state": allocation.state,
            "allocated_at": allocation.allocated_at,
            "reason": allocation.reason,
        },
        "coverage": coverage,
    }


@router.delete("/consultants/me/manual-processing/allocations/{allocation_id}")
async def consultant_release_client(
    allocation_id: str,
    request: Request,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Release one ACTIVE allocation belonging to the caller's OWN firm.

    The allocation is re-read against the caller's firm's own allocations, so a
    cross-firm allocation id is denied (never silently released).
    """
    ensure_consultant_permission(context, "manage_clients")
    firm_id = str(context.firm_member.firm_id)
    actor = getattr(context.profile, "user_id", None) or firm_id

    firm_allocations = await repos.manual_processing.list_allocations(
        consultant_id=firm_id, state="active"
    )
    match = next((a for a in firm_allocations if a.id == allocation_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="active allocation not found")

    released = await repos.manual_processing.release_allocation(
        allocation_id=allocation_id, reason=None, actor_id=actor
    )
    if released is None:
        raise HTTPException(status_code=404, detail="active allocation not found")

    await _audit(
        repos,
        action="manual_processing:allocation_released",
        scope_id=firm_id,
        actor=actor,
        details={
            "allocation_id": released.id,
            "organization_id": released.organization_id,
            "released_at": released.released_at,
            "via": "consultant",
        },
        correlation_id=_request_id(request),
    )
    coverage = await _consultant_coverage_payload(
        repos, firm_id, getattr(context.profile, "company_name", None)
    )
    return {
        "released": {
            "id": released.id,
            "organization_id": released.organization_id,
            "state": released.state,
            "released_at": released.released_at,
        },
        "coverage": coverage,
    }

