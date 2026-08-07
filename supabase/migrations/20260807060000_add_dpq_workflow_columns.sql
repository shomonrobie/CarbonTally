-- ============================================================================
-- CarbonTally Backend v2.1 — Phase 0, Migration M7 of 8
-- File: 20260807060000_add_dpq_workflow_columns.sql
--
-- Workflow/retry bookkeeping for the document-processing state machine
-- (Backend v2.1 §14.4; Readiness Review R7/R22/R23).
--
-- The document_processing_queue.status column already drives the workflow
-- state machine; these two additive columns support retry governance:
--   * workflow_error_count: failed transition attempts (drives the retry cap)
--   * workflow_next_retry_at: earliest timestamp a retry may be attempted
--
-- Non-destructive, additive columns with defaults. Existing rows unaffected
-- (error count 0, retry time NULL).
-- Idempotent: ADD COLUMN IF NOT EXISTS.
-- ============================================================================

ALTER TABLE public.document_processing_queue
    ADD COLUMN IF NOT EXISTS workflow_error_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS workflow_next_retry_at TIMESTAMPTZ;

COMMENT ON COLUMN public.document_processing_queue.workflow_error_count IS
    'Count of failed workflow transitions for this document (retry cap).';
COMMENT ON COLUMN public.document_processing_queue.workflow_next_retry_at IS
    'Earliest timestamp at which a retry of this workflow may be attempted.';

-- ============================================================================
-- VERIFICATION CHECKLIST (M7)
--   [ ] Column workflow_error_count exists (INTEGER NOT NULL DEFAULT 0)
--   [ ] Column workflow_next_retry_at exists (TIMESTAMPTZ, nullable)
--   [ ] Existing document_processing_queue rows untouched
--   [ ] Re-running this file is a no-op
-- ============================================================================
