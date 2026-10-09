# CT-COMMERCIAL-SUBSCRIPTION-INDEPENDENT-ASSESSMENT-01

**Document ID:** CT-COMMERCIAL-SUBSCRIPTION-INDEPENDENT-ASSESSMENT-01
**Task type:** INDEPENDENT CURRENT-STATE ASSESSMENT + IMPLEMENTATION PLAN (READ-ONLY)
**Date:** 2026-10-07
**Status:** COMMERCIAL-CURRENT-STATE-ASSESSED

**Read-only compliance statement.** This task produced exactly one artefact: this
document. No code, migration, RLS policy, API contract, frontend file, test, seed
data or Git state was created, modified, deleted or committed. No database row was
written. No `reset`, `clean`, `stash` or `force-push` was executed. No payment
provider was integrated. No new module was implemented.

**Statement classification vocabulary used throughout this document.** Every
substantive claim is tagged:

| Tag | Meaning |
| --- | --- |
| `CURRENT FACT` | Verified against current source and/or the live database during this assessment |
| `IMPLEMENTATION GAP` | Something the current implementation does not do |
| `ARCHITECTURAL RECOMMENDATION` | A proposal — not existing behaviour |
| `UX RECOMMENDATION` | A proposal about user experience — not existing behaviour |
| `PO DECISION REQUIRED` | A business/commercial/policy choice that must not be invented by an agent |
| `UNKNOWN` | Not established by the repository, the live database, or the inspected documents |
| `NOT ESTABLISHED` | The repository does not answer the question |

---

## 1. Executive Summary

**`CURRENT FACT`** CarbonTally already has a real, versioned, server-authoritative,
provider-neutral, **organization-scoped** commercial/subscription foundation. It was
built deliberately in D37-0 → D37 → P6-BILL-1, is committed at HEAD, and is unmodified
by the concurrent consultant workstream.

**`CURRENT FACT`** It is not a payment system. It has: a versioned plan catalogue, a
single-active-relationship subscription table with a 7-state lifecycle, versioned
commercial configuration, an append-only credit ledger with a derived balance, a common
order model (automated/assisted/managed/storage), server-measured storage metering,
provider-neutral payment records, and durable idempotency. It has **no** payment
provider, no checkout, no webhook ingestion, no invoice, no trial, no discount, no
add-on, no proration, and no tax.

**`CURRENT FACT` (live database)** In the running local environment
(`ct_local_93d5cdd`) there are **zero** `customer_subscriptions` rows, **zero**
credit-ledger rows, **zero** orders, **zero** payment records and **zero** storage
snapshots. No organisation currently has a subscription. Because
`BillingService.charge_processing` denies chargeable processing when there is no active
subscription (PO-D7, ratified), **every** organisation's chargeable processing is
denied in this environment.

**`CURRENT FACT` (live database)** The administrative commercial surface is
**unreachable by every identity in the local environment**: `staff_roles` contains only
`manager`, `operator`, `pe_manager`, and **no role carries `can_manage_billing`**. The
D37-0 migration grants the flag to a role named `admin`, which does not exist in this
database. The `/api/v3/commercial/*` API and the `/ops` → **Commercial** tab are
therefore both gated shut. This is the same defect independently recorded as PR-03 in
`CT-PRODUCT-REALITY-AUDIT-01` and it is still current.

**`CURRENT FACT`** Commercial Coverage is **not** general subscription. It is a
**Manual Processing–specific entitlement/eligibility/allocation subsystem layered on top
of** general subscription. It reuses `billing_plans.features` as the purchased-coverage
carrier, `consultant_clients` as the eligibility anchor, and `consultant_mp_allocations`
for selected-client capacity. It created no parallel subscription system.

**`IMPLEMENTATION GAP`** The sponsored-coverage half of that subsystem is
**unreachable at runtime** in the local environment: `consultant_mp_allocations` and
`manual_processing_processors` do not exist in the live database, and
`consultant_profiles.organization_id` (the firm→subscription link) does not exist
either. No plan carries `features.consultant_manual_processing`.

**`CURRENT FACT`** The largest architectural gaps are: (1) no payment abstraction of any
kind; (2) no self-service subscription UI for any role; (3) no "Subscription" navigation
anywhere; (4) plan `features` values are unauthored (every plan carries
`{"reports": true}`); (5) the Admin UI can create a plan but cannot publish most plan
fields, cannot edit `features`, and cannot activate/deactivate a plan.

**`CURRENT FACT`** The public surface contradicts the runtime: the public website states
there is no open signup, while `/signup` performs a real Supabase Auth self-service
signup and `registration_mode` has **no** configuration row, so org creation is permitted
by the documented `OPEN_REGISTRATION` default.

**`PO DECISION REQUIRED`** Ten decisions remain open (currency, prices, payment
provider, self-service plan-change/cancellation semantics, which plan feature blocks to
author, whether the Admin commercial surface is promoted out of `/ops`, whether
`api_access`/`managed_processing_available` are enforced entitlements or metadata,
legacy retirement, and read-endpoint shape).

**Bottom line.** `CURRENT FACT` The architecture is a sound basis for a reusable
Commercial/Subscription module — it does not need to be replaced. `IMPLEMENTATION GAP`
Most of the module requested by the task does not exist yet: the Plan catalogue and
subscription state machine partly exist; pricing is single-value without intervals;
payment, invoicing, entitlement resolution as a first-class reusable service, usage
metering breadth and commercial audit consolidation are absent or partial.

---

## 2. Current-State Verdict

| Question | Verdict | Basis |
| --- | --- | --- |
| Q1 — Current Billing/Subscription/Commercial architecture? | A committed, org-scoped, versioned, provider-neutral D37 commercial foundation with 7 dedicated tables plus a 7-state subscription lifecycle and an append-only credit ledger. | `CURRENT FACT` — migrations, domain, repositories, service, APIs, live DB |
| Q2 — What already exists? | Versioned plan catalogue; subscription state machine (admin-driven); versioned commercial config; append-only credit ledger (7 entry types); common order model; server-measured storage metering; provider-neutral payment records; durable idempotency; customer billing reads; assisted/managed order flow; admin config/plan/subscription/credit/order APIs; Manual Processing coverage (direct + consultant-sponsored) at domain and API level. | `CURRENT FACT` |
| Q3 — What is partial? | Plan `features` authoring; Admin plan-version publishing (UI sends 3 fields only); storage metering enforcement; `api_access` / `managed_processing_available`; consultant-sponsored coverage persistence; consultant commercial UI; public pricing (static, hard-coded, not catalogue-driven); registration_mode (key supported, no row). | `CURRENT FACT` |
| Q4 — What is missing? | Any payment provider, checkout, webhook ingestion, invoice/receipt artefact, refund execution, trial, discount, add-on, proration, tax handling; any customer/consultant self-service subscription UI; any "Subscription" navigation; a plan features/entitlement editor; a reusable payment abstraction. | `IMPLEMENTATION GAP` |
| Q5 — Reusable infrastructure? | `billing_plans`, `billing_commercial_config`, `customer_subscriptions`, `billing_credit_ledger`, `billing_orders`, `billing_storage_usage`, `billing_payment_records`, `billing_idempotency_keys`, `BillingService`, the seven repositories, the org-scoped tenancy model, and the deny-by-default RLS posture. | `CURRENT FACT` |
| Q6 — What is Manual-Processing/Coverage-specific rather than general subscription? | `consultant_mp_allocations` (selected-client capacity ledger), `manual_processing_grants` (FIN-06 governance), `manual_processing_processors` (routing destination), `features.manual_processing`, `features.consultant_manual_processing`, and `services/manual_processing_routing.py`. | `CURRENT FACT` |
| Q7 — What should become the reusable Commercial module? | The plan catalogue, subscription lifecycle, entitlement resolver, credit ledger, order model, storage metering, payment-record model and idempotency — i.e. the D37 stack, reorganised behind one module boundary. | `ARCHITECTURAL RECOMMENDATION` |
| Q8 — What should remain outside it? | Manual Processing governance/routing, PE assignment, consultant-client relationship and client access profiles, staff RBAC/capability model, branding/white-label presentation, organisation/project master data. | `ARCHITECTURAL RECOMMENDATION` |
| Q9 — What must change per surface? | Public: catalogue-driven pricing + a real (initially virtual) checkout path. Consultant: a Subscription/Billing surface. Organisation: self-service plan change where PO permits. Platform Admin: plan `features`/activation editor, coverage UI, target-selectable credit operations, metered-usage UI with pagination/search/filter. | `IMPLEMENTATION GAP` + `ARCHITECTURAL RECOMMENDATION` |
| Q10 — Safest implementation sequence? | Author the missing data + make the existing surface reachable first (Phase 0), then Commercial Core, then Admin, then Public, then Consultant, then Organisation, then managed-client inheritance, then integration, then independent verification. | `ARCHITECTURAL RECOMMENDATION` |

**Overall maturity.** `CURRENT FACT` Commercial architecture: **partially implemented
and committed**. Commercial **data**: **effectively empty in the running local
environment**. Commercial **administration**: **implemented in code, unreachable in the
local environment**. Commercial **payment**: **absent by design**.

---

## 3. Commercial Terminology Map

The repository uses several overlapping vocabularies. This map records what the code
actually means.

| Term | Where it lives | Actual meaning in current code | Classification |
| --- | --- | --- | --- |
| **Plan** | `billing_plans` | A versioned catalogue entry keyed by `plan_code` + `version`; the current version is the row with `effective_to IS NULL`. Holds price, currency, interval, included credits, included storage, team limit, `processing_limits`, `features`, three legacy boolean entitlements, and a `billing_mode` scope. | `CURRENT FACT` |
| **Plan version** | `billing_plans.version` + `effective_from`/`effective_to` | Publishing a change inserts a **new** `(plan_code, version)` row and closes the previous one. Historical commercial records keep the terms under which they were created. | `CURRENT FACT` |
| **Price** | `billing_plans.price` + `currency` + `billing_interval` | A single price per plan version. **One interval only** (`month` is the default and the only seeded value). No annual/multi-interval price set, no price list, no tier pricing. | `CURRENT FACT` |
| **Subscription** | `customer_subscriptions` | The organisation's **current commercial relationship** — not an invoice ledger. Exactly one active relationship per organisation (partial unique index). | `CURRENT FACT` |
| **Lifecycle status** | `customer_subscriptions.lifecycle_status` | D37 vocabulary: `pending`, `trial`, `active`, `past_due`, `suspended`, `cancelled`, `expired`. Enforced by a CHECK constraint. | `CURRENT FACT` |
| **Legacy status** | `customer_subscriptions.status` | Pre-D37 vocabulary: `trialing`, `active`, `past_due`, `paused`, `cancelled`, `expired`. Retained, **not used by D37**. | `CURRENT FACT` (legacy) |
| **Billing mode** | `organizations.billing_mode`, `customer_subscriptions.billing_mode` | `CREDIT` or `STANDARD`. Customer-specific; assigned at org creation from the versioned default and never silently migrated. | `CURRENT FACT` |
| **Credit** | `billing_credit_ledger` | A **non-monetary processing unit**. Balance is derived as `SUM(credit_delta)`; the ledger row is authoritative and immutable. 7 entry types: `grant`, `consume`, `adjustment`, `rollover`, `emergency_allowance`, `refund`, `reversal`. | `CURRENT FACT` |
| **Emergency allowance** | `billing_commercial_config.credit_policy` | A configurable temporary overrun on a CREDIT-mode consume when the balance is insufficient. Default `allowance_pct: 10`. | `CURRENT FACT` |
| **STANDARD allowance** | `billing_commercial_config.standard_allowance` | A monthly **processing-unit** allowance used instead of credits when `billing_mode = STANDARD`. Measured from `usage_tracking`. | `CURRENT FACT` |
| **Order** | `billing_orders` | One common commercial order model for `automated` / `assisted` / `managed` / `storage` / `other`, with an immutable line-item JSON snapshot and a 12-state status vocabulary. | `CURRENT FACT` |
| **Assisted Processing** | `order_type = 'assisted'` | CarbonTally performs human-assisted processing; the price resolves from the versioned `assisted_pricing` config key, never hard-coded. Customer approves before work begins. | `CURRENT FACT` |
| **Managed Processing** | `order_type = 'managed'` | A "drop the scope, CarbonTally manages the workflow" request. Currently recorded as an order with `quoted: true` and `total_amount: 0`; quote and fulfilment are manual. | `CURRENT FACT` |
| **Commercial Coverage** | `/ops` → **Commercial Coverage** tab; `manual_processing_*` domains; `consultant_mp_allocations` | **Manual Processing only.** Purchased coverage + eligible clients + selected-client allocations + effective entitlement for one organisation. Not general subscription. | `CURRENT FACT` — see §11 |
| **Coverage mode** | `billing_plans.features.consultant_manual_processing.mode` | `SELECTED_CLIENTS` or `ALL_ELIGIBLE_CLIENTS`. | `CURRENT FACT` |
| **Allocation** | `consultant_mp_allocations` | One consumed unit of a firm's selected-client capacity for one client organisation. `active` consumes a unit; `released` returns it. History is never deleted. | `CURRENT FACT` (in code; table absent in live DB) |
| **Entitlement** | `BillingService.get_entitlement` / `domain/manual_processing.entitlement_from_plan` | Two different resolvers with the same word. The billing one answers "what is this org commercially entitled to right now". The manual-processing one answers "does this org's plan include Manual Processing". They are **not** unified. | `CURRENT FACT` |
| **Capability** | `staff_roles.permissions`, `organization_members`, `consultant_firm_members.can_*` | An RBAC flag that authorises an **action**. Distinct from an entitlement. | `CURRENT FACT` |
| **Usage** | `usage_tracking`; `billing_storage_usage` | Two separate usage mechanisms: a per-month processing-unit counter (`usage_tracking`) used only by STANDARD mode, and a storage snapshot table used by the storage entitlement view. | `CURRENT FACT` |
| **Payment record** | `billing_payment_records` | A **provider-neutral** intent/confirmation record. `provider` is free text. No provider SDK, no transaction execution, no credentials stored. | `CURRENT FACT` |
| **Idempotency key** | `billing_idempotency_keys` | A durable claim table: a repeated commercial mutation with the same key raises a conflict instead of double-executing. | `CURRENT FACT` |
| **Registration mode** | `billing_commercial_config` key `registration_mode` | `INVITATION_ONLY` or `OPEN_REGISTRATION`. A **provisioning gate only** — it never grants authorization, access or capability. | `CURRENT FACT` (key supported; **no row** in live DB) |
| **Consultant commercial mode** | `consultant_profiles.commercial_mode` (added by a later migration) | `standard` / `co_branded` / `white_label`. Resolved by `domain/consultant_entitlement.py`. This is **presentation + plane availability**, not billing. | `CURRENT FACT` |

`PO DECISION REQUIRED` The vocabulary is currently **split**: "billing mode" (commercial
CREDIT/STANDARD), "product mode" (presentation standard/co-branded/white-label), and
"coverage mode" (Manual Processing SELECTED_ALL) all use the word "mode". A future
Commercial module needs one coherent user-facing vocabulary.

---

## 4. Current Architecture

### 4.1 Layering (verified)

```
┌─ API ───────────────────────────────────────────────────────────────────────────┐
│ /api/v3/billing/*       customer, org-scoped      require_org_member()          │
│ /api/v3/commercial/*    admin                     require_staff                  │
│                                                   + require_internal_staff       │
│                                                   + can_manage_billing           │
│ /api/v3/admin/manual-processing/*   admin coverage control plane                │
│ /api/v3/.../manual-processing       customer/consultant coverage projections    │
├─ Service ───────────────────────────────────────────────────────────────────────┤
│ services/billing.py        BillingService  (944 lines) — authoritative rules     │
│ services/storage_metering.py                — best-effort non-blocking metering  │
│ services/manual_processing_routing.py       — MP entitlement + fallback routing  │
├─ Domain (pure) ─────────────────────────────────────────────────────────────────┤
│ domain/billing.py            plans, config, ledger, subscription, orders, …      │
│ domain/manual_processing.py  MP entitlement, coverage, routing decisions         │
│ domain/consultant_entitlement.py  product-mode presentation entitlements         │
├─ Persistence ───────────────────────────────────────────────────────────────────┤
│ data/billing.py — 7+ repositories over the billing tables and usage_tracking     │
├─ Database ──────────────────────────────────────────────────────────────────────┤
│ billing_plans · billing_commercial_config · billing_credit_ledger ·              │
│ billing_orders · billing_storage_usage · billing_payment_records ·               │
│ billing_idempotency_keys · customer_subscriptions · usage_tracking ·             │
│ organizations (billing_mode + legacy billing/trial/tax columns)                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

`CURRENT FACT` `backend/api/router.py:219` registers `v3_commercial_router`,
`:220` registers `v3_billing_router`, `:248` registers `manual_processing_admin_router`,
`:251` registers `v3_manual_processing_coverage_router`. All commercial routes are
live in the application.

### 4.2 Authoritative / derived status

| Element | Authority | Notes |
| --- | --- | --- |
| Plan catalogue | **Authoritative** (admin-configured, versioned) | `billing_plans` |
| Commercial rules | **Authoritative** (admin-configured, versioned) | `billing_commercial_config` |
| Subscription row | **Authoritative** (admin-written only) | `customer_subscriptions` |
| Credit balance | **Derived** | `SUM(credit_delta)` over the authoritative ledger |
| Credit ledger | **Authoritative + immutable** | append-only |
| Storage usage | **Derived snapshot** | measured server-side from `organization_files` |
| Order + line items | **Authoritative + immutable after completion** | corrections are new adjustments |
| Payment record | **Authoritative internal record of intent** | not a payment |
| Idempotency claim | **Authoritative** | blocks replay |
| Entitlement view | **Derived** at request time | no cached entitlement table |

`ARCHITECTURAL RECOMMENDATION` The derived-entitlement approach is correct and should be
preserved. A cached/materialised entitlement table would be a regression.

### 4.3 Naming and boundary observations

- `CURRENT FACT` `BillingService` mixes four concerns: entitlement resolution,
  subscription lifecycle, credit ledger operations, and the order lifecycle.
- `CURRENT FACT` Two files named `ManualProcessingCoverageTab.jsx` exist
  (`frontend/src/v3/ops/` and `frontend/src/v3/consultant/`) with different content and
  different audiences. This is not a defect, but it is a discoverability risk.
- `IMPLEMENTATION GAP` There is no single module/package boundary that a future
  "reusable Commercial module" could be lifted from. The concern is spread across
  `domain/`, `data/`, `services/` and `api/` by layer, which is the established project
  convention, not a billing-specific boundary.

---

## 5. Current Database / Schema Map

All live figures below were obtained by read-only `SELECT` against the local database
`ct_local_93d5cdd` at `127.0.0.1:5432` during this assessment. Credentials were sourced
from `backend/.env` and are not reproduced anywhere in this document.

| Structure | Purpose | Authority | Scope | RLS (live) | Live rows | Reusable? | Legacy? | Manual-Processing-specific? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `billing_plans` | Versioned plan catalogue | Authoritative | Global catalogue | Enabled, **0 policies** | **8** | **Yes** | No | No | Contains duplicate versions (§8) |
| `billing_commercial_config` | Versioned commercial rules | Authoritative | Global | Enabled, **0 policies** | **7** | **Yes** | No | Partly (`assisted_pricing`, `standard_allowance`) | 7 keys, all v1; **no `registration_mode`** |
| `billing_credit_ledger` | Append-only credit ledger | Authoritative, immutable | Org | Enabled, **0 policies** | **0** | **Yes** | No | No | Balance derived |
| `billing_orders` | Common order model | Authoritative | Org | Enabled, **0 policies** | **0** | **Yes** | No | Partly (`managed`/`assisted`) | Immutable line-item snapshot |
| `billing_storage_usage` | Storage metering snapshots | Derived, auditable | Org | Enabled, **0 policies** | **0** | **Yes** | No | No | Never browser-reported |
| `billing_payment_records` | Provider-neutral payment records | Internal record | Org | Enabled, **0 policies** | **0** | **Yes** | No | No | `provider` free text; no adapter |
| `billing_idempotency_keys` | Durable idempotency | Authoritative | Global key space | Enabled, **0 policies** | **0** | **Yes** | No | No | — |
| `customer_subscriptions` | The org's commercial relationship | Authoritative | **Org** | Enabled, **1 policy** (`SELECT` for `authenticated`) | **0** | **Yes** | Partly (Stripe columns, `plan`, `status`) | No | One active row per org; **no org currently has one** |
| `usage_tracking` | Per-month processing-unit counter | Authoritative | Org | Enabled, **1 policy** (`SELECT` for `authenticated`) | **0** | Partly | Partly | No | Used only by STANDARD mode |
| `consultant_billing` | Legacy consultant billing | — | Consultant | Enabled, **0 policies** | **0** | **No** | **Yes (deprecated)** | No | 0 rows, no application code references, Stripe-named columns |
| `consultant_mp_allocations` | Selected-client coverage ledger | Authoritative | Firm ↔ client org | — | **TABLE ABSENT** | Yes (once applied) | No | **Yes** | Migration authored, **not applied** |
| `manual_processing_processors` | Manual Processing routing destination | Authoritative config | Scope | — | **TABLE ABSENT** | Partly | No | **Yes** | Migration authored, **not applied** |
| `manual_processing_grants` | FIN-06 operational enablement | Authoritative | Scope | present | **0** | Partly | No | **Yes** | Governance, not commerce |
| `consultant_clients` | Firm ↔ organisation relationship | Authoritative | Relationship | present | **3** | **Yes** | No | Partly (eligibility anchor) | — |
| `organizations` | Tenant + billing mode + legacy billing columns | Authoritative | Tenant | Enabled, **2 policies** (`SELECT`, `UPDATE` for `authenticated`; table-level `UPDATE`/`INSERT`/`DELETE` **revoked**) | **25** | **Yes** | Partly (`subscription_*`, `trial_*`, `billing_*`, `tax_rate`) | No | `billing_mode`: CREDIT **23**, NULL **2** |
| `organization_files` | D32 document records | Authoritative | Org | present | present | **Yes** (metering source) | No | No | Source of truth for storage metering |
| `audit_trail` | Append-only audit | Authoritative | Global | present | present | **Yes** | No | No | All commercial mutations audited here |
| `staff_roles` | Staff capability catalogue | Authoritative | Global | Enabled, **0 policies** | **3** (`manager`, `operator`, `pe_manager`) | Partly | No | No | **No role carries `can_manage_billing`** |

### 5.1 Column-level facts worth recording

- `CURRENT FACT` `customer_subscriptions` base columns (from
  `supabase/migrations/00000000000000_init_schema.sql:1449`): `plan` (`NOT NULL`),
  `status`, `ai_extraction_limit`, `ai_extraction_used`, `batch_upload_limit`,
  `batch_upload_per_day`, `manual_extraction_pages_included`,
  `manual_extraction_pages_used`, `price_per_ai_extra`, `price_per_manual_page`,
  `currency`, `features`, **`stripe_subscription_id`**, **`stripe_customer_id`**,
  **`stripe_price_id`**, `billing_period_start`, `billing_period_end`, `cancelled_at`,
  `cancelled_by`.
- `CURRENT FACT` D37 added: `billing_mode`, `plan_code`, `plan_version`,
  `lifecycle_status`, `current_period_start`, `current_period_end`, `activated_at`,
  `idempotency_key`, plus `CHECK` constraints for `billing_mode` and `lifecycle_status`.
- `CURRENT FACT` The D37 `Subscription` domain object (`backend/domain/billing.py:189`)
  does **not** map `cancelled_at` / `cancelled_by`, although those columns exist.
- `CURRENT FACT` `billing_plans` outbound foreign keys: **none** — it is a catalogue.
- `CURRENT FACT` `customer_subscriptions.plan_code` has **no foreign key** to
  `billing_plans`; the reference is resolved in application code via
  `BillingPlansRepository.get_version` / `get_current_by_code`.
- `CURRENT FACT` `consultant_profiles.organization_id` — the linkage that makes a
  consultant firm's **own** organisation subscription the sponsorship source —
  **does not exist in the live database** (column count 0), although the migration that
  adds it exists in the repository.

### 5.2 RLS and grants (live)

| Table | RLS enabled | Policies | `anon` grants | `authenticated` grants |
| --- | --- | --- | --- | --- |
| `billing_plans` | yes | 0 | none | none |
| `billing_commercial_config` | yes | 0 | none | none |
| `billing_credit_ledger` | yes | 0 | none | none |
| `billing_orders` | yes | 0 | none | none |
| `billing_storage_usage` | yes | 0 | none | none |
| `billing_payment_records` | yes | 0 | none | none |
| `billing_idempotency_keys` | yes | 0 | none | none |
| `consultant_billing` | yes | 0 | none | **SELECT** only |
| `customer_subscriptions` | yes | 1 (`customer_subscriptions_tenant_select`, SELECT, `authenticated`) | none | **SELECT** only |
| `usage_tracking` | yes | 1 (`usage_tracking_tenant_select`, SELECT, `authenticated`) | none | **SELECT** only |
| `organizations` | yes | 2 (`organizations_org_select` SELECT; `organizations_org_update` UPDATE) | none | **SELECT** only (table-level `INSERT`/`UPDATE`/`DELETE` revoked, making the UPDATE policy inert) |
| `staff_roles` | yes | 0 | none | none |

`CURRENT FACT` `service_role` holds **49** grants across the `billing_%` tables. This is
intentional: the authoritative rules live in `BillingService` (FastAPI), not in RLS.

---

## 6. Current APIs

### 6.1 Customer — `/api/v3/billing` (`backend/api/v3_billing.py`)

Authorization: `require_org_member()` on every endpoint; the organisation is resolved
**server-side** from the authenticated context (`_resolve_org`, `v3_billing.py:295`).
The browser never supplies a trusted organisation id.

| Method | Path | Purpose | Mutating |
| --- | --- | --- | --- |
| GET | `/me` | Entitlement + credit balance + storage + STANDARD allowance | No |
| GET | `/me/credits` | Append-only credit ledger for the caller's org | No |
| GET | `/me/orders` | Orders for the caller's org | No |
| GET | `/me/orders/{order_id}` | One order (org-scoped fetch) | No |
| GET | `/me/payments` | Provider-neutral payment records (read-only) | No |
| POST | `/me/storage/refresh` | Re-measure storage server-side | Yes (metering snapshot only) |
| POST | `/orders/assisted` | Create an Assisted Processing estimate from the price book | Yes |
| POST | `/orders/{order_id}/approve` | Customer approval authorises the commercial job | Yes |
| POST | `/orders/{order_id}/cancel` | Cancel an order | Yes |
| POST | `/managed/orders` | Submit a Managed Processing request | Yes |

`CURRENT FACT` There is **no** customer endpoint to select a plan, start a checkout,
pay, upgrade, downgrade, cancel a subscription, or manage a payment method.

### 6.2 Platform Admin — `/api/v3/commercial` (`backend/api/v3_commercial.py`)

Authorization: `require_staff` dependency **plus** `_require_billing_admin`, which is
`require_internal_staff(context)` + `ensure_staff_permission(context, "can_manage_billing")`
(`v3_commercial.py:56`). Customers, consultants, PE staff, customer team members and
staff without the flag are denied.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/overview` | Current config + plan catalogue + default billing mode |
| GET | `/config` · `/config/{key}` | Versioned commercial rules (current + history) |
| PUT | `/config/{key}` | Publish a **new version** of a rule key (whitelisted keys) |
| GET | `/plans` · `/plans/{plan_code}` | Plan catalogue (current + full version history) |
| POST | `/plans` | Create a plan (version 1) |
| PUT | `/plans/{plan_code}` | Publish a **new plan version** (history preserved) |
| GET | `/ledger?organization_id=` | Append-only credit ledger + derived balance |
| GET | `/organizations?billing_mode=` | Organisations + per-customer billing mode |
| GET | `/subscriptions` · POST `/subscriptions` · POST `/subscriptions/{id}/status` | Subscription list / activate / change lifecycle status |
| GET | `/orders` · `/orders/{id}` · POST `/orders/{id}/complete` | Order administration |
| GET | `/storage?organization_id=` | Storage snapshots (all orgs, or one) |
| GET | `/payments?organization_id=` | Payment records |
| GET | `/entitlement/{organization_id}` | Per-org resolved entitlement |
| POST | `/credits/grant` · `/adjust` · `/reverse` · `/refund` · `/rollover` | Credit operations |

`CURRENT FACT` The whitelisted configurable keys are: `default_billing_mode`,
`credit_rules`, `structured_data_bands`, `storage`, `assisted_pricing`,
`credit_policy`, `standard_allowance`, `registration_mode`
(`v3_commercial.py:44`).

`CURRENT FACT` `PlanCreate` / `PlanUpdate` accept `name`, `description`, `price`,
`currency`, `billing_interval`, `included_credits`, `included_storage_bytes`,
`team_member_limit`, `processing_limits`, **`features`**, `billing_mode`,
`assisted_processing_available`, `managed_processing_available`, `api_access`,
`is_active`. The **API can therefore configure every plan field, including the
entitlement carrier**.

`IMPLEMENTATION GAP` The API has **no** endpoint to create a discount, a trial, an
add-on, an invoice, a refund execution, or to start a checkout session.

### 6.3 Manual Processing — `/api/v3/admin/manual-processing` and coverage projections

`CURRENT FACT` `backend/api/manual_processing_admin.py` exposes:
`GET /grants`, `GET /effective/{organization_id}`, `PUT /grants`,
`DELETE /grants/{scope_type}/{scope_id}`, `GET /state`, `GET /processors`,
`PUT /processors`, `DELETE /processors/{scope_type}/{scope_id}`,
`GET /coverage/{consultant_id}`, `POST /coverage/allocations`,
`DELETE /coverage/allocations/{allocation_id}`, `GET /clients/{organization_id}`,
`GET /organizations`.

`CURRENT FACT` `backend/api/v3_manual_processing_coverage.py` exposes:
`GET /organizations/{organization_id}/manual-processing` (`require_org_member()`),
`GET /consultants/me/manual-processing/coverage` (`require_consultant`),
`POST /consultants/me/manual-processing/allocations` (`require_consultant` +
`can_manage_clients`), `DELETE /consultants/me/manual-processing/allocations/{id}`
(same).

`CURRENT FACT` The consultant firm identity and the client organisation id are
**resolved server-side**; the component never sends a firm id
(`frontend/src/v3/consultant/ManualProcessingCoverageTab.jsx:5-9`).

### 6.4 Registration gate — `/api/v3/organizations` and `/api/v3/consultants`

`CURRENT FACT` `POST /api/v3/organizations` (`v3_organizations.py:107`) calls
`resolve_registration_mode(repos)` (`:142`) and returns a denial when the mode is
`INVITATION_ONLY` (`:143`). `POST /api/v3/consultants/me` applies the same gate
(`v3_consultants.py:359`).

---

## 7. Current RLS

`CURRENT FACT` The commercial security model has two distinct postures.

**Posture A — deny-by-default (browser has no access at all).**
`billing_plans`, `billing_commercial_config`, `billing_credit_ledger`, `billing_orders`,
`billing_storage_usage`, `billing_payment_records`, `billing_idempotency_keys` have RLS
enabled with **zero** policies and **no** `anon`/`authenticated` grants. Every read and
write for a customer reaches these tables only through the trusted FastAPI service path.

**Posture B — tenant read-only.**
`customer_subscriptions`, `usage_tracking` and `consultant_billing` carry a single
`SELECT` policy for `authenticated`; their `INSERT`/`UPDATE`/`DELETE` were dropped as
policies **and** revoked at table level by D37-0
(`20260824020000_...sql:57-65`). `organizations` additionally had table-level
`UPDATE`/`INSERT`/`DELETE` revoked (`:102`, `:106`), which closes the D36 P0 where a
customer could rewrite their own plan, limits, trial and tax fields through PostgREST.

`CURRENT FACT` All three revocations were independently confirmed in the live database:
`authenticated` holds `SELECT` only on `customer_subscriptions`, `usage_tracking`,
`consultant_billing` and `organizations`, and holds **nothing** on the seven D37 tables.

`CURRENT FACT` `consultant_mp_allocations` and `manual_processing_processors` are
authored with RLS enabled, **zero** policies, and `anon` + `authenticated` fully revoked
(service-role only) — but neither exists in the live database.

`IMPLEMENTATION GAP` The `organizations_org_update` policy still exists in
`pg_policies` while the underlying table-level privilege is revoked. It is inert, but it
is a misleading artefact for future readers and for any future grant change.

`ARCHITECTURAL RECOMMENDATION` Preserve both postures verbatim. Do not add
`authenticated` grants to the D37 tables to "make a UI work". If elevated access is
genuinely required, keep the explicit application-level authorization and document the
reason (AGENTS.md §67).

---

## 8. Plan / Pricing State

### 8.1 Live catalogue (verified)

| plan_code | version | price | currency | interval | credits | assisted | managed | api | current |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| starter | v1 | 0 | GBP | month | 10 | false | false | false | no (retired) |
| starter | v2 | 49 | **USD** | month | 100 | false | false | false | no (retired) |
| starter | **v3** | 49 | **USD** | month | 100 | false | false | false | **yes** |
| professional | **v1** | 149 | GBP | month | 500 | true | false | false | **yes** |
| business | v1 | 299 | GBP | month | 1500 | true | true | true | no (retired) |
| business | v2 | 399 | **USD** | month | 2000 | true | true | true | no (retired) |
| business | **v3** | 399 | **USD** | month | 2000 | true | true | true | **yes** |
| enterprise | **v1** | 0 | GBP | month | 0 | true | true | true | **yes** |

`CURRENT FACT` **Every** row carries `features = {"reports": true}`; `enterprise` adds
`"custom": true`. Therefore:

- `features.manual_processing` — **absent from every plan**
- `features.consultant` — **absent from every plan**
- `features.consultant_manual_processing` — **absent from every plan**

`CURRENT FACT` `included_storage_bytes` is populated (starter v3 = 20 GiB,
business v3 = 500 GiB), but no repository search found an enforcement path that
**refuses** anything on capacity; storage is metered and billed as `additional_bytes`.

### 8.2 Answers to the Plan/Pricing questions

| Question | Answer | Classification |
| --- | --- | --- |
| Where do plans exist? | Only in `billing_plans` and its API/UI. The public `/pricing` page carries a **separate hard-coded** list. | `CURRENT FACT` |
| Are plans persisted? | Yes, versioned. | `CURRENT FACT` |
| Are prices persisted? | Yes — `price` + `currency` per plan version. | `CURRENT FACT` |
| Does a billing interval exist? | A single `billing_interval` text column exists; every row is `month`. There is **no** multi-interval price set (no monthly + annual pair), no interval-level price record. | `CURRENT FACT` |
| Are plans versioned? | Yes — `UNIQUE (plan_code, version)` + `effective_from`/`effective_to`. | `CURRENT FACT` |
| Can plans be activated/deactivated? | `is_active` exists and is enforced when activating a subscription; the API can set it. The **UI cannot**. | `CURRENT FACT` + `IMPLEMENTATION GAP` (UI) |
| Do plans contain entitlements? | The **carrier** exists (`features` JSONB + 3 legacy boolean columns). The **values are unauthored**. | `CURRENT FACT` |
| Do plans contain limits? | `processing_limits` JSONB, `team_member_limit`, `included_credits`, `included_storage_bytes`. `processing_limits` is stored and projected but **not read by any enforcement path**. | `CURRENT FACT` |
| Who can modify plans? | Internal staff with `can_manage_billing` only. | `CURRENT FACT` |
| Does Platform Admin have a usable UI? | **Partial.** Create a plan: yes. Publish a new version: yes, but the UI sends only `name`, `price`, `included_credits` (`CommercialTab.jsx:170-194`). Edit `features`: **no UI**. Edit `billing_interval` / `is_active` / `team_member_limit` / `processing_limits` / the three booleans: **no UI**. Activate/deactivate: **no UI**. | `CURRENT FACT` |
| Can consultants view plans? | **No.** There is no consultant-facing plan-catalogue endpoint. | `CURRENT FACT` |
| Can public users view plans? | Only a static, hard-coded marketing page at `/pricing`. | `CURRENT FACT` |

### 8.3 Plan/pricing defects (independently confirmed)

1. `CURRENT FACT` **Duplicate plan versions from a non-idempotent seed.**
   `20260824030000_d37_master_commercial_billing.sql` computes
   `COALESCE(MAX(version),0)+1` and inserts for `starter`/`business` **without** an
   `ON CONFLICT` guard (`:244-273`). Applied twice, it produced byte-identical `v2` and
   `v3` rows. Live evidence: 8 rows for 4 logical plans.
2. `CURRENT FACT` **Mixed currency.** `starter`/`business` current versions are `USD`;
   `professional`/`enterprise` are `GBP`; `billing_commercial_config.assisted_pricing`
   is `USD`; `standard_allowance` and `storage` are `GBP`.
3. `CURRENT FACT` **Public display contradicts the catalogue.** `PricingPage.jsx:92-96`
   and `LandingPage.jsx:93-96` hard-code `£49 / £149 / £399` (and no currency at all for
   Enterprise). This both mismatches the catalogue and violates the proposed
   `CT-SUB-001` §3 rule that commercial values must not be hard-coded in frontend code.
4. `CURRENT FACT` **No plan carries an entitlement block**, so
   `BillingService.consultant_capability()` resolves `entitled: false` for every
   organisation, and consultant-sponsored Manual Processing coverage can never be true.
5. `IMPLEMENTATION GAP` **`api_access` and `managed_processing_available` are stored,
   seeded, projected and asserted in tests — but no enforcement path reads them.**

---

## 9. Subscription State

### 9.1 Trace: Customer → Plan → Subscription → Payment → Status → Entitlement → Usage

| Step | Classification | Evidence |
| --- | --- | --- |
| Customer (organisation) exists | **IMPLEMENTED** | `organizations` = 25 rows live |
| Plan exists | **IMPLEMENTED** | `billing_plans` = 8 live rows |
| Subscription created | **IMPLEMENTED (admin-only)** | `POST /api/v3/commercial/subscriptions` |
| Subscription visible to customer | **IMPLEMENTED** | `GET /api/v3/billing/me` → `subscription` |
| Subscription **exists for anyone** | **MISSING (data)** | `customer_subscriptions` = **0 rows** |
| Plan → subscription linkage | **IMPLEMENTED** | `plan_code` + `plan_version` (+ resolver) |
| Payment | **MISSING** | No provider, no checkout, no webhook |
| Subscription **status transitions** | **PARTIAL** | Only admin `activate` + `change status`; **no** scheduled expiry, renewal, dunning, grace period, or self-service cancellation |
| Entitlement | **PARTIAL** | `get_entitlement` computes correctly from a subscription; with 0 subscriptions it returns a null plan and zero included values |
| Usage | **PARTIAL** | `usage_tracking` for STANDARD only (0 rows); storage snapshots (0 rows); no document/credit consumption metering outside the charge path |
| Overall | **PARTIAL / effectively inert in the running environment** | — |

### 9.2 Subscription states

`CURRENT FACT` The states **do** exist as a vocabulary and a CHECK constraint:

```
pending | trial | active | past_due | suspended | cancelled | expired
```

`CURRENT FACT` A second, **legacy** vocabulary still exists on the same table and is
**not used by D37**:

```
trialing | active | past_due | paused | cancelled | expired
```

`CURRENT FACT` Only `trial`, `active`, `past_due`, `suspended` participate in the
"at most one active commercial relationship per organisation" partial unique index.
Setting `cancelled`/`expired` frees the organisation for a new relationship.

`IMPLEMENTATION GAP` `CURRENT FACT` **No code path sets `pending`, `past_due`,
`suspended`, `cancelled` or `expired` automatically.** The only writers are the admin
activate endpoint (which accepts any value in the vocabulary) and the admin status-change
endpoint (a manual human action). There is no scheduler, no payment failure handler, and
no period-end sweep, even though `idx_customer_subscriptions_period` exists to support one.

### 9.3 Upgrade / downgrade / cancellation

`CURRENT FACT` There are **no dedicated columns or semantics**. A plan change is expressed
as a new `plan_code`/`plan_version` on the same active row through
`SubscriptionsRepository.upsert_active`. Plan version history exists, but **no
subscription-change history** is retained per se — the audit trail is the only record.

`PO DECISION REQUIRED` Whether customers (and consultants) may self-serve a plan change
or cancellation, and what upgrade/downgrade/cancellation semantics (immediate vs
period-end, proration, refunds) apply.

---

## 10. Payment State

`IMPLEMENTATION GAP` **There is no payment implementation.**

| Question | Finding | Classification |
| --- | --- | --- |
| Payment tables | `billing_payment_records` (RLS on, 0 policies, 0 rows). The legacy `customer_subscriptions.stripe_*` and `consultant_billing.stripe_*` columns are unused. | `CURRENT FACT` |
| Payment transaction model | A single-row intent/confirmation record: `provider` (free text), `payment_method_type`, `provider_transaction_ref`, `amount`, `currency`, `status` (`pending`/`confirmed`/`failed`/`refunded`), `order_id`, `subscription_id`, `idempotency_key`, `recorded_at`, `confirmed_at`, `metadata`. | `CURRENT FACT` |
| Checkout | **Absent.** No checkout session concept anywhere. | `IMPLEMENTATION GAP` |
| Provider abstraction | **Not implemented.** No interface, no protocol, no base class, no provider registry. The migration header explicitly states "provider-neutral: no provider integration, no provider SDK, no checkout". | `IMPLEMENTATION GAP` |
| Provider-specific implementation | **Absent.** No Stripe/PayPal/Wise/Paddle/GoCardless/Braintree/Square SDK in any of `backend/`, `frontend/src/`, `admin/src/`, `supabase/`. The only `stripe` matches are legacy column names and comments. | `CURRENT FACT` |
| Webhook handling | **Absent.** No webhook route, no signature verification, no event ingestion. | `IMPLEMENTATION GAP` |
| Invoice generation | **Absent.** No invoice model, no invoice number, no PDF/receipt artefact. `billing_orders` is not an invoice. | `IMPLEMENTATION GAP` |
| Refunds | **No payment refund.** Credit refunds exist as a ledger entry type (`refund`) and an admin endpoint; that is a credit adjustment, not money movement. | `CURRENT FACT` |
| Failed payment handling | **Absent.** No dunning, no retry, no `past_due` transition driven by a payment failure. | `IMPLEMENTATION GAP` |
| Payment audit | Every commercial mutation, including `record_payment_intent`, is appended to `audit_trail` by `BillingService._audit`. | `CURRENT FACT` |
| Virtual/demo payment support | **Not implemented as a provider.** The nearest existing behaviour is that `approve_order` writes a `billing_payment_records` row with `provider='pending'` and `payment_method_type='to_be_selected'` (`services/billing.py:614-627`) — a placeholder, not a virtual provider. | `CURRENT FACT` |
| Does a provider-independent abstraction already exist? | **Partially, at the data level only.** `billing_payment_records` is deliberately shaped to receive records from any future provider. There is no code-level abstraction. | `CURRENT FACT` |

### 10.1 Minimum abstraction needed later (NOT implemented here)

`ARCHITECTURAL RECOMMENDATION` The smallest abstraction that fits the existing data model
without replacing it:

1. A `PaymentProvider` protocol with `create_checkout(...)` and
   `verify_webhook(raw_body, headers) -> PaymentEvent`.
2. A `VirtualProvider` implementation that immediately emits a `confirmed` event, so the
   whole lifecycle is exercisable in Demo Lab with no credentials.
3. Provider selection persisted in the **existing** `billing_commercial_config` as a new
   versioned key (e.g. `payment_provider`) — no new configuration table.
4. Provider events written to the **existing** `billing_payment_records` and de-duplicated
   through the **existing** `billing_idempotency_keys`.
5. A `CheckoutSession` concept — `UNKNOWN` whether this needs a table or can be a
   provider-side reference recorded on the payment record. This is a design choice, not
   an existing fact.

`PO DECISION REQUIRED` Which provider(s) to launch with, and whether a real provider is in
scope at all for the next implementation phase.

---

## 11. Commercial Coverage Analysis

### 11.1 What the subsystem actually is

`CURRENT FACT` "Commercial Coverage" in the current Platform Admin UI
(`/ops` → tab labelled **Commercial Coverage**, `OperationsPage.jsx:117-121`) is the
**Manual Processing commercial control plane**. It is *not* general subscription
management and it is *not* a separate billing system.

It answers exactly three questions, and the code keeps them separate:

1. **ENTITLEMENT** — does the organisation's **active subscription plan** include
   Manual Processing? (direct path), **or** does a consultant firm's **own organisation
   subscription plan** sponsor this client? (sponsored path).
2. **ELIGIBILITY** — for the sponsored path, is there an **active** `consultant_clients`
   relationship between that firm and this client organisation?
3. **ALLOCATION** — for `SELECTED_CLIENTS` mode only, is one of the firm's purchased
   capacity units used for this client (`consultant_mp_allocations`, state `active`)?

Two further, explicitly **distinct** concepts are kept out of the commercial answer:

- **GOVERNANCE** — FIN-06 `manual_processing_grants` (admin enable/disable, scope
  precedence `consultant_client` > `consultant_firm` > `organization`).
- **ROUTING** — `manual_processing_processors` (the configured destination Processing
  Entity).

`CURRENT FACT` The authoritative business rule is
`manual_processing_effective = subscription_entitled AND governance_enabled`
(`domain/manual_processing.py:318`). A stale governance grant can never bypass the
subscription requirement, and a subscription alone never activates routing.

### 11.2 Direct answers

| # | Question | Answer | Classification |
| --- | --- | --- | --- |
| 1 | Is Commercial Coverage general subscription? | **No.** It is a capability-specific commercial view layered on the general subscription model. | `CURRENT FACT` |
| 2 | Is it Manual Processing-specific? | **Yes.** Every field is Manual Processing. | `CURRENT FACT` |
| 3 | Is it an entitlement? | It **projects** an entitlement (direct OR sponsored). The entitlement itself lives on `billing_plans.features`. | `CURRENT FACT` |
| 4 | Is it an allocation/credit mechanism? | It is an **allocation** mechanism (selected-client capacity units), not a monetary credit. It never touches `billing_credit_ledger`. | `CURRENT FACT` |
| 5 | Is it a legacy commercial abstraction? | **No.** It is current, PO-approved (CT-PO-MP-SUB-003), and built deliberately on D37. | `CURRENT FACT` |
| 6 | Can it be reused by a future Commercial module? | Its **pattern** can (plan-feature-carried capacity + an allocation ledger). Its **table** cannot — it is Manual-Processing semantics. | `ARCHITECTURAL RECOMMENDATION` |
| 7 | Should it remain an internal operational concept? | **Yes.** Admin sees full coverage + allocations + effective entitlement; customer and consultant see caller-scoped projections only. | `CURRENT FACT` (implemented) |
| 8 | Should it be replaced or renamed? | **Do not rename the tab without a PO decision.** The label "Commercial Coverage" sits next to a tab named "Manual Processing" and a tab named "Commercial", which is genuinely confusing. | `UX RECOMMENDATION` + `PO DECISION REQUIRED` |
| 9 | What must NOT change (authoritative semantics)? | The FIN-06 scope vocabulary and precedence; `effective = entitled AND enabled`; "a relationship alone is never an entitlement"; "an allocation row is not an authorization grant"; "an entitled-but-not-configured org must not read as not-subscribed"; the separation of commercial entitlement from governance and from PE configuration. | `CURRENT FACT` (authoritative) |

### 11.3 Coverage reachability gap

`IMPLEMENTATION GAP` In the live local database:

- `consultant_mp_allocations` — **absent** (`to_regclass` returns NULL)
- `manual_processing_processors` — **absent**
- `consultant_profiles.organization_id` — **absent** (information_schema column count = 0)
- `manual_processing_grants` — present, **0 rows**
- `consultant_clients` — 3 rows
- `billing_plans.features.consultant_manual_processing` — **absent from every plan**

Consequence: `sponsored_entitlement_for()` cannot resolve a firm organisation, so the
sponsored path is **unreachable at runtime**. The customer- and consultant-facing coverage
UI will render its "no coverage" empty state for every identity.

`CURRENT FACT` This is a **migration-state/environment** gap, not a code defect: the
repository contains the migrations that create these structures.

`ARCHITECTURAL RECOMMENDATION` Do **not** resolve this by adding a data shortcut. Resolve
it by applying the authored migrations in a controlled environment and authoring the plan
feature block, as part of the Commercial Core phase.

---

## 12. Storage Metering Analysis

### 12.1 Mechanism

`CURRENT FACT` Source of truth: `public.organization_files` (D32), filtered by
`organization_id`, `is_active = TRUE`, `deleted_at IS NULL`, summing `size_bytes`
(`services/billing.py:668-675`).

| Question | Finding | Classification |
| --- | --- | --- |
| Source of truth | `organization_files` records | `CURRENT FACT` |
| Measurement mechanism | Server-side `SUM(size_bytes)`; **never** browser-reported | `CURRENT FACT` |
| Tables | `billing_storage_usage` (snapshots, append-only in practice) | `CURRENT FACT` |
| Aggregation | A full re-measure per snapshot; current usage = **latest** snapshot per org | `CURRENT FACT` |
| Organisation relationship | `organization_id` on the snapshot | `CURRENT FACT` |
| Consultant relationship | **None on the metering row.** A consultant-originated document is written under the **client organisation's** namespace, so it meters against the client org. The firm has no separate storage meter. | `CURRENT FACT` |
| Historical records | Yes — every measurement is a new row ordered by `measured_at DESC` | `CURRENT FACT` |
| Current usage | Latest snapshot; the entitlement view exposes `usage_bytes`, `included_bytes`, `additional_bytes = max(0, usage - included)` | `CURRENT FACT` |
| Limits | `billing_plans.included_storage_bytes` per plan version; live values 20 GiB (starter v3), 50 GiB (professional v1 = 53687091200), 500 GiB (business v3) | `CURRENT FACT` |
| Billing relationship | Storage is **metered and billable** as `additional_bytes`. It is **not** charged automatically by any code path. | `CURRENT FACT` |
| Enforcement | **None.** Uploads are never refused on capacity. The module documents this as deliberate. | `CURRENT FACT` |
| Recalculation | Triggered by an explicit customer action (`POST /me/storage/refresh`) and best-effort after a security-accepted direct upload (`services/storage_metering.py:39-83`) | `CURRENT FACT` |
| Auditability | The snapshot row is the record; the upload audit entry records the metering outcome (`recorded`, `usage_bytes`, `included_bytes`, `additional_bytes`, `source`) | `CURRENT FACT` |
| Failure behaviour | Deliberately **fail-open**: a metering failure never blocks an upload; the outcome reports `recorded: false` with a reason | `CURRENT FACT` |

`CURRENT FACT` The client-namespace decision is explicit and ratified
(`services/storage_metering.py:131-136`): "Storage is metered per organisation, including
consultant-originated documents, which are stored in the client organisation's namespace."

`IMPLEMENTATION GAP` There is **no** per-consultant-firm or per-managed-client capacity
model. `capacity_integration_status()` reports this deliberately as
`not_integrated.consultant_managed_client_capacity`.

### 12.2 Current UI assessment (independent)

`CURRENT FACT` The only current storage UI is:
- a card on the customer Billing page showing used / included with a **"Re-measure"**
  button (`BillingPage.jsx:139-146`), and
- `GET /api/v3/commercial/storage` consumed by the admin Commercial tab.

| Capability | Supported today? | Classification |
| --- | --- | --- |
| Pagination | **No** | `IMPLEMENTATION GAP` |
| Search | **No** | `IMPLEMENTATION GAP` |
| Filtering | Only a single org id query parameter on the API; **no UI** | `IMPLEMENTATION GAP` |
| Sorting | **No** | `IMPLEMENTATION GAP` |
| Organisation selection | **No UI** (API accepts `?organization_id=`) | `IMPLEMENTATION GAP` |
| Consultant selection | **No** — not modelled at all | `IMPLEMENTATION GAP` |
| Date filtering | **No** | `IMPLEMENTATION GAP` |
| Current vs historical usage | Current only in the UI; the repository can list history (`list_for_org`) but **no UI consumes it** | `IMPLEMENTATION GAP` |
| Drill-down | **No** | `IMPLEMENTATION GAP` |
| Empty states | Customer card shows `0 B used`; the admin tab has no meaningful empty state | `IMPLEMENTATION GAP` |
| Loading states | Customer card: yes (button label swaps to "Measuring…"). Admin: generic page loader | `CURRENT FACT` (partial) |
| Errors | Customer: inline error banner. Admin: generic error string | `CURRENT FACT` (partial) |

`CURRENT FACT` `GET /api/v3/commercial/storage` issues **one `latest_for_org` query per
organisation** in a loop over `list_all()` (`v3_commercial.py:649-655`). With the full
investor demo population (≈1,185 identities / 50+ direct organisations plus 911
consultant-client organisations) this is an N+1 pattern that will not scale.

`UX RECOMMENDATION` A metered-usage surface needs server-side aggregation, pagination,
and org/consultant/period filtering before it is usable at demo or production scale.

---

## 13. Credit Operations Analysis

### 13.1 What a credit is

`CURRENT FACT` A credit is a **non-monetary processing unit**. It is **not** currency and
it is **not** a document. Consumption is driven by document **complexity class**
(`simple` 1, `standard` 2, `complex` 4, `exceptional` quoted) or by **structured-data
bands** (rows → units).

`CURRENT FACT` Ownership is **org-scoped**: `billing_credit_ledger.organization_id`. There
is no user-scoped or consultant-scoped credit balance. A consultant firm's credits live on
the firm's **own organisation**.

### 13.2 Ledger structure and operations

| Question | Finding | Classification |
| --- | --- | --- |
| Ledger structure | Single append-only table with `credit_delta` (CHECK `<> 0`), `entry_type`, `source`, `reason`, `plan_code`, `plan_version`, `subscription_id`, `order_id`, `external_reference`, `correlation_id`, `created_by` | `CURRENT FACT` |
| Balance | **Derived** — `SUM(credit_delta)`; no mutable balance column | `CURRENT FACT` |
| Idempotency | Two layers: unique partial index `(organization_id, external_reference)` where non-null, **and** the `billing_idempotency_keys` claim table used by every service method | `CURRENT FACT` |
| Audit trail | Each operation calls `_audit(...)` writing `credit.grant` / `credit.consume` / `credit.adjustment` / `credit.reversal` / `credit.refund` / `credit.rollover` into `audit_trail` | `CURRENT FACT` |
| **Grant** | `POST /credits/grant` — positive-only, source default `plan_included` | `CURRENT FACT` |
| **Consume** | `BillingService.consume_credits` — used by `charge_processing`; if the balance is insufficient and the policy permits, writes an `emergency_allowance` grant (default 10%) **then** the consume | `CURRENT FACT` |
| **Reverse** | `POST /credits/reverse` — locates the original by `external_reference` and writes an opposite-delta `reversal` row; never rewrites history | `CURRENT FACT` |
| **Refund** | `POST /credits/refund` — a positive `refund` row; a **credit** refund, not money | `CURRENT FACT` |
| **Expiration** | **Not implemented.** `credit_policy.rollover.expiry_months` exists in config but is `NULL` and no code reads it. | `IMPLEMENTATION GAP` |
| **Rollover** | `POST /credits/rollover` — caller supplies `eligible_credits`; the service **does not compute** eligibility from the prior period | `IMPLEMENTATION GAP` |
| **Adjustment** | `POST /credits/adjust` — signed `delta`, non-zero | `CURRENT FACT` |
| Target selection — organisation | **Yes.** `organization_id` is an explicit field on every credit request. | `CURRENT FACT` |
| Target selection — consultant firm | **No.** There is no firm-scoped credit target anywhere. | `IMPLEMENTATION GAP` |
| Authorisation | `require_staff` + `require_internal_staff` + `can_manage_billing`, on every credit endpoint | `CURRENT FACT` |

### 13.3 Target selection — UI gap (explicitly recorded, NOT fixed)

`CURRENT FACT` The admin credit-operations panel in
`frontend/src/v3/ops/CommercialTab.jsx:588-624` presents a **free-text "Organisation id"**
input box. There is:
- no organisation search or picker,
- no organisation name display while typing,
- no validation that the id exists before submitting,
- no consultant-firm target at all,
- no recent/history affordance.

`UX RECOMMENDATION` This is the single clearest operational usability gap in the
commercial control plane: an operator must already know a raw UUID to grant or adjust
credits. A searchable, name-rendering target selector (organisation, and later firm) is
required before this surface is operationally usable at investor-demo scale. Per the task
instruction this is recorded as a gap and **not fixed**.

### 13.4 Consumption is largely unexercised

`CURRENT FACT` The only production caller of `charge_processing` is
`customer_review_item` in `backend/api/v3_processing_workflow.py`, at customer approval,
charging `batch.organization_id` with idempotency key `charge:item:{item_id}`.

`CURRENT FACT` With `customer_subscriptions` = 0 rows, that call raises
`EntitlementUnavailableError` (403) for every organisation. Credit consumption therefore
**cannot occur** in the current local environment.

---

## 14. Public / Signup State

### 14.1 What actually exists

| Element | State | Classification |
| --- | --- | --- |
| Public account creation | **EXISTS.** `/signup` → `frontend/src/SelfServiceSignup.jsx` performs a real `supabase.auth.signUp` with `email`, `password`, `full_name`, `company_name` and `onboarding: true`. | `CURRENT FACT` |
| Beta-code signup | **EXISTS.** `/beta/signup` → `BetaSignup.jsx` (optional administrative mechanism). | `CURRENT FACT` |
| Organisation creation | **EXISTS.** `POST /api/v3/organizations` (`v3_organizations.py:107`), gated by the registration mode. | `CURRENT FACT` |
| Onboarding route | **EXISTS.** `/onboarding` → `OnboardingPage.jsx`. The legacy `OnboardingWizard` overlay was retired (P8-FIN-01a). | `CURRENT FACT` |
| Consultant signup | **EXISTS (API).** `POST /api/v3/consultants/me` (`v3_consultants.py`), same registration gate. | `CURRENT FACT` |
| Plan selection | **MISSING.** No step anywhere in the signup or onboarding flow offers a plan. | `IMPLEMENTATION GAP` |
| Checkout | **MISSING.** | `IMPLEMENTATION GAP` |
| Payment | **MISSING.** | `IMPLEMENTATION GAP` |
| Subscription activation | **MISSING from the public path.** Activation exists only as an admin API call. | `IMPLEMENTATION GAP` |
| Entitlement provisioning | **MISSING.** A newly created organisation has **no** subscription, so `get_entitlement` returns a null plan. | `IMPLEMENTATION GAP` |
| Public pricing page | **EXISTS but static.** `/pricing` → `PricingPage.jsx` renders four hard-coded plans (`£49 / £149 / £399` / Custom), hard-coded credit bands, and the statement "No online checkout — CarbonTally is preparing for commercial launch and access is by arrangement." | `CURRENT FACT` |
| Public marketing pricing preview | **EXISTS, also hard-coded.** `LandingPage.jsx:92-97`. | `CURRENT FACT` |
| Public FAQ / Services copy | States online checkout is "Arranged directly with the CarbonTally team" and that access is by arrangement. | `CURRENT FACT` |

### 14.2 Exact traced path (current)

```
Visitor
  → /signup  (SelfServiceSignup.jsx)
      → supabase.auth.signUp(email, password, {full_name, company_name})
          → (email confirmation) → /auth/callback
              → goToWorkspace() → /api/v3/me/context
                  → no organisation  → /onboarding
                      → POST /api/v3/organizations
                          → resolve_registration_mode(repos)
                              → no registration_mode row
                                  → DEFAULT_REGISTRATION_MODE = "OPEN_REGISTRATION"
                                      → organisation CREATED, caller becomes OWNER
                                          → /home  (V3Layout customer shell)
                                              → Billing shows "No active subscription"
```

`CURRENT FACT` There is **no** plan, price, checkout, payment or subscription step
anywhere in this path.

### 14.3 Contradiction (independently confirmed)

`CURRENT FACT` `registration_mode` has **no row** in `billing_commercial_config`
(live config contains 7 keys; `registration_mode` is not among them). The documented
resolver default is `OPEN_REGISTRATION` (`domain/billing.py:34`), so **open self-service
account and organisation creation is currently permitted**.

`CURRENT FACT` The public website simultaneously states: "There is no open signup at
this stage" (`public/ContactPage.jsx:43`) and "Public sign-up, subscriptions and online
payment are not currently offered" (`TermsPage.jsx:33-35`).

`PO DECISION REQUIRED` Which is correct: (a) publish `registration_mode =
INVITATION_ONLY` and align the signup UI, or (b) accept open registration and correct the
public copy.

---

## 15. Consultant State

| Question | Finding | Classification |
| --- | --- | --- |
| Does a consultant subscription exist? | **Not as a distinct concept.** A consultant firm is commercially represented by its **own organisation's** subscription (`consultant_profiles.organization_id` → that org's `customer_subscriptions`). No consultant-firm subscription table exists. | `CURRENT FACT` |
| Does a consultant plan exist? | Plans are global; a firm "buys" a plan through its own organisation. No consultant-specific plan catalogue. | `CURRENT FACT` |
| Does consultant billing exist? | **No.** `consultant_billing` is legacy, 0 rows, no code references. | `CURRENT FACT` |
| Does the consultant see subscription state? | **No.** No consultant-facing subscription endpoint or UI. | `IMPLEMENTATION GAP` |
| Does the consultant see available plans? | **No.** No consultant-facing plan-catalogue endpoint. | `IMPLEMENTATION GAP` |
| Can the consultant subscribe? | **No.** Activation is admin-only. | `IMPLEMENTATION GAP` |
| Can the consultant pay? | **No.** No payment path for anyone. | `IMPLEMENTATION GAP` |
| Can the consultant change plan? | **No.** | `IMPLEMENTATION GAP` |
| Can the consultant cancel? | **No.** | `IMPLEMENTATION GAP` |
| Does subscription affect capabilities? | **Server-side yes, in code.** `BillingService.consultant_capability()` projects `features.consultant` → `{entitled, client_capacity, team_member_limit, white_label, workspace}`. **In data: no** — no plan carries the block, so `entitled` is `false` everywhere. | `CURRENT FACT` |
| Does subscription affect client access? | **No, by ratified design.** The resolver comments state explicitly that client access stays on the active `consultant_clients` grant and action permissions stay on the capability model. | `CURRENT FACT` |
| Does subscription affect branding? | **No.** Branding/white-label is governed by `consultant_profiles.commercial_mode` and the D21 flags through `domain/consultant_entitlement.py`, which is presentation-only and separate from billing. | `CURRENT FACT` |
| Does subscription affect White-Label? | The **plan** advertises `features.consultant.white_label`, but the **enforcement** is `domain/consultant_entitlement.resolve_entitlements(mode)`. Two sources exist; only the mode-based one is enforced. | `CURRENT FACT` — potential dual source of truth |
| Does subscription affect client limits? | `capability.client_capacity` is projected but **no enforcement path consumes it**. | `IMPLEMENTATION GAP` |
| Does subscription affect team limits? | `billing_plans.team_member_limit` is projected into the entitlement payload; **no enforcement path consumes it**. | `IMPLEMENTATION GAP` |
| Does subscription affect Manual Processing? | **Yes, and this is the one place it is genuinely enforced.** A consultant firm's plan carrying `features.consultant_manual_processing` grants sponsored coverage to eligible clients. The consultant's in-app "Manual Processing" tab reads the firm's own coverage. | `CURRENT FACT` |

`CURRENT FACT` Current consultant UI: `frontend/src/v3/consultant/ConsultantPage.jsx`
tabs are Dashboard / Clients / Team / **Manual Processing** / Branding. There is **no**
Subscription or Billing tab. `ConsultantTeamTab.jsx:32-34` states explicitly that
commercial entitlement (plan/seats/mode/white-label) is deliberately excluded because it
is CarbonTally-Admin-controlled (PO-5).

`CURRENT FACT` The consultant client operating plane deliberately excludes the customer
`/billing` route (`V3Layout.jsx:135-140`, PD-6) because "CarbonTally bills consultant
FIRMS, so a managed client's billing is not the consultant's billing". This is a ratified
boundary and must not be reopened.

`CURRENT FACT` `frontend/src/v3/consultant/ManualProcessingCoverageTab.jsx` is
**untracked** in Git — it is part of the concurrent CT-MP-SUB-004 work, not pre-existing.

---

## 16. Organisation State

### 16.1 Direct CarbonTally organisation

`CURRENT FACT` A direct organisation's commercial model is:
`organizations` (tenant, `billing_mode`) → `customer_subscriptions` (its own active
relationship) → `billing_plans` (plan_code + plan_version) → entitlement via
`BillingService.get_entitlement` → enforcement at `charge_processing` and the manual
processing routing gate.

`CURRENT FACT` In the live environment, **no** direct organisation has a subscription.

`IMPLEMENTATION GAP` The organisation **profile** UI shows `billing_mode` read-only
(`frontend/src/v3/admin/ProfileTab.jsx:143`), and the customer Billing page shows mode and
plan read-only. There is no organisation-facing subscription management.

### 16.2 Consultant-managed organisation

**Does a consultant-managed Organisation become a separate CarbonTally commercial
customer?**

`CURRENT FACT` **No — it is not a separate paying customer, and the current
implementation enforces that. The enforcing mechanisms are:**

1. **Billing is org-scoped and the firm is the payer.** A consultant firm's commercial
   relationship is its **own** organisation's subscription, reached through
   `consultant_profiles.organization_id`. The managed client does not need one.
2. **Manual Processing sponsored coverage is derived from the firm's plan, not the
   client's.** `ManualProcessingRouter.sponsored_entitlement_for()` resolves
   `grant.consultant_id → firm_organization_id → that org's active subscription → plan →
   features.consultant_manual_processing`
   (`services/manual_processing_routing.py:114-159`).
3. **The customer UI states the boundary in words.** The client-facing Manual Processing
   page renders: "Manual Processing for a consultant-managed client is arranged through
   your FIRM's commercial coverage with CarbonTally, not the client's own subscription"
   (`frontend/src/v3/customer/ManualProcessingPage.jsx:106-112`).
4. **The consultant client plane hides `/billing`** (PD-6, `V3Layout.jsx:135-140`).
5. **The client portal carries no billing control at all** —
   `frontend/src/v3/portal/ClientPortal.jsx:11-13` records that billing, branding and user
   management deliberately do not exist client-side (PO-9/PO-2/PO-3A/PO-5).
6. **A relationship is never an entitlement.** `sponsored_entitlement()` fails closed
   unless the firm's plan actually carries the coverage block.

**Is the current implementation complete?**

`IMPLEMENTATION GAP` The **model** is enforced, but the **runtime** is incomplete in the
local environment: the firm→subscription link column
(`consultant_profiles.organization_id`) does not exist, `consultant_mp_allocations` does
not exist, and no plan carries the coverage feature. So the boundary is correctly
*expressed* but cannot currently be *demonstrated*.

`IMPLEMENTATION GAP` There is **no explicit "managed-by-consultant ⇒ no own
subscription" constraint**. If a managed client organisation were also given its own
subscription, nothing prevents it — the two paths combine (direct **OR** sponsored) by
design, so the client would simply have two valid paths to one service. This is
documented as intended ("Both commercial paths support one operational Manual Processing
service, not two"), so it is arguably correct — but it means the "no duplicate client
subscription" requirement in the task brief is an **intention, not an enforced invariant**.

`PO DECISION REQUIRED` Whether a consultant-managed organisation must be **prevented**
from holding its own subscription, or whether dual coverage is acceptable by design.

---

## 17. Platform Admin State

### 17.1 Reachability — the blocking finding

`CURRENT FACT` **The Admin commercial surface is unreachable by every identity in the
local environment.**

Live evidence:
- `staff_roles` contains exactly three rows: `manager`, `operator`, `pe_manager`.
- **None** of them has `can_manage_billing`.
- The count of roles with `can_manage_billing` is **0**.
- No role named `admin` or `system_admin` exists in this database, yet the D37-0 migration
  grants the flag with `WHERE name = 'admin'`
  (`20260824020000_...sql:300-304`) and a later migration targets `system_admin`
  (`20260828010000_v3m8_system_admin_role_model.sql:24-28`).

`CURRENT FACT` Consequence, in the running application:
- `/api/v3/commercial/*` refuses every caller (`ensure_staff_permission` denies).
- The `/ops` → **Commercial** tab is never rendered (`OperationsPage.jsx:135`).
- No operator can configure a plan, change a config version, activate a subscription,
  grant credits, or view the payment/storage/order surfaces.

`CURRENT FACT` The root cause is already documented externally: the demo-lab provisioner
`tools/demo_lab/provision.py::ensure_staff_roles` performs a **wholesale replacement** of
`staff_roles.permissions` for a fixed role map that omits `can_manage_billing`, `can_qc`,
`can_view_all` and `can_manage_backups`, which erases whatever the migrations granted.
This is **PR-03 / PR-01/02** in `CT-PRODUCT-REALITY-AUDIT-01` and is still current.

`IMPLEMENTATION GAP` This must be resolved before any commercial administration can be
demonstrated. It is a capability-data / provisioning defect, not a missing gate.

`PO DECISION REQUIRED` **Which role owns commercial configuration** — the release
`system_admin` model, or the demo `admin` role — and therefore which role the provisioner
must stop stripping.

### 17.2 Page / tab inventory

| Surface | Route / host | Audience | Classification |
| --- | --- | --- | --- |
| **Commercial** | `/ops` tab | Staff with `can_manage_billing` | **B. Admin configuration** (currently unreachable) |
| **Commercial Coverage** | `/ops` tab | Staff with `can_manage_organizations` | **A. User-facing operational product** (for internal ops) + **B** |
| **Manual Processing** | `/ops` tab | Staff with `can_manage_organizations` | **A. Operational product** |
| **Billing** | `/billing` | Customer (org member) | **A. User-facing operational product** |
| **Manual processing** | `/manual-processing` | Customer | **A. User-facing operational product** |
| **Manual Processing** (firm coverage) | `/consultant?view=coverage` | Consultant | **A** (new, untracked) |
| **Pricing** | `/pricing` | Public | **A. Marketing**, static/unmanaged |
| **Services / FAQ** | `/services`, `/faq` | Public | **A. Marketing**, static |
| **Legacy admin CRA** | `admin/` app | Legacy staff | **D. Legacy/duplicate** — carries no commercial surface (only a `subscription_tier` badge in `admin/src/pages/admin/Customers.js:263`) |
| Dedicated **Subscription** navigation | — | — | **E. Missing functionality** |
| Plan `features` / activation editor | — | — | **E. Missing functionality** |
| Payment / invoice / trial / discount / add-on surfaces | — | — | **E. Missing functionality** |
| Consultant subscription surface | — | — | **E. Missing functionality** |

### 17.3 UX / information-architecture assessment (independent)

`CURRENT FACT` All commercial administration lives inside one tab named **"Commercial"**
nested under **"Internal Operations"**, alongside sixteen other tabs
(Dashboard, Operational health, Data entry, Review, Assignments, CarbonTally QC, QC,
Staff, Roles, Entities, SLA, Messaging, PE messages, Audit, Settings, Issues, Backups,
plus Commercial Coverage and Manual Processing).

`UX RECOMMENDATION` Findings, ranked:

1. **Target selection is raw UUID entry.** The credit-operations panel
   (`CommercialTab.jsx:593-603`) and the subscription activation form
   (`:536-553`) require a pasted organisation UUID. There is no picker, no name preview,
   no existence validation. This is the most severe usability defect and it exposes a raw
   developer identifier as the primary input, contrary to AGENTS.md §34/§75.
2. **The Commercial tab renders raw JSON.** Versioned commercial rules are edited in
   `<textarea className="commercial-json">` boxes (`:301-306`). An operator must author
   JSONB by hand for credit rules, structured-data bands, storage, assisted pricing,
   credit policy and standard allowance.
3. **Plan version publishing is silently partial.** The UI sends only `name`, `price` and
   `included_credits` on publish (`:170-194`). An operator cannot edit features,
   `billing_interval`, `is_active`, `team_member_limit`, `processing_limits` or the three
   boolean entitlements from the UI, even though the API accepts them. The consequence is
   an operator can believe they have "updated the plan" while the entitlement carrier is
   untouched.
4. **No pagination, search, filtering or sorting anywhere in the Commercial tab.**
   Subscribers, orders, storage and payments are rendered as unconditional full tables.
   The storage endpoint is also an N+1 query per organisation (§12.2).
5. **Terminology collision.** Three tabs — "Commercial", "Commercial Coverage" and
   "Manual Processing" — plus a customer page named "Billing" and a consultant tab named
   "Manual Processing" all describe parts of one commercial story. "Commercial Coverage"
   is Manual Processing–only and does not read that way.
6. **Audit history is not surfaced in context.** Every commercial change is audited into
   `audit_trail`, but the Commercial tab does not show before/after version or reason
   inline; an operator must leave for the separate Audit tab.
7. **Confirmation.** Mutating buttons act immediately. The only confirmation-like pattern
   found in the coverage surfaces is the release-allocation confirmation.
8. **Empty / loading / error states.** Loading: generic spinner. Error: a raw
   `e.message` string. Empty: mostly absent ("No orders yet"-style copy exists only on the
   customer page).
9. **Mixed currencies are displayed without warning.** The plan table renders
   `USD` and `GBP` rows side by side with no reconciliation or flag.

`UX RECOMMENDATION` None of the above requires reopening a frozen UX decision. D21 tokens
are already in use (`v3-admin-card`, `v3-table`, `v3-btn`, `workspace-pane`).

---

## 18. Entitlement Architecture

### 18.1 The two mappings requested

**Mapping A — plan-derived entitlement**

```
Plan                              billing_plans (plan_code + version)
 ↓
Subscription                      customer_subscriptions (one active per org)
 ↓
Commercial entitlement            BillingService.get_entitlement(org)
                                     → billing_mode, plan, credits, storage,
                                       standard, features, team_member_limit,
                                       processing_limits, capabilities.consultant
 ↓
Feature                           billing_plans.features (JSONB) — the canonical carrier
 ↓
Usage / limit                     billing_credit_ledger (derived balance),
                                  usage_tracking (STANDARD month),
                                  billing_storage_usage (latest snapshot)
```

**Mapping B — consultant commercial + relationship + access + entitlement**

```
Consultant capability             consultant_firm_members.can_* (RBAC, action-level)
+
Consultant-client relationship    consultant_clients (status active) — ELIGIBILITY anchor
+
Client access profile             per-client access mode (read-only/collaborative/managed)
+
Commercial entitlement            billing_plans.features.consultant
                                  + billing_plans.features.consultant_manual_processing
                                  (resolved from the FIRM's OWN org subscription)
+
Presentation entitlement          consultant_profiles.commercial_mode
                                  → domain/consultant_entitlement.resolve_entitlements()
```

`CURRENT FACT` The code states the intended non-collapse explicitly
(`domain/consultant_entitlement.py:6-20`): "the five boundaries — PRODUCT MODE,
COMMERCIAL ENTITLEMENT, CONSULTANT RBAC, CLIENT ACCESS PROFILE, CARBONTALLY AUTHORITY —
must not collapse".

### 18.2 Where the implementation does and does not mix concerns

| Boundary | Verdict | Evidence |
| --- | --- | --- |
| Subscription entitlement vs RBAC capability | **Correctly separated.** `capability` is a `staff_roles`/membership flag; `entitlement` is plan-derived. | `CURRENT FACT` |
| Subscription entitlement vs relationship | **Correctly separated.** A `consultant_clients` row never grants entitlement (fail-closed). | `CURRENT FACT` |
| Subscription entitlement vs client access profile | **Correctly separated**, though the access profile is implemented in the parallel consultant workstream, so its current file set is **not stable** during this assessment. | `CURRENT FACT` + `UNKNOWN` (concurrent change) |
| Service entitlement vs Manual Processing eligibility | **Correctly separated.** `entitlement = eligibility only`; activation needs governance too. | `CURRENT FACT` |
| Manual Processing coverage vs FIN-06 governance vs PE config | **Correctly separated and documented** as three concepts (`ManualProcessingCoverageTab.jsx:9-16`). | `CURRENT FACT` |
| Credits vs storage vs allowances | **Correctly separated** — three distinct mechanisms with distinct tables. | `CURRENT FACT` |
| **Data entitlement vs presentation entitlement** | **MIXED — two sources of truth.** A plan can advertise `features.consultant.white_label`, while actual white-label enforcement reads `consultant_profiles.commercial_mode`. | `IMPLEMENTATION GAP` |
| **Entitlement resolution — two resolvers, one word** | **MIXED.** `BillingService.get_entitlement` and `domain/manual_processing.entitlement_from_plan` independently re-implement plan→subscription→plan lookup. | `IMPLEMENTATION GAP` |
| **Plan feature values are unauthored** | The carrier exists but carries nothing, so every entitlement except the legacy boolean fallback resolves to `false`. | `IMPLEMENTATION GAP` |
| **`api_access` / `managed_processing_available`** | Stored, seeded, projected, tested — **never enforced**. | `IMPLEMENTATION GAP` |

### 18.3 Enforcement points (where entitlement is actually enforced today)

| Enforcement point | Mechanism | Layer | Verdict |
| --- | --- | --- | --- |
| Chargeable processing approval | `BillingService.charge_processing` → `EntitlementUnavailableError` (403) when no active subscription; `InsufficientCreditsError` (402) when the balance and emergency allowance are exhausted | **Domain/service** | `CURRENT FACT` |
| Consultant submission to CarbonTally QC | `BillingService.ensure_processing_entitlement` (read-only, fails closed) | **Domain/service** | `CURRENT FACT` |
| Document upload authorisation | `backend/api/upload_gate.py` — authentication, org isolation, staff/PE scope, viewer read-only, consultant active grant + `can_upload_documents` | **API** | `CURRENT FACT` |
| Manual Processing routing | `ManualProcessingRouter.entitlement_for()` (direct OR sponsored) → governance → processor | **Domain/service** | `CURRENT FACT` |
| Consultant capability projection | `BillingService.consultant_capability()` | **Service** (projection only — **not enforced**) | `CURRENT FACT` |
| Admin commercial API | `require_internal_staff` + `can_manage_billing` | **API** | `CURRENT FACT` |
| Commercial tables directly from the browser | RLS deny-by-default (0 policies, no grants) | **Database/RLS** | `CURRENT FACT` |
| Tenant reads of own subscription/usage | RLS SELECT policy | **Database/RLS** | `CURRENT FACT` |

### 18.4 Features controlled ONLY by UI

`CURRENT FACT` The following are decided by UI visibility **only** on the client:

| Element | UI gate | Server enforcement |
| --- | --- | --- |
| `/ops` → **Commercial** tab | `p.can_manage_billing` (`OperationsPage.jsx:135`) | **Yes** — every `/api/v3/commercial/*` endpoint re-checks server-side. Sound. |
| `/ops` → **Commercial Coverage** / **Manual Processing** tabs | `p.can_manage_organizations` (`OperationsPage.jsx:116`) | **Yes** — the MP admin API re-checks at the API boundary. Sound. |
| Enable/disable of admin coverage controls | `activeCanManage` prop (`OperationsPage.jsx:148-151`) | **Yes** — server refuses regardless. Sound. |
| `/billing` link in the consultant client plane | filtered out in `V3Layout` (PD-6) | **Yes** — `/billing` requires org membership; a consultant without it is refused. Sound. |
| Customer Billing plan card | rendered when data exists | **Yes** — `require_org_member()`. Sound. |

`CURRENT FACT` **No entitlement-bearing feature was found that is controlled only by UI
visibility without a server-side check.** This is a positive finding. The UI gates listed
above are navigation aids layered on top of real server authorization (AGENTS.md §7/§44
satisfied).

`IMPLEMENTATION GAP` But note the inverse: `api_access`, `managed_processing_available`,
`team_member_limit`, `processing_limits`, `included_storage_bytes`-as-a-capacity-limit,
and `capability.client_capacity` are **not enforced anywhere — not even in the UI**. They
are metadata.

---

## 19. Security / Tenancy

All probes below were read-only and were executed during this assessment against the live
local database and the current source.

| Question | Finding | Classification |
| --- | --- | --- |
| Can a consultant read another consultant's commercial data? | **No.** The consultant coverage endpoint resolves the firm from the authenticated consultant context and never accepts a firm id (`v3_manual_processing_coverage.py:6-9`, `:248-264`). | `CURRENT FACT` |
| Can an organisation read another organisation's commercial data? | **No.** `/api/v3/billing/*` resolves the org server-side via `_resolve_org` and every repository call is org-scoped (`get_for_org`, `list_for_org`). | `CURRENT FACT` |
| Can a client read consultant billing? | **No.** There is no endpoint, and the coverage projection for a client exposes only `{company_name}` — never capacity, allocation counts, other clients, allocation ids or routing ids (`v3_manual_processing_coverage.py:136-170`). | `CURRENT FACT` |
| Can a managed client read the consultant's subscription? | **No.** No endpoint exposes a firm subscription to a client. | `CURRENT FACT` |
| Can a consultant modify its own entitlements? | **No.** Entitlement is plan-derived and the consultant has no write path to `billing_plans`, `customer_subscriptions` or `billing_commercial_config`. | `CURRENT FACT` |
| Does Platform Admin have appropriate authority? | **In code, yes** — `require_staff` + `require_internal_staff` + `can_manage_billing`, with PE/tenant identities denied. **In the live environment, unreachable** because no role holds the flag (§17.1). | `CURRENT FACT` + `IMPLEMENTATION GAP` |
| Can commercial state be spoofed by the UI? | **No.** All billing tables are deny-by-default with no `authenticated` grants; `customer_subscriptions`, `usage_tracking`, `consultant_billing` and `organizations` are SELECT-only for `authenticated`; every commercial mutation requires an `idempotency_key` and is audited. | `CURRENT FACT` |
| Is hostname/branding treated as security identity? | **No.** `domain/consultant_entitlement.py` resolves presentation entitlements only and states it "never authorizes an actor and never grants capability". White-label/hostname is presentation. | `CURRENT FACT` |
| Are signed URLs leaked? | `upload_gate.py` records document events without object bytes or signed URLs; ACTION_SIGNED_URL_ISSUED is an audit action, not a stored URL. | `CURRENT FACT` |
| D36 P0 (customer self-granting credits/plan via PostgREST) | **Closed.** `authenticated` holds no write privilege on any billing table and no table-level write on `organizations`. Independently confirmed live. | `CURRENT FACT` |

**Existing issues found (recorded, NOT fixed):**

| # | Issue | Severity | Classification |
| --- | --- | --- | --- |
| S-1 | The entire admin commercial surface is unreachable in the local environment (no role holds `can_manage_billing`). This is an availability/operability defect, not a privilege escalation. | **High** | `IMPLEMENTATION GAP` |
| S-2 | `organizations_org_update` RLS policy remains present while its backing table privilege is revoked. Currently inert; it is a latent hazard if a future grant is re-added. | **Low** | `IMPLEMENTATION GAP` |
| S-3 | Admin billing authority rests on a **capability flag** rather than a distinct System Admin role identity. The project constitution requires administrative capabilities to remain explicit; the flag is explicit, but the role-identity linkage is unresolved. | **Low–Medium** | `PO DECISION REQUIRED` |
| S-4 | `GET /api/v3/commercial/storage` and `GET /api/v3/commercial/organizations` iterate all organisations with per-row queries — a scalability/DoS-surface concern at demo population scale. | **Medium** | `IMPLEMENTATION GAP` |
| S-5 | Credit-operations target is a free-text organisation id with no existence validation before the mutation attempt; a typo produces a late failure rather than a pre-flight rejection. | **Low** | `UX RECOMMENDATION` |

`CURRENT FACT` No security weakness was introduced, weakened or modified by this
assessment, because this assessment made no changes.

---

## 20. Test Coverage

### 20.1 Inventory (verified counts)

| Test file | Tests | What it actually covers | Classification |
| --- | --- | --- | --- |
| `backend/tests/unit/api/test_billing_core.py` | **17** | Credit grant/consume/adjust/rollover/refund/reversal, derived balances, emergency allowance, order lifecycle incl. approve → payment record → complete, idempotency conflicts | **Authoritative** |
| `backend/tests/unit/api/test_commercial_settings.py` | **19** | Admin commercial config versioning, plan create/publish/history, `can_manage_billing` authorization matrix, subscription activate + status change, audit entries | **Authoritative** |
| `backend/tests/unit/api/test_p6bill1_entitlement_and_consultant_commercial.py` | **23** | PO-D7 entitlement denial, consultant capability from `features.consultant`, registration mode (default OPEN, INVITATION_ONLY denies org + consultant self-registration, non-admin cannot change it) | **Authoritative** |
| `backend/tests/unit/api/test_ct_mp_sub_003_consultant_coverage.py` | **32** | Firm coverage mode/capacity, SELECTED_CLIENTS allocation + release, eligibility enforcement, over-allocation, ALL_ELIGIBLE_CLIENTS, inactive firm subscription grants nothing, direct OR sponsored combination | **Authoritative** |
| `backend/tests/unit/api/test_ct_mp_sub_004_coverage_surfaces.py` | **24** | Caller-scoped customer/consultant coverage projections and admin coverage separation | **Incomplete** — file is **untracked** (concurrent CT-MP-SUB-004) |
| `backend/tests/unit/domain/test_consultant_mp_coverage.py` | **22** | Pure-domain coverage rules incl. legacy `assisted_processing_available` compatibility | **Authoritative** |
| `backend/tests/unit/api/test_p6_2d_entitlement.py` | **2** | Entitlement enforced at the consultant submission boundary | **Authoritative** |
| `backend/tests/unit/domain/test_manual_processing_routing.py` | — | Plan→entitlement resolution and fallback source | **Authoritative** |
| `backend/tests/unit/api/test_manual_processing_routing.py` | — | Routing decisions | **Incomplete** — untracked |
| `backend/tests/unit/api/fakes.py` | — | In-memory doubles for plans, config, subscriptions, orders, storage, payments, idempotency, coverage/allocation | **Authoritative** |
| `backend/tests/integration/test_v3_rls_behavior.py` | — | **Negative RLS**: `authenticated` cannot write `billing_plans`, `billing_commercial_config`, `billing_credit_ledger`, `billing_orders`, `billing_storage_usage`, `billing_payment_records`, `billing_idempotency_keys`, `consultant_billing` | **Authoritative (environment-dependent)** — requires the integration DB |
| `backend/tests/integration/test_final_03_rls_remediation_live.py` | — | Live negative RLS probes | **Environment-dependent** |
| `frontend/src/v3/__tests__/manual-processing-coverage.test.jsx` | — | Customer/consultant/admin coverage UI incl. empty states and "no internal consultant state exposed" | **Authoritative** (new, untracked) |
| `frontend/src/v3/__tests__/api.test.js` | — | Frontend billing/commercial API client contract targets | **Incomplete** — contract shape only, no behaviour |
| `backend/tests/unit/tools/test_demo_lab_staff_role_provisioning.py` | — | Asserts the provisioner preserves migration-granted admin capabilities (`can_qc`, `can_manage_billing`, `can_manage_backups`) | **Partially authoritative** — see §20.3 |

**Approximate commercial test count: 139+ backend tests across 7 primary files.**

### 20.2 What is NOT tested

| Area | Tested? | Classification |
| --- | --- | --- |
| Credit ledger arithmetic, order lifecycle, idempotency | **Yes** | `AUTHORITATIVE` |
| Plan versioning create/publish/history at API level | **Yes** | `AUTHORITATIVE` |
| Plan `features` JSONB round-trip through the API | **Yes** (contract-level) | `AUTHORITATIVE` |
| Consultant coverage domain rules + API | **Yes** | `AUTHORITATIVE` |
| RLS deny-by-default on billing tables (negative) | **Yes** | `AUTHORITATIVE` (environment-dependent) |
| Registration-mode gating | **Yes** | `AUTHORITATIVE` |
| `managed_processing_available` / `api_access` **enforcement** | **No** — and no enforcement code exists | `MISSING` |
| Subscription upgrade / downgrade / cancel / renew semantics | **No** — not implemented | `MISSING` |
| Payment provider / checkout / webhook / refund execution | **No** — not implemented | `MISSING` |
| Frontend **BillingPage** behaviour | **No dedicated test file** | `MISSING` |
| Frontend **CommercialTab** behaviour | **Indirect only** — other tests mock it out | `MISSING` |
| Storage-metring UI (pagination/search/filter) | **No** — not implemented | `MISSING` |
| Migration idempotency for the D37 seed | **No** — and the live DB proves it is not idempotent | `MISSING` |
| `get_entitlement` with a real active subscription end-to-end | Partially (fixtures) | `INCOMPLETE` |
| Consultant commercial **UI** (there is none) | n/a | `MISSING` |
| Public pricing ↔ catalogue consistency | **No** | `MISSING` |

### 20.3 A contradicted assumption worth recording

`CURRENT FACT` `backend/tests/unit/tools/test_demo_lab_staff_role_provisioning.py`
asserts that provisioning **preserves** migration-granted admin capabilities
(`can_qc`, `can_manage_billing`, `can_manage_backups`).

`CURRENT FACT` The live database contradicts the effective outcome: **no** role carries
`can_manage_billing`, and no `admin`/`system_admin` role exists at all. Either the test
covers a different code path than the one that produced this database, or the database
predates/postdates that fix. This was **not** resolved by this assessment — resolving it
requires running the provisioner, which is out of scope for a read-only task.

`UNKNOWN` Whether the provisioner has been fixed since this database was provisioned.

### 20.4 Overall test verdict

`CURRENT FACT` No test suite was executed during this assessment (read-only, no
authorisation to run the suite, and running it was not required to establish the facts).
This section therefore records **what exists**, not a pass/fail verdict.

- **Authoritative**: the D37 billing core, the commercial settings/admin API, the
  registration gate, and the Manual Processing coverage domain.
- **Historical / environment-dependent**: the two live integration RLS files.
- **Incomplete**: the untracked CT-MP-SUB-004 files (concurrent work, not this task's).
- **Missing**: everything payment, everything self-service subscription, all frontend
  commercial surfaces, and migration idempotency.

---

## 21. Reusable Commercial Module Boundary

`ARCHITECTURAL RECOMMENDATION` — this is a proposal. It is **not** existing behaviour and
must not be presented as such.

### 21.1 Proposed conceptual boundary

```
Commercial Core (reusable module)
├── Plan catalogue            billing_plans (+ versioning, activation)
├── Pricing                   billing_plans.price/currency/interval  ← needs a price-set
├── Subscription lifecycle    customer_subscriptions (+ transition rules)
├── Payment abstraction       NEW (protocol + provider registry)
├── Payment transactions      billing_payment_records (+ checkout session)
├── Invoice / receipt         NEW (invoice model + artefact generation)
├── Entitlement resolution    BillingService.get_entitlement (unify with MP resolver)
├── Usage / metering          usage_tracking, billing_storage_usage (+ metering service)
├── Limits                    processing_limits, team_member_limit, included_*
├── Commercial state          organizations.billing_mode, subscription state
└── Audit                     audit_trail + billing_idempotency_keys
```

### 21.2 Deliberate exclusions from the module

`ARCHITECTURAL RECOMMENDATION` The following stay **outside** the Commercial Core:

- FIN-06 Manual Processing governance (`manual_processing_grants`)
- Manual Processing routing (`manual_processing_processors`, `manual_processing_routing`)
- Processing Entity model and work assignment
- Consultant-client relationship and client access profiles
- Staff RBAC / capability catalogue
- Branding, white-label and product-mode presentation
- Organisation, facility, asset, vehicle and supplier master data
- Document storage and the upload authorisation gate

Rationale: these are **operational** or **relationship** concerns. Making them part of the
commercial module would recreate exactly the concern-mixing that the current architecture
correctly avoids (`domain/consultant_entitlement.py:6-20`).

### 21.3 Module boundary risks

`ARCHITECTURAL RECOMMENDATION` Two hard constraints if this boundary is ever implemented:

1. **Do not introduce a second subscription source.** Every current consumer
   (`BillingService.get_entitlement`, `BillingService.consultant_capability`,
   `ManualProcessingRouter._plan_for_org`) must keep resolving through
   `customer_subscriptions` → `billing_plans`. `CT-SUB-001` §6 and CT-MP-SUB-003 §25 both
   forbid a parallel model.
2. **Do not introduce a second entitlement resolver.** The two existing resolvers read the
   same tables and can drift. Consolidating them behind one read model is a genuine
   improvement; adding a third would be a regression.

---

## 22. Reuse / Extend / Replace / New Matrix

`ARCHITECTURAL RECOMMENDATION` for every proposed Commercial Core component, mapped to
existing code and schema.

| Proposed component | Existing artefact | Verdict | Rationale |
| --- | --- | --- | --- |
| Plan catalogue | `billing_plans`, `data/billing.py::BillingPlansRepository`, `v3_commercial.py` plans API, `CommercialTab.jsx` plan table | **REUSABLE** | Versioning and historicity already correct |
| Plan catalogue — seed integrity | `20260824030000_d37_master_commercial_billing.sql` | **REPLACE (the seed statement only)** | Non-idempotent; already produced duplicate versions |
| Plan catalogue — feature authoring | `billing_plans.features` (carrier exists) | **EXTEND** | Carrier correct; values unauthored; API supports it; UI does not |
| Plan catalogue — activation control | `billing_plans.is_active` | **EXTEND** | Enforced at activation; no UI |
| Pricing | `billing_plans.price/currency/billing_interval` | **EXTEND** | Single price + single interval; needs a multi-interval price set |
| Pricing — currency coherence | live catalogue is USD+GBP mixed | **REPLACE (data)** | Data defect, not a schema defect |
| Subscription lifecycle | `customer_subscriptions` + `Subscription` domain + `upsert_active` / `update_status` | **REUSABLE** | Correct state machine for an org-scoped relationship |
| Subscription lifecycle — transitions | `BillingService.activate_subscription` / `change_subscription_status` | **EXTEND** | Admin-only today; no scheduled expiry, renewal, dunning or grace period |
| Subscription lifecycle — change history | `audit_trail` only | **NEW** (or accept audit-as-history) | No subscription-change record beyond audit |
| Payment abstraction | — | **NEW** | Nothing exists at code level |
| Payment transactions | `billing_payment_records` | **REUSABLE** | Row shape is deliberately provider-neutral and correct |
| Payment transactions — virtual provider | — | **NEW** | No demo/virtual provider exists |
| Checkout session | — | **NEW** / `UNKNOWN` | Whether this needs a table is not established |
| Webhook ingestion | `billing_idempotency_keys` | **EXTEND** | Idempotency primitive exists; no ingestion path |
| Invoice / receipt | — | **NEW** | Nothing exists |
| Entitlement resolution | `BillingService.get_entitlement` | **REUSABLE** | Single server-authoritative resolver |
| Entitlement resolution — unification | `BillingService.get_entitlement` + `domain/manual_processing.entitlement_from_plan` | **EXTEND** | Two resolvers over the same tables; drift risk |
| Usage — credits | `billing_credit_ledger` + `consume_credits` | **REUSABLE** | Correct financial primitive; append-only, derived balance |
| Usage — STANDARD allowance | `usage_tracking` + `_standard_usage_this_period` | **REUSABLE** | Correct mechanism; narrower than the requested "usage/metering" |
| Usage — storage | `billing_storage_usage` + `meter_storage` | **REUSABLE** | Server-measured, never browser-reported |
| Usage — broad metering | — | **EXTEND** / **NEW** | Documents/rows/reports metering outside the charge path is absent |
| Limits | `processing_limits`, `team_member_limit`, `included_credits`, `included_storage_bytes` | **EXTEND** | Stored and projected; **not enforced** |
| Limits — `api_access`, `managed_processing_available` | `billing_plans` columns | **EXTEND or RETIRE** | Metadata only; disposition is a PO decision |
| Commercial state | `organizations.billing_mode`, `customer_subscriptions.lifecycle_status` | **REUSABLE** | Authoritative and write-protected |
| Audit | `audit_trail` (append-only) + `billing_idempotency_keys` | **REUSABLE** | Correct and already used on every mutation |
| Order model | `billing_orders` + line-item snapshot | **REUSABLE** | Covers automated/assisted/managed/storage |
| Admin commercial API | `v3_commercial.py` (834 lines, complete) | **REUSABLE** | Comprehensive; under-exposed in UI |
| Admin commercial UI | `CommercialTab.jsx` | **EXTEND** | Present but incomplete (features, activation, target selection, pagination) |
| Customer billing UI | `frontend/src/v3/customer/BillingPage.jsx` | **EXTEND** | Preserve and extend, do not replace (CT-SUB-001 §5, CT-UX-SUB-001 §18) |
| Public pricing | `PricingPage.jsx`, `LandingPage.jsx` | **REPLACE (data source)** | Hard-coded prices; must read the catalogue if CT-SUB-001 §3 is adopted |
| Registration mode | `billing_commercial_config` key + `resolve_registration_mode` | **EXTEND** | Resolver implemented; **no data row** |
| Consultant commercial UI | — | **NEW** | Nothing exists |
| Consultant-sponsor persistence | `consultant_mp_allocations` migration | **EXTEND (apply)** | Authored; not applied |
| `consultant_billing` | legacy table | **REPLACE/RETIRE (later)** | 0 rows, no code, contradicts org-scoped billing; AGENTS.md §79 forbids casual removal |
| Legacy `organizations.subscription_*` / `trial_*` / `billing_*` | legacy columns | **REPLACE/RETIRE (later)** | Retained and write-revoked |
| `Provisioner role data` | `tools/demo_lab/provision.py::ensure_staff_roles` | **REPLACE (the permission write)** | Wholesale replacement erases migration-granted capabilities |

`UNKNOWN` Whether the concurrent `CT-CONSULTANT-PLATFORM-CLOSURE-01` work will change the
consultant commercial capability projection or the client access profile surface before
this plan is actioned. This assessment could not treat those files as stable.

---

## 23. Target Architecture

`ARCHITECTURAL RECOMMENDATION`

```
                        ┌───────────────────────────────────────────────┐
                        │            PLATFORM ADMIN                     │
                        │  plans · pricing · subscriptions · credits    │
                        │  usage · coverage · audit · payment records   │
                        └───────────────────┬───────────────────────────┘
                                            │ can_manage_billing (BROKEN today)
                                            ▼
┌─────────────────────┐         ┌───────────────────────────────────────┐
│       PUBLIC        │         │        COMMERCIAL CORE                │
│  pricing (catalogue)│────────▶│  Plan catalogue (versioned)           │
│  signup             │         │  Pricing (multi-interval)             │
│  plan selection     │         │  Subscription lifecycle               │
│  checkout (virtual  │         │  Payment abstraction + providers      │
│   first)            │         │  Entitlement resolution (ONE resolver)│
└─────────────────────┘         │  Usage / metering / limits            │
                                │  Audit + idempotency                  │
                                └───────┬───────────────┬───────────────┘
                                        │               │
                        ┌───────────────▼──┐   ┌────────▼────────────────┐
                        │   CONSULTANT     │   │   DIRECT ORGANISATION   │
                        │  Subscription &  │   │  Subscription & Billing │
                        │  Billing surface │   │  (self-service per PO)  │
                        └────────┬─────────┘   └────────┬────────────────┘
                                 │                      │
                                 │  firm's OWN org subscription
                                 ▼
                        ┌───────────────────────────────────────────────┐
                        │  CONSULTANT-MANAGED CLIENT ORGANISATION       │
                        │  inherits commercial behaviour from the FIRM  │
                        │  no duplicate client subscription             │
                        └───────────────────────────────────────────────┘
                                        │
                                        ▼  (OUTSIDE the Commercial Core)
                        ┌───────────────────────────────────────────────┐
                        │  Manual Processing governance (FIN-06)        │
                        │  Routing → Processing Entity assignment       │
                        └───────────────────────────────────────────────┘
```

`ARCHITECTURAL RECOMMENDATION` Four invariants the target architecture must preserve:

1. **One subscription model, organization-scoped.** Consultant firms are represented by
   their own organisation subscription. Do not create a consultant-firm subscription table
   (AGENTS.md §11 forbids cloning to change ownership; `CT-SUB-001` §6 forbids a second
   model).
2. **One authoritative price.** Price is always resolved server-side from the catalogue at
   purchase time. A displayed price is never the authority for charging.
3. **One entitlement resolver.** Plan → subscription → entitlement → feature → usage.
4. **Commercial entitlement never grants access.** Org access stays on membership/grants;
   capability stays on RBAC; presentation stays on product mode.

`ARCHITECTURAL RECOMMENDATION` The module boundary should be a **package boundary inside
the existing layer convention** (i.e. `domain/commercial/`, `services/commercial/`,
`data/commercial/`, `api/v3_commercial.py`), not a new deployment or a second application.
AGENTS.md §64 forbids separate deployments and duplicate tenant abstractions.

---

## 24. Implementation Phases

`ARCHITECTURAL RECOMMENDATION` Phases are ordered so that **nothing is built on data that
cannot yet exist**. Phase 0 exists because the current environment cannot demonstrate or
test any of the rest.

### Phase 0 — Unblock the environment (prerequisite, no new architecture)

| Item | Why | Owner |
| --- | --- | --- |
| Fix `tools/demo_lab/provision.py::ensure_staff_roles` so it **merges** rather than **replaces** `staff_roles.permissions`, preserving migration-granted `can_manage_billing`, `can_qc`, `can_view_all`, `can_manage_backups` | The admin commercial surface is unreachable (§17.1) | Implementation |
| Decide + publish the role that owns commercial configuration | `PO DECISION REQUIRED` (§17.1) | **PO** |
| Apply the authored migrations `20261010000000` (adds `consultant_profiles.organization_id`), `20261030000000` (`manual_processing_processors`), `20261101000000` (`consultant_mp_allocations`) | Sponsored coverage is unreachable (§11.3) | Implementation |
| Publish `registration_mode` explicitly (either value) instead of relying on the default | Removes the public-copy contradiction (§14.3) | **PO** + Implementation |
| Make the D37 plan seed idempotent and de-duplicate the live catalogue | Duplicate versions (§8.3) | Implementation |
| Resolve the catalogue currency (`USD` vs `GBP`) and reconcile the public page | Data conflict (§8.3) | **PO** + Implementation |
| Author the plan entitlement blocks (`features.manual_processing`, `features.consultant`, `features.consultant_manual_processing`) as a **new plan version** | Every entitlement resolves false today (§8.3) | **PO** + Implementation |
| Create at least one real subscription for a test organisation | 0 subscriptions makes the whole chain inert (§9.1) | Test setup |

### Phase A — Commercial Core

- Harden the plan model: multi-interval pricing, activation control, feature authoring path.
- Formalise the subscription lifecycle: explicit transition rules, period boundaries,
  expiry/renewal sweep.
- Introduce the **payment abstraction**: `PaymentProvider` protocol + `VirtualProvider`
  (virtual first — no credentials).
- Persist provider selection in the **existing** `billing_commercial_config` (new key).
- Route provider events into the **existing** `billing_payment_records` and
  `billing_idempotency_keys`.
- Unify entitlement resolution behind one read model.
- Extend usage/limits so stored limits become enforceable.
- Keep all audit on `audit_trail`.

### Phase B — Platform Admin

- Plan editor that exposes **every** plan field including `features`, `billing_interval`,
  `is_active`, `team_member_limit`, `processing_limits` and the boolean entitlements.
- Replace raw JSON textareas with structured editors for the commercial rule keys.
- Subscription management with a **searchable organisation picker**, not a UUID field.
- Credit operations with the same picker, plus a firm target if/when a firm credit scope
  is decided.
- Usage/metering surface with server-side aggregation, pagination, search, filtering,
  date range and drill-down.
- Surface before/after version and reason inline from `audit_trail`.
- Consultant coverage/allocation UI (currently API-only).

### Phase C — Public

- Drive `/pricing` from the catalogue (or a published projection) rather than hard-coded
  values.
- Add a plan-selection step to signup/onboarding.
- Add a checkout step backed by `VirtualProvider`.
- Add subscription activation + entitlement provisioning on successful checkout.
- Align the public copy with the published `registration_mode`.

### Phase D — Consultant

- A Subscription & Billing surface in the consultant workspace: current plan,
  usage/limits, payment state, upgrade/change, cancellation.
- Consultant plan visibility (a consultant-scoped plan-catalogue projection).
- Preserve the PD-6 boundary: the client's `/billing` is never offered in the client plane.

### Phase E — Direct Organisation

- Commercial state view (already partially present on `/billing`).
- Self-service plan change — **only if** the PO permits it (see `D-4` in §27).
- Billing detail: payment method, invoices/receipts (dependent on Phase A).

### Phase F — Consultant-managed Organisations

- Keep the firm as the payer; keep the client's commercial behaviour inherited.
- Ensure the client's Manual Processing coverage continues to render the firm's commercial
  context, not the client's.
- Decide + implement (or explicitly document as intentional) whether a managed client may
  hold its own subscription.

### Phase G — Integration

- Consultant capabilities (`features.consultant`) — author the values, then enforce
  `client_capacity` and `team_member_limit` if the PO decides they are real limits.
- Client access profiles — integration only; do not redesign (owned by the consultant
  workstream).
- Branding / white-label — resolve the **dual source of truth** (plan feature vs
  `commercial_mode`).
- Manual Processing — keep it wired to the firm's plan; do not fork billing.
- Usage limits — enforce `processing_limits`, `team_member_limit`, storage capacity (if
  the PO decides to enforce rather than meter).

### Phase H — Independent verification

- Security and tenancy negative tests for every new commercial endpoint.
- Lifecycle tests: activate → renew → past_due → suspend → cancel → expire.
- Payment tests: virtual provider happy path, replay/idempotency, webhook replay.
- Entitlement tests: plan → subscription → entitlement → enforcement, both ALLOW and DENY.
- UI verification across the D21 responsive breakpoints and the accessibility checklist.
- Regression: the existing 139+ commercial tests must remain green.
- Commercial QA evidence per AGENTS.md §53.

`ARCHITECTURAL RECOMMENDATION` Phase 0 is deliberately **not** optional. Building Phase A
on top of an environment where no subscription exists and no admin can reach the config
surface would produce unverifiable work.

---

## 25. Dependency Graph

`ARCHITECTURAL RECOMMENDATION` with blockers marked.

```
   EXISTING D37 ARCHITECTURE  (committed, RLS-protected, tested)
   billing_plans · billing_commercial_config · customer_subscriptions
   billing_credit_ledger · billing_orders · billing_storage_usage
   billing_payment_records · billing_idempotency_keys
                │
                │  BLOCKER B1 — no staff role carries can_manage_billing
                │  BLOCKER B2 — 0 customer_subscriptions rows
                │  BLOCKER B3 — no plan carries an entitlement block
                │  BLOCKER B4 — D37 seed is not idempotent (duplicate versions)
                ▼
        COMMERCIAL CORE  (Phase A)
                │
                ├──────────────┬──────────────┐
                ▼              ▼              ▼
        PLAN / PRICING   SUBSCRIPTION    PAYMENT ABSTRACTION
        (Phase A)        LIFECYCLE       (Phase A)
                │              │              │
                │              │   BLOCKER B5 — no provider; virtual first
                │              │   BLOCKER B6 — no checkout/session concept
                ▼              ▼              ▼
            ┌───────────────────────────────────────┐
            │        ENTITLEMENT RESOLUTION         │
            │  (unify the two existing resolvers)   │
            └───────────────────┬───────────────────┘
                                │  BLOCKER B7 — entitlement not enforced for
                                │  api_access / managed / team limit / capacity
                                ▼
     ┌──────────┬───────────────┬────────────────┬──────────────────┐
     ▼          ▼               ▼                ▼                  ▼
  PUBLIC    CONSULTANT     ORGANISATION    PLATFORM ADMIN     MANAGED CLIENTS
  (Phase C) (Phase D)      (Phase E)       (Phase B)          (Phase F)
     │          │               │                │                  │
     └──────────┴───────────────┴────────────────┴──────────────────┘
                                │
                                ▼
                    INTEGRATION (Phase G)
     consultant capability · client access · branding · MP · limits
                                │
                                ▼
                INDEPENDENT VERIFICATION (Phase H)
```

### 25.1 Blockers

| # | Blocker | Blocks | Owner |
| --- | --- | --- | --- |
| B1 | No staff role carries `can_manage_billing`; no `admin`/`system_admin` role exists locally | All Phase B work; demonstrability of every admin surface | **PO** (role choice) + Implementation (provisioner) |
| B2 | `customer_subscriptions` = 0 rows | Demonstrability + testing of entitlement, usage, credits, storage, MP routing | Implementation/Test setup |
| B3 | No plan carries an entitlement block | Consultant capability, MP coverage, any feature-based entitlement | **PO** (which blocks) + Implementation |
| B4 | D37 seed not idempotent | Catalogue integrity | Implementation |
| B5 | No payment provider | Phases C, E (payment-dependent parts) | **PO** (provider choice) |
| B6 | No checkout-session concept; needs design | Phase C | **PO** + Architecture |
| B7 | Stored limits are not enforced | Phase G | **PO** (enforce vs meter) |
| B8 | Sponsored-coverage persistence migrations not applied | Phase F, MP coverage demonstration | Implementation |

### 25.2 Dependencies that are already satisfied

- `CURRENT FACT` The event-driven order → payment-record → completion chain is already
  proven by `test_billing_core.py` (17 tests) — no new design is needed for the audit and
  idempotency layers.
- `CURRENT FACT` The versioned config mechanism already allows a new configuration key
  (e.g. `payment_provider`) to be added with no schema change.

---

## 26. Risks

| # | Risk | Likelihood | Impact | Classification | Mitigation |
| --- | --- | --- | --- | --- | --- |
| R-1 | A future implementation creates a **second** subscription/plan/payment model | Medium | High | `ARCHITECTURAL RECOMMENDATION` | Enforce the existing-first rule; extend `billing_*`; forbid a parallel source in review |
| R-2 | A future implementation adds `authenticated` grants to billing tables "to make the UI work" | Medium | High | `ARCHITECTURAL RECOMMENDATION` | Preserve the deny-by-default posture; keep authorization in FastAPI |
| R-3 | The admin commercial surface stays unreachable, so Phase A/B work cannot be verified | **High** | High | `IMPLEMENTATION GAP` | Phase 0 first (§24) |
| R-4 | Two entitlement resolvers drift apart as features are added | Medium | Medium | `IMPLEMENTATION GAP` | Unify behind one read model (Phase A) |
| R-5 | The plan catalogues and the public price page diverge further (already diverged) | **High** (already true) | Medium | `IMPLEMENTATION GAP` | Phase C: catalogue-driven pricing |
| R-6 | Mixed currency (USD/GBP) is charged against customers who were shown GBP | Medium | **High** (commercial/legal) | `PO DECISION REQUIRED` | Resolve D-1 before any real payment |
| R-7 | A dual source of truth for white-label (plan `features.consultant.white_label` vs `commercial_mode`) produces an inconsistent client experience | Medium | Medium | `IMPLEMENTATION GAP` | Decide one authority in Phase G |
| R-8 | `GET /commercial/storage` and `/organizations` N+1 patterns become unusable at investor-demo scale | High (already) | Medium | `IMPLEMENTATION GAP` | Server-side aggregation + pagination in Phase B |
| R-9 | A real payment provider is added without the abstraction, coupling business logic to a vendor | Medium | High | `ARCHITECTURAL RECOMMENDATION` | Build `PaymentProvider` + `VirtualProvider` first |
| R-10 | The concurrent `CT-CONSULTANT-PLATFORM-CLOSURE-01` work changes consultant commercial files mid-phase | **High** (currently happening) | Medium | `UNKNOWN` | Sequence after the consultant closure, or freeze those files during commercial work |
| R-11 | Legacy `consultant_billing` / `organizations.subscription_*` columns are removed casually | Low | Medium | `PO DECISION REQUIRED` | AGENTS.md §79: deprecation path required |
| R-12 | Self-service subscription signup goes live before entitlement enforcement is complete, allowing free processing | Low | High | `ARCHITECTURAL RECOMMENDATION` | Enforce B7 before Phase C activation |
| R-13 | Trial/discount/proration semantics are invented by an implementer | Medium | High | `PO DECISION REQUIRED` | Keep them out of scope until decided |
| R-14 | The duplicate plan versions are presented to a customer as real tier options | Low | Medium | `IMPLEMENTATION GAP` | De-duplicate (Phase 0) |
| R-15 | Demo-lab provisioning erases capabilities again after any future migration grant | Medium | High | `IMPLEMENTATION GAP` | Fix the merge semantics (Phase 0) and keep the regression test |

---

## 27. Decisions Required from the PO

`PO DECISION REQUIRED` — none of these is decided by this assessment.

### 27.1 Carried forward from CT-SUB-001 §57 and CT-UX-SUB-001 §64 (still open)

Final plan names · final plan count · final prices · final currencies · final limits ·
final trial policy · final discount policy · tax implementation and provider ·
payment provider(s) to launch with · provider priority · upgrade proration ·
downgrade semantics · refund policy · failed-payment grace period ·
data-retention interaction · enterprise custom pricing model · add-on catalogue ·
usage-overage policy · whether customers may self-serve all plan changes ·
whether annual plans receive discounts · analytics KPIs.

### 27.2 Surfaced or confirmed by this assessment

| # | Decision | Why it is needed | Evidence |
| --- | --- | --- | --- |
| **D-1** | **Catalogue currency.** Resolve `USD` (starter/business) vs `GBP` (professional/enterprise/assisted_pricing) and reconcile the public `£` display | Mixed currencies are live in the charged catalogue | §8.3 |
| **D-2** | May the public pricing page keep hard-coded prices, or must it read the catalogue? | Conflicting with the proposed `CT-SUB-001` §3 rule | §8.3, §14.1 |
| **D-3** | Which payment provider(s), and the shape of the provider abstraction contract | No provider exists; Phases C and E depend on it | §10 |
| **D-4** | Is self-service plan change / cancellation permitted for customers **and** consultants? | Determines whether new customer write endpoints are required | §9.3, §16.2 |
| **D-5** | Which plan `features` blocks must be authored first (`manual_processing`, `consultant`, `consultant_manual_processing`)? | All entitlement currently rests on the legacy boolean fallback | §8.1, §17.3 |
| **D-6** | Are the CT-MP-SUB-003/004 migrations and the P17A `consultant_profiles.organization_id` addition ratified for application, and when? | Sponsored coverage is unreachable without them | §11.3 |
| **D-7** | Should the Admin commercial surface be promoted out of `/ops` → "Commercial" into a dedicated Subscription/Commercial control plane with its own navigation? | Directly addresses the Platform Owner's original observation | §17.3 |
| **D-8** | Are `managed_processing_available` and `api_access` **enforced entitlements** or **informational metadata**? | They are metadata today and are seeded as marketing flags | §18.2 |
| **D-9** | Retire `consultant_billing` and the legacy `organizations.subscription_*` / `trial_*` / `billing_*` columns — and on what migration path? | AGENTS.md §79 forbids casual removal | §4.3, §22 |
| **D-10** | Does subscription **visibility** for customers/consultants require new read endpoints, or does `/api/v3/billing/me` suffice? | Determines the consultant API surface for Phase D | §6.1, §15 |
| **D-11** | **Which role owns commercial configuration** (`can_manage_billing`) — the release `system_admin` model or the local `admin` role? | B1; without an answer the Admin surface stays unreachable | §17.1 |
| **D-12** | Is the platform **open** or **invitation-only** for registration? | Public copy contradicts the runtime default | §14.3 |
| **D-13** | Must a consultant-managed organisation be **prevented** from holding its own subscription, or is dual coverage acceptable? | "No duplicate client subscription" is currently an intention, not an invariant | §16.2 |
| **D-14** | Should `team_member_limit`, `processing_limits` and storage capacity be **enforced** (refusal) or remain **metered/billable**? | Determines whether limits are real or metadata | §12.1, §18.4 |
| **D-15** | Which authority wins for white-label: the plan feature or `commercial_mode`? | Two sources of truth today | §18.2 |
| **D-16** | Is there a **consultant-firm credit scope**, or are credits strictly org-scoped? | The credit UI has no firm target; the task brief anticipates multi-target credit operations | §13.2, §13.3 |
| **D-17** | Should the "Commercial Coverage" tab be renamed/re-scoped for clarity? | Three tabs use overlapping commercial vocabulary | §11.2, §17.3 |

`PO DECISION REQUIRED` Also still open from the prior discovery: approval of the
`CT-UX-MP-SUB-003` ASCII UI/UX specification, the reconciliation of `CT-SUB-001` /
`CT-UX-SUB-001`, and the disposition of the superseded
`CarbonTally_Manual_Processing_Subscription_Options_old.md`.

---

## 28. Items Already Decided — DO NOT REOPEN

`CURRENT FACT` The following are ratified decisions or frozen UX/architecture. This
assessment treats them as constraints, not as open questions.

| # | Decided item | Source | Status |
| --- | --- | --- | --- |
| 1 | Billing is **organization-scoped**; there is exactly one subscription model | D37-0/D37; `CT-SUB-001` §6 | **RATIFIED** |
| 2 | Commercial state is **server-authoritative**; the browser is never authoritative | D37 migration headers; AGENTS.md §7/§44 | **RATIFIED** |
| 3 | The commercial model must be **configurable, versioned and provider-neutral**; two billing modes CREDIT/STANDARD; one common order model | D36 → D37-0 → D37 | **RATIFIED** |
| 4 | **P0 billing security**: no client writes to authoritative billing state; `authenticated` write grants revoked on `usage_tracking`, `customer_subscriptions`, `consultant_billing`, `organizations` | D37-0 | **RATIFIED — do not weaken** |
| 5 | Every commercial mutation is **idempotent and audited** | D37; `billing_idempotency_keys` + `audit_trail` | **RATIFIED** |
| 6 | No-chargeable-entitlement ⇒ the chargeable action is **DENIED** (PO-D7) | P6-BILL-1 | **RATIFIED** |
| 7 | Registration mode is a **provisioning gate only**; it never grants authorization, access, capability or PE/CT authority | D-A / CT-BILL-004 | **RATIFIED** |
| 8 | Consultant capability comes from the firm's **own organisation subscription** (`features.consultant`); no second organisation is created | D-C / CT-CONSULT-003 | **RATIFIED** |
| 9 | Manual Processing is a **subscription-plan capability**, with two paths (direct OR consultant-sponsored) | CT-PO-MP-SUB-003 | **PO APPROVED — AUTHORITATIVE** |
| 10 | Manual Processing commercial entitlement is **only** the firm's own org subscription plan; a relationship alone never grants it | CT-PO-MP-SUB-003 §25 | **PO APPROVED** |
| 11 | `SELECTED_CLIENTS` and `ALL_ELIGIBLE_CLIENTS` are the only coverage modes | CT-PO-MP-SUB-003 | **PO APPROVED** |
| 12 | An allocation row is **not** an authorization grant | CT-MP-SUB-003 | **RATIFIED** |
| 13 | `manual_processing_effective = subscription_entitled AND governance_enabled`; a stale governance grant can never bypass the subscription | FIN-06 + `domain/manual_processing.py` | **RATIFIED** |
| 14 | ENTITLEMENT / ELIGIBILITY / GOVERNANCE / ALLOCATION / PE ASSIGNMENT are **five separate concepts** and must not collapse | CT-MP-SUB-003 §1 | **RATIFIED** |
| 15 | CarbonTally is the **direct merchant**; billing is in-house, no reseller | `CARBONTALLY_DIRECT_MERCHANT_COMMERCIAL_ARCHITECTURE_V1.md` | **Reference decision** |
| 16 | **CarbonTally bills consultant FIRMS** — a managed client's billing is not the consultant's billing; `/billing` is excluded from the consultant client plane | PD-6 (`V3Layout.jsx:135-140`) | **RATIFIED UX** |
| 17 | The client portal has **no** billing, branding or user-management capability | PO-9 / PO-2 / PO-3A / PO-5 (`ClientPortal.jsx:11-13`) | **RATIFIED** |
| 18 | Consultant commercial entitlement (plan/seats/mode/white-label) is **CarbonTally-Admin-controlled**, not consultant-self-administered | PO-5 (`ConsultantTeamTab.jsx:32-34`) | **RATIFIED** |
| 19 | The canonical staff/admin control plane is V3 `/ops` | CL-66 | **RATIFIED** (legacy retirement not PO-signed) |
| 20 | The five consultant boundaries — PRODUCT MODE, COMMERCIAL ENTITLEMENT, CONSULTANT RBAC, CLIENT ACCESS PROFILE, CARBONTALLY AUTHORITY — must not collapse | `domain/consultant_entitlement.py:6-20` | **RATIFIED** |
| 21 | A consultant-client relationship ending preserves `organization.id`, data, history and provenance; **do not clone the organisation** | AGENTS.md §11 | **RATIFIED** |
| 22 | Three product modes: STANDARD / CO-BRANDED / WHITE-LABEL; unknown mode fails closed to STANDARD; the stored mode wins over legacy boolean flags | CT-CONSULTANT-MODEL-IMPLEMENTATION-03; PO-3B/PO-4 | **RATIFIED** |
| 23 | D19 workbench, D21 design system and D17 master-data UX are frozen | AGENTS.md §39/§40/§41 | **FROZEN** |
| 24 | Existing customer Billing functionality must be **preserved and extended**, not replaced | `CT-SUB-001` §5; `CT-UX-SUB-001` §18 | **Proposed but consistent with all ratified discipline** |
| 25 | **Existing-first rule**: extend the existing subscription infrastructure; never create a new Subscription model | `CT-SUB-001` §6 | **Proposed but consistent** |

### 28.1 Explicitly out of scope for this assessment (per the task instruction)

`CURRENT FACT` This assessment did **not** reopen, and must not be read as reopening:

- the Consultant Plane redesign
- the client workspace redesign
- the consultant/client relationship model
- PO-1 through PO-10
- client access profile semantics
- the consultant capability model
- tenant invariants

`CURRENT FACT` Where a Commercial dependency touches the Consultant Platform, this
document references the existing decision/architecture and does not redesign it. Where
concurrent `CT-CONSULTANT-PLATFORM-CLOSURE-01` changes made a file set unstable, that is
recorded as `UNKNOWN` rather than asserted.

---

## 29. Recommended Next Implementation Task

`ARCHITECTURAL RECOMMENDATION` — **not** an implementation authorisation.

**Recommended next task: `CT-COMMERCIAL-PHASE-0-UNBLOCK-01`**

A small, bounded, largely **data-and-provisioning** task that makes the existing
commercial architecture demonstrable and testable, with the smallest possible code
footprint.

**Scope:**

1. Fix `tools/demo_lab/provision.py::ensure_staff_roles` to **merge** permissions instead
   of replacing them, preserving migration-granted capabilities. Keep/extend
   `backend/tests/unit/tools/test_demo_lab_staff_role_provisioning.py` as the regression
   guard.
2. Apply the authored migrations that the sponsored-coverage model depends on
   (`20261010000000` for `consultant_profiles.organization_id`, `20261030000000`,
   `20261101000000`) in a controlled environment — **subject to D-6**.
3. Make the D37 plan seed statement idempotent and de-duplicate the local catalogue
   — **subject to D-1** for the currency values it publishes.
4. Publish `registration_mode` explicitly — **subject to D-12**.
5. Author the plan entitlement blocks as **new plan versions** — **subject to D-5**.
6. Create one test subscription and one credit grant so the entitlement → usage → charge
   chain can be exercised end-to-end.

**Explicitly OUT of scope for that task:** any payment provider, checkout, invoice, trial,
discount, add-on, proration, tax, consultant subscription UI, self-service plan change, or
new commercial table.

**Why this and not "build the subscription system":** `CURRENT FACT` the subscription
system's core already exists and is committed. What is missing is (a) reachability of the
admin surface, (b) data in the tables, (c) authored entitlement values, and (d) catalogue
integrity. Building Phase A on top of the current state would produce work that cannot be
verified.

**Ordering constraint:** `UNKNOWN` whether `CT-CONSULTANT-PLATFORM-CLOSURE-01` should
complete first. The consultant closure touches `manual_processing_admin.py`,
`domain/manual_processing.py`, `data/manual_processing.py`, `manual_processing_auth.py` and
several consultant frontend files — the same files Phase 0/Phase A would touch. Recommend
sequencing to avoid file-level collision.

---

## 30. Independent Verification Plan

`ARCHITECTURAL RECOMMENDATION` — a plan for verifying future commercial work independently
of the implementing agent, consistent with AGENTS.md §51–§53 and §72–§73.

### 30.1 Environment and evidence baseline

- Record branch, `HEAD` SHA, and worktree state before and after (AGENTS.md §70).
- Record the Git SHA of the verified revision in every piece of evidence.
- Record screenshots of **authenticated workspaces** (not landing pages) at the D21
  breakpoints: 1920x1080, 1440x900, 1280x800, 1024x768, 768x1024, 430x932, 390x844,
  375x812.
- Record console errors, network evidence (request/response), and database evidence for
  every claim.

### 30.2 Database verification

- Assert `to_regclass` presence for every table the change depends on.
- Assert row counts before/after for `customer_subscriptions`, `billing_credit_ledger`,
  `billing_orders`, `billing_storage_usage`, `billing_payment_records`,
  `billing_idempotency_keys`.
- Assert RLS enablement and policy counts remain unchanged on the seven D37 tables (i.e.
  still 0 policies) and that `authenticated` still holds **no** grants on them.
- Assert `authenticated` still holds **SELECT only** on `customer_subscriptions`,
  `usage_tracking`, `consultant_billing`, `organizations`.
- Assert the plan catalogue has no duplicate `(plan_code, version)` and exactly one row
  per `plan_code` with `effective_to IS NULL`.
- Assert at least one staff role carries the capability the commercial surface requires.

### 30.3 Security and tenancy (ALLOW **and** DENY for each)

Customer A → Customer B · Client A → Client B · Consultant A → Consultant B ·
Consultant A → Consultant B's client · PE A → PE B · PE → prohibited customer document ·
Viewer → prohibited write · Member → admin operation · Staff → Staff Admin operation ·
Staff Admin → System Admin-only operation · Customer → internal operations ·
PE → internal operations.

Additionally, for every new commercial endpoint:
- unauthenticated request → denied
- authenticated-but-unauthorised role → denied (403, not a UI redirect)
- no client-supplied organisation/firm/subscription/price/entitlement value is trusted
- replay of any commercial mutation with the same idempotency key → conflict, no
  duplicate ledger/order/payment row.

`CURRENT FACT` Every unexpected ALLOW must be treated as a serious security finding
(AGENTS.md §45).

### 30.4 Lifecycle verification

Exercise the state machine end-to-end for at least one organisation:
`pending → trial → active → past_due → suspended → cancelled → expired`, asserting at each
step what the entitlement resolver returns and what the charge path does (ALLOW vs 403/402).
Assert that `cancelled`/`expired` frees the organisation for a new relationship and that an
active duplicate is refused.

### 30.5 Payment verification (when a virtual provider exists)

- Virtual checkout happy path → payment record `confirmed` → subscription `active`.
- Webhook replay with the same event id → no duplicate payment record.
- Failed payment → `failed` record → subscription transition per the PO-decided policy.
- Refund path → record status, ledger effect, subscription effect.
- Assert that **no** provider secret, token or signed URL appears in logs, audit payloads,
  or the database.

### 30.6 Entitlement verification

For each authored feature block, prove both directions:
- plan carries `manual_processing.enabled = true` → chargeable Manual Processing allowed
- plan carries `manual_processing.enabled = false` → denied despite `assisted_processing_available`
- firm plan carries `consultant_manual_processing` + active relationship + (mode
  permitting) allocation → sponsored coverage true
- the same **without** the plan block → coverage false (a relationship is never an
  entitlement)
- the same **with** the block but **without** governance → `not_enabled`
- the same **with** the block and governance but **without** a processor →
  `no_processor_configured`

### 30.7 UI verification

Per commercial surface: navigation reachability for each role; pagination/search/filter/
sort behaviour at scale; empty states; loading states (distinct from "working"); error
states that do not expose raw exceptions; confirmation for destructive actions;
inline audit history; keyboard navigation and focus management; contrast and labels.

### 30.8 Regression

`CURRENT FACT` The existing commercial suite comprises at least: 17 + 19 + 23 + 32 + 24 +
22 + 2 = **139 backend tests** across seven primary files, plus the frontend
`manual-processing-coverage.test.jsx` and the `api.test.js` contract tests. All must remain
green. Additionally, the two live integration RLS suites must be run in the environment
that supports them.

### 30.9 Acceptance language

`ARCHITECTURAL RECOMMENDATION` Report using the AGENTS.md §73 vocabulary and never
collapse it:

`IMPLEMENTED` ≠ `TESTED` ≠ `VERIFIED` ≠ `ACCEPTED`.

"Implemented but not independently verified" is a valid and expected status.
No acceptance verdict may be issued on the strength of a passing unit test, a loading
page, or a successful single API call.

---

## Appendix A — Worktree Safety Record

`CURRENT FACT` Captured at the start of this assessment.

| Item | Value |
| --- | --- |
| Repository | `/home/shomonrobie/ct_93d5cdd` (CarbonTally V3 monorepo) |
| Branch | `p8-release-reconciled` |
| HEAD | `3fec874ca1f170ecb03e7daf69992dbf9e9cd18e` |
| Worktree state | **NOT CLEAN** — 222 porcelain entries |
| Live database probed | `ct_local_93d5cdd` at `127.0.0.1:5432` (demo-lab; **not production**) |
| DB access | Read-only `SELECT` only. Credentials sourced from `backend/.env`, never printed. |
| Changes made by this task | **NONE** |

`CURRENT FACT` **Nothing was reset, cleaned, stashed, committed, pushed or modified.** No
file other than this document was created.

### A.1 Pre-existing vs concurrently changed

`CURRENT FACT` Distinct attribution of the dirty tree:

| Category | Files | Attribution |
| --- | --- | --- |
| **Committed and UNMODIFIED** (pre-existing HEAD state) | `backend/api/v3_commercial.py`, `backend/api/v3_billing.py`, `backend/services/billing.py`, `backend/domain/billing.py`, `backend/data/billing.py`, `frontend/src/v3/customer/BillingPage.jsx`, `frontend/src/v3/ops/CommercialTab.jsx`, `supabase/migrations/20260824020000_d37_0_…sql`, `supabase/migrations/20260824030000_d37_master_…sql` | Last commits `9458067` (2026-08-25, "feat(v3): commit D20-D37 commercial platform release") and `daad396` (2026-09-11, release). **Not touched by Cline.** |
| **Concurrently modified** | `backend/api/manual_processing_admin.py`, `backend/api/manual_processing_auth.py`, `backend/domain/manual_processing.py`, `backend/data/manual_processing.py`, `backend/api/consultant_auth.py`, `backend/data/consultants.py`, `backend/api/v3_consultants.py`, `backend/api/router.py`, `frontend/src/v3/consultant/*`, `frontend/src/v3/__tests__/consultant-page.test.jsx` | **CT-CONSULTANT-PLATFORM-CLOSURE-01** (Cline) |
| **Untracked — concurrent work** | `backend/api/v3_manual_processing_coverage.py`, `backend/domain/consultant_entitlement.py`, `backend/domain/consultant_retention.py`, `backend/domain/relationship_access.py`, `backend/services/manual_processing_routing.py`, `backend/services/manual_processing_notifications.py`, `backend/tests/unit/api/test_ct_mp_sub_004_coverage_surfaces.py`, `backend/tests/unit/api/test_ct_mp_sub_003_consultant_coverage.py`, `frontend/src/v3/consultant/ManualProcessingCoverageTab.jsx` | **CT-MP-SUB-003 / CT-MP-SUB-004 / consultant closure** (Cline) |
| **Untracked — prior artefacts** | `docs/architecture/CT-SUB-001_…`, `docs/architecture/CT-UX-SUB-001_…`, `docs/architecture/CT-DISC-SUB-001-…`, `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md` | Prior PO/design work, present in the tree but not committed |

`CURRENT FACT` **No change made by this assessment is attributable to
CT-CONSULTANT-PLATFORM-CLOSURE-01, and no change made by that workstream is attributed to
this assessment.**

### A.2 Hindsight

`CURRENT FACT` A Hindsight `recall` for commercial/subscription/billing/coverage/credits/
storage/metering/entitlement terms was attempted against the project bank at
`http://localhost:8888`. The service responded successfully but returned **zero** results
for this topic. No durable project memory was retrieved or written by this assessment.

---

## Appendix B — Evidence Command Reference

Read-only commands used (reproducible; no credentials reproduced).

**Git baseline**
```bash
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1
git log -1 --format='%h %ad %s' --date=short -- <path>
```

**Repository sweeps**
```bash
grep -rn "billing_plans|billing_orders|billing_credit_ledger|billing_storage_usage|
          billing_payment_records|billing_commercial_config|billing_idempotency_keys" backend/
grep -rn "consultant_billing|consultant_subscription|stripe|Stripe" backend/
grep -nE "@router\.(get|post|delete|put)" backend/api/v3_commercial.py backend/api/v3_billing.py \
        backend/api/manual_processing_admin.py backend/api/v3_manual_processing_coverage.py
grep -nE "v3_commercial|v3_billing|v3_manual_processing_coverage|manual_processing_admin" backend/api/router.py
grep -c '^\s*def test_' <each commercial test file>
```

**Live database (read-only; credentials redacted)**
```bash
set -a; . ./backend/.env; set +a
psql "$DATABASE_URL" -X -q -t -A -F '|' -c "<SELECT …>"
```
Queries executed: `to_regclass` presence probes; `information_schema.columns` for
`consultant_profiles.organization_id`; row counts for all 12 billing/usage tables;
`billing_plans` full catalogue with `is_current`; `billing_commercial_config` current keys;
`organizations` `billing_mode` distribution; `pg_class.relrowsecurity` + `pg_policies`
counts; `information_schema.role_table_grants` for `anon`/`authenticated`/`service_role`;
`staff_roles` permission keys; `staff_roles` `can_manage_billing` presence;
`consultant_profiles` / `consultant_clients` / `manual_processing_grants` counts.

**Not performed (out of scope / no authorisation):** applying migrations, running the test
suite, frontend build, browser/E2E verification, any write to code, database, RLS or Git.

---

## Final Verdict

**COMMERCIAL-CURRENT-STATE-ASSESSED**

### Current maturity

`CURRENT FACT` CarbonTally possesses a **committed, versioned, server-authoritative,
provider-neutral, organization-scoped** commercial foundation (D37-0 → D37 → P6-BILL-1),
with a versioned plan catalogue, a single-active-relationship subscription state machine,
versioned commercial configuration, an append-only credit ledger with a derived balance, a
common order model, server-measured storage metering, provider-neutral payment records,
durable idempotency, a customer billing read surface, and a comprehensive admin API.

`CURRENT FACT` It is **inert in the running local environment**: 0 subscriptions, 0 ledger
rows, 0 orders, 0 payment records, 0 storage snapshots, and an admin surface that **no
staff identity can reach** because no role carries `can_manage_billing`.

`CURRENT FACT` It contains **no payment capability of any kind** — by explicit design.

### Biggest architectural gaps

1. `IMPLEMENTATION GAP` No payment abstraction, no checkout, no webhook ingestion, no
   invoice, no refund execution, no trial, no discount, no add-on, no proration, no tax.
2. `IMPLEMENTATION GAP` No self-service subscription surface for any role, and no
   "Subscription" navigation anywhere.
3. `IMPLEMENTATION GAP` Plan `features` values are unauthored — every plan carries
   `{"reports": true}` — so the entire entitlement model falls back to a legacy boolean.
4. `IMPLEMENTATION GAP` The stored limits (`processing_limits`, `team_member_limit`,
   `api_access`, `managed_processing_available`, storage capacity, consultant
   `client_capacity`) are **projected but not enforced**.
5. `IMPLEMENTATION GAP` Two entitlement resolvers read the same tables independently.
6. `IMPLEMENTATION GAP` Pricing is single-value and single-interval, and the public page
   is hard-coded and contradicts the catalogue's currency.

### Reusable components

`ARCHITECTURAL RECOMMENDATION` The plan catalogue and its versioning, the org-scoped
subscription state machine, the append-only credit ledger and its derived balance, the
common order model with immutable line items, the storage metering snapshots, the
provider-neutral payment-record shape, the durable idempotency primitive, the append-only
audit, the deny-by-default RLS posture, and the single entitlement resolver — all are
sound foundations to be **reused and extended**, not replaced.

### Duplicate / legacy concerns

- `CURRENT FACT` Duplicate plan versions (`starter` v2/v3, `business` v2/v3) produced by a
  non-idempotent D37 seed.
- `CURRENT FACT` `consultant_billing` is legacy: 0 rows, no application code references,
  Stripe-named columns, and conceptually at odds with org-scoped billing.
- `CURRENT FACT` Legacy `organizations.subscription_*` / `trial_*` / `billing_*` / `tax_rate`
  columns and `customer_subscriptions.plan` / `.status` / `stripe_*` are retained and
  write-revoked.
- `CURRENT FACT` Two vocabularies ("billing mode", "product mode", "coverage mode") claim
  the word "mode".
- `CURRENT FACT` The legacy `admin/` CRA carries no commercial surface; `/ops` is canonical.

### Required PO decisions

`PO DECISION REQUIRED` **D-1 … D-17** in §27, plus the carried-forward CT-SUB-001 §57 and
CT-UX-SUB-001 §64 lists. The most blocking are: **D-11** (which role owns commercial
configuration — without it the admin surface stays unreachable), **D-1** (catalogue
currency), **D-3** (payment provider and abstraction), **D-5** (which plan feature blocks
to author), **D-6** (whether the coverage migrations are ratified for application), and
**D-12** (open vs invitation-only registration).

### Recommended implementation sequence

`ARCHITECTURAL RECOMMENDATION` **Phase 0 (unblock the environment)** → Phase A (Commercial
Core) → Phase B (Platform Admin) → Phase C (Public) → Phase D (Consultant) → Phase E
(Direct Organisation) → Phase F (Consultant-managed Organisations) → Phase G (Integration)
→ Phase H (Independent verification). Phase 0 is a prerequisite, not an optional extra.

### Explicit non-claims

`CURRENT FACT` This assessment makes **no** implementation claim, **no** acceptance
verdict, and **no** production-readiness claim. It asserts only what was verified against
the current source, the current live database, and the current repository documents.

---

**CT-COMMERCIAL-SUBSCRIPTION-INDEPENDENT-ASSESSMENT-01 — COMMERCIAL-CURRENT-STATE-ASSESSED**

*Report path: `docs/architecture/CT-COMMERCIAL-SUBSCRIPTION-INDEPENDENT-ASSESSMENT-01.md`*
