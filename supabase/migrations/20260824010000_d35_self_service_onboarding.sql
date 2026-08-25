-- ============================================================================
-- D35 — Self-service customer onboarding (additive, idempotent)
-- ----------------------------------------------------------------------------
-- D34 P1 #1: a completely new customer must be able to discover CarbonTally,
-- sign up, create/adopt an organization, become OWNER and enter the V3
-- customer workspace WITHOUT CarbonTally staff manually provisioning the
-- account.
--
-- The D19 existing-data discovery flow stays INTACT. This migration only makes
-- ``data_discovery_requests`` able to represent a PRE-ORG-CREATION
-- (self-service onboarding) request, so a brand-new customer with no
-- organization can run "ORGANIZATION CHECK -> POTENTIAL EXISTING DATA ->
-- VERIFICATION -> USE ALL / PARTIAL / DISCARD" BEFORE creating an org.
--
-- Changes (all additive / idempotent / RLS-safe):
--
-- 1. ``data_discovery_requests.organization_id`` becomes NULLABLE. A NULL
--    value marks an onboarding request created by an authenticated user who
--    does not (yet) belong to any organization. Existing requests are
--    untouched (their organization_id stays set).
--
-- 2. ``data_discovery_requests.created_by`` records the authenticated actor
--    who initiated an onboarding (organization_id IS NULL) request. That
--    actor is the only user allowed to verify the request and choose an
--    adoption outcome for it — a cross-user access guard in the API layer.
--
-- 3. A partial unique index keeps at most one live (pending_verification /
--    verified) onboarding request per candidate organisation, preventing
--    duplicate onboarding requests from the same no-org customer.
--
-- No destructive change. No data deleted. No RLS policy altered.
-- ============================================================================

ALTER TABLE public.data_discovery_requests
    ALTER COLUMN organization_id DROP NOT NULL;

ALTER TABLE public.data_discovery_requests
    ADD COLUMN IF NOT EXISTS created_by UUID;

CREATE UNIQUE INDEX IF NOT EXISTS uq_data_discovery_requests_onboarding_candidate
    ON public.data_discovery_requests (candidate_organization_id)
    WHERE organization_id IS NULL AND status IN ('pending_verification', 'verified');

COMMENT ON COLUMN public.data_discovery_requests.organization_id IS
    'D35: nullable — NULL marks a pre-org-creation (self-service onboarding) '
    'discovery request initiated before the customer creates/adopts an org.';

COMMENT ON COLUMN public.data_discovery_requests.created_by IS
    'D35: the authenticated user who initiated an onboarding (organization_id '
    'IS NULL) discovery request; only that user may verify it and choose an '
    'adoption outcome (USE ALL / PARTIAL / DISCARD).';

-- ---------------------------------------------------------------------------
-- 4. auth.users -> public.users sync (self-service membership FK)
-- ---------------------------------------------------------------------------
-- ``organization_members.user_id`` REFERENCES ``public.users(id)``. A new
-- Supabase Auth signup lives in ``auth.users`` only — without this sync the
-- first server-side membership insert (self-service org creation / D19
-- adoption / invitation) would violate the FK. The trigger runs SECURITY
-- DEFINER as the migration owner (postgres) and NEVER blocks auth signup:
-- sync failures are swallowed so a row-sync problem can never prevent a
-- customer from authenticating.
CREATE OR REPLACE FUNCTION public.sync_auth_user_to_public_users()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.users (
        id, email, first_name, last_name, is_active, email_verified,
        created_at, updated_at
    )
    VALUES (
        NEW.id,
        COALESCE(NEW.email, ''),
        NULLIF(NEW.raw_user_meta_data ->> 'full_name', ''),
        NULLIF(NEW.raw_user_meta_data ->> 'last_name', ''),
        TRUE, TRUE, NOW(), NOW()
    )
    ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email;
    RETURN NEW;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NEW;  -- never block authentication
END;
$$;

-- The trigger is only meaningful when the Supabase Auth schema is present
-- (main app database). The dedicated ``carbontally_test`` integration DB has
-- no ``auth`` schema — the guard makes the migration idempotent everywhere.
DO $d35$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'auth' AND tablename = 'users') THEN
        DROP TRIGGER IF EXISTS trg_sync_auth_user_to_public_users ON auth.users;
        CREATE TRIGGER trg_sync_auth_user_to_public_users
            AFTER INSERT ON auth.users
            FOR EACH ROW
            EXECUTE FUNCTION public.sync_auth_user_to_public_users();
    END IF;
END
$d35$;

COMMENT ON FUNCTION public.sync_auth_user_to_public_users() IS
    'D35: mirror newly-created Supabase Auth users into public.users so the '
    'organization_members.user_id FK (-> public.users) holds for self-service '
    'customers. Additive and idempotent; sync failures never block signup.';

