"""V3 Scope 2 calculation surface (P17-IMPLEMENT-05).

Exposes the minimum backend capability required to invoke a Scope 2 calculation
through the existing v3 API architecture. This is a thin transport over
:class:`services.scope2_calculation.Scope2CalculationService` — it owns no
calculation, factor-selection or persistence logic of its own, so there is no
second calculation API architecture.

Server-side authority
---------------------
``organization_id`` in the request body is the **data-owning organization the
caller claims**. It is never trusted: ``ensure_record_owner_authorized``
re-authorises the authenticated actor against that organization through the
IMPLEMENT-02 accounting-context layer, which is also the **only** source of the
acting-for / performed-by attribution. No attribution value is read from the
request body, so a forged acting-for is structurally impossible here.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.accounting_context_auth import ensure_record_owner_authorized
from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, require_org_member
from core.exceptions import InstrumentEligibilityError, ValidationFailedError
from domain.contractual_instruments import InstrumentAllocation
from domain.matching import MatchResult
from domain.scope2 import requires_instrument
from engines.calculation import CalculationEngine
from services.scope2_calculation import SCOPE2, Scope2CalculationService, Scope2Input

router = APIRouter(prefix="/api/v3/scope2", tags=["V3 — Scope 2"])

#: Namespace for the deterministic Scope 2 request identity. Derived from the
#: calculation's canonical inputs so an identical repeat yields the same
#: ``request_id`` — the P16 idempotency property, applied to a path where no
#: matching-engine request id exists because the operator selected the factor.
_REQUEST_NAMESPACE = uuid.UUID("6f1c7d2e-3a4b-4c5d-8e6f-7a8b9c0d1e2f")


class Scope2CalculateRequest(BaseModel):
    """A Scope 2 calculation request.

    ``scope2_method`` and ``energy_type`` are required with no default: a Scope 2
    claim cannot be submitted without stating its accounting method.
    """

    organization_id: str
    scope2_method: str
    energy_type: str
    quantity: Decimal = Field(gt=0)
    unit: str
    date: date
    reporting_year: int = Field(ge=1990, le=2100)
    activity: str
    activity_type: str
    #: Explicit operator factor selection (factor-governance rule 1). The service
    #: still validates scope, year and geography — an operator choice does not
    #: bypass governance.
    factor_id: Optional[str] = None
    geography: Optional[str] = None
    data_quality: Optional[str] = None
    facility_id: Optional[str] = None
    source_item_id: Optional[str] = None
    source_line_item_id: Optional[str] = None
    #: MARKET_BASED only — the contractual instrument to claim. Identified by id;
    #: its OWNERSHIP is never taken from this request. The instrument is loaded
    #: server-side and scoped to the resolved data-owning organization, so an
    #: instrument belonging to another tenant is simply not found.
    instrument_id: Optional[str] = None
    #: MARKET_BASED only — the quantity of the instrument claimed by this
    #: calculation. Defaults to the consumption quantity: a market-based claim is
    #: a full claim by definition, and the Scope 2 service independently requires
    #: the allocation to equal the consumption quantity.
    allocated_quantity: Optional[Decimal] = None
    #: The consumption period the allocation applies to. Defaults to the
    #: calculation date (a single-day period) — that is the activity's own date,
    #: not an invented window.
    allocation_period_start: Optional[date] = None
    allocation_period_end: Optional[date] = None


def _deterministic_request_id(payload: Scope2CalculateRequest) -> str:
    """Derive the P16 request identity from the calculation's canonical inputs."""
    canonical = "|".join(
        [
            "scope2",
            payload.organization_id,
            payload.scope2_method,
            payload.energy_type,
            str(payload.quantity),
            payload.unit,
            payload.date.isoformat(),
            str(payload.reporting_year),
            payload.activity,
            payload.activity_type,
            payload.factor_id or "",
        ]
    )
    return str(uuid.uuid5(_REQUEST_NAMESPACE, canonical))


@router.post("/calculate")
async def calculate_scope2(
    payload: Scope2CalculateRequest,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Validate, calculate and persist one Scope 2 result.

    Authorization is resolved server-side against the claimed data owner. The
    method and energy type are validated by the domain layer (``fuel`` is
    refused), and a market-based request is refused rather than downgraded.
    """
    context = await ensure_record_owner_authorized(
        current_user, repos, payload.organization_id
    )
    # The RESOLVED data-owning organization is the authorisation key. It is never
    # taken from the request body: the payload only names the organization the
    # caller claims, and that claim has just been verified.
    data_owner = context.data_owning_organization_id

    if payload.factor_id is None:
        raise ValidationFailedError(
            "an explicit factor_id is required for a Scope 2 calculation; "
            "automatic matching for Scope 2 is not exposed through this route",
            details={"field": "factor_id"},
        )
    factor = await repos.factors.get(payload.factor_id)
    if factor is None:
        raise ValidationFailedError(
            "the requested emission factor does not exist",
            details={"field": "factor_id", "factor_id": payload.factor_id},
        )

    instrument = None
    existing_allocations: list[InstrumentAllocation] = []
    period_start = payload.allocation_period_start or payload.date
    period_end = payload.allocation_period_end or payload.date
    allocated_quantity: Optional[Decimal] = payload.allocated_quantity

    if requires_instrument(payload.scope2_method):
        # ---------------------------------------------------------------
        # MARKET_BASED — the instrument is loaded SERVER-SIDE and scoped to the
        # authorized data-owning organization. Ownership is decided by the query,
        # never by the request body, so a client cannot establish accounting
        # entitlement by naming an instrument or an organization.
        # ---------------------------------------------------------------
        if payload.instrument_id is None:
            raise InstrumentEligibilityError(
                "a MARKET_BASED Scope 2 calculation requires instrument_id; the "
                "grid-average figure is a different claim and is never "
                "substituted automatically",
                details={"field": "instrument_id"},
            )
        if repos.contractual_instruments is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "the contractual instrument repository is not available in "
                    "this deployment; refusing a market-based claim rather than "
                    "trusting client-supplied instrument data"
                ),
            )
        instrument = await repos.contractual_instruments.get_for_organization(
            payload.instrument_id, data_owner
        )
        if instrument is None:
            # Not found OR not this tenant — deliberately indistinguishable, so the
            # response confirms nothing about another tenant's instruments.
            raise InstrumentEligibilityError(
                "no contractual instrument with that id is available to this "
                "organization",
                details={"field": "instrument_id"},
            )
        if allocated_quantity is None:
            allocated_quantity = payload.quantity
        existing_allocations = await repos.contractual_instruments.list_allocations(
            payload.instrument_id, data_owner
        )

    match = MatchResult(
        status="matched",
        factor=factor,
        confidence=1.0,
        methodology="direct_multiply",
        request_id=_deterministic_request_id(payload),
        factor_kind="emission_factor",
    )
    service = Scope2CalculationService(CalculationEngine(sink=repos.logs))
    result = await service.calculate(
        Scope2Input(
            organization_id=data_owner,
            quantity=payload.quantity,
            quantity_unit=payload.unit,
            date=payload.date,
            reporting_year=payload.reporting_year,
            activity=payload.activity,
            activity_type=payload.activity_type,
            method=payload.scope2_method,
            energy_type=payload.energy_type,
            match=match,
            geography=payload.geography,
            data_quality=payload.data_quality,
            facility_id=payload.facility_id,
            source_item_id=payload.source_item_id,
            source_line_item_id=payload.source_line_item_id,
            performed_by=current_user.user_id,
            performed_by_organization_id=context.actor_organization_id,
            acting_for_organization_id=context.acting_for_organization_id,
            instrument=instrument,
            allocated_quantity=allocated_quantity,
            existing_allocations=existing_allocations,
        )
    )
    # ------------------------------------------------------------------
    # Allocation persistence — written only AFTER the calculation succeeded, so
    # the allocation always references a real, already-persisted snapshot. The
    # claim is recorded idempotently against the calculation request identity.
    # ------------------------------------------------------------------
    allocation_id: Optional[str] = None
    if instrument is not None and instrument.id is not None:
        existing = await repos.contractual_instruments.find_allocation_for_request(
            instrument_id=instrument.id,
            organization_id=data_owner,
            period_start=period_start,
            period_end=period_end,
            request_id=result.snapshot.match_request_id,
        )
        if existing is not None:
            allocation_id = existing
        else:
            allocation_id = await repos.contractual_instruments.record_allocation(
                InstrumentAllocation(
                    organization_id=data_owner,
                    instrument_id=instrument.id,
                    allocated_quantity=allocated_quantity,
                    allocated_unit=payload.unit,
                    allocation_period_start=period_start,
                    allocation_period_end=period_end,
                    calculation_snapshot_id=result.snapshot.id,
                    # The snapshot is the authoritative link; CalculationResult does
                    # not return the log id and the column is nullable.
                    emissions_log_id=None,
                    claim_reference=f"scope2:{result.snapshot.match_request_id}",
                )
            )

    dimensions = result.snapshot.accounting_dimensions
    return {
        "snapshot_id": result.snapshot.id,
        "request_id": result.snapshot.match_request_id,
        "organization_id": result.snapshot.organization_id,
        "acting_for_organization_id": (
            dimensions.acting_for_organization_id if dimensions else None
        ),
        "performed_by_organization_id": (
            dimensions.performed_by_organization_id if dimensions else None
        ),
        "scope": result.snapshot.scope,
        "scope2_method": dimensions.scope2_method if dimensions else None,
        "energy_type": dimensions.energy_type if dimensions else None,
        "data_quality": dimensions.data_quality if dimensions else None,
        "factor_id": result.snapshot.factor_id,
        "factor_kind": result.snapshot.factor_kind,
        "factor_year": factor.reporting_year,
        # P17-IMPLEMENT-06 — market-based provenance: which instrument backed the
        # claim and which allocation row records it. Both are null for
        # location-based results, which is what makes the method distinguishable
        # downstream without inference.
        "instrument_id": instrument.id if instrument is not None else None,
        "allocation_id": allocation_id,
        "co2e_kg": str(result.co2e_kg),
        "co2e_tonnes": str(result.co2e_tonnes),
        "methodology": result.snapshot.methodology,
        "reporting_year": result.snapshot.reporting_year,
        "content_hash": result.snapshot.content_hash,
    }
