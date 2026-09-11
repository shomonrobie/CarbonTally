-- ============================================================================
-- CarbonTally — WS4 Gate 6 (Human-After-Automation Attribution) — Workstream W1
-- File: 20260906010000_gate6_w1_automation_extracted_output.sql
--
-- Accepted readiness: docs/architecture/CARBONTALLY_WS4_GATE6_READINESS_REPORT.md
--   * gap G6-A — "No immutable/independent copy of the machine-extracted output
--     payload currently survives when the output is subsequently modified by a
--     human."
--   * proposal §12 G6-W1 option (a) — an additive, write-once JSONB column on
--     the canonical automated-execution record
--     ``public.document_processing_queue`` mirroring the accepted Gate-5 T1/T6
--     schema pattern.
--
-- Semantics (truthful provenance):
--   * automation_extracted_data — the ORIGINAL output produced by the automatic
--     extraction pipeline (deterministic AND AI-contributing runs) at the first
--     extraction->mapping advance that persisted ``extracted_data``. It is an
--     independent, write-once copy of the machine output that survives later
--     human correction of the working ``extracted_data`` (original-vs-current
--     separation). NULL = the automatic pipeline never durably produced an
--     extraction output (failed/blocked extraction attempt) or a legacy row
--     predating this column — NEVER fabricated/backfilled.
--   * The Gate-5 automation_provider/model/version block is NOT changed by this
--     migration; it remains AI-contribution-specific and write-once. A
--     deterministic-only run therefore has automation_extracted_data populated
--     (the pipeline produced machine output) while the automation_* block stays
--     NULL (no AI contributed) — the two records stay truthful and
--     distinguishable.
--
-- Write-once enforcement: a dedicated BEFORE UPDATE guard
--   (dpq_guard_automation_extracted_data_write_once) rejects overwriting or
--   clearing a populated value while always allowing the first (NULL->value)
--   population and identical no-op rewrites. The accepted Gate-5 trigger
--   (dpq_guard_automation_write_once) is deliberately NOT modified.
--
-- Data safety:
--   * purely additive + idempotent (ADD COLUMN IF NOT EXISTS; CREATE OR REPLACE
--     FUNCTION; DROP TRIGGER IF EXISTS + CREATE TRIGGER) — reapplying this file
--     is a no-op;
--   * existing rows untouched (new column NULL for every legacy row); no
--     backfill; no index; no constraint on existing data; no new table;
--   * no RLS change (the existing 4 org-scoped DPQ policies are untouched);
--   * Gate-4 columns (calculation_snapshots.performed_by / source_item_id) and
--     all D38/D39/D40 surfaces untouched.
-- ============================================================================

BEGIN;

ALTER TABLE public.document_processing_queue
    ADD COLUMN IF NOT EXISTS automation_extracted_data jsonb;

COMMENT ON COLUMN public.document_processing_queue.automation_extracted_data IS
    'Original automated-extraction output preserved independently of later '
    'human edits (WS4 Gate 6, workstream W1 / gap G6-A). Write-once JSONB copy '
    'of the machine-produced extraction output persisted by the automatic '
    'pipeline at the first extraction->mapping advance; deterministic-only and '
    'AI-contributing runs are both eligible (the automation_provider/model/'
    'version block above stays AI-contribution-specific). NULL = the pipeline '
    'never durably produced an extraction output (failed/blocked attempt) or a '
    'legacy row predating this column - never fabricated/backfilled. Human '
    'saves never write this column; it cannot be overwritten or cleared once '
    'populated. Not an authorization input.';

CREATE OR REPLACE FUNCTION public.dpq_guard_automation_extracted_data_write_once()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.automation_extracted_data IS DISTINCT FROM OLD.automation_extracted_data
       AND OLD.automation_extracted_data IS NOT NULL THEN
        RAISE EXCEPTION
            'document_processing_queue.automation_extracted_data is write-once; '
            'an already-populated value cannot be overwritten or cleared'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.dpq_guard_automation_extracted_data_write_once() IS
    'WS4 Gate 6 (workstream W1) BEFORE UPDATE write-once guard for the preserved '
    'original automated extraction output (automation_extracted_data) on '
    'document_processing_queue. NULL -> value is always allowed (first '
    'population); an already-populated value can never be changed or cleared '
    '(raises check_violation). SECURITY INVOKER; additive and idempotent; does '
    'not modify the accepted Gate-5 trigger (dpq_guard_automation_write_once), '
    'any other column, RLS, or the Gate-4 human provenance mechanism.';

DROP TRIGGER IF EXISTS dpq_guard_automation_extracted_data_write_once
    ON public.document_processing_queue;
CREATE TRIGGER dpq_guard_automation_extracted_data_write_once
    BEFORE UPDATE ON public.document_processing_queue
    FOR EACH ROW
    EXECUTE FUNCTION public.dpq_guard_automation_extracted_data_write_once();

COMMIT;
