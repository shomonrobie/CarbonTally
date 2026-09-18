"""Automatic document extraction (V3 Phase A / CL-56).

Deterministic file → ``extracted_data`` conversion for the automatic pipeline.
No database access; pure parsing. Returns a JSON-safe summary with the method,
a 0..1 completeness/confidence score, the suggested fields and the list of
fields the extractor could not resolve.

Supported inputs
----------------
* **PDF** — digital text via pdfplumber, falling back to Tesseract OCR for
  scanned pages (the historical recovery fixes), then the deterministic
  field-suggestion pass (:mod:`services.extraction_suggestions`).
* **IMAGE** — Tesseract OCR then the same suggestion pass.
* **CSV / XLSX** — tabular parsing into ``line_items`` with per-row
  activity/quantity/unit/supplier/date/amount where the columns allow it;
  currency amounts without a unit column become spend-based lines.

Output shape::

    {"status": "ok"|"no_text"|"unsupported"|"error",
     "method": str, "page_count": int, "extracted_data": dict,
     "unresolved": list[str], "confidence": float}

``confidence`` is the fraction of the required pipeline fields
(activity/quantity/unit) resolved, so the worker's confidence gate can route
low-completeness extractions to the manual-review gate. ``extracted_data`` is a
SUGGESTION for single-line documents (human-review pre-fill) and a
line-item table for tabular documents — the automatic pipeline treats it as
confirmed only when the gate passes.
"""
from __future__ import annotations

import io
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from core.logging import get_logger
from services.extraction_suggestions import suggest as suggest_text

logger = get_logger(__name__)

#: Required pipeline fields used to compute the completeness/confidence score.
_REQUIRED = ("activity", "quantity", "unit")

#: Activity keywords reused by the tabular parsers (same labels as the
#: deterministic suggestion pass).
_ACTIVITY_KEYWORDS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Natural gas", re.compile(r"natural\s+gas|gas\b", re.IGNORECASE)),
    ("Electricity", re.compile(r"electricity|electrical|mpan", re.IGNORECASE)),
    ("Diesel", re.compile(r"diesel|red\s+diesel", re.IGNORECASE)),
    ("Petrol", re.compile(r"petrol|gasoline|unleaded", re.IGNORECASE)),
    ("Waste", re.compile(r"waste", re.IGNORECASE)),
    ("Water", re.compile(r"water", re.IGNORECASE)),
    ("Business travel", re.compile(r"travel|hotel|rail|flight|accommodation", re.IGNORECASE)),
)

#: Column-name normalisation → canonical field.
_COLUMN_ALIASES: dict[str, str] = {
    "date": "date",
    "invoice_date": "date",
    "transaction_date": "date",
    "billing_period_start": "date",
    "period_start": "date",
    "reading_date": "date",
    "period": "date",
    "supplier": "supplier",
    "supplier_name": "supplier",
    "vendor": "supplier",
    "merchant": "supplier",
    "category": "activity",
    "activity": "activity",
    "description": "activity",
    "item": "activity",
    "fuel": "activity",
    "fuel_type": "activity",
    "meter_type": "activity",
    "energy_type": "activity",
    "utility_type": "activity",
    "product": "activity",
    "reading_type": "activity",
    "quantity": "quantity",
    "qty": "quantity",
    "consumption": "quantity",
    "volume": "quantity",
    "usage": "quantity",
    "units_used": "quantity",
    "reading": "quantity",
    "kwh": "quantity",
    "unit": "unit",
    "uom": "unit",
    "units_of_measure": "unit",
    "measure": "unit",
    "amount": "amount",
    "cost": "amount",
    "total": "amount",
    "total_cost": "amount",
    "line_total": "amount",
    "spend": "amount",
    "charge": "amount",
    "gross_amount": "amount",
    "net_amount": "amount",
    "currency": "currency",
    "ccy": "currency",
    "invoice_number": "invoice_number",
    "invoice_no": "invoice_number",
    "invoice_ref": "invoice_number",
}

#: Step 2C / POD-3 — segment-aware alias resolution.
#:
#: The pre-V3 readers (``utils/emissions``) accepted the header shapes real
#: supplier exports actually use (``Fuel Type``, ``Volume (L)``,
#: ``Transaction Date``, ``Total Cost (£)``, ``Meter Type``, ``Site Name`` …).
#: The V3 tabular reader originally resolved **exact normalised keys only**, so
#: those columns fell through to unknown fields and the row lost
#: ``activity``/``quantity``/``unit`` entirely — the file parsed, but the job
#: was blocked with a misleadingly empty extraction. These tables restore the
#: intended parity: an exact key wins, then the longest alias **segment**
#: contained in the key.
_ALIAS_SEGMENTS: tuple[tuple[str, str], ...] = (
    ("invoice_number", "invoice_number"),
    ("invoice_ref", "invoice_number"),
    ("transaction_date", "date"),
    ("billing_period_start", "date"),
    ("period_start", "date"),
    ("reading_date", "date"),
    ("invoice_date", "date"),
    ("date", "date"),
    ("period", "date"),
    ("supplier_name", "supplier"),
    ("supplier", "supplier"),
    ("vendor", "supplier"),
    ("merchant", "supplier"),
    ("meter_type", "activity"),
    ("fuel_type", "activity"),
    ("energy_type", "activity"),
    ("utility_type", "activity"),
    ("reading_type", "activity"),
    ("description", "activity"),
    ("category", "activity"),
    ("activity", "activity"),
    ("product", "activity"),
    ("fuel", "activity"),
    ("item", "activity"),
    ("consumption", "quantity"),
    ("volume", "quantity"),
    ("usage", "quantity"),
    ("quantity", "quantity"),
    ("qty", "quantity"),
    ("reading", "quantity"),
    ("units_used", "quantity"),
    ("kwh", "quantity"),
    ("units_of_measure", "unit"),
    ("uom", "unit"),
    ("unit", "unit"),
    ("measure", "unit"),
    ("total_cost", "amount"),
    ("line_total", "amount"),
    ("gross_amount", "amount"),
    ("net_amount", "amount"),
    ("amount", "amount"),
    ("cost", "amount"),
    ("total", "amount"),
    ("spend", "amount"),
    ("charge", "amount"),
    ("currency", "currency"),
    ("ccy", "currency"),
)

#: Columns that must **not** be coerced by segment matching. A unit *price* is
#: not a line amount, and a site/asset identifier is not an activity: mapping
#: them would silently mis-state the row. They are preserved verbatim as their
#: own fields instead.
_ALIAS_EXCLUSIONS: frozenset[str] = frozenset(
    {
        "unit_price",
        "price",
        "price_per_unit",
        "unit_rate",
        "site_name",
        "site",
        "location",
        "vehicle_registration",
        "registration",
        "driver_id",
        "mpan",
        "mprn",
        "meter_id",
        "meter_number",
        "account_number",
    }
)

#: Unit tokens recognised **as whole key segments** (so ``volume_l`` → litres,
#: while ``total`` is never mistaken for a litre column because "l" is not its
#: own segment). Maps the segment to the canonical unit spelling.
_UNIT_SEGMENTS: dict[str, str] = {
    "kwh": "kWh",
    "mwh": "MWh",
    "m3": "m3",
    "m³": "m3",
    "therm": "therms",
    "therms": "therms",
    "l": "litres",
    "lt": "litres",
    "ltr": "litres",
    "litre": "litres",
    "litres": "litres",
    "liter": "litres",
    "liters": "litres",
    "gal": "gallons",
    "gallon": "gallons",
    "gallons": "gallons",
    "kg": "kg",
    "t": "tonnes",
    "ton": "tonnes",
    "tonne": "tonnes",
    "tonnes": "tonnes",
    "miles": "miles",
    "mile": "miles",
    "km": "km",
}

#: Segments that indicate the column carries a physical quantity (used to decide
#: whether a unit segment belongs to the quantity column).
_QUANTITY_SEGMENTS = frozenset(
    {"quantity", "qty", "consumption", "volume", "usage", "reading", "units_used"}
)


#: Units the tabular parser accepts when a unit column is missing but the value
#: looks like a physical quantity (fraction of the factor-unit vocabulary).
_PHYSICAL_UNITS = {
    "kwh", "mwh", "m3", "m³", "litres", "liters", "litre", "liter", "l",
    "tonnes", "tons", "tonne", "ton", "t", "kg", "miles", "km", "mile", "grosscv",
}

#: Currency codes recognised as spend-based units.
_CURRENCIES = {"gbp", "eur", "usd", "£", "€", "$"}

def _classify(filename: str, mime: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf" or "pdf" in mime:
        return "PDF"
    if ext in ("jpg", "jpeg", "png", "gif", "webp") or "image" in mime:
        return "IMAGE"
    if ext in ("csv", "xlsx", "xls"):
        return "SPREADSHEET"
    return "OTHER"


def _clean(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_number(value: Any) -> Optional[float]:
    text = _clean(value)
    if not text:
        return None
    text = text.replace(",", "").replace("£", "").replace("€", "").replace("$", "")
    try:
        return float(Decimal(text))
    except (InvalidOperation, ValueError):
        return None


def _detect_activity(text: str) -> Optional[str]:
    if not text:
        return None
    for label, pattern in _ACTIVITY_KEYWORDS:
        if pattern.search(text):
            return label
    return None


def _detect_unit(text: str) -> Optional[str]:
    unit = (_clean(text) or "").strip().lower()
    if unit in _PHYSICAL_UNITS:
        return {"m3": "m3", "m³": "m3"}.get(unit, unit)
    if unit in _CURRENCIES:
        return "GBP" if unit == "£" else unit.upper()
    return None


#: Lazy ONNX OCR engine (pure-pip, no system Tesseract dependency).
_onnx_ocr_engine = None


def _onnx_ocr(content: bytes) -> Optional[str]:
    """OCR ``content`` with the ONNX engine when Tesseract is unavailable.

    Returns the recognised text lines joined with newlines, or ``None``.
    Used as the fallback for scanned PDFs/images on hosts without Tesseract
    (e.g. fresh CI/demo boxes) so the automatic pipeline still works.
    """
    global _onnx_ocr_engine
    try:
        import io

        import numpy as np
        from PIL import Image
        from rapidocr_onnxruntime import RapidOCR

        if _onnx_ocr_engine is None:
            _onnx_ocr_engine = RapidOCR()
        image = Image.open(io.BytesIO(content)).convert("RGB")
        result, _ = _onnx_ocr_engine(np.asarray(image))
        lines = [
            str(item[1])
            for item in (result or [])
            if len(item) >= 2 and item[1]
        ]
        return "\n".join(lines) or None
    except Exception:  # noqa: BLE001 — OCR fallback must never raise
        return None


def _completeness(extracted: dict) -> float:
    if not extracted:
        return 0.0
    line_items = extracted.get("line_items") or []
    if line_items:
        resolved = 0
        total = 0
        for line in line_items:
            for field in _REQUIRED:
                total += 1
                if str(line.get(field) or "").strip():
                    resolved += 1
        return round(resolved / total, 4) if total else 0.0
    resolved = sum(
        1 for field in _REQUIRED if str(extracted.get(field) or "").strip()
    )
    return round(resolved / len(_REQUIRED), 4)



def _pdf_text(content: bytes) -> tuple[str, str, int]:
    """Deterministic PDF → ``(text, method, page_count)`` (never raises).

    Shared by the deterministic suggestion pass and the optional AI extraction
    step (Phase 2) so the document text is extracted exactly once per pipeline.
    """
    from pdf_engine import PDFExtractor

    extractor = PDFExtractor()
    method = "pdf_text"
    text = extractor._extract_text_direct(content)
    if not text or len(text.strip()) < 20:
        ocr = extractor._extract_text_ocr(content)
        if ocr and len(ocr.strip()) >= 20:
            text, method = ocr, "tesseract_ocr"
        else:
            # Tesseract/poppler unavailable → pypdfium2 render + ONNX OCR.
            pages = _render_pdf_pages_pypdfium(content)
            if pages:
                recognized = [_onnx_ocr(p) for p in pages]
                joined = "\n".join(t for t in recognized if t)
                if joined and len(joined.strip()) >= 20:
                    text, method = joined, "onnx_ocr"
    page_count = extractor._get_page_count(content)
    return (text or ""), method, int(page_count or 0)


def _apply_p1_fidelity(
    text: str,
    *,
    method: str,
    page_count: int,
    extracted: dict,
    unresolved: list,
    organization_id: Optional[str] = None,
) -> dict:
    """Phase 8 P1 (P1-D1) — the shared extraction-fidelity shape/coverage hook.

    SHADOW-FIRST: in ``shadow`` (the default) this only **measures** — the
    coverage block is attached to the result and logged, and customer-visible
    output is unchanged. In ``enabled`` mode a multi-line-suspect document emits
    per-source-line ``line_items[]``; a suspect document whose lines cannot be
    separated is reported as ``multi_line_unresolved`` with the bounded ``P1-D2``
    reason for the caller to gate.

    Step 2 / WS-B B3 — this hook is applied to **both** the PDF path and the
    IMAGE path. ``P1-D1`` covers multi-line *PDF/IMAGE* documents; before this
    change only ``_extract_pdf`` was wired, so a scanned multi-line IMAGE (or a
    single-page image invoice) was still silently collapsed.

    Returns ``{"extracted": …, "coverage": …|None, "block": …|None}``.
    """
    from services import extraction_fidelity as p1

    # Step 2C / POD-4 — the effective mode is tenant-aware: `enabled` is honoured
    # only for organisations inside the controlled rollout allowlist; everything
    # else (and the default) stays `shadow`, i.e. unchanged customer-visible
    # behaviour. `rollout` is attached as audit evidence.
    mode = p1.shape_mode(organization_id=organization_id)
    rollout = p1.rollout_status(organization_id=organization_id)
    coverage: Optional[dict] = None
    out_extracted = extracted
    block: Optional[dict] = None
    if mode != p1.MODE_OFF:
        judgement = p1.classify(text, method=method, page_count=page_count)
        coverage = judgement.as_coverage()
        coverage["mode"] = mode
        coverage["ai_fanout"] = p1.ai_fanout_plan(judgement)
        logger.info(
            "P1 coverage (%s): method=%s suspect=%s lines=%s pages=%s basis=%s chars=%s",
            mode,
            method,
            judgement.multi_line_suspect,
            judgement.candidate_lines,
            judgement.page_count,
            judgement.page_basis,
            judgement.text_chars,
        )
        if mode == p1.MODE_ENABLED and judgement.multi_line_suspect:
            items, shape_coverage = p1.build_line_items(
                text,
                method=method,
                page_count=page_count,
                # `033` D-F — the document-level invoice number already established by the
                # existing extraction travels onto each line item (no new field).
                invoice_number=extracted.get("invoice_number"),
            )
            coverage = shape_coverage
            coverage["mode"] = mode
            if items:
                out_extracted = {**extracted, "line_items": items}
            else:
                # P1-D2: never silently collapse a suspect document.
                block = {
                    "status": "multi_line_unresolved",
                    "method": method,
                    "page_count": page_count,
                    "extracted_data": extracted,
                    "unresolved": unresolved,
                    "confidence": _completeness(extracted),
                    "coverage": coverage,
                    "block_reason": p1.block_reason(judgement),
                }
    # POD-4 — the rollout decision is attached as audit evidence on every
    # governed extraction (which mode was requested, which mode was effective for
    # this organisation, and whether it is inside the controlled rollout).
    return {
        "extracted": out_extracted,
        "coverage": coverage,
        "block": block,
        "rollout": rollout,
    }


def _extract_pdf(content: bytes, *, organization_id: Optional[str] = None) -> dict:
    text, method, page_count = _pdf_text(content)
    if not text or len(text.strip()) < 20:
        return {
            "status": "no_text",
            "method": method,
            "page_count": page_count,
            "extracted_data": {},
            "unresolved": list(_REQUIRED) + ["supplier", "date"],
            "confidence": 0.0,
            "detail": "no usable text extracted (blank page, or image too low quality)",
        }
    suggestion = suggest_text(text[:200_000])
    extracted = dict(suggestion.get("suggested_data") or {})
    unresolved = list(suggestion.get("unresolved") or [])
    # ------------------------------------------------------------------
    # Phase 8 P1 (P1-D1) — extraction fidelity, SHADOW-FIRST (shared hook).
    # Step 2 / WS-B B3 — the same hook now also covers the IMAGE path.
    # ------------------------------------------------------------------
    p1_outcome = _apply_p1_fidelity(
        text,
        method=method,
        page_count=page_count,
        extracted=extracted,
        unresolved=unresolved,
        organization_id=organization_id,
    )
    if p1_outcome["block"] is not None:
        return p1_outcome["block"]
    extracted = p1_outcome["extracted"]
    coverage = p1_outcome["coverage"]
    result = {
        "status": "ok",
        "method": method,
        "page_count": page_count,
        "extracted_data": extracted,
        "unresolved": unresolved,
        "confidence": _completeness(extracted),
    }
    if coverage is not None:
        result["coverage"] = coverage
    return result


def _render_pdf_pages_pypdfium(content: bytes) -> list[bytes]:
    """Render PDF pages to PNG bytes via pypdfium2 (no poppler dependency)."""
    try:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(content)
        out: list[bytes] = []
        for page in pdf:
            bitmap = page.render(scale=2.0)
            pil = bitmap.to_pil().convert("RGB")
            import io

            buf = io.BytesIO()
            pil.save(buf, format="PNG")
            out.append(buf.getvalue())
        pdf.close()
        return out
    except Exception:  # noqa: BLE001 — render fallback must never raise
        return []


def _image_text(content: bytes) -> tuple[str, str]:
    """Deterministic IMAGE → ``(text, method)`` (never raises)."""
    from pdf_engine import PDFExtractor

    extractor = PDFExtractor()
    method = "tesseract_ocr"
    text = ""
    try:
        text = extractor.extract_image_text(content)
    except Exception:  # noqa: BLE001 — Tesseract missing/blank on this host
        text = ""
    if not text or len(text.strip()) < 20:
        # Tesseract unavailable/blank → ONNX OCR fallback (pure-pip).
        fallback = _onnx_ocr(content)
        if fallback and len(fallback.strip()) >= 20:
            text, method = fallback, "onnx_ocr"
    return (text or ""), method


def _extract_image(content: bytes, *, organization_id: Optional[str] = None) -> dict:
    text, method = _image_text(content)
    if not text or len(text.strip()) < 20:
        return {
            "status": "no_text",
            "method": method,
            "page_count": 1,
            "extracted_data": {},
            "unresolved": list(_REQUIRED) + ["supplier", "date"],
            "confidence": 0.0,
            "detail": "no usable OCR text (image too low quality)",
        }
    suggestion = suggest_text(text[:200_000])
    extracted = dict(suggestion.get("suggested_data") or {})
    unresolved = list(suggestion.get("unresolved") or [])
    # Step 2 / WS-B B3 — the P1 fidelity hook applies to the IMAGE path too
    # (P1-D1 covers multi-line PDF *and* IMAGE documents).
    p1_outcome = _apply_p1_fidelity(
        text,
        method=method,
        page_count=1,
        extracted=extracted,
        unresolved=unresolved,
        organization_id=organization_id,
    )
    if p1_outcome["block"] is not None:
        return p1_outcome["block"]
    extracted = p1_outcome["extracted"]
    coverage = p1_outcome["coverage"]
    result = {
        "status": "ok",
        "method": method,
        "page_count": 1,
        "extracted_data": extracted,
        "unresolved": unresolved,
        "confidence": _completeness(extracted),
    }
    if coverage is not None:
        result["coverage"] = coverage
    return result


def _normalise_columns(header: list[str]) -> list[tuple[Optional[str], Optional[str]]]:
    """Map a header row to ``(field, unit_hint)`` pairs.

    ``unit_hint`` is a unit token embedded in a quantity header such as
    ``Quantity (litres)`` / ``Consumption (kWh)``; the row parser applies it to
    every row when no explicit unit cell is present.

    Step 2C / POD-3 — resolution order per column:

    1. the exact normalised key in ``_COLUMN_ALIASES``;
    2. an explicit ``_ALIAS_EXCLUSIONS`` key → preserved as its own field and
       **never** coerced (a unit price is not an amount; a site is not an
       activity);
    3. a whole-segment unit token (``_UNIT_SEGMENTS``) combined with a physical
       quantity segment → ``quantity`` carrying the unit hint;
    4. the **longest** ``_ALIAS_SEGMENTS`` alias contained as a whole key segment;
    5. a whole-segment unit token alone → ``unit``;
    6. otherwise the normalised key itself (preserved verbatim).
    """
    out: list[tuple[Optional[str], Optional[str]]] = []
    for cell in header:
        raw = str(cell).strip()
        key = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")
        if not key:
            out.append((None, None))
            continue
        if key in _COLUMN_ALIASES:
            out.append((_COLUMN_ALIASES[key], None))
            continue
        if key in _ALIAS_EXCLUSIONS:
            out.append((key, None))
            continue
        segments = [seg for seg in key.split("_") if seg]
        unit_hint = next(
            (_UNIT_SEGMENTS[seg] for seg in segments if seg in _UNIT_SEGMENTS), None
        )
        if unit_hint and any(seg in _QUANTITY_SEGMENTS for seg in segments):
            out.append(("quantity", unit_hint))
            continue
        matches = [
            (alias, target)
            for alias, target in _ALIAS_SEGMENTS
            if alias in segments
        ]
        if matches:
            # Longest alias wins: `fuel_consumption` is a quantity column, not
            # an activity column, even though both segments are aliases.
            target = max(matches, key=lambda item: len(item[0]))[1]
            out.append((target, None))
            continue
        if unit_hint:
            out.append(("unit", unit_hint))
            continue
        out.append((key, None))
    return out


def _rows_to_line_items(
    rows: list[list[Any]],
    header: list[tuple[Optional[str], Optional[str]]],
) -> tuple[list[dict], list[str]]:
    """Convert data rows + normalised header into ``line_items`` records.

    Step 2C / POD-3 — every record carries ``source_row`` (1-based data-row index)
    so a parsed line can always be traced back to its position in the original
    file, and the row order of ``line_items`` matches the file's row order.
    """
    line_items: list[dict] = []
    unresolved: set[str] = set()
    unit_hint = next((u for _, u in header if u), None)
    for row_index, raw in enumerate(rows, start=1):
        if not raw or all(_clean(c) is None for c in raw):
            continue
        record: dict[str, Any] = {"source_row": row_index}
        for idx, (field, _hint) in enumerate(header):
            if field is None or idx >= len(raw):
                continue
            value = raw[idx]
            if field == "quantity":
                number = _to_number(value)
                if number is not None:
                    record["quantity"] = number
            elif field == "amount":
                number = _to_number(value)
                if number is not None:
                    record["amount"] = number
            elif field in ("activity", "unit", "supplier", "date", "currency", "invoice_number"):
                cleaned = _clean(value)
                if cleaned:
                    record[field] = cleaned
        activity = record.get("activity")
        detected = _detect_activity(activity) if activity else None
        if detected:
            record["activity"] = detected
        unit = record.get("unit")
        detected_unit = _detect_unit(unit) if unit else None
        if not detected_unit and unit_hint:
            detected_unit = _detect_unit(unit_hint)
        # Currency amount with no physical unit → spend-based line.
        currency = (record.get("currency") or "").strip().upper()
        if not detected_unit and "amount" in record and record.get("amount") is not None:
            detected_unit = "GBP" if currency in ("", "GBP", "£") else currency
        if detected_unit:
            record["unit"] = detected_unit
        elif record.get("unit"):
            del record["unit"]
        if not record.get("quantity") and "amount" in record and record.get("amount") is not None:
            record["quantity"] = record["amount"]
        for field in ("activity", "quantity", "unit"):
            if not str(record.get(field) or "").strip():
                unresolved.add(field)
        # POD-3 — a record with no canonical field is a phantom line (e.g. a
        # workbook cover sheet). It must not count as extracted activity, or a
        # cover sheet would look like a successful extraction and stop the sheet
        # scan from reaching the real data sheet.
        if record and any(
            field in record for field in ("activity", "quantity", "unit", "amount")
        ):
            line_items.append(record)
    return line_items, sorted(unresolved)

def _extract_csv(content: bytes) -> dict:
    import csv as _csv

    text = content.decode("utf-8-sig", errors="replace")
    reader = _csv.reader(io.StringIO(text))
    rows = [r for r in reader if any(_clean(c) for c in r)]
    if not rows:
        return {
            "status": "no_text", "method": "csv", "page_count": 0,
            "extracted_data": {}, "unresolved": list(_REQUIRED), "confidence": 0.0,
        }
    header = _normalise_columns(rows[0])
    line_items, unresolved = _rows_to_line_items(rows[1:], header)
    extracted: dict[str, Any] = {"line_items": line_items}
    # POD-3 — preserve the source header row verbatim (provenance: a mapped
    # field can always be traced back to the column it came from).
    extracted["source_headers"] = [str(c) for c in rows[0]]
    if line_items and line_items[0].get("supplier"):
        extracted["supplier"] = line_items[0]["supplier"]
    if line_items and line_items[0].get("date"):
        extracted["date"] = line_items[0]["date"]
    if line_items and line_items[0].get("invoice_number"):
        extracted["invoice_number"] = line_items[0]["invoice_number"]
    return {
        "status": "ok" if line_items else "no_text",
        "method": "csv",
        "page_count": 0,
        "extracted_data": extracted,
        "unresolved": unresolved,
        "confidence": _completeness(extracted),
    }


#: Step 2C / POD-3 — a workbook is scanned sheet-by-sheet (bounded), so a file
#: whose *first* sheet is a cover/summary page still yields its activity data.
#: Bounded to the first ``_XLSX_SHEET_SCAN_LIMIT`` sheets: no unbounded work, and
#: the scan order is the workbook's own declaration order (deterministic).
_XLSX_SHEET_SCAN_LIMIT = 5


def _xlsx_sheet_result(sheet, sheet_title: str, sheet_names: list[str]) -> dict:
    """Parse one worksheet into the canonical extraction result shape."""
    rows = [list(row) for row in sheet.iter_rows(values_only=True)]
    rows = [r for r in rows if any(_clean(c) for c in r)]
    if not rows:
        return {
            "status": "no_text", "method": "xlsx", "page_count": 0,
            "extracted_data": {}, "unresolved": list(_REQUIRED), "confidence": 0.0,
            "detail": f"sheet {sheet_title!r} contains no rows",
        }
    header_cells = [str(c) if c is not None else "" for c in rows[0]]
    header = _normalise_columns(header_cells)
    line_items, unresolved = _rows_to_line_items(rows[1:], header)
    extracted: dict[str, Any] = {"line_items": line_items}
    # POD-3 — preserve the source header row + sheet provenance verbatim.
    extracted["source_headers"] = header_cells
    extracted["source_sheet"] = sheet_title
    extracted["sheet_names"] = sheet_names
    if line_items and line_items[0].get("supplier"):
        extracted["supplier"] = line_items[0]["supplier"]
    if line_items and line_items[0].get("date"):
        extracted["date"] = line_items[0]["date"]
    return {
        "status": "ok" if line_items else "no_text",
        "method": "xlsx",
        "page_count": 0,
        "extracted_data": extracted,
        "unresolved": unresolved,
        "confidence": _completeness(extracted),
    }


def _extract_xlsx(content: bytes) -> dict:
    import openpyxl

    try:
        workbook = openpyxl.load_workbook(
            io.BytesIO(content), read_only=True, data_only=True
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error", "method": "xlsx", "page_count": 0,
            "extracted_data": {}, "unresolved": list(_REQUIRED), "confidence": 0.0,
            "detail": f"workbook parse failed: {exc}",
        }
    sheet_names = list(workbook.sheetnames)
    if not sheet_names:
        workbook.close()
        return {
            "status": "no_text", "method": "xlsx", "page_count": 0,
            "extracted_data": {}, "unresolved": list(_REQUIRED), "confidence": 0.0,
            "detail": "workbook has no worksheets",
        }
    # POD-3: the active sheet is tried first, then the remaining sheets in
    # workbook order. A cover/summary first sheet must not hide the data sheet
    # (this is one of the reasons "Excel files were not being extracted").
    ordered = [workbook.active.title] + [
        name for name in sheet_names if name != workbook.active.title
    ]
    best: Optional[dict] = None
    for name in ordered[:_XLSX_SHEET_SCAN_LIMIT]:
        result = _xlsx_sheet_result(workbook[name], name, sheet_names)
        if result["status"] == "ok":
            workbook.close()
            return result
        if best is None:
            best = result
    workbook.close()
    return best or {
        "status": "no_text", "method": "xlsx", "page_count": 0,
        "extracted_data": {}, "unresolved": list(_REQUIRED), "confidence": 0.0,
    }


def extract_document(
    content: bytes, filename: str, mime: str, *, organization_id: Optional[str] = None
) -> dict:
    """Extract structured ``extracted_data`` from ``content`` (never raises).

    The public entry point for the automatic pipeline. Classification is by
    file extension/mime; unknown types return ``unsupported`` so the worker
    routes the job to the manual-review gate instead of failing the upload.

    ``organization_id`` (Step 2C / POD-4) scopes the governed P1 rollout: it is
    passed to the fidelity hook so ``enabled`` mode is honoured only for the
    organisations inside the controlled allowlist. Omitting it is safe — the
    resolver then keeps the existing ``shadow`` behaviour.
    """
    ftype = _classify(filename, mime)
    try:
        if ftype == "PDF":
            return _extract_pdf(content, organization_id=organization_id)
        if ftype == "IMAGE":
            return _extract_image(content, organization_id=organization_id)
        if ftype == "SPREADSHEET":
            ext = filename.rsplit(".", 1)[-1].lower()
            if ext == "csv":
                return _extract_csv(content)
            return _extract_xlsx(content)
    except Exception as exc:  # noqa: BLE001 — extraction must never raise
        return {
            "status": "error", "method": ftype.lower(), "page_count": 0,
            "extracted_data": {}, "unresolved": list(_REQUIRED), "confidence": 0.0,
            "detail": str(exc)[:500],
        }
    return {
        "status": "unsupported", "method": ftype.lower(), "page_count": 0,
        "extracted_data": {}, "unresolved": list(_REQUIRED), "confidence": 0.0,
        "detail": f"unsupported file type {ftype}",
    }


def completeness_score(extracted: dict) -> float:
    """Public 0..1 completeness over the canonical pipeline fields.

    Mirrors the private ``_completeness`` used by the deterministic extractors
    and the durable job's ``completeness`` property, so every extraction source
    (deterministic, AI, human) is measured the same way.
    """
    return _completeness(extracted or {})


def extract_document_text(content: bytes, filename: str, mime: str) -> dict:
    """Deterministic document → raw text layer (Phase 2, AI reuse).

    Returns ``{"status", "ftype", "text", "method", "page_count"}`` where
    ``status`` is ``ok`` / ``no_text`` / ``unsupported`` / ``error``. PDFs and
    images reuse the same deterministic text resolution as the suggestion pass
    (``_pdf_text`` / ``_image_text``); CSV returns its decoded text. XLSX and
    unknown types are ``unsupported`` (not suitable for an LLM text pass).
    Never raises.
    """
    ftype = _classify(filename, mime)
    try:
        if ftype == "PDF":
            text, method, page_count = _pdf_text(content)
            return {
                "status": "ok" if text and len(text.strip()) >= 20 else "no_text",
                "ftype": ftype, "text": text[:200_000], "method": method,
                "page_count": page_count,
            }
        if ftype == "IMAGE":
            text, method = _image_text(content)
            return {
                "status": "ok" if text and len(text.strip()) >= 20 else "no_text",
                "ftype": ftype, "text": text[:200_000], "method": method,
                "page_count": 1,
            }
        if ftype == "SPREADSHEET":
            ext = filename.rsplit(".", 1)[-1].lower()
            if ext != "csv":
                return {
                    "status": "unsupported", "ftype": ftype, "text": "",
                    "method": "xlsx", "page_count": 0,
                    "detail": "xlsx is parsed tabularly, not sent to an LLM",
                }
            text = content.decode("utf-8-sig", errors="replace")
            return {
                "status": "ok" if text.strip() else "no_text",
                "ftype": ftype, "text": text[:200_000], "method": "csv",
                "page_count": 0,
            }
    except Exception as exc:  # noqa: BLE001 — text extraction must never raise
        return {
            "status": "error", "ftype": ftype, "text": "",
            "method": ftype.lower(), "page_count": 0, "detail": str(exc)[:500],
        }
    return {
        "status": "unsupported", "ftype": ftype, "text": "",
        "method": ftype.lower(), "page_count": 0,
        "detail": f"unsupported file type {ftype}",
    }
