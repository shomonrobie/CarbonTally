"""V3 organisation-scoped search (G-P1-1).

The backend is the search boundary: the query is always org-scoped and only the
organisation's own rows are searched. The UI (nav search box) is presentation
only — it never holds a copy of the data.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_repositories,
)
from auth import AuthUser, require_org_member

router = APIRouter(prefix="/api/v3/search", tags=["V3 — Search"])


@router.get("")
async def search_org(
    organization_id: str = Query(..., min_length=1),
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=50),
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Org-scoped keyword search across documents, items, issues, suppliers,
    facilities, vehicles and reports."""
    ensure_org_access(current_user, organization_id)
    results = await repos.search.search_org(organization_id, q, limit)
    return {"query": q, "organization_id": organization_id, "results": results}
