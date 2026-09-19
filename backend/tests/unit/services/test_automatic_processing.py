"""Unit tests for the automatic-processing service (CL-56) with fake repos."""
from __future__ import annotations

import copy
import uuid
from collections.abc import Iterator, Sequence
from decimal import Decimal
from typing import Any, Optional

import pytest

from data.activity_clarifications import ActivityClarificationsRepository
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


class _ClarificationConn:
    """Capturing fake connection whose READ SEMANTICS mirror the real SQL.

    Two scripted sets, because the two reads have different semantics:

    * ``items`` — persisted extraction contexts, returned in call order (the
      ``manual_extraction_items`` lookup);
    * ``adjudications`` — ``activity_clarifications`` rows, filtered EXACTLY as the
      effective-read SQL does: only a row that is ``is_current`` **and** belongs to
      the organisation in ``$1`` is visible. A retired version or another tenant's
      row is therefore never handed to the service, which is the boundary being
      asserted — not a stub that would answer "yes" unconditionally.

    Writes are recorded but never performed, so ``writes`` proves the consumption
    path is read-only.
    """

    def __init__(self, *, items: Sequence[Any] = (), adjudications: Sequence[dict] = ()) -> None:
        self.items = list(items)
        self.adjudications = list(adjudications)
        self.queries: list[str] = []
        self.params: list[tuple] = []

    async def fetchrow(self, query: str, *args: Any) -> Any:
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        if "AND is_current" in query:
            return self._effective(args)
        return self.items.pop(0) if self.items else None

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        return []

    async def execute(self, query: str, *args: Any) -> str:
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        return "OK"

    def _effective(self, args: tuple) -> Optional[dict]:
        """Only a CURRENT row of the organisation in ``$1`` is visible."""
        org = str(args[0])
        for row in self.adjudications:
            if row.get("is_current") and str(row.get("organization_id")) == org:
                return row
        return None

    @property
    def writes(self) -> list[str]:
        return [q for q in self.queries if q.startswith(("INSERT", "UPDATE", "DELETE"))]


class _ClarificationAcquire:
    def __init__(self, conn: _ClarificationConn) -> None:
        self._conn = conn

    async def __aenter__(self) -> _ClarificationConn:
        return self._conn

    async def __aexit__(self, *exc: Any) -> bool:
        return False


class _ClarificationPool:
    def __init__(self, conn: _ClarificationConn) -> None:
        self._conn = conn

    def acquire(self) -> _ClarificationAcquire:
        return _ClarificationAcquire(self._conn)


class _FakeRepos:
    def __init__(
        self,
        job: AutomaticProcessingJob,
        *,
        adjudications: Sequence[dict] = (),
        evidence_rows: Sequence[Any] = (),
    ) -> None:
        self.processing = _FakeProcessing()
        self.processing.store[job.id] = job
        self.logs = _FakeLogs()
        self.organizations = _FakeOrganizations()
        # F-039-1 (063) F1 — the REAL clarifications repository over the capturing
        # fake connection, so the service's adjudication consumption executes the
        # genuine server-side derivation, tenant scoping and current-version read.
        self.clarification_conn = _ClarificationConn(
            items=evidence_rows, adjudications=adjudications
        )
        self.clarifications = ActivityClarificationsRepository(
            _ClarificationPool(self.clarification_conn)  # type: ignore[arg-type]
        )


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
    """Keyword matcher double.

    ``clarification_candidates`` supplies the SCRIPTED candidate window for the
    family-conflict gate. It defaults to empty, which reproduces the previous
    behaviour (no diversion) for every pre-existing test; the F-039-1 lifecycle
    tests pass the real 041/039 ``Waste`` window so the genuine diversion is
    reached. ``requests`` records every match request, so a test can prove WHICH
    text the policy produced.
    """

    def __init__(self, candidates: Sequence[Any] = ()) -> None:
        self._candidates = list(candidates)
        self.requests: list[Any] = []

    async def match(self, request):
        self.requests.append(request)
        return MatchResult(
            status="matched",
            factor=_FACTOR,
            confidence=1.0,
            methodology="keyword_search",
            stages_executed=("keyword_search",),
        )

    def clarification_candidates(self, request):
        return list(self._candidates)


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


def _make_service(
    job: AutomaticProcessingJob,
    audit_logger=None,
    *,
    candidates: Sequence[Any] = (),
    evidence_rows: Sequence[Any] = (),
    adjudications: Sequence[dict] = (),
):
    repos = _FakeRepos(
        job, adjudications=adjudications, evidence_rows=evidence_rows
    )
    repos.factors = _FakeFactors()
    repos.customer_factors = _FakeCustomerFactors()
    repos.notifications = _FakeNotifications()
    repos.manual_extraction = _FakeManualExtraction()
    service = AutomaticProcessingService(
        repos,
        matching_engine=_FakeMatchingEngine(candidates),
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


def _low_conf_deterministic(content: bytes, filename: str, mime: str, **_kw) -> dict:
    """Deterministic pass that only resolves ``activity`` (completeness 1/3)."""
    return {
        "status": "ok",
        "method": "pdf_text",
        "page_count": 1,
        "extracted_data": {"activity": "Diesel"},
        "unresolved": ["quantity", "unit"],
        "confidence": 0.3333,
    }


def _full_deterministic(content: bytes, filename: str, mime: str, **_kw) -> dict:
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

    def _fake_text(content: bytes, filename: str, mime: str, **_kw) -> dict:
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

        def _full_deterministic(content: bytes, filename: str, mime: str, **_kw) -> dict:
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

        def _deterministic(content: bytes, filename: str, mime: str, **_kw) -> dict:
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



# ---------------------------------------------------------------------------
# F-039-1 (063) — adjudication lifecycle: F1 consumption inside automatic mapping
# ---------------------------------------------------------------------------
#
# These tests drive the REAL service over the REAL clarifications repository (a
# scripted, capturing connection — no database is touched), the REAL clarification
# engine and the REAL factor-selection policy. Only the transport-adjacent
# dependencies are doubles.
#
# The activity is deliberately the bare ``Waste``: with the 041/039 candidate
# window it produces the treatment-vs-combustion family collision, which is the
# only shape that actually reaches the clarification diversion the lifecycle
# exists for. Diesel alone produces policy ambiguity and would not exercise the
# intended diversion branch.
#
# NOTE on authorization: the F1 consumption path is the durable worker path and
# carries no user context, so there is no authorization call to exercise at this
# layer — its boundary is the SERVER-DERIVED tenant + bounded context, asserted
# in A8. Consultant/client authorization lives at the HTTP boundary and is
# exercised against the real ``ensure_processing_org_access`` in the read-endpoint
# tests (Parts B/C).

_ORG_B = "99999999-9999-4999-8999-999999999999"
_ITEM = "22222222-2222-4222-8222-222222222222"
_BATCH = "33333333-3333-4333-8333-333333333333"
_FILE = "44444444-4444-4444-8444-444444444444"


def _signature(
    activity: str = "Waste",
    unit: Optional[str] = "tonnes",
    scope: Optional[str] = "Scope 3",
) -> str:
    """The D-F039-1-I signature, produced by the repository's own helper."""
    return ActivityClarificationsRepository.evidence_signature(activity, unit, scope)


def _waste_candidates() -> list:
    """The 041/039 ``Waste`` window: three treatment routes + a waste-oils fuel."""
    def _f(
        name: str,
        *,
        unit: str = "tonnes",
        scope: str = "Scope 3",
        value: str = "1.26338",
        fid: str = "f-1",
    ) -> EmissionFactor:
        text = f"{name} [{unit}]" if "[" not in name else name
        return EmissionFactor(
            id=fid, reporting_year=2025, activity_type=text,
            co2e_multiplier=Decimal(value), unit=unit, scope=scope,
            factor_source="DEFRA-DESNZ", factor_set="DEFRA-2025", country="GB",
            provider_key="DEFRA-DESNZ", natural_key=("2025", text, "GB", unit, scope),
        )

    return [
        _f("Waste disposal > Construction > Aggregates - Landfill (kg CO2e)", fid="lf"),
        _f("Waste disposal > Construction > Aggregates - Open-loop (kg CO2e)",
           value="1.00835", fid="ol"),
        _f("Waste disposal > Construction > Aggregates - Incineration with Energy "
           "Recovery (kg CO2e)", value="0.02106", fid="inc"),
        _f("Fuels > Liquid fuels > Waste oils (kg CO2e)", scope="Scope 1",
           value="3219.37916", fid="oils"),
    ]




def _waste_item_row(
    *,
    organization_id: str = _ORG,
    unit: str = "tonnes",
    scope: str = "Scope 3",
    activity: str = "Waste",
) -> dict:
    """The PERSISTED extraction context the server derives evidence and tenant from."""
    return {
        "item_key": _ITEM,
        "batch_key": _BATCH,
        "source_file_id": _FILE,
        "source_file_name": "waste.csv",
        "organization_id": organization_id,
        "extracted_data": {
            "supplier": "Acme Waste Ltd",
            "date": "05/01/2025",
            "line_items": [
                {
                    "activity": activity,
                    "source_line": activity,
                    "unit": unit,
                    "scope": scope,
                    "quantity": 12.5,
                }
            ],
        },
    }


def _waste_job(**overrides: Any) -> AutomaticProcessingJob:
    """A job resuming at mapping with one bare-``Waste`` line (the F-039-1 shape)."""
    base = dict(
        stage="extracting",
        status="processing",
        source_item_id=_ITEM,
        extracted_data={
            "supplier": "Acme Waste Ltd",
            "date": "05/01/2025",
            "line_items": [
                {
                    "activity": "Waste",
                    "source_line": "Waste",
                    "unit": "tonnes",
                    "scope": "Scope 3",
                    "quantity": 12.5,
                }
            ],
        },
    )
    base.update(overrides)
    return _csv_job(**base)


def _adjudication_row(
    *,
    clarification: str = "Landfill",
    evidence_signature: Optional[str] = None,
    selected_factor_id: Optional[str] = "lf",
    organization_id: str = _ORG,
    is_current: bool = True,
    version: int = 1,
    **over: Any,
) -> dict:
    """One persisted ``activity_clarifications`` version, as the repository reads it."""
    row = {
        "id": f"row-v{version}",
        "adjudication_id": "adj-1",
        "organization_id": organization_id,
        "activity_key": _ITEM,
        "original_activity": "Waste",
        "clarification": clarification,
        "clarification_type": "semantic_activity",
        "policy_input": f"Waste {clarification}",
        "outcome_status": "selected",
        "selected_factor_id": selected_factor_id,
        "version": version,
        "is_current": is_current,
        "effective_context_key": _ITEM,
        "evidence_signature": evidence_signature,
        "re_evaluation_required": False,
    }
    row.update(over)
    return row


def _waste_service(
    job: AutomaticProcessingJob,
    *,
    adjudications: Sequence[dict] = (),
    item_row: Optional[dict] = None,
):
    """Service + repos wired for the bare-``Waste`` diversion with scripted rows."""
    return _make_service(
        job,
        candidates=_waste_candidates(),
        evidence_rows=[_waste_item_row() if item_row is None else item_row],
        adjudications=list(adjudications),
    )


def _matched_activities(service: AutomaticProcessingService) -> list[str]:
    """Every activity text the matching engine was asked to match, in order."""
    return [str(request.activity) for request in service._matching_engine.requests]


class TestAdjudicationLifecycleConsumption:
    """F-039-1 (063) A1–A8 — the F1 consumption contract at the service level."""

    # -- A1: no adjudication -> the existing diversion stays in force ---------
    async def test_a1_bare_waste_without_an_adjudication_still_diverts(self) -> None:
        job = _waste_job()
        service, repos = _waste_service(job)

        final = await service.process_job(job, "token-a1")

        assert final.stage == "blocked"
        assert final.mapped_data is None          # nothing mapped -> no factor guessed
        reason = repos.processing.marked_blocked[-1]
        assert "clarification required for 'Waste'" in reason
        # The reason is the ENGINE's own family-conflict explanation, so the
        # diversion came from the real assessment rather than a helper stub.
        assert "treatment/material handling" in reason
        assert "factor-1" not in reason
        # The consumption path really was entered, asking for the CURRENT row of
        # the bounded context.
        conn = repos.clarification_conn
        effective = [q for q in conn.queries if "AND is_current" in q]
        assert len(effective) == 1
        assert "organization_id = $1" in effective[0]
        assert "effective_context_key = $2" in effective[0]
        assert conn.writes == []

    # -- A2: compatible adjudication -> consumed, processing proceeds ---------
    async def test_a2_a_compatible_adjudication_is_consumed_and_processing_proceeds(
        self,
    ) -> None:
        job = _waste_job()
        service, repos = _waste_service(
            job, adjudications=[_adjudication_row(evidence_signature=_signature())]
        )

        final = await service.process_job(job, "token-a2")

        assert final.stage == "review"
        assert repos.processing.marked_blocked == []
        mapped = final.mapped_data["line_items"][0]
        assert mapped["status"] == "mapped"
        assert mapped["factor_id"] == _FACTOR.id
        # The stored SEMANTIC clarification was re-entered into the existing policy
        # (the policy's own text is what the matcher was asked for) …
        assert _matched_activities(service) == ["Waste", "Waste Landfill"]
        # … and the resulting match — not the stored factor id — is what was mapped.
        assert mapped["factor_id"] != "lf"
        # The lookup carried the full bounded context, never the activity text alone.
        assert repos.clarification_conn.params[1] == (_ORG, _ITEM, _ITEM, "Waste")

    # -- A3: the stored selected_factor_id can never bypass the policy --------
    async def test_a3_a_stored_selected_factor_id_cannot_bypass_the_policy(
        self,
    ) -> None:
        job = _waste_job()
        service, repos = _waste_service(
            job,
            adjudications=[
                _adjudication_row(
                    clarification="Landfill",   # the policy resolves this to "lf"
                    selected_factor_id="ol",    # deliberately a DIFFERENT factor
                    evidence_signature=_signature(),
                )
            ],
        )

        final = await service.process_job(job, "token-a3")

        assert final.stage == "review"
        mapped = final.mapped_data["line_items"][0]
        assert mapped["factor_id"] == _FACTOR.id
        # Neither the stored id nor the policy's own winner is taken as an override:
        # the mapped factor is what the matching engine returned for the POLICY INPUT.
        assert mapped["factor_id"] not in {"ol", "lf"}
        assert _matched_activities(service)[-1] == "Waste Landfill"
        # No mapping entry anywhere carries the stored factor id.
        assert all(
            entry.get("factor_id") not in {"ol", "lf"}
            for entry in final.mapped_data["line_items"]
        )


    # -- A4: changed authoritative evidence -> no silent reuse ----------------
    async def test_a4_changed_evidence_signature_prevents_silent_reuse(self) -> None:
        job = _waste_job()
        historical = _adjudication_row(evidence_signature=_signature())  # stored: tonnes
        before = copy.deepcopy(historical)
        assert _signature() != _signature(unit="litres")
        service, repos = _waste_service(
            job,
            adjudications=[historical],
            item_row=_waste_item_row(unit="litres"),  # persisted evidence changed
        )

        final = await service.process_job(job, "token-a4")

        assert final.stage == "blocked"
        assert final.mapped_data is None
        assert "clarification required for 'Waste'" in repos.processing.marked_blocked[-1]
        # The historical adjudication is untouched, nothing was written, and the
        # policy was never re-entered with the stale semantics.
        assert historical == before
        assert repos.clarification_conn.writes == []
        assert _matched_activities(service) == ["Waste"]

    # -- A5: no stored signature -> no proof of compatibility -> no reuse ----
    async def test_a5_a_row_without_an_evidence_signature_is_not_silently_reused(
        self,
    ) -> None:
        job = _waste_job()
        legacy = _adjudication_row(evidence_signature=None)
        before = copy.deepcopy(legacy)
        service, repos = _waste_service(job, adjudications=[legacy])

        final = await service.process_job(job, "token-a5")

        assert final.stage == "blocked"
        assert final.mapped_data is None
        assert "clarification required for 'Waste'" in repos.processing.marked_blocked[-1]
        assert legacy == before
        assert repos.clarification_conn.writes == []
        assert _matched_activities(service) == ["Waste"]

    # -- A6: the policy abstains again -> unresolved, no fallback ------------
    async def test_a6_a_still_ambiguous_adjudication_leaves_the_activity_unresolved(
        self,
    ) -> None:
        job = _waste_job()
        service, repos = _waste_service(
            job,
            adjudications=[
                _adjudication_row(
                    clarification="Waste disposal",  # the policy: still ambiguous
                    selected_factor_id="lf",         # must NOT be used as a fallback
                    evidence_signature=_signature(),
                )
            ],
        )

        final = await service.process_job(job, "token-a6")

        assert final.stage == "blocked"
        assert final.mapped_data is None
        reason = repos.processing.marked_blocked[-1]
        assert "clarification required for 'Waste'" in reason
        assert "lf" not in reason
        # The policy was re-run and abstained, so the matcher was never asked to
        # realise the adjudication's factor id.
        assert _matched_activities(service) == ["Waste"]
        assert repos.clarification_conn.writes == []


    # -- A7: versioning — only the current version is consumed ---------------
    async def test_a7_only_the_current_version_is_consumed(self) -> None:
        job = _waste_job()
        v1 = _adjudication_row(
            clarification="Incineration", version=1, is_current=False,
            evidence_signature=_signature(),
        )
        v2 = _adjudication_row(
            clarification="Landfill", version=2, is_current=True,
            evidence_signature=_signature(),
        )
        snapshot = (copy.deepcopy(v1), copy.deepcopy(v2))
        service, repos = _waste_service(job, adjudications=[v1, v2])

        final = await service.process_job(job, "token-a7")

        assert final.stage == "review"
        # v2's clarification — not v1's — is what reached the existing policy.
        assert _matched_activities(service) == ["Waste", "Waste Landfill"]
        assert "Waste Incineration" not in _matched_activities(service)
        # The immutable history is still intact and unchanged …
        assert (v1, v2) == snapshot
        assert [row["version"] for row in repos.clarification_conn.adjudications] == [1, 2]
        # … and consumption wrote nothing at all (no silent overwrite/supersede).
        assert repos.clarification_conn.writes == []
        # The effective read is the CURRENT-version predicate.
        assert "AND is_current" in repos.clarification_conn.queries[1]

    async def test_a7_a_retired_version_alone_is_never_consumed(self) -> None:
        job = _waste_job()
        service, repos = _waste_service(
            job,
            adjudications=[
                _adjudication_row(
                    clarification="Landfill", version=1, is_current=False,
                    evidence_signature=_signature(),
                )
            ],
        )

        final = await service.process_job(job, "token-a7b")

        assert final.stage == "blocked"
        assert final.mapped_data is None
        assert "clarification required for 'Waste'" in repos.processing.marked_blocked[-1]
        assert _matched_activities(service) == ["Waste"]
        assert repos.clarification_conn.writes == []

    # -- A8: bounded context + tenant isolation ------------------------------
    async def test_a8_the_lookup_carries_the_resolved_tenant_and_bounded_context(
        self,
    ) -> None:
        job = _waste_job()
        service, repos = _waste_service(
            job, adjudications=[_adjudication_row(evidence_signature=_signature())]
        )

        final = await service.process_job(job, "token-a8")

        assert final.stage == "review"          # A consumes A's own adjudication
        conn = repos.clarification_conn
        assert conn.params[1] == (_ORG, _ITEM, _ITEM, "Waste")
        assert "organization_id = $1" in conn.queries[1]
        for clause in ("effective_context_key = $2", "activity_key = $3",
                       "original_activity = $4", "AND is_current"):
            assert clause in conn.queries[1]

    async def test_a8_another_tenants_adjudication_is_never_consumed(self) -> None:
        job = _waste_job()                       # organisation A
        foreign = _adjudication_row(
            organization_id=_ORG_B, evidence_signature=_signature()
        )
        before = copy.deepcopy(foreign)
        service, repos = _waste_service(job, adjudications=[foreign])

        final = await service.process_job(job, "token-a8b")

        assert final.stage == "blocked"          # the diversion, not B's answer
        assert final.mapped_data is None
        assert "clarification required for 'Waste'" in repos.processing.marked_blocked[-1]
        assert foreign == before                 # B's row was not touched
        assert repos.clarification_conn.writes == []
        assert _matched_activities(service) == ["Waste"]

    async def test_a8_the_job_cannot_steer_the_tenant_the_lookup_is_scoped_to(
        self,
    ) -> None:
        """The look-up tenant is the PERSISTED item's, never the job's/client's."""
        job = _waste_job(organization_id=_ORG)   # the job claims organisation A
        service, repos = _waste_service(
            job,
            item_row=_waste_item_row(organization_id=_ORG_B),   # the item is B's
            adjudications=[_adjudication_row(organization_id=_ORG)],  # A's row
        )

        final = await service.process_job(job, "token-a8c")

        assert repos.clarification_conn.params[1][0] == _ORG_B
        assert final.stage == "blocked"
        assert final.mapped_data is None
        assert "clarification required for 'Waste'" in repos.processing.marked_blocked[-1]
        assert _matched_activities(service) == ["Waste"]

