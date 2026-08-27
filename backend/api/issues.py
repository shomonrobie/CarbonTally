"""V3 Issue endpoints (ADR-V3-009 — DECIDED, Option B).

First-class Issue surface with the settled boundary rules:

* Customer-facing issues are org-scoped and always ``entity_id IS NULL``
  (V3M-5 org storey); entity-scoped issues are never customer-visible.
* Lifecycle transitions are validated against the domain transition table and
  transition authority is enforced here (the DB enforces vocabulary only).
* No hard-delete surface (V3M-5 has no DELETE policy).
* Issue history is recorded through the existing ``AuditRepository``
  (ADR-V3-013 — no new history table).
"""
from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.contracts import (
    IssueCreate,
    IssueListOut,
    IssueOut,
    IssueUpdate,
    issue_out,
)
from api.dependencies import (
    AuditContext,
    RepositoryBundle,
    ensure_org_access,
    get_audit_context,
    get_current_user,
    get_repositories,
    require_admin,
    require_entity_member,
    require_org_member,
)
from auth import AuthUser
from domain.audit import AuditEntry
from domain.issue import Issue

router = APIRouter(prefix="/api/v3/issues", tags=["V3 — Issues"])


# ---------------------------------------------------------------------------
# Customer-facing surface (org-scoped, entity_id IS NULL)
# ---------------------------------------------------------------------------


@router.get("", response_model=IssueListOut)
async def list_issues(
    organization_id: str,
    limit: int = Query(100, ge=1, le=500, description="Page size (1..500)"),
    offset: int = Query(0, ge=0, description="Page offset"),
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> IssueListOut:
    """List customer-facing issues for an organisation (entity-scoped rows are
    never included — V3M-5 storey). Bounded pagination (D26 scale hardening):
    stable ``created_at DESC, id`` ordering; ``total`` is the full count."""
    ensure_org_access(current_user, organization_id)
    issues = await repos.issues.list_for_org(organization_id, limit=limit, offset=offset)
    return IssueListOut(
        total=await repos.issues.count_for_org(organization_id),
        issues=[issue_out(i) for i in issues],
    )


@router.get("/{issue_id}", response_model=IssueOut)
async def get_issue(
    issue_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> IssueOut:
    """Return one customer-facing issue (404 when unknown or entity-scoped)."""
    issue = await repos.issues.get(issue_id)
    if issue is None or issue.entity_id is not None:
        raise HTTPException(status_code=404, detail=f"issue {issue_id} not found")
    if issue.organization_id is not None:
        ensure_org_access(current_user, issue.organization_id)
    return issue_out(issue)


@router.post("", response_model=IssueOut, status_code=201)
async def create_issue(
    payload: IssueCreate,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> IssueOut:
    """Create a customer-facing issue (``entity_id`` forced to NULL — entity
    issue creation is CarbonTally-internal, V3M-5 storey)."""
    org_id = payload.organization_id or current_user.organization_id
    if org_id is None:
        raise HTTPException(status_code=422, detail="organization_id is required")
    ensure_org_access(current_user, org_id)
    now = datetime.now(timezone.utc)
    issue = Issue(
        id=str(uuid.uuid4()),
        title=payload.title.strip(),
        description=payload.description,
        issue_type=payload.issue_type,
        severity=payload.severity,
        priority=payload.priority,
        status="open",
        organization_id=org_id,
        entity_id=None,  # customer-facing surface only
        work_item_id=payload.work_item_id,
        document_id=payload.document_id,
        batch_id=payload.batch_id,
        conversation_id=payload.conversation_id,
        assignee_id=payload.assignee_id,
        created_at=now,
        updated_at=now,
        created_by=current_user.user_id,
        updated_by=current_user.user_id,
    )
    stored = await repos.issues.save(issue)
    await _record_issue_audit(
        repos, None, action="issue:created", issue=stored, actor=current_user.user_id,
        after={"status": stored.status, "severity": stored.severity},
    )
    return issue_out(stored)


@router.put("/{issue_id}", response_model=IssueOut)
async def update_issue(
    issue_id: str,
    payload: IssueUpdate,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
) -> IssueOut:
    """Update a customer-facing issue (status transitions validated + audited;
    reopening stamps ``reopened_at``)."""
    existing = await repos.issues.get(issue_id)
    if existing is None or existing.entity_id is not None:
        raise HTTPException(status_code=404, detail=f"issue {issue_id} not found")
    if existing.organization_id is not None:
        ensure_org_access(current_user, existing.organization_id)

    new_status = payload.status if payload.status is not None else existing.status
    if not existing.can_transition_to(new_status):
        raise HTTPException(
            status_code=409,
            detail=f"invalid issue transition {existing.status!r} -> {new_status!r}",
        )
    reopened_at = (
        datetime.now(timezone.utc)
        if new_status == "open" and existing.status in ("resolved", "closed")
        else existing.reopened_at
    )

    updated = replace(
        existing,
        issue_type=payload.issue_type if payload.issue_type is not None else existing.issue_type,
        severity=payload.severity if payload.severity is not None else existing.severity,
        priority=payload.priority if payload.priority is not None else existing.priority,
        status=new_status,
        title=payload.title.strip() if payload.title is not None else existing.title,
        description=payload.description if payload.description is not None else existing.description,
        assignee_id=payload.assignee_id if payload.assignee_id is not None else existing.assignee_id,
        reopened_at=reopened_at,
        updated_by=current_user.user_id,
    )
    stored = await repos.issues.save(updated)
    await _record_issue_audit(
        repos, audit, action="issue:updated", issue=stored, actor=current_user.user_id,
        before={"status": existing.status},
        after={"status": stored.status},
    )
    return issue_out(stored)


# ---------------------------------------------------------------------------
# CarbonTally-internal surface (entity-scoped + open triage)
# ---------------------------------------------------------------------------


@router.get("/admin/entity/{entity_id}", response_model=IssueListOut)
async def list_entity_issues(
    entity_id: str,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> IssueListOut:
    """List issues scoped to one processing entity (entity staff see their own
    entity only; CarbonTally internal staff see any)."""
    await require_entity_member(entity_id)(current_user)
    # F1 (PE security audit): entity-staff read surfaces require an ACTIVE
    # entity. Internal staff keep read access for administration/oversight.
    if current_user.is_entity_staff:
        entity = await repos.entities.get(entity_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="processing entity not found")
        if entity.status != "active":
            raise HTTPException(
                status_code=403,
                detail=f"processing entity is {entity.status}; only active entities may access this surface",
            )
    issues = await repos.issues.list_for_entity(entity_id)
    return IssueListOut(total=len(issues), issues=[issue_out(i) for i in issues])


@router.get("/admin/open", response_model=IssueListOut)
async def list_open_issues(
    organization_id: Optional[str] = Query(None, description="Optional org filter"),
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> IssueListOut:
    """CarbonTally-internal triage: open/in-progress/escalated issues."""
    issues = await repos.issues.list_open(organization_id=organization_id)
    return IssueListOut(total=len(issues), issues=[issue_out(i) for i in issues])


async def _record_issue_audit(
    repos: RepositoryBundle,
    audit: Optional[AuditContext],
    *,
    action: str,
    issue: Issue,
    actor: str,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
) -> None:
    """Record issue writes through the existing audit repository (best-effort)."""
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id=audit.correlation_id if audit is not None else "",
        entity_type="issue",
        entity_id=issue.id,
        action=action,
        actor=actor,
        occurred_at=datetime.now(timezone.utc),
        changed_fields={"status": issue.status, "severity": issue.severity},
        ip_address=audit.ip_address if audit is not None else None,
        before=before,
        after=after,
    )
    await repos.audit.record(entry)


