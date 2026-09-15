"""Phase 8-X X4 — aggregation runtime tests (real PostgreSQL, disposable target).

Authority: the PO-approved X4 contract. Verification requirements covered here:

* **direct SQL cross-checks** — every aggregate figure is compared with an
  independently written SQL count over the same rows;
* the **redaction fixture** — a job whose ``last_error`` contains an e-mail address
  must not leak that text (or any error/filename/URL) into the payload;
* the **truncation** behaviour through the real read path;
* the configured / not-configured SLA cases against the real ``queue_settings`` row.

**F-046-1 discipline:** the ``pool`` fixture performs destructive setup
(``TRUNCATE … RESTART IDENTITY CASCADE``), so this suite is executed only against a
**disposable clone** (``ct_*``) or the dedicated test database, never QA, never the
investor demo, never production. Rows created here are removed in ``finally`` blocks.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import asyncpg
import pytest

from data.document_processing import DocumentProcessingRepository
from data.queue_settings import QueueSettingsRepository
from services.operational_intelligence import (
    QUEUE_READ_LIMIT,
    OperationalIntelligenceService,
    aggregate_queue_rows,
)
from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio

#: The single settings row ``QueueSettingsRepository`` manages.
SETTINGS_KEY = "review_sla_defaults"


class _Bundle:
    """The two **real** repositories X1/X2 already use (no fake SQL)."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self.processing = DocumentProcessingRepository(pool)
        self.queue_settings = QueueSettingsRepository(pool)


async def _insert_job(
    pool: asyncpg.Pool,
    org_id: str,
    *,
    stage: str,
    attempt_count: int = 0,
    max_attempts: int = 3,
    workflow_error_count: int = 0,
    lock_token: str | None = None,
    locked_at: datetime | None = None,
    last_error: str | None = None,
    status: str = "processing",
) -> str:
    """Insert one durable-job row using only pre-existing columns."""
    job_id = new_id()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO public.document_processing_queue
                (id, organization_id, processing_type, status, file_name, file_url,
                 stage, attempt_count, max_attempts, workflow_error_count,
                 lock_token, locked_at, last_error, created_at, ingested_at)
            VALUES ($1,$2,'document',$3,$4,$5,$6,$7,$8,$9,$10,$11,$12, NOW(), NOW())
            """,
            job_id,
            org_id,
            status,
            f"{job_id}.pdf",
            f"https://example.invalid/{job_id}.pdf",
            stage,
            attempt_count,
            max_attempts,
            workflow_error_count,
            lock_token,
            locked_at,
            last_error,
        )
    return job_id


async def _insert_processing_queue_row(
    pool: asyncpg.Pool, org_id: str, *, breached: bool
) -> str:
    """Insert a ``processing_queue`` row carrying the persisted breach flag."""
    row_id = new_id()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO public.processing_queue
                (id, document_id, organization_id, document_type, queue_status, sla_breached)
            VALUES ($1,$2,$3,'document',$4,$5)
            """,
            row_id,
            new_id(),
            org_id,
            "pending",
            breached,
        )
    return row_id


async def _cleanup(pool: asyncpg.Pool, *, job_ids=(), queue_ids=()) -> None:
    async with pool.acquire() as conn:
        if job_ids:
            await conn.execute(
                "DELETE FROM public.document_processing_queue WHERE id = ANY($1::uuid[])",
                list(job_ids),
            )
        if queue_ids:
            await conn.execute(
                "DELETE FROM public.processing_queue WHERE id = ANY($1::uuid[])",
                list(queue_ids),
            )


# ---------------------------------------------------------------------------
# Every aggregate cross-checked against direct SQL over the same rows
# ---------------------------------------------------------------------------


async def test_aggregates_cross_check_against_direct_sql(pool: asyncpg.Pool) -> None:
    org_id = await make_org(pool, "X4 Runtime Co")
    stale_lock = datetime.now(timezone.utc) - timedelta(hours=2)
    job_ids: list[str] = []
    queue_ids: list[str] = []
    settings_existed = False
    try:
        job_ids.append(await _insert_job(pool, org_id, stage="failed"))
        job_ids.append(await _insert_job(pool, org_id, stage="failed",
                                         last_error="OCR failed: notify billing@customer.example.com"))
        job_ids.append(await _insert_job(pool, org_id, stage="blocked"))
        job_ids.append(await _insert_job(pool, org_id, stage="manual_review"))
        job_ids.append(await _insert_job(pool, org_id, stage="extracting",
                                         attempt_count=3, max_attempts=3,
                                         workflow_error_count=2))
        job_ids.append(await _insert_job(pool, org_id, stage="extracting",
                                         lock_token=new_id(), locked_at=stale_lock))
        job_ids.append(await _insert_job(pool, org_id, stage="completed",
                                         status="completed"))
        queue_ids.append(await _insert_processing_queue_row(pool, org_id, breached=True))
        queue_ids.append(await _insert_processing_queue_row(pool, org_id, breached=True))
        queue_ids.append(await _insert_processing_queue_row(pool, org_id, breached=False))

        async with pool.acquire() as conn:
            settings_existed = bool(
                await conn.fetchval(
                    "SELECT 1 FROM public.queue_settings WHERE setting_key = $1", SETTINGS_KEY
                )
            )
            if not settings_existed:
                await conn.execute(
                    "INSERT INTO public.queue_settings (setting_key, setting_value) "
                    "VALUES ($1, $2::jsonb)",
                    SETTINGS_KEY,
                    '{"sla_hours": 48}',
                )

        service = OperationalIntelligenceService(_Bundle(pool))
        held = await service.summary()

        # --- independent SQL over exactly the rows this test created ---------
        async with pool.acquire() as conn:
            sql_failed = await conn.fetchval(
                "SELECT count(*) FROM public.document_processing_queue "
                "WHERE organization_id = $1 AND stage = 'failed'",
                org_id,
            )
            sql_exhausted = await conn.fetchval(
                "SELECT count(*) FROM public.document_processing_queue "
                "WHERE organization_id = $1 AND attempt_count >= max_attempts",
                org_id,
            )
            sql_blocked = await conn.fetchval(
                "SELECT count(*) FROM public.document_processing_queue "
                "WHERE organization_id = $1 AND stage = 'blocked'",
                org_id,
            )
            sql_manual = await conn.fetchval(
                "SELECT count(*) FROM public.document_processing_queue "
                "WHERE organization_id = $1 AND stage = 'manual_review'",
                org_id,
            )
            sql_stuck = await conn.fetchval(
                "SELECT count(*) FROM public.document_processing_queue "
                "WHERE organization_id = $1 AND lock_token IS NOT NULL "
                "AND locked_at <= NOW() - interval '300 seconds'",
                org_id,
            )
            sql_breached = await conn.fetchval(
                "SELECT count(*) FROM public.processing_queue WHERE sla_breached = true"
            )

        assert held["failed_jobs"] == sql_failed == 2
        assert held["retry_exhausted_jobs"] == sql_exhausted == 1
        assert held["blocked_jobs"] == sql_blocked == 1
        assert held["manual_review_jobs"] == sql_manual == 1
        assert held["stuck_locked_jobs"] == sql_stuck == 1
        assert held["sla_breached_items"] == sql_breached == 2

        # --- composition checks (real rows through the real X1 predicates) ---
        rows = await _Bundle(pool).processing.queue_visibility_rows(limit=QUEUE_READ_LIMIT)
        recomputed = aggregate_queue_rows(
            [r for r in rows if str(r["organization_id"]) == str(org_id)]
        )
        assert recomputed["failed_jobs"] == held["failed_jobs"]
        assert recomputed["retry_exhausted_jobs"] == held["retry_exhausted_jobs"]
        assert recomputed["queue_depth_by_stage"]["failed"] == 2
        assert held["error_rate_by_stage"].get("extracting") == 1
        assert held["open_vs_closed"]["closed"] >= 1
        assert held["sla_state"] == "configured"
        assert held["sla_hours"] == 48
    finally:
        await _cleanup(pool, job_ids=job_ids, queue_ids=queue_ids)
        if not settings_existed:
            async with pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM public.queue_settings WHERE setting_key = $1", SETTINGS_KEY
                )


# ---------------------------------------------------------------------------
# SLA — configured vs not configured, against the real settings row
# ---------------------------------------------------------------------------


async def test_sla_not_configured_reads_no_breach_from_the_database(
    pool: asyncpg.Pool,
) -> None:
    """With no settings row, X4 must report `not_configured` and no breach at all."""
    org_id = await make_org(pool, "X4 No SLA Co")
    queue_ids = [await _insert_processing_queue_row(pool, org_id, breached=True)]
    settings_snapshot = None
    try:
        async with pool.acquire() as conn:
            settings_snapshot = await conn.fetchrow(
                "SELECT setting_key, setting_value FROM public.queue_settings "
                "WHERE setting_key = $1",
                SETTINGS_KEY,
            )
            await conn.execute(
                "DELETE FROM public.queue_settings WHERE setting_key = $1", SETTINGS_KEY
            )

        held = await OperationalIntelligenceService(_Bundle(pool)).summary()

        assert held["sla_state"] == "not_configured"
        assert held["sla_configured"] is False
        assert held["sla_breached_items"] is None
        assert held["sla_hours"] is None
    finally:
        await _cleanup(pool, queue_ids=queue_ids)
        if settings_snapshot is not None:
            async with pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO public.queue_settings (setting_key, setting_value) "
                    "VALUES ($1, $2::jsonb) ON CONFLICT (setting_key) DO NOTHING",
                    settings_snapshot["setting_key"],
                    settings_snapshot["setting_value"],
                )


# ---------------------------------------------------------------------------
# Truncation through the real read path
# ---------------------------------------------------------------------------


async def test_truncation_is_honest_at_the_real_read_bound(pool: asyncpg.Pool) -> None:
    """A full bound from the real read path must be reported as truncated."""
    org_id = await make_org(pool, "X4 Bound Co")
    job_ids = [await _insert_job(pool, org_id, stage="failed") for _ in range(4)]
    try:
        repo = _Bundle(pool).processing
        rows = await repo.queue_visibility_rows(limit=3)
        assert len(rows) == 3  # the real bound is honoured by the SQL

        out = aggregate_queue_rows(rows, limit=3)
        assert out["truncated"] is True
        assert out["rows_examined"] == 3

        full = await repo.queue_visibility_rows(limit=QUEUE_READ_LIMIT)
        assert aggregate_queue_rows(full, limit=QUEUE_READ_LIMIT)["truncated"] is False
    finally:
        await _cleanup(pool, job_ids=job_ids)


# ---------------------------------------------------------------------------
# Redaction — the e-mail-bearing last_error must never reach the payload
# ---------------------------------------------------------------------------


async def test_last_error_with_an_email_is_never_exposed(pool: asyncpg.Pool) -> None:
    org_id = await make_org(pool, "X4 Redaction Co")
    job_ids = [
        await _insert_job(
            pool,
            org_id,
            stage="failed",
            workflow_error_count=1,
            last_error=(
                "Extraction failed; escalation emailed to "
                "billing@customer.example.com (ref 8821)"
            ),
        )
    ]
    try:
        held = await OperationalIntelligenceService(_Bundle(pool)).summary()
        text = repr(held)

        assert "billing@customer.example.com" not in text
        assert "escalation emailed" not in text
        assert "last_error" not in text
        assert "file_url" not in text
        assert "example.invalid" not in text  # the stored file URL never surfaces
        assert org_id not in text             # no per-organisation breakdown
        # The failure is still counted — redaction must not hide the signal.
        assert held["failed_jobs"] >= 1
        assert held["error_rate_by_stage"].get("failed", 0) >= 1
    finally:
        await _cleanup(pool, job_ids=job_ids)


# ---------------------------------------------------------------------------
# Worker liveness via the real heartbeat store
# ---------------------------------------------------------------------------


async def test_worker_liveness_unknown_then_healthy_from_the_real_store(
    pool: asyncpg.Pool,
) -> None:
    from domain.operational_health import (
        HEARTBEAT_HEALTHY,
        HEARTBEAT_METRIC_NAME,
        HEARTBEAT_METRIC_TYPE,
        HEARTBEAT_UNKNOWN,
    )

    async def _clear() -> None:
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM public.dashboard_metrics "
                "WHERE metric_type = $1 AND metric_name = $2",
                HEARTBEAT_METRIC_TYPE,
                HEARTBEAT_METRIC_NAME,
            )

    repo = _Bundle(pool).processing
    await _clear()
    try:
        unknown = await OperationalIntelligenceService(_Bundle(pool)).summary()
        assert unknown["worker_liveness"]["state"] == HEARTBEAT_UNKNOWN
        assert unknown["worker_liveness"]["age_seconds"] is None

        await repo.record_worker_heartbeat(worker_id="x4-test-worker")
        healthy = await OperationalIntelligenceService(_Bundle(pool)).summary()
        assert healthy["worker_liveness"]["state"] == HEARTBEAT_HEALTHY
        assert healthy["worker_liveness"]["worker_id"] == "x4-test-worker"
    finally:
        await _clear()


# ---------------------------------------------------------------------------
# X4 must not write anything (read-only contract)
# ---------------------------------------------------------------------------


async def test_x4_writes_nothing(pool: asyncpg.Pool) -> None:
    """A read-only aggregation must leave the persisted state untouched."""
    async with pool.acquire() as conn:
        before = (
            await conn.fetchval("SELECT count(*) FROM public.document_processing_queue"),
            await conn.fetchval("SELECT count(*) FROM public.processing_queue"),
            await conn.fetchval("SELECT count(*) FROM public.dashboard_metrics"),
            await conn.fetchval("SELECT count(*) FROM public.audit_trail"),
        )

    await OperationalIntelligenceService(_Bundle(pool)).summary()

    async with pool.acquire() as conn:
        after = (
            await conn.fetchval("SELECT count(*) FROM public.document_processing_queue"),
            await conn.fetchval("SELECT count(*) FROM public.processing_queue"),
            await conn.fetchval("SELECT count(*) FROM public.dashboard_metrics"),
            await conn.fetchval("SELECT count(*) FROM public.audit_trail"),
        )
    assert before == after



