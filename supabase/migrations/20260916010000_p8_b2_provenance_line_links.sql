-- ============================================================================
-- CarbonTally Phase 8 Reporting / Disclosure — B2 (Evidence / Line-Item
-- Addressability) — migration 2 of 2 (B2-2)
-- File: 20260916010000_p8_b2_provenance_line_links.sql
--
-- Purpose (task CT-P8-B2-IMPLEMENTATION-20260913-024; contract §8, §9, §18.1):
--   Add the two provenance links that make a reported result addressable down
--   to the source line:
--     * public.calculation_snapshots.source_line_item_id      (§8.1)
--     * public.disclosure_value_evidence.source_line_item_id  (§9.1)
--   each with a guarded FK to public.evidence_line_items(id) ON DELETE SET NULL
--   and an explicit index for the reverse trace (line → calculations/evidence).
--
-- Governing contract:
--   docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md
-- PO decisions honoured here: B2-D1 (consumer links are non-destructive:
--   SET NULL; only the line's own parent link is RESTRICT) and B2-D12 (no
--   retro-linking — this migration writes no row and backfills no value).
--
-- Scope discipline (B2-2 only):
--   * ADDITIVE on two EXISTING tables: two nullable columns, two guarded FKs,
--     two indexes, comments. NOTHING else.
--   * NO column altered/dropped/renamed, NO row read or written, NO policy,
--     grant or RLS-flag change on either table (contract §16.2 — the clone
--     harness must prove table-level parity).
--   * NO B2-1 object is modified (evidence_line_items is a dependency only).
--   * NO B3 (intensity/projections), NO B4 (narrative/frozen artefacts).
--   * Idempotent: ADD COLUMN IF NOT EXISTS, guarded constraint DO blocks,
--     CREATE INDEX IF NOT EXISTS; re-running this file is a no-op.
--   * Ordering authority is the filename prefix: this file sorts strictly
--     after B1 (20260914/20260915) and after B2-1 (20260916000000).
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. calculation_snapshots.source_line_item_id  (contract §8.1 — normative)
--    Nullable: NULL is the honesty mechanism (flat records, manual entries,
--    pre-B2 history, or a line not yet materialised). B2 never rewrites a
--    historical snapshot (B2-D12 / §13.4).
-- ---------------------------------------------------------------------------
ALTER TABLE public.calculation_snapshots
    ADD COLUMN IF NOT EXISTS source_line_item_id uuid;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'calculation_snapshots_source_line_item_id_fkey'
          AND conrelid = 'public.calculation_snapshots'::regclass
    ) THEN
        ALTER TABLE public.calculation_snapshots
            ADD CONSTRAINT calculation_snapshots_source_line_item_id_fkey
            FOREIGN KEY (source_line_item_id)
            REFERENCES public.evidence_line_items(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_calculation_snapshots_source_line_item
    ON public.calculation_snapshots (source_line_item_id);

COMMENT ON COLUMN public.calculation_snapshots.source_line_item_id IS
    'Phase 8 B2 §8.1 — the addressable source line this immutable snapshot was calculated from (finer than source_item_id; complementary, not an alternative). NULL where no line identity exists or existed at insert time. ON DELETE SET NULL; never re-derived, never retro-linked (B2-D12).';

-- ---------------------------------------------------------------------------
-- 2. disclosure_value_evidence.source_line_item_id  (contract §9.1 — normative;
--    already sanctioned by the ratified B1 contract for B2 to add)
-- ---------------------------------------------------------------------------
ALTER TABLE public.disclosure_value_evidence
    ADD COLUMN IF NOT EXISTS source_line_item_id uuid;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'disclosure_value_evidence_source_line_item_id_fkey'
          AND conrelid = 'public.disclosure_value_evidence'::regclass
    ) THEN
        ALTER TABLE public.disclosure_value_evidence
            ADD CONSTRAINT disclosure_value_evidence_source_line_item_id_fkey
            FOREIGN KEY (source_line_item_id)
            REFERENCES public.evidence_line_items(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_dve_source_line_item
    ON public.disclosure_value_evidence (source_line_item_id);

COMMENT ON COLUMN public.disclosure_value_evidence.source_line_item_id IS
    'Phase 8 B2 §9.1 — the finer, line-level provenance of this evidence row (denormalised from the snapshot, exactly as B1 denormalised source_item_id/source_file_id). Both may be non-NULL; the application-enforced consistency invariant (§8.3) requires dve.source_line_item_id = snapshot.source_line_item_id whenever both the snapshot and the line are known.';

-- ============================================================================
-- VERIFICATION CHECKLIST (B2-2)
--   [ ] exactly two new columns exist, both nullable, on the two named tables
--   [ ] exactly two new FK constraints exist, both ON DELETE SET NULL, named
--       calculation_snapshots_source_line_item_id_fkey /
--       disclosure_value_evidence_source_line_item_id_fkey
--   [ ] exactly two new explicit indexes exist: idx_calculation_snapshots_
--       source_line_item / idx_dve_source_line_item
--   [ ] no column dropped/altered, no row changed, no policy/grant/RLS change
--       on either table
--   [ ] re-running this file is a no-op
-- ============================================================================

COMMIT;
