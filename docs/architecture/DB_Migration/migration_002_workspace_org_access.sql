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