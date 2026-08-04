-- ================================================================
-- RC2: Complete RLS Coverage
-- Priority: Critical
-- Purpose: Close all RLS gaps identified in RC1 audit
-- Compatibility: RC1 schema frozen - extends security only
-- ================================================================

-- ================================================================
-- RLS Helper Functions
-- ================================================================

-- Function to get user's organisation ID (null if consultant)
CREATE OR REPLACE FUNCTION public.get_user_organisation_id()
RETURNS UUID
LANGUAGE plpgsql
STABLE
SET search_path = public
AS $$
DECLARE
    v_org_id UUID;
BEGIN
    SELECT organisation_id INTO v_org_id
    FROM public.users
    WHERE id = auth.uid();
    RETURN v_org_id;
END;
$$;

-- Function to check if user is a consultant
CREATE OR REPLACE FUNCTION public.is_consultant()
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
SET search_path = public
AS $$
DECLARE
    v_is_consultant BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM public.consultants 
        WHERE user_id = auth.uid()
    ) INTO v_is_consultant;
    
    RETURN v_is_consultant;
END;
$$;

-- Function to check if user is admin of their organisation
CREATE OR REPLACE FUNCTION public.is_org_admin()
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
SET search_path = public
AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.users
        WHERE id = auth.uid()
        AND role = 'admin'
    );
END;
$$;

-- ================================================================
-- RLS Policies: organisations
-- ================================================================

-- Drop existing policies to avoid conflicts
DROP POLICY IF EXISTS "Users can view own organisation" ON public.organisations;
DROP POLICY IF EXISTS "Admins can update own organisation" ON public.organisations;

-- Organisations: Viewable by any member of the organisation
CREATE POLICY "Users can view own organisation" 
ON public.organisations 
FOR SELECT 
USING (
    id IN (
        SELECT organisation_id FROM public.users WHERE id = auth.uid()
    )
    OR
    id IN (
        SELECT organisation_id FROM public.consultants WHERE user_id = auth.uid()
    )
);

-- Organisations: Only admins can update
CREATE POLICY "Admins can update own organisation" 
ON public.organisations 
FOR UPDATE 
USING (
    id IN (
        SELECT organisation_id FROM public.users 
        WHERE id = auth.uid() AND role = 'admin'
    )
);

-- No insert or delete policies - organisations created via app logic

-- ================================================================
-- RLS Policies: users
-- ================================================================

DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
DROP POLICY IF EXISTS "Organisation admins can view members" ON public.users;

-- Users: View own profile and other members in same organisation
CREATE POLICY "Users can view relevant profiles" 
ON public.users 
FOR SELECT 
USING (
    id = auth.uid() -- Own profile
    OR
    organisation_id = get_user_organisation_id() -- Same organisation
    OR
    id IN (SELECT user_id FROM public.consultants WHERE organisation_id = get_user_organisation_id()) -- Consultants in org
);

-- Users: Update own profile only
CREATE POLICY "Users can update own profile" 
ON public.users 
FOR UPDATE 
USING (id = auth.uid())
WITH CHECK (id = auth.uid());

-- Users: Only admins can insert (service role for auth triggers)
CREATE POLICY "Service role can manage users" 
ON public.users 
FOR ALL 
USING (auth.role() = 'service_role');

-- ================================================================
-- RLS Policies: consultants
-- ================================================================

DROP POLICY IF EXISTS "Users can view consultants in org" ON public.consultants;
DROP POLICY IF EXISTS "Consultants can update own profile" ON public.consultants;

-- Consultants: Viewable by organisation members
CREATE POLICY "Organisation members can view consultants" 
ON public.consultants 
FOR SELECT 
USING (
    organisation_id = get_user_organisation_id()
    OR
    user_id = auth.uid()
);

-- Consultants: Update own profile only
CREATE POLICY "Consultants can update own profile" 
ON public.consultants 
FOR UPDATE 
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- ================================================================
-- RLS Policies: clients (assuming table exists)
-- ================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'clients') THEN
        CREATE POLICY "Organisation members can view clients" ON public.clients
        FOR SELECT USING (
            organisation_id = get_user_organisation_id()
        );
        
        CREATE POLICY "Organisation admins can manage clients" ON public.clients
        FOR ALL USING (
            organisation_id = get_user_organisation_id()
            AND is_org_admin()
        );
    END IF;
END $$;

-- ================================================================
-- RLS Policies: documents
-- ================================================================

DROP POLICY IF EXISTS "Users can view documents in org" ON public.documents;
DROP POLICY IF EXISTS "Users can insert documents" ON public.documents;
DROP POLICY IF EXISTS "Users can update documents" ON public.documents;

-- Documents: Viewable by organisation members
CREATE POLICY "Organisation members can view documents" 
ON public.documents 
FOR SELECT 
USING (
    organisation_id = get_user_organisation_id()
    OR
    EXISTS (SELECT 1 FROM public.consultants WHERE user_id = auth.uid() AND organisation_id = documents.organisation_id)
);

-- Documents: Insert with organisation validation
CREATE POLICY "Users can insert documents" 
ON public.documents 
FOR INSERT 
WITH CHECK (
    organisation_id = get_user_organisation_id()
    AND auth.role() IN ('authenticated', 'service_role')
);

-- Documents: Update own documents only
CREATE POLICY "Users can update own documents" 
ON public.documents 
FOR UPDATE 
USING (
    (uploaded_by = auth.uid() OR is_org_admin())
    AND organisation_id = get_user_organisation_id()
)
WITH CHECK (
    (uploaded_by = auth.uid() OR is_org_admin())
    AND organisation_id = get_user_organisation_id()
);

-- Documents: Only admins can delete
CREATE POLICY "Admins can delete documents" 
ON public.documents 
FOR DELETE 
USING (
    is_org_admin()
    AND organisation_id = get_user_organisation_id()
);

-- ================================================================
-- RLS Policies: messages
-- ================================================================

DROP POLICY IF EXISTS "Users can view messages in org" ON public.messages;
DROP POLICY IF EXISTS "Users can send messages" ON public.messages;

-- Messages: Viewable by organisation members
CREATE POLICY "Organisation members can view messages" 
ON public.messages 
FOR SELECT 
USING (
    organisation_id = get_user_organisation_id()
    OR
    EXISTS (SELECT 1 FROM public.consultants WHERE user_id = auth.uid() AND organisation_id = messages.organisation_id)
);

-- Messages: Insert with validation
CREATE POLICY "Organisation members can send messages" 
ON public.messages 
FOR INSERT 
WITH CHECK (
    organisation_id = get_user_organisation_id()
    AND auth.role() IN ('authenticated', 'service_role')
    AND (sender_id = auth.uid() OR sender_id IS NULL) -- Allow NULL for system messages
);

-- Messages: Update only own messages (for edits)
CREATE POLICY "Users can update own messages" 
ON public.messages 
FOR UPDATE 
USING (sender_id = auth.uid())
WITH CHECK (sender_id = auth.uid());

-- ================================================================
-- RLS Policies: suppliers
-- ================================================================

DROP POLICY IF EXISTS "Organisation members can view suppliers" ON public.suppliers;

-- Suppliers: Viewable by organisation members
CREATE POLICY "Organisation members can view suppliers" 
ON public.suppliers 
FOR SELECT 
USING (
    organisation_id = get_user_organisation_id()
);

-- Suppliers: Admins can manage
CREATE POLICY "Admins can manage suppliers" 
ON public.suppliers 
FOR ALL 
USING (
    organisation_id = get_user_organisation_id()
    AND is_org_admin()
);

-- ================================================================
-- RLS Policies: reports
-- ================================================================

DROP POLICY IF EXISTS "Organisation members can view reports" ON public.reports;
DROP POLICY IF EXISTS "Users can create reports" ON public.reports;

-- Reports: Viewable by organisation members
CREATE POLICY "Organisation members can view reports" 
ON public.reports 
FOR SELECT 
USING (
    organisation_id = get_user_organisation_id()
);

-- Reports: Create with validation
CREATE POLICY "Users can create reports" 
ON public.reports 
FOR INSERT 
WITH CHECK (
    organisation_id = get_user_organisation_id()
    AND (created_by = auth.uid() OR auth.role() = 'service_role')
);

-- Reports: Update own reports
CREATE POLICY "Users can update own reports" 
ON public.reports 
FOR UPDATE 
USING (
    created_by = auth.uid()
    AND organisation_id = get_user_organisation_id()
)
WITH CHECK (
    created_by = auth.uid()
    AND organisation_id = get_user_organisation_id()
);

-- ================================================================
-- RLS Policies: audit_logs
-- ================================================================

-- Already created in security file, but ensure it exists
CREATE POLICY IF NOT EXISTS "Users can view own tenant audit logs" 
ON public.audit_logs 
FOR SELECT 
USING (tenant_id = get_user_organisation_id());

-- ================================================================
-- RLS Policies: verification
-- ================================================================

-- Ensure all tables have RLS enabled
DO $$
DECLARE
    table_rec RECORD;
BEGIN
    FOR table_rec IN 
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename NOT IN ('audit_logs') -- Already done
    LOOP
        EXECUTE format('ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY', 
                      table_rec.schemaname, table_rec.tablename);
        
        -- Add a default policy if none exists
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE schemaname = table_rec.schemaname 
            AND tablename = table_rec.tablename
        ) THEN
            -- Create a restrictive default policy
            EXECUTE format('CREATE POLICY "Default deny" ON %I.%I 
                          FOR ALL USING (false)', 
                          table_rec.schemaname, table_rec.tablename);
            RAISE NOTICE 'Added default deny policy to %', table_rec.tablename;
        END IF;
    END LOOP;
END;
$$;

-- ================================================================
-- RLS Policy Conflict Resolution
-- ================================================================

-- Ensure policies are ordered correctly (most restrictive first)
-- This is handled by PostgreSQL automatically

-- Verify all policies are correctly applied
CREATE OR REPLACE FUNCTION public.verify_rls_coverage()
RETURNS TABLE(
    table_name TEXT,
    has_rls BOOLEAN,
    policy_count BIGINT
)
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.tablename::TEXT,
        (SELECT relrowsecurity FROM pg_class WHERE relname = t.tablename) AS has_rls,
        (SELECT COUNT(*) FROM pg_policies WHERE tablename = t.tablename) AS policy_count
    FROM pg_tables t
    WHERE schemaname = 'public'
    ORDER BY tablename;
END;
$$;

COMMENT ON FUNCTION public.verify_rls_coverage() IS 
'Verifies RLS is enabled and policies exist for all public tables';