"""V3 manual-extraction surface (V3 new capability).

Batches and work items for external/manual data processing, org-scoped.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_repositories,
)
from auth import AuthUser, require_org_member, require_org_admin
from api.manual_processing_auth import ensure_manual_processing_allowed

router = APIRouter(prefix="/api/v3/manual-extraction", tags=["V3 — Manual Extraction"])


class BatchCreate(BaseModel):
    batch_name: str
    batch_description: Optional[str] = None
    total_documents: int = 0
    total_pages: int = 0
    total_cost: float = 0.0
    price_per_page: Optional[float] = None
    currency: str = "GBP"


class ItemCreate(BaseModel):
    file_name: str
    file_url: str
    page_count: int = 1
    document_type: Optional[str] = None


class ItemUpdate(BaseModel):
    extracted_data: Optional[dict] = None
    mapped_data: Optional[dict] = None
    calculated_emissions_kg_co2e: Optional[float] = None


@router.post("/batches", status_code=201)
async def create_batch(
    organization_id: str,
    payload: BatchCreate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    # FIN-06 — Manual Processing is OFF by default and CarbonTally-Admin controlled.
    await ensure_manual_processing_allowed(repos, current_user, organization_id)
    return await repos.manual_extraction.create_batch(
        org_id=organization_id,
        batch_name=payload.batch_name,
        total_documents=payload.total_documents,
        total_pages=payload.total_pages,
        total_cost=payload.total_cost,
        currency=payload.currency,
        batch_description=payload.batch_description,
        price_per_page=payload.price_per_page,
        created_by=current_user.user_id,
    )


@router.get("/batches")
async def list_batches(
    organization_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    return {"batches": await repos.manual_extraction.list_batches_with_counts(organization_id)}


@router.get("/batches/{batch_id}")
async def get_batch(
    batch_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    batch = await repos.manual_extraction.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    ensure_org_access(current_user, batch.organization_id)
    return batch


@router.post("/batches/{batch_id}/items", status_code=201)
async def create_item(
    batch_id: str,
    payload: ItemCreate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    batch = await repos.manual_extraction.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    ensure_org_access(current_user, batch.organization_id)
    # FIN-06 — adding manual work to a batch is also governed.
    await ensure_manual_processing_allowed(repos, current_user, batch.organization_id)
    return await repos.manual_extraction.create_item(
        batch_id, payload.file_name, payload.file_url, payload.page_count,
        payload.document_type, "pending",
    )


@router.get("/batches/{batch_id}/items")
async def list_items(
    batch_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    batch = await repos.manual_extraction.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    ensure_org_access(current_user, batch.organization_id)
    return {"items": await repos.manual_extraction.list_items(batch_id)}


@router.put("/items/{item_id}")
async def update_item(
    item_id: str,
    payload: ItemUpdate,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    item = await repos.manual_extraction.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    batch = await repos.manual_extraction.get_batch(item.batch_id)
    if batch is None:
        # Fail closed: without the batch the organisation scope cannot be
        # established, so neither isolation nor the FIN-06 entitlement can be
        # evaluated. (Previously such an item was written without any
        # organisation check at all.)
        raise HTTPException(status_code=409, detail="item batch not found")
    ensure_org_access(current_user, batch.organization_id)
    # FIN-06 (P8 remediation IV-01) — manual extraction data entry is manual
    # processing: it must carry the CarbonTally-Admin entitlement, not merely
    # organisation membership.
    await ensure_manual_processing_allowed(repos, current_user, batch.organization_id)
    updated = await repos.manual_extraction.update_item(
        item_id,
        payload.extracted_data,
        payload.mapped_data,
        payload.calculated_emissions_kg_co2e,
        current_user.user_id,
    )
    # WS4 Gate 6 (workstream W4 / gap G6-D) — human extraction edits are
    # attributable (item-level audit, machine-origin flag when the previous
    # extractor was the automatic pipeline's zero-UUID marker).
    if payload.extracted_data is not None:
        from api.audit_helpers import (
            changed_extraction_keys,
            record_item_extraction_edit,
        )

        await record_item_extraction_edit(
            repos,
            item_id=item_id,
            action="org_item_extraction:edited",
            actor=current_user.user_id,
            correlation_id=(
                str(item.document_processing_queue_id)
                if item.document_processing_queue_id
                else item_id
            ),
            job_id=(
                str(item.document_processing_queue_id)
                if item.document_processing_queue_id
                else None
            ),
            status_from=item.status,
            status_to=updated.status if updated is not None else "extracted",
            previous_extracted_by=item.extracted_by,
            changed_keys=changed_extraction_keys(
                item.extracted_data, payload.extracted_data
            ),
        )
    return updated
