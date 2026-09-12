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
from domain.report_lifecycle import DEFAULT_STATUS, validate_status

_VERSION_COLUMNS = """
    id, report_id, version_number, content, file_url, file_name,
    created_by, created_at, notes, change_summary, is_current, status
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
        # Phase 8 S3 — ratified version lifecycle state (defaults to DRAFT for
        # legacy rows written before the state column existed).
        "status": str(r.get("status") or DEFAULT_STATUS),
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
        status: str = DEFAULT_STATUS,
    ) -> dict:
        """Insert one version snapshot row and return it.

        ``is_current`` invariant (Phase 8 S1-A): a report has **at most one**
        current version. Creating a current version therefore demotes any
        existing current version(s) for the same report inside the **same
        transaction** as the insert — the established ``conn.transaction()``
        pattern (cf. ``data.imports.activate_batch``, which enforces the
        single-active-batch invariant identically). A successful call leaves
        exactly one current version; a failure rolls back and leaves the
        previous state untouched.

        Creating a non-current version (``is_current=False``) never touches the
        existing current version.

        ``status`` (Phase 8 S3) is the report-version **lifecycle** state and
        defaults to ``DRAFT`` — a freshly generated version is a draft until it
        is put forward for review. It is distinct from the generation status on
        ``report_generation_queue`` and may not take an unratified value.
        """
        validate_status(status)
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                if is_current:
                    await conn.execute(
                        "UPDATE public.report_versions SET is_current = FALSE "
                        "WHERE report_id = $1 AND is_current = TRUE",
                        report_id,
                    )
                row = await conn.fetchrow(
                    f"""
                    INSERT INTO public.report_versions (
                        report_id, version_number, content, file_url, file_name,
                        created_by, notes, change_summary, is_current, status
                    ) VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7, $8, $9, $10)
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
                    status,
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

    async def current_by_reports(self, report_ids: list[str]) -> dict[str, dict]:
        """Return the current version per report — the batch form of
        :meth:`get_current` (Phase 8 S1-B).

        One query for every supplied report id, so the report listing can expose
        ``current_version`` without an N+1 pattern. Reports that have no current
        version are simply **absent** from the result: no value is invented, and
        absence is never converted to version 1.

        The authoritative source is ``is_current`` (not ``MAX(version_number)``).
        ``ORDER BY version_number DESC`` with ``setdefault`` mirrors
        :meth:`get_current`'s ordering, so a legacy report that already carries
        duplicated current rows resolves to the same version in both paths.
        """
        if not report_ids:
            return {}
        rows = await self._fetch_all(
            f"""
            SELECT {_VERSION_COLUMNS} FROM public.report_versions
            WHERE report_id = ANY($1::uuid[]) AND is_current = TRUE
            ORDER BY version_number DESC
            """,
            report_ids,
        )
        current: dict[str, dict] = {}
        for row in rows:
            version = _row_to_version(row)
            current.setdefault(version["report_id"], version)
        return current

    async def get_by_number(
        self, report_id: str, version_number: int
    ) -> Optional[dict]:
        """Return one version of a report by its ``version_number``, or ``None``.

        Phase 8 S3: lifecycle mutations are **version-scoped** — every lifecycle
        endpoint addresses a specific ``version_number`` of a specific report,
        never "whichever version happens to be current" (Reporting Lifecycle
        Spec §23.3 rule 1).
        """
        row = await self._fetch_one(
            f"""
            SELECT {_VERSION_COLUMNS} FROM public.report_versions
            WHERE report_id = $1 AND version_number = $2
            """,
            report_id,
            version_number,
        )
        return _row_to_version(row) if row is not None else None

    async def set_status(
        self,
        report_id: str,
        version_id: str,
        *,
        expected_status: str,
        new_status: str,
    ) -> Optional[dict]:
        """Atomically move one version from ``expected_status`` to ``new_status``.

        Phase 8 S3 state guard (Reporting Lifecycle Spec §26.1): the ``UPDATE``
        carries the expected current state in its ``WHERE`` clause, so a
        concurrent transition (or a stale caller) matches **zero** rows and
        returns ``None`` — the API surfaces a ``409`` rather than clobbering a
        state it did not observe. Row identity is never rewritten, so an
        approval stays bound to its exact version.

        Returns the updated version, or ``None`` when the guard did not match.
        """
        validate_status(new_status)
        validate_status(expected_status)
        row = await self._fetch_one(
            f"""
            UPDATE public.report_versions
            SET status = $3
            WHERE id = $1 AND report_id = $2 AND status = $4
            RETURNING {_VERSION_COLUMNS}
            """,
            version_id,
            report_id,
            new_status,
            expected_status,
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
