# CT-PROD-PUBLICATION-STAGING-PREP-20260911-001

**Prompt Ref:** `CT-PROD-PUBLICATION-STAGING-PREP-20260911-001`
**Response Ref:** `CT-PROD-PUBLICATION-STAGING-PREP-20260911-001-R1`
**Datetime:** 2026-09-11
**Mode:** **BOUNDED PRE-STAGING** — nothing staged, committed, pushed, deployed; no migration created/modified/
reordered/applied; no production contact; no application or migration file modified.
**Reconstruction source:** `docs/cline/prompt-history/CT-PROD-PUBLICATION-RECON-20260911-001.md`
(624 lines, sha256 `db5b03766c80baf1…`, re-read in full for the A/B/C sets — no A list was reconstructed from
memory).
**Starting HEAD:** `c864d729526ef2c5e40cd19fdc451e8f0975144b`
**`origin/main`:** `6148c86826e25e1889d8cf86bb02dbb2901577c6` · **branch:** `main` · **ahead 30 / behind 0**

## EXECUTIVE SUMMARY

The reconstruction's boundary has been **re-verified against the live repository** and an exact,
path-level staging candidate is produced: **123 A-files** to publish and **152 intentional deletions**,
with the PO's seven B-item decisions applied. Three findings refine the reconstruction:

1. **A-count correction.** The reconstruction reported "A-total: 107"; the verified expansion of its own
   component tables is **125 files** (an arithmetic slip in the summary line, not a boundary error).
2. **One safety refinement (A → C).** `qa_harness/findings/{raw,normalized,deduplicated}/*.jsonl` are
   **generated QA run output** (413 raw / 413 normalized / 83 deduplicated records, `source: run_db.py`,
   timestamped 2026-08-31), not code — `store.py` documents them as the run's persistence stages. They are
   removed from the candidate, exactly like `qa_harness/evidence/**` and `reports/**`. `findings/__init__.py`
   and `findings/store.py` (code) remain in A.
3. **`package-lock.json` resolved: INCLUDE.** The working-tree lock now matches the committed `package.json`
   **exactly** on all 15 dependency entries, and its diff is precisely the realignment to `daad396`'s
   committed pins (`prisma ^7.9.1→^6.12.0`, `@snaplet/seed ^0.98.0→^0.89.6`, plus `@playwright/test`,
   `@types/node`). No production impact (the Vercel build uses `frontend/` and `admin/`, each with its own
   tracked lock).

No material contradiction to the PO boundary was found. Two non-blocking observations are recorded (§10).

## §1 — PHASE 1: BOUNDARY RE-VERIFICATION (not assumed)

| Check | Reconstruction | Now | Status |
|---|---|---|---|
| Reconstruction report exists | — | yes, 624 lines, sha256 `db5b0376…` | ✔ |
| Branch | `main` | `main` | unchanged |
| HEAD | `c864d729526ef2c5e40cd19fdc451e8f0975144b` | identical | unchanged |
| `origin/main` | `6148c86826e25e1889d8cf86bb02dbb2901577c6` | identical | unchanged |
| Ahead / behind | 30 / 0 | 30 / 0 | unchanged |
| **Staged files** | **0** | **0** (`git diff --cached --name-status` → empty) | unchanged |
| Modified tracked | 210 | 210 | unchanged |
| Deleted tracked | 152 | 152 | unchanged |
| Untracked (non-ignored) | 853 | 853 | unchanged |
| `git reflog` head | `c864d72 commit: feat: close CarbonTally Phase 6…` | identical | unchanged |

**Conclusion:** the repository has not changed except for the reconstruction report itself. The boundary on
which the PO decisions were made is still the live boundary.

## §2 — PHASE 2: A-PATH RE-VERIFICATION

Every A path from the reconstruction's tables was expanded to exact files and checked for: existence,
non-generated content, absence of secret material, no E2E/local state, no accidental duplication, and
consistency with authoritative documentation. Result: **all exist; none missing; none already staged**.

| Group | Files | Verification |
|---|---|---|
| `backend/backup/` | 9 | all present (`__init__` 2,422 B … `catalog.py` 27,274 B) |
| `backend/tests/{unit,integration}/backup/` | 8 | present (6 unit + 1 integration + 2 `__init__`) |
| `backend/requirements.txt` | 1 | modified (`M`), contains only the additive `cryptography>=41.0.0` block |
| `.gitignore` | 1 | modified (`M`), +13 lines (demo + Playwright ignores) |
| `docs/architecture/` (production/backup set) | 8 | present (5 backup + deployment readiness + migration safety + supabase reconciliation) |
| `docs/legal/` | 10 | present (3 registers/audits + 7 `draft/` policies) |
| `docs/ChatGPT/` PO decision register | 1 | present (17,442 B) |
| `AGENTS.md`, `playwright.config.ts` | 2 | present at root, untracked |
| `docs/cline/prompt-history/` untracked records | 18 | present (incl. the reconstruction report) |
| `qa_harness/` (code + metadata) | 67 → **64** | 67 present; **3 `.jsonl` run-data files removed** (see §2.1) |
| **Sub-total** | **125 → 122** | |
| plus this report | +1 | `CT-PROD-PUBLICATION-STAGING-PREP-20260911-001.md` |
| **FINAL A ALLOWLIST** | **123** | |

### 2.1 Safety refinement applied to the candidate (A → C)

`qa_harness/findings/raw/raw.jsonl` (413 lines), `…/normalized/normalized.jsonl` (413),
`…/deduplicated/deduplicated.jsonl` (83) are **run output**, not source:
`qa_harness/findings/store.py` states *"Finding persistence across the three stages (spec §28, §30) — raw/
every finding exactly as produced (JSON lines); normalized/ normalized + assigned QA-<CAT>-NNN ids;
deduplicated/ canonical findings after deduplication."* Sample record: `{"id": "QA-DB-001", "category":
"DB", "severity": "P1", "title": "Missing table: storage_buckets", …, "source": "run_db.py", "timestamp":
"2026-08-31T09:30:11+00:00"}`. They are the same class as the already-excluded `qa_harness/evidence/**`
and `qa_harness/reports/**` → **EXCLUDE**. The `findings/` **code** (`__init__.py`, `store.py`) stays in A.
After this removal, **every remaining file in the `qa_harness` A subdirectories is `.py` or build metadata**
(verified: non-code files in `core|api|db|agents|rules|identities|visual|findings|workflows` = 3, all now
excluded).

## §3 — PHASE 3: EXCLUSION VERIFICATION

Every excluded group was confirmed **still present in the working tree** and **not staged** (so nothing has
silently moved into the candidate):

| Excluded tree | Status entries | Staged | Verified as |
|---|---|---|---|
| `admin/**` (legacy CRA) | 67 | 0 | EOL-only churn (`-w` diff empty); quarantined-not-deleted per CL-66 / D-P2-02 |
| `.agents/skills/**` | 69 | 0 | EOL-only churn; canonical retained skill copy (must not be deleted) |
| `.claude/skills/**` | 78 (69 D + 9 ??) | 0 | deletions + **machine-local symlinks** outside the repo |
| `.windsurf/skills/**` | 78 (69 D + 9 ??) | 0 | same as above |
| `screenshots/**` | 96 | 0 | generated captures |
| `qa_harness/evidence/**` | 138 | 0 | generated QA evidence |
| `qa_harness/reports/**` | 55 | 0 | generated QA reports |
| `qa_harness/*.egg-info/**` | 5 | 0 | Python build metadata |
| `output/**` | 21 (13 D, 7 ??, 1 M) | 0 | generated pipeline output |
| `saas-assurance/**` | 217 | 0 | PO: DO NOT PUBLISH (separate framework) |
| `agent_swarm/**` | 39 | 0 | PO: DO NOT PUBLISH |
| `agent_swarm_v2_artifacts/**` | 97 | 0 | generated swarm artefacts |
| `.openhands/**` | 7 | 0 | agent session memory |
| `.clinerules/**` | 13 | 0 | agent hook tooling |
| `demodatagen/**` | 13 | 0 | EOL-only churn |
| `carbon-tally-ui-demo/**`, `shared/**` | 1 + 1 | 0 | EOL-only; `ManualEntryCore.jsx` has 0 referrers |
| `tools/carbon_data_factory/**` | 29 | 0 | EOL-only churn |
| `tests/example.spec.ts` | 1 | 0 | Playwright stock scaffold |
| `independent_audit/**`, `node_modules/**`, `frontend/node_modules/**`, `backend/.venv/**`, `.tmp_pgdata/**`, `website_candidate/**`, `local_backups/**` | 0 (ignored) | 0 | ignored / not stageable |

Single-artifact exclusions re-confirmed **present and unstaged**: `supabase/config.toml` (M, local port
remap), `config.toml` (??, MCP client config), `requirements.txt` (M, EOL-only), `API_ENDPOINTS.md` (M),
`v3_schema.sql` (??), `CarbonTally_DB_Schema_V3M2.sql` (M), `admin-dashboard.zip` (??, 132 MB),
`CARBONTALLY_AUDIT_FINDING_VERIFICATION.md` (??), `docs/Robie/getting this on live website.txt` (??),
`package-lock.json` (**M — decision in §6**), `supabase/snippets/Untitled query {303,407,673}.sql`,
`.github/workflows/playwright.yml` (?? — PO HOLD).

## §4 — PHASE 4: BACKUP PUBLICATION VERIFICATION

| Requirement | Result |
|---|---|
| `backend/backup/**` in the candidate | **Yes** — 9 modules, 2,449 lines |
| Associated tests in the candidate | **Yes** — 6 unit + 1 integration (+2 `__init__`) |
| Associated documentation | **Yes** — 5 `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_*.md` |
| Durability established | **Yes** — `CT-PROD-BACKUP-DECISIONS-20260911-002` records PO-ratified **D1–D5**; implementation report + two independent verifications (P1.1, P1.1-N1) |
| Production credentials present | **None** — no JWT/PEM/service key/credential DSN anywhere in the candidate (§8) |
| Backup **artifacts** present | **None** — no `.dump`, `.backup`, `.enc`, `.gpg`, `.age`, `.tar`, `.gz`, `.zip` in the candidate |
| Production backup executed | **No** — D5 records the role was never created and no SQL ran |
| Migration / role SQL added accidentally | **No `.sql` file in the candidate at all** (count = 0). `CREATE ROLE ct_backup …` appears **only as documented design DDL inside `CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md`**; the verification records state *"New privileged roles: **None** — no `CREATE ROLE`/`GRANT`"* and *"D5 — production role not created: no SQL was executed"* |
| Restore implementation introduced | **No** — `def restore|class Restore|restore_job` matches inside the candidate = **0** (restore is design-only, D4) |

Confirmed unchanged: no production backup executed, no restore executed, no `ct_backup` role creation, no
migration application, no deployment.

## §5 — PHASE 5: MIGRATION BOUNDARY (TABLE 5)

Repo state: `supabase/migrations/` = **53 tracked at HEAD**, **0 uncommitted changes**, **0 files in the
staging candidate**. The isolated E2E tree `e2e/environment/supabase/migrations/` = **53 tracked, 0
uncommitted** (already committed; separate environment lineage).

| Migration (committed set) | Publication status | Application status |
|---|---|---|
| 35 migrations already on `origin/main` | already published | not applied by this operation; live production state UNKNOWN |
| `20260829000000_v3m9_durable_automatic_processing.sql` (`17665d0`) | committed, **unpublished → published by a future push** | NOT AUTHORIZED / not applied |
| `20260831000000_v3m10_org_membership_unique.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260831010000_v3m11_operational_indexes.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260831020000_audit_activity_immutability.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260831030000_tenant_org_id_not_null.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260831040000_consultant_revocation_roles.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260902020000_v1_2_dual_origin_workflow.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260902030000_phase5_work_item_assignments.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260902040000_phase5_pe_operational_messaging.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260902050000_phase5_notification_event_key.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260905000000_gate4_actor_provenance.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260905010000_gate5_t1_automation_provenance.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260905020000_gate5_t6_automation_write_once_guard.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260906010000_gate6_w1_automation_extracted_output.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260906090000_p6_1c_consultant_engagement.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260906100000_p6_2a_consultant_processing_permissions.sql` | committed, unpublished | NOT AUTHORIZED / not applied |
| `20260910120000_p6_2d_consultant_provenance.sql` | committed, unpublished | NOT AUTHORIZED / not applied |

> **PUBLICATION STATUS ≠ MIGRATION APPLICATION STATUS.** Publishing migration files places them in the
> repository/push stream. **Applying** them to any database is a separate, unauthorised operation. This
> preparation neither creates, modifies, reorders nor applies any migration, and no production Supabase
> connection was made.

## §6 — PHASE 6: PACKAGE-LOCK FOCUSED REVIEW

Read-only comparison of `package.json` (HEAD, unmodified), `package-lock.json` (working tree, modified),
`frontend/package.json` + `frontend/package-lock.json`, `admin/package-lock.json`, the build script and
`vercel.json`.

| Question | Finding |
|---|---|
| Does the lock correspond to the current intended `package.json`? | **YES.** All 15 entries match exactly: `dependencies` — faker `^10.5.0`, `@prisma/adapter-pg` `^7.9.1`, `@radix-ui/react-popover` `^1.1.23`, `@snaplet/seed` `^0.89.6`, `@supabase/realtime-js` `^2.111.0`, `@supabase/supabase-js` `^2.111.0`, `pg` `^8.22.0`, `prisma` `^6.12.0`, `react-hot-toast` `^2.6.0`, `tsx` `^4.23.5`; `devDependencies` — `@playwright/test` `^1.62.1`, `@prisma/client` `^7.9.1`, `@snaplet/copycat` `^6.0.0`, `@types/node` `^26.4.0`, `@types/pg` `^8.20.3` → **0 MISMATCH** |
| Are `package.json` / `package-lock.json` internally consistent? | **YES for the reviewed pair.** The lock's diff is exactly the realignment to those pins (`- "@snaplet/seed": "^0.98.0"` → `+ "^0.89.6"`; `- "prisma": "^7.9.1"` → `+ "^6.12.0"`; `+ "@playwright/test"`; `+ "@types/node"`), and resolved versions agree (`prisma 6.12.0`, `@snaplet/seed 0.89.6`, `@prisma/client 7.9.1`, `@playwright/test 1.62.1`, `@types/node 26.4.0`) |
| Is the change intentional? | **YES.** It repairs the pre-existing inconsistency where the committed `package.json` (downgraded by `daad396`) disagreed with its lock |
| Does it materially affect production? | **NO** — `lockfileVersion 3`, 530 packages, monorepo root only (no `frontend/`/`admin/` workspace entries); the root deps are dev/seed tooling |
| Is the lock required for the actual frontend build? | **NO.** The root `build` script runs `cd frontend && npm install && npm run build && cd ../admin && npm install && npm run build …`; `frontend/package-lock.json` (750,762 B) and `admin/package-lock.json` (723,189 B) are separate, already tracked and **unmodified** |
| Merely accidental/generated churn? | **NO** — a coherent dependency-tree change (3,938 insertions / 3,742 deletions) |

### DECISION: **PACKAGE-LOCK — INCLUDE**
Staged as a single modified file. Residual observation (non-blocking, pre-existing, **not** corrected here
because `package.json` is out of scope): its `allowScripts` keys still name the superseded pins
(`@snaplet/seed@0.98.0`, `prisma@7.9.1`, `@prisma/engines@5.14.0-dev.34`, `@prisma/engines@7.9.1`,
`esbuild@0.28.1`) — see §10.

## §7 — PHASE 7: DELETION VERIFICATION (TABLE 4)

`git ls-files -d` = **152** tracked deletions, unchanged, **none restored** (all four samples verified absent
from disk). `git diff --cached` = 0, so no deletion has been staged.

| Path group | Files | Reason | Replacement / evidence |
|---|---|---|---|
| `.claude/skills/prisma-*/**` | 69 | Intentional — per-tool duplicate copies replaced by local symlinks; the canonical copy is tracked | `.agents/skills/**` = **69 tracked files** (verified); `.claude/skills/prisma-*` now 9 machine-local symlinks → `./../../../carbon_ledger/.agents/skills/prisma-*` (excluded as C) |
| `.windsurf/skills/prisma-*/**` | 69 | Identical pattern | Same as above (`.windsurf/skills/prisma-*` are symlinks too) |
| `output/json/*.json` (8), `output/reports/*.md` (4), `output/sql/import_defra_2025.sql` (1) | 13 | Generated pipeline output | Reproducible by the importer; `output/` also holds untracked generated dirs (`logs/`, `seai_2025/`) |
| `frontend/src/StaffDashboard.jsx` | 1 | Obsolete legacy UI | **0 imports**: greps find only `admin/src/pages/staff/StaffDashboard.js` + `admin/src/App.js` (a *different, legacy-CRA* file that remains, untouched); the V3 staff surface is `frontend/src/v3/ops/**` (27 files) |

**Exact inventory of each 69-file skill tree** (identical filenames in both trees):
`prisma-cli/` SKILL.md + `references/{db-execute,db-pull,db-push,db-seed,debug,dev,format,generate,init,mcp,
migrate-deploy,migrate-dev,migrate-diff,migrate-reset,migrate-resolve,migrate-status,studio,validate}.md` (19);
`prisma-client-api/` SKILL.md + `references/{client-methods,constructor,filters,model-queries,query-options,
raw-queries,relations,transactions}.md` (9);
`prisma-compute/` SKILL.md + `references/{app-deploy-cli,compute-config,create-prisma,frameworks,sdk-api,
troubleshooting}.md` (7);
`prisma-database-setup/` SKILL.md + `references/{cockroachdb,mongodb,mysql,postgresql,prisma-client-setup,
prisma-postgres,sqlite,sqlserver}.md` (9);
`prisma-driver-adapter-implementation/SKILL.md` (1);
`prisma-mongodb-upgrade/` SKILL.md + `references/{client-api-mapping,decision-stay-or-migrate,
migrations-mapping,schema-contract-mapping,verify-cutover-checklist}.md` (6);
`prisma-postgres-setup/` SKILL.md + `references/{api-basics,auth,endpoints,prisma7-client}.md` (5);
`prisma-postgres/` SKILL.md + `references/{console-and-connections,create-db-cli,management-api-sdk,
management-api}.md` (5);
`prisma-upgrade-v7/` SKILL.md + `references/{accelerate-users,driver-adapters,env-variables,esm-support,
prisma-config,removed-features,schema-changes}.md` (8) → **69**.

*No deletion removes required production functionality; no deletion touches `backend/**`, `frontend/src/v3/**`,
`admin/**`, `supabase/**` or deployment config. Nothing was restored (PO instruction respected).*

## §8 — PHASE 8: SECRET / ARTIFACT SAFETY SCAN

Scan universe: the **124 candidate files** (all existing), plus the excluded single-artifact list. No secret
value is reproduced anywhere in this report.

| Probe | Result |
|---|---|
| `.env` / `.env.*` files in the candidate | **0** (all `.env*` on disk are ignored — `.gitignore:83`) |
| JWT (`eyJ…`) | **0 files** |
| `sk-…` API keys | **0 files** |
| PEM / private keys (`-----BEGIN … PRIVATE KEY`) | **0 files** |
| `BEGIN PGP MESSAGE` / backup ciphertext | **0 files** |
| Credential-bearing DSNs | **2 files, both synthetic/placeholder**: `backend/tests/integration/backup/test_exporter_local.py:37` → `DEFAULT_DSN = "postgresql://postgres:postgres@127.0.0.1:54426/postgres"` (standard local-dev default for the local Supabase DB, not a production credential); `CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md:134` → `postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-<region>.pooler.supabase.com:5432/postgres` (**redacted placeholder**) |
| `SUPABASE_SERVICE_ROLE*` strings | **2 files, names only**: deployment-readiness doc (line 239 — states the service-role credential is `REQUIRED`, server-side only, "must never…"); `qa_harness/core/secrets.py:33` — the env-var **name** in the redaction list (same module also holds a JWT *detection* regex at line 48 — a redactor, not a secret) |
| `service_role_key` strings | **2 files, names only**: prompt-history records describing this very scan |
| `ct_backup` references | 17 files — the ratified D5 **role name** in backup code/docs; **no role-creation SQL file** exists (see §4) |
| Generated archives / dumps / DB state / screenshots / traces / E2E state | **0 in the candidate** (all such trees are C, §3) |
| Machine-local agent state | **0 in the candidate** (`.openhands/**`, `.clinerules/**`, `.claude/.windsurf` symlinks = C) |

**No candidate path contains a secret-like artifact → no file required removal from the candidate for secret
reasons.** The only removals performed were the three generated `qa_harness/findings/*.jsonl` run-data files
(§2.1), removed on the generated-artifact rule, not for secrecy.

## §9 — FINAL MANIFEST

### TABLE 1 — PUBLISH (A: 124 files, all `INCLUDE IN PUBLICATION`)

| Path (group) | Count | Reason | Evidence |
|---|---|---|---|
| `backend/backup/{__init__,artifact,catalog,crypto,errors,exporter,service,settings,storage}.py` | 9 | PO-ratified production backup subsystem | 2,449 lines; D1–D5 ratified; 2 independent verifications |
| `backend/tests/unit/backup/{__init__,test_artifact,test_crypto,test_service,test_storage_and_settings,test_p1_1_remediation}.py` + `backend/tests/integration/backup/{__init__,test_exporter_local}.py` | 8 | Backup tests (AGENTS.md §72) | Present; exercise encryption/exporter/service/settings |
| `backend/requirements.txt` | 1 | Adds `cryptography>=41.0.0` for `backend/backup/crypto.py` | `git diff` +6/−1 with the D3 comment |
| `.gitignore` | 1 | Investor-demo + Playwright artefact ignores | `git diff` +13 |
| `package-lock.json` | 1 | **Realigns the lock to the committed `package.json`** (0 mismatches, §6) | +3,938/−3,742; resolved prisma 6.12.0 / seed 0.89.6 |
| `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_{ARCHITECTURE,IMPLEMENTATION_PHASE1,P1_1_N1_INDEPENDENT_VERIFICATION,PHASE1_1_INDEPENDENT_VERIFICATION}_20260911.md` + `…BACKUP_RESTORE_ROADMAP_V1.0.md` | 5 | Backup architecture/implementation/verification/roadmap | Referenced by the `CT-PROD-BACKUP-*` records |
| `docs/architecture/CARBONTALLY_PRODUCTION_{DEPLOYMENT_READINESS,MIGRATION_SAFETY_PLAN,SUPABASE_RECONCILIATION}_20260911.md` | 3 | Production-readiness documentation | Companion to the tracked pre-commit-gate/readiness-audit docs |
| `docs/legal/{LEGAL_RISK_REGISTER,POLICY_PRODUCT_CONSISTENCY_AUDIT,THIRD_PARTY_PROCESSOR_REGISTER}.md` + `docs/legal/draft/CARBONTALLY_{COOKIE_POLICY,DATA_RETENTION_ARCHIVAL_ANONYMIZATION_POLICY,DPA,MSA,PRIVACY_POLICY,REFUND_POLICY,TERMS_OF_SERVICE}_DRAFT.md` | 10 | Legal/compliance registers + draft policies | Registers carry P0 launch risks; drafts cited by the register |
| `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md` | 1 | PO decision register (governance source of truth) | 17,442 B |
| `AGENTS.md` | 1 | Project operating constitution | Root governance file |
| `playwright.config.ts` | 1 | E2E configuration (`testDir ./tests/e2e`, env-skip contract) | Required by `tests/e2e/**` |
| `docs/cline/prompt-history/` — 18 records + **this staging-prep report** | 19 | Governance audit trail (AGENTS.md §83–§84) | Directory already holds 105 tracked records |
| `qa_harness/{__init__.py,Makefile,pyproject.toml,README.md,requirements.txt}` + `{agents,api,core,db,findings,identities,rules,visual,workflows}/**` (`.py` only) | 64 | QA Harness v1.1/v1.2 code + metadata (AGENTS.md §52) | `pyproject.toml` → `carbontally-qa-harness` v1.1.0; portability audit covers the tree; **3 `.jsonl` run-data files excluded** |
| **TOTAL** | **124** | | 0 already staged; all verified present |

### TABLE 2 — EXCLUDE (C)

| Path / pattern | Reason | Evidence |
|---|---|---|
| `admin/**` (67), `.agents/**` (69), `tools/carbon_data_factory/**` (29), `demodatagen/**` (13), `carbon-tally-ui-demo/**` (1), `shared/**` (1), `.clineignore`, `.vercelignore`, root `requirements.txt` | Line-ending-only churn (no content change) | `git diff --shortstat` non-zero but `git diff -w --shortstat` **empty**; `shared/components/ManualEntryCore.jsx` has 0 referrers |
| `.claude/skills/prisma-*`, `.windsurf/skills/prisma-*` (18 entries) | Machine-local **symlinks pointing outside the repo** (`./../../../carbon_ledger/.agents/skills/…`) | `ls -la` + `readlink` output |
| `.openhands/**` (7), `.clinerules/hooks/**` (13), root `config.toml` | Agent-session/hook state and local MCP client config | Paths/type; `config.toml` = `[mcp] shttp_servers = [{url = "http://localhost:8888/mcp/carbontally-full-ui/"}]` |
| `saas-assurance/**` (217) | PO decision 1: **DO NOT PUBLISH** — separate framework product | `docs/standalone/REPOSITORY_STRATEGY.md` (separate-repo proposal) |
| `agent_swarm/**` (39), `agent_swarm_v2_artifacts/**` (97) | PO decision 2: **DO NOT PUBLISH** | AGENTS.md §57 vs Release-Manifest EXCLUDE; artefacts are run output |
| `tools/seed_investor_demo/*.py` (14) | PO decision 4: **DO NOT PUBLISH AT THIS TIME** (demo/investor features only post-Phase-8) | PO instruction this prompt |
| `output/**` (21), `screenshots/**` (96), `probe_out*.txt` (9), `test_results{,all}.json`, `backend/test_results.json`, `clean_emissions_output.json`, `admin_log_viewer.feature.txt`, `mock_*.csv`, `v1.9.txt` | Generated run output / probes / test results / mock fixtures | Generated-artifact class |
| `qa_harness/evidence/**` (138), `qa_harness/reports/**` (55), `qa_harness/*.egg-info/**` (5), **`qa_harness/findings/{raw,normalized,deduplicated}/*.jsonl` (3)** | Generated QA evidence/reports/run data + build metadata | `store.py` documents the `.jsonl` stages; sample record timestamped 2026-08-31 |
| `e2e/environment/*.json` (4), `e2e/environment/supabase/.temp/**` (2) | Disposable E2E/CLI run state | Untracked runtime files |
| `supabase/config.toml`, `supabase/snippets/Untitled query {303,407,673}.sql` | Local dev port remap; Studio scratch snippets | Ports 54325→54425 etc.; untitled snippet names |
| `v3_schema.sql`, `CarbonTally_DB_Schema_V3M2.sql` | Stale generated schema dumps (53 migrations are authoritative) | Superseded eras |
| `admin-dashboard.zip` (132 MB), any `*.zip` | Binary archive | Size; listed in `.clineignore` |
| `tests/example.spec.ts` | Playwright stock scaffold (`playwright.dev`) | File content; excluded by `testDir` |
| `API_ENDPOINTS.md`, `generate_*.py`, `export_postman.py`, `list_endpoints.py`, `quick_api_ref.py`, `test_endpoints.py`, `clean.js`, `seed.ts`, `create_admin_dashboard.py` | Locally generated doc / dev utilities (EOL-only edits); `create_admin_dashboard.py` scaffolds the deprecated legacy admin | `-w` diffs empty; CL-66 / D-P2-02 |
| `independent_audit/**` (1,840), `.env*`, `.local-demo-credentials.md`, `tools/seed_investor_demo/{DEMO_IDENTITIES.md,demo_manifest.json,.demo_state.json}`, `node_modules/**`, `frontend/node_modules/**`, `backend/.venv/**`, `qa_harness/.venv/**`, `myenv/**`, `.tmp_pgdata/**`, `website_candidate/**`, `local_backups/**`, `**/__pycache__/**`, `.pytest_cache/**` | Local runtime state, secrets, caches, superseded trees | `.gitignore` rules + `.git/info/exclude:9`; all verified ignored/not stageable |

### TABLE 3 — HOLD (PO decisions applied; 7 items)

| Path | Decision | Reason |
|---|---|---|
| `saas-assurance/**` | **DO NOT PUBLISH** (do not delete / modify / stage) | PO decision 1 — separate open-source assurance framework |
| `agent_swarm/**` | **DO NOT PUBLISH** (do not delete / modify / stage) | PO decision 2 — agent/swarm working material |
| `.github/workflows/playwright.yml` | **HOLD — DO NOT STAGE** (do not delete / modify) | PO decision 3 — would activate CI on push/PR, an unauthorised operational decision |
| `tools/seed_investor_demo/*.py` (14) | **DO NOT PUBLISH AT THIS TIME** (do not delete / modify / stage) | PO decision 4 — `/demo` + `/investors` only after Phases 1–8 and the final audit |
| `CARBONTALLY_AUDIT_FINDING_VERIFICATION.md` | **HOLD — NOT STAGED** (evidence not conclusive) | PO decision 5. Evidence: an audit-swarm verification record (2026-08-31, checkpoint `1639121`, *"Read-only… Nothing committed"*, 514 lines) whose evidence source is the **excluded** `independent_audit/reports/evidence/*.json`; it sits at repo root while `docs/audit/` holds 7 similarly-named audit documents; it is cited by name in the tracked `docs/audit/cline/CARBONTALLY_AUDIT_REMEDIATION_REPORT.md` but has no canonical home. Not conclusive → unstaged; **file unmodified** |
| `docs/Robie/getting this on live website.txt` | **HOLD — DO NOT STAGE** (do not delete / modify) | PO decision 6 — production-incident note (login 404 at carbontally.co.uk while the Supabase DB was unavailable, plus a "service unavailable page" requirement) |
| `package-lock.json` | **PACKAGE-LOCK — INCLUDE** (moved into TABLE 1) | PO decision 7 — review concluded: corresponds / consistent / intentional / no production impact / not required for the frontend build; residual `allowScripts` observation in §10 |

## §10 — UNRESOLVED AMBIGUITY / OBSERVATIONS

| # | Observation | Status |
|---|---|---|
| O1 | The reconstruction report's summary line "A-total: 107" under-counts its own component tables; the verified expansion is **125**, refined here to **124** (+`package-lock.json`, −3 `.jsonl`). | **Corrected in this manifest.** No boundary change; recorded for accuracy |
| O2 | `package.json.allowScripts` still names superseded pins (`@snaplet/seed@0.98.0`, `prisma@7.9.1`, `@prisma/engines@{5.14.0-dev.34,7.9.1}`, `esbuild@0.28.1`) while the pins are now `^0.89.6` / `^6.12.0`. Pre-existing (introduced by `daad396`), unrelated to the lock change, and **not correctable here** (`package.json` is out of scope; no file may be modified). | **PO follow-up recommended** (a one-line hygiene change in a future authorised edit). Non-blocking |
| O3 | `CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md` **contains proposed DDL as documentation** (`CREATE ROLE ct_backup LOGIN …`, `ALTER ROLE ct_backup BYPASSRLS`, `ALTER ROLE ct_backup SET default_transaction_read_only = on`) inside a design appendix. It is prose, not an executable `.sql` file, and D5 records that the role was never created. | **No boundary breach**; flagged so no reader mistakes documented design DDL for applied DDL |
| O4 | `docs/Robie/getting this on live website.txt` records a **live production incident** and an unmet requirement ("custom page design if service is not accessible"). Held per PO decision 6, but the underlying production issue should be tracked in the roadmap/backlog. | **PO follow-up recommended** (work item, not publication) |
| O5 | `docs/audit/cline/CARBONTALLY_AUDIT_REMEDIATION_REPORT.md` (tracked) cites `CARBONTALLY_AUDIT_FINDING_VERIFICATION.md`, which remains unstaged → a **dangling reference** in the published tree until the PO resolves that file's canonical status/placement. | **Disclosed for PO decision 5** |
| O6 | The reconstruction's boundary conflicts C1–C10 remain reported (not resolved): notably C1 (backup implemented vs the earlier "PARKED" statement), C2 (legacy `admin/` vs V3 `/ops`), C3 (dual 53-file migration lineages), C10 (roadmap still shows `NEXT GATE: P6-2C`). | **Out of scope here** (documentation/roadmap work) |

Nothing discovered contradicts the PO's decisions; the expected verdict therefore remains option A.

## §11 — EXACT PROPOSED STAGING COMMANDS (NOT EXECUTED)

Rules honoured: **explicit paths only**; no `git add .`, `git add -A`, `git add --all`, `git add -u`; no
global deletion staging; every path below was verified to exist (or, for deletions, verified to be a tracked
deletion). Run from the repository root, in this order.

```bash
# Command 1 — backup implementation + tests + dependency
git add -- backend/backup/__init__.py backend/backup/artifact.py backend/backup/catalog.py \
  backend/backup/crypto.py backend/backup/errors.py backend/backup/exporter.py \
  backend/backup/service.py backend/backup/settings.py backend/backup/storage.py \
  backend/tests/unit/backup/__init__.py backend/tests/unit/backup/test_artifact.py \
  backend/tests/unit/backup/test_crypto.py backend/tests/unit/backup/test_p1_1_remediation.py \
  backend/tests/unit/backup/test_service.py backend/tests/unit/backup/test_storage_and_settings.py \
  backend/tests/integration/backup/__init__.py backend/tests/integration/backup/test_exporter_local.py \
  backend/requirements.txt

# Command 2 — repository policy + root governance/config + lockfile (PO decision 7: INCLUDE)
git add -- .gitignore package-lock.json AGENTS.md playwright.config.ts

# Command 3 — production/backup architecture documentation (8 files)
git add -- docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md \
  docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_IMPLEMENTATION_PHASE1_20260911.md \
  docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_P1_1_N1_INDEPENDENT_VERIFICATION_20260911.md \
  docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_PHASE1_1_INDEPENDENT_VERIFICATION_20260911.md \
  docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_RESTORE_ROADMAP_V1.0.md \
  docs/architecture/CARBONTALLY_PRODUCTION_DEPLOYMENT_READINESS_20260911.md \
  docs/architecture/CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md \
  docs/architecture/CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md

# Command 4 — legal registers + draft policies (10 files)
git add -- docs/legal/CARBONTALLY_LEGAL_RISK_REGISTER.md \
  docs/legal/CARBONTALLY_POLICY_PRODUCT_CONSISTENCY_AUDIT.md \
  docs/legal/CARBONTALLY_THIRD_PARTY_PROCESSOR_REGISTER.md \
  docs/legal/draft/CARBONTALLY_COOKIE_POLICY_DRAFT.md \
  docs/legal/draft/CARBONTALLY_DATA_RETENTION_ARCHIVAL_ANONYMIZATION_POLICY_DRAFT.md \
  docs/legal/draft/CARBONTALLY_DPA_DRAFT.md docs/legal/draft/CARBONTALLY_MSA_DRAFT.md \
  docs/legal/draft/CARBONTALLY_PRIVACY_POLICY_DRAFT.md \
  docs/legal/draft/CARBONTALLY_REFUND_POLICY_DRAFT.md \
  docs/legal/draft/CARBONTALLY_TERMS_OF_SERVICE_DRAFT.md \
  docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md
```

```bash
# Command 5 — governance prompt-history records (19 files, incl. this report)
git add -- docs/cline/prompt-history/CT-PHASE6-COMMIT-20260911-001.md \
  docs/cline/prompt-history/CT-PHASE6-PUSH-AUDIT-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-BACKUP-ARCHITECTURE-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-BACKUP-DECISIONS-20260911-002.md \
  docs/cline/prompt-history/CT-PROD-BACKUP-DR-ROADMAP-DOC-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-BACKUP-IMPLEMENTATION-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-BACKUP-IV-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-IMPLEMENTATION-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-IV-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-N1-IMPLEMENTATION-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-BACKUP-P1.1-N1-IV-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-DEPLOYMENT-READINESS-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-MIGRATION-PREP-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-PUBLICATION-RECON-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-PUBLICATION-STAGING-PREP-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-RELEASE-COMMIT-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-RELEASE-COMMIT-CORRECTION-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-SUPABASE-RECON-20260911-001.md \
  docs/cline/prompt-history/CT-PROD-SUPABASE-RECON-20260911-002.md

# Command 6 — QA Harness v1.1/v1.2 code + metadata (64 files; run-data/evidence/reports EXCLUDED)
git add -- qa_harness/__init__.py qa_harness/Makefile qa_harness/pyproject.toml \
  qa_harness/README.md qa_harness/requirements.txt
git add -- qa_harness/agents/__init__.py qa_harness/agents/api_agent.py qa_harness/agents/base.py \
  qa_harness/agents/judge_agent.py qa_harness/agents/security_agent.py qa_harness/agents/swarm.py \
  qa_harness/agents/ux_agent.py qa_harness/agents/workflow_agent.py
git add -- qa_harness/api/__init__.py qa_harness/api/authorization.py qa_harness/api/contract.py \
  qa_harness/api/inventory.py qa_harness/api/probe.py qa_harness/api/security.py \
  qa_harness/api/session.py qa_harness/api/workflows.py
git add -- qa_harness/core/__init__.py qa_harness/core/config.py qa_harness/core/credentials.py \
  qa_harness/core/evidence.py qa_harness/core/findings.py qa_harness/core/run_context.py \
  qa_harness/core/safety.py qa_harness/core/secrets.py qa_harness/core/status.py
git add -- qa_harness/db/__init__.py qa_harness/db/constraints.py qa_harness/db/discovery.py \
  qa_harness/db/indexes.py qa_harness/db/integrity.py qa_harness/db/migrations.py qa_harness/db/rls.py \
  qa_harness/db/schema_inventory.py
git add -- qa_harness/findings/__init__.py qa_harness/findings/store.py
git add -- qa_harness/identities/__init__.py qa_harness/identities/context.py \
  qa_harness/identities/loader.py qa_harness/identities/resolver.py qa_harness/identities/selectors.py
git add -- qa_harness/rules/__init__.py qa_harness/rules/business.py qa_harness/rules/navigation.py \
  qa_harness/rules/security.py qa_harness/rules/tables.py qa_harness/rules/ux.py
git add -- qa_harness/visual/__init__.py qa_harness/visual/axe/__init__.py qa_harness/visual/axe/runner.py
git add -- qa_harness/workflows/__init__.py qa_harness/workflows/admin.py qa_harness/workflows/base.py \
  qa_harness/workflows/client.py qa_harness/workflows/consultant.py qa_harness/workflows/customer.py \
  qa_harness/workflows/executor.py qa_harness/workflows/messaging.py qa_harness/workflows/operations.py \
  qa_harness/workflows/pe.py
```

```bash
# Command 7 — intentional deletions (152 tracked deletions; tracked-deletion-scoped, NOT directory-wide)

# 7a — the 14 non-skill deletions, enumerated explicitly:
git add -- frontend/src/StaffDashboard.jsx \
  output/json/duplicates.json output/json/import_summary.json output/json/imported_rows.json \
  output/json/mapping_report.json output/json/skipped_rows.json output/json/validation_report.json \
  output/json/workbook_analysis.json output/json/worksheet_analysis.json \
  output/reports/mapping_report.md output/reports/validation_report.md \
  output/reports/workbook_analysis.md output/reports/worksheet_analysis.md \
  output/sql/import_defra_2025.sql

# 7b — the 138 skill-tree deletions. A directory-wide `git add -- .claude/skills` would ALSO sweep the
# machine-local symlinks (excluded as C), so the deletion set is expanded from the index instead, scoped to
# exactly the two trees and limited to tracked deletions:
git add -- $(git ls-files -d -- .claude/skills .windsurf/skills)
```

### Exact effect of the commands

| Command | Files affected |
|---|---|
| 1 | 17 new files (`backend/backup/**`, `backend/tests/{unit,integration}/backup/**`) + 1 modification (`backend/requirements.txt`) |
| 2 | 1 modification (`.gitignore`), 1 modification (`package-lock.json`), 2 new (`AGENTS.md`, `playwright.config.ts`) |
| 3 | 8 new `docs/architecture/*.md` |
| 4 | 10 new `docs/legal/**` + 1 new `docs/ChatGPT/**` |
| 5 | 19 new `docs/cline/prompt-history/*.md` |
| 6 | 64 new `qa_harness/**` files (all `.py` plus `Makefile`, `README.md`, `pyproject.toml`, `requirements.txt`) |
| 7 | **152 recorded deletions** (138 skill-tree + 13 `output/**` + 1 `frontend/src/StaffDashboard.jsx`) |
| **Net** | **124 additions/modifications + 152 deletions** → the "complete accumulated CarbonTally development state" candidate |

## §12 — PRE-STAGING RISKS

| # | Risk | Mitigation contained in this manifest |
|---|---|---|
| R1 | A broad command (`git add -A`/`.`) would sweep 178 EOL-only files and ~700 excluded paths | Commands use explicit paths only; forbidden forms listed in §11 |
| R2 | A directory-wide add of `.claude/skills` / `.windsurf/skills` would also stage the 18 machine-local symlinks | Command 7b is scoped to `git ls-files -d` (tracked deletions only) |
| R3 | Staging `package-lock.json` may raise a reviewer question (no `package.json` diff) | Explained in §6: the lock realigns to the *already-committed* `package.json`; 0 mismatches |
| R4 | A push after the commit could trigger a production deploy (root `vercel.json`) — **push is not authorised** | Out of scope; the PO sequence keeps commit, verification, push and deploy as separate authorisations |
| R5 | Publishing migration **files** could be confused with **applying** them | §5 states the distinction explicitly and repeatedly |
| R6 | `allowScripts` staleness (O2) could be mistaken for a lock/JSON inconsistency | Documented as pre-existing and unrelated; follow-up recommended |
| R7 | Dangling citation of the held file (O5) | Disclosed; PO decision 5 remains open, nothing staged |
| R8 | Working-tree preservation during a future staging | Staging touches only the index; no file content is changed by the commands |

## §13 — PHASE 10: STAGED STATE (verified empty)

```text
git diff --cached --name-status   →  (no output — 0 staged files)
```

* Staged files: **0** — nothing was staged by this operation, and nothing was accidentally staged.
* `HEAD` still `c864d729526ef2c5e40cd19fdc451e8f0975144b`; `origin/main` still
  `6148c86826e25e1889d8cf86bb02dbb2901577c6`; ahead 30 / behind 0; reflog top still
  `c864d72 commit: feat: close CarbonTally Phase 6 consultant workflow`.
* Working tree counts unchanged: 210 modified tracked, 152 deleted tracked, 853 untracked
  (**+1** versus the reconstruction = this report only).
* No incident: no unstaging was necessary.

## §14 — FINAL VERDICT

**STAGING MANIFEST COMPLETE — READY FOR PO STAGING AUTHORIZATION**

* The A allowlist is exact and verified: **124 files**, all present, none generated, none secret, none
  already staged.
* All seven PO B-item decisions are applied and each item is verifiably **untouched** (no delete, no modify,
  no stage).
* The intentional deletion set (**152**) is verified, its replacements confirmed present, and nothing was
  restored.
* `PACKAGE-LOCK — INCLUDE`, backed by a completed focused review.
* Migrations are untouched: publication ≠ application, stated explicitly.
* Two non-blocking follow-ups (O2 `allowScripts`; O4 `docs/Robie` production issue; plus the open O5 file
  decision) are disclosed but do not alter the boundary.

### ATTESTATION

* **files created:** ONLY the required staging-preparation history report
  (`docs/cline/prompt-history/CT-PROD-PUBLICATION-STAGING-PREP-20260911-001.md`)
* **files modified:** ONLY the required staging-preparation history report
* **files deleted:** NO
* **files staged:** NO (`git diff --cached --name-status` → empty)
* **commit created:** NO
* **push performed:** NO
* **deployment performed:** NO
* **production Supabase contacted:** NO
* **production Supabase modified:** NO
* **migrations applied:** NO
* **production backup executed:** NO
* **restore executed:** NO
* **application source modified:** NO
* **migration files modified:** NO

**STOPPED after writing and verifying this report.** No staging, no commit, no push, no deploy, no production
change, no unrelated-file clean-up, no restoration of excluded deletions. The next operation is separately
authorised by the Product Owner after reviewing this exact staging manifest.
