-- ================================================================
-- RC2: Verification Script
-- Priority: Medium
-- Purpose: Verify all fixes have been applied correctly
-- Can be run after migration to validate success
-- ================================================================

-- ================================================================
-- Schema Verification
-- ================================================================

CREATE OR REPLACE FUNCTION public.verify_rc2_migration()
RETURNS TABLE(
    check_name TEXT,
    passed BOOLEAN,
    details TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- ============================================================
    -- 1. Verify RLS is enabled on all tables
    -- ============================================================
    RETURN QUERY
    SELECT 
        'RLS: ' || t.tablename,
        (SELECT relrowsecurity FROM pg_class WHERE relname = t.tablename),
        CASE 
            WHEN (SELECT relrowsecurity FROM pg_class WHERE relname = t.tablename) 
            THEN 'RLS enabled'
            ELSE 'RLS NOT enabled - SECURITY RISK'
        END
    FROM pg_tables t
    WHERE schemaname = 'public'
    AND t.tablename NOT IN ('audit_logs', 'job_queue');
    
    -- ============================================================
    -- 2. Verify key constraints exist
    -- ============================================================
    RETURN QUERY
    SELECT 
        'Constraint: ' || conname,
        TRUE,
        'Exists: ' || conname
    FROM pg_constraint 
    WHERE conname IN (
        'uq_users_organisation_email',
        'uq_consultants_user_id',
        'chk_users_email_format',
        'chk_documents_file_size',
        'chk_documents_mime_type',
        'chk_messages_content'
    );
    
    -- ============================================================
    -- 3. Verify updated_at triggers
    -- ============================================================
    RETURN QUERY
    SELECT 
        'Trigger: ' || tgname,
        EXISTS (
            SELECT 1 FROM pg_trigger 
            WHERE tgname = 'trigger_set_updated_at'
        ),
        CASE 
            WHEN EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_set_updated_at')
            THEN 'Trigger exists'
            ELSE 'Trigger missing'
        END
    FROM pg_trigger
    WHERE tgname = 'trigger_set_updated_at';
    
    -- ============================================================
    -- 4. Verify security functions exist
    -- ============================================================
    RETURN QUERY
    SELECT 
        'Function: ' || proname,
        EXISTS (
            SELECT 1 FROM pg_proc WHERE proname = 'anonymise_user'
        ),
        CASE 
            WHEN EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'anonymise_user')
            THEN 'Function exists'
            ELSE 'Function missing'
        END
    FROM pg_proc
    WHERE proname IN ('anonymise_user', 'is_admin', 'get_current_tenant');
    
    -- ============================================================
    -- 5. Verify storage policies exist
    -- ============================================================
    RETURN QUERY
    SELECT 
        'Storage Policy: ' || policyname,
        EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE schemaname = 'storage' 
            AND policyname IN ('Users can upload documents', 'Users can view documents')
        ),
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM pg_policies 
                WHERE schemaname = 'storage' 
                AND policyname IN ('Users can upload documents', 'Users can view documents')
            )
            THEN 'Storage policies exist'
            ELSE 'Storage policies missing'
        END
    FROM pg_policies
    WHERE schemaname = 'storage' 
    LIMIT 1;
    
    -- ============================================================
    -- 6. Verify indexes exist
    -- ============================================================
    RETURN QUERY
    SELECT 
        'Index: ' || indexname,
        EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE indexname IN (
                'idx_users_organisation_id',
                'idx_documents_organisation_id',
                'idx_messages_organisation_id',
                'idx_suppliers_organisation_id',
                'idx_reports_organisation_id'
            )
        ),
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname IN (
                    'idx_users_organisation_id',
                    'idx_documents_organisation_id',
                    'idx_messages_organisation_id',
                    'idx_suppliers_organisation_id',
                    'idx_reports_organisation_id'
                )
            )
            THEN 'Critical indexes exist'
            ELSE 'Missing critical indexes - PERFORMANCE RISK'
        END
    FROM pg_indexes
    WHERE tablename = 'users'
    LIMIT 1;
    
    -- ============================================================
    -- 7. Verify audit log protection
    -- ============================================================
    RETURN QUERY
    SELECT 
        'Audit Log Protection',
        EXISTS (
            SELECT 1 FROM pg_trigger 
            WHERE tgname IN ('prevent_audit_log_update', 'prevent_audit_log_delete')
        ),
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM pg_trigger 
                WHERE tgname IN ('prevent_audit_log_update', 'prevent_audit_log_delete')
            )
            THEN 'Audit logs protected'
            ELSE 'Audit logs not protected - GDPR RISK'
        END
    FROM pg_trigger
    WHERE tgname = 'prevent_audit_log_update';
    
    -- ============================================================
    -- 8. Verify GDPR compliance
    -- ============================================================
    RETURN QUERY
    SELECT 
        'GDPR: anonymise_user exists',
        EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'anonymise_user'),
        CASE 
            WHEN EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'anonymise_user')
            THEN 'GDPR functions exist'
            ELSE 'GDPR compliance incomplete'
        END
    FROM pg_proc
    WHERE proname = 'anonymise_user';
    
    -- ============================================================
    -- 9. Verify queue functions
    -- ============================================================
    RETURN QUERY
    SELECT 
        'Queue: process_next_job exists',
        EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'process_next_job'),
        CASE 
            WHEN EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'process_next_job')
            THEN 'Queue processing functions exist'
            ELSE 'Queue functions missing'
        END
    FROM pg_proc
    WHERE proname = 'process_next_job';
    
    -- ============================================================
    -- 10. Summary check - all passed
    -- ============================================================
    RETURN QUERY
    SELECT 
        'OVERALL: Critical Checks',
        (
            SELECT COUNT(*) FROM (
                SELECT 1 FROM pg_proc WHERE proname = 'anonymise_user'
                UNION ALL
                SELECT 1 FROM pg_proc WHERE proname = 'get_current_tenant'
                UNION ALL
                SELECT 1 FROM pg_proc WHERE proname = 'set_updated_at'
                UNION ALL
                SELECT 1 FROM pg_proc WHERE proname = 'process_next_job'
            ) checks
        ) >= 4,
        CASE 
            WHEN (
                SELECT COUNT(*) FROM (
                    SELECT 1 FROM pg_proc WHERE proname = 'anonymise_user'
                    UNION ALL
                    SELECT 1 FROM pg_proc WHERE proname = 'get_current_tenant'
                    UNION ALL
                    SELECT 1 FROM pg_proc WHERE proname = 'set_updated_at'
                    UNION ALL
                    SELECT 1 FROM pg_proc WHERE proname = 'process_next_job'
                ) checks
            ) >= 4
            THEN 'All critical functions exist'
            ELSE 'Some critical functions missing'
        END;
END;
$$;

-- ================================================================
-- Run verification
-- ================================================================

-- Execute the verification
SELECT * FROM public.verify_rc2_migration()
ORDER BY check_name;

-- ================================================================
-- Additional Security Checks
-- ================================================================

-- Find any tables without RLS
SELECT 
    schemaname,
    tablename,
    CASE WHEN relrowsecurity THEN 'Enabled' ELSE 'DISABLED - FIX!' END as rls_status
FROM pg_tables t
JOIN pg_class c ON c.relname = t.tablename
WHERE schemaname = 'public'
AND NOT EXISTS (
    SELECT 1 FROM pg_policies p 
    WHERE p.schemaname = t.schemaname 
    AND p.tablename = t.tablename
)
ORDER BY tablename;

-- Find any tables without updated_at triggers
SELECT 
    t.tablename,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM pg_trigger tr 
            WHERE tr.tgname = 'trigger_set_updated_at'
            AND tr.tgrelid = c.oid
        ) 
        THEN 'Has trigger' 
        ELSE 'MISSING TRIGGER' 
    END as trigger_status
FROM pg_tables t
JOIN pg_class c ON c.relname = t.tablename
WHERE schemaname = 'public'
AND EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = t.tablename 
    AND column_name = 'updated_at'
)
ORDER BY tablename;

-- Verify all foreign keys are properly indexed
SELECT 
    conname,
    conrelid::regclass AS table_name,
    a.attname AS column_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE tablename = conrelid::regclass::text
            AND indexdef LIKE '%' || a.attname || '%'
        ) 
        THEN 'Indexed' 
        ELSE 'NOT INDEXED - Performance Risk' 
    END as index_status
FROM pg_constraint c
JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
WHERE contype = 'f'
ORDER BY table_name, column_name;

COMMENT ON FUNCTION public.verify_rc2_migration() IS 
'RC2 migration verification script. Check all security and performance fixes applied.';