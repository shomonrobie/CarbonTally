# CarbonTally V3 — D20–D37 Release Staging Report

**Task type:** CONTROLLED GIT STAGING + VERIFICATION ONLY.
**Executed:** Explicit-path staging of the D20–D37 release manifest; EOL normalization of the 14 manifest "mixed" files (the only authorized source modification). **No commit, no push, no history rewrite, no deletions, no restore, no reset, no `.gitignore` change, no migration execution, no database change.**
**Date:** 2026-08-25

---

## 1. Executive Summary

The D20–D37 release has been staged **exactly per Appendix C of the preparation report**:

- **220 files staged** (184 added, 36 modified, 0 deleted): 10 migrations, 60 new backend source modules, 20 modified backend files, 35 new backend test files, 6 modified backend test files, 45 V3 frontend files, 5 new frontend pages/styles, 10 modified frontend files, 29 documentation files.
- **EOL/CRLF handling:** the 14 manifest "mixed" files were normalized CRLF→LF (verified content-identical via EOL-insensitive diff). **0 CR bytes exist in the staged content.** The 534 EOL-only files were **not staged** and left untouched.
- **Secret scan of the staged diff: 0 matches.** `probe_out5.txt`, `.env*`, `deeepseek_api.txt`, screenshots, zips, generated output, and agent-tooling files are **not staged** (verified).
- **Python syntax verification:** all 119 staged `.py` files parse cleanly (read-only AST check). Frontend build and pytest suites were **not** executed (build would generate files; suites risk DB/env mutation per known conftest constraints) — deferred to the commit task.
- **One external-environment change detected during the task:** root `package.json`/`package-lock.json` were modified by an outside process (added `n8n-nodes-pollinations` dependency at 17:12). **Not staged** (not in the manifest); flagged for PO review/revert.
- **Required-but-not-staged: NONE. Unexpected-staged: NONE.**
- **HARD STOP maintained:** HEAD remains `878bd0f`; no commit/push/history-rewrite occurred.

---

## 2. Safety Preconditions

| Precondition | Status |
|---|---|
| HEAD = `878bd0f` | ✅ Verified at start and end |
| origin/main = `878bd0f` | ✅ Verified |
| Branch = `main` | ✅ Verified |
| Ahead/behind = 0/0 | ✅ Verified |
| Existing staged changes before task | ✅ None (`git diff --cached` empty) |
| Stash | ✅ Empty |
| Submodules / LFS | ✅ None / not installed |
| Prep report read as authoritative scope | ✅ `docs/audit/cline/CARBONTALLY_V3_D20_D37_GIT_RELEASE_PREPARATION_REPORT.md` (Appendix C/D, §29–§32) |
| PO authorizations (revoked key, backup) | ✅ Recorded assertions |

No contradiction was found between the preparation report and the repository state.

---

## 3. HEAD Verification

`git rev-parse HEAD` = `878bd0f9eb5d277510b9b911ecd1a10be0213bd1` — "Remove exposed API key file" (2026-08-24). Unchanged throughout the task.

---

## 4. Remote Verification

`git rev-parse origin/main` = `878bd0f9eb5d277510b9b911ecd1a10be0213bd1`; `git rev-list --left-right --count origin/main...main` = `0 0`. Remote untouched.

---

## 5. Initial Working Tree State

Baseline at task start (matches the preparation report):

| Metric | Count |
|---|---|
| Modified | 582 |
| Deleted | 151 |
| Untracked | 187 |
| Staged | 0 |

During the task an external process additionally modified root `package.json` and `package-lock.json` (mtime 17:12; added `n8n-nodes-pollinations`). These are **not staged** and are reported in §23/§24.

---

## 6. Release Manifest Used

Scope source: preparation report **Appendix C** (Required Release Manifest) + §24 documentation list + §23 test list. Exact staged groups:

1. Migrations (10) — the D20/D21/D22/p9/D27/D32/D33/D35/D37-0/D37-master SQL files.
2. Backend new (60) — `backend/api/v3_*.py` (21) + `consultant_auth/branding` + `operations_auth`; `backend/data/*` (20); `backend/domain/*` (9); `backend/engines/pdf_render.py` + `processing_workflow.py`; `backend/services/billing.py` + `storage.py` + `v3_email.py`; `backend/requirements-dev.txt`.
3. Backend modified (20) — `main.py`, `api/{router,contracts,dependencies,issues}.py`, `auth.py`, `config.py`, `data/{__init__,emission_factors,emissions_logs,issues,organizations,reports}.py`, `domain/{calculation,issue,organization}.py`, `engines/{calculation,report_generation}.py`, `requirements.txt`, `routes/organizations/members.py`.
4. Frontend new (50) — `frontend/src/v3/**` (45) + `PricingPage.jsx`, `SelfServiceSignup.jsx`, `OnboardingPage.jsx`, `css/lp2.css`, `css/pricing_page.css`.
5. Frontend modified (10) — `App.js`, `AuthCallback.js`, `BetaSignup.jsx`, `LandingPage.jsx`, `Login.js`, `MagicLink.jsx`, `components/AppFooter.jsx`, `components/AppHeader.jsx`, `css/LandingPage.css`, `supabaseClient.js`.
6. Tests (41) — 35 new (unit/api incl. billing/commercial/evidence/onboarding/storage suites, unit/domain, unit/engines, integration) + 6 modified (`conftest.py`, `test_reports.py`, `test_v3_rls_behavior.py`, `fakes.py`, `test_foundation.py`, `test_v3_issues.py`).
7. Documentation (29) — D27–D37 audit reports, the two prior audit reports, the preparation report, 6 architecture docs, 5 pricing specs, `RECONSTRUCTED_TASK_HISTORY.md`, the service-catalogue brief.

NOT staged (Appendix D + PO-pending items): `.gitignore`, `supabase/config.toml`, root `requirements.txt`, `frontend/App_.js`, `database/rc2/…init_schema.sql`, screenshots, output/, zips, probe files, env files, agent-tooling changes, `package.json`/`package-lock.json`.

---

## 7. Files Staged

**220 files staged** — see Appendix A (complete list) and §17 (statistics). All 220 are exactly within the four allowed release roots: `backend/`, `frontend/src/`, `supabase/migrations/`, `docs/`.

---

## 8. Files Intentionally Not Staged

See Appendix B (complete list). Highlights: 534 EOL-only modified files; 9 non-manifest real-content modified files (`.gitignore`, `CarbonTally_DB_Schema_V3M2.sql`, `docs/cline/Architecture_Review.md`, `docs/cline/Backend_Architecture_v2.1.md`, `docs/Final/*`, `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md`, `frontend/App_.js`, root `requirements.txt`, `supabase/config.toml`); 151 deleted files (agent-skill + output artifacts — deletions not part of this release); 187+ untracked non-manifest files (screenshots, generated output, probes, env files, agent symlinks, archives); the two externally-modified package files.

---

## 9. EOL-Only Files Excluded

- **534 files** whose working-tree content is identical to HEAD except CRLF↔LF were **not staged and not touched** (verified via `git diff --ignore-space-at-eol` = empty for them).
- **0 CR bytes** exist in the staged diff (`git diff --cached | grep -c $'\r'` = 0), so the staged release is clean-LF even for the untracked new files.

---

## 10. Mixed EOL/Content Files Handled

14 of the 19 mixed files (real content + CRLF) are in the release manifest and were EOL-normalized **CRLF→LF** with `sed -i 's/\r$//'` (the single authorized source modification):

`backend/auth.py`, `backend/config.py`, `backend/main.py`, `backend/requirements.txt`, `backend/routes/organizations/members.py`, `frontend/src/AuthCallback.js`, `frontend/src/BetaSignup.jsx`, `frontend/src/LandingPage.jsx`, `frontend/src/Login.js`, `frontend/src/MagicLink.jsx`, `frontend/src/components/AppFooter.jsx`, `frontend/src/components/AppHeader.jsx`, `frontend/src/css/LandingPage.css`, `frontend/src/supabaseClient.js`.

- Content preservation verified: EOL-insensitive diff unchanged after normalization; HEAD EOL is LF for all 14, so staged diffs now show **only** the meaningful D20–D37 content (e.g., `backend/main.py` raw diff dropped from 394/362 to 32 insertions).
- All 14 are fully staged (0 unstaged remainder).

The other 5 mixed files are **not** in the manifest and were left untouched: `.gitignore`, `CarbonTally_DB_Schema_V3M2.sql`, `docs/cline/Architecture_Review.md`, `docs/cline/Backend_Architecture_v2.1.md`, root `requirements.txt`.

---

## 11. Backend Staging Verification

- All 60 new backend source modules staged; all 20 modified backend files staged (with the 5 mixed ones normalized).
- **Entry-point wiring verified:** `backend/api/router.py` imports all 21 staged `api.v3_*` routers + `operations_auth`/`consultant_auth`; `backend/main.py` imports `api.router`; `api/v3_billing.py`/`v3_commercial.py` import `services.billing`, `data.billing`, `domain.billing` — all staged.
- D37 billing slice present: `v3_billing.py` (300 lines), `v3_commercial.py` (822), `services/billing.py` (832), `data/billing.py` (914), `domain/billing.py` (288).
- Python AST parse of all 119 staged `.py` files: **0 syntax errors**.

---

## 12. Frontend Staging Verification

- All 45 `frontend/src/v3/**` files staged (api.js, V3Layout, RoleRoute, StateViews, EvidenceRecordPanel, customer/ops/admin/consultant/reports pages, BillingPage, CommercialTab, __tests__/api.test.js).
- 5 new public pages/styles staged (`PricingPage`, `SelfServiceSignup`, `OnboardingPage`, `lp2.css`, `pricing_page.css`).
- All 10 modified frontend files staged; `App.js` wiring verified to reference only staged `./v3/*`, `PricingPage`, `SelfServiceSignup`, `OnboardingPage` modules.
- `frontend/App_.js` excluded (stray duplicate, PO decision).

---

## 13. Migration Staging Verification

All 10 D20–D37 migrations staged, in order, no duplicates, no unrelated migrations:

1. `20260821000000_d20_d15_active_consultant_grant.sql`
2. `20260821010000_d21_white_label_branding.sql`
3. `20260821020000_d22_processing_work_assignment.sql`
4. `20260822000000_p9_rls_recursion_fix.sql`
5. `20260822010000_d27_d19_customer_lifecycle.sql`
6. `20260823000000_d32_private_documents_storage.sql`
7. `20260823010000_d33_evidence_traceability.sql`
8. `20260824010000_d35_self_service_onboarding.sql`
9. `20260824020000_d37_0_billing_security_and_configurable_subscription.sql`
10. `20260824030000_d37_master_commercial_billing.sql`

The D37-0 RLS lockdown statements are present in migration 9 (verified earlier: `REVOKE INSERT/UPDATE/DELETE … FROM authenticated`, `ENABLE ROW LEVEL SECURITY`). No migration was executed. `database/rc2/…init_schema.sql` and `supabase/snippets/Untitled query 673.sql` are NOT staged.

---

## 14. Test Staging Verification

- 35 new test files staged (unit/api: billing_core, commercial_settings, d19_lifecycle, evidence_*, operations_auth, self_service_onboarding, storage_security, scope_aware_authorization, v3_* suites, route_paths; unit/domain: d19_domain; unit/engines: pdf_render; integration: consultants, customer_admin, report_versions).
- 6 modified tracked test files staged (conftest, test_reports, test_v3_rls_behavior, fakes, test_foundation, test_v3_issues).
- No temporary test output, debug logs, probe results, or scratch files staged.

---

## 15. Documentation Staging Verification

29 documentation files staged — exactly the preparation-report §24 list:
- 16 `docs/audit/cline/` reports (D27 inventory, D27/D19 final, D28, D30, D31, D32, D33, D33.1, D34, D35, D36, D37-0, D37-master, public-website audit, git-repo audit, D20–D37 preparation report).
- 6 `docs/architecture/` docs (Actor Workspace Access Model, Terminology & Domain Glossary, Backend Consolidation Plan, Legacy Conformity Plan, Evidence Traceability Principles, Blog CMS Decisions).
- 5 `docs/Pricing/` specs, `docs/RECONSTRUCTED_TASK_HISTORY.md`, `docs/cline/prompts/…Service_Catalogue…Brief.md`.

Not staged: the other untracked `docs/audit/cline/*` (LOCAL_SUPABASE_SETUP_AUDIT, ARCHITECTURE_CONFORMITY_GATE, FRONTEND_RUN_REPORT, PHASE_4–8, RESUMPTION_AFTER_POWER_LOSS, Legacy_Capability, Local_Codebase_UX, New_Capabilities, Phase1_Backend_Consolidation, Processing_Workflow) — not in the manifest; candidates for a later docs/archive task. The Product Platform Experience Standard (`CARBONTALLY_V3_PUBLIC_PRODUCT_PLATFORM_EXPERIENCE_STANDARD.md`) is not in the repository and is a D38 item.

---

## 16. Secret Scan Result

- `git diff --cached` scanned for: `sk-…` provider keys, `AKIA…`, `ghp_…`, private-key blocks, JWT (`eyJ…`). **Matches: 0.**
- `probe_out5.txt` staged: **0** (file excluded).
- `tools/carbon_data_factory/deeepseek_api.txt` staged: **0** (remains deleted at HEAD).
- Any `.env*` staged: **0**.
- Any `.zip`/screenshots/`output/`/probe file staged: **0**.
- `.gitignore`, `supabase/config.toml`, `frontend/App_.js` staged: **0**.
- No credential values reproduced in this report.

---

## 17. Staged Diff Statistics

```
220 files changed, 66929 insertions(+), 1052 deletions(-)
```
- Added (A): 184 · Modified (M): 36 · Deleted (D): 0
- 0 CR bytes in staged content; all staged text is LF.

---

## 18. Complete Staged File Inventory

See **Appendix A** for the full `git diff --cached --name-status` listing (220 entries). Highlights: 10 migrations; 60 new backend modules; 20 modified backend files; 45 V3 frontend files; 5 new frontend pages/styles; 10 modified frontend files; 41 test files; 29 documentation files.

---

## 19. Required-but-Missing Files

**NONE.** Every file in Appendix C of the preparation report is staged. Spot-checked explicitly: `frontend/src/v3/api.js`, `frontend/src/v3/customer/BillingPage.jsx`, `frontend/src/v3/ops/CommercialTab.jsx`, `backend/services/billing.py`, `backend/api/v3_billing.py`, `supabase/migrations/20260824030000_d37_master_commercial_billing.sql` — all staged.

---

## 20. Unexpected Staged Files

**NONE.** All 220 staged files belong to the four allowed release roots and match the manifest. No temp/backup/duplicate/generated/secrets were staged.

---

## 21. Build/Test Verification

- **Python AST parse:** 119/119 staged `.py` files parse cleanly (read-only, no bytecode written).
- **Frontend build:** NOT executed — `npm run build` would write generated files to `frontend/build/` (a side-effect the task prohibits). Deferred to the commit task.
- **pytest suites:** NOT executed — known conftest/env-mutation constraints (unit+RLS must run in separate processes; integration tests touch Supabase/local DB state). Deferred to the commit task, where the D37 baseline (unit 1056, RLS 27, frontend 25, build OK) should be re-verified.
- **Static import wiring:** verified that all modules imported by `router.py`, `main.py`, `v3_billing.py`, `v3_commercial.py`, and `App.js` are present in the staged set.

---

## 22. Release Completeness Check

| Check | Result |
|---|---|
| REQUIRED AND STAGED | 220/220 |
| REQUIRED BUT NOT STAGED | **0** |
| STAGED BUT NOT REQUIRED | **0** |
| Migrations complete & ordered | ✅ 10/10 |
| D37 billing slice complete | ✅ backend + frontend + migration + tests |
| Secrets staged | 0 |
| CRLF content staged | 0 |

---

## 23. Remaining Risks

1. **External `package.json`/`package-lock.json` modification** (added `n8n-nodes-pollinations` at 17:12 during this task, by an outside process). Not staged. PO must decide whether to revert these files before the commit task.
2. **Unstaged working-tree residue** (548 modified + 187 untracked) remains by design (EOL-only + non-manifest + agent tooling + generated). The commit task must not use `git add -A`/`git add -u`.
3. **History remediation** of the DeepSeek key in `2d23fb8` remains a separate task (§27).
4. **Full test/build verification deferred** to the commit task.
5. The 14 normalized files now have LF working-tree content (a deliberate, authorized change); if the PO rejects EOL normalization, the staging would need rework.

---

## 24. Product Owner Decisions

1. **Approve the staged 220-file release set** (or request changes before commit).
2. **`package.json`/`package-lock.json`:** revert the external `n8n-nodes-pollinations` change (recommended) or retain.
3. **Commit model:** one atomic commit (recommended) vs the ordered 5-commit sequence pushed together.
4. **`.gitignore` / `supabase/config.toml`:** still pending — decide whether to include in a later config commit (not in this release).
5. **History remediation timing** (§27): before or after the release push.
6. **Release tag** (`v3.0-d37`) after push.

---

## 25. Exact Recommended Commit Command (future task, NOT executed)

```
git commit -m "feat: D20-D37 V3 commercial release (billing, processing, lifecycle, onboarding, evidence, storage)"
```
If the ordered multi-commit variant is chosen, use the 5-commit plan from the preparation report §30. **Do not use `git add -A`/`-u` in any follow-up.**

---

## 26. Exact Recommended Push Command (future task, NOT executed)

```
git push origin main
```
Fast-forward from `878bd0f`. No force-push. After PO approval of the committed state and test/build results. Optionally then `git tag v3.0-d37 && git push origin v3.0-d37`.

---

## 27. Historical Secret Remediation Reminder

The revoked DeepSeek key still exists in pushed history at commit `2d23fb8`. History remediation (`git filter-repo --path tools/carbon_data_factory/deeepseek_api.txt --invert-paths` + force-push on a fresh clone) is a **separate authorized future task**. Nothing in this staging task affects or performs that remediation.

---

## 28. Final Release Readiness

The staged release is **internally complete and reviewable**: 220 files, clean-LF, no secrets, no EOL noise, no unexpected files, migrations ordered, backend/frontend/tests/docs all wired. The commit/push decision remains with the PO after reviewing `git diff --cached`.

---

## 29. HARD STOP

Verified at completion:
- HEAD unchanged: `878bd0f9eb5d277510b9b911ecd1a10be0213bd1`.
- origin/main unchanged; no commit (70 total), no push, no history rewrite, no migration executed, no database state change.
- Staged: only the intended 220 release files. `probe_out5.txt` NOT staged. `deeepseek_api.txt` remains deleted. No secret staged.
- The only source modification was the authorized EOL normalization of the 14 mixed release files.
- This staging report is **left untracked** (not part of the D20–D37 release manifest).
- STOP. No commit, push, cleanup, history rewrite, or D38 implementation performed.

---

## Appendix A — Complete Staged File List

Generated directly from `git diff --cached --name-status` at report time (see the appended listing below this section).

---

## Appendix B — Complete Excluded File List (summary)

- **534 EOL-only modified files** (unstaged; content identical to HEAD apart from CRLF).
- **Real-content modified files NOT staged (9):** `.gitignore`, `CarbonTally_DB_Schema_V3M2.sql`, `docs/Final/CarbonTally - Final Database Schema Analysis & Recommendation.md`, `docs/architecture/CarbonTally_V3_Architectural_Decisions_Register.md`, `docs/cline/Architecture_Review.md`, `docs/cline/Backend_Architecture_v2.1.md`, `frontend/App_.js`, `requirements.txt`, `supabase/config.toml`.
- **Externally modified (2):** `package.json`, `package-lock.json` (n8n dependency added by outside process at 17:12).
- **Deleted tracked files (151):** 138 `.claude/skills/*` + `.windsurf/skills/*` (agent-tooling; replaced by external symlinks) + 13 `output/` generated artifacts. Not staged.
- **Untracked non-manifest files (187+):** `screenshots/**`, `output/**`, `probe_out1…9.txt` (incl. `probe_out5.txt` — JWT), `v3_schema.sql`, `admin-dashboard.zip`, `backend/test_results.json`, root `test_results*.json`, `.env*` (gitignored), `database/rc2/…init_schema.sql`, `supabase/snippets/Untitled query 673.sql`, `.claude/.windsurf` skill symlinks, `.agents/skills` (modified), `prisma/`, `seed*.ts`, `carbon-tally-ui-demo/`, other non-manifest `docs/audit/cline/*`, `tools/` etc.
- **Not in repo:** `CARBONTALLY_V3_PUBLIC_PRODUCT_PLATFORM_EXPERIENCE_STANDARD.md` (D38 item).

---

## Appendix C — Required-but-not-staged List

**NONE.** (All 220 manifest files staged.)

---

## Appendix D — Unexpected Staged List

**NONE.** (All 220 staged files match the manifest.)

---

## Appendix E — Secret Scan Summary

| Check | Result |
|---|---|
| Secret patterns in `git diff --cached` (keys/JWTs/private keys/passwords) | 0 matches |
| `probe_out5.txt` staged | No |
| `tools/carbon_data_factory/deeepseek_api.txt` staged | No (remains deleted) |
| `.env*` staged | No |
| `.zip`/screenshots/`output/`/probe staged | No |
| `.gitignore`/`supabase/config.toml`/`frontend/App_.js` staged | No |
| Historical secret at `2d23fb8` | Present (remediation deferred, §27) |
| JWT in `probe_out5.txt` (working tree) | Present but unstaged/excluded |

---

## Appendix F — Verification Results

| Check | Result |
|---|---|
| HEAD / origin/main | `878bd0f` / `878bd0f` (0/0) |
| Commit count | 70 (no new commit) |
| Staged files | 220 (184 A, 36 M, 0 D) |
| Staged insertions/deletions | 66,929 / 1,052 |
| CR bytes in staged diff | 0 |
| Python AST parse (staged `.py`) | 119 files, 0 errors |
| Required-but-not-staged | 0 |
| Unexpected staged | 0 |
| Migrations staged | 10/10 |
| Unstaged modified residue | 548 (537 EOL-only + 11 real-content non-manifest incl. 2 external package files) |
| Untracked residue | 187 (+ this report when created) |

---

*End of staging report. Staging only — no commit, push, history rewrite, migration execution, or database change occurred. The staging report is intentionally left untracked (not part of the D20–D37 release manifest).*

```
A	backend/api/consultant_auth.py
A	backend/api/consultant_branding.py
M	backend/api/contracts.py
M	backend/api/dependencies.py
M	backend/api/issues.py
A	backend/api/operations_auth.py
M	backend/api/router.py
A	backend/api/v3_billing.py
A	backend/api/v3_commercial.py
A	backend/api/v3_consultants.py
A	backend/api/v3_discovery.py
A	backend/api/v3_documents.py
A	backend/api/v3_emissions.py
A	backend/api/v3_exports.py
A	backend/api/v3_manual_extraction.py
A	backend/api/v3_messaging.py
A	backend/api/v3_notifications.py
A	backend/api/v3_operations.py
A	backend/api/v3_organizations.py
A	backend/api/v3_processing.py
A	backend/api/v3_processing_workflow.py
A	backend/api/v3_qc.py
A	backend/api/v3_reporting.py
A	backend/api/v3_reports.py
A	backend/api/v3_review.py
A	backend/api/v3_suppliers.py
A	backend/api/v3_verifications.py
A	backend/api/v3_whitelabel.py
M	backend/auth.py
M	backend/config.py
M	backend/data/__init__.py
A	backend/data/billing.py
A	backend/data/consultants.py
A	backend/data/discovery.py
M	backend/data/emission_factors.py
M	backend/data/emissions_logs.py
A	backend/data/exports.py
A	backend/data/invitations.py
M	backend/data/issues.py
A	backend/data/manual_extraction.py
A	backend/data/messaging.py
A	backend/data/notifications.py
A	backend/data/organization_files.py
M	backend/data/organizations.py
A	backend/data/queue_settings.py
A	backend/data/report_versions.py
A	backend/data/reporting.py
M	backend/data/reports.py
A	backend/data/review_queue.py
A	backend/data/roles.py
A	backend/data/staff.py
A	backend/data/suppliers.py
A	backend/data/tenant.py
A	backend/data/upload_batches.py
A	backend/data/verifications.py
A	backend/data/whitelabel.py
A	backend/domain/billing.py
A	backend/domain/branding.py
M	backend/domain/calculation.py
A	backend/domain/discovery.py
A	backend/domain/evidence.py
M	backend/domain/issue.py
A	backend/domain/messaging.py
A	backend/domain/operations.py
M	backend/domain/organization.py
A	backend/domain/partners.py
A	backend/domain/staff.py
A	backend/domain/whitelabel.py
M	backend/engines/calculation.py
A	backend/engines/pdf_render.py
A	backend/engines/processing_workflow.py
M	backend/engines/report_generation.py
M	backend/main.py
A	backend/requirements-dev.txt
M	backend/requirements.txt
M	backend/routes/organizations/members.py
A	backend/services/billing.py
A	backend/services/storage.py
A	backend/services/v3_email.py
M	backend/tests/integration/conftest.py
A	backend/tests/integration/test_consultants.py
A	backend/tests/integration/test_customer_admin.py
A	backend/tests/integration/test_report_versions.py
M	backend/tests/integration/test_reports.py
M	backend/tests/integration/test_v3_rls_behavior.py
M	backend/tests/unit/api/fakes.py
A	backend/tests/unit/api/route_paths.py
A	backend/tests/unit/api/test_billing_core.py
A	backend/tests/unit/api/test_commercial_settings.py
A	backend/tests/unit/api/test_composition_root.py
A	backend/tests/unit/api/test_consultant_branding.py
A	backend/tests/unit/api/test_d19_lifecycle.py
A	backend/tests/unit/api/test_evidence_record.py
A	backend/tests/unit/api/test_evidence_traceability.py
M	backend/tests/unit/api/test_foundation.py
A	backend/tests/unit/api/test_operations_auth.py
A	backend/tests/unit/api/test_org_membership_resolution.py
A	backend/tests/unit/api/test_reporting.py
A	backend/tests/unit/api/test_scope_aware_authorization.py
A	backend/tests/unit/api/test_self_service_onboarding.py
A	backend/tests/unit/api/test_storage_security.py
A	backend/tests/unit/api/test_v3_consultants.py
A	backend/tests/unit/api/test_v3_customer_admin.py
A	backend/tests/unit/api/test_v3_d23_extraction_ux.py
A	backend/tests/unit/api/test_v3_discovery.py
A	backend/tests/unit/api/test_v3_emissions.py
A	backend/tests/unit/api/test_v3_entity_extraction.py
A	backend/tests/unit/api/test_v3_exports_serialization.py
M	backend/tests/unit/api/test_v3_issues.py
A	backend/tests/unit/api/test_v3_legacy_reimplementation.py
A	backend/tests/unit/api/test_v3_messaging.py
A	backend/tests/unit/api/test_v3_new_capabilities.py
A	backend/tests/unit/api/test_v3_notifications.py
A	backend/tests/unit/api/test_v3_operations.py
A	backend/tests/unit/api/test_v3_processing_workflow.py
A	backend/tests/unit/api/test_v3_qc.py
A	backend/tests/unit/api/test_v3_reports.py
A	backend/tests/unit/api/test_v3_routes_exposed.py
A	backend/tests/unit/api/test_v3_whitelabel.py
A	backend/tests/unit/domain/test_d19_domain.py
A	backend/tests/unit/engines/test_pdf_render.py
A	docs/Pricing/CARBONTALLY_ASSISTED_AND_MANAGED_PROCESSING_SPECIFICATION_V1(1).md
A	docs/Pricing/CARBONTALLY_DIRECT_MERCHANT_COMMERCIAL_ARCHITECTURE_V1.md
A	docs/Pricing/CarbonTally_Pricing_Comparison_Baseline_v2.md
A	docs/Pricing/CarbonTally_Unit_Economics_Baseline_v1.md
A	docs/Pricing/CarbonTally_V3_Draft_Pricing_Strategy_and_Competitive_Benchmark.md
A	docs/RECONSTRUCTED_TASK_HISTORY.md
A	docs/architecture/CARBONTALLY_BLOG_CMS_DECISIONS.md
A	docs/architecture/CARBONTALLY_EVIDENCE_TRACEABILITY_AND_PROVENANCE_PRINCIPLES.md
A	docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md
A	docs/architecture/CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md
A	docs/architecture/CARBONTALLY_V3_LEGACY_CONFORMITY_PLAN.md
A	docs/architecture/CARBONTALLY_V3_TERMINOLOGY_AND_DOMAIN_GLOSSARY.md
A	docs/audit/cline/CARBONTALLY_V3_D20_D37_GIT_RELEASE_PREPARATION_REPORT.md
A	docs/audit/cline/CARBONTALLY_V3_D27_AUDIT_INVENTORY.md
A	docs/audit/cline/CARBONTALLY_V3_D27_D19_FINAL_REPORT.md
A	docs/audit/cline/CARBONTALLY_V3_D28_VISUAL_QA_REPORT.md
A	docs/audit/cline/CARBONTALLY_V3_D30_REPORTING_COMPLETENESS_REPORT.md
A	docs/audit/cline/CARBONTALLY_V3_D31_REPORTING_COMPLETION_REPORT.md
A	docs/audit/cline/CARBONTALLY_V3_D32_FINAL_PRODUCT_COMPLETENESS_AUDIT.md
A	docs/audit/cline/CARBONTALLY_V3_D33_1_EVIDENCE_PRECISION_REPORT.md
A	docs/audit/cline/CARBONTALLY_V3_D33_EVIDENCE_TRACEABILITY_REPORT.md
A	docs/audit/cline/CARBONTALLY_V3_D34_PRODUCTION_CUSTOMER_JOURNEY_READINESS_REPORT.md
A	docs/audit/cline/CARBONTALLY_V3_D35_TECHNICAL_REMEDIATION_REPORT.md
A	docs/audit/cline/CARBONTALLY_V3_D36_BILLING_COMMERCIAL_ARCHITECTURE_AUDIT.md
A	docs/audit/cline/CARBONTALLY_V3_D37_0_BILLING_SECURITY_AND_CONFIGURABLE_SUBSCRIPTION_REPORT.md
A	docs/audit/cline/CARBONTALLY_V3_D37_MASTER_COMMERCIAL_BILLING_COMPLETION_REPORT.md
A	docs/audit/cline/CARBONTALLY_V3_GIT_REPOSITORY_AUDIT_AND_RELEASE_READINESS_REPORT.md
A	docs/audit/cline/CARBONTALLY_V3_PUBLIC_WEBSITE_AND_ARCHITECTURE_AUDIT.md
A	docs/cline/prompts/CarbonTally_V3_Service_Catalogue_and_Evidence_Traceability_Cline_Brief.md
M	frontend/src/App.js
M	frontend/src/AuthCallback.js
M	frontend/src/BetaSignup.jsx
M	frontend/src/LandingPage.jsx
M	frontend/src/Login.js
M	frontend/src/MagicLink.jsx
A	frontend/src/OnboardingPage.jsx
A	frontend/src/PricingPage.jsx
A	frontend/src/SelfServiceSignup.jsx
M	frontend/src/components/AppFooter.jsx
M	frontend/src/components/AppHeader.jsx
M	frontend/src/css/LandingPage.css
A	frontend/src/css/lp2.css
A	frontend/src/css/pricing_page.css
M	frontend/src/supabaseClient.js
A	frontend/src/v3/NotificationsPage.jsx
A	frontend/src/v3/__tests__/api.test.js
A	frontend/src/v3/admin/AdminPage.jsx
A	frontend/src/v3/admin/FacilitiesTab.jsx
A	frontend/src/v3/admin/MembersTab.jsx
A	frontend/src/v3/admin/ProfileTab.jsx
A	frontend/src/v3/admin/SecurityTab.jsx
A	frontend/src/v3/admin/SuppliersTab.jsx
A	frontend/src/v3/admin/admin.css
A	frontend/src/v3/api.js
A	frontend/src/v3/components/EvidenceRecordPanel.jsx
A	frontend/src/v3/components/RoleRoute.jsx
A	frontend/src/v3/components/StateViews.jsx
A	frontend/src/v3/components/V3Layout.jsx
A	frontend/src/v3/consultant/ClientMessagingTab.jsx
A	frontend/src/v3/consultant/ConsultantPage.jsx
A	frontend/src/v3/consultant/WhiteLabelTab.jsx
A	frontend/src/v3/consultant/consultant.css
A	frontend/src/v3/customer/BillingPage.jsx
A	frontend/src/v3/customer/DashboardPage.jsx
A	frontend/src/v3/customer/DocumentsPage.jsx
A	frontend/src/v3/customer/EmissionsPage.jsx
A	frontend/src/v3/customer/ExistingDataDiscoveryPage.jsx
A	frontend/src/v3/customer/IssuesPage.jsx
A	frontend/src/v3/customer/MessagingPage.jsx
A	frontend/src/v3/customer/ProcessingPage.jsx
A	frontend/src/v3/ops/CommercialTab.jsx
A	frontend/src/v3/ops/EntityExtractionWorkspace.jsx
A	frontend/src/v3/ops/ExtractionPanel.jsx
A	frontend/src/v3/ops/OperationsPage.jsx
A	frontend/src/v3/ops/OperatorQueue.jsx
A	frontend/src/v3/ops/OpsDashboard.jsx
A	frontend/src/v3/ops/ProcessingEntitiesTab.jsx
A	frontend/src/v3/ops/QcQueue.jsx
A	frontend/src/v3/ops/ReviewQueue.jsx
A	frontend/src/v3/ops/SlaTab.jsx
A	frontend/src/v3/ops/StaffRolesTab.jsx
A	frontend/src/v3/ops/StaffRoster.jsx
A	frontend/src/v3/ops/WorkItemWorkspace.jsx
A	frontend/src/v3/ops/ops.css
A	frontend/src/v3/reports/ReportDetailPage.jsx
A	frontend/src/v3/reports/ReportsPage.jsx
A	frontend/src/v3/reports/reports.css
A	frontend/src/v3/utils.js
A	frontend/src/v3/v3.css
A	supabase/migrations/20260821000000_d20_d15_active_consultant_grant.sql
A	supabase/migrations/20260821010000_d21_white_label_branding.sql
A	supabase/migrations/20260821020000_d22_processing_work_assignment.sql
A	supabase/migrations/20260822000000_p9_rls_recursion_fix.sql
A	supabase/migrations/20260822010000_d27_d19_customer_lifecycle.sql
A	supabase/migrations/20260823000000_d32_private_documents_storage.sql
A	supabase/migrations/20260823010000_d33_evidence_traceability.sql
A	supabase/migrations/20260824010000_d35_self_service_onboarding.sql
A	supabase/migrations/20260824020000_d37_0_billing_security_and_configurable_subscription.sql
A	supabase/migrations/20260824030000_d37_master_commercial_billing.sql
```
