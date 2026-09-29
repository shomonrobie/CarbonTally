# CT-IMPLEMENT-04 — Independent Verification Brief (frozen handover)

**Date prepared:** 2026-09-28
**Repository (the only tree in scope):** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled` — **HEAD:** `dc3d78dc8021bd65978754cf131c38045ff8013d`
**Prepared by:** implementation agent (Cline). **Scope decision:** the Product Owner has confirmed
CT-IMPLEMENT-04 is complete; **no CT-IMPLEMENT-05 implementation has been started**.
**Implementation report:** `CT-IMPLEMENT-04-20260928-REPORT-FACTOR-READ-REPOINT.md`

> **Status of the artefact under test: IMPLEMENTED + LOCALLY TESTED — NOT INDEPENDENTLY VERIFIED —
> NOT ACCEPTED.**
>
> This brief is a *handover*, not evidence. It tells the independent verifier what to test, how, and
> what a pass looks like. Nothing in it may be cited as verification.

> Scope warning: `/home/shomonrobie/carbon_tally` is a **different working tree** at a different
> commit. Do not mix measurements between the two trees. Every claim here was measured in
> `/home/shomonrobie/ct_93d5cdd` only.

---

## 1. Freeze baseline — verify this FIRST

The worktree was frozen at **2026-09-28T07:29:07Z**. Verify the freeze before testing anything; if
any hash below differs, the run is invalid and must be reported as such rather than tested.

```bash
cd /home/shomonrobie/ct_93d5cdd
git rev-parse HEAD          # expect dc3d78dc8021bd65978754cf131c38045ff8013d
git branch --show-current   # expect p8-release-reconciled
git status --short | grep -v '^??'   # expect exactly 12 modified files (see §1.2)
git --no-pager diff --stat HEAD -- backend frontend
#   8 files changed, 131 insertions(+), 32 deletions(-)
```

### 1.1 SHA-256 of every file this task touched

```bash
cd /home/shomonrobie/ct_93d5cdd
sha256sum -c <<'EOF'
53627ed277b91f27aac5587e6cafa74333bcc79dc14dab492ad477338ad29cd1  backend/report_generator.py
94ba0931ed227ccf33db4bc7d4a0a9f11ba045cbe56ad6a6b7168544af31d370  backend/routes/emissions.py
d537684b5fcbd7fc19513556b1d96024b22a8895a874c2912d29f0e2969c410a  backend/routes/organizations/data.py
80ca6ed3ac281e1b02deb112c2b55065e4a20ac33e25a28243579769607f7fa7  backend/routes/organizations/dashboard.py
ff6b51e068beca0cefde5b9e96e5f70e79d086bf9d3fb2ce73aec4cc79db3c80  backend/routes/organizations/exports.py
27a6e44ad31109e666cb21dee0d701bd585208ff476ae5bdaee276717ad77e07  backend/tests/unit/test_ct_implement_01_remediation.py
2dba8358e74e0e0412a3740536288391ea01054983c93f0d88b2f259b2244a58  frontend/src/App.js
27bb9af5641882e895b327a85f58f642c35a29a755c1b049f989a0b6c6ac75e4  frontend/App_.js
886719105ce8bf634c358e71793e3ba2b1c74de75413e6f2364ea352be15af3a  docs/architecture/CT-IMPLEMENT-04-20260928-REPORT-FACTOR-READ-REPOINT.md
fd8a51511ab618cfe69d26d8af5fb04fe2d06ca042a73d481432a08aaf5bb699  docs/architecture/CT-IMPLEMENT-01-20260927-REPORT.md
EOF
```

Governance documents truth-passed during this task (hashes as of the same freeze):

```bash
cd /home/shomonrobie/ct_93d5cdd
sha256sum -c <<'EOF'
bbbc30c5bdf136d5b2eec75c67f6695508bebc989cbdf7287234daab43a6ef27  docs/architecture/CT-PO-CARBONTALLY-CT-IMPLEMENT-02-REPORT-20260928.md
6b70fe03d7e6de460991f18af6dcbd77e3fd2088e7863fdaaa59470241d85dd8  docs/architecture/CT-PO-CARBONTALLY-CT-IMPLEMENT-03-REPORT-20260928.md
ad9bdc87ce75d6536e1e4c3f62550de51eb7dab266bd08845388635784e1a4b4  docs/architecture/CT-PO-CARBONTALLY-CT-SCHEMA-03-REPORT-20260927.md
7c7b8e6ee8402050910ca72cccbdc26bbcb162094a64bb29d08c6a6f34807a4d  docs/architecture/CT-PO-CARBONTALLY-CAPABILITY-AND-RELEASE-LEDGER-20260926.md
42b41d9422238d1c935fc712ca7cd2f7aaca1d37dcab933cd42fb36eb004d10c  docs/architecture/CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md
EOF
```

### 1.2 Modified tracked files (12)

Eleven were changed by this task (`backend/report_generator.py`, `backend/routes/emissions.py`,
`backend/routes/organizations/{data,dashboard,exports}.py`, the guard test, `frontend/src/App.js`,
`frontend/App_.js`, and the CT-IMPLEMENT-01/02/03 reports). The twelfth, `.gitignore`, is an
**unrelated pre-existing working-tree change** (215-line diffstat, one genuine insertion under
`--ignore-cr-at-eol`) deliberately left untouched per AGENTS.md §70. It is **not** part of
CT-IMPLEMENT-04 and must not be scored as such.

### 1.3 Untracked files

Most 2026-09-27/28 governance documents — including the CT-SCHEMA-03 report, the capability/release
ledger, the FIEW register and this brief — are untracked (`??`); edits to them are therefore
uncommitted **and** untracked. `supabase/` has **zero** modifications.

---

## 2. What was changed — the 20 repoints

Measured from `git diff -U0 HEAD` over the seven source files. This is the count the verifier must
reproduce independently:

```bash
cd /home/shomonrobie/ct_93d5cdd
git --no-pager diff -U0 HEAD -- backend/report_generator.py backend/routes/emissions.py \
  backend/routes/organizations/data.py backend/routes/organizations/dashboard.py \
  backend/routes/organizations/exports.py frontend/src/App.js frontend/App_.js \
  | grep '^-' | grep -o 'defra_conversion_factors' | wc -l      # expect 20
```

**20 occurrences of the retired name were removed, spanning 23 changed locations** — three of those
locations are local-variable renames (`defra` → `factor_row`) whose removed line does not itself
name the table.

| # | File | Line(s) (post-change) | Location | Occurrence → canonical |
|---|---|---|---|---|
| 1 | `backend/report_generator.py` | 594 | report dataset select | embed `defra_conversion_factors(...)` → `emission_factors(...)` |
| 2 | `backend/report_generator.py` | 620–623 | scope classification | `record.get('defra_conversion_factors', {})` → `record.get('emission_factors', {})` (+ comment) |
| 3 | `backend/report_generator.py` | 627 | scope classification | variable rename `defra` → `factor_row` |
| 4 | `backend/report_generator.py` | 766–767 | emission-class loop | `record.get('defra_conversion_factors', {})` → `(record.get('emission_factors') or {})` |
| 5 | `backend/routes/emissions.py` | 152 | `get_emissions_for_organization` embed | → `emission_factors (id, …)` |
| 6 | `backend/routes/emissions.py` | 198 | same | row dict → `factor_row` |
| 7 | `backend/routes/emissions.py` | 212–215 | same, **response keys retained** | `defra_factor_id` / `activity_type` / `co2e_multiplier` / `reporting_year` now read from `factor_row` |
| 8 | `backend/routes/organizations/dashboard.py` | 109 | `get_dashboard_summary` embed | → `emission_factors (activity_type)` |
| 9 | `backend/routes/organizations/dashboard.py` | 124 | same | `'activity_type'` mapping |
| 10 | `backend/routes/organizations/dashboard.py` | 203 | `get_organization_activity` embed | → `emission_factors (activity_type)` |
| 11 | `backend/routes/organizations/dashboard.py` | 236 | same | `'activity_type'` mapping |
| 12 | `backend/routes/organizations/data.py` | 142 | `get_organization_emissions` embed | → `emission_factors (…)` |
| 13 | `backend/routes/organizations/data.py` | 168–169 | same | row dict → `factor_row` (+ comment) |
| 14 | `backend/routes/organizations/data.py` | 179 | same | `'activity_type'` mapping |
| 15 | `backend/routes/organizations/data.py` | 230 | `export_emissions_csv` embed | → `emission_factors (activity_type, co2e_multiplier, reporting_year)` |
| 16 | `backend/routes/organizations/data.py` | 248 | CSV row | `'Activity Type'` |
| 17 | `backend/routes/organizations/data.py` | 253 | CSV row | `'Reporting Year'` |
| 18 | `backend/routes/organizations/data.py` | 254 | CSV row | `'Multiplier'` |
| 19 | `backend/routes/organizations/data.py` | 392 | `get_organization_defra_factors` | `from_('defra_conversion_factors')` → `from_('emission_factors')` |
| 20 | `backend/routes/organizations/exports.py` | 55 | `export_emissions_data` embed | → `emission_factors!left(...)` |
| 21 | `frontend/src/App.js` | 729–736 → deleted | Dashboard select embed | entire legacy embed block removed |
| 22 | `frontend/App_.js` | 1068 | Dashboard column | `row.defra_conversion_factors?.activity_type` fallback removed |
| 23 | `frontend/App_.js` | 1069 | Dashboard column | `row.defra_conversion_factors?.co2e_multiplier` fallback removed |

Rows 1–20 carry the 20 removed occurrences. Rows 3, 7 and 14 are the rename / key-preserving
locations. Verify each row by reading the file at the stated line — **do not** accept this table as
evidence. The per-file distribution to reproduce is: `report_generator.py` 3, `emissions.py` 2,
`data.py` 7, `dashboard.py` 4, `exports.py` 1, `frontend/src/App.js` 1, `frontend/App_.js` 2.

---

## 3. Verification areas

Each area states the objective, a reproducible method, the expected result, and what a failure means.
Run them in order; area 5 is the highest-risk one (it is the only area that can invalidate the
repoint's *runtime* correctness).

### 3.1 All 20 R-1 repoints present and correct

*Objective:* every non-PD-gated legacy factor read now uses the canonical table.
*Method:* the §2 count command; then, for each of the seven files,
`grep -n 'defra_conversion_factors' <file>` and expect **no output**.
*Expected:* count `20`; zero remaining occurrences in all seven files.
*Failure means:* an incomplete repoint (a runtime read still hitting the retired table), or a
mis-stated inventory. Record the exact file and line.

### 3.2 Canonical `emission_factors` usage

*Objective:* the canonical read is equivalent — same columns, same embed semantics, same call sites.
*Method:* diff the pre-change and post-change view of each repointed read side by side; the pre-change
side comes from the object database without touching the frozen worktree:

```bash
mkdir -p /tmp/ct_pre/backend/routes/organizations
cd /home/shomonrobie/ct_93d5cdd
git show HEAD:backend/routes/organizations/data.py        > /tmp/ct_pre/backend/routes/organizations/data.py
git show HEAD:backend/routes/organizations/dashboard.py   > /tmp/ct_pre/backend/routes/organizations/dashboard.py
git show HEAD:backend/routes/organizations/exports.py     > /tmp/ct_pre/backend/routes/organizations/exports.py
git show HEAD:backend/routes/emissions.py                 > /tmp/ct_pre/backend/routes/emissions.py
git show HEAD:backend/report_generator.py                 > /tmp/ct_pre/backend/report_generator.py
diff -u /tmp/ct_pre/backend/routes/organizations/data.py backend/routes/organizations/data.py
```

*Expected:* every hunk is either (a) the legacy table name → `emission_factors`, (b) the local
variable `defra` → `factor_row`, or (c) an added explanatory comment. **No column list may change, no
`.eq()/.select()` semantics may change, no new/removed rows may appear in any projection.**
*Failure means:* a silent behavioural change smuggled in with the rename (e.g. a dropped
`reporting_year`, a dropped `!left` hint, a changed filter).

### 3.3 API response-contract preservation

*Objective:* no client-visible contract change.
*Method:* the response keys are part of the contract and were deliberately retained (§2 row 7). Verify
by inspecting the post-change code at `backend/routes/emissions.py:212–215` and by comparing the
generated OpenAPI schema against the pre-change baseline app:

```bash
cd /home/shomonrobie/ct_93d5cdd/backend
/usr/bin/python3 - <<'PY'
import json, os, sys
sys.path.insert(0, os.getcwd())      # backend/ is the app's import root
import main as m
doc = m.app.openapi()
with open('/tmp/ct_openapi_after.json', 'w') as fh:
    json.dump(doc, fh, sort_keys=True, indent=1)
print('paths:', len(doc.get('paths', {})))          # measured: 606
print('has /api/organizations/{org_id}/dashboard-summary:',
      '/api/organizations/{org_id}/dashboard-summary' in doc.get('paths', {}))
PY
```

Do **not** run this from the repository root — `backend/main.py` uses `from config import Config`
(backend-local imports), so it fails with `ModuleNotFoundError: No module named 'config'` unless the
working directory is `backend/`. Importing the app emits a pre-existing
`Duplicate Operation ID get_required_metadata_fields…` warning; that is not a CT-IMPLEMENT-04
regression.

*Expected:* `defra_factor_id`, `activity_type`, `co2e_multiplier`, `reporting_year` still emitted by
`GET /api/organizations/{org_id}/emissions`; `/api/organizations/{org_id}/defra-factors` still
registered; the OpenAPI document unchanged apart from any pre-existing drift.
*Failure means:* a client breaking change (renamed/removed key) — that is a defect regardless of why
it happened.

### 3.4 Organization authorization and tenant isolation (ALLOW **and** DENY)

*Objective:* the repointed reads did not weaken authorization and still enforce tenant scope.
*Method:* exercise every repointed endpoint as two different organisations, plus a cross-role matrix,
using identities from `tools/seed_investor_demo/DEMO_IDENTITIES.md`. Endpoints in scope, with the
decorator that registers each one — confirm the resolved path against the OpenAPI document from §3.3
(router prefixes matter, and one of them nests an extra segment):

| Endpoint | Source |
|---|---|
| `GET /api/{org_id}/emissions` | `backend/routes/emissions.py:103` (prefix `/api`) |
| `GET /api/organizations/data/{org_id}/emissions-data` | `data.py:88` (prefix `/api/organizations/data`) |
| `GET /api/organizations/data/{org_id}/emissions/export-csv` | `data.py:200` |
| `GET /api/organizations/data/{org_id}/defra-factors` | `data.py:364` |
| `GET /api/organizations/{org_id}/dashboard-summary` | `dashboard.py:14` (prefix `/api/organizations`) |
| `GET /api/organizations/{org_id}/organization-activity` | `dashboard.py:166` |
| exports route | `exports.py:44` `POST` under prefix `/api/organizations/{org_id}/exports` — resolve the exact path from OpenAPI |

Plus the report-generator path (`backend/report_generator.py`, `backend/routes/reports.py`) as used by
the reporting endpoints.

*Expected:* ALLOW for the owning organisation (with real factor values); DENY (403/404, never 200 with
another tenant's rows) for a foreign organisation, for a viewer attempting a write, and for a client
reaching a consultant-only surface. Both ALLOW and DENY must be recorded.
*Failure means:* **any unexpected ALLOW is a serious security finding** (AGENTS.md §45) and stops the
run for that area.

### 3.5 Actual PostgREST FK embed validity — highest risk

*Objective:* the embeds introduced in §2 rows 1, 5, 8, 10, 12, 15, 20 are resolvable by PostgREST
against the canonical schema. A wrong embed name is a **runtime** 400, not a test failure, which is
exactly why this area exists.

*Method (read-only first):*
1. Confirm the FK graph in the **reconstructed canonical schema**: `emissions_logs.emission_factor_id`
   → `emission_factors.id`. Use the canonical verifier rather than eyeballing:
   `python e2e/environment/scripts/canonical_schema_verify.py` (read-only) and/or
   `python e2e/environment/scripts/ct02_verify_db.py`; for a direct check query
   `pg_constraint` / `information_schema` for the FK and confirm the referenced relation's name is
   exactly `emission_factors`.
2. Issue the embed request against a disposable environment:
   `GET {SUPABASE_URL}/rest/v1/emissions_logs?select=id,emission_factor_id,emission_factors(activity_type,co2e_multiplier,reporting_year)&limit=1`.
3. Repeat with the `!left` hint form used by `exports.py` and the aliased projections used by the
   routes.

*Expected:* HTTP 200 with a populated `emission_factors` object (or `null` only where
`emission_factor_id` is null); **never** `PGRST200 / "Could not find a relationship"`.
*Failure means:* the repoint is runtime-broken for that route — a defect, to be reported, not fixed
here. Note whether RLS (rather than the schema) caused an empty result; those are different findings.

### 3.6 Reporting, dashboard and export runtime behaviour

*Objective:* the repointed reads still return **real factor values**, not blanks.
*Method:* for one organisation with known calculated emissions, exercise and capture:
- the sustainability report generator (`backend/report_generator.py`, the §2 rows 1–4 path);
- dashboard summary and organisation activity;
- the emissions CSV export and the organisation export (`data.py:230+`, `exports.py`).

Assert the exported/report output contains the expected `activity_type`, `co2e_multiplier` and
`reporting_year` for a known row — i.e. compare to the values in `emission_factors` for that
`emission_factor_id` in the database.
*Expected:* non-empty values matching the canonical factor row; no `None`/`''`/"N/A" regressions that
were not present before the repoint.
*Failure means:* the embed resolved but the **key path** is wrong (e.g. the JSON key changed), or a
report now silently emits blank factor data — a data-integrity defect. Remember AGENTS.md §74: a CSV
that downloads is not proof that the emissions are correct.

### 3.7 Frontend behaviour

*Objective:* the two frontend embed removals did not break the Dashboard.
*Method:* the frontend no longer requests the legacy table anywhere (`frontend/src/App.js` and
`frontend/App_.js` are clean). Load the authenticated Dashboard for an organisation with calculated
emissions and inspect: fuel-type column, factor column, console errors, network requests.
*Expected:* the Dashboard renders from `row.metadata.*` (`fuel_type`, `defra_factor_used`) without
console errors and without requesting the retired table; where metadata is absent the cell degrades to
`N/A` rather than throwing.
*Failure means:* a UI regression, or a frontend request that still targets the retired table (would
indicate an embed the frontend removal missed, e.g. in a bundle not covered by the guard — see §6).
Note: the `defra-factors` dashboard widget path (F-08 in the CT-IMPLEMENT-04 report) is a
**pre-existing, separately-tracked** defect; it is outside this task's scope and must be reported as
its own finding rather than counted against the repoint.

### 3.8 The 34-case regression guard

*Objective:* the guard proves the retired name is confined to the decided files.
*Method:*

```bash
cd /home/shomonrobie/ct_93d5cdd
/usr/bin/python3 -m pytest backend/tests/unit/test_ct_implement_01_remediation.py -q
```

*Expected:* **34 passed**, exit code 0 (measured 2026-09-28 in the frozen tree). The cases include
`_REPOINTED_FILES` (**11** entries), `_CANONICAL_FACTOR_READ_FILES` (5 entries), and
`test_legacy_factor_table_references_are_confined_to_decided_files` with
`_LEGACY_REFERENCE_ALLOWLIST` (7 entries) over `_LEGACY_SCAN_ROOTS`, as measured in the frozen
revision:

```bash
cd /home/shomonrobie/ct_93d5cdd
/usr/bin/python3 -m pytest backend/tests/unit/test_ct_implement_01_remediation.py -q --collect-only | tail -3
#   tests/unit/test_ct_implement_01_remediation.py: 34
```

Note the interpreter: the repository `.venv` has **no pytest** installed; `/usr/bin/python3`
(pytest 9.1.1) is the interpreter that produces the 34-case result. If a verifier uses a different
interpreter, the case count must still be 34.

Case composition to reproduce (arithmetic, `-q --collect-only` + reading the source):
`_REPOINTED_FILES` = **11** entries → 11 `test_no_legacy_factor_table_reference_remains` cases;
an inline 4-entry tuple → 4 `test_emissions_logs_writes_use_the_canonical_factor_column` cases;
`_CANONICAL_FACTOR_READ_FILES` = 5 entries → 5 `test_repointed_factor_reads_use_the_canonical_table`
cases; 1 unparametrized
`test_legacy_factor_table_references_are_confined_to_decided_files`; 13 unparametrized tests =
**34**. `_LEGACY_REFERENCE_ALLOWLIST` has 7 entries and `_LEGACY_SCAN_ROOTS` has 5 (root, pattern)
pairs.

> Count discrepancy to record: an earlier internal summary of this task described
> `_REPOINTED_FILES` as having 12 entries. The frozen source has **11**. The frozen report's hash has
> not been altered to match (altering it would invalidate the §1 freeze). Treat the source as
> authoritative and, if the report states 12, record it as a documentation-accuracy finding — do not
> fix it here.

*Negative control (mandatory):* in a **throwaway copy** (`cp -r` to `/tmp` or a scratch worktree — do
not mutate the frozen tree), introduce one legacy reference into a non-allowlisted file and confirm
the guard **fails**; then confirm it passes again in the copy once reverted. A guard that cannot fail
is not evidence. Note the guard's own file legitimately contains 5 mentions of the retired name
(string constants/allowlist) — that is intentional, not a residual.
*Failure means:* either the guard is broken, or a residual reference exists in a file that should be
clean.

### 3.9 Absence of the retired name from all non-gated runtime surfaces

*Objective:* the retired name is confined to the decided (PO-gated) surfaces; the residual inventory
in the report matches reality.

*Method:* re-measure independently rather than trusting the report:

```bash
cd /home/shomonrobie/ct_93d5cdd
/usr/bin/python3 - <<'PY'
import pathlib
ROOTS = ["backend", "frontend", "frontend/src", "admin/src", "supabase", "prisma", "e2e", "tools", "docs"]
EXCL = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
        ".mypy_cache", "build", "dist"}
NEEDLE = "defra_conversion_factors"
for root in ROOTS:
    base = pathlib.Path(root)
    if not base.exists():
        continue
    for p in sorted(base.rglob("*")):
        if not p.is_file() or set(p.parts) & EXCL:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        n = text.count(NEEDLE)
        if n:
            print(f"{n:5d}  {p}")
PY
```

*Expected* (measured 2026-09-28; occurrences, not files):

| Surface | Count | Classification expected by the verifier |
|---|---|---|
| `backend/routes/admin/defra.py` | 16 | PD-3 / F-06 — **gated**, not a residual defect |
| `backend/routes/reports.py` | 2 (`:279` PD-5, `:1290` PD-3) | **gated** |
| `backend/routes/reference.py` | 1 | documentation comment only |
| `backend/tests/unit/test_ct_implement_01_remediation.py` | 5 | the guard itself — intentional |
| `admin/src/**` (3 files) | 9 | PD-3 / F-07 — **gated** |
| `prisma/schema.prisma` | 7 | legacy model retained; no runtime read |
| `prisma/seed.ts` | 1 | legacy seed data |
| pre-V3 backup bundle | 4 | not live code |
| `e2e/environment/scripts/canonical_schema_verify.py` | 1 | verification helper naming the legacy table |
| `frontend/node_modules/.cache` | 29 | build cache |
| `docs/**` | 82 | documentation |

*Expected conclusion:* **zero** occurrences in the 11 `_REPOINTED_FILES` and zero in any live-code file
outside the 7-entry allowlist.
*Failure means:* a live surface still reads the retired table. Any occurrence in a **new** live-code
file is a finding; an occurrence in an allowlisted file is by design. If the counts drift, record the
delta — do not adjust the guard.

### 3.10 Preservation of the canonical 92-migration schema

*Objective:* this task changed **no** schema and no migration.
*Method:*

```bash
cd /home/shomonrobie/ct_93d5cdd
ls -1 supabase/migrations/*.sql | wc -l     # expect 92
git status --short supabase/                # expect empty
git --no-pager diff --stat HEAD -- supabase/   # expect empty
git --no-pager log --oneline -1 -- supabase/   # last migration commit is pre-task
```

*Expected:* 92 migration files, no modification, no addition, no rename, no deletion; the canonical
schema is still reproducible by `e2e/environment/scripts/canonical_schema_rebuild.sh` and verifiable
read-only by `e2e/environment/scripts/canonical_schema_verify.py`.
*Failure means:* a schema change slipped in — a serious defect (AGENTS.md §66).

---

## 4. Safety constraints the verifier must honour

1. **F-046-1 (test-harness target safety).** `backend/tests/integration/conftest.py`'s `pool` fixture
   executes `TRUNCATE … RESTART IDENTITY CASCADE`. Never point `INTEGRATION_DATABASE_URL` at a
   persistent environment. Allowed targets: the dedicated test database (`carbontally_test`) or a
   disposable `ct_*` clone. The fixture refuses names matching `qa`/`demo`/`investor`/`prod`/`live`.
2. **Never** touch production, the investor-demo dataset, or the live Supabase project with writes.
   Read-only calls only. No reseeding, no credential changes, no global data modification.
3. **Never** run destructive schema scripts (`canonical_schema_rebuild.sh`, `reset.sh`,
   `teardown.sh`, `apply_migrations.sh`) against anything but a disposable clone.
4. **Do not mutate the frozen tree.** Negative controls (§3.8), mutation probes and any exploration
   must happen in a copy under `/tmp`. `supabase/`, the 12 tracked modifications and the untracked
   governance documents must be exactly as in §1 when the run ends.
5. **Never** commit, push, force-push, rebase, reset, or deploy. No secrets, tokens, JWTs or signed
   URLs in evidence; redact organisation-identifying data in screenshots where it is not needed.
6. Keep evidence per AGENTS.md §53: role, organisation, route, URL, viewport, screenshot, console,
   network, API request/response, database evidence, Git SHA, timestamp.

---

## 5. Defect handling — do not fix anything

If any area fails, the verifier's output is a **finding**, not a patch:

- record the area, the exact command, the observed output, the expected result, the affected
  route/workflow/role, severity, and a minimal reproduction;
- state clearly whether the defect is *introduced* by CT-IMPLEMENT-04 or *pre-existing* (compare
  against the `git show HEAD:<path>` baseline described in §3.2);
- any defect is to be handled as a **separate implementation task** (e.g. `CT-IMPLEMENT-05`), with its
  own scope, tests and report;
- **do not** edit code, schema, RLS, tests or the frozen report to make a check pass. A green run
  achieved by modifying the artefact under test is void;
- every unexpected ALLOW is a serious security finding (AGENTS.md §45).

If a check cannot be executed (missing environment, unavailable database, no disposable target), mark
it **BLOCKED** with the reason — never **PASS**, never silently SKIPPED.

---

## 6. Limitations, known gaps and claims that must not be made

### 6.1 What is *not* verified by the implementation work

- No live runtime, browser, database, RLS or PostgREST verification was performed by the
  implementation agent. The repoint was **locally tested** (source-level guard) only.
- The runtime correctness of the repoint rests on two things this brief asks the verifier to prove:
  the embed actually resolving (§3.5) and the response keys being consumed unchanged (§3.3).
- Do not report "no residual references in the codebase" — the residual inventory in §3.9 is real and
  intentional. The correct claim is "no residual references outside the decided, PO-gated surfaces".
- Do not report "accepted" or "investor ready" from any of these checks (AGENTS.md §73, §85).

### 6.2 Documentation-accuracy discrepancies in the frozen report (record, do not fix)

Reading `CT-IMPLEMENT-04-20260928-REPORT-FACTOR-READ-REPOINT.md` against the frozen source reveals
three statements that do not match the artefact:

| Report line | Report says | Frozen source says |
|---|---|---|
| 148 | `_REPOINTED_FILES` (12 entries) | **11** entries (4 pre-existing + 5 CT-IMPLEMENT-04 backend + 2 frontend) |
| 165 | "13 test functions (34 parametrized cases)" | 13 **unparametrized** tests **+ 21 parametrized** cases = 34 |
| 174 | guard ran in the "repo venv" | the repository `.venv` has **no pytest**; `/usr/bin/python3` (pytest 9.1.1) was used |

The implementation and the guard are correct; the report's wording is not. Because the report was
frozen before this brief, its hash was **not** altered — correcting it would invalidate §1. These are
documentation findings for a separate task, not defects in the repoint.

### 6.3 Guard scope — what the guard does and does not cover

`_LEGACY_SCAN_ROOTS` covers `backend/**/*.py`, `frontend/src/**/*.{js,jsx}` and
`admin/src/**/*.{js,jsx}`. It does **not** walk `frontend/*.js` bundles, `prisma/`, `e2e/`, `docs/`,
or the pre-V3 backup bundle. The two frontend bundle/SDK files touched by this task
(`frontend/src/App.js`, `frontend/App_.js`) are covered by the explicit
`test_no_legacy_factor_table_reference_remains` case instead. A verifier finding the retired name in a
live file **outside** those roots (e.g. another bundle) is a genuine finding, not a guard regression.

### 6.4 Pre-existing issues that are *out of scope* here

- **F-08** — the Dashboard widget calls `/api/defra-factors/{year}` while the route is registered as
  `@router.get("/defra-factors/{reporting_year}")` at `backend/routes/reports.py:270` under the
  `/api/reports` prefix (`backend/routes/reports.py:53`, mounted at `backend/main.py:214`) — i.e. the
  real path is `/api/reports/defra-factors/{year}`, so the frontend's call is a genuine 404 on the
  current build; the pre-V3 backup bundle repeats the wrong path (`frontend/App_.js:366–372`).
  Pre-existing and separately tracked; **not** a CT-IMPLEMENT-04 defect.
- **Two divergent PD registers** exist (a ledger numbered PD-1…PD-10 and a CT-SCHEMA-03 register
  numbered PD-1…PD-6). Every PD reference in the CT-IMPLEMENT-04 report is qualified with
  "(CT-SCHEMA-03 numbering)". A verifier citing PD numbers must state which register.
- **Open, unratified:** PD-3, PD-4, PD-5 (and PD-7 / F-04 hardening) remain unratified; the
  PD-gated surfaces must keep naming the retired table until a PO decision lands.
- The `.gitignore` modification in the worktree predates this task and is unrelated (§1.2).

---

## 7. Verdict template

Record one row per area. Allowed values: **PASS**, **FAIL**, **SKIPPED**, **BLOCKED**, **UNVERIFIED**
(AGENTS.md §52). Do not compress areas, and do not record an overall verdict that is stronger than its
rows.

| # | Area | Verdict | Evidence reference |
|---|---|---|---|
| 1 | 20 repoints present and correct | | |
| 2 | Canonical `emission_factors` usage (projection parity) | | |
| 3 | API response-contract preservation | | |
| 4 | Organization authorization / tenant isolation (ALLOW + DENY) | | |
| 5 | PostgREST FK embed validity | | |
| 6 | Reporting / dashboard / export runtime behaviour | | |
| 7 | Frontend behaviour | | |
| 8 | 34-case regression guard (+ negative control) | | |
| 9 | Retired name absent from non-gated runtime surfaces | | |
| 10 | Canonical 92-migration schema preserved | | |
| — | Freeze baseline integrity (§1) | | |

Overall verdict must be expressed in AGENTS.md §73 language — e.g. "implemented, independently
verified for areas 1–4 and 8–10, area 5 BLOCKED (no disposable PostgREST target)". "The checks ran" is
not acceptance (§52).

---

*End of brief. Prepared against HEAD `dc3d78dc8021bd65978754cf131c38045ff8013d` at
2026-09-28T07:29:07Z; this file was created after the freeze and is therefore itself not covered by
the §1 hash list. No code, schema, RLS or migration was modified in producing it.*
