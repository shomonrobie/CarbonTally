-- CT-CONSULTANT-MODEL-IMPLEMENTATION-02 (Phase 1) — consultant capability model.
--
-- Task:   CT-CONSULTANT-MODEL-IMPLEMENTATION-02
-- Source: docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md
--         §7.2/§7.3 (capability chain + mandatory capability properties),
--         §13.1 (approval contract, PO-6 B+C), §17.1 F-1/F-2, §17.2 F-10,
--         §20.1 AC-F-1 / AC-F-2 / AC-F-18, §20.4 NT-10 / NT-11 / NT-12 / NT-24.
--
-- WHY
--   F-1: consultant ADMISSION was capability-blind. `resolve_managed_org_ids`
--        and `ensure_consultant_org_access` admitted on the existence of an
--        ACTIVE consultant_clients row alone, so every non-processing consultant
--        route reusing the organisation guard was effectively "has relationship
--        = full access" — forbidden outright by §7.4. CAP-VIEW-CLIENT (the
--        roster/workspace admission capability) had no column to be checked.
--   F-2: PO-6 (B+C) / §13.1 require FINAL approval on a consultant-MANAGED
--        organisation to be authorised by a consultant capability (CAP-APPROVE),
--        separable from processing/mapping. The only `can_approve` flags in the
--        system lived in the CarbonTally STAFF surface (a different identity
--        plane), so the capability did not exist to be checked.
--
-- SCOPE OF THIS MIGRATION
--   Additive columns only. No RLS policy is added, dropped, disabled or
--   weakened (AGENTS.md §67): the new columns are read by the application
--   authorization layer (`backend/api/consultant_auth.py`), not by RLS, which
--   continues to resolve consultant scope through the existing
--   `public.is_org_consultant(org)` helper.
--
--   Deny-by-default: both columns default FALSE, so a firm member created after
--   this migration holds NO admission and NO approval capability until the firm
--   explicitly grants it (AC-F-18 — nothing is granted by omission).

ALTER TABLE public.consultant_firm_members
    ADD COLUMN IF NOT EXISTS can_view_client boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS can_approve     boolean NOT NULL DEFAULT false;

COMMENT ON COLUMN public.consultant_firm_members.can_view_client IS
    'CAP-VIEW-CLIENT (§7.3): see a client in the firm roster / open its '
    'workspace. Consultant ADMISSION requires this capability — relationship '
    'existence alone never admits (§7.4, F-1). Grantable/revocable per member.';

COMMENT ON COLUMN public.consultant_firm_members.can_approve IS
    'CAP-APPROVE (§7.3, §13.1): give FINAL approval on behalf of a '
    'consultant-managed organisation (PO-6 B+C). Deliberately separable from '
    'the processing/mapping capabilities, so one person need not both produce '
    'and approve (F-2). Grantable/revocable per member.';

-- IMPL-1 backfill — preserve pre-existing de-facto consultant scope.
--
-- Before this migration an ACTIVE firm member reached every organisation the
-- firm held an ACTIVE grant for. Removing that would silently break every
-- already-provisioned consultant (including the investor demo roster) the
-- moment the F-1 admission gate lands. The existing de-facto scope is
-- therefore preserved EXPLICITLY as a granted CAP-VIEW-CLIENT for rows that
-- already exist; the new columns stay FALSE for every row created afterwards.
--
-- `can_approve` is deliberately NOT backfilled: no consultant implementation
-- path could previously give final approval on a managed organisation (that is
-- exactly finding F-2), so granting it here would invent an authority nobody
-- held. It must be granted explicitly (the firm/capability-write path).
UPDATE public.consultant_firm_members
   SET can_view_client = true,
       updated_at = NOW()
 WHERE coalesce(is_active, true) = true
   AND can_view_client = false;
