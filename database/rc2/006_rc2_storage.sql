-- ================================================================
-- RC2: Storage Security Hardening
-- Priority: High
-- Purpose: Secure storage buckets with RLS
-- Compatibility: RC1 schema frozen - adds storage policies only
-- ================================================================

-- ================================================================
-- Storage Bucket Policies
-- ================================================================

-- Documents bucket policies
DO $$
BEGIN
    -- Drop existing policies if they exist
    DROP POLICY IF EXISTS "Users can upload documents" ON storage.objects;
    DROP POLICY IF EXISTS "Users can view own documents" ON storage.objects;
    DROP POLICY IF EXISTS "Users can update own documents" ON storage.objects;
    DROP POLICY IF EXISTS "Users can delete own documents" ON storage.objects;

    -- Upload documents
    CREATE POLICY "Users can upload documents" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'documents'
        AND auth.role() = 'authenticated'
        AND (storage.foldername(name))[1] = 'users'
        AND (storage.foldername(name))[2] = auth.uid()::text
    );

    -- View documents
    CREATE POLICY "Users can view own documents" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'documents'
        AND auth.role() = 'authenticated'
        AND (
            (storage.foldername(name))[1] = 'users'
            AND (storage.foldername(name))[2] = auth.uid()::text
        )
        OR
        EXISTS (
            SELECT 1 FROM public.documents d
            WHERE d.organisation_id = public.get_user_organisation_id()
            AND d.file_path = storage.foldername(name) || '/' || storage.filename(name)
        )
    );

    -- Update documents
    CREATE POLICY "Users can update own documents" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'documents'
        AND auth.role() = 'authenticated'
        AND (storage.foldername(name))[1] = 'users'
        AND (storage.foldername(name))[2] = auth.uid()::text
    );

    -- Delete documents
    CREATE POLICY "Users can delete own documents" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'documents'
        AND auth.role() = 'authenticated'
        AND (storage.foldername(name))[1] = 'users'
        AND (storage.foldername(name))[2] = auth.uid()::text
    );
END;
$$;

-- Avatars bucket policies
DO $$
BEGIN
    DROP POLICY IF EXISTS "Users can upload avatars" ON storage.objects;
    DROP POLICY IF EXISTS "Users can view avatars" ON storage.objects;
    DROP POLICY IF EXISTS "Users can update own avatar" ON storage.objects;
    DROP POLICY IF EXISTS "Users can delete own avatar" ON storage.objects;

    -- Upload avatars (public bucket, but controlled)
    CREATE POLICY "Users can upload avatars" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'avatars'
        AND auth.role() = 'authenticated'
        AND (storage.foldername(name))[1] = 'users'
        AND (storage.foldername(name))[2] = auth.uid()::text
    );

    -- View avatars (public)
    CREATE POLICY "Users can view avatars" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'avatars'
        AND auth.role() = 'authenticated'
    );

    -- Update own avatar
    CREATE POLICY "Users can update own avatar" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'avatars'
        AND auth.role() = 'authenticated'
        AND (storage.foldername(name))[1] = 'users'
        AND (storage.foldername(name))[2] = auth.uid()::text
    );

    -- Delete own avatar
    CREATE POLICY "Users can delete own avatar" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'avatars'
        AND auth.role() = 'authenticated'
        AND (storage.foldername(name))[1] = 'users'
        AND (storage.foldername(name))[2] = auth.uid()::text
    );
END;
$$;

-- Reports bucket policies
DO $$
BEGIN
    DROP POLICY IF EXISTS "Users can upload reports" ON storage.objects;
    DROP POLICY IF EXISTS "Users can view reports" ON storage.objects;
    DROP POLICY IF EXISTS "Users can delete reports" ON storage.objects;

    -- Upload reports
    CREATE POLICY "Users can upload reports" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'reports'
        AND auth.role() = 'authenticated'
        AND (storage.foldername(name))[1] = 'organisations'
        AND EXISTS (
            SELECT 1 FROM public.users
            WHERE id = auth.uid()
            AND organisation_id::text = (storage.foldername(name))[2]
        )
    );

    -- View reports
    CREATE POLICY "Users can view reports" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'reports'
        AND auth.role() = 'authenticated'
        AND EXISTS (
            SELECT 1 FROM public.users
            WHERE id = auth.uid()
            AND organisation_id::text = (storage.foldername(name))[2]
        )
    );

    -- Delete reports
    CREATE POLICY "Users can delete reports" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'reports'
        AND auth.role() = 'authenticated'
        AND (
            EXISTS (
                SELECT 1 FROM public.users
                WHERE id = auth.uid()
                AND organisation_id::text = (storage.foldername(name))[2]
                AND role = 'admin'
            )
            OR
            (storage.foldername(name))[1] = 'users'
            AND (storage.foldername(name))[2] = auth.uid()::text
        )
    );
END;
$$;

-- ================================================================
-- Storage Performance
-- ================================================================

-- Create storage performance indexes
CREATE INDEX IF NOT EXISTS idx_storage_objects_bucket_created 
ON storage.objects (bucket_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_storage_objects_owner 
ON storage.objects (owner);

-- ================================================================
-- Storage Metadata Functions
-- ================================================================

-- Function to get storage usage per organisation
CREATE OR REPLACE FUNCTION public.get_storage_usage(
    org_id UUID
)
RETURNS TABLE(
    bucket TEXT,
    total_size BIGINT,
    file_count INTEGER
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- Ensure user has access to this organisation
    IF NOT EXISTS (
        SELECT 1 FROM public.users 
        WHERE id = auth.uid() AND organisation_id = org_id
    ) AND NOT EXISTS (
        SELECT 1 FROM public.consultants 
        WHERE user_id = auth.uid() AND organisation_id = org_id
    ) THEN
        RAISE EXCEPTION 'User does not have access to organisation %', org_id;
    END IF;
    
    RETURN QUERY
    SELECT 
        bucket_id::TEXT,
        SUM(size)::BIGINT,
        COUNT(*)::INTEGER
    FROM storage.objects
    WHERE bucket_id IN ('documents', 'reports', 'avatars')
    AND owner::text IN (
        SELECT id::text FROM public.users WHERE organisation_id = org_id
    )
    GROUP BY bucket_id;
END;
$$;

COMMENT ON FUNCTION public.get_storage_usage(UUID) IS 
'Get storage usage statistics for an organisation. Restricted to organisation members.';