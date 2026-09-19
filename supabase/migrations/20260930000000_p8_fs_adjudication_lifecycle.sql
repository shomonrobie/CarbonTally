-- ============================================================================
-- CarbonTally — F-039-1 activity clarification: ADJUDICATION LIFECYCLE
-- File: 20260930000000_p8_fs_adjudication_lifecycle.sql
--
-- PURPOSE (PO decisions D-F039-1-A/-B/-C/-D/-F/-G/-H)
--   An activity clarification is a PERSISTENT, VERSIONED adjudication — not a
--   transient API response. This migration lets the stored row carry:
--     * a stable adjudication identity across versions  (adjudication_id)
--     * immutable version history                       (version, supersedes_id)
--     * exactly one current/effective version           (is_current)
--     * the bounded reuse scope                         (effective_context_key)
--     * evidence compatibility / conflict detection     (evidence_signature)
--     * authoritative provenance context                (evidence_context jsonb)
--     * factor-set drift surfaced, history never rewritten
--                                                       (re_evaluation_required)
--
-- HISTORY RULE (D-039-1-D/-H): a modification INSERTS a new version and flips
--   ``is_current`` on the previous row. No row is deleted and no historical factor
--   metadata is rewritten, so history survives a later factor-set change.
--
-- UNIQUENESS (idempotency preserved, no destructive overwrite)
--   OLD: UNIQUE(activity_key, original_activity, clarification)
--   NEW: UNIQUE(adjudication_id, version)                          — version identity
--        UNIQUE(activity_key, original_activity, clarification, version)
--                                                                  — replay = same version
--        UNIQUE(adjudication_id) WHERE is_current                  — one effective version
--   The old constraint must go: it would forbid a NEW version that changes only the
--   clarification — which is exactly what a modification is.
--
-- CONVENTIONS: guarded/idempotent (DO blocks + IF NOT EXISTS); GRANTs unchanged;
--   RLS left ENABLED with the four tenant policies untouched — the new columns are
--   covered by the same row policies.
--
-- STATUS: applied and verified ONLY in the dedicated disposable carbontally_test
--   database. NEVER applied to production.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Lifecycle columns (idempotent)
-- ---------------------------------------------------------------------------
ALTER TABLE public.activity_clarifications
    ADD COLUMN IF NOT EXISTS adjudication_id        uuid,
    ADD COLUMN IF NOT EXISTS version                integer NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS supersedes_id          uuid,
    ADD COLUMN IF NOT EXISTS is_current             boolean NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS effective_context_key  text,
    ADD COLUMN IF NOT EXISTS evidence_signature     text,
    ADD COLUMN IF NOT EXISTS evidence_context       jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS re_evaluation_required boolean NOT NULL DEFAULT false;

-- ---------------------------------------------------------------------------
-- 2. Backfill existing rows as version 1 / current of their own adjudication
-- ---------------------------------------------------------------------------
UPDATE public.activity_clarifications
   SET adjudication_id = COALESCE(adjudication_id, id),
       effective_context_key = COALESCE(effective_context_key, activity_key)
 WHERE adjudication_id IS NULL
    OR effective_context_key IS NULL;

ALTER TABLE public.activity_clarifications
    ALTER COLUMN adjudication_id SET NOT NULL,
    ALTER COLUMN effective_context_key SET NOT NULL;

-- ---------------------------------------------------------------------------
-- 3. Self-reference: the version this row supersedes (history linkage)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'activity_clarifications_supersedes_fkey'
           AND conrelid = 'public.activity_clarifications'::regclass
    ) THEN
        ALTER TABLE public.activity_clarifications
            ADD CONSTRAINT activity_clarifications_supersedes_fkey
            FOREIGN KEY (supersedes_id)
            REFERENCES public.activity_clarifications(id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 4. Uniqueness: version identity + one current version (idempotent swap)
-- ---------------------------------------------------------------------------
ALTER TABLE public.activity_clarifications
    DROP CONSTRAINT IF EXISTS activity_clarifications_unique;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'activity_clarifications_version_unique'
           AND conrelid = 'public.activity_clarifications'::regclass
    ) THEN
        ALTER TABLE public.activity_clarifications
            ADD CONSTRAINT activity_clarifications_version_unique
            UNIQUE (adjudication_id, version);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'activity_clarifications_replay_unique'
           AND conrelid = 'public.activity_clarifications'::regclass
    ) THEN
        ALTER TABLE public.activity_clarifications
            ADD CONSTRAINT activity_clarifications_replay_unique
            UNIQUE (activity_key, original_activity, clarification, version);
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS activity_clarifications_current_unique
    ON public.activity_clarifications (adjudication_id)
    WHERE is_current;

-- ---------------------------------------------------------------------------
-- 5. Lookup indexes for the consumption path (Finding 1)
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS activity_clarifications_effective_idx
    ON public.activity_clarifications
       (organization_id, effective_context_key, activity_key, original_activity)
    WHERE is_current;
CREATE INDEX IF NOT EXISTS activity_clarifications_history_idx
    ON public.activity_clarifications (adjudication_id, version DESC);
