"""P17-H estimation-record repository (P17-IMPLEMENT-08).

The persistence layer for ``public.estimation_records``. Until this existed,
``domain.estimation.EstimationRecord`` was validated but never written, so an
estimate's basis lived only in memory — a real gap against T-INV-12, which says an
estimated value must carry a *persisted* estimation record.

This repository only stores what the domain already validated. It re-uses
``EstimationRecord`` unchanged (no second estimation model), and never decides
whether an estimate is acceptable — that is ``domain.estimation``'s job.

Linkage
-------
The schema (``20261013000000_p17h_estimation_and_assumption_records.sql``) links a
record to the calculation it substantiates via ``calculation_snapshot_id`` with
``ON DELETE CASCADE``. That is the relationship used: a record cannot reference a
nonexistent calculation, because the foreign key requires a real snapshot and the
record is written only **after** the calculation has been persisted.

Tenant ownership comes from the caller's resolved accounting context. This module
never accepts a client-supplied organization as authority.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb
from domain.estimation import EstimationRecord

#: Explicit column list — never ``SELECT *``.
_RECORD_COLUMNS = """
    id, organization_id, calculation_snapshot_id, emissions_log_id,
    estimation_method, inputs, assumptions, factor_id, source_reference,
    scope3_category, actor_user_id, actor_organization_id,
    acting_for_organization_id, created_at
"""


def _row_to_record(row: Any) -> dict[str, Any]:
    """Map an ``estimation_records`` row to a plain dict.

    Reads return the stored row rather than fabricating a domain instance: the
    domain object is the *input* shape and carries no ``id`` or ``created_at``.
    """
    return {
        "id": str(row["id"]),
        "organization_id": str(row["organization_id"]),
        "calculation_snapshot_id": (
            str(row["calculation_snapshot_id"])
            if row["calculation_snapshot_id"] is not None
            else None
        ),
        "emissions_log_id": (
            str(row["emissions_log_id"])
            if row["emissions_log_id"] is not None
            else None
        ),
        "estimation_method": row["estimation_method"],
        "scope3_category": row["scope3_category"],
        "factor_id": str(row["factor_id"]) if row["factor_id"] is not None else None,
    }


class EstimationRecordsRepository(AbstractRepository[dict]):
    """Read/write surface for P17-H estimation records."""

    async def get(self, id: str) -> Optional[dict[str, Any]]:
        """Return the estimation record with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_RECORD_COLUMNS} FROM public.estimation_records WHERE id = $1",
            id,
        )
        return _row_to_record(row) if row is not None else None

    async def list_for_snapshot(self, snapshot_id: str) -> list[dict[str, Any]]:
        """Every estimation record substantiating one calculation."""
        rows = await self._fetch_all(
            f"SELECT {_RECORD_COLUMNS} FROM public.estimation_records "
            "WHERE calculation_snapshot_id = $1 ORDER BY created_at, id",
            snapshot_id,
        )
        return [_row_to_record(r) for r in rows]

    async def record(self, record: EstimationRecord) -> Optional[str]:
        """Persist a validated estimation record. Returns the new id, or ``None``.

        ``None`` means a record already exists for this calculation, so nothing
        new was written — the call is idempotent for one calculation, which is what
        stops a retry doubling the evidence for the same snapshot.

        The domain has already validated the record; a database constraint failure
        here would be a real defect and is deliberately left to surface.
        """
        if record.calculation_snapshot_id is None:
            raise ValueError(
                "an estimation record must reference the calculation it "
                "substantiates; refusing to persist an orphan record"
            )
        row = await self._fetch_one(
            """
            INSERT INTO public.estimation_records (
                organization_id, calculation_snapshot_id, emissions_log_id,
                estimation_method, inputs, assumptions, factor_id,
                source_reference, scope3_category, actor_user_id,
                actor_organization_id, acting_for_organization_id
            )
            SELECT $1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, $9, $10, $11, $12
             WHERE NOT EXISTS (
                SELECT 1 FROM public.estimation_records
                 WHERE calculation_snapshot_id = $2
             )
            RETURNING id
            """,
            record.organization_id,
            record.calculation_snapshot_id,
            record.emissions_log_id,
            record.estimation_method,
            dumps_jsonb(dict(record.inputs)),
            dumps_jsonb(dict(record.assumptions)),
            record.factor_id,
            record.source_reference,
            record.scope3_category,
            record.actor_user_id,
            record.actor_organization_id,
            record.acting_for_organization_id,
        )
        return str(row["id"]) if row is not None else None

    async def save(self, entity: dict) -> dict:
        """Not supported: a record is created once, by :meth:`record`."""
        raise NotImplementedError(
            "estimation records are written through record(); use that method so "
            "the calculation linkage and the not-already-recorded guard apply"
        )

    async def delete(self, id: str) -> None:
        """Refuse deletion: an estimation record is the evidence for an estimate."""
        raise NotImplementedError(
            "estimation records are accounting evidence and must not be deleted"
        )

