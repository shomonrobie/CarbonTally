"""Phase 10 API contracts (prep-pack Phase 10.2).

Stable, JSON-serialisable request/response models for the v2.1 API. Contracts
are deliberately separate from:

* database models / SQL (``data`` layer),
* provider models and import internals (``src/providers``),
* engine implementation details (``engines`` — only the public output objects
  are serialised).

**CO2/CO2e provenance** is preserved in every response that carries factor
data through ``gas_coverage`` (``"CO2"`` for SEAI CO2-only factors, ``"CO2e"``
otherwise). The domain classifier :func:`domain.factor.gas_coverage` is the
single source of truth — the API never relabels CO2-only data as CO2e.

Decimal values are serialised as strings (stable, exact) exactly as the domain
layer already does (``domain.factor.RESULT_PRECISION`` quantisation).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from domain.audit import AuditEntry
from domain.benchmarking import BenchmarkMetric, BenchmarkResult
from domain.calculation import CalculationResult, CalculationSnapshot, VerificationResult
from domain.factor import EmissionFactor, gas_coverage
from domain.matching import FactorAlias, MatchResult, Suggestion
from domain.provider import ImportBatch, ImportError as BatchImportError
from domain.report import GeneratedReport
from domain.validation import ValidationIssue, ValidationReport
from engines.report_generation import ReportContent, ReportGenerationResult


def _jsonable(value: Any) -> Any:
    """Convert a domain value to a JSON-serialisable structure."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return str(value)


# ===========================================================================
# Shared / error envelope
# ===========================================================================


class ErrorDetail(BaseModel):
    """One machine-readable error payload (``core.exceptions`` contract)."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """The uniform error envelope returned by the API.

    ``code`` is the stable machine-readable code from
    ``core.exceptions.CarbonTallyError.code`` (or ``VALIDATION_ERROR`` /
    ``NOT_FOUND`` / ``INTERNAL_ERROR``), never a raw database or stack-trace
    string.
    """

    error: ErrorDetail
    request_id: str = ""


class HealthResponse(BaseModel):
    """Liveness response (no database access)."""

    status: Literal["ok"] = "ok"
    service: str = "carbontally-api-v2"
    version: str = "1.0"
    request_id: str = ""


# ===========================================================================
# Factors / matching
# ===========================================================================


class FactorOut(BaseModel):
    """An emission factor as returned by the API.

    ``gas_coverage`` preserves the CO2-only (SEAI) vs CO2e (DEFRA) distinction
    exactly as ``domain.factor.gas_coverage`` classifies it.
    """

    id: str
    reporting_year: int
    activity_type: str
    co2e_multiplier: str
    unit: Optional[str] = None
    scope: Optional[str] = None
    factor_source: str = ""
    factor_set: str = ""
    country: str = "GB"
    provider_key: str = ""
    import_batch_id: Optional[str] = None
    gas_coverage: Literal["CO2", "CO2e"] = "CO2e"


def factor_out(factor: EmissionFactor) -> FactorOut:
    """Serialise a domain factor, computing the provenance label."""
    return FactorOut(
        id=factor.id,
        reporting_year=factor.reporting_year,
        activity_type=factor.activity_type,
        co2e_multiplier=str(factor.co2e_multiplier),
        unit=factor.unit,
        scope=factor.scope,
        factor_source=factor.factor_source,
        factor_set=factor.factor_set,
        country=factor.country,
        provider_key=factor.provider_key,
        import_batch_id=factor.import_batch_id,
        gas_coverage=gas_coverage(factor),
    )


class SuggestionOut(BaseModel):
    """An alternative factor offered for manual selection (CT-ARCH-014)."""

    factor: FactorOut
    score: float
    reason: str
    stage: str


class FactorMatchIn(BaseModel):
    """POST /api/v2/factor-match request (CT-ARCH-012)."""

    activity: str = Field(..., min_length=1, max_length=500)
    country: str = Field("GB", min_length=2, max_length=2)
    reporting_year: int = Field(..., ge=1990, le=2100)
    unit: Optional[str] = None
    scope: Optional[str] = None
    organization_id: Optional[str] = None
    preferred_provider: Optional[str] = None
    max_stages: int = Field(6, ge=1, le=6)

    model_config = ConfigDict(extra="forbid")


class FactorMatchOut(BaseModel):
    """POST /api/v2/factor-match response (explainable match, CT-ARCH-014)."""

    status: str
    factor: Optional[FactorOut] = None
    confidence: float = 0.0
    methodology: str = ""
    provider: Optional[str] = None
    stages_executed: list[str] = Field(default_factory=list)
    request_id: str = ""
    suggestions: list[SuggestionOut] = Field(default_factory=list)


def match_out(result: MatchResult) -> FactorMatchOut:
    """Serialise a matching-engine result."""
    return FactorMatchOut(
        status=result.status,
        factor=factor_out(result.factor) if result.factor is not None else None,
        confidence=result.confidence,
        methodology=result.methodology,
        provider=result.provider,
        stages_executed=list(result.stages_executed or ()),
        request_id=result.request_id or "",
        suggestions=[
            SuggestionOut(factor=factor_out(s.factor), score=s.score, reason=s.reason, stage=s.stage)
            for s in (result.suggestions or ())
        ],
    )


# ===========================================================================
# Calculation
# ===========================================================================


class CalculationIn(BaseModel):
    """POST /api/v2/calculate request (CT-ARCH-012).

    ``factor_id`` refers to an existing emission factor; the API resolves it
    through ``EmissionFactorsRepository`` and hands the domain factor to the
    Calculation Engine (no matching logic is reimplemented here).
    """

    organization_id: str = Field(..., min_length=1)
    factor_id: str = Field(..., min_length=1)
    quantity: Decimal
    quantity_unit: str = Field(..., min_length=1)
    date: date
    reporting_year: int = Field(..., ge=1990, le=2100)
    activity: str = Field(..., min_length=1)
    activity_type: str = Field(..., min_length=1)
    scope: Optional[str] = None
    methodology: str = "direct_multiply"
    source_file: Optional[str] = None
    source_page: Optional[int] = None
    log_id: Optional[str] = None
    asset_id: Optional[str] = None
    facility_id: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class CalculationSnapshotOut(BaseModel):
    """Immutable calculation snapshot (reproducible figure, §13)."""

    id: str
    match_request_id: str
    organization_id: str
    factor_id: str
    quantity: str
    quantity_unit: str
    co2e_multiplier: str
    co2e_kg: str
    scope: Optional[str] = None
    date: date
    reporting_year: int
    methodology: str
    algorithm_version: str
    created_at: date
    content_hash: str = ""
    source_file: Optional[str] = None
    source_page: Optional[int] = None


def _snapshot_out(s: CalculationSnapshot) -> CalculationSnapshotOut:
    return CalculationSnapshotOut(
        id=s.id,
        match_request_id=s.match_request_id,
        organization_id=s.organization_id,
        factor_id=s.factor_id,
        quantity=str(s.quantity),
        quantity_unit=s.quantity_unit,
        co2e_multiplier=str(s.co2e_multiplier),
        co2e_kg=str(s.co2e_kg),
        scope=s.scope,
        date=s.date,
        reporting_year=s.reporting_year,
        methodology=s.methodology,
        algorithm_version=s.algorithm_version,
        created_at=s.created_at,
        content_hash=s.content_hash,
        source_file=s.source_file,
        source_page=s.source_page,
    )


class CalculationOut(BaseModel):
    """POST /api/v2/calculate response.

    ``gas_coverage`` carries the factor's CO2/CO2e provenance — a SEAI CO2-only
    figure is never relabelled as CO2e here.
    """

    co2e_kg: str
    co2e_tonnes: str
    gas_coverage: Literal["CO2", "CO2e"] = "CO2e"
    snapshot: CalculationSnapshotOut
    factor: FactorOut
    methodology: str


def calculation_out(result: CalculationResult) -> CalculationOut:
    """Serialise a calculation-engine result."""
    return CalculationOut(
        co2e_kg=str(result.co2e_kg),
        co2e_tonnes=str(result.co2e_tonnes),
        gas_coverage=gas_coverage(result.factor_used),
        snapshot=_snapshot_out(result.snapshot),
        factor=factor_out(result.factor_used),
        methodology=result.methodology.value,
    )


class VerificationOut(BaseModel):
    """Audit-time reproducibility check result (§13)."""

    match: bool
    discrepancy: Optional[str] = None
    tampered: bool = False


def verification_out(result: VerificationResult) -> VerificationOut:
    return VerificationOut(
        match=result.match,
        discrepancy=str(result.discrepancy) if result.discrepancy is not None else None,
        tampered=result.tampered,
    )


# ===========================================================================
# Validation
# ===========================================================================


class ValidationIn(BaseModel):
    """POST /api/v2/validate request (Phase 9A surface, thin orchestration)."""

    organization_id: str = Field(..., min_length=1)
    reporting_year: int = Field(..., ge=1990, le=2100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    scope_filter: Optional[str] = None
    entity_ids: list[str] = Field(default_factory=list)
    strict: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _check_period(self) -> "ValidationIn":
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError("start_date and end_date must be provided together")
        if self.start_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class ValidationIssueOut(BaseModel):
    """One validation finding (code/severity/context, CT-ARCH-014)."""

    code: str
    severity: str
    message: str
    entity_type: str
    entity_id: str
    field: str = ""
    context: dict[str, Any] = Field(default_factory=dict)


class ValidationOut(BaseModel):
    """POST /api/v2/validate response.

    ``ok`` is ``False`` whenever blocking (error-severity) issues exist. Strict
    mode raises a 422 ``VALIDATION_FAILED`` instead of returning a failing
    report (the engine's documented strict-blocking contract).
    """

    ok: bool
    counts: dict[str, int] = Field(default_factory=dict)
    issues: list[ValidationIssueOut] = Field(default_factory=list)


def validation_out(report: ValidationReport) -> ValidationOut:
    return ValidationOut(
        ok=report.ok,
        counts=dict(report.counts),
        issues=[
            ValidationIssueOut(
                code=i.code,
                severity=i.severity.value,
                message=i.message,
                entity_type=i.entity_type,
                entity_id=i.entity_id,
                field=i.field,
                context=_jsonable(i.context),
            )
            for i in report.issues
        ],
    )


# ===========================================================================
# Benchmarking
# ===========================================================================


class BenchmarkIn(BaseModel):
    """POST /api/v2/benchmark request (Phase 9B surface, thin orchestration)."""

    organization_id: str = Field(..., min_length=1)
    reporting_year: int = Field(..., ge=1990, le=2100)
    compare_years: list[int] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=lambda: ["year", "facility", "scope"])
    metrics: list[str] = Field(
        default_factory=lambda: ["total", "per_fte", "per_area", "per_revenue", "activity_intensity"]
    )
    facility_filter: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("compare_years")
    @classmethod
    def _years_in_range(cls, years: list[int]) -> list[int]:
        for year in years:
            if not 1990 <= year <= 2100:
                raise ValueError(f"compare year {year} outside supported range 1990-2100")
        return years


class BenchmarkMetricOut(BaseModel):
    """One benchmark row (explicit non-available statuses are never fabricated)."""

    key: str
    label: str
    unit: str
    status: str
    value: Optional[str] = None
    numerator: Optional[str] = None
    denominator: Optional[str] = None
    baseline_value: Optional[str] = None
    delta: Optional[str] = None
    delta_pct: Optional[str] = None
    comparison: str = ""
    source: str = ""
    scope: Optional[str] = None
    facility_id: Optional[str] = None
    activity_type: Optional[str] = None
    note: str = ""


def _metric_out(m: BenchmarkMetric) -> BenchmarkMetricOut:
    return BenchmarkMetricOut(
        key=m.key,
        label=m.label,
        unit=m.unit,
        status=m.status.value,
        value=str(m.value) if m.value is not None else None,
        numerator=str(m.numerator) if m.numerator is not None else None,
        denominator=str(m.denominator) if m.denominator is not None else None,
        baseline_value=str(m.baseline_value) if m.baseline_value is not None else None,
        delta=str(m.delta) if m.delta is not None else None,
        delta_pct=str(m.delta_pct) if m.delta_pct is not None else None,
        comparison=m.comparison,
        source=m.source,
        scope=m.scope,
        facility_id=m.facility_id,
        activity_type=m.activity_type,
        note=m.note,
    )


class BenchmarkOut(BaseModel):
    """POST /api/v2/benchmark response."""

    organization_id: str
    reporting_year: int
    metrics: list[BenchmarkMetricOut] = Field(default_factory=list)
    by_scope: dict[str, str] = Field(default_factory=dict)
    by_group: dict[str, str] = Field(default_factory=dict)
    generated_at: datetime


def benchmark_out(result: BenchmarkResult) -> BenchmarkOut:
    return BenchmarkOut(
        organization_id=result.organization_id,
        reporting_year=result.reporting_year,
        metrics=[_metric_out(m) for m in result.metrics],
        by_scope={str(k): str(v) for k, v in result.by_scope.items()},
        by_group={str(k): str(v) for k, v in result.by_group.items()},
        generated_at=result.generated_at,
    )


# ===========================================================================
# Report generation
# ===========================================================================


class ReportRequestIn(BaseModel):
    """POST /api/v2/generate-report request (CT-ARCH-012)."""

    organization_id: str = Field(..., min_length=1)
    report_type: str = Field(..., min_length=1)
    reporting_year: int = Field(..., ge=1990, le=2100)
    template_id: Optional[str] = None
    options: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class ReportOut(BaseModel):
    """POST /api/v2/generate-report response.

    ``content`` is the structured, 12-section report payload (Phase 9C) with the
    provenance section carrying the CO2/CO2e mix; ``report`` mirrors the
    persisted lifecycle record.
    """

    id: str
    organization_id: str
    report_type: str
    reporting_year: int
    storage_url: str = ""
    file_size_bytes: int = 0
    generated_at: datetime
    page_count: int = 0
    content: dict[str, Any] = Field(default_factory=dict)


def report_out(result: ReportGenerationResult) -> ReportOut:
    report = result.report
    return ReportOut(
        id=report.id,
        organization_id=report.organization_id,
        report_type=report.report_type,
        reporting_year=report.reporting_year,
        storage_url=report.storage_url,
        file_size_bytes=report.file_size_bytes,
        generated_at=report.generated_at,
        page_count=report.page_count,
        content=result.content.to_dict(),
    )


def report_out_from_report(report: GeneratedReport, content: Optional[ReportContent] = None) -> ReportOut:
    """Serialise a persisted report plus optional structured content."""
    return ReportOut(
        id=report.id,
        organization_id=report.organization_id,
        report_type=report.report_type,
        reporting_year=report.reporting_year,
        storage_url=report.storage_url,
        file_size_bytes=report.file_size_bytes,
        generated_at=report.generated_at,
        page_count=report.page_count,
        content=content.to_dict() if content is not None else {},
    )


# ===========================================================================
# Admin — imports
# ===========================================================================


class ImportErrorOut(BaseModel):
    """One row-level import error."""

    row_number: int
    field: str
    message: str
    severity: str


def _import_error_out(e: BatchImportError) -> ImportErrorOut:
    return ImportErrorOut(row_number=e.row_number, field=e.field, message=e.message, severity=e.severity)


class ImportBatchOut(BaseModel):
    """An import batch (read-only exposure of ``import_batches``)."""

    id: str
    provider_key: str
    provider_version: str
    source_file: str
    source_checksum: str
    reporting_year: int
    status: str
    rows_total: int = 0
    rows_imported: int = 0
    rows_skipped: int = 0
    rows_duplicate: int = 0
    errors: list[ImportErrorOut] = Field(default_factory=list)
    is_active: bool = False
    created_at: datetime
    created_by: str = ""
    rolled_back_from: Optional[str] = None
    updated_at: Optional[datetime] = None


def import_batch_out(b: ImportBatch) -> ImportBatchOut:
    return ImportBatchOut(
        id=b.id,
        provider_key=b.provider_key,
        provider_version=b.provider_version,
        source_file=b.source_file,
        source_checksum=b.source_checksum,
        reporting_year=b.reporting_year,
        status=b.status,
        rows_total=b.rows_total,
        rows_imported=b.rows_imported,
        rows_skipped=b.rows_skipped,
        rows_duplicate=b.rows_duplicate,
        errors=[_import_error_out(e) for e in b.errors],
        is_active=b.is_active,
        created_at=b.created_at,
        created_by=getattr(b, "created_by", "") or "",
        rolled_back_from=getattr(b, "rolled_back_from", None),
        updated_at=getattr(b, "updated_at", None),
    )


class ImportBatchListOut(BaseModel):
    """Batch history for one provider (newest first)."""

    provider: str
    total: int
    batches: list[ImportBatchOut] = Field(default_factory=list)


class ImportActiveOut(BaseModel):
    """The currently active batch for a provider + year (nullable when none)."""

    provider: str
    reporting_year: int
    batch: Optional[ImportBatchOut] = None

# ===========================================================================
# Admin — providers
# ===========================================================================


class ProviderOut(BaseModel):
    """Provider metadata + implementation state.

    ``implemented`` is ``False`` for deferred providers (EPA/ADEME/IPCC) — the
    API never pretends a deferred provider is live. ``active_batches`` and
    ``factor_count`` are derived from the repository for implemented providers.
    """

    key: str
    name: str
    jurisdiction: str
    country_codes: list[str] = Field(default_factory=list)
    website: str = ""
    license: str = ""
    latest_version: str = ""
    publisher: str = ""
    language: str = ""
    documentation_url: str = ""
    implemented: bool
    status: Literal["active", "deferred"] = "deferred"
    factor_count: int = 0
    active_batches: list[ImportBatchOut] = Field(default_factory=list)


class ProviderListOut(BaseModel):
    """Provider catalogue response."""

    providers: list[ProviderOut] = Field(default_factory=list)


# ===========================================================================
# Admin — audit
# ===========================================================================


class AuditEntryOut(BaseModel):
    """One audit-trail entry (staff/admin surface)."""

    id: str
    correlation_id: str = ""
    entity_type: str
    entity_id: str
    action: str
    actor: str = ""
    occurred_at: datetime
    changed_fields: dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    before: Optional[dict[str, Any]] = None
    after: Optional[dict[str, Any]] = None


def audit_entry_out(entry: AuditEntry) -> AuditEntryOut:
    return AuditEntryOut(
        id=entry.id,
        correlation_id=entry.correlation_id,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        action=entry.action,
        actor=entry.actor,
        occurred_at=entry.occurred_at,
        changed_fields=_jsonable(entry.changed_fields),
        reason=entry.reason,
        ip_address=entry.ip_address,
        before=_jsonable(entry.before) if entry.before is not None else None,
        after=_jsonable(entry.after) if entry.after is not None else None,
    )


class AuditListOut(BaseModel):
    """Paged audit-query response."""

    total: int
    entries: list[AuditEntryOut] = Field(default_factory=list)


class AuditCsvOut(BaseModel):
    """CSV export of matching audit entries (produced by AuditRepository)."""

    filename: str
    content_type: str = "text/csv"
    csv: str


# ===========================================================================
# Admin — factor aliases
# ===========================================================================


class FactorAliasOut(BaseModel):
    """A global or organisation-scoped factor alias."""

    id: str
    organization_id: Optional[str] = None
    alias_text: str
    target_activity_type: str
    target_provider_key: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None


def factor_alias_out(alias: FactorAlias) -> FactorAliasOut:
    return FactorAliasOut(
        id=alias.id,
        organization_id=alias.organization_id,
        alias_text=alias.alias_text,
        target_activity_type=alias.target_activity_type,
        target_provider_key=alias.target_provider_key,
        created_by=alias.created_by,
        created_at=alias.created_at,
    )


class FactorAliasCreate(BaseModel):
    """POST /api/v2/admin/aliases payload.

    ``organization_id = None`` creates a global alias; a non-NULL value creates
    an organisation-scoped alias (organisation ownership is preserved).
    """

    alias_text: str = Field(..., min_length=1, max_length=200)
    target_activity_type: str = Field(..., min_length=1)
    target_provider_key: str = Field(..., min_length=1)
    organization_id: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class FactorAliasUpdate(BaseModel):
    """PUT /api/v2/admin/aliases/{id} payload — at least one field required."""

    alias_text: Optional[str] = Field(None, min_length=1, max_length=200)
    target_activity_type: Optional[str] = Field(None, min_length=1)
    target_provider_key: Optional[str] = Field(None, min_length=1)
    organization_id: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _at_least_one(self) -> "FactorAliasUpdate":
        fields = (self.alias_text, self.target_activity_type, self.target_provider_key)
        if not any(f is not None for f in fields):
            raise ValueError("at least one field must be provided to update an alias")
        return self


class FactorAliasListOut(BaseModel):
    """Alias listing response."""

    total: int
    aliases: list[FactorAliasOut] = Field(default_factory=list)


