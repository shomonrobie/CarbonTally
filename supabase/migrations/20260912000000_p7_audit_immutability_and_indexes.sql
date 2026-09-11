-- ============================================================================
-- CarbonTally Phase 7 — Auditor / Assurance: audit-ledger integrity + indexes
-- File: 20260912000000_p7_audit_immutability_and_indexes.sql
--
-- Purpose (Phase 7, PO-authorized): make the canonical audit ledger resistant
-- to ordinary modification/deletion and efficient to investigate.
--
-- Canonical responsibility (no new audit architecture is introduced):
--   * ``public.audit_trail`` (RC2) — the canonical append-only audit ledger
--     used by ``backend/data/audit.py`` (AuditRepository) for material
--     human/system actions across every surface. Phase 7 stores its
--     category/origin/outcome/actor_type/organization_id taxonomy in the
--     existing ``metadata`` JSONB (no schema change).
--   * ``audit_logs`` / ``activity_logs`` / ``document_activity_log`` — legacy
--     per-domain activity records; already made immutable by migration
--     ``20260831020000_audit_activity_immutability.sql`` (DB-0001).
--   * ``calculation_snapshots`` — immutable forensic calculation records
--     (existing; append-only by design + SHA-256 ``content_hash``).
--
-- This migration is ADDITIVE and IDEMPOTENT. It does not modify existing
-- policies, does not weaken RLS, and does not touch any business table.
--
-- NOTE ON ENFORCEMENT: the trigger fires for every role, including the
-- service role used by the backend — so the ledger is append-only at the
-- database, not merely by convention. A future authorised retention/purge
-- process must deliberately drop this trigger first (documented, controlled).
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Append-only enforcement on the canonical audit ledger
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.p7_audit_trail_immutable()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'audit_trail is append-only (Phase 7): % is not permitted', TG_OP
        USING ERRCODE = 'raise_exception';
END;
$$;

COMMENT ON FUNCTION public.p7_audit_trail_immutable() IS
    'Phase 7 — blocks UPDATE/DELETE on public.audit_trail so the canonical '
    'audit ledger is append-only for every role.';

DROP TRIGGER IF EXISTS p7_audit_trail_immutable ON public.audit_trail;
CREATE TRIGGER p7_audit_trail_immutable
    BEFORE UPDATE OR DELETE ON public.audit_trail
    FOR EACH ROW
    EXECUTE FUNCTION public.p7_audit_trail_immutable();

-- ---------------------------------------------------------------------------
-- 2. Investigation indexes (audit console + scoped audit reads)
-- ---------------------------------------------------------------------------
-- Chronological investigation (the dominant query order).
CREATE INDEX IF NOT EXISTS idx_audit_trail_performed_at
    ON public.audit_trail (performed_at DESC);

-- Action/resource lookup (audit console filters).
CREATE INDEX IF NOT EXISTS idx_audit_trail_action_type
    ON public.audit_trail (action_type);

CREATE INDEX IF NOT EXISTS idx_audit_trail_table_record
    ON public.audit_trail (table_name, record_id);

-- Phase 7 taxonomy filters (category/origin/outcome/organization_id live in
-- metadata). jsonb_path_ops keeps the GIN index small.
CREATE INDEX IF NOT EXISTS idx_audit_trail_metadata_gin
    ON public.audit_trail USING gin (metadata jsonb_path_ops);

-- Org-scoped audit reads (org-tagged events) — partial index keeps it lean.
CREATE INDEX IF NOT EXISTS idx_audit_trail_org
    ON public.audit_trail ((metadata->>'organization_id'))
    WHERE metadata ? 'organization_id';

-- ============================================================================
-- VERIFICATION CHECKLIST
--   [ ] function public.p7_audit_trail_immutable() exists
--   [ ] trigger p7_audit_trail_immutable exists on public.audit_trail
--   [ ] UPDATE/DELETE on audit_trail raises an exception (all roles)
--   [ ] INSERT/SELECT on audit_trail unaffected
--   [ ] investigation indexes exist and are valid
--   [ ] re-running this file is a no-op
-- ============================================================================
