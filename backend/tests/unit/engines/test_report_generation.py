"""Unit tests for engines.report_generation (Phase 9C — ReportGenerationEngine).

Covers basic generation, organisation/period/totals/scopes/activities sections,
ValidationEngine integration (results, warnings, strict blocking failures),
BenchmarkingEngine integration (availability states, insufficient data), the
mandatory CO2/CO2e provenance rules (SEAI CO2-only / DEFRA CO2e / mixed),
calculation-snapshot verification, source lineage, empty/insufficient input,
serialisation, repository persistence, EventBus + AuditLogger side effects, the
no-database-side-effects guarantee, engine-failure wrapping, and Phase 9A / 9B
regressions with the real engines injected.

All repository surfaces are fakes; no database is touched.
"""
from __future__ import annotations

import dataclasses
import json
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import pytest

from core.exceptions import (
    BenchmarkDataInsufficientError,
    ReportGenerationFailedError,
    ValidationFailedError,
)
from core.types import DateRange
from domain.audit import AuditEntry
from domain.benchmarking import (
    BenchmarkAvailability,
    BenchmarkMetric,
    BenchmarkRequest,
    BenchmarkResult,
)
from domain.calculation import (
    CalculationSnapshot,
    EmissionLog,
    EmissionsAggregate,
    VerificationResult,
)
from domain.factor import RESULT_PRECISION, EmissionFactor
from domain.organization import Asset, Facility, Organization, OrganizationMetadata
from domain.report import GeneratedReport, ReportRequest, ReportSection, ReportTemplate
from domain.validation import (
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
    ValidationSeverity,
)
from domain.workflow import ReportGenerated

from engines.benchmarking import BenchmarkingEngine
from engines.report_generation import ReportGenerationEngine
from engines.validation import ValidationEngine
from infra.event_bus import EventBus

_SEAI_ELECTRICITY = "Fuels > Electricity > Electricity consumption (kg CO2) [kWh]"
_DEFRA_GAS = "Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]"
_SEAI_BATCH = "9e3b2c8a-1d4f-4e6b-8a7c-2f5d6e7a8b9c"

#: The full default ordered section set produced by the engine.
DEFAULT_SECTIONS = [
    "metadata", "organization", "period", "totals", "scopes", "activities",
    "validation", "benchmarking", "provenance", "calculation", "lineage",
    "generation",
]


def make_factor(**kwargs: Any) -> EmissionFactor:
    return EmissionFactor(
        id=str(kwargs.get("id") or f"f-{uuid.uuid4().hex[:12]}"),
        reporting_year=int(kwargs.get("year", 2025)),
        activity_type=str(kwargs.get("activity_type") or _DEFRA_GAS),
        co2e_multiplier=Decimal(str(kwargs.get("multiplier") or "0.18400")),
        unit=kwargs.get("unit") or "kWh",
        scope=kwargs.get("scope") or "Scope 1",
        factor_source=str(kwargs.get("factor_source") or "DEFRA-DESNZ"),
        factor_set=str(kwargs.get("factor_set") or "DEFRA-2025"),
        country=str(kwargs.get("country") or "GB"),
        provider_key=str(kwargs.get("provider") or "defra"),
        import_batch_id=kwargs.get("import_batch_id"),
        natural_key=(),
    )


def make_seai(**kwargs: Any) -> EmissionFactor:
    return make_factor(
        activity_type=_SEAI_ELECTRICITY,
        factor_source="SEAI",
        factor_set="SEAI-2025",
        country="IE",
        provider="seai",
        scope="Scope 2",
        multiplier="0.197803384",
        unit="kWh",
        import_batch_id=_SEAI_BATCH,
        **kwargs,
    )


def make_log(**kwargs: Any) -> EmissionLog:
    factor = kwargs.get("factor")
    return EmissionLog(
        id=str(kwargs.get("id") or f"log-{uuid.uuid4().hex[:8]}"),
        organization_id=str(kwargs.get("organization_id") or "org-1"),
        factor_id=str(kwargs.get("factor_id") or (factor.id if factor else "f-1")),
        quantity=Decimal(str(kwargs.get("quantity") or "100")),
        date=kwargs.get("date", date(2025, 6, 1)),
        unit=kwargs.get("unit", factor.unit if factor else "kWh"),
        scope=kwargs.get("scope", factor.scope if factor else "Scope 1"),
        asset_id=kwargs.get("asset_id"),
        facility_id=kwargs.get("facility_id"),
        snapshot_id=kwargs.get("snapshot_id"),
        calculated_kg_co2e=Decimal(str(kwargs.get("calculated_kg_co2e") or "0")),
    )


def make_snapshot(**kwargs: Any) -> CalculationSnapshot:
    factor = kwargs.get("factor")
    quantity = Decimal(str(kwargs.get("quantity") or "100"))
    multiplier = Decimal(
        str(kwargs.get("multiplier") or (factor.co2e_multiplier if factor else "0.18400"))
    )
    co2e_kg = kwargs.get("co2e_kg")
    if co2e_kg is None:
        co2e_kg = (quantity * multiplier).quantize(RESULT_PRECISION)
    snapshot = CalculationSnapshot(
        id=str(kwargs.get("id") or f"snap-{uuid.uuid4().hex[:8]}"),
        match_request_id=str(kwargs.get("match_request_id") or "match-1"),
        organization_id=str(kwargs.get("organization_id") or "org-1"),
        factor_id=str(kwargs.get("factor_id") or (factor.id if factor else "f-1")),
        quantity=quantity,
        quantity_unit=str(kwargs.get("quantity_unit") or (factor.unit if factor else "kWh")),
        co2e_multiplier=multiplier,
        co2e_kg=Decimal(str(co2e_kg)),
        scope=kwargs.get("scope", factor.scope if factor else "Scope 1"),
        date=kwargs.get("date", date(2025, 6, 1)),
        reporting_year=int(kwargs.get("reporting_year") or 2025),
        methodology=str(kwargs.get("methodology") or "direct_multiply"),
        algorithm_version=str(kwargs.get("algorithm_version") or "v1.0"),
        created_at=kwargs.get("created_at", date(2025, 6, 1)),
        content_hash=str(kwargs.get("content_hash") or ""),
    )
    if not snapshot.content_hash:
        snapshot = dataclasses.replace(snapshot, content_hash=snapshot.build_content_hash())
    return snapshot


def make_org(**kwargs: Any) -> Organization:
    return Organization(
        id=str(kwargs.get("id") or "org-1"),
        name=str(kwargs.get("name") or "Test Co"),
        country=str(kwargs.get("country") or "GB"),
        is_active=bool(kwargs.get("is_active", True)),
        created_at=kwargs.get("created_at", datetime.now()),
    )


def make_metadata(**kwargs: Any) -> OrganizationMetadata:
    return OrganizationMetadata(
        total_floor_area_sqm=kwargs.get("total_floor_area_sqm"),
        occupied_floor_area_sqm=kwargs.get("occupied_floor_area_sqm"),
        fte_count=kwargs.get("fte_count"),
        annual_revenue_gbp=kwargs.get("annual_revenue_gbp"),
        sector=kwargs.get("sector"),
    )


def make_facility(facility_id: str = "fac-1", org_id: str = "org-1") -> Facility:
    return Facility(id=facility_id, organization_id=org_id, name="Facility 1", address="")


def make_asset(asset_id: str = "asset-1", org_id: str = "org-1") -> Asset:
    return Asset(
        id=asset_id,
        facility_id="fac-1",
        organization_id=org_id,
        name="Asset 1",
        asset_type="boiler",
    )


def make_request(**kwargs: Any) -> ReportRequest:
    return ReportRequest(
        organization_id=str(kwargs.get("organization_id") or "org-1"),
        report_type=str(kwargs.get("report_type") or "annual"),
        reporting_year=int(kwargs.get("reporting_year") or 2025),
        template_id=kwargs.get("template_id"),
        sections=tuple(kwargs.get("sections") or ()),
        options=dict(kwargs.get("options") or {}),
    )


def make_benchmark_result(
    metrics: Optional[list[BenchmarkMetric]] = None,
) -> BenchmarkResult:
    return BenchmarkResult(
        organization_id="org-1",
        reporting_year=2025,
        metrics=tuple(
            metrics
            or [
                BenchmarkMetric(
                    key="total",
                    label="Total emissions",
                    unit="kg CO2e",
                    status=BenchmarkAvailability.AVAILABLE,
                    value=Decimal("18.40"),
                    numerator=Decimal("18.40"),
                    comparison="2025",
                    source="DEFRA-DESNZ",
                )
            ]
        ),
        by_scope={"Scope 1": Decimal("18.40")},
    )


class _FakeLogs:
    """In-memory LogsSource; aggregates are computed from the stored logs."""

    def __init__(self, logs: Optional[list[EmissionLog]] = None) -> None:
        self.logs = list(logs or [])
        self.aggregate_calls: list[tuple[str, DateRange, str]] = []
        self.find_calls: list[tuple[str, DateRange]] = []

    def _in_period(self, org_id: str, period: DateRange) -> list[EmissionLog]:
        return [
            log
            for log in self.logs
            if log.organization_id == org_id and period.contains(log.date)
        ]

    async def find_by_org(self, org_id: str, period: DateRange) -> list[EmissionLog]:
        self.find_calls.append((org_id, period))
        return self._in_period(org_id, period)

    async def aggregate(
        self, org_id: str, period: DateRange, group_by: str
    ) -> EmissionsAggregate:
        self.aggregate_calls.append((org_id, period, group_by))
        logs = self._in_period(org_id, period)
        by_scope: dict[str, Decimal] = {}
        for log in logs:
            key = log.scope or "none"
            by_scope[key] = by_scope.get(key, Decimal("0")) + log.calculated_kg_co2e
        total = sum((log.calculated_kg_co2e for log in logs), Decimal("0"))
        return EmissionsAggregate(
            organization_id=org_id,
            period=period,
            group_by=group_by,
            total_co2e_kg=total,
            total_rows=len(logs),
            by_scope=by_scope,
            by_group={},
        )


class _FakeOrgs:
    """In-memory OrgSource with call tracking (reads only)."""

    def __init__(
        self,
        org: Optional[Organization] = None,
        metadata: Optional[OrganizationMetadata] = None,
        facilities: Optional[list[Facility]] = None,
        assets: Optional[list[Asset]] = None,
    ) -> None:
        self.org = org
        self.metadata = metadata
        self.facilities = list(facilities or [])
        self.assets = list(assets or [])
        self.calls: list[str] = []

    async def get(self, org_id: str) -> Optional[Organization]:
        self.calls.append("get")
        return self.org

    async def get_metadata(self, org_id: str) -> Optional[OrganizationMetadata]:
        self.calls.append("get_metadata")
        return self.metadata

    async def get_facilities(self, org_id: str) -> list[Facility]:
        self.calls.append("get_facilities")
        return self.facilities

    async def get_assets(self, org_id: str) -> list[Asset]:
        self.calls.append("get_assets")
        return self.assets


class _FakeFactors:
    """In-memory FactorLookup with call tracking (reads only)."""

    def __init__(self, factors: Optional[list[EmissionFactor]] = None) -> None:
        self.factors = {f.id: f for f in (factors or [])}
        self.get_calls: list[str] = []

    async def get(self, factor_id: str) -> Optional[EmissionFactor]:
        self.get_calls.append(factor_id)
        return self.factors.get(factor_id)


class _FakeReports:
    """In-memory ReportsStore; records every persistence call."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.created: list[GeneratedReport] = []
        self.completed: list[GeneratedReport] = []
        self.persisted_content: Optional[dict[str, Any]] = None
        self.completed_kwargs: list[dict[str, Any]] = []

    async def create_generation_request(
        self, org_id: str, report_type: str, year: int, template_id: Optional[str]
    ) -> GeneratedReport:
        self.calls.append("create_generation_request")
        report = GeneratedReport(
            id=f"report-{len(self.created) + 1}",
            organization_id=org_id,
            report_type=report_type,
            reporting_year=year,
            storage_url="",
            file_size_bytes=0,
            generated_at=datetime.now(timezone.utc),
            page_count=0,
        )
        self.created.append(report)
        return report

    async def complete_generation(
        self,
        report_id: str,
        storage_url: str,
        file_size: int,
        page_count: int,
        content: Optional[dict[str, Any]] = None,
    ) -> GeneratedReport:
        self.calls.append("complete_generation")
        previous = self.created[-1] if self.created else None
        report = GeneratedReport(
            id=report_id,
            organization_id=previous.organization_id if previous else "org-1",
            report_type=previous.report_type if previous else "annual",
            reporting_year=previous.reporting_year if previous else 2025,
            storage_url=storage_url,
            file_size_bytes=file_size,
            generated_at=datetime.now(timezone.utc),
            page_count=page_count,
        )
        self.persisted_content = dict(content or {})
        self.completed_kwargs.append(
            {
                "storage_url": storage_url,
                "file_size": file_size,
                "page_count": page_count,
                "content": content,
            }
        )
        self.completed.append(report)
        return report


class _FakeValidation:
    """In-memory ValidationSurface; returns a preset report or raises."""

    def __init__(
        self,
        report: Optional[ValidationReport] = None,
        error: Optional[Exception] = None,
    ) -> None:
        self.report = report if report is not None else ValidationReport()
        self.error = error
        self.requests: list[ValidationRequest] = []

    async def validate(self, request: ValidationRequest) -> ValidationReport:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.report


class _FakeBenchmarking:
    """In-memory BenchmarkingSurface; returns a preset result or raises."""

    def __init__(
        self,
        result: Optional[BenchmarkResult] = None,
        error: Optional[Exception] = None,
    ) -> None:
        self.result = result if result is not None else make_benchmark_result()
        self.error = error
        self.requests: list[BenchmarkRequest] = []

    async def benchmark(self, request: BenchmarkRequest) -> BenchmarkResult:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.result


class _FakeCalculation:
    """Replicates CalculationEngine.verify for snapshot checks."""

    def __init__(self) -> None:
        self.verified: list[CalculationSnapshot] = []

    def verify(self, snapshot: CalculationSnapshot) -> VerificationResult:
        self.verified.append(snapshot)
        recomputed = (snapshot.quantity * snapshot.co2e_multiplier).quantize(
            RESULT_PRECISION
        )
        match = snapshot.verify_reproducibility(recomputed)
        tampered = bool(snapshot.content_hash) and snapshot.content_hash != (
            snapshot.build_content_hash()
        )
        return VerificationResult(
            match=match,
            discrepancy=None if match else recomputed - snapshot.co2e_kg,
            tampered=tampered,
        )


class _AuditSink:
    """In-memory audit sink satisfying the AuditLogger surface."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    async def log_action(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        correlation_id: str,
        actor: Optional[str] = None,
        changed_fields: Optional[dict[str, Any]] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        before: Any = None,
        after: Any = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor or "system",
            occurred_at=datetime.now(timezone.utc),
            changed_fields=dict(changed_fields or {}),
            reason=reason,
            ip_address=ip_address,
            before=before,
            after=after,
        )
        self.entries.append(entry)
        return entry


def make_engine(
    *,
    reports: Optional[_FakeReports] = None,
    logs: Optional[_FakeLogs] = None,
    orgs: Optional[_FakeOrgs] = None,
    factors: Optional[_FakeFactors] = None,
    validation: Any = None,
    benchmarking: Any = None,
    calculation: Any = None,
    event_bus: Optional[EventBus] = None,
    audit_logger: Any = None,
) -> tuple[ReportGenerationEngine, _FakeReports]:
    """Build a ReportGenerationEngine over fakes; return ``(engine, reports)``."""
    reports = reports or _FakeReports()
    engine = ReportGenerationEngine(
        reports,
        orgs or _FakeOrgs(),
        logs or _FakeLogs(),
        factor_lookup=factors,
        validation_engine=validation,
        benchmarking_engine=benchmarking,
        calculation_engine=calculation,
        event_bus=event_bus,
        audit_logger=audit_logger,
    )
    return engine, reports


def default_fixtures() -> tuple[_FakeLogs, _FakeOrgs, _FakeFactors]:
    """A one-DEFRA-log dataset with org profile data."""
    factor = make_factor()
    logs = _FakeLogs(
        [
            make_log(
                factor=factor,
                facility_id="fac-1",
                calculated_kg_co2e=Decimal("18.40"),
            )
        ]
    )
    orgs = _FakeOrgs(
        org=make_org(name="Test Co", country="GB"),
        metadata=make_metadata(
            fte_count=10,
            total_floor_area_sqm=100.0,
            annual_revenue_gbp=1000.0,
            sector="Manufacturing",
        ),
        facilities=[make_facility("fac-1")],
        assets=[make_asset()],
    )
    factors = _FakeFactors([factor])
    return logs, orgs, factors


class TestBasicGeneration:
    async def test_basic_report_generation(self) -> None:
        logs, orgs, factors = default_fixtures()
        engine, reports = make_engine(
            logs=logs,
            orgs=orgs,
            factors=factors,
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        result = await engine.generate(make_request())

        assert result.report.id == "report-1"
        assert result.report.organization_id == "org-1"
        assert result.report.report_type == "annual"
        assert result.report.reporting_year == 2025
        assert result.report.storage_url == ""
        assert result.report.page_count == 12
        assert result.report.file_size_bytes > 0

        ids = [s.section_id for s in result.content.render()]
        assert ids == DEFAULT_SECTIONS

        data = result.content.to_dict()
        assert data["totals"]["status"] == "available"
        assert data["validation"]["status"] == "passed"
        assert data["benchmarking"]["status"] == "available"

    async def test_template_ordering(self) -> None:
        logs, orgs, factors = default_fixtures()
        engine, _reports = make_engine(
            logs=logs,
            orgs=orgs,
            factors=factors,
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        template = ReportTemplate(
            id="tpl-1",
            name="Executive",
            report_type="annual",
            structure=(
                ReportSection(section_id="totals", title="Emissions totals", content="", order=0),
                ReportSection(section_id="validation", title="Validation", content="", order=1),
                ReportSection(section_id="benchmarking", title="Benchmarking", content="", order=2),
            ),
        )
        content = await engine.build_content(make_request(options={"template": template}))
        ids = [s.section_id for s in content.render()]
        assert ids.index("totals") == 0
        assert ids.index("validation") == 1
        assert ids.index("benchmarking") == 2
        assert len(ids) == 12

    async def test_organization_metadata(self) -> None:
        logs, orgs, factors = default_fixtures()
        engine, _reports = make_engine(
            logs=logs,
            orgs=orgs,
            factors=factors,
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        data = (await engine.build_content(make_request())).to_dict()
        org = data["organization"]
        assert org["status"] == "found"
        assert org["name"] == "Test Co"
        assert org["country"] == "GB"
        assert org["metadata"]["sector"] == "Manufacturing"
        assert org["metadata"]["fte_count"] == 10

    async def test_reporting_period(self) -> None:
        logs, orgs, factors = default_fixtures()
        engine, _reports = make_engine(
            logs=logs, orgs=orgs, factors=factors,
            validation=_FakeValidation(), benchmarking=_FakeBenchmarking(),
        )
        data = (await engine.build_content(make_request())).to_dict()
        period = data["period"]
        assert period["start_date"] == "2025-01-01"
        assert period["end_date"] == "2025-12-31"
        assert period["reporting_year"] == 2025

    async def test_total_emissions(self) -> None:
        factor = make_factor()
        logs = _FakeLogs(
            [
                make_log(factor=factor, calculated_kg_co2e=Decimal("10")),
                make_log(factor=factor, scope="Scope 2", calculated_kg_co2e=Decimal("5.5")),
            ]
        )
        engine, _reports = make_engine(
            logs=logs,
            orgs=_FakeOrgs(org=make_org()),
            factors=_FakeFactors([factor]),
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        data = (await engine.generate(make_request())).content.to_dict()
        totals = data["totals"]
        assert totals["status"] == "available"
        assert totals["total_co2e_kg"] == "15.5"
        assert totals["total_rows"] == 2
        assert totals["unit"] == "kg CO2e"

    async def test_scope_summaries(self) -> None:
        factor = make_factor()
        logs = _FakeLogs(
            [
                make_log(factor=factor, calculated_kg_co2e=Decimal("10")),
                make_log(factor=factor, scope="Scope 2", calculated_kg_co2e=Decimal("5.5")),
            ]
        )
        engine, _reports = make_engine(
            logs=logs,
            orgs=_FakeOrgs(org=make_org()),
            factors=_FakeFactors([factor]),
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        data = (await engine.generate(make_request())).content.to_dict()
        scopes = data["scopes"]
        assert scopes["status"] == "available"
        assert scopes["scopes"]["Scope 1"]["co2e_kg"] == "10"
        assert scopes["scopes"]["Scope 2"]["co2e_kg"] == "5.5"

    async def test_activity_summaries(self) -> None:
        gas = make_factor()
        electricity = make_seai()
        logs = _FakeLogs(
            [
                make_log(factor=gas, calculated_kg_co2e=Decimal("10")),
                make_log(factor=gas, calculated_kg_co2e=Decimal("2")),
                make_log(factor=electricity, calculated_kg_co2e=Decimal("7")),
            ]
        )
        engine, _reports = make_engine(
            logs=logs,
            orgs=_FakeOrgs(org=make_org()),
            factors=_FakeFactors([gas, electricity]),
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        data = (await engine.generate(make_request())).content.to_dict()
        activities = data["activities"]
        assert activities["status"] == "available"
        assert activities["total_activities"] == 2
        # highest-emitting activity first (12.00 > 7.00)
        assert activities["activities"][0]["activity_type"] == gas.activity_type
        assert activities["activities"][0]["co2e_kg"] == "12"
        assert activities["activities"][0]["quantity"] == "200"
        assert activities["activities"][0]["row_count"] == 2


class TestValidationIntegration:
    async def test_validation_results_passed(self) -> None:
        engine, _reports = make_engine(
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        data = (await engine.generate(make_request())).content.to_dict()
        validation = data["validation"]
        assert validation["status"] == "passed"
        assert validation["ok"] is True
        assert validation["counts"]["error"] == 0
        assert validation["issues"] == []

    async def test_validation_warnings_included(self) -> None:
        issues = (
            ValidationIssue(
                code="VAL_CALC_ROUNDING_TOLERANCE",
                severity=ValidationSeverity.WARNING,
                message="result differs from stored value within tolerance",
                entity_type="calculation_snapshot",
                entity_id="snap-1",
            ),
        )
        engine, reports = make_engine(
            validation=_FakeValidation(report=ValidationReport(issues=issues)),
            benchmarking=_FakeBenchmarking(),
        )
        result = await engine.generate(make_request())
        validation = result.content.to_dict()["validation"]
        assert validation["status"] == "passed"
        assert validation["counts"]["warning"] == 1
        assert validation["issues"][0]["severity"] == "warning"
        assert validation["issues"][0]["code"] == "VAL_CALC_ROUNDING_TOLERANCE"
        assert len(reports.completed) == 1

    async def test_validation_failures_block_generation(self) -> None:
        error = ValidationFailedError(
            "validation failed with blocking errors",
            details={"errors": ["VAL_ORG_NOT_FOUND"]},
        )
        engine, reports = make_engine(
            validation=_FakeValidation(error=error),
            benchmarking=_FakeBenchmarking(),
        )
        with pytest.raises(ValidationFailedError):
            await engine.generate(make_request())
        # strict failure must not persist anything
        assert reports.calls == []
        assert reports.created == []

    async def test_validation_not_configured(self) -> None:
        engine, _reports = make_engine(benchmarking=_FakeBenchmarking())
        validation = (await engine.build_content(make_request())).to_dict()["validation"]
        assert validation["status"] == "not_configured"

    async def test_engine_failure_wrapped(self) -> None:
        engine, reports = make_engine(
            validation=_FakeValidation(error=RuntimeError("boom")),
            benchmarking=_FakeBenchmarking(),
        )
        with pytest.raises(ReportGenerationFailedError):
            await engine.generate(make_request())
        assert reports.calls == []


class TestBenchmarkingIntegration:
    async def test_benchmark_results_available(self) -> None:
        metric = BenchmarkMetric(
            key="total",
            label="Total emissions",
            unit="kg CO2e",
            status=BenchmarkAvailability.AVAILABLE,
            value=Decimal("18.40"),
            numerator=Decimal("18.40"),
            comparison="2025",
            source="DEFRA-DESNZ",
        )
        result = BenchmarkResult(
            organization_id="org-1",
            reporting_year=2025,
            metrics=(metric,),
            by_scope={"Scope 1": Decimal("18.40")},
        )
        engine, _reports = make_engine(
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(result=result),
        )
        data = (await engine.generate(make_request())).content.to_dict()
        benchmark = data["benchmarking"]
        assert benchmark["status"] == "available"
        assert benchmark["metrics"][0]["key"] == "total"
        assert benchmark["metrics"][0]["value"] == "18.40"
        assert benchmark["by_scope"]["Scope 1"] == "18.40"

    async def test_unavailable_benchmark_metric_not_zeroed(self) -> None:
        unavailable = BenchmarkMetric(
            key="per_fte",
            label="Emissions per FTE",
            unit="kg CO2 per FTE",
            status=BenchmarkAvailability.NOT_AVAILABLE,
            value=None,
            source="DEFRA-DESNZ",
        )
        zero_denom = BenchmarkMetric(
            key="per_area",
            label="Emissions per floor area",
            unit="kg CO2 per sqm",
            status=BenchmarkAvailability.ZERO_DENOMINATOR,
            value=None,
            denominator=Decimal("0"),
            source="DEFRA-DESNZ",
        )
        result = BenchmarkResult(
            organization_id="org-1",
            reporting_year=2025,
            metrics=(unavailable, zero_denom),
        )
        engine, _reports = make_engine(
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(result=result),
        )
        data = (await engine.generate(make_request())).content.to_dict()
        metrics = {m["key"]: m for m in data["benchmarking"]["metrics"]}
        assert metrics["per_fte"]["status"] == "not_available"
        assert metrics["per_fte"]["value"] is None
        assert metrics["per_fte"]["value"] != "0"
        assert metrics["per_area"]["status"] == "zero_denominator"
        assert metrics["per_area"]["value"] is None
        assert metrics["per_area"]["denominator"] == "0"

    async def test_insufficient_benchmark_data_caught(self) -> None:
        engine, reports = make_engine(
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(
                error=BenchmarkDataInsufficientError("no emissions data in period")
            ),
        )
        result = await engine.generate(make_request())
        benchmark = result.content.to_dict()["benchmarking"]
        assert benchmark["status"] == "insufficient_data"
        assert "no emissions data" in benchmark["detail"]
        assert len(reports.completed) == 1

    async def test_benchmarking_not_configured(self) -> None:
        engine, _reports = make_engine(validation=_FakeValidation())
        benchmark = (await engine.build_content(make_request())).to_dict()["benchmarking"]
        assert benchmark["status"] == "not_configured"


class TestProvenance:
    async def test_seai_co2_only_report(self) -> None:
        seai = make_seai()
        logs = _FakeLogs(
            [make_log(factor=seai, calculated_kg_co2e=Decimal("19.780338"))]
        )
        engine, _reports = make_engine(
            logs=logs,
            orgs=_FakeOrgs(org=make_org(country="IE")),
            factors=_FakeFactors([seai]),
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        data = (await engine.generate(make_request())).content.to_dict()
        assert data["totals"]["unit"] == "kg CO2"
        assert data["provenance"]["gas_coverage"] == "CO2"
        assert data["provenance"]["factor_sources"] == ["SEAI"]
        assert data["provenance"]["factor_sets"] == ["SEAI-2025"]
        assert "CO2e" not in data["totals"]["unit"]
        assert "CO2e" not in data["provenance"]["gas_coverage"]

    async def test_defra_co2e_report(self) -> None:
        factor = make_factor()
        logs = _FakeLogs(
            [make_log(factor=factor, calculated_kg_co2e=Decimal("18.40"))]
        )
        engine, _reports = make_engine(
            logs=logs,
            orgs=_FakeOrgs(org=make_org()),
            factors=_FakeFactors([factor]),
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        data = (await engine.generate(make_request())).content.to_dict()
        assert data["totals"]["unit"] == "kg CO2e"
        assert data["provenance"]["gas_coverage"] == "CO2e"
        assert data["provenance"]["factor_sources"] == ["DEFRA-DESNZ"]

    async def test_mixed_seai_and_defra_provenance(self) -> None:
        seai = make_seai()
        defra = make_factor()
        logs = _FakeLogs(
            [
                make_log(factor=seai, calculated_kg_co2e=Decimal("19.78")),
                make_log(factor=defra, calculated_kg_co2e=Decimal("18.40")),
            ]
        )
        engine, _reports = make_engine(
            logs=logs,
            orgs=_FakeOrgs(org=make_org()),
            factors=_FakeFactors([seai, defra]),
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        data = (await engine.generate(make_request())).content.to_dict()
        assert data["provenance"]["gas_coverage"] == "CO2/CO2e mixed"
        assert data["totals"]["unit"] == "kg CO2/CO2e mixed"
        assert sorted(data["provenance"]["factor_sources"]) == ["DEFRA-DESNZ", "SEAI"]
        assert sorted(data["provenance"]["factor_sets"]) == ["DEFRA-2025", "SEAI-2025"]
        assert sorted(data["provenance"]["countries"]) == ["GB", "IE"]

    async def test_factor_source_and_factor_set_provenance(self) -> None:
        factor = make_factor(
            factor_source="DEFRA-DESNZ", factor_set="DEFRA-2025", country="GB"
        )
        logs = _FakeLogs(
            [make_log(factor=factor, calculated_kg_co2e=Decimal("1"))]
        )
        engine, _reports = make_engine(
            logs=logs,
            orgs=_FakeOrgs(org=make_org()),
            factors=_FakeFactors([factor]),
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        provenance = (await engine.generate(make_request())).content.to_dict()["provenance"]
        assert provenance["factor_sources"] == ["DEFRA-DESNZ"]
        assert provenance["factor_sets"] == ["DEFRA-2025"]
        assert provenance["countries"] == ["GB"]


class TestCalculationAndLineage:
    async def test_calculation_snapshot_verification(self) -> None:
        factor = make_factor()
        snapshot = make_snapshot(factor=factor)
        logs = _FakeLogs(
            [make_log(factor=factor, calculated_kg_co2e=snapshot.co2e_kg)]
        )
        engine, _reports = make_engine(
            logs=logs,
            orgs=_FakeOrgs(org=make_org()),
            factors=_FakeFactors([factor]),
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
            calculation=_FakeCalculation(),
        )
        data = (await engine.build_content(
            make_request(options={"snapshots": [snapshot]})
        )).to_dict()
        calc = data["calculation"]
        assert calc["status"] == "verified"
        assert calc["methodology"] == "direct_multiply"
        assert calc["snapshot_verification"][0]["snapshot_id"] == snapshot.id
        assert calc["snapshot_verification"][0]["match"] is True
        assert calc["snapshot_verification"][0]["tampered"] is False

    async def test_calculation_snapshot_tamper_detected(self) -> None:
        factor = make_factor()
        snapshot = make_snapshot(factor=factor)
        # Stale content_hash / altered figure => tampered + mismatch.
        tampered = dataclasses.replace(
            snapshot,
            co2e_kg=snapshot.co2e_kg + Decimal("1"),
            content_hash="deadbeef",
        )
        engine, _reports = make_engine(
            logs=_FakeLogs(
                [make_log(factor=factor, calculated_kg_co2e=snapshot.co2e_kg)]
            ),
            orgs=_FakeOrgs(org=make_org()),
            factors=_FakeFactors([factor]),
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
            calculation=_FakeCalculation(),
        )
        data = (await engine.build_content(
            make_request(options={"snapshots": [tampered]})
        )).to_dict()
        calc = data["calculation"]
        assert calc["status"] == "verification_failed"
        verification = calc["snapshot_verification"][0]
        assert verification["match"] is False
        assert verification["tampered"] is True

    async def test_source_lineage(self) -> None:
        factor = make_factor()
        logs = _FakeLogs(
            [
                make_log(factor=factor, calculated_kg_co2e=Decimal("10")),
                make_log(factor=factor, calculated_kg_co2e=Decimal("5")),
            ]
        )
        engine, _reports = make_engine(
            logs=logs,
            orgs=_FakeOrgs(org=make_org()),
            factors=_FakeFactors([factor]),
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        data = (await engine.generate(make_request())).content.to_dict()
        lineage = data["lineage"]
        assert lineage["emissions_logs"]["count"] == 2
        assert lineage["emissions_logs"]["reporting_year"] == 2025
        assert lineage["emission_factors"]["resolved"] == 1
        assert lineage["emission_factors"]["factor_ids"] == [factor.id]
        assert lineage["aggregate"]["total_rows"] == 2
        assert lineage["source"] == (
            "emissions_logs + emission_factors (read-only aggregation)"
        )


class TestEmptyAndSerialization:
    async def test_empty_input_explicit_insufficient_data(self) -> None:
        engine, reports = make_engine(
            logs=_FakeLogs([]),
            orgs=_FakeOrgs(org=make_org()),
            factors=_FakeFactors([]),
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(
                error=BenchmarkDataInsufficientError("no emissions data in period")
            ),
        )
        result = await engine.generate(make_request())
        data = result.content.to_dict()
        assert data["totals"]["status"] == "insufficient_data"
        assert data["totals"]["total_co2e_kg"] is None
        assert data["scopes"]["status"] == "insufficient_data"
        assert data["activities"]["status"] == "insufficient_data"
        assert data["benchmarking"]["status"] == "insufficient_data"
        assert data["calculation"]["status"] == "insufficient_data"
        assert len(reports.completed) == 1

    async def test_serialization(self) -> None:
        logs, orgs, factors = default_fixtures()
        engine, _reports = make_engine(
            logs=logs, orgs=orgs, factors=factors,
            validation=_FakeValidation(), benchmarking=_FakeBenchmarking(),
        )
        result = await engine.generate(make_request())
        data = result.content.to_dict()
        # The full content dict round-trips through JSON unchanged.
        raw = json.dumps(data)
        assert json.loads(raw) == data
        # Every section's string content is itself valid JSON.
        for section in result.content.render():
            payload = json.loads(section.content)
            assert isinstance(payload, dict)
            assert payload == data[section.section_id]


class TestPersistenceAndSideEffects:
    async def test_repository_persistence(self) -> None:
        logs, orgs, factors = default_fixtures()
        engine, reports = make_engine(
            logs=logs, orgs=orgs, factors=factors,
            validation=_FakeValidation(), benchmarking=_FakeBenchmarking(),
        )
        result = await engine.generate(make_request())
        assert reports.persisted_content == result.content.to_dict()
        kwargs = reports.completed_kwargs[0]
        assert kwargs["storage_url"] == ""
        assert kwargs["page_count"] == 12
        assert kwargs["file_size"] == len(
            json.dumps(result.content.to_dict()).encode("utf-8")
        )
        assert result.report.file_size_bytes == kwargs["file_size"]

    async def test_eventbus_publishes_report_generated(self) -> None:
        logs, orgs, factors = default_fixtures()
        bus = EventBus()
        received: list[ReportGenerated] = []
        bus.subscribe(ReportGenerated, lambda event: received.append(event))
        engine, _reports = make_engine(
            logs=logs, orgs=orgs, factors=factors,
            validation=_FakeValidation(), benchmarking=_FakeBenchmarking(),
            event_bus=bus,
        )
        result = await engine.generate(make_request())
        await bus.drain()
        assert len(received) == 1
        assert received[0].report_id == result.report.id
        assert received[0].organization_id == "org-1"
        assert received[0].storage_url == ""

    async def test_audit_logger_records_generation(self) -> None:
        logs, orgs, factors = default_fixtures()
        sink = _AuditSink()
        engine, _reports = make_engine(
            logs=logs, orgs=orgs, factors=factors,
            validation=_FakeValidation(), benchmarking=_FakeBenchmarking(),
            audit_logger=sink,
        )
        result = await engine.generate(make_request())
        assert len(sink.entries) == 1
        entry = sink.entries[0]
        assert entry.action == "report:generated"
        assert entry.entity_type == "report"
        assert entry.entity_id == result.report.id
        assert entry.correlation_id == result.report.id
        assert entry.actor == "report_generation_engine"
        assert entry.after["report_type"] == "annual"
        assert entry.after["reporting_year"] == 2025
        assert entry.after["page_count"] == 12
        assert entry.after["sections"] == DEFAULT_SECTIONS

    async def test_no_database_side_effects_outside_approved_persistence(self) -> None:
        factor = make_factor()
        logs = _FakeLogs(
            [make_log(factor=factor, calculated_kg_co2e=Decimal("18.40"))]
        )
        orgs = _FakeOrgs(
            org=make_org(),
            metadata=make_metadata(fte_count=10),
            facilities=[make_facility()],
            assets=[make_asset()],
        )
        factors = _FakeFactors([factor])
        reports = _FakeReports()
        engine, _reports2 = make_engine(
            reports=reports,
            logs=logs,
            orgs=orgs,
            factors=factors,
            validation=_FakeValidation(),
            benchmarking=_FakeBenchmarking(),
        )
        await engine.generate(make_request())
        # Report persistence is limited to create + complete.
        assert reports.calls == ["create_generation_request", "complete_generation"]
        # Source surfaces were only read.
        assert len(logs.aggregate_calls) == 1
        assert len(logs.find_calls) == 1
        assert "get" in orgs.calls
        assert len(factors.get_calls) == 1


class TestRealEngineRegression:
    """Phase 9A/9B regressions: the real engines injected as surfaces."""

    async def test_real_validation_engine_composition(self) -> None:
        factor = make_factor()
        logs = _FakeLogs(
            [make_log(factor=factor, facility_id="fac-1", calculated_kg_co2e=Decimal("18.40"))]
        )
        orgs = _FakeOrgs(
            org=make_org(),
            metadata=make_metadata(fte_count=10),
            facilities=[make_facility("fac-1")],
            assets=[make_asset()],
        )
        factors = _FakeFactors([factor])
        validation = ValidationEngine(logs, orgs, factors)
        engine, _reports = make_engine(
            logs=logs, orgs=orgs, factors=factors,
            validation=validation,
            benchmarking=_FakeBenchmarking(),
        )
        data = (await engine.generate(make_request())).content.to_dict()
        assert data["validation"]["status"] == "passed"
        assert data["totals"]["status"] == "available"
        assert data["provenance"]["gas_coverage"] == "CO2e"

    async def test_real_validation_engine_strict_blocking_error(self) -> None:
        factor = make_factor()
        # Facility is referenced but does not belong to the org => blocking A8 error.
        logs = _FakeLogs(
            [make_log(factor=factor, facility_id="fac-missing", calculated_kg_co2e=Decimal("1"))]
        )
        orgs = _FakeOrgs(
            org=make_org(),
            facilities=[make_facility("fac-1")],
            assets=[],
        )
        factors = _FakeFactors([factor])
        validation = ValidationEngine(logs, orgs, factors)
        reports = _FakeReports()
        engine, _reports2 = make_engine(
            reports=reports, logs=logs, orgs=orgs, factors=factors,
            validation=validation,
            benchmarking=_FakeBenchmarking(),
        )
        with pytest.raises(ValidationFailedError):
            await engine.generate(make_request())
        assert reports.calls == []

    async def test_real_benchmarking_engine_composition(self) -> None:
        factor = make_factor()
        logs = _FakeLogs(
            [make_log(factor=factor, facility_id="fac-1", calculated_kg_co2e=Decimal("18.40"))]
        )
        orgs = _FakeOrgs(
            org=make_org(),
            metadata=make_metadata(
                fte_count=10, total_floor_area_sqm=100.0, annual_revenue_gbp=1000.0
            ),
            facilities=[make_facility("fac-1")],
        )
        factors = _FakeFactors([factor])
        benchmarking = BenchmarkingEngine(logs, orgs, factors)
        engine, _reports = make_engine(
            logs=logs, orgs=orgs, factors=factors,
            validation=_FakeValidation(),
            benchmarking=benchmarking,
        )
        data = (await engine.generate(make_request())).content.to_dict()
        benchmark = data["benchmarking"]
        assert benchmark["status"] == "available"
        keys = {m["key"] for m in benchmark["metrics"]}
        assert "total" in keys
        assert "per_fte" in keys
        assert "per_area" in keys
        assert "per_revenue" in keys
        # availability states are preserved — never fabricated zeros
        for metric in benchmark["metrics"]:
            if metric["status"] != "available":
                assert metric["value"] is None
        assert data["totals"]["unit"] == "kg CO2e"

    async def test_real_engines_empty_period_insufficient(self) -> None:
        logs = _FakeLogs([])
        orgs = _FakeOrgs(org=make_org(), metadata=make_metadata(fte_count=10))
        factors = _FakeFactors([])
        validation = ValidationEngine(logs, orgs, factors)
        benchmarking = BenchmarkingEngine(logs, orgs, factors)
        engine, reports = make_engine(
            logs=logs, orgs=orgs, factors=factors,
            validation=validation,
            benchmarking=benchmarking,
        )
        result = await engine.generate(make_request())
        data = result.content.to_dict()
        # Empty period: totals + benchmarking are explicitly insufficient.
        assert data["totals"]["status"] == "insufficient_data"
        assert data["benchmarking"]["status"] == "insufficient_data"
        # Validation still passes (no blocking issues on an empty dataset).
        assert data["validation"]["status"] == "passed"
        assert len(reports.completed) == 1












