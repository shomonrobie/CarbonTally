-- =============================================
-- CREATE USERS FIRST (If not already done)
-- =============================================

INSERT INTO users (
    id, email, first_name, last_name, user_type, 
    is_active, email_verified, created_at, updated_at
) VALUES
    (gen_random_uuid(), 'sarah.johnson@acme.com', 'Sarah', 'Johnson', 'company_user', true, true, CURRENT_DATE - INTERVAL '365 days', CURRENT_DATE),
    (gen_random_uuid(), 'mike.thompson@techcorp.co.uk', 'Mike', 'Thompson', 'company_user', true, true, CURRENT_DATE - INTERVAL '300 days', CURRENT_DATE),
    (gen_random_uuid(), 'emma.walsh@greenenergy.ie', 'Emma', 'Walsh', 'company_user', true, true, CURRENT_DATE - INTERVAL '400 days', CURRENT_DATE),
    (gen_random_uuid(), 'john.obrien@ecobuild.ie', 'John', 'O''Brien', 'company_user', true, true, CURRENT_DATE - INTERVAL '250 days', CURRENT_DATE),
    (gen_random_uuid(), 'klaus.schmidt@eurologistics.de', 'Klaus', 'Schmidt', 'company_user', true, true, CURRENT_DATE - INTERVAL '200 days', CURRENT_DATE),
    (gen_random_uuid(), 'marie.dubois@pharmacare.fr', 'Marie', 'Dubois', 'company_user', true, true, CURRENT_DATE - INTERVAL '180 days', CURRENT_DATE),
    (gen_random_uuid(), 'anna.makela@nordictech.fi', 'Anna', 'Mäkelä', 'company_user', true, true, CURRENT_DATE - INTERVAL '150 days', CURRENT_DATE),
    (gen_random_uuid(), 'david.williams@midlandmfg.co.uk', 'David', 'Williams', 'company_user', true, true, CURRENT_DATE - INTERVAL '120 days', CURRENT_DATE),
    (gen_random_uuid(), 'laura.smith@retailcorp.co.uk', 'Laura', 'Smith', 'company_user', true, true, CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE),
    (gen_random_uuid(), 'peter.chen@datavision.ai', 'Peter', 'Chen', 'company_user', true, true, CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE);