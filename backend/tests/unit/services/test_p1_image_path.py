"""Step 2 / WS-B (B3) — the shared P1 fidelity hook on the IMAGE path.

`P1-D1` authorises the multi-line shape for new **PDF/IMAGE** documents, but
before Step 2 the fidelity hook was wired only into `_extract_pdf`, so a scanned
multi-line image could still be silently collapsed into a single line. These
tests lock the IMAGE-path integration and its shadow-first rollout behaviour.
"""
from __future__ import annotations

import pytest

import services.automatic_extraction as ax


def test_image_path_applies_the_fidelity_hook_when_enabled(monkeypatch):
    multi_line = (
        "Invoice INV-1\n"
        "Water supply 100 m3 50.00\n"
        "Water treatment 20 m3 15.00\n"
    )
    monkeypatch.setattr(ax, "_image_text", lambda content: (multi_line, "tesseract_ocr"))
    monkeypatch.setenv("CARBONTALLY_P1_EXTRACTION_SHAPE", "enabled")
    # Step 2C / POD-4 — 'enabled' is only honoured inside the controlled rollout,
    # so the sanctioned test opt-in is the explicit wildcard allowlist.
    monkeypatch.setenv("CARBONTALLY_P1_ORGANIZATION_ALLOWLIST", "*")

    result = ax._extract_image(b"image-bytes")

    assert result["method"] == "tesseract_ocr"
    assert result["coverage"]["mode"] == "enabled"
    assert result["coverage"]["multi_line_suspect"] is True
    # A suspect IMAGE is either given per-source-line items or is truthfully
    # blocked with the bounded P1-D2 reason — never silently collapsed.
    assert result["status"] in ("ok", "multi_line_unresolved")
    if result["status"] == "multi_line_unresolved":
        assert result["block_reason"]
    else:
        assert result["extracted_data"]["line_items"]


def test_image_path_shadow_mode_only_measures(monkeypatch):
    monkeypatch.setattr(
        ax, "_image_text", lambda content: ("Water supply 100 m3 50.00", "tesseract_ocr")
    )
    monkeypatch.setenv("CARBONTALLY_P1_EXTRACTION_SHAPE", "shadow")

    result = ax._extract_image(b"image-bytes")

    assert result["status"] == "ok"
    assert result["coverage"]["mode"] == "shadow"
    assert "line_items" not in result["extracted_data"]


def test_image_path_mode_off_has_no_coverage(monkeypatch):
    monkeypatch.setattr(
        ax, "_image_text", lambda content: ("Water supply 100 m3 50.00", "tesseract_ocr")
    )
    monkeypatch.setenv("CARBONTALLY_P1_EXTRACTION_SHAPE", "off")

    result = ax._extract_image(b"image-bytes")

    assert result["status"] == "ok"
    assert "coverage" not in result


def test_pdf_path_still_uses_the_same_shared_hook(monkeypatch):
    """The refactor must not regress the PDF path it replaced."""
    monkeypatch.setattr(
        ax,
        "_pdf_text",
        lambda content: ("Water supply 100 m3 50.00", "pdf_text", 1),
    )
    monkeypatch.setenv("CARBONTALLY_P1_EXTRACTION_SHAPE", "shadow")

    result = ax._extract_pdf(b"pdf-bytes")

    assert result["status"] == "ok"
    assert result["coverage"]["mode"] == "shadow"
    assert "line_items" not in result["extracted_data"]
