-- ============================================================================
-- CarbonTally V3 — Phase 9 RLS recursion fix (2026-08-22)
--
-- Defect found during Phase 9 RLS verification:
--   SELECT/INSERT/UPDATE policies on `organization_members` and
--   `consultant_firm_members` / `consultant_clients` embed INLINE subqueries
--   against the SAME table. Postgres RLS applies RLS inside those subqueries,
--   so any direct authenticated read of these tables raised:
--       ERROR: infinite recursion detected in policy for relation "..."
--   The security posture failed CLOSED (no data leaked), but the legitimate
--   direct-RLS surface was broken for every authenticated user.
--
-- Fix (bounded, no semantic change):
--   * Add SECURITY DEFINER helpers that query the membership tables WITHOUT
--     RLS (the established pattern used by is_org_member / is_org_consultant /
--     is_entity_member / is_org_admin_or_owner).
--   * Rewrite the recursive policies to call those helpers.
--   * Behaviour for every actor is UNCHANGED: members see their own rows and
--     their org/firm admin sees admin rows; everyone else sees nothing.
-- ============================================================================
BEGIN;

-- ---------------------------------------------------------------------------
-- 1. SECURITY DEFINER firm-membership helpers (bypass RLS like the existing
--    is_org_* / is_entity_member helpers).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.is_consultant_firm_member(p_firm uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public'
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.consultant_firm_members me
         WHERE me.firm_id = p_firm
           AND me.user_id = auth.uid()
           AND coalesce(me.is_active, true) = true
    );
$$;

CREATE OR REPLACE FUNCTION public.is_consultant_firm_manager(p_firm uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public'
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.consultant_firm_members me
         WHERE me.firm_id = p_firm
           AND me.user_id = auth.uid()
           AND coalesce(me.is_active, true) = true
           AND me.can_manage_clients = true
    );
$$;

CREATE OR REPLACE FUNCTION public.is_consultant_team_admin(p_firm uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public'
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.consultant_firm_members me
         WHERE me.firm_id = p_firm
           AND me.user_id = auth.uid()
           AND coalesce(me.is_active, true) = true
           AND me.can_manage_team = true
    );
$$;


-- ---------------------------------------------------------------------------
-- 2. organization_members — replace inline self-referential subqueries.
-- ---------------------------------------------------------------------------
DROP POLICY IF EXISTS om_select_self_or_admin ON public.organization_members;
CREATE POLICY om_select_self_or_admin ON public.organization_members
    FOR SELECT TO authenticated
    USING ((user_id = auth.uid()) OR public.is_org_admin_or_owner(organization_id));

DROP POLICY IF EXISTS om_insert_admin ON public.organization_members;
CREATE POLICY om_insert_admin ON public.organization_members
    FOR INSERT TO authenticated
    WITH CHECK (public.is_org_admin_or_owner(organization_id));

DROP POLICY IF EXISTS om_update_admin ON public.organization_members;
CREATE POLICY om_update_admin ON public.organization_members
    FOR UPDATE TO authenticated
    USING (public.is_org_admin_or_owner(organization_id))
    WITH CHECK (((role)::text = ANY ((ARRAY['owner'::character varying, 'admin'::character varying, 'member'::character varying, 'viewer'::character varying])::text[])));

-- ---------------------------------------------------------------------------
-- 3. consultant_firm_members — replace inline self-referential subquery.
-- ---------------------------------------------------------------------------
DROP POLICY IF EXISTS cfm_select_self_or_team_admin ON public.consultant_firm_members;
CREATE POLICY cfm_select_self_or_team_admin ON public.consultant_firm_members
    FOR SELECT TO authenticated
    USING ((user_id = auth.uid()) OR public.is_consultant_team_admin(firm_id));

-- ---------------------------------------------------------------------------
-- 4. consultant_clients — replace inline firm-membership subqueries.
-- ---------------------------------------------------------------------------
DROP POLICY IF EXISTS cc_select_own_firm ON public.consultant_clients;
CREATE POLICY cc_select_own_firm ON public.consultant_clients
    FOR SELECT TO authenticated
    USING (public.is_consultant_firm_member(consultant_id));

DROP POLICY IF EXISTS cc_update_own_firm ON public.consultant_clients;
CREATE POLICY cc_update_own_firm ON public.consultant_clients
    FOR UPDATE TO authenticated
    USING (public.is_consultant_firm_manager(consultant_id));

DROP POLICY IF EXISTS cc_delete_own_firm ON public.consultant_clients;
CREATE POLICY cc_delete_own_firm ON public.consultant_clients
    FOR DELETE TO authenticated
    USING (public.is_consultant_firm_manager(consultant_id));

DROP POLICY IF EXISTS cc_insert_own_firm ON public.consultant_clients;
CREATE POLICY cc_insert_own_firm ON public.consultant_clients
    FOR INSERT TO authenticated
    WITH CHECK (public.is_consultant_firm_manager(consultant_id));

COMMIT;
