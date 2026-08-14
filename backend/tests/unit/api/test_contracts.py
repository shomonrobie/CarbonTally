"""Phase 10.4 — API contract tests (request validation, serialization,
CO2/CO2e provenance preservation, optional/required fields)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.contracts import (
    BenchmarkIn,
    CalculationIn,
    FactorAliasCreate,
    FactorAliasUpdate,
    FactorMatchIn,
    ReportRequestIn,
    ValidationIn,
    factor_out,
)
from tests.unit.api.fakes import seed_defra_factor, seed_seai_factor


# ---------------------------------------------------------------------------
# Required / optional fields (request models)
# ---------------------------------------------------------------------------


def test_factor_match_requires_activity():
    with pytest.raises(ValidationError):
        FactorMatchIn(country="GB", reporting_year=2025)


def test_factor_match_accepts_optional_fields():
    model = FactorMatchIn(
        activity="Natural gas",
        country="GB",
        reporting_year=2025,
        unit="kWh",
        scope="Scope 1",
        organization_id="org-a",
        preferred_provider="defra",
        max_stages=3,
    )
    assert model.unit == "kWh"
    assert model.max_stages == 3


def test_factor_match_forbids_unknown_fields():
    with pytest.raises(ValidationError):
        FactorMatchIn(activity="Gas", country="GB", reporting_year=2025, hack="x")


def test_calculation_requires_numeric_quantity():
    with pytest.raises(ValidationError):
        CalculationIn(
            organization_id="org-a",
            factor_id="f1",
            quantity="not-a-number",
            quantity_unit="kWh",
            date="2025-06-01",
            reporting_year=2025,
            activity="Gas",
            activity_type="Natural gas",
        )


def test_validation_period_requires_both_dates():
    with pytest.raises(ValidationError):
        ValidationIn(organization_id="org-a", reporting_year=2025, start_date="2025-01-01")


def test_benchmark_compare_year_range():
    with pytest.raises(ValidationError):
        BenchmarkIn(organization_id="org-a", reporting_year=2025, compare_years=[1800])


def test_alias_create_requires_target_fields():
    with pytest.raises(ValidationError):
        FactorAliasCreate(alias_text="NG")  # missing targets


def test_alias_update_requires_at_least_one_field():
    with pytest.raises(ValidationError):
        FactorAliasUpdate()


def test_report_request_requires_type_and_year():
    with pytest.raises(ValidationError):
        ReportRequestIn(organization_id="org-a", reporting_year=2025)


# ---------------------------------------------------------------------------
# CO2/CO2e provenance preservation (contracts serialization)
# ---------------------------------------------------------------------------


def test_factor_out_preserves_defra_co2e():
    out = factor_out(seed_defra_factor())
    assert out.gas_coverage == "CO2e"
    assert out.provider_key == "defra"
    assert out.country == "GB"


def test_factor_out_preserves_seai_co2_only():
    """SEAI factors are CO2-only and must never be relabelled as CO2e."""
    out = factor_out(seed_seai_factor())
    assert out.gas_coverage == "CO2"
    assert out.provider_key == "seai"
    assert out.country == "IE"


def test_decimal_multiplier_serialised_as_string():
    out = factor_out(seed_defra_factor())
    assert out.co2e_multiplier == "0.183"
    assert isinstance(out.co2e_multiplier, str)


# ---------------------------------------------------------------------------
# Response serialization through the live API
# ---------------------------------------------------------------------------


def test_match_response_preserves_provenance(client):
    response = client.post(
        "/api/v2/factor-match",
        json={"activity": "Natural gas", "country": "GB", "reporting_year": 2025},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "matched"
    assert body["factor"]["gas_coverage"] == "CO2e"
    assert body["factor"]["co2e_multiplier"] == "0.183"


def test_seai_match_is_co2_not_co2e(client):
    response = client.post(
        "/api/v2/factor-match",
        json={"activity": "Natural gas", "country": "IE", "reporting_year": 2025},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["factor"]["gas_coverage"] == "CO2"
    assert body["factor"]["provider_key"] == "seai"


def test_calculate_response_serialization(client):
    response = client.post(
        "/api/v2/calculate",
        json={
            "organization_id": "org-a",
            "factor_id": "factor-defra-gas",
            "quantity": "1000",
            "quantity_unit": "kWh",
            "date": "2025-06-01",
            "reporting_year": 2025,
            "activity": "Natural gas consumption",
            "activity_type": "Natural gas",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["co2e_kg"] == "183.000000"
    assert body["co2e_tonnes"] == "0.183000"
    assert body["gas_coverage"] == "CO2e"
    assert body["snapshot"]["content_hash"]
    assert body["factor"]["id"] == "factor-defra-gas"
