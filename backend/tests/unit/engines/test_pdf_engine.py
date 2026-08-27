"""Unit tests for the legacy PDF/image extraction engine (``pdf_engine.PDFExtractor``).

Regression coverage for the historical-extraction recovery fixes:

1. Scanned-PDF OCR uses ``pdf2image.convert_from_bytes`` (the bytes API) instead
   of ``convert_from_path(io.BytesIO(...))``, which pdf2image never accepted and
   which silently returned no text.
2. The tesseract binary is resolved from ``TESSERACT_CMD`` / the system PATH
   instead of a hard-coded Windows path that broke OCR on Linux/Render.
3. Image OCR is dispatched through ``extract_and_parse_image`` (PIL decode +
   tesseract) and surfaces errors instead of silently swallowing them.
"""
from __future__ import annotations

import pdf_engine
from pdf_engine import PDFExtractor


class _FakeImage:
    """Minimal PIL-like stand-in returned by the mocks."""


def test_ocr_uses_convert_from_bytes_and_tags_pages(monkeypatch):
    """Scanned-PDF OCR must call the bytes API and keep per-page markers."""
    pages = [_FakeImage(), _FakeImage()]
    captured: dict = {}

    def fake_convert_from_bytes(data, dpi=200):
        captured["data"] = data
        return pages

    monkeypatch.setattr("pdf_engine.convert_from_bytes", fake_convert_from_bytes)
    calls: list = []
    monkeypatch.setattr(
        pdf_engine.pytesseract,
        "image_to_string",
        lambda img: calls.append(img) or f"page-text-{len(calls)}",
    )

    extractor = PDFExtractor()
    result = extractor._extract_text_ocr(b"fake-scan-pdf")

    assert captured["data"] == b"fake-scan-pdf"
    assert len(calls) == 2
    assert "[page 1]" in result
    assert "[page 2]" in result
    assert "page-text-1" in result
    assert "page-text-2" in result


def test_ocr_returns_empty_on_failure(monkeypatch):
    monkeypatch.setattr(
        "pdf_engine.convert_from_bytes",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("poppler missing")),
    )
    extractor = PDFExtractor()
    assert extractor._extract_text_ocr(b"x") == ""


def test_tesseract_cmd_not_forced_to_windows_path(monkeypatch):
    """The constructor must not hard-code a Windows-only tesseract path."""
    monkeypatch.delenv("TESSERACT_CMD", raising=False)
    monkeypatch.setattr(pdf_engine.pytesseract.pytesseract, "tesseract_cmd", "tesseract")
    PDFExtractor()
    assert pdf_engine.pytesseract.pytesseract.tesseract_cmd == "tesseract"


def test_tesseract_cmd_honours_env_override(monkeypatch):
    monkeypatch.setenv("TESSERACT_CMD", "/opt/tesseract/bin/tesseract")
    PDFExtractor()
    assert (
        pdf_engine.pytesseract.pytesseract.tesseract_cmd
        == "/opt/tesseract/bin/tesseract"
    )


def test_extract_and_parse_falls_back_to_ocr_when_no_digital_text(monkeypatch):
    extractor = PDFExtractor()
    monkeypatch.setattr(extractor, "_extract_text_direct", lambda b: "")
    monkeypatch.setattr(
        extractor,
        "_extract_text_ocr",
        lambda b: "\n[page 1]\nElectricity supply invoice showing 12500 kWh consumption\n",
    )
    monkeypatch.setattr(extractor, "_get_page_count", lambda b: 1)

    result = extractor.extract_and_parse(b"scan.pdf", "scan.pdf", "utility")
    assert result["file_metadata"]["extraction_method"] == "Tesseract OCR Engine v2.4"
    stream = result["data_streams"][0]
    assert stream["extracted_fields"]["consumption_kwh"]["value"] == 12500.0


def test_extract_and_parse_image_extracts_fields(monkeypatch):
    """Image OCR path: PIL decode + tesseract, structured parser applied."""
    monkeypatch.setattr(pdf_engine.Image, "open", lambda b: _FakeImage())
    monkeypatch.setattr(
        pdf_engine.pytesseract,
        "image_to_string",
        lambda img: "Electricity invoice dated 15/01/2025 showing 12500 kWh consumption",
    )

    extractor = PDFExtractor()
    result = extractor.extract_and_parse_image(b"fake-img", "bill.png", "utility")

    # Success responses carry batch_id/file_metadata/data_streams (no "status").
    assert result.get("status") != "error"
    assert result["file_metadata"]["file_type"] == "IMAGE"
    assert result["file_metadata"]["extraction_method"] == "Tesseract OCR Engine v2.4"
    assert (
        result["data_streams"][0]["extracted_fields"]["consumption_kwh"]["value"]
        == 12500.0
    )


def test_extract_and_parse_image_returns_error_when_ocr_fails(monkeypatch):
    monkeypatch.setattr(pdf_engine.Image, "open", lambda b: _FakeImage())

    def boom(img):
        raise RuntimeError("tesseract binary not found")

    monkeypatch.setattr(pdf_engine.pytesseract, "image_to_string", boom)
    extractor = PDFExtractor()
    result = extractor.extract_and_parse_image(b"fake-img", "bill.png", "utility")
    assert result["status"] == "error"
    assert "Could not process image" in result["message"]
