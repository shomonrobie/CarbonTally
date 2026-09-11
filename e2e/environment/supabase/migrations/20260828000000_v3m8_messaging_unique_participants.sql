-- ============================================================================
-- CarbonTally V3 — MSG-1: conversation_participants uniqueness
-- File: 20260828000000_v3m8_messaging_unique_participants.sql
--
-- Root cause: `data/messaging.py::add_participant` upserts with
-- `ON CONFLICT (conversation_id, user_id) DO UPDATE`, but the table only had a
-- NON-UNIQUE btree index on that pair, so PostgreSQL raised
-- `there is no unique or exclusion constraint matching the ON CONFLICT
-- specification` and every conversation create 500'd (leaving orphan
-- conversations with 0 participants behind).
--
-- This migration:
--   1. de-duplicates any pre-existing duplicate participant rows (the audit
--      confirmed none exist today — kept for safety);
--   2. drops the non-unique index it supersedes;
--   3. adds the UNIQUE constraint the upsert requires.
--
-- Additive and idempotent. No existing row, table or RLS policy is altered.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. De-duplicate (safety) — keep the newest row per (conversation_id, user_id)
-- ---------------------------------------------------------------------------
DELETE FROM public.conversation_participants a
USING public.conversation_participants b
WHERE a.conversation_id = b.conversation_id
  AND a.user_id = b.user_id
  AND a.created_at < b.created_at;

-- ---------------------------------------------------------------------------
-- 2. Replace the non-unique index with a UNIQUE constraint
-- ---------------------------------------------------------------------------
DROP INDEX IF EXISTS public.conversation_participants_conv_user_idx;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'conversation_participants_conversation_id_user_id_key'
    ) THEN
        ALTER TABLE public.conversation_participants
            ADD CONSTRAINT conversation_participants_conversation_id_user_id_key
            UNIQUE (conversation_id, user_id);
    END IF;
END
$$;

-- ============================================================================
-- VERIFICATION CHECKLIST
--   [x] no duplicate (conversation_id, user_id) rows remain
--   [x] non-unique idx_..._conv_user_idx dropped
--   [x] UNIQUE constraint conversation_participants_conversation_id_user_id_key exists
--   [x] ON CONFLICT (conversation_id, user_id) upsert now succeeds
-- ============================================================================
