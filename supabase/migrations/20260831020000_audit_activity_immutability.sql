-- WS1 / DB-0001 — Legacy audit/activity mutability hardening (2026-08-31).
--
-- Approved remediation (Audit finding DB-0001):
--   * `audit_logs`, `activity_logs`, `document_activity_log` are historical
--     audit/activity records -> ordinary authenticated users must NOT be able
--     to UPDATE or DELETE them. Their UPDATE/DELETE tenant policies are
--     dropped (IF EXISTS: these policies historically lived in the live
--     schema, not in this migration chain). INSERT and SELECT policies are
--     untouched so legitimate logging and read surface keep working.
--   * `activity_feed` is a user-facing feed (read/unread state) where
--     mutation is legitimate UX -> UPDATE/DELETE are retained but scoped to
--     the row owner (`user_id = auth.uid()`) instead of any org member.
--
-- The V3 forensic `audit_trail` is already deny-by-default (no policies) and
-- is intentionally NOT touched here.
--
-- Service-role/backend writes are unaffected (service role bypasses RLS).

-- 1. audit_logs — immutable history.
DROP POLICY IF EXISTS audit_logs_tenant_update ON public.audit_logs;
DROP POLICY IF EXISTS audit_logs_tenant_delete ON public.audit_logs;

-- 2. activity_logs — immutable history.
DROP POLICY IF EXISTS activity_logs_tenant_update ON public.activity_logs;
DROP POLICY IF EXISTS activity_logs_tenant_delete ON public.activity_logs;

-- 3. document_activity_log — immutable history.
DROP POLICY IF EXISTS document_activity_log_tenant_update ON public.document_activity_log;
DROP POLICY IF EXISTS document_activity_log_tenant_delete ON public.document_activity_log;

-- 4. activity_feed — user-facing feed; mutation is row-owner scoped only.
DROP POLICY IF EXISTS activity_feed_tenant_update ON public.activity_feed;
DROP POLICY IF EXISTS activity_feed_tenant_delete ON public.activity_feed;
DROP POLICY IF EXISTS activity_feed_own_update ON public.activity_feed;
DROP POLICY IF EXISTS activity_feed_own_delete ON public.activity_feed;

CREATE POLICY activity_feed_own_update ON public.activity_feed
    FOR UPDATE TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY activity_feed_own_delete ON public.activity_feed
    FOR DELETE TO authenticated
    USING (user_id = auth.uid());
