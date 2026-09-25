"""P17 accounting-context API (IMPLEMENT-02).

Task: ``P17-IMPLEMENT-02-20260925-API-ACTING-FOR-WRITE-PATHS``.

Exposes the minimum useful surface to exercise the P17 CAMS backend:

* the effective **accounting context** (who is acting, for which organisation, and
  what entitles them to);
* the actor's **authorized organisations** (own + active consultant delegations);
* **selecting/switching** the acting-for organisation (validated server-side);
* **resolving accounting dimensions** for an input (validation only — this task
  implements NO Scope 2 / Scope 3 calculation);
* **persisting acting-for attribution** on a record, and reading it back;
* the Scope 3 **reference vocabulary**.

Authorisation is never taken from the request. ``acting_for_organization_id`` is a
REQUEST that must match an organisation the actor is entitled to; the
data-owning organisation of an attributed record is the authority the actor must
satisfy. Every persisted attribution is written from the server-resolved context
and recorded in the existing audit ledger.

Errors reuse the existing API envelope: the P17 domain errors
(``AccountingDimensionError``, ``BoundaryAmbiguityError``,
``Scope3CategoryNotSupportedError``, ``ActingForError``, ...) already declare
their own ``code``/``http_status`` and are translated by ``api.router`` with no
special casing here.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from api.audit_helpers import record_acting_for_attribution
from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, get_current_user
from data.accounting_context import ACTING_FOR_CARRIERS
from domain.cams import describe_dimensions, resolve_accounting_dimensions
from api.accounting_context_auth import (
    ensure_record_owner_authorized,
    list_authorized_organizations,
    resolve_accounting_context,
)

router = APIRouter(prefix="/api/v3/accounting", tags=["V3 — Accounting Context"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class ActingForSelection(BaseModel):
    """Select the organisation the actor intends to operate for."""

    acting_for_organization_id: str = Field(min_length=1)


class DimensionResolutionRequest(BaseModel):
    """The CAMS dimensions to resolve for one accounting input.

    ``acting_for_organization_id`` selects the organisation the input belongs to
    and is authorised server-side; every other field is an accounting dimension
    validated by the unified engine.
    """

    scope: str = Field(min_length=1)
    acting_for_organization_id: Optional[str] = None
    scope2_method: Optional[str] = None
    scope3_category: Optional[int] = None
    energy_type: Optional[str] = None
    data_quality: Optional[str] = None
    facility_id: Optional[str] = None
    transport_boundary: Optional[str] = None
    waste_origin: Optional[str] = None
    source_snapshot_id: Optional[str] = None


class ActingForAttributionRequest(BaseModel):
    """Persist acting-for attribution on one existing record.

    Deliberately carries NO attribution values: the actor and acting-for
    organisations are resolved server-side from the record's owner, so a client
    cannot forge the persisted attribution by supplying it.
    """

    carrier: str = Field(min_length=1)
    record_id: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# A. Current / effective accounting context
# ---------------------------------------------------------------------------
@router.get("/context")
async def get_accounting_context(
    acting_for_organization_id: Optional[str] = Query(default=None),
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Resolve the effective accounting context for the authenticated actor.

    With no ``acting_for_organization_id`` the actor's own organisation is used
    (their membership organisation, or their consultant firm organisation). A
    request for an organisation they are not entitled to is refused with 403.
    """
    context = await resolve_accounting_context(
        current_user, repos, acting_for_organization_id
    )
    return {"context": context.as_payload()}


# ---------------------------------------------------------------------------
# B. Authorized consultant/client relationships
# ---------------------------------------------------------------------------
@router.get("/organizations")
async def list_accounting_organizations(
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """List every organisation the actor may act for, with the reason.

    Includes the actor's own organisation, their consultant firm organisation
    (when linked) and each client with an ACTIVE consultant-client grant. An
    organisation reachable only through an inactive or unratified grant is absent.
    """
    organizations = await list_authorized_organizations(current_user, repos)
    return {
        "organizations": [o.as_payload() for o in organizations],
        "count": len(organizations),
    }


# ---------------------------------------------------------------------------
# C. Select / switch the acting-for organisation
# ---------------------------------------------------------------------------
@router.post("/acting-for")
async def select_acting_for(
    payload: ActingForSelection,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Validate an acting-for selection and return the effective context.

    This is a *selection*, not an authorisation: the requested organisation must
    already be one the actor is entitled to, otherwise 403. Nothing is persisted
    here — attribution is persisted per record, at the point of the write.
    """
    context = await resolve_accounting_context(
        current_user, repos, payload.acting_for_organization_id
    )
    return {
        "context": context.as_payload(),
        "persisted": False,
        "note": (
            "Acting-for selection is a validated request context. Attribution is "
            "persisted per record via POST /api/v3/accounting/acting-for/attribute."
        ),
    }


# ---------------------------------------------------------------------------
# D. Resolve the effective accounting context + validate CAMS dimensions
# ---------------------------------------------------------------------------
@router.post("/dimensions/resolve")
async def resolve_dimensions(
    payload: DimensionResolutionRequest,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Resolve and validate the accounting dimensions for one input.

    VALIDATION ONLY. This endpoint does not calculate: no factor is selected, no
    quantity is multiplied and no snapshot is written. It exists so an input's
    accounting context can be established, authorised and checked before the
    calculation phases build on it.

    Dimension violations raise the P17 domain errors, which already carry their
    own HTTP status and machine-readable code — no mapping is duplicated here.
    """
    context = await resolve_accounting_context(
        current_user, repos, payload.acting_for_organization_id
    )
    dimensions = resolve_accounting_dimensions(
        scope=payload.scope,
        scope2_method=payload.scope2_method,
        scope3_category=payload.scope3_category,
        energy_type=payload.energy_type,
        data_quality=payload.data_quality,
        facility_id=payload.facility_id,
        transport_boundary=payload.transport_boundary,
        waste_origin=payload.waste_origin,
        source_snapshot_id=payload.source_snapshot_id,
        consolidation_approach=context.consolidation_approach,
    )
    return {
        "context": context.as_payload(),
        "dimensions": dimensions.as_columns(),
        "description": describe_dimensions(dimensions),
        "would_persist": False,
    }


# ---------------------------------------------------------------------------
# E. Persist acting-for attribution on a record
# ---------------------------------------------------------------------------
@router.post("/acting-for/attribute")
async def attribute_acting_for(
    payload: ActingForAttributionRequest,
    request: Request,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Persist acting-for attribution on one existing record, and audit it.

    The record's OWNER organisation is the authority: the actor must be entitled
    to it, otherwise 403. Carriers that carry no owner column (review decisions,
    report versions, audit entries) require an explicit
    ``acting_for_organization_id`` query parameter, authorised the same way.

    The stored values come from the server-resolved context, so a forged
    attribution cannot be persisted through this endpoint.
    """
    carrier = payload.carrier
    if carrier not in ACTING_FOR_CARRIERS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"unknown carrier {carrier!r}; expected one of "
                f"{sorted(ACTING_FOR_CARRIERS)}"
            ),
        )

    existing = await repos.accounting_context.get_acting_for_attribution(
        carrier=carrier, record_id=payload.record_id
    )
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=f"no {carrier} record with id {payload.record_id}",
        )

    owner = existing.get("owner_organization_id")
    if owner:
        # The record's owner is the authority — never the request payload.
        context = await ensure_record_owner_authorized(current_user, repos, owner)
    else:
        requested = request.query_params.get("acting_for_organization_id")
        if not requested:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"carrier {carrier!r} has no owner column; "
                    "acting_for_organization_id is required"
                ),
            )
        context = await resolve_accounting_context(current_user, repos, requested)

    stored = await repos.accounting_context.persist_acting_for(
        carrier=carrier,
        record_id=payload.record_id,
        actor_organization_id=context.actor_organization_id,
        acting_for_organization_id=context.acting_for_organization_id,
    )
    if stored is None:
        raise HTTPException(
            status_code=404,
            detail=f"no {carrier} record with id {payload.record_id}",
        )

    await record_acting_for_attribution(
        repos,
        carrier=carrier,
        record_id=payload.record_id,
        actor=current_user.user_id,
        actor_organization_id=context.actor_organization_id,
        acting_for_organization_id=context.acting_for_organization_id,
        owner_organization_id=owner,
    )
    return {
        "attribution": stored,
        "owner_organization_id": owner,
        "context": context.as_payload(),
        "audited": True,
    }


# ---------------------------------------------------------------------------
# F. Retrieve persisted acting-for attribution
# ---------------------------------------------------------------------------
@router.get("/acting-for/attribution")
async def get_attribution(
    carrier: str = Query(min_length=1),
    record_id: str = Query(min_length=1),
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Return the persisted acting-for attribution for one record.

    Reading attribution is itself tenant-scoped: when the carrier has an owner
    column, the actor must be entitled to that owner, so the endpoint cannot be
    used to probe another tenant's records.
    """
    if carrier not in ACTING_FOR_CARRIERS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"unknown carrier {carrier!r}; expected one of "
                f"{sorted(ACTING_FOR_CARRIERS)}"
            ),
        )
    attribution = await repos.accounting_context.get_acting_for_attribution(
        carrier=carrier, record_id=record_id
    )
    if attribution is None:
        raise HTTPException(
            status_code=404, detail=f"no {carrier} record with id {record_id}"
        )
    owner = attribution.get("owner_organization_id")
    if owner:
        await ensure_record_owner_authorized(current_user, repos, owner)
    return {"attribution": attribution}


# ---------------------------------------------------------------------------
# Scope 3 reference vocabulary
# ---------------------------------------------------------------------------
@router.get("/scope3/categories")
async def list_scope3_categories(
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Return the 15-category reference vocabulary with its architecture status.

    The status comes from the domain module (the authoritative rollup), NOT from
    the database: a category row is reference data and must never be read as
    "this category is implemented". ``calculable`` is the honest flag a UI can
    use to enable or disable a category picker.
    """
    from domain.scope3 import (
        SCOPE3_CATEGORIES,
        categories_requiring_consolidation,
        categories_requiring_transport_boundary,
        categories_requiring_waste_origin,
        is_calculable,
    )

    rows = await repos.accounting_context.list_scope3_categories()
    by_number = {c.category: c for c in SCOPE3_CATEGORIES}
    payload = []
    for row in rows:
        definition = by_number.get(row["category"])
        payload.append(
            {
                **row,
                "architecture_status": (
                    definition.status.value if definition else None
                ),
                "bounded_path": definition.bounded_path if definition else None,
                "boundary_note": definition.boundary_note if definition else None,
                "calculable": is_calculable(row["category"]),
                "requires_transport_boundary": (
                    row["category"] in categories_requiring_transport_boundary()
                ),
                "requires_waste_origin": (
                    row["category"] in categories_requiring_waste_origin()
                ),
                "requires_consolidation_approach": (
                    row["category"] in categories_requiring_consolidation()
                ),
            }
        )
    return {"categories": payload, "count": len(payload)}


# ---------------------------------------------------------------------------
# Persisted CAMS dimensions for one snapshot
# ---------------------------------------------------------------------------
@router.get("/dimensions/snapshot/{snapshot_id}")
async def get_snapshot_dimensions(
    snapshot_id: str,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Return the persisted CAMS dimensions and acting-for attribution of a snapshot.

    The snapshot's owning organisation is the authority, so this read is
    tenant-scoped like every other: an actor who is not entitled to the owning
    organisation receives 403.
    """
    dimensions = await repos.accounting_context.get_snapshot_dimensions(snapshot_id)
    if dimensions is None:
        raise HTTPException(status_code=404, detail="Calculation snapshot not found")
    context = await ensure_record_owner_authorized(
        current_user, repos, dimensions["organization_id"]
    )
    return {
        "dimensions": dimensions,
        "acting_for_organization_id": dimensions.get("acting_for_organization_id"),
        "attribution_persisted": (
            dimensions.get("acting_for_organization_id") is not None
        ),
        "context_persona": context.persona,
    }
