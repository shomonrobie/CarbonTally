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