"""V3 automatic-processing surface (Phase A / CL-56).

Org-scoped API over the durable document-processing pipeline. The worker runs
the stages server-side; this surface provides observability (job list/detail),
the manual gates (confirm a blocked job after a human fixes the item in the
existing workbench; retry a failed job) and the distinct customer/owner review
approval (D5). The upload surface (``POST /api/v3/uploads``) enqueues the
durable job automatically.

Authorization mirrors the existing processing workflow:
* list/detail/confirm/retry - org member, internal staff, or a consultant with
  an ACTIVE client grant (``ensure_processing_org_access``); PE staff denied.
* customer review/approval - organisation owner/admin only (D5), or
  CarbonTally internal staff (operational).

Machine provenance (WS4 Gate 5, task T5): job payloads expose a typed
``automation`` block (``provider`` / ``model`` / ``model_version``) that reflects
the write-once automated-execution attribution persisted on the durable job
record. It is machine-execution evidence only — distinct from human actor
provenance, never a user/PE/role identity, and never an authorization signal.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    RepositoryBundle,
    ensure_processing_org_access,
    get_repositories,
)
from auth import AuthUser, require_auth, require_org_admin
from core.logging import get_logger
from domain.audit import AuditEntry
from domain.automatic_processing import STAGE_LABELS, AutomaticProcessingJob
from pydantic import BaseModel

router = APIRouter(prefix="/api/v3/processing", tags=["V3 - Automatic Processing"])

logger = get_logger(__name__)


def _job_payload(job: Optional[AutomaticProcessingJob]) -> dict:
    if job is None:
        raise HTTPException(status_code=404, detail="processing job not found")
    return {
        "id": job.id,
        "organization_id": job.organization_id,
        "file_name": job.file_name,
        "file_type": job.file_type,
        "processing_type": job.processing_type,
        "status": job.status,
        "stage": job.stage,
        "stage_label": STAGE_LABELS.get(job.stage or "", job.stage or ""),
        "attempt_count": job.attempt_count,
        "max_attempts": job.max_attempts,
        "last_error": job.last_error,
        "manual_review_reason": job.manual_review_reason,
        "completeness": job.completeness,
        "extracted_data": job.extracted_data,
        "mapped_data": job.mapped_data,
        "validation_result": job.validation_result,
        "calculation_snapshot_id": job.calculation_snapshot_id,
        "source_item_id": job.source_item_id,
        "pipeline_version": job.pipeline_version,
        "reprocess_count": job.reprocess_count,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "completed_at": job.completed_at,
        "ingested_at": job.ingested_at,
        "extracted_at": job.extracted_at,
        "mapped_at": job.mapped_at,
        "validated_at": job.validated_at,
        "calculated_at": job.calculated_at,
        "review_ready_at": job.review_ready_at,
        "notified_at": job.notified_at,
        # Phase 2 — AI-extraction provenance (candidate step). Populated from
        # the job metadata by the worker when an AI engine ran; ``None`` when
        # extraction was purely deterministic. Contains method/model/confidence
        # and timings — never prompt text, raw document content or credentials.
        "ai_extraction": (job.metadata or {}).get("ai_extraction"),
        # WS4 Gate 5 (task T5) — typed durable machine-attribution block on the
        # canonical automated-execution record (document_processing_queue). Each
        # value is NULL for deterministic-only/legacy results; a non-NULL block
        # means an AI pass CONTRIBUTED to the persisted extraction (write-once,
        # never overwritten by human processing). Machine evidence only — never a
        # human/PE/role identity.
        "automation": {
            "provider": job.automation_provider,
            "model": job.automation_model,
            "model_version": job.automation_model_version,
        },
        # WS4 Gate 6 (workstream W1 / gap G6-A) — original automated extraction
        # output preserved write-once at first machine extraction. Always
        # distinct from the current/human-editable ``extracted_data`` above;
        # NULL when no automated extraction output was ever durably produced.
        "automation_extracted_data": job.automation_extracted_data,
        # WS4 Gate 6 (workstream W3 / gap G6-C) — authoritative human-after-
        # automation attribution, read-only and never client-supplied. Kept in
        # a separate structure so a human action can never be read as the
        # original machine output (``automation`` / ``automation_extracted_data``).
        # ``updated_by`` = authenticated user of the last confirm/retry
        # re-enqueue; the ``customer_reviewed_*`` fields = the owner/admin
        # review decision. ``automatic_pipeline`` is a machine actor and never
        # appears here.
        "human": {
            "created_by": job.created_by,
            "updated_by": job.updated_by,
            "customer_reviewed_by": job.customer_reviewed_by,
            "customer_reviewed_at": job.customer_reviewed_at,
            "customer_approved": job.customer_approved,
            "customer_rejection_reason": job.customer_rejection_reason,
            "customer_notes": job.customer_notes,
        },
    }


async def _checked_job(
    current_user: AuthUser,
    repos: RepositoryBundle,
    job_id: str,
) -> AutomaticProcessingJob:
    """Load a job and enforce organisation isolation (consultant grants incl.)."""
    job = await repos.processing.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="processing job not found")
    await ensure_processing_org_access(current_user, repos, job.organization_id)
    return job


async def _authorize_consultant_job_action(
    current_user: AuthUser,
    repos: RepositoryBundle,
    job: AutomaticProcessingJob,
    *,
    permission: str,
) -> None:
    """P6-2A-R1 — apply the CANONICAL P6-2A Consultant authorization contract to
    a job action (confirm / retry) BEFORE any mutation or side effect.

    Uses ``ensure_consultant_processing_authorized`` (no parallel
    implementation). Internal staff and organisation members pass through
    unchanged (actor separation / P6-2-D10); the resolver enforces active
    membership → active engagement → ``permission`` (``confirm_automation``) →
    resource scope → D38 conflict whenever the caller acts in the CONSULTANT
    capacity. The source item + its batch (if present) are resolved
    server-side so the D38 rule evaluates the same canonical assignment
    surface as the item workflow.
    """
    from api.consultant_auth import ensure_consultant_processing_authorized

    item = None
    batch = None
    source_item_id = getattr(job, "source_item_id", None)
    if source_item_id:
        try:
            item = await repos.manual_extraction.get_item(source_item_id)
        except Exception:  # noqa: BLE001 — item lookup is best-effort
            item = None
        if item is not None:
            batch = await repos.manual_extraction.get_batch(item.batch_id)
    await ensure_consultant_processing_authorized(
        current_user,
        repos,
        batch=batch,
        item=item,
        organization_id=str(getattr(job, "organization_id", "") or ""),
        permission=permission,
    )


async def _record_human_gate_audit(
    repos: RepositoryBundle,
    *,
    job_id: str,
    action: str,
    actor: str,
    stage_from: Optional[str],
    stage_to: Optional[str],
    status_from: Optional[str],
    status_to: Optional[str],
    extra: Optional[dict] = None,
) -> None:
    """Best-effort append-only audit of a HUMAN gate on an automatic job.

    WS4 Gate 6 (workstream W2 / gap G6-B): confirm / retry / review (approve /
    reject) are human-after-automation actions. The entry is recorded on the
    same entity/correlation as the machine ``automatic_processing:extracted``
    event (``document_processing_queue`` + job id) but with the AUTHENTICATED
    human actor id, so an auditor can distinguish and order the machine action
    and the later human action. Actor identity always comes from the request
    context (``current_user.user_id``) — never from an untrusted client field.
    Audit failure never breaks the endpoint.
    """
    changed: dict[str, object] = {
        "status_from": status_from,
        "status_to": status_to,
        "stage_from": stage_from,
        "stage_to": stage_to,
    }
    if extra:
        changed.update(extra)
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id=job_id,
        entity_type="document_processing_queue",
        entity_id=job_id,
        action=action,
        actor=actor,
        occurred_at=datetime.now(timezone.utc),
        changed_fields=changed,
        ip_address=None,
    )
    try:
        await repos.audit.record(entry)
    except Exception:  # noqa: BLE001 — audit must never break the human gate
        logger.exception(
            "human job-gate audit (%s) failed for job %s", action, job_id
        )


# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------


@router.get("/jobs")
async def list_jobs(
    organization_id: str,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """List durable processing jobs for an organisation (filters optional)."""
    await ensure_processing_org_access(current_user, repos, organization_id)
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))
    jobs = await repos.processing.list_for_org(
        organization_id,
        status=status,
        stage=stage,
        limit=limit,
        offset=offset,
    )
    return {
        "organization_id": organization_id,
        "total": len(jobs),
        "jobs": [_job_payload(j) for j in jobs],
        "by_stage": await repos.processing.count_by_stage(organization_id),
    }


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Return one durable job with its persisted pipeline outputs."""
    job = await _checked_job(current_user, repos, job_id)
    return _job_payload(job)


# ---------------------------------------------------------------------------
# Manual gates
# ---------------------------------------------------------------------------


class ConfirmPayload(BaseModel):
    """Resume a blocked job after human rework.

    ``stage`` selects the re-entry point: ``enqueued`` restarts the whole
    pipeline (idempotent - persisted outputs are the resume markers), or
    ``extracting``/``mapping``/``validating`` re-runs the corrected stage.

    ``extracted_data`` / ``mapped_data`` carry any human corrections made in
    the item workbench; when supplied they are persisted to the job (and the
    item) before re-enqueue so the resumed pipeline validates the corrections.
    """

    stage: str = "enqueued"
    reset_attempts: bool = True
    extracted_data: Optional[dict] = None
    mapped_data: Optional[dict] = None


@router.post("/jobs/{job_id}/confirm")
async def confirm_job(
    job_id: str,
    payload: ConfirmPayload,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Human confirmation gate: re-enqueue a blocked job after rework.

    The human first corrects the extraction/mapping in the existing item
    workbench (or supplies the corrections in the payload), then confirms here
    - the job re-enters the pipeline at the chosen stage and the worker resumes
    it (server-authorized, org-scoped).
    """
    job = await _checked_job(current_user, repos, job_id)
    # P6-2A-R1 (B1) — Consultant authorization MUST precede any mutation: active
    # membership → active engagement → can_confirm_automation → resource scope →
    # D38 conflict. Internal staff / org members are unaffected by this check.
    await _authorize_consultant_job_action(
        current_user, repos, job, permission="confirm_automation"
    )
    if job.stage not in ("blocked", "failed"):
        raise HTTPException(
            status_code=409,
            detail=(
                f"job is {job.stage!r}; only blocked/failed jobs can be "
                "confirmed and re-enqueued"
            ),
        )
    if payload.stage not in ("enqueued", "extracting", "mapping", "validating"):
        raise HTTPException(
            status_code=422,
            detail="stage must be one of enqueued/extracting/mapping/validating",
        )
    # Apply any human corrections to the item (evidence-chain root) first.
    _corrected_item_before = None
    if payload.extracted_data is not None and job.source_item_id:
        try:
            _corrected_item_before = await repos.manual_extraction.get_item(
                job.source_item_id
            )
        except Exception:  # noqa: BLE001 — audit context is best-effort
            _corrected_item_before = None
    if payload.extracted_data is not None and job.source_item_id:
        try:
            await repos.manual_extraction.save_extracted_data(
                job.source_item_id, payload.extracted_data, current_user.user_id
            )
        except Exception:  # noqa: BLE001 — item sync is best-effort
            pass
    if payload.mapped_data is not None and job.source_item_id:
        try:
            await repos.manual_extraction.save_mapped_data(
                job.source_item_id,
                payload.mapped_data,
                None,
                None,
                None,
                payload.mapped_data.get("factor_id"),
            )
        except Exception:  # noqa: BLE001
            pass
    # WS4 Gate 6 (workstream W4 / gap G6-D) — a human-supplied extraction
    # correction on the work item is attributable at the item level (distinct
    # from the machine extraction) and correlated to this job.
    if _corrected_item_before is not None and payload.extracted_data is not None:
        from api.audit_helpers import (
            changed_extraction_keys,
            record_item_extraction_edit,
        )

        await record_item_extraction_edit(
            repos,
            item_id=job.source_item_id,
            action="automatic_processing:item_extraction_corrected",
            actor=current_user.user_id,
            correlation_id=job_id,
            job_id=job_id,
            status_from=_corrected_item_before.status,
            status_to="extracted",
            previous_extracted_by=_corrected_item_before.extracted_by,
            changed_keys=changed_extraction_keys(
                _corrected_item_before.extracted_data, payload.extracted_data
            ),
        )
    updated = await repos.processing.reenqueue(
        job_id,
        stage=payload.stage,
        reset_attempts=payload.reset_attempts,
        updated_by=current_user.user_id,
    )
    # Sync the (possibly corrected) item data into the job so the resumed run
    # validates the corrected values.
    if job.source_item_id:
        item = await repos.manual_extraction.get_item(job.source_item_id)
        if item is not None and (item.extracted_data or item.mapped_data):
            updated = await repos.processing.sync_item_data(
                job_id,
                extracted_data=payload.extracted_data or item.extracted_data,
                mapped_data=payload.mapped_data or item.mapped_data,
            )
    # WS4 Gate 6 (workstream W2 / gap G6-B) — human confirm gate after
    # automation: append-only audit event attributed to the authenticated
    # human, correlated to the same job as the machine extraction event.
    await _record_human_gate_audit(
        repos,
        job_id=job_id,
        action="automatic_processing:confirmed",
        actor=current_user.user_id,
        stage_from=job.stage,
        stage_to=updated.stage if updated is not None else payload.stage,
        status_from=job.status,
        status_to=updated.status if updated is not None else "pending",
        extra={
            "gate": "confirm",
            "re_entry_stage": payload.stage,
            "source_item_id": job.source_item_id,
        },
    )
    return _job_payload(updated)


@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Retry a failed job (dead-letter recovery)."""
    job = await _checked_job(current_user, repos, job_id)
    # P6-2A-R1 (B1) — retry is a Consultant automation-control action: same
    # canonical authorization contract (can_confirm_automation) before any
    # re-enqueue side effect. Internal staff / org members are unaffected.
    await _authorize_consultant_job_action(
        current_user, repos, job, permission="confirm_automation"
    )
    if job.stage not in ("failed", "blocked"):
        raise HTTPException(
            status_code=409,
            detail=f"job is {job.stage!r}; only failed/blocked jobs can be retried",
        )
    updated = await repos.processing.reenqueue(
        job_id,
        stage="enqueued",
        reset_attempts=True,
        updated_by=current_user.user_id,
    )
    # WS4 Gate 6 (workstream W2 / gap G6-B) — human retry gate after automation.
    await _record_human_gate_audit(
        repos,
        job_id=job_id,
        action="automatic_processing:retried",
        actor=current_user.user_id,
        stage_from=job.stage,
        stage_to=updated.stage if updated is not None else "enqueued",
        status_from=job.status,
        status_to=updated.status if updated is not None else "pending",
        extra={
            "gate": "retry",
            "source_item_id": job.source_item_id,
        },
    )
    return _job_payload(updated)


class ReviewPayload(BaseModel):
    """Distinct customer/owner verification (D5)."""

    approved: bool
    rejection_reason: Optional[str] = None
    customer_notes: Optional[str] = None


@router.post("/jobs/{job_id}/review")
async def review_job(
    job_id: str,
    payload: ReviewPayload,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Customer/owner review approval (or rejection) of a processed job.

    Only the organisation's owner/admin (or CarbonTally internal staff) may
    approve; members/viewers are denied. Rejection routes the job back to the
    manual-review gate with the customer's reason.
    """
    job = await _checked_job(current_user, repos, job_id)
    if job.stage != "review":
        raise HTTPException(
            status_code=409,
            detail=(
                f"job is {job.stage!r}; only jobs awaiting review can be "
                "approved or rejected"
            ),
        )
    if not payload.approved and not payload.rejection_reason:
        raise HTTPException(
            status_code=422,
            detail="a rejection reason is required when rejecting a job",
        )
    updated = await repos.processing.complete_review(
        job_id,
        approved=payload.approved,
        reviewer=current_user.user_id,
        rejection_reason=payload.rejection_reason,
        customer_notes=payload.customer_notes,
    )
    # Stamp the underlying manual-extraction item with the same decision so the
    # existing customer-review surface and evidence chain stay consistent.
    if job.source_item_id:
        await repos.manual_extraction.customer_review(
            job.source_item_id,
            payload.approved,
            current_user.user_id,
            payload.rejection_reason,
            payload.customer_notes,
        )
    # WS4 Gate 6 (workstream W2 / gap G6-B) — human customer review (approve /
    # reject) after automation.
    _review_extra: dict[str, object] = {
        "gate": "approve" if payload.approved else "reject",
        "approved": payload.approved,
        "source_item_id": job.source_item_id,
    }
    if payload.rejection_reason:
        _review_extra["rejection_reason"] = payload.rejection_reason
    if payload.customer_notes:
        _review_extra["customer_notes"] = payload.customer_notes
    await _record_human_gate_audit(
        repos,
        job_id=job_id,
        action=(
            "automatic_processing:approved"
            if payload.approved
            else "automatic_processing:rejected"
        ),
        actor=current_user.user_id,
        stage_from=job.stage,
        stage_to=updated.stage if updated is not None else (
            "completed" if payload.approved else "blocked"
        ),
        status_from=job.status,
        status_to=updated.status if updated is not None else (
            "approved" if payload.approved else "manual_review"
        ),
        extra=_review_extra,
    )
    return _job_payload(updated)


class EnqueuePayload(BaseModel):
    processing_type: str = "utility"



@router.post("/documents/{file_id}/enqueue", status_code=201)
async def enqueue_document(
    file_id: str,
    payload: EnqueuePayload,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Enqueue an existing uploaded document for automatic processing.

    Finds-or-creates the manual-extraction ``Uploads`` batch + item (the
    evidence-chain root) and creates the durable job. Idempotent: a document
    that already has an active job returns that job instead of duplicating it.
    Org-scoped; internal staff and active-consultant grants pass.
    """
    doc = await repos.files.get(file_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    await ensure_processing_org_access(current_user, repos, doc.organization_id)

    from services.storage import path_from_url

    # Find-or-create the Uploads manual-extraction batch.
    batches = await repos.manual_extraction.list_batches(doc.organization_id)
    batch = next(
        (
            b
            for b in batches
            if b.batch_name == "Uploads"
            and b.status in ("open", "in_progress")
        ),
        None,
    )
    if batch is None:
        batch = await repos.manual_extraction.create_batch(
            org_id=doc.organization_id,
            batch_name="Uploads",
            total_documents=1,
            total_pages=doc.metadata.get("ocr", {}).get("page_count") or 1,
            total_cost=0.0,
            currency="GBP",
            batch_description="Auto-created from document uploads",
            price_per_page=None,
            created_by=current_user.user_id,
        )
    item = await repos.manual_extraction.find_item_by_file(
        doc.organization_id, doc.name
    )
    if item is None:
        item = await repos.manual_extraction.create_item(
            batch.id,
            doc.name,
            path_from_url(doc.path),
            doc.metadata.get("ocr", {}).get("page_count") or 1,
            (doc.file_type or "OTHER").lower(),
            "pending",
            file_id=doc.id,
        )
    # Idempotency: a live job for this item short-circuits.
    existing = await repos.processing.get_by_item(item.id)
    if existing is not None and not existing.terminal:
        return _job_payload(existing)
    job = await repos.processing.create(
        organization_id=doc.organization_id,
        file_name=doc.name,
        file_url=path_from_url(doc.path),
        file_type=doc.file_type,
        processing_type=payload.processing_type,
        created_by=current_user.user_id,
        source_item_id=item.id,
        metadata={
            "mime": doc.mime_type,
            "page_count": doc.metadata.get("ocr", {}).get("page_count"),
            "document_id": doc.id,
        },
    )
    return _job_payload(job)

