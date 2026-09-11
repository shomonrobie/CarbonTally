-- ============================================================================
-- CarbonTally V3 — Phase A (CL-56): Durable Automatic Document Processing
-- File: 20260829000000_v3m9_durable_automatic_processing.sql
--
-- Makes the RC2 ``document_processing_queue`` table the durable job store for
-- the automatic document-processing pipeline:
--
--     UPLOAD → INGEST → EXTRACTION → MAPPING → VALIDATION → CALCULATION
--     → EVIDENCE → REVIEW/APPROVAL → REPORTING
--
-- The table's existing ``status`` column keeps the RC2 vocabulary
-- (pending/processing/ai_extracted/manual_review/manual_extraction/qc/
-- customer_review/approved/rejected/completed/failed) so legacy consumers and
-- the existing CHECK constraint remain valid. The new fine-grained ``stage``
-- column records the exact pipeline step the durable job is at, and the new
-- bookkeeping columns support retry, idempotency, resumability and the
-- confidence/manual-review gates:
--
--   * attempt_count / max_attempts — retry governance (dead-letter after cap)
--   * last_error — the most recent failure detail (never leaked to clients)
--   * locked_at / lock_token — durable single-owner claim (FOR UPDATE SKIP
--     LOCKED + stale-lock recovery)
--   * extracted_data / mapped_data / validation_result / calculation_snapshot_id
--     — per-stage persisted outputs (the resume markers)
--   * manual_review_reason — why the job is awaiting a human (gate)
--   * source_item_id — authoritative link to manual_extraction_items (the
--     evidence chain root used by calculation_snapshots.source_item_id)
--   * per-stage completed-at timestamps — persisted progress
--   * reprocess_count / pipeline_version — provenance for re-runs
--
-- Non-destructive, additive columns with defaults; existing rows unaffected.
-- Idempotent: ADD COLUMN IF NOT EXISTS.
-- ============================================================================

ALTER TABLE public.document_processing_queue
    ADD COLUMN IF NOT EXISTS stage VARCHAR,
    ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS max_attempts INTEGER NOT NULL DEFAULT 3,
    ADD COLUMN IF NOT EXISTS last_error TEXT,
    ADD COLUMN IF NOT EXISTS locked_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS lock_token TEXT,
    ADD COLUMN IF NOT EXISTS extracted_data JSONB,
    ADD COLUMN IF NOT EXISTS mapped_data JSONB,
    ADD COLUMN IF NOT EXISTS validation_result JSONB,
    ADD COLUMN IF NOT EXISTS calculation_snapshot_id UUID,
    ADD COLUMN IF NOT EXISTS manual_review_reason TEXT,
    ADD COLUMN IF NOT EXISTS notified_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS pipeline_version VARCHAR,
    ADD COLUMN IF NOT EXISTS source_item_id UUID,
    ADD COLUMN IF NOT EXISTS ingested_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS extracted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS mapped_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS validated_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS calculated_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS review_ready_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS reprocess_count INTEGER NOT NULL DEFAULT 0;

-- Durable-claim index: the worker claims runnable jobs oldest-first with
-- FOR UPDATE SKIP LOCKED (status/stage partial index keeps it narrow).
CREATE INDEX IF NOT EXISTS dpq_auto_claim_idx
    ON public.document_processing_queue (created_at, id)
    WHERE status = ANY (ARRAY[
        'pending'::character varying,
        'processing'::character varying,
        'manual_review'::character varying
    ]);

-- Org-scoped listing index (customer/consultant/ops job dashboards).
CREATE INDEX IF NOT EXISTS dpq_org_created_idx
    ON public.document_processing_queue (organization_id, created_at DESC);

-- Lock-token lookup index for stale-lock recovery and claim release.
CREATE INDEX IF NOT EXISTS dpq_lock_token_idx
    ON public.document_processing_queue (lock_token)
    WHERE lock_token IS NOT NULL;

-- Snapshot lookup index for the no-duplicate-calculation guard.
CREATE INDEX IF NOT EXISTS dpq_snapshot_idx
    ON public.document_processing_queue (calculation_snapshot_id)
    WHERE calculation_snapshot_id IS NOT NULL;

COMMENT ON COLUMN public.document_processing_queue.stage IS
    'Fine-grained automatic-pipeline stage (enqueued/ingesting/extracting/mapping/'
    'validating/calculating/review/completed/failed/blocked).';
COMMENT ON COLUMN public.document_processing_queue.attempt_count IS
    'Number of pipeline execution attempts for the current stage (retry cap).';
COMMENT ON COLUMN public.document_processing_queue.max_attempts IS
    'Retry cap after which the job is dead-lettered to failed/blocked.';
COMMENT ON COLUMN public.document_processing_queue.locked_at IS
    'Timestamp the worker claimed the job (stale-lock recovery basis).';
COMMENT ON COLUMN public.document_processing_queue.lock_token IS
    'Unique claim token owned by the worker processing this job.';
COMMENT ON COLUMN public.document_processing_queue.extracted_data IS
    'Structured extraction output persisted by the extraction stage (resume marker).';
COMMENT ON COLUMN public.document_processing_queue.mapped_data IS
    'Mapping decisions (factor + tenant references) persisted by the mapping stage.';
COMMENT ON COLUMN public.document_processing_queue.validation_result IS
    'Persisted validation findings (passed/failed + findings list).';
COMMENT ON COLUMN public.document_processing_queue.calculation_snapshot_id IS
    'Immutable calculation_snapshots.id produced for this job (no-duplicate guard).';
COMMENT ON COLUMN public.document_processing_queue.manual_review_reason IS
    'Why the job awaits a human (extraction confidence / no factor / rejection).';
COMMENT ON COLUMN public.document_processing_queue.source_item_id IS
    'manual_extraction_items.id this job drives (evidence chain root).';
