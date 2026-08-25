-- ============================================================================
-- CarbonTally V3 — D27 / D19 Customer Lifecycle + White-Label + Messaging
-- File: 20260822010000_d27_d19_customer_lifecycle.sql
--
-- Implements the D19 final commercial model (APPROVED 2026-08-20):
--   1. Consultant-client relationship LIFECYCLE: ACTIVE / SUSPENDED / ENDED.
--      Enforcement: RLS `is_org_consultant` + API `ensure_consultant_org_access`
--      already gate on `consultant_clients.status = 'active'` (D15); this
--      migration adds lifecycle columns so SUSPENDED / ENDED transitions are
--      first-class and auditable.
--   2. CUSTOMER-INITIATED DIRECT ONBOARDING + EXISTING DATA DISCOVERY.
--      `data_discovery_requests` carries the discovery lifecycle
--      (pending_verification -> verified -> adopted | discarded). Adoption is
--      IN-PLACE: the existing organizations.id becomes the direct-customer org
--      (no data copy); DISCARD never deletes data.
--   3. WHITE-LABEL completion: consultant_custom_domains + consultant_senders.
--      A domain/sender NEVER grants authorization by itself.
--   4. MESSAGING RLS fix (D26 audit §42): conversation_participants had ZERO
--      policies (deny-all). Add recursion-safe SELECT access. Processing Entity
--      staff get NO messaging access (D18 boundary preserved).
--
-- Safety: additive + idempotent; new tables RLS-enabled with no policies
-- (deny-by-default, service-role API only); no generic tenant abstraction.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. organizations.customer_type (informational — NEVER authorization)
-- ---------------------------------------------------------------------------
ALTER TABLE public.organizations
    ADD COLUMN IF NOT EXISTS customer_type TEXT;

COMMENT ON COLUMN public.organizations.customer_type IS
    'D27/D19 informational label: ''direct'' (Direct CarbonTally Customer) | '
    '''consultant_managed'' | NULL (unknown). NEVER used as an authorization '
    'source — access is always derived from memberships/grants/RLS.';

-- ---------------------------------------------------------------------------
-- 2. consultant_clients lifecycle columns (ACTIVE / SUSPENDED / ENDED)
-- ---------------------------------------------------------------------------
ALTER TABLE public.consultant_clients
    ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ended_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ended_by UUID,
    ADD COLUMN IF NOT EXISTS lifecycle_updated_at TIMESTAMPTZ;

COMMENT ON COLUMN public.consultant_clients.status IS
    'D27/D19 relationship lifecycle: active (authorized) | suspended (no '
    'temporary access) | ended (no access; historical provenance only) | '
    'inactive (legacy soft-deactivate). RLS is_org_consultant and API '
    'ensure_consultant_org_access grant access ONLY when status = ''active''.';
COMMENT ON COLUMN public.consultant_clients.suspended_at IS
    'When the relationship was last suspended (NULL when never suspended).';
COMMENT ON COLUMN public.consultant_clients.ended_at IS
    'When the relationship was ended (NULL while active).';
COMMENT ON COLUMN public.consultant_clients.ended_by IS
    'Who ended the relationship (auth user id; provenance, not authorization).';

CREATE INDEX IF NOT EXISTS idx_consultant_clients_lifecycle
    ON public.consultant_clients (consultant_id, status);

-- ---------------------------------------------------------------------------
-- 3. data_discovery_requests — customer-initiated existing-data adoption
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.data_discovery_requests (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    -- The requesting (new) organisation — the customer's signup org.
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    -- The existing organisation that may already hold matching data.
    candidate_organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    -- pending_verification | verified | adopted | discarded | expired | rejected
    status TEXT NOT NULL DEFAULT 'pending_verification',
    -- email (verification code to the candidate org's registered contact) |
    -- staff_mediated (CarbonTally internal admin confirms, operational fallback)
    verification_method TEXT NOT NULL DEFAULT 'email',
    verification_code_hash TEXT,
    verification_code_expires_at TIMESTAMPTZ,
    verification_attempts INTEGER NOT NULL DEFAULT 0,
    verified_at TIMESTAMPTZ,
    verified_by UUID,
    -- use_all | partial | discard
    adoption_choice TEXT,
    -- category selection for PARTIAL adoption (provenance only — no unsafe
    -- partial-copy semantics are performed; D19 §8)
    adoption_scope JSONB,
    adopted_at TIMESTAMPTZ,
    adopted_by UUID,
    discarded_at TIMESTAMPTZ,
    discarded_by UUID,
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (organization_id, candidate_organization_id)
);

CREATE INDEX IF NOT EXISTS idx_data_discovery_requests_candidate
    ON public.data_discovery_requests (candidate_organization_id);
CREATE INDEX IF NOT EXISTS idx_data_discovery_requests_status
    ON public.data_discovery_requests (status);

COMMENT ON TABLE public.data_discovery_requests IS
    'D27/D19: customer-initiated existing-data discovery/adoption requests. '
    'Deny-by-default RLS — service-role API only. A request NEVER grants access '
    'by itself; verification proves control of the candidate org registered '
    'contact, adoption creates real organization membership.';
ALTER TABLE public.data_discovery_requests ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 4. consultant_custom_domains — white-label custom-domain lifecycle
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.consultant_custom_domains (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    consultant_id UUID NOT NULL REFERENCES public.consultant_profiles(id) ON DELETE CASCADE,
    domain TEXT NOT NULL,
    -- pending | verified | active | removed_suspended
    status TEXT NOT NULL DEFAULT 'pending',
    verification_token TEXT NOT NULL,
    verified_at TIMESTAMPTZ,
    removed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (consultant_id, domain)
);

CREATE INDEX IF NOT EXISTS idx_consultant_custom_domains_consultant
    ON public.consultant_custom_domains (consultant_id);

COMMENT ON TABLE public.consultant_custom_domains IS
    'D27/D19 white-label: a consultant''s custom portal domain. PENDING -> '
    '(DNS TXT verification) -> VERIFIED -> ACTIVE; removal -> '
    'REMOVED_SUSPENDED. A domain NEVER grants authorization — branding is '
    'always derived from the authenticated consultant relationship. '
    'Deny-by-default RLS (service-role API only).';
ALTER TABLE public.consultant_custom_domains ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 5. consultant_senders — optional verified custom email senders (Resend)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.consultant_senders (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    consultant_id UUID NOT NULL REFERENCES public.consultant_profiles(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    domain TEXT,
    -- pending | verified | removed
    status TEXT NOT NULL DEFAULT 'pending',
    verification_token TEXT NOT NULL,
    verified_at TIMESTAMPTZ,
    removed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (consultant_id, email)
);

CREATE INDEX IF NOT EXISTS idx_consultant_senders_consultant
    ON public.consultant_senders (consultant_id);

COMMENT ON TABLE public.consultant_senders IS
    'D27/D19 white-label email: an optional verified From address for a '
    'consultant firm (e.g. reports@consultant-domain.com). Resend verifies the '
    'underlying domain; only VERIFIED senders may be used as a From address. '
    'Arbitrary From addresses are never allowed. Deny-by-default RLS.';
ALTER TABLE public.consultant_senders ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 6. Messaging RLS — recursion-safe participant access (D26 audit §42)
-- ---------------------------------------------------------------------------
-- conversation_participants currently has ZERO policies (deny-all). Add
-- recursion-safe SELECT access: the participant themselves OR an org member /
-- active-grant consultant of the conversation's organisation. Entity staff are
-- intentionally excluded (D18 boundary — no entity policies are created).

CREATE OR REPLACE FUNCTION public.is_conversation_participant(p_conversation uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public'
AS $$
    SELECT EXISTS (
        SELECT 1
          FROM public.conversation_participants cp
         WHERE cp.conversation_id = p_conversation
           AND cp.user_id = auth.uid()
           AND coalesce(cp.is_active, true) = true
    );
$$;

CREATE OR REPLACE FUNCTION public.can_view_conversation_participants(p_conversation uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'public'
AS $$
    SELECT (
        EXISTS (
            SELECT 1
              FROM public.conversations c
             WHERE c.id = p_conversation
               AND c.organization_id IS NOT NULL
               AND (public.is_org_member(c.organization_id)
                    OR public.is_org_consultant(c.organization_id))
        )
        OR public.is_conversation_participant(p_conversation)
    );
$$;

DROP POLICY IF EXISTS conversation_participants_select ON public.conversation_participants;
CREATE POLICY conversation_participants_select
    ON public.conversation_participants
    FOR SELECT TO authenticated
    USING (public.can_view_conversation_participants(conversation_id));

-- Participants may mark their own participation active/inactive (join/leave).
DROP POLICY IF EXISTS conversation_participants_update_own ON public.conversation_participants;
CREATE POLICY conversation_participants_update_own
    ON public.conversation_participants
    FOR UPDATE TO authenticated
    USING (public.is_conversation_participant(conversation_id))
    WITH CHECK (user_id = auth.uid());

COMMENT ON TABLE public.conversation_participants IS
    'D27/D19: conversation participants. SELECT = participant OR org member / '
    'active-grant consultant of the conversation org. Processing Entity staff '
    'never participate (no entity policy).';

-- ============================================================================
-- VERIFICATION CHECKLIST (D27)
--   [ ] organizations.customer_type added (informational)
--   [ ] consultant_clients lifecycle columns added + index
--   [ ] data_discovery_requests created + RLS enabled (no policies = deny-all)
--   [ ] consultant_custom_domains created + RLS enabled (deny-all)
--   [ ] consultant_senders created + RLS enabled (deny-all)
--   [ ] is_conversation_participant / can_view_conversation_participants
--       SECURITY DEFINER helpers (Phase 9 recursion-safe pattern)
--   [ ] conversation_participants SELECT + UPDATE-own policies present
--   [ ] Entity staff messaging remains denied (no entity policies created)
--   [ ] Existing rows untouched; no factor data touched
--   [ ] Re-running this file is a no-op
-- ============================================================================

