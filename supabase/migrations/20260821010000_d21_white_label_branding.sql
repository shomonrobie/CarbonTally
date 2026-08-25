-- 20260821010000_d21_white_label_branding.sql
-- D21 — White-Label Foundation: consultant branding presentation mode.
--
-- SMALLEST POSSIBLE SCHEMA CHANGE. Every other branding field D21.1 requires
-- already exists on public.consultant_profiles:
--   brand_name, logo_url, primary_color, secondary_color, footer_text,
--   email_from, website, support_email, support_phone, support_hours,
--   client_portal_url, co_branding_enabled.
-- Only the FULL white-label presentation flag is genuinely missing: no
-- existing column distinguishes "CarbonTally invisible" (fully white-labeled)
-- from "both brands shown" (co_branding_enabled already covers that mode).
--
-- No new tenancy model is introduced. Branding remains on the existing
-- consultant profile row — the presentation/commercial layer. Organisations
-- stay the data-tenancy anchor (no workspace / tenant / white_label_tenant
-- table, no second organisation hierarchy).
--
-- Backward compatible: existing rows default to white_label_enabled = false,
-- which preserves the previous behaviour (CarbonTally fallback branding).
ALTER TABLE public.consultant_profiles
    ADD COLUMN IF NOT EXISTS white_label_enabled boolean NOT NULL DEFAULT false;

COMMENT ON COLUMN public.consultant_profiles.white_label_enabled IS
    'D21: when TRUE the firm presents under its own brand with CarbonTally invisible on supported surfaces (mutually exclusive with co_branding_enabled; white-label wins when both are set).';
