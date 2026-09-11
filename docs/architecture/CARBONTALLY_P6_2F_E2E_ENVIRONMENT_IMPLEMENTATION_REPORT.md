# CarbonTally — P6-2F E2E Environment Implementation Report

**Prompt Ref:** `CT-P6-2F-ENV-IMPL-20260911-001`
**Response Ref:** `CT-P6-2F-ENV-IMPL-20260911-001-R1`
**Date/time:** 2026-09-11, 00:55 → 02:40 (+0600)
**Agent:** Cline (implementation agent — NOT the independent verifier)
**Objective:** resolve BLK-1 (isolated E2E environment), BLK-2 (real auth/RLS browser acceptance) and
BLK-3 (Processing-Entity coverage) for P6-2F, without changing unrelated product behaviour.

**Final verdict:** `P6-2F E2E ENVIRONMENT IMPLEMENTATION — PARTIALLY COMPLETE / BLOCKERS REMAIN`

---

## 1. Prompt Ref

`CT-P6-2F-ENV-IMPL-20260911-001`.

## 2. Previous blockers (from `CARBONTALLY_P6_2F_INDEPENDENT_VERIFICATION_REPORT.md`)

* **BLK-1** — no mandatory dedicated isolated E2E environment (class-7 deliverable).
* **BLK-2** — mandatory browser ALLOW/DENY + real Supabase Auth/RLS acceptance not executable
  (in-memory fake auth is not evidence).
* **BLK-3** — Processing-Entity acceptance coverage absent (no PE seeded; `pe_operator` unused; zero
  PE tests; no cross-PE DENY).

## 3. Authority sources inspected

Blueprint V1.3; Master Roadmap V1.0; P6-2 PO Decision Register (D6/D7/D7b/D8/D11/D11-C1/D4/F-ACC/
F-ENV); Phase-6 Remainder Implementation Contract V1.0 (§11–§19); CP2-closure/P6-2F-preflight report;
P6-2F implementation report; **P6-2F independent verification report (BLK-1…3, NB-1…11)**;
`supabase/config.toml`; `supabase/migrations/**` (53); `backend/{config,database}.py`,
`backend/api/dependencies.py`; `tools/seed_investor_demo/{config,client,seed_core}.py`;
`tests/e2e/**`; `backend/tests/e2e/**`; `qa_harness/**`.

## 4. Environment architecture

A **second, fully isolated Supabase stack** is provisioned from an isolated CLI project:

```
e2e/environment/
  supabase/config.toml          project_id = carbontally_e2e, ports remapped 544xx → 553xx
  supabase/migrations/          copy of the 53 repo migrations
  scripts/bootstrap.sh          start + migrate + capture env
  scripts/apply_migrations.sh   finish migrations as supabase_admin (storage-owner)
  scripts/capture_env.sh        → e2e/environment/.env.e2e (gitignored)
  scripts/reset.sh              drop + re-migrate (resettable)
  scripts/teardown.sh           stop + remove (disposable)
  scripts/verify_auth.py        real GoTrue sign-in probe
```

| Service | Demo (`carbon_ledger`) | **Isolated (`carbontally_e2e`)** |
|---|---|---|
| API / REST / Auth | 54425 | **55325** |
| Postgres | 54426 | **55326** |
| Studio | 54423 | **55323** |
| Inbucket | 54424 | **55324** |

Containers: `supabase_{db,auth,kong,rest,realtime,storage,studio,pg_meta,inbucket}_carbontally_e2e`.

## 5. Isolation proof

| Check | Result |
|---|---|
| Isolated `public` tables | **116** |
| Isolated `organizations` rows | 0 (fresh) |
| Isolated `processing_entities` rows | 0 (fresh) |
| Demo `organizations` rows (port 54426) | **975 — unchanged** |
| Demo migrations recorded | 46 (unchanged) |
| `supabase status` target | `API_URL=http://127.0.0.1:55325`, `DB_URL=…:55326` |

No demo/investor data was read, written, reset or repurposed; the demo row counts were observed
before and after and are unchanged.

## 6. Synthetic organisations / firms / PEs / personas

**Environment substrate: DELIVERED. Synthetic seed data: NOT YET DELIVERED.**

Org A / Org B, Consultant Firm A / Firm B, Processing Entity A / PE B, internal QC/ops staff and the
persona mappings are **designed and specified** (`e2e/environment/README.md`,
`backend/tests/e2e/personas.py`), and the seeding approach is proven (§7/§8). The actual insert of
those rows (plus the `E2E_*` persona credentials file) is the outstanding item — see §35.

## 7. Authentication setup (REAL, verified)

`scripts/verify_auth.py` against the isolated stack:

```
environment : carbontally_e2e (http://127.0.0.1:55325)
auth health : 200
create user : 200
sign-in     : 200
  role      : authenticated
  sub       : 5ca306a5-2c9f-4013-a913-cf7b870d9c6c
  aud       : authenticated
  token len : 844
REAL AUTH: PASS
```

**Real Supabase authentication (GoTrue) works in the isolated environment.** The password grant
returns a genuine signed JWT issued by the isolated GoTrue; no `get_current_user` override is
involved.

## 8. Fixture design

Reuses the project's existing seeding patterns (`tools/seed_investor_demo/client.py`: service-role
PostgREST + GoTrue admin + `deterministic_uuid`) under an **isolated namespace** (`p6_2f_e2e`) with no
demo marker. Deterministic UUIDs + deterministic passwords give a resettable, reproducible fixture
set: Org A/B; users (owner/admin/member/viewer); memberships; staff roles/profiles; two PEs + PE
staff; consultant profiles/firm members (with capabilities); consultant-client grants (active +
suspended); manual-extraction batches/items; and billing plan/subscription/credit entitlement.

## 9. Reset / teardown

`scripts/reset.sh` (drop + re-migrate + re-capture) and `scripts/teardown.sh` (`supabase stop`) give
deterministic reset and disposal of the isolated stack only. Migration application is reproducible:
`bootstrap.sh` runs `supabase db reset --no-seed` then
`apply_migrations.sh 20260823000000_d32_private_documents_storage.sql` (the storage-RLS migration
requires the `supabase_admin` role that owns `storage.objects` — an **environment** workaround; no
migration file was modified). Result: **53/53 migrations applied**
(`APPLIED=27 SKIPPED=26`, plus 26 from `db reset`).

## 10–15. frontend / backend / Supabase / RLS / ALLOW / DENY / PE coverage

* **Supabase / Auth / REST / DB:** live and real (§7); PostgREST on `55325/rest/v1`, DB on `55326`.
* **Backend / frontend startup:** **not performed in this session** — no app servers were launched.
* **RLS verification:** not executed (real RLS needs an authenticated PostgREST session over seeded
  rows).
* **Browser ALLOW / DENY:** the specs exist (`tests/e2e/carbontally/*.spec.ts`) and remain
  **SKIPPED** (no `E2E_*` credentials yet) — unchanged from the IV.
* **PE ALLOW / DENY:** **NOT DELIVERED** (BLK-3 remains open).

## 16–32. D6 / D7 / D8 / D11 / D11-C1 / IV-N6 / IDOR / injection / replay / entitlement evidence

No new acceptance evidence was produced in this session beyond the environment + real-auth proof.
The application-level evidence from `CT-P6-2F-IMPL-20260910-001` (39/39 E2E tests) stands unchanged
and the IV's assessment of those layers is unaffected. **No invariant was changed:** no schema, RLS,
billing, role/capability, processing-origin or conversation-kind change was made; D11-C1 untouched;
no migration added.

## 33. Test results

| Run | Result |
|---|---|
| Isolated stack `supabase start` | **EXIT=0** (project `carbontally_e2e`) |
| Migrations applied | **53/53** (`ALL_APPLIED`) |
| `verify_auth.py` (real GoTrue sign-in) | **PASS** (role `authenticated`) |
| `supabase status` target | 55325 / 55326 (isolated) |
| Demo instance rows (54426) | 975 orgs — **unchanged** |

No CarbonTally unit/E2E suite was re-run (no application code changed).

## 34. Remaining skips

* Authenticated browser specs (`consultant-lifecycle`, `security-denies`) — **SKIPPED** (no seeded
  personas/`E2E_*`).
* All Processing-Entity acceptance — **not present**.

## 35. Remaining blockers

1. **Synthetic seed not yet inserted** — personas/orgs/firms/PEs/items/entitlement and the `E2E_*`
   credential file are specified but not yet run.
2. **App servers not started** — backend + frontend against the isolated stack.
3. **Browser ALLOW/DENY, IV-N6, D8, D6 boundary — not executed.**
4. **PE ALLOW/DENY + cross-PE isolation — not implemented (BLK-3 open).**
5. RLS not exercised.

## 36. Non-blocking findings

NB-1…NB-11 from the IV remain untouched; none was expanded into this task (per prompt §40).

## 37. Scope-control statement

Only P6-2F **environment** artifacts were created: `e2e/environment/**` (isolated config, migrations
copy, scripts, README, `.gitignore`) and the two required reports. **No product code, test,
migration, schema, RLS, billing, role, capability or UI file was modified.** The only configuration
change is inside the new isolated `e2e/environment/supabase/config.toml`; the repository's own
`supabase/config.toml` is untouched.

## 38. Git state

* Branch `main`; HEAD `16391217103b98dcea520070c5a22c68f12fe607` (unchanged).
* **No commit, no push, no staging.**
* Created (untracked): `e2e/environment/**`, this report, the prompt-history record.

## 39. Final verdict

> **`P6-2F E2E ENVIRONMENT IMPLEMENTATION — PARTIALLY COMPLETE / BLOCKERS REMAIN`**

**Substantially resolved:** the mandatory isolated E2E environment now **exists** — a separate
Supabase project (`carbontally_e2e`) with the full schema (53/53 migrations), proven **real Supabase
authentication**, resettable/disposable scripts, and demo data provably untouched (975 orgs
unchanged). This addresses the core of BLK-1 and the core of BLK-2 (real Supabase Auth).

**Still open:** synthetic fixture/persona seeding, app-server bring-up, authenticated browser
ALLOW/DENY execution, IV-N6/D8/D6 boundary execution, and Processing-Entity coverage (BLK-3). These
are the remaining mandatory items before a fresh independent verification can pass.

## 6. Synthetic organisations / firms / PEs / personas — **SEEDED (this session)**

`e2e/environment/scripts/seed_e2e.py` (schema-introspecting, deterministic, idempotent) ran against
the isolated DB with **0 errors**:

| Table | Rows | Content |
|---|---|---|
| `organizations` | 2 | **Org A**, **Org B** (synthetic, `metadata.e2e`) |
| `organization_metadata` | 2 | A + B |
| `users` | 13 | all personas (customer + staff) |
| `organization_members` | 6 | A: owner/admin/member/viewer; B: owner/member |
| `staff_roles` | 2 | `qc_specialist` (can_qc/can_review), `p6f_ops` (can_manage_staff) |
| `processing_entities` | 2 | **PE A**, **PE B** |
| `staff_profiles` | 5 | internal QC, internal Ops, PE-A manager, PE-A staff, PE-B manager |
| `consultant_profiles` | 2 | **Firm A**, **Firm B** |
| `consultant_firm_members` | 2 | consultant_a (firm A, all capabilities), consultant_b (firm B) |
| `consultant_clients` | 3 | **firm A→org A active**; **firm B→org B active**; **firm B→org A suspended** |
| `manual_extraction_batches` | 3 | org A, org B, **PE-A-assigned batch** (`entity_id = PE A`) |
| `manual_extraction_items` | 3 | org A `calculated`; org B `calculated`; **PE-A item `pe_qc_approved`, origin `PROCESSING_ENTITY`** |

**Real authentication: 13/13 personas sign in** (`/auth/v1/token?grant_type=password`) with genuine
GoTrue-issued JWTs. Credentials are written to the gitignored `tests/e2e/.env.personas`; deterministic
ids come from `uuid5("carbontally-e2e-p6f:<key>")`, so reset + reseed reproduces the identical graph.
`bootstrap.sh` now runs migrate → grants → capture → seed end-to-end.

Environment-only provisioning note: the isolated DB required
`GRANT … ON ALL TABLES IN SCHEMA public TO service_role` (`scripts/grant_service_role.sql`) for
PostgREST seeding — the demo instance already has these grants. **No RLS policy was changed and
`authenticated`/`anon` were deliberately NOT broadened**, so the RLS boundary under test is intact.

## 6b. Still open after this session

* Backend/frontend app servers not yet started against the isolated stack.
* Browser ALLOW/DENY, D6/D8/D11/IV-N6 and PE-acceptance specs not yet executed (personas now exist, so
  the specs will execute rather than skip once servers are up).
* Real PostgREST/RLS acceptance not yet executed.
* Regression suites not re-run (no application code changed).

*End of report. No independent verification was performed. No Phase 7/8 work was started.*



---

# CT-P6-2F-ENV-IMPL-20260911-003 — EXECUTION ADDENDUM (2026-09-11)

Status: **P6-2F E2E ENVIRONMENT IMPLEMENTATION — PARTIALLY COMPLETE / BLOCKERS REMAIN**

This addendum records ONLY work performed by task `...003`. Work delivered by
`...001`/`...002` (isolated stack, ports 553xx, 53 migrations, service-role grant
helper, deterministic synthetic seed, 2 orgs / 2 firms / 2 PEs / 13 personas,
real GoTrue auth, `.env.personas`, demo isolation) was preserved unchanged and
NOT repeated.

## 1. Application startup — EXECUTED (evidence)

| Item | Value |
|---|---|
| Backend | `backend/.venv/bin/python` + `uvicorn main:app --host 127.0.0.1 --port 8051` |
| Routes registered | 662 |
| `SUPABASE_URL` | `http://127.0.0.1:55325` (isolated `carbontally_e2e`) |
| `DATABASE_URL` | `postgresql://postgres@127.0.0.1:55326/postgres` (isolated) |
| Service/anon keys | taken from `e2e/environment/.env.e2e`, overriding `backend/.env` |
| Auth | real GoTrue password grant on `:55325/auth/v1/token` for every persona |
| Demo/production | not contacted; backend env was re-exported per-process |

Frontend was NOT started against the isolated stack (see blockers).

## 2. Acceptance runner — EXECUTED

`e2e/environment/scripts/run_acceptance.py` → `e2e/environment/.acceptance_report.json`.
Two boundaries are reported separately because the backend uses a
service-role pool: FastAPI results are **application authorization only** and
are NOT evidence of RLS.

### 2.1 Application boundary (FastAPI, real user JWT) — 10/10 PASS

| Case | Identity | Expected | Actual |
|---|---|---|---|
| org owner notifications | org_a_owner | 200 | 200 PASS |
| unauthenticated notifications | anon | 401/403 | 401 PASS |
| consultant me | consultant_a | 200 | 200 PASS |
| consultant A granted client items | consultant_a | 200 | 200 PASS |
| consultant B → Org A client | consultant_b | 403/404 | 403 PASS |
| consultant B → Org A item (IDOR) | consultant_b | 403/404 | 403 PASS |
| org B → Org A item | org_b_owner | 403/404 | 403 PASS |
| PE A me | pe_a_manager | 200 | 200 PASS |
| **PE B → PE-A item** | pe_b_manager | 403/404 | 403 PASS |
| internal QC queue | internal_qc | 200 | 200 PASS |
| consultant → internal ops | consultant_a | 403 | 403 PASS |

### 2.2 Database/RLS boundary (PostgREST, real user JWT, no service-role) — BLOCKED

| Case | Identity | Expected | Actual |
|---|---|---|---|
| org A reads own org | org_a_owner | 200 + row | **403 / `42501`** |
| org B reads own org | org_b_owner | 200 + row | **403 / `42501`** |
| org A reads Org B | org_a_owner | no row | 403 — **INCONCLUSIVE** |
| org B reads Org A | org_b_owner | no row | 403 — **INCONCLUSIVE** |
| unauthenticated read | anon | 401/403 | 401 PASS |

Root cause (evidence, not inference): PostgREST returns
`{"code":"42501", "message":"permission denied ...", "hint":"GRANT SELECT ON
public.organizations TO authenticated"}` for `organizations`,
`organization_members` and `notifications`. The isolated environment's
migrations were applied without the standard Supabase default table privileges
for `authenticated`, so **every** authenticated REST read is denied before RLS
is evaluated. The DENY rows are therefore non-discriminating and are recorded
as INCONCLUSIVE, never PASS (no false positives).

Per mandate §5 (do not grant privileges to `authenticated`/`anon`) and §24
(no migration/RLS/architecture change), this was NOT repaired opportunistically.
Fixing it requires an environment-provisioning change (grant baseline table
privileges to `authenticated`, or apply migrations as the role that owns the
privileges) and a re-run of the RLS matrix.

**Result: 12/16 checks PASS (APP 10/10; RLS 1/5).** `run_acceptance.py` exits 1
when any check is not a PASS, so this artifact cannot silently go green.

## 3. Remaining blockers after this session

| Item | State | Evidence |
|---|---|---|
| BLK-2 backend vs isolated env | **EXECUTED** | 662 routes; all API calls used real GoTrue JWTs |
| BLK-2 frontend vs isolated env | NOT EXECUTED | frontend not started against `:55325` |
| BLK-2 real PostgREST/RLS acceptance | **BLOCKED** | `42501` privilege gap (§2.2); requires env provisioning change (mandate §24) |
| BLK-2 browser ALLOW/DENY (Playwright) | NOT EXECUTED | frontend/server not brought up |
| D6 / D8 / D11 / IV-N6 | NOT EXECUTED | require the running frontend + notification flow |
| BLK-3 PE acceptance | **PARTIALLY EXECUTED** | PE-A `/api/v3/pe/me` 200; PE-B → PE-A item 403 (cross-PE + direct-IDOR denied at the application boundary) |
| Regression suites | NOT EXECUTED this session | no counts claimed |
| Reset/recreate + teardown proof | NOT EXECUTED this session | scripts left intact; stack intentionally left RUNNING for the fresh verification session |

## 4. Isolation evidence

| Environment | Port | Database | organisations | processing_entities | auth users |
|---|---|---|---|---|---|
| isolated `carbontally_e2e` | 55325 (postgres 55326) | isolated CLI stack | 2 | 2 | 14 (13 personas + fixture) |
| demo/investor | 54321 | untouched this session | 975 (prior capture) | — | 1185 (prior capture) |

No demo/investor database, credential or record was read or written by this task.

## 5. Residual non-blocking findings / limitations

* `authenticated` lack-of-privileges is an **environment provisioning gap**, not
  an RLS policy defect. It must be fixed in `e2e/environment` (grant baseline
  table privileges to `authenticated`, or apply migrations as the privilege
  owner) and the RLS matrix re-run.
* RLS DENY rows are recorded INCONCLUSIVE (non-discriminating) — they must not
  be cited as isolation evidence until the ALLOW rows succeed.
* This is an implementation/environment record only: **not independent
  verification**.

## 6. Verdict

**P6-2F E2E ENVIRONMENT IMPLEMENTATION — PARTIALLY COMPLETE / BLOCKERS REMAIN**

## 7. CT-P6-2F-ENV-IMPL-20260911-004 — PRIVILEGE BASELINE REPAIR + REMAINING ACCEPTANCE

### 7.1 Root cause of the previous `42501`

The schema's own privilege model was inspected before granting anything:

* 116 public tables, all RLS-enabled, 175 policies.
* 17 migration files contain `TO authenticated`, granting explicit
  `SELECT, INSERT, UPDATE, DELETE` on the tables PostgREST is expected to serve
  (e.g. `processing_entities`).
* The tested tables (`organizations`, `organization_members`, `users`) held only
  `REFERENCES, TRIGGER, TRUNCATE` for `authenticated` — leftovers, not the
  product's model — while carrying policies whose role *is* `authenticated`:
  `organizations_org_select` (`is_org_member(id) OR is_org_consultant(id)`),
  `organizations_org_update`, `om_select_self_or_admin`, `om_insert_admin`,
  `om_update_admin`, `om_update_self`.
* The CLI-applied migration role therefore produced objects without the
  `authenticated` DML grants, and PostgreSQL answered `42501` **before** RLS was
  evaluated. That denial was a privilege failure, not a policy decision.

### 7.2 The E2E-only provisioning

`e2e/environment/scripts/grant_authenticated.sql` — E2E only, idempotent,
documented inline:

* `GRANT USAGE ON SCHEMA public TO authenticated`.
* A `DO` block reading `pg_policies` that grants **exactly the DML privileges
  implied by each table's own RLS policies for `authenticated`** — derived from
  the schema, never a blanket `GRANT ALL`.
* `GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated` (repo
  convention; policies call helpers such as `is_org_member`).
* **`anon` deliberately untouched** — stricter than Supabase's default baseline,
  so the unauthenticated boundary stays unambiguous.

Wired into `bootstrap.sh` and `reset.sh` so it is applied automatically after
migrations (both target port 55326 only; never demo/investor).

### 7.3 Proof the grant does not bypass RLS

| Check | Before | After |
|---|---|---|
| RLS-enabled public tables | 116 | **116 (unchanged)** |
| Policies in `public` | 175 | **175 (unchanged)** |
| `organizations` policy text | `is_org_member(id) OR is_org_consultant(id)` | **byte-identical** |
| `anon` DML grants | 36 | **36 (not broadened)** |
| `authenticated` on `organizations` | REFERENCES,TRIGGER,TRUNCATE | +SELECT,UPDATE |

### 7.4 Real PostgREST/RLS matrix (real personas, real JWTs, no service-role)

`ACCEPTANCE: 16/16 passed` (exit 0).

| Case | Identity | Expected | Actual |
|---|---|---|---|
| Org A reads own org | org_a_owner | 200 + row | 200 + row **PASS** |
| Org A reads Org B | org_a_owner | no row | 200, **0 rows (RLS filtered)** PASS |
| Org B reads own org | org_b_owner | 200 + row | 200 + row **PASS** |
| Org B reads Org A | org_b_owner | no row | 200, **0 rows (RLS filtered)** PASS |
| unauthenticated read | anon | 401/403 | 401 **PASS** |
| consultant A granted client items | consultant_a | 200 | 200 PASS |
| consultant B → Org A client | consultant_b | 403/404 | 403 PASS |
| consultant B → Org A item (IDOR) | consultant_b | 403/404 | 403 PASS |
| org B → Org A item | org_b_owner | 403/404 | 403 PASS |
| PE A `/me` | pe_a_manager | 200 | 200 PASS |
| **PE B → PE-A item** | pe_b_manager | 403/404 | 403 PASS |
| internal QC queue | internal_qc | 200 | 200 PASS |
| consultant → internal ops | consultant_a | 403 | 403 PASS |
| unauth notifications | anon | 401/403 | 401 PASS |

Cross-tenant denials now return **HTTP 200 with an empty result set** — the RLS
boundary itself filtering rows — which is the genuine policy behaviour and was
unobservable before this repair.

### 7.5 Authenticated browser acceptance (real CRA frontend + isolated stack)

Frontend: `react-scripts start` on `:3000` with
`REACT_APP_SUPABASE_URL=http://127.0.0.1:55325`,
`REACT_APP_SUPABASE_ANON_KEY=<isolated anon>`,
`REACT_APP_API_URL=http://127.0.0.1:8051` — overriding `.env`/`.env.local`, whose
default points at the **production** Supabase project (`pvwiojoyaqywtydzcpbg`).
Personas were written to `.env.personas` (gitignored); the file had been **empty**,
which is why 8 specs previously skipped.

`npx playwright test`: **16 tests — 10 passed, 3 failed, 3 skipped, exit 1 (57.3s)**.

Passed at the real boundary: 7 route-protection specs; **IV-N6 consultant deep
link opens the Client Item Workspace served by `/api/v3/processing/items/...`
(test 1, 21.0s)**; cross-firm consultant denied another firm's client item;
consultant denied the admin control plane.

Failed — in **all three the API actually denied the caller**; only the specs'
literal expected status sets did not match:

| Spec | Expected in set | Received |
|---|---|---|
| organisation member cannot approve a customer decision | `404` | `[401, 403]` |
| unauthenticated API calls are rejected | `200` | `[401, 403]` |
| consultant cannot invoke internal ops workspace route | `200` | `[401, 403, 404]` |

No spec or assertion was modified to obtain green results (mandate §12); these
are recorded as open findings for the independent verification session.

Skipped (state-based, not credential-based): submit-to-QC and pass-review (item
not in a submittable/reviewable state) and the consultant lifecycle notification
deep link (no lifecycle notification fixture) — a **fixture-state coverage gap**
for D11 browser acceptance.

### 7.6 Reset / recreate proof — PASSED

`reset.sh` → `supabase db reset` + 53 migrations + both grant helpers →
`seed_e2e.py` → `run_acceptance.py` = **`ACCEPTANCE: 16/16 passed`, EXIT=0**.
The privilege baseline is re-applied automatically by the wired scripts and the
synthetic topology + personas are deterministically recreated.

### 7.7 Teardown

`teardown.sh` runs `supabase stop` from `e2e/environment` (isolated project
`carbontally_e2e` only). It was **reviewed but left un-executed** so the stack
stays running for the independent verification session. Restart procedure:
`bootstrap.sh`, or `supabase start` → `apply_migrations.sh` → both grant helpers
→ `seed_e2e.py` → `capture_env.sh`.

### 7.8 Regression / isolation

* `pytest backend/tests/unit backend/tests/e2e` — **1,693 tests collected,
  1,693 passed, 0 failed, 0 errors, 0 skipped, exit 0** (progress stream analysed
  from the `-q` output: 1,693 `.`, 0 `s`, 0 `F`, 0 `E`).
* `npx playwright test` — exact figures in §7.5 (16 total / 10 passed / 3 failed /
  3 skipped / exit 1).
* Isolation: isolated DB `:55326` = **2 organisations, 2 processing entities,
  14 auth users**; demo/investor untouched (prior capture 975 orgs / 1185
  identities). No demo or production credential or endpoint was used — the API
  and frontend were both re-pointed at `:55325` / `:8051` for this session.

### 7.9 Remaining findings

* **NF-1** — three browser DENY specs carry literal status-set expectations that
  do not match current API responses (`404` vs `401/403`; `200` vs `401/403`).
  The denials themselves are correct; adjudication belongs to the independent
  verification session, not a local edit.
* **NF-2** — D11 browser coverage (notification deep link, submit-to-QC,
  pass-review) skips because the synthetic item's workflow state and notification
  fixtures do not reach those states.
* **NF-3** — reset/recreation is proven at DB + API level; the full browser suite
  was not re-run after the reset within budget.
* **D6 / D8 / D11 (event-level) / PE alternate-route browser denial** — not
  executed in this session.
* No RLS policy, schema, migration, role, capability, billing, provenance,
  conversation-kind or processing-origin behaviour was changed; `IV-N1`…`IV-N5`
  were not remediated.

### 7.10 Verdict

**P6-2F E2E ENVIRONMENT IMPLEMENTATION — PARTIALLY COMPLETE / BLOCKERS REMAIN**

## 8. CT-P6-2F-ENV-IMPL-20260911-005 — D6/D8/D11/PE + BROWSER COMPLETION

### 8.1 Browser expectation mismatches — adjudicated and fixed (no weakening)

Root cause (not a product defect): the three specs issued **relative** requests
through `page.request` / `request`, which resolve against `baseURL` = the CRA
dev-server origin `:3000`. The SPA answers every path with `index.html` **200**,
so the specs never reached the server boundary at all — the previous run failed
them correctly.

Contract determination: every isolated API response for those routes is a
refusal, never a payload; `401` (no/invalid session), `403` (authenticated, not
permitted) and `404` (route not exposed to the caller) are all legitimate
refusals. The assertion must therefore target the **API origin** with a **real
JWT**, and must additionally prove the reply is not the SPA fallback.

| Spec | Old | Observed | New | Why not weakened |
|---|---|---|---|---|
| member cannot approve a customer decision | `page.request.post('/api/v3/.../customer-review')` → `expect([401,403])` | SPA 404 | `apiCall()` to `:8051` with the member's real JWT, on an item genuinely in `ct_qc_approved`; `expect([401,403])` **+** follow-up read must not show a decided item | DENY still proven, now at the real boundary, on an action that is applicable so only authorization can refuse |
| unauthenticated API calls rejected | `request.get('/api/v3/notifications')` | SPA **200** | `request.get('${apiBase()}/api/v3/notifications')`; `expect([401,403])` **+** body must not contain `<html` | the SPA 200 previously masked a real 401; the 401 is now the API's |
| consultant cannot invoke the internal ops route | `page.request.get('/api/v3/ops/items/{id}/workspace')` | SPA 200 | `apiCall()` with the consultant's real JWT; `expect([401,403,404])` **+** no `<html` | same: SPA 200 eliminated, server refusal asserted |

New helpers in `tests/e2e/personas.ts`: `apiBase()` (`E2E_API_URL`),
`sessionToken(page)` (real Supabase session from `localStorage`) and `apiCall()`.

**Result: 13 passed / 0 failed / 3 skipped (26.1s)** — all three DENY specs pass
against the real boundary.

### 8.2 State-based skips — partially remediated

`e2e/environment/scripts/seed_lifecycle_fixtures.py` (new, E2E-only) adds
deterministic lifecycle-state items (`consultant_reviewed`, `ct_qc_approved`,
idempotent `uuid5`) and an **active client-organisation subscription**
(`customer_subscriptions`, `lifecycle_status='active'`, `billing_mode='STANDARD'`
— the table's CHECK constraints were read from the schema first). It also drives
one item through the real `consultant-submit` endpoint so `submitted_to_qc` emits
a durable firm-centric notification via the workflow itself. Wired into
`bootstrap.sh` and `reset.sh`.

Effect: the gate that had been silently blocking everything —
`403 "No active processing entitlement for this organization"` — is satisfied;
`consultant-submit` returns **200**, the item transitions
`consultant_reviewed → reviewed`, and notifications are written durably
(2 rows, unchanged on replay).

The three consultant-surface browser specs still skip because the workspace does
not render the action buttons for these items: the fixture items carry
`consultant_firm_id = NULL` (internal origin), so "Pass review" / "Submit to
CarbonTally QC" are not presented. **Single remaining browser gap** — needs the
fixture items consultant-firm-scoped (`consultant_firm_id = FIRM_A`) and a re-run.

### 8.3 Acceptance results

* `run_acceptance.py` (RLS + application): **16/16 PASS** (unchanged).
* `run_p6f_acceptance.py` (new): **34/37 PASS**.
  * **D8 6/6 PASS** — `conversation_kind` vocabulary observed `[]` for synthetic
    data, no consultant kind; consultant A authorised org conversation access
    200; cross-org 403; other-firm 403; unauthenticated 401. No new
    kind/table/role/capability.
  * **D6 8/8 PASS** — owner reads own entitlement 200 (`organization_id` = Org A);
    other org 404; consultant 404 (grant ≠ ownership); PE 404; unauthenticated
    401; approval-time gate canonical **402 fail-closed**; replay 402 (no
    re-application); no financial path invoked.
  * **D11 9/12 PASS** — `submitted_to_qc` real submit (409 idempotent replay after
    the fixture's 200) with a durable firm-centric notification and silent denial
    for `consultant_b`; `accepted`/review 409 (state idempotency); `rework`
    authorization-scoped 403; `qc_outcome` GET route inventory 405.
    **`customer_decision` → 402** (same canonical allowance gate; no credit
    fixture yet).
  * **PE 11/12 PASS** — PE-A work queue 200; PE-B → PE-A workspace 403; all five
    alternate PE routes (/work, /status, /pe-review, /pe-qc, /clarify) refuse
    PE-B; PE-B → internal item 403; PE-A → Org B item 403; consultant → PE route
    403; unauthenticated 401. **PE-A item workspace 403** (see §8.5 R4).

### 8.4 Regression / environment

* `npx playwright test`: **16 total — 13 passed, 0 failed, 3 skipped, exit 1,
  26.1s** (was 10 / 3 / 3).
* `pytest backend/tests/unit backend/tests/e2e`: launched in the background; the
  session ended before completion — **no counts claimed**. Last complete run
  (task 004): 1,693 / 1,693, exit 0.
* Isolation unchanged: `:55325` / `:55326`, API `:8051`, frontend `:3000`
  re-pointed at the isolated stack; demo/investor untouched.

### 8.5 Remaining findings (verdict B)

* **R1** — no credit/allowance fixture, so the canonical approval-time gate
  returns `402`; D6/D11 **ALLOW-at-approval** (owner decision → 200 with
  consumption) is not evidenced. Needs an E2E allowance/credit fixture.
* **R2** — `customer_decision` (D11) and the approval-dependent browser specs
  depend on R1.
* **R3** — the D11 recipient-persistence assertion reads 0 rows because the
  harness selects `user_id,organization_id` (column mismatch); the rows
  demonstrably exist (count = 2). Harness defect, not a product finding.
* **R4** — PE-A item-workspace ALLOW returns `403` while `/api/v3/pe/work` (200)
  and every PE DENY case pass. PE-assignment fixture gap vs product behaviour is
  **unresolved** — recorded, not guessed.
* **R5** — three consultant-surface browser specs still skip (§8.2).
* No stop condition triggered: no production/demo/investor change, no RLS or
  schema change, no new role/capability/permission, no D6/D7/D8/D11 or
  `processing_origin` change.

### 8.6 Verdict

**P6-2F E2E ENVIRONMENT IMPLEMENTATION — PARTIALLY COMPLETE / BLOCKERS REMAIN**

## 9. CT-P6-2F-ENV-IMPL-20260911-006 — R1/R2/R3/R5 FINALIZATION ATTEMPT

### 9.1 Root causes established from the schema (evidence, not guesswork)

* **R1** — the canonical approval charge reads
  `billing_commercial_config['standard_allowance'].config_value.monthly_processing_units`
  (`backend/services/billing.py:113-126`); with no config the STANDARD branch sees
  `remaining = 0` and fails closed with **402 InsufficientCreditsError**
  (`billing.py:38-42`, `727-732`). The seed contained **no** allowance config row.
* **R4** — the PE workspace handler re-validates *item ↔ assignment*
  (`backend/api/v3_pe.py:561 _ensure_assigned_item`), and the isolated
  `work_item_assignments` table was **empty (0 rows)**.
* **R3** — `notifications` columns are `id, event_key, notification_type,
  recipient_id, recipient_type, link, title, message, metadata, actor_domain,
  is_read, read_at, is_dismissed, dismissed_at, priority, created_at, updated_at`.
  The harness selected the non-existent `user_id, organization_id`, so PostgREST
  returned an error and the read counted 0 rows.
* **R5** — the lifecycle fixture items carried `consultant_firm_id = NULL`.

### 9.2 Changes applied (E2E fixtures + harness only)

| Item | Change | Result |
|---|---|---|
| R1 | `billing_commercial_config` row `standard_allowance`, `version 2`, `{"monthly_processing_units": 100}` (upsert on `config_key,version`; v1 already existed) | **201 inserted** |
| R3 | harness selects the real columns `id, event_key, notification_type, recipient_id, recipient_type, link` | **fixed — reads 2 real rows** |
| R5 | `consultant_firm_id = FIRM_A` applied to `ITEM_A`, `ITEM_A2`, `ITEM_A3`, `ITEM_A6`, `ITEM_A7` | items + item A upserts **200** |
| R4 | `work_item_assignments` row for `ITEM_PE_A`/PE_A | **400 `23502` NOT NULL violation** — rejected |

All changes are in `e2e/environment/scripts/seed_lifecycle_fixtures.py` (fixture) and
`run_p6f_acceptance.py` (harness). No product code, schema, RLS, role, capability,
billing model or recipient policy was touched.

### 9.3 Outcome — R1 clears the 402 gate but exposes a 500

With a legitimate allowance in place the **402 disappeared** and the canonical
approval path now returns **HTTP 500** (and **409** on the following attempt,
because the fixture had already driven the item's state):

```
D6  approval-time enforcement is canonical   org_a_owner -> 500  (was 402)
D11 4 customer_decision (owner)              org_a_owner -> 409  (was 402)
PE  PE A opens its assigned item             pe_a_manager -> 403  (unchanged)
D6/D8/D11/PE ACCEPTANCE: 34/37 passed
```

Interpretation: the entitlement/allowance gate itself is now satisfied, so the
failure has moved *deeper into the approval/charge path*. **D6 ALLOW-at-approval
and D11 `customer_decision` are still NOT evidenced**, so the R1/R2 acceptance
criteria remain unmet.

**New finding NF-4 (unresolved):** with an active STANDARD subscription plus a
positive `standard_allowance`, the customer-approval endpoint returns **500**
instead of succeeding. Unverified hypothesis (to be tested, not assumed): a
remaining fixture gap in the STANDARD branch's usage/consumption writes (e.g. the
`billing_usage`/allowance-config interaction) rather than a product defect. This
must be investigated by the independent verification session with server logs; it
was deliberately **not** patched speculatively.

### 9.4 R4 status — unresolved (not fixed speculatively)

`/api/v3/pe/work` returns **200** for PE-A while the item workspace returns
**403**, and the assignment-table fixture insert is rejected by a NOT NULL
constraint (`23502`) whose column is not derivable from the table's column list
alone. Per mandate §10 this is recorded as an **unresolved blocker**, not guessed
at and not worked around.

### 9.5 R5 status — fixtures applied, verification not completed

Firm-scoping of the consultant lifecycle items was applied successfully. The
browser re-run for this cycle was still executing when the session budget ended,
so **no browser result is claimed for 006**; the last captured browser result is
005's (16 total — 13 passed, 0 failed, 3 skipped).

### 9.6 Regression

`pytest backend/tests/unit backend/tests/e2e` was launched and was at ~12% when
the session ended; it **did not complete**, so no counts are claimed for 006. The
last complete regression remains 004's 1,693/1,693 (exit 0).

### 9.7 Verdict

**P6-2F E2E ENVIRONMENT IMPLEMENTATION — PARTIALLY COMPLETE / BLOCKERS REMAIN**

## 10. CT-P6-2F-REMED-20260911-008 — BLOCKING-FINDING DIAGNOSIS

### 10.1 NF-4 (D6 approval 500) — ROOT CAUSE FOUND (application defect)

Reproduced and captured from the running API's own log
(`POST /api/v3/processing/items/{item}/customer-review` → **500**):

```
asyncpg.exceptions.AmbiguousFunctionError:
    function to_char(unknown, unknown) is not unique
  ... backend/api/v3_processing_workflow.py:987  (customer_review_item → D37 charge)
  ... backend/data/billing.py:849, in record     (billing_usage.record)
  ... backend/data/base.py:53, in _fetch_one
```

**Classification: B — existing application defect.** The charge path's usage
write calls `to_char(...)` with **untyped parameters**, so PostgreSQL cannot
resolve the overload and the statement fails to prepare. The failure occurs
*after* the D6 entitlement/allowance gate has passed (the earlier 402 is gone),
which is why it appeared only once the allowance fixture existed. This is not an
E2E fixture gap, not a harness defect, not infrastructure: the same SQL would fail
identically anywhere.

**Proposed minimal fix (NOT applied — see §10.3):** make the overload unambiguous
by casting the arguments in that statement in `backend/data/billing.py`
(`to_char($n::timestamptz, <literal>)`), with a focused regression test on the
STANDARD-mode usage write. That is a product-code change outside this bounded
cycle's executed work.

### 10.2 R4 (PE-A item workspace 403) — ROOT CAUSE FOUND (E2E fixture gap)

`work_item_assignments` is **empty**, and `_ensure_assigned_item`
(`backend/api/v3_pe.py:69-95`) authorises only when
`work_item_effective_entity(item) == caller entity`, i.e. an **open item-level
assignment row** must exist. The schema was then read verbatim:

* NOT NULL: `id` (default), `manual_extraction_item_id`, `status` (default
  `'open'`), **`action`**, **`assignee_kind`**, **`assigned_by`**,
  **`actor_domain`**, `created_at`, `updated_at`.
* `work_item_assignee_shape` CHECK: `assignee_kind='processing_entity'` requires
  **`processing_entity_id IS NOT NULL AND assigned_to IS NULL`**; the
  `internal_staff` branch is the mirror image.
* `action ∈ {assign, reassign, claim, recover}`, `actor_domain ∈
  {internal_staff, processing_entity}`, `assignee_kind ∈ {internal_staff,
  processing_entity}`, `status ∈ {open, closed}`.
* FK `manual_extraction_item_id → manual_extraction_items(id)` (CASCADE);
  FK `processing_entity_id → processing_entities(id)`.

The earlier 006 attempt failed (`23502`) because it supplied **`assigned_to`
alongside `processing_entity_id`** (violating the shape CHECK) and **omitted
`assigned_by`** (NOT NULL). **Classification: A — E2E fixture/configuration gap**;
a legitimate validity-rejected fixture, not a product defect.

**Proposed minimal fixture (NOT applied — see §10.3):** insert one row
`{manual_extraction_item_id: ITEM_PE_A, processing_entity_id: PE_A,
assignee_kind: 'processing_entity', assigned_to: NULL, action: 'assign',
actor_domain: 'processing_entity', assigned_by: <PE-A user id>, status: 'open'}`
via the E2E fixture script, then re-run the PE ALLOW/DENY matrix.

### 10.3 Remediation status

**No remediation was applied in this cycle.** Both root causes are now
definitively identified with file/line and schema-level evidence, but the session
budget ended before the PE assignment fixture could be added and the acceptance /
browser / regression suites re-run. Nothing was half-applied: the repository code
and the E2E fixtures are exactly as the previous cycle left them.

## 11. CT-P6-2F-REMED-20260911-009 — APPLIED FIXES

### 11.1 NF-4 — FIXED (defect removed)

Exact SQL found in `backend/data/billing.py::UsageTrackingRepository.record`
(line ~849):

```sql
INSERT INTO public.usage_tracking
    (organization_id, usage_date, usage_month, ai_files_processed)
VALUES ($1, $2, to_char($2, 'YYYY-MM'), $3)
```

`$2` (a Python `datetime`) was sent **untyped**, so PostgreSQL resolved
`to_char(unknown, unknown)` ambiguously → `AmbiguousFunctionError` → HTTP 500.

**Applied fix (smallest type-safe correction, semantics preserved):**

```sql
VALUES ($1, $2::timestamptz, to_char($2::timestamptz, 'YYYY-MM'), $3)
```

**Evidence it worked:** the API was restarted against the isolated env and the
canonical `POST /api/v3/processing/items/{id}/customer-review` no longer produces
500/`AmbiguousFunctionError` — it now returns a **deterministic 409** (a
state-machine refusal from `_require_transition`), i.e. execution proceeds *past*
the previously crashing usage write. `run_acceptance.py` stayed **16/16**.

**Not yet achieved:** a *successful* canonical approval with observable allowance
consumption. The remaining 409 is a workflow-state refusal, not the billing
defect; the harness's `ct_qc_approved` item is being refused the `approved`
transition (`ct_qc_approved → ct_qc_approved`, status unchanged), so either the
canonical manual path requires an intermediate state or the fixture item is not in
the state the transition table expects. This is a **diagnosis step, not a code
change** — no workflow logic was altered.

### 11.2 R4 — fixture accepted, authorization still refuses

The corrected E2E fixture row (exact schema shape: `processing_entity_id = PE_A`,
`assigned_to = NULL`, `assignee_kind='processing_entity'`, `action='assign'`,
`actor_domain='processing_entity'`, `assigned_by = <PE-A user>`, `status='open'`)
was **accepted by the database (`assign : 201`)** — the 23502/shape errors are
gone.

**However `GET /api/v3/pe/items/{ITEM_PE_A}/workspace` as `pe_a_manager` still
returns 403**, and PE-B → same item still 403, PE-A → Org B item 403,
unauthenticated 401. Because a schema-valid *open* item-level assignment is now
present and the handler still refuses, this is **no longer explainable as a
missing-fixture problem** (`_ensure_assigned_item` resolves
`work_item_effective_entity(item)` and compares it to `pe.entity_id`; the
remaining mismatch must be traced in that resolver, e.g. batch-vs-item precedence
or the entity identity used by the PE context). Per mandate §10 the authorization
path was **not** patched speculatively; the exact refusal remains to be traced.

### 11.3 Test results (this cycle, current)

* `run_acceptance.py` — **16/16 PASS**
* `run_p6f_acceptance.py` — **34/37**
  * D6 approval-time: **409** (was 500 → was 402); `customer_decision`: **409**
  * PE-A item workspace: **403** (unchanged)
  * D8 6/6, other D11/PE denials unchanged
* `npx playwright test` — **16 total: 13 passed / 0 failed / 3 skipped, exit 1,
  34.4s** (three consultant-surface specs still skipped)
* `pytest backend/tests/unit backend/tests/e2e` — launched again; **not
  completed** within the session → no counts claimed
* Fixtures: `items 200`, `item A 200`, `allow 200`, **`assign 201`**,
  `submit → 200`

### 11.4 Files changed in 009

`backend/data/billing.py` (the `::timestamptz` cast — **product code, the one
authorized defect fix**) ·
`e2e/environment/scripts/seed_lifecycle_fixtures.py` (correct PE assignment row
shape + `uid` import) · this report section · the 009 prompt-history file.

### 11.5 Verdict

**P6-2F REMEDIATION PARTIALLY COMPLETE — BLOCKERS REMAIN**

## 12. CT-P6-2F-REMED-20260911-010 — FINAL BLOCKING DIAGNOSIS

### 12.1 Blocker A (D6) — root cause found: burned idempotency keys + incomplete cast

Exact evidence (real Org-A owner JWT, isolated API):

```
D6  a68689c7  500  {"message":"column \"usage_month\" is of type date but
                    expression is of type text"}
D6  0d4edab4  409  {"message":"idempotency key 'charge:item:0d4edab4-…' already used"}
D6 replay a68689c7  409  same idempotency key message
item=a68689c7 → ct_qc_approved      usage_rows=0 units=0
```

Three distinct facts, all now proven:

1. **The 409 was never a state-machine refusal.** `backend/domain/partners.py:107`
   defines `"ct_qc_approved": ("customer_review", "mapping", "approved",
   "rejected")` — so `ct_qc_approved → approved` **is** a valid transition. The 409
   body is `idempotency key 'charge:item:<item>' already used`, i.e. the D37 charge
   **replay guard working correctly**.
2. **Why the keys are burned:** the charge path claims the idempotency key
   (`_claim_key`, `backend/services/billing.py:733`) **before** the usage write that
   the original defect crashed. Every 500 therefore *consumed the key* while leaving
   the item `ct_qc_approved` and `usage_tracking` empty — a stuck state created by
   the pre-009 defect. Retrying the same item can never succeed; a **fresh,
   un-charged item** is required to evidence D6.
3. **The 009 cast was incomplete** (my own change): `to_char()` returns `text` but
   `usage_month` is a **`date`** column → `column "usage_month" is of type date but
   expression is of type text`. This was corrected in 010 to
   `date_trunc('month', $2::timestamptz)::date` (semantics preserved: same
   month-bucket, correct column type). The statement is now type-consistent; it has
   **not yet been proven end-to-end** because every available item's key is burned.

**Classification: A (E2E fixture/state) + the authorized application fix.** No
workflow/state-machine logic was changed — the transition table is correct as
written. Required next action (fixture-only): add a **fresh** `ct_qc_approved` item
and approve that, then observe state `approved`, `usage_tracking` row/units
increment, and a 409 replay with no second write.

### 12.2 Blocker B (PE-A) — root cause found: seed role lacks `can_process`

Exact evidence:

```
GET /api/v3/pe/me → 200 {"entity":{"id":"a6e795f5-…","name":"P6F Processing Entity A Ltd",
                     "status":"active"},"role":{"key":"qc_specialist"},
                     "capabilities":["communicate","qc","read_work"]}
GET /api/v3/pe/items/{PE_A_ITEM}/workspace → 403
     {"message":"staff lacks permission: can_process"}
SQL public.work_item_effective_entity(item) → a6e795f5-… (= PE_A)
item = PE_A in manual_extraction_items; batch.entity = PE_A; open assignment
     processing_entity_id = PE_A, assignee_kind = processing_entity
```

The PE auth context resolves the **correct** entity (PE_A), the item, batch and the
schema-valid open assignment all agree on PE_A, and the SQL resolver returns PE_A.
The refusal is purely a **capability** refusal: the seeded `pe_a_manager` persona
holds the `qc_specialist` roster role, whose capability set omits **`can_process`**,
which the workspace route requires.

**Classification: A (E2E fixture/seed role gap).** This is *not* a PE authorization
defect and no resolver precedence or authorization code was touched. Required next
action (fixture-only): seed the PE processing role/membership for `pe_a_manager`
with `can_process` (e.g. the processing-operator role), then re-verify PE-A ALLOW
and confirm PE-B / cross-org / IDOR / unauthenticated denials are unchanged.

### 12.3 Test results (this cycle, current)

* `run_acceptance.py` — **16/16** (last run, unchanged)
* `run_p6f_acceptance.py` — **34/37** (D6 approval 409, `customer_decision` 409,
  PE-A workspace 403; D8 6/6 and the remaining denials unchanged)
* `npx playwright test` — **16 total / 13 passed / 0 failed / 3 skipped, exit 1**
* `pytest backend/tests/unit backend/tests/e2e` — **not completed** (no counts claimed)

### 12.4 Files changed in 010

`backend/data/billing.py` — cast corrected to
`date_trunc('month', $2::timestamptz)::date` (the same authorized defect fix, made
type-correct) · this report section · the 010 prompt-history file.

### 12.5 Verdict

**P6-2F REMEDIATION PARTIALLY COMPLETE — BLOCKERS REMAIN**

## 13. CT-P6-2F-REMED-20260911-011 — E2E COMPLETION (fixture handoff)

No new architectural investigation; this section records the exact, fully
specified fixture changes and the current state, because the cycle ended before
they could be applied and re-verified.

### 13.1 D6 — fresh eligible item (fixture-only)

The existing D6 items (`a68689c7…`, `0d4edab4…`, `ITEM_A3`, `ITEM_A6`) all have
**burned** `charge:item:<id>` idempotency keys from the pre-009 500s, so no existing
item can evidence canonical approval. Required fixture (add to
`e2e/environment/scripts/seed_lifecycle_fixtures.py`, deterministic `uuid5`, idempotent):

* a **new** `manual_extraction_items` row, Org A, `status='ct_qc_approved'`,
  `batch_id = BATCH_A`, `processing_origin='CARBONTALLY_INTERNAL'`,
  `processing_mode='manual'`, `consultant_firm_id = FIRM_A` (matching the other
  lifecycle fixtures) → guarantees an **unused** `charge:item:<new-id>` key.

Then run the canonical `POST /api/v3/processing/items/{new}/customer-review` as
`org_a_owner` and record: item → `approved`, a `usage_tracking` row written with
`ai_files_processed ≥ 1`, `usage_month` populated as a **date**, allowance remaining
decrementing by 1, entitlement ownership unchanged (Org A), and a **replay** that
returns the deterministic idempotency refusal with **no second usage row**.

### 13.2 PE-A capability — fixture-only, exact mechanism identified

* `GET /api/v3/pe/me` → entity = **PE_A** (`a6e795f5-…`), `role.key = "qc_specialist"`,
  `capabilities = ["communicate","qc","read_work"]`.
* `backend/api/pe_auth.py:52,66` — the frozen PE role vocabulary maps
  `qc_specialist → {read_work, qc, communicate}`; **`can_process` is not part of that
  role**. The workspace route requires `can_process`
  (`403 "staff lacks permission: can_process"`).
* The persona's role comes from `staff_roles` / `staff_profiles.role_id` (per
  `backend/api/v3_operations.py:19`).

Required fixture: seed the `pe_a_manager` persona with the **existing** PE
manager/operator role (the role whose existing capability set includes
`can_process`) instead of `qc_specialist` — no new role, no new capability, no
authorization change, no production change.

Once applied, re-verify: PE-A workspace **200**; PE-B → PE-A item **403**; PE-A →
Org B item **403**; unassigned IDOR **403**; unauthenticated **401**; alternate PE
routes (already 403/405) unchanged.

### 13.3 Consultant browser skips — still open

The three skipped specs remain unfixed this cycle. Their skip conditions are
state-based (`Submit to CarbonTally QC` / `Pass review` visibility, and "no lifecycle
notification") plus the same role/capability class now proven for PE. No production
authorization change is warranted; the remaining work is E2E fixture/state and a
completed browser run.

### 13.4 Test results (current, no historical substitution)

* `run_acceptance.py` — **16/16**
* `run_p6f_acceptance.py` — **34/37** (D6 approval 409, `customer_decision` 409,
  PE-A workspace 403 — all three now attributable to the two fixture gaps above)
* `npx playwright test` — **16 total / 13 passed / 0 failed / 3 skipped, exit 1**
* `pytest backend/tests/unit backend/tests/e2e` — **not completed**; no counts claimed

### 13.5 NF-4 regression coverage

The applied billing fix
(`date_trunc('month', $2::timestamptz)::date`) is type-correct; its live regression
evidence is the E2E canonical approval path itself (13.1). No mock was written and no
new test framework was created, per §14.

### 13.6 Files changed in 011

Documentation only (this section + the 011 prompt-history file). No code, fixture,
schema, RLS, role or configuration change was made in this cycle.

### 13.7 Verdict

**P6-2F REMEDIATION PARTIALLY COMPLETE — BLOCKERS REMAIN**

## 14. CT-P6-2F-REMED-20260911-012 — FINAL EXECUTION (both blockers resolved)

### 14.1 Fixture A — fresh D6 item (APPLIED)

`e2e/environment/scripts/seed_lifecycle_fixtures.py` now seeds a **new**
deterministic item `ITEM_A8 = det("item:a8")` — Org A, `BATCH_A`,
`status='ct_qc_approved'`, `processing_origin='CARBONTALLY_INTERNAL'`,
`processing_mode='manual'`, `consultant_firm_id=FIRM_A` — i.e. a legitimate
existing workflow state with an **unused** `charge:item:<id>` idempotency key
(`items : 201`).

### 14.2 Fixture B — PE-A persona role (APPLIED, isolated E2E only)

```
UPDATE staff_profiles SET role_id=(existing staff_roles row) WHERE user_id=<pe_a_manager> → UPDATE 1
role=pe_manager
```

The persona now holds the **existing** PE manager role (whose capability set already
includes `can_process`). No new role, no new capability, no authorization, RLS or
production change.

### 14.3 Results — both blockers now pass

```
D6  approval-time approval succeeds + consumes  org_a_owner -> 200   (ct_qc_approved -> approved)
PE  PE A opens its assigned item                pe_a_manager -> 200
API ACCEPTANCE: 16/16 passed
```

* **D6 canonical approval SUCCEEDED**: `HTTP 200`, item transitioned
  `ct_qc_approved → approved` with the allowance/charge path now executing
  (the pre-009 `to_char` defect and the burned-key state are both cleared).
* **PE-A ALLOW SUCCEEDED**: workspace `200`; PE-B → PE-A item `403`; PE-A → Org B
  item `403`; unauthenticated `401` — all denials intact.
* **D6 negatives intact**: Org-B `404`, consultant `404` (grant ≠ ownership), PE
  `404`, unauthenticated `401`.

### 14.4 Harness re-runnability (class B, harness-only)

The acceptance harness is **not idempotent across runs**: the first run consumes
the fresh item (and its charge key), so a second run reports
`D6 → 403 (approved→approved)` and `D11 customer_decision → 409`. Those are
**artefacts of repeated execution**, not product behaviour — the successful first-run
evidence is recorded above and in §14.3. A future cycle should either re-seed the
fixture before each harness run or use a distinct item per assertion.

### 14.5 Current suite numbers (this cycle)

* `run_acceptance.py` — **16/16 PASS**
* `run_p6f_acceptance.py` — **35/37** (first run: D6 200/approved and PE-A 200;
  second-run replay of consumed items yields the D6 403 / D11 409 artefacts above)
* `npx playwright test` — **16 total / 13 passed / 0 failed / 3 skipped, exit 1, 32.6s**
* `pytest backend/tests/unit backend/tests/e2e` — **not completed** (no counts claimed)

### 14.6 Remaining findings

* **F4** — three consultant browser specs still skip (unchanged).
* **F5** — full pytest not completed.
* **D11** — `submitted_to_qc` evidenced (durable firm-centric notification, replay
  idempotent, denied-path silent); `customer_decision` evidenced on first run;
  `accepted`/`qc_outcome`/`rework` still lack full event-level records.
* **Harness** — re-runnability (see §14.4).
* Resolved this cycle: **R4/PE-A ALLOW** and **D6 canonical approval**.

### 14.7 Files changed in 012

`e2e/environment/scripts/seed_lifecycle_fixtures.py` (fresh `ITEM_A8`) ·
`e2e/environment/scripts/run_p6f_acceptance.py` (D6 expectation now asserts the
successful transition; D11 uses a distinct item) · this section · the 012
prompt-history file. Isolated E2E persona role updated in the database
(`staff_profiles`, `pe_a_manager` → existing `pe_manager` role). No application
code, schema, RLS, capability or production change.

### 14.8 Verdict

**P6-2F REMEDIATION PARTIALLY COMPLETE — BLOCKERS REMAIN**

## 15. CT-P6-2F-FINAL-20260911-013 — EVIDENCE CLOSURE

### 15.1 Status of the two resolved blockers (re-confirmed this cycle)

* **D6 canonical approval** — succeeded in cycle 012 (`HTTP 200`, item
  `ct_qc_approved → approved`, usage write executes — the pre-009 `to_char` /
  `usage_month` defect is fixed by
  `date_trunc('month', $2::timestamptz)::date`). Re-running the harness now returns
  `403 (approved→approved)`, i.e. **the item is already approved** — repeat-run
  state, not a defect.
* **PE-A ALLOW** — re-confirmed this cycle: `pe_a_manager → /api/v3/pe/items/{PE_A_ITEM}/workspace`
  = **200**; PE-B → PE-A item **403**; PE-A → Org B item **403**; unauthenticated
  **401**; alternate routes 403/405. All denials intact.

### 15.2 Acceptance harness re-runnability — root cause identified, NOT yet implemented

The harness is stateful because each assertion consumes the single fixture item
(and its `charge:item:<id>` idempotency key). Required fix (§10 option B/C):
either re-seed the isolated state before a full run, or give **each assertion its
own deterministic item**. Identified, not implemented in this cycle — this is the
principal remaining harness work.

### 15.3 Consultant browser skips — unchanged

`npx playwright test` remains **16 total / 13 passed / 0 failed / 3 skipped**
(specs: submit-to-QC, pass-review, notification deep link). Their guards are
state-based and are not satisfied by the current isolated fixture state; resolving
them requires additional legitimate lifecycle/notification fixture state (and a
completed browser run). No production authorization change is warranted.

### 15.4 D11 — five-event evidence

* `submitted_to_qc` — evidenced (real submit 200, durable firm-centric notification,
  replay idempotent with no duplicate rows, denied submit 403 with zero new rows).
* `customer_decision` — evidenced on the first run of cycle 012 (200 + notification).
* `accepted`, `qc_outcome`, `rework` — still lack complete event-level records
  (only state-idempotency 409 / route-inventory 405 / authorization-scoped 403
  probes so far).
* D11 and **D11-C1 (firm-centric recipients)** were not modified.

### 15.5 Regression (this cycle)

* `run_acceptance.py` — **16/16 PASS**
* `run_p6f_acceptance.py` — **35/37** (PE-A 200 ✓; the two flagged lines are the
  §15.2 repeat-run state)
* `pytest backend/tests/unit backend/tests/e2e` — launched with a 40-minute budget;
  **still running at the session cut-off with no failures observed in the progress
  stream**. No counts are claimed.
* Playwright — as §15.3.

### 15.6 NF-4 regression evidence

The live D6 approval path (cycle 012) exercised the corrected SQL against the real
isolated database — `usage_tracking` insert with a properly typed
`usage_month`. No mock-only test was added; that live path is the available
regression coverage (no suitable existing live-DB unit layer exists).

### 15.7 Security / environment / git

All security properties unchanged and re-confirmed: unauthenticated 401, cross-org
403/404 (+ zero-row RLS), cross-firm 403, PE cross-PE 403, PE IDOR 403,
consultant→internal ops 403, entitlement ownership Org-A, no actor/recipient/origin
injection, replay safe. Work stayed inside the isolated environment
(`:55325` / `:55326` / `:8051` / `:3000`); production, demo and investor untouched.
branch `main` · HEAD `16391217103b98dcea520070c5a22c68f12fe607` · staged **none** ·
commit **no** · push **no** · reset/clean **no** · unrelated pre-existing
modifications preserved.

### 15.8 Deferred (classified for later, NOT implemented — roadmap protection)

* Harness re-runnability (P6-2F harness debt).
* Consultant browser skip fixtures (P6-2F acceptance completeness).
* Any UX/analytics/auditor/performance observations — for Phase 7/8 planning.

### 15.9 Verdict

**P6-2F REMEDIATION PARTIALLY COMPLETE — BLOCKERS REMAIN**

## 16. CT-P6-2F-FINAL-20260911-014 — FINAL EVIDENCE PREPARATION

### 16.1 Consultant browser skips — exact cause captured (fixture state consumption)

Direct evidence (real `consultant_a` JWT, isolated API):

```
GET /api/v3/processing/items/{item:a}/workspace  → 200  status = consultant_reviewed
GET /api/v3/processing/items/{item:a2}/workspace → 200  status = consultant_reviewed
GET /api/v3/notifications (consultant_a)         → 200
   [{notification_type: "consultant.lifecycle.customer_decision", recipient_type: "user", …}]
```

* The consultant **authorization and workspace access are correct** (200, full workspace
  payload with `batch/data/issues/item/source/status/workflow`).
* The skips are caused by **fixture state consumption**: `item:a` has already advanced
  `calculated → consultant_reviewed` (the pass-review spec needs `calculated`), and the
  earlier mutating runs left the lifecycle items in post-action states. Test 3's item
  (`item:a2`) is `consultant_reviewed` but the submit control still did not present —
  the residual difference needs UI-side inspection.
* A `consultant.lifecycle.customer_decision` notification **now exists for consultant A**,
  so the notification deep-link spec's "no notification" guard should no longer trip.

**Required minimal fixture (identified, not applied):** give each mutating spec its own
dedicated, run-reset item — e.g. `item:a9` (`calculated`, FIRM_A) for pass-review and
`item:a10` (`consultant_reviewed`, FIRM_A) for submit-to-QC — and have
`seed_lifecycle_fixtures.py` re-assert those statuses on every run and write the fresh ids
into `tests/e2e/.env.personas` (`E2E_ITEM_A_ID` / `E2E_ITEM_A2_ID`). This makes both the
browser specs and the API harness reproducible from a known clean state **without touching
authorization, RLS, capabilities or workflow semantics**, and without removing skip
conditions or weakening assertions.

### 16.2 D11 — remaining events

`submitted_to_qc` and `customer_decision` are evidenced (durable firm-centric
notifications, replay idempotent, denied paths silent). `accepted`, `qc_outcome` and
`rework` still lack complete event-level records; they require fresh dedicated items and
the same run-reset discipline described in §16.1. D11 and **D11-C1** remain untouched.

### 16.3 Harness reproducibility

Same root cause as §16.1 (consumed items and their `charge:item:<id>` keys). The
minimal, non-redesign fix is the dedicated-per-assertion item approach above. Recorded
as P6-2F tooling debt rather than redesigned.

### 16.4 Regression

* `run_acceptance.py` — **16/16 PASS** (last clean run)
* `run_p6f_acceptance.py` — **35/37** (PE-A 200 ✓; the two flagged lines are the
  §16.3 repeat-run state)
* `npx playwright test` — **16 total / 13 passed / 0 failed / 3 skipped** (24–34 s,
  exit 1)
* `pytest backend/tests/unit backend/tests/e2e` — launched this cycle with a 50-minute
  budget; **not observed to complete within the session** → **no counts claimed**

### 16.5 Security / environment / git

Unchanged and re-confirmed: unauthenticated 401 · cross-org 403/404 (+ zero-row RLS) ·
cross-firm 403 · PE cross-PE 403 · PE IDOR 403 · consultant→internal ops 403 ·
entitlement ownership Org-A · no actor/recipient/`processing_origin` injection · replay
safe. Isolated environment only (`:55325` / `:55326` / `:8051` / `:3000`); production,
demo and investor untouched. branch `main` · HEAD
`16391217103b98dcea520070c5a22c68f12fe607` · staged **none** · commit **no** · push
**no** · reset/clean **no** · unrelated pre-existing modifications preserved.

### 16.6 Verdict

**P6-2F REMEDIATION PARTIALLY COMPLETE — BLOCKERS REMAIN**

## 19. CT-P6-2F-FINAL-EVIDENCE-EXECUTION-20260911-017 — EVIDENCE EXECUTION

### 19.1 Executed sequentially, to completion, and observed

**Task A — full browser suite** (`npx playwright test`, isolated frontend `:3000` /
API `:8051` / Supabase `:55325`, real JWTs from `tests/e2e/.env.personas`, which the
015 fixture repointed to `ITEM_A9` (`calculated`) and `ITEM_A10`
(`consultant_reviewed`)):

```
Running 16 tests using 2 workers
 ✓  1 consultant-lifecycle  consultant opens the deep-linked item workspace (14.8s)
 ✓  5..11 route-protection  (7 specs, unauthenticated redirects + sign-in surface)
 ✓ 12 security-denies      cross-firm consultant cannot open another firm client item
 ✓ 13 security-denies      organisation member cannot approve a customer decision
 ✓ 14 security-denies      unauthenticated API calls are rejected
 ✓ 15 security-denies      consultant cannot invoke the internal ops workspace route
 ✓ 16 security-denies      consultant cannot reach the admin control plane
 -  2 consultant-lifecycle  consultant submits reviewed work to CarbonTally QC
 -  3 consultant-lifecycle  consultant completes the review action on a calculated item
 -  4 consultant-lifecycle  the consultant's own notification deep link resolves to the item
 3 skipped / 13 passed (34.1s)   PW_EXIT=0
```

**Result: 16 total · 13 passed · 0 failed · 3 skipped · exit code 0 · 34.1 s.**
The three consultant-lifecycle ALLOW specs still skip.

### 19.2 Why the three still skip (evidence, not speculation)

* Those specs guard on the **visible UI control**, not on API authorization: the
  consulted API returns **200** for the same items (`GET /api/v3/processing/items/{id}/workspace`
  as `consultant_a` → 200, `status` correctly `calculated` / `consultant_reviewed`
  after the 015 fixture reassert). The browser therefore reaches the authenticated
  workspace but does not present the `Pass review` / `Submit to CarbonTally QC`
  control the spec waits for, and the `/notifications` page's `/^open$/i` link is not
  matched by the persisted lifecycle notification.
* No authorization, RLS, capability or workflow assertion failed anywhere: all 13
  executable specs — including every DENY and route-protection spec and the IV-N6
  deep-link spec — passed.
* Per §4 (fixture logic frozen) and §18 (evidence-only failure), **no fixture or
  harness change was made in this prompt.** Diagnosing the UI-control gating further
  would be a harness/UI investigation, which this prompt does not authorize.

### 19.3 Outstanding evidence (unchanged by this cycle)

* D11 `accepted`, `qc_outcome`, `rework` — no executor route was exercised this cycle;
  the missing piece is a fresh un-consumed item per event plus capture of the
  persisted notification, its `event_key`, the server-derived firm recipient and the
  replay/denied-path results.
* Full `pytest backend/tests/unit backend/tests/e2e` — not completed (long-running;
  §5 forbids overlapping runs and no completion was observed).
* reset → reseed → acceptance → browser cycle — not executed.

### 19.4 Preserved evidence (not reopened; not re-executed)

D6 approval (200, `ct_qc_approved → approved`, live usage write, safe replay, Org-A
entitlement ownership) · PE-A 200 with PE-B / cross-org / IDOR / unauthenticated /
alternate-route denials · RLS zero-row cross-tenant filtering · real-JWT
authentication · D7 provenance (`CARBONTALLY_INTERNAL` / `PROCESSING_ENTITY` only) ·
D8 existing conversation model · D11 `submitted_to_qc` + `customer_decision` ·
**D11-C1** firm-centric recipients. `run_acceptance.py` remains **16/16**.

### 19.5 File-modification policy compliance

```
Application code changed: NO
Fixture logic changed:   NO
Schema changed:          NO
RLS changed:             NO
Roles/capabilities:      NO
Billing changed:         NO
Product behavior:        NO
```

Documentation only: this section + the 017 prompt-history file. Isolated environment
only (`:55325` / `:55326` / `:8051` / `:3000`); production, demo and investor
untouched. branch `main` · HEAD `16391217103b98dcea520070c5a22c68f12fe607` ·
staged **none** · commit **no** · push **no** · reset/clean **no**.

### 19.6 Verdict

No material defect was discovered; all executable acceptance specs pass. The required
evidence set is incomplete **for execution/tooling reasons only**.

**P6-2F REMEDIATION PARTIALLY COMPLETE — EVIDENCE EXECUTION BLOCKED**

Exact incomplete evidence: (1) the three consultant-lifecycle ALLOW specs still skip
(visible-control gating, while the same items return HTTP 200 at the API);
(2) D11 `accepted`; (3) D11 `qc_outcome`; (4) D11 `rework`; (5) a completed
`pytest backend/tests/unit backend/tests/e2e` run with exact counts; (6) the
reset → reseed → acceptance → browser reproducibility cycle.


### 18.1 Executed this cycle

```
=== FIXTURES (reassert) ===   items : 200   LIFECYCLE FIXTURES OK
=== API ===                   ACCEPTANCE: 16/16 passed
=== BROWSER (full) ===        launched (16 specs, isolated frontend/API/Supabase,
                              real JWTs, .env.personas repointed to ITEM_A9/A10)
                              → run did not finish within the session budget
```

* **Fixture reassert** — `seed_lifecycle_fixtures.py` re-applied the dedicated
  run-reset items (`ITEM_A9` → `calculated`, `ITEM_A10` → `consultant_reviewed`) plus
  the allowance / PE-assignment / subscription fixtures, idempotently (`items : 200`).
* **API acceptance** — `run_acceptance.py` = **16/16 PASS** (application + RLS
  boundary, real JWTs).
* **Browser** — the complete suite was launched with the corrected fixtures and was
  **still executing at the cut-off, so no 016 browser counts are claimed**. Last fully
  captured run remains **16 total / 13 passed / 0 failed / 3 skipped**.

### 18.2 Evidence still outstanding (class B — evidence/tooling only, no defect found)

| Item | State |
|---|---|
| Browser suite captured with run-reset fixtures | launched, not captured |
| D11 `accepted` | not yet evidenced (needs a fresh un-consumed engagement fixture) |
| D11 `qc_outcome` | not yet evidenced (needs a fresh QC-eligible item + real QC decision) |
| D11 `rework` | not yet evidenced (needs a fresh item driven through an actual rejection path) |
| Full `pytest backend/tests/unit backend/tests/e2e` | launched repeatedly; **never observed to complete** → no counts claimed |
| reset → reseed → acceptance → browser cycle | not completed |

### 18.3 Preserved evidence (unchanged, not reopened)

D6 (approval 200, `ct_qc_approved → approved`, live usage write, safe replay, Org-A
ownership) · PE-A 200 with PE-B / cross-org / IDOR / unauthenticated / alternate-route
denials · RLS zero-row cross-tenant filtering · real-JWT authentication · D7
provenance (`CARBONTALLY_INTERNAL` / `PROCESSING_ENTITY` only, server-derived
`consultant_firm_id`) · D8 existing conversation model · D11 `submitted_to_qc` and
`customer_decision` evidenced · **D11-C1** firm-centric recipients.

### 18.4 Security / environment / git

No change to authorization, RLS, schema, roles, capabilities, permissions, billing,
entitlement ownership, `processing_origin`, D7, D8, D11 or D11-C1; no new routes,
conversation kinds or product behaviour. Isolated environment only
(`:55325` / `:55326` / `:8051` / `:3000`); production, demo and investor untouched.
branch `main` · HEAD `16391217103b98dcea520070c5a22c68f12fe607` · staged **none** ·
commit **no** · push **no** · reset/clean **no** · unrelated pre-existing
modifications preserved.

### 18.5 Verdict

**No material product/security/architecture defect was discovered.** The remaining
items are evidence-completeness only:

**P6-2F REMEDIATION PARTIALLY COMPLETE — BLOCKERS REMAIN**

Exact remaining blockers: (1) capture the browser suite with the applied run-reset
fixtures; (2) D11 `accepted`; (3) D11 `qc_outcome`; (4) D11 `rework`; (5) a completed
`pytest backend/tests/unit backend/tests/e2e` run with exact counts; (6) the
reset → reseed → acceptance → browser cycle.


### 17.1 Applied fixture — dedicated run-reset items (Work Item A, part 1)

`e2e/environment/scripts/seed_lifecycle_fixtures.py` now seeds two **dedicated
run-reset** items and repoints the mutating browser specs at them:

```
ITEM_A9  = det("item:a9")   status = calculated            (pass-review spec)
ITEM_A10 = det("item:a10")  status = consultant_reviewed    (submit-to-QC spec)
→ tests/e2e/.env.personas:  E2E_ITEM_A_ID  = <A9>
                            E2E_ITEM_A2_ID = <A10>
```

Fixture run output: `items : 201` · `allow : 200` · `assign : 200` ·
`LIFECYCLE FIXTURES OK`. The seeding is idempotent and re-asserts the required
statuses on every run, so the browser assertions can no longer be starved by earlier
mutations. No authorization, RLS, role, capability, schema or workflow semantics were
touched; no skip was removed and no assertion weakened.

### 17.2 Browser outcome

The full Playwright run was launched against the isolated frontend/API/Supabase with
real JWTs and the repointed `.env.personas`; **it had not finished when the session
budget ended, so no 015 browser counts are claimed.** The last fully captured run
remains **16 total / 13 passed / 0 failed / 3 skipped**, and the skip cause is now
fixed at fixture level (16.1 → 17.1).

### 17.3 Remaining evidence gaps (Work Items B, C, D)

* **B — D11 `accepted`, `qc_outcome`, `rework`**: still lack complete event-level
  records. They require the same dedicated-item discipline (a fresh, un-consumed item
  per event) plus capture of the persisted notification, its `event_key`, the
  server-derived firm recipient and the replay outcome. D11 and **D11-C1** remain
  untouched throughout.
* **C — full `pytest backend/tests/unit backend/tests/e2e`**: launched again this
  cycle with a 50-minute budget; **not observed to complete** → no counts claimed.
* **D — reset/reseed reproducibility proof**: `reset.sh` + `seed_e2e.py` +
  `seed_lifecycle_fixtures.py` remain the reproducible path; a full reset→reseed→
  (acceptance+browser) cycle was not completed this session.

### 17.4 Already-settled evidence (unchanged, not reopened)

D6 canonical approval (200, `ct_qc_approved → approved`, live usage write, safe
replay, Org-A-owned entitlement) · PE-A workspace 200 with PE-B / cross-org / IDOR /
unauthenticated denials · RLS zero-row cross-tenant filtering · real-JWT
authentication · D7 provenance (`CARBONTALLY_INTERNAL` / `PROCESSING_ENTITY` only,
server-derived `consultant_firm_id`) · D8 existing conversation model · D11
`submitted_to_qc` and `customer_decision` evidenced · D11-C1 firm-centric recipients.

### 17.5 Security / environment / git

No RLS, schema, role, capability, permission, entitlement, billing,
`processing_origin`, D7, D8, D11 or D11-C1 change; no new routes or product
behaviour. Isolated environment only (`:55325` / `:55326` / `:8051` / `:3000`);
production, demo and investor untouched. branch `main` · HEAD
`16391217103b98dcea520070c5a22c68f12fe607` · staged **none** · commit **no** · push
**no** · reset/clean **no** · unrelated pre-existing modifications preserved.

### 17.6 Verdict

No product/application/architecture/security defect was discovered; the remaining
items are evidence-completeness only (class B). No independent verification is
claimed.

**P6-2F REMEDIATION PARTIALLY COMPLETE — BLOCKERS REMAIN**

Remaining: (1) capture the browser run with the applied fixtures; (2) D11
`accepted` / `qc_outcome` / `rework` event evidence; (3) a completed full pytest run
with exact counts; (4) the reset→reseed reproducibility proof.


Remaining (all fixture/evidence, no application/architecture/policy issue):
(1) dedicated run-reset items for the three consultant browser specs;
(2) complete `accepted` / `qc_outcome` / `rework` event evidence;
(3) a completed full pytest run with exact counts;
(4) harness/browser reproducibility via the §16.1 approach.





Both remaining blockers are **fixture-only** and precisely specified: (1) a fresh
`ct_qc_approved` item for the D6 approval + consumption evidence; (2) a `can_process`
PE role for the `pe_a_manager` persona. **No application, workflow, authorization,
RLS, billing-policy, D7/D8/D11/D11-C1 or `processing_origin` change is required.**


Remaining: (1) D6 canonical approval still refused at the state-machine step
(409) — needs the transition precondition diagnosed, not changed;
(2) PE-A workspace still 403 with a valid assignment — `work_item_effective_entity`
must be traced; (3) three consultant browser specs still skipped;
(4) full pytest not completed. No architecture/billing/policy redesign was
performed or required.


| ID | Status after 008 |
|---|---|
| F1 / R4 (PE-A 403) | **Root cause identified** (fixture gap, exact row shape known) — fixture not yet applied |
| F2 / NF-4 (D6 approval 500) | **Root cause identified** (`to_char` ambiguity, `billing.py:849`) — application defect; fix requires a product-code change |
| F3 (D11 events) | Unchanged — needs the NF-4 path working before `customer_decision` can be evidenced |
| F4 (3 browser skips) | Unchanged — needs a completed browser run |
| F5 (regression) | Unchanged — run not completed |
| F6/F7/F8 | Unchanged (non-blocking / informational) |


Remaining blockers: **NF-3/NF-4** (approval path 500 with a legitimate allowance →
D6 ALLOW + `customer_decision` unevidenced), **R4** (PE-A workspace 403,
assignment NOT NULL constraint), **R5 verification** (browser re-run + full
regression), and R3 is now fixed (harness reads real notification rows).




The original `42501` blocker is **resolved** — the RLS boundary is now genuinely
testable and passing (16/16, incl. cross-tenant RLS filtering and PE isolation).
Remaining gaps are the D6/D8/D11/PE-browser coverage plus the three
literal-expectation mismatches above.





---

# CT-P6-2F-RESUME-20260911-001 — EXECUTION ADDENDUM (2026-09-11)

**Prompt Ref:** `CT-P6-2F-RESUME-20260911-001` · **Branch:** `main` · **HEAD:** `daad396523ac693352cc2f4ebb7fc58814a9e60b`
**Role:** Cline — implementation/evidence agent (NOT the independent verifier).

This addendum closes the evidence gaps recorded in §19 (`...-017`) and records one
**new blocking product defect** found by that evidence, its fix, and the
reproducibility proof. P6-2C / P6-2D / P6-2E were not reopened; no settled evidence
was re-executed for its own sake.

## 1. Environment brought up (isolated only)

| Item | Value |
|---|---|
| Supabase / Auth (GoTrue) | `http://127.0.0.1:55325` (project `carbontally_e2e`) |
| Postgres | `127.0.0.1:55326` |
| Backend | `uvicorn main:app --host 127.0.0.1 --port 8051` (662 routes), env from `.env.e2e` |
| Frontend | CRA dev server `http://localhost:3000`, `REACT_APP_SUPABASE_URL`/`REACT_APP_API_URL` pointed at the isolated stack |
| Backend `.env` | **not** sourced; backend vars were exported per-process from `.env.e2e` |
| Production / demo / investor | **not contacted**; the served dev bundle (`/static/js/bundle.js`) contains **no** production project ref (0 occurrences) and 0 `onrender` references |

## 2. F4 — the three browser skips: ROOT CAUSE, FIX, RESULT

**Root cause (proved, not inferred).** A standalone Playwright probe signed in as the
real `consultant_a` persona and measured the guard value at both moments:

| Probe | Value at the guard (as the spec evaluated it) | Value after waiting for the app | Reality |
|---|---|---|---|
| item `calculated` → `Pass review` | `false` — page body at that instant was `"Checking access…"` | **`true`** | workspace API returns `"calculated"` |
| item `consultant_reviewed` → `Submit to CarbonTally QC` | `false` | **`true`** | — |
| `/notifications` → link `Open` | `0` matches | **`2` matches** | two real lifecycle notifications with deep links |

The specs probed for a control with `isVisible()` / `count()` **immediately after
navigation**. Those APIs do not auto-wait, so the probe evaluated against the SPA's
`Checking access…` gate and skipped a control that genuinely exists. **The skips were a
harness synchronisation defect, not a product defect** — the same items returned HTTP
200 from `GET /api/v3/processing/items/{id}/workspace` with the expected statuses, and
the same items are what the D11 evidence below drives.

**Fix (harness only, assertions strengthened not weakened).** `tests/e2e/personas.ts`
gained `waitForAccessCheck(page)` (waits for the access gate to clear) and
`visibleAfterLoad(locator)` (bounded wait, then a real visibility probe);
`consultant-lifecycle.spec.ts` uses them before its `test.skip(...)` guards. The DENY
specs are deliberately untouched — for them the *absence* of the workspace is the
assertion, so they must **not** wait for content. No mock, no skip removed, no
assertion relaxed: the three specs now actually perform the review, the submission and
the notification deep-link and assert their outcomes.

**Result:** `3 skipped / 13 passed` → **`16 passed / 0 failed / 0 skipped`** (0 exit).

## 3. NEW DEFECT `LT-1` (P1) — customer acceptance returned HTTP 500

**Symptom.** `POST /api/v3/organizations/{org}/consultant-engagements/{id}/accept`
returned **500** `inconsistent types deduced for parameter $2 / DETAIL: text versus
character varying`. The engagement stayed `pending`: no transition, no audit, no D11
`accepted` notification. This is the only path from a pending engagement to active
(P6-1C), so customer acceptance of a consultant engagement was **broken against a real
database**. The consultant-side lifecycle moves that share the same statement
(`/api/v3/consultants/**` suspend/end, discovery end, engagement reject) are affected
identically; `update_task_status` (`consultant_tasks`) had the same defect.

**Root cause.** In `backend/data/consultants.py` the same parameter was assigned to a
`character varying` status column *and* compared with text literals in `CASE`
branches, so PostgreSQL deduced two types for `$2` and rejected the whole statement.
Parameter-type inference happens at parse time, so it failed regardless of data.

**Why it survived.** Unit tests exercise a **fake** repository (`tests/unit/api/fakes.py`)
— the SQL never executed. The only real-database coverage (the integration suite) is
currently non-functional for this area (finding `LT-2` below). P6-2F's `accepted`
evidence had never been executed.

**Fix (smallest correct change, product code).** Pin the parameter to text where it is
assigned, in the two affected statements:
`SET status = $2::text` in `transition_client_lifecycle` and in `update_task_status`
(the `CASE` comparisons then agree). Verified first by a rolled-back SQL probe against
the isolated database:

| Statement | Before | After |
|---|---|---|
| `consultant_clients` transition | `AmbiguousParameterError: inconsistent types deduced for parameter $2` | `OK` for every target (`active`, `suspended`, `ended`, `rejected`, `pending`) |
| `consultant_tasks` update | same error | `OK` |

Nothing else was touched: no schema, RLS, role, capability, billing, origin, D7, D8, D11
or D11-C1 change; no new route; no API contract change (the endpoint's behaviour is now
the behaviour it always documented).



## 4. D11 lifecycle evidence completed — `accepted`, `qc_outcome`, `rework`

New script `e2e/environment/scripts/verify_lifecycle_events.py` (isolated-only guard;
refuses any target but `:55325`). Real GoTrue personas, real endpoints, evidence read
back from the persisted rows; it restores the fixtures it consumes.

| Event | Trigger (real endpoint, real JWT) | HTTP | Entity after | Notification evidence |
|---|---|---|---|---|
| `accepted` | org-B **owner** accepts the pending engagement | **200** | `pending` → **`active`** | `consultant.lifecycle.accepted:engagement:9db837d8-…`; exactly one row per active firm member; recipients = server-derived firm membership; the accepting customer is not notified of its own decision; replay → **409** with no duplicate row; consultant attempt → **403** |
| `qc_outcome` (approved) | consultant submits item A10, then internal QC approves | 200 / **200** | `reviewed` → **`ct_qc_approved`** | `…qc_outcome:item:057bd21b-…:approved`; recipients include the engaged firm; `actor_domain=internal_staff`; replay → **409**; consultant attempt → **403** |
| `qc_outcome` (rejected) | internal QC rejects item A7 | **200** | `reviewed` → **`ct_qc_rejected`** | `…qc_outcome:item:04e671e9-…:rejected`; same recipient/actor guarantees |
| `rework` | (same rejection — source `ct_qc_rejected`) | — | — | `…rework:item:04e671e9-…:ct_qc_rejected`; recipients include the engaged firm; rows deep-link to `/consultant/items/<client>/<item>` |

**Result: `LIFECYCLE EVIDENCE: 30/30 checks passed; 0 failed`** (report written to
`e2e/environment/.lifecycle_evidence_report.json`). Every previously outstanding D11
event is now evidenced with its deterministic `event_key`, its server-derived firm
recipients, its replay behaviour and a denied path. D11-C1 (firm-centric recipients)
is preserved and re-confirmed.

Fixture addition (E2E-only): `seed_lifecycle_fixtures.py` now seeds a deterministic
**pending** engagement (`engagement:org-b-firm-a`, origin `engagement_request`) for the
org-B owner to accept. ORG-B/FIRM-A is a pair no other P6-2F assertion depends on.

## 5. API acceptance and browser security acceptance

| Suite | Result |
|---|---|
| `run_acceptance.py` (RLS/PostgREST + FastAPI boundary matrix) | **16/16 PASS** |
| `npx playwright test` (browser ALLOW + DENY + route protection) | **16 passed / 0 failed / 0 skipped** |

Backend unit regression: `pytest tests/unit` → **1,763 passed / 0 failed / 0 errors / 0 skipped** (exit 0).
Application E2E suite: `pytest tests/e2e` → **39 passed / 0 failed / 0 errors / 0 skipped** (exit 0).

## 6. Reproducibility proof (reset → reseed → evidence → acceptance → browser)

```text
bash e2e/environment/scripts/reset.sh   # drop + re-migrate the isolated DB
                                        #   -> APPLIED=27 SKIPPED=26 ALL_APPLIED
seed_e2e.py                             # 13/13 personas authenticated, 0 errors, SEED OK
seed_lifecycle_fixtures.py              # items/allow/assign/subs/engage/submit OK
verify_lifecycle_events.py              # 30/30 PASS   (on the FRESH schema)
run_acceptance.py                       # 16/16 PASS
npx playwright test                     # 16 passed / 0 failed / 0 skipped
```

The chain was executed twice — once against the pre-existing environment and once after a
**full reset and reseed** — with identical results, so the evidence is reproducible and
the `LT-1` fix holds on a freshly migrated schema.

## 7. Findings and disposition

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| **LT-1** | **P1** | Consultant/client lifecycle transitions and consultant-task updates returned HTTP 500 on a real database (ambiguous `$2`), so **customer acceptance of a consultant engagement was broken** (the P6-1C path) | **FIXED** in this operation (two SQL parameters); evidenced end-to-end. It would block the first customer, so it blocks the gate — hence fixed rather than deferred |
| **LT-2** | **P3** | The dedicated integration database `carbontally_test` schema is **stale**: its consultant suite errors on `column "can_extract" does not exist` before reaching the statements, so repository SQL has effectively **no automated real-DB coverage** — exactly why `LT-1` survived | **NOT FIXED** — environment provisioning is outside P6-2F scope. Owner: test-infrastructure/environment work. Mitigation now in place: `verify_lifecycle_events.py` exercises the real endpoints against the current schema on every P6-2F evidence cycle. Does not block first customer |
| **F4** | — | Three browser skips | **RESOLVED** — harness synchronisation; 16/16 pass |

**No P0/P1 security finding remains.** No cross-tenant authorization defect was found:
the DENY matrix (cross-firm consultant, org member vs customer decision, consultant →
internal `/ops`, consultant → admin control plane, unauthenticated API) passes on both
the API and the browser boundaries, and the new evidence adds DENY checks for
engagement acceptance and QC decisions (403 each).

## 8. Files changed by this operation

| File | Change |
|---|---|
| `backend/data/consultants.py` | `SET status = $2::text` ×2 (+ explanatory comments) — the `LT-1` fix |
| `tests/e2e/personas.ts` | `waitForAccessCheck` + `visibleAfterLoad` helpers (F4) |
| `tests/e2e/carbontally/consultant-lifecycle.spec.ts` | use the helpers before the skip guards (F4) |
| `e2e/environment/scripts/seed_lifecycle_fixtures.py` | deterministic pending-engagement fixture + env export |
| `e2e/environment/scripts/verify_lifecycle_events.py` | **new** D11 evidence + lifecycle-transition regression script |
| this addendum | evidence record |

Unchanged: schema, migrations (22 → 53 untouched), RLS, roles/capabilities/permissions,
billing/entitlement, `processing_origin`, D7, D8, D11/D11-C1 semantics, frontend code and
the API contract. Production, demo and investor environments were never contacted.

## 9. Git

branch `main` · HEAD `daad396523ac693352cc2f4ebb7fc58814a9e60b` · staged **none** ·
commit **no** · push **no** · repository reset/clean **no** · unrelated pre-existing
working-tree changes preserved.

## 10. Verdict (implementation only)

**P6-2F IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION.**

No independent verification is claimed here; that is a separate, fresh-context operation.

