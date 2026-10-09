# CT-RECON-01 — CarbonTally Complete Capability & Change Census

**Task ID:** `CT-RECON-01-20260926-CARBONTALLY-COMPLETE-CAPABILITY-AND-CHANGE-CENSUS`
**Type:** READ-ONLY FORENSIC PRODUCT / ENGINEERING CENSUS — **DISCOVERY ONLY**
**Date:** 2026-09-26
**Canonical tree inspected:** `/home/shomonrobie/ct_93d5cdd`, branch `p8-release-reconciled`, HEAD `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`
**Historical tree inspected:** `/home/shomonrobie/carbon_tally`, branch `main`, HEAD `20b7a928bb73fdfacf8271ff537a8fd245f62c79`
**GitHub refs inspected:** `2f56562` (`main`), `cb70fd6` (`p8-release-reconciled`), `0bc203f`, `2fd4345`, `363105a`, `954e97c` (PR#1), tags `rc2-final`, `v2.1-phase4`, `v2.1.1-phase3`
**Writes performed:** three new markdown documents only. **No source change, no migration, no database access, no deployment, no push.**
**Product Owner decisions:** **NONE TAKEN** — every PO field here and in the companion ledger is `UNKNOWN`.

---

## 0. Reading rules — how to use this census

This census separates states that are routinely collapsed. A claim is **never**
promoted to a stronger state without evidence. Weakest to strongest:

| # | State | Meaning |
|---|---|---|
| 1 | **DOCUMENTED** | A document asserts it. No code evidence required. |
| 2 | **CODE EXISTS** | Source is present in the inspected tree. |
| 3 | **ROUTE WIRED** | Registered in a backend router table or a React route table (reachable code path). |
| 4 | **AVAILABLE** | Wired and bootable in the inspected runtime configuration (not necessarily running). |
| 5 | **PERSISTED** | Backed by a table or migration **in the repository** — this is *not* a claim that the migration has been applied to any live database. |
| 6 | **E2E VERIFIED** | Exercised end-to-end by a test or a recorded journey. |
| 7 | **INDEPENDENTLY VERIFIED** | Verified by a party other than the implementer (OHD / CoStrict / verifier agent). |
| 8 | **PRODUCTION VERIFIED** | Observed working against the live production artefact. |

Two orthogonal hazards are called out explicitly wherever they apply:

* **LEGACY-DUAL-MOUNT** — `backend/main.py` mounts both the legacy
  `backend/routes/**` routers **and** the V3 `backend/api/router.py`. 407 of the
  802 measurable endpoints (≈51 %) are legacy, and both sets are reachable in
  production.
* **P17-SCHEMA-GAP** — six P17 migrations exist in the repository but are **not
  applied to any live database** (they sit behind a PO-authorised production
  migration gate). Code that reads those objects therefore boots successfully
  and fails only at query time in production.

Confidence tokens: **H** = high (≥2 independent evidence sources, directly
inspected); **M** = medium (single direct source, or a reasoned inference);
**L** = low (documented only, or unverified inference).

Column abbreviations:

* *Current Code State* — `WIRED` (registered/rendered) · `CODE-ONLY` (present but not registered anywhere) · `DUAL` (legacy and V3 both present) · `LEGACY` (legacy surface only)
* *Production Evidence* — `PV` (production verified) · `LIVE-UNKNOWN` (not verifiable read-only) · `NOT-DEPLOYED` · `N/A`
* *P17 Dep* — `yes` · `no` · `partial`
* *Tests* — `U:` unit test files · `I:` integration test files that name the capability

---

## 1. Executive summary

### 1.1 What CarbonTally contains

CarbonTally is a multi-tenant emissions-data-processing platform implemented as
**three deployable surfaces over one PostgreSQL database**:

| Surface | Root | Evidence |
|---|---|---|
| Public website + authenticated customer/consultant workspace | `frontend/**` (CRA React 18) | `frontend/package.json`; `frontend/src/App.js` (2,285 lines) |
| Separately-hosted admin/operations console | `admin/**` (CRA React) | `admin/src/App.js` (117 lines, 18 routes) |
| FastAPI business API | `backend/**` | `backend/main.py` → `app`; `backend/api/router.py` (46 routers) |

plus Supabase (PostgreSQL + Auth + Storage + Realtime), Resend email, Vercel
frontend hosting and Render backend hosting.

Measured surface sizes in the canonical tree (`/home/shomonrobie/ct_93d5cdd`):

| Measure | Value |
|---|---|
| API route decorators (whole backend) | **809** — `get` 442, `post` 258, `put` 71, `delete` 35, `patch` 3 |
| — legacy `backend/routes/**` | **407** endpoints, 50 modules (incl. `admin/`, `organizations/`, `documents/`) |
| — V3 `backend/api/**` | **395** endpoints, 46 registered routers |
| Domain modules | 49 files in `backend/domain/` |
| Engines | 15 files in `backend/engines/` |
| Data-access repositories | 52 files in `backend/data/` |
| Services | 30 files in `backend/services/` |
| Migrations | **89** `.sql` under `supabase/migrations/` |
| Static DB objects declared in migrations | 156 `CREATE TABLE` statements (146 distinct names), 112 `CREATE POLICY` (85 distinct names), 34 functions, 221 indexes, 1 `CREATE TYPE` |
| React route paths | frontend **54** unique `path=` values; admin **18** |
| V3 UI modules | 156 files under `frontend/src/v3/` across 16 sub-surfaces |
| Tests (static counts) | backend test functions **3,672** (of which integration **413**); frontend 410 assertions in 44 files; admin 22 in 4 files; `qa_harness` 29 files |
| Documentation | `docs/architecture` 399 files; `docs/cline` 269 (121 reports, 77 prompt-history); `docs/audit` 197+; `docs/Final_Kimi` 94 |

The platform's real centre of gravity is the pipeline
`UPLOAD → ENQUEUE → INGEST → EXTRACT → MAP → VALIDATE → CALCULATE → EVIDENCE →
REVIEW → CUSTOMER APPROVAL → COMPLETED → REPORTING`, served by a durable
in-process worker (`backend/workers/automatic_processing.py`) with persisted job
state, plus a governed accounting layer (**CAMS**: Scope 1/2/3, contractual
instruments, accounting dimensions, acting-for attribution, estimation records)
that is implemented and repository-persisted but **not applied to any live
database**.

### 1.2 What changed over time (major evolution)

1. **V2.x → V3M1–V3M11 (2026-08-10 → 2026-08-31).** Processing Entities, entity
   relationships, customer factors, issues, entity RLS, organisation-membership
   uniqueness, operational indexes, audit immutability, tenant `org_id NOT NULL`,
   consultant revocation roles.
2. **D20–D37 commercial platform release (2026-08-25/27).** Consultants,
   white-label branding, processing-work assignment, private document storage,
   evidence traceability, self-service onboarding, configurable
   billing/subscription.
3. **Phase 1–9 hardening + operational intelligence (2026-08-29 → 2026-09-15).**
   Restored core business workflow; durable automatic processing; consultant and
   PE operating models; routed item workspaces; server-side pagination; D19
   workbench; Phase 7 document processing and AI extraction; Phase 8 workflow
   orchestrator; Phase 8 report lifecycle (B1–B4, S1–S3, RLS-4A/4B); Phase 8X
   operational health, alerting and API metrics; admin-configurable Google
   Analytics 4.
4. **Phase 8 Insight programme (2026-09-12 → 2026-09-23).** I1 persistence, I2
   authorisation, I3 tool catalogue, I4 interaction orchestration, temporal
   comparison (P2 closure), data-quality reproducibility (P3 / P3-IV-01), each
   with independent OHD verification records.
5. **P12 / P14 / P16 (2026-09-23 → 2026-09-25).** Investor-demo engineering
   (canonical synthetic PDF corpus, demo lab), competitive Scope 1/2/3 coverage
   audit, core accounting journeys and remediation (operator factor precedence,
   factor safety, supplier propagation, financial-year governance, result
   reportability lifecycle, deterministic calculation idempotency, F-046-1
   destructive-harness target guard).
6. **P17 (2026-09-25 → 2026-09-26).** The largest single architectural addition:
   unified CAMS (accounting dimensions and boundaries, acting-for attribution,
   contractual-instrument repository, all fifteen Scope 3 categories, estimation
   and assumption records, product-contract reporting dimensions), the governed
   capability catalogue (18 requirement rows), and the customer/investor
   capability truth surface.
7. **P18 (2026-09-26).** Public-truth hardening: build provenance, admin config
   gate, six security headers, admin branding, publish and live verification.

### 1.3 What currently exists (current code + deployment state)

* The canonical release tree is `/home/shomonrobie/ct_93d5cdd` at `cb70fd6`,
  published to GitHub `refs/heads/p8-release-reconciled` and deployed by Vercel
  **Production deployment `6679336317`** (`vercel[bot]`, status `success`,
  2026-09-26T13:20:23Z).
* `p8-release-reconciled` is a **strict descendant of GitHub `main`**
  (`git merge-base HEAD github/main` = `2f56562` = `main`; `main` is an ancestor
  of HEAD). The release branch therefore contains everything on `main` and has
  **not** been merged back to `main`.
* The backend was **not** redeployed for P18 (Render auto-deploy disabled as an
  operator precondition); **no database operation** was performed.
* ~800 API endpoints, 89 migrations, 54 frontend routes and 18 admin routes are
  present in the release tree.

### 1.4 What exists historically but is not currently verified

Nine clusters (detail in §5 and §6):

1. **`tools/seed_investor_demo/`** — 30 files, including `DEMO_IDENTITIES.md`
   (the ~1,185-identity manifest that `AGENTS.md` §54 makes normative) and
   `demo_manifest.json`. This exists **only** in `~/carbon_tally` and is
   **untracked**; it is **absent from the canonical tree**, while the canonical
   `AGENTS.md` still instructs agents to use it.
2. **32 files of real (non-whitespace) uncommitted work** in `~/carbon_tally` —
   including `backend/engines/calculation.py` (154 delta lines),
   `backend/services/automatic_processing.py` (893),
   `backend/services/automatic_extraction.py`, `backend/domain/calculation.py`
   (13), `backend/domain/automatic_processing.py`, `backend/data/emissions_logs.py`,
   `backend/api/v3_operations.py`, `backend/api/v3_reports.py`,
   `frontend/src/App.js` (74), `frontend/src/v3/api.js`,
   `frontend/src/v3/reports/ReportDetailPage.jsx`, and
   `admin/src/pages/admin/Users.js` (1,221). **A second, divergent copy of
   accounting and admin logic with no counterpart commit in the canonical tree.**
3. **Auditing / assurance tooling and evidence** present only in the historical
   tree: `agent_swarm/`, `agent_swarm_v2_artifacts/`, `saas-assurance/`,
   `independent_audit/`, and `qa_harness/{findings,reports,evidence}`.
4. **Untracked product code**: `frontend/src/v3/reports/ReportLifecyclePanel.jsx`
   (+ its test) and `admin/src/analytics.js`.
5. **1,659 commits reachable only through 553 `refs/cline/*` checkpoint refs** in
   `~/carbon_tally` — IDE auto-checkpoints, not product history (see §4.3).
6. **Static HTML design mockups**: `docs/architecture/UI/`, `docs/architecture/UI2/`
   (`carbontally_dashboard.html`, `compliance_dashboard.html`,
   `batch_management.html`, `audit_logs.html`, `carbontally-themes.html`, …) and
   `carbon-tally-ui-demo/modules/activity_feed.html`.
7. **Legacy admin dashboard artefacts**: `create_admin_dashboard.py`,
   `admin-dashboard.zip`, `docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md`.
8. **`frontend_backup_pre_v3_public_20260827/`** — 235-file frozen pre-V3-public
   frontend snapshot.
9. **Prisma/TypeScript lineage**: `prisma/schema.prisma` (3,510 lines, **129
   models** across `auth` + `public`, datasource `127.0.0.1:54326`), `seed.ts`,
   `seed.config.ts`, `prisma.config.ts`, `tools/carbon_data_factory/` (29 files),
   `clean_emissions_output.json` — a schema snapshot and data factory that sit
   outside the Supabase-migration source of truth.

### 1.5 Partially implemented

* `P17-IMPLEMENT-09` — real-PostgreSQL verified, applicability model deferred.
* `P17-IMPLEMENT-10` — methodology / purchase channel / data-quality vocabulary /
  reporting landed; applicability stopped pending a PO decision.
* Scope 2 **market-based** engine — the P17-K gate asserts "a market-based Scope 2
  requirement must not be recorded with producible capability while no
  market-based engine exists".
* PDF extraction — P12 recorded `CSV PASS / PDF PARTIAL, supplier reuse NOT
  IMPLEMENTED`.
* QA harness — `qa_harness/README.md` declares **BUILD-ONLY**; "must NOT be run
  against CarbonTally until … a run is explicitly authorized"; findings store
  contains 2 files.
* Admin console — renders a config notice because the admin deployment lacks
  `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY`.

### 1.6 Production verified

Only the public-surface artefacts published by P18 are production verified: the
served document and JS bundles (`main.5f9a4b10.js` public, `main.c9f8b964.js`
admin), build provenance pinning the full SHA and branch, the six security
headers byte-exact against the committed `vercel.json`, `/admin` rendering the
config notice instead of the retired test branding, the public routes rendering
non-blank, and API reachability (Render 503 → 200 on cold start). **No
authenticated business workflow is production verified in this census**, and the
live regression in §8.1 is open.

### 1.7 Uncertain

The production database migration ledger (never directly verifiable here;
`docs/operations/MIGRATION_DRIFT_GATE_RUNBOOK.md` records that production "once
carried **21 of 68** migrations while application code that needed the missing
objects was deployable"); the deployed Render revision (no `render.yaml`,
`Dockerfile` or `Procfile` exists, and no Render credential is present); whether
the 32 uncommitted files in the historical tree were superseded or lost; whether
any canonical-only migration beyond the six P17 ones is applied live.

### 1.8 Requires Product Owner decisions

All of §11 — including whether the 32 historical-tree work files are abandoned,
superseded or lost; the P17 production-migration gate; the P17 backend release
decision; legacy API/route retirement (407 dual-mounted endpoints); the QA
harness status; the absent investor-demo seeder and identity manifest; the
P17-K governed capability vocabulary as the single canonical one; and whether
the release branch is ever published to `main`.

---

## 2. Methodology

### 2.1 Posture

Read-only. No file in either repository was modified, created (other than the
three required deliverables) or deleted during the discovery work. No database
was connected to, read from or written to. No migration was executed. No
deployment, push, merge, rebase, reset, cherry-pick or amend was performed. No
package was installed. No product decision was taken.

### 2.2 Evidence classes

The census was built from four evidence classes, deliberately cross-checked:

| Class | What was read | Why it matters |
|---|---|---|
| **Runtime/repo truth** | Git refs, branches, tags, remotes, ancestry, file trees, route tables, router registration, migrations, test files | Primary — current code state |
| **Static database truth** | `supabase/migrations/*.sql` object declarations; `prisma/schema.prisma` introspected model list | Schema shape without touching a database |
| **Governance documents** | PO decision register, master workplan, P16/P17 decisions and implementation reports, migration-drift runbook, verification records | Says what is *authorised* — not what exists |
| **Deployment evidence** | Vercel deployment identity, live bundle hashes, HTTP headers, GitHub refs, as recorded by the immediately preceding P18-04 publication/verification task | The only available source of production truth |

### 2.3 Inspection categories actually executed

1. Repository identity/state: `symbolic-ref`, `rev-parse`, `remote -v`,
   `status --porcelain`, `branch -a`, `tag`, `ls-remote`, `reflog`.
2. History reconstruction: `rev-list --count`, `log --pretty`,
   `diff --stat`, `diff --name-status`, `merge-base --is-ancestor`, set
   comparison of `rev-list --all` across the two trees, `for-each-ref` per-ref
   commit counts.
3. Working-tree forensics: `status --porcelain`, `diff --stat`,
   `diff --ignore-all-space --stat` (to separate line-ending churn from real
   change), file-by-file `diff` between the two trees.
4. Backend census: directory inventory of `api/ routes/ services/ domain/
   engines/ workers/ middleware/ infra/ core/ data/ utils/ tools/`; `grep` of
   `@router.<verb>` decorators; `include_router` registration lists in both
   `backend/api/router.py` and `backend/main.py`.
5. Frontend/admin census: `App.js` route tables, `path=` extraction, page
   directory inventories, `V3Layout` navigation model, `REACT_APP_*` surface.
6. Database census (static): migration filename inventory and cross-tree
   comparison; object-declaration counts.
7. Documentation census: per-directory file counts, newest-document listing,
   targeted reading of governance documents.
8. Static test census: test-file counts and test-function counts.

### 2.4 Limits of this census (stated, not hidden)

* **No live database was read**, by rule. Every *PERSISTED* claim means "a
  migration in the repository declares it". Applied-state is `UNKNOWN` unless a
  governance document records a specific verification run.
* **No authenticated production journey was executed.** Production claims are
  limited to what the preceding P18-04 verification recorded.
* **The two trees are not the same repository.** Commit objects are shared where
  they are shared, but the object sets differ (§4). Cross-tree file comparison
  is by content, not by commit identity.
* **Static counts are not test results.** Test *functions* were counted; the
  suites were **not run** for this census (running them requires a database
  target and is outside the discovery mandate; `AGENTS.md` §55.1 forbids
  pointing the destructive integration harness at any persistent database).
* Where a document claimed a fact that could not be re-verified from code, the
  claim is recorded as DOCUMENTED with confidence **L**.

---

## 3. Sources inspected

### 3.1 Repositories

| Tree | Path | Branch | HEAD | Notes |
|---|---|---|---|---|
| Canonical release | `/home/shomonrobie/ct_93d5cdd` | `p8-release-reconciled` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | 537 commits on HEAD, 545 reachable, 208 reflog entries; 1 pre-existing tracked modification (`.gitignore`); 23 pre-existing untracked paths |
| Historical working tree | `/home/shomonrobie/carbon_tally` | `main` | `20b7a928bb73fdfacf8271ff537a8fd245f62c79` | 206 commits on HEAD; 2,000 reachable via `--all`, of which **1,659 only via `refs/cline/*`**; 227 tracked modifications (predominantly line-ending churn); 78 untracked paths |

Canonical-tree remotes: `github` → `https://github.com/shomonrobie/CarbonTally.git`
(authoritative), `origin` → `/tmp/ct_step2` (a local scratch clone whose
`p8-release-reconciled` sits 204 commits behind HEAD).
Historical-tree remote: `origin` → `https://github.com/shomonrobie/CarbonTally.git`,
with **stale remote-tracking refs** (`origin/p8-release-reconciled` recorded at
333 commits / `93d5cddd`, while the live GitHub ref is `cb70fd6`).

### 3.2 GitHub refs (read-only `ls-remote`, identical from both trees)

| Ref | SHA |
|---|---|
| `HEAD` / `refs/heads/main` | `2f56562ad797c5c2f1b73da7380e45199584e016` |
| `refs/heads/p8-release-reconciled` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| `refs/heads/openhands/analytics-ga4-admin-settings` | `0bc203f8ada4ebed627251b5550cfb1325992497` |
| `refs/heads/openhands/public-website-visual-refactor` | `2fd43454579139ce3e7d1daa1e6ba69646829fd9` |
| `refs/heads/posthog-self-driving/…-c0bc29` | `363105a0d93306b2e84f8f56282590ef58ac02a8` |
| `refs/pull/1/head` · `refs/pull/1/merge` | `363105a…` · `954e97cc7c1cafe6fa9c8e4a837e2a1dc4cd1ac2` |
| `refs/tags/rc2-final` | `eed55d62ee9f103279d0d2a94006952a517d3bde` |
| `refs/tags/v2.1-phase4` | tag obj `16d5519…` → commit `aa4114f46c8b33e19a46a7b98330310ac1b6d473` |
| `refs/tags/v2.1.1-phase3` | tag obj `0c55c8b…` → commit `822936b29f444ded626b387741b1e392407bf774` |

### 3.3 Historical sources read

`~/carbon_tally` working tree (tracked and untracked); 5 local branches (`main`,
`p8-release-reconciled` = `93d5cddd`, `fx12-publish` = `f1a1cf8`, two
`openhands/*` branches); 553 `refs/cline/checkpoints/*` refs; 3 tags;
`tools/seed_investor_demo/*`; `tools/p2_census/*`; `agent_swarm/*`;
`saas-assurance/*`; `independent_audit/*`; `carbon-tally-ui-demo/*`; `prisma/*`;
and 78 untracked paths.

### 3.4 Governance and evidence documents read (selection)

`AGENTS.md`; `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`;
`docs/CARBONTALLY_V3_REFERENCE_INDEX.md`;
`docs/architecture/CT-PO-MASTER-WORKPLAN-20260925.md`;
`CT-PO-P17-L-CAPABILITY-TRUTH-SURFACE-20260926.md`;
`CT-PO-P17-K-GOVERNED-CAPABILITY-CATALOGUE-RUNTIME-DIMENSIONS-20260926.md`;
`docs/operations/MIGRATION_DRIFT_GATE_RUNBOOK.md`;
`docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md`;
`docs/operations/CARBONTALLY_TECHNICAL_OPERATIONS_QUICK_REFERENCE_V1.0.md`;
`docs/verification/CT-P8-I2-PRODUCTION-DEPLOYMENT-STATE-20260921.md`;
`CT-PO-P18-PUBLIC-TRUTH-04-20260926-PUBLISH-VERIFICATION-FINAL.md`;
`.github/workflows/migration-drift.yml`; `backend/api/router.py`;
`backend/main.py`; `supabase/migrations/20261020000000_p17k_governed_capability_catalogue.sql`.

**Explicitly classified as blueprint, not evidence:** `docs/CarbonTally Complete
Customer Feature List.md` (V5.0 "Product Blueprint") and `docs/featurellist.md`
(MVP list) describe aspirational capability sets — including roles that do not
exist in the implementation (`Sustainability Manager`, `Finance Manager`,
`Procurement Manager`, `Auditor`, custom roles and custom permissions). They are
recorded here as **DOCUMENTED ONLY**.

---

## 4. Repository topology and history reconciliation

### 4.1 Are the two trees the same lineage?

| Question | Measured answer |
|---|---|
| Is `93d5cddd` (historical `p8-release-reconciled`; suffix of the canonical directory name) an ancestor of canonical HEAD? | **Yes** — on the canonical lineage, 204 commits behind HEAD |
| Is `98a89d0` (the pre-P18 remote head) an ancestor of HEAD? | **Yes** — 64 commits behind HEAD |
| Is GitHub `main` (`2f56562`) an ancestor of canonical HEAD? | **Yes** — `merge-base HEAD github/main` = `2f56562` = `main` |
| Is canonical HEAD an ancestor of `main`? | **No** — the release branch is a strict, unmerged descendant |
| Is the historical tree's `main` (`20b7a928`) an ancestor of canonical HEAD? | **No** |
| Is `f1a1cf8` (`fx12-publish`) an ancestor of canonical HEAD? | **No** |

### 4.2 Commit-set comparison (`rev-list --all`, sorted, compared)

| Set | Count |
|---|---|
| Canonical tree, all reachable objects | **545** |
| Canonical tree, on HEAD | **537** |
| Historical tree, all reachable objects | **2,000** |
| Historical tree, reachable from branches + tags + remotes | **341** |
| Historical tree, reachable **only** via `refs/cline/*` | **1,659** |
| Commits present in **both** trees | **341** |
| Commits present **only** in the canonical tree | **204** |

### 4.3 Interpretation (evidence-based; no product judgement)

* The canonical tree was **seeded from `93d5cddd`** (hence the directory name
  `ct_93d5cdd`, and `origin` = a local scratch clone sitting 204 commits behind),
  then advanced by **204 commits that exist nowhere else**. The branch is 333
  commits at `93d5cddd` in the historical tree and 537 at `cb70fd6` in the
  canonical tree.
* The historical tree's `2,000` commit count is **not** 2,000 commits of product
  history: **553 `refs/cline/checkpoints/*` refs** (IDE auto-snapshots, each
  ~209 commits of shared history) account for **1,659** of them. Real product
  history in the historical tree is **341** commits from branches, tags and
  remotes.
* **204** real commits — including the entire P17 and P18 body of work and the
  later P8/P12/P16 work that reached `98a89d0` — exist **only** in the canonical
  tree. **The historical tree cannot reproduce them.**
* `93d5cddd..HEAD` = **204** commits; `98a89d0..HEAD` = **64** commits (§5).
* The historical tree's home branch is `main` at `20b7a928` (2026-09-16); the
  canonical tree is ten days ahead of it and lineage-divergent from it.

### 4.4 Migrations differ between the trees

| Tree / ref | `.sql` migrations |
|---|---|
| Canonical `cb70fd6` | **89** |
| Historical `p8-release-reconciled` (`93d5cddd`) | **75** |
| Historical `main` (`20b7a928`) | **68** |

21 canonical migrations are absent from the historical tree's `main`, including
all of: `p8_rls_4b_group1_enablement`, `p8_d4_emission_factors_internal_containment`,
`p8_fin06_manual_processing_governance`, the three `p8_fs_*` migrations, the six
`p8_insight_*` / `p8_i*` migrations, `p16r5_result_reportability_lifecycle`,
`p16r7_calculation_request_idempotency`, and the six `p17*` migrations. No
migration exists in the historical `main` that is absent from the canonical
tree — the canonical set is a strict superset.

### 4.5 Working-tree forensics on the historical tree

`git status --porcelain` reports 227 tracked modifications and 78 untracked
paths. Measured with `--ignore-all-space`, the tracked modifications collapse to
**32 files, 774 insertions, 71 deletions** of real change. The remainder —
notably all 69 `.agents/skills/**` files, all 29 `tools/carbon_data_factory/**`
files, and `v1.9.txt` (2,700 changed lines), `test_results.json`,
`test_results_all.json` — are **pure line-ending churn** (`file` reports CRLF
work-tree files against LF index blobs; e.g. `admin/src/App.js` shows 105/105
line churn, and the same file is byte-identical in content).

Verdict on the historical working tree: **32 files of substantive uncommitted
work**, of which the accounting-critical ones are
`backend/engines/calculation.py`, `backend/domain/calculation.py`,
`backend/services/automatic_processing.py`,
`backend/services/automatic_extraction.py`,
`backend/domain/automatic_processing.py`, `backend/data/emissions_logs.py`,
`backend/data/manual_extraction.py`, `backend/api/v3_operations.py`,
`backend/api/v3_reports.py`, plus frontend `App.js`, `v3/api.js`,
`v3/reports/ReportDetailPage.jsx`, `v3/reports/reports.css`, and admin
`Users.js`, `Settings.js`, `BetaManagement.js`, `AuthContext.js`, `index.js`,
`components/admin/{ImportDefraModal,ReviewExtractionModal,ReviewWorkflow}.js`.

---

## 5. Special investigation — the 64-commit range `98a89d0..cb70fd6`

The range is **64 commits** (2026-09-25 → 2026-09-26). Tree delta:
**131 files changed — 91 added, 40 modified, 0 deleted; 41,503 insertions,
46 deletions.** Top-level distribution: `backend` 68 files, `docs` 30,
`frontend` 12, `admin` 12, `supabase` 6, `vercel.json` 1, `tools` 1, `src` 1.

### 5.1 What the range collectively contains

| Cluster | Representative commits | What it added |
|---|---|---|
| **P17 architecture freeze** | `906e66c`, `172bdd2`, `4bd87a3`, `79e10d2`, `0d9e29f` | ARCH-02/04/05/06 reconciliation, independent re-verification, freeze findings |
| **P17-MASTER-01** | `3b8f85a`, `3dd9fbe`, `2ba39e3`, `9f27665` | Unified CAMS domain layer (scope2, scope3, acting-for, instruments, estimation), CAMS dimension/boundary migrations, tests |
| **P17-IMPLEMENT-02/03** | `415f0f2`, `5834906`, `7b5eb2f`, `fa7edba`, `df52233`, `eb402d5` | Accounting-context resolution, acting-for persistence on the audit ledger, API surface, supplier write-path attribution |
| **P17-IMPLEMENT-04** | `6f48f23`, `5713073`, `a852d6a` | Validated canonical accounting-dimension value object; dimension and attribution threading through the canonical write |
| **P17-IMPLEMENT-05** | `c04d38d`, `a8d0186`, `7dd4b08` | Scope 2 calculation service, API surface, vertical-slice tests |
| **P17-IMPLEMENT-06** | `1f61422`, `d1cb321`, `87a0512` | Trusted contractual-instrument repository, MARKET_BASED Scope 2 wiring |
| **P17-IMPLEMENT-07/08** | `4505e6f`, `b68bf7b`, `7739ed7`, `73c8b9c` | Unified Scope 3 framework with fifteen category contracts, canonical Scope 3 endpoint, estimation-record persistence |
| **P17-IMPLEMENT-09/10** | `75377cc`, `0f248ad` | Real-PostgreSQL Scope 2/3 log persistence; category methodology, purchase channel, widened data-quality vocabulary |
| **P17-K** | `4f8853b`, `ba19ccd` | Governed capability catalogue migration (18 rows); acceptance gates AG-1…AG-8 plus two isolation tests |
| **P17-L** | `a22b97a`, `fb3eba1` | Canonical governed capability projection and capability read endpoint; customer and product capability truth surfaces |
| **P17-M2** | `aa04a48`, `db7dca0` | DEF-1 fix — catalogue version selection anchored to the complete identity set |
| **P17-M (independent)** | `c0b5f27`, `41e6c61` | Independent verification of the P17-K/P17-L capability truth surface |
| **P18-02** | `cb70fd6` | Build provenance, admin config gate, six security headers, admin branding |

### 5.2 Classification of the range (evidence only — not a desirability judgement)

| Classification | Applies to |
|---|---|
| **current** | All of it — the range is the tip of the deployed release branch and nothing supersedes it |
| **production-deployed (frontend only)** | `cb70fd6` — Vercel Production `6679336317` serves this exact SHA |
| **production-NOT-deployed (backend + DB)** | Every backend module and all six `p17*` migrations in the range; the backend was not redeployed and no migration was applied |
| **dependent** | All P17 code depends on the six `p17*` migrations; the P17-L truth surface depends on the P17-K catalogue rows |
| **incomplete** | `P17-IMPLEMENT-09` (applicability model deferred) and `P17-IMPLEMENT-10` (applicability stopped for a PO decision) — self-declared PARTIAL in their own reports |
| **historical** | Nothing in this range; nothing was deleted |
| **superseded** | One internally superseded commit: `db7dca0` re-records the P17-M2 verification environment after `aa04a48` |
| **duplicate** | None identified in this range |
| **uncertain** | Whether the six `p17*` migrations are applied to *any* live database (production ledger state `UNKNOWN`) |

### 5.3 What the range did **not** do

* Added **no** new frontend or admin dependency (only `package.json` edits).
* Deleted **nothing** (0 deletions across 131 files).
* Did **not** change any P17 migration's application state.
* Did **not** merge to `main`, and did **not** reconcile the historical tree.

## 6. Capability census

Every row is one capability. Tokens are defined in §0. `Prod` = Production
Evidence. `P17` = P17 dependency. `Conf` = confidence.

| ID | Capability / Change | Type | Evidence | Historical State | Current Code State | Frontend | Admin | Backend/API | DB/Supabase | Tests | Prod | Dependencies | P17 | Conf | Open Questions |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CAP-001 | Public marketing website (landing) | UI | `frontend/src/LandingPage.jsx`; route `/` | pre-V3 public snapshot `frontend_backup_pre_v3_public_20260827/` (235 files) | WIRED | `/` | — | — | — | — | PV | — | no | H | Which public pages are contractually published? |
| CAP-002 | Company / about page | UI | `AboutUs.jsx`; route `/about` | present pre-V3 | WIRED | `/about` | — | — | — | — | LIVE-UNKNOWN | — | no | M | Content ownership |
| CAP-003 | Pricing page | UI | `PricingPage.jsx`; route `/pricing`; `docs/Pricing/` | present pre-V3 | WIRED | `/pricing` | — | legacy billing routes | `customer_subscriptions` | — | LIVE-UNKNOWN | Billing (CAP-119) | partial | M | Is public pricing authoritative vs configurable billing? |
| CAP-004 | Legal and policy pages (terms, privacy, cookies, data security) | UI | `TermsPage.jsx`, `PrivacyPolicy.jsx`, `CookiePolicy.jsx`, `DataSecurity.jsx`; routes `/terms` `/privacy` `/cookies` `/data-security` | present pre-V3 | WIRED | 4 routes | — | — | — | `DataSecurity.test.jsx` | LIVE-UNKNOWN | — | no | H | Legal review status |
| CAP-005 | Cookie consent banner | UI | `CookieBanner.jsx` | pre-V3 | WIRED | global | — | — | — | — | PV | — | no | H | Is consent recorded/persisted? |
| CAP-006 | Glossary (public read + admin management) | UI+API | `Glossary.jsx`; `backend/routes/glossary.py` (8 endpoints); admin `GlossaryManagement.js` | pre-V3 | DUAL | `/glossary` | `/admin/glossary-management` | legacy glossary router | `glossary` | — | LIVE-UNKNOWN | — | no | H | Which glossary is canonical? |
| CAP-007 | FAQ / contact / services marketing pages | UI | routes `/faq` `/contact` `/services` `/processing-services` `/platform` | pre-V3 | WIRED | 5 routes | — | — | — | — | LIVE-UNKNOWN | — | no | M | Some may be placeholders |
| CAP-008 | Carbon Reduction Plan page | UI | `CarbonReductionPlan.jsx`; route `/carbon-reduction-plan` | pre-V3 | WIRED | route | — | — | — | — | LIVE-UNKNOWN | — | no | M | Reporting product or marketing page? |
| CAP-009 | Public CarbonTally Assistant (visitor chat) | UI+API | `frontend/src/components/chat/**`; `backend/routes/communication.py` (22 endpoints); commit `55410d9` | existed as chat widget | LEGACY | chat widget | — | legacy communication router | `messages`, `conversations`, `message_activity_log` | — | LIVE-UNKNOWN | messaging model (CAP-100) | no | M | Public-only by policy? Which LLM provider? |
| CAP-010 | SEO and PWA artefacts | UI | `frontend/public/{sitemap.xml,robots.txt,manifest.json,sw.js}`, `favicon.ico`, `logo192/512.png` | pre-V3 | WIRED | static assets | — | — | — | — | PV | — | no | M | Is `sw.js` a functional service worker? |
| CAP-011 | Admin-configurable Google Analytics 4 | Admin | commit `37b19d1`; admin `Analytics.js`; `frontend/src/components/AnalyticsBootstrap.jsx`; `posthog-self-driving-report.md` | none | WIRED | global bootstrap | `/admin/analytics` | — | `system_settings` | `AnalyticsBootstrap.test.jsx` | LIVE-UNKNOWN | admin config gate (ISS-006) | no | M | Does GA4 fire live? PostHog lineage unresolved |
| CAP-012 | Self-service signup / onboarding | UI+API | `SelfServiceSignup.jsx` `/signup`; `OnboardingWizard.jsx`, `OnboardingPage.jsx`, `CompanyNamePrompt.jsx`; `d35_self_service_onboarding` | beta-only entry | DUAL | `/signup`, `/onboarding` | `/admin/customers` | legacy `users`, `organizations`; V3 `v3_organizations` | `organizations`, `organization_members`, `pending_invites`, `invitations` | `I:organization_membership` | LIVE-UNKNOWN | PO: public signup closed | no | M | Is public signup closed in production as decided? |
| CAP-013 | Beta access programme | UI+API+Admin | `BetaLogin.jsx` `/beta-login`, `BetaSignup.jsx` `/beta/signup`; admin `BetaManagement.js`; `backend/routes/admin/beta.py` (10 endpoints) | beta was the original entry path | DUAL | 2 routes | `/admin/beta-management` | legacy admin beta router | `beta_users`, `beta_access_codes` | — | LIVE-UNKNOWN | PO §1.3 says retire obsolete beta | no | M | Retire or retain? PO decision recorded, implementation unclear |
| CAP-014 | Email + password authentication | API | `Login.js`; `AuthServiceUnavailable.jsx`; `backend/auth.py`; Supabase Auth | pre-V3 | WIRED | `/login` | `/admin/login` | `backend/auth.py` | `auth.users`, `sessions`, `refresh_tokens` | — | LIVE-UNKNOWN | — | no | H | Live login works end-to-end? (see ISS-001) |
| CAP-015 | Google OAuth / OAuth callback | API | `AuthCallback.js` `/auth/callback`; `REACT_APP_GOOGLE_CLIENT_ID`, `REACT_APP_OAUTH_REDIRECT_URL`; `oauth_*`, `identities`, `custom_oauth_providers` | pre-V3 | WIRED | `/auth/callback` | — | Supabase Auth OAuth | `auth.identities`, `auth.oauth_clients`, `auth.oauth_consents` | — | **open regression** | — | no | H | Google login succeeds then workspace load fails (ISS-001) |
| CAP-016 | Magic-link authentication | API | `MagicLink.jsx` `/auth/magic` | pre-V3 | WIRED | `/auth/magic` | — | Supabase Auth | `auth.one_time_tokens` | — | LIVE-UNKNOWN | — | no | M | Enabled in production? |

| CAP-017 | TOTP MFA / authenticator app | API | `auth.mfa_factors`, `auth.mfa_challenges`, `auth.mfa_amr_claims`, `auth.webauthn_credentials` | pre-V3 | WIRED | — | — | Supabase Auth | `auth.*` MFA tables | — | LIVE-UNKNOWN | deployment policy | no | M | Optional in dev; enforcement is a deployment decision |
| CAP-018 | Password reset | API | `auth.password_reset_tokens`; Supabase reset flow | pre-V3 | WIRED | `/login` | `/admin/login` | Supabase Auth | `password_reset_tokens` | — | LIVE-UNKNOWN | email (CAP-105) | no | M | — |
| CAP-019 | One account, one role identity model | Architecture | PO Register §2.1; `v3m8_system_admin_role_model`; `backend/data/roles.py` | — | WIRED | — | — | `data/roles.py` | `roles`, `organization_members.role` | `I:` role suites | LIVE-UNKNOWN | — | no | H | Is dual-scope identity truly excluded everywhere? |
| CAP-020 | Role model: customer owner/admin/member/viewer | API | `backend/data/roles.py`; RLS migrations `rc2_rls`, `v3m6_entity_rls` | pre-V3 | WIRED | RoleRoute.jsx | — | `api/dependencies.py` | `organization_members`, policies | `U:api/*` | LIVE-UNKNOWN | — | no | H | — |
| CAP-021 | CT internal roles (operator, reviewer, QC, staff admin, system admin) | API | `v3m8_system_admin_role_model`; `staff_roles`; `docs/architecture/CARBONTALLY_*CONTROL_PLANE*` | — | WIRED | `/ops` | admin app | `api/operations_auth.py`, `staff.py` | `staff_roles`, `staff_profiles`, policies | `I:test_operations*` | LIVE-UNKNOWN | — | no | H | Exact capability matrix per staff role |
| CAP-022 | PE roles (PE manager, PE staff/operator) | API | `v3m8_pe_manager_role`; `api/pe_auth.py` | — | WIRED | `/pe` | — | `api/v3_pe.py`, `pe_auth.py` | `processing_entities`, `roles` | `I:test_pe*` | LIVE-UNKNOWN | — | no | H | — |
| CAP-023 | Consultant roles and granular permissions | API | `consultant_roles`, `consultant_role_permissions`, `p6_2a_consultant_processing_permissions` | — | WIRED | `/consultant` | — | `api/v3_consultants.py` | three `consultant_*` tables | `I:test_consultant*` | LIVE-UNKNOWN | — | no | M | Is a consultant "first-class operator" enforced server-side? |
| CAP-024 | Team management (invite / remove / suspend) | UI+API | `TeamManagement.js`; `MembersTab.jsx`; `routes/organizations/members.py` (10), `team.py` (4); `invitations.py` | pre-V3 | DUAL | `/organization` | `/admin/users` | legacy + V3 `v3_organizations` | `organization_members`, `pending_invites`, `invitations` | `U:data/invitations` | LIVE-UNKNOWN | — | no | H | Legacy and V3 member paths both reachable |
| CAP-025 | Login history / staff presence | UI+API | `login_history`; `StaffPresence.jsx`; `StaffOnlinePresence.jsx`; `staff_activity_log` | pre-V3 | DUAL | component | `/staff-dashboard` | legacy staff router | `login_history`, `staff_activity_log` | — | LIVE-UNKNOWN | — | no | M | Retention config (CAP-124) applies? |
| CAP-026 | Organisation profile and metadata | UI+API | `/organization`; `v3/admin/ProfileTab.jsx`; `routes/organizations/metadata.py` (15); `organization_metadata`, `OrganizationMetadata.jsx` | pre-V3 | DUAL | `/organization` | `/admin/organizations` | legacy + V3 | `organizations`, `organization_metadata` | `U:` metadata suites | LIVE-UNKNOWN | — | no | H | Two metadata implementations |
| CAP-027 | Facilities master data | UI+API | `v3/admin/FacilitiesTab.jsx`; `routes/organizations/assets.py`; `facilities` table | pre-V3 | DUAL | `/organization` tab | — | legacy + V3 | `facilities` | `I:` facility tests | LIVE-UNKNOWN | — | no | H | UUID display vs human-readable (AGENTS §34) |
| CAP-028 | Locations master data | UI+API | `v3/admin/LocationsTab.jsx`; `sites/locations` objects in migrations | — | WIRED | `/organization` tab | — | V3 | location tables | `I:` | LIVE-UNKNOWN | — | no | M | Relationship to facilities |
| CAP-029 | Assets master data | UI+API | `AssetManager.js`; `routes/organizations/assets.py` (11 endpoints); `assets` table | pre-V3 | DUAL | `/organization` | — | legacy + V3 | `assets` | — | LIVE-UNKNOWN | — | no | H | — |
| CAP-030 | Vehicles master data | UI+API | `v3/admin/VehiclesTab.jsx`; `api/v3_vehicles.py`; `v3m7_vehicles` | none | WIRED | `/organization` tab | — | V3 vehicles router | vehicles table | `I:` | LIVE-UNKNOWN | — | no | M | — |

| CAP-031 | Suppliers master data | UI+API | `SuppliersTab.jsx`, `v3/admin/SuppliersTab.jsx`; `api/v3_suppliers.py`; `data/suppliers.py`; `suppliers`, `supplier_categories` | pre-V3 | DUAL | `/organization` tab | — | legacy + V3 | `suppliers`, `supplier_categories` | `U:api/test_p17_03_supplier_write_path.py` | NOT-DEPLOYED (P17 write path) | acting-for (CAP-066) | partial | H | Supplier write path now requires accounting context |
| CAP-032 | System settings / platform configuration | API | `api/v3_settings.py`; `system_settings`, `queue_settings`; `SettingsTab.jsx`; admin `Settings.js` | pre-V3 | DUAL | settings tab | `/admin/settings` | legacy settings router + V3 | `system_settings`, `queue_settings` | `U:` settings | LIVE-UNKNOWN | retention (CAP-124), billing (CAP-119) | no | H | Which settings are authoritative? |
| CAP-033 | Protected environment / demo lab | Tooling | `tools/demo_lab/**`; `DEMO_LAB_DATABASE_URL`; `docs/demo-investor/DR-003-demo-lab-cors-browser-verification.md` | none | CODE-ONLY | — | — | scripts only | own DB URL | — | N/A | — | no | M | Is the demo lab still operated? |
| CAP-034 | CSV / XLSX import pipeline | API | `routes/upload.py` (10), `admin_imports.py`; `import_batches`; `docs/sample_bills/`; commits `ad07cd4`, `790923f` | pre-V3 | DUAL | `/documents` upload | `/admin/batches` | legacy upload + V3 documents | `import_batches`, `uploads` | `I:` import tests | LIVE-UNKNOWN | — | no | H | — |
| CAP-035 | Bulk upload (multi-file) | UI+API | `BulkUpload.jsx`, `UploadManager.js`, `UploadSection.js`; `routes/upload.py` | pre-V3 | DUAL | components | — | legacy upload router | `document_processing_queue` | — | LIVE-UNKNOWN | — | no | M | Overlap with V3 upload |
| CAP-036 | PDF ingestion portal | UI+API | `PDFIngestionPortal.jsx`; `routes/documents_main.py`, `customer_documents.py` (16) | pre-V3 | DUAL | `/documents` | `/admin/batches` | legacy + V3 | `customer_documents`, `documents` | — | LIVE-UNKNOWN | OCR (CAP-041) | no | M | Relationship to unified document model |
| CAP-037 | Private document storage (bucket + RLS) | DB | `d32_private_documents_storage`; `backend/services/storage.py`; `organization_files` | none | PERSISTED | — | — | `services/storage.py` | storage bucket + policies | `I:` storage | LIVE-UNKNOWN | — | no | H | Bucket provisioning verified live? |
| CAP-038 | Document status and activity logging | UI+API | `DocumentStatus.jsx`; `useDocumentLogging.js`; `document_activity_log`, `document_activity.py` | pre-V3 | DUAL | component | `/admin/batches` | legacy | `document_activity_log` | — | LIVE-UNKNOWN | — | no | M | — |
| CAP-039 | Manual entry (single + standalone + V3) | UI+API | `ManualEntry.jsx`, `ManualEntryStandalone.jsx`, `ManualEntryView.jsx`, `shared/components/ManualEntryCore.jsx`; `api/v3_manual_extraction.py` | pre-V3 | DUAL | `/dashboard`, `/existing-data` | `/admin/manual-review-queue` | legacy + V3 | `manual_extraction_batches`, `manual_extraction_items`, `draft_entries` | `I:` manual extraction | LIVE-UNKNOWN | FIN-06 governance | no | H | Three manual-entry implementations coexist |
| CAP-040 | Manual extraction review (FIN-06 governance) | API | `api/manual_processing_admin.py`, `manual_processing_auth.py`; `p8_fin06_manual_processing_governance`; `docs/operations/MANUAL_PROCESSING_GOVERNANCE_FIN06.md` | none | WIRED | — | admin manual queue | manual processing admin router | governance tables | `U:` | NOT-DEPLOYED | — | no | H | Migration applied live? |
| CAP-041 | OCR / PDF text extraction | Engine | `backend/pdf_engine.py`; `engines/pdf_render.py`; `tools/provision_tesseract_local.sh`; `OCR_MAX_PAGES`; `ExtractionPanel.jsx` | pre-V3 | WIRED | workspace panel | extraction error review | `engines/extraction.py` | — | `I:` extraction | LIVE-UNKNOWN | **environment dependency (tesseract)** | no | M | Is OCR installed in the Render image? No Dockerfile exists |
| CAP-042 | AI-assisted document extraction | Engine | `engines/ai_extraction.py`, `invoice_extraction.py`; `services/ai_document_extraction.py`; `infra/llm_client.py`, `ai_runtime.py`; `ai_content_history` | — | WIRED | — | — | engines + services | `ai_content_history` | `U:engines/*` | LIVE-UNKNOWN | LLM provider credentials | no | M | Which provider is configured live? Cost controls |
| CAP-043 | Extraction fidelity scoring and suggestions | Service | `services/extraction_fidelity.py`, `extraction_suggestions.py` | none | CODE-ONLY | workspace panel | — | services | — | `U:` | NOT-DEPLOYED | — | no | M | Is it exposed in any route? |
| CAP-044 | Activity clarifications (F-039-1) | API+DB | `api/v3_activity_clarifications.py`; `data/activity_clarifications.py`; three `p8_fs_*` migrations | none | WIRED | workspace | — | V3 clarifications router | clarification + adjudication tables | `U:` | NOT-DEPLOYED | adjudication (CAP-089) | no | H | Migration applied live? |
| CAP-045 | Durable automatic processing worker | Backend | `workers/automatic_processing.py`; `services/automatic_processing.py`; `v3m9_durable_automatic_processing`; `api/v3_automatic_processing.py`; `main.py:268-287` starts it | none | WIRED | `/processing` | live queue stats | worker + service + domain | durable job tables | `I:` automatic processing | LIVE-UNKNOWN | — | no | H | Worker runs in production? Stale-lock recovery exercised? |

| CAP-046 | Processing workflow / job state machine | Domain | `api/v3_processing_workflow.py`, `v3_processing.py`; `domain/workflow.py`; `engines/processing_workflow.py`, `workflow.py` | pre-V3 queue | DUAL | `/processing/:itemId` | `/admin/work-hub` | V3 + legacy | `processing_*`, `processing_queue`, `processing_steps` | `I:` workflow | LIVE-UNKNOWN | — | no | H | Two queue models coexist |
| CAP-047 | Factor matching engine | Engine | `engines/factor_matching.py`, `matching_stages.py`; `domain/matching.py`; `infra/search_index.py` | pre-V3 | WIRED | mapping UI | — | engines | `emission_factors` | `U:engines/test_matching*` | LIVE-UNKNOWN | — | no | H | — |
| CAP-048 | Factor selection policy (precedence and safety) | Engine | `engines/factor_selection_policy.py`; P16 remediation `a12d156` | none | WIRED | — | — | engines | — | `U:` P16 factor suites | LIVE-UNKNOWN | — | no | H | — |
| CAP-049 | DEFRA emission-factor provider and catalogue | Data | `src/providers/defra/*`; `defra_conversion_factors`; admin `DefraFactors.js`, `ImportDefraModal.js` | pre-V3 | DUAL | — | `/admin/defra` | CLI provider + admin router | `defra_conversion_factors` | `U:src/providers/defra/tests/*` | LIVE-UNKNOWN | factor governance (CAP-052) | no | H | Which DEFRA release is live? |
| CAP-050 | SEAI emission-factor provider | Data | `src/providers/seai/*`; five `docs/cline/CarbonTally-SEAI-*` docs; `SEAI-conversion-and-emission-factors.xlsx` | added post-V2.1 | WIRED | — | — | CLI provider | factor import | `U:test_parser.py`, `test_defra_regression.py` | LIVE-UNKNOWN | — | no | H | Ireland launch readiness |
| CAP-051 | Customer custom factors + owner self-approval | UI+API+DB | `api/customer_factors.py`; `domain/customer_factor.py`; `data/customer_factors.py`; `v3m3_customer_factors`; `CustomFactorsTab.jsx` | none | WIRED | admin tab | — | V3 customer-factors router | customer factor tables | `U:engines/test_customer_factor_integration.py` | LIVE-UNKNOWN | PO §16 permits owner self-approval | no | H | Is self-approval implemented as decided? |
| CAP-052 | Factor governance (P17-A) | Domain+DB | `p17a_accounting_dimensions_and_factor_governance`; `p8_d4_emission_factors_internal_containment` | none | PERSISTED | — | — | `data/emission_factors.py` | governance tables + policies | `U:data/test_p17_migrations.py` | NOT-DEPLOYED | — | yes | H | Six P17 migrations unapplied live |
| CAP-053 | Factor aliases | API+DB | `api/admin_aliases.py`; `data/factor_aliases.py`; `add_factor_aliases` | none | WIRED | — | — | aliases router | `factor_aliases` | — | LIVE-UNKNOWN | — | no | M | — |
| CAP-054 | Unit normalisation | Domain | `backend/core/units.py` | pre-V3 | WIRED | — | — | core | — | `U:core/test_units*` | LIVE-UNKNOWN | — | no | H | Single central mechanism? |
| CAP-055 | Validation engine and issue lifecycle | Engine+API | `engines/validation.py`; `domain/validation.py`; `api/issues.py`; `v3m5_issues`; `IssuesPage.jsx` | pre-V3 | DUAL | `/issues` | `/admin/errors` | legacy + V3 issues | `issues` | `I:` issues | LIVE-UNKNOWN | — | no | H | Are stale blocking issues cleared? |
| CAP-056 | Multi-line / item-level factor contract | Engine | fixes `899706d`, `78718bb`; `domain/line_items.py`; `data/emissions_logs.py` | none | WIRED | — | — | engines + domain | `emissions_logs` | `U:` line-item suites | LIVE-UNKNOWN | — | no | H | — |
| CAP-057 | Calculation engine and immutable snapshots | Engine+DB | `engines/calculation.py`; `domain/calculation.py`; `add_calculation_snapshots` | pre-V3 | DUAL | `/emissions` | — | engines + domain | `calculation_snapshots` | `U:engines/test_calculation.py` | LIVE-UNKNOWN | — | no | H | Snapshot provenance fields complete? |

| CAP-058 | Deterministic calculation idempotency | DB+Domain | `p16r7_calculation_request_idempotency`; commit `a12d156` | none | PERSISTED | — | — | domain calculation | idempotency keys | `U:` P16 suites | NOT-DEPLOYED | — | partial | H | Is the migration applied live? |
| CAP-059 | Result reportability lifecycle | DB+Domain | `p16r5_result_reportability_lifecycle`; `domain/report_lifecycle.py` | none | PERSISTED | — | — | domain | lifecycle columns | `U:` P16 suites | NOT-DEPLOYED | reports (CAP-091) | partial | H | — |
| CAP-060 | Scope 1 emissions (fuel and combustion) | Domain+DB | `data/emissions_logs.py`; `mock_uk_fuel_card_messy.csv`; `generate_messy_fuel_csv.py`; `api/v3_emissions.py` | pre-V3 | WIRED | `/emissions` | — | V3 emissions router | `emissions_logs` | `I:test_emissions_logs.py` | LIVE-UNKNOWN | — | no | H | — |
| CAP-061 | Scope 2 location-based accounting | Domain+DB | `domain/scope2.py`; `api/v3_scope2.py`; `services/scope2_calculation.py`; `mock_uk_utility_bill.csv` | location accounting pre-V3 | WIRED | `/emissions` | — | V3 scope2 router | scope2 tables (P17) | `U:services/test_p17_05_scope2_calculation.py` | NOT-DEPLOYED | P17 migrations | yes | H | Which parts require the P17 schema? |
| CAP-062 | Scope 2 market-based + contractual instruments | Domain+DB+API | commits `1f61422`, `d1cb321`; `domain/contractual_instruments.py`; `data/contractual_instruments.py`; `p17c_contractual_instruments_and_allocations` | none | WIRED | `/emissions` | — | V3 scope2 router | instrument + allocation tables | `U:data/test_p17_06_contractual_instrument_repository.py` | NOT-DEPLOYED | P17 migrations | yes | H | Self-declared incomplete (no market-based engine at gate authoring) |
| CAP-063 | Scope 3 — all fifteen categories | Domain+DB+API | commits `4505e6f`, `b68bf7b`, `7739ed7`; `domain/scope3.py`, `scope3_contracts.py`; `services/scope3_calculation.py`; `api/v3_scope3.py`; `p17d_scope3_category_taxonomy` | none | WIRED | `/emissions` | — | V3 scope3 router | category taxonomy tables | `U:domain/test_p17_scope3.py` (15 categories) | NOT-DEPLOYED | P17 migrations | yes | H | Category applicability deferred (PO) |
| CAP-064 | Scope 3 estimation and assumption records | Domain+DB | commit `73c8b9c`; `domain/estimation.py`; `data/estimation_records.py`; `p17h_estimation_and_assumption_records` | none | WIRED | `/emissions` | — | V3 scope3 path | estimation tables | `I:test_p17_09_scope2_scope3_persistence_runtime.py` | NOT-DEPLOYED | P17 migrations | yes | H | — |
| CAP-065 | Unified CAMS domain and accounting boundaries | Domain | `domain/cams.py`, `accounting_dimensions.py`; `p17a_*`; `CT-PO-P17-ARCH-01-*` | none | WIRED | — | — | domain | dimension and boundary tables | `U:domain/test_p17_cams.py` | NOT-DEPLOYED | P17 migrations | yes | H | — |
| CAP-066 | Acting-for attribution and accounting-context API | API+DB | commits `415f0f2`, `5834906`, `eb402d5`; `api/v3_accounting_context.py`, `accounting_context_auth.py`; `domain/acting_for.py`; `data/accounting_context.py` | none | WIRED | — | — | accounting-context router (registered) | audit-ledger attribution columns | `U:api/test_p17_02_accounting_api.py` | NOT-DEPLOYED | P17 migrations | yes | H | Registered after `v3_context` so `/me/context` is unchanged |
| CAP-067 | Product-contract reporting dimensions | DB+Domain | commit `0f248ad`; `p17_10_product_contract_reporting_dimensions` | none | PERSISTED | — | — | domain | contract dimension tables | `U:domain/test_p17_10_product_contract.py` | NOT-DEPLOYED | P17 migrations | yes | H | — |
| CAP-068 | Governed capability catalogue (18 rows) | DB+Domain | commit `4f8853b`; `20261020000000_p17k_governed_capability_catalogue.sql`; `domain/capability_catalogue.py`; gates AG-1…AG-8 | none | PERSISTED | — | — | domain + `api/v3_disclosure.py` | `disclosure_framework_versions`, `disclosure_requirement_versions` | `U:data/test_p17k_*.py`; `I:test_p17k_*_runtime.py` | NOT-DEPLOYED | P17-K migration | yes | H | Scope 3 rollup must be 4/6/3/2 per the PO freeze |
| CAP-069 | Customer + investor capability truth surface | UI+API | commits `a22b97a`, `fb3eba1`; `CapabilityTruthSurface.jsx`, `CapabilitiesPage.jsx`, `InvestorCapabilityPage.jsx`; routes `/capabilities`, `/capabilities/product` | none | WIRED | 2 routes | — | `api/v3_disclosure.py` (extended) | reads P17-K catalogue | `U:api/test_p17l_capability_truth_surface.py`; `frontend/src/v3/__tests__/capability-truth-surface.test.jsx` | NOT-DEPLOYED | CAP-068 | yes | H | Rendering branches of AG-3…AG-8 were PENDING before P17-L |
| CAP-070 | Seven governed capability values / one vocabulary | Domain | `domain/disclosure.py` `CARBONTALLY_CAPABILITIES` (7); DB CHECK constraint equality asserted by AG-1 | none | WIRED | — | — | domain | CHECK constraint | `U:data/test_p17k_governed_capability_catalogue.py` | NOT-DEPLOYED | CAP-068 | yes | H | Second capability model must not be created (PO F-1/F-2) |

| CAP-071 | Evidence trail and source-evidence viewer | UI+API | `EvidenceTrail.jsx`, `EvidenceRecordPanel.jsx`, `SourceEvidenceViewer.jsx`; `api/v3_evidence.py`; `d33_evidence_traceability` | none | WIRED | evidence views | — | V3 evidence router | evidence tables | `U:` | LIVE-UNKNOWN | — | no | H | Signed-URL handling must not leak (AGENTS §68) |
| CAP-072 | Evidence line items + provenance line links | DB | `p8_b2_evidence_line_items`; `p8_b2_provenance_line_links`; `data/evidence_line_items.py`; `tools/backfill_evidence_line_items.py` | none | PERSISTED | — | — | data layer | two P8-B2 tables | `I:` B2 suites | NOT-DEPLOYED | — | no | H | Migration applied live? |
| CAP-073 | Immutable audit ledger | DB+API | `audit_logs`, `audit_trail`; `p7_audit_immutability_and_indexes`; `audit_activity_immutability`; `infra/audit_logger.py`; shared `audit_logger.py` | pre-V3 | DUAL | — | audit tabs | legacy `admin_audit` + V3 | `audit_logs`, `audit_trail` | `U:domain/test_audit*` | LIVE-UNKNOWN | — | no | H | — |
| CAP-074 | Actor, automation and write-once provenance gates | DB | `gate4_actor_provenance`; `gate5_t1_automation_provenance`; `gate5_t6_automation_write_once_guard`; `gate6_w1_automation_extracted_output` | none | PERSISTED | — | — | data layer | gate columns + guards | `I:` gate suites | LIVE-UNKNOWN | — | no | H | — |
| CAP-075 | Data-quality scan and reproducibility | Service+DB | `domain/data_quality.py`; `p8_insight_data_quality_reproducibility`; P3-IV-01 remediation `8554b78`; OHD verification `0c34908` | none | WIRED | Insight surface | — | services | reproducibility tables | `U:` data-quality suites | NOT-DEPLOYED | Insight (CAP-100) | no | H | `all_checks_passed` semantics fixed in P3-IV-01 |
| CAP-076 | Review queue and review workspace (D19) | UI+API | `api/v3_review.py`; `ReviewQueue.jsx`, `ReviewPage.jsx`, `ReviewDetailPage.jsx`, `ReviewItemPage.jsx`; routes `/review`, `/review/:itemId`, `/ops/review/:itemId` | pre-V3 review | DUAL | 3 routes | `/admin/reviews` | V3 review router | `review_queue`, `review_audit_trail` | `I:` review suites | LIVE-UNKNOWN | — | no | H | — |
| CAP-077 | CarbonTally QC queue | UI+API | `api/v3_qc.py`; `QcQueue.jsx`, `QcItemPage.jsx`, `CtQcTab.jsx`; route `/ops/qc/:itemId` | none | WIRED | 1 route | — | V3 QC router | `qc_checks`, `qc_checklists`, `qc_errors` | `I:` QC suites | LIVE-UNKNOWN | — | no | H | — |
| CAP-078 | Quality chain: PE QC → CT QC → Customer final approval | Workflow | PO Register §2.3; `approval_requests`, `approval_decisions`, `customer_review_log`; `customer_verifications.py` (13 endpoints) | none | DUAL | `/review` | — | legacy + V3 | approval tables | `I:` approval suites | LIVE-UNKNOWN | — | no | H | Are all three stages enforced server-side? |
| CAP-079 | Manual review queue (operator) | UI+API | `admin/src/pages/admin/ManualReviewQueue.js`; `manual_review_queue`; `data/review_queue.py` | pre-V3 | DUAL | — | `/admin/manual-review-queue` | legacy reviews router | `manual_review_queue` | — | LIVE-UNKNOWN | — | no | M | — |
| CAP-080 | Reassignment and review-assignment history | DB | `reassignment_history`, `review_assignment_history`; `admin/assignments.py` (4) | pre-V3 | LEGACY | — | `/admin/assignments` | legacy admin | two history tables | — | LIVE-UNKNOWN | — | no | M | V3 equivalent? |
| CAP-081 | Adjudication lifecycle and context lineage | DB+API | `p8_fs_adjudication_lifecycle`; `p8_fs_adjudication_context_lineage` | none | PERSISTED | workspace | — | clarifications path | adjudication tables | `U:` | NOT-DEPLOYED | CAP-044 | no | M | Migration applied live? |
| CAP-082 | Extraction error review (admin) | UI+API | `ExtractionErrorReview.js`; `routes/admin/extraction.py` (4); `processing_logs`, `processing_audit_trail` | pre-V3 | LEGACY | — | `/admin/errors` | legacy admin | processing logs | — | LIVE-UNKNOWN | — | no | M | Overlaps V3 issues |
| CAP-083 | Work-item assignment foundation and PE operational messaging | DB | `ws4_gate3_4a_item_assignment_foundation`; `phase5_work_item_assignments`; `phase5_pe_operational_messaging` | none | PERSISTED | `/pe/assignments` | — | V3 PE + ops | assignment and message tables | `I:` Phase-5 suites | LIVE-UNKNOWN | — | no | H | — |

| CAP-084 | Report lifecycle and catalogue | UI+API+DB | `p8_report_lifecycle_status`; `api/v3_reports.py`, `v3_reporting.py`; `ReportLifecyclePanel.jsx`; `domain/report.py`, `report_lifecycle.py` | Phase 8 foundation `19e4f01` | WIRED | `/reports`, `/reports/:id` | `/admin/reviews` | V3 reports + reporting routers | report lifecycle columns | `U:api/test_v3_report_lifecycle.py` | NOT-DEPLOYED | CAP-059 | no | H | `ReportLifecyclePanel.jsx` is untracked in the historical tree only |
| CAP-085 | Report versions and frozen artefacts | DB+Service | `p8_b4_frozen_artefact`; `data/report_versions.py`, `report_artefacts.py`; `services/report_artefact_storage.py`; `docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md` | none | PERSISTED | `/reports/:id` | — | services | version/artefact tables + bucket | `I:test_report_versions.py` | NOT-DEPLOYED | bucket provisioning | no | H | Is the bucket provisioned in production? |
| CAP-086 | Intensity catalogue and ratios | DB | `p8_b3_intensity_catalogue`; `p8_b3_intensity_ratios` | none | PERSISTED | — | — | — | two catalogue tables | `U:` P8-B3 | NOT-DEPLOYED | — | no | H | — |
| CAP-087 | Disclosure narrative overlay | DB+Service | `p8_b4_narrative_overlay`; `services/disclosure_narrative.py`; `data/disclosure_narrative.py` | none | CODE-ONLY | — | — | services | narrative tables | `U:` | NOT-DEPLOYED | — | no | M | Exposed in any UI? |
| CAP-088 | Disclosure model and projection engine | Domain+API | `p8_b1_disclosure_model_foundation`; `domain/disclosure.py`, `disclosure_projection.py`, `disclosure_exposure.py`; `api/v3_disclosure.py`; `services/disclosure_finalisation.py` | none | WIRED | capabilities pages | — | V3 disclosure router | disclosure tables | `U:domain/test_disclosure*` | NOT-DEPLOYED | CAP-068 | yes | H | `derive_effective_class` precedence is the outcome engine |
| CAP-089 | Disclosure correction privileges and evidence idempotency | DB | `p8_b1_correction_privileges_and_evidence_idempotency` | none | PERSISTED | — | — | — | privilege + idempotency constraints | `U:` | NOT-DEPLOYED | — | no | H | — |
| CAP-090 | Report exports and export history | UI+API | `api/v3_exports.py`; `routes/organizations/exports.py`, `exports.py`; `export_history`, `report_exports` | pre-V3 | DUAL | — | `/admin/batches` | legacy + V3 exports | `export_history`, `report_exports` | — | LIVE-UNKNOWN | CAP-085 | no | M | — |
| CAP-091 | Legacy reporting and report generator | Backend | `routes/reports.py` (23), `legacy_reports.py`; `backend/report_generator.py`; `engines/report_generation.py`; `report_generation_queue`, `report_templates` | pre-V3 | LEGACY | `/reports` | `/admin/reviews` | legacy routers + generator | template/queue tables | — | LIVE-UNKNOWN | CAP-084 | no | H | Retire or migrate? |
| CAP-092 | Insight Layer-1 persistence (I1) | API+DB | `p8_i1_insight_persistence`; `api/v3_insight.py`; `data/insight.py`; `domain/insight.py`; `InsightPage.jsx`; route `/insight` | none | WIRED | `/insight` | — | V3 Insight router | Insight conversation tables | `U:`/`I:` I1 suites | NOT-DEPLOYED | — | no | H | Persistence only — no LLM in I1 |
| CAP-093 | Insight Layer-1 authorisation (I2) | DB | `p8_i2_insight_authorization`; OHD records `docs/verification/OHD-P8-I2-*` | none | PERSISTED | — | — | policies | policy change | `I:` I2 suites | NOT-DEPLOYED | — | no | H | Independently verified (OHD) at I2 |
| CAP-094 | Insight tool catalogue (I3) — four ratified read-only tools | API | `api/v3_insight_tools.py`; `domain/insight_tool.py`; `services/insight_tools.py`; PO I3 ratification | none | WIRED | `/insight` | — | V3 insight-tools router | reads existing data | `U:` I3 suites | NOT-DEPLOYED | — | no | H | Only four tools are ratified |
| CAP-095 | Insight Layer-2 interaction orchestration (I4) | API+DB | `api/v3_insight_interactions.py`; `p8_i4_insight_interactions`; `services/insight_interactions.py`; `data/insight_interactions.py` | none | WIRED | InsightInteraction.jsx | — | V3 router | interaction tables | `U:` I4 suites | NOT-DEPLOYED | — | no | H | Answer-generation scope |
| CAP-096 | Insight query planner, context and rate limiting | Service+DB | `services/insight_query_planner.py`, `insight_context.py`, `insight_rate_limit.py`; `p8_insight_discovery_aggregation_rate_limit`; `domain/insight_query.py`, `insight_quality.py` | none | CODE-ONLY | — | — | services | rate-limit tables | `U:` | NOT-DEPLOYED | CAP-094 | no | M | Wired to a route? |
| CAP-097 | Insight temporal comparison (P2) | Service+DB | `p8_insight_temporal_comparison`; `InsightComparison.jsx`; closure record `1b33f22` | none | WIRED | `/insight` | — | services | comparison SQL | `U:` | NOT-DEPLOYED | — | no | H | PO closure recorded |
| CAP-098 | Insight references and answer-state model | UI | `InsightReferences.jsx`, `InsightAnswerState.jsx`, `references.js`, `answerStates.js`, `format.js` | none | WIRED | `/insight` | — | — | — | `U:` | NOT-DEPLOYED | CAP-095 | no | M | — |

| CAP-099 | Authenticated messaging (N1) | UI+API+DB | `api/v3_messaging.py`; `MessagingPage.jsx`; `useConversationRealtime.js`; `conversations`, `conversation_participants`, `messages`; `v3m8_messaging_unique_participants` | legacy chat | DUAL | `/messaging` | — | V3 messaging router | 3 messaging tables | `I:` messaging suites | LIVE-UNKNOWN | Realtime | no | H | Boundaries enforced server-side (AGENTS §28)? |
| CAP-100 | Realtime subscriptions | Infra | `frontend/src/context/RealtimeContext.jsx`; Supabase Realtime | pre-V3 | WIRED | global | — | — | publication config | — | LIVE-UNKNOWN | — | no | M | Which tables are published? |
| CAP-101 | Notifications (in-app + delivery ledger) | UI+API+DB | `api/v3_notifications.py`; `NotificationsPage.jsx`, `NotificationSettings.jsx`; `notification_templates`, `notification_delivery`, `notification_delivery_log`; `phase5_notification_event_key` | pre-V3 | DUAL | `/notifications` | bell | legacy + V3 | 3 notification tables | `I:` notification suites | LIVE-UNKNOWN | Resend | no | H | — |
| CAP-102 | Email delivery via Resend | Service | `services/v3_email.py`, `email_service.py`; `utils/email.py`; `email_logs`, `email_templates`; `RESEND_API_KEY` | pre-V3 | DUAL | — | templates | services | `email_logs` | — | LIVE-UNKNOWN | Resend credential | no | H | Sending-domain verification |
| CAP-103 | Activity feed and activity logging | UI+DB | `ActivityFeed.jsx`; `activity_feed`, `activity_logs`; `carbon-tally-ui-demo/modules/activity_feed.html` | pre-V3 | WIRED | dashboard | — | legacy routes | activity tables | — | LIVE-UNKNOWN | — | no | M | Mockup lineage |
| CAP-104 | Consultant workspace | UI+API | `api/v3_consultants.py`; `ConsultantPage.jsx`, `ConsultantItemPage.jsx`; routes `/consultant`, `/consultant/items/:clientId/:itemId` | Phase E `6b4d749` | WIRED | 2 routes | — | V3 consultants router | `consultant_profiles`, `consultant_clients` | `I:` consultant suites | LIVE-UNKNOWN | — | no | H | — |
| CAP-105 | Consultant portfolio and active-client switching | API+DB | `consultant_clients`; `d20_d15_active_consultant_grant`; `v3_context.py` active-client resolver | none | WIRED | `/consultant` | — | context resolver | grant + client tables | `I:` | LIVE-UNKNOWN | — | no | H | Cross-consultant denial tested (AGENTS §45)? |
| CAP-106 | Consultant team management | UI+API+DB | `ConsultantTeamTab.jsx`; `consultant_firm_members`; commit `5d35603` (CL-61) | none | WIRED | consultant tab | — | V3 consultants router | `consultant_firm_members` | `I:` | LIVE-UNKNOWN | — | no | M | Team revocation verified (commit `fc05f05`)? |
| CAP-107 | Consultant new-customer onboarding (CON-1) | UI+API | `NewCustomerView.jsx`; commit `5d35603` | none | WIRED | `/consultant` | — | V3 consultants router | `organizations` | `I:` | LIVE-UNKNOWN | AGENTS §10 | no | M | — |
| CAP-108 | Consultant revocation / lifecycle | API+DB | `consultant_revocation_roles`; `services/consultant_lifecycle.py`; commit `fc05f05` | none | WIRED | — | — | services | revocation role model | `I:` | LIVE-UNKNOWN | AGENTS §11 (same org.id) | no | M | Access revoked without cloning the org? |
| CAP-109 | Consultant billing | DB | `consultant_billing`; `domain/billing.py` | none | CODE-ONLY | — | — | domain | `consultant_billing` | — | NOT-DEPLOYED | CAP-131 | no | L | Live commercial capability? |
| CAP-110 | White-label branding and custom domains | UI+API+DB | `api/v3_whitelabel.py`, `consultant_branding.py`; `WhiteLabelTab.jsx`; `d21_white_label_branding`; `domain/branding.py` | none | WIRED | consultant tab | — | V3 white-label router | branding tables | `I:` | LIVE-UNKNOWN | AGENTS §64 | no | H | No separate deployment (AGENTS §64) |
| CAP-111 | PE dedicated workspace shell | UI | `PEDedicatedHome.jsx`, `PEShell.jsx`, `pe.css`; route `/pe`; commit `85eb074` (G5) | none | WIRED | `/pe` | — | — | — | `I:` | LIVE-UNKNOWN | AGENTS §32 separation | no | H | Dedicated app vs route/shell unresolved |
| CAP-112 | PE work items and assignments | UI+API | `PeWorkItemsPage.jsx`; `/pe/assignments`; `api/v3_pe.py`; `d22_processing_work_assignment` | none | WIRED | `/pe/assignments` | — | V3 PE router | assignment tables | `I:test_pe*` | LIVE-UNKNOWN | CT controls assignment (PO §2.2) | no | H | — |
| CAP-113 | PE routed item workspace (G5) | UI | `PEEntityItemPage.jsx`, `EntityExtractionWorkspace.jsx`; route `/pe/items/:entityId/:itemId`; commit `85eb074` | none | WIRED | route | — | V3 PE router | work-item tables | `U:` | LIVE-UNKNOWN | D19 | no | M | — |
| CAP-114 | Secure document viewer / PE no-download policy | UI | `SecureDocumentViewer.jsx`; PO Register §3.3; `docs/audit/openhands/CARBONTALLY_V3_PE_SECURITY_AUDIT.md` | none | CODE-ONLY | PE + workbench | — | storage service | signed-URL policy | `I:` | LIVE-UNKNOWN | **PO LOCKED: PE must never download** | no | H | Server-side enforcement verified? |
| CAP-115 | PE manager dashboard (F1) | UI | `PEManagerDashboard.jsx`; commit `fc05f05` | none | WIRED | `/ops` + PE | — | V3 PE/ops | assignment tables | `U:` | LIVE-UNKNOWN | — | no | M | — |
| CAP-116 | Processing Entities administration | Admin+API | `ProcessingEntitiesTab.jsx`; `api/v3_processing.py`; `v3m1_processing_entities`, `v3m2_entity_relationships`, `v3m6_entity_rls`; `domain/entity.py` | none | WIRED | — | admin | V3 processing router | entity tables + RLS | `I:test_entity*` | LIVE-UNKNOWN | AGENTS §8 | no | H | — |
| CAP-117 | Operations console | UI+API | `OperationsPage.jsx`, `OpsDashboard.jsx`; `api/v3_operations.py`; route `/ops`; commit `137765f` (X5) | none | WIRED | `/ops` | `/admin/work-hub` | V3 operations router | operational tables | `I:test_operations*` | LIVE-UNKNOWN | — | no | H | X5 extension is read-only |
| CAP-118 | Operator queue and routed workspaces | UI | `OperatorQueue.jsx`, `OperatorItemPage.jsx`, `ReviewItemPage.jsx`, `QcItemPage.jsx`; routes `/ops/items/:itemId`, `/ops/review/:itemId`, `/ops/qc/:itemId`; commits `60e2ab9`, `d632afc` | inline queue | WIRED | 3 routes | — | V3 ops | queue tables | `U:` | LIVE-UNKNOWN | AGENTS §38 (no hunting) | no | H | — |
| CAP-119 | Operational health (X1) | UI+API | `OperationalHealthTab.jsx`; `domain/operational_health.py`; route `/ops/operational-health`; commit `20d27c0` | none | WIRED | 1 route | — | V3 operations | health aggregation | `U:` | LIVE-UNKNOWN | — | no | H | — |
| CAP-120 | Operational alerting (X2) | Service+DB | `services/operational_alerting.py`; `domain/operational_alerts.py`; `p8x_x2_operational_telemetry_retention`; commit `20d27c0` | none | CODE-ONLY | — | — | services | telemetry retention | `U:` | NOT-DEPLOYED | CAP-125 | no | M | Wired to a route? |
| CAP-121 | Operational intelligence aggregation (X4) | Service | `services/operational_intelligence.py`; commit `a71a46a` | none | CODE-ONLY | — | — | services | — | `U:` | NOT-DEPLOYED | — | no | M | Wired? |
| CAP-122 | Persisted API runtime metrics (X7) | Service+DB | `services/api_metrics.py`; `domain/api_metrics.py`; `data/api_metrics.py`; commit `3a34ae3` | none | WIRED | — | — | middleware + services | metrics tables | `U:test_api_metrics*` | NOT-DEPLOYED | — | no | H | Rolling 60m, p95, slow/error |
| CAP-123 | SLA definitions and compliance | DB+UI | `sla_definitions`, `sla_compliance`; `SlaTab.jsx` | none | CODE-ONLY | ops tab | — | — | two SLA tables | — | NOT-DEPLOYED | — | no | L | Which SLAs are contractual? |
| CAP-124 | Search and existing-data discovery | UI+API | `api/v3_search.py`, `v3_discovery.py`; `SearchBox.jsx`, `ExistingDataDiscoveryPage.jsx`; `infra/search_index.py`; commit `d632afc` | pre-V3 search | WIRED | `/existing-data` | search | V3 search + discovery | search index | `I:test_search*` | LIVE-UNKNOWN | — | no | H | — |
| CAP-125 | Configurable retention (N3) | Service+DB | `services/retention.py`; `tools/enforce_retention.py`; `p8x_x2_operational_telemetry_retention`; commit `dc931a3` | none | WIRED | — | admin settings | services + CLI | `system_settings` | `I:` retention | NOT-DEPLOYED | AGENTS §42 (server-side) | no | H | Which retention domains are enforced live? |
| CAP-126 | Admin control plane (separate application) | Admin | `admin/src/App.js` (18 routes); `docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md` | legacy admin dashboard artefacts | WIRED | — | whole app | legacy + V3 | all | `admin/src/*.test.js` (4 files) | config notice | Supabase build settings | no | H | Not operational until build env is configured (ISS-006) |
| CAP-127 | Admin dashboard, customers, organisations, users, batches | Admin | `Dashboard.js`, `Customers.js`, `Organizations.js`, `Users.js`, `Batches.js`; legacy admin routers (dashboard 12, logs 8, staff 16) | pre-V3 | LEGACY | — | 5 routes | legacy admin | organisations, users | — | LIVE-UNKNOWN | — | no | H | — |
| CAP-128 | Admin work hub, live queue stats, staff dashboard, presence | Admin | `WorkHub.jsx`, `LiveQueueStats.jsx`, `StaffOnlinePresence.jsx`; `/staff-dashboard` | none | WIRED | — | 3 routes | legacy staff router | `staff_*`, `queue_settings` | — | LIVE-UNKNOWN | — | no | M | — |
| CAP-129 | Audit console tabs (admin + ops) | Admin+UI | `v3/admin/AuditTab.jsx`, `v3/admin/ActivityTab.jsx`, `v3/ops/AuditConsoleTab.jsx`; `admin/src/components/LogViewer.jsx`; `/admin/log-viewer` | pre-V3 log viewer | DUAL | ops tabs | 2 routes | legacy `admin_audit` + V3 | `audit_logs` | — | LIVE-UNKNOWN | CAP-073 | no | H | — |
| CAP-130 | Commercial and settings tabs (admin/ops) | Admin+UI | `v3/ops/CommercialTab.jsx`, `SettingsTab.jsx`, `StaffRolesTab.jsx`, `ProcessingEntitiesTab.jsx`, `IssuesTriageTab.jsx`, `OpsAssignmentsTab.jsx`; `api/v3_commercial.py` | none | WIRED | ops tabs | admin | V3 commercial router | commercial tables | `I:` | LIVE-UNKNOWN | CAP-131 | no | M | — |
| CAP-131 | Configurable billing and subscription | UI+API+DB | `api/v3_billing.py`; `BillingPage.jsx`; `routes/organizations/*`; `d37_0_billing_security_and_configurable_subscription`, `d37_master_commercial_billing`; `domain/billing.py`, `services/billing.py`; `customer_subscriptions`, `product_categories` | pre-V3 | DUAL | `/billing` | `/admin/customers` | V3 billing router | subscription tables | `I:` billing suites | LIVE-UNKNOWN | AGENTS §43 (configure, not hard-code) | no | H | Was the existing subscription architecture inspected before extension? |
| CAP-132 | Public website vs authenticated application separation | Architecture | AGENTS §30; `frontend/src/App.js` public + `/dashboard/*` authenticated trees; `frontend/src/v3/components/RoleRoute.jsx` | partial | WIRED | both trees | separate app | — | — | — | PV (public side) | — | no | H | Authenticated side unverified live |
| CAP-133 | Build provenance (SHA + branch in the bundle) | Tooling | `tools/generate_build_info.js`; `frontend/src/lib/buildInfo.js`; `admin/src/buildInfo.js`; `CB70FD6`-pinned bundles | none | WIRED | global | global | — | — | `buildInfo.test.js` (frontend + admin) | **PV** | — | no | H | Provenance publishes pre-render by design |
| CAP-134 | Security headers (6, byte-exact) | Config | `vercel.json` headers block | none | WIRED | all routes | all routes | — | — | `—` | **PV** | — | no | H | Report-only CSP not yet enforced |
| CAP-135 | Migration drift gate (WP-8) | Tooling+CI | `backend/tools/migration_drift.py`; `.github/workflows/migration-drift.yml`; `docs/operations/MIGRATION_DRIFT_GATE_RUNBOOK.md` | none | WIRED | — | — | CLI (read-only) | reads ledger | `U:` drift tests | CI failing at startup (ISS-008) | — | no | H | Repo-side check needs credentials-free path |
| CAP-136 | Backup and recovery drill | Tooling | `tools/backup_recovery_drill.py`; `backend/tools/backup_export.py`; `docs/operations/CARBONTALLY_BACKUP_RECOVERY_DRILL.md`; `backups/*.sql` | none | CODE-ONLY | — | — | CLI | `CT_BACKUP_TEST_DSN` | — | N/A | — | no | M | Drill last executed when? |
| CAP-137 | Investor demo seeder and identity manifest | Tooling | `~/carbon_tally/tools/seed_investor_demo/**` (30 files incl. `DEMO_IDENTITIES.md`, `demo_manifest.json`, `safety.py`, `reset.py`, `verify.py`) | created for the investor demo | **absent from canonical tree** | — | — | scripts | seeds all tables | — | N/A | AGENTS §54 | no | H | **Absent from the release tree while AGENTS §54 cites it** (ISS-003) |
| CAP-138 | Carbon data factory (Prisma/TS scaffold) | Tooling | `~/carbon_tally/tools/carbon_data_factory/**` (29 files, `seed.ts`, `verify.ts`, `analyze_project.py`, `.env`) | data-generation lineage | **absent from canonical tree** | — | — | scripts | Prisma | — | N/A | — | no | M | Superseded by `demodatagen`? |
| CAP-139 | Synthetic documents and OCR environment provisioning | Tooling | `tools/generate_synthetic_documents.py`; `tools/provision_tesseract_local.sh`; `demodatagen/**` (generators, data_output, scripts); `generate_messy_*.py`; `mock_*.csv`; `docs/sample_bills/` (8 files) | data lineage | CODE-ONLY | — | — | scripts | — | — | N/A | **OCR is an environment dependency** | no | H | Is tesseract installed in the live backend image? |
| CAP-140 | CarbonTally QA harness | Tooling | `qa_harness/**` (Makefile, scripts `run_all/run_db/run_api/run_browser/run_workflows/run_agents`, identities, rules, workflows, visual/axe); README | none | CODE-ONLY | — | — | read-only probes | read-only | 29 files; `python qa_harness/scripts/run_all.py` not run | N/A | **BUILD-ONLY by policy** | no | H | Findings store holds only 2 files; harness has never been run against the app (ISS-010) |
| CAP-141 | Isolated E2E environment | Tooling | `e2e/environment/**` (bootstrap/reset/teardown/apply_migrations/capture_env, isolated `carbontally_e2e` stack on remapped ports, 26–53 copied migrations) | built for P6-2F acceptance | CODE-ONLY | — | — | provisioning scripts | isolated DB | `--acceptance_report.json` (untracked, historical tree only) | N/A | ports 55325/55326 | no | M | Still provisionable? |
| CAP-142 | Independent audit tooling, agent swarm, SaaS assurance framework | Tooling | `~/carbon_tally/{independent_audit,agent_swarm,agent_swarm_v2_artifacts,saas-assurance}/**`; `docs/ohd/**`; `.costrict/agents/carbon-tally-verifier.md` | OHD/CoStrict-era tooling | **absent from canonical tree** (only the `.costrict` verifier stub remains) | — | — | agents/browser drivers | — | — | N/A | OpenRouter swarm key | no | M | Retain, port or retire? |
| CAP-143 | Legacy admin dashboard artefacts | Tooling | `create_admin_dashboard.py`; `admin-dashboard.zip`; `docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md` | earliest admin prototype | CODE-ONLY | — | — | generator script | — | — | N/A | — | no | M | Historical; PO decision on disposal |
| CAP-144 | Static UI mockups and design demos | Docs/UI | `docs/architecture/UI/**` (incl. `UI.zip`, `Settings .html`), `docs/architecture/UI2/**`, `carbon-tally-ui-demo/modules/activity_feed.html` | design phase | CODE-ONLY | static HTML | — | — | — | — | N/A | — | no | M | Not the live app (per reference index) |
| CAP-145 | Prisma schema snapshot and introspection lineage | DB | `prisma/schema.prisma` (3,510 lines, 129 models, `auth`+`public`), `seed.ts`, `seed.config.ts`, `prisma.config.ts` | used for schema analysis | CODE-ONLY | — | — | — | mirrors Supabase schema | — | N/A | developer tool pin `127.0.0.1:54326` | no | M | Is this maintained or frozen? Which DB was introspected? |
| CAP-146 | D19 processing workbench | UI | `frontend/src/v3/components/workbench/**` (`WorkbenchShell`, `SplitPane`, `WorkflowNav`, `AutosaveIndicator`, `ConfidenceBadge`, `StructuredDataPreview`, `SecureDocumentViewer`); AGENTS §39 | none | WIRED | workbench routes | — | — | — | `I:` workbench suites | LIVE-UNKNOWN | **FROZEN UX decision** | no | H | Any architectural change needs PO review |
| CAP-147 | D21 unified design system | UI | `frontend/src/v3/components/ui/**` (`Card`, `Badge`, `Button`, `DataTable`, `Dialog`, `Drawer`, `FormControls`, `Icon`, `StateViews`, `StatusBadge`, `Tabs`, `hooks.js`, `statusConfig.js`, `ui.css`), `tokens.css`, `v3.css` | none | WIRED | all V3 | — | — | — | `U:` component tests | LIVE-UNKNOWN | **FROZEN UX decision** | no | H | Legacy styling still present in legacy pages |
| CAP-148 | Shared table contract, pagination and page-size standard | UI | `ui/DataTable.jsx`; commits `4e2c3e3`, `8041001`, `60e2ab9`, `1b55ad6`, `d494999` (server-side pagination for review/QC/entities/staff) | none | WIRED | ops + admin tables | admin tables | server-side pagination params | — | `U:` table rules (`qa_harness/rules/tables.py`) | LIVE-UNKNOWN | AGENTS §36 | no | H | Which tables still lack pagination? |
| CAP-149 | Deployment topology and hosting configuration | Config | `vercel.json`; `runtime.txt` (`python-3.11.9`); `backend/main.py`; `frontend/package.json`; `admin/package.json`; `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md` | pre-V3 | WIRED | Vercel | Vercel path `/admin` | Render (`carbontally-api.onrender.com`) | Supabase | — | PV (frontend) | **no `render.yaml`/`Dockerfile`/`Procfile`** | no | H | Render build/start config unverifiable (ISS-012) |
| CAP-150 | Legacy API surface and dual router mount | Architecture | `backend/main.py:212-259` (legacy includes) + `:265` (`api_router`); `backend/routes/**` 407 endpoints | V2.1 | DUAL | all legacy pages | all admin pages | 407 legacy endpoints | shared tables | `ai_route_fullmigration_smoke_test.py` etc. | LIVE-UNKNOWN | retirement policy | no | H | ~51 % of endpoints are legacy; retirement not done (ISS-004) |
| CAP-151 | Dual ASGI entrypoints | Backend | `backend/main.py` (`app`, legacy + V3, V3 import optional at boot) and `backend/main_v2.py` (pure V3 `app`) | main_v2 added for V3 | DUAL | — | — | both | — | `verify_startup.py` | LIVE-UNKNOWN | — | no | H | Which entrypoint does Render run? V3 import failure silently degrades |
| CAP-152 | Seed and demo data definitions | DB+Tooling | `supabase/seed.sql`, `supabase/seed/`, `backups/seed.sql`, `seed.ts`, `e2e/environment/scripts/seed_*.py`, `docs/demo-investor/**` (7 records) | pre-V3 | CODE-ONLY | — | — | scripts | seeds | `—` | N/A | demo identities (CAP-137) | no | M | Which seeds target production-safe data? |

## 7. Change census

Significant changes that are not standalone features. *Origin* = first observed
appearance; *Prod* = production state; *P17* = P17 dependency.

| ID | Change | Evidence | Origin | Current State | Affected Layers | Prod | P17 | Conf | Open Questions |
|---|---|---|---|---|---|---|---|---|---|
| CHG-001 | Tenant model: organisation-scoped `org_id` enforcement | `tenant_org_id_not_null`; `p9_rls_recursion_fix`; `v3m10_org_membership_unique` | V3 hardening 2026-08-31 | PERSISTED, policy-enforced | DB, API, RLS | LIVE-UNKNOWN | no | H | All tenant tables covered? |
| CHG-002 | Processing Entity as first-class entity distinct from organisation | `v3m1_processing_entities`; `v3m2_entity_relationships`; AGENTS §8 | V3M1 2026-08-10 | WIRED, persisted | DB, API, UI | LIVE-UNKNOWN | no | H | — |
| CHG-003 | PE no-download document boundary | PO Register §3.3; PE security audit | PO decision | Documented policy; viewer component CODE-ONLY | UI, storage, API | LIVE-UNKNOWN | no | H | Server-side enforcement evidence? |
| CHG-004 | One account, one role (no dual-scope identity) | PO Register §2.1 | PO decision | Documented; role model matches | Identity, DB | LIVE-UNKNOWN | no | H | Enforced by constraint or convention? |
| CHG-005 | Quality chain: PE QC → CT QC → Customer final approval | PO Register §2.3; QC + review routers | PO decision | WIRED (review, QC, approvals) | Workflow, DB, UI | LIVE-UNKNOWN | no | H | All transitions server-enforced? |
| CHG-006 | Consultant as first-class operator with client portfolio | AGENTS §10–11; `consultant_*`; `d20_d15_active_consultant_grant` | D20 2026-08-21 | WIRED | DB, API, UI | LIVE-UNKNOWN | no | H | Cross-consultant denial tested live? |
| CHG-007 | Consultant-client relationship is a relationship, not a copy | AGENTS §11; `consultant_revocation_roles` | PO decision | WIRED (revocation roles) | DB, API | LIVE-UNKNOWN | no | M | Org preserved on consultant exit? |
| CHG-008 | Customer factor precedence over generic factors | `customer_factors`; `v3m3_customer_factors`; P16 `a12d156` | V3M3 + P16 | WIRED, tested | Domain, DB | LIVE-UNKNOWN | no | H | Snapshot provenance complete? |
| CHG-009 | Customer-owner self-approval of own custom factor | AGENTS §16 | PO decision | Implementation state not established by this census | Domain, workflow | LIVE-UNKNOWN | no | M | Implemented as ratified? |
| CHG-010 | Deterministic server-side calculation with snapshots | `engines/calculation.py`; `calculation_snapshots`; AGENTS §25 | pre-V3 | WIRED | Engine, DB | LIVE-UNKNOWN | no | H | Any JS-side authoritative calculation left? |
| CHG-011 | Calculation idempotency via deterministic request IDs | `p16r7_calculation_request_idempotency` | P16 2026-09-24 | PERSISTED | DB, engine | NOT-DEPLOYED | partial | H | Applied live? |
| CHG-012 | Result reportability lifecycle as a first-class state | `p16r5_result_reportability_lifecycle`; `domain/report_lifecycle.py` | P16 | PERSISTED | DB, domain, UI | NOT-DEPLOYED | partial | H | — |
| CHG-013 | Accounting dimensions and organisational boundaries (CAMS) | `domain/accounting_dimensions.py`, `cams.py`; `p17a_*` | P17 Master 2026-09-25 | WIRED | Domain, DB | NOT-DEPLOYED | yes | H | — |
| CHG-014 | Acting-for attribution persisted on the audit ledger | `domain/acting_for.py`; `5834906`; `v3_accounting_context.py` | P17-IMPLEMENT-02/03 | WIRED | Domain, DB, API | NOT-DEPLOYED | yes | H | — |
| CHG-015 | Contractual instruments with allocation and retirement | `domain/contractual_instruments.py`; `p17c_*` | P17-IMPLEMENT-06 | WIRED | Domain, DB, API | NOT-DEPLOYED | yes | H | Retirement and expiry semantics |
| CHG-016 | Scope 2 dual-method (location + market) accounting | `domain/scope2.py`; `v3_scope2.py`; PO DECISION-03 §8.3 | P17 | WIRED | Domain, API | NOT-DEPLOYED | yes | H | Market-engine completeness (gate SC-4) |
| CHG-017 | Scope 3 taxonomy widened to all fifteen categories with contracts | `domain/scope3.py`, `scope3_contracts.py`; `p17d_*`; `7739ed7` | P17-IMPLEMENT-07 | WIRED | Domain, DB, API | NOT-DEPLOYED | yes | H | Category applicability deferred (PO) |
| CHG-018 | Estimation and assumption records become persisted entities | `domain/estimation.py`; `data/estimation_records.py`; `p17h_*` | P17-IMPLEMENT-08 | WIRED | Domain, DB | NOT-DEPLOYED | yes | H | — |
| CHG-019 | Product-contract reporting dimensions | `p17_10_*`; `0f248ad` | P17-IMPLEMENT-10 | PERSISTED | DB, domain | NOT-DEPLOYED | yes | H | Applicability stopped for a PO decision |
| CHG-020 | Governed capability vocabulary: seven values mapped from architecture status | `domain/disclosure.py`; `p17k_*`; PO DECISION-03 §5.3 `M-1` | P17-K | PERSISTED | DB, domain | NOT-DEPLOYED | yes | H | A second vocabulary must not be invented (`F-2`) |
| CHG-021 | Capability truth surface separated from customer category applicability | `CT-PO-P17-L-*`; `P17-DECISION-01` (`PO-3`) | P17-L | WIRED | API, UI | NOT-DEPLOYED | yes | H | Is any applicability surfaced to customers? |
| CHG-022 | Durable, resumable, idempotent automatic processing | `v3m9_durable_automatic_processing`; worker; AGENTS §19 | Phase A–C `17665d0` | WIRED | DB, worker, API | LIVE-UNKNOWN | no | H | Duplicate-snapshot prevention exercised live? |
| CHG-023 | Audit immutability (ledger and activity) | `p7_audit_immutability_and_indexes`; `audit_activity_immutability` | Phase 7 | PERSISTED | DB | LIVE-UNKNOWN | no | H | Any update path still open? |
| CHG-024 | RLS hardening programme (anon/authenticated grant containment, group enablement) | `p8_rls_anon_grant_containment`; `p8_rls_4a1b`; `p8_rls_4a2`; `p8_rls_4b_group1_enablement` | Phase 8 RLS | PERSISTED | DB policies | 4b NOT-DEPLOYED | no | H | Which RLS groups remain un-enabled? |
| CHG-025 | Factor governance and internal containment of factor data | `p17a_*`; `p8_d4_emission_factors_internal_containment` | P8/P17 | PERSISTED | DB, domain | NOT-DEPLOYED | yes | H | — |
| CHG-026 | Storage boundary: private documents bucket with policy | `d32_private_documents_storage` | D32 | PERSISTED | Storage, DB | LIVE-UNKNOWN | no | H | Bucket and policy verified live? |
| CHG-027 | Evidence traceability made explicit (line items + provenance links) | `d33_evidence_traceability`; `p8_b2_*` | D33 + P8-B2 | PERSISTED | DB, UI | B2 NOT-DEPLOYED | no | H | — |
| CHG-028 | Report disclosure lifecycle and frozen artefacts | `p8_b1_*`, `p8_b3_*`, `p8_b4_*`, `p8_s2_*` | Phase 8 B/S | PERSISTED | DB, API | NOT-DEPLOYED | no | H | — |
| CHG-029 | AI Insight stack layered I1→I4 with independent verification | `p8_i1..i4_*`; OHD verification records | Phase 8 Insight | WIRED | DB, API, UI | NOT-DEPLOYED | no | H | Where does answer generation stand? |
| CHG-030 | Operational telemetry and configurable retention policy | `p8x_x2_*`; `services/retention.py` | Phase 8X | WIRED | DB, service | NOT-DEPLOYED | no | H | Retention durations are a PO decision |
| CHG-031 | Public-truth hardening: build provenance, admin config gate, security headers | `cb70fd6`; `vercel.json`; `buildInfo.js` | P18-02 2026-09-26 | WIRED | Frontend, admin, config | **PV** | no | H | — |
| CHG-032 | Destructive integration-harness target guard (F-046-1) | `backend/tests/integration/conftest.py`; AGENTS §55.1 | P16 | WIRED (refuses qa/demo/investor/prod targets) | Tests | N/A | no | H | Pre-existing; unchanged by this census |
| CHG-033 | Product Owner decision register established as the governance baseline | `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`; reference index | 2026-08-26 | DOCUMENTED, current | Governance | N/A | no | H | Is the register kept current? |
| CHG-034 | Master workplan and authorisation framework | `CT-PO-MASTER-WORKPLAN-20260925.md` | 2026-09-25 | DOCUMENTED, ACTIVE; production deployment NOT AUTHORIZED | Governance | N/A | no | H | Current authorisation state for P17 release |
| CHG-035 | Three-agent development cycle (OHD/QA → backlog → Cline → QA) | AGENTS §58–61; `docs/ohd/**`, `docs/audit/**`, `docs/verification/**` | programme-level | In use | Process | N/A | no | H | — |
| CHG-036 | Evidence states formalised (IMPLEMENTED ≠ TESTED ≠ VERIFIED ≠ ACCEPTED ≠ PRODUCTION READY) | AGENTS §73; P17-L §1.3 verification-state table | P17-L | Adopted | Governance | N/A | no | H | — |


## 8. Issue register

## 8. Issue register

Discovered issues, including but not limited to the live regression. Severity
is an evidence-based impact class, not a product decision: **S1** = blocks a
core business workflow, **S2** = blocks a role/surface or defeats a control,
**S3** = correctness/quality risk or verification gap, **S4** = hygiene,
**INFO** = observation.

| ID | Issue | Class | Evidence | Sev | Impact | Status |
|---|---|---|---|---|---|---|
| ISS-001 | **Live regression: Google/Gmail authentication succeeds but the application then reports "Error: Failed to load your workspace. Please try again." followed by "Redirecting to login..."** | Live defect | Registered by this census as required; observed in the live application | **S1** | A user who authenticates cannot reach their workspace at all | **OPEN — root cause NOT investigated here** (a separate forensic task is authorised for this) |
| ISS-002 | Production database migration ledger state is unverifiable from this environment, and has previously drifted | Governance/deployment | `docs/operations/MIGRATION_DRIFT_GATE_RUNBOOK.md` ("production once carried 21 of 68 migrations"); `CT-P8-I2-PRODUCTION-DEPLOYMENT-STATE-20260921.md` (`UNKNOWN`) | **S2** | Code requiring missing objects can deploy and fail at query time | OPEN — PO-authorised migration gate required |
| ISS-003 | `tools/seed_investor_demo/` (incl. `DEMO_IDENTITIES.md`, the 1,185-identity manifest) exists only in the historical tree; `AGENTS.md` §54 still cites it as the normative manifest | Documentation/code divergence | `find` in both trees; AGENTS.md §54 | S2 | Agents instructed to use a manifest absent from the release tree | OPEN — PO decision on porting |
| ISS-004 | 407 legacy endpoints remain dual-mounted alongside 395 V3 endpoints | Architecture/debt | `backend/main.py:212-259`; `backend/routes/**` | S2 | Two authorisation models and two data models reachable in production; security surface ~2× | OPEN — PO decision (retirement policy) |
| ISS-005 | V3 router import is optional at boot; failure silently degrades to legacy-only | Reliability | `backend/main.py:23-34`; true ops quick reference §3 | S2 | A partial deploy can present a legacy application as if healthy | OPEN — evidence question: does production detect this? |
| ISS-006 | Admin console is not operational: Supabase build settings absent, so it renders a config notice | Deployment config | P18-04 verification (admin bundle `main.c9f8b964.js`; `/admin` notice) | S2 | The internal control plane cannot be used | OPEN — operator action (deployment configuration, not code) |
| ISS-007 | Six P17 migrations are unapplied live while P17 code is on the release branch | Deployment/schema | §6 P17 rows; master workplan (production DB mutation NOT AUTHORIZED) | S2 | P17 surfaces fail at query time if reached in production | OPEN — PO decision (production-migration gate) |
| ISS-008 | `migration-drift` CI run failed at startup with 0 jobs (pre-existing) | CI | Push-triggered run `36244749061` (recorded by P18-04) | S3 | The release gate does not actually run | OPEN — workflow repair required |
| ISS-009 | 32 files of substantive uncommitted work in the historical tree, with no canonical counterpart | Change loss risk | `git diff --ignore-all-space` (32 files, 774 insertions) | **S2** | A second, divergent revision of `calculation.py`, `automatic_processing.py` and admin pages exists outside version control | OPEN — PO decision (abandon, port or retire) |
| ISS-010 | QA harness is BUILD-ONLY and has never been run against the application; findings store holds 2 files | Verification gap | `qa_harness/README.md`; `qa_harness/findings/**` | S2 | AGENTS §51–53 independent automated QA is not yet delivered | OPEN — authorisation decision |
| ISS-011 | No `render.yaml`, `Dockerfile` or `Procfile`; Render build/start settings are not in the repository | Deployment provenance | repository scan; Render config record §2 | S3 | Backend deployment is not reproducible from the repository | OPEN |
| ISS-012 | OCR (tesseract) is an environment dependency with no container definition | Environment | `tools/provision_tesseract_local.sh`; `OCR_MAX_PAGES`; no Dockerfile | S2 | PDF/scan processing may fail in production silently | OPEN — verify the live image |
| ISS-013 | `ReportLifecyclePanel.jsx` exists only as untracked code in the historical tree | Code provenance | `git status` (untracked) in `~/carbon_tally` | S3 | A report-lifecycle UI panel is not in version control | OPEN |
| ISS-014 | Production database, QA database and investor-demo database identities are not distinguishable from the repository | Safety | AGENTS §55.1; `e2e/environment/README.md` (demo = `carbon_ledger` 54425/54426; e2e = `carbontally_e2e` 55325/55326) | S3 | Mis-targeted destructive runs are possible without the F-046-1 guard | Mitigated in code by F-046-1; operational discipline still required |
| ISS-015 | Historical tree's remote-tracking refs are stale (`origin/p8-release-reconciled` = `93d5cddd`, live = `cb70fd6`) | Hygiene/observation | `for-each-ref` in `~/carbon_tally`; `ls-remote` | S4 | Distance measurements taken from that tree are wrong until fetched | OPEN (do not fetch without instruction) |
| ISS-016 | Two `openhands/*` branches and one `posthog-self-driving/*` branch (+ PR #1) are unmerged in the repository | Branch hygiene | `ls-remote`; `refs/pull/1/head` | S4 | Unmerged work of unknown state | OPEN — PO/engineering decision |
| ISS-017 | `p8-release-reconciled` is 64+ commits of unreleased work relative to the deployed branch tip it replaced, and is unmerged into `main` | Release management | `merge-base`/ancestry measurements §4.1 | S3 | `main` does not represent what customers receive | OPEN — PO decision |
| ISS-018 | 1,659 commits are reachable only through 553 `refs/cline/checkpoints/*` refs | Repository hygiene | `for-each-ref`; `rev-list --all` set arithmetic | S3 | Repository size and history clarity; audit tools may miscount history | OPEN — do not prune without instruction |
| ISS-019 | `AGENTS.md` differs between the trees (29 delta lines) | Documentation divergence | `diff` of `AGENTS.md` | S3 | Agents may apply different constitutions depending on checkout | OPEN |
| ISS-020 | Two empty untracked files (`8`, `=`) exist at the canonical repository root | Hygiene | `stat`/`file` on both paths (0 bytes) | S4 | Shell-redirect litter; noise in status output | OPEN — created by an earlier session, not this one |
| ISS-021 | `.p18_audit_tmp/` (browser profiles, `live_453.js`) and `.costrict/` are untracked in the canonical tree | Hygiene/evidence | `git status`; file listing | S4 | Working-tree litter from prior audit runs | OPEN |
| ISS-022 | `.gitignore` is the canonical tree's only tracked modification (pre-existing) | Hygiene | `git status --porcelain` | S4 | Uncommitted configuration change of unknown intent | OPEN — preserved unmodified by this census |
| ISS-023 | Doc/code divergence: blueprint feature lists describe roles and capabilities absent from the implementation | Documentation | `docs/CarbonTally Complete Customer Feature List.md`; `docs/featurellist.md` | S3 | Readers may believe unimplemented features exist | OPEN — mark status in the reference index |
| ISS-024 | Doc/code divergence: `AGENTS.md` §41 "D17 master data UX" governs Facilities/Locations/Assets/Vehicles/Suppliers, but no D17 decision record was located in `docs/architecture` by filename search | Documentation | filename search of `docs/architecture` | S4 | The named frozen decision cannot be traced by ID | OPEN — locate or record the D17 record |
| ISS-025 | Duplicate implementations: manual entry (3 JSX variants), metadata (legacy + V3), messaging (legacy chat + V3), reports (legacy + V3), issues (legacy + V3) | Duplicate code | §6 rows CAP-024, CAP-039, CAP-091, CAP-099, CAP-055 | S3 | Divergent behaviour and duplicate maintenance | OPEN — PO/engineering decision |
| ISS-026 | Verification gap: `qa_harness/scripts/run_all.py`, the DB/API/browser/workflow suites and every frontend suite in this census were **not executed** | Verification gap | §2.4; no database target authorised | S3 | All "E2E VERIFIED" claims here rest on repository test presence, not on a run | OPEN — requires an authorised, disposable target |
| ISS-027 | Test-count ≠ test-pass: 3,672 backend test functions exist, but no suite was run for this census; P16 recorded 9 failures (3,322/3,342 passed, 11 skipped) | Verification gap | `CT-PO-MASTER-WORKPLAN-20260925.md` §2 | S3 | Green-suite assumptions are unsafe | OPEN |
| ISS-028 | `docs/audit` contains 197+ files across `cline` (71) and `openhands` (many) plus subdirectories; their findings are historical unless re-verified | Evidence age | directory counts | S3 | Stale findings can be mistaken for current defects | OPEN — re-verification policy |
| ISS-029 | `frontend_backup_pre_v3_public_20260827/` (235 files) is a full frozen pre-V3 frontend copy inside the release tree | Hygiene/artifact | directory listing | S4 | Build/scan tooling may traverse it | OPEN |
| ISS-030 | `prisma/schema.prisma` pins a local datasource URL and duplicates the schema outside the authoritative migration set | Config/tooling | `prisma/schema.prisma:10-13` | S3 | A second schema source could drift from `supabase/migrations` | OPEN — is Prisma tooling still used? |
| ISS-031 | `src/` (DEFRA and SEAI provider CLIs) and `backend/engines/*` both contain factor-matching logic; the CLI providers are outside `backend/` and outside the API process | Architecture | `src/providers/*`; `engines/factor_matching.py` | S3 | Factor import path may bypass API-level governance | OPEN |
| ISS-032 | Security observation: the CSP is deployed as `Content-Security-Policy-Report-Only` while the enforced policy is a four-directive subset | Security | `vercel.json` headers | S3 | Reported violations are not blocked | OPEN — PO/security decision to enforce |
| ISS-033 | Security observation: `object-src`/`frame-ancestors`/`form-action` are enforced but no `default-src` is enforced | Security | `vercel.json` | S3 | Weaker than intended posture | OPEN (same decision as ISS-032) |
| ISS-034 | Observation: P18 published frontend only; the backend revision serving production is **not** the release branch tip | Deployment mismatch | P18-04 report (no backend redeploy); §10 | S3 | The verified frontend and the running API may be different revisions | OPEN — PO decision (backend release) |
| ISS-035 | Observation: the six `p17*` migrations are the only ones explicitly gated; 15 further canonical-only migrations (P8/P16) also have unknown live state | Deployment/schema | §4.4 comparison | S3 | Scope of the migration decision may be wider than six | OPEN — PO decision |
| ISS-036 | Observation: `docs/architecture` holds 399 documents with no machine-readable index of authority tier for the newest 100+ | Documentation | `ls -t docs/architecture` | S4 | Agents may rely on the wrong tier | OPEN |


## 9. Dependency clusters

## 9. Dependency clusters

The census found **seven** load-bearing dependency clusters. A failure anywhere
in a cluster degrades everything downstream of it.

### 9.1 P17 migration cluster (largest, and the only PO-gated one)

```
p17a  accounting dimensions + factor governance ─┐
p17c  contractual instruments + allocations     │
p17d  scope3 category taxonomy                  ├─→ domain/cams.py, scope2.py, scope3.py,
p17h  estimation + assumption records           │   scope3_contracts.py, accounting_dimensions.py,
p17_10 product-contract reporting dimensions    │   acting_for.py, contractual_instruments.py,
p17k  governed capability catalogue (18 rows) ──┘   estimation.py, capability_catalogue.py
                                                 │
                                                 ├─→ api/v3_scope2.py, v3_scope3.py,
                                                 │   v3_accounting_context.py, v3_disclosure.py,
                                                 │   v3_suppliers.py (write path)
                                                 │
                                                 └─→ UI: /capabilities, /capabilities/product,
                                                     capability truth surface
```

Everything downstream is `WIRED` in code, `PERSISTED` in the repository, and
**`NOT-DEPLOYED` live**. No migration in this cluster was applied by this task.

### 9.2 Legacy dual-mount cluster

`backend/main.py` → legacy `backend/routes/**` (407 endpoints) **and** V3
`backend/api/router.py` (395 endpoints), sharing one database. Consequences
observed: duplicate manual entry (3 variants), duplicate metadata, duplicate
messaging, duplicate reports, duplicate issues, two authz models (server-side
V3 authz + legacy route checks) over the same RLS.

### 9.3 Phase 8 disclosure/report cluster

`p8_b1_*` → `p8_b2_*` → `p8_b3_*` → `p8_b4_*` → `p8_s2_*`, plus
`p8_report_lifecycle_status` and `p16r5_result_reportability_lifecycle`
(CAP-084…CAP-091). The P17 capability catalogue projects into this same
vocabulary — explicitly *not* a second model (`F-1`, `F-2`).

### 9.4 Phase 8 Insight cluster

`p8_i1` → `p8_i2` → `p8_i3` (tool catalogue) → `p8_i4` (interactions), with
`p8_insight_discovery_aggregation_rate_limit`, temporal comparison and
data-quality reproducibility alongside. Layered by PO authorisation, not by
release.

### 9.5 Evidence and provenance cluster

`d33_evidence_traceability` → `p8_b2_evidence_line_items` →
`p8_b2_provenance_line_links` → audit ledger (`p7_*`, `audit_activity_immutability`)
→ `gate4_actor_provenance`, `gate5_t1_automation_provenance`,
`gate5_t6_automation_write_once_guard`, `gate6_w1_automation_extracted_output`
→ P17 acting-for attribution. The AGENTS §17 provenance chain depends on the
whole of it.

### 9.6 Identity and tenancy cluster

`rc2_rls` → `v3m1/v3m2/v3m6` (entities + entity RLS) → `v3m8` (system admin, PE
manager) → `v3m10` (membership uniqueness) → `d20_d15` (active consultant grant)
→ `tenant_org_id_not_null` → `p9_rls_recursion_fix` → `p8_rls_*` hardening.
Every role boundary (customer, consultant, client, PE, internal staff) resolves
through this cluster.

### 9.7 Verification cluster (the weak link)

`qa_harness` (BUILD-ONLY, never run) + frontend/admin Jest suites (not run here)
+ Playwright config at root + `e2e/environment` (isolated stack) + `backend/tests`
(3,672 test functions, not run here) + `.github/workflows/migration-drift.yml`
(failing at startup). **Independent automated verification of the live platform
is therefore not yet available**, which is exactly what `AGENTS.md` §51–§53
requires.

### 9.8 Tooling that exists only in the historical tree

`tools/seed_investor_demo/` (incl. the identity manifest), `tools/p2_census/`,
`tools/carbon_data_factory/`, `agent_swarm/`, `agent_swarm_v2_artifacts/`,
`saas-assurance/`, `independent_audit/`, `qa_harness/{findings,reports,evidence}`,
`screenshots/`, `local_backups/`, `myenv/`, `carbon_tally/` and `carbontally/`
(nested Python virtualenvs), `uploads/`, `output/`, `admin-dashboard.zip`,
`backend - backup.zip`.

## 10. Deployment census

## 10. Deployment census

### 10.1 Current live state (as recorded by the immediately preceding P18-04 task)

| Surface | Live value | Evidence quality |
|---|---|---|
| Frontend host | Vercel, path `/` (public + authenticated) | Direct (HTTP + deployment API) |
| Frontend Production deployment | `6679336317`, `vercel[bot]`, status `success`, `2026-09-26T13:20:23Z` | Direct |
| Deployed SHA | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` (ref = same SHA) | Direct |
| Deployment URL | `https://carbon-tally-1l8sht7f3-shomonrobies-projects.vercel.app` | Direct |
| Previous Production deployment | `6656505133`, `2026-09-25T08:10:25Z`, sha `98a89d0c1…` | Direct |
| Live public bundle | `main.5f9a4b10.js` (provenance-pinned, published pre-render) | Direct |
| Live admin bundle | `main.c9f8b964.js` | Direct |
| Live admin state | Renders **P18-02 config notice**; old test branding absent | Direct |
| Live security headers | 6/6 byte-exact vs committed `vercel.json` (pre-push: 0/6) | Direct |
| GitHub branch | `p8-release-reconciled` = `cb70fd6` (fast-forward from `98a89d0`) | Direct |
| Backend | **Not redeployed** for P18; API cold-start 503 → 200 (suspended instance) | Direct |
| Database | **No operation performed** by P18-04 or by this census | Direct (no connection attempted) |
| Admin deployment config | `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY` absent → console inoperative | Direct (ISS-006) |

### 10.2 Migration deployment state

| Migration group | Repository | Applied live |
|---|---|---|
| Through `20261009000000_p16r7_*` | present | `UNKNOWN` (never verified from this environment) |
| Six `p17*` migrations (`20261010000000` … `20261020000000`) | present | **NOT applied — PO-gated** |
| 15 further canonical-only migrations (P8/P16 group) | present | `UNKNOWN` — wider than the six explicitly gated (ISS-035) |
| Production ledger | not readable here | `UNKNOWN`; historically drifted (21 of 68 per the WP-8 runbook) |

### 10.3 Known production observations carried forward

* API instance is **suspended when idle** (cold-start 503 before 200) — operational
  behaviour, not a defect, but it affects any "is the platform up?" check.
* The CSP is report-only (ISS-032/ISS-033).
* Render service configuration is **not** represented in the repository (ISS-011).
* `migration-drift` CI fails at startup with 0 jobs (ISS-008).

### 10.4 Deployment relationship summary

```
GitHub main (2f56562)  ──┐
                         ├── ancestor of ──→ GitHub p8-release-reconciled (cb70fd6)
GitHub p8-release-reconciled ── Vercel Production 6679336317 (frontend only)
GitHub p8-release-reconciled ── ✗ no backend deploy
GitHub p8-release-reconciled ── ✗ no migration application
```

**Production therefore runs: current frontend + an unverified backend revision +
a database whose schema state is unknown.** That mismatch is the single most
important deployment fact in this census.

## 11. Uncertain items and Product Owner decisions required

## 11. Uncertain items and Product Owner decisions required

**No Product Owner decision is taken by this census. Every row below is
`UNKNOWN` by design.**

### 11.1 Uncertain (evidence could not settle the question)

| ID | Uncertain item | Why it is unresolved |
|---|---|---|
| UNC-001 | Production database migration ledger contents | No database access is permitted in this task |
| UNC-002 | Which backend revision Render is currently serving | No Render credential, no `render.yaml`; not inferable from Git |
| UNC-003 | Whether the 32 historical-tree work files were superseded or lost | No canonical counterpart commit was found for them |
| UNC-004 | Whether P17 surfaces are reachable in production today | Frontend routes exist; backend revision and schema state are both unknown |
| UNC-005 | Whether the capability truth surface renders live | Depends on UNC-002 and UNC-004 |
| UNC-006 | Whether the investor demo dataset (1,185 identities) still exists in its database | Requires database access; the seeder is absent from the release tree |
| UNC-007 | Whether every canonical-only migration beyond the six is applied | Ledger unknown (UNC-001) |
| UNC-008 | Whether tesseract is installed in the live backend image | No container definition in the repository |
| UNC-009 | Whether the legacy API surface is still exercised by any live client | No access logs available read-only |
| UNC-010 | Whether `v3_insight*`, `operational_alerting`, `extraction_fidelity` etc. are reachable by any route at all | `CODE-ONLY` classification is based on registration tables, not runtime introspection |
| UNC-011 | Whether the PostHog/GA4 analytics configuration is active live | Requires runtime config access |
| UNC-012 | Whether the demo lab and isolated E2E stack are still operable | No execution attempted |
| UNC-013 | Whether any of the 553 `refs/cline/*` checkpoints contains work not present in a branch | Set arithmetic shows no branch-only loss, but individual checkpoint contents were not diffed |
| UNC-014 | Whether the D17 frozen master-data UX decision exists as a document | Filename search found no D17 record (ISS-024) |

### 11.2 Product Owner decisions required

| ID | Decision required | Evidence that forces the decision | Options (not chosen here) |
|---|---|---|---|
| POD-001 | Is the **P17 backend release** authorised? | Six P17 migrations + all P17 code are unreleased; master workplan says production deployment NOT AUTHORIZED | release / defer / partial |
| POD-002 | Is the **production migration gate** authorised for the six `p17*` migrations? | ISS-007; drift history ISS-002 | apply 6 / apply all 21 / defer |
| POD-003 | What is the **disposition of the 32 uncommitted historical-tree files**? | ISS-009 | abandon / port into canonical / archive |
| POD-004 | Should `tools/seed_investor_demo/` and `DEMO_IDENTITIES.md` be **ported into the canonical tree**? | ISS-003 (AGENTS §54 cites an absent artefact) | port / remove the AGENTS reference / leave |
| POD-005 | What is the **legacy API retirement policy** (407 endpoints)? | ISS-004 | retire / freeze / keep |
| POD-006 | Is the **QA harness** authorised to run, and against which target? | ISS-010, ISS-026 | authorise on disposable clone / keep BUILD-ONLY |
| POD-007 | Should `p8-release-reconciled` be **merged to `main`**? | ISS-017 | merge / keep separate |
| POD-008 | Should the CSP be **enforced** rather than report-only? | ISS-032, ISS-033 | enforce / retain report-only |
| POD-009 | Are the **retention durations** to be configured (and which domains first)? | CHG-030; AGENTS §42 forbids inventing durations | configure / defer |
| POD-010 | Is the **P17-K seven-value capability vocabulary** the single canonical vocabulary? | CHG-020, CAP-070 (`F-1`/`F-2` prohibit a second model) | ratify / redefine |
| POD-011 | Should the **admin console** be made operational (Supabase build settings)? | ISS-006 | configure / leave |
| POD-012 | What is the **beta programme's fate** (PO Register §1.3 says retire obsolete beta)? | CAP-013 | retire / retain |
| POD-013 | Are the **pilot/prototype tooling artefacts** (UI mockups, legacy admin dashboard, Prisma lineage, `carbon-tally-ui-demo`) to be retained? | ISS-029, ISS-030, CAP-143…CAP-145 | retain / archive / remove |
| POD-014 | Which **verification regime** should re-verify this census independently (OHD / CoStrict / other)? | ISS-026, ISS-027 | nominate |
| POD-015 | Does the **live workspace-load regression (ISS-001)** take priority over P17 release work? | ISS-001 | prioritise / parallel |
| POD-016 | Should the **historical tree be reconciled** (fetched, branched or archived) rather than left divergent? | ISS-015, ISS-019 | reconcile / archive / leave |
| POD-017 | Which **role capability matrix** is authoritative for internal staff (operator/reviewer/QC/staff admin/system admin)? | CAP-021 | ratify matrix / leave to code |
| POD-018 | Are the **sales-blueprint feature lists** to be marked as non-implemented? | ISS-023 | annotate / remove / publish roadmap |

## 12. Safety verification

## 12. Safety verification

### 12.1 Read-only attestation

| Rule | Result |
|---|---|
| Application/frontend/admin/backend source modified | **NO** |
| SQL or migration modified | **NO** |
| Supabase schema or RLS policy modified | **NO** |
| Configuration modified | **NO** |
| Deploy / push / merge / rebase / reset / cherry-pick / amend performed | **NO** |
| Files deleted or renamed | **NO** |
| Packages installed | **NO** |
| Migrations executed | **NO** |
| Database write or read performed | **NO** (no connection attempted) |
| Records created in any database | **NO** |
| Git history altered | **NO** |
| Anything "cleaned up" | **NO** |
| Product decision taken | **NO** |
| Secret, token, credential, JWT or signed URL recorded | **NO** |

### 12.2 Files created by this task (all new; all documentation)

1. `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md`
2. `docs/architecture/CT-PO-CARBONTALLY-CAPABILITY-AND-RELEASE-LEDGER-20260926.md`
3. `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926-REPORT.md`

All three are **untracked** additions in the canonical tree. No pre-existing file
was modified. Temporary inspection output was written only to `/tmp/*` and was
not placed in either repository.

### 12.3 Start/end state comparison

| Item | At start | At end | Match |
|---|---|---|---|
| Canonical branch | `p8-release-reconciled` | `p8-release-reconciled` | ✅ |
| Canonical HEAD | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | ✅ |
| Canonical tracked modifications | 1 (`.gitignore`, pre-existing) | 1 (`.gitignore`, unchanged) | ✅ |
| Canonical reflog tip | `cb70fd6 HEAD@{2026-09-26 16:19:11 +0600}: commit: fix(public-truth)…` | unchanged | ✅ |
| Historical branch | `main` | `main` | ✅ |
| Historical HEAD | `20b7a928bb73fdfacf8271ff537a8fd245f62c79` | `20b7a928bb73fdfacf8271ff537a8fd245f62c79` | ✅ |
| Historical tracked modifications | 227 | 227 | ✅ |
| GitHub remote refs | `main` = `2f56562…`, `p8-release-reconciled` = `cb70fd6…` | unchanged (read-only `ls-remote`) | ✅ |

### 12.4 Evidence-handling note

Facts about the live artefact in §10 are **copied from the immediately preceding
P18-04 publication/verification task's final report** and are labelled as such.
This census did **not** perform any HTTP request against production, so the live
values are second-hand in this document and should be treated as
`recorded by the deploying agent`, not independently re-measured here.

## 13. Verdict

## 13. Verdict

### 13.1 Required census totals

| Required figure | Value |
|---|---|
| Exact HEAD inspected (canonical) | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` on `p8-release-reconciled` |
| Exact HEAD inspected (historical) | `20b7a928bb73fdfacf8271ff537a8fd245f62c79` on `main` |
| Repositories inspected | 2 (`/home/shomonrobie/ct_93d5cdd`, `/home/shomonrobie/carbon_tally`) |
| GitHub refs inspected | 9 branch/PR refs + 3 tags (read-only) |
| Historical sources inspected | historical working tree (tracked + 78 untracked paths), 5 local branches, 553 `refs/cline/*` refs, 3 tags, 399 architecture docs, 269 `docs/cline` artefacts, 197+ `docs/audit` artefacts |
| **Capabilities discovered** | **152** (`CAP-001` … `CAP-152`) |
| **Significant changes discovered** | **36** (`CHG-001` … `CHG-036`) |
| **Issues discovered** | **36** (`ISS-001` … `ISS-036`) — 1 live S1 regression, 8 S2, 21 S3, 6 S4 |
| **Uncertain items** | **14** (`UNC-001` … `UNC-014`) |
| **Items requiring a PO decision** | **18** (`POD-001` … `POD-018`) |
| Dependency clusters | **7** load-bearing + 1 tooling-only (§9.1–§9.8) |
| Major P17 dependencies | Six migrations (`p17a`, `p17c`, `p17d`, `p17h`, `p17_10`, `p17k`) → 29 backend modules → 4 API surfaces → 3 UI surfaces (CAP-052, CAP-061…CAP-070, CHG-013…CHG-021) |

### 13.2 Production-versus-code discrepancies (the headline findings)

1. **Frontend deployed; backend and schema not.** Vercel serves `cb70fd6`, while
   the Render backend was not redeployed for P18 and the six `p17*` migrations
   are not applied. The running system is therefore a *mix* of revisions.
2. **Six P17 migrations gate ~30 wired capabilities.** They are the largest
   single blocker to the P17 feature set going live.
3. **407 legacy endpoints are still dual-mounted** beside 395 V3 endpoints in the
   same process, over the same database.
4. **The admin console is deployed but inoperative** (missing Supabase build
   settings) — the internal control plane is not usable.
5. **The live workspace-load regression (ISS-001)** means an authenticated user
   can currently fail to reach their workspace at all.
6. **The verification layer that AGENTS §51–§53 mandates does not yet exist in
   operational form**: the QA harness is BUILD-ONLY, the migration-drift CI gate
   fails at startup, and no suite was run for this census.
7. **The investor-demo identity manifest normative in `AGENTS.md` §54 is absent
   from the release tree**, and 32 files of substantive work (including
   accounting-logic edits) exist only as uncommitted changes in the historical
   tree.

### 13.3 Known live regression (registered only)

```
Symptom  : Google/Gmail authentication succeeds, then the live application shows
           "Error: Failed to load your workspace. Please try again."
           then "Redirecting to login..."
Severity : S1 (blocks the core authenticated workflow)
Status   : REGISTERED — OPEN
Scope    : registered only; root cause deliberately NOT investigated here
Owner    : a separate, authorised forensic task
```

### 13.4 Files created

| # | Path (canonical tree) | Purpose |
|---|---|---|
| 1 | `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md` | Primary deliverable — this census |
| 2 | `docs/architecture/CT-PO-CARBONTALLY-CAPABILITY-AND-RELEASE-LEDGER-20260926.md` | Decision ledger (PO/release columns all `UNKNOWN`) |
| 3 | `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926-REPORT.md` | Implementation/forensic report (method, evidence, limits, safety) |

### 13.5 Confirmation

**No implementation, no deployment, and no database change was made.** No source
file, migration, SQL, configuration or policy was altered; no push, merge or
commit occurred; no database was read or written; no migration was executed; no
product decision was taken. Both trees are byte-identical to their starting state
except for the three new untracked documents listed above.

### 13.6 Verdict

```
CT_RECON_01_COMPLETE_READ_ONLY_CENSUS
```

The census is complete: both repositories, all GitHub refs, the full reachable
history of both trees, the migration corpus, the route/module/page surfaces and
the governance corpus were inspected. Where evidence was unavailable (production
ledger, Render revision, live authenticated journeys) the item is recorded as
`UNKNOWN` rather than inferred, and the limitation is stated in §2.4 and §11.1.
