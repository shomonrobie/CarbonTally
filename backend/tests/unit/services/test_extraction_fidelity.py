"""Phase 8 P1 — extraction fidelity: classifier, coverage, shape and policy.

Locks the PO-ratified P1 decisions (`P1-D1`…`P1-D8`) as executable tests: the
shadow-first default, the multi-line shape, the `P1-D2` block, the `P1-D3` fan-out
cap, the `P1-D5`/`P1-D7` page semantics and the `P1-D8` provenance stamps.
"""
from __future__ import annotations

import pytest

from services import extraction_fidelity as p1

SINGLE_LINE = "Acme Water Ltd\nInvoice 1234\nElectricity supply 12,500 kWh 2,340.00\nTotal due 2,340.00\n"

MULTI_LINE = (
    "Acme Water Ltd\n"
    "Invoice 1234\n"
    "Electricity supply 12,500 kWh 2,340.00\n"
    "Natural gas 4,000 kWh 320.00\n"
    "Water supply 300 m3 450.00\n"
    "Total due 3,110.00\n"
)

OCR_MARKER = "[page 1]\nDiesel for generator 1,200 litres 1,450.00\n[page 2]\nElectricity 3,000 kWh 900.00\n"


# -- P1-D1: shadow-first default --------------------------------------------
def test_shape_mode_defaults_to_shadow() -> None:
    assert p1.shape_mode(env={}) == p1.MODE_SHADOW


@pytest.mark.parametrize("raw", ["enabled", "shadow", "off", "ENABLED", " shadow "])
def test_shape_mode_reads_the_env(raw: str) -> None:
    assert p1.shape_mode(env={p1.SHAPE_MODE_ENV: raw}) == raw.strip().lower()


@pytest.mark.parametrize("raw", ["", "banana", "1", "yes"])
def test_shape_mode_fails_safe_to_shadow(raw: str) -> None:
    assert p1.shape_mode(env={p1.SHAPE_MODE_ENV: raw}) == p1.MODE_SHADOW


def test_pipeline_version_was_bumped() -> None:
    from domain.automatic_processing import PIPELINE_VERSION

    assert PIPELINE_VERSION == p1.PIPELINE_VERSION_P1


# -- P1-D5 / P1-D7: page semantics ------------------------------------------
def test_digital_text_without_boundaries_states_document_basis() -> None:
    pages, basis, resolution = p1.split_pages(MULTI_LINE, method="pdf_text")
    assert basis == "document" and resolution == "document" and len(pages) == 1


def test_formfeed_is_a_real_page_boundary() -> None:
    text = "Electricity 5 kWh 10.00\n\fGas 6 kWh 20.00\n"
    pages, basis, resolution = p1.split_pages(text, method="pdf_text")
    assert (basis, resolution, len(pages)) == ("formfeed", "formfeed", 2)


def test_ocr_markers_are_lower_trust_pages() -> None:
    pages, basis, resolution = p1.split_pages(OCR_MARKER, method="tesseract_ocr")
    assert (basis, resolution, len(pages)) == ("marker", "marker", 2)


# -- source-line detection ---------------------------------------------------
def test_only_genuine_activity_lines_are_found() -> None:
    lines = p1.find_source_lines(MULTI_LINE)
    assert len(lines) == 3
    assert all("total due" not in line["raw"].lower() for line in lines)


@pytest.mark.parametrize(
    "furniture",
    [
        "Total due 3,110.00",
        "Subtotal 2,660.00",
        "VAT 20% 532.00",
        "Invoice date 01/01/2026",
        "Page 1 of 3",
        "Head Office, 1 High Street",
    ],
)
def test_invoice_furniture_is_never_a_source_line(furniture: str) -> None:
    assert p1.find_source_lines(furniture) == []


def test_a_number_without_a_unit_is_not_a_source_line() -> None:
    assert p1.find_source_lines("Invoice number 12345") == []



# -- classifier --------------------------------------------------------------
def test_single_line_document_is_not_suspect() -> None:
    judgement = p1.classify(SINGLE_LINE, method="pdf_text", page_count=1)
    assert judgement.multi_line_suspect is False
    assert judgement.candidate_lines == 1


def test_multi_line_document_is_suspect() -> None:
    judgement = p1.classify(MULTI_LINE, method="pdf_text", page_count=1)
    assert judgement.multi_line_suspect is True
    assert judgement.candidate_lines == 3


def test_coverage_block_is_measurable_and_complete() -> None:
    coverage = p1.classify(MULTI_LINE, method="pdf_text", page_count=1).as_coverage()
    for key in (
        "multi_line_suspect",
        "candidate_lines",
        "page_count",
        "page_basis",
        "page_resolution",
        "text_chars",
        "clipped",
        "reasons",
        "page_cap",
    ):
        assert key in coverage
    assert coverage["text_chars"] == len(MULTI_LINE)


def test_clipping_is_reported() -> None:
    judgement = p1.classify("x" * (p1.CLIP_CHARS + 1), method="pdf_text", page_count=9)
    assert judgement.clipped is True


# -- P1-D3: AI fan-out policy ------------------------------------------------
def test_no_per_page_ai_when_not_suspect() -> None:
    plan = p1.ai_fanout_plan(p1.classify(SINGLE_LINE, method="pdf_text", page_count=1))
    assert plan["per_page_ai"] is False and plan["pages"] == 0


def test_no_per_page_ai_when_within_the_clip() -> None:
    plan = p1.ai_fanout_plan(p1.classify(MULTI_LINE, method="pdf_text", page_count=40))
    assert plan["per_page_ai"] is False


def test_per_page_ai_only_when_suspect_and_clipped_and_capped() -> None:
    text = MULTI_LINE + ("filler line with no unit at all\n" * 1000)
    judgement = p1.classify(text, method="pdf_text", page_count=500)
    assert judgement.multi_line_suspect and judgement.clipped
    plan = p1.ai_fanout_plan(judgement)
    assert plan["per_page_ai"] is True
    assert plan["pages"] == p1.PAGE_CAP == 20


# -- P1-D2: bounded block reason --------------------------------------------
def test_block_reason_is_bounded_and_truthful() -> None:
    reason = p1.block_reason(p1.classify(MULTI_LINE, method="pdf_text", page_count=1))
    assert "human review" in reason
    assert "single line" in reason
    assert len(reason) < 400


# -- P1-D8: provenance stamps ------------------------------------------------
def test_deterministic_stamp_names_the_method() -> None:
    assert p1.method_stamp(method="pdf_text", ai_used=False) == "det:pdf_text"
    assert p1.method_stamp(method="tesseract_ocr", ai_used=False) == "det:tesseract_ocr"


def test_ai_used_is_explicitly_stamped_never_relabelled() -> None:
    stamp = p1.method_stamp(method="pdf_text", ai_used=True)
    assert stamp.startswith("det:pdf_text+ai:")
    assert "ai:yes" in stamp


# -- the ratified shape ------------------------------------------------------
def test_multi_line_shape_emits_per_source_line_items() -> None:
    items, coverage = p1.build_line_items(MULTI_LINE, method="pdf_text", page_count=1)
    assert len(items) == 3
    assert [item["line_number"] for item in items] == [1, 2, 3]
    assert items[0]["activity"] == "Electricity"
    assert items[0]["quantity"] == 12500.0
    assert items[0]["page"] == 1
    assert items[0]["page_basis"] == "document"
    assert items[0]["page_trust"] == "standard"
    assert items[0]["extraction_method"] == "det:pdf_text"
    assert coverage["line_items"] == 3


def test_one_line_document_still_yields_exactly_one_line() -> None:
    items, _ = p1.build_line_items(SINGLE_LINE, method="pdf_text", page_count=1)
    assert len(items) == 1


def test_ocr_marker_lines_carry_lower_trust_pages() -> None:
    items, coverage = p1.build_line_items(OCR_MARKER, method="tesseract_ocr", page_count=2)
    assert [item["page"] for item in items] == [1, 2]
    assert all(item["page_trust"] == "lower" for item in items)
    assert all(item["extraction_method"] == "det:tesseract_ocr" for item in items)
    assert coverage["page_basis"] == "marker"
