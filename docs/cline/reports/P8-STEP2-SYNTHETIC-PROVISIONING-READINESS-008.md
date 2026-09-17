# Phase 8 — Synthetic Production Acceptance Tenant Provisioning Readiness

**Task ID:** `CT-STEP2-ACCEPT-008` · **Type:** READ-ONLY FORENSIC / PROVISIONING READINESS AUDIT
**Date:** 2026-09-17 · **Baseline:** `13cf6e5e139e14ba8971a983bbf234ccb5db9ce2`
**Decision:** `SYNTHETIC PROVISIONING PATH EXISTS — PO ACTION REQUIRED`

---

## 1. Task identity

Determine the **legitimate, supported** way to establish a synthetic production acceptance
organization and authenticated Owner session so `CT-STEP2-ACCEPT-007` can later be completed.
Read-only: no code, config, RLS, auth, billing, corpus or production data was changed.

## 2. Objective

Answer, with evidence: *how can CarbonTally legitimately create a synthetic production
Organization Owner without bypassing authentication, RLS or security?*

## 3. Baseline

Frontend promoted and live (`main.8f1cfa49.css`, F-07 scoped rules present); backend healthy;
OpenAPI **570 paths**; corpus **579 files** content-characterised; 24-document acceptance manifest
prepared; authenticated acceptance previously `UNVERIFIABLE`. Corpus not re-inventoried (§2).

## 4. Git state

```
branch : p8-release-reconciled        HEAD : 13cf6e5e139e14ba8971a983bbf234ccb5db9ce2
remote : origin https://github.com/shomonrobie/CarbonTally.git
status : ?? docs/cline/reports/P8-STEP2-PRODUCTION-ACCEPTANCE-007.md   staged: 0
protected ~/carbon_tally : main @ 20b7a92 — untouched
```

No stage/commit/push/reset/stash/checkout/clean. No deployment. No production mutation.

## 5. Production deployment state

Re-fetched live (`/openapi.json`, 2026-09-17): **570 paths**. Public probe: `/signup` **HTTP 200**.
Served bundle `/static/js/main.9febc8f0.js` contains `/api/v3/organizations` (1), `/onboarding`
(1), `acknowledged_candidates` (1), `auth.signUp` (1), `Set up your organisation` (1),
`Email not confirmed` (1). No 5xx observed. No env/DB credential file exists in this worktree
(`backend/.env` etc. absent), so a direct read-only production census was **not available**.

## 6. Existing authentication architecture

Source of truth: `docs/architecture/CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md`.

| Mechanism | Present | Evidence |
| --- | --- | --- |
| Supabase Auth (authoritative) | YES | frontend `supabaseClient`; signUp/signInWithPassword |
| Email + password | YES | `Login.js`; `SelfServiceSignup.jsx` (`auth.signUp`) |
| Google OAuth | YES | `signInWithOAuth provider:'google'` |
| **Public self-service sign-up** | **YES** | `frontend/src/SelfServiceSignup.jsx` (D35), route `/signup`, **live HTTP 200**, `auth.signUp` in the deployed bundle |
| Email verification | YES (Supabase-side) | spec: `/login` handles *"Email not confirmed"*; that string is in the deployed bundle |
| Beta access-code signup (optional admin mechanism) | YES | `/beta/signup` (`BetaSignup.jsx`) |
| Magic-link (`/api/auth/magic`) | route exists, not documented as a supported production method | spec |

## 7. Organization creation mechanisms

| Mechanism | Endpoint | Auth | Live in production | Notes |
| --- | --- | --- | --- | --- |
| **D35 self-service org creation** | `POST /api/v3/organizations` (201) | `require_auth()` only — any authenticated user | **YES** | `backend/api/v3_organizations.py:104`; creator becomes **OWNER**; org + owner membership in **ONE transaction** via the server-side pool; duplicate-signal guard (`409 discovery_required` unless `acknowledged_candidates`) |
| Consultant-created customer | `POST /api/v3/consultants/me/customers` (201) | `require_consultant` | **YES** | CON-1: creates the customer organisation **and provisions the owner identity server-side**, linked to the firm |
| Internal admin org create | `POST /api/organizations/` | `require_role(["admin"])` | YES | internal admin only (`backend/routes/organizations/management.py:255`) |

**Registration gate:** `services/billing.py::resolve_registration_mode` reads
`billing_commercial_config['registration_mode']`; when absent, the documented behaviour is
`DEFAULT_REGISTRATION_MODE = "OPEN_REGISTRATION"` (`domain/billing.py:30-34`) — the pre-existing D35
self-service path. If CarbonTally Administration has published `INVITATION_ONLY`, this route is
gated (403) for self-service creators. **Production row existence could not be re-verified here**
(no DB credentials in this worktree) — *condition to confirm before executing*.

## 8. User provisioning mechanisms

| Mechanism | Detail | Production-usable |
| --- | --- | --- |
| Supabase `auth.signUp` (public `/signup`) | self-service identity creation; email confirmation then `/auth/callback` | **YES** (subject to email confirmation) |
| Org invitation (`POST /api/v3/organizations/{org_id}/invitations`) | V3 invitation surface; requires an **existing org admin** | YES (adds users to an existing org; cannot create the first org) |
| Legacy invites (`/api/organizations/members/invite`, `/{member_id}/resend-invite`, `/team/{org_id}/invite`, `/{org_id}/members/bulk/invite`) | all require an existing authenticated org admin | YES (same limitation) |
| Consultant owner provisioning | `POST /api/v3/consultants/me/customers` provisions the client-owner identity server-side | YES (needs a consultant) |
| Internal staff admin tooling | `backend/tests/setup_test_orgs.py`, `setup_test_data.py`, `tools/seed_investor_demo/*` — **test/local only** | NO (test-only; would bypass production auth) |

## 9. Invitation mechanisms (the four routes named in the task)

All four are **member/user invitation only**, never org creation, and each requires an existing
authenticated org admin (legacy `/api/organizations/*`; the V3 surface is
`POST/DELETE /api/v3/organizations/{org_id}/invitations`). **None can establish the first Owner of
a brand-new organisation** — they presuppose the organisation exists. They are useful *after* a
synthetic org exists (e.g. to create the synthetic Org **Member** required by ACCEPT-007 §8).
They were **not invoked** against production.

## 10. Owner assignment mechanisms

`POST /api/v3/organizations` assigns the **creator as OWNER** atomically (documented in the
handler docstring: "the creator always owns the organization they create"). Other paths:
invitation with `role=owner` by an existing admin; consultant `POST /me/customers` (server-side
owner provisioning). No client-side owner self-assertion exists — ownership is derived
server-side from the created membership row (RLS-authorising).

## 11. Admin / staff mechanisms

`/api/v3/organizations/{org_id}/members` (+ `/roles`), `PUT /members/{member_id}`,
`POST /organizations/` (internal admin), `/api/admin/bulk/*`, `/ops` staff application
(`ensure_staff_permission`). These are internal-CarbonTally/staff surfaces; they are **not**
available to Cline (no staff identity) and were not used. Admin→Create-Organization exists for
internal admins (`POST /api/organizations/`, `require_role(["admin"])`) but requires an internal
admin identity that Cline does not possess and must not obtain.

## 12. Demo / seed mechanisms

| Mechanism | Class | Production-safe? |
| --- | --- | --- |
| `tools/seed_investor_demo/*` (1,185-identity local demo seed, `DEMO_IDENTITIES.md`) | **development/local-only** | NO — writes thousands of records; explicitly local investor machinery |
| `backend/tests/setup_test_orgs.py`, `setup_test_data.py` | **test-only** | NO — bypasses production auth/RLS |
| `demodatagen/`, `tools/carbon_data_factory/` | **generation tooling** | NO — data synthesis, not provisioning |
| `supabase/seed.sql`, `seed.ts` | **schema/seed dev** | NO |
| Public `/signup` + `/onboarding` + `POST /api/v3/organizations` | **production-supported (D35)** | **YES — this is the supported path** |
| `/beta/signup` (beta access code) | production-supported administrative mechanism | YES (requires a valid code) |

No production provisioning CLI/admin tool beyond the above was found. **No service-role,
direct-DB or JWT-forging path is needed or permitted.**

## 13. Consultant provisioning mechanisms

Supported, production-live, no DB manipulation required:
`POST /api/v3/consultants/me` (201) — consultant profile self-registration →
`POST /api/v3/consultants/me/customers` (201) — creates customer organisations (Demo Clients A/B/C)
with server-side owner identities and links them as active clients →
`POST /api/v3/consultants/me/team` for team members. Engagement requests to **pre-existing** orgs go
through `POST /me/clients` (P6-1C: pending→accept/reject, no self-authorisation). Prerequisite: an
authenticated consultant profile (itself subject to the registration gate). **Not executed.**

## 14. Production API findings

Live `/api/v3/organizations` POST; `/api/v3/organizations/{org_id}/invitations` POST/DELETE;
`/api/v3/organizations/{org_id}/members` GET/POST + `/{member_id}` GET/PUT/DELETE; the full
`/api/v3/consultants/*` self-service surface (`me`, `me/customers`, `me/clients`, `me/engagements`,
`me/team`, `me/tasks`, `me/branding`, `me/custom-domains`, `me/senders`);
`/api/v3/health/realtime`; plus legacy internal admin routes. No mutation endpoint was called.

## 15. UI findings

Public routes (spec + live checks): `/signup` (**200 live**), `/beta/signup`, `/onboarding`,
`/login`, `/auth/callback`. Deployed bundle carries `auth.signUp`, `/onboarding`,
`acknowledged_candidates`, `Set up your organisation`, `Email not confirmed`. So the **UI for
creating a synthetic tenant exists and is deployed** — the onboarding surface is the intended
entry point for a brand-new customer (D34/D35).

## 16. Security constraints

The supported path preserves Supabase Auth, server-side authorization, RLS, tenant isolation,
ownership derivation, normal session establishment and auditability. It requires **no** service-role
exposure, direct DB writes, RLS bypass, forged JWT, impersonation, undocumented privileged endpoint
or production secret. Every rejected alternative (local seed tooling, test fixtures, service-role
scripts) was **not executed**.

## 17. Supported provisioning paths

**P1 — D35 self-service (organisation tenant).** `/signup` (Supabase `auth.signUp`) → email
confirmation → `/login` → `/onboarding` → `POST /api/v3/organizations`
(`{"name":"CarbonTally Demo Acceptance — Step2-007","acknowledged_candidates":[…]}`) → creator is
OWNER → optional `POST /api/v3/organizations/{org_id}/invitations` for the synthetic Member.
**P2 — Consultant path** (§13) → Demo Clients A/B/C with server-provisioned owners.
**P3 — Internal admin path** (`POST /api/organizations/`, role `admin`) — internal CarbonTally staff
only.

## 18. Unsupported / unsafe paths (explicitly rejected)

Local investor-demo seed (1,185 identities, destructive tooling); `setup_test_orgs.py` /
`setup_test_data.py`; `demodatagen`; `supabase/seed.sql`; service-role scripts; direct SQL inserts;
JWT forging; session impersonation; using the PO's Babui Google account. None was executed.

## 19. Required PO action

Two independent supported routes exist; the PO chooses (not ranked here, per §15):

**Option A — self-service (D35) synthetic tenant.**
1. Confirm `registration_mode` is not `INVITATION_ONLY` in production
   (`billing_commercial_config` key; absent row ⇒ documented `OPEN_REGISTRATION`).
2. Complete `https://carbontally.co.uk/signup` with a **synthetic** address in a mailbox the PO
   controls (`… — Step2-007`); click the confirmation email.
3. Sign in → `/onboarding` → create `CarbonTally Demo Acceptance — Step2-007` (creator = OWNER).
4. Optionally invite a synthetic Member via `/api/v3/organizations/{org_id}/invitations`.
5. Make the synthetic session usable by Cline (supply that **synthetic test account's** email +
   password, or drive the browser for the acceptance run). The Babui account and any real customer
   credential is never involved.

**Option B — consultant path (also enables Consultant/Client acceptance).** Create a synthetic
consultant profile (`POST /api/v3/consultants/me`) → `POST /api/v3/consultants/me/customers` for
`Demo Client A/B/C — Step2-007` (owners provisioned server-side).

**Option C — internal admin.** `POST /api/organizations/` by CarbonTally internal staff; requires a
staff identity Cline does not possess and must not obtain.

**Why Cline cannot execute Option A alone:** production email verification is Supabase-side (the
spec documents the "Email not confirmed" path; the deployed bundle carries that string). Cline has
no mailbox, and creating an unconfirmed production user would violate this task (§18: 0 users).
An authorized human must therefore complete confirmation or supply a session.

## 20. Whether a synthetic tenant can now be created legitimately

**YES — via a supported production workflow** (P1 self-service or P2 consultant), subject to
(a) the registration gate being open (documented default, not re-verified here) and (b) a human
completing the Supabase email confirmation. Cline cannot complete step (b) alone.

**Correction to `CT-STEP2-ACCEPT-007` §9.** That report concluded "production exposes no
self-service signup". That conclusion was **wrong**, for two concrete reasons: (i) the signup is
executed **client-side by Supabase Auth** (`auth.signUp`), so it never appears in the FastAPI
OpenAPI path list; and (ii) my earlier filter was truncated alphabetically inside
`/api/organizations/*`, so `/api/v3/organizations` was never examined. Evidence to the contrary is
recorded in §5, §6, §7 and §15. All other ACCEPT-007 findings stand.

## 21. Exact provisioning gap

The only residual gap is **not** a missing capability but a **verification step**: whether
production has published `registration_mode = INVITATION_ONLY`. If it has, self-service org
creation returns 403 and the PO must either (a) clear/repoint that commercial-config key through the
authorised CarbonTally Administration surface, or (b) use an already-supported provisioning route
(internal admin / consultant / invitation into an existing organisation). **No new product
capability is required** to create the acceptance tenant.

## 22. Proposed next task, if required

**Not required for capability.** If the PO prefers provisioning to be a first-class, auditable,
one-click operation rather than reusing D35 onboarding, the bounded follow-up would be:
`CT-STEP2-DEMO-TENANT-PROVISIONING-009 — Approved Synthetic/Demo Tenant Provisioning`
(authorised staff actor; synthetic org creation; owner creation/invitation; audit record; tenant
isolation; no service-role exposure; revoke/reset). That is **Step 3 territory** and is
**proposed, not implemented**.

## 23. Acceptance-007 readiness

| Prerequisite | State |
| --- | --- |
| Release/backend/contract verified | ✅ (`13cf6e5`, 570 paths, no 5xx) |
| Frontend promoted + F-07 live | ✅ (`main.8f1cfa49.css`, scoped rules) |
| Corpus + 24-document manifest | ✅ (579 files preserved; manifest = ACCEPT-007 §8) |
| Synthetic authenticated session | ❌ **the only blocker** — path exists, PO action required |
| XLSX / image fixtures | No XLSX in corpus (NOT APPLICABLE); image OCR needs one synthetic image |

`CT-STEP2-ACCEPT-007` becomes **fully executable in one run** the moment a synthetic Owner session
exists; no code change is required.

## 24. Final verdict

### `SYNTHETIC PROVISIONING PATH EXISTS — PO ACTION REQUIRED`

A supported, production-live, security-preserving provisioning path exists (D35 self-service signup
+ `POST /api/v3/organizations`, optionally the consultant path). It is **not Cline-executable
alone** because Supabase email confirmation requires a human-controlled mailbox and Cline holds no
authorized synthetic session.

## 25. Required provisioning matrix

| Requirement | Existing mechanism | Actor | Production-safe? | PO action required? | Result |
| --- | --- | --- | --- | --- | --- |
| Create user | Supabase `auth.signUp` via public `/signup` (D35); invitations for existing orgs | any visitor / org admin | **YES** | **YES** (email confirmation) | PATH EXISTS |
| Create organization | `POST /api/v3/organizations` (creator becomes OWNER, one transaction) | authenticated user (subject to registration gate) | **YES** | YES (must be signed in) | PATH EXISTS |
| Assign Owner | Automatic on org creation; invitation `role=owner`; consultant `me/customers` server-side | creator / org admin / consultant | **YES** | YES | PATH EXISTS |
| Invite member | `POST /api/v3/organizations/{org_id}/invitations`; legacy invite routes | existing org admin | **YES** | YES (needs existing org) | PATH EXISTS (after org exists) |
| Create Consultant | `POST /api/v3/consultants/me` | authenticated user (gate-dependent) | **YES** | YES | PATH EXISTS |
| Create Client | `POST /api/v3/consultants/me/customers` (owner provisioned server-side) | consultant | **YES** | YES | PATH EXISTS |
| Establish login session | Supabase `signInWithPassword` / OAuth → `/auth/callback` | the synthetic user | **YES** | YES | PATH EXISTS |
| Reset/revoke synthetic account | org member `DELETE`/`PUT`; Supabase password reset; org `DELETE` by owner | owner/admin | **YES** | Optional (cleanup) | PATH EXISTS |

## 26. Production census

Direct DB census **not available** (no DB credentials in this worktree); no read-only SQL session
was attempted. Created by this task: **0 organizations, 0 users, 0 invitations, 0 documents,
0 jobs, 0 reports, 0 storage objects.** No mutation endpoint was called; only public read-only HTTP
probes (`/openapi.json`, `/`, `/signup`) were issued. Corpus: 579 files, unchanged.

```text
Current state:
STEP 2 ACCEPTANCE — WAITING FOR SYNTHETIC AUTHENTICATED SESSION

Next execution:
CT-STEP2-ACCEPT-007

Acceptance dataset:
24 content-characterised synthetic documents

Corpus:
579 files preserved and unchanged

Babui production account:
NOT USED
```



