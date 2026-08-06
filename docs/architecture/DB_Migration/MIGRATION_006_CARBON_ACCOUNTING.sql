-- ============================================
-- MIGRATION 006: CARBON ACCOUNTING
-- Domain 6: Emission Factors, Calculations, Results
-- ============================================

-- ============================================
-- 6.1 Emission Factors
-- ============================================

CREATE TABLE IF NOT EXISTS emission_factors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    factor_code VARCHAR UNIQUE,
    source VARCHAR CHECK (source IN ('DEFRA', 'EPA', 'IPCC', 'GHG_Protocol', 'Other')),
    year INTEGER,
    activity_type VARCHAR,
    scope VARCHAR CHECK (scope IN ('1', '2', '3')),
    category VARCHAR,
    unit VARCHAR,
    co2e_multiplier NUMERIC,
    ch4_multiplier NUMERIC,
    n2o_multiplier NUMERIC,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 6.2 Activity Data
-- ============================================

CREATE TABLE IF NOT EXISTS activity_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    facility_id UUID REFERENCES facilities(id),
    document_id UUID REFERENCES documents(id),
    emission_factor_id UUID REFERENCES emission_factors(id),
    activity_type VARCHAR,
    raw_quantity NUMERIC,
    unit VARCHAR,
    start_date DATE,
    end_date DATE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 6.3 Emission Calculations
-- ============================================

CREATE TABLE IF NOT EXISTS emission_calculations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_data_id UUID REFERENCES activity_data(id) ON DELETE CASCADE,
    calculated_kg_co2e NUMERIC,
    calculated_t_co2e NUMERIC,
    calculation_method VARCHAR,
    calculation_version VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 6.4 Scope Results (Aggregated)
-- ============================================

CREATE TABLE IF NOT EXISTS scope_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    reporting_period_start DATE NOT NULL,
    reporting_period_end DATE NOT NULL,
    scope_type VARCHAR NOT NULL CHECK (scope_type IN ('1', '2', '3')),
    total_kg_co2e NUMERIC,
    total_t_co2e NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(organization_id, reporting_period_start, reporting_period_end, scope_type)
);

-- ============================================
-- 6.5 Baselines
-- ============================================

CREATE TABLE IF NOT EXISTS baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    base_year INTEGER,
    base_period_start DATE,
    base_period_end DATE,
    scope_1_kg_co2e NUMERIC,
    scope_2_kg_co2e NUMERIC,
    scope_3_kg_co2e NUMERIC,
    total_kg_co2e NUMERIC,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 6.6 Targets
-- ============================================

CREATE TABLE IF NOT EXISTS targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    baseline_id UUID REFERENCES baselines(id),
    name VARCHAR NOT NULL,
    target_type VARCHAR CHECK (target_type IN ('absolute', 'intensity')),
    target_year INTEGER,
    reduction_percentage NUMERIC,
    absolute_target_kg_co2e NUMERIC,
    intensity_target_kg_per_unit NUMERIC,
    intensity_unit VARCHAR,
    status VARCHAR CHECK (status IN ('draft', 'active', 'achieved', 'expired')),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- ROLLBACK: MIGRATION 006
-- ============================================

-- DROP TABLE IF EXISTS targets;
-- DROP TABLE IF EXISTS baselines;
-- DROP TABLE IF EXISTS scope_results;
-- DROP TABLE IF EXISTS emission_calculations;
-- DROP TABLE IF EXISTS activity_data;
-- DROP TABLE IF EXISTS emission_factors;