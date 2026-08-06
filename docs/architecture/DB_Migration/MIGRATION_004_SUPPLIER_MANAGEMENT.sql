-- ============================================
-- MIGRATION 004: SUPPLIER MANAGEMENT
-- Domain 3: Suppliers, Contacts, Emissions
-- ============================================

-- ============================================
-- 4.1 Suppliers (Core)
-- ============================================

CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    supplier_code VARCHAR UNIQUE,
    name VARCHAR NOT NULL,
    legal_name VARCHAR,
    trading_name VARCHAR,
    status VARCHAR DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    tier VARCHAR CHECK (tier IN ('strategic', 'preferred', 'approved', 'restricted')),
    relationship_type VARCHAR CHECK (relationship_type IN ('direct', 'indirect', 'distribution')),
    industry VARCHAR,
    website VARCHAR,
    notes TEXT,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 4.2 Supplier Contacts
-- ============================================

CREATE TABLE IF NOT EXISTS supplier_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    email VARCHAR,
    phone VARCHAR,
    role VARCHAR,
    is_primary BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 4.3 Supplier Addresses
-- ============================================

CREATE TABLE IF NOT EXISTS supplier_addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    address_type VARCHAR CHECK (address_type IN ('registered', 'operational', 'billing')),
    address_line1 VARCHAR,
    address_line2 VARCHAR,
    city VARCHAR,
    state VARCHAR,
    country VARCHAR,
    postal_code VARCHAR,
    is_primary BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 4.4 Supplier Categories
-- ============================================

CREATE TABLE IF NOT EXISTS supplier_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    category_id UUID, -- References global categories table
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(supplier_id, category_id)
);

-- ============================================
-- 4.5 Supplier Documents
-- ============================================

CREATE TABLE IF NOT EXISTS supplier_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    type VARCHAR CHECK (type IN ('contract', 'certificate', 'invoice', 'emissions', 'other')),
    valid_from DATE,
    valid_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 4.6 Supplier Notes
-- ============================================

CREATE TABLE IF NOT EXISTS supplier_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    note TEXT NOT NULL,
    visibility VARCHAR CHECK (visibility IN ('private', 'shared', 'client')),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 4.7 Supplier Tags
-- ============================================

CREATE TABLE IF NOT EXISTS supplier_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    tag VARCHAR NOT NULL,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(supplier_id, tag)
);

-- ============================================
-- 4.8 Supplier Emissions
-- ============================================

CREATE TABLE IF NOT EXISTS supplier_emissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    reporting_period_start DATE NOT NULL,
    reporting_period_end DATE NOT NULL,
    scope_1_emissions_kg NUMERIC,
    scope_2_emissions_kg NUMERIC,
    scope_3_emissions_kg NUMERIC,
    total_emissions_kg NUMERIC,
    revenue NUMERIC,
    employees INTEGER,
    methodology VARCHAR,
    verification_status VARCHAR CHECK (verification_status IN ('pending', 'verified', 'rejected')),
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMPTZ,
    notes TEXT,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 4.9 Supplier Spend
-- ============================================

CREATE TABLE IF NOT EXISTS supplier_spend (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(id) ON DELETE CASCADE,
    fiscal_year INTEGER,
    amount NUMERIC NOT NULL,
    currency VARCHAR DEFAULT 'GBP',
    category VARCHAR CHECK (category IN ('goods', 'services', 'utilities', 'other')),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- ROLLBACK: MIGRATION 004
-- ============================================

-- DROP TABLE IF EXISTS supplier_spend;
-- DROP TABLE IF EXISTS supplier_emissions;
-- DROP TABLE IF EXISTS supplier_tags;
-- DROP TABLE IF EXISTS supplier_notes;
-- DROP TABLE IF EXISTS supplier_documents;
-- DROP TABLE IF EXISTS supplier_categories;
-- DROP TABLE IF EXISTS supplier_addresses;
-- DROP TABLE IF EXISTS supplier_contacts;
-- DROP TABLE IF EXISTS suppliers;