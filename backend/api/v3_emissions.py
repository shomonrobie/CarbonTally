"""V3 emissions-intelligence surface (V3 Phase 4).

Read-only, org-scoped intelligence over the authoritative persisted data, plus
the single authoritative calculation chain:

    Activity data → V3 factor matching → V3 calculation engine
        → persisted snapshot + emissions_log → provenance → API

Design rules followed here:

* **The frontend never calculates.** ``POST /calculate`` runs the authoritative
  ``engines/calculation.py`` through the same dependency factory as ``/api/v2``;
  the client supplies activity inputs (or an explicit factor id), never a result.
* **Matching stays authoritative.** ``POST /calculate`` (no explicit factor)
  uses the V3 ``FactorMatchingEngine``; the standalone match contract remains
  ``POST /api/v2/factor-match`` (already mounted, correct — not duplicated).
* **History is persisted, never recomputed.** Calculation history, details and
  provenance read ``calculation_snapshots`` (append-only, ADR-5); the verify
  endpoint recomputes only to *check* a stored result.
* **No invented metrics.** Every breakdown maps to a real column: scope/unit on
  ``emissions_logs``; asset/facility via ``asset_id`` and ``metadata->>'facility_id'``;
  supplier via ``emissions_logs.supplier_id``; activity via the joined
  ``calculation_snapshots.activity_type``.
"""
from __future__ import annotations

import uuid
from datetime import date as _Date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator

from api.contracts import calculation_out
from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_calculation_engine,
    get_matching_engine,
    get_repositories,
    require_org_member,
)
from auth import AuthUser
from core.types import DateRange
from domain.factor import RESULT_PRECISION
from domain.matching import MatchRequest
from engines.calculation import CalculationEngine, CalculationRequest
from engines.factor_matching import FactorMatchingEngine

router = APIRouter(prefix="/api/v3/emissions", tags=["V3 — Emissions Intelligence"])


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------


#: Accepted scope aliases → the canonical GHG Protocol vocabulary
#: (``core.types.Scope``). The V3 Emissions form historically sent ``scope1``;
#: the authoritative persisted values (validated by ``ValidationEngine`` and
#: stored on ``emissions_logs``/``calculation_snapshots``) are ``Scope 1`` etc.
SCOPE_ALIASES: dict[str, str] = {
    "scope1": "Scope 1",
    "scope 1": "Scope 1",
    "scope2": "Scope 2",
    "scope 2": "Scope 2",
    "scope3": "Scope 3",
    "scope 3": "Scope 3",
    "outside of scopes": "Outside of Scopes",
}

#: The full supported scope set (canonical values accepted verbatim).
SUPPORTED_SCOPES: set[str] = set(SCOPE_ALIASES.values())


def normalize_scope(value: Optional[str]) -> Optional[str]:
    """Map a client-supplied scope to the canonical GHG Protocol label.

    ``None`` passes through (the calculation engine resolves the factor scope).
    Known aliases (``scope1`` → ``Scope 1``) are normalised; an unsupported
    value is rejected here (HTTP 422) so invalid scopes never reach the
    validation engine as blocking report-generation errors.
    """
    if value is None:
        return None
    key = value.strip().lower()
    canonical = SCOPE_ALIASES.get(key)
    if canonical is not None:
        return canonical
    if key in SUPPORTED_SCOPES:
        return value.strip()
    raise ValueError(
        f"unsupported scope {value!r}; expected one of {sorted(SUPPORTED_SCOPES)}"
    )


class CalculateIn(BaseModel):
    """Authoritative calculation request (client never supplies the result).

    Exactly one of ``factor_id`` / ``customer_factor_id`` may be provided;
    when neither is provided the authoritative matching engine resolves the
    factor (customer factors matched first per D-cf-5 when an org is scoped).
    """

    organization_id: str
    activity: str
    quantity: str
    quantity_unit: str
    date: _Date
    reporting_year: int
    country: str = "GB"
    unit: Optional[str] = None
    scope: Optional[str] = None
    factor_id: Optional[str] = None
    customer_factor_id: Optional[str] = None
    asset_id: Optional[str] = None
    facility_id: Optional[str] = None
    activity_type: Optional[str] = None
    methodology: str = "direct_multiply"
    source_file: Optional[str] = None
    source_page: Optional[int] = None
    source_item_id: Optional[str] = None

    @field_validator("scope")
    @classmethod
    def _canonical_scope(cls, value: Optional[str]) -> Optional[str]:
        """Normalise scope aliases to the canonical GHG Protocol vocabulary."""
        return normalize_scope(value)


# ---------------------------------------------------------------------------
# Helpers (pure — unit-tested without a database)
# ---------------------------------------------------------------------------


def build_period(start_date: _Date, end_date: _Date) -> DateRange:
    """Build an inclusive period, rejecting an inverted range with HTTP 422."""
    if end_date < start_date:
        raise HTTPException(
            status_code=422,
            detail="end_date must not be before start_date",
        )
    return DateRange(start_date=start_date, end_date=end_date)


def shape_snapshot(row: dict) -> dict:
    """Present one immutable snapshot row in the human-readable history contract."""
    return {
        "id": row["id"],
        "organization_id": row["organization_id"],
        "activity": row["activity"],
        "activity_type": row["activity_type"],
        "quantity": str(row["quantity"]),
        "quantity_unit": row["quantity_unit"],
        "co2e_multiplier": str(row["co2e_multiplier"]),
        "co2e_kg": str(row["co2e_kg"]),
        "scope": row["scope"],
        "date": row["date"],
        "reporting_year": row["reporting_year"],
        "factor_id": row["factor_id"],
        "factor_source": row["factor_source"],
        "factor_set": row["factor_set"],
        "factor_kind": row.get("factor_kind") or "emission_factor",
        "customer_factor_id": row["customer_factor_id"],
        "methodology": row["methodology"],
        "algorithm_version": row["algorithm_version"],
        "calculated_at": row["calculated_at"],
        "calculated_by": row["calculated_by"],
        "content_hash": row["content_hash"],
    }


def verify_snapshot_row(row: dict) -> dict:
    """Audit-time reproducibility check over a stored snapshot row.

    Recomputes ``quantity × co2e_multiplier`` (``RESULT_PRECISION``) and the
    SHA-256 content hash of the canonical inputs, comparing both to the stored
    values. Pure — deterministic, no database access.
    """
    import hashlib

    quantity = Decimal(str(row["quantity"]))
    multiplier = Decimal(str(row["co2e_multiplier"]))
    stored = Decimal(str(row["co2e_kg"]))
    recomputed = (quantity * multiplier).quantize(RESULT_PRECISION)
    match = recomputed == stored

    canonical = "|".join(
        [
            str(quantity),
            str(row["quantity_unit"]),
            str(multiplier),
            str(row.get("factor_kind") or "emission_factor"),
            str(row.get("factor_id") or ""),
            str(row.get("customer_factor_id") or ""),
            str(row.get("scope") or ""),
            str(row["date"]),
            str(row["reporting_year"]),
            str(row["methodology"]),
            str(row["algorithm_version"]),
        ]
    )
    recomputed_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    hash_match = recomputed_hash == str(row["content_hash"])
    return {
        "match": match,
        "discrepancy": str(recomputed - stored) if not match else None,
        "content_hash_match": hash_match,
        "recomputed_co2e_kg": str(recomputed),
        "recomputed_content_hash": recomputed_hash,
        "tampered": not (match and hash_match),
    }


def filter_factors(factors, *, scope=None, factor_source=None, factor_set=None) -> list:
    """In-memory filter for the factor interface (kept DB-surface minimal)."""
    out = factors
    if scope is not None:
        out = [f for f in out if f.scope == scope]
    if factor_source is not None:
        out = [f for f in out if f.factor_source == factor_source]
    if factor_set is not None:
        out = [f for f in out if f.factor_set == factor_set]
    return out


def _jsonable(value):
    """Convert raw SQL values into JSON-safe primitives (Decimal → str)."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (_Date, datetime)):
        return value.isoformat()
    return value


def jsonable_rows(rows: list[dict]) -> list[dict]:
    """Present raw aggregate rows (Decimal quantities/co2e) as JSON-safe dicts."""
    return [{k: _jsonable(v) for k, v in row.items()} for row in rows]


# ---------------------------------------------------------------------------
# Emissions dashboard / reporting-period views
# ---------------------------------------------------------------------------


@router.get("/dashboard")
async def emissions_dashboard(
    organization_id: str,
    start_date: _Date,
    end_date: _Date,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Reporting-period dashboard: total, scope, activity, supplier, facility
    and asset breakdowns — every figure from persisted ``emissions_logs`` /
    ``calculation_snapshots`` rows."""
    ensure_org_access(current_user, organization_id)
    period = build_period(start_date, end_date)

    by_scope = await repos.logs.aggregate(organization_id, period, "scope")
    by_month = await repos.logs.aggregate(organization_id, period, "month")
    by_asset = await repos.logs.aggregate(organization_id, period, "asset")
    by_facility = await repos.logs.aggregate(organization_id, period, "facility")
    suppliers = await repos.logs.aggregate_by_supplier(organization_id, period)
    activities = await repos.logs.aggregate_by_activity(organization_id, period)

    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "total_co2e_kg": str(by_scope.total_co2e_kg),
        "total_rows": by_scope.total_rows,
        "by_scope": {k: str(v) for k, v in by_scope.by_scope.items()},
        "by_month": {k: str(v) for k, v in by_month.by_group.items()},
        "by_asset": {k: str(v) for k, v in by_asset.by_group.items()},
        "by_facility": {k: str(v) for k, v in by_facility.by_group.items()},
        "by_supplier": jsonable_rows(suppliers),
        "by_activity": jsonable_rows(activities),
    }


@router.get("/scope-breakdown")
async def scope_breakdown(
    organization_id: str,
    start_date: _Date,
    end_date: _Date,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Scope 1 / 2 / 3 (and Outside of Scopes) totals over a period."""
    ensure_org_access(current_user, organization_id)
    period = build_period(start_date, end_date)
    agg = await repos.logs.aggregate(organization_id, period, "scope")
    return {
        "total_co2e_kg": str(agg.total_co2e_kg),
        "by_scope": {k: str(v) for k, v in agg.by_scope.items()},
    }


# ---------------------------------------------------------------------------
# Calculation history / details / provenance
# ---------------------------------------------------------------------------


@router.get("/calculations")
async def calculation_history(
    organization_id: str,
    start_date: Optional[_Date] = None,
    end_date: Optional[_Date] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Calculation history from the persisted snapshots (never recomputed)."""
    ensure_org_access(current_user, organization_id)
    period = build_period(
        start_date or _Date(1990, 1, 1),
        end_date or _Date.today(),
    )
    total = await repos.logs.count_snapshots(organization_id, period)
    rows = await repos.logs.list_snapshots(organization_id, period, limit, offset)
    return {
        "total": total,
        "calculations": [shape_snapshot(r) for r in rows],
    }


@router.get("/calculations/{snapshot_id}")
async def calculation_detail(
    snapshot_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """One calculation's inputs, result and human-readable provenance."""
    row = await repos.logs.get_snapshot(snapshot_id)
    if row is None:
        raise HTTPException(status_code=404, detail="calculation not found")
    ensure_org_access(current_user, row["organization_id"])
    factor = (
        await repos.factors.get(str(row["factor_id"]))
        if row.get("factor_id")
        else None
    )
    customer_factor = (
        await repos.customer_factors.get(str(row["customer_factor_id"]))
        if row.get("customer_factor_id")
        else None
    )
    return {
        "snapshot": shape_snapshot(row),
        "factor": factor,
        "customer_factor": customer_factor,
        "provenance": {
            "factor_kind": row.get("factor_kind") or "emission_factor",
            "factor_source": row.get("factor_source"),
            "factor_set": row.get("factor_set"),
            "import_batch_id": row.get("import_batch_id"),
            "reporting_year": row.get("reporting_year"),
            "methodology": row.get("methodology"),
            "algorithm_version": row.get("algorithm_version"),
            "content_hash": row.get("content_hash"),
            "calculated_at": row.get("calculated_at"),
            "calculated_by": row.get("calculated_by"),
            "request_id": row.get("request_id"),
        },
    }


@router.get("/{log_id}/evidence")
async def emission_evidence(
    log_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """D33 — trace one emission result to its exact source evidence.

    Chain: emissions_log -> calculation_snapshot -> extraction item ->
    source document (organization_files) -> private-storage signed URL.

    Returns the calculation, the extracted/mapped line, the factor and the
    source document metadata + an authorized signed URL (never a public URL).
    """
    from domain.audit import AuditEntry
    from domain.evidence import build_evidence_record
    from services.storage import path_from_url, storage_signed_url

    log = await repos.logs.get(log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="emission not found")
    ensure_org_access(current_user, log.organization_id)

    snapshot = None
    if log.snapshot_id:
        snapshot = await repos.logs.get_snapshot(log.snapshot_id)

    item = None
    item_id = snapshot.get("source_item_id") if snapshot else None
    if item_id:
        item = await repos.manual_extraction.get_item(str(item_id))

    file_row = None
    if item is not None and item.file_id:
        file_row = await repos.files.get(item.file_id)
    if file_row is None and item is not None:
        # Fallback: canonical path match (historical rows before D33 backfill).
        file_row = await repos.files.get_by_path(item.file_url)

    signed_url = ""
    if file_row is not None:
        signed_url = storage_signed_url(path_from_url(file_row.path))

    factor = None
    if snapshot and snapshot.get("factor_id"):
        factor = await repos.factors.get(str(snapshot["factor_id"]))
    customer_factor = None
    if snapshot and snapshot.get("customer_factor_id"):
        customer_factor = await repos.customer_factors.get(str(snapshot["customer_factor_id"]))

    evidence_record = build_evidence_record(
        emission=log,
        snapshot=snapshot,
        item=item,
        file_row=file_row,
        factor=factor,
        customer_factor=customer_factor,
    )

    # D33.1 — append-only evidence-access audit (ids only; never tokens/URLs).
    from datetime import datetime, timezone

    try:
        await repos.audit.record(
            AuditEntry(
                id=str(uuid.uuid4()),
                correlation_id=str(log.snapshot_id or log.id),
                entity_type="emissions_logs",
                entity_id=log.id,
                action="evidence.access",
                actor=current_user.user_id,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={
                    "organization_id": log.organization_id,
                    "snapshot_id": log.snapshot_id,
                    "source_file_id": file_row.id if file_row is not None else None,
                },
                reason="evidence record viewed",
            )
        )
    except Exception:  # noqa: BLE001 — audit must never break the read path
        pass

    return {
        "emission": {
            "id": log.id,
            "organization_id": log.organization_id,
            "snapshot_id": log.snapshot_id,
            "start_date": log.date,
            "raw_quantity": log.quantity,
            "unit": log.unit,
            "calculated_kg_co2e": log.calculated_kg_co2e,
            "scope": log.scope,
            "asset_id": log.asset_id,
            "created_at": log.created_at,
        },
        "calculation": shape_snapshot(snapshot) if snapshot else None,
        "source_item": (
            {
                "id": item.id,
                "file_name": item.file_name,
                "file_url": item.file_url,
                "file_id": item.file_id,
                "page_count": item.page_count,
                "document_type": item.document_type,
                "status": item.status,
                "extracted_data": item.extracted_data,
                "mapped_data": item.mapped_data,
                "calculated_emissions_kg_co2e": item.calculated_emissions_kg_co2e,
            }
            if item is not None
            else None
        ),
        "source_document": (
            {
                "id": file_row.id,
                "name": file_row.name,
                "path": file_row.path,
                "file_type": file_row.file_type,
                "size_bytes": file_row.size_bytes,
                "uploaded_by": file_row.uploaded_by,
                "uploaded_at": file_row.uploaded_at,
                "metadata": file_row.metadata,
                "signed_url": signed_url,
            }
            if file_row is not None
            else None
        ),
        "factor": factor,
        "customer_factor": customer_factor,
        "evidence": {
            "source_item_id": item_id,
            "source_file": snapshot.get("source_file") if snapshot else None,
            "source_page": snapshot.get("source_page") if snapshot else None,
            "signed_url": signed_url,
            "authorized_org": log.organization_id,
        },
        "evidence_record": evidence_record,
    }


@router.post("/calculations/{snapshot_id}/verify")
async def verify_calculation(
    snapshot_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Reproducibility check: recompute and compare a stored snapshot."""
    row = await repos.logs.get_snapshot(snapshot_id)
    if row is None:
        raise HTTPException(status_code=404, detail="calculation not found")
    ensure_org_access(current_user, row["organization_id"])
    return verify_snapshot_row(row)


# ---------------------------------------------------------------------------
# Emission-factor interface (managed factors; customer factors stay on
# /api/v3/customer-factors — org-isolated surface already implemented)
# ---------------------------------------------------------------------------


@router.get("/factors")
async def factor_search(
    query: Optional[str] = None,
    reporting_year: Optional[int] = None,
    country: Optional[str] = None,
    scope: Optional[str] = None,
    unit: Optional[str] = None,
    factor_source: Optional[str] = None,
    factor_set: Optional[str] = None,
    provider: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Factor search with provenance filters (reporting year, country, scope,
    unit, factor source/set, provider)."""
    factors = await repos.factors.find_by_activity(
        query or "",
        unit=unit,
        year=reporting_year,
        country=country,
        provider=provider,
        limit=limit,
    )
    factors = filter_factors(
        factors,
        scope=scope,
        factor_source=factor_source,
        factor_set=factor_set,
    )
    return {"total": len(factors), "factors": factors}


@router.get("/factors/{factor_id}")
async def factor_detail(
    factor_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """One managed factor with provenance and usage statistics."""
    factor = await repos.factors.get(factor_id)
    if factor is None:
        raise HTTPException(status_code=404, detail="factor not found")
    count = await repos.logs.snapshot_count_for_factor(factor_id)
    span = await repos.logs.factor_usage_span(factor_id)
    return {
        "factor": factor,
        "provenance": {
            "factor_source": factor.factor_source,
            "factor_set": factor.factor_set,
            "import_batch_id": factor.import_batch_id,
            "provider_key": factor.provider_key,
            "reporting_year": factor.reporting_year,
            "country": factor.country,
            "unit": factor.unit,
            "scope": factor.scope,
            "natural_key": list(factor.natural_key),
        },
        "usage": {
            "snapshot_count": count,
            **(span or {}),
        },
    }


# ---------------------------------------------------------------------------
# Authoritative calculation chain
# ---------------------------------------------------------------------------


@router.post("/calculate")
async def calculate(
    payload: CalculateIn,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
    matching: FactorMatchingEngine = Depends(get_matching_engine),
    engine: CalculationEngine = Depends(get_calculation_engine),
):
    """Authoritative calculation: activity inputs → V3 factor matching (or an
    explicit factor) → CalculationEngine → persisted snapshot + emissions log.

    The response is the engine's ``CalculationOut`` (never a client-supplied
    figure); ``content_hash`` + snapshot id give the frontend the provenance
    pointer for history/details/verify.
    """
    ensure_org_access(current_user, payload.organization_id)
    try:
        quantity = Decimal(payload.quantity)
    except (InvalidOperation, ValueError):
        raise HTTPException(status_code=422, detail="quantity must be a number")
    if quantity < 0:
        raise HTTPException(status_code=422, detail="quantity must be >= 0")

    factor = None
    customer_factor = None
    match_request_id = str(uuid.uuid4())

    if payload.factor_id and payload.customer_factor_id:
        raise HTTPException(
            status_code=422,
            detail="factor_id and customer_factor_id are mutually exclusive",
        )
    if payload.factor_id:
        factor = await repos.factors.get(payload.factor_id)
        if factor is None:
            raise HTTPException(status_code=404, detail="factor not found")
    elif payload.customer_factor_id:
        customer_factor = await repos.customer_factors.get(payload.customer_factor_id)
        if customer_factor is None:
            raise HTTPException(status_code=404, detail="customer factor not found")
        if customer_factor.status != "active":
            raise HTTPException(status_code=422, detail="customer factor is not active")
        ensure_org_access(current_user, customer_factor.organization_id)
    else:
        match_result = await matching.match(
            MatchRequest(
                id=match_request_id,
                activity=payload.activity,
                country=payload.country,
                reporting_year=payload.reporting_year,
                unit=payload.quantity_unit,
                scope=payload.scope,
                organization_id=payload.organization_id,
            )
        )
        match_request_id = match_result.request_id or match_request_id
        if match_result.status != "matched":
            raise HTTPException(
                status_code=422,
                detail=f"no factor matched ({match_result.status})",
            )
        if match_result.factor_kind == "customer_factor":
            customer_factor = await repos.customer_factors.get(
                match_result.customer_factor_id
            )
            if customer_factor is None:
                raise HTTPException(404, detail="matched customer factor not found")
        else:
            factor = match_result.factor

    if factor is None and customer_factor is None:
        raise HTTPException(status_code=422, detail="no factor resolved for calculation")

    request = CalculationRequest(
        match_request_id=match_request_id,
        organization_id=payload.organization_id,
        quantity=quantity,
        quantity_unit=payload.quantity_unit,
        date=payload.date,
        reporting_year=payload.reporting_year,
        activity=payload.activity,
        activity_type=payload.activity_type
        or (factor.activity_type if factor is not None else customer_factor.activity_type),
        scope=payload.scope,
        methodology=payload.methodology,
        source_file=payload.source_file,
        source_page=payload.source_page,
        source_item_id=payload.source_item_id,
        asset_id=payload.asset_id,
        facility_id=payload.facility_id,
        factor=factor,
        customer_factor=customer_factor,
    )
    result = await engine.calculate(request)
    return calculation_out(result)






