-- ============================================================================
-- CarbonTally Phase 8 — CarbonTally Insight I2 — authorization boundary
-- hardening (narrow).
-- File: 20261002000000_p8_i2_insight_authorization.sql
--
-- AUTHORITY
--   * docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md
--     §8 (authorization boundary; stored references are not grants), §9.2
--     (initial visibility = creator-private), §10.4 (PE: no Insight capability).
--   * PO decision (2026-09-21) — ratified Insight access model (customer /
--     consultant / staff-admin / no auditor / no PE / no public).
--   * OHD independent I1 verification (commit 66adfb5, verdict PASS) findings
--     F-03 (client may forge `role='insight'` via the database path) and the
--     bounded I1 hardening instruction. F-01/F-04 are resolved in code; F-02 by
--     explicit parameter casts; F-05 is a carried invariant (service_role
--     bypasses RLS, so application-layer scoping remains the boundary).
--
-- SCOPE — ONE policy replacement, nothing else.
--   `ci_messages_conversation_creator_insert` gains the author-kind condition
--   `role = 'user'`: an authenticated CLIENT may only persist human-authored
--   messages. The reserved `insight` author kind (D2 §7 Layer 2/3, I4) can then
--   only be written by the service-role backend, which is the only writer that
--   is authorized to attribute content to CarbonTally.
--
--   Not scope: no table/column/index/constraint change; no INSERT grant change;
--   no conversation policy change; no SELECT policy change; no change to the
--   human messaging domain; no audit/AI-interaction semantics (I4); no reuse or
--   alteration of `public.ai_content_history`.
--
-- WHY THIS IS THE MINIMUM CHANGE
--   The invariant "a client cannot forge an author kind it is not authorized to
--   author" is expressible directly in the existing WITH CHECK predicate, which
--   is already re-evaluated per statement from the caller's own identity
--   (`auth.uid()`). No trigger, no new column and no application trust are
--   introduced.
--
-- ROLLOUT NOTE
--   The backend uses `service_role` (BYPASSRLS) and is unaffected. Only the
--   authenticated (PostgREST/client) path is tightened, and only for the one
--   reserved author-kind value that the FastAPI layer already rejects (422).
--   Apply to persistent environments only under separate authorization.
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'carbontally_insight_messages'
          AND policyname = 'ci_messages_conversation_creator_insert'
    ) THEN
        DROP POLICY ci_messages_conversation_creator_insert
            ON public.carbontally_insight_messages;
    END IF;

    CREATE POLICY ci_messages_conversation_creator_insert
        ON public.carbontally_insight_messages
        FOR INSERT TO authenticated
        WITH CHECK (
            public.is_org_member(organization_id)
            AND created_by = auth.uid()
            -- I2 / F-03 — author-kind integrity: a client may author only
            -- human-authored messages. `insight` rows are backend-only.
            AND role = 'user'
            AND EXISTS (
                SELECT 1
                  FROM public.carbontally_insight_conversations c
                 WHERE c.id = carbontally_insight_messages.conversation_id
                   AND c.organization_id = carbontally_insight_messages.organization_id
                   AND c.created_by = auth.uid()
            )
        );
END $$;

COMMENT ON POLICY ci_messages_conversation_creator_insert
    ON public.carbontally_insight_messages IS
    'I1 creator-private append + I2 author-kind integrity (OHD F-03): the authenticated client may insert only role = ''user'' rows, inside its own organisation and its own conversation. The reserved ''insight'' author kind is written exclusively by the service-role backend (future I4).';
