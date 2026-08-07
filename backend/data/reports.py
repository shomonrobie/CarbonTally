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


class ReportsRepository(AbstractRepository[GeneratedReport]):
    """CRUD and lifecycle for generated reports."""

    async def create_generation_request(
        self,
        org_id: str,
        report_type: str,
        year: int,
        template_id: Optional[str],
    ) -> GeneratedReport:
        """Create a pending report-generation request."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.report_generation_queue (
                organization_id, report_type, reporting_year, template_id,
                status, created_at, updated_at
            ) VALUES ($1, $2, $3, $4::uuid, 'pending', NOW(), NOW())
            RETURNING {_REPORT_COLUMNS}
            """,
            org_id,
            report_type,
            year,
            template_id,
        )
        if row is None:
            raise RuntimeError("report request insert returned no row")
        return _row_to_report(row)

    async def complete_generation(
        self,
        report_id: str,
        storage_url: str,
        file_size: int,
        page_count: int,
    ) -> GeneratedReport:
        """Mark the report as completed with its stored artefact details."""
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
            dumps_jsonb({"page_count": page_count}),
        )
        if row is None:
            raise RuntimeError(f"report {report_id!r} does not exist")
        return _row_to_report(row)

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

