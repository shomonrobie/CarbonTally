-- ============================================
-- MIGRATION 012: DATA MIGRATION & CLEANUP
-- Migrate existing data to new schema
-- ============================================

-- ============================================
-- 12.1 Migrate Organizations
-- ============================================

-- Existing organizations table is kept as-is.
-- Any missing fields are preserved in metadata.

-- ============================================
-- 12.2 Migrate Organization Members to Organization Access
-- ============================================

-- Get client workspace ID
DO $$
DECLARE
    client_workspace_id UUID;
BEGIN
    SELECT id INTO client_workspace_id FROM workspaces WHERE code = 'client';
    
    -- Migrate existing organization_members to organization_access
    INSERT INTO organization_access (
        user_id,
        organization_id,
        workspace_id,
        access_type,
        is_active,
        created_at,
        updated_at
    )
    SELECT 
        om.user_id,
        om.organization_id,
        client_workspace_id,
        CASE 
            WHEN om.role = 'admin' THEN 'owner'
            ELSE 'member'
        END,
        om.is_active,
        om.created_at,
        om.updated_at
    FROM organization_members om
    WHERE om.user_id IS NOT NULL
    AND om.organization_id IS NOT NULL
    ON CONFLICT (user_id, organization_id, workspace_id) DO NOTHING;
END $$;

-- ============================================
-- 12.3 Migrate Existing Users (If users table exists)
-- ============================================

-- This assumes there's an existing users/auth table
-- Adjust based on actual existing schema

DO $$
BEGIN
    -- If users table exists and is not the new users table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'auth_users') THEN
        INSERT INTO users (
            id,
            email,
            password_hash,
            first_name,
            last_name,
            created_at,
            updated_at
        )
        SELECT 
            id,
            email,
            password_hash,
            first_name,
            last_name,
            created_at,
            updated_at
        FROM auth_users
        WHERE email IS NOT NULL
        ON CONFLICT (email) DO NOTHING;
    END IF;
END $$;

-- ============================================
-- 12.4 Migrate Documents (if customer_documents exists)
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'customer_documents') THEN
        INSERT INTO documents (
            id,
            organization_id,
            name,
            description,
            file_name,
            file_size,
            mime_type,
            storage_path,
            status,
            created_by,
            created_at,
            updated_at,
            metadata
        )
        SELECT 
            cd.id,
            cd.organization_id,
            cd.file_name,
            cd.file_name, -- Use file name as description
            cd.file_name,
            NULL, -- file_size not available
            cd.file_type,
            cd.file_url,
            COALESCE(cd.status, 'uploaded'),
            NULL, -- created_by not available
            COALESCE(cd.upload_date, NOW()),
            COALESCE(cd.updated_at, NOW()),
            jsonb_build_object(
                'asset_id', cd.asset_id,
                'organization_member_id', cd.organization_member_id,
                'document_type_code', cd.document_type_code,
                'billing_period_start', cd.billing_period_start,
                'billing_period_end', cd.billing_period_end
            )
        FROM customer_documents cd
        WHERE cd.organization_id IS NOT NULL
        ON CONFLICT (id) DO NOTHING;
    END IF;
END $$;

-- ============================================
-- 12.5 Migrate Suppliers (if suppliers exists)
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'suppliers') THEN
        -- Suppliers table already exists, assuming it matches our schema
        -- If not, migration would be needed
        NULL;
    END IF;
END $$;

-- ============================================
-- 12.6 Migrate Emission Factors
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'defra_conversion_factors') THEN
        INSERT INTO emission_factors (
            factor_code,
            source,
            year,
            activity_type,
            scope,
            unit,
            co2e_multiplier,
            created_at,
            updated_at
        )
        SELECT 
            'DEFRA_' || df.reporting_year || '_' || df.activity_type,
            'DEFRA',
            df.reporting_year,
            df.activity_type,
            '1', -- Default scope, adjust as needed
            'unit', -- Default unit, adjust as needed
            df.co2e_multiplier,
            COALESCE(df.created_at, NOW()),
            COALESCE(df.updated_at, NOW())
        FROM defra_conversion_factors df
        WHERE df.co2e_multiplier IS NOT NULL
        ON CONFLICT (factor_code) DO NOTHING;
    END IF;
END $$;

-- ============================================
-- 12.7 Migrate Activity Data (if emissions_logs exists)
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'emissions_logs') THEN
        INSERT INTO activity_data (
            id,
            organization_id,
            document_id,
            emission_factor_id,
            activity_type,
            raw_quantity,
            unit,
            start_date,
            end_date,
            created_by,
            created_at,
            updated_at,
            metadata
        )
        SELECT 
            el.id,
            el.organization_id,
            el.customer_document_id,
            el.defra_factor_id,
            NULL, -- activity_type
            el.raw_quantity,
            NULL, -- unit
            el.start_date,
            el.end_date,
            el.created_by_user_id,
            COALESCE(el.created_at, NOW()),
            COALESCE(el.updated_at, NOW()),
            jsonb_build_object(
                'asset_id', el.asset_id,
                'calculated_kg_co2e', el.calculated_kg_co2e,
                'file_id', el.file_id
            )
        FROM emissions_logs el
        WHERE el.organization_id IS NOT NULL
        ON CONFLICT (id) DO NOTHING;
    END IF;
END $$;

-- ============================================
-- 12.8 Migrate Emission Calculations
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'emissions_logs') THEN
        INSERT INTO emission_calculations (
            activity_data_id,
            calculated_kg_co2e,
            calculated_t_co2e,
            created_at,
            updated_at
        )
        SELECT 
            el.id,
            el.calculated_kg_co2e,
            el.calculated_kg_co2e / 1000, -- Convert kg to tonnes
            COALESCE(el.created_at, NOW()),
            COALESCE(el.updated_at, NOW())
        FROM emissions_logs el
        WHERE el.calculated_kg_co2e IS NOT NULL
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

-- ============================================
-- 12.9 Migrate Manual Review Queue
-- ============================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'manual_review_queue') THEN
        -- Manual reviews table already exists
        -- We'll keep it but link to documents
        UPDATE manual_review_queue mrq
        SET document_id = cd.id
        FROM customer_documents cd
        WHERE mrq.customer_document_id = cd.id
        AND mrq.document_id IS NULL;
    END IF;
END $$;

-- ============================================
-- 12.10 Audit Log Migration
-- ============================================

DO $$
BEGIN
    -- Existing audit logs can be migrated if needed
    -- Adjust based on existing table structure
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        -- If old audit_logs table exists, we assume it matches our schema
        -- or we create a migration
        NULL;
    END IF;
END $$;

-- ============================================
-- 12.11 Cleanup: Drop Deprecated Tables (Post-Migration)
-- ============================================

-- WARNING: Only run after verifying data migration is complete

-- These are kept for backward compatibility during migration
-- They can be dropped after all code is updated

-- DROP TABLE IF EXISTS organization_members CASCADE;
-- DROP TABLE IF EXISTS customer_documents CASCADE;
-- DROP TABLE IF EXISTS defra_conversion_factors CASCADE;
-- DROP TABLE IF EXISTS emissions_logs CASCADE;
-- DROP TABLE IF EXISTS manual_review_queue CASCADE;

-- ============================================
-- ROLLBACK: MIGRATION 012
-- ============================================

-- Not fully reversible due to data transformations
-- Use restore from backup if rollback is needed