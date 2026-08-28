"""CL-3 / PRC-2 — unit alias normalisation regression tests.

Covers ``core.units`` (alias table, ``normalize_unit``, ``units_equivalent``,
``resolve_unit_for_factor``, currency detection and the honest spend-based
mapping reason) so a mapped ``L`` activity calculates against a ``litres``
factor while genuinely incompatible units stay rejected.
"""

from __future__ import annotations

from decimal import Decimal

from core.units import (
    is_currency_unit,
    mapping_no_factors_reason,
    normalize_unit,
    resolve_unit_for_factor,
    units_equivalent,
)
from domain.factor import EmissionFactor


def _litres_factor() -> EmissionFactor:
    return EmissionFactor(
        id="f-diesel-litres",
        reporting_year=2026,
        activity_type="Diesel (average biofuel blend) [litres]",
        co2e_multiplier=Decimal("2.52"),
        unit="litres",
        scope="Scope 1",
    )


def test_normalize_l_to_litres() -> None:
    assert normalize_unit("L") == "litres"
    assert normalize_unit("l") == "litres"
    assert normalize_unit("litre") == "litres"
    assert normalize_unit("liters") == "litres"


def test_normalize_mass_and_energy() -> None:
    assert normalize_unit("t") == "tonnes"
    assert normalize_unit("tonne") == "tonnes"
    assert normalize_unit("kg") == "kilograms"
    assert normalize_unit("kWh") == "kWh"
    assert normalize_unit("m3") == "cubic metres"
    assert normalize_unit("m³") == "cubic metres"


def test_normalize_unknown_passthrough() -> None:
    # Unknown units are returned unchanged so the engine decides — we never
    # invent a unit or weaken validation.
    assert normalize_unit("widgets") == "widgets"
    assert normalize_unit(None) is None


def test_units_equivalent_aliases() -> None:
    assert units_equivalent("L", "litres")
    assert units_equivalent("t", "tonnes")
    assert not units_equivalent("m3", "kWh")
    assert not units_equivalent(None, "litres")


def test_resolve_unit_for_factor_l_matches_litres() -> None:
    # PRC-2: the operator enters `L`; the factor is keyed `litres`.
    assert resolve_unit_for_factor("L", _litres_factor().unit) == "litres"


def test_resolve_unit_for_factor_qualifier() -> None:
    # `kWh` against `kWh (Gross CV)` resolves to the factor's canonical unit.
    assert resolve_unit_for_factor("kWh", "kWh (Gross CV)") == "kWh (Gross CV)"


def test_resolve_unit_for_factor_genuine_mismatch_passthrough() -> None:
    # A genuine mismatch is passed through unchanged — the engine raises the
    # established UNIT_MISMATCH (validation is NOT weakened).
    assert resolve_unit_for_factor("m3", "litres") == "m3"


def test_currency_unit_detection() -> None:
    assert is_currency_unit("GBP")
    assert is_currency_unit("EUR")
    assert is_currency_unit("£")
    assert not is_currency_unit("litres")
    assert not is_currency_unit(None)


def test_mapping_no_factors_reason_spend_based() -> None:
    reason = mapping_no_factors_reason("Purchased goods", "GBP", has_factors=False)
    assert reason is not None
    assert "Spend-based activity" in reason
    assert "physical-unit" in reason


def test_mapping_no_factors_reason_none_when_found() -> None:
    assert mapping_no_factors_reason("Diesel", "L", has_factors=True) is None


def test_mapping_no_factors_reason_neutral_no_match() -> None:
    reason = mapping_no_factors_reason("Something unusual", "widgets", has_factors=False)
    assert reason is not None
    assert "No matching emission factor" in reason
