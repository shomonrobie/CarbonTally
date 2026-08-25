"""V3 review surface (V3 legacy-capability reimplementation).

Review queue, assignment and SLA settings — thin API over the V3 repositories.
Staff-only (``require_admin``).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, require_admin

router = APIRouter(prefix="/api/v3/admin", tags=["V3 — Review"])


class AssignRequest(BaseModel):
    assigned_to: str
    sla_deadline: Optional[str] = None


class CompleteRequest(BaseModel):
    manual_extraction_result: dict = {}
    review_time_seconds: int = 0


class QueueSettingsUpdate(BaseModel):
    max_reviews_per_staff: Optional[int] = None
    sla_hours: Optional[int] = None
    auto_assign_enabled: Optional[bool] = None
    escalation_hours: Optional[int] = None
    priority_weights: Optional[dict] = None


@router.get("/review-queue")
async def list_review_queue(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    return {
        "items": await repos.review_queue.list_items(
            status=status, assigned_to=assigned_to, limit=limit, offset=offset
        )
    }


@router.get("/review-queue/{review_id}")
async def get_review_item(
    review_id: str,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    item = await repos.review_queue.get(review_id)
    if item is None:
        raise HTTPException(status_code=404, detail="review item not found")
    return item


@router.post("/review-queue/{review_id}/assign")
async def assign_review_item(
    review_id: str,
    payload: AssignRequest,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    item = await repos.review_queue.assign(
        review_id, payload.assigned_to, current_user.user_id, payload.sla_deadline
    )
    if item is None:
        raise HTTPException(status_code=404, detail="review item not found")
    return item


@router.post("/review-queue/{review_id}/complete")
async def complete_review_item(
    review_id: str,
    payload: CompleteRequest,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    item = await repos.review_queue.complete(
        review_id, payload.manual_extraction_result, payload.review_time_seconds
    )
    if item is None:
        raise HTTPException(status_code=404, detail="review item not found")
    return item


@router.get("/sla/settings")
async def get_sla_settings(
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    return await repos.queue_settings.get_settings()


@router.put("/sla/settings")
async def update_sla_settings(
    payload: QueueSettingsUpdate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    return await repos.queue_settings.update_settings(
        max_reviews_per_staff=payload.max_reviews_per_staff,
        sla_hours=payload.sla_hours,
        auto_assign_enabled=payload.auto_assign_enabled,
        escalation_hours=payload.escalation_hours,
        priority_weights=payload.priority_weights,
        updated_by=current_user.user_id,
    )
