-- ============================================================================
-- CarbonTally V3 — Implementation Phase 1, Migration V3M-2
-- File: 20260810010000_v3m2_entity_relationships.sql
--
-- Implements the approved Processing Entity relationships to existing work
-- structures (ADR-V3-001 — DECIDED, Option B; V3 IA §8 V3M-2; V3 Database
-- Impact Plan §4.3).
--
-- Scope (strictly V3M-2 — only the tables explicitly identified by the
-- approved database impact plan):
--   * manual_review_queue.entity_id  (EXTEND — nullable FK to processing_entities)
--   * upload_batches.entity_id       (EXTEND — nullable FK to processing_entities)
--
-- NOT in scope (do not add entity_id to these):
--   * processing_queue / processing_assignments / processing_steps (dormant;
--     retirement per ADR-V3-016; entity scope not required)
--   * document_processing_queue (technical state machine — ADR-V3-004)
--   * report_generation_queue (technical output store)
--   * review_assignment_history (attribution derived via staff/entity, no column)
--
-- Semantics (register ADR-V3-001 Q5 convention):
--   * manual_review_queue.entity_id NULL = CarbonTally internal processing
--   * upload_batches.entity_id NULL      = CarbonTally internal processing
--   * populated = the Processing Entity performing the work
--   * NULL is a POSITIVE value (CarbonTally internal) — never "unknown".
--
-- Safety:
--   * Additive and backward compatible; existing rows default entity_id NULL.
--   * FK ON DELETE RESTRICT (same rationale as V3M-1): entity rows are never
--     hard-deleted while referenced; the NULL convention is never corrupted.
--   * Existing tenant RLS on these tables is UNCHANGED (no policy touched);
--     entity-scoped access policies belong to ADR-V3-010 and are not created.
--   * No factor data is touched.
-- Idempotent: ADD COLUMN IF NOT EXISTS, guarded FK, CREATE INDEX IF NOT EXISTS.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. manual_review_queue.entity_id (EXTEND)
-- ---------------------------------------------------------------------------
ALTER TABLE public.manual_review_queue
    ADD COLUMN IF NOT EXISTS entity_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'manual_review_queue_entity_id_fkey'
    ) THEN
        ALTER TABLE public.manual_review_queue
            ADD CONSTRAINT manual_review_queue_entity_id_fkey
            FOREIGN KEY (entity_id) REFERENCES public.processing_entities(id)
            ON DELETE RESTRICT;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_manual_review_queue_entity_id
    ON public.manual_review_queue (entity_id);

COMMENT ON COLUMN public.manual_review_queue.entity_id IS
    'Processing Entity performing this Work Item (NULL = CarbonTally internal; '
    'ADR-V3-001 Q5). ON DELETE RESTRICT preserves attribution.';

-- ---------------------------------------------------------------------------
-- 2. upload_batches.entity_id (EXTEND)
-- ---------------------------------------------------------------------------
ALTER TABLE public.upload_batches
    ADD COLUMN IF NOT EXISTS entity_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'upload_batches_entity_id_fkey'
    ) THEN
        ALTER TABLE public.upload_batches
            ADD CONSTRAINT upload_batches_entity_id_fkey
            FOREIGN KEY (entity_id) REFERENCES public.processing_entities(id)
            ON DELETE RESTRICT;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_upload_batches_entity_id
    ON public.upload_batches (entity_id);

COMMENT ON COLUMN public.upload_batches.entity_id IS
    'Processing Entity allocated this batch (NULL = CarbonTally internal; '
    'ADR-V3-001 Q5). ON DELETE RESTRICT preserves attribution.';

-- ============================================================================
-- VERIFICATION CHECKLIST (V3M-2)
--   [ ] manual_review_queue.entity_id exists (nullable UUID) + FK + index
--   [ ] upload_batches.entity_id exists (nullable UUID) + FK + index
--   [ ] FKs reference processing_entities(id) ON DELETE RESTRICT
--   [ ] Existing work rows untouched; entity_id = NULL (= CarbonTally internal)
--   [ ] No entity_id added to dormant/technical queues (processing_queue family,
--       document_processing_queue, report_generation_queue, review_assignment_history)
--   [ ] Existing tenant RLS on manual_review_queue / upload_batches unchanged
--   [ ] Factor baseline untouched (DEFRA 7,029 · SEAI 20 · TOTAL 7,049)
--   [ ] Re-running this file is a no-op
-- ============================================================================
