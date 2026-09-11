"""P0-1 — upload content-type normalisation regression tests.

New documents must be stored with a browser-renderable content type so the
document viewer renders PDFs/images inline instead of triggering a download.
Generic browser-supplied types (application/octet-stream) are replaced by the
canonical type for the classified file type; specific types are trusted;
unknown types fall back to the supplied value so uploads never fail.
"""
from __future__ import annotations

from api.v3_documents import _renderable_content_type


def test_pdf_with_octet_stream_maps_to_application_pdf() -> None:
    assert (
        _renderable_content_type("invoice.pdf", "PDF", "application/octet-stream")
        == "application/pdf"
    )


def test_pdf_with_empty_mime_maps_to_application_pdf() -> None:
    assert _renderable_content_type("invoice.pdf", "PDF", "") == "application/pdf"


def test_pdf_with_specific_mime_is_preserved() -> None:
    assert (
        _renderable_content_type("invoice.pdf", "PDF", "application/pdf")
        == "application/pdf"
    )


def test_png_with_octet_stream_maps_to_image_png() -> None:
    assert (
        _renderable_content_type("scan.png", "IMAGE", "application/octet-stream")
        == "image/png"
    )


def test_csv_with_octet_stream_maps_to_text_csv() -> None:
    assert (
        _renderable_content_type("usage.csv", "SPREADSHEET", "application/octet-stream")
        == "text/csv"
    )


def test_unknown_extension_falls_back_to_supplied() -> None:
    assert (
        _renderable_content_type("file.weird", "OTHER", "text/html") == "text/html"
    )


def test_unknown_extension_no_supplied_returns_octet_stream() -> None:
    assert (
        _renderable_content_type("file.weird", "OTHER", "")
        == "application/octet-stream"
    )
