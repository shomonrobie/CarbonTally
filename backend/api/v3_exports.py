"""V3 exports surface (V3 legacy-capability reimplementation).

CSV/JSON exports computed from typed repository queries (emissions logs and
documents). Data is read-only; no export-history table is assumed.
"""
from __future__ import annotations

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_repositories,
)
from auth import AuthUser, require_org_member

router = APIRouter(prefix="/api/v3/exports", tags=["V3 — Exports"])


def _csv_response(rows: list[dict], filename: str) -> StreamingResponse:
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/emissions.csv")
async def export_emissions_csv(
    organization_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    scope: Optional[str] = None,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    rows = await repos.exports.emissions(organization_id, start_date, end_date, scope)
    return _csv_response(rows, "emissions.csv")


@router.get("/emissions.json")
async def export_emissions_json(
    organization_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    scope: Optional[str] = None,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    rows = await repos.exports.emissions(organization_id, start_date, end_date, scope)
    return JSONResponse({"emissions": rows})


@router.get("/documents.csv")
async def export_documents_csv(
    organization_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    rows = await repos.exports.documents(organization_id)
    return _csv_response(rows, "documents.csv")
