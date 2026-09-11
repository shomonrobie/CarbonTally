-- ============================================================================
-- CarbonTally V3 — Implementation Phase 1, Migration V3M-5
-- File: 20260810040000_v3m5_issues.sql
--
-- Implements the approved First-Class Issue Management model (ADR-V3-009 —
-- DECIDED, Option B; V3 IA §8 V3M-5; V3 Database Impact Plan §6).
--
-- Scope (strictly V3M-5):
--   * issues (NEW table — first-class Issue domain)
--
-- Issue ≠ Conversation ≠ Validation Error ≠ QC Error ≠ User Feedback:
--   * user_feedback, qc_checks/qc_errors, validation mechanisms, rejection/
--     correction surfaces and the conversations/messages surface are KEPT
--     unchanged — nothing is converted into the Issue entity.
--   * A Conversation may be associated with an Issue (nullable conversation_id);
--     Issue and Conversation remain distinct concepts.
--   * No new audit/history table: issue history uses the existing layered stack
--     (audit_trail + domain_events; ADR-V3-013 PROVISIONALLY DECIDED — no new
--     audit system, no duplicate history surfaces).
--
-- Lifecycle (spec §14.2): creation → assignment → priority/severity → SLA →
-- escalation → resolution → reopening → closure. issue_type/severity/status use
-- VARCHAR + CHECK (existing style — no new enums). Transition authority is an
-- API/backend concern (mirrors customer_factors D-cf-3); the DB enforces the
-- vocabulary and integrity constraints.
--
-- RLS (ADR-V3-010 — PROVISIONALLY DECIDED): the org-scope storey uses the fully
-- resolved RC2 helpers (is_org_member / is_org_consultant). Entity-scoped
-- access policies (is_entity_member) belong to ADR-V3-010 and are NOT created
-- here (same convention as V3M-1): entity-scoped issues are deny-by-default for
-- authenticated and remain service-role-accessible (CarbonTally internal) until
-- ADR-V3-010 resolves. Spec §14.4: entity issue surfaces are entity-scoped;
-- NEVER customer-visible — org-scope policies therefore exclude rows where
-- entity_id IS NOT NULL.
--
-- Safety:
--   * Additive and backward compatible; new table only; no existing table,
--     constraint or policy is modified.
--   * No factor data is touched (baseline DEFRA 7,029 · SEAI 20 · TOTAL 7,049).
-- Idempotent: CREATE TABLE IF NOT EXISTS, CREATE INDEX IF NOT EXISTS, guarded
-- FK, DROP POLICY IF EXISTS + CREATE POLICY, DROP TRIGGER IF EXISTS +
-- CREATE TRIGGER.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. issues (NEW)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.issues (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),

    -- Categorization / triage (VARCHAR + CHECK — no new enums).
    issue_type VARCHAR NOT NULL DEFAULT 'exception'
        CHECK (issue_type IN ('defect','exception','escalation')),
    severity VARCHAR NOT NULL DEFAULT 'medium'
        CHECK (severity IN ('low','medium','high','critical')),
    priority INTEGER NOT NULL DEFAULT 0 CHECK (priority >= 0),
    status VARCHAR NOT NULL DEFAULT 'open'
        CHECK (status IN ('open','in_progress','on_hold','escalated','resolved','closed')),

    -- Subject / description.
    title VARCHAR NOT NULL,
    description TEXT,

    -- Context (all nullable — CarbonTally-internal issues may carry none).
    organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES public.processing_entities(id) ON DELETE RESTRICT,
    work_item_id UUID REFERENCES public.manual_review_queue(id) ON DELETE RESTRICT,
    document_id UUID REFERENCES public.customer_documents(id) ON DELETE RESTRICT,
    batch_id UUID REFERENCES public.upload_batches(id) ON DELETE RESTRICT,
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE SET NULL,

    -- Ownership / assignment (loose UUIDs, matching manual_review_queue.assigned_to
    -- and user_feedback.assigned_to conventions; attribution history via the
    -- existing audit stack, ADR-V3-013).
    owner_id UUID,
    assignee_id UUID,

    -- SLA / escalation (reuse existing vocabulary).
    sla_deadline TIMESTAMPTZ,
    sla_breached BOOLEAN DEFAULT FALSE,
    escalation_level INTEGER NOT NULL DEFAULT 0 CHECK (escalation_level >= 0),
    escalated_at TIMESTAMPTZ,

    -- Resolution / closure / reopening.
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    reopened_at TIMESTAMPTZ,

    -- Audit / provenance.
    metadata JSONB,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE public.issues IS
    'First-class operational Issue domain (ADR-V3-009 — Option B). An Issue is the '
    'operational problem/exception/defect/escalation/resolution workflow — NOT a '
    'conversation, NOT a validation error, NOT a QC error, NOT user feedback. '
    'Conversations may be associated (conversation_id); context is optional '
    '(organization/customer, processing entity, work item, document, batch). Lifecycle: '
    'open → in_progress → on_hold/escalated → resolved → closed, with reopening. '
    'History via the existing audit stack (audit_trail/domain_events; ADR-V3-013).';
COMMENT ON COLUMN public.issues.issue_type IS
    'Categorization: defect / exception / escalation (VARCHAR + CHECK — no new enum).';
COMMENT ON COLUMN public.issues.severity IS
    'Operational impact: low / medium / high / critical.';
COMMENT ON COLUMN public.issues.status IS
    'Lifecycle: open → in_progress → on_hold/escalated → resolved → closed; a resolved '
    'issue may be reopened (status back to open, reopened_at records the event). '
    'Transition authority is an API/backend concern; the DB enforces the vocabulary.';
COMMENT ON COLUMN public.issues.organization_id IS
    'Owning customer organization (customer-facing issues; org-scoped RLS surface). '
    'NULL for CarbonTally-internal / entity-scoped issues.';
COMMENT ON COLUMN public.issues.entity_id IS
    'Processing Entity context (spec §14.2). Entity issue surfaces are entity-scoped and '
    'NEVER customer-visible (spec §14.4); entity-scoped access policies are deferred to '
    'ADR-V3-010 — entity rows are deny-by-default for authenticated until then. '
    'ON DELETE RESTRICT preserves attribution (V3M-1 convention).';
COMMENT ON COLUMN public.issues.work_item_id IS
    'Associated Work Item (manual_review_queue row; ADR-V3-012 work-item boundary). '
    'ON DELETE RESTRICT preserves attribution.';
COMMENT ON COLUMN public.issues.document_id IS
    'Associated document (customer_documents row). ON DELETE RESTRICT preserves attribution.';
COMMENT ON COLUMN public.issues.batch_id IS
    'Associated batch (upload_batches row). ON DELETE RESTRICT preserves attribution.';
COMMENT ON COLUMN public.issues.conversation_id IS
    'Associated Conversation (communication about the Issue). Issue and Conversation remain '
    'distinct concepts; SET NULL so a deleted conversation never destroys the Issue.';
COMMENT ON COLUMN public.issues.owner_id IS
    'Accountable owner (staff/entity worker/Customer Service depending on surface; loose UUID '
    'matching existing assignment conventions).';
COMMENT ON COLUMN public.issues.assignee_id IS
    'Current assignee (loose UUID matching manual_review_queue.assigned_to). Assignment '
    'attribution history lives in the existing audit stack (ADR-V3-013).';
COMMENT ON COLUMN public.issues.escalation_level IS
    'Escalation depth (0 = not escalated); reuses the manual_review_queue.escalation_level '
    'vocabulary concept.';
COMMENT ON COLUMN public.issues.resolved_at IS
    'When the issue entered the resolved state.';
COMMENT ON COLUMN public.issues.reopened_at IS
    'When a resolved/closed issue was reopened (status returns to open; spec §14.2 Reopening).';
COMMENT ON COLUMN public.issues.closed_at IS
    'When the issue was closed (final lifecycle state; soft — never hard-deleted).';


-- Tenant triage + relationship indexes (M7/customer_factors conventions).
CREATE INDEX IF NOT EXISTS idx_issues_organization_id
    ON public.issues (organization_id);

CREATE INDEX IF NOT EXISTS idx_issues_org_status
    ON public.issues (organization_id, status);

CREATE INDEX IF NOT EXISTS idx_issues_entity_id
    ON public.issues (entity_id);

CREATE INDEX IF NOT EXISTS idx_issues_assignee_id
    ON public.issues (assignee_id);

CREATE INDEX IF NOT EXISTS idx_issues_work_item_id
    ON public.issues (work_item_id);

-- updated_at maintenance trigger (RC2 006 convention — dynamic install covered
-- tables existing at RC2 time; this table is new, so the trigger is installed
-- here explicitly).
DROP TRIGGER IF EXISTS trg_set_updated_at_issues ON public.issues;
CREATE TRIGGER trg_set_updated_at_issues
    BEFORE UPDATE ON public.issues
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ---------------------------------------------------------------------------
-- 2. issues RLS
--    Org-scope storey (resolved RC2 helpers); entity-scope policies deferred
--    to ADR-V3-010 (V3M-1 convention). Spec §14.4: entity issue surfaces are
--    entity-scoped; NEVER customer-visible.
-- ---------------------------------------------------------------------------
ALTER TABLE public.issues ENABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE public.issues TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.issues TO authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.issues FROM authenticated;

-- SELECT: org member OR authorised consultant, customer-facing issues ONLY
-- (entity-scoped issues are excluded — never customer-visible; service-role /
-- CarbonTally-internal access until ADR-V3-010).
DROP POLICY IF EXISTS issues_select_own ON public.issues;
CREATE POLICY issues_select_own ON public.issues
    FOR SELECT TO authenticated
    USING (
        (public.is_org_member(organization_id) OR public.is_org_consultant(organization_id))
        AND entity_id IS NULL
    );

-- INSERT: org member, customer-facing only (entity-scoped issue creation is
-- CarbonTally-internal via service_role until ADR-V3-010).
DROP POLICY IF EXISTS issues_insert_own ON public.issues;
CREATE POLICY issues_insert_own ON public.issues
    FOR INSERT TO authenticated
    WITH CHECK (
        public.is_org_member(organization_id)
        AND entity_id IS NULL
    );

-- UPDATE: org member, customer-facing only.
DROP POLICY IF EXISTS issues_update_own ON public.issues;
CREATE POLICY issues_update_own ON public.issues
    FOR UPDATE TO authenticated
    USING (
        public.is_org_member(organization_id)
        AND entity_id IS NULL
    )
    WITH CHECK (
        public.is_org_member(organization_id)
        AND entity_id IS NULL
    );

-- NO DELETE policy: issues are never hard-deleted (soft lifecycle via status;
-- resolution/closure and historical attribution are preserved).

-- ============================================================================
-- VERIFICATION CHECKLIST (V3M-5)
--   [ ] issues table exists (org/entity/work-item/document/batch/conversation context)
--   [ ] issue_type/severity/status CHECKs + priority/escalation_level CHECKs present
--   [ ] FKs: organization CASCADE; entity/work_item/document/batch RESTRICT;
--       conversation SET NULL
--   [ ] Indexes: organization_id, org_status, entity_id, assignee_id, work_item_id
--   [ ] RLS enabled; service_role ALL; authenticated DML (no TRUNCATE);
--       SELECT = org member OR consultant AND entity_id IS NULL; INSERT/UPDATE =
--       org member AND entity_id IS NULL; NO DELETE policy
--   [ ] No entity-scoped policies created (deferred to ADR-V3-010 — V3M-1 convention)
--   [ ] trg_set_updated_at_issues installed
--   [ ] conversations / user_feedback / qc_checks / qc_errors untouched (distinct)
--   [ ] No new audit/history table (existing audit_trail/domain_events reused — ADR-V3-013)
--   [ ] emission_factors & customer_factors untouched (7,049 baseline preserved)
--   [ ] Re-running this file is a no-op
-- ============================================================================

