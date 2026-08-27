# CarbonTally V3 — Master Completion & Security Hardening Report

| | |
|---|---|
| Document type | Phase-completion + security verification report |
| Task | Master Completion & Security Hardening (Identity/Onboarding Phase 1 completion → Processing Entity hardening → inspection phases) |
| Canonical baseline | `d4dcca1eb11f86bcae497815c8592d688a7e305f` (`origin/main`, 70 commits) |
| Superseded baseline | `9458067c073bdaedae2a621b9cee42e419f14a75` (NOT used) |
| Date | 2026-08-26 |
| Author | Cline (implementation engineer) |
| Execution location | Isolated canonical clone `/tmp/carbontally_audit` (uncommitted) — dev working tree untouched |
| Status | COMPLETE — **HARD STOP** (no commit, no push) |

---

## 1. Executive Summary

**Phase 1 (identity/onboarding) is finished:** the server-authoritative
`GET /api/v3/me/context` foundation (previous task) is preserved and the
remaining verified issues are now resolved — demo/test identities are
repo-reproducible (tracked seed + documented provisioning, no credentials),
invitation **acceptance** is implemented end-to-end (backend + frontend +
tests), legacy `/dashboard/*` routing is confirmed unreachable and the beta
code flow is documented as obsolete (D35 self-service replaces it; no RLS
weakening).

**Phase 2 (Processing Entity hardening) is complete** for every finding that
does not require a Product Owner decision: a central `ensure_entity_active`
lifecycle gate (suspended/terminated entities → 403 on all entity surfaces,
including the previously-ungated entity dashboard), legacy upload batch
IDOR fixes, signed-URL-only entity item responses (D32 model), the
`current_user.id` defect class eliminated (171 occurrences), `require_org_admin`
403-not-500 robustness, a fail-closed DB assignment-invariant migration, and a
comprehensive cross-scope security test matrix.

**Decision-gated items are documented, not guessed:** dual-scope identity
invariants (2H), legacy document route removal (2C) and legacy-app
deprecation (1C) require Product Owner confirmation; Phases 3–5 (international
processing, retention, AI providers) are inspection-only with no engineering
change.

The independent "OhOr" audit artifact is **not present in the tracked
repository**; the task's own finding descriptions (2A–2J) were treated as the
authoritative scope, cross-checked against the in-repo D34/D35 remediation
reports and the code.

## 2. Phase 1 Completed

| Item | Status |
|---|---|
| Identity / context | `GET /api/v3/me/context` (previous task) — preserved and re-verified |
| Actor precedence | internal staff → Processing Entity staff → consultant → Customer Organisation member → pending invitation → new user (unchanged, server-side) |
| Workspace routing | `resolvePostLoginPath` → server destination; all login/signup callers show controlled error states (never `/onboarding` on failure) |
| Demo identities | **NEW** — `supabase/seeds/README.md`, `supabase/seeds/demo_identities.sql` (identity rows), `supabase/seeds/provision_demo_identities.py` (Auth provisioning; refuses production; passwords never committed) |
| Invitation acceptance | **NEW** — `POST /api/v3/invitations/{token}/accept`; `InvitationPending.jsx` + `/accept-invite` route; full test matrix |
| Legacy routing | `/dashboard/*` first-match redirect confirmed (legacy Dashboard unreachable); `BetaLogin.jsx` all three `navigate('/dashboard')` call sites now use the authoritative resolver |
| Beta flow | Documented as **obsolete** — D35 `/signup` is the replacement; `beta_access_codes` remains RLS-deny-by-default (non-functional publicly); backend admin infra retained; no RLS change |

### 2A. Reproducible demo identities (1A)

- Verified (as in the previous audit): `seed.sql` data-empty; `demodatagen` CSVs
  0-byte; `local_backups/` untracked; no `@demo.carbontally.local` in tracked code.
- **Implemented:** a tracked seed directory with a persona matrix (12 personas),
  an idempotent SQL identity-row seed (`ON CONFLICT DO NOTHING`) covering
  organisations, memberships, staff roles/profiles, processing entities,
  consultant firm + members + active client grant, and a pending invitation;
  and a provisioning script that (a) refuses `CARBONTALLY_ENV=production`,
  (b) requires `CARBONTALLY_DEMO_SEED_ALLOWED=1`, (c) creates Supabase Auth
  users via the Admin API with per-run generated passwords printed once
  (never committed), and (d) applies the identity seed with the real auth
  user ids substituted. The seed is **not** a migration.
- Verified: script `py_compile` clean; persona destinations match the
  resolver (owner→`/home`, consultant→`/consultant`, staff→`/ops`, etc.).

### 2B. Invitation acceptance (1B)

- `InvitationsRepository.get_by_token` + `mark_accepted` (new); acceptance
  endpoint enforces: authenticated (401), token lookup (404), status pending
  (409 otherwise), expiry (410), email ownership (403), no duplicate
  membership (409), single-use (replay → 409), role restricted to the
  customer-org vocabulary (owner/admin/member/viewer), audit event recorded.
  Acceptance can never grant staff / Processing Entity / consultant
  privileges.
- Frontend: `InvitationPending.jsx` reads `?token=` and calls the endpoint;
  `/accept-invite` alias route registered so the emailed link resolves.

### 2C. Legacy `/dashboard/*` routing (1C)

- `App.js` declares TWO `/dashboard/*` routes; the first is
  `<Navigate to="/home" replace />` → the legacy `Dashboard` (and its
  `CompanyNamePrompt` / `OnboardingWizard` overlay) is **unreachable** via the
  primary routes (React Router first-match wins).
- No current frontend V3 surface links to `/dashboard`; `AboutUs` CTA and
  `AppHeader` navigations are covered by the `/home` redirect.
- `BetaLogin.jsx` no longer navigates to `/dashboard` in any of its three
  paths (resolver-based now).
- **Decision deferred (not removed):** the legacy `main.py` app and legacy
  `Dashboard` component remain in the tree. Formal deprecation/removal is a
  Product Owner decision (no consumer removal risk without knowing every
  historical entry point).

### 2D. Beta code flow (1D)

- Verified: `BetaSignup.jsx` validates codes by a **direct anon-key query** on
  `beta_access_codes`; the table has **no RLS policies** → deny-by-default →
  public beta validation is non-functional (as previously identified).
- D35 self-service `/signup` is the approved replacement.
- **Disposition (safe deprecation):** no RLS change; no backend removal; beta
  tables/admin endpoints retained; documented as obsolete with a
  recommendation to remove the public beta entry points in a later phase.

## 3. Processing Entity Security Completed (Phase 2)

| Finding | Resolution | Verified |
|---|---|---|
| 2A Suspended/terminated entity staff could read the entity **dashboard** (extraction workspace already gated) | **Central** `ensure_entity_active(repos, entity_id)` in `operations_auth.py`; `entity_dashboard` now enforces it; `_entity_workspace_guard` refactored onto it (no per-endpoint patches) | suspended→403, terminated→403, active→200, revoked staff→403 |
| 2B Legacy upload IDOR (`GET /api/upload/batches/stats?organization_id=…` + `…/{id}/progress`) | Non-admin callers can never widen scope with a user-supplied `organization_id`; `progress` now enforces the batch-org membership check (server-derived scope) | unit tests (2E static + 2J matrix) + code |
| 2C Legacy document routes | **Inventory produced** — all legacy doc routes live in the separate `main.py` app (NOT the V3 API), use `require_org_member` + path `org_id` without cross-org re-check, and have **no frontend consumers**. Not removed (stop condition #7); recommended for formal deprecation | documented; V3 `/api/v3/documents/*signed-url` remains the authoritative surface |
| 2D Entity staff received **raw** item storage paths (internal surface signed; entity surface did not) | Entity item / next-item / batch-items endpoints now return `signed_item(...)` — short-lived signed URLs only (D32 private-bucket model); never raw paths | entity item test asserts raw path is never returned |
| 2E `current_user.id` defect class (AuthUser has only `user_id`) | **171 occurrences across 17 legacy route files replaced** with `current_user.user_id` | static regression test enforces zero remaining |
| 2F `require_org_admin` could 500 on Supabase lookup failure | `get_supabase_client()` moved inside the guarded fallback → authorization failure is always a clean 403 | test: lookup failure → 403 (never 500) |
| 2G Batch assignment invariant (`entity_id XOR assigned_to`, unassigned allowed) | **Fail-closed migration** `20260826000000_assignment_xor_check.sql` adds the CHECK constraint (raises if any violating row exists; idempotent) | migration test asserts constraint + fail-closed guard |
| 2H Dual-scope identity | **PO decision deferred** — no invariant enforced (would risk altering approved membership semantics); documented in §11 |
| 2I Assignment/reassignment | Existing D22 model verified (exactly-one-party enforced by the API; audit trail records before/after); **new tests**: previous entity loses access after reassignment; new entity gains access; unassigned work invisible to entity staff |
| 2J Cross-scope security tests | **NEW** `test_processing_entity_security.py` (11 tests) + extended suite — see §10 |

## 4. Files Changed

**Backend (API/auth/data):**
- `backend/api/operations_auth.py` — `ensure_entity_active` central lifecycle gate
- `backend/api/v3_operations.py` — entity dashboard lifecycle gate; entity item/next-item/batch-items signed URLs
- `backend/api/v3_invitations.py` — **NEW** invitation acceptance endpoint
- `backend/api/v3_context.py` — **NEW** (previous task; preserved)
- `backend/api/v3_organizations.py` — staff/consultant org-creation guard (previous task; preserved)
- `backend/api/router.py` — registered context + invitations routers
- `backend/auth.py` — `require_org_admin` 403-not-500
- `backend/data/invitations.py` — `get_by_token`, `mark_accepted`, `get_pending_by_email`
- `backend/routes/upload.py` — batch stats/progress org-scope hardening
- `backend/routes/**` (17 legacy files) — `current_user.id` → `current_user.user_id` (171 replacements)

**Tests:**
- `backend/tests/unit/api/test_processing_entity_security.py` — **NEW** (11 tests)
- `backend/tests/unit/api/test_v3_invitations.py` — **NEW** (9 tests)
- `backend/tests/unit/api/test_v3_context.py` — **NEW** (previous task; preserved)
- `backend/tests/unit/api/fakes.py` — invitations fakes
- `backend/tests/unit/api/test_self_service_onboarding.py` — guard tests (previous task; preserved)

**Frontend:**
- `frontend/src/v3/api.js` — `acceptInvitation`
- `frontend/src/InvitationPending.jsx` — functional acceptance page
- `frontend/src/App.js` — `/accept-invite` route
- `frontend/src/BetaLogin.jsx` — all `/dashboard` redirects → resolver
- Phase-1 routing files preserved (`Login.js`, `AuthCallback.js`, `MagicLink.jsx`, `SelfServiceSignup.jsx`, `BetaSignup.jsx`, `OnboardingPage.jsx`, `V3Layout.jsx`, `v3/__tests__/api.test.js`)

**Seed / migration:**
- `supabase/seeds/README.md`, `supabase/seeds/demo_identities.sql`, `supabase/seeds/provision_demo_identities.py` — **NEW**
- `supabase/migrations/20260826000000_assignment_xor_check.sql` — **NEW**

**Total:** 37 files changed (754 insertions / 268 deletions) + new untracked files.

## 5. Database Changes

| Item | Detail |
|---|---|
| Migration | `20260826000000_assignment_xor_check.sql` — adds `manual_extraction_batches_assignment_xor_check` CHECK: `NOT (entity_id IS NOT NULL AND assigned_to IS NOT NULL)` (allows NULL/NULL, entity/NULL, NULL/assigned; rejects both set) |
| Safety | Fail-closed: a `DO` block RAISES if any existing row violates the invariant before the constraint is applied; idempotent (`IF NOT EXISTS` on the constraint name and columns) |
| Seed | `supabase/seeds/demo_identities.sql` — identity-row seed (organisations, memberships, staff roles/profiles, processing entities, consultant firm + members + client grant, pending invitation) — **not a migration**, explicit invocation only |

## 6. RLS Changes

**None.** No policy or RLS function was added, removed or weakened. The
lifecycle gate is enforced server-side over the service-role paths (which
bypass RLS by design); the RLS `is_entity_member` / `is_org_member` /
`is_org_consultant` gates remain unchanged as defense-in-depth.

## 7. API Changes

| Route | Change |
|---|---|
| `POST /api/v3/invitations/{token}/accept` | **NEW** — invitation redemption (ownership/status/expiry/single-use/role/audit) |
| `GET /api/v3/ops/entities/{id}/dashboard` | NOW enforces ACTIVE entity (403 suspended/terminated) |
| `GET /api/v3/ops/entities/{id}/extraction/…` (all) | lifecycle gate via `ensure_entity_active` (unchanged behaviour for active entities) |
| `GET /api/v3/ops/entities/{id}/extraction/items/{item_id}` · `…/next-item` · `…/batches/{batch_id}/items` | item `file_url` returned as a short-lived **signed URL** (never a raw storage path) |
| `GET /api/upload/batches/stats` | non-admin scope fixed to the caller's own memberships (user-supplied `organization_id` ignored) |
| `GET /api/upload/batches/{id}/progress` | batch-org membership check added (403 for non-members) |
| `GET /api/v3/me/context` · `POST /api/v3/organizations` | preserved from Phase 1 |

## 8. Storage Changes

**None.** The `documents` bucket stays private; no bucket/path changes; no
service-role credentials in frontend. Entity item surfaces now return signed
URLs through the existing `services/storage.storage_signed_url` mechanism
(short-lived, server-issued after entity-assignment authorization) instead of
raw paths.

## 9. Tests

| Suite | Result |
|---|---|
| Backend `tests/unit/api` (full) | **exit=0 — zero failures** (~585 tests) |
| `test_processing_entity_security.py` (NEW) | 11/11 pass |
| `test_v3_invitations.py` (NEW) | 9/9 pass |
| `test_v3_context.py` (Phase 1) | 17/17 pass |
| `test_self_service_onboarding.py` (Phase 1 guards) | pass |
| `test_v3_operations` / `test_v3_entity_extraction` / `test_v3_qc` / `test_v3_processing_workflow` / `test_scope_aware_authorization` | all pass (no regression from 2A/2D) |
| Frontend `v3/__tests__/api.test.js` | 30/30 pass |
| Frontend production build | **exit=0** (only pre-existing lint warnings) |

Remaining failures: **none**. (The 5 `test_v3_customer_admin.py` failures seen
in earlier runs were environment-flaky — requests/urllib3 venv mismatch — and
passed in the final full run; they are not code defects.)

## 10. Security Verification

| Axis | Result |
|---|---|
| Cross-org isolation | Existing org-scoped guards + RLS unchanged; legacy upload `stats`/`progress` now server-derived (org A user cannot read org B batch data) |
| Cross-entity isolation | Entity staff can only list/read/process their own entity's assigned batches (existing D22 + new tests) |
| Assignment / reassignment | Exactly-one-party enforced; after reassignment Entity A → B, A loses access (403) and B gains access (200); audit trail records before/after |
| Document access | Entity item responses return signed URLs only; raw storage paths never exposed (2D test) |
| Signed URLs | Short-lived, server-issued after entity-assignment authorization; bucket remains private; no service-role exposure |
| Suspended entity | 403 on entity dashboard AND all entity extraction surfaces |
| Terminated entity | 403 (same surfaces) |
| Revoked staff | 403 on `/ops/me`, entity dashboard, entity extraction (inactive profile is not an identity) |
| Legacy routes | Legacy `main.py` app is NOT mounted in the V3 API; no frontend consumers; `current_user.id` class eliminated; upload batch IDORs closed; legacy document routes documented for deprecation (not removed — stop condition #7) |
| Fail-open check | `require_org_admin` lookup failure → 403 (never fail open, never 500); `/me/context` errors → 500 (never "new customer") |

## 11. Deferred Items

**Product Owner decisions (required, not guessed):**
- 2H **Dual-scope identity invariant** — whether a user may hold Processing
  Entity Staff AND Customer Organisation membership / Consultant membership
  simultaneously. Enforcing a provisioning-time invariant would alter
  membership semantics; no change made.
- 1C **Legacy app deprecation** — formal removal of `main.py` / legacy
  `Dashboard` / `CompanyNamePrompt` / `OnboardingWizard` and the legacy
  document/upload route family.
- 1D **Beta retirement** — removing the public beta entry points / tables.
- Public customer signup timing (existing open decision).

**Future architecture / engineering (documented, not implemented):**
- Phase 3 international processing: `processing_entities.metadata` JSONB can
  carry location/destination policy without new tables; **no gap requiring
  implementation**; destination policy = PO decision.
- Phase 4 retention/deletion: no retention-policy schema exists; a broad
  retention system requires explicit approval; **not implemented**.
- Phase 5 AI providers: AI extraction engine + workflow exist; the live HTTP
  route remains deterministic/manual with human review — public wording
  (AI-assisted at launch with validation/human review) unchanged; provider
  governance requires PO approval; **not implemented**.

**Legal/contractual:** DPA, transfer mechanisms/assessments, DPIA, supplier
due diligence, Processing Entity contracts, customer contractual controls,
privacy counsel review — outside engineering scope.

## 12. Regulatory Boundary

No legal interpretation was encoded as application behaviour. No
Bangladesh-specific processing, destination policy, or data-locality rule was
implemented. The regulatory boundary (DPA/transfer/DPIA/contracts/counsel)
remains outside the engineering implementation.

## 13. Git State

| Item | Value |
|---|---|
| Starting HEAD (clone) | `d4dcca1eb11f86bcae497815c8592d688a7e305f` |
| Ending HEAD (clone) | `d4dcca1eb11f86bcae497815c8592d688a7e305f` (unchanged — uncommitted work only) |
| Commits created | **0** |
| Pushes | **0** |
| Stashes | 0 |
| Dev working tree | Untouched (0 staged; existing 546 modified / 151 deleted / 58 untracked preserved) |
| Remote `main` | Unchanged at `d4dcca1e…` |

## STOP Conditions Review

1. Approved Processing Entity model — unchanged. 2. Customer Organisation
membership semantics — unchanged. 3. Actor precedence — unchanged (preserved).
4. No new commercial/business rule encoded. 5. No legal interpretation encoded.
6. Public product positioning — untouched (no public website/pricing change).
7. Legacy routes: upload/document batch routes hardened where safe; removal
deferred (documented) rather than guessed. 8. Migration is additive, guarded,
fail-closed — no existing-data risk.

---

**HARD STOP — NO COMMIT, NO PUSH, NO D38.** All work is uncommitted in the
isolated canonical clone `/tmp/carbontally_audit`. The developer working tree
is untouched. Awaiting Product Owner instruction to commit/push and for the
decision-gated items in §11.
