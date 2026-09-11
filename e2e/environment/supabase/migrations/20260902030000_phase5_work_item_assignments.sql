-- ============================================================
-- CarbonTally Phase 5 — WS1 / D38: Work-item assignment ledger
-- (canonical V3 assignment / reassignment / attribution).
--
-- Additive only. The existing `manual_extraction_items` table remains the
-- canonical work-item representation. This ledger records append-only,
-- current-plus-historical assignment attribution for those items.
--
-- Immutable V1.2 provenance (manual_extraction_items.processing_origin /
-- processing_entity_id) is NEVER written by this migration or by the D38
-- service; current assignment is a separate, changeable concept.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.work_item_assignments (
    id                            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    manual_extraction_item_id     uuid NOT NULL
                                  REFERENCES public.manual_extraction_items (id)
                                  ON DELETE CASCADE,
    status                        text NOT NULL DEFAULT 'open'
                                  CHECK (status IN ('open', 'closed')),
    action                        text NOT NULL
                                  CHECK (action IN
                                    ('assign', 'reassign', 'claim', 'recover')),
    assignee_kind                 text NOT NULL
                                  CHECK (assignee_kind IN
                                    ('internal_staff', 'processing_entity')),
    assigned_to                   uuid,
    processing_entity_id          uuid
                                  REFERENCES public.processing_entities (id),
    assigned_by                   uuid NOT NULL,
    actor_domain                  text NOT NULL
                                  CHECK (actor_domain IN
                                    ('internal_staff', 'processing_entity')),
    previous_assigned_to          uuid,
    previous_processing_entity_id uuid,
    reason                        text,
    close_action                  text CHECK (close_action IN
                                    ('released', 'completed', 'reassigned',
                                     'recovered', 'superseded')),
    closed_by                     uuid,
    closed_at                     timestamptz,
    created_at                    timestamptz NOT NULL DEFAULT now(),
    updated_at                    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT work_item_assignee_shape CHECK (
        (assignee_kind = 'internal_staff'  AND assigned_to IS NOT NULL
            AND processing_entity_id IS NULL) OR
        (assignee_kind = 'processing_entity' AND processing_entity_id IS NOT NULL
            AND assigned_to IS NULL)
    )
);

-- At most ONE open assignment per work item (claim/assign concurrency guard).
CREATE UNIQUE INDEX IF NOT EXISTS uq_work_item_assignments_open
    ON public.work_item_assignments (manual_extraction_item_id)
    WHERE status = 'open';

CREATE INDEX IF NOT EXISTS ix_work_item_assignments_item
    ON public.work_item_assignments (manual_extraction_item_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_work_item_assignments_assignee
    ON public.work_item_assignments (assignee_kind, assigned_to)
    WHERE status = 'open';

CREATE INDEX IF NOT EXISTS ix_work_item_assignments_entity
    ON public.work_item_assignments (processing_entity_id)
    WHERE status = 'open' AND assignee_kind = 'processing_entity';

-- Backend repositories access this ledger through the asyncpg pool (bypassing
-- RLS exactly as the rest of the V3 workflow tables). RLS is enabled with NO
-- policies so no PostgREST/authenticated client can ever read or write the
-- ledger directly — the V3 API contract is the only access path.
ALTER TABLE public.work_item_assignments ENABLE ROW LEVEL SECURITY;
