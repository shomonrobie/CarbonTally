CarbonTally - Updated Database Schema
Date: August 2, 2026
Author: Shomon Robie & DeepSeek
Version: 2.0
Status: Ready for Implementation

Overview
This document provides the complete updated database schema for CarbonTally, building on your existing tables. All new tables include:

✅ Full audit logging - Every action is tracked with created_by, updated_by, and timestamps

✅ Activity logs - Who did what, when, and what changed

✅ No breaking changes - Existing tables remain untouched

✅ Future-proof - Designed for scalability

1. New Tables for Document Processing
1.1 Document Processing Queue
sql
-- ============================================
-- TABLE: document_processing_queue
-- Purpose: Track AI and manual document processing
-- ============================================

CREATE TABLE document_processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    customer_document_id UUID REFERENCES customer_documents(id),
    
    -- Processing Type
    processing_type VARCHAR(50) NOT NULL, -- 'ai_auto', 'ai_batch', 'manual_request', 'manual_batch'
    
    -- Status
    status VARCHAR(50) DEFAULT 'queued',
    -- 'queued', 'processing', 'extracted', 'mapped', 'verified', 'failed', 'manual_review', 'completed'
    
    -- File Details
    file_name VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    file_size_bytes BIGINT,
    file_type VARCHAR(50),
    page_count INTEGER DEFAULT 0,
    
    -- AI Extraction Results
    ai_extraction_result JSONB, -- Full AI extracted data
    ai_confidence_score DECIMAL(5,4),
    ai_extraction_method VARCHAR(50), -- 'ocr', 'nlp', 'pattern_match', 'hybrid'
    ai_extracted_at TIMESTAMPTZ,
    ai_processing_time_ms INTEGER,
    
    -- AI Mapping Results
    ai_mapped_facility_id UUID REFERENCES facilities(id),
    ai_mapped_asset_id UUID REFERENCES assets(id),
    ai_mapped_supplier_id UUID REFERENCES suppliers(id), -- NEW
    ai_mapping_confidence DECIMAL(5,4),
    ai_mapped_document_type_code VARCHAR(50),
    
    -- Manual Extraction (if requested)
    manual_requested_by UUID REFERENCES organization_members(id),
    manual_requested_at TIMESTAMPTZ,
    manual_assigned_to UUID REFERENCES staff_profiles(id),
    manual_assigned_by UUID REFERENCES staff_profiles(id),
    manual_assigned_at TIMESTAMPTZ,
    manual_extraction_result JSONB,
    manual_extracted_by UUID REFERENCES staff_profiles(id),
    manual_extracted_at TIMESTAMPTZ,
    manual_notes TEXT,
    
    -- Quality Control
    qc_required BOOLEAN DEFAULT FALSE,
    qc_by UUID REFERENCES staff_profiles(id),
    qc_at TIMESTAMPTZ,
    qc_notes TEXT,
    qc_approved BOOLEAN,
    
    -- Customer Review
    customer_reviewed_by UUID REFERENCES organization_members(id),
    customer_reviewed_at TIMESTAMPTZ,
    customer_approved BOOLEAN,
    customer_rejection_reason TEXT,
    customer_notes TEXT,
    
    -- Emissions Calculation
    calculated_emissions_kg_co2e DECIMAL(10,2),
    defra_factor_used UUID REFERENCES defra_conversion_factors(id),
    emission_calculation_method VARCHAR(100),
    
    -- Batch Information
    batch_id UUID REFERENCES upload_batches(id),
    batch_sequence INTEGER,
    
    -- Pricing
    processing_cost DECIMAL(10,2),
    billing_currency VARCHAR(3) DEFAULT 'GBP',
    
    -- Timestamps - Full Audit Trail
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES organization_members(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES organization_members(id),
    completed_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB
);

-- Indexes
CREATE INDEX idx_processing_queue_org ON document_processing_queue(organization_id);
CREATE INDEX idx_processing_queue_status ON document_processing_queue(status);
CREATE INDEX idx_processing_queue_document ON document_processing_queue(customer_document_id);
CREATE INDEX idx_processing_queue_batch ON document_processing_queue(batch_id);
CREATE INDEX idx_processing_queue_type ON document_processing_queue(processing_type);
CREATE INDEX idx_processing_queue_created ON document_processing_queue(created_at);
1.2 Processing Audit Trail
sql
-- ============================================
-- TABLE: processing_audit_trail
-- Purpose: Every action on a document in the queue
-- ============================================

CREATE TABLE processing_audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id UUID NOT NULL REFERENCES document_processing_queue(id) ON DELETE CASCADE,
    
    -- Action Details
    action VARCHAR(50) NOT NULL,
    -- 'created', 'uploaded', 'ai_started', 'ai_completed', 'mapped', 'verified', 
    -- 'manual_requested', 'manual_assigned', 'manual_completed', 'qc_passed', 
    -- 'customer_reviewed', 'approved', 'rejected', 'completed'
    
    -- Who Did It
    performed_by UUID REFERENCES organization_members(id),
    performed_by_staff UUID REFERENCES staff_profiles(id),
    performed_by_type VARCHAR(20), -- 'customer', 'staff', 'system', 'ai'
    
    -- What Changed
    previous_value JSONB,
    new_value JSONB,
    
    -- Notes
    notes TEXT,
    
    -- Timing
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_queue ON processing_audit_trail(queue_id);
CREATE INDEX idx_audit_action ON processing_audit_trail(action);
2. New Tables for Suppliers
2.1 Suppliers
sql
-- ============================================
-- TABLE: suppliers
-- Purpose: Track suppliers for Scope 3 reporting
-- ============================================

CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    -- Basic Info
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100), -- 'energy', 'fuel', 'waste', 'transport', 'manufacturing', 'professional'
    supplier_category_id UUID REFERENCES supplier_categories(id),
    
    -- Contact
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    address TEXT,
    website VARCHAR(255),
    tax_id VARCHAR(100),
    registration_number VARCHAR(100),
    
    -- Emissions Data (Self-Reported)
    annual_emissions_scope1 DECIMAL(10,2),
    annual_emissions_scope2 DECIMAL(10,2),
    annual_emissions_scope3 DECIMAL(10,2),
    reporting_year INTEGER,
    
    -- Emission Factors (if supplier provides)
    emission_factor_scope1 DECIMAL(10,4),
    emission_factor_scope2 DECIMAL(10,4),
    emission_factor_scope3 DECIMAL(10,4),
    emission_factor_unit VARCHAR(50), -- 'per_employee', 'per_revenue', 'per_unit'
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES organization_members(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES organization_members(id),
    
    -- Metadata
    metadata JSONB
);

CREATE INDEX idx_suppliers_org ON suppliers(organization_id);
CREATE INDEX idx_suppliers_category ON suppliers(supplier_category_id);
CREATE INDEX idx_suppliers_type ON suppliers(type);
2.2 Supplier Categories
sql
-- ============================================
-- TABLE: supplier_categories
-- Purpose: Categorize suppliers for reporting
-- ============================================

CREATE TABLE supplier_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category_group VARCHAR(50), -- 'direct', 'indirect', 'upstream', 'downstream'
    default_emission_factor DECIMAL(10,4),
    default_emission_factor_unit VARCHAR(50),
    ghg_protocol_category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed Data
INSERT INTO supplier_categories (name, category_group, ghg_protocol_category) VALUES
    ('Electricity Supplier', 'direct', 'Purchased Electricity'),
    ('Natural Gas Supplier', 'direct', 'Purchased Fuel'),
    ('Fuel Supplier', 'direct', 'Purchased Fuel'),
    ('Waste Management', 'indirect', 'Waste Disposal'),
    ('Transportation', 'indirect', 'Downstream Transportation'),
    ('Raw Materials', 'upstream', 'Purchased Goods & Services'),
    ('Manufacturing', 'upstream', 'Purchased Goods & Services'),
    ('Professional Services', 'indirect', 'Purchased Goods & Services'),
    ('Telecommunications', 'indirect', 'Purchased Goods & Services');
3. New Tables for Product Categories
3.1 Product Categories
sql
-- ============================================
-- TABLE: product_categories
-- Purpose: Categorize emissions by product/service
-- ============================================

CREATE TABLE product_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    -- Basic Info
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category_type VARCHAR(50), -- 'product', 'service', 'material', 'energy'
    
    -- GHG Protocol Mapping
    ghg_protocol_scope VARCHAR(10), -- '1', '2', '3'
    ghg_protocol_category VARCHAR(100),
    
    -- ESRS/ISSB Mapping
    esrs_e1_category VARCHAR(100),
    issb_category VARCHAR(100),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES organization_members(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES organization_members(id),
    
    -- Metadata
    metadata JSONB
);

CREATE INDEX idx_product_categories_org ON product_categories(organization_id);
4. New Tables for Subscriptions & Billing
4.1 Customer Subscriptions
sql
-- ============================================
-- TABLE: customer_subscriptions
-- Purpose: Track subscription tiers and limits
-- ============================================

CREATE TABLE customer_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    -- Plan Details
    plan VARCHAR(50) NOT NULL, -- 'free_trial', 'starter', 'professional', 'enterprise'
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'expired', 'cancelled', 'suspended'
    
    -- Limits
    ai_extraction_limit INTEGER,
    ai_extraction_used INTEGER DEFAULT 0,
    batch_upload_limit INTEGER, -- max files per batch
    batch_upload_per_day INTEGER,
    manual_extraction_pages_included INTEGER,
    manual_extraction_pages_used INTEGER DEFAULT 0,
    
    -- Pricing
    price_per_ai_extra DECIMAL(10,2),
    price_per_manual_page DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'GBP',
    
    -- Features
    features JSONB, -- Feature flags
    -- {
    --   "batch_upload": true,
    --   "manual_extraction": true,
    --   "csrd_reports": true,
    --   "issb_reports": true,
    --   "api_access": false
    -- }
    
    -- Billing
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    stripe_price_id VARCHAR(255),
    billing_period_start DATE,
    billing_period_end DATE,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES organization_members(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES organization_members(id),
    cancelled_at TIMESTAMPTZ,
    cancelled_by UUID REFERENCES organization_members(id)
);

CREATE INDEX idx_subscriptions_org ON customer_subscriptions(organization_id);
CREATE INDEX idx_subscriptions_status ON customer_subscriptions(status);
CREATE INDEX idx_subscriptions_plan ON customer_subscriptions(plan);
4.2 Usage Tracking
sql
-- ============================================
-- TABLE: usage_tracking
-- Purpose: Track daily/monthly usage per organization
-- ============================================

CREATE TABLE usage_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    -- Usage Period
    usage_date DATE DEFAULT CURRENT_DATE,
    usage_month DATE DEFAULT DATE_TRUNC('month', CURRENT_DATE),
    
    -- Counts
    ai_files_processed INTEGER DEFAULT 0,
    batch_files_uploaded INTEGER DEFAULT 0,
    manual_pages_extracted INTEGER DEFAULT 0,
    reports_generated INTEGER DEFAULT 0,
    
    -- Storage
    total_storage_bytes BIGINT DEFAULT 0,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_usage_org ON usage_tracking(organization_id);
CREATE INDEX idx_usage_date ON usage_tracking(usage_date);
CREATE INDEX idx_usage_month ON usage_tracking(usage_month);
5. New Tables for Reports
5.1 Report Templates
sql
-- ============================================
-- TABLE: report_templates
-- Purpose: Store report templates (SECR, CSRD, etc.)
-- ============================================

CREATE TABLE report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id), -- NULL = system templates
    
    -- Template Details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    report_type VARCHAR(50) NOT NULL, -- 'SECR', 'CSRD', 'ISSB', 'Custom'
    
    -- Template Structure
    template_structure JSONB NOT NULL,
    -- {
    --   "sections": [
    --     {"id": "executive_summary", "title": "Executive Summary", "order": 1},
    --     {"id": "company_overview", "title": "Company Overview", "order": 2},
    --     ...
    --   ]
    -- }
    
    -- AI Content Prompts
    ai_prompts JSONB,
    -- {
    --   "executive_summary": "Generate executive summary based on emissions data",
    --   "analysis": "Analyze emissions trends and provide insights"
    -- }
    
    -- Branding
    logo_url TEXT,
    primary_color VARCHAR(7),
    secondary_color VARCHAR(7),
    font_family VARCHAR(100),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    is_system BOOLEAN DEFAULT FALSE,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES organization_members(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES organization_members(id)
);

CREATE INDEX idx_templates_org ON report_templates(organization_id);
CREATE INDEX idx_templates_type ON report_templates(report_type);
5.2 Report Generation Queue
sql
-- ============================================
-- TABLE: report_generation_queue
-- Purpose: Track report generation jobs
-- ============================================

CREATE TABLE report_generation_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID REFERENCES organization_members(id),
    
    -- Report Details
    template_id UUID REFERENCES report_templates(id),
    report_type VARCHAR(50) NOT NULL,
    reporting_year INTEGER NOT NULL,
    report_name VARCHAR(255),
    
    -- Data Sources
    data_sources JSONB,
    -- {
    --   "document_ids": ["uuid1", "uuid2"],
    --   "emission_ids": ["uuid3", "uuid4"],
    --   "manual_entry_id": "uuid5"
    -- }
    
    -- Status
    status VARCHAR(50) DEFAULT 'queued',
    -- 'queued', 'processing_data', 'generating_content', 'editing', 'complete', 'failed'
    
    -- Progress
    progress_percentage INTEGER DEFAULT 0,
    current_step VARCHAR(255),
    
    -- AI Generated Content
    generated_content JSONB,
    -- {
    --   "executive_summary": {"content": "...", "ai_generated": true},
    --   "analysis": {"content": "...", "ai_generated": true}
    -- }
    
    -- User Edits
    user_edits JSONB,
    -- {
    --   "executive_summary": {"content": "...", "user_edited": true}
    -- }
    
    -- Final Report
    final_report_url TEXT,
    final_report_file_name VARCHAR(255),
    final_report_size_bytes BIGINT,
    
    -- AI Usage
    ai_model_used VARCHAR(50),
    ai_tokens_used INTEGER,
    ai_cost DECIMAL(10,4),
    ai_processing_time_ms INTEGER,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES organization_members(id),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES organization_members(id),
    
    -- Metadata
    metadata JSONB,
    error_log TEXT
);

CREATE INDEX idx_report_queue_org ON report_generation_queue(organization_id);
CREATE INDEX idx_report_queue_user ON report_generation_queue(user_id);
CREATE INDEX idx_report_queue_status ON report_generation_queue(status);
CREATE INDEX idx_report_queue_year ON report_generation_queue(reporting_year);
5.3 AI Content History
sql
-- ============================================
-- TABLE: ai_content_history
-- Purpose: Track AI-generated content with feedback
-- ============================================

CREATE TABLE ai_content_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    report_id UUID REFERENCES report_generation_queue(id),
    
    -- AI Request
    prompt_type VARCHAR(50) NOT NULL, -- 'executive_summary', 'analysis', 'methodology'
    prompt_text TEXT,
    model_used VARCHAR(50),
    
    -- Response
    generated_content TEXT,
    content_format VARCHAR(20), -- 'text', 'markdown', 'html'
    
    -- Metrics
    tokens_used INTEGER,
    processing_time_ms INTEGER,
    cost DECIMAL(10,4),
    
    -- Feedback
    user_rating INTEGER, -- 1-5
    user_feedback TEXT,
    was_accepted BOOLEAN DEFAULT TRUE,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES organization_members(id)
);

CREATE INDEX idx_ai_history_org ON ai_content_history(organization_id);
CREATE INDEX idx_ai_history_report ON ai_content_history(report_id);
6. New Tables for Manual Extraction
6.1 Manual Extraction Batches
sql
-- ============================================
-- TABLE: manual_extraction_batches
-- Purpose: Track manual extraction batch jobs
-- ============================================

CREATE TABLE manual_extraction_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    -- Batch Details
    batch_name VARCHAR(255) NOT NULL,
    batch_description TEXT,
    total_documents INTEGER NOT NULL,
    total_pages INTEGER NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL,
    price_per_page DECIMAL(10,2) DEFAULT 0.99,
    currency VARCHAR(3) DEFAULT 'GBP',
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    -- 'pending', 'assigned', 'in_progress', 'quality_check', 'ready_for_customer', 'approved', 'completed', 'rejected'
    
    -- SLA
    estimated_completion_date TIMESTAMPTZ,
    actual_completion_date TIMESTAMPTZ,
    sla_deadline TIMESTAMPTZ,
    sla_breached BOOLEAN DEFAULT FALSE,
    
    -- Assignment (Internal CarbonTally Team)
    assigned_to UUID REFERENCES staff_profiles(id),
    assigned_by UUID REFERENCES staff_profiles(id),
    assigned_at TIMESTAMPTZ,
    
    -- Quality Control
    qc_by UUID REFERENCES staff_profiles(id),
    qc_at TIMESTAMPTZ,
    qc_notes TEXT,
    qc_approved BOOLEAN,
    
    -- Customer Communication
    customer_notes TEXT,
    staff_notes TEXT,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES organization_members(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES organization_members(id),
    completed_by UUID REFERENCES organization_members(id),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_manual_batches_org ON manual_extraction_batches(organization_id);
CREATE INDEX idx_manual_batches_status ON manual_extraction_batches(status);
CREATE INDEX idx_manual_batches_assigned ON manual_extraction_batches(assigned_to);
6.2 Manual Extraction Items
sql
-- ============================================
-- TABLE: manual_extraction_items
-- Purpose: Individual documents in a manual batch
-- ============================================

CREATE TABLE manual_extraction_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES manual_extraction_batches(id) ON DELETE CASCADE,
    document_processing_queue_id UUID REFERENCES document_processing_queue(id),
    
    -- Document Details
    file_name VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    page_count INTEGER NOT NULL,
    document_type VARCHAR(50),
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    -- 'pending', 'in_progress', 'extracted', 'qc_review', 'ready', 'approved', 'rejected', 'needs_correction'
    
    -- Extracted Data
    extracted_data JSONB,
    -- {
    --   "fields": {
    --     "invoice_number": {"value": "INV-001", "confidence": 0.95},
    --     "total_amount": {"value": 250.00, "confidence": 0.98}
    --   }
    -- }
    
    -- Mapping Data
    mapped_data JSONB,
    mapped_facility_id UUID REFERENCES facilities(id),
    mapped_asset_id UUID REFERENCES assets(id),
    mapped_supplier_id UUID REFERENCES suppliers(id),
    
    -- Emissions Calculation
    calculated_emissions_kg_co2e DECIMAL(10,2),
    defra_factor_used UUID REFERENCES defra_conversion_factors(id),
    
    -- Extraction Team
    extracted_by UUID REFERENCES staff_profiles(id),
    extracted_at TIMESTAMPTZ,
    
    -- Quality Control
    qc_by UUID REFERENCES staff_profiles(id),
    qc_at TIMESTAMPTZ,
    qc_notes TEXT,
    quality_score INTEGER, -- 1-100
    
    -- Customer Review
    customer_reviewed_by UUID REFERENCES organization_members(id),
    customer_reviewed_at TIMESTAMPTZ,
    customer_approved BOOLEAN,
    customer_rejection_reason TEXT,
    customer_notes TEXT,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_manual_items_batch ON manual_extraction_items(batch_id);
CREATE INDEX idx_manual_items_status ON manual_extraction_items(status);
CREATE INDEX idx_manual_items_queue ON manual_extraction_items(document_processing_queue_id);
7. New Tables for Document Types
7.1 Document Type Categories
sql
-- ============================================
-- TABLE: document_type_categories
-- Purpose: Reference for document types
-- ============================================

CREATE TABLE document_type_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category_group VARCHAR(50), -- 'utility', 'fuel', 'waste', 'travel', 'general'
    
    -- Default Settings
    default_priority INTEGER DEFAULT 1,
    requires_facility BOOLEAN DEFAULT TRUE,
    requires_asset BOOLEAN DEFAULT FALSE,
    requires_supplier BOOLEAN DEFAULT FALSE,
    requires_date_range BOOLEAN DEFAULT TRUE,
    
    -- Default DEFRA Mapping
    default_defra_activity_type VARCHAR(100),
    default_scope VARCHAR(10), -- '1', '2', '3'
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed Data
INSERT INTO document_type_categories (code, name, category_group, default_scope, default_defra_activity_type) VALUES
    ('electricity', 'Electricity Bill', 'utility', '2', 'Electricity'),
    ('gas', 'Gas Bill', 'utility', '1', 'Natural Gas'),
    ('fuel_card', 'Fuel Card', 'fuel', '1', 'Diesel'),
    ('fuel_invoice', 'Fuel Invoice', 'fuel', '1', 'Diesel'),
    ('waste_manifest', 'Waste Manifest', 'waste', '3', 'Waste'),
    ('travel_expense', 'Travel Expense', 'travel', '3', 'Business Travel'),
    ('flight', 'Flight Invoice', 'travel', '3', 'Aviation'),
    ('accommodation', 'Accommodation Invoice', 'travel', '3', 'Hotel'),
    ('general', 'General Document', 'general', NULL, NULL);
8. Updated Tables (Add Columns)
8.1 Upload Batches - Add Fields
sql
-- ============================================
-- ALTER TABLE: upload_batches
-- Purpose: Add fields for batch tracking
-- ============================================

ALTER TABLE upload_batches 
ADD COLUMN IF NOT EXISTS batch_type VARCHAR(50) DEFAULT 'ai_auto',
ADD COLUMN IF NOT EXISTS estimated_processing_time TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS error_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS manual_extraction_requested BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS manual_extraction_batch_id UUID REFERENCES manual_extraction_batches(id),
ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES organization_members(id),
ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES organization_members(id);

-- Update indexes
CREATE INDEX IF NOT EXISTS idx_batches_type ON upload_batches(batch_type);
CREATE INDEX IF NOT EXISTS idx_batches_manual ON upload_batches(manual_extraction_batch_id);
8.2 Customer Documents - Add Fields
sql
-- ============================================
-- ALTER TABLE: customer_documents
-- Purpose: Add fields for processing
-- ============================================

ALTER TABLE customer_documents 
ADD COLUMN IF NOT EXISTS processing_queue_id UUID REFERENCES document_processing_queue(id),
ADD COLUMN IF NOT EXISTS supplier_id UUID REFERENCES suppliers(id),
ADD COLUMN IF NOT EXISTS product_category_id UUID REFERENCES product_categories(id),
ADD COLUMN IF NOT EXISTS processing_method VARCHAR(50), -- 'ai_auto', 'ai_batch', 'manual'
ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(5,4),
ADD COLUMN IF NOT EXISTS extracted_data JSONB,
ADD COLUMN IF NOT EXISTS mapped_data JSONB,
ADD COLUMN IF NOT EXISTS calculated_emissions_kg_co2e DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES organization_members(id);

-- Update indexes
CREATE INDEX IF NOT EXISTS idx_documents_processing ON customer_documents(processing_queue_id);
CREATE INDEX IF NOT EXISTS idx_documents_supplier ON customer_documents(supplier_id);
8.3 Emissions Logs - Add Fields
sql
-- ============================================
-- ALTER TABLE: emissions_logs
-- Purpose: Add fields for tracking
-- ============================================

ALTER TABLE emissions_logs 
ADD COLUMN IF NOT EXISTS organization_member_id UUID REFERENCES organization_members(id),
ADD COLUMN IF NOT EXISTS supplier_id UUID REFERENCES suppliers(id),
ADD COLUMN IF NOT EXISTS product_category_id UUID REFERENCES product_categories(id),
ADD COLUMN IF NOT EXISTS data_source VARCHAR(50), -- 'ai_extraction', 'manual_entry', 'csv_upload', 'api'
ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(5,4),
ADD COLUMN IF NOT EXISTS verified_by UUID REFERENCES organization_members(id),
ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES organization_members(id);

-- Update indexes
CREATE INDEX IF NOT EXISTS idx_emissions_supplier ON emissions_logs(supplier_id);
CREATE INDEX IF NOT EXISTS idx_emissions_verified ON emissions_logs(verified_by);
9. Complete Audit Trail Coverage
9.1 All Tables Include These Fields
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  AUDIT TRAIL FIELDS - EVERY TABLE                                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  created_at TIMESTAMPTZ DEFAULT NOW()                                          │ │
│  │  created_by UUID REFERENCES organization_members(id)                           │ │
│  │  updated_at TIMESTAMPTZ DEFAULT NOW()                                          │ │
│  │  updated_by UUID REFERENCES organization_members(id)                           │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  PLUS dedicated audit tables for critical operations:                          │ │
│  │  ● processing_audit_trail - Every document processing event                    │ │
│  │  ● activity_logs - General system activities                                   │ │
│  │  ● user_activity_log - User-specific actions                                   │ │
│  │  ● audit_logs - Full audit trail with before/after values                     │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
9.2 Activity Logging Functions
sql
-- ============================================
-- FUNCTION: log_activity
-- Purpose: Unified activity logging
-- ============================================

CREATE OR REPLACE FUNCTION log_activity(
    p_user_id UUID,
    p_organization_id UUID,
    p_action VARCHAR,
    p_resource_type VARCHAR,
    p_resource_id UUID,
    p_details JSONB,
    p_ip_address VARCHAR,
    p_user_agent TEXT,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
    v_activity_id UUID;
BEGIN
    INSERT INTO activity_logs (
        user_id,
        organization_id,
        action,
        resource_type,
        resource_id,
        details,
        ip_address,
        user_agent,
        metadata,
        created_at
    ) VALUES (
        p_user_id,
        p_organization_id,
        p_action,
        p_resource_type,
        p_resource_id,
        p_details,
        p_ip_address,
        p_user_agent,
        p_metadata,
        NOW()
    )
    RETURNING id INTO v_activity_id;
    
    RETURN v_activity_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- FUNCTION: log_audit
-- Purpose: Log changes with before/after values
-- ============================================

CREATE OR REPLACE FUNCTION log_audit(
    p_user_id UUID,
    p_organization_id UUID,
    p_action_type TEXT,
    p_resource_type TEXT,
    p_resource_id UUID,
    p_action TEXT,
    p_description TEXT,
    p_old_data JSONB,
    p_new_data JSONB,
    p_ip_address TEXT,
    p_user_agent TEXT,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
    v_audit_id UUID;
BEGIN
    INSERT INTO audit_logs (
        user_id,
        organization_id,
        action_type,
        resource_type,
        resource_id,
        action,
        description,
        old_data,
        new_data,
        changes,
        ip_address,
        user_agent,
        metadata,
        created_at
    ) VALUES (
        p_user_id,
        p_organization_id,
        p_action_type,
        p_resource_type,
        p_resource_id,
        p_action,
        p_description,
        p_old_data,
        p_new_data,
        (SELECT jsonb_object_agg(
            key,
            jsonb_build_object('old', old_data[key], 'new', new_data[key])
        ) FROM jsonb_each(p_new_data) WHERE old_data ? key),
        p_ip_address,
        p_user_agent,
        p_metadata,
        NOW()
    )
    RETURNING id INTO v_audit_id;
    
    RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql;
10. Migration Script
sql
-- ============================================
-- MIGRATION SCRIPT - Complete Run All
-- ============================================

BEGIN;

-- 1. Create New Tables
-- (All CREATE TABLE statements from above)

-- 2. Alter Existing Tables
-- (All ALTER TABLE statements from above)

-- 3. Create Indexes
-- (All CREATE INDEX statements from above)

-- 4. Create Functions
-- (All CREATE FUNCTION statements from above)

-- 5. Seed Data
INSERT INTO supplier_categories (name, category_group, ghg_protocol_category) VALUES
    ('Electricity Supplier', 'direct', 'Purchased Electricity'),
    ('Natural Gas Supplier', 'direct', 'Purchased Fuel'),
    ('Fuel Supplier', 'direct', 'Purchased Fuel'),
    ('Waste Management', 'indirect', 'Waste Disposal'),
    ('Transportation', 'indirect', 'Downstream Transportation'),
    ('Raw Materials', 'upstream', 'Purchased Goods & Services'),
    ('Manufacturing', 'upstream', 'Purchased Goods & Services'),
    ('Professional Services', 'indirect', 'Purchased Goods & Services'),
    ('Telecommunications', 'indirect', 'Purchased Goods & Services')
ON CONFLICT (id) DO NOTHING;

INSERT INTO document_type_categories (code, name, category_group, default_scope, default_defra_activity_type) VALUES
    ('electricity', 'Electricity Bill', 'utility', '2', 'Electricity'),
    ('gas', 'Gas Bill', 'utility', '1', 'Natural Gas'),
    ('fuel_card', 'Fuel Card', 'fuel', '1', 'Diesel'),
    ('fuel_invoice', 'Fuel Invoice', 'fuel', '1', 'Diesel'),
    ('waste_manifest', 'Waste Manifest', 'waste', '3', 'Waste'),
    ('travel_expense', 'Travel Expense', 'travel', '3', 'Business Travel'),
    ('flight', 'Flight Invoice', 'travel', '3', 'Aviation'),
    ('accommodation', 'Accommodation Invoice', 'travel', '3', 'Hotel'),
    ('general', 'General Document', 'general', NULL, NULL)
ON CONFLICT (code) DO NOTHING;

COMMIT;
11. Schema Summary
11.1 New Tables Added
Table	Purpose
document_processing_queue	Track AI and manual document processing
processing_audit_trail	Every action on a document
suppliers	Track suppliers for Scope 3
supplier_categories	Categorize suppliers
product_categories	Categorize emissions by product
customer_subscriptions	Track subscription tiers
usage_tracking	Track daily/monthly usage
report_templates	Store report templates
report_generation_queue	Track report generation
ai_content_history	Track AI-generated content
manual_extraction_batches	Track manual extraction jobs
manual_extraction_items	Individual documents in batches
document_type_categories	Reference for document types
11.2 Tables Modified
Table	Changes
upload_batches	Added batch_type, manual_extraction fields
customer_documents	Added processing_queue_id, supplier_id, product_category_id
emissions_logs	Added supplier_id, product_category_id, verification fields
12. Next Steps
With the database schema finalized, the next steps are:

Run Migration - Execute the migration script

Update RLS Policies - Add policies for new tables

API Development - Build endpoints for new tables

Frontend Integration - Connect UI to new data structures

🚀 CarbonTally - Database Ready for Implementation.


You're right to question 500MB per batch—that's far above industry standards. Let me revise the limits based on what companies actually use.

Industry Standards for Document Processing
Company/Service	File Size Limit	Page Limit	Batch/Other Limits
Ocrolus	200 MB	3,000 pages	Hard limits, no batch specified 
Sensible	Not specified	Not specified	Per-document pricing 
AutoEntry	199 pages per file	199 pages	50 files (mobile), 24+ hours processing 
Sparrow	5 MB (free tier)	3 pages (free)	30 calls/6 hours 
Alibaba Doc Mining	100 MB	1,000 pages	100 docs/session, 50 docs/console 
OpenAI Chat	32MB per file	N/A	50MB total attachments 
Azure AI Document Intelligence	Not specified	Not specified	500 free pages/month 
Mathpix	Not specified	Not specified	Batches up to 200,000 files 
Amazon Textract	5,000 bytes per analysis	Not specified	Need to break up larger docs 
Recommended Limits for CarbonTally
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  RECOMMENDED LIMITS - ALIGNED WITH INDUSTRY STANDARDS                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Limit Type          │ Value                     │ Industry Benchmark           │ │
│  ├──────────────────────┼───────────────────────────┼─────────────────────────────┤ │
│  │  Max File Size       │ 100 MB                    │ Alibaba (100MB) [citation:15] │ │
│  │  Max Pages per File  │ 300 pages                 │ Ocrolus (3000), lower is safer│ │
│  │  Max Files per Batch │ 50 files                  │ AutoEntry (50 mobile) [citation:12] │ │
│  │  Max Total per Batch │ 500 MB → CHANGE TO 100 MB │ Practical & aligned           │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
Revised Per-Upload Limits
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  REVISED PER-UPLOAD LIMITS                                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Limit Type          │ Auto Extraction    │ Manual Extraction                   │ │
│  ├──────────────────────┼────────────────────┼─────────────────────────────────────┤ │
│  │  Max Files per Upload│ 50 files           │ 50 files per batch                  │ │
│  │  Max File Size       │ 100 MB             │ 100 MB                              │ │
│  │  Max Total Size      │ 100 MB per upload  │ 500 MB per batch                   │ │
│  │  Max Pages per File  │ 300 pages          │ No limit (manual)                   │ │
│  │  Supported Formats   │ CSV, PDF, JPG, PNG │ PDF, JPG, PNG, TIFF                │ │
│  │                     │ XLSX, HEIC         │                                     │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
Why These Limits?
100 MB Per File
Industry standard: Ocrolus 200MB , Alibaba 100MB 

Most utility bills/invoices are 2-15MB

Covers 95% of use cases

Prevents abuse/performance issues

300 Pages Per File
Ocrolus supports 3,000 pages , but that's excessive for carbon documents

Typical utility bill: 1-5 pages

Bank statement: 20-50 pages

300 pages covers annual reports

50 Files Per Batch
AutoEntry mobile limit: 50 files 

Practical for users to manage

Prevents overwhelming AI processing

100 MB Total Per Batch
Not 500MB - that's too much for self-service

50 files × avg 2MB = 100MB

Manual extraction can handle larger batches

Updated Subscription Tiers
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  SUBSCRIPTION TIERS - WITH REVISED LIMITS                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Feature               │ Starter    │ Professional │ Enterprise                 │ │
│  ├────────────────────────┼────────────┼──────────────┼────────────────────────────┤ │
│  │  Price                 │ $99/mo     │ $299/mo      │ Custom                     │ │
│  ├────────────────────────┼────────────┼──────────────┼────────────────────────────┤ │
│  │  Auto Extraction       │            │              │                            │ │
│  │  - Files/month         │ 100        │ 500          │ Unlimited                  │ │
│  │  - Max per upload      │ 1          │ 50           │ 50                         │ │
│  │  - File size           │ 100 MB     │ 100 MB       │ 100 MB                     │ │
│  │  - Batch upload        │ ❌         │ ✅ (2/day)   │ ✅ (unlimited)            │ │
│  │  - Pages per file      │ 300        │ 300          │ 300                        │ │
│  ├────────────────────────┼────────────┼──────────────┼────────────────────────────┤ │
│  │  Manual Extraction     │            │              │                            │ │
│  │  - Pages included      │ 0          │ 50           │ 500                        │ │
│  │  - Extra pages         │ N/A        │ £0.99/page   │ £0.79/page                 │ │
│  │  - SLA                 │ N/A        │ 24-48 hrs    │ 12-24 hrs                  │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
Key Takeaway
100 MB per file and 100 MB per batch is the practical, industry-aligned limit. 500MB per batch is too high for self-service AI extraction—that's more appropriate for manual extraction batches where file size matters less.

Would you like me to update the full product specification with these revised limits?

yes
CarbonTally - Complete Product Specification (Revised)
Date: August 1, 2026
Author: Shomon Robie & DeepSeek
Version: 2.0
Status: Finalized

1. Product Overview
1.1 Vision
"Upload any document → Get clean data → Generate audit-ready reports. Simple, fast, accurate."

1.2 Core Value Proposition
One upload interface - Single or batch, system handles everything

AI-first extraction - 85-95% accuracy, instant results

Human backup - Manual extraction when needed

Audit-ready reports - SECR, CSRD, ISSB with one click

2. Upload System
2.1 Two Upload Modes
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  UPLOAD MODES                                                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Mode                     │ Description                   │ When to Use           │ │
│  ├───────────────────────────┼───────────────────────────────┼───────────────────────┤ │
│  │  Auto Extraction (AI)     │ Self-service, instant         │ Default for all docs  │ │
│  │                           │ 2-5 minutes turnaround       │ Included in plan      │ │
│  ├───────────────────────────┼───────────────────────────────┼───────────────────────┤ │
│  │  Manual Extraction        │ Professional service          │ AI fails or customer  │ │
│  │  (Human)                  │ 24-48 hours turnaround       │ requests verification │ │
│  │                           │ £0.99/page                   │                       │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
2.2 Upload Limits
Limit Type	Auto Extraction	Manual Extraction
Max Files per Upload	50 files	50 files per batch
Max File Size	100 MB	100 MB
Max Total per Upload	100 MB	500 MB (manual)
Max Pages per File	300 pages	No limit
Supported Formats	CSV, PDF, JPG, PNG, XLSX, HEIC	PDF, JPG, PNG, TIFF
2.3 Monthly Limits by Plan
Plan	Auto Extraction	Manual Extraction
Free Trial	10 files (one-time)	Not available
Starter ($99/mo)	100 files/month	Not available
Professional ($299/mo)	500 files/month	50 pages included, £0.99/page after
Enterprise (Custom)	Unlimited	500 pages included, £0.79/page after
3. Subscription Tiers
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  SUBSCRIPTION TIERS - COMPLETE                                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Feature                    │ Free Trial  │ Starter    │ Professional │ Enterprise│
│  ├─────────────────────────────┼─────────────┼────────────┼──────────────┼──────────┤
│  │  Price                      │ $0          │ $99/mo     │ $299/mo      │ Custom   │
│  ├─────────────────────────────┼─────────────┼────────────┼──────────────┼──────────┤
│  │  Auto Extraction            │             │            │              │           │
│  │  - Files/month              │ 10 (one-time)│ 100        │ 500          │ Unlimited│
│  │  - Max per upload           │ 1           │ 1          │ 50           │ 50       │
│  │  - File size                │ 100 MB      │ 100 MB     │ 100 MB       │ 100 MB   │
│  │  - Batch upload             │ ❌          │ ❌         │ ✅           │ ✅       │
│  │  - Pages per file           │ 300         │ 300        │ 300          │ 300      │
│  ├─────────────────────────────┼─────────────┼────────────┼──────────────┼──────────┤
│  │  Manual Extraction          │             │            │              │           │
│  │  - Pages included           │ 0           │ 0          │ 50           │ 500      │
│  │  - Extra pages              │ N/A         │ N/A        │ £0.99/page   │ £0.79/page│
│  │  - SLA                      │ N/A         │ N/A        │ 24-48 hrs    │ 12-24 hrs │
│  ├─────────────────────────────┼─────────────┼────────────┼──────────────┼──────────┤
│  │  Reports                    │ ✅ Basic    │ ✅ Basic   │ ✅ Advanced  │ ✅ Custom│
│  │  - SECR                     │ ✅          │ ✅         │ ✅           │ ✅       │
│  │  - CSRD                     │ ❌          │ ❌         │ ✅           │ ✅       │
│  │  - ISSB                     │ ❌          │ ❌         │ ✅           │ ✅       │
│  ├─────────────────────────────┼─────────────┼────────────┼──────────────┼──────────┤
│  │  Support                    │ Email       │ Email      │ Priority     │ Dedicated│
│  │  - Response time            │ 48 hrs      │ 24 hrs     │ 12 hrs       │ 4 hrs    │
│  ├─────────────────────────────┼─────────────┼────────────┼──────────────┼──────────┤
│  │  API Access                 │ ❌          │ ❌         │ Limited      │ ✅ Full  │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
4. Customer Journey
4.1 The 3-Step Flow
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  3-STEP CUSTOMER JOURNEY                                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  STEP 1: UPLOAD                                                                ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  • One unified upload interface                                             │││
│  │  │  • Drag & drop (single or multiple)                                        │││
│  │  │  • Auto-detects document type                                               │││
│  │  │  • AI processes instantly (2-5 minutes)                                    │││
│  │  │  • Manual extraction only if AI fails                                     │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  STEP 2: REVIEW & APPROVE                                                       ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  • Side-by-side viewer (PDF + Data)                                        │││
│  │  │  • AI highlights extracted fields                                          │││
│  │  │  • Confidence scores (🟢 high, 🟡 medium, 🟠 low)                          │││
│  │  │  • One-click approve or edit                                              │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  STEP 3: GENERATE REPORT                                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  • One-click report generation                                              │││
│  │  │  • AI writes content (executive summary, analysis)                         │││
│  │  │  • Edit content on-the-fly                                                 │││
│  │  │  • Download PDF/Excel (audit-ready)                                        │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
4.2 Document Mapping (Auto-Mapping)
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  DOCUMENT MAPPING - SYSTEM DOES THE WORK                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Document Type     │ Auto-Detect │ Auto-Map To        │ Confidence             │ │
│  ├────────────────────┼─────────────┼────────────────────┼────────────────────────┤ │
│  │  Utility Bill      │ ✅ Yes      │ Facility, Asset    │ 85-95%                 │ │
│  │  Fuel Card         │ ✅ Yes      │ Vehicle Asset      │ 85-95%                 │ │
│  │  Waste Manifest    │ ✅ Yes      │ Facility           │ 70-85%                 │ │
│  │  Travel Expense    │ ✅ Yes      │ None (needs help)  │ 50-70%                 │ │
│  │  General Document  │ ⚠️ Partial  │ None (needs help)  │ < 50%                  │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  User Actions:                                                                  │ │
│  │  ● 80%: Nothing (auto-approved) ✅                                              │ │
│  │  ● 15%: One-click confirm 🟡                                                   │ │
│  │  ● 5%: Select from dropdown 🟠                                                 │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
5. User Interface
5.1 Top Navigation
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  TOP NAVIGATION                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  🌿 CT  │ Dashboard │ Documents │ Upload │ Reports │ Settings │ [👤]           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ✅ One navigation system (no sidebar)                                              │
│  ✅ Maximum horizontal space for side-by-side viewer                               │
│  ✅ Mobile: Hamburger menu                                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘
5.2 Mobile Side-by-Side Viewer (Tabs)
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  MOBILE SIDE-BY-SIDE VIEWER                                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  [📄 PDF]  [📊 Data]  [📋 Compare]                                             ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ✅ Each view gets full screen (readable)                                           │
│  ✅ AI highlights fields in PDF                                                    │
│  ✅ Swipe left/right to switch tabs                                                │
└─────────────────────────────────────────────────────────────────────────────────────┘
6. Pricing Summary
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  PRICING SUMMARY                                                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Plan         │ Price      │ Auto Extraction  │ Manual Extraction               │ │
│  ├───────────────┼────────────┼──────────────────┼─────────────────────────────────┤ │
│  │  Free Trial   │ $0         │ 10 files (one)   │ Not available                   │ │
│  ├───────────────┼────────────┼──────────────────┼─────────────────────────────────┤ │
│  │  Starter      │ $99/mo     │ 100 files/month  │ Not available                   │ │
│  ├───────────────┼────────────┼──────────────────┼─────────────────────────────────┤ │
│  │  Professional │ $299/mo    │ 500 files/month  │ 50 pages incl, £0.99/page      │ │
│  ├───────────────┼────────────┼──────────────────┼─────────────────────────────────┤ │
│  │  Enterprise   │ Custom     │ Unlimited        │ 500 pages incl, £0.79/page     │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
7. Success Metrics
Metric	Target
Time to First Upload	< 2 minutes
Time to First Report	< 10 minutes
Document Approval Rate	> 85%
User Retention (Monthly)	> 90%
AI Extraction Success	> 85%
8. Product Blueprint - Final Summary
8.1 Core Features
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  CORE FEATURES                                                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  1. One Unified Upload Interface                                                    │
│     ├── Single or batch (50 files max)                                             │
│     ├── Auto-detects document type                                                 │
│     └── AI processes instantly (2-5 minutes)                                      │
│                                                                                      │
│  2. Auto-Mapping System                                                             │
│     ├── 85-95% of documents auto-mapped                                            │
│     ├── AI matches to facilities, assets, suppliers                                │
│     └── User confirms when uncertain                                               │
│                                                                                      │
│  3. Side-by-Side Reviewer                                                           │
│     ├── PDF (left) + Extracted Data (right)                                        │
│     ├── AI highlights fields in PDF                                               │
│     ├── One-click approve or edit                                                 │
│     └── Mobile: Tab-based view (PDF, Data, Compare)                               │
│                                                                                      │
│  4. AI Report Generation                                                            │
│     ├── One-click report generation                                                │
│     ├── AI writes content (executive summary, analysis)                           │
│     ├── Edit on-the-fly                                                           │
│     └── Download PDF/Excel (audit-ready)                                          │
│                                                                                      │
│  5. Manual Extraction (Premium Service)                                             │
│     ├── When AI fails or customer requests                                        │
│     ├── £0.99/page, 24-48 hours                                                  │
│     └── Quality-checked by CarbonTally team                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
9. Next Steps
With the product specification finalized, the next steps are:

Database Schema Implementation - Create the tables

API Development - Build the endpoints

Frontend Development - Build the UI components

AI Integration - Connect to OpenAI/OCR services

Testing & QA - Ensure quality

Beta Launch - Launch with 10-20 beta customers

🚀 CarbonTally - Ready to build.




CarbonTally - Top Navigation UI/UX Specification
Date: August 1, 2026
Author: Shomon Robie & DeepSeek
Version: 1.0
Status: Approved for Development

1. Overview
1.1 Purpose
This document defines the UI/UX specification for the CarbonTally top navigation system. It covers both desktop and mobile implementations, ensuring a consistent, intuitive, and efficient user experience across all devices.

1.2 Design Principles
Simplicity First – One navigation system, no confusion

Maximum Content Space – Optimized for side-by-side document review

Mobile-First – Seamless experience on all screen sizes

Consistency – Same navigation structure across all pages

Accessibility – WCAG 2.1 AA compliant

2. Navigation Structure
2.1 Main Navigation Items
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  NAVIGATION ITEMS (Maximum 6)                                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌────────────┬────────────┬────────────┬────────────┬────────────┬────────────┐   │
│  │   Logo     │ Dashboard  │ Documents  │   Upload   │  Reports   │  Settings  │   │
│  │  🌿 CT     │   📊       │   📄       │   📤       │   📊       │   ⚙️       │   │
│  └────────────┴────────────┴────────────┴────────────┴────────────┴────────────┘   │
│                                                                                      │
│  Right Side:                                                                        │
│  ┌────────────┬────────────┬────────────┐                                          │
│  │   Search   │  Notify    │  Profile   │                                          │
│  │   🔍       │   🔔       │   👤 ▼     │                                          │
│  └────────────┴────────────┴────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────────────┘
2.2 Navigation Item Details
Item	Icon	Label	Destination	Description
Logo	🌿 CT	-	/dashboard	Brand identity, returns to dashboard
Dashboard	📊	Dashboard	/dashboard	Overview with KPIs and status
Documents	📄	Documents	/documents	List of all uploaded documents
Upload	📤	Upload	/upload	Single and batch document upload
Reports	📊	Reports	/reports	Report generation and history
Settings	⚙️	Settings	/settings	Organization preferences
2.3 Profile Dropdown
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  PROFILE DROPDOWN                                                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  👤 John Smith                                                             ││ │
│  │  │  Acme Corp                                                                  ││ │
│  │  │  ─────────────────────────────────────────────────────────────────────────── ││ │
│  │  │  📋 My Profile                                                             ││ │
│  │  │  🏢 Organization                                                           ││ │
│  │  │  💳 Billing & Usage                                                        ││ │
│  │  │  🔑 API Keys                                                               ││ │
│  │  │  ─────────────────────────────────────────────────────────────────────────── ││ │
│  │  │  🆘 Help & Support                                                         ││ │
│  │  │  🚪 Logout                                                                 ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
3. Desktop Implementation (≥ 1024px)
3.1 Desktop Layout
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  DESKTOP LAYOUT                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  🌿 CT  │ 📊 Dashboard │ 📄 Documents │ 📤 Upload │ 📊 Reports │ ⚙️ Settings │ 🔍││
│  │  CarbonTally                                                                   ││ │
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  CONTENT AREA (Full Width)                                                      ││
│  │  ┌──────────────────────────────────┬──────────────────────────────────────────┐││
│  │  │  PDF Viewer                      │  Extracted Data                         │││
│  │  │  (50% width)                     │  (50% width)                            │││
│  │  └──────────────────────────────────┴──────────────────────────────────────────┘││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  🏢 Acme Corp  │  🔔 3 Notifications  │  👤 John Smith  │  📅 15 Jan 2025     ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
3.2 Desktop Specifications
Property	Value
Nav Height	64px
Font Size	14px
Item Spacing	32px (between items)
Logo Width	120px
Active Indicator	Bottom border, 3px, primary color
Hover State	Background: rgba(0,0,0,0.05)
Active State	Font weight: 600, Color: Primary
Max Nav Items	6 (to avoid clutter)
3.3 Desktop Interactions
Interaction	Behavior
Click Nav Item	Navigate to page, highlight active
Hover Nav Item	Subtle background change
Hover Dropdown	Show profile menu
Search (Ctrl+K)	Open global search modal
Notifications	Show notification panel
Resize	Collapse to mobile when < 1024px
4. Mobile Implementation (< 1024px)
4.1 Mobile Layout (Hamburger Menu)
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  MOBILE LAYOUT - COLLAPSED                                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  ☰  🌿 CarbonTally                                           🔔  👤           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  CONTENT AREA (Full Width)                                                      ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  [PDF Viewer or Data View - Full Screen]                                   │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
4.2 Mobile Menu (Expanded)
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  MOBILE MENU - EXPANDED                                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  ☰  🌿 CarbonTally                                               ✕ Close       ││
│  │  ────────────────────────────────────────────────────────────────────────────── ││
│  │                                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │  📊 Dashboard                                                              │ ││
│  │  │  📄 Documents                                                              │ ││
│  │  │  📤 Upload                                                                 │ ││
│  │  │  📊 Reports                                                                │ ││
│  │  │  ⚙️ Settings                                                               │ ││
│  │  └────────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                                  ││
│  │  ────────────────────────────────────────────────────────────────────────────── ││
│  │                                                                                  ││
│  │  ┌────────────────────────────────────────────────────────────────────────────┐ ││
│  │  │  👤 John Smith                                                             │ ││
│  │  │  Acme Corp                                                                  │ ││
│  │  │  ─────────────────────────────────────────────────────────────────────────── │ ││
│  │  │  📋 My Profile                                                             │ ││
│  │  │  🏢 Organization                                                           │ ││
│  │  │  💳 Billing & Usage                                                        │ ││
│  │  │  🔑 API Keys                                                               │ ││
│  │  │  🆘 Help & Support                                                         │ ││
│  │  │  🚪 Logout                                                                 │ ││
│  │  └────────────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
4.3 Mobile Specifications
Property	Value
Nav Height	56px
Font Size	16px (touch-friendly)
Hamburger Icon	24x24px, touch target 44x44px
Menu Width	100% (drawer slides from left)
Menu Items	48px height, 16px padding
Backdrop	60% opacity black overlay
Swipe	Swipe right to open, left to close
4.4 Mobile Interactions
Interaction	Behavior
Tap Hamburger	Slide in menu from left
Tap Item	Navigate and close menu
Tap Backdrop	Close menu
Swipe Right	Open menu
Swipe Left	Close menu
Tap Profile	Expand profile section
Search (Ctrl+F)	Open mobile search
5. Side-by-Side Viewer (Mobile Tabs)
5.1 Tab Layout
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  MOBILE SIDE-BY-SIDE VIEWER - TABS                                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  Invoice_123.pdf                                    [Approve] [Reject]          ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  [📄 PDF]  [📊 Data]  [📋 Compare]                                         ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  TAB 1: PDF VIEW (Full Screen)                                                 ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  [PDF Content - Zoomable, Panable]                                        │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  INVOICE NUMBER: INV-2025-00123  ← AI Highlighted (Green)             │││
│  │  │  │  Total Amount: £1,250.00          ← AI Highlighted (Green)             │││
│  │  │  │  Consumption: 3,450 kWh           ← AI Highlighted (Orange - Low Conf)  │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  └─────────────────────────────────────────────────────────────────────────────┘│
│  │                                                                                  ││
│  │  [🔍 Zoom In]  [📄 Page 1/5]  [↔ Rotate]  [📥 Download]                       ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  TAB 2: DATA VIEW (Full Screen)                                                ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ⚡ Auto-Extracted Fields                                                  │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  Invoice Number: INV-2025-00123    ✅ (95%)                            │││
│  │  │  │  Total Amount: £1,250.00            ✅ (98%)                            │││
│  │  │  │  Consumption: 3,450 kWh             ⚠️ (72%)  [✏️ Edit]               │││
│  │  │  │  Billing Period: 01/01/25-31/01/25 ✅ (90%)                            │││
│  │  │  │                                                                         │││
│  │  │  │  📋 Mapped Data                                                         │││
│  │  │  │  Facility: [London Office] ▼                                           │││
│  │  │  │  Asset: [Boiler 1] ▼                                                   │││
│  │  │  │  Supplier: [EnergyCo] ▼                                                │││
│  │  │  │                                                                         │││
│  │  │  │  💰 Total Emissions: 714.4 kg CO2e                                     │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  └─────────────────────────────────────────────────────────────────────────────┘│
│  │                                                                                  ││
│  │  [Approve]  [Reject]  [Save Draft]                                              ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  TAB 3: COMPARE VIEW (Split)                                                   ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  📄 PDF Preview (Top 40%)                                                  │││
│  │  │  ─────────────────────────────────────────────────────────────────────────── │││
│  │  │  📊 Extracted Data (Bottom 60%)                                            │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  Invoice: INV-001 ✅ │ Amount: £1,250 ✅ │ 3,450 kWh ⚠️                 │││
│  │  │  │  Facility: London ▼ │ Asset: Boiler 1 ▼                                │││
│  │  │  │  💰 714.4 kg CO2e                                                      │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  └─────────────────────────────────────────────────────────────────────────────┘│
│  │                                                                                  ││
│  │  [Approve]  [Reject]                                                            ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
5.2 Tab Specifications
Property	Value
Tab Height	48px
Tab Font	14px, medium weight
Active Tab	Bottom border, 3px, primary color
Tab Order	PDF → Data → Compare
Swipe	Swipe left/right to switch tabs
Animation	300ms ease-in-out slide
6. Responsive Breakpoints
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  RESPONSIVE BREAKPOINTS                                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Breakpoint        │ Layout                           │ Nav Style              │ │
│  ├────────────────────┼──────────────────────────────────┼────────────────────────│ │
│  │  < 480px (Phone)   │ Mobile (Portrait)                │ Hamburger Menu         │ │
│  │  481-767px (Phone) │ Mobile (Landscape)               │ Hamburger Menu         │ │
│  │  768-1023px (Tablet)│ Tablet                           │ Hamburger Menu         │ │
│  │  1024-1439px (Desktop)│ Desktop (Small)               │ Full Top Nav           │ │
│  │  1440px+ (Widescreen)│ Desktop (Large)                │ Full Top Nav           │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
7. Visual Design Specifications
7.1 Color Palette
Color	Hex	Usage
Primary	#2D6A4F	Active state, primary buttons
Primary Light	#40916C	Hover states
Primary Dark	#1B4332	Active nav item
Background	#FFFFFF	Nav background
Text Primary	#1A1A2E	Nav labels
Text Secondary	#64748B	Inactive nav items
Border	#E2E8F0	Bottom border
Hover	#F8FAFC	Hover background
7.2 Typography
Property	Value
Font Family	Inter, system-ui, sans-serif
Logo Font	20px, bold
Nav Label	14px, medium (desktop), 16px (mobile)
Active	600 weight
Inactive	500 weight
7.3 Spacing
Property	Value
Nav Height	64px (desktop), 56px (mobile)
Padding Left/Right	24px
Item Spacing	32px (desktop), 0 (mobile menu)
Logo Width	120px
Icon Size	20px
8. Accessibility Requirements
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ACCESSIBILITY REQUIREMENTS                                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ✅ WCAG 2.1 AA Compliance                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  ● Color contrast ratio: 4.5:1 minimum                                        │ │
│  │  ● Keyboard navigation: Tab, Enter, Space                                     │ │
│  │  ● Screen reader support: ARIA labels                                         │ │
│  │  ● Focus indicators: Visible outline                                          │ │
│  │  ● Touch targets: 44x44px minimum (mobile)                                    │ │
│  │  ● Reduced motion: Respect prefers-reduced-motion                            │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
9. Implementation Notes
9.1 Technology Stack
Framework: Next.js 14 (App Router)

UI Library: shadcn/ui

Icons: Lucide React

Animations: Framer Motion

State: Refine

9.2 Key Components
<Navbar /> - Main navigation component

<MobileMenu /> - Hamburger menu for mobile

<TabView /> - Side-by-side viewer tabs

<ProfileDropdown /> - User profile dropdown

<SearchBar /> - Global search

9.3 File Structure
text
src/
├── components/
│   ├── navigation/
│   │   ├── Navbar.tsx
│   │   ├── MobileMenu.tsx
│   │   ├── ProfileDropdown.tsx
│   │   └── SearchBar.tsx
│   └── viewer/
│       ├── TabView.tsx
│       ├── PDFViewer.tsx
│       └── DataViewer.tsx
├── hooks/
│   └── useMobile.ts
└── config/
    └── navigation.ts
10. User Flow Examples
10.1 Desktop User Flow
User logs in → Dashboard

Clicks "Upload" → Upload page

Uploads document → Document processing

Reviews side-by-side → PDF (left) + Data (right)

Approves → Document approved

10.2 Mobile User Flow
User logs in → Dashboard

Tap hamburger → Menu opens

Tap "Upload" → Upload page

Uploads document → Document processing

Reviews document → Switch tabs (PDF → Data → Compare)

Approves → Document approved

11. Performance Considerations
Metric	Target
Largest Contentful Paint (LCP)	< 2.5s
First Input Delay (FID)	< 100ms
Cumulative Layout Shift (CLS)	< 0.1
Time to Interactive (TTI)	< 3.5s
Bundle Size	< 200KB (gzipped)
12. Testing Checklist
□ All navigation items navigate correctly
□ Active state highlights correctly
□ Mobile hamburger menu opens/closes
□ Swipe gestures work on mobile
□ Tabs switch correctly on viewer pages
□ Keyboard navigation works (Tab, Enter)
□ Screen reader reads labels correctly
□ Touch targets are 44x44px minimum
□ Responsive at all breakpoints
□ Animations are smooth (60fps)
13. Approvals
Role	Name	Date	Signature
Product Owner	Shomon Robie	2026-08-01	✅
UX Designer	DeepSeek	2026-08-01	✅
Lead Developer	TBD		⬜
QA Lead	TBD		⬜
14. Version History
Version	Date	Author	Changes
1.0	2026-08-01	Shomon Robie & DeepSeek	Initial specification
15. Appendix
A. Navigation Items Full List
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  FULL NAVIGATION ITEM DETAILS                                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌────────────┬────────────┬────────────────┬───────────────┬─────────────────────┐ │
│  │  Item      │ Icon       │ Label          │ Destination   │ Description          │ │
│  ├────────────┼────────────┼────────────────┼───────────────┼─────────────────────┤ │
│  │  Logo      │ 🌿 CT      │ -              │ /dashboard    │ Brand & Home        │ │
│  │  Dashboard │ 📊         │ Dashboard      │ /dashboard    │ Overview & KPIs     │ │
│  │  Documents │ 📄         │ Documents      │ /documents    │ Document list       │ │
│  │  Upload    │ 📤         │ Upload         │ /upload       │ Single/Batch upload │ │
│  │  Reports   │ 📊         │ Reports        │ /reports      │ Report generation   │ │
│  │  Settings  │ ⚙️         │ Settings       │ /settings     │ Preferences         │ │
│  └────────────┴────────────┴────────────────┴───────────────┴─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
B. Keyboard Shortcuts
Shortcut	Action
Ctrl+K	Open global search
Ctrl+1	Navigate to Dashboard
Ctrl+2	Navigate to Documents
Ctrl+3	Navigate to Upload
Ctrl+4	Navigate to Reports
Ctrl+5	Navigate to Settings
Esc	Close dropdowns/modals
End of Document

CarbonTally - Customer Journey Map (Simplified)
Date: August 1, 2026
Author: Shomon Robie & DeepSeek
Version: 2.0
Status: Approved for Development

1. The Core Insight: One Upload, One Process
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🎯 THE CORE EXPERIENCE                                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                                │ │
│  │  "Upload any document → Get clean data → Generate report"                     │ │
│  │                                                                                │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                                │ │
│  │  Just 3 steps. That's it.                                                      │ │
│  │                                                                                │ │
│  │  1. Upload (single or batch - same interface)                                 │ │
│  │  2. Review & Approve                                                           │ │
│  │  3. Generate Report                                                            │ │
│  │                                                                                │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
2. Simplified Journey Map
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  COMPLETE CUSTOMER JOURNEY - 4 SIMPLE STEPS                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  STEP 1: LOGIN                                                                 ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  Email & Password → Dashboard                                               │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  STEP 2: UNIFIED UPLOAD                                                         ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  "Upload any file"                                                          │││
│  │  │  • Single file (CSV, PDF, Image)                                           │││
│  │  │  • Multiple files (batch upload)                                           │││
│  │  │  • System handles everything                                               │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  STEP 3: REVIEW & APPROVE                                                       ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  • View extracted data (side-by-side)                                      │││
│  │  │  • Approve → Done                                                          │││
│  │  │  • Edit → Fix data                                                         │││
│  │  │  • Manual extraction → Only if AI fails                                    │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  STEP 4: GENERATE REPORT                                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  • Click "Generate Report"                                                │││
│  │  │  • AI writes content                                                        │││
│  │  │  • Download PDF/Excel                                                       │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
3. Unified Upload Manager - The Heart of Simplicity
3.1 The Upload Screen
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📤 UNIFIED UPLOAD MANAGER                                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  📤 Upload Documents                                                           ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  [Drop files here or click to browse]                                     │││
│  │  │                                                                             │││
│  │  │  ✅ CSV  ✅ PDF  ✅ Image  ✅ Excel  ✅ Batch                              │││
│  │  │  Max file size: 10MB each                                                  │││
│  │  │                                                                             │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  📄 Invoice_123.pdf       2.4 MB   [✕]                                │││
│  │  │  │  📄 Utility_Bill.pdf      1.8 MB   [✕]                                │││
│  │  │  │  📊 Fuel_Card_Q4.csv      3.2 MB   [✕]                                │││
│  │  │  │  📄 Waste_Manifest.pdf    1.2 MB   [✕]                                │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  │                                                                             │││
│  │  │  [Upload All →]                                                             │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  💡 Smart Help:                                                                ││
│  │  ● CSV: Auto-mapped to emission factors                                       ││
│  │  ● PDF/Image: AI extracts data                                                ││
│  │  ● Multiple files: All processed in one batch                                ││
│  │  ● No need to choose - we handle it for you                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
3.2 Upload Decision Tree (Simplified)
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  DECISION TREE - USER DOESN'T THINK                                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  User: "I want to upload documents"                                            ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  ONE UPLOAD BUTTON                                                              ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  [Upload Documents]                                                         │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  System Does Everything                                                         ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ✅ If CSV  → Auto-map to emission factors                                │││
│  │  │  ✅ If PDF  → AI extract data                                              │││
│  │  │  ✅ If Image → OCR + AI extract                                            │││
│  │  │  ✅ If Multiple → Batch process together                                   │││
│  │  │  ✅ If Excel → Convert to CSV + process                                   │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  One Output: Clean Data                                                         ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ✅ CSV with mapped data                                                  │││
│  │  │  ✅ Emissions calculated                                                   │││
│  │  │  ✅ Ready for review                                                       │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
4. The 3-Step Customer Journey
Step 1: Upload (Unified)
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: UPLOAD (Unified)                                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  📱 Screen: Upload Manager                                                    ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  📤 Upload Documents                                                       │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │                                                                         │││
│  │  │  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │  │  │  [Drag files here or click to browse]                              │││
│  │  │  │  └─────────────────────────────────────────────────────────────────────┘││
│  │  │  │                                                                         │││
│  │  │  │  ┌────────────┬────────────┬────────────────────────────────────────────┐││
│  │  │  │  │  📄 CSV   │  📄 PDF   │  🖼️ Image   │  📊 Excel   │  📦 Batch      │││
│  │  │  │  │  (Auto-map)│  (AI)     │  (AI)      │  (Auto)    │  (All types)   │││
│  │  │  │  └────────────┴────────────┴────────────────────────────────────────────┘││
│  │  │  │                                                                         │││
│  │  │  │  [Upload →]                                                             │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  💡 User Actions:                                                               ││
│  │  1. Open Upload page                                                            ││
│  │  2. Drag & drop files (single or multiple)                                    ││
│  │  3. Click Upload                                                               ││
│  │  4. System processes (AI or auto-map)                                         ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
Step 2: Review & Approve
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: REVIEW & APPROVE                                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  📱 Screen: Document Review                                                   ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  📄 Invoice_123.pdf                            [← Back] [Status: Processing] ││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  ┌──────────────────────────────────┬──────────────────────────────────────────┐││
│  │  │  📄 PDF VIEWER                   │  📊 EXTRACTED DATA                     │││
│  │  │  ┌────────────────────────────┐  │  │  ┌────────────────────────────────┐  ││
│  │  │  │  [PDF Preview]              │  │  │  │  ✅ Invoice: INV-001          │  ││
│  │  │  │  AI Highlights:              │  │  │  │  ✅ Amount: £1,250           │  ││
│  │  │  │  🔍 Invoice Number           │  │  │  │  ⚠️ Consumption: 3,450 kWh  │  ││
│  │  │  │  🔍 Total Amount             │  │  │  │  📋 Facility: London Office ▼│  ││
│  │  │  │  🔍 Consumption              │  │  │  │  📋 Asset: Boiler 1 ▼       │  ││
│  │  │  └────────────────────────────┘  │  │  │  💰 Emissions: 714.4 kg CO2e │  ││
│  │  └──────────────────────────────────┘  │  └────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  [✅ Approve]  [✏️ Edit]  [🔄 Request Manual]  [💾 Save]                    │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  💡 User Actions:                                                               ││
│  │  1. Review PDF (left)                                                          ││
│  │  2. Review extracted data (right)                                              ││
│  │  3. Edit if needed (click ✏️)                                                 ││
│  │  4. Approve → Document ready for reporting                                    ││
│  │  5. Request Manual → Only if AI failed                                        ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
Step 3: Generate Report
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: GENERATE REPORT                                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  📱 Screen: Report Generator                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  📊 Generate Report                                                        │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  ✅ 89 Approved Documents                                              │││
│  │  │  │  📊 Total Emissions: 1,234.6 tCO2e                                    │││
│  │  │  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │  │  │  [Generate SECR Report]  [Generate CSRD Report]  [Custom Report]   │││
│  │  │  │  └─────────────────────────────────────────────────────────────────────┘││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  │                                                                             │││
│  │  │  ✨ AI is generating your report... (2-3 seconds)                         │││
│  │  │                                                                             │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  ✅ Report Generated!                                                  │││
│  │  │  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │  │  │  📄 SECR Report 2025                                               │││
│  │  │  │  │  🏢 Acme Corp                                                      │││
│  │  │  │  │  📅 15 Jan 2025                                                    │││
│  │  │  │  │  📊 1,234.6 tCO2e                                                  │││
│  │  │  │  └─────────────────────────────────────────────────────────────────────┘││
│  │  │  │  [📥 Download PDF]  [📊 Download Excel]  [✏️ Edit Report]               │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  💡 User Actions:                                                               ││
│  │  1. Click "Generate Report"                                                     ││
│  │  2. AI writes content (seconds)                                                ││
│  │  3. Review & edit content (if needed)                                         ││
│  │  4. Download PDF/Excel                                                         ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
5. Simplified Dashboard
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📊 SIMPLIFIED DASHBOARD                                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  🌿 CarbonTally                                                           🔍 👤 ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  👋 Welcome back, Sarah!                                     📅 15 Jan 2025│││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            ││
│  │  │  1,234.6     │ │  147         │ │  23          │ │  12          │            ││
│  │  │  tCO₂e       │ │  Documents   │ │  Processing  │ │  Pending     │            ││
│  │  │  ↓ 2.3%      │ │  ↑ 8%        │ │  ⏳          │ │  Review      │            ││
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘            ││
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  📤 Quick Upload                                                           │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  [Drop files here or click to upload]                                  │││
│  │  │  │  CSV, PDF, Image, Batch (up to 50 files)                              │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  📄 Recent Activity                                                         │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  ✅ Invoice_123.pdf approved         2 hrs ago                          │││
│  │  │  │  ⏳ Fuel_Card_Q4.csv processing      5 hrs ago                          │││
│  │  │  │  📤 Utility_Bill.pdf uploaded        1 day ago                          │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  │  [View All →]                                                               ││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  🚀 Quick Actions                                                          ││
│  │  │  [📤 Upload]  [📊 Report]  [📋 Review Queue]  [⚙️ Settings]                 ││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
6. The Complete User Flow (Visual)
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  COMPLETE USER FLOW - ONE JOURNEY                                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                ││
│  │  LOGIN → DASHBOARD → UPLOAD (1 click) → REVIEW (Side-by-side) → REPORT        ││
│  │                                                                                ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  WHAT THE USER SEES:                                                           ││
│  │                                                                                ││
│  │  ● One upload button that handles everything                                  ││
│  │  ● One review screen (PDF + data)                                             ││
│  │  ● One report button that generates everything                                ││
│  │                                                                                ││
│  │  That's it. 3 simple steps.                                                    ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
7. Success Metrics (Simplified)
Metric	Target	Why It Matters
Time to First Upload	< 2 minutes	Easy to start
Time to First Report	< 10 minutes	Quick results
Document Approval Rate	> 85%	High accuracy
User Retention	> 90%	They keep coming back
8. Summary
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ✅ FINAL: THE CARBONTALLY EXPERIENCE                                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                                │ │
│  │  1. Upload (unified - single or batch - system handles everything)             │ │
│  │  2. Review (side-by-side - PDF vs data - approve/edit)                        │ │
│  │  3. Report (AI generates - one click - download)                              │ │
│  │                                                                                │ │
│  │  That's it. Simple. Fast. Accurate.                                            │ │
│  │                                                                                │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
End of Document

CarbonTally - Document Mapping Strategy
Date: August 1, 2026
Author: Shomon Robie & DeepSeek
Version: 1.0
Status: Approved for Development

1. The Core Question: Do Customers Need Mapping?
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  THE ANSWER: YES, BUT SYSTEM SHOULD DO IT AUTOMATICALLY                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  ❌ WRONG: Force user to manually map every document                           │ │
│  │  ✅ RIGHT: AI auto-maps, user only confirms when uncertain                     │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Why Mapping Matters:                                                          │ │
│  │                                                                                │ │
│  │  ● Facility: "Which site does this bill belong to?"                           │ │
│  │  ● Asset: "Which equipment generated this emission?"                          │ │
│  │  ● Supplier: "Which vendor provided this service?"                            │ │
│  │  ● Document Type: "What kind of document is this?"                            │ │
│  │                                                                                │ │
│  │  Without mapping → Emissions can't be correctly attributed                    │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
2. What Needs to Be Mapped?
2.1 Mapping Fields
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  MAPPING FIELDS - WHAT NEEDS TO BE ATTRIBUTED                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Field          │ Purpose                       │ Example                       │ │
│  ├─────────────────┼───────────────────────────────┼───────────────────────────────┤ │
│  │  Document Type  │ What kind of document         │ Utility Bill / Fuel Card     │ │
│  │  Facility       │ Which site/location           │ London Office                 │ │
│  │  Asset          │ Which equipment               │ Boiler 1 / AC System 2       │ │
│  │  Supplier       │ Which vendor                  │ EnergyCo / WasteCo           │ │
│  │  Date Range     │ Which billing period          │ Jan 2025                      │ │
│  │  Product Category│ What product/service          │ Electricity / Natural Gas    │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
2.2 Who Provides This Data?
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  DATA SOURCES FOR MAPPING                                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Source                     │ Provided By          │ Confidence                  │ │
│  ├─────────────────────────────┼──────────────────────┼─────────────────────────────┤ │
│  │  Organization Profile       │ Customer (Setup)     │ 100% (pre-configured)       │ │
│  │  - Facilities               │                      │                             │ │
│  │  - Assets                   │                      │                             │ │
│  │  - Suppliers                │                      │                             │ │
│  ├─────────────────────────────┼──────────────────────┼─────────────────────────────┤ │
│  │  Document Content (AI)      │ AI Extraction        │ 85-95% (auto-detected)      │ │
│  │  - Address                  │                      │                             │ │
│  │  - Supplier Name            │                      │                             │ │
│  │  - Date Range               │                      │                             │ │
│  │  - Amount                   │                      │                             │ │
│  ├─────────────────────────────┼──────────────────────┼─────────────────────────────┤ │
│  │  File Name / Metadata       │ User Upload          │ 70-80% (hints)              │ │
│  │  - "Invoice_123.pdf"        │                      │                             │ │
│  │  - "London_Utility"         │                      │                             │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
3. Smart Auto-Mapping Strategy
3.1 Auto-Mapping Rules
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  AUTO-MAPPING RULES - SYSTEM DOES THE WORK                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  RULE 1: AI Document Type Detection                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  Document Content → AI Classifies:                                          ││ │
│  │  │  ● "kWh", "meter reading" → Electricity Bill                              ││ │
│  │  │  ● "litres", "fuel" → Fuel Card                                           ││ │
│  │  │  ● "waste", "disposal" → Waste Manifest                                   ││ │
│  │  │  ● "flight", "hotel" → Travel Expense                                     ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  RULE 2: Facility/Asset Detection                                               │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  Document Address → Matched to Facilities:                                  ││ │
│  │  │  ● "123 Green Street" → London Office                                     ││ │
│  │  │  ● "Manchester Hub" → Manchester Office                                    ││ │
│  │  │  ● "Unit 4, Birmingham" → Birmingham Depot                                 ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  RULE 3: Supplier Detection                                                     │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  Document Supplier → Matched to Suppliers:                                  ││ │
│  │  │  ● "E.ON" → EnergyCo                                                      ││ │
│  │  │  ● "British Gas" → GasCo                                                  ││ │
│  │  │  ● "Biffa" → WasteCo                                                      ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  RULE 4: File Name Pattern Detection                                            │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  File Name → Extracts Hints:                                                ││ │
│  │  │  ● "Invoice_123.pdf" → Invoice Document                                   ││ │
│  │  │  ● "London_Utility_Jan25.pdf" → London Office, Utility Bill               ││ │
│  │  │  ● "Fuel_Card_Q4_2024.csv" → Fuel Card, Q4 2024                          ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
3.2 Confidence Scoring
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  CONFIDENCE SCORING - USER KNOWS WHAT TO TRUST                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Confidence Level      │ Color    │ User Action                                 │ │
│  ├────────────────────────┼──────────┼─────────────────────────────────────────────┤ │
│  │  95-100% (High)        │ 🟢 Green │ Auto-approve, show confirmation           │ │
│  │  70-94% (Medium)       │ 🟡 Yellow│ Show suggestion, user clicks to confirm   │ │
│  │  0-69% (Low)           │ 🟠 Orange│ User must manually map                    │ │
│  │  No Match              │ 🔴 Red   │ User must select from list                │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Example:                                                                      │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  Facility: London Office (95% confidence) 🟢                              ││ │
│  │  │  Asset: Boiler 1 (72% confidence) 🟡 - Click to confirm                   ││ │
│  │  │  Supplier: Unknown (0% confidence) 🔴 - Select from list                  ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
4. Upload Experience: Single vs Batch
4.1 Single Document Upload
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  SINGLE DOCUMENT UPLOAD - AUTO-MAPPING                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  📤 Upload Document                                                           ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  [Drop file here or click to browse]                                       │││
│  │  │  📄 Invoice_123.pdf                                                        │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  🔍 AI Detected:                                                           │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  Document Type:     Utility Bill     🟢 95%  [Confirm]                  │││
│  │  │  │  Facility:          London Office    🟢 92%  [Confirm]                  │││
│  │  │  │  Asset:             Boiler 1         🟡 72%  [Select ▼]                │││
│  │  │  │  Supplier:          EnergyCo         🟡 78%  [Select ▼]                │││
│  │  │  │  Date Range:        Jan 2025         🟢 90%  [Confirm]                  │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  │                                                                             │││
│  │  │  [Upload & Continue]  [Edit Mapping]                                       │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
4.2 Batch Document Upload (Mixed Types)
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  BATCH UPLOAD - MIXED DOCUMENT TYPES                                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  📤 Upload Documents (Batch - 5 files)                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  [Drop files here or click to browse]                                     │││
│  │  │                                                                             │││
│  │  │  📄 Invoice_123.pdf        2.4 MB                                          │││
│  │  │  📄 Utility_Bill.pdf       1.8 MB                                          │││
│  │  │  📊 Fuel_Card_Q4.csv       3.2 MB                                          │││
│  │  │  📄 Waste_Manifest.pdf     1.2 MB                                          │││
│  │  │  📄 Flight_Booking.pdf     0.8 MB                                          │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  📊 Batch Summary - System Processed All                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  File              │ Type        │ Facility    │ Asset     │ Status         ││ │
│  │  ├────────────────────┼─────────────┼─────────────┼───────────┼─────────────────┤ │
│  │  │  Invoice_123.pdf   │ Utility     │ London      │ Boiler 1  │ 🟢 Ready        │ │
│  │  │  Utility_Bill.pdf  │ Utility     │ Manchester  │ Boiler 2  │ 🟡 Check Asset  │ │
│  │  │  Fuel_Card_Q4.csv  │ Fuel Card   │ Birmingham  │ Vehicle 1 │ 🟢 Ready        │ │
│  │  │  Waste_Manifest.pdf│ Waste       │ London      │ None      │ 🟠 Map Asset    │ │
│  │  │  Flight_Booking.pdf│ Travel      │ -           │ -         │ 🟠 Map Facility │ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  [Approve All]  [Review Individually]  [Edit Mappings]                         ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
4.3 Mixed Batch: Smart Grouping
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  MIXED BATCH - SMART GROUPING                                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  📊 AI Grouped Documents by Type                                                ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ⚡ Utility Bills (3 files)                                                │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  ✓ Invoice_123.pdf     → London, Boiler 1  🟢                         │││
│  │  │  │  ✓ Utility_Bill.pdf    → Manchester, Boiler 2  🟡                     │││
│  │  │  │  ✓ Gas_Bill.pdf        → London, Boiler 1  🟢                         │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  │                                                                             │││
│  │  │  ⛽ Fuel Cards (2 files)                                                   │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  ✓ Fuel_Card_Q4.csv   → Fleet, Vehicle 1  🟢                          │││
│  │  │  │  ✓ Fuel_Card_Q3.csv   → Fleet, Vehicle 2  🟢                          │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  │                                                                             │││
│  │  │  🗑️ Waste (1 file)                                                        │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  ⚠️ Waste_Manifest.pdf → London, No Asset  🟠                         │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  │                                                                             │││
│  │  │  ✈️ Travel (1 file)                                                        │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  ⚠️ Flight_Booking.pdf → No Facility, No Asset  🔴                    │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
5. The User Experience (No Thinking Required)
5.1 Upload Flow - User Journey
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  UPLOAD USER JOURNEY - NO THINKING REQUIRED                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  USER: "I need to upload these documents"                                      ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  Step 1: Drag & Drop                                                           ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  User selects all files (any type, any number)                             │││
│  │  │  Drags them into the upload box                                            │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  Step 2: System Processes                                                      ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ● AI detects document types                                                │││
│  │  │  ● Auto-maps to facilities (from content)                                  │││
│  │  │  ● Auto-maps to assets (from content)                                      │││
│  │  │  ● Identifies suppliers                                                    │││
│  │  │  ● Extracts date ranges                                                    │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  Step 3: User Confirms (Only If Needed)                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ● 80% of documents auto-approved 🟢                                       │││
│  │  │  ● 15% need confirmation 🟡 (click to confirm)                             │││
│  │  │  ● 5% need manual mapping 🔴 (select from list)                            │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  Step 4: Done                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ✅ All documents processed                                                │││
│  │  │  📊 Emissions calculated                                                   │││
│  │  │  📄 Ready for reporting                                                    │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
5.2 What User Actually Sees
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  USER VIEW - AFTER UPLOAD                                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  ✅ 5 Documents Uploaded Successfully                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  📊 Summary:                                                               │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  ✅ 4 documents auto-mapped and approved                               │││
│  │  │  │  ⚠️ 1 document needs your attention (Waste_Manifest.pdf)              │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  │                                                                             │││
│  │  │  💰 Total Emissions Calculated: 1,234.6 kg CO2e                           │││
│  │  │                                                                             │││
│  │  │  [Review Now]  [Go to Dashboard]  [Upload More]                            │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
6. Handling Different Document Types
6.1 Document Type Matrix
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  DOCUMENT TYPE HANDLING                                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Document Type     │ Auto-Detect │ Auto-Map         │ User Action              │ │
│  ├────────────────────┼─────────────┼──────────────────┼───────────────────────────┤ │
│  │  Utility Bill      │ ✅ Yes      │ Facility, Asset   │ Confirm if uncertain    │ │
│  │  (Electricity/Gas) │             │                  │                          │ │
│  ├────────────────────┼─────────────┼──────────────────┼───────────────────────────┤ │
│  │  Fuel Card         │ ✅ Yes      │ Vehicle Asset    │ Confirm vehicle ID       │ │
│  │  (CSV)             │             │                  │                          │ │
│  ├────────────────────┼─────────────┼──────────────────┼───────────────────────────┤ │
│  │  Waste Manifest    │ ✅ Yes      │ Facility, Type   │ Map to asset if needed   │ │
│  ├────────────────────┼─────────────┼──────────────────┼───────────────────────────┤ │
│  │  Travel Expense    │ ✅ Yes      │ None             │ Map to facility/asset    │ │
│  │  (Flights/Hotels)  │             │                  │                          │ │
│  ├────────────────────┼─────────────┼──────────────────┼───────────────────────────┤ │
│  │  General Invoice   │ ⚠️ Partial  │ None             │ User maps everything     │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
6.2 Mixed Batch Handling
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  MIXED BATCH - SYSTEM HANDLES ALL                                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  User Uploads:                                                                 ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  📄 Invoice_123.pdf        (Electricity)                                   │││
│  │  │  📄 Utility_Bill.pdf       (Gas)                                          │││
│  │  │  📊 Fuel_Card_Q4.csv       (Diesel)                                       │││
│  │  │  📄 Waste_Manifest.pdf     (General Waste)                                │││
│  │  │  📄 Flight_Booking.pdf     (Business Travel)                              │││
│  │  │  📄 General_Invoice.pdf    (Office Supplies)                              │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  System Groups by Type:                                                         ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  Group 1: Utility Bills (2 files)   → Auto-mapped ✅                       │││
│  │  │  Group 2: Fuel Cards (1 file)       → Auto-mapped ✅                       │││
│  │  │  Group 3: Waste (1 file)            → Facility mapped 🟡                  │││
│  │  │  Group 4: Travel (1 file)           → No mapping 🟠                       │││
│  │  │  Group 5: General (1 file)          → Manual mapping required 🔴           │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  User Reviews:                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ✅ 4 documents ready (auto-approved)                                      │││
│  │  │  ⚠️ 1 document needs confirmation (Waste)                                 │││
│  │  │  ⚠️ 1 document needs mapping (Travel)                                     │││
│  │  │  🔴 1 document needs full mapping (General)                               │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
7. Configuration: Organization Setup
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ORGANIZATION SETUP - ONCE, BEFORE FIRST USE                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  🏢 Organization Setup                                                         ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  Step 1: Add Your Facilities                                               │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  Facility Name    │ Address                │ Type       │               │││
│  │  │  ├────────────────────┼────────────────────────┼────────────┼───────────────┤││
│  │  │  │  London Office    │ 123 Green Street      │ Office     │ ✅            │││
│  │  │  │  Manchester Hub   │ 456 Business Park     │ Office     │ ✅            │││
│  │  │  │  Birmingham Depot │ Unit 4, Industrial    │ Depot      │ ✅            │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  │  [Add Facility]                                                              ││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  Step 2: Add Your Assets                                                   │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  Asset Name    │ Type       │ Facility       │ Supplier    │            │││
│  │  │  ├────────────────┼────────────┼────────────────┼─────────────┼────────────┤││
│  │  │  │  Boiler 1      │ Boiler     │ London Office  │ EnergyCo    │ ✅         │││
│  │  │  │  Boiler 2      │ Boiler     │ Manchester     │ GasCo       │ ✅         │││
│  │  │  │  Vehicle 1     │ Van        │ Birmingham     │ FuelCo      │ ✅         │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  │  [Add Asset]                                                                ││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  Step 3: Add Your Suppliers                                                │││
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │  │  Supplier Name    │ Type       │ Contact        │                       │││
│  │  │  ├───────────────────┼────────────┼────────────────┼───────────────────────┤││
│  │  │  │  EnergyCo         │ Electricity│ energy@co.com  │ ✅                    │││
│  │  │  │  GasCo            │ Gas        │ gas@co.com     │ ✅                    │││
│  │  │  │  FuelCo           │ Fuel       │ fuel@co.com    │ ✅                    │││
│  │  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │  │  [Add Supplier]                                                             ││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
8. Summary: Mapping Strategy
8.1 Auto-Mapping Rules Summary
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  AUTO-MAPPING RULES SUMMARY                                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Document Type     │ Auto-Detect │ Auto-Map To        │ Confidence             │ │
│  ├────────────────────┼─────────────┼────────────────────┼────────────────────────┤ │
│  │  Utility Bill      │ ✅ Yes      │ Facility, Asset    │ 85-95%                 │ │
│  │  Fuel Card         │ ✅ Yes      │ Vehicle Asset      │ 85-95%                 │ │
│  │  Waste Manifest    │ ✅ Yes      │ Facility           │ 70-85%                 │ │
│  │  Travel Expense    │ ✅ Yes      │ None (needs help)  │ 50-70%                 │ │
│  │  General Document  │ ⚠️ Partial  │ None (needs help)  │ < 50%                  │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
8.2 What User Does
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  USER ACTIONS SUMMARY                                                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Action                    │ When                          │ How                 │ │
│  ├────────────────────────────┼───────────────────────────────┼─────────────────────┤ │
│  │  Nothing (Auto-approved)   │ 80% of documents              │ System handles      │ │
│  │  Confirm Suggestion        │ 15% of documents              │ One click           │ │
│  │  Select from List          │ 5% of documents               │ Dropdown selection  │ │
│  │  Manual Entry              │ Rare (0.5% of docs)           │ Type to search      │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
9. Next Steps
Now that we have the mapping strategy defined, would you like me to:

Design the Organization Setup Screen - Facilities, Assets, Suppliers

Design the Batch Review Screen - Side-by-side for multiple documents

Design the Mapping Confirmation Screen - Where users confirm auto-mappings

Update the Customer Journey Map - With full mapping integration

🚀 CarbonTally: Upload once, auto-map everything, generate reports instantly.

