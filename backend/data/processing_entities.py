"""Processing-entities repository (V3, ADR-V3-001 — DECIDED).

Persistence for the V3M-1 ``processing_entities`` table. Access to this table is
CarbonTally-internal (the table is deny-by-default for ``authenticated``;
entity-scoped reads are via the V3M-6 ``is_entity_member`` RLS policies).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.entity import ProcessingEntity

_ENTITY_COLUMNS = """
    id, name, description, status, metadata, created_at, updated_at,
    created_by, updated_by
"""


def _row_to_entity(row: Any) -> ProcessingEntity:
    r = dict(row)
    return ProcessingEntity(
        id=str(r["id"]),
        name=str(r["name"]),
        status=str(r["status"]),
        description=str(r["description"]) if r.get("description") else None,
        metadata=loads_jsonb(r.get("metadata")) or {},
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
        created_by=str(r["created_by"]) if r.get("created_by") else None,
        updated_by=str(r["updated_by"]) if r.get("updated_by") else None,
    )


class ProcessingEntitiesRepository(AbstractRepository[ProcessingEntity]):
    """CRUD and lifecycle persistence for processing entities."""

    async def get(self, id: str) -> Optional[ProcessingEntity]:
        """Return the entity with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_ENTITY_COLUMNS} FROM public.processing_entities WHERE id = $1",
            id,
        )
        return _row_to_entity(row) if row is not None else None

    async def list_all(self) -> list[ProcessingEntity]:
        """Return every processing entity, by name."""
        rows = await self._fetch_all(
            f"SELECT {_ENTITY_COLUMNS} FROM public.processing_entities "
            "ORDER BY name, id"
        )
        return [_row_to_entity(r) for r in rows]

    async def list_by_status(self, status: str) -> list[ProcessingEntity]:
        """Return every entity in ``status``, by name."""
        rows = await self._fetch_all(
            f"SELECT {_ENTITY_COLUMNS} FROM public.processing_entities "
            "WHERE status = $1 ORDER BY name, id",
            status,
        )
        return [_row_to_entity(r) for r in rows]

    async def save(self, entity: ProcessingEntity) -> ProcessingEntity:
        """Insert or update an entity (lifecycle preserved; never hard-delete)."""
        now = datetime.now(timezone.utc)
        row = await self._fetch_one(
            f"""
            INSERT INTO public.processing_entities (
                id, name, description, status, metadata,
                created_at, updated_at, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9)
            ON CONFLICT (id)
            DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                status = EXCLUDED.status,
                metadata = EXCLUDED.metadata,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            RETURNING {_ENTITY_COLUMNS}
            """,
            entity.id,
            entity.name,
            entity.description,
            entity.status,
            dumps_jsonb(entity.metadata),
            entity.created_at or now,
            now,
            entity.created_by,
            entity.updated_by,
        )
        if row is None:
            raise RuntimeError("processing entity upsert returned no row")
        return _row_to_entity(row)

    async def update_status(
        self, id: str, status: str, *, updated_by: Optional[str] = None
    ) -> ProcessingEntity:
        """Transition an entity to ``status`` (authority enforced by the API)."""
        row = await self._fetch_one(
            f"""
            UPDATE public.processing_entities
            SET status = $2, updated_at = NOW(), updated_by = $3
            WHERE id = $1
            RETURNING {_ENTITY_COLUMNS}
            """,
            id,
            status,
            updated_by,
        )
        if row is None:
            raise RuntimeError(f"processing entity {id!r} does not exist")
        return _row_to_entity(row)

    async def delete(self, id: str) -> None:
        """Hard-delete is NOT permitted for referenced entities (V3M-1
        ON DELETE RESTRICT). Raising here keeps the domain honest: lifecycle
        transitions are the supported path."""
        raise NotImplementedError(
            "processing_entities are never hard-deleted; use lifecycle transitions"
        )
