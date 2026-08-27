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