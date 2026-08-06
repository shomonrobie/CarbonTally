-- =============================================
-- CARBONTALLY - COMPLETE SEED DATA
-- Customers + Internal Staff
-- Date: August 2, 2026
-- =============================================

-- =============================================
-- 1. DEFRA CONVERSION FACTORS
-- =============================================

INSERT INTO defra_conversion_factors (id, reporting_year, activity_type, co2e_multiplier, created_at, updated_at) VALUES
    (gen_random_uuid(), 2025, 'Electricity (UK Grid)', 0.20712, NOW(), NOW()),
    (gen_random_uuid(), 2025, 'Natural Gas (Combustion)', 0.18316, NOW(), NOW()),
    (gen_random_uuid(), 2025, 'Diesel (Combustion)', 2.54, NOW(), NOW()),
    (gen_random_uuid(), 2025, 'Petrol (Combustion)', 2.16, NOW(), NOW()),
    (gen_random_uuid(), 2025, 'Short Haul Flight', 0.155, NOW(), NOW()),
    (gen_random_uuid(), 2025, 'Long Haul Flight', 0.195, NOW(), NOW()),
    (gen_random_uuid(), 2025, 'National Rail', 0.035, NOW(), NOW()),
    (gen_random_uuid(), 2025, 'Hotel Stay', 10.5, NOW(), NOW()),
    (gen_random_uuid(), 2025, 'Mixed Waste (Landfill)', 0.500, NOW(), NOW()),
    (gen_random_uuid(), 2025, 'Recycled Waste', -0.050, NOW(), NOW());

-- =============================================
-- 2. ORGANIZATIONS (10 Customers)
-- =============================================

INSERT INTO organizations (
    id, name, company_number, industry, sector, country, 
    currency, timezone, language, locale,
    vat_number, tax_region, tax_rate, vat_region, vat_registered,
    registration_region, sic_code, naics_code, nace_code,
    business_structure, is_public, is_listed,
    address_line1, city, county, postcode,
    website, primary_contact_name, primary_contact_email,
    reporting_standard, reporting_frequency,
    subscription_tier, subscription_status, trial_start_date,
    created_at, updated_at
) VALUES
(
    gen_random_uuid(), 'Acme Corporation', '12345678', 'Technology', 'Software Development', 'United Kingdom',
    'GBP', 'Europe/London', 'en-GB', 'en_GB',
    'GB123456789', 'UK', 20.0, 'UK', true,
    'UK', '62020', '541512', '62.01',
    'Limited Company', false, false,
    '123 High Street', 'London', 'Greater London', 'EC1A 1AA',
    'https://acme.com', 'Sarah Johnson', 'sarah.johnson@acme.com',
    'SECR', 'annual',
    'enterprise', 'active', CURRENT_DATE - INTERVAL '365 days',
    CURRENT_DATE - INTERVAL '365 days', CURRENT_DATE
),
(
    gen_random_uuid(), 'TechCorp Ltd', '87654321', 'Technology', 'IT Services', 'United Kingdom',
    'GBP', 'Europe/London', 'en-GB', 'en_GB',
    'GB987654321', 'UK', 20.0, 'UK', true,
    'UK', '62020', '541512', '62.01',
    'Limited Company', false, false,
    '456 Oxford Street', 'Manchester', 'Greater Manchester', 'M1 1AA',
    'https://techcorp.co.uk', 'Mike Thompson', 'mike.thompson@techcorp.co.uk',
    'SECR', 'annual',
    'professional', 'active', CURRENT_DATE - INTERVAL '300 days',
    CURRENT_DATE - INTERVAL '300 days', CURRENT_DATE
),
(
    gen_random_uuid(), 'GreenEnergy Solutions', 'IE123456', 'Energy', 'Renewable Energy', 'Ireland',
    'EUR', 'Europe/Dublin', 'en-IE', 'en_IE',
    'IE123456789', 'IE', 23.0, 'IE', true,
    'IE', '35110', '221122', '35.11',
    'Limited Company', false, false,
    '42 Main Street', 'Dublin', 'County Dublin', 'D02 XY12',
    'https://greenenergy.ie', 'Emma Walsh', 'emma.walsh@greenenergy.ie',
    'CSRD', 'annual',
    'enterprise', 'active', CURRENT_DATE - INTERVAL '400 days',
    CURRENT_DATE - INTERVAL '400 days', CURRENT_DATE
),
(
    gen_random_uuid(), 'EcoBuild Ltd', 'IE654321', 'Construction', 'Green Building', 'Ireland',
    'EUR', 'Europe/Dublin', 'en-IE', 'en_IE',
    'IE987654321', 'IE', 23.0, 'IE', true,
    'IE', '41220', '236220', '41.22',
    'Limited Company', false, false,
    '5 Grand Canal Quay', 'Dublin', 'County Dublin', 'D02 XY34',
    'https://ecobuild.ie', 'John O''Brien', 'john.obrien@ecobuild.ie',
    'CSRD', 'annual',
    'professional', 'active', CURRENT_DATE - INTERVAL '250 days',
    CURRENT_DATE - INTERVAL '250 days', CURRENT_DATE
),
(
    gen_random_uuid(), 'EuroLogistics GmbH', 'DE12345678', 'Logistics', 'Freight Transport', 'Germany',
    'EUR', 'Europe/Berlin', 'de-DE', 'de_DE',
    'DE123456789', 'EU', 19.0, 'EU', true,
    'DE', '49410', '484121', '49.41',
    'GmbH', false, false,
    'Alexanderstrasse 12', 'Berlin', 'Berlin', '10115',
    'https://eurologistics.de', 'Klaus Schmidt', 'klaus.schmidt@eurologistics.de',
    'CSRD', 'annual',
    'enterprise', 'active', CURRENT_DATE - INTERVAL '200 days',
    CURRENT_DATE - INTERVAL '200 days', CURRENT_DATE
),
(
    gen_random_uuid(), 'PharmaCare SA', 'FR12345678', 'Pharmaceuticals', 'Healthcare', 'France',
    'EUR', 'Europe/Paris', 'fr-FR', 'fr_FR',
    'FR123456789', 'EU', 20.0, 'EU', true,
    'FR', '21100', '325412', '21.10',
    'SA', false, false,
    '25 Rue de Rivoli', 'Paris', 'Île-de-France', '75001',
    'https://pharmacare.fr', 'Marie Dubois', 'marie.dubois@pharmacare.fr',
    'CSRD', 'annual',
    'professional', 'active', CURRENT_DATE - INTERVAL '180 days',
    CURRENT_DATE - INTERVAL '180 days', CURRENT_DATE
),
(
    gen_random_uuid(), 'NordicTech Oyj', 'FI12345678', 'Technology', 'Software', 'Finland',
    'EUR', 'Europe/Helsinki', 'fi-FI', 'fi_FI',
    'FI123456789', 'EU', 24.0, 'EU', true,
    'FI', '62020', '541512', '62.01',
    'Oyj', false, false,
    'Mannerheimintie 10', 'Helsinki', 'Uusimaa', '00100',
    'https://nordictech.fi', 'Anna Mäkelä', 'anna.makela@nordictech.fi',
    'CSRD', 'annual',
    'enterprise', 'active', CURRENT_DATE - INTERVAL '150 days',
    CURRENT_DATE - INTERVAL '150 days', CURRENT_DATE
),
(
    gen_random_uuid(), 'Midland Manufacturing Ltd', '23456789', 'Manufacturing', 'Industrial', 'United Kingdom',
    'GBP', 'Europe/London', 'en-GB', 'en_GB',
    'GB234567890', 'UK', 20.0, 'UK', true,
    'UK', '25110', '332710', '25.11',
    'Limited Company', false, false,
    'Unit 4, Industrial Estate', 'Birmingham', 'West Midlands', 'B1 1AA',
    'https://midlandmfg.co.uk', 'David Williams', 'david.williams@midlandmfg.co.uk',
    'SECR', 'annual',
    'professional', 'active', CURRENT_DATE - INTERVAL '120 days',
    CURRENT_DATE - INTERVAL '120 days', CURRENT_DATE
),
(
    gen_random_uuid(), 'RetailCorp Group', '34567890', 'Retail', 'E-commerce', 'United Kingdom',
    'GBP', 'Europe/London', 'en-GB', 'en_GB',
    'GB345678901', 'UK', 20.0, 'UK', true,
    'UK', '47910', '454110', '47.91',
    'Limited Company', false, false,
    '1 High Street', 'Leeds', 'West Yorkshire', 'LS1 1AA',
    'https://retailcorp.co.uk', 'Laura Smith', 'laura.smith@retailcorp.co.uk',
    'SECR', 'annual',
    'starter', 'active', CURRENT_DATE - INTERVAL '90 days',
    CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE
),
(
    gen_random_uuid(), 'DataVision AI Ltd', '45678901', 'Technology', 'Artificial Intelligence', 'United Kingdom',
    'GBP', 'Europe/London', 'en-GB', 'en_GB',
    'GB456789012', 'UK', 20.0, 'UK', true,
    'UK', '62020', '541512', '62.01',
    'Limited Company', false, false,
    'King''s Cross, 25', 'London', 'Greater London', 'N1C 4AB',
    'https://datavision.ai', 'Peter Chen', 'peter.chen@datavision.ai',
    'SECR', 'annual',
    'professional', 'active', CURRENT_DATE - INTERVAL '60 days',
    CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE
);

-- =============================================
-- 3. ORGANIZATION MEMBERS (Using existing users)
-- =============================================
INSERT INTO organization_members (
    id, organization_id, user_id, role, 
    is_active, created_at, updated_at
) VALUES
    -- Acme Corporation
    (gen_random_uuid(), (SELECT id FROM organizations WHERE name = 'Acme Corporation'), 'f5c20f3f-ebb3-48fb-b799-7847ed8784f4', 'admin', true, NOW(), NOW()),
    -- TechCorp Ltd
    (gen_random_uuid(), (SELECT id FROM organizations WHERE name = 'TechCorp Ltd'), '6e787668-082b-47be-a8ba-aa7b09c2c322', 'admin', true, NOW(), NOW()),
    -- GreenEnergy Solutions
    (gen_random_uuid(), (SELECT id FROM organizations WHERE name = 'GreenEnergy Solutions'), 'd632d399-da60-48b8-b685-9504fcf1479c', 'admin', true, NOW(), NOW()),
    -- EcoBuild Ltd
    (gen_random_uuid(), (SELECT id FROM organizations WHERE name = 'EcoBuild Ltd'), 'efbe0c33-1545-4a73-8ca8-874fb529b326', 'admin', true, NOW(), NOW()),
    -- EuroLogistics GmbH
    (gen_random_uuid(), (SELECT id FROM organizations WHERE name = 'EuroLogistics GmbH'), '55251ae2-3093-4b4a-b962-908bf22cfaf1', 'admin', true, NOW(), NOW()),
    -- PharmaCare SA
    (gen_random_uuid(), (SELECT id FROM organizations WHERE name = 'PharmaCare SA'), 'e39dbe58-be4c-4ffa-90a7-6ab5355cc7bb', 'admin', true, NOW(), NOW()),
    -- NordicTech Oyj
    (gen_random_uuid(), (SELECT id FROM organizations WHERE name = 'NordicTech Oyj'), '8e752ef2-4f7d-41c2-afca-b761890569ae', 'admin', true, NOW(), NOW()),
    -- Midland Manufacturing Ltd
    (gen_random_uuid(), (SELECT id FROM organizations WHERE name = 'Midland Manufacturing Ltd'), '74a214b1-d32b-41ca-9c3d-a1e87e0a6a4d', 'admin', true, NOW(), NOW()),
    -- RetailCorp Group
    (gen_random_uuid(), (SELECT id FROM organizations WHERE name = 'RetailCorp Group'), '6757f2e9-5790-4dfc-be14-f2041fbd786c', 'admin', true, NOW(), NOW()),
    -- DataVision AI Ltd
    (gen_random_uuid(), (SELECT id FROM organizations WHERE name = 'DataVision AI Ltd'), '6d9d7dbe-1e6e-4c1d-b9f2-ae337f31a07d', 'admin', true, NOW(), NOW());

-- =============================================
-- 4. FACILITIES
-- =============================================

WITH orgs AS (
    SELECT id, name FROM organizations
)
INSERT INTO facilities (
    id, organization_id, name, type, 
    address_line1, city, county, postcode, country,
    latitude, longitude, is_active, created_at
)
SELECT 
    gen_random_uuid(),
    orgs.id,
    facility_name,
    facility_type,
    address,
    city,
    county,
    postcode,
    country,
    lat,
    lng,
    true,
    CURRENT_DATE - INTERVAL '30 days'
FROM orgs
CROSS JOIN LATERAL (
    VALUES 
        (orgs.name || ' Headquarters', 'office', 
         '123 Main Street', 'London', 'Greater London', 'EC1A 1AA', 'United Kingdom', 51.5074, -0.1278),
        (orgs.name || ' Northern Hub', 'office',
         '456 Business Park', 'Manchester', 'Greater Manchester', 'M1 1AA', 'United Kingdom', 53.4808, -2.2426),
        (orgs.name || ' Data Center', 'data_center',
         '789 Tech Road', 'Slough', 'Berkshire', 'SL1 1AA', 'United Kingdom', 51.5105, -0.5954),
        (orgs.name || ' Warehouse', 'warehouse',
         'Unit 12, Industrial Estate', 'Birmingham', 'West Midlands', 'B1 1AA', 'United Kingdom', 52.4862, -1.8904)
) AS f(facility_name, facility_type, address, city, county, postcode, country, lat, lng);

-- =============================================
-- 5. ASSETS
-- =============================================

WITH facilities_cte AS (
    SELECT id, organization_id FROM facilities
)
INSERT INTO assets (
    id, facility_id, organization_id, name, type, description,
    capacity, capacity_unit, serial_number, installation_date,
    is_active, created_at
)
SELECT 
    gen_random_uuid(),
    f.id,
    f.organization_id,
    asset_name,
    asset_type,
    asset_type || ' unit',
    capacity,
    'kW',
    'SN-' || LPAD(generate_series::text, 6, '0'),
    CURRENT_DATE - INTERVAL '5 years',
    true,
    CURRENT_DATE - INTERVAL '365 days'
FROM facilities_cte f
CROSS JOIN LATERAL (
    VALUES 
        ('Boiler 1', 'boiler', 500),
        ('AC System 1', 'ac', 200),
        ('Generator 1', 'generator', 1000),
        ('HVAC System 1', 'hvac', 300),
        ('Lighting System 1', 'lighting', 150),
        ('Vehicle 1', 'vehicle', 100),
        ('Solar Panel 1', 'solar', 50),
        ('Battery Storage 1', 'battery', 250)
) AS a(asset_name, asset_type, capacity)
CROSS JOIN LATERAL generate_series(1, 1) AS generate_series
LIMIT 80;

-- =============================================
-- 6. SUPPLIERS
-- =============================================

WITH orgs AS (
    SELECT id FROM organizations
)
INSERT INTO suppliers (
    id, organization_id, name, type,
    address_line1, city, county, postcode, country,
    contact_name, contact_email, contact_phone,
    is_active, created_at
)
SELECT 
    gen_random_uuid(),
    orgs.id,
    supplier_name,
    supplier_type,
    address,
    city,
    county,
    postcode,
    country,
    'Contact Name',
    'contact@' || LOWER(REPLACE(supplier_name, ' ', '')) || '.com',
    '+44 20 1234 5678',
    true,
    CURRENT_DATE - INTERVAL '30 days'
FROM orgs
CROSS JOIN LATERAL (
    VALUES 
        ('EnergyCo', 'energy', '123 Power Street', 'London', 'Greater London', 'EC1A 1AA', 'United Kingdom'),
        ('GasCo', 'gas', '456 Gas Road', 'Manchester', 'Greater Manchester', 'M1 1AA', 'United Kingdom'),
        ('FuelCo', 'fuel', '789 Fuel Lane', 'Birmingham', 'West Midlands', 'B1 1AA', 'United Kingdom')
) AS s(supplier_name, supplier_type, address, city, county, postcode, country);

-- =============================================
-- 7. CUSTOMER DOCUMENTS
-- =============================================

WITH orgs AS (
    SELECT 
        o.id as organization_id,
        (SELECT a.id FROM assets a WHERE a.organization_id = o.id LIMIT 1) as asset_id,
        (SELECT om.id FROM organization_members om WHERE om.organization_id = o.id LIMIT 1) as member_id
    FROM organizations o
),
doc_types AS (
    SELECT unnest(ARRAY[
        'utility', 'electricity', 'gas', 'fuel_card', 'waste_manifest',
        'travel_expense', 'flight', 'accommodation', 'general', 'water'
    ]) as doc_type
)
INSERT INTO customer_documents (
    id, organization_id, organization_member_id, asset_id,
    file_name, file_url, file_type, document_type_code,
    upload_date, status, confidence_score,
    billing_period_start, billing_period_end,
    calculated_emissions_kg_co2e,
    created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    orgs.organization_id,
    orgs.member_id,
    orgs.asset_id,
    doc_types.doc_type || '_' || LPAD(generate_series::text, 4, '0') || '.pdf',
    'https://storage.carbontally.com/documents/' || orgs.organization_id::text || '/' || doc_types.doc_type || '_' || LPAD(generate_series::text, 4, '0') || '.pdf',
    CASE 
        WHEN doc_types.doc_type IN ('utility', 'electricity', 'gas', 'water') THEN 'invoice'
        WHEN doc_types.doc_type IN ('fuel_card') THEN 'fuel_slip'
        WHEN doc_types.doc_type IN ('waste_manifest', 'travel_expense', 'flight', 'accommodation') THEN 'maintenance'
        ELSE 'other'
    END,
    doc_types.doc_type,
    CURRENT_DATE - (generate_series || ' days')::interval,
    CASE (generate_series % 5)
        WHEN 0 THEN 'approved'
        WHEN 1 THEN 'pending'
        WHEN 2 THEN 'processing'
        WHEN 3 THEN 'extracted'
        ELSE 'pending'
    END,
    (70 + (generate_series % 25))::float / 100,
    CURRENT_DATE - ((generate_series + 30) || ' days')::interval,
    CURRENT_DATE - ((generate_series + 15) || ' days')::interval,
    (100 + generate_series * 50)::numeric(10,2),
    CURRENT_DATE - (generate_series || ' days')::interval,
    CURRENT_DATE - ((generate_series - 5) || ' days')::interval
FROM orgs
CROSS JOIN doc_types
CROSS JOIN LATERAL generate_series(1, 20) AS generate_series
LIMIT 200;

-- =============================================
-- 8. EMISSIONS LOGS
-- =============================================

WITH orgs AS (
    SELECT 
        o.id as organization_id,
        (SELECT a.id FROM assets a WHERE a.organization_id = o.id LIMIT 1) as asset_id,
        (SELECT d.id FROM defra_conversion_factors d WHERE d.activity_type = 'Electricity (UK Grid)' LIMIT 1) as defra_factor_id,
        (SELECT om.id FROM organization_members om WHERE om.organization_id = o.id LIMIT 1) as member_id
    FROM organizations o
    LIMIT 5
)
INSERT INTO emissions_logs (
    id, organization_id, asset_id, defra_factor_id,
    start_date, end_date, raw_quantity, calculated_kg_co2e,
    created_by_user_id, created_at, updated_at,
    data_source, confidence_score
)
SELECT 
    gen_random_uuid(),
    orgs.organization_id,
    orgs.asset_id,
    orgs.defra_factor_id,
    CURRENT_DATE - '90 days'::interval,
    CURRENT_DATE - '60 days'::interval,
    (100 + (generate_series % 10) * 100)::numeric(10,2),
    ((100 + (generate_series % 10) * 100) * 0.207)::numeric(10,2),
    orgs.member_id,
    CURRENT_DATE - '90 days'::interval,
    CURRENT_DATE - '60 days'::interval,
    'document_auto',
    (70 + (generate_series % 25))::numeric(5,2)
FROM orgs
CROSS JOIN LATERAL generate_series(1, 3) AS generate_series
LIMIT 15;

-- =============================================
-- 9. CARBONTALLY INTERNAL STAFF
-- =============================================

-- Insert staff users first
INSERT INTO users (
    id, email, first_name, last_name, user_type, 
    is_active, email_verified, created_at, updated_at
) VALUES
    (gen_random_uuid(), 'admin@carbontally.com', 'Admin', 'User', 'staff', true, true, CURRENT_DATE - INTERVAL '365 days', CURRENT_DATE),
    (gen_random_uuid(), 'manager@carbontally.com', 'Manager', 'User', 'staff', true, true, CURRENT_DATE - INTERVAL '300 days', CURRENT_DATE),
    (gen_random_uuid(), 'approver1@carbontally.com', 'Senior', 'Approver', 'staff', true, true, CURRENT_DATE - INTERVAL '250 days', CURRENT_DATE),
    (gen_random_uuid(), 'qc1@carbontally.com', 'QC', 'Specialist', 'staff', true, true, CURRENT_DATE - INTERVAL '200 days', CURRENT_DATE),
    (gen_random_uuid(), 'qc2@carbontally.com', 'Quality', 'Control', 'staff', true, true, CURRENT_DATE - INTERVAL '180 days', CURRENT_DATE),
    (gen_random_uuid(), 'extractor1@carbontally.com', 'Data', 'Extractor', 'staff', true, true, CURRENT_DATE - INTERVAL '150 days', CURRENT_DATE),
    (gen_random_uuid(), 'extractor2@carbontally.com', 'Extraction', 'Pro', 'staff', true, true, CURRENT_DATE - INTERVAL '120 days', CURRENT_DATE),
    (gen_random_uuid(), 'extractor3@carbontally.com', 'Extractor', 'Junior', 'staff', true, true, CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE),
    (gen_random_uuid(), 'viewer1@carbontally.com', 'Viewer', 'User', 'staff', true, true, CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE),
    (gen_random_uuid(), 'staff1@carbontally.com', 'Staff', 'Member', 'staff', true, true, CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE);

-- =============================================
-- 10. STAFF ROLES
-- =============================================

INSERT INTO staff_roles (id, name, description, permissions, is_active, created_at, updated_at) VALUES
    (gen_random_uuid(), 'admin', 'Full system access', '{"all": true}'::jsonb, true, NOW(), NOW()),
    (gen_random_uuid(), 'manager', 'Manage team and workload', '{"manage_team": true, "view_all": true, "assign": true}'::jsonb, true, NOW(), NOW()),
    (gen_random_uuid(), 'approver', 'Approve QC and final documents', '{"approve": true, "view_all": true}'::jsonb, true, NOW(), NOW()),
    (gen_random_uuid(), 'qc', 'Quality control reviews', '{"qc": true, "view_all": true}'::jsonb, true, NOW(), NOW()),
    (gen_random_uuid(), 'extractor', 'Document extraction and mapping', '{"extract": true, "map": true}'::jsonb, true, NOW(), NOW()),
    (gen_random_uuid(), 'viewer', 'Read-only access', '{"view": true}'::jsonb, true, NOW(), NOW());

-- =============================================
-- 11. STAFF PROFILES
-- =============================================

WITH staff_roles AS (
    SELECT id, name FROM staff_roles
)
INSERT INTO staff_profiles (
    id, user_id, first_name, last_name, email, role_id,
    is_active, hire_date, skills, max_concurrent_tasks,
    created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    u.id,
    u.first_name,
    u.last_name,
    u.email,
    sr.id,
    true,
    CASE 
        WHEN u.email = 'admin@carbontally.com' THEN CURRENT_DATE - INTERVAL '365 days'
        WHEN u.email = 'manager@carbontally.com' THEN CURRENT_DATE - INTERVAL '300 days'
        WHEN u.email LIKE 'extractor%' THEN CURRENT_DATE - INTERVAL '150 days'
        ELSE CURRENT_DATE - INTERVAL '90 days'
    END,
    CASE 
        WHEN u.email LIKE 'extractor%' THEN '["utility", "fuel", "waste"]'::jsonb
        WHEN u.email LIKE 'qc%' THEN '["utility", "fuel", "waste", "travel"]'::jsonb
        ELSE '["all"]'::jsonb
    END,
    CASE 
        WHEN u.email LIKE 'extractor%' THEN 5
        WHEN u.email LIKE 'qc%' THEN 3
        WHEN u.email = 'admin@carbontally.com' THEN 10
        ELSE 4
    END,
    CURRENT_DATE - INTERVAL '30 days',
    CURRENT_DATE - INTERVAL '30 days'
FROM users u
JOIN staff_roles sr ON sr.name = CASE 
    WHEN u.email = 'admin@carbontally.com' THEN 'admin'
    WHEN u.email = 'manager@carbontally.com' THEN 'manager'
    WHEN u.email = 'approver1@carbontally.com' THEN 'approver'
    WHEN u.email = 'qc1@carbontally.com' THEN 'qc'
    WHEN u.email = 'qc2@carbontally.com' THEN 'qc'
    WHEN u.email LIKE 'extractor%' THEN 'extractor'
    WHEN u.email = 'viewer1@carbontally.com' THEN 'viewer'
    ELSE 'extractor'
END
WHERE u.user_type = 'staff';

-- =============================================
-- 12. STAFF WORKLOAD
-- =============================================

WITH staff_list AS (
    SELECT id FROM staff_profiles
)
INSERT INTO staff_workload (
    id, staff_id, assigned_tasks, in_progress_tasks, pending_tasks,
    completed_today, workload_score, capacity_percentage,
    date, updated_at
)
SELECT 
    gen_random_uuid(),
    s.id,
    (1 + (random() * 8))::int,
    (1 + (random() * 4))::int,
    (1 + (random() * 3))::int,
    (1 + (random() * 5))::int,
    (20 + (random() * 60))::numeric(5,2),
    (30 + (random() * 50))::numeric(5,2),
    CURRENT_DATE,
    CURRENT_DATE
FROM staff_list s
CROSS JOIN LATERAL generate_series(1, 1) AS g;

-- =============================================
-- 13. STAFF PERFORMANCE
-- =============================================

WITH staff_list AS (
    SELECT id FROM staff_profiles
)
INSERT INTO staff_performance (
    id, staff_id, period_start, period_end, period_type,
    total_assigned, total_completed, total_rejected,
    avg_processing_time_seconds, qc_pass_rate, accuracy_rate, productivity_score,
    created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    s.id,
    DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month',
    DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 day',
    'monthly',
    (10 + (random() * 40))::int,
    (5 + (random() * 30))::int,
    (1 + (random() * 3))::int,
    (300 + (random() * 1200))::int,
    (60 + (random() * 35))::numeric(5,2),
    (70 + (random() * 25))::numeric(5,2),
    (50 + (random() * 40))::numeric(5,2),
    CURRENT_DATE - INTERVAL '30 days',
    CURRENT_DATE - INTERVAL '30 days'
FROM staff_list s
CROSS JOIN LATERAL generate_series(1, 1) AS g;

-- =============================================
-- 14. PROCESSING QUEUE (For admin dashboard)
-- =============================================

WITH orgs AS (
    SELECT id, (SELECT id FROM customer_documents WHERE organization_id = organizations.id LIMIT 1) as doc_id
    FROM organizations 
    WHERE id IN (SELECT id FROM organizations LIMIT 5)
)
INSERT INTO processing_queue (
    id, document_id, organization_id, document_type, priority,
    priority_score, queue_status, sla_deadline, sla_breached,
    estimated_completion_hours, page_count, file_size_bytes,
    created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    doc_id,
    orgs.id,
    CASE (generate_series % 3)
        WHEN 0 THEN 'utility'
        WHEN 1 THEN 'fuel'
        ELSE 'waste'
    END,
    (generate_series % 3) + 1,
    (generate_series % 5) * 10,
    CASE (generate_series % 4)
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'assigned'
        WHEN 2 THEN 'in_progress'
        ELSE 'completed'
    END,
    CURRENT_DATE + ((generate_series % 5) || ' days')::interval,
    CASE WHEN generate_series % 5 = 0 THEN true ELSE false END,
    (generate_series % 24) + 4,
    (generate_series % 10) + 1,
    1024 * 1024 * (generate_series % 5 + 1),
    CURRENT_DATE - ((generate_series * 2) || ' days')::interval,
    CURRENT_DATE - ((generate_series) || ' days')::interval
FROM orgs
CROSS JOIN LATERAL generate_series(1, 5) AS generate_series
WHERE doc_id IS NOT NULL
LIMIT 25;

-- =============================================
-- 15. CONSULTANT PROFILES
-- =============================================

INSERT INTO consultant_profiles (
    id, user_id, company_name, company_number,
    address_line1, city, county, postcode, country,
    website, phone, brand_name,
    firm_type, firm_size, industries_served, expertise,
    partner_since, partner_status, partner_tier,
    created_at, updated_at
) VALUES
(
    gen_random_uuid(), (SELECT id FROM users WHERE email = 'sarah.johnson@acme.com'), 'EcoSustain Advisors', 'CS123456',
    '1 Green Street', 'London', 'Greater London', 'EC1A 1AA', 'United Kingdom',
    'https://ecosustain.com', '+44 20 1234 5678', 'EcoSustain',
    'consultancy', '10-50', ARRAY['technology', 'finance', 'energy']::text[], ARRAY['carbon accounting', 'ESG reporting', 'SECR']::text[],
    CURRENT_DATE - INTERVAL '365 days', 'active', 'gold',
    CURRENT_DATE - INTERVAL '365 days', CURRENT_DATE
),
(
    gen_random_uuid(), (SELECT id FROM users WHERE email = 'mike.thompson@techcorp.co.uk'), 'CarbonWise Consulting', 'CW789012',
    '2 Sustainability Lane', 'Manchester', 'Greater Manchester', 'M1 1AA', 'United Kingdom',
    'https://carbonwise.co.uk', '+44 20 1234 5679', 'CarbonWise',
    'consultancy', '10-50', ARRAY['manufacturing', 'retail']::text[], ARRAY['carbon footprint', 'lifecycle analysis']::text[],
    CURRENT_DATE - INTERVAL '300 days', 'active', 'silver',
    CURRENT_DATE - INTERVAL '300 days', CURRENT_DATE
),
(
    gen_random_uuid(), (SELECT id FROM users WHERE email = 'emma.walsh@greenenergy.ie'), 'GreenShift Advisors', 'IE123456',
    '3 Green Park', 'Dublin', 'County Dublin', 'D02 XY12', 'Ireland',
    'https://greenshift.ie', '+353 1 234 5678', 'GreenShift',
    'consultancy', '5-10', ARRAY['energy', 'construction']::text[], ARRAY['CSRD', 'ESG']::text[],
    CURRENT_DATE - INTERVAL '250 days', 'active', 'silver',
    CURRENT_DATE - INTERVAL '250 days', CURRENT_DATE
),
(
    gen_random_uuid(), (SELECT id FROM users WHERE email = 'john.obrien@ecobuild.ie'), 'EcoBuild Advisory', 'IE654321',
    '4 Eco Street', 'Cork', 'County Cork', 'T12 XY34', 'Ireland',
    'https://ecobuild.ie', '+353 1 234 5679', 'EcoBuild',
    'consultancy', '5-10', ARRAY['construction', 'property']::text[], ARRAY['green building', 'carbon reduction']::text[],
    CURRENT_DATE - INTERVAL '200 days', 'active', 'bronze',
    CURRENT_DATE - INTERVAL '200 days', CURRENT_DATE
),
(
    gen_random_uuid(), (SELECT id FROM users WHERE email = 'klaus.schmidt@eurologistics.de'), 'CarbonLogistics GmbH', 'DE123456',
    '5 Logistics Way', 'Berlin', 'Berlin', '10115', 'Germany',
    'https://carbonlogistics.de', '+49 30 1234 5678', 'CarbonLogistics',
    'consultancy', '10-50', ARRAY['logistics', 'transport']::text[], ARRAY['supply chain', 'fleet emissions']::text[],
    CURRENT_DATE - INTERVAL '180 days', 'active', 'silver',
    CURRENT_DATE - INTERVAL '180 days', CURRENT_DATE
),
(
    gen_random_uuid(), (SELECT id FROM users WHERE email = 'marie.dubois@pharmacare.fr'), 'PharmaCarbon SA', 'FR123456',
    '6 Rue de Paris', 'Paris', 'Île-de-France', '75001', 'France',
    'https://pharmacarbon.fr', '+33 1 2345 6789', 'PharmaCarbon',
    'consultancy', '5-10', ARRAY['pharmaceuticals', 'healthcare']::text[], ARRAY['CSRD', 'Scope 3']::text[],
    CURRENT_DATE - INTERVAL '150 days', 'active', 'bronze',
    CURRENT_DATE - INTERVAL '150 days', CURRENT_DATE
),
(
    gen_random_uuid(), (SELECT id FROM users WHERE email = 'anna.makela@nordictech.fi'), 'NordicCarbon Oyj', 'FI123456',
    '7 Helsinki Street', 'Helsinki', 'Uusimaa', '00100', 'Finland',
    'https://nordiccarbon.fi', '+358 9 1234 5678', 'NordicCarbon',
    'consultancy', '10-50', ARRAY['technology', 'forestry']::text[], ARRAY['net zero', 'carbon offsets']::text[],
    CURRENT_DATE - INTERVAL '120 days', 'active', 'gold',
    CURRENT_DATE - INTERVAL '120 days', CURRENT_DATE
),
(
    gen_random_uuid(), (SELECT id FROM users WHERE email = 'david.williams@midlandmfg.co.uk'), 'Midland Carbon Solutions', 'CS234567',
    '8 Industrial Road', 'Birmingham', 'West Midlands', 'B1 1AA', 'United Kingdom',
    'https://midlandcarbon.co.uk', '+44 20 1234 5680', 'Midland Carbon',
    'consultancy', '5-10', ARRAY['manufacturing', 'engineering']::text[], ARRAY['industrial emissions', 'energy efficiency']::text[],
    CURRENT_DATE - INTERVAL '90 days', 'active', 'silver',
    CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE
),
(
    gen_random_uuid(), (SELECT id FROM users WHERE email = 'laura.smith@retailcorp.co.uk'), 'RetailCarbon Advisors', 'CS345678',
    '9 Retail Street', 'Leeds', 'West Yorkshire', 'LS1 1AA', 'United Kingdom',
    'https://retailcarbon.co.uk', '+44 20 1234 5681', 'RetailCarbon',
    'consultancy', '5-10', ARRAY['retail', 'consumer goods']::text[], ARRAY['supply chain', 'scope 3']::text[],
    CURRENT_DATE - INTERVAL '60 days', 'active', 'bronze',
    CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE
),
(
    gen_random_uuid(), (SELECT id FROM users WHERE email = 'peter.chen@datavision.ai'), 'DataCarbon AI', 'CS456789',
    '10 AI Street', 'London', 'Greater London', 'N1C 4AB', 'United Kingdom',
    'https://datacarbon.ai', '+44 20 1234 5682', 'DataCarbon',
    'consultancy', '5-10', ARRAY['technology', 'AI']::text[], ARRAY['AI for carbon', 'data analytics']::text[],
    CURRENT_DATE - INTERVAL '30 days', 'active', 'silver',
    CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE
);

-- =============================================
-- 16. CONSULTANT FIRM MEMBERS
-- =============================================

INSERT INTO consultant_firm_members (
    id, firm_id, user_id, role, 
    can_manage_clients, can_upload_documents, can_generate_reports, can_manage_team,
    is_active, invited_at, joined_at, created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    cp.id,
    u.id,
    role_arr[1 + (ROW_NUMBER() OVER (PARTITION BY cp.id ORDER BY 1) % 3)],
    true,
    true,
    true,
    false,
    true,
    CURRENT_DATE - '30 days'::interval,
    CURRENT_DATE - '30 days'::interval,
    CURRENT_DATE - '30 days'::interval,
    CURRENT_DATE - '30 days'::interval
FROM consultant_profiles cp
CROSS JOIN LATERAL (
    VALUES ('consultant'), ('analyst'), ('intern'), ('consultant'), ('analyst')
) AS r(role_arr)
CROSS JOIN LATERAL (
    SELECT id FROM users WHERE user_type = 'company_user' 
    AND id NOT IN (SELECT user_id FROM consultant_firm_members)
    LIMIT 3
) u
WHERE (SELECT count(*) FROM consultant_firm_members WHERE firm_id = cp.id) < 3
LIMIT 30;

-- =============================================
-- 17. CONSULTANT CLIENTS
-- =============================================

INSERT INTO consultant_clients (
    id, consultant_id, organization_id, client_name, client_industry,
    client_contact_email, client_contact_name, status,
    billing_plan, billing_cycle, created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    cp.id,
    o.id,
    o.name,
    o.industry,
    o.primary_contact_email,
    o.primary_contact_name,
    'active',
    'professional',
    'monthly',
    CURRENT_DATE - '30 days'::interval,
    CURRENT_DATE - '30 days'::interval
FROM consultant_profiles cp
CROSS JOIN LATERAL (
    SELECT o.id, o.name, o.industry, o.primary_contact_email, o.primary_contact_name
    FROM organizations o
    WHERE o.id NOT IN (
        SELECT organization_id FROM consultant_clients WHERE consultant_id = cp.id
    )
    ORDER BY o.id
    LIMIT 5
) o
WHERE (SELECT count(*) FROM consultant_clients WHERE consultant_id = cp.id) < 5
LIMIT 50;