"""Phase 8-X X7 — API runtime metrics read endpoint: authorization + privacy.

Authority: PO decisions `X7-D1`…`X7-D7` (prompt `CT-P8X-X7-GATE-02`).

The endpoint's data layer is stubbed and `get_pool` is patched, so these tests
touch **no database** (the development database is never opened).
"""
from __future__ import annotations

from api.operations_auth import StaffContext, require_staff
from domain.api_metrics import SERIES_METRIC_NAME, SERIES_METRIC_TYPE
from domain.staff import StaffProfile
from tests.unit.api.fakes import member_user

URL = "/api/v3/ops/api-runtime-metrics"

AGGREGATE = {
    "series": {
        "metric_type": SERIES_METRIC_TYPE,
        "metric_name": SERIES_METRIC_NAME,
        "scope": "application_merged",
        "version": 1,
    },
    "window_seconds": 3600,
    "slots_in_window": 3,
    "request_volume": 42,
    "status_distribution": {"2xx": 40, "3xx": 0, "4xx": 1, "5xx": 1},
    "p95_latency_ms": 500,
    "p95_latency_ms_resolution": "bucket_upper_bound",
    "slow_threshold_ms": 1000,
    "slow_requests": 2,
    "error_requests": 2,
    "slow_routes": {"/api/v3/reports/{report_id}": 2},
    "error_routes": {"/api/v3/ops/dashboard": 2},
    "routes": {"/api/v3/reports/{report_id}": {"requests": 42}},
    "series_present": True,
    "persisted_at": "2026-09-15T12:00:00+00:00",
    "pending_local_slots": 0,
}


class _StubRepo:
    def __init__(self, pool=None) -> None:
        self._pool = pool

    async def read_series(self):
        return None

    async def merge_slots(self, slots, *, now=None):
        return slots


async def _stub_get_pool():
    return None


def _staff(*, can_view_all: bool, entity_id=None):
    context = StaffContext(
        profile=StaffProfile(
            id="p1",
            user_id="staff-1",
            first_name="Ops",
            last_name="One",
            email="ops@carbontally.test",
            role_id="role-1",
            is_active=True,
            entity_id=entity_id,
        ),
        permissions={"can_view_all": can_view_all},
    )

    async def _override():
        return context

    return _override


def _patch(monkeypatch, *, payload=None):
    import api.v3_operations as ops

    monkeypatch.setattr(ops, "get_pool", _stub_get_pool)
    monkeypatch.setattr(ops, "ApiMetricsRepository", _StubRepo)
    if payload is not None:
        from services.api_metrics import ApiMetricsService

        class _Svc(ApiMetricsService):
            async def read(self, *, now=None):
                return dict(payload)

        monkeypatch.setattr(ops, "ApiMetricsService", _Svc)


def test_internal_staff_with_can_view_all_is_allowed(app, client, monkeypatch) -> None:
    _patch(monkeypatch, payload=AGGREGATE)
    app.dependency_overrides[require_staff] = _staff(can_view_all=True)

    response = client.get(URL)

    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "internal"
    assert body["x7_scope"] == "api_runtime_metrics"
    assert body["request_volume"] == 42
    assert body["status_distribution"]["5xx"] == 1
    assert body["p95_latency_ms"] == 500
    assert body["slow_requests"] == 2
    assert body["error_requests"] == 2
    assert body["window_seconds"] == 3600
    assert body["slow_threshold_ms"] == 1000


def test_payload_carries_no_request_content_or_attribution(
    app, client, monkeypatch
) -> None:
    _patch(monkeypatch, payload=AGGREGATE)
    app.dependency_overrides[require_staff] = _staff(can_view_all=True)

    text = client.get(URL).text.lower()

    # Route templates are present; nothing that could carry PII is.
    for forbidden in (
        "token",
        "authorization",
        "query",
        "body",
        "email",
        "user_id",
        "organization",
        "tenant",
        "entity_",
        "ip",
    ):
        assert forbidden not in text
    assert "{report_id}" in text  # template identity, not a raw path


def test_staff_without_can_view_all_is_denied(app, client, monkeypatch) -> None:
    _patch(monkeypatch)
    app.dependency_overrides[require_staff] = _staff(can_view_all=False)

    assert client.get(URL).status_code == 403


def test_processing_entity_staff_is_denied(app, client, monkeypatch) -> None:
    _patch(monkeypatch)
    app.dependency_overrides[require_staff] = _staff(
        can_view_all=True, entity_id="entity-1"
    )

    assert client.get(URL).status_code == 403


def test_non_staff_customer_is_denied(client, user_provider, world) -> None:
    user_provider.set_user(member_user("org-a", "member-a", "member.a@test"))

    assert client.get(URL).status_code == 403


def test_unauthenticated_caller_is_denied(client, user_provider, world) -> None:
    user_provider.set_unauthenticated()

    assert client.get(URL).status_code == 401


def test_x7_exposes_one_read_only_route() -> None:
    from api.v3_operations import router
    from tests.unit.api.route_paths import flatten_router_paths

    paths = flatten_router_paths(router)
    assert "/api/v3/ops/api-runtime-metrics" in paths
    write_routes = [
        route
        for route in router.routes
        if getattr(route, "path", "").endswith("/api-runtime-metrics")
        and "GET" not in getattr(route, "methods", set())
    ]
    assert write_routes == []
