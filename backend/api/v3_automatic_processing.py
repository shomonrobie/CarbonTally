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
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    RepositoryBundle,
    ensure_processing_org_access,
    get_repositories,
)
from auth import AuthUser, require_auth, require_org_admin
from domain.automatic_processing import STAGE_LABELS, AutomaticProcessingJob
from pydantic import BaseModel

router = APIRouter(prefix="/api/v3/processing", tags=["V3 - Automatic Processing"])


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
    return _job_payload(updated)


@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Retry a failed job (dead-letter recovery)."""
    job = await _checked_job(current_user, repos, job_id)
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

