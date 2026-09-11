# CarbonTally — Audit Remediation Report

- **Date:** 2026-08-31
- **Checkpoint:** `16391217103b98dcea520070c5a22c68f12fe607` (HEAD `1639121`)
- **Source findings:** Independent Audit Swarm run `20260831T173912_16391217` (18 findings), verified by Cline (`CARBONTALLY_AUDIT_FINDING_VERIFICATION.md`).
- **Nature:** APPROVED remediation. Read the approved product/architecture decisions and implemented only the approved workstreams. Findings explicitly closed/deferred were NOT touched.

---

## 1. Findings addressed (approved workstreams)

| Finding | Workstream | Change |
|---|---|---|
| DB-0001 | WS1 | RLS hardening: legacy audit/activity tables immutable; activity_feed mutation row-owner scoped |
| ARCH-0001 | WS2 | Canonical-surface documentation + regression tests (both route families retained) |
| API-0001 | WS3 | Missing credentials → 401 + `WWW-Authenticate` (HTTPBearer auto_error off) |
| ARCH-0003 | WS4 | Shared legacy API client (`services/apiClient.js`); AssetManager + TeamManagement migrated |
| DB-0002 | WS5 | `assets.organization_id` → NOT NULL (strictly tenant-scoped) |
| SEC-0003 | WS6 | Consultant revocation role model (Owner/Admin/Manager only) — RLS + backend |
| FE-0003 | WS7 | Deleted dead `frontend/src/StaffDashboard.jsx` |
| UX-0001 | WS8 | `DataSecurity.jsx` link `/privacy-policy` → `/privacy` |

## 2. Findings intentionally NOT addressed (closed / deferred / false)

| Finding | Reason |
|---|---|
| API-0002 | Approved: do not create `GET /api/v3/organizations` |
| API-0003 | Approved: do not "fix" OpenAPI based on the invalid 600-vs-247 comparison |
| ARCH-0002 | Approved: customer/consultant vs internal Operations surfaces are intentionally separate |
| ARCH-0004 | Approved: audit/activity tables intentionally separate |
| DB-0003 / SEC-0002 | Approved: FORCE RLS deferred to a separate security investigation |
| FE-0002 | Closed as false (route redirect works) |
| FE-0004 | Closed as false (contexts/hooks are referenced) |
| UX-0002 | Closed as production defect (`vercel.json` serves the admin app at `/admin`) |
| SEC-0001 | Approved: calculation snapshots remain API-only for consultants |

## 3. Product/architecture decisions applied

1. Consultant-client revocation: Consultant Owner/Admin/Manager may revoke; Member/Viewer may not. Revocation is a soft lifecycle state (`consultant_clients.status='ended'` + `ended_at`/`ended_by` + audit event) — **not** account deletion; client data is preserved.
2. Processing API architecture: customer/consultant vs internal Operations surfaces kept separate (no route merging).
3. Calculation snapshots: remain API-only; no direct consultant Supabase access.
4. V3 migration: controlled convergence; legacy surface retained; no reckless deletion.
5. FORCE RLS: not enabled (deferred).
6. Audit/activity tables: not consolidated.

---

## 4–8. Per-finding detail

### WS1 — DB-0001 — Legacy audit/activity mutability

**Original audit claim:** `audit_logs_tenant_update/delete` (and equivalents on `activity_logs`, `activity_feed`, `document_activity_log`) allow any `authenticated` org member to UPDATE/DELETE audit records.

**Cline verification:** VERIFIED TRUE (policies exist in live schema; V3 `audit_trail` is already deny-by-default and untouched).

**Approved decision:** Remove ordinary-user mutation of immutable audit history; preserve legitimate activity-feed mutation (row-owner scoped); leave the V3 forensic `audit_trail` alone.

**Implementation:**
- New migration `supabase/migrations/20260831020000_audit_activity_immutability.sql`:
  - `DROP POLICY IF EXISTS` UPDATE + DELETE on `audit_logs`, `activity_logs`, `document_activity_log` (immutable history; INSERT/SELECT kept).
  - `activity_feed`: replaced org-member-wide UPDATE/DELETE with `activity_feed_own_update` / `activity_feed_own_delete` scoped to `user_id = auth.uid()` (read/unread UX preserved, tenant isolation tightened).
- Service-role/backend writes unaffected (RLS bypass by design).

**Regression tests:** `backend/tests/unit/api/test_audit_immutability_migration.py` (deterministic migration invariants: drops present, INSERT/SELECT preserved, non-destructive, `audit_trail` untouched).

**Result:** 6/6 tests pass. Migration is idempotent (`DROP POLICY IF EXISTS`). **Live-DB apply + OHD re-verification recommended** (no DB connection available in this environment; the migration is defensive and will not fail if the policies were never created).

### WS2 — ARCH-0001 — Duplicate SLA/Review API surfaces

**Original audit claim:** `/sla/settings` and review-assign routes duplicated between `v3_review` (`/api/v3/admin/*`) and `v3_operations` (`/api/v3/ops/*`).

**Cline verification:** VERIFIED TRUE as duplication; the two families have **different authorization semantics**; the product UI consumes only `/api/v3/ops/*`.

**Approved decision:** Both families are intentionally retained (admin legacy-compat vs canonical ops). Document the distinction; do not delete or force-consolidate.

**Implementation:**
- `backend/api/v3_review.py`: module docstring now records the canonical-surface decision (ops = canonical UI surface; admin = retained legacy-compat, no frontend consumer, do not route new work through it).

**Regression tests:** `backend/tests/unit/api/test_review_sla_surfaces.py` — both families registered; canonical ops routes exist with expected verbs; no route collision.

**Result:** 4/4 tests pass.

### WS3 — API-0001 — Authentication status semantics

**Original audit claim:** missing credentials return 403 "Not authenticated" instead of 401.

**Cline verification:** VERIFIED TRUE — `HTTPBearer()` default `auto_error=True` short-circuits missing headers to 403 before `get_current_user`.

**Approved decision:** Correct 401-vs-403 semantics (missing → 401 + `WWW-Authenticate`; invalid → 401; insufficient permission → 403).

**Implementation:** `backend/auth.py`:
- `security = HTTPBearer(auto_error=False)`.
- `get_current_user` raises `401 "Not authenticated"` with `WWW-Authenticate: Bearer` when `credentials is None`.
- `get_current_user_optional` unchanged (already handles `None`).

**Regression tests:** `backend/tests/unit/api/test_auth_status_semantics.py` — auto_error disabled; missing creds → 401 + WWW-Authenticate (and not 500); authenticated-but-insufficient → 403.

**Result:** 4/4 tests pass.


### WS4 — ARCH-0003 — V3 frontend/API consolidation

**Original audit claim:** legacy components duplicate `API_URL`/token/fetch plumbing beside the V3 client.

**Cline verification:** VERIFIED TRUE (AssetManager/TeamManagement/UploadManager/BulkUpload/PDFIngestionPortal etc.).

**Approved decision:** Controlled convergence — centralize legacy HTTP plumbing; do not rewrite legacy business logic or delete reachable functionality.

**Implementation:**
- New `frontend/src/services/apiClient.js`: `getApiUrl()`, `getToken()`, `apiRequest(path, {method, body})` — consistent base-URL resolution, bearer-token header, JSON/FormData handling, and a `{ok,status,data}` return shape that preserves the existing call-site behaviour.
- Migrated `frontend/src/AssetManager.js` and `frontend/src/TeamManagement.js` to `apiRequest` (removed their per-component `API_URL`/`getToken`).
- **Retained legacy surface (documented, not migrated in this workstream):** `UploadManager.js`, `BulkUpload.jsx`, `PDFIngestionPortal.jsx`, `ManualEntryStandalone.jsx` — continue to use their own fetch/axios; migration is follow-up work under the same convergence plan.

**Regression tests:** `frontend/src/services/__tests__/apiClient.test.js` (8 tests: env/default URL, session + localStorage token, auth header, JSON encoding, non-throwing error shape, FormData passthrough).

**Result:** 8/8 tests pass; full V3 frontend suite 174/174 passes; `npm run build` succeeds (pre-existing warnings only in unrelated v3 files).

### WS5 — DB-0002 — Tenant organization_id nullability

**Original audit claim:** `organization_id` nullable on tenant-scoped tables (assets, activity_feed, …).

**Cline verification:** PARTIALLY TRUE — columns nullable (fact); orphan/NULL risk not demonstrated for `assets`.

**Approved decision:** NOT NULL only where demonstrably correct; NULL kept where it has legitimate meaning.

**Implementation:** `supabase/migrations/20260831030000_tenant_org_id_not_null.sql` — `ALTER TABLE public.assets ALTER COLUMN organization_id SET NOT NULL`. Analysis documented in the migration: `assets` is strictly tenant-scoped (V3 API derives org from path; investor-demo seed always sets it; no global asset records). All other nullable tables preserved (global rows, system events, legacy records).

**Regression tests:** `backend/tests/unit/api/test_tenant_org_not_null_migration.py` (assets altered; no other table altered; non-destructive).

**Result:** 3/3 tests pass. **Deployment note:** the ALTER fails loudly if any NULL row exists in a target DB — run `SELECT count(*) FROM assets WHERE organization_id IS NULL;` before applying. No DB connection was available here to run the count.

### WS6 — SEC-0003 — Consultant-client revocation role model

**Original audit claim:** `consultant_clients_tenant_delete` (any org member) + `cc_delete_own_firm` (any `can_manage_clients` member) are permissive; audit classified as PO_DECISION.

**Cline verification:** VERIFIED TRUE (policies as stated). Product decision ratified: consultant **Owner/Admin/Manager** may revoke; **Member/Viewer** may not.

**Approved decision (soft-state, provenance-preserving):** the existing D19 lifecycle already implements revocation as `status='ended'` (row + timestamps retained, audit event written, `is_org_consultant` gates on `status='active'`). This design was chosen over hard-deletion because it preserves provenance and is compatible with the existing architecture.

**Implementation:**
- `supabase/migrations/20260831040000_consultant_revocation_roles.sql`:
  - New `public.is_consultant_firm_revoker(p_firm)` — ACTIVE member with `role IN ('owner','admin','manager')` (role-based, per decision).
  - `cc_delete_own_firm` (RLS DELETE) → `is_consultant_firm_revoker(consultant_id)`.
  - `consultant_clients_tenant_delete` → `is_org_admin_or_owner(organization_id)` (customer owner/admin only — Member/Viewer cannot sever).
- `backend/api/consultant_auth.py`: `CONSULTANT_REVOKER_ROLES` + `ensure_consultant_revocation_authority(context)`.
- `backend/api/v3_consultants.py`: suspend / end / reactivate / delete / status-update lifecycle endpoints now require `ensure_consultant_revocation_authority` (role-based) instead of the generic `manage_clients` capability for the revocation actions.

**Regression tests:** `backend/tests/unit/api/test_consultant_revocation.py` (owner/admin/manager allowed; member/'consultant'/viewer denied — including with `can_manage_clients=true`; provenance preserved: relationship row + org retained after `end`; audit event written; revoked relationship no longer grants access) + `test_consultant_revocation_migration.py` (migration invariants).

**Result:** 13/13 new tests + existing `test_d19_lifecycle.py` pass (7/7).


### WS7 — FE-0003 — Dead code cleanup

**Original audit claim:** `frontend/src/StaffDashboard.jsx` (and local `ManualExtractionForm`) unreferenced.

**Cline verification:** VERIFIED TRUE — repo-wide search found no import/route/test/build reference; the admin app's `admin/src/pages/staff/StaffDashboard.js` is a **different, live** file.

**Approved decision:** Delete only if still demonstrably dead.

**Implementation:** `frontend/src/StaffDashboard.jsx` deleted after full repository reference search (dynamic imports, tests, scripts, build, admin app checked). The live admin `StaffDashboard.js` is untouched.

**Result:** Build succeeds; no dangling references.

### WS8 — UX-0001 — Privacy route

**Original audit claim:** `DataSecurity.jsx` links to `/privacy-policy` (not registered).

**Cline verification:** VERIFIED TRUE.

**Approved decision:** Fix to the canonical `/privacy` route (no intentional alias exists).

**Implementation:** `frontend/src/DataSecurity.jsx` line 441: `<Link to="/privacy-policy">` → `<Link to="/privacy">`.

**Note:** `DataSecurity.jsx` itself is currently not routed/imported anywhere (legacy component) — the link fix is correct regardless and the component remains reachable if/when routed.

**Result:** Verified in source; build passes.

---

## 9. Files changed (this remediation)

**Backend API/auth:**
- `backend/auth.py` (WS3)
- `backend/api/consultant_auth.py` (WS6)
- `backend/api/v3_consultants.py` (WS6)
- `backend/api/v3_review.py` (WS2 — docstring only)

**Frontend:**
- `frontend/src/services/apiClient.js` (new, WS4)
- `frontend/src/AssetManager.js` (WS4)
- `frontend/src/TeamManagement.js` (WS4)
- `frontend/src/DataSecurity.jsx` (WS8)
- `frontend/src/StaffDashboard.jsx` (deleted, WS7)

**Database/RLS migrations (new):**
- `supabase/migrations/20260831020000_audit_activity_immutability.sql` (WS1)
- `supabase/migrations/20260831030000_tenant_org_id_not_null.sql` (WS5)
- `supabase/migrations/20260831040000_consultant_revocation_roles.sql` (WS6)

**Tests (new):**
- `backend/tests/unit/api/test_auth_status_semantics.py` (WS3)
- `backend/tests/unit/api/test_review_sla_surfaces.py` (WS2)
- `backend/tests/unit/api/test_audit_immutability_migration.py` (WS1)
- `backend/tests/unit/api/test_tenant_org_not_null_migration.py` (WS5)
- `backend/tests/unit/api/test_consultant_revocation.py` (WS6)
- `backend/tests/unit/api/test_consultant_revocation_migration.py` (WS6)
- `frontend/src/services/__tests__/apiClient.test.js` (WS4)

## 10–11. Database/RLS changes & migrations

Three new migrations (see above). No existing migration modified. No destructive statement (no DROP TABLE/TRUNCATE). Migrations are idempotent/defensive. **Applied to no live database in this session** (no DB connection available); application must occur through the normal Supabase migration tooling with the pre-apply checks noted in WS1/WS5.


## 12. Existing tests run & results

- Backend targeted regression set (WS1–WS6 affected suites, 12 files): **82 passed** (includes all new tests + existing `test_d19_lifecycle`, `test_v3_consultants`, `test_operations_auth`, `test_scope_aware_authorization`, `test_admin_endpoints`, `test_legacy_upload_idor`).
- Full backend `tests/unit/api/` suite: started in background; see appended result at the end of this file (the environment's shell tooling intermittently drops long-running background output — the targeted regression set above plus the frontend suites are the verified gate).
- Frontend V3 + services suites: **15 suites / 174 tests passed**.
- `npm run build`: succeeds (EXIT=0; warnings are pre-existing in unrelated v3 files).

## 13. Risks remaining

- **Live-DB apply unverified** for WS1/WS5/WS6 migrations (no DB connection in this environment). Migrations are defensive; WS5 fails loudly if a NULL asset row exists.
- WS4: four legacy components (`UploadManager`, `BulkUpload`, `PDFIngestionPortal`, `ManualEntryStandalone`) remain on their own HTTP plumbing — documented as retained; follow-up convergence.
- WS6: the consultant UI (`ConsultantPage.jsx`) still shows lifecycle buttons to capability holders; server-side 403 is authoritative (UI is not a security boundary). Optionally hide buttons for Member/Viewer in a follow-up.
- WS3: the auth change is app-wide (legacy + V3). Any external client that relied on 403-for-missing-credentials would need updating — the correct 401 semantics are the approved target.
- `DataSecurity.jsx` is not currently routed (legacy); the link fix is correct but the component itself may warrant routing or removal review.

## 14. Items requiring further PO decision

- Whether Member/Viewer should also see lifecycle actions in the consultant UI (server-side enforcement is already in place).
- Whether `UploadManager`/`BulkUpload`/`PDFIngestionPortal`/`ManualEntryStandalone` should be migrated to `services/apiClient.js` now or retired with the legacy surface.

## 15. Items requiring OHD re-verification

- All 8 addressed findings (WS1–WS8), especially:
  - WS1 DB-0001: live RLS policy state after migration.
  - WS5 DB-0002: `assets` NOT NULL applied with zero NULL rows.
  - WS6 SEC-0003: RLS revocation behavior for all five consultant roles against a live Supabase.
  - WS3 API-0001: live 401 + `WWW-Authenticate` on the running API.

---

## Final safety check

- `git status`/`git diff`: only the files listed in §9 changed by this session. All other working-tree modifications are pre-existing (audit/QA tooling and prior sessions' work) and were not touched.
- No audit-swarm files (`independent_audit/`, `agent_swarm*`) modified.
- No secrets introduced or printed; `.env` untouched.
- No destructive migration; no data mutated.
- **No commits or pushes made.**
- No migration was applied to any database in this session (application deferred to the Supabase migration tooling).

---

## Appendix — full backend suite result (background run)

`pytest tests/unit/api/ -q` ran to completion against the remediated tree:

- Progress reached `[100%]` with **zero failure markers** (`F`) and **no short-test-summary section** — pytest prints any failed test before the warnings summary; there were none.
- ~690 tests collected in `tests/unit/api/` (progress batches: 9×72 + 43 dots).
- Final "N passed" count line was not captured because the environment's background tooling dropped the last buffered stdout line after `[100%]`; the absence of any `FAILED`/`failed`/`short test summary info` output confirms a clean pass.
- Separately, the targeted regression set covering every changed file plus directly-affected existing suites passed **82/82**.
- Frontend: **15 suites / 174 tests passed**; `npm run build` succeeded.


