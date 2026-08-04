-- ============================================================================
-- CarbonTally v1.0 RC1 — Production Hardening Migration
-- File 006 of 008: Approved triggers — updated_at maintenance only
-- Source of truth:
--   * Companion to 005_rc1_functions.sql F1 (public.set_updated_at()).
--   * Scope rule: every MUTABLE table carrying an updated_at column gains a
--     BEFORE UPDATE maintenance trigger. The dump shows NO triggers at all,
--     so these are new (verify-first: each trigger is dropped by name and
--     recreated, making the file idempotent and tolerant of pre-existing
--     equivalents under the same conventional name).
--   * Append-only log/audit tables are DELIBERATELY EXCLUDED: the approved
--     hardening-plan B item "audit privilege hardening (revoke UPDATE/DELETE
--     on audit tables; drop updated_at from append-only logs)" (§5 B, v1.0.1)
--     removes updated_at from exactly those tables — installing maintenance
--     triggers on them now would create machinery scheduled for removal and
--     would bless UPDATEs on rows that should be immutable. Excluded:
--       activity_logs, document_activity_log, email_logs, processing_logs,
--       user_activity_log, review_audit_trail.
--   * REJECTED/DEFERRED and intentionally absent: audit hash-chain triggers
--     (§6 D5, REJECT), speculative audit triggers on the 9+ audit log tables
--     (flagged as over-engineering), soft-delete triggers (C13, DEFER v1.0.x).
--
-- Idempotency: one DO-block; each trigger is DROP TRIGGER IF EXISTS'd by its
-- deterministic name then recreated. Never touches any other trigger.
-- No CONCURRENTLY needed (metadata-only). UK English.
-- Rollback: run the commented DO-block at the foot of the file.
-- ============================================================================

BEGIN;

DO $$
DECLARE
    t text;
    mutable_tables text[] := ARRAY[
        -- Reference/config (mutable)
        'activity_categories',
        'beta_access_codes',
        'document_type_categories',
        'document_types',
        'email_templates',
        'emission_factors',          -- Stage-1 R1 final name (was defra_conversion_factors)
        'glossary',
        'notification_templates',
        'roles',
        'supplier_categories',
        'units',
        -- Tenant core
        'organizations',
        'organization_members',
        'organization_metadata',
        'organization_files',
        'users',
        'beta_users',
        'waitlist',
        'password_reset_tokens',
        -- Tenant business tables
        'assets',
        'consultant_billing',
        'consultant_clients',
        'consultant_firm_members',
        'consultant_profiles',
        'consultant_tasks',
        'conversation_participants',
        'conversations',
        'customer_documents',
        'customer_review_log',
        'customer_subscriptions',
        'customer_verifications',
        'customer_communication',
        'document_processing_queue',
        'draft_entries',
        'emissions_logs',
        'export_history',
        'facilities',
        'manual_extraction_batches',
        'manual_extraction_items',
        'manual_review_queue',
        'messages',
        'notification_delivery',
        'notifications',
        'pending_invites',
        'product_categories',
        'processing_queue',
        'processing_assignments',
        'processing_steps',
        'processing_time_log',
        'report_comments',
        'report_generation_queue',
        'report_templates',
        'suppliers',
        'typing_status',
        'upload_batches',
        'usage_tracking',
        'user_feedback',
        'user_invitations',
        -- Staff/QC/operations (mutable workflow tables)
        'approval_decisions',
        'approval_requests',
        'business_hours',
        'internal_tasks',
        'qc_checklists',
        'qc_checks',
        'qc_errors',
        'queue_settings',
        'sla_compliance',
        'sla_definitions',
        'staff_daily_performance',
        'staff_performance',
        'staff_profiles',
        'staff_roles',
        'staff_workload',
        'system_settings',
        'task_assignments',
        'team_performance'
    ];
BEGIN
    FOREACH t IN ARRAY mutable_tables LOOP
        -- Guards: table must exist AND must actually carry an updated_at
        -- column (dump drift / migration-file reconciliation tolerance).
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_schema = 'public' AND table_name = t
                         AND column_name = 'updated_at') THEN
            RAISE NOTICE 'TRIGGER: public.% missing or has no updated_at — skipped', t;
            CONTINUE;
        END IF;

        EXECUTE format('DROP TRIGGER IF EXISTS %I ON public.%I',
                       'trg_set_updated_at_' || t, t);
        EXECUTE format(
            'CREATE TRIGGER %I
                 BEFORE UPDATE ON public.%I
                 FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()',
            'trg_set_updated_at_' || t, t);
    END LOOP;
END $$;

-- ============================================================================
-- VERIFICATION (commented; run manually after applying)
-- Every mutable table with updated_at but no maintenance trigger:
--
-- SELECT c.table_name
--   FROM information_schema.columns c
--  WHERE c.table_schema = 'public' AND c.column_name = 'updated_at'
--    AND c.table_name NOT IN ('activity_logs','document_activity_log','email_logs',
--                             'processing_logs','user_activity_log','review_audit_trail')
--    AND NOT EXISTS (SELECT 1 FROM information_schema.triggers tr
--                     WHERE tr.event_object_schema = 'public'
--                       AND tr.event_object_table = c.table_name
--                       AND tr.trigger_name = 'trg_set_updated_at_' || c.table_name)
--  ORDER BY c.table_name;
--
-- Behavioural smoke test (per table class):
--   BEGIN;
--   UPDATE public.organizations SET name = name WHERE id = '<some-id>';
--   -- confirm updated_at advanced relative to its prior value
--   ROLLBACK;
-- ============================================================================

-- ============================================================================
-- EXPLICITLY NOT IMPLEMENTED (register verification):
--   * Audit hash-chain triggers — REJECTED (hardening plan §6 D5).
--   * Speculative audit/activity triggers on the existing 9+ audit log
--     tables — over-engineering flagged by the review; no new audit machinery.
--   * Soft-delete (deleted_at) triggers — DEFERRED (Structural Review C13,
--     v1.0.x window).
--   * Append-only log tables — excluded pending the approved v1.0.1 B item
--     that drops their updated_at columns entirely.
--
-- ROLLBACK (removes ONLY the triggers this file owns):
--   DO $$
--   DECLARE t text;
--   BEGIN
--       FOR t IN SELECT event_object_table FROM information_schema.triggers
--                 WHERE trigger_schema = 'public'
--                   AND trigger_name LIKE 'trg\_set\_updated\_at\_%' LOOP
--           EXECUTE format('DROP TRIGGER IF EXISTS %I ON public.%I',
--                          'trg_set_updated_at_' || t, t);
--       END LOOP;
--   END $$;
-- ============================================================================

COMMIT;

-- End of 006_rc1_triggers.sql
