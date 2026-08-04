-- ============================================================================
-- CarbonTally v1.0 RC1 — Production Hardening Migration
-- File 004 of 008: Row Level Security hardening (verify-first, additive only)
-- Source of truth:
--   * CarbonTally_v1.0_Production_Hardening_Plan.md §3 register, Category A
--     row 5 ("Verify the full RLS policy matrix; enforce service-role
--     discipline") and §7 checklist row 5 — the launch gate is an executed
--     penetration matrix (§9 Gate 4) with ZERO cross-tenant rows.
--   * Structural Change Review C2 (APPROVE): organizations.is_active gives
--     RLS policies "a clean suspend predicate" (review §2 C2 benefits).
--   * Structural Change Review §5 K8/T-null note: NULL organization_id rows
--     fall outside every tenant-equality policy (tenancy hole) — the org
--     backfill/NOT NULL remediation is plan row 6, outside this file.
--
-- VERIFY-FIRST POSTURE (plan §9 Gate 1, "action zero"):
--   The schema dump shows NO RLS policies, but the dump is known to be silent
--   on policies/functions. This file therefore NEVER drops, alters or weakens
--   an existing policy. It only:
--     1. ENABLEs row level security where it is not already enabled
--        (ALTER TABLE ... ENABLE ROW LEVEL SECURITY is itself idempotent);
--     2. CREATEs policies ONLY where pg_policies shows no policy of the same
--        name on the same table.
--   If the Supabase migration files turn out to contain a real policy matrix,
--   this file collapses to a no-op verification pass and the penetration
--   matrix (plan §9 Gate 4) is executed against what is already there.
--
-- *** POLICY PATTERN ASSUMPTION (prominent, per instruction) ***
--   The dump implies no policy pattern, so this file standardises on the
--   conventional Supabase pattern: auth.uid()-based membership through
--   public.organization_members (organization_id, user_id, is_active),
--   evaluated by SECURITY DEFINER helpers (public.is_org_member /
--   public.is_org_active) with row_security disabled inside the helper to
--   avoid recursive policy evaluation on organization_members itself.
--   Alternative considered and NOT used: (organization_id =
--   (current_setting('app.current_organization_id', true))::uuid) — no
--   evidence in the dump that the API sets that GUC, whereas
--   organization_members is the schema's own membership table and auth.uid()
--   is the Supabase-authenticated identity. ONE pattern, applied consistently.
--   Service-role connections (workers, migration owner) BYPASS RLS in
--   Supabase; per plan row 5 they must continue to filter organization_id in
--   code — that discipline is verified by the penetration matrix, not here.
--   UK/IE: no policy differences (launch-scope decision; jurisdiction is a
--   data attribute, not an isolation boundary).
--
-- Idempotency: DO-guards throughout; safe to re-run. No CONCURRENTLY needed.
-- Rollback: this file is additive; rollback = drop ONLY the policies it
-- created (names below) and DISABLE RLS ONLY on tables where this file
-- enabled it — prefer fixing forward; disabling RLS re-opens the dangerous
-- state. Per-table rollback template is commented at the foot of the file.
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 0 — Policy helper functions (membership + tenant suspend predicate)
-- Created here (not in 005) because the policies below depend on them.
-- SECURITY DEFINER + SET row_security = off: the lookup bypasses RLS, which
-- is required (a) to avoid infinite recursion when policy-checking
-- organization_members itself and (b) to keep the predicate index-friendly.
-- Search path pinned (Supabase SECURITY DEFINER hardening convention).
-- ============================================================================
CREATE OR REPLACE FUNCTION public.is_org_member(p_organization_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
SET row_security = off
AS $$
    SELECT EXISTS (
        SELECT 1
          FROM public.organization_members om
         WHERE om.organization_id = p_organization_id
           AND om.user_id = auth.uid()
           AND coalesce(om.is_active, true)
    );
$$;

COMMENT ON FUNCTION public.is_org_member(uuid) IS
    'RLS helper (plan §3 A row 5): is auth.uid() an active member of the given tenant? SECURITY DEFINER, row_security off (no recursion).';

-- C2 suspend predicate: write policies additionally require the tenant to be
-- live (organizations.is_active = true). Suspended tenants keep read access
-- to their own data but cannot mutate it.
CREATE OR REPLACE FUNCTION public.is_org_active(p_organization_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
SET row_security = off
AS $$
    SELECT EXISTS (
        SELECT 1
          FROM public.organizations o
         WHERE o.id = p_organization_id
           AND coalesce(o.is_active, true)
    );
$$;

COMMENT ON FUNCTION public.is_org_active(uuid) IS
    'RLS helper (Structural Review C2, APPROVE): tenant lifecycle predicate — is the organisation live (not suspended/archived)? Used on write policies only.';

-- Lock the helpers down: the world may execute them (they leak only a
-- boolean scoped to the caller's own uid), nothing more.
REVOKE ALL ON FUNCTION public.is_org_member(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.is_org_active(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.is_org_member(uuid) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.is_org_active(uuid) TO authenticated, service_role;

-- ============================================================================
-- SECTION 1 — Tenant-owned tables: ENABLE RLS + membership policies
-- Tenant-owned set derived from the dump: every table carrying an
-- organization_id column (organization root handled in Section 2; user-scoped
-- tables in Section 3; shared reference data in Section 4).
-- Four policies per table, created only if absent:
--   <table>_tenant_select  FOR SELECT  USING (is_org_member(organization_id))
--   <table>_tenant_insert  FOR INSERT  WITH CHECK (member AND org active)
--   <table>_tenant_update  FOR UPDATE  USING (member) WITH CHECK (member AND active)
--   <table>_tenant_delete  FOR DELETE  USING (member AND org active)
-- NEVER drops or replaces a pre-existing policy — if the real migration
-- files already define policies under other names, those stand and the
-- penetration matrix validates the union.
-- ROLLBACK per table (comment out to execute):
--   DROP POLICY IF EXISTS <t>_tenant_select  ON public.<t>;
--   DROP POLICY IF EXISTS <t>_tenant_insert  ON public.<t>;
--   DROP POLICY IF EXISTS <t>_tenant_update  ON public.<t>;
--   DROP POLICY IF EXISTS <t>_tenant_delete  ON public.<t>;
-- ============================================================================
DO $$
DECLARE
    t text;
    tenant_tables text[] := ARRAY[
        -- Dump-derived organization_id-bearing tables (see migration header).
        'activity_feed',
        'activity_logs',
        'ai_content_history',
        'assets',
        'audit_logs',
        'consultant_clients',
        'conversations',
        'customer_communication',
        'customer_documents',
        'customer_review_log',
        'customer_subscriptions',
        'customer_verifications',
        'document_activity_log',
        'document_processing_queue',
        'draft_entries',
        'emissions_logs',
        'export_history',
        'facilities',
        'file_attachments',
        'manual_extraction_batches',
        'manual_review_queue',
        'messages',
        'organization_files',
        'organization_members',
        'organization_metadata',
        'pending_invites',
        'processing_logs',
        'processing_queue',
        'product_categories',
        'report_generation_queue',
        'report_templates',
        'suppliers',
        'upload_batches',
        'usage_tracking',
        'user_feedback',
        'user_invitations'
    ];
BEGIN
    FOREACH t IN ARRAY tenant_tables LOOP
        -- Skip silently if the table does not exist (dump drift guard); the
        -- verification query at the foot of this file surfaces the omission.
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = t) THEN
            RAISE NOTICE 'RLS: table public.% not found — skipped', t;
            CONTINUE;
        END IF;

        -- 1. Enable RLS (idempotent; never DISABLE here — that would weaken).
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);

        -- 2. Policies, each guarded on pg_policies (PG16 has no
        --    CREATE POLICY IF NOT EXISTS).
        IF NOT EXISTS (SELECT 1 FROM pg_policies
                       WHERE schemaname = 'public' AND tablename = t
                         AND policyname = t || '_tenant_select') THEN
            EXECUTE format(
                'CREATE POLICY %I ON public.%I FOR SELECT TO authenticated
                     USING (public.is_org_member(organization_id))',
                t || '_tenant_select', t);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies
                       WHERE schemaname = 'public' AND tablename = t
                         AND policyname = t || '_tenant_insert') THEN
            EXECUTE format(
                'CREATE POLICY %I ON public.%I FOR INSERT TO authenticated
                     WITH CHECK (public.is_org_member(organization_id)
                                 AND public.is_org_active(organization_id))',
                t || '_tenant_insert', t);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies
                       WHERE schemaname = 'public' AND tablename = t
                         AND policyname = t || '_tenant_update') THEN
            EXECUTE format(
                'CREATE POLICY %I ON public.%I FOR UPDATE TO authenticated
                     USING (public.is_org_member(organization_id))
                     WITH CHECK (public.is_org_member(organization_id)
                                 AND public.is_org_active(organization_id))',
                t || '_tenant_update', t);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies
                       WHERE schemaname = 'public' AND tablename = t
                         AND policyname = t || '_tenant_delete') THEN
            EXECUTE format(
                'CREATE POLICY %I ON public.%I FOR DELETE TO authenticated
                     USING (public.is_org_member(organization_id)
                            AND public.is_org_active(organization_id))',
                t || '_tenant_delete', t);
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- SECTION 2 — organizations (tenant root: the tenant key is id itself)
-- Members may read their own organisation; only members of a live
-- organisation may update it. INSERT of new organisations is intentionally
-- NOT granted to authenticated here — org creation is a service-role
-- onboarding flow (plan row 5 service-role discipline); adjust at the API
-- layer if self-serve signup is enabled.
-- ============================================================================
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public'
                   AND tablename='organizations' AND policyname='organizations_member_select') THEN
        CREATE POLICY organizations_member_select ON public.organizations
            FOR SELECT TO authenticated
            USING (public.is_org_member(id));
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public'
                   AND tablename='organizations' AND policyname='organizations_member_update') THEN
        CREATE POLICY organizations_member_update ON public.organizations
            FOR UPDATE TO authenticated
            USING (public.is_org_member(id))
            WITH CHECK (public.is_org_member(id) AND public.is_org_active(id));
    END IF;
END $$;

-- ============================================================================
-- SECTION 3 — User-scoped tables (no organization_id by design)
-- users: self read/update only. PII scrubbing on erasure is performed by the
-- SECURITY DEFINER procedure in 005 (plan §3 A row 22), which bypasses RLS.
-- notifications: recipient-only read; recipient-only update (read receipts).
-- ============================================================================
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public'
                   AND tablename='users' AND policyname='users_self_select') THEN
        CREATE POLICY users_self_select ON public.users
            FOR SELECT TO authenticated USING (id = auth.uid());
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public'
                   AND tablename='users' AND policyname='users_self_update') THEN
        CREATE POLICY users_self_update ON public.users
            FOR UPDATE TO authenticated
            USING (id = auth.uid()) WITH CHECK (id = auth.uid());
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public'
                   AND tablename='notifications' AND policyname='notifications_recipient_select') THEN
        CREATE POLICY notifications_recipient_select ON public.notifications
            FOR SELECT TO authenticated USING (recipient_id = auth.uid());
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public'
                   AND tablename='notifications' AND policyname='notifications_recipient_update') THEN
        CREATE POLICY notifications_recipient_update ON public.notifications
            FOR UPDATE TO authenticated
            USING (recipient_id = auth.uid()) WITH CHECK (recipient_id = auth.uid());
    END IF;
END $$;

-- ============================================================================
-- SECTION 4 — Shared reference data (global, non-tenant): read-only to
-- authenticated users; all writes remain service-role only (service_role
-- bypasses RLS in Supabase, so no write policy is created or needed).
-- emission_factors is the Stage-1 R1 final name (was defra_conversion_factors).
-- ============================================================================
DO $$
DECLARE
    t text;
    reference_tables text[] := ARRAY[
        'activity_categories',
        'document_type_categories',
        'document_types',
        'email_templates',
        'emission_factors',
        'glossary',
        'notification_templates',
        'roles',
        'supplier_categories',
        'units'
    ];
BEGIN
    FOREACH t IN ARRAY reference_tables LOOP
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = t) THEN
            RAISE NOTICE 'RLS: reference table public.% not found — skipped', t;
            CONTINUE;
        END IF;

        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);

        IF NOT EXISTS (SELECT 1 FROM pg_policies
                       WHERE schemaname = 'public' AND tablename = t
                         AND policyname = t || '_authenticated_read') THEN
            EXECUTE format(
                'CREATE POLICY %I ON public.%I FOR SELECT TO authenticated USING (true)',
                t || '_authenticated_read', t);
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- SECTION 5 — VERIFICATION (commented; run manually after applying)
-- The dangerous state is "RLS enabled, zero policies" (table locked to every
-- non-owner role). List any such table before sign-off; the penetration
-- matrix (plan §9 Gate 4) then proves zero cross-tenant rows per role.
--
-- SELECT t.tablename
--   FROM pg_tables t
--  WHERE t.schemaname = 'public'
--    AND t.rowsecurity = true
--    AND NOT EXISTS (SELECT 1 FROM pg_policies p
--                     WHERE p.schemaname = 'public' AND p.tablename = t.tablename)
--  ORDER BY t.tablename;
--
-- Companion check — tenant-owned tables where RLS is still NOT enabled:
--
-- SELECT c.table_name
--   FROM information_schema.columns c
--  WHERE c.table_schema = 'public' AND c.column_name = 'organization_id'
--    AND NOT EXISTS (SELECT 1 FROM pg_tables t
--                     WHERE t.schemaname = 'public' AND t.tablename = c.table_name
--                       AND t.rowsecurity = true)
--  ORDER BY c.table_name;
-- ============================================================================

-- ============================================================================
-- EXPLICITLY NOT DONE (never weaken existing security; no DEFER/REJECT):
--   * No DROP POLICY / ALTER POLICY anywhere in this file.
--   * No FORCE ROW LEVEL SECURITY: would also bind the table owner and risks
--     breaking service flows; Supabase service_role bypass is the approved
--     discipline (plan row 5). Revisit only with penetration-matrix evidence.
--   * No audit-hash or soft-delete policy machinery (REJECT/DEFER items).
--   * pending_invites is policy-protected like any tenant table here; the
--     write-BLOCK on pending_invites (plan row 22, user_invitations canonical)
--     is a privilege change owned by the P2 integrity batch, not RLS.
-- ============================================================================

COMMIT;

-- ============================================================================
-- FULL-FILE ROLLBACK TEMPLATE (destructive — comment out deliberately; only
-- ever run after confirming no pre-existing policies depend on this file):
--   DO $$
--   DECLARE t text;
--   BEGIN
--       FOREACH t IN ARRAY ARRAY[ /* Section 1 tenant table list */ ] LOOP
--           EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', t||'_tenant_select', t);
--           EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', t||'_tenant_insert', t);
--           EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', t||'_tenant_update', t);
--           EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', t||'_tenant_delete', t);
--       END LOOP;
--   END $$;
--   -- Then, and only if this file was the sole enabler:
--   -- ALTER TABLE public.<t> DISABLE ROW LEVEL SECURITY;  -- re-opens the dangerous state; prefer fixing forward
-- ============================================================================

-- End of 004_rc1_rls.sql
