"""Phase 10.4 — business-processing endpoint contract tests.

Covers the CT-ARCH-012 processing surface (factor-match, calculate, validate,
benchmark, generate-report): delegation to the real engines, organisation
isolation, error mapping, and CO2/CO2e provenance.
"""
from __future__ import annotations

from datetime import date

import pytest

from tests.unit.api.fakes import member_user, seed_log

CALCULATE_PAYLOAD = {
    "organization_id": "org-a",
    "factor_id": "factor-defra-gas",
    "quantity": "1000",
    "quantity_unit": "kWh",
    "date": "2025-06-01",
    "reporting_year": 2025,
    "activity": "Natural gas consumption",
    "activity_type": "Natural gas",
}


# ===========================================================================
# factor-match
# ===========================================================================


def test_factor_match_matched(client):
    response = client.post(
        "/api/v2/factor-match",
        json={"activity": "Natural gas", "country": "GB", "reporting_year": 2025},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "matched"
    assert body["factor"]["provider_key"] == "defra"
    assert body["factor"]["gas_coverage"] == "CO2e"
    assert body["methodology"]
    assert body["stages_executed"]


def test_factor_match_no_match(client):
    response = client.post(
        "/api/v2/factor-match",
        json={"activity": "totally unknown activity xyzzy", "country": "GB", "reporting_year": 2025},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "no_match"


def test_factor_match_through_alias(client):
    response = client.post(
        "/api/v2/factor-match",
        json={"activity": "NG", "country": "GB", "reporting_year": 2025, "organization_id": "org-a"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "matched"
    assert body["methodology"] == "alias_match"
    assert body["factor"]["gas_coverage"] == "CO2e"


def test_factor_match_org_isolation(client, user_provider):
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v2/factor-match",
        json={
            "activity": "Natural gas",
            "country": "GB",
            "reporting_year": 2025,
            "organization_id": "org-b",
        },
    )
    assert response.status_code == 403


def test_factor_match_requires_auth(client, user_provider):
    user_provider.set_unauthenticated()
    response = client.post(
        "/api/v2/factor-match",
        json={"activity": "Natural gas", "country": "GB", "reporting_year": 2025},
    )
    assert response.status_code == 401


# ===========================================================================
# calculate
# ===========================================================================


def test_calculate_defra_co2e(client):
    response = client.post("/api/v2/calculate", json=CALCULATE_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["co2e_kg"] == "183.000000"
    assert body["co2e_tonnes"] == "0.183000"
    assert body["gas_coverage"] == "CO2e"
    assert body["snapshot"]["content_hash"]


def test_calculate_seai_co2_only(client):
    payload = {
        **CALCULATE_PAYLOAD,
        "factor_id": "factor-seai-gas",
        "quantity": "100",
    }
    response = client.post("/api/v2/calculate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["co2e_kg"] == "20.500000"  # 100 * 0.205
    assert body["gas_coverage"] == "CO2"  # SEAI is CO2-only — never relabelled


def test_calculate_factor_not_found(client):
    response = client.post(
        "/api/v2/calculate",
        json={**CALCULATE_PAYLOAD, "factor_id": "missing-factor"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FACTOR_NOT_FOUND"


def test_calculate_unit_mismatch(client):
    response = client.post(
        "/api/v2/calculate",
        json={**CALCULATE_PAYLOAD, "quantity_unit": "litres"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UNIT_MISMATCH"


def test_calculate_org_isolation(client, user_provider):
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v2/calculate",
        json={**CALCULATE_PAYLOAD, "organization_id": "org-b"},
    )
    assert response.status_code == 403


# ===========================================================================
# validate
# ===========================================================================


def test_validate_clean_org_strict(client):
    response = client.post(
        "/api/v2/validate",
        json={
            "organization_id": "org-a",
            "reporting_year": 2025,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "strict": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["counts"]["error"] == 0


def test_validate_strict_blocks_on_errors(client, world):
    # org-b owns a log referencing a factor that does not exist -> blocking.
    world.logs._logs.append(
        seed_log(
            log_id="log-b1",
            org_id="org-b",
            factor_id="missing-factor",
            quantity="10",
            unit="kWh",
            scope="Scope 1",
            day=date(2025, 5, 1),
            calculated="1.000000",
        )
    )
    response = client.post(
        "/api/v2/validate",
        json={
            "organization_id": "org-b",
            "reporting_year": 2025,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "strict": True,
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_FAILED"


def test_validate_non_strict_returns_failing_report(client, world):
    world.logs._logs.append(
        seed_log(
            log_id="log-b1",
            org_id="org-b",
            factor_id="missing-factor",
            quantity="10",
            unit="kWh",
            scope="Scope 1",
            day=date(2025, 5, 1),
            calculated="1.000000",
        )
    )
    response = client.post(
        "/api/v2/validate",
        json={
            "organization_id": "org-b",
            "reporting_year": 2025,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "strict": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    codes = {issue["code"] for issue in body["issues"]}
    assert "VAL_FACTOR_ORPHAN" in codes


def test_validate_org_isolation(client, user_provider):
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v2/validate",
        json={"organization_id": "org-b", "reporting_year": 2025},
    )
    assert response.status_code == 403


# ===========================================================================
# benchmark
# ===========================================================================


def test_benchmark_available(client):
    response = client.post(
        "/api/v2/benchmark",
        json={"organization_id": "org-a", "reporting_year": 2025},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["organization_id"] == "org-a"
    by_key = {m["key"]: m for m in body["metrics"]}
    assert by_key["total"]["status"] == "available"
    assert by_key["total"]["value"] == "183.000000"
    assert "per_fte" in by_key


def test_benchmark_insufficient_data(client):
    response = client.post(
        "/api/v2/benchmark",
        json={"organization_id": "org-b", "reporting_year": 2025},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "BENCHMARK_DATA_INSUFFICIENT"


def test_benchmark_org_isolation(client, user_provider):
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v2/benchmark",
        json={"organization_id": "org-b", "reporting_year": 2025},
    )
    assert response.status_code == 403


# ===========================================================================
# generate-report
# ===========================================================================

REPORT_SECTION_IDS = {
    "metadata",
    "organization",
    "period",
    "totals",
    "scopes",
    "activities",
    "validation",
    "benchmarking",
    "provenance",
    "calculation",
    "lineage",
    "generation",
}


def test_generate_report_structured(client):
    response = client.post(
        "/api/v2/generate-report",
        json={
            "organization_id": "org-a",
            "report_type": "annual",
            "reporting_year": 2025,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["organization_id"] == "org-a"
    assert body["report_type"] == "annual"
    assert set(body["content"].keys()) == REPORT_SECTION_IDS
    # Provenance section preserves the CO2/CO2e mix.
    provenance = body["content"]["provenance"]
    assert "CO2e" in str(provenance)
    assert body["content"]["totals"]["total_co2e_kg"] == "183.000000"


def test_generate_report_org_isolation(client, user_provider):
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v2/generate-report",
        json={"organization_id": "org-b", "report_type": "annual", "reporting_year": 2025},
    )
    assert response.status_code == 403



