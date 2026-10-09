# CarbonTally — Database / Schema / Data / Provenance Reconciliation Ledger

**Task ID:** `CT-DB-RECON-01-20260927-CARBONTALLY-COMPLETE-DATABASE-DISCOVERY-AND-RECONCILIATION`
**Document:** 2 of 3 — Reconciliation Ledger
**Status:** DISCOVERY + FORENSIC RECONCILIATION ONLY. Nothing was consolidated, migrated,
seeded, repaired, reset, deleted or chosen as canonical by this task.
**Date:** 2026-09-27

## 0. How to read this ledger

Each row is an evidence-bounded statement about one capability, dataset, migration state,
artefact or configuration relationship. Rows deliberately do **not** decide what the
canonical database should be; they state what exists, where, with what provenance, and what
the reconciliation consequence is.

| Column | Meaning |
|---|---|
| **ID** | Stable id (`CAP-nn`, `DAT-nn`, `MIG-nn`, `ART-nn`, `CFG-nn`) |
| **CATEGORY** | Capability / Dataset / Migration-state / Artefact / Configuration |
| **DESCRIPTION** | The thing being reconciled |
| **DB SOURCE(S)** | Which discovered database(s) hold it (`INST-01` names; `INST-02`…`INST-07` where applicable) |
| **SCHEMA VERSION** | Public-table count / ledger state / migration generation |
| **ROW COUNT** | Exact count where readable, else `n/a` |
| **PROVENANCE** | Tooling/document that produced it + evidence class (DOCUMENTED / CODE / COMMAND EXECUTED / DATA-VERIFIED) |
| **FIRST / LAST EVIDENCE** | Earliest and latest evidence date found |
| **RECON STATUS** | `SHARED` · `LOCAL-ONLY` · `OTHER-DB-ONLY` · `LIVE-ONLY` · `SUPERSEDED` · `DUPLICATE` · `PARTIAL` · `CONFLICTING` · `UNKNOWN` |
| **PRODUCT VALUE** | Why the PO might care |
| **PROD SENSITIVITY** | Production-relevant? (Yes / No / Unknown) |
| **PO DECISION?** | `YES — PO`, `YES — reconcile first`, or `NO` |
| **EVIDENCE** | Artefact references |
| **CONFIDENCE** | VERIFIED / STRONGLY SUPPORTED / PLAUSIBLE / UNKNOWN |

## 1. Capability ledger

### CAP-01 — P17 accounting / governed capability catalogue (`scope3_categories` family)

| Field | Value |
|---|---|
| DB SOURCE(S) | **Only** 15 ephemeral INST-01 clones: `ct_p17_09_verify_20260925`, `ct_p17_10_verify_20260925`, `ct_p17_migcheck_20260925`, `ct_p17k_20260926`, `ct_p17k_ctl_20260926`, `ct_p17l_surface_20260926`, `ct_p17m_full_20260926`, `ct_p17m_nocat_20260926`, `ct_p17m_verify_20260926`, `ct_iv_p17m2_20260926`, `ct_iv_p17m2_clean_20260926`, `ct_iv_p17m_b_20260926`, `ct_iv_p17m_c_20260926`, `ct_m3_nocat_20260926153335`, `ct_m3_suite_20260926154500`, `ct_m3_verify_20260926153100` |
| SCHEMA VERSION | 145 public tables (vs 116 flagship / 141 Demo Lab / 135 `ct_local_93d5cdd`) |
| ROW COUNT | e.g. `ct_p17m_verify_20260926` 243 organisations, `ct_iv_p17m_c_20260926` 192; others 0–25 (fixture scale) |
| PROVENANCE | Repo B migrations `20261010000000_p17a…`, `20261011000000_p17c…`, `20261012000000_p17d…`, `20261013000000_p17h…`, `20261014000000_p17_10…`, `20261020000000_p17k…`, applied only to clone databases via `CREATE DATABASE … TEMPLATE …` (shell history 2026-09-26) |
| FIRST / LAST EVIDENCE | 2026-09-25 (earliest `ct_p17_*_verify`) / 2026-09-27 |
| RECON STATUS | **OTHER-DB-ONLY** (only in disposable clones) |
| PRODUCT VALUE | Highest-value unreleased capability; **has no home in any durable database** |
| PROD SENSITIVITY | **Unknown** — present in no observable environment |
| PO DECISION? | **YES — PO**: which durable database is authorised to receive the P17 generation |
| EVIDENCE | `db10_matrix_lines.txt` (15 rows `scope3_categories=T`); repo B migration filenames |
| CONFIDENCE | **VERIFIED** |

### CAP-02 — P16R disclosure / reportability generation

| Field | Value |
|---|---|
| DB SOURCE(S) | `carbontally_demo_local`, `ct_local_93d5cdd`, `carbontally_qa_phase8`, plus 20+ ephemeral `ct_*` clones; **absent** from `postgres` |
| ROW COUNT | `ct_local_93d5cdd`: 3 frameworks / 0 versions; `carbontally_qa_phase8`: 3 frameworks / **471** versions / **1069** requirements; `carbontally_demo_local`: 3 / 0 / 0; `ct_p17l_surface_20260926`: 103 / 212 |
| PROVENANCE | Repo B P8-era and P16/P16R migrations; `ct_local_93d5cdd` built 2026-09-19 by applying 67 migration files directly |
| FIRST / LAST EVIDENCE | 2026-09-14 (`carbontally_qa_phase8` rows) / 2026-09-27 |
| RECON STATUS | **SHARED** but **PARTIAL** — framework *versions* populated only in QA/ephemeral clones, zero in `ct_local_93d5cdd` and Demo Lab |
| PRODUCT VALUE | Core reporting/disclosure capability |
| PROD SENSITIVITY | **Unknown** (production not observable) |
| PO DECISION? | YES — reconcile first (which corpus is authoritative) |
| EVIDENCE | `db08_out.txt` (`P8_P16_OBJECT_MATRIX`), `db05_census_lines.txt` |
| CONFIDENCE | **VERIFIED** |

### CAP-03 — B2 evidence lineage (`evidence_line_items`, `source_line_item_id`)

| Field | Value |
|---|---|
| DB SOURCE(S) | `carbontally_demo_local` (67 rows), `carbontally_b2_clone_20260913` (62), `ct_b2_iv_20260913`, `ct_b4v4_20260914`, `ct_int_20260914`, `ct_x*`; `ct_local_93d5cdd` 0; **object absent entirely from `postgres`** |
| PROVENANCE | P8/B2 migration generation of repo B; `ct_local_93d5cdd` (67-migration build) |
| FIRST / LAST EVIDENCE | 2026-09-13 (`carbontally_b2_clone_20260913`) / 2026-09-27 |
| RECON STATUS | **SHARED / PARTIAL** — the flagship dataset has **no evidence store at all** |
| PRODUCT VALUE | Required for any provenance / emissions-traceability claim (AGENTS.md §17) |
| PROD SENSITIVITY | **Yes**, if any evidence claim is made about live data |
| PO DECISION? | YES — reconcile first |
| EVIDENCE | `db06_out.txt`, `db05_census_lines.txt` |
| CONFIDENCE | **VERIFIED** |

### CAP-04 — CarbonTally Insight (4 `carbontally_insight_*` tables)

| Field | Value |
|---|---|
| DB SOURCE(S) | **`carbontally_demo_local` only** among principals (plus `carbontally_test` and most P17 ephemarals). Absent from `postgres`, `ct_local_93d5cdd`, `carbontally_qa_phase8` |
| PROVENANCE | Insight migrations (`20260923000000_p8_insight_data_quality_reproducibility.sql`, `20261006000000_p8_insight_temporal_comparison.sql`, per shell history) |
| FIRST / LAST EVIDENCE | 2026-09-20 (Demo Lab provisioning) / 2026-09-27 |
| RECON STATUS | **OTHER-DB-ONLY** relative to the flagship and to the 25-org DB |
| PRODUCT VALUE | Investor-facing Insight capability — demoable only in the Demo Lab database |
| PROD SENSITIVITY | Unknown |
| PO DECISION? | YES — reconcile first (which environment is the Insight evidence environment) |
| EVIDENCE | `db06_out.txt` (`carbontally_insight_conversations` matrix), `db10_matrix_lines.txt` |
| CONFIDENCE | **VERIFIED** |

### CAP-05 — Manual-processing grants (`manual_processing_grants`)

| Field | Value |
|---|---|
| DB SOURCE(S) | `carbontally_demo_local`, `ct_local_93d5cdd`, plus ephemarals; **absent** from `postgres` and `carbontally_qa_phase8` |
| RECON STATUS | **PARTIAL** |
| PO DECISION? | YES — reconcile first |
| CONFIDENCE | **VERIFIED** |

### CAP-06 — Multi-generation billing / subscription tables

| Field | Value |
|---|---|
| DB SOURCE(S) | `postgres` has the D37 generation (`billing_commercial_config`, `billing_credit_ledger`, `billing_idempotency_keys`, `billing_orders`, `billing_payment_records`, `billing_plans`, `billing_storage_usage`, `customer_subscriptions`) with `billing_plans` populated; every other principal DB also carries `billing_plans` |
| RECON STATUS | **SHARED** (schema) / **PARTIAL** (data) |
| PO DECISION? | NO for discovery; **YES — PO** before any billing-data consolidation |
| EVIDENCE | `db05_tables_ext.txt`, `db08_out.txt` |
| CONFIDENCE | **VERIFIED** |

### CAP-07 — Authenticated messaging domain (`conversations`, `messages`, `notifications`, `message_activity_log`)

| Field | Value |
|---|---|
| DB SOURCE(S) | All six principals; `postgres` carries real messaging rows (34 conversations / 52 messages per Phase-5 reports), Demo Lab and `ct_local_93d5cdd` carry schema with little/no data |
| RECON STATUS | **SHARED (schema)** / **PARTIAL (data)** |
| PO DECISION? | NO for discovery |
| CONFIDENCE | **VERIFIED** (schema), STRONGLY SUPPORTED (flagship row counts from reports) |

### CAP-08 — Supabase Auth data model (`auth` schema)

| Field | Value |
|---|---|
| DB SOURCE(S) | **Present**: `postgres` (23 tables; `auth.users` 1,206; `auth.identities` 1,206), `carbontally_demo_local` (23; 14 users; **0 identities**), `carbontally_qa_phase8` (23), `carbontally_b2_clone_20260913` (23), `carbontally_test` (**absent**), `ct_local_93d5cdd` (**absent**) |
| RECON STATUS | **PARTIAL / CONFLICTING** — the two databases the two repositories actually point at (`postgres` for repo A, `ct_local_93d5cdd` for repo B) have **different auth capability**: full vs none |
| PRODUCT VALUE | Any login / `auth.uid()` RLS / identity-based test is impossible against `ct_local_93d5cdd` |
| PROD SENSITIVITY | Yes |
| PO DECISION? | **YES — PO**: is a Supabase-Auth-bearing local environment required, and which database should carry it? |
| EVIDENCE | `db06_out.txt` (`AUTH` section), `db05_census_lines.txt` (`auth_tables`) |
| CONFIDENCE | **VERIFIED** |

### CAP-09 — Storage buckets / objects

| Field | Value |
|---|---|
| DB SOURCE(S) | `postgres`: bucket `documents` (private), **685 objects**. `carbontally_demo_local`: buckets `documents` **and** `report-artifacts`, 38 objects. `ct_local_93d5cdd`: 1 bucket, object count not enumerated (bucket row present). `carbontally_test`: 1 bucket. Ephemeral clones: 0–1 bucket each |
| RECON STATUS | **CONFLICTING** — the flagship's 685 document objects exist in a schema generation that cannot record report artifacts |
| PROD SENSITIVITY | **Yes** (documents are tenant data) |
| PO DECISION? | YES — reconcile first; storage rows are **not** to be deleted |
| EVIDENCE | `db08_out.txt` (`STORAGE`), `db10_matrix_lines.txt` (`buckets=`) |
| CONFIDENCE | **VERIFIED** |

### CAP-10 — Operational processing pipeline tables

(`document_processing_queue`, `processing_queue`, `manual_extraction_items`,
`calculation_snapshots`, `emissions_logs`, `report_versions`)

| Field | Value |
|---|---|
| DB SOURCE(S) | All principals. `postgres`: extraction items 264, manual review queue 2, snapshots 100, emissions 100, report versions 17, generation queue 14, processing entities 11. `carbontally_demo_local`: 38 / 0 / 34 / 34 / 4 / 4 / 2. `ct_local_93d5cdd`: 1 / 0 / 0 / 0 / 0 / 0 / 7 |
| RECON STATUS | **SHARED (schema)**; **CONFLICTING (data)** — real pipeline output exists only in `postgres`, whose schema lacks the evidence/artifact generations |
| PO DECISION? | YES — reconcile first |
| CONFIDENCE | **VERIFIED** |

### CAP-11 — Master data (facilities / assets / vehicles / suppliers)

| Field | Value |
|---|---|
| DB SOURCE(S) | `postgres`: facilities **157**, assets **310**, vehicles **3**, suppliers **156** (+ `supplier_categories`). `carbontally_demo_local`: 1 / 1 / 0 / 1. `ct_local_93d5cdd`: 0 / 0 / 0 / 0. Ephemeral P17 clones: suppliers up to 63 (`ct_iv_p17m_c_20260926`), 35 (`ct_p17_09_verify_20260925`) |
| RECON STATUS | **LOCAL-ONLY in the flagship**; empty/`SUPERSEDED` elsewhere — the D17 master-data capability is only meaningfully populated in the 116-table database |
| PRODUCT VALUE | D17 master data is a first-class product feature |
| PO DECISION? | YES — reconcile first (master-data migration into a modern-schema database is a PO decision, not an implementation detail) |
| EVIDENCE | `db05_census_lines.txt`, `db10_matrix_lines.txt` |
| CONFIDENCE | **VERIFIED** |

## 2. Dataset ledger

### DAT-01 — 7,049 emission factors (`postgres`)

| Field | Value |
|---|---|
| DB SOURCE(S) | `postgres` (INST-01) — the dataset visible through the Supabase API/Studio today |
| ROW COUNT | **7,049** (row-id hash `93668772ba460b0d03c7d9f9029f16c9`; content hash `eefbcf6e3d26ea6d908bac182fe4a309`) |
| PROVENANCE | Generated idempotent SQL import (`output/sql/emission_factors.sql` DEFRA + `output/seai_2025/sql` SEAI), **not** a migration and **not** the investor-demo seed: all 7,049 rows have `import_batch_id IS NULL` and `import_batches` is empty. `reporting_year = 2025`; sets DEFRA-2025 = 7,029 and SEAI-2025 = 20 (preservation evidence). Rows created **2026-08-26 14:04:22–14:04:26Z** |
| FIRST / LAST EVIDENCE | 2026-08-15 (generation of the SQL per `output/reports/import_summary.md`) / 2026-09-27 |
| RECON STATUS | **DUPLICATE (content) with `carbontally_demo_local`** — identical content hash, different row ids |
| PRODUCT VALUE | The factor library is the basis of all calculation |
| PROD SENSITIVITY | **Yes** — the same 7,049 count is reported for production |
| PO DECISION? | YES — reconcile first (must this dataset be preserved into the canonical environment?) |
| EVIDENCE | `db06_out.txt`, `db14_out.txt`, `carbontally_preservation_20260916/preservation_evidence.json`, `docs/audit/cline/CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md`, `docs/cline/CarbonTally-SEAI-Provider-Implementation-v1.0.md` |
| CONFIDENCE | **VERIFIED** (counts, timestamps, hashes, batch nulls) |

### DAT-02 — 7,049 emission factors (`carbontally_demo_local`)

| Field | Value |
|---|---|
| ROW COUNT | **7,049** (row-id hash `e7c28218636fc5fee2ddb79bd1058312` — **different ids**) |
| PROVENANCE | Demo Lab factor import: `tools/demo_lab/seed_factors.py` + `ct_local_env/demo_lab/factor_import/`; `import_batch_id` set on every row; `import_batches` = 2. Rows created **2026-09-24 10:15:16–10:15:20Z** |
| RECON STATUS | **DUPLICATE (content-identical, independently imported)** |
| PO DECISION? | YES — reconcile first (only one factor library should survive into the canonical environment) |
| EVIDENCE | `db06_out.txt`, `db14_out.txt`, `ct_local_env/demo_lab/factor_import/` |
| CONFIDENCE | **VERIFIED** |

### DAT-03 — 7,029-factor DEFRA-only clones (`ct_v078_t2b`, `ct_v078_t2b_tests`)

| Field | Value |
|---|---|
| ROW COUNT | 7,029 each (content hash `b50c9f4f8fa02e166c25bfdb761d3b73`; `import_batch_id` set) |
| PROVENANCE | V0.7.8 T2B verification era — the pre-SEAI state |
| RECON STATUS | **SUPERSEDED** by the 7,049 sets |
| PO DECISION? | NO — but do **not** delete (7,029-row working copies of factor data) |
| CONFIDENCE | **VERIFIED** |

### DAT-04 — 975 organisations + identities (`postgres`)

| Field | Value |
|---|---|
| DB SOURCE(S) | **`postgres` only** — no other discovered database contains this dataset |
| ROW COUNT | organisations **975**; `auth.users` **1,206**; `auth.identities` **1,206**; `public.users` **1,344**; `organization_members` **1,125**; `consultant_clients` **917**; `consultant_profiles` **55**; `consultant_firm_members` **54**; `staff_profiles` **21**; `processing_entities` **11** |
| PROVENANCE | Investor-demo seeding into INST-01 via `tools/seed_investor_demo/` (GoTrue admin API + PostgREST; default target `http://127.0.0.1:54425`; local-safety guard `assert_local_environment`). Organisation rows created **2026-08-22 16:53:32Z → 2026-08-28 22:42:27Z**. The manifest `DEMO_IDENTITIES.md` records the verified post-seed state (2026-08-28): users 1,325; organisations **976**; consultant–client assignments 916; client organisations 911; memberships 1,127; 11 processing entities; **1,185 demo identities** |
| FIRST / LAST EVIDENCE | 2026-08-22 (earliest organisation row) / 2026-09-27 |
| RECON STATUS | **LOCAL-ONLY**, with **CONFLICTING counts**: manifest 976 orgs / 1,325 users vs current 975 orgs / 1,206 `auth.users` / 1,344 `public.users`. Both observations are preserved; the drift is unexplained → **REQUIRES_RECONCILIATION** (candidates: later fixture organisations, auth-user cleanup, or a partial re-seed) |
| PRODUCT VALUE | The only investor-scale persona dataset in the environment; the population behind Cline/OHD persona QA and the DEMO_IDENTITIES manifest |
| PROD SENSITIVITY | **No** — explicitly local-only tooling with a local-environment guard |
| PO DECISION? | **YES — PO**: protect; do not blindly migrate; AGENTS.md §55 forbids resetting, truncating or globally modifying it |
| EVIDENCE | `db05_census_lines.txt`, `db06_out.txt` (`ORGS`, `AUTH`), `tools/seed_investor_demo/DEMO_IDENTITIES.md`, `docs/cline/reports/CT-OPS-LOCAL-PLATFORM-MANUAL-TEST-START-20260912-001.md` ("the `carbon_ledger` database holds the investor demo dataset (975 organisations)"), `docs/architecture/CT-PO-COMPREHENSIVE-INVESTOR-READY-PLATFORM-STUDY-20260924.md` (975 orgs, 116 tables, legacy schema) |
| CONFIDENCE | **VERIFIED** (present state, counts, timestamps); **STRONGLY SUPPORTED** (that `seed_investor_demo` produced it) |

### DAT-05 — 25-organisation dataset A (`ct_local_93d5cdd`) — the READINESS-02 database

| Field | Value |
|---|---|
| DB SOURCE(S) | `ct_local_93d5cdd` (INST-01) |
| ROW COUNT | organisations **25**; `public.users` **658**; `organization_members` **16**; `emission_factors` **0**; `customer_factors` 5; `processing_entities` 7; `consultant_profiles` 3; `consultant_clients` 3; `staff_profiles` 5; `manual_extraction_items` 1 |
| PROVENANCE | Created 2026-09-19 by the isolated local-run task (`ct_local_env/README.md`: "Task: CT-STEP2-LOCAL-LATEST-RUN-WITHOUT-BASELINE-072"; database "`ct_local_93d5cdd` (disposable)", the target of repo B's `backend/.env`; 135 public tables, 67 migrations applied, 218 RLS policies). Organisation rows created **2026-09-19 03:43:07Z – 13:00:36Z** |
| FIRST / LAST EVIDENCE | 2026-09-19 / 2026-09-27 (this census; also READINESS-02) |
| RECON STATUS | **LOCAL-ONLY**; the "25 orgs / 0 factors" signature is **also matched by a second database** (DAT-06) → **CONFLICTING** attribution risk |
| PRODUCT VALUE | The database the current canonical repository actually points to; the environment READINESS-02 measured |
| PROD SENSITIVITY | **No** (disposable by design; contains test fixtures only) |
| PO DECISION? | **YES — PO**: decide whether this disposable DB remains the target of future verification, or whether verification must move to a modern-schema database |
| EVIDENCE | `db05_census_lines.txt`, `db08_out.txt`, `ct_local_env/README.md`, READINESS-01 report |
| CONFIDENCE | **VERIFIED** |

### DAT-06 — 25-organisation dataset B (`carbontally_qa_phase8`)

| Field | Value |
|---|---|
| DB SOURCE(S) | `carbontally_qa_phase8` (INST-01) |
| ROW COUNT | organisations **25** (all `Test Co`/`System`); `public.users` **498**; `emission_factors` **0**; disclosure **471** framework versions / **1069** requirement versions; `report_generation_queue` 15; `report_versions` 3 |
| PROVENANCE | Phase-8 QA dataset; organisation rows created **2026-09-14 08:52:54Z** (five days before DAT-05) |
| RECON STATUS | **DUPLICATE / CONFLICTING** with DAT-05 — identical 25-organisation naming pattern, different dates, different users, different disclosure corpus. This census **cannot** determine whether DAT-05 was derived from this database, from a shared seed script, or created independently |
| PO DECISION? | **YES — reconcile first**: two distinct "25-organisation datasets" exist and only one is described by READINESS-02 |
| EVIDENCE | `db05_census_lines.txt`, `db08_out.txt` (`ORG_NAMES_25`) |
| CONFIDENCE | **VERIFIED** (both datasets exist); **UNKNOWN** (their mutual derivation) |

### DAT-07 — 4-organisation Demo Lab dataset (`carbontally_demo_local`)

| Field | Value |
|---|---|
| ROW COUNT | organisations 4 (`Demo Lab Client A`, …); `public.users` 14; `auth.users` 14; `auth.identities` **0**; documents 38; calculations 34; evidence 67; report versions 4 |
| PROVENANCE | `tools/demo_lab` provisioning + P12 canonical corpus (`ct_local_env/demo_lab/corpus/p12-canonical-demo-v1`, `t3-uk-curated-v1`); organisation rows created 2026-09-24 10:15:08Z |
| RECON STATUS | **LOCAL-ONLY**; the only durable database carrying the Insight + P16R + B2 + manual-grant generations |
| PO DECISION? | YES — reconcile first (candidate evidence environment for modern-schema journeys) |
| EVIDENCE | `db05_census_lines.txt`, `ct_local_env/demo_lab/evidence/*`, `docs/architecture/CT-PO-P12-STEP2-IMPLEMENTATION-REPORT-20260924.md` |
| CONFIDENCE | **VERIFIED** |

### DAT-08 — Production dataset (`INST-07`, owner-reported)

| Field | Value |
|---|---|
| ROW COUNT | organisations **2**; `emission_factors` **7,049** (owner-supplied only) |
| PROVENANCE | Product Owner observation; **no independent evidence obtained in this task** |
| FIRST / LAST EVIDENCE | 2026-09-27 (owner statement) vs 2026-09-11 (recon: host NXDOMAIN; state UNKNOWN) |
| RECON STATUS | **LIVE-ONLY / UNKNOWN** |
| PROD SENSITIVITY | **Yes** |
| PO DECISION? | **YES — PO**: authorise (or decline) an authorised read-only production inspection |
| EVIDENCE | task §1; `CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md` |
| CONFIDENCE | **PLAUSIBLE** (owner-supplied, unverified here) |

### DAT-09 — Other non-empty datasets in principals and clones

| DB | Notable data |
|---|---|
| `carbontally_b2_clone_20260913` | 35 orgs, 87 users, 37 report versions, 62 evidence rows, 2 factors |
| `carbontally_test` | 748 `public.users`, 3 orgs, 2 customer factors (volatile — `TRUNCATE`d by the harness) |
| `ct_iv_p17m_c_20260926` | **192 orgs**, 63 suppliers, 59 emissions logs — largest fixture dataset outside the flagship |
| `ct_p17m_verify_20260926` | **243 orgs**, 16 factors |
| `ct_int_20260914` | 87 orgs, 585 users, 75 report versions, 51 memberships |
| `ct_b2_iv_20260913` | 154 orgs, 20 memberships, 14 processing entities, 13 customer factors |
| `ct_p17_09_verify_20260925` / `ct_p17_10_verify_20260925` | 110 orgs each, 35 suppliers, 37 emissions logs |
| `ct_iv066_api` | 47 orgs, 686 users, 19 memberships |
| `ct_iv_replay_20260916` | 97 tables, **0 RLS policies** (deliberately un-policied replay) |

RECON STATUS for all of DAT-09: **EPHEMERAL** fixtures — disposable verification clones,
not canonical data.

## 3. Migration-state ledger

| ID | DESCRIPTION | DB | LEDGER | OBJECT EVIDENCE | RECON STATUS | PO DECISION? | CONFIDENCE |
|---|---|---|---|---|---|---|---|
| MIG-01 | Canonical migration set | repo B `supabase/migrations` | — | 89 files, max `20261020000000_p17k…` | **SOURCE OF TRUTH (candidate)** | YES — PO to ratify | VERIFIED |
| MIG-02 | Baseline migration set | repo A `supabase/migrations` | — | 68 files, max `20260924000000_p8x_x2_…` | **SUPERSEDED** by MIG-01 | NO | VERIFIED |
| MIG-03 | Applied migrations of `postgres` | `postgres` | 46 rows, max `20260903010000_ws4_gate3_4a_…` | 116 tables | **PARTIAL** (stale by ~3 weeks + all P8/P16/P17 work) | YES — reconcile first | VERIFIED |
| MIG-04 | Applied migrations of `ct_local_93d5cdd` | `ct_local_93d5cdd` | none | 135 tables, 218 policies; README records 67 applied | **CONFIRMED_APPLIED 67 (documented + object-corroborated)** | NO | STRONGLY SUPPORTED |
| MIG-05 | Applied migrations of `carbontally_demo_local` | `carbontally_demo_local` | none | 141 tables incl. Insight/P16R/B2 | **OBJECTS_PRESENT_APPLICATION_TIME_UNKNOWN** | YES — reconcile first | VERIFIED (objects) / UNKNOWN (provenance of application) |
| MIG-06 | P17 generation applied anywhere durable | none | — | only 15 `ct_*` clones | **OTHER-DB-ONLY (disposable)** | **YES — PO** | VERIFIED |
| MIG-07 | Repo-side migration drift | repo A + repo B | — | READINESS-01: 0 anomalies in the repo comparator | **CLEAN** | NO | VERIFIED (prior task) |
| MIG-08 | CI drift gate | `.github/workflows/migration-drift.yml` | — | READINESS-01: actionlint rejects the step `if:` at line 47 → workflow never runs | **INERT** (carried forward from READINESS-01; not re-tested here) | YES — PO (evidence environment for ledger comparison) | VERIFIED (prior task) |

## 4. Artefact ledger (data-bearing files that are **not** live databases)

| ID | ARTEFACT | CONTENTS | EVIDENCES A DATABASE? | RECON STATUS | PO DECISION? | CONFIDENCE |
|---|---|---|---|---|---|---|
| ART-01 | `~/carbontally_db_backups/carbontally_dev_20260901T125134.dump` + `.sql` | Dump "from database version 17.6", 2026-09-01 12:51 (+06) | **Yes** — a database named **`carbontally_dev`** that no longer exists in INST-01 | **ORPHAN / requires identification** | **YES — PO** (what was `carbontally_dev`, and does anything in it matter?) | VERIFIED (header) |
| ART-02 | `carbon_tally/backups/carbontally_v3_verified_2026-08-14.dump` | 2026-08-14 v3 verified dump (0.97 MB) | Yes — a 2026-08-14 state | **HISTORICAL** | NO | VERIFIED |
| ART-03 | `local_backups/carbon_tally_live_public_schema.sql` + `…_live_public_data.sql` (2026-08-20) | Live/hosted public schema (232 KB) + data (1.86 MB) | **Yes** — the live schema restored into the local DB | **LIVE-ONLY (historic capture)** | YES — reconcile first | VERIFIED |
| ART-04 | `local_backups/local_before_live_data_restore.sql` | Pre-restore local snapshot | Yes | **HISTORICAL BASELINE** | NO | VERIFIED |
| ART-05 | `carbontally_preservation_20260916/emission_factors.*` + `preservation_evidence.json` | 7,049-factor preservation copy + hashes/evidence | Yes (factor library) | **PRESERVATION COPY** | NO — must be retained | VERIFIED |
| ART-06 | `carbon_tally/backups/seed.sql` = `ct_93d5cdd/backups/seed.sql` = `supabase/seed.sql` (7.3 MB) | Repository seed payload; `[db.seed] enabled = false` in both configs | Not proven applied anywhere | **DORMANT** | NO | VERIFIED (files identical in size; content not diffed) |
| ART-07 | `CarbonTally_DB_Schema_V3M2.sql` (244 KB, repo A), `v3_schema.sql` (232 KB, repo A), `schema.sql`, `ct_93d5cdd/database/{rc1,rc2,v3}` | Schema text snapshots | Design artefacts | **HISTORICAL** | NO | VERIFIED |
| ART-08 | `carbon_tally/.tmp_pgdata` (Windows PG18 cluster, 3 databases, 35 MB) | A complete Windows-era cluster data directory | **Yes** — pre-Linux development cluster | **ORPHAN / preserved artefact** | **YES — PO** (retain or formally retire; do not delete blindly) | VERIFIED (structure) / UNKNOWN (contents) |
| ART-09 | `e2e/environment/.env.e2e`, `.env.personas`, `tests/e2e/.env.personas` | E2E environment/persona configurations | Configures INST-02 | **CONFIG-ONLY** | NO | VERIFIED |
| ART-10 | `output/sql/emission_factors.sql` (DEFRA), `output/seai_2025/sql`, `output/json|reports/*` | The **generated factor import SQL** + source statistics | Yes — the mechanism that created DAT-01 | **SOURCE OF DAT-01** | NO | VERIFIED (code) + docs |

## 5. Configuration / target ledger

| ID | CONFIGURATION | TARGET | RECON STATUS | PO DECISION? | CONFIDENCE |
|---|---|---|---|---|---|
| CFG-01 | `carbon_tally/supabase/config.toml` (`project_id = carbon_ledger`, ports 5442x, migrations disabled) | INST-01, database `postgres` | **ACTIVE** (matches the running stack) | NO | VERIFIED |
| CFG-02 | `ct_93d5cdd/supabase/config.toml` (`project_id = carbon_ledger`, ports 5432x, migrations **enabled**) | The *same* INST-01 volume, addressed on different ports | **CONFLICTING (same project id, different ports)** — `REQUIRES_RECONCILIATION` | **YES — PO** (port/project convention must be fixed so CI and humans never address the wrong DB) | VERIFIED |
| CFG-03 | `carbon_tally/.env` (root) | `:54326/postgres` — **not listening** | **STALE** | NO | VERIFIED |
| CFG-04 | `carbon_tally/backend/.env` | `:54426/postgres` (975-org flagship) | **ACTIVE** | NO | VERIFIED |
| CFG-05 | `ct_93d5cdd/backend/.env` | `:54426/ct_local_93d5cdd`; Supabase URL deliberately unroutable (:19999) | **ACTIVE for repo B**; Supabase-Auth unavailable by design | YES — reconcile first | VERIFIED |
| CFG-06 | `ct_local_env/demo_lab/backend.env` | `:54426/carbontally_demo_local`; gateway :54430 | **ACTIVE (Demo Lab)** | NO | VERIFIED |
| CFG-07 | `carbon_tally/e2e/environment/supabase/config.toml` = `ct_93d5cdd/…` (`carbontally_e2e`, ports 5532x) | INST-02 (stopped) | **DORMANT** | YES — PO (retain or retire the E2E environment) | VERIFIED |
| CFG-08 | Integration harness `INTEGRATION_DATABASE_URL` default `:54326/carbontally_test` + **destructive `TRUNCATE … CASCADE`** with F-046-1 guard | `carbontally_test` (INST-01) | **DANGEROUS BY DESIGN, GUARDED** — must never be pointed at a data-bearing DB | **YES — PO** (make the default a disposable clone) | VERIFIED |

## 6. N-way reconciliation matrix (no winner selected)

Legend: **●** holds it · **◐** partial/empty-but-present · **○** absent · **?** unknown.

| Capability / dataset | `postgres` | `carbontally_demo_local` | `ct_local_93d5cdd` | `carbontally_qa_phase8` | `carbontally_test` | `carbontally_b2_clone_20260913` | 70 `ct_*` clones | INST-02 | INST-04/05 | INST-07 |
|---|---|---|---|---|---|---|---|---|---|---|
| Investor-scale organisations (975) | ● | ○ | ○ | ○ | ○ | ○ | ○ | ? | ? | ○ (2 orgs) |
| Factor library 7,049 | ● | ● | ○ | ○ | ○ | ◐ (2) | ◐ (7,029 ×2) | ? | ? | ● (owner-reported) |
| P16 disclosure | ○ | ● | ● | ● | ? | ● | ● | ? | ? | ? |
| P16R artifacts | ○ | ● | ● | ● | ? | ● | ● | ? | ? | ? |
| B2 evidence lineage | ○ | ● | ● | ● | ? | ● | ● | ? | ? | ? |
| Insight | ○ | ● | ○ | ○ | ● | ○ | ● | ? | ? | ? |
| Manual-processing grants | ○ | ● | ● | ○ | ? | ○ | ● | ? | ? | ? |
| P17 accounting | ○ | ○ | ○ | ○ | ○ | ○ | ● (15) | ? | ? | ? |
| Supabase Auth data model | ● | ● | **○** | ● | ○ | ● | mostly ● | ? | ? | ? |
| Master data (facilities/assets/suppliers) | ● | ◐ | ○ | ○ | ○ | ○ | ◐ | ? | ? | ? |
| Pipeline output (documents → reports) | ● | ◐ | ◐ | ○ | ○ | ◐ | ◐ | ? | ? | ? |
| Messaging domain data | ● | ○ | ○ | ○ | ○ | ○ | ○ | ? | ? | ? |
| Storage objects | ● (685) | ◐ (38) | ◐ | ○ | ◐ | ○ | ◐ | ? | ? | ? |
| Migration ledger | ● (46) | ○ | ○ | ◐ (0 rows) | ○ | ◐ (0 rows) | ○ | ? | ? | ? |
| Repo B 89-migration generation | ○ | ◐ | ◐ | ◐ | ○ | ◐ | ◐ | ? | ? | ? |

**Read-only conclusions (no winner):**

1. No single database is a superset. `postgres` has the data but the oldest schema;
   `carbontally_demo_local` has the newest durable schema but trivial data;
   `ct_local_93d5cdd` has the schema the canonical repository targets but **no factors and
   no auth**; the P17 generation exists nowhere durable.
2. The reconciliation is therefore a **schema + data merge problem**, not a "pick one
   database" problem. Consolidation is explicitly out of scope for this task and requires a
   PO decision on the target environment.

## 7. Items requiring a PO decision before any consolidation

| # | Decision required | Why it is not an implementation decision |
|---|---|---|
| PD-1 | Which database is authorised to become the canonical local/development target | Only the PO can authorise replacing the database that currently holds the 975-organisation investor dataset (AGENTS.md §55) |
| PD-2 | Whether the 975-organisation dataset must be **preserved in place** or **carried forward** into a modern-schema database | Migration of investor-demo data changes what persona QA and OHD observe |
| PD-3 | Which environment is the authorised **evidence environment** for P16R/Insight/P17 verification | Carries forward an open READINESS-01 item; determines which DB must receive those generations |
| PD-4 | Whether a local **Supabase-Auth-bearing** database is required (and which) | `ct_local_93d5cdd` has **no `auth` schema**, so authenticated/RLS E2E cannot be validated there |
| PD-5 | The port/project convention for `carbon_ledger` (5432x vs 5442x; migrations enabled vs disabled) | Prevents CI or a human from addressing the wrong database after a `supabase start` in the wrong repository |
| PD-6 | What `carbontally_dev` was, and whether its 2026-09-01 dump must be preserved | An orphan dump of a database that no longer exists |
| PD-7 | Whether the 35 MB Windows-era `D:/carbon_ledger/.tmp_pgdata` (3 databases) is retained or formally retired | Contains a development dataset that cannot be read without starting it |
| PD-8 | Whether the stopped `carbontally_e2e` cluster and `ct_p3_verify_pg` container are retained, retired or re-used as disposable targets | Both are stopped, un-inspected, and hold unknown data |
| PD-9 | Whether production inspection is authorised (to resolve DAT-08 / INST-07) | Production state is currently owner-evidence only |
| PD-10 | Whether the integration-harness default (`carbontally_test` + destructive `TRUNCATE`) must become a disposable `ct_*` clone | Safety of future test runs (F-046-1 invariant) |

## 8. Items that must NOT be changed, reset or deleted (protection list)

1. `postgres` (INST-01) — the 975-organisation investor dataset, 7,049 factors, 1,206 auth
   identities, 685 storage objects, 1,125 memberships, 917 consultant-client links.
2. `carbontally_demo_local` — Demo Lab database (4 orgs, 7,049 factors, Insight/P16R/B2
   schema, 38 storage objects).
3. `ct_local_93d5cdd` — the READINESS-02 database and the target of the canonical
   repository's `backend/.env`; the only source of the recorded 25-org observation.
4. `carbontally_qa_phase8` — the only populated P16R disclosure corpus
   (471 framework versions / 1,069 requirement versions) among durable databases.
5. `carbontally_test` — the integration-test database (must stay isolated; it must never
   receive investor data, and nothing that matters may ever be pointed at it).
6. `carbontally_b2_clone_20260913` — 35 orgs / 37 report versions / 62 evidence fixtures.
7. All 70 `ct_*` clones — evidence of verification runs. Classify as
   **`CANDIDATE_FOR_CLEANUP` only**, and only after PD-3/PD-8 are decided. This task
   touched none of them.
8. Docker volumes `supabase_db_carbon_ledger`, `supabase_db_carbontally_e2e`,
   `carbontally_demo_lab_storage`.
9. The stopped containers `supabase_db_carbontally_e2e` (+ full E2E stack) and
   `ct_p3_verify_pg` (no volume — its data exists only in that container layer).
10. `carbon_tally/.tmp_pgdata` — the Windows-era cluster data directory.
11. `~/carbontally_db_backups/carbontally_dev_20260901T125134.{dump,sql}`,
    `carbon_tally/backups/*`, `carbon_tally/local_backups/*`,
    `carbontally_preservation_20260916/*`.
12. `INST-04` host PostgreSQL 18 data (`/var/lib/postgresql/18/main`) — unidentified; must
    not be assumed disposable.
13. `tools/seed_investor_demo/*` and its manifest — the only description of the investor
    dataset's intended population.

## 9. Provenance confidence summary

| Statement | Confidence |
|---|---|
| INST-01 hosts 78 logical databases; six are principal | **VERIFIED** |
| `postgres` holds 975 orgs / 7,049 factors and serves the Supabase API | **VERIFIED** |
| `ct_local_93d5cdd` is the READINESS-02 database (25 orgs / 0 factors), in the **same cluster** as `postgres` | **VERIFIED** |
| Two databases hold 7,049 factors with **identical content** but different row ids | **VERIFIED** (content hashes equal) |
| The 7,049 factors came from generated SQL imports — not migrations, not the demo seed | **VERIFIED** (`import_batch_id IS NULL` for all rows; `import_batches` empty; matching docs) |
| The 975-organisation dataset came from `tools/seed_investor_demo` | **STRONGLY SUPPORTED** (manifest + document quotes + row timestamps; the exact seeding command line was not recovered) |
| `ct_local_93d5cdd` was created 2026-09-19 by the isolated local-run task | **STRONGLY SUPPORTED** (`ct_local_env/README.md` + row timestamps + `.env`) |
| `carbontally_demo_local` was created by `tools/demo_lab` | **STRONGLY SUPPORTED** (tooling + container env + row timestamps) |
| INST-02 / INST-03 / INST-04 / INST-05 contents | **UNKNOWN** (not inspected, by safety boundary) |
| Production state | **UNKNOWN / owner-evidence only** |
| Mutual derivation of the two 25-organisation datasets | **UNKNOWN** |
| Whether `carbontally_dev` was ever a live database | **STRONGLY SUPPORTED** (dump header) but not catalogue-verifiable |

## 10. Ledger limitations

* Everything here describes **INST-01 as observed on 2026-09-27 13:09–13:24 (+06)**. The 70
  ephemeral clones are a moving population; a future census may show more or fewer.
* Row counts are point-in-time `SELECT count(*)` values without snapshot isolation, so a
  concurrently running process could shift a count slightly. Two catalogue passes minutes
  apart agreed exactly on the database list, which suggests the environment was quiescent.
* No production, `carbontally_e2e`, `ct_p3_verify_pg`, host-5432 or Windows-cluster content
  was read.
* This ledger does **not** recommend a canonical database; that is PD-1.

## 11. Open reconciliation items (explicitly unresolved by this task)

| # | Conflict / gap | Observations preserved | Status |
|---|---|---|---|
| R-1 | Two databases match "25 organisations / 0 factors" (`ct_local_93d5cdd` 2026-09-19; `carbontally_qa_phase8` 2026-09-14) | Both datasets kept; READINESS-02 named `ct_local_93d5cdd` explicitly | **REQUIRES_RECONCILIATION** |
| R-2 | Investor-demo counts drift: manifest 976 orgs / 1,325 users vs current 975 orgs / 1,206 `auth.users` / 1,344 `public.users` | Both values preserved | **REQUIRES_RECONCILIATION** |
| R-3 | Port/project duality: same `project_id = carbon_ledger` on 5432x and 5442x, `[db.migrations]` true in one repo and false in the other | Both configs preserved | **REQUIRES_RECONCILIATION** |
| R-4 | Production: owner reports 2 orgs / 7,049 factors, while the 2026-09-11 reconciliation recorded the project host as NXDOMAIN with state UNKNOWN | Both preserved | **REQUIRES_RECONCILIATION / PO** |
| R-5 | Documentation asserts two concurrent Supabase stacks ("older stack at 54323–54326 still running") but only one `carbon_ledger` volume/container exists today | Document as historical; current Docker state is the fact | **REQUIRES_RECONCILIATION** |
| R-6 | Orphan dump of `carbontally_dev` (2026-09-01) with no corresponding live database | Dump preserved untouched | **REQUIRES_RECONCILIATION / PO** |
| R-7 | `ct_local_93d5cdd` has no `auth` schema while the canonical repo's frontend/backend expect Supabase Auth | `.env` shows Supabase URL deliberately unroutable (:19999) | **REQUIRES_RECONCILIATION / PO (PD-4)** |
| R-8 | No durable database carries the canonical 89-migration generation (P17 only in disposable clones) | 15 clone DBs preserved | **REQUIRES_RECONCILIATION / PO (PD-3)** |
| R-9 | The flagship's dataset (975 orgs, 685 objects, 100 snapshots) cannot satisfy §17 evidence/provenance requirements because its schema has no evidence/artifact tables | Flagship preserved as-is | **REQUIRES_RECONCILIATION / PO (PD-2)** |
| R-10 | `carbontally_demo_lab_postgrest/storage` read `carbontally_demo_local` while the Supabase REST/Studio serve `postgres` — the same cluster presents two different "current" app databases on different ports (54430 vs 54425) | Both kept | **PLAUSIBLE-BY-DESIGN** (documented as a deliberate lab) |

## 12. Ledger verdict

**`CT_DB_RECON_01_COMPLETE_WITH_UNRESOLVED_DATABASES`** — the discovery is complete for every
reachable database and for all documentary/filesystem evidence; four physical instances and
two artefact classes remain deliberately un-inspected (INST-02, INST-03, INST-04, INST-05 and
production), and ten reconciliation items remain open for PO decision.
No fixes, migrations, consolidations, resets, seeds or deletions were performed.









