-- ============================================================================
-- CarbonTally Phase 8 — CarbonTally Insight I4 — Layer-2 interaction
-- persistence (append-only evidence) for the authorized I4 stage.
-- File: 20261003000000_p8_i4_insight_interactions.sql
--
-- AUTHORITY
--   * PO I4 Implementation Authorization (2026-09-21) + PO Q1–Q14 decision
--     register, in particular:
--       Q2  canonical audit ledger is public.audit_trail (NOT created here);
--       Q3  I4 answer-status vocabulary is separate from the closed I3 ToolStatus
--           (tool_status below keeps the exact I3 six-value vocabulary);
--       Q4  raw questions live in the I1 message layer; here we store only a
--           sha256 question hash for correlation/integrity;
--       Q5  Layer-2 interaction evidence is append-only/immutable after creation;
--       Q6  only an allowlisted structured projection of tool data is persisted;
--       Q7  Layer 2 owns the interaction lifecycle (I1 is untouched);
--       Q8  creator-private visibility only (no new personas/permissions);
--       Q9  immutable interaction_id + child tool_call_id correlation;
--       Q10 idempotency/uniqueness so retries cannot duplicate identities or
--           the same logical tool call;
--       Q12/Q13 retention/deletion/export and billing are NOT implemented here.
--   * D2 §7 (Layer 2 = I4), §8/§9.2 (every read re-authorised, creator-private),
--     §3.2.1/§3.8 (canonical `carbontally_insight_*` naming).
--   * Master Spec v1.1 §8.1/§9.3 (Layer-2 record), §14 (answer states),
--     §20.1/§20.4 (no layer collapse; no payloads in the ledger).
--
-- SCOPE — two new tables, their indexes/constraints, append-only triggers, RLS
-- and privileges. Additive and idempotent only.
--
-- EXPLICIT NON-SCOPE
--   * `public.ai_content_history` is NOT touched in any way (PO Q1 — retained
--     unchanged, outside I4): no column, index, constraint, grant or policy of
--     that table is created, altered or referenced here.
--   * No canonical-audit table is created (PO Q2 reuses public.audit_trail).
--   * No retention/deletion/export semantics (I7, PO Q12); no billing/credits
--     (I8, PO Q13); no I5 context/compaction structures; no I6 UI.
--   * No raw prompt/answer text and no unrestricted tool payloads are stored
--     here (PO Q4/Q6): text stays in the I1 message layer.
--
-- RLS POSTURE (explicit, matching the I1 pattern)
--   anon          : REVOKE ALL
--   authenticated : SELECT + INSERT only (no UPDATE, no DELETE) gated by the
--                   creator-private policies below
--   service_role  : ALL (the FastAPI backend is the writer and re-authorises
--                   every read in code; it BYPASSes RLS by design)
--   Creator-private: an interaction is visible to its creator within its
--   organisation only (D2 §9.2, PO Q8). Stored references are not grants.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Layer-2 interaction record (PO Q7 lifecycle, Q9 interaction identity)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.carbontally_insight_interactions (
    id               uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id  uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    conversation_id  uuid NOT NULL,
    created_by       uuid NOT NULL,
    -- Lifecycle (PO Q7). Forward-only; enforced by the trigger below.
    lifecycle        varchar(16) NOT NULL DEFAULT 'received',
    -- Authoritative I4 answer state (PO Q3 / Master Spec §14). NULL while running.
    answer_status    varchar(24),
    -- Correlation (PO Q9). The interaction id is the immutable correlation key.
    message_id       uuid,
    audit_record_id  uuid,
    -- Idempotency (PO Q10) — unique per organisation when supplied.
    idempotency_key  varchar(128),
    -- Correlation/integrity without duplicating raw prompt text (PO Q4).
    question_hash    char(64) NOT NULL,
    request_hash     char(64),
    -- Deterministic interpretation (I3 machinery, reused not modified).
    intent           varchar(64),
    intent_source    varchar(16),
    -- Truthful provider attribution (PO Q14) — never the configured value
    -- reported as a successful execution.
    provider         varchar(64),
    model            varchar(160),
    model_version    varchar(64),
    narration_state  varchar(24) NOT NULL DEFAULT 'not_attempted',
    -- Usage/cost remain nullable until authoritative provider usage exists (Q14).
    tokens_used      integer,
    cost             numeric,
    tool_call_count  integer NOT NULL DEFAULT 0,
    reference_count  integer NOT NULL DEFAULT 0,
    error_class      varchar(64),
    metadata         jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at       timestamptz NOT NULL DEFAULT now(),
    completed_at     timestamptz,
    CONSTRAINT ci_interactions_id_org_unique UNIQUE (id, organization_id),
    CONSTRAINT ci_interactions_lifecycle_check
        CHECK (lifecycle IN ('received', 'executing', 'completed', 'failed')),
    CONSTRAINT ci_interactions_answer_status_check
        CHECK (answer_status IS NULL OR answer_status IN (
            'success', 'zero', 'no_data', 'not_authorized', 'insufficient_data',
            'needs_clarification', 'tool_failure', 'provider_unavailable',
            'partial', 'rate_limited', 'refused', 'ungrounded',
            'invalid_input', 'error')),
    CONSTRAINT ci_interactions_intent_source_check
        CHECK (intent_source IS NULL OR intent_source IN ('deterministic', 'none')),
    CONSTRAINT ci_interactions_narration_state_check
        CHECK (narration_state IN ('not_attempted', 'completed', 'unavailable', 'skipped')),
    CONSTRAINT ci_interactions_counts_check
        CHECK (tool_call_count >= 0 AND reference_count >= 0),
    CONSTRAINT ci_interactions_tokens_check
        CHECK (tokens_used IS NULL OR tokens_used >= 0),
    CONSTRAINT ci_interactions_cost_check
        CHECK (cost IS NULL OR cost >= 0),
    -- A terminal lifecycle must carry a completion timestamp; a running one must not.
    CONSTRAINT ci_interactions_completed_at_check
        CHECK ((lifecycle IN ('completed', 'failed')) = (completed_at IS NOT NULL)),
    CONSTRAINT ci_interactions_answer_status_terminal_check
        CHECK (lifecycle IN ('completed', 'failed') OR answer_status IS NULL),
    CONSTRAINT ci_interactions_conversation_fk
        FOREIGN KEY (conversation_id, organization_id)
        REFERENCES public.carbontally_insight_conversations (id, organization_id)
        ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ci_interactions_org_idempotency_unique
    ON public.carbontally_insight_interactions (organization_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_ci_interactions_org_created
    ON public.carbontally_insight_interactions (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ci_interactions_org_creator_created
    ON public.carbontally_insight_interactions (organization_id, created_by, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ci_interactions_conversation
    ON public.carbontally_insight_interactions (conversation_id, created_at ASC);

-- ---------------------------------------------------------------------------
-- 2. Layer-2 tool-call evidence (PO Q6 allowlisted projection, Q9 tool_call_id)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.carbontally_insight_tool_calls (
    id               uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    interaction_id   uuid NOT NULL,
    organization_id  uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    -- Deterministic order of calls inside one interaction.
    call_ordinal     integer NOT NULL,
    -- The closed I3 catalogue only: no tool may be added by I4 (PO Q3/Q6).
    tool_name        varchar(64) NOT NULL,
    contract_version varchar(32) NOT NULL,
    -- Exact closed I3 ToolStatus vocabulary (PO Q3) — never the I4 answer vocabulary.
    tool_status      varchar(24) NOT NULL,
    -- Allowlisted/normalised projections only (PO Q6). No raw payloads, no secrets.
    arguments        jsonb NOT NULL DEFAULT '{}'::jsonb,
    result_metadata  jsonb NOT NULL DEFAULT '{}'::jsonb,
    -- `references` is a PostgreSQL reserved keyword: it must always be quoted
    -- (OHD D-1 — an unquoted identifier aborts the whole migration).
    "references"     jsonb NOT NULL DEFAULT '[]'::jsonb,
    arguments_hash   char(64) NOT NULL,
    result_hash      char(64) NOT NULL,
    result_item_count integer NOT NULL DEFAULT 0,
    truncated        boolean NOT NULL DEFAULT false,
    duration_ms      integer,
    created_at       timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ci_tool_calls_ordinal_check CHECK (call_ordinal >= 1),
    CONSTRAINT ci_tool_calls_tool_name_check
        CHECK (tool_name IN ('report_lookup', 'report_version_lookup',
                             'report_evidence_lookup', 'calculation_snapshot_lookup')),
    CONSTRAINT ci_tool_calls_tool_status_check
        CHECK (tool_status IN ('success', 'no_data', 'not_authorized',
                               'invalid_input', 'provider_unavailable', 'error')),
    CONSTRAINT ci_tool_calls_counts_check
        CHECK (result_item_count >= 0),
    CONSTRAINT ci_tool_calls_duration_check
        CHECK (duration_ms IS NULL OR duration_ms >= 0),
    CONSTRAINT ci_tool_calls_interaction_fk
        FOREIGN KEY (interaction_id, organization_id)
        REFERENCES public.carbontally_insight_interactions (id, organization_id)
        ON DELETE CASCADE,
    -- One position per interaction, and no duplicate logical call (PO Q10): a
    -- retry of the same logical call cannot create a second evidence row.
    CONSTRAINT ci_tool_calls_ordinal_unique UNIQUE (interaction_id, call_ordinal),
    CONSTRAINT ci_tool_calls_logical_unique UNIQUE (interaction_id, tool_name, arguments_hash)
);

CREATE INDEX IF NOT EXISTS idx_ci_tool_calls_interaction
    ON public.carbontally_insight_tool_calls (interaction_id, call_ordinal ASC);
CREATE INDEX IF NOT EXISTS idx_ci_tool_calls_org
    ON public.carbontally_insight_tool_calls (organization_id);

-- ---------------------------------------------------------------------------
-- 3. Append-only enforcement (PO Q5)
--    tool_calls  : no UPDATE, no DELETE, ever.
--    interactions: no DELETE, ever; UPDATE only as a forward-only lifecycle
--                  completion, and never on an immutable evidence column
--                  (identity, org, conversation, creator, created_at, hashes,
--                  idempotency key, message correlation).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.ci_tool_calls_immutable()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'carbontally_insight_tool_calls is append-only (I4 Q5): % is not permitted', TG_OP
        USING ERRCODE = 'raise_exception';
END;
$$;

COMMENT ON FUNCTION public.ci_tool_calls_immutable() IS
    'Phase 8 I4 (PO Q5) — blocks UPDATE/DELETE on Insight Layer-2 tool-call evidence.';

DROP TRIGGER IF EXISTS ci_tool_calls_immutable ON public.carbontally_insight_tool_calls;
CREATE TRIGGER ci_tool_calls_immutable
    BEFORE UPDATE OR DELETE ON public.carbontally_insight_tool_calls
    FOR EACH ROW
    EXECUTE FUNCTION public.ci_tool_calls_immutable();

CREATE OR REPLACE FUNCTION public.ci_interactions_immutable()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION
            'carbontally_insight_interactions is append-only (I4 Q5): DELETE is not permitted'
            USING ERRCODE = 'raise_exception';
    END IF;

    IF OLD.lifecycle IN ('completed', 'failed') THEN
        RAISE EXCEPTION
            'carbontally_insight_interactions: terminal interaction evidence is immutable (I4 Q5)'
            USING ERRCODE = 'raise_exception';
    END IF;

    IF NOT (
        (OLD.lifecycle = 'received'  AND NEW.lifecycle IN ('executing', 'completed', 'failed'))
        OR (OLD.lifecycle = 'executing' AND NEW.lifecycle IN ('completed', 'failed'))
    ) THEN
        RAISE EXCEPTION
            'carbontally_insight_interactions: lifecycle % -> % is not a forward transition (I4 Q5)',
            OLD.lifecycle, NEW.lifecycle
            USING ERRCODE = 'raise_exception';
    END IF;

    IF NEW.id IS DISTINCT FROM OLD.id
       OR NEW.organization_id IS DISTINCT FROM OLD.organization_id
       OR NEW.conversation_id IS DISTINCT FROM OLD.conversation_id
       OR NEW.created_by IS DISTINCT FROM OLD.created_by
       OR NEW.created_at IS DISTINCT FROM OLD.created_at
       OR NEW.question_hash IS DISTINCT FROM OLD.question_hash
       OR NEW.request_hash IS DISTINCT FROM OLD.request_hash
       OR NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key
       OR NEW.message_id IS DISTINCT FROM OLD.message_id THEN
        RAISE EXCEPTION
            'carbontally_insight_interactions: immutable interaction columns cannot change (I4 Q5)'
            USING ERRCODE = 'raise_exception';
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.ci_interactions_immutable() IS
    'Phase 8 I4 (PO Q5) — interaction evidence is insert-only except a forward-only lifecycle completion.';

DROP TRIGGER IF EXISTS ci_interactions_immutable ON public.carbontally_insight_interactions;
CREATE TRIGGER ci_interactions_immutable
    BEFORE UPDATE OR DELETE ON public.carbontally_insight_interactions
    FOR EACH ROW
    EXECUTE FUNCTION public.ci_interactions_immutable();

-- ---------------------------------------------------------------------------
-- 4. Privilege posture (mirrors the I1 pattern; PO Q8 creator-private)
-- ---------------------------------------------------------------------------
ALTER TABLE public.carbontally_insight_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.carbontally_insight_tool_calls   ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.carbontally_insight_interactions FROM anon;
REVOKE ALL ON TABLE public.carbontally_insight_tool_calls   FROM anon;

GRANT SELECT, INSERT ON TABLE public.carbontally_insight_interactions TO authenticated;
GRANT SELECT, INSERT ON TABLE public.carbontally_insight_tool_calls   TO authenticated;
-- Append-only: authenticated clients may never update or delete evidence (Q5).
REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, MAINTAIN
    ON TABLE public.carbontally_insight_interactions FROM authenticated;
REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, MAINTAIN
    ON TABLE public.carbontally_insight_tool_calls FROM authenticated;

GRANT ALL ON TABLE public.carbontally_insight_interactions TO service_role;
GRANT ALL ON TABLE public.carbontally_insight_tool_calls   TO service_role;

-- ---------------------------------------------------------------------------
-- 5. Policies — creator-private within the organisation (PO Q8, D2 §9.2)
--    Predicates are re-evaluated per statement from the caller's own identity
--    (`auth.uid()`): a stored interaction id or reference confers no access.
--    No UPDATE/DELETE policy exists — the evidence surface is append-only.
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'carbontally_insight_interactions'
          AND policyname = 'ci_interactions_creator_select'
    ) THEN
        CREATE POLICY ci_interactions_creator_select
            ON public.carbontally_insight_interactions
            FOR SELECT TO authenticated
            USING (
                public.is_org_member(organization_id)
                AND created_by = auth.uid()
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'carbontally_insight_interactions'
          AND policyname = 'ci_interactions_creator_insert'
    ) THEN
        CREATE POLICY ci_interactions_creator_insert
            ON public.carbontally_insight_interactions
            FOR INSERT TO authenticated
            WITH CHECK (
                public.is_org_member(organization_id)
                AND created_by = auth.uid()
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'carbontally_insight_tool_calls'
          AND policyname = 'ci_tool_calls_creator_select'
    ) THEN
        CREATE POLICY ci_tool_calls_creator_select
            ON public.carbontally_insight_tool_calls
            FOR SELECT TO authenticated
            USING (
                public.is_org_member(organization_id)
                AND EXISTS (
                    SELECT 1 FROM public.carbontally_insight_interactions i
                     WHERE i.id = carbontally_insight_tool_calls.interaction_id
                       AND i.organization_id = carbontally_insight_tool_calls.organization_id
                       AND i.created_by = auth.uid()
                )
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'carbontally_insight_tool_calls'
          AND policyname = 'ci_tool_calls_creator_insert'
    ) THEN
        CREATE POLICY ci_tool_calls_creator_insert
            ON public.carbontally_insight_tool_calls
            FOR INSERT TO authenticated
            WITH CHECK (
                public.is_org_member(organization_id)
                AND EXISTS (
                    SELECT 1 FROM public.carbontally_insight_interactions i
                     WHERE i.id = carbontally_insight_tool_calls.interaction_id
                       AND i.organization_id = carbontally_insight_tool_calls.organization_id
                       AND i.created_by = auth.uid()
                )
            );
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 6. Comments — the I4 boundary is recorded in the schema itself.
-- ---------------------------------------------------------------------------
COMMENT ON TABLE public.carbontally_insight_interactions IS
    'CarbonTally Insight I4 (PO Q7/Q9) — Layer-2 interaction evidence: immutable interaction identity, creator-private, forward-only lifecycle, I4 answer state, truthful provider attribution. Append-only (PO Q5). Raw question text lives in the I1 message layer (PO Q4). No retention/deletion/export (I7) and no billing (I8). Does not use public.ai_content_history (PO Q1).';
COMMENT ON TABLE public.carbontally_insight_tool_calls IS
    'CarbonTally Insight I4 (PO Q6/Q9) — Layer-2 tool-call evidence: child of one interaction, closed I3 tool catalogue and closed I3 ToolStatus, allowlisted argument/result projections only. Append-only. Stored references are locators, never authorization grants.';
COMMENT ON COLUMN public.carbontally_insight_interactions.answer_status IS
    'Authoritative I4 answer state (Master Spec §14). Deliberately separate from the closed I3 tool_status vocabulary (PO Q3).';
COMMENT ON COLUMN public.carbontally_insight_interactions.question_hash IS
    'sha256 of the raw question for correlation/integrity only; the raw question is persisted once, in the I1 message layer (PO Q4).';
COMMENT ON COLUMN public.carbontally_insight_tool_calls.tool_status IS
    'Exact closed I3 ToolStatus vocabulary (PO Q3): success | no_data | not_authorized | invalid_input | provider_unavailable | error.';

-- ---------------------------------------------------------------------------
-- 7. Post-conditions (fail loudly rather than silently mis-provision)
-- ---------------------------------------------------------------------------
DO $$
DECLARE
    pol_count int;
BEGIN
    SELECT count(*) INTO pol_count
      FROM pg_policies
     WHERE schemaname = 'public'
       AND tablename IN ('carbontally_insight_interactions', 'carbontally_insight_tool_calls');
    IF pol_count < 4 THEN
        RAISE EXCEPTION
            'I4 precondition failed: expected >= 4 creator-private policies, found %', pol_count;
    END IF;
END $$;
