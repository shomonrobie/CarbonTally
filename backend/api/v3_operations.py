"""V3 operations surface (V3 Phase 8).

CarbonTally-internal workforce layer: the operations dashboard, staff roster,
operator/reviewer/QC queues, item workflow (data entry → review → QC) and the
processing-company dashboards.

Architecture (all server-side authorized):

* Every endpoint passes ``require_staff()`` (active ``staff_profiles`` row) and
  re-authorizes the entity / batch / item / review record it touches.
* **CarbonTally internal staff** (``staff_profiles.entity_id IS NULL``) are the
  only identities that may run the manual-extraction pipeline, the ops-wide
  dashboard and staff/entity administration.
* **Processing-entity staff** (``entity_id`` populated) are scoped to their own
  entity's work: ``manual_review_queue.entity_id`` / ``issues.entity_id``. The
  schema has no entity column on manual-extraction batches/items, so entity staff
  structurally cannot access the pipeline (documented gap).
* Action permissions come from the real ``roles.permissions`` jsonb resolved via
  ``staff_profiles.role_id`` (``can_process`` for data entry, ``can_review`` for
  review/QC, ``can_manage_staff`` for staff/assignment administration,
  ``can_view_all`` for the ops dashboard).

Engines are REUSED (no duplication): the item workflow calls the same
``save_extracted_data`` / ``save_mapped_data`` / ``set_item_status`` repository
methods and the same ``validate_processing_item`` / ``CalculationEngine``
engines as the customer-facing Phase 3 surface — only the authorization layer is
different.
"""
from __future__ import annotations

import uuid
from datetime import date as _Date
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.contracts import calculation_out
from api.dependencies import (
    AuditContext,
    RepositoryBundle,
    get_audit_context,
    get_calculation_engine,
    get_repositories,
)
from api.operations_auth import (
    StaffContext,
    ensure_entity_batch_access,
    ensure_entity_review_scope,
    ensure_staff_permission,
    require_entity_scope,
    require_internal_staff,
    require_staff,
)
from domain.audit import AuditEntry
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

router = APIRouter(prefix="/api/v3/ops", tags=["V3 — Operations"])

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


class StaffCreate(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    email: str
    role_id: Optional[str] = None
    entity_id: Optional[str] = None
    max_concurrent_tasks: Optional[int] = None


class StaffUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    role_id: Optional[str] = None
    entity_id: Optional[str] = None
    max_concurrent_tasks: Optional[int] = None
    is_active: Optional[bool] = None


class BatchAssign(BaseModel):
    """Assignment payload (D22): exactly ONE of ``assigned_to`` (internal
    operator) or ``entity_id`` (Processing Entity) must be provided; ``None``
    for the other side clears it (reassignment). ``reason`` is recorded in the
    audit trail when the batch was previously assigned (reassignment)."""

    assigned_to: Optional[str] = None
    entity_id: Optional[str] = None
    reason: Optional[str] = None
    sla_deadline: Optional[str] = None


class ReviewAssign(BaseModel):
    assigned_to: str
    sla_deadline: Optional[str] = None


class ReviewComplete(BaseModel):
    manual_extraction_result: dict = {}
    review_time_seconds: int = 0


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


class QCReview(BaseModel):
    quality_score: int
    approved: bool = True
    qc_notes: Optional[str] = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stage_for_status(status: Optional[str]) -> Optional[str]:
    for stage, statuses in WORKFLOW_STAGE_STATUSES.items():
        if status in statuses:
            return stage
    return None


def _require_transition(item, target: str) -> None:
    if not can_transition_item_status(item.status, target):
        raise HTTPException(
            status_code=409,
            detail=f"cannot transition item {item.id!r} from {item.status!r} to {target!r}",
        )


def _findings_out(findings) -> list[dict]:
    return [
        {
            "code": f.code,
            "severity": f.severity,
            "message": f.message,
            "field": f.field,
        }
        for f in findings
    ]


async def _get_item_and_batch(
    context: StaffContext,
    repos: RepositoryBundle,
    item_id: str,
):
    """Load an item + its batch and enforce pipeline authorization.

    D22: a batch has exactly ONE processing party. CarbonTally internal staff
    may read/view any batch (including entity-assigned work) — the internal
    validation/QC gates must review entity-produced output. The operator
    *processing* surfaces (start/extract/map/calculate) additionally enforce
    ``_ensure_operator_batch`` (entity-assigned work is the entity's to process;
    reassignment is the explicit return path). Entity staff are never allowed
    on this internal surface — they use the entity extraction workspace.
    """
    if context.profile.entity_id is not None:
        raise HTTPException(
            status_code=403,
            detail="Processing-entity staff cannot use the internal extraction pipeline",
        )
    item = await repos.manual_extraction.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    batch = await repos.manual_extraction.get_batch(item.batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    return item, batch


def _ensure_operator_batch(
    context: StaffContext, batch, *, allow_entity_gate: bool = False
) -> None:
    """An operator may only work CarbonTally-internal batches assigned to them
    (or unassigned/open). Entity-assigned batches are the entity's work — unless
    ``allow_entity_gate`` (CarbonTally's validation/review gate over entity
    output)."""
    if batch.entity_id is not None:
        if allow_entity_gate:
            return
        raise HTTPException(
            status_code=403,
            detail="Batch is assigned to a processing entity; reassign to internal staff first",
        )
    if batch.assigned_to not in (None, context.profile.user_id):
        raise HTTPException(
            status_code=403,
            detail="Operator is not assigned to this batch",
        )


async def _open_validation_issues(
    repos: RepositoryBundle, context: StaffContext, item, batch, findings
) -> None:
    """Record blocking validation findings as first-class ``issues`` rows.

    The ``issues`` schema links work items through ``work_item_id`` →
    ``manual_review_queue`` and ``batch_id`` → ``upload_batches``; manual
    extraction batches link through the D22 ``manual_extraction_batch_id``.
    When the batch is Processing-Entity assigned (``entity_id`` populated) the
    issue is entity-scoped (mediated rework loop — never customer-visible);
    internal batches produce CarbonTally-internal issues. The blocking findings
    are surfaced to the reviewer via the validate response and the workspace
    ``validation.findings`` payload.
    """
    for finding in findings:
        if finding.severity == "error":
            await repos.issues.save(
                Issue(
                    id=str(uuid.uuid4()),
                    title=f"Validation: {finding.code}",
                    issue_type="defect",
                    severity="medium",
                    priority=1,
                    status="open",
                    description=finding.message,
                    organization_id=batch.organization_id,
                    entity_id=batch.entity_id,
                    work_item_id=None,
                    batch_id=None,
                    manual_extraction_batch_id=batch.id,
                    assignee_id=context.profile.user_id,
                    created_by=context.profile.user_id,
                )
            )


async def _record_batch_assignment_audit(
    repos: RepositoryBundle,
    audit: AuditContext,
    *,
    batch,
    actor: str,
    action: str,
    before: dict,
    reason: Optional[str] = None,
) -> None:
    """Record batch assignment/reassignment through the existing audit trail.

    ADR-V3-013 ("no new history table"): the V3 audit_trail is the established
    event carrier (issues, branding, …). The dormant queue-keyed
    ``processing_assignments``/``reassignment_history`` family is left
    untouched (retirement per ADR-V3-016).
    """
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id=audit.correlation_id if audit is not None else "",
        entity_type="manual_extraction_batch",
        entity_id=batch.id,
        action=action,
        actor=actor,
        occurred_at=datetime.now(timezone.utc),
        changed_fields={
            "entity_id": batch.entity_id,
            "assigned_to": batch.assigned_to,
            "assigned_by": batch.assigned_by,
        },
        reason=reason,
        ip_address=audit.ip_address if audit is not None else None,
        before=before,
        after={"entity_id": batch.entity_id, "assigned_to": batch.assigned_to},
    )
    await repos.audit.record(entry)



def _resolve_unit_for_factor(extracted_unit: str, factor) -> str:
    """Normalise a human-typed unit against the selected factor's unit.

    DEFRA units carry qualifiers (e.g. "kWh (Gross CV)"). When the operator
    types "kWh" and selects a "kWh (Gross CV)" factor, the quantity is in the
    factor's unit; the request uses the factor's canonical unit so the engine's
    exact-unit check passes and the multiplier applies 1:1. A genuine mismatch
    (e.g. "m3" vs "kWh") is left untouched and the engine rejects it with a
    clear UNIT_MISMATCH error.
    """
    unit = str(extracted_unit or "").strip()
    factor_unit = str(getattr(factor, "unit", "") or "").strip()
    if not unit or not factor_unit:
        return unit or factor_unit
    if unit == factor_unit:
        return unit
    if unit in factor_unit or factor_unit in unit:
        return factor_unit
    return unit


async def _run_line_calculation(
    repos: RepositoryBundle,
    calculation_engine: CalculationEngine,
    item,
    batch,
    payload,
) -> dict:
    """Calculate every mapped line of a multi-line item (D23).

    Each line produces its own persisted ``emissions_logs`` row (the engine's
    normal pipeline); the item's ``calculated_emissions_kg_co2e`` is the sum,
    and the per-line results are stored back into ``mapped_data.line_items``.
    """
    extracted = item.extracted_data or {}
    mapped = item.mapped_data or {}
    lines = extracted.get("line_items") or []
    mapped_lines = (
        mapped.get("line_items")
        if isinstance(mapped.get("line_items"), list)
        else []
    )
    total = Decimal("0")
    line_results: list[dict] = []
    for idx, line in enumerate(lines):
        if not isinstance(line, dict):
            raise HTTPException(
                status_code=422, detail=f"line {idx + 1} is not an object"
            )
        ml = (
            mapped_lines[idx]
            if idx < len(mapped_lines) and isinstance(mapped_lines[idx], dict)
            else {}
        )
        factor_id = ml.get("factor_id") or line.get("factor_id")
        if not factor_id:
            raise HTTPException(
                status_code=422,
                detail=f"line {idx + 1} has no emission factor mapped",
            )
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
        raw_qty = line.get("quantity")
        if raw_qty in (None, ""):
            raise HTTPException(
                status_code=422, detail=f"line {idx + 1} quantity is required"
            )
        try:
            quantity = Decimal(str(raw_qty))
        except (InvalidOperation, ValueError):
            raise HTTPException(
                status_code=422, detail=f"line {idx + 1} quantity is not numeric"
            )
        if quantity < 0:
            raise HTTPException(
                status_code=422, detail=f"line {idx + 1} quantity must be >= 0"
            )
        quantity_unit = _resolve_unit_for_factor(str(line.get("unit") or ""), factor or customer_factor)
        if not quantity_unit:
            raise HTTPException(
                status_code=422, detail=f"line {idx + 1} unit is required"
            )
        activity = str(line.get("activity") or "").strip()
        activity_type = str(ml.get("activity_type") or "").strip() or activity
        scope = payload.scope or (
            factor.scope if factor is not None else customer_factor.scope
        )
        reporting_year = (
            payload.date.year
            if payload.date is not None
            else (factor if factor is not None else customer_factor).reporting_year
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
            asset_id=payload.asset_id,
            facility_id=payload.facility_id,
            factor=factor,
            customer_factor=customer_factor,
        )
        result = await calculation_engine.calculate(request)
        co2e = Decimal(str(result.co2e_kg))
        total += co2e
        line_results.append(
            {
                "activity_type": activity_type,
                "factor_id": factor_id,
                "unit": quantity_unit,
                "quantity": float(quantity),
                "emissions_kg": float(co2e),
            }
        )
    updated_mapped = dict(mapped)
    updated_mapped["line_items"] = line_results
    updated = await repos.manual_extraction.save_calculation(
        item.id, float(total), mapped_data=updated_mapped
    )
    return {
        "result": {
            "co2e_kg": float(total),
            "multi_line": True,
            "lines": line_results,
        },
        "item": updated,
    }


# ---------------------------------------------------------------------------
# Identity + operations dashboard
# ---------------------------------------------------------------------------


@router.get("/me")
async def get_my_staff_context(
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The caller's staff profile + role + resolved permissions."""
    return await _staff_out(context, repos)


@router.get("/dashboard")
async def operations_dashboard(
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """CarbonTally operations dashboard (real data, ``can_view_all``)."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_view_all")
    staff_agg = await repos.staff.ops_dashboard()
    pipeline = await repos.manual_extraction.ops_dashboard_all()
    entities = await repos.entities.list_all()
    return {
        "scope": "internal",
        "organizations": staff_agg["organizations"],
        "processing_entities": staff_agg["entities"],
        "staff": staff_agg["staff"],
        "pipeline": pipeline,
        "review_queue": staff_agg["review_queue"],
        "issues": staff_agg["issues"],
        "entities": entities,
        "sla": await repos.queue_settings.get_settings(),
    }


# ---------------------------------------------------------------------------
# Staff roster administration (CarbonTally internal)
# ---------------------------------------------------------------------------


@router.get("/staff")
async def list_staff(
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """List the staff roster (``can_view_all`` or ``can_manage_staff``)."""
    require_internal_staff(context)
    if not context.permissions.get("can_view_all") and not context.permissions.get(
        "can_manage_staff"
    ):
        raise HTTPException(
            status_code=403, detail="staff lacks permission: can_view_all or can_manage_staff"
        )
    profiles = await repos.staff.list_profiles()
    out = []
    for profile in profiles:
        role = await repos.staff.get_role(profile.role_id) if profile.role_id else None
        out.append(
            {
                "id": profile.id,
                "user_id": profile.user_id,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "email": profile.email,
                "role_id": profile.role_id,
                "role_name": role.name if role else None,
                "is_active": profile.is_active,
                "entity_id": profile.entity_id,
                "is_internal_staff": profile.is_internal_staff,
                "max_concurrent_tasks": profile.max_concurrent_tasks,
            }
        )
    return {"staff": out, "total": len(out)}



# ---------------------------------------------------------------------------
# Processing entities (CarbonTally internal administration)
# ---------------------------------------------------------------------------


@router.get("/entities")
async def list_entities(
    status: Optional[str] = None,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """List processing entities (CarbonTally internal staff)."""
    require_internal_staff(context)
    if status is not None:
        return {"entities": await repos.entities.list_by_status(status)}
    return {"entities": await repos.entities.list_all()}


@router.get("/entities/{entity_id}/dashboard")
async def entity_dashboard(
    entity_id: str,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Processing-company dashboard (entity staff own scope; internal staff any).

    Real data only: review queue + issues are linked to the entity through
    ``manual_review_queue.entity_id`` / ``issues.entity_id`` (ADR-V3-001 Q5);
    the extraction block is the entity's assigned manual-extraction work
    (``manual_extraction_batches.entity_id``, D22).
    """
    require_entity_scope(context, entity_id)
    entity = await repos.entities.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="processing entity not found")
    # F1 (PE security audit): processing-entity staff must not retain read
    # access once their entity leaves ``active``. CarbonTally internal staff
    # keep read access for administration/oversight of suspended entities.
    if context.profile.entity_id is not None and entity.status != "active":
        raise HTTPException(
            status_code=403,
            detail=f"processing entity is {entity.status}; only active entities may access this surface",
        )
    agg = await repos.staff.entity_dashboard(entity_id)
    review_items = await repos.review_queue.list_items(status=None, limit=100)
    review_items = [r for r in review_items if r.entity_id == entity_id]
    return {
        "entity": agg["entity"],
        "staff_count": agg["staff_count"],
        "staff": await repos.staff.list_entity_staff(entity_id),
        "review_queue": {
            "total": agg["review_queue"]["total"],
            "by_status": agg["review_queue"]["by_status"],
            "sla_breached": agg["review_queue"]["sla_breached"],
            "items": review_items,
        },
        "issues": {
            "total": agg["issues"]["total"],
            "by_status": agg["issues"]["by_status"],
            "items": await repos.issues.list_for_entity(entity_id),
        },
        "extraction": await repos.manual_extraction.entity_workflow_dashboard(entity_id),
    }


# ---------------------------------------------------------------------------
# Entity extraction workspace (D22 — Processing Entity staff process ONLY the
# work assigned to their entity; entity staff never gain customer-org access)
# ---------------------------------------------------------------------------


async def _entity_workspace_guard(
    context: StaffContext,
    repos: RepositoryBundle,
    entity_id: str,
):
    """Gate every entity extraction endpoint: own-entity scope + ``can_process``
    + ACTIVE entity (an inactive entity's staff receive no work — the
    ``is_entity_member`` RLS gate is mirrored server-side)."""
    require_entity_scope(context, entity_id)
    ensure_staff_permission(context, "can_process")
    entity = await repos.entities.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="processing entity not found")
    if entity.status != "active":
        raise HTTPException(
            status_code=403,
            detail=f"processing entity is {entity.status}; only active entities process work",
        )
    return entity


async def _entity_checked_item(
    context: StaffContext,
    repos: RepositoryBundle,
    entity_id: str,
    item_id: str,
):
    """Load an item + its batch inside the entity workspace (batch must be
    assigned to ``entity_id`` — re-checked server-side on every touch)."""
    item = await repos.manual_extraction.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    batch = await ensure_entity_batch_access(context, repos, entity_id, item.batch_id)
    return item, batch


@router.get("/entities/{entity_id}/extraction/batches")
async def entity_extraction_batches(
    entity_id: str,
    status: Optional[str] = None,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The entity's assigned extraction batches (own-entity only)."""
    await _entity_workspace_guard(context, repos, entity_id)
    batches = await repos.manual_extraction.list_entity_batches(entity_id, status)
    return {"batches": batches, "total": len(batches)}


@router.get("/entities/{entity_id}/extraction/batches/{batch_id}")
async def entity_extraction_batch(
    entity_id: str,
    batch_id: str,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """One batch assigned to the entity (404/403 when not assigned)."""
    await _entity_workspace_guard(context, repos, entity_id)
    batch = await ensure_entity_batch_access(context, repos, entity_id, batch_id)
    return {"batch": batch}


@router.get("/entities/{entity_id}/extraction/batches/{batch_id}/items")
async def entity_extraction_batch_items(
    entity_id: str,
    batch_id: str,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The items of one entity-assigned batch (minimum work information).

    D32: items carry a SHORT-LIVED SIGNED ``file_url`` (view-only) — raw
    persisted storage paths are never returned to entity staff. The signed URL
    is issued by the service-role client after authorization and expires per the
    existing signed-URL convention.
    """
    await _entity_workspace_guard(context, repos, entity_id)
    batch = await ensure_entity_batch_access(context, repos, entity_id, batch_id)
    items = await repos.manual_extraction.list_items(batch_id)
    return {"batch": batch, "items": [signed_item(i) for i in items]}


@router.get("/entities/{entity_id}/extraction/items/{item_id}")
async def entity_extraction_item_workspace(
    entity_id: str,
    item_id: str,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """One item + its batch (the processing workspace payload).

    D19/D32: the item carries a SHORT-LIVED SIGNED ``file_url`` (view-only, PE
    no-download boundary), the deterministic OCR field SUGGESTIONS (for human
    confirmation — never auto-written) and the server validation findings. The
    same helpers/engines as the internal ops workspace are reused.
    """
    await _entity_workspace_guard(context, repos, entity_id)
    item, batch = await _entity_checked_item(context, repos, entity_id, item_id)
    ocr_suggestions = None
    if item.file_id:
        src = await repos.files.get(item.file_id)
        if src is not None:
            ocr = (src.metadata or {}).get("ocr") or {}
            ocr_suggestions = ocr.get("suggested_data") or None
    return {
        "item": signed_item(item),
        "batch": batch,
        "suggestions": ocr_suggestions,
        "validation": {"findings": _findings_out(validate_processing_item(item))},
    }


@router.get("/entities/{entity_id}/extraction/items/{item_id}/mapping-options")
async def entity_extraction_mapping_options(
    entity_id: str,
    item_id: str,
    activity: Optional[str] = None,
    unit: Optional[str] = None,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Mapping suggestions for an entity-assigned item (same sources as the
    internal surface — facilities/assets/suppliers + factor candidates)."""
    await _entity_workspace_guard(context, repos, entity_id)
    item, batch = await _entity_checked_item(context, repos, entity_id, item_id)
    extracted = item.extracted_data or {}
    search_activity = str(activity or extracted.get("activity") or "").strip()
    search_unit = str(unit or extracted.get("unit") or "").strip() or None
    factors = (
        await repos.factors.find_by_activity(search_activity, unit=search_unit, limit=20, unit_substring=True)
        if search_activity
        else []
    )
    return {
        "facilities": await repos.organizations.get_facilities(batch.organization_id),
        "assets": await repos.organizations.get_assets(batch.organization_id),
        "suppliers": await repos.suppliers.list_for_org(batch.organization_id),
        "factors": factors,
    }


@router.get("/entities/{entity_id}/extraction/next-item")
async def entity_extraction_next_item(
    entity_id: str,
    stage: str,
    exclude_item_id: Optional[str] = None,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The next item awaiting ``stage`` work in the entity's batches."""
    await _entity_workspace_guard(context, repos, entity_id)
    item = await repos.manual_extraction.next_entity_item(
        entity_id, stage, exclude_item_id
    )
    if item is None:
        raise HTTPException(
            status_code=404, detail=f"no item awaiting {stage!r} work"
        )
    return {"item": item}


class EntityItemStatus(BaseModel):
    """Transition an entity-assigned item to ``status`` (workflow vocabulary)."""

    status: str


class EntityClarify(BaseModel):
    """Mediated clarification request (entity staff -> CarbonTally; NEVER a
    direct entity<->customer channel)."""

    title: str
    description: Optional[str] = None


@router.post("/entities/{entity_id}/extraction/items/{item_id}/start")
async def entity_extraction_start_item(
    entity_id: str,
    item_id: str,
    payload: ItemStart,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Claim a stage for an entity-assigned item (extraction/mapping/calculation
    only — validation/review/QC are CarbonTally gates)."""
    await _entity_workspace_guard(context, repos, entity_id)
    item, batch = await _entity_checked_item(context, repos, entity_id, item_id)
    if payload.stage not in _STAGE_WORKING_STATUS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown stage {payload.stage!r}; expected one of {list(_STAGE_WORKING_STATUS)}",
        )
    if payload.stage in ("validation", "review"):
        raise HTTPException(
            status_code=403,
            detail="validation/review are CarbonTally-internal gates",
        )
    working = _STAGE_WORKING_STATUS[payload.stage]
    _require_transition(item, working)
    updated = await repos.manual_extraction.set_item_status(item_id, working)
    return {"item": updated, "stage": payload.stage, "working_status": working}


@router.post("/entities/{entity_id}/extraction/items/{item_id}/extract")
async def entity_extraction_save(
    entity_id: str,
    item_id: str,
    payload: ExtractPayload,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Save extraction output for an entity-assigned item."""
    await _entity_workspace_guard(context, repos, entity_id)
    item, batch = await _entity_checked_item(context, repos, entity_id, item_id)
    _require_transition(item, "extracted")
    updated = await repos.manual_extraction.save_extracted_data(
        item_id, payload.extracted_data, context.profile.user_id
    )
    return {"item": updated}


@router.post("/entities/{entity_id}/extraction/items/{item_id}/map")
async def entity_extraction_map(
    entity_id: str,
    item_id: str,
    payload: MapPayload,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Save mapping output for an entity-assigned item."""
    await _entity_workspace_guard(context, repos, entity_id)
    item, batch = await _entity_checked_item(context, repos, entity_id, item_id)
    _require_transition(item, "mapped")
    updated = await repos.manual_extraction.save_mapped_data(
        item_id,
        payload.mapped_data,
        payload.mapped_facility_id,
        payload.mapped_asset_id,
        payload.mapped_supplier_id,
        payload.emission_factor_used,
    )
    return {"item": updated}

@router.post("/entities/{entity_id}/extraction/items/{item_id}/calculate")
async def entity_extraction_calculate(
    entity_id: str,
    item_id: str,
    payload: CalculatePayload,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
    calculation_engine: CalculationEngine = Depends(get_calculation_engine),
):
    """Authoritative calculation for an entity-assigned item — identical to the
    internal pipeline (the engine computes and persists the result; the client
    never supplies it; quantity/unit/factor come from the item's extracted and
    mapped data)."""
    await _entity_workspace_guard(context, repos, entity_id)
    item, batch = await _entity_checked_item(context, repos, entity_id, item_id)
    _require_transition(item, "calculated")
    if batch.status in ("completed", "cancelled"):
        raise HTTPException(status_code=409, detail=f"batch is {batch.status}")

    extracted = item.extracted_data or {}
    mapped = item.mapped_data or {}

    # D23: multi-line documents calculate each mapped line and sum the result.
    if isinstance(extracted.get("line_items"), list) and extracted["line_items"]:
        return await _run_line_calculation(
            repos, calculation_engine, item, batch, payload
        )

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
            raise HTTPException(status_code=422, detail="mapped customer factor is not active")

    activity = (payload.activity or "").strip() or str(extracted.get("activity") or "")
    activity_type = (
        (payload.activity_type or "").strip()
        or mapped.get("activity_type")
        or activity
    )
    scope = payload.scope or (
        factor.scope if factor is not None else customer_factor.scope
    )
    reporting_year = (
        payload.date.year
        if payload.date is not None
        else (factor if factor is not None else customer_factor).reporting_year
    )

    quantity_unit = _resolve_unit_for_factor(quantity_unit, factor or customer_factor)
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
        asset_id=payload.asset_id,
        facility_id=payload.facility_id,
        factor=factor,
        customer_factor=customer_factor,
    )
    result = await calculation_engine.calculate(request)
    updated = await repos.manual_extraction.save_calculation(item_id, float(result.co2e_kg))
    return {"result": calculation_out(result), "item": updated}


@router.post("/entities/{entity_id}/extraction/items/{item_id}/status")
async def entity_extraction_set_status(
    entity_id: str,
    item_id: str,
    payload: EntityItemStatus,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Set an entity-assigned item's status (workflow transition validated;
    validation/review/QC statuses remain CarbonTally-internal gates)."""
    await _entity_workspace_guard(context, repos, entity_id)
    item, batch = await _entity_checked_item(context, repos, entity_id, item_id)
    if payload.status in (
        "validating", "validated", "customer_review",
        "approved", "rejected", "qc_approved", "qc_rejected",
    ):
        raise HTTPException(
            status_code=403,
            detail=f"{payload.status!r} is a CarbonTally/customer-gated status",
        )
    _require_transition(item, payload.status)
    updated = await repos.manual_extraction.set_item_status(item_id, payload.status)
    return {"item": updated}


@router.post("/entities/{entity_id}/extraction/items/{item_id}/clarify")
async def entity_extraction_clarify(
    entity_id: str,
    item_id: str,
    payload: EntityClarify,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
):
    """Open a mediated clarification issue on the assigned work.

    The entity-scoped issue is the Processing Entity -> CarbonTally leg of the
    mediated clarification boundary (§2): CarbonTally staff triage it
    (``/api/v3/issues/admin/open``), relay to the customer/consultant via the
    customer-facing issue surface, and the entity reads the outcome through its
    own entity issue list. The customer NEVER sees the entity-scoped issue and
    the entity NEVER receives customer communication identities.
    """
    await _entity_workspace_guard(context, repos, entity_id)
    item, batch = await _entity_checked_item(context, repos, entity_id, item_id)
    now = datetime.now(timezone.utc)
    issue = Issue(
        id=str(uuid.uuid4()),
        title=payload.title.strip(),
        issue_type="exception",
        severity="medium",
        priority=1,
        status="open",
        description=payload.description,
        organization_id=batch.organization_id,
        entity_id=entity_id,
        work_item_id=None,
        batch_id=None,
        manual_extraction_batch_id=batch.id,
        assignee_id=None,
        created_by=context.profile.user_id,
        created_at=now,
        updated_at=now,
        updated_by=context.profile.user_id,
    )
    stored = await repos.issues.save(issue)
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id=audit.correlation_id if audit is not None else "",
        entity_type="issue",
        entity_id=stored.id,
        action="issue:created",
        actor=context.profile.user_id,
        occurred_at=now,
        changed_fields={"status": "open", "entity_id": entity_id},
        ip_address=audit.ip_address if audit is not None else None,
    )
    await repos.audit.record(entry)
    return {"issue": stored}



# ---------------------------------------------------------------------------
# Queues: operator / review / QC
# ---------------------------------------------------------------------------


@router.get("/queues/operator")
async def operator_queue(
    status: Optional[str] = None,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The operator's assignment queue (``can_process``, internal staff).

    Assignment model (real columns): ``manual_extraction_batches.assigned_to``
    is the operator; ``NULL`` + open = the self-serve queue.
    """
    require_internal_staff(context)
    ensure_staff_permission(context, "can_process")
    batches = await repos.manual_extraction.list_operator_batches(
        context.profile.user_id, status
    )
    out = []
    for batch in batches:
        progress = await repos.manual_extraction.batch_progress(batch.id)
        org = await repos.organizations.get(batch.organization_id)
        out.append(
            {
                "batch": batch,
                "progress": progress,
                "organization": {"id": org.id, "name": org.name} if org else None,
            }
        )
    return {"queued": len(out), "batches": out}



# ---------------------------------------------------------------------------
# Split-screen workspace (shared by data entry / review / QC)
# ---------------------------------------------------------------------------


@router.get("/items/{item_id}/workspace")
async def item_workspace(
    item_id: str,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Split-screen workspace payload for one pipeline item.

    Reuses the exact Phase 3 workspace contract (``source`` + ``data`` +
    ``status`` + ``issues`` + ``workflow``). The role-specific workflow stage is
    derived from the item status — the same UI component renders the active
    stage and its controls.
    """
    item, batch = await _get_item_and_batch(context, repos, item_id)
    org = await repos.organizations.get(batch.organization_id)
    issues = await repos.issues.list_for_work_item(item.id)
    findings = validate_processing_item(item)
    # D32 (P0): documents are served only via short-lived signed URLs.
    signed = signed_item(item)
    # OCR text + deterministic field suggestions persisted at upload time
    # (organization_files.metadata) — surfaced so the human reviewer can
    # confirm/correct. ``ocr_suggestions`` are SUGGESTIONS only; the confirmed
    # values live in ``data.extracted_data`` (set via the /extract endpoint).
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
        "organization": {"id": org.id, "name": org.name} if org else None,
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
                "qc_notes": item.qc_notes,
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
        "validation": {"findings": _findings_out(findings)},
    }


@router.get("/items/{item_id}/mapping-options")
async def mapping_options(
    item_id: str,
    activity: Optional[str] = None,
    unit: Optional[str] = None,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Mapping suggestions for the split-screen data panel (same sources as the
    Phase 3 surface — facilities/assets/suppliers + factor candidates).

    ``activity``/``unit`` query params let the extraction form fetch candidates
    before the extraction is saved (fallback to the item's saved values)."""
    item, batch = await _get_item_and_batch(context, repos, item_id)
    extracted = item.extracted_data or {}
    search_activity = str(activity or extracted.get("activity") or "").strip()
    search_unit = str(unit or extracted.get("unit") or "").strip() or None
    factors = (
        await repos.factors.find_by_activity(search_activity, unit=search_unit, limit=20, unit_substring=True)
        if search_activity
        else []
    )
    return {
        "facilities": await repos.organizations.get_facilities(batch.organization_id),
        "assets": await repos.organizations.get_assets(batch.organization_id),
        "suppliers": await repos.suppliers.list_for_org(batch.organization_id),
        "factors": factors,
    }



# ---------------------------------------------------------------------------
# Item workflow: start / extract / map / validate / calculate / qc
# ---------------------------------------------------------------------------


@router.post("/items/{item_id}/start")
async def start_item(
    item_id: str,
    payload: ItemStart,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Claim a stage for an item (data entry: ``can_process``; validation:
    ``can_review``). Sets the in-flight status from the workflow vocabulary."""
    require_internal_staff(context)
    if payload.stage in ("validation", "review"):
        ensure_staff_permission(context, "can_review")
    else:
        ensure_staff_permission(context, "can_process")
    item, batch = await _get_item_and_batch(context, repos, item_id)
    if payload.stage not in _STAGE_WORKING_STATUS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown stage {payload.stage!r}; expected one of {list(_STAGE_WORKING_STATUS)}",
        )
    working = _STAGE_WORKING_STATUS[payload.stage]
    _require_transition(item, working)
    _ensure_operator_batch(
        context, batch, allow_entity_gate=(payload.stage in ("validation", "review"))
    )
    updated = await repos.manual_extraction.set_item_status(item_id, working)
    return {"item": updated, "stage": payload.stage, "working_status": working}


@router.post("/items/{item_id}/extract")
async def extract_item(
    item_id: str,
    payload: ExtractPayload,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Save extraction output (data entry, ``can_process`` + batch assignment)."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_process")
    item, batch = await _get_item_and_batch(context, repos, item_id)
    _require_transition(item, "extracted")
    _ensure_operator_batch(context, batch)
    updated = await repos.manual_extraction.save_extracted_data(
        item_id, payload.extracted_data, context.profile.user_id
    )
    return {"item": updated}


@router.post("/items/{item_id}/map")
async def map_item(
    item_id: str,
    payload: MapPayload,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Save mapping output (data entry, ``can_process`` + batch assignment)."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_process")
    item, batch = await _get_item_and_batch(context, repos, item_id)
    _require_transition(item, "mapped")
    _ensure_operator_batch(context, batch)
    updated = await repos.manual_extraction.save_mapped_data(
        item_id,
        payload.mapped_data,
        payload.mapped_facility_id,
        payload.mapped_asset_id,
        payload.mapped_supplier_id,
        payload.emission_factor_used,
    )
    return {"item": updated}


@router.post("/items/{item_id}/validate")
async def validate_item(
    item_id: str,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Run the authoritative validation engine (reviewer, ``can_review``).

    Blocking findings open ``issues`` rows and route the item back to
    ``mapping``; clean items advance to ``validated`` — identical behaviour to
    the Phase 3 surface (same engine, same statuses).
    """
    require_internal_staff(context)
    ensure_staff_permission(context, "can_review")
    item, batch = await _get_item_and_batch(context, repos, item_id)
    _require_transition(item, "validated")
    findings = validate_processing_item(item)
    blocking = has_blocking_findings(findings)
    if blocking:
        await _open_validation_issues(repos, context, item, batch, findings)
        await repos.manual_extraction.set_item_status(item.id, "mapping")
        return {
            "status": "mapping",
            "blocking": True,
            "findings": _findings_out(findings),
        }
    await repos.manual_extraction.set_item_status(item.id, "validated")
    return {
        "status": "validated",
        "blocking": False,
        "findings": _findings_out(findings),
    }


@router.post("/items/{item_id}/calculate")
async def calculate_item(
    item_id: str,
    payload: CalculatePayload,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
    engine: CalculationEngine = Depends(get_calculation_engine),
):
    """Run the authoritative V3 calculation (``can_process``).

    The client never supplies the result: the engine computes and persists the
    immutable snapshot + emissions row, then the item is stamped. Reuses
    ``get_calculation_engine`` and ``CalculationRequest`` unchanged.
    """
    require_internal_staff(context)
    ensure_staff_permission(context, "can_process")
    item, batch = await _get_item_and_batch(context, repos, item_id)
    _require_transition(item, "calculated")
    if batch.status in ("completed", "cancelled"):
        raise HTTPException(status_code=409, detail=f"batch is {batch.status}")

    extracted = item.extracted_data or {}
    mapped = item.mapped_data or {}
    # D23: multi-line documents calculate each mapped line and sum the result.
    if isinstance(extracted.get("line_items"), list) and extracted["line_items"]:
        return await _run_line_calculation(repos, engine, item, batch, payload)


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
            raise HTTPException(status_code=422, detail="mapped customer factor is not active")

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

    quantity_unit = _resolve_unit_for_factor(quantity_unit, factor or customer_factor)
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
        asset_id=payload.asset_id,
        facility_id=payload.facility_id,
        factor=factor,
        customer_factor=customer_factor,
    )
    result = await engine.calculate(request)
    updated = await repos.manual_extraction.save_calculation(item_id, float(result.co2e_kg))
    return {"result": calculation_out(result), "item": updated}


@router.post("/items/{item_id}/qc")
async def qc_item(
    item_id: str,
    payload: QCReview,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """QC decision over an extracted item (CarbonTally internal, ``can_review``).

    Reuses the real ``qc_review`` repository method (stamps qc_by/qc_at/
    qc_notes/quality_score and moves the item to qc_approved/qc_rejected).
    """
    require_internal_staff(context)
    ensure_staff_permission(context, "can_review")
    if not 0 <= payload.quality_score <= 100:
        raise HTTPException(status_code=422, detail="quality_score must be 0..100")
    item, _ = await _get_item_and_batch(context, repos, item_id)
    if item.status != "extracted":
        raise HTTPException(
            status_code=409, detail=f"only extracted items enter QC (status is {item.status!r})"
        )
    updated = await repos.manual_extraction.qc_review(
        item_id,
        payload.quality_score,
        payload.qc_notes,
        context.profile.user_id,
        payload.approved,
    )
    return {"item": updated}


# ---------------------------------------------------------------------------
# Assignment (CarbonTally internal administration)
# ---------------------------------------------------------------------------


@router.get("/batches/{batch_id}/items")
async def ops_batch_items(
    batch_id: str,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The items of one batch (internal operators/reviewers; entity staff use
    their own workspace surface).

    D32: items carry a SHORT-LIVED SIGNED ``file_url`` (view-only) — raw
    persisted storage paths are never returned.
    """
    require_internal_staff(context)
    batch = await repos.manual_extraction.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    items = await repos.manual_extraction.list_items(batch_id)
    return {"batch": batch, "items": [signed_item(i) for i in items]}


@router.post("/batches/{batch_id}/assign")
async def assign_batch(
    batch_id: str,
    payload: BatchAssign,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditContext = Depends(get_audit_context),
):
    """Assign (or reassign) a manual-extraction batch to ONE processing party.

    CarbonTally controls the assignment (``can_manage_staff`` + ``can_process``,
    internal staff only):

    * ``assigned_to`` = an internal operator (existing model; entity assignment
      on the batch is cleared).
    * ``entity_id``   = a Processing Entity (D22; any individual operator
      assignment on the batch is cleared).

    Exactly one of the two must be provided. Reassignment (the batch was
    previously assigned) is recorded in the existing V3 audit trail with the
    previous → new processing party and an optional ``reason`` (ADR-V3-013 —
    no new history table).
    """
    require_internal_staff(context)
    ensure_staff_permission(context, "can_manage_staff")
    ensure_staff_permission(context, "can_process")
    if (payload.assigned_to is None) == (payload.entity_id is None):
        raise HTTPException(
            status_code=422,
            detail="exactly one of assigned_to (internal operator) or entity_id (processing entity) is required",
        )

    batch = await repos.manual_extraction.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    if batch.status in ("completed", "cancelled"):
        raise HTTPException(status_code=409, detail=f"batch is {batch.status}")

    if payload.entity_id is not None:
        entity = await repos.entities.get(payload.entity_id)
        if entity is None:
            raise HTTPException(status_code=422, detail="entity_id is not a known processing entity")
        if entity.status != "active":
            raise HTTPException(
                status_code=422,
                detail=f"processing entity is {entity.status}; only active entities receive work",
            )
        updated = await repos.manual_extraction.update_batch(
            batch_id,
            status="in_progress",
            assigned_to=None,  # entity-level assignment carries no person
            assigned_by=context.profile.user_id,
            entity_id=payload.entity_id,
            updated_by=context.profile.user_id,
        )
    else:
        target = await repos.staff.get_by_user(payload.assigned_to)
        if target is None or not target.is_active:
            raise HTTPException(status_code=422, detail="assigned_to is not an active staff profile")
        if target.entity_id is not None:
            raise HTTPException(
                status_code=422,
                detail="processing-entity staff cannot be assigned manual-extraction batches",
            )
        updated = await repos.manual_extraction.update_batch(
            batch_id,
            status="in_progress",
            assigned_to=payload.assigned_to,
            assigned_by=context.profile.user_id,
            entity_id=None,  # internal assignment clears any entity assignment
            updated_by=context.profile.user_id,
        )

    previous_party = {
        "entity_id": batch.entity_id,
        "assigned_to": batch.assigned_to,
    }
    await _record_batch_assignment_audit(
        repos,
        audit,
        batch=updated,
        actor=context.profile.user_id,
        action="reassigned" if previous_party != {
            "entity_id": updated.entity_id,
            "assigned_to": updated.assigned_to,
        } and (previous_party["entity_id"] or previous_party["assigned_to"])
        else "assigned",
        before=previous_party,
        reason=payload.reason,
    )
    return {"batch": updated}


@router.post("/review/{review_id}/assign")
async def assign_review_item(
    review_id: str,
    payload: ReviewAssign,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Assign a review-queue item (``can_review`` + ``can_manage_staff``).

    Reuses the real ``ReviewQueueRepository.assign`` (assigned_to/assigned_by/
    status -> 'assigned').
    """
    ensure_staff_permission(context, "can_review")
    ensure_staff_permission(context, "can_manage_staff")
    item = await repos.review_queue.get(review_id)
    if item is None:
        raise HTTPException(status_code=404, detail="review item not found")
    if context.profile.entity_id is not None:
        if item.entity_id != context.profile.entity_id:
            raise HTTPException(
                status_code=403,
                detail="Review item does not belong to this processing entity",
            )
    updated = await repos.review_queue.assign(
        review_id, payload.assigned_to, context.profile.user_id, payload.sla_deadline
    )
    return {"item": updated}


@router.post("/review/{review_id}/complete")
async def complete_review_item(
    review_id: str,
    payload: ReviewComplete,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Complete a review-queue item (``can_review``, entity/assignee scoped).

    Reuses the real ``ReviewQueueRepository.complete`` (status -> 'completed',
    manual_extraction_result + review_time_seconds stamped).
    """
    ensure_staff_permission(context, "can_review")
    item = await repos.review_queue.get(review_id)
    if item is None:
        raise HTTPException(status_code=404, detail="review item not found")
    if context.profile.entity_id is not None:
        if item.entity_id != context.profile.entity_id:
            raise HTTPException(
                status_code=403,
                detail="Review item does not belong to this processing entity",
            )
    elif (
        not context.permissions.get("can_view_all")
        and item.assigned_to is not None
        and item.assigned_to != context.profile.user_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Review item is assigned to another reviewer",
        )
    updated = await repos.review_queue.complete(
        review_id, payload.manual_extraction_result, payload.review_time_seconds
    )
    return {"item": updated}


# ---------------------------------------------------------------------------
# SLA / priority (read-only surface of the existing queue settings)
# ---------------------------------------------------------------------------


@router.get("/sla/settings")
async def sla_settings(
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The real ``queue_settings`` row (SLA defaults, escalation, priority
    weights). Never fabricated — read straight from the repository."""
    return await repos.queue_settings.get_settings()


class SlaSettingsUpdate(BaseModel):
    """Bounded SLA write (D25): only the review SLA hours are exposed for
    update; capacity automation is deliberately not part of this surface."""

    sla_hours: Optional[int] = Field(None, ge=1, le=24 * 30)


@router.put("/sla/settings")
async def update_sla_settings(
    payload: SlaSettingsUpdate,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Update the review SLA default hours (``can_manage_staff``, internal
    staff). Reuses the existing ``queue_settings`` upsert — no new table."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_manage_staff")
    updated = await repos.queue_settings.update_settings(
        max_reviews_per_staff=None,
        sla_hours=payload.sla_hours,
        auto_assign_enabled=None,
        escalation_hours=None,
        priority_weights=None,
        updated_by=context.profile.user_id,
    )
    return updated
@router.get("/queues/review")
async def review_queue(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Internal review queue (``can_review``).

    * Entity staff: only their entity's ``manual_review_queue`` rows.
    * Internal staff: items assigned to them, or everything with ``can_view_all``.
    """
    ensure_staff_permission(context, "can_review")
    items = await repos.review_queue.list_items(
        status=status, assigned_to=assigned_to, limit=200
    )
    if context.profile.entity_id is not None:
        items = [r for r in items if r.entity_id == context.profile.entity_id]
    elif not context.permissions.get("can_view_all") and assigned_to is None:
        items = [r for r in items if r.assigned_to == context.profile.user_id]
    return {"queued": len(items), "items": items}


@router.get("/queues/qc")
async def qc_queue(
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """QC queue: extracted items awaiting QC review (``can_review``, internal)."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_review")
    return {"queued": len(await repos.manual_extraction.list_qc_pending()),
            "items": await repos.manual_extraction.list_qc_pending()}


@router.get("/next-item")
async def next_item(
    stage: str,
    exclude_item_id: Optional[str] = None,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Next item awaiting ``stage`` work in the operator's assigned batches
    (``can_process``, internal staff)."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_process")
    if stage not in WORKFLOW_STAGES and stage != "qc":
        raise HTTPException(
            status_code=422,
            detail=f"unknown stage {stage!r}; expected one of {WORKFLOW_STAGES}",
        )
    item = await repos.manual_extraction.next_operator_item(
        context.profile.user_id, stage, exclude_item_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="no item waiting in this stage")
    return item

@router.post("/staff", status_code=201)
async def create_staff(
    payload: StaffCreate,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Create a staff profile (``can_manage_staff``, CarbonTally internal)."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_manage_staff")
    existing = await repos.staff.get_by_user(payload.user_id)
    if existing is not None:
        raise HTTPException(status_code=409, detail="a staff profile already exists for this user")
    if payload.entity_id:
        entity = await repos.entities.get(payload.entity_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="processing entity not found")
    profile = await repos.staff.create_profile(
        user_id=payload.user_id,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=payload.email.strip(),
        role_id=payload.role_id,
        entity_id=payload.entity_id,
        max_concurrent_tasks=payload.max_concurrent_tasks,
        created_by=context.profile.user_id,
    )
    return {"profile": profile}


@router.put("/staff/{profile_id}")
async def update_staff(
    profile_id: str,
    payload: StaffUpdate,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Update a staff profile (``can_manage_staff``, CarbonTally internal)."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_manage_staff")
    existing = await repos.staff.get(profile_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="staff profile not found")
    if payload.entity_id:
        entity = await repos.entities.get(payload.entity_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="processing entity not found")
    updated = await repos.staff.update_profile(
        profile_id,
        first_name=payload.first_name.strip() if payload.first_name is not None else None,
        last_name=payload.last_name.strip() if payload.last_name is not None else None,
        email=payload.email.strip() if payload.email is not None else None,
        role_id=payload.role_id,
        entity_id=payload.entity_id,
        max_concurrent_tasks=payload.max_concurrent_tasks,
        is_active=payload.is_active,
        updated_by=context.profile.user_id,
    )
    return {"profile": updated}


@router.get("/staff-roles")
async def list_staff_roles(
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Staff-role reference catalog (the authoritative staff permission
    source ``staff_roles``) plus the customer-org ``roles`` reference."""
    roles = await repos.staff.list_roles()
    role_matrix = await repos.roles.list()
    return {"staff_roles": roles, "roles": role_matrix}


async def _staff_out(context: StaffContext, repos: RepositoryBundle) -> dict:
    """Staff profile + role name + resolved permissions (read-only payload)."""
    role = None
    if context.profile.role_id:
        role = await repos.staff.get_role(context.profile.role_id)
    return {
        "profile": {
            "id": context.profile.id,
            "user_id": context.profile.user_id,
            "first_name": context.profile.first_name,
            "last_name": context.profile.last_name,
            "email": context.profile.email,
            "role_id": context.profile.role_id,
            "role_name": role.name if role else None,
            "is_active": context.profile.is_active,
            "entity_id": context.profile.entity_id,
            "is_internal_staff": context.profile.is_internal_staff,
            "max_concurrent_tasks": context.profile.max_concurrent_tasks,
        },
        "permissions": context.permissions,
    }

