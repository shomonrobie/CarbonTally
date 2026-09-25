"""V3 Scope 3 calculation surface (P17-IMPLEMENT-07).

ONE canonical endpoint for all fifteen categories, mirroring the Scope 2 surface.
The category is a request field, not fifteen routes: the pathway comes from the
category contract and every category persists through the same canonical
``CalculationEngine`` path.

``organization_id`` names the organization the caller *claims* and is never
trusted: ``ensure_record_owner_authorized`` re-authorises the actor and the data
owner plus acting-for attribution are taken from the resolved context only.

A clarification (missing required input) is surfaced as **422** naming the missing
fields — a manual-review path that never persists a fabricated value.
"""
from __future__ import annotations

import dataclasses
import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.accounting_context_auth import (
    ensure_record_owner_authorized,
    resolve_authorized_supplier,
)
from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, require_org_member
from core.exceptions import ValidationFailedError
from domain.data_quality import is_estimated
from domain.estimation import EstimationRecord
from domain.matching import MatchResult
from engines.calculation import CalculationEngine
from services.scope3_calculation import Scope3CalculationService, Scope3Input

router = APIRouter(prefix="/api/v3/scope3", tags=["V3 — Scope 3"])

#: Namespace for the deterministic Scope 3 request identity. Derived from the
#: canonical inputs so an identical repeat yields the same ``request_id`` — the
#: P16 idempotency property, on a path with no matching-engine request id.
_REQUEST_NAMESPACE = uuid.UUID("7a2d8e3f-4b5c-4d6e-9f70-8b9c0d1e2f30")


class Scope3CalculateRequest(BaseModel):
    """A Scope 3 calculation request. ``category`` is required with no default."""

    organization_id: str
    category: int = Field(ge=1, le=15)
    quantity: Decimal = Field(gt=0)
    unit: str
    date: date
    reporting_year: int = Field(ge=1990, le=2100)
    activity: str
    activity_type: str
    factor_id: Optional[str] = None
    pathway: Optional[str] = None
    methodology: Optional[str] = None
    data_quality: Optional[str] = None
    #: Category-specific inputs (material, treatment_route, trip_purpose,
    #: use_phase_assumption, allocation_basis, capitalisation_declared, ...).
    inputs: dict[str, Any] = Field(default_factory=dict)
    #: DC-02 / DC-04 / DC-05 / DC-07 boundary declarations.
    transport_boundary: Optional[str] = None
    waste_origin: Optional[str] = None
    consolidation_approach: Optional[str] = None
    source_snapshot_id: Optional[str] = None
    facility_id: Optional[str] = None
    supplier_id: Optional[str] = None
    source_item_id: Optional[str] = None
    source_line_item_id: Optional[str] = None
    #: T-INV-12 — the estimation basis, required whenever the value is an estimate.
    estimation_method: Optional[str] = None
    estimation_inputs: dict[str, Any] = Field(default_factory=dict)
    estimation_assumptions: dict[str, Any] = Field(default_factory=dict)


def deterministic_scope3_request_id(payload: Scope3CalculateRequest) -> str:
    """Derive the P16 request identity from the calculation's canonical inputs."""
    canonical = "|".join(
        [
            "scope3",
            payload.organization_id,
            str(payload.category),
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


def _build_estimation(
    payload: Scope3CalculateRequest, data_owner: str
) -> Optional[EstimationRecord]:
    """Build the estimation record when the caller supplied an estimation basis."""
    if payload.estimation_method is None:
        return None
    return EstimationRecord(
        organization_id=data_owner,
        estimation_method=payload.estimation_method,
        inputs=payload.estimation_inputs,
        assumptions=payload.estimation_assumptions,
        factor_id=payload.factor_id,
        scope3_category=payload.category,
    )


@router.post("/calculate")
async def calculate_scope3(
    payload: Scope3CalculateRequest,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Validate, calculate and persist one Scope 3 result for any category."""
    context = await ensure_record_owner_authorized(
        current_user, repos, payload.organization_id
    )
    data_owner = context.data_owning_organization_id

    # ------------------------------------------------------------------
    # P17-IMPLEMENT-09 — supplier attribution is a CLAIM, not an authority:
    # resolved server-side against the authorized data owner, so a calculation
    # can never attribute emissions to another tenant's supplier, and an
    # unhonourable claim is refused instead of being silently dropped.
    # ------------------------------------------------------------------
    supplier_id = await resolve_authorized_supplier(
        repos, payload.supplier_id, data_owner
    )

    match: Optional[MatchResult] = None
    if payload.factor_id is not None:
        factor = await repos.factors.get(payload.factor_id)
        if factor is None:
            raise ValidationFailedError(
                "the requested emission factor does not exist",
                details={"field": "factor_id", "factor_id": payload.factor_id},
            )
        match = MatchResult(
            status="matched",
            factor=factor,
            confidence=1.0,
            methodology="direct_multiply",
            request_id=deterministic_scope3_request_id(payload),
            factor_kind="emission_factor",
        )

    service = Scope3CalculationService(CalculationEngine(sink=repos.logs))
    outcome = await service.calculate(
        Scope3Input(
            organization_id=data_owner,
            category=payload.category,
            quantity=payload.quantity,
            quantity_unit=payload.unit,
            date=payload.date,
            reporting_year=payload.reporting_year,
            activity=payload.activity,
            activity_type=payload.activity_type,
            match=match,
            pathway=payload.pathway,
            methodology=payload.methodology,
            data_quality=payload.data_quality,
            inputs=payload.inputs,
            transport_boundary=payload.transport_boundary,
            waste_origin=payload.waste_origin,
            consolidation_approach=payload.consolidation_approach,
            source_snapshot_id=payload.source_snapshot_id,
            facility_id=payload.facility_id,
            supplier_id=supplier_id,
            source_item_id=payload.source_item_id,
            source_line_item_id=payload.source_line_item_id,
            performed_by=current_user.user_id,
            performed_by_organization_id=context.actor_organization_id,
            acting_for_organization_id=context.acting_for_organization_id,
            estimation=_build_estimation(payload, data_owner),
        )
    )

    if not outcome.calculated:
        # A controlled, non-fabricating outcome: 422 with the exact gaps.
        raise HTTPException(status_code=422, detail=outcome.clarification.as_payload())

    contract = outcome.contract
    snapshot = outcome.result.snapshot
    dimensions = snapshot.accounting_dimensions

    # ------------------------------------------------------------------
    # Estimation persistence (T-INV-12) — written only AFTER the calculation
    # succeeded, so the record's foreign key always references a real snapshot.
    # Ownership comes from the resolved data owner and the resolved attribution,
    # never from the request body.
    # ------------------------------------------------------------------
    estimation_id: Optional[str] = None
    if payload.estimation_method is not None and repos.estimation_records is not None:
        estimation_id = await repos.estimation_records.record(
            dataclasses.replace(
                _build_estimation(payload, data_owner),
                calculation_snapshot_id=snapshot.id,
                # The snapshot is the authoritative link; CalculationResult does
                # not return the log id and the column is nullable.
                emissions_log_id=None,
                actor_user_id=current_user.user_id,
                actor_organization_id=context.actor_organization_id,
                acting_for_organization_id=context.acting_for_organization_id,
            )
        )

    return {
        "status": "CALCULATED",
        "snapshot_id": snapshot.id,
        "request_id": snapshot.match_request_id,
        "category": dimensions.scope3_category,
        "category_name": contract.name,
        "scope": snapshot.scope,
        "pathway": contract.pathway.value,
        "architecture_status": contract.architecture_status,
        "methodology": snapshot.methodology,
        "data_quality": dimensions.data_quality,
        "is_estimated": is_estimated(dimensions.data_quality),
        "organization_id": snapshot.organization_id,
        "acting_for_organization_id": dimensions.acting_for_organization_id,
        "performed_by_organization_id": dimensions.performed_by_organization_id,
        "transport_boundary": dimensions.transport_boundary,
        "waste_origin": dimensions.waste_origin,
        "source_snapshot_id": dimensions.source_snapshot_id,
        "factor_id": snapshot.factor_id,
        "factor_kind": snapshot.factor_kind,
        "estimation_record_id": estimation_id,
        "co2e_kg": str(outcome.result.co2e_kg),
        "co2e_tonnes": str(outcome.result.co2e_tonnes),
        "reporting_year": snapshot.reporting_year,
        "content_hash": snapshot.content_hash,
    }

