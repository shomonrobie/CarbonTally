"""Step 2 / CT-STEP2-WORKER-CANCEL-017 — cancellation-safe attempt lifecycle.

Confirmed defect (CT-STEP2-WORKER-RUNTIME-DISCREPANCY-016): an in-flight attempt
receiving ``asyncio.CancelledError`` bypassed the failure pathway, leaving the
claim held until the 300 s stale window with ``attempt_count = 0`` and no trace.

Disposable fixtures only — no database, storage or production resource is used.
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
from workers.automatic_processing import AutomaticProcessingWorker

_ORG = "11111111-1111-4111-8111-111111111111"


def _job(stage: str = "extracting", attempt_count: int = 0) -> AutomaticProcessingJob:
    return AutomaticProcessingJob(
        id=str(uuid.uuid4()),
        organization_id=_ORG,
        file_name="scan_light_gas.pdf",
        file_url="uploads/org-1/scan.pdf",
        file_type="PDF",
        stage=stage,
        status="processing",
        attempt_count=attempt_count,
        metadata={"mime": "application/pdf"},
    )


class _Recorder:
    """Records every persistence call the service/worker makes (no database)."""

    def __init__(self) -> None:
        self.failed: list[dict] = []
        self.blocked: list[dict] = []
        self.stages: list[dict] = []
        self.released: list[dict] = []

    async def mark_failed(self, job_id, *, last_error, lock_token, attempt_count=None):
        self.failed.append({"attempt_count": attempt_count, "last_error": last_error})
        return None

    async def mark_blocked(self, job_id, *, reason, lock_token, last_error=None, metadata=None):
        self.blocked.append({"reason": reason})
        return None

    async def advance_stage(self, job_id, **kw):
        self.stages.append(kw)
        return None

    async def get(self, job_id):
        return None

    async def release_lock(self, job_id, lock_token):
        self.released.append({"job_id": job_id, "lock_token": lock_token})
        return True

    async def record_interruption_and_release(self, job_id, lock_token, reason):
        self.released.append({"job_id": job_id, "lock_token": lock_token, "reason": reason})
        return True


def _service(rec: _Recorder) -> AutomaticProcessingService:
    return AutomaticProcessingService(
        SimpleNamespace(processing=rec), ai_extraction_engine=None
    )


def _blocking_extractor(seconds: float = 5.0):
    def _extract(content, name, mime, *, organization_id=None):
        time.sleep(seconds)
        return {"status": "ok", "extracted_data": {"quantity": 1}, "method": "pdf_text"}
    return _extract


def _worker(rec: _Recorder, service) -> AutomaticProcessingWorker:
    w = AutomaticProcessingWorker()
    w._repos = SimpleNamespace(processing=rec)
    w._service = service
    return w


# --- Test 1 / 2 / 3 — cancel during / immediately after claim / before persist --

@pytest.mark.asyncio
async def test_cancel_during_extraction_releases_claim_and_records_truth(monkeypatch):
    monkeypatch.setattr(auto_mod, "EXTRACTION_TIMEOUT_S", 30.0)
    monkeypatch.setattr(auto_mod, "extract_document", _blocking_extractor(3.0))
    rec = _Recorder()
    service = _service(rec)
    job = _job()
    service._content_cache[job.id] = b"%PDF-1.4"
    worker = _worker(rec, service)

    task = asyncio.create_task(worker._process_one(job, "lock-token-1"))
    await asyncio.sleep(0.3)                       # extraction in flight
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert rec.failed == [] and rec.blocked == []          # no false failure/gate
    assert rec.stages == []                                # nothing persisted
    assert len(rec.released) == 1                          # claim released + traced
    assert "interrupted" in rec.released[0]["reason"]
    assert rec.released[0]["lock_token"] == "lock-token-1"


@pytest.mark.asyncio
async def test_cancel_immediately_after_claim_does_not_orphan_the_job():
    rec = _Recorder()

    class _CancelImmediately:
        async def process_job(self, job, token):
            raise asyncio.CancelledError()

    worker = _worker(rec, _CancelImmediately())
    with pytest.raises(asyncio.CancelledError):
        await worker._process_one(_job(stage="enqueued"), "tok-2")

    assert len(rec.released) == 1 and rec.released[0]["lock_token"] == "tok-2"
    assert rec.failed == [] and rec.blocked == []


@pytest.mark.asyncio
async def test_cancel_before_persistence_never_persists_stale_results(monkeypatch):
    monkeypatch.setattr(auto_mod, "EXTRACTION_TIMEOUT_S", 30.0)
    monkeypatch.setattr(auto_mod, "extract_document", _blocking_extractor(1.0))
    rec = _Recorder()
    service = _service(rec)
    job = _job()
    service._content_cache[job.id] = b"%PDF-1.4"
    worker = _worker(rec, service)

    task = asyncio.create_task(worker._process_one(job, "tok-3"))
    await asyncio.sleep(0.2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await asyncio.sleep(1.5)            # let the orphan thread finish

    # Test 8 — late completion of the orphan thread cannot overwrite anything.
    assert rec.stages == [], "a cancelled attempt persisted stale extraction data"
    assert rec.failed == [] and rec.blocked == []
    assert len(rec.released) == 1


# --- Test 4 / 5 — timeout and ordinary failure semantics must be unchanged ----

@pytest.mark.asyncio
async def test_timeout_still_uses_the_ordinary_failure_pathway(monkeypatch):
    monkeypatch.setattr(auto_mod, "EXTRACTION_TIMEOUT_S", 0.2)
    monkeypatch.setattr(auto_mod, "extract_document", _blocking_extractor(5.0))
    rec = _Recorder()
    service = _service(rec)
    job = _job(attempt_count=1)
    service._content_cache[job.id] = b"%PDF-1.4"

    status = await service._run_stage(job, "tok-timeout")

    assert status == "failed"
    assert len(rec.failed) == 1
    assert rec.failed[0]["attempt_count"] == 2          # attempt accounting intact
    assert "execution budget" in rec.failed[0]["last_error"]
    assert rec.released == []                            # cancellation path NOT used


@pytest.mark.asyncio
async def test_ordinary_extraction_failure_is_unchanged(monkeypatch):
    def _boom(content, name, mime, *, organization_id=None):
        raise ValueError("bad workbook")

    monkeypatch.setattr(auto_mod, "extract_document", _boom)
    rec = _Recorder()
    service = _service(rec)
    job = _job(attempt_count=0)
    service._content_cache[job.id] = b"%PDF-1.4"

    status = await service._run_stage(job, "tok-fail")

    assert status == "failed"
    assert rec.failed[0]["attempt_count"] == 1
    assert "ValueError" in rec.failed[0]["last_error"]
    assert rec.released == []


# --- Test 6 — graceful worker shutdown with an in-flight job -----------------

@pytest.mark.asyncio
async def test_graceful_worker_stop_releases_the_in_flight_claim(monkeypatch):
    started = asyncio.Event()
    rec = _Recorder()

    class _SlowService:
        async def process_job(self, job, token):
            started.set()
            await asyncio.sleep(30)                  # in-flight when stopped

    worker = _worker(rec, _SlowService())

    async def fake_claim(token, *, limit=3, stale_after_seconds=300):
        return [_job(stage="enqueued")]

    worker._tick = lambda: None                        # replaced below

    async def tick():
        if worker._repos is None:
            worker._repos = SimpleNamespace(processing=rec)
        jobs = await fake_claim("tok")
        await asyncio.gather(*(worker._process_one(j, "tok") for j in jobs),
                             return_exceptions=True)

    worker._tick = tick
    worker._poll_interval_seconds = 0.01
    await worker.start()
    await asyncio.wait_for(started.wait(), timeout=5)
    await worker.stop()

    assert len(rec.released) == 1, "shutdown left the claim orphaned"
    assert rec.failed == [] and rec.blocked == []
    assert worker._task is None                        # worker remains stoppable


# --- Test 7 — a released (cancelled) job cannot starve later jobs -------------

@pytest.mark.asyncio
async def test_interruption_release_clears_the_lock_so_later_jobs_are_claimable():
    repo = dp_mod.DocumentProcessingRepository.__new__(dp_mod.DocumentProcessingRepository)
    seen: list[str] = []

    async def _execute(sql, *args):
        seen.append(" ".join(str(sql).split()))
        return "UPDATE 1"

    repo._execute = _execute                              # type: ignore[assignment]
    ok = await repo.record_interruption_and_release("job-1", "tok-1", "interrupted")

    assert ok is True
    sql = seen[0]
    assert "locked_at = NULL" in sql and "lock_token = NULL" in sql
    assert "WHERE id = $1 AND lock_token = $2" in sql     # owner-scoped only
    assert "SET stage" not in sql and "status =" not in sql  # no state lies
    assert "last_error = $3" in sql                       # truthful trace recorded


# --- Test 8b — the cancellation outcome is recorded, not swallowed ------------

@pytest.mark.asyncio
async def test_worker_re_raises_cancellation_after_releasing(monkeypatch):
    rec = _Recorder()

    class _Cancel:
        async def process_job(self, job, token):
            raise asyncio.CancelledError()

    worker = _worker(rec, _Cancel())
    with pytest.raises(asyncio.CancelledError):
        await worker._process_one(_job(), "tok-x")
    assert len(rec.released) == 1
