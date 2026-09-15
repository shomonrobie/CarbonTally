-- ============================================================================
-- CarbonTally Phase 8 — Separate Workstream RLS — RLS-4A-2
-- File: 20260922000000_p8_rls_4a2_authenticated_grant_hardening.sql
--
-- PO DECISION (2026-09-14, decision 6) AUTHORISED:
--   "Authorise the bounded security remediation to revoke unnecessary blanket
--    TRUNCATE-class privileges from signed-in application users [= role
--    `authenticated`], subject to the existing RLS/security contract and
--    independent verification. Do not expand this into the unresolved RLS
--    steps 3–5."
--
-- AUTHORITATIVE DEFINITION (RLS hold register §6.1, RLS-4A-2):
--   Scope:      reduce `authenticated` from `ALL` to
--               `SELECT, INSERT, UPDATE, DELETE` — i.e. drop the non-DML
--               blanket privileges `TRUNCATE` / `REFERENCES` / `TRIGGER`.
--   Operations: REVOKE only. No ENABLE, no policy change, no grant to any role.
--
-- TWO IMPLEMENTATION FACTS THAT SHAPE THIS FILE (both verified live, PG 17.6):
--
--   1. `MAINTAIN` — PostgreSQL 17 added the `MAINTAIN` table privilege
--      (VACUUM/ANALYZE/REINDEX/CLUSTER/REFRESH). `authenticated` holds it on the
--      same 119 relations. The register was written before MAINTAIN existed, so
--      its stated target posture ("exactly SELECT,INSERT,UPDATE,DELETE") cannot
--      be reached on this server without revoking MAINTAIN too. MAINTAIN is the
--      same class of non-DML blanket privilege, so revoking it **completes** the
--      ratified target rather than expanding it. It is called out here so the PO
--      can veto it if that reading is unwanted.
--
--   2. DEFAULT PRIVILEGES — `public` carries a default ACL registered by role
--      `postgres` that grants `Dxtm` (TRUNCATE, REFERENCES, TRIGGER, MAINTAIN)
--      to `authenticated` on every **future** table:
--        postgres | ns=public | r | {postgres=arwdDxtm, anon=Dxtm,
--                                     authenticated=Dxtm, service_role=Dxtm}
--      A table-level REVOKE alone would therefore be silently undone by the next
--      `CREATE TABLE`. The matching default-privilege REVOKE is included so the
--      hardening is durable. It is still REVOKE-only and touches the same
--      privilege class for the same single role.
--
-- EXPLICITLY NOT TOUCHED (scope discipline):
--   * role `anon` — belongs to RLS-4A-1 and the unratified product decision D-4
--     (`emission_factors`). NOTE for the record: the same default ACL also grants
--     `anon` `Dxtm` on new tables, so RLS-4A-1's table-level revocation is
--     likewise non-durable. That is reported as an observation, NOT fixed here.
--   * role `service_role` — required by the backend.
--   * RLS flags, RLS policies, columns, constraints, indexes, functions, data.
--   * `emission_factors` — no product question is pre-empted.
--
-- ENVIRONMENT: QA / non-production only (`carbontally_qa_phase8`, PO-named
-- 2026-09-14). Production is PROHIBITED (G0-D open) and is not touched.
--
-- IDEMPOTENT: re-running finds no remaining privileges to revoke and is a no-op.
-- ============================================================================

BEGIN;

DO $$
DECLARE
    -- Non-DML blanket privileges to remove from `authenticated`.
    privs        text[] := ARRAY['TRUNCATE', 'REFERENCES', 'TRIGGER'];
    priv_list    text;
    r            record;
    tables_done  int := 0;
    before_count int;
    after_count  int;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        RAISE EXCEPTION 'RLS-4A-2 precondition failed: role authenticated is absent';
    END IF;

    -- PostgreSQL 17+: MAINTAIN is part of the same non-DML class (see header).
    IF current_setting('server_version_num')::int >= 170000 THEN
        privs := array_append(privs, 'MAINTAIN');
    END IF;
    priv_list := array_to_string(privs, ', ');

    -- Measurement helper: relations where `authenticated` holds any target priv.
    SELECT count(*) INTO before_count
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relkind IN ('r', 'p')
      AND EXISTS (SELECT 1 FROM unnest(privs) AS p
                  WHERE has_table_privilege('authenticated', c.oid, p));

    FOR r IN
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind IN ('r', 'p')
          AND EXISTS (SELECT 1 FROM unnest(privs) AS p
                      WHERE has_table_privilege('authenticated', c.oid, p))
        ORDER BY c.relname
    LOOP
        EXECUTE format('REVOKE %s ON TABLE public.%I FROM authenticated',
                       priv_list, r.relname);
        tables_done := tables_done + 1;
    END LOOP;

    -- Durability: stop future `public` tables from re-acquiring the same class.
    EXECUTE format(
        'ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public '
        'REVOKE %s ON TABLES FROM authenticated',
        priv_list
    );

    SELECT count(*) INTO after_count
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relkind IN ('r', 'p')
      AND EXISTS (SELECT 1 FROM unnest(privs) AS p
                  WHERE has_table_privilege('authenticated', c.oid, p));

    RAISE NOTICE 'RLS-4A-2: tables processed=%, authenticated non-DML relations before=%, after=% (privs=%)',
        tables_done, before_count, after_count, priv_list;
END $$;

COMMIT;
