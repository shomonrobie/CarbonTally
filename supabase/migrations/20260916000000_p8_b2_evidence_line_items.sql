-- ============================================================================
-- CarbonTally Phase 8 Reporting / Disclosure — B2 (Evidence / Line-Item
-- Addressability) — migration 1 of 2 (B2-1)
-- File: 20260916000000_p8_b2_evidence_line_items.sql
--
-- Purpose (task CT-P8-B2-IMPLEMENTATION-20260913-024; contract §7, §16, §18.1):
--   Create the durable, addressable evidence-line model:
--     * public.evidence_line_items — the FK target of B2's two provenance links
--     * the four constraints, the two explicit indexes and the constraint-backed
--       unique identity index evidence_line_items_identity_unique
--     * RLS enabled + two SELECT-only policies (org member; PE mirror)
--     * privilege posture mirroring the B1 correction migration
--       (anon: none; authenticated: SELECT only; service_role: ALL)
--     * table/column comments recording the B2 boundary
--
-- Governing contract:
--   docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md
-- PO decisions (CLOSED; that document §23): this file materialises
--   B2-D1  (source_item_id ON DELETE RESTRICT — preservation-first) and
--   B2-D3  (PE read access mirrors the existing item boundary) and
--   B2-D11 (no retention/deletion mechanism: no trigger, no soft-delete
--           column, no purge path).
--
-- Scope discipline (B2-1 only):
--   * ADDITIVE + IDEMPOTENT. Creates exactly ONE new table.
--     MODIFIES ZERO existing tables, grants, policies or RLS flags.
--   * Reuses — never recreates — the B1 helper
--     public.p8_disclosure_is_org_member(uuid) and the PE helpers
--     public.work_item_effective_entity / public.is_entity_member.
--   * NO B2-2 (calculation_snapshots / disclosure_value_evidence columns).
--   * NO B3 (intensity/projections), NO B4 (narrative/frozen artefacts).
--   * NO extraction/pipeline change; NO calculation-engine change.
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 0. Preconditions — fail LOUDLY when the B1 foundation (or the PE boundary
--    helpers) is absent. Contract §16.1: B2-1 must never silently create a
--    duplicate helper definition that could drift from B1's.
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regprocedure('public.p8_disclosure_is_org_member(uuid)') IS NULL THEN
        RAISE EXCEPTION
            'B2-1 precondition failed: B1 helper public.p8_disclosure_is_org_member(uuid) is absent. Apply supabase/migrations/20260914000000_p8_b1_disclosure_model_foundation.sql (and its correction 20260915000000_…) before this migration.';
    END IF;
    IF to_regprocedure('public.work_item_effective_entity(uuid)') IS NULL
       OR to_regprocedure('public.is_entity_member(uuid)') IS NULL THEN
        RAISE EXCEPTION
            'B2-1 precondition failed: Processing-Entity helpers public.work_item_effective_entity(uuid) / public.is_entity_member(uuid) are absent. B2-D3 mirrors the existing item boundary and must not invent a new one.';
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 1. public.evidence_line_items  (contract §7.1 — normative DDL)
--    line_number = the 1-based position of the element in the persisted
--    extracted_data.line_items[] at materialisation time; ordinals are never
--    renumbered and gaps are preserved for ineligible elements (contract §11.1).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.evidence_line_items (
    id                   uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id      uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    source_item_id       uuid NOT NULL
                             REFERENCES public.manual_extraction_items(id) ON DELETE RESTRICT,  -- B2-D1
    source_file_id       uuid          REFERENCES public.organization_files(id) ON DELETE SET NULL,
    line_number          integer NOT NULL,                     -- 1-based ordinal in the persisted array
    source_page          integer,                              -- ONLY a genuine per-line page; else NULL
    row_reference        text,                                 -- ONLY a genuine printed reference; else NULL
    raw_description      text,                                 -- source activity/description, as extracted
    raw_quantity         numeric,                              -- source quantity, as extracted
    raw_unit             text,                                 -- source unit, as extracted (pre-normalisation)
    payload_hash         text NOT NULL,                        -- sha256 of the canonical line payload
    extraction_method    varchar NOT NULL DEFAULT 'unknown',   -- producing path where provable; else 'unknown'
    materialisation_kind varchar NOT NULL,                     -- 'FORWARD' | 'BACKFILL'
    created_at           timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT evidence_line_items_line_number_check CHECK (line_number >= 1),
    CONSTRAINT evidence_line_items_source_page_check
        CHECK (source_page IS NULL OR source_page >= 1),
    CONSTRAINT evidence_line_items_kind_check
        CHECK (materialisation_kind IN ('FORWARD', 'BACKFILL')),
    CONSTRAINT evidence_line_items_identity_unique UNIQUE (source_item_id, line_number)
);

CREATE INDEX IF NOT EXISTS idx_eli_org ON public.evidence_line_items (organization_id);
CREATE INDEX IF NOT EXISTS idx_eli_source_file ON public.evidence_line_items (source_file_id);
-- (the (source_item_id, line_number) index is provided by evidence_line_items_identity_unique)


-- ---------------------------------------------------------------------------
-- 2. Comments — the B2 boundary is recorded in the schema itself (contract
--    §7.5 hybrid model; §11.4 backfill boundary; §9 provenance).
-- ---------------------------------------------------------------------------
COMMENT ON TABLE public.evidence_line_items IS
    'Phase 8 B2 — durable, addressable source line identity (contract §7). Hybrid model: extracted_data.line_items[] remains the sole ELIGIBILITY source and is mutable; these rows are the immutable PROVENANCE authority that a calculation snapshot / disclosure evidence row points at. Append-only in B2 (B2-D11: no retention, no soft-delete, no purge, no trigger). Lines are DERIVED, never authored, and never fabricated for a flat document (P1 owns extraction fidelity).';

COMMENT ON COLUMN public.evidence_line_items.line_number IS
    'B2 §7.1 — 1-based ordinal of the element in extracted_data.line_items[] as persisted at materialisation time. Never renumbered; a skipped element leaves a permanent gap.';
COMMENT ON COLUMN public.evidence_line_items.payload_hash IS
    'B2 §11.2 — sha256 of the canonical recognised-key payload; the divergence detector on rerun (§11.3: detect + report + never rewrite, B2-D2).';
COMMENT ON COLUMN public.evidence_line_items.source_page IS
    'B2 §7.1/§11.7 — a genuine per-line page only. Never page_count (F-B2-7 is a separate workstream; B2-D4).';
COMMENT ON COLUMN public.evidence_line_items.row_reference IS
    'B2 §11.7/B2-D8 — a genuine printed source reference only; NULL for Class-1 materialisation (not recoverable from the persisted representation).';
COMMENT ON COLUMN public.evidence_line_items.extraction_method IS
    'B2 §11.2/B2-D7 — observational, OPEN vocabulary (no CHECK); the producing path where provable, otherwise the honest default unknown.';
COMMENT ON COLUMN public.evidence_line_items.materialisation_kind IS
    'B2 §11.2/B2-D10 — FORWARD (extraction-write hook) or BACKFILL (idempotent offline operation).';

-- ---------------------------------------------------------------------------
-- 3. RLS + privilege posture (contract §7.6, §16.1)
--    anon          : REVOKE ALL
--    authenticated : SELECT only (+ revoked TRUNCATE/TRIGGER/REFERENCES/
--                    MAINTAIN, which the local Supabase default ACL grants and
--                    which the B1 correction pattern removes — TRUNCATE is not
--                    RLS-gated)
--    service_role  : ALL (the backend is the writer; bypasses RLS)
-- ---------------------------------------------------------------------------
ALTER TABLE public.evidence_line_items ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.evidence_line_items FROM anon;
GRANT SELECT ON TABLE public.evidence_line_items TO authenticated;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, MAINTAIN
    ON TABLE public.evidence_line_items FROM authenticated;
GRANT ALL ON TABLE public.evidence_line_items TO service_role;

-- ---------------------------------------------------------------------------
-- 4. Policies — exactly two, both FOR SELECT TO authenticated (contract §16.1)
--    (1) org-member read, reusing the B1 helper
--    (2) PE read, mirroring manual_extraction_items_entity_select (B2-D3)
--    No INSERT/UPDATE/DELETE policy exists anywhere: B2 has no write path
--    other than the service-role backend (§12.3).
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'evidence_line_items'
          AND policyname = 'evidence_line_items_org_select'
    ) THEN
        CREATE POLICY evidence_line_items_org_select
            ON public.evidence_line_items
            FOR SELECT TO authenticated
            USING (public.p8_disclosure_is_org_member(organization_id));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'evidence_line_items'
          AND policyname = 'evidence_line_items_entity_select'
    ) THEN
        CREATE POLICY evidence_line_items_entity_select
            ON public.evidence_line_items
            FOR SELECT TO authenticated
            USING (
                public.work_item_effective_entity(source_item_id) IS NOT NULL
                AND public.is_entity_member(
                    public.work_item_effective_entity(source_item_id)
                )
            );
    END IF;
END $$;

-- ============================================================================
-- VERIFICATION CHECKLIST (B2-1)
--   [ ] exactly one new table exists: public.evidence_line_items
--   [ ] evidence_line_items_identity_unique exists (UNIQUE (source_item_id,
--       line_number)) and is counted SEPARATELY from the two explicit indexes
--   [ ] source_item_id FK is ON DELETE RESTRICT (never CASCADE) — B2-D1
--   [ ] no trigger of any kind was created (B2-D11)
--   [ ] relrowsecurity = TRUE; exactly two SELECT-only policies exist
--   [ ] anon: no privilege; authenticated: SELECT only; service_role: ALL
--   [ ] re-running this file is a no-op (IF NOT EXISTS / guarded DO blocks)
--   [ ] no existing table's grant, policy, RLS flag or column was modified
-- ============================================================================

COMMIT;
