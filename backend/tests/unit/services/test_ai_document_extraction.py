"""Unit tests for services.ai_document_extraction (Phase 2).

Candidate AI extraction over deterministic document text:
- strict JSON parsing + code-fence stripping;
- canonical unit normalisation via the Phase-1 core.units mechanism;
- invalid JSON / non-object / transport failure return durable error envelopes
  (never raise, never a false success);
- output is CANDIDATE data — canonical completeness is computed the same way
  as the deterministic extractor so the durable gate treats both identically.
"""
from __future__ import annotations

import json

import pytest

from infra.llm_client import ChatCompletionResponse, LLMClient
from services.ai_document_extraction import AIDocumentExtractionEngine


def _client_for(response: str, *, fail: bool = False) -> LLMClient:
    def transport(payload):
        if fail:
            from core.exceptions import AIExtractionFailedError

            raise AIExtractionFailedError("LLM API returned HTTP 500")
        return ChatCompletionResponse(text=response)

    return LLMClient(
        base_url="https://llm.example.test/v1",
        api_key="test-key",
        model="test-model",
        transport=transport,
    )


async def _extract(response: str, text: str = "invoice text") -> dict:
    engine = AIDocumentExtractionEngine(_client_for(response))
    return await engine.extract_candidate(text, filename="bill.pdf", method="pdf_text")


async def test_single_item_candidate_normalized_units() -> None:
    payload = json.dumps(
        {
            "activity": "Natural gas",
            "quantity": "1000",
            "unit": "m3",
            "date": "2025-06-01",
            "supplier": "British Gas",
        }
    )
    result = await _extract(payload)
    assert result["status"] == "ok"
    assert result["model"] == "test-model"
    assert result["method"] == "ai:pdf_text"
    data = result["extracted_data"]
    assert data["activity"] == "Natural gas"
    assert data["quantity"] == 1000.0
    # Phase-1 canonical normalisation: m3 → cubic metres, never a second layer.
    assert data["unit"] == "cubic metres"
    assert data["date"] == "2025-06-01"
    assert result["confidence"] == 1.0


async def test_l_alias_normalized_to_litres() -> None:
    payload = json.dumps({"activity": "Diesel", "quantity": 1250, "unit": "L"})
    result = await _extract(payload)
    assert result["extracted_data"]["unit"] == "litres"


async def test_unknown_unit_is_not_silently_made_valid() -> None:
    # An unknown unit passes through unchanged — the deterministic mapping /
    # canonical CalculationRequest boundary rejects it downstream (no invented
    # validity).
    payload = json.dumps({"activity": "Widgets", "quantity": 5, "unit": "boxes"})
    result = await _extract(payload)
    assert result["status"] == "ok"
    assert result["extracted_data"]["unit"] == "boxes"
    # Completeness reflects presence, not validity — validity is decided by the
    # authoritative deterministic layer.
    assert result["confidence"] == 1.0


async def test_line_items_shape() -> None:
    payload = json.dumps(
        {
            "line_items": [
                {"activity": "Diesel", "quantity": 1250, "unit": "litres", "date": "2025-01-05"},
                {"activity": "Petrol", "quantity": 300, "unit": "litres", "date": "2025-01-06"},
            ]
        }
    )
    result = await _extract(payload)
    assert result["status"] == "ok"
    lines = result["extracted_data"]["line_items"]
    assert len(lines) == 2
    assert lines[0]["activity"] == "Diesel"
    assert result["extracted_data"]["date"] == "2025-01-05"
    assert result["confidence"] == 1.0


async def test_code_fence_stripped() -> None:
    payload = "```json\n" + json.dumps({"activity": "Diesel", "quantity": 1, "unit": "litres"}) + "\n```"
    result = await _extract(payload)
    assert result["status"] == "ok"
    assert result["extracted_data"]["quantity"] == 1.0


async def test_invalid_json_is_a_durable_error() -> None:
    result = await _extract("this is not json")
    assert result["status"] == "error"
    assert result["confidence"] == 0.0
    assert "invalid JSON" in (result.get("detail") or "")


async def test_non_object_response_is_error() -> None:
    result = await _extract("[1, 2, 3]")
    assert result["status"] == "error"


async def test_transport_failure_is_durable_error() -> None:
    engine = AIDocumentExtractionEngine(_client_for("", fail=True))
    result = await engine.extract_candidate("some text", filename="x.pdf")
    assert result["status"] == "error"
    assert "HTTP 500" in (result.get("detail") or "")


async def test_empty_text_is_no_text() -> None:
    engine = AIDocumentExtractionEngine(_client_for("{}"))
    result = await engine.extract_candidate("   ")
    assert result["status"] == "no_text"
    assert result["confidence"] == 0.0


async def test_negative_quantity_rejected() -> None:
    payload = json.dumps({"activity": "Diesel", "quantity": -5, "unit": "litres"})
    result = await _extract(payload)
    assert result["status"] == "ok"
    assert "quantity" not in result["extracted_data"]
    assert result["confidence"] < 1.0


async def test_spend_based_currency_fallback() -> None:
    payload = json.dumps(
        {"activity": "Purchased goods", "amount": "2500", "currency": "GBP"}
    )
    result = await _extract(payload)
    data = result["extracted_data"]
    assert data["quantity"] == 2500.0
    assert data["unit"] == "GBP"


async def test_empty_candidate_is_zero_confidence_not_valid() -> None:
    # An empty LLM payload yields an empty candidate with zero completeness —
    # the deterministic gate (confidence >= 0.5) blocks it into manual review.
    result = await _extract("{}")
    assert result["status"] == "ok"
    assert result["extracted_data"] == {}
    assert result["confidence"] == 0.0
    assert result["unresolved"] == ["activity", "quantity", "unit"]
