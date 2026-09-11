-- ============================================================================
-- CarbonTally V1.2 — Dual-Origin Workflow & CarbonTally QC gate
-- File: 20260902020000_v1_2_dual_origin_workflow.sql
--
-- Approved design: docs/architecture/CARBONTALLY_V1.2_DUAL_ORIGIN_WORKFLOW_DESIGN.md
-- Frozen: CT-QC-001..005, PE-ROLE-001.
--
-- Change set (additive, data-preserving, idempotent):
--   1. manual_extraction_items.processing_origin   — IMMUTABLE origin
--      ('CARBONTALLY_INTERNAL' | 'PROCESSING_ENTITY'), set when extraction
--      begins and never auto-updated. Distinct from the mutable batch carrier.
--   2. manual_extraction_items.processing_entity_id — the Processing Entity
--      that originated the work (FK RESTRICT), set once with origin.
--   3. manual_extraction_items.pe_reviewed_by/at, pe_qc_by/at — PE stage actor
--      convenience columns (mirrors existing qc_by/qc_at pattern).
--   4. Backfill of existing rows from the current batch carrier. Evidence
--      analysis (2026-09-02): 260 items; 251 internal-carrier, 9 PE-carrier;
--      0 reassignment/mismatch cases requiring audit reconstruction; 0
--      ambiguous; early-QC records keep their historical meaning unchanged.
--   5. staff_roles.permissions 'can_qc' on internal qc_specialist/admin rows
--      (CarbonTally QC capability; PE authority still denied by trust-domain
--      checks require_internal_staff / require_admin).
--   6. No change to emission_factors, processing_entities, batches, review,
--      customer or audit tables.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1+2+3. manual_extraction_items — additive origin / stage-actor columns
-- ---------------------------------------------------------------------------
ALTER TABLE public.manual_extraction_items
    ADD COLUMN IF NOT EXISTS processing_origin VARCHAR
        NOT NULL DEFAULT 'CARBONTALLY_INTERNAL',
    ADD COLUMN IF NOT EXISTS processing_entity_id UUID,
    ADD COLUMN IF NOT EXISTS pe_reviewed_by UUID,
    ADD COLUMN IF NOT EXISTS pe_reviewed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS pe_qc_by UUID,
    ADD COLUMN IF NOT EXISTS pe_qc_at TIMESTAMPTZ;

-- FK (guarded) — originating PE; ON DELETE RESTRICT preserves provenance.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'manual_extraction_items_processing_entity_id_fkey'
    ) THEN
        ALTER TABLE public.manual_extraction_items
            ADD CONSTRAINT manual_extraction_items_processing_entity_id_fkey
            FOREIGN KEY (processing_entity_id)
            REFERENCES public.processing_entities(id)
            ON DELETE RESTRICT;
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 4. Backfill (approved policy): existing rows take origin from the current
--     batch carrier; processing_entity_id set where origin is PROCESSING_ENTITY.
--     Evidence shows 0 ambiguous/reassignment cases on 2026-09-02.
-- ---------------------------------------------------------------------------
UPDATE public.manual_extraction_items AS i
SET processing_origin = 'PROCESSING_ENTITY',
    processing_entity_id = b.entity_id
FROM public.manual_extraction_batches AS b
WHERE b.id = i.batch_id
  AND b.entity_id IS NOT NULL
  AND i.processing_origin = 'CARBONTALLY_INTERNAL';

-- ---------------------------------------------------------------------------
-- Vocabulary CHECK (guarded) — origin is one of the two frozen values and a
-- PROCESSING_ENTITY origin always carries its entity.
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'manual_extraction_items_processing_origin_check'
    ) THEN
        ALTER TABLE public.manual_extraction_items
            ADD CONSTRAINT manual_extraction_items_processing_origin_check
            CHECK (
                processing_origin IN ('CARBONTALLY_INTERNAL', 'PROCESSING_ENTITY')
                AND NOT (processing_origin = 'PROCESSING_ENTITY'
                         AND processing_entity_id IS NULL)
            );
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- Indexes (idempotent)
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_items_processing_origin
    ON public.manual_extraction_items (processing_origin);

CREATE INDEX IF NOT EXISTS idx_items_processing_entity_id
    ON public.manual_extraction_items (processing_entity_id)
    WHERE processing_entity_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 5. CarbonTally QC capability (least-privilege internal role capability;
--     PE staff can never act on it because every CT QC surface enforces the
--     internal trust domain: entity_id IS NULL + require_admin rejects PE).
-- ---------------------------------------------------------------------------
UPDATE public.staff_roles
SET permissions = COALESCE(permissions, '{}'::jsonb) || '{"can_qc": true}'::jsonb
WHERE name IN ('qc_specialist', 'admin')
  AND NOT (COALESCE(permissions, '{}'::jsonb) ? 'can_qc');

-- ---------------------------------------------------------------------------
-- Comments
-- ---------------------------------------------------------------------------
COMMENT ON COLUMN public.manual_extraction_items.processing_origin IS
    'Immutable processing origin (V1.2/CT-QC-004): CARBONTALLY_INTERNAL or '
    'PROCESSING_ENTITY. Set when extraction begins; never auto-updated on '
    'reassignment. Historical audit events remain authoritative.';
COMMENT ON COLUMN public.manual_extraction_items.processing_entity_id IS
    'Processing Entity that ORIGINATED the work (set once with processing_origin '
    '= PROCESSING_ENTITY). Distinct from the mutable batch assignment carrier. '
    'ON DELETE RESTRICT preserves provenance.';
COMMENT ON COLUMN public.manual_extraction_items.pe_reviewed_by IS
    'PE Review actor (PE Reviewer, frozen role).';
COMMENT ON COLUMN public.manual_extraction_items.pe_reviewed_at IS
    'PE Review completion timestamp.';
COMMENT ON COLUMN public.manual_extraction_items.pe_qc_by IS
    'PE QC actor (PE QC Specialist, frozen role).';
COMMENT ON COLUMN public.manual_extraction_items.pe_qc_at IS
    'PE QC completion timestamp.';

