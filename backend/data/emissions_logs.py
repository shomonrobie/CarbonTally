"""Emissions-logs repository (Backend v2.1 §10).

Persistence for the RC2 ``emissions_logs`` operational record. The table has no
``facility_id`` column, so the domain's ``facility_id`` round-trips through the
``metadata`` JSONB column; ``calculated_kg_co2e`` is written by the Calculation
Engine (Phase 6) via :meth:`EmissionsLogsRepository.save`.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from core.types import DateRange
from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.calculation import (
    CalculationSnapshot,
    EmissionLog,
    EmissionsAggregate,
)

#: Service-role placeholder used for NOT NULL actor/user columns the v2.1
#: contract does not pass to the repository.
_SYSTEM_UUID = "00000000-0000-0000-0000-000000000000"

_LOG_COLUMNS = """
    id, organization_id, asset_id, emission_factor_id, start_date, end_date,
    raw_quantity, calculated_kg_co2e, created_at, unit, scope, snapshot_id,
    metadata
"""

#: Same columns as a single-line comma list (for ``l.<cols>`` qualified refs).
_LOG_COLUMNS_LIST = (
    "id, organization_id, asset_id, emission_factor_id, start_date, end_date, "
    "raw_quantity, calculated_kg_co2e, created_at, unit, scope, snapshot_id, metadata"
)

#: Every log column explicitly qualified with ``l.`` (JOIN-safe).
_LOG_COLUMNS_L = ", ".join(f"l.{c}" for c in _LOG_COLUMNS_LIST.split(", "))

#: Allowed ``group_by`` dimensions mapped to SQL expressions (SQL-injection safe).
_GROUP_EXPRESSIONS: dict[str, str] = {
    "scope": "scope",
    "month": "to_char(start_date, 'YYYY-MM')",
    "year": "to_char(start_date, 'YYYY')",
    "asset": "COALESCE(asset_id::text, 'none')",
    "facility": "COALESCE(metadata->>'facility_id', 'none')",
}

#: Explicit ``calculation_snapshots`` column list for the Phase 4 read surface
#: (immutable forensic record — read-only; never ``SELECT *``).
_SNAPSHOT_COLUMNS = """
    id, organization_id, activity, activity_type, quantity, quantity_unit,
    co2e_multiplier, co2e_kg, scope, date, factor_id, factor_source, factor_set,
    import_batch_id, reporting_year, methodology, algorithm_version, content_hash,
    calculated_at, calculated_by, request_id, factor_kind, customer_factor_id,
    source_item_id, source_file, source_page
"""


def _row_to_log(row: Any) -> EmissionLog:
    r = dict(row)
    metadata = loads_jsonb(r.get("metadata")) or {}
    facility_id = metadata.get("facility_id")
    return EmissionLog(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        factor_id=str(r["emission_factor_id"]) if r.get("emission_factor_id") else None,
        quantity=Decimal(str(r["raw_quantity"])),
        date=r["start_date"],
        unit=r["unit"],
        scope=r["scope"],
        asset_id=str(r["asset_id"]) if r.get("asset_id") else None,
        facility_id=str(facility_id) if facility_id else None,
        snapshot_id=str(r["snapshot_id"]) if r.get("snapshot_id") else None,
        calculated_kg_co2e=Decimal(str(r["calculated_kg_co2e"])),
        created_at=r["created_at"],
    )


def _log_metadata(facility_id: Optional[str]) -> str:
    """JSONB metadata carrying the non-column ``facility_id`` field.

    Takes the id directly (rather than a throwaway :class:`EmissionLog`) because
    the domain model rejects empty ids, and metadata is built for rows that do
    not exist yet.
    """
    payload: dict[str, object] = {}
    if facility_id:
        payload["facility_id"] = facility_id
    return dumps_jsonb(payload)


class EmissionsLogsRepository(AbstractRepository[EmissionLog]):
    """CRUD and aggregation for operational emissions records."""

    async def create(
        self,
        org_id: str,
        factor_id: Optional[str],
        quantity: Decimal,
        unit: str,
        scope: Optional[str],
        date: date,
        asset_id: Optional[str],
        facility_id: Optional[str],
        snapshot_id: str,
    ) -> EmissionLog:
        """Insert one emissions record and return it.

        ``factor_id`` is ``None`` for customer-factor calculations (O1 — the
        column is nullable; provenance lives on the snapshot).
        ``calculated_kg_co2e`` is stored as ``0``; the Calculation Engine writes
        the computed figure through :meth:`save` (repositories never compute).
        """
        row = await self._fetch_one(
            f"""
            INSERT INTO public.emissions_logs (
                organization_id, asset_id, emission_factor_id, start_date,
                end_date, raw_quantity, calculated_kg_co2e, created_by_user_id,
                created_at, updated_at, unit, scope, snapshot_id, metadata
            ) VALUES ($1, $2, $3, $4, $4, $5, 0, $6, NOW(), NOW(), $7, $8, $9, $10::jsonb)
            RETURNING {_LOG_COLUMNS}
            """,
            org_id,
            asset_id,
            factor_id,
            date,
            quantity,
            _SYSTEM_UUID,
            unit,
            scope,
            snapshot_id,
            _log_metadata(facility_id),
        )
        if row is None:
            raise RuntimeError("emissions log insert returned no row")
        return _row_to_log(row)

    async def find_by_org(self, org_id: str, period: DateRange) -> list[EmissionLog]:
        """Return all logs for ``org_id`` whose date falls inside ``period``."""
        rows = await self._fetch_all(
            f"""
            SELECT {_LOG_COLUMNS} FROM public.emissions_logs
            WHERE organization_id = $1
              AND start_date >= $2
              AND start_date <= $3
            ORDER BY start_date, created_at
            """,
            org_id,
            period.start_date,
            period.end_date,
        )
        return [_row_to_log(r) for r in rows]

    async def aggregate(
        self, org_id: str, period: DateRange, group_by: str
    ) -> EmissionsAggregate:
        """Sum emissions for ``org_id``/``period`` grouped by ``group_by``."""
        if group_by not in _GROUP_EXPRESSIONS:
            raise ValueError(
                f"group_by {group_by!r} not in {sorted(_GROUP_EXPRESSIONS)}"
            )
        group_expr = _GROUP_EXPRESSIONS[group_by]
        scope_rows = await self._fetch_all(
            """
            SELECT COALESCE(scope, 'unknown') AS scope_key,
                   SUM(calculated_kg_co2e) AS co2e
            FROM public.emissions_logs
            WHERE organization_id = $1
              AND start_date >= $2
              AND start_date <= $3
            GROUP BY COALESCE(scope, 'unknown')
            ORDER BY scope_key
            """,
            org_id,
            period.start_date,
            period.end_date,
        )
        group_rows = await self._fetch_all(
            f"""
            SELECT {group_expr} AS group_key,
                   SUM(calculated_kg_co2e) AS co2e,
                   COUNT(*) AS cnt
            FROM public.emissions_logs
            WHERE organization_id = $1
              AND start_date >= $2
              AND start_date <= $3
            GROUP BY {group_expr}
            ORDER BY group_key
            """,
            org_id,
            period.start_date,
            period.end_date,
        )
        by_scope = {str(r["scope_key"]): Decimal(str(r["co2e"])) for r in scope_rows}
        by_group = {str(r["group_key"]): Decimal(str(r["co2e"])) for r in group_rows}
        total = sum(by_group.values(), Decimal("0"))
        total_rows = sum(int(r["cnt"]) for r in group_rows)
        return EmissionsAggregate(
            organization_id=org_id,
            period=period,
            group_by=group_by,
            total_co2e_kg=total,
            total_rows=total_rows,
            by_scope=by_scope,
            by_group=by_group,
        )

    async def count_by_scope(self, org_id: str, year: int) -> dict[str, int]:
        """Return per-scope counts for ``org_id`` in ``year``."""
        rows = await self._fetch_all(
            """
            SELECT COALESCE(scope, 'unknown') AS scope_key, COUNT(*) AS count
            FROM public.emissions_logs
            WHERE organization_id = $1
              AND EXTRACT(YEAR FROM start_date) = $2
            GROUP BY COALESCE(scope, 'unknown')
            """,
            org_id,
            year,
        )
        return {str(r["scope_key"]): int(r["count"]) for r in rows}


    # -- Phase 4 read surfaces (emissions intelligence) ---------------------
    async def aggregate_by_supplier(self, org_id: str, period: DateRange) -> list[dict]:
        """Supplier breakdown for ``org_id`` over ``period`` (raw rows)."""
        rows = await self._fetch_all(
            """
            SELECT COALESCE(l.supplier_id::text, 'none') AS supplier_id,
                   COALESCE(s.name, 'Unassigned') AS supplier_name,
                   COUNT(*) AS row_count,
                   SUM(l.raw_quantity) AS quantity,
                   SUM(l.calculated_kg_co2e) AS co2e_kg
            FROM public.emissions_logs l
            LEFT JOIN public.suppliers s ON s.id = l.supplier_id
            WHERE l.organization_id = $1
              AND l.start_date BETWEEN $2 AND $3
            GROUP BY l.supplier_id, s.name
            ORDER BY co2e_kg DESC
            """,
            org_id,
            period.start_date,
            period.end_date,
        )
        return [dict(r) for r in rows]

    async def aggregate_by_activity(self, org_id: str, period: DateRange) -> list[dict]:
        """Activity/category breakdown via the immutable snapshots (raw rows)."""
        rows = await self._fetch_all(
            """
            SELECT cs.activity_type, COUNT(*) AS row_count,
                   SUM(cs.quantity) AS quantity,
                   SUM(cs.co2e_kg) AS co2e_kg
            FROM public.calculation_snapshots cs
            JOIN public.emissions_logs l ON l.snapshot_id = cs.id
            WHERE cs.organization_id = $1
              AND l.start_date BETWEEN $2 AND $3
            GROUP BY cs.activity_type
            ORDER BY co2e_kg DESC
            """,
            org_id,
            period.start_date,
            period.end_date,
        )
        return [dict(r) for r in rows]

    async def count_snapshots(self, org_id: str, period: DateRange) -> int:
        """Count calculation snapshots for ``org_id`` over ``period``."""
        row = await self._fetch_one(
            f"SELECT COUNT(*) AS n FROM public.calculation_snapshots "
            "WHERE organization_id = $1 AND date BETWEEN $2 AND $3",
            org_id,
            period.start_date,
            period.end_date,
        )
        return int(row["n"]) if row is not None else 0

    async def list_snapshots(
        self,
        org_id: str,
        period: DateRange,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Calculation history rows for ``org_id`` over ``period`` (newest first)."""
        rows = await self._fetch_all(
            f"SELECT {_SNAPSHOT_COLUMNS} FROM public.calculation_snapshots "
            "WHERE organization_id = $1 AND date BETWEEN $2 AND $3 "
            "ORDER BY calculated_at DESC "
            "LIMIT $4 OFFSET $5",
            org_id,
            period.start_date,
            period.end_date,
            int(limit),
            int(offset),
        )
        return [dict(r) for r in rows]

    async def list_for_file(self, file_id: str) -> list[dict]:
        """D33 — every emission derived from one source document.

        Chain: emissions_logs.snapshot_id -> calculation_snapshots.source_item_id
        -> manual_extraction_items.file_id -> organization_files.id.
        """
        rows = await self._fetch_all(
            f"""
            SELECT {_LOG_COLUMNS_L}, s.source_file, s.source_page
              FROM public.emissions_logs l
              JOIN public.calculation_snapshots s ON s.id = l.snapshot_id
              JOIN public.manual_extraction_items i ON i.id = s.source_item_id
             WHERE i.file_id = $1
             ORDER BY l.created_at
            """,
            file_id,
        )
        return [dict(r) for r in rows]

    async def get_snapshot(self, snapshot_id: str) -> Optional[dict]:
        """One immutable calculation-snapshot row (raw dict), or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_SNAPSHOT_COLUMNS} FROM public.calculation_snapshots "
            "WHERE id = $1",
            snapshot_id,
        )
        return dict(row) if row is not None else None

    async def snapshot_count_for_factor(self, factor_id: str) -> int:
        """Number of calculations that used ``factor_id`` (provenance/usage)."""
        row = await self._fetch_one(
            "SELECT COUNT(*) AS n FROM public.calculation_snapshots "
            "WHERE factor_id = $1",
            factor_id,
        )
        return int(row["n"]) if row is not None else 0

    async def factor_usage_span(self, factor_id: str) -> Optional[dict]:
        """First/last ``calculated_at`` for ``factor_id`` (provenance/usage)."""
        row = await self._fetch_one(
            "SELECT MIN(calculated_at) AS first_calculated_at, "
            "       MAX(calculated_at) AS last_calculated_at "
            "FROM public.calculation_snapshots WHERE factor_id = $1",
            factor_id,
        )
        if row is None:
            return None
        return {
            "first_calculated_at": row["first_calculated_at"],
            "last_calculated_at": row["last_calculated_at"],
        }

    async def get(self, id: str) -> Optional[EmissionLog]:
        """Return the single log with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_LOG_COLUMNS} FROM public.emissions_logs WHERE id = $1",
            id,
        )
        return _row_to_log(row) if row is not None else None

    async def save(self, entity: EmissionLog) -> EmissionLog:
        """Update an existing emissions record and return the stored state."""
        row = await self._fetch_one(
            f"""
            UPDATE public.emissions_logs
            SET emission_factor_id = $2,
                raw_quantity = $3,
                calculated_kg_co2e = $4,
                unit = $5,
                scope = $6,
                start_date = $7,
                end_date = $7,
                asset_id = $8,
                snapshot_id = $9,
                metadata = $10::jsonb,
                updated_at = NOW()
            WHERE id = $1
            RETURNING {_LOG_COLUMNS}
            """,
            entity.id,
            entity.factor_id,
            entity.quantity,
            entity.calculated_kg_co2e,
            entity.unit,
            entity.scope,
            entity.date,
            entity.asset_id,
            entity.snapshot_id,
            _log_metadata(entity.facility_id),
        )
        if row is None:
            raise RuntimeError(
                f"emissions log {entity.id!r} does not exist; cannot save"
            )
        return _row_to_log(row)

    async def save_snapshot(
        self,
        snapshot: CalculationSnapshot,
        *,
        activity: str,
        activity_type: str,
        factor_source: Optional[str] = None,
        factor_set: Optional[str] = None,
        import_batch_id: Optional[str] = None,
        calculated_by: Optional[str] = None,
        factor_kind: Optional[str] = None,
        customer_factor_id: Optional[str] = None,
    ) -> CalculationSnapshot:
        """Persist an immutable calculation snapshot (Backend v2.1 §13).

        The RC2 ``calculation_snapshots`` table stores provenance columns the
        domain model does not carry (``activity``, ``activity_type``,
        ``factor_source``, ``factor_set``, ``import_batch_id``), so they are
        supplied here alongside the snapshot. V3 (O1 / ADR-V3-014): the
        customer-factor provenance columns ``factor_kind`` and
        ``customer_factor_id`` are also written; existing emission-factor rows
        keep ``factor_kind='emission_factor'`` (the V3M-3 NOT NULL DEFAULT).
        ``calculated_at`` defaults to ``NOW()`` and the snapshot's
        ``match_request_id`` is stored in the table's ``request_id`` column.
        Snapshots are append-only and are never updated or deleted (ADR-5); a
        conflict on ``id`` therefore raises.
        """
        row = await self._fetch_one(
            f"""
            INSERT INTO public.calculation_snapshots (
                id, organization_id, activity, activity_type, quantity,
                quantity_unit, co2e_multiplier, co2e_kg, scope, date,
                factor_id, factor_source, factor_set, import_batch_id,
                reporting_year, methodology, algorithm_version, content_hash,
                calculated_by, request_id, factor_kind, customer_factor_id,
                source_item_id, source_file, source_page
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                      $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25)
            RETURNING id
            """,
            snapshot.id,
            snapshot.organization_id,
            activity,
            activity_type,
            snapshot.quantity,
            snapshot.quantity_unit,
            snapshot.co2e_multiplier,
            snapshot.co2e_kg,
            snapshot.scope,
            snapshot.date,
            snapshot.factor_id,
            factor_source,
            factor_set,
            import_batch_id,
            snapshot.reporting_year,
            snapshot.methodology,
            snapshot.algorithm_version,
            snapshot.content_hash,
            calculated_by,
            snapshot.match_request_id,
            factor_kind if factor_kind is not None else snapshot.factor_kind,
            customer_factor_id if customer_factor_id is not None else snapshot.customer_factor_id,
            snapshot.source_item_id,
            snapshot.source_file,
            snapshot.source_page,
        )
        if row is None:
            raise RuntimeError("calculation snapshot insert returned no row")
        return snapshot

    async def delete(self, id: str) -> None:
        """Delete an emissions record (not used in the normal flow)."""
        await self._execute(
            "DELETE FROM public.emissions_logs WHERE id = $1", id
        )

