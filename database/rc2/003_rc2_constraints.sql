-- ================================================================
-- RC2: Constraints Hardening
-- Priority: High
-- Purpose: Fix data safety issues, missing constraints
-- Compatibility: RC1 schema frozen - adds constraints only
-- ================================================================

-- ================================================================
-- FIX: Missing NOT NULL Constraints
-- ================================================================

-- Ensure organisation_id is never null for core tables
DO $$
BEGIN
    -- Users table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE public.users 
        ALTER COLUMN organisation_id SET NOT NULL;
    END IF;
    
    -- Documents table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents') THEN
        ALTER TABLE public.documents 
        ALTER COLUMN organisation_id SET NOT NULL;
    END IF;
    
    -- Messages table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'messages') THEN
        ALTER TABLE public.messages 
        ALTER COLUMN organisation_id SET NOT NULL;
    END IF;
    
    -- Suppliers table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'suppliers') THEN
        ALTER TABLE public.suppliers 
        ALTER COLUMN organisation_id SET NOT NULL;
    END IF;
    
    -- Reports table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'reports') THEN
        ALTER TABLE public.reports 
        ALTER COLUMN organisation_id SET NOT NULL;
    END IF;
    
    -- Audit logs
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        ALTER TABLE public.audit_logs 
        ALTER COLUMN tenant_id SET NOT NULL;
    END IF;
END;
$$;

-- ================================================================
-- FIX: Missing CHECK Constraints for Data Integrity
-- ================================================================

-- Users: Validate email format (basic)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'email') THEN
        ALTER TABLE public.users 
        ADD CONSTRAINT chk_users_email_format 
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
    END IF;
END;
$$;

-- Documents: Validate file size
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'file_size') THEN
        ALTER TABLE public.documents 
        ADD CONSTRAINT chk_documents_file_size 
        CHECK (file_size > 0 AND file_size <= 52428800); -- 50MB
    END IF;
END;
$$;

-- Documents: Validate MIME type
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'mime_type') THEN
        ALTER TABLE public.documents 
        ADD CONSTRAINT chk_documents_mime_type 
        CHECK (mime_type IN ('application/pdf', 'image/jpeg', 'image/png', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'));
    END IF;
END;
$$;

-- Messages: Validate content not empty
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'messages' AND column_name = 'content') THEN
        ALTER TABLE public.messages 
        ADD CONSTRAINT chk_messages_content 
        CHECK (char_length(trim(content)) > 0);
    END IF;
END;
$$;

-- ================================================================
-- FIX: Unique Constraints for Business Logic
-- ================================================================

-- Users: Ensure unique email per organisation
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') 
    AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_users_organisation_email') THEN
        ALTER TABLE public.users 
        ADD CONSTRAINT uq_users_organisation_email 
        UNIQUE (organisation_id, email) 
        DEFERRABLE INITIALLY DEFERRED;
    END IF;
END;
$$;

-- Consultants: Ensure one consultant record per user
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'consultants') 
    AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_consultants_user_id') THEN
        ALTER TABLE public.consultants 
        ADD CONSTRAINT uq_consultants_user_id 
        UNIQUE (user_id);
    END IF;
END;
$$;

-- ================================================================
-- FIX: Foreign Key Actions
-- ================================================================

-- These are safe to add because they reference existing RC1 tables

DO $$
BEGIN
    -- Documents: ON DELETE CASCADE for organisation
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents') THEN
        ALTER TABLE public.documents 
        DROP CONSTRAINT IF EXISTS fk_documents_organisation;
        
        ALTER TABLE public.documents 
        ADD CONSTRAINT fk_documents_organisation 
        FOREIGN KEY (organisation_id) 
        REFERENCES public.organisations(id) 
        ON DELETE CASCADE;
    END IF;
    
    -- Messages: ON DELETE CASCADE for organisation
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'messages') THEN
        ALTER TABLE public.messages 
        DROP CONSTRAINT IF EXISTS fk_messages_organisation;
        
        ALTER TABLE public.messages 
        ADD CONSTRAINT fk_messages_organisation 
        FOREIGN KEY (organisation_id) 
        REFERENCES public.organisations(id) 
        ON DELETE CASCADE;
    END IF;
    
    -- Reports: ON DELETE CASCADE for organisation
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'reports') THEN
        ALTER TABLE public.reports 
        DROP CONSTRAINT IF EXISTS fk_reports_organisation;
        
        ALTER TABLE public.reports 
        ADD CONSTRAINT fk_reports_organisation 
        FOREIGN KEY (organisation_id) 
        REFERENCES public.organisations(id) 
        ON DELETE CASCADE;
    END IF;
    
    -- Suppliers: ON DELETE RESTRICT for organisations
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'suppliers') THEN
        ALTER TABLE public.suppliers 
        DROP CONSTRAINT IF EXISTS fk_suppliers_organisation;
        
        ALTER TABLE public.suppliers 
        ADD CONSTRAINT fk_suppliers_organisation 
        FOREIGN KEY (organisation_id) 
        REFERENCES public.organisations(id) 
        ON DELETE RESTRICT;
    END IF;
END;
$$;

-- ================================================================
-- FIX: Default Values
-- ================================================================

-- Add sensible defaults for common columns
DO $$
BEGIN
    -- Documents: Status default
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'status') THEN
        ALTER TABLE public.documents 
        ALTER COLUMN status SET DEFAULT 'pending';
    END IF;
    
    -- Messages: Read status default
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'messages' AND column_name = 'is_read') THEN
        ALTER TABLE public.messages 
        ALTER COLUMN is_read SET DEFAULT FALSE;
    END IF;
    
    -- Reports: Status default
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'status') THEN
        ALTER TABLE public.reports 
        ALTER COLUMN status SET DEFAULT 'draft';
    END IF;
END;
$$;

-- ================================================================
-- FIX: GDPR Compliance Constraints
-- ================================================================

-- Ensure audit logs are immutable (can't be updated)
DO $$
BEGIN
    -- Create trigger to prevent updates to audit_logs
    CREATE OR REPLACE FUNCTION public.prevent_audit_log_updates()
    RETURNS TRIGGER
    LANGUAGE plpgsql
    SECURITY DEFINER
    SET search_path = public
    AS $$
    BEGIN
        RAISE EXCEPTION 'Audit logs are immutable and cannot be updated or deleted';
        RETURN NULL;
    END;
    $$;
    
    -- Apply trigger if table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        DROP TRIGGER IF EXISTS prevent_audit_log_update ON public.audit_logs;
        DROP TRIGGER IF EXISTS prevent_audit_log_delete ON public.audit_logs;
        
        CREATE TRIGGER prevent_audit_log_update
        BEFORE UPDATE ON public.audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION public.prevent_audit_log_updates();
        
        CREATE TRIGGER prevent_audit_log_delete
        BEFORE DELETE ON public.audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION public.prevent_audit_log_updates();
    END IF;
END;
$$;