# CT-RECON-01 — Census Implementation & Forensic Report

**Task ID:** `CT-RECON-01-20260926-CARBONTALLY-COMPLETE-CAPABILITY-AND-CHANGE-CENSUS`
**Task type:** READ-ONLY FORENSIC DISCOVERY — **no implementation, no deployment, no database change**
**Date:** 2026-09-26
**Primary deliverable:** `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md`
**Secondary deliverable:** `docs/architecture/CT-PO-CARBONTALLY-CAPABILITY-AND-RELEASE-LEDGER-20260926.md`
**Canonical tree:** `/home/shomonrobie/ct_93d5cdd` — `p8-release-reconciled` — `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`
**Historical tree:** `/home/shomonrobie/carbon_tally` — `main` — `20b7a928bb73fdfacf8271ff537a8fd245f62c79`

---

## 1. Task identity and scope

### 1.1 What was asked

A read-only forensic product/engineering census of CarbonTally: discover the
**complete** set of capabilities, features, architectural changes, workflows,
integrations, data models, UI surfaces, unfinished work and historical
modifications across the CarbonTally development history — explicitly not
limited to features the Product Owner already remembered — and record them in a
master census, a decision ledger and this report, **without making any product
decision and without changing anything**.

### 1.2 What was done

The census was executed as a discovery task across two working trees, the
GitHub ref namespace, the migration corpus, the backend/frontend/admin code
surfaces, the tooling surfaces and the documentation corpus. It produced:

| Deliverable | Content |
|---|---|
| `CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md` | §0 reading rules · §1 executive summary · §2 methodology · §3 sources · §4 repository topology and history reconciliation · §5 the 64-commit range investigation · §6 capability census (152 rows × 16 columns) · §7 change census (36 rows) · §8 issue register (36 rows) · §9 dependency clusters · §10 deployment census · §11 uncertain items and PO decisions · §12 safety verification · §13 verdict |
| `CT-PO-CARBONTALLY-CAPABILITY-AND-RELEASE-LEDGER-20260926.md` | 152-row capability ledger (15 columns, including PO decision and release decision — both `UNKNOWN` throughout), PO decision register, release decision register, verification-state summary, sign-off |
| This report | Method, sources, commands, findings, limitations, evidence quality, totals, unresolved questions, safety verification |

### 1.3 Scope exclusions (deliberate, per task rules)

The following were **not** done, by instruction:

* root-cause investigation of the live workspace-load regression (registered as
  `ISS-001` only, with no investigation);
* fixing the admin console configuration;
* merging or reconciling branches;
* removing old or duplicate code;
* authorising or applying P17 migrations;
* any Supabase / Render / Vercel configuration change;
* any product decision.

---

## 2. Methodology

### 2.1 Investigation order (followed literally)

1. Read `AGENTS.md` (project constitution) from the working directory.
2. Record Git state for **both** trees before anything else.
3. Reconstruct the history and topology of both trees; identify divergence.
4. Inventory the code surfaces (backend, frontend, admin, tooling).
5. Inventory the database surface **statically** from migrations and the Prisma
   snapshot.
6. Read the governance corpus (PO decisions, master workplan, P16/P17 decisions
   and reports, runbooks, verification records) for authority and for claims to
   test against code.
7. Cross-check every claim against code; downgrade unverifiable claims to
   DOCUMENTED with confidence **L**.
8. Build the capability table, change table, issue register, clusters,
   deployment census, uncertainty list and PO-decision list.
9. Re-verify that nothing in either tree changed.

### 2.2 Why the census is "complete" in the sense the task intended

The task's warning was that a remembered feature list would be incomplete. The
census avoided that in three ways:

1. **It enumerated from the code**, not from documents: 809 route decorators,
   46 registered routers, 54 + 18 React route paths, 89 migrations, 49 domain
   modules, 15 engines, 52 repositories, 30 services, 156 V3 UI modules,
   8 `tools/` entries, plus the `qa_harness/` and `e2e/` trees.
2. **It enumerated from disk, not from Git**, in the historical tree — which is
   where 78 untracked paths live (whole tools directories, product code, and 32
   files of real modifications) that **no branch contains**.
3. **It enumerated from history**, including a cross-tree commit-set comparison
   that exposed 204 canonical-only commits, 1,659 checkpoint-only commits and
   21 canonical-only migrations.

### 2.3 Command categories actually used

| Category | Representative commands |
|---|---|
| Repository identity | `git symbolic-ref`, `git rev-parse`, `git remote -v`, `git status --porcelain`, `git branch -a`, `git tag`, `git reflog` |
| Remote inspection (read-only) | `git ls-remote github`, `git ls-remote origin` |
| History measurement | `git rev-list --count`, `git rev-list --all`, `git log --pretty=format:…`, `git log --oneline --no-decorate` |
| Ancestry and divergence | `git merge-base --is-ancestor`, `git merge-base`, `git rev-list --count A..B`, `comm` over sorted SHA sets |
| Ref enumeration | `git for-each-ref --format='%(objectname) %(objecttype) %(refname)'` |
| Tree comparison | `git diff --stat`, `--name-status`, `--numstat`, `--ignore-all-space --stat`, `git ls-tree -r --name-only <ref> -- path` |
| Cross-tree file comparison | `diff -q`, `diff | grep -c '^[<>]'` |
| Code census | `ls`, bounded `find`, `grep -rhoE '@router\.(get|post|put|patch|delete)'`, `grep -nE 'include_router'`, `grep -rhoE 'path="[^"]+"'`, `grep -cE '^(    )?(async )?def test_'` |
| Database census (static) | `grep -c 'CREATE TABLE'`, policy/function/index/type counts, migration filename set comparison (`comm`) |
| Documentation census | per-directory `find … | wc -l`, `ls -t`, targeted `head` / `sed -n` reads |
| File typing | `file`, `stat -c%s` |

**No command in this list writes.** No `git fetch`, `pull`, `checkout`, `add`,
`commit`, `push`, `reset`, `clean`, `stash` or `gc` was executed. No `psql`,
`supabase`, migration or seed command was executed. No package-manager command
was executed. No HTTP write was performed. Inspection output was redirected to
`/tmp/*` only, never into either repository.

### 2.4 Analysis discipline applied to discovered claims

* A commit message was **never** treated as proof that functionality exists.
* A document was **never** promoted above `DOCUMENTED` without code evidence.
* A migration in the repository was **never** treated as applied to a database.
* A test file's existence was **never** treated as a passing test.
* An old audit finding was **never** reported as a current defect without
  re-verification in the current tree.
* Where a document's assertion could not be tested (e.g. anything requiring the
  production database), the item was recorded as `UNKNOWN`.

---

## 3. Sources inspected

### 3.1 Trees, branches and refs

| Source | Detail |
|---|---|
| Canonical tree | `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6` on `p8-release-reconciled` (537 commits; 545 reachable; 208 reflog entries) |
| Historical tree | `/home/shomonrobie/carbon_tally` @ `20b7a928` on `main` (206 commits; 2,000 reachable; 5 local branches; 553 `refs/cline/checkpoints/*` refs) |
| GitHub refs | `main` `2f56562`, `p8-release-reconciled` `cb70fd6`, `openhands/analytics-ga4-admin-settings` `0bc203f`, `openhands/public-website-visual-refactor` `2fd4345`, `posthog-self-driving/…` `363105a`, `pull/1/head` `363105a`, `pull/1/merge` `954e97c`, tags `rc2-final`, `v2.1-phase4`, `v2.1.1-phase3` |
| Historical branches | `p8-release-reconciled` = `93d5cddd`, `fx12-publish` = `f1a1cf8`, two `openhands/*` |
| Migration corpus | 89 `.sql` in the canonical tree; 75 at `93d5cddd`; 68 at historical `main` |
| Static schema snapshot | `prisma/schema.prisma` (3,510 lines, 129 models) |

### 3.2 Code surfaces enumerated

`backend/{api,routes,services,domain,engines,workers,middleware,infra,core,data,utils,tools}`,
`frontend/src/**` (incl. `v3/**` 156 files, 16 sub-surfaces), `admin/src/**`
(18 routes, `pages/admin` 18 files), `src/**` (DEFRA/SEAI providers),
`tools/**`, `qa_harness/**`, `e2e/**`, `demodatagen/**`, `database/{rc1,rc2,v3}`,
`supabase/**`, `backups/**`, `shared/**`, `carbon-tally-ui-demo/**`,
`frontend_backup_pre_v3_public_20260827/**`.

### 3.3 Documentation corpus enumerated

`docs/architecture` (399), `docs/audit` (197+, incl. `cline` 71 and
`openhands` 18 top-level + subdirectories), `docs/cline` (269: 121 reports,
77 prompt-history), `docs/Final_Kimi` (94), `docs/implementation` (21),
`docs/verification` (12), `docs/standalone` (12), `docs/legal` (10),
`docs/operations` (6), `docs/ohd` (reports), `docs/business` (1),
`docs/ChatGPT` (5), `docs/Pricing` (5), `docs/sample_bills` (8),
`docs/demo-investor` (7), `docs/Final` (5), plus the five top-level
`docs/*.md` records (reference index, customer feature list, feature list,
todos, reconstructed task history) and `.github/workflows/migration-drift.yml`.

**Read in depth:** `AGENTS.md`; PO Decision Register v1;
`CARBONTALLY_V3_REFERENCE_INDEX.md`; `CT-PO-MASTER-WORKPLAN-20260925.md`;
`CT-PO-P17-L-CAPABILITY-TRUTH-SURFACE-20260926.md`; the P17-K migration;
`MIGRATION_DRIFT_GATE_RUNBOOK.md`; `CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md`;
`CARBONTALLY_TECHNICAL_OPERATIONS_QUICK_REFERENCE_V1.0.md`;
`CT-P8-I2-PRODUCTION-DEPLOYMENT-STATE-20260921.md`;
`CT-PO-P18-PUBLIC-TRUTH-04-…-PUBLISH-VERIFICATION-FINAL.md`;
`CARBONTALLY_LEGACY_ADMIN_INVENTORY.md`; `e2e/environment/README.md`;
`qa_harness/README.md`; `backend/api/router.py`; `backend/main.py`.

---

## 4. Findings

### 4.1 Repository topology

* The canonical tree is **not** a copy of the historical tree. It was seeded from
  `93d5cddd` (the suffix of its own directory name, and the historical tree's
  `p8-release-reconciled` branch) and then advanced by **204 commits that exist
  nowhere else**.
* `p8-release-reconciled` (`cb70fd6`) is a **strict descendant of GitHub `main`**
  (`2f56562`): `main` is an ancestor, HEAD is not an ancestor of `main`, and the
  merge-base is `main`'s own tip. The release branch is therefore a superset of
  `main` that has never been merged back.
* The historical tree's `main` (`20b7a928`) is **not** an ancestor of the
  canonical HEAD — the two `main` lineages diverged.
* The historical tree's `2,000` reachable commits are dominated by **553
  `refs/cline/checkpoints/*` refs** accounting for **1,659** commits. Real
  product history there is **341** commits (branches + tags + remotes).
* The historical tree's remote-tracking refs are **stale**
  (`origin/p8-release-reconciled` = `93d5cddd` versus a live `cb70fd6`), so any
  distance measurement made from that tree without a fetch is wrong.

### 4.2 History content (the 64-commit range and the 204-commit fork delta)

The 64-commit range `98a89d0..cb70fd6` (2026-09-25 → 2026-09-26) changed 131
files (+91 added, 40 modified, 0 deleted; 41,503 insertions, 46 deletions), and
contains: the P17 architecture freeze chain, P17-MASTER-01, P17-IMPLEMENT-02 to
IMPLEMENT-10, P17-K (governed capability catalogue), P17-L (capability truth
surface), P17-M2 (DEF-1 fix), the P17-M independent verification, and P18-02
(public-truth hardening). The wider 204-commit delta additionally contains the
P8 Insight and report-lifecycle body of work, Phase 8X operational telemetry,
the P12 investor-demo engineering, the P14 competitive coverage audit, and the
P16 core-accounting remediation.

### 4.3 Code surface

| Layer | Measured | Observation |
|---|---|---|
| API endpoints | **809** (`get` 442, `post` 258, `put` 71, `delete` 35, `patch` 3) | legacy 407 vs V3 395 — two coexisting models |
| Registered V3 routers | **46**, incl. `v3_accounting_context`, `v3_health`, `v3_activity_clarifications`, `v3_evidence`, `v3_insight`, `v3_insight_tools`, `v3_insight_interactions` | the P17/Insight routers are registered, so they boot |
| Frontend routes | **54** unique `path=` values | mixed public + legacy dashboard + V3 trees in one `App.js` (2,285 lines) |
| Admin routes | **18** | separate application, distinct surface, path-rewritten to `/admin` |
| V3 UI modules | **156** files across 16 sub-surfaces | design system, workbench, ops, pe, consultant, insight, capabilities, evidence, reports, messaging |
| Duplicate implementations | manual entry ×3, metadata ×2, messaging ×2, reports ×2, issues ×2, admin ×2 lineages | consequence of the dual-mount |

### 4.4 Database surface (static only)

* **89** migrations; **156** `CREATE TABLE` statements (**146** distinct names);
  **112** `CREATE POLICY` (**85** distinct names); **34** functions; **221**
  indexes; **1** `CREATE TYPE`.
* **40** capabilities are repository-persisted; **none** of them is claimed
  applied.
* The canonical migration set is a **strict superset** of the historical tree's:
  21 migrations exist only in the canonical tree (six `p17*`, six `p8_i*`/Insight,
  three `p8_fs_*`, `p8_fin06`, `p8_d4`, `p8_rls_4b`, `p16r5`, `p16r7`).
* The Prisma snapshot documents **129** models across `auth` and `public` — a
  useful independent cross-check of the declared surface, but it is **not** the
  authoritative schema (`supabase/migrations` is).

### 4.5 The historical working tree (the most consequential finding)

`git status` in `~/carbon_tally` reports **227 tracked modifications** and
**78 untracked paths**. Measured with `--ignore-all-space`, the tracked
modifications are **32 files / 774 insertions / 71 deletions** of real change;
the other ~195 files (all 69 `.agents/skills/**`, all 29
`tools/carbon_data_factory/**`, `v1.9.txt` with 2,700 changed lines,
`test_results*.json`) are **pure line-ending churn** (CRLF work-tree files
against LF index blobs).

The 32 real files include accounting- and operations-critical code with **no
counterpart commit in the canonical tree**:

```
backend/engines/calculation.py            154 delta lines
backend/domain/calculation.py              13
backend/services/automatic_processing.py  893
backend/services/automatic_extraction.py
backend/domain/automatic_processing.py
backend/data/emissions_logs.py, manual_extraction.py
backend/api/v3_operations.py, v3_reports.py
frontend/src/App.js                        74
frontend/src/v3/api.js, reports/ReportDetailPage.jsx, reports/reports.css
admin/src/pages/admin/{Users.js 1221, Settings.js, BetaManagement.js}
admin/src/{context/AuthContext.js, index.js}
admin/src/components/admin/{ImportDefraModal,ReviewExtractionModal,ReviewWorkflow}.js
requirements.txt, supabase/config.toml, CarbonTally_DB_Schema_V3M2.sql, AGENTS.md
```

Untracked **product** code in that tree includes
`frontend/src/v3/reports/ReportLifecyclePanel.jsx` (+ test) and
`admin/src/analytics.js`. Untracked **tooling** includes
`tools/seed_investor_demo/**` (30 files, incl. the 1,185-identity
`DEMO_IDENTITIES.md` that `AGENTS.md` §54 makes normative — **absent from the
canonical tree**), `tools/p2_census/`, `agent_swarm/`, `agent_swarm_v2_artifacts/`,
`saas-assurance/`, `qa_harness/{findings,reports,evidence}`, and `.github/`.

### 4.6 Deployment and operational findings

* Vercel serves the exact release SHA `cb70fd6`; the Render backend was **not**
  redeployed and the six `p17*` migrations are **not** applied. Production is
  therefore a **mixture** of revisions.
* The admin console is deployed but renders a configuration notice because the
  admin deployment lacks `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY`.
* No `render.yaml`, `Dockerfile` or `Procfile` exists — backend build/start
  configuration is not reproducible from the repository.
* The API is suspended when idle (cold-start 503 → 200).
* The migration-drift CI gate exists but its run failed at startup with 0 jobs.
* The enforced CSP is a four-directive subset; the full policy is report-only.

### 4.7 Verification apparatus findings

* `qa_harness/` is a substantial read-only QA harness (scripts for DB, API,
  browser, visual/axe, workflows, agents + identities/rules/workflows) that
  **declares itself BUILD-ONLY** and **has never been run against the
  application**; its findings store holds 2 files.
* `e2e/environment/` provisions an isolated Supabase stack with remapped ports —
  a usable disposable target, if authorised.
* 3,672 backend test functions and 410 frontend assertions exist; **none were
  run** for this census.
* Only **5** capabilities have a locatable **non-implementer** verification
  record (Insight I1–I3 OHD records, plus P3-IV-01/P16 as programme records).

### 4.8 Governance findings

* The PO Decision Register, the Master Workplan (which states production
  deployment and production database mutation are **NOT AUTHORIZED**) and the
  P17 decision/report chain are coherent and mutually consistent.
* The repository contains **aspirational blueprints** (`CarbonTally Complete
  Customer Feature List` V5.0, `featurellist.md`) describing roles and
  capabilities that do not exist in the implementation (e.g. `Sustainability
  Manager`, `Finance Manager`, `Procurement Manager`, `Auditor`, custom
  roles/permissions). These are a documentation/code divergence risk if read as
  a capability statement.
* `AGENTS.md` §41 cites a "D17 master data UX" decision, but no D17 decision
  record was located by filename search.

---

## 5. Evidence quality

| Evidence class | Quality | Notes |
|---|---|---|
| Git measurements (counts, ancestry, diffs) | **High** | Directly measured, reproducible from the recorded commands |
| Code-surface counts | **High** | Mechanical greps over the inspected trees; counts are of *declarations*, not of runtime behaviour |
| Migration content | **High** (static) · **Low** (applied state) | Presence is proven; application is not |
| Historical working-tree forensics | **High** | Verified twice (raw status, then `--ignore-all-space`) |
| Governance claims | **Medium** | Authoritative for intent; only as strong as the code evidence behind them |
| Production state | **Medium** | Second-hand from the immediately preceding P18-04 task; no live request was made here |
| Behavioural / runtime claims | **Low / absent** | No runtime, no database, no authenticated journey, no test run |
| Independent verification of the *findings* | **Absent** | This census is a first-party discovery artefact |

Weakest links, stated plainly: (a) **no database was read**, so every
"persisted" item is a repository claim; (b) **no suite was run**, so no
functional claim in this census is newly verified; (c) **no authenticated
journey was executed**, so the authenticated platform's live behaviour is
`UNKNOWN` apart from the registered regression.

---

## 6. Totals

| Required total | Value |
|---|---|
| Capabilities discovered | **152** |
| Significant changes discovered | **36** |
| Issues discovered | **36** (1× S1, 8× S2, 21× S3, 6× S4) |
| Uncertain items | **14** |
| Items requiring a PO decision | **18** |
| Dependency clusters | **7** load-bearing + tooling-only (§9.8 of the census) |
| Repositories inspected | 2 |
| Git refs inspected | 9 branches/PR refs + 3 tags |
| Migration files reconciled | 89 canonical / 75 `93d5cddd` / 68 historical `main` |
| Canonical-only commits | 204 |
| Historical checkpoint-only commits | 1,659 (reachable via 553 refs) |
| Capabilities that are production verified | **7** (public surface only) |
| Capabilities known NOT deployed | **34** |
| Capabilities whose state is live-unknown | **45** |

---

## 7. Unresolved questions (summary)

The fourteen `UNC` items in the census (§11.1) collapse into four root causes:

1. **No database access is permitted in this task** → the production migration
   ledger, the persisted state of every table, and the investor-demo dataset are
   all `UNKNOWN` (UNC-001, UNC-006, UNC-007).
2. **No backend deployment provenance is available** → the running Render
   revision, the active environment configuration, and therefore whether P17
   code paths are reachable, are all `UNKNOWN` (UNC-002, UNC-004, UNC-005,
   UNC-008, UNC-011).
3. **No canonical counterpart exists for the historical tree's uncommitted work**
   → whether those 32 files were superseded or lost is `UNKNOWN` (UNC-003).
4. **Static inspection cannot distinguish "registered" from "reachable"** → the
   `CODE-ONLY` classification of 31 capabilities rests on registration tables,
   not runtime introspection (UNC-010, plus UNC-012/UNC-013 at the margin).

Two documentation-hygiene unknowns remain: whether the D17 decision record
exists (UNC-014) and whether the historical tree should remain divergent
(POD-016).

---

## 8. Limitations of this census

1. **No database was read.** Every persistence statement is a repository claim.
2. **No test suite was run.** Static test counts are not results; the P16
   programme recorded 9 failures and 11 skips at its own final run.
3. **No authenticated application journey was executed.** Live behaviour of the
   authenticated platform is unverified except for the registered regression.
4. **Production evidence is second-hand.** It is copied from the immediately
   preceding P18-04 task and labelled as such; this task made no live request.
5. **Capability granularity is a judgement.** Micro-capabilities were grouped
   (e.g. the legal pages as one row) and macro-capabilities split (e.g. Scope 2
   location versus market). A different analyst may draw the boundaries
   differently; the total is therefore "at least 152 discoverable capabilities",
   not a physical constant.
6. **`CODE-ONLY` may over-count.** A module classified `CODE-ONLY` because it is
   absent from the `include_router` tables could still be reachable through
   another import path; runtime introspection would be needed to settle it.
7. **The historical tree was inspected as-is**, and its stale remote-tracking
   refs were left stale (no fetch was performed).
8. **This census is not independent.** It was produced by a single agent; the
   independent verification step required by `AGENTS.md` §60 has not occurred
   (POD-014).

---

## 9. Safety verification

| Rule from the task | Result |
|---|---|
| Modify application/frontend/admin/backend source | **NO** |
| Modify SQL or migrations | **NO** |
| Modify Supabase schema or RLS | **NO** |
| Modify configuration | **NO** |
| Deploy / push / merge / rebase / reset / cherry-pick / amend | **NO** |
| Delete or rename files | **NO** |
| Install packages | **NO** |
| Run migrations | **NO** |
| Write to production or development databases | **NO** |
| Create database records | **NO** |
| Alter Git history | **NO** |
| "Clean up" anything discovered | **NO** |
| Make product decisions | **NO** |
| Remove pre-existing files or temporary artefacts | **NO** (none were touched) |

State comparison (measured at start and at end):

| Item | Start | End | Match |
|---|---|---|---|
| Canonical branch / HEAD | `p8-release-reconciled` / `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | identical | ✅ |
| Canonical tracked modifications | 1 (`.gitignore`) | 1 (identical) | ✅ |
| Canonical reflog tip | `cb70fd6 HEAD@{2026-09-26 16:19:11 +0600}` | identical | ✅ |
| Historical branch / HEAD | `main` / `20b7a928bb73fdfacf8271ff537a8fd245f62c79` | identical | ✅ |
| Historical tracked modifications | 227 | 227 | ✅ |
| GitHub refs (read-only) | `main` `2f56562`, `p8-release-reconciled` `cb70fd6` | identical | ✅ |

Files created: the three documents listed in §1.2 — all new, all documentation,
all untracked. Temporary inspection output was written to `/tmp/*` only.

---

## 10. Verdict and follow-on work

### 10.1 Verdict

```
CT_RECON_01_COMPLETE_READ_ONLY_CENSUS
```

The census was completed across both trees, all GitHub refs, the reachable
history of both trees, the migration corpus, the code and UI surfaces, the
tooling surfaces and the governance corpus. Where evidence was unavailable it is
recorded as `UNKNOWN` with the reason stated — not inferred, and not presented
as fact.

### 10.2 Follow-on work implied by the findings (no decision taken here)

These are **evidence-implied follow-ups**, listed for the Product Owner to
accept, reject or re-order. None is authorised by this report, and none
constitutes a recommendation of product policy.

1. **A root-cause forensic task for `ISS-001`** — the live authenticated
   workspace-load failure (explicitly out of scope here; already noted in the
   task brief as a separate task).
2. **A decision pack for `POD-001`/`POD-002`** — the P17 backend release and the
   production-migration gate, including whether the decision must cover the
   other 15 canonical-only migrations (`ISS-035`).
3. **An operator action for `POD-011`/`ISS-006`** — admin Supabase build settings
   (deployment configuration, not code).
4. **A disposition record for `POD-003`/`POD-004`** — the 32 uncommitted files
   and the absent investor-demo seeder and identity manifest.
5. **An authorisation decision for `POD-006`** — running the QA harness against a
   disposable target (the isolated E2E stack is the evident candidate).
6. **A verification nomination for `POD-014`** — independent re-verification of
   this census and its ledger by a party other than the author.
7. **A repair item for `ISS-008`** — the migration-drift CI workflow failing at
   startup, since it is the project's only automated release gate.
8. **A reconciliation item for `POD-016`** — the divergent historical tree,
   including whether its stale refs and checkpoint-only history are retained.

### 10.3 Acceptance statement

This report is an **implementation-evidence artefact**, not an acceptance.
Nothing in it is `INDEPENDENTLY VERIFIED`, `ACCEPTED` or `PRODUCTION VERIFIED`
for the authenticated platform. Per `AGENTS.md` §73 those terms are not
synonyms, and none of them is claimed here.
