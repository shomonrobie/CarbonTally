"""V3 emissions intelligence (Phase 4) — route registration + pure helpers.

The authoritative calculation/matching logic lives in the engines (tested by the
existing engine suites); these tests cover the V3 surface wiring and the
deterministic helpers (period, snapshot shaping, reproducibility verification,
factor filtering).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from api.v3_emissions import (
    build_period,
    filter_factors,
    shape_snapshot,
    verify_snapshot_row,
)
from domain.factor import EmissionFactor
from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/emissions/dashboard",
    "/api/v3/emissions/scope-breakdown",
    "/api/v3/emissions/calculations",
    "/api/v3/emissions/calculations/{snapshot_id}",
    "/api/v3/emissions/calculations/{snapshot_id}/verify",
    "/api/v3/emissions/factors",
    "/api/v3/emissions/factors/{factor_id}",
    "/api/v3/emissions/calculate",
)


def test_v3_emissions_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    missing = [
        fragment
        for fragment in EXPECTED_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"missing V3 emissions routes: {missing}"


def test_item_calculate_contract_rejects_client_supplied_result() -> None:
    """Regression guard: the frontend must never supply the calculated result."""
    from api.v3_processing_workflow import CalculatePayload

    assert "calculated_emissions_kg_co2e" not in CalculatePayload.model_fields


def _snapshot_row(content_hash: str) -> dict:
    return {
        "id": "snap-1",
        "organization_id": "org-1",
        "activity": "Electricity",
        "activity_type": "Electricity",
        "quantity": Decimal("12000"),
        "quantity_unit": "kWh",
        "co2e_multiplier": Decimal("0.2"),
        "co2e_kg": Decimal("2400.000000"),
        "scope": "Scope 2",
        "date": date(2026, 1, 15),
        "reporting_year": 2026,
        "factor_id": "f-1",
        "factor_source": "DEFRA-DESNZ",
        "factor_set": "DEFRA-2025",
        "import_batch_id": "b-1",
        "methodology": "direct_multiply",
        "algorithm_version": "v1.0",
        "calculated_at": datetime(2026, 1, 15, 12, 0, 0),
        "calculated_by": "u-1",
        "request_id": "req-1",
        "factor_kind": "emission_factor",
        "customer_factor_id": None,
        "content_hash": content_hash,
    }


def _expected_hash(row: dict) -> str:
    import hashlib

    canonical = "|".join(
        [
            str(row["quantity"]),
            row["quantity_unit"],
            str(row["co2e_multiplier"]),
            row.get("factor_kind") or "emission_factor",
            str(row.get("factor_id") or ""),
            str(row.get("customer_factor_id") or ""),
            str(row.get("scope") or ""),
            str(row["date"]),
            str(row["reporting_year"]),
            row["methodology"],
            row["algorithm_version"],
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_verify_snapshot_row_passes_for_untampered() -> None:
    row = _snapshot_row(_expected_hash(_snapshot_row("")))
    result = verify_snapshot_row(row)
    assert result["match"] is True
    assert result["content_hash_match"] is True
    assert result["tampered"] is False
    assert result["recomputed_co2e_kg"] == "2400.000000"


def test_verify_snapshot_row_detects_tampered_result() -> None:
    row = _snapshot_row(_expected_hash(_snapshot_row("")))
    row["co2e_kg"] = Decimal("9999.000000")
    result = verify_snapshot_row(row)
    assert result["match"] is False
    assert result["tampered"] is True
    assert result["discrepancy"] is not None


def test_verify_snapshot_row_detects_tampered_hash() -> None:
    row = _snapshot_row("0" * 64)
    result = verify_snapshot_row(row)
    assert result["content_hash_match"] is False
    assert result["tampered"] is True


def test_shape_snapshot_presents_human_readable_contract() -> None:
    row = _snapshot_row(_expected_hash(_snapshot_row("")))
    shaped = shape_snapshot(row)
    assert shaped["quantity"] == "12000"
    assert shaped["co2e_kg"] == "2400.000000"
    assert shaped["factor_kind"] == "emission_factor"
    assert shaped["content_hash"] == row["content_hash"]


def test_build_period_rejects_inverted_range() -> None:
    with pytest.raises(Exception):
        build_period(date(2026, 12, 31), date(2026, 1, 1))


def test_build_period_accepts_valid_range() -> None:
    period = build_period(date(2026, 1, 1), date(2026, 12, 31))
    assert period.start_date == date(2026, 1, 1)
    assert period.end_date == date(2026, 12, 31)


def _factor(**kwargs) -> EmissionFactor:
    base = dict(
        id="f-1",
        reporting_year=2025,
        activity_type="Electricity",
        co2e_multiplier=Decimal("0.2"),
        unit="kWh",
        scope="Scope 2",
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
    )
    base.update(kwargs)
    return EmissionFactor(**base)


def test_filter_factors_by_scope_source_set() -> None:
    factors = [
        _factor(id="a", scope="Scope 1", factor_source="DEFRA-DESNZ", factor_set="DEFRA-2025"),
        _factor(id="b", scope="Scope 2", factor_source="DEFRA-DESNZ", factor_set="DEFRA-2025"),
        _factor(id="c", scope="Scope 1", factor_source="SEAI", factor_set="SEAI-2025"),
    ]
    assert [f.id for f in filter_factors(factors, scope="Scope 1")] == ["a", "c"]
    assert [f.id for f in filter_factors(factors, factor_source="SEAI")] == ["c"]
    assert [f.id for f in filter_factors(factors, scope="Scope 2", factor_set="DEFRA-2025")] == ["b"]
    assert filter_factors(factors, scope="Scope 3") == []

# ---------------------------------------------------------------------------
# Scope contract (P1-F5): the Emissions form sends scope aliases (scope1) but
# the authoritative vocabulary is "Scope 1|2|3" (ValidationEngine + persisted
# columns). CalculateIn must normalise aliases so calculations never poison
# report generation with VAL_SCOPE_UNKNOWN / VAL_SCOPE_MISMATCH.
# ---------------------------------------------------------------------------


def test_normalize_scope_aliases_to_canonical() -> None:
    from api.v3_emissions import normalize_scope

    assert normalize_scope("scope1") == "Scope 1"
    assert normalize_scope("Scope 2") == "Scope 2"
    assert normalize_scope("scope3") == "Scope 3"
    assert normalize_scope("Scope 1") == "Scope 1"
    assert normalize_scope("outside of scopes") == "Outside of Scopes"
    assert normalize_scope(None) is None


def test_normalize_scope_rejects_unknown() -> None:
    from api.v3_emissions import normalize_scope

    with pytest.raises(ValueError):
        normalize_scope("scope4")
    with pytest.raises(ValueError):
        normalize_scope("nonsense")


def test_calculate_in_normalises_scope_alias() -> None:
    from api.v3_emissions import CalculateIn

    payload = CalculateIn(
        organization_id="org-a",
        activity="Natural gas",
        quantity="5.5",
        quantity_unit="tonnes",
        date=date(2025, 8, 1),
        reporting_year=2025,
        country="GB",
        scope="scope1",
    )
    assert payload.scope == "Scope 1"

    canonical = CalculateIn(
        organization_id="org-a",
        activity="Electricity",
        quantity="100",
        quantity_unit="kWh",
        date=date(2025, 8, 1),
        reporting_year=2025,
        country="GB",
        scope="Scope 2",
    )
    assert canonical.scope == "Scope 2"

    unscoped = CalculateIn(
        organization_id="org-a",
        activity="Electricity",
        quantity="100",
        quantity_unit="kWh",
        date=date(2025, 8, 1),
        reporting_year=2025,
        country="GB",
    )
    assert unscoped.scope is None


def test_calculate_in_rejects_unsupported_scope() -> None:
    from pydantic import ValidationError

    from api.v3_emissions import CalculateIn

    with pytest.raises(ValidationError):
        CalculateIn(
            organization_id="org-a",
            activity="Electricity",
            quantity="100",
            quantity_unit="kWh",
            date=date(2025, 8, 1),
            reporting_year=2025,
            country="GB",
            scope="Scope 9",
        )

