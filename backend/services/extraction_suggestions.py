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
    ("Waste", re.compile(r"\bwaste\b", re.IGNORECASE)),
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
_FIELD_ALIASES: dict[str, str] = {
    "supplier": "supplier",
    "invoice_number": "invoice_number",
    "date": "date",
    "invoice_date": "date",
    "net_amount": "net_amount",
    "net_total": "net_amount",
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

    for engine_field, target in _FIELD_ALIASES.items():
        value = fields.get(engine_field)
        if value and value.strip():
            suggested.setdefault(target, value.strip())
    if "supplier" not in suggested:
        unresolved.append("supplier")
    if "invoice_number" not in suggested:
        unresolved.append("invoice_number")
    if "date" not in suggested:
        unresolved.append("date")

    quantity, unit, q_unresolved = _suggest_quantity_unit(fields)
    if q_unresolved:
        unresolved.extend(q_unresolved)
    else:
        suggested["quantity"] = quantity
        suggested["unit"] = unit

    activity = next(
        (label for label, pattern in _ACTIVITY_KEYWORDS if pattern.search(text)),
        None,
    )
    if activity:
        suggested["activity"] = activity
    else:
        unresolved.append("activity")

    return {
        "suggested": True,
        "engine": "deterministic_v1",
        "suggested_data": suggested,
        "unresolved": sorted(set(unresolved)),
    }
