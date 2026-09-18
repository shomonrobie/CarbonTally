"""033 Slice 1 (D-F) — the document's own invoice_number travels onto multi-line line items.

No new field: the existing deterministic extraction establishes `invoice_number`
(services/automatic_extraction.py aliases + promotion; engines/extraction.py regex), and the P1
multi-line path now carries that same value onto every line item so the existing provenance chain
can resolve it per row. Absence must change nothing (backward compatible).
"""
from __future__ import annotations

import pytest

from services import extraction_fidelity as p1

MULTI_FUEL = (
    "Pure Energy PLC\n"
    "Ref No.: PWR/2026/8130\n"
    "Date: May 08, 2026\n"
    "Description Qty Unit Rate Subtotal\n"
    "Gas usage 5,362.2000 kWh €0.0670 €359.2700\n"
    "Diesel supply 4,434.4000 L €1.6190 €7,179.2900\n"
    "Waste disposal 60 t €105.8140 €6,348.8400\n"
    "Water supply 163.2000 m³ €2.0130 €328.5200\n"
    "Power consumption 24,620.5000 kWh €0.1710 €4,210.1100\n"
    "Subtotal: €18,426.0300\n"
)
INVOICE = "PWR/2026/8130"


def test_invoice_number_is_carried_onto_every_line_item() -> None:
    items, coverage = p1.build_line_items(
        MULTI_FUEL, method="pdf_text", page_count=2, invoice_number=INVOICE
    )
    assert coverage["candidate_lines"] == 5 and len(items) == 5
    assert [item["invoice_number"] for item in items] == [INVOICE] * 5
    # the existing per-row provenance is untouched by the addition
    assert [item["line_number"] for item in items] == [1, 2, 3, 4, 5]
    assert all(item["source_line"] for item in items)
    assert all(item["quantity"] is not None and item["unit"] for item in items)


def test_absence_of_an_invoice_number_changes_nothing() -> None:
    with_invoice, _ = p1.build_line_items(
        MULTI_FUEL, method="pdf_text", page_count=2, invoice_number=INVOICE
    )
    without, coverage = p1.build_line_items(MULTI_FUEL, method="pdf_text", page_count=2)
    assert coverage["candidate_lines"] == 5
    assert len(without) == len(with_invoice) == 5
    assert all("invoice_number" not in item for item in without)
    # identical in every other respect
    stripped = [
        {k: v for k, v in item.items() if k != "invoice_number"} for item in with_invoice
    ]
    assert stripped == without


def test_blank_invoice_number_is_not_recorded() -> None:
    items, _ = p1.build_line_items(
        MULTI_FUEL, method="pdf_text", page_count=2, invoice_number="   "
    )
    # falsy values must not create a field that the provenance chain would then resolve as ""
    assert all("invoice_number" not in item for item in items)


def test_single_line_document_is_unchanged() -> None:
    items, _ = p1.build_line_items(
        "Electricity supply 12,500 kWh 2,340.00\n",
        method="pdf_text",
        page_count=1,
        invoice_number=INVOICE,
    )
    assert len(items) == 1
    assert items[0]["invoice_number"] == INVOICE
    assert items[0]["quantity"] == 12500.0
