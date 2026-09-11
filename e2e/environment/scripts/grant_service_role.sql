-- P6-2F E2E environment ONLY — grant the local PostgREST `service_role` the
-- table privileges it needs for synthetic seeding (the demo instance already
-- has them). This is an ISOLATED-environment provisioning step: it does NOT
-- change RLS policies, does NOT touch `authenticated`/`anon` (so the RLS
-- boundary under test is unchanged), and does NOT modify repo migrations.
-- Run against port 55326 only.
GRANT USAGE ON SCHEMA public TO service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

