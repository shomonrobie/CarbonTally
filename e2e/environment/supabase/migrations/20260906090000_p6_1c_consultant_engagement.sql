-- ============================================================================
-- P6-1C — Consultant Engagement Confirmation for Pre-existing Organisations
-- ----------------------------------------------------------------------------
-- Additive + idempotent. Extends `consultant_clients` (the single relationship
-- model — reused, NOT duplicated) so that a consultant requesting an
-- ALREADY-existing customer organisation starts as `status='pending'` and only
-- becomes `active` after an authorised customer representative ACCEPTS.
--
-- * relationship_origin distinguishes:
--     - `legacy`                      : rows predating P6-1C (kept as ratified)
--     - `consultant_created_customer` : firm CREATED the org (Case A — active
--       via the approved provisioning flow, no second acceptance required)
--     - `engagement_request`          : firm requested an EXISTING org
--       (Case B — inserted pending; customer acceptance is the boundary)
-- * engagement_requested_at / engagement_decided_by / engagement_decided_at
--   preserve lifecycle actor/time provenance.
-- * Only `status='active'` grants consultant access (D15 `is_org_consultant`
--   and `_authorized_client_org` unchanged) — pending/rejected never grant.
-- * RLS hardening: authenticated INSERT/UPDATE on `consultant_clients` are
--   DROPPED. Previously `cc_insert_own_firm` (any `can_manage_clients` member)
--   could insert an ACTIVE grant for any org and `cc_update_own_firm` could
--   flip status directly — both would bypass the engagement boundary. SELECT
--   (own firm) and DELETE (revoker role / customer owner-admin severance)
--   policies are preserved. All relationship writes now run through the
--   server-authoritative API (service role), which enforces the P6-1C policy.
-- ============================================================================

ALTER TABLE public.consultant_clients
    ADD COLUMN IF NOT EXISTS relationship_origin TEXT NOT NULL DEFAULT 'legacy',
    ADD COLUMN IF NOT EXISTS engagement_requested_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS engagement_decided_by UUID,
    ADD COLUMN IF NOT EXISTS engagement_decided_at TIMESTAMPTZ;

-- Status vocabulary constraint (idempotent). Existing rows use a subset of the
-- new vocabulary (the live column also carries the pre-existing ``onboarding``
-- state used by the firm-provisioning flow), so the CHECK must be additive.
DO $p6_1c$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'consultant_clients_engagement_status_check'
          AND conrelid = 'public.consultant_clients'::regclass
    ) THEN
        ALTER TABLE public.consultant_clients
            ADD CONSTRAINT consultant_clients_engagement_status_check
            CHECK (status IN ('pending', 'active', 'rejected',
                              'suspended', 'ended', 'inactive',
                              'onboarding'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'consultant_clients_relationship_origin_check'
          AND conrelid = 'public.consultant_clients'::regclass
    ) THEN
        ALTER TABLE public.consultant_clients
            ADD CONSTRAINT consultant_clients_relationship_origin_check
            CHECK (relationship_origin IN ('legacy',
                                           'consultant_created_customer',
                                           'engagement_request'));
    END IF;
END
$p6_1c$;

COMMENT ON COLUMN public.consultant_clients.relationship_origin IS
    'P6-1C: legacy | consultant_created_customer (Case A — firm created the '
    'org) | engagement_request (Case B — pre-existing org, customer acceptance '
    'required). Only active grants access (D15).';
COMMENT ON COLUMN public.consultant_clients.engagement_requested_at IS
    'P6-1C: when the consultant requested the engagement (Case B).';
COMMENT ON COLUMN public.consultant_clients.engagement_decided_by IS
    'P6-1C: authenticated actor who accepted/rejected the engagement (server-'
    'authoritative; never a client-supplied value).';
COMMENT ON COLUMN public.consultant_clients.engagement_decided_at IS
    'P6-1C: when the engagement was accepted/rejected.';

-- RLS hardening: no authenticated INSERT/UPDATE on consultant_clients.
-- All relationship writes go through the server-authoritative API (service
-- role), which enforces the P6-1C policy. Drop every authenticated-write
-- policy on the live schema:
--   * cc_insert_own_firm / cc_update_own_firm  (earlier legacy names)
--   * consultant_clients_tenant_insert — NO qualifier: ANY authenticated
--     user could insert a row (even status='active') for any organisation.
--     This is the pre-1C "grant access by naming an org id" bypass.
--   * consultant_clients_tenant_update — any org member could flip a row
--     (e.g. pending -> active) without the owner/admin acceptance boundary.
-- SELECT (own firm + tenant read) and DELETE (firm revoker + customer
-- owner/admin tenant severance) policies remain in force.
DROP POLICY IF EXISTS cc_insert_own_firm ON public.consultant_clients;
DROP POLICY IF EXISTS consultant_clients_tenant_insert ON public.consultant_clients;
DROP POLICY IF EXISTS consultant_clients_tenant_update ON public.consultant_clients;
