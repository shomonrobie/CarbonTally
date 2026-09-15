"""Phase 8-X X4 — endpoint authorization and payload tests.

Authority: PO-approved X4 contract (X4-D5 = ONE read-only operator aggregation
endpoint) and the internal-only authority chain X1 already uses
(``require_staff`` → ``require_internal_staff`` → ``can_view_all``).

Both directions are asserted: ALLOW for internal staff and DENY for non-staff,
customer members, PE/entity staff and unauthenticated callers. The repository
bundle is replaced with a deterministic stub (the endpoint's real SQL lives in
``data/document_processing.py`` and is unchanged by X4).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from api.dependencies import get_repositories
from api.operations_auth import StaffContext, require_staff
from domain.staff import StaffProfile
from tests.unit.api.fakes import member_user

URL = "/api/v3/ops/operational-intelligence"
NOW = datetime.now(timezone.utc)


# --- deterministic repository stub (no database) -----------------------------


class _StubProcessing:
    def __init__(self, rows, *, breached: int = 0, heartbeat=None) -> None:
        self._rows = rows
        self._breached = breached
        self._heartbeat = heartbeat

    async def queue_visibility_rows(self, *, limit: int = 2000):
        return self._rows

    async def count_sla_breached(self) -> int:
        return self._breached

    async def latest_worker_heartbeat(self):
        return self._heartbeat


class _StubQueueSettings:
    def __init__(self, *, configured: bool, sla_hours: int = 48) -> None:
        self._configured = configured
        self._sla_hours = sla_hours

    async def is_configured(self) -> bool:
        return self._configured

    async def get_settings(self):
        from types import SimpleNamespace

        return SimpleNamespace(sla_hours=self._sla_hours)


class _StubBundle:
    def __init__(self, *, configured: bool = True, rows=None, breached: int = 0) -> None:
        self.processing = _StubProcessing(
            rows if rows is not None else [_row("failed"), _row("blocked")],
            breached=breached,
            # Timestamped at construction (i.e. per request) so the liveness
            # assertion can never flake on a slow suite: a module-level "now"
            # would age past the 300s stale window during a long run.
            heartbeat={
                "tick_at": datetime.now(timezone.utc).isoformat(),
                "worker_id": "w1",
            },
        )
        self.queue_settings = _StubQueueSettings(configured=configured)


def _row(stage: str, **over) -> dict:
    base = {
        "id": "job",
        "organization_id": "org-secret",
        "stage": stage,
        "status": "processing",
        "attempt_count": 0,
        "max_attempts": 3,
        "workflow_error_count": 0,
        "workflow_next_retry_at": None,
        "last_error": None,
        "locked_at": None,
        "lock_token": None,
        "created_at": NOW,
        "ingested_at": NOW,
    }
    base.update(over)
    return base


def _profile(*, entity_id=None, role_id="role-1") -> StaffProfile:
    return StaffProfile(
        id="profile-1",
        user_id="staff-1",
        first_name="Ops",
        last_name="Operator",
        email="ops@carbontally.test",
        role_id=role_id,
        is_active=True,
        entity_id=entity_id,
    )


def _staff_context(*, can_view_all: bool, entity_id=None):
    """Override only the staff-context dependency; the endpoint's own checks stay."""
    context = StaffContext(
        profile=_profile(entity_id=entity_id),
        permissions={"can_view_all": can_view_all},
    )

    async def _override():
        return context

    return _override


# --- ALLOW -------------------------------------------------------------------


def test_internal_staff_with_can_view_all_is_allowed(app, client, world) -> None:
    app.dependency_overrides[get_repositories] = lambda: _StubBundle(
        configured=True, breached=2
    )
    app.dependency_overrides[require_staff] = _staff_context(can_view_all=True)

    response = client.get(URL)

    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "internal"
    assert body["x4_scope"] == "failures_and_sla"
    assert body["failed_jobs"] == 1
    assert body["blocked_jobs"] == 1
    assert body["sla_state"] == "configured"
    assert body["sla_hours"] == 48
    assert body["sla_breached_items"] == 2
    assert body["worker_liveness"]["state"] == "HEALTHY"
    assert body["truncated"] is False
    for key in (
        "retry_exhausted_jobs",
        "stuck_locked_jobs",
        "manual_review_jobs",
        "error_rate_by_stage",
        "queue_depth_by_stage",
        "open_vs_closed",
        "evaluated_at",
    ):
        assert key in body


def test_sla_not_configured_is_reported_without_a_breach(app, client, world) -> None:
    app.dependency_overrides[get_repositories] = lambda: _StubBundle(configured=False)
    app.dependency_overrides[require_staff] = _staff_context(can_view_all=True)

    body = client.get(URL).json()

    assert body["sla_state"] == "not_configured"
    assert body["sla_breached_items"] is None
    assert body["sla_hours"] is None


def test_truncated_is_visible_at_the_read_bound(app, client, world) -> None:
    app.dependency_overrides[get_repositories] = lambda: _StubBundle(
        rows=[_row("failed") for _ in range(2000)]
    )
    app.dependency_overrides[require_staff] = _staff_context(can_view_all=True)

    body = client.get(URL).json()

    assert body["truncated"] is True
    assert body["read_limit"] == 2000


def test_response_is_redacted_and_has_no_tenant_breakdown(app, client, world) -> None:
    app.dependency_overrides[get_repositories] = lambda: _StubBundle(
        rows=[
            _row(
                "failed",
                last_error="OCR failed; escalation sent to billing@customer.example.com",
                workflow_error_count=1,
            )
        ]
    )
    app.dependency_overrides[require_staff] = _staff_context(can_view_all=True)

    text = client.get(URL).text

    assert "billing@customer.example.com" not in text
    assert "last_error" not in text
    assert "OCR failed" not in text
    assert "file_url" not in text
    assert "org-secret" not in text
    assert "organization" not in text.lower()


def test_no_trend_or_window_keys_in_the_transport_payload(app, client, world) -> None:
    app.dependency_overrides[get_repositories] = lambda: _StubBundle()
    app.dependency_overrides[require_staff] = _staff_context(can_view_all=True)

    body = client.get(URL).json()

    for forbidden in ("trend", "window", "last_24h", "last_7d", "percent"):
        assert forbidden not in " ".join(body).lower()


# --- DENY --------------------------------------------------------------------


def test_internal_staff_without_can_view_all_is_denied(app, client, world) -> None:
    app.dependency_overrides[get_repositories] = lambda: _StubBundle()
    app.dependency_overrides[require_staff] = _staff_context(can_view_all=False)

    assert client.get(URL).status_code == 403


def test_processing_entity_staff_is_denied(app, client, world) -> None:
    app.dependency_overrides[get_repositories] = lambda: _StubBundle()
    app.dependency_overrides[require_staff] = _staff_context(
        can_view_all=True, entity_id="entity-1"
    )

    assert client.get(URL).status_code == 403


def test_non_staff_customer_member_is_denied(client, user_provider, world) -> None:
    """No staff profile → the real `require_staff` dependency refuses."""
    user_provider.set_user(member_user("org-a", "member-a", "member.a@test"))

    assert client.get(URL).status_code == 403


def test_unauthenticated_caller_is_denied(client, user_provider, world) -> None:
    user_provider.set_unauthenticated()

    assert client.get(URL).status_code == 401


# --- X4-D5: exactly one read-only aggregation endpoint -----------------------


def test_x4_exposes_one_read_route_and_no_mutation_route() -> None:
    """X4-D5 — one read-only endpoint; no POST/PUT/DELETE surface was added."""
    from api.v3_operations import router
    from tests.unit.api.route_paths import flatten_router_paths

    paths = flatten_router_paths(router)
    assert "/api/v3/ops/operational-intelligence" in paths

    # No write verb exists on the X4 path in any form.
    write_routes = [
        route
        for route in router.routes
        if getattr(route, "path", "").endswith("/operational-intelligence")
        and "GET" not in getattr(route, "methods", set())
    ]
    assert write_routes == []
    # X1's endpoints are untouched.
    assert "/api/v3/ops/operational-health/queue" in paths
    assert "/api/v3/ops/operational-health/worker" in paths


