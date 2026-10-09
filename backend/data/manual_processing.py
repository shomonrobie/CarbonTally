"""FIN-06 — Manual Processing governance persistence.

Only explicit governance rows live in ``public.manual_processing_grants``; the
resolver in :mod:`domain.manual_processing` decides the effective value by
most-specific-wins precedence and fails closed when nothing matches.
"""
from __future__ import annotations

from typing import Any, Optional

import asyncpg

from data.base import AbstractRepository
from domain.manual_processing import (
    CapacityExceededError,
    ConsultantAllocation,
    DuplicateActiveAllocationError,
    EffectiveManualProcessing,
    ManualProcessingGrant,
    ManualProcessingProcessor,
    OrgContext,
    resolve_effective,
    resolve_processor,
)

_COLUMNS = "id, scope_type, scope_id, enabled, reason, set_by, set_at, updated_at"

_PROCESSOR_COLUMNS = (
    "id, scope_type, scope_id, processing_entity_id, active, reason, set_by, "
    "set_at, updated_at"
)

_ALLOCATION_COLUMNS = (
    "id, consultant_id, consultant_client_id, organization_id, state, reason, "
    "allocated_by, allocated_at, released_by, released_at, updated_at"
)


def _row_to_allocation(row: Any) -> ConsultantAllocation:
    return ConsultantAllocation(
        id=str(row["id"]),
        consultant_id=str(row["consultant_id"]),
        consultant_client_id=str(row["consultant_client_id"]),
        organization_id=str(row["organization_id"]),
        state=str(row["state"]),
        reason=row.get("reason"),
        allocated_by=str(row["allocated_by"]) if row.get("allocated_by") else None,
        allocated_at=row.get("allocated_at"),
        released_by=str(row["released_by"]) if row.get("released_by") else None,
        released_at=row.get("released_at"),
        updated_at=row.get("updated_at"),
    )



def _row_to_processor(row: Any) -> ManualProcessingProcessor:
    return ManualProcessingProcessor(
        scope_type=str(row["scope_type"]),
        scope_id=str(row["scope_id"]),
        processing_entity_id=str(row["processing_entity_id"]),
        active=bool(row["active"]),
        reason=row.get("reason"),
        set_by=str(row["set_by"]) if row.get("set_by") else None,
        set_at=row.get("set_at"),
    )


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

    # -- server-side relationship context (consultant scopes) ----------------
    async def org_context_for_organization(self, organization_id: str) -> OrgContext:
        """Resolve the ACTIVE consultant relationship for one organisation.

        Used by the automatic fallback router, which has no authenticated user
        and therefore must resolve the consultant-client/firm context from the
        database rather than from a request. The same REAL relationship entities
        are used as everywhere else (``consultant_clients.id`` = the client
        grant, ``consultant_clients.consultant_id`` = ``consultant_profiles.id``
        = the firm), so no second tenancy concept is introduced.
        """
        row = await self._fetch_one(
            "SELECT id, consultant_id FROM public.consultant_clients "
            "WHERE organization_id = $1 AND status = 'active' "
            "ORDER BY created_at DESC LIMIT 1",
            organization_id,
        )
        if row is None:
            return OrgContext(organization_id=organization_id)
        return OrgContext(
            organization_id=organization_id,
            consultant_client_id=str(row["id"]) if row.get("id") else None,
            consultant_firm_id=(
                str(row["consultant_id"]) if row.get("consultant_id") else None
            ),
        )

    # -- processor configuration (routing destination) ----------------------
    async def list_processors(
        self, *, scope_type: Optional[str] = None
    ) -> list[ManualProcessingProcessor]:
        """List configured processors (admin control plane)."""
        if scope_type is None:
            rows = await self._fetch_all(
                f"SELECT {_PROCESSOR_COLUMNS} FROM public.manual_processing_processors "
                "ORDER BY scope_type, scope_id"
            )
        else:
            rows = await self._fetch_all(
                f"SELECT {_PROCESSOR_COLUMNS} FROM public.manual_processing_processors "
                "WHERE scope_type = $1 ORDER BY scope_id",
                scope_type,
            )
        return [_row_to_processor(r) for r in rows]

    async def get_processor(
        self, *, scope_type: str, scope_id: str
    ) -> Optional[ManualProcessingProcessor]:
        row = await self._fetch_one(
            f"SELECT {_PROCESSOR_COLUMNS} FROM public.manual_processing_processors "
            "WHERE scope_type = $1 AND scope_id = $2",
            scope_type,
            scope_id,
        )
        return _row_to_processor(row) if row is not None else None

    async def processors_for_context(
        self, context: OrgContext
    ) -> list[ManualProcessingProcessor]:
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
            f"SELECT {_PROCESSOR_COLUMNS} FROM public.manual_processing_processors "
            "WHERE scope_id = ANY($1::uuid[])",
            scope_ids,
        )
        return [_row_to_processor(r) for r in rows]

    async def resolve_processor_for_context(
        self, context: OrgContext
    ) -> Optional[ManualProcessingProcessor]:
        """Most-specific-wins processor for one organisation context."""
        return resolve_processor(await self.processors_for_context(context), context)

    async def set_processor(
        self,
        *,
        scope_type: str,
        scope_id: str,
        processing_entity_id: str,
        active: bool = True,
        reason: Optional[str],
        actor_id: str,
    ) -> ManualProcessingProcessor:
        """Upsert the configured processor for one scope (one row per scope)."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.manual_processing_processors (
                scope_type, scope_id, processing_entity_id, active, reason,
                set_by, set_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
            ON CONFLICT (scope_type, scope_id) DO UPDATE
                SET processing_entity_id = EXCLUDED.processing_entity_id,
                    active = EXCLUDED.active,
                    reason = EXCLUDED.reason,
                    set_by = EXCLUDED.set_by,
                    set_at = NOW(),
                    updated_at = NOW()
            RETURNING {_PROCESSOR_COLUMNS}
            """,
            scope_type,
            scope_id,
            processing_entity_id,
            bool(active),
            reason,
            actor_id,
        )
        if row is None:
            raise RuntimeError("manual_processing_processors upsert returned no row")
        return _row_to_processor(row)

    async def delete_processor(self, *, scope_type: str, scope_id: str) -> bool:
        row = await self._fetch_one(
            "DELETE FROM public.manual_processing_processors "
            "WHERE scope_type = $1 AND scope_id = $2 RETURNING id",
            scope_type,
            scope_id,
        )
        return row is not None

    # -- consultant-sponsored coverage (CT-MP-SUB-003) ----------------------
    async def active_client_grants(self, organization_id: str) -> list[dict]:
        """ACTIVE consultant relationships targeting one organisation.

        This is the ELIGIBILITY anchor for consultant-sponsored coverage: the
        existing ``consultant_clients`` relationship, resolved server-side.
        """
        rows = await self._fetch_all(
            "SELECT id, consultant_id FROM public.consultant_clients "
            "WHERE organization_id = $1 AND status = 'active' "
            "ORDER BY created_at DESC",
            organization_id,
        )
        return [
            {"id": str(r["id"]), "consultant_id": str(r["consultant_id"])}
            for r in rows
            if r.get("consultant_id")
        ]

    async def firm_organization_id(self, firm_id: str) -> Optional[str]:
        """The consultant firm's OWN organisation (``consultant_profiles.organization_id``).

        The firm's organisation subscription is the commercial source of the
        sponsored coverage. A NULL linkage means NO covered subscription — fail
        closed (no parallel consultant-user billing is invented).
        """
        row = await self._fetch_one(
            "SELECT organization_id FROM public.consultant_profiles WHERE id = $1",
            firm_id,
        )
        if row is None:
            return None
        value = row.get("organization_id")
        return str(value) if value else None

    async def eligible_clients(self, firm_id: str) -> list[dict]:
        """ACTIVE client organisations of one firm (the eligible population)."""
        rows = await self._fetch_all(
            "SELECT id, organization_id FROM public.consultant_clients "
            "WHERE consultant_id = $1 AND status = 'active' ORDER BY created_at",
            firm_id,
        )
        return [
            {"id": str(r["id"]), "organization_id": str(r["organization_id"])}
            for r in rows
        ]

    async def list_allocations(
        self,
        *,
        consultant_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        state: Optional[str] = None,
    ) -> list[ConsultantAllocation]:
        """List allocation rows (history preserved; never deleted)."""
        clauses: list[str] = []
        params: list[Any] = []
        if consultant_id is not None:
            params.append(consultant_id)
            clauses.append(f"consultant_id = ${len(params)}")
        if organization_id is not None:
            params.append(organization_id)
            clauses.append(f"organization_id = ${len(params)}")
        if state is not None:
            params.append(state)
            clauses.append(f"state = ${len(params)}")
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = await self._fetch_all(
            f"SELECT {_ALLOCATION_COLUMNS} FROM public.consultant_mp_allocations"
            f"{where} ORDER BY allocated_at DESC",
            *params,
        )
        return [_row_to_allocation(r) for r in rows]

    async def get_active_allocation(
        self, *, consultant_id: str, organization_id: str
    ) -> Optional[ConsultantAllocation]:
        row = await self._fetch_one(
            f"SELECT {_ALLOCATION_COLUMNS} FROM public.consultant_mp_allocations "
            "WHERE consultant_id = $1 AND organization_id = $2 AND state = 'active' "
            "LIMIT 1",
            consultant_id,
            organization_id,
        )
        return _row_to_allocation(row) if row is not None else None

    async def count_active_allocations(self, consultant_id: str) -> int:
        row = await self._fetch_one(
            "SELECT count(*) AS n FROM public.consultant_mp_allocations "
            "WHERE consultant_id = $1 AND state = 'active'",
            consultant_id,
        )
        return int(row["n"]) if row is not None else 0

    async def create_allocation(
        self,
        *,
        consultant_id: str,
        consultant_client_id: str,
        organization_id: str,
        reason: Optional[str],
        actor_id: str,
        capacity: Optional[int] = None,
    ) -> ConsultantAllocation:
        """Create one ACTIVE allocation, atomically and race-safely (F-9).

        Duplicate protection and capacity enforcement are performed INSIDE ONE
        transaction on ONE connection, serialised by a per-firm advisory
        transaction lock, so concurrent requests cannot both observe spare
        capacity and over-allocate:

        * a per-firm ``pg_advisory_xact_lock`` serialises allocation writes for
          the firm (concurrent attempts run one at a time; the loser re-reads
          the committed count and is refused deterministically rather than
          over-allocating);
        * when ``capacity`` is supplied, the active count is re-read under the
          lock and ``CapacityExceededError`` is raised if it is already full;
        * the existing partial unique index remains the authoritative
          duplicate guard; a unique violation is translated to the typed
          ``DuplicateActiveAllocationError``.

        Every OTHER failure (connection loss, FK/constraint error other than the
        duplicate guard) propagates unchanged, so it surfaces as a genuine
        server error rather than masquerading as a duplicate (F-7).

        ``capacity=None`` preserves the previous behaviour (no finite capacity
        configured ⇒ no cap enforced).
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))",
                    f"consultant_mp_allocations:{consultant_id}",
                )
                if capacity is not None:
                    active = await conn.fetchval(
                        "SELECT count(*) FROM public.consultant_mp_allocations "
                        "WHERE consultant_id = $1 AND state = 'active'",
                        consultant_id,
                    )
                    if int(active or 0) >= int(capacity):
                        raise CapacityExceededError(
                            "selected-client capacity is exhausted"
                        )
                try:
                    row = await conn.fetchrow(
                        f"INSERT INTO public.consultant_mp_allocations "
                        f"(consultant_id, consultant_client_id, organization_id, "
                        f"state, reason, allocated_by) "
                        f"VALUES ($1, $2, $3, 'active', $4, $5) "
                        f"RETURNING {_ALLOCATION_COLUMNS}",
                        consultant_id,
                        consultant_client_id,
                        organization_id,
                        reason,
                        actor_id,
                    )
                except asyncpg.UniqueViolationError as exc:
                    raise DuplicateActiveAllocationError(
                        "duplicate active allocation"
                    ) from exc
        if row is None:
            raise RuntimeError("consultant_mp_allocations insert returned no row")
        return _row_to_allocation(row)

    async def release_allocation(
        self, *, allocation_id: str, reason: Optional[str], actor_id: str
    ) -> Optional[ConsultantAllocation]:
        """Release one ACTIVE allocation (returns its capacity unit)."""
        row = await self._fetch_one(
            f"UPDATE public.consultant_mp_allocations "
            f"SET state = 'released', reason = COALESCE($2, reason), "
            f"released_by = $3, released_at = NOW(), updated_at = NOW() "
            f"WHERE id = $1 AND state = 'active' RETURNING {_ALLOCATION_COLUMNS}",
            allocation_id,
            reason,
            actor_id,
        )
        return _row_to_allocation(row) if row is not None else None


