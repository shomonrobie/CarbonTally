-- ============================================================================
-- CarbonTally BACKUP-01 — the durable backup job model (`public.backup_jobs`).
-- File: 20261026000000_ct_backup_01_backup_jobs.sql
--
-- WHY THIS FILE EXISTS (BACKUP-01 §9–§11):
--   The ratified production-backup architecture
--   (`docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md`
--   §10) requires a *durable* queue for backup jobs: an admin request must create
--   only a `queued` row, and a worker must claim it with
--   `FOR UPDATE SKIP LOCKED`.  Nothing in the pre-existing schema models a
--   backup, so this file creates exactly one table — the missing half of the
--   queue whose worker side is `backend/backup/jobs.py`.
--
-- WHAT THIS CREATES:
--   * `public.backup_jobs` with the §10 column set (status, scope, actor,
--     timing, lock token, artifact metadata, manifest, retention, deletion
--     audit), plus `idempotency_key` required by §11;
--   * the §11 **single-flight guard** — a PARTIAL UNIQUE INDEX over the active
--     states, so at most one `queued`/`running` job can exist at a time.  A
--     second concurrent request is resolved to the existing job by the
--     application's `ON CONFLICT DO NOTHING`, never by a duplicate dump;
--   * CHECK constraints making the status and fixed-scope vocabularies
--     impossible to violate from any client;
--   * the established RLS posture for an INTERNAL, non-organisation table.
--
-- WHY THIS TABLE IS NOT ORGANISATION-SCOPED:
--   §10 is explicit: "internal-admin only; never organisation-scoped; no `anon`
--   access".  A backup spans every tenant, so there is no owning
--   `organization_id` and therefore no `public.is_org_member(...)` policy.  The
--   correct posture is RLS enabled with **no** policy for `anon`/`authenticated`,
--   which denies them at the database rather than at the route.
--
-- WHAT THIS DOES NOT DO:
--   * it does NOT export, encrypt, upload, verify or schedule anything — those
--     are application responsibilities (`backend/backup/`);
--   * it creates no second audit model: actor actions are recorded in the
--     EXISTING `audit_trail` through `api/audit_helpers.py`;
--   * it does not touch any other table, bucket, storage policy or grant.
--
-- DEPLOYMENT BOUNDARY: nothing is deployed by this file.  It must be applied by
-- the normal authorised deployment process before the backup admin surface can
-- be registered; until then the code fails loudly on the missing relation rather
-- than silently reporting an empty history.
--
-- IDEMPOTENT: `CREATE TABLE IF NOT EXISTS`, guarded index creation, a guarded
-- capability grant, and a converging verification block — re-running is a
-- bounded no-op.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- §10 — the job row
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.backup_jobs (
    id              UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    status          TEXT NOT NULL DEFAULT 'queued',
    scope           TEXT NOT NULL,
    requested_by    UUID REFERENCES public.users(id) ON DELETE SET NULL,
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    attempt_count   INTEGER NOT NULL DEFAULT 0,
    lock_token      TEXT,
    locked_at       TIMESTAMPTZ,
    storage_key     TEXT,
    storage_bucket  TEXT,
    artifact_bytes  BIGINT,
    checksum_sha256 TEXT,
    key_version     TEXT,
    manifest        JSONB,
    release_commit  TEXT,
    error_reason    TEXT,
    expires_at      TIMESTAMPTZ,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID REFERENCES public.users(id) ON DELETE SET NULL,
    idempotency_key TEXT,
    CONSTRAINT backup_jobs_status_check CHECK (
        status IN ('queued', 'running', 'completed', 'failed', 'expired', 'deleted')
    ),
    CONSTRAINT backup_jobs_scope_check CHECK (
        scope IN ('public+schema+roles')
    ),
    CONSTRAINT backup_jobs_attempt_count_check CHECK (attempt_count >= 0),
    CONSTRAINT backup_jobs_artifact_bytes_check CHECK (
        artifact_bytes IS NULL OR artifact_bytes > 0
    ),
    -- 64 lowercase hex characters, or nothing: a half-written digest is never
    -- accepted, so the history can be trusted when it reports a checksum.
    CONSTRAINT backup_jobs_checksum_check CHECK (
        checksum_sha256 IS NULL OR checksum_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT backup_jobs_manifest_check CHECK (
        manifest IS NULL OR jsonb_typeof(manifest) = 'object'
    ),
    -- A terminal job carries a finish time; an active or soft terminal one
    -- (expired/deleted) does not have to.
    CONSTRAINT backup_jobs_finished_at_check CHECK (
        status NOT IN ('completed', 'failed') OR finished_at IS NOT NULL
    ),
    -- Retention is only meaningful once an artifact exists.
    CONSTRAINT backup_jobs_expires_at_check CHECK (
        expires_at IS NULL OR status IN ('completed', 'expired', 'deleted')
    ),
    -- Deletion audit fields travel together.
    CONSTRAINT backup_jobs_deleted_check CHECK (
        (deleted_at IS NULL AND deleted_by IS NULL)
        OR (status = 'deleted' AND deleted_at IS NOT NULL)
    )
);

COMMENT ON TABLE public.backup_jobs IS
    'BACKUP-01 §10: durable backup-job queue (status machine + single-flight '
    'slot). Internal-admin only; never organisation-scoped; no anon access. '
    'Rows are metadata only — no plaintext and no encryption key is ever stored.';
COMMENT ON COLUMN public.backup_jobs.status IS
    'queued|running|completed|failed|expired|deleted (§10 state machine).';
COMMENT ON COLUMN public.backup_jobs.scope IS
    'Fixed vocabulary; the only ratified value is public+schema+roles.';
COMMENT ON COLUMN public.backup_jobs.lock_token IS
    'SKIP LOCKED claim token; identifies the worker holding the job.';
COMMENT ON COLUMN public.backup_jobs.key_version IS
    'Encryption key IDENTIFIER only — never the key material.';
COMMENT ON COLUMN public.backup_jobs.error_reason IS
    'Sanitised, bounded failure reason; must never contain secrets.';
COMMENT ON COLUMN public.backup_jobs.expires_at IS
    'Derived from the existing backup_retention_days setting; NULL = no expiry.';
COMMENT ON COLUMN public.backup_jobs.idempotency_key IS
    '§11 Idempotency-Key: identical key resolves to the identical job.';

-- ----------------------------------------------------------------------------
-- §11 — single-flight guard, idempotency slot and history/expiry access paths
-- ----------------------------------------------------------------------------
-- At most one active job may exist.  This is the constraint the application
-- relies on for `ON CONFLICT DO NOTHING`: a second admin clicking "backup" while
-- one is queued or running is resolved to the existing job.
CREATE UNIQUE INDEX IF NOT EXISTS backup_jobs_single_flight_idx
    ON public.backup_jobs (status)
    WHERE status IN ('queued', 'running');

-- §11: a repeated request carrying the same Idempotency-Key returns the same job.
CREATE UNIQUE INDEX IF NOT EXISTS backup_jobs_idempotency_key_idx
    ON public.backup_jobs (idempotency_key)
    WHERE idempotency_key IS NOT NULL;

-- History listing is newest-first (§9 "Admin Backup History").
CREATE INDEX IF NOT EXISTS backup_jobs_history_idx
    ON public.backup_jobs (requested_at DESC, id DESC);

-- Retention sweeps only ever look at completed, expiring, non-deleted rows.
CREATE INDEX IF NOT EXISTS backup_jobs_expiry_idx
    ON public.backup_jobs (expires_at)
    WHERE status = 'completed' AND expires_at IS NOT NULL;

-- ----------------------------------------------------------------------------
-- RLS posture — internal-admin only (see the header note on organisation scope)
-- ----------------------------------------------------------------------------
ALTER TABLE public.backup_jobs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.backup_jobs FROM anon;
REVOKE ALL ON TABLE public.backup_jobs FROM authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.backup_jobs FROM authenticated;
GRANT ALL ON TABLE public.backup_jobs TO service_role;

-- NOTE DELIBERATE: no policy is created for `anon` or `authenticated`.  With RLS
-- enabled and no permissive policy, both roles are denied every row — which is
-- the §10 requirement ("no anon access", internal-admin only).  Reachability is
-- therefore governed by the application's admin capability, never by a table
-- policy that could be widened by accident.

-- ----------------------------------------------------------------------------
-- §9 — the explicit admin capability (a DATA grant, not a policy change)
-- ----------------------------------------------------------------------------
-- `staff_roles.permissions` is the authoritative permission catalog (see
-- 20260828010000_v3m8_system_admin_role_model.sql for the established pattern).
-- Granting the capability here means the (separately deployed) admin surface is
-- reachable by the internal admin roles and by nobody else.  It widens no RLS
-- policy, creates no role, and touches no other permission.
-- `auth.ADMIN_ROLE_NAMES` recognises exactly ('admin', 'system_admin'), and
-- PO Decision 2 makes `system_admin` a superset of the legacy `admin` role, so
-- both names are granted.
UPDATE public.staff_roles
SET permissions = permissions || '{"can_manage_backups": true}'::jsonb,
    updated_at = NOW()
WHERE name IN ('admin', 'system_admin')
  AND (permissions->>'can_manage_backups') IS DISTINCT FROM 'true';

-- ----------------------------------------------------------------------------
-- Verification — fail loudly rather than leave a half-provisioned queue
-- ----------------------------------------------------------------------------
DO $ct_backup_01$
DECLARE
    active_jobs integer;
BEGIN
    IF to_regclass('public.backup_jobs') IS NULL THEN
        RAISE EXCEPTION 'BACKUP-01: public.backup_jobs was not created';
    END IF;

    IF NOT (SELECT relrowsecurity
            FROM pg_class
            WHERE oid = 'public.backup_jobs'::regclass) THEN
        RAISE EXCEPTION
            'BACKUP-01: row level security is not enabled on public.backup_jobs';
    END IF;

    IF to_regclass('public.backup_jobs_single_flight_idx') IS NULL THEN
        RAISE EXCEPTION 'BACKUP-01: the single-flight unique index is missing';
    END IF;

    -- The single-flight guarantee must hold on live data as well as on writes.
    SELECT count(*) INTO active_jobs
    FROM public.backup_jobs
    WHERE status IN ('queued', 'running');

    IF active_jobs > 1 THEN
        RAISE EXCEPTION
            'BACKUP-01: % active backup jobs violate the single-flight guarantee',
            active_jobs;
    END IF;

    RAISE NOTICE
        'BACKUP-01: public.backup_jobs ready (internal-admin only, single-flight enforced).';
END
$ct_backup_01$;

COMMIT;


