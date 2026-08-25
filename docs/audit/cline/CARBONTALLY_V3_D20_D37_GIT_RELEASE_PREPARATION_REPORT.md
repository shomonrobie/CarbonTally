# CarbonTally V3 — D20–D37 Git Release Preparation Report

**Task type:** AUDIT + PREPARATION ONLY. Read-only analysis of the repository, Git metadata, diffs, migrations, and release contents.
**Executed:** No commits, no staging, no pushes, no history rewrites, no deletions, no restores, no `.gitignore`/source/migration/configuration modifications, no line-ending changes, no migrations run, no database state change. The only repository addition is this report.
**Date:** 2026-08-24

---

## 1. Executive Summary

The D20–D37 CarbonTally V3 release is **complete and coherent in the working tree, entirely uncommitted, and atomically wired** into the currently tracked application entry points.

Key conclusions:

1. **Git state is exactly as expected:** `main` = `origin/main` = `878bd0f` ("Remove exposed API key file"), `0 ahead / 0 behind`. No discrepancy from the prior audit. Working tree: 582 modified, 151 deleted, 186 untracked, 0 staged.
2. **EOL/CRLF claim independently verified:** of the 582 modified tracked files, **534 are EOL-only** (content identical to HEAD apart from CRLF↔LF), **48 have real content changes**, of which **19 are "mixed"** (real changes + CRLF) and must be EOL-normalized before commit.
3. **The D20–D37 release is atomic:** tracked `backend/api/router.py`, `backend/main.py`, and `frontend/src/App.js` import the currently-untracked V3 modules, migrations, and pages. A partial commit of tracked files only would produce a non-importable application. **One atomic release commit (or a strictly ordered commit sequence that lands together before any push) is required.**
4. **Phase evidence is documentable for D15, D19–D22, D27, D32, D33, D33.1, D34, D35, D36, D37-0, D37-1…9** from migrations, test names, reports, architecture records, and code comments. **D23–D26, D28–D31, D29 have partial/indirect evidence** (test names, reports, architecture sections, code comments) — see the Phase Evidence Matrix (§8). No phase name is invented; anything not evidenced is marked accordingly.
5. **Secrets:** the previously exposed DeepSeek API key is absent from the working tree and from HEAD, but **confirmed present in historical commit `2d23fb8`** (revoked by the Product Owner; history remediation deferred to a separate task). One live JWT remains in untracked scratch file `probe_out5.txt` (must never be committed). No other live credentials were found in tracked files.
6. **The Product Platform Experience Standard document (`CARBONTALLY_V3_PUBLIC_PRODUCT_PLATFORM_EXPERIENCE_STANDARD.md`) is NOT present in the repository** (§13/D38 note).
7. **Release decision: DO NOT COMMIT/PUSH in this task.** The next authorized task should execute the staging plan (§29–§31): EOL normalization → stage migrations → backend → frontend → tests → docs → approved config → verify → commit (one atomic release commit or the ordered multi-commit sequence) → run tests/build → push → tag.

---

## 2. Safety Preconditions

| Precondition | Status |
|---|---|
| HEAD matches the prior audit (`878bd0f`) | ✅ Verified (`git rev-parse HEAD` = `878bd0f9eb5d277510b9b911ecd1a10be0213bd1`) |
| origin/main matches HEAD | ✅ Verified (`0 ahead / 0 behind`, merge-base = HEAD) |
| Exposed DeepSeek key revoked by PO | ✅ Product Owner assertion recorded (accepted as given) |
| Full filesystem backup created by PO outside repo | ✅ Product Owner assertion recorded |
| No staging present | ✅ Verified (0 staged) |
| No stash present | ✅ Verified (`git stash list` empty) |
| No submodules | ✅ Verified (`git submodule status` empty) |
| No Git LFS | ✅ Not installed/configured (`git lfs` is not a git command) |
| Working tree untouched by this audit | ✅ Verified at end (HEAD unchanged; no source modifications) |

---

## 3. Current Git State

| Attribute | Value |
|---|---|
| Current branch | `main` (only local branch) |
| HEAD commit | `878bd0f9eb5d277510b9b911ecd1a10be0213bd1` — "Remove exposed API key file" (2026-08-24) |
| origin/main | `878bd0f9eb5d277510b9b911ecd1a10be0213bd1` |
| Ahead / behind | `0 / 0` |
| Merge base (main, origin/main) | `878bd0f` (both tips identical) |
| Tracking | `main` → `origin/main` (up to date) |
| Remote | single: `origin` → `https://github.com/shomonrobie/CarbonTally.git` |
| Total commits | 70 |
| Tags | `rc2-final` (`2d23fb8`), `v2.1-phase4` (`be405d8`), `v2.1.1-phase3` (`ae1d685`) — all ancestors of HEAD |
| Cline checkpoint refs | 146 local refs (`refs/cline/checkpoints/*`) — local only, never on remote |

---

## 4. Remote State

- `origin` fetch/push URL: `https://github.com/shomonrobie/CarbonTally.git`.
- Remote HEAD: `refs/remotes/origin/HEAD → origin/main`.
- Last push to remote: `878bd0f` on 2026-08-24 08:17:00 UTC (per `.git/logs/refs/remotes/origin/main`).
- Previous push before that: `a909cbe` on 2026-08-15 12:20:33 UTC (see Git Repository Audit report).
- **No remote state change is required by this task.**

---

## 5. Current HEAD

`878bd0f9eb5d277510b9b911ecd1a10be0213bd1` — "Remove exposed API key file"
- Parent: `a909cbe` ("checkpoint: CarbonTally V3 Render-ready backend", 2026-08-15).
- Contents: deletes `tools/carbon_data_factory/deeepseek_api.txt` (1 file, 1 deletion).
- This is the commit point at which the D20–D37 release (working tree) will be layered.

---

## 6. Working Tree Summary

| Category | Count | Composition |
|---|---|---|
| Modified | **582** | 48 real-content changed (44 project + agent-skill stragglers), **534 EOL-only** |
| Deleted | **151** | 138 `.claude/skills/*` + `.windsurf/skills/*` tracked files (replaced by symlinks to external `~/carbon_ledger/.agents/skills/`), 13 `output/` generated artifacts |
| Untracked | **186** | 96 backend, 50 frontend, 11 supabase, 42 docs, 96 screenshots (incl. this report + 2 prior audit reports) |
| Staged | 0 | none |
| Diff magnitude | 733 files, 275,850 insertions, 801,925 deletions | dominated by deletion of generated artifacts (`output/json/validation_report.json` −203 K lines, `imported_rows.json` −189 K, `output/sql/import_defra_2025.sql` −105 K) and EOL-only rewrites |

---

## 7. Development History Relevant to D20–D37

The D20–D37 release was developed **between 2026-08-15 (last push `a909cbe`) and 2026-08-24**, entirely as uncommitted working-tree changes. Evidence: zero intermediate commits in that window (`git log`/`git reflog`), untracked migration timestamps `20260821…20260824`, untracked D-series reports, and the architecture document's dated records (e.g., D24 2026-08-22, D25 2026-08-22, D26 2026-08-22).

Committed history immediately before the release (evidence context):
- `a909cbe` 2026-08-15 — V3 Render-ready backend checkpoint (last push).
- `cfabe26` / `dbe72aa` 2026-08-14/15 — V3 baseline + database-foundation checkpoints.
- Phase 0–8 (2026-08-07/08) — the earlier V3 backend build.
- `2d23fb8` 2026-08-06 — RC2 database baseline (**contains the exposed DeepSeek key**).

---

## 8. Phase Evidence Matrix

Each phase is listed only where repository evidence exists. "Not provable" means no direct repository evidence was found for a distinct named phase in this release window (the work may exist folded into other migrations/modules).

| Phase | Evidence | Where | Status |
|---|---|---|---|
| D15 | Active-consultant grant | Migration `20260821000000_d20_d15_active_consultant_grant.sql` (name) | PROVEN (in release set) |
| D19 | Consultant-client lifecycle | Migration `20260822010000_d27_d19_customer_lifecycle.sql`; tests `test_d19_lifecycle.py`, `test_d19_domain.py`; architecture §41 ("D19 consultant-client → direct customer BLOCKED — business decision") | PROVEN (in release set) |
| D20 | Active consultant grant | Migration `d20_d15_active_consultant_grant` (name); architecture §D20 | PROVEN |
| D21 | White-label branding | Migration `20260821010000_d21_white_label_branding.sql`; `backend/api/consultant_branding.py`; `test_consultant_branding.py`; architecture §D21 | PROVEN |
| D22 | Processing work assignment | Migration `20260821020000_d22_processing_work_assignment.sql`; architecture §D22 (assign control, entity scope) | PROVEN |
| D23 | Extraction UX | Test `test_v3_d23_extraction_ux.py`; architecture references | PARTIAL (test + arch; no dedicated migration — app-only work) |
| D24 | Processing-Entity workspace completion | Architecture §24 (2026-08-22): `v3/ops/ProcessingEntitiesTab.jsx`, `EntityExtractionWorkspace.jsx`, entity assign/scope | PROVEN (frontend + arch records; no dedicated migration) |
| D25 | Product-completion UX/workflow (issues, messaging, notifications, branding payload) | Architecture §40 (2026-08-22): issues/messaging/notifications implementations; frontend Jest 12/12 "added D25 API-client tests" | PROVEN (code + arch record) |
| D26 | Product-completion audit + scale hardening (bounded pagination) | Architecture §41 (2026-08-22); notifications pagination `limit 1..500` in `v3/api.js`/backend | PROVEN (code + arch record) |
| D27 | Customer lifecycle (extends D19) | Migration `d27_d19_customer_lifecycle`; reports `D27_AUDIT_INVENTORY`, `D27_D19_FINAL_REPORT`; architecture §D27 | PROVEN |
| D28 | Visual QA | Report `CARBONTALLY_V3_D28_VISUAL_QA_REPORT.md` | PROVEN (documentation) |
| D29 | Reliability/UX (bounded requests, server-authoritative post-login routing) | Code comments `frontend/src/v3/api.js`: `// D29/F3 — bounded requests`, `// D29/F5 — resolve … landing workspace` | PARTIAL (code comments only; no migration) |
| D30 | Reporting completeness | Report `D30_REPORTING_COMPLETENESS_REPORT.md`; `screenshots/d30_reporting/` | PROVEN (docs + screenshots) |
| D31 | Reporting completion | Report `D31_REPORTING_COMPLETION_REPORT.md`; `screenshots/d31_reporting/` | PROVEN (docs + screenshots) |
| D32 | Private documents storage | Migration `20260823000000_d32_private_documents_storage.sql`; `test_storage_security.py`; report `D32_FINAL_PRODUCT_COMPLETENESS_AUDIT.md` | PROVEN |
| D33 | Evidence traceability | Migration `20260823010000_d33_evidence_traceability.sql`; `test_evidence_*.py`; report `D33_EVIDENCE_TRACEABILITY_REPORT.md`; `screenshots/d33_evidence/` | PROVEN |
| D33.1 | Evidence precision / customer evidence | Report `D33_1_EVIDENCE_PRECISION_REPORT.md`; evidence panels in `frontend/src/v3/components/EvidenceRecordPanel.jsx` | PROVEN (docs + code) |
| D34 | Customer journey audit | Report `D34_PRODUCTION_CUSTOMER_JOURNEY_READINESS_REPORT.md`; `screenshots/d34_customer_journey/` | PROVEN (documentation + assets) |
| D35 | Self-service onboarding | Migration `20260824010000_d35_self_service_onboarding.sql`; `test_self_service_onboarding.py`; `frontend/src/SelfServiceSignup.jsx`, `OnboardingPage.jsx`, `OnboardingWizard.jsx`; report `D35_TECHNICAL_REMEDIATION_REPORT.md` | PROVEN |
| D36 | Billing & commercial architecture audit | Report `D36_BILLING_COMMERCIAL_ARCHITECTURE_AUDIT.md` | PROVEN (documentation) |
| D37-0 | Billing security + configurable subscription foundation | Migration `20260824020000_d37_0_….sql`; `test_commercial_settings.py`; `backend/api/v3_commercial.py`; `organizations.billing_mode`; report `D37_0_…REPORT.md` | PROVEN |
| D37-1 … D37-9 | Commercial billing master (one implementation) | Migration `20260824030000_d37_master_commercial_billing.sql`; `v3_billing.py`, `data/billing.py`, `domain/billing.py`, `services/billing.py`, `test_billing_core.py`; `BillingPage.jsx`, `CommercialTab.jsx`; report scope line "D37-1 … D37-9 (one master implementation over the completed D37-0 foundation)" | PROVEN (master scope; individual D37-1…9 sub-labels are internal to the master, not separately evidenced) |
| p9 | RLS recursion fix (not a D-phase; precedes D-series in this window) | Migration `20260822000000_p9_rls_recursion_fix.sql` | PROVEN (migration) |

Additional workstreams evidenced (not D-numbered): processing workflow (`v3_processing_workflow.py`, `engines/processing_workflow.py`), discovery (`v3_discovery.py`, `data/discovery.py`), messaging (`v3_messaging.py`), notifications (`v3_notifications.py`), QC (`v3_qc.py`), review (`v3_review.py`), manual extraction (`v3_manual_extraction.py`), suppliers (`v3_suppliers.py`), verifications (`v3_verifications.py`), whitelabel (`v3_whitelabel.py`, `domain/whitelabel.py`), reporting (`v3_reporting.py`, `data/reporting.py`), exports (`v3_exports.py`), storage (`services/storage.py`), partners/operations domain (`domain/partners.py`, `domain/operations.py`), pdf render (`engines/pdf_render.py`).

Phases with **NO evidence in this release window** (may be folded elsewhere or never separately implemented): D0–D14, D16–D18 (pre-existing/legacy), D37-1…D37-9 as *individually evidenced sub-commits* (they exist only as a master scope). Where a phase name is not provable, this report says so rather than inventing it.

---

## 9. File Classification Method

Every working-tree change was classified against the repository by:
1. **Status** (modified / deleted / untracked) from `git status --short`.
2. **EOL content check** via `git diff --ignore-space-at-eol --name-only` to isolate real-content changes.
3. **CRLF check** via `file` on each real-content file.
4. **Reference check** — is the file imported/required by tracked entry points (`backend/api/router.py`, `backend/main.py`, `frontend/src/App.js`, `backend/api/v3_*.py`, migrations chronology)?
5. **Generation check** — is it a build/generated/scratch artifact (output, probe logs, test results, screenshots, zips)?
6. **Dedup check** — is it a known duplicate/backup/copy (`* copy.*`, `.bak`, `.zip`, snapshot files)?

Classification labels (Task 3): A. REQUIRED CURRENT APPLICATION SOURCE · B. REQUIRED CURRENT DATABASE/MIGRATION · C. REQUIRED CURRENT TEST · D. REQUIRED CURRENT CONFIGURATION · E. REQUIRED CURRENT DOCUMENTATION · F. REQUIRED CURRENT ASSET · G. GENERATED BUT REQUIRED · H. GENERATED AND NOT REQUIRED · I. TEMPORARY / DEBUG / PROBE · J. OLD / LEGACY / SUPERSEDED · K. BACKUP / DUPLICATE · L. EOL-ONLY / CRLF-LF NOISE · M. SECRET / SECURITY-SENSITIVE · N. UNKNOWN — REQUIRES PRODUCT OWNER DECISION.

---

## 10. Full File Classification Summary

| Class | Count | Representative items |
|---|---|---|
| A. REQUIRED APPLICATION SOURCE | ~145 | All untracked `backend/api/v3_*.py`, `backend/data/*` (billing, consultants, discovery, exports, etc.), `backend/domain/*`, `backend/services/*`, `backend/engines/*`; `frontend/src/v3/*` (45); `PricingPage.jsx`, `SelfServiceSignup.jsx`, `OnboardingPage.jsx`, `css/lp2.css`, `css/pricing_page.css`; 44 real-content-modified tracked files |
| B. REQUIRED DATABASE/MIGRATION | 10 | The ten untracked `supabase/migrations/20260821*–20260824*` migrations |
| C. REQUIRED TEST | ~26 | Untracked `backend/tests/unit/api/*` (test_billing_core, test_commercial_settings, test_d19_lifecycle, test_evidence_*, etc.), `integration/test_consultants.py`, `test_customer_admin.py`, `test_report_versions.py`, `unit/domain/test_d19_domain.py`, `unit/engines/test_pdf_render.py`; 6 modified test files |
| D. REQUIRED CONFIGURATION | 3–6 | `backend/requirements.txt` (modified, CRLF), `backend/requirements-dev.txt` (untracked), `supabase/config.toml` (modified), `vercel.json` (EOL-only), `.gitignore` (modified, CRLF) — PO decision on inclusion |
| E. REQUIRED DOCUMENTATION | ~40 | Untracked `docs/audit/cline/*` (D27–D37 reports), `docs/architecture/CARBONTALLY_V3_*`, `docs/Pricing/*`, `docs/RECONSTRUCTED_TASK_HISTORY.md`, `docs/cline/prompts/*`; modified docs (2) |
| F. REQUIRED ASSET | 0 (PO decision) | `frontend/src/images/*`, `frontend/public/*` are already tracked; no new required assets identified |
| G. GENERATED BUT REQUIRED | 0 | none identified (no generated file is required by the release) |
| H. GENERATED NOT REQUIRED | ~20 | `output/` (7 untracked + 13 deleted), `v3_schema.sql`, `backend/test_results.json`, `test_results.json`/`_all.json`, `CarbonTally_DB_Schema_V3M2.sql` (schema snapshot) |
| I. TEMPORARY / DEBUG / PROBE | ~15 | `probe_out1…9.txt`, `_*.txt`/`tmp_*.txt` scratch (gitignored), `supabase/snippets/Untitled query 673.sql` |
| J. OLD / LEGACY / SUPERSEDED | ~30 | copy files, `backend/main copy*.py`, `main_v2.py`, `frontend/App_.js`, `carbon-tally-ui-demo/`, root `src/`, `prisma/` experiment, legacy `tests/` scripts |
| K. BACKUP / DUPLICATE | ~15 | `backend - backup.zip`, `admin-dashboard.zip`, `backend/carbon_tally_backup*.sql`, `database/rc2/…init_schema.sql` (divergent duplicate), `local_backups/env_backup/*` |
| L. EOL-ONLY NOISE | **534** | ~467 modified tracked files with content identical to HEAD except CRLF |
| M. SECRET / SECURITY-SENSITIVE | 3 | `probe_out5.txt` (JWT), `.env*`/`env_backup` (gitignored, on disk), hard-coded publishable Supabase key in `supabaseClient.js` |
| N. UNKNOWN — PO DECISION | ~10 | `.gitignore`/`supabase/config.toml` inclusion, `.clineignore`/`.vercelignore`, `frontend/App_.js`, agent-tooling changes, `database/rc2/…init_schema.sql`, `admin/` app, `carbon-tally-ui-demo/` |

Complete per-file mapping is in **Appendix A**.

---

## 11. EOL/CRLF Analysis (Task 4 — independent verification)

Method: `git diff --name-only` (733 = 582 modified + 151 deleted) vs `git diff --ignore-space-at-eol --name-only` (199 = 48 real-content modified + 151 deleted), then `file` CRLF detection on each real-content file.

| Category | Count | Basis |
|---|---|---|
| EOL-only (content identical to HEAD) | **534** | 582 − 48 (real-content modified) |
| Real content changes (LF, clean) | **29** | `file` → LF among the 48 |
| Mixed: real content changes + CRLF | **19** | `file` → CRLF among the 48 |
| Deleted | 151 | separate status |

The 19 mixed files (must be EOL-normalized before commit): `.gitignore`, `CarbonTally_DB_Schema_V3M2.sql`, `backend/auth.py`, `backend/config.py`, `backend/main.py`, `backend/requirements.txt`, `backend/routes/organizations/members.py`, `docs/cline/Architecture_Review.md`, `docs/cline/Backend_Architecture_v2.1.md`, `frontend/src/AuthCallback.js`, `frontend/src/BetaSignup.jsx`, `frontend/src/LandingPage.jsx`, `frontend/src/Login.js`, `frontend/src/MagicLink.jsx`, `frontend/src/components/AppFooter.jsx`, `frontend/src/components/AppHeader.jsx`, `frontend/src/css/LandingPage.css`, `frontend/src/supabaseClient.js`, `requirements.txt`.

**Conclusion: the previous audit's ~534 estimate is confirmed exactly.** Example proof: `backend/routes/communication.py` shows 2,303/2,303 insertions/deletions in the raw diff but **zero** in `--ignore-space-at-eol` (CRLF-only change).

---

## 12. Real Content Change Analysis (Task 4 continued)

The 48 real-content modified files are the legitimate D20–D37 wiring changes:

- **Backend (19):** `api/contracts.py`, `api/dependencies.py`, `api/issues.py`, `api/router.py`, `auth.py`, `config.py`, `data/__init__.py`, `data/emission_factors.py`, `data/emissions_logs.py`, `data/issues.py`, `data/organizations.py`, `data/reports.py`, `domain/calculation.py`, `domain/issue.py`, `domain/organization.py`, `engines/calculation.py`, `engines/report_generation.py`, `main.py`, `routes/organizations/members.py`
- **Tests (6):** `integration/conftest.py`, `integration/test_reports.py`, `integration/test_v3_rls_behavior.py`, `unit/api/fakes.py`, `unit/api/test_foundation.py`, `unit/api/test_v3_issues.py`
- **Frontend (11):** `src/App.js` (+171/−2 V3 wiring), `AuthCallback.js`, `BetaSignup.jsx`, `LandingPage.jsx`, `Login.js`, `MagicLink.jsx`, `components/AppFooter.jsx`, `components/AppHeader.jsx`, `css/LandingPage.css`, `supabaseClient.js`, `frontend/App_.js` (stray duplicate)
- **Config/docs (8):** `.gitignore`, `supabase/config.toml`, root `requirements.txt`, `CarbonTally_DB_Schema_V3M2.sql`, `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md`, `docs/cline/Architecture_Review.md`, `docs/cline/Backend_Architecture_v2.1.md`, `docs/cline/# CarbonTally Backend v2.1 …Implementation Preparation Pack.md`

`supabase/config.toml` diff is a local port renumber (54325→54425, 54326→54426, 54320→54420, 54329→54429) — **local environment change, NOT part of the application release** (PO decision: exclude or separate config commit). `backend/main.py` is a 394/362 rewrite (V3 composition root) — part of the release. `frontend/src/App.js` +171/−2 is the V3 route wiring — part of the release.

---

## 13. Required Release Files (Task 5)

The D20–D37 release REQUIRED set (must be preserved/committed together) is the union of:

**Backend (new, untracked):** `backend/api/v3_billing.py`, `v3_commercial.py`, `v3_processing_workflow.py`, `v3_documents.py`, `v3_emissions.py`, `v3_operations.py`, `v3_organizations.py`, `v3_reports.py`, `v3_reporting.py`, `v3_exports.py`, `v3_notifications.py`, `v3_messaging.py`, `v3_discovery.py`, `v3_manual_extraction.py`, `v3_qc.py`, `v3_review.py`, `v3_verifications.py`, `v3_suppliers.py`, `v3_whitelabel.py`, `v3_consultants.py`, `consultant_auth.py`, `consultant_branding.py`, `operations_auth.py`; `backend/data/billing.py`, `consultants.py`, `discovery.py`, `exports.py`, `invitations.py`, `manual_extraction.py`, `messaging.py`, `notifications.py`, `organization_files.py`, `queue_settings.py`, `report_versions.py`, `reporting.py`, `review_queue.py`, `roles.py`, `staff.py`, `suppliers.py`, `tenant.py`, `upload_batches.py`, `verifications.py`, `whitelabel.py`; `backend/domain/billing.py`, `branding.py`, `discovery.py`, `evidence.py`, `messaging.py`, `operations.py`, `partners.py`, `staff.py`, `whitelabel.py`; `backend/engines/pdf_render.py`, `processing_workflow.py`; `backend/services/billing.py`, `storage.py`, `v3_email.py`; `backend/requirements-dev.txt`.

**Backend (modified, required):** the 19 real-content backend files listed in §12 (incl. `main.py`, `router.py`).

**Frontend (new, untracked):** `frontend/src/v3/**` (45 files), `PricingPage.jsx`, `SelfServiceSignup.jsx`, `OnboardingPage.jsx`, `css/lp2.css`, `css/pricing_page.css`.

**Frontend (modified, required):** the 11 real-content frontend files listed in §12 (incl. `App.js`), **excluding `frontend/App_.js`** (stray duplicate — PO decision).

**Database (untracked migrations):** the 10 migrations listed in §19.

**Tests:** the untracked D-series tests + the 6 modified test files (§23).

**Documentation:** the untracked D-series reports + architecture docs (§24).

**Verification:** D37 completion reports confirm the release set at D37 completion (unit 1039→1056, RLS 23→27, frontend 23→25, build OK, live 23/23).

---

## 14. Files That Must NOT Be Committed (Task 6)

| Group | Files | Reason |
|---|---|---|
| Secrets/security-sensitive | `probe_out5.txt` (JWT), all `.env*`, `backend/.env.bak`, `local_backups/env_backup/*`, `tools/carbon_data_factory/.env`, `admin/.env` | Credentials/tokens (values redacted) |
| Scratch/probe | `probe_out1…9.txt`, root `_*.txt`, `tmp_*.txt`, `tmp_*.log`, `current_project_structure.txt` | Debug/scratch (mostly gitignored already) |
| Generated output | `output/**`, `v3_schema.sql`, `backend/test_results.json`, root `test_results.json`/`_all.json`, `clean_emissions_output.json` | Generated artifacts |
| Large binaries/archives | `admin-dashboard.zip` (127 MB), `backend - backup.zip`, `backend/carbon_tally_backup*.sql` | Not for Git |
| Screenshots (unless PO approves) | `screenshots/**` (~96 files) | Verification evidence; recommend `.gitignore` |
| Agent-tooling symlinks | `.claude/skills/*`, `.windsurf/skills/*` (symlinks → external dir) | Broken for other clones |
| Local config | `supabase/config.toml` port changes, `.clineignore`/`.vercelignore` (unless approved) | Environment-local |
| Caches | `node_modules/`, `__pycache__/`, `.pytest_cache/` | Gitignored already |
| Copy/duplicate source | `* copy.*`, `App copy.*`, `main copy*.py`, `requirements copy.txt`, `config copy.toml`, `frontend/App_.js` | Superseded duplicates |

Full mapping in **Appendix D**.

---

## 15. Generated / Temporary Files (Task 11 support)

| Path | State | Recommendation |
|---|---|---|
| `output/json/*`, `output/reports/*`, `output/sql/*`, `output/seai_2025/*` | 13 tracked-deleted + 7 untracked | Do not commit; recommend `.gitignore` + future untrack commit |
| `v3_schema.sql`, `CarbonTally_DB_Schema_V3M2.sql` | untracked / tracked-mod | Schema snapshots — migrations are source of truth; archive |
| `backend/test_results.json`, root `test_results*.json` | untracked / tracked-mod | Do not commit; `.gitignore` |
| `clean_emissions_output.json` | tracked-mod | Generated; remove from tracking later |
| `probe_out1…9.txt` | untracked | Do not commit (one contains a JWT) |
| `admin-dashboard.zip` (127 MB) | untracked | Do not commit; `.gitignore` |
| `screenshots/**` (~96 files) | untracked | PO decision: archive or ignore |
| `supabase/snippets/Untitled query 673.sql` | untracked | Do not commit |

---

## 16. Backup / Legacy Files (Task 11 support)

| Path | State | Classification |
|---|---|---|
| `backend/main copy.py`, `backend/main copy 2.py` | tracked | Dead copies (debug prints of secret env presence) — ARCHIVE/DELETE later |
| `backend/main_v2.py` | tracked | Legacy entry — ARCHIVE |
| `backend/glossary copy.py`, `backend/requirements copy.txt` | tracked | Dead copies |
| `frontend/src/App copy.js`, `App copy.css`, `LandingPage copy.jsx`, `components/CarbonTallyDemo copy.jsx`, `FileUploadHero copy.jsx`, `frontend/App_.js` | tracked | Dead copies / stray duplicate |
| `supabase/config copy.toml` | tracked | Duplicate config |
| `backend - backup.zip`, `backend/carbon_tally_backup.sql`, `carbon_tally_backup_data.sql` | tracked/ignored | Backups — ARCHIVE/DELETE later |
| `database/rc2/00000000000000_init_schema.sql` | untracked | **DIVERGENT duplicate** of `supabase/migrations/…init_schema.sql` (diff: 265 insertions / 2,281 deletions) — do NOT commit; PO decision on removal |
| `prisma/`, `prisma.config.ts`, `seed.ts`, `seed.config.ts` | untracked | Abandoned Snaplet/Prisma experiment (no Prisma imports in backend) — PO decision |
| root `src/` (commands/providers), `carbon-tally-ui-demo/` | tracked | Legacy tooling — ARCHIVE |

---

## 17. Secret Scan Results (Task 7)

| Finding | Category | Location | Severity |
|---|---|---|---|
| LLM-provider API key (previously exposed) | API key | `tools/carbon_data_factory/deeepseek_api.txt` — **absent from working tree and HEAD**; **present in `2d23fb8`** | P0 (history) |
| JWT token | JWT | `probe_out5.txt` (untracked scratch) — 2 JWT-like tokens | P1 (local only) |
| Supabase publishable (anon) key + live project URL | Publishable key | `frontend/src/supabaseClient.js` fallback (tracked) | P2 |
| Env files with service-role/JWT/Resend credentials | Credentials | `.env*` on disk (root/backend/frontend/admin/tools), `backend/.env.bak`, `local_backups/env_backup/*` | P2 (gitignored; delete backups locally) |

No other embedded credential values were found in tracked files at HEAD (scan patterns: `sk-…`, `AKIA…`, `ghp_…`, private-key blocks, service-role assignments). Values are intentionally not reproduced.

---

## 18. Historical Secret Finding (Task 7/16)

- **File:** `tools/carbon_data_factory/deeepseek_api.txt`
- **Added:** commit `2d23fb8` "CarbonTally RC2 Final database baseline" (2026-08-06) — 35-byte blob starting with the `sk-` provider-key prefix.
- **Pushed:** `2d23fb8` was pushed 2026-08-06 14:11:20 UTC (tag `rc2-final`); the commit is an ancestor of `origin/main`.
- **Removed at HEAD:** commit `878bd0f` (2026-08-24), pushed the same day.
- **Revocation:** Product Owner confirms the key has been revoked (recorded assertion).
- **Current status:** file gone from working tree and HEAD; credential **still in pushed history at `2d23fb8`**.
- **Remediation:** deferred to a separate controlled task — see §32. No history rewrite is performed in this task.

---

## 19. Database Migration Inventory (Task 9)

Untracked D20–D37 migrations (all present in the working tree, in application order):

| # | Migration file | Covers |
|---|---|---|
| 1 | `20260821000000_d20_d15_active_consultant_grant.sql` | D15/D20 active-consultant grant |
| 2 | `20260821010000_d21_white_label_branding.sql` | D21 white-label branding |
| 3 | `20260821020000_d22_processing_work_assignment.sql` | D22 processing work assignment |
| 4 | `20260822000000_p9_rls_recursion_fix.sql` | p9 RLS recursion fix |
| 5 | `20260822010000_d27_d19_customer_lifecycle.sql` | D27/D19 customer lifecycle |
| 6 | `20260823000000_d32_private_documents_storage.sql` | D32 private documents storage |
| 7 | `20260823010000_d33_evidence_traceability.sql` | D33 evidence traceability |
| 8 | `20260824010000_d35_self_service_onboarding.sql` | D35 self-service onboarding |
| 9 | `20260824020000_d37_0_billing_security_and_configurable_subscription.sql` | D37-0 billing security + configurable subscription (incl. P0 RLS lockdown: `REVOKE INSERT/UPDATE/DELETE … FROM authenticated` on `usage_tracking`, `customer_subscriptions`, `consultant_billing`, `organizations`; `ENABLE ROW LEVEL SECURITY` on `billing_plans`, `billing_commercial_config`, `billing_credit_ledger`) |
| 10 | `20260824030000_d37_master_commercial_billing.sql` | D37 master commercial billing (subscriptions lifecycle, orders, storage usage, payment records, idempotency keys, plan v2 seeds, deny-by-default RLS + `service_role` grants) |

All are timestamp-ordered and strictly sequential (each timestamp strictly greater than the previous). The tracked migration series ends at `20260810050000_v3m6_entity_rls.sql`; the first untracked migration (`20260821000000`) continues after it with no gap conflict.

---

## 20. Migration Dependency Analysis (Task 9)

- **Order integrity:** filenames are chronologically ordered; applying them in order after `v3m6` is correct.
- **Cross-references:** the untracked migrations reference earlier timestamp families (`20260821` ×4, `20260822` ×2) in comments/context; no migration references a **missing** migration. No migration was found that depends on a migration not present in this set.
- **Completeness:** every D20–D37 phase that requires schema change has a migration (D20/D21/D22/p9/D27/D32/D33/D35/D37-0/D37-master). D23–D26, D28–D31, D29 have no dedicated migrations (app-only/RLS-doc-only work) — consistent with evidence in §8.
- **Obsolete/duplicate:** none found within the untracked set. The untracked `database/rc2/00000000000000_init_schema.sql` is a **divergent duplicate** of the tracked baseline (265 insertions / 2,281 deletions difference) — do not commit; it is not part of the release migration chain.
- **Untracked snippet:** `supabase/snippets/Untitled query 673.sql` — scratch SQL, not a migration, do not commit.

---

## 21. Backend Release Manifest (Task 5)

Required backend release files (new + modified) — see §13 for the full list. Highlights:
- **Composition root:** `backend/main.py` (modified, imports `api.router`).
- **API layer:** `backend/api/router.py` (modified — imports 22 `api.v3_*` routers), all untracked `api/v3_*.py` + `consultant_auth.py`, `consultant_branding.py`, `operations_auth.py`.
- **Services:** `backend/services/billing.py`, `storage.py`, `v3_email.py`.
- **Data/repos:** `backend/data/billing.py` + 19 other untracked data modules.
- **Domain:** `backend/domain/billing.py` + 8 other untracked domain modules.
- **Engines:** `backend/engines/pdf_render.py`, `processing_workflow.py`.
- **Auth/authorization:** modified `backend/auth.py`, `backend/api/dependencies.py`; untracked `operations_auth.py`.
- **Config:** `backend/requirements.txt` (modified), `backend/requirements-dev.txt` (new).

---

## 22. Frontend Release Manifest (Task 5)

Required frontend release files:
- **Entry:** `frontend/src/App.js` (modified, +171/−2 V3 wiring).
- **V3 feature tree:** `frontend/src/v3/**` (45 files) — `api.js`, `utils.js`, `v3.css`, `components/` (V3Layout, RoleRoute, StateViews, EvidenceRecordPanel), `customer/` (Dashboard, Documents, Emissions, Processing, Issues, Messaging, ExistingDataDiscovery, **BillingPage**), `ops/` (OperationsPage, OpsDashboard, queues, **CommercialTab**, SlaTab, StaffRolesTab, StaffRoster, ProcessingEntitiesTab, WorkItemWorkspace, EntityExtractionWorkspace, ExtractionPanel, ops.css), `admin/` (AdminPage + tabs), `consultant/` (ConsultantPage, ClientMessagingTab, WhiteLabelTab), `reports/` (ReportsPage, ReportDetailPage), `__tests__/api.test.js`.
- **Public pages:** `PricingPage.jsx`, `SelfServiceSignup.jsx`, `OnboardingPage.jsx`, `css/lp2.css`, `css/pricing_page.css`.
- **Modified supporting files:** `Login.js`, `MagicLink.jsx`, `AuthCallback.js`, `BetaSignup.jsx`, `LandingPage.jsx`, `AppHeader.jsx`, `AppFooter.jsx`, `supabaseClient.js`, `css/LandingPage.css`.
- **Excluded:** `frontend/App_.js` (stray duplicate — PO decision).

---

## 23. Test Release Manifest (Task 5)

- **New (untracked):** `backend/tests/unit/api/route_paths.py`, `test_billing_core.py`, `test_commercial_settings.py`, `test_composition_root.py`, `test_consultant_branding.py`, `test_d19_lifecycle.py`, `test_evidence_record.py`, `test_evidence_traceability.py`, `test_operations_auth.py`, `test_org_membership_resolution.py`, `test_reporting.py`, `test_scope_aware_authorization.py`, `test_self_service_onboarding.py`, `test_storage_security.py`, `test_v3_consultants.py`, `test_v3_customer_admin.py`, `test_v3_d23_extraction_ux.py`, `test_v3_discovery.py`, `test_v3_emissions.py`, `test_v3_entity_extraction.py`, `test_v3_exports_serialization.py`, `test_v3_legacy_reimplementation.py`, `test_v3_messaging.py`, `test_v3_new_capabilities.py`, `test_v3_notifications.py`, `test_v3_operations.py`, `test_v3_processing_workflow.py`, `test_v3_qc.py`, `test_v3_reports.py`, `test_v3_routes_exposed.py`, `test_v3_whitelabel.py`; `backend/tests/unit/domain/test_d19_domain.py`; `backend/tests/unit/engines/test_pdf_render.py`; `backend/tests/integration/test_consultants.py`, `test_customer_admin.py`, `test_report_versions.py`.
- **Modified (tracked):** `integration/conftest.py`, `integration/test_reports.py`, `integration/test_v3_rls_behavior.py`, `unit/api/fakes.py`, `unit/api/test_foundation.py`, `unit/api/test_v3_issues.py`.
- **Frontend:** `frontend/src/v3/__tests__/api.test.js` (untracked, part of v3 tree).
- **Legacy scripts in tests/ (NOT part of release):** `create_test_users.py`, `setup_test_data.py`, `setup_test_orgs.py`, `test_api.py`, `test_api_simple.py`, `test_auth_simple.py`, `test_failing_endpoints.py`, `test_all_endpoints.py`, `verify_setup.py`, `fix_imports.py`, `check_imports.py`, `export_postman.py`, `audit_code.py` — ARCHIVE later.
- **Live smoke scripts** are outside the repo (`/tmp/d37_live_smoke.py`, `/tmp/d370_live_smoke.py`).

---

## 24. Documentation Release Manifest (Task 12)

**Commit with the release (current authoritative documentation):**
- `docs/audit/cline/CARBONTALLY_V3_D27_*`, `D28_*`, `D30_*`, `D31_*`, `D32_*`, `D33_*`, `D33_1_*`, `D34_*`, `D35_*`, `D36_*`, `D37_0_*`, `D37_MASTER_*` reports; `CARBONTALLY_V3_PUBLIC_WEBSITE_AND_ARCHITECTURE_AUDIT.md`; `CARBONTALLY_V3_GIT_REPOSITORY_AUDIT_AND_RELEASE_READINESS_REPORT.md`; this report.
- `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` (untracked), `CARBONTALLY_V3_TERMINOLOGY_AND_DOMAIN_GLOSSARY.md`, `CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md`, `CARBONTALLY_V3_LEGACY_CONFORMITY_PLAN.md`, `CARBONTALLY_EVIDENCE_TRACEABILITY_AND_PROVENANCE_PRINCIPLES.md`, `CARBONTALLY_BLOG_CMS_DECISIONS.md` (untracked).
- `docs/Pricing/*` (5 untracked commercial specs), `docs/RECONSTRUCTED_TASK_HISTORY.md`, `docs/cline/prompts/CarbonTally_V3_Service_Catalogue_and_Evidence_Traceability_Cline_Brief.md`.

**Historical / not part of this release commit (archive later):** `docs/Final/*`, `docs/Final_Kimi/*`, `docs/architecture/DB_Migration/*`, `docs/architecture/UI/*`, older `docs/cline/*`, `docs/Todos.md`, `docs/featurellist.md`, `docs/CarbonTally Complete Customer Feature List.md`, `docs/styles/*`, `docs/sample_bills/*`.

**Conflict note (Task 18):** the untracked architecture/audit docs describe the D20–D37 state; the D37-0/D37 completion reports' test counts (unit 1039→1056, RLS 23→27) are historical records. If any doc conflicts with current code, the current implementation is authoritative; no conflicts requiring action were found in this audit beyond the known "FUTURE" gaps already documented in the D37 report (e.g., branded-PDF rendering).

---

## 25. Configuration Release Manifest (Task 5/D)

| Item | Status | Recommendation |
|---|---|---|
| `backend/requirements.txt` | modified (CRLF) | Commit with backend (after EOL normalization) |
| `backend/requirements-dev.txt` | untracked | Commit with backend |
| `frontend/package.json`, `frontend/public/*` | tracked, unchanged | No change required |
| `supabase/config.toml` | modified (port renumber) | **EXCLUDE from release** (local env change) or separate config commit — PO decision |
| `.gitignore` | modified (real content, CRLF) | PO decision: commit updated ignore rules with release or separately; ensure recommended additions (§26) are included |
| `vercel.json`, `.vercelignore`, `.clineignore`, `runtime.txt` | modified (mostly EOL) | EOL-only → excluded; real-content `.clineignore`/`.vercelignore` → PO decision |
| Root `requirements.txt` | modified (CRLF; contains invalid `=>` syntax) | Do not commit; ARCHIVE later (backend requirements are authoritative) |

---

## 26. .gitignore Assessment (Task 10)

Current `.gitignore` (working-tree version) already excludes: `__pycache__`, `node_modules`, `.env*`, `build/dist`, `*.log`, `backups/`, `local_backups/`, `.tmp_pgdata/`, root `_*.py`/`_*.txt`, `admin-dashboard/`, `.local-demo-credentials.md`, `current_project_structure.txt`.

**Verified good:** all `.env*` files (root/backend/frontend/admin/tools, incl. `backend/.env.bak`, `local_backups/env_backup/*`) are untracked and gitignored.

**Recommended additions (NOT applied in this task):**
- `*.zip` / `admin-dashboard.zip`
- `probe_out*.txt`
- `screenshots/`
- `output/`
- `backend/test_results.json`, root `test_results*.json`
- `supabase/snippets/Untitled query *.sql`
- `database/rc2/` (divergent baseline duplicate)
- `backend/carbon_tally_backup*.sql` (already partially covered)

---

## 27. Public Publication Risk Assessment (Task 11)

| Risk | Files | Verdict |
|---|---|---|
| Credentials published | `.env*`, `env_backup/`, `probe_out5.txt` | Must not be committed (gitignored / excluded) |
| Customer/PDB dumps | none found in working tree; `backups/*.dump` gitignored | Low |
| Large binaries | `admin-dashboard.zip` (127 MB), `backend - backup.zip`, `screenshots/*` | Must not be committed |
| Internal tooling | `tools/`, `demodatagen/` (internal benchmarks/seed generators) | PO decision; safe to commit if intended as project tooling |
| Prior public-website audit findings | sensitive claims content in reports | Reports are project documentation; commit with docs (PO approval) |
| The exposed key in history | `2d23fb8` | History remediation (§32); revocation already done |

---

## 28. Atomic vs Multi-Commit Recommendation (Task 8)

**Recommendation: ONE ATOMIC RELEASE COMMIT is the safest representation** of the D20–D37 release.

Evidence for atomicity:
1. `backend/api/router.py` (tracked, modified) imports 22 currently-untracked `api.v3_*` modules; `backend/main.py` imports `api.router`. A commit of only tracked files leaves the backend non-importable.
2. `frontend/src/App.js` (tracked, modified) imports currently-untracked `./v3/*`, `PricingPage`, `SelfServiceSignup`, `OnboardingPage`. A tracked-only frontend commit breaks the build.
3. Migrations D20→D37 must be applied in order for the backend to function (e.g., `billing_*` tables from D37-0 before D37-master uses them).
4. Tests reference the new modules and migrations; docs describe the release state.

**If the Product Owner prefers logical commit separation, the ONLY safe variant is a strictly ordered sequence that is pushed together as one unit (never pushed partially):**
1. Migrations → 2. Backend → 3. Frontend → 4. Tests → 5. Documentation.
Each intermediate commit would be broken if *pushed* alone, but is acceptable if the sequence lands before any push (local-only intermediate states). **Risk of partial commits:** an uncommitted backend with committed migrations, or committed backend without the new frontend, recreates the current split-brain state or worse.

**Decision needed (PO):** one atomic commit (`feat: D20–D37 V3 commercial release`) vs. the ordered 5-commit sequence pushed together. This report recommends the single atomic commit for maximum safety and reviewability.

---

## 29. Exact Future Staging Plan (Task 15)

This plan is for the NEXT authorized task. Nothing here is executed now.

- **Phase A — Safety verification:** confirm PO backup exists; `git rev-parse HEAD` still `878bd0f`; confirm `git status --short` matches this report's baseline (582/151/186).
- **Phase B — EOL normalization (PO-approved):** add `.gitattributes` (`* text=auto eol=lf` with binary exceptions for PNG/GIF/PDF/zip) in a preparation step; run `git add --renormalize` scoped to the release file set so the 19 mixed + any EOL-only staged files commit as LF. Alternatively, exclude EOL-only files entirely from the commit.
- **Phase C — Stage migrations:** `supabase/migrations/20260821000000…20260824030000` (10 files). Do NOT stage `database/rc2/…init_schema.sql` or `supabase/snippets/*`.
- **Phase D — Stage backend:** all untracked `backend/api|data|domain|engines|services` release files + the 19 modified backend files + `backend/requirements-dev.txt` + `backend/requirements.txt` (normalized). Exclude `main copy*`, `glossary copy.py`, `main_v2.py`, `backend/test_results.json`, `carbon_tally_backup*`.
- **Phase E — Stage frontend:** `frontend/src/v3/**`, `PricingPage.jsx`, `SelfServiceSignup.jsx`, `OnboardingPage.jsx`, `css/lp2.css`, `css/pricing_page.css`, and the modified frontend files (normalized). Exclude `frontend/App_.js` pending PO decision.
- **Phase F — Stage tests:** the untracked D-series tests + the 6 modified test files.
- **Phase G — Stage documentation:** the §24 doc set.
- **Phase H — Stage approved configuration:** `.gitignore` (with §26 additions) only if PO approves; do NOT stage `supabase/config.toml` unless PO explicitly approves the port changes.
- **Phase I — Verify staged diff:** `git diff --cached --stat`; confirm no `output/`, `probe_*`, `*.zip`, `.env*`, `screenshots/`, agent-skill symlinks, or `database/rc2/` appear; confirm no CRLF entries remain for staged text files.
- **Phase J — Run tests/build:** backend unit + RLS suites (separate pytest processes per prior reports), frontend `npm test`, `npm run build`; confirm the D37 baseline counts (unit 1056, RLS 27, frontend 25, build OK) or record deltas.
- **Phase K — Commit:** per §28 (atomic or ordered sequence) with a descriptive message.
- **Phase L — Push:** `git push origin main` (fast-forward) only after PO sign-off.
- **Phase M — Tag:** propose `v3.0-d37` (PO approval).

---

## 30. Exact Future Commit Plan (Task 15)

**Preferred (recommended): ONE atomic commit**
- Message: `feat: D20-D37 V3 commercial release (billing, processing, lifecycle, onboarding, evidence, storage)`
- Contents: §§29 Phase C–H union (migrations + backend + frontend + tests + docs + approved config).

**Alternative (if PO requires logical separation, pushed together):**
1. `feat(database): D20–D37 migrations (consultants, lifecycle, storage, evidence, onboarding, billing)` — Phase C.
2. `feat(backend): V3 services, billing, processing workflow, auth` — Phase D.
3. `feat(frontend): V3 workspace, onboarding, pricing, billing UI` — Phase E.
4. `test(backend): D-series unit/integration/RLS suites` — Phase F.
5. `docs: D20–D37 reports and architecture updates` — Phase G (+ this report).

**Commit hygiene rules:** no unrelated files in any commit; no generated artifacts; no secrets; EOL-normalized; `--no-verify` NOT used (run pre-commit checks).

---

## 31. Exact Future Push Plan (Task 15)

- Push **only after** PO approval of the staged diff and after tests/build pass.
- `git push origin main` (fast-forward; current remote is `878bd0f`, so the release commits append cleanly).
- **Never** force-push (history remediation is a separate task with its own force-push approval).
- After push, optionally create tag `v3.0-d37` and push the tag.
- Verify with `git fetch origin && git rev-list --left-right --count origin/main...main` (= `0 0`).

---

## 32. Separate Git History Remediation Plan (Task 16)

**Context:** the exposed DeepSeek key is revoked (PO assertion) and a full backup exists. History is NOT rewritten in this task.

- **Affected path:** `tools/carbon_data_factory/deeepseek_api.txt`
- **Affected reachable commits:** `2d23fb8` (pushed; ancestor of `origin/main`); local checkpoint-only commits `5f4c361`/`4ce9368` (refs/cline/checkpoints/*, not ancestors of HEAD) also reference the path.
- **Removal scope:** only the file needs removal; no unrelated history should be touched.
- **Strategy (recommended):**
  1. Confirm key revocation at the provider (done per PO).
  2. From a **fresh clone** (or after creating a full bare-clone backup), run:
     `git filter-repo --path tools/carbon_data_factory/deeepseek_api.txt --invert-paths`
  3. Verify: `git log --all -- tools/carbon_data_factory/deeepseek_api.txt` → empty; scan the new history for the key prefix → no matches.
  4. Force-push the rewritten `main` to `origin` (this is the single authorized force-push).
  5. Update local refs and prune the old local checkpoint refs:
     `git for-each-ref refs/cline/checkpoints | xargs git update-ref -d` then `git reflog expire --expire=now --all && git gc --prune=now`.
  6. Notify anyone with clones to re-clone from the rewritten remote.
- **Force-push implications:** all SHAs change; GitHub PR refs/CI caches referencing old SHAs break; single-developer `main` → blast radius is low. Do this BEFORE pushing the D20–D37 release (or accept that remediation after the release push rewrites release commits too).
- **Verification:** after remediation, confirm the working tree and release content are byte-identical (the rewrite only removes the one path).

---

## 33. Product Owner Decisions Required

1. **Commit model:** ONE atomic release commit (recommended) vs. the ordered 5-commit sequence pushed together (§28).
2. **EOL normalization:** approve `.gitattributes` (`* text=auto eol=lf`) + `git add --renormalize` for the release set (§29 Phase B).
3. **`supabase/config.toml`:** exclude the local port renumber from the release (recommended) or include in a separate config commit.
4. **`.gitignore`:** approve committing the updated `.gitignore` (with §26 additions: `*.zip`, `probe_out*.txt`, `screenshots/`, `output/`, `test_results*.json`, snippets, `database/rc2/`).
5. **Agent tooling:** exclude `.agents`/`.claude`/`.windsurf` changes from the release (recommended) or handle in a separate tooling commit.
6. **`frontend/App_.js`:** confirm removal (recommended) or retention.
7. **Screenshots:** ignore them (`screenshots/`) or commit as verification evidence.
8. **`database/rc2/00000000000000_init_schema.sql`:** confirm it is a stale divergent duplicate and exclude from the release.
9. **`admin/` app and `carbon-tally-ui-demo/`:** archive or retain (outside this release).
10. **History remediation timing:** approve running §32 BEFORE the release push (recommended) or defer.
11. **Release tag:** approve `v3.0-d37` after push.
12. **`CARBONTALLY_V3_PUBLIC_PRODUCT_PLATFORM_EXPERIENCE_STANDARD.md`:** NOT present in the repo — confirm whether the PO will supply it for the D38 baseline documentation (§13).

---

## 34. Release Readiness Assessment (Task 17)

| Check | Result |
|---|---|
| Backend entry wired to V3 modules | ✅ `main.py` → `api.router` → 22 `api.v3_*` routers (all present in working tree) |
| D37 billing slice present | ✅ `v3_billing.py` (300 lines, 10 routes), `v3_commercial.py` (822 lines, 24 routes), `services/billing.py` (832), `data/billing.py` (914), `domain/billing.py` (288) |
| D37-0 RLS lockdown present | ✅ `REVOKE INSERT/UPDATE/DELETE … FROM authenticated` + `ENABLE ROW LEVEL SECURITY` in migration 9 |
| Frontend billing UI present | ✅ `frontend/src/v3/customer/BillingPage.jsx`, `frontend/src/v3/ops/CommercialTab.jsx` |
| Migrations complete & ordered | ✅ 10 migrations, timestamp-ordered, no missing dependencies |
| Tests present | ✅ New D-series unit/integration suites + modified tracked tests |
| Documentation present | ✅ D27–D37 reports + architecture docs |
| D37 baseline verification record | ✅ Reported: unit 1056, RLS 27, frontend 25, build OK, live 23/23 (D37 report) — re-verify in commit task |
| Working tree is the complete release | ✅ No missing imports detected in the release set wiring |

**Health verdict:** the working tree contains the full known D37 completion state. The only risk is the uncommitted + EOL-contaminated packaging, addressed by §29.

---

## 35. Final Recommendation

1. The D20–D37 release is **preservable and complete**; it must be committed as a unit (atomic or ordered-then-pushed-together) per §28–§31.
2. **Do not push** until: key revocation is confirmed (done), §32 history-remediation decision is made, the §29 staging plan is executed with EOL normalization and strict excludes, and tests/build pass on the committed state.
3. **Do not commit** the do-not-commit set (§14, Appendix D).
4. The next authorized task should be the §29–§31 release commit+push task, followed separately by the §32 history-remediation task (if approved), then D38.

---

## 36. HARD STOP

- Verified: HEAD unchanged at `878bd0f9eb5d277510b9b911ecd1a10be0213bd1`.
- Verified: no application source changed, no migration changed, no RLS/configuration changed, no staging, no commit, no push, no history rewrite occurred during this task.
- The only repository addition is: `docs/audit/cline/CARBONTALLY_V3_D20_D37_GIT_RELEASE_PREPARATION_REPORT.md`.
- STOP. No commit/push/cleanup/history-rewrite/D38 implementation is performed.

---

## Appendix A — Complete File Classification Matrix

| Path / Group | State | Class | Evidence |
|---|---|---|---|
| `backend/api/v3_*.py` (24), `backend/data/*` (20), `backend/domain/*` (9), `backend/services/*` (3), `backend/engines/pdf_render.py`, `processing_workflow.py` | untracked | A — REQUIRED SOURCE | Imported by tracked `router.py`/`main.py` |
| `backend/api/router.py`, `main.py`, `auth.py`, `config.py`, `api/dependencies.py`, `api/contracts.py`, `api/issues.py`, `data/{__init__,emission_factors,emissions_logs,issues,organizations,reports}.py`, `domain/{calculation,issue,organization}.py`, `engines/{calculation,report_generation}.py`, `routes/organizations/members.py` | modified | A — REQUIRED SOURCE | Real content changes; release wiring |
| `frontend/src/v3/**` (45) | untracked | A — REQUIRED SOURCE | Imported by `App.js` |
| `PricingPage.jsx`, `SelfServiceSignup.jsx`, `OnboardingPage.jsx`, `css/lp2.css`, `css/pricing_page.css` | untracked | A — REQUIRED SOURCE | Imported by `App.js`/routes |
| `App.js`, `AuthCallback.js`, `BetaSignup.jsx`, `LandingPage.jsx`, `Login.js`, `MagicLink.jsx`, `AppFooter.jsx`, `AppHeader.jsx`, `css/LandingPage.css`, `supabaseClient.js` | modified | A — REQUIRED SOURCE (EOL-normalize 9 of them) | Real content; CRLF on 9 |
| `frontend/App_.js` | modified | N — UNKNOWN/PO | Not imported anywhere |
| `supabase/migrations/20260821*–20260824*` (10) | untracked | B — REQUIRED MIGRATION | D20–D37 schema history |
| `database/rc2/00000000000000_init_schema.sql` | untracked | K/N — DUPLICATE/PO | Diverges from tracked baseline (265+/2281−) |
| `backend/tests/unit/api/*` (new D-series, 31), `unit/domain/test_d19_domain.py`, `unit/engines/test_pdf_render.py`, `integration/test_consultants.py`, `test_customer_admin.py`, `test_report_versions.py` | untracked | C — REQUIRED TEST | D-series suites |
| 6 modified test files (conftest, test_reports, test_v3_rls_behavior, fakes, test_foundation, test_v3_issues) | modified | C — REQUIRED TEST | Real content |
| `backend/requirements-dev.txt` | untracked | D — REQUIRED CONFIG | Dev deps |
| `backend/requirements.txt` | modified (CRLF) | D — REQUIRED CONFIG | EOL-normalize |
| `supabase/config.toml` | modified | N — PO (exclude) | Local port renumber |
| `.gitignore` | modified (CRLF) | D/N — PO | Real content; 3 lines; approve inclusion |
| `docs/audit/cline/*D27–D37*`, this report, prior audit reports | untracked | E — REQUIRED DOCS | D-series evidence |
| `docs/architecture/CARBONTALLY_V3_*` (6), `docs/Pricing/*` (5), `docs/RECONSTRUCTED_TASK_HISTORY.md`, `docs/cline/prompts/*` | untracked | E — REQUIRED DOCS | Current architecture |
| `docs/cline/*` (modified 3), `docs/Final/*`, `docs/Final_Kimi/*`, `docs/architecture/{DB_Migration,UI}/*` | tracked | J — ARCHIVE | Historical |
| `output/**`, `v3_schema.sql`, `backend/test_results.json`, root `test_results*.json`, `clean_emissions_output.json` | mixed | H — GENERATED NOT REQUIRED | Generated artifacts |
| `probe_out1…9.txt` | untracked | I/M — TEMP/SECRET | `probe_out5.txt` contains a JWT |
| `admin-dashboard.zip`, `backend - backup.zip`, `backend/carbon_tally_backup*.sql` | untracked/tracked | K — BACKUP | Archives |
| `* copy.*`, `App copy.*`, `main copy*.py`, `requirements copy.txt`, `config copy.toml`, `main_v2.py`, `glossary copy.py`, `carbon-tally-ui-demo/`, root `src/`, `prisma/` experiment | tracked/untracked | J/K — LEGACY/DUPLICATE | Superseded |
| `screenshots/**` (~96) | untracked | F/N — ASSET/PO | Verification evidence |
| `.claude/skills/*`, `.windsurf/skills/*` (138 deleted tracked + 18 untracked symlinks), `.agents/skills/*` (69 modified) | mixed | N — PO | Agent tooling; symlinks → external dir |
| `supabase/snippets/Untitled query 673.sql` | untracked | I — TEMP | Scratch SQL |
| 534 EOL-only modified files | modified | L — EOL-ONLY NOISE | `--ignore-space-at-eol` empty diff |
| `.env*`, `backend/.env.bak`, `local_backups/env_backup/*`, `tools/carbon_data_factory/.env`, `admin/.env` | ignored/untracked | M — SECRET (local) | Gitignored; delete backups locally |
| `tools/carbon_data_factory/deeepseek_api.txt` | removed at HEAD | M — SECRET (history) | Present in `2d23fb8` |

---

## Appendix B — D20–D37 Development History Matrix

| Phase | Date (evidence) | Evidence files | Status |
|---|---|---|---|
| D15/D20 | 2026-08-21 | `20260821000000_d20_d15_active_consultant_grant.sql` | In release |
| D21 | 2026-08-21 | `20260821010000_d21_white_label_branding.sql`, `consultant_branding.py`, `test_consultant_branding.py` | In release |
| D22 | 2026-08-21 | `20260821020000_d22_processing_work_assignment.sql` | In release |
| p9 (RLS recursion fix) | 2026-08-22 | `20260822000000_p9_rls_recursion_fix.sql` | In release |
| D19/D27 | 2026-08-22 | `20260822010000_d27_d19_customer_lifecycle.sql`, `test_d19_lifecycle.py`, `test_d19_domain.py`, D27 reports | In release |
| D23 | 2026-08-22 (test evidence) | `test_v3_d23_extraction_ux.py` | In release (app-only) |
| D24 | 2026-08-22 | Architecture §24: `ProcessingEntitiesTab.jsx`, `EntityExtractionWorkspace.jsx` | In release (app-only) |
| D25 | 2026-08-22 | Architecture §40: issues/messaging/notifications; frontend tests | In release |
| D26 | 2026-08-22 | Architecture §41: scale hardening; bounded pagination | In release |
| D28 | 2026-08-22 | `CARBONTALLY_V3_D28_VISUAL_QA_REPORT.md` | In release (docs) |
| D29 | pre-D37 | `v3/api.js` comments `D29/F3`, `D29/F5` | Partial evidence (code comments) |
| D30/D31 | 2026-08-22/23 | `D30_REPORTING_*`, `D31_REPORTING_*` reports; `screenshots/d30_*`, `d31_*` | In release |
| D32 | 2026-08-23 | `20260823000000_d32_private_documents_storage.sql`, `test_storage_security.py`, D32 report | In release |
| D33 | 2026-08-23 | `20260823010000_d33_evidence_traceability.sql`, `test_evidence_*.py`, D33 report | In release |
| D33.1 | 2026-08-23 | `D33_1_EVIDENCE_PRECISION_REPORT.md`, `EvidenceRecordPanel.jsx` | In release |
| D34 | 2026-08-23 | `D34_PRODUCTION_CUSTOMER_JOURNEY_READINESS_REPORT.md`, `screenshots/d34_*` | In release |
| D35 | 2026-08-24 | `20260824010000_d35_self_service_onboarding.sql`, `test_self_service_onboarding.py`, `SelfServiceSignup.jsx`, `OnboardingPage.jsx` | In release |
| D36 | 2026-08-24 | `D36_BILLING_COMMERCIAL_ARCHITECTURE_AUDIT.md` | In release (docs) |
| D37-0 | 2026-08-24 | `20260824020000_d37_0_….sql`, `test_commercial_settings.py`, `v3_commercial.py`, `D37_0_…REPORT.md` | In release |
| D37-1…9 | 2026-08-24 | `20260824030000_d37_master_commercial_billing.sql`, `v3_billing.py`, `data/domain/services/billing.py`, `test_billing_core.py`, `BillingPage.jsx`, `CommercialTab.jsx`, `D37_MASTER_…REPORT.md` | In release (one master) |

Not evidenced as separate phases in this window: D0–D14, D16–D18 (legacy/pre-release); D37-1…9 individual sub-labels (master scope only).

---

## Appendix C — Required Release Manifest (REQUIRED TO COMMIT)

Directories/files to be staged in the future commit task (§29 Phase C–H):

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
- `backend/api/v3_*.py`, `consultant_auth.py`, `consultant_branding.py`, `operations_auth.py`
- `backend/data/*` (all untracked release modules), `backend/domain/*` (all untracked release modules), `backend/services/billing.py`, `storage.py`, `v3_email.py`, `backend/engines/pdf_render.py`, `processing_workflow.py`
- `backend/main.py`, `backend/api/router.py`, `backend/auth.py`, `backend/config.py`, `backend/api/{contracts,dependencies,issues}.py`, `backend/data/{__init__,emission_factors,emissions_logs,issues,organizations,reports}.py`, `backend/domain/{calculation,issue,organization}.py`, `backend/engines/{calculation,report_generation}.py`, `backend/routes/organizations/members.py`
- `backend/requirements.txt` (normalized), `backend/requirements-dev.txt`
- `frontend/src/v3/**` (45 files), `PricingPage.jsx`, `SelfServiceSignup.jsx`, `OnboardingPage.jsx`, `css/lp2.css`, `css/pricing_page.css`
- `frontend/src/App.js`, `AuthCallback.js`, `BetaSignup.jsx`, `LandingPage.jsx`, `Login.js`, `MagicLink.jsx`, `components/AppFooter.jsx`, `components/AppHeader.jsx`, `css/LandingPage.css`, `supabaseClient.js` (all EOL-normalized)
- All untracked D-series test files (§23) + the 6 modified test files
- Documentation set (§24): D27–D37 reports, architecture docs, pricing specs, task history, this report
- `.gitignore` (only if PO approves; with §26 additions)

---

## Appendix D — Do-Not-Commit Manifest

| Item | Reason |
|---|---|
| `probe_out1…9.txt` (esp. `probe_out5.txt` — JWT) | Scratch + secret |
| `.env*`, `backend/.env.bak`, `local_backups/env_backup/*`, `tools/carbon_data_factory/.env`, `admin/.env` | Credentials (gitignored; delete backups locally) |
| `output/**`, `v3_schema.sql`, `backend/test_results.json`, root `test_results*.json`, `clean_emissions_output.json` | Generated |
| `admin-dashboard.zip`, `backend - backup.zip`, `backend/carbon_tally_backup*.sql` | Archives/binaries |
| `screenshots/**` | Unless PO approves |
| `.claude/skills/*`, `.windsurf/skills/*` (symlinks), `.agents/skills/*` (unless PO approves tooling commit) | Agent tooling / external symlinks |
| `database/rc2/00000000000000_init_schema.sql` | Divergent duplicate baseline |
| `supabase/snippets/Untitled query 673.sql` | Scratch |
| `supabase/config.toml` (port changes) | Local env change (unless PO approves) |
| `* copy.*`, `App copy.*`, `main copy*.py`, `requirements copy.txt`, `config copy.toml`, `frontend/App_.js` | Superseded duplicates (PO approval to remove later) |
| `carbon-tally-ui-demo/`, root `src/`, `prisma/`, `prisma.config.ts`, `seed.ts`, `seed.config.ts` | Abandoned experiments (PO decision) |
| root `requirements.txt` (invalid `=>` syntax) | Stale; backend requirements authoritative |

---

## Appendix E — Security Findings

| Severity | Finding | Location | Status |
|---|---|---|---|
| P0 | Exposed LLM-provider API key (revoked) | `tools/carbon_data_factory/deeepseek_api.txt` at `2d23fb8` (pushed history) | History remediation (§32) |
| P1 | JWT tokens in untracked scratch file | `probe_out5.txt` | Delete locally; never commit |
| P2 | Supabase publishable key + live URL hard-coded | `frontend/src/supabaseClient.js` | Move to env (hygiene) |
| P2 | Env backups with credentials on disk | `backend/.env.bak`, `local_backups/env_backup/*` | Delete locally |
| P2 | Large untracked-but-unignored binaries | `admin-dashboard.zip`, `screenshots/`, `output/` | Add `.gitignore` entries |
| P3 | Cline checkpoint refs retain stale objects locally | `refs/cline/checkpoints/*` (146) | Local prune later |

---

## Appendix F — Unknown / Decision-Required Items

1. Commit model: atomic vs ordered multi-commit (§28).
2. EOL normalization approval (§29 Phase B).
3. `supabase/config.toml` inclusion.
4. `.gitignore` inclusion + additions.
5. Agent-tooling changes handling.
6. `frontend/App_.js` disposition.
7. Screenshots disposition.
8. `database/rc2/…init_schema.sql` disposition.
9. `admin/` app and `carbon-tally-ui-demo/` disposition.
10. History-remediation timing (before vs after release push).
11. Release tag name.
12. `CARBONTALLY_V3_PUBLIC_PRODUCT_PLATFORM_EXPERIENCE_STANDARD.md` — NOT in repository; PO to supply for D38 baseline docs.

---

*End of report. This is an audit + preparation artifact only; no Git or application state was mutated except the creation of this report.*
