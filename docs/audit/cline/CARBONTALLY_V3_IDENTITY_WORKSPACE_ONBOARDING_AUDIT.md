# CarbonTally V3 — Identity, Actor, Workspace & Onboarding Audit

| | |
|---|---|
| Document type | READ-ONLY AUDIT + IMPLEMENTATION PLAN (no code/data/RLS changes) |
| Project | CarbonTally |
| Architecture baseline | CarbonTally V3 — **commit `d4dcca1eb11f86bcae497815c8592d688a7e305f`** (`origin/main`, 70 commits, post git-history-remediation canonical baseline) |
| Old baseline superseded | `9458067c073bdaedae2a621b9cee42e419f14a75` (NOT used) |
| Date | 2026-08-25 |
| Author | Cline (read-only analysis of the clean clone `/tmp/carbontally_audit`) |
| Status | AUDIT + DESIGN ONLY — **HARD STOP, nothing modified** |
| Authority references | `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` (design authority), `docs/architecture/CARBONTALLY_V3_TERMINOLOGY_AND_DOMAIN_GLOSSARY.md`, migrations under `supabase/migrations/`, `backend/`, `frontend/src/` |

---

## 1. Executive Summary

**Problem (PO-reported):** every CarbonTally test user — organisation owner, admin, member, viewer, consultant, consultant member, operator, reviewer, QC, staff admin, entity staff — is presented with the same **"Welcome to CarbonTally / Set up your organisation…"** onboarding flow, and an organisation **owner can get through onboarding inappropriately**.

**Root cause (two layers):**

1. **ARCHITECTURAL (primary, code-level).** The post-login destination is decided by a **frontend probe chain** — `resolvePostLoginPath()` (`frontend/src/v3/api.js:107`) and the equivalent guard inside the D35 `OnboardingPage.jsx` — that probes three server endpoints (org membership → staff → consultant) and **treats ANY failure (404, 403, 500, timeout) as "brand-new customer"**, routing the user into the D35 customer-org onboarding (`/onboarding`). There is **no single server-authoritative actor-classification / workspace-resolution endpoint** and **no onboarding-state column**; "needs onboarding" is *inferred from the absence of DB rows*. Two competing routing systems coexist: the legacy `Dashboard.checkUserStatus` (`App.js`) keys off **client-claim `user_metadata.company_name`** and can force the legacy `CompanyNamePrompt` overlay ("Welcome to CarbonTally! … enter your organization name"), while the V3 path keys off DB probes. Any data gap, RLS misconfiguration, or backend hiccup therefore misroutes *every* user into customer-org creation.

2. **DATA (secondary, environment-level).** The repository contains **no reproducible demo data**: `supabase/seed.sql` is a data-empty schema dump; `demodatagen/data_output/users.csv`/`organizations.csv` are **0 bytes**; the demo identities (`*@demo.carbontally.local`) and their organisation/staff/consultant/entity relationships exist **only in untracked `local_backups/` scripts** (`seed_demo_data.sql`, `mint_tokens.py`) and the live DB. A freshly provisioned environment (new local Supabase / CI) therefore has auth users but **no `organization_members`, `staff_profiles`, `consultant_profiles`, or `processing_entities` rows** → all three role probes fail → **every user lands on "Set up your organisation"**. This exactly reproduces the PO observation.

**Owner-failure mechanisms (each real, evidence-cited in §8):** (a) the D35 create-org guard `POST /api/v3/organizations` and the routing guard share the *same* membership lookup, so when membership data is missing they fail *together* and an existing owner can create a second org; (b) the guard checks **only org memberships** — it does **not** prevent staff or consultant identities from creating a customer org; (c) the onboarding guard swallows probe *errors* (500/timeout) as "no identity" and a 12 s fallback timer unblocks the form even during slow resolution.

**Verdict on the D35 "Set up your organisation" flow:** it is *correct for its intended audience* (brand-new external customer with no relationship), **incorrect as a universal fallback** for any authenticated user whose probes fail.

**Recommendation (high level):** introduce a single **server-authoritative "actor/workspace resolution" endpoint** (`GET /api/v3/me/context`) returning actor type, workspace, membership, onboarding state, and destination; route from that, never from a frontend fallback chain; add explicit onboarding-state columns; gate `POST /api/v3/organizations` to exclude staff/consultant identities as well as existing members; make demo personas **repo-reproducible** (checked-in seed SQL) so every environment has coherent actor data. Full phased plan in §24.

---

## 2. Current Actor Model — Evidence Matrix

Evidence sources: schema (`00000000000000_init_schema.sql`, `20260810000000_v3m1_processing_entities.sql`), RLS (`20260803000000_rc2_rls.sql`, `20260810050000_v3m6_entity_rls.sql`), backend (`auth.py`, `api/operations_auth.py`, `api/consultant_auth.py`, `api/v3_organizations.py`), design authority `CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` §3.

| Actor | Database representation | Role source | Workspace | Membership | Invitation mechanism | Authentication | Authorization | Onboarding requirement | Destination |
|---|---|---|---|---|---|---|---|---|---|
| Customer org **owner** | `organization_members` (`role='owner'`, `is_active`) | org membership CHECK | Customer `/home` | org membership row | D35 org creation (self, becomes owner) or admin-invite | Supabase auth | `require_org_admin`; RLS `is_org_member`+admin | Only when no membership found | `/home` (D35 onboarding if probes fail) |
| Customer org **admin** | `organization_members` (`role='admin'`) | same | Customer `/home` | org row | admin invite | Supabase auth | `require_org_admin`; RLS admin | None (has org) | `/home` |
| Customer org **member** | `organization_members` (`role='member'`) | same | Customer `/home` | org row | admin invite (`team.py` POST `/{org_id}/invite` direct insert) | Supabase auth | `require_org_member`; RLS `is_org_member` | None (has org) | `/home` |
| Customer org **viewer** | `organization_members` (`role='viewer'`) | same | Customer `/home` | org row | admin invite | Supabase auth | `require_org_member` (read) | None | `/home` |
| **Consultant firm owner** | `consultant_profiles` + `consultant_firm_members` (`role='owner'`, active) | firm member row | Consultant `/consultant` | firm membership | provisioned server-side (`add_firm_member`); self `POST /api/v3/consultants/me` creates profile only, not firm-membership | Supabase auth | `require_consultant`; `ensure_consultant_org_access` via active `consultant_clients` | Only when no firm membership found | `/consultant` |
| **Consultant member** | `consultant_firm_members` (`role='manager'/'consultant'/'viewer'`) | firm member row | Consultant `/consultant` | firm membership | `add_firm_member` (firm owner/admin) | Supabase auth | `require_consultant` + `can_*` flags | None | `/consultant` |
| **Staff operator (internal)** | `staff_profiles` (`role_id`→`staff_roles.name='operator'`, `entity_id IS NULL`, active) | `staff_roles.permissions` jsonb | Ops `/ops` | staff profile | CarbonTally admin provisioning | Supabase auth | `require_staff` + `can_process`; internal scope | None | `/ops` |
| **Staff reviewer (internal)** | `staff_roles.name='reviewer'` | same | Ops `/ops` | staff profile | admin | Supabase auth | `require_staff` + `can_review` | None | `/ops` |
| **Staff QC (internal)** | `staff_roles.name='qc_specialist'` | same | Ops `/ops` | staff profile | admin | Supabase auth | `require_staff` + `can_process`+`can_review` | None | `/ops` |
| **Staff admin (CarbonTally)** | `staff_roles.name='admin'`, `entity_id IS NULL` | same | Ops `/ops` + admin surfaces | staff profile | admin | Supabase auth | `require_staff`; `is_admin` only if internal + admin role (D20 guard) | None | `/ops` |
| **Processing/entity staff** | `staff_profiles` with `entity_id` set (FK→`processing_entities`) | `staff_roles` | Entity workspace inside `/ops` (`v3/ops/EntityExtractionWorkspace.jsx`) | staff profile scoped to entity | entity admin provisioning | Supabase auth | `require_staff` + entity scope (`is_entity_member` RLS; `_entity_workspace_guard`) | None | `/ops` (entity-scoped) |
| **Processing service (entity)** | `processing_entities` (active/remediation/suspended/terminated) | — (an organisation, not a user) | — | entity staff profile(s) | — | — | RLS `is_entity_member` | — | — |

**Not invented / absent:** there is **no separate "CarbonTally owner" actor** — the closest is the internal staff `admin` role (`is_admin` = staff + `entity_id IS NULL` + admin-named role, `auth.py`). There is **no "individual / personal user" actor** — every customer user is org-scoped.

## 3. Current Role Model

Four **independent** role families coexist (design authority §10 — do not merge):

1. **Organisation roles** — `organization_members.role` CHECK: `owner | admin | member | viewer` (customer tenancy only). The `roles` reference table exists but the org vocab is enforced by the CHECK constraint; `roles` seed inserts are **not present in migrations** (empty in a fresh DB).
2. **Staff roles** — `staff_roles.name`: `operator | reviewer | qc_specialist | admin` (vocabulary table; permissions jsonb `can_view_all, can_manage_staff, can_manage_roles, can_process, can_review, …`). Seed data not in migrations.
3. **Consultant firm roles** — `consultant_firm_members.role`: `owner | manager | consultant | viewer`; authorization via `can_*` booleans (`can_manage_clients, can_upload_documents, can_generate_reports, can_manage_team`).
4. **Derived `AuthUser` roles** — `user | staff | <staff_role_name> | org_owner | org_admin | org_member | org_viewer`, computed in `get_current_user` (`backend/auth.py:143-330`). Precedence: **staff wins over org** (`if is_staff … elif is_org_member …`). `is_admin` (global CarbonTally admin) is scoped to internal staff only (D20 guard). A user with no staff/org row → `role="user"`.

**Actor vs Role vs Workspace vs Membership vs Permission — actual distinction:**

- **Actor** is NOT a stored column. It is *inferred* from which DB tables a user appears in (org membership row ⇒ customer; staff profile ⇒ staff; consultant profile+firm-member ⇒ consultant). A single user may hold **multiple actor identities** (e.g., a user who is both an org member and a staff member — possible in schema, resolved with staff precedence).
- **Role** is stored per family (CHECK constraints / vocabulary tables / firm-member role column).
- **Workspace** is a *conceptual* surface keyed to actor family (`/home`, `/consultant`, `/ops`); there is no `workspaces` table. Context selection: customer = primary org; consultant = localStorage active client; ops = caller's staff identity.
- **Membership** is the row that ties a user to a tenancy (org / firm / staff profile / entity).
- **Permission** is enforced server-side per family (RLS for org; `staff_roles.permissions` jsonb; consultant `can_*` booleans).

**Architectural ambiguity (recorded, not resolved):** the same user can be a member of multiple families simultaneously; there is no explicit precedence *document* for cross-family routing (staff-first is hard-coded in `auth.py`), and the frontend probe order (org → staff → consultant) differs from the backend precedence (staff → org). This mismatch is one source of the routing confusion.

## 4. Current Workspace Model

Implemented surfaces (evidence: `App.js` routes 1955-2114, `frontend/src/v3/components/V3Layout.jsx`, `RoleRoute.jsx`, design authority §9):

| Workspace | Route | Implemented? | Who can reach it |
|---|---|---|---|
| Public marketing site | `/`, `/pricing`, `/about`, `/privacy`, `/terms`, `/cookies` | ✅ IMPLEMENTED | anon |
| Login / signup | `/login`, `/signup` (D35 self-service), `/beta/signup`, `/beta-login`, `/auth/callback`, `/auth/magic` | ✅ IMPLEMENTED | anon |
| D35 self-service onboarding | `/onboarding` (`OnboardingPage.jsx`) | ✅ IMPLEMENTED | any authenticated user whose three role probes fail |
| Customer workspace | `/home`, `/emissions`, `/documents`, `/processing`, `/existing-data`, `/messaging`, `/issues`, `/notifications`, `/reports`, `/reports/:id`, `/billing`, `/organization` | ✅ IMPLEMENTED (V3Layout + customer pages) | `RoleRoute requireOrg` (active org member) |
| Consultant workspace | `/consultant` (`ConsultantPage.jsx`) | ✅ IMPLEMENTED | `RoleRoute requireConsultant` |
| Ops workspace (internal + entity) | `/ops` (`OperationsPage.jsx`; entity workspace for entity staff) | ✅ IMPLEMENTED | `RoleRoute requireStaff` |
| Legacy monolith | `/dashboard/*` → legacy `Dashboard` + `CompanyNamePrompt`/`OnboardingWizard` | ✅ IMPLEMENTED (legacy, partially superseded) | any signed-in user (beta login redirects here) |

**Not implemented (explicitly):**
- **Personal / individual workspace** — **NOT IMPLEMENTED**. No `user_type='individual'` handling; `users.user_type` column is unused outside tests. An individual must create an organisation and become its owner (current-only customer model).
- **Organisation workspace as a first-class object** — implemented only as the customer surface keyed to the primary org.
- **Consultant signup classification** — **NOT IMPLEMENTED** (see §9).
- **Processing-service workspace outside `/ops`** — entity staff share the `/ops` surface with an entity scope.

## 5. Current Membership Model

| Family | Table | Row semantics | Guard |
|---|---|---|---|
| Customer org | `organization_members` (org_id, user_id, role CHECK `owner/admin/member/viewer`, `is_active`) | active membership; `is_active` is the toggle (no hard delete via RLS) | `require_org_member`/`require_org_admin`; RLS `is_org_member` |
| Consultant firm | `consultant_firm_members` (firm_id→`consultant_profiles`, user_id, role, `can_*`, `client_access uuid[]`, `is_active`) | firm membership; `require_consultant` needs profile + **active** firm-member row | RLS `is_org_consultant` for org reads (via `consultant_clients`/`client_access`) |
| Staff | `staff_profiles` (user_id, `role_id`→`staff_roles`, `is_active`, `entity_id` NULL=internal) | staff identity; `require_staff` needs active profile | `require_staff`/`require_internal_staff`/entity scope |
| Processing entity | `processing_entities` (status active/remediation/suspended/terminated) | the service organisation | RLS `is_entity_member` |

**Key gap:** `organization_members.user_id` FK → `public.users(id)`. A Supabase Auth signup lives in `auth.users` only; the D35 migration adds a trigger mirroring `auth.users → public.users` (SECURITY DEFINER, never blocks signup). **Demo users created before D35 (or via the admin API without the mirror) have no `public.users` row** — so membership/staff/consultant rows either cannot be inserted (FK) or silently resolve nothing → probes fail → onboarding.

## 6. Current Invitation Model

- **Legacy org invite** — `POST /api/organizations/{org_id}/invite` (`backend/routes/organizations/team.py:97`): requires the invitee to **already have an auth account** ("Please ask them to sign up first"), then **directly inserts** the `organization_members` row. No acceptance step, no token.
- **V3 invitation** — `POST /api/v3/organizations/{org_id}/invitations` (`v3_organizations.py:543`, org-admin only) writes `user_invitations` (token, status, expiry). **But there is NO acceptance endpoint/route in the repo** — the emailed link `https://carbontally.co.uk/accept-invite?token=…` (`backend/utils/email.py:127`) has **no matching route**. Token-based invitations are effectively **dead-ended**.
- **No invitation-aware onboarding** — nothing routes a pending-invitee's first login to their destination org; destination depends entirely on the org-membership probe succeeding.


## 7. Current Onboarding Flow — Exact Trace

**Login/signup entry points → destination:**

1. `Login.js` (password/OAuth/magic-link): on success calls `resolvePostLoginPath()` → `navigate(path)`.
2. `SelfServiceSignup.jsx` (D35): `supabase.auth.signUp({ data: { full_name, company_name, is_beta_user:false, onboarding:true }})` → if session, `resolvePostLoginPath()`, else "check your email" → `/auth/callback` → `resolvePostLoginPath()`.
3. `AuthCallback.js`, `MagicLink.jsx`: `resolvePostLoginPath()`.
4. `BetaSignup.jsx`: creates auth user with beta metadata; legacy `BetaLogin.jsx` redirects existing sessions to `/dashboard` (legacy surface!).

**`resolvePostLoginPath()` (`frontend/src/v3/api.js:107-121`) — THE routing decision:**
```
1. resolveV3Organization()  → GET /api/organizations/members/user/{user.id}  (legacy endpoint)
       · 200 + primary_organization  → return '/home'
       · 404 (no active membership) → null   · error → null
2. getOpsMe()                → GET /api/v3/ops/me   (require_staff)
       · 200 → return '/ops'      · 403 → throw → catch → continue
3. getConsultantProfile()    → GET /api/v3/consultants/me  (require_consultant)
       · 200 → return '/consultant'   · 403 → throw → catch → continue
4. return '/onboarding'      ← DEFAULT for ANY user who fails all three
```

**The three probes:**
- `GET /api/organizations/members/user/{id}` (`backend/routes/organizations/members.py:72`): SELF-only; queries `organization_members` (is_active=true) via service-role client → **404 if no row** ("User is not an active member of any organization"). Response `primary_organization` + `primary_role`.
- `GET /api/v3/ops/me` (`backend/api/v3_operations.py:472`): `require_staff` → resolves `staff_profiles` by user + `is_active` + role permissions → **403 if not an active staff profile**.
- `GET /api/v3/consultants/me` (`backend/api/v3_consultants.py:205`): `require_consultant` → `consultant_profiles` by user + active `consultant_firm_members` row → **403 if not an active firm member**.

**Then:** `/onboarding` → `OnboardingPage.jsx` (D35). Its own guard repeats the SAME three probes in the same order (org→staff→consultant), each in `try/catch` that **swallows errors as "not that identity"**, with a **12-second fallback timer** that unblocks the form even while resolution is still in flight. If all probes fail → the D35 page renders:

> **"Welcome to CarbonTally — Set up your organisation to start measuring, verifying and reporting your carbon emissions."**

with steps: details → review (candidates) → verify → decision (USE ALL/PARTIAL/DISCARD) → created (OWNER).

**WHY all test users reach it (the exact mechanism):**
- The routing chain has **no actor classification and no server-side onboarding state** — it only knows "membership? staff? consultant?" and its default is *customer onboarding*.
- **Any one of the following makes EVERY user fall through:** (a) missing/inactive `organization_members` rows; (b) missing `staff_profiles`; (c) missing `consultant_profiles`/firm-member rows; (d) `public.users` mirror rows absent (FK/join failures); (e) probe timeout (v3Fetch aborts > timeout and throws — treated as "not that identity"); (f) RLS blocks the service-role client only if credentials misconfigured.
- Additionally `V3Layout.jsx` re-checks and **force-redirects any user with no org+staff+consultant to `/onboarding`** — so even a user who manually reaches `/home` is pushed back.
- And the **legacy** path: `BetaLogin` → `/dashboard` → legacy `Dashboard.checkUserStatus` (`App.js:806-854`) keys on **`user_metadata.company_name`** (a client/JWT claim) and shows the legacy `CompanyNamePrompt` overlay **"Welcome to CarbonTally! … enter your organization name"** whenever that metadata is missing — independent of any DB membership.

**Conclusion:** the symptom is the *combination* of a fragile universal fallback (code) and missing demo-identity rows in the tested environment (data).

## 8. Owner Failure Analysis

**Reported symptom:** an organisation owner can get through the current onboarding flow inappropriately.

**Evidence-based mechanisms:**

1. **Shared-membership-dependency collapse (primary).** The routing probe (`resolveV3Organization` → membership endpoint) and the D35 create-org guard (`POST /api/v3/organizations` → `get_active_memberships_for_user`) both depend on the SAME `organization_members` lookup. When membership data is missing, incoherent (wrong user_id), or `public.users` mirror rows are absent, **both fail together**: the owner is misrouted to `/onboarding`, and the create endpoint sees "no membership" → creates a **second organisation** with the caller as OWNER (`create_with_owner`, one transaction). The two guards cannot protect each other because they share one data dependency.

2. **Staff/consultant identities are not guarded.** `POST /api/v3/organizations` checks **only org memberships** (`v3_organizations.py:192-199`). A staff or consultant user whose org probe fails (or who deliberately calls the endpoint) can create a customer organisation and become its owner. There is no check for active `staff_profiles` or `consultant_firm_members` rows.

3. **Probe-error swallowing + fallback timer.** `OnboardingPage.jsx` guard wraps each probe in `try/catch` treating any error (500, timeout) as "not that identity", and a 12 s `fallbackTimer` sets `checking=false` regardless of whether resolution completed. A legitimate owner therefore sees the onboarding form during/after a backend hiccup and may submit it.

4. **Client-claim metadata path (legacy).** `Dashboard.checkUserStatus` decides onboarding need purely from `user_metadata.company_name` (JWT claim) — not from the DB. A demo owner without that metadata sees the legacy "Welcome to CarbonTally! … enter your organization name" overlay; saving calls the legacy `POST /api/organizations/` which requires **global `admin` role** (`management.py:253`) → 403 for owners (dead-end, not an escalation, but still wrong UX).

5. **No onboarding-state marker.** Nothing records "onboarding completed" for an actor; the state is re-inferred on every login. A user who finished D35 onboarding but later has their membership deactivated returns to onboarding again.

**Root-cause classification (PO list):** the primary driver is a **combination**: (a) *missing actor classification* and *missing server-side onboarding state*, (b) *incorrect redirect* (universal fallback to customer onboarding), (c) *seed/demo-data problem* (identities not reproducible from repo), and (d) an *authorization gap* (create-org guard omits staff/consultant). It is **not** primarily an RLS or frontend-only-routing bug; the backend D35 endpoint is well-guarded *when membership data exists* (verified by `backend/tests/unit/api/test_self_service_onboarding.py`: `test_create_org_rejects_user_with_existing_membership`, `test_onboarding_choice_by_different_user_denied`).

## 9. Consultant Flow

- **How CarbonTally knows a user is a consultant (authoritative):** server-side rows only — `consultant_profiles` (one per firm, `user_id`) + an **active** `consultant_firm_members` row. `require_consultant` demands both (`consultant_auth.py:_resolve_context`). The `/consultant` route is gated by `RoleRoute requireConsultant`.
- **Signup classification: NOT IMPLEMENTED.** `POST /api/v3/consultants/me` (`v3_consultants.py:226`) lets *any* user create a `consultant_profiles` row — but **not** the required firm-member row (that requires server-side `add_firm_member`). Without the member row, `require_consultant` still fails and the user is not routed to `/consultant`. So consultant identity is **provisioned**, never client-selected.
- **Client access:** consultant → org access is via **active** `consultant_clients` rows (D15); RLS `is_org_consultant` for org tenant reads.
- **Current onboarding behaviour:** a consultant whose firm-member row is missing/inactive fails the consultant probe → falls through → `/onboarding` (customer org creation!). **This is wrong and must be fixed** — a consultant must never see "Set up your organisation".

## 10. Human Processing Service Flow

- **Representation:** `processing_entities` (first-class service organisation; lifecycle active/remediation/suspended/terminated). Its users are `staff_profiles` rows with `entity_id` set (FK `staff_profiles_entity_id_fkey`, V3M1).
- **Assignment:** `manual_extraction_batches.entity_id` (D22) + `processing_assignments`; entity staff process **only assigned** work; internal staff (`entity_id IS NULL`) run the ops-wide pipeline.
- **Data boundaries:** RLS `is_entity_member(entity)` (V3M6) scopes entity staff to their own entity rows (`manual_review_queue`, `upload_batches`, `issues`); backend `_entity_workspace_guard` re-checks per item; entity staff are **structurally denied** the customer-context/manual-extraction-pipeline surfaces.
- **Onboarding/destination:** entity staff are staff — `require_staff` resolves → `/ops` renders the **entity workspace** for `profile.entity_id` staff. No dedicated onboarding. If the `staff_profiles` row is missing/inactive → fails the staff probe → **falls through to `/onboarding`** (wrong).

## 11. Internal Staff Flow

- owner/admin/reviewer/QC/operator = `staff_profiles` (internal: `entity_id IS NULL`) + `staff_roles.permissions`; `get_current_user` sets `role` = staff role name, `is_admin` only for internal admin (D20).
- Destination: `/ops` (OperationsPage). Staff dashboard/admin surfaces (`StaffDashboard.jsx`, `AdminPage`) render by permission.
- **Current bug surface:** any staff user whose `staff_profiles` row is missing/inactive, or whose `public.users` mirror row is absent, fails `require_staff` → falls to `/onboarding` (customer org creation). Internal staff must **never** enter customer onboarding.

## 12. Customer Organisation Flow

- **Who can create:** any authenticated user with **no active org membership** (D35 guard) — and (gap) even staff/consultant identities. Legacy `POST /api/organizations/` requires global `admin`.
- **Duplicate detection (D19/D35):** `lookup_candidates(name, company_number, email_domain, contact_email)` — exact company-number match **blocks** with 409 `discovery_required` unless acknowledged; weaker signals are informational only. Adoption requires D19 verification (email code / staff-mediated) + explicit USE ALL/PARTIAL/DISCARD.
- **Country / company registration number:** captured in the org form (`country` GB/IE/DE/FR/NL/US/AU/CA/Other; `company_number` optional) → `organizations` columns.
- **Ownership:** `create_with_owner` inserts org + owner membership in one service-role transaction.
- **Membership creation:** owner row only; other members via admin invite.
- **Onboarding completion recorded:** **NO** — no flag; re-inferred each login.
- **Verdict:** the flow is correct for a **brand-new customer**; it is wrong as the fallback for staff/consultant/existing members.

## 13. Beta Access Flow

- **Frontend:** `BetaSignup.jsx` (`/beta/signup?code=…`) validates the code by **directly querying `beta_access_codes`** through the anon-key Supabase client (`supabase.from('beta_access_codes').select('code,email,status,expires_at').eq('code', code).single()`), then signs up with `is_beta_user:true, beta_code` metadata; `BetaLogin.jsx` handles magic-link auto-login → legacy `/dashboard`.
- **Backend:** `backend/routes/admin/beta.py` — admin-only CRUD (`GET/POST /codes`, `PUT /codes/{id}/status`, `DELETE`, `GET/POST /users`, `PUT /users/{id}/access`, `/codes/validate/{code}`, stats).
- **Database:** `beta_access_codes` (code, email, status, expires_at, used_at, magic_token) + `beta_users` (user_id, email, beta_code, access_level, invited_by).
- **RLS:** **no policies found on `beta_access_codes`/`beta_users`** in any migration → **deny-by-default** for `anon`/`authenticated`. Consequence: the frontend direct query **always fails** ("Invalid beta access code") in a correctly locked DB — the public beta path is effectively **non-functional** (only the admin API, service-role, works).
- **PO decision context:** CarbonTally is **not currently accepting customers**. Recommendation: (a) keep the backend/admin infrastructure (no removal), (b) **publicly disable** the self-service entry points (`/signup`, `/beta/signup`, beta-code validation) behind an environment flag (e.g., `VITE_PUBLIC_SIGNUP_ENABLED=false`) so controlled internal/test users can still use them, (c) fix or remove the frontend direct-query code validation (route through the backend admin endpoint or a deliberately-public validation endpoint with rate limiting), (d) retain tables/migrations for future use.

## 14. Demo User Analysis

The demo identities (`*@demo.carbontally.local`) are **documented** (design authority §17; D30 report) but **not reproducible from the repository**:

| Demo user | Intended actor/role | Intended org/entity/firm | Expected destination |
|---|---|---|---|
| `owner@demo.carbontally.local` | Customer org owner | CarbonTally Demo Ltd | `/home` |
| `admin@demo.carbontally.local` | Customer org admin | Demo Ltd | `/home` |
| `member@demo.carbontally.local` | Customer org member | Demo Ltd | `/home` |
| `viewer@demo.carbontally.local` | Customer org viewer | Demo Ltd | `/home` |
| `consultant@demo.carbontally.local` | Consultant firm owner | Net Zero Advisory | `/consultant` |
| `consultant-member@demo.carbontally.local` | Consultant firm member | own firm + active client grant (D30) | `/consultant` |
| `operator@demo.carbontally.local` | Staff operator (internal) | `entity_id IS NULL` | `/ops` |
| `reviewer@demo.carbontally.local` | Staff reviewer (internal) | `entity_id IS NULL` | `/ops` |
| `qc@demo.carbontally.local` | Staff QC specialist (internal) | `entity_id IS NULL` | `/ops` |
| `staff-admin@demo.carbontally.local` | Staff admin (CarbonTally internal) | `entity_id IS NULL` | `/ops` |
| `entity-staff@demo.carbontally.local` | Entity staff (operator) | Entity Beta (`f77e6b5f-…`) | `/ops` (entity workspace) |

**Repo evidence for "why all reach onboarding":** none of these emails appear in the repository (`grep -r demo.carbontally .` → only docs references). The provisioning scripts (`local_backups/seed_demo_data.sql`, `local_backups/mint_tokens.py`) are **untracked**. `supabase/seed.sql` contains **zero data rows** (no `COPY` blocks), and `demodatagen/data_output/users.csv` + `organizations.csv` are **0 bytes**. Therefore any environment built solely from the repository has **no org memberships, no staff profiles, no consultant profiles, no entities** → every auth user fails all three routing probes → **"Set up your organisation"**. This is the concrete, evidence-backed explanation of the PO observation.

## 15. Demo Data Architecture

- **In-repo generators:** `demodatagen/` (Python) generates orgs, users, facilities, documents, carbon data etc. — but its committed `data_output/*.csv` are empty; generation output is not committed. `seed.ts` (`demoConfig`) is a Prisma-based seed for a *different* target (not the Supabase schema used at runtime).
- **Live demo data source:** `local_backups/seed_demo_data.sql` (untracked) — per D30 report it seeds org, 4 customer members, facilities/assets/suppliers, documents, extraction batches, review queue, QC, reports, emissions, consultant firm + active client grant, Entity Alpha/Beta, entity staff, consultant member. **Not in the repo.**
- **Coverage gaps (design authority §18-19):** no multi-org (single org); no second consultant client; no processing-entity lifecycle rows beyond fixtures; entity staff and consultant-member exist only as D30 transient fixtures.
- **Conclusion:** the demo architecture is *rich* but **not version-controlled** — the single most important reproducibility defect behind the observed symptom.

## 16. Authorization Analysis

Server-side enforcement points verified:
- `auth.py get_current_user` (staff-first, then org; `is_admin` internal-only; `role="user"` fallback).
- Legacy `require_auth / require_org_member / require_org_admin / require_admin`; V3 `require_staff / require_internal_staff / require_entity_scope / require_consultant / ensure_consultant_org_access / ensure_org_access` (every org-scoped V3 endpoint re-authorizes).
- `POST /api/v3/organizations`: anonymous 401; existing-membership 409; company-number exact match 409; `create_with_owner` transactional ownership; D19 adoption binding (created_by-only verify/choice — `test_onboarding_choice_by_different_user_denied`).
- Legacy membership endpoint: **self-only** (403 for other users) — no org enumeration.

**Onboarding-specific security gaps:**
1. `POST /api/v3/organizations` does not exclude **active staff or consultant identities** from creating a customer org (org-membership check only).
2. The frontend routing chain has **no server-side arbitration** — a user who is a member/staff/consultant can be shown customer onboarding; backend guards prevent data damage but not the misroute.
3. `user_metadata.company_name` is treated as identity state in the legacy path (client-claim trust).
4. Beta code validation depends on client-side direct DB query (RLS-locked → non-functional; if policies were loosened → public code guessing; no rate limit).

## 17. RLS Analysis

- **Floor:** RC2 RLS enables RLS on every public table, zero policies originally → deny-by-default; service-role/postgres bypass by definition (the backend repos rely on this; **every V3 endpoint re-authorizes server-side**).
- **Key helpers (SECURITY DEFINER, search_path pinned):** `is_org_member(org)` (active member of active org via `auth.uid()`), `is_org_active`, `is_org_admin_or_owner`, `is_org_consultant(org)` (active firm member with client grant), `is_entity_member(entity)` (V3M6).
- **Table policies relevant to onboarding/identity:** `organizations` SELECT (member OR consultant), UPDATE (member); `users` SELECT/UPDATE self; `organization_members` select-self-or-admin / insert-admin / update-self / update-admin (role vocab CHECK; self-escalation moved to app layer); `consultant_profiles` select own; `consultant_firm_members` select self-or-team-admin; V3M6 entity policies on `processing_entities`/`staff_profiles`/`manual_review_queue`/`upload_batches`/`issues`; `p9_rls_recursion_fix` resolves recursive org/admin policies.
- **Mismatch findings:**
  - `beta_access_codes` / `beta_users`: **no policies** → deny-by-default → frontend beta validation cannot work (direct client query).
  - Onboarding itself does **not** rely on RLS for the *decision* (that is API probes); RLS protects the *data* once a workspace is entered. No RLS change is required for the fix — the identity tables' SELECT policies for `authenticated` are minimal, so direct client lookup of "am I staff/consultant" is intentionally unavailable (backend probes only). **No RLS changes made or recommended as part of onboarding routing** (backend probes are authoritative).

## 18. Target Actor Model (proposed, not implemented)

One **actor type** per user, server-resolved, with ordered precedence that is documented and single-sourced:

| Actor type | Resolution (server-side, one endpoint) | Onboarding gate |
|---|---|---|
| CarbonTally staff (internal) | active `staff_profiles` (`entity_id IS NULL`) | none — straight to `/ops` |
| Processing-entity staff | active `staff_profiles` (`entity_id` set, entity active) | none — `/ops` entity workspace |
| Consultant (owner/member) | active `consultant_profiles` + active firm member | none — `/consultant` (unless onboarding incomplete) |
| Customer org member (owner/admin/member/viewer) | active `organization_members` | none — `/home` |
| New external user | no identity rows, no pending invite | D35 onboarding (with actor-choice) |
| Invited external user | no identity rows BUT a live invitation | invitation redemption → destination org |
| Individual (future, per PO decision) | no org, selected "individual" at onboarding | individual workspace (to be designed) |

Rules: a user with **staff** identity always lands in `/ops` first (internal staff must never enter customer org creation). A **consultant** always lands in `/consultant`. An **org member** always lands in `/home`. Only a user with **no** server-side identity may enter onboarding — and onboarding **must first** check for a live invitation and a prior onboarding-state.

## 19. Target Workspace Model (proposed)

Keep the four implemented surfaces (`/home` customer, `/consultant`, `/ops` incl. entity scope, `/onboarding`) and add, per PO decision only: **individual/personal workspace** (future), **invitation-acceptance surface** (needed now — currently dead-end `/accept-invite`). No `workspaces` table is proposed — workspace remains a resolved surface keyed to actor type, but the resolution becomes server-authoritative and recorded in an onboarding-state column.

## 20. Target Onboarding Architecture (proposed)

```
login / signup
   └─► GET /api/v3/me/context          ← NEW single server-authoritative resolver
         returns: { actor_type, workspaces[], primary_workspace,
                    organization?, role?, staff?, consultant?, entity?,
                    pending_invitation?, onboarding_required, onboarding_state,
                    destination: '/home' | '/consultant' | '/ops' | '/onboarding' | '/invitation' }
         precedence: staff (internal) > staff (entity) > consultant > org member
                     > pending invitation > onboarding_required > new customer
   └─► frontend navigates ONLY from destination — never from a client fallback chain
   └─► /onboarding guard: on mount, re-call /me/context; if destination !== '/onboarding'
                          redirect immediately (no try/catch fallthrough, no 12s timer)
   └─► New-customer onboarding: WHO ARE YOU? (individual / own org / consultant / provider)
       └─► server-side classification is authoritative:
            consultant/provider/staff selections require an existing server-side
            provisioning row or an invitation — otherwise rejected with a clear
            "your organisation must invite you" message; never silently create a
            conflicting identity
   └─► Invited user: /accept-invite?token= → server redeems token → creates active
                     membership → destination = the org workspace
   └─► On completion of any onboarding: record onboarding_state ('completed', timestamp)
       on the actor; the resolver returns the stable destination thereafter.
```

Design constraints: backend authoritative; no client role claims; every workspace guarded by existing `RoleRoute`/RLS; onboarding cannot create orgs for staff/consultants/invited-elsewhere identities.

## 21. Onboarding Matrix (target)

| Actor | New/Invited | Identification method | Onboarding required? | Onboarding screens | Workspace | Landing page | Server authorization | Demo user | Status |
|---|---|---|---|---|---|---|---|---|---|
| Customer org owner | New | D35 self-service (no identity rows) | YES | D35: details → review → verify → decision → created (OWNER) | Customer | `/home` | `POST /api/v3/organizations` (401 anon, 409 member, 409 company-number, create_with_owner) | `owner@demo…` | INTENDED ✓ |
| Customer org owner | Existing | membership row | NO | — | Customer | `/home` | `require_org_admin`; RLS | `owner@demo…` | CURRENTLY BROKEN (probe fallthrough) |
| Customer org admin | Invited/existing | membership row | NO | — | Customer | `/home` | `require_org_admin` | `admin@demo…` | BROKEN (data) |
| Customer org member | Invited/existing | membership row | NO | — | Customer | `/home` | `require_org_member` | `member@demo…` | BROKEN (data) |
| Customer org viewer | Invited/existing | membership row | NO | — | Customer | `/home` | `require_org_member` (read) | `viewer@demo…` | BROKEN (data) |
| Consultant (owner/member) | Provisioned (invited) | `consultant_profiles` + active firm member | NO | — | Consultant | `/consultant` | `require_consultant`; `ensure_consultant_org_access` | `consultant@demo…`, `consultant-member@demo…` | BROKEN (data) |
| Staff operator | Provisioned | active `staff_profiles`, internal | NO | — | Ops | `/ops` | `require_staff` + `can_process` | `operator@demo…` | BROKEN (data) |
| Staff reviewer | Provisioned | active staff profile | NO | — | Ops | `/ops` | `require_staff` + `can_review` | `reviewer@demo…` | BROKEN (data) |
| Staff QC | Provisioned | active staff profile | NO | — | Ops | `/ops` | `require_staff` | `qc@demo…` | BROKEN (data) |
| Staff admin (CarbonTally) | Provisioned | active staff profile, internal admin | NO | — | Ops + admin | `/ops` | `require_staff`; `is_admin` | `staff-admin@demo…` | BROKEN (data) |
| Entity staff | Provisioned | active staff profile + `entity_id` | NO | — | Entity workspace | `/ops` (entity) | `require_staff` + entity scope; RLS `is_entity_member` | `entity-staff@demo…` | BROKEN (data) |
| Invited member (token) | Invited | `user_invitations` token | YES (redemption) | Accept-invite screen (to be built) | Customer | org workspace | token redemption endpoint (to be built) | — | NOT IMPLEMENTED (dead `/accept-invite`) |
| Brand-new external user | New | no identity rows | YES | D35 (+ WHO-ARE-YOU actor choice) | Customer | `/onboarding` | D35 guards | — | INTENDED ✓ |

## 22. Demo Persona Matrix (proposed — no data created)

| Persona | Email | Actor type | Role | Workspace | Organisation | Relationships | Expected landing | Expected permissions | Expected demo data |
|---|---|---|---|---|---|---|---|---|---|
| Individual | `individual@demo.carbontally.local` | individual (future) | — | (future personal) | none | none | onboarding → individual (if approved) | own data only | own emissions uploads |
| Org owner | `owner@demo.carbontally.local` | customer | owner | Customer | CarbonTally Demo Ltd | owner; invites admins | `/home` | org admin (manage org, members, billing, suppliers, facilities) | full org data (assets/facilities/emissions/reports) |
| Org admin | `admin@demo.carbontally.local` | customer | admin | Customer | Demo Ltd | admin | `/home` | org admin (no ownership transfer) | same org data |
| Org member | `member@demo.carbontally.local` | customer | member | Customer | Demo Ltd | member | `/home` | member (upload, edit) | same org data |
| Org viewer | `viewer@demo.carbontally.local` | customer | viewer | Customer | Demo Ltd | viewer | `/home` | member-read only | same org data (read) |
| Consultant owner | `consultant@demo.carbontally.local` | consultant | owner | Consultant | Net Zero Advisory | active client grant on Demo Ltd | `/consultant` | all `can_*`; client org read | firm clients, branded portal |
| Consultant member | `consultant-member@demo.carbontally.local` | consultant | member | Consultant | own firm | active client grant (D30) | `/consultant` | member `can_*` subset | firm client data |
| Processing-service owner | `entity-owner@demo.carbontally.local` | entity staff (owner/admin of entity) | admin | Entity workspace | Processing Entity Alpha | entity staff | `/ops` (entity) | entity-scoped ops, staff mgmt | assigned batches/items |
| Processing-service member | `entity-staff@demo.carbontally.local` | entity staff | operator | Entity workspace | Entity Beta | entity staff (operator) | `/ops` (entity) | `can_process` entity-scoped | assigned extraction items |
| CarbonTally admin | `staff-admin@demo.carbontally.local` | staff (internal) | admin | Ops | — | internal | `/ops` | `can_manage_staff, can_view_all…` | ops-wide dashboard |
| CarbonTally staff | `staff@demo.carbontally.local` | staff (internal) | operator/reviewer | Ops | — | internal | `/ops` | `can_process`/`can_review` | ops queues |
| Reviewer | `reviewer@demo.carbontally.local` | staff (internal) | reviewer | Ops | — | internal | `/ops` | `can_review, can_view_all` | review queue |
| QC | `qc@demo.carbontally.local` | staff (internal) | qc_specialist | Ops | — | internal | `/ops` | `can_process+can_review` | QC checks |

Each persona above already has (or would have) the server rows that the resolver keys on; the demo seed must be **checked into the repo** so these destinations hold in every environment.

## 23. Open Product Decisions (genuine only)

1. **Individual / personal account model** — should CarbonTally offer a personal workspace for a solo user, or must every customer create an organisation? (Schema already has unused `users.user_type`.)
2. **Consultant signup policy** — may a user self-select "consultant" at onboarding (creating a firm profile), or is consultant identity strictly invitation/provisioning-only? (Current code: provisioning-only, but the self-service `POST /api/v3/consultants/me` profile creation suggests intent.)
3. **Human processing service onboarding policy** — who provisions a processing entity and its staff, and should entity owners have an onboarding flow at all, or is it admin-only?
4. **Public customer signup timing** — CarbonTally is not currently accepting customers: when does public `/signup` reopen, and what gates it (waitlist, invite-only, beta codes)?
5. **Beta access retirement** — keep `beta_access_codes` infra for internal/test users only, or retire publicly and move test provisioning to a non-public path?
6. **Organisation claim rules** — may a user "claim" an existing organisation by company number + email-domain verification without staff mediation, or is D19 email-verification the only self-serve claim path?
7. **Multi-org and dual identities** — if a user is both a consultant firm member and a customer org member, which workspace wins? (Frontend currently: org first; backend precedence: staff first.)
8. **Invitation UX** — should token invitations be re-activated (implement `/accept-invite`) or is the direct-membership legacy invite the supported path?

## 24. Implementation Plan (proposed — NOT executed in this task)

**PHASE A — Identity / actor classification.** Add `actor_type` + `onboarding_state` columns (nullable, additive) or a small `user_onboarding` table; build server-side `GET /api/v3/me/context` resolver (staff→entity→consultant→org→invitation→new) with explicit precedence; unit tests for precedence and error paths. *(Identity resolution only — no routing change yet.)*

**PHASE B — Workspace detection.** Extend the resolver to return full workspace set + primary destination; keep existing role endpoints as sources; add integration tests covering member/staff/consultant/entity/new/invited.

**PHASE C — Onboarding routing.** Replace `resolvePostLoginPath()` and the `OnboardingPage` guard with a single call to `/me/context`; remove the 12 s fallback timer and error-swallowing fallthrough; `V3Layout` and `RoleRoute` redirect from the resolver destination; delete/replace the legacy `CompanyNamePrompt` dependency in `Dashboard` (keep legacy routes working but non-blocking); frontend tests for the new router.

**PHASE D — Organisation onboarding.** Keep D35 flow for new customers; strengthen `POST /api/v3/organizations` to 409 for any user with an active **staff or consultant** identity as well as org membership; record onboarding_state on completion; surface "you already belong to an organisation" messaging instead of a bare 409.

**PHASE E — Consultant onboarding.** Decide (PO) the self-service vs invitation-only consultant path; implement the approved path (e.g., invitation-based firm-member creation that completes the consultant identity, or gated self-service that creates profile + owner firm-member row in one transaction); consultant landing always `/consultant`.

**PHASE F — Human Processing Services onboarding.** Admin-only entity provisioning (existing `admin_entities.py`) + staff profile creation; entity staff get `/ops` entity workspace with no onboarding; no self-service entity creation without a decision.

**PHASE G — Internal CarbonTally user routing.** Internal staff always `/ops`; staff admin surfaces guarded by `is_admin`; regression test that no staff identity can reach `/onboarding` or create an org.

**PHASE H — Demo/test persona data.** Check in a repo-reproducible demo seed (SQL or generator) covering the §22 persona matrix (org + members, consultant firm + member + active client grant, two processing entities + entity staff, internal staff roles, reviewer/QC/operator, and a brand-new-user fixture); keep demo emails pinned to `*@demo.carbontally.local`; document seeding in README.

**PHASE I — Authorization/security verification.** Pen-test-style checks that onboarding cannot create unauthorized orgs, claim orgs, gain consultant/processing/staff access, bypass invitation/membership, escalate role, or cross workspace isolation; verify backend enforcement (not just UI).

**PHASE J — End-to-end testing.** Smoke suite logging in as every persona and asserting the exact landing workspace, permissions, and denials; browser-walk the new-customer onboarding; verify RLS denials for cross-tenant probes.

## 25. Testing Strategy

- **Unit:** resolver precedence; org-create guards (member/staff/consultant/anon); invitation redemption; beta-code validation via API; `me/context` for every actor family.
- **Integration (existing harness, `backend/tests/integration/`):** D35 onboarding (create/lookup/verify/choice) incl. denied different-user choice; RLS behavior tests (org/consultant/entity isolation); post-login destination tests for all 11 demo personas + new user.
- **Frontend:** `resolvePostLoginPath`/new router unit tests; `OnboardingPage` guard tests (redirect-on-context; no fallthrough on error); V3Layout redirect tests.
- **Manual (browser) walk:** one login per persona asserting landing + nav visibility + denials; new-signup journey end-to-end; invited-user redemption.
- **Security:** attempt to reach each workspace cross-actor; attempt org creation as staff/consultant; attempt claim of another org via company number.

## 26. Risks

- **Data absence is the immediate symptom driver** — without a repo-reproducible demo seed, every future environment repeats the failure; the fix must include PHASE H or the symptom persists.
- **Frontend probe refactor touches every login path** (Login, MagicLink, OAuth callback, signup, V3Layout, RoleRoute) — risk of regressions; mitigate with the existing frontend test suite + PHASE J.
- **Two routing systems** must converge; leaving the legacy `Dashboard`/`CompanyNamePrompt` alive risks future divergence — decide whether legacy `/dashboard/*` is deprecated.
- **Multi-family identities** (staff+consultant, org+staff) have no documented precedence — resolver precedence must be explicit and agreed.
- **Beta-code RLS lockdown** makes the public beta non-functional today; loosening RLS without rate-limiting risks code-guessing — do not loosen without a decision.
- **Invitation dead-end** (`/accept-invite` no route) means token invitations are unsafe to advertise.

## 27. Final Recommendation

1. **Immediate (correct the symptom):** make demo personas repo-reproducible (PHASE H) and route post-login from a single server-authoritative `/me/context` (PHASES A–C). This alone resolves "all users see Set up your organisation".
2. **Authorization hardening (PHASE I):** extend the D35 org-create guard to staff/consultant identities and record onboarding state (PHASE D).
3. **Decision-driven (PHASES E, F, G, §23):** consultant signup policy, entity onboarding policy, internal routing, beta retirement, invitation reactivation — each requires a PO decision before implementation.
4. **Do not remove** any backend infra (beta codes, invitations, consultant tables) until the decisions in §23 are made.

---

**HARD STOP — this task was AUDIT + DESIGN ONLY.** No application source, database, migration, RLS, demo data, seed data, authentication, or frontend routing was modified; nothing was committed or pushed. Awaiting PO decisions on §23 before any implementation phase begins.
