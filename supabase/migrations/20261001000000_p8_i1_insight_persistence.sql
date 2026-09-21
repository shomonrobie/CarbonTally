-- ============================================================================
-- CarbonTally Phase 8 — CarbonTally Insight I1 — persistent conversation
-- foundation (Layer 1 only).
-- File: 20261001000000_p8_i1_insight_persistence.sql
--
-- AUTHORITY
--   * docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md
--     (D2 PO-ratified): §5.1 conversations are persisted; §6 separate
--     conversational domain (never the human messaging tables); §7 three-layer
--     model with Layer 1 at I1 (Layer 2 AI interaction record + Layer 3
--     canonical audit event remain I4); §3.2.1/§3.8 canonical
--     `carbontally_insight_*` naming for all new implementation; §9.2 initial
--     creator-private visibility; §8 every read re-authorised, stored
--     references are not grants; §24.2 the I1 MAY-include list; §24.3/§23.3 the
--     I1 MUST-NOT-expand list; §24.6 I1 must state its RLS posture explicitly.
--   * Cline implementation authorization CT-P8-I1-INSIGHT-PERSISTENCE-20260921-002.
--
-- SCOPE — two new tables, their indexes/constraints, RLS and privileges.
--
-- EXPLICIT NON-SCOPE (not created, not altered, not referenced)
--   * NO product status vocabulary (D2 §11.6 defers it); NO retention/archival/
--     deletion semantics (I7, D2 §20); NO billing/allowance fields (I8, §21).
--   * NO AI interaction / audit / model / provider fields (I4/I8; D2 §7.1, §22).
--   * `public.ai_content_history` is NOT reused, migrated, altered or deleted
--     (D2 §22; prompt §8) — its treatment stays open for I3/I4.
--   * Human messaging (`public.conversations`, `public.messages`,
--     `public.message_activity_log`) is NOT touched or coupled (D2 §6.2).
--   * No `ask_*` object is created (D2 §3.8 supersession).
--
-- RLS POSTURE (explicit, D2 §24.6 — not left to the dynamic tenant mechanism)
--   anon          : REVOKE ALL (no client surface)
--   authenticated : SELECT + INSERT on both tables, gated by the policies below
--                   (no UPDATE, no DELETE in I1)
--   service_role  : ALL (the FastAPI backend is the writer and re-authorises
--                   every read in code; it BYPASSes RLS by design)
--   Creator-private: a conversation is visible to its creator within its
--   organisation only (D2 §9.2). Stored references are not grants (D2 §8.4).
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Layer-1 conversation persistence
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.carbontally_insight_conversations (
    id               uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id  uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    -- Creator identity (creator-private visibility, D2 §9.2). No FK into the
    -- auth schema: existing platform tables treat the principal as an id.
    created_by       uuid NOT NULL,
    -- Optional human-readable label for conversation listing (technical minimum).
    title            text,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now(),
    -- Composite key target: lets a message prove its own organisation matches
    -- its conversation's organisation structurally (no trigger needed).
    CONSTRAINT ci_conversations_id_org_unique UNIQUE (id, organization_id)
);

CREATE INDEX IF NOT EXISTS idx_ci_conversations_org_created
    ON public.carbontally_insight_conversations (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ci_conversations_org_creator_created
    ON public.carbontally_insight_conversations (organization_id, created_by, created_at DESC);

-- ---------------------------------------------------------------------------
-- 2. Layer-1 message persistence (separate domain, D2 §6.2)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.carbontally_insight_messages (
    id               uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    conversation_id  uuid NOT NULL,
    -- Denormalised organisation key: required so the RLS predicate can be
    -- expressed on the row itself (D2 §24.6) and so org-scoped queries cannot
    -- leak across tenants. Kept consistent by the composite FK below.
    organization_id  uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    created_by       uuid,
    -- Author kind only: 'user' = human-authored; 'insight' = CarbonTally
    -- Insight-authored (no LLM exists in I1 — the value is future-safe, not
    -- implemented). NOT an answer status (D2 §11.6 defers that vocabulary).
    role             varchar(16) NOT NULL,
    content          text NOT NULL,
    -- 1-based ordinal within the conversation; ordering is explicit and stable.
    ordinal          integer NOT NULL,
    created_at       timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT ci_messages_role_check CHECK (role IN ('user', 'insight')),
    CONSTRAINT ci_messages_ordinal_check CHECK (ordinal >= 1),
    CONSTRAINT ci_messages_content_check CHECK (length(content) > 0),
    CONSTRAINT ci_messages_user_has_author_check CHECK (role <> 'user' OR created_by IS NOT NULL),
    CONSTRAINT ci_messages_conversation_fk
        FOREIGN KEY (conversation_id, organization_id)
        REFERENCES public.carbontally_insight_conversations (id, organization_id)
        ON DELETE CASCADE,
    CONSTRAINT ci_messages_ordinal_unique UNIQUE (conversation_id, ordinal)
);

CREATE INDEX IF NOT EXISTS idx_ci_messages_conversation_ordinal
    ON public.carbontally_insight_messages (conversation_id, ordinal);
CREATE INDEX IF NOT EXISTS idx_ci_messages_org
    ON public.carbontally_insight_messages (organization_id);

-- ---------------------------------------------------------------------------
-- 3. Privilege posture (mirrors the P8 B2 evidence_line_items pattern)
-- ---------------------------------------------------------------------------
ALTER TABLE public.carbontally_insight_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.carbontally_insight_messages      ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.carbontally_insight_conversations FROM anon;
REVOKE ALL ON TABLE public.carbontally_insight_messages      FROM anon;

GRANT SELECT, INSERT ON TABLE public.carbontally_insight_conversations TO authenticated;
GRANT SELECT, INSERT ON TABLE public.carbontally_insight_messages      TO authenticated;
REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, MAINTAIN
    ON TABLE public.carbontally_insight_conversations FROM authenticated;
REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, MAINTAIN
    ON TABLE public.carbontally_insight_messages FROM authenticated;

GRANT ALL ON TABLE public.carbontally_insight_conversations TO service_role;
GRANT ALL ON TABLE public.carbontally_insight_messages      TO service_role;

-- ---------------------------------------------------------------------------
-- 4. Policies — creator-private within the organisation (D2 §8, §9.2, §24.6)
--    Predicates are re-evaluated per statement from the caller's own identity
--    (`auth.uid()`): a stored id or reference confers no access. No UPDATE /
--    DELETE policy exists in I1 (no such client surface exists).
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'carbontally_insight_conversations'
          AND policyname = 'ci_conversations_creator_select'
    ) THEN
        CREATE POLICY ci_conversations_creator_select
            ON public.carbontally_insight_conversations
            FOR SELECT TO authenticated
            USING (
                public.is_org_member(organization_id)
                AND created_by = auth.uid()
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'carbontally_insight_conversations'
          AND policyname = 'ci_conversations_creator_insert'
    ) THEN
        CREATE POLICY ci_conversations_creator_insert
            ON public.carbontally_insight_conversations
            FOR INSERT TO authenticated
            WITH CHECK (
                public.is_org_member(organization_id)
                AND created_by = auth.uid()
            );
    END IF;
END $$;

-- Messages inherit visibility from their conversation: the caller must be an
-- active member of the message's organisation AND the creator of the parent
-- conversation (I1 has no separate sharing semantics).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'carbontally_insight_messages'
          AND policyname = 'ci_messages_conversation_creator_select'
    ) THEN
        CREATE POLICY ci_messages_conversation_creator_select
            ON public.carbontally_insight_messages
            FOR SELECT TO authenticated
            USING (
                public.is_org_member(organization_id)
                AND EXISTS (
                    SELECT 1
                      FROM public.carbontally_insight_conversations c
                     WHERE c.id = carbontally_insight_messages.conversation_id
                       AND c.organization_id = carbontally_insight_messages.organization_id
                       AND c.created_by = auth.uid()
                )
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'carbontally_insight_messages'
          AND policyname = 'ci_messages_conversation_creator_insert'
    ) THEN
        CREATE POLICY ci_messages_conversation_creator_insert
            ON public.carbontally_insight_messages
            FOR INSERT TO authenticated
            WITH CHECK (
                public.is_org_member(organization_id)
                AND created_by = auth.uid()
                AND EXISTS (
                    SELECT 1
                      FROM public.carbontally_insight_conversations c
                     WHERE c.id = carbontally_insight_messages.conversation_id
                       AND c.organization_id = carbontally_insight_messages.organization_id
                       AND c.created_by = auth.uid()
                )
            );
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 5. Comments — the I1 boundary is recorded in the schema itself.
-- ---------------------------------------------------------------------------
COMMENT ON TABLE public.carbontally_insight_conversations IS
    'CarbonTally Insight I1 (D2 §5.1/§7) — Layer-1 persistent conversations; separate conversational domain (D2 §6), never the human messaging tables; creator-private within the organisation (D2 §9.2). I1 boundary: no status vocabulary, no retention/archival, no billing, no AI interaction/audit fields (I4/I7/I8).';
COMMENT ON COLUMN public.carbontally_insight_conversations.created_by IS
    'Creator principal id; creator-private visibility (D2 §9.2). A stored id is not a grant (D2 §8.4).';
COMMENT ON TABLE public.carbontally_insight_messages IS
    'CarbonTally Insight I1 (D2 §7) — Layer-1 persisted messages. The denormalised organization_id makes the RLS predicate expressible on the row (D2 §24.6) and is held consistent by the composite FK to the conversation. No AI interaction record (Layer 2) is written here; that is I4.';
COMMENT ON COLUMN public.carbontally_insight_messages.role IS
    'Author kind only: user | insight. NOT an answer status — the exact answer-state vocabulary is deliberately deferred by D2 §11.6 (I3/I4).';
COMMENT ON COLUMN public.carbontally_insight_messages.ordinal IS
    '1-based ordinal within the conversation; explicit, stable ordering (I1 retrieval requirement).';
