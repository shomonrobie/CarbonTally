-- ============================================================
-- CarbonTally Phase 5 — WS2 / D39: PE ↔ CarbonTally Operations
-- operational messaging (PE-MSG-001) — Option B.
--
-- Extends the EXISTING conversation family. Additive + idempotent.
--  * conversation_kind discriminator: 'org' (existing, default) vs 'entity'
--  * processing_entity_id on conversations (entity-scoped operational threads)
--  * context jsonb for optional batch/item work context
--  * organization_id (conversations + messages) becomes nullable ONLY for
--    entity-kind rows; a CHECK guarantees exactly one scope per conversation.
--  * Entity-scope RLS policies + helpers so NULL-org rows can never satisfy an
--    existing organisation policy and entity conversations are visible only to
--    the owning ACTIVE processing entity's staff and authorised CarbonTally
--    Operations (internal staff with can_manage_staff).
-- Existing org rows are untouched (conversation_kind='org', org NOT NULL).
-- ============================================================

ALTER TABLE public.conversations
    ADD COLUMN IF NOT EXISTS conversation_kind text;

ALTER TABLE public.conversations
    ADD COLUMN IF NOT EXISTS processing_entity_id uuid
    REFERENCES public.processing_entities (id);

ALTER TABLE public.conversations
    ADD COLUMN IF NOT EXISTS context jsonb;

UPDATE public.conversations SET conversation_kind = 'org'
 WHERE conversation_kind IS NULL;

ALTER TABLE public.conversations
    ALTER COLUMN conversation_kind SET DEFAULT 'org';

ALTER TABLE public.conversations
    ALTER COLUMN conversation_kind SET NOT NULL;

-- organisation scope may be NULL ONLY for entity-kind conversations.
ALTER TABLE public.conversations
    ALTER COLUMN organization_id DROP NOT NULL;

ALTER TABLE public.messages
    ALTER COLUMN organization_id DROP NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conname = 'conversations_scope_kind_consistent'
           AND conrelid = 'public.conversations'::regclass
    ) THEN
        ALTER TABLE public.conversations ADD CONSTRAINT conversations_scope_kind_consistent CHECK (
            (conversation_kind = 'org' AND organization_id IS NOT NULL
                 AND processing_entity_id IS NULL) OR
            (conversation_kind = 'entity' AND organization_id IS NULL
                 AND processing_entity_id IS NOT NULL)
        );
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_conversations_entity
    ON public.conversations (processing_entity_id, conversation_kind);

CREATE INDEX IF NOT EXISTS ix_conversations_kind
    ON public.conversations (conversation_kind, created_at DESC);

-- ---------------------------------------------------------------------------
-- RLS helpers (SECURITY DEFINER, same pattern as rc2_rls helpers).
-- ---------------------------------------------------------------------------

-- Caller is an ACTIVE member of an ACTIVE processing entity.
CREATE OR REPLACE FUNCTION public.is_active_pe_member(p_entity uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$    SELECT EXISTS (
        SELECT 1
          FROM public.staff_profiles sp
          JOIN public.processing_entities pe ON pe.id = sp.entity_id
         WHERE sp.entity_id = p_entity
           AND sp.user_id = auth.uid()
           AND coalesce(sp.is_active, true) = true
           AND coalesce(pe.status, '') = 'active'
    );$$;

-- Caller is authorised CarbonTally Operations for PE operational messaging:
-- INTERNAL staff (entity_id NULL) whose staff role grants can_manage_staff.
CREATE OR REPLACE FUNCTION public.is_ops_messaging_staff()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$    SELECT EXISTS (
        SELECT 1
          FROM public.staff_profiles sp
          JOIN public.staff_roles sr ON sr.id = sp.role_id
         WHERE sp.user_id = auth.uid()
           AND sp.entity_id IS NULL
           AND coalesce(sp.is_active, true) = true
           AND coalesce(sr.permissions->>'can_manage_staff', 'false')::boolean = true
    );$$;

-- Entity conversation visibility: owner-entity PE staff OR authorised Ops.
CREATE OR REPLACE FUNCTION public.can_view_entity_conversation(p_conversation uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$    SELECT EXISTS (
        SELECT 1 FROM public.conversations c
         WHERE c.id = p_conversation
           AND c.conversation_kind = 'entity'
           AND (
               (c.processing_entity_id IS NOT NULL
                    AND public.is_active_pe_member(c.processing_entity_id))
               OR public.is_ops_messaging_staff()
           )
    );$$;

-- ---------------------------------------------------------------------------
-- Entity-scope policies (SELECT). Organisation policies are untouched and
-- cannot match NULL-org entity rows (is_org_member/is_org_consultant both
-- require organisation_id = p_org, which never matches NULL).
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS conversations_entity_select ON public.conversations;
CREATE POLICY conversations_entity_select ON public.conversations
    FOR SELECT TO authenticated
    USING (public.can_view_entity_conversation(id));

DROP POLICY IF EXISTS messages_entity_select ON public.messages;
CREATE POLICY messages_entity_select ON public.messages
    FOR SELECT TO authenticated
    USING (public.can_view_entity_conversation(conversation_id));

DROP POLICY IF EXISTS conversation_participants_entity_select
    ON public.conversation_participants;
CREATE POLICY conversation_participants_entity_select
    ON public.conversation_participants
    FOR SELECT TO authenticated
    USING (public.can_view_entity_conversation(conversation_id));
