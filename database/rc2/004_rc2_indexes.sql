-- ================================================================
-- RC2: Index Performance Optimisation
-- Priority: High
-- Purpose: Fix missing indexes for performance
-- Compatibility: RC1 schema frozen - adds indexes only
-- ================================================================

-- ================================================================
-- Tenant-based indexes for multi-tenant queries
-- ================================================================

-- Primary tenant indexes (essential for all multi-tenant queries)
DO $$
BEGIN
    -- Users: Organisation queries
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_organisation_id 
        ON public.users (organisation_id);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_organisation_role 
        ON public.users (organisation_id, role);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email 
        ON public.users (email);
    END IF;
    
    -- Documents: Tenant + status queries
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_organisation_id 
        ON public.documents (organisation_id);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_organisation_status 
        ON public.documents (organisation_id, status);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_created_at 
        ON public.documents (created_at DESC);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_uploaded_by 
        ON public.documents (uploaded_by);
    END IF;
    
    -- Messages: Tenant + time queries
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'messages') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_organisation_id 
        ON public.messages (organisation_id);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_created_at 
        ON public.messages (created_at DESC);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_sender_id 
        ON public.messages (sender_id);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_is_read 
        ON public.messages (is_read) 
        WHERE is_read = false;
    END IF;
    
    -- Suppliers: Tenant queries
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'suppliers') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_organisation_id 
        ON public.suppliers (organisation_id);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_name 
        ON public.suppliers (name);
    END IF;
    
    -- Reports: Tenant + time queries
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'reports') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_organisation_id 
        ON public.reports (organisation_id);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_created_at 
        ON public.reports (created_at DESC);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_status 
        ON public.reports (status) 
        WHERE status = 'processing';
    END IF;
    
    -- Consultants: Organisation + user queries
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'consultants') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_consultants_organisation_id 
        ON public.consultants (organisation_id);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_consultants_user_id 
        ON public.consultants (user_id);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_consultants_specialisation 
        ON public.consultants (specialisation);
    END IF;
END;
$$;

-- ================================================================
-- Foreign Key Support Indexes
-- ================================================================

DO $$
BEGIN
    -- Messages: Foreign key indexes
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'messages') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_supplier_id 
        ON public.messages (supplier_id);
    END IF;
    
    -- Documents: Foreign key indexes
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_supplier_id 
        ON public.documents (supplier_id);
    END IF;
    
    -- Reports: Foreign key indexes
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'reports') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_created_by 
        ON public.reports (created_by);
    END IF;
END;
$$;

-- ================================================================
-- Partial Indexes for Performance
-- ================================================================

DO $$
BEGIN
    -- Documents: Index only active/processing documents
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_processing 
        ON public.documents (created_at) 
        WHERE status = 'processing';
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_ocr_pending 
        ON public.documents (created_at) 
        WHERE status = 'ocr_pending';
    END IF;
    
    -- Users: Index only active users
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active 
        ON public.users (organisation_id) 
        WHERE active = true;
    END IF;
END;
$$;

-- ================================================================
-- GIN Indexes for JSON/Text Search
-- ================================================================

DO $$
BEGIN
    -- Documents: JSON metadata search
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'metadata') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_metadata_gin 
        ON public.documents USING gin (metadata);
    END IF;
    
    -- Documents: Full text search on document name
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'name') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_name_trgm 
        ON public.documents USING gin (name gin_trgm_ops);
    END IF;
    
    -- Suppliers: Text search on name
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'suppliers' AND column_name = 'name') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_name_trgm 
        ON public.suppliers USING gin (name gin_trgm_ops);
    END IF;
    
    -- Suppliers: JSON capabilities
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'suppliers' AND column_name = 'capabilities') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_capabilities_gin 
        ON public.suppliers USING gin (capabilities);
    END IF;
    
    -- Messages: Full text search on content
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'messages' AND column_name = 'content') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_content_trgm 
        ON public.messages USING gin (content gin_trgm_ops);
    END IF;
    
    -- Reports: Full text search on name/description
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'name') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_name_trgm 
        ON public.reports USING gin (name gin_trgm_ops);
    END IF;
END;
$$;

-- ================================================================
-- Queue Performance Indexes
-- ================================================================

DO $$
BEGIN
    -- If job queue exists, add performance indexes
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'job_queue') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_queue_status_priority 
        ON public.job_queue (status, priority DESC, created_at)
        WHERE status IN ('pending', 'processing');
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_queue_retry_count 
        ON public.job_queue (retry_count) 
        WHERE retry_count < 5 AND status = 'failed';
    END IF;
END;
$$;

-- ================================================================
-- Date-range indexes for reporting
-- ================================================================

DO $$
BEGIN
    -- Documents: Date range queries
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_created_at_brin 
        ON public.documents USING brin (created_at);
    END IF;
    
    -- Messages: Date range queries
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'messages') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_created_at_brin 
        ON public.messages USING brin (created_at);
    END IF;
    
    -- Reports: Date range queries
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'reports') THEN
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_created_at_brin 
        ON public.reports USING brin (created_at);
    END IF;
END;
$$;

-- ================================================================
-- Analyse tables for statistics
-- ================================================================

-- Run ANALYZE to update statistics for new indexes
DO $$
BEGIN
    ANALYZE public.users;
    ANALYZE public.documents;
    ANALYZE public.messages;
    ANALYZE public.suppliers;
    ANALYZE public.reports;
    ANALYZE public.consultants;
    ANALYZE public.audit_logs;
END;
$$;

COMMENT ON TABLE public.documents IS 'Document storage with full-text search and JSON metadata support';
COMMENT ON TABLE public.messages IS 'Message system with content search and queue-like performance';