-- ============================================================================
-- CarbonTally — F-039-1 Activity Clarification
-- File: 20260928000000_p8_fs_activity_clarifications.sql
--
-- PURPOSE
--   First-class persistence for AUTHORISED ACTIVITY CLARIFICATION: a user clarifies the
--   MEANING of an extracted activity (never an emission-factor id); the SAME
--   factor-selection policy is re-run with the clarification as additional evidence and the
--   resulting policy outcome is recorded here — separately from the source document
--   evidence, which this table never overwrites.
--
-- CONVENTIONS FOLLOWED (traced from existing migrations, not invented)
--   * RLS is ENABLEd on the new table (deny-by-default floor) —
--     cf. 20260807070000_add_new_table_rls.sql · 20260803000000_rc2_rls.sql.
--   * Explicit GRANTs are required on this stack: service_role ALL; authenticated DML only
--     (TRUNCATE/TRIGGER/REFERENCES/MAINTAIN REVOKEd); anon gets nothing.
--   * Policies reuse the existing SECURITY DEFINER helpers
--       public.is_org_member(uuid)      — organisation membership (customer users)
--       public.is_org_consultant(uuid)  — authorised consultant access to a client org
--     following the frozen tenant-table matrix:
--       SELECT : is_org_member(organization_id) OR is_org_consultant(organization_id)
--       INSERT : WITH CHECK (is_org_member(organization_id))
--       UPDATE : USING + WITH CHECK (is_org_member(organization_id))
--       DELETE : USING (is_org_member(organization_id))
--     ⇒ an organisation reaches only its own rows; a consultant reaches only the client
--       organisations the existing helper already authorises; a consultant CLIENT is a
--       member of its own organisation and is confined to it by the same predicate.
--       No new admin bypass is introduced.
--   * Idempotent: ENABLE RLS is idempotent, GRANT re-application is a no-op, and every
--     policy uses DROP POLICY IF EXISTS + CREATE POLICY.
--
-- STATUS: created in the repository, NOT executed in any environment.
--   DELIBERATE, DOCUMENTED LIMITATION: item_key/batch_key carry the parent identity as text
--   because the batch/item table names were not confirmed within this window; binding them
--   as real FKs is a one-line follow-up once confirmed.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.activity_clarifications (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_key         text NOT NULL,
    batch_key            text,
    item_key             text,
    organization_id      uuid REFERENCES public.organizations(id) ON DELETE CASCADE,
    original_activity    text NOT NULL,
    source_evidence_ref  text,
    clarification        text NOT NULL,
    clarification_type   text NOT NULL DEFAULT 'semantic_activity',
    policy_input         text NOT NULL,
    outcome_status       text NOT NULL,
    selected_factor_id   uuid REFERENCES public.emission_factors(id) ON DELETE SET NULL,
    selected_factor_name text,
    factor_set           text,
    factor_source        text,
    reporting_year       integer,
    unit                 text,
    scope                text,
    eligible_group_count integer NOT NULL DEFAULT 0,
    eligible_groups      jsonb NOT NULL DEFAULT '[]'::jsonb,
    actor_id             uuid,
    actor_scope          text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT activity_clarifications_unique
        UNIQUE (activity_key, original_activity, clarification)
);

CREATE INDEX IF NOT EXISTS activity_clarifications_org_created_idx
    ON public.activity_clarifications (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS activity_clarifications_activity_idx
    ON public.activity_clarifications (activity_key);

ALTER TABLE public.activity_clarifications ENABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE public.activity_clarifications TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.activity_clarifications TO authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN
    ON TABLE public.activity_clarifications FROM authenticated;

DROP POLICY IF EXISTS activity_clarifications_tenant_select ON public.activity_clarifications;
CREATE POLICY activity_clarifications_tenant_select ON public.activity_clarifications
    FOR SELECT TO authenticated
    USING (public.is_org_member(organization_id) OR public.is_org_consultant(organization_id));

DROP POLICY IF EXISTS activity_clarifications_tenant_insert ON public.activity_clarifications;
CREATE POLICY activity_clarifications_tenant_insert ON public.activity_clarifications
    FOR INSERT TO authenticated
    WITH CHECK (public.is_org_member(organization_id));

DROP POLICY IF EXISTS activity_clarifications_tenant_update ON public.activity_clarifications;
CREATE POLICY activity_clarifications_tenant_update ON public.activity_clarifications
    FOR UPDATE TO authenticated
    USING (public.is_org_member(organization_id))
    WITH CHECK (public.is_org_member(organization_id));

DROP POLICY IF EXISTS activity_clarifications_tenant_delete ON public.activity_clarifications;
CREATE POLICY activity_clarifications_tenant_delete ON public.activity_clarifications
    FOR DELETE TO authenticated
    USING (public.is_org_member(organization_id));
