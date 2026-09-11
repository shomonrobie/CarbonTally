"""V3 QC surface (V3 new capability).

QC review over manual-extraction items. The RC2 schema already carries the QC
columns on ``manual_extraction_items`` (qc_by, qc_at, qc_notes, quality_score);
no schema change is required for this surface.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    # CL-58 — server-side pagination over the QC pending queue.
    # V1.2 / CT-QC-004 — CarbonTally QC may verify data from EITHER origin
    # (CarbonTally internal OR Processing Entity). Each queue row carries its
    # processing_origin so the independent internal QC gate can identify what
    # it is reviewing and which upstream controls already apply.
    import dataclasses

    from domain.processing_origin import processing_origin_for_batch

    items = await repos.manual_extraction.list_qc_pending()
    out = []
    for item in items:
        row = dataclasses.asdict(item)
        batch = await repos.manual_extraction.get_batch(item.batch_id)
        row["processing_origin"] = processing_origin_for_batch(
            batch.entity_id if batch is not None else None
        )
        out.append(row)
    total = len(out)
    return {
        "items": out[offset:offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def qc_stats(
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    from domain.processing_origin import (
        ORIGIN_CARBONTALLY_INTERNAL,
        ORIGIN_PROCESSING_ENTITY,
        processing_origin_for_batch,
    )

    items = await repos.manual_extraction.list_qc_pending()
    by_origin = {ORIGIN_CARBONTALLY_INTERNAL: 0, ORIGIN_PROCESSING_ENTITY: 0}
    for item in items:
        batch = await repos.manual_extraction.get_batch(item.batch_id)
        origin = processing_origin_for_batch(
            batch.entity_id if batch is not None else None
        )
        by_origin[origin] = by_origin.get(origin, 0) + 1
    return {
        "pending_qc": len(items),
        "by_origin": by_origin,
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
