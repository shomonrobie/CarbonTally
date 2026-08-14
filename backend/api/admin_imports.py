"""Admin import-batch endpoints (prep-pack Phase 10.3, imports).

Read-only exposure of the existing :class:`data.imports.ImportsRepository` batch
lifecycle. The API does **not** create a second import engine and does **not**
import data: every endpoint reads existing ``import_batches`` state only.

Access: ``require_admin`` (existing ``backend/auth.py`` staff-admin check).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from api.contracts import (
    ImportActiveOut,
    ImportBatchListOut,
    ImportBatchOut,
    import_batch_out,
)
from api.dependencies import RepositoryBundle, get_repositories, require_admin

router = APIRouter(prefix="/api/v2/admin/imports", tags=["Admin Imports"])


@router.get("", response_model=ImportBatchListOut)
async def list_import_batches(
    provider: str = Query(..., min_length=1, description="Provider key (e.g. defra, seai)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> ImportBatchListOut:
    """List the import-batch history for ``provider`` (newest first)."""
    history = await repos.imports.get_history(provider)
    page = history[offset : offset + limit]
    return ImportBatchListOut(
        provider=provider,
        total=len(history),
        batches=[import_batch_out(b) for b in page],
    )


@router.get("/active", response_model=ImportActiveOut)
async def get_active_batch(
    provider: str = Query(..., min_length=1, description="Provider key (e.g. defra, seai)"),
    reporting_year: int = Query(..., ge=1990, le=2100),
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> ImportActiveOut:
    """Return the currently active batch for ``provider`` + ``reporting_year``.

    ``batch`` is ``null`` when no batch is active for that provider/year (a
    valid state — no data has been imported yet).
    """
    batch = await repos.imports.get_active(provider, reporting_year)
    return ImportActiveOut(
        provider=provider,
        reporting_year=reporting_year,
        batch=import_batch_out(batch) if batch is not None else None,
    )


@router.get("/{batch_id}", response_model=ImportBatchOut)
async def get_import_batch(
    batch_id: str,
    current_user=Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> ImportBatchOut:
    """Return a single import batch by id (404 when unknown)."""
    batch = await repos.imports.get(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail=f"import batch {batch_id} not found")
    return import_batch_out(batch)
