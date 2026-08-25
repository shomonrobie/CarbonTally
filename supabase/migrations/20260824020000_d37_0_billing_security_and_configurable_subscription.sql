-- ============================================================================
-- D37-0 — Billing security remediation + configurable subscription foundation
-- ----------------------------------------------------------------------------
-- D36 audit found a P0 billing-security defect: the ``authenticated`` role
-- could INSERT/UPDATE/DELETE ``usage_tracking`` and ``customer_subscriptions``
-- rows and UPDATE ``organizations.subscription_*`` / ``trial_*`` / ``tax_rate``
-- columns directly through PostgREST (the browser Supabase client). A customer
-- could rewrite their own usage, plan, limits and trial/subscription state.
--
-- This migration (all additive / idempotent / RLS-safe):
--
-- 1. P0: LOCK DOWN direct client writes to authoritative billing state
--    (usage_tracking, customer_subscriptions, consultant_billing, and the
--    organisations billing/trial/tax columns). SELECT stays open for the
--    tenant's own rows; writes become service-role/trusted-API only.
--
-- 2. organisations.billing_mode — per-customer commercial mode
--    (CREDIT | STANDARD). The default for NEW customers is read from the
--    versioned ``billing_commercial_config`` at org-creation time; existing
--    customers are backfilled once to the seeded default and are NEVER
--    silently migrated by later default changes.
--
-- 3. billing_plans — configurable, VERSIONED plan catalogue (Starter /
--    Professional / Business / Enterprise). Changing a plan creates a NEW
--    version row; historical commercial records keep the terms under which
--    they were created.
--
-- 4. billing_commercial_config — VERSIONED key/value commercial rules
--    (default_billing_mode, credit_rules, structured_data_bands, storage,
--    assisted_pricing, credit_policy, standard_allowance). Each change is a
--    new version row with effective_from/effective_to.
--
-- 5. billing_credit_ledger — APPEND-ONLY credit ledger foundation
--    (grant/consume/adjustment/rollover/emergency_allowance/refund/reversal).
--    The balance is DERIVED (SUM of credit_delta); the ledger is authoritative
--    and immutable. Unique (organization_id, external_reference) gives
--    idempotency for future payment events.
--
-- 6. Seed data: initial plans + commercial configuration (provisional,
--    Admin-configurable values — never hard-coded in business logic).
--
-- Provider-neutral: no provider integration, no provider SDK, no checkout.
-- The existing customer_subscriptions/consultant_billing rows stay untouched
-- and their Stripe-named columns are retained (documented legacy).
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. P0 — lock down direct client writes (keep tenant SELECT)
-- ---------------------------------------------------------------------------

-- usage_tracking — drop the tenant write policies; keep SELECT only.
DROP POLICY IF EXISTS usage_tracking_tenant_insert ON public.usage_tracking;
DROP POLICY IF EXISTS usage_tracking_tenant_update ON public.usage_tracking;
DROP POLICY IF EXISTS usage_tracking_tenant_delete ON public.usage_tracking;

-- customer_subscriptions — drop the tenant write policies; keep SELECT only.
DROP POLICY IF EXISTS customer_subscriptions_tenant_insert ON public.customer_subscriptions;
DROP POLICY IF EXISTS customer_subscriptions_tenant_update ON public.customer_subscriptions;
DROP POLICY IF EXISTS customer_subscriptions_tenant_delete ON public.customer_subscriptions;

-- Remove the authenticated write privileges at the table level (belt & braces:
-- even if a policy is ever re-added, the grant is gone).
REVOKE INSERT, UPDATE, DELETE ON public.usage_tracking FROM authenticated;
REVOKE INSERT, UPDATE, DELETE ON public.customer_subscriptions FROM authenticated;
REVOKE INSERT, UPDATE, DELETE ON public.consultant_billing FROM authenticated;

-- ---------------------------------------------------------------------------
-- 2. organisations.billing_mode (per-customer commercial mode)
-- ---------------------------------------------------------------------------

ALTER TABLE public.organizations
    ADD COLUMN IF NOT EXISTS billing_mode TEXT;

DO $d370$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'organizations_billing_mode_check'
          AND conrelid = 'public.organizations'::regclass
    ) THEN
        ALTER TABLE public.organizations
            ADD CONSTRAINT organizations_billing_mode_check
            CHECK (billing_mode IN ('CREDIT', 'STANDARD'));
    END IF;
END
$d370$;

-- Initial backfill: existing customers are assigned the seeded default once.
-- Later Admin changes to the default affect ONLY new customers.
UPDATE public.organizations
   SET billing_mode = 'CREDIT'
 WHERE billing_mode IS NULL;

-- organisations — REVOKE table-level UPDATE from authenticated. A bare
-- column-level REVOKE cannot override a table-level grant in PostgreSQL, so
-- the authoritative fix is to remove the table-level UPDATE grant entirely:
-- every organisation write now goes through the trusted CarbonTally API
-- (service role). The ``organizations_org_update`` RLS policy becomes inert
-- (no privilege behind it) and the D36 P0 (direct billing/trial/tax column
-- mutation via PostgREST) is closed for the WHOLE row, not just the billing
-- columns.
REVOKE UPDATE ON public.organizations FROM authenticated;

-- Also block authenticated INSERT/DELETE on organisations for defense-in-depth
-- (only the trusted API creates organisations; D35 self-service onboarding).
REVOKE INSERT, DELETE ON public.organizations FROM authenticated;

COMMENT ON COLUMN public.organizations.billing_mode IS
    'D37-0: per-customer commercial mode (CREDIT | STANDARD). Assigned at org '
    'creation from the versioned commercial default; never silently migrated '
    'when the Admin default changes. Authoritative — column-REVOKEd from '
    'authenticated; only trusted/server-side paths may write it.';

-- ---------------------------------------------------------------------------
-- 3. billing_plans — configurable, versioned plan catalogue
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.billing_plans (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    plan_code TEXT NOT NULL,              -- stable identity across versions
    name TEXT NOT NULL,
    description TEXT,
    price NUMERIC NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'GBP',
    billing_interval TEXT NOT NULL DEFAULT 'month',
    included_credits INTEGER NOT NULL DEFAULT 0,
    included_storage_bytes BIGINT NOT NULL DEFAULT 0,
    team_member_limit INTEGER,
    processing_limits JSONB,              -- e.g. {"structured_data_units": 100}
    features JSONB,                       -- entitlement flags
    billing_mode TEXT CHECK (billing_mode IN ('CREDIT', 'STANDARD')),  -- NULL = both
    assisted_processing_available BOOLEAN NOT NULL DEFAULT FALSE,
    managed_processing_available BOOLEAN NOT NULL DEFAULT FALSE,
    api_access BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version INTEGER NOT NULL DEFAULT 1,
    version_label TEXT,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID,
    UNIQUE (plan_code, version)
);

CREATE INDEX IF NOT EXISTS idx_billing_plans_active
    ON public.billing_plans (plan_code) WHERE is_active = TRUE;

COMMENT ON TABLE public.billing_plans IS
    'D37-0: configurable, VERSIONED plan catalogue. Plan changes create a new '
    '(plan_code, version) row; historical commercial records keep the terms '
    'under which they were created. Deny-by-default RLS — written/read through '
    'the trusted billing API only.';

ALTER TABLE public.billing_plans ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 4. billing_commercial_config — versioned key/value commercial rules
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.billing_commercial_config (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    config_key TEXT NOT NULL,
    config_value JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    UNIQUE (config_key, version)
);

CREATE INDEX IF NOT EXISTS idx_billing_commercial_config_current
    ON public.billing_commercial_config (config_key) WHERE effective_to IS NULL;

COMMENT ON TABLE public.billing_commercial_config IS
    'D37-0: versioned commercial rule set (default_billing_mode, credit_rules, '
    'structured_data_bands, storage, assisted_pricing, credit_policy, '
    'standard_allowance). Each change inserts a new version; the current value '
    'is the row with effective_to IS NULL. Deny-by-default RLS — trusted '
    'billing API only.';

ALTER TABLE public.billing_commercial_config ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 5. billing_credit_ledger — append-only credit ledger foundation
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.billing_credit_ledger (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    entry_type TEXT NOT NULL CHECK (entry_type IN (
        'grant', 'consume', 'adjustment', 'rollover',
        'emergency_allowance', 'refund', 'reversal'
    )),
    credit_delta INTEGER NOT NULL CHECK (credit_delta <> 0),
    source TEXT NOT NULL,                 -- plan_included | purchase | promotional | adjustment | refund | emergency | rollover
    reason TEXT,
    plan_code TEXT,
    plan_version INTEGER,
    subscription_id UUID,
    external_reference TEXT,              -- provider/idempotency reference
    correlation_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_billing_credit_ledger_org
    ON public.billing_credit_ledger (organization_id, created_at);

-- Idempotency: at most one ledger entry per (org, external_reference).
CREATE UNIQUE INDEX IF NOT EXISTS uq_billing_credit_ledger_extref
    ON public.billing_credit_ledger (organization_id, external_reference)
    WHERE external_reference IS NOT NULL;

COMMENT ON TABLE public.billing_credit_ledger IS
    'D37-0: APPEND-ONLY credit ledger. Balance is DERIVED (SUM(credit_delta));
    the ledger is authoritative and immutable. Deny-by-default RLS — writes via '
    'the trusted billing service, reads via staff API. No mutable balance-only '
    'design.';

ALTER TABLE public.billing_credit_ledger ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 6. Seed data — provisional, Admin-configurable commercial defaults
-- ---------------------------------------------------------------------------
-- Initial plans (Starter / Professional / Business / Enterprise). Prices are
-- PROVISIONAL and configurable from the Admin Dashboard; they live in the
-- database, never in business logic.

INSERT INTO public.billing_plans (
    plan_code, name, description, price, currency, billing_interval,
    included_credits, included_storage_bytes, team_member_limit,
    processing_limits, features, billing_mode,
    assisted_processing_available, managed_processing_available, api_access,
    is_active, version, version_label, effective_from
) VALUES
    ('starter', 'Starter', 'Entry plan for smaller organisations', 0, 'GBP', 'month',
     10, 10737418240, 3, '{"structured_data_units": 10}', '{"reports": true}', 'CREDIT',
     FALSE, FALSE, FALSE, TRUE, 1, 'v1', NOW()),
    ('professional', 'Professional', 'Standard plan for growing teams', 149, 'GBP', 'month',
     500, 53687091200, 10, '{"structured_data_units": 500}', '{"reports": true}', 'CREDIT',
     TRUE, FALSE, FALSE, TRUE, 1, 'v1', NOW()),
    ('business', 'Business', 'High-volume plan with managed options', 299, 'GBP', 'month',
     1500, 214748364800, 25, '{"structured_data_units": 2000}', '{"reports": true}', 'CREDIT',
     TRUE, TRUE, TRUE, TRUE, 1, 'v1', NOW()),
    ('enterprise', 'Enterprise', 'Custom plan — quoted', 0, 'GBP', 'month',
     0, 0, NULL, '{}', '{"reports": true, "custom": true}', 'CREDIT',
     TRUE, TRUE, TRUE, TRUE, 1, 'v1', NOW())
ON CONFLICT (plan_code, version) DO NOTHING;

-- Initial commercial configuration (version 1 of each key).
INSERT INTO public.billing_commercial_config (config_key, config_value, version, reason, created_by) VALUES
    ('default_billing_mode', '{"mode": "CREDIT"}', 1, 'D37-0 initial seed', NULL),
    ('credit_rules', jsonb_build_object('classes', jsonb_build_array(
         jsonb_build_object('class', 'simple', 'credits', 1, 'description', 'Simple single-item documents'),
         jsonb_build_object('class', 'standard', 'credits', 2, 'description', 'Standard invoices and utilities'),
         jsonb_build_object('class', 'complex', 'credits', 4, 'description', 'Complex multi-line documents'),
         jsonb_build_object('class', 'exceptional', 'credits', NULL, 'quoted', TRUE, 'description', 'Calculated / quoted')
    )), 1, 'D37-0 initial seed', NULL),
    ('structured_data_bands', jsonb_build_object('bands', jsonb_build_array(
         jsonb_build_object('max_rows', 1000, 'units', 1),
         jsonb_build_object('max_rows', 10000, 'units', 3),
         jsonb_build_object('max_rows', 50000, 'units', 10),
         jsonb_build_object('max_rows', 250000, 'units', 30),
         jsonb_build_object('max_rows', 1000000, 'units', 100),
         jsonb_build_object('max_rows', NULL, 'units', NULL, 'custom', TRUE)
    )), 1, 'D37-0 initial seed', NULL),
    ('storage', jsonb_build_object(
         'included_bytes', 0,
         'additional_rate_per_gb', NULL,
         'currency', 'GBP',
         'unit', 'GB',
         'markup_percent', 100
    ), 1, 'D37-0 initial seed', NULL),
    ('assisted_pricing', jsonb_build_object(
         'simple', jsonb_build_object('price', 0.99, 'currency', 'USD'),
         'standard', jsonb_build_object('price', 1.99, 'currency', 'USD'),
         'complex', jsonb_build_object('price', 3.99, 'currency', 'USD'),
         'exceptional', jsonb_build_object('quoted', TRUE)
    ), 1, 'D37-0 initial seed', NULL),
    ('credit_policy', jsonb_build_object(
         'rollover', jsonb_build_object('enabled', TRUE, 'max_carryover_pct', NULL, 'expiry_months', NULL),
         'emergency_allowance', jsonb_build_object('enabled', TRUE, 'allowance_pct', 10)
    ), 1, 'D37-0 initial seed', NULL),
    ('standard_allowance', jsonb_build_object(
         'monthly_processing_units', NULL,
         'additional_rate', NULL,
         'currency', 'GBP'
    ), 1, 'D37-0 initial seed', NULL)
ON CONFLICT (config_key, version) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 7. Platform-admin staff permission for the commercial surface
-- ---------------------------------------------------------------------------
-- The Commercial (billing) administration tab + API require the real
-- ``can_manage_billing`` staff permission (D37-0 §24). Grant it to the
-- existing platform-admin role; every other staff role keeps the default
-- (denied).
UPDATE public.staff_roles
   SET permissions = permissions || '{"can_manage_billing": true}'::jsonb,
       updated_at = NOW()
 WHERE name = 'admin'
   AND NOT (permissions ? 'can_manage_billing');

-- ---------------------------------------------------------------------------
-- 8. Trusted service-role grants for the D37-0 foundation tables
-- ---------------------------------------------------------------------------
-- The authoritative billing tables are deny-by-default for anon/authenticated
-- (customers/consultants/entity staff have NO grants — the P0 lockdown). The
-- trusted ``service_role`` (server/backend paths) is granted ALL so the
-- PostgREST service path and future billing services can operate. Table owners
-- (postgres) are unaffected.
GRANT ALL ON public.billing_plans, public.billing_commercial_config,
    public.billing_credit_ledger TO service_role;


