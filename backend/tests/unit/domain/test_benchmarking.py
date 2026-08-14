"""Unit tests for domain.benchmarking (Phase 9B domain contracts)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from dataclasses import FrozenInstanceError
from domain.benchmarking import (
    BenchmarkAvailability,
    BenchmarkMetric,
    BenchmarkRequest,
    BenchmarkResult,
    GROUP_FACILITY,
    GROUP_SCOPE,
    GROUP_YEAR,
    METRIC_TOTAL,
)


def make_metric(key: str = "total", label: str = "Total emissions") -> BenchmarkMetric:
    return BenchmarkMetric(
        key=key,
        label=label,
        unit="kg CO2e",
        value=Decimal("100"),
        numerator=Decimal("100"),
    )


class TestBenchmarkAvailability:
    def test_values(self) -> None:
        assert BenchmarkAvailability.AVAILABLE.value == "available"
        assert BenchmarkAvailability.NOT_AVAILABLE.value == "not_available"
        assert BenchmarkAvailability.INSUFFICIENT_DATA.value == "insufficient_data"
        assert BenchmarkAvailability.ZERO_DENOMINATOR.value == "zero_denominator"
        assert BenchmarkAvailability.INVALID_DENOMINATOR.value == "invalid_denominator"
        assert BenchmarkAvailability.INCOMPATIBLE_UNIT.value == "incompatible_unit"
        assert BenchmarkAvailability.INCOMPATIBLE_PERIOD.value == "incompatible_period"


class TestBenchmarkMetric:
    def test_constructs(self) -> None:
        metric = make_metric()
        assert metric.key == "total"
        assert metric.label == "Total emissions"
        assert metric.unit == "kg CO2e"
        assert metric.status is BenchmarkAvailability.AVAILABLE
        assert metric.value == Decimal("100")
        assert metric.numerator == Decimal("100")
        assert metric.denominator is None
        assert metric.baseline_value is None
        assert metric.delta is None
        assert metric.delta_pct is None
        assert metric.comparison == ""
        assert metric.source == ""
        assert metric.scope is None
        assert metric.facility_id is None
        assert metric.activity_type is None
        assert metric.note == ""

    def test_is_available(self) -> None:
        assert make_metric().is_available is True
        metric = BenchmarkMetric(
            key="per_fte",
            label="Emissions per FTE",
            unit="kg CO2e per FTE",
            status=BenchmarkAvailability.NOT_AVAILABLE,
        )
        assert metric.is_available is False

    def test_is_immutable(self) -> None:
        with pytest.raises(FrozenInstanceError):
            make_metric().key = "changed"  # type: ignore[misc]

    def test_rejects_empty_key(self) -> None:
        with pytest.raises(ValueError, match="key"):
            BenchmarkMetric(key="", label="Total", unit="kg CO2e")

    def test_rejects_empty_label(self) -> None:
        with pytest.raises(ValueError, match="label"):
            BenchmarkMetric(key="total", label="", unit="kg CO2e")


class TestBenchmarkRequest:
    def test_constructs_defaults(self) -> None:
        request = BenchmarkRequest(organization_id="org-1", reporting_year=2025)
        assert request.organization_id == "org-1"
        assert request.reporting_year == 2025
        assert request.compare_years == ()
        assert request.group_by == (GROUP_YEAR, GROUP_FACILITY, GROUP_SCOPE)
        assert "total" in request.metrics
        assert request.facility_filter is None

    def test_accepts_explicit_config(self) -> None:
        request = BenchmarkRequest(
            organization_id="org-1",
            reporting_year=2025,
            compare_years=(2024, 2023),
            group_by=("month",),
            metrics=(METRIC_TOTAL,),
            facility_filter="fac-1",
        )
        assert request.compare_years == (2024, 2023)
        assert request.group_by == ("month",)
        assert request.metrics == (METRIC_TOTAL,)
        assert request.facility_filter == "fac-1"

    def test_rejects_empty_organization(self) -> None:
        with pytest.raises(ValueError, match="organization_id"):
            BenchmarkRequest(organization_id="", reporting_year=2025)

    def test_rejects_implausible_year(self) -> None:
        with pytest.raises(ValueError, match="reporting_year"):
            BenchmarkRequest(organization_id="org-1", reporting_year=1899)

    def test_rejects_empty_metrics(self) -> None:
        with pytest.raises(ValueError, match="metrics"):
            BenchmarkRequest(organization_id="org-1", reporting_year=2025, metrics=())

    def test_rejects_unsupported_metric(self) -> None:
        with pytest.raises(ValueError, match="unsupported metric"):
            BenchmarkRequest(
                organization_id="org-1", reporting_year=2025, metrics=("external_peer",)
            )

    def test_rejects_unsupported_group(self) -> None:
        with pytest.raises(ValueError, match="unsupported group_by"):
            BenchmarkRequest(
                organization_id="org-1", reporting_year=2025, group_by=("supplier",)
            )

    def test_rejects_compare_year_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="compare year"):
            BenchmarkRequest(
                organization_id="org-1", reporting_year=2025, compare_years=(1800,)
            )

    def test_rejects_compare_year_equals_reporting_year(self) -> None:
        with pytest.raises(ValueError, match="incompatible comparison period"):
            BenchmarkRequest(
                organization_id="org-1", reporting_year=2025, compare_years=(2025,)
            )


class TestBenchmarkResult:
    def test_metric_lookup(self) -> None:
        result = BenchmarkResult(
            organization_id="org-1",
            reporting_year=2025,
            metrics=(make_metric(), make_metric(key="per_fte", label="Per FTE")),
        )
        assert result.metric("total") is not None
        assert result.metric("per_fte") is not None
        assert result.metric("missing") is None

    def test_defaults(self) -> None:
        result = BenchmarkResult(organization_id="org-1", reporting_year=2025)
        assert result.metrics == ()
        assert result.by_scope == {}
        assert result.by_group == {}
        assert result.generated_at is not None

