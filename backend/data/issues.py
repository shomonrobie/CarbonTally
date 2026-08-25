"""Issues repository (V3, ADR-V3-009 — DECIDED, Option B).

Persistence for the V3M-5 ``issues`` table. The repository always filters by
the requested scope in code (service-role pool): organisation-facing rows carry
``entity_id IS NULL``; processing-entity rows carry ``entity_id``; CarbonTally
internal rows may carry neither.

Lifecycle transitions and transition authority are enforced by the service/API
layer; the DB enforces the vocabulary (V3M-5 CHECKs) and integrity.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from data.base import AbstractRepository
from domain.issue import Issue

_ISSUE_COLUMNS = """
    id, issue_type, severity, priority, status, title, description,
    organization_id, entity_id, work_item_id, document_id, batch_id,
    manual_extraction_batch_id, conversation_id, assignee_id, escalation_level,
    sla_deadline, sla_breached, reopened_at, created_at, updated_at,
    created_by, updated_by
"""


def _row_to_issue(row: Any) -> Issue:
    r = dict(row)
    return Issue(
        id=str(r["id"]),
        issue_type=str(r["issue_type"]),
        severity=str(r["severity"]),
        priority=int(r["priority"]),
        status=str(r["status"]),
        title=str(r["title"]),
        description=str(r["description"]) if r.get("description") else None,
        organization_id=str(r["organization_id"]) if r.get("organization_id") else None,
        entity_id=str(r["entity_id"]) if r.get("entity_id") else None,
        work_item_id=str(r["work_item_id"]) if r.get("work_item_id") else None,
        document_id=str(r["document_id"]) if r.get("document_id") else None,
        batch_id=str(r["batch_id"]) if r.get("batch_id") else None,
        manual_extraction_batch_id=(
            str(r["manual_extraction_batch_id"])
            if r.get("manual_extraction_batch_id")
            else None
        ),
        conversation_id=str(r["conversation_id"]) if r.get("conversation_id") else None,
        assignee_id=str(r["assignee_id"]) if r.get("assignee_id") else None,
        escalation_level=int(r["escalation_level"]) if r.get("escalation_level") is not None else 0,
        sla_deadline=r.get("sla_deadline"),
        sla_breached=r.get("sla_breached"),
        reopened_at=r.get("reopened_at"),
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
        created_by=str(r["created_by"]) if r.get("created_by") else None,
        updated_by=str(r["updated_by"]) if r.get("updated_by") else None,
    )


class IssuesRepository(AbstractRepository[Issue]):
    """Issue persistence with org/entity/CarbonTally-internal scoped queries."""

    async def get(self, id: str) -> Optional[Issue]:
        """Return the issue with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_ISSUE_COLUMNS} FROM public.issues WHERE id = $1", id
        )
        return _row_to_issue(row) if row is not None else None

    async def list_for_org(
        self, org_id: str, limit: int = 100, offset: int = 0
    ) -> list[Issue]:
        """Return customer-facing issues for ``org_id`` (``entity_id IS NULL`` —
        entity-scoped issues are never customer-visible, V3M-5 storey).

        ``limit``/``offset`` bound the page (the API layer clamps ``limit`` to
        1..500); ordering is always ``created_at DESC, id`` for stable pagination.
        """
        rows = await self._fetch_all(
            f"SELECT {_ISSUE_COLUMNS} FROM public.issues "
            "WHERE organization_id = $1 AND entity_id IS NULL "
            "ORDER BY created_at DESC, id "
            f"LIMIT {int(limit)} OFFSET {int(offset)}",
            org_id,
        )
        return [_row_to_issue(r) for r in rows]

    async def count_for_org(self, org_id: str) -> int:
        """Total customer-facing issues for ``org_id`` (pagination totals)."""
        row = await self._fetch_one(
            "SELECT COUNT(*) FROM public.issues "
            "WHERE organization_id = $1 AND entity_id IS NULL",
            org_id,
        )
        return int(row[0]) if row is not None else 0

    async def list_for_entity(self, entity_id: str) -> list[Issue]:
        """Return issues scoped to one processing entity (internal surface)."""
        rows = await self._fetch_all(
            f"SELECT {_ISSUE_COLUMNS} FROM public.issues "
            "WHERE entity_id = $1 ORDER BY created_at DESC, id",
            entity_id,
        )
        return [_row_to_issue(r) for r in rows]

    async def list_open(self, *, organization_id: Optional[str] = None) -> list[Issue]:
        """Return open issues, optionally org-scoped (CarbonTally internal)."""
        if organization_id is not None:
            rows = await self._fetch_all(
                f"SELECT {_ISSUE_COLUMNS} FROM public.issues "
                "WHERE status IN ('open','in_progress','on_hold','escalated') "
                "AND organization_id = $1 ORDER BY priority DESC, created_at, id",
                organization_id,
            )
        else:
            rows = await self._fetch_all(
                f"SELECT {_ISSUE_COLUMNS} FROM public.issues "
                "WHERE status IN ('open','in_progress','on_hold','escalated') "
                "ORDER BY priority DESC, created_at, id"
            )
        return [_row_to_issue(r) for r in rows]

    async def list_for_work_item(self, work_item_id: str) -> list[Issue]:
        """Return every issue linked to a processing work item (pipeline order)."""
        rows = await self._fetch_all(
            f"SELECT {_ISSUE_COLUMNS} FROM public.issues "
            "WHERE work_item_id = $1 ORDER BY created_at DESC, id",
            work_item_id,
        )
        return [_row_to_issue(r) for r in rows]

    async def list_for_batch(self, batch_id: str) -> list[Issue]:
        """Return every issue linked to a processing batch."""
        rows = await self._fetch_all(
            f"SELECT {_ISSUE_COLUMNS} FROM public.issues "
            "WHERE batch_id = $1 ORDER BY created_at DESC, id",
            batch_id,
        )
        return [_row_to_issue(r) for r in rows]

    async def save(self, entity: Issue) -> Issue:
        """Insert or update an issue (status/assignee/priority/severity etc.)."""
        now = datetime.now(timezone.utc)
        row = await self._fetch_one(
            f"""
            INSERT INTO public.issues (
                id, issue_type, severity, priority, status, title, description,
                organization_id, entity_id, work_item_id, document_id, batch_id,
                manual_extraction_batch_id, conversation_id, assignee_id,
                escalation_level, sla_deadline, sla_breached, reopened_at,
                created_at, updated_at, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                      $14, $15, $16, $17, $18, $19, $20, $21, $22, $23)
            ON CONFLICT (id)
            DO UPDATE SET
                issue_type = EXCLUDED.issue_type,
                severity = EXCLUDED.severity,
                priority = EXCLUDED.priority,
                status = EXCLUDED.status,
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                assignee_id = EXCLUDED.assignee_id,
                escalation_level = EXCLUDED.escalation_level,
                sla_deadline = EXCLUDED.sla_deadline,
                sla_breached = EXCLUDED.sla_breached,
                reopened_at = EXCLUDED.reopened_at,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            RETURNING {_ISSUE_COLUMNS}
            """,
            entity.id,
            entity.issue_type,
            entity.severity,
            entity.priority,
            entity.status,
            entity.title,
            entity.description,
            entity.organization_id,
            entity.entity_id,
            entity.work_item_id,
            entity.document_id,
            entity.batch_id,
            entity.manual_extraction_batch_id,
            entity.conversation_id,
            entity.assignee_id,
            entity.escalation_level,
            entity.sla_deadline,
            entity.sla_breached,
            entity.reopened_at,
            entity.created_at or now,
            now,
            entity.created_by,
            entity.updated_by,
        )
        if row is None:
            raise RuntimeError("issue upsert returned no row")
        return _row_to_issue(row)

    async def update_status(
        self,
        id: str,
        status: str,
        *,
        reopened_at: Optional[datetime] = None,
        updated_by: Optional[str] = None,
    ) -> Issue:
        """Transition an issue's status (authority enforced by the service)."""
        row = await self._fetch_one(
            f"""
            UPDATE public.issues
            SET status = $2, updated_at = NOW(), updated_by = $3,
                reopened_at = COALESCE($4, reopened_at)
            WHERE id = $1
            RETURNING {_ISSUE_COLUMNS}
            """,
            id,
            status,
            updated_by,
            reopened_at,
        )
        if row is None:
            raise RuntimeError(f"issue {id!r} does not exist")
        return _row_to_issue(row)

    async def delete(self, id: str) -> None:
        """Issues are never hard-deleted (V3M-5 has no DELETE policy; soft
        lifecycle via status)."""
        raise NotImplementedError(
            "issues are never hard-deleted; use update_status"
        )

