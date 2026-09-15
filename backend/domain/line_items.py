"""B2 — evidence line-item materialisation domain logic (pure, no I/O).

Implements the *normative* derivation rules of the ratified Phase 8 B2 contract
(``docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md``
§11.1/§11.2/§11.3/§11.7) as deterministic, side-effect-free functions so the
eligibility, canonical-payload, ordinal and divergence rules are unit-testable
without a database and are shared verbatim by the forward hook, the read layer
and the Class-1 backfill.

Boundaries this module must never cross (contract §6, §11.4, §22.2):

* It never reads ``mapped_data`` — line identity derives **only** from the
  persisted ``extracted_data.line_items[]`` (§11.1, F-B2-4).
* It never fabricates a line for a flat document and never splits an aggregate
  into synthetic rows (manufacturing granularity is prohibited; P1 owns
  extraction fidelity).
* It never invents ``source_page`` / ``row_reference``: they are populated only
  from the element's own optional keys (§11.7), never from ``page_count``
  (F-B2-7 is a separate workstream; B2-D4).
* It performs no re-parsing, OCR, LLM or heuristic step of any kind.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Optional, Sequence

# ---------------------------------------------------------------------------
# Vocabulary (contract §11.2)
# ---------------------------------------------------------------------------

#: The union of what the extractors actually emit (F-B2-5/F-B2-6).
LINE_ITEM_VALUE_KEYS: tuple[str, ...] = (
    "activity",
    "description",
    "item",
    "quantity",
    "unit",
    "amount",
    "currency",
    "supplier",
    "date",
    "invoice_number",
)

#: ``raw_description`` = first non-empty of these, in this order (§11.2).
DESCRIPTION_KEYS: tuple[str, ...] = ("activity", "description", "item")

#: Optional per-line location/provenance keys a future extractor may supply
#: (§11.7 — the complete B2↔P1 interface; none has a producer today).
PER_LINE_PAGE_KEY = "page"
PER_LINE_REFERENCE_KEY = "line_reference"
PER_LINE_EXTRACTION_METHOD_KEY = "extraction_method"

#: Honest default when the write site cannot supply the producing path (§11.2).
UNKNOWN_EXTRACTION_METHOD = "unknown"

#: ``evidence_line_items.materialisation_kind`` values (B2-D10).
MATERIALISATION_FORWARD = "FORWARD"
MATERIALISATION_BACKFILL = "BACKFILL"
MATERIALISATION_KINDS: tuple[str, ...] = (
    MATERIALISATION_FORWARD,
    MATERIALISATION_BACKFILL,
)

#: Per-ordinal materialisation decision (§11.3).
ACTION_INSERT = "INSERT"
ACTION_SKIP_EXISTS = "SKIP_EXISTS"
ACTION_DIVERGENCE = "DIVERGENCE"

#: Audit actions (contract §17) — they extend the established ``report:``
#: namespace used by B1 (``report:disclosure_*``). No parallel audit system is
#: created: the existing ``audit_trail`` / ``data.audit.AuditRepository``
#: mechanism is reused.
AUDIT_LINE_ITEMS_MATERIALISED = "report:evidence_line_items_materialised"
AUDIT_LINE_ITEMS_BACKFILLED = "report:evidence_line_items_backfilled"
AUDIT_LINE_ITEMS_DIVERGENCE_DETECTED = (
    "report:evidence_line_items_divergence_detected"
)

AUDIT_ACTIONS: tuple[str, ...] = (
    AUDIT_LINE_ITEMS_MATERIALISED,
    AUDIT_LINE_ITEMS_BACKFILLED,
    AUDIT_LINE_ITEMS_DIVERGENCE_DETECTED,
)


#: ``line_count`` sentinel for an ineligible item (§11.1).
INELIGIBLE_LINE_COUNT = -1


def _is_empty(value: Any) -> bool:
    """``True`` when ``value`` carries nothing (None, blank text, empty list)."""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) == 0
    return False


def canonical_value(value: Any) -> Optional[str]:
    """Canonical string form of a scalar payload value (``None`` = omit).

    Contract §11.2: numbers are normalised via
    ``format(Decimal(str(v)).normalize(), "f")`` so ``100``, ``100.0`` and
    ``100.00`` hash identically (int/float drift must never create a *false*
    divergence). Non-scalar values are omitted. Text is kept as extracted
    (whitespace-trimmed) — including text that is not numeric.
    """
    if isinstance(value, bool):
        # JSON booleans are canonicalised explicitly: they are scalars, but they
        # are not quantities and Decimal(True) is meaningless.
        return "true" if value else "false"
    if isinstance(value, (int, float, Decimal)):
        try:
            return format(Decimal(str(value)).normalize(), "f")
        except (InvalidOperation, ValueError):
            return str(value)
    if isinstance(value, str):
        text = value.strip()
        try:
            return format(Decimal(text).normalize(), "f")
        except (InvalidOperation, ValueError):
            return text
    if isinstance(value, (list, tuple, dict, set)):
        return None  # non-scalar ⇒ omitted from the canonical payload
    return str(value)


def canonical_payload(element: Mapping[str, Any]) -> dict[str, str]:
    """The recognised-key payload of one element, canonicalised (§11.2).

    Only recognised keys carrying a non-empty scalar value are included; the
    result is JSON-serialisable with a deterministic key order (``sort_keys``).
    """
    payload: dict[str, str] = {}
    for key in LINE_ITEM_VALUE_KEYS:
        if key not in element:
            continue
        rendered = canonical_value(element.get(key))
        if rendered is None or rendered == "":
            continue
        payload[key] = rendered
    return payload


def compute_payload_hash(element: Mapping[str, Any]) -> str:
    """``sha256(canonical_json(payload))`` — keys sorted, compact separators, UTF-8."""
    payload = canonical_payload(element)
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_decimal(value: Any) -> Optional[Decimal]:
    """``quantity`` as a ``Decimal``, else ``None`` (§11.2 — never guessed)."""
    if isinstance(value, bool) or _is_empty(value):
        return None
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None


def first_text(element: Mapping[str, Any], keys: Sequence[str]) -> Optional[str]:
    """First non-empty text value among ``keys`` (whitespace-trimmed)."""
    for key in keys:
        value = element.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()


def _per_line_page(element: Mapping[str, Any]) -> Optional[int]:
    """``source_page`` from the element's own ``page`` key, else ``None`` (§11.7)."""
    value = element.get(PER_LINE_PAGE_KEY)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if value >= 1 else None


def _per_line_reference(element: Mapping[str, Any]) -> Optional[str]:
    """``row_reference`` from the element's own ``line_reference`` key, else ``None``."""
    value = element.get(PER_LINE_REFERENCE_KEY)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _per_line_extraction_method(element: Mapping[str, Any]) -> Optional[str]:
    """Per-line method override, else ``None`` (document-level attribution applies)."""
    value = element.get(PER_LINE_EXTRACTION_METHOD_KEY)
    return value.strip() if isinstance(value, str) and value.strip() else None


# ---------------------------------------------------------------------------
# Derivation (§11.1 / §11.2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LineCandidate:
    """One materialisable line: its ordinal and every derived column value."""

    line_number: int
    payload_hash: str
    raw_description: Optional[str]
    raw_quantity: Optional[Decimal]
    raw_unit: Optional[str]
    source_page: Optional[int]
    row_reference: Optional[str]
    extraction_method_override: Optional[str]


@dataclass(frozen=True)
class DerivationResult:
    """Outcome of deriving one item's lines (§11.1 skip categories)."""

    eligible: bool
    line_count: int
    candidates: tuple[LineCandidate, ...]
    skipped_empty: int
    skipped_malformed: int
    skipped_no_lines: int

    @property
    def materialisable(self) -> int:
        return len(self.candidates)


def derive_line_candidates(extracted_data: Any) -> DerivationResult:
    """Derive the materialisable lines of one extraction item (§11.1/§11.2).

    Eligibility is a pure function of the persisted JSONB: ``extracted_data``
    must be an object whose ``line_items`` is an array. An array that is present
    but empty yields 0 rows and is counted as ``skipped_no_lines`` — it **never**
    falls back to the flat record. A skipped element leaves a permanent ordinal
    **gap**: ordinals are never renumbered.
    """
    if not isinstance(extracted_data, Mapping):
        return DerivationResult(False, INELIGIBLE_LINE_COUNT, (), 0, 0, 0)
    line_items = extracted_data.get("line_items")
    if not isinstance(line_items, list):
        return DerivationResult(False, INELIGIBLE_LINE_COUNT, (), 0, 0, 0)
    if len(line_items) == 0:
        return DerivationResult(True, 0, (), 0, 0, 1)

    candidates: list[LineCandidate] = []
    skipped_empty = 0
    skipped_malformed = 0
    for index, element in enumerate(line_items):
        ordinal = index + 1  # 1-based; never renumbered (§7.1)
        if not isinstance(element, Mapping):
            skipped_malformed += 1
            continue
        if not canonical_payload(element):
            skipped_empty += 1
            continue
        raw_unit = element.get("unit")
        candidates.append(
            LineCandidate(
                line_number=ordinal,
                payload_hash=compute_payload_hash(element),
                raw_description=first_text(element, DESCRIPTION_KEYS),
                raw_quantity=parse_decimal(element.get("quantity")),
                raw_unit=(
                    raw_unit.strip()
                    if isinstance(raw_unit, str) and raw_unit.strip()
                    else None
                ),
                source_page=_per_line_page(element),
                row_reference=_per_line_reference(element),
                extraction_method_override=_per_line_extraction_method(element),
            )
        )
    return DerivationResult(
        True,
        len(line_items),
        tuple(candidates),
        skipped_empty,
        skipped_malformed,
        0,
    )


# ---------------------------------------------------------------------------
# Rerun / divergence decisions (§11.3, B2-D2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OrdinalDecision:
    """What a rerun must do with one already-known-or-new ordinal."""

    line_number: int
    action: str
    line_id: Optional[str] = None
    stored_hash: Optional[str] = None
    current_hash: Optional[str] = None


def decide_ordinals(
    candidates: Sequence[LineCandidate],
    existing: Mapping[int, tuple[str, str]],
) -> tuple[OrdinalDecision, ...]:
    """Insert-if-absent / skip-if-present / report-if-divergent (§11.3).

    ``existing`` maps ``line_number → (line_id, payload_hash)`` as persisted.
    A hash difference is a **DIVERGENCE**: reported, never reconciled in place
    (B2-D2 — detect + report + never rewrite; ``ON CONFLICT DO NOTHING``, never
    B1's ``DO UPDATE``, because a line row is immutable evidence).
    """
    decisions: list[OrdinalDecision] = []
    for candidate in candidates:
        current = existing.get(candidate.line_number)
        if current is None:
            decisions.append(
                OrdinalDecision(
                    line_number=candidate.line_number,
                    action=ACTION_INSERT,
                    current_hash=candidate.payload_hash,
                )
            )
            continue
        line_id, stored_hash = current
        if stored_hash == candidate.payload_hash:
            decisions.append(
                OrdinalDecision(
                    line_number=candidate.line_number,
                    action=ACTION_SKIP_EXISTS,
                    line_id=line_id,
                    stored_hash=stored_hash,
                    current_hash=candidate.payload_hash,
                )
            )
        else:
            decisions.append(
                OrdinalDecision(
                    line_number=candidate.line_number,
                    action=ACTION_DIVERGENCE,
                    line_id=line_id,
                    stored_hash=stored_hash,
                    current_hash=candidate.payload_hash,
                )
            )
    return tuple(decisions)

    return None
