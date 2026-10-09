-- ============================================================================
-- CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — client access profile, product mode,
-- relationship requests and retention policy.
--
-- Task:   CT-CONSULTANT-MODEL-IMPLEMENTATION-03
-- Source: docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md
--           §8   client access-profile model (F-3)
--           §6.1/§6.2/§8.4  PROFILE = CEILING; resolution order; profile x mode
--           §12  branding contract (PO-3A/PO-3B) — mode caps presentation
--           §14/§15 termination + post-relationship retained read-only (F-4)
--           §19 OQ-1/OQ-2/OQ-3  (now BINDING: relationship requests; 7-year
--                                configurable retention; OFF-client support path)
--           §20.1 AC-F-3..AC-F-6, AC-F-14, AC-F-16
--         CT-CONSULTANT-PO-CONSOLIDATION-01 §4 (PO-1 mode request semantics)
--
-- SAFETY
--   * Additive + idempotent. No RLS policy is weakened, dropped or disabled.
--   * The two new request tables are RLS-enabled with NO policies
--     (deny-by-default, service-role API only) — the same pattern as
--     public.data_discovery_requests.
--   * Deny-by-default: the client access profile defaults to 'off' and the
--     product mode backfill only ever PRESERVES an already-de-facto mode.
--   * No Organisation is deleted or cloned anywhere.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. consultant_clients — the CLIENT ACCESS PROFILE (F-3) + PO-10 retention.
-- ---------------------------------------------------------------------------
ALTER TABLE public.consultant_clients
    ADD COLUMN IF NOT EXISTS client_access_profile TEXT NOT NULL DEFAULT 'off',
    ADD COLUMN IF NOT EXISTS retained_read_only BOOLEAN NOT NULL DEFAULT false;

DO $ct03_profile$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'consultant_clients_access_profile_check'
          AND conrelid = 'public.consultant_clients'::regclass
    ) THEN
        ALTER TABLE public.consultant_clients
            ADD CONSTRAINT consultant_clients_access_profile_check
            CHECK (client_access_profile IN
                   ('off', 'read_only', 'collaborative', 'managed'));
    END IF;
END
$ct03_profile$;

COMMENT ON COLUMN public.consultant_clients.client_access_profile IS
    'CT03 (F-3, §8.1): the Plane C CEILING — off | read_only | collaborative | '
    'managed. Set by the consultant firm (CAP-MANAGE-CLIENTS), enforced '
    'SERVER-SIDE on every client-plane read and write. Deny-by-default: new and '
    'pre-existing relationships start at ''off'' so nothing is granted by '
    'omission. The profile is a CEILING, never a grant (§6.1).';

COMMENT ON COLUMN public.consultant_clients.retained_read_only IS
    'CT03 (F-4, PO-10/§15): when true AND the relationship status is '
    'ended/terminated, the client retains READ-ONLY historical access to their '
    'own data. The relationship is never deleted, the Organisation.id never '
    'changes and no data is migrated. The retention DURATION is governed by the '
    'configurable policy (system_settings.consultant_relationship_retention), '
    'never hard-coded here.';

-- Existing relationships are NOT silently granted a profile: no client plane
-- existed before CT03 (F-7/F-8), so 'off' is not a regression of any shipped
-- feature, and deny-by-default is the ratified stance (§6.5 FM-1). A consultant
-- must grant a profile explicitly through the firm administration surface.
COMMENT ON TABLE public.consultant_clients IS
    'Consultant-client relationships. CT03 adds the client access profile and '
    'the PO-10 retained-read-only flag. Only status=active grants consultant '
    'access (D15).';

-- ---------------------------------------------------------------------------
-- 2. consultant_profiles.commercial_mode — the PRODUCT MODE (F-5, PO-4/PO-5).
-- ---------------------------------------------------------------------------
ALTER TABLE public.consultant_profiles
    ADD COLUMN IF NOT EXISTS commercial_mode TEXT NOT NULL DEFAULT 'standard';

DO $ct03_mode$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'consultant_profiles_commercial_mode_check'
          AND conrelid = 'public.consultant_profiles'::regclass
    ) THEN
        ALTER TABLE public.consultant_profiles
            ADD CONSTRAINT consultant_profiles_commercial_mode_check
            CHECK (commercial_mode IN ('standard', 'co_branded', 'white_label'));
    END IF;
END
$ct03_mode$;

COMMENT ON COLUMN public.consultant_profiles.commercial_mode IS
    'CT03 (F-5, §5.2/§6.1): the firm PRODUCT MODE — standard | co_branded | '
    'white_label. CarbonTally Admin-controlled (PO-5); a consultant may only '
    'REQUEST a change (PO-1), never write it. The MODE is authoritative over the '
    'legacy white_label_enabled / co_branding_enabled flags (IMPL-3 / BR-5), '
    'which are capped at presentation and never destroyed. Grants no capability.';

-- Backfill ONLY to preserve an already-de-facto mode (IMPL-3): a firm that was
-- white-label keeps white-label; a co-branded firm keeps co-branded. Anything
-- else stays the deny-by-default 'standard'. The legacy flags are untouched.
UPDATE public.consultant_profiles
   SET commercial_mode = CASE
           WHEN white_label_enabled IS TRUE THEN 'white_label'
           WHEN co_branding_enabled IS TRUE THEN 'co_branded'
           ELSE 'standard'
       END
 WHERE commercial_mode = 'standard'
   AND (white_label_enabled IS TRUE OR co_branding_enabled IS TRUE);

-- ---------------------------------------------------------------------------
-- 3. consultant_relationship_requests — OQ-1 / OQ-3 (now BINDING).
--    A client (or, for an OFF client, an authorised registered contact via the
--    CarbonTally support path) REQUESTS a change of consultant or an end of the
--    relationship. A request NEVER destroys the relationship: the PO-7 state
--    machine (ACTIVE -> REQUESTED -> CONFIRMED -> TERMINATED/RETAINED) applies
--    only after confirmation. Non-destructive by construction.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.consultant_relationship_requests (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    consultant_id UUID REFERENCES public.consultant_profiles(id) ON DELETE SET NULL,
    -- change_consultant | end_relationship
    request_type TEXT NOT NULL,
    -- client | consultant | support  (WHO initiated, in what capacity)
    initiated_capacity TEXT NOT NULL,
    initiated_by UUID,
    contact_email TEXT,
    reason TEXT,
    -- requested | confirmed | cancelled | completed
    status TEXT NOT NULL DEFAULT 'requested',
    confirmed_by UUID,
    confirmed_at TIMESTAMPTZ,
    decided_by UUID,
    decided_at TIMESTAMPTZ,
    decision_note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT consultant_relationship_requests_type_check
        CHECK (request_type IN ('change_consultant', 'end_relationship')),
    CONSTRAINT consultant_relationship_requests_capacity_check
        CHECK (initiated_capacity IN ('client', 'consultant', 'support')),
    CONSTRAINT consultant_relationship_requests_status_check
        CHECK (status IN ('requested', 'confirmed', 'cancelled', 'completed'))
);

CREATE INDEX IF NOT EXISTS idx_consultant_relationship_requests_org
    ON public.consultant_relationship_requests (organization_id, status);

COMMENT ON TABLE public.consultant_relationship_requests IS
    'CT03 (OQ-1/OQ-3, PO-7, §14.1): an authenticated, authorised, confirmed and '
    'auditable REQUEST to change or end a consultant relationship. A request is '
    'never a destructive operation — the relationship is terminated only through '
    'the confirmed PO-7 state machine, which preserves the Organisation, its id '
    'and all history. Deny-by-default RLS (service-role API only).';
ALTER TABLE public.consultant_relationship_requests ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 4. consultant_mode_change_requests — PO-1 (B+D) mode-change REQUEST.
--    A mode change is a commercial transaction, not a settings toggle: the firm
--    REQUESTS, CarbonTally decides, effect at the billing/renewal boundary
--    unless CarbonTally approves an immediate transition.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.consultant_mode_change_requests (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    firm_id UUID NOT NULL REFERENCES public.consultant_profiles(id) ON DELETE CASCADE,
    requested_by UUID,
    current_mode TEXT NOT NULL,
    requested_mode TEXT NOT NULL,
    reason TEXT,
    -- requested | approved | rejected | cancelled
    status TEXT NOT NULL DEFAULT 'requested',
    decided_by UUID,
    decided_at TIMESTAMPTZ,
    decision_note TEXT,
    -- the billing/renewal boundary the change becomes effective at (PO-1)
    effective_at TIMESTAMPTZ,
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT consultant_mode_change_requests_status_check
        CHECK (status IN ('requested', 'approved', 'rejected', 'cancelled')),
    CONSTRAINT consultant_mode_change_requests_mode_check
        CHECK (current_mode IN ('standard', 'co_branded', 'white_label')
               AND requested_mode IN ('standard', 'co_branded', 'white_label'))
);

CREATE INDEX IF NOT EXISTS idx_consultant_mode_change_requests_firm
    ON public.consultant_mode_change_requests (firm_id, status);

COMMENT ON TABLE public.consultant_mode_change_requests IS
    'CT03 (PO-1 B+D, §4.2/§6.5): a mode-change REQUEST. Direct mode mutation by '
    'a consultant is rejected; CarbonTally Admin controls approval and the '
    'effective date (billing/renewal boundary unless immediate transition is '
    'explicitly approved). Records requester, current/requested mode, decision '
    'actor and effective date. Deny-by-default RLS (service-role API only).';
ALTER TABLE public.consultant_mode_change_requests ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 5. Retention policy (OQ-2 — now BINDING: 7-year default, Admin-configurable).
--    ONE authoritative source. NOT hard-coded into scattered business logic
--    (§24). Reuses the EXISTING Admin configuration architecture
--    (public.system_settings), which already carries the platform's other
--    retention settings (data_retention_days / document_retention_days /
--    audit_log_retention_days).
-- ---------------------------------------------------------------------------
INSERT INTO public.system_settings (setting_key, setting_value, setting_type, description)
VALUES (
    'consultant_relationship_retention',
    '{"years": 7, "retained_read_only": true, "legal_hold_blocks_deletion": true, "auto_delete_enabled": false}'::jsonb,
    'consultant_retention',
    'CT03 (OQ-2, PO-10): how long a consultant relationship''s Organisation data '
    'is retained after the relationship ends. Default = 7 years (PO decision). '
    'Configurable by CarbonTally Admin only. Retained read-only access is '
    'permitted while the policy allows; a legal hold overrides normal deletion. '
    'Auto-deletion execution is NOT enabled by this migration.'
)
ON CONFLICT (setting_key) DO NOTHING;

COMMENT ON COLUMN public.system_settings.setting_value IS
    'JSONB setting payload. CT03 adds the consultant_relationship_retention key '
    '(years / retained_read_only / legal_hold_blocks_deletion / '
    'auto_delete_enabled) — the single authoritative retention policy for the '
    'consultant relationship lifecycle (OQ-2).';



