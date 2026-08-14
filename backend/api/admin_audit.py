"""Admin audit-trail endpoints (prep-pack Phase 10.3, audit).

Exposes the existing :class:`data.audit.AuditRepository` — no second audit-log
system is created. The surface is staff/admin only and returns the full entry
structure (correlation id, actor, changed fields, before/after) so authorised
users can reconstruct what happened on any entity, while unauthorised users
never reach the endpoint at all (no tenant-sensitive data leaks).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.contracts import (
    AuditCsvOut,
    AuditEntryOut,
    AuditListOut,
    audit_entry_out,
)
from api.dependencies import RepositoryBundle, get_repositories, require_admin
from domain.audit import AuditQuery

router = APIRouter(prefix="/api/v2/admin/audit", tags=["Admin Audit"])


def _audit_query_from_params(
    *,
    correlation_id: Optional[str],
    entity_type: Optional[str],
    entity_id: Optional[str],
    action: Optional[str],
    actor: Optional[str],
    occurred_after: Optional[datetime],
    occurred_before: Optional[datetime],
    limit: int,
    offset: int,
) -> AuditQuery:
    return AuditQuery(
        correlation_id=correlation_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        occurred_after=occurred_after,
        occurred_before=occurred_before,
        limit=limit,
        offset=offset,
    )


@router.get("", response_model=AuditListOut)
async def query_audit(
    correlation_id: Optional[str] = Query(None, description="Filter by request/correlation id"),
    entity_type: Optional[str] = Query(None, description="Filter by entity kind (e.g. import_batch)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity id"),
    action: Optional[str] = Query(None, description="Filter by action verb (e.g. report:generated)"),
    actor: Optional[str] = Query(None, description="Filter by actor (user id or system)"),
    occurred_after: Optional[datetime] = Query(None, description="ISO-8601 inclusive lower bound"),
    occurred_before: Optional[datetime] = Query(None, description="ISO-8601 inclusive upper bound"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> AuditListOut:
    """Search the audit trail with the existing ``AuditRepository.query`` filters."""
    filters = _audit_query_from_params(
        correlation_id=correlation_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        occurred_after=occurred_after,
        occurred_before=occurred_before,
        limit=limit,
        offset=offset,
    )
    entries = await repos.audit.query(filters)
    return AuditListOut(total=len(entries), entries=[audit_entry_out(e) for e in entries])


@router.get("/export", response_model=AuditCsvOut)
async def export_audit(
    correlation_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    occurred_after: Optional[datetime] = Query(None),
    occurred_before: Optional[datetime] = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> AuditCsvOut:
    """Export matching audit entries as CSV via ``AuditRepository.export_csv``.

    The CSV body is returned inside a JSON envelope (Phase 10.2 interpretation —
    no streaming transport is introduced; the payload is the repository output).
    """
    filters = _audit_query_from_params(
        correlation_id=correlation_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        occurred_after=occurred_after,
        occurred_before=occurred_before,
        limit=limit,
        offset=offset,
    )
    csv = await repos.audit.export_csv(filters)
    return AuditCsvOut(filename="audit-export.csv", csv=csv)


@router.get("/correlation/{correlation_id}", response_model=AuditListOut)
async def get_audit_by_correlation(
    correlation_id: str,
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> AuditListOut:
    """Return every entry belonging to one correlation id, in order."""
    entries = await repos.audit.get_by_correlation(correlation_id)
    return AuditListOut(total=len(entries), entries=[audit_entry_out(e) for e in entries])


@router.get("/{entry_id}", response_model=AuditEntryOut)
async def get_audit_entry(
    entry_id: str,
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> AuditEntryOut:
    """Return a single audit entry (404 when unknown)."""
    entry = await repos.audit.get(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"audit entry {entry_id} not found")
    return audit_entry_out(entry)
