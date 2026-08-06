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