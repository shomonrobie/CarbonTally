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