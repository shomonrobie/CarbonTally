"""Synthetic upload fixtures (PDF/CSV/XLSX/OCR) for future mutation tests.

Generating fixtures is a harness-local operation that never touches the
application; the fixtures themselves are only used by future run stages.
"""

from qa_harness.browser.fixtures.generate import (
    make_csv_fixture,
    make_pdf_fixture,
    make_xlsx_fixture,
)

__all__ = ["make_csv_fixture", "make_pdf_fixture", "make_xlsx_fixture"]
