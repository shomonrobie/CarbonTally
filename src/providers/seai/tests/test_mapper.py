"""Unit tests: SEAI mapper (28-row classification, 20-row mapping, skips).

Offline tests against the real workbook.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from src.providers.seai import analyze_workbook, map_all, map_row
from src.providers.seai.models import (
    COUNTRY,
    FACTOR_SOURCE,
    FACTOR_SET,
    REPORTING_YEAR,
    SKIP_NON_CANONICAL_BASIS,
    SKIP_NO_FACTOR_VALUE,
)

IMPORTED_NAMES = [
    "Crude oil",
    "Gasoline / petrol (100% petroleum)",
    "Kerosene",
    "Jet Kerosene",
    "Diesel / gasoil (100% petroleum)",
    "Residual fuel oil / fuel oil",
    "LPG",
    "Biodiesel ME",
    "Road diesel (avg. biofuel content)",
    "Road petrol (avg. biofuel content)",
    "Petroleum coke",
    "Bituminous coal",
    "Anthracite",
    "Lignite",
    "Milled peat",
    "Sod peat",
    "Peat briquettes",
    "Natural gas (NCV)",
    "Electricity consumption",
    "Gross electricity supply",
]

#: Workbook row names for the 8 non-importable rows -> skip reason.
SKIPPED_NAMES = {
    "Bioethanol": SKIP_NO_FACTOR_VALUE,
    "Biodiesel HVO": SKIP_NO_FACTOR_VALUE,
    "Biodiesel CHVO": SKIP_NO_FACTOR_VALUE,
    "Biopropane": SKIP_NO_FACTOR_VALUE,
    "Biojet HVO": SKIP_NO_FACTOR_VALUE,
    "Wood pellets & briquettes": SKIP_NO_FACTOR_VALUE,
    "Wood logs & chips": SKIP_NO_FACTOR_VALUE,
    "Natural gas (GCV)": SKIP_NON_CANONICAL_BASIS,
}

#: source name -> (approx multiplier, unit, scope) for key spot-checks.
EXPECTED_VALUES = {
    "Crude oil": ("2.942558", "litres", "Scope 1"),
    "Diesel / gasoil (100% petroleum)": ("2.682327", "litres", "Scope 1"),
    "Biodiesel ME": ("0.133294", "litres", "Scope 1"),
    "Bituminous coal": ("2.633874", "kg", "Scope 1"),
    "Milled peat": ("0.741213", "kg", "Scope 1"),
    "Natural gas (NCV)": ("2.005357", "cubic metres", "Scope 1"),
    "Electricity consumption": ("0.197803", "kWh", "Scope 2"),
    "Gross electricity supply": ("0.178328", "kWh", "Scope 2"),
}


@pytest.fixture(scope="session")
def mapped(seai_data):
    factors, skipped = map_all(list(seai_data.rows))
    return seai_data, factors, skipped


def test_mapping_classifies_20_and_8(mapped):
    _, factors, skipped = mapped
    assert len(factors) == 20
    assert len(skipped) == 8


def test_mapping_imported_names(mapped):
    _, factors, _ = mapped
    assert [f.source_name for f in factors] == IMPORTED_NAMES


def test_mapping_skipped_names_and_reasons(mapped):
    _, _, skipped = mapped
    by_name = {s.name: s.reason for s in skipped}
    assert by_name == SKIPPED_NAMES


def test_mapping_values_units_scopes(mapped):
    _, factors, _ = mapped
    by_name = {f.source_name: f for f in factors}
    for name, (mult, unit, scope) in EXPECTED_VALUES.items():
        factor = by_name[name]
        assert float(factor.co2e_multiplier) == pytest.approx(float(mult), abs=1e-6), name
        assert factor.unit == unit, name
        assert factor.scope == scope, name


def test_mapping_labels_use_canonical_form(mapped):
    _, factors, _ = mapped
    for f in factors:
        assert f.activity_type.startswith(f"Fuels > ")
        assert "(kg CO2)" in f.activity_type
        assert f.activity_type.endswith(f") [{f.unit}]")


def test_electricity_pair_not_collapsed(mapped):
    _, factors, _ = mapped
    elec = {f.source_name for f in factors if f.top_section == "Electricity"}
    assert elec == {"Electricity consumption", "Gross electricity supply"}


def test_biodiesel_me_imported_with_value(mapped):
    _, factors, _ = mapped
    me = next(f for f in factors if f.source_name == "Biodiesel ME")
    assert me.co2e_multiplier > 0


def test_gas_gcv_skipped_ncv_imported(mapped):
    _, factors, skipped = mapped
    names = {f.source_name for f in factors}
    skipped_names = {s.name for s in skipped}
    assert "Natural gas (GCV)" in skipped_names
    assert "Natural gas (NCV)" in names


def test_co2_only_semantics(mapped):
    _, factors, _ = mapped
    for f in factors:
        assert f.co2_only is True
        assert f.factor_source == FACTOR_SOURCE
        assert f.factor_set == FACTOR_SET
        assert f.country == COUNTRY
        assert f.reporting_year == REPORTING_YEAR


def test_no_duplicate_natural_keys(mapped):
    _, factors, _ = mapped
    keys = [f.natural_key for f in factors]
    assert len(keys) == len(set(keys))


def test_map_row_unit_mismatch_never_generates_new_unit(mapped):
    """Units must come from the approved canonical set only."""
    _, factors, _ = mapped
    assert {f.unit for f in factors} <= {"litres", "kg", "cubic metres", "kWh"}


def test_map_row_on_gcv_skips(seai_data):
    gcv = next(r for r in seai_data.rows if r.name == "Natural gas (GCV)")
    factor, skip = map_row(gcv)
    assert factor is None
    assert skip is not None
    assert skip.reason == SKIP_NON_CANONICAL_BASIS
