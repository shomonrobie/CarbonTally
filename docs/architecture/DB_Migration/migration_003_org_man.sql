-- ============================================
-- MIGRATION 003: ORGANIZATION MANAGEMENT
-- Domain 2: Organizations, Facilities, Departments, Teams
-- ============================================

-- ============================================
-- 3.1 Organizations (Core)
-- ============================================

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    company_number VARCHAR UNIQUE,
    legal_name VARCHAR,
    trading_name VARCHAR,
    registration_number VARCHAR,
    vat_number VARCHAR,
    website TEXT,
    industry VARCHAR,
    sector VARCHAR,
    company_size VARCHAR,
    country VARCHAR,
    timezone VARCHAR DEFAULT 'UTC',
    currency VARCHAR DEFAULT 'GBP',
    status VARCHAR DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'archived')),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 3.2 Organization Settings
-- ============================================

CREATE TABLE IF NOT EXISTS organization_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE UNIQUE,
    reporting_standard VARCHAR CHECK (reporting_standard IN ('ghg_protocol', 'secr', 'esrs', 'issb')),
    financial_year_end DATE,
    default_defra_version INTEGER,
    preferred_units VARCHAR,
    secr_enabled BOOLEAN DEFAULT FALSE,
    esrs_enabled BOOLEAN DEFAULT FALSE,
    issb_enabled BOOLEAN DEFAULT FALSE,
    require_2fa BOOLEAN DEFAULT FALSE,
    session_timeout_minutes INTEGER DEFAULT 60,
    data_retention_days INTEGER DEFAULT 365,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 3.3 Organization Metadata
-- ============================================

CREATE TABLE IF NOT EXISTS organization_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE UNIQUE,
    -- Employee metrics
    total_employees INTEGER,
    full_time_employees INTEGER,
    part_time_employees INTEGER,
    contract_employees INTEGER,
    average_employees INTEGER,
    -- Financial metrics
    annual_revenue NUMERIC,
    ebitda NUMERIC,
    total_assets NUMERIC,
    -- Operational metrics
    total_facilities INTEGER,
    total_floor_area_sqft NUMERIC,
    occupied_floor_area_sqft NUMERIC,
    renewable_energy_percentage NUMERIC,
    carbon_offset_percentage NUMERIC,
    energy_intensity NUMERIC,
    -- Contacts
    primary_contact_name VARCHAR,
    primary_contact_email VARCHAR,
    primary_contact_phone VARCHAR,
    sustainability_officer_name VARCHAR,
    sustainability_officer_email VARCHAR,
    -- Classification
    industry_sector VARCHAR,
    naics_code VARCHAR,
    sic_code VARCHAR,
    custom_metrics JSONB,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 3.4 Facilities
-- ============================================

CREATE TABLE IF NOT EXISTS facilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    type VARCHAR CHECK (type IN ('office', 'warehouse', 'manufacturing', 'retail', 'data_center', 'research', 'other')),
    address_line1 VARCHAR,
    address_line2 VARCHAR,
    city VARCHAR,
    county VARCHAR,
    country VARCHAR,
    postcode VARCHAR,
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    region VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 3.5 Departments
-- ============================================

CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    facility_id UUID REFERENCES facilities(id),
    name VARCHAR NOT NULL,
    code VARCHAR,
    cost_center VARCHAR,
    manager_id UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 3.6 Teams
-- ============================================

CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id),
    name VARCHAR NOT NULL,
    leader_id UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- ROLLBACK: MIGRATION 003
-- ============================================

-- DROP TABLE IF EXISTS teams;
-- DROP TABLE IF EXISTS departments;
-- DROP TABLE IF EXISTS facilities;
-- DROP TABLE IF EXISTS organization_metadata;
-- DROP TABLE IF EXISTS organization_settings;
-- DROP TABLE IF EXISTS organizations;