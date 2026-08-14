"""Report Generation Engine (Backend v2.1 §7, Phase 9C — contract 9.3).

Structured report generation only. The engine composes ordered, JSON-serialisable
report sections from CalculationEngine (verification), ValidationEngine
(validation section; strict blocking respected), BenchmarkingEngine
(benchmarking section; availability states preserved), ReportsRepository
(lifecycle + structured-content persistence), OrganizationsRepository +
EmissionsLogsRepository (source data), EventBus (``ReportGenerated``) and
AuditLogger.

The output is a stable, serialisable structure suitable for later
rendering/API consumption (Phase 10) — independent of HTTP, FastAPI, PDF and
HTML. No rendering is performed here.

CO2/CO2e provenance is mandatory: SEAI factors are CO2-only, DEFRA factors are
CO2e. Every emissions figure carries a provenance-aware unit
(``kg CO2`` / ``kg CO2e`` / ``kg CO2/CO2e mixed``) and source labels; SEAI
CO2-only results are never relabelled as full CO2e.

No data is invented: sections with insufficient data are represented
explicitly (``insufficient_data`` / availability states) rather than as
fabricated zeros. If strict validation is configured and blocking errors
exist, ``ValidationFailedError`` propagates and no report is persisted.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional, Protocol

from core.exceptions import (
    BenchmarkDataInsufficientError,
    ReportGenerationFailedError,
    ValidationFailedError,
)
from core.logging import get_logger
from core.types import DateRange
from domain.benchmarking import BenchmarkRequest, BenchmarkResult
from domain.calculation import (
    CalculationSnapshot,
    EmissionLog,
    EmissionsAggregate,
    VerificationResult,
)
from domain.factor import EmissionFactor, gas_coverage
from domain.organization import Organization, OrganizationMetadata
from domain.report import GeneratedReport, ReportRequest, ReportSection, ReportTemplate
from domain.validation import ValidationReport, ValidationRequest
from domain.workflow import ReportGenerated
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus

logger = get_logger(__name__)

#: Engine version stamped into the generation section.
ENGINE_VERSION = "1.0"

#: Default ordered report sections (section_id, title).
_SECTION_ORDER: tuple[tuple[str, str], ...] = (
    ("metadata", "Report metadata"),
    ("organization", "Organization"),
    ("period", "Reporting period"),
    ("totals", "Emissions totals"),
    ("scopes", "Scope summaries"),
    ("activities", "Category / activity summaries"),
    ("validation", "Validation"),
    ("benchmarking", "Benchmarking"),
    ("provenance", "Factor provenance"),
    ("calculation", "Calculation information"),
    ("lineage", "Source lineage"),
    ("generation", "Generation metadata"),
)


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


@dataclass(frozen=True, slots=True)
class ReportContent:
    """Structured, JSON-serialisable report content (Phase 9C).

    ``sections`` is an ordered tuple of ``(section_id, title, payload)`` where
    every payload is a JSON-serialisable dict. :meth:`render` produces the
    domain :class:`ReportSection` objects (string content) and :meth:`to_dict`
    the full serialisable dict persisted into ``generated_content``.
    """

    sections: tuple[tuple[str, str, dict[str, Any]], ...] = ()

    def render(self) -> tuple[ReportSection, ...]:
        """Return the ordered domain sections with JSON-string content."""
        return tuple(
            ReportSection(
                section_id=section_id,
                title=title,
                content=json.dumps(
                    _jsonable(payload), separators=(",", ":"), sort_keys=True
                ),
                order=index,
            )
            for index, (section_id, title, payload) in enumerate(self.sections)
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the full serialisable content dict (by section id)."""
        return {
            section_id: _jsonable(payload)
            for section_id, _title, payload in self.sections
        }


@dataclass(frozen=True, slots=True)
class ReportGenerationResult:
    """The engine output: the persisted lifecycle record + structured content."""

    report: GeneratedReport
    content: ReportContent


# ---------------------------------------------------------------------------
# Repository / engine surfaces (protocols) — satisfied structurally by the
# production repositories/engines and by fakes in the unit suite.
# ---------------------------------------------------------------------------


class ReportsStore(Protocol):
    """The report-persistence surface (``ReportsRepository``)."""

    async def create_generation_request(
        self, org_id: str, report_type: str, year: int, template_id: Optional[str]
    ) -> GeneratedReport: ...

    async def complete_generation(
        self,
        report_id: str,
        storage_url: str,
        file_size: int,
        page_count: int,
        content: Optional[dict[str, Any]] = None,
    ) -> GeneratedReport: ...


class OrgSource(Protocol):
    """The organisations surface the engine reads (``OrganizationsRepository``)."""

    async def get(self, org_id: str) -> Optional[Organization]: ...

    async def get_metadata(self, org_id: str) -> Optional[OrganizationMetadata]: ...


class LogsSource(Protocol):
    """The emissions-log surface the engine reads (``EmissionsLogsRepository``)."""

    async def aggregate(
        self, org_id: str, period: DateRange, group_by: str
    ) -> EmissionsAggregate: ...

    async def find_by_org(self, org_id: str, period: DateRange) -> list[EmissionLog]: ...


class FactorLookup(Protocol):
    """The factor surface the engine reads (``EmissionFactorsRepository``)."""

    async def get(self, id: str) -> Optional[EmissionFactor]: ...


class ValidationSurface(Protocol):
    """The injected ValidationEngine surface (Phase 9A)."""

    async def validate(self, request: ValidationRequest) -> ValidationReport: ...


class BenchmarkingSurface(Protocol):
    """The injected BenchmarkingEngine surface (Phase 9B)."""

    async def benchmark(self, request: BenchmarkRequest) -> BenchmarkResult: ...


class CalculationSurface(Protocol):
    """The injected CalculationEngine verification surface (Phase 6)."""

    def verify(self, snapshot: CalculationSnapshot) -> VerificationResult: ...


class ReportGenerationEngine:
    """Structured report generation (Phase 9C).

    Args:
        reports_repo: Report-persistence surface (:class:`ReportsStore`).
        org_repo: Organisations surface (:class:`OrgSource`).
        logs_repo: Emissions-log surface (:class:`LogsSource`).
        factor_lookup: Optional factor surface (:class:`FactorLookup`), used for
            activity summaries and CO2/CO2e provenance.
        validation_engine: Optional injected ValidationEngine
            (:class:`ValidationSurface`).
        benchmarking_engine: Optional injected BenchmarkingEngine
            (:class:`BenchmarkingSurface`).
        calculation_engine: Optional injected CalculationEngine
            (:class:`CalculationSurface`), used to verify snapshot figures.
        event_bus: Optional bus receiving ``ReportGenerated``.
        audit_logger: Optional logger recording every generation.
    """

    def __init__(
        self,
        reports_repo: ReportsStore,
        org_repo: OrgSource,
        logs_repo: LogsSource,
        *,
        factor_lookup: Optional[FactorLookup] = None,
        validation_engine: Optional[ValidationSurface] = None,
        benchmarking_engine: Optional[BenchmarkingSurface] = None,
        calculation_engine: Optional[CalculationSurface] = None,
        event_bus: Optional[EventBus] = None,
        audit_logger: Optional[AuditLogger] = None,
    ) -> None:
        if reports_repo is None or org_repo is None or logs_repo is None:
            raise ValueError(
                "reports_repo, org_repo and logs_repo must not be None"
            )
        self._reports = reports_repo
        self._orgs = org_repo
        self._logs = logs_repo
        self._factors = factor_lookup
        self._validation = validation_engine
        self._benchmarking = benchmarking_engine
        self._calculation = calculation_engine
        self._event_bus = event_bus
        self._audit_logger = audit_logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(self, request: ReportRequest) -> ReportGenerationResult:
        """Build, persist and publish a structured report for ``request``.

        Raises:
            ValidationFailedError: When strict validation is configured and
                blocking errors exist (propagated from ValidationEngine).
            ReportGenerationFailedError: On any other engine failure.
        """
        try:
            content = await self.build_content(request)
        except ValidationFailedError:
            raise
        except ReportGenerationFailedError:
            raise
        except Exception as exc:  # noqa: BLE001 - wrap into the report error
            raise ReportGenerationFailedError(
                "report generation failed",
                details={
                    "organization_id": request.organization_id,
                    "report_type": request.report_type,
                    "reporting_year": request.reporting_year,
                },
            ) from exc

        rendered = content.render()
        content_dict = content.to_dict()
        report = await self._reports.create_generation_request(
            request.organization_id,
            request.report_type,
            request.reporting_year,
            request.template_id,
        )
        completed = await self._reports.complete_generation(
            report.id,
            storage_url="",
            file_size=len(json.dumps(content_dict).encode("utf-8")),
            page_count=len(rendered),
            content=content_dict,
        )
        await self._publish_report_generated(completed)
        await self._audit(completed, rendered)
        return ReportGenerationResult(report=completed, content=content)

    async def build_content(self, request: ReportRequest) -> ReportContent:
        """Compose the ordered structured sections for ``request``.

        Runs validation (strict contract respected), benchmarking (insufficient
        data caught and represented explicitly), aggregates the emissions
        figures, and labels every figure with its CO2/CO2e provenance.
        """
        org_id = request.organization_id
        year = request.reporting_year
        period = DateRange(date(year, 1, 1), date(year, 12, 31))

        org = await self._orgs.get(org_id)
        metadata = await self._orgs.get_metadata(org_id)
        aggregate = await self._logs.aggregate(org_id, period, "year")
        logs = await self._logs.find_by_org(org_id, period)
        factors = await self._load_factors(logs)

        validation_report = await self._validate(org_id, year, period, request)
        benchmark_payload = await self._benchmark(org_id, year, request)

        coverage, sources, factor_sets, countries = self._provenance(logs, factors)

        built = [
            self._metadata_section(request),
            self._organization_section(org, metadata),
            self._period_section(period),
            self._totals_section(aggregate, coverage, sources),
            self._scopes_section(aggregate, coverage, sources),
            self._activities_section(logs, factors, request),
            self._validation_section(validation_report),
            self._benchmarking_section(benchmark_payload),
            self._provenance_section(coverage, sources, factor_sets, countries),
            self._calculation_section(request, aggregate, coverage),
            self._lineage_section(request, logs, aggregate, factors),
            self._generation_section(request),
        ]
        return ReportContent(sections=tuple(self._ordered_sections(built, request)))

    # ------------------------------------------------------------------
    # Section builders (ordered, JSON-serialisable payloads)
    # ------------------------------------------------------------------

    def _metadata_section(self, request: ReportRequest) -> tuple[str, str, dict[str, Any]]:
        return (
            "metadata",
            "Report metadata",
            {
                "report_type": request.report_type,
                "reporting_year": request.reporting_year,
                "template_id": request.template_id,
                "organization_id": request.organization_id,
            },
        )

    def _organization_section(
        self, org: Optional[Organization], metadata: Optional[OrganizationMetadata]
    ) -> tuple[str, str, dict[str, Any]]:
        if org is None:
            return ("organization", "Organization", {"status": "not_found"})
        payload: dict[str, Any] = {
            "status": "found",
            "organization_id": org.id,
            "name": org.name,
            "country": org.country,
            "is_active": org.is_active,
        }
        if metadata is not None:
            payload["metadata"] = {
                "sector": metadata.sector,
                "fte_count": metadata.fte_count,
                "total_floor_area_sqm": metadata.total_floor_area_sqm,
                "annual_revenue_gbp": metadata.annual_revenue_gbp,
            }
        else:
            payload["metadata"] = {"status": "not_available"}
        return ("organization", "Organization", payload)

    def _period_section(self, period: DateRange) -> tuple[str, str, dict[str, Any]]:
        return (
            "period",
            "Reporting period",
            {
                "start_date": period.start_date.isoformat(),
                "end_date": period.end_date.isoformat(),
                "reporting_year": period.start_date.year,
            },
        )

    def _totals_section(
        self, aggregate: EmissionsAggregate, coverage: str, sources: set[str]
    ) -> tuple[str, str, dict[str, Any]]:
        source_label = ",".join(sorted(sources)) or "unknown"
        unit = f"kg {coverage}"
        if aggregate.total_rows == 0:
            return (
                "totals",
                "Emissions totals",
                {
                    "status": "insufficient_data",
                    "total_co2e_kg": None,
                    "unit": unit,
                    "source": source_label,
                    "note": "no emissions data in reporting period",
                },
            )
        return (
            "totals",
            "Emissions totals",
            {
                "status": "available",
                "total_co2e_kg": str(aggregate.total_co2e_kg),
                "unit": unit,
                "source": source_label,
                "total_rows": aggregate.total_rows,
            },
        )

    def _scopes_section(
        self, aggregate: EmissionsAggregate, coverage: str, sources: set[str]
    ) -> tuple[str, str, dict[str, Any]]:
        source_label = ",".join(sorted(sources)) or "unknown"
        scopes = {
            scope_label: {
                "co2e_kg": str(value),
                "unit": f"kg {coverage}",
            }
            for scope_label, value in sorted(aggregate.by_scope.items())
        }
        return (
            "scopes",
            "Scope summaries",
            {
                "status": "available" if scopes else "insufficient_data",
                "scopes": scopes,
                "unit": f"kg {coverage}",
                "source": source_label,
            },
        )

    def _activities_section(
        self,
        logs: list[EmissionLog],
        factors: dict[str, EmissionFactor],
        request: ReportRequest,
    ) -> tuple[str, str, dict[str, Any]]:
        groups: dict[str, list[EmissionLog]] = {}
        for log in logs:
            factor = factors.get(log.factor_id)
            if factor is None:
                continue
            groups.setdefault(factor.activity_type, []).append(log)
        if not groups:
            return (
                "activities",
                "Category / activity summaries",
                {
                    "status": "insufficient_data",
                    "activities": [],
                    "note": "no factor-resolved activity data in reporting period",
                },
            )
        activities = []
        for activity_type, group in groups.items():
            units = {log.unit for log in group}
            activities.append(
                {
                    "activity_type": activity_type,
                    "co2e_kg": str(sum((log.calculated_kg_co2e for log in group), Decimal("0"))),
                    "quantity": str(sum((log.quantity for log in group), Decimal("0"))),
                    "unit": next(iter(units)) if len(units) == 1 else "mixed",
                    "row_count": len(group),
                }
            )
        activities.sort(key=lambda item: Decimal(item["co2e_kg"]), reverse=True)
        top_n = int(request.options.get("top_activities", 10))
        return (
            "activities",
            "Category / activity summaries",
            {
                "status": "available",
                "activities": activities[:top_n],
                "total_activities": len(activities),
            },
        )

    def _validation_section(
        self, validation_report: Optional[ValidationReport]
    ) -> tuple[str, str, dict[str, Any]]:
        if validation_report is None:
            return (
                "validation",
                "Validation",
                {"status": "not_configured", "note": "validation engine not configured"},
            )
        return (
            "validation",
            "Validation",
            {
                "status": "passed" if validation_report.ok else "failed",
                "ok": validation_report.ok,
                "counts": validation_report.counts,
                "issues": [
                    {
                        "code": issue.code,
                        "severity": issue.severity.value,
                        "message": issue.message,
                        "entity_type": issue.entity_type,
                        "entity_id": issue.entity_id,
                        "field": issue.field,
                        "context": issue.context,
                    }
                    for issue in validation_report.issues
                ],
            },
        )

    def _benchmarking_section(
        self, payload: object
    ) -> tuple[str, str, dict[str, Any]]:
        if isinstance(payload, dict):
            return ("benchmarking", "Benchmarking", dict(payload))
        result = payload
        metrics = []
        for metric in result.metrics:
            metrics.append(
                {
                    "key": metric.key,
                    "label": metric.label,
                    "unit": metric.unit,
                    "status": metric.status.value,
                    "value": str(metric.value) if metric.value is not None else None,
                    "numerator": str(metric.numerator) if metric.numerator is not None else None,
                    "denominator": str(metric.denominator) if metric.denominator is not None else None,
                    "baseline_value": str(metric.baseline_value) if metric.baseline_value is not None else None,
                    "delta": str(metric.delta) if metric.delta is not None else None,
                    "delta_pct": str(metric.delta_pct) if metric.delta_pct is not None else None,
                    "comparison": metric.comparison,
                    "source": metric.source,
                    "scope": metric.scope,
                    "facility_id": metric.facility_id,
                    "activity_type": metric.activity_type,
                    "note": metric.note,
                }
            )
        return (
            "benchmarking",
            "Benchmarking",
            {
                "status": "available",
                "metrics": metrics,
                "by_scope": {key: str(value) for key, value in result.by_scope.items()},
            },
        )

    def _provenance_section(
        self,
        coverage: str,
        sources: set[str],
        factor_sets: set[str],
        countries: set[str],
    ) -> tuple[str, str, dict[str, Any]]:
        return (
            "provenance",
            "Factor provenance",
            {
                "gas_coverage": coverage,
                "factor_sources": sorted(sources),
                "factor_sets": sorted(factor_sets),
                "countries": sorted(countries),
                "note": (
                    "SEAI factors are CO2-only (CH4/N2O excluded by source design); "
                    "DEFRA factors are CO2e. Mixed aggregations are labelled "
                    "'CO2/CO2e mixed' and are never relabelled as full CO2e."
                ),
            },
        )

    def _calculation_section(
        self,
        request: ReportRequest,
        aggregate: EmissionsAggregate,
        coverage: str,
    ) -> tuple[str, str, dict[str, Any]]:
        verification: list[dict[str, Any]] = []
        verified = True
        snapshots = request.options.get("snapshots") or ()
        for snapshot in snapshots:
            if self._calculation is None:
                verification.append(
                    {
                        "snapshot_id": snapshot.id,
                        "status": "not_verified",
                        "note": "calculation engine not configured",
                    }
                )
                verified = False
                continue
            result = self._calculation.verify(snapshot)
            verification.append(
                {
                    "snapshot_id": snapshot.id,
                    "match": result.match,
                    "tampered": result.tampered,
                    "discrepancy": str(result.discrepancy)
                    if result.discrepancy is not None
                    else None,
                }
            )
            verified = verified and result.match and not result.tampered
        if aggregate.total_rows == 0:
            status = "insufficient_data"
        elif verification:
            status = "verified" if verified else "verification_failed"
        else:
            status = "available"
        return (
            "calculation",
            "Calculation information",
            {
                "status": status,
                "methodology": "direct_multiply",
                "algorithm_version": request.options.get("algorithm_version", "v1.0"),
                "figures_from": "emissions_logs_aggregation",
                "unit": f"kg {coverage}",
                "snapshot_verification": verification,
            },
        )

    def _lineage_section(
        self,
        request: ReportRequest,
        logs: list[EmissionLog],
        aggregate: EmissionsAggregate,
        factors: dict[str, EmissionFactor],
    ) -> tuple[str, str, dict[str, Any]]:
        return (
            "lineage",
            "Source lineage",
            {
                "emissions_logs": {
                    "count": len(logs),
                    "reporting_year": request.reporting_year,
                },
                "emission_factors": {
                    "resolved": len(factors),
                    "factor_ids": sorted(factors.keys()),
                },
                "aggregate": {
                    "total_rows": aggregate.total_rows,
                    "by_scope_count": len(aggregate.by_scope),
                },
                "source": "emissions_logs + emission_factors (read-only aggregation)",
            },
        )

    def _generation_section(
        self, request: ReportRequest
    ) -> tuple[str, str, dict[str, Any]]:
        return (
            "generation",
            "Generation metadata",
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "engine": "report_generation",
                "engine_version": ENGINE_VERSION,
                "template_id": request.template_id,
            },
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _provenance(
        self, logs: list[EmissionLog], factors: dict[str, EmissionFactor]
    ) -> tuple[str, set[str], set[str], set[str]]:
        """Return ``(coverage, sources, factor_sets, countries)`` for the data."""
        sources: set[str] = set()
        factor_sets: set[str] = set()
        countries: set[str] = set()
        coverages: set[str] = set()
        for factor in factors.values():
            if factor.factor_source:
                sources.add(factor.factor_source)
            if factor.factor_set:
                factor_sets.add(factor.factor_set)
            if factor.country:
                countries.add(factor.country)
            coverages.add(gas_coverage(factor))
        if coverages == {"CO2"}:
            coverage = "CO2"
        elif coverages == {"CO2e"}:
            coverage = "CO2e"
        elif coverages:
            coverage = "CO2/CO2e mixed"
        else:
            coverage = "unknown"
        return coverage, sources, factor_sets, countries

    async def _validate(
        self,
        org_id: str,
        year: int,
        period: DateRange,
        request: ReportRequest,
    ) -> Optional[ValidationReport]:
        """Run ValidationEngine; strict blocking errors propagate unchanged."""
        if self._validation is None:
            return None
        strict = bool(request.options.get("strict_validation", True))
        return await self._validation.validate(
            ValidationRequest(
                organization_id=org_id,
                reporting_year=year,
                period=period,
                strict=strict,
            )
        )

    async def _benchmark(
        self, org_id: str, year: int, request: ReportRequest
    ) -> object:
        """Run BenchmarkingEngine; insufficient data becomes an explicit payload."""
        if self._benchmarking is None:
            return {
                "status": "not_configured",
                "note": "benchmarking engine not configured",
            }
        benchmark_request = BenchmarkRequest(
            organization_id=org_id,
            reporting_year=year,
            compare_years=tuple(request.options.get("compare_years", ())),
            metrics=tuple(
                request.options.get(
                    "benchmark_metrics",
                    ("total", "per_fte", "per_area", "per_revenue", "activity_intensity"),
                )
            ),
            group_by=tuple(request.options.get("benchmark_group_by", ("scope",))),
        )
        try:
            return await self._benchmarking.benchmark(benchmark_request)
        except BenchmarkDataInsufficientError as exc:
            return {"status": "insufficient_data", "detail": str(exc)}

    def _ordered_sections(
        self,
        built: list[tuple[str, str, dict[str, Any]]],
        request: ReportRequest,
    ) -> list[tuple[str, str, dict[str, Any]]]:
        """Order the built sections by the template skeleton when provided."""
        template_order = self._template_order(request)
        if not template_order:
            return built
        by_id = {section_id: payload for section_id, _title, payload in built}
        titles = {section_id: title for section_id, title, _payload in built}
        ordered: list[tuple[str, str, dict[str, Any]]] = []
        seen: set[str] = set()
        for section_id in template_order:
            if section_id in by_id and section_id not in seen:
                ordered.append((section_id, titles[section_id], by_id[section_id]))
                seen.add(section_id)
        for section_id, title, payload in built:
            if section_id not in seen:
                ordered.append((section_id, title, payload))
        return ordered

    def _template_order(self, request: ReportRequest) -> Optional[tuple[str, ...]]:
        template = request.options.get("template")
        if isinstance(template, ReportTemplate) and template.structure:
            return tuple(section.section_id for section in template.structure)
        if request.sections:
            return tuple(section.section_id for section in request.sections)
        return None

    async def _load_factors(
        self, logs: list[EmissionLog]
    ) -> dict[str, EmissionFactor]:
        """Resolve the distinct factor ids referenced by ``logs``."""
        if self._factors is None:
            return {}
        factors: dict[str, EmissionFactor] = {}
        for log in logs:
            if log.factor_id in factors:
                continue
            factor = await self._factors.get(log.factor_id)
            if factor is not None:
                factors[log.factor_id] = factor
        return factors

    async def _publish_report_generated(self, report: GeneratedReport) -> None:
        """Publish ``ReportGenerated`` (fire-and-forget)."""
        if self._event_bus is None:
            return
        event = ReportGenerated(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(timezone.utc),
            correlation_id=report.id,
            report_id=report.id,
            organization_id=report.organization_id,
            storage_url=report.storage_url,
        )
        try:
            await self._event_bus.publish(event)
        except Exception:  # noqa: BLE001 - side effects must not break generation
            logger.exception(
                "failed to publish ReportGenerated for report %s", report.id
            )

    async def _audit(
        self, report: GeneratedReport, sections: tuple[ReportSection, ...]
    ) -> None:
        """Record the generation (CT-ARCH-014)."""
        if self._audit_logger is None:
            return
        try:
            await self._audit_logger.log_action(
                action="report:generated",
                entity_type="report",
                entity_id=report.id,
                correlation_id=report.id,
                actor="report_generation_engine",
                after={
                    "report_type": report.report_type,
                    "reporting_year": report.reporting_year,
                    "sections": [section.section_id for section in sections],
                    "page_count": len(sections),
                },
            )
        except Exception:  # noqa: BLE001 - audit must not break generation
            logger.exception("failed to audit report generation %s", report.id)







