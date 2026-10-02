# CT-FINAL-02 — Final Local/Disposable Rehearsal Report

**Date:** 2026-10-01
**Author:** Cline (implementation/rehearsal author — **not** an acceptance authority)
**Repository:** `/home/shomonrobie/ct_93d5cdd` · branch `p8-release-reconciled` · HEAD `cabdca8380415e73a25cf23eb393d0b15c0af391`
**Basis:** `docs/architecture/CT-FINAL-02-20261001-LIVE-EVIDENCE-CLOSURE-PASS-REPORT.md`,
`docs/architecture/CT-FINAL-02-20260930-REHEARSAL-BASELINE-AND-GAP-MATRIX.md`,
`docs/architecture/CT-FINAL-02-INDEPENDENT-VERIFICATION-REPORT.md`
**Task authority:** "FINAL-02 Final Local Rehearsal & Acceptance Preparation" (not FINAL-03).

---

## Status

> **FINAL-02 REHEARSAL COMPLETE — READY FOR INDEPENDENT ACCEPTANCE**

This report does **not** accept FINAL-02. Acceptance is CoStrict/OHD's to grant.

---

## 1. Objective and authorization boundary

Close the remaining FINAL-02 evidence gaps **by rehearsal against the existing
head-complete disposable database `ct_final02_src`**, using only pre-existing local
identities, and hand the result to independent acceptance.

Hard stops observed throughout (see §13 for the confirmation):

* no production mutation, no production migration, no production provisioning;
* no production email; no deployment; no FINAL-03 work;
* no new database was created; no repository file was changed by the rehearsal
  itself (only this report was added);
* the canonical migration history was not rewritten; no RLS policy, predicate,
  threshold or decision was changed or reopened;
* no new role, rule, provider or architecture was introduced.

## 2. Inspection performed first (read-only)

| Checked | Result |
| --- | --- |
| `git status --short`, HEAD, branch | 130 working-tree entries (pre-existing), `cabdca8`, `p8-release-reconciled` — **preserved, untouched** |
| FINAL-02 reports | live-evidence closure pass, rehearsal baseline & gap matrix, independent verification, email/upload configuration |
| Working harnesses | `e2e/environment/**` (isolated P6-2F stack), `qa_harness/**` (build-only QA harness incl. the credential provider), `tools/demo_lab/**` (DEMO-T1 local lab topology) |
| Local stacks | CLI stack `carbon_ledger` (54425 API / 54426 DB) → DB `postgres`; demo-lab stack (`carbontally_demo_lab_*`, gateway 54430) → DB `carbontally_demo_local`; app-wired DB `ct_local_93d5cdd`; **head-complete `ct_final02_src`** |
| `ct_final02_src` | 149 public tables / 149 RLS-enabled / 271 policies / 7,049 factors / 1,206 auth users / 975 organisations / `documents` bucket private, 10 MiB / 685 storage objects |
| App wiring | `backend/.env` → `ct_local_93d5cdd` + unroutable `SUPABASE_URL` (19999); `frontend/.env.local` → demo-lab gateway 54430 — i.e. the previously reported incoherence, **left untouched** |

**Preserved:** every pre-existing modification and untracked file. Nothing was reset,
cleaned, stashed or discarded.

## 3. Environment established for the rehearsal

The previous pass recorded that the local path was incoherent (application → one DB,
API → another, no Auth on the app-wired DB). A **single coherent, disposable path**
was established over the existing rehearsal database, without touching any existing
container, database or repository file:

```text
gateway   http://127.0.0.1:54440   nginx (the only published port, replaced demo-lab style)
rest      ct_final02_rest          PostgREST v14.5      -> ct_final02_src
auth      ct_final02_auth          GoTrue  v2.195.0     -> ct_final02_src   (real password grants)
storage   ct_final02_storage       storage-api v1.69.0  -> ct_final02_src   (+ private byte-store copy)
app       uvicorn :8090            CarbonTally FastAPI  DATABASE_URL->ct_final02_src, SUPABASE_URL->:54440
browser   CRA dev server :3100     carbon frontend      REACT_APP_SUPABASE_URL->:54440
```

* Each service container was created from **the same image and the same environment
  the running local stack uses**; the only differences are the database name in the
  service DSNs and the published gateway port.
* The storage byte store is a **read-only copy** of the stack volume
  (`supabase_storage_carbon_ledger` → volume `ct_final02_storage_data`, 686 files,
  9.7 MB). The source volume is never written.
* Nothing in `carbon_ledger`, `carbon_ledger`'s databases, the demo-lab stack, the
  repository, or production was modified. Teardown is
  `bash /home/shomonrobie/ct_local_env/final02_rehearsal/stack_down.sh --purge`.


## 4. Database used, and its measured state

**Database: `ct_final02_src`** (existing local cluster `supabase_db_carbon_ledger`).
No new database was created. Measured again during this pass (before and after the
rehearsal — identical):

| Fact | Value |
| --- | --- |
| Public base tables | **149** (canonical head) |
| RLS-enabled tables | **149** |
| Policies (public) | **271** |
| Emission factors | **7,049** (authoritative data set) |
| Auth users / identities | **1,206** / 1,206 (all with password hashes) |
| Organisations / memberships | 975 / 1,125 |
| `documents` bucket | **private**, `file_size_limit = 10485760` (10 MiB — the ratified ceiling) |
| `storage.objects` | 685 at start → **686** after the rehearsal (see §11) |
| `d32_documents_*` policies | present (select/insert/update/delete, `authenticated`, org-folder predicate) |
| `system_settings` | `analytics_ga4`, `platform_retention` (no `email_provider` row) |

The schema, RLS surface, factor library and RLS policies were **not changed**: 149
tables, 271 policies and 149 RLS-enabled tables before and after.

## 5. Findings produced while establishing coherence

Two **fidelity gaps in the disposable rehearsal database itself** (not application
defects, and not present on a stack built by the canonical chain) had to be repaired
before the platform services could run against it. Both were measured first, repaired
narrowly, and verified.

### F-A · Platform schema privileges were absent (measured, then restored)

```text
pg_namespace.nspacl @ postgres        auth/storage : full Supabase platform ACL set
pg_namespace.nspacl @ ct_final02_src  auth/storage : NULL
effect:  supabase_auth_admin / supabase_storage_admin had NO usable search_path
         (current_schemas(false) = {}), so GoTrue died with
         "no schema has been selected to create in" and the storage API with
         "relation \"migrations\" does not exist" (or 42501) — even though the
         objects existed.
fix:     prepare_platform_grants.py — 785 GRANT statements generated from the
         SOURCE stack's own catalogs (schemas, relations, sequences, functions)
         applied to ct_final02_src; verified 0 source ACLs missing in the target.
```

### F-B · Platform object ownership was not carried into the clone (measured, then restored)

```text
storage.migrations owner @ postgres        = supabase_storage_admin
storage.migrations owner @ ct_final02_src  = postgres
=> has_table_privilege('supabase_storage_admin','storage.migrations','SELECT')
      source: true    rehearsal: false  -> storage API "permission denied for table migrations"
fix: prepare_platform_ownership.py — 166 ALTER ... OWNER TO statements restoring the
     source owners (ALTER requires the provider role; executed as supabase_admin with
     the database container's own local dev credential, which is never printed).
     Verified: 166/166 applied, 0 mismatches, ownership matches source.
```

### F-C · `public` privilege baseline was absent (measured, then restored with the repo's own scripts)

```text
authenticated SELECT @ postgres 108/116 tables -> @ ct_final02_src 38/149
service_role  SELECT @ postgres 115/116 tables -> @ ct_final02_src 43/149
anon          SELECT @ postgres 107/116 tables -> @ ct_final02_src  0/149
fix: e2e/environment/scripts/grant_service_role.sql then
     e2e/environment/scripts/grant_authenticated.sql, applied VERBATIM to
     ct_final02_src (the repository's own isolated-stack provisioning scripts:
     RLS-derived `authenticated` DML + `service_role` baseline; `anon` deliberately
     untouched — the stricter posture the repository already chose).
after: service_role 149/149, authenticated 95/149 (RLS-derived), anon 0/149,
       RLS unchanged: 271 policies / 149 RLS tables.
```

**Positive evidence of fidelity:** PostgREST, GoTrue and the storage API all run
against `ct_final02_src` **as their canonical platform roles** (`authenticator`,
`supabase_auth_admin`, `supabase_storage_admin`); no role, guard or RLS policy was
weakened to make the rehearsal work.

**Observations reported, not fixed (out of this task's scope):**

1. `GET /api/organizations/{org_id}` returns **403 for an in-org owner** by its own
   guard design, and `GET /api/organizations/members/` returns **500** for an active
   org owner — both pre-existing and independent of the lifecycle flag (candidate for
   a separate bounded follow-up).
2. `frontend/src/App.test.js` cannot resolve `react-router/dom` — a frontend
   dependency-resolution defect (§10).

## 6. Identities used (roles/counts only — no credential is recorded)

All identities are **pre-existing local demo identities already present in
`ct_final02_src`**; none was created, provisioned or imported. The shared local demo
password was resolved through the **repository's own credential mechanism**
(`qa_harness/core/credentials.py`: environment override, else the gitignored local
credentials file) and is never printed, logged or stored.

| Role used | Count | Purpose |
| --- | --- | --- |
| Org A owner / admin / member / viewer | 4 | member path, admin authority, D-7 role matrix |
| Org B owner (second tenant) | 1 | cross-tenant deny + tenant-scoped denial |
| Consultant (active client grant to org A) | 1 | consultant path protection |
| Internal staff (`admin` staff role) | 1 | admin suspend/reactivate handler, staff continuity, audit |
| **Total distinct principals** | **7** | password-grant sign-in (GoTrue) for every one |
| Additional principals used in the auth probe | 2 | broader sign-in sweep (9/9 succeeded) |

**Real authentication, not fakes:** every request in §7/§8 presents a JWT obtained by
a real GoTrue password grant at the rehearsal gateway; no `get_current_user`
override, no direct-SQL assertion, no forged identity.

## 7. B5 — JWT / PostgREST / Storage isolation matrix — **29/29 PASS**

Script: `matrix_b5.py` (results: `logs/b5_matrix.json`). Org A =
`11111111-1111-4111-8111-111111111111`; Org B = `e5218a70-c235-5b73-a5a3-da029c995462`.

| # | Check | Expected | Actual |
| --- | --- | --- | --- |
| 1 | Real password grant (org A owner) | 200 | **200** |
| 2 | Token claims role/aud | authenticated | **authenticated/authenticated** |
| 3 | Wrong password refused | 400 | **400** |
| 4 | Expired token refused by PostgREST | 401 | **401** |
| 5 | Token signed with a wrong secret refused | 401 | **401** |
| 6 | Malformed token refused | 401 | **401** |
| 7 | **Org A → Org A rows** (emissions_logs) | 200 & rows>0 | **200, 78 rows** |
| 8 | Org A → Org B rows | 0 rows | **200, 0 rows** |
| 9 | **Org B → Org A rows** | 0 rows | **200, 0 rows** |
| 10 | **Org B → Org B rows** | 200 & rows>0 | **200, 1 row** |
| 11 | Org A member → Org A rows | 200 & rows>0 | **200, 78 rows** |
| 12 | Org A admin → Org A rows | 200 & rows>0 | **200, 78 rows** |
| 13 | Org A viewer → Org A rows | 200 & rows>0 | **200, 78 rows** |
| 14 | Anonymous → Org A rows | denied | **401, 0 rows** |
| 15 | Org B cannot read Org A `organizations` | 0 rows | **200, 0 rows** |
| 16 | Org B cannot read Org A `organization_members` | 0 rows | **200, 0 rows** |
| 17 | **Org B INSERT into Org A** | 403 | **403** (42501 `new row violates row-level security policy`) |
| 18 | Org B UPDATE of an Org A row | 0 rows / 403 | **200, 0 rows** |
| 19 | Org B DELETE of an Org A row | 0 rows / 403 | **200, 0 rows** |
| 20 | Org A downloads its own object | 200 | **200** |
| 21 | **Org B downloads its own object** | 200 | **200** |
| 22 | **Org B downloads an Org A object** | denied | **400** |
| 23 | Org A signs its own object | 200 | **200** |
| 24 | **Org B signs an Org A object** | denied | **400** |
| 25 | Org B signs its own object | 200 | **200** |
| 26 | Anonymous download refused | 401/400 | **400** |
| 27 | Service role downloads object | 200 | **200** |
| 28 | **Org B upload into an Org A path** | denied | **400** |
| 29 | Org B upload into its own path | 200 | **200** |

Notes. (a) A read denial is observed as an RLS-filtered empty set (PostgREST
semantics) while a **write** denial is a hard **403** — both are recorded verbatim.
(b) Check 29 wrote one object into the disposable database's own tenant path
(`uploads/<org B>/f02probe/f02.txt`); that is the +1 in `storage.objects` (§11).
(c) The storage byte store already contained bytes for both tenants, so the allowed
downloads returned real content, not metadata.

## 8. B4 — D-7 Decision B live-equivalent proof — **35/35 PASS**

Script: `matrix_b4_d7.py` (results: `logs/b4_d7_matrix.json`). The organisation
lifecycle flag was flipped **through the product's own admin handler**
(`POST /api/admin/bulk/organizations/status`, `require_admin()`), never by direct SQL.
`MEMBER_ROUTE = /api/organizations/team/<org A>/members`,
`CONTEXT_ROUTE = /api/v3/accounting/context`.

| Required evidence | Check | Actual |
| --- | --- | --- |
| 1. active organisation access works | 4 principals × member path + accounting context (baseline) | **200 for owner/admin/member/viewer** |
| — | admin handler suspends org A | **200, `success_count: 1`** |
| 2. suspended access denied | 4 principals × member path | **403 for all four** |
| 2b. suspended access denied (second route) | 4 principals × accounting context | **403 for all four** |
| 3. denial is non-disclosing | one message for every role | **1 distinct message** (`This organization is suspended`) |
| 4. member path protected | member/viewer denied | **403** |
| 5. consultant path protected | consultant + suspended client org | **403** on the client's accounting context |
| 6. owner/admin authority does not bypass | owner **and** admin denied | **403 / 403** |
| 7. internal staff unaffected | `/api/v3/admin/review-queue`, `/api/admin/audit/activity` | **200 / 200 while the tenant is suspended** |
| 8. tenant-scoped | org B's own member path while org A is suspended | **200** |
| 9. reactivation restores access | admin handler reactivates → 4 principals × both routes | **200 for all** |

Additional observations recorded: the consultant's **own** portfolio route
(`/api/v3/consultants/me/clients`) stays **200** while the client org is suspended
(the suspension is scoped to the client organisation, not the consultant's workspace),
and reactivation returns the org to `is_active = true` (verified in the database
afterwards).

## 9. B3 — Browser / admin verification — **PARTIAL (exact limitation recorded)**

Performed:

* the CarbonTally frontend (CRA dev server) was started **against the rehearsal stack**
  (`REACT_APP_SUPABASE_URL=http://127.0.0.1:54440`, `REACT_APP_API_URL=http://127.0.0.1:8090`)
  and **compiles and serves**: `GET http://127.0.0.1:3100/` → **200**;
* the served bundle `/static/js/bundle.js` contains the rehearsal gateway **3×**
  (`54440`) — i.e. the browser application is wired to the rehearsal stack, not to the
  demo-lab stack (54430) and not to production;
* **headless Chrome** (real browser, present at `/usr/bin/google-chrome`) rendered
  `/login`: **1.29 MB** of DOM, `id="root"` present, **150** form/input elements —
  the application UI renders, it is not a blank page or an error screen.

Not performed — **environment limitation, reported rather than worked around:**

> No scripted browser driver exists in this repository or environment
> (`playwright`, `puppeteer`, `cypress` are absent from `frontend/package.json`
> devDependencies and from `frontend/node_modules/.bin`; `qa_harness` lists
> Playwright as an **optional, currently-unavailable** tool, and running the QA
> harness itself is outside this task's authorization — it is BUILD-ONLY and
> "must NOT be run against CarbonTally until … explicitly authorized").
> Only `react-scripts test` (Jest/jsdom) is available.

Consequently the **interactive** journeys (typing into the login form, navigating
workspaces, observing suspension in the UI) were **not** automated. This is not a
downgrade of B4/B5: those were exercised with the *exact mechanism the browser uses*
— a real GoTrue password grant followed by real authenticated HTTP — and the SPA is
proven to render and to point at the same stack. The remaining, genuinely
browser-only question (visual/interaction acceptance of `/ops`) stays with the
independent verifier, who may run the sanctioned QA harness once authorized.

## 10. Regression results

| Run | Result |
| --- | --- |
| **Canonical FINAL-02 pytest set** (7 files, the exact set named by the FINAL-02 matrix §4.1) | **314 passed · 0 failed · 0 skipped — EXIT=0** |
| Full backend unit suite (`pytest tests/unit`) | **4,621 collected → 4,605 passed · 8 skipped · 8 failed — EXIT=1** (all 8 pre-existing, classified in §10.2) |
| Frontend Jest (`react-scripts test`, CRA) | **46 suites: 44 passed / 2 failed · 521 tests: 520 passed / 1 failed — EXIT=1** (both pre-existing, §10.3) |

### 10.1 The canonical FINAL-02 acceptance set is green

`314 passed, 0 failed, 0 skipped, EXIT=0` — the 7 files are exactly the set the
FINAL-02 matrix names in §4.1: F-05-R1 organisation-scope authorization, D-7
organisation-lifecycle decisions, D-7 F1/F2/F3 enforcement, Storage Management
Step 1, Storage Management Step 2, G1/G2 emissions-query scope and staff access, and
the FINAL-02 email provider. **No failure, no error and no skip**: every
acceptance-scope behaviour this rehearsal exercised is still green on the current
working tree, and the rehearsal's database work (F-A/F-B/F-C repairs) changed no test
outcome — the repairs were applied to the **database clone**, not to the repository.

### 10.2 The 8 full-suite failures are the documented pre-existing set (not FINAL-02)

Measured in this rehearsal:

| # | Test | Cause (measured) | Classification |
| --- | --- | --- | --- |
| 1 | `api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` | `assert True is False` on `body["verification_delivered"]` — the pre-existing uncommitted discovery work reports delivery as configured. **Reproduces identically under a stripped environment** (`env -i PATH=… HOME=…`), so it is *not* induced by this rehearsal's environment. | **PRE-EXISTING** — already recorded by the Storage Management Step 1 and Step 2 reports |
| 2 | `data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | `assert 94 == 71` — stale migration-count pin | **PRE-EXISTING** (stale pin) |
| 3 | `data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | expects a short exact list of migrations after I1; later P8/CT migrations exist | **PRE-EXISTING** (stale pin) |
| 4 | `data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | expects `20261007000000_…` last; later migrations exist | **PRE-EXISTING** (stale pin) |
| 5 | `data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | `unexpected migration after the P16 baseline: 20261025000000_ct_step2_documents_bucket_size_alignment.sql` | **PRE-EXISTING** (stale pin) |
| 6–8 | `engines/test_extraction_suggestions.py::{test_suggest_parses_clean_invoice, test_suggest_missing_fields_leave_unresolved, test_suggest_no_fabrication_on_garbage}` | extraction-engine drift: `'2026-01-15' == '15/01/2026'`, and an extra `extraction_evidence` key on the empty-result paths | **PRE-EXISTING** (engine output drift) |
| — | any FINAL-02 / D-7 / storage-step / org-scope / email-provider test | — | **none** |

This measured set is **byte-for-byte the set already recorded as pre-existing** by
`CARBONTALLY_STORAGE_MANAGEMENT_STEP2_IMPLEMENTATION_20260930.md` §15 ("8 failures,
all pre-existing and unrelated"), which additionally proves the migration-hygiene
group stays red **with the Step 2 migration temporarily moved aside**. The FINAL-02
independent-verification report recorded **7** of them at its own revision (its sweep
`7 failed, 4 398 passed, 8 skipped`, A/B-proved against a pristine `cabdca8`
worktree); the additional one here is the discovery-API failure that the Storage
Management reports record. **Both are outside FINAL-02 scope, and the delta is not
attributable to this task — this rehearsal modified no tracked repository file at all
(§12), so it can neither have introduced nor repaired any test outcome.**

### 10.3 The 2 frontend Jest failures are pre-existing

`react-scripts test` (CRA, jsdom) on the current working tree:

```text
Test Suites: 2 failed, 44 passed, 46 total
Tests:       1 failed, 520 passed, 521 total
Time:        23.884 s
EXIT=1
```

| Failing suite | Symptom | Classification |
| --- | --- | --- |
| `src/App.test.js` | `Cannot find module 'react-router/dom'` — dependency-resolution defect | **PRE-EXISTING** — recorded as failing identically on the pristine `4887c66` tree |
| `src/v3/__tests__/dr007-investor-display-fixes.test.jsx` | assertion drift, `"Mapped activity"` vs `"Natural gas"` | **PRE-EXISTING** — same baseline comparison |

The suite has grown from `39 suites / 430 tests` (FINAL-02 verification revision) to
`46 suites / 521 tests` (current working tree, additive pre-existing work), and the
**same one failed test in the same two failed suites** is the whole failure shape —
i.e. no new frontend failure appears in this change set either. Consistently with §6,
no frontend test asserts on credentials, and none was skipped, deleted or modified.

## 11. Demo-data classification (authoritative clarification applied)

* **The 7,049 emission factors are the authoritative data set.** Nothing in this
  rehearsal touched a factor row (7,049 before and after).
* **Everything else** in `ct_final02_src` — organisations, users, documents, reports,
  calculations, evidence, consultant/client records — is **demo/test data**, as
  clarified by the product owner. It is **not** used as evidence of production
  readiness anywhere in this report, and no demo organisation is treated as a real
  customer.
* Writes performed during the rehearsal, **all inside the disposable database**:

| Write | Scope | Net state |
| --- | --- | --- |
| Org A suspended, then reactivated via the product's admin handler | `organizations.is_active` + the handler's own audited status | **restored**: `is_active = true`, verified |
| One storage object created by the "org B upload into its own path" allow-probe | `documents` bucket, org B tenant folder | 685 → **686** objects |
| GoTrue sessions/refresh tokens from the sign-ins | `auth.sessions` (rehearsal DB only) | expected auth activity |
| Audit entries from the two admin status calls | the product's own audit trail | expected product behaviour |

* **No production demo data was deleted or cleaned** — production demo-data cleanup
  belongs to FINAL-03 and was not performed.

## 12. Files changed, exact commands, repository state

**Repository files changed by this task: exactly one — this report.**
`docs/architecture/CT-FINAL-02-20261001-LOCAL-REHEARSAL-REPORT.md`

**Local disposable rehearsal environment (outside the repository, never committed):**

```text
/home/shomonrobie/ct_local_env/final02_rehearsal/
  nginx.conf                          gateway config (request-time upstream resolution)
  stack_up.sh / stack_down.sh         bring-up / teardown (only ct_final02_* objects)
  prepare_platform_grants.py          F-A repair (785 GRANTs; --check-only, --revoke)
  prepare_platform_ownership.py       F-B repair (166 owners; --check-only)
  login_probe.py                      real password-grant probe (9/9)
  route_probe.py                      org-scope route discovery (evidence for route choice)
  matrix_b5.py                        B5 matrix -> logs/b5_matrix.json
  matrix_b4_d7.py                     B4/D-7 matrix -> logs/b4_d7_matrix.json
  storage.env / rest.env / auth.env   retargeted service environments (mode 600)
  backend.env                         app environment -> rehearsal stack (mode 600)
  logs/                               matrices + backend/frontend logs
```

**Exact commands (canonical order):**

```bash
# 1. build the disposable rehearsal stack over the EXISTING database
bash /home/shomonrobie/ct_local_env/final02_rehearsal/stack_up.sh
python3 .../final02_rehearsal/prepare_platform_grants.py        # F-A (idempotent)
python3 .../final02_rehearsal/prepare_platform_ownership.py     # F-B (idempotent)
docker restart ct_final02_auth ct_final02_storage               # pick up F-A / F-B
cd /home/shomonrobie/ct_93d5cdd && docker exec -i supabase_db_carbon_ledger psql \
    -U postgres -d ct_final02_src -v ON_ERROR_STOP=1 -f - \
    < e2e/environment/scripts/grant_service_role.sql            # F-C (repo script, verbatim)
cd /home/shomonrobie/ct_93d5cdd && docker exec -i supabase_db_carbon_ledger psql \
    -U postgres -d ct_final02_src -v ON_ERROR_STOP=1 -f - \
    < e2e/environment/scripts/grant_authenticated.sql           # F-C (repo script, verbatim)

# 2. application + browser surface against the same database
cd /home/shomonrobie/ct_93d5cdd/backend && .venv/bin/python -m uvicorn main:app \
    --host 127.0.0.1 --port 8090 --env-file .../final02_rehearsal/backend.env
cd /home/shomonrobie/ct_93d5cdd/frontend && REACT_APP_SUPABASE_URL=http://127.0.0.1:54440 \
    REACT_APP_API_URL=http://127.0.0.1:8090 PORT=3100 BROWSER=none npx react-scripts start

# 3. the two authenticated matrices (real password grants; no fakes)
cd /home/shomonrobie/ct_93d5cdd && backend/.venv/bin/python \
    /home/shomonrobie/ct_local_env/final02_rehearsal/matrix_b5.py      # 29/29
cd /home/shomonrobie/ct_93d5cdd && backend/.venv/bin/python \
    /home/shomonrobie/ct_local_env/final02_rehearsal/matrix_b4_d7.py   # 35/35

# 4. regression (canonical FINAL-02 set, per the matrix §4.1)
cd /home/shomonrobie/ct_93d5cdd/backend && .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/unit/api/test_f05_r1_org_scope_authorization.py \
  tests/unit/api/test_d7_org_lifecycle_decisions.py \
  tests/unit/api/test_d7_f1_f2_f3_enforcement.py \
  tests/unit/api/test_storage_management_step1.py \
  tests/unit/api/test_storage_management_step2.py \
  tests/unit/api/test_g1_g2_emissions_query_scope_and_staff_access.py \
  tests/unit/api/test_ct_final_02_email_provider.py

# 5. teardown (rehearsal containers only; the database is never dropped)
bash /home/shomonrobie/ct_local_env/final02_rehearsal/stack_down.sh --purge
```

# 6. completion re-verification (§16.1) — read-only, changes no state
python3 /home/shomonrobie/ct_local_env/final02_rehearsal/login_probe.py   # 9/9 grants
docker exec supabase_db_carbon_ledger psql -U postgres -d ct_final02_src -tA -F'|' -c "
  select 'tables',count(*)::text from pg_class c join pg_namespace n on n.oid=c.relnamespace
    where c.relkind='r' and n.nspname='public'
  union all select 'rls_tables',count(*)::text from pg_class c join pg_namespace n
    on n.oid=c.relnamespace where c.relrowsecurity and n.nspname='public'
  union all select 'policies',count(*)::text from pg_policies where schemaname='public'
  union all select 'factors',count(*)::text from public.emission_factors
  union all select 'auth_users',count(*)::text from auth.users
  union all select 'orgs',count(*)::text from public.organizations
  union all select 'storage_objects',count(*)::text from storage.objects"
  # -> 149 / 149 / 271 / 7049 / 1206 / 975 / 686
git -C /home/shomonrobie/ct_93d5cdd status --short | wc -l                # -> 131
```

**Repository identity at completion:** branch `p8-release-reconciled`,
HEAD `cabdca8380415e73a25cf23eb393d0b15c0af391`.

`git status --short` = **131** entries = the **130 pre-existing** entries recorded at
the start of the rehearsal **+ exactly one new entry attributable to this task — this
report, untracked (`??`)**. Composition: 41 pre-existing modified tracked files
(**0** of them modified by this task) and 90 untracked paths (89 pre-existing).
**No tracked file was modified, and nothing was reset, checked out, cleaned, stashed,
committed or pushed.**

## 13. Production confirmation

The production project was **not contacted** during this rehearsal (the gateway, the
app and every probe point at `127.0.0.1` only). Explicitly:

* no production mutation, no production migration, no schema/RLS/bucket/setting change;
* no production provisioning (no live user, organisation, identity or credential);
* no production email and no SMTP send of any kind;
* no backend/frontend deployment; no production secret read or changed;
* no FINAL-03 work, no demo-data cleanup, and no re-opening of any closed decision.

## 14. Blocker re-status (B1–B6) after this rehearsal

| # | Blocker | Status after this rehearsal |
| --- | --- | --- |
| **B1** | external A2Hosting SMTP delivery | **UNCHANGED / NOT CLOSABLE LOCALLY.** Requires the deployment credential; the existing controlled-delivery evidence (IV report §5.2) stands. Retained finding: the canonical Python provider cannot express implicit TLS on port 465 (live-evidence pass F.3). |
| **B2** | live/shared Supabase credentials | **CLOSED as a premise** by the live-evidence pass (live reachable read-only; the "unavailable" premise was stale). Managed backup/PITR evidence remains an owner decision. |
| **B3** | `/ops` browser QA | **PARTIALLY ADDRESSED — see §9.** A coherent local stack now exists; the SPA compiles, serves and renders against it, and authenticated journeys were proven at the API level with the browser's own mechanism. **Scripted** interaction is not automatable here (no Playwright/Puppeteer/Cypress), so the interactive/visual portion stays with the independent verifier (the QA harness is authorization-gated). |
| **B4** | D-7 inactive-organisation **live/RLS/PostgREST** proof | **CLOSED (live-equivalent):** 35/35 checks with real JWTs, no fakes (§8). The implementation facet was already independently verified. |
| **B5** | Storage/JWT isolation matrix | **CLOSED (live-equivalent):** 29/29 checks through the real PostgREST/Storage path — read filtering, hard 403 on cross-tenant write, signed-URL issuance and cross-tenant object access (§7). |
| **B6** | local rehearsal stack 33 canonical tables behind | **RESOLVED for the rehearsal** (it ran on the head-complete `ct_final02_src`). Whether to bring the *developer* local stack forward remains an owner decision and is not part of FINAL-02. |

Remaining engineering findings deliberately **not** fixed here (reported as required):
the storage-bucket migration guard's table-existence-only NO-OP check, the missing
implicit-TLS/465 capability in the email provider, and the local dev-stack
incoherence (bypassed for the rehearsal only — `backend/.env` and
`frontend/.env.local` were left untouched).

## 15. Limitations and what is deliberately **not** claimed

1. **"Live-equivalent" is not "live".** The real PostgREST v14.5, GoTrue v2.195.0 and
   storage-api v1.69.0 were exercised, but over **loopback**, against a **clone** of
   the existing database, not the hosted project: no managed TLS termination,
   connection pooler, edge/CDN behaviour, hosted log drain or managed backup is
   exercised. Nothing here should be read as hosted-infrastructure acceptance.
2. **Browser interaction is not claimed** (§9): the SPA compiles, serves, renders and
   points at the rehearsal stack, but no scripted login/navigation journey ran,
   because no browser driver exists in this environment and running the QA harness
   requires explicit authorization.
3. **No acceptance is self-declared.** This is an implementer-authored rehearsal report.
   It provides evidence; it does **not** accept FINAL-02. Independent verification of
   its claims remains required.
4. **Not claimed:** external SMTP delivery (B1), managed backup/PITR evidence, a
   malware-scan vendor integration, physical destruction of rejected/expired objects,
   performance/scale characteristics, and production deployment readiness.
5. **Clone-fidelity findings are carried forward as runbook requirements.** F-A/F-B/F-C
   establish that a bare clone **loses** platform-schema ACLs, platform object
   ownership and `public` privileges; the real deployment/restore runbook must apply
   the equivalent grants and ownership (F-C is already covered by the repository's own
   `e2e/environment/scripts/grant_*.sql`). No repository file was changed for this; the
   repair scripts live in the local rehearsal directory.
6. **Environment sensitivity of one pre-existing failure was checked, not assumed**
   (§10.2 item 1, `env -i` re-run).
7. **One object was written** into the disposable database's own tenant path by the
   allow-path probe (§7 note b, §11); it is disclosed rather than hidden, and no
   cleanup of it or of any other demo data was performed (FINAL-03 owns cleanup).

## 16. Evidence summary (all results as measured)

| # | Evidence | Result |
| --- | --- | --- |
| 1 | Existing database retained; no new database created; no production contact | **PASS** |
| 2 | Database facts unchanged: 149 tables / 149 RLS / 271 policies / 7,049 factors / 1,206 users / 975 organisations; `documents` bucket private, 10 MiB cap | **PASS** |
| 3 | F-A platform-schema ACLs restored (785 GRANTs; 0 source ACLs missing) | **PASS** |
| 4 | F-B platform object ownership restored (166/166 `ALTER … OWNER TO`) | **PASS** |
| 5 | F-C `public` privileges via the repo's own scripts (service_role 149/149; authenticated 95/149; anon 0/149) with **RLS unchanged** (271 policies / 149 RLS tables) | **PASS** |
| 6 | Real GoTrue password grants for pre-existing demo identities (9/9 sign-ins) | **PASS** |
| 7 | **B5 JWT/PostgREST/Storage isolation matrix — 29/29** (read filtering, hard 403 cross-tenant write, signed URLs, cross-tenant + anonymous denial, service-role allow) | **PASS** |
| 8 | **B4 D-7 live-equivalent matrix — 35/35** (suspend via the product's admin handler; 403 for owner/admin/member/viewer; single non-disclosing message; tenant-scoped; staff unaffected; audited; reactivation restores access) | **PASS** |
| 9 | Canonical FINAL-02 pytest set — 314 passed / 0 failed / 0 skipped, EXIT=0 | **PASS** |
| 10 | Full backend unit suite — 4,621 collected, 4,605 passed, 8 skipped, **8 failed = the documented pre-existing set**, 0 attributable to this change set or to FINAL-02 scope | **PASS (no new failures)** |
| 11 | Frontend Jest — 44/46 suites, 520/521 tests; the 2 failing suites are the documented pre-existing ones | **PASS (no new failures)** |
| 12 | SPA served (HTTP 200), renders in real headless Chrome (1.29 MB DOM, 150 form elements) and is wired to the rehearsal gateway (54440 ×3) | **PASS** |
| 13 | Scripted/interactive browser journeys | **NOT VERIFIED** (no driver available — §9) |
| 14 | Production mutation / migration / provisioning / email / deployment | **NONE — PASS** |
| 15 | Repository change attributable to this task | **exactly 1 new untracked file (this report); 0 tracked files modified** |

### 16.1 Re-verification at completion (fresh, read-only, no cached log)

Immediately before this report was finalised, every headline figure was re-read live
from the rehearsal environment rather than re-quoted from an earlier log:

| Re-check | How | Result |
| --- | --- | --- |
| Database facts | SQL against `ct_final02_src` | tables **149**, RLS tables **149**, policies **271**, factors **7,049**, auth users **1,206**, organisations **975** — unchanged |
| Storage objects | `storage.objects` count | **686** = 685 pre-rehearsal + the **1** disclosed probe object |
| `documents` bucket | `storage.buckets` | `public = false`, `file_size_limit = 10,485,760` (**10 MiB**) |
| Org A lifecycle state | `organizations.is_active` for org A | **`true`** (restored after suspension) |
| `public` privileges | `information_schema.table_privileges` grouped by grantee | `service_role` **149**, `authenticated` **95**, `postgres` (owner) 149, `anon` **0** |
| Real password grants | `login_probe.py` re-run | **9/9 succeeded** — every identity `200 role=authenticated aud=authenticated` |
| Repository delta | `git status --short`, `git rev-parse` | **131** entries = 130 pre-existing + this report; HEAD `cabdca8…`, branch `p8-release-reconciled` |

The matrices themselves were also re-confirmed from their stored JSON
(`logs/b5_matrix.json` = `total 29 / passed 29 / failed 0`;
`logs/b4_d7_matrix.json` = `total 35 / passed 35 / failed 0`).

## 17. Governance confirmation and status

Confirmed by this rehearsal:

* **No production mutation, migration, schema/RLS/bucket/setting change, provisioning,
  email send or deployment was performed**, and the production project was not
  contacted (§13).
* **FINAL-03 work was not started**: no demo-data cleanup, no deletion of production
  demo data.
* **No closed decision was reopened**, no frozen/published artifact was edited, and no
  acceptance, verification or remediation report was modified.
* **No secret was written into any artifact**: this report records role names, counts
  and status codes only; credentials were resolved through the repository's own local
  credential mechanism and were never printed.
* **The disposable database is retained** (not dropped, not re-cloned) and has been
  returned to its pre-rehearsal observable state (org A active), with the single
  disclosed extra storage object.
* **Prepared by Cline** (implementer) — evidence generation only, **no self-acceptance**.
  Acceptance of FINAL-02 remains with the independent verifier.

> ## Status: **FINAL-02 REHEARSAL COMPLETE — READY FOR INDEPENDENT ACCEPTANCE**
>
> Every blocker evidence gap that is closable in a local, disposable,
> production-untouched manner is closed (B4 and B5 live-equivalent; B6 for the
> rehearsal; B2 premise), the acceptance-scope regression set is fully green, and the
> remaining local limitations (B1 external SMTP, scripted browser interaction, hosted
> infrastructure) are stated explicitly with their exact reasons rather than worked
> around.

### 17.1 Suggested next actions for the independent verifier

1. Re-run the two matrices (`matrix_b5.py`, `matrix_b4_d7.py`) from the local rehearsal
   directory and diff the JSON against §7/§8.
2. Re-run the canonical FINAL-02 pytest set and confirm `314 passed / EXIT=0`.
3. If browser acceptance of `/ops` is required, run the **sanctioned QA harness** under
   explicit authorization — the SPA is already proven to compile, serve, render and
   point at this stack.
4. Treat §10.2/§10.3 as the frozen pre-existing failure baseline when assessing
   no-regression claims.
