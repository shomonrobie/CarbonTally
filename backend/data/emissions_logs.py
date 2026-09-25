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
from domain.insight_query import (
    canonical_scope,
    parse_int,
    parse_iso_date,
    resolve_amount_bounds,
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
    source_item_id, source_line_item_id, source_file, source_page, performed_by
"""

#: Allowed analytics grouping dimensions → fixed, allowlisted SQL expressions
#: (Phase 8 Insight analytics). ``cs.`` expressions require the snapshot join.
_ANALYTICS_DIMENSION_EXPRESSIONS: dict[str, str] = {
    "scope": "COALESCE(l.scope, 'unknown')",
    "month": "to_char(l.start_date, 'YYYY-MM')",
    "year": "to_char(l.start_date, 'YYYY')",
    "activity": "COALESCE(cs.activity_type, 'unknown')",
    "supplier": "COALESCE(l.supplier_id::text, 'none')",
    "facility": "COALESCE(l.metadata->>'facility_id', 'none')",
    "asset": "COALESCE(l.asset_id::text, 'none')",
}

#: Dimensions whose group keys are organisation-owned catalogue ids → the
#: (table, key column) used for a bounded, organisation-scoped label lookup.
_ANALYTICS_LABEL_SOURCES: dict[str, tuple[str, str]] = {
    "supplier": ("public.suppliers", "id"),
    "facility": ("public.facilities", "id"),
    "asset": ("public.assets", "id"),
}


def _analytics_expression(dimension: str) -> str:
    """Return the allowlisted grouping expression, or raise (never a query)."""
    try:
        return _ANALYTICS_DIMENSION_EXPRESSIONS[dimension]
    except KeyError as exc:
        raise ValueError(
            f"dimension {dimension!r} not in {sorted(_ANALYTICS_DIMENSION_EXPRESSIONS)}"
        ) from exc


def _containment_pattern(term: str) -> str:
    """Build a literal containment pattern, escaping wildcard metacharacters.

    The user's term is never a pattern: ``%`` and ``_`` are escaped so the match
    stays a deterministic containment test rather than an accidental wildcard
    search.
    """
    escaped = (
        term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )
    return f"%{escaped}%"


def _snapshot_filter_clause(
    filters: dict[str, Any], start_index: int
) -> tuple[str, list[Any]]:
    """Build the discovery WHERE fragment (fixed literals + positional params).

    Returns ``(clause_sql, params)`` where ``clause_sql`` starts with ``AND`` or is
    empty. An empty filter set raises, because the caller must never be able to
    trigger an unbounded scan of the organisation's snapshots.
    """
    clauses: list[str] = []
    params: list[Any] = []
    index = start_index

    start = parse_iso_date(filters.get("start_date"))
    if start is not None:
        clauses.append(f"s.date >= ${index}")
        params.append(start)
        index += 1
    end = parse_iso_date(filters.get("end_date"))
    if end is not None:
        clauses.append(f"s.date <= ${index}")
        params.append(end)
        index += 1

    year = parse_int(filters.get("reporting_year"))
    if year is not None:
        clauses.append(f"s.reporting_year = ${index}")
        params.append(year)
        index += 1

    bounds = resolve_amount_bounds(filters)
    if bounds is not None:
        clauses.append(f"s.co2e_kg >= ${index}")
        params.append(bounds.low)
        index += 1
        clauses.append(f"s.co2e_kg <= ${index}")
        params.append(bounds.high)
        index += 1

    activity = str(filters.get("activity") or "").strip()
    if activity:
        clauses.append(f"s.activity_type ILIKE ${index}")
        params.append(_containment_pattern(activity))
        index += 1

    scope = canonical_scope(filters.get("scope"))
    if scope:
        clauses.append(f"s.scope = ${index}")
        params.append(scope)
        index += 1

    supplier_id = str(filters.get("supplier_id") or "").strip()
    if supplier_id:
        clauses.append(
            "EXISTS (SELECT 1 FROM public.emissions_logs l "
            f"WHERE l.snapshot_id = s.id AND l.supplier_id::text = ${index})"
        )
        params.append(supplier_id)
        index += 1

    facility_id = str(filters.get("facility_id") or "").strip()
    if facility_id:
        clauses.append(
            "EXISTS (SELECT 1 FROM public.emissions_logs l "
            f"WHERE l.snapshot_id = s.id AND l.metadata->>'facility_id' = ${index})"
        )
        params.append(facility_id)
        index += 1

    asset_id = str(filters.get("asset_id") or "").strip()
    if asset_id:
        clauses.append(
            "EXISTS (SELECT 1 FROM public.emissions_logs l "
            f"WHERE l.snapshot_id = s.id AND l.asset_id::text = ${index})"
        )
        params.append(asset_id)
        index += 1

    if not clauses:  # pragma: no cover - validation rejects this case first
        raise ValueError("discovery filters must contain at least one predicate")
    return " AND " + " AND ".join(clauses), params


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
        # O1 — customer-factor calculations leave emission_factor_id NULL; the
        # authoritative factor reference lives on the linked snapshot
        # (calculation_snapshots.customer_factor_id) and is joined here so the
        # validation/reporting engines can resolve it instead of treating the
        # log as an orphaned factor.
        customer_factor_id=(
            str(r["customer_factor_id"]) if r.get("customer_factor_id") else None
        ),
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
        supplier_id: Optional[str] = None,
    ) -> EmissionLog:
        """Insert one emissions record and return it.

        ``factor_id`` is ``None`` for customer-factor calculations (O1 — the
        column is nullable; provenance lives on the snapshot).
        ``calculated_kg_co2e`` is stored as ``0``; the Calculation Engine writes
        the computed figure through :meth:`save` (repositories never compute).
        ``supplier_id`` (P12-IMPL-02 §E) carries the operator-resolved supplier
        from ``manual_extraction_items.mapped_supplier_id`` — the Decision-01
        source of truth. ``None`` stays NULL rather than being back-filled with a
        guessed supplier: an unresolved supplier is never invented.
        """
        row = await self._fetch_one(
            f"""
            INSERT INTO public.emissions_logs (
                organization_id, asset_id, emission_factor_id, start_date,
                end_date, raw_quantity, calculated_kg_co2e, created_by_user_id,
                created_at, updated_at, unit, scope, snapshot_id, metadata,
                supplier_id
            ) VALUES ($1, $2, $3, $4, $4, $5, 0, $6, NOW(), NOW(), $7, $8, $9, $10::jsonb, $11)
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
            supplier_id,
        )
        if row is None:
            raise RuntimeError("emissions log insert returned no row")
        return _row_to_log(row)

    async def find_by_org(self, org_id: str, period: DateRange) -> list[EmissionLog]:
        """Return all logs for ``org_id`` whose date falls inside ``period``.

        O1 — customer-factor calculations carry ``customer_factor_id`` on the
        linked snapshot; it is joined here so validation/reporting can resolve
        the authoritative factor for a log whose ``emission_factor_id`` is NULL.
        """
        rows = await self._fetch_all(
            f"""
            SELECT {_LOG_COLUMNS_L}, s.customer_factor_id
            FROM public.emissions_logs l
            LEFT JOIN public.calculation_snapshots s ON s.id = l.snapshot_id
            WHERE l.organization_id = $1
              AND l.start_date >= $2
              AND l.start_date <= $3
            ORDER BY l.start_date, l.created_at
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
              -- P16-RD-4: non-reportable results are never aggregated into
              -- reported totals. They remain individually inspectable.
              AND reportability_status = 'reportable'
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
              -- P16-RD-4: non-reportable results are never aggregated.
              AND reportability_status = 'reportable'
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

    async def list_for_line(
        self, line_item_id: str, organization_id: str, limit: int = 5
    ) -> list[dict]:
        """Source Evidence Viewer — the calculations derived from one evidence line.

        Bounded, org-scoped and allowlist-only: the caller receives the stable
        reference and the calculation result context, never the raw snapshot row.
        ``organization_id`` is applied in SQL as well as checked by the API, so a
        stored line id can never widen scope.
        """
        rows = await self._fetch_all(
            """
            SELECT id, organization_id, source_item_id, source_line_item_id,
                   activity, activity_type, quantity, quantity_unit, co2e_kg,
                   scope, date, reporting_year, methodology, algorithm_version,
                   content_hash, calculated_at
              FROM public.calculation_snapshots
             WHERE source_line_item_id = $1 AND organization_id = $2
             ORDER BY calculated_at DESC
             LIMIT $3
            """,
            line_item_id,
            organization_id,
            int(limit),
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

    async def find_snapshot_by_request_id(self, request_id: str) -> Optional[dict]:
        """Resolve an existing snapshot by its ``request_id``.

        Used by the automatic pipeline's no-duplicate-calculation guard: the
        worker derives a deterministic request id per job, so re-running a job
        whose snapshot was already written (e.g. after a crash between the
        snapshot insert and the job update) reuses the immutable snapshot
        instead of creating a duplicate calculation.
        """
        row = await self._fetch_one(
            f"SELECT {_SNAPSHOT_COLUMNS} FROM public.calculation_snapshots "
            "WHERE request_id = $1 ORDER BY calculated_at DESC LIMIT 1",
            request_id,
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

    async def invalidate_snapshot_result(
        self,
        snapshot_id: str,
        *,
        status: str,
        reason: str,
        actor_user_id: str,
        superseded_by_snapshot_id: Optional[str] = None,
    ) -> dict:
        """P16-REMEDIATION-05 / RD-4 — move a calculation result out of reporting.

        Marks the snapshot *and* its paired emissions log(s) as
        ``not_for_reporting``/``superseded`` with an explicit reason, actor and
        timestamp, and records the replacement relationship when supplied.

        The historical accounting values (``co2e_kg``, ``calculated_kg_co2e``,
        quantities, factor ids, scope) are **never** modified — only the
        reportability lifecycle state is. Non-reportable results stay fully
        inspectable; they are excluded from reporting/disclosure aggregation by
        the consumption boundary.

        Returns ``{"snapshot_id", "log_ids", "status"}``. An already
        non-reportable result is left untouched (idempotent).
        """
        if status not in ("not_for_reporting", "superseded"):
            raise ValueError(f"unsupported reportability status {status!r}")
        if not str(reason or "").strip():
            raise ValueError("an invalidation reason is required")

        superseded_log_id = None
        if superseded_by_snapshot_id:
            replacement = await self._fetch_one(
                "SELECT id FROM public.emissions_logs WHERE snapshot_id = $1 "
                "ORDER BY created_at LIMIT 1",
                superseded_by_snapshot_id,
            )
            if replacement is not None:
                superseded_log_id = replacement["id"]

        snapshot_row = await self._fetch_one(
            """
            UPDATE public.calculation_snapshots
            SET reportability_status = $2,
                invalidated_reason = $3,
                invalidated_by = $4,
                invalidated_at = now(),
                superseded_by_snapshot_id = $5
            WHERE id = $1 AND reportability_status = 'reportable'
            RETURNING id
            """,
            snapshot_id,
            status,
            reason,
            actor_user_id,
            superseded_by_snapshot_id,
        )
        if snapshot_row is None:
            raise LookupError(f"snapshot {snapshot_id!r} is missing or already non-reportable")

        log_rows = await self._fetch_all(
            """
            UPDATE public.emissions_logs
            SET reportability_status = $2,
                invalidated_reason = $3,
                invalidated_by = $4,
                invalidated_at = now(),
                superseded_by_log_id = $5
            WHERE snapshot_id = $1 AND reportability_status = 'reportable'
            RETURNING id
            """,
            snapshot_id,
            status,
            reason,
            actor_user_id,
            superseded_log_id,
        )
        return {
            "snapshot_id": snapshot_id,
            "log_ids": [r["id"] for r in log_rows],
            "status": status,
        }

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
        performed_by: Optional[str] = None,
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
                source_item_id, source_file, source_page, performed_by,
                source_line_item_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                      $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26,
                      $27)
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
            performed_by,
            snapshot.source_line_item_id,
        )
        if row is None:
            raise RuntimeError("calculation snapshot insert returned no row")
        return snapshot

    async def delete(self, id: str) -> None:
        """Delete an emissions record (not used in the normal flow)."""
        await self._execute(
            "DELETE FROM public.emissions_logs WHERE id = $1", id
        )

    # ----------------------------------------------------------------------
    # Phase 8 Insight analytics — bounded discovery / aggregation / provenance
    #
    # Authorization: PO Insight Discovery-Aggregation-Provenance package
    # (2026-09-22). Every SQL fragment below is a fixed allowlisted literal and
    # every caller value is a positional parameter, so no caller text can reach
    # the statement. Every query is organisation-scoped and bounded.
    # ----------------------------------------------------------------------

    async def search_snapshots(
        self, org_id: str, filters: dict[str, Any], limit: int
    ) -> list[dict]:
        """Bounded discovery over the authoritative calculation snapshots.

        Ordering is deterministic (``date`` descending, then ``id``), so an
        identical authorized request against unchanged data yields an identical
        candidate list.
        """
        clause, params = _snapshot_filter_clause(filters, start_index=2)
        sql = (
            f"SELECT {_SNAPSHOT_COLUMNS} FROM public.calculation_snapshots s "
            f"WHERE s.organization_id = $1{clause} "
            "ORDER BY s.date DESC, s.id ASC "
            f"LIMIT ${len(params) + 2}"
        )
        rows = await self._fetch_all(sql, org_id, *params, int(limit))
        return [dict(r) for r in rows]

    async def count_matching_snapshots(
        self, org_id: str, filters: dict[str, Any], cap: int
    ) -> int:
        """Count discovery matches, bounded by ``cap`` (never an unbounded count)."""
        clause, params = _snapshot_filter_clause(filters, start_index=2)
        sql = (
            "SELECT COUNT(*) AS n FROM ("
            "SELECT 1 FROM public.calculation_snapshots s "
            f"WHERE s.organization_id = $1{clause} "
            f"LIMIT ${len(params) + 2}"
            ") capped"
        )
        row = await self._fetch_one(sql, org_id, *params, int(cap))
        return int(row["n"]) if row is not None else 0

    async def aggregate_groups(
        self, org_id: str, period: DateRange, dimension: str, limit: int
    ) -> list[dict]:
        """CO₂e by an allowlisted dimension over a bounded period (kg CO₂e only).

        The measure is ``emissions_logs.calculated_kg_co2e`` — the same basis the
        existing emissions aggregates use — and the grouping expression comes from
        the closed dimension map, so an unsupported dimension is a ``ValueError``
        rather than a query.

        A summed *quantity* is deliberately not returned: one group can mix
        litres, kWh, m³ and currency, and presenting such a total as a quantity
        would be untrue.
        """
        expression = _analytics_expression(dimension)
        join = (
            "LEFT JOIN public.calculation_snapshots cs "
            "ON cs.id = l.snapshot_id AND cs.organization_id = $1 "
            if "cs." in expression
            else ""
        )
        rows = await self._fetch_all(
            f"""
            SELECT {expression} AS group_key,
                   COUNT(*) AS row_count,
                   SUM(l.calculated_kg_co2e) AS co2e_kg
            FROM public.emissions_logs l
            {join}
            WHERE l.organization_id = $1
              AND l.start_date BETWEEN $2 AND $3
            GROUP BY {expression}
            ORDER BY co2e_kg DESC, group_key ASC
            LIMIT $4
            """,
            org_id,
            period.start_date,
            period.end_date,
            int(limit),
        )
        return [dict(r) for r in rows]

    async def group_labels(
        self, org_id: str, dimension: str, keys: list[str]
    ) -> dict[str, str]:
        """Resolve human-readable labels for asset/facility/supplier group keys.

        Bounded to the keys actually returned, organisation-scoped, and never
        inferred: a key with no matching row simply has no label.
        """
        source = _ANALYTICS_LABEL_SOURCES.get(dimension)
        if source is None or not keys:
            return {}
        table, key_column = source
        rows = await self._fetch_all(
            f"SELECT t.{key_column}::text AS key, t.name AS label "
            f"FROM {table} t "
            "WHERE t.organization_id = $1 AND t.name IS NOT NULL "
            f"AND t.{key_column}::text = ANY($2::text[])",
            org_id,
            [str(k) for k in keys],
        )
        return {str(r["key"]): str(r["label"]) for r in rows}

    async def list_group_snapshots(
        self,
        org_id: str,
        period: DateRange,
        dimension: str,
        group_key: str,
        limit: int,
    ) -> list[dict]:
        """Bounded provenance: the calculation snapshots behind one aggregate cell.

        Only rows carrying an authoritative ``snapshot_id`` are returned, and the
        snapshot join is organisation-scoped, so one tenant can never receive
        another tenant's calculation identity.
        """
        expression = _analytics_expression(dimension)
        rows = await self._fetch_all(
            f"""
            SELECT DISTINCT l.snapshot_id AS id,
                   cs.date AS date,
                   cs.activity_type AS activity_type,
                   cs.scope AS scope,
                   cs.co2e_kg AS co2e_kg,
                   cs.source_line_item_id AS source_line_item_id
            FROM public.emissions_logs l
            JOIN public.calculation_snapshots cs
              ON cs.id = l.snapshot_id AND cs.organization_id = $1
            WHERE l.organization_id = $1
              AND l.start_date BETWEEN $2 AND $3
              AND l.snapshot_id IS NOT NULL
              AND {expression} = $4
            ORDER BY cs.date DESC, l.snapshot_id ASC
            LIMIT $5
            """,
            org_id,
            period.start_date,
            period.end_date,
            str(group_key),
            int(limit),
        )
        return [dict(r) for r in rows]

    async def count_group_snapshots(
        self, org_id: str, period: DateRange, dimension: str, group_key: str, cap: int
    ) -> int:
        """Count contributing snapshots for one aggregate cell, bounded by ``cap``."""
        expression = _analytics_expression(dimension)
        row = await self._fetch_one(
            f"""
            SELECT COUNT(*) AS n FROM (
                SELECT DISTINCT l.snapshot_id
                FROM public.emissions_logs l
                WHERE l.organization_id = $1
                  AND l.start_date BETWEEN $2 AND $3
                  AND l.snapshot_id IS NOT NULL
                  AND {expression} = $4
                LIMIT $5
            ) capped
            """,
            org_id,
            period.start_date,
            period.end_date,
            str(group_key),
            int(cap),
        )
        return int(row["n"]) if row is not None else 0

