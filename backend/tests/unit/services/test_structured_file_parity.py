"""Step 2C / POD-3 — CSV/XLSX parity with the pre-V3 structured-file readers.

The V3 tabular reader resolved **exact normalised header keys only**, so the
column shapes real supplier exports actually use (``Fuel Type``, ``Volume (L)``,
``Transaction Date``, ``Total Cost (£)``, ``Meter Type`` …) fell through to
unknown fields. The file still parsed, but every row lost
``activity``/``quantity``/``unit`` and the job was blocked with a misleadingly
empty extraction — the PO-visible symptom "CSV/Excel files are not being
extracted" after upload.

These tests pin the parity behaviour using the project's own fixtures:

* ``mock_scope3.csv`` — already worked; regression-guarded.
* ``mock_uk_fuel_card_messy.csv`` — 50 rows, previously completeness **0.00**.
* ``mock_uk_utility_bill.csv`` — 20 rows, previously ``activity`` unresolved.

They also pin the anti-fabrication rules and the XLSX sheet-awareness rules.
"""
from __future__ import annotations

import io
from pathlib import Path

import openpyxl
import pytest

from services.automatic_extraction import (
    _normalise_columns,
    extract_document,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_FUEL_CARD = _REPO_ROOT / "mock_uk_fuel_card_messy.csv"
_UTILITY_BILL = _REPO_ROOT / "mock_uk_utility_bill.csv"
_SCOPE3 = _REPO_ROOT / "mock_scope3.csv"


def _run(path: Path):
    return extract_document(path.read_bytes(), path.name, "text/csv")


pytestmark = pytest.mark.skipif(
    not (_FUEL_CARD.exists() and _UTILITY_BILL.exists() and _SCOPE3.exists()),
    reason="repository CSV fixtures are not present in this checkout",
)


def test_fuel_card_export_is_fully_resolved():
    result = _run(_FUEL_CARD)

    assert result["status"] == "ok"
    assert result["method"] == "csv"
    lines = result["extracted_data"]["line_items"]
    assert len(lines) == 50  # every data row survives
    # The gate must now clear: previously 0.00 with activity/quantity/unit missing.
    assert result["confidence"] >= 0.5
    assert result["unresolved"] == []

    first = lines[0]
    assert first["activity"] == "Diesel"          # canonicalised from "Diesel (Premium)"
    assert first["quantity"] == 53.8              # the raw "Volume (L)" value, unmodified
    assert first["unit"] == "litres"              # derived from the (L) column header
    assert first["amount"] == 85.21
    assert first["supplier"] == "Esso"            # "Merchant" column
    assert first["date"] == "01/10/2023"          # "Transaction Date" column
    assert first["source_row"] == 1               # row identity preserved


def test_fuel_card_rows_keep_order_and_do_not_fabricate_values():
    lines = _run(_FUEL_CARD)["extracted_data"]["line_items"]

    assert [line["source_row"] for line in lines] == list(range(1, len(lines) + 1))
    assert [line["quantity"] for line in lines[:3]] == [53.8, 43.12, 20.96]
    for line in lines:
        assert line.get("activity")
        assert isinstance(line.get("quantity"), float)
        assert line.get("unit") in ("litres", "kwh", "kg", "tonnes", "GBP")


def test_utility_bill_activity_is_resolved_from_the_meter_type_column():
    result = _run(_UTILITY_BILL)

    assert result["status"] == "ok"
    lines = result["extracted_data"]["line_items"]
    assert len(lines) == 20
    assert result["confidence"] >= 0.5
    assert result["unresolved"] == []          # previously ["activity"]

    first = lines[0]
    assert first["activity"] == "Natural gas"  # canonicalised from "NAT GAS"
    assert first["quantity"] == 6354.47        # "Consumption (kWh)"
    assert first["unit"] == "kwh"
    assert first["amount"] == 1390.44


def test_scope3_csv_behaviour_is_unchanged():
    result = _run(_SCOPE3)

    assert result["status"] == "ok"
    assert result["confidence"] == 1.0
    assert len(result["extracted_data"]["line_items"]) == 4
    assert result["unresolved"] == []


def test_headers_and_row_identity_are_preserved():
    extracted = _run(_UTILITY_BILL)["extracted_data"]

    assert extracted["source_headers"][0] == "Billing Period Start"
    assert "Consumption (kWh)" in extracted["source_headers"]
    assert all("source_row" in line for line in extracted["line_items"])


def test_unit_price_and_site_columns_are_never_coerced():
    header = _normalise_columns(["Unit Price", "Site Name", "Fuel Consumption (litres)"])

    assert header[0] == ("unit_price", None)     # not an amount
    assert header[1] == ("site_name", None)      # not an activity
    assert header[2] == ("quantity", "litres")   # longest alias segment wins


def test_single_letter_unit_segment_does_not_match_inside_a_word():
    # "Total" must not be read as a litre column just because it contains an "l".
    assert _normalise_columns(["Total"])[0] == ("amount", None)
    assert _normalise_columns(["Volume (L)"])[0] == ("quantity", "litres")


def test_rows_without_a_quantity_column_do_not_fabricate_one():
    content = b"Category,Description,Cost (\xc2\xa3)\nHotel,Dublin stay,350.00\n"
    result = extract_document(content, "no_quantity.csv", "text/csv")

    line = result["extracted_data"]["line_items"][0]
    # With two mapped activity columns the LAST one wins (pre-existing rule):
    # `Category` = "Hotel", `Description` = "Dublin stay". Both are source-faithful.
    assert line["activity"] == "Dublin stay"
    assert line["amount"] == 350.0
    # spend-only line: quantity mirrors the amount (pre-existing spend-based rule)
    assert line["quantity"] == 350.0
    assert line["unit"] == "GBP"
    assert result["status"] == "ok"


def _workbook_bytes() -> bytes:
    """A cover-sheet-first workbook: the data lives on the SECOND sheet."""
    workbook = openpyxl.Workbook()
    summary = workbook.active
    summary.title = "Summary"
    summary.append(["Prepared for", "Birmingham Hub"])
    summary.append(["Billing period", "October 2023"])
    readings = workbook.create_sheet("Readings")
    readings.append([
        "Transaction Date", "Vehicle Registration", "Fuel Type",
        "Volume (L)", "Total Cost (£)", "Merchant",
    ])
    readings.append(["01/10/2023", "BV67 FFF", "Diesel (Premium)", 53.8, 85.21, "Esso"])
    readings.append(["02/10/2023", "BV67 HHH", "diesel", 20.96, 32.87, "MOTO Services"])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_xlsx_data_sheet_is_found_behind_a_cover_sheet():
    result = extract_document(
        _workbook_bytes(),
        "fuel_card.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    assert result["status"] == "ok"
    assert result["method"] == "xlsx"
    extracted = result["extracted_data"]
    assert extracted["source_sheet"] == "Readings"
    assert extracted["sheet_names"] == ["Summary", "Readings"]
    assert len(extracted["line_items"]) == 2
    assert extracted["line_items"][0]["quantity"] == 53.8
    assert extracted["line_items"][0]["unit"] == "litres"
    assert extracted["line_items"][0]["activity"] == "Diesel"
    assert extracted["source_headers"][2] == "Fuel Type"


def test_xlsx_is_never_treated_as_a_pdf_or_image():
    result = extract_document(_workbook_bytes(), "fuel_card.xlsx", "")

    assert result["method"] == "xlsx"
    assert result["status"] == "ok"
    assert result["page_count"] == 0
    assert "line_items" in result["extracted_data"]

