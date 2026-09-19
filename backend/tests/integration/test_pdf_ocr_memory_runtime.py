"""F-070-D — the OCR path against the REAL renderer: bounded memory, fail-safe behaviour.

No database is involved, so this module never requests the integration `pool` fixture.

The production incident (Render API OOM, 512 MiB limit, 2026-09-17 → 2026-09-19) was
reproduced locally before the fix: ``convert_from_bytes(pdf_bytes, dpi=300)`` with no page
bounds makes pdf2image read poppler's ENTIRE multi-page stdout stream and parse every page
into PIL objects before returning (measured +399.7 MiB for six A4 pages, +1348.8 MiB for
twenty-four), and on the production host all of it was discarded because the Tesseract
binary was missing — the peak happened before the first page was OCR'd.

The local host has poppler but no Tesseract binary, so the recogniser is stubbed where a
WORKING OCR host must be simulated. That isolates the render behaviour, which is where the
memory goes; the real binary's presence is covered by the probe tests.
"""
from __future__ import annotations

import concurrent.futures
import pathlib
import resource

import pytest
from PIL import Image, ImageDraw

import pdf_engine
from pdf_engine import PDFExtractor

A4_150DPI = (1240, 1754)


def peak_mib() -> float:
    """Process peak RSS so far (the metric a container memory limit enforces)."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def scan_pdf(directory: pathlib.Path, pages: int) -> bytes:
    """An image-only (scanned-shaped) multi-page PDF: no text layer, so OCR is required."""
    built = []
    for index in range(1, pages + 1):
        image = Image.new("RGB", A4_150DPI, (252, 250, 246))
        draw = ImageDraw.Draw(image)
        for line in range(0, 40):
            draw.text((80, 120 + line * 26),
                      f"Page {index} line {line}: Diesel fuel 1250 litres 1775.00 GBP",
                      fill=(20, 20, 20))
        built.append(image)
    target = directory / f"scan_{pages}p.pdf"
    built[0].save(target, "PDF", save_all=True, append_images=built[1:], resolution=150.0)
    return target.read_bytes()


@pytest.fixture(scope="module")
def scans(tmp_path_factory) -> dict:
    directory = tmp_path_factory.mktemp("f070d")
    return {n: scan_pdf(directory, n) for n in (1, 6, 24)}


@pytest.fixture
def working_recogniser(monkeypatch):
    """Simulate a host where Tesseract IS installed (the render still runs for real)."""
    monkeypatch.setattr(pdf_engine, "tesseract_available", lambda: True)
    monkeypatch.setattr(
        pdf_engine.pytesseract, "image_to_string",
        lambda image, *a, **k: f"Diesel fuel {image.width}x{image.height} litres",
    )
    return True


# ---------------------------------------------------------------------------
# 1–4: small, multi-page, large and OCR-required documents
# ---------------------------------------------------------------------------


def test_1_a_small_pdf_is_ocr_read(scans, working_recogniser) -> None:
    extractor = PDFExtractor()
    text = extractor._extract_text_ocr(scans[1])
    assert "[page 1]" in text and "Diesel fuel" in text
    assert extractor._extract_text_direct(scans[1]) == ""   # no text layer: OCR was needed


def test_2_a_multi_page_pdf_reads_every_page_once(scans, working_recogniser) -> None:
    extractor = PDFExtractor()
    text = extractor._extract_text_ocr(scans[6])
    assert [f"[page {n}]" in text for n in range(1, 7)] == [True] * 6
    assert extractor._get_page_count(scans[6]) == 6


def test_3_a_large_document_stays_memory_bounded(scans, working_recogniser) -> None:
    """The 24-page scan peaked at 1.9 GiB before the fix; one page at a time is flat."""
    extractor = PDFExtractor()
    before = peak_mib()
    text = extractor._extract_text_ocr(scans[24])
    delta = peak_mib() - before
    assert "[page 24]" in text
    # Pre-fix this document needed ~1.3 GiB of additional peak; the bound is generous
    # enough for interpreter/poppler noise yet far below any whole-document materialisation.
    assert delta < 150, f"24-page OCR added {delta:.1f} MiB of peak RSS"


def test_4_an_ocr_required_document_reaches_ocr_and_reports_its_method(
    scans, working_recogniser
) -> None:
    """The real API helper over the real renderer: OCR is reached and named honestly."""
    from api.v3_documents import _extract_document_text

    summary = _extract_document_text(scans[6], "scan.pdf", "application/pdf")
    assert summary["status"] == "ok"
    assert summary["method"] == "tesseract_ocr"
    assert summary["page_count"] == 6
    assert "Diesel fuel" in summary["text"]



# ---------------------------------------------------------------------------
# 5–6: missing binary and a failing recogniser — fail safe, no wasted work
# ---------------------------------------------------------------------------


def test_5_a_missing_binary_renders_nothing(scans, monkeypatch) -> None:
    """The production configuration: OCR cannot run, so no page is materialised at all."""
    renders: list = []
    monkeypatch.setattr(pdf_engine, "tesseract_available", lambda: False)
    monkeypatch.setattr(
        "pdf_engine.convert_from_bytes",
        lambda *a, **k: renders.append(a) or [],
    )
    extractor = PDFExtractor()
    before = peak_mib()
    assert extractor._extract_text_ocr(scans[24]) == ""
    assert renders == []                    # the 24-page document was never rendered
    assert peak_mib() - before < 5          # and therefore cost no memory


def test_6_a_failing_recogniser_keeps_what_was_read_and_never_raises(scans, monkeypatch) -> None:
    monkeypatch.setattr(pdf_engine, "tesseract_available", lambda: True)
    state = {"page": 0}

    def _flaky(image, *a, **k):
        state["page"] += 1
        if state["page"] >= 2:
            raise RuntimeError("tesseract died mid-document")
        return "first page text"

    monkeypatch.setattr(pdf_engine.pytesseract, "image_to_string", _flaky)
    extractor = PDFExtractor()
    text = extractor._extract_text_ocr(scans[6])       # must not raise
    assert "first page text" in text
    assert "[page 2]" not in text


# ---------------------------------------------------------------------------
# 7–8: repeated and concurrent requests must not accumulate
# ---------------------------------------------------------------------------


def test_7_repeated_requests_do_not_accumulate_memory(scans, working_recogniser) -> None:
    extractor = PDFExtractor()
    before = peak_mib()
    for _ in range(10):
        assert "[page 6]" in extractor._extract_text_ocr(scans[6])
    assert peak_mib() - before < 150


def test_8_concurrent_requests_stay_bounded(scans, working_recogniser) -> None:
    """Four concurrent extractions of a 6-page scan: bounded, not 4 × whole-document."""
    extractor = PDFExtractor()
    before = peak_mib()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        texts = list(pool.map(lambda _: extractor._extract_text_ocr(scans[6]), range(4)))
    assert all("[page 6]" in text for text in texts)
    delta = peak_mib() - before
    # Pre-fix each worker alone needed ~400 MiB for this document (≈1.6 GiB combined).
    assert delta < 300, f"4 concurrent 6-page OCRs added {delta:.1f} MiB of peak RSS"


# ---------------------------------------------------------------------------
# The no-poppler fallback must also render one page at a time
# ---------------------------------------------------------------------------


def test_the_pypdfium_fallback_yields_pages_lazily(scans) -> None:
    pytest.importorskip("pypdfium2")
    from services.automatic_extraction import _render_pdf_pages_pypdfium

    pages = _render_pdf_pages_pypdfium(scans[24])
    assert not isinstance(pages, list)          # a generator, never a materialised list
    first = next(iter(pages))
    assert first[:8] == b"\x89PNG\r\n\x1a\n"    # a real rendered page


def test_the_pypdfium_fallback_is_memory_bounded(scans) -> None:
    pytest.importorskip("pypdfium2")
    from services.automatic_extraction import _render_pdf_pages_pypdfium

    before = peak_mib()
    rendered = 0
    for page in _render_pdf_pages_pypdfium(scans[24]):
        assert page[:8] == b"\x89PNG\r\n\x1a\n"
        rendered += 1
    delta = peak_mib() - before
    assert rendered == 24
    # A materialised list of 24 rendered pages would cost hundreds of MiB.
    assert delta < 150, f"24-page fallback render added {delta:.1f} MiB of peak RSS"

