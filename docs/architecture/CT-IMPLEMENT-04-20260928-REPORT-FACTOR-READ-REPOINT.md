# CT-IMPLEMENT-04 — Legacy factor-read repoint onto the canonical `emission_factors` table

**Date:** 2026-09-28
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**HEAD:** `dc3d78dc8021bd65978754cf131c38045ff8013d` — unchanged by this task (nothing committed, pushed or deployed)
**Source findings:** CT-SCHEMA-03 §15/§19 **F-05** (legacy factor reads on `emissions_logs` embeds) and **F-09** (legacy frontend factor embeds)

> Scope note: `/home/shomonrobie/carbon_tally` is a **different working tree** at a different
> commit (`20b7a928…`). All measurements in this report are taken from the pinned target
> above only; no conclusion here should be applied to the other tree without re-measuring.

---

## 1. Task

Repoint every read of the **retired** legacy factor table `defra_conversion_factors` onto the
**canonical** `emission_factors` table, for all sites that are **not** gated on an unratified
Product-Owner decision, and extend the CT-IMPLEMENT-01 regression guard so the repoint cannot
silently regress.

Explicit non-goals (unchanged by this task):

* no change to factor **selection** or precedence (`backend/utils/emissions.py`);
* no change to PD-gated surfaces (PD-3 / PD-4 / PD-5);
* no database, schema, migration, RLS or storage change; no write to any live/demo data;
* no commit, no push, no deploy.

## 2. Why a repoint is the correct fix

* `backend/utils/emissions.py` (CT-IMPLEMENT-01 §6.5) is the canonical resolver chain:
  **approved customer factor → `emission_factors` (joined via `factor_aliases`) → controlled
  "unresolved"**. The table it resolves against is `emission_factors`.
* `emissions_logs.emission_factor_id` has a foreign key to `emission_factors(id)`. PostgREST
  resolves embedded resources through that FK graph, so
  `emissions_logs?select=*,emission_factors(...)` is a **valid** embed while
  `…,defra_conversion_factors(...)` is a **structurally invalid** one — there is no FK to a
  table of that name. That is the mechanism behind the silently-broken reporting/dashboard/
  export features recorded as F-05 and F-08.
* The canonical rebuild contains **no** table of the legacy name; the repository asserts its
  absence deliberately in `e2e/environment/scripts/canonical_schema_verify.py`.
* The legacy name must therefore be *removed* from live code, never reintroduced (no rename
  of the canonical table, no re-creation of the legacy table).

## 3. Changes (20 occurrences across 7 files)

### 3.1 `backend/report_generator.py` (3 occurrences)

* `:595` embed `defra_conversion_factors(activity_type, co2e_multiplier, reporting_year)` → `emission_factors(...)`.
* `:618-625` `defra = record.get('defra_conversion_factors', {}) or {}` → `factor_row = record.get('emission_factors', {}) or {}`
  (with a comment naming `emissions_logs.emission_factor_id` as the provenance edge); the Scope-1/2/3
  fallback classification now reads `factor_row.get('activity_type', '')`.
* `:764-766` activity grouping now reads `record.get('emission_factors') or {}`.

### 3.2 `backend/routes/emissions.py` (embed + key mapping)

* `:153` embed `defra_conversion_factors (id, activity_type, co2e_multiplier, …)` → `emission_factors (…)`.
* `:199` `defra = record.get('defra_conversion_factors', {})` → `factor_row = record.get('emission_factors') or {}`.
* **Response keys are intentionally unchanged**: `defra_factor_id`, `activity_type`,
  `co2e_multiplier` (and the rest of the emissions payload) keep their existing JSON names —
  they are part of the published API contract consumed by the frontend, and renaming them is a
  separate, PO-visible API-versioning decision. Only the *source table* changed.

### 3.3 `backend/routes/organizations/data.py` (5 occurrences)

* `:142` embed in `get_organization_emissions` → `emission_factors (activity_type, co2e_multiplier, reporting_year)`.
* `:168` `record.get('defra_conversion_factors', {})` → `factor_row = record.get('emission_factors') or {}`;
  `:179` `activity_type` now read from `factor_row`.
* `:230` embed in `export_emissions_csv` → `emission_factors (...)`.
* `:248,251,252` CSV columns `Activity Type` / `Reporting Year` / `Multiplier` now read
  `(record.get('emission_factors') or {})`.
* `:392` `supabase.from_('defra_conversion_factors')` → `supabase.from_('emission_factors')` in
  `get_organization_defra_factors` (an organisation-scoped **catalogue listing**, selected as
  `id, activity_type, co2e_multiplier, reporting_year`; the function's own pre-existing
  organisation authorization check is untouched).

### 3.4 `backend/routes/organizations/dashboard.py` (4 occurrences)

* `:109` and `:203` embeds → `emission_factors (activity_type)`.
* `:124` and `:236` `record.get('defra_conversion_factors', {})` → `(record.get('emission_factors') or {})`.

### 3.5 `backend/routes/organizations/exports.py` (1 occurrence)

* `:56` `assets!left(name, type), defra_conversion_factors!left(activity_type, co2e_multiplier)`
  → `assets!left(name, type), emission_factors!left(activity_type, co2e_multiplier)`.

### 3.6 `frontend/src/App.js` (dead embed removed)

* `:730-734` the unused `defra_conversion_factors (id, activity_type, co2e_multiplier, reporting_year)`
  embed was deleted from the `emissions_logs` select inside `Dashboard()`. The surrounding query and
  every consumer of the row are unchanged.

### 3.7 `frontend/App_.js` (legacy fallback removed)

* `:1068-1069` `row.defra_conversion_factors?.activity_type` / `?.co2e_multiplier` fallbacks removed;
  the remaining sources are `row.metadata?.fuel_type` and `row.metadata?.defra_factor_used`. This file is
  a pre-V3 legacy bundle; the edit removes the only reference to the retired table from it.

## 4. API-contract and behaviour preservation

* **Response keys are not renamed.** `backend/routes/emissions.py` still returns
  `defra_factor_id`, `activity_type` and `co2e_multiplier` as JSON keys, now sourced from the
  canonical factor row. Renaming them would be an externally visible API change and is not part
  of this remediation.
* **No request/response schema changed.** `routes/organizations/data.py`'s
  `get_organization_defra_factors` keeps its path, its pre-existing organisation authorization
  check, its `reporting_year` filter and its projection; only the `from_()` table name changed.
* **No new factor selection.** Every repointed read is either (a) the factor already recorded
  on the emissions row (`emissions_logs.emission_factor_id`) or (b) a year-filtered catalogue
  listing. Neither path chooses a factor for a calculation, so AGENTS.md §15 precedence
  (approved customer factor → CarbonTally matching → unresolved/manual review) is neither
  weakened nor bypassed, and no silent fallback to a generic factor was introduced (the PD-6
  concern).
* **No error-masking added.** Where an embedded factor row can be absent, the code uses
  `(record.get('emission_factors') or {})` so a missing embed yields the same neutral value the
  legacy code produced for an empty object, instead of raising `AttributeError`.
* **Dead code removed, not repurposed.** The `frontend/src/App.js` embed had no consumer; the
  `frontend/App_.js` fallbacks were string-only display fallbacks, and the row's `metadata`
  fields remain the primary source.

## 5. Residual inventory (measured 2026-09-28 at `dc3d78dc`)

The repoint is complete for **source code**. The retired name still appears in the places below,
each with an explicit reason:

| Surface | Occurrences | Files | Class / reason |
|---|---|---|---|
| `backend/routes/admin/defra.py` | 16 | 1 | **PD-3** / F-06 — the whole admin factor API is gated on a PO decision |
| `backend/routes/reports.py` | 2 | 1 | **PD-3** factor import (`:1290`) + **PD-5** factor catalogue read (`:279`) — F-05 residual |
| `backend/routes/reference.py` | 1 | 1 | documentation comment only (no query) |
| `backend/tests/unit/test_ct_implement_01_remediation.py` | 5 | 1 | the guard itself — 2 docstring mentions + 3 assertions that the name is *absent* |
| `admin/src/pages/admin/DefraFactors.js`, `components/admin/DefraFactorModal.js`, `components/admin/ImportDefraModal.js` | 9 | 3 | **PD-3** / F-07 — Control-Plane factor administration |
| `prisma/schema.prisma` | 7 | 1 | stale schema snapshot (the retired model + 3 relations) — F-13, not a runtime path |
| `seed.ts` | 1 | 1 | dead seed config — F-13 |
| `frontend_backup_pre_v3_public_20260827/` (`src/App.js`, `src/App copy.js`, `App_.js`) | 4 | 3 | pre-V3 backup bundle, neither built nor deployed — F-13 |
| `e2e/environment/scripts/canonical_schema_verify.py` | 1 | 1 | deliberate assertion that the canonical rebuild has **no** such table |
| `frontend/node_modules/.cache` (babel-loader + webpack `.pack`) | 29 | 7 | stale build cache holding **pre-edit** transpiled copies; regenerated by the next build, not source |
| `docs/**` | 82 | 17 | governance history — these documents must remain able to name the retired table |

**`frontend/src/**` and `frontend/App_.js` contain zero occurrences.** The build-cache and backup
surfaces are binary artefacts outside the guard's scan roots by design.

## 6. Regression guard

`backend/tests/unit/test_ct_implement_01_remediation.py` was extended (it already covered the
CT-SCHEMA-03 F-03 canonical resolver):

* `_REPOINTED_FILES` (12 entries) now includes the five CT-IMPLEMENT-04 backend files and the two
  frontend files; `test_no_legacy_factor_table_reference_remains` asserts the retired name is
  **absent** from each (parametrized).
* `_CANONICAL_FACTOR_READ_FILES` (5 entries) + `test_repointed_factor_reads_use_the_canonical_table`
  assert `emission_factors` is **present** — so the guard cannot be satisfied by simply deleting
  the factor lookup.
* `test_legacy_factor_table_references_are_confined_to_decided_files` walks `_LEGACY_SCAN_ROOTS`
  (`backend/**/*.py`, `frontend/src/**/*.{js,jsx}`, `admin/src/**/*.{js,jsx}`), skips
  `_EXCLUDED_DIRS` (`node_modules`, `build`, `dist`, `.venv`, caches, …) and fails on any file
  naming the retired table that is not in `_LEGACY_REFERENCE_ALLOWLIST` (7 entries: PD-3 admin API
  + 3 admin UI files, the two `reports.py`/`reference.py` residuals, and the guard itself). The
  allowlist can only shrink — remediating a listed file makes it stop matching, while a *new*
  reference fails immediately.

```bash
cd /home/shomonrobie/ct_93d5cdd/backend
./.venv/bin/python -m pytest tests/unit/test_ct_implement_01_remediation.py -q
# 34 passed — 13 test functions (34 parametrized cases), exit code 0, no database access
```

## 7. Verification performed

| Check | Result |
|---|---|
| Python AST parse of the 5 edited backend modules | clean |
| Occurrence inventory (§5), measured with a pathlib scan (not a truncated shell pipe) | as tabulated |
| Guard suite (`pytest`, repo venv) | **34 passed** (exit 0; 34 parametrized cases counted from the `-q` progress line, since this local pytest build printed no explicit "N passed" line), 3 pre-existing FastAPI `regex=` deprecation warnings |
| `git status --short` / `git rev-parse HEAD` | 11 tracked files modified by this task + 1 unrelated pre-existing modification (`.gitignore`); HEAD still `dc3d78dc…`; nothing committed or pushed |
| PD-gated files | not touched (verified by diff scope) |

**Not verified:** no live/staging execution, no browser verification and no database write were
performed — the task was read-only against Supabase. The repoint's runtime effect therefore rests
on embed validity against the FK graph (`emission_factor_id → emission_factors`) and the canonical
resolver, not on an observed end-to-end report/dashboard/export run.

## 8. Security and authorization impact

* **No authorization change.** Every edited endpoint keeps its existing authentication and
  organization/role checks; `get_organization_defra_factors` keeps its pre-existing
  "not authorized for this organization" guard. No check was relaxed or removed.
* **No new client-visible data path.** The edited backend code runs with the server-side service
  key (as `utils/emissions.py` and `routes/reference.py` already did); D-4 RLS on
  `emission_factors` stays revoked from `anon`/`authenticated`, so the repoint does not create a
  new reachable-from-the-browser table.
* **No storage/signed-URL involvement**, no secrets, keys or tokens added to code, logs or docs.
* **Tenant isolation preserved:** the embeds are bounded by the same `organization_id` filters as
  before; only the embedded relation name changed.

## 9. Documentation truth-pass

| Document | Change |
|---|---|
| `CT-IMPLEMENT-01-20260927-REPORT.md` §12 (R-1) | status block: 20 occurrences/7 files repointed, 19 remaining in 3 backend files, 9 in `admin/src`, 13 in stale/assertion artefacts, residual table, and the statement that PD-3/PD-4/PD-5 are still unratified |
| `CT-PO-CARBONTALLY-CT-SCHEMA-03-REPORT-20260927.md` | new **§19.1 Remediation status** (F-03 REMEDIATED, F-04/F-05 PARTIAL, F-06/F-07/F-08/F-14/F-13/F-15 OPEN, F-09 REMEDIATED); **§20** PD-1…PD-6 annotated with status; **§21** proposal annotated (steps 3 and 5 executed, step 8 superseded, step 7 PD-5-gated) |
| `CT-PO-CARBONTALLY-CT-IMPLEMENT-02-REPORT-20260928.md` §9 item 4 | R-1 "~37" annotated with the measured residual |
| `CT-PO-CARBONTALLY-CT-IMPLEMENT-03-REPORT-20260928.md` §17 | R-1 row status updated to "partially remediated (CT-IMPLEMENT-04)" |
| `CT-PO-CARBONTALLY-CAPABILITY-AND-RELEASE-LEDGER-20260926.md` (CAP-049) | R-1 truth-pass note added inside the existing cell (column count preserved) |
| `CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md` | **no row change required** — cross-register check recorded in a new §11 explaining why, and that the factor-related rows (`FIEW-005`/`050`/`052`) depend on unapplied migrations |

**Governance caveat (reported, not resolved):** `docs/` currently holds **two divergent PD
registers** — the ledger's PD-1…PD-10 and CT-SCHEMA-03's PD-1…PD-6 — so a bare "PD-N" is
ambiguous. This report always qualifies which register it means (CT-SCHEMA-03 numbering), and it
makes no claim about the ledger's differently-numbered items.

## 10. Not done / remaining

* **PD-3** (admin factor management) is **unratified**: `backend/routes/admin/defra.py` (16) and
  the three `admin/src` files (9) are untouched by design, and the SCM-004 trap assertions (F-14)
  remain in place because they cover exactly those endpoints.
* **PD-5** (manual-entry factor lookup) is **unratified**: `ManualEntryStandalone.jsx:226` still
  calls `${API_URL}/api/defra-factors/${reporting_year}` (F-08) — re-measured this session,
  unchanged. The catalogue route is in fact registered under the **reports** prefix
  (`routes/reports.py:270` → `/api/reports/defra-factors/{year}`, router prefix `/api/reports`,
  `main.py:214`), so the frontend's path is a genuine 404 and not merely a PD-gated endpoint. The
  pre-V3 backup bundle repeats the same wrong path at `frontend/App_.js:366-372`
  (`/api/defra-factors/{year}` with an `/api/defra-factors` fallback); the *live* bundle's call
  site is untouched by this task because it is PD-5-gated.
* **PD-4** (orphan `routes/admin/audit_logs.py`) is **unratified**.
* **F-04 hardening** (a missing factor becoming a *blocking validation* state rather than a
  neutral value) is **not** implemented.
* CT-SCHEMA-03 §21 steps 2, 4, 6, 7, 9 and 10 are untouched.
* Stale artefacts (`prisma/schema.prisma` 7, `seed.ts` 1, the pre-V3 backup bundle 4) remain —
  F-13; and the frontend build cache (`node_modules/.cache`, 29) clears on the next build.

## 11. Git state

* **HEAD unchanged:** `dc3d78dc8021bd65978754cf131c38045ff8013d` on `p8-release-reconciled`.
  Nothing committed, nothing pushed, nothing deployed.
* **Tracked files modified by this task (11):**
  `backend/report_generator.py`, `backend/routes/emissions.py`,
  `backend/routes/organizations/{data,dashboard,exports}.py`,
  `backend/tests/unit/test_ct_implement_01_remediation.py`,
  `frontend/App_.js`, `frontend/src/App.js`,
  `docs/architecture/CT-IMPLEMENT-01-20260927-REPORT.md`,
  `docs/architecture/CT-PO-CARBONTALLY-CT-IMPLEMENT-02-REPORT-20260928.md`,
  `docs/architecture/CT-PO-CARBONTALLY-CT-IMPLEMENT-03-REPORT-20260928.md`.
* **New untracked report:** `docs/architecture/CT-IMPLEMENT-04-20260928-REPORT-FACTOR-READ-REPOINT.md`.
  Note that the CT-SCHEMA-03 report, the capability/release ledger and the FIEW register are
  themselves **untracked** files (as are most of the 2026-09-27/28 governance docs), so the edits
  made to them are uncommitted *and* untracked.
* **Unrelated pre-existing working-tree change (not produced by this task, not reverted):**
  `.gitignore` — the diff rewrites ~110 lines and also contains one genuine insertion
  (`git diff --ignore-cr-at-eol --stat` still reports `1 insertion(+)`), which is consistent with a
  line-ending normalisation plus one added ignore entry. It should be **reviewed before any
  commit**; AGENTS.md §70 forbids discarding unrelated working-tree changes, so it was left as
  found.

## 12. Acceptance language

**IMPLEMENTED and TESTED locally** — the 20 repointed occurrences, the removal of both frontend
embeds, the extended guard (34 passing tests) and the documentation truth-pass are all verified
against the pinned commit as recorded above.

**NOT independently VERIFIED and NOT ACCEPTED.** No live or staging run, no browser/UX
verification, no database or RLS exercise and no independent QA was performed. The PD-3/PD-4/PD-5
surfaces and the F-04 hardening remain open, and the runtime behaviour of the repointed reporting/
dashboard/export paths should be confirmed by the next independent QA pass against a running
environment.
