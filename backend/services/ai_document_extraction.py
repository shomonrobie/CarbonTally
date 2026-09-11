"""Candidate AI extraction for the durable automatic pipeline (Phase 2).

Composes the deterministic document-text layer (already used by the automatic
pipeline) with an optional LLM client and returns a candidate
``extracted_data`` envelope shaped exactly like the deterministic extractor
output, so mapping / validation / calculation consume it unchanged.

Contract / boundaries
---------------------
* The LLM is the only non-deterministic input. The prompt, JSON parsing and
  post-processing are deterministic.
* AI output is **candidate** data only. It still passes the deterministic
  completeness gate, factor matching, item validation and the canonical
  :class:`engines.calculation.CalculationRequest` boundary (Phase-1 unit +
  methodology normalisation) before any calculation is persisted.
* ``unit`` values are canonicalised with ``core.units.normalize_unit`` — the
  Phase-1 canonical mechanism. This module never invents a second normaliser.
* Failures (transport, non-JSON, malformed fields) return an ``error`` /
  low-confidence envelope instead of raising, so the durable caller represents
  them durably (blocked / manual review) — never a false success.
* No credentials or raw document contents are logged or persisted.
"""
from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from core.exceptions import AIExtractionFailedError
from core.logging import get_logger
from core.units import normalize_unit
from infra.llm_client import LLMClient
from services.automatic_extraction import completeness_score

logger = get_logger(__name__)

#: Bounds the prompt text so token usage stays bounded for long documents.
DEFAULT_MAX_TEXT_CHARS = 20_000

#: Date formats accepted from the LLM (ISO preferred).
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%d %b %Y")

_SYSTEM_PROMPT = (
    "You are a precise energy/fuel invoice data-extraction assistant for "
    "carbon-emissions reporting. Return only JSON."
)

def _clean_str(value: Any, limit: int = 200) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:limit]


def _to_positive_number(value: Any) -> Optional[float]:
    """Parse a non-negative number (str/int/float/Decimal)."""
    if value is None:
        return None
    try:
        number = float(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if number < 0:
        return None
    return number


def _canonical_unit(value: Any) -> Optional[str]:
    """Canonical unit via the Phase-1 normaliser (never a second mechanism)."""
    cleaned = _clean_str(value, limit=40)
    if not cleaned:
        return None
    return normalize_unit(cleaned) or None


def _canonical_date(value: Any) -> Optional[str]:
    """Return ISO ``YYYY-MM-DD`` when the LLM date parses; else raw (unresolved)."""
    cleaned = _clean_str(value, limit=40)
    if not cleaned:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _strip_code_fence(text: str) -> str:
    """Remove a surrounding Markdown code fence from an LLM response."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _clean_single(fields: dict) -> dict:
    """Deterministically post-process one candidate line/record."""
    record: dict[str, Any] = {}
    activity = _clean_str(fields.get("activity"))
    if activity:
        record["activity"] = activity
    supplier = _clean_str(fields.get("supplier"))
    if supplier:
        record["supplier"] = supplier
    amount = _to_positive_number(fields.get("amount"))
    if amount is not None:
        record["amount"] = amount
    quantity = _to_positive_number(fields.get("quantity"))
    unit = _canonical_unit(fields.get("unit"))
    currency = _clean_str(fields.get("currency"), limit=10)
    if quantity is None and amount is not None and unit is None:
        # Spend-based fallback: currency amount with no physical unit.
        quantity, unit = amount, (currency or "GBP").upper()
    if quantity is not None:
        record["quantity"] = quantity
    if unit:
        record["unit"] = unit
    date = _canonical_date(fields.get("date"))
    if date:
        record["date"] = date
    invoice = _clean_str(fields.get("invoice_number"), limit=80)
    if invoice:
        record["invoice_number"] = invoice
    return record

class AIDocumentExtractionEngine:
    """Candidate LLM extraction over deterministic document text.

    Args:
        llm_client: The configured :class:`infra.llm_client.LLMClient`.
        max_text_chars: Maximum document characters sent to the LLM.
    """

    def __init__(self, llm_client: LLMClient, *, max_text_chars: int = DEFAULT_MAX_TEXT_CHARS) -> None:
        if llm_client is None:
            raise ValueError("llm_client must not be None")
        if max_text_chars < 1:
            raise ValueError("max_text_chars must be >= 1")
        self._llm_client = llm_client
        self._max_text_chars = max_text_chars

    @property
    def llm_client(self) -> LLMClient:
        """The underlying LLM client (model/provider metadata lives on it)."""
        return self._llm_client

    @property
    def max_text_chars(self) -> int:
        """The document-character bound sent to the LLM."""
        return self._max_text_chars

    def _prompt(self, text: str) -> str:
        return (
            "Extract the fuel/energy consumption data from this document for "
            "carbon-emissions reporting.\n\n"
            "Return ONLY JSON with one of these two shapes:\n"
            '1) Single item: {"activity": "...", "quantity": <number>, "unit": '
            '"...", "date": "YYYY-MM-DD", "supplier": "...", "amount": <number>, '
            '"currency": "..."}\n'
            '2) Tabular document: {"line_items": [{"activity": "...", "quantity": '
            '<number>, "unit": "...", "date": "YYYY-MM-DD", "supplier": "...", '
            '"amount": <number>}, ...]}\n\n'
            "Rules:\n"
            "- activity is the fuel/energy category (e.g. Diesel, Natural gas, "
            "Electricity, Water, Business travel), not the brand.\n"
            "- quantity is the numeric consumption; unit is the consumption unit "
            "(litres, kWh, m3, cubic metres, tonnes, km, miles).\n"
            "- When a line is a currency amount with no physical quantity, use "
            'the currency code (GBP/EUR/USD) as "unit" and set quantity to the '
            "amount.\n"
            "- Only include fields that appear in the document; omit anything "
            "unknown.\n\n"
            f"Document text:\n{text}"
        )

    async def extract_candidate(
        self,
        text: str,
        *,
        filename: str = "",
        method: str = "pdf_text",
    ) -> dict:
        """Run the LLM over ``text`` and return a deterministic-shaped envelope.

        Returns ``{"status", "method", "model", "extracted_data",
        "unresolved", "confidence"}`` (plus ``detail`` on failure) — never
        raises. ``status`` is ``ok`` / ``no_text`` / ``error``.
        """
        clipped = (text or "").strip()
        if not clipped:
            return {
                "status": "no_text", "method": "ai", "model": self._llm_client.model,
                "extracted_data": {}, "unresolved": [],
                "confidence": 0.0,
                "detail": "no document text available for AI extraction",
            }
        clipped = clipped[: self._max_text_chars]
        try:
            raw = await self._llm_client.complete(
                self._prompt(clipped),
                system=_SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=1024,
            )
        except AIExtractionFailedError as exc:
            logger.warning("AI extraction request failed for %r: %s", filename, exc)
            return {
                "status": "error", "method": "ai", "model": self._llm_client.model,
                "extracted_data": {}, "unresolved": [],
                "confidence": 0.0, "detail": str(exc)[:500],
            }
        try:
            parsed = json.loads(_strip_code_fence(raw))
        except (ValueError, TypeError):
            logger.warning("AI extraction returned non-JSON for %r", filename)
            return {
                "status": "error", "method": "ai", "model": self._llm_client.model,
                "extracted_data": {}, "unresolved": [],
                "confidence": 0.0, "detail": "LLM returned invalid JSON",
            }
        if not isinstance(parsed, dict):
            return {
                "status": "error", "method": "ai", "model": self._llm_client.model,
                "extracted_data": {}, "unresolved": [],
                "confidence": 0.0, "detail": "LLM response must be a JSON object",
            }
        extracted, unresolved = self._build_candidate(parsed)
        return {
            "status": "ok",
            "method": f"ai:{method}",
            "model": self._llm_client.model,
            "extracted_data": extracted,
            "unresolved": unresolved,
            "confidence": completeness_score(extracted),
        }

    def _build_candidate(self, parsed: dict) -> tuple[dict, list[str]]:
        """Map raw LLM output to the canonical pipeline shape (deterministic)."""
        raw_lines = parsed.get("line_items")
        if isinstance(raw_lines, list) and raw_lines:
            lines: list[dict] = []
            unresolved: set[str] = set()
            for raw in raw_lines:
                if not isinstance(raw, dict):
                    continue
                record = _clean_single(raw)
                for field in ("activity", "quantity", "unit"):
                    if not str(record.get(field) or "").strip():
                        unresolved.add(field)
                if record:
                    lines.append(record)
            if lines:
                extracted: dict[str, Any] = {"line_items": lines}
                first = lines[0]
                for field in ("supplier", "date", "invoice_number"):
                    if first.get(field):
                        extracted[field] = first[field]
                return extracted, sorted(unresolved)
        record = _clean_single(parsed)
        if not record:
            return {}, ["activity", "quantity", "unit"]
        unresolved_out = [
            f for f in ("activity", "quantity", "unit")
            if not str(record.get(f) or "").strip()
        ]
        return record, unresolved_out

