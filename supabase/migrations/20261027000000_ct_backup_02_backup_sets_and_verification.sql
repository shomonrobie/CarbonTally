-- ============================================================================
-- CarbonTally BACKUP-02 — backup sets (database + object jobs) and verification.
-- File: 20261027000000_ct_backup_02_backup_sets_and_verification.sql
--
-- WHY THIS FILE EXISTS (BACKUP-01 §12 + §14):
--   1. §14 requires Storage-**object** backup to be a SEPARATE job from the
--      database backup, "sequenced and paired by a common backup-set id so a
--      restore can select a consistent pair". BACKUP-01 created one queue row per
--      job but had no way to say *which kind* a row is, nor to pair the two
--      halves — so this adds `kind` and `backup_set_id`.
--   2. §12 requires an integrity-verification outcome to be recorded, and the
--      Admin Dashboard requires *latest verification status*. Without a home for
--      that result a "Verify Backup" action could not be honest, so this adds
--      `verification_status` / `verification_checked_at` / `verification_error`.
--   3. Consequence of (1): the BACKUP-01 single-flight guard used to be
--      `UNIQUE (status) WHERE status IN ('queued','running')`, which allows only
--      ONE active job in total — that would let an object job block a database
--      backup (and vice versa), contradicting §14's "separate jobs" requirement.
--      The guard is therefore rebuilt as **one slot per kind**.
--
-- WHAT THIS CHANGES:
--   * seven additive columns on `public.backup_jobs` (no data loss, no rewrite of
--     any BACKUP-01 column);
--   * CHECK constraints pinning the new vocabularies, so no client can write a
--     job kind or a verification state outside the ratified set;
--   * the single-flight index is **replaced in place** (same name, key now
--     `(kind)`) — the BACKUP-01 verification block that asserts the index exists
--     therefore continues to hold, and becomes *stronger*;
--   * two supporting indexes (pair lookup, verification sweep) and COMMENTs.
--
-- WHAT THIS DOES NOT DO:
--   * it does NOT export, encrypt, upload, verify or restore anything — those are
--     application responsibilities (`backend/backup/`);
--   * it creates no second audit model and no second notification model;
--   * it widens no RLS policy and touches no other table, bucket or grant.
--
-- DEPLOYMENT BOUNDARY: nothing is deployed by this file. It must be applied by
-- the normal authorised deployment process; until then `backend/backup/jobs.py`
-- fails loudly on the missing columns rather than silently mis-recording a job.
--
-- IDEMPOTENT: additive columns, guarded constraints (via a DO block), index
-- replacement with IF NOT EXISTS, and a converging verification block.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- §14 — job kind and the backup-set pairing id
-- ----------------------------------------------------------------------------
ALTER TABLE public.backup_jobs
    ADD COLUMN IF NOT EXISTS kind TEXT NOT NULL DEFAULT 'database';
ALTER TABLE public.backup_jobs
    ADD COLUMN IF NOT EXISTS backup_set_id UUID;
ALTER TABLE public.backup_jobs
    ADD COLUMN IF NOT EXISTS object_count INTEGER;
ALTER TABLE public.backup_jobs
    ADD COLUMN IF NOT EXISTS object_bytes BIGINT;

-- ----------------------------------------------------------------------------
-- §12 — verification outcome (set by the "Verify Backup" action only)
-- ----------------------------------------------------------------------------
ALTER TABLE public.backup_jobs
    ADD COLUMN IF NOT EXISTS verification_status TEXT NOT NULL DEFAULT 'unverified';
ALTER TABLE public.backup_jobs
    ADD COLUMN IF NOT EXISTS verification_checked_at TIMESTAMPTZ;
ALTER TABLE public.backup_jobs
    ADD COLUMN IF NOT EXISTS verification_error TEXT;

-- ----------------------------------------------------------------------------
-- Vocabulary guards — ADD CONSTRAINT has no IF NOT EXISTS, so guard by name.
-- ----------------------------------------------------------------------------
DO $ct_backup_02_constraints$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'backup_jobs_kind_check'
          AND conrelid = 'public.backup_jobs'::regclass
    ) THEN
        ALTER TABLE public.backup_jobs
            ADD CONSTRAINT backup_jobs_kind_check
            CHECK (kind IN ('database', 'objects'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'backup_jobs_verification_status_check'
          AND conrelid = 'public.backup_jobs'::regclass
    ) THEN
        ALTER TABLE public.backup_jobs
            ADD CONSTRAINT backup_jobs_verification_status_check
            CHECK (verification_status IN ('unverified', 'verified', 'failed'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'backup_jobs_object_counts_check'
          AND conrelid = 'public.backup_jobs'::regclass
    ) THEN
        ALTER TABLE public.backup_jobs
            ADD CONSTRAINT backup_jobs_object_counts_check
            CHECK (
                (object_count IS NULL OR object_count >= 0)
                AND (object_bytes IS NULL OR object_bytes >= 0)
            );
    END IF;
END
$ct_backup_02_constraints$;

-- ----------------------------------------------------------------------------
-- §11 single-flight, now PER KIND (§14)
-- ----------------------------------------------------------------------------
-- BACKUP-01's guard allowed exactly one active row in the whole table, which
-- would make the object job and the database job mutually exclusive. Replacing
-- the key with `(kind)` keeps single-flight within each queue while allowing the
-- two halves of one backup set to be queued together. The index NAME is kept so
-- the BACKUP-01 verification block keeps asserting the same invariant.
DROP INDEX IF EXISTS public.backup_jobs_single_flight_idx;
CREATE UNIQUE INDEX IF NOT EXISTS backup_jobs_single_flight_idx
    ON public.backup_jobs (kind)
    WHERE status IN ('queued', 'running');

-- Pair lookup: both halves of a backup set (§14).
CREATE INDEX IF NOT EXISTS backup_jobs_backup_set_idx
    ON public.backup_jobs (backup_set_id)
    WHERE backup_set_id IS NOT NULL;

-- Verification sweep: "latest verification status" and re-verify candidates.
CREATE INDEX IF NOT EXISTS backup_jobs_verification_idx
    ON public.backup_jobs (verification_status, verification_checked_at DESC)
    WHERE status = 'completed';

COMMENT ON COLUMN public.backup_jobs.kind IS
    'Artifact kind: database (the logical dump) or objects (the paired Storage-object artifact). One single-flight slot exists per kind.';
COMMENT ON COLUMN public.backup_jobs.backup_set_id IS
    'Pairs the database job and its object job so a restore can select a consistent pair (architecture §14).';
COMMENT ON COLUMN public.backup_jobs.object_count IS
    'Number of Storage objects in an object artifact (NULL for a database job).';
COMMENT ON COLUMN public.backup_jobs.object_bytes IS
    'Total bytes of the Storage objects in an object artifact (NULL for a database job).';
COMMENT ON COLUMN public.backup_jobs.verification_status IS
    'Integrity-verification outcome recorded by the Verify Backup action: unverified|verified|failed (architecture §12).';
COMMENT ON COLUMN public.backup_jobs.verification_error IS
    'Sanitised reason a verification failed. Never contains key material, credentials or artifact contents.';

-- ----------------------------------------------------------------------------
-- Verification — fail loudly rather than leave a half-provisioned queue
-- ----------------------------------------------------------------------------
DO $ct_backup_02$
DECLARE
    offending_kinds integer;
BEGIN
    IF to_regclass('public.backup_jobs') IS NULL THEN
        RAISE EXCEPTION 'BACKUP-02: public.backup_jobs does not exist';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'backup_jobs'
          AND column_name IN ('kind', 'backup_set_id', 'object_count',
                              'object_bytes', 'verification_status',
                              'verification_checked_at', 'verification_error')
        HAVING count(*) = 7
    ) THEN
        RAISE EXCEPTION 'BACKUP-02: the additive columns were not created';
    END IF;

    IF to_regclass('public.backup_jobs_single_flight_idx') IS NULL THEN
        RAISE EXCEPTION 'BACKUP-02: the single-flight index is missing';
    END IF;

    -- The index must key on `kind`; a `(status)` key would mean the BACKUP-01
    -- guard survived and an object job could block a database backup.
    IF NOT EXISTS (
        SELECT 1 FROM pg_index i
        JOIN pg_class c ON c.oid = i.indexrelid
        WHERE c.relname = 'backup_jobs_single_flight_idx'
          AND pg_get_indexdef(i.indexrelid) LIKE '%(kind)%'
    ) THEN
        RAISE EXCEPTION 'BACKUP-02: the single-flight index is not keyed on kind';
    END IF;

    -- Single-flight must hold per kind on live data, not only on write.
    SELECT count(*) INTO offending_kinds
    FROM (
        SELECT count(*) AS active
        FROM public.backup_jobs
        WHERE status IN ('queued', 'running')
        GROUP BY kind
    ) per_kind
    WHERE active > 1;

    IF offending_kinds > 0 THEN
        RAISE EXCEPTION
            'BACKUP-02: % job kind(s) violate the single-flight guarantee',
            offending_kinds;
    END IF;

    RAISE NOTICE
        'BACKUP-02: backup sets + verification live (single-flight now per kind).';
END
$ct_backup_02$;

COMMIT;
