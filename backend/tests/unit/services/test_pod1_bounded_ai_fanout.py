"""Step 2C / POD-1 — bounded automatic AI fan-out.

PO decision A: limited automatic additional AI calls are authorised when the
deterministic/P1 pass cannot establish sufficient document structure — with hard
limits, no recursion, no fabrication, separate deterministic/AI evidence and
document-level (never positional) adjudication.

These tests record the ACTUAL call counts.
"""
from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace

import pytest

import services.automatic_processing as auto_mod
from domain.automatic_processing import AutomaticProcessingJob
from services import extraction_fidelity as p1
from services.automatic_processing import AutomaticProcessingService

_ORG = "11111111-1111-4111-8111-111111111111"

#: A page body that is multi-line, numeric and unit-bearing (so the document is
#: multi-line-suspect) and long enough that the total text exceeds the AI clip.
_PAGE_BODY = "\n".join(f"Diesel {i} 1,{i:03d} litres {i}.00" for i in range(1, 61))
_FILLER = "Site note line without any structured figures " * 600


def _long_text(pages: int = 2) -> str:
    parts = [f"[page {index}]\n{_PAGE_BODY}\n{_FILLER}" for index in range(1, pages + 1)]
    return "\n".join(parts)


def _short_text() -> str:
    return "Diesel 1,500 litres 1,800.00\nUnleaded petrol 900 litres 1,200.00"


def _job() -> AutomaticProcessingJob:
    return AutomaticProcessingJob(
        id=str(uuid.uuid4()),
        organization_id=_ORG,
        file_name="invoice.pdf",
        file_url="uploads/org-1/invoice.pdf",
        file_type="PDF",
        stage="enqueued",
        status="pending",
        metadata={"mime": "application/pdf"},
        source_item_id="item-pod1",
    )


class _CancellingEngine:
    """Engine that records every call and replays scripted outcomes per call."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0
        self.texts: list[str] = []

    async def extract_candidate(self, text: str, *, filename: str = "", method: str = "pdf") -> dict:
        self.calls += 1
        self.texts.append(text)
        index = self.calls - 1
        outcome = self.outcomes[index] if index < len(self.outcomes) else self.outcomes[-1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _ok(payload: dict, page_model: str = "test-model") -> dict:
    return {
        "status": "ok",
        "method": "ai:pdf_text",
        "model": page_model,
        "extracted_data": payload,
        "unresolved": [],
        "confidence": 0.8,
    }


def _service(engine) -> AutomaticProcessingService:
    return AutomaticProcessingService(SimpleNamespace(), ai_extraction_engine=engine)


@pytest.mark.asyncio
async def test_one_recorded_call_per_page_when_the_plan_permits_fan_out():
    engine = _CancellingEngine([_ok({"quantity": 1250}), _ok({"unit": "litres"})])
    service = _service(engine)

    candidates, fanout = await service._bounded_ai_candidates(
        _long_text(2), filename="invoice.pdf", method="pdf_text"
    )

    assert engine.calls == 2                      # one call per page, no extras
    assert fanout["per_page_ai"] is True
    assert fanout["pages_available"] == 2
    assert fanout["pages_attempted"] == 2
    assert fanout["calls_made"] == 2
    assert fanout["plan"]["page_cap"] == p1.PAGE_CAP
    assert [c["page_index"] for c in candidates] == [1, 2]
    # each page's text is bounded by the per-call clip
    assert all(len(text) <= auto_mod.AI_FANOUT_PAGE_CLIP_CHARS for text in engine.texts)


@pytest.mark.asyncio
async def test_no_unnecessary_fan_out_when_the_text_layer_is_not_clipped():
    engine = _CancellingEngine([_ok({"quantity": 1250})])
    service = _service(engine)

    candidates, fanout = await service._bounded_ai_candidates(
        _short_text(), filename="invoice.pdf", method="pdf_text"
    )

    assert engine.calls == 1                      # exactly the single legacy pass
    assert fanout["per_page_ai"] is False
    assert fanout["calls_made"] == 1
    assert fanout["pages_attempted"] == 1
    assert [c["page_index"] for c in candidates] == [0]


@pytest.mark.asyncio
async def test_the_call_cap_is_never_exceeded(monkeypatch):
    monkeypatch.setattr(auto_mod, "AI_FANOUT_MAX_CALLS", 2)
    engine = _CancellingEngine([_ok({"quantity": 1})])
    service = _service(engine)

    _candidates, fanout = await service._bounded_ai_candidates(
        _long_text(5), filename="invoice.pdf", method="pdf_text"
    )

    assert engine.calls == 2                      # hard cap honoured
    assert fanout["calls_made"] == 2
    assert fanout["max_calls"] == 2
    skipped = [entry for entry in fanout["per_page"] if entry["status"] == "skipped"]
    assert skipped and "call cap" in skipped[0]["detail"]


@pytest.mark.asyncio
async def test_an_engine_error_is_reported_once_and_never_retried(monkeypatch):
    engine = _CancellingEngine([
        {"status": "error", "method": "ai", "detail": "LLM API returned HTTP 500"}
    ])
    service = _service(engine)
    _patch_text_layer(monkeypatch, _long_text(2))
    deterministic = {"activity": "Diesel", "amount": 85.21}

    meta, extracted, confidence, method = await service._run_ai_candidate(
        _job(), b"x" * 100, deterministic, 0.33, "pdf_text"
    )

    # one call per page, and NOT a retry: an engine answer is never re-requested
    # (a retry would make this 4 calls for two pages).
    assert engine.calls == 2
    assert meta["status"] == "error"
    assert "HTTP 500" in meta["detail"]           # truthful detail preserved
    assert extracted == deterministic             # deterministic evidence unchanged
    assert method == "pdf_text"
    assert confidence == 0.33
    assert meta["ai_fanout"]["first_failure"]["detail"].startswith("LLM API")


def _patch_text_layer(monkeypatch, text: str) -> None:
    monkeypatch.setattr(
        auto_mod,
        "extract_document_text",
        lambda content, filename, mime, **_kw: {
            "status": "ok",
            "ftype": "PDF",
            "text": text,
            "method": "pdf_text",
            "page_count": 2,
        },
    )


@pytest.mark.asyncio
async def test_a_timeout_is_retried_once_then_falls_back(monkeypatch):
    monkeypatch.setattr(auto_mod, "AI_FANOUT_TIMEOUT_S", 0.01)
    engine = _CancellingEngine([asyncio.TimeoutError(), asyncio.TimeoutError()])
    service = _service(engine)
    _patch_text_layer(monkeypatch, _long_text(2))
    deterministic = {"activity": "Diesel"}

    meta, extracted, _confidence, method = await service._run_ai_candidate(
        _job(), b"x" * 100, deterministic, 0.33, "pdf_text"
    )

    # bounded retry: the first page is attempted twice (1 + 1 retry), then the
    # remaining pages are still attempted within the global cap.
    assert engine.calls == 4
    assert engine.calls <= auto_mod.AI_FANOUT_MAX_CALLS
    assert meta["status"] == "error"
    assert "exceeded" in meta["detail"]
    assert extracted == deterministic
    assert method == "pdf_text"
    assert [entry["status"] for entry in meta["ai_fanout"]["per_page"]] == [
        "timeout",
        "timeout",
        "timeout",
        "timeout",
    ]


@pytest.mark.asyncio
async def test_a_malformed_ai_response_fabricates_nothing(monkeypatch):
    engine = _CancellingEngine([{"status": "ok"}])   # no extracted_data at all
    service = _service(engine)
    _patch_text_layer(monkeypatch, _long_text(2))
    deterministic = {"activity": "Diesel", "amount": 85.21}

    meta, extracted, _confidence, _method = await service._run_ai_candidate(
        _job(), b"x" * 100, deterministic, 0.33, "pdf_text"
    )

    assert meta["status"] == "ok"
    assert extracted == deterministic              # nothing invented, nothing lost
    assert "unit" not in extracted                 # still unresolved, not filled
    # AI evidence is honestly empty rather than a fabricated payload
    assert meta["ai_candidate"]["payload"] == {}
    assert meta["ai_candidate"]["fields_present"] == []


@pytest.mark.asyncio
async def test_pages_are_adjudicated_field_by_field_not_positionally(monkeypatch):
    engine = _CancellingEngine([
        _ok({"activity": "AI-CHOICE", "amount": 999, "quantity": 1250}),
        _ok({"unit": "litres", "amount": 777}),
    ])
    service = _service(engine)
    _patch_text_layer(monkeypatch, _long_text(2))
    deterministic = {"activity": "Diesel", "amount": 85.21}

    meta, extracted, confidence, _method = await service._run_ai_candidate(
        _job(), b"x" * 100, deterministic, 0.33, "pdf_text"
    )

    # deterministic values win; AI only fills fields that were unresolved
    assert extracted["activity"] == "Diesel"
    assert extracted["amount"] == 85.21
    assert extracted["quantity"] == 1250          # filled from page 1
    assert extracted["unit"] == "litres"          # filled from page 2
    # page 2's amount (777) must never overwrite via positional pairing
    assert extracted["amount"] != 777
    assert confidence == 1.0
    # per-page AI provenance is recorded separately from the deterministic pass
    assert [page["page_index"] for page in meta["ai_pages"]] == [1, 2]
    assert meta["ai_fanout"]["calls_made"] == 2
    assert meta["adjudication"]["rule"] == "p1_document_level_adjudication"
    assert meta["adjudication"]["positional_blending"] is False

