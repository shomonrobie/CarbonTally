"""Roles repository (V3 Phase 6).

Read access to the RC2 ``roles`` table (RBAC role definitions). The customer
organisation role set is the ``organization_members.role`` CHECK constraint
(owner/admin/member/viewer — the V3 customer role model); this repository serves
the ``roles`` table rows for invitation ``role_id`` resolution and reference
only. No second role system is created.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository

_ROLE_COLUMNS = "id, name, description, permissions, created_at, updated_at"


def _row_to_role(row: Any) -> dict:
    r = dict(row)
    return {
        "id": str(r["id"]),
        "name": str(r["name"]),
        "description": r.get("description"),
        "permissions": r.get("permissions"),
        "created_at": (
            r["created_at"].isoformat()
            if getattr(r.get("created_at"), "isoformat", None)
            else r.get("created_at")
        ),
    }


class RolesRepository(AbstractRepository[dict]):
    """Read-only access to the ``roles`` table (invitation resolution)."""

    async def get_by_name(self, name: str) -> Optional[dict]:
        row = await self._fetch_one(
            f"SELECT {_ROLE_COLUMNS} FROM public.roles WHERE name = $1",
            name,
        )
        return _row_to_role(row) if row is not None else None

    async def list(self) -> list[dict]:
        rows = await self._fetch_all(
            f"SELECT {_ROLE_COLUMNS} FROM public.roles ORDER BY name, id"
        )
        return [_row_to_role(r) for r in rows]

    async def get(self, id: str) -> Optional[dict]:
        row = await self._fetch_one(
            f"SELECT {_ROLE_COLUMNS} FROM public.roles WHERE id = $1",
            id,
        )
        return _row_to_role(row) if row is not None else None

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        return None
