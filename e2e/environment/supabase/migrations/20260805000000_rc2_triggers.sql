-- ============================================================================
-- CarbonTally v1.0 RC2 — Production Hardening Migration (REPAIR RELEASE)
-- File 006 of 008: updated_at maintenance triggers
-- Source of truth:
--   * Prior: database/rc1/006_rc1_triggers.sql (trigger-naming convention)
--   * Baseline: supabase/migrations/00000000000000_init_schema.sql
--   * CarbonTally_v1.0_Production_Hardening_Plan.md (§7 checklist; plan B §5)
-- Database: PostgreSQL 16 (Supabase). Schema: public. Single transaction.
--
-- BASELINE REALITY (verified): the baseline init creates NO triggers. This file
-- installs one `trg_set_updated_at_<table>` BEFORE UPDATE trigger on every
-- MUTABLE base table that carries an `updated_at` column, invoking the approved
-- SECURITY-INVOKER helper public.set_updated_at() (created in 005).
--
-- DELIBERATE EXCLUSIONS — 6 append-only log tables are IMMUTABLE by design
-- (rows are appended, never updated), so an update-maintenance trigger would
-- bless UPDATEs on rows that must stay frozen for audit continuity:
--   activity_logs, document_activity_log, email_logs,
--   processing_logs, user_activity_log, review_audit_trail
-- (This is the approved v1.0.1 item to DROP updated_at from exactly these; we
-- do not install the inverse maintenance trigger on them now.)
--
-- The trigger set is GENERATED from live catalog state and the exclusion list,
-- so the exact count is whatever the schema yields (verified independently by
-- 007 §7) — it is NOT hard-coded and therefore cannot drift from the schema.
-- Idempotent: every trigger is DROP-then-CREATE under its deterministic name.
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1 — INSTALL updated_at MAINTENANCE TRIGGERS
-- ============================================================================
DO $$
DECLARE
    r record;
    v_excluded text[] := ARRAY[
        'activity_logs','document_activity_log','email_logs',
        'processing_logs','user_activity_log','review_audit_trail'
    ];
BEGIN
    FOR r IN
        SELECT c.table_name
          FROM information_schema.columns c
          JOIN pg_tables t ON t.schemaname = c.table_schema
                          AND t.tablename  = c.table_name
         WHERE c.table_schema = 'public'
           AND c.column_name   = 'updated_at'
           AND c.table_name <> ALL (v_excluded)
         ORDER BY 1
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_set_updated_at_%s ON public.%I',
                       r.table_name, r.table_name);
        EXECUTE format(
            'CREATE TRIGGER trg_set_updated_at_%s
                 BEFORE UPDATE ON public.%I
                 FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()',
            r.table_name, r.table_name);
        RAISE NOTICE 'install updated_at trigger -> public.% (trg_set_updated_at_%)',
            r.table_name, r.table_name;
    END LOOP;
END $$;

-- ============================================================================
-- SECTION 2 — EXPLICITLY NOT IMPLEMENTED (register verification)
-- ============================================================================
--   * The six append-only log tables above: NO update-maintenance trigger (by
--     design). Dropping `updated_at` column from them is the approved DEFERRED
--     v1.0.1 plan-B item; the inverse trigger is intentionally not installed.
--   * No audit/who-changed triggers (updated_by / old_data new_data): audit
--     machinery was REJECTED / DEFERRED in the hardening plan; the audit storey
--     is privilege revocation + PITR, not row-capture triggers.
--   * No soft-delete, no queue-claim, no anonymise triggers: DEFERRED.
--
-- DEPENDENCIES: requires public.set_updated_at() (005). Runs after 005.
--
-- ROLLBACK:
--   DROP TRIGGER IF EXISTS trg_set_updated_at_<table> ON public.<table>;
--   for each table the file installed (or re-run this file is idempotent).
--   set_updated_at() itself is kept for re-install; drop only with 005.
-- ============================================================================

COMMIT;

-- End of 006_rc2_triggers.sql
