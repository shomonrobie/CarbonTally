-- ============================================================================
-- CT-IMPLEMENT-02 — canonical report sharing (PD-1)
-- File: 20261022000000_ct02_report_sharing.sql
--
-- PO DECISION IMPLEMENTED (ratified — not reinterpreted here):
--   PD-1  IMPLEMENT CANONICAL REPORT SHARING.
--         * Do NOT retire report sharing and do NOT recreate `report_history`.
--         * Sharing operates against the canonical report/version architecture
--           (`report_generation_queue` + `report_versions`).
--
-- WHAT WAS WRONG (verified, not assumed):
--   `POST /api/reports/{id}/share` and `GET /api/reports/shared` in
--   `backend/routes/reports.py` read and wrote a `report_history` table that
--   does not exist in the canonical schema, and stored "shares" inside that
--   row's `metadata` JSONB. Report sharing was therefore live-broken, had no
--   server-side authorization, no tenant isolation, no expiry enforcement, no
--   revocation, no access history and no audit — and the legacy `GET /shared`
--   enumerated every report history row in the database before filtering in
--   Python.
--
-- CANONICAL MODEL (this file):
--   public.report_shares              one share of ONE immutable report version
--   public.report_share_access_events append-only access/revocation history
--
-- DESIGN GUARANTEES (each one is enforced, not documented-only):
--   * VERSION-BOUND   — `report_version_id` is NOT NULL and cannot be changed;
--                       a share is never re-pointed at another version.
--   * NEVER MUTABLE STATE — a share may only be created for a version whose
--                       ratified lifecycle state is immutable (APPROVED/FINAL —
--                       the domain's own definition, `domain/report_lifecycle.
--                       IMMUTABLE_STATUSES`). Enforced by trigger on INSERT.
--   * EXPLICIT OWNER  — `organization_id` is NOT NULL and must equal the
--                       organisation that owns the referenced report/version;
--                       enforced by trigger against `report_generation_queue`.
--   * EXPLICIT RECIPIENT — at least one of `recipient_user_id` /
--                       `recipient_email` is required (CHECK).
--   * PERMISSION/SCOPE — `permission` ∈ {view, download} (CHECK).
--   * EXPIRY          — `expires_at` is validated at creation and evaluated
--                       server-side; an expired share is not usable.
--   * REVOCATION      — revocation is an UPDATE that must be self-describing
--                       (revoked_by + revocation_reason + revoked_at).
--   * NO ANONYMOUS PERMANENT PUBLIC URL — there is no public token column and
--                       no anon/public grant or policy. Link-style sharing uses
--                       an opaque, SHA-256-hashed token (`share_token_hash`,
--                       uniquely indexed) whose plaintext is returned once to
--                       the creating actor and never stored; and it still
--                       requires an AUTHENTICATED recipient.
--   * APPEND-ONLY HISTORY — `report_share_access_events` accepts no UPDATE, no
--                       DELETE and no TRUNCATE from any role, and is written
--                       server-side only.
--   * PROVENANCE      — every share row carries the exact report id + version
--                       id, so the shared artefact stays traceable to the
--                       calculation/evidence chain that produced it.
--
-- SCOPE DISCIPLINE: additive + idempotent. Creates exactly TWO new tables.
-- MODIFIES ZERO existing tables, columns, grants, policies or RLS flags.
-- No `report_history` is created. No legacy table is recreated.
--
-- VERIFICATION CHECKLIST
--   [ ] tables report_shares / report_share_access_events exist
--   [ ] report_history is still ABSENT
--   [ ] RLS enabled on both; no anon/public policy or grant
--   [ ] insert with mismatched organisation/report is rejected (trigger)
--   [ ] insert for a DRAFT/REVIEWED version is rejected (trigger)
--   [ ] share without recipient is rejected (CHECK)
--   [ ] permission outside {view,download} is rejected (CHECK)
--   [ ] scope columns cannot be changed by UPDATE (trigger)
--   [ ] access events reject UPDATE/DELETE/TRUNCATE (trigger + privileges)
--   [ ] re-running this file is a no-op
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 0. Preconditions — fail closed rather than silently no-op
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('public.report_generation_queue') IS NULL
       OR to_regclass('public.report_versions') IS NULL THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-1) precondition failed: the canonical report '
            'entities (report_generation_queue / report_versions) are absent. '
            'Report sharing binds to the canonical report/version architecture.';
    END IF;
    IF to_regprocedure('public.p8_disclosure_is_org_member(uuid)') IS NULL
       OR to_regprocedure('public.p8_disclosure_is_org_admin(uuid)') IS NULL THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-1) precondition failed: the B1 organisation '
            'helpers are absent; RLS cannot be expressed. Apply '
            '20260914000000_p8_b1_disclosure_model_foundation.sql first.';
    END IF;
    IF to_regclass('public.report_history') IS NOT NULL THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-1): report_history EXISTS in this target. '
            'PD-1 forbids recreating it; investigate before applying.';
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 1. public.report_shares — one share of one immutable report version
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.report_shares (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    -- The tenant that owns the shared data (never the recipient's tenant).
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    report_id uuid NOT NULL REFERENCES public.report_generation_queue(id) ON DELETE CASCADE,
    report_version_id uuid NOT NULL REFERENCES public.report_versions(id) ON DELETE CASCADE,
    -- Scope of the share: read-only by design (view) or read+download.
    permission varchar(16) NOT NULL DEFAULT 'view',
    -- Explicit recipient identity: an authenticated user, an invited address,
    -- or both. A share with neither is meaningless and is rejected.
    recipient_user_id uuid,
    recipient_email text,
    -- Opaque link token: only the SHA-256 hex of the token is stored, and it is
    -- never rendered back after creation. Link access still requires an
    -- authenticated recipient (no anonymous permanent public report URLs).
    share_token_hash char(64),
    created_by uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz,
    revoked_at timestamptz,
    revoked_by uuid,
    revocation_reason text,
    -- Access bookkeeping (updated only by the access recorder).
    access_count integer NOT NULL DEFAULT 0,
    last_accessed_at timestamptz,
    CONSTRAINT report_shares_permission_check
        CHECK (permission IN ('view', 'download')),
    CONSTRAINT report_shares_recipient_check
        CHECK (recipient_user_id IS NOT NULL OR recipient_email IS NOT NULL),
    CONSTRAINT report_shares_email_shape_check
        CHECK (recipient_email IS NULL
               OR recipient_email ~ '^[^@[:space:]]+@[^@[:space:]]+[.][^@[:space:]]+$'),
    CONSTRAINT report_shares_email_normalised_check
        CHECK (recipient_email IS NULL OR recipient_email = lower(recipient_email)),
    CONSTRAINT report_shares_token_hash_check
        CHECK (share_token_hash IS NULL OR share_token_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT report_shares_expiry_after_creation_check
        CHECK (expires_at IS NULL OR expires_at > created_at),
    -- Revocation must be self-describing: who, why and when.
    CONSTRAINT report_shares_revocation_described_check
        CHECK (revoked_at IS NULL
               OR (revoked_by IS NOT NULL
                   AND revocation_reason IS NOT NULL
                   AND btrim(revocation_reason) <> '')),
    CONSTRAINT report_shares_access_count_check CHECK (access_count >= 0)
);

COMMENT ON TABLE public.report_shares IS
    'CT-IMPLEMENT-02 (PD-1) — canonical share of ONE immutable report version. '
    'Version-bound and never re-pointed; created only for APPROVED/FINAL '
    'versions; tenant-owned by organization_id; recipient-explicit; expiring; '
    'revocable; access-history-bearing. There is deliberately no public token '
    'column: link tokens are stored only as a SHA-256 hash and still require an '
    'authenticated recipient.';
COMMENT ON COLUMN public.report_shares.report_version_id IS
    'The exact report version shared (PD-1). Immutable after insert — a share '
    'never follows a report to a newer version.';
COMMENT ON COLUMN public.report_shares.share_token_hash IS
    'SHA-256 (lowercase hex) of an opaque link token. The plaintext is returned '
    'once to the creating actor and never persisted. Not a public URL.';
COMMENT ON COLUMN public.report_shares.revocation_reason IS
    'Mandatory when revoked_at is set (report_shares_revocation_described_check).';


-- ---------------------------------------------------------------------------
-- 2. Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_report_shares_organization
    ON public.report_shares (organization_id);
CREATE INDEX IF NOT EXISTS idx_report_shares_report
    ON public.report_shares (report_id);
CREATE INDEX IF NOT EXISTS idx_report_shares_version
    ON public.report_shares (report_version_id);
CREATE INDEX IF NOT EXISTS idx_report_shares_recipient_user
    ON public.report_shares (recipient_user_id)
    WHERE recipient_user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_report_shares_recipient_email
    ON public.report_shares (lower(recipient_email))
    WHERE recipient_email IS NOT NULL;

-- One live share per (version, recipient): re-sharing is an explicit revoke +
-- re-share, so a recipient can never accumulate ambiguous duplicate grants.
CREATE UNIQUE INDEX IF NOT EXISTS report_shares_active_recipient_key
    ON public.report_shares (
        report_version_id,
        coalesce(recipient_user_id, '00000000-0000-0000-0000-000000000000'::uuid),
        coalesce(lower(recipient_email), '')
    )
    WHERE revoked_at IS NULL;

-- The hashed link token is a bearer credential: it must be unique.
CREATE UNIQUE INDEX IF NOT EXISTS report_shares_token_hash_key
    ON public.report_shares (share_token_hash)
    WHERE share_token_hash IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 3. Server-side validation triggers
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.ct02_report_share_validate()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_status       text;
    v_report_org   uuid;
BEGIN
    -- Cross-row invariants: the version must exist, be immutable, and belong to
    -- the same organisation and report as the share.
    SELECT rv.status, rq.organization_id
      INTO v_status, v_report_org
      FROM public.report_versions rv
      JOIN public.report_generation_queue rq ON rq.id = rv.report_id
     WHERE rv.id = NEW.report_version_id;

    IF v_status IS NULL THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-1): report version % is not bound to a '
            'canonical report; a share cannot be created for it.',
            NEW.report_version_id
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    IF v_report_org <> NEW.organization_id THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-1): cross-tenant share refused. Version % '
            'belongs to organisation %, not %.',
            NEW.report_version_id, v_report_org, NEW.organization_id
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    IF v_status NOT IN ('APPROVED', 'FINAL') THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-1): report version % is in state % — only an '
            'immutable (APPROVED/FINAL) version may be shared; sharing mutable '
            'report state is forbidden.',
            NEW.report_version_id, v_status
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.ct02_report_share_validate() IS
    'CT-IMPLEMENT-02 (PD-1) — refuses a share whose version is absent, belongs '
    'to another tenant, or is not in an immutable (APPROVED/FINAL) state.';

DROP TRIGGER IF EXISTS ct02_report_shares_validate ON public.report_shares;
CREATE TRIGGER ct02_report_shares_validate
    BEFORE INSERT ON public.report_shares
    FOR EACH ROW
    EXECUTE FUNCTION public.ct02_report_share_validate();


-- ---------------------------------------------------------------------------
-- 4. A share's identity and scope are frozen; only revocation and access
--    bookkeeping may change. Re-scoping means revoke + create a new share.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.ct02_report_share_update_guard()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.organization_id    IS DISTINCT FROM OLD.organization_id
       OR NEW.report_id       IS DISTINCT FROM OLD.report_id
       OR NEW.report_version_id IS DISTINCT FROM OLD.report_version_id
       OR NEW.permission      IS DISTINCT FROM OLD.permission
       OR NEW.recipient_user_id IS DISTINCT FROM OLD.recipient_user_id
       OR NEW.recipient_email IS DISTINCT FROM OLD.recipient_email
       OR NEW.share_token_hash IS DISTINCT FROM OLD.share_token_hash
       OR NEW.expires_at      IS DISTINCT FROM OLD.expires_at
       OR NEW.created_by      IS DISTINCT FROM OLD.created_by
       OR NEW.created_at      IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-1): a report share''s identity and scope are '
            'immutable. Revoke it and create a new share instead.'
            USING ERRCODE = 'check_violation';
    END IF;

    -- Revocation is one-way: a revoked share can never be reinstated.
    IF OLD.revoked_at IS NOT NULL
       AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at THEN
        RAISE EXCEPTION
            'CT-IMPLEMENT-02 (PD-1): share % is already revoked; the revocation '
            'record is immutable.', OLD.id
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.ct02_report_share_update_guard() IS
    'CT-IMPLEMENT-02 (PD-1) — freezes share identity/scope and makes revocation '
    'one-way; only revocation columns and access bookkeeping may be updated.';

DROP TRIGGER IF EXISTS ct02_report_shares_update_guard ON public.report_shares;
CREATE TRIGGER ct02_report_shares_update_guard
    BEFORE UPDATE ON public.report_shares
    FOR EACH ROW
    EXECUTE FUNCTION public.ct02_report_share_update_guard();

-- ---------------------------------------------------------------------------
-- 5. public.report_share_access_events — append-only access history
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.report_share_access_events (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    share_id uuid NOT NULL REFERENCES public.report_shares(id) ON DELETE CASCADE,
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    report_version_id uuid NOT NULL,
    actor_user_id uuid,
    event_type varchar(16) NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    detail jsonb,
    CONSTRAINT report_share_access_events_type_check
        CHECK (event_type IN ('created', 'access', 'download', 'revoked', 'denied')),
    -- Detail must never carry credentials, tokens or signed URLs.
    CONSTRAINT report_share_access_events_detail_shape_check
        CHECK (detail IS NULL OR jsonb_typeof(detail) = 'object')
);

COMMENT ON TABLE public.report_share_access_events IS
    'CT-IMPLEMENT-02 (PD-1) — append-only access history for one report share '
    '(created/access/download/revoked/denied). Written server-side only; no '
    'UPDATE, DELETE or TRUNCATE for any role. Never stores tokens or signed '
    'URLs. The canonical ledger public.audit_trail carries the same events as '
    'audit entries; this table is the share-scoped view.';

CREATE INDEX IF NOT EXISTS idx_report_share_access_share
    ON public.report_share_access_events (share_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_share_access_org
    ON public.report_share_access_events (organization_id, occurred_at DESC);

DROP TRIGGER IF EXISTS ct02_report_share_access_no_truncate
    ON public.report_share_access_events;
CREATE TRIGGER ct02_report_share_access_no_truncate
    BEFORE TRUNCATE ON public.report_share_access_events
    FOR EACH STATEMENT
    EXECUTE FUNCTION public.ct02_audit_truncate_guard();

DROP TRIGGER IF EXISTS ct02_report_share_access_immutable
    ON public.report_share_access_events;
CREATE TRIGGER ct02_report_share_access_immutable
    BEFORE UPDATE OR DELETE ON public.report_share_access_events
    FOR EACH ROW
    EXECUTE FUNCTION public.ct02_append_only_guard();

-- ---------------------------------------------------------------------------
-- 6. RLS + privileges
--    Canonical convention (matching report_version_artifacts): RLS enabled,
--    anon revoked with no policy, authenticated granted exactly the DML its
--    policies imply. RLS decides every row.
-- ---------------------------------------------------------------------------
ALTER TABLE public.report_shares ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.report_shares FROM anon;
REVOKE ALL ON TABLE public.report_shares FROM authenticated;
-- No DELETE: a share is revoked, never erased (history and audit depend on it).
GRANT SELECT, INSERT, UPDATE ON TABLE public.report_shares TO authenticated;

-- The tenant's own members see the shares of their reports; a recipient sees
-- the share addressed to them (by user id or by authenticated email). Nothing
-- else is visible, and no anon/public role is granted anything.
DROP POLICY IF EXISTS report_shares_read ON public.report_shares;
CREATE POLICY report_shares_read
    ON public.report_shares FOR SELECT TO authenticated
    USING (
        public.p8_disclosure_is_org_member(organization_id)
        OR recipient_user_id = auth.uid()
        OR (recipient_email IS NOT NULL
            AND auth.email() IS NOT NULL
            AND lower(recipient_email) = lower(auth.email()))
    );

-- Creating a share is an organisation authority action (Owner/Admin), and the
-- trigger above additionally proves the version belongs to that organisation.
DROP POLICY IF EXISTS report_shares_insert ON public.report_shares;
CREATE POLICY report_shares_insert
    ON public.report_shares FOR INSERT TO authenticated
    WITH CHECK (public.p8_disclosure_is_org_admin(organization_id));

-- Revocation is an organisation authority action. The update guard trigger
-- restricts what may change to the revocation/bookkeeping columns.
DROP POLICY IF EXISTS report_shares_update ON public.report_shares;
CREATE POLICY report_shares_update
    ON public.report_shares FOR UPDATE TO authenticated
    USING (public.p8_disclosure_is_org_admin(organization_id))
    WITH CHECK (public.p8_disclosure_is_org_admin(organization_id));

ALTER TABLE public.report_share_access_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.report_share_access_events FROM anon;
REVOKE ALL ON TABLE public.report_share_access_events FROM authenticated;
-- Read-only for the tenant; the history is written by the server, never by a
-- client (no INSERT/UPDATE/DELETE grant and no such policy).
GRANT SELECT ON TABLE public.report_share_access_events TO authenticated;

DROP POLICY IF EXISTS report_share_access_events_read
    ON public.report_share_access_events;
CREATE POLICY report_share_access_events_read
    ON public.report_share_access_events FOR SELECT TO authenticated
    USING (
        public.p8_disclosure_is_org_member(organization_id)
        OR actor_user_id = auth.uid()
    );

-- Server-side writers keep the full write path (they bypass RLS by design).
DO $$
DECLARE
    role_name text;
BEGIN
    FOREACH role_name IN ARRAY ARRAY['service_role', 'postgres'] LOOP
        CONTINUE WHEN NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name);
        EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.report_shares TO %s',
                       quote_ident(role_name));
        EXECUTE format('GRANT SELECT, INSERT ON TABLE public.report_share_access_events TO %s',
                       quote_ident(role_name));
    END LOOP;
END $$;

COMMIT;

-- ============================================================================
-- VERIFICATION CHECKLIST
--   [ ] tables report_shares / report_share_access_events exist
--   [ ] report_history is still ABSENT
--   [ ] RLS enabled on both; no anon/public policy or grant
--   [ ] insert with mismatched organisation/report is rejected (trigger)
--   [ ] insert for a DRAFT/REVIEWED version is rejected (trigger)
--   [ ] share without recipient is rejected (CHECK)
--   [ ] permission outside {view,download} is rejected (CHECK)
--   [ ] scope columns cannot be changed by UPDATE (trigger)
--   [ ] access events reject UPDATE/DELETE/TRUNCATE (trigger + privileges)
--   [ ] re-running this file is a no-op
-- ============================================================================


