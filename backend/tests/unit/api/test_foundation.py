"""Phase 10.4 — API foundation contract tests.

Covers: router registration, middleware (correlation ID, timing, structured
context), authentication handling, authorization handling, and the consistent
error mapping (CarbonTallyError, HTTPException, pydantic 422, generic 500).
"""
from __future__ import annotations

import pytest

def test_notification_domain_matches_real_schema(client):
    """D25 regression guard — the notifications repository was broken against
    the real ``notifications`` schema (referenced a non-existent ``user_id``
    column). The domain model must expose the schema's per-recipient shape."""
    from domain.operations import Notification
    import dataclasses

    fields = {f.name for f in dataclasses.fields(Notification)}
    assert "recipient_type" in fields
    assert "recipient_id" in fields
    assert "user_id" not in fields
    n = Notification(id="n1", recipient_id="user-1")
    assert n.recipient_type == "user"
    assert n.recipient_id == "user-1"


from tests.unit.api.fakes import member_user
from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATHS = {
    "/api/v2/health",
    "/api/v2/factor-match",
    "/api/v2/calculate",
    "/api/v2/validate",
    "/api/v2/benchmark",
    "/api/v2/generate-report",
    "/api/v2/admin/imports",
    "/api/v2/admin/imports/active",
    "/api/v2/admin/imports/{batch_id}",
    "/api/v2/admin/providers",
    "/api/v2/admin/providers/{key}",
    "/api/v2/admin/audit",
    "/api/v2/admin/audit/export",
    "/api/v2/admin/audit/correlation/{correlation_id}",
    "/api/v2/admin/audit/{entry_id}",
    "/api/v2/admin/aliases",
    "/api/v2/admin/aliases/{alias_id}",
}


def test_router_registration(app):
    """The single router exposes the full Phase 10 surface, no double prefix."""
    paths = flatten_router_paths(app)
    missing = EXPECTED_PATHS - paths
    assert not missing, f"missing routes: {sorted(missing)}"
    assert not any("/api/v2/api/v2" in p for p in paths), "double prefix detected"


def test_health_endpoint(client):
    response = client.get("/api/v2/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "carbontally-api-v2"


def test_correlation_id_generated_and_echoed(client):
    response = client.get("/api/v2/health")
    request_id = response.headers.get("X-Request-ID")
    assert request_id
    assert response.headers.get("X-Correlation-ID") == request_id
    assert response.json()["request_id"] == request_id


def test_correlation_id_respects_incoming_header(client):
    response = client.get("/api/v2/health", headers={"X-Request-ID": "trace-42"})
    assert response.headers.get("X-Request-ID") == "trace-42"
    assert response.json()["request_id"] == "trace-42"


def test_response_time_header_present(client):
    response = client.get("/api/v2/health")
    assert "X-Response-Time-Ms" in response.headers


def test_unknown_path_uses_error_envelope(client):
    response = client.get("/api/v2/definitely-not-a-route")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["request_id"]


def test_unauthenticated_user_rejected(client, user_provider):
    user_provider.set_unauthenticated()
    response = client.post(
        "/api/v2/factor-match",
        json={"activity": "Natural gas", "country": "GB", "reporting_year": 2025},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_ordinary_member_cannot_access_admin(client, user_provider):
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v2/admin/imports", params={"provider": "defra"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_can_access_admin(client, user_provider):
    response = client.get("/api/v2/admin/imports", params={"provider": "defra"})
    assert response.status_code == 200
    assert response.json()["provider"] == "defra"


def test_carbon_tally_error_maps_to_declared_status(client):
    """Unknown factor -> FactorNotFoundError -> 404 FACTOR_NOT_FOUND."""
    response = client.post(
        "/api/v2/calculate",
        json={
            "organization_id": "org-a",
            "factor_id": "missing-factor",
            "quantity": "100",
            "quantity_unit": "kWh",
            "date": "2025-06-01",
            "reporting_year": 2025,
            "activity": "Gas",
            "activity_type": "Natural gas",
        },
    )
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "FACTOR_NOT_FOUND"
    assert body["request_id"]


def test_pydantic_validation_maps_to_422(client):
    response = client.post(
        "/api/v2/factor-match",
        json={"country": "GB", "reporting_year": 2025},  # missing activity
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "errors" in body["error"]["details"]


def test_unhandled_error_never_leaks_internals(app):
    """A generic exception becomes a 500 envelope — no stack traces or secrets.

    FastAPI routes the ``Exception`` handler to Starlette's
    ``ServerErrorMiddleware``, which deliberately re-raises after sending the
    response (so servers can log it). The TestClient must therefore not re-raise
    server exceptions for this assertion.
    """
    from starlette.testclient import TestClient

    from api.dependencies import get_current_user

    async def _boom():
        raise RuntimeError("secret-db-password in stack")

    app.dependency_overrides[get_current_user] = _boom
    with TestClient(app, raise_server_exceptions=False) as quiet_client:
        response = quiet_client.post(
            "/api/v2/factor-match",
            json={"activity": "Natural gas", "country": "GB", "reporting_year": 2025},
        )
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["message"] == "Internal server error"
    assert "secret-db-password" not in response.text
