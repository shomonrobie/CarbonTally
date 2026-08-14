"""Unit tests for engines.benchmarking (Phase 9B — BenchmarkingEngine B1–B8).

Covers every approved capability, the denominator/data-availability rules, the
SEAI CO2-only provenance requirement, cross-tenant isolation and the
no-database-side-effects guarantee. All repository surfaces are fakes; no
database is touched.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import pytest

from core.exceptions import BenchmarkDataInsufficientError
from core.types import DateRange
from domain.audit import AuditEntry
from domain.benchmarking import BenchmarkAvailability, BenchmarkRequest
from domain.calculation import EmissionLog, EmissionsAggregate
from domain.factor import EmissionFactor
from domain.organization import Facility, OrganizationMetadata

import engines.benchmarking as _b

_SEAI_ELEC = "Fuels > Electricity > Electricity consumption (kg CO2) [kWh]"
_DEFRA_GAS = "Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]"
_SEAI_BATCH = "9e3b2c8a-1d4f-4e6b-8a7c-2f5d6e7a8b9c"


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
        activity_type=_SEAI_ELEC,
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
        quantity=Decimal(str(kwargs["quantity"] if "quantity" in kwargs else "100")),
        date=kwargs.get("date", date(2025, 6, 1)),
        unit=kwargs.get("unit", factor.unit if factor else "kWh"),
        scope=kwargs.get("scope", factor.scope if factor else "Scope 1"),
        asset_id=kwargs.get("asset_id"),
        facility_id=kwargs.get("facility_id"),
        snapshot_id=kwargs.get("snapshot_id"),
        calculated_kg_co2e=Decimal(str(kwargs.get("calculated_kg_co2e") or "0")),
    )


def make_metadata(**kwargs: Any) -> OrganizationMetadata:
    return OrganizationMetadata(
        total_floor_area_sqm=kwargs.get("total_floor_area_sqm"),
        occupied_floor_area_sqm=kwargs.get("occupied_floor_area_sqm"),
        fte_count=kwargs.get("fte_count"),
        annual_revenue_gbp=kwargs.get("annual_revenue_gbp"),
        sector=kwargs.get("sector"),
    )


def make_facility(facility_id: str = "fac-1", name: str = "Facility") -> Facility:
    return Facility(id=facility_id, organization_id="org-1", name=name, address="")


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
        by_group: dict[str, Decimal] = {}
        for log in logs:
            scope_key = log.scope or "none"
            by_scope[scope_key] = by_scope.get(scope_key, Decimal("0")) + log.calculated_kg_co2e
            key = self._group_key(log, group_by)
            by_group[key] = by_group.get(key, Decimal("0")) + log.calculated_kg_co2e
        total = sum((log.calculated_kg_co2e for log in logs), Decimal("0"))
        return EmissionsAggregate(
            organization_id=org_id,
            period=period,
            group_by=group_by,
            total_co2e_kg=total,
            total_rows=len(logs),
            by_scope=by_scope,
            by_group=by_group,
        )

    def _group_key(self, log: EmissionLog, group_by: str) -> str:
        if group_by == "scope":
            return log.scope or "none"
        if group_by == "year":
            return str(log.date.year)
        if group_by == "facility":
            return log.facility_id or "none"
        if group_by == "asset":
            return log.asset_id or "none"
        if group_by == "month":
            return log.date.strftime("%Y-%m")
        return "none"


class _FakeOrgs:
    def __init__(
        self,
        metadata: Optional[OrganizationMetadata] = None,
        facilities: Optional[list[Facility]] = None,
    ) -> None:
        self.metadata = metadata
        self.facilities = list(facilities or [])

    async def get_metadata(self, org_id: str) -> Optional[OrganizationMetadata]:
        return self.metadata

    async def get_facilities(self, org_id: str) -> list[Facility]:
        return self.facilities


class _FakeFactors:
    def __init__(self, factors: Optional[list[EmissionFactor]] = None) -> None:
        self.factors = {f.id: f for f in (factors or [])}
        self.get_calls: list[str] = []

    async def get(self, factor_id: str) -> Optional[EmissionFactor]:
        self.get_calls.append(factor_id)
        return self.factors.get(factor_id)


class _AuditSink:
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


def status_of(result, key: str) -> BenchmarkAvailability:
    metric = result.metric(key)
    assert metric is not None, f"metric {key!r} not present"
    return metric.status


class TestB1YearOverYear:
    async def test_total_yoy_delta_and_pct(self) -> None:
        factor = make_factor()
        logs = [
            make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("100")),
            make_log(factor=factor, date=date(2024, 6, 1), calculated_kg_co2e=Decimal("80")),
        ]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, compare_years=(2024,),
            metrics=("total",),
        )
        result = await engine.benchmark(request)
        total = result.metric("total")
        assert total is not None and total.value == Decimal("100")
        assert total.comparison == "2025"
        yoy = result.metric("total_vs_2024")
        assert yoy is not None
        assert yoy.baseline_value == Decimal("80")
        assert yoy.delta == Decimal("20")
        assert yoy.delta_pct == Decimal("25.00")
        assert yoy.comparison == "2025 vs 2024"
        assert result.by_group["year:2025"] == Decimal("100")
        assert result.by_group["year:2024"] == Decimal("80")

    async def test_decrease_yoy(self) -> None:
        factor = make_factor()
        logs = [
            make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("60")),
            make_log(factor=factor, date=date(2024, 6, 1), calculated_kg_co2e=Decimal("80")),
        ]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, compare_years=(2024,),
            metrics=("total",),
        )
        result = await engine.benchmark(request)
        yoy = result.metric("total_vs_2024")
        assert yoy is not None and yoy.delta == Decimal("-20")
        assert yoy.delta_pct == Decimal("-25.00")

    async def test_multiple_reporting_periods(self) -> None:
        factor = make_factor()
        logs = [
            make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("100")),
            make_log(factor=factor, date=date(2024, 6, 1), calculated_kg_co2e=Decimal("80")),
            make_log(factor=factor, date=date(2023, 6, 1), calculated_kg_co2e=Decimal("50")),
        ]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, compare_years=(2024, 2023),
            metrics=("total",),
        )
        result = await engine.benchmark(request)
        assert result.metric("total_vs_2024") is not None
        assert result.metric("total_vs_2023") is not None
        assert result.metric("total_vs_2023").delta == Decimal("50")
        assert result.by_group["year:2023"] == Decimal("50")


class TestB2Facility:
    async def test_facility_comparison_and_yoy(self) -> None:
        factor = make_factor()
        facilities = [make_facility("fac-1", "Hub A"), make_facility("fac-2", "Hub B")]
        logs = [
            make_log(factor=factor, facility_id="fac-1", date=date(2025, 6, 1), calculated_kg_co2e=Decimal("60")),
            make_log(factor=factor, facility_id="fac-2", date=date(2025, 6, 1), calculated_kg_co2e=Decimal("40")),
            make_log(factor=factor, facility_id="fac-2", date=date(2024, 6, 1), calculated_kg_co2e=Decimal("30")),
        ]
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(facilities=facilities), _FakeFactors([factor])
        )
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, compare_years=(2024,),
            metrics=("total",), group_by=("facility",),
        )
        result = await engine.benchmark(request)
        fac1 = result.metric("facility:fac-1")
        fac2 = result.metric("facility:fac-2")
        assert fac1 is not None and fac1.value == Decimal("60")
        assert fac2 is not None and fac2.value == Decimal("40")
        # facility-vs-facility: average = (60 + 40) / 2 = 50
        assert fac1.comparison == "facility vs org facility average"
        assert fac1.delta == Decimal("10")
        assert fac1.delta_pct == Decimal("20.00")
        # fac-2 has a 2024 baseline -> YoY comparison wins
        assert fac2.comparison == "2025 vs 2024"
        assert fac2.baseline_value == Decimal("30")
        assert fac2.delta == Decimal("10")
        assert result.by_group["facility:fac-1"] == Decimal("60")
        assert result.by_group["facility:fac-2"] == Decimal("40")

    async def test_facility_without_data(self) -> None:
        factor = make_factor()
        facilities = [make_facility("fac-1", "Hub A"), make_facility("fac-2", "Hub B")]
        logs = [
            make_log(factor=factor, facility_id="fac-1", date=date(2025, 6, 1), calculated_kg_co2e=Decimal("60")),
        ]
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(facilities=facilities), _FakeFactors([factor])
        )
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, metrics=("total",),
            group_by=("facility",),
        )
        result = await engine.benchmark(request)
        fac2 = result.metric("facility:fac-2")
        assert fac2 is not None and fac2.status is BenchmarkAvailability.INSUFFICIENT_DATA
        assert "no emissions data" in fac2.note

    async def test_facility_filter(self) -> None:
        factor = make_factor()
        facilities = [make_facility("fac-1", "Hub A"), make_facility("fac-2", "Hub B")]
        logs = [
            make_log(factor=factor, facility_id="fac-1", date=date(2025, 6, 1), calculated_kg_co2e=Decimal("60")),
            make_log(factor=factor, facility_id="fac-2", date=date(2025, 6, 1), calculated_kg_co2e=Decimal("40")),
        ]
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(facilities=facilities), _FakeFactors([factor])
        )
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, metrics=("total",),
            group_by=("facility",), facility_filter="fac-1",
        )
        result = await engine.benchmark(request)
        assert result.metric("facility:fac-1") is not None
        assert result.metric("facility:fac-2") is None
        assert "facility:fac-2" not in result.by_group
        assert result.by_group["facility:fac-1"] == Decimal("60")


class TestB3Scope:
    async def test_scope_breakdown_and_yoy(self) -> None:
        factor1 = make_factor(id="f1", scope="Scope 1")
        factor2 = make_factor(id="f2", activity_type="Fuels > Electricity > X (kg CO2e) [kWh]", scope="Scope 2")
        logs = [
            make_log(factor=factor1, scope="Scope 1", date=date(2025, 6, 1), calculated_kg_co2e=Decimal("70")),
            make_log(factor=factor2, scope="Scope 2", date=date(2025, 6, 1), calculated_kg_co2e=Decimal("30")),
            make_log(factor=factor1, scope="Scope 1", date=date(2024, 6, 1), calculated_kg_co2e=Decimal("50")),
        ]
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor1, factor2])
        )
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, compare_years=(2024,),
            metrics=("total",), group_by=("scope",),
        )
        result = await engine.benchmark(request)
        assert result.by_scope["Scope 1"] == Decimal("70")
        assert result.by_scope["Scope 2"] == Decimal("30")
        s1 = result.metric("scope:Scope 1")
        assert s1 is not None and s1.value == Decimal("70")
        assert s1.baseline_value == Decimal("50")
        assert s1.delta == Decimal("20")
        assert s1.comparison == "2025 vs 2024"
        assert s1.scope == "Scope 1"


class TestB4PerFte:
    async def test_per_fte_normal(self) -> None:
        factor = make_factor()
        logs = [make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("1000"))]
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(metadata=make_metadata(fte_count=10)),
            _FakeFactors([factor]),
        )
        request = BenchmarkRequest(organization_id="org-1", reporting_year=2025, metrics=("per_fte",))
        result = await engine.benchmark(request)
        metric = result.metric("per_fte")
        assert metric is not None
        assert metric.status is BenchmarkAvailability.AVAILABLE
        assert metric.value == Decimal("100.000000")
        assert metric.numerator == Decimal("1000")
        assert metric.denominator == Decimal("10")
        assert metric.unit == "kg CO2e per FTE"


class TestB5PerArea:
    async def test_per_area_normal(self) -> None:
        factor = make_factor()
        logs = [make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("1000"))]
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(metadata=make_metadata(total_floor_area_sqm=500)),
            _FakeFactors([factor]),
        )
        request = BenchmarkRequest(organization_id="org-1", reporting_year=2025, metrics=("per_area",))
        result = await engine.benchmark(request)
        metric = result.metric("per_area")
        assert metric is not None
        assert metric.status is BenchmarkAvailability.AVAILABLE
        assert metric.value == Decimal("2.000000")
        assert metric.unit == "kg CO2e per square metres"


class TestB6PerRevenue:
    async def test_per_revenue_normal(self) -> None:
        factor = make_factor()
        logs = [make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("1000"))]
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(metadata=make_metadata(annual_revenue_gbp=2000)),
            _FakeFactors([factor]),
        )
        request = BenchmarkRequest(organization_id="org-1", reporting_year=2025, metrics=("per_revenue",))
        result = await engine.benchmark(request)
        metric = result.metric("per_revenue")
        assert metric is not None
        assert metric.status is BenchmarkAvailability.AVAILABLE
        assert metric.value == Decimal("0.500000")
        assert metric.unit == "kg CO2e per GBP"


class TestB7ActivityIntensity:
    async def test_activity_intensity_and_yoy(self) -> None:
        factor = make_factor(activity_type=_DEFRA_GAS, unit="kWh")
        logs = [
            make_log(factor=factor, unit="kWh", date=date(2025, 6, 1),
                     quantity=Decimal("1000"), calculated_kg_co2e=Decimal("184")),
            make_log(factor=factor, unit="kWh", date=date(2024, 6, 1),
                     quantity=Decimal("800"), calculated_kg_co2e=Decimal("147.2")),
        ]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, compare_years=(2024,),
            metrics=("activity_intensity",),
        )
        result = await engine.benchmark(request)
        metric = result.metric(f"activity:{_DEFRA_GAS}")
        assert metric is not None
        assert metric.status is BenchmarkAvailability.AVAILABLE
        assert metric.value == Decimal("0.184000")
        assert metric.baseline_value == Decimal("0.184000")
        assert metric.delta == Decimal("0.000000")
        assert metric.delta_pct == Decimal("0.00")
        assert metric.unit == "kg CO2e per kWh"
        assert metric.activity_type == _DEFRA_GAS

    async def test_activity_intensity_incompatible_units(self) -> None:
        factor = make_factor(activity_type=_DEFRA_GAS, unit="kWh")
        logs = [
            make_log(factor=factor, unit="kWh", date=date(2025, 6, 1),
                     quantity=Decimal("10"), calculated_kg_co2e=Decimal("2")),
            make_log(factor=factor, unit="m3", date=date(2025, 6, 1),
                     quantity=Decimal("10"), calculated_kg_co2e=Decimal("20")),
        ]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, metrics=("activity_intensity",),
        )
        result = await engine.benchmark(request)
        metric = result.metric(f"activity:{_DEFRA_GAS}")
        assert metric is not None and metric.status is BenchmarkAvailability.INCOMPATIBLE_UNIT

    async def test_activity_intensity_zero_quantity(self) -> None:
        factor = make_factor(activity_type=_DEFRA_GAS, unit="kWh")
        logs = [
            make_log(factor=factor, unit="kWh", date=date(2025, 6, 1),
                     quantity=Decimal("0"), calculated_kg_co2e=Decimal("5")),
        ]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, metrics=("activity_intensity",),
        )
        result = await engine.benchmark(request)
        metric = result.metric(f"activity:{_DEFRA_GAS}")
        assert metric is not None and metric.status is BenchmarkAvailability.ZERO_DENOMINATOR


class TestB8InternalCapabilities:
    async def test_month_grouping(self) -> None:
        factor = make_factor()
        logs = [
            make_log(factor=factor, date=date(2025, 1, 15), calculated_kg_co2e=Decimal("10")),
            make_log(factor=factor, date=date(2025, 6, 15), calculated_kg_co2e=Decimal("90")),
        ]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, metrics=("total",),
            group_by=("month",),
        )
        result = await engine.benchmark(request)
        assert result.by_group["month:2025-01"] == Decimal("10")
        assert result.by_group["month:2025-06"] == Decimal("90")

    async def test_asset_grouping(self) -> None:
        factor = make_factor()
        logs = [
            make_log(factor=factor, asset_id="asset-1", date=date(2025, 6, 1), calculated_kg_co2e=Decimal("30")),
            make_log(factor=factor, asset_id="asset-2", date=date(2025, 6, 1), calculated_kg_co2e=Decimal("70")),
        ]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, metrics=("total",),
            group_by=("asset",),
        )
        result = await engine.benchmark(request)
        assert result.by_group["asset:asset-1"] == Decimal("30")
        assert result.by_group["asset:asset-2"] == Decimal("70")


class TestDenominatorRule:
    async def test_missing_organization_metadata(self) -> None:
        factor = make_factor()
        logs = [make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("1000"))]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(metadata=None), _FakeFactors([factor]))
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025,
            metrics=("per_fte", "per_area", "per_revenue"),
        )
        result = await engine.benchmark(request)
        for key in ("per_fte", "per_area", "per_revenue"):
            metric = result.metric(key)
            assert metric is not None
            assert metric.status is BenchmarkAvailability.NOT_AVAILABLE
            assert metric.value is None
            assert metric.numerator == Decimal("1000")
            assert "denominator missing" in metric.note

    async def test_missing_specific_denominator(self) -> None:
        factor = make_factor()
        logs = [make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("1000"))]
        metadata = make_metadata(fte_count=None, total_floor_area_sqm=500, annual_revenue_gbp=2000)
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(metadata=metadata), _FakeFactors([factor]))
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025,
            metrics=("per_fte", "per_area", "per_revenue"),
        )
        result = await engine.benchmark(request)
        assert result.metric("per_fte").status is BenchmarkAvailability.NOT_AVAILABLE
        assert result.metric("per_area").status is BenchmarkAvailability.AVAILABLE
        assert result.metric("per_revenue").status is BenchmarkAvailability.AVAILABLE

    async def test_zero_denominator(self) -> None:
        factor = make_factor()
        logs = [make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("1000"))]
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(metadata=make_metadata(fte_count=0)), _FakeFactors([factor])
        )
        request = BenchmarkRequest(organization_id="org-1", reporting_year=2025, metrics=("per_fte",))
        result = await engine.benchmark(request)
        metric = result.metric("per_fte")
        assert metric is not None and metric.status is BenchmarkAvailability.ZERO_DENOMINATOR
        assert metric.value is None

    async def test_invalid_negative_denominator(self) -> None:
        factor = make_factor()
        logs = [make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("1000"))]
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(metadata=make_metadata(fte_count=-5)), _FakeFactors([factor])
        )
        request = BenchmarkRequest(organization_id="org-1", reporting_year=2025, metrics=("per_fte",))
        result = await engine.benchmark(request)
        metric = result.metric("per_fte")
        assert metric is not None and metric.status is BenchmarkAvailability.INVALID_DENOMINATOR
        assert metric.value is None


class TestInsufficientData:
    async def test_empty_reporting_period_raises(self) -> None:
        factor = make_factor()
        engine = _b.BenchmarkingEngine(_FakeLogs([]), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(organization_id="org-1", reporting_year=2025)
        with pytest.raises(BenchmarkDataInsufficientError):
            await engine.benchmark(request)

    async def test_empty_baseline_year_noted(self) -> None:
        factor = make_factor()
        logs = [make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("100"))]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, compare_years=(2024,),
            metrics=("total",),
        )
        result = await engine.benchmark(request)
        yoy = result.metric("total_vs_2024")
        assert yoy is not None
        assert yoy.baseline_value is None
        assert yoy.delta is None
        assert "baseline year 2024 has no emissions data" in yoy.note

    async def test_no_facility_data_is_insufficient(self) -> None:
        factor = make_factor()
        facilities = [make_facility("fac-1", "Hub A")]
        logs = [make_log(factor=factor, facility_id="fac-1", date=date(2025, 6, 1), calculated_kg_co2e=Decimal("10"))]
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(facilities=facilities), _FakeFactors([factor])
        )
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, metrics=("total",),
            group_by=("facility",), facility_filter="fac-9",
        )
        result = await engine.benchmark(request)
        assert result.metric("facility:fac-9") is None


class TestProvenance:
    async def test_all_seai_is_co2(self) -> None:
        factor = make_seai()
        logs = [make_log(factor=factor, unit="kWh", scope="Scope 2",
                         date=date(2025, 6, 1), calculated_kg_co2e=Decimal("100"))]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(organization_id="org-1", reporting_year=2025, metrics=("total",))
        result = await engine.benchmark(request)
        total = result.metric("total")
        assert total is not None
        assert total.unit == "kg CO2"
        assert total.source == "SEAI"

    async def test_all_defra_is_co2e(self) -> None:
        factor = make_factor()
        logs = [make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("100"))]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(organization_id="org-1", reporting_year=2025, metrics=("total",))
        result = await engine.benchmark(request)
        total = result.metric("total")
        assert total is not None
        assert total.unit == "kg CO2e"
        assert total.source == "DEFRA-DESNZ"

    async def test_mixed_provenance_is_not_silently_relabelled(self) -> None:
        defra = make_factor(id="defra-1")
        seai = make_seai(id="seai-1")
        logs = [
            make_log(factor=defra, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("100")),
            make_log(factor=seai, unit="kWh", scope="Scope 2", date=date(2025, 6, 1),
                     calculated_kg_co2e=Decimal("50")),
        ]
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(), _FakeFactors([defra, seai])
        )
        request = BenchmarkRequest(organization_id="org-1", reporting_year=2025, metrics=("total",))
        result = await engine.benchmark(request)
        total = result.metric("total")
        assert total is not None
        assert total.unit == "kg CO2/CO2e mixed"
        assert total.source == "DEFRA-DESNZ,SEAI"
        assert total.value == Decimal("150")

    async def test_seai_per_fte_unit_preserves_co2(self) -> None:
        factor = make_seai()
        logs = [make_log(factor=factor, unit="kWh", scope="Scope 2",
                         date=date(2025, 6, 1), calculated_kg_co2e=Decimal("1000"))]
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(metadata=make_metadata(fte_count=10)), _FakeFactors([factor])
        )
        request = BenchmarkRequest(organization_id="org-1", reporting_year=2025, metrics=("per_fte",))
        result = await engine.benchmark(request)
        metric = result.metric("per_fte")
        assert metric is not None and metric.unit == "kg CO2 per FTE"


class TestNoCrossTenantLeakage:
    async def test_org_a_benchmark_uses_only_org_a_data(self) -> None:
        factor = make_factor()
        logs = [
            make_log(factor=factor, organization_id="org-a", date=date(2025, 6, 1),
                     calculated_kg_co2e=Decimal("10")),
            make_log(factor=factor, organization_id="org-b", date=date(2025, 6, 1),
                     calculated_kg_co2e=Decimal("999999")),
        ]
        engine = _b.BenchmarkingEngine(_FakeLogs(logs), _FakeOrgs(), _FakeFactors([factor]))
        request = BenchmarkRequest(organization_id="org-a", reporting_year=2025, metrics=("total",))
        result = await engine.benchmark(request)
        total = result.metric("total")
        assert total is not None and total.value == Decimal("10")


class TestNoDatabaseSideEffects:
    async def test_audits_benchmark(self) -> None:
        factor = make_factor()
        logs = [make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("100"))]
        audit = _AuditSink()
        engine = _b.BenchmarkingEngine(
            _FakeLogs(logs), _FakeOrgs(metadata=make_metadata(fte_count=10)),
            _FakeFactors([factor]), audit_logger=audit,
        )
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, metrics=("total", "per_fte"),
        )
        result = await engine.benchmark(request)
        assert len(audit.entries) == 1
        entry = audit.entries[0]
        assert entry.action == "benchmark:completed"
        assert entry.entity_type == "organization"
        assert entry.entity_id == "org-1"
        assert entry.after["empty"] is False
        assert "total" in entry.after["metric_keys"]
        assert "per_fte" in entry.after["metric_keys"]

    async def test_read_only_repository_surface(self) -> None:
        """The engine must never call write methods on repositories."""
        factor = make_factor()
        logs = [make_log(factor=factor, date=date(2025, 6, 1), calculated_kg_co2e=Decimal("100"))]
        fake_logs = _FakeLogs(logs)
        fake_orgs = _FakeOrgs(metadata=make_metadata(fte_count=10))
        fake_factors = _FakeFactors([factor])
        engine = _b.BenchmarkingEngine(fake_logs, fake_orgs, fake_factors)
        request = BenchmarkRequest(
            organization_id="org-1", reporting_year=2025, compare_years=(2024,),
            metrics=("total", "per_fte", "activity_intensity"), group_by=("scope", "facility", "month"),
        )
        await engine.benchmark(request)
        # Only read operations were invoked; no write path exists on the fakes.
        assert fake_logs.aggregate_calls
        assert fake_logs.find_calls
        assert fake_factors.get_calls







