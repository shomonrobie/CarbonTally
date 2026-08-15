"""Unit tests for V3 customer-factor integration (D-cf-5 matching precedence
and O1 calculation snapshot provenance)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

import pytest

from domain.calculation import EmissionLog
from domain.customer_factor import CustomerFactor
from domain.factor import EmissionFactor
from domain.matching import MatchRequest, MatchingPipelineConfig
from engines.calculation import CalculationEngine, CalculationRequest
from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline


# ---------------------------------------------------------------------------
# Minimal stubs
# ---------------------------------------------------------------------------


class _EmptyIndex:
    """A FactorSearch that never matches (isolates the customer-factor path)."""

    def exact_natural_key(self, key):
        return None

    def keyword_search(self, query, unit=None, country=None, provider=None, limit=10):
        return []


def _cf(*, factor_id: str, status: str = "active") -> CustomerFactor:
    return CustomerFactor(
        id=factor_id,
        organization_id="org-a",
        name="Customer Electricity",
        activity_type="Electricity",
        co2e_multiplier=Decimal("0.31"),
        unit="kWh",
        scope="Scope 2",
        country="GB",
        reporting_year=2025,
        status=status,
    )


class _StubCustomerLookup:
    def __init__(self, factors: list[CustomerFactor]) -> None:
        self._factors = factors

    async def get_active_for_org(self, org_id: str) -> list[CustomerFactor]:
        return [f for f in self._factors if f.status == "active"]


def _make_matching_engine(lookup) -> FactorMatchingEngine:
    """Build the engine over the empty index with the D-cf-5 customer-factor
    lookup.

    Mirrors the production construction in
    ``api.dependencies.get_matching_engine``; the empty index isolates the
    customer-factor path from CarbonTally pipeline matches.
    """
    return FactorMatchingEngine(
        _EmptyIndex(),
        build_matching_pipeline(MatchingPipelineConfig()),
        customer_factor_lookup=lookup,
    )


@dataclass
class _RecordingSink:
    """Records ``save_snapshot`` arguments and log persistence (O1 contract)."""

    saved: list[dict] = field(default_factory=list)
    logs: dict[str, EmissionLog] = field(default_factory=dict)

    async def save_snapshot(self, snapshot, **kwargs):
        self.saved.append(
            {
                "factor_id": snapshot.factor_id,
                "factor_kind": snapshot.factor_kind,
                "customer_factor_id": snapshot.customer_factor_id,
                "co2e_multiplier": snapshot.co2e_multiplier,
                "kwargs_factor_kind": kwargs.get("factor_kind"),
                "kwargs_customer_factor_id": kwargs.get("customer_factor_id"),
                "content_hash": snapshot.content_hash,
            }
        )
        return snapshot

    async def create(self, org_id, factor_id, quantity, unit, scope, date,
                     asset_id, facility_id, snapshot_id):
        log = EmissionLog(
            id=f"log-{snapshot_id}",
            organization_id=org_id,
            factor_id=factor_id,
            quantity=quantity,
            date=date,
            unit=unit,
            scope=scope,
            asset_id=asset_id,
            facility_id=facility_id,
            snapshot_id=snapshot_id,
            calculated_kg_co2e=Decimal("0"),
        )
        self.logs[log.id] = log
        return log

    async def save(self, entity):
        self.logs[entity.id] = entity
        return entity



# ---------------------------------------------------------------------------
# D-cf-5 — approved customer factor wins ahead of the CarbonTally pipeline
# ---------------------------------------------------------------------------


class TestCustomerFactorMatching:
    async def test_active_customer_factor_wins(self) -> None:
        lookup = _StubCustomerLookup([_cf(factor_id="cf-active")])
        engine = _make_matching_engine(lookup)
        request = MatchRequest(
            id="m1", activity="Electricity", country="GB", reporting_year=2025,
            organization_id="org-a",
        )
        result = await engine.match(request)
        assert result.status == "matched"
        assert result.factor_kind == "customer_factor"
        assert result.customer_factor_id == "cf-active"
        assert result.factor is None

    async def test_draft_customer_factor_is_not_considered(self) -> None:
        lookup = _StubCustomerLookup([_cf(factor_id="cf-draft", status="draft")])
        engine = _make_matching_engine(lookup)
        request = MatchRequest(
            id="m2", activity="Electricity", country="GB", reporting_year=2025,
            organization_id="org-a",
        )
        result = await engine.match(request)
        # Falls through to the (empty) CarbonTally pipeline.
        assert result.status == "no_match"
        assert result.factor_kind == "emission_factor"

    async def test_ambiguous_when_multiple_active(self) -> None:
        lookup = _StubCustomerLookup(
            [_cf(factor_id="cf-1"), _cf(factor_id="cf-2")]
        )
        engine = _make_matching_engine(lookup)
        request = MatchRequest(
            id="m3", activity="Electricity", country="GB", reporting_year=2025,
            organization_id="org-a",
        )
        result = await engine.match(request)
        assert result.status == "ambiguous"
        assert result.factor_kind == "customer_factor"

    async def test_no_org_scoped_request_uses_pipeline(self) -> None:
        lookup = _StubCustomerLookup([_cf(factor_id="cf-active")])
        engine = _make_matching_engine(lookup)
        request = MatchRequest(
            id="m4", activity="Electricity", country="GB", reporting_year=2025,
        )
        result = await engine.match(request)
        assert result.status == "no_match"


# ---------------------------------------------------------------------------
# O1 — customer-factor calculation snapshot provenance
# ---------------------------------------------------------------------------


class TestCustomerFactorCalculation:
    async def test_snapshot_records_customer_provenance(self) -> None:
        sink = _RecordingSink()
        engine = CalculationEngine(sink)  # type: ignore[arg-type]
        request = CalculationRequest(
            match_request_id="mr-1",
            organization_id="org-a",
            factor=None,
            customer_factor=_cf(factor_id="cf-active"),
            quantity=Decimal("100"),
            quantity_unit="kWh",
            date=date(2025, 6, 1),
            reporting_year=2025,
            activity="Electricity",
            activity_type="Electricity",
            scope="Scope 2",
        )
        result = await engine.calculate(request)
        assert result.customer_factor is not None
        assert result.customer_factor.id == "cf-active"
        assert result.snapshot.factor_kind == "customer_factor"
        assert result.snapshot.customer_factor_id == "cf-active"
        assert result.snapshot.factor_id is None
        assert sink.saved, "save_snapshot was not invoked"
        record = sink.saved[0]
        assert record["factor_kind"] == "customer_factor"
        assert record["customer_factor_id"] == "cf-active"
        assert record["factor_id"] is None
        assert record["kwargs_factor_kind"] == "customer_factor"
        assert record["kwargs_customer_factor_id"] == "cf-active"
        assert record["content_hash"]

    async def test_rejects_both_factor_sources(self) -> None:
        factor = EmissionFactor(
            id="ef-1", reporting_year=2025, activity_type="Electricity",
            co2e_multiplier=Decimal("0.2"), unit="kWh", scope="Scope 2",
            factor_source="DEFRA-DESNZ", factor_set="DEFRA-2025", country="GB",
        )
        with pytest.raises(ValueError):
            CalculationRequest(
                match_request_id="mr-2",
                organization_id="org-a",
                factor=factor,
                customer_factor=_cf(factor_id="cf-active"),
                quantity=Decimal("100"),
                quantity_unit="kWh",
                date=date(2025, 6, 1),
                reporting_year=2025,
                activity="Electricity",
                activity_type="Electricity",
            )

    async def test_rejects_no_factor_source(self) -> None:
        with pytest.raises(ValueError):
            CalculationRequest(
                match_request_id="mr-3",
                organization_id="org-a",
                factor=None,
                quantity=Decimal("100"),
                quantity_unit="kWh",
                date=date(2025, 6, 1),
                reporting_year=2025,
                activity="Electricity",
                activity_type="Electricity",
            )


