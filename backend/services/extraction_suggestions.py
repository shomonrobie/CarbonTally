"""Deterministic OCR → structured field suggestions (human-reviewed pre-fill).

The V3 workflow treats OCR/extraction as HUMAN-REVIEWED: the engine may suggest
values, but they are never automatically approved or written into
``manual_extraction_items.extracted_data``. This module is the small adapter
between raw OCR text and a **suggested** ``extracted_data``-shaped dict.

Reuse rules (per the Product Owner decision register and the extraction
audits):

- The deterministic field pass is the existing
  :class:`engines.extraction.DocumentExtractionEngine` (generic ``Key: value``
  + named patterns) — not a new extraction system.
- Only fields that can be validly parsed are suggested. Missing/ambiguous
  fields are listed in ``unresolved`` — never fabricated.
- The output carries ``suggested: true`` and must be surfaced only as a
  pre-fill reference; confirmation happens through the existing extraction
  review API (``POST .../items/{id}/extract``).
"""
from __future__ import annotations

import re
from typing import Any

from engines.extraction import DocumentExtractionEngine
from engines import invoice_extraction


#: The engine needs a document sink for construction only; suggestions never
#: touch document status, so a no-op sink is safe.
class _NoopSink:
    async def update_status(self, doc_id: str, status: str) -> Any:
        return None


_ENGINE = DocumentExtractionEngine(_NoopSink())

#: Known activity labels derived deterministically from text keywords. Order
#: matters — the first match wins (most-specific first).
_ACTIVITY_KEYWORDS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Natural gas", re.compile(r"\bnatural\s+gas\b", re.IGNORECASE)),
    ("Electricity", re.compile(r"\belectricity\b|\belectrical\b|\bmpan\b", re.IGNORECASE)),
    ("Diesel", re.compile(r"\bdiesel\b", re.IGNORECASE)),
    ("Petrol", re.compile(r"\bpetrol\b|\bgasoline\b|\bunleaded\b", re.IGNORECASE)),
    ("Waste", re.compile(r"\bwaste\b|\brecycl|\brefuse\b|\blandfill\b|\bcompost", re.IGNORECASE)),
    ("Water", re.compile(r"\bwater\b", re.IGNORECASE)),
    ("Travel", re.compile(r"\btravel\b|\bhotel\b|\brail\b|\bflight\b", re.IGNORECASE)),
)

#: Units the quantity parser accepts (lowercased). Conservative set aligned
#: with CarbonTally's factor units; anything else stays unresolved.
_KNOWN_UNITS = {
    "kwh", "mwh", "m3", "m³", "litres", "liters", "litre", "liter", "l",
    "tonnes", "tons", "tonne", "ton", "t", "kg", "miles", "km", "mile", "grosscv",
}

_NUMBER_UNIT_RE = re.compile(r"(?P<qty>\d[\d,]*(?:\.\d+)?)\s*(?P<unit>[a-zA-Z³0-9]+)")

#: Mapping of engine field names → V3 extracted_data keys (subset of the
#: schema used by the processing workflow; nothing new is invented).
#: P12-IMPL-01 adds the header/period/tax vocabulary the canonical invoice class
#: requires (customer, billing period, document VAT) — all JSONB keys in the
#: existing ``extracted_data`` contract, so no schema change is involved.
_FIELD_ALIASES: dict[str, str] = {
    "supplier": "supplier",
    "invoice_number": "invoice_number",
    "date": "date",
    "invoice_date": "date",
    "customer": "customer",
    "billing_period": "billing_period",
    "net_amount": "net_amount",
    "net_total": "net_amount",
    "vat_amount": "vat_amount",
    "gross_amount": "gross_amount",
    "total_amount": "gross_amount",
    "gross_total": "gross_amount",
    "currency": "currency",
    "billing_currency": "currency",
}


def _suggest_quantity_unit(fields: dict[str, str]) -> tuple[Any, str | None, list[str]]:
    """Find a ``quantity``/``unit`` pair from the field values.

    Prefers an explicit quantity-like field (``consumption``, ``quantity``,
    ``usage``); otherwise scans every field value for a ``<number> <unit>``
    pattern where the unit is in :data:`_KNOWN_UNITS`. Returns
    ``(quantity, unit, unresolved_notes)``; never fabricates a value.
    """
    quantity_fields = [
        v for k, v in fields.items()
        if "consumption" in k or k in ("quantity", "usage", "volume")
    ]
    candidates: list[tuple[Any, str]] = []
    for value in quantity_fields or list(fields.values()):
        for m in _NUMBER_UNIT_RE.finditer(value):
            unit = m.group("unit").strip().lower()
            if unit in _KNOWN_UNITS:
                try:
                    qty = float(m.group("qty").replace(",", ""))
                except ValueError:
                    continue
                candidates.append((qty, m.group("unit").strip()))
        if candidates:
            break
    if not candidates:
        return None, None, ["quantity/unit"]
    qty, unit = candidates[0]
    return qty, unit, []


def suggest(text: str) -> dict[str, Any]:
    """Deterministic field suggestions for ``text``.

    Returns::

        {"suggested": True, "engine": "deterministic_v1",
         "suggested_data": {<v3 extracted_data keys that could be parsed>},
         "unresolved": [<field names that could not be determined>]}

    ``suggested_data`` is a SUGGESTION — the caller must not write it into
    ``manual_extraction_items.extracted_data`` without human confirmation.
    """
    if not text or not text.strip():
        return {
            "suggested": True,
            "engine": "deterministic_v1",
            "suggested_data": {},
            "unresolved": ["supplier", "invoice_number", "date", "quantity", "unit", "activity"],
        }

    fields = _ENGINE.suggest_fields(text)
    suggested: dict[str, Any] = {}
    unresolved: list[str] = []
    evidence: dict[str, Any] = {}

    for engine_field, target in _FIELD_ALIASES.items():
        value = fields.get(engine_field)
        if value and value.strip():
            suggested.setdefault(target, value.strip())

    # P12-IMPL-01: reference-labelled invoices (``Ref:``) supply the invoice
    # number only when no explicit invoice label was printed.
    if "invoice_number" not in suggested:
        reference = (fields.get("invoice_ref") or "").strip()
        if reference:
            suggested["invoice_number"] = reference
            evidence["invoice_number_source"] = "reference_label"

    # P12-IMPL-01: supplier — labelled pattern first, then the guarded
    # document-header strategy. Uncertain headers stay unresolved.
    if "supplier" in suggested:
        evidence["supplier_source"] = "labelled"
    else:
        supplier_name, supplier_evidence = invoice_extraction.extract_supplier_header(text)
        evidence["supplier_header"] = supplier_evidence
        if supplier_name:
            suggested["supplier"] = supplier_name
            evidence["supplier_source"] = "document_header"

    # P12-IMPL-01: normalise the printed date to ISO, preserving the raw value.
    printed_date = (suggested.get("date") or "").strip()
    if printed_date:
        iso_date = invoice_extraction.parse_date(printed_date)
        suggested["date_raw"] = printed_date
        if iso_date:
            suggested["date"] = iso_date
        else:
            suggested.pop("date", None)

    # P12-IMPL-01: billing period → explicit start/end; an end date is never
    # invented (both ends must parse).
    printed_period = (suggested.get("billing_period") or "").strip()
    suggested.pop("billing_period", None)
    if printed_period:
        period_start, period_end = invoice_extraction.parse_period(printed_period)
        if period_start and period_end:
            suggested["billing_period_start"] = period_start
            suggested["billing_period_end"] = period_end
            suggested["billing_period_raw"] = printed_period

    # P12-IMPL-01: item-table rows (deterministic, fail-closed).
    line_items = invoice_extraction.extract_invoice_lines(text)
    document_activity = next(
        (label for label, pattern in _ACTIVITY_KEYWORDS if pattern.search(text)), None
    )
    lines_cover_required = False
    if line_items:
        for item in line_items:
            item["activity"] = next(
                (
                    label
                    for label, pattern in _ACTIVITY_KEYWORDS
                    if pattern.search(item["description"])
                ),
                document_activity,
            )
        suggested["line_items"] = line_items
        evidence["line_item_count"] = len(line_items)
        lines_cover_required = all(
            str(item.get(field) or "").strip()
            for item in line_items
            for field in ("activity", "quantity", "unit")
        )

    if "supplier" not in suggested:
        unresolved.append("supplier")
    if "invoice_number" not in suggested:
        unresolved.append("invoice_number")
    if "date" not in suggested:
        unresolved.append("date")
    if "billing_period_start" not in suggested:
        unresolved.append("billing_period")

    quantity, unit, q_unresolved = _suggest_quantity_unit(fields)
    if lines_cover_required:
        # activity/quantity/unit are resolved per line: reporting them as
        # document-level ``unresolved`` would misstate the extraction, and
        # inventing a single document-level quantity from multi-line data would
        # fabricate a value.
        suggested.pop("quantity", None)
        suggested.pop("unit", None)
    else:
        if q_unresolved:
            unresolved.extend(q_unresolved)
        else:
            suggested["quantity"] = quantity
            suggested["unit"] = unit
        if document_activity:
            suggested["activity"] = document_activity
        else:
            unresolved.append("activity")

    if evidence:
        suggested["extraction_evidence"] = evidence

    return {
        "suggested": True,
        "engine": "deterministic_v1",
        "suggested_data": suggested,
        "unresolved": sorted(set(unresolved)),
    }
