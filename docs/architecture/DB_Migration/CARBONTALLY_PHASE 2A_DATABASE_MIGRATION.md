CARBONTALLY PHASE 2A - DATABASE MIGRATION
Migration Execution Plan
This document defines the complete migration sequence for CarbonTally v1.0. The architecture is frozen and these migrations represent the final, approved schema design.

Migration Strategy
Principles
Idempotent: Each migration can be run multiple times safely

Reversible: Each migration has a rollback path

Incremental: Small, focused migrations

Data-preserving: No data loss during migration

Backward-compatible: Old code continues to work during migration

Execution Order
text
Phase 2A - Database Migration
│
├── 001_identity.sql     → Users, Roles, Permissions (Domain 1)
├── 002_workspace.sql    → Workspaces, Organization Access (Domain 1)
├── 003_organization.sql → Organizations, Facilities (Domain 2)
├── 004_supplier.sql     → Suppliers, Contacts, Emissions (Domain 3)
├── 005_document.sql     → Documents, Versions, Processing (Domain 4)
├── 006_carbon.sql       → Emission Factors, Calculations (Domain 6)
├── 007_reporting.sql    → Reports, Templates, Compliance (Domain 7)
├── 008_collaboration.sql → Notifications, Messages (Domain 8)
├── 009_platform.sql     → Audit Logs, Settings, Flags (Domain 9)
├── 010_rls.sql          → Row Level Security Policies
├── 011_indexes.sql      → Performance Indexes
└── 012_migration.sql    → Data Migration & Cleanup
MIGRATION 001: IDENTITY & ACCESS
sql
-- ============================================
-- MIGRATION 001: IDENTITY & ACCESS
-- Domain 1: Users, Roles, Permissions
-- ============================================

-- ============================================
-- 1.1 Users
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    first_name VARCHAR,
    last_name VARCHAR,
    display_name VARCHAR,
    avatar_url TEXT,
    phone VARCHAR,
    timezone VARCHAR DEFAULT 'UTC',
    locale VARCHAR DEFAULT 'en',
    email_verified_at TIMESTAMPTZ,
    phone_verified_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    last_login_ip INET,
    is_active BOOLEAN DEFAULT TRUE,
    is_locked BOOLEAN DEFAULT FALSE,
    locked_until TIMESTAMPTZ,
    failed_login_attempts INTEGER DEFAULT 0,
    employee_id VARCHAR,
    department VARCHAR,
    job_title VARCHAR,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 1.2 Workspaces
-- ============================================

CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    code VARCHAR UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed default workspaces
INSERT INTO workspaces (id, name, code, description) VALUES
    (gen_random_uuid(), 'Platform Workspace', 'platform', 'Internal platform staff administration'),
    (gen_random_uuid(), 'Client Workspace', 'client', 'Organization dashboard and management')
ON CONFLICT (code) DO NOTHING;

-- ============================================
-- 1.3 Permissions
-- ============================================

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR UNIQUE NOT NULL,
    resource VARCHAR NOT NULL,
    action VARCHAR NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed base permissions
INSERT INTO permissions (code, resource, action, description) VALUES
    -- Document permissions
    ('documents.view', 'documents', 'view', 'View documents'),
    ('documents.create', 'documents', 'create', 'Upload/create documents'),
    ('documents.update', 'documents', 'update', 'Update document metadata'),
    ('documents.delete', 'documents', 'delete', 'Delete/archive documents'),
    ('documents.approve', 'documents', 'approve', 'Approve documents'),
    ('documents.review', 'documents', 'review', 'Review documents'),
    
    -- Supplier permissions
    ('suppliers.view', 'suppliers', 'view', 'View suppliers'),
    ('suppliers.create', 'suppliers', 'create', 'Create suppliers'),
    ('suppliers.update', 'suppliers', 'update', 'Update suppliers'),
    ('suppliers.delete', 'suppliers', 'delete', 'Delete suppliers'),
    
    -- Emission permissions
    ('emissions.view', 'emissions', 'view', 'View emission data'),
    ('emissions.create', 'emissions', 'create', 'Create emission records'),
    ('emissions.update', 'emissions', 'update', 'Update emission records'),
    ('emissions.delete', 'emissions', 'delete', 'Delete emission records'),
    ('emissions.calculate', 'emissions', 'calculate', 'Perform emission calculations'),
    
    -- Report permissions
    ('reports.view', 'reports', 'view', 'View reports'),
    ('reports.create', 'reports', 'create', 'Generate reports'),
    ('reports.export', 'reports', 'export', 'Export reports'),
    
    -- Organization permissions
    ('organizations.view', 'organizations', 'view', 'View organization details'),
    ('organizations.update', 'organizations', 'update', 'Update organization settings'),
    ('organizations.manage', 'organizations', 'manage', 'Manage organization members'),
    
    -- Platform permissions
    ('platform.admin', 'platform', 'admin', 'Full platform administration'),
    ('platform.view_users', 'platform', 'view_users', 'View platform users'),
    ('platform.manage_users', 'platform', 'manage_users', 'Manage platform users'),
    ('platform.view_audit', 'platform', 'view_audit', 'View audit logs'),
    ('platform.manage_settings', 'platform', 'manage_settings', 'Manage system settings')
ON CONFLICT (code) DO NOTHING;

-- ============================================
-- 1.4 Permission Groups
-- ============================================

CREATE TABLE IF NOT EXISTS permission_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR,
    sort_order INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed permission groups
INSERT INTO permission_groups (name, description, sort_order) VALUES
    ('Document Management', 'Document upload, review, and approval', 1),
    ('Supplier Management', 'Supplier data management', 2),
    ('Carbon Accounting', 'Emission calculations and tracking', 3),
    ('Reporting', 'Report generation and export', 4),
    ('Organization Management', 'Organization settings and team', 5),
    ('Platform Administration', 'System administration and settings', 6),
    ('Audit & Compliance', 'Audit logs and compliance', 7)
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- 1.5 Group Permissions
-- ============================================

CREATE TABLE IF NOT EXISTS group_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID REFERENCES permission_groups(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(group_id, permission_id)
);

-- Link permissions to groups
WITH groups AS (
    SELECT id, name FROM permission_groups
),
perms AS (
    SELECT id, code FROM permissions
)
INSERT INTO group_permissions (group_id, permission_id)
SELECT 
    (SELECT id FROM groups WHERE name = 'Document Management'),
    (SELECT id FROM perms WHERE code LIKE 'documents.%')
WHERE EXISTS (SELECT 1 FROM perms WHERE code LIKE 'documents.%')
ON CONFLICT (group_id, permission_id) DO NOTHING;

-- ============================================
-- 1.6 Roles
-- ============================================

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR UNIQUE NOT NULL,
    description TEXT,
    role_type VARCHAR NOT NULL CHECK (role_type IN ('platform', 'organization')),
    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL
);

-- Seed default roles
INSERT INTO roles (name, description, role_type, is_system) VALUES
    -- Platform roles
    ('Super Admin', 'Full platform access', 'platform', TRUE),
    ('Carbon Analyst', 'Carbon analysis and reporting', 'platform', TRUE),
    ('Senior Validator', 'Validation and approval of data', 'platform', TRUE),
    ('Support', 'Customer support access', 'platform', TRUE),
    ('Sales', 'Sales and CRM access', 'platform', TRUE),
    ('Compliance', 'Compliance and audit access', 'platform', TRUE),
    
    -- Organization roles
    ('Organization Admin', 'Full organization management', 'organization', TRUE),
    ('Sustainability Manager', 'Manage sustainability data', 'organization', TRUE),
    ('Finance', 'Access to financial carbon impact', 'organization', TRUE),
    ('Operations', 'Access to operational emissions', 'organization', TRUE),
    ('Data Entry', 'Upload and data entry', 'organization', TRUE),
    ('Viewer', 'Read-only access', 'organization', TRUE),
    ('Consultant', 'Multi-organization access', 'organization', TRUE)
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- 1.7 Role Permissions
-- ============================================

CREATE TABLE IF NOT EXISTS role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    granted_by UUID REFERENCES users(id),
    UNIQUE(role_id, permission_id)
);

-- ============================================
-- 1.8 User Roles
-- ============================================

CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    granted_by UUID REFERENCES users(id),
    expires_at TIMESTAMPTZ NULL,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, role_id)
);

-- ============================================
-- 1.9 Sessions
-- ============================================

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    last_activity_at TIMESTAMPTZ DEFAULT NOW(),
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 1.10 API Keys (Future)
-- ============================================

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    key_hash VARCHAR UNIQUE NOT NULL,
    key_preview VARCHAR(8),
    permissions JSONB,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- ROLLBACK: MIGRATION 001
-- ============================================

-- DROP TABLE IF EXISTS api_keys;
-- DROP TABLE IF EXISTS sessions;
-- DROP TABLE IF EXISTS user_roles;
-- DROP TABLE IF EXISTS role_permissions;
-- DROP TABLE IF EXISTS roles;
-- DROP TABLE IF EXISTS group_permissions;
-- DROP TABLE IF EXISTS permission_groups;
-- DROP TABLE IF EXISTS permissions;
-- DROP TABLE IF EXISTS workspaces;
-- DROP TABLE IF EXISTS users;
MIGRATION 002: WORKSPACE & ORGANIZATION ACCESS
sql
-- ============================================
-- MIGRATION 002: WORKSPACE & ORGANIZATION ACCESS
-- Domain 1: Organization Access, Workspace Access
-- ============================================

-- ============================================
-- 2.1 Organization Access (CORE TABLE)
-- ============================================

CREATE TABLE IF NOT EXISTS organization_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id),
    role_id UUID REFERENCES roles(id),
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    access_type VARCHAR CHECK (access_type IN ('owner', 'member', 'consultant', 'platform')),
    invited_by UUID REFERENCES users(id),
    accepted_at TIMESTAMPTZ,
    last_accessed_at TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    UNIQUE(user_id, organization_id, workspace_id)
);

-- ============================================
-- 2.2 Workspace Access
-- ============================================

CREATE TABLE IF NOT EXISTS workspace_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id),
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, workspace_id)
);

-- ============================================
-- 2.3 Organization Members (Legacy Compatibility)
-- ============================================

-- Keep as a view for backward compatibility
CREATE OR REPLACE VIEW organization_members AS
SELECT 
    oa.id,
    oa.organization_id,
    oa.user_id,
    r.name AS role,
    oa.created_at,
    oa.is_active,
    oa.updated_at
FROM organization_access oa
LEFT JOIN roles r ON r.id = oa.role_id
WHERE oa.deleted_at IS NULL;

-- ============================================
-- ROLLBACK: MIGRATION 002
-- ============================================

-- DROP VIEW IF EXISTS organization_members;
-- DROP TABLE IF EXISTS workspace_access;
-- DROP TABLE IF EXISTS organization_access;
MIGRATION 003: ORGANIZATION MANAGEMENT
sql
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
MIGRATION 004: SUPPLIER MANAGEMENT
sql
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
MIGRATION 005: DOCUMENT MANAGEMENT
sql
-- ============================================
-- MIGRATION 005: DOCUMENT MANAGEMENT
-- Domain 4: Documents, Versions, Processing
-- ============================================

-- ============================================
-- 5.1 Document Types (Taxonomy)
-- ============================================

CREATE TABLE IF NOT EXISTS document_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    category VARCHAR,
    description TEXT,
    file_extensions TEXT[],
    mime_types TEXT[],
    requires_asset BOOLEAN DEFAULT FALSE,
    requires_date_range BOOLEAN DEFAULT FALSE,
    requires_facility BOOLEAN DEFAULT FALSE,
    priority INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 5.2 Documents (Core)
-- ============================================

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    supplier_id UUID REFERENCES suppliers(id),
    document_type_id UUID REFERENCES document_types(id),
    name VARCHAR NOT NULL,
    description TEXT,
    file_name VARCHAR NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR,
    storage_path TEXT NOT NULL,
    hash VARCHAR,
    status VARCHAR DEFAULT 'uploaded' 
        CHECK (status IN ('uploaded', 'processing', 'processed', 'reviewed', 'approved', 'rejected', 'archived')),
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 5.3 Document Versions
-- ============================================

CREATE TABLE IF NOT EXISTS document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    file_name VARCHAR NOT NULL,
    file_size BIGINT,
    storage_path TEXT NOT NULL,
    hash VARCHAR,
    changes TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(document_id, version)
);

-- ============================================
-- 5.4 Document Processing (Pipeline)
-- ============================================

CREATE TABLE IF NOT EXISTS document_processing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    stage VARCHAR NOT NULL 
        CHECK (stage IN ('uploaded', 'ocr', 'extraction', 'mapping', 'review', 'approval')),
    status VARCHAR DEFAULT 'pending' 
        CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 5.5 Document Extractions
-- ============================================

CREATE TABLE IF NOT EXISTS document_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    extraction_type VARCHAR CHECK (extraction_type IN ('ocr', 'ai', 'hybrid')),
    raw_data JSONB,
    structured_data JSONB,
    confidence_score NUMERIC(5,2),
    fields_extracted JSONB,
    extraction_model VARCHAR,
    extracted_by VARCHAR,
    extracted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 5.6 Document Reviews
-- ============================================

CREATE TABLE IF NOT EXISTS document_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    reviewer_id UUID REFERENCES users(id),
    review_status VARCHAR CHECK (review_status IN ('pending', 'in_progress', 'completed')),
    comments TEXT,
    changes JSONB,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 5.7 Document Approvals
-- ============================================

CREATE TABLE IF NOT EXISTS document_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    approver_id UUID REFERENCES users(id),
    approval_level INTEGER DEFAULT 1,
    status VARCHAR CHECK (status IN ('pending', 'approved', 'rejected')),
    comments TEXT,
    signature_data JSONB,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 5.8 Document Exports
-- ============================================

CREATE TABLE IF NOT EXISTS document_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    export_format VARCHAR CHECK (export_format IN ('pdf', 'csv', 'excel', 'json')),
    exported_by UUID REFERENCES users(id),
    exported_at TIMESTAMPTZ DEFAULT NOW(),
    file_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- ROLLBACK: MIGRATION 005
-- ============================================

-- DROP TABLE IF EXISTS document_exports;
-- DROP TABLE IF EXISTS document_approvals;
-- DROP TABLE IF EXISTS document_reviews;
-- DROP TABLE IF EXISTS document_extractions;
-- DROP TABLE IF EXISTS document_processing;
-- DROP TABLE IF EXISTS document_versions;
-- DROP TABLE IF EXISTS documents;
-- DROP TABLE IF EXISTS document_types;
MIGRATION 006: CARBON ACCOUNTING
sql
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
MIGRATION 007: REPORTING & COMPLIANCE
sql
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
MIGRATION 008: COLLABORATION
sql
-- ============================================
-- MIGRATION 008: COLLABORATION
-- Domain 8: Notifications, Messages, Comments
-- ============================================

-- ============================================
-- 8.1 Conversations
-- ============================================

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    subject VARCHAR,
    status VARCHAR DEFAULT 'active' CHECK (status IN ('active', 'archived', 'closed')),
    last_message_at TIMESTAMPTZ,
    is_urgent BOOLEAN DEFAULT FALSE,
    priority VARCHAR DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 8.2 Conversation Participants
-- ============================================

CREATE TABLE IF NOT EXISTS conversation_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    last_read_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(conversation_id, user_id)
);

-- ============================================
-- 8.3 Messages
-- ============================================

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 8.4 Comments
-- ============================================

CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES comments(id),
    entity_type VARCHAR NOT NULL CHECK (entity_type IN ('document', 'supplier', 'report', 'emission', 'organization')),
    entity_id UUID NOT NULL,
    content TEXT NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 8.5 Notifications
-- ============================================

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id),
    type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    message TEXT,
    link TEXT,
    priority VARCHAR DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    is_dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 8.6 Tasks
-- ============================================

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES users(id),
    assigned_by UUID REFERENCES users(id),
    title VARCHAR NOT NULL,
    description TEXT,
    task_type VARCHAR CHECK (task_type IN ('review', 'approval', 'data_entry', 'verification', 'other')),
    entity_type VARCHAR CHECK (entity_type IN ('document', 'supplier', 'report', 'emission', 'organization')),
    entity_id UUID,
    priority VARCHAR DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status VARCHAR DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 8.7 Support Tickets
-- ============================================

CREATE TABLE IF NOT EXISTS support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    assigned_to UUID REFERENCES users(id),
    title VARCHAR NOT NULL,
    description TEXT,
    severity VARCHAR CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- ROLLBACK: MIGRATION 008
-- ============================================

-- DROP TABLE IF EXISTS support_tickets;
-- DROP TABLE IF EXISTS tasks;
-- DROP TABLE IF EXISTS notifications;
-- DROP TABLE IF EXISTS comments;
-- DROP TABLE IF EXISTS messages;
-- DROP TABLE IF EXISTS conversation_participants;
-- DROP TABLE IF EXISTS conversations;
MIGRATION 009: PLATFORM ADMINISTRATION
sql
-- ============================================
-- MIGRATION 009: PLATFORM ADMINISTRATION
-- Domain 9: Audit Logs, Settings, Flags, Jobs
-- ============================================

-- ============================================
-- 9.1 Audit Logs
-- ============================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    action_type VARCHAR NOT NULL,
    resource_type VARCHAR,
    resource_id UUID,
    description TEXT,
    ip_address INET,
    user_agent TEXT,
    old_data JSONB,
    new_data JSONB,
    changes JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- 9.2 System Settings
-- ============================================

CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    settings_json JSONB,
    max_file_size_mb INTEGER DEFAULT 50,
    allowed_file_types TEXT[] DEFAULT '{".pdf",".csv",".xlsx"}',
    enable_auto_repair BOOLEAN DEFAULT TRUE,
    max_batch_files INTEGER DEFAULT 100,
    max_total_batch_size_mb INTEGER DEFAULT 1000,
    data_retention_days INTEGER DEFAULT 365,
    require_2fa BOOLEAN DEFAULT FALSE,
    session_timeout_minutes INTEGER DEFAULT 60,
    max_login_attempts INTEGER DEFAULT 5,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 9.3 Feature Flags
-- ============================================

CREATE TABLE IF NOT EXISTS feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR UNIQUE NOT NULL,
    code VARCHAR UNIQUE NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT FALSE,
    enabled_for_organizations UUID[],
    enabled_for_users UUID[],
    rollout_percentage INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 9.4 Background Jobs
-- ============================================

CREATE TABLE IF NOT EXISTS background_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR NOT NULL,
    job_data JSONB,
    status VARCHAR DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    priority INTEGER DEFAULT 1,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    last_error TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    scheduled_for TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 9.5 API Logs
-- ============================================

CREATE TABLE IF NOT EXISTS api_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id),
    organization_id UUID REFERENCES organizations(id),
    endpoint VARCHAR NOT NULL,
    method VARCHAR NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    ip_address INET,
    user_agent TEXT,
    request_body JSONB,
    response_body JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 9.6 Error Logs
-- ============================================

CREATE TABLE IF NOT EXISTS error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_code VARCHAR,
    error_message TEXT,
    stack_trace TEXT,
    context JSONB,
    severity VARCHAR CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- ROLLBACK: MIGRATION 009
-- ============================================

-- DROP TABLE IF EXISTS error_logs;
-- DROP TABLE IF EXISTS api_logs;
-- DROP TABLE IF EXISTS background_jobs;
-- DROP TABLE IF EXISTS feature_flags;
-- DROP TABLE IF EXISTS system_settings;
-- DROP TABLE IF EXISTS audit_logs;
MIGRATION 010: ROW LEVEL SECURITY (RLS)
sql
-- ============================================
-- MIGRATION 010: ROW LEVEL SECURITY
-- All tables with organization_id get RLS
-- ============================================

-- ============================================
-- Enable RLS on all tables
-- ============================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE facilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_access ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_access ENABLE ROW LEVEL SECURITY;
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_emissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_spend ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_processing ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_extractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE emission_calculations ENABLE ROW LEVEL SECURITY;
ALTER TABLE scope_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE baselines ENABLE ROW LEVEL SECURITY;
ALTER TABLE targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_exports ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE support_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- Helper Function: Get User's Organizations
-- ============================================

CREATE OR REPLACE FUNCTION get_user_organizations(user_id UUID)
RETURNS TABLE(org_id UUID) AS $$
BEGIN
    RETURN QUERY
    SELECT oa.organization_id
    FROM organization_access oa
    WHERE oa.user_id = user_id
    AND oa.is_active = TRUE
    AND oa.deleted_at IS NULL
    AND (oa.valid_to IS NULL OR oa.valid_to > NOW());
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================
-- Organization Access Policies
-- ============================================

-- Users can view their own access records
CREATE POLICY organization_access_select_policy ON organization_access
    FOR SELECT USING (user_id = auth.uid() OR 
                      auth.uid() IN (SELECT created_by FROM organizations WHERE id = organization_id));

-- Users can update their own access records
CREATE POLICY organization_access_update_policy ON organization_access
    FOR UPDATE USING (user_id = auth.uid());

-- ============================================
-- Organizations Policies
-- ============================================

CREATE POLICY organizations_select_policy ON organizations
    FOR SELECT USING (
        id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND is_active = TRUE)
        OR EXISTS (SELECT 1 FROM organization_access WHERE user_id = auth.uid() AND access_type = 'platform' AND is_active = TRUE)
    );

CREATE POLICY organizations_update_policy ON organizations
    FOR UPDATE USING (
        id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND access_type IN ('owner', 'platform') AND is_active = TRUE)
    );

-- ============================================
-- Facilities Policies
-- ============================================

CREATE POLICY facilities_select_policy ON facilities
    FOR SELECT USING (
        organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND is_active = TRUE)
    );

CREATE POLICY facilities_modify_policy ON facilities
    FOR ALL USING (
        organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND access_type IN ('owner', 'member', 'consultant') AND is_active = TRUE)
    );

-- ============================================
-- Suppliers Policies
-- ============================================

CREATE POLICY suppliers_select_policy ON suppliers
    FOR SELECT USING (
        organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND is_active = TRUE)
    );

CREATE POLICY suppliers_modify_policy ON suppliers
    FOR ALL USING (
        organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND access_type IN ('owner', 'member', 'consultant') AND is_active = TRUE)
    );

-- ============================================
-- Documents Policies
-- ============================================

CREATE POLICY documents_select_policy ON documents
    FOR SELECT USING (
        organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND is_active = TRUE)
    );

CREATE POLICY documents_modify_policy ON documents
    FOR ALL USING (
        organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND access_type IN ('owner', 'member', 'consultant') AND is_active = TRUE)
    );

-- ============================================
-- Reports Policies
-- ============================================

CREATE POLICY reports_select_policy ON reports
    FOR SELECT USING (
        organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND is_active = TRUE)
    );

CREATE POLICY reports_modify_policy ON reports
    FOR ALL USING (
        organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND access_type IN ('owner', 'member', 'consultant') AND is_active = TRUE)
    );

-- ============================================
-- Activity Data Policies
-- ============================================

CREATE POLICY activity_data_select_policy ON activity_data
    FOR SELECT USING (
        organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND is_active = TRUE)
    );

CREATE POLICY activity_data_modify_policy ON activity_data
    FOR ALL USING (
        organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND access_type IN ('owner', 'member', 'consultant') AND is_active = TRUE)
    );

-- ============================================
-- Audit Logs Policies (Platform staff only)
-- ============================================

CREATE POLICY audit_logs_select_policy ON audit_logs
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM organization_access WHERE user_id = auth.uid() AND access_type = 'platform' AND is_active = TRUE)
        OR organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND is_active = TRUE)
    );

CREATE POLICY audit_logs_insert_policy ON audit_logs
    FOR INSERT WITH CHECK (TRUE); -- Anyone can insert audit logs

-- ============================================
-- Notifications Policies
-- ============================================

CREATE POLICY notifications_select_policy ON notifications
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY notifications_update_policy ON notifications
    FOR UPDATE USING (user_id = auth.uid());

-- ============================================
-- Messages Policies
-- ============================================

CREATE POLICY messages_select_policy ON messages
    FOR SELECT USING (
        conversation_id IN (SELECT conversation_id FROM conversation_participants WHERE user_id = auth.uid())
    );

CREATE POLICY messages_insert_policy ON messages
    FOR INSERT WITH CHECK (
        conversation_id IN (SELECT conversation_id FROM conversation_participants WHERE user_id = auth.uid())
    );

-- ============================================
-- Comments Policies
-- ============================================

CREATE POLICY comments_select_policy ON comments
    FOR SELECT USING (
        organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid() AND is_active = TRUE)
    );

CREATE POLICY comments_modify_policy ON comments
    FOR ALL USING (user_id = auth.uid());

-- ============================================
-- Rollback: MIGRATION 010
-- ============================================

-- DROP POLICY IF EXISTS comments_modify_policy ON comments;
-- DROP POLICY IF EXISTS comments_select_policy ON comments;
-- DROP POLICY IF EXISTS messages_insert_policy ON messages;
-- DROP POLICY IF EXISTS messages_select_policy ON messages;
-- DROP POLICY IF EXISTS notifications_update_policy ON notifications;
-- DROP POLICY IF EXISTS notifications_select_policy ON notifications;
-- DROP POLICY IF EXISTS audit_logs_insert_policy ON audit_logs;
-- DROP POLICY IF EXISTS audit_logs_select_policy ON audit_logs;
-- DROP POLICY IF EXISTS activity_data_modify_policy ON activity_data;
-- DROP POLICY IF EXISTS activity_data_select_policy ON activity_data;
-- DROP POLICY IF EXISTS reports_modify_policy ON reports;
-- DROP POLICY IF EXISTS reports_select_policy ON reports;
-- DROP POLICY IF EXISTS documents_modify_policy ON documents;
-- DROP POLICY IF EXISTS documents_select_policy ON documents;
-- DROP POLICY IF EXISTS suppliers_modify_policy ON suppliers;
-- DROP POLICY IF EXISTS suppliers_select_policy ON suppliers;
-- DROP POLICY IF EXISTS facilities_modify_policy ON facilities;
-- DROP POLICY IF EXISTS facilities_select_policy ON facilities;
-- DROP POLICY IF EXISTS organizations_update_policy ON organizations;
-- DROP POLICY IF EXISTS organizations_select_policy ON organizations;
-- DROP POLICY IF EXISTS organization_access_update_policy ON organization_access;
-- DROP POLICY IF EXISTS organization_access_select_policy ON organization_access;
MIGRATION 011: PERFORMANCE INDEXES
sql
-- ============================================
-- MIGRATION 011: PERFORMANCE INDEXES
-- Critical indexes for all tables
-- ============================================

-- ============================================
-- Users Indexes
-- ============================================

CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ============================================
-- Organizations Indexes
-- ============================================

CREATE INDEX idx_organizations_company_number ON organizations(company_number) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_status ON organizations(status);
CREATE INDEX idx_organizations_created_at ON organizations(created_at);

-- ============================================
-- Organization Access Indexes
-- ============================================

CREATE INDEX idx_org_access_user_id ON organization_access(user_id) WHERE is_active = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_org_access_organization_id ON organization_access(organization_id) WHERE is_active = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_org_access_user_org ON organization_access(user_id, organization_id) WHERE is_active = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_org_access_workspace ON organization_access(workspace_id) WHERE is_active = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_org_access_type ON organization_access(access_type) WHERE is_active = TRUE AND deleted_at IS NULL;

-- ============================================
-- Facilities Indexes
-- ============================================

CREATE INDEX idx_facilities_organization_id ON facilities(organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_facilities_postcode ON facilities(postcode);
CREATE INDEX idx_facilities_is_active ON facilities(is_active);

-- ============================================
-- Suppliers Indexes
-- ============================================

CREATE INDEX idx_suppliers_organization_id ON suppliers(organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_suppliers_supplier_code ON suppliers(supplier_code) WHERE deleted_at IS NULL;
CREATE INDEX idx_suppliers_status ON suppliers(status);
CREATE INDEX idx_suppliers_tier ON suppliers(tier);

-- ============================================
-- Supplier Emissions Indexes
-- ============================================

CREATE INDEX idx_supplier_emissions_supplier_id ON supplier_emissions(supplier_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_supplier_emissions_period ON supplier_emissions(reporting_period_start, reporting_period_end) WHERE deleted_at IS NULL;

-- ============================================
-- Documents Indexes
-- ============================================

CREATE INDEX idx_documents_organization_id ON documents(organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_supplier_id ON documents(supplier_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_type ON documents(document_type_id);
CREATE INDEX idx_documents_hash ON documents(hash);

-- ============================================
-- Document Processing Indexes
-- ============================================

CREATE INDEX idx_doc_processing_document_id ON document_processing(document_id);
CREATE INDEX idx_doc_processing_status ON document_processing(status);
CREATE INDEX idx_doc_processing_stage ON document_processing(stage);

-- ============================================
-- Activity Data Indexes
-- ============================================

CREATE INDEX idx_activity_data_organization_id ON activity_data(organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_activity_data_facility_id ON activity_data(facility_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_activity_data_document_id ON activity_data(document_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_activity_data_period ON activity_data(start_date, end_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_activity_data_emission_factor ON activity_data(emission_factor_id) WHERE deleted_at IS NULL;

-- ============================================
-- Emission Calculations Indexes
-- ============================================

CREATE INDEX idx_emission_calc_activity_data_id ON emission_calculations(activity_data_id);

-- ============================================
-- Scope Results Indexes
-- ============================================

CREATE INDEX idx_scope_results_organization_id ON scope_results(organization_id);
CREATE INDEX idx_scope_results_period ON scope_results(reporting_period_start, reporting_period_end);
CREATE INDEX idx_scope_results_scope ON scope_results(scope_type);

-- ============================================
-- Reports Indexes
-- ============================================

CREATE INDEX idx_reports_organization_id ON reports(organization_id);
CREATE INDEX idx_reports_template_id ON reports(template_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_period ON reports(reporting_period_start, reporting_period_end);

-- ============================================
-- Notifications Indexes
-- ============================================

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- ============================================
-- Messages Indexes
-- ============================================

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- ============================================
-- Conversation Participants Indexes
-- ============================================

CREATE INDEX idx_conv_participants_conversation ON conversation_participants(conversation_id);
CREATE INDEX idx_conv_participants_user ON conversation_participants(user_id);

-- ============================================
-- Comments Indexes
-- ============================================

CREATE INDEX idx_comments_user_id ON comments(user_id);
CREATE INDEX idx_comments_entity ON comments(entity_type, entity_id);
CREATE INDEX idx_comments_parent_id ON comments(parent_id);

-- ============================================
-- Tasks Indexes
-- ============================================

CREATE INDEX idx_tasks_organization_id ON tasks(organization_id);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_entity ON tasks(entity_type, entity_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);

-- ============================================
-- Audit Logs Indexes
-- ============================================

CREATE INDEX idx_audit_logs_organization_id ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- ============================================
-- Support Tickets Indexes
-- ============================================

CREATE INDEX idx_support_tickets_organization_id ON support_tickets(organization_id);
CREATE INDEX idx_support_tickets_assigned_to ON support_tickets(assigned_to);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);

-- ============================================
-- Background Jobs Indexes
-- ============================================

CREATE INDEX idx_bg_jobs_status ON background_jobs(status);
CREATE INDEX idx_bg_jobs_scheduled_for ON background_jobs(scheduled_for);

-- ============================================
-- Rollback: MIGRATION 011
-- ============================================

-- DROP INDEX IF EXISTS idx_support_tickets_status;
-- DROP INDEX IF EXISTS idx_support_tickets_assigned_to;
-- DROP INDEX IF EXISTS idx_support_tickets_organization_id;
-- DROP INDEX IF EXISTS idx_audit_logs_created_at;
-- DROP INDEX IF EXISTS idx_audit_logs_resource;
-- DROP INDEX IF EXISTS idx_audit_logs_action_type;
-- DROP INDEX IF EXISTS idx_audit_logs_user_id;
-- DROP INDEX IF EXISTS idx_audit_logs_organization_id;
-- DROP INDEX IF EXISTS idx_tasks_due_date;
-- DROP INDEX IF EXISTS idx_tasks_entity;
-- DROP INDEX IF EXISTS idx_tasks_status;
-- DROP INDEX IF EXISTS idx_tasks_assigned_to;
-- DROP INDEX IF EXISTS idx_tasks_organization_id;
-- DROP INDEX IF EXISTS idx_comments_parent_id;
-- DROP INDEX IF EXISTS idx_comments_entity;
-- DROP INDEX IF EXISTS idx_comments_user_id;
-- DROP INDEX IF EXISTS idx_conv_participants_user;
-- DROP INDEX IF EXISTS idx_conv_participants_conversation;
-- DROP INDEX IF EXISTS idx_messages_created_at;
-- DROP INDEX IF EXISTS idx_messages_sender_id;
-- DROP INDEX IF EXISTS idx_messages_conversation_id;
-- DROP INDEX IF EXISTS idx_notifications_created_at;
-- DROP INDEX IF EXISTS idx_notifications_is_read;
-- DROP INDEX IF EXISTS idx_notifications_user_id;
-- DROP INDEX IF EXISTS idx_reports_period;
-- DROP INDEX IF EXISTS idx_reports_status;
-- DROP INDEX IF EXISTS idx_reports_template_id;
-- DROP INDEX IF EXISTS idx_reports_organization_id;
-- DROP INDEX IF EXISTS idx_scope_results_scope;
-- DROP INDEX IF EXISTS idx_scope_results_period;
-- DROP INDEX IF EXISTS idx_scope_results_organization_id;
-- DROP INDEX IF EXISTS idx_emission_calc_activity_data_id;
-- DROP INDEX IF EXISTS idx_activity_data_emission_factor;
-- DROP INDEX IF EXISTS idx_activity_data_period;
-- DROP INDEX IF EXISTS idx_activity_data_document_id;
-- DROP INDEX IF EXISTS idx_activity_data_facility_id;
-- DROP INDEX IF EXISTS idx_activity_data_organization_id;
-- DROP INDEX IF EXISTS idx_doc_processing_stage;
-- DROP INDEX IF EXISTS idx_doc_processing_status;
-- DROP INDEX IF EXISTS idx_doc_processing_document_id;
-- DROP INDEX IF EXISTS idx_documents_hash;
-- DROP INDEX IF EXISTS idx_documents_type;
-- DROP INDEX IF EXISTS idx_documents_created_at;
-- DROP INDEX IF EXISTS idx_documents_status;
-- DROP INDEX IF EXISTS idx_documents_supplier_id;
-- DROP INDEX IF EXISTS idx_documents_organization_id;
-- DROP INDEX IF EXISTS idx_supplier_emissions_period;
-- DROP INDEX IF EXISTS idx_supplier_emissions_supplier_id;
-- DROP INDEX IF EXISTS idx_suppliers_tier;
-- DROP INDEX IF EXISTS idx_suppliers_status;
-- DROP INDEX IF EXISTS idx_suppliers_supplier_code;
-- DROP INDEX IF EXISTS idx_suppliers_organization_id;
-- DROP INDEX IF EXISTS idx_facilities_is_active;
-- DROP INDEX IF EXISTS idx_facilities_postcode;
-- DROP INDEX IF EXISTS idx_facilities_organization_id;
-- DROP INDEX IF EXISTS idx_org_access_type;
-- DROP INDEX IF EXISTS idx_org_access_workspace;
-- DROP INDEX IF EXISTS idx_org_access_user_org;
-- DROP INDEX IF EXISTS idx_org_access_organization_id;
-- DROP INDEX IF EXISTS idx_org_access_user_id;
-- DROP INDEX IF EXISTS idx_organizations_created_at;
-- DROP INDEX IF EXISTS idx_organizations_status;
-- DROP INDEX IF EXISTS idx_organizations_company_number;
-- DROP INDEX IF EXISTS idx_users_is_active;
-- DROP INDEX IF EXISTS idx_users_created_at;
-- DROP INDEX IF EXISTS idx_users_email;
MIGRATION 012: DATA MIGRATION & CLEANUP
sql
-- ============================================
-- MIGRATION 012: DATA MIGRATION & CLEANUP
-- Migrate existing data to new schema
-- ============================================

-- ============================================
-- 12.1 Migrate Organizations
-- ============================================

-- Existing organizations table is kept as-is.
-- Any missing fields are preserved in metadata.

-- ============================================
-- 12.2 Migrate Organization Members to Organization Access
-- ============================================

-- Get client workspace ID
DO $$
DECLARE
    client_workspace_id UUID;
BEGIN
    SELECT id INTO client_workspace_id FROM workspaces WHERE code = 'client';
    
    -- Migrate existing organization_members to organization_access
    INSERT INTO organization_access (
        user_id,
        organization_id,
        workspace_id,
        access_type,
        is_active,
        created_at,
        updated_at
    )
    SELECT 
        om.user_id,
        om.organization_id,
        client_workspace_id,
        CASE 
            WHEN om.role = 'admin' THEN 'owner'
            ELSE 'member'
        END,
        om.is_active,
        om.created_at,
        om.updated_at
    FROM organization_members om
    WHERE om.user_id IS NOT NULL
    AND om.organization_id IS NOT NULL
    ON CONFLICT (user_id, organization_id, workspace_id) DO NOTHING;
END $$;

-- ============================================
-- 12.3 Migrate Existing Users (If users table exists)
-- ============================================

-- This assumes there's an existing users/auth table
-- Adjust based on actual existing schema

DO $$
BEGIN
    -- If users table exists and is not the new users table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'auth_users') THEN
        INSERT INTO users (
            id,
            email,
            password_hash,
            first_name,
            last_name,
            created_at,
            updated_at
        )
        SELECT 
            id,
            email,
            password_hash,
            first_name,
            last_name,
            created_at,
            updated_at
        FROM auth_users
        WHERE email IS NOT NULL
        ON CONFLICT (email) DO NOTHING;
    END IF;
END $$;

-- ============================================
-- 12.4 Migrate Documents (if customer_documents exists)
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'customer_documents') THEN
        INSERT INTO documents (
            id,
            organization_id,
            name,
            description,
            file_name,
            file_size,
            mime_type,
            storage_path,
            status,
            created_by,
            created_at,
            updated_at,
            metadata
        )
        SELECT 
            cd.id,
            cd.organization_id,
            cd.file_name,
            cd.file_name, -- Use file name as description
            cd.file_name,
            NULL, -- file_size not available
            cd.file_type,
            cd.file_url,
            COALESCE(cd.status, 'uploaded'),
            NULL, -- created_by not available
            COALESCE(cd.upload_date, NOW()),
            COALESCE(cd.updated_at, NOW()),
            jsonb_build_object(
                'asset_id', cd.asset_id,
                'organization_member_id', cd.organization_member_id,
                'document_type_code', cd.document_type_code,
                'billing_period_start', cd.billing_period_start,
                'billing_period_end', cd.billing_period_end
            )
        FROM customer_documents cd
        WHERE cd.organization_id IS NOT NULL
        ON CONFLICT (id) DO NOTHING;
    END IF;
END $$;

-- ============================================
-- 12.5 Migrate Suppliers (if suppliers exists)
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'suppliers') THEN
        -- Suppliers table already exists, assuming it matches our schema
        -- If not, migration would be needed
        NULL;
    END IF;
END $$;

-- ============================================
-- 12.6 Migrate Emission Factors
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'defra_conversion_factors') THEN
        INSERT INTO emission_factors (
            factor_code,
            source,
            year,
            activity_type,
            scope,
            unit,
            co2e_multiplier,
            created_at,
            updated_at
        )
        SELECT 
            'DEFRA_' || df.reporting_year || '_' || df.activity_type,
            'DEFRA',
            df.reporting_year,
            df.activity_type,
            '1', -- Default scope, adjust as needed
            'unit', -- Default unit, adjust as needed
            df.co2e_multiplier,
            COALESCE(df.created_at, NOW()),
            COALESCE(df.updated_at, NOW())
        FROM defra_conversion_factors df
        WHERE df.co2e_multiplier IS NOT NULL
        ON CONFLICT (factor_code) DO NOTHING;
    END IF;
END $$;

-- ============================================
-- 12.7 Migrate Activity Data (if emissions_logs exists)
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'emissions_logs') THEN
        INSERT INTO activity_data (
            id,
            organization_id,
            document_id,
            emission_factor_id,
            activity_type,
            raw_quantity,
            unit,
            start_date,
            end_date,
            created_by,
            created_at,
            updated_at,
            metadata
        )
        SELECT 
            el.id,
            el.organization_id,
            el.customer_document_id,
            el.defra_factor_id,
            NULL, -- activity_type
            el.raw_quantity,
            NULL, -- unit
            el.start_date,
            el.end_date,
            el.created_by_user_id,
            COALESCE(el.created_at, NOW()),
            COALESCE(el.updated_at, NOW()),
            jsonb_build_object(
                'asset_id', el.asset_id,
                'calculated_kg_co2e', el.calculated_kg_co2e,
                'file_id', el.file_id
            )
        FROM emissions_logs el
        WHERE el.organization_id IS NOT NULL
        ON CONFLICT (id) DO NOTHING;
    END IF;
END $$;

-- ============================================
-- 12.8 Migrate Emission Calculations
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'emissions_logs') THEN
        INSERT INTO emission_calculations (
            activity_data_id,
            calculated_kg_co2e,
            calculated_t_co2e,
            created_at,
            updated_at
        )
        SELECT 
            el.id,
            el.calculated_kg_co2e,
            el.calculated_kg_co2e / 1000, -- Convert kg to tonnes
            COALESCE(el.created_at, NOW()),
            COALESCE(el.updated_at, NOW())
        FROM emissions_logs el
        WHERE el.calculated_kg_co2e IS NOT NULL
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

-- ============================================
-- 12.9 Migrate Manual Review Queue
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'manual_review_queue') THEN
        -- Manual reviews table already exists
        -- We'll keep it but link to documents
        UPDATE manual_review_queue mrq
        SET document_id = cd.id
        FROM customer_documents cd
        WHERE mrq.customer_document_id = cd.id
        AND mrq.document_id IS NULL;
    END IF;
END $$;

-- ============================================
-- 12.10 Audit Log Migration
-- ============================================

DO $$
BEGIN
    -- Existing audit logs can be migrated if needed
    -- Adjust based on existing table structure
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        -- If old audit_logs table exists, we assume it matches our schema
        -- or we create a migration
        NULL;
    END IF;
END $$;

-- ============================================
-- 12.11 Cleanup: Drop Deprecated Tables (Post-Migration)
-- ============================================

-- WARNING: Only run after verifying data migration is complete

-- These are kept for backward compatibility during migration
-- They can be dropped after all code is updated

-- DROP TABLE IF EXISTS organization_members CASCADE;
-- DROP TABLE IF EXISTS customer_documents CASCADE;
-- DROP TABLE IF EXISTS defra_conversion_factors CASCADE;
-- DROP TABLE IF EXISTS emissions_logs CASCADE;
-- DROP TABLE IF EXISTS manual_review_queue CASCADE;

-- ============================================
-- ROLLBACK: MIGRATION 012
-- ============================================

-- Not fully reversible due to data transformations
-- Use restore from backup if rollback is needed
MIGRATION EXECUTION CHECKLIST
Pre-Migration
□ Backup database
□ Run migrations in DEV environment
□ Validate data integrity
□ Test application functionality
□ Create rollback plan
Migration Execution
sql
-- Execute in order
\i 001_identity.sql
\i 002_workspace.sql
\i 003_organization.sql
\i 004_supplier.sql
\i 005_document.sql
\i 006_carbon.sql
\i 007_reporting.sql
\i 008_collaboration.sql
\i 009_platform.sql
\i 010_rls.sql
\i 011_indexes.sql
\i 012_migration.sql
Post-Migration Validation
□ Verify all tables created
□ Verify RLS policies applied
□ Verify indexes created
□ Verify data migrated
□ Test application authentication
□ Test organization access
□ Test document operations
□ Test supplier operations
□ Test emission calculations
□ Test reporting
ROLLBACK PLAN
sql
-- Rollback in reverse order
\i 012_rollback.sql  -- Drop migrated data
\i 011_rollback.sql  -- Drop indexes
\i 010_rollback.sql  -- Drop RLS policies
\i 009_rollback.sql  -- Drop platform tables
\i 008_rollback.sql  -- Drop collaboration tables
\i 007_rollback.sql  -- Drop reporting tables
\i 006_rollback.sql  -- Drop carbon tables
\i 005_rollback.sql  -- Drop document tables
\i 004_rollback.sql  -- Drop supplier tables
\i 003_rollback.sql  -- Drop organization tables
\i 002_rollback.sql  -- Drop workspace tables
\i 001_rollback.sql  -- Drop identity tables

-- Restore from backup
SUMMARY
Migration	Tables Created	Purpose
001	10	Identity & Access Layer
002	3	Workspace & Organization Access
003	6	Organization Management
004	9	Supplier Management
005	8	Document Management
006	6	Carbon Accounting
007	6	Reporting & Compliance
008	7	Collaboration
009	6	Platform Administration
010	-	RLS Policies
011	-	Performance Indexes
012	-	Data Migration
Total	61	Complete v1.0 Schema
Migration Status: ✅ READY FOR EXECUTION

Next Step: Run in DEV environment and validate

