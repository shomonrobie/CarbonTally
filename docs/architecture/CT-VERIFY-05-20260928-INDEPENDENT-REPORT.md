# CT-VERIFY-05 — Independent verification of CT-IMPLEMENT-04 (legacy factor-read repoint)

**Date:** 2026-09-28
**Verifier:** independent verification agent (CT-VERIFY-05), separate from the CT-IMPLEMENT-04 implementer
**Repository (frozen target):** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled` — **HEAD:** `dc3d78dc8021bd65978754cf131c38045ff8013d` (unchanged by this run)
**Brief:** `docs/architecture/CT-IMPLEMENT-04-20260928-INDEPENDENT-VERIFICATION-BRIEF.md`
**Artefacts under test:** `docs/architecture/CT-IMPLEMENT-04-20260928-REPORT-FACTOR-READ-REPOINT.md` + the frozen working-tree change-set

> **Mandate honoured:** no product code, schema, RLS, migration, test or frozen-report edit; no
> commit, push, rebase, reset or deploy; the frozen tree was not mutated (every verifier artefact
> was written under `/tmp/ctv05`); the investor-demo dataset and the live Supabase project were
> never contacted; `/home/shomonrobie/carbon_tally` (a different tree at `20b7a928…`) was not touched.

---

## 1. Scope

Verify, independently and with runtime evidence, the **20 authorised non-PD-gated factor-read
repoints** from the retired `defra_conversion_factors` onto the canonical `emission_factors`, plus
the two CT-SCHEMA-03 F-09 frontend embed removals, the extended regression guard, the residual
inventory, the API contract and the absence of schema change.

Explicitly out of scope (per brief §6.4): PD-3 / PD-4 / PD-5 gated surfaces, F-08, the divergent PD
registers, the `.gitignore` pre-existing modification.

---

## 2. Environment and apparatus

| Element | Value |
|---|---|
| Frozen tree | `/home/shomonrobie/ct_93d5cdd` @ `dc3d78dc8021bd65978754cf131c38045ff8013d`, branch `p8-release-reconciled` |
| **AFTER** base | working tree, `uvicorn main:app` on `127.0.0.1:8071` (dirty tree = the change-set; HEAD identical to BEFORE) |
| **BEFORE** base | pristine HEAD extracted with `git archive HEAD backend` into `/tmp/ctv05/base_head` (no worktree mutation), `uvicorn main:app` on `127.0.0.1:8072` |
| Database | disposable clone `ct_verify05_pg`, Postgres `127.0.0.1:55530` (never a persistent environment) |
| PostgREST | `3099` (root) + gateway `127.0.0.1:54531` bridging `/rest/v1`; service token minted locally |
| Seed | Org A `…000a` / Org B `…000b`; members `ownerA …000a` (Org A `owner`), `ownerB …000b` (Org B `owner`), `outsider …000c` (no membership); 3 emissions rows in Org A + 1 in Org B; 2 canonical factor rows |
| F-046-1 | **honoured** — the integration harness (`TRUNCATE … RESTART IDENTITY CASCADE`) was never run; only seed-time `CREATE` plus read-only SQL/HTTP against the disposable clone |

**Controlled-variable disclosure.** `run_mod.sh` (AFTER) additionally exports `DATABASE_URL`;
`run_base.sh` (BEFORE) does not. Cases that depend on `DATABASE_URL` (`/api/v3/exports/…`) are
therefore **not** a clean A/B and are not used as evidence for or against the repoint. The
factor-embed cases are unaffected: both trees reach the same PostgREST endpoint with the same
service key, and only the SQL/embed string under test differs.

**Side-effect control.** `export_history` row count after every probe = **0** (`exports.py:97–108`
builds an export record but never inserts it), so the cross-tenant probe neither created nor
modified victim-tenant data. All other probes were `GET`/`POST` reads.

---

## 3. Freeze-baseline integrity (brief §1) — **PASS**

| Check | Expected | Measured |
|---|---|---|
| `git rev-parse HEAD` | `dc3d78dc8021bd65978754cf131c38045ff8013d` | ✔ identical |
| `git branch --show-current` | `p8-release-reconciled` | ✔ identical |
| tracked modified files | 12 | ✔ 12 (11 from the task + `.gitignore`) |
| `git --no-pager diff --stat HEAD -- backend frontend` | 8 files, 131 insertions, 32 deletions | ✔ `8 files changed, 131 insertions(+), 32 deletions(-)` |
| `sha256sum -c` (10 task files) | all OK | ✔ all OK |
| `sha256sum -c` (5 governance files) | all OK | ✔ all OK |
| freeze re-checked **after** all controls/probes | unchanged | ✔ 12 tracked modifications, HEAD `dc3d78dc…` |

Untracked-tree note (recorded, not removed — AGENTS.md §70): the tree also contains pre-existing
untracked scratch artefacts unrelated to the change-set (e.g. the single-character files `8` and
`=`); nothing produced by this verification lives outside `/tmp/ctv05`.

---

## 4. Verdict summary (brief §7 template)

| # | Area | Verdict | Evidence |
|---|---|---|---|
| 1 | 20 repoints present and correct | **PASS** | §5.1 |
| 2 | Canonical `emission_factors` usage (projection parity) | **PASS** | §5.2 |
| 3 | API response-contract preservation | **PASS** | §5.3 |
| 4 | Organization authorization / tenant isolation (ALLOW + DENY) | **FAIL** | §5.4, finding **F-05-R1** |
| 5 | PostgREST FK embed validity | **PASS** | §5.5 |
| 6 | Reporting / dashboard / export runtime behaviour | **FAIL** (partial; factor values correct where the route completes) | §5.6, **F-05-R2/R3/R4** |
| 7 | Frontend behaviour | **BLOCKED** (static leg PASS, browser leg not executable) | §5.7 |
| 8 | 34-case regression guard (+ negative control) | **PASS** | §5.8 |
| 9 | Retired name absent from non-gated runtime surfaces | **PASS** (with recorded count drift) | §5.9, **F-05-R6** |
| 10 | Canonical 92-migration schema preserved | **PASS** | §5.10 |
| — | Freeze baseline integrity (§1) | **PASS** | §3 |

**Overall verdict (AGENTS.md §73 language):**

> The 20 repoints are **IMPLEMENTED, locally TESTED and now independently VERIFIED for areas
> 1–3, 5 and 8–10**, including runtime end-to-end proof that the canonical embed resolves and
> returns real factor values. **Area 4 FAILS** with a reproducible **cross-tenant data disclosure**
> (High) that CT-IMPLEMENT-04 makes reachable; **area 6 FAILS** in part (report generation and
> organisation activity still return 500 for pre-existing defects the change surfaced); **area 7 is
> BLOCKED** for the browser leg. **CT-IMPLEMENT-04 is therefore NOT ACCEPTED.** The repoint itself is
> correct and should not be reverted; it must be completed by a follow-on task
> (`CT-IMPLEMENT-05`) that restores server-side organisation scoping on the export routes and clears
> the surfaced 500s, after which areas 4 and 6 must be re-verified.

---

## 5. Area-by-area results

### 5.1 Area 1 — all 20 repoints present and correct: **PASS**

*Method.* (a) The brief §2 count command; (b) per-file `grep -n 'defra_conversion_factors'` expecting
no output; (c) an independent accounting that does not rely on the brief: `git archive HEAD backend|frontend`
into `/tmp/ctv05/base_head*` and compare every repointed file's occurrence count at HEAD against the
working tree.

| File | Occurrences at HEAD | Occurrences now | Canonical now |
|---|---|---|---|
| `backend/report_generator.py` | 3 | **0** | 4 |
| `backend/routes/emissions.py` | 2 | **0** | 2 |
| `backend/routes/organizations/data.py` | 7 | **0** | 7 |
| `backend/routes/organizations/dashboard.py` | 4 | **0** | 4 |
| `backend/routes/organizations/exports.py` | 1 | **0** | 1 |
| `frontend/src/App.js` | 1 | **0** | 0 |
| `frontend/App_.js` | 2 | **0** | 0 |
| **Total** | **20** | **0** | 18 |

The per-file distribution (3 / 2 / 7 / 4 / 1 / 1 / 2 = **20**) reproduces the brief §2 table and the
`grep '^-' … | grep -o 'defra_conversion_factors' | wc -l` = **20** removed occurrences exactly. 18
canonical replacements plus 2 deletions-without-replacement (`frontend/src/App.js` dead embed,
`frontend/App_.js` orphan fallbacks) account for all 20. `frontend/src/App.js` and `frontend/App_.js`
now contain **zero** occurrences of either name — consistent with a pure removal.

### 5.2 Area 2 — canonical `emission_factors` usage / projection parity: **PASS**

Full unified diffs (`-U2`/`-U3`) of all five backend files were read hunk by hunk against
`git archive HEAD` baselines. Every hunk is one of:

* (a) legacy table name → `emission_factors`;
* (b) local variable `defra` → `factor_row`;
* (c) an added explanatory comment;
* (d) `record.get('emission_factors')` / `(record.get('emission_factors') or {})` — the None-safe
  form of the legacy `record.get(..., {})` (hardening, not a semantic change).

**No column list, projection, `!left` hint, `.eq()`/`.gte()`/`.lte()` filter, order, page size or
returned JSON key changed.** Specifically:

* `exports.py:56` keeps the `emission_factors!left(activity_type, co2e_multiplier)` hint form;
* `data.py:142/:230` keep `activity_type, co2e_multiplier, reporting_year`; `:392` keeps the same
  projection and the function's own pre-existing organisation check;
* `dashboard.py:109/:203` keep `emission_factors (activity_type)` and the `organization_id` filter;
* `report_generator.py:594` keeps the same three columns; the three scope-classification reads keep
  their exact `activity_type` semantics;
* `emissions.py:153` keeps the full projection, and the response keys
  `defra_factor_id` / `activity_type` / `co2e_multiplier` / `reporting_year` are **retained**.

### 5.3 Area 3 — API response-contract preservation: **PASS**

*OpenAPI A/B* (app imported from `backend/` for both trees): `paths_before=606 paths_after=606`,
`methods 720/720`, `schemas 300/300` with identical names, `paths_only_before=[]`,
`paths_only_after=[]`, `path_method_changed=[]`, **`leaf_diffs=0`** — the document is unchanged by
the change-set.
*Runtime key retention*: `GET /api/{orgA}/emissions` (ownerA) returns
`"defra_factor_id":"eeee…0002","activity_type":"Electricity (kWh, UK grid)","co2e_multiplier":0.20707,"reporting_year":2024`
— the four contract keys are present and carry the canonical values. The same request against the
BEFORE base reports `MISSING_KEYS=['"defra_factor_id"','"activity_type"','"co2e_multiplier"','"reporting_year"',…]`
(HTTP 500), i.e. the keys could not be emitted at all before the repoint.

*Recorded discrepancy (not a regression):* the brief §3.3 expects
`/api/organizations/{org_id}/defra-factors` to be "still registered". That path is **absent in both**
trees; the registered catalogue path is `/api/organizations/data/{org_id}/defra-factors`
(`data.py:364`). Before/after identical → no contract change.

### 5.4 Area 4 — organization authorization / tenant isolation: **FAIL** (blocking)

*Method.* An **independent** probe (`/tmp/ctv05/authz_probe.py`) that mints its own HS256 tokens from
the disposable PostgREST secret, prints the `sub` it actually signed, and uses three identities:
`ownerA` (Org A `owner`), `ownerB` (Org B `owner` — **no membership of Org A**), `outsider` (no
membership). It was run against both bases. Ownership facts were confirmed directly in the database:
`organization_members` = (`…000a` → user `…000a` owner), (`…000b` → user `…000b` owner) only.

| Request (as `ownerB`, member of Org B only) | BEFORE (:8072) | AFTER (:8071) |
|---|---|---|
| `POST /api/organizations/{ORG_A}/exports/exports/emissions` `{"format":"json"}` | HTTP 500 (PGRST200, embed broken) | **HTTP 200 — Org A's emission rows returned** |
| `POST` same, as `outsider` | 403 | 403 |
| `POST` same, as `ownerA` | 500 | 200 |
| `GET /api/organizations/{ORG_A}/exports` | 200 (empty; `export_history` has 0 rows) | 200 (empty) |
| `GET /api/{ORG_A}/emissions` as `ownerB` | 500 (fails closed, wrong status) | 500 (fails closed, wrong status) |
| `GET /api/organizations/{ORG_A}/dashboard-summary` as `ownerB` | 500 (fails closed) | 500 (fails closed) |
| `GET /api/organizations/data/{ORG_A}/emissions-data` as `ownerB` | 500 (fails closed) | 500 (fails closed) |
| `GET /api/{ORG_A}/emissions` as `ownerA` (ALLOW) | 500 (embed broken) | **200 with rows + factor values** |

Reproduction (AFTER, verbatim):

```
[AFTER] POST ownerB /api/organizations/aaaa0005-…-00000000000a/exports/exports/emissions -> HTTP 200
        cross_tenant_needles=['aaaa0005-…-00000000000a', 'fafa0005-…-000000000001']
        body[0:260]=[\n {\n "id": "fafa0005-…-000000000001",\n "organization_id": "aaaa0005-…-00000000000a", …
```

Root cause (read, not guessed):

* the route is `POST /api/organizations/{org_id}/exports` + `/exports/emissions` → the real path is the
  doubly-nested `…/exports/exports/emissions` (`exports.py:17` prefix, `:44` decorator);
* its only authorization dependency is `require_org_member()` (`exports.py:48`), which
  (`backend/auth.py:445–468`) asserts nothing more than `current_user.is_org_member` — "is a member of
  **some** organisation". It never compares the **path** `org_id` with the caller's organisation;
* the handler then runs with the **service-role** Supabase client and scopes the query only by the path
  parameter (`.eq('organization_id', org_id)`, `exports.py:55–57`), so it reads another tenant's rows
  and returns them directly as the response body (`:113–120`).

**Attribution.** The authorization defect is **pre-existing** (it is not created by these 20 repoints),
but the *reachability* of the disclosure **is** created by CT-IMPLEMENT-04: at HEAD the same request died
with `PGRST200` before any row was read; after the repoint the embed resolves and the request succeeds
with another tenant's emissions data. For a commercial multi-tenant emissions platform this is a
High-severity cross-tenant disclosure of the platform's core data, and it is a direct consequence of
shipping this change-set as-is. See **F-05-R1**.

Same-class surfaces (identified statically, deliberately **not** probed — a DELETE probe would be
destructive): `GET {org}/exports`, `GET {org}/exports/{export_id}/download`, `DELETE {org}/exports/{export_id}`
(`require_org_admin`, whose check at `auth.py:481–511` also never compares the path org), and further
modules that depend on `require_org_member()` without any `organization_members` comparison of their own
(`backend/api/*`, `backend/routes/*` — 47 files matched the dependency; only the export, emissions,
dashboard and data routes were executed here). A dedicated authorization sweep is required; this report
claims only what was executed.

### 5.5 Area 5 — PostgREST FK embed validity: **PASS**

*Schema (read-only, disposable clone):*
`emissions_logs_emission_factor_id_fkey :: FOREIGN KEY (emission_factor_id) REFERENCES emission_factors(id)`;
`information_schema.tables` count for `public.defra_conversion_factors` = **0** (the retired table does
not exist in the canonical schema).

*Direct PostgREST A/B (no application code involved):*

```
GET /rest/v1/emissions_logs?select=id,organization_id,emission_factors(activity_type,co2e_multiplier)&limit=2
-> HTTP 200  [{"id":"…0001","emission_factors":{"activity_type":"Natural gas (kWh, Gross CV)","co2e_multiplier":0.18293}},
              {"id":"…0002","emission_factors":{"activity_type":"Electricity (kWh, UK grid)","co2e_multiplier":0.20707}}]

GET /rest/v1/emissions_logs?select=id,organization_id,defra_conversion_factors(activity_type,co2e_multiplier)&limit=2
-> HTTP 400  {"code":"PGRST200", … "message":"Could not find a relationship between 'emissions_logs' and 'defra_conversion_factors' …"}
```

The `!left` hint form used by `exports.py` and the projection forms used by the routes were exercised
through the application (§5.6): `POST …/exports/exports/emissions` returns
`"emission_factors":{"activity_type":…,"co2e_multiplier":…}` per row; the CSV and catalogue routes
return the same values. **No `PGRST200` occurred in the modified run**: the AFTER uvicorn log contains
**0** occurrences of `PGRST200` / `Could not find a relationship`, versus many in the BEFORE log. RLS was
not the cause of any empty result (the server-side service-role key behaviour is unchanged).

### 5.6 Area 6 — reporting / dashboard / export runtime behaviour: **FAIL** (partial)

*Factor-value requirement (the area's purpose) — satisfied where the route completes.* For Org A with
three known rows and two canonical factor rows, the AFTER run returned values **exactly matching**
`emission_factors`:

| Surface | BEFORE | AFTER | Factor data |
|---|---|---|---|
| `GET /api/{orgA}/emissions` | 500 PGRST200 | **200** | `…0002 → Electricity (kWh, UK grid) 0.20707 / 2024`; `…0001 → Natural gas (kWh, Gross CV) 0.18293 / 2025`; NULL-factor row → explicit `null`s |
| `GET /api/organizations/data/{orgA}/emissions/export-csv` | 500 PGRST200 | **200** | CSV rows carry `Activity Type`, `Reporting Year`, `Multiplier` = canonical values; NULL-factor row degrades to empty (neutral, pre-existing semantics) |
| `POST …/exports/exports/emissions` | 500 PGRST200 | **200** | JSON rows carry `emission_factors` objects with the canonical values |
| `GET /api/organizations/data/{orgA}/defra-factors` (catalogue repoint) | 500 PGRST205 | **200** | both canonical factor rows |
| `GET /api/organizations/{orgA}/dashboard-summary` | 500 PGRST200 | **200** | org name + summary (2026 window has no rows) |

*Routes that still return 500 after the repoint (all pre-existing defects, surfaced not caused):*

1. `reports/generate-enhanced-report` and the `/api/generate-enhanced-report` compatibility route →
   `500 Report generation failed: FPDF.set_fill_color() takes from 2 to 4 positional arguments but 6 were given`.
   The failing call sites (`report_generator.py:449/452`, plus the `*fill_color` splat at `:360`) are
   **identical** in the HEAD archive and the working tree and are not inside any CT-IMPLEMENT-04 diff hunk;
   at HEAD the request died earlier on the embed, so this FPDF incompatibility was masked. The brief's
   expectation "no `set_fill_color` traceback in the modified run" is therefore **not met** (2 occurrences
   in the AFTER log).
2. `organization-activity` → `500 … column users_1.raw_user_meta_data does not exist` (42703) — an
   unrelated select/schema defect in `dashboard.py`'s activity query, outside the repointed lines.
3. `data/emissions-data` as ownerA → `500 … 2 validation errors: response.organization_id Field required`
   — the route's `response_model` requires `organization_id` while the handler returns
   `{'records': [...], 'total': n}`; the echoed input shows the records *were* produced, i.e. the repoint
   advanced the request past the embed failure and exposed a pre-existing response-model mismatch.
4. Own-tenant `GET /api/{orgB}/emissions` (ownerB) → `500 … 'NoneType' object has no attribute 'get'`.
   The Org B fixture row has a NULL `asset_id`, and `asset = record.get('assets', {})` (an **unchanged**
   context line at `emissions.py:197`) yields `None` before `asset.get('facilities', {})`. Pre-existing and
   data-shape dependent.

The area verdict is **FAIL** because two of the area's mandated surfaces (the report generator and
organisation activity) cannot be exercised at all; the factor-value leg measured correctly, and a CSV/JSON
that merely downloads is explicitly not treated as proof here (AGENTS.md §74) — the values were compared
row-by-row against the database.

### 5.7 Area 7 — frontend behaviour: **BLOCKED** (browser leg) / static leg PASS

*Static evidence (executed).* `frontend/src/index.js` imports `./App` — so `frontend/src/App.js` is the
live CRA entry — and **no** file under `frontend/src`, `frontend/package.json` or `frontend/public`
references `App_`; `frontend/App_.js` (where the two `row.defra_conversion_factors?.…` fallbacks were
removed) is therefore a **build-orphan** outside CRA's `src/` root and is neither built nor served.
The Dashboard's emissions-history select (`frontend/src/App.js:719–731`) contains no factor embed and the
existing consumers read `row.metadata?.fuel_type` (`:1593`) and the upload mapping `row[fieldConfig.factor]`
(`:1055`) — nothing reads the removed embed. `frontend/` (excluding `node_modules`/`build`) contains
**0** occurrences of the retired name, so no bundle or missed embed still targets it.

*Why the browser leg is BLOCKED.* Rendering the authenticated Dashboard requires a build of the frozen
revision plus working auth against the disposable DB. The only build present
(`frontend/build/index.html`, dated 2026-09-22) **predates** the change and cannot validate it; a rebuild
would write into the frozen tree (`frontend/build`, prohibited by brief §4.4) and the SPA embeds its
Supabase project configuration at build time, which the disposable stack cannot satisfy for an
authenticated session. `chromium`/`google-chrome` is installed but there is **no automation harness**
(no Playwright/Cypress/Puppeteer in `frontend/node_modules/.bin`), so no console/network capture could be
performed. Recorded as **BLOCKED — browser leg not executable in this environment**, never PASS
(brief §5). No console/network claim is made anywhere in this report.

### 5.8 Area 8 — the 34-case regression guard (+ negative control): **PASS**

| Check | Result |
|---|---|
| `pytest backend/tests/unit/test_ct_implement_01_remediation.py -q` (repo root, `/usr/bin/python3`, `-p no:cacheprovider`) | exit **0** |
| `--collect-only` | `tests/unit/test_ct_implement_01_remediation.py: **34**` |
| AST counts | `_REPOINTED_FILES` = **11**, `_CANONICAL_FACTOR_READ_FILES` = **5**, `_LEGACY_REFERENCE_ALLOWLIST` = **7**, `_LEGACY_SCAN_ROOTS` = **5**, `test_*` functions = **13** |
| case arithmetic | 11 + 4 + 5 + 1 + 13 = **34** ✔ |
| `_REPOINTED_FILES` covers the repoint | all 5 backend files + both frontend files ✔ |

Negative controls were run in a **throwaway copy** (`/tmp/ctv05/guard_copy2`, 1036 files) so the frozen
tree was never mutated:

| Control | Mutation | Expected | Observed |
|---|---|---|---|
| A | none | 34 pass | ✔ 34 pass |
| B | legacy reference added to `backend/config.py` (non-allowlisted) | FAIL | ✔ `AssertionError: assert ['backend/config.py'] == []` |
| C | B reverted | 34 pass | ✔ 34 pass, 0 residual probe lines |
| D | legacy embed restored to `frontend/src/App.js` (repointed file) | FAIL | ✔ both `test_no_legacy_factor_table_reference_remains[frontend/src/App.js]` and the confinement test FAILED |

After the controls the frozen tree still shows `tracked_modifications=12` at HEAD `dc3d78dc…` ✔.

### 5.9 Area 9 — retired name absent from non-gated runtime surfaces: **PASS** (drift recorded)

Independently re-measured (occurrences, not files):

| Surface | Brief/report expectation | Measured | Classification |
|---|---|---|---|
| `backend/routes/admin/defra.py` | 16 | **16** | PD-3 / F-06 — gated |
| `backend/routes/reports.py` | 2 (`:279` PD-5, `:1290` PD-3) | **2** | gated |
| `backend/routes/reference.py` | 1 | **1** | comment only |
| guard test | 5 | **5** | intentional |
| `admin/src/**` (3 files) | 9 | **9** | PD-3 / F-07 — gated |
| `prisma/` | `schema.prisma` 7 + `seed.ts` 1 | **7 in `prisma/schema.prisma`; `prisma/seed.ts` does not exist** — the single occurrence is the root-level `seed.ts` (1) | stale artefacts |
| `supabase/**` | *not listed* | **8 in 3 files** (2 historical migrations quoting the name + 1 snippet) | historical SQL, not a live read |
| `e2e/environment/scripts/canonical_schema_verify.py` | 1 | **1** | deliberate absence assertion |
| pre-V3 backup bundle | 4 (3 files) | **4 (3 files)** | not live |
| `docs/**` | 82 | **300 across 68 files** | governance/prose |
| `tools/` | — | **0** | clean |
| `frontend/` (excl. `node_modules`, `build`) | 0 | **0** | clean |
| `backend/**` total | 24 | **24** (4 files: the 4 gated/guard files only) | the 5 repointed files are **0** |

**Zero occurrences in the 11 `_REPOINTED_FILES`; zero in live code outside the 7-entry allowlist.**
Drift (F-05-R6): `docs/**` measured 300 vs the report's 82 (the docs tree includes many files added after
that measurement, including the CT-IMPLEMENT-04 report itself with 12 and the brief with 9);
`supabase/**` = 8 was omitted from the report's table; `prisma/seed.ts` does not exist. None of these is a
runtime surface and the guard must not be adjusted for them (brief §3.9).

### 5.10 Area 10 — canonical 92-migration schema preserved: **PASS**

| Check | Expected | Measured |
|---|---|---|
| migration files | 92 | ✔ 92 (working tree) / ✔ 92 (`git archive HEAD supabase/migrations`) |
| schema fingerprint | unchanged | ✔ `4dca3c20b74617feaa989023249b144bd3d8c1d118b6e194be7e9b197649aada` identical for worktree and HEAD |
| `git diff --name-only HEAD -- supabase prisma` | empty | ✔ 0 paths |

---

## 6. Findings

Severity follows AGENTS.md §45/§73. Each finding states route/role, reproduction, impact, root cause and
whether CT-IMPLEMENT-04 introduced it.

### F-05-R1 — Cross-tenant emissions disclosure via the repointed export embed — **HIGH, BLOCKING**

* **Route / role:** `POST /api/organizations/{org_id}/exports/exports/emissions`, dependency
  `require_org_member()`; any authenticated user who is a member of *any* organisation.
* **Reproduction (AFTER base :8071, disposable clone):** mint a token whose `sub` is a member of Org B
  only (`bbbb0005-…-000b`), then
  `POST /api/organizations/aaaa0005-…-000a/exports/exports/emissions {"format":"json"}` →
  **HTTP 200** with Org A's `emissions_logs` rows (payload contains
  `"organization_id":"aaaa0005-…-000a"` and row id `fafa0005-…-0001`). Against the BEFORE base the same
  request returns HTTP 500 (`PGRST200`) and discloses nothing.
* **Impact:** a member of one tenant can read another tenant's emissions data — the platform's core
  commercially sensitive output — over a documented public API path. It also establishes that the same
  request would write an `export_history` row attributed to the victim organisation if/when that insert is
  implemented (`exports.py:97–108`). `export_history` is currently never written, so no tenant data was
  modified by the probe (verified: 0 rows).
* **Root cause:** `require_org_member()` (`backend/auth.py:445–468`) tests only
  `current_user.is_org_member`; neither it nor the handler compares the path `org_id` with the caller's
  membership, and the handler queries with the service-role client (`exports.py:52–57`).
* **Introduced by CT-IMPLEMENT-04?** The *authorization defect* is **pre-existing** (present at HEAD and in
  earlier reports as the generic "org-scoped dependency" concern). The *exploitable behaviour* is
  **introduced by this change-set**: at HEAD the request was blocked by the invalid legacy embed
  (`PGRST200`) before any row was read; the repoint makes the endpoint work, so the latent gap becomes a
  live cross-tenant read. It must therefore be treated as a release blocker for this change-set.
* **Recommended remediation (separate task, not applied here):** enforce path-org scoping server-side in
  `require_org_member()`/`require_org_admin()` (or a new `require_org_scope` dependency): resolve
  `organization_members` for `(path org_id, current_user.user_id)` and 403 otherwise; then add
  `ALLOW`/`DENY` cases for `ownerB → Org A` on every repointed route to the runtime matrix and re-verify
  area 4. Related: the `require_org_admin()` path (`auth.py:481–511`) has the same shape and should be
  corrected in the same task.

### F-05-R2 — Three pre-existing 500s surfaced by the repoint — **MEDIUM**

1. Report generation: `FPDF.set_fill_color() takes from 2 to 4 positional arguments but 6 were given`
   (`report_generator.py:360`, `:449`, `:452`); the brief's "no `set_fill_color` traceback" expectation
   is not met (2 tracebacks in the AFTER log).
2. `organization-activity`: `column users_1.raw_user_meta_data does not exist` (42703).
3. `data/emissions-data`: response-model validation error (`organization_id` required, handler returns
   `{'records': …}`).
   *Attribution:* code identical at HEAD; masked before the repoint by the earlier embed failure. *Impact:*
   the reporting and activity features remain non-functional end-to-end; they must not be described as
   "fixed" by CT-IMPLEMENT-04 (AGENTS.md §74). *Remediation:* `CT-IMPLEMENT-05` (FPDF call signature,
   activity select, response model), with regression tests.

### F-05-R3 — Cross-tenant DENY returns HTTP 500 instead of 403/404 — **MEDIUM**

`ownerB → /api/{orgA}/emissions`, `/api/organizations/{orgA}/dashboard-summary` and
`/api/organizations/data/{orgA}/emissions-data` all return **500** with
`'NoneType' object has no attribute 'data'` instead of 403 (the underlying membership check uses
`.maybe_single()` and then dereferences `.data`). They **fail closed** (no data disclosed) but violate
AGENTS.md §46 and mask real denials as system faults. Pre-existing; unchanged by the repoint (identical
status/body on both bases).

### F-05-R4 — Own-tenant read with a NULL relation still raises AttributeError — **LOW**

`GET /api/{orgB}/emissions` (ownerB, own tenant, row with NULL `asset_id`) → 500
`'NoneType' object has no attribute 'get'` at `emissions.py:197` (`asset = record.get('assets', {})`
returns `None` when the embed is null, then `asset.get('facilities', …)`). The line is **unchanged** by the
change-set (it appears as diff context) and the failure mode predates the repoint; it is now reachable
again because the embed succeeds. The new `(record.get('emission_factors') or {})` idiom guards the factor
row but not the asset row — a small symmetry gap worth closing in `CT-IMPLEMENT-05`.

### F-05-R5 — Frozen report documentation inaccuracies — **LOW (documentation)**

Recorded, not fixed (brief §6.2 requires this; correcting the frozen report would invalidate §1):

| Report statement | Frozen source |
|---|---|
| "`_REPOINTED_FILES` (12 entries)" | **11** entries (verified by AST) |
| "13 test functions (34 parametrized cases)" | 13 unparametrized tests + 21 parametrized cases = 34 |
| guard ran in the "repo venv" | repo `.venv` has no pytest; `/usr/bin/python3` produces the 34-case result |

### F-05-R6 — Residual-inventory drift and omissions — **INFORMATIONAL**

* `docs/**` measured **300** occurrences across 68 files versus the report's **82** — the docs tree now
  contains many additional governance/analysis files (including the CT-IMPLEMENT-04 report itself, 12, and
  the verification brief, 9). Docs are not runtime surfaces; no action beyond recording (brief §3.9: do not
  adjust the guard).
* `supabase/**` = **8** occurrences in 3 files (historical migrations quoting the retired name, plus a
  snippet) is **absent** from the report's residual table. These are historical SQL artefacts; the
  canonical schema (92 migrations) is unmodified (git diff empty, fingerprint identical).
* `prisma/seed.ts` (expected 1) **does not exist**; the single `seed.ts` occurrence is the root-level file.
* `frontend/node_modules/.cache` (report: 29) was **not** counted here — it is outside every source scan
  root by design and regenerates on the next build.

### F-05-R7 — Guard scan-root coverage gap — **INFORMATIONAL**

`_LEGACY_SCAN_ROOTS` covers `backend/**/*.py`, `frontend/src/**/*.{js,jsx}` and `admin/src/**/*.{js,jsx}`.
It does **not** walk `frontend/*.js` (root bundles), `prisma/`, `e2e/` or the pre-V3 backup bundle, so a
*new* legacy reference introduced into a root-level frontend bundle would not fail the confinement test;
the two files touched by CT-IMPLEMENT-04 are covered by the explicit per-file
`test_no_legacy_factor_table_reference_remains` case, which was proven to fail on mutation (control D).
Measured today: `frontend/` outside `node_modules`/`build` = 0 occurrences, so no such reference exists.
Recommended (separate task): widen the scan roots to `frontend/*.js`/`frontend/*.jsx`.

### F-05-R8 — Out-of-scope pre-existing defects re-confirmed (no change) — **INFORMATIONAL**

* **F-08**: the catalogue route is `/api/reports/defra-factors/{year}`; `reports/defra-factors/2025` returns
  500 `PGRST205` on **both** bases (a real problem in `reports.py:279`, PD-5-gated), and the frontend calls
  `/api/defra-factors/{year}`. Unchanged by this change-set.
* `/api/v3/exports/emissions.json` differs between the bases only because of the apparatus difference
  disclosed in §2 (`DATABASE_URL`); it is not attributable to the repoint.
* The two divergent PD registers remain (cite which register when citing PD numbers).

---

## 7. Evidence index

All verifier artefacts are under `/tmp/ctv05/` (disposable, outside the repository):

| File | Content |
|---|---|
| `area10_final.txt` | git state, per-file inventory, migration fingerprint, frontend orphan checks, secret scan |
| `area11_final.txt` | corrected per-file occurrence accounting, diff-line repoint inventory, schema fingerprint A/B, entry-point determination, guard lists |
| `area14_hashes.txt` | `sha256sum -c` results for the 10 task files + 5 governance files (freeze gate) |
| `area15_guard.txt`, `area15_guard_counts.txt` | 34-case pytest run (exit 0, 34 collected), AST tuple/count verification |
| `area8_negctl2.txt` | regression-guard negative controls A–D in a throwaway copy + frozen-tree re-check |
| `area16_residuals.txt`, `area20_residual_sums.txt` | independent residual scan (349 occurrences / 80 files) and per-surface sums |
| `area12_db.txt` | FK graph on `emissions_logs`, row→factor linkage, canonical factor rows, legacy-table absence |
| `area12_rest.txt` | direct PostgREST embed A/B (canonical 200 / legacy 400 PGRST200) |
| `area13_db2.txt` | `export_history` = 0 rows (side-effect control), org/member fixtures |
| `area17_bodies.txt` | full ALLOW-path bodies (emissions, CSV, catalogue, dashboard, export JSON) with canonical factor values |
| `area18_frontend.txt` | CRA entry point, `App_.js` orphan proof, Dashboard select region, browser-harness availability |
| `area3_openapi.txt` | BEFORE/AFTER OpenAPI structural comparison (606 paths, 720 methods, 300 schemas, 0 leaf diffs) |
| `area4_authz_after.txt`, `area4_authz_before.txt` | independent cross-tenant probe against both bases (F-05-R1 evidence) |
| `run_mod.out`, `run_base.out` | 22-case runtime matrices (AFTER `cases=22 passed=11 failed=11`; BEFORE `cases=22 passed=5 failed=17`) |
| `uvicorn.log`, `uvicorn_base.log`, `area6_logs2.txt` | PGRST200 count 0 (AFTER) vs many (BEFORE); `set_fill_color` traceback present on the shared code path |
| `authz_probe.py`, `capture_bodies.py`, `residual_sums.py`, `evidence10.sh`, `evidence11.sh`, `negctl2.sh`, `openapi_ab.sh` | verifier tooling (not product code) |

---

## 8. Limitations and remaining unknowns

1. **Browser/console/network leg of area 7 is BLOCKED** (§5.7). No screenshot, console or network evidence
   exists, and none is claimed.
2. **Authorization sweep incomplete by design.** Only the export, emissions, dashboard and data routes were
   executed. The same dependency shape appears across ~47 modules; each requires its own ALLOW/DENY probe.
   No finding is asserted for the unprobed routes.
3. **Single-tenant fixtures.** The probe used two organisations and three identities. Role-level variations
   (Member/Viewer/consultant/PE/internal staff) and the 1,185-identity investor-demo population were **not**
   exercised (the investor demo was deliberately untouched).
4. **`POST …/exports/exports/emissions` returns raw rows, not a file.** `export_history` is never written
   (`exports.py:97–108`), so download/list/delete behaviour on that table could not be validated with real
   rows.
5. **Data-shape dependence.** One fixture row has `emission_factor_id IS NULL` and one has `asset_id IS
   NULL`; those exercised the neutral/None paths but not a full canonical population.
6. **Environment.** `backend/.env` points at an unroutable Supabase project, so all runtime evidence comes
   from the disposable stack (Postgres clone + PostgREST + gateway), not from a hosted environment. The
   `DATABASE_URL` apparatus difference between bases is disclosed in §2.
7. **PD-gated surfaces** (PD-3/PD-4/PD-5) and F-04 hardening remain unratified and were not assessed as
   defects.

---

## 9. Acceptance statement and recommended next steps

* **Implemented:** yes — 20 repoints across 7 files, per-file distribution reproduced independently.
* **Tested locally (implementer):** yes — 34-case guard, exit 0.
* **Independently verified:** yes for areas 1, 2, 3, 5, 8, 9, 10 and the freeze baseline; **no** for
  area 4 (FAIL), area 6 (FAIL, partial), area 7 (BLOCKED).
* **Accepted:** **NO.**

Recommended sequence:

1. **`CT-IMPLEMENT-05` (blocking):** restore path-org authorization on the exports router (and audit
   `require_org_member` / `require_org_admin` callers); return 403 rather than 500 on cross-tenant denial;
   guard the asset embed like the factor embed; resolve the FPDF / activity / response-model 500s. Add
   ALLOW+DENY runtime cases for every repointed route.
2. **Re-verify** areas 4 and 6 with the same disposable-stack method (the harness and evidence scripts
   already exist under `/tmp/ctv05`).
3. Widen the guard's scan roots (`frontend/*.js`) and correct the documentation inaccuracies listed in
   F-05-R5 in a docs-only change.
4. Do not revert the repoint: the canonical-table reads themselves are verified correct, resolve against a
   real FK, and return values matching the database.

> **The repoint is correct; the change-set is not yet safe to release.** No acceptance verdict is claimed
> beyond the per-area rows above, and no claim is made that any workflow is production-ready
> (AGENTS.md §52, §73, §74, §85).

---

*End of CT-VERIFY-05. Frozen target `dc3d78dc8021bd65978754cf131c38045ff8013d` on `p8-release-reconciled`;
no code, schema, RLS, migration or test was modified in producing this report; nothing was committed,
pushed or deployed; all evidence was gathered from disposable infrastructure under `/tmp/ctv05`.*







