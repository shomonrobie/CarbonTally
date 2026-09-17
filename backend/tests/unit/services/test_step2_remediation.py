"""Step 2 functional-remediation unit tests (WS-A D1 + WS-B P1).

Locks the Step 2 remediation contract:

* **D1 / WS-A** — a *partial* extraction is persisted **before** the completeness
  gate blocks the job (the partial result is no longer discarded), the gate's
  decision is unchanged, nothing is fabricated, and the queue job's resume
  marker is never written on the blocked path (so a retry still re-extracts and
  cannot bypass the gate).
* **P1 §7.3 / WS-B** — document-level adjudication replaced the positional,
  lossy deterministic/AI merge; the AI candidate is retained as bounded evidence
  and a disagreement is recorded, never blended.
* **P1-D2 / WS-B B5** — the bounded `block_reason` from the extractor survives
  into the job's blocked reason.
* **B3 / WS-B** — the shared fidelity hook is wired for the IMAGE path too.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

import pytest

from domain.automatic_processing import AutomaticProcessingJob
from services.automatic_processing import (
    AutomaticProcessingService,
    _adjudication_record,
    _ai_candidate_evidence,
    _merge_extraction_candidates,
)

_ORG = "11111111-1111-4111-8111-111111111111"
_SYSTEM_ACTOR = "00000000-0000-0000-0000-000000000000"

#: A realistic partial result: the extractor resolved everything except the two
#: fields production actually reported as unresolved.
_PARTIAL = {
    "activity": "Water supply",
    "supplier": "Severn Trent",
    "date": "05/01/2025",
    "unit": None,
    "quantity": None,
}


def _job(**overrides: Any) -> AutomaticProcessingJob:
    base: dict[str, Any] = dict(
        id=str(uuid.uuid4()),
        organization_id=_ORG,
        file_name="invoice.pdf",
        file_url="uploads/org-1/invoice.pdf",
        file_type="PDF",
        stage="extracting",
        status="processing",
        metadata={"mime": "application/pdf"},
        source_item_id="item-1",
    )
    base.update(overrides)
    return AutomaticProcessingJob(**base)


class _FakeManualExtraction:
    def __init__(self) -> None:
        self.saves: list[dict[str, Any]] = []

    async def save_extracted_data(
        self, item_id, extracted_data, extracted_by, extraction_method=None
    ):
        self.saves.append(
            {
                "item_id": item_id,
                "extracted_data": extracted_data,
                "extracted_by": extracted_by,
                "extraction_method": extraction_method,
            }
        )
        return None

    async def save_mapped_data(self, *a: Any, **k: Any):
        return None

    async def set_item_status(self, *a: Any, **k: Any):
        return None

    async def save_calculation(self, *a: Any, **k: Any):
        return None


class _FakeProcessing:
    def __init__(self) -> None:
        self.blocked: list[dict[str, Any]] = []
        self.advances: list[dict[str, Any]] = []

    async def mark_blocked(self, job_id, *, reason, lock_token, **kw: Any):
        self.blocked.append({"job_id": job_id, "reason": reason, **kw})
        return None

    async def advance_stage(self, job_id, **kw: Any):
        self.advances.append(kw)
        return None

    async def mark_failed(self, job_id, *, last_error, lock_token, **kw: Any):
        return None

    async def release_lock(self, job_id, lock_token) -> bool:
        return True

    async def mark_notified(self, job_id):
        return None


class _Repos:
    def __init__(self) -> None:
        self.processing = _FakeProcessing()
        self.manual_extraction = _FakeManualExtraction()
        self.logs = SimpleNamespace(snapshots={})
        self.organizations = SimpleNamespace(get_members=lambda *_a, **_k: [])
        self.factors = None
        self.customer_factors = None


def _service(monkeypatch: pytest.MonkeyPatch, result: dict):
    """A service whose deterministic extractor always returns ``result``."""
    import services.automatic_processing as svc

    calls: list[bytes] = []

    def _fake_extract_document(content: bytes, filename: str, mime: str) -> dict:
        calls.append(content)
        return result

    monkeypatch.setattr(svc, "extract_document", _fake_extract_document)
    repos = _Repos()
    service = AutomaticProcessingService(repos)
    return service, repos, calls


async def _run_extract(service, job) -> str:
    service._content_cache[job.id] = b"content-bytes"
    return await service._extract(job, "token-1")


# ---------------------------------------------------------------------------
# WS-A (D1) — partial extraction persistence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_partial_extraction_is_persisted_before_blocking(monkeypatch):
    service, repos, _calls = _service(
        monkeypatch,
        {
            "status": "ok",
            "method": "pdf_text",
            "page_count": 1,
            "extracted_data": dict(_PARTIAL),
            "unresolved": ["quantity", "unit"],
            "confidence": 0.33,
        },
    )
    job = _job()
    outcome = await _run_extract(service, job)

    assert outcome == "blocked"
    # 1. the gate still blocks with the same semantics and reason text
    assert len(repos.processing.blocked) == 1
    block = repos.processing.blocked[0]
    assert "0.33" in block["reason"] and "0.50" in block["reason"]
    assert "quantity, unit" in block["reason"]

    # 2. the genuinely extracted data IS persisted to the manual-extraction item,
    #    byte-identical to what the extractor produced (nothing invented)
    assert len(repos.manual_extraction.saves) == 1
    saved = repos.manual_extraction.saves[0]
    assert saved["extracted_data"] == _PARTIAL
    assert saved["item_id"] == "item-1"
    assert saved["extracted_by"] == _SYSTEM_ACTOR
    assert saved["extraction_method"] == "pdf_text"
    assert saved["extracted_data"]["quantity"] is None

    # 3. the job carries a machine-readable partial-extraction record
    record = block["metadata"]["partial_extraction"]
    assert record["unresolved"] == ["quantity", "unit"]
    assert record["confidence"] == 0.33
    assert record["method"] == "pdf_text"
    assert record["status"] == "partial"
    assert record["item_persisted"] is True
    assert record["fields_present"] == ["activity", "date", "supplier"]

    # 4. the queue job's resume marker is NOT written → no gate bypass on retry
    assert repos.processing.advances == []


@pytest.mark.asyncio
async def test_complete_extraction_path_is_unchanged(monkeypatch):
    complete = {
        "activity": "Water supply",
        "quantity": 1200,
        "unit": "m3",
        "supplier": "Severn Trent",
        "date": "05/01/2025",
    }
    service, repos, _calls = _service(
        monkeypatch,
        {
            "status": "ok",
            "method": "pdf_text",
            "page_count": 1,
            "extracted_data": dict(complete),
            "unresolved": [],
            "confidence": 1.0,
        },
    )
    outcome = await _run_extract(service, _job())

    assert outcome == "mapping"
    assert repos.processing.blocked == []
    assert len(repos.processing.advances) == 1
    advance = repos.processing.advances[0]
    assert advance["extracted_data"] == complete
    assert advance["target_stage"] == "mapping"
    # the success path still syncs the item exactly once
    assert len(repos.manual_extraction.saves) == 1


@pytest.mark.asyncio
async def test_blocked_job_re_extracts_on_retry_so_the_gate_cannot_be_bypassed(monkeypatch):
    service, repos, calls = _service(
        monkeypatch,
        {
            "status": "ok",
            "method": "pdf_text",
            "page_count": 1,
            "extracted_data": dict(_PARTIAL),
            "unresolved": ["quantity", "unit"],
            "confidence": 0.33,
        },
    )
    job = _job()
    assert await _run_extract(service, job) == "blocked"
    # A later resume must run extraction again (no resume marker was written for
    # the queue job), so the completeness gate is re-evaluated rather than skipped.
    assert await _run_extract(service, job) == "blocked"
    assert len(calls) == 2
    assert repos.processing.advances == []


@pytest.mark.asyncio
async def test_multi_line_unresolved_keeps_the_true_block_reason(monkeypatch):
    service, repos, _calls = _service(
        monkeypatch,
        {
            "status": "multi_line_unresolved",
            "method": "pdf_text",
            "page_count": 1,
            "extracted_data": dict(_PARTIAL),
            "unresolved": ["quantity", "unit"],
            "confidence": 0.33,
            "coverage": {"mode": "enabled", "candidate_lines": 3},
            "block_reason": (
                "This document appears to contain multiple activity lines "
                "(3 detected) but automatic extraction could not reliably separate them."
            ),
        },
    )
    outcome = await _run_extract(service, _job())

    assert outcome == "blocked"
    reason = repos.processing.blocked[0]["reason"]
    # P1-D2 — the bounded, truthful reason is preserved, not replaced by the
    # generic "no usable data" fallback.
    assert "multiple activity lines" in reason
    assert "no usable data" not in reason
    # the partial payload is still persisted for the human reviewer
    assert repos.manual_extraction.saves[0]["extracted_data"] == _PARTIAL
    record = repos.processing.blocked[0]["metadata"]["partial_extraction"]
    assert record["status"] == "multi_line_unresolved"
    assert record["coverage"] == {"mode": "enabled", "candidate_lines": 3}


@pytest.mark.asyncio
async def test_ai_failure_still_persists_the_deterministic_partial(monkeypatch):
    class _FailingAi:
        async def extract_candidate(self, *a: Any, **k: Any):
            raise RuntimeError("provider unavailable")

    service, repos, _calls = _service(
        monkeypatch,
        {
            "status": "ok",
            "method": "pdf_text",
            "page_count": 1,
            "extracted_data": dict(_PARTIAL),
            "unresolved": ["quantity", "unit"],
            "confidence": 0.33,
        },
    )
    service._ai_extraction_engine = _FailingAi()
    job = _job(metadata={"mime": "application/pdf", "ai_required": True})
    outcome = await _run_extract(service, job)

    assert outcome == "blocked"
    reason = repos.processing.blocked[0]["reason"]
    assert "AI extraction failed" in reason
    record = repos.processing.blocked[0]["metadata"]["partial_extraction"]
    assert record["ai_status"] == "error"
    assert repos.manual_extraction.saves[0]["extracted_data"] == _PARTIAL


# ---------------------------------------------------------------------------
# WS-B (P1 §7.3) — document-level adjudication, no positional blending
# ---------------------------------------------------------------------------


def test_adjudication_never_blends_positionally():
    deterministic = {
        "line_items": [
            {"activity": "Diesel", "quantity": 1250.0, "unit": "litres"},
            {"activity": "Petrol"},
        ]
    }
    ai = {
        "line_items": [
            {"quantity": 1, "unit": "kWh"},  # contradicts deterministic line 1
            {"quantity": 300, "unit": "litres"},
        ]
    }
    merged = _merge_extraction_candidates(deterministic, ai)

    # The deterministic candidate is accepted WHOLE: no AI value is copied into
    # any line, even where the deterministic line had a gap.
    assert merged == deterministic
    assert merged["line_items"][1] == {"activity": "Petrol"}

    record = _adjudication_record(deterministic, ai, merged)
    assert record["positional_blending"] is False
    assert record["accepted_candidate"] == "deterministic"
    assert record["deterministic_line_items"] == 2
    assert record["ai_line_items"] == 2
    assert record["divergent"] is True


def test_adjudication_flags_differing_line_counts_as_divergent():
    deterministic = {"line_items": [{"activity": "Diesel"}]}
    ai = {"line_items": [{"activity": "Diesel"}, {"activity": "Petrol"}]}
    merged = _merge_extraction_candidates(deterministic, ai)
    record = _adjudication_record(deterministic, ai, merged)
    assert record["divergent"] is True
    assert record["accepted_line_items"] == 1


def test_adjudication_accepts_the_ai_candidate_when_there_is_no_deterministic_table():
    ai = {"line_items": [{"activity": "Diesel", "quantity": 1250, "unit": "litres"}]}
    merged = _merge_extraction_candidates({}, ai)
    assert merged == ai
    record = _adjudication_record({}, ai, merged)
    assert record["accepted_candidate"] == "ai"
    # No deterministic candidate exists, so there is nothing to disagree with.
    assert record["divergent"] is False


def test_adjudication_keeps_the_scalar_gap_fill_unchanged():
    deterministic = {"activity": "Diesel"}
    ai = {"quantity": 1250, "unit": "litres", "supplier": "Shell"}
    merged = _merge_extraction_candidates(deterministic, ai)
    assert merged == {
        "activity": "Diesel",
        "quantity": 1250,
        "unit": "litres",
        "supplier": "Shell",
    }


def test_ai_candidate_is_retained_as_bounded_evidence():
    small = {"activity": "Diesel", "quantity": 1250, "unit": "litres"}
    evidence = _ai_candidate_evidence(small)
    assert evidence["retained"] is True
    assert evidence["payload"] == small
    assert evidence["fields_present"] == ["activity", "quantity", "unit"]

    huge = {"line_items": [{"activity": "x" * 500} for _ in range(40)]}
    big_evidence = _ai_candidate_evidence(huge)
    assert big_evidence["retained"] is False
    assert "exceeded" in big_evidence["retention_note"]
    assert big_evidence["line_items"] == 40


# ---------------------------------------------------------------------------
# WS-B (B3) — the IMAGE-path hook lives in tests/unit/services/test_p1_image_path.py
# ---------------------------------------------------------------------------



