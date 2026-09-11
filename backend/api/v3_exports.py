"""V3 exports surface (V3 legacy-capability reimplementation).

CSV/JSON exports computed from typed repository queries (emissions logs and
documents). Data is read-only; no export-history table is assumed.
"""
from __future__ import annotations

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse

from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    ensure_org_audit_access,
    get_repositories,
)
from auth import AuthUser, get_current_user, require_org_member

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
    limit: int = 100,
    offset: int = 0,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """List persisted emissions rows with the shared server-side pagination
    contract (``emissions`` + authoritative ``total``). The CSV export remains a
    full-data download; the JSON surface is page-windowed so large histories
    never force an over-broad result set into the UI."""
    ensure_org_access(current_user, organization_id)
    rows = await repos.exports.emissions(
        organization_id, start_date, end_date, scope, limit=max(1, min(limit, 500)), offset=max(0, offset)
    )
    total = await repos.exports.count_emissions(
        organization_id, start_date, end_date, scope
    )
    return JSONResponse({"emissions": rows, "total": total})


@router.get("/documents.csv")
async def export_documents_csv(
    organization_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    rows = await repos.exports.documents(organization_id)
    return _csv_response(rows, "documents.csv")


@router.get("/audit-package.json")
async def export_audit_package(
    organization_id: str,
    reporting_year: Optional[int] = None,
    limit: int = 500,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Phase 7 — scoped audit/evidence package (JSON).

    Contains CarbonTally-generated evidence only: calculation snapshots with
    factor provenance and integrity hashes, the organisation activity timeline
    and the evidence-readiness indicator, plus a package hash. It is **not** an
    assurance opinion — the payload carries an explicit notice and
    ``not_assurance: true``. Authorization: organisation owner/admin, an
    authorized consultant (active client grant), or internal staff.
    """
    await ensure_org_audit_access(current_user, repos, organization_id)
    package = await repos.reporting.audit_package(
        organization_id, reporting_year=reporting_year, limit=limit
    )
    return JSONResponse(jsonable_encoder(package))
