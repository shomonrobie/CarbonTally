"""V3 processing-company surface (V3 new capability).

Management of Human Data Processing Companies (``processing_entities``),
CarbonTally-internal. Reuses the existing V3 ``ProcessingEntitiesRepository``
and the ``ProcessingEntity`` domain model (ADR-V3-001).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, require_admin
from domain.entity import ENTITY_STATUSES, ProcessingEntity

router = APIRouter(prefix="/api/v3/processing-entities", tags=["V3 — Processing Companies"])


class EntityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"
    metadata: dict = {}


class EntityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None


@router.get("")
async def list_processing_entities(
    status: Optional[str] = None,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    if status is not None:
        return {"entities": await repos.entities.list_by_status(status)}
    return {"entities": await repos.entities.list_all()}


@router.post("", status_code=201)
async def create_processing_entity(
    payload: EntityCreate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    if payload.status not in ENTITY_STATUSES:
        raise HTTPException(status_code=422, detail=f"invalid status: {payload.status}")
    entity = ProcessingEntity(
        id=str(uuid.uuid4()),
        name=payload.name,
        description=payload.description,
        status=payload.status,
        metadata=dict(payload.metadata),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        created_by=current_user.user_id,
        updated_by=current_user.user_id,
    )
    return await repos.entities.save(entity)


@router.get("/{entity_id}")
async def get_processing_entity(
    entity_id: str,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    entity = await repos.entities.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="processing entity not found")
    return entity


@router.put("/{entity_id}")
async def update_processing_entity(
    entity_id: str,
    payload: EntityUpdate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    entity = await repos.entities.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="processing entity not found")
    from dataclasses import replace

    new_status = payload.status if payload.status is not None else entity.status
    if new_status not in ENTITY_STATUSES:
        raise HTTPException(status_code=422, detail=f"invalid status: {new_status}")
    updated = replace(
        entity,
        name=payload.name if payload.name is not None else entity.name,
        description=payload.description if payload.description is not None else entity.description,
        status=new_status,
        metadata=dict(payload.metadata) if payload.metadata is not None else entity.metadata,
        updated_by=current_user.user_id,
    )
    return await repos.entities.save(updated)
