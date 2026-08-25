# CarbonTally V3 — Git Repository Audit & Release Readiness Report

**Task type:** READ-ONLY AUDIT + RELEASE READINESS ANALYSIS.
**Constraint:** No application source, schema, RLS, API, migration, route, `.gitignore`, or deployment file was modified. No commit, stage, push, branch operation, history rewrite, or destructive command was executed. `git fetch origin` was performed (permitted — updates remote-tracking refs only). The only repository addition is this report.
**Date:** 2026-08-24

---

## 1. Executive Summary

**The repository is currently synchronized at HEAD, but the entire post-15-August development release exists only in the working tree and has never been committed or pushed.**

The definitive findings:

1. **On GitHub now:** commit `878bd0f` ("Remove exposed API key file"), pushed **2026-08-24 08:17:00 UTC**.
2. **Previous successful push (provable):** `a909cbe` ("checkpoint: CarbonTally V3 Render-ready backend"), pushed **2026-08-15 12:20:33 UTC** — evidenced by `.git/logs/refs/remotes/origin/main`. The remote stayed at `a909cbe` from 15-Aug until today's push.
3. **Local vs remote:** identical. `main` = `origin/main` = `878bd0f`; merge-base is `878bd0f`; `0 ahead / 0 behind`. No local-only commits, no remote-only commits.
4. **The D20–D37 release is uncommitted.** The working tree contains the entire V3-commercial implementation (D20–D37): the V3 backend modules, the D20–D37 database migrations, the V3 frontend, tests, and the D27–D37 documentation — **582 modified, 151 deleted, 184 untracked files**. None of it has ever been committed; none of it is on GitHub.
5. **The release is atomic and currently entangled with working-tree noise:** the tracked entry points (`backend/api/router.py`, `backend/main.py`, `frontend/src/App.js`) import the untracked V3 modules. Committing only the tracked files would create an application that cannot import/start. ~534 of the 582 "modified" files differ from HEAD **only by line endings (CRLF vs LF)** and must not be committed as-is.
6. **Secret in history (confirmed):** `tools/carbon_data_factory/deeepseek_api.txt` (an LLM-provider API key) was **added in `2d23fb8` (2026-08-06, pushed the same day) and removed in `878bd0f` (2026-08-24, pushed)**. The credential therefore **still exists in the pushed GitHub history** at `2d23fb8`. Git history remediation is required as a separate, authorized task. No other embedded credentials were found in tracked files at HEAD; one untracked scratch file (`probe_out5.txt`) contains a JWT and must never be committed.
7. **Release readiness decision: DO NOT PUSH YET.** The working tree is mixed (real D37 code + EOL noise + generated artifacts + agent-tooling churn + sensitive scratch files). A structured, authorized commit sequence (with line-ending normalization and strict include/exclude lists) is required before the next push.

---

## 2. Repository Identity

| Attribute | Value |
|---|---|
| Top-level path | `/home/shomonrobie/carbon_tally` |
| Git version repo | `git rev-parse --show-toplevel` → `/home/shomonrobie/carbon_tally` |
| Total commits on `main` | **70** |
| Local refs | `refs/heads/main` |
| Cline checkpoint refs | **146** under `refs/cline/checkpoints/*` (local tooling; not on remote) |
| Tags | `rc2-final` → `2d23fb8`; `v2.1-phase4` → `be405d8`; `v2.1.1-phase3` → `ae1d685` (all ancestors of HEAD) |
| Working tree file count (tracked) | 1,326 files |

**Repository is a single-branch (`main`) single-remote repository.** No other local or remote branches exist. All three tags point to commits reachable from `origin/main`.

---

## 3. Remote Configuration

| Attribute | Value |
|---|---|
| Remote name | `origin` |
| Fetch URL | `https://github.com/shomonrobie/CarbonTally.git` |
| Push URL | `https://github.com/shomonrobie/CarbonTally.git` |
| Tracking | `main` → `origin/main` |
| Remote HEAD | `refs/remotes/origin/HEAD → origin/main` |

Only one remote. HTTPS (no SSH). No other remotes configured.

---

## 4. Current Branch State

- Branch: `main` (only local branch).
- `git branch -vv`: `* main 878bd0f [origin/main] Remove exposed API key file`.
- `git status`: *"Your branch is up to date with 'origin/main'."*
- `git rev-parse HEAD` = `878bd0f9eb5d277510b9b911ecd1a10be0213bd1`.
- `git rev-parse origin/main` (after fetch) = `878bd0f9eb5d277510b9b911ecd1a10be0213bd1`.

**Conclusion:** HEAD and origin/main point to the same commit.

---

## 5. Local vs Remote Reconciliation

| Check | Result |
|---|---|
| `git merge-base main origin/main` | `878bd0f9eb5d277510b9b911ecd1a10be0213bd1` (both tips are the same commit) |
| `git rev-list --left-right --count origin/main...main` | `0  0` (zero ahead, zero behind) |
| Local-only commits (`origin/main..main`) | none |
| Remote-only commits (`main..origin/main`) | none |
| Staged changes | none (`0` added) |
| Working-tree modifications | **582** (see §11) |
| Working-tree deletions | **151** (see §12) |
| Untracked files | **184** (see §10) |

**At the commit level the repository is fully synchronized.** All divergence is in the **working tree** (uncommitted changes), not in commit history.

---

## 6. Evidence of Previous Pushes

**The exact previous push date CAN be established from the remote-tracking reflog.**

`.git/logs/refs/remotes/origin/main` records every `update by push` event with an epoch timestamp. Conversions (UTC):

| Pushed commit | Subject | Push timestamp (UTC) |
|---|---|---|
| `2d23fb8` | CarbonTally RC2 Final database baseline | 2026-08-06 14:11:20 |
| `97e0f69` | Phase 0-2: Architecture Foundation | 2026-08-07 17:39:01 |
| `a57c224` | Phase 3: Infrastructure Layer | 2026-08-07 18:47:06 |
| `a13fd10` | Phase 4: Factor Matching Engine | 2026-08-07 19:42:10 |
| `0a5a603` | Phase 5: Emissions Calculation Engine | 2026-08-07 20:38:56 |
| `c5eadec` | Phase 7: Document Processing & AI Extraction | 2026-08-08 01:07:27 |
| `e57543d` | Phase 8: Workflow Orchestrator | 2026-08-08 08:34:17 |
| `8bcd490` | Fix integration test database isolation | 2026-08-08 10:49:40 |
| `dbe72aa` | checkpoint: verified V2.1 and V3 database foundation | 2026-08-14 11:58:42 |
| `cfabe26` | checkpoint: CarbonTally V3 baseline | 2026-08-15 08:53:49 |
| `a909cbe` | checkpoint: CarbonTally V3 Render-ready backend | **2026-08-15 12:20:33** |
| `878bd0f` | Remove exposed API key file | 2026-08-24 08:17:00 |

**Previous successful push:** `a909cbe` was pushed on **2026-08-15 12:20:33 UTC**. origin/main then remained at `a909cbe` until `878bd0f` was pushed on 2026-08-24.

Therefore **every commit and every file created or changed after 2026-08-15 12:20:33 UTC has never been pushed.** That includes the entire D20–D37 release now sitting uncommitted in the working tree. The recent `git push --set-upstream origin main` that advanced the remote `a909cbe → 878bd0f` only pushed that single new commit; it did not push any of the working-tree work (none of it is committed).

The local `HEAD` reflog confirms commits were made on 15-Aug (checkpoint commits) and 24-Aug (API-key removal), with nothing in between — i.e., no intermediate commits were created for the D20–D37 work; it was developed entirely as uncommitted working-tree changes.

---

## 7. Reconstructed Development History

The chronology below is reconstructed **from Git evidence only** (commit messages, commit dates, changed-file statistics, migration chronology, and the pushed file inventory). Where a named CarbonTally phase appears in commit messages or repository documentation, the association is explicit; otherwise a descriptive workstream name is used. No remembered D-number sequence was assumed as input.

### 7.1 Commit-level periodization (main history, oldest → newest)

| Period / Identified Work | Approx. dates | Commit range | Evidence | Remote status | Confidence |
|---|---|---|---|---|---|
| Early app + admin dashboard + beta signup/login + Supabase client fixes | 2026-07-21 → 07-24 | ~`8b59378` … `a34b2f0` | Commit subjects ("fix: admin dashboard.", "fix: beta signup/login N.", "fix: supabase client.", "Add Google OAuth…", "Feature complete: CarbonTally v3.0…") | Pushed (present on origin/main) | High |
| Staff dashboard / review assignment / beta management | 2026-07-23 → 07-27 | `987500a` … `9c68ab1` | Commit subjects; "Major update: Manual Entry, Staff Review Queue, Admin Assignment, Document Status, and Log Viewer" | Pushed | High |
| RC1/RC2 database baselines; sidebar/Realtime fixes; "stop tracking SQL backups" | 2026-08-04 → 08-06 | `eca5156` … `2d23fb8` | `rc1 database full`, `rc2 database full`, `CarbonTally RC2 Final database baseline`; tag `rc2-final` at `2d23fb8`; **the exposed API key was committed here** | Pushed (tag pushed) | High |
| V3 backend Phase 0–8 build (foundation → infra → factor matching → emissions calc → document/AI extraction → workflow orchestrator) | 2026-08-07 → 08-08 | `97e0f69` … `8bcd490` | Phase-named commit subjects; matches working-tree docs `CARBONTALLY_V3_PHASE_4…8_REPORT.md`; all pushes same/next day | Pushed | High |
| V3 database foundation + V3 API core (admin/aliases/audit/imports/providers, contracts, dependencies, router, middleware; domain/engines benchmarking/report_generation/validation) | 2026-08-14 | `dbe72aa` | `checkpoint: verified V2.1 and V3 database foundation`; push log 08-14 | Pushed | High |
| V3 baseline (schema snapshot, admin_entities, customer_factors, issues, processing_entities; data/domain/engines; tests) | 2026-08-15 | `cfabe26` | `checkpoint: CarbonTally V3 baseline`; push log 08-15 | Pushed | High |
| V3 Render-ready backend (verify_startup, auth/routes fixes, Render docs) | 2026-08-15 | `a909cbe` | `checkpoint: CarbonTally V3 Render-ready backend`; **last push before today** | Pushed (08-15 12:20 UTC) | High |
| **D20–D37 V3-commercial release: consultants, white-label, processing assignment, lifecycle, private storage, evidence traceability, self-service onboarding, billing security + configurable subscription, commercial billing master — plus V3 backend modules, V3 frontend, tests, and the D27–D37 documentation** | 2026-08-15 → 08-24 | **NO COMMITS — working tree only** | Untracked files (`backend/api/v3_*.py`, `backend/data/billing.py`, `backend/services/billing.py`, `frontend/src/v3/`, `supabase/migrations/20260821*`–`20260824*`, `docs/audit/cline/CARBONTALLY_V3_D27…D37_*.md`) + modified tracked entry points (`router.py`, `main.py`, `App.js`) | **NOT on remote; never committed** | High |
| Remove exposed API key file | 2026-08-24 | `878bd0f` | Commit subject; 1-file deletion | Pushed (08-24) | High |
### 7.2 Note on Cline checkpoint refs (146 local refs)

`refs/cline/checkpoints/*` (146 refs) are **local tooling snapshots** created by the Cline extension across development sessions. They are **not on the remote**. Two of them (`5f4c361`, `4ce9368`, subjects "untracked files on cline checkpoint") matched the exposed key path under rename-tracking search, but **neither is an ancestor of HEAD**; they are reachable only from checkpoint refs. These refs keep local objects (including possibly the key blob) alive in the local object database and are candidates for local pruning in a future cleanup task (they do not affect the remote).

---

## 8. Development History Confidence Assessment

| Assertion | Confidence | Basis |
|---|---|---|
| Last push before today = `a909cbe` on 2026-08-15 12:20:33 UTC | **Proven** | `.git/logs/refs/remotes/origin/main` (push-log with epoch timestamps) |
| Local/remote synchronized at `878bd0f` | **Proven** | rev-list 0/0; merge-base = HEAD |
| D20–D37 work exists only in the working tree | **Proven** | D37 files (`v3_billing.py`, `v3_commercial.py`, `data/billing.py`, `domain/billing.py`, `services/billing.py`) are untracked; D20–D37 migrations are untracked; `git status` shows 184 untracked + 582 modified + 151 deleted |
| Release is atomic (tracked entry points import untracked modules) | **Proven** | `router.py` imports 22 `api.v3_*` modules (all untracked); `main.py` imports `api.router`; `App.js` imports `./v3/*` and `PricingPage`/`SelfServiceSignup`/`OnboardingPage` (all untracked) |
| Exposed key committed at `2d23fb8` (2026-08-06), removed at `878bd0f` (2026-08-24) | **Proven** | `git show` both commits; blob is 35 bytes beginning with the `sk-` provider-key prefix |
| Exposed key still present in pushed history | **Proven** | `2d23fb8` is an ancestor of `origin/main` and was pushed on 08-06 (push log) |
| EOL-only working-tree modifications (~534 files) | **Proven** | `git diff --ignore-space-at-eol` reduces the 582 modified files to 48 real-content-changed files (46 project + 2 agent-skill) |
| Phase naming for commits | **Supported by commit subjects + working-tree phase reports** | Phase 0–8 commit subjects and `CARBONTALLY_V3_PHASE_4…8_REPORT.md` docs |
| Earlier (pre-14-Aug) history attribution detail | Medium (older commits have terse subjects) | Commit subjects only; full file-level reconstruction not required for release boundary |

---

## 9. Current Working Tree State

`git status --short` summary:

| Category | Count | Notes |
|---|---|---|
| Modified | **582** | ~46 real-content project changes, ~69 agent-skill file updates, ~467 EOL-only (CRLF↔LF) |
| Deleted | **151** | 138 tracked `.claude/skills/*` + `.windsurf/skills/*` (replaced by symlinks to an external dir), 13 `output/` generated artifacts |
| Untracked | **184** | V3 backend (96 files), V3 frontend (45 files), D20–D37 migrations (10), screenshots (~60), docs (~30), generated artifacts, agent-skill symlinks (18) |
| Staged | 0 | nothing staged |
| Diff magnitude | 733 files, 275,850 insertions, 801,925 deletions | dominated by deletion of generated artifacts (`output/json/validation_report.json` −203 K lines, `imported_rows.json` −189 K, `output/sql/import_defra_2025.sql` −105 K) and EOL-only rewrites |

**The working tree is a mixture of four distinct states** (see the four-state model in §Final Questions): (A) HEAD content, (B) no local commits beyond HEAD, (C) a large legitimate release delta (D20–D37) *plus* environment/agent noise, (D) a few ambiguous items. They must be separated before any commit.

### 9.1 Line-ending condition

`backend/routes/communication.py` and many other files exist as CRLF in the working tree but LF in HEAD (`git diff --ignore-space-at-eol` shows no content change for them). Files such as `backend/main.py` and `backend/config.py` have **both** real content changes and CRLF. **Committing the working tree verbatim would inject CRLF into ~500 files** and corrupt the diff history. Line-ending normalization is a mandatory part of the future commit task (via `.gitattributes` and/or a one-time normalization commit) — not something done during this audit.

---

## 10. Untracked File Inventory

Grouped inventory of all 184 untracked files (none staged, none ignored):

| Group | Count | Examples | Classification |
|---|---|---|---|
| V3 backend API modules | 24 | `backend/api/v3_billing.py`, `v3_commercial.py`, `v3_documents.py`, `v3_emissions.py`, `v3_processing_workflow.py`, `operations_auth.py`, `consultant_auth.py` … | **KEEP — CURRENT PRODUCTION SOURCE** (imported by `router.py`) |
| V3 backend data layer | 20 | `backend/data/billing.py`, `consultants.py`, `discovery.py`, `reporting.py`, `tenant.py` … | **KEEP — CURRENT PRODUCTION SOURCE** |
| V3 backend domain layer | 9 | `backend/domain/billing.py`, `branding.py`, `evidence.py`, `operations.py` … | **KEEP — CURRENT PRODUCTION SOURCE** |
| V3 backend engines/services | 5 | `backend/engines/pdf_render.py`, `processing_workflow.py`, `backend/services/billing.py`, `storage.py`, `v3_email.py` | **KEEP — CURRENT PRODUCTION SOURCE** |
| V3 backend tests | 26 | `backend/tests/unit/api/test_billing_core.py`, `test_commercial_settings.py`, `integration/test_customer_admin.py` … | **KEEP — CURRENT TEST** |
| V3 frontend | 45 | `frontend/src/v3/` (customer/ops/admin/consultant/reports/components), `PricingPage.jsx`, `SelfServiceSignup.jsx`, `OnboardingPage.jsx`, `css/lp2.css`, `css/pricing_page.css` | **KEEP — CURRENT PRODUCTION SOURCE** (imported by `App.js`) |
| Migrations (untracked) | 10 | `supabase/migrations/20260821*` (d20, d21, d22), `20260822*` (p9, d27), `20260823*` (d32, d33), `20260824*` (d35, d37-0, d37-master) + `database/rc2/00000000000000_init_schema.sql` | **KEEP — CURRENT MIGRATION** |
| Documentation | ~30 | `docs/audit/cline/CARBONTALLY_V3_D27…D37_*.md`, `docs/architecture/CARBONTALLY_V3_*`, `docs/Pricing/*`, `docs/RECONSTRUCTED_TASK_HISTORY.md` | **KEEP — CANONICAL DOCUMENTATION / HISTORICAL RECORD** |
| Screenshots | ~60 | `screenshots/d27_evidence/…`, `d30_reporting/…`, `d31_reporting/…`, `d33_evidence/…`, `d34_customer_journey/…`, `d35_customer_onboarding/…` | **ARCHIVE/IGNORE** (verification evidence; consider `screenshots/` in `.gitignore`) |
| Agent-skill symlinks | 18 | `.claude/skills/prisma-*`, `.windsurf/skills/prisma-*` (symlinks → `~/carbon_ledger/.agents/skills/*`) | **REVIEW** — never commit (broken for other clones; external target) |
| Generated/scratch | ~18 | `admin-dashboard.zip`, `backend/test_results.json`, `probe_out*.txt` (9), `v3_schema.sql`, `output/json/emission_factors.json`, `output/seai_2025/`, `supabase/snippets/Untitled query 673.sql` | **IGNORE / DELETE (after PO approval)** — see §18 |

---

## 11. Modified File Inventory

Of the 582 modified files:

- **~46 project files with real content changes** (EOL-insensitive diff). These are the legitimate D20–D37 release changes to tracked files:
  - Backend: `api/contracts.py`, `api/dependencies.py`, `api/issues.py`, `api/router.py`, `auth.py`, `config.py`, `data/__init__.py`, `data/emission_factors.py`, `data/emissions_logs.py`, `data/issues.py`, `data/organizations.py`, `data/reports.py`, `domain/calculation.py`, `domain/issue.py`, `domain/organization.py`, `engines/calculation.py`, `engines/report_generation.py`, `main.py`, `requirements.txt`, `routes/organizations/members.py`
  - Tests: `integration/conftest.py`, `integration/test_reports.py`, `integration/test_v3_rls_behavior.py`, `unit/api/fakes.py`, `unit/api/test_foundation.py`, `unit/api/test_v3_issues.py`
  - Frontend: `src/App.js` (+171/−2 — the V3 wiring), `src/AuthCallback.js`, `src/BetaSignup.jsx`, `src/LandingPage.jsx`, `src/Login.js`, `src/MagicLink.jsx`, `src/components/AppFooter.jsx`, `src/components/AppHeader.jsx`, `src/css/LandingPage.css`, `src/supabaseClient.js`
  - Config/docs: `.gitignore`, `supabase/config.toml`, `requirements.txt` (root), `CarbonTally_DB_Schema_V3M2.sql`, a handful of `docs/*`
  - Oddity: `frontend/App_.js` (42 KB, tracked, modified, **not imported anywhere**) — a stray duplicate to REVIEW (likely an accidental copy of `App.js`).
- **~69 `.agents/skills/*` files** — agent-tooling content updates (skill system sync), not project work.
- **~467 files** — EOL-only (CRLF) differences; no content change. Must be excluded from the release commit or normalized.

**Assessment:** the real-content modified files are **legitimate current development** (D20–D37 wiring), with the exception of `.gitignore`/`supabase/config.toml` (environment/ignore adjustments — decide whether to include in the release commit or a separate config commit), the stray `frontend/App_.js`, and the agent-skill files.

---

## 12. Deleted File Inventory

All 151 deletions are unstaged working-tree deletions:

| Group | Count | Classification |
|---|---|---|
| `.claude/skills/*` tracked files (69) | Deleted; replaced by symlinks → `~/carbon_ledger/.agents/skills/*` | **Environment/tooling churn — REVIEW.** The tracked regular files were superseded by an external-symlink arrangement. Committing these deletions removes agent tooling from the repo; probably desirable, but it is an environment artifact, not project work — PO decision (§32). |
| `.windsurf/skills/*` tracked files (69) | Same pattern | Same |
| `output/json/*.json`, `output/reports/*.md`, `output/sql/import_defra_2025.sql` (13) | Generated import/validation artifacts removed from the working tree | **IGNORE/DELETE — generated output** that should not be tracked at all (they remain in HEAD history; recommend a future commit removing them + gitignore) |

No application-source deletions were found among the deleted set (all deletions are tooling or generated artifacts). The `tools/carbon_data_factory/deeepseek_api.txt` deletion is already a committed change (`878bd0f`), not a working-tree deletion.

---

## 13. Current Source Verification (D37 — without assuming it is the "starting point")

The D37 implementation expected in the repository **exists in the working tree, is substantial, and is entirely uncommitted**:

| File | Lines | Status |
|---|---|---|
| `backend/api/v3_billing.py` | 300 | **UNTRACKED** (working tree only) |
| `backend/api/v3_commercial.py` | 822 | **UNTRACKED** (working tree only) |
| `backend/data/billing.py` | 914 | **UNTRACKED** (working tree only) |
| `backend/domain/billing.py` | 288 | **UNTRACKED** (working tree only) |
| `backend/services/billing.py` | 832 | **UNTRACKED** (working tree only) |
| `backend/api/v3_processing_workflow.py` | — | **UNTRACKED** (working tree only) |
| `supabase/migrations/20260824020000_d37_0_…sql` | — | **UNTRACKED** |
| `supabase/migrations/20260824030000_d37_master_…sql` | — | **UNTRACKED** |
| `docs/audit/cline/CARBONTALLY_V3_D37_0_…REPORT.md`, `…D37_MASTER_…REPORT.md` | — | **UNTRACKED** |
| `frontend/src/v3/customer/BillingPage.jsx`, `frontend/src/v3/ops/CommercialTab.jsx` | — | **UNTRACKED** |

- No duplicate/older D37 implementations exist in the commits — **no D37 implementation exists in any commit at all**.
- The billing slice is wired into the tracked `router.py` (`from api.v3_billing import …`, `from api.v3_commercial import …`) and into `domain.billing`/`services.billing`/`data.billing` imports inside those modules.
- Completeness is corroborated by the working-tree D37 reports and the file line counts above; **final runtime verification belongs to the commit/QA task** (this audit performs no builds/tests).

**Conclusion:** D37 is complete in the working tree and absent from Git. The next commit sequence must include it.

---

## 14. Migration Audit

Tracked migrations (on origin/main): the full `supabase/migrations/` series through `20260810050000_v3m6_entity_rls.sql` (rc2 baseline → v3m6), plus the older `database/rc2/00000000000000_init_schema.sql` (tracked).

**Untracked (working tree only, never committed):**
- `supabase/migrations/20260821000000_d20_d15_active_consultant_grant.sql`
- `supabase/migrations/20260821010000_d21_white_label_branding.sql`
- `supabase/migrations/20260821020000_d22_processing_work_assignment.sql`
- `supabase/migrations/20260822000000_p9_rls_recursion_fix.sql`
- `supabase/migrations/20260822010000_d27_d19_customer_lifecycle.sql`
- `supabase/migrations/20260823000000_d32_private_documents_storage.sql`
- `supabase/migrations/20260823010000_d33_evidence_traceability.sql`
- `supabase/migrations/20260824010000_d35_self_service_onboarding.sql`
- `supabase/migrations/20260824020000_d37_0_billing_security_and_configurable_subscription.sql`
- `supabase/migrations/20260824030000_d37_master_commercial_billing.sql`
- `database/rc2/00000000000000_init_schema.sql` (untracked duplicate baseline — REVIEW: possibly a copy of the tracked init; do not commit a second baseline without PO review)
- `supabase/snippets/Untitled query 673.sql` (scratch — IGNORE)

**Findings:** All D20–D37 schema history is uncommitted. The migration chronology is coherent (`20260821` → `20260824`), additive, and matches the documented D-series. No duplicate/conflicting migration numbering was found. Migrations represent schema history and must be committed together with the D37 release; they must not be deleted or reordered. The untracked `database/rc2/…init_schema.sql` should be checked for identity with the tracked `supabase/migrations/00000000000000_init_schema.sql` before any commit (avoid two baselines).

---

## 15. Test Audit

- **Canonical tests (committed):** `backend/tests/integration/` (rc2/v3 suite incl. `test_v3_rls_behavior.py` — this file also has real working-tree changes) and `backend/tests/unit/` (api/domain/engines/infra). These are committed on origin/main.
- **Canonical tests (untracked, part of the release):** the D20–D37 test additions — `backend/tests/unit/api/test_billing_core.py`, `test_commercial_settings.py`, `test_d19_lifecycle.py`, `test_operations_auth.py`, `test_self_service_onboarding.py`, `test_storage_security.py`, `test_evidence_*.py`, `test_scope_aware_authorization.py`, `test_v3_consultants.py`, `test_v3_customer_admin.py`, `route_paths.py`, `integration/test_consultants.py`, `integration/test_customer_admin.py`, `integration/test_report_versions.py`, `unit/domain/test_d19_domain.py`, `unit/engines/test_pdf_render.py`, etc. → **KEEP — CURRENT TEST**, commit with the release.
- **Fixtures/helpers:** `tests/unit/api/fakes.py`, `conftest.py` (modified, part of release).
- **Legacy/one-off scripts inside `tests/`:** `create_test_users.py`, `setup_test_data.py`, `setup_test_orgs.py`, `test_api.py`, `test_api_simple.py`, `test_auth_simple.py`, `test_failing_endpoints.py`, `test_all_endpoints.py`, `verify_setup.py`, `fix_imports.py`, `check_imports.py`, `export_postman.py`, `audit_code.py` — tracked, legacy. **ARCHIVE/MOVE** (future cleanup; do not delete now).
- **Generated test outputs:** `backend/test_results.json` (untracked), `test_results.json`/`test_results_all.json` (root, tracked+modified) — **IGNORE** (add to `.gitignore` in the future).
- **Live smoke scripts** (`/tmp/d37_live_smoke.py`, `/tmp/d370_live_smoke.py`): outside the repo — safe; consider promoting a checked-in version later (P3).

---

## 16. Documentation Audit

- **CANONICAL CURRENT:** the D27–D37 reports in `docs/audit/cline/` (all untracked) and the architecture docs in `docs/architecture/` (mixed tracked/untracked) that describe the current product. Commit with the release.
- **HISTORICAL RECORD:** `docs/cline/*`, `docs/Final/*`, `docs/Final_Kimi/*`, `docs/architecture/DB_Migration/*`, `docs/architecture/UI/*` — historical analysis/design documents. Keep (archive later, do not delete).
- **DUPLICATE/SCATTERED:** `CarbonTally_DB_Schema_V3M2.sql` and `v3_schema.sql` (root) and `docs/cline/CarbonTally_DB_Schema_V3M2.md` — multiple schema snapshots; migrations remain the single source of truth. **CONSOLIDATE** (future).
- **SUPERSEDED/TEMPORARY:** `v1.9.txt`, `API_ENDPOINTS.md` (root), `featurelist.txt`, `admin_log_viewer.feature.txt`, `docs/Final_Kimi/user_pasted_clipboard_*.txt`, `docs/architecture/chatGptPrompts.txt`, `docs/Todos.md` — **ARCHIVE** (future).
- The public-website audit report (`docs/audit/cline/CARBONTALLY_V3_PUBLIC_WEBSITE_AND_ARCHITECTURE_AUDIT.md`) is untracked — commit it with the documentation set.

---

## 17. Script Audit

- **Maintenance/dev tooling (keep):** `tools/` (benchmark_runner, carbon_data_factory, documentation_generator, load_tester, migration_generator, schema_auditor), `demodatagen/`, `verify_startup.py`, `create_admin_dashboard.py`.
- **One-off/legacy scripts at root (ARCHIVE/MOVE later):** `clean.js`, `generate_messy_fuel_csv.py`, `generate_messy_utility_csv.py`, `list_endpoints.py`, `quick_api_ref.py`, `export_postman.py`, `test_endpoints.py` (some are tracked and have working-tree changes; all are dev helpers, not production).
- **Build/deploy config:** `vercel.json` (tracked, modified), `runtime.txt`, root `package.json`, `frontend/package.json`, `backend/requirements*.txt`. Root `requirements.txt` currently uses invalid `=>` syntax (stale — REVIEW; the backend one is authoritative).
- No deployment scripts contain embedded credentials (checked — env-var reads only).

---

## 18. Generated / Temporary Artifact Audit

| Path | State | Classification |
|---|---|---|
| `admin-dashboard.zip` (127 MB) | untracked | **IGNORE / DELETE (PO)** — binary archive, not for Git |
| `probe_out1…9.txt` | untracked | **IGNORE / DELETE** — `probe_out5.txt` contains a JWT; never commit |
| `output/` (json/reports/sql incl. `seai_2025/`) | tracked(13 del) + untracked(7) | **IGNORE / DELETE from tracking** — generated import/validation output |
| `v3_schema.sql`, `CarbonTally_DB_Schema_V3M2.sql` | untracked/tracked-mod | **CONSOLIDATE** — schema snapshots (migrations are source of truth) |
| `backend/test_results.json`, `test_results.json`, `test_results_all.json` | untracked / tracked-mod | **IGNORE** |
| `screenshots/` (~60 untracked PNG/PDF) | untracked | **ARCHIVE or IGNORE** — verification evidence; consider `.gitignore` |
| `backups/`, `local_backups/`, `uploads/`, `.tmp_pgdata/` | ignored/untracked | local-only — keep ignored |
| `clean_emissions_output.json` | tracked-mod | generated — IGNORE |
| mock CSVs (`mock_*.csv`) | tracked-mod | fixtures — MOVE to tests/fixtures later |

---

## 19. Duplicate / Backup File Audit

| Path | State | Assessment |
|---|---|---|
| `backend/main copy.py`, `backend/main copy 2.py` | tracked | Dead copies (contain debug prints referencing secret env vars); **ARCHIVE/REMOVE later** |
| `backend/main_v2.py` | tracked | Legacy entry variant; superseded by `main.py` — ARCHIVE |
| `backend/glossary copy.py`, `backend/requirements copy.txt` | tracked | Dead copies — ARCHIVE |
| `frontend/src/App copy.js`, `App copy.css`, `LandingPage copy.jsx`, `components/CarbonTallyDemo copy.jsx`, `FileUploadHero copy.jsx` | tracked | Dead copies — ARCHIVE |
| `frontend/App_.js` | tracked+modified | Stray duplicate, **not imported anywhere** — REVIEW (likely accidental; remove only with PO approval) |
| `supabase/config copy.toml` | tracked | Duplicate config — ARCHIVE |
| `docs/architecture/UI/UI.zip`, `docs/architecture/DB_Migration/*.zip`, `docs/Final_Kimi/*.zip` | tracked | Historical archives — move to `docs/_archive/` later |
| `backend - backup.zip`, `backend/carbon_tally_backup.sql`, `carbon_tally_backup_data.sql` | tracked/ignored | Backup artifacts — ARCHIVE/REMOVE later |
| `prisma/` + `prisma.config.ts` + `seed.ts` + `seed.config.ts` + root `package.json` (Prisma/Snaplet) | untracked | Abandoned experiment (backend has no Prisma imports) — ARCHIVE/DELETE (PO) |
| `carbon-tally-ui-demo/` | tracked | Superseded demo — ARCHIVE |
| `src/` (root Python package: `commands/`, `providers/`) | tracked | Stray legacy import tooling — MOVE/ARCHIVE |
| `local_backups/env_backup/*` | ignored | Env backups with secrets on disk — **DELETE locally** (PO) |

---

## 20. Agent / AI Tooling Audit

- Tracked skill files existed in three locations: `.agents/skills/*` (69), `.claude/skills/*` (69), `.windsurf/skills/*` (69).
- Working-tree state:
  - `.agents/skills/*` — **modified** (69 files).
  - `.claude/skills/*` and `.windsurf/skills/*` — tracked files **deleted**; the directories now contain **untracked symlinks** pointing to an external directory `~/carbon_ledger/.agents/skills/*` (outside this repository).
- **Assessment:** this is agent-tooling churn produced by the skills installation/sync mechanism, **not project development**. The symlinks must **never be committed** (they are broken for any other clone). Whether to commit the `.claude`/`.windsurf` deletions and/or the `.agents` updates is a **PO decision** (§32); the safest default is to **exclude all `.agents`/`.claude`/`.windsurf` changes from the release commit** and handle tooling in a separate, optional commit.
- `.clineignore` (tracked, modified) and `.vercelignore` (tracked, modified): project config — include only if intentional (REVIEW).

---

## 21. Gitignore Audit

Current `.gitignore` (working-tree version — itself an uncommitted modification) already covers: `__pycache__`, `node_modules`, `.env*`, `build/`/`dist/`, `*.log`, `backups/`, `local_backups/`, `.tmp_pgdata/`, `_*.py`/`_*.txt` (root), `admin-dashboard/`, `.local-demo-credentials.md`, `current_project_structure.txt`.

**Gaps (recommend adding in the future commit task — NOT changed now):**
- `*.zip` / `admin-dashboard.zip` (127 MB on disk, currently untracked and visible to `git status`).
- `probe_out*.txt` (one contains a JWT).
- `screenshots/` (60+ files currently untracked and visible).
- `output/` (generated import/validation artifacts; currently partially tracked — tracked files should be removed from tracking in a future cleanup commit).
- `backend/test_results.json`, root `test_results.json` / `test_results_all.json`.
- `supabase/snippets/Untitled query *.sql`.
- `backend/.env.bak` (covered by `.env*`; on disk — delete locally).

**Verified:** `.env`, `.env.local`, `.env.production`, `.env.test`, `backend/.env`, `backend/.env.bak`, `admin/.env`, `frontend/.env*`, `tools/carbon_data_factory/.env`, and `local_backups/env_backup/*` are **all untracked** (gitignored). No `.env` file is tracked by Git.

---

## 22. Secret / Credential Audit

Summary of what exists and where (no secret values reproduced):

| Item | Category | Current tree | HEAD | History | Remediation status |
|---|---|---|---|---|---|
| `tools/carbon_data_factory/deeepseek_api.txt` | Third-party LLM provider API key (`sk-…`) | **Removed** (not present) | **Removed** (`878bd0f`) | **PRESENT at `2d23fb8` (2026-08-06, pushed)**; also referenced by checkpoint-only commits `5f4c361`/`4ce9368` (not ancestors of HEAD) | **HISTORY REMEDIATION REQUIRED** (see §23) |
| `probe_out5.txt` | JWT (RS256) captured in a scratch probe log | Untracked working-tree file | n/a | n/a (never committed) | **DELETE locally / never commit** (P2) |
| `frontend/src/supabaseClient.js` | Hard-coded live Supabase project URL + **publishable** (anon) key as fallback | Tracked (modified) | Tracked | present | Publishable key is public by Supabase design — low risk, but move URL/key to env (P2/P3) |
| `.env*` files (root, backend, frontend, admin, tools, env_backup) | Service-role keys, JWT secret, Resend key, DB URLs | On disk | Not tracked | Not in history | `.gitignore` correctly excludes them (P2: delete `backend/.env.bak` and `local_backups/env_backup/`) |
| `backend/main copy*.py` | Debug prints of secret env var presence (not values) | Tracked | Tracked | present | Remove copies later (P3) |

**Verified clean:** no embedded `sk-…`, `AKIA…`, `ghp_…`, private-key blocks, or service-role values were found in tracked files at HEAD (secret-pattern scan over `*.py/*.js/*.jsx/*.ts/*.json/*.md/*.txt/*.toml` returned only `os.getenv(...)` reads and a debug *presence* print).

---

## 23. Exposed API-Key History Analysis

### 23.1 Facts
- **Added:** commit `2d23fb8` "CarbonTally RC2 Final database baseline" (2026-08-06, author time 06:42 −0700) — `tools/carbon_data_factory/deeepseek_api.txt | 1 insertion`. Blob is 35 bytes; content begins with the `sk-` provider-key prefix (value intentionally not reproduced here).
- **Pushed:** `2d23fb8` was pushed to GitHub on 2026-08-06 14:11:20 UTC (push log). It is tagged `rc2-final` and is an ancestor of `origin/main`.
- **Removed:** commit `878bd0f` "Remove exposed API key file" (2026-08-24) — 1 deletion. Pushed 2026-08-24 08:17:00 UTC.
- **Status:** file is not in the working tree and not in HEAD, but **the credential is permanently present in the pushed GitHub history** at `2d23fb8` (and any downstream clone/fork).

### 23.2 Verdict
### HISTORY REMEDIATION REQUIRED
- **Affected path:** `tools/carbon_data_factory/deeepseek_api.txt`
- **Affected reachable commit:** `2d23fb8` (pushed); local-only checkpoint commits `5f4c361` and `4ce9368` (not ancestors of HEAD) also reference the path and should be pruned locally.
- **Secret category:** LLM-provider API key (appears to be `sk-…` style, DeepSeek-family).
- **Provider-side rotation/revocation:** **REQUIRED immediately.** The key is assumed compromised (it was public in a GitHub repo). Revoke it in the provider console and issue a new key if still needed.
- **Git history cleanup:** **Recommended** — remove the blob from all pushed history (e.g., `git filter-repo --path tools/carbon_data_factory/deeepseek_api.txt --invert-paths`) and force-push, OR replace the key-committing commit via history rewrite if the team accepts a rewrite of the single-developer `main` branch. If history rewriting is unacceptable, the residual risk is that the (revoked) key remains visible in history.
- **Risks of rewriting:** all clone SHAs change (single-developer repo — low blast radius); GitHub Actions caches/PR refs referencing old SHAs may break; require re-clone of collaborators; never rewrite while other clones are actively pushing.
- **Proposed future remediation procedure (separate authorized task):**
  1. Revoke the key at the provider.
  2. Create a full local backup of the repo (bare clone).
  3. Run `git filter-repo` on a clone to remove the path from all history.
  4. Verify with `git log --all -- tools/carbon_data_factory/deeepseek_api.txt` (empty) and a blob scan.
  5. Force-push to `origin/main`; update local refs; delete the old local backup after verification.
  6. Prune local Cline checkpoint refs containing the blob (`git for-each-ref refs/cline/checkpoints`), then `git reflog expire` + `git gc --prune=now` locally.
  7. Confirm no other secrets were exposed by scanning history.

---

## 24. Security Risk Assessment

| Severity | Finding | Status |
|---|---|---|
| **P0** | LLM-provider API key committed at `2d23fb8` and present in **pushed GitHub history** | Mitigated at HEAD (removed + pushed) but history still contaminated → revocation + history rewrite required |
| **P1** | Untracked `probe_out5.txt` contains a JWT (working-tree scratch) | Local-only; must never be committed; delete or gitignore |
| **P2** | `.env.bak` / `local_backups/env_backup/` retain secrets on disk | Gitignored, but should be deleted locally |
| **P2** | Hard-coded live Supabase URL + publishable key in `supabaseClient.js` | Publishable (low risk); move to env as hygiene |
| **P2** | 127 MB `admin-dashboard.zip` + generated artifacts untracked but not ignored | Accidental-commit hazard; add to `.gitignore` |
| **P3** | `backend/main copy*.py` debug prints reference secret env var names | Archive/remove later |
| **P3** | Cline checkpoint refs (146) keep stale objects locally, incl. possibly the key blob | Local GC later |

**Note:** the D37-0 billing RLS lockdown (verified in the previous audits) remains intact in the working-tree migrations; the uncommitted state does not weaken it, but those migrations must be committed + deployed for production enforcement to be effective in the remote database.

---

## 25. Build/Test Safety Assessment

- The working tree is **coherent enough to verify**: backend entry (`backend/main.py` → `api.router`) and frontend entry (`frontend/src/App.js` → `./v3/*`) both wire into the untracked release files, and all required modules are present in the working tree.
- **Committing only tracked+modified files would create an incomplete application** that cannot start (missing `api.v3_*`, `data/billing.py`, `services/billing.py`, `frontend/src/v3/`, new pages) and cannot migrate (missing D20–D37 SQL). The release commit set **must** include the untracked production/test/migration files.
- Untracked files required for a successful build/test include: all V3 backend modules (96 files), the V3 frontend (45 files), the D20–D37 migrations, the new tests, and the schema-dependent fixtures. Without them, `pytest` would skip the new suites and the frontend build would fail on `./v3/*` imports.
- **No tests or builds were executed during this audit** (read-only task). Baseline suite health is documented in the (uncommitted) D37 completion reports: unit 1039→1056, RLS 23→27, frontend 23→25 — to be re-verified in the commit/QA task.
- **Known caveat for the commit task:** ~467 files are EOL-only differences. If staged blindly, the diff would be unusable and could trigger mass CRLF changes in every clone. The commit task must use line-ending normalization (`.gitattributes` + `git add --renormalize`) and/or exclude EOL-only files from the content commit.

---

## 26. Release Boundary Assessment

**Conclusion: NO SAFE RELEASE BOUNDARY CAN CURRENTLY BE ESTABLISHED at the commit level — but a CLEAN LOGICAL RELEASE BOUNDARY EXISTS in the working tree and can be materialized with a disciplined commit sequence.**

Evidence:
- The last committed boundary is `a909cbe`/`878bd0f` (15-Aug snapshot + today's key removal). Everything since is uncommitted.
- The working tree is **mixed development**: (1) the legitimate D20–D37 release (backend, frontend, migrations, tests, docs), (2) EOL-only noise (~467 files), (3) generated artifacts (output/, test_results, probe logs, screenshots, zip), (4) agent-tooling churn (`.agents/.claude/.windsurf`).
- The release is **atomic** (tracked entry points depend on untracked modules), so the D20–D37 work cannot be split into "tracked-only" and "untracked" commits without breaking the build — it must be committed as a coherent set (or a small sequence of logical commits: migrations → backend → frontend → tests → docs), with the noise categories excluded.
- A clean boundary **can** be created by: normalizing EOL, excluding generated/scratch/agent files, then committing the release in logical groups (§27). Only then does a safe push become possible (§28).

---

## 27. Recommended Commit Strategy

**Preparation (in the authorized commit task, not this audit):**
1. Add line-ending control: introduce `.gitattributes` (`* text=auto eol=lf` + explicit binary exceptions) and run `git add --renormalize` so EOL-only files do not pollute the diff.
2. Add `.gitignore` entries for: `*.zip`, `probe_out*.txt`, `screenshots/`, `output/` (or plan to untrack `output/`), `backend/test_results.json`, root `test_results*.json`, `supabase/snippets/Untitled query *.sql`. (Do not ignore anything already tracked without a deliberate follow-up removal commit.)

**Recommended logical commit groups (in order):**
1. **Migrations** — the 10 untracked `supabase/migrations/20260821*–20260824*` files (+ resolve the `database/rc2/…init_schema.sql` duplicate before committing). Schema history first.
2. **Backend core + V3 services** — untracked `backend/api/v3_*.py`, `backend/data/*`, `backend/domain/*`, `backend/engines/*`, `backend/services/*` new files, plus the ~20 modified backend files (with EOL normalized).
3. **Frontend V3** — untracked `frontend/src/v3/`, `PricingPage.jsx`, `SelfServiceSignup.jsx`, `OnboardingPage.jsx`, `css/lp2.css`, `css/pricing_page.css`, plus modified `App.js` and the other modified frontend files.
4. **Tests** — untracked `backend/tests/unit/api/*` (new D-series tests), `integration/test_consultants.py`, etc., and the modified test files.
5. **Documentation** — untracked `docs/audit/cline/*`, `docs/architecture/*`, `docs/Pricing/*`, `docs/RECONSTRUCTED_TASK_HISTORY.md`, this report, and the modified docs.
6. **Config (separate, small)** — `.gitignore` + `supabase/config.toml` + `requirements.txt` only if the team agrees they belong in the release; otherwise leave uncommitted.
7. **Agent tooling (OPTIONAL, separate)** — only with explicit PO approval: `.agents/skills/*` updates + `.claude`/`.windsurf` deletions. Default recommendation: **exclude from the release commit**.

**Explicitly NOT to be committed:** `admin-dashboard.zip`, `probe_out*.txt`, `output/`, `v3_schema.sql` (until de-duplicated), `backend/test_results.json`, screenshots (unless PO wants them), the `.claude`/`.windsurf` symlinks, `prisma/`/`seed.ts`/`seed.config.ts` (until PO decides), `carbon-tally-ui-demo/`, copy/backup files, `.env*`.

---

## 28. Recommended Push Strategy

### DO NOT PUSH YET

Reasons:
1. **The working tree is mixed** — committing blindly would push EOL noise, generated artifacts, and agent-tooling symlinks alongside the D37 release.
2. **History is contaminated** — the API key exists in pushed history at `2d23fb8`; pushing the release now does not make that worse, but the cleanest sequence is: (a) revoke the key, (b) decide on history remediation, (c) then push the release. Pushing the release first is acceptable only if history remediation is definitively not going to happen (rewrites and release pushes conflict).
3. **The release has never been committed or verified in Git** — a push before a clean commit sequence would make the remote unreviewable.

**When PUSH NOW becomes correct:** after (a) the key is revoked and the history-remediation decision is made, (b) the §27 commit sequence is executed with EOL normalization and strict excludes, (c) the D37 test/build verification passes against the committed state, and (d) the PO has approved the commit groups. Then `git push origin main` is safe (fast-forward from `878bd0f`).

---

## 29. Repository Cleanup Manifest

(Actions for a FUTURE authorized cleanup task — nothing performed now.)

### KEEP — CURRENT PRODUCTION SOURCE
- All V3 backend modules (untracked list §10), V3 frontend (`frontend/src/v3/`, new pages), D20–D37 migrations, modified backend/frontend entry points, `backend/requirements.txt`, `vercel.json`, `runtime.txt`.

### KEEP — CURRENT TEST
- `backend/tests/unit/*`, `backend/tests/integration/*` (canonical + new D-series), `frontend/src/v3/__tests__/api.test.js`, `App.test.js`.

### KEEP — CANONICAL DOCUMENTATION
- `docs/audit/cline/` (D-series reports incl. this report), `docs/architecture/` (current), `docs/Pricing/`, `docs/guides/`.

### KEEP — DEVELOPMENT TOOLING
- `tools/` (minus the removed key file), `demodatagen/`, `backend/verify_startup.py`, `scripts` (when created).

### ARCHIVE — HISTORICAL BUT VALUABLE
- `docs/Final/`, `docs/Final_Kimi/`, `docs/architecture/DB_Migration/`, `docs/architecture/UI/`, `docs/cline/` (older), `CarbonTally_DB_Schema_V3M2.sql` / `v3_schema.sql` (schema snapshots), `docs/RECONSTRUCTED_TASK_HISTORY.md`, `screenshots/`, `mock_*.csv`, `v1.9.txt` → move to `docs/_archive/` or `archive/`.

### MOVE — VALID BUT MISPLACED
- Root one-off scripts (`clean.js`, `generate_*`, `list_endpoints.py`, `quick_api_ref.py`, `export_postman.py`, `test_endpoints.py`) → `scripts/`; root `src/` Python package → `tools/` or archive; `frontend/App_.js` → review/remove.

### CONSOLIDATE — DUPLICATE / FRAGMENTED
- `requirements*.txt` (root invalid `=>` file), duplicated audit-logger modules (`utils/` vs `infra/`), duplicated schema snapshots, `supabase/config copy.toml`, Prisma/Snaplet experiment (`prisma/`, `seed.ts`, `seed.config.ts`, `prisma.config.ts`).

### IGNORE — GENERATED / LOCAL-ONLY
- Add to `.gitignore`: `*.zip`, `probe_out*.txt`, `screenshots/`, `output/`, `*test_results*.json`, `supabase/snippets/Untitled query *.sql`, `backend/.env.bak`.

### DELETE — PROVEN UNNECESSARY (after PO approval; git history retains originals)
- `admin-dashboard.zip`, `backend - backup.zip`, `backend/carbon_tally_backup*.sql`, `clean_emissions_output.json`, `v1.9.txt`, copy files (`* copy.*`, `App copy.*`, `main copy*.py`, `requirements copy.txt`, `config copy.toml`), `probe_out*.txt`, `output/` tracked artifacts, `current_project_structure.txt`, `featurelist.txt`, `test_results*.json`.

### REVIEW — CANNOT SAFELY DETERMINE
- `.gitignore` + `supabase/config.toml` modifications (include in release or separate config commit?), `frontend/App_.js`, `.clineignore`/`.vercelignore` modifications, `database/rc2/00000000000000_init_schema.sql` (duplicate baseline?), agent-tooling changes (`.agents` modified / `.claude`+`.windsurf` deleted), `carbon-tally-ui-demo/`, `admin/` app (second dashboard), `backups/` contents, `supabase/snippets/Untitled query 673.sql`.

---

## 30. Recommended Future Repository Structure

(For a future refactor — NOT executed now.)

```
carbon_tally/
├── apps/
│   ├── frontend/            # existing frontend/
│   └── admin/               # existing admin/ (fate: PO decision)
├── backend/                 # existing backend/ (api/ services/ data/ domain/ engines/ core/ infra/ tests/)
├── supabase/                # migrations (single source of truth) + seed + config.toml
├── scripts/                 # dev/one-off/ops scripts (from root + tests/ root)
├── tools/                   # benchmark/load/schema/migration tooling (minus removed key file)
├── docs/                    # architecture/ audit/ cline/ guides/ pricing/ _archive/
├── .env.example             # the only tracked env template
└── README.md  CONTRIBUTING.md
```

**Key moves:** root scratch → delete; copy/backup files → delete; schema snapshots → `docs/_archive/`; `output/`/`screenshots/` → gitignored; one-off scripts → `scripts/`; abandoned experiments (`prisma/`, root `src/`, `carbon-tally-ui-demo/`) → archive/delete; `.gitattributes` for LF normalization.

---

## 31. Future Git Workflow Recommendations

1. **Commit discipline:** commit working-tree state frequently (at least per completed phase); the 9-day uncommitted D20–D37 window is the single largest risk in this repository's history.
2. **Line endings:** add `.gitattributes` (`* text=auto eol=lf`) now; prevent CRLF churn permanently.
3. **Secrets:** never commit keys; use `.env` + provider secrets managers; add a pre-commit secret scanner (e.g., gitleaks) — `probe_out5.txt` shows scratch logs can capture tokens.
4. **History safety:** do not force-push except for the (separately authorized) secret-history remediation; keep the repo single-`main` until release discipline is established.
5. **Local refs hygiene:** Cline checkpoint refs (146) should be periodically pruned locally; they never reach the remote.
6. **Ignore hygiene:** keep `.gitignore` aligned with the actual working tree (screenshots, zips, outputs) so `git status` stays reviewable.
7. **Release flow:** after this release is pushed, tag it (e.g., `v3.0-d37`) so the next audit can establish a clean boundary.

---

## 32. Product Owner Decisions Required

1. **History remediation:** approve the separate task to revoke the leaked key + rewrite pushed history (or accept residual risk with a revoked key)? — REQUIRED before/around the release push.
2. **Commit approval:** approve the §27 commit-group sequence (migrations → backend → frontend → tests → docs → config)?
3. **Line endings:** approve `.gitattributes` + `--renormalize` as part of the commit task?
4. **Agent tooling:** commit the `.agents/skills` updates and `.claude`/`.windsurf` deletions, or exclude them from the release?
5. **Config files:** include `.gitignore` + `supabase/config.toml` (port changes 54325→54425 etc.) + root `requirements.txt` changes in the release, or keep them uncommitted?
6. **Generated artifacts:** approve untracking/removing `output/`, `test_results*.json`, `screenshots/`, `probe_out*.txt`, `admin-dashboard.zip` (and their `.gitignore` entries)?
7. **Stray/duplicate files:** approve removal of `frontend/App_.js`, copy/backup files, `prisma/`+Snaplet experiment, `carbon-tally-ui-demo/`, root `src/` package?
8. **`admin/` app:** keep the separate admin dashboard app (and the `/ops` hub in the main app), or consolidate later?
9. **`database/rc2/…init_schema.sql`:** confirm it is not a second baseline before any migration commit.
10. **Release tag:** approve tagging the pushed release (e.g., `v3.0-d37`)?

---

## 33. Final Release Readiness Decision

**NOT RELEASE-READY IN ITS CURRENT GIT STATE.**

- The product code in the working tree is a complete, coherent D20–D37 release (verified structurally: entry points wire into all modules; D37 files present and substantial).
- Git state is **not** release-ready: nothing since 2026-08-15 is committed, the release is entangled with EOL noise and generated/scratch artifacts, and the pushed history contains the exposed API key.
- **Safe next operations (in order):**
  1. Revoke the leaked provider key (immediately).
  2. Authorize the history-remediation task (rewrite pushed history to remove the key) — or explicitly accept residual risk.
  3. Authorize the commit task per §27 (EOL normalization → commit groups: migrations → backend → frontend → tests → docs → config), keeping §29 excludes.
  4. Run the D37 verification (unit/RLS/frontend suites + production build) against the committed state.
  5. `git push origin main` (fast-forward from `878bd0f`), then tag the release.

---

## Development History Matrix (evidence-based)

| Identified Work / Period | Date Range | Commit Range | Evidence | Remote Status | Confidence |
|---|---|---|---|---|---|
| Early app: admin dashboard, beta signup/login, Supabase client, OAuth, mobile responsiveness, "v3.0 feature complete" | 2026-07-21 → 07-24 | `8b59378` … `a34b2f0` | Commit subjects | Pushed | High |
| Staff dashboard / review assignment / beta management; Manual Entry + review queue + log viewer | 2026-07-23 → 07-27 | `987500a` … `9c68ab1` | Commit subjects | Pushed | High |
| RC1/RC2 database baselines; sidebar/Realtime fixes; stop tracking SQL backups; **key committed** | 2026-08-04 → 08-06 | `eca5156` … `2d23fb8` (tag `rc2-final`) | Commit subjects; push log; `git show` | Pushed | High |
| V3 backend Phase 0–8 (foundation, infra, factor matching, emissions calc, document/AI extraction, workflow orchestrator) | 2026-08-07 → 08-08 | `97e0f69` … `8bcd490` | Phase-named commits; phase reports in working tree | Pushed | High |
| V3 database foundation + V3 API core | 2026-08-14 | `dbe72aa` | Checkpoint commit; push log | Pushed | High |
| V3 baseline (entities, customer factors, issues, schema snapshot, tests) | 2026-08-15 | `cfabe26` | Checkpoint commit; push log | Pushed | High |
| V3 Render-ready backend | 2026-08-15 | `a909cbe` | Checkpoint commit; push log | Pushed (last push before today) | High |
| **D20–D37 commercial release (uncommitted)** — consultants, white-label, processing assignment, lifecycle, private storage, evidence traceability, self-service onboarding, billing security + configurable subscription, commercial billing master; V3 backend/frontend/tests; D27–D37 docs | 2026-08-15 → 08-24 | **no commits** | Untracked file inventory; modified tracked wiring (`router.py`, `main.py`, `App.js`); untracked migrations + reports | **Working tree only** | High |
| Remove exposed API key file | 2026-08-24 | `878bd0f` | Commit subject; 1-file deletion | Pushed (08-24) | High |

---

## File Classification Matrix

| Path / Group | State | Classification | Evidence | Recommended Action | Risk | PO Review |
|---|---|---|---|---|---|---|
| `backend/api/v3_*.py` (24 files), `backend/data/billing.py` + data/*, `backend/domain/billing.py` + domain/*, `backend/services/billing.py` + services/*, `backend/engines/*` | Untracked | KEEP — PRODUCTION SOURCE | Imported by tracked `router.py`/`main.py`; D37 reports in working tree | Commit (group 2) | None | Approve |
| `frontend/src/v3/` (45 files), `PricingPage.jsx`, `SelfServiceSignup.jsx`, `OnboardingPage.jsx`, `css/lp2.css`, `css/pricing_page.css` | Untracked | KEEP — PRODUCTION SOURCE | Imported by tracked `App.js` | Commit (group 3) | None | Approve |
| `supabase/migrations/20260821*…20260824*` (10) | Untracked | KEEP — MIGRATION | D20–D37 schema history; chronology coherent | Commit (group 1) | None | Approve |
| New backend tests (`test_billing_core.py`, `test_commercial_settings.py`, etc.) + modified test files | Untracked / Modified | KEEP — TEST | D37 report suite counts | Commit (group 4) | None | Approve |
| `docs/audit/cline/*D27–D37*`, `docs/architecture/*`, `docs/Pricing/*`, `docs/RECONSTRUCTED_TASK_HISTORY.md`, this report | Untracked | KEEP — DOCUMENTATION | Project history + reports | Commit (group 5) | None | Approve |
| `backend/main.py`, `backend/api/router.py`, `frontend/src/App.js`, `backend/config.py`, `supabaseClient.js`, ~40 other real-content-modified files | Modified | KEEP (release wiring) | Real content diff; EOL-normalize before commit | Commit (groups 2–5) after `--renormalize` | EOL corruption if not normalized | Approve |
| ~467 EOL-only modified files | Modified | IGNORE (for content commit) | `git diff --ignore-space-at-eol` = no content change | Exclude or renormalize | CRLF pollution | Approve `.gitattributes` |
| `.claude/skills/*`, `.windsurf/skills/*` (138 deleted tracked + 18 untracked symlinks) | Deleted/Untracked | REVIEW — agent tooling | Symlinks → external `~/carbon_ledger/.agents/skills` | Exclude from release; separate optional commit | Broken symlinks if committed | Decide |
| `.agents/skills/*` (69 modified) | Modified | REVIEW — agent tooling | Skill-system sync | Exclude or separate commit | None | Decide |
| `.gitignore`, `supabase/config.toml`, root `requirements.txt` | Modified | REVIEW — config | Env/ignore changes; toml port changes | Separate config commit or leave | None | Decide |
| `output/` (13 deleted + 7 untracked) | Deleted/Untracked | IGNORE — generated | Generated import/validation output | `.gitignore` + untrack commit | None | Approve |
| `admin-dashboard.zip`, `backend/test_results.json`, `probe_out*.txt`, `v3_schema.sql`, `screenshots/` (~60), `supabase/snippets/Untitled query 673.sql` | Untracked | IGNORE / DELETE | Generated/scratch/binary; `probe_out5.txt` has a JWT | `.gitignore`; delete probes locally | JWT exposure if committed | Approve |
| `frontend/App_.js` | Modified | REVIEW | Not imported anywhere | Confirm then remove | None | Decide |
| Copy/backup files (`* copy.*`, `main copy*.py`, `requirements copy.txt`, `config copy.toml`, `backend - backup.zip`) | Tracked | DELETE — proven unnecessary | Duplicates of live files | Future cleanup commit | None | Approve |
| `prisma/`, `prisma.config.ts`, `seed.ts`, `seed.config.ts`, root `src/` pkg, `carbon-tally-ui-demo/` | Tracked/Untracked | ARCHIVE/DELETE | Abandoned experiments (no Prisma imports in backend) | Archive/delete later | None | Approve |
| `.env*` on disk (incl. `backend/.env.bak`, `local_backups/env_backup/`) | Ignored | LOCAL-ONLY | Secret-bearing; gitignored | Delete `.bak`/backup copies locally | Secret leakage if shared | Approve |
| `tools/carbon_data_factory/deeepseek_api.txt` | Removed at HEAD | P0 — REMEDIATE HISTORY | Committed `2d23fb8`, pushed | History rewrite task + key revocation | **P0** | **REQUIRED** |

---

## Security Findings

| Severity | Finding | Where | Status / Action |
|---|---|---|---|
| **P0** | LLM-provider API key committed and **pushed** at `2d23fb8` (2026-08-06); removed at HEAD (`878bd0f`) but persists in pushed history | `tools/carbon_data_factory/deeepseek_api.txt` | Revoke key now; history remediation as separate authorized task |
| **P1** | JWT token present in untracked scratch file | `probe_out5.txt` | Delete locally; ensure never committed |
| **P2** | Secrets retained on disk in env backups | `backend/.env.bak`, `local_backups/env_backup/*` | Delete locally (gitignored) |
| **P2** | Live Supabase URL + publishable key hard-coded in source fallback | `frontend/src/supabaseClient.js` | Move to env; low risk (publishable key) |
| **P2** | Large binaries + generated files untracked but not ignored | `admin-dashboard.zip`, `screenshots/`, `output/` | Add to `.gitignore` |
| **P3** | Debug prints referencing secret env var names | `backend/main copy*.py` | Archive/remove |
| **P3** | 146 local Cline checkpoint refs keep stale objects (incl. possibly the key blob) locally | `refs/cline/checkpoints/*` | Local GC/prune later |
| **P3** | No pre-commit secret scanner configured | repo-wide | Add gitleaks/secret-scan hook |

No other embedded credentials were found in tracked files at HEAD; `.env` files are not tracked. The billing RLS lockdown migrations (D37-0) are intact in the working tree but must be committed and applied to production for enforcement.

---

## Final Questions

**1. What commit is currently on GitHub `main`?**
`878bd0f9eb5d277510b9b911ecd1a10be0213bd1` — "Remove exposed API key file" (pushed 2026-08-24 08:17:00 UTC).

**2. What commit is currently local `main`?**
`878bd0f9eb5d277510b9b911ecd1a10be0213bd1` (identical to origin/main).

**3. Are local and remote currently synchronized at HEAD?**
Yes. `git rev-list --left-right --count origin/main...main` = `0 0`; merge-base = HEAD.

**4. Are there local commits not on GitHub?**
No. There are zero local-only commits.

**5. Are there remote commits not local?**
No. Zero remote-only commits.

**6. What is the oldest commit currently local but not remote, if any?**
None. Local and remote share the same 70-commit history ending at `878bd0f`.

**7. Can the exact previous push date be established?**
**Yes.** `.git/logs/refs/remotes/origin/main` proves the previous push brought origin/main to `a909cbe` on **2026-08-15 12:20:33 UTC**.

**8. What development history can be reliably reconstructed?**
The full 70-commit chronology (July 2026 early app → Aug 4–6 RC baselines → Aug 7–8 Phase 0–8 V3 backend → Aug 14–15 V3 checkpoints → Aug 15–24 uncommitted D20–D37 release → Aug 24 key removal), reconstructed from commit subjects, dates, push logs, changed files, and migration chronology (§7).

**9. What important work exists only in the working tree?**
The entire D20–D37 release: V3 backend modules (96 files), V3 frontend (45 files), D20–D37 migrations (10), new tests (~26), D27–D37 documentation (~30), plus ~46 real-content modifications to tracked files.

**10. Which untracked files are legitimate current source?**
The V3 backend (api/data/domain/engines/services), V3 frontend (`frontend/src/v3/` + new pages), the D20–D37 migrations, the new tests, and the canonical docs (§10).

**11. Which untracked files should not be committed?**
`admin-dashboard.zip`, `probe_out*.txt`, `output/`, `v3_schema.sql`, `backend/test_results.json`, screenshots, `.claude`/`.windsurf` symlinks, `supabase/snippets/Untitled query 673.sql`, and any env-like content.

**12. Does the removed API-key file exist in Git history?**
**Yes.** Committed at `2d23fb8` (2026-08-06, pushed), removed at `878bd0f` (2026-08-24). The credential remains in pushed history.

**13. Are other secrets present?**
A JWT in untracked `probe_out5.txt`; env backups on disk (gitignored); a publishable Supabase key hard-coded in `supabaseClient.js`. No other embedded credentials in tracked files.

**14. Does Git history remediation need to happen?**
**Yes** — the pushed history contains the API key at `2d23fb8`. Provider-side revocation is mandatory; history rewrite is strongly recommended (separate authorized task, §23).

**15. Is the repository safe to push further?**
Not yet. Commit the release cleanly (§27), decide on history remediation, verify the committed build/tests, then push.

**16. What should be committed first?**
The D20–D37 migrations, then backend, frontend, tests, documentation (in that order), with EOL normalization and strict excludes (§27).

**17. What should be cleaned before the next push?**
EOL-only files (normalize), generated artifacts, probe logs, screenshots, zip archives, agent-skill churn — excluded from the release commit; `.gitignore` updated.

**18. What should be archived?**
Historical docs (`docs/Final*`, `docs/architecture/DB_Migration|UI`, older `docs/cline/`), schema snapshots, screenshots, mock data, `v1.9.txt`, the abandoned `prisma/`/`carbon-tally-ui-demo/`/root `src/` experiments.

**19. What should be ignored?**
`*.zip`, `probe_out*.txt`, `screenshots/`, `output/`, `*test_results*.json`, `supabase/snippets/Untitled query *.sql`, `backend/.env.bak` (already covered by `.env*`).

**20. What should be deleted only after Product Owner approval?**
Copy/backup files, `frontend/App_.js`, `admin-dashboard.zip`, tracked `output/` artifacts, `backend - backup.zip`, `.env.bak`/env backups, `carbon-tally-ui-demo/`, root `src/`, `prisma/` experiment.

**21. What should remain untouched?**
The D20–D37 working-tree release content, the D37-0 RLS lockdown migrations, `supabase/migrations` history, the committed 70-commit history (until the separate secret-remediation task), all `.env` files, and the current HEAD state until the authorized commit task begins.

---

*End of Git repository audit. This is a READ-ONLY audit: no commits, staging, pushes, deletions, restores, history rewrites, or source modifications were performed. The only repository addition is this report.*
