"""CT-MP-SUB-003 — consultant-sponsored Manual Processing coverage (pure domain).

Covers the ratified commercial model at the domain layer (no HTTP, no database):

* the plan-derived consultant coverage feature resolution;
* the selected-capacity allocation projection (allocated/available/over-allocated);
* the sponsored-entitlement decision (eligibility + coverage + allocation);
* the DIRECT **OR** SPONSORED entitlement combination;
* the legacy ``assisted_processing_available`` compatibility.
"""
from __future__ import annotations

from domain.billing import BillingPlan
from domain.manual_processing import (
    COVERAGE_ALL_ELIGIBLE_CLIENTS,
    COVERAGE_SELECTED_CLIENTS,
    ConsultantCoverage,
    ManualProcessingEntitlement,
    combine_entitlement,
    consultant_coverage_from_plan,
    entitlement_from_plan,
    sponsored_entitlement,
    summarize_allocations,
)


def _plan(*, features=None, assisted: bool = False, code: str = "consultant", version: int = 1):
    return BillingPlan(
        id="plan-1",
        plan_code=code,
        name="Plan",
        price=0,
        features=features if features is not None else {},
        assisted_processing_available=assisted,
        version=version,
    )


def _coverage(mode, capacity=None, *, enabled=True):
    return ConsultantCoverage(enabled=enabled, mode=mode, selected_capacity=capacity)


class TestCoverageFromPlan:
    """Consultant coverage is derived from the firm's OWN subscription plan."""

    def test_no_plan_is_no_coverage(self) -> None:
        coverage = consultant_coverage_from_plan(None)
        assert coverage.enabled is False
        assert coverage.mode is None

    def test_absent_feature_block_is_no_coverage(self) -> None:
        coverage = consultant_coverage_from_plan(_plan(features={}))
        assert coverage.enabled is False

    def test_selected_clients_coverage(self) -> None:
        coverage = consultant_coverage_from_plan(
            _plan(
                code="consultant-10",
                version=2,
                features={
                    "consultant_manual_processing": {
                        "enabled": True,
                        "mode": "SELECTED_CLIENTS",
                        "selected_capacity": 10,
                    }
                },
            )
        )
        assert coverage.enabled is True
        assert coverage.mode == COVERAGE_SELECTED_CLIENTS
        assert coverage.selected_capacity == 10
        assert coverage.plan_code == "consultant-10"
        assert coverage.plan_version == 2

    def test_all_eligible_coverage(self) -> None:
        coverage = consultant_coverage_from_plan(
            _plan(
                features={
                    "consultant_manual_processing": {
                        "enabled": True,
                        "mode": "ALL_ELIGIBLE_CLIENTS",
                    }
                }
            )
        )
        assert coverage.enabled is True
        assert coverage.mode == COVERAGE_ALL_ELIGIBLE_CLIENTS

    def test_disabled_block_grants_no_coverage(self) -> None:
        coverage = consultant_coverage_from_plan(
            _plan(
                features={
                    "consultant_manual_processing": {
                        "enabled": False,
                        "mode": "ALL_ELIGIBLE_CLIENTS",
                    }
                }
            )
        )
        assert coverage.enabled is False
        assert coverage.mode is None

    def test_unrecognised_mode_is_fail_closed(self) -> None:
        """A malformed mode must never silently grant all-eligible coverage."""
        coverage = consultant_coverage_from_plan(
            _plan(
                features={
                    "consultant_manual_processing": {
                        "enabled": True,
                        "mode": "UNLIMITED_TOTALLY_FREE",
                    }
                }
            )
        )
        assert coverage.enabled is False
        assert coverage.mode is None


class TestAllocationSummary:
    """Selected capacity is finite; over-allocation is surfaced, never hidden."""

    def test_selected_available_capacity(self) -> None:
        usage = summarize_allocations(_coverage(COVERAGE_SELECTED_CLIENTS, 25), 18)
        assert usage.capacity == 25
        assert usage.allocated == 18
        assert usage.available == 7
        assert usage.over_allocated == 0

    def test_selected_capacity_exhausted(self) -> None:
        usage = summarize_allocations(_coverage(COVERAGE_SELECTED_CLIENTS, 25), 25)
        assert usage.available == 0
        assert usage.over_allocated == 0

    def test_selected_over_allocation_is_reported(self) -> None:
        usage = summarize_allocations(_coverage(COVERAGE_SELECTED_CLIENTS, 10), 22)
        assert usage.available == 0
        assert usage.over_allocated == 12

    def test_all_eligible_has_no_finite_capacity(self) -> None:
        usage = summarize_allocations(_coverage(COVERAGE_ALL_ELIGIBLE_CLIENTS), 37)
        assert usage.capacity is None
        assert usage.available is None
        assert usage.over_allocated == 0

    def test_selected_without_capacity_is_fail_closed(self) -> None:
        usage = summarize_allocations(_coverage(COVERAGE_SELECTED_CLIENTS, None), 3)
        assert usage.available is None
        assert usage.over_allocated == 3


class TestSponsoredDecision:
    """Sponsored entitlement = eligibility AND purchased coverage (+ allocation)."""

    def test_relationship_alone_is_not_an_entitlement(self) -> None:
        decision = sponsored_entitlement(
            firm_id="firm-1",
            has_relationship=True,
            coverage=_coverage(None, enabled=False),
            allocation_active=False,
            allocated_count=0,
        )
        assert decision.entitled is False
        assert decision.reason == "no_coverage"

    def test_no_relationship_is_never_entitled(self) -> None:
        decision = sponsored_entitlement(
            firm_id=None,
            has_relationship=False,
            coverage=_coverage(COVERAGE_ALL_ELIGIBLE_CLIENTS),
            allocation_active=True,
            allocated_count=1,
        )
        assert decision.entitled is False
        assert decision.reason == "no_relationship"

    def test_all_eligible_covers_without_allocation(self) -> None:
        decision = sponsored_entitlement(
            firm_id="firm-1",
            has_relationship=True,
            coverage=_coverage(COVERAGE_ALL_ELIGIBLE_CLIENTS),
            allocation_active=False,
            allocated_count=0,
        )
        assert decision.entitled is True
        assert decision.reason == "all_eligible"

    def test_selected_requires_an_active_allocation(self) -> None:
        coverage = _coverage(COVERAGE_SELECTED_CLIENTS, 10)
        not_allocated = sponsored_entitlement(
            firm_id="firm-1",
            has_relationship=True,
            coverage=coverage,
            allocation_active=False,
            allocated_count=7,
        )
        assert not_allocated.entitled is False
        assert not_allocated.reason == "not_allocated"
        allocated = sponsored_entitlement(
            firm_id="firm-1",
            has_relationship=True,
            coverage=coverage,
            allocation_active=True,
            allocated_count=7,
        )
        assert allocated.entitled is True
        assert allocated.reason == "selected_allocated"
        assert allocated.available == 3


class TestCombination:
    """Effective entitlement is DIRECT OR SPONSORED, keeping both facts."""

    def _direct(self, entitled: bool, source: str = "feature"):
        return ManualProcessingEntitlement(entitled=entitled, source=source)

    def _sponsored(self, entitled: bool):
        return sponsored_entitlement(
            firm_id="firm-1",
            has_relationship=True,
            coverage=(
                _coverage(COVERAGE_ALL_ELIGIBLE_CLIENTS)
                if entitled
                else _coverage(None, enabled=False)
            ),
            allocation_active=False,
            allocated_count=0,
        )

    def test_both_paths_yield_one_operational_entitlement(self) -> None:
        combined = combine_entitlement(self._direct(True), self._sponsored(True))
        assert combined.entitled is True
        assert combined.source == "direct+sponsored"
        assert combined.direct_entitled is True
        assert combined.sponsored_entitled is True

    def test_direct_only_keeps_the_direct_source(self) -> None:
        combined = combine_entitlement(self._direct(True), self._sponsored(False))
        assert combined.entitled is True
        assert combined.source == "feature"

    def test_sponsored_only_is_entitled(self) -> None:
        """Direct ends while sponsorship remains -> still entitled."""
        combined = combine_entitlement(self._direct(False, "none"), self._sponsored(True))
        assert combined.entitled is True
        assert combined.source == "sponsored"
        assert combined.sponsored_mode == COVERAGE_ALL_ELIGIBLE_CLIENTS

    def test_both_inactive_is_not_entitled(self) -> None:
        combined = combine_entitlement(self._direct(False, "none"), self._sponsored(False))
        assert combined.entitled is False
        assert combined.source == "none"

    def test_no_relationship_produces_no_sponsored_component(self) -> None:
        combined = combine_entitlement(self._direct(False, "none"), None)
        assert combined.entitled is False
        assert combined.sponsored_entitled is False


class TestLegacyCompatibility:
    """Legacy ``assisted_processing_available`` still grants DIRECT entitlement."""

    def test_assisted_processing_available_is_preserved(self) -> None:
        decision = entitlement_from_plan(_plan(assisted=True))
        assert decision.entitled is True
        assert decision.source == "assisted_processing_available"

    def test_explicit_feature_flag_overrides_assisted(self) -> None:
        decision = entitlement_from_plan(
            _plan(assisted=True, features={"manual_processing": {"enabled": False}})
        )
        assert decision.entitled is False
        assert decision.source == "feature"


