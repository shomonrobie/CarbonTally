"""Business-processing endpoints (CT-ARCH-012, prep-pack Phase 10.1/10.2).

The API boundary exposes the existing engines. Every handler is thin: it
validates the contract, resolves identifiers through the repositories, builds
the domain request object and delegates to the engine — no matching,
calculation, validation, benchmarking or report-generation logic lives here.

Endpoints:

* ``POST /api/v2/factor-match``      → FactorMatchingEngine
* ``POST /api/v2/calculate``         → CalculationEngine
* ``POST /api/v2/validate``          → ValidationEngine (strict → 422)
* ``POST /api/v2/benchmark``         → BenchmarkingEngine
* ``POST /api/v2/generate-report``   → ReportGenerationEngine
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from api.contracts import (
    BenchmarkIn,
    BenchmarkOut,
    CalculationIn,
    CalculationOut,
    FactorMatchIn,
    FactorMatchOut,
    ReportRequestIn,
    ReportOut,
    ValidationIn,
    ValidationOut,
    benchmark_out,
    calculation_out,
    match_out,
    report_out,
    validation_out,
)
from api.dependencies import (
    AuthUser,
    RepositoryBundle,
    ensure_org_access,
    get_benchmarking_engine,
    get_calculation_engine,
    get_current_user,
    get_matching_engine,
    get_repositories,
    get_report_engine,
    get_validation_engine,
)
from core.exceptions import FactorNotFoundError
from core.types import DateRange
from domain.benchmarking import BenchmarkRequest
from domain.matching import MatchRequest
from domain.report import ReportRequest
from domain.validation import ValidationRequest
from engines.benchmarking import BenchmarkingEngine
from engines.calculation import CalculationEngine, CalculationRequest
from engines.factor_matching import FactorMatchingEngine
from engines.report_generation import ReportGenerationEngine
from engines.validation import ValidationEngine

router = APIRouter(prefix="/api/v2", tags=["CarbonTally Processing"])


@router.post("/factor-match", response_model=FactorMatchOut)
async def factor_match(
    payload: FactorMatchIn,
    current_user: AuthUser = Depends(get_current_user),
    engine: FactorMatchingEngine = Depends(get_matching_engine),
) -> FactorMatchOut:
    """Match an activity to an emission factor (explainable, CT-ARCH-014)."""
    org_id = payload.organization_id or getattr(current_user, "organization_id", None)
    if org_id:
        ensure_org_access(current_user, org_id)
    request = MatchRequest(
        id=str(uuid.uuid4()),
        activity=payload.activity,
        country=payload.country,
        reporting_year=payload.reporting_year,
        unit=payload.unit,
        scope=payload.scope,
        organization_id=org_id,
        preferred_provider=payload.preferred_provider,
        max_stages=payload.max_stages,
    )
    result = await engine.match(request)
    return match_out(result)


@router.post("/calculate", response_model=CalculationOut)
async def calculate(
    payload: CalculationIn,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
    engine: CalculationEngine = Depends(get_calculation_engine),
) -> CalculationOut:
    """Calculate emissions from a matched factor (no matching logic here).

    V3 (O1): ``customer_factor_id`` resolves an approved customer factor and
    the snapshot records ``factor_kind='customer_factor'`` provenance.
    """
    ensure_org_access(current_user, payload.organization_id)
    customer_factor = None
    if payload.customer_factor_id is not None:
        customer_factor = await repos.customer_factors.get(payload.customer_factor_id)
        if customer_factor is None:
            raise HTTPException(
                status_code=404,
                detail=f"customer factor {payload.customer_factor_id} not found",
            )
        if customer_factor.organization_id != payload.organization_id:
            raise HTTPException(
                status_code=403,
                detail="customer factor does not belong to this organisation",
            )
        if customer_factor.status != "active":
            raise HTTPException(
                status_code=409,
                detail="only approved customer factors can be used in calculations",
            )
        factor = None
    else:
        factor = await repos.factors.get(payload.factor_id)  # type: ignore[arg-type]
        if factor is None:
            raise FactorNotFoundError(
                f"factor {payload.factor_id} not found",
                details={"factor_id": payload.factor_id},
            )
    request = CalculationRequest(
        match_request_id=str(uuid.uuid4()),
        organization_id=payload.organization_id,
        factor=factor,
        quantity=payload.quantity,
        quantity_unit=payload.quantity_unit,
        date=payload.date,
        reporting_year=payload.reporting_year,
        activity=payload.activity,
        activity_type=payload.activity_type,
        scope=payload.scope,
        methodology=payload.methodology,
        source_file=payload.source_file,
        source_page=payload.source_page,
        log_id=payload.log_id,
        asset_id=payload.asset_id,
        facility_id=payload.facility_id,
        customer_factor=customer_factor,
    )
    result = await engine.calculate(request)
    return calculation_out(result)


@router.post("/validate", response_model=ValidationOut)
async def validate(
    payload: ValidationIn,
    current_user: AuthUser = Depends(get_current_user),
    engine: ValidationEngine = Depends(get_validation_engine),
) -> ValidationOut:
    """Run Phase 9 data-quality validation over an organisation's data.

    Strict mode raises ``ValidationFailedError`` → HTTP 422 ``VALIDATION_FAILED``
    when blocking errors exist (the engine's strict-blocking contract).
    """
    ensure_org_access(current_user, payload.organization_id)
    period = (
        DateRange(start_date=payload.start_date, end_date=payload.end_date)
        if payload.start_date is not None
        else None
    )
    request = ValidationRequest(
        organization_id=payload.organization_id,
        reporting_year=payload.reporting_year,
        period=period,
        scope_filter=payload.scope_filter,
        entity_ids=tuple(payload.entity_ids or ()),
        strict=payload.strict,
    )
    report = await engine.validate(request)
    return validation_out(report)


@router.post("/benchmark", response_model=BenchmarkOut)
async def benchmark(
    payload: BenchmarkIn,
    current_user: AuthUser = Depends(get_current_user),
    engine: BenchmarkingEngine = Depends(get_benchmarking_engine),
) -> BenchmarkOut:
    """Run internal (self-referential) benchmarks for an organisation (Phase 9B)."""
    ensure_org_access(current_user, payload.organization_id)
    request = BenchmarkRequest(
        organization_id=payload.organization_id,
        reporting_year=payload.reporting_year,
        compare_years=tuple(payload.compare_years or ()),
        group_by=tuple(payload.group_by or ()),
        metrics=tuple(payload.metrics or ()),
        facility_filter=payload.facility_filter,
    )
    result = await engine.benchmark(request)
    return benchmark_out(result)


@router.post("/generate-report", response_model=ReportOut)
async def generate_report(
    payload: ReportRequestIn,
    current_user: AuthUser = Depends(get_current_user),
    engine: ReportGenerationEngine = Depends(get_report_engine),
) -> ReportOut:
    """Generate a structured report (12 sections) through ReportGenerationEngine."""
    ensure_org_access(current_user, payload.organization_id)
    request = ReportRequest(
        organization_id=payload.organization_id,
        report_type=payload.report_type,
        reporting_year=payload.reporting_year,
        template_id=payload.template_id,
        options=dict(payload.options or {}),
    )
    result = await engine.generate(request)
    return report_out(result)
