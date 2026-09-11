"""Deterministic synthetic fixture generation (spec §14).

These are tiny, valid files for future upload/processing QA runs. They are
generated in-memory/temp — never written into the CarbonTally repo. Names are
QA-tagged so future cleanup can identify them.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Optional

QA_FIXTURE_PREFIX = "qa_harness_fixture_"


def _tag(name: str) -> str:
    return QA_FIXTURE_PREFIX + name


def make_csv_fixture(rows: Optional[list] = None) -> str:
    """Return CSV text for a fuel/utility activity fixture (QA-tagged)."""
    data = rows or [
        ["date", "activity", "quantity", "unit"],
        ["2026-08-01", "Diesel", "4258.9", "L"],
        ["2026-08-02", "Petrol", "1200.0", "L"],
    ]
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(data)
    return buffer.getvalue()


def make_pdf_fixture() -> bytes:
    """Return a tiny, structurally-valid PDF (minimal objects).

    Not meant for real OCR — enough to exercise upload → file record →
    processing pipelines. Deterministic bytes (no timestamps).
    """
    content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj\n4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 72 720 Td (QA harness fixture) Tj ET\nendstream\nendobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
    return content


def make_xlsx_fixture() -> bytes:
    """Return a minimal XLSX (zip) containing one worksheet.

    Uses Python's stdlib zipfile/zlib only — no openpyxl dependency.
    """
    sheet_xml = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        b'<sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>activity</t></is></c></row>'
        b'<row r="2"><c r="A2" t="inlineStr"><is><t>Diesel</t></is></c></row>'
        b'</sheetData></worksheet>'
    )
    return _zip_bytes({
        "[Content_Types].xml": (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            b'<Default Extension="xml" ContentType="application/xml"/>'
            b'<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            b'<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            b'</Types>'
        ),
        "_rels/.rels": (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            b'</Relationships>'
        ),
        "xl/workbook.xml": (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            b'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            b'<sheets><sheet name="QA" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            b'</Relationships>'
        ),
        "xl/worksheets/sheet1.xml": sheet_xml,
    })


def _zip_bytes(files: dict) -> bytes:
    import zipfile
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def write_fixture(kind: str, directory: Optional[Path] = None) -> Path:
    """Write a fixture file into ``directory`` (default: temp dir)."""
    directory = Path(directory) if directory else Path(__file__).resolve().parent
    directory.mkdir(parents=True, exist_ok=True)
    if kind == "csv":
        path = directory / f"{_tag('fuel.csv')}"
        path.write_text(make_csv_fixture(), encoding="utf-8")
    elif kind == "pdf":
        path = directory / f"{_tag('invoice.pdf')}"
        path.write_bytes(make_pdf_fixture())
    elif kind == "xlsx":
        path = directory / f"{_tag('activity.xlsx')}"
        path.write_bytes(make_xlsx_fixture())
    else:
        raise ValueError(f"unknown fixture kind {kind!r}")
    return path
