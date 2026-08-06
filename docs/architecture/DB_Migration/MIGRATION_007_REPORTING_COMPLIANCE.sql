-- ============================================
-- MIGRATION 007: REPORTING & COMPLIANCE
-- Domain 7: Reports, Templates, Compliance
-- ============================================

-- ============================================
-- 7.1 Compliance Frameworks
-- ============================================

CREATE TABLE IF NOT EXISTS compliance_frameworks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    description TEXT,
    version VARCHAR,
    requirements JSONB,
    required_scopes VARCHAR[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 7.2 Report Templates
-- ============================================

CREATE TABLE IF NOT EXISTS report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    template_type VARCHAR CHECK (template_type IN ('secr', 'esrs', 'issb', 'custom')),
    description TEXT,
    sections JSONB,
    required_fields JSONB,
    default_filters JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 7.3 Reports
-- ============================================

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    template_id UUID REFERENCES report_templates(id),
    name VARCHAR NOT NULL,
    report_type VARCHAR CHECK (report_type IN ('secr', 'esrs', 'issb', 'custom')),
    reporting_period_start DATE,
    reporting_period_end DATE,
    status VARCHAR CHECK (status IN ('draft', 'generating', 'completed', 'failed')),
    data JSONB,
    file_path TEXT,
    generated_by UUID REFERENCES users(id),
    generated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 7.4 Report Exports
-- ============================================

CREATE TABLE IF NOT EXISTS report_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    format VARCHAR CHECK (format IN ('pdf', 'csv', 'excel', 'json')),
    file_path TEXT,
    file_size BIGINT,
    exported_by UUID REFERENCES users(id),
    exported_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    download_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 7.5 Report History
-- ============================================

CREATE TABLE IF NOT EXISTS report_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    action VARCHAR,
    old_status VARCHAR,
    new_status VARCHAR,
    notes TEXT,
    performed_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 7.6 SECR Reports (UK-specific)
-- ============================================

CREATE TABLE IF NOT EXISTS secr_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id),
    fiscal_year INTEGER,
    energy_consumption_kwh NUMERIC,
    scope_1_emissions_t_co2e NUMERIC,
    scope_2_emissions_t_co2e NUMERIC,
    total_emissions_t_co2e NUMERIC,
    energy_intensity_kwh_per_revenue NUMERIC,
    emissions_intensity_t_per_revenue NUMERIC,
    methodology VARCHAR,
    verification_status VARCHAR CHECK (verification_status IN ('pending', 'verified', 'rejected')),
    filed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- ROLLBACK: MIGRATION 007
-- ============================================

-- DROP TABLE IF EXISTS secr_reports;
-- DROP TABLE IF EXISTS report_history;
-- DROP TABLE IF EXISTS report_exports;
-- DROP TABLE IF EXISTS reports;
-- DROP TABLE IF EXISTS report_templates;
-- DROP TABLE IF EXISTS compliance_frameworks;