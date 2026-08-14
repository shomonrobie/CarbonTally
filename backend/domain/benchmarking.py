"""Benchmarking domain objects (Backend v2.1 §9, Phase 9B contract 9.2).

Pure Python, immutable frozen dataclasses.

* :class:`BenchmarkAvailability` — per-metric availability/status vocabulary.
* :class:`BenchmarkMetric` — one benchmark row: numerator, optional
  denominator, calculated value, baseline, change, unit, status, context and
  provenance.
* :class:`BenchmarkRequest` — the engine input.
* :class:`BenchmarkResult` — the engine output (metrics + scope/group totals).

Benchmarking is **internal / self-referential** (approved Phase 9 scope): every
comparison is computed from the organisation's own ``emissions_logs`` and
``organization_metadata``. There is no external reference dataset and no
benchmark reference table in Phase 9.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Optional

#: Metric keys supported by the engine.
METRIC_TOTAL = "total"
METRIC_PER_FTE = "per_fte"
METRIC_PER_AREA = "per_area"
METRIC_PER_REVENUE = "per_revenue"
METRIC_ACTIVITY_INTENSITY = "activity_intensity"

SUPPORTED_METRICS = (
    METRIC_TOTAL,
    METRIC_PER_FTE,
    METRIC_PER_AREA,
    METRIC_PER_REVENUE,
    METRIC_ACTIVITY_INTENSITY,
)

#: Grouping dimensions supported by ``EmissionsLogsRepository.aggregate``.
GROUP_YEAR = "year"
GROUP_FACILITY = "facility"
GROUP_SCOPE = "scope"
GROUP_MONTH = "month"
GROUP_ASSET = "asset"

SUPPORTED_GROUPS = (GROUP_YEAR, GROUP_FACILITY, GROUP_SCOPE, GROUP_MONTH, GROUP_ASSET)


class BenchmarkAvailability(StrEnum):
    """Per-metric availability/status.

    ``available`` is the only successful status. ``not_available`` /
    ``zero_denominator`` / ``invalid_denominator`` / ``insufficient_data`` /
    ``incompatible_unit`` / ``incompatible_period`` are explicit, non-fabricated
    results — the engine never silently substitutes or returns zero.
    """

    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"
    INSUFFICIENT_DATA = "insufficient_data"
    ZERO_DENOMINATOR = "zero_denominator"
    INVALID_DENOMINATOR = "invalid_denominator"
    INCOMPATIBLE_UNIT = "incompatible_unit"
    INCOMPATIBLE_PERIOD = "incompatible_period"


@dataclass(frozen=True, slots=True)
class BenchmarkMetric:
    """One benchmark result row.

    Attributes:
        key: Stable key (``total``, ``per_fte``, ``per_area``, ``per_revenue``,
            ``facility:<id>``, ``scope:<label>``, ``activity:<activity_type>``).
        label: Human-readable label.
        unit: Unit of ``value`` (provenance-aware, e.g. ``kg CO2 per FTE``).
        status: Availability/status of this metric.
        value: Calculated value (``None`` unless ``available``).
        numerator: Emissions numerator (kg CO2e / kg CO2).
        denominator: Denominator when applicable (FTE, m², GBP, activity qty).
        baseline_value: Baseline-period value (YoY), when available.
        delta: ``value - baseline_value`` when a baseline exists.
        delta_pct: Percentage change vs baseline (``None`` when unavailable).
        comparison: Comparison label (e.g. ``2025 vs 2024``).
        source: Provenance label (e.g. ``SEAI``, ``DEFRA-DESNZ,SEAI``).
        scope: Scope context when the metric is scope-scoped.
        facility_id: Facility context when the metric is facility-scoped.
        activity_type: Activity context for activity-intensity metrics.
        note: Free-text explanation for non-available results.
    """

    key: str
    label: str
    unit: str
    status: BenchmarkAvailability = BenchmarkAvailability.AVAILABLE
    value: Optional[Decimal] = None
    numerator: Optional[Decimal] = None
    denominator: Optional[Decimal] = None
    baseline_value: Optional[Decimal] = None
    delta: Optional[Decimal] = None
    delta_pct: Optional[Decimal] = None
    comparison: str = ""
    source: str = ""
    scope: Optional[str] = None
    facility_id: Optional[str] = None
    activity_type: Optional[str] = None
    note: str = ""

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("key must not be empty")
        if not self.label:
            raise ValueError("label must not be empty")

    @property
    def is_available(self) -> bool:
        """``True`` when the metric was computed successfully."""
        return self.status is BenchmarkAvailability.AVAILABLE


@dataclass(frozen=True, slots=True)
class BenchmarkRequest:
    """Input contract for the Benchmarking Engine (Phase 9 contract, 9.2).

    Attributes:
        organization_id: The organisation whose data is benchmarked.
        reporting_year: The reporting (current/comparison) year.
        compare_years: Baseline year(s) for year-over-year comparisons. Must
            differ from ``reporting_year`` (else ``INCOMPATIBLE_PERIOD``).
        group_by: Grouping dimensions for the result totals (year/facility/
            scope/month/asset).
        metrics: Metric keys to compute (defaults to all five).
        facility_filter: When set, restrict facility-scoped results to this
            facility.
    """

    organization_id: str
    reporting_year: int
    compare_years: tuple[int, ...] = ()
    group_by: tuple[str, ...] = (GROUP_YEAR, GROUP_FACILITY, GROUP_SCOPE)
    metrics: tuple[str, ...] = SUPPORTED_METRICS
    facility_filter: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.organization_id:
            raise ValueError("organization_id must not be empty")
        if not (1990 <= self.reporting_year <= 2100):
            raise ValueError(
                f"reporting_year {self.reporting_year} outside supported range 1990-2100"
            )
        if not self.metrics:
            raise ValueError("metrics must not be empty")
        for metric in self.metrics:
            if metric not in SUPPORTED_METRICS:
                raise ValueError(f"unsupported metric {metric!r}")
        for group in self.group_by:
            if group not in SUPPORTED_GROUPS:
                raise ValueError(f"unsupported group_by {group!r}")
        for year in self.compare_years:
            if not (1990 <= year <= 2100):
                raise ValueError(
                    f"compare year {year} outside supported range 1990-2100"
                )
            if year == self.reporting_year:
                raise ValueError(
                    f"compare year {year} must differ from reporting_year "
                    f"{self.reporting_year} (incompatible comparison period)"
                )


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """The outcome of a benchmarking run.

    Attributes:
        organization_id: The organisation benchmarked.
        reporting_year: The reporting year benchmarked.
        metrics: Every computed metric (including explicit non-available ones).
        by_scope: Total emissions per scope for the reporting year.
        by_group: Total emissions per requested group (keys prefixed with the
            group name, e.g. ``year:2025``, ``facility:<id>``).
        generated_at: When the result was produced.
    """

    organization_id: str
    reporting_year: int
    metrics: tuple[BenchmarkMetric, ...] = ()
    by_scope: dict[str, Decimal] = field(default_factory=dict)
    by_group: dict[str, Decimal] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def metric(self, key: str) -> Optional[BenchmarkMetric]:
        """Return the metric with ``key``, or ``None``."""
        return next((m for m in self.metrics if m.key == key), None)

