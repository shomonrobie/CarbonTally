"""V3 Processing Entity admin endpoints (ADR-V3-001 — DECIDED, Option B).

CarbonTally-internal administration surface for ``processing_entities``. The
table is deny-by-default for ``authenticated`` (V3M-1); only CarbonTally
internal staff/admin may manage entities and their lifecycle (ADR-V3-001 Q6 —
entities cannot self-activate).

Lifecycle transitions are validated against the domain transition table and
recorded through the existing ``AuditRepository`` (ADR-V3-013 reuse — no new
history table).
"""
from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.contracts import (
    ProcessingEntityCreate,
    ProcessingEntityListOut,
    ProcessingEntityOut,
    ProcessingEntityUpdate,
    processing_entity_out,
)
from api.dependencies import (
    AuditContext,
    RepositoryBundle,
    get_audit_context,
    get_repositories,
    require_admin,
)
from domain.audit import AuditEntry
from domain.entity import ProcessingEntity

router = APIRouter(
    prefix="/api/v3/admin/entities", tags=["V3 Admin — Processing Entities"]
)


@router.get("", response_model=ProcessingEntityListOut)
async def list_entities(
    status: Optional[str] = Query(None, description="Filter by lifecycle status"),
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> ProcessingEntityListOut:
    """List processing entities (optionally by lifecycle status)."""
    if status:
        entities = await repos.entities.list_by_status(status)
    else:
        entities = await repos.entities.list_all()
    return ProcessingEntityListOut(
        total=len(entities), entities=[processing_entity_out(e) for e in entities]
    )


@router.get("/{entity_id}", response_model=ProcessingEntityOut)
async def get_entity(
    entity_id: str,
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> ProcessingEntityOut:
    """Return one processing entity (404 when unknown)."""
    entity = await repos.entities.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"processing entity {entity_id} not found")
    return processing_entity_out(entity)


@router.post("", response_model=ProcessingEntityOut, status_code=201)
async def create_entity(
    payload: ProcessingEntityCreate,
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
) -> ProcessingEntityOut:
    """Onboard a processing entity (CarbonTally-internal)."""
    now = datetime.now(timezone.utc)
    entity = ProcessingEntity(
        id=str(uuid.uuid4()),
        name=payload.name.strip(),
        description=payload.description,
        status=payload.status,
        metadata=payload.metadata,
        created_at=now,
        updated_at=now,
        created_by=current_user.user_id,
        updated_by=current_user.user_id,
    )
    stored = await repos.entities.save(entity)
    await _record_entity_audit(
        repos, audit, action="processing_entity:created", entity=stored,
        after={"name": stored.name, "status": stored.status},
    )
    return processing_entity_out(stored)


@router.put("/{entity_id}", response_model=ProcessingEntityOut)
async def update_entity(
    entity_id: str,
    payload: ProcessingEntityUpdate,
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
) -> ProcessingEntityOut:
    """Update entity fields / lifecycle status (404 when unknown)."""
    existing = await repos.entities.get(entity_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"processing entity {entity_id} not found")

    new_status = payload.status if payload.status is not None else existing.status
    if not existing.can_transition_to(new_status):
        raise HTTPException(
            status_code=409,
            detail=f"invalid lifecycle transition {existing.status!r} -> {new_status!r}",
        )

    updated = replace(
        existing,
        name=payload.name.strip() if payload.name is not None else existing.name,
        description=payload.description if payload.description is not None else existing.description,
        status=new_status,
        metadata=payload.metadata if payload.metadata is not None else existing.metadata,
        updated_by=current_user.user_id,
    )
    stored = await repos.entities.save(updated)
    await _record_entity_audit(
        repos, audit, action="processing_entity:updated", entity=stored,
        before={"status": existing.status},
        after={"name": stored.name, "status": stored.status},
    )
    return processing_entity_out(stored)


async def _record_entity_audit(
    repos: RepositoryBundle,
    audit: AuditContext,
    *,
    action: str,
    entity: ProcessingEntity,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
) -> None:
    """Record entity writes through the existing audit repository (best-effort)."""
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id=audit.correlation_id,
        entity_type="processing_entity",
        entity_id=entity.id,
        action=action,
        actor=audit.actor,
        occurred_at=datetime.now(timezone.utc),
        changed_fields={"name": entity.name, "status": entity.status},
        ip_address=audit.ip_address or None,
        before=before,
        after=after,
    )
    await repos.audit.record(entry)


