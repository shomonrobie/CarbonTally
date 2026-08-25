# CarbonTally V3 — D37-0 Billing Security Remediation & Configurable Subscription Foundation

**Phase:** D37-0 — the first implementation phase after the D36 Billing &
Commercial Architecture Audit. Ends in a **HARD STOP** before any
payment-provider integration.

**Date:** 2026-08-24 · **State:** COMPLETE, HARD STOP.

## 1. Executive summary

D37-0 closes the D36 **P0 billing-security defect** (authenticated customers
could mutate authoritative billing state through PostgREST) and establishes a
**configurable, provider-neutral subscription/commercial foundation** with
Admin Dashboard configuration, versioned/auditable rules and an append-only
credit ledger. The approach followed the project discipline
**reuse → extend → replace only when justified**:

- **REUSED:** the `customer_subscriptions` / `usage_tracking` /
  `consultant_billing` tables (rows/IDs untouched), the tenant/RLS organisation
  boundary, D35 self-service onboarding, D33 evidence, the staff authorization
  chain, the append-only audit trail, the ops frontend conventions.
- **EXTENDED:** `organizations.billing_mode` (per-customer CREDIT/STANDARD),
  org profile serialization, the staff permission vocabulary
  (`can_manage_billing`), and the org profile editable-field set
  (`tax_rate` removed — authoritative tax fields are no longer customer-set).
- **REPLACED:** only the **defective** direct-PostgREST write path to billing
  state (that *was* the vulnerability); the legitimate trusted/API paths are
  preserved.
- **ADDED:** `billing_plans` (versioned), `billing_commercial_config`
  (versioned key/value rules), `billing_credit_ledger` (append-only), the
  `/api/v3/commercial/*` admin surface, and the **Commercial** tab in the
  existing Internal Operations hub.

**Test record:** backend unit **1039 passed** (+19), RLS **23 passed** (+8),
frontend **23 passed** (+2), production build **OK**, live verification
**26/26 passed** against the real stack; all fixtures cleaned.

## 2. Existing subscription architecture (before D37-0)

### 2.1 Database
- `customer_subscriptions` — org-scoped subscription row (Stripe-named
  columns: `stripe_subscription_id`, `stripe_customer_id`, `stripe_price_id`),
  schema-only (no repository, no API, no UI).
- `usage_tracking` — org-scoped per-month rollup (AI files, batch files, manual
  pages, reports, storage), schema-only.
- `consultant_billing` — consultant-scoped billing row (Stripe-named), **0 RLS
  policies** (deny-by-default, hence unusable).
- `organizations.subscription_status / subscription_tier / subscription_id /
  trial_start_date / trial_end_date / tax_rate` — denormalised billing/tax
  columns on the tenancy anchor.
- **No plan catalogue, no price book, no billing mode, no credit ledger, no
  entitlement, no commercial configuration versioning.**

### 2.2 Backend / frontend / security
- No billing repositories, no billing API routes, no billing service, no
  metering writes, no background jobs, no webhooks.
- Frontend: no subscription/plan/billing UI. The customer org page exposes
  `tax_rate` in the profile editor.
- Security: the D36 P0 defect (below).

## 3. Existing billing architecture inventory (D36 recap, verified)
- Billing tables are schema-only and **provider-coupled** (Stripe column
  names), `consultant_billing` has no policies (unusable), there is no
  billing service/API/UI, no entitlement enforcement, no complexity
  classifier, no credit ledger, no price book, no `billing_mode`.
- The D36 report classified the org tenancy, processing pipeline, D32 storage,
  D33 evidence, audit/events as **reusable**; the billing layer as effectively
  **greenfield**.

## 4. P0 security root cause
The `authenticated` role held **table-level** `INSERT/UPDATE/DELETE` grants on
`usage_tracking` and `customer_subscriptions` and table-level `UPDATE` on
`organizations`, combined with tenant INSERT/UPDATE/DELETE RLS policies and the
`organizations_org_update` policy. PostgREST therefore allowed a customer's
browser to:

- insert/update/delete their own usage rows (self-metering),
- create/modify their own subscription row (plan, status, limits),
- update `organizations.subscription_*`, `trial_*` and `tax_rate` (trial
  extension, entitlement, tax authority).

A **bare column-level REVOKE cannot override a table-level grant in
PostgreSQL** (verified live during D37-0: the column REVOKE did not take
effect). The authoritative fix therefore revokes the table-level grants.

## 5. P0 remediation (exact RLS/grant changes)
Migration `supabase/migrations/20260824020000_d37_0_billing_security_and_configurable_subscription.sql`:

1. `DROP POLICY` the tenant INSERT/UPDATE/DELETE policies on
   `usage_tracking` and `customer_subscriptions` (SELECT policies retained).
2. `REVOKE INSERT, UPDATE, DELETE ON usage_tracking, customer_subscriptions,
   consultant_billing FROM authenticated;`
3. `REVOKE UPDATE, INSERT, DELETE ON organizations FROM authenticated;` —
   closes the WHOLE org row for authenticated writes (the app updates orgs via
   the trusted API; no frontend path writes organizations directly).
4. `GRANT ALL ON billing_plans, billing_commercial_config,
   billing_credit_ledger TO service_role;` — trusted server/service paths only;
   `anon`/`authenticated`/consultant/entity staff have **no** grants
   (deny-by-default + RLS disabled policies).
5. `organizations.billing_mode TEXT CHECK (billing_mode IN
   ('CREDIT','STANDARD'))` — added after the grants block, backfilled to the
   seeded default **once**.

Preserved legitimate paths: the trusted CarbonTally API runs as the table
owner (service pool) and remains unaffected; the service-role PostgREST path
is granted on the new foundation tables.

## 6. Schema changes (exact)
| Object | Change |
|---|---|
| `organizations` | + `billing_mode` column + CHECK (CREDIT/STANDARD) |
| `billing_plans` | NEW versioned plan catalogue (plan_code+version unique; effective_from/to; price, currency, interval, included_credits, storage, team limit, processing_limits JSONB, features JSONB, mode, assisted/managed/api flags, active) |
| `billing_commercial_config` | NEW versioned key/value rules (config_key+version unique; current = effective_to IS NULL) |
| `billing_credit_ledger` | NEW append-only ledger (org FK cascade, entry_type CHECK, delta ≠ 0, source, plan refs, external_reference, unique partial idempotency index) |
| `staff_roles.admin` | permissions += `can_manage_billing: true` |

Seed data (provisional, Admin-configurable): Starter (£0/10cr), Professional
(£149/500cr), Business (£299/1500cr), Enterprise (quoted); config keys
`default_billing_mode` (CREDIT), `credit_rules` (simple 1 / standard 2 /
complex 4 / exceptional-quoted), `structured_data_bands` (≤1k=1 … >1M=custom),
`storage` (included 0, rate NULL, unit GB, 100% markup intent),
`assisted_pricing` (simple 0.99 / standard 1.99 / complex 3.99 / exceptional
quote), `credit_policy` (rollover enabled, emergency allowance 10%),
`standard_allowance` (TBD).

## 7. RLS changes (exact)
- Legacy billing tables: write policies dropped; authenticated write grants
  removed; SELECT kept.
- `organizations`: authenticated INSERT/UPDATE/DELETE revoked.
- New billing tables: `ENABLE ROW LEVEL SECURITY` with **no** policies and no
  `authenticated` grants — deny-by-default; `service_role` granted ALL.

## 8. API changes (exact)
`backend/api/v3_commercial.py` (prefix `/api/v3/commercial`, registered in
`api/router.py`). Every endpoint: `require_staff()` + `require_internal_staff`
+ `ensure_staff_permission(context, "can_manage_billing")` (D37-0 §24).

- `GET /overview` — current config + plans + default mode + modes list.
- `GET /config` — all current rule keys.
- `GET /config/{key}` — current + full history.
- `PUT /config/{key}` — publish a NEW version (history preserved; audit
  entry `commercial_config.updated`; `default_billing_mode` validated).
- `GET /plans`, `GET /plans/{plan_code}` (current + history).
- `POST /plans` — create plan v1 (409 on duplicate code).
- `PUT /plans/{plan_code}` — publish a NEW version (audit
  `plan.version_published`).
- `GET /ledger?organization_id=` — append-only ledger + derived balance.
- `GET /organizations?billing_mode=` — org billing modes (filterable).

Backend support:
- `data/billing.py` — `BillingPlansRepository` (versioned),
  `BillingCommercialConfigRepository` (versioned),
  `BillingCreditLedgerRepository` (append-only, idempotent).
- `domain/billing.py` — `BillingPlan`, `CommercialConfig`,
  `CreditLedgerEntry`, `BILLING_MODES`.
- `api/dependencies.py` — the three repos wired into `RepositoryBundle`.
- `data/organizations.py` — `create_with_owner(billing_mode=...)` (org creation
  assigns the versioned default), `get_billing_mode`, `billing_mode` in org
  serialization; `tax_rate` removed from `_PROFILE_UPDATE_FIELDS`.
- `api/v3_organizations.py` — `create_organization` resolves the default mode.
- `auth.py` — `can_manage_billing` added to `DEFAULT_STAFF_PERMISSIONS`.

## 9. Admin Dashboard changes (exact)
- `frontend/src/v3/ops/CommercialTab.jsx` (NEW) — default billing mode,
  versioned commercial-rule editor (JSON + reason + versioned publish), plans
  table (version history, publish new version), new-plan form, customer
  billing-mode filter, per-org credit-ledger read surface.
- `frontend/src/v3/ops/OperationsPage.jsx` — `Commercial` tab appended when
  `me.permissions.can_manage_billing` (the real permission, server-enforced).
- `frontend/src/v3/api.js` — 9 commercial client functions.
- `frontend/src/v3/ops/ops.css` — `.commercial-json`, `.commercial-reason`,
  `.v3-table`.
- `frontend/src/v3/admin/ProfileTab.jsx` — `tax_rate` removed from the
  customer-editable profile fields; `billing_mode` shown read-only.


## 10. Commercial configuration model
`billing_commercial_config` — versioned key/value. Keys: `default_billing_mode`
(NEW customers only), `credit_rules`, `structured_data_bands`, `storage`,
`assisted_pricing`, `credit_policy`, `standard_allowance`. Current = row with
`effective_to IS NULL`; every update inserts a new version and closes the old
one (audited). Admin-only (staff + `can_manage_billing`).

## 11. Plan model
`billing_plans` — `plan_code` stable identity, `version` + effective window
historical-safety. Configurable: name, description, price, currency, billing
interval, included credits, included storage, team limit, processing limits,
features, billing mode, assisted/managed/api availability, active flag.
Values live in the database — never hard-coded in business logic.

## 12. Billing-mode model
`organizations.billing_mode` is the per-customer authoritative mode
(CREDIT | STANDARD). New customers get the versioned default at creation;
existing customers are NEVER silently migrated by a default change (verified
live: default flip CREDIT→STANDARD left the existing org on CREDIT).

## 13. Credit-rule model
`credit_rules` config: classes (simple/standard/complex/exceptional) → credits
(1/2/4/quoted). Configurable from Admin; not hard-coded in extraction logic.

## 14. Structured-data model
`structured_data_bands` config: rows → units (≤1k=1 … ≤1M=100, >1M=custom).
Configurable from Admin; no one-file-one-credit assumption.

## 15. Storage configuration
`storage` config: included bytes, additional rate, unit, markup intent (~100%).
Plan-specific `included_storage_bytes` per plan. Storage billing NOT
implemented in D37-0 (foundation only).

## 16. Assisted Processing price foundation
`assisted_pricing` config: simple £0.99 / standard £1.99 / complex £3.99+ /
exceptional quote (currency-configurable). Commercially separate from
automated credits; order/payment workflow deliberately NOT implemented.

## 17. Credit ledger foundation
`billing_credit_ledger` — append-only: grant/consume/adjustment/rollover/
emergency_allowance/refund/reversal; balance DERIVED (SUM), never a mutable
balance column; `(organization_id, external_reference)` unique idempotency for
future provider events. Writes via trusted service paths only; reads via the
staff API.

## 18. Entitlement foundation
Subscription → Plan (versioned) → included credits/limits/features →
credit ledger (grant → consumption → remaining). The payment provider is NOT
authoritative; no external payment events implemented yet.

## 19. Versioning strategy
All material commercial rules + plans use version rows with effective
windows. Historical commercial records reference the version in force at the
time; Admin changes never rewrite history.

## 20. Audit strategy

## 22. Tests
- **Backend unit: 1039 passed / 0 failed / 0 errors** (was 1020; +19 in
  `tests/unit/api/test_commercial_settings.py`): authorization matrix
  (anonymous 401; customer/consultant/entity-staff/plain-staff 403; billing
  admin 200), versioned config, versioned plans, ledger + idempotency,
  per-customer mode assignment, no-silent-migration.
- **RLS: 23 passed / 0 failed** (was 15; +8 in
  `tests/integration/test_v3_rls_behavior.py::TestBillingSecurityLockdown`):
  the 12 D37-0 §5 denial checks + trusted-path writes + schema-foundation.
- **Frontend: 23 passed** (api.test.js; +2 D37-0); the only failing suite is
  the PRE-EXISTING `App.test.js` react-router-dom v7 resolution failure
  (documented in D35/D36, unrelated).
- **Production build: OK** (exit 0; same pre-existing warnings as D35).

## 23. Live verification (26/26 passed; real stack, temporary fixtures)
1. P0 — customer INSERT `usage_tracking` / `customer_subscriptions` /
   `billing_credit_ledger` denied (3/3); org `subscription_status`/`tax_rate`/
   `trial_end_date` PATCH denied (403).
2. Authorization — customer 403, plain staff 403, billing admin 200.
3. CREDIT + STANDARD represented; seeded plans/config present.
4. Default mode flip → v2; history [1,2]; NEW customer STANDARD; existing
   customer CREDIT (no silent migration).
5. credit_rules v2 with history; plan professional v2 (179) with history
   (v1=149).
6. Ledger: trusted INSERT + staff balance 500 + customer read 403.
7. D33 evidence list 200; D35 onboarding 201 with billing_mode=CREDIT.
   Fixtures cleaned (orgs 0, users 0, ledger 0, config back to seed v1).

## 24. Remaining limitations (intentional for D37-0)
- No billing service/API/UI for customers, no checkout, no provider
  integration, no webhooks, no payment collection.
- No entitlement ENFORCEMENT (limits/credits not yet consumed by the
  processing pipeline — D37-1+).
- No complexity-classifier wiring; credit rules are configurable but not yet
  applied.
- No storage billing; no Assisted/Managed order workflow.
- No credit consumption yet (the ledger foundation exists; grants are the
  only demonstrated path).
- `can_manage_billing` is granted to the admin role; other staff roles need an
  explicit grant if the Product Owner wants tiered access.
- Combined-process unit+integration pytest runs show 5 pre-existing
  customer-admin failures caused by the integration conftest's env mutation
  (they pass in separate runs — the project convention).

## 25. D37-1 prerequisites
- Product Owner ratification of the D36 §29 decisions (provider selection,
  credit classes, bands, assisted prices, Managed terms, storage markup,
  rollover/emergency rules, STANDARD terms, B2B/B2C tax) BEFORE D37-1.
- D37-1 should build: billing core service (provider-neutral), entitlement
  enforcement at processing time, credit consumption via the ledger,
  idempotent order records, then the chosen provider adapter + webhooks.

## 26. Final recommendation
**HARD STOP reached — D37-0 is complete.** The P0 billing-security defect is
closed, the existing subscription system has been analysed (reused/extended,
nothing sound was replaced), a configurable provider-neutral commercial
foundation exists with Admin configuration and versioning, and all tests +
live verification are green. **D37-1 must NOT begin** until the Product Owner
ratifies the D36 §29 commercial decisions.

Every config/plan change appends an `audit_trail` entry
(`billing_commercial_config` / `billing_plan`, actor = staff user_id,
before/after version, reason). The audit append is fail-open (never blocks the
authoritative change).

## 21. Provider-neutral architecture
No provider SDK, no hard-coded provider business logic. Provider-specific
concepts map to provider-neutral fields (`external_reference`,
`subscription_id`, plan refs). The legacy Stripe-named columns on
`customer_subscriptions`/`consultant_billing` remain as documented legacy and
are not used by the new foundation.

