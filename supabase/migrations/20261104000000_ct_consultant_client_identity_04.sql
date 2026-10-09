-- ============================================================================
-- CT-CONSULTANT-CLIENT-IDENTITY-04 — client-user invitation lifecycle (PD-1A)
-- and client-user role administration (PD-2A).
--
-- Task:   CT-CONSULTANT-CLIENT-IDENTITY-04
-- Source: docs/architecture/CT-CONSULTANT-PLATFORM-DECISION-REGISTER-02.md §2
--           PD-1A (A) — CarbonTally-controlled secure single-use invitation;
--                       consultant/client must not bypass it.
--           PD-2A (C) — dual authority with explicit boundaries; consultant may
--                       create/manage client users on the client's behalf within
--                       the permitted role boundary; creating a user grants no
--                       client-plane DATA access.
--         docs/architecture/CT-CONSULTANT-PLATFORM-FULL-IMPLEMENTATION-03.md
--
-- SAFETY
--   * Additive + idempotent. No column is dropped, renamed or retyped; every
--     new column is nullable so existing rows are untouched.
--   * public.user_invitations ALREADY exists (00000000000000_init_schema.sql)
--     and RLS is ALREADY enabled on it
--     (20260925000000_p8_rls_4b_group1_enablement.sql). This migration does NOT
--     add a permissive policy, does NOT weaken an existing one and does NOT
--     disable RLS — the table stays service-role-API only (deny-by-default).
--   * The invited ROLE is added as a first-class, CHECK-guarded column. Before
--     this migration the requested role was DISCARDED at the store (only an
--     optional ``role_id`` was kept), so acceptance could not create the
--     membership with the role the inviter was authorised to assign. No second
--     role vocabulary is introduced: the CHECK mirrors organization_members.role
--     exactly (owner/admin/member/viewer).
--   * Expiry is NEVER stored — it is derived from ``expires_at`` by the policy
--     module domain/client_identity.py. No scheduled job is required for an
--     expired invitation to be un-consumable.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. user_invitations — PD-1A provenance + role + acceptance/revocation trail.
-- ---------------------------------------------------------------------------
ALTER TABLE public.user_invitations
    ADD COLUMN IF NOT EXISTS role TEXT,
    ADD COLUMN IF NOT EXISTS invited_by_firm_id UUID,
    ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS accepted_by UUID,
    ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS revoked_by UUID;

DO $ct04_role$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'user_invitations_role_check'
          AND conrelid = 'public.user_invitations'::regclass
    ) THEN
        ALTER TABLE public.user_invitations
            ADD CONSTRAINT user_invitations_role_check
            CHECK (role IS NULL OR role IN ('owner', 'admin', 'member', 'viewer'));
    END IF;
END
$ct04_role$;

DO $ct04_firm_fk$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'user_invitations_invited_by_firm_id_fkey'
          AND conrelid = 'public.user_invitations'::regclass
    ) THEN
        ALTER TABLE public.user_invitations
            ADD CONSTRAINT user_invitations_invited_by_firm_id_fkey
            FOREIGN KEY (invited_by_firm_id)
            REFERENCES public.consultant_profiles(id) ON DELETE SET NULL;
    END IF;
END
$ct04_firm_fk$;

COMMENT ON COLUMN public.user_invitations.role IS
    'CT04 (PD-1A/PD-2A): the CLIENT organisation role the invitation was created '
    'for (owner/admin/member/viewer) — the same vocabulary as '
    'organization_members.role. On acceptance this role is used to create the '
    'membership; it is the role the inviter was AUTHORISED to assign. NULL for '
    'legacy rows created before CT04 (their requested role was discarded).';

COMMENT ON COLUMN public.user_invitations.invited_by_firm_id IS
    'CT04 (PD-2A): when a CONSULTANT firm created the invitation on the client''s '
    'behalf, the consultant_profiles.id of that firm. NULL when the client '
    'Organisation self-invited. Provenance only — it grants the consultant NO '
    'client-plane data access.';

COMMENT ON COLUMN public.user_invitations.accepted_at IS
    'CT04 (PD-1A): when the single-use invitation was consumed. Set by an atomic '
    'conditional UPDATE (status pending + unexpired); a second attempt matches '
    'no row and is refused.';

COMMENT ON COLUMN public.user_invitations.accepted_by IS
    'CT04 (PD-1A): the accepting user''s auth id (public.users.id).';

COMMENT ON COLUMN public.user_invitations.revoked_at IS
    'CT04 (PD-1A): when the invitation was revoked before acceptance.';

COMMENT ON COLUMN public.user_invitations.revoked_by IS
    'CT04 (PD-1A): the actor (client owner/admin or consultant) that revoked it.';

COMMENT ON COLUMN public.user_invitations.status IS
    'CT04 (PD-1A): durable lifecycle state — pending | accepted | revoked. The '
    'fourth effective state, EXPIRED, is derived from expires_at (pending AND '
    'expires_at <= now) and is intentionally never stored, so no scheduled job '
    'is required for expiry to be authoritative.';

-- ---------------------------------------------------------------------------
-- 2. Lookup index for the org-scoped pending-invitation scan used by the admin
--    list surfaces. ``token`` is already UNIQUE (btree) — no new token index.
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_user_invitations_org_status
    ON public.user_invitations (organization_id, status);
