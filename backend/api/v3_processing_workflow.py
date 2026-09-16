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

from api.consultant_auth import (
    ensure_consultant_processing_authorized,
    ensure_consultant_review_authorized,
    ensure_consultant_submission_authorized,
)
from api.contracts import calculation_out
from api.dependencies import (
    RepositoryBundle,
    customer_factor_mapping_options,
    ensure_processing_org_access,
    get_calculation_engine,
    get_repositories,
)
from api.manual_processing_auth import ensure_manual_processing_allowed
from api.v3_operations import _run_line_calculation
from auth import AuthUser, require_auth, require_org_admin
from core.units import (
    mapping_no_factors_reason,
    relevant_customer_factors,
    resolve_unit_for_factor,
    spend_mapping_suggestion,
)
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

#: P6-2A — the consultant capability required to claim/act on each processing
#: stage (consultant path only; org-member and internal-staff paths unchanged).
#: Stages without an entry are NOT consultant processing actions.
#:
#: P6-2C (PO-P6-2C-D2 / contract CARBONTALLY-P6-2C-IC-20260910-001) — an active
#: consultant grant must NOT implicitly grant every workflow-stage capability.
#: The generic `review` stage claim hands the item to the Customer Review surface,
#: so it requires the existing `can_submit` capability; `source` is the alias of
#: `extraction` and requires the same existing `can_extract` capability. No new
#: capability, role or permission is introduced.
_STAGE_PERMISSION: dict[str, str] = {
    "source": "extract",
    "extraction": "extract",
    "mapping": "map",
    "validation": "validate",
    "calculation": "calculate",
    "review": "submit",
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
    *,
    permission: Optional[str] = None,
    enforce_manual_processing: bool = False,
) -> tuple:
    """Load an item + its batch and enforce organisation isolation.

    PO Decision 3 — consultants with an ACTIVE grant may operate their own
    customers' processing items (the grant is re-checked server-side).

    P6-2A — when a processing *action* is requested, the canonical Consultant
    processing authorization contract is enforced (active membership →
    active engagement → capability → resource scope → D38 conflict) whenever
    the caller acts in the CONSULTANT capacity. Organisation-member and
    internal-staff callers are unaffected (P6-2-D10).

    FIN-06 (P8 remediation IV-01) — ``enforce_manual_processing=True`` marks a
    MANUAL-PROCESSING ACTION (stage claim, extraction, mapping, validation,
    calculation). Those actions are additionally governed by the Manual
    Processing entitlement, so a direct API call cannot bypass the
    CarbonTally-Admin control. It is applied AFTER the identity/organisation/
    consultant checks so unauthorized callers still fail on authorization (and
    never learn governance state), and it is a no-op for CarbonTally internal
    staff (the platform operator) — see ``api.manual_processing_auth``.

    Read surfaces (workspace, mapping options) and the approval surfaces
    (customer review) leave the flag at its default and are deliberately NOT
    governed: reading work is not manual processing.
    """
    item = await repos.manual_extraction.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    batch = await repos.manual_extraction.get_batch(item.batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    await ensure_processing_org_access(current_user, repos, batch.organization_id)
    if permission is not None:
        await ensure_consultant_processing_authorized(
            current_user, repos, batch=batch, item=item, permission=permission
        )
    if enforce_manual_processing:
        # FIN-06 — manual-processing entitlement for the target organisation.
        await ensure_manual_processing_allowed(
            repos, current_user, batch.organization_id
        )
    return item, batch


async def _record_consultant_provenance(
    repos: RepositoryBundle,
    *,
    item,
    current_user: AuthUser,
) -> None:
    """P6-2D (D7) — persist durable, server-derived consultant provenance.

    Called at every consultant-capacity processing action immediately before the
    action's mutation, so the provenance exists exactly when the action occurs.

    * **Firm** — resolved server-side from the caller's authorised consultant
      membership/engagement relationship (``resolve_consultant_firm_id``). A
      request-supplied firm/organization value is never consulted, so no actor
      can cause another firm to be recorded.
    * **Mode** — the item's canonical processing-mode classification at this
      boundary, from the authoritative server-side predicate
      (``item_is_automatic``): ``automatic`` or ``manual``. It is deliberately
      NOT derived from the actor (automatic vs manual is actor-agnostic) and it
      is stored separately from ``processing_origin``.

    Non-consultant callers (organisation members, internal staff, PE staff) are
    a no-op — no consultant firm provenance is recorded for them. Recording is
    write-once in the repository, so later actions, later firms and later
    membership/engagement changes never rewrite recorded provenance.
    """
    from api.consultant_auth import resolve_consultant_firm_id
    from api.processing_mode import item_is_automatic

    firm_id = await resolve_consultant_firm_id(current_user, repos)
    if not firm_id:
        return
    mode = "automatic" if await item_is_automatic(repos, item) else "manual"
    await repos.manual_extraction.record_consultant_provenance(
        item.id, firm_id=firm_id, processing_mode=mode
    )


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
            # Manual-extraction batches link through the dedicated
            # ``manual_extraction_batch_id`` column. ``work_item_id`` FKs to
            # ``manual_review_queue(id)`` (a review-queue row must exist) and
            # ``batch_id`` FKs to ``upload_batches`` — neither exists for a
            # manual-extraction item, so both stay NULL (canonical pattern,
            # see api.v3_operations._open_validation_issues).
            work_item_id=None,
            batch_id=None,
            manual_extraction_batch_id=batch.id,
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
    # FIN-06 (P8 remediation IV-01) — starting a manual batch begins manual
    # processing work, so the entitlement is enforced here as well.
    await ensure_manual_processing_allowed(repos, current_user, batch.organization_id)
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
    item, batch = await _get_checked_item(
        current_user, repos, item_id,
        permission=_STAGE_PERMISSION.get(payload.stage),
        enforce_manual_processing=True,
    )
    if batch.status in ("completed", "cancelled"):
        raise HTTPException(
            status_code=409, detail=f"batch is {batch.status}"
        )
    working = _STAGE_WORKING_STATUS.get(payload.stage)
    if working is None:
        return item
    _require_transition(item, working)
    if payload.stage == "review":
        # P6-2B-4 — handing work to the Customer Review surface requires the
        # mandatory CarbonTally CT-QC pass for MANUALLY processed work
        # (automatic work is exempt). Runs AFTER the state-machine check (so
        # existing 409 semantics are preserved) and BEFORE any mutation.
        from api.processing_mode import ensure_manual_ct_qc_prerequisite

        await ensure_manual_ct_qc_prerequisite(
            repos, item, action="Customer Review"
        )
    await _record_consultant_provenance(repos, item=item, current_user=current_user)
    return await repos.manual_extraction.set_item_status(item_id, working)


@router.post("/items/{item_id}/extract")
async def extract_item(
    item_id: str,
    payload: ExtractPayload,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Data-entry: save extracted fields and advance the item to ``extracted``."""
    item, batch = await _get_checked_item(
        current_user, repos, item_id, permission="extract",
        enforce_manual_processing=True,
    )
    _require_transition(item, "extracted")
    await _record_consultant_provenance(repos, item=item, current_user=current_user)
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
    item, batch = await _get_checked_item(
        current_user, repos, item_id, permission="map",
        enforce_manual_processing=True,
    )
    _require_transition(item, "mapped")
    if payload.emission_factor_used is None and not (payload.mapped_data or {}).get(
        "factor_id"
    ):
        raise HTTPException(
            status_code=422,
            detail="an emission factor must be selected (emission_factor_used "
            "or mapped_data.factor_id)",
        )
    await _record_consultant_provenance(repos, item=item, current_user=current_user)
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
    item, batch = await _get_checked_item(
        current_user, repos, item_id, permission="validate",
        enforce_manual_processing=True,
    )
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
    await _record_consultant_provenance(repos, item=item, current_user=current_user)
    updated = await repos.manual_extraction.set_item_status(item_id, target)
    if not issues:
        # ISC-2 / CL-26 — a clean validation run proves previously blocking
        # findings (EXTRACTION_MISSING_FIELD …) are resolved; close them so the
        # item no longer carries stale open issues into approval.
        await repos.issues.resolve_open_for_item(item.id, current_user.user_id)
    return {
        "item": updated,
        "findings": [
            {
                "code": f.code,
                "severity": f.severity,
                "message": f.message,
                "field": getattr(f, "field", None),
            }
            for f in findings
        ],
        "blocking": bool(issues),
        "issues_created": issues,
    }


# ---------------------------------------------------------------------------
# Consultant Review (P6-2B-1) — readiness control before the future submit step
# ---------------------------------------------------------------------------


class ConsultantReviewPayload(BaseModel):
    """P6-2B-1 — Consultant Review decision on one processed item.

    ``passed=True`` records the item as ``consultant_reviewed`` (ready for the
    future P6-2B-2 submit action). ``passed=False`` routes the item back to
    ``mapping`` rework. Review NEVER grants CarbonTally QC or Customer
    Approval authority and NEVER requires ``can_submit``.
    """

    passed: bool = True
    rejection_reason: Optional[str] = None
    consultant_notes: Optional[str] = None


async def _audit_consultant_review(
    repos: RepositoryBundle,
    *,
    item_id: str,
    actor: str,
    status_from: str,
    status_to: str,
    passed: bool,
    notes: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    """Append-only human audit for Consultant Review (best-effort)."""
    from datetime import datetime, timezone
    from domain.audit import AuditEntry

    try:
        await repos.audit.record(
            AuditEntry(
                id="",
                correlation_id=item_id,
                entity_type="manual_extraction_item",
                entity_id=item_id,
                action="consultant.review:passed" if passed else "consultant.review:rework",
                actor=actor,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={
                    "status_from": status_from,
                    "status_to": status_to,
                    "consultant_notes": notes,
                    "rejection_reason": reason,
                },
                before={"status": status_from},
                after={"status": status_to},
            )
        )
    except Exception:  # noqa: BLE001 — audit never breaks the review
        pass


@router.post("/items/{item_id}/consultant-review")
async def consultant_review_item(
    item_id: str,
    payload: ConsultantReviewPayload,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """P6-2B-1 — Consultant Review action (item-level, consultant capacity).

    Authorization (complete BEFORE any mutation):

        identity → active consultant membership → active engagement →
        server-derived resource scope → D38 conflict → workflow-state
        eligibility (item must be ``calculated``) → review decision.

    Self-review is ratified (P6-2B-D1): the processing consultant may review
    their own item. Review does NOT require ``can_submit`` and does NOT grant
    QC or Customer Approval authority.
    """
    item = await repos.manual_extraction.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    batch = await repos.manual_extraction.get_batch(item.batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")

    await ensure_consultant_review_authorized(
        current_user, repos, batch=batch, item=item
    )
    # FIN-06 (P8 remediation IV-01) — consultant review is part of the manual
    # processing workflow, so it is governed like the other manual actions.
    await ensure_manual_processing_allowed(repos, current_user, batch.organization_id)

    # Workflow-state eligibility: Consultant Review is entered ONLY from
    # `calculated` (processing complete). A reviewed/advanced item cannot be
    # re-reviewed here; any other state is rejected server-side.
    if item.status != "calculated":
        raise HTTPException(
            status_code=409,
            detail=(
                "Consultant Review requires item status 'calculated' "
                f"(current status: {item.status!r})"
            ),
        )

    target = "consultant_reviewed" if payload.passed else "mapping"
    _require_transition(item, target)
    if not payload.passed and not (payload.rejection_reason or "").strip():
        raise HTTPException(
            status_code=422,
            detail="rejection_reason is required when Consultant Review fails",
        )
    await _record_consultant_provenance(repos, item=item, current_user=current_user)
    updated = await repos.manual_extraction.set_item_status(item_id, target)
    await _audit_consultant_review(
        repos,
        item_id=item.id,
        actor=current_user.user_id,
        status_from=item.status,
        status_to=target,
        passed=payload.passed,
        notes=payload.consultant_notes,
        reason=payload.rejection_reason,
    )
    if not payload.passed:
        # P6-2E (D11) — lifecycle event 5 "rework" (consultant-review rejection
        # routes the item back to `mapping`). Emitted only after the rejection
        # transition + audit succeeded.
        from services.consultant_lifecycle import (
            REWORK_SOURCE_CONSULTANT_REVIEW_REJECTED,
            notify_rework,
        )

        await notify_rework(
            repos,
            item=item,
            source=REWORK_SOURCE_CONSULTANT_REVIEW_REJECTED,
            batch=batch,
        )
    return {"item": updated}


# ---------------------------------------------------------------------------
# Consultant Submission (P6-2B-2) — Consultant Review → CarbonTally QC intake
# ---------------------------------------------------------------------------

#: P6-2B-2 — the existing CarbonTally QC intake state reached by Consultant
#: submission. ``reviewed`` is the canonical internal hand-off state that the
#: CT-QC pending queue (``list_ct_qc_pending``) lists and the CT-QC decision
#: endpoint accepts — the work therefore becomes eligible for the EXISTING
#: internal CarbonTally QC authority with no QC change. Consultant firm/origin
#: distinction is deferred to the D7 provenance workstream (P6-2D) and is NOT
#: represented here.
_CT_QC_INTAKE_STATUS = "reviewed"


async def _audit_consultant_submit(
    repos: RepositoryBundle,
    *,
    item_id: str,
    actor: str,
    status_from: str,
    status_to: str,
) -> None:
    """Append-only human audit for Consultant submission (best-effort)."""
    from datetime import datetime, timezone
    from domain.audit import AuditEntry

    try:
        await repos.audit.record(
            AuditEntry(
                id="",
                correlation_id=item_id,
                entity_type="manual_extraction_item",
                entity_id=item_id,
                action="consultant.submit:submitted",
                actor=actor,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={
                    "status_from": status_from,
                    "status_to": status_to,
                },
                before={"status": status_from},
                after={"status": status_to},
            )
        )
    except Exception:  # noqa: BLE001 — audit never breaks the submission
        pass


@router.post("/items/{item_id}/consultant-submit")
async def consultant_submit_item(
    item_id: str,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """P6-2B-2 — Consultant submission of reviewed work to CarbonTally QC.

    Authorization (complete BEFORE any mutation or billing side effect):

        identity → active consultant membership → active engagement →
        ``can_submit`` capability (no other capability substitutes) →
        server-derived resource scope → D38 conflict → workflow-state
        eligibility (item must be ``consultant_reviewed``) → non-charging
        entitlement availability (D6, fail closed) → submission mutation.

    The item enters the existing CarbonTally QC intake state (``reviewed``)
    and becomes eligible for the existing internal CarbonTally QC authority.
    NO charge occurs (Customer Approval remains the canonical charge point).
    Submission NEVER grants CarbonTally QC or Customer Approval authority.
    The organization is derived server-side from the item's batch — the
    request body is never consulted.
    """
    item = await repos.manual_extraction.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    batch = await repos.manual_extraction.get_batch(item.batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")

    await ensure_consultant_submission_authorized(
        current_user, repos, batch=batch, item=item
    )
    # FIN-06 (P8 remediation IV-01) — consultant submission is a manual
    # processing action and is governed by the same entitlement.
    await ensure_manual_processing_allowed(repos, current_user, batch.organization_id)

    # Workflow-state eligibility: submission is ONLY from Consultant Review
    # completion (`consultant_reviewed`). No other state may be submitted, and
    # a consultant cannot skip Consultant Review (an item must first have been
    # reviewed).
    if item.status != "consultant_reviewed":
        raise HTTPException(
            status_code=409,
            detail=(
                "Consultant submission requires item status 'consultant_reviewed' "
                f"(current status: {item.status!r})"
            ),
        )

    target = _CT_QC_INTAKE_STATUS
    _require_transition(item, target)

    # D6 — non-charging entitlement availability (server-authoritative, read
    # only). Fails closed BEFORE any mutation when the client organisation has
    # no active processing entitlement. No order/payment/credit/subscription
    # mutation and no charge occurs here (charge point remains Customer
    # Approval, D37).
    try:
        from services.billing import BillingError, BillingService

        await BillingService(repos).ensure_processing_entitlement(
            batch.organization_id
        )
    except BillingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    await _record_consultant_provenance(repos, item=item, current_user=current_user)
    updated = await repos.manual_extraction.set_item_status(item_id, target)
    await _audit_consultant_submit(
        repos,
        item_id=item.id,
        actor=current_user.user_id,
        status_from=item.status,
        status_to=target,
    )
    # P6-2E (D11) — lifecycle event 2 "submitted_to_qc". Emitted only after the
    # submission + audit succeeded (denial, state conflict and the non-charging
    # entitlement preflight all raise before this point).
    from services.consultant_lifecycle import notify_submitted_to_qc

    await notify_submitted_to_qc(repos, item=item, batch=batch)
    return {"item": updated}


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
    item, batch = await _get_checked_item(
        current_user, repos, item_id, permission="calculate",
        enforce_manual_processing=True,
    )
    _require_transition(item, "calculated")
    if batch.status in ("completed", "cancelled"):
        raise HTTPException(status_code=409, detail=f"batch is {batch.status}")

    extracted = item.extracted_data or {}
    mapped = item.mapped_data or {}

    await _record_consultant_provenance(repos, item=item, current_user=current_user)

    # D23 — multi-line documents calculate each mapped line and sum the result
    # (shared with the internal surface so both surfaces behave identically).
    if isinstance(extracted.get("line_items"), list) and extracted["line_items"]:
        result = await _run_line_calculation(repos, engine, item, batch, payload)
        return {"item": result["item"], "calculation": result["result"]}

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
    # V1.2 / CT-QC-002/005 — Customer Approval must not bypass required
    # CarbonTally QC. PE-originated work may only be submitted for customer
    # review AFTER the late CarbonTally QC gate (ct_qc_approved). Internal
    # items follow the canonical internal Review → CarbonTally QC path for new
    # work while legacy calculated items keep their existing submission path.
    origin = await repos.manual_extraction.get_item_origin(item_id)
    if origin and origin.get("processing_origin") == "PROCESSING_ENTITY":
        if item.status not in ("ct_qc_approved", "customer_review", "approved"):
            raise HTTPException(
                status_code=403,
                detail=(
                    "PE-originated work must pass CarbonTally QC "
                    "(ct_qc_approved) before customer approval"
                ),
            )
    target = "approved" if payload.approved else "rejected"
    _require_transition(item, target)
    # P6-2C (PO-P6-2C-D1 / contract CARBONTALLY-P6-2C-IC-20260910-001) — the
    # `calculated → approved` transition exists ONLY for the automatic-processing
    # workflow and is therefore explicitly automatic-processing-only. It is never
    # a generic approval capability: a manually processed item has no approval
    # path from `calculated` and must pass CarbonTally QC (`ct_qc_approved`)
    # first. Runs AFTER the state-machine check (existing 409 semantics
    # preserved) and BEFORE the D37 charge, so a denied request is zero
    # workflow/billing mutation.
    if item.status == "calculated":
        from api.processing_mode import item_is_automatic

        if not await item_is_automatic(repos, item):
            raise HTTPException(
                status_code=403,
                detail=(
                    "the calculated -> approved transition is "
                    "automatic-processing only; manually processed work must "
                    "pass CarbonTally QC (ct_qc_approved) before customer "
                    "approval"
                ),
            )
    # P6-2B-4 — mandatory CarbonTally CT-QC prerequisite for MANUALLY processed
    # work (automatic work is exempt via the P1 containment predicate). Runs
    # AFTER the state-machine check (preserving existing 409 semantics) and
    # BEFORE the D37 charge, so a denied approval is zero workflow/billing
    # mutation.
    from api.processing_mode import ensure_manual_ct_qc_prerequisite

    await ensure_manual_ct_qc_prerequisite(repos, item, action="Customer Approval")
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
    # P6-2E (D11) — lifecycle event 4 "customer_decision". Emitted only after
    # the decision + billing/issue side-effects succeeded; recipients are the
    # engaged firm's members (the client is the actor here).
    from services.consultant_lifecycle import notify_customer_decision

    await notify_customer_decision(
        repos, item=item, approved=bool(payload.approved), batch=batch
    )
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
    # P2 EF-E (PO D-A(b), D-B T2): strict qualifier-aware selection — without it a
    # qualified factor is invisible and `has_factors` below can report a false
    # dead-end for a unit that does have eligible factors.
    factors = (
        await repos.factors.find_by_activity(
            activity, unit=unit, limit=20, unit_qualifier_tolerant=True
        )
        if activity
        else []
    )
    # CL-44 / D-cf-5 — approved customer factors join the picker and take
    # precedence over system factors for the same activity/unit.
    customer_factors = await customer_factor_mapping_options(
        repos, batch.organization_id
    )
    # The guidance below reflects whether ANY factor (system or customer)
    # covers THIS activity/unit — an unrelated approved customer factor (e.g.
    # a Diesel factor) must not mask a spend-activity dead-end (CL-47).
    relevant = relevant_customer_factors(customer_factors, activity, unit)
    has_factors = bool(factors) or bool(relevant)
    return {
        "facilities": await repos.organizations.get_facilities(batch.organization_id),
        "assets": await repos.organizations.get_assets(batch.organization_id),
        "suppliers": await repos.suppliers.list_for_org(batch.organization_id),
        "factors": factors,
        "customer_factors": customer_factors,
        # ISC-9 / CL-32 — honest spend-based mapping state. The DEFRA/SEAI
        # factor sets are physical-unit based; a currency activity (GBP/EUR/…)
        # has no applicable factor unless a customer factor is added. The
        # mapper surfaces an explicit, actionable reason instead of an empty
        # dead-end (never invents a factor, never treats GBP as a physical unit).
        "no_factors_reason": mapping_no_factors_reason(activity, unit, has_factors),
        # CL-47 — machine-readable guidance so the UI can offer the supported
        # spend workflow (create an approved customer factor, then map).
        "spend_suggestion": spend_mapping_suggestion(activity, unit, has_factors),
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




