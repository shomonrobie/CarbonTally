"""Deterministic OCR → field-suggestion unit tests (human-reviewed pre-fill).

Verifies the adapter contract:
- clean documents suggest the supported V3 extracted_data fields;
- missing/ambiguous fields stay UNRESOLVED (never fabricated);
- malformed OCR / garbage text yields empty suggestions, not invented values;
- suggestions have no status/event side effects (they never auto-approve).
"""
from __future__ import annotations

from services.extraction_suggestions import suggest

_CLEAN = (
    "Supplier: Meridian Fuel Supplies Ltd\n"
    "Invoice number: INV-2026-0417\n"
    "Invoice date: 15/01/2026\n"
    "Electricity consumption: 12500 kWh\n"
    "Net amount: 3125.00 GBP\n"
    "Total amount: 3750.00 GBP\n"
)


def test_suggest_parses_clean_invoice():
    out = suggest(_CLEAN)
    assert out["suggested"] is True
    assert out["engine"] == "deterministic_v1"
    d = out["suggested_data"]
    assert d["supplier"] == "Meridian Fuel Supplies Ltd"
    assert d["invoice_number"] == "INV-2026-0417"
    assert d["date"] == "15/01/2026"
    assert d["quantity"] == 12500.0
    assert d["unit"] == "kWh"
    assert d["activity"] == "Electricity"
    assert out["unresolved"] == []


def test_suggest_gas_invoice_activity():
    text = (
        "Supplier: Eco Gas Plc\n"
        "Invoice number: INV-9\n"
        "Invoice date: 01/02/2026\n"
        "Natural gas usage: 500 m3\n"
    )
    out = suggest(text)
    assert out["suggested_data"]["activity"] == "Natural gas"
    assert out["suggested_data"]["quantity"] == 500.0
    assert out["suggested_data"]["unit"] == "m3"


def test_suggest_missing_fields_leave_unresolved():
    # No supplier, no invoice number, no quantity/unit, no activity keyword.
    text = "We hope you enjoyed your stay. Please remit 42.00 soon.\n"
    out = suggest(text)
    assert out["suggested_data"] == {}
    assert "supplier" in out["unresolved"]
    assert "invoice_number" in out["unresolved"]
    assert "date" in out["unresolved"]
    assert "quantity/unit" in out["unresolved"]
    assert "activity" in out["unresolved"]


def test_suggest_quantity_not_invented():
    # Supplier present but NO quantity-like value -> quantity/unit unresolved.
    text = (
        "Supplier: ABC Ltd\n"
        "Invoice date: 01/02/2026\n"
        "Electricity account summary attached.\n"
    )
    out = suggest(text)
    d = out["suggested_data"]
    assert "quantity" not in d
    assert "unit" not in d
    assert "quantity/unit" in out["unresolved"]
    # Activity still derived from text keyword (Electricity) - deterministic.
    assert d.get("activity") == "Electricity"


def test_suggest_no_fabrication_on_garbage():
    text = "asdf qwerty !!!! 12345 zzz yyy"
    out = suggest(text)
    assert out["suggested_data"] == {}
    assert len(out["unresolved"]) >= 4


def test_suggest_empty_text():
    out = suggest("")
    assert out["suggested_data"] == {}
    assert set(out["unresolved"]) == {
        "supplier", "invoice_number", "date", "quantity", "unit", "activity",
    }


def test_suggest_fields_has_no_status_side_effects():
    """suggest_fields must not transition any document status (no auto-approval)."""
    from engines.extraction import DocumentExtractionEngine

    class _RecordingSink:
        def __init__(self):
            self.updates = []

        async def update_status(self, doc_id, status):
            self.updates.append((doc_id, status))
            return None

    sink = _RecordingSink()
    engine = DocumentExtractionEngine(sink)
    fields = engine.suggest_fields(_CLEAN)
    assert fields["supplier"] == "Meridian Fuel Supplies Ltd"
    assert sink.updates == []  # no status transition was performed
