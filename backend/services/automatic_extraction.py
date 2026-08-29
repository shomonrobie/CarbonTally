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

from services.extraction_suggestions import suggest as suggest_text

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
    "period": "date",
    "supplier": "supplier",
    "vendor": "supplier",
    "merchant": "supplier",
    "category": "activity",
    "activity": "activity",
    "description": "activity",
    "item": "activity",
    "fuel": "activity",
    "product": "activity",
    "quantity": "quantity",
    "qty": "quantity",
    "consumption": "quantity",
    "volume": "quantity",
    "usage": "quantity",
    "kwh": "quantity",
    "unit": "unit",
    "uom": "unit",
    "amount": "amount",
    "cost": "amount",
    "total": "amount",
    "gross_amount": "amount",
    "net_amount": "amount",
    "currency": "currency",
    "ccy": "currency",
    "invoice_number": "invoice_number",
    "invoice_no": "invoice_number",
}

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



def _extract_pdf(content: bytes) -> dict:
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
    return {
        "status": "ok",
        "method": method,
        "page_count": page_count,
        "extracted_data": extracted,
        "unresolved": unresolved,
        "confidence": _completeness(extracted),
    }


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


def _extract_image(content: bytes) -> dict:
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
    return {
        "status": "ok",
        "method": method,
        "page_count": 1,
        "extracted_data": extracted,
        "unresolved": unresolved,
        "confidence": _completeness(extracted),
    }


def _normalise_columns(header: list[str]) -> list[tuple[Optional[str], Optional[str]]]:
    """Map a header row to ``(field, unit_hint)`` pairs.

    ``unit_hint`` is a unit token embedded in a quantity header such as
    ``Quantity (litres)`` / ``Consumption (kWh)``; the row parser applies it to
    every row when no explicit unit cell is present.
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
        unit_tokens = [
            t
            for t in ("kwh", "litres", "litre", "m³", "m3", "tonnes", "tonne", "kg", "miles", "mile")
            if t in key
        ]
        if unit_tokens and any(
            q in key for q in ("quantity", "qty", "consumption", "usage", "volume")
        ):
            out.append(("quantity", unit_tokens[0]))
        elif unit_tokens:
            out.append(("unit", None))
        else:
            out.append((key, None))
    return out


def _rows_to_line_items(
    rows: list[list[Any]],
    header: list[tuple[Optional[str], Optional[str]]],
) -> tuple[list[dict], list[str]]:
    """Convert data rows + normalised header into ``line_items`` records."""
    line_items: list[dict] = []
    unresolved: set[str] = set()
    unit_hint = next((u for _, u in header if u), None)
    for raw in rows:
        if not raw or all(_clean(c) is None for c in raw):
            continue
        record: dict[str, Any] = {}
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
        if record:
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


def _extract_xlsx(content: bytes) -> dict:
    import openpyxl

    try:
        workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error", "method": "xlsx", "page_count": 0,
            "extracted_data": {}, "unresolved": list(_REQUIRED), "confidence": 0.0,
            "detail": f"workbook parse failed: {exc}",
        }
    sheet = workbook.active
    if sheet is None:
        return {
            "status": "no_text", "method": "xlsx", "page_count": 0,
            "extracted_data": {}, "unresolved": list(_REQUIRED), "confidence": 0.0,
        }
    rows = [list(row) for row in sheet.iter_rows(values_only=True)]
    rows = [r for r in rows if any(_clean(c) for c in r)]
    workbook.close()
    if not rows:
        return {
            "status": "no_text", "method": "xlsx", "page_count": 0,
            "extracted_data": {}, "unresolved": list(_REQUIRED), "confidence": 0.0,
        }
    header = _normalise_columns([str(c) if c is not None else "" for c in rows[0]])
    line_items, unresolved = _rows_to_line_items(rows[1:], header)
    extracted: dict[str, Any] = {"line_items": line_items}
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


def extract_document(content: bytes, filename: str, mime: str) -> dict:
    """Extract structured ``extracted_data`` from ``content`` (never raises).

    The public entry point for the automatic pipeline. Classification is by
    file extension/mime; unknown types return ``unsupported`` so the worker
    routes the job to the manual-review gate instead of failing the upload.
    """
    ftype = _classify(filename, mime)
    try:
        if ftype == "PDF":
            return _extract_pdf(content)
        if ftype == "IMAGE":
            return _extract_image(content)
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
