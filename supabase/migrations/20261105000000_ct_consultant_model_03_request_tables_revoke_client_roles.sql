-- ============================================================================
-- CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — CLOSURE (finding F-1)
-- Client-role privilege revocation on the two CT03 request tables.
--
-- Task:   CT-CARBONTALLY-LIVE-SUPABASE-UPDATE-01 closure
-- Finding: docs/architecture/CT-CARBONTALLY-LIVE-SUPABASE-UPDATE-01.md §9 (F-1)
-- Source: docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md
--           §4    PO-1   mode-change REQUEST (CarbonTally decides)
--           §14.1 OQ-1/OQ-3 + PO-7  relationship change/end REQUEST
--           §19   OQ-2   retention (relationship records are retained evidence)
--
-- WHY THIS FILE EXISTS
--   20261103000000_ct_consultant_model_03_client_access_and_mode.sql created
--   public.consultant_relationship_requests and
--   public.consultant_mode_change_requests and documented them (§SAFETY) as
--   "RLS-enabled with NO policies (deny-by-default, service-role API only)",
--   but it did NOT revoke the client roles' table privileges. Measured on the
--   live project (2026-10-09):
--       anon = arwd | authenticated = arwd | service_role = arwdDxtm
--   Client-role access was therefore denied only by RLS evaluation, not by
--   privilege. The two immediately preceding migrations of the same delta DO
--   revoke, and measure anon = (none) / authenticated = (none):
--       20261030000000_manual_processing_routing.sql:118-121
--           (manual_processing_processors)
--       20261101000000_ct_mp_sub_003_consultant_coverage.sql:127-128
--           (consultant_mp_allocations)
--   This file brings the two CT03 tables to that same, already-established
--   posture — it invents no new convention.
--
--   Access path verified before revoking (2026-10-09): the ONLY consumers of both
--   tables are the backend service path —
--       backend/data/consultants.py    (direct SQL via the backend pool)
--       backend/api/v3_consultants.py  (the endpoints that create/decide requests)
--   No frontend/, admin/ or supabase-js code reads or writes either table, so no
--   client-role (anon/authenticated) PostgREST path exists that could regress.
--
-- ROOT CAUSE (recorded here, deliberately NOT changed)
--   Supabase's platform default ACL grants anon/authenticated table privileges
--   to newly created public tables ("grant by default, deny by RLS"). The house
--   rule for internal, service-only tables is therefore an explicit REVOKE in
--   the creating migration. A project-wide ALTER DEFAULT PRIVILEGES is
--   intentionally NOT applied: many existing tables legitimately rely on the
--   platform default, so that would change behaviour far beyond this finding.
--
-- SAFETY
--   * Hardening only, additive and idempotent (REVOKE/GRANT are absolute and
--     re-runnable).
--   * No policy is created, altered, dropped or disabled; RLS stays ENABLED on
--     both tables. This adds defence in depth and cannot widen access.
--   * No client role is granted anything. No DDL on columns/constraints/indexes,
--     no DROP, no TRUNCATE, no data modification.
--   * service_role keeps the privileges the backend needs — asserted, not assumed.
--   * The post-condition is FAIL-CLOSED: the DO block raises (rolling the whole
--     transaction back) if any client role retains any privilege, if service_role
--     lost DML, or if RLS is not enabled. A partial or ineffective apply cannot pass.
--
-- ROLLBACK (not recommended: restores only the platform default, and RLS with
--           zero policies would still deny every row):
--   GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
--       public.consultant_relationship_requests,
--       public.consultant_mode_change_requests TO anon, authenticated;
-- ============================================================================

BEGIN;

REVOKE ALL PRIVILEGES ON TABLE public.consultant_relationship_requests FROM anon;
REVOKE ALL PRIVILEGES ON TABLE public.consultant_relationship_requests FROM authenticated;
REVOKE ALL PRIVILEGES ON TABLE public.consultant_mode_change_requests   FROM anon;
REVOKE ALL PRIVILEGES ON TABLE public.consultant_mode_change_requests   FROM authenticated;

-- House convention for service-only tables (identical to 20261030 / 20261101):
GRANT ALL PRIVILEGES ON TABLE public.consultant_relationship_requests TO service_role;
GRANT ALL PRIVILEGES ON TABLE public.consultant_mode_change_requests   TO service_role;

-- ----------------------------------------------------------------------------
-- Fail-closed post-condition. Anything unexpected raises inside the
-- transaction, leaving the project byte-identical to its prior state.
-- ----------------------------------------------------------------------------
DO $ct03_f1_closure$
DECLARE
    tbl   text;
    priv  text;
    worst text;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'consultant_relationship_requests',
        'consultant_mode_change_requests'
    ]
    LOOP
        -- (a) NO privilege of any kind may remain for a client role. The ACL is
        --     read directly (not per privilege name) so a future privilege type
        --     cannot slip through this check.
        SELECT string_agg(DISTINCT format('%s:%s', r.rolname, a.privilege_type), ', ')
          INTO worst
          FROM pg_class c
          CROSS JOIN LATERAL aclexplode(
                 coalesce(c.relacl, acldefault('r', c.relowner))) AS a
          JOIN pg_roles r ON r.oid = a.grantee
         WHERE c.oid = format('public.%I', tbl)::regclass
           AND r.rolname IN ('anon', 'authenticated');

        IF worst IS NOT NULL THEN
            RAISE EXCEPTION
                'CT03 F-1 closure: public.% still grants % to a client role',
                tbl, worst;
        END IF;

        -- (b) The service-role API path must keep its DML.
        FOREACH priv IN ARRAY ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        LOOP
            IF NOT has_table_privilege('service_role', format('public.%I', tbl), priv) THEN
                RAISE EXCEPTION
                    'CT03 F-1 closure: service_role lost % on public.%', priv, tbl;
            END IF;
        END LOOP;

        -- (c) RLS must still be enabled: this file hardens, it never loosens.
        IF NOT (SELECT relrowsecurity FROM pg_class
                 WHERE oid = format('public.%I', tbl)::regclass) THEN
            RAISE EXCEPTION
                'CT03 F-1 closure: RLS is not enabled on public.%', tbl;
        END IF;

        RAISE NOTICE 'CT03 F-1 closure: public.% is service-role only, RLS enabled', tbl;
    END LOOP;
END
$ct03_f1_closure$;

COMMIT;

