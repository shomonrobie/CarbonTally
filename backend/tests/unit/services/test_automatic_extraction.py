"""Unit tests for the automatic extraction parser (CL-56)."""
from __future__ import annotations

import io

import openpyxl

from services.automatic_extraction import extract_document


def _gas_xlsx() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Gas"
    ws.append(["Date", "Supplier", "Description", "Consumption (m3)", "Amount"])
    ws.append(["01/01/2025", "National Grid", "Business gas consumption", 4200, 2100.00])
    ws.append(["01/02/2025", "National Grid", "Business gas consumption", 3850, 1925.00])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestCsvExtraction:
    def test_diesel_csv_line_items(self) -> None:
        content = (
            "Date,Supplier,Category,Quantity (litres),Amount,Currency\n"
            "05/01/2025,Shell Fleet Solutions,Diesel fuel,1250,1775.00,GBP\n"
            "12/01/2025,BP Fuel Cards,Diesel fuel,980,1421.00,GBP\n"
        ).encode("utf-8")
        result = extract_document(content, "fleet.csv", "text/csv")
        assert result["status"] == "ok"
        assert result["method"] == "csv"
        assert result["confidence"] == 1.0
        lines = result["extracted_data"]["line_items"]
        assert len(lines) == 2
        assert lines[0]["activity"] == "Diesel"
        assert lines[0]["unit"] == "litres"
        assert lines[0]["quantity"] == 1250.0
        assert lines[0]["supplier"] == "Shell Fleet Solutions"
        assert result["extracted_data"]["supplier"] == "Shell Fleet Solutions"

    def test_spend_based_csv_uses_currency_unit(self) -> None:
        content = (
            "Date,Supplier,Category,Amount,Currency\n"
            "10/01/2025,Carbon Advisors Ltd,Consulting services,12500.00,GBP\n"
        ).encode("utf-8")
        result = extract_document(content, "spend.csv", "text/csv")
        lines = result["extracted_data"]["line_items"]
        assert result["confidence"] == 1.0
        assert lines[0]["activity"] == "Consulting services"
        assert lines[0]["unit"] == "GBP"
        assert lines[0]["quantity"] == 12500.0


class TestXlsxExtraction:
    def test_gas_xlsx_with_unit_embedded_header(self) -> None:
        result = extract_document(
            _gas_xlsx(),
            "gas.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        assert result["status"] == "ok"
        assert result["confidence"] == 1.0
        lines = result["extracted_data"]["line_items"]
        assert len(lines) == 2
        assert lines[0]["activity"] == "Natural gas"
        assert lines[0]["unit"] == "m3"
        assert lines[0]["quantity"] == 4200.0


class TestUnsupported:
    def test_unknown_type_is_unsupported_not_raised(self) -> None:
        result = extract_document(b"hello", "notes.txt", "text/plain")
        assert result["status"] == "unsupported"
        assert result["confidence"] == 0.0

    def test_empty_input_is_no_text(self) -> None:
        result = extract_document(b"", "blank.csv", "text/csv")
        assert result["status"] in ("no_text", "unsupported")
