-- ============================================================================
-- CarbonTally Backend v2.1 — Phase 0, Migration M2 of 8
-- File: 20260807010000_add_emission_factors_import_batch.sql
--
-- Links every emission factor to the import batch that produced it, enabling
-- full provenance: factor → batch → provider → version → source checksum
-- (Backend v2.1 §17 Versioning Strategy; Readiness Review R2).
--
-- Non-destructive, additive column:
--   * Existing rows keep import_batch_id = NULL until a backfill import batch
--     is created (one-off data script, not part of this migration).
--   * The RC2 natural-key unique index
--     (reporting_year, activity_type, COALESCE(country,'GB'),
--      COALESCE(unit,'{no-unit}'), COALESCE(scope,'{no-scope}'))
--     is unaffected.
--
-- Idempotency:
--   * Column: ADD COLUMN IF NOT EXISTS
--   * FK: guarded DO block on pg_constraint (no IF NOT EXISTS for constraints)
--   * Index: CREATE INDEX IF NOT EXISTS
-- ============================================================================

ALTER TABLE public.emission_factors
    ADD COLUMN IF NOT EXISTS import_batch_id UUID;

-- Foreign key is created only if not already present (idempotent re-run).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'emission_factors_import_batch_id_fkey'
    ) THEN
        ALTER TABLE public.emission_factors
            ADD CONSTRAINT emission_factors_import_batch_id_fkey
            FOREIGN KEY (import_batch_id) REFERENCES public.import_batches(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_emission_factors_import_batch
    ON public.emission_factors (import_batch_id);

COMMENT ON COLUMN public.emission_factors.import_batch_id IS
    'Provenance link to the import_batches row that created this factor (Backend v2.1 §17).';

-- ============================================================================
-- VERIFICATION CHECKLIST (M2)
--   [ ] Column import_batch_id exists on emission_factors (nullable UUID)
--   [ ] FK emission_factors_import_batch_id_fkey → import_batches(id)
--       (ON DELETE SET NULL, convalidated)
--   [ ] Index idx_emission_factors_import_batch exists
--   [ ] Existing 7029 rows untouched; import_batch_id = NULL
--   [ ] RC2 natural-key unique index still intact
--   [ ] Re-running this file is a no-op
-- ============================================================================
