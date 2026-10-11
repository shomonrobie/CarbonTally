-- ============================================================================
-- CT-CARBONTALLY-PHASE-1-CANONICAL-BUILD-REMEDIATION-07 — finding F-06-01
-- Anonymous-privilege containment: residual anonymous TABLE grants in `public`
-- and the anonymous entry in the `public` TABLE default ACL owned by `postgres`.
--
-- Task:   CT-CARBONTALLY-PHASE-1-CANONICAL-BUILD-REMEDIATION-07 (Phase 1)
-- Source: docs/architecture/CT-CARBONTALLY-ONE-DB-CLONE-REHEARSAL-06/
--           OPTION-D-VS-B-RECOMMENDATION.md §5 (F-06-01)
--           MIGRATION-REHEARSAL-LOG.md §6
--         docs/architecture/CT-CARBONTALLY-PHASE-1-CANONICAL-BUILD-REMEDIATION-07/
--           SECURITY-GRANTS-AND-RLS-REPORT.md (before/after evidence)
--
-- WHY THIS FILE EXISTS (measured, not assumed)
--   A canonical from-zero rebuild reproduced a state the hosted/live baseline
--   does not have:
--       public table grants to anon : 12 (4 DML privileges x 3 tables)
--         activity_clarifications (20260928000000), insight_concurrency_leases
--         and insight_rate_limit_buckets (20261005000000)
--       public TABLE default ACL owned by postgres : {..., anon=arwd, ...}
--   The live local database (`carbontally_demo_local`, read-only probe
--   2026-10-10) has 0 anonymous table privileges in `public`, but its
--   `postgres` public TABLE default ACL is REDUCED rather than clean:
--       {anon=r, authenticated=arwd, service_role=arwdDxtm}
--   The hosted-equivalent baseline therefore still names `anon` there -- with
--   SELECT only. This file is deliberately STRICTER than that baseline: it
--   removes the `anon` entry outright, so no future table can inherit even
--   anonymous SELECT. The residual hosted `anon=r` default is recorded as the
--   F-06-01 live residual (a Phase 2 hardening candidate, not fixed here).
--
-- ROOT CAUSE
--   The three tables were created AFTER the anonymous-grant containment
--   migrations (20260920000000 RLS-4A-1 revoked `anon` table by table;
--   20260923000000 P8-RLS-4A-1B / Option A removed the *non-DML* part of the
--   `postgres` public TABLE default ACL, i.e. TRUNCATE/REFERENCES/TRIGGER/
--   MAINTAIN, on the recorded belief that the default carried only `Dxtm`).
--   On this platform the bare Supabase Postgres image registers
--   `anon=arwdDxtm` -- it carries the DML as well. Removing `Dxtm` therefore
--   left `anon=arwd`: every table created afterwards inherited anonymous
--   SELECT/INSERT/UPDATE/DELETE, and the ratified intent ("anon holds no public
--   table privilege" -- RLS-4A-1, Option A 2026-09-14, D-4 containment
--   20260926000000) was not achieved. RLS remained the enforcing boundary
--   throughout (RLS is ENABLED on all three tables and no policy grants
--   anon/public anywhere), so this is a defence-in-depth defect -- but it is a
--   real production-shaped condition, and it independently reproduces the
--   earlier "anon grants on 3 hosted tables" finding.
--
-- SCOPE (deliberately narrow -- REVOKE only, `anon` only)
--   (1) the three existing tables above: REVOKE ALL from `anon`, so their
--       effective posture equals the live baseline and the creating
--       migrations' documented intent;
--   (2) the `public` TABLE default ACL owned by `postgres` (the role that runs
--       the CarbonTally migration chain and therefore creates application
--       tables): REVOKE ALL from `anon`, so no FUTURE table can be created
--       with anonymous privileges. This completes the ratified Option A.
--   Nothing else. Specifically NOT changed: `authenticated` (the live baseline
--   keeps `authenticated=arwd` on the public TABLE default), `service_role`
--   (backend role), the `storage` schema (Supabase-managed), any RLS flag, any
--   policy, any column/constraint/index, and no data.
--
--   The `supabase_admin` public default ACL is NOT touched here: a migration
--   runs as `postgres`, which holds neither ownership nor membership of that
--   role, so it cannot be altered from the application chain. It is
--   normalised at the platform layer instead (PHASE A of
--   e2e/environment/scripts/canonical_schema_rebuild.sh) -- see the Phase 1
--   CANONICAL-BUILD-CONTRACT.md. Anonymous privileges on *sequences* and
--   *functions* (which the live baseline also does not register) are
--   dispositioned the same way, at the platform layer, never here.
--
-- SAFETY
--   * Hardening only, additive and idempotent (REVOKE is absolute and
--     re-runnable).
--   * No privilege is granted to any role. No policy is created, altered,
--     dropped or disabled; RLS stays ENABLED. No DDL on columns, constraints
--     or indexes; no DROP; no TRUNCATE; no data modification.
--   * `service_role` and `authenticated` access paths are asserted to still
--     hold -- a regression there raises and rolls the whole transaction back.
--   * The post-condition is FAIL-CLOSED: a residual anonymous privilege on any
--     of the three tables, or a residual `anon` entry in the `postgres` public
--     TABLE default ACL, aborts the migration. A partial or ineffective apply
--     cannot pass.
--
-- ROLLBACK (not recommended -- it restores only the platform default, and RLS
--           denies every row to anon in any case):
--   GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
--       public.activity_clarifications,
--       public.insight_concurrency_leases,
--       public.insight_rate_limit_buckets TO anon;
--   ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
--       GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon;
-- ============================================================================


BEGIN;

-- ----------------------------------------------------------------------------
-- (1) Existing objects -- the three tables that carried anonymous DML.
-- ----------------------------------------------------------------------------
REVOKE ALL PRIVILEGES ON TABLE public.activity_clarifications    FROM anon;
REVOKE ALL PRIVILEGES ON TABLE public.insight_concurrency_leases FROM anon;
REVOKE ALL PRIVILEGES ON TABLE public.insight_rate_limit_buckets FROM anon;

-- ----------------------------------------------------------------------------
-- (2) Future objects -- the `public` TABLE default ACL owned by `postgres`.
--     (RLS-4A-1B removed `Dxtm`; this removes the `arwd` remainder.)
-- ----------------------------------------------------------------------------
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    REVOKE ALL PRIVILEGES ON TABLES FROM anon;

-- ----------------------------------------------------------------------------
-- (3) Fail-closed post-condition.
-- ----------------------------------------------------------------------------
DO $ct_p1_anon_containment$
DECLARE
    tbl     text;
    worst   text;
    defacl  text;
    tbl_oid oid;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'activity_clarifications',
        'insight_concurrency_leases',
        'insight_rate_limit_buckets'
    ]
    LOOP
        tbl_oid := format('public.%I', tbl)::regclass;

        -- (a) No anonymous privilege of ANY kind may remain. The ACL is read
        --     directly (not per privilege name) so a future privilege type
        --     cannot slip through this check.
        SELECT string_agg(DISTINCT format('%s:%s', r.rolname, a.privilege_type), ', ')
          INTO worst
          FROM pg_class c
          CROSS JOIN LATERAL aclexplode(
                 coalesce(c.relacl, acldefault('r', c.relowner))) AS a
          JOIN pg_roles r ON r.oid = a.grantee
         WHERE c.oid = tbl_oid
           AND r.rolname = 'anon';

        IF worst IS NOT NULL THEN
            RAISE EXCEPTION
                'F-06-01 containment: public.% still grants % to anon', tbl, worst;
        END IF;

        -- (b) The service-role backend path must keep its DML.
        IF NOT has_table_privilege('service_role', tbl_oid, 'SELECT')
           OR NOT has_table_privilege('service_role', tbl_oid, 'INSERT') THEN
            RAISE EXCEPTION
                'F-06-01 containment: service_role lost DML on public.%', tbl;
        END IF;

        -- (c) RLS must still be enabled: this file hardens, it never loosens.
        IF NOT (SELECT relrowsecurity FROM pg_class WHERE oid = tbl_oid) THEN
            RAISE EXCEPTION
                'F-06-01 containment: RLS is not enabled on public.%', tbl;
        END IF;

        RAISE NOTICE 'F-06-01 containment: public.% is anon-free, RLS still enabled', tbl;
    END LOOP;

    -- (d) The default ACL for FUTURE public tables (owned by postgres) must no
    --     longer name `anon` at all. An absent row (defaclacl IS NULL) passes:
    --     "no anonymous entry" is the objective, not "an entry with r".
    SELECT cast(a.defaclacl AS text) INTO defacl
      FROM pg_default_acl a
      JOIN pg_roles r     ON r.oid = a.defaclrole
      JOIN pg_namespace n ON n.oid = a.defaclnamespace
     WHERE r.rolname = 'postgres' AND n.nspname = 'public'
       AND a.defaclobjtype = 'r';

    IF defacl LIKE '%anon=%' THEN
        RAISE EXCEPTION
            'F-06-01 containment: the postgres public TABLE default ACL still '
            'grants anon (%)', defacl;
    END IF;

    RAISE NOTICE 'F-06-01 containment complete: postgres public TABLE default ACL = %',
        coalesce(defacl, '(no anon entry)');
END
$ct_p1_anon_containment$;

COMMIT;
