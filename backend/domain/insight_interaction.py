"""CarbonTally Insight I4 — Layer-2 interaction contract (authorized I4 stage).

Authorization: PO I4 Implementation Authorization (2026-09-21) and the PO Q1–Q14
decision register. Ratified authority: D2 §7 (Layer 2 = I4), §8/§9.2 (every read
re-authorised; creator-private), §3.2.1/§3.8 (canonical ``carbontally_insight_*``
names); Master Spec v1.1 §8.1/§9.3 (Layer-2 record), §14 (answer states), §20
(audit separation).

Boundaries encoded here (not decorative):

* **Q3** — the I4 *answer* vocabulary is a separate contract from the closed I3
  ``ToolStatus`` vocabulary. This module never mutates ``domain.insight_tool``.
* **Q4** — no raw question text is carried in a Layer-2 record: only a sha256
  hash for correlation/integrity; the raw question lives in the I1 message layer.
* **Q5** — records are evidence: append-only, forward-only lifecycle.
* **Q6** — only allowlisted argument/result *projections* are persisted.
* **Q9** — immutable ``interaction_id`` with child ``tool_call_id`` correlation.
* Pure contract/typing: no I/O, no database, no provider, no authorization decision.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping, Optional, Sequence

#: Stamped on every persisted Layer-2 record so an auditor can attribute it to a
#: known contract version without re-deriving it from code.
INTERACTION_CONTRACT_VERSION = "i4-layer2-v1"

#: Bounded input (Q4/Q10).
MAX_QUESTION_LENGTH = 2000
MAX_IDEMPOTENCY_KEY_LENGTH = 128
#: At most one call per ratified tool (the catalogue has exactly four).
MAX_TOOL_CALLS_PER_INTERACTION = 4
#: Bounded provider attempts (Q10) — no unbounded retry loop.
MAX_PROVIDER_ATTEMPTS = 2


class InteractionLifecycle(StrEnum):
    """PO Q7 — Layer 2 owns the interaction lifecycle."""

    RECEIVED = "received"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnswerStatus(StrEnum):
    """Authoritative I4 answer states (Master Spec §14, PO Q3).

    The specification enumerates fourteen states; Phase 8 Insight analytics adds
    **one**, ``multiple_matches``, authorized by the PO Insight
    Discovery-Aggregation-Provenance package (2026-09-22): a bounded discovery
    that matched several authoritative calculation records must say so rather
    than silently choosing one. ``success`` is the specification's
    ``success / answered``. This vocabulary is deliberately not the I3
    ``ToolStatus`` vocabulary and must not be merged with it.
    """

    SUCCESS = "success"
    ZERO = "zero"
    NO_DATA = "no_data"
    NOT_AUTHORIZED = "not_authorized"
    INSUFFICIENT_DATA = "insufficient_data"
    NEEDS_CLARIFICATION = "needs_clarification"
    MULTIPLE_MATCHES = "multiple_matches"
    TOOL_FAILURE = "tool_failure"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PARTIAL = "partial"
    RATE_LIMITED = "rate_limited"
    REFUSED = "refused"
    UNGROUNDED = "ungrounded"
    INVALID_INPUT = "invalid_input"
    ERROR = "error"


class NarrationState(StrEnum):
    """PO Q11/Q14 — whether provider narration ran, and truthfully why not."""

    NOT_ATTEMPTED = "not_attempted"
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"


#: The closed I3 tool vocabulary, mirrored read-only for persistence validation.
ALLOWED_TOOL_STATUSES: tuple[str, ...] = (
    "success",
    "no_data",
    "not_authorized",
    "invalid_input",
    "provider_unavailable",
    "error",
)

#: The ratified reference domains (locators, never grants).
ALLOWED_REFERENCE_KINDS: tuple[str, ...] = (
    "report",
    "report_version",
    "evidence_line_item",
    "calculation_snapshot",
)

#: Q6 — the only argument names any I4 tool call may persist, per tool. Derived
#: from the ratified I3 ``ToolInputSpec``; an unknown tool persists nothing.
TOOL_ARGUMENT_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "report_lookup": ("report_id",),
    "report_version_lookup": ("version_id", "report_id", "version_number"),
    "report_evidence_lookup": ("report_version_id",),
    "calculation_snapshot_lookup": ("snapshot_id",),
    # Phase 8 Insight analytics (bounded typed inputs only; no free text).
    "insight_discovery": (
        "start_date",
        "end_date",
        "reporting_year",
        "co2e_kg",
        "co2e_tolerance_kg",
        "co2e_tolerance_pct",
        "co2e_approx",
        "activity",
        "scope",
        "supplier_id",
        "facility_id",
        "asset_id",
        "limit",
    ),
    "insight_aggregation": ("group_by", "start_date", "end_date", "limit"),
    "insight_aggregate_provenance": (
        "group_by",
        "group_key",
        "start_date",
        "end_date",
        "limit",
    ),
}

#: Q6 — the only result-metadata keys an I4 tool call may persist. Everything
#: else (raw rows, content fields, signed URLs) is excluded by omission.
RESULT_METADATA_ALLOWLIST: tuple[str, ...] = (
    "status",
    "reason",
    "item_count",
    "truncated",
    "reference_kinds",
    "reference_count",
    "contract_version",
    # Phase 8 analytics: a bounded match/group *count* is metadata, not content.
    "match_count",
)

_ANSWER_ORDER: tuple[AnswerStatus, ...] = (
    AnswerStatus.ERROR,
    AnswerStatus.NOT_AUTHORIZED,
    AnswerStatus.INVALID_INPUT,
    AnswerStatus.RATE_LIMITED,
    AnswerStatus.REFUSED,
    AnswerStatus.MULTIPLE_MATCHES,
    AnswerStatus.TOOL_FAILURE,
    AnswerStatus.PARTIAL,
    AnswerStatus.NO_DATA,
    AnswerStatus.SUCCESS,
)

_TOOL_TO_ANSWER: dict[str, AnswerStatus] = {
    "success": AnswerStatus.SUCCESS,
    "no_data": AnswerStatus.NO_DATA,
    "not_authorized": AnswerStatus.NOT_AUTHORIZED,
    "invalid_input": AnswerStatus.INVALID_INPUT,
    "provider_unavailable": AnswerStatus.PROVIDER_UNAVAILABLE,
    "error": AnswerStatus.ERROR,
}


def hash_text(value: str) -> str:
    """Stable sha256 hex digest of a string (Q4/Q10 correlation + integrity)."""
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def tool_answer_status(tool_status: str) -> AnswerStatus:
    """Map one closed I3 tool status onto an I4 answer state (Q3)."""
    try:
        return _TOOL_TO_ANSWER[str(tool_status)]
    except KeyError as exc:  # pragma: no cover - defensive
        raise ValueError(f"unratified tool status: {tool_status!r}") from exc


def combine_answer_statuses(statuses: Sequence[AnswerStatus]) -> AnswerStatus:
    """Deterministically combine several tool outcomes into one answer state.

    Mixed success/no_data and multi-outcome cases are reported truthfully as
    ``partial`` rather than being flattened into a single tool's outcome.
    """
    seen = list(dict.fromkeys(statuses))
    if not seen:
        return AnswerStatus.NO_DATA
    if len(seen) == 1:
        return seen[0]
    for status in _ANSWER_ORDER:
        if status is AnswerStatus.PARTIAL:
            continue
        if status in seen:
            return status
    return AnswerStatus.PARTIAL


def project_tool_arguments(tool_name: str, payload: Mapping[str, Any]) -> dict[str, str]:
    """Q6 — allowlisted projection of the arguments actually used by a tool call.

    Unknown tools project to an empty mapping (omission, never inference). Values
    are coerced to bounded strings; nothing else is carried.
    """
    allowed = TOOL_ARGUMENT_ALLOWLIST.get(tool_name, ())
    projected: dict[str, str] = {}
    for key in allowed:
        if key in payload and payload[key] is not None:
            projected[key] = str(payload[key])[:256]
    return projected


def project_result_metadata(result: Mapping[str, Any], *, contract_version: str) -> dict[str, Any]:
    """Q6 — allowlisted projection of a ratified I3 ``ToolResult``.

    Only status/reason/bounds/reference *kinds* are persisted. The result ``data``
    payload and any signed URLs never enter Layer 2.
    """
    data = result.get("data") or {}
    references = result.get("references") or []
    kinds = sorted({str(r.get("kind")) for r in references if isinstance(r, Mapping)})
    item_count = 0
    for value in data.values() if isinstance(data, Mapping) else []:
        if isinstance(value, (list, tuple)):
            item_count += len(value)
    projected: dict[str, Any] = {
        "status": str(result.get("status")) if result.get("status") else None,
        "reason": result.get("reason"),
        "item_count": item_count,
        "truncated": bool(result.get("truncated", False)),
        "reference_kinds": kinds,
        "reference_count": len(references),
        "contract_version": contract_version,
    }
    # A bounded match count is evidence metadata (how many records matched), never
    # record content, so it may be persisted where the tool reports one.
    if isinstance(data, Mapping) and isinstance(data.get("match_count"), int):
        projected["match_count"] = int(data["match_count"])
    return {k: v for k, v in projected.items() if k in RESULT_METADATA_ALLOWLIST}


@dataclass(frozen=True, slots=True)
class InsightInteraction:
    """One Layer-2 interaction (PO Q7/Q9) as persisted."""

    id: str
    organization_id: str
    conversation_id: str
    created_by: str
    lifecycle: str
    answer_status: Optional[str]
    message_id: Optional[str]
    audit_record_id: Optional[str]
    idempotency_key: Optional[str]
    question_hash: str
    request_hash: Optional[str]
    intent: Optional[str]
    intent_source: Optional[str]
    provider: Optional[str]
    model: Optional[str]
    model_version: Optional[str]
    narration_state: str
    tokens_used: Optional[int]
    cost: Optional[float]
    tool_call_count: int
    reference_count: int
    error_class: Optional[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class InsightToolCall:
    """One append-only tool-call evidence row (PO Q6/Q9)."""

    id: str
    interaction_id: str
    organization_id: str
    call_ordinal: int
    tool_name: str
    contract_version: str
    tool_status: str
    arguments: dict[str, Any] = field(default_factory=dict)
    result_metadata: dict[str, Any] = field(default_factory=dict)
    references: tuple[dict[str, str], ...] = ()
    arguments_hash: str = ""
    result_hash: str = ""
    result_item_count: int = 0
    truncated: bool = False
    duration_ms: Optional[int] = None
    created_at: Optional[datetime] = None
