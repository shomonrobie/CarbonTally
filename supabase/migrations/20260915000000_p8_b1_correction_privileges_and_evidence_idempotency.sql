-- ============================================================================
-- CarbonTally Phase 8 Reporting — B1 CORRECTION (additive)
-- File: 20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql
--
-- Purpose (task CT-P8-B1-CORRECTION-20260912-015): correct the two defects that
-- gate V1 confirmed against the B1 Deliverable and that require a DATABASE
-- change. The application-layer defects F1/F2/F3(app) and F5 are corrected in
-- backend/data/disclosure.py; this migration carries the schema-side corrections.
--
--   F4 (V1, P2) — NEW B1 TABLE PRIVILEGES.
--       The B1 migration did not apply the repository's ratified new-table
--       privilege pattern (20260807070000_add_new_table_rls.sql onward):
--         * service_role received no usable access (only the environment's
--           default Dxtm), so a service-role writer could not read or write any
--           B1 table although contract §13/§23 name the service role as the
--           write/platform owner;
--         * authenticated kept TRUNCATE / TRIGGER / REFERENCES / MAINTAIN,
--           which the local Supabase default ACL grants to new tables and which
--           the established pattern explicitly REVOKEs — TRUNCATE is NOT gated
--           by Row Level Security.
--
--   F3 (V1, P2, database half) — NULL-SAFE EVIDENCE-LINK UNIQUENESS.
--       UNIQUE (disclosure_value_id, calculation_snapshot_id) cannot prevent a
--       duplicate row when calculation_snapshot_id IS NULL (NULLs are distinct),
--       so contract §25 "re-linking = no duplicates" was not deliverable at the
--       database level. This migration adds a NULL-safe unique index over the
--       evidence REFERENCE so the guarantee is real for both the calculated and
--       the manual/CUSTOMER_INPUT paths. The application layer is corrected in
--       the same task (explicit re-link-as-update); the index is the backstop.
--
-- Scope discipline (B1 correction only):
--   * Touches ONLY the 11 new public.disclosure_* tables and their grants/indexes.
--   * Modifies ZERO existing tables, columns, policies or other tables' grants.
--   * Does NOT perform the wider RLS remediation / production RLS baseline work.
--   * Introduces NO permissive write policy, NO USING (true) write policy, and
--     does NOT weaken RLS (no policy is dropped or disabled here).
--   * NO B2 (evidence_line_items / source_line_item_id), NO B3 (intensity),
--     NO B4 (narrative/finalisation).
--   * Does NOT modify supabase/migrations/20260914000000_p8_b1_* (the B1 file
--     stays byte-identical; corrections are additive, per task §15).
--
-- Idempotent: GRANT/REVOKE re-application is a no-op; the index uses
-- IF NOT EXISTS; re-running this file is safe.
-- ============================================================================

-- ============================================================================
-- F4. B1 table privileges — mirror the repository's established pattern
--     service_role : ALL (the platform write owner, contract §13/§23)
--     authenticated: unchanged DML posture from B1, MINUS TRUNCATE / TRIGGER /
--                    REFERENCES / MAINTAIN (TRUNCATE is not RLS-gated)
--     anon         : already holds NO privilege on these tables (the B1
--                    migration revoked ALL from anon); unchanged here.
-- ============================================================================

GRANT ALL ON TABLE public.disclosure_frameworks TO service_role;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_frameworks FROM authenticated;

GRANT ALL ON TABLE public.disclosure_framework_versions TO service_role;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_framework_versions FROM authenticated;

GRANT ALL ON TABLE public.disclosure_requirement_versions TO service_role;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_requirement_versions FROM authenticated;

GRANT ALL ON TABLE public.disclosure_requirement_mappings TO service_role;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_requirement_mappings FROM authenticated;

GRANT ALL ON TABLE public.disclosure_report_purposes TO service_role;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_report_purposes FROM authenticated;

GRANT ALL ON TABLE public.disclosure_report_purpose_versions TO service_role;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_report_purpose_versions FROM authenticated;

GRANT ALL ON TABLE public.disclosure_purpose_requirements TO service_role;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_purpose_requirements FROM authenticated;

GRANT ALL ON TABLE public.disclosure_applicability_assessments TO service_role;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_applicability_assessments FROM authenticated;

GRANT ALL ON TABLE public.disclosure_report_instance_binding TO service_role;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_report_instance_binding FROM authenticated;

GRANT ALL ON TABLE public.disclosure_values TO service_role;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_values FROM authenticated;

GRANT ALL ON TABLE public.disclosure_value_evidence TO service_role;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.disclosure_value_evidence FROM authenticated;

-- ============================================================================
-- F3 (database half). NULL-safe unique index on the evidence reference.
--
-- Existing constraint (B1, unchanged): UNIQUE (disclosure_value_id,
-- calculation_snapshot_id). PostgreSQL treats NULLs as distinct, so two rows with
-- the same (value, NULL snapshot) and the same evidence references were allowed
-- (V1 F3). The index below closes that gap by indexing the COALESCEd reference.
--
-- The zero UUID is the codebase's established machine/"no value" marker
-- (data/audit.py ``_SYSTEM_UUID``, data/documents.py, tests/integration/conftest
-- ``_SYSTEM_UUID``); it can never be a real calculation_snapshots/emissions_logs/
-- manual_extraction_items/organization_files id, so it is a safe sentinel and no
-- legitimate reference can collide with it.
--
-- Effect: at most ONE evidence row per (value, snapshot, emissions_log,
-- source_item, source_file) reference. Distinct references remain independently
-- representable (they differ in at least one indexed column); the pre-existing
-- non-NULL uniqueness is unchanged and additionally implied here.
--
-- Additive only: no column, constraint or row is altered or deleted, and no
-- evidence_line_items / source_line_item_id (B2) is introduced.
--
-- DEPLOYMENT PRECONDITION (documented; deliberately NOT auto-remediated): if the
-- index is created on a database where the PRE-CORRECTION code already produced
-- duplicate NULL-snapshot links, CREATE UNIQUE INDEX fails LOUDLY (never
-- silently). That is intended: this migration does not delete evidence rows, and
-- "fail loudly" is exactly what proves the index detects the defect. B1 has never
-- been deployed (no environment holds disclosure rows), so the index creates
-- cleanly everywhere real. If residue ever exists, an operator must first run an
-- explicitly authorised dedupe, for example:
--
--   DELETE FROM public.disclosure_value_evidence d
--    USING public.disclosure_value_evidence k
--    WHERE d.ctid < k.ctid
--      AND d.disclosure_value_id = k.disclosure_value_id
--      AND d.calculation_snapshot_id IS NOT DISTINCT FROM k.calculation_snapshot_id
--      AND d.emissions_log_id       IS NOT DISTINCT FROM k.emissions_log_id
--      AND d.source_item_id         IS NOT DISTINCT FROM k.source_item_id
--      AND d.source_file_id         IS NOT DISTINCT FROM k.source_file_id;
-- ============================================================================
CREATE UNIQUE INDEX IF NOT EXISTS uq_dve_reference_nullsafe
    ON public.disclosure_value_evidence (
        disclosure_value_id,
        (COALESCE(calculation_snapshot_id, '00000000-0000-0000-0000-000000000000'::uuid)),
        (COALESCE(emissions_log_id,       '00000000-0000-0000-0000-000000000000'::uuid)),
        (COALESCE(source_item_id,         '00000000-0000-0000-0000-000000000000'::uuid)),
        (COALESCE(source_file_id,         '00000000-0000-0000-0000-000000000000'::uuid))
    );

COMMENT ON INDEX public.uq_dve_reference_nullsafe IS
    'B1 correction (CT-P8-B1-CORRECTION-20260912-015): NULL-safe duplicate-link prevention on disclosure_value_evidence. Completes contract §25 "re-linking = no duplicates" for NULL calculation_snapshot_id (manual/CUSTOMER_INPUT evidence).';

-- ============================================================================
-- VERIFICATION CHECKLIST (correction migration)
--   [ ] service_role has ALL (SELECT/INSERT/UPDATE/DELETE/TRUNCATE/… at least
--       SELECT+INSERT+UPDATE+DELETE) on all 11 B1 tables
--   [ ] authenticated has NO TRUNCATE / TRIGGER / REFERENCES / MAINTAIN on any
--       of the 11 B1 tables
--   [ ] authenticated DML posture unchanged from B1:
--       - SELECT only on the 7 catalogue tables + disclosure_values +
--         disclosure_value_evidence
--       - SELECT/INSERT/UPDATE/DELETE on disclosure_applicability_assessments
--         and disclosure_report_instance_binding
--   [ ] anon still holds NO privilege on any of the 11 B1 tables
--   [ ] uq_dve_reference_nullsafe exists (partial/expression unique index)
--   [ ] no existing table's grant or policy was modified
--   [ ] exactly 11 disclosure_* tables still exist (no new table)
--   [ ] re-running this file is a no-op
-- ============================================================================
