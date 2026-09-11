# CT-PROD-PUBLICATION-RECON-20260911-001

**Prompt Ref:** `CT-PROD-PUBLICATION-RECON-20260911-001`
**Response Ref:** `CT-PROD-PUBLICATION-RECON-20260911-001-R1` · **Datetime:** 2026-09-11
**Mode:** **READ-ONLY RECONSTRUCTION** — no stage, commit, push, reset, restore, checkout, delete, rename,
or modification of source/migrations/config/documentation; no `.gitignore`/`.clineignore`/`.vercelignore`
change; no migration applied; no deploy; no backup executed; no production contact.
**Repository:** CarbonTally · branch `main` · `origin` = `https://github.com/shomonrobie/CarbonTally.git`
**HEAD:** `c864d729526ef2c5e40cd19fdc451e8f0975144b` · **`origin/main`:** `6148c86826e25e1889d8cf86bb02dbb2901577c6`
**Durable output:** this file (the only file created).

---

## PHASE 1 — CURRENT GIT BOUNDARY (measured)

| Item | Value |
|---|---|
| Branch | `main` (tracking `origin/main`, **ahead 30, behind 0**) |
| HEAD | `c864d729526ef2c5e40cd19fdc451e8f0975144b` (Phase-6 closure commit) |
| `origin/main` | `6148c86826e25e1889d8cf86bb02dbb2901577c6` = **merge base** (fast-forward possible) |
| Clean/dirty | **Dirty** — 0 staged, 210 modified tracked, 152 deleted tracked, 852 untracked non-ignored, **194,900 ignored-but-present** files |
| Other refs | local `openhands/d2001f58-…` (70 commits, ancestor of origin/main); remote `origin/openhands/public-website-visual-refactor` (**ahead 1, behind 77** — one commit not on `origin/main`); tags `rc2-final`, `v2.1-phase4`, `v2.1.1-phase3` |
| Total commits | `HEAD` = **177**; all refs = **616** |
| Remotes | `origin` → GitHub only (no production remote configured) |

Ignored-but-present highlights: `frontend/node_modules` (95,961), `website_candidate/frontend` (38,323),
`backend/.venv` (9,921), `.venv` (9,540), `qa_harness/.venv` (1,296), `independent_audit/reports` (1,705),
`.tmp_pgdata` (local Postgres data directory), `myenv/`. All `.env*` files are ignored by `.gitignore:83`
(`.env*`) — see PHASE 6.

## PHASE 2 — COMMITTED HISTORY RECONSTRUCTION

**The 30 commits between `origin/main` and HEAD are internally consistent CarbonTally product/release work.**
All are locally authored (2026-08-29 → 2026-09-11). Content scans found no secrets, generated output or
agent scratch state in them (PHASE 6). Scope per commit (top-level file counts):

| # | Commit | Date | Subject (abbrev.) | Dominant scope | Class |
|---|---|---|---|---|---|
| 1 | `17665d0` | 08-29 | V3 phases A–C: durable automatic processing, customer workspace, security/factor lifecycle | backend 24, frontend 12, docs 3, **supabase 1** | product |
| 2 | `55410d9` | 08-30 | Phase D: authenticated communication via V3 API + public-only Assistant | frontend 8, backend 4 | product |
| 3 | `a0194a9` | 08-30 | V3 ops hardening: CL-65/CL-62/CL-59 | frontend 7, backend 1 | product |
| 4 | `5d35603` | 08-30 | Phase E: consultant product — roster (CL-61), onboarding (CON-1) | backend 4, frontend 4 | product |
| 5 | `4e2c3e3` | 08-30 | CL-58 shared table contract + operator queue pagination | frontend 4, backend 1 | product |
| 6 | `4491103` | 08-30 | CL-66: canonical staff/admin control plane (doc) | docs 1 | documentation |
| 7 | `58285e6` | 08-30 | Phase 2 implementation report | root report | documentation |
| 8 | `6b4d749` | 08-30 | Phase E: consultant operational workspace | backend 4, frontend 4 | product |
| 9 | `85eb074` | 08-30 | Phase F/G: PE routed item workspace (G5) | frontend 3 | product |
| 10 | `60e2ab9` | 08-30 | Phase H/I: server-side pagination (review/QC) | frontend 4, backend 2 | product |
| 11 | `dc931a3` | 08-30 | Phase K: retention persistence fix | backend 3 | product |
| 12 | `d632afc` | 08-30 | Phase L: search deep-link | frontend 1 | product |
| 13 | `5fa19d0` | 08-30 | Phase 2 completion matrix | docs 1 | documentation |
| 14 | `1b55ad6` | 08-30 | Phase H: staff roster pagination (H4) | frontend 2, backend 1 | product |
| 15 | `97104a9` | 08-30 | Phase 2 completion report (NOT COMPLETE verdict) | root report | documentation |
| 16 | `fc05f05` | 08-30 | Phase 2 close-out: PE Manager dashboard, consultant revoke, evidence view | backend 5, frontend 5 | product |
| 17 | `d494999` | 08-30 | Phase H close-out: entities catalogue pagination | frontend 2, backend 1 | product |
| 18 | `17db17d` | 08-30 | Fix P1: blocking findings 500 (issues FK) | backend 2 | product |
| 19 | `78718bb` | 08-30 | Fix: multi-line validation / item-level factor contract | backend 2 | product |
| 20 | `899706d` | 08-30 | Fix: customer calculate D23 multi-line support | backend 3 | product |
| 21 | `8041001` | 08-30 | DataTable rollout (CL-58 remainder) | backend 4, frontend 3 | product |
| 22 | `430a30f` | 08-30 | Close-out: Phase 2 report + matrix refresh | docs | documentation |
| 23 | `7e24941` | 08-30 | D-P2-01: queue disclosure (CL-55/57) | backend 4, frontend 3 | product |
| 24 | `cd95d03` | 08-30 | D-P2-02/03/04: **legacy admin deprecation inventory**, QC authority, retention | docs 2, backend 1 | product+doc |
| 25 | `0a51a78` | 08-30 | D-P2 item 3: notifications pagination | frontend 1 | product |
| 26 | `bb6cd7d` | 08-30 | P1 fix: customer-factor → report generation (O1) | backend 5 | product |
| 27 | `56ae6fa` | 08-30 | Phase 2 close-out docs (COMPLETE verdict + PO decisions) | docs | documentation |
| 28 | `1639121` | 08-30 | Phase 2 report refresh | root report | documentation |
| 29 | **`daad396`** | 09-11 | **release: establish CarbonTally production release 1** | **485 files**: docs 168, backend 98, qa_harness 70, e2e 69, frontend 55, **supabase 17**, root `vercel.json` + `package.json` | release |
| 30 | **`c864d72`** | 09-11 | **feat: close CarbonTally Phase 6 consultant workflow** | 11 files: backend 1 (LT-1 fix), tests 2, e2e 2, docs 6 | release |

**Neither release commit is complete.** `daad396`'s own report
(`CARBONTALLY_PRODUCTION_RELEASE_MANIFEST_20260911.md`, baseline `1639121`) records that it captured
production source + 17 migrations + release config, with tests/harness/docs as "commit-but-not-deploy" and a
residual PO-decision list — it did **not** capture the backup subsystem, the QA-harness restructure, the
legal/PO registers, the deployment-readiness/migration-safety documents, or the pending deletions
(PHASE 4). `c864d72` contains exactly the 11 authorised Phase-6 closure files.

## PHASE 3 — PRE-PHASE-1 WORK RECONSTRUCTION

### 3.1 The repository contains TWO unrelated root lineages, already merged

* Root A `7ca9533` — **"Clean slate: Properly structured CarbonTally monorepo" (2026-07-17)** → the
  **v1/v2 era**, carrying tags `rc2-final` (59 commits, 2026-08-06 "CarbonTally RC2 Final database
  baseline"), `v2.1.1-phase3` (61, 2026-08-07 "Phase 3: Infrastructure Layer") and `v2.1-phase4`
  (62, 2026-08-07 "Phase 4: Factor Matching Engine").
* Root B `b322ab3` — same first message/date → the **V3 era** (`feat(v3): restore core business workflow
  (Phase 1)` is the tip of `origin/main` at 147 commits).
* **Merge `c36c848` (2026-08-27): "chore: reconcile divergent origin/main lineage (history unification;
  verified V3 tree preserved)"** — the single merge commit in HEAD's history. Because BOTH roots are
  ancestors of `origin/main` (verified via `rev-list --max-parents=0`), the v1/v2 lineage **is already
  published as history**, but the merge deliberately **kept the V3 working tree** — so pre-Phase-1 *tree
  content* (the v2.1 backend, RC2 schema baseline, the phase-1-era admin CRA's own lineage) was **not
  carried into the current tree** except where V3 reuses it (e.g. the quarantined `admin/` CRA).

**Conclusions for Phase 3:** the pre-Phase-1 development is **not missing from the repository** — it exists
as published history on `origin/main` via `c36c848`, recoverable read-only by tag/branch
(`rc2-final`, `v2.1-phase4`, `v2.1.1-phase3`, `origin/openhands/public-website-visual-refactor`). What is
**not** represented in the current tree is that era's file content. Whether any of it should be *restored*
into the tree is a PO decision (**not** performed here).

### 3.2 Roadmap authority on the pre-Phase-1 / Phase-1 era

`CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` is explicit and is quoted rather than inferred:

* §14 Phase Authority Map — Phase 1: *"*(unresolved)*… **UNRESOLVED — NO AUTHORITATIVE PRODUCT PHASE-1
  ARTIFACT LOCATED** (PO-ratified; does not block Phase 6) — none required — PO ratified as an accepted
  documentation gap."*
* §15 "Legacy Phase Numbering Warning" — the repository holds **multiple mutually incompatible "Phase N"
  lineages** (V2.1 backend build phases, V3 consolidation phases, platform master audit 1–16,
  security-assessment, standalone migration 0–11, OpenHands UX), with the binding rule that *"Only the
  Phase numbering defined in the CarbonTally Master Project Roadmap constitutes the product implementation
  roadmap."*
* §13 Current Project Position still records "NEXT GATE: P6-2C" — i.e. the roadmap document itself is
  **stale** relative to Phase 6 closure (a documentation-sync item, not a publication blocker).

**Answer to "does intentional pre-Phase-1 work remain unpublished?"** — Yes, in one specific sense: the
current working tree carries **Phase-1-era/WIP artefacts that never entered any commit** and are not part of
the V3 tree: the legacy admin CRA's line-ending churn (`admin/**`), `create_admin_dashboard.py`,
`admin-dashboard.zip` (132 MB), `frontend_backup_pre_v3_public_20260827/**` (tracked), `shared/**`
(unreferenced), `carbon-tally-ui-demo/**`, `demodatagen/**`, `tools/carbon_data_factory/**`, the root
probe/mock/test scripts, and the v2-era schema dumps (`v3_schema.sql`, `CarbonTally_DB_Schema_V3M2.sql`).
PHASE 4/7 classify each of these; the large majority are local/historical/generated (**C**).

### 3.3 Reflog

50 reflog entries, all `HEAD` checkouts/commits with no lost commits: top entry
`c864d72 commit: feat: close CarbonTally Phase 6 consultant workflow`, next `daad396 release: establish
CarbonTally production release 1`. No dangling/abandoned work is indicated by the reflog.

## PHASE 4 — CURRENT WORKING TREE ANALYSIS

### 4.0 Decisive measurement: line-ending churn vs real change

`git diff` reports 210 modified tracked files, but `git diff --ignore-all-space --name-only` shows that
**most of that is CRLF/EOL churn with identical content**:

| Set | Files | Evidence |
|---|---|---|
| Modified with **real** (non-whitespace) content change | **6 non-deletion files** | `.gitignore`, `backend/requirements.txt`, `supabase/config.toml`, `CarbonTally_DB_Schema_V3M2.sql`, `package-lock.json`, `requirements.txt` |
| Modified **whitespace/EOL-only** (no content change) | 178 | `admin/**` 67 — `git diff --shortstat` = `19197 insertions / 19197 deletions`, and `-w` = **empty**; `.agents/**` 69 — `-w` = **empty**; `tools/**` 29, `demodatagen/**` 13 |
| Deletions (`D`) | 152 | PHASE 8 |
| Deletions that also appear in `--ignore-all-space` name lists | 138 + 13 + 1 | inherent to deletion |

Consequence: **the only modified files that carry a durable content decision are 6**, of which
`backend/requirements.txt` and `.gitignore` are intentional (A), and the other four are local/generated
(C — see PHASE 7).

### 4.1 Classification of the working tree by the fifteen required groups

| # | Group | Paths (count / status) | Verdict |
|---|---|---|---|
| 1 | Backend production source | Only `backend/requirements.txt` (M, real: adds `cryptography>=41.0.0` "Backup foundation (Phase 1, D3)… used by backend/backup/crypto.py") | **A** |
| 2 | Frontend production source | Only `frontend/src/StaffDashboard.jsx` (**D**); no modified/untracked frontend source | **D (deletion)** |
| 3 | Admin production source | `admin/**` 67 files **EOL-only** (content identical under `-w`) | **C (no-op)** |
| 4 | Supabase migrations/schema/config | `supabase/migrations/**` **0 changes** (53 tracked = fully committed); `supabase/config.toml` (M, real: local ports 54325→54425 / 54326→54426 / 54320→54420); `supabase/snippets/Untitled query {303,407,673}.sql` (M/M/??) | **C** (local env + dashboard snippets) |
| 5 | Tests | `backend/tests/{unit,integration}/backup/**` 8 files (new) | **A** |
| 6 | Documentation | untracked: `docs/architecture` 8, `docs/cline` 17, `docs/legal` 10, `docs/ChatGPT` 1, `docs/Robie` 1; `docs/audit` 0 new; `docs/standalone` (12) already tracked | **A** (except `docs/Robie` note → B) |
| 7 | Production operations/deployment | untracked `docs/architecture/CARBONTALLY_PRODUCTION_{DEPLOYMENT_READINESS,MIGRATION_SAFETY_PLAN,SUPABASE_RECONCILIATION}_20260911.md`; `playwright.config.ts` (??); `.github/workflows/playwright.yml` (??) | **A** / **B** (CI) |
| 8 | Backup/DR implementation | `backend/backup/**` 9 modules (2,449 lines), 8 tests, 5 docs, `requirements.txt` line | **A** |
| 9 | E2E infrastructure | `e2e/environment/**` 70 tracked (0 changed) + 6 untracked **report JSONs** and `supabase/.temp/**` | **C** (generated/local) |
| 10 | Developer tooling | `tools/seed_investor_demo/**` 14 new `.py`; `tools/carbon_data_factory/**` 29 EOL-only; root dev scripts (see 4.2) | **B** / **C** |
| 11 | Agent tooling | `.agents/skills/**` 69 tracked (EOL-only); `.claude/skills|.windsurf/skills` 138 **deleted** + 18 **machine-local symlinks**; `.clinerules/hooks/**` 13; `.openhands/memory/*.md` 7; root `config.toml` (MCP) | **D** (deletions) / **C** |
| 12 | Generated output | `output/**` (13 D, 1 M, 7 ??), `screenshots/**` 96, `qa_harness/evidence/**` 138, `qa_harness/reports/**` 55, `qa_harness/*.egg-info` 5 | **C** |
| 13 | Temporary/runtime state | `e2e/environment/supabase/.temp/**`, `.tmp_pgdata/**`, `__pycache__`, `.pytest_cache`, `qa_harness/.venv`, `independent_audit/**` (ignored via `.git/info/exclude`), `website_candidate/**`, `local_backups/**`, `local_backups/env_backup/.env*` | **C** |
| 14 | Archives | `admin-dashboard.zip` (**132,467,465 bytes**), `v3_schema.sql` (232 KB), `CarbonTally_DB_Schema_V3M2.sql` (M) | **C** |
| 15 | Unknown/ambiguous | `saas-assurance/**` (217 visible), `agent_swarm/**` (39) + `agent_swarm_v2_artifacts/**` (97), `CARBONTALLY_AUDIT_FINDING_VERIFICATION.md` (46 KB, root), `docs/Robie/…txt`, `package-lock.json` (M) | **B/C** |

### 4.2 Root-level files (40 entries, individually classified)

*Modified, real change:* `.gitignore` (**A** — adds `tools/seed_investor_demo/{demo_manifest.json,
.demo_state.json,DEMO_IDENTITIES.md}` and `/test-results/`, `/playwright-report/`, `/blob-report/`,
`/playwright/.cache/`, `/playwright/.auth/`); `backend/requirements.txt` (**A**); `supabase/config.toml`
(**C** local ports); `CarbonTally_DB_Schema_V3M2.sql` (**C** v3m2-era schema dump, superseded by 53
migrations); `package-lock.json` (**B** +3,938 lines with no accompanying `package.json` change);
`requirements.txt` (**C** EOL-only).

*Modified, EOL-only (content identical under `-w` → no durable change):* `API_ENDPOINTS.md`,
`admin_log_viewer.feature.txt`, `clean.js`, `clean_emissions_output.json`, `create_admin_dashboard.py`,
`export_postman.py`, `generate_api_docs.py`, `generate_messy_fuel_csv.py`, `generate_messy_utility_csv.py`,
`list_endpoints.py`, `mock_scope3.csv`, `mock_uk_fuel_card_messy.csv`, `mock_uk_utility_bill.csv`,
`quick_api_ref.py`, `seed.ts`, `test_endpoints.py`, `test_results.json`, `test_results_all.json`,
`v1.9.txt`, `.clineignore`, `.vercelignore` — **C**.

*Untracked (15):* `AGENTS.md` (**A** — the project operating constitution); `playwright.config.ts`
(**A** — real config, `testDir ./tests/e2e`, documents skip-when-no-environment);
`CARBONTALLY_AUDIT_FINDING_VERIFICATION.md` (**B**); `.github/workflows/playwright.yml` is included in
group 7; `probe_out{,2..9}.txt` 9 files, 354–12,025 bytes (**C** probe outputs); `v3_schema.sql` (**C**);
`admin-dashboard.zip` (**C**, 132 MB); `config.toml` (root; `[mcp] shttp_servers =
[{url = "http://localhost:8888/mcp/carbontally-full-ui/"}]` → **C** local agent-tool config);
`tests/example.spec.ts` (Playwright's stock `playwright.dev` scaffold → **C**).

## PHASE 5 — SPECIAL PRODUCTION RELEASE REVIEW

### 5.A Production backend

* The **only** uncommitted backend production change is `backend/requirements.txt` (+`cryptography>=41.0.0`,
  with an inline comment naming `backend/backup/crypto.py` as the consumer) → **A**.
* All other backend production code (api, data, domain, services, engines, workers, infra, `main/database/
  auth.py`, `core/exceptions.py`) is **already committed** in `daad396` — including the billing subsystem
  (`backend/data/billing.py`, `backend/domain/billing.py`, `backend/services/billing.py` +
  `backend/tests/unit/api/test_billing_core.py`). Verified: `git log origin/main..HEAD -- backend/*/billing.py`
  returns exactly one commit (`daad396`), and no billing file appears in the working-tree status.
* No backend source file is modified or deleted in the working tree.

### 5.B Frontend — the actual production frontend tree

`vercel.json` (root, production) routes `/(.*)` → `/frontend/index.html` and `/static/(.*)` →
`/frontend/static/$1`; the root `package.json` `build` script runs `cd frontend && npm run build && cd ../admin
&& npm run build … cp -r admin/build/* public/admin/`. Therefore:

* **`frontend/` is the production front end** (`frontend/src/v3/**` = `admin`, `consultant`, `customer`,
  `ops`, `pe`, `reports`, `messaging`, plus `tokens.css`/`v3.css`). **`frontend/src/v3/admin/**` (11 files)
  is the relevant V3 admin area** — confirmed present and complete (`AdminPage.jsx`, `MembersTab`,
  `SecurityTab`, `FacilitiesTab`, `LocationsTab`, `VehiclesTab`, `SuppliersTab`, `CustomFactorsTab`,
  `ProfileTab`, `ActivityTab`).
* **`admin/` is the quarantined legacy CRA**, retained deliberately: `package.json` `name:
  carbontally-admin`, `homepage: /admin`; `CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md` — *"The legacy admin
  CRA is **quarantined**, not deleted… no new feature is built on it"*, and
  `CARBONTALLY_LEGACY_ADMIN_INVENTORY.md` (D-P2-02) — *"not deleted — it remains mounted until the
  retirement conditions below are met"*. **Legacy code must not be reintroduced or removed**; its 67
  working-tree modifications are line-ending-only (**C**).
* Frontend working-tree content: only `frontend/src/StaffDashboard.jsx` **deleted** (zero remaining imports
  per the release manifest) → intentional deletion.

### 5.C Supabase migrations

* `supabase/migrations/` at HEAD = **53** (origin/main = 35 → **18 added** by the unpushed commits
  `17665d0` ×1 and `daad396` ×17). **Zero** migration changes in the working tree.
* The 18 publication-candidate migrations (already committed; publication ≠ application):
  `20260829000000_v3m9_durable_automatic_processing`, `20260831000000_v3m10_org_membership_unique`,
  `20260831010000_v3m11_operational_indexes`, `20260831020000_audit_activity_immutability`,
  `20260831030000_tenant_org_id_not_null`, `20260831040000_consultant_revocation_roles`,
  `20260902020000_v1_2_dual_origin_workflow`, `20260902030000_phase5_work_item_assignments`,
  `20260902040000_phase5_pe_operational_messaging`, `20260902050000_phase5_notification_event_key`,
  `20260903010000_ws4_gate3_4a_item_assignment_foundation`, `20260905000000_gate4_actor_provenance`,
  `20260905010000_gate5_t1_automation_provenance`, `20260905020000_gate5_t6_automation_write_once_guard`,
  `20260906010000_gate6_w1_automation_extracted_output`, `20260906090000_p6_1c_consultant_engagement`,
  `20260906100000_p6_2a_consultant_processing_permissions`, `20260910120000_p6_2d_consultant_provenance`.
* **E2E-only schema:** `e2e/environment/supabase/migrations/` holds its **own** 53-file copy (all already
  committed) — an isolated-environment schema set, not a production migration path.
* **No migration is applied, and none is claimed applied.** Production database state is UNKNOWN from this
  environment (no production credentials; read-only task).

### 5.D Backup implementation — **intentional durable work: A**

* `backend/backup/` 9 modules, 2,449 lines: `__init__.py`, `artifact.py` (324), `catalog.py` (614),
  `crypto.py` (169), `errors.py` (84), `exporter.py` (253), `service.py` (403), `settings.py` (240),
  `storage.py` (284); plus 6 unit-test files and 1 integration-test file (+2 `__init__.py`).
* Authority chain (read): `CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md` (Part 1 assessment +
  Part 2 ratified decisions), `…BACKUP_IMPLEMENTATION_PHASE1_20260911.md`,
  `…BACKUP_PHASE1_1_INDEPENDENT_VERIFICATION_20260911.md`,
  `…BACKUP_P1_1_N1_INDEPENDENT_VERIFICATION_20260911.md`,
  `CARBONTALLY_PRODUCTION_BACKUP_RESTORE_ROADMAP_V1.0.md`, and 9 `CT-PROD-BACKUP-*` prompt-history records.
  `CT-PROD-BACKUP-DECISIONS-20260911-002` records **PO-ratified D1–D5** (asyncpg exporter; private off-site
  object storage; application-level encryption with separate key custody; restore as a separately
  authorised capability; restricted `ct_backup` role) with verdict *"READY FOR BOUNDED IMPLEMENTATION —
  EXPLICIT PO AUTHORIZATION REQUIRED"*, followed by implementation and two independent verifications.
* Wiring status: `grep` for `backup` imports outside `backend/backup/` = **0** → the subsystem is **not yet
  mounted** into the API/router (a standalone, tested capability). `cryptography` is declared for it.
* Contrast with the Phase-6 closure document's "Backup/DR = PARKED": the backup work is **later** than that
  document and is implementation-verified → the later state governs (PHASE 9, conflict C1).

### 5.E Production-readiness documentation

Durable (**A**): `CARBONTALLY_PRODUCTION_DEPLOYMENT_READINESS_20260911.md`,
`CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md`,
`CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md`, the 5 backup documents, the 17
`docs/cline/prompt-history/*` records, and the 10 `docs/legal/**` documents (Legal Risk Register,
Third-Party Processor Register, Policy↔Product Consistency Audit + 7 draft policies, each marked
"Draft — for legal review").
Temporary-analysis: root `CARBONTALLY_AUDIT_FINDING_VERIFICATION.md` (**B**), `API_ENDPOINTS.md`
(locally regenerated by `generate_api_docs.py`) → **C**.

### 5.F Billing / provisioning (P0 production readiness)

* **No uncommitted billing or provisioning implementation exists.** All billing/provisioning work
  (`backend/data/billing.py` `date_trunc('month', $2::timestamptz)::date` fix, `backend/services/billing.py`
  +117 lines, `backend/domain/billing.py`, its unit test, the D37 commercial migrations and the
  `frontend/src/v3/admin/*` provisioning surfaces) is **already committed** in `daad396`.
* The only working-tree "billing" hits are QA evidence artefacts under `qa_harness/evidence/**` → **C**.

## PHASE 6 — SECRET / ARTIFACT / RUNTIME SCAN

| Probe | Result |
|---|---|
| `.env` family in the working tree | `.env`, `.env.local`, `.env.production`, `backend/.env`, `backend/.env.bak`, `backend/tests/.env.test`, `frontend/.env{,.local,.production}`, `tools/carbon_data_factory/.env`, `e2e/environment/.env.e2e`, `e2e/environment/.env.personas`, `tests/e2e/.env.personas`, `local_backups/env_backup/.env*`, `frontend_backup_pre_v3_public_20260827/.env*` — **ALL ignored** (`.gitignore:83 .env*`, `/local_backups/`, or a nested `.gitignore`) → **not publishable** |
| `.env*` tracked at HEAD | **0** |
| Private keys / PEM / `.key` / `id_rsa` / `.p12` | **0** |
| Real JWTs (`eyJ…`) | **0** — only synthetic fakes in `qa_harness/tests/harness/{test_secrets,test_run_context}.py` |
| Service-role / anon keys | **0 literals**; `e2e/environment/scripts/capture_env.sh` + `seed_e2e.py` read `SERVICE_ROLE_KEY` from the environment at runtime and write a gitignored local file |
| Credential-bearing DSNs | Only synthetic test values (e.g. `postgresql://postgres:local-secret-123@127.0.0.1:54426/…`) and `USER:PASSWORD@HOST` placeholders in already-published agent-skill docs |
| Demo credentials | `.local-demo-credentials.md` and `tools/seed_investor_demo/{DEMO_IDENTITIES.md,demo_manifest.json,.demo_state.json}` are **gitignored** (the latter three by the *new* `.gitignore` lines) → **not publishable** |
| Certificates / DB dumps / archives | `admin-dashboard.zip` (132 MB) → C; `backups/seed.sql` (7.3 MB) is **already published on origin/main** and unchanged |
| Generated local DB state | `.tmp_pgdata/**` (ignored), `local_backups/**` (ignored), `e2e/environment/supabase/.temp/**` |
| Caches / venvs / node_modules | `frontend/node_modules`, `node_modules`, `backend/.venv`, `.venv`, `myenv/`, `qa_harness/.venv`, `.pytest_cache` — all ignored |
| Playwright reports/traces/videos | not present as untracked non-ignored; the new `.gitignore` lines add `/test-results/`, `/playwright-report/`, `/blob-report/`, `/playwright/.cache/`, `/playwright/.auth/` |
| Screenshots / probes | `screenshots/**` 96 untracked (C), `probe_out*.txt` 9 untracked (C), `qa_harness/evidence/screenshots/**` (C) |
| Agent session state | `.openhands/memory/*.md` (7), `.clinerules/hooks/**` (13), root `config.toml` (MCP), `agent_swarm_v2_artifacts/**` (97), `independent_audit/**` (ignored locally via `.git/info/exclude`) |
| Personal/local tooling state | `docs/Robie/getting this on live website.txt` (PO-observed production incident note) |

**SECRET-LIKE ARTIFACT FOUND:** none meeting the threshold. The only near-miss class is the **ignored**
`.env*` family and `local_backups/env_backup/.env*` (type: local environment files; status: untracked +
ignored; recommended action: keep excluded — already enforced). No secret value is reproduced in this report.

## PHASE 7 — PRECISE PUBLICATION MANIFEST

Classification: **A — MUST PUBLISH** · **B — PO CONFIRMATION REQUIRED** · **C — MUST NOT PUBLISH**.
Action: `INCLUDE IN PUBLICATION` · `HOLD FOR PO` · `EXCLUDE`.

### 7.1 A — MUST PUBLISH (INCLUDE)

| Path | Class | Reason | Evidence | Action |
|---|---|---|---|---|
| `backend/backup/__init__.py`, `artifact.py`, `catalog.py`, `crypto.py`, `errors.py`, `exporter.py`, `service.py`, `settings.py`, `storage.py` | A | Production backup subsystem — PO-ratified D1–D5, implemented and independently verified; production-readiness deliverable | 2,449 lines; `CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md` (Parts 1–2); 2 independent-verification docs; 9 `CT-PROD-BACKUP-*` records | INCLUDE IN PUBLICATION |
| `backend/tests/unit/backup/{__init__,test_artifact,test_crypto,test_service,test_storage_and_settings,test_p1_1_remediation}.py` (6) | A | Backup unit tests required by AGENTS.md §72 | Same authority chain as above | INCLUDE IN PUBLICATION |
| `backend/tests/integration/backup/{__init__,test_exporter_local}.py` (2) | A | Backup integration test (local exporter) | Same authority chain | INCLUDE IN PUBLICATION |
| `backend/requirements.txt` (modified) | A | Adds `cryptography>=41.0.0` required by `backend/backup/crypto.py`; comment cites the Phase-1/D3 basis. Without it the backup install is transitively incomplete | `git diff -- backend/requirements.txt` (+6/−1) | INCLUDE IN PUBLICATION |
| `.gitignore` (modified) | A | Adds the investor-demo artefact ignores (`tools/seed_investor_demo/{demo_manifest.json,.demo_state.json,DEMO_IDENTITIES.md}`) and Playwright artefact ignores (`/test-results/`, `/playwright-report/`, `/blob-report/`, `/playwright/.cache/`, `/playwright/.auth/`) | `git diff -- .gitignore` (+13) | INCLUDE IN PUBLICATION |
| `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md`, `…BACKUP_IMPLEMENTATION_PHASE1_20260911.md`, `…BACKUP_PHASE1_1_INDEPENDENT_VERIFICATION_20260911.md`, `…BACKUP_P1_1_N1_INDEPENDENT_VERIFICATION_20260911.md`, `…BACKUP_RESTORE_ROADMAP_V1.0.md` (5) | A | Backup architecture/implementation/verification/roadmap documentation | Files present, untracked, referenced by the `CT-PROD-BACKUP-*` records | INCLUDE IN PUBLICATION |
| `docs/architecture/CARBONTALLY_PRODUCTION_DEPLOYMENT_READINESS_20260911.md`, `…PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md`, `…PRODUCTION_SUPABASE_RECONCILIATION_20260911.md` (3) | A | Production-readiness documentation set | Untracked; companion to the committed pre-commit-gate / readiness-audit docs | INCLUDE IN PUBLICATION |
| `docs/cline/prompt-history/CT-PHASE6-COMMIT-20260911-001.md`, `CT-PHASE6-PUSH-AUDIT-20260911-001.md`, `CT-PROD-BACKUP-ARCHITECTURE-20260911-001.md`, `CT-PROD-BACKUP-DECISIONS-20260911-002.md`, `CT-PROD-BACKUP-DR-ROADMAP-DOC-20260911-001.md`, `CT-PROD-BACKUP-IMPLEMENTATION-20260911-001.md`, `CT-PROD-BACKUP-IV-20260911-001.md`, `CT-PROD-BACKUP-P1.1-IMPLEMENTATION-20260911-001.md`, `CT-PROD-BACKUP-P1.1-IV-20260911-001.md`, `CT-PROD-BACKUP-P1.1-N1-IMPLEMENTATION-20260911-001.md`, `CT-PROD-BACKUP-P1.1-N1-IV-20260911-001.md`, `CT-PROD-DEPLOYMENT-READINESS-20260911-001.md`, `CT-PROD-MIGRATION-PREP-20260911-001.md`, `CT-PROD-RELEASE-COMMIT-20260911-001.md`, `CT-PROD-RELEASE-COMMIT-CORRECTION-20260911-001.md`, `CT-PROD-SUPABASE-RECON-20260911-001.md`, `CT-PROD-SUPABASE-RECON-20260911-002.md`, and **this file** `CT-PROD-PUBLICATION-RECON-20260911-001.md` (18) | A | Prompt-history records are the governance audit trail (AGENTS.md §83–§84); `docs/cline/prompt-history/` already holds 105 tracked records | Directory precedent + content | INCLUDE IN PUBLICATION |
| `docs/legal/CARBONTALLY_LEGAL_RISK_REGISTER.md`, `…POLICY_PRODUCT_CONSISTENCY_AUDIT.md`, `…THIRD_PARTY_PROCESSOR_REGISTER.md` (3) | A | Durable legal/compliance registers (P0 risks for commercial launch) | Headers show read-only, evidence-based audits | INCLUDE IN PUBLICATION |
| `docs/legal/draft/CARBONTALLY_{COOKIE_POLICY,DATA_RETENTION_ARCHIVAL_ANONYMIZATION_POLICY,DPA,MSA,PRIVACY_POLICY,REFUND_POLICY,TERMS_OF_SERVICE}_DRAFT.md` (7) | A | Draft customer-facing policy set awaiting legal review | Referenced by the Legal Risk Register (e.g. LR-01 → retention policy §6) | INCLUDE IN PUBLICATION |
| `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` (1) | A | PO decision register — primary governance source of truth | Untracked; referenced role in the governance model | INCLUDE IN PUBLICATION |
| `AGENTS.md` (root, untracked) | A | The project operating constitution (agent/QA/security/PO rules) that the whole workflow cites | Untracked at root; content is the governance rule-set | INCLUDE IN PUBLICATION |
| `playwright.config.ts` (root, untracked) | A | Real E2E configuration (`testDir ./tests/e2e`, isolated-environment contract, skip-when-unconfigured) required by `tests/e2e/**` and the Playwright workflow | File content + `tests/e2e` (6 tracked files) | INCLUDE IN PUBLICATION |
| `qa_harness/{__init__.py,Makefile,pyproject.toml,README.md,requirements.txt}` (5) | A | QA Harness v1.1 packaging/metadata — project deliverable per AGENTS.md §52 (read-only independent QA) | `pyproject.toml` → `name = "carbontally-qa-harness"`, v1.1.0, "Reusable read-only QA Harness for CarbonTally V3" | INCLUDE IN PUBLICATION |
| `qa_harness/core/**` (9), `api/**` (8), `db/**` (8), `agents/**` (8), `rules/**` (6), `identities/**` (5), `visual/**` (3), `findings/**` (5), `workflows/**` (10) — 62 files | A | QA Harness v1.2 module code (config/credentials/db/api/browser/workflow layers) | Module docstrings reference spec V1.2 and CarbonTally V3; `docs/standalone/QA_HARNESS_V1_2_PORTABILITY_AUDIT.md` audits this tree | INCLUDE IN PUBLICATION |

**A-total: 107 files** (17 backup incl. tests · 1 `backend/requirements.txt` · 1 `.gitignore` · 8
`docs/architecture` · 18 prompt-history incl. this file · 10 `docs/legal` · 1 PO register · `AGENTS.md` ·
`playwright.config.ts` · 67 qa_harness).

### 7.2 B — PO CONFIRMATION REQUIRED (HOLD FOR PO)

| Path | Class | Why the evidence is insufficient | Action |
|---|---|---|---|
| `saas-assurance/**` (217 non-ignored files; 593 on disk; own `README.md`, `.gitignore`, `docs/`, `packages/`, `profiles/`, `tests/`) | B | A **separate framework product** ("SaaS Assurance") developed inside this working tree. `docs/standalone/REPOSITORY_STRATEGY.md` (Status: PROPOSAL — for PO review) presents options for a **separate repository**, and `docs/standalone/OPEN_SOURCE_SECURITY_CHECKLIST.md` states "The standalone repository will be public." No nested `.git` found, so git treats it as plain files. Publishing here contradicts the stated separate-repo direction; discarding it loses work. | HOLD FOR PO |
| `agent_swarm/**` (39: `README.md`, `requirements.txt`, `swarm.py`, `swarm_v2.py`, `v2/`, `artifacts/`) | B | Referenced by AGENTS.md §57 as project infrastructure, but `CT-PROD-RELEASE-MANIFEST-20260911-001` lists `agent_swarm/**` under **EXCLUDE / PO-decision-required**, and its `artifacts/` are generated. Code-vs-artefact intent unresolved. | HOLD FOR PO |
| `.github/workflows/playwright.yml` (untracked) | B | Real CI workflow (`on: push/pull_request` → `npm ci` → `npx playwright install` → `npx playwright test` → upload report). Adding it **enables automated CI on GitHub** for every push/PR — a process change — and the suite is env-dependent (skips when `E2E_*` unset). Intent not established from the repo. | HOLD FOR PO |
| `tools/seed_investor_demo/*.py` (14: `__init__`, `__main__`, `client`, `config`, `manifest`, `pipeline`, `reset`, `safety`, `seed_aux`, `seed_core`, `seed_documents`, `seed_messaging`, `synthetic`, `verify`) | B | The investor-demo seeder is infrastructure per AGENTS.md §54–§56, but the Release Manifest placed `tools/**` in **EXCLUDE / PO-decision-required**. Its data artefacts are now deliberately gitignored, indicating a "code yes / state no" intent needing confirmation. | HOLD FOR PO |
| `CARBONTALLY_AUDIT_FINDING_VERIFICATION.md` (root, untracked, 46 KB) | B | A genuine verification record, but at the repository root with no `docs/` home, and **no identically-named file under `docs/`** (0 matches) — placement/duplication policy is a PO choice. | HOLD FOR PO |
| `docs/Robie/getting this on live website.txt` (untracked) | B | A personal-directory note recording a **real production incident** (login failure at `https://carbontally.co.uk/login` while the Supabase DB server was unavailable) plus a requirement ("we need custom page design if service is not accessible") — outstanding work, but an informal note rather than a project document. | HOLD FOR PO |
| `package-lock.json` (root, modified, +3,938 lines) | B | A lock-file change with **no corresponding `package.json` change** in the working tree; intent (refresh vs EOL churn vs accidental) cannot be confirmed. | HOLD FOR PO |

### 7.3 C — MUST NOT PUBLISH (EXCLUDE)

| Path / pattern | Class | Reason | Evidence | Action |
|---|---|---|---|---|
| `admin/**` (67 modifications) | C | **Line-ending-only** change; content identical | `git diff --shortstat -- admin` = `19197 ins/19197 del`; `git diff -w --shortstat -- admin` = **empty** | EXCLUDE |
| `.agents/**` (69 modifications) | C | Line-ending-only | `git diff -w --shortstat -- .agents` = **empty** | EXCLUDE |
| `tools/carbon_data_factory/**` (29), `demodatagen/**` (13), `carbon-tally-ui-demo/**` (1), `shared/components/ManualEntryCore.jsx` (1) | C | Line-ending-only churn, no functional change; `ManualEntryCore.jsx` has **0** referrers in `frontend/`, `admin/`, `backend/` | `-w` diffs empty; referrer grep returned 0 | EXCLUDE |
| `supabase/config.toml` (modified) | C | Local development port remap only (54325→54425, 54326→54426, 54320→54420) — environment-specific, not product config | `git diff -- supabase/config.toml` | EXCLUDE |
| `supabase/snippets/Untitled query {303,407,673}.sql` | C | Supabase Studio scratch snippets (machine-local, untitled) | Paths/filenames | EXCLUDE |
| `CarbonTally_DB_Schema_V3M2.sql` (modified), `v3_schema.sql` (untracked) | C | Generated schema dumps of superseded eras; the 53 tracked migrations are the authority | Migration inventory + Release-Manifest generated-artefact class | EXCLUDE |
| `output/**` (13 D, 1 M, 7 ??), `screenshots/**` (96), `probe_out{,2..9}.txt` (9), `test_results.json`, `test_results_all.json`, `backend/test_results.json`, `clean_emissions_output.json`, `admin_log_viewer.feature.txt`, `mock_*.csv` (3), `v1.9.txt` | C | Generated run outputs / probe captures / test results / mock fixtures | Present as generated artefacts; Release-Manifest EXCLUDE class | EXCLUDE |
| `qa_harness/evidence/**` (138), `qa_harness/reports/**` (55), `qa_harness/carbontally_qa_harness.egg-info/**` (5) | C | Generated QA evidence/reports and Python build metadata | Directory semantics; Release Manifest lists `qa_harness/{evidence,reports}/**` as EXCLUDE | EXCLUDE |
| `e2e/environment/.acceptance_report.json`, `.lifecycle_evidence_report.json`, `.p6f_acceptance_report.json`, `.seed_report.json`; `e2e/environment/supabase/.temp/**` (2) | C | Disposable E2E/CLI run state | Untracked runtime JSON + Supabase CLI temp files | EXCLUDE |
| `agent_swarm_v2_artifacts/**` (97) | C | Generated swarm artefacts (`all_worker_results.json`, `repository_inventory.json`, `run_metadata.json`, `raw/*.json`, `screenshots/`, `MASTER_QA_REPORT.md`) | Contents are run outputs | EXCLUDE |
| `admin-dashboard.zip` (132,467,465 B) and any `*.zip` | C | Binary archive; also listed in `.clineignore` | File size/inspection | EXCLUDE |
| `.openhands/memory/*.md` (7) | C | Agent-session memory (local agent state) | Paths/type | EXCLUDE |
| `.clinerules/hooks/**` (13: `TaskStart`, `TaskComplete`, `TaskCancel`, `UserPromptSubmit`, `lib`, `settings.json`) | C | Agent-tool hook state | Directory role | EXCLUDE |
| `.claude/skills/prisma-*`, `.windsurf/skills/prisma-*` (18 entries) | C | **Machine-local symlinks pointing outside the repository** — `prisma-cli -> ./../../../carbon_ledger/.agents/skills/prisma-cli`; broken elsewhere and referencing a different local project directory | `ls -la .claude/skills` + `readlink` output | EXCLUDE |
| root `config.toml` (untracked) | C | Local MCP client config (`[mcp] shttp_servers = [{url = "http://localhost:8888/mcp/carbontally-full-ui/"}]`) | File content | EXCLUDE |
| `tests/example.spec.ts` | C | Playwright's stock scaffold targeting `https://playwright.dev/` — accidental | File content; `playwright.config.ts` `testDir` excludes it | EXCLUDE |
| `requirements.txt` (root, modified), `.clineignore`, `.vercelignore` (modified) | C | Line-ending-only | `-w` diffs empty | EXCLUDE |
| `API_ENDPOINTS.md`, `generate_api_docs.py`, `export_postman.py`, `list_endpoints.py`, `quick_api_ref.py`, `test_endpoints.py`, `generate_messy_{fuel,utility}_csv.py`, `clean.js`, `seed.ts`, `create_admin_dashboard.py` | C | Line-ending-only modifications to local dev utilities / locally generated docs; `create_admin_dashboard.py` scaffolds the **deprecated** legacy admin with placeholder `.env` values (`your-anon-key-here`) | `-w` diffs empty; CL-66 / D-P2-02 deprecation | EXCLUDE |
| `independent_audit/**` (1,840 files) | C | Excluded only via **`.git/info/exclude:9`** (not repo `.gitignore`) — not stageable; separate audit system per `docs/standalone/DUAL_TOOL_PORTABILITY_AUDIT.md` | `git check-ignore -v` → `.git/info/exclude` | EXCLUDE (not stageable) |
| Ignored-by-policy: `frontend/node_modules/**`, `node_modules/**`, `backend/.venv/**`, `.venv/**`, `myenv/**`, `qa_harness/.venv/**`, `.tmp_pgdata/**`, `website_candidate/**`, `local_backups/**`, all `.env*`, `.local-demo-credentials.md`, `tools/seed_investor_demo/{demo_manifest.json,.demo_state.json,DEMO_IDENTITIES.md}`, `**/__pycache__/**`, `.pytest_cache/**` | C | Local runtime state, secrets, caches, superseded website candidate, local DB data directory | `.gitignore` lines 9–11, 18–19, 39, 43, 47–49, 62, 83, 106 + `git check-ignore` | EXCLUDE |

## PHASE 8 — DELETIONS (152 tracked deletions, classified)

| Deleted paths | Count | Classification | Evidence |
|---|---|---|---|
| `.claude/skills/prisma-*/**` | 69 | **Intentional** (tooling consolidation) | The same 9 skill trees now exist once as tracked files in `.agents/skills/**` (69 files) and once as **machine-local symlinks** at `.claude/skills/prisma-*`. The duplicated per-tool copies are redundant; removal is deliberate, not accidental. |
| `.windsurf/skills/prisma-*/**` | 69 | **Intentional** | Identical pattern to `.claude` (symlinks present; tracked copies live in `.agents/skills/**`). |
| `output/json/*.json` (8), `output/reports/*.md` (5), `output/sql/import_defra_2025.sql` | 13 (+1 modified `output/**` file) | **Generated-artifact deletion** | Pipeline run outputs (import/mapping/validation reports, duplicates, imported rows) reproducible by the importer; Release-Manifest EXCLUDE class. |
| `frontend/src/StaffDashboard.jsx` | 1 | **Obsolete-legacy deletion** | Release manifest: *"grep proves `StaffDashboard.jsx` has **zero remaining imports**, so accepting that deletion cannot break the build."* Superseded by the V3 `/ops` staff surface. |

* **No** deletion is classified accidental.
* **No** deletion materially alters the production application: no `backend/**`, `frontend/src/v3/**`,
  `admin/**`, `supabase/**` or deployment file is deleted. The single application-surface deletion
  (`StaffDashboard.jsx`) is unreferenced.
* **Explicit flag:** a future commit including these deletions must **not** also delete `.agents/skills/**`
  (the canonical retained copy) — otherwise the skill trees are removed entirely.
* `admin/` must **not** be deleted in any form (quarantined-not-deleted policy; PHASE 5.B).

## PHASE 9 — DUPLICATES / CONFLICTS (reported, not resolved)

| ID | Item | Nature | Recommendation |
|---|---|---|---|
| **C1** | "Backup/DR = PARKED" (`CARBONTALLY_PHASE6_CLOSURE_AND_RELEASE_BOUNDARY_20260911.md` §7) **vs** the implemented + independently verified `backend/backup/**` and the 9 `CT-PROD-BACKUP-*` records | **Temporal conflict.** The backup prompts post-date the closure document; the roadmap/blueprint contain **no** backup reference (grep: one unrelated "restore" hit) | PO to confirm the newer state governs; schedule a roadmap/blueprint amendment |
| **C2** | `admin/**` (legacy CRA at `/admin/*`, still built/deployed by root `package.json`) **vs** `frontend/src/v3/admin/**` + `/ops` (V3-canonical) | **Competing admin implementations**, deliberately coexisting (CL-66 / D-P2-02) | No action; do not delete legacy until its 4 retirement conditions are met |
| **C3** | `supabase/migrations/**` (53) **vs** `e2e/environment/supabase/migrations/**` (53) | Duplicate schema lineage (isolated E2E environment) | Keep both; note for the future repo-split strategy |
| **C4** | `frontend_backup_pre_v3_public_20260827/**` (tracked, already on origin) **vs** `frontend/**`; `website_candidate/**` (ignored) | Retained pre-V3 front-end copy | PO decision on future removal (out of scope here) |
| **C5** | `v3_schema.sql` (untracked) + `CarbonTally_DB_Schema_V3M2.sql` (tracked) **vs** the 53 migrations | Stale generated schema copies | EXCLUDE (already C) |
| **C6** | `tools/carbon_data_factory/**` (tracked) **vs** `demodatagen/**` (tracked) **vs** `tools/seed_investor_demo/**` (new) | Overlapping demo/dataset tooling | PO decision (B) on which are canonical |
| **C7** | `docs/standalone/REPOSITORY_STRATEGY.md` + `OPEN_SOURCE_SECURITY_CHECKLIST.md` (tracked; "the standalone repository will be public") **vs** `saas-assurance/**` living inside this repo | Strategy says separate public repo; the tree is here | PO decision (B) |
| **C8** | Root `playwright.config.ts` (testDir `tests/e2e`) **vs** `tests/example.spec.ts` (stock scaffold) | Competing Playwright entry points | EXCLUDE the example (C); keep the config (A) |
| **C9** | Root `config.toml` (MCP client, untracked) **vs** `supabase/config.toml` (tracked) | Name collision, unrelated purposes | EXCLUDE root `config.toml` (C) |
| **C10** | Roadmap §13 still says "NEXT GATE: P6-2C" while Phase 6 is closed | **Stale authoritative document** | PO/coordinator update per roadmap §16 change-control |

## PHASE 10 — PUBLICATION COMPLETENESS (explicit answers)

1. **Does `origin/main` + existing committed commits represent the complete intended CarbonTally development
   state?** **No** — it lacks everything in PHASE 4/7-A still uncommitted, and it is **30 commits behind**
   HEAD.
2. **What intentional uncommitted work is missing?** The backup subsystem (17 files), `cryptography` in
   `backend/requirements.txt`, the `.gitignore` ignores, 8 production/backup architecture documents,
   10 legal documents, the PO decision register, 18 prompt-history records (incl. this one), `AGENTS.md`,
   `playwright.config.ts`, QA Harness v1.1/v1.2 code (67 files), the 152 pending deletions — plus the seven
   B-items.
3. **Does intentional pre-Phase-1 work remain unpublished?** The pre-Phase-1 **history** is already
   published (both root lineages merged at `c36c848`; tags `rc2-final`, `v2.1.1-phase3`, `v2.1-phase4`).
   Pre-Phase-1 **tree content** was not carried forward by design ("verified V3 tree preserved").
   Working-tree Phase-1-era remnants (legacy-admin EOL churn, `create_admin_dashboard.py`,
   `admin-dashboard.zip`, `shared/**`, `carbon-tally-ui-demo/**`, `demodatagen/**`,
   `tools/carbon_data_factory/**`, stale schema dumps, root probes/mocks) are **C**.
4. **Does the working tree contain production code that must be included?** Yes, but **only two files**:
   `backend/requirements.txt` and `.gitignore`. All other production source reached HEAD via `daad396`.
5. **Does the working tree contain the newly implemented production backup subsystem that should be
   included?** **Yes** — `backend/backup/**` (9 modules), 8 tests, 5 documents, and the `cryptography`
   dependency. Classified **A** (PO-ratified D1–D5, implemented, independently verified twice).
6. **Are there migrations that should be published but not applied?** **18 committed-but-unpushed
   migrations** (in `17665d0`/`daad396`) are published by a push. **No uncommitted migration exists**, and
   **applying** them remains unauthorized and unperformed.
7. **Are there files that must NOT be published?** Yes — PHASE 7.3 (C): every `.env*` (already ignored),
   generated output, QA evidence/reports, screenshots/probes, archives (incl. a 132 MB zip), agent state,
   machine-local symlinks, local env config, deprecated/demo tooling, and all line-ending-only
   modifications.
8. **Are there deletions that must be preserved?** Yes — the 152 in PHASE 8 are intentional and should
   accompany the publication, but **not** alongside a deletion of `.agents/skills/**`.
9. **Are there ambiguous files requiring PO confirmation?** Yes — the seven B-items and conflicts
   C1–C10.
10. **Is it technically safe to proceed to a later staging/commit review after this reconstruction?**
    **Technically yes** (explicit A-set, no security-blocking artefact, no secret in scope). **Procedurally
    no** until the PO resolves the B-items and conflicts C1/C2/C3/C6/C7, because they determine whether the
    publication is A-only or A+B.

## PHASE 11 — EXACT NEXT-STEP INSTRUCTIONS

### A. SAFE TO STAGE (A — MUST PUBLISH; 107 files)

```text
backend/backup/__init__.py  backend/backup/artifact.py  backend/backup/catalog.py  backend/backup/crypto.py
backend/backup/errors.py  backend/backup/exporter.py  backend/backup/service.py  backend/backup/settings.py
backend/backup/storage.py
backend/tests/unit/backup/__init__.py  backend/tests/unit/backup/test_artifact.py
backend/tests/unit/backup/test_crypto.py  backend/tests/unit/backup/test_service.py
backend/tests/unit/backup/test_storage_and_settings.py  backend/tests/unit/backup/test_p1_1_remediation.py
backend/tests/integration/backup/__init__.py  backend/tests/integration/backup/test_exporter_local.py
backend/requirements.txt                       (modified: cryptography>=41.0.0)
.gitignore                                     (modified: demo + Playwright ignores)
AGENTS.md
playwright.config.ts
docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md
docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_IMPLEMENTATION_PHASE1_20260911.md
docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_P1_1_N1_INDEPENDENT_VERIFICATION_20260911.md
docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_PHASE1_1_INDEPENDENT_VERIFICATION_20260911.md
docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_RESTORE_ROADMAP_V1.0.md
docs/architecture/CARBONTALLY_PRODUCTION_DEPLOYMENT_READINESS_20260911.md
docs/architecture/CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md
docs/architecture/CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md
docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md
docs/legal/CARBONTALLY_LEGAL_RISK_REGISTER.md
docs/legal/CARBONTALLY_POLICY_PRODUCT_CONSISTENCY_AUDIT.md
docs/legal/CARBONTALLY_THIRD_PARTY_PROCESSOR_REGISTER.md
docs/legal/draft/CARBONTALLY_COOKIE_POLICY_DRAFT.md
docs/legal/draft/CARBONTALLY_DATA_RETENTION_ARCHIVAL_ANONYMIZATION_POLICY_DRAFT.md
docs/legal/draft/CARBONTALLY_DPA_DRAFT.md
docs/legal/draft/CARBONTALLY_MSA_DRAFT.md
docs/legal/draft/CARBONTALLY_PRIVACY_POLICY_DRAFT.md
docs/legal/draft/CARBONTALLY_REFUND_POLICY_DRAFT.md
docs/legal/draft/CARBONTALLY_TERMS_OF_SERVICE_DRAFT.md
docs/cline/prompt-history/CT-PHASE6-COMMIT-20260911-001.md
docs/cline/prompt-history/CT-PHASE6-PUSH-AUDIT-20260911-001.md
docs/cline/prompt-history/CT-PROD-BACKUP-ARCHITECTURE-20260911-001.md
docs/cline/prompt-history/CT-PROD-BACKUP-DECISIONS-20260911-002.md
docs/cline/prompt-history/CT-PROD-BACKUP-DR-ROADMAP-DOC-20260911-001.md
docs/cline/prompt-history/CT-PROD-BACKUP-IMPLEMENTATION-20260911-001.md
docs/cline/prompt-history/CT-PROD-BACKUP-IV-20260911-001.md
docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-IMPLEMENTATION-20260911-001.md
docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-IV-20260911-001.md
docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-N1-IMPLEMENTATION-20260911-001.md
docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-N1-IV-20260911-001.md
docs/cline/prompt-history/CT-PROD-DEPLOYMENT-READINESS-20260911-001.md
docs/cline/prompt-history/CT-PROD-MIGRATION-PREP-20260911-001.md
docs/cline/prompt-history/CT-PROD-RELEASE-COMMIT-20260911-001.md
docs/cline/prompt-history/CT-PROD-RELEASE-COMMIT-CORRECTION-20260911-001.md
docs/cline/prompt-history/CT-PROD-SUPABASE-RECON-20260911-001.md
docs/cline/prompt-history/CT-PROD-SUPABASE-RECON-20260911-002.md
docs/cline/prompt-history/CT-PROD-PUBLICATION-RECON-20260911-001.md      (this file)
qa_harness/__init__.py  qa_harness/Makefile  qa_harness/pyproject.toml  qa_harness/README.md
qa_harness/requirements.txt
qa_harness/core/**  qa_harness/api/**  qa_harness/db/**  qa_harness/agents/**  qa_harness/rules/**
qa_harness/identities/**  qa_harness/visual/**  qa_harness/findings/**  qa_harness/workflows/**   (62 files)
```

### B. HOLD FOR PO

`saas-assurance/**` (217) · `agent_swarm/**` (39) · `.github/workflows/playwright.yml` ·
`tools/seed_investor_demo/*.py` (14) · `CARBONTALLY_AUDIT_FINDING_VERIFICATION.md` ·
`docs/Robie/getting this on live website.txt` · `package-lock.json` (modified).

### C. DO NOT STAGE

`admin/**` · `.agents/**` · `.claude/skills/**` · `.windsurf/skills/**` · `.clinerules/**` ·
`.openhands/**` · `tools/carbon_data_factory/**` · `demodatagen/**` · `carbon-tally-ui-demo/**` ·
`shared/**` · `agent_swarm_v2_artifacts/**` · `independent_audit/**` · `output/**` · `screenshots/**` ·
`qa_harness/evidence/**` · `qa_harness/reports/**` · `qa_harness/*.egg-info/**` · `e2e/environment/*.json`
and `e2e/environment/supabase/.temp/**` · `supabase/config.toml` · `supabase/snippets/**` ·
`v3_schema.sql` · `CarbonTally_DB_Schema_V3M2.sql` · `admin-dashboard.zip` · `tests/example.spec.ts` ·
root `config.toml` · root `requirements.txt` · `API_ENDPOINTS.md` · `probe_out*.txt` ·
`test_results*.json` · `clean_emissions_output.json` · `admin_log_viewer.feature.txt` · `mock_*.csv` ·
`v1.9.txt` · `.clineignore` · `.vercelignore` · `create_admin_dashboard.py` · `generate_*.py` ·
`export_postman.py` · `list_endpoints.py` · `quick_api_ref.py` · `test_endpoints.py` · `clean.js` ·
`seed.ts` · all ignored paths (`.env*`, `node_modules/**`, `.venv/**`, `.tmp_pgdata/**`,
`website_candidate/**`, `local_backups/**`, `DEMO_IDENTITIES.md`, `demo_manifest.json`,
`.demo_state.json`, `__pycache__/**`, `.pytest_cache/**`).

### D. REQUIRED DELETION SET

`.claude/skills/**` (69) · `.windsurf/skills/**` (69) · `output/json/**` + `output/reports/**` +
`output/sql/import_defra_2025.sql` (13) · `frontend/src/StaffDashboard.jsx` (1) — **152 total**, all
intentional (PHASE 8). Must not be accompanied by deleting `.agents/skills/**` or `admin/**`.

### E. MIGRATION SET (publication vs application)

* **Publication (via push of existing commits):** the 18 migrations listed in PHASE 5.C — already committed
  by `17665d0` (1) and `daad396` (17). Nothing to stage.
* **Application:** **NONE AUTHORISED.** No migration may be applied; production live state is UNKNOWN
  pending the separately authorised read-only reconciliation.

### F. RELEASE CONTENT SUMMARY

If the A-set were committed on top of `c864d72`, the accumulated CarbonTally development state would be
complete with respect to the backup subsystem, the QA Harness, the governance/legal/PO documentation and the
intentional deletions: **+107 files staged**, **152 deletions recorded**, and no application-source change
beyond `backend/requirements.txt` (+`cryptography`) and `.gitignore`. Combined with the 30 unpushed commits,
`origin/main` would then carry backend/frontend V3 product work (Phases A–L + Phase 6), 53 migrations, the
production backup subsystem, the QA Harness v1.1/1.2, the E2E environment, the full documentation corpus,
and the corrected ignore policy.

### G. RISKS

1. **CI activation (B).** Publishing `.github/workflows/playwright.yml` enables Playwright CI on every
   push/PR; the suite skips without `E2E_*` (no false acceptance) but it will run.
2. **Push may equal deploy.** Root `vercel.json` + `package.json` mean a `main` push can trigger a Vercel
   (and possibly Render) production deployment; deploying remains unauthorised.
3. **Migration publication vs application.** Pushing publishes 18 migration files; applying them is
   explicitly NOT AUTHORISED — the distinction must be preserved in the commit/PR narrative.
4. **Line-ending noise.** 178 modified files are EOL-only; mis-staging them (e.g. `git add -A`) would create
   a ~35,000-line no-op diff and hide the real changes.
5. **Separate-product leakage (B).** `saas-assurance/**` and `agent_swarm/**` are separate-product/tooling
   trees; publishing them into the product repository contradicts the recorded standalone-repo strategy.
6. **Secret safety rests on ignore rules.** Nothing tracked contains a secret, but the `.env*` family,
   `local_backups/env_backup/.env*` and `DEMO_IDENTITIES.md` exist on disk and rely on `.gitignore` /
   `/local_backups/` plus agent discipline.
7. **`independent_audit/**` is excluded only via `.git/info/exclude`** (machine-local, not repo policy).
8. **Stale authoritative docs (C10)** — the roadmap still points at P6-2C.

### H. NEXT COMMAND

No `git add` command is issued: the manifest is **not** unambiguous, because seven B-items and conflicts
C1/C2/C3/C6/C7 determine the publication's shape. Therefore:

**PO DECISION REQUIRED BEFORE STAGING**

Confirm at minimum: (i) whether `saas-assurance/**` and `agent_swarm/**` are published here or elsewhere;
(ii) whether the Playwright CI workflow is to be enabled; (iii) whether `tools/seed_investor_demo/**` code
is published; (iv) whether `CARBONTALLY_AUDIT_FINDING_VERIFICATION.md`, `docs/Robie/*.txt` and
`package-lock.json` are included, relocated or excluded; (v) that the A-set (107 files) plus the 152
deletions constitute the commit; and (vi) that no deployment follows the push.

---

## FINAL VERDICT

**PUBLICATION RECONSTRUCTION COMPLETE — PO DECISION REQUIRED**

### Attestation

* **Files inspected:** the git boundary/history/reflog/refs/tags/remotes; all 30 commits' name-status output;
  `admin/{package.json,README.md,src/**,serve.py,server.js,public/**}`; `backend/backup/*.py` (9);
  `backend/tests/{unit,integration}/backup/**`; `backend/requirements.txt`; the `.gitignore`/`.clineignore`/
  `.vercelignore` diffs; `AGENTS.md`; `playwright.config.ts`; `.github/workflows/playwright.yml`;
  `tests/example.spec.ts`; root configs (`package.json`, `vercel.json`, `config.toml`, `requirements.txt`,
  `admin-dashboard.zip`, `v3_schema.sql`, `CarbonTally_DB_Schema_V3M2.sql`, `probe_out*.txt`);
  `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`,
  `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`,
  `docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md`,
  `docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md`,
  `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md`,
  `docs/architecture/CARBONTALLY_PHASE6_CLOSURE_AND_RELEASE_BOUNDARY_20260911.md`,
  `docs/cline/prompt-history/CT-PROD-RELEASE-MANIFEST-20260911-001.md`,
  `docs/cline/prompt-history/CT-PROD-BACKUP-DECISIONS-20260911-002.md`,
  `docs/standalone/{REPOSITORY_STRATEGY,OPEN_SOURCE_SECURITY_CHECKLIST,DUAL_TOOL_PORTABILITY_AUDIT}.md`,
  `docs/legal/CARBONTALLY_LEGAL_RISK_REGISTER.md`, `docs/Robie/getting this on live website.txt`,
  `qa_harness/{pyproject.toml,README.md,core/*.py}`, `saas-assurance/**` listing, `agent_swarm/**` listing,
  the `.claude`/`.windsurf` symlink targets, `tools/seed_investor_demo/**` listing, and the
  `independent_audit/**` ignore rule.
* **Commands executed (all read-only):** `git status --short --branch`; `git status --porcelain=v1 -uall`;
  `git branch -a` / `-vv`; `git tag`; `git remote -v`; `git rev-parse`; `git rev-list
  --count/--all/--max-parents=0`; `git merge-base`; `git log` (oneline/decorate/reverse/merges/`--all`/
  `--name-only`/`--stat`/`--diff-filter`); `git reflog --date=iso`; `git show`; `git ls-tree -r -l`;
  `git ls-files --others [--ignored]`; `git cat-file -e`; `git check-ignore -v`; `git diff`
  (`--name-only`/`--name-status`/`--numstat`/`--shortstat`/`--stat`/`--ignore-all-space`/`--cached`);
  plus `grep`, `ls -la`, `readlink`, `wc`, `find`, `head` and local Python aggregation scripts. No
  write-capable git command was executed.
* **Tests executed:** **none** — this is a static reconstruction; AGENTS.md §73 forbids claiming "tested"
  where nothing was executed.
* **Tests NOT executed:** the whole `qa_harness/` suite, `backend/tests/**`, and the `tests/e2e` Playwright
  specs (they require the isolated E2E environment and injected credentials); no lint/type check.
* **Production systems contacted:** **NO.**
* **Supabase modified:** **NO.**
* **Files modified by this agent:** **ONLY THE REQUIRED HISTORY REPORT**
  (`docs/cline/prompt-history/CT-PROD-PUBLICATION-RECON-20260911-001.md`).
* **Files deleted:** **NO.** · **Files staged:** **NO.** · **Commit created:** **NO.** · **Push performed:**
  **NO.** · **Deploy / migration application / backup execution:** **NO.**
* **Worktree preservation:** all pre-existing modified, deleted, untracked and ignored state is unchanged;
  the only delta is this report file (untracked).

**STOPPED after writing this reconstruction report.** No staging, no commit, no push, no deploy, no
application-code change, no migration change, no repository "clean-up". The next operation is separately
authorised by the Product Owner after reviewing this manifest.
