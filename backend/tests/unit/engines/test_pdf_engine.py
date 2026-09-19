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
    """Scanned-PDF OCR must call the bytes API and keep per-page markers.

    F-070-D: it must also render EXACTLY ONE page per call (bounded peak memory) and never
    ask pdf2image for the whole document at 300 DPI.
    """
    from PIL import Image as _Image

    captured: list = []

    def fake_convert_from_bytes(data, dpi=200, first_page=None, last_page=None):
        captured.append((data, dpi, first_page, last_page))
        return [_Image.new("RGB", (4, 4))]

    monkeypatch.setattr("pdf_engine.convert_from_bytes", fake_convert_from_bytes)
    monkeypatch.setattr(pdf_engine, "tesseract_available", lambda: True)
    calls: list = []
    monkeypatch.setattr(
        pdf_engine.pytesseract,
        "image_to_string",
        lambda img: calls.append(img) or f"page-text-{len(calls)}",
    )

    extractor = PDFExtractor()
    monkeypatch.setattr(extractor, "_get_page_count", lambda b: 2)
    result = extractor._extract_text_ocr(b"fake-scan-pdf")

    assert len(calls) == 2
    assert "[page 1]" in result
    assert "[page 2]" in result
    assert "page-text-1" in result
    assert "page-text-2" in result
    # one page per render, at the original DPI, in order — never the whole document
    assert captured == [
        (b"fake-scan-pdf", 300, 1, 1),
        (b"fake-scan-pdf", 300, 2, 2),
    ]


def test_ocr_returns_empty_on_failure(monkeypatch):
    monkeypatch.setattr(pdf_engine, "tesseract_available", lambda: True)
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


# ---------------------------------------------------------------------------
# F-070-D — bounded OCR: one page at a time, no wasted render, fail-safe
# ---------------------------------------------------------------------------


def test_missing_tesseract_never_renders_a_page(monkeypatch):
    """The production OOM configuration: the binary is absent, so nothing is rendered."""
    renders: list = []
    monkeypatch.setattr(pdf_engine, "tesseract_available", lambda: False)
    monkeypatch.setattr(
        "pdf_engine.convert_from_bytes", lambda *a, **k: renders.append(a) or []
    )
    extractor = PDFExtractor()
    assert extractor._extract_text_ocr(b"scan") == ""
    assert renders == []                       # no page materialisation at all


def test_recognised_pages_are_kept_when_a_later_page_fails(monkeypatch):
    """A failure stops the pass without discarding the pages already read."""
    from PIL import Image as _Image

    def fake_convert_from_bytes(data, dpi=200, first_page=None, last_page=None):
        if first_page == 3:
            raise RuntimeError("poppler died on page 3")
        return [_Image.new("RGB", (4, 4))]

    monkeypatch.setattr("pdf_engine.convert_from_bytes", fake_convert_from_bytes)
    monkeypatch.setattr(pdf_engine, "tesseract_available", lambda: True)
    monkeypatch.setattr(pdf_engine.pytesseract, "image_to_string", lambda img: "ok-text")
    extractor = PDFExtractor()
    monkeypatch.setattr(extractor, "_get_page_count", lambda b: 5)

    result = extractor._extract_text_ocr(b"scan")
    assert "[page 1]" in result and "[page 2]" in result
    assert "[page 3]" not in result            # the failure is where it stopped
    assert result.count("ok-text") == 2        # earlier pages are never lost


def test_a_failing_recogniser_is_fail_safe(monkeypatch):
    """A recogniser failure returns no text and never raises into the pipeline."""
    from PIL import Image as _Image

    monkeypatch.setattr(
        "pdf_engine.convert_from_bytes",
        lambda data, dpi=200, first_page=None, last_page=None: [
            _Image.new("RGB", (4, 4))
        ],
    )
    monkeypatch.setattr(pdf_engine, "tesseract_available", lambda: True)
    monkeypatch.setattr(
        pdf_engine.pytesseract,
        "image_to_string",
        lambda img: (_ for _ in ()).throw(RuntimeError("tesseract exploded")),
    )
    extractor = PDFExtractor()
    monkeypatch.setattr(extractor, "_get_page_count", lambda b: 2)
    assert extractor._extract_text_ocr(b"scan") == ""


def test_the_page_budget_bounds_the_work(monkeypatch):
    """OCR_MAX_PAGES caps how many pages are rendered and OCR'd (bounded work)."""
    from PIL import Image as _Image

    rendered: list = []
    monkeypatch.setattr(pdf_engine, "tesseract_available", lambda: True)
    monkeypatch.setattr(
        "pdf_engine.convert_from_bytes",
        lambda data, dpi=200, first_page=None, last_page=None: (
            rendered.append(first_page) or [_Image.new("RGB", (4, 4))]
        ),
    )
    monkeypatch.setattr(pdf_engine.pytesseract, "image_to_string", lambda img: "t")
    monkeypatch.setenv("OCR_MAX_PAGES", "2")
    extractor = PDFExtractor()
    monkeypatch.setattr(extractor, "_get_page_count", lambda b: 9)

    result = extractor._extract_text_ocr(b"scan")
    assert rendered == [1, 2]
    assert "[page 2]" in result and "[page 3]" not in result



def test_the_budget_configuration_is_sane(monkeypatch):
    monkeypatch.delenv("OCR_MAX_PAGES", raising=False)
    assert pdf_engine._ocr_max_pages() == pdf_engine._DEFAULT_OCR_MAX_PAGES
    monkeypatch.setenv("OCR_MAX_PAGES", "7")
    assert pdf_engine._ocr_max_pages() == 7
    monkeypatch.setenv("OCR_MAX_PAGES", "not-a-number")
    assert pdf_engine._ocr_max_pages() == pdf_engine._DEFAULT_OCR_MAX_PAGES
    monkeypatch.setenv("OCR_MAX_PAGES", "0")
    assert pdf_engine._ocr_max_pages() == 1     # never zero: it would skip every page


def test_the_tesseract_probe_is_cached_for_the_process(monkeypatch):
    """A missing binary must not be re-probed (and re-paid for) on every document."""
    probes: list = []
    monkeypatch.setattr(
        pdf_engine.pytesseract, "get_tesseract_version", lambda: probes.append(1) or "5.3"
    )
    pdf_engine.reset_tesseract_probe()
    try:
        assert pdf_engine.tesseract_available() is True
        assert pdf_engine.tesseract_available() is True
        extractor = PDFExtractor()
        monkeypatch.setattr(
            "pdf_engine.convert_from_bytes",
            lambda data, dpi=200, first_page=None, last_page=None: [],
        )
        extractor._extract_text_ocr(b"scan")
        extractor._extract_text_ocr(b"scan")
    finally:
        pdf_engine.reset_tesseract_probe()
    assert len(probes) == 1                    # probed exactly once for the whole process


def test_the_probe_reports_unusable_tesseract(monkeypatch):
    monkeypatch.setattr(
        pdf_engine.pytesseract,
        "get_tesseract_version",
        lambda: (_ for _ in ()).throw(RuntimeError("not installed")),
    )
    pdf_engine.reset_tesseract_probe()
    try:
        assert pdf_engine.tesseract_available() is False
        assert pdf_engine.tesseract_available() is False
    finally:
        pdf_engine.reset_tesseract_probe()

