"""V3 Processing Entity access contract (Phase 3).

The dedicated Processing Entity application surface is ``/api/v3/pe/*``. This
is a THIN access-contract layer: every endpoint first enforces the PE
authorization model (identity → active PE membership → frozen PE role →
capability → resource scope) and then DELEGATES to the shared V3 operations
handlers / repositories / engines. It deliberately contains no extraction,
mapping, validation, calculation or workflow business logic.

Resource scope rules enforced here (never trusted from the client):
* the caller's entity id comes from their staff membership — never the URL;
* an item/batch is reachable only when its ``manual_extraction_batches.entity_id``
  equals the caller's entity (CarbonTally-assigned work);
* entity staff can never reach another PE's batches/items/issues.

The existing ``/api/v3/operations/entities/{entity_id}/extraction/*`` surface
remains the shared implementation; PE users reaching the platform through the
legacy ops routes keep working (non-destructive migration), while ``/api/v3/pe/*``
is the canonical PE contract.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api import v3_operations as _ops
from api.dependencies import (
    AuditContext,
    RepositoryBundle,
    get_audit_context,
    get_calculation_engine,
    get_repositories,
)
from engines.calculation import CalculationEngine
from api.pe_auth import (
    CAP_COMMUNICATE,
    CAP_MANAGE_TEAM,
    CAP_PROCESS,
    CAP_QC,
    CAP_READ_WORK,
    CAP_REVIEW,
    PEContext,
    require_pe_capability,
    require_pe_member,
)
from domain.audit import AuditEntry
from engines.processing_workflow import has_blocking_findings, validate_processing_item

router = APIRouter(prefix="/api/v3/pe", tags=["V3 — Processing Entity"])


def _safe_issue(issue) -> dict:
    """Minimal entity-scoped issue payload (data minimization)."""
    return {
        "id": issue.id,
        "title": issue.title,
        "status": issue.status,
        "severity": getattr(issue, "severity", None),
        "manual_extraction_batch_id": getattr(issue, "manual_extraction_batch_id", None),
        "created_at": issue.created_at,
        "updated_at": issue.updated_at,
    }


async def _ensure_assigned_item(
    pe: PEContext,
    repos: RepositoryBundle,
    item_id: str,
):
    """Load ``item_id`` and require its EFFECTIVE processing entity is ``pe``.

    WS4 Gate 3 / Option B: an open item-level D38 assignment takes precedence
    over the batch default; a PE is authorised only when
    ``effective_entity(item) == caller entity``. The immutable batch default is
    never sufficient when an item-level override (or an internal override)
    exists.
    """
    item = await repos.manual_extraction.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    effective = await repos.manual_extraction.work_item_effective_entity(item_id)
    if effective is None or effective != pe.entity_id:
        raise HTTPException(
            status_code=403,
            detail="Item is not effectively assigned to this processing entity",
        )
    batch = await repos.manual_extraction.get_batch(item.batch_id)
    if batch is None or batch.status == "cancelled":
        raise HTTPException(
            status_code=409, detail="work item batch is unavailable"
        )
    return item, batch


async def _ensure_assigned_batch(
    pe: PEContext,
    repos: RepositoryBundle,
    batch_id: str,
):
    """Require ``batch_id`` to be reachable by ``pe`` under the item-level model.

    A batch is reachable when it is the batch default for ``pe`` (the container
    the PE works from) OR it contains at least one item whose effective
    processing entity is ``pe`` (item-level assignment in a batch whose default
    belongs to another party). Item rows returned to the PE are always filtered
    by the item's effective entity.
    """
    batch = await repos.manual_extraction.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    if batch.status == "cancelled":
        raise HTTPException(status_code=409, detail="batch is cancelled")
    if batch.entity_id == pe.entity_id:
        return batch
    effective = await repos.manual_extraction.effective_entity_map(batch_id)
    if pe.entity_id in effective.values():
        return batch
    raise HTTPException(
        status_code=403,
        detail="Batch is not assigned to this processing entity",
    )



# ---------------------------------------------------------------------------
# Context / observability
# ---------------------------------------------------------------------------


@router.get("/me")
async def pe_me(pe: PEContext = Depends(require_pe_member)):
    """The PE member's entity-scoped context (own entity only)."""
    return {
        "entity": {
            "id": pe.entity_id,
            "name": pe.entity.name,
            "status": pe.entity.status,
        },
        "role": {"key": pe.role_key, "label": pe.role_label},
        "capabilities": sorted(pe.capabilities),
        "user_id": pe.user_id,
    }


@router.get("/work")
async def pe_work(
    status: Optional[str] = None,
    pe: PEContext = Depends(require_pe_capability(CAP_READ_WORK)),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The batches reachable by this PE under the item-level assignment model.

    Includes the entity's batch-default batches plus batches that only contain
    item-level assignments for the entity. Per-batch ``item_count`` counts only
    items whose effective processing entity is this PE.
    """
    seen = {}
    default_batches = await repos.manual_extraction.list_entity_batches(pe.entity_id, status)
    item_batches = await repos.manual_extraction.list_batches_with_open_entity_item(pe.entity_id)
    if status is not None:
        item_batches = [b for b in item_batches if b.status == status]
    for batch in default_batches + item_batches:
        seen[batch.id] = batch
    out = []
    for batch in seen.values():
        effective = await repos.manual_extraction.effective_entity_map(batch.id)
        item_count = sum(1 for e in effective.values() if e == pe.entity_id)
        out.append(
            {
                "id": batch.id,
                "batch_name": batch.batch_name,
                "status": batch.status,
                "created_at": batch.created_at,
                "organization_id": batch.organization_id,
                "item_count": item_count,
            }
        )
    out.sort(key=lambda b: b["created_at"] is not None and str(b["created_at"]),
             reverse=True)

    return {"batches": out, "total": len(out)}


@router.get("/batches/{batch_id}/items")
async def pe_batch_items(
    batch_id: str,
    pe: PEContext = Depends(require_pe_capability(CAP_READ_WORK)),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The items of one batch that are EFFECTIVELY assigned to this PE.

    Items whose effective processing entity is another PE (or internal /
    unassigned) are never returned, even though they share the same batch.
    """
    await _ensure_assigned_batch(pe, repos, batch_id)
    items = await repos.manual_extraction.list_items(batch_id)
    effective = await repos.manual_extraction.effective_entity_map(batch_id)
    visible = [i for i in items if effective.get(str(i.id)) == pe.entity_id]
    return {
        "items": [
            {
                "id": item.id,
                "batch_id": item.batch_id,
                "file_name": item.file_name,
                "status": item.status,
                "page_count": item.page_count,
                "document_type": item.document_type,
                "created_at": item.created_at,
            }
            for item in visible
        ],
        "total": len(visible),
    }


# ---------------------------------------------------------------------------
# Workflow actions (thin delegation; capability-gated by PE role)
# ---------------------------------------------------------------------------


@router.post("/items/{item_id}/start")
async def pe_item_start(
    item_id: str,
    payload: _ops.ItemStart,
    pe: PEContext = Depends(require_pe_capability(CAP_PROCESS)),
    repos: RepositoryBundle = Depends(get_repositories),
):
    await _ensure_assigned_item(pe, repos, item_id)
    return await _ops.entity_extraction_start_item(
        entity_id=pe.entity_id, item_id=item_id,
        payload=payload, context=pe.staff, repos=repos,
    )


@router.post("/items/{item_id}/extract")
async def pe_item_extract(
    item_id: str,
    payload: _ops.ExtractPayload,
    pe: PEContext = Depends(require_pe_capability(CAP_PROCESS)),
    repos: RepositoryBundle = Depends(get_repositories),
):
    await _ensure_assigned_item(pe, repos, item_id)
    return await _ops.entity_extraction_save(
        entity_id=pe.entity_id, item_id=item_id,
        payload=payload, context=pe.staff, repos=repos,
    )


@router.post("/items/{item_id}/map")
async def pe_item_map(
    item_id: str,
    payload: _ops.MapPayload,
    pe: PEContext = Depends(require_pe_capability(CAP_PROCESS)),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
):
    await _ensure_assigned_item(pe, repos, item_id)
    return await _ops.entity_extraction_map(
        entity_id=pe.entity_id, item_id=item_id,
        payload=payload, context=pe.staff, repos=repos, audit=audit,
    )


@router.post("/items/{item_id}/validate")
async def pe_item_validate(
    item_id: str,
    pe: PEContext = Depends(require_pe_capability(CAP_REVIEW)),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
):
    """PE validation (PE Reviewer, frozen role) on PE-assigned work.

    Legal transition ``mapped → validated`` (clean findings) or
    ``mapped → mapping`` (blocking findings — item returns to the entity for
    correction). Reuses the canonical validation engine and preserves the
    blocking-finding contract; PE Review / PE QC / CT QC remain separate gates.
    """
    item, _batch = await _ensure_assigned_item(pe, repos, item_id)
    if item.status != "mapped":
        raise HTTPException(
            status_code=409,
            detail=f"PE validation requires a mapped item (status is {item.status!r})",
        )
    findings = validate_processing_item(item)
    blocking = has_blocking_findings(findings)
    target = "mapping" if blocking else "validated"
    await repos.manual_extraction.set_item_status(item.id, target)
    updated = await repos.manual_extraction.get_item(item.id)
    origin = await repos.manual_extraction.get_item_origin(item_id)
    await repos.audit.record(
        AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=audit.correlation_id if audit is not None else item_id,
            entity_type="manual_extraction_item",
            entity_id=item_id,
            action="pe_validate:blocked" if blocking else "pe_validate:validated",
            actor=pe.user_id,
            occurred_at=datetime.now(timezone.utc),
            changed_fields={
                "status_from": "mapped",
                "status_to": target,
                "blocking_count": len([f for f in findings if f.severity == "error"]),
                "processing_origin": (origin or {}).get("processing_origin"),
                "processing_entity_id": (origin or {}).get("processing_entity_id"),
                "entity_id": pe.entity_id,
                "pe_role": pe.role_key,
            },
            ip_address=audit.ip_address if audit is not None else None,
        )
    )
    return {
        "item": updated,
        "status": target,
        "blocking": blocking,
        "findings": [
            {
                "code": f.code,
                "severity": f.severity,
                "message": f.message,
                "field": f.field,
            }
            for f in findings
        ],
    }


@router.post("/items/{item_id}/calculate")
async def pe_item_calculate(
    item_id: str,
    payload: _ops.CalculatePayload,
    pe: PEContext = Depends(require_pe_capability(CAP_PROCESS)),
    repos: RepositoryBundle = Depends(get_repositories),
    calculation_engine: CalculationEngine = Depends(get_calculation_engine),
    audit: AuditContext = Depends(get_audit_context),
):
    await _ensure_assigned_item(pe, repos, item_id)
    # WS4 Gate-4 remediation — resolve the shared calculation engine through
    # FastAPI DI and pass it explicitly to the shared ops handler. Previously
    # the handler's ``Depends(get_calculation_engine)`` default was evaluated
    # only for the ops HTTP surface, so this canonical /pe route invoked the
    # handler with the unresolved ``Depends`` marker and 500'd on calculate.
    return await _ops.entity_extraction_calculate(
        entity_id=pe.entity_id, item_id=item_id,
        payload=payload, context=pe.staff, repos=repos,
        calculation_engine=calculation_engine, audit=audit,
    )


@router.post("/items/{item_id}/status")
async def pe_item_status(
    item_id: str,
    payload: _ops.EntityItemStatus,
    pe: PEContext = Depends(require_pe_capability(CAP_PROCESS)),
    repos: RepositoryBundle = Depends(get_repositories),
):
    await _ensure_assigned_item(pe, repos, item_id)
    return await _ops.entity_extraction_set_status(
        entity_id=pe.entity_id, item_id=item_id,
        payload=payload, context=pe.staff, repos=repos,
    )


class _PEDecision(BaseModel):
    approved: bool = True


@router.post("/items/{item_id}/pe-review")
async def pe_item_pe_review(
    item_id: str,
    payload: _PEDecision,
    pe: PEContext = Depends(require_pe_capability(CAP_REVIEW)),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
):
    """PE Review (PE Reviewer, frozen role) on PE-assigned work.

    ``calculated → pe_reviewed | pe_review_rejected`` with immutable
    actor/timestamp provenance AND an append-only audit event. PE Review is
    PE-domain only.
    """
    item, _ = await _ensure_assigned_item(pe, repos, item_id)
    if item.status not in ("calculated", "pe_review", "pe_reviewed"):
        raise HTTPException(
            status_code=409,
            detail=f"PE Review requires a calculated item (status is {item.status!r})",
        )
    updated = await repos.manual_extraction.pe_review_decision(
        item_id, payload.approved, pe.user_id
    )
    if updated is None:
        raise HTTPException(status_code=409, detail="PE Review decision not applied")
    origin = await repos.manual_extraction.get_item_origin(item_id)
    await repos.audit.record(
        AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=audit.correlation_id if audit is not None else item_id,
            entity_type="manual_extraction_item",
            entity_id=item_id,
            action="pe_review:approved" if payload.approved else "pe_review:rejected",
            actor=pe.user_id,
            occurred_at=datetime.now(timezone.utc),
            changed_fields={
                "status_from": item.status,
                "status_to": "pe_reviewed" if payload.approved else "pe_review_rejected",
                "processing_origin": (origin or {}).get("processing_origin"),
                "processing_entity_id": (origin or {}).get("processing_entity_id"),
                "entity_id": pe.entity_id,
                "pe_role": pe.role_key,
            },
            ip_address=audit.ip_address if audit is not None else None,
        )
    )
    return {"item": updated, "stage": "pe_reviewed" if payload.approved else "pe_review_rejected"}


@router.post("/items/{item_id}/pe-qc")
async def pe_item_pe_qc(
    item_id: str,
    payload: _PEDecision,
    pe: PEContext = Depends(require_pe_capability(CAP_QC)),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
):
    """PE QC (PE QC Specialist, frozen role) on PE-assigned work.

    ``pe_reviewed → pe_qc_approved | pe_qc_rejected``. PE QC NEVER grants
    CarbonTally QC authority — PE-QC-approved work still requires the late
    CarbonTally QC gate before customer approval. Append-only audit recorded.
    """
    item, _ = await _ensure_assigned_item(pe, repos, item_id)
    if item.status not in ("pe_reviewed", "pe_qc", "pe_qc_approved"):
        raise HTTPException(
            status_code=409,
            detail=f"PE QC requires a PE-reviewed item (status is {item.status!r})",
        )
    updated = await repos.manual_extraction.pe_qc_decision(
        item_id, payload.approved, pe.user_id
    )
    if updated is None:
        raise HTTPException(status_code=409, detail="PE QC decision not applied")
    origin = await repos.manual_extraction.get_item_origin(item_id)
    await repos.audit.record(
        AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=audit.correlation_id if audit is not None else item_id,
            entity_type="manual_extraction_item",
            entity_id=item_id,
            action="pe_qc:approved" if payload.approved else "pe_qc:rejected",
            actor=pe.user_id,
            occurred_at=datetime.now(timezone.utc),
            changed_fields={
                "status_from": item.status,
                "status_to": "pe_qc_approved" if payload.approved else "pe_qc_rejected",
                "processing_origin": (origin or {}).get("processing_origin"),
                "processing_entity_id": (origin or {}).get("processing_entity_id"),
                "entity_id": pe.entity_id,
                "pe_role": pe.role_key,
            },
            ip_address=audit.ip_address if audit is not None else None,
        )
    )
    return {"item": updated, "stage": "pe_qc_approved" if payload.approved else "pe_qc_rejected"}


@router.post("/items/{item_id}/clarify")
async def pe_item_clarify(
    item_id: str,
    payload: _ops.EntityClarify,
    pe: PEContext = Depends(require_pe_capability(CAP_COMMUNICATE)),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
):
    """Raise a mediated clarification (PE → CarbonTally, never direct to the
    customer). DELEGATED to the shared entity-clarify handler."""
    await _ensure_assigned_item(pe, repos, item_id)
    return await _ops.entity_extraction_clarify(
        entity_id=pe.entity_id, item_id=item_id,
        payload=payload, context=pe.staff, repos=repos, audit=audit,
    )


# ---------------------------------------------------------------------------
# Entity-scoped issues (PE ↔ CarbonTally Operations communication boundary)
# ---------------------------------------------------------------------------


@router.get("/issues")
async def pe_issues(
    pe: PEContext = Depends(require_pe_capability(CAP_READ_WORK)),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Entity-scoped issues (own entity only; work-item/batch scoped)."""
    issues = await repos.issues.list_for_entity(pe.entity_id)
    return {"issues": [_safe_issue(i) for i in issues], "total": len(issues)}


@router.get("/issues/{issue_id}")
async def pe_issue_detail(
    issue_id: str,
    pe: PEContext = Depends(require_pe_capability(CAP_READ_WORK)),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """One entity-scoped issue (own entity only)."""
    issue = await repos.issues.get(issue_id)
    if issue is None or getattr(issue, "entity_id", None) != pe.entity_id:
        raise HTTPException(status_code=403, detail="Issue is not entity-scoped to you")
    return {"issue": _safe_issue(issue)}


# ---------------------------------------------------------------------------
# PE team administration (Admin capability only)
# ---------------------------------------------------------------------------


@router.get("/team")
async def pe_team(
    pe: PEContext = Depends(require_pe_capability(CAP_MANAGE_TEAM)),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The PE's own staff roster (PE Admin only; own entity only)."""
    from api.pe_auth import PE_FROZEN_ROLE_LABELS

    profiles = await repos.staff.list_entity_staff(pe.entity_id)
    out = []
    for profile in profiles:
        role_key = ""
        if profile.role_id:
            role = await repos.staff.get_role(profile.role_id)
            if role is not None:
                role_key = str(role.name or "")
        out.append(
            {
                "user_id": profile.user_id,
                "first_name": getattr(profile, "first_name", None),
                "last_name": getattr(profile, "last_name", None),
                "is_active": bool(getattr(profile, "is_active", True)),
                "role_key": role_key,
                "role_label": PE_FROZEN_ROLE_LABELS.get(role_key),
            }
        )
    return {"team": out, "total": len(out)}

    return {"batch": batch, "items": [_ops.signed_item(i) for i in items]}


@router.get("/items/{item_id}/workspace")
async def pe_item_workspace(
    item_id: str,
    pe: PEContext = Depends(require_pe_capability(CAP_READ_WORK)),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The processing workspace payload — DELEGATED to the shared handler.

    The shared handler re-validates entity scope, active entity, item↔batch
    assignment and issues the short-lived view-only signed URL.
    """
    await _ensure_assigned_item(pe, repos, item_id)
    return await _ops.entity_extraction_item_workspace(
        entity_id=pe.entity_id,
        item_id=item_id,
        context=pe.staff,
        repos=repos,
    )


# ---------------------------------------------------------------------------
# Phase 5 / WS1 (D38) — canonical WorkItem claim / release / complete (PE)
# ---------------------------------------------------------------------------
import asyncpg  # noqa: E402

from services.work_items import (  # noqa: E402
    WorkItemError,
    pe_claim_item,
    pe_complete_item,
    pe_release_item,
    work_item_read,
)


class PeWorkReason(BaseModel):
    reason: Optional[str] = None


def _raise_pe_work_error(exc: WorkItemError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail)


async def _call_pe_work(fn, *args, **kwargs) -> dict:
    try:
        return await fn(*args, **kwargs)
    except WorkItemError as exc:
        _raise_pe_work_error(exc)
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=409, detail="work item already has an open assignment"
        )


@router.get("/items/{item_id}/work")
async def pe_work_item_read(
    item_id: str,
    pe: PEContext = Depends(require_pe_capability(CAP_READ_WORK)),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Current assignment + attribution history for an own-entity item."""
    await _ensure_assigned_item(pe, repos, item_id)
    try:
        return await work_item_read(repos, item_id)
    except WorkItemError as exc:
        _raise_pe_work_error(exc)


@router.post("/items/{item_id}/work/claim")
async def pe_work_claim(
    item_id: str,
    payload: Optional[PeWorkReason] = None,
    pe: PEContext = Depends(require_pe_capability(CAP_PROCESS)),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Claim an own-entity item for this processing entity (Data Entry
    Operator / Reviewer / QC / Admin with process capability)."""
    await _ensure_assigned_item(pe, repos, item_id)
    return await _call_pe_work(
        pe_claim_item, repos, item_id=item_id, entity_id=pe.entity_id,
        actor_user_id=pe.user_id,
        reason=(payload.reason if payload else None),
    )


@router.post("/items/{item_id}/work/release")
async def pe_work_release(
    item_id: str,
    payload: Optional[PeWorkReason] = None,
    pe: PEContext = Depends(require_pe_capability(CAP_PROCESS)),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    await _ensure_assigned_item(pe, repos, item_id)
    return await _call_pe_work(
        pe_release_item, repos, item_id=item_id, entity_id=pe.entity_id,
        actor_user_id=pe.user_id,
        reason=(payload.reason if payload else None),
    )


@router.post("/items/{item_id}/work/complete")
async def pe_work_complete(
    item_id: str,
    payload: Optional[PeWorkReason] = None,
    pe: PEContext = Depends(require_pe_capability(CAP_PROCESS)),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Completion attribution for an own-entity item."""
    await _ensure_assigned_item(pe, repos, item_id)
    return await _call_pe_work(
        pe_complete_item, repos, item_id=item_id, entity_id=pe.entity_id,
        actor_user_id=pe.user_id,
        reason=(payload.reason if payload else None),
    )
