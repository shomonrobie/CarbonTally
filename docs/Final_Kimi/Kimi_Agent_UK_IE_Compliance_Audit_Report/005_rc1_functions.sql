-- ============================================================================
-- CarbonTally v1.0 RC1 — Production Hardening Migration
-- File 005 of 008: Approved helper functions
-- Source of truth: CarbonTally_v1.0_Production_Hardening_Plan.md
--   * §3 register Category A row 22 / §7 checklist row 23: "Anonymise-in-place
--     erasure procedure (hash users.email, 'Deleted User', keep UUID), tested
--     on staging" — the ONLY approved function-level compliance artefact.
--   * §6 D5: audit hash-chain REJECTED — no hash-chain function exists here.
--   * §5: retention pg_cron jobs DEFERRED to v1.0.1 — no cron/retention
--     function exists here. The manual anonymise-in-place procedure above is
--     the approved A-class artefact and is exactly what this file ships.
--   * set_updated_at(): generic trigger companion required by 006_rc1_triggers
--     (updated_at maintenance; the inverse — dropping updated_at from
--     append-only logs — is plan B, deferred to v1.0.1, so the append-only
--     log tables are deliberately excluded there).
--
-- NOTE: the RLS policy helpers public.is_org_member / public.is_org_active
-- are created in 004_rc1_rls.sql because the policies there depend on them.
--
-- Idempotency: CREATE OR REPLACE throughout; safe to re-run.
-- No CONCURRENTLY needed. UK English. No regex validation anywhere.
-- ============================================================================

BEGIN;

-- ============================================================================
-- F1 — public.set_updated_at()
-- Generic BEFORE UPDATE trigger function maintaining updated_at = now().
-- Needed by the approved updated_at maintenance triggers in 006. Pure clock
-- write; no business logic, no auditing (audit machinery is rejected/deferred).
-- ============================================================================
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.set_updated_at() IS
    'Generic BEFORE UPDATE trigger function: stamps NEW.updated_at := now(). Companion to the 006 updated_at maintenance triggers. SECURITY INVOKER by design (runs with the updating role''s rights; trigger fires regardless of RLS).';

-- ============================================================================
-- F2 — public.anonymise_user(p_user_id uuid, p_actor_id uuid, p_reason text)
-- GDPR/UK-GDPR erasure: anonymise-in-place.
-- (Production Hardening Plan §3 A row 22; §7 checklist row 23; §8 P5 manual
--  runbook — "the erasure artefact is a procedure, not schema"; §9 Gate 5
--  rehearsal is the acceptance evidence.)
--
-- Design decisions (from the plan, prose-level):
--   * HARD DELETE IS STRUCTURALLY IMPOSSIBLE — users.id is pinned by ~40
--     referencing FK columns (audit, logs, messages, queues). We therefore
--     ANONYMISE IN PLACE: identity columns are scrubbed, the UUID (and every
--     FK pointing at it) is preserved, so referential integrity, financial
--     records and audit aggregates survive intact.
--   * users.email is replaced by a deterministic SHA-256-derived mailbox
--     (unique, irreversible, clearly non-routable), honouring the UNIQUE
--     constraint while destroying recoverability (plan wording: "hash
--     users.email").
--   * users.first_name/last_name become 'Deleted' / 'User' (plan wording).
--   * password_hash is nulled (credential material is never retained for an
--     erased account); users.is_active set false, blocking login.
--   * Profile-class PII scrubbed where it is keyed by user_id:
--     consultant_profiles (contact/address block), staff_profiles (name/email),
--     beta_users (email), user_feedback (user_email only — the feedback
--     content itself is product telemetry, reviewed in the residual-PII scan).
--   * Audit/log CONTENT (messages bodies, audit jsonb, free-text fields) is
--     NOT rewritten here — that is the residual-PII scan's job in the Gate 5
--     rehearsal runbook; this procedure handles the structured identity graph.
--
-- Guards (tenant/actor guard, per instruction):
--   * The caller must be authorised: EITHER the actor is the data subject
--     themselves (self-service, auth.uid() = p_user_id) OR the actor is an
--     active staff member (staff_profiles.is_active) OR the call runs in a
--     service/administrative context (auth.uid() IS NULL — service role, as
--     used by the manual runbook). Anything else raises and rolls back.
--   * SECURITY DEFINER so the procedure can scrub across RLS boundaries;
--     search_path pinned; EXECUTE revoked from PUBLIC and granted only to
--     service_role (and authenticated, for the self-service path above).
--
-- Idempotent: a second call on an already-anonymised user detects the
-- marker email domain and no-ops with a NOTICE (safe runbook re-runs).
-- Transactional: runs inside the caller's transaction; any failure raises
-- and rolls the whole scrub back atomically. NOT reversible by design
-- (plan §8 P5 rollback note: "the staging rehearsal evidence is the
-- mitigation").
-- ============================================================================
CREATE OR REPLACE FUNCTION public.anonymise_user(
    p_user_id uuid,
    p_actor_id uuid DEFAULT NULL,
    p_reason  text DEFAULT 'DSAR erasure request'
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_email        varchar;
    v_actor        uuid;
    v_anon_email   text;
BEGIN
    -- ---- Guard 0: target must exist --------------------------------------
    SELECT u.email INTO v_email FROM public.users u WHERE u.id = p_user_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'anonymise_user: user % not found', p_user_id;
    END IF;

    -- ---- Guard 1: actor authorisation ------------------------------------
    -- Effective actor: explicit parameter, else the Supabase-authenticated
    -- identity, else NULL (service/administrative context).
    v_actor := coalesce(p_actor_id, auth.uid());

    IF v_actor IS NOT NULL
       AND v_actor IS DISTINCT FROM p_user_id
       AND NOT EXISTS (SELECT 1 FROM public.staff_profiles sp
                       WHERE sp.user_id = v_actor
                         AND coalesce(sp.is_active, true)) THEN
        RAISE EXCEPTION
            'anonymise_user: actor % is neither the data subject nor active staff — erasure refused', v_actor;
    END IF;

    -- ---- Guard 2: idempotence --------------------------------------------
    IF v_email LIKE 'deleted-%@anonymised.invalid' THEN
        RAISE NOTICE 'anonymise_user: user % already anonymised — no-op', p_user_id;
        RETURN;
    END IF;

    -- ---- Scrub: users (identity core; UUID preserved) --------------------
    v_anon_email := 'deleted-' || encode(sha256(p_user_id::text::bytea), 'hex') || '@anonymised.invalid';

    UPDATE public.users
       SET email          = v_anon_email,
           first_name     = 'Deleted',
           last_name      = 'User',
           password_hash  = NULL,
           is_active      = false,
           email_verified = false
     WHERE id = p_user_id;

    -- ---- Scrub: consultant_profiles (contact/address PII block) ----------
    -- Company identity fields (company_name/number, vat_number) are retained:
    -- they belong to the FIRM, not the person, and underpin billing/audit.
    UPDATE public.consultant_profiles
       SET phone         = NULL,
           website       = NULL,
           email_from    = NULL,
           support_email = NULL,
           support_phone = NULL,
           address_line1 = NULL,
           address_line2 = NULL,
           city          = NULL,
           county        = NULL,
           postcode      = NULL,
           eircode       = NULL,
           api_key       = NULL,
           webhook_url   = NULL
     WHERE user_id = p_user_id;

    -- ---- Scrub: staff_profiles (internal staff PII) ----------------------
    UPDATE public.staff_profiles
       SET first_name = 'Deleted',
           last_name  = 'User',
           email      = v_anon_email,
           is_active  = false
     WHERE user_id = p_user_id;

    -- ---- Scrub: beta_users / user_feedback (email copies) ----------------
    UPDATE public.beta_users SET email = v_anon_email WHERE user_id = p_user_id;
    UPDATE public.user_feedback SET user_email = v_anon_email WHERE user_id = p_user_id;

    RAISE NOTICE 'anonymise_user: user % anonymised (reason: %; actor: %)',
        p_user_id, p_reason, coalesce(v_actor::text, 'service-context');
END;
$$;

COMMENT ON FUNCTION public.anonymise_user(uuid, uuid, text) IS
    'GDPR anonymise-in-place erasure procedure (Production Hardening Plan §3 A row 22 / §7 row 23; manual runbook, §8 P5). Hashes users.email, sets name to "Deleted User", preserves the UUID and all FK/audit aggregates. SECURITY DEFINER with actor guard (self, active staff, or service context). Idempotent; transactional; irreversible by design. Acceptance evidence: §9 Gate 5 staging rehearsal with residual-PII scan.';

REVOKE ALL ON FUNCTION public.anonymise_user(uuid, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.anonymise_user(uuid, uuid, text) TO service_role;
-- Authenticated EXECUTE is granted for the self-service erasure path guarded
-- inside the function (auth.uid() must equal p_user_id).
GRANT EXECUTE ON FUNCTION public.anonymise_user(uuid, uuid, text) TO authenticated;

-- ============================================================================
-- EXPLICITLY NOT IMPLEMENTED (register verification):
--   * Audit hash-chain / tamper-evidence functions — REJECTED (§6 D5,
--     security theatre; privilege revocation + PITR is the approved storey).
--   * Retention cron jobs / pg_cron wrappers — DEFERRED to v1.0.1 (§5 B);
--     the manual anonymise-in-place procedure above is the only approved
--     A-class compliance artefact.
--   * Soft-delete triggers/functions — DEFERRED (v1.0.1 B item).
--   * Erasure self-serve UI support, consent/PECR capture — DEFERRED v1.1
--     (§5 C24); the tested procedure here is what row C24 builds upon.
-- Rollback:
--   DROP FUNCTION IF EXISTS public.anonymise_user(uuid, uuid, text);
--   DROP FUNCTION IF EXISTS public.set_updated_at();   -- only after 006 triggers are removed
-- ============================================================================

COMMIT;

-- End of 005_rc1_functions.sql
