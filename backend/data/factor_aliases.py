"""Factor-aliases repository (Backend v2.1 §10).

Persistence for the RC2 ``factor_aliases`` table. ``organization_id = NULL``
identifies a global alias; a non-NULL value an organisation-scoped alias.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository
from domain.matching import FactorAlias

_ALIAS_COLUMNS = """
    id, organization_id, alias_text, target_activity_type,
    target_provider_key, created_by, created_at
"""


def _row_to_alias(row: Any) -> FactorAlias:
    r = dict(row)
    return FactorAlias(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]) if r.get("organization_id") else None,
        alias_text=str(r["alias_text"]),
        target_activity_type=str(r["target_activity_type"]),
        target_provider_key=str(r["target_provider_key"]),
        created_by=str(r["created_by"]) if r.get("created_by") else None,
        created_at=r.get("created_at"),
    )


class FactorAliasesRepository(AbstractRepository[FactorAlias]):
    """Lookup and persistence for global + org-scoped activity aliases."""

    async def find_by_alias(
        self, alias: str, org_id: Optional[str]
    ) -> Optional[FactorAlias]:
        """Resolve ``alias`` for ``org_id`` (org-scoped first, then global)."""
        row = await self._fetch_one(
            f"""
            SELECT {_ALIAS_COLUMNS} FROM public.factor_aliases
            WHERE organization_id = $1::uuid AND alias_text = $2
            ORDER BY created_at DESC
            LIMIT 1
            """,
            org_id,
            alias,
        )
        if row is None:
            row = await self._fetch_one(
                f"""
                SELECT {_ALIAS_COLUMNS} FROM public.factor_aliases
                WHERE organization_id IS NULL AND alias_text = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                alias,
            )
        return _row_to_alias(row) if row is not None else None

    async def get_global_aliases(self) -> list[FactorAlias]:
        """Return every global alias (no organisation scoping)."""
        rows = await self._fetch_all(
            f"""
            SELECT {_ALIAS_COLUMNS} FROM public.factor_aliases
            WHERE organization_id IS NULL
            ORDER BY alias_text, id
            """
        )
        return [_row_to_alias(r) for r in rows]

    async def get_org_aliases(self, org_id: str) -> list[FactorAlias]:
        """Return every alias scoped to ``org_id``."""
        rows = await self._fetch_all(
            f"""
            SELECT {_ALIAS_COLUMNS} FROM public.factor_aliases
            WHERE organization_id = $1
            ORDER BY alias_text, id
            """,
            org_id,
        )
        return [_row_to_alias(r) for r in rows]

    async def get(self, id: str) -> Optional[FactorAlias]:
        """Return the single alias with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_ALIAS_COLUMNS} FROM public.factor_aliases WHERE id = $1",
            id,
        )
        return _row_to_alias(row) if row is not None else None

    async def save(self, entity: FactorAlias) -> FactorAlias:
        """Persist an alias (insert, or update when ``id`` is already set)."""
        if entity.id:
            row = await self._fetch_one(
                f"""
                INSERT INTO public.factor_aliases (
                    id, organization_id, alias_text, target_activity_type,
                    target_provider_key, created_by, created_at
                ) VALUES ($1, $2::uuid, $3, $4, $5, $6::uuid, $7)
                ON CONFLICT (id)
                DO UPDATE SET
                    organization_id = EXCLUDED.organization_id,
                    alias_text = EXCLUDED.alias_text,
                    target_activity_type = EXCLUDED.target_activity_type,
                    target_provider_key = EXCLUDED.target_provider_key,
                    created_by = EXCLUDED.created_by
                RETURNING {_ALIAS_COLUMNS}
                """,
                entity.id,
                entity.organization_id,
                entity.alias_text,
                entity.target_activity_type,
                entity.target_provider_key,
                entity.created_by,
                entity.created_at,
            )
        else:
            row = await self._fetch_one(
                f"""
                INSERT INTO public.factor_aliases (
                    organization_id, alias_text, target_activity_type,
                    target_provider_key, created_by, created_at
                ) VALUES ($1::uuid, $2, $3, $4, $5::uuid, $6)
                RETURNING {_ALIAS_COLUMNS}
                """,
                entity.organization_id,
                entity.alias_text,
                entity.target_activity_type,
                entity.target_provider_key,
                entity.created_by,
                entity.created_at,
            )
        if row is None:
            raise RuntimeError("factor alias upsert returned no row")
        return _row_to_alias(row)

    async def delete(self, id: str) -> None:
        """Delete an alias."""
        await self._execute(
            "DELETE FROM public.factor_aliases WHERE id = $1", id
        )
