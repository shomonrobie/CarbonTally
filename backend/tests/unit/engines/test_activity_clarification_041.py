"""041 — focused tests for the activity-clarification layer (F-039-1)."""
from __future__ import annotations

from decimal import Decimal

from domain.factor import EmissionFactor
from engines.activity_clarification import (
    assess_activity_evidence,
    decline_clarification,
    resolve_clarification,
)


def _f(name: str, *, unit: str = "tonnes", scope: str = "Scope 3", value: str = "1.26338",
       fid: str = "f-1") -> EmissionFactor:
    text = f"{name} [{unit}]" if "[" not in name else name
    return EmissionFactor(
        id=fid, reporting_year=2025, activity_type=text, co2e_multiplier=Decimal(value),
        unit=unit, scope=scope, factor_source="DEFRA-DESNZ", factor_set="DEFRA-2025",
        country="GB", provider_key="DEFRA-DESNZ", natural_key=("2025", text, "GB", unit, scope),
    )


def _waste_candidates() -> list:
    return [
        _f("Waste disposal > Construction > Aggregates - Landfill (kg CO2e)", fid="lf"),
        _f("Waste disposal > Construction > Aggregates - Open-loop (kg CO2e)", value="1.00835",
           fid="ol"),
        _f("Waste disposal > Construction > Aggregates - Incineration with Energy Recovery "
           "(kg CO2e)", value="0.02106", fid="inc"),
        _f("Fuels > Liquid fuels > Waste oils (kg CO2e)", scope="Scope 1",
           value="3219.37916", fid="oils"),
    ]


def test_bare_waste_is_not_resolved_and_exposes_semantic_options_only() -> None:
    evidence = assess_activity_evidence("Waste", _waste_candidates(), unit="tonnes")
    assert evidence.verdict in ("insufficient_evidence", "clarification_required")
    assert evidence.selected_factor_id is None
    assert evidence.options, "eligible semantic groups must be exposed as choices"
    assert all(len(o.id.split("|")) == 3 for o in evidence.options)  # family|route|variant
    assert not any(o.id in {"lf", "ol", "inc", "oils"} for o in evidence.options)


def test_bare_waste_never_yields_a_waste_oils_factor() -> None:
    evidence = assess_activity_evidence("Waste", _waste_candidates(), unit="tonnes")
    assert evidence.selected_factor_id is None
    assert all("oils" not in o.id for o in evidence.options)


def test_waste_disposal_without_route_requires_clarification_across_routes() -> None:
    evidence = assess_activity_evidence("Waste disposal", _waste_candidates(), unit="tonnes")
    assert evidence.verdict == "clarification_required"
    labels = {o.semantic_term for o in evidence.options}
    assert {"Landfill", "Open-loop recycling"} <= labels


def test_waste_oils_evidence_is_sufficient() -> None:
    evidence = assess_activity_evidence("Waste oils", _waste_candidates(), unit="tonnes")
    assert evidence.verdict == "sufficient"
    assert evidence.selected_factor_id == "oils"


def test_route_specific_evidence_needs_no_clarification() -> None:
    for activity, expected in (("Waste disposal Landfill", "lf"),
                               ("Waste disposal Open-loop", "ol")):
        evidence = assess_activity_evidence(activity, _waste_candidates(), unit="tonnes")
        assert evidence.verdict == "sufficient", activity
        assert evidence.selected_factor_id == expected, activity


def test_user_clarification_landfill_resolves_through_the_policy() -> None:
    record, factor = resolve_clarification(
        "Waste", "Landfill", _waste_candidates(), unit="tonnes",
        activity_key="item-1", actor_id="user-a", actor_scope="org-1",
    )
    assert record.original_activity == "Waste"          # evidence never mutated
    assert record.clarification == "Landfill"           # kept separately
    assert record.policy_input == "Waste Landfill"      # clarification is evidence
    assert record.outcome_status == "selected"
    assert factor is not None and factor.id == "lf"
    assert record.selected_factor_id == "lf"
    assert record.actor_id == "user-a" and record.actor_scope == "org-1"
    assert record.created_at and record.factor_set == "DEFRA-2025"
    assert record.reporting_year == 2025 and record.unit == "tonnes"


def test_user_clarification_waste_oils_is_not_a_factor_bypass() -> None:
    record, factor = resolve_clarification("Waste", "Waste oils", _waste_candidates(),
                                           unit="tonnes", activity_key="item-2")
    assert factor is not None and factor.id == "oils"
    assert record.clarification_type == "semantic_activity"
    assert record.policy_input == "Waste Waste oils"


def test_declined_clarification_selects_nothing() -> None:
    record = decline_clarification("Waste", activity_key="item-3", actor_id="user-b")
    assert record.outcome_status == "unresolved_declined"
    assert record.status == "declined"
    assert record.selected_factor_id is None
    assert record.original_activity == "Waste"


def test_declination_word_is_not_fed_to_the_policy() -> None:
    record, factor = resolve_clarification("Waste", "i_dont_know", _waste_candidates(),
                                           unit="tonnes", activity_key="item-4")
    assert record.policy_input == "Waste"
    assert factor is None
    assert record.outcome_status != "selected"


def test_stale_or_invalid_clarification_stays_unresolved() -> None:
    record, factor = resolve_clarification("Waste", "euro pallet recovery", _waste_candidates(),
                                           unit="tonnes", activity_key="item-5")
    assert factor is None
    assert record.outcome_status in ("ambiguous", "no_eligible_candidate", "not_applicable")


# --- idempotency / determinism / regressions ------------------------------------------------


def test_repeated_clarification_is_deterministic_and_idempotent() -> None:
    first = resolve_clarification("Waste", "Landfill", _waste_candidates(), unit="tonnes",
                                  activity_key="item-6")
    second = resolve_clarification("Waste", "Landfill", _waste_candidates(), unit="tonnes",
                                   activity_key="item-6")
    assert first[0].clarification_id == second[0].clarification_id
    assert first[0].outcome_status == second[0].outcome_status == "selected"
    assert first[1] is not None and second[1] is not None
    assert first[1].id == second[1].id


def test_diesel_ambiguity_regression_requires_clarification() -> None:
    diesel = [
        _f("Fuels > Liquid fuels > Diesel (100% mineral diesel) (kg CO2e)", unit="litres",
           scope="Scope 1", value="2.66155", fid="min"),
        _f("Fuels > Liquid fuels > Diesel (average biofuel blend) (kg CO2e)", unit="litres",
           scope="Scope 1", value="2.57082", fid="blend"),
    ]
    evidence = assess_activity_evidence("Diesel", diesel, unit="litres")
    assert evidence.verdict == "clarification_required"
    assert evidence.selected_factor_id is None
    record, factor = resolve_clarification("Diesel", "100% mineral diesel", diesel,
                                           unit="litres", activity_key="item-7")
    assert factor is not None and factor.id == "min"


def test_scope1_combustion_excludes_wtt_and_aggregate_beats_component() -> None:
    gas = [
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh (Net CV)", scope="Scope 1",
           value="0.2027", fid="agg"),
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e of CH4 per unit)", unit="kWh (Net CV)",
           scope="Scope 1", value="0.00031", fid="ch4"),
        _f("WTT- fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh (Net CV)",
           scope="Scope 3", value="0.03347", fid="wtt"),
    ]
    evidence = assess_activity_evidence("Natural gas", gas, unit="kWh (Net CV)")
    assert evidence.verdict == "sufficient"
    assert evidence.selected_factor_id == "agg"   # aggregate, Scope 1, not WTT, not CH4


def test_wtt_request_remains_selectable() -> None:
    gas = [
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh", scope="Scope 1",
           value="0.2027", fid="agg"),
        _f("WTT- fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh", scope="Scope 3",
           value="0.03347", fid="wtt"),
    ]
    evidence = assess_activity_evidence("Natural gas WTT", gas, unit="kWh")
    assert evidence.verdict == "sufficient"
    assert evidence.selected_factor_id == "wtt"


def test_unclassified_request_is_untouched() -> None:
    water = [_f("Water supply > Water supply > Water supply (kg CO2e)", unit="cubic metres",
                scope="Scope 3", value="0.1913", fid="w")]
    evidence = assess_activity_evidence("Water supply", water, unit="cubic metres")
    assert evidence.verdict == "not_required"   # outside the policy's classes → untouched


def test_d_a_net_cv_regression_through_the_engine() -> None:
    from domain.matching import MatchRequest, MatchingPipelineConfig
    from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline
    from infra.search_index import FactorSearchIndex

    factors = [
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh (Net CV)", scope="Scope 1",
           value="0.2027", fid="net"),
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh (Gross CV)", scope="Scope 1",
           value="0.18296", fid="gross"),
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e of CH4 per unit)", unit="kWh (Net CV)",
           scope="Scope 1", value="0.00031", fid="ch4"),
    ]
    index = FactorSearchIndex()
    index.load(factors)
    config = MatchingPipelineConfig()
    engine = FactorMatchingEngine(index, build_matching_pipeline(config), config=config)

    async def run():
        return await engine.match(
            MatchRequest(id="r41", activity="Natural gas", country="GB", reporting_year=2025,
                         unit="kWh", scope=None, organization_id=None, preferred_provider=None,
                         max_stages=6)
        )

    import asyncio

    result = asyncio.run(run())
    assert result.status == "matched"
    assert result.factor is not None and result.factor.id == "net"
    evidence = assess_activity_evidence("Natural gas", engine._policy_candidates(
        MatchRequest(id="r41b", activity="Natural gas", country="GB", reporting_year=2025,
                     unit="kWh", scope=None, organization_id=None, preferred_provider=None,
                     max_stages=6)), unit="kWh", preferred_unit="kWh (Net CV)")
    assert evidence.verdict == "sufficient"
    assert evidence.selected_factor_id == "net"
