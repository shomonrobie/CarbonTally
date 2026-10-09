# CT-DISC-SUB-001 — Subscription & Billing Architecture Discovery Report

**Document ID:** CT-DISC-SUB-001
**Task ID:** CT-DISC-SUB-001-20261004
**Type:** Discovery / audit (READ-ONLY). No implementation, no migration, no code change, no DB change, no commit, no push, no deploy.
**Status:** DISCOVERY COMPLETE — OPEN PO DECISIONS REMAIN
**Date:** 2026-10-04

---

## 1. Task ID

`CT-DISC-SUB-001-20261004`

Purpose: establish the factual baseline of the existing CarbonTally subscription,
billing, pricing, entitlement and plan-management architecture **before** the Product
Owner approves any future comprehensive subscription UI/UX design.

This report is the permanent deliverable required by the task.

---

## 2. Repository / branch examined

| Item | Value |
| --- | --- |
| Repository | `/home/shomonrobie/ct_93d5cdd` (CarbonTally V3 monorepo) |
| Branch | `p8-release-reconciled` (tracking `origin/p8-release-reconciled`) |
| Repository tier | The task specified branch `p8-release-reconciled`; this was the checked-out branch and was used directly |

---

## 3. Commit / working-tree baseline

| Item | Value |
| --- | --- |
| HEAD commit | `375a48dc1b9e9cfd74090bbf747554ae997acb59` |
| Working tree | **NOT CLEAN** — 121 porcelain entries (31 modified, 90 untracked) |
| Local database | PostgreSQL at `127.0.0.1:5432`, database `ct_local_93d5cdd` (demo-lab; **not production**) |
| DB access | Read-only `SELECT` probes only. Credentials sourced from `backend/.env` and **redacted** from all output |

**Important baseline caveat.** The working tree changed *during* this discovery: an
untracked file `backend/api/v3_manual_processing_coverage.py` and a modified
`backend/api/router.py` appeared mid-session (CT-MP-SUB-004). The HEAD commit did not
move. All findings below were re-verified against the state at the time of writing.

**PO/specification documents inspected are UNTRACKED** (present in the working tree, not
committed). Their content hashes at discovery time:

| Document | sha256 (working tree) |
| --- | --- |
| `docs/architecture/CT-SUB-001_CarbonTally_Configurable_Subscription_Billing_Product_Specification.md` | `a27e3c38f638355210e243bdc77c0f9d931f1367ff840d6405f8d2019987dc74` |
| `docs/architecture/CT-UX-SUB-001_CarbonTally_Subscription_Billing_UI_UX_Specification.md` | `7cbc2267c5ff43ae0b11f01dead09ac235d3dafe527e1f291f71eb2ff5cbc5b5` |
| `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md` | `d55644f00ad04014e286597770c57dfff7582bad3fb9523f8729e53e5b29ea5d` |
| `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` | `a27ad96428808cc44fe632da41dec77c171ed6909cdbbf7bf8e74d676079f3da` |
| `docs/architecture/CT-MP-SUB-003-implementation-report.md` | `16de0ce4d00c448b2a66eafac99c056761cd8fba2d6404201b3fd1af68767fab` |

---

## 4. Subscription architecture summary

CarbonTally **already has a real, versioned, server-authoritative,
provider-neutral commercial/subscription foundation**. It was built deliberately in
D37-0 → D37 → P6-BILL-1 and is **organization-scoped**.

```text
billing_plans (versioned catalogue: plan_code + version)
        │  features JSONB + legacy boolean feature columns
        ▼
customer_subscriptions (ONE active commercial relationship per organization)
        │  lifecycle_status, billing_mode, plan_code + plan_version
        ▼
billing_commercial_config (versioned commercial rules)
billing_credit_ledger    (append-only credits; balance derived)
billing_orders           (automated / assisted / managed / storage / other)
billing_storage_usage    (server-measured snapshots)
billing_payment_records  (provider-NEUTRAL intent/confirmation records)
billing_idempotency_keys (durable idempotency)
        ▼
Entitlement resolution (BillingService.get_entitlement / ensure_processing_entitlement)
        ▼
Product enforcement (upload gate, processing charge, Manual Processing routing)
```

| Layer | Artefact |
| --- | --- |
| Domain (pure) | `backend/domain/billing.py` |
| Persistence | `backend/data/billing.py` (7 repositories) |
| Service (authoritative rules) | `backend/services/billing.py` (`BillingService`) |
| Customer API | `backend/api/v3_billing.py`, prefix `/api/v3/billing` |
| Admin API | `backend/api/v3_commercial.py`, prefix `/api/v3/commercial` |
| Migrations | `20260824020000_d37_0_...sql`, `20260824030000_d37_master_...sql` |
| Customer UI | `frontend/src/v3/customer/BillingPage.jsx` at route `/billing` |
| Admin UI | `frontend/src/v3/ops/CommercialTab.jsx` inside `/ops` tab **Commercial** |
| Public UI | `frontend/src/PricingPage.jsx` at route `/pricing` (static, no checkout) |

**There is exactly one subscription model: organization-scoped.**
No consultant-firm subscription table, no user-scoped billing, no parallel
subscription system, and no second plan catalogue exists.

---

## 5. `billing_plans` findings

Created by `supabase/migrations/20260824020000_d37_0_billing_security_and_configurable_subscription.sql:117`.

| Aspect | Finding |
| --- | --- |
| Stable identity | `plan_code` TEXT NOT NULL — identity persists across versions |
| Versioning | `version` INTEGER NOT NULL DEFAULT 1; `UNIQUE (plan_code, version)` |
| Historicity | `effective_from` / `effective_to`. The **current** version is the row with `effective_to IS NULL` |
| Price | `price NUMERIC NOT NULL DEFAULT 0`; `currency TEXT NOT NULL DEFAULT 'GBP'`; `billing_interval TEXT NOT NULL DEFAULT 'month'` |
| Included quota | `included_credits`, `included_storage_bytes`, `team_member_limit` |
| Limits | `processing_limits JSONB` (e.g. `{"structured_data_units": 100}`) |
| Entitlements | `features JSONB` (canonical entitlement block) |
| Legacy boolean entitlements | `assisted_processing_available`, `managed_processing_available`, `api_access` (all `BOOLEAN NOT NULL DEFAULT FALSE`) |
| Availability | `is_active BOOLEAN NOT NULL DEFAULT TRUE` |
| Mode scoping | `billing_mode TEXT CHECK IN ('CREDIT','STANDARD')`, NULL = usable by both |
| Audit | `created_at/created_by/updated_at/updated_by`, `version_label` |
| Index | `idx_billing_plans_active (plan_code) WHERE is_active` |
| RLS | `ENABLE ROW LEVEL SECURITY` with **0 policies** (deny-by-default); `GRANT ALL ... TO service_role` |
| Foreign keys | None outbound (a catalogue table) |

**Operational meaning.** A plan is *not* a mutable record. Changing a price or a plan
feature publishes a **new `(plan_code, version)` row** and closes the previous row with
`effective_to`. Any commercial record created under v1 keeps v1's terms. This is the
correct foundation for "an Admin changes a price without a deployment and without
rewriting history".

### Verified live state (local demo-lab DB, `ct_local_93d5cdd`)

| plan_code | version | price | currency | interval | credits | active | assisted | managed | api | features |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| starter | v1 (retired) | 0 | GBP | month | 10 | true | false | false | false | `{"reports": true}` |
| starter | v2 (retired) | 49 | USD | month | 100 | true | false | false | false | `{"reports": true}` |
| starter | **v3 (current)** | 49 | USD | month | 100 | true | false | false | false | `{"reports": true}` |
| professional | **v1 (current)** | 149 | GBP | month | 500 | true | true | false | false | `{"reports": true}` |
| business | v1 (retired) | 299 | GBP | month | 1500 | true | true | true | true | `{"reports": true}` |
| business | v2 (retired) | 399 | USD | month | 2000 | true | true | true | true | `{"reports": true}` |
| business | **v3 (current)** | 399 | USD | month | 2000 | true | true | true | true | `{"reports": true}` |
| enterprise | **v1 (current)** | 0 | GBP | month | 0 | true | true | true | true | `{"reports": true, "custom": true}` |

Effective-window evidence confirms the mechanism works (`business v1 → v2 → v3`
windows are contiguous, only v3 is `effective_to IS NULL`).

**Two findings from the live data:**

1. **Duplicate plan versions from a non-idempotent seed migration.**
   `20260824030000_d37_master_commercial_billing.sql` computes
   `COALESCE(MAX(version),0)+1` and inserts **without an `ON CONFLICT` guard** for
   starter/business. It was applied twice (2026-08-24 and 2026-09-19), producing a
   redundant `v2` and then a redundant `v3` with byte-identical commercial values.
   Classification: **PARTIALLY IMPLEMENTED / idempotency defect in the seed migration.**
2. **Mixed currencies and price/currency inconsistency.**
   starter/business current versions are `USD`; professional/enterprise are `GBP`. The
   public pricing page advertises `£49 / £149 / £399`. The commercial values therefore
   disagree with the public surface in currency terms.

---

## 6. `customer_subscriptions` findings

**Base table** (legacy, `supabase/migrations/00000000000000_init_schema.sql:1449`):
`organization_id` (`NOT NULL`, FK → `organizations`), free-text `plan` (`NOT NULL`),
legacy `status`, quota counters, `currency`, `features JSONB`, Stripe-named columns
(`stripe_subscription_id`, `stripe_customer_id`, `stripe_price_id`), and
`CONSTRAINT customer_subscriptions_status_check CHECK (status IN
('trialing','active','past_due','paused','cancelled','expired'))`.

**D37 extension** (`20260824030000_d37_master_commercial_billing.sql:31`): adds
`billing_mode`, `plan_code`, `plan_version`, `lifecycle_status`,
`current_period_start`, `current_period_end`, `activated_at`, `idempotency_key`, plus
`CHECK` constraints for `billing_mode` and `lifecycle_status`.

| Aspect | Finding |
| --- | --- |
| Ownership | `organization_id NOT NULL` → **organization-scoped**, exactly one owner |
| Plan relationship | `plan_code` + `plan_version` (denormalised reference, **no FK**) resolved through `BillingPlansRepository.get_version` / `get_current_by_code` |
| Uniqueness | `UNIQUE (organization_id) WHERE lifecycle_status IN ('trial','active','past_due','suspended')` — **at most one active commercial relationship per organisation** |
| Period index | `idx_customer_subscriptions_period (current_period_end) WHERE lifecycle_status IN ('trial','active','past_due')` — supports renewal sweeps |
| Idempotency | `idempotency_key` column exists; service-layer idempotency is enforced by `billing_idempotency_keys` |
| Cancellation | `cancelled_at`, `cancelled_by` (**base schema only** — the D37 `Subscription` domain object does not map them) |
| Upgrade/downgrade | **No dedicated columns or semantics.** A plan change is expressed as a new `plan_code`/`plan_version` on the same active row via `upsert_active` |
| Trial / renewal | Represented only through `lifecycle_status` + `current_period_start/end`. No trial-duration or dunning fields |

**Operational meaning.** This is an *org-scoped state machine of the current commercial
relationship*, not a billing-invoice ledger. It answers "what is this organisation
entitled to right now", not "what has this organisation been invoiced".

**Verified live state:** `customer_subscriptions` = **0 rows**.
Combined with §5, no organisation in the local database currently has ANY subscription.

---

## 7. Subscription lifecycle findings

Vocabulary (`backend/domain/billing.py:59`):
`pending | trial | active | past_due | suspended | cancelled | expired`
(enforced by `customer_subscriptions_lifecycle_status_check`).

Legacy `status` vocabulary is retained separately and is **not** used by D37
(`('trialing','active','past_due','paused','cancelled','expired')`).

| Operation | Implementation | Exposed to |
| --- | --- | --- |
| Read lifecycle | `BillingService.get_entitlement` → `subscription.lifecycle_status` | Customer (`/api/v3/billing/me`), Admin |
| Activate | `BillingService.activate_subscription` (validates plan exists + is active; sets `activated_at`, period; idempotent; audited) | **Admin only** (`POST /api/v3/commercial/subscriptions`) |
| Change status | `BillingService.change_subscription_status` | **Admin only** (`POST /api/v3/commercial/subscriptions/{id}/status`) |
| Self-service upgrade / downgrade / cancel / renew | **NOT FOUND** | — |

Only the four statuses in the unique index (`trial/active/past_due/suspended`) block a
second active row; setting `cancelled`/`expired` frees the organisation for a new
relationship. There is **no** scheduled expiry, dunning, renewal or grace-period
implementation.

---

## 8. Feature-entitlement findings

### Canonical mechanism
`billing_plans.features` (JSONB) is the canonical, forward-looking entitlement carrier.
The ratified pattern is an additive block per capability:

```text
plan.features = {
  "manual_processing": { "enabled": true, ... },            # canonical (FIN-06 / MP)
  "consultant":        { "enabled": …, "client_capacity": …, "team_member_limit": …,
                          "white_label": …, "workspace": … },# D-C / CT-CONSULT-003
  "consultant_manual_processing": { "enabled": …, "mode": "SELECTED_CLIENTS"|
                                     "ALL_ELIGIBLE_CLIENTS", "selected_capacity": … }
}
```

### Resolution precedence

```text
DIRECT manual-processing entitlement
    = features.manual_processing.enabled            (explicit — WINS)
      OR assisted_processing_available              (legacy column — fallback)

consultant capability
    = features.consultant.enabled                   (no legacy fallback)

consultant-sponsored MP coverage (CT-MP-SUB-003)
    = ACTIVE consultant_clients relationship (eligibility)
      AND the firm's OWN org subscription plan carries
          features.consultant_manual_processing
      AND ( mode == ALL_ELIGIBLE_CLIENTS
            OR an ACTIVE consultant_mp_allocations row exists )

EFFECTIVE = DIRECT OR SPONSORED
```

Authoritative implementation points:
`backend/domain/manual_processing.py` (`entitlement_from_plan`,
`consultant_coverage_from_plan`, `sponsored_entitlement`, `combine_entitlement`),
`backend/services/manual_processing_routing.py`, and
`BillingService._consultant_capability_from_plan` (`backend/services/billing.py:828`).

### Server-side enforcement — YES

| Enforcement point | Evidence |
| --- | --- |
| Processing charge / entitlement gate | `BillingService.charge_processing`, `BillingService.ensure_processing_entitlement` (`backend/services/billing.py:167`) — fails closed with 403 when no active entitlement |
| Upload gate | `backend/api/upload_gate.py` |
| Manual-processing routing | `ManualProcessingRouter.entitlement_for` (direct OR sponsored) |
| Consultant capability projection | `BillingService.consultant_capability` (`backend/services/billing.py:858`) |

### Are the plans' feature values meaningful today? — **NO**

Verified live: **every** `billing_plans` row has `features = {"reports": true}`
(enterprise adds `"custom": true`). Therefore:

* `features.manual_processing` — **absent from every plan**;
* `features.consultant` — **absent from every plan**;
* `features.consultant_manual_processing` — **absent from every plan**.

All current manual-processing and consultant entitlement therefore rests **entirely** on
the legacy boolean columns, and `consultant_capability()` resolves to
`entitled: false` for every organisation.

### `api_access`, `managed_processing_available` — stored but **not consumed**

These columns are defined, seeded, and projected through the domain/repository/API
layers, and asserted in tests — but a repository-wide search found **no entitlement
enforcement path that reads them**. They are currently **IMPLEMENTED BUT DISCONNECTED**
(metadata only).

---

## 9. Legacy / fallback feature findings

| Legacy artefact | Status | Evidence |
| --- | --- | --- |
| `billing_plans.assisted_processing_available` | **ACTIVE fallback** — grants DIRECT manual-processing entitlement when `features.manual_processing` is absent | `backend/domain/manual_processing.py:220`; `test_manual_processing_routing.py:88` |
| `billing_plans.managed_processing_available` | Metadata only — not enforced | §8 |
| `billing_plans.api_access` | Metadata only — not enforced | §8 |
| `customer_subscriptions.plan` / `.status` / Stripe columns | Documented legacy, retained; **not** used by D37 | migration comments |
| `organizations.subscription_status`, `subscription_tier`, `trial_start_date`, `trial_end_date`, `subscription_id`, `billing_contact_*`, `billing_address` | Legacy columns retained on `organizations`; `UPDATE` revoked from `authenticated` | `20260824020000_...sql:102`; live column listing |
| `organizations.billing_mode` | **ACTIVE** — D37-0 per-customer mode | live data: `CREDIT`=23, `NULL`=2 |
| `usage_tracking` | Retained; used by `UsageTrackingRepository` for STANDARD-mode period usage | `backend/data/billing.py:839` |
| Legacy admin CRA (`/admin/*`) subscription badge | `admin/src/pages/admin/Customers.js:263` renders `customer.subscription_tier` | read-only display |

Legacy compatibility is **preserved, not narrowed**: the Professional/Business/Enterprise
entitlement carried by `assisted_processing_available` still grants entitlement.

---

## 10. Admin plan-management findings

**Backend / API capability — COMPREHENSIVE.**
`backend/api/v3_commercial.py`, prefix `/api/v3/commercial`, every endpoint gated by
`require_internal_staff` + `can_manage_billing` (`_require_billing_admin`,
`backend/api/v3_commercial.py:56`):

| Capability | Endpoint |
| --- | --- |
| Commercial overview + plan catalogue | `GET /overview` |
| List / read / update versioned commercial rules | `GET /config`, `GET /config/{key}`, `PUT /config/{key}` |
| List / read plans | `GET /plans`, `GET /plans/{plan_code}` (current + full history) |
| **Create plan** | `POST /plans` |
| **Publish new plan version** | `PUT /plans/{plan_code}` |
| Credit ledger read | `GET /ledger` |
| Organisations + billing mode | `GET /organizations` |
| Subscribers | `GET /subscriptions`, `POST /subscriptions` (activate), `POST /subscriptions/{id}/status` |
| Orders | `GET /orders`, `GET /orders/{id}`, `POST /orders/{id}/complete` |
| Storage metering | `GET /storage` |
| Payment records | `GET /payments` |
| Per-org entitlement | `GET /entitlement/{organization_id}` |
| Credit operations | `POST /credits/grant|adjust|reverse|refund|rollover` |

`PlanCreate` / `PlanUpdate` (`backend/api/v3_commercial.py:160,181`) accept **name,
description, price, currency, billing_interval, included_credits,
included_storage_bytes, team_member_limit, processing_limits, features, billing_mode,
assisted_processing_available, managed_processing_available, api_access, is_active**.
So the **API can configure every plan field, including the `features` JSONB**.

**Actual visible Admin UI capability — PARTIAL.**
`frontend/src/v3/ops/CommercialTab.jsx`, reachable only when
`p.can_manage_billing` (`frontend/src/v3/ops/OperationsPage.jsx:126`):

| UI capability | Present? | Evidence |
| --- | --- | --- |
| View commercial rules + version history | Yes | `CommercialTab.jsx:288` |
| Edit versioned config keys (incl. default billing mode) | Yes | `CommercialTab.jsx:114,136` |
| View plan catalogue with version | Yes | `CommercialTab.jsx:333,352` |
| Create a plan | Yes — plan code, name, price, credits, storage GB, billing mode | `CommercialTab.jsx:196-230` |
| Publish a new plan version | Yes — but **only `name`, `price`, `included_credits`** are sent | `CommercialTab.jsx:170-194` |
| View subscribers + change subscription status | Yes | `CommercialTab.jsx:511,522` |
| Activate a subscription for an org | Yes | `CommercialTab.jsx:538-553` |
| View credit ledger | Yes | `CommercialTab.jsx:485` |
| **Edit plan `features` / entitlement blocks** | **NO UI** (API supports it) | no `features` field in `planEdits` |
| **Edit `billing_interval`, `is_active`, `team_member_limit`, `processing_limits`** | **NO UI** on version publish | `CommercialTab.jsx:172-177` |
| **Edit `assisted_processing_available` / `managed_processing_available` / `api_access`** | **NO UI** on version publish | same |
| **Activate / deactivate a plan** | **NO UI** (`is_active` sent only at creation) | same |
| **View / manage consultant coverage or sponsored capacity** | **NO UI** in Commercial tab | grep for `coverage|allocation|sponsored` in `CommercialTab.jsx` → 0 matches |
| Manual Processing governance screen (reads plan entitlements) | Yes, in a **separate** tab | `frontend/src/v3/ops/ManualProcessingTab.jsx:172` |
| Billing UI in the legacy admin CRA (`admin/`) | **NONE** — only a `subscription_tier` badge | `admin/src/` grep |

---

## 11. Customer subscription UX findings

**Route:** `/billing` → `frontend/src/v3/customer/BillingPage.jsx`.
**Navigation:** D18 customer model includes `{ to: '/billing', label: 'Billing' }`
(`frontend/src/v3/components/V3Layout.jsx:34`).

What a customer currently sees and can do:

| Area | State |
| --- | --- |
| Current plan / active subscription | **Visible, read-only** — plan name, version, lifecycle status, price/currency/interval (`BillingPage.jsx:123-128`) |
| Billing mode | Visible, read-only (`:129`) |
| Credits | Balance + included monthly (`:134`) |
| Storage | Usage / included + a "Re-measure" action (`:139`) |
| STANDARD allowance | Visible when mode is STANDARD (`:147`) |
| Credit history | Visible table (`:156`) |
| Assisted Processing | **Customer can create an estimate** and approve/cancel orders (`:175`, `:228`) |
| Managed Processing | **Customer can submit a request** (`:205`) |
| Orders | Visible table with Approve/Cancel (`:222`) |
| Payments | Read-only provider-neutral records, section hidden unless records exist (`:249`) |
| **Plan selection / pricing at plan level** | **NO** |
| **Checkout / purchase** | **NO** |
| **Upgrade / downgrade** | **NO** |
| **Cancel / renew subscription** | **NO** |
| **Invoices / payment method management** | **NO** |
| **Dedicated "Subscription" page/route** | **NO** (only "Billing") |

**Explicit record: there is no customer subscription self-service UI.** The customer
Billing page is a *commercial status + assisted/managed order request* surface. It
cannot create, change or cancel a subscription.

Note also that a customer has **no write access** to commercial state at all —
`/api/v3/billing/*` exposes only reads plus order create/approve/cancel.

---

## 12. Consultant subscription UX findings

| Question | Finding |
| --- | --- |
| Consultant subscription state UI | **NOT FOUND** |
| Consultant plan selection | **NOT FOUND** |
| Consultant billing / pricing / purchase | **NOT FOUND** |
| Consultant-firm subscription UI | **NOT FOUND** |
| Client-sponsored coverage UI | **NOT FOUND** |
| Manual Processing coverage UI | **NOT FOUND** in the UI |

Evidence: `frontend/src/v3/consultant/ConsultantPage.jsx` contains **no** billing,
subscription, coverage or allocation surface (its only tab set is a stage filter:
All items / Extraction / Mapping / Validation / Calculation / Customer review).
A grep across `frontend/src/v3/consultant/` and `frontend/src/v3/customer/` for
`coverage|sponsored|subscription` returns only two incidental hits in
`BillingPage.jsx`.

**Server-side consultant commercial capability does exist:**
`BillingService.consultant_capability()` resolves `features.consultant` from the
consultant firm's own organisation subscription. Because no plan currently carries that
block (§8), the resolved capability is `entitled: false` for every organisation, and
there is **no UI that would display it**.

### CT-MP-SUB-003 backend (kept separate, per task instruction)

The Admin-grade control plane exists in `backend/api/manual_processing_admin.py`:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v3/admin/manual-processing/coverage/{consultant_id}` | Firm coverage state (mode, capacity, allocated, available, over-allocated, eligible clients, ledger) |
| POST | `/api/v3/admin/manual-processing/allocations` | Allocate an eligible client (capacity + eligibility enforced server-side) |
| DELETE | `/api/v3/admin/manual-processing/allocations/{allocation_id}` | Release an allocation |
| GET | `/api/v3/admin/manual-processing/clients/{organization_id}` | Full client state (direct, sponsored, relationship, governance, PE, effective) |

### CT-MP-SUB-004 (uncommitted, appeared during discovery)

`backend/api/v3_manual_processing_coverage.py` (untracked, 405 lines) + its router
registration add **customer/consultant-facing** projection endpoints:

| Method | Path | Authorization |
| --- | --- | --- |
| GET | `/api/v3/organizations/{organization_id}/manual-processing` | `require_org_member()` |
| GET | `/api/v3/consultants/me/manual-processing/coverage` | `require_consultant` |
| POST | `/api/v3/consultants/me/manual-processing/allocations` | `require_consultant` + `can_manage_clients` |
| DELETE | `/api/v3/consultants/me/manual-processing/allocations/{allocation_id}` | `require_consultant` + `can_manage_clients` |

This is API-only: **no frontend surface consumes it yet.**

---

## 13. Payment / checkout findings

> ## **NO PAYMENT/CHECKOUT IMPLEMENTATION FOUND**

Evidence:

* **No provider SDK or client** for Stripe, PayPal, Wise, Paddle, GoCardless,
  Braintree or Square exists anywhere in `backend/`, `frontend/src/`, `admin/src/` or
  `supabase/`. The only `stripe` matches are **legacy column names** in
  `customer_subscriptions` / `consultant_billing` (unused) and explanatory migration
  comments.
* **No checkout session, payment intent, provider webhook handler, or invoice
  synchronisation** exists.
* `backend/services/billing.py:796` `record_payment_intent()` writes a
  **provider-neutral internal record** (`billing_payment_records`) when an order is
  approved. It calls no external service — `provider` is a free-text label.
* `billing_payment_records` is documented as "payment intent/confirmation for future
  PayPal / Wise / card adapters" (`20260824030000_...sql:158`).
* Migration headers explicitly state "Provider-neutral: no provider integration, no
  provider SDK, no checkout."
* The public pricing page states: *"No online checkout — CarbonTally is preparing for
  commercial launch and access is by arrangement"* (`frontend/src/PricingPage.jsx:1-4`).
* Verified live: `billing_payment_records` = 0 rows.

Subscription provisioning is therefore **100% administrative** today
(`POST /api/v3/commercial/subscriptions`). There is no purchase path a customer or
consultant could use.

---

## 14. Consultant-billing legacy findings

Table `public.consultant_billing` (`supabase/migrations/00000000000000_init_schema.sql:1618`):
`consultant_id` (FK → `consultant_profiles`), optional `client_id`, `plan`,
extraction limits/usage, `billing_cycle`, subscription start/end dates,
`last_invoice_date`/`next_invoice_date`, `auto_extraction_price`,
`manual_extraction_price`, Stripe-named columns, `currency`.

| Question | Finding |
| --- | --- |
| Real data usage? | **No** — verified live: **0 rows** |
| Code references? | **None in application code.** Only negative RLS tests reference it: `backend/tests/integration/test_v3_rls_behavior.py:543,550,556` and `backend/tests/integration/test_final_03_rls_remediation_live.py:469,494` (asserting `authenticated` cannot write it) |
| Active? | **No** |
| Deprecated? | **Yes — DEPRECATED / LEGACY (schema-only)** |
| Conflicts with org-scoped billing? | **Yes, conceptually.** It models consultant-as-billing-entity with Stripe columns, which contradicts the ratified organization-scoped, provider-neutral D37 architecture |
| Reactivate? | **NOT DONE** — per the task instruction the subsystem was not reactivated, modified or removed |

Security posture retained: RLS enabled, **0 policies**, `authenticated` retains
`SELECT` only; `INSERT/UPDATE/DELETE` revoked (`20260824020000_...sql:65`).

---

## 15. Existing PO / business decisions

| # | Decision | Source document | Date / version | Status | Current implementation |
| --- | --- | --- | --- | --- | --- |
| 1 | CarbonTally (UK) Ltd is the direct merchant; owns the commercial relationship | `docs/Pricing/CARBONTALLY_DIRECT_MERCHANT_COMMERCIAL_ARCHITECTURE_V1.md` | 2026-08-23, V1 | Reference decision (Decision owner: PO) | Consistent — billing is org-scoped, in-house, no reseller |
| 2 | Four plans (Starter / Professional / Business / Enterprise), credit-based processing | `CarboTally_V3_Draft_Pricing_Strategy...md`, D37-0 seed | 2026-08-23 DRAFT | DRAFT — proposed starting points | Implemented as the seeded catalogue |
| 3 | Assisted & Managed Processing as commercial services | `docs/Pricing/CARBONTALLY_ASSISTED_AND_MANAGED_PROCESSING_SPECIFICATION_V1(1).md` | 2026-08-23 | Product/commercial decision **draft** | Implemented (estimate→approval→order; managed request) |
| 4 | Billing/commercial architecture must be configurable, versioned and provider-neutral; two billing modes CREDIT/STANDARD; common order model | `CARBONTALLY_V3_D36_BILLING_COMMERCIAL_ARCHITECTURE_AUDIT.md` | 2026-08-23, D36 COMPLETE / HARD STOP | Ratified direction | Implemented D37-0 + D37 |
| 5 | P0 billing security remediation (no client writes to authoritative billing state) + configurable subscription foundation | `CARBONTALLY_V3_D37_0_...REPORT.md` | 2026-08-24 | COMPLETE, HARD STOP | Implemented (grants revoked, deny-by-default RLS) |
| 6 | Provider-neutral master commercial billing, lifecycle, entitlements, credits, orders, idempotency. **No payment provider** | `CARBONTALLY_V3_D37_MASTER_COMMERCIAL_BILLING_COMPLETION_REPORT.md` | 2026-08-24 | **PASS** — HARD STOP | Implemented |
| 7 | Commercial/billing architecture reconciliation; verdict "READY WITH PO DECISIONS" | `CARBONTALLY_P6_BILL_0_COMMERCIAL_ARCHITECTURE_RECONCILIATION.md` | 2026-09-04 | READ-ONLY reconciliation | Consistent with current code |
| 8 | Registration mode (D-A), org→consultant additive entitlement (D-C), client-grant boundary (D-D), **org-scoped credit ownership + denial without entitlement (PO-D7)** | `CARBONTALLY_P6_BILL_1_ENTITLEMENT_AND_CONSULTANT_COMMERCIAL_IMPLEMENTATION.md` | 2026-09-04 | IMPLEMENTED (ratified decisions) | Implemented — `ensure_processing_entitlement` fails closed; `features.consultant` |
| 9 | Manual Processing is a **subscription-plan capability**; two entitlement paths (direct customer / consultant-sponsored); `SELECTED_CLIENTS` + `ALL_ELIGIBLE_CLIENTS`; firm purchases coverage through its own organisation subscription | `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md` (**CT-PO-MP-SUB-003**) | 2026-10-04 | **PO APPROVED — AUTHORITATIVE** | Backend implemented (CT-MP-SUB-003/004). **Not applied to the local DB; no UI** |
| 10 | MP commercial/entitlement ASCII UI/UX (Admin / Customer / Consultant surfaces, transitions, empty & error states) | `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` | 2026-10-04 | **PROPOSED FOR PO APPROVAL** | Not implemented (no frontend) |
| 11 | Canonical staff/admin control plane is V3 `/ops` (legacy `/admin/*` CRA to be retired) | `CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md` (CL-66) | Ratified; last verified 2026-08-30 | Ratified, legacy retirement not PO-signed | `/ops` carries Commercial; legacy CRA has no billing UI |
| 12 | Configurable Subscription & Billing module: DB-authoritative pricing, plan/add-on/trial/discount configuration, payment-provider abstraction, webhook-driven lifecycle, central entitlement. **Manual Processing is not a separate billing system** | `docs/architecture/CT-SUB-001_...Product_Specification.md` | 2026-10-04, v0.1 | **PROPOSED — NOT YET AUTHORIZED FOR IMPLEMENTATION** | Only the D37 subset exists; provider abstraction, checkout, trials, add-ons absent |
| 13 | Subscription & Billing UI/UX (public, customer, consultant, Platform Admin surfaces; checkout; plan change; invoices; admin plan editor) | `docs/architecture/CT-UX-SUB-001_...UI_UX_Specification.md` | 2026-10-04 | **PROPOSED — NOT YET AUTHORIZED** | Not implemented |
| 14 | Existing-first rule: extend the existing subscription infrastructure; do not create a new Subscription model | `CT-SUB-001` §6; `CT-UX-SUB-001` §63 | 2026-10-04 | Proposed (consistent with D36/D37 discipline) | Already honoured by D37/CT-MP-SUB-003 |

---

## 16. Conflicting / superseded decisions

| Conflict | Documents | Date/version | Nature | Apparent status |
| --- | --- | --- | --- | --- |
| MP Subscription Options duplicated | `CarbonTally_Manual_Processing_Subscription_Options_old.md` (status "PO Decision / Design Specification") vs `CarbonTally_Manual_Processing_Subscription_Options.md` (status "PO APPROVED — AUTHORITATIVE") | both dated 2026-10-04 | Same title, differing status; the `_old` file is the predecessor | **`_old` appears SUPERSEDED** by the PO-APPROVED version. Not deleted. Reported, **not reconciled** |
| Currency of the live plan catalogue | Live DB: starter/business current = `USD`; professional/enterprise = `GBP`; `billing_commercial_config.assisted_pricing` = `USD` | DB effective 2026-09-19 | Mixed currencies within one catalogue | **UNRESOLVED CONFLICT** |
| Public price display vs catalogue currency | `frontend/src/PricingPage.jsx` shows `£49 / £149 / £399`; DB current starter/business are `USD 49 / USD 399` | 2026-10-04 vs DB | Public surface implies GBP; catalogue says USD. Also hard-codes commercial values in frontend code, which `CT-SUB-001` §3 ("avoid hard-coded commercial values in frontend code") forbids | **UNRESOLVED CONFLICT** |
| "No online checkout" vs proposed checkout | D37 migration headers ("no provider integration, no checkout") + `PricingPage.jsx` ("No online checkout") vs `CT-SUB-001` §20-23 / `CT-UX-SUB-001` §13-16 (checkout + provider abstraction) | 2026-08-24 vs 2026-10-04 | Architecture boundary vs proposed expansion | **PO DECISION REQUIRED** (CT-SUB-001 is not approved) |
| Plan version duplication | `20260824030000_d37_master_commercial_billing.sql` applied twice | 2026-08-24 and 2026-09-19 | Non-idempotent seed produced redundant `v2`/`v3` plan rows | **Current defect in demo-lab data**; not a PO conflict |
| Billing mode default vs actual | D37-0 backfilled all orgs to `CREDIT`; live: 2 orgs have `NULL billing_mode` | 2026-08-24 onward | Orgs created after the backfill were not assigned a mode (resolution falls back to `DEFAULT`=CREDIT) | **Observation / data-consistency gap** |
| P6-BILL-0 "READY WITH PO DECISIONS" vs D37 already complete | `P6_BILL_0` (2026-09-04) describes decisions as pending; `P6_BILL_1` (2026-09-04) states they were "now ratified" | 2026-09-04 | Sequencing, resolved in the same day | **SUPERSEDED** by P6-BILL-1 |

No conflicting records were silently reconciled.

---

## 17. Current navigation gaps

### Platform Admin / Platform Owner — confirmed gap

| Expected surface | Actual state |
| --- | --- |
| A "Subscription" menu | **DOES NOT EXIST anywhere** |
| Plan management navigation | **Indirect**: `/ops` → tab **"Commercial"**, visible **only** if the staff profile has `can_manage_billing` (`OperationsPage.jsx:126`) |
| Subscription management navigation | **Same Commercial tab** (a "Subscriptions (commercial relationships)" table + activate form) |
| Commercial controls | Config keys + plans + ledger + subscriptions + orders + storage + payments, all inside the one Commercial tab |
| Public marketing pricing page | `/pricing` (static, no checkout) |

**This is the root cause of the Product Owner's observation.** There is no navigation
item named "Subscription" or "Billing" for administrators; the entire commercial control
plane is a single tab named **"Commercial"** nested inside **Operations**, and it is
hidden entirely unless `can_manage_billing` is set. A Platform Owner without that
permission sees **no** commercial control surface at all.

### Customer

| Expected | Actual |
| --- | --- |
| "Subscription" menu | Absent — the item is labelled **"Billing"** at `/billing` |
| Pricing / purchase | Absent from the authenticated app (`/pricing` is a public marketing page only) |
| Current-plan visibility | **Present** (read-only plan card inside Billing) |

### Consultant

| Expected | Actual |
| --- | --- |
| Subscription / coverage menu | **Absent entirely** — the consultant nav item is only "Consultant" (`/consultant`) |
| Pricing / purchase | Absent |
| Firm subscription visibility | Absent |

### Public

`/pricing` exists and links from the public header/footer; it presents four plans,
credit bands, and an explicit "no online checkout" statement.

---

## 18. Security / RLS findings

Verified against the **live local database** (read-only).

| Control | Finding |
| --- | --- |
| Billing ownership scope | **Organization-scoped** (`customer_subscriptions.organization_id NOT NULL`). No user-scoped billing. Consultant firm coverage is expressed through the firm's *own organisation* subscription |
| Who can VIEW plans | Admin (`/api/v3/commercial/plans`, `can_manage_billing`). **No customer/consultant plan-catalogue endpoint exists.** Customers see only their own resolved plan via `/api/v3/billing/me`. Public sees the static pricing page |
| Who can VIEW subscription data | Customer: own org only (`/api/v3/billing/me`, `require_org_member`). Admin: all (`/api/v3/commercial/subscriptions`) |
| Who can CHANGE subscriptions | **Admin only** (`can_manage_billing`). No customer or consultant write path |
| RLS — billing tables | `billing_plans`, `billing_commercial_config`, `billing_credit_ledger`, `billing_orders`, `billing_storage_usage`, `billing_payment_records`, `billing_idempotency_keys`: RLS **enabled with 0 policies** (deny-by-default). No `anon`/`authenticated` grants exist |
| RLS — `customer_subscriptions` | RLS enabled; **1 policy**: `customer_subscriptions_tenant_select` (`SELECT`, role `authenticated`). Write policies dropped; `INSERT/UPDATE/DELETE` revoked at table level (`20260824020000_...sql:57-64`). Confirmed live: `authenticated` holds only `SELECT` |
| RLS — `usage_tracking` | Same posture: `usage_tracking_tenant_select` (`SELECT`), writes revoked. Confirmed live |
| RLS — `consultant_billing` | Enabled, **0 policies**, `authenticated` holds only `SELECT`; writes revoked. Confirmed live |
| RLS — `organizations` | Table-level `UPDATE`/`INSERT`/`DELETE` **revoked** from `authenticated` (`20260824020000_...sql:102,106`) — closes direct billing/trial/tax column mutation via PostgREST. This makes the `organizations_org_update` policy inert by design |
| API authorization | Admin API: `require_internal_staff` **and** `can_manage_billing`. Customer API: `require_org_member()` with server-side org resolution (`v3_billing.py:295`). Consultant coverage API: `require_consultant` (+`can_manage_clients` for writes) |
| Service-role elevation | `service_role` granted `ALL` on the billing tables (49 grants verified). Elevated access is intentional for the server-authoritative BillingService, whose rules remain in FastAPI, not in RLS |
| Idempotency | All commercial mutations require an `idempotency_key` (`_claim_key`, `backend/services/billing.py:882`) backed by `billing_idempotency_keys` |
| Audit | Every commercial change is appended to `audit_trail` with before/after version and reason |

**No security weakness was introduced, weakened or modified by this task.** Notable
*strength*: the D36 P0 (customers self-granting credits/plan through PostgREST) is
confirmed closed in the live database.

**Boundary note (not a defect):** admin billing surfaces rely on a **capability flag**
(`can_manage_billing`) rather than a distinct System Admin role; the task's governing
constitution (§14) requires such capabilities to remain explicit. This is recorded as
context for the future UI design, not a finding.

---

## 19. Subscription-related test evidence

| Test file | Tests | What is actually tested |
| --- | --- | --- |
| `backend/tests/unit/api/test_billing_core.py` | 17 | Credit ledger grant/consume/adjust/rollover/refund/reversal, balances, order lifecycle incl. `approve → payment record → complete`, idempotency conflicts |
| `backend/tests/unit/api/test_commercial_settings.py` | 19 | Admin commercial config versioning, plan create/publish/history, authorization (`can_manage_billing`), subscription activate/status changes |
| `backend/tests/unit/api/test_p6bill1_entitlement_and_consultant_commercial.py` | 23 | PO-D7 entitlement denial, consultant capability from `features.consultant`, registration mode |
| `backend/tests/unit/api/test_p6_2d_entitlement.py` | 2 | Entitlement enforcement at the consultant submission boundary |
| `backend/tests/unit/api/test_ct_mp_sub_003_consultant_coverage.py` | 32 | Firm coverage mode/capacity, `SELECTED_CLIENTS` allocation + release, eligibility enforcement, over-allocation, all-eligible, direct OR sponsored combination |
| `backend/tests/unit/domain/test_consultant_mp_coverage.py` | 22 | Pure-domain coverage rules incl. legacy `assisted_processing_available` compatibility |
| `backend/tests/unit/domain/test_manual_processing_routing.py` | — | Plan→entitlement resolution, `assisted_processing_available` fallback source |
| `backend/tests/unit/api/test_manual_processing_routing.py` | — | Routing decisions |
| `backend/tests/unit/api/fakes.py` | — | In-memory doubles: `BillingPlans`, subscriptions, coverage/allocation, `set_firm_coverage`, `end_client_relationship` |
| `backend/tests/integration/test_v3_rls_behavior.py` | — | **Negative RLS**: `authenticated` cannot write `consultant_billing` etc. |
| `backend/tests/integration/test_final_03_rls_remediation_live.py` | — | Live negative RLS probes incl. `consultant_billing` |
| `backend/tests/e2e/test_p6_2f_invariants.py` | — | End-to-end pipeline invariants |
| `e2e/environment/scripts/run_p6f_acceptance.py`, `seed_lifecycle_fixtures.py` | — | Lifecycle fixtures/acceptance harness |
| `frontend/src/v3/__tests__/api.test.js` | — | Frontend billing/commercial API client contract |

**What is tested vs merely implemented:**

| Area | Tested? |
| --- | --- |
| Credit ledger arithmetic, order lifecycle, idempotency | **Yes** |
| Plan versioning (create/publish/history) at API level | **Yes** |
| Plan `features` JSONB round-trip via the API | **Yes** (API contracts) |
| Consultant coverage domain rules + API | **Yes** |
| RLS deny-by-default on billing tables (negative) | **Yes** |
| `managed_processing_available` / `api_access` **enforcement** | **No tests exist** (and no enforcement code exists) |
| Subscription upgrade/downgrade/cancel/renew semantics | **No** (not implemented) |
| Payment provider / checkout / webhook handling | **No** (not implemented) |
| **Frontend test of the Billing page subscription UI** | **None found** — no `BillingPage` test file exists in `frontend/src/v3/__tests__/` |
| **Frontend test of `CommercialTab`** | Indirect only — `operations-page-assignment-gating.test.jsx` and `operational-health-tab.test.jsx` **mock** `CommercialTab` out |
| Migration idempotency test for the D37 seed | **No** (and the live DB proves it is not idempotent) |

No test suite was executed as part of this discovery task (read-only discovery, no
authorization to run the suite); this section records what exists, not a pass/fail verdict.

---

## 20. Existing-first architecture assessment

**Verdict: the existing architecture IS a sound basis for a future comprehensive
subscription UI/UX. No new subscription system is required.**

### What should be EXTENDED (already correct, merely incomplete)

| Element | Why it is right | What is missing |
| --- | --- | --- |
| `billing_plans` versioned catalogue | Versioning + `effective_from/to` already preserve historical commercial terms; `(plan_code, version)` uniqueness is correct | Seed idempotency; a UI to edit `features`/`billing_interval`/`is_active`/entitlement flags |
| `features` JSONB | Already the ratified canonical entitlement carrier (`features.manual_processing`, `features.consultant`, `features.consultant_manual_processing`) | Plans currently carry only `{"reports": true}` — the blocks must be authored |
| `customer_subscriptions` (org-scoped, one-active-per-org) | Matches the ratified org-scoped ownership model and the consultant-firm-via-its-own-org model | Self-service lifecycle transitions (upgrade/downgrade/cancel/renew) are absent by design |
| `billing_commercial_config` versioned rules | Already supports DB-authoritative configuration without deployment | `registration_mode` has **no row** → falls back to `OPEN_REGISTRATION` |
| `billing_orders` common order model | Covers automated/assisted/managed/storage; immutable items snapshot | Not used for subscription purchases |
| `billing_credit_ledger` append-only + derived balance | Correct financial primitive | Unused in practice (0 rows) |
| `billing_payment_records` provider-neutral | **Exactly** the right shape for a future provider abstraction — the interface already exists | No adapter; no `provider` enum; no webhook ingestion |
| `billing_idempotency_keys` | Correct foundation for webhook/checkout retries | Unused for provider events |
| `billing_storage_usage` | Server-measured, never browser-reported | — |
| Admin `/api/v3/commercial` API | Already covers plan CRUD, versioning, subscriptions, credits, entitlements, orders | Frontend exposes only a subset |
| `BillingService.get_entitlement` | Single server-authoritative entitlement resolver | Should become the one central resolver the new UI reads |

### What should REMAIN unchanged

* Organization-scoped billing ownership (`customer_subscriptions.organization_id`).
* The deny-by-default RLS posture and the revoked `authenticated` write grants.
* The `organizations` table-level write revocation.
* The idempotency + append-only audit requirements on every commercial mutation.
* Existing customer Billing functionality (plan card, credits, storage, credit history,
  Assisted estimate/approval, Managed request, Orders) — `CT-UX-SUB-001` §18 requires
  integration, not replacement.

### What is legacy

* `consultant_billing` — schema-only, 0 rows, no code, contradicts org-scoped billing.
  **Do not reactivate.**
* `customer_subscriptions.plan` / `.status` / Stripe-named columns — documented legacy.
* `organizations.subscription_status` / `subscription_tier` / `trial_*` /
  `billing_contact_*` / `billing_address` — legacy columns (write-revoked).
* The legacy admin CRA (`admin/`) as a commercial surface — CL-66 says `/ops` is canonical.

### What is missing

1. A payment-provider abstraction implementation + provider selection + webhook
   ingestion driven subscription state (currently 0%).
2. Any customer/consultant self-service subscription **UI** (currently 0%).
3. A plan **features/entitlement editor** and plan activation control in the Admin UI.
4. Checkout, trials, discounts, add-ons, proration, invoicing, tax.
5. Consultancy coverage UI (backend endpoints exist; frontend absent).
6. Meaningful `features` values in the plan catalogue.

### What must NOT be duplicated

* A second subscription/plan table — `CT-SUB-001` §6 and `CT-MP-SUB-003` §25 both forbid it.
* A second entitlement resolver — `BillingService.get_entitlement` and the
  `manual_processing` domain resolvers are the canonical pair.
* A second order/payment/idempotency/audit model.
* A second consultant-coverage concept — `consultant_clients` (eligibility) +
  `consultant_mp_allocations` (selected capacity) + the firm's plan (commerce).
* A separate consultant organisation (the firm's `organization_id` is the subscription owner).

---

## 21. CT-MP-SUB-003 integration assessment

### How it sits on the existing architecture

```text
EXISTING (D37)                          CT-MP-SUB-003 (added)
------------------------------------    --------------------------------------------
billing_plans.features JSONB       →    + features.consultant_manual_processing
                                        { enabled, mode, selected_capacity }
customer_subscriptions (org-scoped)→    REUSED — the consultant FIRM's own organisation
                                        subscription is the sponsorship source
consultant_profiles.organization_id→    the firm ↔ organisation linkage used to find
                                        that subscription
consultant_clients (relationship)  →    REUSED — ELIGIBILITY anchor (unchanged gate)
NEW                                 →    consultant_mp_allocations (selected capacity only)
FIN-06 manual_processing_grants    →    REUSED — operational enable/disable, NOT commerce
ManualProcessingRouter             →    entitlement_for() = combine(direct, sponsored)
```

**Design integrity: high.** CT-MP-SUB-003 **reuses** the subscription table, the plan
feature carrier, the relationship model, the governance model and the audit model. It
created exactly **one** new table and **no** parallel subscription/plan/entitlement
system. This is fully consistent with `CT-SUB-001` §6/§58.

**Layering distinction preserved:**
commercial entitlement (subscription plan) ≠ eligibility (`consultant_clients`)
≠ operational activation (FIN-06 grants) ≠ capacity allocation
(`consultant_mp_allocations`) ≠ PE assignment. The task's required separation of
"existing subscription architecture" from the "consultant-sponsored layer" holds.

### Integration gaps identified (NOT FIXED, per task §18)

| # | Gap | Severity | Evidence |
| --- | --- | --- | --- |
| G-1 | **The CT-MP-SUB-003 migration is NOT applied to the local database.** `public.consultant_mp_allocations` does not exist. The sponsored-coverage model therefore has **no persistence** in the running local environment | High (integration) | Live DB: `relation "public.consultant_mp_allocations" does not exist` |
| G-2 | **`consultant_profiles.organization_id` does NOT exist in the local database.** It is added by `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql:281`, which is not applied. Without it the firm→subscription link that CT-MP-SUB-003 depends on cannot resolve at runtime | High (integration) | Live DB column listing has no `organization_id`; the FK/index exist only in the migration file |
| G-3 | `public.manual_processing_processors` does not exist locally — the routing migration (`20261030000000`) is likewise unapplied | Medium (integration) | Live DB probe |
| G-4 | **No plan carries `features.consultant_manual_processing`**, so `sponsored_entitlement` can never be true. The capability exists in code but is unreachable in data | High (commercial) | All 8 plan rows: `features` = `{"reports": true}` |
| G-5 | `mode`/`selected_capacity` are plan-configurable only through the **API**; the Admin UI cannot edit plan `features` at all | Medium (UX) | §10 |
| G-6 | No Admin UI for consultant coverage/allocation (backend endpoints delivered; `CT-MP-SUB-003` §27 defers the frontend) | Medium (UX) | commercial/admin + `ManualProcessingTab` have no coverage UI |
| G-7 | Auto-release of a selected allocation on consultant-client termination is **DEFERRED** (documented and justified in the CT-MP-SUB-003 report §27) | Low | CT-MP-SUB-003 report §1 |
| G-8 | The coverage read/write surfaces are split across **two** uncommitted API modules (admin: `manual_processing_admin.py`; customer/consultant: `v3_manual_processing_coverage.py`) with no shared projection helper — a duplication risk to monitor, not a defect today | Low | Both files inspected |

**G-1/G-2/G-3 are environment/migration-state gaps, not code defects**: the repository
contains the migrations; the local demonstration database simply has not applied
`20261010000000`, `20261030000000` or `20261101000000`. Because AGENTS.md §2 ranks
*actual database state* above *current migrations*, this is reported as the authoritative
current state, and it means **CT-MP-SUB-003 cannot be demonstrated end-to-end in the
current local environment as-is.**

---

## 22. Classification matrix

| Area | Classification | Basis |
| --- | --- | --- |
| `billing_plans` (versioned catalogue) | **IMPLEMENTED** | Migration + domain + repo + API + Admin UI + live rows |
| `billing_plans` seed idempotency | **PARTIALLY IMPLEMENTED** | Duplicate v2/v3 rows in live data |
| `billing_plans.features` values (meaningful entitlements) | **NOT FOUND / NOT AUTHORED** | Every plan: `{"reports": true}` |
| `customer_subscriptions` (org-scoped, one active) | **IMPLEMENTED** | Migration + repo + service + live table; 0 rows |
| Subscription lifecycle (states + Admin transitions) | **IMPLEMENTED** | CHECK constraints; activate/status endpoints |
| Subscription self-service (upgrade/downgrade/cancel/renew) | **NOT FOUND** | No endpoints, no UI |
| `billing_commercial_config` (versioned rules) | **IMPLEMENTED** | 7 current keys live |
| `registration_mode` commercial config | **PARTIALLY IMPLEMENTED** | Key supported + fallback; **no row** in live DB |
| `billing_credit_ledger` (append-only, derived balance) | **IMPLEMENTED** | Repo + service + API; 0 rows |
| `billing_orders` (automated/assisted/managed/storage) | **IMPLEMENTED** | Repo + service + customer & admin APIs; 0 rows |
| Assisted Processing (estimate → approval → order) | **IMPLEMENTED** | Customer UI + API + tests |
| Managed Processing request | **IMPLEMENTED** (request only) | Customer UI + API; quote/fulfilment manual |
| `billing_storage_usage` (server-measured) | **IMPLEMENTED** | Repo + refresh endpoint; 0 rows |
| `billing_payment_records` (provider-neutral) | **IMPLEMENTED BUT DISCONNECTED** | Records written on approval; no provider adapter |
| `billing_idempotency_keys` | **IMPLEMENTED** | Enforced on all commercial mutations |
| Payment provider / checkout / webhooks / invoices | **NOT FOUND** | See §13 |
| Plan management (Admin backend/API) | **IMPLEMENTED** | Full CRUD + versioning |
| Plan management (Admin UI) | **PARTIALLY IMPLEMENTED** | Version publish limited to name/price/credits; no `features` editor; no activate/deactivate |
| Commercial config editing (Admin UI) | **IMPLEMENTED** | Versioned config editor |
| Subscription management (Admin UI) | **IMPLEMENTED** | Subscriber table + status change + activation form |
| Customer subscription experience | **PARTIALLY IMPLEMENTED** | Read-only status + order requests; no purchase/plan change |
| Consultant subscription experience | **NOT FOUND** | No UI, no plan, no coverage display |
| Consultant capability entitlement (`features.consultant`) | **PARTIALLY IMPLEMENTED** | Resolver + API capability projection implemented; **no plan carries the block** |
| `assisted_processing_available` (legacy entitlement) | **IMPLEMENTED** (active fallback) | Enforced in domain + tests |
| `managed_processing_available` | **IMPLEMENTED BUT DISCONNECTED** | Stored/projected only; no enforcement |
| `api_access` | **IMPLEMENTED BUT DISCONNECTED** | Stored/projected only; no enforcement |
| `consultant_billing` | **DEPRECATED / LEGACY** | 0 rows, 0 code refs, Stripe columns, org-scope conflict |
| Legacy `organizations.subscription_*` / `trial_*` columns | **DEPRECATED / LEGACY** | Retained; write-revoked |
| Admin "Subscription" navigation | **NOT FOUND** | Only `/ops` → "Commercial" tab |
| Customer "Subscription" navigation | **NOT FOUND** | Only `/billing` ("Billing") |
| Consultant subscription/coverage navigation | **NOT FOUND** | — |
| Public pricing page | **IMPLEMENTED** (static, no checkout) | `/pricing` |
| CT-MP-SUB-003 consultant coverage (domain + backend) | **IMPLEMENTED** (uncommitted) | Domain rules + tests + admin API |
| CT-MP-SUB-003 consultant coverage (persistence applied) | **BLOCKED** | Migration not applied locally; `consultant_profiles.organization_id` absent |
| CT-MP-SUB-003 coverage UI (admin/customer/consultant) | **DEFERRED** | Justified in the CT-MP-SUB-003 report §27 |
| CT-MP-SUB-004 customer/consultant coverage API | **IMPLEMENTED** (uncommitted, API-only, no UI) | File inspected |
| CT-UX-MP-SUB-003 ASCII UI/UX spec | **PO DECIDED — NOT IMPLEMENTED** | Status "PROPOSED FOR PO APPROVAL"; no frontend |
| CT-SUB-001 product specification | **PO OPEN / UNDECIDED** | Status "PROPOSED — NOT YET AUTHORIZED FOR IMPLEMENTATION" |
| CT-UX-SUB-001 UI/UX specification | **PO OPEN / UNDECIDED** | Status "PROPOSED — NOT YET AUTHORIZED FOR IMPLEMENTATION" |
| Payment provider selection / final prices / trials / proration / refunds | **PO OPEN / UNDECIDED** | CT-SUB-001 §57, CT-UX-SUB-001 §64 |
| Trial / free plan implementation | **NOT FOUND** | `trial` is a lifecycle value only |
| Discounts / promotions | **NOT FOUND** | — |
| Add-ons catalogue | **NOT FOUND** | — |
| Tax / VAT in billing | **NOT FOUND** | Legacy `organizations.tax_rate` column only |
| Invoicing / invoice synchronisation | **NOT FOUND** | — |
| Billing alerts / past-due dunning / grace period | **NOT FOUND** | — |

---

## 23. Open PO decisions that must remain open

The following are **NOT decided** and this discovery task does **not** decide them.

**From `CT-SUB-001` §57 (unchanged, still open):**
final plan names · final plan count · final prices · final currencies · final limits ·
final trial policy · final discount policy · tax implementation/provider ·
payment provider(s) to launch with · payment-provider priority · upgrade proration ·
downgrade semantics · refund policy · failed-payment grace period · data-retention policy ·
enterprise custom pricing model · add-on catalogue · usage-overage policy ·
whether customers may self-serve all plan changes · whether annual plans receive
discounts · exact analytics KPIs.

**From `CT-UX-SUB-001` §64 (unchanged, still open):**
final plan names · final prices · final plan count · trial policy · billing intervals ·
discounts · payment providers to launch with · tax behaviour · upgrade/downgrade
semantics · cancellation semantics · usage-overage behaviour · exact limits · exact add-ons.

**Additional decisions surfaced by this discovery:**

| # | Decision required | Why |
| --- | --- | --- |
| D-1 | **Catalogue currency** — resolve `USD` for starter/business vs `GBP` for professional/enterprise, and reconcile with the public `£` display | Live data conflict (§5, §16) |
| D-2 | Whether the **public pricing page** may keep hard-coded prices, or must read the catalogue | Conflicts with `CT-SUB-001` §3 ("avoid hard-coded commercial values in frontend code") |
| D-3 | Which **payment provider(s)** to launch with, and the provider abstraction contract | No provider exists; CT-SUB-001 §21-24 requires approval |
| D-4 | Whether **self-service plan change/cancellation** is permitted for customers (and for consultants) | Drives whether new customer write endpoints are needed |
| D-5 | Which **plan features/entitlement blocks** must be authored into the catalogue first (e.g. `features.manual_processing`, `features.consultant`, `features.consultant_manual_processing`) | All current manuals/consultant entitlement depends on legacy booleans only |
| D-6 | Whether **CT-MP-SUB-003/004** (and the pending migrations) are ratified for application, and when | Coverage model is unreachable in the local environment (G-1..G-4) |
| D-7 | Whether the **Admin commercial surface** should be promoted out of `/ops` → "Commercial" into a dedicated Subscription/Commercial control plane with its own navigation | Directly addresses the Platform Owner's observation (§17) |
| D-8 | Whether `managed_processing_available` / `api_access` are **enforced entitlements** or **informational metadata** | They are currently metadata only |
| D-9 | Whether to **retire** `consultant_billing` and the legacy `organizations.subscription_*` / `trial_*` columns, and on what migration path | AGENTS.md §79 forbids casual removal |
| D-10 | Whether customer/consultant subscription **visibility** requires new read endpoints or can reuse `/api/v3/billing/me` | §18 |

Also still open (carried forward, unresolved): the PO approval of
`CT-UX-MP-SUB-003` ASCII UI/UX, the PO reconciliation of `CT-SUB-001`/`CT-UX-SUB-001`,
and the disposition of the superseded `..._old.md` MP document.

---

## 24. Exact files inspected

### Migrations / schema (repository)
* `supabase/migrations/00000000000000_init_schema.sql` (customer_subscriptions §1449, usage_tracking §1480, consultant_profiles §1501, consultant_billing §1618)
* `supabase/migrations/20260824020000_d37_0_billing_security_and_configurable_subscription.sql` (full)
* `supabase/migrations/20260824030000_d37_master_commercial_billing.sql` (full)
* `supabase/migrations/20260925000000_p8_rls_4b_group1_enablement.sql`
* `supabase/migrations/20261028000000_ct_final_03_rls_security_remediation.sql`
* `supabase/migrations/20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` (`consultant_profiles.organization_id`)
* `supabase/migrations/20260927000000_p8_fin06_manual_processing_governance.sql`
* `supabase/migrations/20261030000000_manual_processing_routing.sql`
* `supabase/migrations/20261101000000_ct_mp_sub_003_consultant_coverage.sql`
* `database/rc1/004_rc1_rls.sql`, `database/rc2/002_rc2_constraints.sql`, `database/rc2/007_rc2_verification.sql` (RLS/constraint history discovery)

### Backend
* `backend/domain/billing.py` (full)
* `backend/services/billing.py` (structure; entitlement `§87-204`, consultant capability `§823-944`)
* `backend/data/billing.py` (repository/method inventory)
* `backend/api/v3_billing.py` (full)
* `backend/api/v3_commercial.py` (full)
* `backend/domain/manual_processing.py`
* `backend/services/manual_processing_routing.py`
* `backend/api/manual_processing_admin.py`
* `backend/api/v3_manual_processing_coverage.py` (untracked)
* `backend/api/router.py` (registration diff)
* `backend/api/upload_gate.py`, `backend/api/processing_mode.py` (entitlement touchpoint search)

### Frontend
* `frontend/src/v3/customer/BillingPage.jsx` (full)
* `frontend/src/v3/ops/CommercialTab.jsx` (structure + plan edit/create paths)
* `frontend/src/v3/ops/OperationsPage.jsx` (tab gating)
* `frontend/src/v3/ops/ManualProcessingTab.jsx`
* `frontend/src/v3/components/V3Layout.jsx` (navigation model)
* `frontend/src/v3/consultant/ConsultantPage.jsx` (tab inventory)
* `frontend/src/PricingPage.jsx` (public pricing)
* `admin/src/pages/admin/Customers.js` (legacy tier badge)

### Tests
* `backend/tests/unit/api/test_billing_core.py`
* `backend/tests/unit/api/test_commercial_settings.py`
* `backend/tests/unit/api/test_p6bill1_entitlement_and_consultant_commercial.py`
* `backend/tests/unit/api/test_p6_2d_entitlement.py`
* `backend/tests/unit/api/test_ct_mp_sub_003_consultant_coverage.py`
* `backend/tests/unit/domain/test_consultant_mp_coverage.py`
* `backend/tests/unit/domain/test_manual_processing_routing.py`
* `backend/tests/unit/api/test_manual_processing_routing.py`
* `backend/tests/unit/api/fakes.py`
* `backend/tests/integration/test_v3_rls_behavior.py`
* `backend/tests/integration/test_final_03_rls_remediation_live.py`

### Documentation
* `docs/architecture/CT-SUB-001_CarbonTally_Configurable_Subscription_Billing_Product_Specification.md`
* `docs/architecture/CT-UX-SUB-001_CarbonTally_Subscription_Billing_UI_UX_Specification.md`
* `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md`
* `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options_old.md`
* `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md`
* `docs/architecture/CT-MP-SUB-003-implementation-report.md`
* `docs/architecture/CARBONTALLY_P6_BILL_0_COMMERCIAL_ARCHITECTURE_RECONCILIATION.md`
* `docs/architecture/CARBONTALLY_P6_BILL_1_ENTITLEMENT_AND_CONSULTANT_COMMERCIAL_IMPLEMENTATION.md`
* `docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md`
* `docs/architecture/CT-PO-MASTER-WORKPLAN-20260925.md`
* `docs/audit/cline/CARBONTALLY_V3_D36_BILLING_COMMERCIAL_ARCHITECTURE_AUDIT.md`
* `docs/audit/cline/CARBONTALLY_V3_D37_0_BILLING_SECURITY_AND_CONFIGURABLE_SUBSCRIPTION_REPORT.md`
* `docs/audit/cline/CARBONTALLY_V3_D37_MASTER_COMMERCIAL_BILLING_COMPLETION_REPORT.md`
* `docs/Pricing/CARBONTALLY_DIRECT_MERCHANT_COMMERCIAL_ARCHITECTURE_V1.md`
* `docs/Pricing/CARBONTALLY_ASSISTED_AND_MANAGED_PROCESSING_SPECIFICATION_V1(1).md`
* `docs/Pricing/CarbonTally_V3_Draft_Pricing_Strategy_and_Competitive_Benchmark.md`
* `docs/Pricing/CarbonTally_Pricing_Comparison_Baseline_v2.md`
* `docs/Pricing/CarbonTally_Unit_Economics_Baseline_v1.md`
* `docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md`

---

## 25. Exact commands / searches used

**Git baseline**
```bash
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --porcelain
git branch -a
git diff backend/api/router.py
git log -1 --format="last-commit: %h %ad %s" --date=short -- <doc>
git ls-files --error-unmatch <doc>          # tracked vs untracked
```

**Repository sweeps**
```bash
find . -path ./node_modules -prune -o -type f \
  \( -iname "*billing*" -o -iname "*subscription*" -o -iname "*pricing*" \
     -o -iname "*checkout*" -o -iname "*commercial*" -o -iname "*entitlement*" -o -iname "*plan*" \) -print
grep -rl -i -E "billing_plan|customer_subscription|billing|subscription" supabase/migrations/ database/ prisma/
grep -rn "CREATE TABLE.*customer_subscriptions" --include=*.sql .
grep -rn "CREATE TABLE.*consultant_billing"     --include=*.sql .
grep -rn -i "stripe|paypal|wise|checkout_session|payment_intent|paddle|gocardless|braintree|square" \
  backend/ frontend/src/ supabase/ admin/src/
grep -rn "assisted_processing_available|managed_processing_available|api_access" backend/
grep -rn "consultant_billing" backend/ frontend/src/ admin/src/
grep -n "@router\." backend/api/v3_commercial.py backend/api/v3_billing.py
grep -n -i "POLICY" supabase/migrations/*.sql
```

**Live database (read-only; credentials redacted)**
```bash
set -a; . ./backend/.env; set +a
psql "$DATABASE_URL" -tAc "<SELECT ...>"      # every query passed through sed "s#${U}#[REDACTED]#g"
```
Queries executed:
* `information_schema.tables` — billing/subscription table inventory
* `billing_plans` — full catalogue with version, price, currency, interval, credits, flags, `features`
* `billing_plans` — `effective_from` / `effective_to` windows
* `customer_subscriptions`, `billing_orders`, `billing_credit_ledger`,
  `billing_payment_records`, `billing_storage_usage`, `usage_tracking`,
  `manual_processing_grants`, `consultant_billing` — row counts
* `to_regclass()` probes for `consultant_mp_allocations`, `manual_processing_processors`
* `billing_commercial_config` — current keys + versions
* `pg_class.relrowsecurity` + `pg_policies` — RLS enablement + policy counts
* `information_schema.role_table_grants` — `anon`/`authenticated`/`service_role` grants
* `information_schema.columns` — `organizations` billing/trial columns; `consultant_profiles` columns
* `organizations.billing_mode` distribution
* `consultant_profiles` / `consultant_clients` counts

**Environment probes**
```bash
python3 -c "socket connect 127.0.0.1:5432/54321/54322"   # DB reachability
grep -oE '^[A-Za-z_][A-Za-z0-9_]*=' .env backend/.env     # key NAMES only, no values
sha256sum <PO documents>
```

**Not performed (no authorization / out of scope):** applying migrations, running the
test suite, frontend build, browser/E2E verification, any write to code, DB, RLS, Git.

---

## 26. Final conclusion

CarbonTally already possesses a **real, versioned, server-authoritative,
provider-neutral, organization-scoped subscription and billing foundation** (D37-0 →
D37 → P6-BILL-1), comprising:

* a versioned plan catalogue with a canonical `features` JSONB entitlement carrier and
  three legacy boolean entitlement columns;
* a single-active-relationship `customer_subscriptions` table with a 7-state lifecycle;
* versioned commercial configuration, an append-only credit ledger, a common order
  model, server-measured storage metering, provider-neutral payment records and durable
  idempotency;
* a comprehensive Admin/API control plane behind `can_manage_billing`;
* a working customer Billing surface (status, credits, storage, Assisted/Managed orders);
* and a correctly-layered consultant-sponsored Manual Processing model
  (CT-MP-SUB-003/004) that reuses — and does not duplicate — that foundation.

**What is genuinely absent:** any payment provider, checkout, webhook-driven lifecycle,
trial/discount/add-on/proration/invoicing, any customer or consultant self-service
subscription UI, any "Subscription" navigation for any role, meaningful plan feature
values, and any Admin UI for plan `features`/activation or consultant coverage.

**Material integration gaps:** the CT-MP-SUB-003 persistence
(`consultant_mp_allocations`), the P17A `consultant_profiles.organization_id` link and the
Manual Processing routing tables are **not applied to the local database**, and no plan
carries `features.consultant_manual_processing` — so the sponsored-coverage model is
currently unreachable in the running local environment despite being implemented in
code.

**Material defects observed:** duplicate plan versions produced by a non-idempotent D37
seed migration; mixed/incorrect catalogue currency versus the public `£` pricing page;
two organisations without `billing_mode`; `managed_processing_available` and `api_access`
stored but never enforced; and no frontend test coverage for the Billing or Commercial
surfaces.

**Nothing was changed.** No code, migration, database row, RLS policy, UI, commit or push
was touched. All PO decisions were reported as found, with conflicts left explicitly
unreconciled.

## Subscription Architecture Status

**DISCOVERY COMPLETE — OPEN PO DECISIONS REMAIN**

Rationale: the existing architecture and PO history are now sufficiently understood to
proceed (Section 20 explicitly concludes the existing architecture *does* support a
future comprehensive subscription UI/UX without a new subscription system), **but**
`CT-SUB-001` and `CT-UX-SUB-001` are both still `PROPOSED — NOT YET AUTHORIZED FOR
IMPLEMENTATION`, the ten open PO decisions enumerated in Section 23 (notably payment
provider, currency, prices, upgrade/downgrade and cancellation semantics) remain
undecided, and the CT-MP-SUB-003 persistence layer is not applied in the local
environment.

This report does **not** design the subscription UI, does **not** claim PO approval, and
does **not** claim production readiness.

---

**CT-DISC-SUB-001 DISCOVERY COMPLETE**

*Report path: `docs/architecture/CT-DISC-SUB-001-subscription-discovery-report.md`*
