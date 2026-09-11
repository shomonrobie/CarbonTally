# CarbonTally P6-BILL-0 — Commercial / Billing Architecture Reconciliation

**Status:** READ-ONLY — no implementation, no migration, no commit/push.
**Date:** 2026-09-04
**Authority:** `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`
**Rule 5 report:** No code changes were underway from an earlier task that this
reconciliation would disturb; this session changed only temporary probes under
`/tmp` and this report. The repo's pre-existing working-tree state (in-flight
Phase 4–6 work, uncommitted) was not touched.

---

## 1. Executive Verdict

### `READY WITH PO DECISIONS`

The D37/D37-0 provider-neutral, server-authoritative commercial foundation is
**real, active and well aligned** with V1.3 §21 (billing), §31.3
(CT-BILL-001…003) and the Direct Merchant Architecture. Everything commercial
is organisation-scoped, deny-by-default in RLS, audited and versioned — so
D-7 (client organisation owns the processing entitlement) is satisfied **by
construction for any org that has an active subscription**. Consultant
commercial packaging, org→consultant additive upgrade binding, configurable
registration modes and payment-provider execution are **NOT CURRENTLY
IMPLEMENTED**; several draft commercial documents still describe Consultant
plans with pooled credits that are superseded by D-7 (draft ≠ final). The
genuinely unresolved items are PO decisions, not architecture conflicts.

---

## 2. Current Architecture (implemented reality)

- **Server-authoritative commercial core (D37-0, 2026-08-24):** versioned
  plan catalogue (`billing_plans`), versioned commercial rules
  (`billing_commercial_config`), append-only credit ledger
  (`billing_credit_ledger`), per-org `billing_mode` (CREDIT | STANDARD).
  All writes service-role only; authenticated INSERT/UPDATE/DELETE revoked on
  `usage_tracking`, `customer_subscriptions`, `consultant_billing`,
  `organizations` (D37-0 P0 lockdown).
- **Master commercial layer (D37, 2026-08-24):** subscription lifecycle on
  `customer_subscriptions` (plan_code/plan_version/billing_mode/
  lifecycle_status/idempotency_key + one-active-per-org unique index), common
  order model (`billing_orders`), storage metering, provider-neutral payment
  records (`billing_payment_records`), durable idempotency
  (`billing_idempotency_keys`).
- **Consumption hook:** `BillingService.charge_processing(organization_id, …)`
  is called only from the customer-approval route
  (`v3_processing_workflow.py` `customer_review_item`) against
  `batch.organization_id`, idempotent per item. Pre-commercial orgs (no active
  subscription) return `{mode:"no_subscription", allowed:True, charged:False}` —
  billing is not enforced for unsubscribed orgs.
- **Admin control surface:** `v3_commercial.py` (internal staff + real
  `can_manage_billing`) configures plans/config, activates/changes
  subscriptions, grants/adjusts/reverses/refunds/rolls over credits, completes
  orders, reads ledger/storage/payments/entitlement.
- **Customer read/request surface:** `v3_billing.py` (org members) — view
  entitlement/credits/storage/orders/payments; create+approve Assisted and
  Managed orders (server-priced).
- **No payment provider is integrated** (no Stripe/PayPal code in the source
  tree; `record_payment_intent` writes a `pending` record only).
- **Registration:** open self-service org creation exists (`POST
  /api/v3/organizations`, D35, any authenticated user with no membership,
  duplicate-discovery guard). Org-member invitations exist (7-day expiry,
  org-admin only). There is **no configurable platform registration mode**
  (no `INVITATION_ONLY`/`OPEN_REGISTRATION` flag anywhere).
- **Consultant surface:** profiles/firm membership/client grants exist;
  `consultant_billing` is a dormant legacy table (0 rows, no code references,
  authenticated writes revoked).

**Runtime evidence (read-only DB probe):** `billing_plans` 6 rows
(starter/professional/business/enterprise only — no consultant plan codes;
seed shows GBP→USD version drift: `starter` v1 £0 → v2 $49, `business` v1 £299 →
v2 $399 — provisional). `customer_subscriptions` 0, `billing_credit_ledger` 0,
`billing_orders` 0, `billing_payment_records` 0, `billing_storage_usage` 0,
`billing_idempotency_keys` 0, `consultant_billing` 0. `organizations` 975,
`consultant_profiles` 55, `consultant_firm_members` 54, `consultant_clients`
917, `user_invitations` 8, `beta_access_codes` 0. Commercial enforcement is
therefore effectively dormant in the current database.

## 3. Database Model (relevant tables/columns and roles)

| Table (migration) | Role | Key columns |
|---|---|---|
| `billing_plans` (D37-0) | Versioned plan catalogue; server-authoritative price/entitlement | `plan_code`, `version`, `price`, `currency`, `billing_interval`, `included_credits`, `included_storage_bytes`, `team_member_limit`, `processing_limits`, `features`, `billing_mode`, `assisted/managed/api` flags, `is_active`, `effective_from/to` |
| `billing_commercial_config` (D37-0) | Versioned commercial rules | `config_key`, `config_value`, `version`, `effective_from/to` — keys: `default_billing_mode`, `credit_rules`, `structured_data_bands`, `storage`, `assisted_pricing`, `credit_policy`, `standard_allowance` |
| `billing_credit_ledger` (D37-0) | **Append-only** org-scoped credit ledger (balance = SUM) | `organization_id` (FK), `entry_type` (grant/consume/adjustment/rollover/emergency_allowance/refund/reversal), `credit_delta`, `source`, `plan_code/version`, `subscription_id`, `external_reference` (idempotent) |
| `customer_subscriptions` (init + D37) | Org subscription lifecycle | `organization_id`, legacy `plan/status/stripe_*` (kept, legacy), D37: `plan_code`, `plan_version`, `billing_mode`, `lifecycle_status` (pending/trial/active/past_due/suspended/cancelled/expired), `current_period_*`, `idempotency_key`; one active per org (partial unique index) |
| `billing_orders` (D37) | Common order model (automated/assisted/managed/storage) | `organization_id`, `order_type`, `status`, `items` (immutable price snapshot), `total_amount`, `currency`, `plan_code/version`, `config_version`, `idempotency_key`, `approved_by/at`, `created_by` |
| `billing_storage_usage` (D37) | Storage metering snapshots | `organization_id`, `usage_bytes`, `included_bytes`, `measured_at` |
| `billing_payment_records` (D37) | Provider-neutral payment records | `organization_id`, `provider`, `amount`, `status` (pending/confirmed/failed/refunded), `provider_transaction_ref`, `order_id`, `subscription_id`, `idempotency_key` |
| `billing_idempotency_keys` (D37) | Durable idempotency | `key`, `operation`, `entity_type/id`, `request_hash` |
| `organizations.billing_mode` (D37-0) | Per-org CREDIT/STANDARD mode | default from config at creation; authenticated writes revoked |
| `usage_tracking` (init) | STANDARD-mode monthly usage | `organization_id`, `usage_month`, counters (ai_files_processed etc.) |
| `consultant_profiles` (init) | Firm identity (one per consultant) | `id`, `user_id`, `company_name`, `default_plan`, `partner_status/tier`, branding/white-label fields |
| `consultant_firm_members` (init) | Firm membership + real permission flags | `firm_id`, `user_id`, `role`, `can_manage_clients/can_upload_documents/can_generate_reports/can_manage_team` (default FALSE), `invited_at/joined_at`, `role_id`, `permissions` |
| `consultant_clients` (init + D15/D19/D27) | Firm↔org grant (the access key) | `consultant_id`, `organization_id`, `status` (only `active` grants access), lifecycle provenance (`suspended_at/ended_at/ended_by`), `created_by` |
| `consultant_billing` (init + rc2) | **Legacy/dormant** consultant billing | `consultant_id`, `client_id`, `plan`, credit counters; 0 rows; no code references; authenticated writes revoked (D37-0) |
| `user_invitations` (init) | Org membership invitations | `email`, `role_id`, `organization_id`, `token` UNIQUE, `status`, `expires_at` (7-day pattern) |
| `product_categories` / `beta_access_codes` / `waitlist` | Legacy catalogue/registration artifacts | not referenced by D37 |

Notes: consultant-firm ↔ subscription has **no active table** (the dormant
`consultant_billing` is disconnected); there is **no organisation↔firm binding**
column/table; there is **no registration-mode configuration table**; there is
**no client-capacity or active-client-count column** on consultant plans.


## 4. Backend/API Model (actual services/routes)

| Component | What it does |
|---|---|
| `services/billing.py` — `BillingService` | Server-authoritative commercial operations: `get_entitlement(org)` (resolves org + active subscription + plan version + config + ledger balance), `grant_credits`, `consume_credits` (idempotent; emergency allowance path), `rollover`, `adjust/reverse/refund_credits`, `activate_subscription`, `change_subscription_status`, `create_order`, `estimate_assisted_order` (config `assisted_pricing`), `approve/complete/cancel_order`, `meter_storage`, `charge_processing(org, job)` (complexity/structured-data units from config), `record_payment_intent` |
| `api/v3_billing.py` | Org-scoped customer surface: `GET /billing/me` (+credits/orders/payments/storage), `POST /billing/orders/assisted` (server-priced), `POST /billing/managed/orders`, `POST /billing/orders/{id}/approve|cancel` — all `require_org_member` + org context; no client-supplied prices |
| `api/v3_commercial.py` | Admin surface (internal staff + `can_manage_billing`): config GET/PUT (versioned), plan create/PUT (new version), subscription activate/status, credit grant/adjust/reverse/refund/rollover, order list/complete, storage/payments reads, `GET /commercial/entitlement/{org}` |
| `api/v3_processing_workflow.py` `customer_review_item` | The only production caller of `charge_processing` — at **customer approval**, charging `batch.organization_id` (idempotency key `charge:item:{item_id}`) |
| `api/v3_organizations.py` | Self-service org creation (D35, any authenticated non-member), org members CRUD, invitations (create/list/revoke, 7-day expiry, org-admin), facilities/assets |
| `api/v3_consultants.py` | Consultant profile (`POST /me` open), team members (`POST /me/team` gated by `can_manage_team`), clients (`POST /me/clients` gated by `can_manage_clients`, arbitrary org link), customers (`POST /me/customers` creates new org + active grant), client workspace data |
| `api/consultant_auth.py` | `require_consultant` / `ensure_consultant_org_access` (active grant D15) / `ensure_consultant_permission` (real `can_*` flags) |
| `api/v3_whitelabel.py` + branding | White-label/branding surface (per firm profile) — feature gating vs plan entitlement is NOT connected to billing |

Registration routes: auth is Supabase Auth (external); the only server-side
"registration" business logic is org creation and invitations. **There is no
product/plan purchase, checkout, or subscription-request endpoint on the
customer or consultant surface.** Subscriptions are activated by CarbonTally
admin only (`POST /api/v3/commercial/subscriptions`).


## 5. Frontend Model (billing/subscription/registration UI)

- `frontend/src/v3/customer/BillingPage.jsx` — D37 customer surface:
  renders entitlement/plan/subscription/credits/storage/orders/payments read
  from `/api/v3/billing/*`; submits Assisted/Managed order **requests** with
  only complexity/quantity + idempotency keys (**no client-supplied prices** —
  verified contract: `AssistedEstimateLine` has no price field; Managed order
  sends `quantity_documents` only). Plan price is displayed from server data.
- `frontend/src/v3/ops/CommercialTab.jsx` — D37-0 admin tab (staff +
  `can_manage_billing`): plan/config editors, subscription activation/status,
  credit grant/adjust/reverse/refund/rollover, orders/storage/payments ledger
  views.
- `frontend/src/PricingPage.jsx`, public `ServicesPage/ProcessingPage` — static
  marketing pricing pages (no checkout).
- `frontend/src/SelfServiceSignup.jsx` + `OnboardingPage.jsx` — D35 customer
  self-registration/onboarding flow calling org creation; `frontend/src/v3/
  consultant/ConsultantPage.jsx` — consultant workspace (no billing UI).
- **No frontend checkout / plan-selection / payment flow exists.** The
  frontend never computes or submits totals, discounts, tax, or entitlement.
  No frontend reference to `consultant_billing`.

## 6. Commercial Authority Analysis (where authoritative values originate)

- **Server-side only.** Prices, credit rules, storage rates, assisted-pricing,
  plan entitlements and billing modes all resolve from DB tables
  (`billing_plans`, `billing_commercial_config`) read by `BillingService`
  (`get_entitlement`, `_required_units`, `classify_document`,
  `estimate_assisted_order`). Every commercial mutation is
  service-role + idempotency-key + audit. Authenticated direct writes to the
  commercial tables are revoked (deny-by-default RLS; no authenticated
  policies on D37-0/D37 tables).
- The **only** customer-entered commercial inputs are order *shape* fields
  (complexity class, quantities, title); unit prices come from config, and
  client-created Assisted estimates are server-priced before approval.
- Plan/pricing data is **configurable** by CarbonTally admin but the seed
  data is provisional (starter v1 £0/v2 $49; business v1 £299/v2 $399; 0 active
  subscriptions; ledger unused) — i.e. **no public pricing is frozen**.

## 7. Registration Analysis

- **Open self-registration exists for customers**: any authenticated user with
  no membership may create an organisation and become OWNER (D35,
  `v3_organizations.py`), gated by duplicate discovery. Restricted to one org
  per user. Creates org + owner membership transactionally, assigns the
  configured default `billing_mode`; no subscription is auto-created.
- **Consultant self-registration exists backend-side** (`POST /consultants/me`)
  but no product UI calls it; no client access is granted by registration.
- Org membership is invitation-based (org admin, token + 7-day expiry,
  revocation) — the closest existing pattern to a configurable closed mode.
- **Configurable platform registration mode (INVITATION_ONLY vs
  OPEN_REGISTRATION) is NOT CURRENTLY IMPLEMENTED** (no setting, no config key,
  no admin surface). Representable cleanly: it would fit
  `billing_commercial_config` or a dedicated admin config flag checked at
  signup/org-creation; but deciding whether Auth signup itself is gated
  (Supabase external config) vs only org/consultant provisioning is a PO item.
- Invitation infrastructure (`user_invitations`, token/expiry/status) exists
  org-scoped and is reusable for consultant firm membership (P6-1B).

## 8. Consultant Upgrade Analysis (existing org → Consultant)

- **Additive upgrade is feasible without data mutation.** The org model,
  subscription, ledger, orders, provenance and member tables are all
  organisation-scoped and independent of the consultant model. An existing
  org could acquire "consultant capability" as an additive plan/feature
  entitlement (`billing_plans.features` JSONB already supports feature flags;
  `customer_subscriptions` is org-scoped).
- **What is missing (NOT CURRENTLY IMPLEMENTED):**
  - an organisation↔consultant-firm binding (no table/column maps an
    organisation to a `consultant_profiles`/firm identity it operates);
  - consultant-capability flags/features in plans and entitlement evaluation;
  - any consultant plan record in `billing_plans` (probe: none);
  - logic granting an org's users consultant workspace access based on the
    org's subscription entitlement.
- No duplicate-org conversion exists in the current model precisely because
  the two models are separate; adding a binding is additive. D-C decision
  (owner-user-based firm vs org↔firm binding) still required (see §16).


## 9. Consultant Client Model

- Client organisations are first-class `organizations` rows; the Consultant
  relationship is the separate `consultant_clients` grant
  (`consultant_id` = firm profile, `organization_id`, `status`). **Client
  relationship is distinct from subscription ownership** — no subscription
  column/table keys to a consultant.
- Consultant-created customers: `POST /consultants/me/customers` creates a new
  organisation + owner identity + active grant (PO Decision 3 / CON-1,
  CT-CONSULT-002); `created_by` on `consultant_clients` is available but not
  set by `add_client` (audit gap).
- Arbitrary existing-org linking: `POST /consultants/me/clients` currently
  allows any `can_manage_clients` member to link **any** `organization_id`
  with no customer/CT confirmation (violates CT-CONSULT-003 as-is; needs the
  controlled-engagement mechanism — a P6-1C/PO item, already flagged in the
  P6-0.1 report).
- Independence after termination: relationship ends via D19 soft lifecycle
  (`status=ended` + provenance); the client org/data/history remain; the
  former client can operate direct (CT-CONSULT-004) — the org model already
  supports this (org access is membership/RLS-based, independent of the
  consultant grant). Runtime evidence: 917 `consultant_clients` rows vs 975
  organisations — the two models are already independent in data.

## 10. Credit Ownership Analysis — D-7

Answers to the nine questions:

1. **Who owns processing credits today?** The **organisation**
   (`billing_credit_ledger.organization_id`, `usage_tracking.organization_id`,
   `customer_subscriptions.organization_id`). No credit object is
   consultant/firm-scoped in the active implementation.
2. **Can credits be associated with an organisation?** Yes — every D37/D37-0
   credit object is organisation-keyed and consumed against
   `organizations.billing_mode`.
3. **Can a Consultant consume credits belonging to a client?** There is **no
   consultant-billing code path at all** in the active implementation; the only
   consumption hook (`charge_processing`) is called on **customer approval**
   with `batch.organization_id` — i.e. the org that owns the work (the client
   org, even when a consultant uploaded the document). A consultant does not
   consume anything today.
4. **Can one client's credits be consumed for another client?** No — ledger,
   subscription, usage and orders are all per-organisation; there is no pool.
5. **Where is usage recorded?** `billing_credit_ledger` (consume entries,
   CREDIT mode), `usage_tracking` (STANDARD mode) — both org-scoped; storage
   in `billing_storage_usage`.
6. **How are credits deducted?** Append-only ledger `consume` entries via
   `BillingService.consume_credits`/`charge_processing`; balance is derived
   (SUM); idempotent per item (`charge:item:{id}`); emergency allowance
   configurable. No mutable balance column.
7. **Are Consultant subscription credits currently modeled?** **NO** — no
   consultant plan record, no consultant subscription, and the dormant
   `consultant_billing` table has 0 rows and no code references.
8. **Do draft docs include Consultant credits, and how does that interact
   with D-7?** Yes — draft documents describe Consultant/Consultant-Business
   plans **with pooled processing credits/month** and per-client overage
   (e.g. `CarbonTally_V3_Draft_Pricing_Strategy…` §8 "1,000 processing
   credits/month"; `Pricing_Comparison_Baseline_v2` §13 and its "NOT FINAL"
   price book §31; Assisted/Managed spec §30 table). These drafts **conflict
   with D-7** (client org owns the entitlement) if read as firm-pooled credits
   automatically usable across clients. Per Rule 2 they are drafts, not final;
   per Blueprint §31.3 they are superseded by CT-BILL-001…003 + D-7. A PO
   decision is required on the consultant commercial packaging that resolves
   this (see §16, PO-D7).
9. **Is an explicit PO decision required?** Yes — see §16 (PO-D7) and note
   the current runtime default: orgs with **no active subscription** are not
   charged at all (`no_subscription → allowed`), so D-7 enforcement only
   exists once org subscriptions exist; if a client org is unsubscribed and a
   Consultant's own (future) plan included credits, current code would leave
   the work uncharged rather than consume either pool.

**Bottom line:** the D37 foundation is already D-7-aligned **per organisation**;
what is missing is the consultant plan packaging decision and the rule for
work performed for an unsubscribed/under-subscribed client org.


## 11. Payment Provider Analysis

- **Provider:** NONE integrated. No Stripe/PayPal/etc. code in the project
  source (search over `backend/api|data|domain|services` finds only comments
  in `domain/billing.py`/`data/billing.py` describing the design as
  provider-neutral and future-adapters). The Direct Merchant Architecture
  names Stripe/PayPal as **candidates only**; MoR providers explicitly NOT
  selected; final provider NOT selected.
- **Provider IDs stored:** legacy `customer_subscriptions.stripe_*` columns
  remain (documented as legacy, unused); active D37 fields are
  `billing_payment_records.provider` / `provider_transaction_ref`
  (provider-neutral).
- **Payment status:** `billing_payment_records.status`
  (pending/confirmed/failed/refunded). Only `pending` records can be created
  today (`record_payment_intent`); no confirmation path exists.
- **Webhooks/callbacks:** NOT CURRENTLY IMPLEMENTED.
- **Billing state ownership:** CarbonTally-owned and server-authoritative
  (orders, subscriptions, ledger, entitlement all in CarbonTally DB; payment
  records are references, never the ledger — matches Direct Merchant §19
  "Payment vs Entitlement").
- **Idempotency:** durable `billing_idempotency_keys` + unique refs on
  ledger/orders — PASS for the application-level commercial mutations.
- **Provider switching:** architecturally possible (provider-neutral tables
  and adapter design); nothing to switch today.

## 12. Security / Authorization Analysis (separation)

| Concept | Implemented as | Separation evidence |
|---|---|---|
| Registration | Supabase Auth + D35 org creation + invitations | A signed-in identity is not an org member or consultant until a separate act creates membership |
| Subscription / entitlement | org-scoped `customer_subscriptions` + plans/config (server-authoritative) | Admin-activated only; authenticated cannot write |
| Authorization | org membership/RLS + role checks (`require_org_admin`, `require_org_member`) + staff permissions (`can_manage_billing`) | Per-request server checks; RLS is never bypassed |
| Client data access (consultant) | `consultant_clients.status='active'` grant + `ensure_consultant_org_access` + `is_org_consultant` RLS | Independent of any plan flag; a plan/subscription never grants org access |
| Processing credits | org-scoped ledger/usage consumed at customer approval on `batch.organization_id` | Independent of who uploaded the document (customer or consultant) |

The five concepts are **not collapsed** into `is_consultant` or
`subscription=consultant` — there is no such boolean or enum in the schema.
One gap: entitlement is not yet consulted on the **consultant** surface at all
(there is no consultant entitlement to check) and processing-capability checks
(plan flags → action availability, e.g. upload/extract) are NOT enforced
anywhere today because subscriptions are dormant (`no_subscription → allowed`).


## 13. Legacy Billing Analysis

- `consultant_billing` (init schema, `rc2_schema.sql` added `currency`) —
  legacy consultant billing table. **Where:** schema only. **What it appears
  to do:** per-firm plan label + credit counters (auto/manual extraction,
  per-client rows). **Referenced:** NO backend or frontend source reference
  exists (search: empty outside tests/venv). **Active:** NO — 0 rows;
  authenticated INSERT/UPDATE/DELETE **revoked** (D37-0 P0 lockdown). **Conflicts
  with current architecture:** its semantics (firm-scoped credits pooled
  against client work) contradict D-7 if ever reactivated; it has no RLS
  integration with D37 ledger/idempotency. **Recommendation (documented only,
  not executed):** do not delete, reactivate, or refactor; if consultant
  commercial packaging is later implemented, replace its semantics with the
  org-scoped D37 ledger per D-7 rather than reviving this table.
- `customer_subscriptions` legacy columns (`plan` free-text, `status` legacy
  CHECK vocabulary, `stripe_*`) — kept and documented as legacy; D37 fields
  are authoritative. Same handling recommendation.
- `product_categories`, `beta_access_codes`, `waitlist`, legacy
  `customer_documents`/`routes/*` billing mentions — historical/legacy,
  not part of the active commercial surface.
- Draft pricing docs (§8 above) are **drafts**, explicitly marked "NOT FINAL"
  in `Pricing_Comparison_Baseline_v2` §31 and "Working Draft" in the strategy
  document; they are evidence/history for packaging, not authoritative pricing.

## 14. Invariant Matrix

| Invariant | Status | Evidence | Risk |
|---|---|---|---|
| BILL-SEC-001 — Server-side commercial authority | **PASS** (scoped to the D37 customer surface) | All prices/credits/rules/subscriptions resolve server-side from `billing_plans`/`billing_commercial_config`/ledger (`services/billing.py`); authenticated direct writes revoked; deny-by-default RLS on all D37 tables | Nil for current surface. New checkout must preserve server-priced order creation; consultant commercial surface must use the same service |
| BILL-SEC-002 — Client price integrity | **PASS** (no checkout exists) | Contracts carry no price/total/discount/tax fields (`v3_billing.py` `AssistedEstimate`/`ManagedOrder`/`OrderAction` = `extra="forbid"`); Managed items forced to quoted 0 line; server sets `total_amount` | Checkout must NEVER accept client totals — enforce via server-side amount derivation + signature/quote refs when built |
| BILL-SEC-003 — Entitlement integrity | **PARTIAL** | Entitlement evaluation is server-side and plan-gated where used; but entitlement is **not enforced on any product action yet** (0 subscriptions; `charge_processing` returns `no_subscription → allowed`; no action-level capability gating on upload/extract; consultant surface has no entitlement checks) | When subscriptions go live, unsubscribed orgs would silently process for free; capability gating must be added; plan features must never grant resource authorization |
| BILL-SEC-004 — Administrative configuration | **PASS** | `v3_commercial.py` configures plans/rules/modes/credits/subscriptions; versioned + audited + gated by internal staff `can_manage_billing`; admin configuration cannot write authorization/RLS surfaces | Ensure consultant commercial config (CT-BILL-003) is added to this same surface, not hard-coded; keep commercial config strictly separate from org-grant/RLS config |


## 15. Required Changes

### Implementation-ready (no PO decision needed; additive, aligned with V1.3)
1. Add consultant/product capability concepts to the existing versioned plan
   catalogue and entitlement evaluation (feature flags already exist in
   `billing_plans.features`/`processing_limits`; entitlement already returns a
   dict) — purely additive.
2. Wire processing-action entitlement checks (upload/extract/calculate) to
   `BillingService.get_entitlement(org)` server-side (idempotent, audit);
   keep the D7 owner-org rule.
3. Set `consultant_clients.created_by` on `add_client`/`create_customer`
   (audit provenance).
4. Add org↔consultant-firm binding (additive table or org column) once the
   mapping model is chosen (needs D-C decision first — see §16).
5. Fix seeded plan catalogue hygiene (GBP/USD drift, £0/v1-vs-$/v2) as data
   configuration when pricing is ratified (implementation, after PO pricing).
6. Registration-mode flag (INVITATION_ONLY / OPEN_REGISTRATION) configurable
   by admin — needs PO decision D-A on scope (Auth signup vs provisioning).

### Requiring PO decision
See §16 — D-A registration-mode scope, PO-D7 consultant credit packaging
(D-7 interaction), D-C org→consultant binding, D-D engagement authority for
pre-existing orgs, and final pricing/plans/catalogue + provider selection.

### Architecture conflicts
**None found.** Draft pricing documents conflict with D-7 only in *packaging
semantics* (draft), and legacy `consultant_billing` semantics conflict with
D-7 if revived — neither is an active-code conflict. No Gate 3–6 decision is
weakened by anything found.

## 16. Explicit PO Decisions Required

Genuinely unresolvable from V1.3 + ratified decisions alone:

- **PO-D7 — Consultant plan credit packaging.** If a Consultant plan includes
  credits, what do they mean given D-7 (client org owns the processing
  entitlement)? Options: (a) consultant plans carry no processing credits —
  clients buy/own credits; (b) consultant plan credits are a *reseller/
  pass-through allowance* billable to the client org on consumption
  (org-scoped ledger credited on purchase with the client org as the
  consuming org); (c) a firm-level non-processing "platform" credit concept
  (careful — conflicts with D-7 wording). Also: what happens to work for a
  client org **without an active subscription** (current default: free)?
- **D-A — Registration modes.** Where is INVITATION_ONLY / OPEN_REGISTRATION
  enforced (Supabase Auth signup gate is external config; server gate at org/
  consultant provisioning?) and does the mode apply to customers and
  consultants separately?
- **D-C — Organisation → Consultant upgrade binding.** Owner-user-based firm
  identity vs explicit organisation↔firm binding table; which org users gain
  consultant workspace access under the upgrade.
- **D-D — Engagement authority for existing client organisations.** Who
  authorizes a consultant linking a pre-existing org (customer owner
  confirmation / CT confirmation / engagement invite), plus confirmation that
  consultant-created customers (PO Decision 3) keep automatic active grants.
- **Final consultant commercial catalogue and pricing** (CT-BILL-003 says
  admin-configurable; the actual codes/limits/prices need PO sign-off — draft
  documents are explicitly NOT FINAL).

## 17. Recommended Next Workstream

**P6-BILL-1 — "Entitlement enforcement + consultant commercial scaffolding"
(bounded, additive, server-side):**
1. PO answers PO-D7, D-A, D-C, D-D (small decision sheet).
2. Implement: org↔firm binding (per D-C); consultant capability flag(s) as a
   plan feature and server-side entitlement checks; enforce
   `charge_processing` org-ownership (already true) with explicit
   no-subscription behaviour per PO-D7; add registration-mode config key +
   admin toggle; record `created_by` on consultant client grants.
3. Tests: entitlement allow/deny matrix, credit owner isolation
   (client A vs client B), unsubscribed-org rule, admin-config versioning.
4. No payment provider, no checkout, no public pricing yet.

This keeps the smallest correct scope: it converts the ratified model into
server-authoritative enforcement without committing to a payment provider,
final prices, or a full Consultant UI (P6-6).

---

## Final confirmation

**READ-ONLY compliance:** no application code, schema, migration, RLS policy,
API route, frontend behaviour, billing/subscription/registration logic was
modified; legacy code was neither deleted nor revived; no checkout/pricing/
provider work implemented. No commit, no push. Only this report and temporary
`/tmp` probes were created.

