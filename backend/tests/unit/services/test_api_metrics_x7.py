"""Phase 8-X X7 — API runtime metrics tests (pure + service + persistence).

Authority: PO decisions `X7-D1`…`X7-D7` (prompt `CT-P8X-X7-GATE-02`).
Covers: route-template normalisation, the approved metrics, the rolling window,
the p95 bucket semantics, the 1,000 ms slow threshold, the 5-minute flush cadence,
the single-merged-series merge, and privacy (no raw path/query/body/token/PII).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from domain.api_metrics import (
    FLUSH_INTERVAL_SECONDS,
    SERIES_METRIC_NAME,
    SERIES_METRIC_TYPE,
    SLOW_THRESHOLD_MS,
    UNMATCHED_ROUTE,
    WINDOW_SECONDS,
    aggregate_slots,
    empty_slot,
    is_slow,
    prune_slots,
    record_sample,
    slot_key,
    status_class,
)
from services.api_metrics import ApiMetricsService

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


class _FakeRequest:
    def __init__(self, path: str, route_path: str | None = None) -> None:
        self.url = type("U", (), {"path": path})()
        self.method = "GET"
        self.scope = {"route": type("R", (), {"path": route_path})()} if route_path else {}


class _StubRepo:
    """In-memory stand-in for ApiMetricsRepository (no database)."""

    def __init__(self) -> None:
        self.slots: dict = {}
        self.merge_calls = 0

    async def merge_slots(self, slots, *, now=None):
        from data.api_metrics import _merge_slot_maps
        from domain.api_metrics import prune_slots as _prune

        self.merge_calls += 1
        _merge_slot_maps(self.slots, slots)
        _prune(self.slots, now=now or NOW)
        return self.slots

    async def read_series(self):
        return {"slots": self.slots, "persisted_at": NOW.isoformat()} if self.slots else None


def _service(repo=None) -> ApiMetricsService:
    return ApiMetricsService(repo or _StubRepo(), clock=lambda: NOW)


# ---------------------------------------------------------------------------
# X7-D4/D5/D6 — metric definitions
# ---------------------------------------------------------------------------


def test_status_class_covers_every_class_and_never_drops_a_status() -> None:
    assert status_class(200) == "2xx"
    assert status_class(301) == "3xx"
    assert status_class(404) == "4xx"
    assert status_class(500) == "5xx"
    assert status_class(0) == "5xx"  # unusual status is reported, never dropped


def test_slow_threshold_is_the_po_value_one_thousand_ms() -> None:
    assert SLOW_THRESHOLD_MS == 1000
    assert is_slow(999.9) is False
    assert is_slow(1000) is True          # >= 1000 ms
    assert is_slow(1500) is True


def test_window_and_flush_constants_match_the_po_decisions() -> None:
    assert WINDOW_SECONDS == 3600          # X7-D5 rolling 60 minutes
    assert FLUSH_INTERVAL_SECONDS == 300   # X7-D2 every 5 minutes


def test_slot_key_is_the_wall_clock_five_minute_slot() -> None:
    assert slot_key(datetime(2026, 9, 15, 12, 7, 42, tzinfo=timezone.utc)) == slot_key(
        datetime(2026, 9, 15, 12, 9, 59, tzinfo=timezone.utc)
    )
    assert slot_key(datetime(2026, 9, 15, 12, 9, tzinfo=timezone.utc)) != slot_key(
        datetime(2026, 9, 15, 12, 10, tzinfo=timezone.utc)
    )


# ---------------------------------------------------------------------------
# The approved metrics (no rate/denominator metric exists)
# ---------------------------------------------------------------------------


def _slot_with(*samples) -> dict:
    slot = empty_slot()
    for route, status, duration in samples:
        record_sample(slot, route=route, status_code=status, duration_ms=duration)
    return slot


def test_aggregate_reports_volume_status_distribution_and_thresholds() -> None:
    slots = {
        slot_key(NOW): _slot_with(
            ("/api/v3/reports/{report_id}", 200, 120),
            ("/api/v3/reports/{report_id}", 200, 1200),   # slow (>=1000)
            ("/api/v3/reports/{report_id}", 404, 30),     # error
            ("/api/v3/ops/dashboard", 500, 2500),         # error + slow
        )
    }
    out = aggregate_slots(slots, now=NOW)

    assert out["request_volume"] == 4
    assert out["status_distribution"] == {"2xx": 2, "3xx": 0, "4xx": 1, "5xx": 1}
    assert out["slow_requests"] == 2
    assert out["error_requests"] == 2
    assert out["slow_threshold_ms"] == 1000
    assert out["slow_routes"] == {
        "/api/v3/ops/dashboard": 1,
        "/api/v3/reports/{report_id}": 1,
    }
    assert out["error_routes"] == {
        "/api/v3/ops/dashboard": 1,
        "/api/v3/reports/{report_id}": 1,
    }
    # No denominator-dependent metric is emitted anywhere.
    for forbidden in ("rate", "percentage", "ratio"):
        assert forbidden not in " ".join(out).lower()


def test_p95_is_reported_as_a_bucket_upper_bound_not_an_exact_figure() -> None:
    # 19 requests around 120 ms and 1 at 900 ms: the 95th observation still sits
    # in the 250 ms bucket, so p95 reports that bucket's upper bound.
    samples = [("/api/v3/x", 200, 120)] * 19 + [("/api/v3/x", 200, 900)]
    out = aggregate_slots({slot_key(NOW): _slot_with(*samples)}, now=NOW)
    assert out["p95_latency_ms"] == 250
    assert out["p95_latency_ms_resolution"] == "bucket_upper_bound"


def test_p95_is_none_when_nothing_has_been_observed() -> None:
    out = aggregate_slots({}, now=NOW)
    assert out["p95_latency_ms"] is None
    assert out["request_volume"] == 0
    assert out["slots_in_window"] == 0


# ---------------------------------------------------------------------------
# X7-D5 — rolling 60-minute window
# ---------------------------------------------------------------------------


def test_slots_outside_the_rolling_window_are_excluded() -> None:
    inside = slot_key(NOW - timedelta(minutes=30))
    outside = slot_key(NOW - timedelta(minutes=90))
    slots = {
        inside: _slot_with(("/api/v3/x", 200, 100)),
        outside: _slot_with(("/api/v3/x", 200, 100)),
    }
    out = aggregate_slots(slots, now=NOW)

    assert out["request_volume"] == 1     # only the slot inside 60 minutes counts
    assert out["slots_in_window"] == 1


def test_prune_slots_drops_only_expired_slots() -> None:
    fresh = slot_key(NOW - timedelta(minutes=5))
    stale = slot_key(NOW - timedelta(minutes=61))
    slots = {fresh: empty_slot(), stale: empty_slot()}

    dropped = prune_slots(slots, now=NOW)

    assert dropped == {stale}
    assert fresh in slots and stale not in slots


# ---------------------------------------------------------------------------
# X7-D2/D3 — flush cadence, single merged series, privacy
# ---------------------------------------------------------------------------


def test_flush_is_due_at_first_observation_then_only_after_five_minutes() -> None:
    repo = _StubRepo()
    service = ApiMetricsService(repo, clock=lambda: NOW)

    assert service.flush_due() is True                 # never flushed yet
    asyncio.run(service.flush())
    assert service.flush_due() is False                # immediately after a flush
    assert service.flush_due(now=NOW + timedelta(seconds=299)) is False
    assert service.flush_due(now=NOW + timedelta(seconds=300)) is True


def test_only_instrumented_api_v3_paths_are_recorded() -> None:
    repo = _StubRepo()
    service = ApiMetricsService(repo, clock=lambda: NOW)

    asyncio.run(
        service.observe_request(
            _FakeRequest("/api/v3/reports/abc", "/api/v3/reports/{report_id}"),
            status_code=200,
            duration_ms=90,
        )
    )
    asyncio.run(
        service.observe_request(
            _FakeRequest("/health", None), status_code=200, duration_ms=90
        )
    )

    on_disk = repo.slots[slot_key(NOW)]["routes"]
    assert list(on_disk) == ["/api/v3/reports/{report_id}"]


def test_unmatched_requests_never_store_the_raw_path() -> None:
    repo = _StubRepo()
    service = ApiMetricsService(repo, clock=lambda: NOW)
    raw = "/api/v3/reports/3f2b8c1e-1111-4111-8111-111111111111?token=secret#x"

    asyncio.run(
        service.observe_request(
            _FakeRequest(raw, None), status_code=404, duration_ms=40
        )
    )

    serialised = repr(repo.slots)
    assert list(repo.slots[slot_key(NOW)]["routes"]) == [UNMATCHED_ROUTE]
    assert "3f2b8c1e" not in serialised   # no identifier
    assert "token" not in serialised      # no query string
    assert "secret" not in serialised


def test_two_processes_merge_into_one_series_and_one_row_set() -> None:
    """X7-D3 — concurrent flushes merge into a single series, not per-process rows."""
    shared = _StubRepo()
    first = ApiMetricsService(shared, clock=lambda: NOW)
    second = ApiMetricsService(shared, clock=lambda: NOW)

    first.record(route="/api/v3/x", method="GET", status_code=200, duration_ms=100)
    second.record(route="/api/v3/x", method="GET", status_code=500, duration_ms=1500)
    asyncio.run(first.flush())
    asyncio.run(second.flush())

    merged = shared.slots[slot_key(NOW)]["routes"]["/api/v3/x"]
    assert merged["requests"] == 2
    assert merged["slow"] == 1
    assert merged["errors"] == 1
    assert shared.merge_calls == 2                 # same series, merged in place

    out = aggregate_slots(shared.slots, now=NOW)
    assert out["request_volume"] == 2
    assert out["series"]["metric_type"] == SERIES_METRIC_TYPE
    assert out["series"]["metric_name"] == SERIES_METRIC_NAME
    assert out["series"]["scope"] == "application_merged"


def test_read_model_exposes_only_approved_aggregate_keys() -> None:
    repo = _StubRepo()
    service = ApiMetricsService(repo, clock=lambda: NOW)
    service.record(route="/api/v3/x", method="GET", status_code=200, duration_ms=100)
    asyncio.run(service.flush())

    out = asyncio.run(service.read(now=NOW))

    assert out["request_volume"] == 1
    assert out["series_present"] is True
    assert out["persisted_at"] == NOW.isoformat()
    # No raw telemetry record and no tenant/entity attribution is exposed.
    for forbidden in ("organization", "tenant", "entity", "user_id", "ip", "query"):
        assert forbidden not in " ".join(out).lower()


def test_record_and_flush_never_raise_on_a_broken_repository() -> None:
    class _Broken(_StubRepo):
        async def merge_slots(self, slots, *, now=None):
            raise RuntimeError("db down")

    service = ApiMetricsService(_Broken(), clock=lambda: NOW)
    service.record(route="/api/v3/x", method="GET", status_code=200, duration_ms=100)

    assert asyncio.run(service.flush()) == {}   # swallowed, logged, never raised


