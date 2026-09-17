"""Phase 8 P1 — PDF/IMAGE extraction fidelity (shadow-first, additive).

Implements the **PO-ratified** P1 decisions
(`docs/architecture/CARBONTALLY_PHASE8_P1_PO_DECISION_RECORD_20260913.md`):

* **`P1-D1`** — a multi-line PDF/IMAGE may emit per-source-line ``line_items[]``, for
  **new documents only**, behind a ``PIPELINE_VERSION`` bump, and **shadow-first**:
  the coverage/classifier block is computed and logged with **no** change to
  customer-visible behaviour until shadow evidence proves the classifier selective.
* **`P1-D2`** — multi-line-suspect **and** AI unavailable ⇒ **block with a bounded
  truthful reason**; never silently collapse to a single line.
* **`P1-D3`** — per-page AI only when multi-line-suspect **and** the text exceeds the
  existing clip, never beyond the P1 page cap.
* **`P1-D5`** / **`P1-D7`** — per-line ``page`` for new output; marker-derived pages
  carry the OCR method stamp and are explicitly **lower trust**.
* **`P1-D8`** — AI-derived lines are stamped ``ai:*`` (or ``det:*+ai``) and are never
  relabelled as deterministic.

This module is deliberately **pure** (no I/O, no AI call, no database) so the
classifier can be shadow-measured and unit-tested in isolation. It performs **no**
calculation, **no** factor lookup and **no** historical reprocessing (`P1-D4`).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Optional

#: Extraction-shape mode. ``shadow`` (default) computes and logs the coverage block
#: only; ``enabled`` applies the ratified shape; ``off`` does not even measure.
#: The default **must** stay ``shadow`` until shadow evidence is recorded (`P1-D1`).
SHAPE_MODE_ENV = "CARBONTALLY_P1_EXTRACTION_SHAPE"
#: Step 2C / POD-4 — controlled rollout. Comma-separated organisation ids for
#: which `enabled` is honoured, or the deliberate global value `*`. An empty or
#: missing allowlist downgrades `enabled` to `shadow` (fail-safe).
ROLLOUT_ALLOWLIST_ENV = "CARBONTALLY_P1_ORGANIZATION_ALLOWLIST"
ROLLOUT_ALLOW_ALL = "*"
MODE_SHADOW = "shadow"
MODE_ENABLED = "enabled"
MODE_OFF = "off"

#: Pipeline generation stamp for P1-shaped output (`P1-D1`).
PIPELINE_VERSION_P1 = "v3-auto-1.1"

#: A document is multi-line-suspect from this many genuine source lines (`P1-D1`).
MULTI_LINE_MIN_LINES = 2

#: Hard cap on pages that may be sent to AI in one job (`P1-D3`).
PAGE_CAP = 20

#: Mirrors ``DEFAULT_MAX_TEXT_CHARS`` in the AI modules; kept here so the fan-out
#: decision needs no import of the AI stack.
CLIP_CHARS = 20_000

#: Deterministic extraction-method stamps (`P1-D8`) — never relabelled as another.
STAMP_DETERMINISTIC_PREFIX = "det:"
STAMP_AI_PREFIX = "ai:"

#: Unit tokens that make a line a plausible activity source line.
_UNIT_TOKENS = (
    "kwh", "mwh", "litre", "liter", "kg", "tonne", "ton ", "m3", "mile", "km",
    "night", "gbp", "£", "eur", "usd", "therm", "gallon",
)

#: Invoice furniture that must never be mistaken for a source line.
_FURNITURE = (
    "total", "subtotal", "sub-total", "vat", "tax", "amount due", "balance",
    "invoice", "statement", "sort code", "page ", "thank", "terms", "due date",
    "invoice date", "customer", "supplier", "address", "phone",
)

_NUMBER = re.compile(r"(?<![\w.])(\d{1,3}(?:[,\s]\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)")
_MARKER_PAGE = re.compile(r"\[\s*page\s+(\d+)\s*\]", re.IGNORECASE)


@dataclass(frozen=True)
class Judgement:
    """The classifier's verdict plus the measurable coverage facts."""

    multi_line_suspect: bool
    candidate_lines: int
    page_count: int
    page_basis: str
    page_resolution: str
    text_chars: int
    clipped: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def as_coverage(self) -> dict[str, Any]:
        """The coverage block written to logs/job metadata in shadow mode."""
        return {
            "multi_line_suspect": self.multi_line_suspect,
            "candidate_lines": self.candidate_lines,
            "page_count": self.page_count,
            "page_basis": self.page_basis,
            "page_resolution": self.page_resolution,
            "text_chars": self.text_chars,
            "clipped": self.clipped,
            "reasons": list(self.reasons),
            "multi_line_min_lines": MULTI_LINE_MIN_LINES,
            "page_cap": PAGE_CAP,
        }


def shape_mode(
    env: Optional[dict[str, str]] = None,
    organization_id: Optional[str] = None,
) -> str:
    """Resolve the **effective** extraction-shape mode for an organisation.

    Step 2C / POD-4 (PO decision C — controlled rollout). The mode is resolved in
    two independent steps so the default can never accidentally enable P1
    globally:

    1. the *requested* mode from ``SHAPE_MODE_ENV`` (invalid/absent → ``shadow``);
    2. an explicit **organisation allowlist** — ``enabled`` is honoured only for a
       listed organisation. An empty/missing allowlist downgrades ``enabled`` to
       ``shadow`` (fail-safe), so enabling P1 globally requires the deliberate
       value ``*`` in ``ROLLOUT_ALLOWLIST_ENV``.

    Resolution is deterministic and reversible: removing the organisation from the
    allowlist (or unsetting ``enabled``) returns it to the existing safe
    behaviour on the next extraction. Nothing is cached.
    """
    source = env if env is not None else os.environ
    raw = str(source.get(SHAPE_MODE_ENV, "") or "").strip().lower()
    requested = raw if raw in (MODE_ENABLED, MODE_SHADOW, MODE_OFF) else MODE_SHADOW
    if requested != MODE_ENABLED:
        return requested
    allowlist = _rollout_allowlist(source)
    if not allowlist:
        # Fail-safe: 'enabled' with no allowlist is treated as shadow.
        return MODE_SHADOW
    if ROLLOUT_ALLOW_ALL in allowlist:
        return MODE_ENABLED
    if organization_id and str(organization_id) in allowlist:
        return MODE_ENABLED
    return MODE_SHADOW


def _rollout_allowlist(env: Optional[dict[str, str]] = None) -> list[str]:
    """Parse the organisation allowlist (comma-separated organisation ids)."""
    source = env if env is not None else os.environ
    raw = str(source.get(ROLLOUT_ALLOWLIST_ENV, "") or "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def rollout_status(
    env: Optional[dict[str, str]] = None,
    organization_id: Optional[str] = None,
) -> dict[str, Any]:
    """Audit/evidence record for the controlled rollout decision.

    Deliberately free of secrets: it reports the requested mode, the effective
    mode, whether the organisation is inside the rollout, the allowlist size and
    whether the explicit global opt-in is set. Safe to persist as evidence on an
    extraction result or emit to logs.
    """
    source = env if env is not None else os.environ
    raw = str(source.get(SHAPE_MODE_ENV, "") or "").strip().lower()
    allowlist = _rollout_allowlist(source)
    effective = shape_mode(source, organization_id)
    return {
        "requested_mode": raw if raw in (MODE_ENABLED, MODE_SHADOW, MODE_OFF) else MODE_SHADOW,
        "effective_mode": effective,
        "organization_id": str(organization_id) if organization_id else None,
        "in_rollout": effective == MODE_ENABLED,
        "allowlist_size": len([item for item in allowlist if item != ROLLOUT_ALLOW_ALL]),
        "allow_all": ROLLOUT_ALLOW_ALL in allowlist,
    }


def split_pages(text: str, *, method: str) -> tuple[list[str], str, str]:
    """Split a text layer into pages.

    Returns ``(pages, page_basis, page_resolution)`` where ``page_basis`` is
    ``marker`` (OCR ``[page N]`` markers — **lower trust**, `P1-D7`), ``formfeed``
    (a real page boundary in the text layer) or ``document`` (no reliable boundary:
    the whole text is treated as one page, and that is **stated**, not guessed).
    """
    if not text:
        return ([], "document", "none")
    if _MARKER_PAGE.search(text):
        parts = _MARKER_PAGE.split(text)
        # split() yields [pre, n1, body1, n2, body2, ...]
        bodies = [parts[i] for i in range(2, len(parts), 2)]
        pages = [b for b in bodies if b.strip()]
        if pages:
            return (pages, "marker", "marker")
    if "\f" in text:
        pages = [p for p in text.split("\f") if p.strip()]
        if len(pages) > 1:
            return (pages, "formfeed", "formfeed")
    return ([text], "document", "document")



def _is_furniture(lowered: str) -> bool:
    return any(token in lowered for token in _FURNITURE)


def _has_unit(lowered: str) -> bool:
    return any(token.strip() in lowered for token in _UNIT_TOKENS)


def find_source_lines(page_text: str) -> list[dict[str, Any]]:
    """Deterministically identify genuine source lines on one page.

    Conservative by design — the `P1-D1` enablement gate depends on selectivity. A
    line needs real description text **and** a quantity with a recognised unit or
    currency mark, and must not be invoice furniture (totals, VAT, headers, footers).
    """
    found: list[dict[str, Any]] = []
    for raw in page_text.splitlines():
        line = " ".join(raw.split())
        if len(line) < 6 or len(line) > 300:
            continue
        lowered = line.lower()
        if _is_furniture(lowered):
            continue
        if sum(ch.isalpha() for ch in line) < 3:
            continue
        numbers = _NUMBER.findall(line)
        if not numbers or not _has_unit(lowered):
            continue
        quantity = None
        for candidate in numbers:
            try:
                value = float(candidate.replace(",", "").replace(" ", ""))
            except ValueError:
                continue
            if value == 0:
                continue
            quantity = value
            break
        if quantity is None:
            continue
        description = " ".join(_NUMBER.sub(" ", line).split())
        if sum(ch.isalpha() for ch in description) < 3:
            continue
        found.append({"description": description[:200], "quantity": quantity, "raw": line[:300]})
    return found


def classify(text: str, *, method: str, page_count: int) -> Judgement:
    """Classify a text layer for multi-line suspicion and record coverage facts."""
    body = text or ""
    pages, page_basis, page_resolution = split_pages(body, method=method)
    candidates = sum(len(find_source_lines(page)) for page in pages)
    reasons: list[str] = []
    if candidates >= MULTI_LINE_MIN_LINES:
        reasons.append(f"{candidates} candidate source lines")
    if page_basis == "marker":
        reasons.append("page numbers are marker-derived (lower trust, P1-D7)")
    if len(body) > CLIP_CHARS:
        reasons.append(f"text layer exceeds the AI clip ({len(body)} > {CLIP_CHARS})")
    return Judgement(
        multi_line_suspect=candidates >= MULTI_LINE_MIN_LINES,
        candidate_lines=candidates,
        page_count=int(page_count or len(pages) or 0),
        page_basis=page_basis,
        page_resolution=page_resolution,
        text_chars=len(body),
        clipped=len(body) > CLIP_CHARS,
        reasons=tuple(reasons),
    )


def ai_fanout_plan(judgement: Judgement) -> dict[str, Any]:
    """The `P1-D3` decision: may AI run per page, and within what cap?"""
    if not judgement.multi_line_suspect:
        return {
            "per_page_ai": False,
            "pages": 0,
            "page_cap": PAGE_CAP,
            "reason": "not multi-line-suspect",
        }
    if not judgement.clipped:
        return {
            "per_page_ai": False,
            "pages": 0,
            "page_cap": PAGE_CAP,
            "reason": "text layer is within the AI clip; a single pass suffices",
        }
    pages = max(1, min(judgement.page_count or 1, PAGE_CAP))
    return {
        "per_page_ai": True,
        "pages": pages,
        "page_cap": PAGE_CAP,
        "reason": f"multi-line-suspect and clipped; capped at {PAGE_CAP} pages",
    }


def method_stamp(*, method: str, ai_used: bool) -> str:
    """The provenance stamp for an extracted line (`P1-D8`)."""
    base = f"{STAMP_DETERMINISTIC_PREFIX}{method or 'unknown'}"
    return f"{base}+{STAMP_AI_PREFIX}{'yes' if ai_used else 'no'}" if ai_used else base


def block_reason(judgement: Judgement) -> str:
    """The bounded, truthful `P1-D2` reason for blocking a suspect document."""
    return (
        "This document appears to contain multiple activity lines "
        f"({judgement.candidate_lines} detected) but automatic extraction could not "
        "reliably separate them, and AI extraction is unavailable. It has been sent "
        "for human review instead of being reported as a single line."
    )


def build_line_items(
    text: str, *, method: str, page_count: int, ai_used: bool = False
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build the P1 per-source-line ``line_items[]`` shape for a new document.

    Records stay compatible with the existing tabular shape (``activity``,
    ``quantity``, ``unit``) and add P1 provenance: ``page``, ``page_basis``,
    ``page_trust``, ``extraction_method``, ``line_number`` and ``source_line``.
    """
    from services.automatic_extraction import _detect_activity, _detect_unit

    pages, page_basis, page_resolution = split_pages(text, method=method)
    stamp = method_stamp(method=method, ai_used=ai_used)
    items: list[dict[str, Any]] = []
    for page_index, page in enumerate(pages, start=1):
        for line in find_source_lines(page):
            record: dict[str, Any] = {}
            activity = _detect_activity(line["description"]) if line.get("description") else None
            if activity:
                record["activity"] = activity
            if line.get("quantity") is not None:
                record["quantity"] = line["quantity"]
            unit = _detect_unit(line["raw"])
            if unit:
                record["unit"] = unit
            if not record.get("activity") and not record.get("unit"):
                continue
            record["page"] = page_index
            record["page_basis"] = page_basis
            record["page_trust"] = "lower" if page_basis == "marker" else "standard"
            record["extraction_method"] = stamp
            record["line_number"] = len(items) + 1
            record["source_line"] = line["raw"]
            items.append(record)
    coverage = classify(text, method=method, page_count=page_count).as_coverage()
    coverage["page_basis"] = page_basis
    coverage["page_resolution"] = page_resolution
    coverage["line_items"] = len(items)
    coverage["extraction_method"] = stamp
    return items, coverage
