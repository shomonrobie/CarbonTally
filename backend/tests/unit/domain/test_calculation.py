"""Unit tests for domain.calculation."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import pytest

from domain.calculation import (
    CalculationMethodology,
    CalculationResult,
    CalculationSnapshot,
    VerificationResult,
)
from domain.factor import EmissionFactor


def make_snapshot(**overrides: object) -> CalculationSnapshot:
    values: dict[str, object] = {
        "id": "snap-1",
        "match_request_id": "mr-1",
        "organization_id": "org-1",
        "factor_id": "f-1",
        "quantity": Decimal("100"),
        "quantity_unit": "litres",
        "co2e_multiplier": Decimal("2.52"),
        "co2e_kg": Decimal("252.000000"),
        "scope": "Scope 1",
        "date": date(2025, 3, 1),
        "reporting_year": 2025,
        "methodology": "direct_multiply",
        "algorithm_version": "2.1.0",
        "created_at": date(2025, 3, 1),
        "content_hash": "",
        "source_file": None,
        "source_page": None,
    }
    values.update(overrides)
    return CalculationSnapshot(**values)  # type: ignore[arg-type]


def make_factor() -> EmissionFactor:
    return EmissionFactor(
        id="f-1",
        reporting_year=2025,
        activity_type="Fuels > Liquid fuels > Diesel ... (kg CO2e) [litres]",
        co2e_multiplier=Decimal("2.52"),
        unit="litres",
        scope="Scope 1",
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
        provider_key="defra",
        import_batch_id="batch-1",
    )


class TestCalculationSnapshot:
    def test_constructs(self) -> None:
        snap = make_snapshot()
        assert snap.co2e_kg == Decimal("252.000000")

    def test_is_immutable(self) -> None:
        snap = make_snapshot()
        with pytest.raises(FrozenInstanceError):
            snap.co2e_kg = Decimal("1")  # type: ignore[misc]

    def test_build_content_hash_is_deterministic(self) -> None:
        a = make_snapshot().build_content_hash()
        b = make_snapshot().build_content_hash()
        assert a == b
        assert len(a) == 64  # sha256 hex digest

    def test_build_content_hash_changes_with_inputs(self) -> None:
        base = make_snapshot().build_content_hash()
        changed_quantity = make_snapshot(quantity=Decimal("200")).build_content_hash()
        changed_factor = make_snapshot(factor_id="f-2").build_content_hash()
        changed_method = make_snapshot(methodology="distance_based").build_content_hash()
        assert base != changed_quantity
        assert base != changed_factor
        assert base != changed_method

    def test_verify_reproducibility(self) -> None:
        snap = make_snapshot()
        recomputed = (snap.quantity * snap.co2e_multiplier).quantize(Decimal("0.000001"))
        assert snap.verify_reproducibility(recomputed) is True
        assert snap.verify_reproducibility(recomputed + Decimal("0.01")) is False


class TestCalculationResult:
    def test_constructs(self) -> None:
        snap = make_snapshot()
        factor = make_factor()
        result = CalculationResult(
            co2e_kg=Decimal("252.000000"),
            co2e_tonnes=Decimal("0.252"),
            snapshot=snap,
            factor_used=factor,
            methodology=CalculationMethodology.DIRECT_MULTIPLY,
        )
        assert result.co2e_tonnes == Decimal("0.252")
        assert result.factor_used.id == "f-1"
        assert result.methodology is CalculationMethodology.DIRECT_MULTIPLY


class TestVerificationResult:
    def test_matching(self) -> None:
        assert VerificationResult(match=True).match is True

    def test_discrepancy(self) -> None:
        vr = VerificationResult(match=False, discrepancy=Decimal("0.5"), tampered=True)
        assert vr.discrepancy == Decimal("0.5")
        assert vr.tampered is True
