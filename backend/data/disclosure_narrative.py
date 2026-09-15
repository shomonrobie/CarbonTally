"""Phase 8 B4 — narrative overlay data layer (repository).

Persistence for ``public.disclosure_narrative_entries`` (B4-1). It stores prose
only: it never writes an authoritative value, never touches a calculation or a
factor, and never creates an artefact. Supersession is an in-place content
replacement of the single entry per ``(report version, requirement, kind)``
(``A1``), recorded through ``updated_at``/``updated_by``.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository

_ENTRY_COLUMNS = """
    id, organization_id, report_version_id, requirement_version_id,
    disclosure_value_id, narrative_kind, body, state, authored_by, authored_at,
    updated_by, updated_at, created_at
"""


def _row_to_entry(row: Any) -> dict:
    r = dict(row)
    return {
        "id": str(r["id"]),
        "organization_id": str(r["organization_id"]),
        "report_version_id": str(r["report_version_id"]),
        "requirement_version_id": str(r["requirement_version_id"]),
        "disclosure_value_id": str(r["disclosure_value_id"]) if r.get("disclosure_value_id") else None,
        "narrative_kind": str(r["narrative_kind"]),
        "body": r["body"],
        "state": str(r["state"]),
        "authored_by": str(r["authored_by"]) if r.get("authored_by") else None,
        "authored_at": r.get("authored_at").isoformat() if r.get("authored_at") else None,
        "updated_by": str(r["updated_by"]) if r.get("updated_by") else None,
        "updated_at": r.get("updated_at").isoformat() if r.get("updated_at") else None,
        "created_at": r.get("created_at").isoformat() if r.get("created_at") else None,
    }


class DisclosureNarrativeRepository(AbstractRepository[dict]):
    """Requirement-bound narrative entries (A1)."""

    async def get(self, id: str) -> Optional[dict]:
        row = await self._fetch_one(
            f"SELECT {_ENTRY_COLUMNS} FROM public.disclosure_narrative_entries WHERE id = $1",
            id,
        )
        return _row_to_entry(row) if row is not None else None

    async def list_entries(
        self, report_version_id: str, *, requirement_version_id: Optional[str] = None
    ) -> list[dict]:
        if requirement_version_id:
            rows = await self._fetch_all(
                f"SELECT {_ENTRY_COLUMNS} FROM public.disclosure_narrative_entries "
                "WHERE report_version_id = $1 AND requirement_version_id = $2 "
                "ORDER BY narrative_kind",
                report_version_id,
                requirement_version_id,
            )
        else:
            rows = await self._fetch_all(
                f"SELECT {_ENTRY_COLUMNS} FROM public.disclosure_narrative_entries "
                "WHERE report_version_id = $1 ORDER BY requirement_version_id, narrative_kind",
                report_version_id,
            )
        return [_row_to_entry(row) for row in rows]

    async def upsert(
        self,
        *,
        organization_id: str,
        report_version_id: str,
        requirement_version_id: str,
        narrative_kind: str,
        body: str,
        authored_by: Optional[str] = None,
        disclosure_value_id: Optional[str] = None,
    ) -> dict:
        """Create or replace the single draft entry for the binding (A1)."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.disclosure_narrative_entries
                (organization_id, report_version_id, requirement_version_id,
                 disclosure_value_id, narrative_kind, body, state, authored_by, authored_at)
            VALUES ($1, $2, $3, $4, $5, $6, 'DRAFT', $7, now())
            ON CONFLICT (report_version_id, requirement_version_id, narrative_kind)
            DO UPDATE SET body = EXCLUDED.body,
                          state = 'DRAFT',
                          disclosure_value_id = EXCLUDED.disclosure_value_id,
                          updated_by = EXCLUDED.authored_by,
                          updated_at = now()
            RETURNING {_ENTRY_COLUMNS}
            """,
            organization_id,
            report_version_id,
            requirement_version_id,
            disclosure_value_id,
            narrative_kind,
            body,
            authored_by,
        )
        return _row_to_entry(row) if row is not None else {}

    async def save(self, entity: dict) -> dict:
        return await self.upsert(
            organization_id=str(entity["organization_id"]),
            report_version_id=str(entity["report_version_id"]),
            requirement_version_id=str(entity["requirement_version_id"]),
            narrative_kind=str(entity["narrative_kind"]),
            body=str(entity["body"]),
            authored_by=entity.get("authored_by"),
            disclosure_value_id=entity.get("disclosure_value_id"),
        )

    async def delete(self, id: str) -> None:
        await self._execute(
            "DELETE FROM public.disclosure_narrative_entries WHERE id = $1", id
        )
