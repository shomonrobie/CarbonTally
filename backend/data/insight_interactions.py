"""CarbonTally Insight I4 — Layer-2 interaction persistence (append-only evidence).

Authorization: PO I4 Implementation Authorization (2026-09-21); PO Q5 (append-only),
Q6 (allowlisted projections only), Q7 (Layer-2 lifecycle), Q9 (interaction/tool-call
correlation), Q10 (idempotency), Q4 (no raw question text — only its hash).

Design notes:

* Bound to the **service-role** pool like every other repository, so every read is
  explicitly scoped by ``organization_id`` **and** (for creator-private reads) by
  ``created_by``, in defence in depth with the RLS policies.
* This repository has **no delete and no arbitrary update surface**: the only
  mutation is a forward-only lifecycle completion, which the migration's trigger
  also enforces in the database (a completion of an already-terminal row, or a
  change to an immutable column, is refused by PostgreSQL, not merely by Python).
* ``record_tool_call`` is idempotent on ``(interaction_id, tool_name,
  arguments_hash)`` — a retry returns the existing evidence row instead of
  duplicating it (PO Q10).
"""
from __future__ import annotations

from typing import Any, Optional, Sequence

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.insight_interaction import InsightInteraction, InsightToolCall

_INTERACTION_COLUMNS = (
    "id, organization_id, conversation_id, created_by, lifecycle, answer_status, "
    "message_id, audit_record_id, idempotency_key, question_hash, request_hash, "
    "intent, intent_source, provider, model, model_version, narration_state, "
    "tokens_used, cost, tool_call_count, reference_count, error_class, metadata, "
    "created_at, completed_at"
)

_TOOL_CALL_COLUMNS = (
    "id, interaction_id, organization_id, call_ordinal, tool_name, contract_version, "
    'tool_status, arguments, result_metadata, "references", arguments_hash, '
    "result_hash, result_item_count, truncated, duration_ms, created_at"
)

_CREATE_INTERACTION_SQL = f"""
    INSERT INTO public.carbontally_insight_interactions
        (organization_id, conversation_id, created_by, lifecycle, question_hash,
         request_hash, idempotency_key, intent, intent_source, message_id)
    VALUES ($1, $2, $3, 'received', $4, $5, $6, $7, $8, $9)
    RETURNING {_INTERACTION_COLUMNS}
"""

_FIND_IDEMPOTENT_SQL = f"""
    SELECT {_INTERACTION_COLUMNS}
      FROM public.carbontally_insight_interactions
     WHERE organization_id = $1 AND idempotency_key = $2
"""

_GET_INTERACTION_SQL = f"""
    SELECT {_INTERACTION_COLUMNS}
      FROM public.carbontally_insight_interactions
     WHERE id = $1 AND organization_id = $2
       AND ($3::uuid IS NULL OR created_by = $3::uuid)
"""

_LIST_INTERACTIONS_SQL = f"""
    SELECT {_INTERACTION_COLUMNS}
      FROM public.carbontally_insight_interactions
     WHERE organization_id = $1
       AND ($2::uuid IS NULL OR created_by = $2::uuid)
       AND ($3::uuid IS NULL OR conversation_id = $3::uuid)
     ORDER BY created_at DESC, id DESC
     LIMIT $4 OFFSET $5
"""

_COUNT_INTERACTIONS_SQL = """
    SELECT count(*) AS n
      FROM public.carbontally_insight_interactions
     WHERE organization_id = $1
       AND ($2::uuid IS NULL OR created_by = $2::uuid)
       AND ($3::uuid IS NULL OR conversation_id = $3::uuid)
"""

_MARK_EXECUTING_SQL = f"""
    UPDATE public.carbontally_insight_interactions
       SET lifecycle = 'executing'
     WHERE id = $1 AND organization_id = $2 AND lifecycle = 'received'
    RETURNING {_INTERACTION_COLUMNS}
"""

_COMPLETE_SQL = f"""
    UPDATE public.carbontally_insight_interactions
       SET lifecycle = $3, answer_status = $4, provider = $5, model = $6,
           model_version = $7, narration_state = $8, tokens_used = $9, cost = $10,
           tool_call_count = $11, reference_count = $12, error_class = $13,
           audit_record_id = $14, metadata = $15::jsonb, completed_at = now()
     WHERE id = $1 AND organization_id = $2
       AND lifecycle IN ('received', 'executing')
    RETURNING {_INTERACTION_COLUMNS}
"""

_RECORD_TOOL_CALL_SQL = f"""
    INSERT INTO public.carbontally_insight_tool_calls
        (interaction_id, organization_id, call_ordinal, tool_name, contract_version,
         tool_status, arguments, result_metadata, "references", arguments_hash,
         result_hash, result_item_count, truncated, duration_ms)
    VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9::jsonb, $10, $11, $12, $13, $14)
    ON CONFLICT (interaction_id, tool_name, arguments_hash) DO NOTHING
    RETURNING {_TOOL_CALL_COLUMNS}
"""

_GET_TOOL_CALL_BY_LOGICAL_SQL = f"""
    SELECT {_TOOL_CALL_COLUMNS}
      FROM public.carbontally_insight_tool_calls
     WHERE interaction_id = $1 AND tool_name = $2 AND arguments_hash = $3
"""

_LIST_TOOL_CALLS_SQL = f"""
    SELECT {_TOOL_CALL_COLUMNS}
      FROM public.carbontally_insight_tool_calls
     WHERE interaction_id = $1 AND organization_id = $2
     ORDER BY call_ordinal ASC
"""


def _row_to_interaction(row: Any) -> InsightInteraction:
    r = dict(row)
    return InsightInteraction(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        conversation_id=str(r["conversation_id"]),
        created_by=str(r["created_by"]),
        lifecycle=r["lifecycle"],
        answer_status=r.get("answer_status"),
        message_id=str(r["message_id"]) if r.get("message_id") else None,
        audit_record_id=str(r["audit_record_id"]) if r.get("audit_record_id") else None,
        idempotency_key=r.get("idempotency_key"),
        question_hash=r["question_hash"],
        request_hash=r.get("request_hash"),
        intent=r.get("intent"),
        intent_source=r.get("intent_source"),
        provider=r.get("provider"),
        model=r.get("model"),
        model_version=r.get("model_version"),
        narration_state=r.get("narration_state") or "not_attempted",
        tokens_used=r.get("tokens_used"),
        cost=float(r["cost"]) if r.get("cost") is not None else None,
        tool_call_count=int(r.get("tool_call_count") or 0),
        reference_count=int(r.get("reference_count") or 0),
        error_class=r.get("error_class"),
        metadata=loads_jsonb(r.get("metadata")) or {},
        created_at=r.get("created_at"),
        completed_at=r.get("completed_at"),
    )


def _row_to_tool_call(row: Any) -> InsightToolCall:
    r = dict(row)
    # asyncpg returns jsonb as text in this configuration: decode through the
    # project helper (data.base.loads_jsonb) instead of coercing the string
    # with dict(), which raised ValueError (OHD D-3).
    refs = loads_jsonb(r.get("references")) or []
    return InsightToolCall(
        id=str(r["id"]),
        interaction_id=str(r["interaction_id"]),
        organization_id=str(r["organization_id"]),
        call_ordinal=int(r["call_ordinal"]),
        tool_name=r["tool_name"],
        contract_version=r["contract_version"],
        tool_status=r["tool_status"],
        arguments=loads_jsonb(r.get("arguments")) or {},
        result_metadata=loads_jsonb(r.get("result_metadata")) or {},
        references=tuple(dict(x) for x in refs if isinstance(x, dict)),
        arguments_hash=r["arguments_hash"],
        result_hash=r["result_hash"],
        result_item_count=int(r.get("result_item_count") or 0),
        truncated=bool(r.get("truncated")),
        duration_ms=r.get("duration_ms"),
        created_at=r.get("created_at"),
    )


class InsightInteractionRepository(AbstractRepository[InsightInteraction]):
    """Layer-2 interaction + tool-call evidence (append-only)."""

    async def get(self, entity_id: str):  # pragma: no cover - boundary
        """No organisation-less read surface exists for I4 evidence."""
        raise NotImplementedError(
            "CarbonTally Insight I4 exposes only organisation-scoped reads "
            "(get_interaction / list_tool_calls); a generic get is absent so a "
            "stored id can never bypass the I2 boundary."
        )

    async def save(self, entity):  # pragma: no cover - boundary
        """No generic upsert: Layer-2 evidence is append-only (PO Q5)."""
        raise NotImplementedError(
            "CarbonTally Insight I4 evidence is append-only; use "
            "create_interaction / complete_interaction / record_tool_call."
        )

    async def delete(self, entity_id: str) -> None:  # pragma: no cover - guard
        """I4 has no delete surface: retention/deletion is deferred to I7 (PO Q12)."""
        raise NotImplementedError(
            "CarbonTally Insight I4 has no delete surface; retention and deletion "
            "semantics are deferred to I7 (PO Q12)."
        )

    # -- interaction surface ---------------------------------------------
    async def create_interaction(
        self,
        *,
        organization_id: str,
        conversation_id: str,
        created_by: str,
        question_hash: str,
        request_hash: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        intent: Optional[str] = None,
        intent_source: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> InsightInteraction:
        row = await self._fetch_one(
            _CREATE_INTERACTION_SQL,
            organization_id,
            conversation_id,
            created_by,
            question_hash,
            request_hash,
            idempotency_key,
            intent,
            intent_source,
            message_id,
        )
        return _row_to_interaction(row)  # type: ignore[arg-type]

    async def find_by_idempotency_key(
        self, *, organization_id: str, idempotency_key: str
    ) -> Optional[InsightInteraction]:
        """Q10 — locate the interaction a retried request already produced."""
        row = await self._fetch_one(_FIND_IDEMPOTENT_SQL, organization_id, idempotency_key)
        return _row_to_interaction(row) if row else None

    async def get_interaction(
        self,
        *,
        interaction_id: str,
        organization_id: str,
        created_by: Optional[str] = None,
    ) -> Optional[InsightInteraction]:
        """Organisation-scoped read; ``created_by`` applies creator-private (Q8)."""
        row = await self._fetch_one(
            _GET_INTERACTION_SQL, interaction_id, organization_id, created_by
        )
        return _row_to_interaction(row) if row else None

    async def list_interactions(
        self,
        *,
        organization_id: str,
        created_by: Optional[str] = None,
        conversation_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[InsightInteraction]:
        rows = await self._fetch_all(
            _LIST_INTERACTIONS_SQL,
            organization_id,
            created_by,
            conversation_id,
            limit,
            offset,
        )
        return [_row_to_interaction(r) for r in rows]

    async def count_interactions(
        self,
        *,
        organization_id: str,
        created_by: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> int:
        row = await self._fetch_one(
            _COUNT_INTERACTIONS_SQL, organization_id, created_by, conversation_id
        )
        return int(row["n"]) if row else 0

    async def mark_executing(
        self, *, interaction_id: str, organization_id: str
    ) -> Optional[InsightInteraction]:
        """Forward-only ``received -> executing`` (Q5)."""
        row = await self._fetch_one(_MARK_EXECUTING_SQL, interaction_id, organization_id)
        return _row_to_interaction(row) if row else None

    async def complete_interaction(
        self,
        *,
        interaction_id: str,
        organization_id: str,
        lifecycle: str,
        answer_status: str,
        narration_state: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        model_version: Optional[str] = None,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None,
        tool_call_count: int = 0,
        reference_count: int = 0,
        error_class: Optional[str] = None,
        audit_record_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[InsightInteraction]:
        """Single forward-only completion update; the trigger refuses anything else."""
        row = await self._fetch_one(
            _COMPLETE_SQL,
            interaction_id,
            organization_id,
            lifecycle,
            answer_status,
            provider,
            model,
            model_version,
            narration_state,
            tokens_used,
            cost,
            tool_call_count,
            reference_count,
            error_class,
            audit_record_id,
            dumps_jsonb(metadata or {}),
        )
        return _row_to_interaction(row) if row else None

    # -- tool-call evidence surface --------------------------------------
    async def record_tool_call(
        self,
        *,
        interaction_id: str,
        organization_id: str,
        call_ordinal: int,
        tool_name: str,
        contract_version: str,
        tool_status: str,
        arguments: Optional[dict[str, Any]] = None,
        result_metadata: Optional[dict[str, Any]] = None,
        references: Optional[Sequence[dict[str, str]]] = None,
        arguments_hash: str = "",
        result_hash: str = "",
        result_item_count: int = 0,
        truncated: bool = False,
        duration_ms: Optional[int] = None,
    ) -> InsightToolCall:
        """Append one tool-call evidence row, idempotently (PO Q6/Q10)."""
        row = await self._fetch_one(
            _RECORD_TOOL_CALL_SQL,
            interaction_id,
            organization_id,
            call_ordinal,
            tool_name,
            contract_version,
            tool_status,
            dumps_jsonb(arguments or {}),
            dumps_jsonb(result_metadata or {}),
            dumps_jsonb(list(references or [])),
            arguments_hash,
            result_hash,
            result_item_count,
            truncated,
            duration_ms,
        )
        if row is None:
            existing = await self._fetch_one(
                _GET_TOOL_CALL_BY_LOGICAL_SQL, interaction_id, tool_name, arguments_hash
            )
            if existing is None:  # pragma: no cover - defensive
                raise RuntimeError("tool-call insert returned no row")
            return _row_to_tool_call(existing)
        return _row_to_tool_call(row)

    async def list_tool_calls(
        self, *, interaction_id: str, organization_id: str
    ) -> Sequence[InsightToolCall]:
        rows = await self._fetch_all(_LIST_TOOL_CALLS_SQL, interaction_id, organization_id)
        return [_row_to_tool_call(r) for r in rows]


__all__ = ["InsightInteractionRepository"]
