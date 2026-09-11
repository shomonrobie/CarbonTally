-- ============================================================================
-- CarbonTally Backend v2.1 — Phase 0, Migration M4 of 8
-- File: 20260807030000_add_emissions_logs_snapshot.sql
--
-- Links the operational emissions_logs row to its immutable calculation
-- snapshot (Backend v2.1 §13, Readiness Review R8).
--
-- Relationship (frozen):
--   * emissions_logs      = operational record (dashboards, aggregation).
--   * calculation_snapshots = forensic record (audit, reproducibility).
--   * emissions_logs.snapshot_id → calculation_snapshots.id (nullable;
--     pre-existing rows have no snapshot).
--
-- Non-destructive, additive column. Existing rows unaffected (NULL).
-- Idempotent: guarded column add, guarded FK creation, IF NOT EXISTS index.
-- ============================================================================

ALTER TABLE public.emissions_logs
    ADD COLUMN IF NOT EXISTS snapshot_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'emissions_logs_snapshot_id_fkey'
    ) THEN
        ALTER TABLE public.emissions_logs
            ADD CONSTRAINT emissions_logs_snapshot_id_fkey
            FOREIGN KEY (snapshot_id) REFERENCES public.calculation_snapshots(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_emissions_logs_snapshot
    ON public.emissions_logs (snapshot_id);

COMMENT ON COLUMN public.emissions_logs.snapshot_id IS
    'Optional link to the immutable calculation_snapshots forensic record (Backend v2.1 §13).';

-- ============================================================================
-- VERIFICATION CHECKLIST (M4)
--   [ ] Column snapshot_id exists on emissions_logs (nullable UUID)
--   [ ] FK emissions_logs_snapshot_id_fkey → calculation_snapshots(id)
--       (ON DELETE SET NULL, convalidated)
--   [ ] Index idx_emissions_logs_snapshot exists
--   [ ] Existing emissions_logs rows untouched; snapshot_id = NULL
--   [ ] Existing emissions_logs_unit_fkey (dropped in RC2 002) remains absent
--   [ ] Re-running this file is a no-op
-- ============================================================================
