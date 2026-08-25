# CarbonTally V3 — D37 Master Commercial Billing Completion Report

**Scope:** D37-1 … D37-9 (one master implementation over the completed D37-0
foundation). **Date:** 2026-08-24 · **Status:** **PASS** — HARD STOP reached.

## 1. Executive Summary

D37 completed CarbonTally's provider-neutral commercial billing system without
replacing the sound D37-0 foundation (secure → reuse → extend → integrate →
verify). Delivered in one pass: subscription lifecycle, server-authoritative
entitlements, the CREDIT mode (complexity-based credits + configurable
structured-data bands), the STANDARD mode (monthly allowance), the common order
model (Automated / Assisted / Managed / storage), Assisted Processing
estimate→approval→commercial order, Managed Processing requests, D32-derived
storage metering, provider-neutral payment records, a durable idempotency
layer, an append-only credit ledger with grant/consume/rollover/emergency/
adjustment/reversal/refund, a customer Billing page, and an extended Admin
Commercial surface. **No payment-provider integration was performed.**

**Final test record (before → after):**

| Suite | Before (D37-0) | After (D37) |
|---|---|---|
| Backend unit | 1039 passed | **1056 passed** (+17) |
| RLS | 23 passed | **27 passed** (+4) |
| Frontend (api) | 23 passed | **25 passed** (+2) |
| Production build | OK | **OK** |
| Live verification | 26/26 | **23/23** |

## 2. D37 Status

**PASS.** All phase gates met; all fixtures cleaned; D37-0 P0 lockdown intact.

## 3. D37-0 Baseline Verification

Re-verified before building: unit 1039, RLS 23, frontend 23, build OK,
live 26/26. The D37-0 foundation (billing_plans, billing_commercial_config,
billing_credit_ledger, organizations.billing_mode, P0 lockdown,
can_manage_billing) is preserved and extended additively.

## 4. Architecture

Organization → Subscription (customer_subscriptions, extended) → Plan VERSION
→ Billing Mode → Entitlements → Usage/Processing → Credits or Allowances →
Orders/Commercial Records → Future Payment Provider.

```
Customer browser → Authorized CarbonTally API → BillingService (server-side)
  → billing tables (deny-by-default RLS; service_role trusted paths)
  → credit ledger (append-only) / orders (immutable after completion)
  → audit_trail
Future: Provider Adapter Interface → PayPal / Wise / Card
```

## 5. Subscription System

`customer_subscriptions` extended (REUSED, not duplicated): `billing_mode`,
`plan_code`, `plan_version`, `lifecycle_status` (pending/trial/active/past_due/
suspended/cancelled/expired), `current_period_*`, `activated_at`,
`idempotency_key`; unique partial index = one active relationship per org.
Admin activates/renews (new row; history preserved) and changes lifecycle;
plan/version relationship enforced (exact plan version for historical terms).

## 6. Entitlement System

`BillingService.get_entitlement(org)` answers "what is this org entitled to use
right now" server-side: active subscription → exact plan version → billing
mode → configurable credit rules / storage / credit policy / standard
allowance → derived ledger balance. No entitlement logic in React.

## 7. CREDIT Mode

- Complexity classifier (configurable thresholds) → simple 1 / standard 2 /
  complex 4 / exceptional-quoted (configurable `credit_rules`).
- Structured data → configurable `structured_data_bands` (no one-file-one-credit).
- `charge_processing` consumes credits via the ledger; **no separate
  calculation charge**.
- Grant / consume / rollover / emergency allowance / adjustment / reversal /
  refund — all idempotent + audited + ledger-visible.

## 8. STANDARD Mode

Same entitlement architecture: monthly allowance from versioned
`standard_allowance` config; usage recorded server-side in `usage_tracking`;
allowance exhausted → 402. No parallel credit system.

## 9. Assisted Processing

Customer requests estimate → configurable price book (`assisted_pricing`) →
order `awaiting_customer_approval` → **customer approval required** →
`approved` + provider-neutral payment intent → admin completes → immutable.

## 10. Managed Processing

Managed requests use the **common** `billing_orders` model (no separate
architecture): status estimated/awaiting approval; CarbonTally quotes and
manages the workflow; Processing Entity staff receive only assigned work.

## 11. Storage Metering

Server-authoritative snapshots (`billing_storage_usage`) summed from the D32
`organization_files` records — never browser-reported. Included allowance from
the plan version; additional bytes tracked. No data deletion at limit.

## 12. Orders

`billing_orders` common model (automated/assisted/managed/storage/other) with
immutable item JSON snapshots + config_version references; lifecycle
draft/estimated/awaiting_customer_approval/approved/queued/processing/
awaiting_qc/completed/cancelled/rejected/failed/refunded; org-scoped,
audited, idempotent creation; completed orders never rewritten (corrections
are new adjustments).

## 13. Provider-Neutral Payment Architecture

`billing_payment_records` (provider, method type, transaction ref, amount,
currency, status, order/subscription link) — no credentials, no vaulting.
Approval records a `pending` intent. Adapters can be added later without
touching the ledger/order/subscription/config/tenancy model.

## 14. VAT / Tax / Accounting Integration Boundary

No tax engine. Commercial records (orders with immutable items + plan/config
versions, ledger, payment records, audit) preserve the information a future
third-party tax/accounting service needs. No tax policy hard-coded.

## 15. Admin Dashboard

The existing `/ops` **Commercial** tab now also manages: subscriptions
(activate/renew + lifecycle changes), orders (list + complete), credit
operations (grant/adjust/reverse/refund/rollover), storage metering, and the
D37-0 plan/config/ledger surfaces — all behind the real `can_manage_billing`
permission (server-enforced).

## 16. Customer Billing UI

New `/billing` page (V3Layout nav): plan, billing mode, credits balance + full
ledger history, storage usage (re-measure), STANDARD allowance, Assisted
estimate builder, Managed request, orders list (approve/cancel), and
provider-neutral payment records. All reads/writes org-scoped via
`/api/v3/billing/*`.

## 17. Database Changes

Migration `supabase/migrations/20260824030000_d37_master_commercial_billing.sql`
(additive/idempotent): `customer_subscriptions` lifecycle columns;
`billing_orders`, `billing_storage_usage`, `billing_payment_records`,
`billing_idempotency_keys` (new); `billing_credit_ledger.order_id`;
plan v2 for Starter ($49/100) + Business ($399/2,000) per the approved
baseline (v1 preserved as history); service_role grants.

## 18. RLS / Security

All new tables: `ENABLE ROW LEVEL SECURITY`, no authenticated policies/grants
(deny-by-default) + `service_role` ALL. D37-0 P0 lockdown unchanged.
`UsageTrackingRepository` is the only trusted writer to `usage_tracking`.
Verified: customers cannot write orders/subscriptions/ledger/payments/storage
or grant credits (403/400); trusted service paths succeed.

## 19. Auditability

Every credit op, subscription change, order lifecycle event and processing
charge appends an `audit_trail` entry (actor, entity, detail). Ledger + orders
are the authoritative commercial record.

## 20. Historical Integrity

Ledger append-only; completed orders immutable; plan/config versions never
rewritten; reversals are new entries. Live-verified (reversal left the original
grant intact in history).

## 21. API Changes

- Customer: `/api/v3/billing/me`, `/me/credits`, `/me/orders(+/{id})`,
  `/me/payments`, `/me/storage/refresh`, `/orders/assisted`,
  `/orders/{id}/approve`, `/orders/{id}/cancel`, `/managed/orders`.
- Admin: `/api/v3/commercial/subscriptions(+/{id}/status)`, `/orders(+/{id})`,
  `/orders/{id}/complete`, `/storage`, `/payments`, `/entitlement/{org}`,
  `/credits/grant|adjust|reverse|refund|rollover`.
- Processing: `customer_review_item` charges CREDIT/STANDARD on approval
  (idempotent per item; no-subscription orgs unaffected).

## 22. Test Results

Unit **1056** (0 fail) · RLS **27** (0 fail) · frontend **25** (0 fail;
pre-existing rrd-v7 `App.test.js` suite apart) · **build OK**.

## 23. Live Verification

**23/23 passed** against the real stack: onboarding, entitlement read,
subscription activation (versioned), credit grant, plan+balance visible,
Assisted estimate $21.85 → approval → payment record, Managed order, storage
measurement, admin views, reversal with history intact, security denials.
Fixtures cleaned (orgs 0, users 0, orders 0, subs 0, idempotency keys 0).

## 24. Migration Results

Migration applied to main + test DBs (EXIT=0, idempotent).

## 25. Performance Considerations

Ledger balance is a SUM over an indexed (org, created_at) scan (authoritative,
no cache drift); orders/config reads are single-row indexed; storage metering
is one SUM over `organization_files` per refresh. No per-record N+1 in charge
paths.

## 26. Known Limitations

- No actual payment collection (by design); payment records are intents.
- Assisted/Managed orders do not yet auto-create processing-entity assignments
  (the order is the commercial foundation; workflow linkage is a later step).
- STANDARD allowance uses a flat per-period counter; per-item complexity is
  not applied in STANDARD.
- Emergency allowance reconciliation rules are configurable fields; the
  automated reconciliation job is future work.

## 27. Deferred Work (explicitly outside this task)

- **PayPal integration** — not implemented (adapter interface ready).
- **Wise integration** — not implemented.
- **Card payment integration** — not implemented.
- **Checkout / payment capture / webhooks** — not implemented.
- **Tax provider integration** — not implemented (records preserved).
- **Accounting provider integration** — not implemented (records preserved).
- Managed Processing end-to-end assignment; emergency reconciliation job.

## 28. Final Architecture Diagram

```
Organization
  └─ customer_subscriptions (lifecycle, plan version, billing mode)
       └─ billing_plans (versioned) ── configurable commercial rules
            ├─ billing_commercial_config (credit/bands/storage/pricing/policy)
            ├─ billing_credit_ledger (append-only credits)
            ├─ billing_orders (automated/assisted/managed/storage)
            ├─ billing_storage_usage (metering)
            └─ billing_payment_records (provider-neutral)
   Authorized API → BillingService (entitlement + credit ops + orders)
   Durable idempotency + audit_trail on every mutation
```

## 29. D37 Completion Checklist

Security ✓ · Subscription ✓ · Entitlements ✓ · CREDIT ✓ (grants/consume/
rollover/emergency/adjust/reverse/refund/ledger/idempotency) · STANDARD ✓ ·
Assisted ✓ (estimate/approval/order) · Managed ✓ (common model) · Storage ✓ ·
Payment architecture ✓ (no integration) · Tax boundary ✓ · Admin ✓ · Customer ✓ ·
Historical integrity ✓ · Tests ✓ · Build ✓ · Live verification ✓ · Docs ✓.

## 30. Recommended Next Step

HARD STOP. D37 is complete. The next phase (D38 or Product Owner direction)
should be decided by the Product Owner — candidate work: provider adapter
selection (Stripe/PayPal/Wise), managed-processing assignment automation, and
third-party tax/accounting integration.
