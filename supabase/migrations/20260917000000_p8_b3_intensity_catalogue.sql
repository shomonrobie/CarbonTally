-- ============================================================================
-- CarbonTally Phase 8 Reporting / Disclosure — B3 (Disclosure Model
-- Integration) — migration 1 of 2 (B3-1)
-- File: 20260917000000_p8_b3_intensity_catalogue.sql
--
-- Purpose (task CT-P8-B3-IMPLEMENTATION-20260913-032; contract §6.1, §17;
--          PO direction of 2026-09-13 answering B3-D1):
--   * public.disclosure_intensity_denominator_types
--       — the GENERIC, CarbonTally-owned controlled denominator catalogue
--         ("CarbonTally denominator capability").
--   * public.disclosure_intensity_denominator_framework_links
--       — SEPARATE framework-specific treatment records
--         ("regulatory requirement" claims), each carrying its own
--         evidence/provenance, so a generic capability is never presented as
--         a statutory requirement.
--
-- RATIFIED / PO CONSTRAINTS HONOURED
--   * D11-CAT: a controlled catalogue; the customer selects/confirms from
--     supported denominator types; NO unrestricted custom denominator.
--   * B3-D1 (PO, 2026-09-13): the four candidates (net revenue/turnover,
--     floor area, FTE headcount, physical output) remain CANDIDATES; none may
--     be labelled a statutory SECR/ESRS E1 requirement merely because it is
--     plausible or commonly used; no official identifier may be invented.
--   * Structural guarantee: the framework-link CHECK constraint makes a
--     'STATUTORY_REQUIRED' treatment IMPOSSIBLE without evidence_basis,
--     source_tier and verified_at — i.e. the schema cannot record an
--     unverified statutory claim.
--
-- SCOPE DISCIPLINE (B3-1 only)
--   * ADDITIVE + IDEMPOTENT. Creates exactly TWO new reference tables.
--     MODIFIES ZERO existing tables, grants, policies or RLS flags.
--   * NO seeds in the framework-link table: with no authoritative evidence
--     supplied, the honest record is the ABSENCE of a claim.
--   * NO B3-2 (disclosure_intensity_ratios), NO projections, NO B4, NO P1/P2,
--     NO RLS remediation, NO Phase 8-X, NO extraction/calculation change.
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 0. Preconditions — fail LOUDLY when the B1 foundation is absent.
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regprocedure('public.p8_disclosure_is_org_member(uuid)') IS NULL THEN
        RAISE EXCEPTION
            'B3-1 precondition failed: B1 helper public.p8_disclosure_is_org_member(uuid) is absent. Apply 20260914000000_p8_b1_disclosure_model_foundation.sql first.';
    END IF;
    IF to_regclass('public.disclosure_framework_versions') IS NULL THEN
        RAISE EXCEPTION
            'B3-1 precondition failed: public.disclosure_framework_versions is absent. Apply the B1 foundation before B3-1.';
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 1. public.disclosure_intensity_denominator_types — GENERIC capability only.
--    A row here asserts NOTHING about any framework.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_intensity_denominator_types (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(64) NOT NULL UNIQUE,
    name varchar(200) NOT NULL,
    denominator_kind varchar(20) NOT NULL,
    unit_hint varchar(40),
    support_class varchar(40) NOT NULL DEFAULT 'CARBONTALLY_SUPPORTED',
    description text,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    CONSTRAINT disclosure_intensity_denominator_types_kind_check
        CHECK (denominator_kind IN ('FINANCIAL', 'PHYSICAL', 'HEADCOUNT', 'AREA')),
    CONSTRAINT disclosure_intensity_denominator_types_support_check
        CHECK (support_class IN ('CARBONTALLY_SUPPORTED')),
    CONSTRAINT disclosure_intensity_denominator_types_code_check
        CHECK (code = upper(code) AND code ~ '^[A-Z0-9_]+$')
);

COMMENT ON TABLE public.disclosure_intensity_denominator_types IS
  'B3: GENERIC CarbonTally-supported intensity denominator catalogue (D11-CAT). A row here is a CarbonTally capability, never a regulatory claim. Framework-specific treatment lives in disclosure_intensity_denominator_framework_links.';
COMMENT ON COLUMN public.disclosure_intensity_denominator_types.support_class IS
  'Only CARBONTALLY_SUPPORTED is permitted here. Framework/statutory classes are recorded per framework version in the framework-links table so capability and regulatory obligation are never conflated (PO direction 2026-09-13).';

-- ---------------------------------------------------------------------------
-- 2. public.disclosure_intensity_denominator_framework_links — framework
--    treatment claims, each with its own evidence/provenance.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_intensity_denominator_framework_links (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    denominator_type_id uuid NOT NULL REFERENCES public.disclosure_intensity_denominator_types(id) ON DELETE RESTRICT,
    framework_version_id uuid NOT NULL REFERENCES public.disclosure_framework_versions(id) ON DELETE RESTRICT,
    treatment varchar(30) NOT NULL,
    evidence_basis text,
    source_tier smallint,
    official_reference text,
    verified_at timestamptz,
    verified_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    CONSTRAINT disclosure_intensity_denominator_framework_links_unique
        UNIQUE (denominator_type_id, framework_version_id),
    CONSTRAINT disclosure_intensity_denominator_framework_links_treatment_check
        CHECK (treatment IN ('NOT_VERIFIED', 'SUPPORTED', 'RECOMMENDED', 'STATUTORY_REQUIRED')),
    CONSTRAINT disclosure_intensity_denominator_framework_links_source_tier_check
        CHECK (source_tier IS NULL OR source_tier BETWEEN 1 AND 3),
    -- A statutory/mandatory claim is structurally impossible without evidence.
    CONSTRAINT disclosure_intensity_denominator_framework_links_statutory_requires_evidence
        CHECK (
            treatment <> 'STATUTORY_REQUIRED'
            OR (evidence_basis IS NOT NULL AND btrim(evidence_basis) <> ''
                AND source_tier IS NOT NULL AND verified_at IS NOT NULL)
        ),
    -- An official reference may exist only on a verified row.
    CONSTRAINT disclosure_intensity_denominator_framework_links_reference_requires_verification
        CHECK (official_reference IS NULL OR verified_at IS NOT NULL)
);

COMMENT ON TABLE public.disclosure_intensity_denominator_framework_links IS
  'B3: framework-specific treatment of a generic denominator (NOT_VERIFIED / SUPPORTED / RECOMMENDED / STATUTORY_REQUIRED) with mandatory evidence for the last class. Seeded EMPTY: no authoritative SECR/E1 evidence has been supplied, so no claim is recorded (PO direction 2026-09-13; D17).';

-- ---------------------------------------------------------------------------
-- 3. Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_didt_active
    ON public.disclosure_intensity_denominator_types (is_active, code);
CREATE INDEX IF NOT EXISTS idx_didfl_denominator
    ON public.disclosure_intensity_denominator_framework_links (denominator_type_id);
CREATE INDEX IF NOT EXISTS idx_didfl_framework_version
    ON public.disclosure_intensity_denominator_framework_links (framework_version_id);

-- ---------------------------------------------------------------------------
-- 4. RLS — global reference tables: authenticated READ; NO client write; no anon
--    (mirrors the B1 global-catalogue posture exactly).
-- ---------------------------------------------------------------------------
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'disclosure_intensity_denominator_types',
        'disclosure_intensity_denominator_framework_links'
    ] LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('REVOKE ALL ON TABLE public.%I FROM anon', t);
        EXECUTE format('REVOKE INSERT, UPDATE, DELETE ON TABLE public.%I FROM authenticated', t);
        EXECUTE format('GRANT SELECT ON TABLE public.%I TO authenticated', t);
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', t || '_read', t);
        EXECUTE format(
            'CREATE POLICY %I ON public.%I FOR SELECT TO authenticated USING (true)',
            t || '_read', t
        );
    END LOOP;
END $$;

-- ---------------------------------------------------------------------------
-- 5. SEEDS — the four PO-named CANDIDATES as generic CarbonTally capabilities.
--    support_class is CARBONTALLY_SUPPORTED for every row; NO framework link
--    row is seeded (no authoritative evidence exists yet).
--    Idempotent: ON CONFLICT (code) DO NOTHING.
-- ---------------------------------------------------------------------------
INSERT INTO public.disclosure_intensity_denominator_types
    (code, name, denominator_kind, unit_hint, support_class, description)
VALUES
    ('NET_REVENUE',      'Net revenue / turnover', 'FINANCIAL', 'GBP',
     'CARBONTALLY_SUPPORTED',
     'CarbonTally-supported intensity denominator. Not asserted as a statutory requirement of any framework.'),
    ('FLOOR_AREA',       'Total floor area', 'AREA', 'm2',
     'CARBONTALLY_SUPPORTED',
     'CarbonTally-supported intensity denominator. Not asserted as a statutory requirement of any framework.'),
    ('FTE_HEADCOUNT',    'FTE headcount', 'HEADCOUNT', 'FTE',
     'CARBONTALLY_SUPPORTED',
     'CarbonTally-supported intensity denominator. Not asserted as a statutory requirement of any framework.'),
    ('PHYSICAL_OUTPUT',  'Physical output', 'PHYSICAL', NULL,
     'CARBONTALLY_SUPPORTED',
     'CarbonTally-supported intensity denominator. Not asserted as a statutory requirement of any framework.')
ON CONFLICT (code) DO NOTHING;

COMMIT;
