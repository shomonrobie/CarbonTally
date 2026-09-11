-- WS6 / SEC-0003 — Consultant-client revocation role model (2026-08-31).
--
-- Approved product decision:
--   * Consultant Owner / Admin / Manager may revoke a consultant-client
--     relationship.
--   * Consultant Member / Viewer may NOT revoke it.
--
-- Revocation preserves provenance: the existing D19 soft-lifecycle
-- (consultant_clients.status = 'ended' + ended_at/ended_by, written by the
-- backend) already keeps the historical relationship row and writes an audit
-- event; it is NOT account/client deletion. `is_org_consultant` already gates
-- access on `status = 'active'` (D15), so a revoked relationship immediately
-- stops granting consultant access.
--
-- This migration:
--   1. Adds `is_consultant_firm_revoker(p_firm)`: an ACTIVE firm member whose
--      role is owner/admin/manager (the schema role vocabulary is
--      owner/manager/consultant/viewer; 'admin' is included for forward
--      compatibility with role-name conventions).
--   2. Scopes the RLS-level relationship DELETE (`cc_delete_own_firm`) to
--      that revoker role set (previously any `can_manage_clients` member).
--   3. Tightens the client-side tenant DELETE
--      (`consultant_clients_tenant_delete`) from "any org member" to
--      customer owner/admin only (`is_org_admin_or_owner`) — the client does
--      not have direct platform access, and Member/Viewer must not be able to
--      sever the relationship.
--
-- INSERT/UPDATE (relationship creation/metadata) keep the existing
-- `can_manage_clients` gate (that is relationship management, not
-- revocation) and are deliberately not changed.

CREATE OR REPLACE FUNCTION public.is_consultant_firm_revoker(p_firm uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO 'public'
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.consultant_firm_members me
         WHERE me.firm_id = p_firm
           AND me.user_id = auth.uid()
           AND coalesce(me.is_active, true) = true
           AND me.role IN ('owner', 'admin', 'manager')
    );
$$;

GRANT ALL ON FUNCTION public.is_consultant_firm_revoker(uuid) TO authenticated;
GRANT ALL ON FUNCTION public.is_consultant_firm_revoker(uuid) TO service_role;

-- Consultant-side relationship revocation: owner/admin/manager only.
DROP POLICY IF EXISTS cc_delete_own_firm ON public.consultant_clients;
CREATE POLICY cc_delete_own_firm ON public.consultant_clients
    FOR DELETE TO authenticated
    USING (public.is_consultant_firm_revoker(consultant_id));

-- Client-side relationship severance: customer owner/admin only (no member/viewer).
DROP POLICY IF EXISTS consultant_clients_tenant_delete ON public.consultant_clients;
CREATE POLICY consultant_clients_tenant_delete ON public.consultant_clients
    FOR DELETE TO authenticated
    USING (public.is_org_admin_or_owner(organization_id));
