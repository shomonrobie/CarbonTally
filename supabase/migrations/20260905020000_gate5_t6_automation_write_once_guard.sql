-- ============================================================================
-- CarbonTally — WS4 Gate 5 (Automated-Extraction Machine Provenance) — T6
-- File: 20260905020000_gate5_t6_automation_write_once_guard.sql
--
-- Accepted design: docs/architecture/CARBONTALLY_WS4_GATE5_DESIGN_READINESS_REPORT.md
--   * §5.1 "Write-once" + §6 optional hardening (task T6): a BEFORE UPDATE guard
--     function/trigger ``dpq_guard_automation_write_once`` on the canonical
--     automated-execution record ``public.document_processing_queue`` that
--     REJECTS changes to non-NULL ``automation_*`` values.
--
-- Invariant (exact write-once semantics):
--   * OLD value NULL        -> NEW value may be set (legitimate FIRST population
--     of a previously NULL field is always allowed; NULL stays NULL if desired).
--   * OLD value non-NULL    -> NEW value identical (IS NOT DISTINCT FROM) is
--     allowed (no-op / idempotent re-write, e.g. the T3 COALESCE path).
--   * OLD value non-NULL    -> NEW value different (including NULL, i.e. an
--     attempted clear) RAISES check_violation — an already-populated automated
--     provenance value can never be overwritten.
--
-- Compatibility:
--   * T3 ``advance_stage`` writes with ``COALESCE(<col>, $n)``, which never
--     produces a non-NULL -> different-value change, so the guard never blocks
--     the accepted persistence path.
--   * Human saves / Gate-6 human-after-automation processing never write these
--     columns; the guard cannot conflict with later human attribution.
--   * Guarded columns are ONLY automation_provider / automation_model /
--     automation_model_version — every other column update is unaffected.
--
-- Data safety:
--   * additive + idempotent (CREATE OR REPLACE FUNCTION; DROP TRIGGER IF EXISTS
--     + CREATE TRIGGER); existing rows untouched; no backfill; no RLS change;
--     Gate-4 columns (calculation_snapshots.performed_by / source_item_id) and
--     all D38/D39/D40 surfaces untouched.
-- ============================================================================

BEGIN;

CREATE OR REPLACE FUNCTION public.dpq_guard_automation_write_once()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.automation_provider IS DISTINCT FROM OLD.automation_provider
       AND OLD.automation_provider IS NOT NULL THEN
        RAISE EXCEPTION
            'document_processing_queue.automation_provider is write-once; '
            'an already-populated value cannot be overwritten'
            USING ERRCODE = 'check_violation';
    END IF;
    IF NEW.automation_model IS DISTINCT FROM OLD.automation_model
       AND OLD.automation_model IS NOT NULL THEN
        RAISE EXCEPTION
            'document_processing_queue.automation_model is write-once; '
            'an already-populated value cannot be overwritten'
            USING ERRCODE = 'check_violation';
    END IF;
    IF NEW.automation_model_version IS DISTINCT FROM OLD.automation_model_version
       AND OLD.automation_model_version IS NOT NULL THEN
        RAISE EXCEPTION
            'document_processing_queue.automation_model_version is write-once; '
            'an already-populated value cannot be overwritten'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.dpq_guard_automation_write_once() IS
    'WS4 Gate 5 (task T6) BEFORE UPDATE write-once guard for the automated '
    'machine-provenance block (automation_provider/automation_model/'
    'automation_model_version) on document_processing_queue. NULL -> value is '
    'always allowed (first population); an already-populated value can never be '
    'changed or cleared (raises check_violation). SECURITY INVOKER; additive and '
    'idempotent; does not affect any other column, RLS, or the Gate-4 human '
    'provenance mechanism.';

DROP TRIGGER IF EXISTS dpq_guard_automation_write_once
    ON public.document_processing_queue;
CREATE TRIGGER dpq_guard_automation_write_once
    BEFORE UPDATE ON public.document_processing_queue
    FOR EACH ROW
    EXECUTE FUNCTION public.dpq_guard_automation_write_once();

COMMIT;
