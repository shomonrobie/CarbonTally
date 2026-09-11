"""Regression tests for the Phase 2 text-layer refactor + candidate merge.

The deterministic text layer (``extract_document_text``) was extracted from the
PDF/IMAGE suggestion path so the optional AI step reuses it — its behaviour must
be identical to the pre-refactor deterministic pipeline. The candidate merge
must preserve deterministic source evidence (AI only fills gaps).
"""
from __future__ import annotations

from services.automatic_extraction import (
    completeness_score,
    extract_document,
    extract_document_text,
)
from services.automatic_processing import (
    _merge_extraction_candidates,
    _missing_required,
)


def test_text_layer_csv_returns_decoded_text() -> None:
    content = (
        "Date,Supplier,Category,Quantity (litres),Amount,Currency\n"
        "05/01/2025,Shell Fleet Solutions,Diesel fuel,1250,1775.00,GBP\n"
    ).encode("utf-8")
    layer = extract_document_text(content, "fleet.csv", "text/csv")
    assert layer["status"] == "ok"
    assert layer["method"] == "csv"
    assert "Diesel fuel" in layer["text"]


def test_text_layer_unsupported_never_raises() -> None:
    layer = extract_document_text(b"\x00\x01", "note.weird", "application/octet-stream")
    assert layer["status"] == "unsupported"
    assert layer["text"] == ""


def test_text_layer_garbage_pdf_never_raises() -> None:
    layer = extract_document_text(b"not a real pdf at all", "bill.pdf", "application/pdf")
    assert layer["status"] in ("no_text", "error")


def test_deterministic_and_text_layer_pdf_agree() -> None:
    # The deterministic suggestion pass and the text layer share the same text
    # resolution — a low-quality/garbage PDF must not raise in either.
    content = b"garbage bytes that are not a pdf"
    det = extract_document(content, "bill.pdf", "application/pdf")
    layer = extract_document_text(content, "bill.pdf", "application/pdf")
    assert det["status"] in ("ok", "no_text", "error")
    assert layer["status"] in ("ok", "no_text", "error")


def test_completeness_score_public_semantics() -> None:
    assert completeness_score({"activity": "Diesel"}) == 0.3333
    assert completeness_score({"activity": "Diesel", "quantity": 1, "unit": "litres"}) == 1.0
    assert completeness_score({}) == 0.0
    assert completeness_score({"line_items": [{"quantity": 1}]}) == 0.3333


def test_missing_required_reports_unresolved() -> None:
    assert _missing_required({"activity": "Diesel"}) == ["quantity", "unit"]
    assert _missing_required({}) == ["activity", "quantity", "unit"]
    lines = {"line_items": [{"quantity": 1}, {"unit": "kWh"}]}
    assert _missing_required(lines) == ["activity", "quantity", "unit"]


def test_merge_keeps_deterministic_source_evidence() -> None:
    deterministic = {
        "activity": "Diesel", "quantity": 1250.0, "unit": "litres",
        "supplier": "Shell Fleet", "date": "05/01/2025",
    }
    ai = {"activity": "Petrol", "quantity": 999, "unit": "kWh", "supplier": "AI Co"}
    merged = _merge_extraction_candidates(deterministic, ai)
    # Deterministic values win everywhere; AI may only fill gaps (none here).
    assert merged == deterministic


def test_merge_ai_fills_gaps_only() -> None:
    deterministic = {"activity": "Diesel"}
    ai = {"quantity": 1250, "unit": "litres", "supplier": "Shell"}
    merged = _merge_extraction_candidates(deterministic, ai)
    assert merged["activity"] == "Diesel"
    assert merged["quantity"] == 1250
    assert merged["unit"] == "litres"
    assert merged["supplier"] == "Shell"


def test_merge_line_items_indexed() -> None:
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
    lines = merged["line_items"]
    # Line 1 deterministic values win; line 2 AI fills the missing fields.
    assert lines[0]["quantity"] == 1250.0
    assert lines[0]["unit"] == "litres"
    assert lines[1]["quantity"] == 300
    assert lines[1]["unit"] == "litres"
