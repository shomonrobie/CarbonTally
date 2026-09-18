"""039 — focused tests for the F-038-1 / F-038-2 follow-ups (deterministic, no DB)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from domain.factor import EmissionFactor
from domain.matching import MatchRequest, MatchingPipelineConfig
from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline
from engines.factor_selection_policy import select_factor
from infra.search_index import FactorSearchIndex


def _f(name: str, *, unit: str = "litres", scope: str = "Scope 1", value: str = "2.66155",
       fid: str = "f-1") -> EmissionFactor:
    text = f"{name} [{unit}]" if "[" not in name else name
    return EmissionFactor(
        id=fid, reporting_year=2025, activity_type=text, co2e_multiplier=Decimal(value),
        unit=unit, scope=scope, factor_source="DEFRA-DESNZ", factor_set="DEFRA-2025",
        country="GB", provider_key="DEFRA-DESNZ", natural_key=("2025", text, "GB", unit, scope),
    )


_MIN = "Fuels > Liquid fuels > Diesel (100% mineral diesel) (kg CO2e)"
_BLEND = "Fuels > Liquid fuels > Diesel (average biofuel blend) (kg CO2e)"
_DEV = "Bioenergy > Biofuel > Development diesel (kg CO2e)"


def test_f038_1_bare_diesel_with_two_products_is_ambiguous() -> None:
    """Two materially different diesel products, no product evidence → ambiguity."""
    outcome = select_factor([_f(_MIN, fid="a"), _f(_BLEND, fid="b")], activity="Diesel",
                            unit="litres")
    assert outcome.status == "ambiguous"
    assert {g[2] for g in outcome.groups} == {"mineral", "biofuel blend"}


def test_f038_1_bio_product_never_wins_on_lexical_order() -> None:
    out1 = select_factor([_f(_DEV, value="0.03705", fid="zzz"), _f(_MIN, fid="aaa")],
                         activity="Diesel", unit="litres")
    out2 = select_factor([_f(_MIN, fid="aaa"), _f(_DEV, value="0.03705", fid="zzz")],
                         activity="Diesel", unit="litres")
    for out in (out1, out2):
        assert out.status == "selected"
        assert out.factor is not None and "mineral diesel" in out.factor.activity_type


def test_f038_1_product_qualified_request_selects_that_product() -> None:
    for activity, expected in (("Diesel 100% mineral diesel", "a"),
                               ("Diesel average biofuel blend", "b")):
        outcome = select_factor([_f(_MIN, fid="a"), _f(_BLEND, fid="b")], activity=activity,
                                unit="litres")
        assert outcome.status == "selected", activity
        assert outcome.factor is not None and outcome.factor.id == expected, activity


def test_f038_1_single_diesel_candidate_is_selected_deterministically() -> None:
    outcome = select_factor([_f(_MIN, fid="only")], activity="Diesel", unit="litres")
    assert outcome.status == "selected"
    assert outcome.factor is not None and outcome.factor.id == "only"


def test_f038_1_per_litre_and_per_km_diesel_are_not_confused() -> None:
    per_km = _f("Business travel- land > Cars > Executive - Diesel (kg CO2e)", unit="km",
                scope="Scope 3", value="0.17088", fid="km")
    outcome = select_factor([_f(_MIN, fid="min"), per_km], activity="Diesel", unit="litres")
    assert outcome.status == "selected"
    assert outcome.factor is not None and outcome.factor.id == "min"


def test_f038_1_insufficient_evidence_returns_ambiguity_not_the_first_candidate() -> None:
    """A bio product plus two mineral products: never the lexically-first row."""
    outcome = select_factor(
        [_f(_DEV, value="0.03705", fid="a-bio"), _f(_MIN, fid="m"), _f(_BLEND, fid="bl")],
        activity="Diesel supply", unit="litres",
    )
    assert outcome.status == "ambiguous"
    assert all("development" not in str(f.activity_type) for f in outcome.eligible)


def _waste(route: str, fid: str) -> EmissionFactor:
    return _f(f"Waste disposal > Construction > Aggregates - {route} (kg CO2e)", unit="tonnes",
              scope="Scope 3", value="1.26338", fid=fid)


def test_f038_2_waste_treatment_never_reaches_a_waste_oil_fuel() -> None:
    oils = _f("Fuels > Liquid fuels > Waste oils (kg CO2e)", unit="tonnes", value="3219.38",
              fid="oils")
    outcome = select_factor([oils, _waste("Landfill", "lf")], activity="Waste disposal",
                            unit="tonnes")
    assert outcome.status == "selected"
    assert outcome.factor is not None and outcome.factor.id == "lf"
    assert any(getattr(f, "id", None) == "oils" for f, _ in outcome.excluded)


def test_f038_2_explicit_route_is_selected_not_the_lexically_first() -> None:
    outcome = select_factor([_waste("Closed-loop", "closed"), _waste("Landfill", "lf")],
                            activity="Waste disposal Landfill", unit="tonnes")
    assert outcome.status == "selected"
    assert outcome.factor is not None and outcome.factor.id == "lf"


def test_f038_2_missing_route_with_multiple_candidates_is_ambiguous() -> None:
    outcome = select_factor(
        [_waste("Closed-loop", "closed"), _waste("Landfill", "lf"), _waste("Open-loop", "open")],
        activity="Waste disposal", unit="tonnes",
    )
    assert outcome.status == "ambiguous"
    assert {"closed-loop", "landfill", "open-loop"} <= {g[1] for g in outcome.groups}


def test_f038_2_missing_route_with_one_candidate_is_deterministic() -> None:
    outcome = select_factor([_waste("Landfill", "lf")], activity="Waste disposal", unit="tonnes")
    assert outcome.status == "selected"
    assert outcome.factor is not None and outcome.factor.id == "lf"


def test_f038_2_waste_oil_fuel_semantics_survive() -> None:
    outcome = select_factor([_f("Fuels > Liquid fuels > Waste oils (kg CO2e)", unit="tonnes",
                                fid="oils")], activity="Waste oils", unit="tonnes")
    assert outcome.status == "selected"
    assert outcome.factor is not None
    assert "waste oils" in outcome.factor.activity_type.casefold()


@pytest.mark.asyncio
async def test_f038_gas_aggregate_prefers_the_already_decided_basis() -> None:
    gas = [
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh (Net CV)", value="0.2027",
           fid="net"),
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh (Gross CV)",
           value="0.18296", fid="gross"),
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e of CH4 per unit)", unit="kWh (Net CV)",
           value="0.00031", fid="ch4"),
    ]
    index = FactorSearchIndex()
    index.load(gas)
    config = MatchingPipelineConfig()
    engine = FactorMatchingEngine(index, build_matching_pipeline(config), config=config)
    result = await engine.match(
        MatchRequest(id="r", activity="Natural gas", country="GB", reporting_year=2025,
                     unit="kWh", scope=None, organization_id=None, preferred_provider=None,
                     max_stages=6)
    )
    assert result.status == "matched"
    assert result.factor is not None and result.factor.id == "net"


def test_f038_wtt_request_only_accepts_upstream_factors() -> None:
    upstream = _f("WTT- fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh",
                  scope="Scope 3", value="0.03347", fid="wtt")
    combustion = _f("Fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh", value="0.2027",
                    fid="comb")
    outcome = select_factor([combustion, upstream], activity="Natural gas WTT", unit="kWh")
    assert outcome.status == "selected"
    assert outcome.factor is not None and outcome.factor.id == "wtt"


def test_f038_unclassified_request_is_left_to_existing_behaviour() -> None:
    outcome = select_factor(
        [_f("Water supply > Water supply (kg CO2e)", unit="cubic metres", scope="Scope 3",
            fid="w")],
        activity="Water supply", unit="cubic metres",
    )
    assert outcome.status == "not_applicable"
