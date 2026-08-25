-- D15 (APPROVED 2026-08-20) — consultant access is based on an ACTIVE
-- consultant-client authorization. When the consultant-client relationship
-- ends (status != 'active'), consultant access to that client ends.
--
-- `is_org_consultant` (RLS) now requires an active `consultant_clients` grant
-- row. `client_access` (a per-member shortcut on `consultant_firm_members`)
-- does NOT independently grant organisation access — the active grant row is
-- the single source of the relationship.
--
-- Scope note (D20): this does not affect Processing Entity staff (they are
-- never consultants); consultant authorization remains a separate model.

CREATE OR REPLACE FUNCTION public.is_org_consultant(p_org uuid)
RETURNS boolean
LANGUAGE sql
STABLE SECURITY DEFINER
SET search_path TO 'public'
AS $$
    SELECT EXISTS (
        SELECT 1
          FROM public.consultant_firm_members cfm
         WHERE cfm.user_id = auth.uid()
           AND coalesce(cfm.is_active, true) = true
           AND EXISTS (
               SELECT 1
                 FROM public.consultant_clients cc
                WHERE cc.consultant_id = cfm.firm_id
                  AND cc.organization_id = p_org
                  AND cc.status = 'active'
           )
    );
$$;

GRANT ALL ON FUNCTION public.is_org_consultant(uuid) TO authenticated;
GRANT ALL ON FUNCTION public.is_org_consultant(uuid) TO service_role;
