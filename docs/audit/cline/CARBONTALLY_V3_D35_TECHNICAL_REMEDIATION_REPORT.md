# CarbonTally V3 — D35 Technical Remediation & Self-Service Customer Onboarding Report

**Date:** 2026-08-23
**Status:** D35 COMPLETE — HARD STOP (commercial/billing explicitly deferred)
**Scope:** D34 P1 #1 (self-service signup / Direct-Customer onboarding), D34 P2
technical items, and the operational documentation gaps (backup/DR,
observability, legacy dashboard). **No billing implementation** (D34 P1 #2 and
D35 §2.8 — provider-neutral; see §22).

Every finding below is classified exactly one of: IMPLEMENTED / VERIFIED /
EXTERNAL CONFIGURATION REQUIRED / BUSINESS DECISION REQUIRED / FUTURE.

---

## 1. Executive summary

D35 makes a completely new customer able to **discover CarbonTally, sign up,
authenticate (Supabase Auth), create or adopt an organization, become OWNER,
and enter the V3 customer workspace** without CarbonTally staff manually
provisioning the account.

Implemented and verified live:

| Capability | State |
|---|---|
| Public self-service signup (`/signup`) — no beta-code gate | IMPLEMENTED + VERIFIED |
| Beta/invite mechanism preserved as optional admin path (`/beta/signup`) | VERIFIED |
| Supabase Auth remains authoritative (email/password + Google OAuth wiring) | VERIFIED (Google = EXTERNAL CONFIGURATION) |
| `POST /api/v3/organizations` — customer-initiated org creation | IMPLEMENTED + VERIFIED |
| Creator becomes OWNER via the real `organization_members.role` model | VERIFIED |
| Atomic org+owner creation in one transaction (no service-role browser bypass) | VERIFIED |
| Duplicate prevention via D19 candidate signals (exact company-number block + acknowledgment) | IMPLEMENTED + VERIFIED |
| Pre-org-creation existing-data discovery (lookup → request → verify → USE ALL/PARTIAL/DISCARD) | IMPLEMENTED + VERIFIED |
| Post-login routing to V3 `/home` (never legacy `/dashboard`) | VERIFIED |
| Onboarding loading guard bounded (never stuck on a spinner) | IMPLEMENTED + VERIFIED |
| RLS / cross-org / consultant / staff / private-storage / evidence authorization intact | VERIFIED |

**Three pre-existing production defects were found and fixed** (genuine D34
blockers discovered during live verification, not new features):

1. `data/tenant.py` inserted `organization_members` with `joined_at`/`last_active`
   — columns that do **not exist** in the live schema (the table has
   `created_at`). This broke **every** membership write server-side, including
   the D19 adoption path. Fixed to the real schema.
2. `data/discovery.py lookup_candidates` crashed with
   `ValueError: unsupported format character` whenever the `name` signal was
   supplied (unescaped SQL `%` wildcards). This is the discovery path the
   onboarding flow depends on. Fixed.
3. Supabase Auth users live in `auth.users` only; `organization_members.user_id`
   references `public.users` — so a brand-new signup could never receive a
   membership row (FK violation). Fixed with an additive `auth.users →
   public.users` sync trigger **plus** a defensive server-side upsert in
   `create_with_owner`.

All D35 changes are additive, idempotent, RLS-safe, documented and tested.

## 2. D34 findings addressed

| D34 finding | D35 disposition |
|---|---|
| **P1 #1 — Self-service signup / Direct-Customer onboarding incomplete** | IMPLEMENTED. `/signup` is now the self-service path (no beta code); a new customer can create/adopt an organization and become OWNER; `/beta/signup` preserves the controlled-cohort mechanism. |
| **P1 #2 — Billing not implemented** | INTENTIONALLY DEFERRED (see §22). No Stripe/Paddle/Lemon Squeezy/Chargebee/Recurly code, no webhooks, no checkout, no subscription/credit/usage billing. Provider-neutral customer/account state preserved only. |
| **P2 — Transactional email templates** | PARTIAL. Minimum required app-level trigger implemented: organization-created confirmation via the existing `send_transactional_email` (fail-open). Auth/verification/reset emails are Supabase Auth (EXTERNAL CONFIGURATION). Other templates (invitation, report-ready, issue, onboarding confirmation variants) classified P2/FUTURE. |
| **P2 — Backup/DR runbook** | DOCUMENTED (operational procedure — §11; no application feature invented). |
| **P2 — Observability/alerting** | DOCUMENTED + low-risk guard added (bounded onboarding loading state). External monitoring = EXTERNAL CONFIGURATION (§12). |
| **P2 — Public help/FAQ** | CLASSIFIED FUTURE. No fictional pricing created (see §18). |
| **P2 — Legacy `/dashboard/*` retirement** | AUDITED + SAFE REDIRECT implemented (see §13). |
| **P2 — Landing/service/pricing/contact content** | Pricing is BUSINESS DECISION REQUIRED (Product Owner). No invented pricing. |

## 3. Self-service onboarding architecture

```
PUBLIC VISITOR ──> /signup ──> Supabase Auth (signUp) ──> /onboarding
                                                           │
                                           resolveV3Organization() ──> /home (has org)
                                                           │
                                      (no org, not staff/consultant)
                                                           │
                                     ┌─────────────────────┴──────────────────┐
                                     ▼                                        ▼
                        POST /api/v3/organizations                 D19 existing-data discovery
                        (candidate check + atomic                  (POST /discovery/lookup,
                         org+owner transaction)                     /requests, verify, choice)
                                     │                                        │
                              creator = OWNER                          USE ALL / PARTIAL / DISCARD
                                     │                                        │
                                     └──────────────┬─────────────────────────┘
                                                    ▼
                                                /home (V3 customer workspace)
                                                    │
                              upload → process → verify → report (unchanged D33 chain)
```

Tenancy anchor remains **organizations** (no generic workspace/tenant model).
The creator's OWNER role is the real `organization_members.role` CHECK
(`owner|admin|member|viewer`) — no second role system.

**Onboarding state** (D35 §8): kept deliberately small — a client-side step
machine on `/onboarding` (`details → review → verify → decision → created`).
Every state has success, error, retry ("Start over"/"Back") and an
authenticated route guard. The guard is **bounded** (12 s fallback) so a user
is never stuck on a loading screen. No server-side onboarding-state table was
needed.

## 4. Signup changes

Audit result (D35 §5):

* **Why beta-gated:** the public `/signup` route rendered `BetaSignup.jsx`,
  which validates a `beta_access_codes` row and refuses to proceed without a
  code; `Login.js` already had an ungated toggle-signup path.
* **Decision:** `/signup` now renders `SelfServiceSignup.jsx` (no beta code).
  The beta/invite mechanism is **preserved** as the optional administrative /
  controlled-cohort path at `/beta/signup` (link: "Have an access code?").
* Supabase Auth remains authoritative: `supabase.auth.signUp({ email, password,
  options: { data: { full_name, company_name, onboarding: true } } })`.
* On immediate session (local `enable_confirmations=false`) the customer is
  routed via `resolvePostLoginPath()` → `/onboarding`; with email confirmation
  enabled (production) the customer confirms and lands back via `/auth/callback`.
* `BetaSignup.jsx` no longer redirects to the legacy `/dashboard` (it uses the
  server-authoritative `resolvePostLoginPath()`).

**Files:** `frontend/src/SelfServiceSignup.jsx` (new), `frontend/src/App.js`
(route), `frontend/src/BetaSignup.jsx` (post-signup routing), `frontend/src/Login.js`
(Google redirect → `/auth/callback`).

## 5. Organization creation

`POST /api/v3/organizations` (new, `api/v3_organizations.py`):

* **Auth:** `require_auth()` (any authenticated user — including a user with no
  organization, the point of self-service).
* **Guard:** a user who already has an ACTIVE membership cannot create a second
  org (`409`).
* **Validation:** name required (1–200), country/company-number optional; extra
  fields rejected (`extra="forbid"`).
* **Duplicate prevention (D19 §6 / D35 §7):** candidate signals (`name`,
  `company_number`, the creator's verified email domain, `contact_email`) are
  matched against existing organizations. An **exact company-number match is a
  strong duplicate signal and blocks creation** (`409`, message guides to the
  existing-data review) unless the customer **explicitly acknowledges** the
  candidate ids. Weaker signals are returned as informational candidates in the
  `201` response. Candidate matching is NEVER authoritative ownership.
* **Atomicity:** `OrganizationsRepository.create_with_owner()` creates the
  organisation + the initial `owner` membership + the creator's `public.users`
  backstop row **in one transaction**.
* **Server-authoritative:** runs through the service-role pool; no browser/
  service-role bypass. The resulting membership is what authorizes the owner's
  RLS-scoped requests.
* **Audit + email:** append-only `organization.created` audit entry and the
  minimum required confirmation email (fail-open).
* `company_number` is now **persisted** on the org row (was discarded) so the
  exact-match duplicate signal works for subsequent customers.


## 6. Direct Customer lifecycle

* A Direct Customer **initiates** the relationship (D35 §2.2). A new user signs
  up and either creates an org (becomes OWNER) or adopts an existing org via the
  discovery flow (becomes OWNER of the existing org; `customer_type=direct`).
* D19 consultant lifecycle (ACTIVE/SUSPENDED/ENDED) preserved: USE ALL / PARTIAL
  adoption ends ACTIVE consultant grants for the adopted org and records
  `consultant_client.ended` audit entries (unchanged D19 code).
* No lifecycle state machine was introduced beyond the existing D19
  `data_discovery_requests` statuses and the client-side onboarding steps.

## 7. Existing-data adoption behavior (D19 preserved)

The D19 flow is **intact** and now also works **before** org creation:

* `data_discovery_requests.organization_id` is now nullable (additive ALTER) —
  `NULL` marks a pre-org-creation onboarding request.
* New column `created_by` binds an onboarding request to the actor who started
  it; only that actor may verify and choose an outcome (`get_for_onboarding`,
  cross-user → 403/404).
* Partial unique index prevents duplicate live onboarding requests per candidate.
* Lookup/request/verify/choice endpoints accept an optional `organization_id`:
  supplied → org-scoped D19 (unchanged); omitted → onboarding variant.
* **USE ALL** — adoption in place: existing organisation id is preserved
  (no duplicate org, no data copy), the customer becomes `owner`, ACTIVE
  consultant grants end, `customer_type=direct`.
* **PARTIAL** — adoption in place with the selected categories recorded for
  provenance (`adoption_scope.categories`).
* **DISCARD** — the decision is recorded (`discarded`, `discarded_by`, note);
  **no data is deleted**; in the blocked (pre-org) case the customer then
  creates a fresh organisation acknowledging the reviewed candidates.

Verified live with real API calls + real auth (see §19) and with unit tests
covering no-match / one candidate / cross-user denial / verify-before-choice /
USE ALL / DISCARD / org-scoped regression.

## 8. Authentication

* Supabase Auth remains authoritative (no custom auth). Email/password via
  `supabase.auth.signUp` / `signInWithPassword`; Google OAuth unchanged
  (redirect target corrected from `/dashboard` to `/auth/callback` so every
  OAuth session resolves through the server-authoritative post-login path).
* MFA, Google provider config, production site URL and redirect URLs, and email
  confirmation are **EXTERNAL CONFIGURATION** (§21). Local behaviour verified:
  signup (auto-confirmed), sign-in, token validation by the backend, sign-out.

## 9. Routing

* `resolvePostLoginPath()` (server-authoritative) order: org → `/home`;
  internal staff → `/ops`; consultant → `/consultant`; **otherwise →
  `/onboarding`** (new customer).
* `/home` + V3Layout: an authenticated user with no org, not staff, not
  consultant is redirected to `/onboarding` (no dead-end empty state).
* Legacy `/dashboard/*` → redirect to `/home` (see §13).
* Roles verified by code inspection + unit coverage: OWNER, CONSULTANT,
  OPERATOR, REVIEWER, QC, STAFF-ADMIN, ENTITY-STAFF resolve to their existing
  workspaces (D29 behaviour not regressed).

## 10. Email / Resend

| Email | State |
|---|---|
| Signup / verification / password reset | Supabase Auth — **EXTERNAL CONFIGURATION** |
| Existing-data verification code | IMPLEMENTED (D19; `send_transactional_email`) — delivery is EXTERNAL CONFIGURATION (Resend) |
| Organization-created confirmation | IMPLEMENTED (D35; fail-open) |
| Onboarding / adoption confirmation | P2/FUTURE |
| Invitation email | P2/FUTURE (existing invitation row + in-app surface) |
| Report-ready / processing / issue notifications | P2/FUTURE |

No email-template management system was built.


## 11. Backup / Disaster Recovery

Operational documentation (D35 §15 — no application feature invented; backups
are NOT claimed to exist where they do not).

* **Database:** the Postgres database (all `public.*` schema + data) is the
  system of record. Local/Supabase-managed environments: use `pg_dump` /
  `pg_dumpall` or Supabase "PITR"/"Database backups" features. This is the
  responsibility boundary for the hosting provider.
* **Supabase responsibilities:** Auth metadata (`auth.users`, identities,
  sessions) and Realtime are managed by Supabase; snapshot/PITR of the managed
  Postgres covers them. Any migration must be additive + idempotent so a
  restore never replays destructive DDL.
* **Storage / documents:** private organisation files live in Supabase Storage
  (`private` bucket, signed-URL access). Backups must include both the
  `organization_files` metadata rows AND the Storage objects (bucket export);
  document-binary export is a P2/FUTURE feature (D34).
* **Recovery procedure (documented runbook):** (1) restore the latest Postgres
  snapshot/PITR to a staging instance; (2) apply any newer additive migrations
  in order; (3) restore Storage objects + verify `organization_files.path`
  references resolve; (4) verify the D33 evidence chain FK integrity + signed
  URL access on the restored environment; (5) point a canary environment at the
  restored DB before production cutover.
* **Restore testing:** NOT yet scheduled — **EXTERNAL CONFIGURATION REQUIRED /
  FUTURE** (an owner decision; not implemented in D35).
* **Retention assumptions:** not yet defined by the operator — **BUSINESS
  DECISION REQUIRED** (RPO/RTO targets, snapshot retention window).
* **Responsibility boundaries:** application code has no backup scheduler and
  should not have one; backups/DR are an operational + hosting-provider
  responsibility.

## 12. Observability / alerting

* **Current state:** the backend exposes `/health` (liveness). The V3 API client
  applies bounded request timeouts (25 s) and surfaces friendly errors. D35
  added a bounded onboarding guard so a slow upstream resolution can never leave
  a customer stuck on a loading screen.
* **Minimum launch-critical monitoring (documented, NOT yet configured):**
  API availability (`/health`), frontend availability, database connectivity,
  processing failures, background/job failures, email delivery failures (Resend
  events), storage failures, authentication failures. External platform
  monitoring (Vercel, Render, Supabase, Resend) — **EXTERNAL CONFIGURATION
  REQUIRED**.
* No observability platform was invented.

## 13. Legacy dashboard assessment

* **Usage audit:** `/dashboard/*` is reachable only by direct URL (post-login
  routing has used `/home` since D29; V3Layout nav, `Login.js`, `AuthCallback.js`
  and `BetaSignup.jsx` all resolve through `resolvePostLoginPath()`). The old
  `App.js:422` notification link pointed at `/dashboard/notifications`.
* **Retirement decision:** the legacy surfaces are safely obsolete for the
  customer journey. D35 implements a **safe redirect**: `/dashboard/*` →
  `/home`, and the notification link now targets `/notifications`. The legacy
  components (`Dashboard`, `DashboardLayout`, old routes) are **not deleted**
  (reversible); a full code-removal is a separate cleanup task (FUTURE).
* Remaining direct references to `/dashboard` were audited (tests, docs) and
  the frontend no longer produces them.

## 14. Security / RLS

All preserved and re-verified:

* Supabase RLS: deny-by-default unchanged; the D35 schema change (nullable
  `organization_id` + `created_by`) does not touch any policy. RLS behaviour
  suite: **15/15** (11 baseline + 4 new D35 assertions: onboarding requests
  deny-by-default, new customer sees no org rows, D35 columns present,
  `owner` role CHECK intact).
* Organization isolation: cross-org access denied live (403) and in unit tests.
* Consultant ACTIVE-grant restrictions: unchanged (D15); adoption ends grants.
* Entity/staff permissions: unchanged (D20 scope-aware model).
* Private document storage + signed URLs: unchanged (D32).
* D33/D33.1 evidence authorization: unchanged (evidence endpoints untouched).
* Messaging authorization: unchanged.
* New endpoints all require authentication; the no-org onboarding request is
  bound to `created_by` and only that actor may verify/choose (cross-user
  denied — verified in unit tests and live).
* No browser/service-role security bypass: server-side pool only.

## 15. Database / migrations

* One additive, idempotent migration: `supabase/migrations/20260824010000_d35_self_service_onboarding.sql`
  — (1) `data_discovery_requests.organization_id` DROP NOT NULL; (2) `created_by`
  column; (3) partial unique index for live onboarding requests per candidate;
  (4) `auth.users → public.users` sync function + guarded trigger.
* No destructive DDL, no data deletion, no RLS policy altered.
* Applied and re-run on the main app database AND the dedicated
  `carbontally_test` database (the trigger is skipped on the test DB, which has
  no `auth` schema — idempotent everywhere).
* Integration-suite main-DB protection verified: pointing
  `INTEGRATION_DATABASE_URL` at the main `postgres` database raises
  `RuntimeError` (no TRUNCATE ever runs against it).


## 16. APIs changed

| Endpoint | Change | State |
|---|---|---|
| `POST /api/v3/organizations` | NEW — self-service org creation (creator → OWNER, atomic, duplicate-prevention, audit + email) | IMPLEMENTED + VERIFIED |
| `POST /api/v3/discovery/lookup` | `organization_id` now optional → pre-org onboarding lookup | IMPLEMENTED + VERIFIED |
| `POST /api/v3/discovery/requests` | `organization_id` optional → onboarding request (bound to `created_by`) | IMPLEMENTED + VERIFIED |
| `GET /api/v3/discovery/requests/{id}` | `organization_id` optional → onboarding fetch | IMPLEMENTED + VERIFIED |
| `POST /api/v3/discovery/requests/{id}/verify` | `organization_id` optional → onboarding verify | IMPLEMENTED + VERIFIED |
| `POST /api/v3/discovery/requests/{id}/choice` | `organization_id` optional → onboarding USE ALL/PARTIAL/DISCARD (no requesting-org deactivation when none exists) | IMPLEMENTED + VERIFIED |
| `GET /api/organizations/members/user/{id}` | unchanged (still the V3 org-resolution endpoint; D29 fix retained) | VERIFIED |

## 17. Frontend changes

* `frontend/src/SelfServiceSignup.jsx` (NEW) — public self-service signup.
* `frontend/src/OnboardingPage.jsx` (NEW) — `/onboarding` step machine with
  bounded guard, org creation, existing-data review, verification, USE ALL /
  PARTIAL / DISCARD decision, error/retry/empty states.
* `frontend/src/v3/api.js` — `createOrganization`, onboarding discovery
  helpers; `resolvePostLoginPath` fallback → `/onboarding`.
* `frontend/src/App.js` — routes: `/signup` (self-service), `/beta/signup`
  (beta), `/onboarding`, `/dashboard/*` → `/home`; notification link fixed.
* `frontend/src/v3/components/V3Layout.jsx` — no-org (non-staff/non-consultant)
  → `/onboarding`.
* `frontend/src/BetaSignup.jsx` — post-signup routing via `resolvePostLoginPath`.
* `frontend/src/Login.js` — Google OAuth redirect → `/auth/callback`.
* `frontend/src/v3/v3.css` — onboarding styles (existing V3 visual language).
* `frontend/src/v3/__tests__/api.test.js` — D35 client tests.

## 18. Tests

* **Backend unit:** `tests/unit/api/test_self_service_onboarding.py` (NEW, 18
  tests: anonymous 401, owner creation, membership guard, empty name 422,
  company-number block + acknowledgment, weak-candidate informational, no-org
  lookup, org-scoped lookup 403 for non-members, onboarding request binding,
  missing candidate 404, USE ALL adoption in place, direct-customer labelling,
  DISCARD records-only, choice-before-verify 409, cross-user 403/404, org-scoped
  adoption regression). Full unit suite: **1020 passed** (baseline + 18).
* **RLS integration:** `tests/integration/test_v3_rls_behavior.py` +4 D35 tests
  → **15 passed**. Main-DB protection re-verified (RuntimeError refusal).
* **Frontend:** `api.test.js` 21 passed (18 baseline + 3 new). Production build
  succeeds.
* **Pre-existing infra note:** `src/App.test.js` cannot load under the current
  jest/react-router-dom v7 combination (`Cannot find module 'react-router/dom'`
  in jest's resolver) — this predates D35 (fails at `App.js:4` loading
  react-router-dom, before any D35 import) and is out of D35 scope.

## 19. Live smoke verification

Against the running stack (backend :8001, frontend :3000, Supabase 54425/54426),
with REAL Supabase Auth users:

**Core journey (11/11 PASS):** admin user create (self-service path) → password
sign-in → no-org resolution empty → anonymous org creation denied (403) →
onboarding discovery lookup (no org) 200 → org creation 201 (OWNER) → org
resolution binds new org → owner workspace profile 200 → **cross-org denied
403** → org-scoped lookup denied for non-member 403 → second org creation
blocked 409 → re-auth token authoritative.

**Adoption journey (10/10 PASS):** candidate org created by owner A → B (no org)
lookup finds candidate → B creates onboarding request (no org) → B verifies
with email code → B **USE ALL** adopts in place (org id preserved; B becomes
owner; `customer_type=direct`) → B's org resolution binds the adopted org → A's
owner access preserved → B cannot create a second org → C **DISCARD** records
the decision (no deletion) → C creates a fresh org.

All live fixtures were removed afterward (before/after counts: orgs 21→0,
onboarding requests 1→0, users/auth-users 23→0); demo data untouched.

## 20. Screenshot evidence

`/home/shomonrobie/carbon_tally/screenshots/d35_customer_onboarding/` — 9
genuine captures from the running application (Selenium + Firefox headless)
+ `UI_SCREENSHOT_MANIFEST.md`:

`d35-landing.png`, `d35-signup.png`, `d35-auth.png`, `d35-onboarding-empty.png`,
`d35-onboarding-error.png`, `d35-onboarding-existing-data.png`,
`d35-onboarding-decision.png`, `d35-onboarding-success.png`,
`d35-customer-home.png`.

## 21. External configuration requirements

* Supabase project: production instance, site URL, redirect URLs
  (`/auth/callback`), Google OAuth provider, **MFA**, email confirmation,
  SMTP/email provider — **EXTERNAL CONFIGURATION REQUIRED**.
* Resend: domain verification + sender for `notifications@carbontally.co.uk`,
  delivery monitoring — **EXTERNAL CONFIGURATION REQUIRED**.
* Vercel (frontend): production env vars (`REACT_APP_SUPABASE_URL`,
  `REACT_APP_SUPABASE_ANON_KEY`, `REACT_APP_API_URL`), site URL — **EXTERNAL
  CONFIGURATION REQUIRED**.
* Render (backend): production env vars (`DATABASE_URL`, `SUPABASE_URL`,
  `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`, `RESEND_API_KEY`), CORS,
  health-check — **EXTERNAL CONFIGURATION REQUIRED**.
* Observability/alerting dashboards (Vercel/Render/Supabase/Resend) —
  **EXTERNAL CONFIGURATION REQUIRED**.
* Backup/PITR retention + restore-testing schedule — **EXTERNAL CONFIGURATION
  REQUIRED / BUSINESS DECISION REQUIRED**.


## 22. Deferred commercial / billing work

D35 §2.8 / §25 ratified: **billing is intentionally deferred** and provider-
neutral. The schema remains Stripe-ready (`customer_subscriptions`,
`usage_tracking`, `consultant_billing` + `manual_extraction_credit`) but no
provider SDK, webhook, checkout, subscription, credit or usage-billing code
exists. A new customer can exist in an unpaid/trial/pending-commercial state
inside the V3 workspace (no invented commercial state machine).

Documented dependency for the next commercial phase (D35-A / D35-B, NOT
started): final pricing + commercial model (incl. manual-extraction
pricing/metering), payment-provider selection, entitlement/usage metering —
**BUSINESS DECISION REQUIRED / FUTURE**.

## 23. Remaining findings

| # | Severity | Finding | Classification |
|---|---|---|---|
| 1 | — | Commercial model + billing implementation | BUSINESS DECISION REQUIRED / FUTURE (D35-A/D35-B) |
| 2 | P2 | Remaining transactional email templates (invitation, report-ready, issue, onboarding variants) | P2/FUTURE |
| 3 | P2 | Backup/DR restore-testing schedule + retention/RPO/RTO targets | EXTERNAL CONFIGURATION REQUIRED / BUSINESS DECISION REQUIRED |
| 4 | P2 | Observability/alerting dashboards (Vercel/Render/Supabase/Resend) | EXTERNAL CONFIGURATION REQUIRED |
| 5 | P2 | Legacy `/dashboard/*` full code removal (redirect already implemented) | FUTURE |
| 6 | P2 | Public Services/Contact/FAQ pages (no invented pricing) | FUTURE (pricing = BUSINESS DECISION REQUIRED) |
| 7 | P3 | Document-binary export | FUTURE (D34) |
| 8 | P3 | "Automated CSV Data Stream Mapping" landing claim vs no automated extraction pipeline | FUTURE (content/business) |
| 9 | P0/P1 | **None found.** Security green: RLS 15/15, cross-org/live denials 403, evidence chain untouched, private storage + signed URLs authoritative, main-DB protection guard intact. | — |

**P0 blockers:** none. **P1 journey blockers:** none remain for the approved
self-service path (billing is intentionally deferred, not a blocker). **P2:**
documented above. Nothing inflated.

## 24. Exact files changed (D35)

Backend:
- `backend/api/v3_organizations.py` (org creation + onboarding audit/email)
- `backend/api/v3_discovery.py` (optional `organization_id` onboarding variants)
- `backend/data/organizations.py` (`create_with_owner`, membership guard,
  `company_number` persistence, `joined_at`→`created_at` fix)
- `backend/data/discovery.py` (`%%` SQL fix; onboarding repo methods)
- `backend/data/tenant.py` (schema-correct member columns)
- `backend/domain/discovery.py` (nullable `organization_id`, `created_by`)
- `backend/tests/unit/api/test_self_service_onboarding.py` (NEW)
- `backend/tests/unit/api/fakes.py` (onboarding fakes)
- `backend/tests/integration/test_v3_rls_behavior.py` (+4 D35 RLS tests)

Frontend:
- `frontend/src/SelfServiceSignup.jsx` (NEW)
- `frontend/src/OnboardingPage.jsx` (NEW)
- `frontend/src/v3/api.js`
- `frontend/src/App.js`
- `frontend/src/v3/components/V3Layout.jsx`
- `frontend/src/BetaSignup.jsx`
- `frontend/src/Login.js`
- `frontend/src/v3/v3.css`
- `frontend/src/v3/__tests__/api.test.js`

Database:
- `supabase/migrations/20260824010000_d35_self_service_onboarding.sql` (NEW)

Evidence:
- `screenshots/d35_customer_onboarding/` (NEW — 9 PNG + manifest)
- `docs/audit/cline/CARBONTALLY_V3_D35_TECHNICAL_REMEDIATION_REPORT.md` (NEW)
- `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` (§48 — D35
  record, see §29)

## 25. Final production-readiness classification

**D35: COMPLETE.**

* Self-service signup / org creation / owner assignment / existing-data
  adoption / V3 `/home` routing: **IMPLEMENTED + VERIFIED** (unit, RLS,
  frontend, build, live smoke, screenshots).
* Security: **VERIFIED** — RLS intact, cross-org/consultant/entity/staff/
  storage/evidence/messaging authorization preserved, main-DB guard intact.
* Commercial/billing: **INTENTIONALLY DEFERRED** (provider-neutral; next phase
  decision list in §22).
* Production operations (backup/DR, observability, Supabase/Resend/Vercel/
  Render config): **DOCUMENTED / EXTERNAL CONFIGURATION REQUIRED** — not
  falsely claimed as implemented.

**HARD STOP.** D35 ends here. No D35-A, D35-B, D36, Stripe/payment-provider
integration, pricing implementation, synthetic-document validation, 5,787-PDF
processing or Blog CMS work was started.

