-- ============================================================================
-- CarbonTally Backend v2.1 — Phase 0, Migration M8 of 8
-- File: 20260807070000_add_new_table_rls.sql
--
-- Row Level Security for the four Phase-0 tables
-- (import_batches, calculation_snapshots, domain_events, factor_aliases).
-- Readiness Review R24.
--
-- Conventions (matches the RC2 RLS storey):
--   * RLS is ENABLEd on every table (deny-by-default floor).
--   * Explicit GRANTs are required because this stack does not auto-grant
--     SELECT/INSERT/UPDATE/DELETE to anon/authenticated/service_role
--     (verified empirically: new tables otherwise get only Dxtm).
--     Service role gets ALL; authenticated gets DML only (no TRUNCATE /
--     TRIGGER); anon gets nothing (fully locked — no policy, no privilege).
--   * Policies reuse the RC2 SECURITY DEFINER helper public.is_org_member(uuid).
--
-- Policy matrix (frozen):
--   import_batches        : no policies          → deny-by-default
--   domain_events         : no policies          → deny-by-default
--   calculation_snapshots : SELECT own org       → org members may read
--   factor_aliases        : SELECT own/global, INSERT/DELETE own org
--
-- Idempotent: ENABLE RLS is idempotent; GRANT re-application is a no-op;
-- policies use DROP POLICY IF EXISTS + CREATE POLICY.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Enable RLS on all four tables (idempotent; never DISABLE here).
-- ---------------------------------------------------------------------------
ALTER TABLE public.import_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.calculation_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.domain_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.factor_aliases ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 2. Table privileges.
--    service_role: full access (backend writes/reads via the service key).
--    authenticated: DML only — SELECT/INSERT/UPDATE/DELETE. TRUNCATE, TRIGGER,
--      REFERENCES and MAINTAIN are explicitly REVOKEd because the local
--      Supabase stack's default ACL grants them (Dxtm) to new tables and
--      TRUNCATE is NOT gated by Row Level Security.
--    anon: no privileges (deny-by-default even beyond RLS).
-- ---------------------------------------------------------------------------
GRANT ALL ON TABLE public.import_batches TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.import_batches TO authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.import_batches FROM authenticated;

GRANT ALL ON TABLE public.calculation_snapshots TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.calculation_snapshots TO authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.calculation_snapshots FROM authenticated;

GRANT ALL ON TABLE public.domain_events TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.domain_events TO authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.domain_events FROM authenticated;

GRANT ALL ON TABLE public.factor_aliases TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.factor_aliases TO authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.factor_aliases FROM authenticated;

-- ---------------------------------------------------------------------------
-- 3. Policies.
--    import_batches / domain_events: intentionally NO policies — deny-by-default.
-- ---------------------------------------------------------------------------

-- calculation_snapshots: organisation members may read their own org's
-- snapshots (immutable forensic records — no INSERT/UPDATE/DELETE policies;
-- writes happen exclusively through the service role).
DROP POLICY IF EXISTS calc_snapshots_select_own ON public.calculation_snapshots;
CREATE POLICY calc_snapshots_select_own ON public.calculation_snapshots
    FOR SELECT TO authenticated
    USING (public.is_org_member(organization_id));

-- factor_aliases: SELECT any global alias (organization_id IS NULL) or an
-- alias belonging to an organisation the user actively belongs to.
DROP POLICY IF EXISTS aliases_select_own ON public.factor_aliases;
CREATE POLICY aliases_select_own ON public.factor_aliases
    FOR SELECT TO authenticated
    USING (
        organization_id IS NULL
        OR public.is_org_member(organization_id)
    );

-- factor_aliases: INSERT only org-scoped aliases for organisations the user
-- actively belongs to (no global-alias creation by authenticated users).
DROP POLICY IF EXISTS aliases_insert_own ON public.factor_aliases;
CREATE POLICY aliases_insert_own ON public.factor_aliases
    FOR INSERT TO authenticated
    WITH CHECK (
        organization_id IS NOT NULL
        AND public.is_org_member(organization_id)
    );

-- factor_aliases: DELETE only own-org aliases.
DROP POLICY IF EXISTS aliases_delete_own ON public.factor_aliases;
CREATE POLICY aliases_delete_own ON public.factor_aliases
    FOR DELETE TO authenticated
    USING (
        organization_id IS NOT NULL
        AND public.is_org_member(organization_id)
    );

-- ============================================================================
-- VERIFICATION CHECKLIST (M8)
--   [ ] RLS enabled on all four tables (pg_class.relrowsecurity = true)
--   [ ] service_role has ALL on all four tables
--   [ ] authenticated has SELECT/INSERT/UPDATE/DELETE (no TRUNCATE/TRIGGER)
--   [ ] anon has no privileges on any of the four tables
--   [ ] calc_snapshots_select_own present (FOR SELECT TO authenticated)
--   [ ] aliases_select_own / aliases_insert_own / aliases_delete_own present
--   [ ] import_batches / domain_events have ZERO policies (deny-by-default)
--   [ ] Re-running this file is a no-op
-- ============================================================================
