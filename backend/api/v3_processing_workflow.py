"""V3 processing-workflow surface (V3 Phase 3).

The end-to-end document-processing pipeline for outsourced manual extraction,
org-scoped:

    Source → Extraction → Mapping → Validation → Calculation → Review → Approval

Everything lives on the existing RC2 tables — ``manual_extraction_batches`` /
``manual_extraction_items`` carry the full pipeline columns (extracted_data,
mapped_data, emission_factor_used, calculated_emissions_kg_co2e, QC and customer
review stamps) and the first-class ``issues`` table (ADR-V3-009) records
validation findings linked via ``work_item_id``. No schema change is required.

Surfaces in this module:

* **dashboard / status / batch progress** — pipeline aggregate views.
* **batch lifecycle** — start (assign), complete, cancel.
* **item workflow** — start, extract (data entry), map, validate, calculate,
  customer review (verification).
* **workspace** — the split-screen source/data contract for one item.
* **queues** — next-item and per-stage listings; customer-review queue; issues.
"""
from __future__ import annotations

import uuid
from datetime import date as _Date
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.contracts import calculation_out
from api.dependencies import (
    RepositoryBundle,
    ensure_processing_org_access,
    get_calculation_engine,
    get_repositories,
)
from auth import AuthUser, require_auth, require_org_admin
from core.units import mapping_no_factors_reason, resolve_unit_for_factor
from domain.issue import Issue
from domain.partners import (
    ITEM_STATUS_FLOW,
    WORKFLOW_STAGES,
    WORKFLOW_STAGE_STATUSES,
    can_transition_item_status,
)
from engines.calculation import CalculationEngine, CalculationRequest
from engines.processing_workflow import (
    has_blocking_findings,
    validate_processing_item,
)
from services.storage import signed_item

router = APIRouter(prefix="/api/v3/processing", tags=["V3 — Processing Workflow"])

#: The in-flight (working) status reached when an operator claims a stage.
_STAGE_WORKING_STATUS: dict[str, str] = {
    "source": "extracting",
    "extraction": "extracting",
    "mapping": "mapping",
    "validation": "validating",
    "calculation": "calculating",
    "review": "customer_review",
}


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------


class BatchStart(BaseModel):
    assigned_to: Optional[str] = None
    sla_deadline: Optional[str] = None


class ItemStart(BaseModel):
    stage: str


class ExtractPayload(BaseModel):
    extracted_data: dict = {}


class MapPayload(BaseModel):
    mapped_data: dict = {}
    mapped_facility_id: Optional[str] = None
    mapped_asset_id: Optional[str] = None
    mapped_supplier_id: Optional[str] = None
    emission_factor_used: Optional[str] = None


class CalculatePayload(BaseModel):
    """Inputs for the authoritative calculation (the client never supplies the
    result — the engine computes and persists ``co2e_kg``)."""

    asset_id: Optional[str] = None
    facility_id: Optional[str] = None
    date: Optional[_Date] = None
    activity: Optional[str] = None
    activity_type: Optional[str] = None
    scope: Optional[str] = None
    methodology: str = "direct_multiply"
    # D33.1 — optional exact source-location precision (page) persisted on the
    # snapshot when the pipeline reliably knows it. Never fabricated.
    source_page: Optional[int] = None


class CustomerReviewPayload(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None
    customer_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stage_for_status(status: Optional[str]) -> Optional[str]:
    for stage, statuses in WORKFLOW_STAGE_STATUSES.items():
        if status in statuses:
            return stage
    return None


async def _get_checked_item(
    current_user: AuthUser,
    repos: RepositoryBundle,
    item_id: str,
) -> tuple:
    """Load an item + its batch and enforce organisation isolation.

    PO Decision 3 — consultants with an ACTIVE grant may operate their own
    customers' processing items (the grant is re-checked server-side).
    """
    item = await repos.manual_extraction.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    batch = await repos.manual_extraction.get_batch(item.batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    await ensure_processing_org_access(current_user, repos, batch.organization_id)
    return item, batch


def _require_transition(item, target: str) -> None:
    """Reject an item transition the state machine does not permit."""
    if not can_transition_item_status(item.status, target):
        raise HTTPException(
            status_code=409,
            detail=f"invalid item transition {item.status!r} -> {target!r}",
        )


async def _open_validation_issues(
    repos: RepositoryBundle,
    item,
    batch,
    findings,
    actor: str,
) -> list[Issue]:
    """Persist blocking validation findings as first-class issues (work_item
    scoped, org + batch context). Returns the created issues."""
    created: list[Issue] = []
    for finding in findings:
        if finding.severity != "error":
            continue
        issue = Issue(
            id=str(uuid.uuid4()),
            title=f"Validation: {finding.code}",
            description=finding.message,
            issue_type="exception",
            severity="medium",
            priority=1,
            status="open",
            organization_id=batch.organization_id,
            batch_id=batch.id,
            work_item_id=item.id,
            created_by=actor,
            updated_by=actor,
        )
        created.append(await repos.issues.save(issue))
    return created


async def _org_checked_batch(current_user, repos, batch):
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    await ensure_processing_org_access(current_user, repos, batch.organization_id)
    return batch


# ---------------------------------------------------------------------------
# Dashboard / status / batch progress
# ---------------------------------------------------------------------------


@router.get("/dashboard")
async def processing_dashboard(
    organization_id: str,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Processing dashboard — batches, items per stage, queue lengths."""
    await ensure_processing_org_access(current_user, repos, organization_id)
    return await repos.manual_extraction.workflow_dashboard(organization_id)


@router.get("/status")
async def processing_status(
    organization_id: str,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Processing status — per-stage pipeline counts + overall progress."""
    await ensure_processing_org_access(current_user, repos, organization_id)
    return await repos.manual_extraction.workflow_status(organization_id)


@router.get("/batches/{batch_id}/progress")
async def batch_progress(
    batch_id: str,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Real-time progress of one batch across the pipeline stages."""
    batch = await repos.manual_extraction.get_batch(batch_id)
    await _org_checked_batch(current_user, repos, batch)
    progress = await repos.manual_extraction.batch_progress(batch_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="batch not found")
    return progress


# ---------------------------------------------------------------------------
# Batch lifecycle (org admin)
# ---------------------------------------------------------------------------


@router.post("/batches/{batch_id}/start")
async def start_batch(
    batch_id: str,
    payload: BatchStart,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Start (and optionally assign) a batch; items become eligible for work."""
    batch = await repos.manual_extraction.get_batch(batch_id)
    await _org_checked_batch(current_user, repos, batch)
    if batch.status not in ("open", "in_progress"):
        raise HTTPException(
            status_code=409,
            detail=f"batch {batch.status!r} cannot be started",
        )
    updated = await repos.manual_extraction.update_batch(
        batch_id,
        status="in_progress",
        assigned_to=payload.assigned_to,
        assigned_by=current_user.user_id,
        updated_by=current_user.user_id,
    )
    return updated


@router.post("/batches/{batch_id}/complete")
async def complete_batch(
    batch_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Complete a batch (completion stamps + actual completion date)."""
    batch = await repos.manual_extraction.get_batch(batch_id)
    await _org_checked_batch(current_user, repos, batch)
    if batch.status in ("completed", "cancelled"):
        raise HTTPException(
            status_code=409, detail=f"batch is already {batch.status}"
        )
    return await repos.manual_extraction.complete_batch(batch_id, current_user.user_id)


@router.post("/batches/{batch_id}/cancel")
async def cancel_batch(
    batch_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Cancel a batch (terminal state; items are left untouched)."""
    batch = await repos.manual_extraction.get_batch(batch_id)
    await _org_checked_batch(current_user, repos, batch)
    if batch.status in ("completed", "cancelled"):
        raise HTTPException(
            status_code=409, detail=f"batch is already {batch.status}"
        )
    return await repos.manual_extraction.cancel_batch(batch_id, current_user.user_id)


# ---------------------------------------------------------------------------
# Item workflow (extraction → mapping → validation)
# ---------------------------------------------------------------------------


@router.post("/items/{item_id}/start")
async def start_item(
    item_id: str,
    payload: ItemStart,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Claim an item for a stage (operator data-entry workflow)."""
    if payload.stage not in WORKFLOW_STAGES and payload.stage != "qc":
        raise HTTPException(
            status_code=422,
            detail=f"unknown stage {payload.stage!r}; expected one of {WORKFLOW_STAGES}",
        )
    item, batch = await _get_checked_item(current_user, repos, item_id)
    if batch.status in ("completed", "cancelled"):
        raise HTTPException(
            status_code=409, detail=f"batch is {batch.status}"
        )
    working = _STAGE_WORKING_STATUS.get(payload.stage)
    if working is None:
        return item
    _require_transition(item, working)
    return await repos.manual_extraction.set_item_status(item_id, working)


@router.post("/items/{item_id}/extract")
async def extract_item(
    item_id: str,
    payload: ExtractPayload,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Data-entry: save extracted fields and advance the item to ``extracted``."""
    item, batch = await _get_checked_item(current_user, repos, item_id)
    _require_transition(item, "extracted")
    return await repos.manual_extraction.save_extracted_data(
        item_id, payload.extracted_data, current_user.user_id
    )


@router.post("/items/{item_id}/map")
async def map_item(
    item_id: str,
    payload: MapPayload,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Mapping: record mapped fields + factor/tenant references; item → ``mapped``."""
    item, batch = await _get_checked_item(current_user, repos, item_id)
    _require_transition(item, "mapped")
    if payload.emission_factor_used is None and not (payload.mapped_data or {}).get(
        "factor_id"
    ):
        raise HTTPException(
            status_code=422,
            detail="an emission factor must be selected (emission_factor_used "
            "or mapped_data.factor_id)",
        )
    return await repos.manual_extraction.save_mapped_data(
        item_id,
        payload.mapped_data,
        payload.mapped_facility_id,
        payload.mapped_asset_id,
        payload.mapped_supplier_id,
        payload.emission_factor_used,
    )


@router.post("/items/{item_id}/validate")
async def validate_item(
    item_id: str,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Run item-level validation.

    Blocking findings are persisted as first-class ``issues`` (linked via
    ``work_item_id``) and the item routes back to ``mapping`` for rework. A
    clean run advances the item to ``validated``.
    """
    item, batch = await _get_checked_item(current_user, repos, item_id)
    _require_transition(item, "validated")
    findings = validate_processing_item(item)
    issues = (
        await _open_validation_issues(
            repos, item, batch, findings, current_user.user_id
        )
        if has_blocking_findings(findings)
        else []
    )
    target = "mapping" if issues else "validated"
    updated = await repos.manual_extraction.set_item_status(item_id, target)
    if not issues:
        # ISC-2 / CL-26 — a clean validation run proves previously blocking
        # findings (EXTRACTION_MISSING_FIELD …) are resolved; close them so the
        # item no longer carries stale open issues into approval.
        await repos.issues.resolve_open_for_item(item.id, current_user.user_id)
    return {
        "item": updated,
        "findings": [f.__dict__ for f in findings],
        "blocking": bool(issues),
        "issues_created": issues,
    }


# ---------------------------------------------------------------------------
# Calculation → customer review (verification workflow)
# ---------------------------------------------------------------------------


@router.post("/items/{item_id}/calculate")
async def calculate_item(
    item_id: str,
    payload: CalculatePayload,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
    engine: CalculationEngine = Depends(get_calculation_engine),
):
    """Run the authoritative V3 calculation for an item.

    The client never supplies the result: the engine computes
    ``quantity × co2e_multiplier`` from the item's extracted quantity/unit and
    mapped factor, persists the immutable snapshot + ``emissions_logs`` row,
    and only then stamps ``calculated_emissions_kg_co2e`` on the item.
    """
    item, batch = await _get_checked_item(current_user, repos, item_id)
    _require_transition(item, "calculated")
    if batch.status in ("completed", "cancelled"):
        raise HTTPException(status_code=409, detail=f"batch is {batch.status}")

    extracted = item.extracted_data or {}
    mapped = item.mapped_data or {}

    raw_qty = extracted.get("quantity")
    if raw_qty in (None, ""):
        raise HTTPException(
            status_code=422, detail="extracted_data.quantity is required to calculate"
        )
    try:
        quantity = Decimal(str(raw_qty))
    except (InvalidOperation, ValueError):
        raise HTTPException(status_code=422, detail="quantity is not numeric")
    if quantity < 0:
        raise HTTPException(status_code=422, detail="quantity must be >= 0")

    quantity_unit = str(extracted.get("unit") or "").strip()
    if not quantity_unit:
        raise HTTPException(
            status_code=422, detail="extracted_data.unit is required to calculate"
        )

    factor_id = item.emission_factor_used or mapped.get("factor_id")
    if not factor_id:
        raise HTTPException(status_code=422, detail="no emission factor mapped to this item")
    factor = await repos.factors.get(factor_id)
    customer_factor = None
    if factor is None:
        customer_factor = await repos.customer_factors.get(factor_id)
        if customer_factor is None:
            raise HTTPException(status_code=404, detail="mapped factor not found")
        if customer_factor.status != "active":
            raise HTTPException(
                status_code=422, detail="mapped customer factor is not active"
            )

    activity = (payload.activity or "").strip() or str(extracted.get("activity") or "")
    activity_type = (payload.activity_type or "").strip() or mapped.get(
        "activity_type"
    ) or activity
    scope = payload.scope or (factor.scope if factor is not None else customer_factor.scope)
    reporting_year = (
        payload.date.year
        if payload.date is not None
        else (factor if factor is not None else customer_factor).reporting_year
    )

    # CL-3 / PRC-2 — unit alias normalisation: ``L`` against a ``litres`` factor
    # (and ``kWh`` against ``kWh (Gross CV)``) is legitimate equivalent input.
    # Genuine mismatches pass through unchanged and the engine rejects them.
    quantity_unit = resolve_unit_for_factor(
        quantity_unit, getattr(factor or customer_factor, "unit", None)
    )

    request = CalculationRequest(
        match_request_id=str(uuid.uuid4()),
        organization_id=batch.organization_id,
        quantity=quantity,
        quantity_unit=quantity_unit,
        date=payload.date or _Date.today(),
        reporting_year=reporting_year,
        activity=activity,
        activity_type=activity_type,
        scope=scope,
        methodology=payload.methodology,
        source_file=item.file_name,
        source_page=payload.source_page,
        source_item_id=item.id,  # D33: authoritative snapshot → extraction-item link
        asset_id=payload.asset_id,
        facility_id=payload.facility_id,
        factor=factor,
        customer_factor=customer_factor,
    )
    result = await engine.calculate(request)
    updated = await repos.manual_extraction.save_calculation(
        item_id, float(result.co2e_kg)
    )
    return {"item": updated, "calculation": calculation_out(result)}


@router.post("/items/{item_id}/customer-review")
async def customer_review_item(
    item_id: str,
    payload: CustomerReviewPayload,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Customer verification: approve or reject a processed item.

    A rejection records the reason and routes the item back to ``mapping``
    (rework loop). The verification decision is stamped with reviewer/time.

    D5 — the approval gate is org OWNER/ADMIN only (``require_org_admin``).
    Review (read) stays open to all org members; the approval action is the
    distinct approver responsibility and is never a frontend-only decision.

    D37: an APPROVAL of a subscribed organisation's item triggers the
    authoritative credit consumption BEFORE the item is marked approved
    (fail closed — processing is never marked complete without a successful
    charge). Pre-commercial orgs (no active subscription) are not charged.
    """
    item, batch = await _get_checked_item(current_user, repos, item_id)
    target = "approved" if payload.approved else "rejected"
    _require_transition(item, target)
    if not payload.approved and not (payload.rejection_reason or "").strip():
        raise HTTPException(
            status_code=422, detail="rejection_reason is required when rejecting"
        )
    if payload.approved:
        # D37: server-authoritative credit consumption (idempotent per item).
        try:
            from services.billing import BillingError, BillingService

            charge = await BillingService(repos).charge_processing(
                batch.organization_id,
                job={
                    "kind": "document",
                    "page_count": item.page_count or 1,
                    "item_count": len((item.extracted_data or {}).get("items", []))
                    if item.extracted_data else 0,
                },
                idempotency_key=f"charge:item:{item.id}",
                actor=current_user.user_id,
            )
        except BillingError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc))
    updated = await repos.manual_extraction.customer_review(
        item_id,
        payload.approved,
        current_user.user_id,
        payload.rejection_reason,
        payload.customer_notes,
    )
    if payload.approved:
        # ISC-2 / CL-26 — an approved item must not carry stale blocking
        # validation issues; the approval closes them (history preserved).
        await repos.issues.resolve_open_for_item(item.id, current_user.user_id)
    return updated


# ---------------------------------------------------------------------------
# Workspace (split-screen source/data) + mapping options
# ---------------------------------------------------------------------------


@router.get("/items/{item_id}/workspace")
async def item_workspace(
    item_id: str,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Split-screen workspace payload for one item.

    ``source`` (left panel — document viewer) and ``data`` (right panel —
    extraction/mapping/calculation) are returned side by side with the pipeline
    status, allowed transitions and linked issues.
    """
    item, batch = await _get_checked_item(current_user, repos, item_id)
    issues = await repos.issues.list_for_work_item(item.id)
    # D32 (P0): documents are served only via short-lived signed URLs.
    signed = signed_item(item)
    # OCR text + deterministic field suggestions persisted at upload time —
    # surfaced for human confirmation. ``ocr_suggestions`` are SUGGESTIONS only;
    # confirmed values live in ``data.extracted_data`` (set via /extract).
    ocr_text = None
    ocr_suggestions = None
    if item.file_id:
        src = await repos.files.get(item.file_id)
        if src is not None:
            ocr = (src.metadata or {}).get("ocr") or {}
            ocr_text = ocr.get("text")
            ocr_suggestions = ocr.get("suggested_data") or None
    return {
        "item": signed,
        "batch": batch,
        "source": {
            "file_url": signed.file_url,
            "file_name": item.file_name,
            "document_type": item.document_type,
            "page_count": item.page_count,
            "viewer_url": signed.file_url,
            "ocr_text": ocr_text,
            "ocr_suggestions": ocr_suggestions,
        },
        "data": {
            "extracted_data": item.extracted_data or {},
            "mapped_data": item.mapped_data or {},
            "mapped_facility_id": item.mapped_facility_id,
            "mapped_asset_id": item.mapped_asset_id,
            "mapped_supplier_id": item.mapped_supplier_id,
            "emission_factor_used": item.emission_factor_used,
            "calculated_emissions_kg_co2e": item.calculated_emissions_kg_co2e,
        },
        "status": {
            "status": item.status,
            "stage": _stage_for_status(item.status),
            "qc": {
                "quality_score": item.quality_score,
                "qc_by": item.qc_by,
                "qc_at": item.qc_at,
            },
            "customer_review": {
                "customer_approved": item.customer_approved,
                "customer_reviewed_by": item.customer_reviewed_by,
                "customer_reviewed_at": item.customer_reviewed_at,
                "customer_rejection_reason": item.customer_rejection_reason,
                "customer_notes": item.customer_notes,
            },
        },
        "issues": issues,
        "workflow": {
            "stages": list(WORKFLOW_STAGES),
            "allowed_transitions": ITEM_STATUS_FLOW.get(item.status or "pending", ()),
        },
    }


@router.get("/items/{item_id}/mapping-options")
async def mapping_options(
    item_id: str,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Mapping suggestions for the split-screen data panel: the organisation's
    facilities/assets/suppliers plus emission-factor candidates derived from the
    extracted activity/unit."""
    item, batch = await _get_checked_item(current_user, repos, item_id)
    extracted = item.extracted_data or {}
    activity = str(extracted.get("activity") or "").strip()
    unit = str(extracted.get("unit") or "").strip() or None
    factors = (
        await repos.factors.find_by_activity(activity, unit=unit, limit=20)
        if activity
        else []
    )
    return {
        "facilities": await repos.organizations.get_facilities(batch.organization_id),
        "assets": await repos.organizations.get_assets(batch.organization_id),
        "suppliers": await repos.suppliers.list_for_org(batch.organization_id),
        "factors": factors,
        # ISC-9 / CL-32 — honest spend-based mapping state. The DEFRA/SEAI
        # factor sets are physical-unit based; a currency activity (GBP/EUR/…)
        # has no applicable factor unless a customer factor is added. The
        # mapper surfaces an explicit, actionable reason instead of an empty
        # dead-end (never invents a factor, never treats GBP as a physical unit).
        "no_factors_reason": mapping_no_factors_reason(
            activity, unit, bool(factors)
        ),
    }


# ---------------------------------------------------------------------------
# Queues: next-item, per-stage, customer review, issues
# ---------------------------------------------------------------------------


@router.get("/next-item")
async def next_item(
    organization_id: str,
    stage: str,
    exclude_item_id: Optional[str] = None,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Return the next item awaiting ``stage`` work (operator high-volume flow)."""
    await ensure_processing_org_access(current_user, repos, organization_id)
    if stage not in WORKFLOW_STAGES and stage != "qc":
        raise HTTPException(
            status_code=422,
            detail=f"unknown stage {stage!r}; expected one of {WORKFLOW_STAGES}",
        )
    item = await repos.manual_extraction.next_item(
        organization_id, stage, exclude_item_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="no item waiting in this stage")
    return item


@router.get("/queue")
async def workflow_queue(
    organization_id: str,
    stage: str,
    limit: int = 100,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """List items currently in a workflow stage (org-scoped)."""
    await ensure_processing_org_access(current_user, repos, organization_id)
    if stage not in WORKFLOW_STAGES and stage != "qc":
        raise HTTPException(
            status_code=422,
            detail=f"unknown stage {stage!r}; expected one of {WORKFLOW_STAGES}",
        )
    return {
        "items": await repos.manual_extraction.list_by_stage(
            organization_id, stage, limit
        )
    }


@router.get("/customer-review")
async def customer_review_queue(
    organization_id: str,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Items awaiting customer verification (customer-review stage)."""
    await ensure_processing_org_access(current_user, repos, organization_id)
    return {
        "items": await repos.manual_extraction.list_customer_review(organization_id)
    }


@router.get("/issues")
async def workflow_issues(
    organization_id: str,
    status: Optional[str] = None,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Processing issues for an organisation (optional status filter)."""
    await ensure_processing_org_access(current_user, repos, organization_id)
    issues = await repos.issues.list_for_org(organization_id)
    if status is not None:
        issues = [i for i in issues if i.status == status]
    return {"issues": issues}




