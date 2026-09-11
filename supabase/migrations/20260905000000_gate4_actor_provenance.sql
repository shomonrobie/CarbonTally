-- ============================================================================
-- CarbonTally — WS4 Gate 4 remediation F1 — calculation actor attribution
-- File: 20260905000000_gate4_actor_provenance.sql
--
-- Additive + idempotent. The Gate 4 acceptance run proved that
-- ``calculation_snapshots.calculated_by`` stores the *organisation id* (the
-- historical semantic of that column), which cannot identify the actual human /
-- Processing-Entity actor who performed a calculation.
--
-- This migration adds ONE nullable actor column:
--
--   calculation_snapshots.performed_by  uuid -> auth.users(id) ON DELETE SET NULL
--
-- * Purely additive: existing rows keep their historical provenance (NULL
--   performed_by means the row predates actor capture, or was produced by the
--   automatic pipeline — machine provenance remains out of scope);
-- * the immutable snapshot contract is unchanged (append-only; existing columns
--   untouched; ``calculated_by`` still carries the organisation context);
-- * the actor is always the authenticated human user id (CarbonTally internal
--   staff, or Processing-Entity staff). Entity/domain attribution is preserved
--   by the item's ``processing_origin``/``processing_entity_id`` and by the
--   canonical audit events (``ops_calculate:applied`` / ``pe_calculate:applied``
--   with entity context), which reference the same actor.
-- ============================================================================

BEGIN;

ALTER TABLE public.calculation_snapshots
    ADD COLUMN IF NOT EXISTS performed_by uuid;

DO $$
BEGIN
    -- Guard: the FK is created only where the Supabase ``auth`` schema exists
    -- (the authoritative environment). The dedicated integration-test database
    -- is a schema-only mirror without ``auth.users``; the actor column itself is
    -- still added there so engine persistence can be integration-tested.
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'calculation_snapshots_performed_by_fkey'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'auth' AND table_name = 'users'
    ) THEN
        ALTER TABLE public.calculation_snapshots
            ADD CONSTRAINT calculation_snapshots_performed_by_fkey
            FOREIGN KEY (performed_by)
            REFERENCES auth.users(id)
            ON DELETE SET NULL;
    END IF;
END $$;

COMMENT ON COLUMN public.calculation_snapshots.performed_by IS
    'Actual human actor (auth.users id) who performed the calculation (CarbonTally internal staff or Processing-Entity staff). NULL = historical row predating actor capture or automatic-pipeline run. Organisation context remains calculated_by. Gate-4 remediation F1.';

CREATE INDEX IF NOT EXISTS idx_calculation_snapshots_performed_by
    ON public.calculation_snapshots (performed_by);

COMMIT;
