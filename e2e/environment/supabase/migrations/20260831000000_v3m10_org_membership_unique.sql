-- BL-1 / QA-DB-024 — enforce unique organisation membership.
--
-- The canonical schema (00000000000000_init_schema.sql) already defines the
-- unique index ``organization_members_org_user_uniq (organization_id, user_id)``
-- and the RC2 verification suite expects it. This migration makes the invariant
-- explicit and idempotent so any environment that was provisioned without the
-- full init schema converges to the canonical state.
--
-- A duplicate (organisation, user) membership would corrupt role/RLS semantics;
-- the API layer translates a violation into a controlled 409
-- (DuplicateMembershipError), never a second membership row.

CREATE UNIQUE INDEX IF NOT EXISTS organization_members_org_user_uniq
    ON public.organization_members (organization_id, user_id);
