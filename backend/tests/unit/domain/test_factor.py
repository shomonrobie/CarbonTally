"""Unit tests for domain.factor."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from core.exceptions import UnitMismatchError
from domain.factor import EmissionFactor, FactorSet, FactorSetMetadata


def make_factor(**overrides: object) -> EmissionFactor:
    """Build a canonical DEFRA-style factor, overriding fields for tests."""
    values: dict[str, object] = {
        "id": "f-1",
        "reporting_year": 2025,
        "activity_type": "Fuels > Liquid fuels > Diesel ... (kg CO2e) [litres]",
        "co2e_multiplier": Decimal("2.52000"),
        "unit": "litres",
        "scope": "Scope 1",
        "factor_source": "DEFRA-DESNZ",
        "factor_set": "DEFRA-2025",
        "country": "GB",
        "provider_key": "defra",
        "import_batch_id": "batch-1",
        "natural_key": (
            "2025",
            "Fuels > Liquid fuels > Diesel ... (kg CO2e) [litres]",
            "GB",
            "litres",
            "Scope 1",
        ),
    }
    values.update(overrides)
    return EmissionFactor(**values)  # type: ignore[arg-type]


class TestEmissionFactor:
    def test_constructs(self) -> None:
        factor = make_factor()
        assert factor.id == "f-1"
        assert factor.co2e_multiplier == Decimal("2.52000")
        assert factor.import_batch_id == "batch-1"

    def test_is_immutable(self) -> None:
        factor = make_factor()
        with pytest.raises(FrozenInstanceError):
            factor.co2e_multiplier = Decimal("1")  # type: ignore[misc]

    def test_rejects_negative_multiplier(self) -> None:
        with pytest.raises(ValueError):
            make_factor(co2e_multiplier=Decimal("-0.5"))

    def test_rejects_empty_id(self) -> None:
        with pytest.raises(ValueError):
            make_factor(id="")

    def test_rejects_empty_activity(self) -> None:
        with pytest.raises(ValueError):
            make_factor(activity_type="")

    def test_rejects_implausible_year(self) -> None:
        with pytest.raises(ValueError):
            make_factor(reporting_year=1880)

    def test_calculate_emissions_matching_unit(self) -> None:
        factor = make_factor()
        result = factor.calculate_emissions(Decimal("100"), "litres")
        assert result == Decimal("252.000000")

    def test_calculate_emissions_rounds_to_six_dp(self) -> None:
        factor = make_factor(co2e_multiplier=Decimal("0.000001"))
        result = factor.calculate_emissions(Decimal("2"), "litres")
        assert result == Decimal("0.000002")
        assert result.as_tuple().exponent == -6

    def test_calculate_emissions_unitless_factor_accepts_any_unit(self) -> None:
        factor = make_factor(unit=None)
        result = factor.calculate_emissions(Decimal("10"), "m2")
        assert result == Decimal("25.200000")

    def test_calculate_emissions_unit_mismatch_raises(self) -> None:
        factor = make_factor()
        with pytest.raises(UnitMismatchError) as excinfo:
            factor.calculate_emissions(Decimal("10"), "kWh")
        assert excinfo.value.code == "UNIT_MISMATCH"

    def test_calculate_emissions_rejects_negative_quantity(self) -> None:
        factor = make_factor()
        with pytest.raises(ValueError):
            factor.calculate_emissions(Decimal("-10"), "litres")

    def test_with_new_year_returns_copy(self) -> None:
        factor = make_factor()
        updated = factor.with_new_year(2026)
        assert updated.reporting_year == 2026
        assert updated.id == factor.id
        assert updated.co2e_multiplier == factor.co2e_multiplier
        assert factor.reporting_year == 2025  # original untouched


class TestFactorSet:
    def _set(self) -> FactorSet:
        return FactorSet(
            provider_key="defra",
            reporting_year=2025,
            version="1.0",
            factors=(
                make_factor(),
                make_factor(
                    id="f-2",
                    activity_type="Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]",
                    unit="kWh",
                    natural_key=(
                        "2025",
                        "Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]",
                        "GB",
                        "kWh",
                        "Scope 1",
                    ),
                ),
            ),
            metadata=FactorSetMetadata(
                row_count=2,
                checksum="abc123",
                imported_at=datetime(2025, 4, 1, tzinfo=timezone.utc),
                source_path="DEFRA-2025.xlsx",
            ),
        )

    def test_find_by_natural_key(self) -> None:
        fs = self._set()
        found = fs.find_by_natural_key(
            ("2025", "Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]", "GB", "kWh", "Scope 1")
        )
        assert found is not None
        assert found.id == "f-2"

    def test_find_by_natural_key_missing(self) -> None:
        assert self._set().find_by_natural_key(("2025", "nope", "GB", "kWh", "Scope 1")) is None

    def test_search_by_activity_substring_case_insensitive(self) -> None:
        fs = self._set()
        hits = fs.search_by_activity("NATURAL GAS")
        assert [f.id for f in hits] == ["f-2"]

    def test_search_by_activity_with_unit_filter(self) -> None:
        fs = self._set()
        hits = fs.search_by_activity("fuels", unit="kWh")
        assert [f.id for f in hits] == ["f-2"]
        assert fs.search_by_activity("fuels", unit="m3") == []
