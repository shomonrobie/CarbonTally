-- ============================================================================
-- CarbonTally V3 — D22 Processing Work Assignment + Extraction Workspace
-- File: 20260821020000_d22_processing_work_assignment.sql
--
-- Implements the approved Processing Entity work-assignment model (actor-model
-- §6.1/§30/§32/§33): CarbonTally assigns extraction work to internal staff OR
-- to a Processing Entity; entity staff may process ONLY the work assigned to
-- their Processing Entity and NEVER gain broad customer-organisation access.
--
-- Change set (minimum robust, additive, backward compatible):
--   1. manual_extraction_batches.entity_id  (EXTEND — nullable FK to
--      processing_entities) — the batch-level extraction assignment carrier.
--      NULL = CarbonTally internal (positive convention, ADR-V3-001 Q5);
--      populated = the Processing Entity performing the work.
--   2. issues.manual_extraction_batch_id    (EXTEND — nullable FK to
--      manual_extraction_batches) — links clarification/rework issues to the
--      extraction batch (the mediated-clarification surface; entity staff may
--      request clarification via entity-scoped issues — never direct
--      entity<->customer communication).
--   3. RLS — entity-scoped SELECT policies mirroring manual_review_queue/
-- ---------------------------------------------------------------------------
-- 1. manual_extraction_batches.entity_id (EXTEND)
-- ---------------------------------------------------------------------------
ALTER TABLE public.manual_extraction_batches
    ADD COLUMN IF NOT EXISTS entity_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'manual_extraction_batches_entity_id_fkey'
    ) THEN
        ALTER TABLE public.manual_extraction_batches
            ADD CONSTRAINT manual_extraction_batches_entity_id_fkey
            FOREIGN KEY (entity_id) REFERENCES public.processing_entities(id)
            ON DELETE RESTRICT;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_manual_extraction_batches_entity_id
    ON public.manual_extraction_batches (entity_id);

COMMENT ON COLUMN public.manual_extraction_batches.entity_id IS
    'Processing Entity allocated this batch (NULL = CarbonTally internal; '
    'ADR-V3-001 Q5). A batch has exactly ONE processing party at a time: '
    'entity_id (entity) OR assigned_to (internal operator). '
    'ON DELETE RESTRICT preserves attribution.';

-- ---------------------------------------------------------------------------
-- 2. issues.manual_extraction_batch_id (EXTEND — mediated clarification)
-- ---------------------------------------------------------------------------
ALTER TABLE public.issues
    ADD COLUMN IF NOT EXISTS manual_extraction_batch_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'issues_manual_extraction_batch_id_fkey'
    ) THEN
        ALTER TABLE public.issues
            ADD CONSTRAINT issues_manual_extraction_batch_id_fkey
            FOREIGN KEY (manual_extraction_batch_id)
            REFERENCES public.manual_extraction_batches(id)
            ON DELETE RESTRICT;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_issues_manual_extraction_batch_id
    ON public.issues (manual_extraction_batch_id);

COMMENT ON COLUMN public.issues.manual_extraction_batch_id IS
    'Links a clarification/rework issue to the manual-extraction batch it '
    'concerns (mediated clarification: Processing Entity -> CarbonTally -> '
    'Customer; NEVER direct entity<->customer communication). Entity-scoped '
    'issues stay invisible to customer-facing surfaces (entity_id IS NULL '
    'storey). ON DELETE RESTRICT preserves attribution.';

-- ---------------------------------------------------------------------------
-- 3. Entity-scoped RLS SELECT policies (additive; V3M-6 pattern)
-- ---------------------------------------------------------------------------

-- 3.1 manual_extraction_batches — entity staff may read batches allocated to
--     their entity (entity_id IS NOT NULL + is_entity_member). Customer-org
--     batches (entity_id IS NULL) keep the existing tenant storey; the two
--     storeys are non-overlapping. SELECT only: assignment is a service-role
--     write flow (V3M-6 convention).
DROP POLICY IF EXISTS manual_extraction_batches_entity_select
    ON public.manual_extraction_batches;
CREATE POLICY manual_extraction_batches_entity_select
    ON public.manual_extraction_batches
    FOR SELECT TO authenticated
    USING (
        entity_id IS NOT NULL
        AND public.is_entity_member(entity_id)
    );

-- 3.2 manual_extraction_items — entity staff may read the items of batches
--     allocated to their entity (entity match resolved via the item's batch).
--     The table has NO other authenticated policy (deny-by-default), so this
--     is purely additive and never widens customer/internal access.
DROP POLICY IF EXISTS manual_extraction_items_entity_select
    ON public.manual_extraction_items;
CREATE POLICY manual_extraction_items_entity_select
    ON public.manual_extraction_items
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1
              FROM public.manual_extraction_batches b
             WHERE b.id = manual_extraction_items.batch_id
               AND b.entity_id IS NOT NULL
               AND public.is_entity_member(b.entity_id)
        )
    );

-- ============================================================================
-- VERIFICATION CHECKLIST (D22)
--   [ ] manual_extraction_batches.entity_id exists (nullable UUID) + FK
--       (processing_entities, ON DELETE RESTRICT) + index + comment
--   [ ] issues.manual_extraction_batch_id exists (nullable UUID) + FK
--       (manual_extraction_batches, ON DELETE RESTRICT) + index + comment
--   [ ] manual_extraction_batches_entity_select present (entity_id IS NOT NULL
--       + is_entity_member) — additive; tenant storey untouched
--   [ ] manual_extraction_items_entity_select present (EXISTS batch entity
--       match) — additive; table stays deny-by-default for non-entity rows
--   [ ] NO entity INSERT/UPDATE/DELETE policies created (writes stay
--       service-role/application)
--   [ ] Existing rows untouched; entity_id / manual_extraction_batch_id = NULL
--   [ ] is_entity_member lifecycle gate intact (entity must be ACTIVE)
--   [ ] No factor data touched; no legacy policy touched
--   [ ] Re-running this file is a no-op
-- ============================================================================

--      upload_batches (V3M-6 pattern, additive; deny-by-default preserved):
--        manual_extraction_batches_entity_select  (entity_id + is_entity_member)
--        manual_extraction_items_entity_select    (via its batch's entity match)
--      NO entity INSERT/UPDATE/DELETE policies are created — entity writes stay
--      service-role/application (V3M-6 convention).
--
-- Assignment/reassignment history is recorded through the existing V3
-- audit_trail (ADR-V3-013 — no new history table; the dormant queue-keyed
-- processing_assignments/reassignment_history family stays untouched).
--
-- Safety:
--   * Additive and backward compatible: existing rows default entity_id NULL
--     (= CarbonTally internal); existing behaviour unchanged.
--   * FK ON DELETE RESTRICT (V3M-1/V3M-2 convention): entity rows and batch
--     rows are never hard-deleted while referenced; the NULL convention is
--     never corrupted.
--   * Existing RLS policies on these tables are UNCHANGED (no policy touched).
--   * No factor data is touched.
-- Idempotent: ADD COLUMN IF NOT EXISTS, guarded FK, CREATE INDEX IF NOT EXISTS,
-- DROP POLICY IF EXISTS + CREATE POLICY.
-- ============================================================================
