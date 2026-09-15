-- ============================================================================
-- CarbonTally Phase 8 — Separate Workstream RLS — RLS-4A-1
-- File: 20260920000000_p8_rls_anon_grant_containment.sql
--
-- PO DECISION D-1 APPROVED (Option B, 2026-09-14): authorise anonymous-grant
-- containment (RLS-4A-1) as an independent hardening step.
--
-- AUTHORITATIVE DEFINITION (RLS hold register §6.1):
--   Scope:        revoke `anon` table privileges across the `public` schema.
--   Operations:   REVOKE only. No ENABLE, no policy change, no grant to any other role.
--   Rationale:    closes the anonymous surface without any RLS change.
--
-- EXPLICIT EXCLUSION — `emission_factors` is NOT touched:
--   whether public/anonymous access to `emission_factors` is a product requirement is
--   the *unratified* decision D-4. Revoking it here would silently answer a product
--   question. It is left exactly as found and carried to the D-4 gate.
--
-- CONFIRMATIONS RECORDED ELSEWHERE:
--   D-11: FORCE ROW LEVEL SECURITY remains DEFERRED — this migration does not set it.
--   D-13: the governed sequence retains RLS-4; F-5/F-6 stay assigned to RLS-4A-1/4A-2.
--
-- SCOPE DISCIPLINE: additive/idempotent hardening only. It does NOT change any RLS
-- flag, any policy, or any `authenticated`/service-role privilege, and it touches no
-- data. Production is prohibited (G0-D): QA / non-production application only.
-- ============================================================================

BEGIN;

DO $$
DECLARE
    r            record;
    grants_before int;
    grants_after  int;
    tables_done   int := 0;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        RAISE EXCEPTION 'RLS-4A-1 precondition failed: role anon is absent';
    END IF;

    SELECT count(*) INTO grants_before
    FROM information_schema.role_table_grants g
    JOIN pg_class c ON c.relname = g.table_name
    JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
    WHERE g.grantee = 'anon' AND g.table_schema = 'public';

    FOR r IN
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind IN ('r', 'p')
          AND c.relname <> 'emission_factors'   -- D-4 (unratified) is NOT pre-empted
          AND EXISTS (
              SELECT 1 FROM information_schema.role_table_grants g
              WHERE g.grantee = 'anon' AND g.table_schema = 'public'
                AND g.table_name = c.relname
          )
        ORDER BY c.relname
    LOOP
        EXECUTE format('REVOKE ALL ON TABLE public.%I FROM anon', r.relname);
        tables_done := tables_done + 1;
    END LOOP;

    SELECT count(*) INTO grants_after
    FROM information_schema.role_table_grants g
    JOIN pg_class c ON c.relname = g.table_name
    JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
    WHERE g.grantee = 'anon' AND g.table_schema = 'public';

    RAISE NOTICE 'RLS-4A-1: public tables processed=%, anon grants before=%, after=% (emission_factors intentionally excluded pending D-4)',
        tables_done, grants_before, grants_after;
END $$;

COMMIT;
