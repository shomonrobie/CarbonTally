"""D30 — V3 reporting surface (read-only dashboard/report aggregates).

Every endpoint is authorization-scoped with the EXISTING guards (D15/D20/D22):
- Customer dashboard  -> org member, own organization only (`ensure_org_access`).
- Consultant portfolio -> active consultant firm member; ACTIVE client grants
  only (ended relationships are counted but never detailed).
- Internal operations / review / QC reporting -> internal staff + permission.
- Processing Entity performance -> own entity only (`require_entity_scope`).

Metrics are computed by `ReportingRepository` in SQL over the live tables — no
derived summary tables, no N+1, no analytics warehouse.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.consultant_auth import require_consultant
from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_repositories,
)
from api.operations_auth import (
    ensure_staff_permission,
    require_entity_scope,
    require_internal_staff,
    require_staff,
)
from auth import AuthUser, get_current_user
from data.base import to_jsonable

router = APIRouter(tags=["V3 — Reporting"])


def _row(obj: Any) -> dict[str, Any]:
    """Coerce one asyncpg row (or dict) to a JSON-safe dict."""
    if obj is None:
        return {}
    data = dict(obj) if not isinstance(obj, dict) else dict(obj)
    return {str(k): to_jsonable(v) for k, v in data.items()}


# ---------------------------------------------------------------------------
# Customer dashboard aggregate (org member, own org only)
# ---------------------------------------------------------------------------


@router.get("/api/v3/reporting/customer-dashboard")
async def customer_dashboard_report(
    organization_id: str = Query(..., min_length=1),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The customer "what is my emissions status and what needs my attention?"

    Source tables: emissions_logs, organization_files,
    document_processing_queue, manual_extraction_batches/items, issues,
    report_generation_queue. All rows are scoped to ``organization_id``.
    """
    ensure_org_access(current_user, organization_id)

    emissions = await repos.reporting.emissions_summary(
        organization_id, start_date, end_date, scope
    )
    documents = await repos.reporting.document_summary(organization_id)
    processing = await repos.reporting.processing_summary(organization_id)
    issues = await repos.reporting.issues_summary(organization_id)
    reports = await repos.reporting.report_summary(organization_id)

    items = processing["items"]
    return {
        "organization_id": organization_id,
        "emissions": emissions,
        "documents": documents,
        "processing": processing,
        "issues": issues,
        "reports": {
            "by_status": reports,
            "ready": reports.get("completed", 0),
            "queued": reports.get("pending", 0),
            "failed": reports.get("failed", 0),
        },
        "attention": {
            "open_issues": issues["open"],
            "sla_breached_open": issues["sla_breached_open"],
            "documents_requiring_attention": documents["requiring_attention"],
            "pending_customer_review": items["by_stage"].get("review", 0),
            "unmapped_items": items["unmapped"],
        },
    }


# ---------------------------------------------------------------------------
# Consultant portfolio (active client grants only)
# ---------------------------------------------------------------------------


@router.get("/api/v3/reporting/consultant-portfolio")
async def consultant_portfolio_report(
    context=Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Portfolio health for the caller's OWN client grants.

    ACTIVE clients are reported in detail. Suspended clients are counted.
    ENDED clients are counted but never detailed (D15 — they carry no access).
    """
    clients = await repos.reporting.consultant_portfolio(context.profile.id)
    detailed = [
        {
            **_row(c),
            "documents": int(c["documents"] or 0),
            "items": int(c["items"] or 0),
            "open_issues": int(c["open_issues"] or 0),
            "ready_reports": int(c["ready_reports"] or 0),
        }
        for c in clients
        if str(c["status"]) == "active"
    ]
    counts = {"active": 0, "suspended": 0, "ended": 0, "inactive": 0}
    for c in clients:
        status = str(c["status"])
        counts[status] = counts.get(status, 0) + 1
    return {
        "firm_id": str(context.profile.id),
        "portfolio": counts,
        "clients": detailed,
    }


# ---------------------------------------------------------------------------
# D31 — customer trend + member activity; consultant client drill-down
# ---------------------------------------------------------------------------


@router.get("/api/v3/reporting/emissions-trend")
async def emissions_trend_report(
    organization_id: str = Query(..., min_length=1),
    months: int = Query(12, ge=1, le=36),
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Zero-filled monthly emissions trend (org member, own org only)."""
    ensure_org_access(current_user, organization_id)
    return await repos.reporting.emissions_trend(organization_id, months)


@router.get("/api/v3/reporting/member-activity")
async def member_activity_report(
    organization_id: str = Query(..., min_length=1),
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Activity by organisation member (org member, own org only).

    Derived from authoritative author columns (see ``ReportingRepository``);
    the activity_logs-family tables are not populated by the current workflow.
    """
    ensure_org_access(current_user, organization_id)
    return {"organization_id": organization_id,
            "members": await repos.reporting.member_activity(organization_id)}


@router.get("/api/v3/reporting/consultant-client/{client_id}")
async def consultant_client_report(
    client_id: str,
    context=Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Per-client drill-down for ONE ACTIVE client grant.

    Ended/suspended relationships are rejected (D15/D19) and non-granted
    clients return 404 — no cross-consultant visibility.
    """
    detail = await repos.reporting.consultant_client_detail(context.profile.id, client_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Client grant not found")
    if str(detail["status"]) != "active":
        raise HTTPException(
            status_code=403,
            detail="Client relationship is not active",
        )
    return detail


# ---------------------------------------------------------------------------
# Internal operations / reviewer / QC / platform reporting
# ---------------------------------------------------------------------------


@router.get("/api/v3/ops/reporting/platform")
async def platform_reporting(
    context=Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """CarbonTally platform overview (internal staff, ``can_view_all``)."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_view_all")
    return await repos.reporting.platform_overview()


@router.get("/api/v3/ops/reporting/aging")
async def queue_aging_report(
    context=Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Queue-aging drill-down (internal staff, ``can_view_all``)."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_view_all")
    return await repos.reporting.queue_aging()


@router.get("/api/v3/ops/reporting/review")
async def review_reporting(
    context=Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Reviewer reporting (internal staff, ``can_review``)."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_review")
    return await repos.reporting.review_reporting()


@router.get("/api/v3/ops/reporting/qc")
async def qc_reporting(
    context=Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """QC reporting (internal staff, ``can_review``)."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_review")
    return await repos.reporting.qc_reporting()


@router.get("/api/v3/ops/reporting/audit")
async def audit_reporting(
    actor: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    context=Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Read-side audit trail (staff admin, ``can_manage_staff`` only).

    Reuses the existing ``AuditRepository.query`` over ``audit_trail``. The
    before/after payloads are deliberately excluded to avoid exposing sensitive
    data; only action/actor/resource/timestamp/changed-field-names are shown.
    """
    require_internal_staff(context)
    ensure_staff_permission(context, "can_manage_staff")
    from datetime import datetime as _dt

    from domain.audit import AuditQuery

    filters = AuditQuery(
        action=action,
        entity_type=entity_type,
        actor=actor,
        limit=limit,
        offset=offset,
    )
    entries = await repos.audit.query(filters)
    return {
        "entries": [
            {
                "id": e.id,
                "correlation_id": e.correlation_id,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "action": e.action,
                "actor": e.actor,
                "occurred_at": e.occurred_at.isoformat() if isinstance(e.occurred_at, _dt) else str(e.occurred_at),
                "reason": e.reason,
                "ip_address": e.ip_address,
                "changed_fields": list((e.changed_fields or {}).keys()),
            }
            for e in entries
        ],
        "total": len(entries),
    }


# ---------------------------------------------------------------------------
# Processing Entity performance (own entity only / internal any)
# ---------------------------------------------------------------------------


@router.get("/api/v3/ops/entities/{entity_id}/performance")
async def entity_performance_report(
    entity_id: str,
    context=Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Entity-scoped performance (entity staff own entity; internal staff any)."""
    require_entity_scope(context, entity_id)
    # F1 (PE security audit): entity-staff read surfaces require an ACTIVE
    # entity. Internal staff keep read access for administration/oversight.
    if context.profile.entity_id is not None:
        entity = await repos.entities.get(entity_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="processing entity not found")
        if entity.status != "active":
            raise HTTPException(
                status_code=403,
                detail=f"processing entity is {entity.status}; only active entities may access this surface",
            )
    return await repos.reporting.entity_performance(entity_id)
