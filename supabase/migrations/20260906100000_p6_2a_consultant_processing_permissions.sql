-- ============================================================================
-- P6-2A — Consultant Processing Capability Flags
-- ----------------------------------------------------------------------------
-- Ratified under P6-2-D1 (consultant processing authorization contract).
--
-- Additive + idempotent + backward-compatible + DENY-BY-DEFAULT.
--
-- Consultant processing authority becomes EXPLICIT and permission-based, in
-- the same real-column architecture as the existing relationship flags on
-- `consultant_firm_members` (can_manage_clients / can_upload_documents /
-- can_generate_reports / can_manage_team).
--
-- New flags (all default FALSE — no existing membership gains processing
-- authority by this migration):
--   * can_extract            — manual extraction / data entry
--   * can_map                — activity mapping
--   * can_validate           — item validation
--   * can_calculate          — authoritative calculation
--   * can_confirm_automation — Gate-6 human-after-automation confirmation
--   * can_submit             — submit-for-review (authorization only; the
--                              workflow submit action lands in a later P6-2
--                              workstream)
--
-- Existing relationship / read / upload functionality is unaffected.
-- No other table is touched. RLS is unchanged.
-- ============================================================================

ALTER TABLE public.consultant_firm_members
    ADD COLUMN IF NOT EXISTS can_extract            boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS can_map                boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS can_validate           boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS can_calculate          boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS can_confirm_automation boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS can_submit             boolean NOT NULL DEFAULT false;

COMMENT ON COLUMN public.consultant_firm_members.can_extract IS
    'P6-2A: consultant may perform manual extraction/data-entry on engaged client work.';
COMMENT ON COLUMN public.consultant_firm_members.can_map IS
    'P6-2A: consultant may map extracted activity data.';
COMMENT ON COLUMN public.consultant_firm_members.can_validate IS
    'P6-2A: consultant may run item validation.';
COMMENT ON COLUMN public.consultant_firm_members.can_calculate IS
    'P6-2A: consultant may run the authoritative calculation.';
COMMENT ON COLUMN public.consultant_firm_members.can_confirm_automation IS
    'P6-2A: consultant may confirm/reject automated extraction output (Gate 6).';
COMMENT ON COLUMN public.consultant_firm_members.can_submit IS
    'P6-2A: consultant may submit processed work for review (workflow action deferred).';
