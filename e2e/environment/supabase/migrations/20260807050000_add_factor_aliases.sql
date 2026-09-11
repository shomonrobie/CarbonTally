-- ============================================================================
-- CarbonTally Backend v2.1 — Phase 0, Migration M6 of 8
-- File: 20260807050000_add_factor_aliases.sql
--
-- Organisation-specific and global activity aliases for the matching pipeline
-- (Backend v2.1 §11.3 Alias Match stage; Admin Platform §20.2).
--
-- Design:
--   * organization_id NULL ⇒ global alias (applies to every organisation);
--     non-NULL ⇒ organisation-scoped alias (only that org's requests).
--   * Uniqueness: at most one alias_text per (organisation or global). The
--     COALESCE with the all-zero UUID is the standard SQL idiom for a UNIQUE
--     index over a nullable column, matching the frozen prep-pack definition.
--   * The AliasMatchStage resolves alias_text → target_activity_type scoped
--     to the request's organisation, then falls back to the global alias.
--
-- Idempotent: CREATE TABLE IF NOT EXISTS + CREATE UNIQUE INDEX IF NOT EXISTS.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.factor_aliases (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
    alias_text VARCHAR NOT NULL,
    target_activity_type VARCHAR NOT NULL,
    target_provider_key VARCHAR NOT NULL,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_factor_aliases_unique
    ON public.factor_aliases (
        COALESCE(organization_id, '00000000-0000-0000-0000-000000000000'::uuid),
        alias_text
    );

COMMENT ON TABLE public.factor_aliases IS
    'Organisation-specific and global activity aliases for factor matching (Backend v2.1 §11.3).';
COMMENT ON COLUMN public.factor_aliases.organization_id IS
    'NULL = global alias; otherwise organisation-scoped.';
COMMENT ON COLUMN public.factor_aliases.target_activity_type IS
    'RC2 activity_type the alias resolves to (e.g. Fuels > Liquid fuels > Diesel ...).';
COMMENT ON COLUMN public.factor_aliases.target_provider_key IS
    'Provider the target factor belongs to (defra, seai, ...).';

-- ============================================================================
-- VERIFICATION CHECKLIST (M6)
--   [ ] Table exists in public schema
--   [ ] Unique index idx_factor_aliases_unique on
--       (COALESCE(organization_id, all-zero UUID), alias_text)
--   [ ] organization_id FK → organizations(id) ON DELETE CASCADE
--   [ ] Re-running this file is a no-op
-- ============================================================================
