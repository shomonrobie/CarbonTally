"""V3 customer verification surface (V3 legacy-capability reimplementation).

Source-document ↔ result verification: approve / reject / correct decisions
recorded on ``customer_documents``.
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
from auth import AuthUser, require_org_member

router = APIRouter(prefix="/api/v3/verifications", tags=["V3 — Verifications"])


class VerificationDecision(BaseModel):
    notes: Optional[str] = None
    extraction: Optional[dict] = None


@router.get("/pending")
async def list_pending(
    organization_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    return {"documents": await repos.verifications.list_pending(organization_id)}


@router.post("/{document_id}/approve")
async def approve_document(
    document_id: str,
    organization_id: str,
    payload: VerificationDecision,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    result = await repos.verifications.verify(
        document_id, organization_id, "approved", current_user.user_id,
        payload.notes, payload.extraction,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="document not found")
    return result


@router.post("/{document_id}/reject")
async def reject_document(
    document_id: str,
    organization_id: str,
    payload: VerificationDecision,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    result = await repos.verifications.verify(
        document_id, organization_id, "rejected", current_user.user_id,
        payload.notes, payload.extraction,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="document not found")
    return result


@router.post("/{document_id}/correct")
async def correct_document(
    document_id: str,
    organization_id: str,
    payload: VerificationDecision,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    result = await repos.verifications.verify(
        document_id, organization_id, "needs_revision", current_user.user_id,
        payload.notes, payload.extraction,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="document not found")
    return result
