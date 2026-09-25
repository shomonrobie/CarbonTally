-- ============================================================================
-- P17-A — Accounting dimensions, factor governance and actor/acting-for context
-- File: 20261010000000_p17a_accounting_dimensions_and_factor_governance.sql
--
-- Authority: docs/architecture/artifacts/p17_schema_delta_20250925.md §2.1, §2.2,
--            §2.3, §2.4, §2.5, §10.1, §10.3 (P17-ARCH-01/02/04/06 reconciled).
--
-- Why: the P17 unified Carbon Accounting Management System (CAMS) cannot carry a
-- Scope 2 accounting method, a Scope 3 category, an energy type, a data-quality
-- classification, a boundary/origin property or an acting-for organization. This
-- migration adds exactly those dimensions as ADDITIVE, nullable columns so that
-- every historical P16 row keeps its exact value and meaning.
--
-- Discipline (P16-preserving):
--   * ADDITIVE ONLY. No column, row, value, index or policy is dropped, renamed
--     or rewritten. No historical migration is modified.
--   * Every new column is NULLABLE with no DEFAULT, so the 34 existing
--     calculation_snapshots and 34 existing emissions_logs rows are untouched and
--     receive NULL — explicitly meaning "no category / no method recorded", never
--     a fabricated one. NO BACKFILL IS PERFORMED.
--   * Scope rules that new writes must satisfy are added NOT VALID, so existing
--     rows are exempt from validation while every subsequent INSERT/UPDATE is
--     enforced. This is how a mandatory-for-new-writes dimension is introduced
--     without rewriting history.
--   * Idempotent: every statement is IF NOT EXISTS / DROP CONSTRAINT IF EXISTS.
--
-- RLS: this migration adds no table and therefore changes no policy. It only adds
-- columns to tables that already have their RLS posture; the new columns inherit
-- it. No RLS is weakened.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. calculation_snapshots — the authoritative calculation record (§2.1)
-- ---------------------------------------------------------------------------
ALTER TABLE public.calculation_snapshots
    ADD COLUMN IF NOT EXISTS scope2_method      text,
    ADD COLUMN IF NOT EXISTS scope3_category    smallint,
    ADD COLUMN IF NOT EXISTS energy_type        text,
    ADD COLUMN IF NOT EXISTS data_quality       text,
    ADD COLUMN IF NOT EXISTS facility_id        uuid,
    ADD COLUMN IF NOT EXISTS transport_boundary text,
    ADD COLUMN IF NOT EXISTS waste_origin       text,
    ADD COLUMN IF NOT EXISTS source_snapshot_id uuid,
    ADD COLUMN IF NOT EXISTS performed_by_organization_id uuid,
    ADD COLUMN IF NOT EXISTS acting_for_organization_id   uuid;

COMMENT ON COLUMN public.calculation_snapshots.scope2_method IS
    'P17-A: Scope 2 accounting method identity. LOCATION_BASED | MARKET_BASED (frozen B1 disclosure vocabulary). NULL for Scope 1/3 rows and for historical rows.';
COMMENT ON COLUMN public.calculation_snapshots.scope3_category IS
    'P17-A: GHG Protocol Scope 3 category 1-15. NULL for Scope 1/2 rows and for historical rows.';
COMMENT ON COLUMN public.calculation_snapshots.energy_type IS
    'P17-A: authoritative Scope 2 energy type: electricity | heat | steam | cooling. fuel is NOT a Scope 2 energy type (ARCH-04 LOW-02); fuel-borne energy is Scope 1/3 and carries NULL here.';
COMMENT ON COLUMN public.calculation_snapshots.data_quality IS
    'P17-A: data-quality dimension. No numeric uncertainty is implied (deferred).';
COMMENT ON COLUMN public.calculation_snapshots.transport_boundary IS
    'P17-A: DC-04 boundary discriminator (category 4 upstream vs category 9 downstream).';
COMMENT ON COLUMN public.calculation_snapshots.waste_origin IS
    'P17-A: DC-05 boundary discriminator (category 5 operations vs category 12 sold_product_eol).';
COMMENT ON COLUMN public.calculation_snapshots.source_snapshot_id IS
    'P17-A: derivation lineage. Category 3 (FERA) derives from a Scope 1/2 snapshot (DC-02).';
COMMENT ON COLUMN public.calculation_snapshots.acting_for_organization_id IS
    'P17-A/ARCH-04: the organization the actor was operating for. CONTEXT ONLY - ownership remains organization_id. Never an authorization boundary.';

-- Dimension vocabulary. NULL always permitted (historical rows and inapplicable rows).
ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_scope2_method_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_scope2_method_check
    CHECK (scope2_method IS NULL OR scope2_method IN ('LOCATION_BASED', 'MARKET_BASED'));

ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_scope3_category_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_scope3_category_check
    CHECK (scope3_category IS NULL OR scope3_category BETWEEN 1 AND 15);

ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_energy_type_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_energy_type_check
    CHECK (energy_type IS NULL OR energy_type IN ('electricity', 'heat', 'steam', 'cooling'));

ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_data_quality_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_data_quality_check
    CHECK (data_quality IS NULL OR data_quality IN
        ('primary_measured', 'primary_supplier', 'secondary_estimated', 'spend_based_estimated', 'modelled'));

ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_transport_boundary_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_transport_boundary_check
    CHECK (transport_boundary IS NULL OR transport_boundary IN ('upstream', 'downstream'));

ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_waste_origin_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_waste_origin_check
    CHECK (waste_origin IS NULL OR waste_origin IN ('operations', 'sold_product_eol'));

-- Cross-column coherence (new writes only: NOT VALID exempts historical rows).
ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_transport_boundary_scope_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_transport_boundary_scope_check
    CHECK (transport_boundary IS NULL OR scope3_category IN (4, 9)) NOT VALID;

ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_waste_origin_scope_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_waste_origin_scope_check
    CHECK (waste_origin IS NULL OR scope3_category IN (5, 12)) NOT VALID;

ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_energy_type_scope_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_energy_type_scope_check
    CHECK (energy_type IS NULL OR scope = 'Scope 2') NOT VALID;

ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_method_scope_consistency;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_method_scope_consistency
    CHECK (scope2_method IS NULL OR scope = 'Scope 2') NOT VALID;

ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_category_scope_consistency;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_category_scope_consistency
    CHECK (scope3_category IS NULL OR scope = 'Scope 3') NOT VALID;

-- Mandatory-for-new-writes scope rules. Historical rows keep NULL and are exempt.
ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_scope2_method_required;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_scope2_method_required
    CHECK (scope <> 'Scope 2' OR scope2_method IS NOT NULL) NOT VALID;

ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_scope3_category_required;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_scope3_category_required
    CHECK (scope <> 'Scope 3' OR scope3_category IS NOT NULL) NOT VALID;

-- DC-02: one FERA (category 3) derivation per source Scope 1/2 snapshot.
CREATE UNIQUE INDEX IF NOT EXISTS uq_calc_snapshots_cat3_source
    ON public.calculation_snapshots (source_snapshot_id)
    WHERE scope3_category = 3 AND source_snapshot_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_calc_snapshots_org_scope3_category
    ON public.calculation_snapshots (organization_id, scope3_category);
CREATE INDEX IF NOT EXISTS idx_calc_snapshots_org_scope2_method
    ON public.calculation_snapshots (organization_id, scope2_method);
CREATE INDEX IF NOT EXISTS idx_calc_snapshots_org_facility
    ON public.calculation_snapshots (organization_id, facility_id);
CREATE INDEX IF NOT EXISTS idx_calc_snapshots_acting_for
    ON public.calculation_snapshots (acting_for_organization_id);

-- ---------------------------------------------------------------------------
-- 2. emissions_logs — the row consumed by reporting (§2.2)
--    Mirrors §2.1 so the consumption boundary can filter Scope 2 method and
--    Scope 3 category without a join to calculation_snapshots.
-- ---------------------------------------------------------------------------
ALTER TABLE public.emissions_logs
    ADD COLUMN IF NOT EXISTS scope2_method      text,
    ADD COLUMN IF NOT EXISTS scope3_category    smallint,
    ADD COLUMN IF NOT EXISTS energy_type        text,
    ADD COLUMN IF NOT EXISTS data_quality       text,
    ADD COLUMN IF NOT EXISTS facility_id        uuid,
    ADD COLUMN IF NOT EXISTS transport_boundary text,
    ADD COLUMN IF NOT EXISTS waste_origin       text,
    ADD COLUMN IF NOT EXISTS source_snapshot_id uuid,
    ADD COLUMN IF NOT EXISTS performed_by_organization_id uuid,
    ADD COLUMN IF NOT EXISTS acting_for_organization_id   uuid;

ALTER TABLE public.emissions_logs DROP CONSTRAINT IF EXISTS emissions_logs_scope2_method_check;
ALTER TABLE public.emissions_logs ADD CONSTRAINT emissions_logs_scope2_method_check
    CHECK (scope2_method IS NULL OR scope2_method IN ('LOCATION_BASED', 'MARKET_BASED'));

ALTER TABLE public.emissions_logs DROP CONSTRAINT IF EXISTS emissions_logs_scope3_category_check;
ALTER TABLE public.emissions_logs ADD CONSTRAINT emissions_logs_scope3_category_check
    CHECK (scope3_category IS NULL OR scope3_category BETWEEN 1 AND 15);

ALTER TABLE public.emissions_logs DROP CONSTRAINT IF EXISTS emissions_logs_energy_type_check;
ALTER TABLE public.emissions_logs ADD CONSTRAINT emissions_logs_energy_type_check
    CHECK (energy_type IS NULL OR energy_type IN ('electricity', 'heat', 'steam', 'cooling'));

ALTER TABLE public.emissions_logs DROP CONSTRAINT IF EXISTS emissions_logs_data_quality_check;
ALTER TABLE public.emissions_logs ADD CONSTRAINT emissions_logs_data_quality_check
    CHECK (data_quality IS NULL OR data_quality IN
        ('primary_measured', 'primary_supplier', 'secondary_estimated', 'spend_based_estimated', 'modelled'));

ALTER TABLE public.emissions_logs DROP CONSTRAINT IF EXISTS emissions_logs_transport_boundary_check;
ALTER TABLE public.emissions_logs ADD CONSTRAINT emissions_logs_transport_boundary_check
    CHECK (transport_boundary IS NULL OR transport_boundary IN ('upstream', 'downstream'));

ALTER TABLE public.emissions_logs DROP CONSTRAINT IF EXISTS emissions_logs_waste_origin_check;
ALTER TABLE public.emissions_logs ADD CONSTRAINT emissions_logs_waste_origin_check
    CHECK (waste_origin IS NULL OR waste_origin IN ('operations', 'sold_product_eol'));

ALTER TABLE public.emissions_logs DROP CONSTRAINT IF EXISTS emissions_logs_scope2_method_required;
ALTER TABLE public.emissions_logs ADD CONSTRAINT emissions_logs_scope2_method_required
    CHECK (scope <> 'Scope 2' OR scope2_method IS NOT NULL) NOT VALID;

ALTER TABLE public.emissions_logs DROP CONSTRAINT IF EXISTS emissions_logs_scope3_category_required;
ALTER TABLE public.emissions_logs ADD CONSTRAINT emissions_logs_scope3_category_required
    CHECK (scope <> 'Scope 3' OR scope3_category IS NOT NULL) NOT VALID;

CREATE INDEX IF NOT EXISTS idx_emissions_logs_org_scope3_category
    ON public.emissions_logs (organization_id, scope3_category);
CREATE INDEX IF NOT EXISTS idx_emissions_logs_org_scope2_method
    ON public.emissions_logs (organization_id, scope2_method);
CREATE INDEX IF NOT EXISTS idx_emissions_logs_org_facility
    ON public.emissions_logs (organization_id, facility_id);

-- ---------------------------------------------------------------------------
-- 3. emission_factors — factor governance (§2.3)
--    Classification columns ONLY. No factor row is created, changed, deleted or
--    given a fabricated multiplier; the existing 7,049 rows stay NULL here until
--    a separately authorised classification pass.
-- ---------------------------------------------------------------------------
ALTER TABLE public.emission_factors
    ADD COLUMN IF NOT EXISTS scope2_method        text,
    ADD COLUMN IF NOT EXISTS scope3_category_hint smallint,
    ADD COLUMN IF NOT EXISTS factor_type          text,
    ADD COLUMN IF NOT EXISTS gas_coverage         text;

COMMENT ON COLUMN public.emission_factors.scope3_category_hint IS
    'P17-A: a PROPOSAL only, never authoritative. The category is confirmed on the activity/snapshot. Must never be treated as the accounting category.';
COMMENT ON COLUMN public.emission_factors.factor_type IS
    'P17-A: primary | secondary | component | upstream | outside_of_scopes.';

ALTER TABLE public.emission_factors DROP CONSTRAINT IF EXISTS emission_factors_scope2_method_check;
ALTER TABLE public.emission_factors ADD CONSTRAINT emission_factors_scope2_method_check
    CHECK (scope2_method IS NULL OR scope2_method IN ('LOCATION_BASED', 'MARKET_BASED'));

ALTER TABLE public.emission_factors DROP CONSTRAINT IF EXISTS emission_factors_scope3_category_hint_check;
ALTER TABLE public.emission_factors ADD CONSTRAINT emission_factors_scope3_category_hint_check
    CHECK (scope3_category_hint IS NULL OR scope3_category_hint BETWEEN 1 AND 15);

ALTER TABLE public.emission_factors DROP CONSTRAINT IF EXISTS emission_factors_factor_type_check;
ALTER TABLE public.emission_factors ADD CONSTRAINT emission_factors_factor_type_check
    CHECK (factor_type IS NULL OR factor_type IN
        ('primary', 'secondary', 'component', 'upstream', 'outside_of_scopes'));

ALTER TABLE public.emission_factors DROP CONSTRAINT IF EXISTS emission_factors_gas_coverage_check;
ALTER TABLE public.emission_factors ADD CONSTRAINT emission_factors_gas_coverage_check
    CHECK (gas_coverage IS NULL OR gas_coverage IN ('CO2', 'CO2e'));

CREATE INDEX IF NOT EXISTS idx_emission_factors_scope2_method
    ON public.emission_factors (scope2_method);

-- ---------------------------------------------------------------------------
-- 4. activity_clarifications — manual-review decisions (§2.4)
--    The EXISTING adjudication lifecycle (versioning, supersedes_id, is_current,
--    evidence_signature, re_evaluation_required) carries the operator decision.
--    No parallel review system is created.
-- ---------------------------------------------------------------------------
ALTER TABLE public.activity_clarifications
    ADD COLUMN IF NOT EXISTS resolved_scope2_method   text,
    ADD COLUMN IF NOT EXISTS resolved_scope3_category smallint;

ALTER TABLE public.activity_clarifications DROP CONSTRAINT IF EXISTS activity_clarifications_resolved_scope2_method_check;
ALTER TABLE public.activity_clarifications ADD CONSTRAINT activity_clarifications_resolved_scope2_method_check
    CHECK (resolved_scope2_method IS NULL OR resolved_scope2_method IN ('LOCATION_BASED', 'MARKET_BASED'));

ALTER TABLE public.activity_clarifications DROP CONSTRAINT IF EXISTS activity_clarifications_resolved_scope3_category_check;
ALTER TABLE public.activity_clarifications ADD CONSTRAINT activity_clarifications_resolved_scope3_category_check
    CHECK (resolved_scope3_category IS NULL OR resolved_scope3_category BETWEEN 1 AND 15);

-- ---------------------------------------------------------------------------
-- 5. organizations — accounting boundary (§2.5) and organization identity (§10.1)
-- ---------------------------------------------------------------------------
ALTER TABLE public.organizations
    ADD COLUMN IF NOT EXISTS consolidation_approach text,
    ADD COLUMN IF NOT EXISTS organization_type      text;

COMMENT ON COLUMN public.organizations.consolidation_approach IS
    'P17-A: OPERATIONAL_CONTROL | FINANCIAL_CONTROL | EQUITY_SHARE (backend/domain/disclosure.py CONSOLIDATION_APPROACHES). NULL = not yet decided and MUST fail closed wherever a category depends on it (DC-07, categories 8/13).';
COMMENT ON COLUMN public.organizations.organization_type IS
    'P17-A/ARCH-06 HIGH-01: the kind of organization this tenant is. A consultant firm is itself a real CarbonTally organization with its own accounting data. NULL is treated as CUSTOMER for backward compatibility so no existing row changes meaning.';

ALTER TABLE public.organizations DROP CONSTRAINT IF EXISTS organizations_consolidation_approach_check;
ALTER TABLE public.organizations ADD CONSTRAINT organizations_consolidation_approach_check
    CHECK (consolidation_approach IS NULL OR consolidation_approach IN
        ('OPERATIONAL_CONTROL', 'FINANCIAL_CONTROL', 'EQUITY_SHARE'));

ALTER TABLE public.organizations DROP CONSTRAINT IF EXISTS organizations_organization_type_check;
ALTER TABLE public.organizations ADD CONSTRAINT organizations_organization_type_check
    CHECK (organization_type IS NULL OR organization_type IN
        ('CUSTOMER', 'CONSULTANT', 'PROCESSING_ENTITY', 'CARBONTALLY_INTERNAL'));

CREATE INDEX IF NOT EXISTS idx_organizations_organization_type
    ON public.organizations (organization_type);

-- ---------------------------------------------------------------------------
-- 6. consultant_profiles — consultant ↔ organization linkage (ARCH-06 HIGH-01)
--    THE documented gap: consultant_profiles is keyed by user_id and carried NO
--    organization_id, so a consultant firm had no tenant identity and could not
--    own accounting data. This adds the linkage additively. It does NOT create a
--    second organization for an existing consultant, does NOT touch
--    consultant_clients (the ratified relationship table, reused unchanged), and
--    does NOT change any existing row: organization_id stays NULL until an
--    operator or a later authorised linkage pass sets it.
-- ---------------------------------------------------------------------------
ALTER TABLE public.consultant_profiles
    ADD COLUMN IF NOT EXISTS organization_id uuid;

COMMENT ON COLUMN public.consultant_profiles.organization_id IS
    'P17-A/ARCH-06 HIGH-01: the organization that IS this consultant firm (organizations.organization_type = CONSULTANT). Nullable and additive - a consultant profile without a firm organization keeps working exactly as before. The firm organization can hold its own Scope 1/2/3 accounting data.';

ALTER TABLE public.consultant_profiles DROP CONSTRAINT IF EXISTS consultant_profiles_organization_id_fkey;
ALTER TABLE public.consultant_profiles ADD CONSTRAINT consultant_profiles_organization_id_fkey
    FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_consultant_profiles_organization_id
    ON public.consultant_profiles (organization_id);

-- ---------------------------------------------------------------------------
-- 7. Acting-for / actor-organization context (§10.3, per-path additive)
--    CONTEXT, NOT AUTHORIZATION. Ownership remains organization_id. These columns
--    are additive metadata and never widen access; RLS is unchanged.
--    Added on every path the architecture marked "(A) additive implementation
--    required", because derivation from an actor column is NOT audit-safe
--    (membership and consultancy can change after the fact).
-- ---------------------------------------------------------------------------
ALTER TABLE public.evidence_line_items
    ADD COLUMN IF NOT EXISTS contributed_by_organization_id uuid,
    ADD COLUMN IF NOT EXISTS acting_for_organization_id    uuid;

ALTER TABLE public.audit_trail
    ADD COLUMN IF NOT EXISTS actor_organization_id      uuid,
    ADD COLUMN IF NOT EXISTS acting_for_organization_id uuid;

ALTER TABLE public.customer_documents
    ADD COLUMN IF NOT EXISTS actor_organization_id      uuid,
    ADD COLUMN IF NOT EXISTS acting_for_organization_id uuid;

ALTER TABLE public.suppliers
    ADD COLUMN IF NOT EXISTS actor_organization_id      uuid,
    ADD COLUMN IF NOT EXISTS acting_for_organization_id uuid;

ALTER TABLE public.review_audit_trail
    ADD COLUMN IF NOT EXISTS actor_organization_id      uuid,
    ADD COLUMN IF NOT EXISTS acting_for_organization_id uuid;

ALTER TABLE public.review_assignment_history
    ADD COLUMN IF NOT EXISTS actor_organization_id      uuid,
    ADD COLUMN IF NOT EXISTS acting_for_organization_id uuid;

ALTER TABLE public.report_versions
    ADD COLUMN IF NOT EXISTS prepared_by_organization_id uuid,
    ADD COLUMN IF NOT EXISTS acting_for_organization_id  uuid;

COMMENT ON COLUMN public.audit_trail.acting_for_organization_id IS
    'P17-A/ARCH-04 §10.3: the authoritative acting-for carrier. Where a path has no reliable object-to-audit linkage this column is the durable record of which organization the actor was operating for.';
COMMENT ON COLUMN public.customer_documents.acting_for_organization_id IS
    'P17-A/ARCH-04 §10.3: persisted acting-for context on the source-document path. Deriving it from uploaded_by at read time is explicitly rejected as not audit-safe.';
COMMENT ON COLUMN public.suppliers.acting_for_organization_id IS
    'P17-A/ARCH-04 §10.3: persisted acting-for context on the supplier path.';
COMMENT ON COLUMN public.report_versions.prepared_by_organization_id IS
    'P17-A/ARCH-04 §10.3: the organization that PREPARED the report (PO §24 "Prepared by: Green Advisory"). Cannot be derived reliably from created_by after the fact.';

CREATE INDEX IF NOT EXISTS idx_customer_documents_acting_for
    ON public.customer_documents (acting_for_organization_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_acting_for
    ON public.suppliers (acting_for_organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_acting_for
    ON public.audit_trail (acting_for_organization_id);
CREATE INDEX IF NOT EXISTS idx_report_versions_prepared_by_org
    ON public.report_versions (prepared_by_organization_id);

-- ============================================================================
-- VERIFICATION CHECKLIST (P17-A)
--   [ ] 8 dimension columns + 2 acting-for columns on calculation_snapshots
--   [ ] mirrors present on emissions_logs
--   [ ] 4 governance columns on emission_factors; ALL existing rows still NULL
--   [ ] 2 resolver columns on activity_clarifications
--   [ ] organizations.consolidation_approach + organization_type
--   [ ] consultant_profiles.organization_id FK -> organizations(id)
--   [ ] acting-for columns on all 7 (§10.3) paths
--   [ ] every historical row byte-identical; NO backfill performed
--   [ ] every NOT VALID rule enforced for new writes only
--   [ ] re-running this file is a no-op
--   [ ] NO RLS policy altered; NO table created
-- ============================================================================




