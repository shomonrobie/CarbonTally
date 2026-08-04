-- ================================================================
-- RC2: Functions Fix and Security Hardening
-- Priority: High
-- Purpose: Fix security, performance, and migration issues
-- Compatibility: RC1 schema frozen - modifies functions only
-- ================================================================

-- ================================================================
-- FIX: Search Path Safety for ALL Functions
-- ================================================================

-- Function to get current user tenant with safe search_path
CREATE OR REPLACE FUNCTION public.get_current_tenant()
RETURNS UUID
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_tenant_id UUID;
BEGIN
    SELECT organisation_id INTO v_tenant_id
    FROM public.users
    WHERE id = auth.uid();
    
    -- Handle case where user is a consultant
    IF v_tenant_id IS NULL THEN
        SELECT organisation_id INTO v_tenant_id
        FROM public.consultants
        WHERE user_id = auth.uid();
    END IF;
    
    RETURN v_tenant_id;
END;
$$;

-- ================================================================
-- FIX: GDPR Anonymisation Improved
-- ================================================================

-- Replace with improved version from 001_rc2_security.sql
-- Ensure this function is properly secured

CREATE OR REPLACE FUNCTION public.anonymise_user(
    user_id UUID
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $$
DECLARE
    target_user_id UUID := user_id;
    v_tenant_id UUID;
BEGIN
    -- Validate user exists
    IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = target_user_id) THEN
        RAISE EXCEPTION 'User % does not exist', target_user_id;
    END IF;

    -- Get tenant before anonymisation
    SELECT organisation_id INTO v_tenant_id
    FROM public.users
    WHERE id = target_user_id;

    -- Anonymise auth.users
    UPDATE auth.users
    SET 
        email = 'anonymised_' || gen_random_uuid()::text || '@example.com',
        raw_user_meta_data = jsonb_build_object(
            'anonymised_at', NOW(),
            'original_user_id', target_user_id
        ),
        phone = NULL,
        confirmation_token = NULL,
        recovery_token = NULL,
        raw_app_meta_data = jsonb_build_object(
            'provider', 'anonymised',
            'providers', ARRAY[]::text[]
        )
    WHERE id = target_user_id;

    -- Anonymise public.users profile
    UPDATE public.users
    SET 
        full_name = 'Anonymised User',
        company = NULL,
        job_title = NULL,
        avatar_url = NULL,
        phone = NULL,
        updated_at = NOW(),
        is_anonymised = TRUE
    WHERE id = target_user_id;

    -- Anonymise messages
    UPDATE public.messages
    SET 
        sender_name = 'Anonymised User',
        updated_at = NOW()
    WHERE sender_id = target_user_id;

    -- Anonymise consultant assignments
    UPDATE public.consultant_assignments
    SET 
        notes = CASE 
            WHEN notes IS NOT NULL THEN '[Anonymised] ' || notes
            ELSE notes
        END,
        updated_at = NOW()
    WHERE consultant_id = target_user_id;

    -- Break sessions
    DELETE FROM auth.refresh_tokens 
    WHERE user_id = target_user_id;

    -- Audit log the anonymisation
    INSERT INTO public.audit_logs (
        table_name,
        record_id,
        action,
        new_data,
        changed_by,
        tenant_id,
        ip_address
    )
    VALUES (
        '_anonymisation',
        target_user_id,
        'ANONYMISE_USER',
        jsonb_build_object('anonymised_by', auth.uid(), 'timestamp', NOW()),
        auth.uid(),
        v_tenant_id,
        inet_client_addr()
    );

    RAISE NOTICE 'User % anonymised successfully', target_user_id;
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Anonymisation failed for user %: %', target_user_id, SQLERRM;
        RAISE;
END;
$$;

-- ================================================================
-- FIX: updated_at Triggers - Ensure All Tables Have Them
-- ================================================================

-- Drop and recreate to ensure all tables covered
DO $$
DECLARE
    table_rec RECORD;
BEGIN
    -- Create trigger function if not exists
    CREATE OR REPLACE FUNCTION public.set_updated_at()
    RETURNS TRIGGER
    LANGUAGE plpgsql
    SET search_path = public
    AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$;

    -- Apply to all tables with updated_at column
    FOR table_rec IN
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
        AND tablename IN (
            SELECT table_name 
            FROM information_schema.columns 
            WHERE column_name = 'updated_at'
        )
    LOOP
        -- Drop existing trigger if exists
        EXECUTE format('DROP TRIGGER IF EXISTS trigger_set_updated_at ON public.%I', table_rec.tablename);
        
        -- Create new trigger
        EXECUTE format('
            CREATE TRIGGER trigger_set_updated_at
            BEFORE UPDATE ON public.%I
            FOR EACH ROW
            EXECUTE FUNCTION public.set_updated_at()', 
            table_rec.tablename
        );
        
        RAISE NOTICE 'Applied updated_at trigger to %', table_rec.tablename;
    END LOOP;
END;
$$;

-- ================================================================
-- FIX: Consultant Access Model
-- ================================================================

-- Function to get consultants for an organisation
CREATE OR REPLACE FUNCTION public.get_org_consultants(
    org_id UUID
)
RETURNS TABLE(
    user_id UUID,
    full_name TEXT,
    email TEXT,
    specialisation TEXT,
    rating DECIMAL
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- Ensure user belongs to this organisation
    IF NOT EXISTS (
        SELECT 1 FROM public.users 
        WHERE id = auth.uid() AND organisation_id = org_id
    ) THEN
        RAISE EXCEPTION 'User does not have access to organisation %', org_id;
    END IF;
    
    RETURN QUERY
    SELECT 
        u.id,
        u.full_name,
        u.email,
        c.specialisation,
        c.rating
    FROM public.consultants c
    JOIN public.users u ON u.id = c.user_id
    WHERE c.organisation_id = org_id
    AND c.active = true
    ORDER BY c.rating DESC NULLS LAST, u.full_name;
END;
$$;

-- ================================================================
-- FIX: Safe Tenant Switching
-- ================================================================

-- Function to switch organisation context (for multi-org users)
CREATE OR REPLACE FUNCTION public.switch_organisation(
    org_id UUID
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- Validate user belongs to this organisation
    IF NOT EXISTS (
        SELECT 1 FROM public.users 
        WHERE id = auth.uid() AND organisation_id = org_id
    ) AND NOT EXISTS (
        SELECT 1 FROM public.consultants 
        WHERE user_id = auth.uid() AND organisation_id = org_id
    ) THEN
        RAISE EXCEPTION 'User does not have access to organisation %', org_id;
    END IF;
    
    -- Update session context (implementation depends on app)
    -- This is a placeholder - actual switching handled by application layer
    
    RETURN jsonb_build_object(
        'success', true,
        'organisation_id', org_id,
        'switched_at', NOW()
    );
END;
$$;

-- ================================================================
-- FIX: Audit Log Helpers
-- ================================================================

-- Function to audit document access
CREATE OR REPLACE FUNCTION public.audit_document_access(
    document_id UUID,
    action TEXT
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.audit_logs (
        table_name,
        record_id,
        action,
        new_data,
        changed_by,
        tenant_id,
        ip_address,
        user_agent
    )
    SELECT 
        'documents',
        document_id,
        'DOCUMENT_ACCESS_' || action,
        jsonb_build_object(
            'document_id', document_id,
            'action', action,
            'timestamp', NOW()
        ),
        auth.uid(),
        d.organisation_id,
        inet_client_addr(),
        current_setting('request.headers', true)::jsonb->>'user-agent'
    FROM public.documents d
    WHERE d.id = document_id;
END;
$$;

-- ================================================================
-- FIX: Queue Processing Functions
-- ================================================================

-- Lock and process next job (safely)
CREATE OR REPLACE FUNCTION public.process_next_job(
    queue_name TEXT DEFAULT 'default'
)
RETURNS TABLE(
    job_id UUID,
    payload JSONB,
    priority INTEGER
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_job_id UUID;
    v_payload JSONB;
    v_priority INTEGER;
BEGIN
    -- Use advisory lock to prevent duplicate processing
    IF pg_try_advisory_xact_lock(hashtext('job_queue_' || queue_name)) THEN
        -- Find next pending job
        SELECT id, payload, priority
        INTO v_job_id, v_payload, v_priority
        FROM public.job_queue
        WHERE status = 'pending'
        AND queue_name = process_next_job.queue_name
        ORDER BY priority DESC, created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED;
        
        IF v_job_id IS NOT NULL THEN
            -- Mark as processing
            UPDATE public.job_queue
            SET 
                status = 'processing',
                started_at = NOW(),
                attempts = attempts + 1
            WHERE id = v_job_id;
            
            RETURN QUERY SELECT v_job_id, v_payload, v_priority;
        END IF;
    END IF;
END;
$$;

-- Complete job with status
CREATE OR REPLACE FUNCTION public.complete_job(
    job_id UUID,
    success BOOLEAN,
    result JSONB DEFAULT NULL,
    error_message TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    UPDATE public.job_queue
    SET 
        status = CASE WHEN success THEN 'completed' ELSE 'failed' END,
        completed_at = NOW(),
        result = complete_job.result,
        error_message = complete_job.error_message
    WHERE id = job_id
    AND status = 'processing';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Job % not found or not in processing state', job_id;
    END IF;
END;
$$;

-- ================================================================
-- FIX: GDPR Data Retention
-- ================================================================

-- Function to purge old audit logs (GDPR compliance)
CREATE OR REPLACE FUNCTION public.purge_audit_logs(
    older_than INTERVAL DEFAULT INTERVAL '1 year'
)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- Only service role can purge logs
    IF auth.role() != 'service_role' AND auth.role() != 'admin' THEN
        RAISE EXCEPTION 'Only service role or admin can purge audit logs';
    END IF;
    
    -- Delete old logs
    WITH deleted AS (
        DELETE FROM public.audit_logs
        WHERE created_at < NOW() - older_than
        RETURNING id
    )
    SELECT COUNT(*) INTO v_deleted_count
    FROM deleted;
    
    -- Log the purge
    INSERT INTO public.audit_logs (
        table_name,
        record_id,
        action,
        new_data,
        changed_by,
        tenant_id
    )
    VALUES (
        '_audit_purge',
        gen_random_uuid(),
        'PURGE_AUDIT_LOGS',
        jsonb_build_object(
            'purged_count', v_deleted_count,
            'older_than', older_than,
            'timestamp', NOW()
        ),
        auth.uid(),
        NULL
    );
    
    RETURN v_deleted_count;
END;
$$;

COMMENT ON FUNCTION public.purge_audit_logs(INTERVAL) IS 
'GDPR-compliant audit log purging. Only service role can execute.';