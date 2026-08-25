"""Review queue repository (V3 legacy-capability reimplementation).

Persistence for the RC2 ``manual_review_queue`` table — the internal review /
assignment / SLA workflow record.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.operations import ReviewItem

_REVIEW_COLUMNS = (
    "id, organization_id, customer_document_id, file_name, file_url, file_type, data_type, "
    "status, priority, priority_score, entity_id, assigned_to, assigned_by, batch_id, "
    "customer_notes, staff_notes, auto_extraction_result, manual_extraction_result, "
    "sla_deadline, sla_breached, escalation_level, created_at, started_at, "
    "completed_at, review_time_seconds"
)


def _uid(value: Any) -> Optional[str]:
    """Coerce a DB ``uuid`` column to its canonical string form."""
    if value is None:
        return None
    return str(value)


def _row_to_review(row: Any) -> ReviewItem:
    r = dict(row)
    return ReviewItem(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        file_id=_uid(r.get("customer_document_id")),
        file_name=str(r["file_name"]),
        file_url=r.get("file_url"),
        file_type=r.get("file_type"),
        data_type=r.get("data_type"),
        status=str(r["status"]),
        priority=int(r.get("priority") or 0),
        priority_score=float(r.get("priority_score") or 0.0),
        entity_id=_uid(r.get("entity_id")),
        assigned_to=_uid(r.get("assigned_to")),
        assigned_by=_uid(r.get("assigned_by")),
        batch_id=_uid(r.get("batch_id")),
        customer_notes=r.get("customer_notes"),
        staff_notes=r.get("staff_notes"),
        auto_extraction_result=loads_jsonb(r.get("auto_extraction_result")),
        manual_extraction_result=loads_jsonb(r.get("manual_extraction_result")),
        sla_deadline=r.get("sla_deadline"),
        sla_breached=bool(r.get("sla_breached", False)),
        escalation_level=int(r.get("escalation_level") or 0),
        created_at=r.get("created_at"),
        started_at=r.get("started_at"),
        completed_at=r.get("completed_at"),
        review_time_seconds=r.get("review_time_seconds"),
    )


class ReviewQueueRepository(AbstractRepository[ReviewItem]):
    """CRUD and lifecycle for manual review queue items."""

    async def create_item(
        self,
        org_id: str,
        file_name: str,
        status: str,
        file_id: Optional[str] = None,
        file_url: Optional[str] = None,
        file_type: Optional[str] = None,
        data_type: Optional[str] = None,
        priority: int = 1,
        batch_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        auto_extraction_result: Optional[dict] = None,
        customer_notes: Optional[str] = None,
    ) -> ReviewItem:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.manual_review_queue (
                organization_id, customer_document_id, file_name, file_url, file_type,
                data_type, status, priority, priority_score, batch_id, entity_id,
                customer_notes, auto_extraction_result, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8, $9, $10, $11, $12, NOW())
            RETURNING {_REVIEW_COLUMNS}
            """,
            org_id,
            file_id,
            file_name,
            file_url,
            file_type,
            data_type,
            status,
            priority,
            batch_id,
            entity_id,
            customer_notes,
            dumps_jsonb(auto_extraction_result or {}),
        )
        if row is None:
            raise RuntimeError("manual_review_queue insert returned no row")
        return _row_to_review(row)

    async def get(self, review_id: str) -> Optional[ReviewItem]:
        row = await self._fetch_one(
            f"SELECT {_REVIEW_COLUMNS} FROM public.manual_review_queue WHERE id = $1",
            review_id,
        )
        return _row_to_review(row) if row is not None else None

    async def list_items(
        self,
        org_id: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReviewItem]:
        query = "SELECT %s FROM public.manual_review_queue WHERE 1=1" % _REVIEW_COLUMNS
        args: list[Any] = []
        if org_id is not None:
            args.append(org_id)
            query += f" AND organization_id = ${len(args)}"
        if status is not None:
            args.append(status)
            query += f" AND status = ${len(args)}"
        if assigned_to is not None:
            args.append(assigned_to)
            query += f" AND assigned_to = ${len(args)}"
        query += " ORDER BY priority DESC, created_at"
        query += f" LIMIT {int(limit)} OFFSET {int(offset)}"
        rows = await self._fetch_all(query, *args)
        return [_row_to_review(r) for r in rows]

    async def assign(
        self,
        review_id: str,
        assigned_to: str,
        assigned_by: str,
        sla_deadline: Optional[str] = None,
    ) -> Optional[ReviewItem]:
        row = await self._fetch_one(
            f"""
            UPDATE public.manual_review_queue
            SET assigned_to = $2, assigned_by = $3, status = 'assigned',
                started_at = COALESCE(started_at, NOW()),
                sla_deadline = COALESCE($4, sla_deadline)
            WHERE id = $1
            RETURNING {_REVIEW_COLUMNS}
            """,
            review_id,
            assigned_to,
            assigned_by,
            sla_deadline,
        )
        return _row_to_review(row) if row is not None else None

    async def complete(
        self,
        review_id: str,
        manual_extraction_result: dict,
        review_time_seconds: int,
    ) -> Optional[ReviewItem]:
        row = await self._fetch_one(
            f"""
            UPDATE public.manual_review_queue
            SET status = 'completed', manual_extraction_result = $2,
                review_time_seconds = $3, completed_at = NOW()
            WHERE id = $1
            RETURNING {_REVIEW_COLUMNS}
            """,
            review_id,
            dumps_jsonb(manual_extraction_result),
            review_time_seconds,
        )
        return _row_to_review(row) if row is not None else None

    async def update_status(self, review_id: str, status: str) -> Optional[ReviewItem]:
        row = await self._fetch_one(
            f"""
            UPDATE public.manual_review_queue SET status = $2 WHERE id = $1
            RETURNING {_REVIEW_COLUMNS}
            """,
            review_id,
            status,
        )
        return _row_to_review(row) if row is not None else None

    async def save(self, entity: ReviewItem) -> ReviewItem:
        return entity

    async def delete(self, id: str) -> None:
        return None
