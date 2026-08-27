-- ============================================================================
-- CarbonTally v1.0 RC2 — Production Hardening Migration (REPAIR RELEASE)
-- File 004 of 008: Row Level Security policies (the RLS "storey")
-- Source of truth:
--   * Baseline: supabase/migrations/00000000000000_init_schema.sql
--   * CarbonTally RC1 — Independent Database Audit.md (RC2-C2, RC2-C4, RC2-C5,
--     RC2-C6; RC2-I3 helper hardening)
--   * CarbonTally_v1.0_Structural_Change_Review.md (APPROVE items only)
-- Database: PostgreSQL 16 (Supabase). Schema: public. Single transaction.
--
-- BASELINE REALITY (verified): the baseline init enables ROW LEVEL SECURITY on
-- EVERY public table, but creates ZERO policies. The net effect is universal
-- DENY-BY-DEFAULT (every non-owner role — anon AND authenticated — is locked
-- out of every table). That is secure-by-default but non-functional: it blocks
-- the very app flows the schema exists to serve, and it leaves no auditable
-- allow path. RC2 004 therefore BUILDS the allow storey on top of the
-- deny-by-default floor:
--   * service_role and postgres BYPASSRLS by definition — no policy, no grant
--     needed (they already act on every row).
--   * `authenticated` gains exactly the read/write policies the tenant model
--     requires. `anon` stays fully locked (deny-by-default retained).
--   * Reference data becomes readable by any authenticated user; tenant data
--     is gated by organisation membership / consultant access; PII & privilege
--     columns are column-restricted.
--   * RC2-C4/C5/C6 embed the three named repro guards (role change / self
--     privilege / consultant tenancy).
--
-- Security helpers are SECURITY DEFINER with `SET search_path` pinned so they
-- can read across RLS without recursion (an owner-context read bypasses RLS
-- and therefore cannot recurse into a policy).
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1 — RLS SECURITY HELPERS (RC2-I3 hardening, policy companions)
-- ============================================================================
-- All four are SECURITY DEFINER so a policy can test tenant state without
-- re-entering the very policies being evaluated (owner-context read). The
-- caller's effective identity is always used directly via auth.uid().

-- is_org_member(org): authenticated user is an ACTIVE member of an ACTIVE org.
CREATE OR REPLACE FUNCTION public.is_org_member(p_org uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$    SELECT EXISTS (
        SELECT 1
          FROM public.organization_members om
          JOIN public.organizations o ON o.id = om.organization_id
         WHERE om.organization_id = p_org
           AND om.user_id = auth.uid()
           AND coalesce(om.is_active, true) = true
           AND coalesce(o.is_active, true) = true
    );$$;

-- is_org_active(org): the org exists and is not archived/suspended.
CREATE OR REPLACE FUNCTION public.is_org_active(p_org uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$    SELECT EXISTS (
        SELECT 1 FROM public.organizations o
         WHERE o.id = p_org AND coalesce(o.is_active, true) = true
    );$$;

-- is_org_admin_or_owner(org): caller is an ACTIVE owner/admin member.
CREATE OR REPLACE FUNCTION public.is_org_admin_or_owner(p_org uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$    SELECT EXISTS (
        SELECT 1 FROM public.organization_members om
         WHERE om.organization_id = p_org
           AND om.user_id = auth.uid()
           AND coalesce(om.is_active, true) = true
           AND om.role IN ('owner','admin')
    );$$;

-- is_org_consultant(org): caller is an ACTIVE consultant firm member with
-- access to the org, either via an explicit client_access entry (UUID[]) or
-- via a live consultant_clients relationship. (RC2-C6.)
CREATE OR REPLACE FUNCTION public.is_org_consultant(p_org uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$    SELECT EXISTS (
        SELECT 1
          FROM public.consultant_firm_members cfm
         WHERE cfm.user_id = auth.uid()
           AND coalesce(cfm.is_active, true) = true
           AND (
               cfm.client_access @> ARRAY[p_org]
               OR EXISTS (
                   SELECT 1 FROM public.consultant_clients cc
                    WHERE cc.consultant_id = cfm.firm_id
                      AND cc.organization_id = p_org
               )
           )
    );$$;

-- ============================================================================
-- SECTION 2 — REFERENCE-DATA READ (authenticated) + re-affirm deny-by-default
-- ============================================================================
-- Pure configuration reference tables: any authenticated user may read, no
-- mutation. RLS stays enabled (baseline) so anon is still denied by default.
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'activity_categories','document_type_categories','document_types',
        'roles','supplier_categories','units','email_templates',
        'notification_templates','glossary'
    ] LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', t || '_authenticated_read', t);
        EXECUTE format(
            'CREATE POLICY %I ON public.%I FOR SELECT TO authenticated USING (true)',
            t || '_authenticated_read', t);
    END LOOP;
END $$;

-- ============================================================================
-- SECTION 3 — TENANT TABLES (organisation-gated)
-- ============================================================================
-- Every table carrying an organisation_id (except the ones handled
-- explicitly in Sections 4–8) is gated:
--   * SELECT: member OR consultant-with-access   (read coverage, incl. C6)
--   * INSERT/UPDATE/DELETE: member only          (write is tenancy-locked)
-- Policy names follow the audit convention `_tenant_*`.
DO $$
DECLARE r record;
BEGIN
        FOR r IN
        SELECT DISTINCT c.table_name
          FROM information_schema.columns c
          JOIN pg_tables t ON t.schemaname = c.table_schema
                          AND t.tablename  = c.table_name
         WHERE c.table_schema = 'public'
           AND c.column_name = 'organization_id'
           AND c.table_name NOT IN ('organizations','organization_members')
         ORDER BY 1
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', r.table_name || '_tenant_select', r.table_name);
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', r.table_name || '_tenant_insert', r.table_name);
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', r.table_name || '_tenant_update', r.table_name);
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', r.table_name || '_tenant_delete', r.table_name);

        EXECUTE format(
            'CREATE POLICY %I ON public.%I FOR SELECT TO authenticated
                 USING (public.is_org_member(organization_id)
                        OR public.is_org_consultant(organization_id))',
            r.table_name || '_tenant_select', r.table_name);

        EXECUTE format(
            'CREATE POLICY %I ON public.%I FOR INSERT TO authenticated
                 WITH CHECK (public.is_org_member(organization_id))',
            r.table_name || '_tenant_insert', r.table_name);

        EXECUTE format(
            'CREATE POLICY %I ON public.%I FOR UPDATE TO authenticated
                 USING (public.is_org_member(organization_id))
                 WITH CHECK (public.is_org_member(organization_id))',
            r.table_name || '_tenant_update', r.table_name);

        EXECUTE format(
            'CREATE POLICY %I ON public.%I FOR DELETE TO authenticated
                 USING (public.is_org_member(organization_id))',
            r.table_name || '_tenant_delete', r.table_name);
    END LOOP;
END $$;

-- ============================================================================
-- SECTION 4 — organizations (tenant root)
-- ============================================================================
-- Member may read their own org (and consultants with access may too).
-- Member may update org profile. No authenticated INSERT/DELETE (tenancy life
-- cycle is service-role owned).
DROP POLICY IF EXISTS organizations_org_select ON public.organizations;
CREATE POLICY organizations_org_select ON public.organizations
    FOR SELECT TO authenticated
    USING (public.is_org_member(id) OR public.is_org_consultant(id));

DROP POLICY IF EXISTS organizations_org_update ON public.organizations;
CREATE POLICY organizations_org_update ON public.organizations
    FOR UPDATE TO authenticated
    USING (public.is_org_member(id))
    WITH CHECK (public.is_org_member(id));

-- ============================================================================
-- SECTION 5 — users (RC2-C5: self-service, column-restricted)
-- ============================================================================
-- A user reads/writes ONLY their own row; privilege & identity columns are
-- column-REVOKEd from authenticated (C5), so no policy can move them.
-- Protected columns: id, email, password_hash, is_active, user_type,
-- email_verified, is_anonymised, last_login.
DROP POLICY IF EXISTS users_select_self ON public.users;
CREATE POLICY users_select_self ON public.users
    FOR SELECT TO authenticated
    USING (id = auth.uid());

DROP POLICY IF EXISTS users_update_self ON public.users;
CREATE POLICY users_update_self ON public.users
    FOR UPDATE TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid() AND new.email = old.email);

-- Column-level restriction (C5): authenticated may UPDATE only benign profile
-- columns. RLS + column privilege BOTH apply; touching a protected column
-- fails the statement, enforcing the guard even if a policy claims self-write.
REVOKE UPDATE ON public.users FROM authenticated;
GRANT UPDATE (first_name, last_name, updated_at) ON public.users TO authenticated;

-- ============================================================================
-- SECTION 6 — organization_members (RC2-C4: role & self-escalation guards)
-- ============================================================================
-- SELECT: a user sees their own memberships; an owner/admin sees the roster
-- for their org (using direct states, not the helper, to avoid the helper
-- reading a table whose own policy is being fabricated).
DROP POLICY IF EXISTS om_select_self_or_admin ON public.organization_members;
CREATE POLICY om_select_self_or_admin ON public.organization_members
    FOR SELECT TO authenticated
    USING (
        user_id = auth.uid()
        OR EXISTS (SELECT 1 FROM public.organization_members admin_om
                    WHERE admin_om.organization_id = organization_members.organization_id
                      AND admin_om.user_id = auth.uid()
                      AND admin_om.role IN ('owner','admin')
                      AND coalesce(admin_om.is_active,true))
    );

-- INSERT: only an owner/admin may add members to their own org.
DROP POLICY IF EXISTS om_insert_admin ON public.organization_members;
CREATE POLICY om_insert_admin ON public.organization_members
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (SELECT 1 FROM public.organization_members admin_om
                 WHERE admin_om.organization_id = organization_members.organization_id
                   AND admin_om.user_id = auth.uid()
                   AND admin_om.role IN ('owner','admin')
                   AND coalesce(admin_om.is_active,true))
    );

-- UPDATE self: a member may touch ONLY their own row and may NOT change role,
-- organisation, or the is_active flag (self-escalation guard, C4).
DROP POLICY IF EXISTS om_update_self ON public.organization_members;
CREATE POLICY om_update_self ON public.organization_members
    FOR UPDATE TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (
        user_id = auth.uid()
        AND new.role = old.role
        AND new.organization_id = old.organization_id
        AND coalesce(new.is_active,true) = coalesce(old.is_active,true)
    );

-- UPDATE admin: an owner/admin may manage other members (and themselves, for
-- the non-role columns) but may not re-home the membership to another org,
-- and roles are confined to the approved vocabulary.
DROP POLICY IF EXISTS om_update_admin ON public.organization_members;
CREATE POLICY om_update_admin ON public.organization_members
    FOR UPDATE TO authenticated
    USING (
        EXISTS (SELECT 1 FROM public.organization_members admin_om
                 WHERE admin_om.organization_id = organization_members.organization_id
                   AND admin_om.user_id = auth.uid()
                   AND admin_om.role IN ('owner','admin')
                   AND coalesce(admin_om.is_active,true))
    )
    WITH CHECK (
        new.organization_id = old.organization_id
        AND new.role IN ('owner','admin','member','viewer')
    );

-- No authenticated DELETE on organization_members: ownership change / removal
-- is done by an admin UPDATE of is_active, plus service-role hard-delete.

-- ============================================================================
-- SECTION 7 — consultant tables (RC2-C6: firm-tenanted access model)
-- ============================================================================
-- consultant_profiles: a firm member reads their own firm profile.
DROP POLICY IF EXISTS cp_select_own ON public.consultant_profiles;
CREATE POLICY cp_select_own ON public.consultant_profiles
    FOR SELECT TO authenticated
    USING (user_id = auth.uid());

-- consultant_firm_members: a firm member reads their own row; a user who can
-- manage the team reads the whole firm roster.
DROP POLICY IF EXISTS cfm_select_self_or_team_admin ON public.consultant_firm_members;
CREATE POLICY cfm_select_self_or_team_admin ON public.consultant_firm_members
    FOR SELECT TO authenticated
    USING (
        user_id = auth.uid()
        OR EXISTS (SELECT 1 FROM public.consultant_firm_members me
                                        WHERE me.firm_id = consultant_firm_members.firm_id
                      AND me.user_id = auth.uid()
                      AND coalesce(me.is_active, true)
                                            AND me.can_manage_team = true)
    );

-- consultant_firm_members: a firm member may update their own row, but may NOT
-- escalate team permissions or widen client_access (RC2-C6).
DROP POLICY IF EXISTS cfm_update_self_or_team_admin ON public.consultant_firm_members;
CREATE POLICY cfm_update_self_or_team_admin ON public.consultant_firm_members
    FOR UPDATE TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (
        user_id = auth.uid()
        AND new.firm_id = old.firm_id
        AND new.can_manage_team = old.can_manage_team
        AND new.can_manage_clients = old.can_manage_clients
        AND new.can_upload_documents = old.can_upload_documents
        AND new.client_access = old.client_access
    );

-- consultant_clients: firm members may read their firm's client links; only a
-- member with client management may create / update / delete them.
DROP POLICY IF EXISTS cc_select_own_firm ON public.consultant_clients;
CREATE POLICY cc_select_own_firm ON public.consultant_clients
    FOR SELECT TO authenticated
    USING (
        EXISTS (SELECT 1 FROM public.consultant_firm_members me
                 WHERE me.firm_id = consultant_clients.consultant_id
                   AND me.user_id = auth.uid()
                   AND coalesce(me.is_active, true))
    );

DROP POLICY IF EXISTS cc_insert_own_firm ON public.consultant_clients;
CREATE POLICY cc_insert_own_firm ON public.consultant_clients
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (SELECT 1 FROM public.consultant_firm_members me
                 WHERE me.firm_id = consultant_clients.consultant_id
                   AND me.user_id = auth.uid()
                   AND coalesce(me.is_active, true)
                   AND me.can_manage_clients = true)
    );

DROP POLICY IF EXISTS cc_update_own_firm ON public.consultant_clients;
CREATE POLICY cc_update_own_firm ON public.consultant_clients
    FOR UPDATE TO authenticated
    USING (
        EXISTS (SELECT 1 FROM public.consultant_firm_members me
                 WHERE me.firm_id = consultant_clients.consultant_id
                   AND me.user_id = auth.uid()
                   AND coalesce(me.is_active, true)
                   AND me.can_manage_clients = true)
    )
    WITH CHECK (new.consultant_id = old.consultant_id);

DROP POLICY IF EXISTS cc_delete_own_firm ON public.consultant_clients;
CREATE POLICY cc_delete_own_firm ON public.consultant_clients
    FOR DELETE TO authenticated
    USING (
        EXISTS (SELECT 1 FROM public.consultant_firm_members me
                 WHERE me.firm_id = consultant_clients.consultant_id
                   AND me.user_id = auth.uid()
                   AND coalesce(me.is_active, true)
                   AND me.can_manage_clients = true)
    );

-- ============================================================================
-- SECTION 8 — EXPLICITLY NOT IMPLEMENTED / GUARD NOTES (register verification)
-- ============================================================================
--   * `anon` role: REMAINS fully denied on every table (the deny-by-default
--     floor is preserved; no anon policy is created anywhere).
--   * service_role / postgres: BYPASSRLS by Supabase convention — no policies
--     and no extra grants are issued here.
--   * staff_profiles / staff-only workflow tables: left deny-by-default for
--     `authenticated` (staff workflows are service-role/internal; the staff
--     RBAC storey is a v1.1 concern).
--
-- ROLLBACK (revert to deny-by-default floor):
--   * Drop the policies created in Sections 2–7 (by their names above) and keep
--     the baseline RLS enablement — that restores full deny-by-default.
--   * DROP FUNCTION
--       public.is_org_member(uuid),
--       public.is_org_active(uuid),
--       public.is_org_admin_or_owner(uuid),
--       public.is_org_consultant(uuid);
--   * REVOKE UPDATE ON public.users FROM authenticated;
-- ============================================================================

COMMIT;

-- End of 004_rc2_rls.sql
