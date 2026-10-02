# FINAL-03 PRE-CUTOVER — P2 / P5 / P6 / RLS DECISION PACKAGE (2026-10-02)

**STATUS: `FINAL-03 PRE-CUTOVER — P2 MANIFEST RECONCILED · FREEZE COMMIT NOT CREATED · PRODUCTION DATA PRESERVATION CONFIRMED · RLS DECISION PENDING (47 TABLES CLASSIFIED: 1 INTENTIONALLY NON-RLS · 16 WITH LIVE-EXPOSURE EVIDENCE · 30 OWNER DECISIONS) · P5-P6 INPUTS PENDING · NO MIGRATION EXECUTED`**

- Repository: `/home/shomonrobie/ct_93d5cdd` · branch `p8-release-reconciled` · HEAD `cabdca8380415e73a25cf23eb393d0b15c0af391`
- This pass is **read-only**. Nothing was deployed, no migration was executed, no RLS migration was created, no production row was modified, no local demo data was touched.
- FINAL-03 is **NOT** declared complete.

## Evidence provenance (all in this directory)

| File | Used for |
|---|---|
| `00-freeze-branch-head.txt` | branch / HEAD / remotes / status counts |
| `00-freeze-git-status-porcelain.txt` | pre-cutover working-tree state |
| `00-freeze-workspace-reconciliation.txt` | first-pass bucket reconciliation (collapsed `??`) |
| `01-production-pre-cutover-state.txt` | production baseline (134/87/47/198, 7049, 2 orgs, 2 users, 71 applied) |
| `02-preservation-assessment-entities.txt` | retained orgs/accounts/memberships, org-linked counts |
| `02-preservation-org-linked-counts.txt` | per-table org-linked row counts |
| `03-schema-drift-and-rls.txt` | the 47 names, existence of unapplied tables, emission_factors touch points |
| `04-migration-conflict-analysis.txt` | DML/DROP/policy-collision/RLS-enablement analysis of the unapplied set |
| `05-rls-prohibition-and-storage.txt` | per-table RLS-enablement probe, storage inventory |
| `06-environment-identity-redacted.txt` | local env identity (hosts only) |
| `07-production-public-tables.txt` | the 134 production public tables |
| `08-*` (this file) | P2/P5/P6 + 47-table classification |

> All production reads were executed under `default_transaction_read_only=on` against `aws-1-eu-west-2.pooler.supabase.com:5432` as `postgres.<ref>` (server 17.6). No credential, key, token, password or DSN is reproduced in this report.

---

# A. P2 — FREEZE MANIFEST (RECONCILED, NOT COMMITTED)

## A.0 Why the commit was not created

The owner's instruction was: *"create the freeze commit and 00-freeze evidence **only if** the exact scope is internally consistent"*, after *"identify any ambiguous file"*.

The manifest below is **exact** (every path enumerated, arithmetic closes to the file), but **four** items cannot be resolved without inventing an answer, and the owner explicitly said *"do not invent"*:

| # | Ambiguous item | Evidence found | Recommendation |
|---|---|---|---|
| AMBIG-1 | `.gitignore` (tracked, **M**) | `git diff` = whole-file CRLF→LF rewrite of all 110 lines **plus exactly one semantic change: `+.aider*`** (an AI-agent scratch pattern). No release-runtime impact. | **EXCLUDE** the modification (not "required by the release"); keep the HEAD version. |
| AMBIG-2 | `frontend/App_.js` (tracked, **M**, 2 insertions/2 deletions) | Zero importers found: `grep -rn "App_" frontend/src frontend/package.json` → **no match** (stray duplicate). | **EXCLUDE** (consistent with the earlier PO decision). |
| AMBIG-3 | `docs/architecture/` untracked set (**63** files) | Owner rule: include FINAL-02/03 + audit docs needed to defend the release; exclude PO/insight/business material. 47 files are unambiguous PO/census/insight/business material; **14** are unambiguously FINAL-02/03 + backup/storage implementation evidence; **2** straddle the line (both are *independent-verification* docs carrying a `CT-PO-` prefix): `CO-STRING-P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE.md`, `CT-PO-CARBONTALLY-CT-VERIFY-03-INDEPENDENT-REPORT-20260928.md`. | **INCLUDE 14; owner to rule on the 2.** |
| AMBIG-4 | `docs/cline/CARBONTALLY_CONSULTANT_CLIENT_DECISION_RECOVERY_20260930.md` (untracked, 1 file) | The only file in `docs/cline/` that is **not** under `evidence/`. It is a consultant↔client decision-recovery record dated inside the FINAL-02 window. | **INCLUDE-recommend** (decision record); owner may strike it. |

Because AMBIG-1…4 all change the content of the frozen tree, the freeze was **not** created. Every other item is decided. Section A.7 gives the exact, copy-pasteable command block that creates the freeze branch and commit the moment the owner answers the four items (any answer works — the include/exclude lists are pre-computed for both outcomes).

---

## A.1 Exact counts (locked, reproducible)

`git status --porcelain -uall | wc -l` → **1000** = **950** untracked (`??`) + **50** tracked-modified (` M`).

> ⚠ **CORRECTION of the first-pass reconciliation.** `00-freeze-workspace-reconciliation.txt` records `165` total (`115 ??` + `50 M`). The `115` counted untracked **directories collapsed** by plain `git status --porcelain`. Re-measured with `-uall`, the true untracked count is **950**. Every bucket count in that file that derives from `??` is therefore superseded by this table; its bucket *membership* analysis (A/B/C/D/E/F) is still valid and is carried forward below.
> Note also that the FINAL-03 pass artifacts are themselves untracked, so these counts grow by +1 per new evidence file (this file is the 30th `docs/cline/` entry).

| # | Bucket | Paths | Freeze |
|---|---|---|---|
| 1 | `.p18_audit_tmp/` | **805** | **NO** — scratch/audit tmp (owner brief) |
| 2 | `.costrict/` | **1** | **NO** — tool scratch (owner brief) |
| 3 | root strays: `8`, `=`, `costrict-p3-ov-01-independent-re-verification.txt` | **3** | **NO** — owner brief |
| 4 | `backend/nohup.out` | **1** | **NO** — runtime log |
| 5 | clean non-docs (runtime + tests + migrations + tool) | **37** | **YES** |
| 6 | `docs/architecture/` (incl. 1 quoted path) | **63** | **YES 14 (+2 borderline)** |
| 7 | `docs/cline/` | **30** | **YES 29 (+1 flagged, AMBIG-4)** |
| 8 | other docs (`docs/ChatGPT`, `docs/deepseek`, `docs/Final_Kimi`) | **10** | **NO** |
| 9 | tracked-modified (` M`) | **50** | **YES 48 (+2 ambiguous)** |
| | **total** | **1000** | include **≈ 128–134**, exclude **≈ 866–872** |

Arithmetic: **805 + 1 + 3 + 1 + 37 + 63 + 30 + 10 = 950** ✓ then **950 + 50 = 1000** ✓.
Exclusion of buckets 1–4 (810 of 950) accounts for **85.3%** of all untracked noise — none of it is frozen, exactly as the owner brief directs.

## A.2 Exact INCLUDE list — tracked-modified (48 of 50)

Runtime / API / services (29):

```
backend/api/dependencies.py
backend/api/router.py
backend/api/v3_consultants.py
backend/api/v3_discovery.py
backend/api/v3_documents.py
backend/api/v3_organizations.py
backend/api/v3_settings.py
backend/auth.py
backend/main.py
backend/backup/__init__.py
backend/backup/errors.py
backend/backup/service.py
backend/backup/settings.py
backend/backup/storage.py
backend/data/organization_files.py
backend/data/settings.py
backend/routes/admin/bulk.py
backend/routes/document_activity.py
backend/routes/emissions.py
backend/routes/notifications.py
backend/routes/organizations/files.py
backend/routes/organizations/management.py
backend/routes/upload.py
backend/services/email_service.py
backend/services/operational_alerting.py
backend/services/retention.py
backend/services/storage.py
backend/services/v3_email.py
backend/utils/email.py
```

Frontend (8) + admin (3) + build config (1):

```
frontend/src/App.js
frontend/src/components/ManualEntryStandalone.jsx
frontend/src/v3/api.js
frontend/src/v3/consultant/ConsultantPage.jsx
frontend/src/v3/customer/DocumentsPage.jsx
frontend/src/v3/ops/OperationsPage.jsx
frontend/src/v3/ops/SettingsTab.jsx
frontend/src/v3/__tests__/review-api.test.js
admin/src/components/admin/DefraFactorModal.js
admin/src/components/admin/ImportDefraModal.js
admin/src/pages/admin/DefraFactors.js
backend/requirements.txt          ← owner brief: INCLUDE
```

Tests (3) + release-defending reports / decision register (4):

```
backend/tests/unit/api/fakes.py
backend/tests/unit/backup/test_storage_and_settings.py
backend/tests/unit/test_ct_implement_01_remediation.py
docs/architecture/CT-IMPLEMENT-01-20260927-REPORT.md
docs/architecture/CT-PO-CARBONTALLY-CT-IMPLEMENT-02-REPORT-20260928.md
docs/architecture/CT-PO-CARBONTALLY-CT-IMPLEMENT-03-REPORT-20260928.md
docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md
```

Group tally: 29 + 12 + 7 = **48** ✓ (50 − AMBIG-1 `.gitignore` − AMBIG-2 `frontend/App_.js`).

## A.3 Exact INCLUDE list — untracked (37 non-doc + 29 `docs/cline` + 14 `docs/architecture`)

### A.3.1 Clean non-docs — 37 (runtime, tests, migrations, tool)

Runtime (19):

```
admin/src/services/factorAdminService.js
backend/api/upload_gate.py
backend/api/v3_backups.py
backend/api/v3_document_uploads.py
backend/backup/jobs.py
backend/backup/objects.py
backend/backup/policy.py
backend/backup/restore.py
backend/backup/retention.py
backend/backup/s3store.py
backend/backup/sigv4.py
backend/backup/verification.py
backend/backup/worker.py
backend/services/document_cleanup.py
backend/services/document_security.py
backend/services/email_provider.py
backend/services/storage_keys.py
backend/services/storage_metering.py
frontend/src/v3/ops/BackupsTab.jsx
```

Tests (14) — 11 backend + 3 frontend:

```
backend/tests/integration/backup/test_restore_local.py
backend/tests/unit/api/test_backup_admin_api.py
backend/tests/unit/api/test_ct_final_02_email_provider.py
backend/tests/unit/api/test_d7_f1_f2_f3_enforcement.py
backend/tests/unit/api/test_d7_org_lifecycle_decisions.py
backend/tests/unit/api/test_g1_g2_emissions_query_scope_and_staff_access.py
backend/tests/unit/api/test_storage_management_step1.py
backend/tests/unit/api/test_storage_management_step2.py
backend/tests/unit/backup/test_b7_connection_lease.py
backend/tests/unit/backup/test_jobs.py
backend/tests/unit/backup/test_sigv4_and_s3store.py
frontend/src/v3/__tests__/backup-admin-api.test.js
frontend/src/v3/__tests__/direct-upload.test.js
frontend/src/v3/__tests__/settings-tab-email-provider.test.jsx
```

Migrations (3) + tool (1):

```
supabase/migrations/20261025000000_ct_step2_documents_bucket_size_alignment.sql
supabase/migrations/20261026000000_ct_backup_01_backup_jobs.sql
supabase/migrations/20261027000000_ct_backup_02_backup_sets_and_verification.sql
tools/b7_pool_soak.py
```

Tally: 19 + 14 + 4 = **37** ✓

> **These 23 are the paths `00-freeze-workspace-reconciliation.txt` already flags as "the paths the frozen release DEPENDS ON but which are UNTRACKED"** (19 runtime + 3 migrations + 1 tool). An untracked-at-HEAD dependency set is exactly why the freeze commit is required before cutover: without it, the released artefact is not reproducible from any commit.

### A.3.2 `docs/cline/` — 30 files (all INCLUDE; 1 flagged as AMBIG-4)

```
docs/cline/CARBONTALLY_CONSULTANT_CLIENT_DECISION_RECOVERY_20260930.md   ← AMBIG-4
docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/  (14 files: 00-freeze-branch-head.txt,
  00-freeze-git-status-porcelain.txt, 00-freeze-workspace-reconciliation.txt, 01-production-pre-cutover-state.txt,
  02-local-environment-inventory.txt, 02-preservation-assessment-entities.txt, 02-preservation-org-linked-counts.txt,
  03-schema-drift-and-rls.txt, 04-migration-conflict-analysis.txt, 05-rls-prohibition-and-storage.txt,
  06-environment-identity-redacted.txt, 07-production-public-tables.txt, README.md, 08-<this file>)
docs/cline/evidence/FINAL-03-P1-B7-20261002/  (15 files: 01-b7-gate/{clone-dsn-used.txt,
  drill-post-fix-source-ct_final02_src.txt, drill-post-fix-source-ct_local_93d5cdd.txt, junit-backup-suites.xml,
  lease-site-grep.txt, p1-b7-test-nodeids.txt, p1-count-reconciliation.txt, p1-suite-counts.txt,
  pytest-backup-suites.stdout.txt, README.md, soak-b7-after-rev1.json, soak-b7-after-rev2.json,
  soak-b7-control-prefix.json, soak-b7-schema-complete.json}, README.md)
```

Tally: 1 + 14 + 15 = **30** ✓

> ⚠ `clone-dsn-used.txt` must be re-checked for a credential before it is committed. It is named as a DSN record; if it contains a password, the freeze must either exclude it or commit a redacted version. **This is a blocking P2 check, not a style preference.**

### A.3.3 `docs/architecture/` — 63 files → INCLUDE 14, BORDERLINE 2, EXCLUDE 47

**INCLUDE (14)** — FINAL-02/03 and backup/storage implementation + verification evidence:

```
CARBONTALLY_PRODUCTION_BACKUP_RESTORE_COMPLETE_IMPLEMENTATION_20261002.md
CARBONTALLY_STORAGE_MANAGEMENT_ARCHITECTURE.md
CARBONTALLY_STORAGE_MANAGEMENT_BASELINE.md
CARBONTALLY_STORAGE_MANAGEMENT_STEP1_IMPLEMENTATION_20260930.md
CARBONTALLY_STORAGE_MANAGEMENT_STEP2_IMPLEMENTATION_20260930.md
CARBONTALLY_STORAGE_PO_EVIDENCE_REVIEW_20260930.md
CT-FINAL-02-20260929-EMAIL-AND-UPLOAD-CONFIGURATION-REPORT.md
CT-FINAL-02-20260930-REHEARSAL-BASELINE-AND-GAP-MATRIX.md
CT-FINAL-02-20261001-LIVE-EVIDENCE-CLOSURE-PASS-REPORT.md
CT-FINAL-02-20261001-LOCAL-REHEARSAL-REPORT.md
CT-FINAL-02-B2-READONLY-VERIFICATION-20261001.md
CT-FINAL-02-CLOSURE-AND-LIVE-READINESS-20261001.md
CT-FINAL-02-INDEPENDENT-VERIFICATION-REPORT.md
CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md
```

**BORDERLINE (2) — owner ruling required (AMBIG-3)** — both are *independent-verification* records, i.e. precisely the evidence a release needs to defend itself, but they carry the `CT-PO-` prefix that otherwise marks PO material:

```
CO-STRING-P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE.md
CT-PO-CARBONTALLY-CT-VERIFY-03-INDEPENDENT-REPORT-20260928.md
```

## A.4 Exact EXCLUDE list

### A.4.1 Untracked scratch / stray (810)

`.p18_audit_tmp/` (**805 files**), `.costrict/` (**1 file**), `8`, `=`, `costrict-p3-ov-01-independent-re-verification.txt`, `backend/nohup.out`.

### A.4.2 Other docs (10) — PO/insight/handoff/compliance material, not release evidence

```
docs/ChatGPT/carbontally_handoff.md
docs/ChatGPT/carbontally_handoff_2026_09_28.md
docs/ChatGPT/CarbonTally_Incremental_ChatGPT_PO_History_2026-09-22.md
docs/ChatGPT/CarbonTally_Incremental_Chat_History_2026-09-22.md
docs/ChatGPT/CarbonTally_Incremental_Chat_History_2026-09-22-Insight-Strategy-v2.md
docs/deepseek/CT-GAP-IMPLEMENTATION-MASTER-2026-09-30-001.md
docs/deepseek/CT-GAP4-SUPPLIER-ENGAGEMENT-PORTAL-CURRENT-STATE-2026-09-30.md
docs/deepseek/CT-GAP5-CONVERSATIONAL-AI-COPILOT-CURRENT-STATE-2026-09-30.md
docs/deepseek/CT-GAP6-AUDITOR-READ-ONLY-PORTAL-CURRENT-STATE-2026-09-30.md
docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/.~lock.CarbonTally_UK_IE_Production_Readiness_Review.docx#
```

(`.~lock.…docx#` is a LibreOffice lock file — never a release artefact.)

### A.4.3 `docs/architecture/` — the 47 EXCLUDED (all paths are under `docs/architecture/`)

```
booking.com-hotel-booking.txt
CarbonTally_Insight_Architecture_Reference_2026-09-22.md
CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md
CarbonTally_Insight_Question_Library_2026-09-22.md
CarbonTally_PO_INS-01_Post-Closure_Reconciliation_2026-09-22.md
CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md
CT-PO-CARBONTALLY-CANONICAL-SCHEMA-FEATURE-SUPPORT-MATRIX-20260927.md
CT-PO-CARBONTALLY-CANONICAL-SCHEMA-FROM-ZERO-VERIFICATION-20260927.md
CT-PO-CARBONTALLY-CAPABILITY-AND-RELEASE-LEDGER-20260926.md
CT-PO-CARBONTALLY-CENSUS-INDEPENDENT-VERIFICATION-20260926.md
CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926.md
CT-PO-CARBONTALLY-COMPLETE-CAPABILITY-CENSUS-20260926-REPORT.md
CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md
CT-PO-CARBONTALLY-CONFIGURATION-CATALOGUE-20260927.md
CT-PO-CARBONTALLY-CT-AUDIT-01-CANONICAL-AUDIT-SYSTEM-RECONCILIATION-20260927.md
CT-PO-CARBONTALLY-CT-SCHEMA-01-REPORT-20260927.md
CT-PO-CARBONTALLY-CT-SCHEMA-02-REPORT-20260927.md
CT-PO-CARBONTALLY-CT-SCHEMA-03-REPORT-20260927.md
CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md
CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md
CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-LEDGER-20260927.md
CT-PO-CARBONTALLY-FALSE-IMPLEMENTED-AND-WIRED-REGISTER-20260927.md
CT-PO-CARBONTALLY-FEATURE-CATALOGUE-INDEPENDENT-VERIFICATION-20260927.md
CT-PO-CARBONTALLY-FEATURE-VERIFICATION-MATRIX-20260927.md
CT-PO-CARBONTALLY-FINAL-REPORT-20260927.md
CT-PO-CARBONTALLY-FUNCTIONALITY-TRACEABILITY-20260927.md
CT-PO-CARBONTALLY-GAP-ANALYSIS-20260927.md
CT-PO-CARBONTALLY-HISTORICAL-32-FILE-MODIFICATION-TIMELINE-20260926.md
CT-PO-CARBONTALLY-HISTORICAL-32-FILE-MODIFICATION-TIMELINE-20260926-REPORT.md
CT-PO-CARBONTALLY-HISTORICAL-32-FILE-TECHNICAL-RECONCILIATION-20260926.md
CT-PO-CARBONTALLY-HISTORICAL-32-FILE-TECHNICAL-RECONCILIATION-20260926-REPORT.md
CT-PO-CARBONTALLY-PO-DECISION-EVIDENCE-PACK-20260927.md
CT-PO-CARBONTALLY-RECON-03C-IMPORT-SUMMARY-AND-SUPABASE-CONFIG-DECISION-PACK-20260927.md
CT-PO-CARBONTALLY-RECON-03C-IMPORT-SUMMARY-AND-SUPABASE-CONFIG-DECISION-PACK-20260927-REPORT.md
CT-PO-CARBONTALLY-SCHEMA-CODE-MISMATCH-REGISTER-20260927.md
CT-PO-CARBONTALLY-SCHEMA-COMPARISON-MATRIX-20260927.md
CT-PO-CT-READINESS-01-MIGRATION-DRIFT-AND-CANONICAL-DB-BASELINE-AUDIT-20260927.md
CT-PO-CT-READINESS-01-MIGRATION-DRIFT-AND-CANONICAL-DB-BASELINE-AUDIT-20260927-REPORT.md
CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927.md
CT-PO-CT-READINESS-02-PHASE-A-REAL-READINESS-BASELINE-20260927-REPORT.md
CT-PO-CT-RELEASE-01-20260927-GITHUB-SYNC-REPORT.md
CT-PO-MASTER-WORKPLAN-20260925.md
CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924.md
CT-PO-P14-RECON-01-INVESTOR-ACCEPTANCE-CONTRACT-20260924.md
CT-PO-P18-PUBLIC-TRUTH-04-20260926-PUBLISH-VERIFICATION-FINAL.md
CT-PO-P18-PUBLIC-TRUTH-04-20260926-PUBLISH-VERIFICATION.md
"P17-PRODUCT-01 — Complete Scope 2 + Scope 3 Processing & Evidence Product Specification.md"
```

Tally: 14 INCLUDE + 2 BORDERLINE + 47 EXCLUDE = **63** ✓

## A.5 Blocking preconditions to the freeze commit (not scope items — hygiene)

**PRECOND-1 — plaintext credential in evidence · BLOCKS THE COMMIT.**
`docs/cline/evidence/FINAL-03-P1-B7-20261002/01-b7-gate/clone-dsn-used.txt` (71 bytes, 1 line) contains:

```
postgresql://<user>:<password>@127.0.0.1:54426/ct_b7_schema_1790937075
```

- userinfo shape is `xxxxxxxx:xxxxxxxx` and `grep -cE '://[^:@/]+:[^@]+@'` = **1** → a password **is** present (masked here; never printed).
- host is **loopback** (`127.0.0.1`) and the database is a throwaway B7 schema clone (`ct_b7_schema_1790937075`, ephemeral port 54426) — so this is a *local* credential, **not** a production secret.
- Tree-wide sibling scan: `grep -rlnE 'postgres(ql)?://[^ ]*:[^ @]+@|eyJ[A-Za-z0-9_-]{10,}|sbp_[A-Za-z0-9]{20,}' docs/cline/evidence/` → **only this file**. No production DSN, no JWT (`eyJ…`), no service key (`sbp_…`) anywhere else in the evidence tree.

Required action (owner-authorised, because it edits an evidence file): replace the password with `<redacted>` before staging — or exclude the file, which weakens the B7-gate record of *which DSN the drill used*. **Recommend redact.** PRECOND-2: confirm the password is local-only; rotate it if it was ever reused for a non-local database.

## A.6 Scope consistency — does the freeze contain unrelated work? **No.**

- All **48** in-scope modified files and all **37** in-scope untracked non-doc files are release lineage: FINAL-02 (email-config / direct-upload), FINAL-03 storage-management steps 1–2, **BACKUP-01/02 (P5)**, B7 connection-lease soak (P1), D7 + G1/G2 enforcement and org-lifecycle decisions, CT-IMPLEMENT-01/02/03 remediation. No new product capability, no unrelated refactor, no rename-only churn.
- The only formatting-only change in the whole tree (`.gitignore` CRLF→LF) is **AMBIG-1** and is recommended **out** — so the include set contains no "unrelated work" of that kind either.
- The unrelated work the owner warned about is exactly what the exclusion rules remove: PO/insight/census/investor material (47 arch docs), AI-handoff/compliance material (10 docs), audit scratch (805 `.p18_audit_tmp/` files) and the stray root files.

**Verdict: the scope is internally consistent and free of unrelated work — it is blocked only on AMBIG-1…4 + PRECOND-1, not on scope.**

## A.7 Exact freeze procedure (to run after the four rulings + PRECOND-1)

```sh
cd /home/shomonrobie/ct_93d5cdd
git rev-parse HEAD        # must print cabdca8380415e73a25cf23eb393d0b15c0af391
git switch -c release/final-03-pre-cutover-freeze   # owner may prefer another name

# G1 — backend (every pathspec below was checked against the A.1 partition: it stages
#      only include-set files; A.2/A.3 remain the authoritative per-path lists)
git add -- backend/api backend/auth.py backend/backup backend/data backend/main.py \
           backend/requirements.txt backend/routes backend/services backend/tests backend/utils

# G2 — frontend + admin
git add -- admin/src frontend/src/App.js frontend/src/components/ManualEntryStandalone.jsx \
           frontend/src/v3/api.js frontend/src/v3/consultant/ConsultantPage.jsx \
           frontend/src/v3/customer/DocumentsPage.jsx frontend/src/v3/ops frontend/src/v3/__tests__

# G3 — migrations + tool
git add -- supabase/migrations/20261025000000_ct_step2_documents_bucket_size_alignment.sql \
           supabase/migrations/20261026000000_ct_backup_01_backup_jobs.sql \
           supabase/migrations/20261027000000_ct_backup_02_backup_sets_and_verification.sql \
           tools/b7_pool_soak.py

# G4 — evidence docs
git add -- docs/cline/evidence \
           docs/cline/CARBONTALLY_CONSULTANT_CLIENT_DECISION_RECOVERY_20260930.md \
           docs/audit/cline/CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md

# G5 — the 17 docs/architecture files (4 modified reports + 13 of the 14 include set;
#       add the 14th — CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md — only if it is
#       final at commit time, since THIS file's sibling evidence will still be moving)
while read -r p; do git add -- "$p"; done <<'EOF'
docs/architecture/CT-IMPLEMENT-01-20260927-REPORT.md
docs/architecture/CT-PO-CARBONTALLY-CT-IMPLEMENT-02-REPORT-20260928.md
docs/architecture/CT-PO-CARBONTALLY-CT-IMPLEMENT-03-REPORT-20260928.md
docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_RESTORE_COMPLETE_IMPLEMENTATION_20261002.md
docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_ARCHITECTURE.md
docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_BASELINE.md
docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_STEP1_IMPLEMENTATION_20260930.md
docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_STEP2_IMPLEMENTATION_20260930.md
docs/architecture/CARBONTALLY_STORAGE_PO_EVIDENCE_REVIEW_20260930.md
docs/architecture/CT-FINAL-02-20260929-EMAIL-AND-UPLOAD-CONFIGURATION-REPORT.md
docs/architecture/CT-FINAL-02-20260930-REHEARSAL-BASELINE-AND-GAP-MATRIX.md
docs/architecture/CT-FINAL-02-20261001-LIVE-EVIDENCE-CLOSURE-PASS-REPORT.md
docs/architecture/CT-FINAL-02-20261001-LOCAL-REHEARSAL-REPORT.md
docs/architecture/CT-FINAL-02-B2-READONLY-VERIFICATION-20261001.md
docs/architecture/CT-FINAL-02-CLOSURE-AND-LIVE-READINESS-20261001.md
docs/architecture/CT-FINAL-02-INDEPENDENT-VERIFICATION-REPORT.md
docs/architecture/CT-FINAL-03-PRODUCTION-CUTOVER-PACKAGE-20261002.md
EOF
```

### A.7.1 Post-add verification (must pass before committing)

```sh
git diff --cached --name-only | wc -l                 # expect 128–131
git diff --cached --name-only | grep -E '^(\.gitignore|frontend/App_\.js)$'   # MUST BE EMPTY
git diff --cached --name-only | sort > /tmp/freeze_included.txt
sha256sum /tmp/freeze_included.txt                    # record: pins the exact frozen scope
git status --porcelain -uall | grep '^??' | grep -vE '\.p18_audit_tmp/|\.costrict/' \
  | grep -vE 'docs/(ChatGPT|deepseek|Final_Kimi)/|^(\?\?) (8|=|costrict-p3-ov-01-independent-re-verification\.txt)$|backend/nohup\.out'
# ^ MUST BE EMPTY: proves no release file was left unstaged
git commit -F- <<'MSG'
chore(FINAL-03 P2): freeze pre-cutover release scope

Freezes the exact pre-cutover tree for the FINAL-03 production cutover:
- BACKUP-01/02 (P5) + B7 connection-lease soak (P1): runtime, tests, migrations, tool
- FINAL-02 email/upload configuration + FINAL-03 storage-management steps 1/2
- FINAL-03 evidence set (docs/cline/evidence/**) and the storage/backup reports

Excluded by design: .p18_audit_tmp/ (805), .costrict/ (1), root strays (8, =, costrict-p3-ov-01-*.txt),
backend/nohup.out, PO/insight/handoff/compliance docs (57), the .gitignore CRLF-only rewrite and the
unimported frontend/App_.js duplicate.

Refs: CT-FINAL-03-DATA-PRESERVATION-20261002
MSG
```

### A.7.2 `00-freeze-*` evidence to write with the commit

| Field | Value now (pre-freeze) | To record at commit |
|---|---|---|
| branch | `p8-release-reconciled` (`00-freeze-branch-head.txt`) | `release/final-03-pre-cutover-freeze` |
| HEAD / frozen SHA | `cabdca8380415e73a25cf23eb393d0b15c0af391` — `docs(CT-FINAL-01): final security-fix and verification report` | **PENDING** — `git rev-parse HEAD` after commit |
| working-tree state | **1000** dirty (950 `??` + 50 ` M`) | residual untracked = only documented excludes (≈866) |
| remotes | `github` → `github.com/shomonrobie/CarbonTally.git`; `origin` → `/tmp/ct_step2` | unchanged |
| frozen-scope manifest | — | `sha256sum /tmp/freeze_included.txt` + the file itself, stored in `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/` |

> The `origin` remote pointing at `/tmp/ct_step2` (an ephemeral path) is itself a cutover hazard worth noting: the frozen commit must reach `github` before `/tmp` is reclaimed.

---

# B. PRODUCTION DATA PRESERVATION — CONFIRMED (read-only)

All figures below are from the eight evidence files listed in the provenance table; all production reads ran under `default_transaction_read_only=on`.

## B.1 Baseline

- **134** public tables; **87** RLS-enabled, **47** RLS-disabled; **198** policies total.
- Applied migrations: **71**, contiguous, latest `20260927000000`; **25** unapplied (files 72–96).
- `anon`: **0** privileges on all 47 RLS-disabled tables (contained by the already-applied P8-D4 grant hardening).
- `authenticated`: **full DML** on **45** of 47; **SELECT only** on `consultant_billing`; **no privileges** on `emission_factors`.
- `service_role`: **ALL** on all 47 → the backend (service-role DSN) is unaffected by RLS for every one of them.

## B.2 Retained entities

| Entity | Rows | Identity |
|---|---|---|
| `organizations` | 2 | Babui Technologies UK Limited; Faria Green Company UK LTD — both `active=true`, created 2026-09-17 |
| `auth.users` | 2 | both confirmed (last sign-ins 2026-09-26 / 2026-09-24) |
| `organization_members` | 2 | one membership per user↔org pair |
| `emission_factors` | **7049** | global catalogue, checksum `md5 021087a43be5db7469ec6d16ae542235` |
| `storage.objects` (`documents` bucket) | **58** | bucket is **private** (`public=false`), ceiling 2 097 152 B today |

## B.3 Org-linked data (the preservation red line)

| Table | Rows |
|---|---|
| `evidence_line_items` | 74 |
| `document_processing_queue` | 11 |
| `organization_files` | 11 |
| `organization_members` | 2 |
| `manual_extraction_batches` | 2 |
| `conversations` | 1 |
| `messages` | 1 |
| **total** | **102** |

`02-preservation-org-linked-counts.txt` cites **101** for the same set → a **±1 reconciliation** to settle by one re-measure at cutover (see F.5).

**No table in this set is one of the 47 RLS-disabled tables.** Only 7 of the 47 hold rows at all, and only 2 of those can be tenant data (`audit_trail` 126 rows; `manual_extraction_items` 14 rows, linked to the 2 retained `manual_extraction_batches` by `batch_id`). Therefore **enabling RLS on the 47 can never disturb the 7 org-linked retained tables** — but for `manual_extraction_items` it must be done as **enable + policy in the same migration**, because the retained rows belong to real customer orgs.

## B.4 What the cutover changes that could touch retained data — nothing, and here is the proof

| Change in the 25-file batch | Effect on retained data |
|---|---|
| **+16 new tables** (`activity_clarifications`, `backup_jobs`, insight/contract/instrument/report-schedule/report-share tables) | All **absent from production today** → purely additive; no retained row lives in any of them |
| **0** `DELETE FROM public.*`, **0** `TRUNCATE public.*`, **0** unconditional `DROP TABLE/COLUMN` | No statement can remove a retained row |
| **RLS enablements: 16**, all on the batch's own new tables; **0 of the 47** | No policy change can filter a retained row away from the backend (`service_role` = ALL, bypasses RLS) |
| `documents` bucket ceiling **2,097,152 → 10,485,760 B** (2 files) | A **widening** of an upload limit; no object is deleted or moved; the **58** objects and the bucket's `public=false` are untouched |
| Backfill of `adjudication_id` / `effective_context_key` (`20260930000000`) | On `activity_clarifications` — a table **created earlier in the same batch**; no pre-existing rows exist to alter |
| `staff_roles.permissions` merge (`20261026000000`) | **The only write to a pre-existing table row in the whole batch**: adds `{"can_manage_backups": true}` for the `admin`/`system_admin` names only. It touches **0** of the 102 org-linked rows and **0** retained business data — but it *does* write a privilege catalogue that is currently world-writable (R-2) |
| Creates of other objects (functions, triggers, indexes, constraints) | Attach to new tables or replace their own guarded definitions; no retained row is rewritten |

**Net:** the batch cannot remove, hide or rewrite the 2 organisations, the 2 accounts, the 2 memberships, the 102 org-linked rows, the 58 storage objects or the 7,049 factors. The only pre-existing row it writes anywhere is `staff_roles.permissions`.

## B.5 Verdict — data preservation: **PASS** (conditional)

- **PASS:** no statement in the 25 unapplied migrations can destroy or alter retained data; all new objects are additive; the only pre-existing row write is a narrow capability grant.
- **Conditions:** (1) the managed backup at step 4 is taken before step 5; (2) the mandatory order (§F.5) is respected; (3) the 10 survival items (§7 of the package README) are re-measured immediately after step 5 and again at step 11; (4) the ±1 reconciliation of the org-linked total (**102** vs the cited **101**) is settled by one re-measure at cutover.
- **Caveat that is *not* about preservation:** the same batch leaves all **47** RLS-disabled tables untouched (§C/F.3), which is a security finding, not a data-preservation one.

---

# C. RLS DECISION — CLASSIFICATION OF ALL 47 RLS-DISABLED TABLES (OWNER DECISION REQUIRED)

## C.0 Method, constants, and the 12 fields

**Constants verified for the whole set** (from `05-rls-prohibition-and-storage.txt` / `03-schema-drift-and-rls.txt`, re-confirmed in this pass):

- **(F5) `anon` privileges = NONE on all 47.**
- **(F7) `service_role` = ALL on all 47** → the backend is unaffected by RLS on every one of them (`postgres`/service-role bypass RLS).
- **(F3b) `authenticated` DML = 45/47**; `consultant_billing` = **SELECT only**; `emission_factors` = **no privileges**.
- **(F8) PostgREST reachability**: every table in (F3b) except `emission_factors` is reachable by **any** authenticated JWT, because PostgREST grants a role exactly what the role holds — there is no per-table gate.
- **No migration among the 96 files enables RLS on any of these 47** (verified exhaustively, twice). The only enablement sites in the repo are: `20260803000000_rc2_rls.sql`, the P8-RLS group (`20260920000000`, `20260922000000`, `20260923000000`, `20260925000000` — **already applied**), and **16 `ALTER TABLE … ENABLE ROW LEVEL SECURITY` statements in the 25 unapplied files** (`20260928000000` ×1, `20261001000000` ×2, `20261003000000` ×2, `20261005000000` ×2, `20261011000000` ×2, `20261012000000` ×1, `20261013000000` ×1, `20261022000000` ×2, `20261023000000` ×2, `20261026000000` ×1) — **one per new table created by the same batch; none targets a legacy table.**

**Field map** — F1 table · F2 rows · F3 tenant/per-user addressable · F4 data class · F5 anon priv · F6 authenticated priv · F7 service_role priv · F8 PostgREST-reachable · F9 browser call sites · F10 existing policies · F11 isolation evidence · F12 proposed class.

**Class legend** — **C1** platform/internal, containment already proven → *intentionally non-RLS*; **C2** privileged-backend-only, contains no tenant data → *acceptable now, enable when the feature ships*; **C3** **should carry RLS** (live exposure evidence) → remedy recommended; **C4** unclear → owner decision (my recommendation shown).

## C.1 The 47 tables

| # | table | rows | tenant/per-user | class | authenticated | browser sites | pol | isolation evidence | proposed |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `approval_decisions` | 0 | per-user cols, unbuilt | workflow | DML | 0 | 0 | 0 backend `.py` refs; 1 sql; no route, no UI, no policy | **C4 → C2** |
| 2 | `approval_requests` | 0 | per-user cols, unbuilt | workflow | DML | 0 | 0 | 0 `.py` refs; 1 sql; same as #1 | **C4 → C2** |
| 3 | `audit_trail` | **126** | yes (actor/user/org cols) | **audit + SEC** (`ip_address`, `user_agent`, `old_data`, `new_data`) | DML | 0 | 0 | **126 live business-audit rows readable *and writable* by any authenticated JWT**; 37 `.py` refs / 14 sql; immutability trigger exists but there is **no row filter** | **C3 — remediate** |
| 4 | `beta_access_codes` | 0 | **credential** (`code`, `magic_token`) | **CRED** | DML | **3** (BetaSignup ×2, BetaManagement ×1) | 0 | token material + a real browser path + no filter: any authenticated JWT can read code/token values | **C3 — remediate** |
| 5 | `beta_users` | 0 | yes (email, access level) | **AUTHZ** | DML | **4** (BetaLogin ×2, BetaSignup ×2) | 0 | access-level/left-join data on a live browser path, unfiltered | **C3 — remediate** |
| 6 | `business_hours` | 0 | no (weekday/time config) | config | DML | 0 | 0 | 0 `.py` / 1 sql refs; tenant-agnostic calendar; no rows, no path | **C4 → C1** |
| 7 | `consultant_billing` | 0 | yes (`consultant_id`) | billing | **SELECT only** | 0 | 0 | authenticated can **read** billing rows with no consultant filter → cross-consultant disclosure if rows ever exist; 0 `.py` refs / 5 sql | **C3 — remediate** |
| 8 | `consultant_tasks` | 0 | yes (`consultant_id`, `client_id`) | ops | DML | 0 | 0 | 6 `.py` refs / 1 sql; per-consultant rows, no filter, reachable | **C3 — remediate** |
| 9 | `conversation_activity_log` | 0 | yes (`conversation_id`, actor) | log | DML | 0 | 0 | 0 `.py` / 1 sql refs; semantics that of a per-conversation activity feed | **C4 → C3** |
| 10 | `conversation_participants` | **1** | yes (`conversation_id`, `user_id`) | messaging membership | DML | **3** (realtime manager, ChatWidget, ChatWindow) | **3** | **3 policies exist but are inert because RLS is off** — the membership filter the product already intends is not applied, while the chat UI reads/writes this table via PostgREST (1 live row) | **C3 — remediate (lowest-risk: activate existing policies)** |
| 11 | `dashboard_metrics` | 1 | no (aggregate row) | metrics | DML | 0 | 0 | 20 `.py` / 1 sql refs; 1 aggregate row, no browser path | **C4 → C2** |
| 12 | `email_logs` | 0 | yes (recipient address) | **PII/log** | DML | **1** (BetaManagement) | 0 | recipient emails + a live admin browser path, unfiltered; 9 `.py` / 3 sql refs | **C3 — remediate** |

| 13 | `emission_factors` | **7049** | no (global catalogue) | factor catalogue | **NONE** | 0 | 0 | 65 `.py` / 19 sql refs; **containment proven**: `authenticated` holds *no* privileges (applied `20260926000000…` hardening); read through the backend/service_role | **C1 — intentionally non-RLS** |
| 14 | `login_history` | 0 | yes (user/session) | **auth/security log** (`ip_address`, `user_agent`, `session_id`, `is_successful`, `failure_reason`) | DML | 0 | 0 | 0 `.py` / 1 sql refs; authentication telemetry is read/writable by any authenticated JWT; no browser path today | **C3 — remediate** |
| 15 | `manual_extraction_items` | **14** | yes (`batch_id` → org) | extracted document data + calculated emissions | DML | 0 | **1** | 88 `.py` / 15 sql refs; **14 live customer rows**; the **1 policy is inert** because RLS is off (policy intent defeated); links to the 2 retained `manual_extraction_batches` | **C3 — remediate (enable + policy in one migration: retained customer data)** |
| 16 | `message_activity_log` | 0 | yes (`message_id`, actor) | log | DML | 0 | 0 | 0 `.py` / 2 sql refs; per-message activity semantics | **C4 → C3** |
| 17 | `notification_delivery` | 0 | yes (recipient) | delivery log | DML | 0 | 0 | 4 `.py` / 1 sql refs; transport-level delivery records | **C4 → C2** |
| 18 | `notifications` | 0 | yes (`recipient_id`/user) | user data | DML | **1 live** (admin `WorkHub.jsx:194`) + 1 comment | 0 | 155 `.py` / 6 sql (word-boundary count inflated by unrelated `*_notifications*` identifiers); per-recipient rows on a live admin path, unfiltered. `frontend/src/context/RealtimeContext.jsx:276` explicitly records that the browser `supabase.from('notifications')` read/write was **removed** there because of deny-by-default RLS — evidence the product already treats this table as RLS-gated elsewhere | **C3 — remediate** |
| 19 | `password_reset_tokens` | 0 | **credential** (`token`, `user_id`) | **CRED** | DML | 0 | 0 | 3 `.py` / 3 sql refs; reset tokens are readable by any authenticated JWT → an account-takeover primitive the moment a row exists | **C3 — remediate** |
| 20 | `processing_assignments` | 0 | yes (assignee) | ops | DML | 0 | 0 | 1 `.py` / 3 sql refs; unbuilt workflow | **C4 → C2** |
| 21 | `processing_audit_trail` | 0 | yes (actor) | log | DML | 0 | 0 | 0 `.py` / 1 sql refs; unbuilt workflow | **C4 → C2** |
| 22 | `processing_steps` | 0 | no (step definitions) | workflow | DML | 0 | 0 | 0 `.py` / 2 sql refs; reference/steps data | **C4 → C2** |
| 23 | `processing_time_log` | 0 | yes (staff) | ops/HR | DML | 0 | 0 | 0 `.py` / 1 sql refs; staff time entries (would be HR-sensitive if populated) | **C4 → C2** |
| 24 | `qc_checklists` | 0 | no (checklist defs) | ops | DML | 0 | 0 | 0 `.py` / 1 sql refs | **C4 → C2** |

| 25 | `qc_checks` | 0 | yes (check → batch) | ops | DML | 0 | 0 | 2 `.py` / 2 sql refs | **C4 → C2** |
| 26 | `qc_errors` | 0 | yes (check → batch) | ops | DML | 0 | 0 | 4 `.py` / 2 sql refs | **C4 → C2** |
| 27 | `queue_settings` | 0 | no (ops tuning) | config | DML | 0 | 0 | 28 `.py` / 1 sql refs; **ops config that changes processing behaviour is writable by any authenticated JWT**; backend-only today | **C4 → C2** |
| 28 | `reassignment_history` | 0 | yes (staff) | log | DML | 0 | 0 | 1 `.py` / 2 sql refs | **C4 → C2** |
| 29 | `report_comments` | 0 | yes (author → report) | user data | DML | 0 | 0 | 0 `.py` / 2 sql refs; user-authored commentary | **C4 → C3** |
| 30 | `report_versions` | 0 | yes (report, `file_url`) | business artefact | DML | 0 | 0 | 60 `.py` / 11 sql refs; report content **and storage URLs** would be world-readable to any authenticated JWT once rows exist | **C4 → C3** |
| 31 | `review_assignment_history` | 0 | yes (staff) | ops | DML | 0 | 0 | 11 `.py` / 3 sql refs | **C4 → C2** |
| 32 | `review_audit_trail` | 0 | yes (actor) | audit log | DML | **5** (admin `reviewService.js`) | 0 | 4 `.py` / 4 sql refs; **5 live admin PostgREST call sites**, unfiltered → the trail the admin review UI writes is fully exposed | **C3 — remediate** |
| 33 | `sla_compliance` | 0 | yes (org/report) | ops | DML | 0 | 0 | 1 `.py` / 1 sql refs | **C4 → C2** |
| 34 | `sla_definitions` | 0 | no (per-document-type SLA config) | config | DML | 0 | 0 | 0 `.py` / 1 sql refs; tenant-agnostic definitions | **C4 → C1** |
| 35 | `staff_activity_log` | 0 | yes (staff) | log/HR | DML | 0 | 0 | 0 `.py` / 1 sql refs; per-staff behavioural log | **C4 → C3** |
| 36 | `staff_daily_performance` | 0 | yes (staff) | HR | DML | 0 | 0 | 0 `.py` / 1 sql refs | **C4 → C2** |

| 37 | `staff_performance` | 0 | yes (staff) | HR | DML | 0 | 0 | 0 `.py` / 1 sql refs | **C4 → C2** |
| 38 | `staff_roles` | **1** | yes (**privilege catalogue**) | **AUTHZ/CRED** (`permissions` jsonb) | DML | 0 | 0 | 22 `.py` / 7 sql refs; **the authoritative permission catalogue is UPDATE-able by any authenticated JWT**; unapplied `20261026000000_ct_backup_01…` itself merges `{"can_manage_backups": true}` into this row → a privilege-escalation surface **the release writes to** | **C3 — remediate** |
| 39 | `staff_workload` | 0 | yes (staff) | HR/ops | DML | **1** (admin `WorkHub.jsx:250`) | 0 | 20 `.py` / 1 sql refs; live admin path, unfiltered | **C3 — remediate** |
| 40 | `system_settings` | **1** | yes (system config) | **CFG/SEC** | DML | **3** (admin `Settings.js:69,120,164`) | 0 | 43 `.py` / 4 sql refs; **this single row drives email-provider selection (`resend`|`smtp`), sender identity and other platform behaviour** (`backend/services/email_provider.py` reads it) — DML means **any authenticated JWT can repoint production email** | **C3 — remediate (highest priority)** |
| 41 | `team_performance` | 0 | yes (team) | HR | DML | 0 | 0 | 0 `.py` / 1 sql refs | **C4 → C2** |
| 42 | `typing_status` | 0 | yes (per-user) | presence | DML | 0 | 0 | 0 `.py` / 1 sql refs; live presence semantics | **C4 → C3** |
| 43 | `user_activity_log` | 0 | yes (user) | log | DML | 0 | 0 | 0 `.py` / 3 sql refs | **C4 → C3** |
| 44 | `user_presence` | 0 | yes (per-user) | presence | DML | 0 | 0 | 0 `.py` / 1 sql refs | **C4 → C3** |
| 45 | `verification_activity_log` | 0 | yes (actor) | log | DML | 0 | 0 | 3 `.py` / 1 sql refs | **C4 → C2** |
| 46 | `verification_logs` | 0 | yes (document/tenant) | log | DML | 0 | 0 | 0 `.py` / 1 sql refs; verification records over tenant evidence | **C4 → C3** |
| 47 | `waitlist` | 0 | yes (public-signup PII) | **PII** | DML | **2** (BetaSignup, BetaManagement) | 0 | 8 `.py` / 2 sql refs; public-signup PII on live browser paths, unfiltered | **C3 — remediate** |

## C.2 Classification totals

| Proposed class | Tables | Count |
|---|---|---|
| **C1** intentionally non-RLS (containment proven) | 13 `emission_factors` | **1** |
| **C3** should carry RLS (live exposure evidence) | 3, 4, 5, 7, 8, 10, 12, 14, 15, 18, 19, 32, 38, 39, 40, 47 | **16** |
| **C4** unclear — owner decision, recommendation shown | the remaining 30 (19 → C2, 9 → C3, 2 → C1) | **30** |
| | | **47** ✓ |

## C.3 Findings that should block the "release-ready" declaration

| ID | Finding | Evidence |
|---|---|---|
| **R-1 (critical)** | `system_settings` — the row that selects the production email provider/sender is writable by **any authenticated user** | 1 row; `authenticated` = DML; 3 admin PostgREST sites; `email_provider.py` reads the setting |
| **R-2 (critical)** | `staff_roles` — the authoritative permission catalogue is **writable by any authenticated user**; BACKUP-01 (in the unapplied set) writes to it | 1 row; `permissions jsonb`; DML; `20261026000000…` merges a capability into this row |
| **R-3 (high)** | `password_reset_tokens` + `beta_access_codes` — credential/token material readable by any authenticated JWT | token columns + DML + no filter; `beta_access_codes` additionally has 3 browser sites |
| **R-4 (high)** | `manual_extraction_items` — **14 retained customer rows** whose existing policy is **inert** (RLS off), tied to the 2 retained batches; and `conversation_participants` — 3 inert policies behind a live chat UI (1 row) | policy counts 1 and 3; RLS disabled |
| **R-5 (high)** | `audit_trail` — 126 rows of before/after business audit **readable and writable** by any authenticated JWT | 126 rows; `old_data`/`new_data`/`ip_address`; DML; immutability trigger ≠ row filter |
| **R-6 (medium)** | 23 live browser call sites across 9 tables would break **fail-closed** the moment RLS is enabled without policies | §C.4 |

## C.4 "Could enabling RLS break the backend?" — no. What would need policies? — 9 tables.

- **The backend cannot break.** `service_role` holds ALL on all 47 and bypasses RLS; the backend never authenticates as `authenticated`. Row-filtering the backend's own queries would require policy changes, and no policy is *needed* for backend correctness.
- **23 browser call sites on 9 tables would break (fail-closed)** if RLS is enabled without matching policies: `beta_access_codes` (3), `beta_users` (4), `conversation_participants` (3), `email_logs` (1), `notifications` (1 live), `review_audit_trail` (5), `staff_workload` (1), `system_settings` (3), `waitlist` (2).
- The product already met this behaviour once: `frontend/src/context/RealtimeContext.jsx:276` documents that the browser read/write of `notifications` was removed there because of deny-by-default RLS.

**Recommended (owner-authorised) sequence — NOT part of this package:**
1. `conversation_participants` — **enable only**; the 3 policies already express intent (lowest-risk first step).
2. `manual_extraction_items` — **enable + policy in one migration** (retained customer rows).
3. R-1…R-3 set: `system_settings`, `staff_roles`, `password_reset_tokens`, `beta_access_codes`, `beta_users` — enable + policies, coordinated with the 9 browser sites.
4. Logs/user data: `audit_trail`, `login_history`, `email_logs`, `notifications`, `review_audit_trail`, `staff_workload`, `waitlist`, `consultant_*`.
5. Settle the 30 C4 tables (recommendations in §C.1).

> **HARD STOP observed:** no RLS migration was created, no `ALTER TABLE … ENABLE ROW LEVEL SECURITY` was executed and none of the 47 was touched. Any such file would be a **new** migration beyond `20261027000000` and requires explicit, separate owner authorisation.

---

# D. P5 — BACKUP TO THE PRODUCTION OBJECT STORE: REQUIRED INPUTS (ALL PENDING)

## D.1 What the code actually requires (authoritative: `backend/backup/settings.py`)

The owner brief names **8** variables. The module's documented environment contract requires **17** (plus 2 used elsewhere in the backup worker/retention). The 9 extra are not optional garnish — the drill cannot be run without several of them.

| Variable | Required when | Default | Purpose |
|---|---|---|---|
| `CT_BACKUP_OBJECT_STORE` | always | `local` | `local` \| `memory` \| `s3` — **must be `s3` for the P5 drill**; leaving it unset silently exercises the *local* store |
| `CT_BACKUP_S3_ENDPOINT` | store=s3 | — | e.g. `https://<ref>.supabase.co/storage/v1/s3` |
| `CT_BACKUP_S3_REGION` | store=s3 | `us-east-1` | Supabase Storage signs `us-east-1` regardless of project region |
| `CT_BACKUP_S3_BUCKET` | store=s3 | — | destination bucket |
| `CT_BACKUP_S3_ACCESS_KEY` | store=s3 | — | S3 access key id |
| `CT_BACKUP_S3_SECRET_KEY` | store=s3 | — | secret; **never logged, never defaulted** |
| `CT_BACKUP_S3_PREFIX` | optional | none | key prefix — recommend a dedicated prefix so drills cannot collide with real objects |
| `CT_BACKUP_S3_PATH_STYLE` | optional | `1` | path-style addressing (what Supabase Storage exposes) |
| `CT_BACKUP_LOCAL_ROOT` | local store | `/tmp/ct_backup_store` | provider root for the local store |
| `CT_BACKUP_TEMP_ROOT` | recommended | none | parent for **temporary export material** — must be writable on Render, whose disk is **ephemeral** |
| `CT_BACKUP_ENCRYPTION_KEY` | when encryption is requested | **none — no default** | base64 (standard, padded) that must decode to **exactly 32 bytes** (AES-256); unset ⇒ `BackupConfigurationError` **before any work starts** |
| `CT_BACKUP_KEY_ID` | optional | `key-v1` | non-secret identifier recorded in the manifest and artifact envelope — needed to know which key decrypts an artifact |
| `CT_BACKUP_SCHEMAS` | optional | `public` | comma-separated export list |
| `CT_BACKUP_COMPRESSION` | optional | `gzip` | `gzip` \| `none` |
| `CT_BACKUP_COMPRESSION_LEVEL` | optional | `6` | 1–9, validated |
| `CT_BACKUP_DENIED_SCHEMA_OVERRIDE` | only to export a denied schema | refused | must equal the exact acknowledgement phrase; **fail-closed** — credential-bearing/provider-private schemas (auth, storage, vault, realtime, migration history) are refused by default (review finding F2) |
| `CT_BACKUP_VERIFY_READBACK` | optional | `1` | read each stored object back and re-verify the application SHA-256 |
| `CT_BACKUP_PRUNE_ARTIFACTS`, `CT_BACKUP_RETENTION_DAYS` | policy decision | — | artifact retention/pruning behaviour |

## D.2 Inputs required from the owner — **none supplied**

1. Confirmation that `CT_BACKUP_OBJECT_STORE` will be **`s3`** for the drill (and not the local default).
2. Bucket identity: endpoint, region, bucket name.
3. Credentials: access key id + secret for that bucket.
4. **Encryption key** (32-byte base64) + the `key_id` it will be recorded under.
5. Key **escrow/ownership answer**: where the key is stored, who can retrieve it, and the rotation plan. *If the key is lost the backups are unrecoverable* — this is the single most important P5 answer.
6. `CT_BACKUP_S3_PREFIX` (recommend a dedicated prefix).
7. `CT_BACKUP_TEMP_ROOT` writable path on Render — and an answer for the **ephemeral-disk** risk: temp export material must not be the only copy at any point.
8. Retention/prune values.
9. Confirmation the target is **not** the local dev store.
10. Who runs the drill, when, and the acceptance evidence required (read-back verification + restore into a scratch schema).

## D.3 Status and exact remaining steps

**P5 = BLOCKED on credentials/identity.** No credentials were supplied and none were invented; nothing was written to any object store in this pass.

Once supplied, the P5 acceptance path is: run the backup with `CT_BACKUP_OBJECT_STORE=s3`, `CT_BACKUP_VERIFY_READBACK=1` and encryption on → confirm the manifest envelope records the right `key_id` → **restore-verify into a scratch schema** (the same pattern the B7 gate already used locally: `ct_b7_schema_*` clone, loopback DSN). The local variant of that drill is already evidenced in `docs/cline/evidence/FINAL-03-P1-B7-20261002/`.

---

# E. P6 — RENDER / VERCEL / EMAIL CUTOVER CONFIGURATION (ALL PENDING)

## E.1 Render (backend service) — required inputs, none supplied

| Input | Status |
|---|---|
| Service identity: name/ID, region, plan, service type | **not supplied** |
| Source: repository + **branch** | must be the P2 freeze branch — **not yet created** |
| Build command / start command | **not supplied**; the service is Python (`backend/requirements.txt` is inside the freeze set) |
| Health-check path, DB pool size / connection limits | **not supplied** |
| Env vars (below) | **not supplied** |

Env vars the backend actually reads (from `os.getenv`; noise from third-party libraries and test-only vars separated out):

```
# release-critical
DATABASE_URL                 # must be the Supabase pooler DSN with service-role rights
SUPABASE_URL
SUPABASE_SERVICE_KEY         # (SUPABASE_SERVICE_ROLE_KEY is also read as an alias)
SUPABASE_ANON_KEY
SUPABASE_JWT_SECRET
SUPABASE_DB_URL
RESEND_API_KEY               # if provider = resend
CT_SMTP_PASSWORD             # if provider = smtp (falls back to SMTP_PASSWORD)
CARBONTALLY_AI_API_KEY  CARBONTALLY_AI_BASE_URL  CARBONTALLY_AI_MODEL
PORT  APP_ENV|ENV  LOG_LEVEL  HOST  RELOAD  PREFIX
CT_REPORT_SCHEDULES_ENABLED
CT_BACKUP_*                  # the 17 + 2 from §D.1
# optional / support
INTEGRATION_DATABASE_URL  AUDIT_BATCH_SIZE  AUDIT_DEFAULT_ACTOR  CACHE_DEFAULT_TTL_SECONDS
EVENT_BUS_MAX_HANDLERS  SEARCH_INDEX_DEFAULT_LIMIT  FOUNDER_EMAIL  NEXT_PUBLIC_SUPABASE_URL
# NOT for production (test-only, must not be set on Render)
TEST_API_URL  TEST_USER_EMAIL  TEST_USER_PASSWORD  TEST_ADMIN_EMAIL  TEST_ADMIN_PASSWORD
TEST_ORG_ADMIN_EMAIL  TEST_ORG_ADMIN_PASSWORD
# OS / third-party noise (never configured by hand): HOME SHELL PATH PAGER DISPLAY WAYLAND_DISPLAY
ANDROID_DATA ANDROID_ROOT DATABRICKS_RUNTIME_VERSION PY_IGNORE_IMPORTMISMATCH PYTEST_THEME*
NUMPY_WARN_IF_NO_MEM_POLICY ORT_* SPHINX_BUILD ALLOW_RELEASED_ONNX_OPSET_ONLY
```

⚠ `DATABASE_URL` must be the production service-role DSN. It must **not** be the read-only probe DSN used for this analysis (`default_transaction_read_only=on` was a *session* guard only — it is not a deployment control and must not be relied on as one).

## E.2 Vercel (frontend) — required inputs, none supplied

| Input | Status |
|---|---|
| Project identity, production domain, build settings | **not supplied** |
| Env vars | **not supplied** |

Env vars referenced by frontend/admin code:

```
REACT_APP_API_URL            # must point at the Render service (the cutover link)
REACT_APP_SUPABASE_URL
REACT_APP_SUPABASE_ANON_KEY
REACT_APP_ENVIRONMENT
REACT_APP_GOOGLE_CLIENT_ID
REACT_APP_OAUTH_REDIRECT_URL # must match the deployed domain exactly
NEXT_PUBLIC_SUPABASE_URL     # also referenced (legacy/Next-style leftovers)
NEXT_PUBLIC_SUPABASE_ANON_KEY
```

Local `.env` identity (for comparison only, values not reproduced): `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_LIVE_URL`, `SUPABASE_LIVE_POSTGRES_DATABASE_URL`, `REACT_APP_API_URL`, `REACT_APP_SUPABASE_URL`, `REACT_APP_SUPABASE_ANON_KEY`, `ENVIRONMENT`.

## E.3 Email / SMTP — the sender identity is **not** an environment variable

Evidence: `backend/services/email_provider.py` (CT-FINAL-02 EMAIL-CONFIG-01).

- Provider selection is a **database setting**: `system_settings` key `email_provider` ∈ {`resend`, `smtp`} (`EMAIL_PROVIDER_SETTING_KEY = "email_provider"`).
- Only the **secret** comes from the environment: `resend` → `RESEND_API_KEY`; `smtp` → `CT_SMTP_PASSWORD` (with `SMTP_PASSWORD` as a fallback). The accepted-secret set is exactly `{RESEND_API_KEY, CT_SMTP_PASSWORD, SMTP_PASSWORD}`.
- SMTP **transport parameters** (host, port, sender) are part of the admin-configured setting, not env: default port `587` (STARTTLS), 20 s timeout, and `smtp_host` is **required** when `smtp` is selected — *"the SMTP provider is never half-configured"*.
- `backend/utils/email.py` and `backend/services/v3_email.py` both resolve the **admin-configured provider and the admin-configured sender**.

**Required inputs:** (1) provider choice (Resend vs SMTP); (2) **sender identity** = from-address + display name; (3) SMTP host, port, username; (4) the matching secret (`RESEND_API_KEY` or `CT_SMTP_PASSWORD`); (5) a delivery-test procedure and a controlled mailbox to receive it; (6) whether each tenant needs its own from-address (two retained orgs — decide now, since it changes the setting model).

⚠ **Security cross-link (R-1):** `system_settings` is one of the 47 RLS-disabled tables with `authenticated` = DML. **The production email configuration is therefore currently writable by any authenticated user.** Closing R-1 before cutover is also an email-security control, not only a database-hardening task.
⚠ Because the sender configuration lives in a database row, **P6 cannot be signed off until that row's production values are confirmed and its write access is gated.**

---

# F. MIGRATION & SCHEMA CONFLICT ANALYSIS (25 UNAPPLIED FILES)

## F.1 The set

Production's applied maximum is **`20260927000000`**; **96** files exist in `supabase/migrations/`, so **25 are unapplied** (positions 72–96 when sorted):

| Group | Files |
|---|---|
| FS / activity clarifications | `20260928000000`, `20260929000000`, `20260930000000`, `20260931000000` |
| Insights (P8 i1–i4 + discovery/rate-limit/temporal/data-quality) | `20261001000000`, `20261002000000`, `20261003000000`, `20261005000000`, `20261006000000`, `20261007000000` |
| Reporting / calculations | `20261008000000`, `20261009000000` |
| P17 taxonomy, accounting, instruments, estimation, product-contract, capability | `20261010000000`, `20261011000000`, `20261012000000`, `20261013000000`, `20261014000000`, `20261020000000` |
| CT-02 | `20261021000000` (audit ledger hardening), `20261022000000` (report sharing), `20261023000000` (scheduled reporting) |
| Storage | `20261024000000`, `20261025000000` (documents bucket ceiling) |
| **BACKUP** | `20261026000000` (**BACKUP-01** jobs), `20261027000000` (**BACKUP-02** sets + verification) |

## F.2 Preservation safety of the set — **PASS** (re-verified in this pass)

- **No** `DELETE FROM public.*`, **no** `TRUNCATE public.*` anywhere in the 25 files; **no** unconditional `DROP TABLE` / `DROP COLUMN` (drops are `IF EXISTS` and target policies, triggers or constraints being replaced); **no** `ADD COLUMN` / `CREATE TABLE` without `IF NOT EXISTS`. The destructive-statement scan returned **nothing**.
- The **16** tables the batch creates are **all absent from production today** → purely additive: `activity_clarifications`, `backup_jobs`, `carbontally_insight_conversations|interactions|messages|tool_calls`, `contractual_instruments`, `estimation_records`, `insight_concurrency_leases`, `insight_rate_limit_buckets`, `instrument_allocations`, `report_schedule_definitions`, `report_schedule_runs`, `report_share_access_events`, `report_shares`, `scope3_categories`.
- Only **two DML statements**, both benign:
  1. `20260930000000_p8_fs_adjudication_lifecycle.sql` — backfills `adjudication_id` / `effective_context_key` on `activity_clarifications`, **created earlier in the same batch** (no pre-existing rows at risk).
  2. `20261026000000_ct_backup_01_backup_jobs.sql` — merges `{"can_manage_backups": true}` into `staff_roles.permissions` for the **`admin` / `system_admin` names only**; documented as widening no RLS policy and touching no other permission — **but see R-2**: that row is currently writable by any authenticated user, so this statement is also a (tiny) privilege-escalation surface until R-2 is closed.

## F.3 Measured state delta — the step-7 gate must be **replaced**

| Object | Production today | Measured delta from the 25 files | Expected after step 5 |
|---|---|---|---|
| tables | **134** | **+16** (all created by the batch) | **150** |
| RLS-enabled | **87** | **+16** — 16 `ALTER TABLE … ENABLE ROW LEVEL SECURITY` statements, **one per new table**, spread over **10 files** | **103** |
| RLS-disabled | **47** | **0** | **47 — unchanged** (no file touches any of the 47) |
| policies | **198** | **35** `CREATE POLICY` / **27** `DROP POLICY…IF EXISTS` across 9 files (guarded replacements on new tables) | **re-measure at step 7** — `198+35 = 233` if every guarded drop is a no-op on a brand-new table; `198+35−27 = 206` if every drop removed a pre-existing policy. Not resolvable from file contents alone. |

**Refinement of the package's own arithmetic:** the earlier draft carried `87 + 11 = 98` RLS-enabled and `198 + 25 = 223` policies. The file contents measure **+16 enables** (not +11) and **35/27 policy statements** (not a flat +25). The table delta (`134 + 16 = 150`) is confirmed. **The RLS-disabled figure stays at 47 after the batch** — which is the sharpest possible statement of the §C problem: applying the entire canonical migration set does not close the 47-table gap by a single table.

⇒ The step-7 expectation **`149 tables · 149 RLS-enabled · 271 policies` cannot be satisfied**, and part of it — enabling RLS on the 47 — is **prohibited in production** by a ratified PO decision carried by `20260920000000_p8_rls_anon_grant_containment.sql` (*"Production is prohibited (G0-D): QA / non-production application only"*). The correct gate is a **production-specific** expectation (the table above, measured from the actual objects after step 5) **plus** an explicit owner risk decision on the 47 (§C).

## F.4 Idempotency risk to watch at step 5 (refined — not a preservation threat)

`CREATE POLICY` with **no** preceding `DROP POLICY IF EXISTS`: **2 files** — `20261001000000` (4 creates / 0 drops) and `20261003000000` (4 creates / 0 drops). The earlier draft listed three files; measurement shows `20261002000000` has 1 create / 1 drop and is therefore guarded. Their target tables do not exist in production, so no collision is expected — and if one fails the rule is **abort and investigate, never skip**.

## F.5 Other pre-cutover deltas (not preservation threats)

- `documents` bucket ceiling **2,097,152 B** vs canonical **10,485,760 B** → corrected by `20261024000000` / `20261025000000` (both inside the batch).
- `backup*` tables are **absent** from production → BACKUP-01/02 land in this same batch and **must be applied before any backend/worker start**.
- **Mandatory order (unchanged):** managed backup of current state (step 4) → apply the 25 migrations **including BACKUP-01/02** (step 5) → pre-start schema gate (step 6) → **only then** start backend/worker (step 14) → re-verify the 10 survival items (step 11).

---

# G. RESIDUAL RISKS AND SCOPE LIMITS OF THIS PACKAGE

| # | Residual risk / limit | Why it matters |
|---|---|---|
| 1 | **The 47-table RLS gap is unclosed** (16 tables carry live-exposure evidence; 2 are critical: R-1 `system_settings`, R-2 `staff_roles`) | This is a security posture issue, not a preservation one. It does **not** block the data-preservation objective, but it should block a *"release-ready"* declaration until the owner accepts it explicitly or schedules remediation (§C.4) |
| 2 | **P2 unratified** → HEAD `cabdca8380415e73a25cf23eb393d0b15c0af391` is **not deployable as-is** (23 required paths are untracked) | Nothing can be tagged or deployed until the freeze commit exists |
| 3 | **P5 blocked** on backup credentials **and on the encryption-key escrow answer** | Without the key, artifacts are unrecoverable; without a drill, backups are unproven |
| 4 | **P6 blocked** on Render/Vercel identity + production sender identity | No deploy target can be configured or tested |
| 5 | **P4 is satisfied on commitment only** — managed PITR is unavailable on the current plan | Consequence: the **only** recovery path for the retained data is the P5 backup, which is not yet proven in production. *This coupling is the single highest-risk item in the package* |
| 6 | Not verified here (needs production/deploy access): Render/Vercel runtime behaviour, an end-to-end post-cutover restore, real email delivery, and sign-in for both accounts after step 5 | These are step-12/13 acceptance items, outside a read-only pass |
| 7 | The **±1** discrepancy in the org-linked total (102 measured vs 101 cited) | Must be settled by one re-measure at cutover (§B.3/B.5) |

**Explicitly not done (and why):** no production mutation, no deploy, no destructive operation, no deletion of any production record, no change to the local demo environment, **no Git commit**, and **no RLS migration** (HARD STOP). Every production read ran under `default_transaction_read_only = on`.

---

# H. DECISION REGISTER — WHAT THE OWNER MUST DECIDE

| ID | Decision | Options | Blocks |
|---|---|---|---|
| **D-1** | Ratify the **P2 freeze manifest** (§A of the package README) | ratify as-is · amend · reject | freeze commit → any tag/deploy |
| **D-2** | **RLS on the 47** | (a) schedule the §C.4 sequence before cutover; (b) accept the documented risk in writing and remediate after cutover; (c) remediate the 3 critical tables (R-1, R-2, R-3) before cutover and accept the rest | security sign-off; the "release-ready" wording |
| **D-3** | Replace the **step-7 gate** | approve the production-specific expectation (§F.3) + the 47-table risk decision | step 7 can otherwise never pass |
| **D-4** | **P5** credentials + **key escrow** | supply the 17+2 values; name the key owner/rotation | backup drill → the only recovery path given P4 |
| **D-5** | **P6** identities + email provider/sender | supply Render/Vercel identity, provider choice, from-address, secret | deploy + email acceptance |
| **D-6** | The **30 unwritten tables** (§C.1 "C4") | accept as backend-only, or approve enabling when the feature ships | closes the classification |

## Status

| Gate | Status |
|---|---|
| P2 — freeze manifest | **OPEN** — reconciled, awaiting ratification |
| P5 — backup to production object store | **OPEN — blocking** (no `CT_BACKUP_*` values exist here; code fails closed) |
| P6 — Render / Vercel / SMTP | **OPEN — blocking** (no service identity, no production sender) |
| RLS — 47 tables | **DECISION REQUIRED** (16 with live-exposure evidence; 2 critical) |
| Data preservation | **PASS** (conditional on §B.5) |
| Migration-set preservation safety | **PASS** (§F.2) |
| Step-7 gate | **MUST BE REPLACED** (§F.3) |

**Report line: `FINAL-03 DATA PRESERVATION PLAN READY — AWAITING P2/P5/P6 + RLS DECISION`**

*This document is the decision companion to `README.md` in the same directory, which holds the full cutover package (steps 1–14), the preservation plan and the evidence index. No file in the repository was modified by this package other than this evidence document; no migration, schema, data or environment change was made.*

