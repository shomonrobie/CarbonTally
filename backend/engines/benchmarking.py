"""Emissions Benchmarking Engine (Backend v2.1 §7, Phase 9B — contract 9.2).

Internal / self-referential benchmarking computed from the organisation's own
``emissions_logs`` and ``organization_metadata``. Implements the approved
Phase 9 capabilities B1–B8: year-over-year (B1), facility-vs-facility (B2),
scope breakdown (B3), emissions per FTE (B4), per floor area (B5), per revenue
(B6), activity intensity (B7), and the approved internal capabilities
(multi-period, month/asset groupings, facility filtering — B8).

Denominator rule: intensity metrics are computed ONLY when the denominator is
available and valid. Missing/zero/invalid denominators produce explicit
``not_available`` / ``zero_denominator`` / ``invalid_denominator`` metric
results — never an estimate, inference or a silent zero. An empty reporting
period raises ``BenchmarkDataInsufficientError`` (404).

The engine never writes to the database. It reads through protocols
(:class:`LogsSource`, :class:`OrgSource`, :class:`FactorLookup`) and records an
audit entry per run. No external reference dataset, no benchmark table, no
cross-tenant comparison, no events (none defined in the frozen event set).

Multi-country/SEAI: the engine operates on calculated emissions data without
assuming a provider or country. ``gas_coverage`` (domain.factor) preserves the
``kg CO2`` vs ``kg CO2e`` distinction and is carried into every metric's unit
and ``source`` label — SEAI CO2-only data is never silently relabelled CO2e.
"""
from __future__ import annotations

import datetime as _dt
from decimal import Decimal
from typing import Optional, Protocol

from core.exceptions import BenchmarkDataInsufficientError
from core.logging import get_logger
from core.types import DateRange
from domain.benchmarking import (
    BenchmarkAvailability,
    BenchmarkMetric,
    BenchmarkRequest,
    BenchmarkResult,
    GROUP_FACILITY,
    GROUP_SCOPE,
    GROUP_YEAR,
    METRIC_ACTIVITY_INTENSITY,
    METRIC_PER_AREA,
    METRIC_PER_FTE,
    METRIC_PER_REVENUE,
    METRIC_TOTAL,
)
from domain.calculation import EmissionLog, EmissionsAggregate
from domain.factor import EmissionFactor, gas_coverage
from domain.organization import Facility, OrganizationMetadata
from infra.audit_logger import AuditLogger

logger = get_logger(__name__)

#: Precision for intensity values (6 decimal places).
_INTENSITY_PRECISION = Decimal("0.000001")

#: Precision for percentage changes (2 decimal places).
_PCT_PRECISION = Decimal("0.01")


def _year_range(year: int) -> DateRange:
    """Return the inclusive calendar-year range for ``year``."""
    return DateRange(_dt.date(year, 1, 1), _dt.date(year, 12, 31))


def _dec(value: object) -> Optional[Decimal]:
    """Convert ``None``/int/float/Decimal to ``Optional[Decimal]``."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _pct(value: Optional[Decimal]) -> Optional[Decimal]:
    """Quantise a percentage change to 2 decimal places."""
    if value is None:
        return None
    return value.quantize(_PCT_PRECISION)


def _provenance(
    logs: list[EmissionLog], factors: dict[str, EmissionFactor]
) -> tuple[str, str]:
    """Return ``(coverage_label, source_label)`` for a set of logs/factors.

    ``coverage_label`` is ``CO2``, ``CO2e``, ``CO2/CO2e mixed`` or ``unknown``;
    ``source_label`` is the comma-joined factor_source values (e.g. ``SEAI``,
    ``DEFRA-DESNZ,SEAI``). This preserves the CO2-vs-CO2e provenance
    distinction while aggregating multi-provider data.
    """
    sources: set[str] = set()
    coverages: set[str] = set()
    for factor in factors.values():
        if factor.factor_source:
            sources.add(factor.factor_source)
        coverages.add(gas_coverage(factor))
    if coverages == {"CO2"}:
        coverage = "CO2"
    elif coverages == {"CO2e"}:
        coverage = "CO2e"
    elif coverages:
        coverage = "CO2/CO2e mixed"
    else:
        coverage = "unknown"
    return coverage, ",".join(sorted(sources)) or "unknown"


def _group_logs_by_activity(
    logs: list[EmissionLog], factors: dict[str, EmissionFactor]
) -> dict[str, list[EmissionLog]]:
    """Group logs by their factor's ``activity_type`` (factors by id)."""
    groups: dict[str, list[EmissionLog]] = {}
    for log in logs:
        factor = factors.get(log.factor_id)
        if factor is None:
            continue
        groups.setdefault(factor.activity_type, []).append(log)
    return groups


# ---------------------------------------------------------------------------
# Repository surfaces (protocols) — satisfied structurally by the production
# repositories (data/emissions_logs.py, data/organizations.py,
# data/emission_factors.py) and by fakes in the unit suite.
# ---------------------------------------------------------------------------


class LogsSource(Protocol):
    """The emissions-log surface the engine reads (``EmissionsLogsRepository``)."""

    async def aggregate(
        self, org_id: str, period: DateRange, group_by: str
    ) -> EmissionsAggregate: ...

    async def find_by_org(self, org_id: str, period: DateRange) -> list[EmissionLog]: ...


class OrgSource(Protocol):
    """The organisations surface the engine reads (``OrganizationsRepository``)."""

    async def get_metadata(self, org_id: str) -> Optional[OrganizationMetadata]: ...

    async def get_facilities(self, org_id: str) -> list[Facility]: ...


class FactorLookup(Protocol):
    """The factor surface the engine reads (``EmissionFactorsRepository``)."""

    async def get(self, id: str) -> Optional[EmissionFactor]: ...


class BenchmarkingEngine:
    """Internal / self-referential emissions benchmarking (Phase 9B).

    Args:
        logs_repo: Emissions-log repository surface (:class:`LogsSource`).
        org_repo: Organisations repository surface (:class:`OrgSource`).
        factor_lookup: Optional factor surface (:class:`FactorLookup`), used
            for activity-intensity labels and CO2/CO2e provenance.
        audit_logger: Optional logger that records every benchmark run.
    """

    def __init__(
        self,
        logs_repo: LogsSource,
        org_repo: OrgSource,
        factor_lookup: Optional[FactorLookup] = None,
        *,
        audit_logger: Optional[AuditLogger] = None,
    ) -> None:
        if logs_repo is None or org_repo is None:
            raise ValueError("logs_repo and org_repo must not be None")
        self._logs = logs_repo
        self._orgs = org_repo
        self._factors = factor_lookup
        self._audit_logger = audit_logger

    async def benchmark(self, request: BenchmarkRequest) -> BenchmarkResult:
        """Run the internal benchmark for ``request`` (B1–B8).

        Raises:
            BenchmarkDataInsufficientError: When the reporting period contains
                no emissions logs (empty period).
        """
        org_id = request.organization_id
        year = request.reporting_year
        current_period = _year_range(year)

        current = await self._logs.aggregate(org_id, current_period, GROUP_YEAR)
        if current.total_rows == 0:
            await self._audit(
                org_id, BenchmarkResult(organization_id=org_id, reporting_year=year),
                empty=True,
            )
            raise BenchmarkDataInsufficientError(
                "no emissions data for the reporting period",
                details={"organization_id": org_id, "reporting_year": year},
            )

        metadata = await self._orgs.get_metadata(org_id)
        facilities = await self._orgs.get_facilities(org_id)
        logs = await self._logs.find_by_org(org_id, current_period)
        if request.facility_filter is not None:
            logs = [log for log in logs if log.facility_id == request.facility_filter]
        factors = await self._load_factors(logs)

        baselines: dict[int, EmissionsAggregate] = {}
        for compare_year in request.compare_years:
            baselines[compare_year] = await self._logs.aggregate(
                org_id, _year_range(compare_year), GROUP_YEAR
            )

        coverage_label, source_label = _provenance(logs, factors)

        metrics: list[BenchmarkMetric] = []
        if METRIC_TOTAL in request.metrics:
            metrics.append(
                self._total_metric(year, current, coverage_label, source_label)
            )
            for compare_year in request.compare_years:
                metrics.append(
                    self._total_yoy_metric(
                        year, compare_year, current, baselines[compare_year],
                        coverage_label, source_label,
                    )
                )

        intensity_keys = {
            METRIC_PER_FTE,
            METRIC_PER_AREA,
            METRIC_PER_REVENUE,
        } & set(request.metrics)
        if intensity_keys:
            metrics.extend(
                self._intensity_metrics(
                    current.total_co2e_kg, metadata, intensity_keys,
                    coverage_label, source_label,
                )
            )

        if GROUP_SCOPE in request.group_by:
            metrics.extend(
                self._scope_metrics(year, current, baselines, coverage_label, source_label)
            )

        if GROUP_FACILITY in request.group_by:
            metrics.extend(
                await self._facility_metrics(
                    request, year, current_period, facilities, baselines,
                    coverage_label, source_label,
                )
            )

        if METRIC_ACTIVITY_INTENSITY in request.metrics:
            baseline_logs: dict[int, list[EmissionLog]] = {}
            for compare_year in request.compare_years:
                baseline_logs[compare_year] = await self._logs.find_by_org(
                    org_id, _year_range(compare_year)
                )
            metrics.extend(
                self._activity_intensity_metrics(
                    year, request.compare_years, logs, factors, baseline_logs,
                    coverage_label, source_label,
                )
            )

        by_group = await self._by_group(
            request, org_id, year, current, current_period, baselines
        )
        result = BenchmarkResult(
            organization_id=org_id,
            reporting_year=year,
            metrics=tuple(metrics),
            by_scope=dict(current.by_scope),
            by_group=by_group,
        )
        await self._audit(org_id, result)
        return result

    # ------------------------------------------------------------------
    # B1 — total + year-over-year
    # ------------------------------------------------------------------

    def _total_metric(
        self, year: int, current: EmissionsAggregate, coverage: str, source: str
    ) -> BenchmarkMetric:
        return BenchmarkMetric(
            key=METRIC_TOTAL,
            label="Total emissions",
            unit=f"kg {coverage}",
            value=current.total_co2e_kg,
            numerator=current.total_co2e_kg,
            comparison=str(year),
            source=source,
        )

    def _total_yoy_metric(
        self,
        year: int,
        compare_year: int,
        current: EmissionsAggregate,
        baseline: EmissionsAggregate,
        coverage: str,
        source: str,
    ) -> BenchmarkMetric:
        baseline_value: Optional[Decimal] = None
        delta: Optional[Decimal] = None
        delta_pct: Optional[Decimal] = None
        note = ""
        if baseline.total_rows > 0:
            baseline_value = baseline.total_co2e_kg
            delta = current.total_co2e_kg - baseline_value
            if baseline_value != 0:
                delta_pct = _pct((delta / baseline_value) * 100)
        else:
            note = f"baseline year {compare_year} has no emissions data"
        return BenchmarkMetric(
            key=f"total_vs_{compare_year}",
            label=f"Total emissions {year} vs {compare_year}",
            unit=f"kg {coverage}",
            value=current.total_co2e_kg,
            numerator=current.total_co2e_kg,
            baseline_value=baseline_value,
            delta=delta,
            delta_pct=delta_pct,
            comparison=f"{year} vs {compare_year}",
            source=source,
            note=note,
        )

    # ------------------------------------------------------------------
    # B4/B5/B6 — intensity metrics (denominator rule)
    # ------------------------------------------------------------------

    def _intensity_metrics(
        self,
        total: Decimal,
        metadata: Optional[OrganizationMetadata],
        requested: set[str],
        coverage: str,
        source: str,
    ) -> list[BenchmarkMetric]:
        specs: list[tuple[str, str, Optional[Decimal], str]] = []
        if METRIC_PER_FTE in requested:
            specs.append(("per_fte", "Emissions per FTE", _dec(metadata.fte_count) if metadata else None, "FTE"))
        if METRIC_PER_AREA in requested:
            specs.append(("per_area", "Emissions per floor area", _dec(metadata.total_floor_area_sqm) if metadata else None, "square metres"))
        if METRIC_PER_REVENUE in requested:
            specs.append(("per_revenue", "Emissions per revenue", _dec(metadata.annual_revenue_gbp) if metadata else None, "GBP"))
        return [
            self._intensity_metric(key, label, total, denominator, denom_label, coverage, source)
            for key, label, denominator, denom_label in specs
        ]

    def _intensity_metric(
        self,
        key: str,
        label: str,
        numerator: Decimal,
        denominator: Optional[Decimal],
        denom_label: str,
        coverage: str,
        source: str,
    ) -> BenchmarkMetric:
        unit = f"kg {coverage} per {denom_label}"
        if denominator is None:
            return BenchmarkMetric(
                key=key, label=label, unit=unit,
                status=BenchmarkAvailability.NOT_AVAILABLE,
                numerator=numerator,
                note=f"{denom_label} denominator missing from organization metadata",
            )
        if denominator == 0:
            return BenchmarkMetric(
                key=key, label=label, unit=unit,
                status=BenchmarkAvailability.ZERO_DENOMINATOR,
                numerator=numerator, denominator=denominator,
                note=f"{denom_label} denominator is zero",
            )
        if denominator < 0:
            return BenchmarkMetric(
                key=key, label=label, unit=unit,
                status=BenchmarkAvailability.INVALID_DENOMINATOR,
                numerator=numerator, denominator=denominator,
                note=f"{denom_label} denominator is negative",
            )
        value = (numerator / denominator).quantize(_INTENSITY_PRECISION)
        return BenchmarkMetric(
            key=key, label=label, unit=unit, value=value,
            numerator=numerator, denominator=denominator, source=source,
        )

    # ------------------------------------------------------------------
    # B3 — scope breakdown/comparison
    # ------------------------------------------------------------------

    def _scope_metrics(
        self,
        year: int,
        current: EmissionsAggregate,
        baselines: dict[int, EmissionsAggregate],
        coverage: str,
        source: str,
    ) -> list[BenchmarkMetric]:
        metrics: list[BenchmarkMetric] = []
        for scope_label, total in sorted(current.by_scope.items()):
            baseline_value: Optional[Decimal] = None
            delta: Optional[Decimal] = None
            delta_pct: Optional[Decimal] = None
            comparison = str(year)
            for compare_year, baseline in baselines.items():
                baseline_scope = baseline.by_scope.get(scope_label)
                if baseline_scope is not None and baseline_scope > 0:
                    baseline_value = baseline_scope
                    delta = total - baseline_scope
                    delta_pct = _pct((delta / baseline_scope) * 100)
                    comparison = f"{year} vs {compare_year}"
                    break
            metrics.append(
                BenchmarkMetric(
                    key=f"scope:{scope_label}",
                    label=f"Emissions: {scope_label}",
                    unit=f"kg {coverage}",
                    value=total,
                    numerator=total,
                    baseline_value=baseline_value,
                    delta=delta,
                    delta_pct=delta_pct,
                    comparison=comparison,
                    source=source,
                    scope=scope_label,
                )
            )
        return metrics

    # ------------------------------------------------------------------
    # B2 — facility-vs-facility comparison
    # ------------------------------------------------------------------

    async def _facility_metrics(
        self,
        request: BenchmarkRequest,
        year: int,
        current_period: DateRange,
        facilities: list[Facility],
        baselines: dict[int, EmissionsAggregate],
        coverage: str,
        source: str,
    ) -> list[BenchmarkMetric]:
        if not facilities:
            return []
        facility_agg = await self._logs.aggregate(
            request.organization_id, current_period, GROUP_FACILITY
        )
        by_fac = dict(facility_agg.by_group)
        baseline_by_fac: dict[int, dict[str, Decimal]] = {}
        for compare_year, baseline in baselines.items():
            agg = await self._logs.aggregate(
                request.organization_id, _year_range(compare_year), GROUP_FACILITY
            )
            baseline_by_fac[compare_year] = dict(agg.by_group)

        with_data = [
            f for f in facilities if (by_fac.get(f.id) or Decimal("0")) > 0
        ]
        average = None
        if with_data:
            average = sum(by_fac[f.id] for f in with_data) / Decimal(len(with_data))

        metrics: list[BenchmarkMetric] = []
        for facility in facilities:
            if request.facility_filter is not None and facility.id != request.facility_filter:
                continue
            facility_id = facility.id
            total = by_fac.get(facility_id)
            if total is None or total == 0:
                metrics.append(
                    BenchmarkMetric(
                        key=f"facility:{facility_id}",
                        label=f"Facility: {facility.name}",
                        unit=f"kg {coverage}",
                        status=BenchmarkAvailability.INSUFFICIENT_DATA,
                        numerator=Decimal("0"),
                        facility_id=facility_id,
                        note="no emissions data for facility in reporting year",
                    )
                )
                continue
            baseline_value: Optional[Decimal] = None
            delta: Optional[Decimal] = None
            delta_pct: Optional[Decimal] = None
            comparison = "facility vs org facility average"
            if average is not None and average != 0:
                delta = total - average
                delta_pct = _pct((delta / average) * 100)
            for compare_year, by_fac_baseline in baseline_by_fac.items():
                facility_baseline = by_fac_baseline.get(facility_id)
                if facility_baseline is not None and facility_baseline > 0:
                    baseline_value = facility_baseline
                    delta = total - facility_baseline
                    delta_pct = _pct((delta / facility_baseline) * 100)
                    comparison = f"{year} vs {compare_year}"
                    break
            metrics.append(
                BenchmarkMetric(
                    key=f"facility:{facility_id}",
                    label=f"Facility: {facility.name}",
                    unit=f"kg {coverage}",
                    value=total,
                    numerator=total,
                    baseline_value=baseline_value,
                    delta=delta,
                    delta_pct=delta_pct,
                    comparison=comparison,
                    source=source,
                    facility_id=facility_id,
                )
            )
        return metrics

    # ------------------------------------------------------------------
    # B7 — activity intensity
    # ------------------------------------------------------------------

    def _activity_intensity_metrics(
        self,
        year: int,
        compare_years: tuple[int, ...],
        logs: list[EmissionLog],
        factors: dict[str, EmissionFactor],
        baseline_logs_by_year: dict[int, list[EmissionLog]],
        coverage: str,
        source: str,
    ) -> list[BenchmarkMetric]:
        groups = _group_logs_by_activity(logs, factors)
        baseline_groups = {
            compare_year: _group_logs_by_activity(baseline_logs, factors)
            for compare_year, baseline_logs in baseline_logs_by_year.items()
        }
        metrics: list[BenchmarkMetric] = []
        for activity_type, group in sorted(groups.items()):
            units = {log.unit for log in group}
            unit = next(iter(units)) if len(units) == 1 else ""
            metric_unit = f"kg {coverage} per {unit}" if unit else f"kg {coverage} per unit"
            total_quantity = sum((log.quantity for log in group), Decimal("0"))
            total_co2e = sum((log.calculated_kg_co2e for log in group), Decimal("0"))
            if len(units) > 1:
                metrics.append(
                    BenchmarkMetric(
                        key=f"activity:{activity_type}",
                        label=f"Activity intensity: {activity_type}",
                        unit=metric_unit,
                        status=BenchmarkAvailability.INCOMPATIBLE_UNIT,
                        numerator=total_co2e,
                        denominator=total_quantity,
                        activity_type=activity_type,
                        note="mixed units in activity group; cannot sum quantity",
                    )
                )
                continue
            if total_quantity == 0:
                metrics.append(
                    BenchmarkMetric(
                        key=f"activity:{activity_type}",
                        label=f"Activity intensity: {activity_type}",
                        unit=metric_unit,
                        status=BenchmarkAvailability.ZERO_DENOMINATOR,
                        numerator=total_co2e,
                        denominator=total_quantity,
                        activity_type=activity_type,
                        note="total activity quantity is zero",
                    )
                )
                continue
            value = (total_co2e / total_quantity).quantize(_INTENSITY_PRECISION)
            baseline_value: Optional[Decimal] = None
            delta: Optional[Decimal] = None
            delta_pct: Optional[Decimal] = None
            comparison = ""
            for compare_year in compare_years:
                baseline_group = baseline_groups.get(compare_year, {}).get(activity_type)
                if not baseline_group:
                    continue
                baseline_units = {log.unit for log in baseline_group}
                if len(baseline_units) != 1:
                    continue
                baseline_quantity = sum((log.quantity for log in baseline_group), Decimal("0"))
                baseline_co2e = sum((log.calculated_kg_co2e for log in baseline_group), Decimal("0"))
                if baseline_quantity == 0:
                    continue
                baseline_value = (baseline_co2e / baseline_quantity).quantize(
                    _INTENSITY_PRECISION
                )
                delta = value - baseline_value
                if baseline_value != 0:
                    delta_pct = _pct((delta / baseline_value) * 100)
                comparison = f"{year} vs {compare_year}"
                break
            metrics.append(
                BenchmarkMetric(
                    key=f"activity:{activity_type}",
                    label=f"Activity intensity: {activity_type}",
                    unit=metric_unit,
                    value=value,
                    numerator=total_co2e,
                    denominator=total_quantity,
                    baseline_value=baseline_value,
                    delta=delta,
                    delta_pct=delta_pct,
                    comparison=comparison,
                    source=source,
                    activity_type=activity_type,
                )
            )
        return metrics

    # ------------------------------------------------------------------
    # Group totals + side effects
    # ------------------------------------------------------------------

    async def _by_group(
        self,
        request: BenchmarkRequest,
        org_id: str,
        year: int,
        current: EmissionsAggregate,
        current_period: DateRange,
        baselines: dict[int, EmissionsAggregate],
    ) -> dict[str, Decimal]:
        by_group: dict[str, Decimal] = {}
        for group in request.group_by:
            if group == GROUP_YEAR:
                for compare_year, baseline in baselines.items():
                    by_group[f"{group}:{compare_year}"] = baseline.total_co2e_kg
                by_group[f"{group}:{year}"] = current.total_co2e_kg
                continue
            aggregate = await self._logs.aggregate(org_id, current_period, group)
            for key, value in aggregate.by_group.items():
                if group == GROUP_FACILITY and request.facility_filter is not None:
                    if key != request.facility_filter:
                        continue
                by_group[f"{group}:{key}"] = value
        return by_group

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

    async def _audit(
        self, org_id: str, result: BenchmarkResult, *, empty: bool = False
    ) -> None:
        """Record the benchmark run (CT-ARCH-014)."""
        if self._audit_logger is None:
            return
        try:
            await self._audit_logger.log_action(
                action="benchmark:completed",
                entity_type="organization",
                entity_id=org_id,
                correlation_id=org_id,
                actor="benchmarking_engine",
                after={
                    "empty": empty,
                    "metric_keys": [metric.key for metric in result.metrics],
                    "metric_statuses": {
                        metric.key: metric.status.value for metric in result.metrics
                    },
                },
            )
        except Exception:  # noqa: BLE001 - audit must not break the benchmark
            logger.exception(
                "failed to audit benchmark for organization %s", org_id
            )





