-- ============================================================================
-- CarbonTally v1.0 RC2 — Production Hardening Migration (REPAIR RELEASE)
-- File 005 of 008: Approved functions (corrected release of 005_rc1_functions)
-- Source of truth:
--   * Prior: database/rc1/005_rc1_functions.sql (function shape, signatures)
--   * CarbonTally RC1 — Independent Database Audit.md (RC2-C3, RC2-H1, RC2-I3)
--   * CarbonTally_v1.0_Production_Hardening_Plan.md (A row 22)
-- Database: PostgreSQL 16 (Supabase). Schema: public. Single transaction.
--
-- TWO REPAIRS SHIP IN THIS FILE relative to RC1 005:
--
--   RC2-C3 (Critical, authorisation):
--     RC1 derived the effective actor from a CALLER-SUPPLIED parameter:
--       v_actor := coalesce(p_actor_id, auth.uid());
--     Because the function is SECURITY DEFINER and `authenticated` holds
--     EXECUTE (for the self-service path), ANY authenticated user could call
--     anonymise_user(victim, trusted_staff_id, '...') and the guard would
--     accept it — the authority came from a spoofable argument, enabling
--     cross-tenant / mass erasure. The fix:
--       * authority derives from THE SESSION ONLY: v_actor := auth.uid();
--       * if a caller-supplied p_actor_id is given under a real session and
--         does not equal auth.uid(), we RAISE (anti-spoof);
--       * p_actor_id is retained only as an advisory/audit tag, never to
--         authorise.
--
--   RC2-H1 (Critical, search_path / hash resolution):
--     The baseline installs pgcrypto WITH SCHEMA extensions, so `sha256` is
--     reachable as extensions.sha256, NOT as a bare unqualified sha256. RC1
--     called sha256(...) unqualified with `search_path = public`, which can
--     never resolve (42702/42883 / wrong-candidate). The fix schema-qualifies
--     the hash: encode(extensions.sha256(...), 'hex').
--
--   RC2-I3 (Medium, helper posture): every function here pins `search_path`
--     (the policy helpers in 004 already do too). An explicit
--     force_secure_search_path() helper is intentionally NOT shipped — the
--     two approved functions already set their own search_path, and adding an
--     uninvoked helper would only expand the attack/review surface.
-- ============================================================================

BEGIN;

-- ============================================================================
-- F1 — public.set_updated_at()
-- ============================================================================
-- Generic BEFORE UPDATE trigger function maintaining updated_at = now();
-- companion to the approved 006 maintenance triggers. SECURITY INVOKER by
-- design (it carries the updating role's rights; the trigger fires regardless
-- of RLS). No change from RC1 — re-issued for completeness and idempotency.
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
    'Generic BEFORE UPDATE trigger function: stamps NEW.updated_at := now(). Companion to the 006 updated_at maintenance triggers. SECURITY INVOKER (runs with the updating role''s rights; the trigger fires regardless of RLS).';

-- ============================================================================
-- F2 — public.anonymise_user(p_user_id uuid, p_actor_id uuid, p_reason text)
-- RC2-C3 / RC2-H1 corrected erasure procedure.
-- ============================================================================
-- GDPR/UK-GDPR erasure: anonymise-in-place (pins the UUID, scrubs identity).
-- Behaviours preserved from RC1 (approved A-22 artefact):
--   * email→ deterministic SHA-256-derived mailbox, unique & non-routable;
--   * first_name/last_name → 'Deleted'/'User'; password_hash → NULL;
--   * is_active=false, email_verified=false;
--   * PII scrubbed across consultant_profiles, staff_profiles, beta_users,
--     user_feedback;
--   * idempotent (marker-domain no-op) and transactional.
--
-- RC2-C3 corrected authorisation model (session-only authority):
--   * v_actor := coalesce(auth.uid(), p_actor_id). Under any real
--     authenticated session auth.uid() is NOT NULL, so the supplied
--     p_actor_id is NEVER authoritative; a mismatched p_actor_id raises.
--     The SECURITY DEFINER body therefore cannot be tricked into treating an
--     arbitrary staff/victim id as the caller. Only service-context
--     (auth.uid() IS NULL — Supabase service_role, which already BYPASSRLS
--     and can do anything) may pass a p_actor_id, and only as an audit tag.
--   * Authorised callers: (a) service context, (b) the data subject themself
--     (auth.uid() = p_user_id), (c) an ACTIVE staff member (auth.uid() is an
--     active staff_profiles.user_id). All other caller identities raise and
--     the whole scrub rolls back.
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

    -- ---- RC2-C3: session-only actor authority ----------------------------
    -- If a real session exists, the caller-supplied p_actor_id must match it;
    -- a mismatch proves a spoof attempt and aborts (anti-escalation).
    IF auth.uid() IS NOT NULL
       AND p_actor_id IS NOT NULL
       AND p_actor_id IS DISTINCT FROM auth.uid() THEN
        RAISE EXCEPTION
            'anonymise_user: spoofed actor id — caller-supplied p_actor_id (%) does not match the authenticated session (%)',
            p_actor_id, auth.uid();
    END IF;

    -- Effective actor: the session's identity; only in service context (no
    -- session) is the advisory p_actor_id used (and then the caller is
    -- service_role anyway, which bypasses RLS).
    v_actor := coalesce(auth.uid(), p_actor_id);

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

    -- ---- RC2-H1: schema-qualified hash (pgcrypto lives in `extensions`) ---
    v_anon_email := 'deleted-' || encode(extensions.sha256(p_user_id::text::bytea), 'hex')
                    || '@anonymised.invalid';

    -- ---- Scrub: users (identity core; UUID preserved) --------------------
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
    'GDPR anonymise-in-place erasure (A-22). RC2-C3: authority derives from auth.uid() only — caller-supplied p_actor_id is advisory and, under a real session, must match auth.uid() or the call aborts (anti-spoof / anti-escalation). RC2-H1: sha256 resolved as extensions.sha256. Hashes users.email, sets name to Deleted/User, preserves UUID and all FK/audit aggregates. SECURITY DEFINER, pinned search_path. Idempotent, transactional, irreversible by design.';

REVOKE ALL ON FUNCTION public.anonymise_user(uuid, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.anonymise_user(uuid, uuid, text) TO service_role;
-- Authenticated EXECUTE remains for the SELF-SERVICE erasure path. Now safe
-- because authority is bound to auth.uid() (C3 fix): an authenticated caller
-- can only erase a row where p_user_id = auth.uid() (subject) or where
-- auth.uid() is active staff — they can never forge p_actor_id.
GRANT EXECUTE ON FUNCTION public.anonymise_user(uuid, uuid, text) TO authenticated;

-- ============================================================================
-- EXPLICITLY NOT IMPLEMENTED (register verification — unchanged from RC1):
--   * Audit hash-chain / tamper-evidence functions — REJECTED.
--   * Retention cron jobs / pg_cron wrappers — DEFERRED v1.0.1.
--   * Soft-delete triggers/functions — DEFERRED v1.0.1.
--   * force_secure_search_path() helper — not shipped (both functions pin
--     search_path themselves; an uninvoked helper widens the review surface).
--
-- DEPENDENCIES:
--   * extensions.sha256 requires pgcrypto (installed by the baseline init and
--     re-ensured in 003). 005 must run after 003 if pgcrypto were missing.
--   * 006 triggers depend on set_updated_at().
--
-- ROLLBACK:
--   DROP FUNCTION IF EXISTS public.anonymise_user(uuid, uuid, text);
--   DROP FUNCTION IF EXISTS public.set_updated_at();  -- only after 006 triggers removed
-- ============================================================================

COMMIT;

-- End of 005_rc2_functions.sql
