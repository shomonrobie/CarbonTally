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
from domain.audit import AuditEntry, AuditQuery

_SYSTEM_UUID = "00000000-0000-0000-0000-000000000000"

_AUDIT_COLUMNS = """
    id, action_type, table_name, record_id, performed_by, performed_at,
    old_data, new_data, changes, ip_address, metadata
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
    payload: dict[str, object] = {
        "correlation_id": entry.correlation_id,
        "actor": entry.actor,
    }
    if entry.reason is not None:
        payload["reason"] = entry.reason
    return dumps_jsonb(payload)


def _row_to_entry(row: Any) -> AuditEntry:
    r = dict(row)
    metadata = loads_jsonb(r.get("metadata")) or {}
    ip = r.get("ip_address")
    return AuditEntry(
        id=str(r["id"]),
        correlation_id=str(metadata.get("correlation_id") or ""),
        entity_type=str(r["table_name"]),
        entity_id=str(r["record_id"]),
        action=str(r["action_type"]),
        actor=str(metadata.get("actor") or r.get("performed_by") or ""),
        occurred_at=r["performed_at"],
        changed_fields=loads_jsonb(r.get("changes")) or {},
        reason=metadata.get("reason"),
        ip_address=str(ip) if ip is not None else None,
        before=loads_jsonb(r.get("old_data")),
        after=loads_jsonb(r.get("new_data")),
    )


class AuditRepository(AbstractRepository[AuditEntry]):
    """Append-only audit trail repository."""

    async def record(self, entry: AuditEntry) -> AuditEntry:
        """Append one audit entry and return it with the stored id."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.audit_trail (
                action_type, table_name, record_id, performed_by,
                performed_at, old_data, new_data, changes, ip_address, metadata,
                created_at
            ) VALUES ($1, $2, $3::uuid, $4::uuid, $5, $6::jsonb, $7::jsonb,
                      $8::jsonb, NULLIF($9, '')::inet, $10::jsonb, NOW())
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
        )
        if row is None:
            raise RuntimeError("audit insert returned no row")
        return _row_to_entry(row)

    async def query(self, filters: AuditQuery) -> list[AuditEntry]:
        """Search the audit trail with the given filters."""
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
        params.append(filters.limit)
        params.append(filters.offset)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        query = (
            f"SELECT {_AUDIT_COLUMNS} FROM public.audit_trail{where}"
            " ORDER BY performed_at DESC, id"
            + f" LIMIT ${len(params) - 1} OFFSET ${len(params)}"
        )
        rows = await self._fetch_all(query, *params)
        return [_row_to_entry(r) for r in rows]

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
        """Persist an audit entry (append-only: ``save`` inserts)."""
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
                ON CONFLICT (id)
                DO UPDATE SET
                    action_type = EXCLUDED.action_type,
                    table_name = EXCLUDED.table_name,
                    record_id = EXCLUDED.record_id,
                    performed_by = EXCLUDED.performed_by,
                    performed_at = EXCLUDED.performed_at,
                    old_data = EXCLUDED.old_data,
                    new_data = EXCLUDED.new_data,
                    changes = EXCLUDED.changes,
                    ip_address = EXCLUDED.ip_address,
                    metadata = EXCLUDED.metadata
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
