# CT-PO — CarbonTally CT-SCHEMA-03 Report

## Legacy code↔schema reference classification and canonical replacement mapping (SCM-004 … SCM-007)

**Task ID:** `CT-SCHEMA-03-20260927-LEGACY-TABLE-REFERENCE-CLASSIFICATION`
**Type:** READ-ONLY deep-dive audit. **No** source, migration, database, seed, deployment or Git mutation was performed.
**Authority (verified this session):** `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`, branch `p8-release-reconciled`
(the requested `/home/shomonrobie/carbon_tally` is a second checkout of the same repository; both were inspected, `ct_93d5cdd` being the authority for the SCHEMA-01/02/03 series)
**Canonical reference schema:** `CT-SCHEMA-01-TARGET-A` disposable rebuild (89/89 canonical migrations applied) per
`CT-PO-CARBONTALLY-CANONICAL-SCHEMA-FROM-ZERO-VERIFICATION-20260927.md`
**Upstream register:** `CT-PO-CARBONTALLY-SCHEMA-CODE-MISMATCH-REGISTER-20260927.md` — SCM-004 … SCM-007 (all graded **S2**, class `CODE_EXPECTS_MISSING_OBJECT`)
**Date:** 2026-09-27

**Verdict:**

```
CT_SCHEMA_03_REFERENCE_CLASSIFICATION_COMPLETE
SCM-004  defra_conversion_factors   → CONFIRMED LIVE-BROKEN (scope materially larger than registered)
SCM-005  report_history             → CONFIRMED LIVE-BROKEN (and NO canonical replacement for the sharing feature)
SCM-006  report_schedules           → CONFIRMED LIVE-BROKEN (and NO canonical replacement table exists at all)
SCM-007  notification_delivery_log  → RECLASSIFIED: UNREACHABLE ORPHAN (latent trap, not a live break)
NEW      canonical chain STRUCTURALLY FORBIDS re-creating SCM-004's table (R1 guard raises and aborts)
```

The four names are **absent** from every probed database, canonical and durable alike (re-confirmed, §3). The question the
SCM-01 register left explicitly open for these four items — *"Determine whether those routes are still registered (U4)"* —
is now answered: **they are.** Three of the four are live, registered, customer/admin-reachable paths that cannot succeed.
The fourth (SCM-007) is not live at all, because its only referencing module is never imported.

---

## 1. Objective and scope

### 1.1 Objective

For each of the four legacy table names:

1. Re-confirm schema absence (canonical + durable environments).
2. Determine the **canonical treatment** of the name inside the 89-file migration chain.
3. Enumerate **every** reference and classify it `LIVE`, `LIVE-BROKEN`, `ORPHAN`, `STALE`, `TEST-ONLY` or `DOCUMENTATION`.
4. Establish the **runtime reachability** of each referencing module (router registration / import graph).
5. Establish the **UI reachability** (customer SPA, admin Control Plane, deployment wiring).
6. Map each legacy name to its **canonical replacement** (or state that none exists).
7. Reconcile against the SCHEMA-01 register and recommend a remediation direction — **without implementing it**.

### 1.2 In scope

`defra_conversion_factors`, `report_history`, `report_schedules`, `notification_delivery_log` — code references, migration
treatment, reachability, replacement mapping, and the deployment surfaces that expose them.

### 1.3 Out of scope (explicitly not investigated)

* SCM-001, SCM-002, SCM-003 (platform/runner/ordering) and SCM-008 … SCM-017.
* Any legacy reference *other than* the four names.
* Any code change, migration, data change or fix. This report ends at *recommendation*.
* Data-level impact quantification (how many documents or logs actually failed) — that requires processing runs against a live stack.

### 1.4 Read-only guarantee

Only read-only operations were used: `git grep`, `git status`, `git rev-parse`, `sed`, `grep`, `ls`, `awk`, and
`information_schema` / `pg_catalog` **SELECT** probes. Nothing outside `/tmp` scratch and this report file was written; no
database row was inserted, updated or deleted; no service was restarted; no migration was applied.

---

## 2. Authority, environment and method

### 2.1 Repository authority

| Field | Value |
|---|---|
| Path | `/home/shomonrobie/ct_93d5cdd` |
| HEAD | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| Branch | `p8-release-reconciled` |
| HEAD commit | `2026-09-26 16:19:11 +0600` — `fix(public-truth): build provenance, admin config gate, security headers, admin branding` |
| Second checkout | `/home/shomonrobie/carbon_tally` (same repository; corroborating evidence only) |
| Working tree | **122 pre-existing changes** (53 deletions, 7 modifications, 62 untracked) — **none authored by this audit** (§2.3) |

### 2.2 Method (five passes)

| Pass | Question | Technique |
|---|---|---|
| 1. Schema | Does the name exist anywhere? | `information_schema.tables` / `columns` probes across every reachable database and docker instance |
| 2. Chain | What does the canonical chain do with the name? | `git grep -F <name> -- supabase/migrations` (89 files), plus reading the R1 guard and verification blocks |
| 3. Inventory | Where is the name referenced? | `git grep -n -F <name>` split by tree (backend / admin / frontend / prisma / seed / docs / non-canonical artefacts) |
| 4. Reachability | Can that reference execute? | Static import graph + the `include_router` registration list in `backend/main.py`, plus deployment build wiring (`package.json`, `frontend/vercel.json`, `admin/package.json`) |
| 5. Mapping | What should the code use instead? | Canonical `CREATE TABLE` census of the 89-migration chain plus the already-remediated precedent (`backend/routes/reference.py`) |

Reachability was established **statically** (import + registration graph). No HTTP request was issued to any endpoint during
this audit; the runtime consequence of each broken path is therefore *inferred* from PostgREST semantics (unknown table →
`PGRST205`; unknown embedded relation → `PGRST200`) combined with the proven absence of the tables. That distinction is
carried through §21 and §23 and is not glossed over.

### 2.3 Pre-existing working-tree changes (not caused by this audit)

`git status --porcelain` = 122 entries:

| Change | Count | Nature |
|---|---|---|
| `??` untracked | 62 | audit/report markdown under `docs/architecture/`, imported chat histories, `.costrict/`, scratch dirs |
| `D` deleted | 53 | the **stale duplicate migration chain** under `e2e/environment/supabase/migrations/` (incl. `00000000000000_init_schema.sql` … `20260806000000_rc2_verification.sql`) |
| `M` modified | 7 | `.gitignore`, `e2e/environment/{README.md,scripts/*.sh,supabase/config.toml}`, `supabase/migrations/20260823000000_d32_private_documents_storage.sql` |

Recorded because (a) the e2e duplicate chain is itself one of the stale-copy findings (§16), and (b) a future reader must not
attribute these to CT-SCHEMA-03. **They were not modified, staged, reverted or committed by this audit.**

---

## 3. Schema absence — re-confirmed this session

Every probe below was catalog-level (`information_schema.tables`, plus `columns`/index checks where relevant). No data rows
were read or written.

| Environment | `defra_conversion_factors` | `report_history` | `report_schedules` | `notification_delivery_log` | Canonical counterparts present |
|---|---|---|---|---|---|
| `CT-SCHEMA-01-TARGET-A` disposable rebuild (canonical 89/89) | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | `emission_factors`, `report_versions`, `notification_delivery`, `notifications` |
| Main stack `carbontally_demo_local` (investor demo) | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | idem |
| Main stack `flagship` | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | idem |
| Main stack QA/test databases probed (`carbontally_test`, `ct_local_93d5cdd`, phase-8 QA) | **ABSENT** | **ABSENT** | **ABSENT** | **ABSENT** | idem |
| Docker instances probed (72 database instances, incl. the `ct_schema01_pg` / `ct_schema02_pg` disposable clusters) | **ABSENT in all** | **ABSENT in all** | **ABSENT in all** | **ABSENT in all** | idem |

Aggregate result: `legacy_objects = 0` for all four names in **every** environment reached, while `emission_factors`,
`report_versions` and `notification_delivery` returned present in the same query. **The mismatch is therefore not deployment
drift — the objects exist nowhere, in any environment, by design of the canonical chain (§5).**

Caveat: Supabase Cloud (production) was **not** probed — no credentials or authority were used. Given that the canonical
chain renames the factor table away at baseline and asserts its absence (§5/§6), production is expected to match, but this
was not independently verified and is listed in §22 as an unknown.


---

## 4. The four names — pre-V3 origin and purpose

| Legacy name | Pre-V3 purpose | Historical DDL that created it (non-canonical) | Canonical successor |
|---|---|---|---|
| `defra_conversion_factors` | The DEFRA conversion-factor table of the pre-V3 factor model — keyed on `activity_type` + `reporting_year`, carrying `co2e_multiplier`, and referenced as `emissions_logs.defra_factor_id` | `database/rc1/001_rc1_schema.sql`; `docs/Final_Kimi/.../001_rc1_schema.sql`; `docs/architecture/DB_Migration/*` | `emission_factors` (+ `factor_aliases` for activity-type resolution, and the factor-set/version model) |
| `notification_delivery_log` | Per-delivery audit log of notification sends (channel, status, error message) | pre-RC2 baseline; still present in `supabase/snippets/Untitled query 303.sql`-era artefacts and `prisma/schema.prisma` introspection | `notification_delivery` (+ `notifications`); `email_logs` for the email channel |
| `report_history` | A report-instance ledger doubling as the **share register** (shares stored in `metadata.shares`) | created only by `docs/architecture/DB_Migration/MIGRATION_007_REPORTING_COMPLIANCE.sql` (a documentation artefact, not a canonical migration; the file itself carries a commented-out `DROP`) | `report_versions` (+ `report_version_artifacts`, `report_generation_queue`, `report_comments`) — **but there is no canonical share register** (§18.2) |
| `report_schedules` | Scheduled/periodic report delivery configuration | created only by `docs/architecture/DB_Migration/MIGRATION_007_REPORTING_COMPLIANCE.sql` | **none — no canonical table of any name (`report_schedule*`, `report_jobs`, `scheduled_reports`) exists in the 89-migration chain** (§18.3) |

The two reporting names were never part of the canonical chain; the other two were *renamed away*. All four share the same
failure mode: code written against the pre-V3 (or documentation-only) schema, committed on `2026-08-27` in
`077c866` (*"feat: finalize v3 ux and promote public website"*) and never revisited after the canonical rename/rebuild.

---

## 5. Migration-chain treatment (89 canonical migrations)

| Legacy name | Occurs in canonical `supabase/migrations`? | Canonical treatment | Evidence |
|---|---|---|---|
| `defra_conversion_factors` | **Yes — assertions only (3 hits, 2 files)** | R1 guard: **raises `EXCEPTION` and aborts** if the table exists; then requires `emission_factors` to exist; emits `NOTICE 'R1 ok: emission_factors present, defra_conversion_factors absent'`. Verification migration re-asserts count = 0 and prints `'% legacy defra_conversion_factors tables (expect 0)'` | `supabase/migrations/20260800000000_rc2_schema.sql:20-30`; `supabase/migrations/20260806000000_rc2_verification.sql:49-51, 69-71` |
| `report_history` | **No — 0 occurrences** | nothing (never modelled) | `git grep -F report_history -- supabase/migrations` → 0 |
| `report_schedules` | **No — 0 occurrences** | nothing | `git grep -F report_schedules -- supabase/migrations` → 0 |
| `notification_delivery_log` | **No — 0 occurrences** | nothing (the name exists pre-RC2; the canonical baseline carries `notification_delivery` instead) | `git grep -F notification_delivery_log -- supabase/migrations` → 0 |

The related legacy column renames are also guarded in the same migration, which is the template for how the project retires
pre-V3 factor vocabulary:

* `emissions_logs.defra_factor_id` → renamed to `emission_factor_id` (**only if** the new column is absent — "the baseline
  carries BOTH the legacy `defra_factor_id` (plain UUID, no FK) AND the authoritative `emission_factor_id` (FK to
  `emission_factors`)");
* `document_processing_queue.defra_factor_used`, `manual_extraction_items.defra_factor_used`,
  `organizations.default_defra_version`, `emission_factors.region` → asserted **absent** by
  `20260806000000_rc2_verification.sql:53-60`.

---

## 6. The structural blocker — the canonical chain forbids the obvious remediation (F-01)

The SCHEMA-01 register offered two options: *"If live → **add the table by migration** or repoint to `emission_factors`"*.
**Option A is not available.** The chain actively refuses it:

```sql
-- supabase/migrations/20260800000000_rc2_schema.sql  (R1 guard)
IF EXISTS (SELECT 1 FROM information_schema.tables
           WHERE table_schema='public' AND table_name='defra_conversion_factors') THEN
    RAISE EXCEPTION 'R1: legacy defra_conversion_factors still present; aborting (baseline should already be renamed)';
END IF;
```

Consequences, in order of importance:

1. **Any migration that re-creates `defra_conversion_factors` would permanently break the canonical chain** — the next
   from-zero rebuild would abort at migration *RC2-schema* with `R1`. The canonicity of the 89/89 rebuild would be destroyed
   as a side effect of "fixing" a route.
2. The intended direction is therefore unambiguous and now effectively **forced by the schema itself**: repoint the code to
   `emission_factors` (or delete the code). Recreating legacy objects is excluded by the chain's own conformance contract.
3. This raises the stakes on SCM-004: it is not "a missing table", it is **code that contradicts the ratified schema
   version**. The same reasoning applies to SCM-007 (`notification_delivery_log` vs canonical `notification_delivery`), though
   that name is not guarded (F-12).

---

## 7. Reference inventory (definitive, excluding `node_modules` and lock files)

Source: `git grep -n -F <name>` on HEAD `cb70fd6`, aggregated per tree.

| Tree | `defra_conversion_factors` | `report_history` | `report_schedules` | `notification_delivery_log` |
|---|---|---|---|---|
| `backend/` (Python) | **12 files / 42 hits** | **1 file / 3 hits** | **1 file / 5 hits** (4 table refs + 1 handler-name false positive, §10) | **1 file / 1 hit** |
| `admin/src/` (Control Plane SPA) | 3 files / 9 hits | 0 | 0 | 0 |
| `frontend/src/` (customer SPA) | 1 file / 1 hit | 0 | 0 | 0 |
| `frontend/` legacy copies (`App_.js`, `App copy.js`, backup tree) | 5 hits | 0 | 0 | 0 |
| `prisma/schema.prisma` | 4 | 0 | 0 | 2 (model + relation) |
| `seed.ts` | 1 | 0 | 0 | 0 |
| **canonical** `supabase/migrations/` | 6 hits / 2 files — **assertions only** | 0 | 0 | 0 |
| `e2e/environment/supabase/migrations/` (stale duplicate chain) | 6 hits / 2 files | 0 | 0 | 0 |
| `database/rc1|rc2/` (non-canonical artefact collection) | 9 | 0 | 0 | 0 |
| `supabase/snippets/` (scratch) | 2 | 0 | 0 | 0 |
| `docs/` (all trees incl. `.md` and copied SQL) | 217 | 6 | 4 | 51 |
| tests | 0 direct name references (2 *endpoint* assertions instead — §17) | 0 | 0 | 0 |

Two facts stand out:

* For `report_history`, `report_schedules` and `notification_delivery_log`, **the entire code footprint is one Python file
  each** (`backend/routes/reports.py` twice, `backend/routes/admin/audit_logs.py` once). The blast radius is precisely
  bounded — these three are *small, surgical* remediations.
* For `defra_conversion_factors` the footprint is **25 tracked code files** (12 backend + 3 admin + 1 frontend + 4 legacy
  frontend + 4 prisma/seed) — an order of magnitude larger, spanning the factor-matching core, six customer data routes,
  report generation, the admin factor-management API and the admin UI.


---

## 8. `defra_conversion_factors` — reference-by-reference classification

**Reachability basis:** every module below is transitively imported from `backend/main.py` and its router **is registered**
(`reports.router` L214, `emissions.router` L226, `documents_main.router` L221, `drafts.router` L224, `defra.router` L233,
`extraction.router` L234 via `routes.admin`, `data.router` L252, `dashboard.router` L254, `exports.router` L258,
`reference.router` L223). `report_generator.py` is nested into the registered `routes/reports.py` router.

| # | Location | Kind | Reachability | Classification | Consequence |
|---|---|---|---|---|---|
| 1 | `backend/utils/emissions.py:58,72,89` | `get_emission_factor()` reads | LIVE — imported by `routes/upload.py`, `routes/admin/extraction.py`, `api/v3_documents.py` | **LIVE-BROKEN (core)** | Factor resolution during upload/extraction/processing cannot succeed → the canonical pipeline's MAP stage has no factor |
| 2 | `backend/report_generator.py:595,621,764` | embedded select + 2 result reads (enhanced report generation) | LIVE — `POST /api/reports/generate-enhanced-report` (L1287) | **LIVE-BROKEN (reporting)** | Generated report cannot embed factor provenance |
| 3 | `backend/routes/emissions.py:153,199` | embedded select + result read | LIVE — `GET /api/emissions/{org_id}` | **LIVE-BROKEN** | Emissions list 500s |
| 4 | `backend/routes/reports.py:280` | read in `GET /api/reports/defra-factors/{reporting_year}` (L271) | LIVE — and asserted `200` by tests (§17) | **LIVE-BROKEN** | Factor-by-year endpoint 500s |
| 5 | `backend/routes/reports.py:1265` | upsert in `POST /api/reports/admin/import-defra-factors` (L1238) | LIVE | **LIVE-BROKEN (admin)** | The only factor-import path under `/api/reports` cannot import anything |
| 6 | `backend/routes/organizations/data.py:142,168,229,247,252,253,391` | 2 embeds + 4 result reads + `GET /{org_id}/defra-factors` (L363) | LIVE | **LIVE-BROKEN (customer data + export)** | Customer data view, export column population and the org-level factor endpoint all fail |
| 7 | `backend/routes/organizations/dashboard.py:109,124,203,236` | 2 embeds + 2 result reads | LIVE | **LIVE-BROKEN (customer dashboard)** | Dashboard activity-type column cannot resolve |
| 8 | `backend/routes/organizations/exports.py:56` | embedded select | LIVE | **LIVE-BROKEN (export)** | Customer export fails |
| 9 | `backend/routes/documents_main.py:517` | factor lookup inside the `approve` branch of document review | LIVE (`documents_main.router` L221) | **LIVE-BROKEN (review/approval)** | Inside the route's `try` block: the lookup cannot return a factor id, so approval continues with `defra_factor_id = None` → emissions recorded **without the factor provenance link** |
| 10 | `backend/routes/drafts.py:406` | factor lookup in the manual-extraction/draft flow | LIVE (`drafts.router` L224) | **LIVE-BROKEN (manual processing)** | Same provenance hole as #9 |
| 11 | `backend/routes/admin/extraction.py:190` | factor lookup in admin extraction | LIVE (`extraction.router` L234) | **LIVE-BROKEN (admin processing)** | Admin extraction cannot attach a factor |
| 12 | `backend/routes/admin/defra.py` — **16 reads across 9 routes** (`:115,129,156,165,211,254,268,319,331,378,410,425,467,492,550,585`) | the entire admin DEFRA factor-management API (`/api/admin/defra/*`) | LIVE | **LIVE-BROKEN (admin API, total)** | List, get, create, update, delete, bulk-create, import, versions and validation all fail |
| 13 | `backend/routes/reference.py:61` | **comment only** | LIVE | **REMEDIATED (precedent)** | Already repointed to canonical factors (CL-15 / CAL-3) — the template for remediation |
| 14 | `admin/src/pages/admin/DefraFactors.js:39,81,95`; `admin/src/components/admin/DefraFactorModal.js:52,68,79`; `admin/src/components/admin/ImportDefraModal.js:68,77,85` | 9 **direct PostgREST** reads/writes from the browser | **LIVE** — the admin SPA is built and deployed (§14) | **LIVE-BROKEN (Control Plane UI)** | `/admin` factor-management page and both modals cannot list, save or import factors |
| 15 | `frontend/src/App.js:731` | embedded select in the shipped customer SPA | LIVE | **LIVE-BROKEN (customer UI)** | Customer emissions/logs view cannot render the factor join |
| 16 | `frontend/src/components/ManualEntryStandalone.jsx:226` | `fetch(API_URL + "/api/defra-factors/" + reporting_year)` | LIVE code path, **wrong URL** | **LIVE-BROKEN (double defect — F-08)** | Even after repointing, this 404s: the only registered route is `/api/reports/defra-factors/{year}` (§12.2) |
| 17 | `frontend/App_.js:1069,1070`; `frontend/src/App copy.js`; `frontend_backup_pre_v3_public_20260827/*` | legacy/duplicate bundles | not built | **STALE** | No runtime effect; source-of-truth hazard |
| 18 | `prisma/schema.prisma` (4) + `seed.ts:208` | Prisma relations + dead `PRESERVE_TABLES` entry | **not runtime** (no `@prisma/client` in backend) | **STALE (§15)** | Introspection snapshot of the pre-RC2 schema |
| 19 | `database/rc1|rc2/*`, `supabase/snippets/Untitled query 303.sql`, `docs/**/*.sql` | historical DDL / scratch | none | **STALE ARTEFACTS (§16)** | Includes the original `CREATE TABLE defra_conversion_factors` |
| 20 | `supabase/migrations/20260800000000_rc2_schema.sql:23-30`, `20260806000000_rc2_verification.sql:51,70` (+ the same two files in the `e2e/` duplicate copy) | guards/assertions | chain | **ASSERTS-ABSENT (correct)** | The chain's intent is explicit and enforced |

**Summary for SCM-004:** of 42 backend hits, **41 are live-broken reads** and 1 is a remediated comment; all 9 admin hits are
live-broken; of the frontend hits, 2 are live-broken (one with an additional URL defect) and the remainder are stale copies.
**This is the largest and most business-critical of the four mismatches** — it sits directly on the canonical pipeline's
factor-resolution/MAP stage (AGENTS.md §15, §22, §25) and on the admin Control Plane's factor administration.


---

## 9. `report_history` — reference-by-reference classification

All three references are in one file, all three on **registered** routes of `reports.router` (L214).

| # | Location | Route (registered) | Classification | Consequence |
|---|---|---|---|---|
| 1 | `backend/routes/reports.py:1852` | `POST /api/reports/{report_id}/share` (L1842-1843) | **LIVE-BROKEN** | The share operation reads the report instance from `report_history`; cannot find it → 500 / not-found |
| 2 | `backend/routes/reports.py:1929` | `POST /api/reports/{report_id}/share` (same handler, share-list update) | **LIVE-BROKEN** | Updating `metadata.shares` (the pre-V3 share register held **inside this table**) cannot persist |
| 3 | `backend/routes/reports.py:1969` | `GET /api/reports/shared` (L1961) | **LIVE-BROKEN** | "Reports shared with me" list cannot be produced |

Note also `models`/`response_model`s: the handler pair is typed with `ReportShareResponse`, i.e. sharing was implemented as a
first-class feature of this pre-V3 table, not as an afterthought.

**Canonical replacement:** `report_versions` (+ `report_version_artifacts`, `report_generation_queue`, `report_comments`)
replaces the *report-instance* role of `report_history`. **However, no canonical table of any name
(`report_share*`, `shared_report*`) exists** — the share register has **no canonical equivalent** (§18.2). The sharing
feature therefore cannot simply be "repointed"; it must be either retired or re-modelled. That is a PO decision (§20).

---

## 10. `report_schedules` — reference-by-reference classification

Five hits, all in `backend/routes/reports.py`, on **three registered routes** of `reports.router`.

| # | Location | Route (registered) | Classification | Consequence |
|---|---|---|---|---|
| 1 | `:1372` | `POST /api/reports/schedule` (L1327-1328, `create_report_schedule`) | **LIVE-BROKEN** | Schedule creation fails (the overlap/existence check and the insert both target the missing table) |
| 2 | `:1435` | `GET /api/reports/schedule` (L1428-1429, `get_report_schedules`) | **LIVE-BROKEN** | Schedule list fails |
| 3 | `:1498` | `DELETE /api/reports/schedule/{schedule_id}` (L1489-1490) | **LIVE-BROKEN** | Existence check fails |
| 4 | `:1510` | `DELETE /api/reports/schedule/{schedule_id}` (same handler, update/insert arm) | **LIVE-BROKEN** | Mutation fails |

Seventh/sixth hits belong to the pair above (the handler's own line, plus one further read): the file as a whole contains 5
literal hits — **four true table references** (`:1372`, `:1435`, `:1498`, `:1510`) plus **one false positive** (`:1429`, the
handler's own name `get_report_schedules`, which merely contains the string). Only the four table references are defects.

**Canonical replacement: none.** No `report_schedules`, `report_schedule*`, `scheduled_reports` or `report_jobs` table exists
anywhere in the 89 canonical migrations; the closest canonical object is `report_generation_queue`, which is a *queue* (in
the pipeline sense) and carries no schedule/cron/recipient configuration (§18.3). Scheduled reporting is therefore a
**capability gap**, not a naming mismatch. PO decision required (§20, PD-2).

---

## 11. `notification_delivery_log` — reference-by-reference classification (RECLASSIFIED)

| # | Location | Reachability | Classification | Consequence |
|---|---|---|---|---|
| 1 | `backend/routes/admin/audit_logs.py:404` (route `GET /api/admin/audit-logs/notifications`) | **UNREACHABLE** | **ORPHAN (latent)** | None at runtime — see below |
| 2 | `prisma/schema.prisma:1959` | not runtime | **STALE** | `model notification_delivery_log` coexists in the same schema with `model notification_delivery` |

**Why this is not a live break (and why the register's S2 grading should be revisited):**

* `backend/routes/admin/audit_logs.py` is **55 KB with 12 route declarations**, but it is **never imported and never
  registered**: `backend/main.py` imports `from routes.admin import logs as admin_logs` and registers `admin_logs.router`
  (L242); `backend/routes/admin/__init__.py` does **not** import `audit_logs`; and a repository-wide search found **no**
  dynamic import (`importlib` / `__import__` occur only inside `.venv` third-party packages). The module is also absent from
  `verify_startup.py`'s import checks (which do cover `routes.admin.workload` and `routes.admin.staff`).
* Consequence: the `notification_delivery_log` read at line 404 **cannot execute in the deployed application**. It is a latent
  trap — any future engineer (or agent) who wires the module into the app would import a guaranteed runtime failure, and any
  code search for "notification delivery audit" would be answered by a dead module rather than by `notification_delivery`.
* **Recommended re-grading: SCM-007 from S2 → S3 (`LATENT_DEAD_CODE`)**, on the evidence that its sole consumer is
  unreachable. The class remains `CODE_EXPECTS_MISSING_OBJECT` for the module's own content.

**Canonical replacement:** `notification_delivery` (canonical, created in `00000000000000_init_schema.sql:1429`) with
`notifications` (L1409) as the parent. The orphan module, if ever revived, must be repointed there — and it should be
reviewed as a whole: it is one of the largest unreferenced modules in the backend and its other 11 routes may reference
further non-canonical objects.


---

## 12. Runtime reachability analysis (route / import graph)

### 12.1 The registration chain (`backend/main.py` @ `cb70fd6`)

```
L212 waitlist   L213 upload     L214 reports      L217 legacy_reports  L218 glossary
L219 users      L220 notifications  L221 documents_main  L222 document_activity
L223 reference  L224 drafts      L225 logs         L226 emissions       L227 feedback
L228 drafts_enhanced  L229 customer_documents
L232 staff      L233 defra       L234 extraction   L235 reviews   L236 assignments
L237 permissions  L238 workload  L239 beta         L240 audit     L241 review_history
L242 admin_logs (= routes.admin.logs)  L243 admin_bulk  L244 email_templates
L245 admin_analytics  L246 settings
L249 management L250 members    L251 assets       L252 data       L253 analytics
L254 dashboard  L255 files      L256 team         L257 metadata   L258 exports
L259 org_bulk
```

Every module that references the three *live* legacy names appears in this list:

| Module | Registered as | References |
|---|---|---|
| `routes/reports.py` | L214 | `report_history` (3), `report_schedules` (4), `defra_conversion_factors` (2) |
| `routes/emissions.py` | L226 | `defra_conversion_factors` (2) |
| `routes/documents_main.py` | L221 | `defra_conversion_factors` (1) |
| `routes/drafts.py` | L224 | `defra_conversion_factors` (1) |
| `routes/organizations/data.py` | L252 | `defra_conversion_factors` (7) |
| `routes/organizations/dashboard.py` | L254 | `defra_conversion_factors` (4) |
| `routes/organizations/exports.py` | L258 | `defra_conversion_factors` (1) |
| `routes/admin/defra.py` | L233 | `defra_conversion_factors` (16) |
| `routes/admin/extraction.py` | L234 | `defra_conversion_factors` (1) |
| `utils/emissions.py` (imported by `upload`, `admin/extraction`, `api/v3_documents`) | — | `defra_conversion_factors` (3) |
| `report_generator.py` (nested into `routes/reports.py`) | via L214 | `defra_conversion_factors` (3) |

**Determination (the register's open item U4): the routes are registered and live.** None of the SCM-004/005/006 consumers is
import-dead, feature-flagged, or excluded from the app.

### 12.2 Route surface for the factor endpoints (used by §8 rows 4, 5, 15 and 16)

| Registered path | Source | Notes |
|---|---|---|
| `GET /api/reports/defra-factors/{reporting_year}` | `routes/reports.py:271` (router prefix `/api/reports`) | **the only** `defra-factors/{year}` route in the backend |
| `GET /api/reports/defra-mapping` | `routes/reports.py:243` | mapping helper |
| `POST /api/reports/admin/import-defra-factors` | `routes/reports.py:1238` | bulk import |
| `GET /api/organizations/{org_id}/defra-factors` | `routes/organizations/data.py:363` | org-scoped factor list |
| `GET/POST … /api/admin/defra/*` | `routes/admin/defra.py` | 9 admin routes |
| `GET /api/defra-factors/{year}` | **does not exist** | requested by `frontend/src/components/ManualEntryStandalone.jsx:226` → 404 (F-08) |

### 12.3 The orphan module (SCM-007)

`backend/routes/admin/audit_logs.py` — not imported by `routes/admin/__init__.py`, not registered in `main.py`, not imported
dynamically, not covered by `verify_startup.py`. Its 12 routes (including `GET /api/admin/audit-logs/notifications`, which is
the home of the `notification_delivery_log` read at `:404`) are **not part of the application's contract**. Contrast with
`routes/admin/logs.py`, which *is* registered (L242) — the two are easily confused, which is itself a maintenance hazard.


---

## 13. Customer SPA reachability

| Surface | File | Reachability | Classification |
|---|---|---|---|
| Customer emissions/logs view (factor join) | `frontend/src/App.js:731` | part of the built customer bundle (`frontend/` → `public/` per root build script) | **LIVE-BROKEN** |
| Manual-entry factor lookup | `frontend/src/components/ManualEntryStandalone.jsx:226` | part of the built bundle | **LIVE-BROKEN (plus path defect F-08)** |
| Legacy duplicate bundles | `frontend/App_.js:1069-1070`, `frontend/src/App copy.js`, `frontend_backup_pre_v3_public_20260827/*` | not built | **STALE** |

There is **no** customer-facing UI for `report_history`, `report_schedules` or `notification_delivery_log` (zero hits in
`frontend/src`), so the customer SPA exposes only SCM-004.

---

## 14. Admin Control Plane reachability (SCM-004, admin surface)

The admin SPA is a **separate application** that is nevertheless **built and deployed** as part of the same artefact:

* root `package.json` (monorepo `carbon-ledger-monorepo`) build script:
  `cd frontend && npm install && npm run build && cd ../admin && npm install && npm run build && cd .. && mkdir -p public/admin && cp -r frontend/build/* public/ && cp -r admin/build/* public/admin/`
  → the admin bundle is published at **`/admin`** of the deployed frontend;
* `frontend/vercel.json` rewrites `/admin/*` → `/admin/index.html` (SPA fallback), and `admin/package.json` declares the
  `/admin` homepage — consistent with the build wiring above;
* the admin app talks **directly to Supabase PostgREST** from the browser for factor data (9 calls in 3 files, §8 row 14).

Because the table is absent, `DefraFactors.js` (list/create/update/delete) and both modals
(`DefraFactorModal.js`, `ImportDefraModal.js`) **cannot function**. `DefraFactors.js:192` even names its CSV export
`defra_factors_<date>.csv` — the page is unambiguously the live control-plane surface for SCM-004's vocabulary, and it is
broken end-to-end (list, edit, import, export).

> Scope note: only the four names were traced. Whether other `/admin` pages behave correctly against canonical is outside
> this audit's scope.

---

## 15. Prisma and seed status

| Artefact | Findings |
|---|---|
| `prisma/schema.prisma` | Contains **4** `defra_conversion_factors` references — including the relation `manual_extraction_items.defra_conversion_factors @relation(fields: [defra_factor_used], …)` (L1810). `defra_factor_used` is a legacy column that the canonical chain **asserts must not exist** (`20260806000000_rc2_verification.sql:57`). The file also declares **`model notification_delivery_log` (L1959)** *alongside* `model notification_delivery` (L~1940). Conclusion: it is a **pre-RC2 introspection snapshot**, not a description of canonical. |
| Runtime impact of Prisma | **None directly** — the backend contains **no** `@prisma/client` usage (repository-wide search over non-`.venv` Python returned nothing); the backend uses `supabase-py`. Prisma exists here for tooling/seed generation only. |
| `seed.ts:208` | `'defra_conversion_factors'` appears in `PRESERVE_TABLES`. `PRESERVE_TABLES` is **declared in the interface (L142) and assigned (L199) but never consumed anywhere in the repository** → the entry is **dead configuration** with no runtime effect. |
| `supabase/seed.sql` | Contains **none** of the four names → no seed-level dependency. |
| Risk (forward-looking) | If the Prisma schema is ever re-introspected or used as a generator against canonical, it will produce inserts/columns (`defra_factor_used`, `notification_delivery_log`) that canonical rejects. It is therefore a **source-of-truth hazard** for agents and engineers, and it contradicts the R1 rename semantics. |

---

## 16. Stale copies and non-canonical DDL

| Location | Contents | Status |
|---|---|---|
| `e2e/environment/supabase/migrations/*` (**duplicate of the chain**) | a full second copy incl. `20260800000000_rc2_schema.sql` (R1 guard) and `20260806000000_rc2_verification.sql` | **being deleted in the current working tree (53 `D` entries, §2.3) but not yet committed.** Until committed, the duplicate remains in the index/HEAD and the two SQL files still contain the four-name guard strings. If that chain were ever applied to a *fresh* database it would behave correctly (R1 raises only if the legacy table is present) — but it is a maintenance burden and a second source of truth. |
| `database/rc1/`, `database/rc2/` | historical non-canonical DDL collection: `rc1/001_rc1_schema.sql` contains the original `CREATE TABLE defra_conversion_factors` (6 hits); `rc1/004_rc1_rls.sql`, `rc1/006_rc1_triggers.sql`, `rc1/007_rc1_verification.sql`, `rc2/001_rc2_schema.sql`, `rc2/007_rc2_verification.sql` (9 hits total) | **STALE ARTEFACT** — kept for archaeology; must never be treated as a migration source (AGENTS.md §66/§79) |
| `docs/architecture/DB_Migration/MIGRATION_007_REPORTING_COMPLIANCE.sql` | the file that **created `report_history` and `report_schedules`** (and carries a commented-out `DROP`) | **DOCUMENTATION-ONLY** — the true origin of SCM-005/006: a documentation-folder migration that was never promoted into `supabase/migrations` |
| `docs/Final_Kimi/.../*.sql`, `docs/Final/...` | copied RC1 DDL incl. `defra_conversion_factors` | DOCUMENTATION |
| `supabase/snippets/Untitled query 303.sql` | ad-hoc scratch (2 hits) | SCRATCH — should not be a source of truth |
| `frontend/App_.js`, `frontend/src/App copy.js`, `frontend_backup_pre_v3_public_20260827/` | duplicate bundles | STALE |

**Documentation mention counts** (`git grep -c` under `docs/`): `defra_conversion_factors` **217**, `notification_delivery_log`
**51**, `report_history` **6**, `report_schedules` **4**. These are mentions, not authority — but the asymmetry matters: the
factor name is documented 217 times, which is exactly the kind of volume that makes a stale vocabulary look "real".

---

## 17. Test and CI references

| Location | Content | Classification |
|---|---|---|
| `backend/tests/test_all_endpoints.py:618` | asserts **200** for `GET /api/reports/defra-mapping` | **TEST-TRAP** — asserts success on a path whose backing object does not exist |
| `backend/tests/test_all_endpoints.py:623` | asserts **200** for `GET /api/reports/defra-factors/2024` | **TEST-TRAP** — same; this endpoint's only factor query (`routes/reports.py:280`) reads the missing table |
| All other tests | **no** direct string references to any of the four names (verified repository-wide) | — |

Two consequences:

1. These tests either **do not run** in the current workflow, or they **fail** against a canonical database. Either way, the
   suite is not currently proving SCM-004's behaviour; there is **no test that would have caught** this mismatch, and none
   that will detect its resolution.
2. The remainder of the four names' coverage is *absent*, so any remediation must add tests rather than rely on existing ones.

**Harness safety (carried forward, unchanged):** the integration `pool` fixture truncates its target
(`TRUNCATE … RESTART IDENTITY CASCADE`) and refuses names matching `qa`/`demo`/`investor`/`prod`/`live`
(**F-046-1** invariant, AGENTS.md §55.1). Nothing in this audit executed, pointed at, or modified any harness target.

---

## 18. Canonical replacement mapping

### 18.1 `defra_conversion_factors` → `emission_factors` (+ factor-set / alias model) — **mappable**

| Aspect | Legacy | Canonical |
|---|---|---|
| Table | `defra_conversion_factors` (`activity_type`, `co2e_multiplier`, `reporting_year`) | `emission_factors` — created by the baseline `00000000000000_init_schema.sql`, **renamed from the legacy table by R1**, then extended by later canonical migrations (`…add_emission_factors_import_batch.sql`, factor-set/version model, and the `region` column removal asserted by `rc2_verification`) |
| Aliases | implied by `activity_type` string matching | `factor_aliases` (`…add_factor_aliases.sql`) — the governed mechanism for activity→factor resolution |
| Provenance column | `emissions_logs.defra_factor_id` (plain UUID, no FK) | `emissions_logs.emission_factor_id` (FK → `emission_factors`) — **already present**; the chain renames/asserts it |
| Queue/manual | `document_processing_queue.defra_factor_used`, `manual_extraction_items.defra_factor_used` | canonical equivalents asserted present/absent appropriately by `rc2_verification`; snapshots via `calculation_snapshots` + `emissions_logs` snapshot migrations |
| Precedent | — | **`backend/routes/reference.py:61`** already documents/uses the canonical factor table (CL-15 / CAL-3). This file is the in-repo template for the repointing work |

**Confidence: high** (verified: canonical table exists and its predecessors were renamed by the chain; the FK column
`emission_factor_id` exists; a remediated precedent exists in-repo). **Not verified in this audit:** the exact column
correspondence (`co2e_multiplier` → canonical factor value column) — that requires reading the canonical factor table's
columns before writing the replacement code, which is a remediation-time task, not an audit-time one.

**Architectural caution (important):** the *correct* remediation is **not** a mechanical rename of 41 call sites to a new
table name. AGENTS.md §15 mandates factor **precedence** (approved customer factor → CarbonTally matching → unresolved/manual
review), and §22/§25 require mapping/calculation to be **server-authoritative and provenance-preserving**. The retired
embeds in `report_generator.py`, `organizations/*`, `emissions.py` and `App.js` re-implement factor joins in the client/route
layer; the ratified destination is the V3 factor-matching/calculation path. A rename-only fix would preserve the broken
architecture while removing the error.

### 18.2 `report_history` → `report_versions` (partial) — **sharing has NO canonical replacement**

| Role of `report_history` | Canonical object | Status |
|---|---|---|
| Report instance/version ledger | `report_versions` (+ `report_version_artifacts`, `report_generation_queue`, `report_comments`) | **Replaces it** |
| **Share register** (`metadata.shares`, `GET /shared`, `POST /{id}/share`) | **none** — no `report_share*`/`shared_report*` table exists in the 89 migrations | **GAP — PO decision required** |

### 18.3 `report_schedules` → **NOTHING — capability gap**

No canonical table models report scheduling (no `report_schedules`, `report_schedule*`, `scheduled_reports`, `report_jobs`).
`report_generation_queue` is a pipeline queue, not a schedule store. Options: retire the three endpoints, or add a canonical
scheduling model by migration **plus** a server-side scheduler (AGENTS.md §19: durable, resumable, server-side) — a PO
decision and a feature-sized piece of work, not a rename.

### 18.4 `notification_delivery_log` → `notification_delivery` (+ `notifications`) — **mappable, currently moot**

The canonical pair exists (`notifications` L1409, `notification_delivery` L1429). Because the only consumer is an unreachable
orphan (§11), no runtime remediation is required *unless* the module is revived — in which case repoint to
`notification_delivery`, and review the module's other 11 routes for further non-canonical objects.

---

## 19. Findings register (CT-SCHEMA-03)

Severity scale is inherited from the SCHEMA-01 register (S1 blocking / S2 high / S3 medium / S4 low / INFO). Classification
uses the extended key: `LIVE-BROKEN`, `LIVE-OK`, `ORPHAN`, `STALE`, `TEST-TRAP`, `ASSERTS-ABSENT`, `GAP`.

| ID | Severity | Class | Finding | Evidence | Recommended action |
|---|---|---|---|---|---|
| **F-01** | **S2** | `SCHEMA_CONTRACT` | **The canonical chain structurally forbids the "add the table" remediation for SCM-004.** The R1 guard raises `EXCEPTION` and aborts the chain if `defra_conversion_factors` exists; the verification migration asserts its count is 0 | `20260800000000_rc2_schema.sql:20-30`; `20260806000000_rc2_verification.sql:49-51,69-71` | Ratify *repoint-or-remove* as the only permissible direction; never create the legacy table |
| **F-02** | **S2** | `LIVE_BREAKAGE` | SCM-004 confirmed live: **12 backend modules / 41 live-broken reads** on registered routers (factor resolution, 6 customer data/export routes, reporting, admin API) | §8; `main.py:214,221,224,226,233,234,252,254,258` | Repoint to canonical factor path, or retire per route — PO decision on scope |
| **F-03** | **S2** | `LIVE_BREAKAGE (pipeline)` | `utils/emissions.get_emission_factor()` cannot resolve any factor on live upload/extraction paths → the MAP stage of the canonical pipeline is non-functional wherever this helper is used | `utils/emissions.py:58,72,89`; importers `routes/upload.py`, `routes/admin/extraction.py`, `api/v3_documents.py` | Highest-priority repoint: route factor selection through the V3 factor-matching service with precedence + provenance |
| **F-04** | **S2** | `LIVE_BREAKAGE (provenance)` | Factor lookup inside review/approval and manual-extraction flows fails silently inside `try` blocks, so approvals continue with a null factor reference → emissions recorded **without** the factor provenance link (AGENTS.md §17/§25) | `documents_main.py:517`; `drafts.py:406`; `admin/extraction.py:190` | Repoint; additionally make a missing factor a *blocking validation* state rather than a silent null |
| **F-05** | **S2** | `LIVE_BREAKAGE (reporting)` | Enhanced report generation embeds the legacy factor relation; `GET /api/reports/defra-factors/{year}`, `GET /api/reports/defra-mapping`-adjacent import, `GET /api/emissions/{org}` and the org dashboard/data/export routes all fail | `report_generator.py:595,621,764`; `reports.py:280,1265`; `emissions.py:153,199`; `organizations/{dashboard.py:109,124,203,236, data.py:…, exports.py:56}` | Repoint to canonical factor objects; reports must read persisted emissions/snapshots (§27) |
| **F-06** | **S2** | `LIVE_BREAKAGE (admin API)` | The **entire** admin factor-management API (`/api/admin/defra/*`, 9 routes, 16 reads) is non-functional | `routes/admin/defra.py` (16 lines listed) | Repoint onto `emission_factors`+factor sets, or retire the API with the page |
| **F-07** | **S2** | `LIVE_BREAKAGE (admin UI)` | The deployed `/admin` factor-management page and both modals cannot list/save/import factors (9 direct PostgREST calls) — a live Control-Plane surface that is dead | `admin/src/pages/admin/DefraFactors.js:39,81,95`; `components/admin/{DefraFactorModal,ImportDefraModal}.js`; deployment wiring §14 | Same decision as F-06; admin factor administration must converge on the canonical factor model |
| **F-08** | **S3** | `API_CONTRACT` | `ManualEntryStandalone.jsx:226` calls `/api/defra-factors/{year}`, but the only registered route is `/api/reports/defra-factors/{year}` → 404 independent of the schema defect | `frontend/src/components/ManualEntryStandalone.jsx:226`; `routes/reports.py:271` | Fix URL **and** repoint the data source, or retire the screen (§29/§30 messaging boundary not implicated) |
| **F-09** | **S2** | `LIVE_BREAKAGE (customer UI)` | The shipped customer SPA's emissions/log view embeds the legacy factor relation | `frontend/src/App.js:731` | Repoint or remove the embed; prefer canonical API over client-side joins |
| **F-10** | **S2** | `LIVE_BREAKAGE + GAP` | SCM-005 confirmed live: report **sharing** (`POST /{report_id}/share`, `GET /shared`) cannot function, **and** its share register has no canonical replacement | `reports.py:1852,1929` (`POST /api/reports/{report_id}/share`, L1842); `reports.py:1969` (`GET /api/reports/shared`, L1961); §18.2 | PO decision: retire the two endpoints, or introduce a canonical share model (migration + RLS + evidence) — **not** a rename |
| **F-11** | **S2** | `LIVE_BREAKAGE + GAP` | SCM-006 confirmed live: scheduled reporting (`POST/GET/DELETE /api/reports/schedule`) cannot function, **and** no canonical scheduling table exists | `reports.py:1372,1435,1498,1510`; routes L1327, L1428, L1489; §18.3 | PO decision: retire the three endpoints, or implement canonical scheduling + a durable server-side scheduler |
| **F-12** | **S3 (was S2)** | `ORPHAN / LATENT` | SCM-007's **only** consumer is unreachable: `backend/routes/admin/audit_logs.py` is never imported, never registered, has no dynamic import, and is absent from `verify_startup.py` → the `notification_delivery_log` read at `:404` cannot execute in the deployed app. It is a latent trap (55 KB, 12 undeclared routes), not a live break | §11, §12.3; `main.py:78,242`; `routes/admin/__init__.py`; repository-wide `importlib`/`__import__` search | Re-grade SCM-007 **S2 → S3**; decide: delete the module, or wire it in *after* repointing onto `notification_delivery` |
| **F-13** | **S4** | `STALE_ARTEFACT` | `prisma/schema.prisma` is a pre-RC2 introspection snapshot (`model notification_delivery_log` + `defra_factor_used` relation) that contradicts the canonical chain, and `seed.ts:208`'s `PRESERVE_TABLES` entry for `defra_conversion_factors` is dead config (`PRESERVE_TABLES` is never consumed). No runtime impact today (no `@prisma/client` in the backend) | §15 | Re-introspect/quarantine the Prisma schema against canonical; delete the dead seed entry; document that Prisma is not a schema authority |
| **F-14** | **S4** | `TEST_TRAP` | Tests assert **200** on routes that cannot succeed (`/api/reports/defra-mapping`, `/api/reports/defra-factors/2024`), and **no** test covers any of the four mismatches → the suite neither caught nor will confirm-fix this class of defect | §17 | Replace with tests that assert canonical behaviour (200 + real factor data) and negative tests for retired endpoints |
| **F-15** | **S4** | `SOURCE_OF_TRUTH` | Stale copies/materials still describe the four names: 217 doc mentions for the factor table; the historical DDL in `database/rc1|rc2` (which *creates* the legacy table); `docs/architecture/DB_Migration/MIGRATION_007_REPORTING_COMPLIANCE.sql` (which creates `report_history`/`report_schedules`); `supabase/snippets/`; duplicate frontend bundles; and the uncommitted deletion of the duplicate `e2e/` migration chain | §16, §2.3 | Commit the `e2e/` deletions; mark the historical DDL/`database/` trees explicitly as non-authoritative; add a "canonical schema only" pointer to the docs that mention the legacy names |

**Totals:** 1 × S2-contract (F-01), 8 × S2 live-breakage/gap (F-02…F-07, F-09…F-11), 2 × S3 (F-08, F-12), 3 × S4
(F-13…F-15). **No S1 finding**: none of the four names blocks a canonical rebuild — indeed the chain *depends* on their
absence.

---

## 19.1 Remediation status (2026-09-28, CT-IMPLEMENT-04)

Historical finding text above is left untouched; this table is the current status.

| Finding | Current status | Evidence / residual |
|---|---|---|
| **F-03** | **REMEDIATED** (CT-IMPLEMENT-01 §6.5) | `utils.emissions.get_emission_factor` resolves through the canonical chain (approved customer factor → `emission_factors` via `factor_aliases` → controlled unresolved) |
| **F-04** | **PARTIAL** — repointed, not hardened | `documents_main.py`, `drafts.py`, `admin/extraction.py` use the canonical resolver; making a missing factor a *blocking validation* state is still open |
| **F-05** | **PARTIAL** — all non-decision-gated sites repointed (CT-IMPLEMENT-04) | repointed: `report_generator.py`, `routes/emissions.py`, `organizations/{data,dashboard,exports}.py`; residual: `routes/reports.py:279,1290` (PD-3/PD-5) |
| **F-06** | **OPEN** (PD-3 unratified) | `routes/admin/defra.py` — its 16 reads are unchanged |
| **F-07** | **OPEN** (PD-3 unratified) | `admin/src` — 9 calls in 3 files unchanged |
| **F-08** | **OPEN** (PD-5 unratified) | `ManualEntryStandalone.jsx:226` still calls the unregistered `/api/defra-factors/{year}` |
| **F-09** | **REMEDIATED** (CT-IMPLEMENT-04) | `frontend/src/App.js` legacy factor embed removed; `frontend/App_.js` legacy fallback removed; `frontend/**` now has **zero** occurrences |
| **F-14** | **OPEN** | the SCM-004 trap assertions are unchanged *by design* while F-05's remaining endpoints are PD-3/PD-5-gated |
| **F-13 / F-15** | **OPEN** (hygiene) | stale artefacts (`prisma/schema.prisma`, `seed.ts`, `database/rc1|rc2`, duplicated frontend bundles) unchanged |

Verification: `backend/tests/unit/test_ct_implement_01_remediation.py` now asserts
both directions — the repointed files contain no legacy reference and *do* contain
`emission_factors`, and a new reference in any other live-code file fails an
explicit allowlist check.

---

## 20. PO decisions required

No business policy is changed or inferred by this audit. The following are **PO DECISION REQUIRED** items (AGENTS.md §62):

| ID | Decision | Options | Consequence if undecided |
|---|---|---|---|
| **PD-1** | Report **sharing** (SCM-005): is share-to-other-users a CarbonTally V3 feature? | (a) Retire `POST /{id}/share` + `GET /shared`; (b) introduce a canonical share model (new canonical table + RLS mirroring consultant/client/PE boundaries + evidence) | The feature silently 500s; customers cannot share reports. **Status 2026-09-28: decided as (b) — "PD-1 and PD-2 were implemented as ratified" (CT-IMPLEMENT-02)**; canonical share tables + route rewrite delivered; consuming/delivering a share still open (CT-IMPLEMENT-03 §12 / G-2) |
| **PD-2** | Scheduled **reporting** (SCM-006): does V3 support scheduled/periodic report delivery? | (a) Retire the three endpoints; (b) add canonical scheduling + a durable server-side scheduler with delivery evidence | Same as PD-1, plus no automation. **Status 2026-09-28: decided as (b) — "PD-1 and PD-2 were implemented as ratified" (CT-IMPLEMENT-02)**; canonical `report_schedule_definitions` + append-only guards + runner/domain layer delivered (CT-IMPLEMENT-03); wiring a worker/trigger remains open |
| **PD-3** | **Admin factor management**: does the Control Plane keep managing factor data directly? | (a) Repoint `/api/admin/defra/*` + `/admin` page onto `emission_factors`/factor sets; (b) retire the API + page in favour of canonical factor administration | A deployed admin surface stays dead; factor data cannot be curated. **Status 2026-09-28: STILL OPEN — not ratified.** `routes/admin/defra.py` (16 reads) and the 3 `admin/src` files are therefore untouched; only the non-admin read sites are remediated (CT-IMPLEMENT-04) |
| **PD-4** | The **orphan** `routes/admin/audit_logs.py` (55 KB, 12 routes) | (a) Delete as dead code; (b) revive and repoint (incl. `notification_delivery`) | Dead code accumulates; a future re-wire imports a guaranteed failure. **Status 2026-09-28: STILL OPEN** — the orphan module is unchanged |
| **PD-5** | **Manual-entry** factor lookup (`ManualEntryStandalone.jsx`) | (a) Repoint to a registered canonical endpoint; (b) retire the screen | A shipped screen silently 404s. **Status 2026-09-28: STILL OPEN** — `frontend/src/components/ManualEntryStandalone.jsx:226` still calls the unregistered `/api/defra-factors/{year}`; F-08 untouched |
| **PD-6** | **Factor precedence** must be honoured by any repointing (approved customer factor → CarbonTally matching → unresolved/manual review; AGENTS.md §15) and must not allow silent fallback to generic factors | Confirm the ratified rule is the basis for the remediation design | The remediation could silently replace approved customer factors — a policy breach. **Status 2026-09-28: not implicated by CT-IMPLEMENT-04** — the repointed sites read the factor already recorded on `emissions_logs.emission_factor_id`, so no new factor *selection* (and therefore no generic-factor fallback) was introduced; `utils/emissions.py` precedence is unchanged |

**Not PO decisions (pure engineering, within ratified architecture):** the `utils/emissions.py` repoint (F-03), the embed
removals (F-05/F-09), F-08's URL correction, F-13/F-14/F-15 hygiene — subject to PD-3/PD-6 design constraints.

---

## 21. Recommended remediation sequence (NOT implemented)

Ordered so each step is independently testable, smallest-first, and respects the canonical chain's constraints. This is a
*proposal*; no item below was executed.

**Status 2026-09-28:** steps **3** (CT-IMPLEMENT-01 §6.5) and **5** (CT-IMPLEMENT-04 — `routes/reports.py:279` remains)
are now executed, and step **8** was superseded by the PD-1/PD-2 decision (CT-IMPLEMENT-02/03). Steps **2, 4, 6, 9, 10**
are unchanged and step **7** remains PD-5-gated.

| Step | Action | Findings | Rationale / obligations |
|---|---|---|---|
| 1 | **Commit or discard the pending deletion of the duplicate `e2e/` migration chain** | F-15 | Removes a second source of truth before anyone edits migrations; must not be mixed into the code fix |
| 2 | **Decide PD-4 and act**: delete `routes/admin/audit_logs.py`, or revive it *after* repointing to `notification_delivery` | F-12 | Removes the only `notification_delivery_log` reference; if revived, review all 12 routes for further non-canonical objects |
| 3 | **Repoint `utils/emissions.get_emission_factor()`** through the V3 factor-matching path (precedence, aliases, provenance) — never by creating the legacy table | F-01, F-03, PD-6 | Unblocks the MAP stage; must test precedence (customer factor wins; unresolved → manual review) |
| 4 | **Repoint or retire the admin factor API + page** (PD-3): `routes/admin/defra.py` (16 reads) and the 3 admin UI files | F-06, F-07 | One decision, two layers; must preserve audit/authorisation for factor mutation |
| 5 | **Repoint or remove the factor embeds** in `report_generator.py`, `emissions.py`, `organizations/{dashboard,data,exports}.py`, `frontend/src/App.js` | F-05, F-09 | Reports must be generated from persisted emissions/snapshots (AGENTS.md §27); prefer canonical API over client joins |
| 6 | **Make a missing factor a blocking validation state**, not a silent null, in `documents_main.py`, `drafts.py`, `admin/extraction.py` | F-04 | Provenance integrity: no emissions number without its factor chain (AGENTS.md §17/§25) |
| 7 | **Fix the `/api/defra-factors/{year}` URL** in `ManualEntryStandalone.jsx` (or retire the screen — PD-5) | F-08 | Independent of the schema defect; cheap and verifiable |
| 8 | **Resolve PD-1 and PD-2** (report sharing, report scheduling): retire endpoints **or** add canonical models | F-10, F-11 | Retiring is small and safe; implementing is a feature (migration + RLS + durable scheduler + evidence) |
| 9 | **Hygiene**: re-introspect/quarantine `prisma/schema.prisma`, delete the dead `PRESERVE_TABLES` entry, sweep stale frontend bundles/`database/` DDL, add "canonical only" pointers to docs naming the legacy tables | F-13, F-15 | Prevents recurrence: this mismatch survived because stale artefacts looked authoritative |
| 10 | **Tests**: replace the two `200`-asserting tests with canonical assertions; add negative tests for retired endpoints; add a grep-level conformance test that fails if any of the four names reappears in non-documentation code | F-14 | Provides the regression barrier this defect class lacked (AGENTS.md §72) |

**Cross-cutting obligations for any step:** no new table may be named `defra_conversion_factors` (F-01); no RLS relaxation
(§67); tenant/consultant/PE boundaries unaffected but re-tested wherever admin factor data is touched (§44/§45); the
`F-046-1` harness-target safety invariant is unchanged (§55.1); independent QA after implementation (AGENTS.md §60).

---

## 22. What this audit did NOT prove (limitations)

| # | Limitation | Effect on conclusions |
|---|---|---|
| 1 | **No endpoint was called.** Breakage is inferred from (proven) table absence plus PostgREST semantics | The *fact* of failure is certain; the exact status/error body per route was not observed |
| 2 | Supabase Cloud (production) was not probed (no credentials or authority) | Production absence is *expected* (the chain renames and asserts) but **unverified**; recorded as an unknown |
| 3 | Reachability is a **static** import/registration analysis | No runtime route dump was taken; a runtime-only registration of `audit_logs` is not supported by any code read, but was not disproven at runtime |
| 4 | Data-level impact (which documents/logs/reports failed, how many, when) was **not** measured | Severity is structural, not quantified; a follow-up can count failed processing runs on a live stack |
| 5 | The canonical factor model's exact column correspondence was not fully read | §18.1's mapping is *directionally* verified; the field-level rename map is a remediation-time task |
| 6 | Only the four names were traced | Other legacy references inside the same files (e.g. the orphan module's remaining routes) are out of scope and may yield additional findings |
| 7 | Documentation counts are grep-level mention counts | They indicate exposure to stale vocabulary, not defect count |
| 8 | Pre-existing working-tree changes (§2.3) were recorded, not adjudicated | `.gitignore` and `20260823000000_d32_private_documents_storage.sql` are modified in the tree; that deserves separate owner attention |

---

## 23. Verdict and acceptance language

### 23.1 Status vocabulary (AGENTS.md §73)

**IMPLEMENTED — nothing.** This task performed no implementation.

**VERIFIED** (directly observed read-only this session):

1. All four names **absent** in every probed database and docker instance, with canonical counterparts present (§3).
2. No canonical migration creates any of the four names; `defra_conversion_factors` is asserted **absent** by a guard that
   aborts the chain (§5, F-01).
3. The consumer modules for SCM-004/005/006 **are registered and live** in `backend/main.py` (§12).
4. `backend/routes/admin/audit_logs.py` is **never imported, never registered, not dynamically imported and not
   startup-verified** (§11 / §12.3) — the basis for the SCM-007 re-grade.
5. The admin SPA **is built and deployed** at `/admin` by the root build script (§14).
6. `PRESERVE_TABLES` is never consumed; the backend does not use `@prisma/client` (§15).
7. Git state: HEAD `cb70fd6`, branch `p8-release-reconciled`, 122 pre-existing working-tree changes (§2.1/§2.3).

**INFERRED** (high confidence, not executed): that each live-broken path returns an error at runtime, and the specific
PostgREST error codes.

**ACCEPTED — NO.** PO acceptance has not been sought; PD-1…PD-6 remain open.

### 23.2 Per-name verdict

| Name | SCHEMA-01 grade | SCHEMA-03 verdict | Classification summary |
|---|---|---|---|
| `defra_conversion_factors` | S2 `CODE_EXPECTS_MISSING_OBJECT` | **CONFIRMED — LIVE-BROKEN (scope understated)** | 41 live-broken backend reads, 9 live-broken admin calls, 2 live-broken frontend calls, 1 URL defect; chain forbids recreation; canonical target `emission_factors` |
| `report_history` | S2 | **CONFIRMED — LIVE-BROKEN + GAP** | 3 refs on 2 registered routes; canonical successor `report_versions`; **no share model exists** → PD-1 |
| `report_schedules` | S2 | **CONFIRMED — LIVE-BROKEN + GAP** | 4 refs on 3 registered routes; **no canonical table at all** → PD-2 |
| `notification_delivery_log` | S2 | **RECLASSIFIED — ORPHAN (latent)** | 1 ref in an unregistered module; canonical target `notification_delivery`; recommend S3 + PD-4 |

### 23.3 One-sentence verdict

> The three SCM-004/005/006 mismatches are **live**, customer- and admin-reachable failures on registered routes that cannot
> be fixed by recreating the legacy objects (the canonical chain forbids it), while SCM-007 is a **latent orphan** whose
> single reference is unreachable — so the correct disposition is *repoint or retire*, with two PO decisions (report sharing,
> report scheduling) required because those two capabilities have no canonical equivalent.

---

## 24. Register reconciliation (delta versus SCHEMA-01)

| Register entry | Register says | SCHEMA-03 finds | Delta / action |
|---|---|---|---|
| **SCM-004** | 5 consumer locations; "add the table **or** repoint" | **12 backend modules / 42 hits**, 3 admin files, 1 frontend file, 4 prisma/seed; **recreation is forbidden by the R1 guard** | **Register scope understated** (its list was a sample). Remove "add the table" as an option; record F-01. Severity stays **S2**; remediation scope grows |
| **SCM-005** | 3 consumers (`1852,1929,1969`) | Exactly those three, on 2 registered routes; canonical successor `report_versions`; **share register has no canonical equivalent** | Add the **gap + PD-1** dimension; severity stays S2 |
| **SCM-006** | 4 consumers (`1372,1435,1498,1510`) | Exactly those four, on 3 registered routes (**the 5th grep hit is the handler name** — a false positive); **no canonical table exists** | Add the **capability-gap + PD-2** dimension; severity stays S2 |
| **SCM-007** | 1 consumer (`audit_logs.py:404`), S2 | Same single consumer, but its module is **unreachable** (not imported / registered / startup-checked) | **Re-grade S2 → S3** (`LATENT_DEAD_CODE`); add PD-4 |
| **SCM-008** (context) | durable DBs are behind the chain | Not in scope; the four names' absence is independent of drift (§3) | No change |

Nothing in the SCHEMA-01 register is contradicted; two entries need **scope** amendments (SCM-004) and the remaining two need
**grading/gap** amendments (SCM-005/006/007).

---

## 25. Appendix — evidence index, manifest and final statement

### 25.1 Evidence artefacts (read-only scratch, session-local)

| Evidence | Contents |
|---|---|
| `/tmp/s03_presence_canon.txt`, `s03_presence_demo.txt`, `s03_presence_flag.txt` | Four-name absence + canonical-counterpart presence, per main-stack database |
| `/tmp/s03_dockerprobe2.txt`, `/tmp/s03_dbs2.txt` | 72 docker database instances, `legacy = 0` |
| `/tmp/s03_canon.txt`, `/tmp/s03_tables3.txt` | Canonical table census (incl. `emission_factors`, `report_versions`, `notification_delivery`, `notifications`, `report_generation_queue`) |
| `/tmp/s03_inv.txt`, `s03_inv2.txt`, `s03_inv3.txt`, `s03_inv4.txt`, `s03_inv5.txt`, `s03_inv6.txt` | Per-tree/per-file reference inventory; Prisma model context; seed config; frontend/admin callers; docs mention counts; Git state; route-registration grep |
| `/tmp/s03_final12.txt`, `s03_final13.txt`, `s03_final14.txt` | R1 guard and verification SQL; `audit_logs` import probe; canonical `report_*` tables; orphan-route analysis; deployment wiring |
| `/tmp/s03_nondocs.txt`, `s03_matrix.txt`, `s03_imports.txt`, `s03_sched3.txt`, `s03_tests.txt`, `s03_ghist4.txt`, `s03_ghist5.txt` | Non-doc reference sweep; classification matrix; import graph; schedule references; test sweep; git-history timeline of the names |
| `/tmp/s03_ports.txt`, `s03_liveness.txt`, `s03_live1.txt` | Backend/frontend/admin liveness and port / openapi probes |
| `/tmp/s03_rprobe.py`, `s03_ef_cols.txt`, `s03_ef_idx.txt`, `s03_sets.txt` | Read-only DB probe script; canonical factor table columns/indexes |

### 25.2 Files changed by this task

| File | Change |
|---|---|
| `docs/architecture/CT-PO-CARBONTALLY-CT-SCHEMA-03-REPORT-20260927.md` | **created** (this report) — the only repository change |

No source file, migration, configuration, database, seed or test was modified. No Git state was altered.

### 25.3 Final statement

The four legacy names are **not** deployment drift, not recoverable objects and not a simple rename. Three are **live
breakage** on registered routes, one is an **unreachable orphan**, one is **forbidden by the canonical schema itself**, and
two expose **capability gaps** (report sharing, report scheduling) that no canonical object covers. Remediation therefore
divides cleanly into *engineering repointing* (bounded, testable, with an in-repo precedent at `backend/routes/reference.py`)
and *PO decisions* (six: PD-1 … PD-6). **Nothing in this report has been implemented**; the §21 sequence is a proposal
awaiting direction.

<!--CTEOF-->
