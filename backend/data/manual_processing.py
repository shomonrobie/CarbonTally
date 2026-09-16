"""FIN-06 — Manual Processing governance persistence.

Only explicit governance rows live in ``public.manual_processing_grants``; the
resolver in :mod:`domain.manual_processing` decides the effective value by
most-specific-wins precedence and fails closed when nothing matches.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository
from domain.manual_processing import (
    EffectiveManualProcessing,
    ManualProcessingGrant,
    OrgContext,
    resolve_effective,
)

_COLUMNS = "id, scope_type, scope_id, enabled, reason, set_by, set_at, updated_at"


def _row_to_grant(row: Any) -> ManualProcessingGrant:
    return ManualProcessingGrant(
        scope_type=str(row["scope_type"]),
        scope_id=str(row["scope_id"]),
        enabled=bool(row["enabled"]),
        reason=row.get("reason"),
        set_by=str(row["set_by"]) if row.get("set_by") else None,
        set_at=row.get("set_at"),
    )


class ManualProcessingRepository(AbstractRepository[ManualProcessingGrant]):
    """Governance-plane persistence + scope expansion (service role only)."""

    async def get(self, id: str) -> Optional[ManualProcessingGrant]:
        row = await self._fetch_one(
            f"SELECT {_COLUMNS} FROM public.manual_processing_grants WHERE id = $1",
            id,
        )
        return _row_to_grant(row) if row is not None else None

    async def save(self, entity: ManualProcessingGrant) -> ManualProcessingGrant:
        return await self.set_grant(
            scope_type=entity.scope_type,
            scope_id=entity.scope_id,
            enabled=entity.enabled,
            reason=entity.reason,
            actor_id=str(entity.set_by or ""),
        )

    async def delete(self, id: str) -> None:
        await self._execute(
            "DELETE FROM public.manual_processing_grants WHERE id = $1", id
        )

    # -- governance reads ---------------------------------------------------
    async def list_grants(
        self, *, scope_type: Optional[str] = None
    ) -> list[ManualProcessingGrant]:
        if scope_type is None:
            rows = await self._fetch_all(
                f"SELECT {_COLUMNS} FROM public.manual_processing_grants "
                "ORDER BY scope_type, scope_id"
            )
        else:
            rows = await self._fetch_all(
                f"SELECT {_COLUMNS} FROM public.manual_processing_grants "
                "WHERE scope_type = $1 ORDER BY scope_id",
                scope_type,
            )
        return [_row_to_grant(r) for r in rows]

    async def grants_for_context(
        self, context: OrgContext
    ) -> list[ManualProcessingGrant]:
        """The governance rows relevant to one organization context."""
        scope_ids = [
            value
            for value in (
                context.consultant_client_id,
                context.consultant_firm_id,
                context.organization_id,
            )
            if value
        ]
        if not scope_ids:
            return []
        rows = await self._fetch_all(
            f"SELECT {_COLUMNS} FROM public.manual_processing_grants "
            "WHERE scope_id = ANY($1::uuid[])",
            scope_ids,
        )
        return [_row_to_grant(r) for r in rows]

    async def effective_for_context(
        self, context: OrgContext
    ) -> EffectiveManualProcessing:
        return resolve_effective(await self.grants_for_context(context), context)

    # -- governance writes (CarbonTally Admin only, behind the API gate) -----
    async def set_grant(
        self,
        *,
        scope_type: str,
        scope_id: str,
        enabled: bool,
        reason: Optional[str],
        actor_id: str,
    ) -> ManualProcessingGrant:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.manual_processing_grants (
                scope_type, scope_id, enabled, reason, set_by, set_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            ON CONFLICT (scope_type, scope_id) DO UPDATE
                SET enabled = EXCLUDED.enabled,
                    reason = EXCLUDED.reason,
                    set_by = EXCLUDED.set_by,
                    set_at = NOW(),
                    updated_at = NOW()
            RETURNING {_COLUMNS}
            """,
            scope_type,
            scope_id,
            bool(enabled),
            reason,
            actor_id,
        )
        if row is None:
            raise RuntimeError("manual_processing_grants upsert returned no row")
        return _row_to_grant(row)

    async def delete_grant(self, *, scope_type: str, scope_id: str) -> bool:
        row = await self._fetch_one(
            "DELETE FROM public.manual_processing_grants "
            "WHERE scope_type = $1 AND scope_id = $2 RETURNING id",
            scope_type,
            scope_id,
        )
        return row is not None

    # -- scope expansion (queued-work invalidation) ------------------------
    async def organizations_in_scope(
        self, *, scope_type: str, scope_id: str
    ) -> list[str]:
        """Organisations covered by one governance scope (REAL relationship ids)."""
        if scope_type == "organization":
            return [scope_id]
        if scope_type == "consultant_client":
            rows = await self._fetch_all(
                "SELECT organization_id FROM public.consultant_clients WHERE id = $1",
                scope_id,
            )
        elif scope_type == "consultant_firm":
            rows = await self._fetch_all(
                "SELECT organization_id FROM public.consultant_clients "
                "WHERE consultant_id = $1 AND status = 'active'",
                scope_id,
            )
        else:
            raise ValueError(f"unknown scope_type: {scope_type!r}")
        return [str(r["organization_id"]) for r in rows if r.get("organization_id")]

    async def queued_batch_ids_for_organizations(
        self, organization_ids: list[str]
    ) -> list[str]:
        """Manual-extraction batches that are QUEUED (status ``open``).

        Running batches (``in_progress``) are deliberately excluded: the PO
        decision allows an actively running job to finish safely.
        """
        if not organization_ids:
            return []
        rows = await self._fetch_all(
            "SELECT id FROM public.manual_extraction_batches "
            "WHERE organization_id = ANY($1::uuid[]) AND status = 'open' "
            "ORDER BY created_at",
            organization_ids,
        )
        return [str(r["id"]) for r in rows]
