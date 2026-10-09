# CarbonTally — Complete Database Discovery & Reconciliation: Executive Forensic Report

**Task ID:** `CT-DB-RECON-01-20260927-CARBONTALLY-COMPLETE-DATABASE-DISCOVERY-AND-RECONCILIATION`
**Document:** 3 of 3 — Executive forensic report
**Mode:** READ-ONLY / FORENSIC. No fixes, consolidation, migration, seeding, reset or deletion.
**Date of observation:** 2026-09-27, 13:09–13:24 (+06) · **Host:** `shomonrobie-H81M-DS2`
**Companion documents:**
`CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md` (census + appendix) ·
`CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-LEDGER-20260927.md` (ledger + matrix)

**FINAL VERDICT: `CT_DB_RECON_01_COMPLETE_WITH_UNRESOLVED_DATABASES`**

---

## 1. Executive summary

* **Eight** physical/held data instances and **two** artefact classes were discovered
  (INST-01…INST-08). Exactly **one** of them is running a CarbonTally application database:
  the `carbon_ledger` local Supabase stack (INST-01), which contains **78 logical
  databases** — not one.
* The Product Owner's current local Supabase (`54423` Studio / `54425` API / `54426`
  Postgres) is **INST-01**, and the application database it serves is the database literally
  named **`postgres`** inside that cluster: `organizations = 975`,
  `emission_factors = 7,049` — matching the owner's observation exactly.
* The READINESS-02 database (`ct_local_93d5cdd`, 25 organisations, 0 emission factors) is
  **not a separate instance**: it is another logical database **inside the same INST-01
  cluster**. The earlier "port 54426 confusion" is explained: one Postgres volume has been
  served under two different port mappings by the two repositories, both of which declare
  `project_id = carbon_ledger`.
* **70 of the 78 databases are disposable verification clones** (`ct_*`) created by
  automated verification tasks; they include the **only copies of the P17 accounting
  generation** (15 databases) and two 7,029-factor DEFRA-only libraries.
* **No durable database carries the canonical 89-migration generation.** The flagship
  database has 46 ledger-recorded migrations and an older 116-table schema; the modern
  schema generations live in low-data databases (Demo Lab, `ct_local_93d5cdd`,
  `carbontally_qa_phase8`).
* The **7,049-factor library exists twice** with **byte-identical content**
  (content hash `eefbcf6e3d26ea6d908bac182fe4a309`) in `postgres` and
  `carbontally_demo_local`, imported independently. Its provenance is the generated
  idempotent SQL imports (DEFRA 7,029 + SEAI 20), **not** migrations and **not** the
  investor-demo seed.
* The **975 organisations** exist **only** in `postgres`, with 1,206 auth identities, 1,125
  memberships and 917 consultant-client links; they were seeded 2026-08-22 → 2026-08-28 by
  `tools/seed_investor_demo/` (manifest `DEMO_IDENTITIES.md`), with a small unexplained
  count drift against the manifest.
* Production remains **owner-evidence only** (`organizations = 2`, `emission_factors =
  7,049`); the last documented attempt to inspect it (2026-09-11) found the project host
  NXDOMAIN and no read-only credential. Production state is **UNKNOWN**.
* Nothing was changed: no write, no migration, no seed, no reset, no container start, no
  repository edit other than these three documents.

---

## 2. Discovered database count and identity table

| INST | Identity | Type | State | Where | Logical DBs | Content reached in this task |
|---|---|---|---|---|---|---|
| **INST-01** | Supabase project `carbon_ledger` (container `supabase_db_carbon_ledger`, image `postgres:17.6.1.147`; volume `supabase_db_carbon_ledger`) | Docker cluster | **RUNNING** (:54426) | localhost | **78** | **Fully censused** |
| **INST-02** | Supabase project `carbontally_e2e` (port mapping 5532x) | Docker cluster | **STOPPED** (Exited 255) | localhost | ? | **Not inspected — UNKNOWN** |
| **INST-03** | `ct_p3_verify_pg` standalone Postgres container | Docker container, **no volume** | **STOPPED** | localhost (:55440 historical) | ? | **Not inspected — UNKNOWN** |
| **INST-04** | Host system PostgreSQL 18 (`/var/lib/postgresql/18/main`) | Native cluster | **RUNNING** (:5432) | 127.0.0.1 | ? | **Not accessible read-only — UNKNOWN** |
| **INST-05** | Windows-era `D:/carbon_ledger/.tmp_pgdata` (PG 18, port 55432) | Native data directory (3 databases, 35 MB) | **NOT RUNNING** | `carbon_tally/.tmp_pgdata` | 3 (unnamed here) | **Structure only — UNKNOWN contents** |
| **INST-06** | `carbontally_demo_lab` stack (gateway/postgrest/storage) | Docker services | **RUNNING** (:54430) | localhost | 0 (client of INST-01) | Verified target = `carbontally_demo_local` |
| **INST-07** | Hosted Supabase project `pvwiojoyaqywtydzcpbg` ("CarbonTally", eu-west-2) | Hosted | **UNVERIFIED** | cloud | ? | **Owner evidence only** |
| **INST-08** | Dump/backup/preservation artefacts (≥10 files, incl. an orphan `carbontally_dev` dump) | Files | static | `~/carbontally_db_backups`, repo `backups/`, `local_backups/`, `carbontally_preservation_20260916` | n/a | Listed and header-verified |

**Headline counts:** 8 instances discovered · 1 running CarbonTally application cluster ·
78 logical databases in INST-01 (6 principal, 2 Supabase-internal, 70 ephemeral) · 4
instances/artefact classes deliberately un-inspected.

## 3. Repository relationship map

```
                        (pre-Linux, Windows era)
     d:\carbon_ledger  ─────────────►  carbon_tally/.tmp_pgdata  (INST-05, PG18, 3 DBs, dead)
                                              │
                                              │  project relocates to Linux (Aug 2026)
                                              ▼
   repository A  /home/shomonrobie/carbon_tally        repository B  /home/shomonrobie/ct_93d5cdd
   HEAD 20b7a92 (2026-09-16, branch main)              HEAD cb70fd6 (2026-09-26, branch p8-release-reconciled)
   supabase/migrations = 68 files                      supabase/migrations = 89 files  (canonical candidate)
   project_id = "carbon_ledger", ports 5442x           project_id = "carbon_ledger", ports 5432x
   backend/.env → :54426/postgres                      backend/.env → :54426/ct_local_93d5cdd
                    │                                                  │
                    └──────────────┬───────────────────────────────────┘
                                   ▼
                    INST-01  Supabase project `carbon_ledger`
                    container supabase_db_carbon_ledger (PG 17.6, volume created 2026-08-23,
                    container re-created 2026-09-01)  ports 54423 / 54425 / 54426
                    78 logical databases:
                      ├── postgres                   ◄── 975 orgs, 7,049 factors, 1,206 auth users  ("flagship")
                      ├── carbontally_demo_local     ◄── Demo Lab (4 orgs, 7,049 factors, Insight/P16R/B2)
                      ├── ct_local_93d5cdd           ◄── READINESS-02 (25 orgs, 0 factors, NO auth schema)
                      ├── carbontally_qa_phase8      ◄── 25 orgs (different dates), P16R corpus 471/1069
                      ├── carbontally_test           ◄── integration-test DB (harness TRUNCATE target)
                      ├── carbontally_b2_clone_20260913
                      ├── _supabase, storage_vectors (Supabase internals)
                      └── 70 × ct_*                  ◄── disposable verification clones (15 carry the P17 generation)

   e2e/environment/supabase/config.toml ──► INST-02  project `carbontally_e2e` (ports 5532x)  STOPPED
   ct_range_2026-09-23/24               ──► INST-03  ct_p3_verify_pg                          STOPPED
   host system service                  ──► INST-04  PostgreSQL 18 @ 127.0.0.1:5432           UNKNOWN provenance
   tools/demo_lab (RUNNING)             ──► INST-06  gateway 54430 → INST-01 carbontally_demo_local
   repository docs (project ref)        ──► INST-07  hosted Supabase `pvwiojoyaqywtydzcpbg`    OWNER EVIDENCE ONLY
   dumps / backups / preservation       ──► INST-08  carbontally_dev dump + v3 dump + live captures + factor copies
```

Relationships shown are evidence-backed. Where evidence is missing the arrow is marked
UNKNOWN rather than inferred (§11 of the census lists each).

## 4. Migration and schema comparison

| Database | Public tables | Ledger | Highest recorded/applied version | Generations present | Assessment |
|---|---|---|---|---|---|
| `postgres` | **116** | 46 rows | `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` | legacy V3M-era only | **Oldest schema, richest data** — no B2 evidence, no P16/P16R, no Insight, no P17 |
| `carbontally_demo_local` | **141** | none | — | P16, P16R, B2, Insight, manual grants | Newest **durable** schema; data is a lab fixture |
| `ct_local_93d5cdd` | **135** | none | 67 migrations applied (documented) | P16, P16R, B2, manual grants | The canonical repo's target; **no factors, no `auth`** |
| `carbontally_qa_phase8` | 133 | 0 rows | — | P16, P16R, B2 | Only populated disclosure corpus |
| `carbontally_test` | 117 | none | — | Insight present | Volatile (harness `TRUNCATE`s it) |
| `carbontally_b2_clone_20260913` | 128 | 0 rows | — | P16R, B2 | B2-era clone |
| 15 × `ct_p17*` / `ct_m3*` | **145** | none | — | + **P17** | The only P17 copies in existence locally |
| Repo A migrations | — | — | 68 files, max `20260924000000_p8x_x2_…` | — | Baseline set |
| Repo B migrations | — | — | **89 files**, max `20261020000000_p17k_…` | — | **Canonical candidate** |

**Divergence, quantified:**

* RLS policies: `postgres` 174 · `carbontally_qa_phase8` 197 · `ct_local_93d5cdd` **218** ·
  `carbontally_demo_local` **298**.
* Public functions: `postgres` 21 · `ct_local_93d5cdd` 55.
* `auth` schema: present in `postgres` (1,206 users, 1,206 identities), Demo Lab (14 users,
  **0 identities**), `qa_phase8`, `b2_clone`; **absent** in `ct_local_93d5cdd` and
  `carbontally_test`.
* Storage: flagship 1 bucket / 685 objects; Demo Lab 2 buckets / 38 objects.

## 5. Data comparison (headline)

| Dataset | `postgres` | `carbontally_demo_local` | `ct_local_93d5cdd` | `carbontally_qa_phase8` | Production (owner) |
|---|---|---|---|---|---|
| organisations | **975** | 4 | **25** | **25** | **2** |
| auth users / public users | 1,206 / 1,344 | 14 / 14 | none / 658 | ? / 498 | ? |
| emission_factors | **7,049** | **7,049** | 0 | 0 | **7,049** |
| evidence_line_items | *table absent* | 67 | 0 | 0 | ? |
| calculation_snapshots / emissions_logs | 100 / 100 | 34 / 34 | 0 / 0 | 0 / 0 | ? |
| facilities / assets / suppliers | 157 / 310 / 156 | 1 / 1 / 1 | 0 / 0 / 0 | 0 / 0 / 0 | ? |
| disclosure framework versions | *table absent* | 0 | 0 | **471** | ? |
| storage objects | **685** | 38 | (bucket present) | 0 | ? |

## 6. 7,049-factor provenance (mandatory trace)

| Question | Answer | Evidence |
|---|---|---|
| Source dataset | DEFRA-2025 (7,029 rows) + SEAI-2025 (20 rows), `reporting_year = 2025` | `preservation_evidence.json` (`factor_sets`), `db06_out.txt` |
| Import tooling | **Generated idempotent SQL insert scripts**, not migrations: `output/sql/emission_factors.sql` (DEFRA) and `output/seai_2025/sql` (SEAI); SEAI rows added after the DEFRA baseline | repo A files; `docs/audit/cline/CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md`; `docs/cline/CarbonTally-SEAI-Provider-Implementation-v1.0.md` |
| Import mechanism | Direct SQL execution (psql) — **not** a migration, **not** the investor-demo seed | all 7,049 rows in `postgres` have `import_batch_id IS NULL`; `import_batches` is empty |
| Import date | Rows created **2026-08-26 14:04:22–14:04:26 UTC** in `postgres` (SQL generation 2026-08-15) | `db06_out.txt`, `output/reports/import_summary.md` |
| Local copy 2 | `carbontally_demo_local` 7,049 rows created **2026-09-24 10:15:16–10:15:20 UTC** by `tools/demo_lab/seed_factors.py`, with `import_batch_id` set and 2 `import_batches` rows | `db06_out.txt`, `db14_out.txt` |
| Local vs local identity | **Content-identical, row-id-different**: content hash `eefbcf6e3d26ea6d908bac182fe4a309` in **both**; id hashes differ (`93668772…` vs `e7c28218…`) | `db14_out.txt` |
| Local vs live identity | **UNKNOWN — not verifiable here.** The live count (7,049) matches, but no production read was performed (task §17) | — |
| Are there version/source metadata fields? | Yes: `factor_source`, `factor_set`, `country`, `reporting_year`, `import_batch_id`, `created_at`, `updated_at` | `information_schema.columns` |
| Prior preservation evidence | `emission_factors row_md5 = ee97d28a03fbe379deae89f515642999`, 7,049 rows, `distinct_activity_types = 7049` (2026-09-16) | `carbontally_preservation_20260916/preservation_evidence.json` |
| Earlier DEFRA-only state | 7,029 rows in `ct_v078_t2b` and `ct_v078_t2b_tests` (content hash `b50c9f4f…`) | `db14_out.txt` |

## 7. 975-organisation provenance (mandatory trace)

| Question | Answer | Evidence |
|---|---|---|
| Which database | **`postgres`** in INST-01 only — no other discovered database contains it | full 78-DB census |
| Creating task / tooling | `tools/seed_investor_demo/` (repo A only; absent from repo B), a CLI seeder built on the GoTrue admin API + PostgREST, with a local-environment safety guard | `tools/seed_investor_demo/{__main__,seed_core,config,safety}.py`; `DEMO_IDENTITIES.md` |
| Documented creation | `CT-OPS-LOCAL-PLATFORM-MANUAL-TEST-START-20260912-001` states "the `carbon_ledger` database holds the investor demo dataset (975 organisations)"; Phase-5 and P6-2F reports record 975 organisations and 917 consultant grants as the unchanged baseline; `CT-PO-COMPREHENSIVE-INVESTOR-READY-PLATFORM-STUDY-20260924` records 975 orgs / 1,205 auth users / 116 tables as "LEGACY / SUPERSEDED SCHEMA, RICH DATA" | repo A and repo B docs |
| Creation date | Organisation rows span **2026-08-22 16:53:32Z → 2026-08-28 22:42:27Z**; manifest verified 2026-08-28 | `db06_out.txt` (`ORGS`), `DEMO_IDENTITIES.md` |
| Synthetic or real? | **Synthetic demo data** (`@demo.carbontally.local` identities, shared local-only password, deterministic UUIDs, `synthetic.Rng`) | seeder code + manifest |
| Intended purpose | Investor / persona demonstration and acceptance testing; the population behind the "1,185 identities" manifest | `DEMO_IDENTITIES.md` |
| Relationship to investor demo | It **is** the investor demo dataset (the "flagship") | as above |
| Present in any other DB? | **No** — not in Demo Lab, not in `ct_local_93d5cdd`, not in `qa_phase8`, not in any `ct_*` clone | census |
| Replaced by 25 or 2? | **No evidence of replacement.** The 25-org datasets are separate databases in the same cluster; the owner-reported production 2 orgs is a different environment | census + ledger R-1 |
| Downstream records referencing them | Yes, extensively: 1,125 memberships, 917 consultant-client links, 55 consultant profiles, 263 organisation files, 264 extraction items, 100 snapshots, 685 storage objects | census §9 |
| Count drift | Manifest: 976 orgs / 1,325 users · current: 975 orgs / 1,206 `auth.users` / 1,344 `public.users` → **unexplained; REQUIRES_RECONCILIATION** | `DEMO_IDENTITIES.md` vs `db06_out.txt` |
| Action taken here | **None.** Dataset untouched (AGENTS.md §55) | this task |

## 8. 25-organisation provenance (mandatory trace)

| Question | Answer | Evidence |
|---|---|---|
| Which database produced READINESS-02's `25 orgs / 0 factors`? | **`ct_local_93d5cdd`** — the database named in the READINESS-02 report, and the target of repo B's `backend/.env` | `ct_local_env/README.md`; `db05_census_lines.txt` (`organizations=25;…emission_factors=0`) |
| Physical identity | A logical database **inside INST-01** (`supabase_db_carbon_ledger` / PG 17.6 / port 54426) — **not** a separate server | `pg_database` read; cluster identity |
| Creating task | `CT-STEP2-LOCAL-LATEST-RUN-WITHOUT-BASELINE-072` — the isolated local run of the latest (93d5cdd) checkout | `ct_local_env/README.md`, `start_latest.sh`, `IDENTITIES.md` |
| Created when | Organisation rows 2026-09-19 03:43:07Z → 13:00:36Z (the same day `ct_local_env` was set up) | `db06_out.txt` (`ORG_NAMES_25`) |
| Migration/seed state | 135 public tables, 67 migrations applied, 218 RLS policies, 0 emission factors; **no `auth` schema**; no migration ledger | README + catalogue |
| Was it created after the move to `ct_93d5cdd`? | **Yes** (2026-09-19) — it exists because of the isolation of repo B's runtime | dates |
| Did Cline create it? | **STRONGLY SUPPORTED**: the harness scripts in `ct_local_env/` and the README are Cline artefacts of that task; the database name encodes the repo commit | `ct_local_env/*` |
| Was it a deliberate canonicalisation? | **No evidence of that.** It is labelled "disposable"; it was created to avoid touching the baseline (`postgres` "untouched" per README) | README |
| Competing 25-org dataset | `carbontally_qa_phase8` (25 orgs, created 2026-09-14, 498 users, populated disclosure corpus) → **the two are not the same database and their derivation relationship is UNKNOWN** | `db05`, `db08` |
| Action taken here | **None.** |

## 9. Production state (mandatory trace)

* Owner-reported today: `organizations = 2`, `emission_factors = 7,049`.
* Documented project identity: Supabase ref `pvwiojoyaqywtydzcpbg`, name `CarbonTally`,
  region eu-west-2.
* Last documented inspection attempt (2026-09-11, read-only): project host **NXDOMAIN**,
  no read-only credential available, only a write-capable service key (not used); result
  `NOT READY — PRODUCTION STATE STILL UNKNOWN`.
* This task: **no production access attempted, no credential requested or printed**.
* Reconciliation status: **REQUIRES_RECONCILIATION (owner evidence vs 2026-09-11 finding)**.

## 10. Cline historical actions on database environments (evidence-class separation)

DOCUMENTED, COMMAND SHOWN, COMMAND EXECUTED, COMMAND SUCCEEDED and DATABASE EFFECT VERIFIED
are never collapsed into one another here.

| # | Historical action | DOCUMENTED | COMMAND SHOWN | COMMAND EXECUTED | SUCCEEDED | DATABASE EFFECT VERIFIED |
|---|---|---|---|---|---|---|
| 1 | Investor-demo seeding of 975 orgs into `postgres` | **Yes** (multiple Cline reports + manifest) | Yes (seeder CLI documented) | **Yes** (row-creation timestamps 2026-08-22→28) | **Yes** | **Yes** — 975 orgs, 1,125 memberships, 1,206 auth users, 917 consultant links (read today) |
| 2 | 7,049-factor import into `postgres` | Yes (`CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md`, SEAI provider doc) | Yes (psql execution of generated SQL) | **Yes** (rows dated 2026-08-26) | **Yes** | **Yes** (counts, sets, hashes read today) |
| 3 | Creation of `ct_local_93d5cdd` + 67-migration apply | Yes (`ct_local_env/README.md`) | Yes (`psql` commands; `start_latest.sh`) | **Yes** (DB exists; 25 orgs dated 2026-09-19) | **Yes** | **Yes** (135 tables / 218 policies read today) |
| 4 | `CREATE DATABASE … TEMPLATE …` clones for P17/I-series/M-series verification | Yes (repo B P17 reports) | **Yes** (shell-history lines against `127.0.0.1:54426`) | **Yes** | **Yes** | **Yes** — 70 `ct_*` databases exist; 15 carry P17 objects |
| 5 | Demo Lab provisioning (`carbontally_demo_local` + `carbontally_demo_lab_*`) | Yes (`tools/demo_lab`, P12 reports) | Yes (`run_demo_lab.sh`, `stack.py`) | **Yes** (containers running; rows dated 2026-09-24) | **Yes** | **Yes** (141 tables, 7,049 factors, 38 objects; live sessions seen) |
| 6 | Isolated E2E project `carbontally_e2e` | Yes (`CT-P6-2F-ENV-IMPL-20260911-001`: "`supabase start` EXIT=0"; 26 migrations then 27 as `supabase_admin` → **53/53**; 116 public tables) | Yes (bootstrap/reset scripts) | **Yes** (stack containers exist) | Yes (per report) | **NOT VERIFIED here** — cluster stopped and deliberately not started |
| 7 | `carbontally_test` provisioning | Yes (`CarbonTally_V3_Test_Database_Diagnostic_v1.0.md`) | Yes (`INTEGRATION_DATABASE_URL`) | **Yes** (117 tables exist) | Yes | **Yes** (schema read today); data state transient by design |
| 8 | `carbontally_dev` database + 2026-09-01 dump | **No documentation found** | Dump filename implies `pg_dump` | Plausible | Unknown | **UNKNOWN** — database no longer exists; dump preserved |
| 9 | Migration-ledger replay into `postgres` (46 rows) | Yes | Yes | Yes | Yes | **Yes** (46 ledger rows read today) |
| 10 | Supabase-Auth provisioning of 1,206 identities | Yes (manifest: GoTrue admin API) | Yes | **Yes** | Yes | **Yes** (`auth.users`/`auth.identities` = 1,206) |
| 11 | Windows-era cluster (`D:/carbon_ledger/.tmp_pgdata`) | Indirectly (docs reference `d:\carbon_ledger`) | Yes (`postmaster.opts` records the Windows start line) | Yes (on the old Windows host) | Unknown | **Not verifiable here** (not started) |
| 12 | Any *destructive* action on the flagship (reset/truncate/reseed) | **None found** | — | — | — | **No** — flagship retains its full dataset |

**Important non-findings:** no evidence of any Cline task resetting, truncating or reseeding
the flagship `postgres` database; and no evidence of a **second** `carbon_ledger` storage
instance — only a second **port mapping**.

## 11. Database topology (evidence-backed only)

* INST-01 is a **single physical cluster with 78 logical databases**; the "multiple database
  instances" impression is a naming/port artefact, not multiple storage engines.
* The two repositories are not attached to different clusters; they are attached to
  **different logical databases of the same cluster** (`postgres` vs `ct_local_93d5cdd`).
* INST-02 is a genuinely separate cluster (own volume), currently stopped.
* INST-03 / INST-04 / INST-05 are separate data holders whose contents could not be read
  without crossing the safety boundary.
* INST-07 (production) is a separate hosted project with no verified connection from this
  environment.
* INST-08 artefacts are static evidence of earlier databases, including one
  (`carbontally_dev`) that no longer exists in any catalogue.

## 12. Unresolved questions

1. What are the contents of INST-02 (`carbontally_e2e`), INST-03 (`ct_p3_verify_pg`) and
   INST-04 (host PG 18)?
2. Which of the two 25-organisation datasets is the intended base for future work, and how
   do they relate to each other?
3. Has production ever been migrated beyond the state described on 2026-09-11?
4. What was `carbontally_dev`, and does its dump contain unique work?
5. Why do the manifest counts and current flagship counts differ (976→975 orgs,
   1,325→1,206/1,344 users)?
6. Which environment is authorised to receive the P17 generation, and where will
   P16R/Insight verification be evidenced?
7. Is a Supabase-Auth-bearing local database required for the next phase?
8. Should the 70 ephemeral clones be retained as evidence, or cleaned up on a schedule?

## 13. Recommended next investigation / decision sequence (nothing performed)

1. **PO decisions PD-1…PD-10** (ledger §7), in particular PD-1 (authorised target), PD-3
   (evidence environment) and PD-4 (auth-bearing environment).
2. **Read-only** inspection of INST-02 and INST-03 **only if** the PO authorises starting
   stopped environments; otherwise record them permanently as UNKNOWN.
3. Identify the owner/purpose of host PostgreSQL 18 (INST-04) with the operator — no
   credential guessing.
4. Diff the `carbontally_dev` dump's schema against `postgres` (offline, read-only) to decide
   whether ART-01 is an orphan or contains unique work.
5. Resolve the 976/975 and 1,325/1,206 drift by reading the seeder manifest and the auth
   tables side by side (read-only).
6. Only after PD-1/PD-2: design a schema+data consolidation **plan** — a plan, not execution.

## 14. Limitations of this investigation

* **Cannot resolve without starting stopped environments:** INST-02 (`carbontally_e2e`) and
  INST-03 (`ct_p3_verify_pg`). Starting them is outside the read-only safety boundary and
  could alter state.
* **Cannot resolve without credentials/authorisation:** INST-04 (host PostgreSQL 18) and
  INST-07 (production). No credential was sought, printed or used.
* **Cannot resolve without starting a cluster:** the 3 databases inside the Windows-era
  `D:/carbon_ledger/.tmp_pgdata` data directory.
* Docker volume sizes on disk could not be measured (`du` output unavailable to this user
  for `/var/snap/docker/...`).
* The factor content hash proves **local-vs-local** equality only; local-vs-production factor
  comparison remains impossible without authorised production access.
* Documentation was used as evidence/hints only, and every material documentary claim used
  here was cross-checked against a catalogue read or filesystem artefact. Where a documentary
  claim could not be cross-checked (two concurrent stacks; 976 vs 975 organisations) it is
  reported as an open conflict rather than adopted.
* Ephemeral database population is time-dependent; the 78-database count is a 2026-09-27
  snapshot.

## 15. Mandatory questions — explicit answers

**1. How many CarbonTally database instances were discovered?**
**Eight** physical/held data instances (INST-01…INST-08): one running application cluster
(INST-01), one stopped cluster (INST-02), one stopped container (INST-03), one host cluster of
unknown provenance (INST-04), one dead Windows-era data directory (INST-05), one Demo-Lab
service stack that is a client of INST-01 (INST-06), one hosted production project (INST-07,
owner evidence only), and one class of dump/backup/preservation artefacts (INST-08).
INST-01 contains **78 logical databases**.

**2. Which one is the Product Owner's current local Supabase?**
**INST-01** — Supabase project `carbon_ledger` (Studio `54423`, API `54425`, Postgres
`54426`; container `supabase_db_carbon_ledger`; PG 17.6). The application database it serves
is the database **named `postgres`** within it: **975 organisations** and **7,049 emission
factors** — exactly the owner's observation (VERIFIED by direct read).

**3. Which database produced the READINESS-02 25-org / 0-factor observation?**
**`ct_local_93d5cdd`** — a logical database **inside INST-01**, created 2026-09-19, holding 25
organisations (`System`, 20 × `Test Co`, `D35 Candidate Org`, `D35 Private Org`,
`Local Demo Customer`, `Local Other Tenant`), 658 public users, 135 tables, 218 RLS policies,
and **0 emission factors**. It is *not* a separate server, and it is the target of repository
B's `backend/.env`.

**4. Are there additional local databases?**
**Yes — many.** Besides the six principal databases (`postgres`, `carbontally_demo_local`,
`ct_local_93d5cdd`, `carbontally_qa_phase8`, `carbontally_test`,
`carbontally_b2_clone_20260913`), INST-01 contains **70 disposable `ct_*` verification
clones** plus two Supabase-internal databases (`_supabase`, `storage_vectors`). Further data
holders exist outside INST-01: INST-02 (stopped E2E cluster), INST-03 (stopped container),
INST-04 (host PG 18) and INST-05 (dead Windows cluster, 3 databases).

**5. Which DB contains the 975 Cline-created organisations?**
**`postgres`**, in INST-01 — and only there. With 1,206 `auth.users` / `auth.identities`,
1,344 `public.users`, 1,125 `organization_members`, 917 `consultant_clients`, 55
`consultant_profiles`, 54 `consultant_firm_members`, 21 `staff_profiles`, 11
`processing_entities`, 263 `organization_files` and 685 storage objects.

**6. Where did those 975 organisations come from?**
From the **investor-demo seeder `tools/seed_investor_demo/`** (present only in repository A),
which writes through the GoTrue admin API and PostgREST against the local Supabase
(`http://127.0.0.1:54425`) with a local-environment safety guard. Organisation rows were
created between **2026-08-22 16:53:32Z and 2026-08-28 22:42:27Z**; the manifest
`DEMO_IDENTITIES.md` records 976 organisations / 1,325 users / 1,185 demo identities as
verified on 2026-08-28 — a small, unexplained drift versus today's 975 orgs / 1,206
`auth.users` / 1,344 `public.users`.

**7. Where did the 7049 emission factors come from?**
From **generated idempotent SQL insert scripts** — `output/sql/emission_factors.sql`
(DEFRA-2025, 7,029 rows) plus `output/seai_2025/sql` (SEAI-2025, 20 rows) — executed directly
into `postgres` (rows created **2026-08-26 14:04:22–14:04:26Z**), **not** via a migration and
**not** via the investor-demo seed (all rows have `import_batch_id IS NULL`; `import_batches`
is empty). A second, independent import of the same library exists in
`carbontally_demo_local` (rows created 2026-09-24 by `tools/demo_lab/seed_factors.py`, with an
`import_batch_id` and 2 batches).

**8. Are the 7049 factors locally and in live Supabase identical?**
**Partially answered.** The two **local** copies are **content-identical** (content hash
`eefbcf6e3d26ea6d908bac182fe4a309` in both `postgres` and `carbontally_demo_local`) though
their row UUIDs differ (id hashes `93668772…` vs `e7c28218…`). **Local vs live is NOT
VERIFIED** — the live count matches (7,049) per owner evidence, but no production read was
performed, so byte-identity between local and production remains **UNKNOWN**.

**9. Which migrations are actually applied to each DB?**

* `postgres`: **46**, ledger-recorded, ending `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql`;
  everything after that (P8-era work, B2 evidence, P16, P16R, Insight, P17) is
  **CONFIRMED_NOT_APPLIED** by object absence.
* `ct_local_93d5cdd`: **67** migrations applied (documented in `ct_local_env/README.md`,
  corroborated by 135 tables / 218 policies); no ledger; P16/P16R/B2 present; Insight and P17
  absent.
* `carbontally_demo_local`: no ledger; P16/P16R/B2/Insight/manual-grant objects present →
  `OBJECTS_PRESENT_APPLICATION_TIME_UNKNOWN`.
* `carbontally_qa_phase8` and `carbontally_b2_clone_20260913`: ledger tables exist but are
  **empty** → `OBJECTS_PRESENT_APPLICATION_TIME_UNKNOWN`.
* `carbontally_test`: no ledger; 117 tables; state transient (harness `TRUNCATE`s it).
* 70 `ct_*` clones: no ledger (two have empty ledger tables); each reflects whichever
  principal database it was cloned from; the **15 P17 clones** carry the P17 generation
  applied only inside them.

**10. What happened to the database environment during the move from `carbon_tally` to
`ct_93d5cdd`?**
The **storage did not move**. Both repositories declare the same Supabase project
(`project_id = carbon_ledger`) and therefore address the **same Postgres volume**
(`supabase_db_carbon_ledger`, created 2026-08-23). What changed is the **address and the
attach point**: the running stack publishes the **5442x** mapping from repository A's config,
while repository B's config publishes **5432x**; and repository B's `backend/.env` was pointed
at a **newly created, disposable logical database** (`ct_local_93d5cdd`, 2026-09-19) with an
unroutable Supabase URL (`:19999`), while repository A's backend kept pointing at the
incumbent `postgres` database (the 975-organisation flagship). The move therefore created a
**new logical database inside the same cluster** rather than a new instance, and left the
incumbent 975-organisation database untouched ("baseline … not modified", "postgres @
127.0.0.1:54426 (untouched)" per `ct_local_env/README.md`).

**11. Did Cline create/reset additional local databases?**
**Yes — additional databases inside the same cluster.** Proven: 70 `ct_*` databases created as
`CREATE DATABASE … TEMPLATE …` clones (shell history shows the commands executed against
`127.0.0.1:54426`), and `ct_local_93d5cdd` created 2026-09-19 for the isolated local run.
`carbontally_demo_local` was created by the Demo-Lab tooling (2026-09-20/24);
`carbontally_qa_phase8` and `carbontally_b2_clone_20260913` by earlier QA/B2 work. **No
evidence** was found of any Cline task **resetting** the flagship `postgres` database; and
this task created or altered nothing.

**12. What schema differences exist between the DBs?**
Four distinct generations, with no superset (§4 of this report): 116 tables / 174 policies /
no evidence-disclosure-Insight-P17 (`postgres`); 135 / 218 with P16/P16R/B2/manual grants
(`ct_local_93d5cdd`); 141 / 298 additionally adding Insight (`carbontally_demo_local`); 145 /
311 additionally adding P17 (the 15 clones). The `auth` schema exists in some and not others;
public functions 21 vs 55.

**13. What data/capabilities exist only in each DB?**

* Only in `postgres`: the 975 organisations, 1,206 auth identities, 1,125 memberships, 917
  consultant links, 157 facilities, 310 assets, 156 suppliers, 685 storage objects.
* Only in `carbontally_demo_local`: the four Insight tables plus the `report-artifacts` bucket.
* Only in `carbontally_qa_phase8`: the populated 471/1,069 disclosure corpus.
* Only in the 15 `ct_*` P17 clones: the P17 accounting / governed-capability schema.
* Only in `ct_local_93d5cdd`: the 25-organisation dataset READINESS-02 measured.
* `carbontally_test`: nothing durable, by design.

**14. What is proven vs merely documented?**

| Proven (read in this task) | Documented only |
|---|---|
| 78 databases with sizes, table/RLS/policy counts | Two concurrent `carbon_ledger` stacks (5432x + 5442x) |
| 975 orgs / 7,049 factors / 1,206 auth users / 685 objects | That `seed_investor_demo` produced them (code + manifest + timestamps corroborate) |
| Factor content equality between the two local copies | Factor equality with production |
| `ct_local_93d5cdd` = 25 orgs, 0 factors, no `auth` | That READINESS-02's DB **is** this one (name + `.env` + counts corroborate) |
| 46-row ledger of `postgres`; no durable P17 anywhere | INST-02's "53/53 migrations, 116 tables" |
| Clone-creation commands (shell history) | That `carbontally_dev` was ever live |
| Containers/volumes/timestamps | Production's current schema/migration/factor state |

**15. What remains UNKNOWN?**
The contents of INST-02, INST-03, INST-04 and INST-05; production schema/migration/RLS/factor
identity; the derivation of the two 25-organisation datasets; the cause of the 976/975 and
1,325/1,206 count drift; whether the 7,049 factors are byte-identical in production; the
identity of `carbontally_dev`; and whether the "two concurrent stacks" ever truly existed.

**16. What must be reconciled before any database consolidation?**
(a) Which environment is authorised as the target (PD-1); (b) whether the 975-organisation
dataset is carried forward or preserved in place (PD-2); (c) which environment is the
authorised evidence environment for P16R/Insight/P17 (PD-3); (d) whether an auth-bearing local
database is required (PD-4); (e) the port/project convention (PD-5); (f) the fate of orphan
holdings — `carbontally_dev` dump, Windows-era data directory, stopped E2E cluster and
`ct_p3_verify_pg` (PD-6/7/8); (g) the integration-harness default (PD-10); and (h) resolution
of the two 25-org datasets and the count drift (ledger R-1, R-2). Plus a schema+data **merge
design**, because no database is a superset.

**17. What must NOT be changed or deleted?**
The flagship `postgres` database and its dataset; `carbontally_demo_local`; `ct_local_93d5cdd`;
`carbontally_qa_phase8`; `carbontally_test` (kept isolated); `carbontally_b2_clone_20260913`;
all 70 `ct_*` clones (`CANDIDATE_FOR_CLEANUP` only, and only after PD-3/PD-8); the Docker
volumes (`supabase_db_carbon_ledger`, `supabase_db_carbontally_e2e`,
`carbontally_demo_lab_storage`); the stopped containers (`supabase_db_carbontally_e2e` and its
stack, `ct_p3_verify_pg`); `carbon_tally/.tmp_pgdata`; the dump/backup/preservation artefacts;
the unidentified host PostgreSQL 18 data; and `tools/seed_investor_demo/*` with its manifest.
See ledger §8.

## 16. Verdict, change record and self-verification

### 16.1 Verdict

**`CT_DB_RECON_01_COMPLETE_WITH_UNRESOLVED_DATABASES`**

Discovery is complete for every reachable database, every Docker/Supabase artefact, every
configuration reference and the documentary history. It is *not* `…COMPLETE_DATABASE_CENSUS`
because four physical data holders (INST-02 `carbontally_e2e`, INST-03 `ct_p3_verify_pg`,
INST-04 host PostgreSQL 18, INST-05 Windows-era data directory) and the hosted production
project (INST-07) could not be inspected without exceeding the read-only safety boundary, and
because ten reconciliation items (ledger §7) and eight open questions (§12) remain for PO
decision. It is *not* `…INCOMPLETE` because no known reachable database was left uncensused and
no evidence source required by the task was skipped.

No readiness vocabulary (`INVESTOR_READY`, `CUSTOMER_READY`, `PRODUCTION_READY`) is used or
implied: this was a discovery task, not a readiness certification.

### 16.2 Change record (exactly three files created; nothing else modified)

| File (in `/home/shomonrobie/ct_93d5cdd/docs/architecture/`) | Contents |
|---|---|
| `CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md` | Discovery + census, 8 instances, 78 databases, appendices A/B |
| `CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-LEDGER-20260927.md` | Capability/dataset/migration/artefact/config ledger, N-way matrix, PO decision list, protection list |
| `CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md` | This executive forensic report (17 mandatory answers, topology, verdict) |

### 16.3 Safety verification performed

| Check | Result |
|---|---|
| Any `INSERT`/`UPDATE`/`DELETE`/`TRUNCATE`/`ALTER`/`DROP`/`CREATE`/`GRANT` executed? | **No** — only `SELECT`/catalogue reads (`docker exec … psql -At -c "select …"`) |
| Any `CREATE DATABASE`, migration, seed, `supabase db push/reset/diff`, `pg_restore`? | **No** |
| Any container/cluster started, stopped, restarted or removed? | **No** (INST-02 and INST-03 left stopped exactly as found) |
| Any Docker volume modified? | **No** |
| `.env`, `config.toml`, source, migration, test or RLS file modified? | **No** |
| Git commit / push / checkout / reset performed? | **No** |
| Secrets printed, copied or committed? | **No** — URLs truncated before credentials; keys reported as `<set>`/`<redacted>`; the demo password was deliberately not reproduced |
| Production contacted? | **No** — no connection attempted, no production credential requested |
| Integration harness pointed at any data-bearing database? | **No** — the harness was never invoked by this task |
| Post-audit re-read of `postgres` counts | Unchanged (975 orgs / 7,049 factors) — confirms no writes occurred |

### 16.4 Post-delivery pointer

The two follow-on actions available to the PO, in the correct order, are:

1. **Decide PD-1…PD-10** (ledger §7), then
2. authorise a **read-only** follow-up for whichever of INST-02/03/04/05/production the
   decision requires — with the standing constraints restated: no consolidation, no
   migration, no seeding, no deletion, and no starting of stopped environments without
   explicit authorisation.

---

*End of report — CarbonTally CT-DB-RECON-01, 2026-09-27.*








