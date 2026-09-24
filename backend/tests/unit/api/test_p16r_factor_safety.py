"""P16-REMEDIATION-01 — factor-safety and supplier-contract regression tests.

Scope note (reported honestly): the *route-level* behaviour added by
P16-REMEDIATION-01 (D-1 operator-factor precedence, D-2 fail-closed guards,
D-3 supplier propagation, FY reporting-year refusal) is proven by the live
real-path harness ``tools/demo_lab/p16r_verify.py`` against the running release
backend. These unit tests lock the two *contracts* those guards depend on:

* ``api.v3_emissions.CalculateIn`` accepts the explicit ``supplier_id`` used by
  D-3, and
* ``engines.factor_selection_policy.is_component`` — the single authoritative
  classifier the D-2 guard reuses — flags gas-component rows and leaves totals
  alone.
"""
from __future__ import annotations

from decimal import Decimal

from api.v3_emissions import CalculateIn
from domain.factor import EmissionFactor
from engines.factor_selection_policy import is_component

#: The exact factor P16 observed being silently selected for a Scope 3 waste line.
P16_INVALID_ACTIVITY = "Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit) [tonnes]"
#: The operator-selected replacement (a total CO2e factor).
P16_SELECTED_ACTIVITY = "Waste disposal > Construction > Metals - Landfill (kg CO2e) [tonnes]"


def _factor(activity_type: str, scope: str, multiplier: str) -> EmissionFactor:
    return EmissionFactor(
        id="f-1",
        reporting_year=2025,
        activity_type=activity_type,
        co2e_multiplier=Decimal(multiplier),
        unit="tonnes",
        scope=scope,
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
    )


def test_calculate_in_accepts_supplier_id_for_d3() -> None:
    """D-3: the request contract carries explicit supplier attribution."""
    assert "supplier_id" in CalculateIn.model_fields
    request = CalculateIn(
        organization_id="org-1", activity="Waste", quantity="90.0",
        quantity_unit="tonnes", date="2025-03-31", reporting_year=2025,
        source_item_id="item-1", supplier_id="sup-1",
    )
    assert request.supplier_id == "sup-1"


def test_calculate_in_supplier_id_defaults_to_none() -> None:
    """D-3: no supplier supplied stays None rather than inventing one."""
    request = CalculateIn(
        organization_id="org-1", activity="Waste", quantity="90.0",
        quantity_unit="tonnes", date="2025-03-31", reporting_year=2025,
    )
    assert request.supplier_id is None


def test_is_component_flags_the_p16_invalid_factor() -> None:
    """D-2: the CH4-component row P16 selected is classified as a component."""
    factor = _factor(P16_INVALID_ACTIVITY, "Scope 1", "3.5504")
    assert is_component(factor) is True


def test_is_component_accepts_a_total_co2e_factor() -> None:
    """D-2: the operator-selected total factor must never be treated as a component."""
    factor = _factor(P16_SELECTED_ACTIVITY, "Scope 3", "1.26435")
    assert is_component(factor) is False


def test_p16_invalid_factor_violates_both_d2_conditions() -> None:
    """D-2: the P16 choice was both a component AND a scope mismatch."""
    invalid = _factor(P16_INVALID_ACTIVITY, "Scope 1", "3.5504")
    assert is_component(invalid) is True                 # condition 1
    assert invalid.scope != "Scope 3"                    # condition 2
