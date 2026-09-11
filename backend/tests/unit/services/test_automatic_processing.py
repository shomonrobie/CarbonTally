"""Unit tests for the automatic-processing service (CL-56) with fake repos."""
from __future__ import annotations

import uuid
from collections.abc import Iterator
from decimal import Decimal
from typing import Any, Optional

import pytest

from domain.automatic_processing import AutomaticProcessingJob
from domain.factor import EmissionFactor
from domain.matching import MatchResult
from services.automatic_processing import AutomaticProcessingService

_ORG = "11111111-1111-4111-8111-111111111111"

#: AI-extraction identity env vars read by the T2 attribution helper; blanked
#: before each test so attribution facts are deterministic (unconfigured).
_AI_ATTR_ENV_KEYS = (
    "CARBONTALLY_AI_BASE_URL",
    "CARBONTALLY_AI_API_KEY",
    "CARBONTALLY_AI_MODEL",
)


@pytest.fixture(autouse=True)
def _neutral_ai_attribution_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Blank every AI-extraction identity env var before each test."""
    for key in _AI_ATTR_ENV_KEYS:
        monkeypatch.setenv(key, "")
    yield
_FACTOR = EmissionFactor(
    id="factor-1",
    reporting_year=2025,
    activity_type="Fuels > Liquid fuels > Diesel (kg CO2e) [litres]",
    co2e_multiplier=Decimal("2.668"),
    unit="litres",
    scope="Scope 1",
    factor_source="DEFRA-DESNZ",
    factor_set="DEFRA-2025",
)


class _FakeProcessing:
    """Durable-job store + transition recording (mirrors the repository)."""

    def __init__(self) -> None:
        self.store: dict[str, AutomaticProcessingJob] = {}
        self.marked_blocked: list[str] = []
        self.marked_failed: list[str] = []
        self.advances: list[dict[str, Any]] = []

    @staticmethod
    def _clone(job: AutomaticProcessingJob, **changes) -> AutomaticProcessingJob:
        import dataclasses

        base = dataclasses.asdict(job)
        base.update(changes)
        return AutomaticProcessingJob(**base)

    async def get(self, job_id: str) -> Optional[AutomaticProcessingJob]:
        return self.store.get(job_id)

    async def advance_stage(self, job_id: str, **kw: Any) -> Optional[AutomaticProcessingJob]:
        job = self.store[job_id]
        stage = kw.get("target_stage", job.stage)
        changes: dict[str, Any] = {
            "stage": stage,
            "status": "processing"
            if stage not in ("review", "completed", "failed", "blocked")
            else stage,
        }
        for key in ("extracted_data", "mapped_data", "validation_result",
                    "calculation_snapshot_id", "attempt_count"):
            if key in kw:
                changes[key] = kw[key]
        # Phase 2 — provenance persistence recorded by the real repository.
        if "metadata" in kw and kw["metadata"]:
            changes["metadata"] = {**(job.metadata or {}), **kw["metadata"]}
        # WS4 Gate 5 (task T3) — write-once automation attribution mirrors the
        # repository COALESCE semantics: existing values are never overwritten.
        for key in ("automation_provider", "automation_model", "automation_model_version"):
            if kw.get(key) is not None and getattr(job, key, None) is None:
                changes[key] = kw[key]
        # WS4 Gate 6 (workstream W1 / gap G6-A) — write-once preservation of the
        # original automated extraction output (mirrors repository COALESCE).
        if (
            kw.get("automation_extracted_data") is not None
            and job.automation_extracted_data is None
        ):
            changes["automation_extracted_data"] = kw["automation_extracted_data"]
        updated = self._clone(job, **changes)
        self.store[job_id] = updated
        self.advances.append(kw)
        self.last_advance_kw = kw
        return updated

    async def mark_blocked(self, job_id: str, *, reason: str, lock_token: str, **kw: Any):
        self.marked_blocked.append(reason)
        job = self.store[job_id]
        updated = self._clone(job, stage="blocked", status="manual_review",
                              manual_review_reason=reason)
        self.store[job_id] = updated
        return updated

    async def mark_failed(self, job_id: str, *, last_error: str, lock_token: str, **kw: Any):
        self.marked_failed.append(last_error)
        job = self.store[job_id]
        updated = self._clone(job, stage="failed", status="failed", last_error=last_error)
        self.store[job_id] = updated
        return updated

    async def release_lock(self, job_id: str, lock_token: str) -> bool:
        return True

    async def mark_notified(self, job_id: str):
        return None


class _FakeRepos:
    def __init__(self, job: AutomaticProcessingJob) -> None:
        self.processing = _FakeProcessing()
        self.processing.store[job.id] = job
        self.logs = _FakeLogs()
        self.organizations = _FakeOrganizations()


class _FakeFactors:
    async def get(self, factor_id: str) -> Optional[EmissionFactor]:
        return _FACTOR if factor_id == _FACTOR.id else None

    async def find_by_activity(self, activity: str, unit: Optional[str] = None, limit: int = 20):
        return [_FACTOR]


class _FakeCustomerFactors:
    async def get(self, factor_id: str):
        return None


class _FakeLogs:
    def __init__(self) -> None:
        self.snapshots: dict[str, dict] = {}

    async def find_snapshot_by_request_id(self, request_id: str) -> Optional[dict]:
        return self.snapshots.get(request_id)


class _FakeOrganizations:
    async def get_members(self, org_id: str):
        return []


class _FakeNotifications:
    async def create(self, *args: Any, **kw: Any):
        return None


class _FakeAuditLogger:
    """Records AuditLogger.log_action calls (optional failure injection)."""

    def __init__(self, *, fail: bool = False) -> None:
        self.actions: list[dict[str, Any]] = []
        self.fail = fail

    async def log_action(self, **kw: Any):
        if self.fail:
            raise RuntimeError("audit sink unavailable")
        self.actions.append(kw)


class _FakeManualExtraction:
    async def save_extracted_data(self, *a: Any, **k: Any):
        return None

    async def save_mapped_data(self, *a: Any, **k: Any):
        return None

    async def set_item_status(self, *a: Any, **k: Any):
        return None

    async def save_calculation(self, *a: Any, **k: Any):
        return None


class _FakeMatchingEngine:
    async def match(self, request):
        return MatchResult(
            status="matched",
            factor=_FACTOR,
            confidence=1.0,
            methodology="keyword_search",
            stages_executed=("keyword_search",),
        )


class _FakeCalculationEngine:
    def __init__(self) -> None:
        self.calls = 0

    async def calculate(self, request):
        from types import SimpleNamespace

        self.calls += 1
        return SimpleNamespace(
            snapshot=SimpleNamespace(
                id=f"snap-{self.calls}", co2e_kg=Decimal("10.0")
            )
        )


def _csv_job(**overrides) -> AutomaticProcessingJob:
    base = dict(
        id=str(uuid.uuid4()),
        organization_id=_ORG,
        file_name="fleet.csv",
        file_url="uploads/org-1/fleet.csv",
        file_type="SPREADSHEET",
        stage="enqueued",
        status="pending",
        metadata={"mime": "text/csv"},
        source_item_id="item-1",
    )
    base.update(overrides)
    return AutomaticProcessingJob(**base)


def _make_service(job: AutomaticProcessingJob, audit_logger=None):
    repos = _FakeRepos(job)
    repos.factors = _FakeFactors()
    repos.customer_factors = _FakeCustomerFactors()
    repos.notifications = _FakeNotifications()
    repos.manual_extraction = _FakeManualExtraction()
    service = AutomaticProcessingService(
        repos,
        matching_engine=_FakeMatchingEngine(),
        calculation_engine=_FakeCalculationEngine(),
        audit_logger=audit_logger,
    )
    service._content_cache[job.id] = (
        "Date,Supplier,Category,Quantity (litres),Amount,Currency\n"
        "05/01/2025,Shell Fleet Solutions,Diesel fuel,1250,1775.00,GBP\n"
    ).encode("utf-8")
    return service, repos


class TestPipelineExecution:
    async def test_full_auto_flow_reaches_review(self) -> None:
        job = _csv_job()
        service, repos = _make_service(job)
        final = await service.process_job(job, "token-1")
        assert final.stage == "review"
        assert final.extracted_data is not None
        assert final.mapped_data is not None
        assert final.validation_result == {"status": "passed", "findings": []}

    async def test_blocked_job_does_not_reprocess(self) -> None:
        job = _csv_job(stage="blocked", status="manual_review")
        service, repos = _make_service(job)
        final = await service.process_job(job, "token-1")
        assert final.stage == "blocked"
        assert repos.processing.marked_blocked == []

    async def test_idempotent_resume_skips_extraction(self) -> None:
        job = _csv_job(
            stage="extracting",
            status="processing",
            extracted_data={
                "supplier": "Shell Fleet Solutions",
                "date": "05/01/2025",
                "activity": "Diesel",
                "quantity": 1250.0,
                "unit": "litres",
            },
        )
        service, repos = _make_service(job)
        final = await service.process_job(job, "token-1")
        assert final.stage == "review"
        assert final.extracted_data["activity"] == "Diesel"

    async def test_no_duplicate_calculation_reuses_snapshot(self) -> None:
        job = _csv_job()
        service, repos = _make_service(job)
        await service.process_job(job, "token-1")
        first = repos.processing.store[job.id]
        calc = service._calculation_engine
        # A re-run of the same job (e.g. after a crash) reuses the snapshot.
        await service.process_job(first, "token-2")
        assert calc.calls == 1
        second = repos.processing.store[job.id]
        assert second.calculation_snapshot_id == first.calculation_snapshot_id

# ---------------------------------------------------------------------------
# Phase 2 — candidate AI extraction inside the durable pipeline. AI is optional
# (provider configured) and CANDIDATE-only: deterministic fields win, the
# deterministic completeness gate still applies, failures are durable, and
# nothing is calculated until the canonical mapping/validation/calculation
# stages accept the merged data.
# ---------------------------------------------------------------------------


class _FakeAIEngine:
    def __init__(self, result: dict) -> None:
        from types import SimpleNamespace

        self.result = result
        self.calls = 0
        self.last_text = ""
        # Mirrors the real AIDocumentExtractionEngine.llm_client so the service
        # can read the attempted model id for truthful failure envelopes.
        self.llm_client = SimpleNamespace(
            model=(result.get("model") or "test-model"),
            base_url=(result.get("base_url") or "https://api.openai.com/v1"),
        )

    async def extract_candidate(self, text: str, *, filename: str = "", method: str = "pdf_text") -> dict:
        self.calls += 1
        self.last_text = text
        return dict(self.result)


def _pdf_job(**overrides) -> AutomaticProcessingJob:
    base = dict(
        id=str(uuid.uuid4()),
        organization_id=_ORG,
        file_name="invoice.pdf",
        file_url="uploads/org-1/invoice.pdf",
        file_type="PDF",
        stage="enqueued",
        status="pending",
        metadata={"mime": "application/pdf"},
        source_item_id="item-p2",
    )
    base.update(overrides)
    return AutomaticProcessingJob(**base)


def _low_conf_deterministic(content: bytes, filename: str, mime: str) -> dict:
    """Deterministic pass that only resolves ``activity`` (completeness 1/3)."""
    return {
        "status": "ok",
        "method": "pdf_text",
        "page_count": 1,
        "extracted_data": {"activity": "Diesel"},
        "unresolved": ["quantity", "unit"],
        "confidence": 0.3333,
    }


def _full_deterministic(content: bytes, filename: str, mime: str) -> dict:
    """Deterministic pass that resolves every required field (completeness 1.0)."""
    return {
        "status": "ok",
        "method": "pdf_text",
        "page_count": 1,
        "extracted_data": {
            "activity": "Diesel",
            "quantity": 1250,
            "unit": "litres",
            "supplier": "Shell Fleet",
            "date": "2025-01-05",
        },
        "unresolved": [],
        "confidence": 1.0,
    }


_AI_OK = {
    "status": "ok",
    "method": "ai:pdf_text",
    "model": "test-model",
    "extracted_data": {
        "quantity": 1250,
        "unit": "litres",
        "date": "2025-01-05",
        "supplier": "Shell Fleet",
    },
    "unresolved": [],
    "confidence": 1.0,
}


async def _run_with_ai(
    job: AutomaticProcessingJob,
    ai_result: dict,
    *,
    deterministic=_low_conf_deterministic,
    text="Natural gas supply invoice with 1250 litres of diesel",
    audit_logger=None,
):
    import services.automatic_processing as auto_mod
    import services.automatic_extraction as auto_extract_mod

    repos = _FakeRepos(job)
    repos.factors = _FakeFactors()
    repos.customer_factors = _FakeCustomerFactors()
    repos.notifications = _FakeNotifications()
    repos.manual_extraction = _FakeManualExtraction()
    ai = _FakeAIEngine(ai_result)
    service = AutomaticProcessingService(
        repos,
        matching_engine=_FakeMatchingEngine(),
        calculation_engine=_FakeCalculationEngine(),
        ai_extraction_engine=ai,
        audit_logger=audit_logger,
    )
    service._content_cache[job.id] = b"x" * 200

    def _fake_text(content: bytes, filename: str, mime: str) -> dict:
        return {
            "status": "ok", "ftype": "PDF", "text": text,
            "method": "pdf_text", "page_count": 1,
        }

    # The deterministic text/field layers are unit-isolated so the pipeline
    # logic under test is deterministic.
    auto_mod.extract_document = deterministic
    auto_mod.extract_document_text = _fake_text
    final = await service.process_job(job, "token-p2")
    # Restore module functions for other tests.
    auto_mod.extract_document = auto_extract_mod.extract_document
    auto_mod.extract_document_text = auto_extract_mod.extract_document_text
    return service, repos, ai, final


class TestPhase2AIDurableExtraction:
    async def test_low_confidence_deterministic_invokes_ai_and_reaches_review(self):
        # A low-completeness deterministic extraction + a confident AI candidate
        # must flow through mapping → validation → calculation → review.
        job = _pdf_job()
        service, repos, ai, final = await _run_with_ai(job, _AI_OK)
        assert ai.calls == 1
        assert final.stage == "review"
        stored = repos.processing.store[job.id]
        assert stored.extracted_data["activity"] == "Diesel"  # deterministic won
        assert stored.extracted_data["quantity"] == 1250
        assert stored.extracted_data["unit"] == "litres"  # AI filled the gap
        # Provenance survived: AI metadata is persisted on the durable job.
        ai_meta = (stored.metadata or {}).get("ai_extraction")
        assert ai_meta is not None
        assert ai_meta["status"] == "ok"
        assert ai_meta["model"] == "test-model"
        assert ai_meta["method"] == "ai:pdf_text"
        assert ai_meta["merged_confidence"] == 1.0
        # The extraction-stage advance carried the AI provenance to persistence.
        extract_advance = next(
            a for a in repos.processing.advances
            if a.get("target_stage") == "mapping" and "extracted_data" in a
        )
        assert extract_advance.get("ai_processing_time_ms") is not None
        assert extract_advance.get("ai_extraction_result") is not None
        assert extract_advance.get("ai_extraction_result")["model"] == "test-model"
        assert extract_advance.get("ai_extraction_method", "").startswith(
            "pdf_text+ai:"
        )

    async def test_ai_failure_is_durable_and_blocks_for_manual_review(self):
        job = _pdf_job()
        failed = {
            "status": "error",
            "method": "ai",
            "model": None,
            "extracted_data": {},
            "unresolved": [],
            "confidence": 0.0,
            "detail": "LLM API returned HTTP 500",
        }
        service, repos, ai, final = await _run_with_ai(job, failed)
        assert ai.calls == 1
        # Job is NOT lost and NOT falsely successful — it is blocked durably.
        assert final.stage == "blocked"
        assert repos.processing.marked_blocked == [
            "AI extraction failed: LLM API returned HTTP 500 "
            "(deterministic completeness 0.33 below 0.50 threshold)"
        ]
        stored = repos.processing.store[job.id]
        assert stored.manual_review_reason is not None
        assert "HTTP 500" in stored.manual_review_reason
        # Retry is the existing durable mechanism: a blocked job re-enters via
        # enqueued and stages re-run idempotently (attempts bounded).
        assert stored.stage == "blocked"
        assert stored.status == "manual_review"

    async def test_ai_merge_persists_write_once_automation_block(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A contributing AI pass must persist the T2 attribution facts on the
        # durable job (write-once), and a later advance must never overwrite it.
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "test-model")
        job = _pdf_job()
        service, repos, ai, final = await _run_with_ai(job, _AI_OK)
        assert ai.calls == 1
        assert final.stage == "review"
        stored = repos.processing.store[job.id]
        assert stored.automation_provider == "openai"
        assert stored.automation_model == "test-model"
        assert stored.automation_model_version is None
        extract_advance = next(
            a for a in repos.processing.advances
            if a.get("target_stage") == "mapping" and "extracted_data" in a
        )
        assert extract_advance.get("automation_provider") == "openai"
        assert extract_advance.get("automation_model") == "test-model"
        assert extract_advance.get("automation_model_version") is None
        # Write-once (per-column COALESCE, design 5.1): a later advance carrying
        # different attribution values must never overwrite the persisted ones.
        await repos.processing.advance_stage(
            job.id,
            target_stage="validating",
            lock_token="token-later",
            automation_provider="anthropic",
            automation_model="other-model",
        )
        after = repos.processing.store[job.id]
        assert after.automation_provider == "openai"
        assert after.automation_model == "test-model"
        assert after.automation_model_version is None

    async def test_deterministic_only_run_keeps_automation_block_null(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Even with a provider configured, no AI engine exists -> deterministic
        # only; the automation block must stay NULL (no fabrication).
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "test-model")
        job = _csv_job()
        service, repos = _make_service(job)
        assert service.ai_extraction_engine is None
        final = await service.process_job(job, "token-t3")
        assert final.stage == "review"
        stored = repos.processing.store[job.id]
        assert stored.automation_provider is None
        assert stored.automation_model is None
        assert stored.automation_model_version is None

    async def test_failed_ai_attempt_records_attempted_model_but_not_contribution(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # AI runs (prefer_ai) and fails, but the deterministic pass already
        # cleared the gate -> the job proceeds deterministically. The failed
        # attempt must be durably recorded WITH the attempted model id, while
        # the automation block stays NULL (AI did not contribute).
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.anthropic.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "claude-attempt")
        failed = {
            "status": "error",
            "method": "ai",
            "model": None,
            "extracted_data": {},
            "unresolved": [],
            "confidence": 0.0,
            "detail": "upstream timeout",
        }
        job = _pdf_job(metadata={"mime": "application/pdf", "prefer_ai": True})
        service, repos, ai, final = await _run_with_ai(
            job, failed, deterministic=_full_deterministic
        )
        assert ai.calls == 1
        assert final.stage == "review"  # deterministic-only output proceeded
        stored = repos.processing.store[job.id]
        # Failed AI is NOT a contributing automation -> block stays NULL even
        # though a provider/model were configured.
        assert stored.automation_provider is None
        assert stored.automation_model is None
        assert stored.automation_model_version is None
        # The durable attempt record truthfully carries the attempted model id.
        stored_ai = (stored.metadata or {}).get("ai_extraction") or {}
        assert stored_ai.get("status") == "error"
        assert stored_ai.get("model") == "test-model"  # engine-attempted model
        assert stored_ai.get("detail") == "upstream timeout"

    async def test_no_ai_engine_keeps_purely_deterministic_flow(self):
        job = _csv_job()
        service, repos = _make_service(job)
        assert service.ai_extraction_engine is None
        final = await service.process_job(job, "token-1")
        assert final.stage == "review"
        assert (repos.processing.store[job.id].metadata or {}).get("ai_extraction") is None

    async def test_deterministic_values_win_over_ai_candidates(self):
        # Deterministic extraction fully resolves the line; AI (even if it
        # disagrees) must NOT overwrite deterministic source evidence.
        job = _pdf_job(metadata={"mime": "application/pdf", "prefer_ai": True})

        def _full_deterministic(content: bytes, filename: str, mime: str) -> dict:
            return {
                "status": "ok",
                "method": "pdf_text",
                "page_count": 1,
                "extracted_data": {
                    "line_items": [{
                        "activity": "Diesel", "quantity": 1250.0, "unit": "litres",
                        "date": "05/01/2025", "supplier": "Shell Fleet",
                    }]
                },
                "unresolved": [],
                "confidence": 1.0,
            }

        ai_contradict = dict(_AI_OK)
        ai_contradict["extracted_data"] = {"quantity": 999, "unit": "kWh"}
        service, repos, ai, final = await _run_with_ai(
            job, ai_contradict, deterministic=_full_deterministic
        )
        assert ai.calls == 1  # prefer_ai invoked the candidate pass
        stored = repos.processing.store[job.id]
        line = stored.extracted_data["line_items"][0]
        assert line["quantity"] == 1250.0  # deterministic won
        assert line["unit"] == "litres"

    async def test_ai_not_reinvoked_on_idempotent_resume(self):
        # Extraction resume marker exists → AI must not be called again and the
        # job continues through the existing resume path.
        job = _pdf_job(
            stage="extracting",
            status="processing",
            extracted_data={
                "activity": "Diesel", "quantity": 1250.0, "unit": "litres",
                "supplier": "Shell Fleet", "date": "2025-01-05",
            },
        )
        repos = _FakeRepos(job)
        repos.factors = _FakeFactors()
        repos.customer_factors = _FakeCustomerFactors()
        repos.notifications = _FakeNotifications()
        repos.manual_extraction = _FakeManualExtraction()
        ai = _FakeAIEngine(_AI_OK)
        service = AutomaticProcessingService(
            repos,
            matching_engine=_FakeMatchingEngine(),
            calculation_engine=_FakeCalculationEngine(),
            ai_extraction_engine=ai,
        )
        final = await service.process_job(job, "token-1")
        assert ai.calls == 0
        assert final.stage == "review", (
            f"stage={final.stage} blocked={repos.processing.marked_blocked} "
            f"failed={repos.processing.marked_failed} "
            f"reason={(repos.processing.store[job.id]).manual_review_reason}"
        )

# ---------------------------------------------------------------------------
# WS4 Gate 5 (task T4) — automatic-processing extraction audit event
# (action "automatic_processing:extracted", machine actor "automatic_pipeline",
# fired after the persisted extraction advance; best-effort/never breaks job).
# ---------------------------------------------------------------------------


class TestT4ExtractionAudit:
    async def test_deterministic_extraction_writes_machine_audit_event(self) -> None:
        job = _csv_job()
        audit = _FakeAuditLogger()
        service, repos = _make_service(job, audit_logger=audit)
        final = await service.process_job(job, "token-t4")
        assert final.stage == "review"
        assert len(audit.actions) == 1
        entry = audit.actions[0]
        assert entry["action"] == "automatic_processing:extracted"
        assert entry["entity_type"] == "document_processing_queue"
        assert entry["entity_id"] == job.id
        assert entry["correlation_id"] == job.id
        assert entry["actor"] == "automatic_pipeline"
        after = entry["after"]
        assert after["method"] == "csv"
        assert after["pipeline_version"] is None  # job not stamped in this fake
        assert after["provider"] is None
        assert after["model"] is None
        assert after["model_version"] is None
        assert after["confidence"] == 1.0
        assert after["attempt_count"] == 1
        assert after["source_item_id"] == job.source_item_id
        assert after["ai_status"] is None  # deterministic-only run

    async def test_contributing_ai_extraction_audit_carries_attribution(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "test-model")
        job = _pdf_job()
        audit = _FakeAuditLogger()
        service, repos, ai, final = await _run_with_ai(
            job, _AI_OK, audit_logger=audit
        )
        assert ai.calls == 1
        assert final.stage == "review"
        assert len(audit.actions) == 1
        entry = audit.actions[0]
        assert entry["action"] == "automatic_processing:extracted"
        assert entry["actor"] == "automatic_pipeline"
        after = entry["after"]
        assert after["provider"] == "openai"
        assert after["model"] == "test-model"
        assert after["model_version"] is None
        assert after["ai_status"] == "ok"
        assert after["source_item_id"] == job.source_item_id

    async def test_audit_failure_never_breaks_job(self) -> None:
        job = _csv_job()
        audit = _FakeAuditLogger(fail=True)
        service, repos = _make_service(job, audit_logger=audit)
        final = await service.process_job(job, "token-t4")
        # Audit failure is swallowed; the job still completes its pipeline.
        assert final.stage == "review"
        assert repos.processing.marked_failed == []

    async def test_blocked_ai_failure_writes_no_extraction_audit(self) -> None:
        # No persisted extraction output -> no "extracted" audit event.
        job = _pdf_job()
        audit = _FakeAuditLogger()
        failed = {
            "status": "error",
            "method": "ai",
            "model": None,
            "extracted_data": {},
            "unresolved": [],
            "confidence": 0.0,
            "detail": "LLM API returned HTTP 500",
        }
        service, repos, ai, final = await _run_with_ai(
            job, failed, audit_logger=audit
        )
        assert ai.calls == 1
        assert final.stage == "blocked"
        assert audit.actions == []


# ---------------------------------------------------------------------------
# WS4 Gate 6 (workstream W1 / gap G6-A) — preserve the original automated
# extraction output independently of later human edits.
# ---------------------------------------------------------------------------


class TestGate6W1PreserveAutomatedOutput:
    """Original machine output is preserved write-once at first extraction."""

    async def test_contributing_ai_preserves_original_automated_output(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "test-model")
        job = _pdf_job()
        service, repos, ai, final = await _run_with_ai(job, _AI_OK)
        assert ai.calls == 1
        assert final.stage == "review"
        stored = repos.processing.store[job.id]
        # The preserved original equals the machine output persisted as the
        # working extraction at the time the automatic pipeline produced it.
        assert stored.automation_extracted_data is not None
        assert stored.automation_extracted_data == stored.extracted_data
        assert stored.automation_extracted_data["activity"] == "Diesel"
        assert stored.automation_extracted_data["quantity"] == 1250
        assert stored.automation_extracted_data["unit"] == "litres"
        # The extraction-stage advance carried the payload to persistence.
        extract_advance = next(
            a for a in repos.processing.advances
            if a.get("target_stage") == "mapping" and "extracted_data" in a
        )
        assert extract_advance.get("automation_extracted_data") == (
            extract_advance.get("extracted_data")
        )
        # Gate-5 provenance remains intact.
        assert stored.automation_provider == "openai"
        assert stored.automation_model == "test-model"
        assert stored.automation_model_version is None

    async def test_preserved_original_survives_human_edit_of_current_output(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "test-model")
        job = _pdf_job()
        service, repos, ai, final = await _run_with_ai(job, _AI_OK)
        assert final.stage == "review"
        original = dict(repos.processing.store[job.id].automation_extracted_data)
        current_before = repos.processing.store[job.id].extracted_data
        # Simulate the human correction path (sync_item_data / item save):
        # the working extraction is overwritten; the preserved original is not.
        import dataclasses

        human_corrected = dataclasses.replace(
            repos.processing.store[job.id],
            extracted_data={
                "activity": "Natural gas", "quantity": 900, "unit": "kWh",
                "date": "2025-01-05", "supplier": "Corrected Supplier",
            },
        )
        repos.processing.store[job.id] = human_corrected
        after = repos.processing.store[job.id]
        assert after.extracted_data != current_before
        assert after.automation_extracted_data == original
        assert after.automation_extracted_data != after.extracted_data
        # Gate-5 provenance unchanged through the human edit.
        assert after.automation_provider == "openai"
        assert after.automation_model == "test-model"

    async def test_preserved_output_cannot_be_overwritten_or_cleared(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "test-model")
        job = _pdf_job()
        service, repos, ai, final = await _run_with_ai(job, _AI_OK)
        original = dict(repos.processing.store[job.id].automation_extracted_data)
        # A later write carrying a DIFFERENT preserved payload must not replace
        # the first persisted value (COALESCE first-write-wins, mirrors the
        # repository; the real DB additionally enforces this via trigger).
        await repos.processing.advance_stage(
            job.id,
            target_stage="review",
            lock_token="token-later",
            automation_extracted_data={"activity": "someone-else", "quantity": 1},
        )
        after = repos.processing.store[job.id]
        assert after.automation_extracted_data == original


    async def test_deterministic_only_run_preserves_output_while_automation_null(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Decision (documented in the W1 report): deterministic-only runs ARE
        # eligible for preservation — the automatic pipeline produced the
        # output. The automation_* block stays NULL (no AI contributed), so
        # output-origin and AI-contribution remain distinguishable.
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "test-model")
        job = _csv_job()
        service, repos = _make_service(job)
        assert service.ai_extraction_engine is None
        final = await service.process_job(job, "token-w1")
        assert final.stage == "review"
        stored = repos.processing.store[job.id]
        assert stored.automation_extracted_data is not None
        assert stored.automation_extracted_data == stored.extracted_data
        assert stored.automation_provider is None
        assert stored.automation_model is None
        assert stored.automation_model_version is None

    async def test_failed_ai_blocked_run_creates_no_preserved_output(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A failed AI attempt that blocks (no persisted extraction) must NOT
        # create a preserved output (no fabricated machine output).
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.anthropic.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "claude-attempt")
        job = _pdf_job()
        failed = {
            "status": "error", "method": "ai", "model": None,
            "extracted_data": {}, "unresolved": [], "confidence": 0.0,
            "detail": "LLM API returned HTTP 500",
        }
        service, repos, ai, final = await _run_with_ai(job, failed)
        assert final.stage == "blocked"
        stored = repos.processing.store[job.id]
        assert stored.extracted_data is None
        assert stored.automation_extracted_data is None

    async def test_failed_ai_but_deterministic_proceeds_preserves_deterministic_output(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # AI attempt fails but deterministic already cleared the gate -> the job
        # proceeds deterministically; the preserved output is the deterministic
        # machine output and the automation block stays NULL (attempt !=
        # contribution).
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.anthropic.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "claude-attempt")
        # prefer_ai forces the candidate AI pass even though the deterministic
        # pass is already complete, so the failure envelope (error metadata
        # with the attempted model) is exercised on the deterministic-proceed
        # path.
        job = _pdf_job(metadata={"mime": "application/pdf", "prefer_ai": True})

        def _deterministic(content: bytes, filename: str, mime: str) -> dict:
            return {
                "status": "ok", "method": "pdf_text", "page_count": 1,
                "extracted_data": {
                    "activity": "Diesel", "quantity": 1250.0, "unit": "litres",
                    "date": "05/01/2025", "supplier": "Shell Fleet",
                },
                "unresolved": [], "confidence": 1.0,
            }

        failed = {
            "status": "error", "method": "ai", "model": None,
            "extracted_data": {}, "unresolved": [], "confidence": 0.0,
            "detail": "upstream timeout",
        }
        service, repos, ai, final = await _run_with_ai(
            job, failed, deterministic=_deterministic
        )
        assert final.stage == "review"
        stored = repos.processing.store[job.id]
        assert stored.automation_extracted_data is not None
        assert stored.automation_extracted_data == stored.extracted_data
        assert stored.automation_extracted_data["quantity"] == 1250.0
        assert stored.automation_provider is None
        assert stored.automation_model is None
        assert (stored.metadata or {}).get("ai_extraction", {}).get("status") == "error"

    async def test_idempotent_resume_does_not_rewrite_preserved_output(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A resume with an existing extraction marker advances without re-running
        # extraction, so the preserved original is never re-copied/overwritten.
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "test-model")
        original = {
            "activity": "Diesel", "quantity": 1250.0, "unit": "litres",
            "date": "2025-01-05", "supplier": "Shell Fleet",
        }
        job = _pdf_job(
            stage="extracting",
            status="processing",
            extracted_data=dict(original),
            automation_extracted_data=dict(original),
        )
        repos = _FakeRepos(job)
        repos.factors = _FakeFactors()
        repos.customer_factors = _FakeCustomerFactors()
        repos.notifications = _FakeNotifications()
        repos.manual_extraction = _FakeManualExtraction()
        service = AutomaticProcessingService(
            repos,
            matching_engine=_FakeMatchingEngine(),
            calculation_engine=_FakeCalculationEngine(),
        )
        final = await service.process_job(job, "token-w1")
        assert final.stage == "review"
        stored = repos.processing.store[job.id]
        assert stored.automation_extracted_data == original



# ---------------------------------------------------------------------------
# WS4 Gate 6 (workstream W4 / gap G6-D) — human correction + resume-marker +
# snapshot integrity on the durable job.
# ---------------------------------------------------------------------------


class TestGate6W4ResumeIntegrity:
    """Human-corrected data must re-enter validation/calculation; corrected data
    must never reuse the pre-correction snapshot; machine provenance survives."""

    ORIGINAL = {
        "activity": "Diesel", "quantity": 1250.0, "unit": "litres",
        "date": "2025-01-05", "supplier": "Shell Fleet",
    }
    MAPPED = {
        "factor_id": "factor-1", "factor_kind": "emission_factor",
        "mapping_confidence": 1.0, "activity": "Diesel", "unit": "litres",
        "methodology": "keyword_search", "stages_executed": ["keyword_search"],
    }

    def _corrected_job(self, extracted: dict) -> AutomaticProcessingJob:
        from datetime import datetime, timezone

        return AutomaticProcessingJob(
            id=str(uuid.uuid4()),
            organization_id=_ORG,
            file_name="invoice.pdf",
            file_url="uploads/org-1/invoice.pdf",
            file_type="PDF",
            stage="extracting",
            status="processing",
            metadata={"mime": "application/pdf"},
            source_item_id="item-1",
            extracted_data=extracted,
            mapped_data=dict(self.MAPPED),
            validation_result=None,  # cleared by G6-D invalidation
            calculation_snapshot_id=None,  # cleared by G6-D invalidation
            automation_provider="openai",
            automation_model="gpt-test",
            automation_extracted_data=dict(self.ORIGINAL),
            notified_at=datetime(2025, 1, 6, tzinfo=timezone.utc),
        )

    async def _resume(
        self, job: AutomaticProcessingJob, seed_old_snapshot: bool = False
    ):
        repos = _FakeRepos(job)
        repos.factors = _FakeFactors()
        repos.customer_factors = _FakeCustomerFactors()
        repos.notifications = _FakeNotifications()
        repos.manual_extraction = _FakeManualExtraction()
        if seed_old_snapshot:
            # History: the pre-correction machine snapshot under the legacy
            # (non-digest) request id — the G6-D failure mode.
            old_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{job.id}::calc::0"))
            repos.logs.snapshots[old_id] = {"id": "snap-OLD"}
        engine = _FakeCalculationEngine()
        service = AutomaticProcessingService(
            repos,
            matching_engine=_FakeMatchingEngine(),
            calculation_engine=engine,
        )
        final = await service.process_job(job, "token-w4")
        return service, repos, engine, final

    async def test_corrected_data_recalculates_new_snapshot_not_old(self) -> None:
        # Scenario 2: automation had already calculated (old snapshot exists);
        # a human correction follows. The corrected run must NOT reuse the old
        # snapshot via the request-id dedupe.
        corrected = dict(self.ORIGINAL)
        corrected["quantity"] = 900.0
        job = self._corrected_job(corrected)
        service, repos, engine, final = await self._resume(
            job, seed_old_snapshot=True
        )
        assert final.stage == "review", (
            f"stage={final.stage} blocked={repos.processing.marked_blocked}"
        )
        stored = repos.processing.store[job.id]
        assert engine.calls == 1  # recalculation actually ran
        assert stored.calculation_snapshot_id == "snap-1"  # NEW snapshot
        assert stored.calculation_snapshot_id != "snap-OLD"
        assert stored.extracted_data["quantity"] == 900.0  # corrected data
        # Machine provenance survives the correction.
        assert stored.automation_extracted_data == dict(self.ORIGINAL)
        assert stored.automation_provider == "openai"
        assert stored.automation_model == "gpt-test"

    async def test_unchanged_data_resume_reuses_existing_snapshot(self) -> None:
        # A crashed re-run over UNCHANGED data must still dedupe to the exact
        # snapshot (no duplicate calculation).
        from dataclasses import replace

        from services.automatic_processing import _calc_payload_digest

        job = self._corrected_job(dict(self.ORIGINAL))
        job = replace(job, stage="calculating")
        digest = _calc_payload_digest(job.extracted_data, job.mapped_data)
        new_id = str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"{job.id}::calc::0::c1::{digest}")
        )
        repos = _FakeRepos(job)
        repos.factors = _FakeFactors()
        repos.customer_factors = _FakeCustomerFactors()
        repos.notifications = _FakeNotifications()
        repos.manual_extraction = _FakeManualExtraction()
        repos.logs.snapshots[new_id] = {"id": "snap-X"}
        engine = _FakeCalculationEngine()
        service = AutomaticProcessingService(
            repos,
            matching_engine=_FakeMatchingEngine(),
            calculation_engine=engine,
        )
        final = await service.process_job(job, "token-w4")
        stored = repos.processing.store[job.id]
        assert final.stage == "review"
        assert engine.calls == 0
        assert stored.calculation_snapshot_id == "snap-X"


    async def test_multiple_corrections_remain_coherent(self) -> None:
        # Scenario 4: correction -> recalculation -> second correction. Each
        # correction produces a fresh snapshot; machine provenance survives.
        from dataclasses import replace

        first = dict(self.ORIGINAL)
        first["quantity"] = 900.0
        second = dict(self.ORIGINAL)
        second["supplier"] = "Corrected Supplier"
        second["quantity"] = 800.0
        job = self._corrected_job(first)
        service, repos, engine, final = await self._resume(job)
        assert final.stage == "review"
        assert engine.calls == 1
        first_snapshot = repos.processing.store[job.id].calculation_snapshot_id
        assert first_snapshot is not None
        # Second correction (markers cleared as G6-D invalidation would).
        current = repos.processing.store[job.id]
        again = replace(
            current,
            stage="extracting",
            status="processing",
            extracted_data=second,
            validation_result=None,
            calculation_snapshot_id=None,
        )
        repos.processing.store[job.id] = again
        final2 = await service.process_job(again, "token-w4b")
        assert final2.stage == "review"
        stored = repos.processing.store[job.id]
        assert engine.calls == 2
        assert stored.calculation_snapshot_id != first_snapshot
        assert stored.extracted_data["supplier"] == "Corrected Supplier"
        # Scenario 5 — machine provenance survives all corrections.
        assert stored.automation_extracted_data == dict(self.ORIGINAL)
        assert stored.automation_provider == "openai"
        assert stored.automation_model == "gpt-test"
        assert stored.automation_model_version is None

    async def test_blocked_before_calculation_reprocesses_after_correction(
        self,
    ) -> None:
        # Scenario 1: automation produced output but the job had not yet
        # calculated (validation/correction gate). A correction with cleared
        # markers re-enters validation -> calculation -> a fresh snapshot.
        corrected = dict(self.ORIGINAL)
        corrected["quantity"] = 950.0
        job = self._corrected_job(corrected)
        service, repos, engine, final = await self._resume(job)
        assert final.stage == "review"
        stored = repos.processing.store[job.id]
        assert engine.calls == 1
        assert stored.calculation_snapshot_id == "snap-1"
        assert stored.extracted_data["quantity"] == 950.0
        assert stored.automation_extracted_data == dict(self.ORIGINAL)

