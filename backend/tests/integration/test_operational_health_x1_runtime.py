"""Phase 8-X X1 — operational health integration tests (real database).

Exercises the two X1 deliverables against a **disposable clone** using the same
F-046-1 rule as every other integration suite in this repository: the session
fixture TRUNCATEs its target, so it must never point at a persistent environment.

Covered:
* M2 — the worker heartbeat is written into the existing ``dashboard_metrics``
  store, read back, classified, and kept to a **single** current row;
* M1 — the queue visibility read model reads real queued rows and classifies them.
"""
from __future__ import annotations

import asyncpg
import pytest

from data.document_processing import DocumentProcessingRepository
from domain.operational_health import (
    HEARTBEAT_HEALTHY,
    HEARTBEAT_METRIC_NAME,
    HEARTBEAT_METRIC_TYPE,
    HEARTBEAT_UNKNOWN,
    classify_worker_liveness,
    summarise_queue,
)

pytestmark = pytest.mark.asyncio


async def _clear_heartbeat(pool: asyncpg.Pool) -> None:
    """Remove only the heartbeat rows this suite manages."""
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM public.dashboard_metrics WHERE metric_type = $1 AND metric_name = $2",
            HEARTBEAT_METRIC_TYPE,
            HEARTBEAT_METRIC_NAME,
        )


# ---------------------------------------------------------------------------
# M2 — worker heartbeat (reuse of the existing dashboard_metrics store)
# ---------------------------------------------------------------------------


async def test_heartbeat_is_recorded_read_back_and_classified_healthy(
    pool: asyncpg.Pool,
) -> None:
    repo = DocumentProcessingRepository(pool)
    await _clear_heartbeat(pool)
    try:
        written = await repo.record_worker_heartbeat(worker_id="x1-test-worker")
        assert written, "the heartbeat write must return the stored row"

        latest = await repo.latest_worker_heartbeat()
        assert latest is not None
        assert latest["worker_id"] == "x1-test-worker"
        assert latest["tick_at"], "a tick timestamp must be persisted"

        liveness = classify_worker_liveness(latest["tick_at"])
        assert liveness["state"] == HEARTBEAT_HEALTHY
    finally:
        await _clear_heartbeat(pool)


async def test_heartbeat_keeps_exactly_one_current_row(pool: asyncpg.Pool) -> None:
    """The store must not grow per tick — X1 invents no retention policy."""
    repo = DocumentProcessingRepository(pool)
    await _clear_heartbeat(pool)
    try:
        for _ in range(4):
            await repo.record_worker_heartbeat(worker_id="x1-test-worker")

        async with pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT count(*) FROM public.dashboard_metrics "
                "WHERE metric_type = $1 AND metric_name = $2",
                HEARTBEAT_METRIC_TYPE,
                HEARTBEAT_METRIC_NAME,
            )
        assert count == 1
    finally:
        await _clear_heartbeat(pool)


async def test_no_heartbeat_reads_back_as_unknown_not_healthy(
    pool: asyncpg.Pool,
) -> None:
    """Honest absence: a worker that never ticked is UNKNOWN, never 'healthy'."""
    repo = DocumentProcessingRepository(pool)
    await _clear_heartbeat(pool)
    assert await repo.latest_worker_heartbeat() is None
    assert classify_worker_liveness(None)["state"] == HEARTBEAT_UNKNOWN


# ---------------------------------------------------------------------------
# M1 — queue visibility read model
# ---------------------------------------------------------------------------


async def test_queue_visibility_reads_the_real_queue_table(pool: asyncpg.Pool) -> None:
    repo = DocumentProcessingRepository(pool)
    rows = await repo.queue_visibility_rows(limit=50)
    assert isinstance(rows, list)

    # Every row must carry the fields the classification needs, and nothing more
    # customer-identifying than the organisation the work belongs to.
    expected = {
        "id", "organization_id", "stage", "status", "attempt_count", "max_attempts",
        "workflow_error_count", "workflow_next_retry_at", "last_error",
        "locked_at", "lock_token", "created_at", "ingested_at",
    }
    for row in rows:
        assert set(row) == expected

    summary = summarise_queue(rows)
    assert summary["total_jobs"] == len(rows)
    assert summary["open_jobs"] <= summary["total_jobs"]
    assert summary["stuck_claims"] <= summary["total_jobs"]


async def test_queue_visibility_is_aggregate_only(pool: asyncpg.Pool) -> None:
    """The API contract must be aggregate — no per-job customer detail leaks."""
    repo = DocumentProcessingRepository(pool)
    summary = summarise_queue(await repo.queue_visibility_rows(limit=50))
    assert set(summary) == {
        "total_jobs", "open_jobs", "stage_distribution", "stuck_claims",
        "retry_exhausted", "jobs_with_last_error", "workflow_error_count",
        "oldest_waiting_age_seconds", "stale_after_seconds",
    }
