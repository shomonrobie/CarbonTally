-- ============================================================================
-- CarbonTally Phase 8 Reporting — B1 Disclosure Model Foundation
-- File: 20260914000000_p8_b1_disclosure_model_foundation.sql
--
-- Purpose (Phase 8 Batch B1 — PO-authorised, CT-P8-B1-IMPLEMENTATION-20260912-013):
--   Create the 11-table Disclosure Model FOUNDATION only:
--     disclosure_frameworks / _framework_versions / _requirement_versions /
--     _requirement_mappings / _report_purposes / _report_purpose_versions /
--     _purpose_requirements / _applicability_assessments /
--     _report_instance_binding / _values / _value_evidence
--
-- Governing contract: docs/architecture/CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md
-- PO decisions: docs/architecture/CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md
--
-- Scope discipline:
--   * ADDITIVE + IDEMPOTENT. Creates 11 new tables. MODIFIES ZERO existing tables.
--   * NO B2 (evidence_line_items / calculation_snapshots.source_line_item_id).
--   * NO B3 (intensity denominator catalogue / intensity ratios).
--   * NO B4 (narrative overlay / management commentary / frozen artefacts).
--   * NO RLS change to any existing table; NO change to the 34 outstanding migrations.
--   * Reference seed = framework identities (D1) + report-purpose identities (D6-R)
--     ONLY. Framework-VERSION rows are deliberately NOT seeded (PQ-6: version rows
--     require a PO-confirmed authoritative-evidence list) — see the header note at
--     the seed block.
--
-- Conventions match the existing repository exactly: UUID PKs via
-- extensions.uuid_generate_v4(), timestamptz defaults, organization_id
-- ... ON DELETE CASCADE, CHECK-enumerated vocabularies (no CREATE TYPE), and the
-- D33 SET NULL evidence pattern.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. disclosure_frameworks  (global catalogue; D1)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_frameworks (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    code varchar NOT NULL,
    name varchar NOT NULL,
    publisher varchar,
    kind varchar NOT NULL,
    is_primary_foundation boolean NOT NULL DEFAULT false,
    description text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    CONSTRAINT disclosure_frameworks_code_key UNIQUE (code),
    CONSTRAINT disclosure_frameworks_code_check
        CHECK (code IN ('GHG_PROTOCOL', 'UK_SECR', 'ESRS_E1')),
    CONSTRAINT disclosure_frameworks_kind_check
        CHECK (kind IN ('accounting_foundation', 'jurisdiction_statute', 'eu_standard'))
);

COMMENT ON TABLE public.disclosure_frameworks IS
    'Phase 8 B1 — canonical register of the frameworks CarbonTally maps to (D1). Global/platform-controlled.';

-- ---------------------------------------------------------------------------
-- 2. disclosure_framework_versions  (global catalogue; D14/D15/D17)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_framework_versions (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    framework_id uuid NOT NULL REFERENCES public.disclosure_frameworks(id) ON DELETE RESTRICT,
    version_label varchar NOT NULL,
    legal_reference text,
    source_tier smallint NOT NULL,
    source_url text,
    authoritative_source_date date,
    status varchar NOT NULL,
    applicable_from date,
    applicable_to date,
    verified_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    CONSTRAINT disclosure_framework_versions_unique UNIQUE (framework_id, version_label),
    CONSTRAINT disclosure_framework_versions_source_tier_check CHECK (source_tier BETWEEN 1 AND 3),
    CONSTRAINT disclosure_framework_versions_status_check
        CHECK (status IN ('IN_FORCE', 'ADOPTED_NOT_IN_FORCE', 'SUPERSEDED', 'WITHDRAWN')),
    CONSTRAINT disclosure_framework_versions_period_order_check
        CHECK (applicable_to IS NULL OR applicable_from IS NULL OR applicable_to >= applicable_from),
    -- A not-in-force version must carry NO applicable_from (design §6.5).
    CONSTRAINT disclosure_framework_versions_not_in_force_check
        CHECK (status <> 'ADOPTED_NOT_IN_FORCE' OR applicable_from IS NULL)
);

COMMENT ON TABLE public.disclosure_framework_versions IS
    'Phase 8 B1 — versioned framework binding unit (D14). Immutable once referenced by a finalised report.';

-- ---------------------------------------------------------------------------
-- 3. disclosure_requirement_versions  (global catalogue; D9/D12/D17)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_requirement_versions (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    framework_version_id uuid NOT NULL REFERENCES public.disclosure_framework_versions(id) ON DELETE RESTRICT,
    requirement_code varchar NOT NULL,
    official_identifier varchar,
    identifier_status varchar NOT NULL DEFAULT 'UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION',
    title varchar NOT NULL,
    description text,
    requirement_class varchar NOT NULL,
    is_quantitative boolean NOT NULL DEFAULT false,
    value_kind varchar NOT NULL,
    unit_hint varchar,
    scope_hint varchar,
    gas_hint varchar,
    scope2_method_hint varchar,
    period_semantics varchar,
    parent_requirement_id uuid REFERENCES public.disclosure_requirement_versions(id) ON DELETE SET NULL,
    display_order integer,
    purpose_hint varchar,
    carbontally_capability varchar NOT NULL,
    source_locator text,
    authoritative_text_ref text,
    source_tier smallint,
    verified_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    CONSTRAINT disclosure_requirement_versions_unique UNIQUE (framework_version_id, requirement_code),
    CONSTRAINT disclosure_requirement_versions_class_check
        CHECK (requirement_class IN ('REQUIRED', 'CONDITIONAL', 'OPTIONAL', 'NOT_APPLICABLE',
                                     'CUSTOMER_INPUT_REQUIRED', 'UNDETERMINED', 'NOT_SUPPORTED', 'FUTURE')),
    CONSTRAINT disclosure_requirement_versions_value_kind_check
        CHECK (value_kind IN ('QUANTITATIVE', 'QUALITATIVE', 'NARRATIVE_BOUND', 'SELECTION')),
    CONSTRAINT disclosure_requirement_versions_capability_check
        CHECK (carbontally_capability IN ('SUPPORTED', 'PARTIALLY_SUPPORTED', 'STRUCTURED_INPUT_REQUIRED',
                                          'EXTERNAL_INPUT_REQUIRED', 'MISSING_CAPABILITY', 'FUTURE',
                                          'NOT_APPLICABLE_TO_PRODUCT')),
    CONSTRAINT disclosure_requirement_versions_scope2_method_check
        CHECK (scope2_method_hint IS NULL OR scope2_method_hint IN ('LOCATION_BASED', 'MARKET_BASED')),
    CONSTRAINT disclosure_requirement_versions_source_tier_check
        CHECK (source_tier IS NULL OR source_tier BETWEEN 1 AND 3),
    CONSTRAINT disclosure_requirement_versions_identifier_status_check
        CHECK (identifier_status IN ('RESOLVED', 'UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION')),
    -- Identifier safety: an UNRESOLVED requirement may NEVER carry an official id (D17 / DM-1).
    CONSTRAINT disclosure_requirement_versions_identifier_safety_check
        CHECK (identifier_status = 'RESOLVED' OR official_identifier IS NULL)
);

COMMENT ON TABLE public.disclosure_requirement_versions IS
    'Phase 8 B1 — a requirement as expressed in ONE framework version (D9/D12). identifier_status gates invented identifiers.';

-- ---------------------------------------------------------------------------
-- 4. disclosure_requirement_mappings  (global catalogue; D4/D14)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_requirement_mappings (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    requirement_version_id uuid NOT NULL REFERENCES public.disclosure_requirement_versions(id) ON DELETE RESTRICT,
    mapping_version integer NOT NULL DEFAULT 1,
    source_kind varchar NOT NULL,
    source_selector jsonb,
    aggregation varchar NOT NULL,
    display_only boolean NOT NULL DEFAULT false,
    is_current boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    CONSTRAINT disclosure_requirement_mappings_unique UNIQUE (requirement_version_id, mapping_version),
    CONSTRAINT disclosure_requirement_mappings_source_kind_check
        CHECK (source_kind IN ('CALCULATION_AGGREGATE', 'EMISSIONS_LOG_AGGREGATE', 'FACTOR_PROVENANCE',
                               'EVIDENCE_COMPLETENESS', 'ENERGY_ACTIVITY', 'INTENSITY_RATIO',
                               'PRIOR_PERIOD_VALUE', 'ORG_PROFILE_FACT', 'CUSTOMER_INPUT')),
    CONSTRAINT disclosure_requirement_mappings_aggregation_check
        CHECK (aggregation IN ('SUM', 'SUM_KG_CO2E', 'DISTINCT_COUNT', 'RATIO', 'PASSTHROUGH'))
);

COMMENT ON TABLE public.disclosure_requirement_mappings IS
    'Phase 8 B1 — controlled requirement→data binding (D4). One CURRENT mapping per requirement (partial unique index).';

-- ---------------------------------------------------------------------------
-- 5. disclosure_report_purposes  (global catalogue; D6-R, DM-2)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_report_purposes (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    code varchar NOT NULL,
    name varchar NOT NULL,
    is_statutory_positioned boolean NOT NULL DEFAULT false,
    description text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    CONSTRAINT disclosure_report_purposes_code_key UNIQUE (code),
    CONSTRAINT disclosure_report_purposes_code_check
        CHECK (code IN ('ANNUAL_CARBON', 'MANAGEMENT', 'UK_SECR', 'ESRS_E1_QUANT'))
);

COMMENT ON TABLE public.disclosure_report_purposes IS
    'Phase 8 B1 — the four ratified report purposes (D6-R). purpose_code is SEPARATE from report_generation_queue.report_type (DM-2).';

-- ---------------------------------------------------------------------------
-- 6. disclosure_report_purpose_versions  (global catalogue; D14)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_report_purpose_versions (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    purpose_id uuid NOT NULL REFERENCES public.disclosure_report_purposes(id) ON DELETE RESTRICT,
    version integer NOT NULL,
    effective_from date,
    status varchar NOT NULL DEFAULT 'DRAFT',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    CONSTRAINT disclosure_report_purpose_versions_unique UNIQUE (purpose_id, version),
    CONSTRAINT disclosure_report_purpose_versions_status_check
        CHECK (status IN ('DRAFT', 'ACTIVE', 'SUPERSEDED'))
);

COMMENT ON TABLE public.disclosure_report_purpose_versions IS
    'Phase 8 B1 — versioning of a purpose''s content (D14).';

-- ---------------------------------------------------------------------------
-- 7. disclosure_purpose_requirements  (global catalogue; D6-R)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_purpose_requirements (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    purpose_version_id uuid NOT NULL REFERENCES public.disclosure_report_purpose_versions(id) ON DELETE CASCADE,
    requirement_version_id uuid NOT NULL REFERENCES public.disclosure_requirement_versions(id) ON DELETE RESTRICT,
    display_order integer NOT NULL,
    required_for_finalisation boolean NOT NULL DEFAULT true,
    purpose_specific_class varchar,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    CONSTRAINT disclosure_purpose_requirements_unique UNIQUE (purpose_version_id, requirement_version_id),
    CONSTRAINT disclosure_purpose_requirements_class_check
        CHECK (purpose_specific_class IS NULL OR purpose_specific_class IN
               ('REQUIRED', 'CONDITIONAL', 'OPTIONAL', 'NOT_APPLICABLE',
                'CUSTOMER_INPUT_REQUIRED', 'UNDETERMINED', 'NOT_SUPPORTED', 'FUTURE'))
);

COMMENT ON TABLE public.disclosure_purpose_requirements IS
    'Phase 8 B1 — which requirement versions a purpose presents, and how (D6-R). purpose_specific_class overrides the requirement''s own class where set.';

-- ---------------------------------------------------------------------------
-- 8. disclosure_applicability_assessments  (organisation-scoped; D13/APPL/DM-3)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_applicability_assessments (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    framework_version_id uuid NOT NULL REFERENCES public.disclosure_framework_versions(id) ON DELETE RESTRICT,
    reporting_year integer NOT NULL,
    reporting_period_start date NOT NULL,
    reporting_period_end date NOT NULL,
    characteristic_snapshot jsonb NOT NULL,
    assessed_status varchar NOT NULL,
    basis text NOT NULL,
    determined_by uuid,
    determined_at timestamptz,
    version integer NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    CONSTRAINT disclosure_applicability_assessments_unique
        UNIQUE (organization_id, framework_version_id, reporting_period_start, reporting_period_end, version),
    CONSTRAINT disclosure_applicability_assessments_period_order_check
        CHECK (reporting_period_end >= reporting_period_start),
    CONSTRAINT disclosure_applicability_assessments_status_check
        CHECK (assessed_status IN ('APPLIES', 'DOES_NOT_APPLY', 'UNDETERMINED', 'CUSTOMER_INPUT_REQUIRED')),
    -- A cited basis is mandatory (auditable; never a bare boolean).
    CONSTRAINT disclosure_applicability_assessments_basis_check
        CHECK (length(btrim(basis)) > 0)
);

COMMENT ON TABLE public.disclosure_applicability_assessments IS
    'Phase 8 B1 — period-dated, version-bound applicability assessment (D13/APPL). Append-only (version); UNDETERMINED is first-class; facts + basis only (no legal determination).';

-- ---------------------------------------------------------------------------
-- 9. disclosure_report_instance_binding  (organisation-scoped; D15/DM-2/DM-3/GP-CONS)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_report_instance_binding (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    report_id uuid NOT NULL REFERENCES public.report_generation_queue(id) ON DELETE CASCADE,
    purpose_version_id uuid NOT NULL REFERENCES public.disclosure_report_purpose_versions(id) ON DELETE RESTRICT,
    applicability_assessment_id uuid REFERENCES public.disclosure_applicability_assessments(id) ON DELETE SET NULL,
    reporting_period_start date NOT NULL,
    reporting_period_end date NOT NULL,
    consolidation_approach varchar NOT NULL DEFAULT 'OPERATIONAL_CONTROL',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    CONSTRAINT disclosure_report_instance_binding_report_key UNIQUE (report_id),
    CONSTRAINT disclosure_report_instance_binding_period_order_check
        CHECK (reporting_period_end >= reporting_period_start),
    CONSTRAINT disclosure_report_instance_binding_consolidation_check
        CHECK (consolidation_approach IN ('OPERATIONAL_CONTROL', 'FINANCIAL_CONTROL', 'EQUITY_SHARE'))
);

COMMENT ON TABLE public.disclosure_report_instance_binding IS
    'Phase 8 B1 — binds an existing report instance (report_generation_queue.id) to its purpose/applicability/period/consolidation. The binding is AUTHORITATIVE for the report instance period (PQ-2); its period MUST equal a referenced assessment''s period (app-layer invariant).';

-- ---------------------------------------------------------------------------
-- 10. disclosure_values  (organisation-scoped; D2/D9/D12/D15; PQ-3)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_values (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    report_version_id uuid NOT NULL REFERENCES public.report_versions(id) ON DELETE CASCADE,
    requirement_version_id uuid NOT NULL REFERENCES public.disclosure_requirement_versions(id) ON DELETE RESTRICT,
    requirement_mapping_id uuid REFERENCES public.disclosure_requirement_mappings(id) ON DELETE RESTRICT,
    -- AUTHORITATIVE home for the derived requirement/applicability/capability outcome (PQ-3).
    effective_class varchar NOT NULL,
    -- Narrow MATERIALISATION lifecycle ONLY (PQ-3): PENDING | RESOLVED | UNRESOLVED.
    -- MUST NOT carry requirement/applicability/capability semantics — those live in effective_class.
    value_status varchar NOT NULL DEFAULT 'PENDING',
    value_kind varchar NOT NULL,
    numeric_value numeric,
    value_unit varchar,
    text_value text,
    reporting_year integer NOT NULL,
    source_kind varchar,
    reason text,
    computed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    CONSTRAINT disclosure_values_unique UNIQUE (report_version_id, requirement_version_id),
    CONSTRAINT disclosure_values_effective_class_check
        CHECK (effective_class IN ('REQUIRED', 'CONDITIONAL', 'OPTIONAL', 'NOT_APPLICABLE',
                                   'CUSTOMER_INPUT_REQUIRED', 'UNDETERMINED', 'NOT_SUPPORTED', 'FUTURE')),
    CONSTRAINT disclosure_values_value_status_check
        CHECK (value_status IN ('PENDING', 'RESOLVED', 'UNRESOLVED')),
    CONSTRAINT disclosure_values_value_kind_check
        CHECK (value_kind IN ('QUANTITATIVE', 'QUALITATIVE', 'NARRATIVE_BOUND', 'SELECTION')),
    CONSTRAINT disclosure_values_source_kind_check
        CHECK (source_kind IS NULL OR source_kind IN ('CALCULATION_AGGREGATE', 'EMISSIONS_LOG_AGGREGATE',
               'FACTOR_PROVENANCE', 'EVIDENCE_COMPLETENESS', 'ENERGY_ACTIVITY', 'INTENSITY_RATIO',
               'PRIOR_PERIOD_VALUE', 'ORG_PROFILE_FACT', 'CUSTOMER_INPUT'))
);

COMMENT ON TABLE public.disclosure_values IS
    'Phase 8 B1 — one resolved value per requirement version per report version (D2/D15). effective_class = derived outcome (authoritative); value_status = PENDING/RESOLVED/UNRESOLVED materialisation only (PQ-3). Projection of persisted calculations; never recomputed.';

-- ---------------------------------------------------------------------------
-- 11. disclosure_value_evidence  (organisation-scoped; D33/DM-7)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.disclosure_value_evidence (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    disclosure_value_id uuid NOT NULL REFERENCES public.disclosure_values(id) ON DELETE CASCADE,
    calculation_snapshot_id uuid REFERENCES public.calculation_snapshots(id) ON DELETE SET NULL,
    emissions_log_id uuid REFERENCES public.emissions_logs(id) ON DELETE SET NULL,
    source_item_id uuid REFERENCES public.manual_extraction_items(id) ON DELETE SET NULL,
    source_file_id uuid REFERENCES public.organization_files(id) ON DELETE SET NULL,
    source_page integer,
    evidence_completeness varchar,
    contribution_share numeric,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid,
    CONSTRAINT disclosure_value_evidence_unique UNIQUE (disclosure_value_id, calculation_snapshot_id),
    CONSTRAINT disclosure_value_evidence_completeness_check
        CHECK (evidence_completeness IS NULL OR evidence_completeness IN ('COMPLETE', 'PARTIAL', 'UNAVAILABLE')),
    CONSTRAINT disclosure_value_evidence_contribution_check
        CHECK (contribution_share IS NULL OR contribution_share >= 0)
);

COMMENT ON TABLE public.disclosure_value_evidence IS
    'Phase 8 B1 — deterministic value→evidence link (D33/DM-7). References existing evidence rows (SET NULL); NEVER copies documents, storage objects or signed URLs. No evidence_line_items (B2).';

-- ============================================================================
-- INDEXES  (contract §11)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_dfv_framework_status
    ON public.disclosure_framework_versions (framework_id, status);
CREATE INDEX IF NOT EXISTS idx_drv_framework_version
    ON public.disclosure_requirement_versions (framework_version_id);
CREATE INDEX IF NOT EXISTS idx_drv_framework_class
    ON public.disclosure_requirement_versions (framework_version_id, requirement_class);
CREATE INDEX IF NOT EXISTS idx_drv_parent
    ON public.disclosure_requirement_versions (parent_requirement_id);
CREATE INDEX IF NOT EXISTS idx_drm_requirement
    ON public.disclosure_requirement_mappings (requirement_version_id);
-- Exactly one CURRENT mapping per requirement.
CREATE UNIQUE INDEX IF NOT EXISTS uq_drm_current
    ON public.disclosure_requirement_mappings (requirement_version_id)
    WHERE is_current;
CREATE INDEX IF NOT EXISTS idx_dpv_purpose
    ON public.disclosure_report_purpose_versions (purpose_id);
CREATE INDEX IF NOT EXISTS idx_dpr_purpose_version
    ON public.disclosure_purpose_requirements (purpose_version_id, display_order);
CREATE INDEX IF NOT EXISTS idx_dpr_requirement
    ON public.disclosure_purpose_requirements (requirement_version_id);
CREATE INDEX IF NOT EXISTS idx_daa_org_fw_period
    ON public.disclosure_applicability_assessments (organization_id, framework_version_id, reporting_period_start);
CREATE INDEX IF NOT EXISTS idx_daa_framework_version
    ON public.disclosure_applicability_assessments (framework_version_id);
CREATE INDEX IF NOT EXISTS idx_drib_org
    ON public.disclosure_report_instance_binding (organization_id);
CREATE INDEX IF NOT EXISTS idx_drib_purpose_version
    ON public.disclosure_report_instance_binding (purpose_version_id);
CREATE INDEX IF NOT EXISTS idx_drib_applicability
    ON public.disclosure_report_instance_binding (applicability_assessment_id);
CREATE INDEX IF NOT EXISTS idx_dv_report_version
    ON public.disclosure_values (report_version_id);
CREATE INDEX IF NOT EXISTS idx_dv_org
    ON public.disclosure_values (organization_id);
CREATE INDEX IF NOT EXISTS idx_dv_requirement
    ON public.disclosure_values (requirement_version_id);
CREATE INDEX IF NOT EXISTS idx_dv_mapping
    ON public.disclosure_values (requirement_mapping_id);
CREATE INDEX IF NOT EXISTS idx_dve_value
    ON public.disclosure_value_evidence (disclosure_value_id);
CREATE INDEX IF NOT EXISTS idx_dve_calc
    ON public.disclosure_value_evidence (calculation_snapshot_id);
CREATE INDEX IF NOT EXISTS idx_dve_source_item
    ON public.disclosure_value_evidence (source_item_id);
CREATE INDEX IF NOT EXISTS idx_dve_source_file
    ON public.disclosure_value_evidence (source_file_id);
-- (idx_drib_report is provided by the UNIQUE(report_id) constraint.)

-- ============================================================================
-- RLS POLICY INTENT  (contract §23) — NEW tables only; nothing existing touched.
--
-- B1 does NOT remediate the wider RLS baseline and does NOT rely on RLS as the
-- security boundary: application-layer authorization is the enforced boundary
-- (see backend/domain/disclosure.py + backend/data/disclosure.py). These policies
-- are defence-in-depth for the eventual remediation.
-- ============================================================================

-- Membership helper (SECURITY DEFINER → bypasses RLS on organization_members, so
-- it cannot reintroduce the known recursive-policy defect on that table).
CREATE OR REPLACE FUNCTION public.p8_disclosure_is_org_member(p_org uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.organization_members m
        WHERE m.organization_id = p_org
          AND m.user_id = auth.uid()
          AND m.is_active
    );
$$;

CREATE OR REPLACE FUNCTION public.p8_disclosure_is_org_admin(p_org uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.organization_members m
        WHERE m.organization_id = p_org
          AND m.user_id = auth.uid()
          AND m.is_active
          AND lower(m.role::text) IN ('owner', 'admin')
    );
$$;

-- ---- Global catalogue tables: authenticated READ; NO client write; no anon ----
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'disclosure_frameworks', 'disclosure_framework_versions',
        'disclosure_requirement_versions', 'disclosure_requirement_mappings',
        'disclosure_report_purposes', 'disclosure_report_purpose_versions',
        'disclosure_purpose_requirements'
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

-- ---- Organisation-scoped tables ----
-- applicability_assessments: member read; admin write.
ALTER TABLE public.disclosure_applicability_assessments ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.disclosure_applicability_assessments FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.disclosure_applicability_assessments TO authenticated;
DROP POLICY IF EXISTS disclosure_applicability_assessments_read ON public.disclosure_applicability_assessments;
CREATE POLICY disclosure_applicability_assessments_read
    ON public.disclosure_applicability_assessments FOR SELECT TO authenticated
    USING (public.p8_disclosure_is_org_member(organization_id));
DROP POLICY IF EXISTS disclosure_applicability_assessments_write ON public.disclosure_applicability_assessments;
CREATE POLICY disclosure_applicability_assessments_write
    ON public.disclosure_applicability_assessments FOR ALL TO authenticated
    USING (public.p8_disclosure_is_org_admin(organization_id))
    WITH CHECK (public.p8_disclosure_is_org_admin(organization_id));

-- report_instance_binding: member read/write (follows report_generation_queue authz).
ALTER TABLE public.disclosure_report_instance_binding ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.disclosure_report_instance_binding FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.disclosure_report_instance_binding TO authenticated;
DROP POLICY IF EXISTS disclosure_report_instance_binding_read ON public.disclosure_report_instance_binding;
CREATE POLICY disclosure_report_instance_binding_read
    ON public.disclosure_report_instance_binding FOR SELECT TO authenticated
    USING (public.p8_disclosure_is_org_member(organization_id));
DROP POLICY IF EXISTS disclosure_report_instance_binding_write ON public.disclosure_report_instance_binding;
CREATE POLICY disclosure_report_instance_binding_write
    ON public.disclosure_report_instance_binding FOR ALL TO authenticated
    USING (public.p8_disclosure_is_org_member(organization_id))
    WITH CHECK (public.p8_disclosure_is_org_member(organization_id));

-- disclosure_values / disclosure_value_evidence: member READ only; writes are
-- system-derived (service role). No authenticated write policy is granted.
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['disclosure_values', 'disclosure_value_evidence'] LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('REVOKE ALL ON TABLE public.%I FROM anon', t);
        EXECUTE format('REVOKE INSERT, UPDATE, DELETE ON TABLE public.%I FROM authenticated', t);
        EXECUTE format('GRANT SELECT ON TABLE public.%I TO authenticated', t);
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', t || '_read', t);
        EXECUTE format(
            'CREATE POLICY %I ON public.%I FOR SELECT TO authenticated USING (public.p8_disclosure_is_org_member(organization_id))',
            t || '_read', t
        );
    END LOOP;
END $$;

-- ============================================================================
-- REFERENCE SEEDS  (PQ-6 — identities ONLY; idempotent)
--
-- Seeded: the 3 framework identities (D1) and the 4 report-purpose identities
-- (D6-R). These are ratified identity facts, not regulatory content.
--
-- DELIBERATELY NOT SEEDED (PQ-6 / contract §4): disclosure_framework_versions.
-- Framework version rows assert a legal in-force fact and require a PO-confirmed,
-- authoritative-evidence list; that list was not supplied with this authorisation
-- task. Requirement / requirement-mapping / purpose-requirement content is B3.
-- The tables exist and are empty; a later authorised task seeds them.
-- ============================================================================
INSERT INTO public.disclosure_frameworks (code, name, publisher, kind, is_primary_foundation, description)
VALUES
    ('GHG_PROTOCOL', 'GHG Protocol Corporate Standard', 'GHG Protocol / WRI & WBCSD',
     'accounting_foundation', true,
     'Primary corporate GHG accounting foundation (D8).'),
    ('UK_SECR', 'UK Streamlined Energy and Carbon Reporting', 'UK Government (DESNZ)',
     'jurisdiction_statute', false,
     'Initial jurisdiction-specific statutory reporting use case (D1/D10).'),
    ('ESRS_E1', 'ESRS E1 Climate Change', 'European Commission (EFRAG)',
     'eu_standard', false,
     'Bounded EU/Ireland quantitative expansion (D1/D7-R).')
ON CONFLICT (code) DO NOTHING;

INSERT INTO public.disclosure_report_purposes (code, name, is_statutory_positioned, description)
VALUES
    ('ANNUAL_CARBON', 'Annual Carbon Report', false, 'Annual carbon report purpose (D6-R).'),
    ('MANAGEMENT', 'Management Report', false, 'Management report purpose (D6-R).'),
    ('UK_SECR', 'UK SECR Report', true, 'UK SECR report purpose (D6-R).'),
    ('ESRS_E1_QUANT', 'ESRS E1 Quantitative Report', true, 'ESRS E1 quantitative report purpose (D6-R).')
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- VERIFICATION CHECKLIST
--   [ ] exactly 11 public.disclosure_* tables exist (no 12th)
--   [ ] ZERO existing tables were modified (no ALTER outside public.disclosure_*)
--   [ ] disclosure_values.value_status CHECK = (PENDING, RESOLVED, UNRESOLVED)
--   [ ] disclosure_values.effective_class present + CHECK in requirement classes
--   [ ] both period-carrying tables have reporting_period_start/end NOT NULL
--     and CHECK (reporting_period_end >= reporting_period_start)
--   [ ] identifier safety CHECK present
--   [ ] ADOPTED_NOT_IN_FORCE ⇒ applicable_from IS NULL CHECK present
--   [ ] uq_drm_current partial unique index present
--   [ ] UNIQUE (report_version_id, requirement_version_id) on disclosure_values
--   [ ] one binding per report: UNIQUE (report_id)
--   [ ] NO evidence_line_items / NO source_line_item_id column created
--   [ ] all new tables ENABLE ROW LEVEL SECURITY; anon revoked
--   [ ] reference seed idempotent (ON CONFLICT DO NOTHING)
--   [ ] re-running this file is a no-op
-- ============================================================================







