"""Durable automatic-processing job repository (V3 Phase A / CL-56).

Persistence for ``document_processing_queue`` as the durable job store of the
automatic pipeline. The repository owns the SQL (including the durable
``FOR UPDATE SKIP LOCKED`` claim) and the RC2/V3M-9 row mapping; it contains no
business logic — stage transitions and gates are decided by the service layer
against the :mod:`domain.automatic_processing` state machine.

Key operations
--------------
* :meth:`create` — record a runnable job for an uploaded document.
* :meth:`claim_next` — atomically claim up to ``limit`` runnable jobs
  (oldest-first, ``FOR UPDATE SKIP LOCKED``) for the worker.
* :meth:`advance_stage` — persist a stage transition + status + output.
* :meth:`mark_failed` / :meth:`mark_blocked` — retry/dead-letter bookkeeping.
* :meth:`release_stale_locks` — resumability: return crashed workers' jobs to
  the runnable pool (the job's persisted outputs make re-entry idempotent).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.automatic_processing import (
    AutomaticProcessingJob,
    PIPELINE_VERSION,
    STAGE_TO_STATUS,
)
from domain.operational_health import (
    HEARTBEAT_METRIC_NAME,
    HEARTBEAT_METRIC_TYPE,
)

#: Every job column the mapper reads (RC2 + V3M-9 additions).
_JOB_COLUMNS = (
    "id, organization_id, customer_document_id, processing_type, status, "
    "file_name, file_url, file_size_bytes, file_type, page_count, "
    "ai_extraction_result, ai_confidence_score, ai_extraction_method, "
    "ai_extracted_at, ai_mapped_facility_id, ai_mapped_asset_id, "
    "ai_mapped_supplier_id, ai_mapping_confidence, metadata, "
    "stage, attempt_count, max_attempts, last_error, locked_at, lock_token, "
    "extracted_data, mapped_data, validation_result, calculation_snapshot_id, "
    "manual_review_reason, notified_at, pipeline_version, source_item_id, "
    "ingested_at, extracted_at, mapped_at, validated_at, calculated_at, "
    "review_ready_at, reprocess_count, created_at, updated_at, completed_at, "
    "emission_factor_used, batch_id, workflow_error_count, "
    "automation_provider, automation_model, automation_model_version, "
    "automation_extracted_data, created_by, updated_by, customer_reviewed_by, "
    "customer_reviewed_at, customer_approved, customer_notes, "
    "customer_rejection_reason"
)


def _uid(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return value


def _row_to_job(row: Any) -> AutomaticProcessingJob:
    r = dict(row)
    return AutomaticProcessingJob(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        file_name=str(r["file_name"]),
        file_url=str(r["file_url"]),
        file_type=r.get("file_type"),
        processing_type=str(r.get("processing_type") or "utility"),
        status=str(r.get("status") or "pending"),
        stage=r.get("stage"),
        attempt_count=int(r.get("attempt_count") or 0),
        max_attempts=int(r.get("max_attempts") or 3),
        last_error=r.get("last_error"),
        extracted_data=loads_jsonb(r.get("extracted_data")) or None,
        mapped_data=loads_jsonb(r.get("mapped_data")) or None,
        validation_result=loads_jsonb(r.get("validation_result")) or None,
        calculation_snapshot_id=_uid(r.get("calculation_snapshot_id")),
        manual_review_reason=r.get("manual_review_reason"),
        source_item_id=_uid(r.get("source_item_id")),
        metadata=loads_jsonb(r.get("metadata")) or {},
        pipeline_version=r.get("pipeline_version"),
        created_at=_dt(r.get("created_at")),
        updated_at=_dt(r.get("updated_at")),
        completed_at=_dt(r.get("completed_at")),
        locked_at=_dt(r.get("locked_at")),
        lock_token=r.get("lock_token"),
        ingested_at=_dt(r.get("ingested_at")),
        extracted_at=_dt(r.get("extracted_at")),
        mapped_at=_dt(r.get("mapped_at")),
        validated_at=_dt(r.get("validated_at")),
        calculated_at=_dt(r.get("calculated_at")),
        review_ready_at=_dt(r.get("review_ready_at")),
        notified_at=_dt(r.get("notified_at")),
        automation_provider=r.get("automation_provider"),
        automation_model=r.get("automation_model"),
        automation_model_version=r.get("automation_model_version"),
        automation_extracted_data=loads_jsonb(r.get("automation_extracted_data"))
        or None,
        reprocess_count=int(r.get("reprocess_count") or 0),
        # WS4 Gate 6 (workstream W3 / gap G6-C) — authoritative human actor
        # fields persisted by the human gates (read-only; see domain model).
        created_by=_uid(r.get("created_by")),
        updated_by=_uid(r.get("updated_by")),
        customer_reviewed_by=_uid(r.get("customer_reviewed_by")),
        customer_reviewed_at=_dt(r.get("customer_reviewed_at")),
        customer_approved=(
            bool(r["customer_approved"])
            if r.get("customer_approved") is not None
            else None
        ),
        customer_notes=r.get("customer_notes"),
        customer_rejection_reason=r.get("customer_rejection_reason"),
    )


class DocumentProcessingRepository(AbstractRepository[AutomaticProcessingJob]):
    """Durable job store for the automatic document-processing pipeline."""
    # -- job lifecycle ------------------------------------------------------

    async def create(
        self,
        *,
        organization_id: str,
        file_name: str,
        file_url: str,
        file_type: Optional[str],
        processing_type: str = "utility",
        created_by: Optional[str] = None,
        source_item_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        max_attempts: int = 3,
    ) -> AutomaticProcessingJob:
        """Record a runnable job (``enqueued``/``pending``)."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.document_processing_queue (
                organization_id, processing_type, status, file_name, file_url,
                file_type, stage, attempt_count, max_attempts, metadata,
                pipeline_version, created_by, created_at, updated_at,
                source_item_id
            ) VALUES ($1, $2, 'pending', $3, $4, $5, 'enqueued', 0, $6,
                      $7, $8, $9, NOW(), NOW(), $10)
            RETURNING {_JOB_COLUMNS}
            """,
            organization_id,
            processing_type,
            file_name,
            file_url,
            file_type,
            int(max_attempts),
            dumps_jsonb(metadata or {}),
            PIPELINE_VERSION,
            created_by,
            source_item_id,
        )
        if row is None:
            raise RuntimeError("document_processing_queue insert returned no row")
        return _row_to_job(row)

    async def get(self, job_id: str) -> Optional[AutomaticProcessingJob]:
        row = await self._fetch_one(
            f"SELECT {_JOB_COLUMNS} FROM public.document_processing_queue "
            "WHERE id = $1",
            job_id,
        )
        return _row_to_job(row) if row is not None else None

    async def get_by_item(self, item_id: str) -> Optional[AutomaticProcessingJob]:
        """Resolve the durable job driving a manual-extraction item."""
        row = await self._fetch_one(
            f"SELECT {_JOB_COLUMNS} FROM public.document_processing_queue "
            "WHERE source_item_id = $1 ORDER BY created_at DESC LIMIT 1",
            item_id,
        )
        return _row_to_job(row) if row is not None else None

    async def list_for_org(
        self,
        org_id: str,
        *,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AutomaticProcessingJob]:
        query = (
            f"SELECT {_JOB_COLUMNS} FROM public.document_processing_queue "
            "WHERE organization_id = $1"
        )
        args: list[Any] = [org_id]
        if status is not None:
            args.append(status)
            query += f" AND status = ${len(args)}"
        if stage is not None:
            args.append(stage)
            query += f" AND stage = ${len(args)}"
        query += " ORDER BY created_at DESC"
        query += f" LIMIT {int(limit)} OFFSET {int(offset)}"
        rows = await self._fetch_all(query, *args)
        return [_row_to_job(r) for r in rows]



    # -- durable claim ------------------------------------------------------

    async def claim_next(
        self,
        lock_token: str,
        *,
        limit: int = 5,
        stale_after_seconds: int = 300,
    ) -> list[AutomaticProcessingJob]:
        """Atomically claim up to ``limit`` runnable jobs for this worker.

        Uses ``FOR UPDATE SKIP LOCKED`` so concurrent workers never double-claim.
        Jobs whose claim is older than ``stale_after_seconds`` (a crashed
        worker) are recovered into the runnable pool first — resumability.
        """
        now = datetime.now(timezone.utc)
        stale_before = now - timedelta(seconds=stale_after_seconds)
        await self._execute(
            "UPDATE public.document_processing_queue SET locked_at = NULL, "
            "lock_token = NULL WHERE locked_at IS NOT NULL AND locked_at < $1",
            stale_before,
        )
        rows = await self._fetch_all(
            f"""
            WITH claimed AS (
                SELECT id FROM public.document_processing_queue
                WHERE stage IN ('enqueued', 'ingesting', 'extracting', 'mapping',
                                'validating', 'calculating')
                   OR (stage IS NULL AND status = 'pending')
                ORDER BY created_at, id
                FOR UPDATE SKIP LOCKED
                LIMIT {int(limit)}
            )
            UPDATE public.document_processing_queue q
            SET locked_at = $1, lock_token = $2, updated_at = $1
            FROM claimed
            WHERE q.id = claimed.id
            RETURNING {", ".join(f"q.{c}" for c in _JOB_COLUMNS.split(", "))}
            """,
            now,
            lock_token,
        )
        return [_row_to_job(r) for r in rows]

    async def release_lock(self, job_id: str, lock_token: str) -> bool:
        """Release a claim (idempotent; only the owning token may release)."""
        status = await self._execute(
            "UPDATE public.document_processing_queue SET locked_at = NULL, "
            "lock_token = NULL WHERE id = $1 AND lock_token = $2",
            job_id,
            lock_token,
        )
        return "UPDATE 1" in status

    async def release_stale_locks(self, stale_after_seconds: int = 300) -> int:
        """Return crashed workers' claims to the runnable pool (resumability)."""
        stale_before = datetime.now(timezone.utc) - timedelta(
            seconds=stale_after_seconds
        )
        status = await self._execute(
            "UPDATE public.document_processing_queue SET locked_at = NULL, "
            "lock_token = NULL WHERE locked_at IS NOT NULL AND locked_at < $1",
            stale_before,
        )
        try:
            return int(status.split()[-1])
        except (ValueError, IndexError):
            return 0

    # -- stage transitions / persisted outputs ------------------------------

    async def advance_stage(
        self,
        job_id: str,
        *,
        target_stage: str,
        lock_token: str,
        extracted_data: Optional[dict] = None,
        mapped_data: Optional[dict] = None,
        validation_result: Optional[dict] = None,
        calculation_snapshot_id: Optional[str] = None,
        manual_review_reason: Optional[str] = None,
        attempt_count: Optional[int] = None,
        page_count: Optional[int] = None,
        ai_confidence_score: Optional[float] = None,
        ai_extraction_method: Optional[str] = None,
        ai_mapping_confidence: Optional[float] = None,
        emission_factor_used: Optional[str] = None,
        metadata: Optional[dict] = None,
        ai_extraction_result: Optional[dict] = None,
        ai_extracted_at: Optional[datetime] = None,
        ai_processing_time_ms: Optional[int] = None,
        # WS4 Gate 5 (task T3) — write-once automated-execution attribution block.
        # Written only at the extraction->mapping advance; COALESCE semantics keep
        # the first persisted value immutable (never overwritten by re-runs or
        # later human processing).
        automation_provider: Optional[str] = None,
        automation_model: Optional[str] = None,
        automation_model_version: Optional[str] = None,
        # WS4 Gate 6 (workstream W1 / gap G6-A) — original automated extraction
        # output, persisted write-once at the SAME extraction advance that first
        # persists `extracted_data` (deterministic AND AI-contributing runs).
        # COALESCE first-write-wins: re-runs and human saves can never replace
        # or clear the preserved original output.
        automation_extracted_data: Optional[dict] = None,
    ) -> Optional[AutomaticProcessingJob]:
        """Persist one stage transition with its outputs and timestamps.

        Only the claiming worker (``lock_token``) may advance the job, which
        keeps concurrent workers from stepping on each other. Idempotency is
        preserved because the caller supplies the same outputs on replay and
        the service layer skips stages whose resume markers already exist.
        """
        status = STAGE_TO_STATUS.get(target_stage, "processing")
        sets = [
            "stage = $3",
            "status = $4",
            "updated_at = NOW()",
            "last_error = NULL",
            "locked_at = NOW()",
        ]
        args: list[Any] = [job_id, lock_token, target_stage, status]
        if extracted_data is not None:
            args.append(dumps_jsonb(extracted_data))
            sets.append(f"extracted_data = ${len(args)}")
        if mapped_data is not None:
            args.append(dumps_jsonb(mapped_data))
            sets.append(f"mapped_data = ${len(args)}")
        if validation_result is not None:
            args.append(dumps_jsonb(validation_result))
            sets.append(f"validation_result = ${len(args)}")
        if calculation_snapshot_id is not None:
            args.append(calculation_snapshot_id)
            sets.append(f"calculation_snapshot_id = ${len(args)}")
        if manual_review_reason is not None:
            args.append(manual_review_reason)
            sets.append(f"manual_review_reason = ${len(args)}")
        if attempt_count is not None:
            args.append(int(attempt_count))
            sets.append(f"attempt_count = ${len(args)}")
        if page_count is not None:
            args.append(int(page_count))
            sets.append(f"page_count = ${len(args)}")
        if ai_confidence_score is not None:
            args.append(float(ai_confidence_score))
            sets.append(f"ai_confidence_score = ${len(args)}")
        if ai_extraction_method is not None:
            args.append(ai_extraction_method)
            sets.append(f"ai_extraction_method = ${len(args)}")
        if ai_mapping_confidence is not None:
            args.append(float(ai_mapping_confidence))
            sets.append(f"ai_mapping_confidence = ${len(args)}")
        if emission_factor_used is not None:
            args.append(emission_factor_used)
            sets.append(f"emission_factor_used = ${len(args)}")
        if metadata is not None:
            # JSONB top-level merge — never clobbers existing job metadata
            # (mime/page_count/document_id, prior provenance, ...).
            args.append(dumps_jsonb(metadata))
            sets.append(f"metadata = COALESCE(metadata, '{{}}'::jsonb) || ${len(args)}")
        if ai_extraction_result is not None:
            args.append(dumps_jsonb(ai_extraction_result))
            sets.append(f"ai_extraction_result = ${len(args)}")
        if ai_extracted_at is not None:
            args.append(ai_extracted_at)
            sets.append(f"ai_extracted_at = ${len(args)}")
        if ai_processing_time_ms is not None:
            args.append(int(ai_processing_time_ms))
            sets.append(f"ai_processing_time_ms = ${len(args)}")
        # Write-once automation attribution (COALESCE = first write wins; a NULL
        # column is filled, a non-NULL column is never overwritten).
        if automation_provider is not None:
            args.append(automation_provider)
            sets.append(f"automation_provider = COALESCE(automation_provider, ${len(args)})")
        if automation_model is not None:
            args.append(automation_model)
            sets.append(f"automation_model = COALESCE(automation_model, ${len(args)})")
        if automation_model_version is not None:
            args.append(automation_model_version)
            sets.append(
                f"automation_model_version = COALESCE(automation_model_version, ${len(args)})"
            )
        # WS4 Gate 6 (workstream W1 / gap G6-A) — write-once preservation of the
        # original automated extraction output (COALESCE = first write wins).
        if automation_extracted_data is not None:
            args.append(dumps_jsonb(automation_extracted_data))
            sets.append(
                "automation_extracted_data = "
                f"COALESCE(automation_extracted_data, ${len(args)})"
            )

        # Per-stage completion stamps (persisted progress).
        if target_stage == "extracting":
            sets.append("extracted_at = NOW()")
        if target_stage == "mapping":
            sets.append("mapped_at = NOW()")
        if target_stage == "validating":
            sets.append("validated_at = NOW()")
        if target_stage == "calculating":
            sets.append("calculated_at = NOW()")
        if target_stage == "review":
            sets.append("review_ready_at = NOW()")
        if target_stage == "completed":
            sets.append("completed_at = NOW()")
        row = await self._fetch_one(
            f"UPDATE public.document_processing_queue "
            f"SET {', '.join(sets)} "
            f"WHERE id = $1 AND lock_token = $2 RETURNING {_JOB_COLUMNS}",
            *args,
        )
        return _row_to_job(row) if row is not None else None

    async def mark_failed(
        self,
        job_id: str,
        *,
        last_error: str,
        lock_token: str,
        attempt_count: Optional[int] = None,
    ) -> Optional[AutomaticProcessingJob]:
        """Dead-letter a job into ``failed`` (retryable via re-enqueue)."""
        row = await self._fetch_one(
            f"""
            UPDATE public.document_processing_queue
            SET stage = 'failed', status = 'failed', last_error = $3,
                locked_at = NULL, lock_token = NULL, updated_at = NOW()
                {', attempt_count = $4' if attempt_count is not None else ''}
            WHERE id = $1 AND lock_token = $2
            RETURNING {_JOB_COLUMNS}
            """,
            *([job_id, lock_token, last_error, int(attempt_count)]
              if attempt_count is not None
              else [job_id, lock_token, last_error]),
        )
        return _row_to_job(row) if row is not None else None

    async def mark_blocked(
        self,
        job_id: str,
        *,
        reason: str,
        lock_token: str,
        last_error: Optional[str] = None,
    ) -> Optional[AutomaticProcessingJob]:
        """Route a job to the manual-review gate (``blocked``/``manual_review``)."""
        row = await self._fetch_one(
            f"""
            UPDATE public.document_processing_queue
            SET stage = 'blocked', status = 'manual_review',
                manual_review_reason = $3,
                last_error = {'$4' if last_error is not None else 'NULL'},
                locked_at = NULL, lock_token = NULL, updated_at = NOW()
            WHERE id = $1 AND lock_token = $2
            RETURNING {_JOB_COLUMNS}
            """,
            *([job_id, lock_token, reason, last_error]
              if last_error is not None
              else [job_id, lock_token, reason]),
        )
        return _row_to_job(row) if row is not None else None

    async def reenqueue(
        self,
        job_id: str,
        *,
        stage: str = "enqueued",
        reset_attempts: bool = True,
        updated_by: Optional[str] = None,
    ) -> Optional[AutomaticProcessingJob]:
        """Return a ``failed``/``blocked`` job to the runnable pool.

        ``stage`` selects the re-entry point: ``enqueued`` restarts the whole
        pipeline (idempotent — persisted outputs are the resume markers), or a
        specific stage (``extracting``/``mapping``/``validating``) re-runs from
        there after a human corrected the data.
        """
        row = await self._fetch_one(
            f"""
            UPDATE public.document_processing_queue
            SET stage = $2, status = 'pending', manual_review_reason = NULL,
                last_error = NULL, locked_at = NULL, lock_token = NULL,
                attempt_count = {'0' if reset_attempts else 'attempt_count'},
                reprocess_count = reprocess_count + 1, updated_at = NOW(),
                updated_by = $3
            WHERE id = $1
            RETURNING {_JOB_COLUMNS}
            """,
            job_id,
            stage,
            updated_by,
        )
        return _row_to_job(row) if row is not None else None

    async def save(self, entity: AutomaticProcessingJob) -> AutomaticProcessingJob:
        """No-op passthrough (the repository persists via explicit methods)."""
        return entity

    async def delete(self, id: str) -> None:
        """Never hard-delete durable jobs — soft-state only."""
        return None

    async def complete_review(
        self,
        job_id: str,
        *,
        approved: bool,
        reviewer: str,
        rejection_reason: Optional[str] = None,
        customer_notes: Optional[str] = None,
    ) -> Optional[AutomaticProcessingJob]:
        """Persist the distinct customer/owner verification decision (D5).

        Approval advances the job ``review -> completed``; rejection routes it
        to the manual-review gate (``blocked``) with the customer's reason so a
        human reworks the extraction/mapping before it can re-enter the pipeline.
        The underlying ``manual_extraction_items`` row is stamped by the API
        layer through the existing :class:`ManualExtractionRepository`.
        """
        if approved:
            row = await self._fetch_one(
                f"""
                UPDATE public.document_processing_queue
                SET stage = 'completed', status = 'approved',
                    customer_reviewed_by = $2, customer_reviewed_at = NOW(),
                    customer_approved = TRUE, customer_notes = $3,
                    completed_at = NOW(), locked_at = NULL, lock_token = NULL,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING {_JOB_COLUMNS}
                """,
                job_id,
                reviewer,
                customer_notes,
            )
        else:
            row = await self._fetch_one(
                f"""
                UPDATE public.document_processing_queue
                SET stage = 'blocked', status = 'manual_review',
                    customer_reviewed_by = $2, customer_reviewed_at = NOW(),
                    customer_approved = FALSE,
                    customer_rejection_reason = $3,
                    customer_notes = $4,
                    manual_review_reason = COALESCE(
                        manual_review_reason,
                        'customer rejected: ' || $3),
                    locked_at = NULL, lock_token = NULL, updated_at = NOW()
                WHERE id = $1
                RETURNING {_JOB_COLUMNS}
                """,
                job_id,
                reviewer,
                rejection_reason,
                customer_notes,
            )
        return _row_to_job(row) if row is not None else None

    async def mark_notified(self, job_id: str) -> Optional[AutomaticProcessingJob]:
        """Stamp the job as notified (dedupe repeated notifications)."""
        row = await self._fetch_one(
            f"""
            UPDATE public.document_processing_queue
            SET notified_at = NOW(), updated_at = NOW()
            WHERE id = $1 AND notified_at IS NULL
            RETURNING {_JOB_COLUMNS}
            """,
            job_id,
        )
        return _row_to_job(row) if row is not None else None

    async def sync_item_data(
        self,
        job_id: str,
        *,
        extracted_data: Optional[dict] = None,
        mapped_data: Optional[dict] = None,
    ) -> Optional[AutomaticProcessingJob]:
        """Copy human-corrected item data into the durable job.

        Used by the manual-review gate: a human fixes the extraction/mapping in
        the item workbench and confirms the job; this method persists the
        corrected values so the resumed pipeline validates the corrections
        (and the validation/calculation outputs are regenerated from them).

        WS4 Gate 6 (workstream W4 / gap G6-D) — stale-resume integrity: when a
        supplied value is DISTINCT from the persisted value, the downstream
        resume markers that would otherwise let the pipeline skip validation /
        calculation on the corrected data are invalidated
        (``validation_result`` and ``calculation_snapshot_id`` are cleared; the
        per-line snapshot dedupe additionally keys request ids on the data
        digest, so a corrected payload cannot reuse the pre-correction
        snapshot). Identical (no-op) syncs leave the markers intact so a plain
        confirm/retry never causes unnecessary re-validation/duplicate
        snapshots. ``automation_extracted_data`` and the Gate-5 automation
        block are never touched here.
        """
        row = await self._fetch_one(
            f"""
            UPDATE public.document_processing_queue
            SET extracted_data = COALESCE($2::jsonb, extracted_data),
                mapped_data = COALESCE($3::jsonb, mapped_data),
                validation_result = CASE
                    WHEN ($2::jsonb IS NOT NULL AND $2::jsonb IS DISTINCT FROM extracted_data)
                      OR ($3::jsonb IS NOT NULL AND $3::jsonb IS DISTINCT FROM mapped_data)
                    THEN NULL ELSE validation_result END,
                calculation_snapshot_id = CASE
                    WHEN ($2::jsonb IS NOT NULL AND $2::jsonb IS DISTINCT FROM extracted_data)
                      OR ($3::jsonb IS NOT NULL AND $3::jsonb IS DISTINCT FROM mapped_data)
                    THEN NULL ELSE calculation_snapshot_id END,
                updated_at = NOW()
            WHERE id = $1
            RETURNING {_JOB_COLUMNS}
            """,
            job_id,
            dumps_jsonb(extracted_data) if extracted_data is not None else None,
            dumps_jsonb(mapped_data) if mapped_data is not None else None,
        )
        return _row_to_job(row) if row is not None else None

    async def count_by_stage(self, org_id: str) -> dict[str, int]:
        """Aggregate job counts per fine-grained stage for one organisation."""
        rows = await self._fetch_all(
            "SELECT stage, COUNT(*) AS n FROM public.document_processing_queue "
            "WHERE organization_id = $1 GROUP BY stage",
            org_id,
        )
        return {str(r["stage"] or "enqueued"): int(r["n"]) for r in rows}

    # ------------------------------------------------------------------
    # Phase 8-X X1 — operational health (queue visibility + worker heartbeat)
    #
    # Bounded first release (PO decisions 2026-09-14): worker/queue visibility
    # and health/worker heartbeat only. Both use EXISTING storage: the queue
    # columns already persisted on this table, and the existing generic
    # ``dashboard_metrics`` store (``expires_at`` already exists) for the tick.
    # NO schema change is introduced (8-X §13 M1: "no schema change required").
    # ------------------------------------------------------------------

    async def queue_visibility_rows(self, *, limit: int = 2000) -> list[dict]:
        """Rows backing the M1 worker/queue visibility read model.

        Only columns the queue already persists are read; the classification
        itself lives in :mod:`domain.operational_health` (pure, unit-tested).
        """
        rows = await self._fetch_all(
            """
            SELECT id, organization_id, stage, status,
                   attempt_count, max_attempts, workflow_error_count,
                   workflow_next_retry_at, last_error,
                   locked_at, lock_token, created_at, ingested_at
            FROM public.document_processing_queue
            ORDER BY created_at DESC
            LIMIT $1
            """,
            int(limit),
        )
        return [dict(r) for r in rows]

    async def record_worker_heartbeat(
        self,
        *,
        worker_id: str,
        stale_after_seconds: int = 300,
        detail: Optional[dict] = None,
    ) -> dict:
        """Record the worker's liveness tick in the existing metric store.

        Exactly **one** current heartbeat row is maintained (the newest row is
        updated in place; a row is inserted only when none exists). This keeps
        the store bounded without inventing any retention policy — retention for
        ``dashboard_metrics`` remains governed by the existing retention
        configuration, not by X1.
        """
        tick_at = datetime.now(timezone.utc)
        expires_at = tick_at + timedelta(seconds=stale_after_seconds)
        payload = {
            "worker_id": worker_id,
            "tick_at": tick_at.isoformat(),
            "stale_after_seconds": stale_after_seconds,
        }
        if detail:
            payload.update(detail)

        existing = await self._fetch_one(
            """
            SELECT id FROM public.dashboard_metrics
            WHERE metric_type = $1 AND metric_name = $2
            ORDER BY created_at DESC
            LIMIT 1
            """,
            HEARTBEAT_METRIC_TYPE,
            HEARTBEAT_METRIC_NAME,
        )
        if existing is not None:
            row = await self._fetch_one(
                """
                UPDATE public.dashboard_metrics
                SET metric_value = $2::jsonb, expires_at = $3
                WHERE id = $1
                RETURNING id, metric_value, expires_at, created_at
                """,
                existing["id"],
                dumps_jsonb(payload),
                expires_at,
            )
        else:
            row = await self._fetch_one(
                """
                INSERT INTO public.dashboard_metrics
                    (metric_type, metric_name, metric_value, period, expires_at)
                VALUES ($1, $2, $3::jsonb, $4, $5)
                RETURNING id, metric_value, expires_at, created_at
                """,
                HEARTBEAT_METRIC_TYPE,
                HEARTBEAT_METRIC_NAME,
                dumps_jsonb(payload),
                tick_at.strftime("%Y-%m-%d"),
                expires_at,
            )
        return dict(row) if row is not None else {}

    async def latest_worker_heartbeat(self) -> Optional[dict]:
        """The most recent heartbeat, or ``None`` when the worker never ticked.

        ``None`` is returned honestly (the API reports ``UNKNOWN`` liveness)
        rather than being presented as a healthy worker.
        """
        row = await self._fetch_one(
            """
            SELECT metric_value, created_at, expires_at
            FROM public.dashboard_metrics
            WHERE metric_type = $1 AND metric_name = $2
            ORDER BY created_at DESC
            LIMIT 1
            """,
            HEARTBEAT_METRIC_TYPE,
            HEARTBEAT_METRIC_NAME,
        )
        if row is None:
            return None
        value = loads_jsonb(row["metric_value"]) or {}
        return {
            "worker_id": value.get("worker_id"),
            "tick_at": value.get("tick_at"),
            "stale_after_seconds": value.get("stale_after_seconds"),
            "recorded_at": row["created_at"].isoformat() if row["created_at"] else None,
            "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
        }

    async def count_sla_breached(self) -> int:
        """Count processing-queue items flagged as SLA-breached (X2 SLA signal).

        Scope for the first X2 release is the ``processing_queue`` breach flag —
        an existing signal. The SLA *threshold* is never taken from here; it comes
        from the configured SLA setting, and if that setting is absent the X2 SLA
        condition reports "not configured" and raises nothing.
        """
        value = await self._fetchval_count_sla_breached()
        return int(value or 0)

    async def _fetchval_count_sla_breached(self) -> Optional[int]:
        row = await self._fetch_one(
            "SELECT count(*) AS n FROM public.processing_queue "
            "WHERE coalesce(sla_breached, false) = true"
        )
        return int(row["n"]) if row is not None else 0

    async def prune_operational_metrics_before(
        self, cutoff: Any, *, dry_run: bool = True
    ) -> dict:
        """Retention for operational METRIC telemetry only (X2 / `PX-7`).

        Scope is the existing generic metric store (X1's heartbeat row and any
        future operational metric). ``document_processing_queue`` — the durable
        job record — is deliberately **not** touched by any retention rule.
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                eligible = await conn.fetchval(
                    "SELECT count(*) FROM public.dashboard_metrics WHERE created_at < $1",
                    cutoff,
                )
                if not dry_run:
                    await conn.execute(
                        "DELETE FROM public.dashboard_metrics WHERE created_at < $1",
                        cutoff,
                    )
        return {
            "domain": "operational_telemetry_retention_days",
            "scope": "operational metric rows (dashboard_metrics)",
            "cutoff": cutoff.isoformat(),
            "eligible_metrics": int(eligible or 0),
            "applied": not dry_run,
        }

