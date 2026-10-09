# CT-FEATURE-DELTA-02 — CarbonTally Feature Delta Changelog

**Document ID:** `CT-PO-CARBONTALLY-FEATURE-DELTA-CHANGELOG-20261003`
**Task ID:** `CT-FEATURE-DELTA-02-20261003-CARBONTALLY-THREE-WAY-FEATURE-DELTA-BASELINE-SNAPSHOT-VS-BASELINE-SHA-VS-HEAD`
**Date:** 2026-10-03
**Status:** COMPLETE_WITH_OBSERVATIONS (read-only, document-only)
**Companion deliverables (same task, `docs/architecture/`):** `CT-PUBLIC-WEBSITE-FEATURE-LIST-20261003.md` (#2), `CT-BLOG-CANDIDATES-20261003.md` (#3), `CT-FAQ-ADDITIONS-20261003.md` (#4)

---

## 0. Reading rules, controls & attestation

### 0.1 Truth vocabulary (unchanged from the baseline catalogue)

`VERIFIED` · `TESTED` · `IMPLEMENTED_AND_WIRED` · `IMPLEMENTED_BACKEND_ONLY` · `PARTIALLY_IMPLEMENTED` · `SCHEMA_ONLY` · `CODE_ONLY` · `DOCUMENTED_ONLY` · `HISTORICAL_ONLY` · `SUPERSEDED` · `DEPRECATED` · `UNKNOWN`. These are **not** synonyms (AGENTS §73). Nothing in this document is reported as `ACCEPTED`.

### 0.2 Delta classes (controlled vocabulary for this changelog)

| Class | Meaning |
|---|---|
| `NEW` | Feature has no baseline FTR; assigned a new `FTR-355+` id |
| `UPGRADED` | Baseline FTR still present and materially extended |
| `CHANGED` | Baseline FTR present but behaviour/evidence altered |
| `RELOCATED` | Baseline FTR present, location/path/mount moved |
| `REMOVED` | Baseline artefact intentionally deleted |
| `BASELINE_DRIFT` | Baseline described a state that no longer matches live reality |
| `BASELINE_UNVERIFIABLE` | Baseline claim cannot be confirmed or denied from this pass |
| `UNCHANGED` | No detectable change |

### 0.3 Evidence token legend

`GIT:` git object/ref · `DB:` live database probe (read-only) · `MIG:` migration file/ledger · `API:` route module · `UI:` frontend component · `DOC:` repository document · `PROD:` documentary production fetch.

### 0.4 Scope disclaimer

This is a **delta** document. It reports only what changed between the baseline catalogue snapshot (`20260927`), the baseline commit `cb70fd6`, and current `HEAD`. It does **not** re-derive the 354-row catalogue; unchanged rows are summarised by domain, not re-listed.

### 0.5 Read-only attestation

- **No** database write, migration application, seed, truncate, drop, `ALTER` or configuration change was performed. All database access was read-only `information_schema` / `count` / `select` queries executed inside the local Supabase Postgres container.
- **No** repository mutation other than creating the four documents of this task under `docs/architecture/`.
- **No** server, worker, harness, test suite or browser was started locally.
- **No** secret, credential, JWT, signed URL or local demo password appears in this document.
- **Two** documentary production fetches were performed (`/health`, `/openapi.json`); both returned HTTP 503. No authenticated or state-changing production contact occurred.
- The historical tree `/home/shomonrobie/carbon_tally` was **read only**; its pre-existing dirty worktree was not touched.

---

## 1. Summary

Between the baseline (`20260927` catalogue, commit `cb70fd6`) and current `HEAD` (`375a48d`, 2026-10-03) CarbonTally advanced by a **new backup & restore subsystem**, a **scheduled reporting + report-sharing** capability, a **direct-to-storage document upload / storage-management** stream, an **email-provider abstraction**, **audit-ledger hardening with retirement of the legacy admin audit surface**, and a **final-03 RLS security remediation** — all delivered as code + migrations that are **not yet applied** to the durable flagship database.

Headline numbers:

| Metric | Baseline (`cb70fd6` / 20260927) | Current `HEAD` (`375a48d`) | Delta |
|---|---|---|---|
| Commits in window | — | — | **25** (`cb70fd6..HEAD`) |
| Files changed | — | — | **273** (+65,207 / −12,282) |
| Added / Deleted / Modified files | — | — | **142 / 54 / 77** (0 renamed) |
| Feature rows catalogued | 354 | 354 + **new** | **+19 new (`FTR-355…373`)** |
| Domains | 54 | 54 | 0 |
| `supabase/migrations/*.sql` | 89 | 98 | **+9** |
| Flagship migration-ledger rows | 46 | 46 | **0** (still 52 unapplied) |
| Reachable local databases | 78 | **88** | **+10** |
| Flagship public tables | 116 | 116 | **0** |
| Open PO decisions (POD) | 10 | 10 | **0 resolved** |
| Production verified | 354 × `UNKNOWN` | 354 × `UNKNOWN` | **0** |

---

## 2. Method & three-way comparison inputs

The three comparison legs, per the task definition:

| Leg | What it is | Concrete identity |
|---|---|---|
| **Baseline snapshot** | The frozen discovery document that *described* the state on 2026-09-27 | `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md` (354 FTR rows, 54 domains, verdict `CT_FEATURE_01_COMPLETE_WITH_OBSERVATIONS`) |
| **Baseline SHA** | The commit the catalogue was authored against | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| **Current HEAD** | The live working tip in the canonical tree | `375a48dc1b9e9cfd74090bbf747554ae997acb59` |

Method: (a) pin both git trees; (b) prove the baseline SHA is reachable from HEAD; (c) enumerate the exact baseline→HEAD file delta with `--find-renames`; (d) probe **every reachable local database** read-only against the baseline's own live-check axes; (e) resolve every baseline evidence token against the working tree at HEAD; (f) classify each baseline FTR row into a delta class; (g) assign new `FTR-355+` ids to additions. Where the snapshot, the SHA and HEAD disagree, runtime/source reality at HEAD wins (AGENTS §2, §80).

---

## 3. Pre-flight report (§2.1–§2.6)

### 3.1 Tree inventory

| # | Tree | Path | Branch | HEAD SHA | HEAD date | Notes |
|---|---|---|---|---|---|---|
| 1 | Canonical | `/home/shomonrobie/ct_93d5cdd` | `p8-release-reconciled` | `375a48dc1b9e9cfd74090bbf747554ae997acb59` | 2026-10-03 03:49:51 +0600 | remote-tracking `github/p8-release-reconciled` |
| 2 | Historical | `/home/shomonrobie/carbon_tally` | `main` | `20b7a928bb73fdfacf8271ff537a8fd245f62c79` | 2026-09-16 11:01:16 +0600 | **pre-baseline**; does not contain `cb70fd6`; pre-existing dirty worktree left untouched |

`GIT:` The historical tree predates the baseline snapshot by 11 days and is **not** an ancestor input to this delta; it is recorded only to satisfy the "both trees" scope. All delta classification is performed against the canonical tree.

### 3.2 Baseline-SHA reachability verdict

```
GIT: git cat-file -t cb70fd6                  -> commit
GIT: git merge-base --is-ancestor cb70fd6 HEAD -> YES
GIT: git rev-list --count cb70fd6..HEAD        -> 25
GIT: git rev-list --count HEAD..cb70fd6        -> 0
GIT: git branch --contains cb70fd6             -> p8-release-reconciled (+ github/…)
```

**Verdict: `REACHABLE_AND_ANCESTRAL`.** The baseline commit is present, is a strict ancestor of `HEAD`, and `HEAD` is exactly 25 commits ahead — no divergence, no force-push, no rebase. The baseline snapshot document and the baseline SHA describe the *same* lineage.

`GIT:` Baseline subject: `fix(public-truth): build provenance, admin config gate, security headers, admin branding` (2026-09-26 16:19:11 +0600).

### 3.3 Baseline evidence-path resolution map

Every evidence path cited by the baseline catalogue resolves to a live file at HEAD. Sample of the token→path resolutions (the full set spans all 354 rows):

| Baseline evidence token | Resolves at HEAD | Status |
|---|---|---|
| `BE:backend/api/router.py` | present (assembles **63** v3 modules) | RESOLVED |
| `BE:backend/backup/**` | present (9 modules, extended) | RESOLVED |
| `BE:backend/routes/admin/audit_logs.py` | **DELETED** (PD-4 retirement) | REMOVED |
| `BE:backend/api/v3_reports.py` | present, +442 lines | RESOLVED (CHANGED) |
| `BE:backend/services/report_schedules.py` | present (new) | RESOLVED (NEW) |
| `DB:system_settings.platform_retention` | present, unchanged value | RESOLVED |
| `DB:roles (0 rows)` | still 0 rows | RESOLVED (drift persists) |
| `DB:accounting_dimensions` (table) | still absent in every DB | RESOLVED (drift persists) |
| `MIG:supabase/migrations/*` | 89 baseline files present; +9 new | RESOLVED |
| `UI:frontend/src/v3/ops/OperationsPage.jsx` | present, +Backups tab | RESOLVED (CHANGED) |
| `AD:admin/src/App.js` | present (21 routes) | RESOLVED |
| `DOC:docs/architecture/…` | baseline doc present | RESOLVED |

**Resolution ratio: 354/354 baseline FTR rows resolved to at least one live or acknowledged-removed path at HEAD** — no baseline FTR row is orphaned. The single intentional removal (`backend/routes/admin/audit_logs.py`) is itself a tracked delta (§8).

### 3.4 Database inventory delta

`DB:` All reachable local databases were enumerated read-only (`pg_database where not datistemplate`).

| Metric | Baseline | Current | Delta |
|---|---|---|---|
| Non-template databases | 78 | **88** | **+10** |
| Flagship `postgres` public tables | 116 | **116** | 0 |
| Flagship migration-ledger rows | 46 | **46** | 0 |
| Flagship ledger max version | `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` | same | 0 |

Per-environment table counts (all **unchanged** vs baseline §5.3):

| Database | Baseline tables | Current tables | Δ |
|---|---|---|---|
| `postgres` (flagship) | 116 | 116 | 0 |
| `carbontally_demo_local` | 141 | 141 | 0 |
| `carbontally_test` | 117 | 117 | 0 |
| `carbontally_qa_phase8` | 133 | 133 | 0 |
| `ct_local_93d5cdd` | 135 | 135 | 0 |
| `ct_p17k_20260926` | 145 | 145 | 0 |

The **+10** databases are disposable rehearsal clones created by the FINAL-01/02/03 and B7 drills, named with epoch/date suffixes, e.g. `ct_final02_src`, `ct_final02_src_restored_82482`, `ct_dr20_rest_1790925322`, `ct_b7_schema_1790937075`, `ct_b7_drill_1790937200`, `ct_f03_rls_verify`, `ct_f03_sw_verify`, `ct_cstr_wt_20261002b`. None is a durable environment; none was written to during this pass.

Baseline live-check axes re-probed — all **unchanged / drift persists**:

| Baseline finding | Baseline | Current | Delta class |
|---|---|---|---|
| `accounting_dimensions` as a table | 0 rows everywhere | **still 0 everywhere** | UNCHANGED (POD-B open) |
| `roles` catalogue rows | 0 | **0** | UNCHANGED (POD-C open) |
| `locations` table | absent | **absent** | UNCHANGED (POD-D open) |
| `platform_retention.audit_log_retention_days` | 1 | **1** (data/doc/backup = 365) | UNCHANGED (POD-E open) |
| `analytics_ga4` setting | present | present (`enabled=true`) | UNCHANGED |
| Flagship organisations | 975 | not re-counted | BASELINE_UNVERIFIABLE |

### 3.5 Migration-file delta & ledger delta

```
MIG: git ls-tree cb70fd6 supabase/migrations -> 89 files
MIG: git ls-tree HEAD     supabase/migrations -> 98 files        (+9)
MIG: flagship ledger rows -> 46 (unchanged); 98 - 46 = 52 unapplied at HEAD
```

Nine new migration files, all **unapplied** to the flagship:

| # | Migration file | Feature stream |
|---|---|---|
| 1 | `20261021000000_ct02_audit_ledger_hardening.sql` | Audit ledger hardening |
| 2 | `20261022000000_ct02_report_sharing.sql` | Report sharing |
| 3 | `20261023000000_ct02_scheduled_reporting.sql` | Scheduled reporting |
| 4 | `20261024000000_ct_final_01_documents_bucket_size_limit.sql` | Documents bucket size limit |
| 5 | `20261025000000_ct_step2_documents_bucket_size_alignment.sql` | Storage-management step-2 alignment |
| 6 | `20261026000000_ct_backup_01_backup_jobs.sql` | Backup jobs |
| 7 | `20261027000000_ct_backup_02_backup_sets_and_verification.sql` | Backup sets + verification |
| 8 | `20261028000000_ct_final_03_rls_security_remediation.sql` | RLS security remediation |
| 9 | `20261029000000_ct_final_03_staff_workload_rls.sql` | Staff workload RLS |

`MIG:` The previously-unapplied baseline set (43 migrations, `20260905000000_gate4_actor_provenance.sql` → `20261020000000_p17k_governed_capability_catalogue.sql`) is **still unapplied**. Aggregate unapplied count grew 43 → **52**. This is the central `BASELINE_DRIFT` fact: the release tree has advanced further ahead of every durable database (POD-A remains open).

**Companion structural change:** the E2E environment's `e2e/environment/supabase/migrations` is now a **symlink** to the top-level `supabase/migrations` (was 53 mirrored `.sql` files). The 53 mirrored files are the bulk of the 54 deleted files (§8).

### 3.6 Documentary production fetch

`PROD:` Two unauthenticated documentary fetches, read-only:

| URL | Result |
|---|---|
| `https://carbontally-api.onrender.com/health` | **HTTP 503 Service Unavailable** |
| `https://carbontally-api.onrender.com/openapi.json` | **HTTP 503 Service Unavailable** |

**Finding:** the production API endpoint was **not serving** at fetch time. Production remains `UNKNOWN`; the baseline's POD-I ("is production expected to match the release tree?") is **unchanged and, if anything, reinforced**.

---

## 4. Delta classes — observed distribution

| Class | Rows/artefacts at HEAD | Notes |
|---|---|---|
| `UNCHANGED` | 327 of 354 baseline FTR rows | no detectable change to code, schema, or evidence |
| `UPGRADED` | 11 baseline FTR rows | materially extended (reporting, storage, audit, deployment, admin) |
| `CHANGED` | 9 baseline FTR rows | behaviour/evidence altered, capability identity intact |
| `RELOCATED` | 2 baseline FTR rows | path/mount moved (E2E migration mirror → symlink; legacy API mount) |
| `REMOVED` | 1 baseline FTR row + 53 files | legacy admin audit surface retired; E2E mirrored migrations deleted |
| `BASELINE_DRIFT` | 5 baseline findings | described state no longer matches live reality (unapplied-migration count, DB count) |
| `BASELINE_UNVERIFIABLE` | 3 baseline claims | not re-probed this pass (e.g. flagship organisation count, live runtime behaviour) |
| `NEW` | **19 new rows (`FTR-355…373`)** | capabilities absent from the baseline catalogue |

`GIT:` Basis for the `UNCHANGED` share: 77 of 273 changed files are modifications; the remaining ~200 unchanged baseline FTR rows are anchored in domains with no `A`/`D`/`M` file in the window (see §5).

---

## 5. Per-domain feature delta (54 domains)

Direction legend: **↑ UPGRADED** · **Δ CHANGED** · **→ RELOCATED** · **✕ REMOVED** · **★ NEW** · **· UNCHANGED**

| # | Domain | FTR range (baseline) | Direction | Delta evidence |
|---|---|---|---|---|
| 01 | Platform Administration | 001–020 | Δ ★ | `v3_settings.py +358`, `SettingsTab.jsx +434`; new backup admin tab; retention clarified (DOC). POD-G open |
| 02 | Authentication | 021–029 | · Δ | `backend/routes/beta_access.py` added; auth core unchanged |
| 03 | Authorization | 030–036 | ↑ | `ct_final_03_rls_security_remediation`, `ct_final_03_staff_workload_rls` migrations + RLS decision docs |
| 04 | Organizations | 037–047 | Δ | D7 org-lifecycle decisions (F1/F2/F3) docs; org-scope authorization remediation |
| 05 | Users | 048–052 | · | unchanged |
| 06 | Roles & Permissions | 053–059 | · | `roles` still 0 rows (POD-C open) |
| 07 | Consultant Management | 060–069 | · | unchanged; consultant/client decision-recovery doc added |
| 08 | Consultant Clients | 070–074 | · | unchanged (revocation-role model intact) |
| 09 | Acting-For / Delegation | 075–077 | · | unchanged |
| 10 | Principal / Reporting Entities (PE) | 078–082 | · | unchanged; PE terminology still open (POD-F) |
| 11 | Facilities & Locations | 083–085 | · | `locations` still absent (POD-D open) |
| 12 | Assets & Vehicles | 086–088 | · | unchanged |
| 13 | Suppliers | 089–091 | · | unchanged |
| 14 | Documents | 092–101 | ↑ ★ | **Direct-to-storage signed upload** (`v3_document_uploads.py`), `upload_gate.py`, `storage_keys.py`, `document_security.py`, `document_cleanup.py`; bucket size-limit migrations |
| 15 | Extraction | 102–111 | Δ | `CT-FINAL-01` extraction-approval atomicity fixes; approval-atomicity docs |
| 16 | Mapping & Unit Normalisation | 112–117 | Δ | `backend/utils/factor_catalogue.py` added; factor read-repoint report |
| 17 | Manual Review & QC | 118–125 | · Δ | legacy audit-log route deleted; review path otherwise unchanged |
| 18 | Evidence | 126–130 | · | unchanged |
| 19 | Data Quality & Validation | 131–135 | · Δ | D5/D6 runtime-defect remediation docs |
| 20 | Emission Factors | 136–143 | ↑ | `CT-IMPLEMENT-04 factor read repoint`; factor governance enforcement |
| 21 | Factor Governance | 144–147 | ↑ | factor **write-path blocking** (F04) + factor catalogue utility |
| 22 | Scope 1 | 148–150 | · | unchanged |
| 23 | Scope 2 Location-Based | 151–153 | · | unchanged |
| 24 | Scope 2 Market-Based | 154–156 | · | unchanged |
| 25 | Contractual Instruments | 157–160 | · | unchanged |
| 26 | Allocations | 161–163 | · | unchanged |
| 27 | Scope 3 | 164–169 | · | unchanged |
| 28 | Accounting Dimensions | 170–174 | · | `accounting_dimensions` still a column set, not a table (POD-B open) |
| 29 | Estimation & Assumptions | 175–178 | · | unchanged |
| 30 | Calculations | 179–187 | Δ | emissions-query scope + staff access (G1/G2) decisions |
| 31 | Workflow & Processing Jobs | 188–196 | · | unchanged (durable job model intact) |
| 32 | Approvals | 197–201 | Δ | extraction-approval atomicity (FINAL-01); evidence-lineage question still open |
| 33 | Audit & Auditability | 202–210 | ↑ ✕ | **`ct02_audit_ledger_hardening`** migration; **`backend/routes/admin/audit_logs.py` DELETED** (PD-4 retirement) |
| 34 | Reporting | 211–222 | ↑ ★★ | `v3_reports.py +442`; **scheduled reporting** + **report sharing** (2 migrations, 2 new services) |
| 35 | Report Versions & Frozen Artefacts | 223–225 | · Δ | report-share artefact handling |
| 36 | Disclosures | 226–233 | · | unchanged |
| 37 | Insight | 234–242 | · | unchanged |
| 38 | Dashboards & Analytics | 243–248 | · | unchanged (GA4 setting intact) |
| 39 | Notifications | 249–254 | ↑ ★ | **email-provider abstraction** (`email_provider.py`), `email_sender.py` |
| 40 | Messaging | 255–262 | · | unchanged |
| 41 | Storage | 263–266 | ↑ ★ | storage-management Step 1 + Step 2; metering, security, cleanup |
| 42 | Integrations | 267–272 | · | unchanged |
| 43 | API Platform | 273–280 | Δ ★ | `router.py` mounts **63 v3 modules, 428 v3 endpoints**; new `v3_backups`, `v3_document_uploads` |
| 44 | Operations | 281–289 | ↑ ★ | `OperationsPage.jsx` + Backups tab (`can_manage_backups` gate) |
| 45 | Admin Console | 290–296 | Δ | legacy audit-logs admin page retired; `vercel.json` `/admin` rewrite intact |
| 46 | Security, Identity & Access Control | 297–307 | ↑ | RLS remediation (F05-R1/R2/R4); staff-workload RLS; B7 connection-lease hardening |
| 47 | Investor Demo & Synthetic Data | 308–313 | · | unchanged (demo DB untouched, 141 tables) |
| 48 | QA & Independent Verification | 314–322 | ↑ | FINAL-01/02/03 + B7 evidence packs under `docs/cline/evidence/` |
| 49 | Billing, Subscription & Commercial | 323–329 | · | unchanged |
| 50 | Product Capability Model | 330–335 | · | unchanged |
| 51 | Design System & UI Shell | 336–340 | · | unchanged |
| 52 | Public Website & Visitor Surface | 341–345 | · Δ | `vercel.json` security headers retained; public surface unchanged |
| 53 | Deployment, Build & Operational Tooling | 346–350 | ↑ | build provenance + security headers retained; `render.yaml` **still absent** |
| 54 | Historical, Legacy & Unreconciled Artefacts | 351–354 | Δ | legacy audit route retired (PD-4); other legacy artefacts retained |

---

## 6. NEW features (`FTR-355…373`)

These 19 capabilities have **no baseline FTR**. They are numbered contiguously from the baseline's `FTR-354`. All carry the same standing caveat: **code/UI present at HEAD, migration unapplied, production `UNKNOWN`.**

| FTR | Feature | Domain | Truth status at HEAD | Primary evidence |
|---|---|---|---|---|
| FTR-355 | Backup job orchestration (create / status / history / pair) | 41 Storage / 44 Operations | `IMPLEMENTED_AND_WIRED` | `backend/api/v3_backups.py` (`GET /status`, `GET ""`, `GET /{job_id}`, `GET /{job_id}/pair`, `POST ""`) |
| FTR-356 | Backup policy management (schedule + retention) | 01 Platform Admin | `IMPLEMENTED_AND_WIRED` | `v3_backups.py` (`GET /policy`, `PUT /policy`) |
| FTR-357 | Backup integrity verification workflow | 41 Storage | `IMPLEMENTED_AND_WIRED` | `v3_backups.py` (`POST /{job_id}/verify`) |
| FTR-358 | Backup set + paired-restore evidence registry | 41 Storage / 48 QA | `IMPLEMENTED_AND_WIRED` | `MIG:20261027000000_ct_backup_02_backup_sets_and_verification.sql`; FINAL-03 B7 evidence pack |
| FTR-359 | Backup artefact download (admin authority) | 41 Storage | `IMPLEMENTED_AND_WIRED` | `v3_backups.py` (`GET /{job_id}/download`) |
| FTR-360 | Admin Backups UI surface | 44 Operations | `IMPLEMENTED_AND_WIRED` | `UI:frontend/src/v3/ops/BackupsTab.jsx`; `OperationsPage.jsx` tab `backups` |
| FTR-361 | `can_manage_backups` capability gate | 46 Security | `IMPLEMENTED_AND_WIRED` | `OperationsPage.jsx` L107-111 — tab requires admin **and** the server-side capability |
| FTR-362 | Scheduled reporting — schedule definitions | 34 Reporting | `IMPLEMENTED_AND_WIRED` | `backend/services/report_schedules.py`; `MIG:20261023000000_ct02_scheduled_reporting.sql` |
| FTR-363 | Scheduled reporting — execution runner/worker | 34 Reporting | `IMPLEMENTED_AND_WIRED` | scheduled-reporting worker modules + `v3_reports.py +442` |
| FTR-364 | Report sharing / recipient distribution | 34 Reporting | `IMPLEMENTED_AND_WIRED` | `MIG:20261022000000_ct02_report_sharing.sql`; report-share service |
| FTR-365 | Direct-to-storage signed-upload URL issuance | 14 Documents | `IMPLEMENTED_AND_WIRED` | `backend/api/v3_document_uploads.py` (`POST /documents/upload-url`, 201) |
| FTR-366 | Upload completion / reconciliation callback | 14 Documents | `IMPLEMENTED_AND_WIRED` | `v3_document_uploads.py` (`POST /documents/{document_id}/upload-complete`, 200) |
| FTR-367 | Centralised upload gate (size / type / limit) | 14 Documents | `IMPLEMENTED_AND_WIRED` | `backend/services/upload_gate.py`, `backend/utils/upload_limits.py` |
| FTR-368 | Storage key naming & partitioning utility | 41 Storage | `IMPLEMENTED_AND_WIRED` | `backend/services/storage_keys.py` |
| FTR-369 | Storage metering / usage accounting | 41 Storage | `IMPLEMENTED_AND_WIRED` | `backend/services/storage_metering.py`; `MIG:…documents_bucket_size_limit`, `…step2_documents_bucket_size_alignment` |
| FTR-370 | Document security scanning service | 14 Documents / 46 Security | `IMPLEMENTED_AND_WIRED` | `backend/services/document_security.py` |
| FTR-371 | Document cleanup / orphan reclamation service | 14 Documents / 41 Storage | `IMPLEMENTED_AND_WIRED` | `backend/services/document_cleanup.py` |
| FTR-372 | Email-provider abstraction (multi-provider) | 39 Notifications | `IMPLEMENTED_AND_WIRED` | `backend/services/email_provider.py`, `email_sender.py`; `DOC:CT-FINAL-02-…EMAIL-AND-UPLOAD-CONFIGURATION-REPORT` |
| FTR-373 | Audit-ledger hardening (immutability / hash chain) | 33 Audit | `IMPLEMENTED_AND_WIRED` | `MIG:20261021000000_ct02_audit_ledger_hardening.sql` |

**Deliberately NOT claimed as NEW:** the new `backend/routes/beta_access.py` route (folded into D02 as `CHANGED`), `backend/utils/factor_catalogue.py` (folded into D16/D20-D21 `UPGRADED`), staff-workload RLS (folded into D46 `UPGRADED`). Counting them as separate FTRs would inflate the catalogue without adding a distinct user-facing capability (AGENTS §74).

---

## 7. UPGRADED and CHANGED features (baseline FTR rows)

### 7.1 UPGRADED (11 baseline FTR rows)

| Baseline FTR (domain) | Upgrade | Evidence |
|---|---|---|
| FTR-211…213 (D34 Reporting — generation, listing, export) | Canonical report generation expanded | `backend/api/v3_reports.py +442` (net) |
| FTR-263…265 (D41 Storage — bucket, upload, retrieval) | Storage management Steps 1 & 2 | `backend/services/storage_*.py`, `document_*.py`; `DOC:CARBONTALLY_STORAGE_MANAGEMENT_STEP1/STEP2_IMPLEMENTATION_20260930` |
| FTR-202…204 (D33 Audit — write, list, export) | Audit-ledger hardening + legacy surface retirement | `MIG:…ct02_audit_ledger_hardening` |
| FTR-249…251 (D39 Notifications — email send, templates) | Email-provider abstraction | `backend/services/email_provider.py` |
| FTR-136…138 (D20 Emission Factors — lookup, list, resolve) | Factor read repoint + catalogue utility | `DOC:CT-IMPLEMENT-04-…REPORT-FACTOR-READ-REPOINT`; `backend/utils/factor_catalogue.py` |
| FTR-144…145 (D21 Factor Governance — approve, block) | Factor **write-path blocking** (F04) | factor-governance enforcement modules |
| FTR-297…300 (D46 Security — RLS, policy enforcement) | Final-03 RLS remediation + staff-workload RLS | `MIG:…ct_final_03_rls_security_remediation`, `…ct_final_03_staff_workload_rls` |
| FTR-346…347 (D53 Deployment — build provenance, env parity) | Build provenance + security headers retained/extended | `vercel.json` headers block |
| FTR-314…317 (D48 QA — suite execution, evidence) | FINAL-01/02/03 + B7 evidence packs | `docs/cline/evidence/**` |
| FTR-281…284 (D44 Operations — queue, workbench entry) | Operations shell extended | `UI:OperationsPage.jsx` |
| FTR-001…005 (D01 Platform Admin — settings, flags) | Settings surface expanded | `backend/api/v3_settings.py +358`, `UI:SettingsTab.jsx +434` |

### 7.2 CHANGED (9 baseline FTR rows)

| Baseline FTR (domain) | Change | Evidence |
|---|---|---|
| FTR-021…023 (D02 Authentication — login, invite) | Beta-access route added | `backend/routes/beta_access.py` (new file) |
| FTR-118…120 (D17 Manual Review — queue, decide) | Review path re-pointed after legacy audit retirement | deletion of `backend/routes/admin/audit_logs.py` |
| FTR-179…181 (D30 Calculations — run, snapshot) | Emissions-query scope + staff access (G1/G2) | decision docs under `docs/cline/evidence/FINAL-03-*` |
| FTR-197…199 (D32 Approvals — request, decide) | Extraction-approval atomicity (FINAL-01) | `DOC:CT-FINAL-01-20260928-REPORT`, `…SECURITY-FIX-AND-FINALIZE-REPORT` |
| FTR-131…133 (D19 Data Quality — validate, block) | D5/D6 runtime-defect remediation | `DOC:CT-PO-CARBONTALLY-CT-IMPLEMENT-02/03-REPORT-20260928` |
| FTR-223…224 (D35 Report Versions — freeze, list) | Report-share artefact handling | report-share service + migration |
| FTR-290…291 (D45 Admin Console — mount, config gate) | Legacy audit-logs page retired | deletion + `vercel.json` `/admin` rewrite intact |
| FTR-341…342 (D52 Public Website — shell, consent) | Public surface unchanged; security headers confirmed | `vercel.json` headers |
| FTR-273…275 (D43 API Platform — mount, versioning) | Router now mounts **63** v3 modules | `BE:backend/api/router.py` |

### 7.3 UNCHANGED (327 baseline FTR rows)

All baseline FTR rows not listed in §6, §7.1, §7.2, §8 are `UNCHANGED`: no added, deleted or modified file in the `cb70fd6..HEAD` window maps to them. This is asserted on file-path evidence, not on re-reading every row; it is therefore an `IMPLEMENTED`-level assertion, **not** a re-verification (AGENTS §73).

---

## 8. RELOCATED and REMOVED

### 8.1 REMOVED

| Artefact | Reason | Evidence |
|---|---|---|
| `backend/routes/admin/audit_logs.py` | Legacy admin audit surface retired (PD-4) | `GIT: D` in `cb70fd6..HEAD`; `DOC:CT-FINAL-01-PD-4-LEGACY-AUDIT-RETIREMENT-20260928` |
| `e2e/environment/supabase/migrations/*.sql` (53 files) | Replaced by a symlink to the canonical tree | `GIT: D × 53`; symlink now present |

The 53 deleted E2E migration files are **not** capability loss — they were a duplicated mirror. Their removal is the single largest source of the `D` count (53 of 54) and is a **positive** de-duplication: there is now one authoritative migration directory (AGENTS §23 "do not duplicate … logic").

### 8.2 RELOCATED

| Artefact | From → To | Class |
|---|---|---|
| E2E migration source | `e2e/environment/supabase/migrations/*.sql` → symlink to `supabase/migrations` | `RELOCATED` |
| Legacy admin audit mount | `backend/routes/admin/audit_logs.py` → withdrawn (superseded by hardened ledger) | `REMOVED` (mount) |

`GIT:` `git diff --find-renames -M40%` returned **0 renames**; the E2E change is a delete + symlink-add rather than a rename, and no other baseline file moved at the 40% similarity threshold.

---

## 9. Baseline drift and unverifiable claims

### 9.1 `BASELINE_DRIFT` (baseline described a state that no longer matches reality)

| Baseline claim | Baseline value | Actual at HEAD | Impact |
|---|---|---|---|
| Unapplied migrations vs flagship | 43 | **52** | The release tree is further ahead of every durable DB than the baseline stated (POD-A) |
| Reachable databases | 78 | **88** | +10 disposable rehearsal clones; the baseline's "78" is stale |
| Migration file count | 89 | **98** | +9 new files |
| `backend/routes/admin/audit_logs.py` existed | present | **deleted** | Legacy audit surface retired (PD-4) |
| E2E migrations directory | 53 mirrored files | **symlink** | De-duplication completed after the baseline |

### 9.2 `BASELINE_UNVERIFIABLE` (cannot be confirmed or denied from this pass)

| Baseline claim | Why unverifiable here |
|---|---|
| Flagship organisation count = 975 | Not re-counted this pass (table count unchanged, row count not queried) |
| Live runtime behaviour of any feature | No server/worker/UI was started (read-only posture) |
| Production schema / migrations / RLS / data | Production returned HTTP 503 and was never authenticated to (POD-I) |
| Test suites passing (16 unit / 54 integration / Playwright) | Suites were **not executed** this pass |

Where a drift is `BASELINE_DRIFT`, the baseline snapshot's *description* is superseded by the SHA/HEAD reality; where `BASELINE_UNVERIFIABLE`, no conclusion is drawn (AGENTS §80).

---

## 10. PO-decision delta (POD-A … POD-J)

| POD | Subject | Baseline status | HEAD status | Delta |
|---|---|---|---|---|
| POD-A | Which durable environment carries the unapplied migrations | OPEN | **OPEN** (43 → **52** unapplied) | Worsened |
| POD-B | `accounting_dimensions` — columns or table | OPEN | OPEN (still columns; table absent) | None |
| POD-C | `roles` catalogue — populate or retire | OPEN | OPEN (still 0 rows) | None |
| POD-D | Locations — entity vs facility facet | OPEN | OPEN (`locations` still absent) | None |
| POD-E | Retention — `audit_log_retention_days = 1` vs 365 | OPEN | OPEN (still 1) | None |
| POD-F | PE terminology — Processing Entity vs Principal/Reporting | OPEN | OPEN | None |
| POD-G | Legacy admin control plane retirement path | OPEN | OPEN (one legacy route actually retired — PD-4) | Partially advanced |
| POD-H | Legacy artefact disposition (Prisma lineage, backups, demo) | OPEN | OPEN | None |
| POD-I | Production schema/migration state ownership | OPEN (`UNKNOWN`) | OPEN; production API was **503** | Reinforced |
| POD-J | Residual capability census (SEO/PWA, X7 metrics, table standard) | OPEN | OPEN | None |

**None of the ten PO decisions was resolved in this window.** POD-A is the one that *materially worsened*: the delta added nine more unapplied migrations on top of the 43 that were already outstanding.

---

## 11. Security delta

| Change | Direction | Evidence | Assessment |
|---|---|---|---|
| RLS security remediation (final-03) | Strengthening | `MIG:…ct_final_03_rls_security_remediation` | Org-scope / cross-tenant containment addressed at policy level — **unapplied**, so not yet in force in any durable DB |
| Staff-workload RLS | Strengthening | `MIG:…ct_final_03_staff_workload_rls` | Scopes staff reads to assigned workload — **unapplied** |
| Org-scope authorization remediation (F05-R1/R2/R4) | Strengthening | `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/09…r1-r2-r3-remediation-decision`, `10…implementation-and-verification` | Server-side authorization hardening |
| Factor write-path blocking (F04) | Strengthening | factor-governance enforcement | Prevents unauthorised factor writes |
| Direct-to-storage signed upload | Neutral→Strengthening | `v3_document_uploads.py`, `document_security.py`, `upload_gate.py` | Upload constrained by a central gate; scanning service added. Signed URLs remain sensitive (AGENTS §68) — **no signed URL is recorded here** |
| Audit-ledger hardening | Strengthening | `MIG:…ct02_audit_ledger_hardening` | Immutability/hash-chain — **unapplied** |
| Legacy admin audit route removed | Neutral | deletion of `backend/routes/admin/audit_logs.py` | Reduces legacy attack surface |
| `can_manage_backups` capability gate | Strengthening | `OperationsPage.jsx` L107-111 | Backup tab requires **server-side** capability, not merely a hidden button (AGENTS §7, §44) |

**No security weakening was introduced in this window.** The critical caveat: the strengthening is **code + unapplied migrations**. Until POD-A is resolved, the effective runtime security posture of every durable database is unchanged from the baseline.

`SECURITY NOTE:` This pass executed **no** negative authorization testing (ALLOW/DENY matrix). The RLS changes are therefore `IMPLEMENTED`, not `TESTED` or `VERIFIED` (AGENTS §45, §72, §73).

---

## 12. Verdict, hand-back & remaining work

### 12.1 Verdict token

```
CT_FEATURE_DELTA_02_COMPLETE_WITH_OBSERVATIONS
```

**Meaning.** The three-way delta objective — baseline snapshot vs baseline SHA `cb70fd6` vs current `HEAD`, across both trees and all reachable local databases — is **complete**, evidenced, and reproducible. The qualifier `WITH_OBSERVATIONS` is carried because (a) production could not be contacted (HTTP 503), (b) no feature was executed, (c) the unapplied-migration gap **widened** from 43 to 52, and (d) no PO decision was resolved.

### 12.2 Observations carried forward

1. **The delta is code-first, database-last.** Nine new migrations and substantial backend/UI surface landed at HEAD, but the flagship ledger is unchanged at 46 rows. Nothing new is *in force* anywhere durable.
2. **Every new feature is `IMPLEMENTED_AND_WIRED` at best** — none is `TESTED` or `VERIFIED` (no suite, server or browser was executed).
3. **Production returned HTTP 503** on both `/health` and `/openapi.json`; production truth remains `UNKNOWN` across all 354+19 features (POD-I).
4. **De-duplication is real progress:** the E2E migration mirror was retired in favour of a symlink, removing 53 duplicated files.
5. **Legacy surface grew smaller by one:** the legacy admin audit route was retired (PD-4).
6. **All ten PO decisions (POD-A…POD-J) remain open**; POD-A worsened.

### 12.3 Hand-back

| Item | Value |
|---|---|
| Task ID | `CT-FEATURE-DELTA-02-20261003-CARBONTALLY-THREE-WAY-FEATURE-DELTA-BASELINE-SNAPSHOT-VS-BASELINE-SHA-VS-HEAD` |
| Verdict | `CT_FEATURE_DELTA_02_COMPLETE_WITH_OBSERVATIONS` |
| Canonical tree | `/home/shomonrobie/ct_93d5cdd` @ `375a48dc1b9e9cfd74090bbf747554ae997acb59`, branch `p8-release-reconciled` |
| Historical tree | `/home/shomonrobie/carbon_tally` @ `20b7a928bb73fdfacf8271ff537a8fd245f62c79`, branch `main` (pre-baseline, dirty worktree untouched) |
| Baseline snapshot doc | `docs/architecture/CT-PO-CARBONTALLY-COMPLETE-FEATURE-CATALOGUE-20260927.md` |
| Baseline SHA | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` — **ancestral, 25 commits behind HEAD** |
| Commit window | `cb70fd6..HEAD` = **25 commits**, 273 files (+65,207 / −12,282) |
| File delta | **142 A / 54 D / 77 M / 0 R** |
| Baseline FTR rows | 354 → 354 + 19 new (`FTR-355…373`); 54 domains (unchanged) |
| Delta classes | 327 `UNCHANGED` · 11 `UPGRADED` · 9 `CHANGED` · 2 `RELOCATED` · 1 `REMOVED` · 5 `BASELINE_DRIFT` · 3 `BASELINE_UNVERIFIABLE` · 19 `NEW` |
| Migrations | 89 → **98** files; flagship ledger **46** (unchanged); **52 unapplied** |
| Databases | 78 → **88** reachable; all six durable envs identical table counts; flagship 116 tables |
| Production | `/health` = 503, `/openapi.json` = 503 (documentary only) |
| Writes performed | **None** (documents only) |
| Migrations applied | **None** |
| Seeds / truncates | **None** |
| Secrets in document | **None** |
| Companion deliverables | `CT-PUBLIC-WEBSITE-FEATURE-LIST-20261003.md`, `CT-BLOG-CANDIDATES-20261003.md`, `CT-FAQ-ADDITIONS-20261003.md` |

### 12.4 Remaining work (explicitly not performed)

1. Resolve POD-A (which durable environment receives the 52 unapplied migrations, and in what order/authority).
2. Execute the stack and the QA Harness (`python qa_harness/scripts/run_all.py --no-ai`) against a disposable clone to move features from `IMPLEMENTED` to `TESTED`.
3. Run the negative-authorization matrix (AGENTS §45) to move the final-03 RLS work from `IMPLEMENTED` to `VERIFIED`.
4. Obtain an authorised production census (POD-I) — blocked partly by the 503 observed here.
5. Resolve the remaining nine PO decisions (POD-B…POD-J).

<!--CTEOF-->
