"""Exports repository (V3 legacy-capability reimplementation).

Read-only data access for export generation. Exports are computed from
``emissions_logs`` (typed rows) and served as CSV/JSON by the API layer; no
dedicated export-history table is assumed.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from data.base import AbstractRepository

_LOG_COLUMNS = (
    "id, organization_id, asset_id, emission_factor_id, start_date, end_date, "
    "raw_quantity, calculated_kg_co2e, unit, scope, snapshot_id, created_at"
)

#: Same list qualified with ``l.`` for the D33 export lineage JOIN.
_LOG_COLUMNS_L = ", ".join(f"l.{c}" for c in _LOG_COLUMNS.split(", "))


def _jsonable_row(row: dict[str, Any]) -> dict[str, Any]:
    """Coerce database types (asyncpg UUID/date/datetime/Decimal) to JSON-safe
    values.

    Repository rows flow straight into FastAPI JSON responses; ``uuid.UUID``,
    ``date``/``datetime`` and ``Decimal`` are not JSON-serialisable by default
    (this was the ``GET /api/v3/exports/emissions.json`` 500 root cause).
    """
    out: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, uuid.UUID):
            out[key] = str(value)
        elif isinstance(value, (datetime, date)):
            out[key] = value.isoformat()
        elif isinstance(value, Decimal):
            out[key] = float(value)
        else:
            out[key] = value
    return out


def _evidence_status(row: dict[str, Any]) -> str:
    """D33.1 — honest evidence-completeness label for an exported emission.

    Derived from the persisted provenance identifiers only (never fabricated):
    COMPLETE requires the source item + source file + an exact source page;
    PARTIAL has a partial chain; UNAVAILABLE has no reliable source reference.
    """
    item_id = row.get("source_item_id")
    source_file = row.get("source_file")
    source_page = row.get("source_page")
    if item_id and source_file:
        return "COMPLETE" if source_page is not None else "PARTIAL"
    if item_id or source_file:
        return "PARTIAL"
    return "UNAVAILABLE"


class ExportsRepository(AbstractRepository[dict]):
    """Query emissions logs and organisation files for export."""

    async def emissions(
        self,
        org_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        scope: Optional[str] = None,
        limit: int = 10000,
    ) -> list[dict]:
        # D33: export carries provenance identifiers — the calculation snapshot
        # id (already on the log) plus the source extraction item / source file
        # name / page reference from the authoritative lineage chain.
        query = (
            f"SELECT {_LOG_COLUMNS_L}, "
            "s.source_item_id, s.source_file, s.source_page, "
            # ISC-3 — the emissions list is self-describing evidence: the
            # activity/factor that produced the emission come from the snapshot
            # join (never fabricated).
            "s.activity, s.activity_type, s.factor_id AS snapshot_factor_id, "
            "ef.activity_type AS factor_name "
            "FROM public.emissions_logs l "
            "LEFT JOIN public.calculation_snapshots s ON s.id = l.snapshot_id "
            "LEFT JOIN public.emission_factors ef ON ef.id = s.factor_id "
            "WHERE l.organization_id = $1"
        )
        args: list[Any] = [org_id]
        if start_date is not None:
            args.append(start_date)
            query += f" AND l.start_date >= ${len(args)}"
        if end_date is not None:
            args.append(end_date)
            query += f" AND l.end_date <= ${len(args)}"
        if scope is not None:
            args.append(scope)
            query += f" AND l.scope = ${len(args)}"
        query += " ORDER BY l.start_date"
        query += f" LIMIT {int(limit)}"
        rows = await self._fetch_all(query, *args)
        out = []
        for r in rows:
            row = _jsonable_row(dict(r))
            row["evidence_status"] = _evidence_status(row)
            out.append(row)
        return out

    async def documents(self, org_id: str) -> list[dict]:
        rows = await self._fetch_all(
            """
            SELECT id, name, file_type, status, uploaded_at, size_bytes
            FROM public.organization_files
            WHERE organization_id = $1 AND is_active = TRUE
            ORDER BY uploaded_at DESC
            """,
            org_id,
        )
        return [_jsonable_row(dict(r)) for r in rows]

    async def get(self, id: str):
        return None

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        return None
