"""P12-IMPL-01 — PDF extraction foundation unit tests.

Covers the deterministic invoice header + item-table parsing introduced by
P12-IMPL-01 (§29 A): supplier header strategy, customer vocabulary, date
normalisation, billing periods, table detection, quantity/unit/rate/net
extraction, total/footer exclusion, VRM/currency exclusion, and fail-closed
behaviour.

Nothing here reads the canonical oracle: the extractor must work from the
document text alone (P12-IMPL-01 §37).
"""
from __future__ import annotations

import pytest

from engines import invoice_extraction as ix
from services import extraction_suggestions as es


# ── supplier document-header strategy ────────────────────────────────────────

LABELLED = "Supplier: Acme Waste Ltd\nInvoice #: X1\nDate: 2025-01-01\n"

CANONICAL_UNLABELLED = (
    "Robinsons Recycling Services Ltd\n"
    "850 Green Lane\n"
    "Sheffield\n"
    "QI14 5ZD\n"
    "UK\n"
    "WASTE INVOICE\n"
    "Invoice #: SVC2025008717\n"
)


def test_supplier_labelled_pattern_wins():
    out = es.suggest(LABELLED)
    data = out["suggested_data"]
    assert data["supplier"] == "Acme Waste Ltd"
    assert data["extraction_evidence"]["supplier_source"] == "labelled"


def test_supplier_unlabelled_document_header_is_detected():
    name, evidence = ix.extract_supplier_header(CANONICAL_UNLABELLED)
    assert name == "Robinsons Recycling Services Ltd"
    assert evidence["selected"] == name
    assert evidence["candidates"]


def test_supplier_uncertain_header_stays_unresolved():
    # A bare word with no company evidence and no address block must not become a supplier.
    text = "n\n\nINVOICE\nInvoice #: X1\n"
    name, evidence = ix.extract_supplier_header(text)
    assert name is None
    assert "supplier" in es.suggest(text)["unresolved"]


def test_supplier_missing_is_reported_unresolved():
    out = es.suggest("Date: 2025-01-01\nInvoice #: X1\n")
    assert "supplier" not in out["suggested_data"]
    assert "supplier" in out["unresolved"]


def test_supplier_after_document_title_stays_unresolved_fail_closed():
    """A sender *after* the document-type marker is not asserted: the strategy
    only accepts a supplier inside the pre-marker header block, so a title-first
    layout stays unresolved rather than being guessed."""
    text = "TAX INVOICE\nACME LTD\n1 High Street\nLeeds\nLS1 1AA\n"
    name, evidence = ix.extract_supplier_header(text)
    assert name is None
    assert evidence["strategy"] == "header_block"
    assert "supplier" in es.suggest(text)["unresolved"]


# ── customer vocabulary (document content only) ──────────────────────────────

@pytest.mark.parametrize(
    "label", ["Buyer", "Customer", "Client", "Recipient", "Bill To", "Sold To"]
)
def test_customer_labels(label):
    out = es.suggest(f"{label}: Sustainable Direct Group\nInvoice #: X1\n")
    assert out["suggested_data"]["customer"] == "Sustainable Direct Group"


def test_customer_missing_unresolved():
    out = es.suggest("Supplier: Acme Ltd\nInvoice #: X1\n")
    assert "customer" not in out["suggested_data"]


def test_customer_is_not_treated_as_tenant():
    # The printed customer is document content; extraction must not invent linkage.
    out = es.suggest("Customer: Sustainable Direct Group\nInvoice #: X1\n")
    data = out["suggested_data"]
    assert data["customer"] == "Sustainable Direct Group"
    assert "organization_id" not in data and "tenant_id" not in data


# ── date normalisation ──────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "printed,expected",
    [
        ("2025-04-02", "2025-04-02"),
        ("02-04-2025", "2025-04-02"),          # day-first (UK convention)
        ("Feb 02, 2026", "2026-02-02"),
        ("2 February 2026", "2026-02-02"),
        ("03-07-2025", "2025-07-03"),
    ],
)
def test_parse_date_normalises(printed, expected):
    assert ix.parse_date(printed) == expected


@pytest.mark.parametrize("bad", ["", "not a date", "32-13-2025", "2025-13-01", None])
def test_parse_date_rejects_uncertain(bad):
    assert ix.parse_date(bad) is None


def test_invoice_date_raw_is_preserved():
    out = es.suggest("Date: Feb 02, 2026\nInvoice #: X1\n")
    data = out["suggested_data"]
    assert data["date"] == "2026-02-02"
    assert data["date_raw"] == "Feb 02, 2026"


# ── billing period ──────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "printed,start,end",
    [
        ("2025-03-01 – 2025-03-31", "2025-03-01", "2025-03-31"),
        ("2025-02-01 – 2025-02-28", "2025-02-01", "2025-02-28"),
        ("01-06-2025 – 30-06-2025", "2025-06-01", "2025-06-30"),
        ("Jan 01, 2026 – Jan 31, 2026", "2026-01-01", "2026-01-31"),
        ("2025-12-01 - 2026-01-31", "2025-12-01", "2026-01-31"),  # year boundary
    ],
)
def test_period_ranges(printed, start, end):
    assert ix.parse_period(printed) == (start, end)


@pytest.mark.parametrize("bad", ["", "2025-03-01", "1 March 2025 to", " – ", "garbage"])
def test_period_never_invents_an_end(bad):
    assert ix.parse_period(bad) == (None, None)


def test_billing_period_label_variants():
    for label in ("Period", "Billing", "Reporting Period", "Service Period"):
        out = es.suggest(f"{label}: 2025-03-01 – 2025-03-31\nInvoice #: X1\n")
        data = out["suggested_data"]
        assert data["billing_period_start"] == "2025-03-01"
        assert data["billing_period_end"] == "2025-03-31"
        assert data["billing_period_raw"].startswith("2025-03-01")


# ── item table: detection, rows, fields ─────────────────────────────────────

ITEM_TABLE = (
    "Robinsons Recycling Services Ltd\n"
    "850 Green Lane\n"
    "Sheffield\n"
    "QI14 5ZD\n"
    "UK\n"
    "WASTE INVOICE\n"
    "Invoice #: SVC2025008717\n"
    "Date: 2025-04-02\n"
    "Buyer: Sustainable Direct Group\n"
    "Period: 2025-03-01 – 2025-03-31\n"
    "Description Qty Unit Rate Subtotal\n"
    "Recycling services - Mixed 90 tonnes £107.64 £9,687.51\n"
    "Waste disposal - General 64 tonnes £190.22 £12,174.21\n"
    "Waste disposal - Mixed 58 tonnes £100.22 £5,812.76\n"
    "Subtotal: £27,674.48\n"
    "VAT (20%): £5,534.89\n"
    "Total: £33,209.37\n"
    "Terms: Net 30 days.\n"
)


def test_no_table_header_means_no_lines():
    assert ix.extract_invoice_lines("Description only\nno table here\n") == []


def test_line_items_are_extracted_with_all_fields():
    rows = ix.extract_invoice_lines(ITEM_TABLE)
    assert len(rows) == 3
    first = rows[0]
    assert first["description"] == "Recycling services - Mixed"
    assert first["quantity"] == 90.0
    assert first["unit"] == "tonnes"
    assert first["unit_price"] == 107.64
    assert first["net_amount"] == 9687.51
    assert first["line_number"] == 1
    assert first["extraction_method"] == "det:pdf_table"
    assert first["source_line"].startswith("Recycling services - Mixed")
    assert first["arithmetic_ok"] is True


def test_description_is_preserved_in_full():
    rows = ix.extract_invoice_lines(ITEM_TABLE)
    assert rows[0]["description"] == "Recycling services - Mixed"


@pytest.mark.parametrize(
    "footer",
    [
        "Subtotal: £100.00",
        "Net Amount: £100.00",
        "Net Total: £100.00",
        "Net Payable: £120.00",
        "VAT: £20.00",
        "VAT (20%): £20.00",
        "GST: £20.00",
        "Tax (20%): £20.00",
        "Total: £120.00",
        "Total Due: £120.00",
        "Payment Information:",
        "Bank: Barclays",
        "Sort Code: 98-49-16",
        "Account Number: 65033104",
        "Page 1",
    ],
)
def test_total_and_footer_rows_are_never_line_items(footer):
    text = (
        "WASTE INVOICE\nInvoice #: X1\n"
        "Description Qty Unit Rate Amount\n"
        "Waste disposal - Mixed 10 tonnes £100.00 £1,000.00\n"
        f"{footer}\n"
    )
    rows = ix.extract_invoice_lines(text)
    assert len(rows) == 1
    assert rows[0]["description"] == "Waste disposal - Mixed"


def test_vrm_or_postcode_text_never_becomes_a_line():
    text = (
        "Robinsons Recycling Services Ltd\n"
        "193 Renewable Road\n"
        "Glasgow\n"
        "MH82 2KM\n"
        "UK\n"
        "WASTE INVOICE\n"
        "Ref: INV1\n"
        "Description Qty Unit Rate Amount\n"
        "Waste collection - General 5 tonnes £65 £297\n"
        "Waste disposal - Organic 43 tonnes £117 £5,021\n"
    )
    rows = ix.extract_invoice_lines(text)
    assert [r["description"] for r in rows] == [
        "Waste collection - General",
        "Waste disposal - Organic",
    ]


def test_currency_token_is_never_a_unit():
    """The measured P1 defect: `GBP` must never be accepted as a unit."""
    assert ix.canonical_unit("GBP") is None
    assert ix.canonical_unit("£") is None
    assert ix.canonical_unit("eur") is None
    text = (
        "Description Qty Unit Rate Amount\n"
        "Waste disposal - Mixed 10 GBP 100.00 1,000.00\n"
    )
    assert ix.extract_invoice_lines(text) == []


def test_unknown_unit_is_rejected():
    text = (
        "Description Qty Unit Rate Amount\n"
        "Waste disposal - Mixed 10 widgets 100.00 1,000.00\n"
    )
    assert ix.extract_invoice_lines(text) == []


@pytest.mark.parametrize(
    "token,expected",
    [("t", "tonnes"), ("tonnes", "tonnes"), ("tonne", "tonnes"),
     ("kg", "kg"), ("kWh", "kwh")],
)
def test_unit_canonicalisation(token, expected):
    assert ix.canonical_unit(token) == expected


def test_rounded_document_values_are_kept_and_flagged_not_rewritten():
    """A document printing rounded figures: values kept, arithmetic flagged."""
    text = (
        "Description Qty Unit Rate Amount\n"
        "Waste collection - General 5 tonnes £65 £297\n"
    )
    rows = ix.extract_invoice_lines(text)
    assert rows[0]["quantity"] == 5.0       # the printed value, not an oracle value
    assert rows[0]["net_amount"] == 297.0
    assert rows[0]["arithmetic_ok"] is False
    assert rows[0]["arithmetic_deviation"] == pytest.approx(28.0)


def test_multi_decimal_values_are_preserved():
    text = (
        "Description Qty Unit Rate Net Amount\n"
        "Recycling services - Organic 41.9800 tonnes £93.8210 £3,938.6100\n"
    )
    row = ix.extract_invoice_lines(text)[0]
    assert (row["quantity"], row["unit_price"], row["net_amount"]) == (41.98, 93.821, 3938.61)


def test_second_table_header_variant_is_supported():
    for header in (
        "Description Qty Unit Rate Subtotal",
        "Description Qty Unit Rate Net Amount",
        "Description Qty Unit Rate Net Total",
        "Description Qty Unit Rate Amount",
    ):
        text = f"{header}\nWaste disposal - Mixed 10 tonnes 100.00 1,000.00\n"
        assert len(ix.extract_invoice_lines(text)) == 1


# ── adapter integration ─────────────────────────────────────────────────────

def test_suggest_reports_line_items_and_required_evidence():
    out = es.suggest(ITEM_TABLE)
    data = out["suggested_data"]
    assert data["supplier"] == "Robinsons Recycling Services Ltd"
    assert data["customer"] == "Sustainable Direct Group"
    assert data["invoice_number"] == "SVC2025008717"
    assert data["date"] == "2025-04-02"
    assert data["billing_period_start"] == "2025-03-01"
    assert len(data["line_items"]) == 3
    # activity/quantity/unit are resolved per line — not reported unresolved,
    # and no single document-level quantity is fabricated from multi-line data.
    assert out["unresolved"] == []
    assert "quantity" not in data and "unit" not in data


def test_suggest_keeps_scalar_quantity_when_no_table_exists():
    out = es.suggest("Electricity\nConsumption: 1200 kWh\nInvoice #: X1\nDate: 2025-01-01\n")
    data = out["suggested_data"]
    assert data["quantity"] == 1200.0
    assert data["unit"] == "kWh"
    assert "line_items" not in data


def test_reference_label_is_a_fallback_only():
    with_ref = es.suggest("Ref: SVC2024-8258\nDate: 2025-03-05\n")
    assert with_ref["suggested_data"]["invoice_number"] == "SVC2024-8258"
    explicit = es.suggest("Invoice #: EXPLICIT-1\nRef: OTHER-2\n")
    assert explicit["suggested_data"]["invoice_number"] == "EXPLICIT-1"


def test_vat_number_is_not_a_vat_amount():
    out = es.suggest("VAT No: GB 963 5089 35\nInvoice #: X1\nVAT (20%): £20.00\n")
    assert out["suggested_data"]["vat_amount"] == "£20.00"


def test_no_document_specific_hard_coding():
    """The parser is structural: an unrelated supplier parses the same way."""
    text = (
        "Another Waste Co Ltd\n"
        "1 Other Road\n"
        "Bristol\n"
        "BS1 1AA\n"
        "UK\n"
        "TAX INVOICE\n"
        "Invoice #: ZZ9\n"
        "Customer: Somebody Else PLC\n"
        "Description Qty Unit Rate Amount\n"
        "General waste 12.5 t £90.00 £1,125.00\n"
    )
    data = es.suggest(text)["suggested_data"]
    assert data["supplier"] == "Another Waste Co Ltd"
    assert data["customer"] == "Somebody Else PLC"
    assert data["invoice_number"] == "ZZ9"
    assert len(data["line_items"]) == 1
    assert data["line_items"][0]["unit"] == "tonnes"

