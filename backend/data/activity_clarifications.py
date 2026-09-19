"""F-039-1 — activity-clarification repository (F-048-2 / 051).

The **only** writer and reader for ``public.activity_clarifications``: the
persistence half of authorised activity clarification.

Design (reuse, no invention):

* the row is a persisted **adjudication**, kept separate from the extracted
  source evidence — ``original_activity`` is the extracted value and is never
  rewritten, while ``clarification`` carries the user's semantic statement;
* **factor metadata is never accepted from a caller.** This repository takes a
  :class:`engines.activity_clarification.ClarificationRecord` — a value object
  the engine produces *after* re-running the existing factor-selection policy —
  and copies the factor fields from that object only. No method here accepts a
  ``selected_factor_id``, ``factor_set``, ``factor_source``, ``reporting_year``,
  ``unit`` or ``scope`` argument, so a caller (and therefore an API client)
  cannot nominate a factor: there is no parameter through which to do it;
* **tenant scope is resolved server-side** from the parent extraction item
  (``manual_extraction_items.batch_id → manual_extraction_batches.organization_id``;
  the item itself has no ``organization_id``), exactly as
  ``data/evidence_line_items.py`` does — the caller cannot supply it;
* **idempotent by construction**: the insert is ``ON CONFLICT DO NOTHING`` on the
  database's ``UNIQUE(activity_key, original_activity, clarification)``; a repeat
  therefore returns the row already stored rather than creating a second one or
  overwriting the first;
* no factor-selection logic exists here — the policy lives in
  ``engines/factor_selection_policy.py`` and is invoked by the engine.

RLS remains the second layer: the service-role pool bypasses it, so every read
is additionally constrained by an explicit ``organization_id`` predicate.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Any, Optional, Sequence

import asyncpg

from core.logging import get_logger
from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from engines.activity_clarification import ClarificationRecord

logger = get_logger(__name__)

#: Explicit column list — never ``SELECT *`` (repository convention).
_COLUMNS = (
    "id, activity_key, organization_id, batch_key, item_key, original_activity, "
    "source_evidence_ref, clarification, clarification_type, policy_input, "
    "outcome_status, selected_factor_id, selected_factor_name, factor_set, "
    "factor_source, reporting_year, unit, scope, eligible_group_count, "
    "eligible_groups, actor_id, actor_scope, created_at, updated_at, "
    "adjudication_id, version, supersedes_id, is_current, effective_context_key, "
    "evidence_signature, evidence_context, re_evaluation_required"
)

#: Server-side tenant resolution: the item carries no organization_id, so the
#: tenant comes from its parent batch (F-B2-8 convention, reused not duplicated).
_CONTEXT_SQL = """
    SELECT i.id              AS item_key,
           i.batch_id        AS batch_key,
           i.file_id         AS source_file_id,
           i.file_name       AS source_file_name,
           b.organization_id AS organization_id,
           i.extracted_data  AS extracted_data
      FROM public.manual_extraction_items i
      LEFT JOIN public.manual_extraction_batches b ON b.id = i.batch_id
     WHERE i.id = $1
"""

#: The persisted evidence keys a clarification request may never set (D-039-1-F/-I).
_EVIDENCE_TEXT_KEYS = ("activity", "source_line", "raw_description", "description")
_EVIDENCE_UNIT_KEYS = ("unit", "raw_unit")
_EVIDENCE_SCOPE_KEYS = ("scope",)

_INSERT_SQL = f"""
    INSERT INTO public.activity_clarifications (
        activity_key, batch_key, item_key, organization_id, original_activity,
        source_evidence_ref, clarification, clarification_type, policy_input,
        outcome_status, selected_factor_id, selected_factor_name, factor_set,
        factor_source, reporting_year, unit, scope, eligible_group_count,
        eligible_groups, actor_id, actor_scope, adjudication_id, version,
        supersedes_id, is_current, effective_context_key, evidence_signature,
        evidence_context
    ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
        $16, $17, $18, $19::jsonb, $20, $21, $22, $23, $24, $25, $26, $27,
        $28::jsonb
    )
    ON CONFLICT ON CONSTRAINT activity_clarifications_replay_unique DO NOTHING
    RETURNING {_COLUMNS}
"""

#: The effective (current) adjudication for one bounded context (Finding 1).
_EFFECTIVE_SQL = f"""
    SELECT {_COLUMNS} FROM public.activity_clarifications
     WHERE organization_id = $1
       AND effective_context_key = $2
       AND activity_key = $3
       AND original_activity = $4
       AND is_current
"""

#: Full immutable version history, deterministic (oldest → newest).
_HISTORY_SQL = f"""
    SELECT {_COLUMNS} FROM public.activity_clarifications
     WHERE organization_id = $1 AND adjudication_id = $2
     ORDER BY version ASC
"""

#: Retire a superseded version. Only ``is_current`` changes; every other column —
#: including factor metadata — is left exactly as it was (D-039-1-D/-H).
_SUPERSEDE_SQL = """
    UPDATE public.activity_clarifications
       SET is_current = false, updated_at = now()
     WHERE organization_id = $1 AND id = $2
"""

_SELECT_BY_KEY_SQL = f"""
    SELECT {_COLUMNS} FROM public.activity_clarifications
     WHERE organization_id = $1
       AND activity_key = $2
       AND original_activity = $3
       AND clarification = $4
       AND version = $5
"""

_SELECT_BY_ID_SQL = f"""
    SELECT {_COLUMNS} FROM public.activity_clarifications
     WHERE organization_id = $1 AND id = $2
"""

_LIST_SQL = f"""
    SELECT {_COLUMNS} FROM public.activity_clarifications
     WHERE organization_id = $1
       AND ($2::text IS NULL OR activity_key = $2)
     ORDER BY created_at DESC
     LIMIT $3
"""

_DELETE_SQL = """
    DELETE FROM public.activity_clarifications
     WHERE organization_id = $1 AND id = $2
"""


def _as_uuid(value: Optional[str]) -> Optional[str]:
    """Return a UUID string, or ``None`` — never invent an identity."""
    if value in (None, ""):
        return None
    return str(value)


def _line_evidence(
    extracted_data: Any, activity: Optional[str]
) -> tuple:
    """Authoritative ``(unit, scope)`` from the persisted extraction line.

    Reads only the persisted ``extracted_data`` line items and accepts a line only on
    an EXACT (case-insensitive) match of the extracted activity text. Zero or several
    matches yield ``(None, None)``: no line is invented and no client value is
    substituted, so the policy decides (D-039-1-I safe path).
    """
    payload = loads_jsonb(extracted_data)
    if payload is None:
        return None, None
    if isinstance(payload, dict):
        lines = payload.get("line_items") or payload.get("lines") or []
    elif isinstance(payload, list):
        lines = payload
    else:
        return None, None
    wanted = (activity or "").strip().casefold()
    if not wanted:
        return None, None
    matches = []
    for line in lines:
        if not isinstance(line, dict):
            continue
        for key in _EVIDENCE_TEXT_KEYS:
            value = line.get(key)
            if isinstance(value, str) and value.strip().casefold() == wanted:
                matches.append(line)
                break
    if len(matches) != 1:
        return None, None
    line = matches[0]

    def _first(keys):
        for key in keys:
            value = line.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    return _first(_EVIDENCE_UNIT_KEYS), _first(_EVIDENCE_SCOPE_KEYS)


class ActivityClarificationsRepository(AbstractRepository[dict]):
    """Persists and reads the adjudication rows for one organisation.

    Every read and write is additionally constrained by ``organization_id``
    (``get``/``delete`` therefore require it). The service-role pool bypasses
    RLS, so this predicate — not the pool — is what keeps tenants apart on the
    server path; RLS stays in force for authenticated direct access.
    """

    # -- server-side context -------------------------------------------------
    async def resolve_context(self, item_id: str) -> Optional[dict]:
        """Resolve the authoritative context for an extraction item, server-side.

        Returns ``None`` when the item does not exist, so callers reject an unknown
        item instead of persisting an orphan adjudication. Provenance
        (``source_evidence_ref``), the authoritative unit/scope and the evidence
        signature are all derived from the PERSISTED item (D-039-1-F/-I) — never from
        a request body.
        """
        return await self.resolve_evidence(item_id)

    async def resolve_evidence(
        self, item_id: str, activity: Optional[str] = None
    ) -> Optional[dict]:
        """Server-derived provenance + authoritative evidence for one item.

        The tenant comes from ``item → batch → organization``; the evidence reference
        from the persisted file identity; ``unit``/``scope`` only from the persisted
        ``extracted_data`` line that matches the extracted activity exactly. When no
        single line matches, ``unit``/``scope`` stay ``None`` — the safe path: nothing
        is invented and no client value is substituted.
        """
        row = await self._fetch_one(_CONTEXT_SQL, _as_uuid(item_id))
        if row is None:
            return None
        data = dict(row)
        unit, scope = _line_evidence(data.get("extracted_data"), activity)
        return {
            "item_key": _as_uuid(data.get("item_key")),
            "batch_key": _as_uuid(data.get("batch_key")),
            "organization_id": _as_uuid(data.get("organization_id")),
            "source_evidence_ref": _as_uuid(data.get("source_file_id"))
            or data.get("source_file_name"),
            "unit": unit,
            "scope": scope,
            "evidence_context": {
                "original_activity": activity,
                "unit": unit,
                "scope": scope,
                "item_key": _as_uuid(data.get("item_key")),
                "batch_key": _as_uuid(data.get("batch_key")),
            },
        }

    @staticmethod
    def evidence_signature(
        original_activity: Optional[str],
        unit: Optional[str],
        scope: Optional[str],
    ) -> str:
        """The D-F039-1-I compatibility signature.

        Covers exactly the three mandated fields — the original extracted activity
        text, the authoritative persisted unit and the authoritative persisted scope —
        and nothing else (no filename, OCR text, quantity, date or other metadata).
        Generated server-side from persisted evidence only.
        """
        parts = [
            (original_activity or "").strip().casefold(),
            (unit or "").strip().casefold(),
            (scope or "").strip().casefold(),
        ]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    async def effective_compatible(
        self,
        *,
        organization_id: str,
        activity_key: str,
        original_activity: str,
        unit: Optional[str],
        scope: Optional[str],
        context_key: Optional[str] = None,
    ) -> tuple:
        """Return ``(row, compatible)`` for the bounded context.

        ``compatible`` is true only when the stored signature equals the signature of
        the CURRENT persisted evidence. A row with no stored signature is treated as
        NOT compatible — without evidence to compare there is no proof of
        compatibility, so the adjudication must not be silently reused
        (D-039-1-G/-I).
        """
        row = await self.effective(
            organization_id=organization_id,
            activity_key=activity_key,
            original_activity=original_activity,
            context_key=context_key,
        )
        if row is None:
            return None, False
        stored = row.get("evidence_signature")
        current = self.evidence_signature(original_activity, unit, scope)
        return row, bool(stored) and stored == current

    # -- writes --------------------------------------------------------------
    async def record(
        self,
        record: ClarificationRecord,
        *,
        organization_id: str,
        item_id: Optional[str] = None,
        batch_key: Optional[str] = None,
        source_evidence_ref: Optional[str] = None,
        eligible_groups: Sequence[Any] = (),
        adjudication_id: Optional[str] = None,
        version: int = 1,
        supersedes_id: Optional[str] = None,
        is_current: bool = True,
        effective_context_key: Optional[str] = None,
        evidence_signature: Optional[str] = None,
        evidence_context: Optional[dict] = None,
    ) -> Optional[dict]:
        """Persist one engine-produced adjudication. Idempotent by construction.

        ``record`` is authoritative: factor fields are copied from it alone, so a
        caller cannot nominate a factor. ``organization_id`` must be the value
        resolved server-side by :meth:`resolve_context`.

        Returns the stored row — the existing one when the database's
        ``UNIQUE(activity_key, original_activity, clarification)`` already holds
        this exact adjudication, in which case nothing is overwritten.
        """
        if not organization_id:
            raise ValueError("organization_id is required (resolve it server-side)")
        row = await self._fetch_one(
            _INSERT_SQL,
            record.activity_key,
            _as_uuid(batch_key),
            _as_uuid(item_id),
            _as_uuid(organization_id),
            record.original_activity,
            source_evidence_ref,
            record.clarification,
            record.clarification_type,
            record.policy_input,
            record.outcome_status,
            _as_uuid(record.selected_factor_id),
            record.selected_factor_name,
            record.factor_set,
            record.factor_source,
            record.reporting_year,
            record.unit,
            record.scope,
            int(record.eligible_group_count or 0),
            dumps_jsonb(list(eligible_groups)),
            _as_uuid(record.actor_id),
            record.actor_scope,
            _as_uuid(adjudication_id) or str(uuid.uuid4()),
            int(version),
            _as_uuid(supersedes_id),
            bool(is_current),
            effective_context_key or record.activity_key,
            evidence_signature,
            dumps_jsonb(evidence_context or {}),
        )
        if row is not None:
            return dict(row)
        existing = await self._fetch_one(
            _SELECT_BY_KEY_SQL,
            _as_uuid(organization_id),
            record.activity_key,
            record.original_activity,
            record.clarification,
            int(version),
        )
        logger.info(
            "activity clarification already adjudicated (idempotent replay): %s/%s",
            record.activity_key,
            record.outcome_status,
        )
        return dict(existing) if existing is not None else None

    async def apply_clarification(
        self,
        activity: str,
        clarification: str,
        candidates: Sequence[Any],
        *,
        organization_id: str,
        actor_id: str,
        actor_scope: Optional[str] = None,
        activity_key: str = "",
        item_id: Optional[str] = None,
        batch_key: Optional[str] = None,
        source_evidence_ref: Optional[str] = None,
        unit: Optional[str] = None,
        scope: Optional[str] = None,
        preferred_unit: Optional[str] = None,
    ) -> dict:
        """Re-enter the existing policy with the semantic clarification, then store it.

        ``actor_id``/``organization_id`` come from trusted server context. The
        user supplies *meaning* only; the factor (if any) is whatever
        ``select_factor`` returns afterwards. ``unit``/``scope``/
        ``preferred_unit`` are *policy inputs* and must be values already
        persisted for the extracted line — never request-body values, which
        could otherwise steer the selection.
        """
        from engines.activity_clarification import resolve_clarification

        record, factor = resolve_clarification(
            activity,
            clarification,
            candidates,
            unit=unit,
            scope=scope,
            preferred_unit=preferred_unit,
            activity_key=activity_key,
            actor_id=actor_id,
            actor_scope=actor_scope,
        )
        stored = await self.record(
            record,
            organization_id=organization_id,
            item_id=item_id,
            batch_key=batch_key,
            source_evidence_ref=source_evidence_ref,
            eligible_groups=record.notes,
        )
        return {"record": stored, "resolved": factor is not None}

    async def apply_decline(
        self,
        activity: str,
        *,
        organization_id: str,
        actor_id: str,
        actor_scope: Optional[str] = None,
        activity_key: str = "",
        item_id: Optional[str] = None,
        batch_key: Optional[str] = None,
        source_evidence_ref: Optional[str] = None,
    ) -> dict:
        """Persist the safe unresolved path: no factor, nothing to calculate."""
        from engines.activity_clarification import decline_clarification

        record = decline_clarification(
            activity,
            activity_key=activity_key,
            actor_id=actor_id,
            actor_scope=actor_scope,
        )
        stored = await self.record(
            record,
            organization_id=organization_id,
            item_id=item_id,
            batch_key=batch_key,
            source_evidence_ref=source_evidence_ref,
        )
        return {"record": stored, "resolved": False}

    # -- reads ---------------------------------------------------------------
    async def get(self, id: str, *, organization_id: str) -> Optional[dict]:
        """Tenant-scoped read by adjudication id (organisation is required)."""
        row = await self._fetch_one(
            _SELECT_BY_ID_SQL, _as_uuid(organization_id), _as_uuid(id)
        )
        return dict(row) if row is not None else None

    async def get_adjudication(
        self,
        activity_key: str,
        original_activity: str,
        clarification: str,
        *,
        organization_id: str,
        version: int = 1,
    ) -> Optional[dict]:
        """Retrieve one persisted version (provenance read) for an exact key."""
        row = await self._fetch_one(
            _SELECT_BY_KEY_SQL,
            _as_uuid(organization_id),
            activity_key,
            original_activity,
            clarification,
            int(version),
        )
        return dict(row) if row is not None else None

    async def list_for_organization(
        self,
        organization_id: str,
        *,
        activity_key: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Most-recent-first adjudications for one organisation."""
        rows = await self._fetch_all(
            _LIST_SQL, _as_uuid(organization_id), activity_key, int(limit)
        )
        return [dict(row) for row in rows]

    # -- AbstractRepository contract ----------------------------------------
    async def save(self, entity: Any) -> Any:
        """Refused: rows are produced by the engine (see :meth:`record`)."""
        raise ValueError(
            "activity_clarifications rows must be written through record()/"
            "apply_clarification()/apply_decline() so the factor metadata is the "
            "factor-selection policy's own result (F-048-2)."
        )

    async def delete(self, id: str, *, organization_id: str) -> None:
        """Tenant-scoped removal of a stored adjudication row."""
        await self._execute(_DELETE_SQL, _as_uuid(organization_id), _as_uuid(id))

    @staticmethod
    def decode_eligible_groups(row: dict) -> list:
        """Decode the persisted ``eligible_groups`` JSONB for callers/tests."""
        return list(loads_jsonb(row.get("eligible_groups")) or [])

    # -- adjudication lifecycle (F-039-1 A/B/C/D) ---------------------------
    async def effective(
        self,
        *,
        organization_id: str,
        activity_key: str,
        original_activity: str,
        context_key: Optional[str] = None,
    ) -> Optional[dict]:
        """The current/effective adjudication for ONE bounded context.

        Deliberately requires the full context boundary (organisation +
        ``effective_context_key`` + activity key + the original extracted activity):
        looking up by activity text alone would leak one context's adjudication into
        another, which D-039-1-C forbids.
        """
        row = await self._fetch_one(
            _EFFECTIVE_SQL,
            _as_uuid(organization_id),
            context_key or activity_key,
            activity_key,
            original_activity,
        )
        return dict(row) if row is not None else None

    async def history(
        self, adjudication_id: str, *, organization_id: str
    ) -> list[dict]:
        """Every version of one adjudication, oldest → newest (immutable history)."""
        rows = await self._fetch_all(
            _HISTORY_SQL, _as_uuid(organization_id), _as_uuid(adjudication_id)
        )
        return [dict(row) for row in rows]

    async def supersede(self, row: dict, *, organization_id: str) -> None:
        """Retire the previous version (``is_current`` only — nothing else changes)."""
        await self._execute(
            _SUPERSEDE_SQL, _as_uuid(organization_id), _as_uuid(row.get("id"))
        )

    async def apply_versioned(
        self,
        record: ClarificationRecord,
        *,
        organization_id: str,
        actor_id: str,
        item_id: Optional[str] = None,
        batch_key: Optional[str] = None,
        source_evidence_ref: Optional[str] = None,
        context_key: Optional[str] = None,
        evidence_signature: Optional[str] = None,
        evidence_context: Optional[dict] = None,
    ) -> dict:
        """Persist an adjudication as version 1, as a replay, or as a NEW version.

        * no effective adjudication → version 1 (its own identity);
        * the same clarification already effective → returned unchanged (replay);
        * a different clarification → version + 1 with ``supersedes_id`` pointing at the
          previous row, which is retired via ``is_current = false`` only. The previous
          version keeps its clarification, outcome and factor metadata forever
          (D-039-1-D/-H).
        """
        key = context_key or record.activity_key
        current = await self.effective(
            organization_id=organization_id,
            activity_key=record.activity_key,
            original_activity=record.original_activity,
            context_key=key,
        )
        if current is not None and (current.get("clarification") or "") == record.clarification:
            return current  # idempotent replay — nothing new, nothing overwritten
        version = 1 if current is None else int(current.get("version") or 1) + 1
        stored = await self.record(
            record,
            organization_id=organization_id,
            item_id=item_id,
            batch_key=batch_key,
            source_evidence_ref=source_evidence_ref,
            eligible_groups=record.notes,
            adjudication_id=(current or {}).get("adjudication_id"),
            version=version,
            supersedes_id=(current or {}).get("id"),
            is_current=True,
            effective_context_key=key,
            evidence_signature=evidence_signature,
            evidence_context=evidence_context,
        )
        if current is not None and stored is not None:
            await self.supersede(current, organization_id=organization_id)
        return stored or {}
