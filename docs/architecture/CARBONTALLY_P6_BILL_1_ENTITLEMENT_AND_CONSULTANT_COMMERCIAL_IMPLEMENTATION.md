# CarbonTally P6-BILL-1 — Entitlement Enforcement + Consultant Commercial Scaffolding

**Status:** IMPLEMENTED (bounded workstream) — no migration, no commit/push.
**Authority:** `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` + the ratified
P6-BILL-1 decisions (D-A registration mode, D-C org→consultant additive
entitlement, D-D existing client-grant boundary, PO-D7 org-scoped credit
ownership + denial without entitlement).
**Baseline/readiness:** `docs/architecture/CARBONTALLY_P6_BILL_0_COMMERCIAL_ARCHITECTURE_RECONCILIATION.md`
(verdict: READY WITH PO DECISIONS — now ratified).

---

## 1. Implemented changes (summary)

1. **Server-side entitlement enforcement (PO-D7):** the single canonical
   processing-charge path (`BillingService.charge_processing`) now **denies**
   an organisation with **no active processing entitlement** instead of the
   previous `no_subscription → allowed/free`. Enforcement point unchanged: the
   org is always the server-derived owner of the work/resource (the customer
   approval transition in `v3_processing_workflow.customer_review_item` passes
   `batch.organization_id`). No billing checks were scattered elsewhere.
2. **Consultant capability representation (D-C):** Consultant capability is
   modelled as an **additive plan feature** on the existing D37 catalogue
   (`billing_plans.features.consultant = {enabled, client_capacity,
   team_member_limit, white_label, workspace}`). The active subscription's plan
   feature block is resolved server-side by `BillingService.consultant_capability(org)`
   and surfaced in `get_entitlement()["capabilities"]["consultant"]`. NO second
   organisation is created; org identity/data/history/billing are untouched.
3. **Registration mode (D-A):** platform registration mode is represented as a
   **versioned commercial config key** (`registration_mode` in
   `billing_commercial_config`, values `INVITATION_ONLY` | `OPEN_REGISTRATION`),
   publishable only through the CarbonTally Admin commercial surface
   (`/api/v3/commercial/config/registration_mode`, internal staff +
   `can_manage_billing`). Canonical resolver
   `services.billing.resolve_registration_mode()` gates self-service entry:
   `INVITATION_ONLY` blocks `POST /api/v3/organizations` (D35 self-service) and
   `POST /api/v3/consultants/me` (consultant self-registration). Missing config
   defaults to `OPEN_REGISTRATION` (the pre-existing behaviour).
4. **Client-grant creator provenance (Scope E / D-D):** consultant client
   grants now record the **server-authoritative authenticated actor** in the
   existing `consultant_clients.created_by` column (never a client-supplied
   value; the request schema has no actor field and ignores unknown fields).

## 2. Database changes

**NONE.** No migration was required — every concept already had a home:
- `consultant_clients.created_by` (column exists since init schema);
- `billing_commercial_config` (versioned config store for `registration_mode`);
- `billing_plans.features` JSONB (Consultant capability feature block).
- `billing_credit_ledger.organization_id` / `customer_subscriptions.organization_id`
  (PO-D7 ownership unchanged).
No historical migration was modified. Live-DB count baseline is **identical
before/after** (see §11) and the new INSERT SQL was verified against the real
schema inside a rolled-back transaction.

## 3. API / domain changes

| File | Change |
|---|---|
| `backend/domain/billing.py` | `REGISTRATION_MODES`, `DEFAULT_REGISTRATION_MODE` constants |
| `backend/services/billing.py` | `resolve_registration_mode(repos)` (canonical resolver); `BillingService.consultant_capability(org)` + `_consultant_capability_from_plan(plan)`; `get_entitlement()` now returns `capabilities.consultant`; `charge_processing` no-entitlement branch now raises `EntitlementUnavailableError` (403) |
| `backend/api/v3_commercial.py` | `registration_mode` added to admin `CONFIG_KEYS` + PUT validation (values whitelist) + overview exposes `registration_modes` |
| `backend/api/v3_organizations.py` | D35 self-service org creation gated by registration mode (INVITATION_ONLY → 403) |
| `backend/api/v3_consultants.py` | Consultant self-registration (`POST /me`) gated by registration mode; `POST /me/clients` and `POST /me/customers` now persist `created_by` from the authenticated actor |
| `backend/domain/partners.py` | `ConsultantClient.created_by` field added (Optional, default None) |
| `backend/data/consultants.py` | `_CLIENT_COLUMNS` includes `created_by`; `_row_to_client` maps it; `add_client(..., created_by=None)` INSERTs it |
| `backend/tests/unit/api/fakes.py` | `MemoryConsultants.add_client` accepts and persists `created_by` |
| `backend/tests/unit/api/test_billing_core.py` | `test_charge_processing_no_subscription_*` updated to the ratified DENY behaviour |
| `backend/tests/unit/api/test_p6bill1_entitlement_and_consultant_commercial.py` | NEW focused suite (23 tests) |

## 4. Entitlement enforcement point

- **Canonical service gate:** `BillingService.charge_processing(organization_id,
  job, idempotency_key, actor)` — the one server-side function every chargeable
  processing path must call. An organisation with no active subscription now
  raises `EntitlementUnavailableError` (HTTP 403) instead of `{mode:
  "no_subscription", allowed: True}`.
- **Single call site preserved:** `v3_processing_workflow.customer_review_item`
  (customer approval) derives the org from `batch.organization_id` and maps
  billing errors to HTTP — the existing D37 "approval triggers the charge"
  design and PO-D7's server-derived org are both preserved.
- **Result:** an organisation without the required active processing
  entitlement cannot complete chargeable processing. Expired/cancelled
  subscriptions resolve to no active entitlement and are likewise denied;
  active-but-exhausted plans continue to fail closed (402).
- Active STANDARD/CREDIT entitlement paths are unchanged; only the
  previously-free no-subscription path was flipped (per PO-D7).

## 5. Consultant capability representation (D-C)

- **Where:** the organisation's ACTIVE subscription → its `billing_plans`
  version → `features.consultant` block:
  `{enabled: bool, client_capacity?: int, team_member_limit?: int,
  white_label?: bool, workspace?: bool}` (admin-configurable through the
  existing versioned plan catalogue — CT-BILL-003, no code change for pricing).
- **Server resolver:** `BillingService.consultant_capability(organization_id)`
  returns the canonical projection `{organization_id, plan_code, entitled,
  client_capacity, team_member_limit, white_label, workspace}`; the same
  projection is embedded in every `get_entitlement()` response under
  `capabilities.consultant` (customer `/billing/me` and the admin
  `/commercial/entitlement/{org}` read).
- **Identity preserved:** capability is resolved ON the organisation id — no
  organisation duplication, no migration, no destructive conversion. Org name,
  users, data, history, billing all stay untouched (verified by test).
- **Boundary kept:** this entitlement NEVER creates consultant_clients grants,
  never grants access to an existing org, and never replaces the active-grant /
  D-3 capability checks (those remain P6-1B/C / P6-2 surfaces).

## 6. Registration mode representation + enforcement (D-A)

- **Representation:** `billing_commercial_config` key `registration_mode` with
  `config_value = {"mode": "INVITATION_ONLY"|"OPEN_REGISTRATION"}` — versioned
  and audited like every other commercial rule; exposed ONLY via the admin
  commercial surface (`/api/v3/commercial/config/...`, internal staff +
  `can_manage_billing`; values whitelisted; normal users get 403).
- **Canonical resolver:** `resolve_registration_mode(repos)`; absent/invalid
  config → `OPEN_REGISTRATION` (pre-existing D35 behaviour — additive safe
  default; Admin can switch the platform to closed mode by publishing the key).
- **Enforcement (self-service entry only):**
  - `POST /api/v3/organizations` (D35) → 403 in INVITATION_ONLY mode.
  - `POST /api/v3/consultants/me` (consultant self-registration) → 403 in
    INVITATION_ONLY mode.
  - Authorized provisioning is unaffected: org invitations, consultant-created
    customers, CarbonTally/demo-seeded identities, member invites.
- **Not an authorization shortcut:** registration mode never grants org/client
  access, consultant capability, processing permissions, or staff/PE/CT/Admin
  authority; no RLS policy changed.

## 7. Credit ownership (PO-D7) — confirmed

**The client organization owns the processing entitlement consumed by its
work.** Credits, usage, orders and subscriptions remain organisation-scoped
(`billing_credit_ledger.organization_id`, `usage_tracking.organization_id`,
`customer_subscriptions.organization_id`); the charge org is server-derived
from the item/batch. No firm-scoped pooled wallet was introduced; no
cross-client transfer is possible; a consultant context cannot redirect a
charge (there is no consultant charging surface, and the only charge call uses
the work's owning org). `consultant_billing` was NOT revived, migrated or
deleted.


## 8. Security invariants (BILL-SEC-001…004)

| Invariant | Result | Evidence |
|---|---|---|
| BILL-SEC-001 — Server-side commercial authority | **PASS** | Plan/features/entitlement/credits resolved from server DB (`billing_plans`, `billing_commercial_config`, ledger) via `BillingService`; registration mode is server config read by `resolve_registration_mode`; authenticated direct writes remain revoked (D37-0) |
| BILL-SEC-002 — Client price integrity | **PASS** | No client-supplied price/total/discount fields exist in commercial request contracts (`extra="forbid"` where defined); charge/entitlement inputs are org+job only |
| BILL-SEC-003 — Entitlement integrity | **PASS** (was PARTIAL) | No active processing entitlement now DENIES the chargeable action (`EntitlementUnavailableError` 403); no client-supplied claim parameter exists to bypass; capability checks are server-resolved |
| BILL-SEC-004 — Administrative configuration | **PASS** | `registration_mode` + plans/config publishable only by internal staff holding `can_manage_billing`, versioned and audited; admin config cannot write RLS/org grants (no authorization bypass) |

Gate 3–6 boundaries untouched: no RLS policy changed, no provenance data
altered, no assignment/messaging/notification/approval rule weakened; the
customer-approval charge path still fires server-side at the approval
transition.

## 9. Tests (exact counts / results)

- **New focused suite** `tests/unit/api/test_p6bill1_entitlement_and_consultant_commercial.py`:
  **23/23 PASS** (exit 0). Coverage: registration mode (default OPEN, admin
  config read, OPEN permits org + consultant self-registration, INVITATION_ONLY
  blocks both, registration never grants client access, non-admin cannot change
  mode), entitlement (active permits / none denies / cancelled denies /
  server-resolved / claims cannot bypass), credit ownership (Client A pays only
  A, A cannot consume B, no firm pool), consultant capability (entitled passes /
  non-entitled fails / no second org / no self-created client grants),
  client-grant provenance (creator = authenticated actor, permission-less
  consultant denied, forged actor field ignored).
- **Updated test:** `test_billing_core.py` no-subscription test now asserts the
  ratified DENY behaviour (403, "processing entitlement").
- **Focused regression** (billing_core, commercial_settings,
  self_service_onboarding, v3_consultants, scope_aware_authorization,
  phase1_core_regressions): **119/119 PASS**.
- **Full unit suite** `pytest tests/unit -q`: **ALL PASS, 0 failures** (exit 0;
  only a pre-existing third-party urllib3/chardet warning).


## 10. Regression verification

- Route registration/authorization tests, org-member/RLS-scope tests,
  consultant cross-client tests, D5 approval-gate tests and D35 onboarding
  tests all remain green (see §9 focused + full unit results).
- The only intended behaviour change is the PO-D7 no-entitlement denial, which
  is covered by the updated and new tests; no other expected-behaviour change
  was made.

## 11. Baseline (before/after, live PostgreSQL read-only)

| Table | Before (P6-BILL-0) | After (this workstream) |
|---|---|---|
| billing_plans | 6 | 6 |
| billing_commercial_config | 7 | 7 |
| billing_credit_ledger / customer_subscriptions / orders / payments / storage / idempotency | 0 | 0 |
| consultant_billing | 0 | 0 |
| consultant_profiles / firm_members | 55 / 54 | 55 / 54 |
| consultant_clients | 917 | 917 |
| organizations | 975 | 975 |

No seeded commercial data, plan prices or identity/grant data were altered.
Real-PostgreSQL verification: the new `add_client` INSERT (with `created_by`)
executed against the live schema returned and read back the actor id, then
rolled back (client count 917 → 917). Registration mode and capability feature
values were NOT seeded — they are admin configuration / plan data for the
Admin control plane to publish.

## 12. Known limitations / deferred work

- Default behaviour remains OPEN_REGISTRATION until CarbonTally Administration
  publishes `registration_mode = INVITATION_ONLY`; no public registration UI
  and no Supabase-Auth signup gate were added (external deployment config).
- Consultant workspace/processing actions (extract/map/validate/calculate),
  D-3 capability enforcement beyond representation, org→consultant workspace
  mapping for org users, controlled firm membership (P6-1B) and the
  authorized-engagement flow for pre-existing client orgs
  (P6-1C / CT-CONSULT-003 confirmation) are NOT implemented — later
  workstreams.
- No payment provider, checkout, webhooks, pricing, taxes, discounts or
  invoices were implemented.
- `features.consultant` client/team capacity values are represented and exposed
  but not yet enforced by any consultant action surface (none exists yet).
- `consultant_clients.created_by` is now written by the two consultant routes;
  pre-existing rows keep NULL `created_by` (historical provenance was not
  fabricated).

## 13. Problems / PO decisions

No unresolved decisions within scope. PO-D7 is implemented additively through
the existing server-authoritative charge path. Registration-mode enforcement
at the Supabase Auth signup layer remains an external-configuration deployment
item, not a code defect.

## 14. Git status

Working tree left for PO review: **no commit, no push, no pull request.**
Files changed/created by this workstream:
- M `backend/domain/billing.py`, `backend/services/billing.py`,
  `backend/api/v3_commercial.py`, `backend/api/v3_organizations.py`,
  `backend/api/v3_consultants.py`, `backend/domain/partners.py`,
  `backend/data/consultants.py`, `backend/tests/unit/api/fakes.py`,
  `backend/tests/unit/api/test_billing_core.py`
- A `backend/tests/unit/api/test_p6bill1_entitlement_and_consultant_commercial.py`
- A `docs/architecture/CARBONTALLY_P6_BILL_1_ENTITLEMENT_AND_CONSULTANT_COMMERCIAL_IMPLEMENTATION.md`

(The repo also contains extensive pre-existing uncommitted Phase 4–6 work from
earlier sessions; this workstream did not touch it beyond the files above.)

