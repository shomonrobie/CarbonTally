# CarbonTally V3 — Independent Product & Platform Audit (Flash)

**Auditor:** OpenHands (independent; read-only)
**Repository:** `https://github.com/shomonrobie/CarbonTally`
**Baseline:** commit `9458067c073bdaedae2a621b9cee42e419f14a75` — `feat(v3): commit D20-D37 commercial platform release` (HEAD of `main`, detached)
**Mode:** READ-ONLY — no source, schema, RLS, migration, test, package, database or GitHub change was made. The only artifact created is this report.
**Date:** 2026-08-24

---

## 1. Executive Summary

CarbonTally V3 is a **technically mature, security-conscious pre-commercial platform** whose engineering core (layered FastAPI backend, Supabase/Postgres + RLS, V3 React surface, self-service onboarding, evidence traceability, and a provider-neutral billing/commercial layer) is coherent and unusually well documented. The D20–D37 release adds a genuine commercial architecture (versioned plans, credit ledger, CREDIT/STANDARD modes, orders, storage metering) and closes real security gaps (D32 private storage, P9 RLS recursion fix, D37-0 billing write lockdown).

The product is **not yet coherent as a public commercial offering** because the public website and several cross-actor flows have not caught up with the engineering:

1. **The public website contradicts the product state.** It presents CarbonTally as a limited beta with a fake waitlist form (lead capture silently discarded), a pricing page that is **unreachable** (and only reachable at the `/privacy` URL), and legal pages with placeholders and fabricated team members.
2. **Team invitations are a dead-end.** The org-admin UI and API create `user_invitations` rows, but there is **no accept endpoint, no invite email, and no invitee journey** — invited users land on generic onboarding.
3. **No money can be collected.** D37 delivers plans, credits, ledger and orders, but **no payment-provider integration exists** — the commercial loop ends at "payment intent".
4. **Actor classification is fully derived from database state** (never selected during onboarding), which is sound and consistent; but multi-identity users (e.g., staff who are also org members) are routed by a fixed precedence with **no workspace switcher**, and multi-org users get an arbitrary "primary" organisation.
5. **Known repository-security item confirmed** (`backend - backup.zip` + historical `.env`/DeepSeek key) — treated as a known cleanup item per instructions, **not** re-audited here.

**Overall rating:** Engineering architecture **B+**; product/UX/website coherence **C−**. Verdict: **CONDITIONAL — not ready for public commercial launch; ready for a controlled, provisioned/partner launch** with the website + invitations + payment leg completed.

---

## 2. Audit Baseline

| Item | Value |
|---|---|
| Repository | `shomonrobie/CarbonTally` (public; the user-supplied name `carbon_tally` returns 404) |
| Audited commit | `9458067c073bdaedae2a621b9cee42e419f14a75` ("feat(v3): commit D20-D37 commercial platform release") |
| Branch | `main` (audited at detached HEAD; no moving branch followed) |
| Clone | separate `CarbonTally_audit` directory; Product Owner's local working directory untouched |
| Tree state at audit | clean (`git status --porcelain` empty); HEAD verified via `git rev-parse HEAD` |
| Scope | Product + platform analysis (actor/workspace/onboarding/journeys/UX/commercial/security); read-only |
| Excluded by instruction | credential remediation; Git-history cleanup (handled separately by Cline) |

---

## 3. Repository / Architecture Overview

Monorepo (`root package.json` = "carbon-ledger-monorepo"):

- **`backend/`** — FastAPI. Two entry points: legacy `main.py` (monolith, `backend/routes/**`) and V3 `main_v2.py` (layered `api → engines → domain → data → infra → core`; routers in `backend/api/`, mounted in `api/router.py`). Both are importable; the legacy surface is **also mounted inside the V3 app** (documented "two competing entry points" from the Architecture Conformity Gate).
- **`frontend/`** — React (CRA) customer app; V3 surface under `frontend/src/v3/**` (customer, consultant, ops, admin tabs) alongside the legacy monolith in `App.js`.
- **`admin/`** — a **separate** React + Tailwind admin dashboard app (document review, user, organization, GDPR) deployed at `/admin`.
- **`supabase/migrations/`** — 31 migrations: RC2 baseline + V3M1–M6 + D20–D37 (atomic, additive, idempotent, RLS-safe).
- **`prisma/`** — abandoned schema experiment (`schema.prisma` hardcodes `postgresql://postgres:postgres@127.0.0.1:54326/postgres`).
- **`docs/`** — unusually extensive: `docs/audit/cline/` (D20–D37 phase reports), `docs/architecture/`, `docs/cline/`, `docs/Pricing/`, `docs/Final*`.
- Miscellaneous committed artifacts: `backend - backup.zip`, `v1.9.txt`, `uploads/`, `output/`, `backups/`, `demodatagen/`, root `src/` package, scratch zips in `docs/`.

Backend scale: ~673 endpoints (264 V3 + legacy), ~108k LOC Python; frontend ~31k LOC JS/JSX.

---

## 4. Actor Model

Authoritative reference: `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` (3097 lines) — this matches the implementation.

Actors (as implemented): customer org `owner` / `admin` / `member` / `viewer` (`organization_members.role` CHECK); staff `operator` / `reviewer` / `qc_specialist` / `admin` (`staff_roles.name`, permissions JSONB); consultant firm `owner` / `manager` / `consultant` / `viewer` (`consultant_firm_members.role` + `can_*` flags); Processing Entity staff (`staff_profiles.entity_id IS NOT NULL`).

**How the system knows an actor type (CRITICAL QUESTION — traced in code):**

- `backend/auth.py get_current_user` (≈L200–290) queries **`staff_profiles`** by `user_id`+`is_active`; resolves role/permissions from **`staff_roles`** by `role_id`; then queries **`organization_members`** by `user_id` (active) for org membership; `role` is derived to `org_owner/org_admin/org_member/org_viewer`, `staff`/role-name, or `user`. `is_internal_staff` = `is_staff and not entity_id`; `is_entity_staff` = `is_staff and entity_id` (auth.py L79–86).
- Consultant identity is **not** part of `AuthUser`; it is resolved by `require_consultant` (`backend/api/consultant_auth.py`) from `consultant_profiles` + `consultant_firm_members`.
- Frontend `useActorRoles` (`frontend/src/v3/components/RoleRoute.jsx`) resolves org/staff/consultant in parallel via `resolveV3Organization()`, `getOpsMe()`, `getConsultantProfile()`.
- **Actor type is NOT selected during onboarding.** It is **derived from database state**: org membership (self-service D35 creation, legacy/seed), staff profile (provisioned by staff admin `POST /api/v3/ops/staff`), entity (`entity_id` on the staff profile), or consultant profile (seeded, or backend `POST /api/v3/consultants/me`).

---

## 5. Workspace Model

There is **no "Workspace" abstraction in code** — surfaces are role-gated route groups (actor/workspace doc §9): customer (`/home`, `/emissions`, `/documents`, `/processing`, `/issues`, `/reports`, `/messaging`, `/existing-data`, `/billing`, `/organization`), consultant (`/consultant` + `ClientWorkspace`), operations (`/ops` tabs + `WorkItemWorkspace`), Processing Entity (`/ops` renders `EntityExtractionWorkspace` for `profile.entity_id` staff).

Context selection: customer = server-resolved primary org (`resolveV3Organization` → `/api/organizations/members/user/{id}`, self-only, 403 otherwise); consultant = `localStorage('v3_consultant_active_client')` with per-request server re-auth; ops = caller's staff identity; entity = `staff_profiles.entity_id`.

---

## 6. Identity Model

- **Auth identity:** Supabase Auth JWT (email/password + Google OAuth wiring). `get_current_user` prefers `supabase.auth.get_user`; falls back to manual JWT decode with `SUPABASE_JWT_SECRET` (HS256, signature verified).
- **Customer membership identity:** `organization_members` (UNIQUE org+user; `is_active`).
- **Staff identity:** `staff_profiles` + `staff_roles` (authoritative, P1-F3/F2); general `roles` table is a legacy customer-role reference only (must NOT be treated as staff authority — doc §5.1).
- **Consultant identity:** `consultant_profiles` (firm root) + `consultant_firm_members` (role + `can_*` flags + `client_access uuid[]`).
- **Processing Entity identity:** `processing_entities` (status `active|remediation|suspended|terminated`; only `active` grants access via `is_entity_member`).
- **Users table sync:** D35 added an `auth.users → public.users` sync trigger (new signups previously could never receive a membership row — FK fix).

---

## 7. Authentication

| Area | Status | Evidence |
|---|---|---|
| Email/password signup | Implemented (self-service) | `SelfServiceSignup.jsx`; `POST /api/v3/organizations` (D35) |
| Email confirmation | Implemented; **EXTERNAL CONFIG** (Supabase templates/redirects) | D34 §29 |
| Password reset | Implemented; reset token = 32-byte urlsafe token in DB; expiry compare mixes tz-aware/naive (fragile) | `routes/auth.py` |
| Google OAuth | Wired; **EXTERNAL CONFIG** | D34 §29 |
| MFA / 2FA | **NOT implemented** (external config required; documented roadmap item) | D34 §29 |
| JWT validation | Dual path (supabase auth API + manual HS256 decode with `SUPABASE_JWT_SECRET`) | `backend/auth.py` |
| Sessions | supabase-js; access token in `localStorage` (XSS-exposed surface; no CSP header found in `frontend/public/index.html`) | `frontend/src/supabaseClient.js` |
| Post-login routing | `resolvePostLoginPath` (server-authoritative role endpoints, never localStorage) — org → `/home`; staff → `/ops`; consultant → `/consultant`; else → `/onboarding` | `frontend/src/v3/api.js` L107–122 |

---

## 8. Authorization

Defense-in-depth is consistently implemented and was verified in a prior sweep:

- **V3 API:** every endpoint re-authorizes server-side via `require_staff` → `require_internal_staff`/`require_entity_scope` → `ensure_staff_permission`; `require_org_member`/`require_org_admin` + `ensure_org_access`; `require_consultant` + `ensure_consultant_org_access` + `ensure_consultant_permission`; `require_admin`; `_require_billing_admin` + `can_manage_billing` (billing).
- **RLS:** three deny-by-default axes — `is_org_member`, `is_org_consultant`, `is_entity_member` (ADR-V3-010). D32 made the documents bucket private (storage RLS + signed URLs); P9 fixed RLS recursion; D37-0 revoked `authenticated` writes on billing state and `organizations`.
- **Service role** bypasses RLS by design; the app-layer checks are therefore the enforcement boundary (see Finding P1-7 for the one legacy gap — deactivated-member checks that omit `is_active` in legacy routes).
- **No SQL injection** found in the V3 data layer (fully parameterized asyncpg); LIMIT/OFFSET are int-cast.

---

## 9. Onboarding

### 9.1 Who sees what (traced)

| Case | Routing / behaviour |
|---|---|
| New visitor | Public `/signup` (SelfServiceSignup) → Supabase signup → `resolvePostLoginPath` → `/onboarding` |
| No org + no staff + no consultant | `/onboarding` (D35 OnboardingPage): D19 existing-data discovery (lookup → verify → USE ALL / PARTIAL / DISCARD) OR create organisation → creator becomes OWNER → `/home` |
| Existing org member | `/home` (customer workspace) |
| Staff (internal) | `/ops` |
| Staff (entity) | `/ops` → `EntityExtractionWorkspace` (never internal tabs) |
| Consultant | `/consultant` |
| **Invited user** (pending `user_invitations`) | **`/onboarding` — the invitation is never surfaced** (no accept flow; see P1-1) |
| Multi-org user | arbitrary "primary" org (`.maybe_single()`); `mode: "single"`, no switcher (P2) |
| Dual-identity user (e.g., staff + org member) | `/home` (org precedence); no workspace switcher (P1-5) |
| Beta-code user | `/beta/signup` still present as admin invite path; `/beta-login` and `/auth/magic` → `/beta-login` legacy flows remain |

### 9.2 Assessment
- D35 **fixed the D34 P1 blocker** (self-service signup + org creation) — verified in code (`SelfServiceSignup.jsx`, `POST /api/v3/organizations`, `OnboardingPage.jsx`, bounded loading guard).
- **Invited users are not handled** — a genuine onboarding hole.
- **Consultant / Processing Entity / staff onboarding do not exist as user journeys** — they are provisioning paths (ops admin creates staff profiles/entities; consultant profile is seed-only or backend-only `POST /me`). A user cannot self-select "I am a consultant" (by design — derivation, not selection), but there is also **no documented application/provisioning journey**.
- The D19 "Existing data" discovery remains permanently in the main customer nav (`V3Layout.jsx` L60) even though it is a one-time onboarding decision (P2).

---

## 10. Customer Journey

Trace (evidence-based):

| Step | State | Evidence |
|---|---|---|
| Discover | **PARTIAL / misleading** — beta framing, fake waitlist, no `/pricing`, no contact | `LandingPage.jsx`; see §14 |
| Sign up | IMPLEMENTED (self-service) | `SelfServiceSignup.jsx` |
| Authenticate | IMPLEMENTED | `Login.jsx` |
| Onboarding | IMPLEMENTED (D19 + D35) | `OnboardingPage.jsx` |
| Organisation | IMPLEMENTED (create/adopt/owner) | `POST /api/v3/organizations` |
| Dashboard | IMPLEMENTED (stats, charts, loading/error/empty states) | `v3/customer/DashboardPage.jsx` + `StateViews.jsx` |
| Data upload | IMPLEMENTED (private storage + signed URLs, D32) | `v3/customer/DocumentsPage.jsx` |
| Processing | IMPLEMENTED (manual-extraction batches/items, full state machine) | `v3/customer/ProcessingPage.jsx`; `domain/partners.py` `ITEM_STATUSES`/`WORKFLOW_STAGES` |
| Validation | IMPLEMENTED (customer review stage) | `v3_review.py`; `ITEM_STATUSES` `customer_review` |
| Evidence | IMPLEMENTED (D33) | `/api/v3/emissions/{log_id}/evidence`; `domain/evidence.py` |
| Reporting | IMPLEMENTED (generation, versions, PDF, statuses pending/generating/completed/failed) | `v3_reports.py`; `engines/report_generation.py`, `engines/pdf_render.py` |
| Billing | **PARTIAL** — plan/credits/orders visible; **no payment** | `v3/customer/BillingPage.jsx`; D37 |
| Ongoing usage | IMPLEMENTED (messages, issues, notifications) | `v3_messaging.py`, `v3_notifications.py` |

Dead ends / contradictions:
- **Invite-a-colleague → dead end** (P1-1).
- **"Request Beta Access" → lead discarded** (P1-3).
- **"Start Free Trial" → `/dashboard` → requires login, no trial exists** (`AboutUs.jsx` L240).
- **"Automated CSV Data Stream Mapping" claim** vs **no automated extraction in the production pipeline** (AI extraction engine exists in `backend/engines/` but is not referenced by any API module) (P1-6 / P2).
- **"24-hour turnaround"** (landing L552) vs **SLA default 48h** (`data/queue_settings.py`) (P2).

---

## 11. Consultant Journey

- Identity: `consultant_profiles` + firm members; permissions = `can_*` flags (`can_manage_clients`, `can_upload_documents`, `can_generate_reports`, `can_manage_team`).
- Onboarding: **no self-serve UI.** `POST /api/v3/consultants/me` exists in the backend (any authenticated user) but **no frontend calls it** (`api.js` has `getConsultantProfile` only). Provisioning is seed/data-driven.
- Workspace: `/consultant` single page — dashboard, client list, active-client switch (localStorage), `ClientWorkspace` (context/reports/dashboard/processing/issues/documents), white-label branding, client messaging. Per-request server re-auth (`_checked_client` → ownership + `ensure_consultant_org_access`).
- Client lifecycle: create/activate/suspend/end/reactivate (`v3_consultants.py`) — D15 semantics; revocation status not filtered in RLS (`is_org_consultant` ignores grant status) — flagged `[CONFLICT — FOR HUMAN DECISION]` in the actor doc §8.
- Billing: consultant-specific billing (`consultant_billing`) is REVOKEd from `authenticated` writes (D37-0); there is **no consultant billing UI/flow**.

**Contradiction:** architecture treats consultants as a first-class client-granted actor; the current UI provides no path to *become* a consultant and no consultant billing surface (doc D36 §15: "Consultant / multi-client billing readiness").

---

## 12. Processing Entity Journey

- Identity & lifecycle: `processing_entities` (status-gated), staff via `staff_profiles.entity_id`, work via `manual_extraction_batches.entity_id` (D22).
- Assignment: CarbonTally internal staff assign a batch to an internal operator **or** an active entity (`assign_batch`: exactly one of `assigned_to`/`entity_id`; reassignment audited).
- Workspace: entity staff land on `/ops` → `EntityExtractionWorkspace` (list batches/items, workspace, start/extract/map/calculate/status, mediated clarification via entity-scoped issues — no direct customer contact).
- Isolation: RLS `is_entity_member` (active entity + active staff); server-side `require_entity_scope`; verified cross-entity/cross-org 403s (D24 transient live verification).
- **Gap:** processing-entity is structurally distinguished from Customer Organisation and CarbonTally Staff correctly (D20 boundary ratified and implemented). Demo/seed coverage for entities is **absent** (actor doc §18/§19) — no seeded `processing_entities` row, so the entity journey cannot be exercised on the demo stack.

---

## 13. CarbonTally Staff Journey

- Identity: `staff_profiles.entity_id IS NULL` (internal) — they alone run the manual-extraction pipeline and ops-wide surfaces (`require_internal_staff`).
- Surfaces: `/ops` (Dashboard, Data entry, Review, QC, Staff, Roles, Entities, SLA tabs) + `WorkItemWorkspace` (split-screen), admin QC (`/api/v3/qc/*`, `require_admin`).
- Commercial administration: **Admin Commercial surface exists** (`v3_commercial.py`: overview, config, plans CRUD, ledger, subscriptions, orders, storage, payments, credits grant/adjust/reverse/refund/rollover) — gated by `can_manage_billing`.
- **Staff are NOT exposed to customer onboarding** — `OnboardingPage` guard redirects staff away (D35). This is correct.
- Residual: the **separate `admin/` app** is a second, parallel admin surface with its own auth and feature set (document review, users, orgs, GDPR) — a divergence/duplication risk (P2).

---

## 14. Public Website

Verified at the audited commit (`frontend/src/App.js` routes L1955–2107, `LandingPage.jsx`, `PricingPage.jsx`, `AboutUs.jsx`, `PrivacyPolicy.jsx`, `TermsPage.jsx`, `CookiePolicy.jsx`, `components/AppHeader.jsx`):

| Finding | Severity | Evidence |
|---|---|---|
| **No `/pricing` route.** Header/footer "Pricing" link to `/PricingPage` (no such route → catch-all → `/`). `BulkUpload.jsx` links to `/pricing` (no route). | P1 | `App.js` routes; `AppHeader.jsx`/`AppFooter.jsx` |
| **Duplicate `/privacy` route** — second `<Route path="/privacy" element={<PricingPage/>}/>` shadows `<PrivacyPolicy/>`. Privacy Policy is unreachable; the pricing page is only reachable at `/privacy`. | P1 | `App.js` L1958–1959 |
| **Fake waitlist.** Homepage/pricing CTAs ("Request Beta Access", plan buttons) open a modal whose submit is a `setTimeout` simulation; email discarded. Backend `routes/waitlist.py` is a `pass` stub. Lead capture silently lost. | P1 | `LandingPage.jsx` L43–59, L596–623; `routes/waitlist.py` |
| **Legal pages not launch-safe.** Privacy: `[Your Company Address]`, `[Your Company Number]` placeholders; "Last updated" computed client-side (always today) on all three legal pages; Terms claim "monthly or annual" billing (annual doesn't exist); Cookie Policy describes Google Analytics/HubSpot/LinkedIn/Ads cookies not implemented anywhere. | P1 | `PrivacyPolicy.jsx` L13, L26–27; `TermsPage.jsx`; `CookiePolicy.jsx` |
| **About page: fictional team** (3 profiles commented "Fictional" using `ui-avatars.com`), "trusted by businesses across the UK" (unsupported), "Start Free Trial" (no trial). | P1 | `AboutUs.jsx` L155–215, L240–241 |
| Beta framing everywhere (banner, hero badge, header "🧪 Beta", waitlist) contradicts D35 self-service + D37 commercial. | P2 | `LandingPage.jsx` (14 beta refs), `AppHeader.jsx` (9) |
| SEO effectively default: stock `<title>CarbonTally</title>`, CRA meta description, no OG/Twitter/canonical/sitemap/structured data; client-rendered SPA. | P2 | `frontend/public/index.html` |
| Footer: ~16 of ~22 links are dead `#` anchors (Blog, Documentation, Help Center, Integrations, Solutions set, socials). No Contact page. | P2 | `AppFooter`/landing footer |
| "24-hour turnaround" on landing vs 48h SLA default. | P2 | `LandingPage.jsx` L552; `data/queue_settings.py` |
| **"Join our beta program" — recommendation (see §33):** retire public beta framing and the waitlist (or replace with a real persisted endpoint if pre-launch capture is wanted); keep `/beta/signup` + `beta_access_codes` as an administrative invite mechanism; primary CTA → `Get Started` (`/signup`), secondary → working `/pricing`. Evidence: D35 made signup self-service; D37 configured commercial plans; the waitlist has no persistence. | P1 (decision) | §5 of Public Website audit (Cline), verified in code |

---

## 15. Dashboard

Customer `DashboardPage.jsx`: stat cards + charts (Recharts) + reports/activity panels; loading spinner, `ErrorState` with retry, empty states via `StateViews.jsx` — good quality. Ops `OpsDashboard.jsx` aggregates queues/metrics. Consultant dashboard = summary cards + client table. All V3 dashboards render from real org-scoped endpoints. No P1/P2 defects found beyond those already listed.

---

## 16. Information Architecture

- Terminology mostly consistent (Direct Customer / consultant / Processing Entity correctly distinguished — D28 terminology audit PASS). Residual ambiguous terms are documented in the actor doc §20 (organisation vs customer, workspace, etc.).
- Nav is long (11 items) and mixes one-time steps ("Existing data") with ongoing surfaces; no org/sworkspace switcher for multi-identity/multi-org users (P2).
- Two parallel admin surfaces (V3 `/ops` vs `admin/` app) and legacy `/dashboard` routes still mounted (duplicate definitions in `App.js` L1975–1982) create IA duplication (P2).

---

## 17. Processing Workflow

Full, coherent state machine: `BATCH_STATUSES` + `ITEM_STATUSES` (`pending → extracting → extracted → mapping → mapped → validating → validated → calculating → calculated → customer_review → approved/rejected`), orthogonal `qc_approved/qc_rejected`; `WORKFLOW_STAGES` source→extraction→mapping→validation→calculation→review→approval. Entity assignment (D22) at batch level; assignment audit. Customer review stage; QC by CarbonTally staff. No automated extraction in the pipeline (see §10).

---

## 18. Evidence

D33 evidence traceability implemented: `calculation_snapshots.source_item_id/source_file/source_page`; `GET /api/v3/emissions/{log_id}/evidence` builds an evidence record; D33.1 append-only evidence-access audit (ids only). Signed-URL source access (D32). This is the product's strongest differentiator and is well implemented.

---

## 19. Reporting

Report lifecycle `pending → generating → completed|failed` with persisted content (never "ready" unless backend confirms); versions; PDF rendering (`engines/pdf_render.py`); structured report generation engine with CO2/CO2e provenance discipline (SEAI CO2-only vs DEFRA CO2e, never relabelled); insufficient-data sections surfaced explicitly rather than fabricated. D30/D31 verified intact.

---

## 20. Billing / Commercial (D37 baseline)

| Capability | State |
|---|---|
| Versioned plan catalogue (`billing_plans`) | IMPLEMENTED — Starter $49/100cr, Professional £149/500cr, Business $399/2,000cr, Enterprise custom; **currency mix GBP/USD in the same table** (see P1-4) |
| CREDIT mode (complexity 1/2/4/quote, structured bands, ledger grant/consume/rollover/emergency/adjust/reverse/refund) | IMPLEMENTED (append-only `billing_credit_ledger`) |
| STANDARD mode (monthly allowance + usage_tracking, 402 on exhaustion) | IMPLEMENTED |
| Orders (automated/assisted/managed/storage), assisted estimate→approval, managed requests | IMPLEMENTED (`billing_orders`, immutable after completion) |
| Storage metering (server-authoritative) | IMPLEMENTED (`billing_storage_usage` from D32 `organization_files`) |
| Payment records | IMPLEMENTED as provider-neutral intents only; **NO provider adapter (Stripe/PayPal/Wise) — no money can move** (P1-2) |
| Admin Commercial surface | IMPLEMENTED (`v3_commercial.py`, `can_manage_billing`) |
| Customer Billing page | IMPLEMENTED (`BillingPage.jsx` — plan, credits, storage, orders, approve/cancel) |
| Billing security | D37-0 P0 fix: `authenticated` write grants revoked on billing state + `organizations`; entitlement is server-authoritative (`BillingService.get_entitlement`) |

**Public pricing vs D37:** plan *numbers* mostly match (Starter/Business USD, Professional GBP → page shows `$` for all — inconsistency); "Save 20%" annual toggle is **not backed** (all plans `billing_interval='month'`); "Priority processing/support" has no config field; rollover wording "planned" is stale (rollover already live); Assisted pricing page matches seed; "Exceptional — quote" tier exists in config but not on the page. Detailed table in the D20-D37 audit (verified).

---

## 21. Security Architecture

Summarised from §8 and the prior sweep; this audit performed **no destructive or exploitative testing**:

- Authentication: Supabase Auth + server-side role derivation; manual JWT fallback.
- Authorization: app-layer re-auth on every V3 endpoint + deny-by-default RLS (3 axes) + service-role trust boundary.
- Tenant isolation: org-scoped everywhere in V3; consultant grant-gated; entity work-scoped; **legacy routes have one gap** — org-membership checks that omit `is_active` (`routes/customer_documents.py` L105/203/293/464/566/681/774; `routes/organizations/data.py` L104) leave soft-deactivated members with API read access (service role bypasses RLS) — P1-7.
- Billing security: D37-0 lockdown verified.
- No SQL injection / command injection / path traversal found in V3.
- Legacy 500 handler leaks `str(exc)` to clients (info disclosure, P2); V3 error envelope is clean.

---

## 22. UX Quality

- V3 surfaces: consistent loading/error/empty states (`StateViews.jsx`), real data, no error blocks in D28 visual pass (28 screenshots). Responsive CSS present (`v3.css`). Accessibility: basic (`aria-label` on nav); no full a11y audit exists.
- Landing/legal/About pages: visually styled but content-level defects (see §14).
- The named UX benchmark does not exist in-repo (see §36); the closest doc (`docs/cline/CarbonTally UI/UX Design Principles & Guidelines v1.0.md`) is an **operator-workspace spec with empty section headers and template content** ("Babui Remote Workers") — not a usable product standard.

---

## 23. Legal / Trust

Not launch-safe: placeholders in Privacy, auto-today dates, Terms annual-billing claim, fictional team members, unsupported "trusted by" and SOC 2/AES-256 claims (partially verifiable), `legal@carbontally.com` vs domain `.co.uk`, "CarbonTally (UK) Limited" vs "CarbonTally Ltd" inconsistency. Carbon Reduction Plan page exists. No Contact page.

---

## 24. SEO

Effectively default (stock CRA title/meta; no OG/Twitter/canonical/sitemap/structured data; client-rendered SPA with no prerendering). No blog (see §25). The D20-D37 public-website audit reached the same conclusion.

---

## 25. Blog / Content Architecture

**NOT IMPLEMENTED.** `docs/architecture/CARBONTALLY_BLOG_CMS_DECISIONS.md` (ratified 2026-08-23) defines a standalone blog CMS (routes `/blog/:slug` etc., admin `/admin/blog/*`) — **no `/blog` route or blog component exists in `frontend/`**. Footer "Blog" link is a dead `#`. Content strategy is documented but zero implemented.

---

## 26. Documentation Conformity

The repo's documentation is unusually strong and **largely matches the implementation** (actor/workspace model, D34/D35/D36/D37 reports align with code). Key contradictions are listed in the Contradiction Matrix (§27) and Register (Appendix G). Most contradictions are between **marketing/legal content and product state**, not between architecture docs and code.

---

## 27. Contradiction Matrix

| # | Source A | Source B | Evidence | Actual implementation | Impact | Recommended decision |
|---|---|---|---|---|---|---|
| C1 | D34 report (2026-08-23): "billing NOT implemented, signup beta-gated" | D35/D37 reports (2026-08-23/24) | D34 §1 vs D35 §1 + D37 §1 | Signup now self-service; billing/commercial implemented | Stale documentation; readers may misjudge readiness | Treat D34 blockers as resolved; re-run journey audit post-D37 |
| C2 | Landing page "24-hour turnaround" | SLA default 48h | `LandingPage.jsx` L552 vs `data/queue_settings.py` L35 | No enforcement of 24h anywhere; SLA field default 48h | Public promise not backed by system | Align SLA to claim (24h) or soften claim |
| C3 | Landing page "Automated CSV Data Stream Mapping" | Production pipeline has no automated extraction | `LandingPage.jsx`; `AIExtractionEngine` not referenced by any API module | Manual extraction pipeline only | Misleading capability claim | Remove/adjust claim or implement automated ingestion |
| C4 | Pricing page shows all plans in USD with annual "Save 20%" | D37 seed mixes GBP/USD; all plans monthly | `PricingPage.jsx` vs `billing_plans` seed | No annual billing; Professional seeded GBP | Misleading commercial claim | Pick one currency; remove annual toggle until implemented |
| C5 | Terms claim "monthly or annual" billing | No annual billing exists | `TermsPage.jsx` vs D37 engine | Monthly only | Legal/commercial mismatch | Correct Terms |
| C6 | `resolvePostLoginPath` comment: "no role → /home" | Code returns `/onboarding` | `v3/api.js` L106 vs L121 | No-role users land on onboarding | Comment/code drift | Fix comment |
| C7 | `/privacy` should render PrivacyPolicy | Duplicate route renders PricingPage | `App.js` L1958–1959 | Privacy unreachable; pricing only at /privacy | Legal + commercial access broken | Remove duplicate route; add real `/pricing` |
| C8 | Footer/About: "Start Free Trial" | No free trial exists | `AboutUs.jsx` L240 | Button routes to `/dashboard` (login wall) | Misleading CTA | Remove or implement trial |
| C9 | Cookie Policy lists GA/HubSpot/LinkedIn/Ads | No such scripts in the codebase | `CookiePolicy.jsx` vs `frontend/public/index.html` | Cookies described are not deployed | Falsely overstates tracking | Rewrite cookie policy to actual scripts |
| C10 | `docs/Final/UI_UX-Final_Guideline.md` titled "UI/UX" | Content is a database schema | file head | Misnamed artifact | Misleading documentation | Rename/re-file |
| C11 | Actor doc §8 flags inactive client-grant revocation not enforced in RLS | `is_org_consultant` ignores grant status | `consultant_clients` + RLS | Revoked client may still read org data at RLS layer | Residual authz ambiguity | Add status filter or document decision |
| C12 | "Workspace" terminology in docs | No Workspace abstraction in code | actor doc §9 | Role-gated route groups only | Terminology/implementation gap | Either formalize or document as conceptual |
| C13 | D37 report "commercial billing completion" | No payment provider integrated | D37 §1 "No payment-provider integration" | Credits/orders/ledger, no money movement | "Billing" ≠ "collecting payment" | Be explicit on public site; plan provider adapter |
| C14 | Beta program messaging (public) | D35 self-service + D37 commercial | `LandingPage.jsx`; `AppHeader.jsx` | Beta framing contradicts product state | Suppresses signup; erodes trust | Retire public beta framing (keep invite path) |

---

## 28. Missing Concepts / Open Questions (evidence-supported)

1. **Invitation acceptance** — no accept endpoint/UI/email; how does an invited user join? (Evidence: `v3_organizations.py` create/list/revoke only; no accept.)
2. **Workspace switching** — how does a user with org+staff, or org+consultant, or 2 orgs switch surfaces? (Evidence: `resolvePostLoginPath` precedence; no switcher; `mode:"single"`.)
3. **Consultant onboarding** — how does a person become a consultant? (Backend `POST /me` exists, no UI; no application flow.)
4. **Payment collection** — who pays, how, for what? (No provider adapter; orders end at intent.)
5. **Billing ownership for consultants** — can consultants be billed independently? (No consultant billing flow; `consultant_billing` revoke-only.)
6. **Processing Entity creation** — who may create entities and under what approval? (Only staff admin, `ProcessingEntitiesTab`; no documented SLA/commercial terms for entities.)
7. **Role change handling** — what happens when a user's role changes mid-session (org member → removed, staff role changed)? (Server re-auth on each request handles enforcement; no UI/notification of role change.)
8. **Multi-org canonicality** — which org is "primary" and how is it chosen? (`.maybe_single()` — arbitrary.)
9. **Beta access codes lifecycle** — are codes consumed, expiring, revocable in UI? (`beta_access_codes` used by `/beta/signup`; admin management surface unclear.)
10. **Notification preferences** — none exist (no email digest, no per-type toggles).

---

## 29. P0 Findings

**None new in this audit.**

- The known repository-secret item (`backend - backup.zip`, historical `.env`, DeepSeek key) is a P0 **security** issue but is excluded by instruction (separate cleanup by Cline; DeepSeek key already revoked). It is NOT re-audited or remediated here. It remains a live risk until the zip is removed from the tree + history and the Supabase/Resend keys are rotated.

---

## 30. P1 Findings

| ID | Finding | Evidence |
|---|---|---|
| P1-1 | **Invitations dead-end**: admin can invite, invitee cannot join — no accept endpoint, no email, invitee lands on `/onboarding`. | `v3_organizations.py` L543–565 (create/list/revoke only); `data/invitations.py`; `resolvePostLoginPath`; `MembersTab.jsx` |
| P1-2 | **No payment collection**: provider-neutral records/orders only; commercial platform cannot collect revenue. | D37 report §13; `billing_payment_records`; `BillingPage.jsx` |
| P1-3 | **Fake waitlist discards leads** and is the primary public CTA. | `LandingPage.jsx` L43–59, L596–623; `routes/waitlist.py` (pass stub) |
| P1-4 | **Pricing/legal/commercial claims misleading**: `/privacy` shadows pricing; no `/pricing`; annual toggle; GBP/USD mix; "Start Free Trial"; fictional team; Terms annual billing. | `App.js` L1958–1959; `PricingPage.jsx`; seed migrations; `AboutUs.jsx`; `TermsPage.jsx` |
| P1-5 | **Multi-identity routing has no switcher**: org membership takes precedence over staff/consultant identity; multi-org users get arbitrary primary org. | `resolvePostLoginPath`; `members.py` L98–134 (`mode:"single"`) |
| P1-6 | **Unsupported marketing claims** ("Automated CSV Data Stream Mapping", "24-hour turnaround", "SOC 2/AES-256/SSO", "certified disclosures", "compliant reports SECR/CSRD/ESRS/ISSB") vs implementation. | `LandingPage.jsx`; engine wiring; `queue_settings.py` |
| P1-7 | **Legacy org-membership checks omit `is_active`** — soft-deactivated members retain API data access (service role bypasses RLS). | `routes/customer_documents.py` L105/203/293/464/566/681/774; `routes/organizations/data.py` L104 |

---

## 31. P2 Findings

| ID | Finding | Evidence |
|---|---|---|
| P2-1 | "Existing data" (one-time onboarding step) permanently in main nav | `V3Layout.jsx` L60 |
| P2-2 | Beta framing persists across marketing surfaces | `LandingPage.jsx` (14), `AppHeader.jsx` (9) |
| P2-3 | SEO default; no prerendering | `frontend/public/index.html` |
| P2-4 | Blog ratified but not implemented; footer links dead | `CARBONTALLY_BLOG_CMS_DECISIONS.md`; `App.js` routes |
| P2-5 | No notification preferences; in-app only, generic email templates | `v3_notifications.py` (list/read/read-all) |
| P2-6 | Legacy 500 handler leaks `str(exc)`; legacy upload echoes backend errors | `backend/main.py`; `routes/upload.py` |
| P2-7 | Parallel admin surfaces (V3 `/ops` vs `admin/` app) + legacy `/dashboard` still mounted | `admin/README.md`; `App.js` L1975–1982 |
| P2-8 | Dead/broken committed files (`main copy*.py`, `email_service.py` IndentationError, `glossary copy.py`, zips, `App copy.*`) | repo tree |
| P2-9 | `xlsx@0.18.5` (CVE-2023-30533) in frontend + admin | `package-lock.json` |
| P2-10 | Backend runtime `requirements.txt` unpinned; root `requirements.txt` has invalid `=>` | files |
| P2-11 | Tokens in localStorage, no CSP header | `supabaseClient.js`; `index.html` |
| P2-12 | No rate limiting wired | `middleware/rate_limit.py` (defined, unused) |
| P2-13 | Access-token in emails/URLs: beta invite link uses code in query param (no expiry UI) | `services/email_service.py` (broken), legacy invite |
| P2-14 | Demo/seed gaps: no Processing Entity, no 2nd consultant client, no multi-org | actor doc §18/§19 |

---

## 32. P3 Findings

- No root README; repo-root hygiene (scratch files, stray `src/` package).
- `prisma/schema.prisma` hardcodes local postgres creds.
- `resolvePostLoginPath` comment/code drift (C6).
- `docs/Final/UI_UX-Final_Guideline.md` misnamed.
- Draft pricing document remains an explicit DRAFT.
- `uploads/`, `output/`, `v1.9.txt` committed artifacts (informational).
- Password-reset expiry tz-awareness fragility.
- PII over-logging in `auth.py` prints.

---

## 33. Product Decisions Required

1. **Retire or keep "Join our beta program"?** Recommendation: **retire** public beta framing; keep `/beta/signup` + `beta_access_codes` as an admin invite path; replace the waitlist with a real persisted endpoint **only if** pre-launch lead capture is wanted; primary CTA → `Get Started` (`/signup`), secondary → a working `/pricing`. Evidence: D35 self-service signup, D37 configured plans, waitlist stub, dead `/privacy`→Pricing route.
2. **Annual billing** — implement, or remove the "Save 20%" toggle and Terms "annual" language.
3. **Canonical currency** — GBP or USD (Professional is GBP; Starter/Business USD; assisted pricing USD).
4. **Payment provider adapter** — choose Stripe/PayPal/Wise to complete the commercial loop.
5. **Invitations** — implement the accept flow (email + token route + UI) or explicitly deprecate.
6. **Consultant acquisition** — expose self-registration UI or keep provisioned-only (document it).
7. **Workspace switching** — build an actor/org switcher or document the precedence rule as final.
8. **Free trial** — implement or remove all trial claims.
9. **"Automated" capability claims** — implement automated ingestion or remove claims.
10. **SLA** — set 24h as the product promise or change the public claim.

---

## 34. Recommended D38 Sequence

1. **Website + commercial coherence** (P1-3/4/6): fix `/privacy` duplicate + add real `/pricing`; replace fake waitlist (real capture or remove); align pricing page to the D37 config (currency, annual toggle, plan-gated features); correct Terms/Cookie content; remove fictional team / trial claims or implement them.
2. **Invitations completion** (P1-1): email + token accept endpoint + invitee routing + RLS on `user_invitations`; surface in onboarding.
3. **Legacy authz gap** (P1-7): add `is_active` to legacy membership checks (or retire legacy routes).
4. **Workspace switching / multi-org** (P1-5): actor switch + explicit primary-org resolution.
5. **Payment adapter** (P1-2): provider-neutral adapter implementation per D37 §13.
6. **Rate limiting + CSP + legacy error sanitization** (P2-12/6/11).
7. **Retire legacy surfaces** (`/dashboard`, `main copy*`, broken `email_service.py`) and reconcile the `admin/` app.
8. **Demo data** (P2-14): seed a Processing Entity + second consultant client + multi-org.
9. **SEO/blog foundation** if public marketing launch is planned.

---

## 35. Overall Conformity Assessment

| Dimension | Verdict |
|---|---|
| Product architecture (V3 backend, RLS, actor model) | CONFORMANT (implementation matches actor/workspace doc) |
| Customer product | CONFORMANT (journey complete; signup/onboarding fixed in D35) |
| Consultant product | MOSTLY CONFORMANT (no acquisition journey; billing absent) |
| Processing Entity product | CONFORMANT (D22/D24; no demo seed) |
| CarbonTally staff product | CONFORMANT (ops hub + commercial admin) |
| Public website vs product state | **NON-CONFORMANT** (beta framing, fake waitlist, broken pricing/privacy) |
| Commercial/billing vs public pricing | PARTIALLY CONFORMANT (values match; currency/annual/claims diverge) |
| Documentation vs implementation | CONFORMANT with documented exceptions (C1–C14) |
| Named Product Experience Standard | **STANDARD NOT AVAILABLE IN REPOSITORY** — cannot be scored |

---

## 36. Evidence Limitations

- **Primary benchmark not available:** `CARBONTALLY_V3_PUBLIC_PRODUCT_PLATFORM_EXPERIENCE_STANDARD.md` is absent; the repo's own D20–D37 release report confirms this (§13/D38 note, line 20). Nothing was invented; the closest available documents (`docs/cline/CarbonTally UI/UX Design Principles & Guidelines v1.0.md`, `docs/Final/UI_UX-Final_Guideline.md`, `docs/audit/cline/CARBONTALLY_V3_D28_VISUAL_QA_REPORT.md`, `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md`) were used as secondary evidence.
- **No runtime/live execution:** static code + git inspection only; no server, database, or browser run performed. Claims about live behaviour (e.g., D35/D37 live verification) are cited from the repo's own reports.
- **No test suite run** (pytest/RLS/frontend not executed in this environment).
- **No destructive or exploitative testing** of any kind.
- **Known credential items excluded** by instruction.
- The two prior independent audits (`CARBONTALLY_V3_PUBLIC_WEBSITE_AND_ARCHITECTURE_AUDIT.md` and `CARBONTALLY_V3_GIT_REPOSITORY_AUDIT_AND_RELEASE_READINESS_REPORT.md`) were cross-checked and their claims re-verified against the audited commit.

---

## 37. Final Recommendation

**Do not launch publicly as a commercial product yet.** Complete the D38 sequence in §34, prioritising: (1) website/pricing/legal coherence, (2) invitation acceptance, (3) payment-provider adapter, (4) legacy authz gap and legacy-surface retirement, (5) workspace switching. A **controlled launch** (provisioned customers/consultants via CarbonTally staff, existing invitation/onboarding data, no public money-collection promise) is defensible today for the functional product.

---

## 38. HARD STOP

Read-only audit complete. No source, schema, RLS, migration, test, package, database, or repository modification was made; nothing staged, committed, pushed, or rewritten. The only artifact created is this report.

---

## Appendix A — Actor Matrix

| Actor | Representation | Role source | Permission source | Workspace | AuthZ |
|---|---|---|---|---|---|
| Org owner | `organization_members.role='owner'` | membership CHECK | `require_org_admin` + RLS | Customer | server + RLS |
| Org admin | `role='admin'` | membership | `require_org_admin` | Customer | server + RLS |
| Org member | `role='member'` | membership | `require_org_member` | Customer | server + RLS |
| Org viewer | `role='viewer'` | membership | `require_org_member` (read) | Customer | server + RLS |
| Staff operator | `staff_roles.name='operator'` | staff_roles | `can_process` | Ops | `require_internal_staff` |
| Staff reviewer | `reviewer` | staff_roles | `can_review` | Ops | `require_staff` |
| Staff QC | `qc_specialist` | staff_roles | `can_process`+`can_review` | Ops | `require_staff` |
| Staff admin | `admin` | staff_roles | `can_manage_staff`… | Ops+QC | `require_admin` |
| Consultant firm owner | `consultant_firm_members.role='owner'` | firm membership | `can_*` flags | Consultant | `require_consultant` |
| Consultant manager/consultant/viewer | firm roles | firm membership | `can_*` flags | Consultant | `require_consultant` |
| Entity staff | `staff_profiles.entity_id` | staff + entity | `require_entity_scope`/`is_entity_member` | Entity workspace | server + RLS |

## Appendix B — Workspace Matrix

| Surface | Route(s) | Actors | Context source | Status |
|---|---|---|---|---|
| Customer | `/home /emissions /documents /processing /issues /reports /messaging /existing-data /billing /organization` | org members | server primary org | IMPLEMENTED |
| Consultant | `/consultant` (+ClientWorkspace) | firm members | localStorage active client + server re-auth | IMPLEMENTED |
| Operations | `/ops` (tabs) | internal staff | staff identity | IMPLEMENTED |
| Processing Entity | `/ops` → EntityExtractionWorkspace | entity staff | `entity_id` | IMPLEMENTED |
| Legacy | `/dashboard/*` | any signed-in | legacy | STILL MOUNTED (duplicate) |

## Appendix C — Onboarding Matrix

| Case | Routing | Onboarding shown | Outcome |
|---|---|---|---|
| New signup (no roles) | `/onboarding` | D19 discovery + D35 org creation | OWNER → `/home` |
| Org member | `/home` | none | customer workspace |
| Internal staff | `/ops` | none | ops hub |
| Entity staff | `/ops` | none | entity workspace |
| Consultant | `/consultant` | none | consultant page |
| Invited user | `/onboarding` | generic (not invitation) | **dead-end** |
| Multi-org user | `/home` (arbitrary primary) | none | no switching |
| Dual-identity (staff+org) | `/home` | none | no switching |

## Appendix D — Route Inventory (summary)

- V3 API modules: `v3_organizations, v3_commercial, v3_billing, v3_documents, v3_review, v3_verifications, v3_notifications, v3_exports, v3_consultants, v3_processing, v3_processing_workflow, v3_emissions, v3_reports, v3_manual_extraction, v3_qc, v3_suppliers, v3_operations, v3_discovery, v3_messaging, v3_whitelabel, v3_reporting` + legacy `routes/**`. V3 = 264 endpoints; total incl. legacy ≈ 673.
- Frontend routes: `/`, `/login`, `/privacy` (x2), `/cookies`, `/terms`, `/about`, `/carbon-reduction-plan`, `/auth/callback`, `/signup`, `/beta/signup`, `/beta-login`, `/glossary`, `/auth/magic`, `/onboarding`, `/dashboard/*` (x2), `/home`, `/emissions`, `/documents`, `/processing`, `/existing-data`, `/messaging`, `/issues`, `/notifications`, `/reports`, `/reports/:id`, `/billing`, `/organization`, `/consultant`, `/ops`, `*`.

## Appendix E — Permission Matrix

Org roles → `require_org_member`/`require_org_admin`; staff → `staff_roles.permissions` keys (`can_view_all, can_manage_staff, can_manage_roles, can_view_organizations, can_manage_organizations, can_extract, can_process, can_review, can_approve, can_export, can_delete`); consultant → `can_manage_clients, can_upload_documents, can_generate_reports, can_manage_team`; billing admin → `can_manage_billing`. Full matrices in actor doc §13–§16 (verified consistent).

## Appendix F — Product Standard Conformity Matrix

**STANDARD NOT AVAILABLE IN REPOSITORY.** Conformity vs the *closest available* guidance: operator/QC UX spec (mostly unimplemented/empty), D28 visual QA (PASS for V3 surfaces), actor/workspace doc (CONFORMANT). Full product-experience conformance cannot be scored without the authoritative standard.

## Appendix G — Contradiction Register

See §27 (C1–C14). Each row: Source A, Source B, Evidence, Actual implementation, Impact, Recommended decision.

## Appendix H — Open Questions Register

See §28 (Q1–Q10). All supported by evidence (endpoints/files cited).

## Appendix I — Evidence Index

- `backend/auth.py` (L61–290) — actor derivation
- `backend/api/consultant_auth.py`, `backend/api/operations_auth.py` — authorization
- `backend/api/router.py` (L170–198) — V3 mounts
- `backend/api/v3_organizations.py` (L532–577) — invitations (no accept)
- `backend/api/v3_consultants.py` (L226–261) — self-registration (backend only)
- `backend/api/v3_commercial.py` (L207–734) — admin commercial
- `backend/data/invitations.py`, `backend/data/queue_settings.py` (SLA 48h)
- `backend/routes/customer_documents.py`, `backend/routes/organizations/data.py` — legacy is_active gap
- `backend/middleware/rate_limit.py` — unused
- `backend/domain/partners.py` (L13–44) — statuses
- `backend/engines/report_generation.py`, `backend/engines/pdf_render.py` — reporting
- `frontend/src/App.js` (L1955–2107) — routes incl. duplicate `/privacy`
- `frontend/src/v3/api.js` (L84–122) — resolveV3Organization + resolvePostLoginPath
- `frontend/src/v3/components/RoleRoute.jsx`, `V3Layout.jsx`
- `frontend/src/v3/ops/OperationsPage.jsx` (L41–42) — entity routing
- `frontend/src/LandingPage.jsx`, `PricingPage.jsx`, `AboutUs.jsx`, `PrivacyPolicy.jsx`, `TermsPage.jsx`, `CookiePolicy.jsx`, `components/AppHeader.jsx`
- `frontend/src/v3/consultant/ConsultantPage.jsx` — consultant journey
- `frontend/public/index.html` — SEO
- `supabase/migrations/` 20260823…D32, 20260824…D35/D37-0/D37, 20260821…D22, 20260822…P9
- `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md`
- `docs/audit/cline/CARBONTALLY_V3_D34_…`, `D35_…`, `D37_…`, `PUBLIC_WEBSITE_AND_ARCHITECTURE_AUDIT.md`, `D28_VISUAL_QA_REPORT.md`, `D32_FINAL_PRODUCT_COMPLETENESS_AUDIT.md`, `D20_D37_GIT_RELEASE_PREPARATION_REPORT.md` (line 20: standard absent)
- `admin/README.md` — separate admin app

---

*Report generated read-only by OpenHands. Baseline `9458067` unmodified.*
