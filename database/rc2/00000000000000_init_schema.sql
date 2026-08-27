-- ============================================================================
-- ORGANIZATIONS & USERS
-- ============================================================================

CREATE TABLE public.organizations (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    name varchar NOT NULL,
    company_number varchar UNIQUE,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    logo_url text,
    industry text,
    sector text,
    company_size text,
    vat_number text,
    registration_number text,
    registered_address text,
    country text,
    timezone text,
    currency text,
    financial_year_end date,
    reporting_standard text,
    secr_enabled boolean,
    esrs_enabled boolean,
    issb_enabled boolean,
    default_defra_version integer,
    preferred_units text,
    website text,
    primary_contact_email text,
    primary_contact_name text,
    billing_contact_email text,
    billing_contact_name text,
    subscription_status text,
    trial_start_date timestamptz,
    trial_end_date timestamptz,
    subscription_tier text,
    subscription_id text,
    billing_address text,
    tax_rate numeric,
    metadata jsonb,
    address_line1 varchar,
    address_line2 varchar,
    city varchar,
    county varchar,
    postcode varchar,
    eircode varchar,
    language varchar,
    locale varchar,
    vat_region varchar,
    vat_registered boolean,
    tax_region varchar,
    registration_region varchar,
    sic_code varchar,
    naics_code varchar,
    nace_code varchar,
    business_structure varchar,
    is_public boolean,
    is_listed boolean,
    isin varchar,
    cik varchar,
    sedol varchar,
    lei varchar,
    reporting_frequency varchar,
    accounting_standard varchar,
    sustainability_standard varchar,
    carbon_tax_region varchar,
    data_protection_officer varchar,
    privacy_policy_url text,
    terms_url text
);
COMMENT ON TABLE public.organizations IS 'Organization/tenant root';

CREATE TABLE public.users (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    email varchar UNIQUE NOT NULL,
    password_hash varchar,
    first_name varchar,
    last_name varchar,
    user_type varchar,
    is_active boolean,
    email_verified boolean,
    last_login timestamptz,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
COMMENT ON TABLE public.users IS 'User accounts (auth.users mirror)';

CREATE TABLE public.organization_members (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role varchar NOT NULL,
    created_at timestamptz DEFAULT now(),
    is_active boolean,
    updated_at timestamptz DEFAULT now(),
    CONSTRAINT organization_members_role_check CHECK (role IN ('owner','admin','member','viewer')),
    CONSTRAINT organization_members_org_user_uniq UNIQUE (organization_id, user_id)
);
COMMENT ON TABLE public.organization_members IS 'Organization membership';

CREATE TABLE public.organization_metadata (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id uuid UNIQUE NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    total_employees integer,
    full_time_employees integer,
    part_time_employees integer,
    contract_employees integer,
    average_employees integer,
    annual_revenue numeric,
    ebitda numeric,
    total_assets numeric,
    total_facilities integer,
    total_floor_area_sqft numeric,
    occupied_floor_area_sqft numeric,
    renewable_energy_percentage numeric,
    carbon_offset_percentage numeric,
    energy_intensity numeric,
    reporting_standard varchar,
    fiscal_year_start date,
    fiscal_year_end date,
    primary_contact_name varchar,
    primary_contact_email varchar,
    primary_contact_phone varchar,
    sustainability_officer_name varchar,
    sustainability_officer_email varchar,
    industry_sector varchar,
    naics_code varchar,
    sic_code varchar,
    custom_metrics jsonb,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    updated_by uuid
);
COMMENT ON TABLE public.organization_metadata IS 'Organization extended metadata';
-- ============================================================================
-- CarbonTally BASELINE INITIAL SCHEMA  (SUPABASE / PostgreSQL 16)
-- ============================================================================
-- This file reproduces the AUTHORITATIVE PRE-HARDENING baseline described in
-- `database.txt` as executable SQL. It is the 000000 starting point that the
-- CarbonTally RC2 hardening migrations (001..007 _rc2) are applied against.
--
-- It is deliberately a PRE-HARDENING build:
--   * Table/column shapes exactly match database.txt.
--   * NO RLS is enabled here. RC2 `004_rc2_rls.sql` enables and hardens RLS.
--   * NO performance indexes beyond PK/UNIQUE. RC2 `003_rc2_indexes.sql` adds them.
--   * Explicit CHECK/UNIQUE/FK declared by database.txt are preserved.
--
-- EXTENSIONS are schema-qualified (`extensions.*`) so they work regardless of
-- search_path on a fresh Supabase project.
--
-- EXECUTION ORDER: apply this file, then 001..007 _rc2 IN ORDER, then re-run 007.
-- ============================================================================

-- ============================================================================
-- EXTENSIONS (idempotent; safe on a fresh Supabase project)
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "pgcrypto"  WITH SCHEMA extensions;

-- ============================================================================
-- REFERENCE TABLES
-- ============================================================================

CREATE TABLE public.activity_categories (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    activity_type text UNIQUE NOT NULL,
    esrs_e1_category text,
    issb_category text,
    ghg_protocol_scope text,
    ghg_protocol_category text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
COMMENT ON TABLE public.activity_categories IS 'Activity classification reference data';

CREATE TABLE public.document_types (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    code text UNIQUE NOT NULL,
    name text NOT NULL,
    category text NOT NULL,
    description text,
    file_extensions text[],
    is_active boolean,
    requires_asset boolean,
    requires_date_range boolean,
    requires_facility boolean,
    priority integer,
    metadata jsonb,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
COMMENT ON TABLE public.document_types IS 'Document type reference';

CREATE TABLE public.document_type_categories (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    code varchar UNIQUE NOT NULL,
    name varchar NOT NULL,
    description text,
    category_group varchar,
    default_priority integer,
    requires_facility boolean,
    requires_asset boolean,
    requires_supplier boolean,
    requires_date_range boolean,
    default_defra_activity_type varchar,
    default_scope varchar,
    is_active boolean,
    is_system boolean,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
COMMENT ON TABLE public.document_type_categories IS 'Document type classification reference';

CREATE TABLE public.roles (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    name varchar UNIQUE NOT NULL,
    description text,
    permissions jsonb,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
COMMENT ON TABLE public.roles IS 'Role definitions for RBAC';

CREATE TABLE public.supplier_categories (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    name varchar NOT NULL,
    description text,
    category_group varchar,
    default_emission_factor numeric,
    default_emission_factor_unit varchar,
    ghg_protocol_category varchar,
    is_active boolean,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
COMMENT ON TABLE public.supplier_categories IS 'Supplier category reference';

CREATE TABLE public.product_categories (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id uuid NOT NULL,
    name varchar NOT NULL,
    description text,
    category_type varchar,
    ghg_protocol_scope varchar,
    ghg_protocol_category varchar,
    esrs_e1_category varchar,
    issb_category varchar,
    is_active boolean,
    created_at timestamptz DEFAULT now(),
    created_by uuid,
    updated_at timestamptz DEFAULT now(),
    updated_by uuid,
    metadata jsonb
);
COMMENT ON TABLE public.product_categories IS 'Product categories per organization';

CREATE TABLE public.units (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    code varchar UNIQUE NOT NULL,
    name varchar NOT NULL,
    category varchar NOT NULL,
    symbol varchar,
    conversion_factor numeric,
    is_active boolean,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
COMMENT ON TABLE public.units IS 'Unit of measurement reference';

CREATE TABLE public.email_templates (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    name varchar NOT NULL,
    subject varchar NOT NULL,
    body text NOT NULL,
    type varchar NOT NULL,
    variables text[],
    is_active boolean,
    description text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    created_by uuid,
    updated_by uuid
);
COMMENT ON TABLE public.email_templates IS 'Email template reference';

CREATE TABLE public.notification_templates (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    template_type varchar UNIQUE NOT NULL,
    name varchar NOT NULL,
    subject varchar NOT NULL,
    body text NOT NULL,
    variables jsonb,
    is_active boolean,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    created_by uuid,
    updated_by uuid
);
COMMENT ON TABLE public.notification_templates IS 'Notification template reference';

CREATE TABLE public.glossary (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    term text UNIQUE NOT NULL,
    definition text NOT NULL,
    category text,
    related_terms text[],
    example text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    is_active boolean
);
COMMENT ON TABLE public.glossary IS 'Glossary of terms';
