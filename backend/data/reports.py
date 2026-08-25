"""Reports repository (Backend v2.1 §10).

Persistence for the ``GeneratedReport`` aggregate. The RC2 schema has no
``generated_reports`` table; the repository maps to the existing
``report_generation_queue`` table, persisting ``page_count`` inside the
``generated_content`` JSONB column (the table has no dedicated column for it).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, cast

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.report import GeneratedReport

_REPORT_COLUMNS = """
    id, organization_id, report_type, reporting_year, template_id, status,
    final_report_url, final_report_size_bytes, generated_content,
    completed_at, created_at
"""

#: Full queue-row column list (the V3 reporting dashboard surface). Mirrors
#: ``report_generation_queue`` — report lifecycle, provenance and artefact state.
_REPORT_FULL_COLUMNS = """
    id, organization_id, user_id, template_id, report_type, reporting_year,
    report_name, data_sources, status, progress_percentage, current_step,
    generated_content, user_edits, final_report_url, final_report_file_name,
    final_report_size_bytes, created_at, created_by, started_at, completed_at,
    updated_at, updated_by, metadata, error_log
"""


def _row_to_report(row: Any) -> GeneratedReport:
    r = dict(row)
    content = loads_jsonb(r.get("generated_content")) or {}
    page_count = int(content.get("page_count") or 0)
    generated_at = r.get("completed_at") or r.get("created_at")
    if generated_at is None:
        raise RuntimeError("report row has neither completed_at nor created_at")
    return GeneratedReport(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        report_type=str(r["report_type"]),
        reporting_year=int(r["reporting_year"]),
        storage_url=str(r.get("final_report_url") or ""),
        file_size_bytes=int(r.get("final_report_size_bytes") or 0),
        generated_at=cast(datetime, generated_at),
        page_count=page_count,
    )


def _page_count_jsonb(report: GeneratedReport) -> str:
    """JSONB payload carrying the non-column ``page_count`` field."""
    return dumps_jsonb({"page_count": report.page_count})


def _iso(value: Any) -> Optional[str]:
    """ISO-8601 for datetime/timestamp columns (or ``None``)."""
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _row_to_report_full(row: Any) -> dict:
    """Map one ``report_generation_queue`` row to the dashboard-facing dict.

    JSONB columns are decoded; datetimes are ISO-8601 so the payload is
    directly JSON-serialisable by the API layer. Status is the authoritative
    queue status (``pending`` / ``generating`` / ``completed`` / ``failed``);
    no status is invented here.
    """
    r = dict(row)
    generated_content = loads_jsonb(r.get("generated_content")) or {}
    page_count = int(generated_content.get("page_count") or 0)
    content = generated_content.get("content")
    return {
        "id": str(r["id"]),
        "organization_id": str(r["organization_id"]),
        "user_id": str(r["user_id"]) if r.get("user_id") else None,
        "template_id": str(r["template_id"]) if r.get("template_id") else None,
        "report_type": str(r["report_type"]),
        "reporting_year": int(r["reporting_year"]),
        "report_name": str(r["report_name"]) if r.get("report_name") else None,
        "status": str(r.get("status") or "pending"),
        "progress_percentage": (
            int(r["progress_percentage"]) if r.get("progress_percentage") is not None else None
        ),
        "current_step": r.get("current_step"),
        "generated_content": content,
        "page_count": page_count,
        "final_report_url": str(r["final_report_url"]) if r.get("final_report_url") else "",
        "final_report_file_name": r.get("final_report_file_name"),
        "final_report_size_bytes": (
            int(r["final_report_size_bytes"])
            if r.get("final_report_size_bytes") is not None
            else 0
        ),
        "created_at": _iso(r.get("created_at")),
        "created_by": str(r["created_by"]) if r.get("created_by") else None,
        "started_at": _iso(r.get("started_at")),
        "completed_at": _iso(r.get("completed_at")),
        "updated_at": _iso(r.get("updated_at")),
        "updated_by": str(r["updated_by"]) if r.get("updated_by") else None,
        "error_log": r.get("error_log"),
        "metadata": loads_jsonb(r.get("metadata")) if r.get("metadata") is not None else {},
    }


class ReportsRepository(AbstractRepository[GeneratedReport]):
    """CRUD and lifecycle for generated reports."""

    async def create_generation_request(
        self,
        org_id: str,
        report_type: str,
        year: int,
        template_id: Optional[str],
        created_by: Optional[str] = None,
        report_name: Optional[str] = None,
    ) -> GeneratedReport:
        """Create a pending report-generation request.

        ``created_by`` and ``report_name`` are optional (backward compatible);
        when supplied they are persisted so the reporting dashboard can show the
        requester and a human-readable name.
        """
        row = await self._fetch_one(
            f"""
            INSERT INTO public.report_generation_queue (
                organization_id, report_type, reporting_year, template_id,
                status, created_at, created_by, report_name, updated_at
            ) VALUES ($1, $2, $3, $4::uuid, 'pending', NOW(), $5, $6, NOW())
            RETURNING {_REPORT_COLUMNS}
            """,
            org_id,
            report_type,
            year,
            template_id,
            created_by,
            report_name,
        )
        if row is None:
            raise RuntimeError("report request insert returned no row")
        return _row_to_report(row)

    async def mark_generating(
        self, report_id: str, user_id: Optional[str] = None
    ) -> Optional[dict]:
        """Move a report into the ``generating`` state (queue lifecycle).

        Persists the transient in-flight state on the existing row (started_at +
        progress). Returns the full row, or ``None`` when the report does not
        exist.
        """
        return await self._update_lifecycle(
            report_id,
            status="generating",
            extra_sql="started_at = NOW()",
            user_id=user_id,
        )

    async def mark_failed(
        self, report_id: str, error_log: str, user_id: Optional[str] = None
    ) -> Optional[dict]:
        """Mark a report generation attempt as failed with the real error.

        The error text is the engine's actual failure (never a fabricated
        message); the client-facing response is produced by the API layer.
        """
        row = await self._fetch_one(
            f"""
            UPDATE public.report_generation_queue
            SET status = 'failed',
                error_log = $2,
                updated_at = NOW(),
                updated_by = $3
            WHERE id = $1
            RETURNING {_REPORT_FULL_COLUMNS}
            """,
            report_id,
            error_log,
            user_id,
        )
        return _row_to_report_full(row) if row is not None else None

    async def complete_generation(
        self,
        report_id: str,
        storage_url: str,
        file_size: int,
        page_count: int,
        content: Optional[dict[str, Any]] = None,
    ) -> GeneratedReport:
        """Mark the report as completed with its stored artefact details.

        ``content`` (Phase 9C) is merged into the ``generated_content`` JSONB
        alongside ``page_count`` so the structured report content is persisted
        for later rendering/API consumption. When ``content`` is ``None`` the
        behaviour is unchanged (page_count only).
        """
        generated: dict[str, Any] = {"page_count": page_count}
        if content is not None:
            generated["content"] = content
        row = await self._fetch_one(
            f"""
            UPDATE public.report_generation_queue
            SET final_report_url = $2,
                final_report_size_bytes = $3,
                generated_content = $4::jsonb,
                status = 'completed',
                completed_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
            RETURNING {_REPORT_COLUMNS}
            """,
            report_id,
            storage_url,
            file_size,
            dumps_jsonb(generated),
        )
        if row is None:
            raise RuntimeError(f"report {report_id!r} does not exist")
        return _row_to_report(row)

    async def _update_lifecycle(
        self,
        report_id: str,
        *,
        status: str,
        extra_sql: str,
        user_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Shared lifecycle transition helper (single UPDATE, returns full row)."""
        row = await self._fetch_one(
            f"""
            UPDATE public.report_generation_queue
            SET status = $2,
                {extra_sql},
                updated_at = NOW(),
                updated_by = $3
            WHERE id = $1
            RETURNING {_REPORT_FULL_COLUMNS}
            """,
            report_id,
            status,
            user_id,
        )
        return _row_to_report_full(row) if row is not None else None

    async def get_full(self, id: str) -> Optional[dict]:
        """Return the full dashboard-facing row for one report."""
        row = await self._fetch_one(
            f"""
            SELECT {_REPORT_FULL_COLUMNS} FROM public.report_generation_queue
            WHERE id = $1
            """,
            id,
        )
        return _row_to_report_full(row) if row is not None else None

    async def list_full(
        self,
        org_id: str,
        *,
        status: Optional[str] = None,
        report_type: Optional[str] = None,
        reporting_year: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Return full report rows for an organisation (dashboard surface).

        Filters are exact matches on the persisted queue columns; no counts or
        statuses are fabricated. Ordered newest-first.
        """
        query = (
            f"SELECT {_REPORT_FULL_COLUMNS} FROM public.report_generation_queue "
            "WHERE organization_id = $1"
        )
        args: list[Any] = [org_id]
        if status is not None:
            args.append(status)
            query += f" AND status = ${len(args)}"
        if report_type is not None:
            args.append(report_type)
            query += f" AND report_type = ${len(args)}"
        if reporting_year is not None:
            args.append(reporting_year)
            query += f" AND reporting_year = ${len(args)}"
        query += " ORDER BY created_at DESC, id"
        query += f" LIMIT {int(limit)} OFFSET {int(offset)}"
        rows = await self._fetch_all(query, *args)
        return [_row_to_report_full(r) for r in rows]

    async def count_by_status(self, org_id: str) -> dict[str, int]:
        """Count report rows grouped by the real persisted status."""
        rows = await self._fetch_all(
            """
            SELECT status, COUNT(*)::int AS n
            FROM public.report_generation_queue
            WHERE organization_id = $1
            GROUP BY status
            """,
            org_id,
        )
        counts = {str(r["status"] or "pending"): int(r["n"]) for r in rows}
        for status in ("pending", "generating", "completed", "failed"):
            counts.setdefault(status, 0)
        return counts

    async def get_by_org(self, org_id: str) -> list[GeneratedReport]:
        """Return every report belonging to the organisation."""
        rows = await self._fetch_all(
            f"""
            SELECT {_REPORT_COLUMNS} FROM public.report_generation_queue
            WHERE organization_id = $1
            ORDER BY created_at DESC, id
            """,
            org_id,
        )
        return [_row_to_report(r) for r in rows]

    async def get(self, id: str) -> Optional[GeneratedReport]:
        """Return the report with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"""
            SELECT {_REPORT_COLUMNS} FROM public.report_generation_queue
            WHERE id = $1
            """,
            id,
        )
        return _row_to_report(row) if row is not None else None

    async def save(self, entity: GeneratedReport) -> GeneratedReport:
        """Upsert a generated report by id and return the stored state."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.report_generation_queue (
                id, organization_id, report_type, reporting_year,
                final_report_url, final_report_size_bytes, generated_content,
                status, completed_at, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7::jsonb,
                CASE WHEN $5 = '' THEN 'pending' ELSE 'completed' END,
                CASE WHEN $5 = '' THEN NULL ELSE NOW() END,
                NOW(), NOW()
            )
            ON CONFLICT (id)
            DO UPDATE SET
                report_type = EXCLUDED.report_type,
                reporting_year = EXCLUDED.reporting_year,
                final_report_url = EXCLUDED.final_report_url,
                final_report_size_bytes = EXCLUDED.final_report_size_bytes,
                generated_content = EXCLUDED.generated_content,
                status = EXCLUDED.status,
                completed_at = EXCLUDED.completed_at,
                updated_at = NOW()
            RETURNING {_REPORT_COLUMNS}
            """,
            entity.id,
            entity.organization_id,
            entity.report_type,
            entity.reporting_year,
            entity.storage_url,
            entity.file_size_bytes,
            _page_count_jsonb(entity),
        )
        if row is None:
            raise RuntimeError("report upsert returned no row")
        return _row_to_report(row)

    async def delete(self, id: str) -> None:
        """Delete a report record."""
        await self._execute(
            "DELETE FROM public.report_generation_queue WHERE id = $1", id
        )

