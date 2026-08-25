"""D30 — Reporting repository (read-only aggregates).

Every metric is computed in SQL from the LIVE CarbonTally tables (no derived
summary tables, no analytics warehouse, no N+1 loops). The repository returns
grouped rows; the API layer composes the response. Authorization is NOT
enforced here — the API layer guards each endpoint with the existing
org / staff / consultant / entity dependencies (D15/D20/D22 stay authoritative).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from data.base import AbstractRepository

#: Persisted item statuses -> workflow stage bucket (authoritative source:
#: ``domain.partners.WORKFLOW_STAGE_STATUSES``).
STAGE_BY_STATUS: dict[str, str] = {
    "pending": "source",
    "extracting": "extraction",
    "extracted": "extraction",
    "mapping": "mapping",
    "mapped": "mapping",
    "validating": "validation",
    "validated": "validation",
    "calculating": "calculation",
    "calculated": "calculation",
    "customer_review": "review",
    "approved": "approval",
    "rejected": "approval",
    "qc_approved": "qc",
    "qc_rejected": "qc",
}

#: Terminal stages counted as "completed" for progress.
COMPLETED_STAGES: frozenset[str] = frozenset({"approval", "qc"})

#: Persisted report-queue statuses.
REPORT_STATUSES: tuple[str, ...] = ("pending", "generating", "completed", "failed")


def stage_distribution(status_rows: list[Any]) -> dict[str, int]:
    """Bucket item rows by workflow stage (pure helper — unit-testable)."""
    counts = {stage: 0 for stage in STAGE_BY_STATUS.values()}
    for row in status_rows:
        status = str(row.get("status") or "pending")
        counts[STAGE_BY_STATUS.get(status, "source")] += 1
    return counts


def completed_ratio(stage_counts: dict[str, int]) -> float:
    total = sum(stage_counts.values())
    if total == 0:
        return 0.0
    done = sum(v for k, v in stage_counts.items() if k in COMPLETED_STAGES)
    return round(done / total * 100, 1)


def coerce_float(value: Any) -> float:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


class ReportingRepository(AbstractRepository[dict]):
    """Read-only aggregate queries for dashboards and reports."""

    async def get(self, id: str):
        """Read-only repository — identity access is not applicable."""
        return None

    async def save(self, entity: dict) -> dict:
        """Read-only repository — persistence is not applicable."""
        return entity

    async def delete(self, id: str) -> None:
        """Read-only repository — deletion is not applicable."""
        return None

    async def emissions_summary(
        self,
        org_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> dict[str, Any]:
        args: list[Any] = [org_id]
        where = ["organization_id = $1"]
        if start_date:
            args.append(start_date)
            where.append(f"start_date >= ${len(args)}")
        if end_date:
            args.append(end_date)
            where.append(f"end_date <= ${len(args)}")
        if scope:
            args.append(scope)
            where.append(f"scope = ${len(args)}")
        clause = " AND ".join(where)

        total = await self._fetch_one(
            f"SELECT COALESCE(SUM(calculated_kg_co2e),0)::float8 AS total, "
            f"COUNT(*) AS n FROM public.emissions_logs WHERE {clause}",
            *args,
        )
        by_scope = await self._fetch_all(
            f"SELECT scope, COALESCE(SUM(calculated_kg_co2e),0)::float8 AS total, "
            f"COUNT(*) AS n FROM public.emissions_logs WHERE {clause} "
            f"GROUP BY scope ORDER BY scope",
            *args,
        )
        by_month = await self._fetch_all(
            f"SELECT to_char(start_date, 'YYYY-MM') AS month, "
            f"COALESCE(SUM(calculated_kg_co2e),0)::float8 AS total, COUNT(*) AS n "
            f"FROM public.emissions_logs WHERE {clause} "
            f"GROUP BY 1 ORDER BY 1",
            *args,
        )
        return {
            "total_kg": coerce_float(total["total"]) if total else 0.0,
            "row_count": int(total["n"]) if total else 0,
            "by_scope": [
                {"scope": str(r["scope"]), "kg": coerce_float(r["total"]), "rows": int(r["n"])}
                for r in by_scope
            ],
            "by_month": [
                {"month": str(r["month"]), "kg": coerce_float(r["total"]), "rows": int(r["n"])}
                for r in by_month
            ],
        }

    async def document_summary(self, org_id: str) -> dict[str, Any]:
        files = await self._fetch_all(
            "SELECT COUNT(*) AS n FROM public.organization_files "
            "WHERE organization_id = $1 AND is_active = TRUE AND deleted_at IS NULL",
            org_id,
        )
        queue = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.document_processing_queue "
            "WHERE organization_id = $1 GROUP BY status ORDER BY status",
            org_id,
        )
        errors = await self._fetch_all(
            "SELECT COUNT(*) AS n FROM public.document_processing_queue "
            "WHERE organization_id = $1 AND COALESCE(workflow_error_count,0) > 0",
            org_id,
        )
        by_status = {str(r["status"]): int(r["n"]) for r in queue}
        processed = sum(
            v for k, v in by_status.items() if k in ("completed", "approved", "qc_approved", "calculated")
        )
        pending = sum(v for k, v in by_status.items() if k in ("pending", "uploaded", "queued"))
        return {
            "total_documents": int(files[0]["n"]) if files else 0,
            "processing_by_status": by_status,
            "processed": processed,
            "pending": pending,
            "requiring_attention": int(errors[0]["n"]) if errors else 0,
        }

    async def processing_summary(self, org_id: str) -> dict[str, Any]:
        batches = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_extraction_batches "
            "WHERE organization_id = $1 GROUP BY status ORDER BY status",
            org_id,
        )
        items = await self._fetch_all(
            "SELECT i.status, COUNT(*) AS n "
            "FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE b.organization_id = $1 "
            "GROUP BY i.status ORDER BY i.status",
            org_id,
        )
        mapped = await self._fetch_all(
            "SELECT COUNT(*) AS n "
            "FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE b.organization_id = $1 "
            "AND (i.mapped_facility_id IS NOT NULL OR i.mapped_asset_id IS NOT NULL "
            "OR i.mapped_supplier_id IS NOT NULL)",
            org_id,
        )
        total_items = await self._fetch_one(
            "SELECT COUNT(*) AS n "
            "FROM public.manual_extraction_items i "
            "JOIN public.manual_extraction_batches b ON b.id = i.batch_id "
            "WHERE b.organization_id = $1",
            org_id,
        )
        batch_by_status = {str(r["status"]): int(r["n"]) for r in batches}
        stage_counts = stage_distribution(items)
        total = int(total_items["n"]) if total_items else 0
        return {
            "batches": {"total": sum(batch_by_status.values()), "by_status": batch_by_status},
            "items": {
                "total": total,
                "by_stage": stage_counts,
                "mapped": int(mapped[0]["n"]) if mapped else 0,
                "unmapped": max(total - (int(mapped[0]["n"]) if mapped else 0), 0),
                "complete_pct": completed_ratio(stage_counts),
            },
        }

    async def issues_summary(self, org_id: str) -> dict[str, Any]:
        rows = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.issues "
            "WHERE organization_id = $1 GROUP BY status ORDER BY status",
            org_id,
        )
        open_sla = await self._fetch_all(
            "SELECT COUNT(*) AS n FROM public.issues "
            "WHERE organization_id = $1 AND status = 'open' AND sla_breached = TRUE",
            org_id,
        )
        by_status = {str(r["status"]): int(r["n"]) for r in rows}
        return {
            "by_status": by_status,
            "open": by_status.get("open", 0),
            "sla_breached_open": int(open_sla[0]["n"]) if open_sla else 0,
        }

    async def report_summary(self, org_id: str) -> dict[str, Any]:
        rows = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.report_generation_queue "
            "WHERE organization_id = $1 GROUP BY status ORDER BY status",
            org_id,
        )
        return {str(r["status"]): int(r["n"]) for r in rows}

    async def consultant_portfolio(self, consultant_id: str) -> list[dict]:
        """Per-client aggregates for the consultant's OWN client grants.

        ``consultant_id`` is the caller's consultant profile id. Ended
        relationships are counted by the API layer but excluded from the
        detailed list (they carry no active access — D15).
        """
        return await self._fetch_all(
            """
            SELECT c.id AS client_id, c.organization_id, c.client_name,
                   c.client_industry, c.status,
                   (SELECT COUNT(*) FROM public.organization_files f
                     WHERE f.organization_id = c.organization_id
                       AND f.is_active = TRUE AND f.deleted_at IS NULL) AS documents,
                   (SELECT COUNT(*) FROM public.manual_extraction_items i
                     JOIN public.manual_extraction_batches b ON b.id = i.batch_id
                    WHERE b.organization_id = c.organization_id) AS items,
                   (SELECT COUNT(*) FROM public.issues iss
                     WHERE iss.organization_id = c.organization_id
                       AND iss.status = 'open') AS open_issues,
                   (SELECT COUNT(*) FROM public.report_generation_queue rq
                     WHERE rq.organization_id = c.organization_id
                       AND rq.status = 'completed') AS ready_reports
              FROM public.consultant_clients c
             WHERE c.consultant_id = $1
             ORDER BY c.client_name
            """,
            consultant_id,
        )

    async def platform_overview(self) -> dict[str, Any]:
        """CarbonTally platform-level aggregates (internal staff, can_view_all)."""
        orgs = await self._fetch_all("SELECT COUNT(*) AS n FROM public.organizations")
        entities = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.processing_entities "
            "GROUP BY status ORDER BY status"
        )
        staff = await self._fetch_all(
            "SELECT CASE WHEN entity_id IS NULL THEN 'internal' ELSE 'entity' END AS scope, "
            "COUNT(*) AS n FROM public.staff_profiles GROUP BY scope"
        )
        items_by_stage = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_extraction_items "
            "GROUP BY status ORDER BY status"
        )
        batches = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_extraction_batches "
            "GROUP BY status ORDER BY status"
        )
        failed = await self._fetch_all(
            "SELECT COUNT(*) AS n FROM public.manual_extraction_items "
            "WHERE status = 'rejected' OR status = 'qc_rejected'"
        )
        review = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_review_queue "
            "GROUP BY status ORDER BY status"
        )
        review_sla = await self._fetch_all(
            "SELECT COUNT(*) AS n FROM public.manual_review_queue WHERE sla_breached = TRUE"
        )
        issues = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.issues GROUP BY status ORDER BY status"
        )
        org_count = int(orgs[0]["n"]) if orgs else 0
        stage_counts = stage_distribution(items_by_stage)
        return {
            "platform": {
                "organizations": org_count,
                "processing_entities": {str(r["status"]): int(r["n"]) for r in entities},
                "staff": {str(r["scope"]): int(r["n"]) for r in staff},
            },
            "processing": {
                "batches_by_status": {str(r["status"]): int(r["n"]) for r in batches},
                "items_by_stage": stage_counts,
                "items_total": sum(stage_counts.values()),
                "items_complete_pct": completed_ratio(stage_counts),
                "failed_or_rejected": int(failed[0]["n"]) if failed else 0,
            },
            "quality": {
                "review_by_status": {str(r["status"]): int(r["n"]) for r in review},
                "review_sla_breached": int(review_sla[0]["n"]) if review_sla else 0,
                "issues_by_status": {str(r["status"]): int(r["n"]) for r in issues},
            },
        }

    async def review_reporting(self) -> dict[str, Any]:
        by_status = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_review_queue "
            "GROUP BY status ORDER BY status"
        )
        aging = await self._fetch_all(
            """
            SELECT CASE
                     WHEN created_at < NOW() - INTERVAL '7 days' THEN '7d+'
                     WHEN created_at < NOW() - INTERVAL '3 days' THEN '3-7d'
                     ELSE '0-3d'
                   END AS bucket, COUNT(*) AS n
              FROM public.manual_review_queue
             WHERE status NOT IN ('completed', 'approved', 'rejected')
             GROUP BY 1 ORDER BY 1
            """
        )
        sla = await self._fetch_all(
            "SELECT COUNT(*) AS n FROM public.manual_review_queue WHERE sla_breached = TRUE"
        )
        # D31 — reviewer workload (per reviewer: assigned/completed/pending/overdue).
        workload = await self._fetch_all(
            """
            SELECT COALESCE(p.first_name || ' ' || p.last_name, u.email) AS name,
                   COALESCE(p.id::text, r.assigned_to::text) AS reviewer_id,
                   COUNT(*) AS assigned,
                   COUNT(*) FILTER (WHERE r.status IN ('completed','approved')) AS completed,
                   COUNT(*) FILTER (WHERE r.status IN ('pending','in_review')) AS pending,
                   COUNT(*) FILTER (WHERE r.sla_breached = TRUE
                                    AND r.status NOT IN ('completed','approved','rejected')) AS overdue
              FROM public.manual_review_queue r
              LEFT JOIN public.staff_profiles p ON p.id = r.assigned_to
              LEFT JOIN public.users u ON u.id = r.assigned_to
             GROUP BY p.first_name, p.last_name, u.email, p.id, r.assigned_to
             ORDER BY assigned DESC
            """
        )
        # D31 — issues generated during review (type/severity/status/monthly trend).
        issues_by_type = await self._fetch_all(
            "SELECT COALESCE(issue_type, 'unknown') AS issue_type, COUNT(*) AS n "
            "FROM public.issues GROUP BY 1 ORDER BY 2 DESC"
        )
        issues_by_status = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.issues GROUP BY 1 ORDER BY 1"
        )
        issues_trend = await self._fetch_all(
            "SELECT to_char(created_at, 'YYYY-MM') AS month, COUNT(*) AS n "
            "FROM public.issues GROUP BY 1 ORDER BY 1"
        )
        return {
            "by_status": {str(r["status"]): int(r["n"]) for r in by_status},
            "aging": {str(r["bucket"]): int(r["n"]) for r in aging},
            "sla_breached": int(sla[0]["n"]) if sla else 0,
            "workload": [
                {
                    "name": str(r["name"]),
                    "reviewer_id": str(r["reviewer_id"]),
                    "assigned": int(r["assigned"]),
                    "completed": int(r["completed"]),
                    "pending": int(r["pending"]),
                    "overdue": int(r["overdue"]),
                }
                for r in workload
            ],
            "issues": {
                "by_type": {str(r["issue_type"]): int(r["n"]) for r in issues_by_type},
                "by_status": {str(r["status"]): int(r["n"]) for r in issues_by_status},
                "by_month": [
                    {"month": str(r["month"]), "n": int(r["n"])} for r in issues_trend
                ],
                # The schema has no blocking column on issues — blocking is a
                # workflow-derived concept (validate_processing_item findings).
                "blocking": None,
            },
        }

    async def qc_reporting(self) -> dict[str, Any]:
        outcomes = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_extraction_items "
            "WHERE status IN ('qc_approved','qc_rejected','approved','rejected') "
            "GROUP BY status ORDER BY status"
        )
        by_scope = await self._fetch_all(
            """
            SELECT CASE WHEN b.entity_id IS NULL THEN 'internal' ELSE 'entity' END AS scope,
                   i.status, COUNT(*) AS n
              FROM public.manual_extraction_items i
              LEFT JOIN public.manual_extraction_batches b ON b.id = i.batch_id
             WHERE i.status IN ('qc_approved','qc_rejected','approved','rejected')
             GROUP BY 1, 2 ORDER BY 1, 2
            """
        )
        quality = await self._fetch_all(
            "SELECT COALESCE(AVG(quality_score),0)::float8 AS avg_score, COUNT(*) AS n "
            "FROM public.manual_extraction_items WHERE quality_score IS NOT NULL"
        )
        # D31 — processor performance (internal vs entity) with sample sizes.
        per_scope = await self._fetch_all(
            """
            SELECT CASE WHEN b.entity_id IS NULL THEN 'internal' ELSE 'entity' END AS scope,
                   COUNT(*) AS completed,
                   COUNT(*) FILTER (WHERE i.status IN ('rejected','qc_rejected')) AS rejected,
                   COALESCE(AVG(i.quality_score), 0)::float8 AS avg_quality,
                   COUNT(i.quality_score) AS scored
              FROM public.manual_extraction_items i
              LEFT JOIN public.manual_extraction_batches b ON b.id = i.batch_id
             WHERE i.status IN ('qc_approved','qc_rejected','approved','rejected')
             GROUP BY 1 ORDER BY 1
            """
        )
        # D31 — recurring-quality marker: qc_checks/qc_errors are not populated
        # by the current workflow, so recurring-quality identification is
        # NOT SUPPORTED BY CURRENT DATA MODEL (documented, not invented).
        qc_errors_n = await self._fetch_one(
            "SELECT COUNT(*) AS n FROM public.qc_errors"
        )
        return {
            "outcomes": {str(r["status"]): int(r["n"]) for r in outcomes},
            "by_scope": [
                {"scope": str(r["scope"]), "status": str(r["status"]), "n": int(r["n"])}
                for r in by_scope
            ],
            "avg_quality_score": round(float(quality[0]["avg_score"]), 1) if quality else 0.0,
            "quality_scored_items": int(quality[0]["n"]) if quality else 0,
            "processor_performance": [
                {
                    "scope": str(r["scope"]),
                    "completed": int(r["completed"]),
                    "rejected": int(r["rejected"]),
                    "avg_quality": round(float(r["avg_quality"]), 1),
                    "scored": int(r["scored"]),
                    "sample_size": int(r["completed"]),
                    "rejection_rate_pct": round(
                        (int(r["rejected"]) / int(r["completed"]) * 100)
                        if int(r["completed"]) else 0.0,
                        1,
                    ),
                }
                for r in per_scope
            ],
            "recurring_quality": {
                "supported": int(qc_errors_n["n"]) > 0 if qc_errors_n else False,
                "source": "qc_errors",
                "note": (
                    "qc_errors is not populated by the current workflow; "
                    "recurring-quality identification is NOT SUPPORTED BY "
                    "CURRENT DATA MODEL."
                ),
            },
        }

    async def entity_performance(self, entity_id: str) -> dict[str, Any]:
        batches = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_extraction_batches "
            "WHERE entity_id = $1 GROUP BY status ORDER BY status",
            entity_id,
        )
        items = await self._fetch_all(
            """
            SELECT i.status, COUNT(*) AS n
              FROM public.manual_extraction_items i
              JOIN public.manual_extraction_batches b ON b.id = i.batch_id
             WHERE b.entity_id = $1
             GROUP BY i.status ORDER BY i.status
            """,
            entity_id,
        )
        # D31 — SLA state on the entity's assigned batches.
        sla_rows = await self._fetch_all(
            """
            SELECT COALESCE(sla_breached, FALSE) AS breached, COUNT(*) AS n
              FROM public.manual_extraction_batches
             WHERE entity_id = $1 AND status NOT IN ('completed', 'cancelled')
             GROUP BY 1
            """,
            entity_id,
        )
        overdue_rows = await self._fetch_all(
            """
            SELECT COUNT(*) AS n FROM public.manual_extraction_batches
             WHERE entity_id = $1 AND status NOT IN ('completed', 'cancelled')
               AND sla_deadline IS NOT NULL AND sla_deadline < NOW()
            """,
            entity_id,
        )
        # D31 — entity-visible quality indicators (own batches only).
        quality_rows = await self._fetch_all(
            """
            SELECT COUNT(*) AS completed,
                   COUNT(*) FILTER (WHERE i.status IN ('rejected','qc_rejected')) AS rejected,
                   COALESCE(AVG(i.quality_score), 0)::float8 AS avg_quality,
                   COUNT(i.quality_score) AS scored
              FROM public.manual_extraction_items i
              JOIN public.manual_extraction_batches b ON b.id = i.batch_id
             WHERE b.entity_id = $1
               AND i.status IN ('qc_approved','qc_rejected','approved','rejected')
            """,
            entity_id,
        )
        staff = await self._fetch_all(
            """
            SELECT p.first_name || ' ' || p.last_name AS name, p.id,
                   COUNT(i.id) AS assigned,
                   COUNT(i.id) FILTER (WHERE i.status IN ('approved','qc_approved','completed')) AS completed
              FROM public.staff_profiles p
              LEFT JOIN public.manual_extraction_items i
                ON i.extracted_by = p.id
              LEFT JOIN public.manual_extraction_batches b
                ON b.id = i.batch_id AND b.entity_id = $1
             WHERE p.entity_id = $1
             GROUP BY p.id, p.first_name, p.last_name
             ORDER BY p.first_name
            """,
            entity_id,
        )
        batch_by_status = {str(r["status"]): int(r["n"]) for r in batches}
        stage_counts = stage_distribution(items)
        q = quality_rows[0] if quality_rows else None
        completed = int(q["completed"]) if q else 0
        rejected = int(q["rejected"]) if q else 0
        sla_breached = sum(int(r["n"]) for r in sla_rows if r["breached"])
        return {
            "batches": {
                "total": sum(batch_by_status.values()),
                "by_status": batch_by_status,
                "sla_breached": sla_breached,
                "overdue": int(overdue_rows[0]["n"]) if overdue_rows else 0,
            },
            "items": {
                "total": sum(stage_counts.values()),
                "by_stage": stage_counts,
                "complete_pct": completed_ratio(stage_counts),
            },
            "quality": {
                "completed": completed,
                "rejected": rejected,
                "rejection_rate_pct": round(rejected / completed * 100, 1) if completed else 0.0,
                "avg_quality": round(float(q["avg_quality"]), 1) if q else 0.0,
                "scored": int(q["scored"]) if q else 0,
                "sample_size": completed,
            },
            "staff": [
                {
                    "id": str(r["id"]),
                    "name": str(r["name"]),
                    "assigned": int(r["assigned"]),
                    "completed": int(r["completed"]),
                }
                for r in staff
            ],
        }

    # ------------------------------------------------------------------
    # D31 — customer reporting
    # ------------------------------------------------------------------

    async def emissions_trend(self, org_id: str, months: int = 12) -> dict[str, Any]:
        """Zero-filled monthly emissions trend for the current org.

        Source: ``emissions_logs`` (``start_date``, ``calculated_kg_co2e``).
        Months with no rows are returned with ``kg = 0.0`` — no fabricated
        historical values.
        """
        months = max(1, min(int(months), 36))
        rows = await self._fetch_all(
            "SELECT to_char(start_date, 'YYYY-MM') AS month, "
            "COALESCE(SUM(calculated_kg_co2e),0)::float8 AS total, COUNT(*) AS n "
            "FROM public.emissions_logs "
            "WHERE organization_id = $1 "
            "AND start_date >= date_trunc('month', NOW()) - ($2 || ' months')::interval "
            "GROUP BY 1 ORDER BY 1",
            org_id,
            str(months - 1),
        )
        by_month = {str(r["month"]): (coerce_float(r["total"]), int(r["n"])) for r in rows}
        # Build the last `months` month keys (zero-filled).
        from datetime import date

        result: list[dict[str, Any]] = []
        today = date.today()
        for offset in range(months - 1, -1, -1):
            y, m = today.year, today.month
            total = y * 12 + (m - 1) - offset
            yy, mm = divmod(total, 12)
            key = f"{yy:04d}-{mm + 1:02d}"
            kg, n = by_month.get(key, (0.0, 0))
            result.append({"month": key, "kg": kg, "rows": n})
        return {"organization_id": org_id, "months": result}

    async def member_activity(self, org_id: str) -> list[dict]:
        """Management view of activity by organisation member.

        Derived from authoritative author columns (activity_logs-family tables
        are write-only / empty locally — see D31 doc):
        - documents uploaded   -> ``organization_files.uploaded_by``
        - extraction batches   -> ``manual_extraction_batches.created_by``
        - issues created/resolved -> ``issues.created_by`` / ``status``
        - emissions rows       -> ``emissions_logs.created_by_user_id``
        """
        return await self._fetch_all(
            """
            SELECT u.id AS user_id,
                   COALESCE(u.first_name || ' ' || u.last_name, u.email) AS name,
                   (SELECT COUNT(*) FROM public.organization_files f
                     WHERE f.organization_id = $1 AND f.uploaded_by = u.id
                       AND f.deleted_at IS NULL) AS documents_uploaded,
                   (SELECT COUNT(*) FROM public.issues i
                     WHERE i.organization_id = $1 AND i.created_by = u.id) AS issues_created,
                   (SELECT COUNT(*) FROM public.issues i
                     WHERE i.organization_id = $1 AND i.created_by = u.id
                       AND i.status = 'resolved') AS issues_resolved,
                   (SELECT COUNT(*) FROM public.manual_extraction_batches b
                     WHERE b.organization_id = $1 AND b.created_by = u.id) AS extraction_batches,
                   (SELECT COUNT(*) FROM public.emissions_logs e
                     WHERE e.organization_id = $1 AND e.created_by_user_id = u.id) AS emissions_rows
              FROM public.organization_members om
              JOIN public.users u ON u.id = om.user_id
             WHERE om.organization_id = $1 AND om.is_active = TRUE
             ORDER BY u.first_name, u.last_name
            """,
            org_id,
        )

    async def consultant_client_detail(
        self, consultant_id: str, client_id: str
    ) -> Optional[dict]:
        """Per-client drill-down for one ACTIVE client grant.

        Returns ``None`` when ``client_id`` is not one of the caller's client
        grants (the API layer turns that into 404 — no cross-consultant data).
        """
        rows = await self._fetch_all(
            """
            SELECT c.id AS client_id, c.organization_id, c.client_name,
                   c.client_industry, c.status,
                   (SELECT COUNT(*) FROM public.organization_files f
                     WHERE f.organization_id = c.organization_id
                       AND f.is_active = TRUE AND f.deleted_at IS NULL) AS documents,
                   (SELECT COUNT(*) FROM public.manual_extraction_items i
                     JOIN public.manual_extraction_batches b ON b.id = i.batch_id
                    WHERE b.organization_id = c.organization_id) AS items_total,
                   (SELECT COUNT(*) FROM public.manual_extraction_items i
                     JOIN public.manual_extraction_batches b ON b.id = i.batch_id
                    WHERE b.organization_id = c.organization_id
                      AND i.status IN ('approved','qc_approved','rejected','qc_rejected')) AS items_completed,
                   (SELECT COUNT(*) FROM public.issues iss
                     WHERE iss.organization_id = c.organization_id) AS issues_total,
                   (SELECT COUNT(*) FROM public.issues iss
                     WHERE iss.organization_id = c.organization_id AND iss.status = 'open') AS issues_open,
                   (SELECT COUNT(*) FROM public.report_generation_queue rq
                     WHERE rq.organization_id = c.organization_id
                       AND rq.status = 'completed') AS ready_reports,
                   (SELECT COALESCE(SUM(calculated_kg_co2e),0)::float8 FROM public.emissions_logs e
                     WHERE e.organization_id = c.organization_id) AS emissions_kg,
                   (SELECT COUNT(*) FROM public.emissions_logs e
                     WHERE e.organization_id = c.organization_id) AS emissions_rows
              FROM public.consultant_clients c
             WHERE c.id = $2 AND c.consultant_id = $1
            """,
            consultant_id,
            client_id,
        )
        if not rows:
            return None
        row = rows[0]

        stage_rows = await self._fetch_all(
            """
            SELECT i.status, COUNT(*) AS n
              FROM public.manual_extraction_items i
              JOIN public.manual_extraction_batches b ON b.id = i.batch_id
             WHERE b.organization_id = $1
             GROUP BY i.status ORDER BY i.status
            """,
            str(row["organization_id"]),
        )
        emissions_by_scope = await self._fetch_all(
            "SELECT scope, COALESCE(SUM(calculated_kg_co2e),0)::float8 AS total, "
            "COUNT(*) AS n FROM public.emissions_logs "
            "WHERE organization_id = $1 GROUP BY scope ORDER BY scope",
            str(row["organization_id"]),
        )
        return {
            "client_id": str(row["client_id"]),
            "organization_id": str(row["organization_id"]),
            "client_name": str(row["client_name"]),
            "client_industry": row["client_industry"],
            "status": str(row["status"]),
            "documents": int(row["documents"] or 0),
            "items": {
                "total": int(row["items_total"] or 0),
                "completed": int(row["items_completed"] or 0),
                "by_stage": stage_distribution(stage_rows),
            },
            "issues": {
                "total": int(row["issues_total"] or 0),
                "open": int(row["issues_open"] or 0),
            },
            "reports": {"ready": int(row["ready_reports"] or 0)},
            "emissions": {
                "total_kg": coerce_float(row["emissions_kg"]),
                "rows": int(row["emissions_rows"] or 0),
                "by_scope": [
                    {"scope": str(r["scope"]), "kg": coerce_float(r["total"]), "rows": int(r["n"])}
                    for r in emissions_by_scope
                ],
            },
        }

    # ------------------------------------------------------------------
    # D31 — internal operations queue aging
    # ------------------------------------------------------------------

    async def queue_aging(self) -> dict[str, Any]:
        """Management aging view across the extraction pipeline.

        Sources: ``manual_extraction_batches`` (created_at/assigned_at/
        sla_deadline/sla_breached/entity_id/assigned_to/status) and
        ``manual_extraction_items`` (created_at/status). Aging buckets are the
        D31 standard: 0-1d, 1-3d, 3-7d, 7d+. No invented SLA thresholds — the
        persisted ``sla_deadline``/``sla_breached`` flags are used verbatim.
        """
        batches = await self._fetch_all(
            """
            SELECT b.status, b.created_at, b.assigned_at, b.completed_at,
                   b.sla_deadline, b.sla_breached, b.entity_id, b.assigned_to,
                   o.name AS organization_name,
                   CASE
                     WHEN b.created_at < NOW() - INTERVAL '7 days' THEN '7d+'
                     WHEN b.created_at < NOW() - INTERVAL '3 days' THEN '3-7d'
                     WHEN b.created_at < NOW() - INTERVAL '1 day' THEN '1-3d'
                     ELSE '0-1d'
                   END AS age_bucket,
                   CASE WHEN b.entity_id IS NULL THEN 'internal' ELSE 'entity' END AS scope
              FROM public.manual_extraction_batches b
              LEFT JOIN public.organizations o ON o.id = b.organization_id
             ORDER BY b.created_at
            """
        )
        items = await self._fetch_all(
            """
            SELECT i.status, i.created_at, b.entity_id,
                   CASE
                     WHEN i.created_at < NOW() - INTERVAL '7 days' THEN '7d+'
                     WHEN i.created_at < NOW() - INTERVAL '3 days' THEN '3-7d'
                     WHEN i.created_at < NOW() - INTERVAL '1 day' THEN '1-3d'
                     ELSE '0-1d'
                   END AS age_bucket
              FROM public.manual_extraction_items i
              JOIN public.manual_extraction_batches b ON b.id = i.batch_id
             ORDER BY i.created_at
            """
        )

        def _buckets(rows: list[Any]) -> dict[str, int]:
            counts = {"0-1d": 0, "1-3d": 0, "3-7d": 0, "7d+": 0}
            for r in rows:
                counts[str(r["age_bucket"])] += 1
            return counts

        open_batches = [r for r in batches if str(r["status"]) not in ("completed", "cancelled")]
        batch_sla_breached = sum(1 for r in open_batches if r["sla_breached"])
        batch_overdue = sum(
            1 for r in open_batches
            if r["sla_deadline"] is not None and r["sla_deadline"] < datetime.now(timezone.utc)
        )
        return {
            "batches": {
                "total": len(batches),
                "open": len(open_batches),
                "completed": sum(1 for r in batches if str(r["status"]) == "completed"),
                "aging": _buckets(open_batches),
                "sla_breached": batch_sla_breached,
                "overdue": batch_overdue,
                "by_scope": {
                    "internal": sum(1 for r in open_batches if str(r["scope"]) == "internal"),
                    "entity": sum(1 for r in open_batches if str(r["scope"]) == "entity"),
                },
            },
            "items": {
                "total": len(items),
                "aging": _buckets(items),
                "by_stage": stage_distribution(items),
                "internal": sum(1 for r in items if r["entity_id"] is None),
                "entity": sum(1 for r in items if r["entity_id"] is not None),
            },
        }
