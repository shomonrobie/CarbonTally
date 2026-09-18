"""CL-3 / 027 — unit-family alias correctness (calculation safety).

Locks the fix for the cross-family coercion found by
`CT-STEP2-MULTILINE-PROVENANCE-MAPPING-026`:

    resolve_unit_for_factor("t", "litres") -> "litres"     # WRONG (mass became volume)

while the same-unit spellings the resolver is actually for are preserved:

    resolve_unit_for_factor("L", "litres")           -> "litres"
    resolve_unit_for_factor("kWh", "kWh (Gross CV)") -> "kWh (Gross CV)"

The seam resolves **spellings**, never **conversions**: no quantity is converted here, so a
different unit — even within one family — must be left alone for the engine's established
``UNIT_MISMATCH`` guard to reject it.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from core.units import (
    UNIT_ALIASES,
    normalize_unit,
    resolve_unit_for_factor,
    split_qualified_unit,
)
from domain.factor import EmissionFactor, UnitMismatchError


def _litres_factor() -> EmissionFactor:
    return EmissionFactor(
        id="factor-litres",
        reporting_year=2026,
        activity_type="Fuels > Liquid fuels > Diesel (average biofuel blend) (kg CO2e)",
        co2e_multiplier=Decimal("2.5"),
        unit="litres",
        scope="scope_1",
    )


# -- the original reproducer and its siblings --------------------------------
def test_tonnes_is_not_coerced_to_litres() -> None:
    # The 026 finding: `"t" in "litres"` made a mass unit look like a volume unit.
    assert resolve_unit_for_factor("t", "litres") == "t"
    assert resolve_unit_for_factor("tonnes", "litres") == "tonnes"
    assert resolve_unit_for_factor("T", "litres") == "T"


@pytest.mark.parametrize(
    ("unit", "factor_unit"),
    [
        ("t", "litres"),            # mass vs volume
        ("tonnes", "litres"),
        ("kg", "litres"),
        ("t", "kWh"),               # mass vs energy
        ("tonnes", "kWh"),
        ("litres", "km"),           # volume vs distance
        ("m3", "tonnes"),           # volume vs mass
        ("kwh", "tonnes"),          # energy vs mass
        ("miles", "kWh"),
    ],
)
def test_incompatible_units_pass_through_unchanged(unit: str, factor_unit: str) -> None:
    assert resolve_unit_for_factor(unit, factor_unit) == unit


# -- legitimate spellings must be untouched ----------------------------------
@pytest.mark.parametrize(
    ("unit", "factor_unit", "expected"),
    [
        ("L", "litres", "litres"),
        ("l", "litres", "litres"),
        ("ltr", "litres", "litres"),
        ("litre", "litres", "litres"),
        ("m3", "cubic metres", "cubic metres"),
        ("m³", "cubic metres", "cubic metres"),
        ("kwh", "kWh", "kWh"),
        ("KWH", "kWh", "kWh"),
        ("kg", "kilograms", "kilograms"),
        ("t", "tonnes", "tonnes"),
        ("ton", "tonnes", "tonnes"),
        ("km", "km", "km"),
        ("miles", "miles", "miles"),
        ("MWh", "MWh", "MWh"),
        # qualified factor spelling of the SAME base unit
        ("kWh", "kWh (Gross CV)", "kWh (Gross CV)"),
        ("kwh", "kWh (Net CV)", "kWh (Net CV)"),
    ],
)
def test_valid_aliases_still_resolve(unit: str, factor_unit: str, expected: str) -> None:
    assert resolve_unit_for_factor(unit, factor_unit) == expected


def test_different_units_of_one_family_are_not_silently_adopted() -> None:
    # No quantity conversion happens at this seam, so adopting the factor's unit here
    # would mis-scale the quantity (1 L ≠ 1 m³). The engine must stay authoritative.
    assert resolve_unit_for_factor("litres", "cubic metres") == "litres"
    assert resolve_unit_for_factor("m3", "litres") == "m3"
    assert resolve_unit_for_factor("tonnes", "kilograms") == "tonnes"
    assert resolve_unit_for_factor("L", "kWh (Gross CV)") == "L"


def test_unit_less_factor_returns_the_typed_unit() -> None:
    assert resolve_unit_for_factor("t", None) == "t"
    assert resolve_unit_for_factor(None, "litres") == "litres"


# -- calculation safety: the engine rejects instead of mis-calculating -------
@pytest.mark.parametrize(
    ("unit", "factor_unit"),
    [("t", "litres"), ("tonnes", "litres"), ("kg", "litres"), ("m3", "tonnes")],
)
def test_cross_family_unit_is_rejected_by_the_engine(unit: str, factor_unit: str) -> None:
    factor = _litres_factor()
    resolved = resolve_unit_for_factor(unit, factor_unit)
    assert resolved != factor.unit, "the factor's unit must not be substituted"
    with pytest.raises(UnitMismatchError):
        factor.calculate_emissions(Decimal("60"), resolved)


def test_compatible_unit_still_calculates() -> None:
    factor = _litres_factor()
    resolved = resolve_unit_for_factor("L", factor.unit)
    assert resolved == factor.unit
    assert factor.calculate_emissions(Decimal("100"), resolved) == Decimal("250.000000")


# -- taxonomy evidence (existing vocabulary, not a parallel one) -------------
def test_existing_alias_taxonomy_covers_the_expected_families() -> None:
    canonical = set(UNIT_ALIASES.values())
    assert {"litres", "cubic metres"} <= canonical        # volume
    assert {"tonnes", "kilograms", "grams"} <= canonical  # mass
    assert {"kWh", "MWh", "MJ", "GJ"} <= canonical        # energy
    assert {"km", "miles", "tonne.km"} <= canonical       # distance / freight
    # every alias resolves 1:1 through the single existing normaliser
    assert all(normalize_unit(alias) == target for alias, target in UNIT_ALIASES.items())
    assert split_qualified_unit("kWh (Gross CV)") == ("kWh", "Gross CV")


# -- the 026 multi-line oracle units stay valid ------------------------------
def test_multi_row_oracle_units_resolve_against_same_unit_factors() -> None:
    pairs = {"kwh": "kWh", "l": "litres", "t": "tonnes", "m³": "cubic metres"}
    for source_unit, factor_unit in pairs.items():
        assert normalize_unit(source_unit) == factor_unit
        assert resolve_unit_for_factor(source_unit, factor_unit) == factor_unit

