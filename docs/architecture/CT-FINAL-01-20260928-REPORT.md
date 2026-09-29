# CT-FINAL-01 — Release-candidate remediation of CT-VERIFY-05 findings

* **Task:** CT-FINAL-01 (implementation agent work item following the independent
  CT-VERIFY-05 report)
* **Date:** 2026-09-28
* **Branch:** `p8-release-reconciled`
* **Baseline HEAD:** `dc3d78dc8021…` (branches and SHA verified at session start)
* **Scope:** remediate the CT-VERIFY-05 findings on the live surface —
  **F-05-R1 (release-blocking)**, **F-05-R2 (three 500s)**, **F-05-R3**,
  **F-05-R4** — plus the recommended guard-scan widening **F-05-R7**. PD-gated
  surfaces were **not** touched (see §7).
* **Deployment:** **none.** No push, no deploy, no production or demo data
  mutation, no migration added or edited.
* **Verdict for this change-set (see §8):**
  `F-05-R1/R2/R3/R4 IMPLEMENTED + TESTED (in-repo);
   INDEPENDENT RE-VERIFICATION (CT-VERIFY-06) REQUIRED BEFORE ACCEPTANCE`.

---

## 1. Findings addressed

| Finding | CT-VERIFY-05 severity | Status in this change-set |
|---|---|---|
| F-05-R1 — cross-tenant emissions disclosure via org path parameter | **HIGH / BLOCKING** | **FIXED + TESTED** (§3) |
| F-05-R2.1 — `FPDF.set_fill_color()` 5-argument call → 500 | MEDIUM | **FIXED + TESTED** (§4) |
| F-05-R2.2 — `organization-activity` selects non-existent columns → 500 | MEDIUM | **FIXED + TESTED** (§4) |
| F-05-R2.3 — `data/emissions-data` response-model validation → 500 | MEDIUM | **FIXED + TESTED** (§4) |
| F-05-R3 — cross-tenant DENY returned 500 (`maybe_single`) | MEDIUM | **FIXED + TESTED** (§3.3) |
| F-05-R4 — NULL embedded relation → `AttributeError` | LOW | **FIXED + TESTED** (§4.4) |
| F-05-R5 — frozen-report documentation inaccuracies | LOW (docs) | **RECORDED, NOT CHANGED** (§6) |
| F-05-R6 — residual-inventory drift | INFORMATIONAL | **RECORDED** (§6) |
| F-05-R7 — guard scan-root coverage gap | INFORMATIONAL | **FIXED** (§6) |
| F-05-R8 — out-of-scope pre-existing defects | INFORMATIONAL | **OUT OF SCOPE** (§7) |

---

## 2. Files changed

| File | Change |
|---|---|
| `backend/auth.py` | F-05-R1/R3 — central exact-tenant enforcement for the organisation guards; list-based membership resolution; corrected guard docstrings |
| `backend/routes/organizations/dashboard.py` | F-05-R2.2 + F-05-R4 — `organization-activity` selects canonical columns; NULL-safe relation reads |
| `backend/routes/organizations/data.py` | F-05-R2.3 + F-05-R4 — `emissions-data` returns the declared response contract; NULL-safe relation reads |
| `backend/report_generator.py` | F-05-R2.1 — `set_fill_color` call arity |
| `backend/tests/unit/api/test_f05_r1_org_scope_authorization.py` | **new** — 35-test F-05-R1/R3 authorization matrix (ALLOW + DENY), incl. the composed-app test |
| `backend/tests/unit/api/test_f05_r2_r4_runtime_defects.py` | **new** — 8-test F-05-R2/R4 regression + guard suite |
| `backend/tests/unit/test_ct_implement_01_remediation.py` | F-05-R7 — `_LEGACY_SCAN_ROOTS` now also covers the root-level bundles (`frontend/*.js(x)`, `admin/*.js(x)`) with the F-05-R7 rationale comment. The whole `_LEGACY_SCAN_ROOTS` construct is uncommitted CT-IMPLEMENT-04 work (absent from HEAD), so the F-05-R7 entries are not separable from it in the working tree; the module passes with the widened roots (**34 passed, exit 0**) |

No database migration was required or added; the canonical schema (92
migrations) is unmodified by this change-set. No API route was added, removed or
renamed, and no request/response schema was changed except adding the
already-declared (`organization_id`, `summary`) and previously-returned
(`total`) fields to the `emissions-data` payload.

### 2.1 Runtime wiring evidence (the fix is reachable in the real app)

Verified against the actual composed legacy application (`backend/main.py`),
without a database:

* the reported route appears in the application's OpenAPI document
  (`/api/organizations/{org_id}/exports/exports/emissions`, method `post`;
  606 paths total), so the legacy app really serves it;
* `POST` with **no** credentials → **401**, and `POST` with an invalid bearer token
  → **401** — i.e. the `require_org_member()` chain (now including the
  path-scope enforcement) is wired into the served route.

There is exactly **one** definition of each organisation guard in the backend
(`backend/auth.py:575` / `:616`); `backend/api/dependencies.py` only re-exports
them, so no route can sidestep the fix.

### 2.2 Git state (nothing committed, nothing pushed)

* HEAD is `dc3d78dc8021bd65978754cf131c38045ff8013d`; this change-set is
  **uncommitted working-tree work** (5 modified files + 2 new test files + this
  report). No commit, push, tag or branch change was made.
* Other working-tree modifications were **already present before this task** and
  are **not** part of this change-set: `.gitignore`,
  `backend/routes/emissions.py`, `backend/routes/organizations/exports.py`,
  `frontend/App_.js`, `frontend/src/App.js`, the three CT-IMPLEMENT-01/02/03
  report documents, and the earlier CT-IMPLEMENT-04 additions to
  `test_ct_implement_01_remediation.py`. They were left untouched.
* Pre-existing untracked artefacts (`.costrict/`, `.p18_audit_tmp/`,
  `costrict-p3-ov-01-independent-re-verification.txt`, and two empty files named
  `8` and `=` dated 23 Sep) were likewise left untouched.
* No secret, credential, token or signed URL appears in the diff (scanned); no
  `.env` file was modified.


---

## 3. F-05-R1 / F-05-R3 — organisation-scope enforcement (the blocking fix)

### 3.1 Root cause (re-verified in the current tree, not inherited)

`require_org_member()` tested only `current_user.is_org_member` — "member of
**some** organisation". Handlers such as
`POST /api/organizations/{org_id}/exports/exports/emissions`
(`backend/routes/organizations/exports.py:44`) then query with the
service-role client scoped **only** by the path `org_id`
(`exports.py:52–57`), so any authenticated organisation member could read
another organisation's emissions data by changing that path parameter.

### 3.2 Remediation (central, not per-route)

New primitives in `backend/auth.py` (immediately above the guards they serve):

* `ORG_SCOPE_PATH_PARAMS` — the path parameter spellings that name an
  organisation (`organization_id`, `org_id`, `organisation_id`).
* `get_request_org_scope(request)` — the organisation ids declared by the
  request PATH; `()` when the route names none.
* `get_active_org_role(user_id, organization_id)` — authoritative role of an
  **ACTIVE** membership, or `None`. **Fail-closed**: an unusable membership
  store denies (403); it can never become an implicit allow and never surfaces
  as a 500 (F-05-R3 — the previous `maybe_single()` raised `AttributeError` on
  `None` for a member of several organisations).
* `enforce_org_path_scope(request, current_user)` — every organisation named by
  the path must be the caller's own organisation or one where they hold an
  active membership, otherwise `403 "You don't have access to this
  organization"`. CarbonTally **internal** staff keep the approved operational
  cross-organisation access; Processing Entity staff remain denied.
* `_org_admin_authority(current_user, org_id)` — owner/admin authority for a
  specific organisation, with a token-derived fast path (no round trip) for the
  caller's own organisation.

`require_org_member()` now takes FastAPI's injected `Request` (verified against
FastAPI 0.141.1 that a nested checker parameter declared `request: Request =
None` **is** injected while direct unit-test calls remain positionally
compatible) and calls `enforce_org_path_scope` **before the handler runs**, i.e.
before any service-role access.

`require_org_admin()` now resolves admin authority for **the path
organisation** (falling back to the caller's own organisation when the route
names none, preserving historical behaviour) and uses the list-based
`get_active_org_role` instead of `maybe_single()`.

**Blast radius (measured, not assumed):** 102 route declarations across 16 files
are path-organisation-scoped and guarded by these two guards — 87 distinct
`METHOD path` pairs, frozen by
`test_org_scoped_guard_surface_is_frozen`. All of them are corrected by this one
change. Route bodies were not edited.

### 3.3 No-parentheses hazard (recorded and guarded)

`Depends(require_org_member)` **without parentheses** hands FastAPI the factory
itself: the check never runs and the checker *function* is injected into the
handler. Reproduced against the pinned FastAPI (`0.141.1`): the no-paren shape
answers **HTTP 200** on a route whose guard never ran, the parenthesised shape
answers 401. The five factory guards previously claimed "works with both"
forms; those docstrings are now explicit, and
`test_no_factory_guard_is_used_without_parentheses` scans the whole backend so a
new bare usage fails the suite. (All 84 existing bare `Depends(require_staff)`
uses import the *dependency function* from `api.operations_auth`, which is
correct usage — verified per file.)

### 3.4 Known asymmetry (recorded, fail-closed, no security impact)

Some V3 routes additionally call `ensure_org_access(...)` from
`backend/api/dependencies.py`, which authorises **token-scoped** membership only
(`current_user.organization_id == organization_id`). A user who is an active
member of two organisations therefore passes the new guard for their second
organisation but is still refused by those in-body checks. That is strictly
fail-closed — it can only deny, never allow — so it is **not** a security defect;
closing it is a separate, PO-neutral consistency task (see §9).

### 3.5 Tests (35, all passing)

`backend/tests/unit/api/test_f05_r1_org_scope_authorization.py` runs the **real
guards** and the **real routers**, DB-free, and asserts both directions:

**ALLOW** — member of org-a on org-a's path (and no membership round trip);
genuine multi-org member on their second org; internal staff; org admin/owner on
their own org (no round trip); stale token role resolved from the membership row;
multi-org owner on each owned org; internal system admin.

**DENY** — member of org-a on org-b's path (403); inactive membership (403);
viewer on another tenant (403); Processing Entity staff (403); entity staff named
`admin` with `is_superuser` (403 — D20 scope-first); non-admin member on the
admin-only delete (403); unauthenticated (401); **cross-tenant routes never touch
the handler's data tables** (asserted on the fake store); 403-not-500 when the
membership store is unconfigured or raises; `maybe_single` is not used on the
admin path.

**HTTP-level (the reported route):** `POST /api/organizations/{org_b}/exports/exports/emissions`
as an org-a member → **403** with zero handler-side queries;
`POST …/{org_a}/exports/exports/emissions` → 200; viewer listing org-b → 403;
admin delete cross-tenant → 403; same-org paths still succeed; no credentials →
401.

**Composed real application (the 35th test):**
`test_composed_legacy_app_exposes_and_guards_the_reported_route` performs the same
ALLOW/DENY pair against the **real `backend/main.py` app** (route present in its
OpenAPI document; cross-tenant → 403 with no table access; own-tenant → 200), so
the guarantee is proven at the composition root and not only on a standalone
router instance.


---

## 4. F-05-R2 / F-05-R4 — the three runtime 500s and the NULL-relation read

### 4.1 F-05-R2.1 — PDF table shading (`backend/report_generator.py`)

`add_data_table` called `set_fill_color(248, 248, 248 if fill else 255, 255,
255)` — five channel arguments, which FPDF rejects (`takes from 2 to 4 positional
arguments but 6 were given`), aborting report generation. It now selects the
alternating row colour explicitly (`248,248,248` for the shaded row, `255,255,255`
otherwise), which is the evident intent of the expression.

Tests: `test_r2_1_add_data_table_does_not_raise_type_error` renders a real PDF
through the production class; `test_r2_1_no_set_fill_color_call_passes_more_than_three_channels`
is a static guard over the whole backend.

### 4.2 F-05-R2.2 — `GET /api/organizations/{org_id}/organization-activity`

Two **non-existent** columns were selected. Evidence from the canonical schema
(`supabase/migrations/00000000000000_init_schema.sql`):

* `public.users` (line 260) = `id, email, password_hash, first_name, last_name,
  user_type, is_active, email_verified, last_login, created_at, updated_at,
  is_anonymised` — there is **no** `raw_user_meta_data` (the embed's
  `raw_user_meta_data->>'full_name' as full_name` produced the reported
  `42703 column users_1.raw_user_meta_data does not exist`);
* `public.organization_members` (line 277) = `id, organization_id, user_id, role,
  created_at, is_active, updated_at` — there is **no** `joined_at` (so the
  reported 500 was the first of two: the second would have failed next).

The route now selects `created_at` and embeds
`users!inner (email, first_name, last_name)`, and composes the display name from
`first_name`/`last_name` (`full_name` is no longer fabricated). The pre-existing
defect class is already recorded in
`supabase/migrations/20260925000000_p8_rls_4b_group1_enablement.sql:51–60`: the
`users` peer reads select non-existent `full_name`/`avatar_url`/
`raw_user_meta_data` columns.

Tests: the route is exercised end-to-end against a fake service client that
rejects non-canonical columns exactly as PostgREST does (so re-introducing either
column fails the suite); a sensitivity control asserts the fake **does** raise
`42703` for the original select; a static guard scans the route's select
literals.

### 4.3 F-05-R2.3 — `GET /api/organizations/data/{org_id}/emissions-data`

`response_model=EmissionsResponse` requires `organization_id` and `summary`, but
the handler returned only `{records, total}`, so FastAPI failed response
validation and answered 500. The handler now returns the declared contract —
`organization_id`, `organization_name` (already fetched), `period_start`,
`period_end`, `records`, `summary` (via the existing
`calculate_emissions_summary`) — and the model also declares the previously
returned `total` so existing consumers keep it.

Tests: the handler is called directly and the payload is validated against the
production `EmissionsResponse`; a sensitivity control proves the pre-fix
`{records, total}` payload fails that model.

### 4.4 F-05-R4 — NULL embedded relation

`record.get('assets', {}).get(...)` raises `AttributeError` when PostgREST
returns `"assets": null` for a null relation. The own-tenant read paths now use
`(record.get('assets') or {})` in the activity feed, the emissions-data
transform, the CSV export and the shared summary helper. Tests cover a NULL-asset
row alongside a populated one.

### 4.5 Tests (8, all passing)

`backend/tests/unit/api/test_f05_r2_r4_runtime_defects.py`.


---

## 5. Test summary

| Suite | Command (from `backend/`) | Result |
|---|---|---|
| F-05-R1/R3 authorization matrix (new) | `python -m pytest tests/unit/api/test_f05_r1_org_scope_authorization.py` | **35 passed** |
| F-05-R2/R4 runtime defects (new) | `python -m pytest tests/unit/api/test_f05_r2_r4_runtime_defects.py` | **8 passed** |
| Both new files together | `python -m pytest tests/unit/api/test_f05_r1_org_scope_authorization.py tests/unit/api/test_f05_r2_r4_runtime_defects.py` | **43 passed, 100%, exit 0** |
| CT-IMPLEMENT-04 remediation (includes the widened F-05-R7 guard) | `python -m pytest tests/unit/test_ct_implement_01_remediation.py` | **34 passed, 100%, exit 0** |
| Full unit suite | `python -m pytest tests/unit` | see §5.1 |

The 43-test figure decomposes exactly: 13 unparametrized + 21 parametrized + 1
composed-app test = **35** in the R1/R3 file, plus **8** in the R2/R4 file.

The composed-app test (`test_composed_legacy_app_exposes_and_guards_the_reported_route`)
is the strongest single piece of evidence in the change-set: it drives the
**real `backend/main.py` application** over HTTP with the real `require_org_member()`
chain and a DB-free service-role fake, and shows **403 for the other tenant**
(handler never touches a table) and **200 for the caller's own tenant**.

All new tests are DB-free: real guards, real routers, fake service-role client;
the canonical database and the investor-demo dataset are never opened.

### 5.1 Full unit-suite result and the A/B proof for the 10 failures

The full unit suite in the final state runs **3,840 tests: 3,830 passed, 10
failed** (10 `FAILED` node ids, progress `[100%]`). All 10 failures are
**pre-existing and unrelated to this change-set**. This was **measured**, not
assumed: the same suite was run with this change-set stashed (i.e. against
baseline HEAD `dc3d78dc8021…`) and the extracted, sorted `FAILED` node-id lists
diff **clean (`diff` exit 0)** — the two sets are **identical**, so no test that
passes at baseline fails with this change-set, and the change-set adds only
passing tests.

| Pre-existing failure | Why it is unrelated |
|---|---|
| `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | asserts `len(migrations) == 71`; the canonical tree has **92** |
| `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | migration-order expectation predates `ct02_*` migrations |
| `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | expects the I2/P3 migration to be last; `20261023000000_ct02_scheduled_reporting.sql` is |
| `tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | same `ct02_*` migration drift |
| `tests/unit/engines/test_extraction_suggestions.py` (3 tests) | engine-level extraction suggestions |
| `tests/unit/api/test_review_sla_surfaces.py` (3 tests) | expects `/api/v3/ops/*` and `/api/v3/admin/sla/*` in a deliberately narrow test app whose only registered path is `/api/v2/health` |

The migration-pinned tests and the SLA-surface tests are **not** validation of the
canonical schema, which is unchanged by this change-set (no migration added,
edited or removed).

### 5.2 Integration / PostgREST suites were deliberately **not** run

`backend/tests/integration/conftest.py`'s `pool` fixture executes
`TRUNCATE … RESTART IDENTITY CASCADE` against whatever `INTEGRATION_DATABASE_URL`
names, and (per AGENTS.md §55.1 / F-046-1) that fixture **refuses** any target whose
name matches `qa`, `demo`, `investor`, `prod` or `live`. No disposable clone
(`ct_*`) was created for this task, so the only compliant decision was to **not**
run those suites: the canonical database and the investor-demo dataset were not
touched. Every claim in this report is therefore either (a) unit-level evidence
using the real guards/routers with DB-free fake service-role clients, or (b)
static/structural evidence from the repository. Live end-to-end verification is
item 1 in §9 (CT-VERIFY-06), to be run against a disposable clone.

---

## 6. Informational findings — recorded, and F-05-R7 fixed

* **F-05-R5 (documentation inaccuracies in the frozen CT-IMPLEMENT-04 report) —
  RECORDED, DELIBERATELY NOT CHANGED.** Correcting the frozen report would
  invalidate its §1, so the CT-VERIFY-05 facts stand as written and the correct
  values are restated here for future citation:
  * `_REPOINTED_FILES` = **11** entries (not 12);
  * **13 unparametrized tests + 21 parametrized cases = 34** (the phrase "13 test
    functions (34 parametrized cases)" is the accurate reading); that 34 is the
    count CT-VERIFY-05 measured — the file has since gained one further test (the
    composed-app test added by this change-set), so it now reports **35**;
  * the 34-case guard result comes from `/usr/bin/python3`; the repo `.venv` has
    no pytest.
* **F-05-R6 (inventory drift) — RECORDED.** `docs/**` now measures 300
  occurrences across 68 files (report: 82); `supabase/**` = 8 occurrences in 3
  files (historical migrations/comments, absent from the report's table);
  `prisma/seed.ts` does not exist (the single `seed.ts` is root-level); 
  `frontend/node_modules/.cache` is outside every source scan root by design.
* **F-05-R7 (scan-root coverage gap) — FIXED.** `_LEGACY_SCAN_ROOTS` in
  `backend/tests/unit/test_ct_implement_01_remediation.py` now walks
  `frontend/*.js` / `frontend/*.jsx` and `admin/*.js` / `admin/*.jsx`
  (recursively, with `node_modules`/`build`/`dist` excluded), so a new retired-name
  reference introduced into a root-level bundle now fails the confinement guard
  instead of passing silently. The module passes with the widened roots.
* **OBS-1 (new, not in CT-VERIFY-05) — legacy root bundle calls a non-existent
  `emissions-data` path: RECORDED, no change made.** The retired root bundle
  `frontend/App_.js:289` requests
  `/api/organizations/${organization.id}/emissions-data`, while the only live
  route is `/api/organizations/data/{org_id}/emissions-data`
  (`backend/routes/organizations/data.py:92`, router prefix `…/data`). This is
  **not** a live defect: the served frontend is the CRA app
  (`frontend/package.json` → `react-scripts`, build root `frontend/src/…`), which
  does not call that endpoint at all (`grep -rn 'emissions-data' frontend/src` →
  no matches), and the legacy call site already falls back to
  `/api/emissions?organization_id=…`. Recorded here so the mismatch is not
  mistaken for the F-05-R2.3 defect, which was a server-side 500 on the correct
  route.
* **F-05-R8 (out-of-scope defects re-confirmed) — unchanged, see §7.**



---

## 7. Explicitly out of scope (PO-gated, not invented here)

Per AGENTS.md §62 (do not silently change business policy) and CT-VERIFY-05 §6.4,
the following were **not** assessed or changed by this task:

* **PD-3 / PD-4 / PD-5 surfaces** — admin factor management
  (`routes/admin/defra.py`, `admin/src/**`), manual-entry factor lookup
  (`routes/reports.py`), and the other PO-gated behaviours. They still name the
  retired `defra_conversion_factors` table and remain in the confinement
  allowlist; no PO decision was taken by this change-set.
* **F-04 hardening**, F-06/F-07/F-08 and the two divergent PD registers.
* Retired-name remediation in PD-gated files, retention configuration, messaging
  boundaries, billing/subscription configuration and upload-limit policy: these
  require ratified Product Owner decisions and were not implemented.
* No database migration was added (none was needed); no production or demo data
  was read, written or reset.

---

## 8. Verdict

**One verdict for the change-set:**
`F-05-R1, F-05-R3, F-05-R2.1/2/3 and F-05-R4 are IMPLEMENTED and TESTED in-repo
(43 targeted regression tests passing — 35 authorization + 8 runtime-defect — and
a full unit suite of 3,840 tests with 3,830 passing and only the 10 proven
pre-existing failures); F-05-R7 is implemented. Acceptance is NOT claimed:
independent re-verification (CT-VERIFY-06) against a running stack — including a
live cross-tenant probe of the reported route with real tokens — is required
before this change-set may be described as ACCEPTED or released.`

What is *not* claimed:

* No end-to-end runtime verification against a live database/server was performed
  in this task (verification used DB-free HTTP-level tests with the real routers
  and real guards).
* No deployment, push, or investor-demo/QA data mutation occurred.
* The 10 pre-existing unit-suite failures remain (proven pre-existing by A/B).
* The integration/PostgREST suites were **not** run: their fixture truncates the
  target database (`TRUNCATE … RESTART IDENTITY CASCADE`, F-046-1) and no
  disposable clone was created (§5.2).
* The runtime 500s are fixed at the code level and covered by regression tests;
  they have not been re-run against the live canonical database.

---

## 9. Remaining work (recommended, in order)

1. **CT-VERIFY-06 (independent):** re-run the area-4 authorization probe on a
   disposable clone with two tenants' real tokens against the reported route and
   a sample of the other 101 path-scoped routes; confirm 403 cross-tenant and 200
   own-tenant; re-run the activity / emissions-data / PDF surfaces that
   previously returned 500.
2. Ratify the PD-3/PD-4/PD-5 surfaces before remediating their retired-table
   references (PO decision required).
3. Reconcile the migration-pinned unit tests with the current 92-migration tree
   (or record the drift as accepted) — a separate task.
4. Consider routing PD-3/PD-5 factor reads through the canonical
   `emission_factors` table once ratified.
5. Optional consistency task: align `ensure_org_access`'s token-scoped check with
   the DB-verified multi-organisation membership the guards now resolve (§3.4) —
   fail-closed today, so not release-blocking.

---

## 10. Evidence and reproducibility

* New tests: `backend/tests/unit/api/test_f05_r1_org_scope_authorization.py`
  (**35**), `backend/tests/unit/api/test_f05_r2_r4_runtime_defects.py` (**8**) —
  together **43 passed, `[100%]`, exit 0**.
* Full unit suite (final state): **3,840 tests run, 3,830 passed, 10 failed** —
  the 10 `FAILED` node ids are identical to the stashed-baseline run
  (`diff` exit 0), and the run includes the 43 new tests.
* `tests/unit/test_ct_implement_01_remediation.py` with the widened
  `_LEGACY_SCAN_ROOTS`: **34 passed, `[100%]`, exit 0**.
* Composed-application evidence: `backend/main.py`'s OpenAPI document contains
  `/api/organizations/{org_id}/exports/exports/emissions` (POST) among 606 paths,
  and the same route answers **403** cross-tenant / **200** own-tenant under the
  real guard chain (`test_composed_legacy_app_exposes_and_guards_the_reported_route`).
* Frozen guarded-route surface: 102 route declarations / 87 distinct
  `METHOD path` pairs, enumerated by AST and asserted by
  `test_org_scoped_guard_surface_is_frozen`.
* Canonical-schema evidence for F-05-R2.2:
  `supabase/migrations/00000000000000_init_schema.sql:260–288` (`public.users`,
  `public.organization_members`) and
  `supabase/migrations/20260925000000_p8_rls_4b_group1_enablement.sql:51–60`.
* FastAPI behaviour claims (Request injection into a nested checker with a `None`
  default; the no-parentheses bypass) were reproduced against the pinned
  `fastapi 0.141.1` in this environment.
* A/B baseline proof: the 10 full-suite failures were re-produced with this
  change-set stashed (`git stash push -- backend/auth.py
  backend/report_generator.py backend/routes/organizations/dashboard.py
  backend/routes/organizations/data.py`), then restored with `git stash pop`
  (single stash; working tree verified afterwards, and `git stash list` is
  **empty** in the final state — nothing was left behind).
* OBS-1 evidence: `grep -rn 'emissions-data' backend/routes` → the single route
  `backend/routes/organizations/data.py:92` under prefix `/api/organizations/data`;

  `grep -rn 'emissions-data' frontend/src` → no matches;
  `frontend/App_.js:289` is the legacy call site and `frontend/package.json`
  builds with `react-scripts` (root `frontend/src/…`), so the legacy bundle is
  not the served frontend.
* Guard-definition evidence: `backend/auth.py:575` (`require_org_member`) and
  `backend/auth.py:616` (`require_org_admin`); `backend/api/dependencies.py:34–35`
  re-exports both with `# noqa: F401` and defines neither.
* Working tree in the final state: 13 modified tracked files = **5 in this
  change-set** + 8 pre-existing (listed in §2.2); 2 new test files; 1 report file;
  `git stash list` empty; HEAD unchanged at `dc3d78dc8021…`.

---

## 11. Addendum — CT-FINAL-01 ratified PO scope implementation (2026-09-28)

This addendum extends the report above. It records the work done under the
**ratified production PO scope** after the F-05-R remediation change-set: the
previously PO-gated items (§7) are no longer pending, because the Product Owner
ratified the scope and the implementation was carried out against it.

**Deployment: none.** No push, no deploy, no production or investor-demo data
was read, written or reset, and no production migration was applied. All work is
uncommitted working-tree state on `p8-release-reconciled`.

### 11.1 What §7 said before, and what is now true

| §7 item (previous position) | Ratified decision | Status now |
|---|---|---|
| PD-3 admin factor management names the retired table | ratified: migrate the admin surface onto the canonical `emission_factors` implementation | **IMPLEMENTED** (frontend migrated off direct table access to the API service; backend admin factor API is the single path) |
| PD-4 orphan legacy audit console | ratified: **retire** it with a documented replacement note | **IMPLEMENTED** — see §11.3 |
| PD-5 manual-entry factor read | ratified: repoint onto canonical factors | **IMPLEMENTED** (`frontend/src/components/ManualEntryStandalone.jsx`; `backend/routes/reports.py` factor read) |
| F-04 hardening | ratified: a missing factor is a **blocking** validation state on write paths | **IMPLEMENTED** — see §11.4 |
| Notifications | ratified: actor ≠ sender; admin-configurable platform sender | **IMPLEMENTED** — see §11.5 |
| Upload limits | ratified: 10MB/file · 50 files/batch · 500MB/batch, server-side | **IMPLEMENTED** — see §11.6 |
| Retention | ratified: purpose-based retention documentation; no unsafe blanket deletion | **IMPLEMENTED (docs)** — see §11.7 |
| No database migration was added | retained | one **storage-configuration** migration added for the bucket size limit (§11.6); no application-schema change |

### 11.2 Files changed by this addendum's scope

| File | Change |
|---|---|
| `backend/utils/emissions.py` | F-04 primitives: `FactorUnresolvedBlocked`, `FACTOR_BLOCKED_CODE`, `factor_blocked_detail()`, `require_emission_factor()` |
| `backend/routes/drafts.py` | F-04: pre-write factor resolution (409 on block); removed the fabricated `2.68` default; factor-provenance metadata |
| `backend/routes/documents_main.py` | F-04: factor resolved **before** the approval status change (409 on block); no null factor reference; provenance metadata |
| `backend/routes/admin/extraction.py` | F-04: import swap to `require_emission_factor`; blocking 409 on both resolution points; provenance metadata |
| `backend/services/email_sender.py` | **new** — sender validation/resolution, actor vs sender identity, no secret handling |
| `backend/services/v3_email.py` | single source of truth for the default sender + `resolve_configured_sender()` |
| `backend/data/settings.py` | `get_notification_sender()` / `update_notification_sender()` on `setting_value` JSONB (no schema change) |
| `backend/api/v3_settings.py` | admin-only `GET`/`PUT /api/v3/settings/notification-sender` |
| `backend/api/v3_organizations.py`, `backend/api/v3_discovery.py`, `backend/services/operational_alerting.py` | transactional email now resolves the configured platform sender |
| `backend/utils/upload_limits.py` | **new** — ratified caps, ceiling semantics, `enforce_single_file` / `enforce_batch` |
| `backend/api/v3_documents.py` | upload-limit enforcement at the canonical document choke point |
| `backend/routes/organizations/files.py` | upload-limit enforcement on single + bulk ingress (limits raised to platform caps; reads de-duplicated) |
| `backend/routes/upload.py` | legacy ingress capped by the ratified ceiling |
| `supabase/migrations/20261024000000_ct_final_01_documents_bucket_size_limit.sql` | **new** — storage-layer alignment (10MB + private), guarded/idempotent, no application schema change |
| `tools/demo_lab/storage.py` | lab `documents` bucket provisioned at the ratified cap |
| `backend/routes/admin/audit_logs.py` | **removed** (PD-4 retirement; git-recoverable, hash recorded) |
| `backend/tests/unit/api/test_f04_factor_write_path_blocking.py` | **new** — 20 F-04 tests |
| `backend/tests/unit/api/test_ct_final_01_notification_sender.py` | **new** — sender + admin API ALLOW/DENY tests |
| `backend/tests/unit/api/test_ct_final_01_upload_limits.py` | **new** — limit + storage-configuration tests |
| `backend/tests/unit/api/test_pd4_legacy_audit_retirement.py` | **new** — retirement guard tests |
| `backend/tests/unit/api/fakes.py` | `_SettingsStub` gained the notification-sender surface |
| `docs/architecture/CT-FINAL-01-PD-4-LEGACY-AUDIT-RETIREMENT-20260928.md` | **new** — PD-4 retirement record |
| `docs/architecture/CT-FINAL-01-RETENTION-PURPOSE-AND-CONFIGURATION-20260928.md` | **new** — purpose-based retention documentation |


### 11.3 PD-4 — legacy audit console retired (with the replacement documented)

`backend/routes/admin/audit_logs.py` (1,431 lines, 12 endpoints) was **orphan
code**: never imported, never registered, never covered by the startup
completeness check, and one of its handlers queried the non-existent
`notification_delivery_log` table (SCM-007). The ratified decision was
*retire*, so the module was deleted rather than migrated.

Evidence that records were **not** retired with it:

* No migration in the chain is dropped or altered; the DB-0001 immutability
  migration `20260831020000_audit_activity_immutability.sql` still pins
  `audit_logs` / `activity_logs` / `document_activity_log` as
  **retained-but-immutable**, and the Phase-7 migration
  `20260912000000_p7_audit_immutability_and_indexes.sql` still documents the
  canonical `audit_trail` ledger alongside them.
* The canonical writer (`backend/data/audit.py`) and the registered read
  surfaces (`/api/v3/ops/reporting/audit`, `/api/v2/admin/audit`) are unchanged.
* `test_pd4_legacy_audit_retirement.py` locks all of the above, including a
  scan proving no runtime module imports the retired console or names the
  non-existent table.

The retirement record is
`docs/architecture/CT-FINAL-01-PD-4-LEGACY-AUDIT-RETIREMENT-20260928.md`; the
deleted file's content hash is recorded there so the removal is verifiable. The
module remains recoverable from git history (deletion is staged in the working
tree only; nothing was pushed).

### 11.4 F-04 — an unresolved factor is a blocking validation state on write

Previously a missing emission factor could be silently absorbed by a fabricated
`2.68` multiplier, producing an emissions figure with no provenance. The
ratified behaviour is now enforced on **every write path**:

| Path | Behaviour |
|---|---|
| `POST /api/drafts/{id}/submit` (`routes/drafts.py:390`) | factor resolved **before** the write; unresolved → **409** `FACTOR_UNRESOLVED_BLOCKED` |
| document approval (`routes/documents_main.py:492`) | factor resolved **before** the status change; unresolved → **409**, no partial approval |
| admin extraction approval (`routes/admin/extraction.py:111`, `:209`) | same guard at both resolution points |

Shared primitives live in `backend/utils/emissions.py`:
`FactorUnresolvedBlocked`, `FACTOR_BLOCKED_CODE = "FACTOR_UNRESOLVED_BLOCKED"`,
`factor_blocked_detail(activity_type, reporting_year)` and
`require_emission_factor(...)`. The three call sites import the same
implementation — there is no duplicated policy. The fabricated default is gone
(only explanatory comments remain), and each successful write records
factor-provenance metadata so the number stays traceable (AGENTS.md #17).

### 11.5 Notifications — actor, acting-for and sender are now distinct

The ratified scope separates three things that were previously conflated:

* **actor** — the authenticated user or system that performed the action;
* **acting_for** — the organisation/client/entity the actor acted on behalf of
  (consultant operating model), optional;
* **sender** — the From address of the platform email, which is **platform
  configuration, never the actor's mailbox**.

`backend/services/email_sender.py` is the single source of truth:
`DEFAULT_SENDER = "CarbonTally <notifications@carbontally.co.uk>"`,
`normalise_email_sender()`, `resolve_email_sender()`, `describe_email_sender()`
and `notification_identity()`. `services/v3_email.py` aliases the default
(`DEFAULT_FROM_EMAIL`) instead of defining a second one, and exposes
`resolve_configured_sender()`; `api/v3_organizations.py`, `api/v3_discovery.py`
and `services/operational_alerting.py` now send through the configured sender.

Configuration is admin-only and server-side:

* `GET /api/v3/settings/notification-sender` — describe the effective sender;
* `PUT /api/v3/settings/notification-sender` — set it (`Depends(require_admin())`,
  **called**, so the guard cannot silently no-op);
* storage is the existing `system_settings.setting_value` JSONB row (key
  `platform_notifications`) — **no schema change and no migration**.

Guard rails: only CarbonTally platform domains may be configured (a
customer/consultant domain requires the externally verified-sender mechanism,
D19 §13); invalid, multi-address or header-injection values raise `ValueError`
and are never used; `resolve_email_sender()` degrades to the ratified default
rather than failing delivery; and **no delivery credential is read, returned or
logged** by the module (`RESEND_API_KEY` is out of its scope entirely).


### 11.6 Upload limits — ratified caps enforced server-side

Ratified limits: **10 MB per file · 50 files per batch · 500 MB per batch**.
They are enforced by `backend/utils/upload_limits.py`
(`MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024`, `MAX_FILES_PER_BATCH = 50`,
`MAX_BATCH_TOTAL_BYTES = 500 * 1024 * 1024`) through a single
`UploadLimitExceeded` error (`413`) and the `enforce_single_file()` /
`enforce_batch()` gates, at three ingress points:

| Ingress | Enforcement |
|---|---|
| `api/v3_documents.py` (canonical document API) | `enforce_single_file` + `enforce_batch` |
| `routes/organizations/files.py` (single + bulk) | both gates; the previously smaller per-request limits were raised to the platform caps so configuration matches the ratified product limit |
| `routes/upload.py` (legacy ingress) | `effective_file_limit_bytes()` ceiling |

**Ceiling semantics are explicit and tested:** a *lower* configured
organisation/bucket limit is honoured, but a configured value can never *raise*
the ratified ceiling — the platform limit is the maximum, not a default
(`effective_file_limit_bytes()`).

Storage-layer alignment is a separate, guarded migration:
`supabase/migrations/20261024000000_ct_final_01_documents_bucket_size_limit.sql`
sets the `documents` bucket's `file_size_limit` to the ratified 10 MB **only if
it is currently unset or larger** (configuration may tighten, never loosen),
re-asserts `public = FALSE`, and is a **no-op with a NOTICE** when
`storage.buckets` does not exist (`to_regclass('storage.buckets') IS NULL`), so
the migration chain still applies cleanly on a non-Supabase database. It
touches **no application table**. `tools/demo_lab/storage.py` provisions the lab
bucket at the same cap so local verification matches production intent.

### 11.7 Retention — documented by purpose, nothing deleted

The ratified item was a *documentation* deliverable, and that is all it is:
`docs/architecture/CT-FINAL-01-RETENTION-PURPOSE-AND-CONFIGURATION-20260928.md`
records retention **by purpose**, and explicitly states that **UK GDPR does not
prescribe a number of years** (Art. 5(1)(e) requires a purpose-based
justification), so no "GDPR requires N years" claim is made anywhere. Where a
long period (≈6–7 years) is used, it is justified as a *commercial/accounting*
position — the prudent superset of the Companies Act 2006 s.388 minimums and the
HMRC expectation of roughly six years — never as a statutory obligation.

Nothing about retention behaviour changed: no duration was invented, no
enforcement path was re-pointed, no domain was added to a purge set, and no
migration was added. The documented guarantees are the existing ones — per-domain
opt-in enforcement, "not configured means nothing is purged", the explicit
never-purge set (`document_processing_queue`, `processing_logs`,
`report_versions`, `report_version_artifacts`, `evidence_line_items`,
`calculation_snapshots`, `emissions_logs`, `audit_trail`), soft-delete only, and
dry-run by default.

### 11.8 Verification evidence

All runs below are local, offline unit/API tests (in-memory fakes; no database,
no network, no storage). Baseline A/B is `dc3d78dc8021…` on detached HEAD in an
isolated `git worktree` at `/tmp/ct2_baseline`, so the uncommitted working tree
was never stashed, reset or otherwise disturbed.

| Run | Result |
|---|---|
| F-04 (`test_f04_factor_write_path_blocking.py`) | **20 passed**, `[100%]`, exit 0 |
| CT-FINAL-01 focused set — F-04 + notification sender + upload limits + PD-4 + `test_v3_settings.py` | **73 passed**, `[100%]`, exit 0 (20 + 25 + 16 + 7 + 5) |
| `tests/unit/api` (whole directory, working tree) | **1,917 collected — 1,914 passed, 3 failed** (the 3 are pre-existing; see below) |
| `tests/unit/api` (whole directory, baseline `dc3d78d` worktree) | **1,806 collected — 1,803 passed, 3 failed** — the *identical* three node ids |
| PD-3 residue scan + import/app-construction check (`/tmp/ct2_verify_pd3.py`) | exit 0; `routes.admin.defra`, `routes.reports`, `utils.factor_catalogue`, `routes.admin.extraction`, `routes.drafts`, `routes.documents_main`, `services.email_sender`, `services.v3_email`, `utils.upload_limits`, `api.v3_settings`, `main` all import; composed app constructs |

The +111 collected tests in the working tree are the new files of the CT-FINAL-01
scope — **68** tests (F-04 20, notification sender 25, upload limits 16, PD-4 7) —
plus the earlier uncommitted F-05-R remediation tests
(`test_f05_r1_org_scope_authorization.py` 35, `test_f05_r2_r4_runtime_defects.py`
8) — all passing, and none of them is collected in the baseline worktree because
none is committed.

**The three failures are pre-existing and unrelated.** They assert that
`api.router.router` (the module-level router) already contains
`/api/v3/ops/sla/settings`, `/api/v3/ops/review/{review_id}/assign` and
`/api/v3/admin/sla/settings`; at import time the module-level router exposes only
`/api/v2/health` because the v3 families are attached during application
composition. The baseline worktree reproduces exactly the same three failures
with **no** CT-FINAL-01 change present, which is the A/B proof that this
change-set neither caused nor masked them. They are recorded as a pre-existing
test defect (the tests inspect the wrong object), **not** as a product defect and
**not** fixed here — fixing them is outside the ratified scope.

PD-3 residue scan result: the retired `defra_conversion_factors` name survives
only in (a) two *prohibitive comments* (`backend/routes/reference.py:60-62` and
the header of `backend/tests/unit/test_ct_implement_01_remediation.py`), which
document why the table must not be used, and (b) historical artefacts —
`supabase/migrations/20260800000000_rc2_schema.sql`,
`20260806000000_rc2_verification.sql`, `supabase/snippets/`, and the
`docs/Final_Kimi/…` audit reports. Migrations are the immutable historical record
and are deliberately not edited. **No runtime code path queries the retired
table**, and `test_ct_implement_01_remediation.py` enforces that with an explicit
allowlist.

### 11.9 Security verification

* **Admin-only configuration, verified by test, both directions.** The
  notification-sender `PUT` is guarded with `Depends(require_admin())` — the
  *called* form; the uncalled form silently disables the guard (a hazard this
  change-set explicitly tests against). The tests assert both ALLOW (admin) and
  DENY (non-admin) responses, and assert `admin_checker` appears in the route's
  dependency list, so the guard cannot be dropped without failing a test.
* **No new trust in the UI.** Both new capabilities are server-side: upload
  limits are enforced in the request handlers (a client that lies about size gets
  `413`), and the sender is validated server-side.
* **Injection and spoofing are closed by construction.** `normalise_email_sender`
  rejects CR/LF/TAB, comma/semicolon/colon, quotes, bare addresses without a
  domain, and any non-platform domain, so neither header injection nor sending
  from a customer/consultant domain is possible through this setting.
* **No secret exposure.** No credential is read, returned, logged or written by
  `services/email_sender.py`; the retention and notification documentation
  contains no tokens or signed URLs.
* **Retention cannot be used as a delete-all lever.** The never-purge set and the
  dry-run default are unchanged and still asserted by existing tests.

### 11.10 Remaining limitations, and what is deliberately not claimed

* **Not deployed, not committed, not pushed.** The whole change-set is
  uncommitted working-tree state on `p8-release-reconciled` at HEAD
  `dc3d78dc8021…`. No production environment, no investor-demo database and no
  hosted storage was read, written, migrated or reset; the new migration has
  **not** been applied to any environment. The new tests are offline unit/API
  tests over in-memory fakes — they are **not** evidence that the migration has
  been run against a real Supabase project.
* **The bucket-size migration is unverified against live storage.** It is
  reviewed-by-inspection only; it must be exercised on a disposable environment
  before any production apply (F-046-1 discipline: never against a persistent or
  data-bearing database).
* **PD-3's frontend migration is verified by source and by the API contract**,
  not by a browser session — no UI test run was performed in this change-set.
* **No independent verification has been performed.** This report records
  IMPLEMENTED and TESTED (locally). It does **not** claim VERIFIED or ACCEPTED:
  those verdicts require independent QA (OHD / harness) against the affected
  workflows, and for the migration, a real database.
* **Still PO-gated (unchanged by this scope):** retention durations for the three
  `PO DECISION REQUIRED` domains (platform security logs, messages, onboarding
  data); whether the pre-existing `test_review_sla_surfaces.py` defect should be
  fixed or the tests retired; MFA enforcement in production.
* **Not started, deliberately:** CT-VERIFY-06.
* Pre-existing repo noise left untouched (not created by this change-set):
  untracked zero-byte files `8` and `=` at the repo root (dated 2026-09-23),
  `.costrict/`, `.p18_audit_tmp/`, and the accumulated untracked docs.

### 11.11 Verdict for this addendum

    CT-FINAL-01-PO-SCOPE-IMPLEMENTED

Every item of the ratified production PO scope is implemented, regression-tested
locally and recorded in the security-relevant detail above, with the three
pre-existing `test_review_sla_surfaces.py` failures proven pre-existing by an
isolated baseline worktree A/B run rather than assumed. Nothing was deployed,
committed or pushed, and no environment data was touched.

