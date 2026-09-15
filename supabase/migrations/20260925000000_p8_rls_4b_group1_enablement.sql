-- ============================================================================
-- CarbonTally Phase 8 — Separate Workstream RLS — RLS-4B
-- File: 20260925000000_p8_rls_4b_group1_enablement.sql
--
-- AUTHORITY (three completed, PO-facing analyses; this file implements their
-- bounded conclusion and nothing else):
--   * P8-PROD-RLS-RECON-001                   — production RLS/grants reconciliation
--   * P8-PROD-SECURITY-REMEDIATION-DESIGN-001 — per-table security model + Group-1 set
--   * P8-PROD-RLS-WRITE-COVERAGE-VERIFY-001   — client coverage + SAFE-RLS rehearsal
--
-- OPERATION — RLS ENABLEMENT ONLY.
--   Scope:      `ALTER TABLE public.<t> ENABLE ROW LEVEL SECURITY` for the
--               approved Group-1 table set (50 tables), each of which already
--               carries its own established, approved policy family written by
--               earlier migrations in this chain.
--   Not scope:  no policy is created, dropped, altered, broadened or narrowed;
--               no GRANT/REVOKE; no ALTER DEFAULT PRIVILEGES; no FORCE ROW LEVEL
--               SECURITY; no storage change; no data change; no function change.
--
-- WHY THIS IS SAFE (verified evidence, not assumption):
--   * Every table below already has >=1 policy in the `public` schema (the guard
--     below RAISEs if that is ever untrue, so RLS can never be enabled on a table
--     that would silently become deny-all by accident).
--   * Tenant/consultant/entity predicate semantics were empirically verified on
--     the disposable clone: member-own-org ALLOW, member-other-org DENY,
--     consultant-of-A ALLOW on A / DENY on B, unrelated user DENY, entity member
--     ALLOW in-entity / DENY out-of-entity, cross-tenant INSERT rejected with
--     "new row violates row-level security policy".
--   * `service_role` (backend/FastAPI) has BYPASSRLS, so enabling RLS does not
--     change backend behaviour; it closes the authenticated/anon client surface.
--
-- ORDERING / DEPENDENCY (explicit):
--   The filename sorts AFTER the whole 47-migration catch-up
--   (`20260810050000` .. `20260924000000`). This is deliberate: the policy
--   families this migration activates are (re)written by pending migrations —
--   D15 active-consultant status (20260821000000), the p9 recursion fix
--   (20260822000000), audit/activity append-only (20260831020000), WS6 consultant
--   revocation (20260831040000), and the RLS-4A-1/4A-2 anon and authenticated
--   privilege containment (20260920000000 / 20260922000000 / 20260923000000).
--   Enabling RLS before those would enforce superseded predicate text. No
--   existing migration is modified, reordered or replaced.
--
-- EXPLICIT NON-SCOPE — carried to their own gates (NOT answered here):
--   D-4 `emission_factors` anonymous access; the documents `batches/…` vs
--   `uploads/…` path mismatch; onboarding `organizations` INSERT and
--   `organization_members` self-insert; `conversation_participants` INSERT; the
--   `users` peer-read projection; the legacy `beta_users` / `beta_access_codes` /
--   `waitlist` flows; client DELETE privilege remediation; client-facing column
--   defects in the legacy frontend.
--
-- KNOWN, PRE-EXISTING IMPACT (recorded, not fixed here):
--   `organizations`, `organization_members` and `users` are included for RLS
--   enablement because their existing read/security policies are already approved
--   and no new policy is required. Their unresolved write/peer-read behaviours
--   were already non-functional before this migration (the legacy frontend writes
--   columns that do not exist: `organizations.created_by`,
--   `organization_members.joined_at`, `conversations.is_group`,
--   `messages.organization_id`; the `users` peer reads select non-existent
--   `full_name`/`avatar_url`/`raw_user_meta_data`). RLS neither causes nor
--   worsens those defects.
--
-- IDEMPOTENT: re-running is a no-op (ENABLE ROW LEVEL SECURITY is idempotent, no
-- policy or privilege is touched, no data is written).
-- ENVIRONMENT: repository artifact. Production remains gated — this file does not
-- authorise or perform any production migration or deployment.
-- ============================================================================

BEGIN;

DO $$
DECLARE
    approved text[] := ARRAY[
        -- reference / global read (H): *_authenticated_read families
        'activity_categories', 'document_type_categories', 'document_types',
        'email_templates', 'glossary', 'notification_templates', 'roles',
        'supplier_categories', 'units',
        -- tenant activity / audit (append-only families)
        'activity_feed', 'activity_logs', 'audit_logs', 'document_activity_log',
        -- tenant business surfaces (tenant + consultant families)
        'ai_content_history', 'assets', 'conversations', 'customer_communication',
        'customer_documents', 'customer_review_log', 'customer_subscriptions',
        'customer_verifications', 'document_processing_queue', 'draft_entries',
        'emissions_logs', 'export_history', 'facilities', 'file_attachments',
        'manual_extraction_batches', 'manual_review_queue', 'messages',
        'organization_files', 'organization_metadata', 'organizations',
        'pending_invites', 'processing_logs', 'processing_queue',
        'product_categories', 'report_generation_queue', 'report_templates',
        'suppliers', 'upload_batches', 'usage_tracking', 'user_feedback',
        'user_invitations',
        -- consultant surfaces (firm / self families)
        'consultant_clients', 'consultant_firm_members', 'consultant_profiles',
        -- membership / identity (self + admin families)
        'organization_members', 'users',
        -- staff / entity surface (entity family)
        'staff_profiles'
    ];
    t              text;
    pol_count      int;
    existing       int := 0;
    enabled_before int := 0;
    enabled_after  int := 0;
    processed      int := 0;
    skipped        int := 0;
BEGIN
    IF array_length(approved, 1) <> 50 THEN
        RAISE EXCEPTION 'RLS-4B precondition failed: approved set holds % entries, expected 50',
            array_length(approved, 1);
    END IF;

    -- How many of the approved tables actually exist here, and how many are
    -- already protected (both are informational; the post-condition below is
    -- written so that this migration is a true no-op on a re-run).
    SELECT count(*) INTO existing
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
      AND c.relname = ANY(approved);

    SELECT count(*) INTO enabled_before
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
      AND c.relname = ANY(approved) AND c.relrowsecurity;

    FOREACH t IN ARRAY approved LOOP
        IF to_regclass('public.' || t) IS NULL THEN
            skipped := skipped + 1;
            RAISE NOTICE 'RLS-4B: public.% is absent in this environment — skipped (no DDL performed)', t;
            CONTINUE;
        END IF;

        SELECT count(*) INTO pol_count
        FROM pg_policies WHERE schemaname = 'public' AND tablename = t;

        IF pol_count = 0 THEN
            RAISE EXCEPTION 'RLS-4B guard: public.% has no policy; refusing to enable RLS (deny-all risk). Table must be excluded pending a security decision.', t;
        END IF;

        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
        processed := processed + 1;
    END LOOP;

    SELECT count(*) INTO enabled_after
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
      AND c.relname = ANY(approved) AND c.relrowsecurity;

    -- Post-condition 1: every existing approved table is protected.
    IF enabled_after <> existing THEN
        RAISE EXCEPTION 'RLS-4B post-condition failed: existing=%, enabled_after=% (expected all existing approved tables to be RLS-enabled)',
            existing, enabled_after;
    END IF;

    -- Post-condition 2: FORCE ROW LEVEL SECURITY remains untouched (D-11 deferred).
    IF EXISTS (
        SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = ANY(approved) AND c.relforcerowsecurity
    ) THEN
        RAISE EXCEPTION 'RLS-4B post-condition failed: FORCE ROW LEVEL SECURITY must remain untouched (D-11 deferred)';
    END IF;

    RAISE NOTICE 'RLS-4B: approved=%, existing=%, processed=%, already_enabled_before=%, now_enabled=%, skipped_absent=%, forced=0. No policy, grant, default-privilege, storage, function or data change was made.',
        array_length(approved, 1), existing, processed, enabled_before, enabled_after, skipped;
END $$;

COMMIT;


