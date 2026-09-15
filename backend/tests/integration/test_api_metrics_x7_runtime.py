"""Phase 8-X X7 — API runtime metrics runtime tests (real PostgreSQL, disposable).

Authority: PO decisions `X7-D1`…`X7-D7` (prompt `CT-P8X-X7-GATE-02`). Verifies the
persistence contract against the **existing** metric store:

* `X7-D1` the series survives a process restart (a new service instance reads the
  previously persisted slots back);
* `X7-D3` exactly **one row** holds the series, and a second instrumented process
  merges into it rather than creating a per-worker row;
* `X7-D5` the rolling 60-minute window is honoured; older slots are dropped on write;
* X2's retention method is untouched and still governs this store.

**F-046-1 discipline:** destructive `TRUNCATE` setup means this runs only against a
disposable clone (`ct_*`) or the dedicated test DB — never QA/demo/production.
Rows created here are removed in `finally` blocks.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import asyncpg
import pytest

from data.api_metrics import ApiMetricsRepository
from data.document_processing import DocumentProcessingRepository
from domain.api_metrics import SERIES_METRIC_NAME, SERIES_METRIC_TYPE, slot_key
from services.api_metrics import ApiMetricsService

pytestmark = pytest.mark.asyncio

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


async def _clear(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM public.dashboard_metrics WHERE metric_type = $1 AND metric_name = $2",
            SERIES_METRIC_TYPE,
            SERIES_METRIC_NAME,
        )


async def test_flush_persists_one_row_and_survives_a_restart(pool: asyncpg.Pool) -> None:
    await _clear(pool)
    try:
        first = ApiMetricsService(ApiMetricsRepository(pool), clock=lambda: NOW)
        first.record(route="/api/v3/x", method="GET", status_code=200, duration_ms=120)
        first.record(route="/api/v3/x", method="GET", status_code=500, duration_ms=1500)
        await first.flush()

        assert await ApiMetricsRepository(pool).count_series_rows() == 1

        # A new process (fresh service, empty buffer) reads the persisted window.
        restarted = ApiMetricsService(ApiMetricsRepository(pool), clock=lambda: NOW)
        held = await restarted.read()

        assert held["series_present"] is True
        assert held["request_volume"] == 2
        assert held["status_distribution"]["5xx"] == 1
        assert held["slow_requests"] == 1
        assert held["error_requests"] == 1
        assert held["routes"]["/api/v3/x"]["requests"] == 2
        assert held["persisted_at"] is not None
    finally:
        await _clear(pool)


async def test_two_processes_merge_into_the_same_single_row(pool: asyncpg.Pool) -> None:
    """X7-D3 — a second instrumented process must not create a second row."""
    await _clear(pool)
    try:
        repo = ApiMetricsRepository(pool)
        a = ApiMetricsService(repo, clock=lambda: NOW)
        b = ApiMetricsService(repo, clock=lambda: NOW)

        a.record(route="/api/v3/y", method="GET", status_code=200, duration_ms=100)
        await a.flush()
        b.record(route="/api/v3/y", method="GET", status_code=200, duration_ms=100)
        await b.flush()

        assert await repo.count_series_rows() == 1
        held = await ApiMetricsService(repo, clock=lambda: NOW).read()
        assert held["request_volume"] == 2          # merged, not overwritten
        assert held["series"]["scope"] == "application_merged"
    finally:
        await _clear(pool)


async def test_rolling_window_excludes_and_prunes_old_slots(pool: asyncpg.Pool) -> None:
    """X7-D5 — only the last 60 minutes counts; older slots are dropped on write."""
    await _clear(pool)
    try:
        repo = ApiMetricsRepository(pool)
        service = ApiMetricsService(repo, clock=lambda: NOW)

        inside = NOW - timedelta(minutes=20)
        outside = NOW - timedelta(minutes=90)
        service.record(
            route="/api/v3/z", method="GET", status_code=200, duration_ms=100, now=inside
        )
        service.record(
            route="/api/v3/z", method="GET", status_code=200, duration_ms=100, now=outside
        )
        await service.flush()

        held = await ApiMetricsService(repo, clock=lambda: NOW).read()
        assert held["request_volume"] == 1        # the 90-minute-old slot is not counted

        persisted = await repo.read_series()
        assert slot_key(outside) not in (persisted or {}).get("slots", {})
        assert slot_key(inside) in (persisted or {}).get("slots", {})
    finally:
        await _clear(pool)


async def test_x2_retention_method_governs_the_store_unchanged(
    pool: asyncpg.Pool,
) -> None:
    """X7 adds no retention policy: X2's prune method still governs this store."""
    await _clear(pool)
    try:
        repo = ApiMetricsRepository(pool)
        service = ApiMetricsService(repo, clock=lambda: NOW)
        service.record(route="/api/v3/x", method="GET", status_code=200, duration_ms=90)
        await service.flush()

        processing = DocumentProcessingRepository(pool)
        preview = await processing.prune_operational_metrics_before(
            NOW + timedelta(days=1), dry_run=True
        )
        assert int(preview.get("eligible_metrics") or 0) >= 1   # inside X2's scope

        # Pruning as of a past cutoff must not remove the live row.
        result = await processing.prune_operational_metrics_before(
            NOW - timedelta(days=1), dry_run=False
        )
        assert int(result.get("deleted_metrics") or result.get("deleted") or 0) == 0
        assert await repo.count_series_rows() == 1
    finally:
        await _clear(pool)


async def test_heartbeat_and_x7_series_coexist_in_the_same_store(
    pool: asyncpg.Pool,
) -> None:
    """X1's heartbeat and X7's series are distinct identities in one store."""
    from domain.operational_health import HEARTBEAT_METRIC_NAME, HEARTBEAT_METRIC_TYPE

    async def _clear_hb() -> None:
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM public.dashboard_metrics "
                "WHERE metric_type = $1 AND metric_name = $2",
                HEARTBEAT_METRIC_TYPE,
                HEARTBEAT_METRIC_NAME,
            )

    await _clear(pool)
    await _clear_hb()
    try:
        repo = ApiMetricsRepository(pool)
        service = ApiMetricsService(repo, clock=lambda: NOW)
        service.record(route="/api/v3/x", method="GET", status_code=200, duration_ms=90)
        await service.flush()

        await DocumentProcessingRepository(pool).record_worker_heartbeat(
            worker_id="x7-test-worker"
        )

        assert await repo.count_series_rows() == 1
        heartbeat = await DocumentProcessingRepository(pool).latest_worker_heartbeat()
        assert heartbeat is not None and heartbeat["worker_id"] == "x7-test-worker"
    finally:
        await _clear(pool)
        await _clear_hb()

