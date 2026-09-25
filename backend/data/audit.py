"""Audit repository (Backend v2.1 §10, §15).

Append-only persistence for the RC2 ``audit_trail`` table. The table has no
``correlation_id``/``reason``/``actor`` columns, so those v2.1 fields are
stored inside the ``metadata`` JSONB column (the table already uses ``metadata``
for flexible extra data).
"""
from __future__ import annotations

import csv
import io
import uuid
from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.audit import (
    ACTOR_SYSTEM,
    AuditEntry,
    AuditQuery,
    CAT_SYSTEM,
    ORIGIN_SYSTEM,
    classify_action,
    classify_origin,
)

_SYSTEM_UUID = "00000000-0000-0000-0000-000000000000"

_AUDIT_COLUMNS = """
    id, action_type, table_name, record_id, performed_by, performed_at,
    old_data, new_data, changes, ip_address, metadata,
    actor_organization_id, acting_for_organization_id
"""

_CSV_HEADERS = [
    "id",
    "correlation_id",
    "entity_type",
    "entity_id",
    "action",
    "actor",
    "occurred_at",
    "changed_fields",
    "reason",
    "ip_address",
    "before",
    "after",
]


def _actor_uuid(actor: str) -> str:
    """Return ``actor`` as a UUID, or the service-role placeholder when it is
    a non-UUID label (e.g. ``system``)."""
    try:
        return str(uuid.UUID(actor))
    except ValueError:
        return _SYSTEM_UUID


def _entry_metadata(entry: AuditEntry) -> str:
    """Serialise the entry's v2.1 fields + Phase 7 taxonomy into ``metadata``.

    Phase 7 always stamps ``category`` and ``origin`` (derived when the caller
    did not set them) so the ledger is investigable without a schema change.
    Actor type / outcome / organisation id are stored only when supplied.
    """
    actor_type = entry.actor_type
    origin = entry.origin or classify_origin(entry.actor, actor_type)
    category = entry.category or classify_action(entry.action)
    payload: dict[str, object] = {
        "correlation_id": entry.correlation_id,
        "actor": entry.actor,
        "category": category,
        "origin": origin,
    }
    if actor_type is not None:
        payload["actor_type"] = actor_type
    if entry.outcome is not None:
        payload["outcome"] = entry.outcome
    if entry.organization_id is not None:
        payload["organization_id"] = entry.organization_id
    if entry.reason is not None:
        payload["reason"] = entry.reason
    # P17-IMPLEMENT-02: mirror the acting-for attribution into metadata as well
    # as into the dedicated columns, so the ledger stays investigable from the
    # metadata payload alone (the established pattern for this table).
    if entry.actor_organization_id is not None:
        payload["actor_organization_id"] = entry.actor_organization_id
    if entry.acting_for_organization_id is not None:
        payload["acting_for_organization_id"] = entry.acting_for_organization_id
    return dumps_jsonb(payload)


def _row_to_entry(row: Any) -> AuditEntry:
    r = dict(row)
    metadata = loads_jsonb(r.get("metadata")) or {}
    ip = r.get("ip_address")
    action = str(r["action_type"])
    actor = str(metadata.get("actor") or r.get("performed_by") or "")
    actor_type = metadata.get("actor_type")
    return AuditEntry(
        id=str(r["id"]),
        correlation_id=str(metadata.get("correlation_id") or ""),
        entity_type=str(r["table_name"]),
        entity_id=str(r["record_id"]),
        action=action,
        actor=actor,
        occurred_at=r["performed_at"],
        changed_fields=loads_jsonb(r.get("changes")) or {},
        reason=metadata.get("reason"),
        ip_address=str(ip) if ip is not None else None,
        before=loads_jsonb(r.get("old_data")),
        after=loads_jsonb(r.get("new_data")),
        # Phase 7 — read the taxonomy back; derive when an entry pre-dates it.
        actor_type=actor_type,
        origin=metadata.get("origin") or classify_origin(actor, actor_type),
        outcome=metadata.get("outcome"),
        organization_id=metadata.get("organization_id"),
        category=metadata.get("category") or classify_action(action),
        # P17-IMPLEMENT-02 — acting-for attribution. The dedicated column is
        # authoritative; fall back to metadata so entries written before the
        # column existed are still read correctly.
        actor_organization_id=(
            str(r["actor_organization_id"]) if r.get("actor_organization_id")
            else metadata.get("actor_organization_id")
        ),
        acting_for_organization_id=(
            str(r["acting_for_organization_id"])
            if r.get("acting_for_organization_id")
            else metadata.get("acting_for_organization_id")
        ),
    )


_SORT_CLAUSES = {
    "occurred_at": "performed_at",
    "action": "action_type",
    "actor": "metadata->>'actor'",
    "entity_type": "table_name",
}


def _where_clause(filters: AuditQuery) -> tuple[list[str], list[object]]:
    """Build the parameterised WHERE clause shared by ``query`` and ``count``.

    ``q`` is a free-text search across the fields an operator would recognise
    (action, resource, entity id, actor, stored reason); it deliberately also
    matches ``record_id``/``performed_by`` casts so UUIDs stay findable.
    """
    clauses: list[str] = []
    params: list[object] = []
    if filters.correlation_id is not None:
        params.append(filters.correlation_id)
        clauses.append(f"metadata->>'correlation_id' = ${len(params)}")
    if filters.entity_type is not None:
        params.append(filters.entity_type)
        clauses.append(f"table_name = ${len(params)}")
    if filters.entity_id is not None:
        params.append(filters.entity_id)
        clauses.append(f"record_id = ${len(params)}::uuid")
    if filters.action is not None:
        params.append(filters.action)
        clauses.append(f"action_type = ${len(params)}")
    if filters.actor is not None:
        params.append(_actor_uuid(filters.actor))
        clauses.append(
            f"(performed_by = ${len(params)}::uuid OR metadata->>'actor' = ${len(params)}::text)"
        )
    if filters.occurred_after is not None:
        params.append(filters.occurred_after)
        clauses.append(f"performed_at >= ${len(params)}")
    if filters.occurred_before is not None:
        params.append(filters.occurred_before)
        clauses.append(f"performed_at <= ${len(params)}")
    if filters.q is not None:
        params.append(f"%{filters.q}%")
        p = len(params)
        clauses.append(
            f"(action_type ILIKE ${p} OR table_name ILIKE ${p} "
            f"OR record_id::text ILIKE ${p} OR performed_by::text ILIKE ${p} "
            f"OR metadata->>'actor' ILIKE ${p} OR metadata->>'reason' ILIKE ${p})"
        )
    # Phase 7 — investigation filters over the taxonomy stored in metadata.
    # ``category`` additionally matches entries written before the taxonomy
    # existed by deriving the same prefix mapping at the SQL boundary is not
    # possible; those legacy rows carry no category and are therefore excluded
    # from a category filter (honest: they are categorised on read, not in SQL).
    if filters.category is not None:
        params.append(filters.category)
        clauses.append(f"metadata->>'category' = ${len(params)}")
    if filters.origin is not None:
        params.append(filters.origin)
        clauses.append(f"metadata->>'origin' = ${len(params)}")
    if filters.outcome is not None:
        params.append(filters.outcome)
        clauses.append(f"metadata->>'outcome' = ${len(params)}")
    if filters.organization_id is not None:
        params.append(filters.organization_id)
        clauses.append(f"metadata->>'organization_id' = ${len(params)}")
    return clauses, params


class AuditRepository(AbstractRepository[AuditEntry]):
    """Append-only audit trail repository."""

    async def record(self, entry: AuditEntry) -> AuditEntry:
        """Append one audit entry and return it with the stored id."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.audit_trail (
                action_type, table_name, record_id, performed_by,
                performed_at, old_data, new_data, changes, ip_address, metadata,
                created_at, actor_organization_id, acting_for_organization_id
            ) VALUES ($1, $2, $3::uuid, $4::uuid, $5, $6::jsonb, $7::jsonb,
                      $8::jsonb, NULLIF($9, '')::inet, $10::jsonb, NOW(),
                      NULLIF($11, '')::uuid, NULLIF($12, '')::uuid)
            RETURNING {_AUDIT_COLUMNS}
            """,
            entry.action,
            entry.entity_type,
            entry.entity_id,
            _actor_uuid(entry.actor),
            entry.occurred_at,
            dumps_jsonb(entry.before),
            dumps_jsonb(entry.after),
            dumps_jsonb(entry.changed_fields),
            entry.ip_address,
            _entry_metadata(entry),
            entry.actor_organization_id,
            entry.acting_for_organization_id,
        )
        if row is None:
            raise RuntimeError("audit insert returned no row")
        return _row_to_entry(row)

    async def query(self, filters: AuditQuery) -> list[AuditEntry]:
        """Search the audit trail with the given filters.

        ``sort``/``order`` (BL-4) select the server ordering from a fixed
        whitelist — never raw SQL — so the audit console can page a fully
        ordered result set without loading it client-side.
        """
        clauses, params = _where_clause(filters)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        if filters.sort is not None:
            order_sql = f"ORDER BY {_SORT_CLAUSES[filters.sort]} {filters.order.upper()}, id"
        else:
            order_sql = "ORDER BY performed_at DESC, id"
        params.append(filters.limit)
        params.append(filters.offset)
        query = (
            f"SELECT {_AUDIT_COLUMNS} FROM public.audit_trail{where} {order_sql}"
            + f" LIMIT ${len(params) - 1} OFFSET ${len(params)}"
        )
        rows = await self._fetch_all(query, *params)
        return [_row_to_entry(r) for r in rows]

    async def count(self, filters: AuditQuery) -> int:
        """Return the number of rows matching ``filters`` (BL-4).

        Uses the same WHERE clause as ``query`` so the audit console can report
        an honest total across pages/filters instead of the page length.
        """
        clauses, params = _where_clause(filters)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        row = await self._fetch_one(
            f"SELECT COUNT(*) AS n FROM public.audit_trail{where}",
            *params,
        )
        return int(row["n"]) if row else 0

    async def export_csv(self, filters: AuditQuery) -> str:
        """Export the audit trail matching ``filters`` as CSV."""
        entries = await self.query(filters)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=_CSV_HEADERS)
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "id": entry.id,
                    "correlation_id": entry.correlation_id,
                    "entity_type": entry.entity_type,
                    "entity_id": entry.entity_id,
                    "action": entry.action,
                    "actor": entry.actor,
                    "occurred_at": entry.occurred_at.isoformat(),
                    "changed_fields": dumps_jsonb(entry.changed_fields),
                    "reason": entry.reason or "",
                    "ip_address": entry.ip_address or "",
                    "before": dumps_jsonb(entry.before),
                    "after": dumps_jsonb(entry.after),
                }
            )
        return buffer.getvalue()

    async def get_by_correlation(self, correlation_id: str) -> list[AuditEntry]:
        """Return every entry belonging to one correlation, in order."""
        rows = await self._fetch_all(
            f"""
            SELECT {_AUDIT_COLUMNS} FROM public.audit_trail
            WHERE metadata->>'correlation_id' = $1
            ORDER BY performed_at, id
            """,
            correlation_id,
        )
        return [_row_to_entry(r) for r in rows]

    async def get(self, id: str) -> Optional[AuditEntry]:
        """Return the single audit entry with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_AUDIT_COLUMNS} FROM public.audit_trail WHERE id = $1",
            id,
        )
        return _row_to_entry(row) if row is not None else None

    async def save(self, entity: AuditEntry) -> AuditEntry:
        """Persist an audit entry (append-only: ``save`` inserts only).

        Phase 7 removed the previous ``ON CONFLICT (id) DO UPDATE`` upsert so
        the write path can never rewrite history; the DB-level immutability
        trigger (migration ``20260912000000``) enforces the same rule.
        """
        if entity.id:
            row = await self._fetch_one(
                f"""
                INSERT INTO public.audit_trail (
                    id, action_type, table_name, record_id, performed_by,
                    performed_at, old_data, new_data, changes, ip_address,
                    metadata, created_at
                ) VALUES ($1, $2, $3, $4::uuid, $5::uuid, $6, $7::jsonb,
                          $8::jsonb, $9::jsonb, NULLIF($10, '')::inet,
                          $11::jsonb, NOW())
                RETURNING {_AUDIT_COLUMNS}
                """,
                entity.id,
                entity.action,
                entity.entity_type,
                entity.entity_id,
                _actor_uuid(entity.actor),
                entity.occurred_at,
                dumps_jsonb(entity.before),
                dumps_jsonb(entity.after),
                dumps_jsonb(entity.changed_fields),
                entity.ip_address,
                _entry_metadata(entity),
            )
        else:
            row = await self._fetch_one(
                f"""
                INSERT INTO public.audit_trail (
                    action_type, table_name, record_id, performed_by,
                    performed_at, old_data, new_data, changes, ip_address,
                    metadata, created_at
                ) VALUES ($1, $2, $3::uuid, $4::uuid, $5, $6::jsonb, $7::jsonb,
                          $8::jsonb, NULLIF($9, '')::inet, $10::jsonb, NOW())
                RETURNING {_AUDIT_COLUMNS}
                """,
                entity.action,
                entity.entity_type,
                entity.entity_id,
                _actor_uuid(entity.actor),
                entity.occurred_at,
                dumps_jsonb(entity.before),
                dumps_jsonb(entity.after),
                dumps_jsonb(entity.changed_fields),
                entity.ip_address,
                _entry_metadata(entity),
            )
        if row is None:
            raise RuntimeError("audit upsert returned no row")
        return _row_to_entry(row)

    async def delete(self, id: str) -> None:
        """Delete an audit entry (not used — audit is immutable)."""
        await self._execute(
            "DELETE FROM public.audit_trail WHERE id = $1", id
        )
