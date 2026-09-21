"""CarbonTally Insight I4 — interaction orchestration (authorized I4 stage).

Authorization: PO I4 Implementation Authorization (2026-09-21) with the PO Q1–Q14
decision register. This module implements the authorized orchestration path:

1. authorize the caller through the closed I2 boundary (``authorize_insight_scope``);
2. persist the raw question once, in the I1 message layer (PO Q4);
3. classify intent deterministically and execute only the ratified I3 tools;
4. re-authorize every read (I2/I3 do this — never re-implemented here);
5. persist append-only Layer-2 evidence (PO Q5/Q6/Q9);
6. optionally narrate through the **existing** provider abstraction (PO Q14);
7. produce a truthful I4 answer state (PO Q3) and append the canonical audit
   event to ``public.audit_trail`` through the existing audit infrastructure (Q2).

Hard boundaries: the LLM/provider never authorizes anything; a provider failure
never produces a fabricated answer (Q11); no tool, persona, permission, RAG,
embedding, billing, retention or export behaviour exists here (Q6/Q12/Q13/Q14).
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Sequence

from fastapi import HTTPException

from domain.insight_interaction import (
    ALLOWED_TOOL_STATUSES,
    AnswerStatus,
    INTERACTION_CONTRACT_VERSION,
    InteractionLifecycle,
    MAX_IDEMPOTENCY_KEY_LENGTH,
    MAX_PROVIDER_ATTEMPTS,
    MAX_QUESTION_LENGTH,
    NarrationState,
    combine_answer_statuses,
    hash_text,
    project_result_metadata,
    project_tool_arguments,
    tool_answer_status,
)
from infra.audit_logger import AuditLogger
from services.insight_tools import classify_intent, invoke_tool

if TYPE_CHECKING:  # pragma: no cover - type-only (no import-time api dependency)
    from api.dependencies import RepositoryBundle
    from auth import AuthUser
    from infra.llm_client import LLMClient

logger = logging.getLogger(__name__)

NARRATION_NONE = "none"
NARRATION_OPTIONAL = "optional"
NARRATION_REQUIRED = "required"
NARRATION_MODES: tuple[str, ...] = (NARRATION_NONE, NARRATION_OPTIONAL, NARRATION_REQUIRED)

MAX_QUESTION_CHARS = MAX_QUESTION_LENGTH
MAX_NARRATION_CONTEXT_CHARS = 2000

_SYSTEM_PROMPT = (
    "You are CarbonTally Insight. Explain only what the provided structured "
    "evidence shows. Never invent emission factors, calculations, report values, "
    "evidence identities, citations, authorisation or tool results. If the "
    "evidence does not establish something, say so plainly. Do not claim that a "
    "value was calculated unless it appears in the evidence."
)

_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

#: Which identifier each ratified tool needs in order to be scoped truthfully.
#: ``None`` means the tool accepts a version identifier.
_TOOL_SCOPE_ARGUMENT: dict[str, Optional[str]] = {
    "report_lookup": "report_id",
    "report_version_lookup": None,
    "report_evidence_lookup": "report_version_id",
    "calculation_snapshot_lookup": "snapshot_id",
}

#: Intent refusals map onto the *I4* answer vocabulary (PO Q3) — never onto a new
#: status, and never onto a fabricated tool call.
_INTENT_REFUSAL_ANSWER: dict[str, AnswerStatus] = {
    "ambiguous_intent": AnswerStatus.NEEDS_CLARIFICATION,
    "unsupported_intent": AnswerStatus.REFUSED,
    "empty_utterance": AnswerStatus.INVALID_INPUT,
    "utterance_too_long": AnswerStatus.INVALID_INPUT,
}


@dataclass(frozen=True, slots=True)
class InteractionOutcome:
    """What one I4 interaction produced (truthful, bounded, no raw payloads)."""

    interaction_id: str
    organization_id: str
    conversation_id: str
    lifecycle: str
    answer_status: str
    narration_state: str
    narration_text: Optional[str]
    intent: Optional[str]
    intent_source: Optional[str]
    provider: Optional[str]
    model: Optional[str]
    model_version: Optional[str]
    tokens_used: Optional[int]
    cost: Optional[float]
    message_id: Optional[str]
    audit_record_id: Optional[str]
    tool_calls: tuple[dict[str, Any], ...] = ()
    references: tuple[dict[str, str], ...] = ()
    replayed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "organization_id": self.organization_id,
            "conversation_id": self.conversation_id,
            "lifecycle": self.lifecycle,
            "answer_status": self.answer_status,
            "narration_state": self.narration_state,
            "narration_text": self.narration_text,
            "intent": self.intent,
            "intent_source": self.intent_source,
            "provider": self.provider,
            "model": self.model,
            "model_version": self.model_version,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "message_id": self.message_id,
            "audit_record_id": self.audit_record_id,
            "tool_calls": [dict(t) for t in self.tool_calls],
            "references": [dict(r) for r in self.references],
            "replayed": self.replayed,
            "contract_version": INTERACTION_CONTRACT_VERSION,
        }


def narration_client() -> Optional["LLMClient"]:
    """The existing provider abstraction, configuration-gated (PO Q14).

    Reads exactly the environment variables the existing AI runtime already uses;
    no new configuration surface and no second provider architecture is added.
    Returns ``None`` when no provider is configured, so the deterministic answer
    is returned truthfully instead of failing.
    """
    from infra.llm_client import LLMClient

    base_url = (os.getenv("CARBONTALLY_AI_BASE_URL") or "").strip()
    api_key = (os.getenv("CARBONTALLY_AI_API_KEY") or "").strip()
    model = (os.getenv("CARBONTALLY_AI_MODEL") or "").strip()
    if not (base_url and api_key and model):
        return None
    return LLMClient(base_url=base_url, api_key=api_key, model=model)


def configured_provider_attribution() -> dict[str, Optional[str]]:
    """Truthful provider attribution via the existing runtime helper (PO Q14)."""
    from infra.ai_runtime import configured_ai_attribution

    return configured_ai_attribution()


def extract_identifiers(text: str) -> tuple[str, ...]:
    """Deterministically collect candidate identifiers from a question."""
    return tuple(dict.fromkeys(_UUID_RE.findall(text or "")))


def build_tool_input(tool_name: str, identifiers: Sequence[str]) -> Optional[dict[str, str]]:
    """Scope a ratified tool from identifiers present in the question.

    Returns ``None`` when the required identifier is absent — the caller then
    reports ``needs_clarification`` rather than guessing a scope.
    """
    if not identifiers or tool_name not in _TOOL_SCOPE_ARGUMENT:
        return None
    required = _TOOL_SCOPE_ARGUMENT[tool_name]
    if required is None:
        return {"version_id": identifiers[0]}
    return {required: identifiers[0]}


def _bounded_context(tool_result: dict[str, Any]) -> str:
    """Narration context built from the tool's declared output only (Q6/Q16.4)."""
    projected = {
        "tool": tool_result.get("tool"),
        "status": tool_result.get("status"),
        "reason": tool_result.get("reason"),
        "data": tool_result.get("data") or {},
        "references": tool_result.get("references") or [],
    }
    try:
        text = json.dumps(projected, sort_keys=True, default=str)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        text = str(projected)
    return text[:MAX_NARRATION_CONTEXT_CHARS]


def _i2():
    """Deferred import of the closed I2 boundary (no import-time api cycle)."""
    from api import insight_authz as module

    return module


async def _audit(
    *,
    repos: "RepositoryBundle",
    interaction_id: str,
    organization_id: str,
    actor: str,
    action: str,
    answer_status: str,
    tool_statuses: Sequence[str],
    tool_call_ids: Sequence[str],
    narration_state: str,
    reason: Optional[str],
) -> Optional[str]:
    """Append the canonical audit event (PO Q2/Q9) — ids and statuses only."""
    audit_logger = AuditLogger(sink=repos.audit, default_actor="system")
    entry = await audit_logger.log_action(
        action=action,
        entity_type="insight_interaction",
        entity_id=interaction_id,
        correlation_id=interaction_id,
        actor=actor,
        changed_fields={
            "interaction_id": interaction_id,
            "organization_id": organization_id,
            "tool_call_ids": list(tool_call_ids),
            "tool_statuses": list(tool_statuses),
            "answer_status": answer_status,
            "narration_state": narration_state,
            "layer": "i4-layer-2",
        },
        reason=reason,
    )
    return str(getattr(entry, "id", "") or None) or None


# --- PART 2 BEGINS BELOW (run_interaction and read helpers) ---

async def run_interaction(
    *,
    current_user: "AuthUser",
    repos: "RepositoryBundle",
    organization_id: str,
    conversation_id: str,
    question: str,
    idempotency_key: Optional[str] = None,
    narration: str = NARRATION_OPTIONAL,
    llm_client: Optional["LLMClient"] = None,
) -> InteractionOutcome:
    """Run one authorized I4 interaction end to end.

    Input/authorization failures raise ``HTTPException`` (fail closed, no
    fabricated success). Every other outcome is reported through the I4 answer
    state and persisted as append-only Layer-2 evidence.
    """
    text = (question or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="question must not be blank")
    if len(text) > MAX_QUESTION_CHARS:
        raise HTTPException(status_code=422, detail="question is too long")
    if narration not in NARRATION_MODES:
        raise HTTPException(status_code=422, detail="unsupported narration mode")
    if idempotency_key is not None and len(idempotency_key) > MAX_IDEMPOTENCY_KEY_LENGTH:
        raise HTTPException(status_code=422, detail="idempotency_key is too long")

    i2 = _i2()
    access = await i2.authorize_insight_scope(current_user, repos, organization_id)

    conversation = await repos.insight.get_conversation(
        conversation_id=conversation_id, organization_id=organization_id
    )
    if conversation is None or not i2.conversation_is_visible(access, conversation):
        raise HTTPException(status_code=404, detail="Conversation not found")

    if idempotency_key:
        existing = await repos.insight_interactions.find_by_idempotency_key(
            organization_id=organization_id, idempotency_key=idempotency_key
        )
        if existing is not None and existing.created_by == access.user_id:
            calls = await repos.insight_interactions.list_tool_calls(
                interaction_id=existing.id, organization_id=existing.organization_id
            )
            return InteractionOutcome(
                interaction_id=existing.id,
                organization_id=existing.organization_id,
                conversation_id=existing.conversation_id,
                lifecycle=existing.lifecycle,
                answer_status=existing.answer_status or "",
                narration_state=existing.narration_state,
                narration_text=None,
                intent=existing.intent,
                intent_source=existing.intent_source,
                provider=existing.provider,
                model=existing.model,
                model_version=existing.model_version,
                tokens_used=existing.tokens_used,
                cost=existing.cost,
                message_id=existing.message_id,
                audit_record_id=existing.audit_record_id,
                tool_calls=tuple(
                    {"tool_call_id": c.id, "tool": c.tool_name, "status": c.tool_status}
                    for c in calls
                ),
                replayed=True,
            )

    # PO Q4 — the raw question is persisted once, in the I1 message layer.
    message = await repos.insight.add_message(
        conversation_id=conversation.id,
        organization_id=conversation.organization_id,
        created_by=access.user_id,
        role="user",
        content=text,
    )

    decision = classify_intent(text)
    selected_tool = decision.get("tool")
    interaction = await repos.insight_interactions.create_interaction(
        organization_id=conversation.organization_id,
        conversation_id=conversation.id,
        created_by=access.user_id,
        question_hash=hash_text(text),
        request_hash=hash_text(f"{conversation.id}:{idempotency_key or ''}:{text}"),
        idempotency_key=idempotency_key,
        intent=selected_tool or decision.get("reason"),
        intent_source="deterministic" if selected_tool else "none",
        message_id=message.id,
    )
    await repos.insight_interactions.mark_executing(
        interaction_id=interaction.id, organization_id=interaction.organization_id
    )

    tool_calls: list[dict[str, Any]] = []
    references: list[dict[str, str]] = []
    tool_statuses: list[str] = []
    call_ids: list[str] = []
    deterministic_status: Optional[AnswerStatus] = None
    narration_state = NarrationState.SKIPPED
    narration_text: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    model_version: Optional[str] = None
    error_class: Optional[str] = None

    if selected_tool is None:
        deterministic_status = _INTENT_REFUSAL_ANSWER.get(
            str(decision.get("reason")), AnswerStatus.INVALID_INPUT
        )
    else:
        tool_input = build_tool_input(selected_tool, extract_identifiers(text))
        if tool_input is None:
            deterministic_status = AnswerStatus.NEEDS_CLARIFICATION
        else:
            started = time.perf_counter()
            result = await invoke_tool(
                tool_name=selected_tool,
                current_user=current_user,
                repos=repos,
                organization_id=organization_id,
                tool_input=tool_input,
            )
            duration_ms = int((time.perf_counter() - started) * 1000)
            payload = result.as_dict()
            if str(result.status) not in ALLOWED_TOOL_STATUSES:  # pragma: no cover
                raise RuntimeError("unratified tool status returned by I3")
            projected_args = project_tool_arguments(selected_tool, tool_input)
            metadata = project_result_metadata(
                payload, contract_version=result.contract_version
            )
            refs = [dict(r.as_dict()) for r in result.references]
            record = await repos.insight_interactions.record_tool_call(
                interaction_id=interaction.id,
                organization_id=interaction.organization_id,
                call_ordinal=1,
                tool_name=selected_tool,
                contract_version=result.contract_version,
                tool_status=str(result.status),
                arguments=projected_args,
                result_metadata=metadata,
                references=refs,
                arguments_hash=hash_text(json.dumps(projected_args, sort_keys=True)),
                result_hash=hash_text(json.dumps(metadata, sort_keys=True, default=str)),
                result_item_count=int(metadata.get("item_count") or 0),
                truncated=bool(result.truncated),
                duration_ms=duration_ms,
            )
            call_ids.append(record.id)
            tool_statuses.append(str(result.status))
            references.extend(refs)
            tool_calls.append(
                {
                    "tool_call_id": record.id,
                    "tool": selected_tool,
                    "status": str(result.status),
                    "reason": result.reason,
                    "duration_ms": duration_ms,
                }
            )
            deterministic_status = tool_answer_status(str(result.status))

            # PO Q11/Q14 — bounded narration over the declared tool output only.
            if narration != NARRATION_NONE and str(result.status) == "success":
                if llm_client is None:
                    narration_state = (
                        NarrationState.SKIPPED
                        if narration == NARRATION_OPTIONAL
                        else NarrationState.UNAVAILABLE
                    )
                else:
                    prompt = (
                        "Structured CarbonTally evidence (authorised, read-only):\n"
                        f"{_bounded_context(payload)}\n\n"
                        f"Question: {text[:500]}\n"
                        "Explain what this evidence establishes."
                    )
                    attempts = 0
                    while attempts < MAX_PROVIDER_ATTEMPTS and narration_text is None:
                        attempts += 1
                        try:
                            candidate = await llm_client.complete(
                                prompt=prompt, system=_SYSTEM_PROMPT, temperature=0.0
                            )
                        except Exception as exc:  # noqa: BLE001 - failure is a state
                            error_class = type(exc).__name__
                            logger.warning(
                                "insight narration attempt %s failed (%s)",
                                attempts,
                                error_class,
                            )
                            continue
                        if candidate and candidate.strip():
                            narration_text = candidate.strip()
                    narration_state = (
                        NarrationState.COMPLETED
                        if narration_text
                        else NarrationState.UNAVAILABLE
                    )
                    if narration_text:
                        attribution = configured_provider_attribution()
                        provider = attribution.get("provider")
                        model = attribution.get("model")
                        model_version = attribution.get("model_version")

    statuses = [tool_answer_status(s) for s in tool_statuses]
    answer_status = (
        deterministic_status
        if deterministic_status is not None
        else combine_answer_statuses(statuses)
    )
    if (
        narration == NARRATION_REQUIRED
        and narration_state is NarrationState.UNAVAILABLE
        and answer_status is AnswerStatus.SUCCESS
    ):
        answer_status = AnswerStatus.PROVIDER_UNAVAILABLE
    lifecycle = (
        InteractionLifecycle.COMPLETED
        if answer_status is not AnswerStatus.ERROR
        else InteractionLifecycle.FAILED
    )

    # Narration text is a message, not Layer-2 evidence (PO Q4).
    if narration_text:
        await repos.insight.add_message(
            conversation_id=conversation.id,
            organization_id=conversation.organization_id,
            created_by=access.user_id,
            role="insight",
            content=narration_text,
        )

    try:
        audit_record_id = await _audit(
            repos=repos,
            interaction_id=interaction.id,
            organization_id=interaction.organization_id,
            actor=access.user_id,
            action=f"insight.interaction.{lifecycle.value}",
            answer_status=answer_status.value,
            tool_statuses=tool_statuses,
            tool_call_ids=call_ids,
            narration_state=narration_state.value,
            reason=error_class,
        )
    except Exception as exc:  # noqa: BLE001 - canonical audit is required (Q2/Q9)
        logger.exception("insight canonical audit append failed")
        audit_record_id = None
        error_class = f"audit_append_failed:{type(exc).__name__}"
        answer_status = AnswerStatus.ERROR
        lifecycle = InteractionLifecycle.FAILED

    await repos.insight_interactions.complete_interaction(
        interaction_id=interaction.id,
        organization_id=interaction.organization_id,
        lifecycle=lifecycle.value,
        answer_status=answer_status.value,
        narration_state=narration_state.value,
        provider=provider,
        model=model,
        model_version=model_version,
        tokens_used=None,
        cost=None,
        tool_call_count=len(call_ids),
        reference_count=len(references),
        error_class=error_class,
        audit_record_id=audit_record_id,
        metadata={"contract_version": INTERACTION_CONTRACT_VERSION},
    )

    return InteractionOutcome(
        interaction_id=interaction.id,
        organization_id=interaction.organization_id,
        conversation_id=interaction.conversation_id,
        lifecycle=lifecycle.value,
        answer_status=answer_status.value,
        narration_state=narration_state.value,
        narration_text=narration_text,
        intent=interaction.intent,
        intent_source=interaction.intent_source,
        provider=provider,
        model=model,
        model_version=model_version,
        tokens_used=None,
        cost=None,
        message_id=message.id,
        audit_record_id=audit_record_id,
        tool_calls=tuple(tool_calls),
        references=tuple(references),
    )

async def get_interaction_outcome(
    *,
    current_user: "AuthUser",
    repos: "RepositoryBundle",
    organization_id: str,
    interaction_id: str,
) -> dict[str, Any]:
    """Creator-private read of one interaction (re-authorized on every read)."""
    i2 = _i2()
    access = await i2.authorize_insight_scope(current_user, repos, organization_id)
    interaction = await repos.insight_interactions.get_interaction(
        interaction_id=interaction_id,
        organization_id=organization_id,
        created_by=access.user_id,
    )
    if interaction is None:
        raise HTTPException(status_code=404, detail="Interaction not found")
    calls = await repos.insight_interactions.list_tool_calls(
        interaction_id=interaction.id, organization_id=interaction.organization_id
    )
    return {
        "interaction_id": interaction.id,
        "organization_id": interaction.organization_id,
        "conversation_id": interaction.conversation_id,
        "lifecycle": interaction.lifecycle,
        "answer_status": interaction.answer_status,
        "narration_state": interaction.narration_state,
        "intent": interaction.intent,
        "intent_source": interaction.intent_source,
        "provider": interaction.provider,
        "model": interaction.model,
        "model_version": interaction.model_version,
        "tokens_used": interaction.tokens_used,
        "cost": interaction.cost,
        "message_id": interaction.message_id,
        "audit_record_id": interaction.audit_record_id,
        "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
        "completed_at": (
            interaction.completed_at.isoformat() if interaction.completed_at else None
        ),
        "tool_calls": [
            {
                "tool_call_id": c.id,
                "tool": c.tool_name,
                "status": c.tool_status,
                "arguments": c.arguments,
                "result_metadata": c.result_metadata,
                "references": list(c.references),
                "duration_ms": c.duration_ms,
            }
            for c in calls
        ],
        "contract_version": INTERACTION_CONTRACT_VERSION,
    }


async def list_interaction_outcomes(
    *,
    current_user: "AuthUser",
    repos: "RepositoryBundle",
    organization_id: str,
    conversation_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """Creator-private listing of interactions (no cross-creator disclosure)."""
    i2 = _i2()
    access = await i2.authorize_insight_scope(current_user, repos, organization_id)
    rows = await repos.insight_interactions.list_interactions(
        organization_id=organization_id,
        created_by=access.user_id,
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )
    total = await repos.insight_interactions.count_interactions(
        organization_id=organization_id,
        created_by=access.user_id,
        conversation_id=conversation_id,
    )
    return {
        "interactions": [
            {
                "interaction_id": r.id,
                "conversation_id": r.conversation_id,
                "lifecycle": r.lifecycle,
                "answer_status": r.answer_status,
                "narration_state": r.narration_state,
                "intent": r.intent,
                "tool_call_count": r.tool_call_count,
                "reference_count": r.reference_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


__all__ = [
    "InteractionOutcome",
    "NARRATION_MODES",
    "NARRATION_NONE",
    "NARRATION_OPTIONAL",
    "NARRATION_REQUIRED",
    "build_tool_input",
    "extract_identifiers",
    "get_interaction_outcome",
    "list_interaction_outcomes",
    "narration_client",
    "run_interaction",
]
