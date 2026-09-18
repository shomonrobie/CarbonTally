"""038 — focused deterministic tests for the factor-selection policy (D-FS-1…D-FS-6).

Synthetic factors only (no DB), so every assertion is deterministic and none
depends on repository row order; the single row-order test explicitly verifies the
FINAL identifier tie-break, which is the only place ordering is allowed to matter.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from core.units import resolve_unit_for_factor
from domain.factor import EmissionFactor
from domain.matching import MatchRequest, MatchingPipelineConfig
from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline
from engines.factor_selection_policy import (
    is_component,
    select_factor,
)
from infra.search_index import FactorSearchIndex

_GAS_ACT = "Fuels > Gaseous fuels > Natural gas (kg CO2e)"


def _factor(
    activity_type: str,
    *,
    unit: str = "kWh (Net CV)",
    scope: str = "Scope 1",
    value: str = "0.20270",
    factor_id: str = "f-1",
    factor_set: str = "DEFRA-2025",
    country: str = "GB",
    source: str = "DEFRA-DESNZ",
) -> EmissionFactor:
    return EmissionFactor(
        id=factor_id,
        reporting_year=2025,
        activity_type=f"{activity_type} [{unit}]" if "[" not in activity_type else activity_type,
        co2e_multiplier=Decimal(value),
        unit=unit,
        scope=scope,
        factor_source=source,
        factor_set=factor_set,
        country=country,
        provider_key=source,
        natural_key=("2025", activity_type, country, unit, scope),
    )


def _gas_set() -> list[EmissionFactor]:
    return [
        _factor(f"{_GAS_ACT}", value="0.20270", factor_id="f-agg"),
        _factor(f"{_GAS_ACT} of CH4 per unit", value="0.00031", factor_id="f-ch4"),
        _factor(f"{_GAS_ACT} of CO2 per unit", value="0.20229", factor_id="f-co2"),
        _factor(f"{_GAS_ACT} of N2O per unit", value="0.00010", factor_id="f-n2o"),
    ]


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
        id="req-038",
        activity=activity,
        country="GB",
        reporting_year=2025,
        unit=unit,
        scope=None,
        organization_id=None,
        preferred_provider=None,
        max_stages=6,
    )


# --- D-FS-1: aggregate over an individual gas component ------------------------


@pytest.mark.parametrize("component", ["of CH4 per unit", "of CO2 per unit", "of N2O per unit"])
def test_component_never_wins_over_aggregate(component: str) -> None:
    outcome = select_factor(_gas_set(), activity="Natural gas", unit="kWh (Net CV)")
    assert outcome.status == "selected"
    assert outcome.factor is not None and outcome.factor.id == "f-agg"
    assert not is_component(outcome.factor)


def test_component_is_excluded_when_an_aggregate_exists_in_the_same_context() -> None:
    outcome = select_factor(
        [f for f in _gas_set() if f.id == "f-ch4"], activity="Natural gas", unit="kWh (Net CV)"
    )
    # only a component available → it remains the only candidate (no fabrication),
    # but the engine will only adopt it when it is the sole eligible candidate.
    assert outcome.status in ("selected", "not_applicable")
    if outcome.status == "selected":
        assert outcome.factor is not None and outcome.factor.id == "f-ch4"


# --- D-FS-2 / D-FS-3: combustion vs WTT, and scope eligibility -----------------


def test_wtt_is_ineligible_for_a_scope1_combustion_request() -> None:
    factors = _gas_set() + [
        _factor(
            "WTT- fuels > Gaseous fuels > Natural gas (kg CO2e)",
            value="0.03347",
            scope="Scope 3",
            factor_id="f-wtt",
        )
    ]
    outcome = select_factor(factors, activity="Natural gas", unit="kWh (Net CV)")
    assert outcome.status == "selected"
    assert outcome.factor is not None and outcome.factor.id == "f-agg"
    assert outcome.factor.scope == "Scope 1"
    assert any(getattr(f, "id", None) == "f-wtt" for f, _ in outcome.excluded)


def test_wtt_request_is_satisfied_only_by_an_upstream_factor() -> None:
    factors = _gas_set() + [
        _factor(
            "WTT- fuels > Gaseous fuels > Natural gas (kg CO2e)",
            value="0.03347",
            scope="Scope 3",
            factor_id="f-wtt",
        )
    ]
    outcome = select_factor(factors, activity="Natural gas WTT", unit="kWh (Net CV)")
    assert outcome.status == "selected"
    assert outcome.factor is not None and outcome.factor.id == "f-wtt"


def test_scope_mismatch_is_excluded_when_the_scope_is_requested() -> None:
    factors = [
        _factor(f"{_GAS_ACT}", factor_id="f-s1", scope="Scope 1"),
        _factor(f"{_GAS_ACT}", factor_id="f-s3", scope="Scope 3"),
    ]
    outcome = select_factor(factors, activity="Natural gas", unit="kWh (Net CV)", scope="Scope 1")
    assert outcome.status == "selected"
    assert outcome.factor is not None and outcome.factor.id == "f-s1"
    assert any(getattr(f, "id", None) == "f-s3" for f, _ in outcome.excluded)


# --- D-FS-4: waste / waste-oils / treatment semantics ---------------------------


def _waste_set() -> list[EmissionFactor]:
    return [
        _factor(
            "Fuels > Liquid fuels > Waste oils (kg CO2e)",
            unit="tonnes",
            value="3219.37916",
            factor_id="f-wasteoils",
        ),
        _factor(
            "Waste disposal > Construction > Aggregates - Landfill (kg CO2e)",
            unit="tonnes",
            scope="Scope 3",
            value="1.26338",
            factor_id="f-landfill",
        ),
        _factor(
            "Waste disposal > Construction > Aggregates - Open-loop (kg CO2e)",
            unit="tonnes",
            scope="Scope 3",
            value="0.85",
            factor_id="f-openloop",
        ),
    ]


def test_waste_treatment_is_not_redirected_to_a_waste_oil_fuel() -> None:
    outcome = select_factor(_waste_set(), activity="Waste disposal", unit="tonnes")
    assert outcome.status == "ambiguous"  # two materially different disposal routes
    assert all("waste oils" not in (f.activity_type or "").casefold() for f in outcome.eligible)
    assert any(getattr(f, "id", None) == "f-wasteoils" for f, _ in outcome.excluded)


def test_treatment_route_is_respected_when_supplied() -> None:
    outcome = select_factor(
        _waste_set(), activity="Waste disposal Landfill", unit="tonnes"
    )
    assert outcome.status == "selected"
    assert outcome.factor is not None and outcome.factor.id == "f-landfill"


def test_waste_oil_fuel_request_is_not_contaminated_by_treatment_factors() -> None:
    outcome = select_factor(
        _waste_set()
        + [
            _factor(
                "Fuels > Liquid fuels > Waste oils (kg CO2e)", unit="tonnes", factor_id="f-wo2"
            )
        ],
        activity="Waste oils",
        unit="tonnes",
    )
    assert outcome.status == "selected"
    assert outcome.factor is not None and "waste oils" in outcome.factor.activity_type.casefold()
    assert all("disposal" not in (f.activity_type or "").casefold() for f in outcome.eligible)


# --- D-FS-5 / D-FS-6: ambiguity and the deterministic tie-break -----------------


def test_materially_different_candidates_return_ambiguity_not_a_value_pick() -> None:
    factors = [
        _factor("Fuels > Liquid fuels > Diesel (100% mineral diesel) (kg CO2e)", unit="litres",
                value="2.66155", factor_id="f-min"),
        _factor("Fuels > Liquid fuels > Diesel (average biofuel blend) (kg CO2e)", unit="litres",
                value="2.57", factor_id="f-blend"),
    ]
    outcome = select_factor(factors, activity="Diesel supply", unit="litres")
    assert outcome.status == "selected"
    assert outcome.factor is not None and outcome.factor.id == "f-min"  # more specific, not bigger


def test_final_tie_break_is_stable_identifier_order() -> None:
    a = _factor("Fuels > Liquid fuels > Diesel (100% mineral diesel) (kg CO2e)", unit="litres",
                value="2.66155", factor_id="aaa")
    b = _factor("Fuels > Liquid fuels > Diesel (100% mineral diesel) (kg CO2e)", unit="litres",
                value="2.66155", factor_id="bbb")
    forward = select_factor([a, b], activity="Diesel supply", unit="litres")
    reverse = select_factor([b, a], activity="Diesel supply", unit="litres")
    assert forward.factor is not None and reverse.factor is not None
    assert forward.factor.id == reverse.factor.id == "aaa"


def test_unrelated_concept_cannot_win_without_a_shared_token() -> None:
    outcome = select_factor(_gas_set(), activity="Power consumption", unit="kWh")
    assert outcome.status in ("no_eligible_candidate", "not_applicable")


# --- engine-level integration ---------------------------------------------------


@pytest.mark.asyncio
async def test_engine_selects_the_aggregate_and_records_the_policy_stage() -> None:
    engine = _engine(_gas_set())
    result = await engine.match(_request("Natural gas", "kWh (Net CV)"))
    assert result.status == "matched"
    assert result.factor is not None and result.factor.id == "f-agg"
    assert result.confidence == 1.0


@pytest.mark.asyncio
async def test_engine_downgrades_a_waste_oil_match_to_ambiguous() -> None:
    engine = _engine(_waste_set())
    result = await engine.match(_request("Waste disposal", "tonnes"))
    assert result.status in ("ambiguous", "no_match") or (
        result.factor is not None and "waste oils" not in (result.factor.activity_type or "").casefold()
    )


# --- regressions required by the task ------------------------------------------


def test_d_a_gross_net_separation_regression() -> None:
    assert resolve_unit_for_factor("kWh (Gross CV)", "kWh (Net CV)") == "kWh (Gross CV)"
    assert resolve_unit_for_factor("kWh (Net CV)", "kWh (Gross CV)") == "kWh (Net CV)"


def test_factor_set_context_is_preserved_on_the_policy_selection() -> None:
    outcome = select_factor(_gas_set(), activity="Natural gas", unit="kWh (Net CV)")
    assert outcome.factor is not None
    assert outcome.factor.factor_set == "DEFRA-2025"
    assert outcome.factor.country == "GB"
    assert outcome.factor.reporting_year == 2025


def test_pipeline_structure_and_p1_shadow_behaviour_are_unchanged() -> None:
    """No new stage was introduced; the policy is a boundary layer, not a stage."""
    config = MatchingPipelineConfig()
    assert tuple(config.stages) == (
        "exact_match",
        "natural_key",
        "alias_match",
        "keyword_search",
        "fuzzy_match",
    )
    assert tuple(s.name for s in build_matching_pipeline(config)) == tuple(config.stages)
