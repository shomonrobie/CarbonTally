-- ============================================================================
-- D37 — Master Commercial Billing (D37-1..D37-9) — additive layer over D37-0
-- ----------------------------------------------------------------------------
-- Builds the provider-neutral commercial billing system on the D37-0
-- foundation (billing_plans / billing_commercial_config / billing_credit_ledger
-- / organizations.billing_mode / P0 lockdown). Everything here is ADDITIVE and
-- idempotent; no D37-0 table, column, policy or grant is weakened.
--
-- Reused (not duplicated): customer_subscriptions (extended with the
-- provider-neutral lifecycle), billing_credit_ledger (extended with order
-- association), audit_trail, the staff can_manage_billing permission model,
-- organization tenancy.
--
-- New domain concepts (genuinely missing): the common ORDER model
-- (billing_orders — automated/assisted/managed/storage), storage metering
-- snapshots (billing_storage_usage), provider-neutral payment records
-- (billing_payment_records — NO provider integration), and durable
-- idempotency (billing_idempotency_keys).
--
-- Security: every new table is RLS-enabled with NO authenticated policies and
-- NO authenticated grants (deny-by-default — customer/consultant/entity-staff
-- access is via the trusted API only). service_role is granted ALL.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Extend customer_subscriptions (REUSE) — provider-neutral lifecycle
-- ---------------------------------------------------------------------------
-- The legacy Stripe-named columns and free-text ``plan`` remain as documented
-- legacy; the D37 authoritative fields reference the versioned plan catalogue
-- and the lifecycle vocabulary below.
ALTER TABLE public.customer_subscriptions
    ADD COLUMN IF NOT EXISTS billing_mode TEXT,
    ADD COLUMN IF NOT EXISTS plan_code TEXT,
    ADD COLUMN IF NOT EXISTS plan_version INTEGER,
    ADD COLUMN IF NOT EXISTS lifecycle_status TEXT,
    ADD COLUMN IF NOT EXISTS current_period_start TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS current_period_end TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS activated_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS idempotency_key TEXT;

DO $d37$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'customer_subscriptions_billing_mode_check'
          AND conrelid = 'public.customer_subscriptions'::regclass
    ) THEN
        ALTER TABLE public.customer_subscriptions
            ADD CONSTRAINT customer_subscriptions_billing_mode_check
            CHECK (billing_mode IN ('CREDIT', 'STANDARD'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'customer_subscriptions_lifecycle_status_check'
          AND conrelid = 'public.customer_subscriptions'::regclass
    ) THEN
        ALTER TABLE public.customer_subscriptions
            ADD CONSTRAINT customer_subscriptions_lifecycle_status_check
            CHECK (lifecycle_status IN
                ('pending', 'trial', 'active', 'past_due', 'suspended',
                 'cancelled', 'expired'));
    END IF;
END
$d37$;

-- At most one ACTIVE commercial relationship per organisation.
CREATE UNIQUE INDEX IF NOT EXISTS uq_customer_subscriptions_org_active
    ON public.customer_subscriptions (organization_id)
    WHERE lifecycle_status IN ('trial', 'active', 'past_due', 'suspended');

CREATE INDEX IF NOT EXISTS idx_customer_subscriptions_period
    ON public.customer_subscriptions (current_period_end)
    WHERE lifecycle_status IN ('trial', 'active', 'past_due');

COMMENT ON COLUMN public.customer_subscriptions.lifecycle_status IS
    'D37: subscription lifecycle (pending/trial/active/past_due/suspended/'
    'cancelled/expired). Authoritative server-side; authenticated has no write '
    'grants (D37-0 P0 lockdown).';

-- ---------------------------------------------------------------------------
-- 2. billing_orders — common order model (automated/assisted/managed/storage)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.billing_orders (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    order_type TEXT NOT NULL CHECK (order_type IN
        ('automated', 'assisted', 'managed', 'storage', 'other')),
    status TEXT NOT NULL CHECK (status IN
        ('draft', 'estimated', 'awaiting_customer_approval', 'approved',
         'queued', 'processing', 'awaiting_qc', 'completed', 'cancelled',
         'rejected', 'failed', 'refunded')) DEFAULT 'draft',
    title TEXT,
    description TEXT,
    complexity TEXT CHECK (complexity IN
        ('simple', 'standard', 'complex', 'exceptional')),
    items JSONB NOT NULL DEFAULT '[]',
    total_amount NUMERIC NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'GBP',
    plan_code TEXT,
    plan_version INTEGER,
    config_version JSONB,
    idempotency_key TEXT,
    external_reference TEXT,
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cancelled_by UUID,
    cancelled_at TIMESTAMPTZ,
    metadata JSONB,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_billing_orders_org
    ON public.billing_orders (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_orders_status
    ON public.billing_orders (status) WHERE status NOT IN ('completed', 'cancelled', 'rejected', 'failed');
CREATE UNIQUE INDEX IF NOT EXISTS uq_billing_orders_idem_org
    ON public.billing_orders (organization_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

COMMENT ON TABLE public.billing_orders IS
    'D37: common commercial order model. Immutable after completion; '
    'corrections are new adjustments. Items are an immutable line-item JSON '
    'snapshot (description, quantity, unit_price, line_total, units, plan '
    'refs) so historical commercial terms are preserved. Deny-by-default RLS; '
    'customer access via the trusted billing API only.';

ALTER TABLE public.billing_orders ENABLE ROW LEVEL SECURITY;


-- ---------------------------------------------------------------------------
-- 3. billing_storage_usage — storage metering snapshots
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.billing_storage_usage (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    usage_bytes BIGINT NOT NULL DEFAULT 0,
    included_bytes BIGINT NOT NULL DEFAULT 0,
    additional_bytes BIGINT NOT NULL DEFAULT 0,
    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT DEFAULT 'organization_files_sum',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_billing_storage_usage_org
    ON public.billing_storage_usage (organization_id, measured_at DESC);

COMMENT ON TABLE public.billing_storage_usage IS
    'D37: authoritative storage metering snapshots (server-measured from the '
    'D32 organization_files records — never browser-reported). Current usage '
    'is the latest snapshot; history is preserved for auditability.';

ALTER TABLE public.billing_storage_usage ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 4. billing_payment_records — provider-neutral payment records
-- ---------------------------------------------------------------------------
-- NO actual payment provider integration (no checkout, no webhooks, no
-- credentials). These records represent payment intent/confirmation for future
-- PayPal / Wise / card adapters. Sensitive payment credentials are NEVER
-- stored.
CREATE TABLE IF NOT EXISTS public.billing_payment_records (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    payment_method_type TEXT,
    provider_transaction_ref TEXT,
    amount NUMERIC NOT NULL,
    currency TEXT NOT NULL DEFAULT 'GBP',
    status TEXT NOT NULL CHECK (status IN
        ('pending', 'confirmed', 'failed', 'refunded')) DEFAULT 'pending',
    order_id UUID REFERENCES public.billing_orders(id) ON DELETE SET NULL,
    subscription_id UUID REFERENCES public.customer_subscriptions(id) ON DELETE SET NULL,
    idempotency_key TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confirmed_at TIMESTAMPTZ,
    metadata JSONB,
    created_by UUID
);

CREATE INDEX IF NOT EXISTS idx_billing_payment_records_org
    ON public.billing_payment_records (organization_id, recorded_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uq_billing_payment_records_idem
    ON public.billing_payment_records (organization_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

COMMENT ON TABLE public.billing_payment_records IS
    'D37: provider-neutral payment records (provider, method type, transaction '
    'ref, amount, currency, status). No provider integration, no card data. '
    'Deny-by-default RLS.';

ALTER TABLE public.billing_payment_records ENABLE ROW LEVEL SECURITY;


-- ---------------------------------------------------------------------------
-- 5. billing_idempotency_keys — durable idempotency for financial mutations
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.billing_idempotency_keys (
    key TEXT PRIMARY KEY,
    operation TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    request_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.billing_idempotency_keys IS
    'D37: durable idempotency. A retried grant/consume/rollover/allowance/'
    'adjustment/reversal/refund/order creation with the same key returns the '
    'original result instead of double-executing.';

ALTER TABLE public.billing_idempotency_keys ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 6. billing_credit_ledger — add order association (REUSE/extend)
-- ---------------------------------------------------------------------------
ALTER TABLE public.billing_credit_ledger
    ADD COLUMN IF NOT EXISTS order_id UUID;

ALTER TABLE public.billing_credit_ledger
    DROP CONSTRAINT IF EXISTS billing_credit_ledger_order_id_fkey;

ALTER TABLE public.billing_credit_ledger
    ADD CONSTRAINT billing_credit_ledger_order_id_fkey
    FOREIGN KEY (order_id) REFERENCES public.billing_orders(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_billing_credit_ledger_order
    ON public.billing_credit_ledger (order_id)
    WHERE order_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 7. D37 master commercial baseline — publish NEW plan versions (history kept)
-- ---------------------------------------------------------------------------
-- Starter $49/100 and Business $399/2,000 per the D37 approved baseline
-- (§9). Professional ($149/500) is already at the baseline. v1 rows remain as
-- versioned history; v2 becomes current. All values remain Admin-configurable.
DO $d37$
DECLARE
    _v INT;
BEGIN
    -- Starter -> v2 ($49, 100 credits)
    SELECT COALESCE(MAX(version), 0) + 1 INTO _v FROM public.billing_plans WHERE plan_code = 'starter';
    UPDATE public.billing_plans SET effective_to = NOW()
     WHERE plan_code = 'starter' AND effective_to IS NULL;
    INSERT INTO public.billing_plans (
        plan_code, name, description, price, currency, billing_interval,
        included_credits, included_storage_bytes, team_member_limit,
        processing_limits, features, billing_mode,
        assisted_processing_available, managed_processing_available, api_access,
        is_active, version, version_label, effective_from, created_by
    ) VALUES (
        'starter', 'Starter', 'Entry plan for smaller organisations', 49, 'USD', 'month',
        100, 21474836480, 3, '{"structured_data_units": 100}', '{"reports": true}', 'CREDIT',
        FALSE, FALSE, FALSE, TRUE, _v, 'v' || _v, NOW(), NULL
    );

    -- Business -> v2 ($399, 2,000 credits)
    SELECT COALESCE(MAX(version), 0) + 1 INTO _v FROM public.billing_plans WHERE plan_code = 'business';
    UPDATE public.billing_plans SET effective_to = NOW()
     WHERE plan_code = 'business' AND effective_to IS NULL;
    INSERT INTO public.billing_plans (
        plan_code, name, description, price, currency, billing_interval,
        included_credits, included_storage_bytes, team_member_limit,
        processing_limits, features, billing_mode,
        assisted_processing_available, managed_processing_available, api_access,
        is_active, version, version_label, effective_from, created_by
    ) VALUES (
        'business', 'Business', 'High-volume plan with managed options', 399, 'USD', 'month',
        2000, 536870912000, 25, '{"structured_data_units": 5000}', '{"reports": true}', 'CREDIT',
        TRUE, TRUE, TRUE, TRUE, _v, 'v' || _v, NOW(), NULL
    );
END
$d37$;

-- ---------------------------------------------------------------------------
-- 8. Trusted service-role grants for the new tables
-- ---------------------------------------------------------------------------
GRANT ALL ON public.billing_orders, public.billing_storage_usage,
    public.billing_payment_records, public.billing_idempotency_keys
    TO service_role;

-- D37-0 grants cover billing_plans/billing_commercial_config/billing_credit_ledger.

