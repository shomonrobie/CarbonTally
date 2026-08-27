# CarbonTally V3 — Identity, Actor, Workspace & Onboarding
# IMPLEMENTATION PHASE 1 — AUTHORITATIVE CONTEXT + ONBOARDING ROUTING

| | |
|---|---|
| Document type | Implementation + verification report |
| Task | Identity-Workspace-Onboarding Phase 1 (server-authoritative context + onboarding routing) |
| Canonical baseline | `d4dcca1eb11f86bcae497815c8592d688a7e305f` (`origin/main`, 70 commits) |
| Superseded baseline | `9458067c073bdaedae2a621b9cee42e419f14a75` (NOT used) |
| Date | 2026-08-25 |
| Author | Cline (implementation engineer) |
| Execution mode | Incremental, minimal correct fix — no redesign, no commit, no push |
| Status | COMPLETE in isolated canonical clone `/tmp/carbontally_audit` — **HARD STOP** |
| Design authorities | `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md`, `docs/audit/cline/CARBONTALLY_V3_IDENTITY_WORKSPACE_ONBOARDING_AUDIT.md` |

---

## 1. Baseline Verification

| Check | Result |
|---|---|
| Live remote `origin/main` | `d4dcca1eb11f86bcae497815c8592d688a7e305f` (fetched; lease-verified) |
| Clean clone used for work | `/tmp/carbontally_audit` — HEAD `d4dcca1e…`, clean at start |
| Developer working tree | **UNTOUCHED** — no reset/clean/checkout/stash/delete; `0` staged; existing 546 modified / 151 deleted / 58 untracked preserved |
| Pristine comparison worktree | `/tmp/pristine` at `d4dcca1e` (proves pre-existing failures only) |
| Backend test env | Dev venv `/home/shomonrobie/carbon_tally/backend/.venv` used **read-only** |
| Pre-existing test failures | `tests/unit/api/test_v3_customer_admin.py` — 5 `requires_admin` tests fail **identically** on pristine `d4dcca1e` (500 vs 403, env/venv-related). **Not introduced by this task.** |

## 2. Files Inspected

**Backend:** `api/router.py`, `api/dependencies.py` (RepositoryBundle, ensure_org_access), `api/v3_organizations.py` (D35 create), `api/v3_operations.py` (`/ops/me`), `api/v3_consultants.py` (`/consultants/me`), `api/operations_auth.py`, `api/consultant_auth.py`, `auth.py` (get_current_user precedence), `data/invitations.py`, `data/staff.py`, `data/consultants.py`, `data/organizations.py`, `data/processing_entities.py`, `data/roles.py`, `domain/staff.py`, `domain/partners.py`, `domain/organization.py`, `domain/entity.py`, `routes/organizations/members.py`, `routes/organizations/team.py`, `routes/organizations/management.py`, `routes/admin/beta.py`, `tests/unit/api/conftest.py`, `tests/unit/api/fakes.py`, `tests/unit/api/test_self_service_onboarding.py`.

**Frontend:** `v3/api.js`, `OnboardingPage.jsx`, `v3/components/V3Layout.jsx`, `v3/components/RoleRoute.jsx`, `Login.js`, `AuthCallback.js`, `MagicLink.jsx`, `SelfServiceSignup.jsx`, `BetaSignup.jsx`, `BetaLogin.jsx`, `App.js`, `v3/__tests__/api.test.js`.

**Schema/migrations:** `00000000000000_init_schema.sql` (roles, organizations, users, organization_members, user_invitations, pending_invites, beta_access_codes, staff_roles, staff_profiles, consultant_profiles, consultant_firm_members), `20260803000000_rc2_rls.sql`, `20260810000000_v3m1_processing_entities.sql`, `20260810050000_v3m6_entity_rls.sql`, `20260822000000_p9_rls_recursion_fix.sql`, `20260824010000_d35_self_service_onboarding.sql`, `supabase/seed.sql`, `demodatagen/`, `seed.ts`.

## 3. Architecture Findings (confirmed from the audit)

1. Post-login routing was a **frontend probe chain** (`resolvePostLoginPath` + the D35 `OnboardingPage` guard): org → staff → consultant, with **any** failure (404/403/500/timeout/network) treated as "new customer → `/onboarding`". A 12 s fallback timer unblocked the onboarding form even while resolution was unresolved. This is the direct cause of every test user seeing "Set up your organisation".
2. A second, competing legacy router (`Dashboard.checkUserStatus` keyed on client-claim `user_metadata.company_name` → `CompanyNamePrompt`) was reachable via `/dashboard/*` and the beta login redirect.
3. The backend already had correct per-family authorization (`require_staff`/`require_consultant`/`require_org_*`, RLS `is_org_member`/`is_org_consultant`/`is_entity_member`) — the routing defect was a **frontend fallback**, not a backend authorization defect.
4. `GET /api/organizations/members/user/{id}` returns **404** for a user with no active membership; `GET /api/v3/ops/me` and `GET /api/v3/consultants/me` return **403** for non-staff/consultant — all three probe failures were treated as "new customer".
5. There is **no server-side onboarding-state mechanism** (Phase 2 analysis below).
6. Demo identities (`*@demo.carbontally.local`) are **not reproducible from the repository** (Phase 6 findings below).

## 4. Implementation Performed

| Phase | Change |
|---|---|
| 1 — Server context | NEW `GET /api/v3/me/context` in `backend/api/v3_context.py`; registered in `backend/api/router.py` |
| 2 — Onboarding state | **No migration.** Analysis concludes Phase 1 requires no schema change (see §7) |
| 3 — Frontend routing | `resolvePostLoginPath()` now calls `/me/context` and returns the server destination; errors **throw** (never `/onboarding`). All callers (`Login.js`, `AuthCallback.js`, `MagicLink.jsx`, `SelfServiceSignup.jsx`, `BetaSignup.jsx`, `BetaLogin.jsx`) now surface a controlled error/retry state. `V3Layout.jsx` no longer hardcodes `/onboarding` |
| 4 — Onboarding guard | `OnboardingPage.jsx` guard now calls `/me/context`, redirects immediately when `destination !== '/onboarding'`, **removed the 12 s fallback timer**, and shows an error/retry screen on context failure |
| 5 — Org-creation security | `POST /api/v3/organizations` now also rejects active **staff** and **consultant** identities (403) in addition to existing members (409) |
| 7 — Invitations (minimal) | `/me/context` detects a valid pending invitation → destination `/invitation`; minimal `frontend/src/InvitationPending.jsx` + `/invitation` route prevents invited users being treated as new customers (full acceptance = Phase 2) |
| 8 — Legacy routing | `BetaLogin.jsx` session redirect changed from legacy `/dashboard` to the server-authoritative resolver. Legacy `Dashboard`/`CompanyNamePrompt` left intact (documented, not deletable without a separate decision) |

## 5. API Contract — `GET /api/v3/me/context`

**Auth:** `Bearer` token (Supabase JWT) via `get_current_user` — unauthenticated → `401`.

**Response (200) — minimal, non-sensitive:**
```json
{
  "actor_type": "internal_staff|processing_staff|consultant|customer_owner|customer_admin|customer_member|customer_viewer|invited_customer|new_external_user",
  "workspaces": ["/ops"],
  "primary_workspace": "/ops",
  "organization": {"id","name","country","is_active"} | null,
  "role": "owner|admin|member|viewer|operator|…" | null,
  "staff": {"id","role","entity_id"} | null,
  "consultant": {"id","company_name","role"} | null,
  "entity": {"id","name","status"} | null,
  "pending_invitation": {"organization_id","organization_name","role","status","expires_at"} | null,
  "onboarding_required": false,
  "onboarding_state": "completed|pending_invitation|required",
  "destination": "/home|/consultant|/ops|/onboarding|/invitation"
}
```
**Fail-safe:** 401 unauthenticated; **500 on any unexpected error — never converted to onboarding.** Cosmetic enrichment lookups (org name, staff role name, entity detail) are guarded; classification inputs (staff / consultant / membership / invitation queries) propagate errors as 500.

**Sensitive data:** no tokens, no password hashes, no permission maps, no full rows, no cross-tenant data.

## 6. Actor Precedence (explicit, server-side)

Implemented in `backend/api/v3_context.py` exactly as specified:

1. **internal staff** — active `staff_profiles`, `entity_id IS NULL` → `/ops`
2. **processing-service staff** — active `staff_profiles`, `entity_id` set (entity returned with status) → `/ops`
3. **consultant** — active `consultant_profiles` + active `consultant_firm_members` → `/consultant`
4. **customer org member** — active `organization_members` (owner/admin/member/viewer) → `/home`
5. **pending invitation** — valid pending, unexpired `user_invitations` by email → `/invitation`
6. **genuinely new user** — no identity rows, no invitation → `/onboarding`

**Consistency note (no STOP required):** this matches the existing backend precedence in `auth.py get_current_user` (staff resolved FIRST, then org) — the previous **frontend** org-first ordering was the bug being fixed. Inactive rows never escalate (they fall through); errors never become "new customer".

## 7. Schema Decision (Phase 2) — NO MIGRATION REQUIRED FOR PHASE 1

**Existing state already available:**
- Identity rows that fully determine an actor: `organization_members` (role + is_active), `staff_profiles` (is_active + entity_id), `consultant_profiles` + `consultant_firm_members` (is_active), `user_invitations` (status + expires_at).
- D35 added `data_discovery_requests.organization_id` NULLABLE + `created_by` for **pre-org-creation discovery** — this is the D19 existing-data workflow, NOT a general onboarding-state flag.
- `users.user_type` exists but is **unused** by any code (only referenced in test helper dict keys).

**Why existing state is insufficient (for the FUTURE, not Phase 1):** nothing records "onboarding completed" as a persistent per-actor flag, so a member whose membership is later deactivated would be re-classified as new. That persistence is a Phase-2 need.

**Minimum required schema change:** NONE for Phase 1. The resolver derives `onboarding_required`/`onboarding_state` from identity rows, which is sufficient and correct for post-login routing. The audit's options (A: `actor_type`+`onboarding_state` columns; B: small `user_onboarding` table) remain open for Phase 2 when persistent completion must be recorded.

**Affected tables/columns:** none. **RLS:** none changed — the endpoint runs over the service-role pool and re-uses existing repos; RLS is unchanged and not weakened. **Migration/backfill:** none.

## 8. Migration Details

**None created.** No destructive or additive DDL. (`git status` shows no migration files.)

## 9. Frontend Routing Changes

| File | Change |
|---|---|
| `frontend/src/v3/api.js` | Added `getMeContext()` (→ `/api/v3/me/context`). Rewrote `resolvePostLoginPath()` to call it and return the authoritative `destination`; **throws** on failure/empty destination (no probe fallback). |
| `frontend/src/OnboardingPage.jsx` | Guard now calls `getMeContext()`; redirects when destination ≠ `/onboarding`; **12 s fallback timer removed**; new `contextError` + retry screen (retry re-runs resolution via `attempt`). |
| `frontend/src/v3/components/V3Layout.jsx` | No-role users are resolved via `getMeContext()`; hardcoded `navigate('/onboarding')` removed; failure stays on the (role-gated, data-protected) surface. |
| `frontend/src/Login.js` | Added `goToWorkspace()` helper — all four `resolvePostLoginPath` call sites now show a controlled error on failure. |
| `frontend/src/AuthCallback.js` | `goToWorkspace()` helper with error state. |
| `frontend/src/MagicLink.jsx` | Session path wrapped in try/catch → error state. |
| `frontend/src/SelfServiceSignup.jsx` | `.catch` on `resolvePostLoginPath` → error state. |
| `frontend/src/BetaSignup.jsx` | `.catch` on `resolvePostLoginPath` → error state. |
| `frontend/src/BetaLogin.jsx` | Session redirect changed from legacy `/dashboard` to `resolvePostLoginPath()` (prevents the legacy `CompanyNamePrompt` override). |
| `frontend/src/App.js` | New `/invitation` route (ProtectedRoute → `InvitationPending`). |
| `frontend/src/InvitationPending.jsx` | NEW minimal placeholder (Phase-2 boundary; no acceptance logic). |

## 10. Organisation-Creation Guard Changes

`POST /api/v3/organizations` (`backend/api/v3_organizations.py:create_organization`) now, in addition to the existing active-membership 409:
- active **internal staff** (`staff_profiles.is_active`, any `entity_id`) → **403** "Staff accounts cannot create customer organisations"
- active **consultant** (profile + active firm member) → **403** "Consultant accounts cannot create customer organisations"

Anonymous → 401 (unchanged); existing owner/admin/member/viewer → 409 (unchanged); inactive staff → not blocked (an inactive row is not an identity). Backend-only enforcement; no frontend reliance.

## 11. Invitation Findings

- `user_invitations` (id, email, role_id, organization_id, invited_by, token, status, expires_at) is created by `POST /api/v3/organizations/{org_id}/invitations` (org-admin).
- The email template (`backend/utils/email.py:127`) advertises `https://carbontally.co.uk/accept-invite?token=…` — **no matching backend route exists** (verified by repo-wide grep). Token redemption is a **dead-end**.
- Phase 1 implemented the resolver detection: `InvitationsRepository.get_pending_by_email(email)` (new) — status `pending` AND (`expires_at IS NULL` OR future) → `/me/context` returns `invited_customer` + destination `/invitation`.
- **Missing acceptance components (Phase-2 boundary, NOT implemented):** backend token-redemption endpoint (validate token + expiry + email match → create active membership → mark accepted), frontend acceptance page/flow, RLS-safe token handling.
- The minimal `/invitation` placeholder prevents an invited user from being pushed into customer-org creation in the interim.

## 12. Legacy Routing Findings

- `Dashboard.checkUserStatus` (`App.js`) decides onboarding need from **client-claim** `user_metadata.company_name` and can render the legacy `CompanyNamePrompt` overlay ("Welcome to CarbonTally! … enter your organization name").
- **Reachability after this task:** the legacy `Dashboard` is only rendered on `/dashboard/*` (legacy route). `Login.js`/`AuthCallback.js`/`MagicLink.jsx`/signup surfaces use `resolvePostLoginPath()` (now `/me/context`-authoritative); `BetaLogin.jsx` no longer redirects to `/dashboard`. The legacy overlay therefore **cannot override the V3 decision** via any normal login path.
- **Decision required (deferred, not done):** whether `/dashboard/*` + the legacy `Dashboard`/`CompanyNamePrompt`/`OnboardingWizard` should be deprecated/removed in a later phase. Removal was NOT performed (scope control; would require verifying every historical entry point).

## 13. Demo-Data Findings (Phase 6 investigation — verified independently)

| Claim from audit | Verification result |
|---|---|
| `supabase/seed.sql` contains no data rows | ✅ Confirmed — schema-only dump; no `COPY public…` data blocks; `grep -c demo` = 0 |
| `demodatagen/data_output/*.csv` empty | ✅ Confirmed — `users.csv` and `organizations.csv` are **0 bytes** |
| No `@demo.carbontally.local` strings in the repo | ✅ Confirmed — grep across all tracked files returns only documentation mentions |
| Demo provisioning lives in untracked `local_backups/` | ✅ Confirmed — not in `git ls-files`; only docs cite `local_backups/seed_demo_data.sql`, `local_backups/mint_tokens.py` |
| `seed.ts` targets a different model | ✅ Confirmed — Prisma seed, not the runtime Supabase schema |

**Design/implementation proposal (Phase H — NOT created):**
1. Check in a **repo-reproducible identity seed** (new migration-guarded SQL, e.g. `supabase/seed/demo_identities.sql`) creating: `public.users` mirrors, orgs (CarbonTally Demo Ltd + a second isolation org), memberships (owner/admin/member/viewer), `staff_profiles` + `staff_roles` (operator/reviewer/qc_specialist/admin, internal), two `processing_entities` + entity staff, consultant firm + owner + member + active client grant, and pending `user_invitations` rows.
2. **Auth users are provisioned OUTSIDE SQL** (Supabase Admin API / `supabase auth` CLI) using deterministic emails — **no real passwords or credentials in Git**; passwords set at runtime in each environment. Document the mechanism in the seed README.
3. A documented `npm run seed:demo` / SQL runner that loads the identity seed and then provisions auth users against the environment's service key (never committed).

## 14. Test Matrix

**Backend — `tests/unit/api/test_v3_context.py` (NEW, 17 tests, all passing):**
- new external user → `/onboarding` (onboarding_required)
- org owner / admin / member / viewer → `/home` (parametrized)
- consultant owner and consultant member → `/consultant`
- internal staff → `/ops`; processing-service staff → `/ops` (+ entity context)
- pending invitation → `/invitation`; identity wins over invitation
- missing identity rows → new user; inactive staff/consultant/membership → fall through (never escalate)
- backend error → **500, not onboarding**; unauthenticated → 401

**Backend — `tests/unit/api/test_self_service_onboarding.py` (extended, 7 new tests, all passing):**
- every org role blocked (owner/admin/member); viewer blocked
- internal staff denied (403); processing-service staff denied (403); consultant denied (403)
- inactive staff not blocked (201); missing identity data → new user can create (201)

**Frontend — `v3/__tests__/api.test.js` (extended, 5 new tests, all passing):**
- `getMeContext` exists; server destination returned; explicit `/onboarding` only on server decision; 500 and network failures **reject** (never `/onboarding`)

**Regression:** full `backend/tests/unit/api` suite run twice (modified + pristine `d4dcca1e`): failure set **identical** — only the 5 pre-existing `test_v3_customer_admin.py` failures (env/venv-related, 500-vs-403). Frontend `api.test.js` suite: 30/30 pass.

## 15. Security Verification

- Backend remains authoritative: `/me/context` is the single post-login decision; org-creation guard extended server-side.
- `user_metadata.company_name` is no longer consulted for post-login routing in any V3 path.
- No client-selected role is trusted; no frontend route protection alone grants access (RoleRoute/RLS unchanged and still enforced).
- RLS **unchanged** (no policies added/removed/weakened); the endpoint uses the service-role pool + existing repos, same as every V3 endpoint.
- `/me/context` exposes only minimal context — no tokens, no permission maps, no cross-tenant data.
- No service-role credentials or secrets introduced into frontend/repository files.
- 500/network/timeout can never become "new customer" (verified by tests).

## 16. Changed-File Manifest

**Backend (5 modified, 2 new):**
- `backend/api/router.py` (register context router)
- `backend/api/v3_context.py` **NEW**
- `backend/api/v3_organizations.py` (guard)
- `backend/data/invitations.py` (`get_pending_by_email`)
- `backend/tests/unit/api/fakes.py` (`MemoryInvitations.get_pending_by_email`)
- `backend/tests/unit/api/test_v3_context.py` **NEW**
- `backend/tests/unit/api/test_self_service_onboarding.py` (7 guard tests)

**Frontend (9 modified, 1 new):**
- `frontend/src/v3/api.js`, `frontend/src/OnboardingPage.jsx`, `frontend/src/v3/components/V3Layout.jsx`, `frontend/src/Login.js`, `frontend/src/AuthCallback.js`, `frontend/src/MagicLink.jsx`, `frontend/src/SelfServiceSignup.jsx`, `frontend/src/BetaSignup.jsx`, `frontend/src/BetaLogin.jsx`, `frontend/src/App.js`
- `frontend/src/InvitationPending.jsx` **NEW**
- `frontend/src/v3/__tests__/api.test.js` (5 tests)

**Migrations:** none. **Total:** 16 files modified/new, 458 insertions, 74 deletions.

## 17. Unresolved Issues

1. **Demo identities not repo-reproducible** — the observed "all users see onboarding" symptom in fresh environments persists until Phase H (repo seed + documented auth provisioning) is implemented.
2. **Invitation acceptance dead-end** — `/accept-invite` has no backend route; full token redemption is Phase 2 (the resolver now correctly detects invitations, but users cannot yet accept them).
3. **5 pre-existing `test_v3_customer_admin.py` failures** on this environment (500 vs 403) — pre-date this task; unrelated to identity routing.
4. **Legacy `/dashboard/*` + `CompanyNamePrompt`/`OnboardingWizard`** still exist (unreachable via V3 login paths); deprecation/removal is a separate decision.
5. **Beta-code flow** remains non-functional publicly (RLS deny-by-default on `beta_access_codes` + frontend direct query) — unchanged, awaiting PO decision.
6. **Onboarding-state persistence** (Phase 2) — no persistent "onboarding completed" record yet.

## 18. Recommendations for the Next Phase

1. **Phase H (demo seed)** first — makes every environment reproduce the 11 demo personas and their workspaces.
2. **Phase 2 (onboarding state + invitations)** — decide the persistent-state mechanism (audit options A vs B), implement `/accept-invite` redemption + UI.
3. **Beta retirement / public signup gating** decision.
4. Legacy-surface deprecation decision.
5. Re-run the 5 pre-existing `test_v3_customer_admin.py` failures under the project's canonical test environment (they may be venv-specific).

---

**HARD STOP — NO COMMIT, NO PUSH, NO D38.** All work is in the isolated canonical clone `/tmp/carbontally_audit` (uncommitted). The developer working tree is untouched. Awaiting PO instruction for commit/push and the next phase.
