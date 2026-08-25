"""Report versions repository (V3 Phase 5).

Persistence for the RC2 ``report_versions`` table — the version-history spine
referenced by ``report_generation_queue`` rows. The V3M2 schema defines the
table with a natural-key unique constraint ``(report_id, version_number)`` and
an ``is_current`` flag; this repository reads/writes that existing structure
only (no schema change). ``report_id`` references the generated report's
``report_generation_queue.id`` (the RC2 dump carries no ``reports`` parent
table, which is documented as an intentional inspection flag in
``database/rc1/002_rc1_constraints.sql``).
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb

_VERSION_COLUMNS = """
    id, report_id, version_number, content, file_url, file_name,
    created_by, created_at, notes, change_summary, is_current
"""


def _row_to_version(row: Any) -> dict:
    r = dict(row)
    return {
        "id": str(r["id"]),
        "report_id": str(r["report_id"]),
        "version_number": int(r["version_number"]),
        "content": loads_jsonb(r.get("content")) if r.get("content") is not None else {},
        "file_url": str(r["file_url"]) if r.get("file_url") else "",
        "file_name": r.get("file_name"),
        "created_by": str(r["created_by"]) if r.get("created_by") else None,
        "created_at": (
            r["created_at"].isoformat() if getattr(r.get("created_at"), "isoformat", None) else r.get("created_at")
        ),
        "notes": r.get("notes"),
        "change_summary": r.get("change_summary"),
        "is_current": bool(r.get("is_current", False)),
    }


class ReportVersionsRepository(AbstractRepository[dict]):
    """CRUD for ``report_versions`` (version history of generated reports)."""

    async def next_version_number(self, report_id: str) -> int:
        """Return the next ``version_number`` for a report (1 when none exist)."""
        row = await self._fetch_one(
            "SELECT COALESCE(MAX(version_number), 0)::int AS n "
            "FROM public.report_versions WHERE report_id = $1",
            report_id,
        )
        return (int(row["n"]) if row is not None else 0) + 1

    async def create(
        self,
        report_id: str,
        *,
        version_number: int,
        content: Optional[dict[str, Any]] = None,
        file_url: str = "",
        file_name: Optional[str] = None,
        created_by: Optional[str] = None,
        notes: Optional[str] = None,
        change_summary: Optional[str] = None,
        is_current: bool = True,
    ) -> dict:
        """Insert one version snapshot row and return it."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.report_versions (
                report_id, version_number, content, file_url, file_name,
                created_by, notes, change_summary, is_current
            ) VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7, $8, $9)
            RETURNING {_VERSION_COLUMNS}
            """,
            report_id,
            version_number,
            dumps_jsonb(content or {}),
            file_url,
            file_name,
            created_by,
            notes,
            change_summary,
            is_current,
        )
        if row is None:
            raise RuntimeError("report version insert returned no row")
        return _row_to_version(row)

    async def list_for_report(self, report_id: str) -> list[dict]:
        """Return every version of a report, newest first."""
        rows = await self._fetch_all(
            f"""
            SELECT {_VERSION_COLUMNS} FROM public.report_versions
            WHERE report_id = $1
            ORDER BY version_number DESC
            """,
            report_id,
        )
        return [_row_to_version(r) for r in rows]

    async def get_current(self, report_id: str) -> Optional[dict]:
        """Return the current version of a report, or ``None``."""
        row = await self._fetch_one(
            f"""
            SELECT {_VERSION_COLUMNS} FROM public.report_versions
            WHERE report_id = $1 AND is_current = TRUE
            ORDER BY version_number DESC
            LIMIT 1
            """,
            report_id,
        )
        return _row_to_version(row) if row is not None else None

    async def get(self, id: str) -> Optional[dict]:
        row = await self._fetch_one(
            f"SELECT {_VERSION_COLUMNS} FROM public.report_versions WHERE id = $1",
            id,
        )
        return _row_to_version(row) if row is not None else None

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        await self._execute(
            "DELETE FROM public.report_versions WHERE id = $1", id
        )
