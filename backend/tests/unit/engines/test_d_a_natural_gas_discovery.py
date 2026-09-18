"""D-A discovery tests: natural-gas calorific-basis discovery in the shared engine.

These exercise the REAL :class:`FactorMatchingEngine` and the REAL
:class:`FactorSearchIndex` (no matcher mocks): an unqualified ``kWh`` request
must reach the qualified ``kWh (Gross CV)`` / ``kWh (Net CV)`` aggregates and
the deterministic basis policy must select the correct one at confidence 1.0,
while electricity / diesel / water / already-qualified requests stay untouched.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from core.units import resolve_unit_for_factor
from domain.factor import EmissionFactor
from domain.matching import MatchRequest, MatchingPipelineConfig
from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline
from infra.search_index import FactorSearchIndex

_ACT = "Fuels > Gas fuels > Natural gas (kg CO2e)"


def _factor(unit: str, factor_id: str, multiplier: str, activity: str = _ACT) -> EmissionFactor:
    return EmissionFactor(
        id=factor_id,
        reporting_year=2025,
        activity_type=f"{activity} [{unit}]",
        co2e_multiplier=Decimal(multiplier),
        unit=unit,
        scope="Scope 1",
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
        provider_key="defra",
        natural_key=("2025", f"{activity} [{unit}]", "GB", unit, "Scope 1"),
    )


def _gas(activity: str = _ACT, *, order: str = "gross_first") -> list[EmissionFactor]:
    gross = _factor("kWh (Gross CV)", "f-gross", "0.18494", activity)
    net = _factor("kWh (Net CV)", "f-net", "0.20489", activity)
    return [gross, net] if order == "gross_first" else [net, gross]


def _index(factors: list[EmissionFactor]) -> FactorSearchIndex:
    index = FactorSearchIndex()
    index.load(factors)
    return index


def _engine(factors: list[EmissionFactor]) -> FactorMatchingEngine:
    config = MatchingPipelineConfig()
    return FactorMatchingEngine(
        _index(factors), build_matching_pipeline(config), config=config
    )


def _request(activity: str, unit: str) -> MatchRequest:
    return MatchRequest(
        id=str(uuid.uuid4()),
        activity=activity,
        country="GB",
        reporting_year=2025,
        unit=unit,
        scope=None,
        organization_id=None,
        preferred_provider=None,
        max_stages=6,
    )


@pytest.mark.asyncio
async def test_unqualified_kwh_discovers_net_cv_default() -> None:
    """Requirement 1/2/7: unqualified kWh discovers both bases and picks Net CV."""
    engine = _engine(_gas())
    result = await engine.match(_request("Natural gas", "kWh"))
    assert result.status == "matched"
    assert result.factor is not None
    assert result.factor.id == "f-net"
    assert result.factor.unit == "kWh (Net CV)"
    assert result.confidence == 1.0
    assert result.methodology == "calorific_basis"
    assert "calorific_basis" in result.stages_executed


@pytest.mark.asyncio
async def test_explicit_gross_prose_selects_gross() -> None:
    """Requirement 3/4: explicit Gross CV / GCV prose selects the Gross candidate."""
    engine = _engine(_gas())
    for prose in ("Natural gas Gross CV", "Natural gas GCV"):
        result = await engine.match(_request(prose, "kWh"))
        assert result.status == "matched", prose
        assert result.factor is not None
        assert result.factor.id == "f-gross", prose
        assert result.factor.unit == "kWh (Gross CV)", prose
        assert result.confidence == 1.0, prose


@pytest.mark.asyncio
async def test_explicit_net_prose_selects_net() -> None:
    """Requirement 5/6: explicit Net CV / NCV prose selects the Net candidate."""
    engine = _engine(_gas())
    for prose in ("Natural gas Net CV", "Natural gas NCV"):
        result = await engine.match(_request(prose, "kWh"))
        assert result.status == "matched", prose
        assert result.factor is not None
        assert result.factor.id == "f-net", prose


@pytest.mark.asyncio
async def test_enumeration_order_cannot_change_selection() -> None:
    """Requirement 8: candidate enumeration order never decides the basis."""
    forward = await _engine(_gas(order="gross_first")).match(
        _request("Natural gas", "kWh")
    )
    reverse = await _engine(_gas(order="net_first")).match(
        _request("Natural gas", "kWh")
    )
    assert forward.factor is not None and reverse.factor is not None
    assert forward.factor.id == reverse.factor.id == "f-net"

    g_forward = await _engine(_gas(order="gross_first")).match(
        _request("Natural gas Gross CV", "kWh")
    )
    g_reverse = await _engine(_gas(order="net_first")).match(
        _request("Natural gas Gross CV", "kWh")
    )
    assert g_forward.factor is not None and g_reverse.factor is not None
    assert g_forward.factor.id == g_reverse.factor.id == "f-gross"


@pytest.mark.asyncio
async def test_already_qualified_request_is_not_rediscovered() -> None:
    """A qualified request has nothing to discover — discovery stays inert."""
    engine = _engine(_gas())
    result = await engine.match(_request("Natural gas", "kWh (Net CV)"))
    assert result.status == "matched"
    assert result.factor is not None
    assert result.factor.id == "f-net"
    assert result.methodology != "calorific_basis"


@pytest.mark.asyncio
async def test_single_qualifier_and_unrelated_families_are_untouched() -> None:
    """Requirements 11/12: electricity / diesel / water behaviour is unchanged."""
    factors = [
        _factor("kWh", "f-elec", "0.20707", "Electricity > UK electricity (kg CO2e)"),
        _factor(
            "litres",
            "f-diesel",
            "2.51233",
            "Fuels > Liquid fuels > Diesel (average biofuel blend)",
        ),
        _factor("m3", "f-water", "0.14900", "Water supply > Water supply (kg CO2e)"),
    ]
    engine = _engine(factors)
    for activity, unit, expected in (
        ("Electricity > UK electricity (kg CO2e)", "kWh", "f-elec"),
        ("Fuels > Liquid fuels > Diesel (average biofuel blend)", "litres", "f-diesel"),
        ("Water supply > Water supply (kg CO2e)", "m3", "f-water"),
    ):
        result = await engine.match(_request(activity, unit))
        assert result.status == "matched", activity
        assert result.factor is not None
        assert result.factor.id == expected, activity
        assert result.methodology != "calorific_basis", activity


def test_gross_net_remain_bases_not_conversions() -> None:
    """Requirement 9/10: 027 family safety — Gross/Net are never interchangeable."""
    assert resolve_unit_for_factor("kWh (Gross CV)", "kWh (Net CV)") == "kWh (Gross CV)"
    assert resolve_unit_for_factor("kWh (Net CV)", "kWh (Gross CV)") == "kWh (Net CV)"
    assert resolve_unit_for_factor("kWh", "kWh (Gross CV)") == "kWh (Gross CV)"
    assert resolve_unit_for_factor("litres", "kWh (Net CV)") == "litres"


def test_discovery_is_inert_without_competing_qualifiers() -> None:
    """The helper only acts when >1 distinct qualifier of one base unit exists."""
    single = _engine([_factor("kWh (Net CV)", "f-net", "0.20489")])
    assert single._discover_calorific_basis(_request("Natural gas", "kWh")) is None
    both = _engine(_gas())
    assert both._discover_calorific_basis(_request("Natural gas", "kWh (Gross CV)")) is None
    assert both._discover_calorific_basis(_request("Natural gas", "litres")) is None
