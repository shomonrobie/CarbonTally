"""V3 QC surface (V3 new capability).

QC review over manual-extraction items. The RC2 schema already carries the QC
columns on ``manual_extraction_items`` (qc_by, qc_at, qc_notes, quality_score);
no schema change is required for this surface.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, require_admin

router = APIRouter(prefix="/api/v3/qc", tags=["V3 — QC"])


class QCReview(BaseModel):
    quality_score: int
    approved: bool = True
    qc_notes: Optional[str] = None


@router.get("/queue")
async def qc_queue(
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    return {"items": await repos.manual_extraction.list_qc_pending()}


@router.get("/stats")
async def qc_stats(
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    items = await repos.manual_extraction.list_qc_pending()
    return {
        "pending_qc": len(items),
        "approved": 0,
        "rejected": 0,
    }


@router.post("/items/{item_id}/review")
async def review_item(
    item_id: str,
    payload: QCReview,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    if not 0 <= payload.quality_score <= 100:
        raise HTTPException(status_code=422, detail="quality_score must be 0..100")
    item = await repos.manual_extraction.qc_review(
        item_id,
        payload.quality_score,
        payload.qc_notes,
        current_user.user_id,
        payload.approved,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    return item
