"""Step 2 / CT-STEP2-WORKER-TIMEOUT-013 — bounded, non-blocking extraction (F1–F4).

Remediation under test
----------------------
F1 — one extraction attempt must have a finite upper bound.
F2 — CPU-bound PDF/OCR work must not run on the asyncio event loop.
F3 — a small group of stuck/executing jobs must not starve later queued jobs.
F4 — a hung job must leave the executing state through the existing
     failure/attempt-accounting pathway (never loop forever, never fabricate).

Disposable fixtures only; no database, storage or production resource is used.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from types import SimpleNamespace

import pytest

import data.document_processing as dp_mod
import services.automatic_processing as auto_mod
from domain.automatic_processing import AutomaticProcessingJob
from services.automatic_processing import AutomaticProcessingService

_ORG = "11111111-1111-4111-8111-111111111111"


def _job(attempt_count: int = 0, extracted_data=None) -> AutomaticProcessingJob:
    return AutomaticProcessingJob(
        id=str(uuid.uuid4()),
        organization_id=_ORG,
        file_name="scan.pdf",
        file_url="uploads/org-1/scan.pdf",
        file_type="PDF",
        stage="extracting",
        status="processing",
        attempt_count=attempt_count,
        metadata={"mime": "application/pdf"},
        source_item_id="item-timeout",
        extracted_data=extracted_data,
    )


class _RecordingProcessing:
    """Records the persistence calls the service makes (no database involved)."""

    def __init__(self) -> None:
        self.failed: list[dict] = []
        self.blocked: list[dict] = []
        self.stages: list[dict] = []
        self.released: list[str] = []
        self._job = None

    async def mark_failed(self, job_id, *, last_error, lock_token, attempt_count=None):
        self.failed.append(
            {"job_id": job_id, "last_error": last_error, "attempt_count": attempt_count}
        )
        return self._job

    async def mark_blocked(self, job_id, *, reason, lock_token, last_error=None, metadata=None):
        self.blocked.append({"job_id": job_id, "reason": reason})
        return self._job

    async def advance_stage(self, job_id, **kwargs):
        self.stages.append({"job_id": job_id, **kwargs})
        return self._job

    async def get(self, job_id):
        return self._job

    async def release_lock(self, job_id, lock_token):
        self.released.append(job_id)
        return True


def _service(processing: _RecordingProcessing) -> AutomaticProcessingService:
    return AutomaticProcessingService(
        SimpleNamespace(processing=processing), ai_extraction_engine=None
    )


def _blocking_extractor(seconds: float = 5.0):
    """A synchronous engine call that blocks far longer than the budget."""

    def _extract(content, name, mime, *, organization_id=None):
        time.sleep(seconds)
        return {"status": "ok", "extracted_data": {"quantity": 1}, "method": "pdf_text"}

    return _extract


@pytest.mark.asyncio
async def test_F1_a_never_returning_extraction_is_bounded(monkeypatch):
    """F1/I1 — the attempt cannot run forever."""
    monkeypatch.setattr(auto_mod, "EXTRACTION_TIMEOUT_S", 0.2)
    monkeypatch.setattr(auto_mod, "extract_document", _blocking_extractor(5.0))
    service = _service(_RecordingProcessing())

    started = time.monotonic()
    with pytest.raises(TimeoutError) as excinfo:
        await service._run_bounded_extraction(_job(), b"%PDF-1.4")
    elapsed = time.monotonic() - started

    assert elapsed < 3.0, "the extraction budget was not enforced"
    assert "execution budget" in str(excinfo.value)


@pytest.mark.asyncio
async def test_F2_blocking_extraction_does_not_block_the_event_loop(monkeypatch):
    """F2/I2 — a synchronous extractor must not stall independent coroutines."""
    monkeypatch.setattr(auto_mod, "EXTRACTION_TIMEOUT_S", 1.0)
    monkeypatch.setattr(auto_mod, "extract_document", _blocking_extractor(0.8))
    service = _service(_RecordingProcessing())

    ticks = 0

    async def heartbeat() -> None:
        nonlocal ticks
        while True:
            ticks += 1
            await asyncio.sleep(0.05)

    hb = asyncio.create_task(heartbeat())
    result = await service._run_bounded_extraction(_job(), b"%PDF-1.4")
    hb.cancel()

    assert result["status"] == "ok"          # I11 — success path unchanged
    assert ticks >= 5, f"event loop was blocked (only {ticks} heartbeats)"


@pytest.mark.asyncio
async def test_F4_timeout_reaches_the_existing_failure_pathway(monkeypatch):
    """F4/I5/I6 — timeout → mark_failed(+1 attempt), truthful reason, no gate."""
    monkeypatch.setattr(auto_mod, "EXTRACTION_TIMEOUT_S", 0.2)
    monkeypatch.setattr(auto_mod, "extract_document", _blocking_extractor(5.0))
    processing = _RecordingProcessing()
    service = _service(processing)
    job = _job(attempt_count=1)
    processing._job = job
    service._content_cache[job.id] = b"%PDF-1.4"   # no storage access in a unit test

    status = await service._run_stage(job, "lock-token")

    assert status == "failed"
    assert len(processing.failed) == 1
    record = processing.failed[0]
    assert record["attempt_count"] == 2, "timeout must participate in attempt accounting"
    assert record["last_error"].startswith("TimeoutError")
    assert "execution budget" in record["last_error"]
    # I3 — no fabrication and no false manual-review gate on a timeout.
    assert processing.blocked == []
    assert processing.stages == []


@pytest.mark.asyncio
async def test_I4_timeout_does_not_overwrite_persisted_partial_evidence(monkeypatch):
    """I4 — a pre-existing partial extraction must survive a timeout unchanged."""
    monkeypatch.setattr(auto_mod, "EXTRACTION_TIMEOUT_S", 0.2)
    monkeypatch.setattr(auto_mod, "extract_document", _blocking_extractor(5.0))
    processing = _RecordingProcessing()
    service = _service(processing)
    job = _job(extracted_data={"quantity": 1, "unresolved": ["unit"]})  # already persisted
    processing._job = job
    service._content_cache[job.id] = b"%PDF-1.4"

    status = await service._run_stage(job, "lock-token")

    # The extraction stage resumes on persisted output, so a timeout cannot
    # erase it: no writer is invoked with placeholder data.
    assert status in ("mapping", "failed")
    assert processing.blocked == []
    assert all(
        call.get("extracted_data") is None for call in processing.stages
    ), "persisted extraction evidence was overwritten"


class _SqlCapturingRepository(dp_mod.DocumentProcessingRepository):
    """Captures the SQL the claim issues (no database connection is opened)."""

    def __init__(self) -> None:
        self.statements: list[str] = []
        self.args: list[tuple] = []

    async def _execute(self, sql, *args):          # type: ignore[override]
        self.statements.append(" ".join(str(sql).split()))
        self.args.append(args)
        return "UPDATE 3"

    async def _fetch_all(self, sql, *args):        # type: ignore[override]
        self.statements.append(" ".join(str(sql).split()))
        self.args.append(args)
        return []


@pytest.mark.asyncio
async def test_F3_claim_skips_freshly_locked_jobs_and_releases_stale_first():
    """F3/I7/I8 — the candidate predicate respects a fresh claim (starvation fix)."""
    repo = _SqlCapturingRepository()
    await repo.claim_next("token-1", limit=3, stale_after_seconds=300)

    assert len(repo.statements) == 2, "claim must release stale locks then select"
    release, claim = repo.statements

    # 1) stale claims are released first (crashed-worker recovery, I9)
    assert "locked_at IS NOT NULL AND locked_at < $1" in release
    assert "locked_at = NULL" in release

    # 2) only UNLOCKED rows are candidates — a busy job is not re-claimed, so
    #    FIFO order reaches the jobs queued behind it (3 stuck jobs no longer
    #    starve a 4th pending job, I7).
    assert "locked_at IS NULL" in claim
    assert "FOR UPDATE SKIP LOCKED" in claim, "claim atomicity was weakened"
    assert "ORDER BY created_at, id" in claim, "FIFO ordering was lost"
    assert "LIMIT 3" in claim
    assert "token-1" in repo.args[1], "the worker lock token was not bound"


