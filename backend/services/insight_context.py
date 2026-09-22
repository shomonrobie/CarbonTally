"""CarbonTally Insight I5 — bounded, deterministic context assembly.

Authorization: PO I5 implementation authorization (2026-09-21) against
``docs/architecture/CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md``.

Ratified I5 decisions implemented here (nothing else):

* **current-conversation context only** (I5-1, I5-9) — no cross-conversation memory;
* **deterministic, bounded selection** with chronological ordering and most-recent
  preference within the configured budget (I5-1);
* **configurable 20,000-character maximum** assembled historical context,
  enforced **before provider submission** (I5-3);
* **no AI summarization/compaction and no persisted summaries** (I5-2, I5-4);
* historical context is **never authoritative** and cannot override a current
  authorized lookup (I5-5), and stale references are presented only as locators;
* only **bounded structured historical interaction/tool-result projections** are
  used — never unrestricted historical payloads (I5-6);
* ``public.audit_trail`` is **not** conversational context (I5-7);
* **empty context is normal** and never becomes ``zero`` (I5-8);
* every protected read passes through the existing I2 boundary.

No token-counting library, no embeddings/vector search, no RAG, no summarisation,
no persistence: this module only *reads* (messages/interactions/tool calls) and
returns an in-memory, character-bounded structure.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Sequence

from fastapi import HTTPException

if TYPE_CHECKING:  # pragma: no cover - type-only (no import-time api dependency)
    from api.dependencies import RepositoryBundle
    from auth import AuthUser

logger = logging.getLogger(__name__)

#: Version stamp of the selection/truncation policy (deterministic contract).
CONTEXT_POLICY_VERSION = "i5-context-v1"

#: PO I5-3 — the ratified maximum assembled historical context (characters).
DEFAULT_MAX_HISTORY_CHARS = 20_000

#: Optional operator override of the budget (configuration, not policy).
_MAX_CHARS_ENV = "CARBONTALLY_INSIGHT_CONTEXT_MAX_CHARS"

#: Bounded read: at most this many prior interactions of the current conversation
#: are considered, newest first, before the budget is applied.
MAX_HISTORY_INTERACTIONS = 50

#: At most this many tool-call projections per interaction (the authorized I3
#: catalogue is four ratified tools plus three Phase 8 analytics tools).
MAX_TOOL_CALLS_PER_INTERACTION = 7

#: A single historical block may never consume more than this share of the budget.
MAX_BLOCK_CHARS = 2_000

#: Evidence classes: history is explicitly marked non-authoritative (I5-5).
EVIDENCE_CLASS_CURRENT = "current_authoritative"
EVIDENCE_CLASS_HISTORY = "historical_context_not_authoritative"

#: Projection allowlist for a historical tool call (I5-6). Anything else, notably
#: result payloads, arguments and URLs, is excluded by omission.
_TOOL_CALL_PROJECTION_FIELDS: tuple[str, ...] = (
    "tool",
    "status",
    "reason",
    "contract_version",
    "result_item_count",
    "truncated",
    "duration_ms",
)


def configured_max_history_chars() -> int:
    """The configured history budget: the ratified default, or an operator override.

    Returns ``DEFAULT_MAX_HISTORY_CHARS`` (20,000) unless
    ``CARBONTALLY_INSIGHT_CONTEXT_MAX_CHARS`` sets a positive integer. The value is
    always positive, so a misconfiguration can never remove the bound.
    """
    raw = (os.getenv(_MAX_CHARS_ENV) or "").strip()
    if raw:
        try:
            value = int(raw)
        except ValueError:
            logger.warning("%s is not an integer; using the ratified default", _MAX_CHARS_ENV)
        else:
            if value > 0:
                return value
            logger.warning("%s must be > 0; using the ratified default", _MAX_CHARS_ENV)
    return DEFAULT_MAX_HISTORY_CHARS


@dataclass(frozen=True, slots=True)
class ContextBlock:
    """One historical interaction of the current conversation (structured only)."""

    interaction_id: str
    created_at: Optional[str]
    lifecycle: str
    answer_status: Optional[str]
    narration_state: str
    intent: Optional[str]
    authoritative: bool = False
    tool_calls: tuple[dict[str, Any], ...] = ()
    references: tuple[dict[str, str], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "created_at": self.created_at,
            "lifecycle": self.lifecycle,
            "answer_status": self.answer_status,
            "narration_state": self.narration_state,
            "intent": self.intent,
            "evidence_class": (
                EVIDENCE_CLASS_CURRENT if self.authoritative else EVIDENCE_CLASS_HISTORY
            ),
            "tool_calls": [dict(t) for t in self.tool_calls],
            "references": [dict(r) for r in self.references],
        }


@dataclass(frozen=True, slots=True)
class InsightContext:
    """The assembled, character-bounded context for one interaction.

    ``question`` is the current question, preserved verbatim (PO I5-3). It is *not*
    counted against the historical budget: the budget bounds the assembled
    **historical** context only.
    """

    conversation_id: str
    organization_id: str
    question: str
    history_text: str
    blocks: tuple[ContextBlock, ...] = ()
    max_chars: int = DEFAULT_MAX_HISTORY_CHARS
    truncated: bool = False
    policy_version: str = CONTEXT_POLICY_VERSION

    @property
    def used_chars(self) -> int:
        return len(self.history_text)

    @property
    def empty(self) -> bool:
        """An empty context is a normal condition (PO I5-8) — never an error."""
        return not self.blocks

    @property
    def interaction_count(self) -> int:
        return len(self.blocks)

    def as_dict(self) -> dict[str, Any]:
        """Diagnostic view. ``history_text`` is included for tests/observability."""
        return {
            "conversation_id": self.conversation_id,
            "organization_id": self.organization_id,
            "question": self.question,
            "history_text": self.history_text,
            "used_chars": self.used_chars,
            "max_chars": self.max_chars,
            "truncated": self.truncated,
            "empty": self.empty,
            "interaction_count": self.interaction_count,
            "policy_version": self.policy_version,
        }


def _i2():
    """Deferred import of the closed I2 boundary (no import-time api cycle)."""
    from api import insight_authz as module

    return module


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _project_tool_call(call: Any) -> dict[str, Any]:
    """Bounded structured projection of one historical tool call (I5-6).

    Only the allowlisted fields survive; arguments, result payloads and any URLs are
    excluded by omission. References are carried as locators (``kind``/``id``) and
    are never treated as authorization.
    """
    projected: dict[str, Any] = {}
    for name in _TOOL_CALL_PROJECTION_FIELDS:
        if name == "tool":
            projected["tool"] = getattr(call, "tool_name", None)
        elif name == "status":
            projected["status"] = getattr(call, "tool_status", None)
        elif name == "reason":
            projected["reason"] = (getattr(call, "result_metadata", None) or {}).get("reason")
        elif name == "result_item_count":
            projected["result_item_count"] = int(getattr(call, "result_item_count", 0) or 0)
        elif name == "truncated":
            projected["truncated"] = bool(getattr(call, "truncated", False))
        else:
            projected[name] = getattr(call, name, None)
    kinds = sorted(
        {str(r.get("kind")) for r in (getattr(call, "references", ()) or ()) if isinstance(r, dict)}
    )
    projected["reference_kinds"] = kinds
    return projected


def _project_references(call: Any) -> tuple[dict[str, str], ...]:
    out: list[dict[str, str]] = []
    for ref in getattr(call, "references", ()) or ():
        if isinstance(ref, dict) and "kind" in ref and "id" in ref:
            out.append({"kind": str(ref["kind"]), "id": str(ref["id"])})
    return tuple(out)


async def assemble_context(
    *,
    current_user: "AuthUser",
    repos: "RepositoryBundle",
    organization_id: str,
    conversation_id: str,
    question: str,
    max_chars: Optional[int] = None,
    exclude_interaction_id: Optional[str] = None,
) -> InsightContext:
    """Assemble the bounded historical context of one conversation (PO I5-1…I5-9).

    Raises ``HTTPException`` exactly like the rest of Insight: authorization is the
    closed I2 boundary, and a conversation the caller may not see is reported as
    absent (404) so existence is never disclosed.

    Determinism: identical authorized inputs against unchanged data produce an
    identical ``InsightContext`` (no clock, no randomness, stable ordering).
    """
    budget = DEFAULT_MAX_HISTORY_CHARS if max_chars is None else int(max_chars)
    if budget < 1:
        raise HTTPException(status_code=422, detail="max_chars must be >= 1")

    i2 = _i2()
    # I2 remains the sole authorization boundary (PO 3.1/I5 boundary).
    access = await i2.authorize_insight_scope(current_user, repos, organization_id)

    conversation = await repos.insight.get_conversation(
        conversation_id=conversation_id, organization_id=organization_id
    )
    if conversation is None or not i2.conversation_is_visible(access, conversation):
        # Another customer's / another creator's conversation is never loaded (404).
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Current conversation only, creator-private, newest first (deterministic).
    candidates = await repos.insight_interactions.list_interactions(
        organization_id=organization_id,
        created_by=access.user_id,
        conversation_id=conversation.id,
        limit=MAX_HISTORY_INTERACTIONS,
        offset=0,
    )

    # Build newest-first, consuming the budget from the most recent material, then
    # emit chronologically. Every step is deterministic for the same inputs.
    selected: list[ContextBlock] = []
    used = 0
    dropped = 0
    overflow = False
    overflow_text = ""
    for row in candidates:
        if exclude_interaction_id and str(row.id) == str(exclude_interaction_id):
            continue
        calls = await repos.insight_interactions.list_tool_calls(
            interaction_id=row.id, organization_id=organization_id
        )
        block = ContextBlock(
            interaction_id=str(row.id),
            created_at=row.created_at.isoformat() if row.created_at else None,
            lifecycle=row.lifecycle,
            answer_status=row.answer_status,
            narration_state=row.narration_state,
            intent=row.intent,
            tool_calls=tuple(
                _project_tool_call(c) for c in list(calls)[:MAX_TOOL_CALLS_PER_INTERACTION]
            ),
            references=tuple(
                ref
                for c in list(calls)[:MAX_TOOL_CALLS_PER_INTERACTION]
                for ref in _project_references(c)
            ),
        )
        rendered = _json(block.as_dict())
        if len(rendered) > MAX_BLOCK_CHARS:
            rendered = rendered[:MAX_BLOCK_CHARS]
            block = ContextBlock(
                interaction_id=block.interaction_id,
                created_at=block.created_at,
                lifecycle=block.lifecycle,
                answer_status=block.answer_status,
                narration_state=block.narration_state,
                intent=block.intent,
                tool_calls=(),
                references=block.references,
            )
            rendered = _json(block.as_dict())
        if used + len(rendered) > budget:
            if not selected:
                # PO I5-1(4)/I5-3: the most recent material is preferred, so when
                # even the newest block cannot fit whole it is included truncated to
                # the remaining budget rather than dropping all context. The bound is
                # still never exceeded, and the truncation point is deterministic.
                overflow_block = block
                overflow_text = rendered[:budget]
                overflow = True
                used = budget
                dropped += 1
                selected.append(block)
            else:
                dropped += 1
            continue
        selected.append(block)
        used += len(rendered)

    ordered = list(reversed(selected))  # chronological ascending for coherence
    if overflow and overflow_text:
        history_text = overflow_text
    else:
        history_text = _json([b.as_dict() for b in ordered]) if ordered else ""
    if len(history_text) > budget:  # defensive: the bound must never be exceeded
        history_text = history_text[:budget]

    return InsightContext(
        conversation_id=conversation.id,
        organization_id=conversation.organization_id,
        question=question,
        history_text=history_text,
        blocks=tuple(ordered),
        max_chars=budget,
        truncated=dropped > 0,
    )


def context_prompt_sections(context: InsightContext) -> dict[str, str]:
    """Prompt-ready sections with the precedence rule stated explicitly (I5-5).

    The historical section is labelled non-authoritative, so a model can never be
    led to treat prior text as the current authoritative result, and an empty
    context is presented as a normal condition rather than as ``zero`` (I5-8).
    """
    return {
        "historical_context": context.history_text or "(no prior conversation context)",
        "historical_context_is_authoritative": "false",
        "historical_context_is_empty": "true" if context.empty else "false",
        "current_question": context.question,
    }


__all__ = [
    "CONTEXT_POLICY_VERSION",
    "ContextBlock",
    "DEFAULT_MAX_HISTORY_CHARS",
    "InsightContext",
    "MAX_HISTORY_INTERACTIONS",
    "MAX_TOOL_CALLS_PER_INTERACTION",
    "assemble_context",
    "configured_max_history_chars",
    "context_prompt_sections",
]
