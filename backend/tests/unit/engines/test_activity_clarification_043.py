"""043 — family-level diversion trigger tests (F-042-1).

The trigger must derive from the candidate FAMILY/SCOPE structure, never from
activity strings: these tests include the two activities that broke the 042 attempt
('Gas usage', 'Power consumption') precisely to prove that.
"""
from __future__ import annotations

from decimal import Decimal

from domain.factor import EmissionFactor
from engines.activity_clarification import assess_family_conflict


def _f(name: str, *, unit: str = "tonnes", scope: str = "Scope 3", value: str = "1.26",
       fid: str = "f-1") -> EmissionFactor:
    text = f"{name} [{unit}]" if "[" not in name else name
    return EmissionFactor(
        id=fid, reporting_year=2025, activity_type=text, co2e_multiplier=Decimal(value),
        unit=unit, scope=scope, factor_source="DEFRA-DESNZ", factor_set="DEFRA-2025",
        country="GB", provider_key="DEFRA-DESNZ", natural_key=("2025", text, "GB", unit, scope),
    )


def _waste_and_fuel() -> list:
    """The real conflict shape: disposal/treatment (Scope 3) vs a waste-derived fuel (Scope 1)."""
    return [
        _f("Waste disposal > Construction > Aggregates - Landfill (kg CO2e)", fid="lf"),
        _f("Waste disposal > Construction > Aggregates - Open-loop (kg CO2e)", value="1.00835", fid="ol"),
        _f("Fuels > Liquid fuels > Waste oils (kg CO2e)", scope="Scope 1", value="3219.37", fid="oils"),
    ]


def _gas_only() -> list:
    """Category word 'gas', one combustion scope → NOT a material conflict."""
    return [
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh", scope="Scope 1",
           value="0.2027", fid="ng"),
        _f("Bioenergy > Biogas > Landfill gas (kg CO2e)", unit="kWh", scope="Scope 1",
           value="0.0002", fid="biogas"),
    ]


def _power_like() -> list:
    """Electricity-ish shape: Scope 2 consumption vs Scope 3 travel."""
    return [
        _f("UK electricity > Electricity consumption (kg CO2e)", unit="kWh", scope="Scope 2",
           value="0.20707", fid="elec"),
        _f("SECR kWh UK electricity for EVs > Cars > Battery Electric Vehicle (kg CO2e)",
           unit="km", scope="Scope 3", value="0.19642", fid="ev"),
    ]


def test_gas_usage_is_not_diverted_despite_the_category_word() -> None:
    assessment = assess_family_conflict("Gas usage", _gas_only(), unit="kWh")
    assert assessment.verdict != "clarification_required"


def test_power_consumption_is_not_diverted_despite_the_category_word() -> None:
    assessment = assess_family_conflict("Power consumption", _power_like(), unit="kWh")
    assert assessment.verdict in ("not_required", "no_candidates")


def test_bare_waste_is_diverted_on_a_real_family_conflict() -> None:
    assessment = assess_family_conflict("Waste", _waste_and_fuel(), unit="tonnes")
    assert assessment.verdict == "clarification_required"
    families = {f for f, _s in assessment.families}
    assert {"waste disposal", "fuels"} <= families
    assert assessment.options, "the real family/route choices must be offered"
    assert all(len(o.id.split("|")) == 3 for o in assessment.options)


def test_waste_disposal_ambiguity_is_left_to_the_policy() -> None:
    assessment = assess_family_conflict("Waste disposal", _waste_and_fuel(), unit="tonnes")
    assert assessment.verdict == "policy_ambiguous"
    assert assessment.selected_factor_id is None


def test_diesel_ambiguity_is_left_to_the_policy() -> None:
    diesel = [
        _f("Fuels > Liquid fuels > Diesel (100% mineral diesel) (kg CO2e)", unit="litres",
           scope="Scope 1", value="2.66155", fid="min"),
        _f("Fuels > Liquid fuels > Diesel (average biofuel blend) (kg CO2e)", unit="litres",
           scope="Scope 1", value="2.57082", fid="blend"),
    ]
    assessment = assess_family_conflict("Diesel", diesel, unit="litres")
    assert assessment.verdict == "policy_ambiguous"   # 039 behaviour preserved


def test_route_qualified_and_clarified_waste_forms_do_not_diverge() -> None:
    """Route-qualified / explicitly-clarified evidence must not divert.

    NOTE (043): the real-dataset run is the authoritative evidence for the
    route-qualified case — 'Waste Landfill' → verdict sufficient with the Landfill
    factor (be0d681d…) and 'Waste Waste oils' → sufficient with the waste-oil
    aggregate (faf9991d…). This unit test covers the clarified form that is
    reproducible with synthetic factors; the fuel distractor is excluded by the
    request class in the policy, which the 038/039/041 suites already assert.
    """
    assessment = assess_family_conflict("Waste Waste oils", _waste_and_fuel(), unit="tonnes")
    assert assessment.verdict != "clarification_required"


def test_explicit_waste_oils_resolves_without_clarification() -> None:
    oils_only = [f for f in _waste_and_fuel() if f.id == "oils"]
    assessment = assess_family_conflict("Waste oils", oils_only, unit="tonnes")
    assert assessment.verdict != "clarification_required"
    assert assessment.selected_factor_id == "oils"


def test_natural_gas_prefers_the_decided_basis_without_diverting() -> None:
    gas = [
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh (Net CV)", scope="Scope 1",
           value="0.2027", fid="net"),
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh (Gross CV)", scope="Scope 1",
           value="0.18296", fid="gross"),
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e of CH4 per unit)", unit="kWh (Net CV)",
           scope="Scope 1", value="0.00031", fid="ch4"),
    ]
    assessment = assess_family_conflict("Natural gas", gas, unit="kWh", preferred_unit="kWh (Net CV)")
    assert assessment.verdict == "sufficient"
    assert assessment.selected_factor_id == "net"


def test_upstream_is_excluded_from_the_conflict_test_so_wtt_stays_selectable() -> None:
    gas = [
        _f("Fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh", scope="Scope 1",
           value="0.2027", fid="ng"),
        _f("WTT- fuels > Gaseous fuels > Natural gas (kg CO2e)", unit="kWh", scope="Scope 3",
           value="0.03347", fid="wtt"),
    ]
    assert assess_family_conflict("Natural gas", gas, unit="kWh").verdict == "sufficient"
    wtt = assess_family_conflict("Natural gas WTT", gas, unit="kWh")
    assert wtt.selected_factor_id == "wtt"


def test_no_candidates_does_not_invent_options() -> None:
    assessment = assess_family_conflict("Power consumption", [], unit="kWh")
    assert assessment.verdict == "no_candidates"
    assert assessment.options == ()


def test_multiple_factors_in_one_family_do_not_diverge() -> None:
    same_family = [
        _f("Waste disposal > Construction > Wood - Closed-loop (kg CO2e)", fid="a"),
        _f("Waste disposal > Construction > Wood - Composting (kg CO2e)", fid="b"),
    ]
    assessment = assess_family_conflict("Waste disposal", same_family, unit="tonnes")
    assert assessment.verdict == "policy_ambiguous"   # one family → policy owns it


def test_deterministic_winner_never_diverts() -> None:
    unique = [_f("Water supply > Water supply > Water supply (kg CO2e)", unit="cubic metres",
                 scope="Scope 3", value="0.1913", fid="w")]
    assessment = assess_family_conflict("Water supply", unique, unit="cubic metres")
    assert assessment.verdict != "clarification_required"
    if assessment.verdict == "sufficient":
        assert assessment.selected_factor_id == "w"


def test_trigger_is_not_string_specific() -> None:
    """The SAME activity text flips only with the candidate structure — proving the
    verdict is derived from families/scopes, not from the string."""
    conflict = assess_family_conflict("Waste disposal", _waste_and_fuel(), unit="tonnes")
    compatible = assess_family_conflict(
        "Waste disposal",
        [_f("Waste disposal > Construction > Aggregates - Landfill (kg CO2e)", fid="lf"),
         _f("Waste disposal > Construction > Aggregates - Open-loop (kg CO2e)", fid="ol")],
        unit="tonnes",
    )
    assert compatible.verdict != "clarification_required"
    assert conflict.verdict in ("policy_ambiguous", "clarification_required")
