"""Manual extraction repository (V3 new capability).

Persistence for ``manual_extraction_batches`` and ``manual_extraction_items``,
including the QC surface already present on items (qc_by, qc_at, qc_notes,
quality_score).
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.partners import (
    ManualExtractionBatch,
    ManualExtractionItem,
    WORKFLOW_STAGE_STATUSES,
)

_BATCH_COLUMNS = (
    "id, organization_id, batch_name, batch_description, entity_id, "
    "total_documents, total_pages, total_cost, price_per_page, currency, status, "
    "estimated_completion_date, actual_completion_date, sla_deadline, sla_breached, "
    "assigned_to, assigned_by, assigned_at, qc_by, qc_at, qc_notes, qc_approved, "
    "customer_notes, staff_notes, created_at, created_by, updated_at, updated_by, "
    "completed_by, completed_at"
)

_ITEM_COLUMNS = (
    "id, batch_id, document_processing_queue_id, file_name, file_url, "
    "page_count, document_type, status, extracted_data, mapped_data, "
    "mapped_facility_id, mapped_asset_id, mapped_supplier_id, "
    "calculated_emissions_kg_co2e, emission_factor_used, extracted_by, "
    "extracted_at, qc_by, qc_at, qc_notes, quality_score, "
    "customer_reviewed_by, customer_reviewed_at, customer_approved, "
    "customer_rejection_reason, customer_notes, created_at, updated_at, file_id"
)


#: Sentinel for ``update_batch`` — distinguishes "leave untouched" (default)
#: from an explicit ``None`` (clear the column, e.g. reassignment back to
#: CarbonTally-internal).
_UNSET = object()


def _uid(value: Any) -> Optional[str]:
    """Coerce a DB ``uuid`` column to its canonical string form.

    asyncpg returns ``uuid.UUID`` objects; every domain field typed as an id
    is a ``str``. Returning strings keeps guards (``assigned_to`` comparisons),
    API payloads and client code consistent.
    """
    if value is None:
        return None
    return str(value)


def _row_to_batch(row: Any) -> ManualExtractionBatch:
    r = dict(row)
    return ManualExtractionBatch(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        batch_name=str(r["batch_name"]),
        batch_description=r.get("batch_description"),
        entity_id=_uid(r.get("entity_id")),
        total_documents=int(r.get("total_documents") or 0),
        total_pages=int(r.get("total_pages") or 0),
        total_cost=float(r.get("total_cost") or 0.0),
        price_per_page=r.get("price_per_page"),
        currency=str(r.get("currency") or "GBP"),
        status=r.get("status"),
        estimated_completion_date=r.get("estimated_completion_date"),
        actual_completion_date=r.get("actual_completion_date"),
        sla_deadline=r.get("sla_deadline"),
        sla_breached=bool(r.get("sla_breached", False)),
        assigned_to=_uid(r.get("assigned_to")),
        assigned_by=_uid(r.get("assigned_by")),
        assigned_at=r.get("assigned_at"),
        qc_by=_uid(r.get("qc_by")),
        qc_at=r.get("qc_at"),
        qc_notes=r.get("qc_notes"),
        qc_approved=r.get("qc_approved"),
        customer_notes=r.get("customer_notes"),
        staff_notes=r.get("staff_notes"),
        created_at=r.get("created_at"),
        created_by=_uid(r.get("created_by")),
        updated_at=r.get("updated_at"),
        updated_by=_uid(r.get("updated_by")),
        completed_by=_uid(r.get("completed_by")),
        completed_at=r.get("completed_at"),
    )


def _row_to_item(row: Any) -> ManualExtractionItem:
    r = dict(row)
    return ManualExtractionItem(
        id=str(r["id"]),
        batch_id=str(r["batch_id"]),
        document_processing_queue_id=_uid(r.get("document_processing_queue_id")),
        file_name=str(r["file_name"]),
        file_url=str(r["file_url"]),
        file_id=_uid(r.get("file_id")),
        page_count=int(r.get("page_count") or 0),
        document_type=r.get("document_type"),
        status=r.get("status"),
        extracted_data=loads_jsonb(r.get("extracted_data")),
        mapped_data=loads_jsonb(r.get("mapped_data")),
        mapped_facility_id=_uid(r.get("mapped_facility_id")),
        mapped_asset_id=_uid(r.get("mapped_asset_id")),
        mapped_supplier_id=_uid(r.get("mapped_supplier_id")),
        calculated_emissions_kg_co2e=(
            float(r["calculated_emissions_kg_co2e"])
            if r.get("calculated_emissions_kg_co2e") is not None
            else None
        ),
        emission_factor_used=_uid(r.get("emission_factor_used")),
        extracted_by=_uid(r.get("extracted_by")),
        extracted_at=r.get("extracted_at"),
        qc_by=_uid(r.get("qc_by")),
        qc_at=r.get("qc_at"),
        qc_notes=r.get("qc_notes"),
        quality_score=r.get("quality_score"),
        customer_reviewed_by=_uid(r.get("customer_reviewed_by")),
        customer_reviewed_at=r.get("customer_reviewed_at"),
        customer_approved=r.get("customer_approved"),
        customer_rejection_reason=r.get("customer_rejection_reason"),
        customer_notes=r.get("customer_notes"),
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
    )


class ManualExtractionRepository(AbstractRepository[dict]):
    """Manual-extraction batches, items and the QC surface."""

    # -- batches -----------------------------------------------------------
    async def create_batch(
        self,
        org_id: str,
        batch_name: str,
        total_documents: int,
        total_pages: int,
        total_cost: float,
        currency: str,
        batch_description: Optional[str],
        price_per_page: Optional[float],
        created_by: Optional[str],
        entity_id: Optional[str] = None,
    ) -> ManualExtractionBatch:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.manual_extraction_batches (
                organization_id, batch_name, batch_description, entity_id,
                total_documents, total_pages, total_cost, price_per_page, currency,
                status, created_at, updated_at, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'open', NOW(), NOW(), $10)
            RETURNING {_BATCH_COLUMNS}
            """,
            org_id,
            batch_name,
            batch_description,
            entity_id,
            total_documents,
            total_pages,
            total_cost,
            price_per_page,
            currency,
            created_by,
        )
        if row is None:
            raise RuntimeError("manual_extraction_batches insert returned no row")
        return _row_to_batch(row)

    async def get_batch(self, batch_id: str) -> Optional[ManualExtractionBatch]:
        row = await self._fetch_one(
            f"SELECT {_BATCH_COLUMNS} FROM public.manual_extraction_batches WHERE id = $1",
            batch_id,
        )
        return _row_to_batch(row) if row is not None else None

    async def list_batches(self, org_id: str) -> list[ManualExtractionBatch]:
        rows = await self._fetch_all(
            f"SELECT {_BATCH_COLUMNS} FROM public.manual_extraction_batches "
            "WHERE organization_id = $1 ORDER BY created_at DESC",
            org_id,
        )
        return [_row_to_batch(r) for r in rows]

    async def list_batches_with_counts(self, org_id: str) -> list[dict]:
        """Batch list enriched with the authoritative per-batch item count.

        The count comes from the real ``manual_extraction_items`` rows via a
        scalar subquery (no extra N+1 queries, no duplicated state). The batch
        fields match ``list_batches`` plus ``item_count``.
        """
        query = (
            f"SELECT {_BATCH_COLUMNS}, "
            "(SELECT COUNT(*) FROM public.manual_extraction_items i "
            " WHERE i.batch_id = b.id) AS item_count "
            "FROM public.manual_extraction_batches b "
            "WHERE b.organization_id = $1 ORDER BY b.created_at DESC"
        )
        rows = await self._fetch_all(query, org_id)
        out: list[dict] = []
        for row in rows:
            batch = _row_to_batch(row)
            out.append({**asdict(batch), "item_count": int(row["item_count"])})
        return out

    # -- items -------------------------------------------------------------
    async def update_batch(
        self,
        batch_id: str,
        *,
        status: Optional[str] = None,
        assigned_to: Any = _UNSET,
        assigned_by: Optional[str] = None,
        entity_id: Any = _UNSET,
        customer_notes: Optional[str] = None,
        staff_notes: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> Optional[ManualExtractionBatch]:
        """Update mutable batch fields; stamps assignment/updated timestamps.

        ``assigned_to`` / ``entity_id`` accept ``None`` to clear the column
        (reassignment back to CarbonTally / to an internal operator) and
        :data:`_UNSET` to leave it untouched. Exactly one processing party
        (entity_id XOR assigned_to) is the API-layer invariant.
        """
        sets = ["updated_at = NOW()"]
        args: list[Any] = [batch_id]
        if status is not None:
            sets.append(f"status = ${len(args) + 1}")
            args.append(status)
        if assigned_to is not _UNSET:
            sets.append(f"assigned_to = ${len(args) + 1}")
            args.append(assigned_to)
        if assigned_by is not None:
            sets.append(f"assigned_by = ${len(args) + 1}")
            args.append(assigned_by)
        if entity_id is not _UNSET:
            sets.append(f"entity_id = ${len(args) + 1}")
            args.append(entity_id)
        if customer_notes is not None:
            sets.append(f"customer_notes = ${len(args) + 1}")
            args.append(customer_notes)
        if staff_notes is not None:
            sets.append(f"staff_notes = ${len(args) + 1}")
            args.append(staff_notes)
        if updated_by is not None:
            sets.append(f"updated_by = ${len(args) + 1}")
            args.append(updated_by)
        if assigned_to is not _UNSET or entity_id is not _UNSET or status == "in_progress":
            sets.append("assigned_at = COALESCE(assigned_at, NOW())")
        row = await self._fetch_one(
            f"UPDATE public.manual_extraction_batches SET {', '.join(sets)} "
            f"WHERE id = $1 RETURNING {_BATCH_COLUMNS}",
            *args,
        )
        return _row_to_batch(row) if row is not None else None

    async def complete_batch(
        self, batch_id: str, completed_by: str
    ) -> Optional[ManualExtractionBatch]:
        """Close a batch: ``completed`` with completion stamps."""
        row = await self._fetch_one(
            f"""
            UPDATE public.manual_extraction_batches
            SET status = 'completed', completed_by = $2, completed_at = NOW(),
                actual_completion_date = NOW(), updated_at = NOW(), updated_by = $2
            WHERE id = $1
            RETURNING {_BATCH_COLUMNS}
            """,
            batch_id,
            completed_by,
        )
        return _row_to_batch(row) if row is not None else None

    async def cancel_batch(
        self, batch_id: str, updated_by: str
    ) -> Optional[ManualExtractionBatch]:
        """Cancel a batch (terminal state; items are left untouched)."""
        row = await self._fetch_one(
            f"""
            UPDATE public.manual_extraction_batches
            SET status = 'cancelled', updated_at = NOW(), updated_by = $2
            WHERE id = $1
            RETURNING {_BATCH_COLUMNS}
            """,
            batch_id,
            updated_by,
        )
        return _row_to_batch(row) if row is not None else None

    async def batch_progress(self, batch_id: str) -> Optional[dict]:
        """Return the batch plus per-status / per-stage item counts."""
        batch = await self.get_batch(batch_id)
        if batch is None:
            return None
        rows = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_extraction_items "
            "WHERE batch_id = $1 GROUP BY status",
            batch_id,
        )
        by_status = {str(r["status"]): int(r["n"]) for r in rows}
        total = sum(by_status.values())
        stages: dict[str, int] = {}
        for stage, statuses in WORKFLOW_STAGE_STATUSES.items():
            stages[stage] = sum(by_status.get(s, 0) for s in statuses)
        done = by_status.get("approved", 0) + by_status.get("qc_approved", 0)
        return {
            "batch": batch,
            "total_items": total,
            "by_status": by_status,
            "by_stage": stages,
            "pct_complete": round(done / total * 100, 2) if total else 0.0,
        }

    async def create_item(
        self,
        batch_id: str,
        file_name: str,
        file_url: str,
        page_count: int,
        document_type: Optional[str],
        status: str,
        file_id: Optional[str] = None,
    ) -> ManualExtractionItem:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.manual_extraction_items (
                batch_id, file_name, file_url, page_count, document_type, status, file_id, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            RETURNING {_ITEM_COLUMNS}
            """,
            batch_id,
            file_name,
            file_url,
            page_count,
            document_type,
            status,
            file_id,
        )
        if row is None:
            raise RuntimeError("manual_extraction_items insert returned no row")
        return _row_to_item(row)

    async def list_items(self, batch_id: str) -> list[ManualExtractionItem]:
        rows = await self._fetch_all(
            f"SELECT {_ITEM_COLUMNS} FROM public.manual_extraction_items "
            "WHERE batch_id = $1 ORDER BY created_at",
            batch_id,
        )
        return [_row_to_item(r) for r in rows]

    async def get_item(self, item_id: str) -> Optional[ManualExtractionItem]:
        row = await self._fetch_one(
            f"SELECT {_ITEM_COLUMNS} FROM public.manual_extraction_items WHERE id = $1",
            item_id,
        )
        return _row_to_item(row) if row is not None else None

    async def update_item(
        self,
        item_id: str,
        extracted_data: Optional[dict],
        mapped_data: Optional[dict],
        calculated_emissions_kg_co2e: Optional[float],
        extracted_by: Optional[str],
    ) -> Optional[ManualExtractionItem]:
        row = await self._fetch_one(
            f"""
            UPDATE public.manual_extraction_items
            SET extracted_data = COALESCE($2, extracted_data),
                mapped_data = COALESCE($3, mapped_data),
                calculated_emissions_kg_co2e = COALESCE($4, calculated_emissions_kg_co2e),
                extracted_by = COALESCE($5, extracted_by),
                status = 'extracted', updated_at = NOW()
            WHERE id = $1
            RETURNING {_ITEM_COLUMNS}
            """,
            item_id,
            dumps_jsonb(extracted_data) if extracted_data is not None else None,
            dumps_jsonb(mapped_data) if mapped_data is not None else None,
            calculated_emissions_kg_co2e,
            extracted_by,
        )
        return _row_to_item(row) if row is not None else None

    # -- workflow (pipeline stage transitions) ------------------------------
    async def save_extracted_data(
        self,
        item_id: str,
        extracted_data: dict,
        extracted_by: str,
    ) -> Optional[ManualExtractionItem]:
        """Persist extraction output (data-entry save) and advance to ``extracted``."""
        row = await self._fetch_one(
            f"""
            UPDATE public.manual_extraction_items
            SET extracted_data = $2, extracted_by = $3, extracted_at = NOW(),
                status = 'extracted', updated_at = NOW()
            WHERE id = $1
            RETURNING {_ITEM_COLUMNS}
            """,
            item_id,
            dumps_jsonb(extracted_data),
            extracted_by,
        )
        return _row_to_item(row) if row is not None else None

    async def save_mapped_data(
        self,
        item_id: str,
        mapped_data: dict,
        mapped_facility_id: Optional[str],
        mapped_asset_id: Optional[str],
        mapped_supplier_id: Optional[str],
        emission_factor_used: Optional[str],
    ) -> Optional[ManualExtractionItem]:
        """Persist mapping decisions and advance to ``mapped``."""
        row = await self._fetch_one(
            f"""
            UPDATE public.manual_extraction_items
            SET mapped_data = $2, mapped_facility_id = $3, mapped_asset_id = $4,
                mapped_supplier_id = $5, emission_factor_used = $6,
                status = 'mapped', updated_at = NOW()
            WHERE id = $1
            RETURNING {_ITEM_COLUMNS}
            """,
            item_id,
            dumps_jsonb(mapped_data),
            mapped_facility_id,
            mapped_asset_id,
            mapped_supplier_id,
            emission_factor_used,
        )
        return _row_to_item(row) if row is not None else None

    async def save_calculation(
        self,
        item_id: str,
        calculated_emissions_kg_co2e: float,
        mapped_data: Optional[dict] = None,
    ) -> Optional[ManualExtractionItem]:
        """Persist the calculated result (and per-line mapping results when
        provided) and advance to ``calculated`` (D23 multi-line support)."""
        if mapped_data is not None:
            row = await self._fetch_one(
                f"""
                UPDATE public.manual_extraction_items
                SET calculated_emissions_kg_co2e = $2, mapped_data = $3,
                    status = 'calculated', updated_at = NOW()
                WHERE id = $1
                RETURNING {_ITEM_COLUMNS}
                """,
                item_id,
                calculated_emissions_kg_co2e,
                dumps_jsonb(mapped_data),
            )
        else:
            row = await self._fetch_one(
                f"""
                UPDATE public.manual_extraction_items
                SET calculated_emissions_kg_co2e = $2, status = 'calculated',
                    updated_at = NOW()
                WHERE id = $1
                RETURNING {_ITEM_COLUMNS}
                """,
                item_id,
                calculated_emissions_kg_co2e,
            )
        return _row_to_item(row) if row is not None else None

    async def set_item_status(
        self,
        item_id: str,
        status: str,
    ) -> Optional[ManualExtractionItem]:
        """Advance an item to ``status`` (transition authority enforced by the API)."""
        row = await self._fetch_one(
            f"""
            UPDATE public.manual_extraction_items
            SET status = $2, updated_at = NOW()
            WHERE id = $1
            RETURNING {_ITEM_COLUMNS}
            """,
            item_id,
            status,
        )
        return _row_to_item(row) if row is not None else None

    async def customer_review(
        self,
        item_id: str,
        approved: bool,
        reviewer: str,
        rejection_reason: Optional[str],
        customer_notes: Optional[str],
    ) -> Optional[ManualExtractionItem]:
        """Record a customer verification decision on an item."""
        row = await self._fetch_one(
            f"""
            UPDATE public.manual_extraction_items
            SET customer_approved = $2, customer_reviewed_by = $3,
                customer_reviewed_at = NOW(),
                customer_rejection_reason = $4, customer_notes = $5,
                status = $6, updated_at = NOW()
            WHERE id = $1
            RETURNING {_ITEM_COLUMNS}
            """,
            item_id,
            approved,
            reviewer,
            rejection_reason,
            customer_notes,
            "approved" if approved else "rejected",
        )
        return _row_to_item(row) if row is not None else None

    # -- queues / dashboards ------------------------------------------------
    async def list_items_for_org(
        self, org_id: str, status: Optional[str] = None
    ) -> list[ManualExtractionItem]:
        query = (
            f"SELECT {_ITEM_COLUMNS} FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE b.organization_id = $1"
        )
        args: list[Any] = [org_id]
        if status is not None:
            args.append(status)
            query += f" AND i.status = ${len(args)}"
        query += " ORDER BY i.created_at"
        rows = await self._fetch_all(query, *args)
        return [_row_to_item(r) for r in rows]

    async def list_by_stage(
        self, org_id: str, stage: str, limit: int = 100
    ) -> list[ManualExtractionItem]:
        statuses = WORKFLOW_STAGE_STATUSES.get(stage)
        if statuses is None:
            return []
        rows = await self._fetch_all(
            f"SELECT {_ITEM_COLUMNS} FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE b.organization_id = $1 AND i.status = ANY($2::text[]) "
            "ORDER BY i.created_at LIMIT $3",
            org_id,
            list(statuses),
            int(limit),
        )
        return [_row_to_item(r) for r in rows]

    async def next_item(
        self, org_id: str, stage: str, exclude_item_id: Optional[str] = None
    ) -> Optional[ManualExtractionItem]:
        """Return the next item awaiting ``stage`` work (oldest first)."""
        statuses = WORKFLOW_STAGE_STATUSES.get(stage)
        if statuses is None:
            return None
        query = (
            f"SELECT {_ITEM_COLUMNS} FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE b.organization_id = $1 AND i.status = ANY($2::text[]) "
            "AND b.status <> 'cancelled'"
        )
        args: list[Any] = [org_id, list(statuses)]
        if exclude_item_id is not None:
            args.append(exclude_item_id)
            query += f" AND i.id <> ${len(args)}"
        query += " ORDER BY i.created_at LIMIT 1"
        row = await self._fetch_one(query, *args)
        return _row_to_item(row) if row is not None else None

    async def list_customer_review(self, org_id: str) -> list[ManualExtractionItem]:
        """Items awaiting customer verification (``customer_review`` stage)."""
        return await self.list_by_stage(org_id, "review")

    async def get_item_org(self, item_id: str) -> Optional[str]:
        """Resolve the owning organisation of an item (via its batch)."""
        row = await self._fetch_one(
            "SELECT b.organization_id FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE i.id = $1",
            item_id,
        )
        return str(row["organization_id"]) if row is not None else None

    async def count_qc_pending(self, org_id: str) -> int:
        """Count items awaiting QC for one organisation."""
        row = await self._fetch_one(
            "SELECT COUNT(*) AS n FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE b.organization_id = $1 AND i.status = 'extracted' "
            "AND i.quality_score IS NULL",
            org_id,
        )
        return int(row["n"]) if row is not None else 0

    async def workflow_dashboard(self, org_id: str) -> dict:
        """Aggregate pipeline + queue counts for one organisation."""
        batch_rows = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_extraction_batches "
            "WHERE organization_id = $1 GROUP BY status",
            org_id,
        )
        batches_by_status = {str(r["status"]): int(r["n"]) for r in batch_rows}
        item_rows = await self._fetch_all(
            "SELECT i.status AS status, COUNT(*) AS n "
            "FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE b.organization_id = $1 GROUP BY i.status",
            org_id,
        )
        items_by_status = {str(r["status"]): int(r["n"]) for r in item_rows}
        total_items = sum(items_by_status.values())
        stages = {
            stage: sum(items_by_status.get(s, 0) for s in statuses)
            for stage, statuses in WORKFLOW_STAGE_STATUSES.items()
        }
        done = items_by_status.get("approved", 0) + items_by_status.get(
            "qc_approved", 0
        )
        return {
            "organization_id": org_id,
            "batches": {
                "total": sum(batches_by_status.values()),
                "by_status": batches_by_status,
            },
            "items": {
                "total": total_items,
                "by_status": items_by_status,
                "by_stage": stages,
                "pct_complete": round(done / total_items * 100, 2)
                if total_items
                else 0.0,
            },
            "queues": {
                "qc_pending": await self.count_qc_pending(org_id),
                "customer_review": items_by_status.get("customer_review", 0),
            },
        }

    async def workflow_status(self, org_id: str) -> dict:
        """Summarise the pipeline state (stage counts + active batches)."""
        dashboard = await self.workflow_dashboard(org_id)
        return {
            "organization_id": org_id,
            "pipeline": dashboard["items"]["by_stage"],
            "item_status_counts": dashboard["items"]["by_status"],
            "total_items": dashboard["items"]["total"],
            "pct_complete": dashboard["items"]["pct_complete"],
            "active_batches": (
                dashboard["batches"]["by_status"].get("in_progress", 0)
                + dashboard["batches"]["by_status"].get("open", 0)
            ),
        }

    # -- operations (Phase 8) ------------------------------------------------

    async def ops_dashboard_all(self) -> dict:
        """Global pipeline aggregates across every organisation.

        Computed in SQL over the live ``manual_extraction_batches`` /
        ``manual_extraction_items`` rows. Used by the CarbonTally operations
        dashboard (staff, ``can_view_all``). No fabricated statistics.
        """
        batches_by_status = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_extraction_batches "
            "GROUP BY status ORDER BY status"
        )
        items_by_status = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_extraction_items "
            "GROUP BY status ORDER BY status"
        )
        item_rows = [
            {"status": str(r["status"]), "n": int(r["n"])} for r in items_by_status
        ]
        by_status = {r["status"]: r["n"] for r in item_rows}
        stages = {
            stage: sum(by_status.get(s, 0) for s in statuses)
            for stage, statuses in WORKFLOW_STAGE_STATUSES.items()
        }
        total_items = sum(by_status.values())
        return {
            "batches": {
                "total": sum(int(r["n"]) for r in batches_by_status),
                "by_status": {
                    str(r["status"]): int(r["n"]) for r in batches_by_status
                },
            },
            "items": {
                "total": total_items,
                "by_status": by_status,
                "by_stage": stages,
                "pct_complete": round(
                    (by_status.get("approved", 0) + by_status.get("qc_approved", 0))
                    / total_items * 100, 2
                )
                if total_items
                else 0.0,
            },
            "queues": {
                "qc_pending": len(await self.list_qc_pending()),
                "customer_review": by_status.get("customer_review", 0),
            },
        }

    async def list_operator_batches(
        self, staff_user_id: str, status: Optional[str] = None
    ) -> list[ManualExtractionBatch]:
        """Batches assigned to the operator OR open/unassigned (self-serve).

        Assignment model (real columns): ``manual_extraction_batches.assigned_to``
        is the operator identity; ``NULL`` + open status = unassigned queue work.
        Batches allocated to a Processing Entity (``entity_id IS NOT NULL``) are
        that entity's work — never shown in the internal operator queue
        (D22 single-active-assignment; reassignment is the explicit return path).
        """
        query = (
            f"SELECT {_BATCH_COLUMNS} FROM public.manual_extraction_batches "
            "WHERE entity_id IS NULL "
            "AND (assigned_to = $1 "
            "   OR (assigned_to IS NULL AND status IN ('open', 'in_progress')))"
        )
        if status is not None:
            query += " AND status = $2"
            rows = await self._fetch_all(query + " ORDER BY assigned_at NULLS LAST, created_at", staff_user_id, status)
        else:
            rows = await self._fetch_all(query + " ORDER BY assigned_at NULLS LAST, created_at", staff_user_id)
        return [_row_to_batch(r) for r in rows]

    async def next_operator_item(
        self,
        staff_user_id: str,
        stage: str,
        exclude_item_id: Optional[str] = None,
    ) -> Optional[ManualExtractionItem]:
        """Return the next item awaiting ``stage`` work in the operator's
        assigned (or unassigned open) batches.

        Stage statuses come from the workflow vocabulary
        (:data:`domain.partners.WORKFLOW_STAGE_STATUSES`).
        """
        statuses = WORKFLOW_STAGE_STATUSES.get(stage)
        if statuses is None:
            return None
        query = (
            f"SELECT i.{_ITEM_COLUMNS.replace(', ', ', i.')} "
            "FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE i.status = ANY($2::text[]) "
            "AND b.entity_id IS NULL "
            "AND (b.assigned_to = $1 "
            "     OR (b.assigned_to IS NULL AND b.status IN ('open', 'in_progress'))) "
            "AND (i.id IS DISTINCT FROM $3::uuid) "
            "ORDER BY b.assigned_at NULLS LAST, b.created_at, i.created_at "
            "LIMIT 1"
        )
        row = await self._fetch_one(query, staff_user_id, list(statuses), exclude_item_id)
        return _row_to_item(row) if row is not None else None

    # -- entity extraction workspace (D22) -----------------------------------
    async def list_entity_batches(
        self, entity_id: str, status: Optional[str] = None
    ) -> list[ManualExtractionBatch]:
        """Batches allocated to ``entity_id`` (the entity's assigned work)."""
        query = (
            f"SELECT {_BATCH_COLUMNS} FROM public.manual_extraction_batches "
            "WHERE entity_id = $1"
        )
        if status is not None:
            query += " AND status = $2"
            rows = await self._fetch_all(query + " ORDER BY created_at DESC", entity_id, status)
        else:
            rows = await self._fetch_all(query + " ORDER BY created_at DESC", entity_id)
        return [_row_to_batch(r) for r in rows]

    async def list_entity_items(
        self,
        entity_id: str,
        stage: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[ManualExtractionItem]:
        """Items belonging to ``entity_id``'s batches (optionally by stage)."""
        query = (
            f"SELECT i.{_ITEM_COLUMNS.replace(', ', ', i.')} "
            "FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE b.entity_id = $1"
        )
        args: list[Any] = [entity_id]
        if stage is not None:
            statuses = WORKFLOW_STAGE_STATUSES.get(stage)
            if statuses is None:
                return []
            args.append(list(statuses))
            query += f" AND i.status = ANY(${len(args)}::text[])"
        elif status is not None:
            args.append(status)
            query += f" AND i.status = ${len(args)}"
        query += " ORDER BY b.created_at, i.created_at"
        rows = await self._fetch_all(query, *args)
        return [_row_to_item(r) for r in rows]

    async def next_entity_item(
        self,
        entity_id: str,
        stage: str,
        exclude_item_id: Optional[str] = None,
    ) -> Optional[ManualExtractionItem]:
        """Return the next item awaiting ``stage`` work in the entity's batches."""
        statuses = WORKFLOW_STAGE_STATUSES.get(stage)
        if statuses is None:
            return None
        query = (
            f"SELECT i.{_ITEM_COLUMNS.replace(', ', ', i.')} "
            "FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE b.entity_id = $1 AND i.status = ANY($2::text[]) "
            "AND b.status <> 'cancelled' "
            "AND (i.id IS DISTINCT FROM $3::uuid) "
            "ORDER BY b.created_at, i.created_at "
            "LIMIT 1"
        )
        row = await self._fetch_one(query, entity_id, list(statuses), exclude_item_id)
        return _row_to_item(row) if row is not None else None

    async def entity_workflow_dashboard(self, entity_id: str) -> dict:
        """Pipeline aggregates for one processing entity's assigned batches."""
        batch_rows = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_extraction_batches "
            "WHERE entity_id = $1 GROUP BY status",
            entity_id,
        )
        batches_by_status = {str(r["status"]): int(r["n"]) for r in batch_rows}
        item_rows = await self._fetch_all(
            "SELECT i.status AS status, COUNT(*) AS n "
            "FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE b.entity_id = $1 GROUP BY i.status",
            entity_id,
        )
        items_by_status = {str(r["status"]): int(r["n"]) for r in item_rows}
        total_items = sum(items_by_status.values())
        stages = {
            stage: sum(items_by_status.get(s, 0) for s in statuses)
            for stage, statuses in WORKFLOW_STAGE_STATUSES.items()
        }
        done = items_by_status.get("approved", 0) + items_by_status.get(
            "qc_approved", 0
        )
        return {
            "entity_id": entity_id,
            "batches": {
                "total": sum(batches_by_status.values()),
                "by_status": batches_by_status,
            },
            "items": {
                "total": total_items,
                "by_status": items_by_status,
                "by_stage": stages,
                "pct_complete": round(done / total_items * 100, 2)
                if total_items
                else 0.0,
            },
            "queues": {
                "qc_pending": items_by_status.get("extracted", 0),
                "customer_review": items_by_status.get("customer_review", 0),
            },
        }

    # -- QC -----------------------------------------------------------------
    async def list_qc_pending(self) -> list[ManualExtractionItem]:
        rows = await self._fetch_all(
            f"SELECT {_ITEM_COLUMNS} FROM public.manual_extraction_items "
            "WHERE status = 'extracted' AND quality_score IS NULL "
            "ORDER BY created_at"
        )
        return [_row_to_item(r) for r in rows]

    async def qc_review(
        self,
        item_id: str,
        quality_score: int,
        qc_notes: Optional[str],
        qc_by: str,
        approved: bool,
    ) -> Optional[ManualExtractionItem]:
        row = await self._fetch_one(
            f"""
            UPDATE public.manual_extraction_items
            SET quality_score = $2, qc_notes = $3, qc_by = $4, qc_at = NOW(),
                status = $5, updated_at = NOW()
            WHERE id = $1
            RETURNING {_ITEM_COLUMNS}
            """,
            item_id,
            quality_score,
            qc_notes,
            qc_by,
            "qc_approved" if approved else "qc_rejected",
        )
        return _row_to_item(row) if row is not None else None

    async def get(self, id: str):
        return await self.get_item(id)

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        return None

