-- ============================================================================
-- CarbonTally Phase 8 — D-4 (ratified): `emission_factors` is INTERNAL /
-- server-side reference data and must NOT be client-accessible.
-- File: 20260926000000_p8_d4_emission_factors_internal_containment.sql
--
-- PO DECISION (P8-FINALIZATION-IMPLEMENT-001, D-4 APPROVED):
--   `emission_factors` is internal/server-side data. It must not be anonymously
--   accessible, and no ordinary customer browser surface may receive access.
--   "Apply the minimum necessary security hardening and regression coverage."
--
-- EVIDENCE FOR THE RULING (recorded, reproducible):
--   * zero client-side references exist (`grep -rn 'emission_factors'
--     frontend/src admin/src` -> no matches);
--   * every consumer is server-side (repository/engines/reporting/admin plane)
--     through the service role, which BYPASSES RLS, so removal of the client
--     privileges cannot break factor matching, import, calculation or reporting;
--   * `emission_factors` is the ONLY table still carrying `anon` grants, having
--     been deliberately excluded from RLS-4A-1 (20260920000000), RLS-4A-2
--     (20260922000000) and RLS-4B (20260925000000) pending this very decision.
--
-- OPERATION — REVOKE ONLY, on ONE table:
--   REVOKE ALL ON TABLE public.emission_factors FROM anon;
--   REVOKE ALL ON TABLE public.emission_factors FROM authenticated;
--
-- EXPLICIT NON-SCOPE (unchanged by this file):
--   * no RLS flag change (RLS is already ENABLED on this table by
--     `00000000000000_init_schema.sql` "RLS ENABLEMENT (All tables)");
--   * no policy created, dropped or altered (the table keeps ZERO policies, i.e.
--     fail-closed for every RLS-bound role);
--   * no GRANT to any role; `service_role` is untouched (the backend needs it);
--   * no data, column, constraint, index, function or trigger change;
--   * no other table touched — `storage` and every tenant table are out of scope;
--   * default privileges for FUTURE tables are already hardened by
--     20260922000000 (authenticated) and 20260923000000 (anon).
--
-- IDEMPOTENT: re-running finds nothing left to revoke (rc=0, no-op notices).
-- ENVIRONMENT: additive, non-destructive; QA/clone application is authorised.
-- Production remains a TERMINAL PO AUTHORIZATION GATE (D-17) — this file does
-- not authorise or perform any production migration or deployment.
-- ============================================================================

BEGIN;

DO $$
DECLARE
    target_table text := 'public.emission_factors';
    before_anon   int;
    before_auth   int;
    after_anon    int;
    after_auth    int;
BEGIN
    IF to_regclass(target_table) IS NULL THEN
        RAISE EXCEPTION 'D-4 precondition failed: % is absent', target_table;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        RAISE EXCEPTION 'D-4 precondition failed: role anon is absent';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        RAISE EXCEPTION 'D-4 precondition failed: role authenticated is absent';
    END IF;

    SELECT count(*) INTO before_anon
      FROM information_schema.role_table_grants g
     WHERE g.grantee = 'anon' AND g.table_schema = 'public'
       AND g.table_name = 'emission_factors';
    SELECT count(*) INTO before_auth
      FROM information_schema.role_table_grants g
     WHERE g.grantee = 'authenticated' AND g.table_schema = 'public'
       AND g.table_name = 'emission_factors';

    -- Literal (not format-built) statements so the revoked roles/objects are
    -- statically auditable in the migration text itself.
    REVOKE ALL ON TABLE public.emission_factors FROM anon;
    REVOKE ALL ON TABLE public.emission_factors FROM authenticated;

    SELECT count(*) INTO after_anon
      FROM information_schema.role_table_grants g
     WHERE g.grantee = 'anon' AND g.table_schema = 'public'
       AND g.table_name = 'emission_factors';
    SELECT count(*) INTO after_auth
      FROM information_schema.role_table_grants g
     WHERE g.grantee = 'authenticated' AND g.table_schema = 'public'
       AND g.table_name = 'emission_factors';

    IF after_anon <> 0 OR after_auth <> 0 THEN
        RAISE EXCEPTION
            'D-4 containment failed: residual grants remain (anon=%, authenticated=%)',
            after_anon, after_auth;
    END IF;

    RAISE NOTICE
        'D-4: emission_factors client privileges contained — anon % -> %, authenticated % -> % (service_role untouched; RLS/policies unchanged)',
        before_anon, after_anon, before_auth, after_auth;
END $$;

COMMIT;

-- ============================================================================
-- VERIFICATION (expected after application; see the D-4 regression tests):
--   has_table_privilege('anon','public.emission_factors','SELECT')           = false
--   has_table_privilege('anon','public.emission_factors','TRUNCATE')         = false
--   has_table_privilege('authenticated','public.emission_factors','SELECT')  = false
--   has_table_privilege('authenticated','public.emission_factors','INSERT')  = false
--   `service_role` privileges are NOT modified by this migration (this file
--     contains no statement naming that role); whatever it held before is held
--     after. Measured in the disposable rehearsal clone, `service_role` held no
--     privilege on this table before OR after — a pre-existing environment
--     condition recorded as an observation, not a regression. The backend's SQL
--     path connects as the table owner (`postgres`), which is unaffected.
--   relrowsecurity                     = true   (unchanged)
--   count(policies on emission_factors) = 0     (unchanged)
-- ============================================================================
