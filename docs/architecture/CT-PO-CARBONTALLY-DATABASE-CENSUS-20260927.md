# CarbonTally — Complete Database Discovery & Census

**Task ID:** `CT-DB-RECON-01-20260927-CARBONTALLY-COMPLETE-DATABASE-DISCOVERY-AND-RECONCILIATION`
**Document:** 1 of 3 — Database Census
**Mode:** READ-ONLY / FORENSIC DISCOVERY. No database, container, volume, config,
migration, seed or repository file was created, altered, started, reset or deleted by
this task other than the three deliverables required by task §21.
**Date of observation:** 2026-09-27 (13:09–13:24 local, `+06`)
**Host:** `shomonrobie-H81M-DS2` · **Operator:** `shomonrobie`

## 0. Document control

| Item | Value |
|---|---|
| Repository A ("baseline") | `/home/shomonrobie/carbon_tally` — branch `main`, HEAD `20b7a928bb73fdfacf8271ff537a8fd245f62c79` (2026-09-16) |
| Repository B ("canonical / latest") | `/home/shomonrobie/ct_93d5cdd` — branch `p8-release-reconciled`, HEAD `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbdbb` (2026-09-26) |
| Deliverables written to | `/home/shomonrobie/ct_93d5cdd/docs/architecture/` (the repository holding the `CT-PO-*` series and the canonical 89-migration set) |
| Verdict vocabulary (task §22) | `CT_DB_RECON_01_COMPLETE_DATABASE_CENSUS` / `CT_DB_RECON_01_COMPLETE_WITH_UNRESOLVED_DATABASES` / `CT_DB_RECON_01_INCOMPLETE` |
| This task's verdict | **`CT_DB_RECON_01_COMPLETE_WITH_UNRESOLVED_DATABASES`** (report, §21) |

**Safety statement.** Every database interaction in this task was a `SELECT` or catalogue
read executed as `docker exec supabase_db_carbon_ledger psql -U postgres -At`. No
`INSERT`/`UPDATE`/`DELETE`/`TRUNCATE`/`ALTER`/`DROP`/`CREATE`/`GRANT`, no
`CREATE DATABASE`, no migration, seed, reset, `supabase db push`, `pg_restore`, and no
Docker mutation was performed. No stopped container or stopped cluster was started. No
secret value is reproduced in these documents (no passwords, keys, tokens, JWTs or
signed URLs).

## 1. Method and evidence sources

Discovery followed the task's required order: running processes and listeners → Docker
containers (running **and** stopped) → Docker volumes → Supabase project configurations →
repository `.env` **key names** with masked URL values → read-only `psql`
catalogue/`SELECT` inspection of every reachable logical database → dump/backup artefacts
→ both documentation trees → shell history → Cline/OHD task reports.

Primary evidence artefacts (all retained outside the repository, in `/tmp`):
`db01_net.txt`, `db01_docker_ps.txt`, `db01_docker_vol.txt`, `db01_home.txt`,
`db01_root_a.txt`, `db01_root_b.txt`, `db02_inspect.txt`, `db02_vols.txt`,
`db02_configtoml.txt`, `db02_supahome.txt`, `db02_dirs.txt`, `db03_dblist.txt`,
`db03_ver.txt`, `db03_configs.txt`, `db03_tmppg.txt`, `db05_census_out.txt`,
`db05_census_lines.txt`, `db05_tables_ext.txt`, `db06_out.txt`, `db07_*.txt`,
`db08_out.txt`, `db09_docs.txt`, `db10_out.txt`, `db10_matrix_lines.txt`,
`db11_dbs2.txt`, `db11_diff.txt`, `db14_out.txt`.

**Counting discipline.** Three independent catalogue passes were taken (`db03` 13:09,
`db05`/`db08` 13:12–13:16, `db10`/`db11` 13:18). The resulting database-name sets are
**set-identical** (`diff` empty) at **78 non-template, connectable databases**. Where an
older document records a different number, the current catalogue read wins.

## 2. Truth ladder, confidence and classification vocabulary

```
DOCUMENTED DB ≠ DB CONFIG EXISTS ≠ DB CONTAINER EXISTS ≠ DB VOLUME EXISTS
≠ DB WAS STARTED ≠ MIGRATION COMMAND EXECUTED ≠ MIGRATION SUCCEEDED
≠ MIGRATION EFFECT VERIFIED ≠ DATA LOADED ≠ DATA PROVENANCE VERIFIED
```

Confidence: **VERIFIED** (read directly in this task) · **STRONGLY SUPPORTED**
(multiple independent artefacts agree, at least one machine-read) · **PLAUSIBLE**
(single documentary or naming indication) · **UNKNOWN** (not obtainable without
crossing the safety boundary).

Database classification: `PRINCIPAL` · `EPHEMERAL` · `SUPABASE INTERNAL` ·
`ARTEFACT-ONLY` · `UNCLASSIFIED`.

## 3. Physical instance inventory

A "physical instance" is an independent PostgreSQL **server / data directory**: a Docker
container with its own PGDATA volume, a native cluster, or a hosted project. One instance
may contain many **logical databases**.

### INST-01 — `carbon_ledger` local Supabase stack (RUNNING) — the dominant instance

| Property | Value | Evidence |
|---|---|---|
| Supabase project id | `carbon_ledger` | `supabase/config.toml` in **both** repositories (`project_id = "carbon_ledger"`) |
| DB container | `supabase_db_carbon_ledger`; created `2026-09-01T11:41:51Z`; `Up 38 hours (healthy)` | `docker ps`, `docker inspect` |
| Image | `public.ecr.aws/supabase/postgres:17.6.1.147` | `docker inspect` |
| Volume | `supabase_db_carbon_ledger`, created `2026-08-23T14:28:13+06:00` | `docker volume inspect` |
| Published port | `0.0.0.0:54426 → 5432` | `ss -ltnp`, `docker ps` |
| Server version | PostgreSQL **17.6** | `select version()` |
| Extensions | `pg_trgm 1.6`, `pgcrypto 1.3`, `plpgsql 1.0`, `uuid-ossp 1.1` | `pg_extension` per DB |
| Companion services | `supabase_kong_carbon_ledger` (:54425), `supabase_studio_carbon_ledger` (:54423), `supabase_auth_carbon_ledger`, `supabase_rest_carbon_ledger`, `supabase_realtime_carbon_ledger`, `supabase_storage_carbon_ledger`, `supabase_pg_meta_carbon_ledger`, `supabase_inbucket_carbon_ledger` — all `Up 38 hours`; `supabase_edge_runtime_carbon_ledger` **Exited (255)** 3 weeks ago | `docker ps -a` |
| Logical databases | **78** (71 with `ct_` prefix + 7 others) | `pg_database where not datistemplate` (twice-confirmed) |
| Port history | The same volume has been served on **5432x** ports (repo B `config.toml`) and **5442x** ports (repo A `config.toml`) at different times — §7 | two configs; volume created 2026-08-23, container recreated 2026-09-01 |
| What the Supabase API exposes | The **`postgres`** database of this instance (`supabase_rest_carbon_ledger` has `PGRST_DB_URI → supabase_db_carbon_ledger:5432/postgres`) | `docker inspect` |

### INST-02 — `carbontally_e2e` isolated E2E Supabase stack (STOPPED)

| Property | Value | Evidence |
|---|---|---|
| Project id | `carbontally_e2e` | `e2e/environment/supabase/config.toml` (exists in both repositories) |
| Ports | API `55325`, DB `55326`, Studio `55323`, SMTP `55324`, shadow `55320`, pooler `55329`, analytics `55327` | same config |
| DB container | `supabase_db_carbontally_e2e`, image `postgres:17.6.1.159`, created `2026-09-11T11:10:20Z`, **Exited (255) "2 weeks ago"** | `docker inspect` |
| Volume | `supabase_db_carbontally_e2e`, created `2026-09-11T17:10:19+06:00` | `docker volume inspect` |
| Rest of stack | `supabase_{kong,auth,rest,realtime,storage,studio,pg_meta,edge_runtime,inbucket}_carbontally_e2e` — all **Exited (255)** | `docker ps -a` |
| `POSTGRES_DB` | `postgres` | `docker inspect` env (name only) |
| Contents | **NOT INSPECTED — UNKNOWN** (cluster stopped; starting it is outside the safety boundary) | — |
| Documented purpose | Isolated E2E environment created by `CT-P6-2F-ENV-IMPL-20260911-001` ("Second Supabase project `carbontally_e2e`, ports 553xx; copy of the 53 migrations; migrate as `postgres` then `supabase_admin`") | `docs/cline/prompt-history/CT-P6-2F-ENV-IMPL-20260911-001.md`, `CARBONTALLY_P6_2F_E2E_ENVIRONMENT_IMPLEMENTATION_REPORT.md` |

### INST-03 — `ct_p3_verify_pg` standalone Postgres container (STOPPED, no volume)

| Property | Value | Evidence |
|---|---|---|
| Container | `ct_p3_verify_pg`, image `postgres:17.6.1.159`, created `2026-09-23T12:31:51Z`, **Exited (255) "3 days ago"** | `docker inspect` |
| Historical port | `127.0.0.1:55440 → 5432` | `docker ps -a` |
| Storage | **No volume, no bind mount** → PGDATA in the container writable layer (`/var/lib/postgresql/data`) | `docker inspect` `.Mounts` empty |
| Env (names only) | `POSTGRES_DB=postgres`, `POSTGRES_USER=supabase_admin` | `docker inspect` |
| Contents | **NOT INSPECTED — UNKNOWN** (stopped; not started) | — |
| Purpose | Standalone fresh Postgres for a "P3" verification run, 2026-09-23/24 | naming + creation date |

### INST-04 — Host system PostgreSQL 18 (RUNNING, contents unknown)

| Property | Value | Evidence |
|---|---|---|
| Process | `/usr/lib/postgresql/18/bin/postgres -D /var/lib/postgresql/18/main -c config_file=/etc/postgresql/18/main/postgresql.conf`, up since Sep 24 | `ps -ef` |
| Listener | `127.0.0.1:5432` only | `ss -ltnp` |
| Contents | **UNKNOWN** — `sudo -n` requires interactive authentication; no credential was used or sought (task §4/§17) | `sudo -n …` → `sudo: interactive authentication is required` |
| CarbonTally relationship | **UNKNOWN.** Neither repository's configuration references port 5432 as a database target. It must be neither assumed nor excluded as a CarbonTally database | repository-wide config inspection |

### INST-05 — Windows-era `D:/carbon_ledger/.tmp_pgdata` cluster (DEAD DATA DIRECTORY)

| Property | Value | Evidence |
|---|---|---|
| Location on this host | `/home/shomonrobie/carbon_tally/.tmp_pgdata` | listing |
| `PG_VERSION` | `18` | file read |
| Recorded start command | `C:/Program Files/PostgreSQL/18/bin/postgres.exe "-D" "D:/carbon_ledger/.tmp_pgdata" "-p" "55432" -c "listen_addresses=127.0.0.1"` | `postmaster.opts` |
| `postmaster.pid` | stale (pid 20636, dir `D:/carbon_ledger/.tmp_pgdata`, port 55432) | file read |
| Size / databases | `base` 18 MB, `pg_wal` 17 MB, **3 user databases** (OIDs 1, 4, 5) | `du`, `base/` listing |
| Running now | **No** — no matching process; nothing listens on 55432 | `ps`, `ss` |
| Meaning | Preserved data directory of the **pre-Linux (Windows) CarbonTally development cluster**, when the project lived at `d:\carbon_ledger` (corroborated by `docs/audit/cline/CarbonTally_V3_Render_Runtime_Fix_Implementation_v1.0.md`: "from `d:\carbon_ledger\backend`") | documents + filesystem |
| Database names inside | **UNKNOWN** — requires starting the cluster, which is forbidden | — |

### INST-06 — `carbontally_demo_lab` stack (RUNNING; **not** a database instance)

This stack has **no PostgreSQL of its own**. It is a data-plane client of INST-01.

| Property | Value | Evidence |
|---|---|---|
| Containers | `carbontally_demo_lab_gateway` (nginx:alpine, `127.0.0.1:54430→80`), `carbontally_demo_lab_postgrest` (`postgrest:v14.5`), `carbontally_demo_lab_storage` (`storage-api:v1.69.0`) — all `Up 38 hours` | `docker ps -a` |
| Volume | `carbontally_demo_lab_storage` (created `2026-09-20T19:16:50+06:00`) | `docker volume inspect` |
| Database target | `PGRST_DB_URI → supabase_db_carbon_ledger:5432/**carbontally_demo_local**`; storage `DATABASE_URL → …/carbontally_demo_local` | `docker inspect` (password masked) |
| Tooling | `tools/demo_lab/` in repository B (`lab.py`, `lab_env.py`, `stack.py`, `provision.py`, `seed_factors.py`, `storage.py`, `run_demo_lab.sh`, `reset_demo_lab.sh`, `manifest.json`, `p12_*`, `p16*`, `p16r*`) | directory listing |
| Live connections | `postgres: main: postgres carbontally_demo_local 172.21.0.7 / 172.21.0.8 idle` | `ps -ef` (server-side session list) |
| Documented purpose | Isolated, disposable Demo Lab on the *same* cluster; `run_demo_lab.sh` / `reset_demo_lab.sh`, with the investor dataset explicitly left untouched | `CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md`, `CT-PO-P12-STEP2-IMPLEMENTATION-REPORT-20260924.md` ("the flagship's 116 tables and 975 organisations untouched") |

### INST-07 — Hosted Supabase production project (evidence: **owner-supplied only**)

| Property | Value | Evidence |
|---|---|---|
| Project ref / name / org | `pvwiojoyaqywtydzcpbg` / `CarbonTally` / `pfurlzwxdtvyljnahlnx`, region eu-west-2 | repository docs (`CARBONTALLY_DEVELOPMENT_DATABASE_BACKUP_REPORT.md`, `CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md`) |
| Current counts (owner-observed) | `organizations = 2`, `emission_factors = 7049` | Product Owner statement, carried into task §1 |
| Independent verification | **NONE in this task.** No production credential was requested, discovered, printed or used; no production connection was attempted | task §4/§17 |
| Conflicting historical finding | `CT-PROD-SUPABASE-RECON-20260911-001` (2026-09-11) recorded: no read-only production credential existed locally; the project host returned **NXDOMAIN**; production *availability* "NOT CONFIRMED"; production schema/migrations/factors "all remain `UNKNOWN`"; verdict `NOT READY — PRODUCTION STATE STILL UNKNOWN` | `docs/architecture/CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md` |
| Status of the conflict | **REQUIRES_RECONCILIATION** — both observations preserved; this census does not choose a winner | — |

### INST-08 — Non-instance data holders and artefacts discovered (**do not delete**)

| Artefact | What it evidences | Evidence |
|---|---|---|
| Docker volume `supabase_db_carbon_ledger` | All 78 logical databases of INST-01 | `docker volume inspect` |
| Docker volume `supabase_db_carbontally_e2e` | Data of the stopped E2E cluster (INST-02) | `docker volume ls/inspect` |
| `~/carbontally_db_backups/carbontally_dev_20260901T125134.dump` (2.8 MB) + `.sql` (11.5 MB) | A dump of a database named **`carbontally_dev`** — "Dumped from database version 17.6", 2026-09-01 12:51 (+06). No database of that name exists in INST-01 today | file listing + dump header |
| `carbon_tally/backups/carbontally_v3_verified_2026-08-14.dump` (0.97 MB) | 2026-08-14 verified v3 development dump | file listing |
| `carbon_tally/backups/seed.sql` and `ct_93d5cdd/backups/seed.sql` (7.3 MB each) | The repository seed payload (also at both repo roots). **`[db.seed] enabled = false`** in both `config.toml` files → not auto-applied | file listing + configs |
| `carbon_tally/local_backups/carbon_tally_live_public_schema.sql` (232 KB) + `carbon_tally_live_public_data.sql` (1.86 MB) | 2026-08-20 capture of a **live/hosted** public schema + data; identified by `CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md` as the origin of ~142 extra `*_tenant_*` policies present in the local DB and absent from the migration chain | file listing + that document |
| `carbon_tally/local_backups/local_before_live_data_restore.sql` (364 KB) | Pre-restore snapshot of the local DB | file listing |
| `carbontally_preservation_20260916/emission_factors.*.sql`, `import_batches.*.sql`, `preservation_evidence.json` | 2026-09-16 preservation copy of the factor library recording `emission_factors rows = 7049`, `row_md5 = ee97d28a03fbe379deae89f515642999`, `distinct_activity_types = 7049`, factor sets `DEFRA-2025 = 7029` + `SEAI-2025 = 20`, `server_version = 17.6` | JSON + listing |
| `carbon_tally/CarbonTally_DB_Schema_V3M2.sql` (244 KB), `v3_schema.sql` (232 KB), `schema.sql`; `ct_93d5cdd/database/{rc1,rc2,v3}` | Schema snapshots (design/verification artefacts, not running databases) | listings |
| `carbon_tally/.tmp_pgdata` | INST-05 dead Windows data directory | filesystem |
| `~/carbon_ledger/` (empty) | Remnant of the Windows-era project path | `ls -la` |

### Directories that own **no** database (context only)

`carbon_tally` (repo A) · `ct_93d5cdd` (repo B) · `ct_local_env` (isolated local-run harness;
owns no DB, targets INST-01) · `carbon_tally_p8_release` ·
`carbon_tally_synthetic_documents` · `carbontally_p8_evidence` ·
`carbontally_preservation_20260916` · `carbontally_db_backups` · `carbon_ledger` (empty).
Non-CarbonTally containers also present (excluded from this census): `hindsight-carbontally`
(volume `hindsight-data` — memory service) and `n8n-n8n-1` (volume `n8n_n8n_data`). Nine
further unnamed exited containers (images `sha256:…`, `lux-ea`; 2026-09-02/03) belong to
other projects; none mounts a CarbonTally volume.

## 4. Logical database census — INST-01 (78 databases)

| Group | Count | Names |
|---|---|---|
| PRINCIPAL | 6 | `postgres`, `carbontally_demo_local`, `ct_local_93d5cdd`, `carbontally_qa_phase8`, `carbontally_test`, `carbontally_b2_clone_20260913` |
| SUPABASE INTERNAL | 2 | `_supabase`, `storage_vectors` |
| EPHEMERAL (`ct_*` verification clones) | 70 | see Appendix A |

* `_supabase` and `storage_vectors` are Supabase platform internals (schemas
  `_analytics`/`_supavisor`; storage vector store) — 0 public tables, 0 RLS.
* The 70 ephemeral databases were created as **clones of a principal database**
  (`CREATE DATABASE <name> TEMPLATE <source>`) by verification tasks. This is proven for
  the 2026-09-26 P17 series by shell history: `psql … -d postgres -c 'CREATE DATABASE
  ct_iv_p17m2_20260926 TEMPLATE ct_iv_p17m_c_20260926' -c '… TEMPLATE ct_p17k_20260926'`,
  executed against `127.0.0.1:54426` (= INST-01) — i.e. **COMMAND EXECUTED** and
  **DATABASE EFFECT VERIFIED** (the databases exist).
* 15 ephemeral databases carry **P17** objects (`scope3_categories`), all created
  2026-09-25/26: `ct_p17_09_verify_20260925`, `ct_p17_10_verify_20260925`,
  `ct_p17_migcheck_20260925`, `ct_p17k_20260926`, `ct_p17k_ctl_20260926`,
  `ct_p17l_surface_20260926`, `ct_p17m_full_20260926`, `ct_p17m_nocat_20260926`,
  `ct_p17m_verify_20260926`, `ct_iv_p17m2_20260926`, `ct_iv_p17m2_clean_20260926`,
  `ct_iv_p17m_b_20260926`, `ct_iv_p17m_c_20260926`, `ct_m3_nocat_20260926153335`,
  `ct_m3_suite_20260926154500`, `ct_m3_verify_20260926153100`. **No principal or
  durable database contains P17 objects.**

The complete 78-row table (size, public tables, RLS tables, `organizations`,
`public.users`, `emission_factors`, modern-capability flags, classification) is
**Appendix A** at the end of this document; it is machine-generated from the catalogue
reads so that no number is transcribed by hand.

## 5. Schema census — principal databases

All values below are direct catalogue reads (2026-09-27). RLS is enabled on **every**
public table in every principal database (`rls_tables = public tables` in all six);
P17 objects are absent from all six.

| Measure | `postgres` | `carbontally_demo_local` | `ct_local_93d5cdd` | `carbontally_qa_phase8` | `carbontally_test` | `carbontally_b2_clone_20260913` |
|---|---|---|---|---|---|---|
| Size | 38 MB | 23 MB | 16 MB | 19 MB | 14 MB | 18 MB |
| Public tables | 116 | 141 | 135 | 133 | 117 | 128 |
| `auth` tables | 23 | 23 | **0** | 23 | **0** | 23 |
| RLS-enabled tables | 116 | 141 | 135 | 133 | 117 | 128 |
| public RLS policies | **174** | **298** | **218** | 197 | 198 | 189 |
| public functions | 21 | — | 55 | — | — | — |
| `supabase_migrations` ledger | **46 rows** (max `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql`) | ledger table absent | ledger table absent | ledger table present, **0 rows** | ledger table absent | ledger table present, **0 rows** |
| Evidence | `db06`, `db08` | `db06`, `db08` | `db06`, `db08` | `db05`, `db08` | `db05`, `db08` | `db05` |

**Schema-generation capability matrix** (`T` = object exists):

| Object family | `postgres` | `carbontally_demo_local` | `ct_local_93d5cdd` | `carbontally_qa_phase8` |
|---|---|---|---|---|
| P16 disclosure (`disclosure_frameworks`, `_values`) | **absent** | present | present | present |
| P16R (`report_version_artifacts`, `disclosure_intensity_ratios`) | **absent** | present | present | present (intensity present in qa clone) |
| B2 evidence (`evidence_line_items`) | **absent** | present | present | present |
| Manual processing (`manual_processing_grants`) | **absent** | present | present | **absent** |
| Insight (`carbontally_insight_conversations`, 4-table family) | **absent** | present | **absent** | **absent** |
| P17 (`scope3_categories` et al., 145-table generation) | **absent** | **absent** | **absent** | **absent** |

Reading of this matrix: **the three most "modern" schema generations live in different
databases** — P16/P16R/B2 in `carbontally_demo_local` **and** `ct_local_93d5cdd`,
Insight only in `carbontally_demo_local`, P17 only in disposable `ct_*` clones, and the
richest dataset (`postgres`) sits on the **oldest** 116-table schema.

### `postgres` (INST-01) — "the flagship"

* 116 public tables; **no** `evidence_line_items`, **no** `report_version_artifacts`,
  **no** `source_line_item_id`-bearing generation, **no** disclosure tables, **no**
  `carbontally_insight_*`, **no** P17.
* Ledger: 46 applied migrations, ending at `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql`
  (2026-09-03) — i.e. it has **not** received the P8-era migrations
  (`2026091x`/`2026092x`) nor any P16/P16R/P17 migration.
* RLS policies 174 (vs 218 in `ct_local_93d5cdd`) — consistent with the historical
  finding in `CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md` that the local DB carries
  ≈142 additional `*_tenant_*` policies that came from the 2026-08-20 **live-schema
  restore**, not from the migration chain.
* Serves the Supabase API (`PGRST_DB_URI → …/postgres`), which is why the Product Owner's
  Studio/API observations (975 organisations, 7049 emission factors) resolve to this
  database.
* Billed and messaging tables present (`customer_subscriptions`, `billing_*`,
  `notifications`, `conversations`, `messages`, `email_logs`).

### `carbontally_demo_local` (INST-01) — Demo Lab

* 141 public tables; the most modern **durable** schema: P16 disclosure, P16R artifacts,
  B2 evidence, manual-processing grants, **and** the four `carbontally_insight_*` tables.
* No migration ledger at all; its schema was provisioned by `tools/demo_lab`
  (`stack.py`/`provision.py`) rather than by Supabase CLI migration history.
* Factor library present with `import_batch_id` set on all rows and 2 `import_batches`
  rows → imported through the Demo Lab's own factor-import path, **not** the legacy
  generated-SQL path used by `postgres`.
* Storage: 2 buckets (`documents`, `report-artifacts`), 38 objects.

### `ct_local_93d5cdd` (INST-01) — READINESS-02 / latest-repo local run

* 135 public tables; 218 policies; 55 public functions; **`auth` schema absent entirely**
  (`auth.users` does not exist).
* P16/P16R/B2/manual-grant objects present; Insight and P17 absent.
* No migration ledger. `ct_local_env/README.md` (2026-09-19) records "135 public tables,
  **67 migrations applied** from `supabase/migrations`; the F-039-1-J uniqueness index and
  218 RLS policies are present" — i.e. the schema was built by applying migration files
  directly (`psql`), not by the Supabase CLI, which is why no ledger exists. The policy
  count (218) and table count (135) independently match this census.
* Because the `auth` schema is absent, Supabase-Auth-dependent behaviour (login, JWT
  →`auth.uid()` RLS, identities, sessions) **cannot** be validated against this database.

### `carbontally_qa_phase8`, `carbontally_test`, `carbontally_b2_clone_20260913`

* `carbontally_qa_phase8` — 133 tables, `auth` present, 25 organisations (all named
  `Test Co`/`System`, created 2026-09-14), 498 `public.users`, disclosure corpus
  471 framework versions / 1069 requirement versions, **0** `emission_factors`.
* `carbontally_test` — 117 tables, **no `auth` schema**, 748 `public.users`, 3 organisations,
  2 `customer_factors`, 1 bucket. This is the database named by the integration-test
  conftest default (`…:54326/carbontally_test`) and therefore the **F-046-1 destructive
  `TRUNCATE … RESTART IDENTITY CASCADE` target**.
* `carbontally_b2_clone_20260913` — 128 tables, 35 organisations, 87 users, 2 factors,
  37 report versions, a 0-row ledger table.

## 6. Migration census

| Item | Repository A (`carbon_tally`) | Repository B (`ct_93d5cdd`) |
|---|---|---|
| Migration files in `supabase/migrations/` | **68** | **89** |
| Latest migration file | `20260924000000_p8x_x2_operational_telemetry_retention.sql` | `20261020000000_p17k_governed_capability_catalogue.sql` |
| Migrations ≥ `202610` (P17 series) | 0 (max `20260924…`) | 6 (`2026101x`, `2026102x`) |
| HEAD | `20b7a92` (2026-09-16) | `cb70fd6` (2026-09-26) |

Application status **per database** (never inferred from file existence alone):

| Database | Ledger rows | Highest ledger version | Object-based conclusion | Classification |
|---|---|---|---|---|
| `postgres` | 46 | `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` | 116 tables; lacks every object introduced after 2026-09-03 (P8 telemetry/lifecycle, B2 evidence, P16 disclosure, P16R artifacts, Insight, P17) | **CONFIRMED_APPLIED (46)**; all later migrations **CONFIRMED_NOT_APPLIED** by object absence |
| `carbontally_demo_local` | 0 (no ledger) | — | 141 tables incl. P16/P16R/B2/Insight; provisioned by `tools/demo_lab`, not by migration replay | **OBJECTS_PRESENT_APPLICATION_TIME_UNKNOWN** for those generations; **CONFIRMED_NOT_APPLIED** for P17 |
| `ct_local_93d5cdd` | 0 (no ledger) | — | 135 tables; `ct_local_env/README.md` states 67 migrations applied on 2026-09-19; P16/P16R/B2 present, Insight/P17 absent | **CONFIRMED_APPLIED (67; documented + object-corroborated)**; later migrations **CONFIRMED_NOT_APPLIED** |
| `carbontally_qa_phase8` | table exists, 0 rows | — | 133 tables; P16/P16R present, manual-grants absent | **OBJECTS_PRESENT_APPLICATION_TIME_UNKNOWN** |
| `carbontally_test` | none | — | 117 tables; no `auth` schema; insight tables present | **PARTIAL / UNKNOWN** (harness `TRUNCATE`s it — object state is transient) |
| `carbontally_b2_clone_20260913` | table exists, 0 rows | — | 128 tables; P16R/B2 present | **OBJECTS_PRESENT_APPLICATION_TIME_UNKNOWN** |
| 70 `ct_*` ephemeral | none (two have 0-row ledger tables) | — | 97–145 tables each, matching whichever principal DB each was cloned from | **PARTIAL / UNKNOWN** (deliberate disposable clones) |

**Repo-side drift status.** READINESS-01 established that the *repository* migration set is
internally clean (0 anomalies in the repo-side comparator). The drift risk in this
environment is therefore not repository drift but **database-generation divergence**: six
principal databases carry four different schema generations, and **no database carries the
canonical 89-file generation**.

## 7. Configuration and port topology

| Configuration file | `project_id` | API | DB | Studio | SMTP | shadow | migration/seed flags |
|---|---|---|---|---|---|---|---|
| `carbon_tally/supabase/config.toml` | `carbon_ledger` | **54425** | **54426** | **54423** | 54424 | 54420 | `[db.migrations] enabled = false`; `[db.seed] enabled = false` |
| `ct_93d5cdd/supabase/config.toml` | `carbon_ledger` | **54325** | **54326** | **54323** | 54324 | 54320 | `[db.migrations] enabled = true`; `[db.seed] enabled = false` |
| `ct_93d5cdd/e2e/environment/supabase/config.toml` (and repo A equivalent) | `carbontally_e2e` | 55325 | 55326 | 55323 | 55324 | 55320 | isolated E2E project |
| `carbon_tally/config.toml` | *(not a Supabase config — `[mcp]` only)* | — | — | — | — | — | — |

**Both repositories declare the same Supabase project id (`carbon_ledger`), differing only
in ports.** Because the Supabase CLI names containers/volumes by project id, the two
configurations address **the same Postgres data volume** (`supabase_db_carbon_ledger`,
created 2026-08-23). This resolves the apparent "port confusion" in earlier reports:

* the volume was created 2026-08-23 — matching
  `CARBONTALLY_V3_PLATFORM_FINALIZATION_REPORT.md`: "The new Docker stack
  (`supabase_*_carbon_ledger`) was created **2026-08-23 16:47**";
* the **current** containers were (re)created 2026-09-01 and publish the **5442x** mapping
  → the running stack corresponds to repository A's `config.toml`;
* repository B's `5432x` mapping is the *same project* started from repository B — which is
  exactly why `carbon_tally/.env` (root) points at `127.0.0.1:54326/postgres` while
  `carbon_tally/backend/.env` points at `127.0.0.1:54426/postgres`;
* documents describing "an older stack at 54323–54326 still running" alongside
  "54423–54426" are therefore most plausibly describing **one cluster addressed through two
  port mappings**, not two storage instances. Only one `supabase_db_carbon_ledger` volume
  exists and only one such container is present, so the *simultaneous two-stack* reading is
  **not reproducible from current Docker state** → `REQUIRES_RECONCILIATION`.

### Environment-file targets (values masked; keys and non-secret metadata only)

| File | Database URL target | Supabase URL target | API port |
|---|---|---|---|
| `carbon_tally/.env` | `…:54326/postgres` (not currently listening) | `http://127.0.0.1:54325` (not currently listening) | `PORT=3000` |
| `carbon_tally/backend/.env` | `…:54426/postgres` (**INST-01 flagship**) | `http://127.0.0.1:54425` (**running**) | `PORT=8050` |
| `carbon_tally/frontend/.env` | — | `http://127.0.0.1:54425` | API `http://localhost:8050` |
| `ct_93d5cdd/backend/.env` | `…:54426/ct_local_93d5cdd` (**INST-01, 25-org DB**) | `http://127.0.0.1:19999` (deliberate unroutable placeholder) | `PORT=8060` |
| `ct_local_env/demo_lab/backend.env` | `…:54426/carbontally_demo_local` (**INST-01, Demo Lab**) | `http://127.0.0.1:54430` (Demo Lab gateway) | — |

Other `.env*` artefacts found (key names only, values not reproduced):
`carbon_tally/.env.local`, `carbon_tally/.env.test`, `carbon_tally/backend/.env.bak`,
`carbon_tally/frontend/.env.production`, `carbon_tally/admin/.env*`,
`carbon_tally/local_backups/env_backup/.env*`, `carbon_tally/e2e/environment/.env.e2e`,
`carbon_tally/e2e/environment/.env.personas`, `carbon_tally/tests/e2e/.env.personas`,
`carbon_tally/tools/carbon_data_factory/.env`, `ct_93d5cdd/frontend/.env.local`,
`ct_93d5cdd/admin/.env.development.local`.

## 8. Provisioning tooling inventory (who creates which database)

| Tooling | Repository | What it provisions / targets | Evidence class |
|---|---|---|---|
| `supabase/` CLI project (`project_id = carbon_ledger`) | both | INST-01 stack and its `postgres` database; `migrations/` = 68 (A) / 89 (B) files | CONFIG + containers |
| `tools/demo_lab/{run_demo_lab.sh,reset_demo_lab.sh,stack.py,provision.py,seed_factors.py,storage.py,manifest.json}` | B | the `carbontally_demo_local` database **inside INST-01** plus the `carbontally_demo_lab_*` containers and gateway :54430 | CODE + running containers + live DB sessions |
| `tools/seed_investor_demo/{__main__,seed_core,seed_documents,seed_messaging,seed_aux,pipeline,synthetic,reset,verify,client,config,safety}.py` + `DEMO_IDENTITIES.md` + `demo_manifest.json` | **A only** (absent from B) | the investor-demo dataset in `postgres`; `config.py` defaults `SUPABASE_URL → http://127.0.0.1:54425` (INST-01) and refuses non-local environments (`safety.assert_local_environment`) | CODE + DATA (row timestamps) + docs |
| `ct_local_env/{start_latest.sh,stop_latest.sh,seed_local_identities.py,local_verify.py}` | harness dir | the `ct_local_93d5cdd` database **inside INST-01** (repo B backend on :8060) | CODE + README + data |
| `tools/demo_lab/*` P17/P16 verification suites (`p16r*`, `p17*` in `backend/tests/integration/` of repo B) | B | the 70 `ct_*` ephemeral clones inside INST-01 (`CREATE DATABASE … TEMPLATE …`), incl. all 15 P17 databases | CODE + shell history + catalogue |
| `e2e/environment/scripts/{bootstrap,reset,apply_migrations}.sh` + `e2e/environment/supabase/config.toml` | both | INST-02 (`carbontally_e2e`, ports 553xx) with a copied migration set | CODE + config + stopped containers/volume |
| `backend/tests/integration/conftest.py` | both | `INTEGRATION_DATABASE_URL`, default `…:54326/carbontally_test`; **destructive `TRUNCATE … RESTART IDENTITY CASCADE`** (15 tables) and an **F-046-1 guard** that refuses targets named `qa`/`demo`/`investor`/`prod`/`live` or the two forbidden main DB names (`postgres`, `supabase_db_carbon_ledger`) | CODE + docs |
| `tools/carbon_data_factory`, `demodatagen/`, `generate_synthetic_documents.py`, `carbon_tally_synthetic_documents/` | A / both | synthetic document/factor generators feeding the local DBs | CODE (not executed by this task) |
| `output/sql/emission_factors.sql` (DEFRA), `output/seai_2025/sql` (SEAI) | A | the **generated idempotent SQL** that loaded the 7049 factors into `postgres` | CODE + docs + data (`import_batch_id IS NULL`) |

## 9. Data census — headline values (exact, 2026-09-27)

### `postgres` (the PO's current local Supabase database — richest dataset)

| Table | Rows |
|---|---|
| `organizations` | **975** (created 2026-08-22 16:53:32Z → 2026-08-28 22:42:27Z; 9 of them named `Test Co`) |
| `organization_members` | 1,125 |
| `auth.users` / `public.users` | **1,206** / **1,344** |
| `staff_profiles` | 21 |
| `consultant_profiles` | 55 |
| `consultant_clients` | **917** |
| `consultant_firm_members` | 54 |
| `processing_entities` | 11 |
| `assets` / `facilities` / `vehicles` | 310 / 157 / 3 |
| `suppliers` | 156 |
| `customer_factors` | 245 |
| `organization_files` / `customer_documents` | 263 / 0 |
| `manual_extraction_items` / `manual_review_queue` | 264 / 2 |
| `calculation_snapshots` / `emissions_logs` | 100 / 100 |
| `report_versions` / `report_generation_queue` | 17 / 14 |
| `emission_factors` | **7,049** |
| `import_batches` | 0 |
| storage | 1 bucket (`documents`, private) with **685 objects** |

### `carbontally_demo_local` (Demo Lab)

`organizations` 4 · `public.users` 14 (all have `auth.users` rows; `auth.identities` 0) ·
`emission_factors` **7,049** · `import_batches` 2 · `organization_files` 38 ·
`manual_extraction_items` 38 · `calculation_snapshots` 34 · `emissions_logs` 34 ·
`evidence_line_items` 67 · `report_versions` 4 · `assets` 1 · `facilities` 1 ·
`suppliers` 1 · `consultant_profiles` 1 · `consultant_clients` 2 · `processing_entities` 2 ·
storage: 2 buckets, 38 objects · `disclosure_framework_versions` 0.

### `ct_local_93d5cdd` (READINESS-02 database)

`organizations` **25** (created 2026-09-19 03:43:07Z → 13:00:36Z) · `public.users` 658 ·
`organization_members` 16 · `emission_factors` **0** · `customer_factors` 5 ·
`processing_entities` 7 · `consultant_profiles` 3 · `consultant_clients` 3 ·
`consultant_firm_members` 4 · `staff_profiles` 5 · `manual_extraction_items` 1 ·
calculation/snapshot/evidence/report rows **0** · storage 1 bucket ·
**no `auth` schema**.

Organisation names (all 25): `System`; 20 × `Test Co`; `D35 Candidate Org`;
`D35 Private Org`; `Local Demo Customer`; `Local Other Tenant`.

## 10. Factor-library provenance cross-check (machine-verified)

| Database | Rows | Row-identity hash (`md5` of ordered `id`s) | Factor-content hash (`md5` of ordered source~set~activity~unit~scope~multiplier~country) | `import_batch_id` | Rows created (UTC) |
|---|---|---|---|---|---|
| `postgres` | 7,049 | `93668772ba460b0d03c7d9f9029f16c9` | **`eefbcf6e3d26ea6d908bac182fe4a309`** | all NULL (0 batches) | 2026-08-26 14:04:22 → 14:04:26 |
| `carbontally_demo_local` | 7,049 | `e7c28218636fc5fee2ddb79bd1058312` | **`eefbcf6e3d26ea6d908bac182fe4a309`** | 2 distinct batches (0 NULL) | 2026-09-24 10:15:16 → 10:15:20 |
| `ct_v078_t2b` / `ct_v078_t2b_tests` | 7,029 each | — | `b50c9f4f8fa02e166c25bfdb761d3b73` (content hash; DEFRA-only era) | 1 batch | — |

**Conclusion (VERIFIED):** the two databases that hold 7,049 factors hold **content-identical
libraries** (identical multiset of source/set/activity/unit/scope/multiplier/country) even
though the row `id`s differ (independent imports). The 7,029-row clones are the earlier
DEFRA-only state, consistent with the documented sequence "DEFRA 7,029 → +SEAI 20 → 7,049".

## 11. Known unknowns and deliberately NOT-inspected items

| Item | Status | Why |
|---|---|---|
| INST-02 `carbontally_e2e` database contents | **UNKNOWN** | cluster stopped; starting it is outside the safety boundary (task §3) |
| INST-03 `ct_p3_verify_pg` contents | **UNKNOWN** | container stopped; no volume; not started |
| INST-04 host PostgreSQL 18 (port 5432) databases | **UNKNOWN** | `sudo` requires interactive authentication; no credential used |
| INST-05 `D:/carbon_ledger/.tmp_pgdata` database names | **UNKNOWN** | requires starting the cluster |
| Production (INST-07) schema, migrations, factor identity, P17 presence | **UNKNOWN / owner-evidence only** | no read-only production credential exists locally (per 2026-09-11 reconciliation); no production access attempted |
| INST-01 volume size on disk | **UNKNOWN** | `du` over `/var/snap/docker/...` volumes returned no output for this user |
| Whether the production 7,049 factors are byte-identical to the local 7,049 | **UNKNOWN** | production not reachable; local content hash recorded above for future comparison |
| Whether `cabontally_dev` (dump, 2026-09-01) ever existed as a live database | **STRONGLY SUPPORTED** (dump header records it) but no remaining catalogue evidence | the database is absent from INST-01 today |
| Exact creating task for each individual `ct_*` clone | **PLAUSIBLE** by name/date (e.g. `ct_p17k_20260926` ← P17K verification; `ct_v078_t2b` ← V0.7.8 T2B) | the clones pre-date/succeed documented tasks; only the 2026-09-26 P17 clones have direct shell-history proof |

## 12. Boundaries observed by this task

* No database was written to; the only statements executed were `SELECT`/catalogue reads.
* No container, cluster or database was started, stopped, created, dropped or repaired.
* No `.env`, `config.toml`, migration, test, source file, RLS policy or Git state was
  modified. `git status` was not used to alter anything; no commit, push or checkout ran.
* No secret value appears in this document: database URLs are truncated before the
  credentials, keys are shown as `<redacted>` or `<set>`, and the one shared demo password
  recorded in `DEMO_IDENTITIES.md` is deliberately **not** reproduced.










## Appendix A — complete 78-database census table (machine-generated from catalogue reads)

Legend — *public tables* = `public` BASE TABLEs; *RLS tables* = relations with `relrowsecurity = true`; *organizations*/*public.users*/*emission_factors* = row counts; *modern capabilities* = presence (`T`) of P16 disclosure, P16R artifacts, B2 evidence, manual-processing grants, Insight, P17 `scope3_categories`.

| DB name | size | public tables | RLS tables | organizations | public.users | emission_factors | modern capabilities present | classification |
|---|---|---|---|---|---|---|---|---|
| `_supabase` | 7507 kB | 0 | 0 |  |  |  | — | SUPABASE INTERNAL (_analytics/_supavisor) |
| `carbontally_b2_clone_20260913` | 18 MB | 128 | 128 | 35 | 87 | 2 | Evidence, P16 disclosure | PRINCIPAL — B2 clone |
| `carbontally_demo_local` | 23 MB | 141 | 141 | 4 | 14 | 7049 | Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | PRINCIPAL — Demo Lab (T2C/P12) |
| `carbontally_qa_phase8` | 19 MB | 133 | 133 | 25 | 498 | 0 | Evidence, P16 disclosure, Rpt artifacts | PRINCIPAL — Phase-8 QA |
| `carbontally_test` | 14 MB | 117 | 117 | 3 | 748 | 0 | Insight | PRINCIPAL — integration-test DB (harness TRUNCATE target) |
| `ct_4a1b_20260914` | 17 MB | 133 | 133 | 0 | 0 | 0 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_4a1b_verify_20260914` | 17 MB | 133 | 133 | 0 | 0 | 0 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_b2_iv_20260913` | 19 MB | 128 | 128 | 154 | 57 | 24 | Evidence, P16 disclosure | EPHEMERAL — B/T-series verification clone |
| `ct_b3_v3_20260913` | 18 MB | 131 | 131 | 13 | 182 | 0 | Evidence, P16 disclosure | EPHEMERAL — B/T-series verification clone |
| `ct_b4v4_20260914` | 18 MB | 133 | 133 | 13 | 182 | 0 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — B/T-series verification clone |
| `ct_base_cmp` | 14 MB | 115 | 115 | 20 | 795 | 4 | — | EPHEMERAL — verification clone |
| `ct_d17d32_chain` | 7707 kB | 0 | 0 |  |  |  | — | EPHEMERAL — verification clone |
| `ct_d17d32_chainp` | 14 MB | 134 | 134 | 0 | 0 | 0 | Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — verification clone |
| `ct_d17rev_lab` | 7811 kB | 3 | 0 |  | 0 |  | — | EPHEMERAL — verification clone |
| `ct_f0391_065` | 14 MB | 115 | 115 | 11 | 673 | 4 | — | EPHEMERAL — verification clone |
| `ct_f0391_067_pre` | 14 MB | 115 | 115 | 10 | 653 | 4 | — | EPHEMERAL — verification clone |
| `ct_fin_impl_20260916` | 19 MB | 134 | 134 | 35 | 49 | 2 | Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — verification clone |
| `ct_i1_verify_20260921` | 14 MB | 117 | 117 | 25 | 655 | 0 | Insight | EPHEMERAL — verification clone |
| `ct_i2_rls_clean` | 14 MB | 117 | 117 | 23 | 652 | 0 | Insight | EPHEMERAL — I-series verification clone |
| `ct_i2_verify_20260921` | 15 MB | 117 | 117 | 3 | 7 | 1 | Insight | EPHEMERAL — I-series verification clone |
| `ct_i3_reverify_20260921` | 19 MB | 133 | 133 | 35 | 60 | 2 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — I-series verification clone |
| `ct_i4_case_b` | 15 MB | 118 | 118 | 3 | 7 | 1 | Insight | EPHEMERAL — I-series verification clone |
| `ct_i4_diag_20260921` | 15 MB | 119 | 119 | 3 | 11 | 1 | Insight | EPHEMERAL — I-series verification clone |
| `ct_i4_remediate_20260921` | 15 MB | 119 | 119 | 3 | 7 | 1 | Insight | EPHEMERAL — I-series verification clone |
| `ct_i4_reverify_20260921` | 16 MB | 119 | 119 | 3 | 11 | 1 | Insight | EPHEMERAL — I-series verification clone |
| `ct_i4_rv_atomic` | 15 MB | 119 | 119 | 3 | 7 | 1 | Insight | EPHEMERAL — I-series verification clone |
| `ct_i4_rv_integration` | 15 MB | 117 | 117 | 3 | 7 | 1 | Insight | EPHEMERAL — I-series verification clone |
| `ct_i4_sens_fresh` | 15 MB | 118 | 117 | 3 | 7 | 1 | Insight | EPHEMERAL — I-series verification clone |
| `ct_i4_verify_20260921` | 15 MB | 118 | 117 | 3 | 7 | 1 | Insight | EPHEMERAL — I-series verification clone |
| `ct_int_20260914` | 20 MB | 133 | 133 | 87 | 585 | 15 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_iv066_api` | 14 MB | 115 | 115 | 47 | 686 | 4 | — | EPHEMERAL — verification clone |
| `ct_iv_d4_20260916` | 19 MB | 133 | 133 | 35 | 49 | 2 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_iv_d4b_20260916` | 19 MB | 133 | 133 | 35 | 49 | 2 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_iv_p17m2_20260926` | 16 MB | 145 | 145 | 3 | 228 | 0 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_iv_p17m2_clean_20260926` | 18 MB | 145 | 145 | 5 | 63 | 4 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_iv_p17m_20260926` | 22 MB | 141 | 141 | 4 | 14 | 7049 | Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_iv_p17m_b_20260926` | 16 MB | 145 | 145 | 3 | 1 | 0 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_iv_p17m_c_20260926` | 17 MB | 145 | 145 | 192 | 223 | 2 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_iv_replay_20260916` | 11 MB | 97 | 97 | 0 | 0 | 0 | — | EPHEMERAL — verification clone |
| `ct_local_93d5cdd` | 16 MB | 135 | 135 | 25 | 658 | 0 | Evidence, P16 disclosure, Rpt artifacts, Manual grants | PRINCIPAL — READINESS-02 / latest-repo local run |
| `ct_m3_nocat_20260926153335` | 17 MB | 145 | 145 | 0 | 0 | 0 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_m3_suite_20260926154500` | 18 MB | 145 | 145 | 3 | 65 | 0 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_m3_verify_20260926153100` | 18 MB | 145 | 145 | 5 | 63 | 4 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_p17_09_verify_20260925` | 17 MB | 145 | 145 | 110 | 112 | 6 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_p17_10_verify_20260925` | 17 MB | 145 | 145 | 110 | 119 | 6 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_p17_migcheck_20260925` | 16 MB | 145 | 145 | 0 | 0 | 0 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_p17k_20260926` | 18 MB | 145 | 145 | 5 | 63 | 4 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_p17k_ctl_20260926` | 17 MB | 145 | 145 | 1 | 125 | 0 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_p17l_surface_20260926` | 18 MB | 145 | 145 | 3 | 246 | 0 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_p17m_full_20260926` | 19 MB | 145 | 145 | 19 | 187 | 9 | P17 scope3, Insight, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_p17m_nocat_20260926` | 16 MB | 135 | 135 | 25 | 658 | 0 | Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_p17m_verify_20260926` | 18 MB | 139 | 139 | 243 | 720 | 16 | P17 scope3, Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — P17 verification clone |
| `ct_p2_backup_20260916` | 7571 kB | 0 | 0 |  |  |  | — | EPHEMERAL — verification clone |
| `ct_p5_restore_20260916` | 7907 kB | 5 | 0 | 3 |  | 3 | Manual grants | EPHEMERAL — verification clone |
| `ct_p5_src_20260916` | 8011 kB | 5 | 1 | 3 |  | 3 | Manual grants | EPHEMERAL — verification clone |
| `ct_p8_rehearsal_20260915` | 19 MB | 133 | 133 | 35 | 49 | 2 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_rls4a2_20260914` | 17 MB | 133 | 133 | 0 | 0 | 0 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_rls4a2_reg_20260914` | 19 MB | 133 | 133 | 78 | 609 | 6 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_s13_iv_20260914` | 17 MB | 133 | 133 | 23 | 4 | 0 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_step2_070` | 16 MB | 135 | 135 | 21 | 669 | 4 | Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — verification clone |
| `ct_t2b_defra` | 19 MB | 136 | 136 | 0 | 0 | 0 | Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — B/T-series verification clone |
| `ct_t2c_tests` | 19 MB | 129 | 127 | 0 | 0 | 0 | P16 disclosure, Manual grants | EPHEMERAL — B/T-series verification clone |
| `ct_v069` | 14 MB | 115 | 115 | 2 | 739 | 0 | — | EPHEMERAL — verification clone |
| `ct_v069_dup` | 14 MB | 115 | 115 | 24 | 652 | 0 | — | EPHEMERAL — verification clone |
| `ct_v069_nofix` | 14 MB | 115 | 115 | 10 | 656 | 4 | — | EPHEMERAL — verification clone |
| `ct_v071` | 14 MB | 115 | 115 | 10 | 744 | 4 | — | EPHEMERAL — verification clone |
| `ct_v071_full` | 16 MB | 135 | 135 | 21 | 657 | 4 | Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — verification clone |
| `ct_v078_t2b` | 25 MB | 129 | 127 | 0 | 0 | 7029 | P16 disclosure, Manual grants | EPHEMERAL — verification clone |
| `ct_v078_t2b_tests` | 24 MB | 129 | 127 | 0 | 0 | 7029 | P16 disclosure, Manual grants | EPHEMERAL — verification clone |
| `ct_v73_rls2_20260919` | 16 MB | 135 | 135 | 43 | 680 | 4 | Evidence, P16 disclosure, Rpt artifacts, Manual grants | EPHEMERAL — verification clone |
| `ct_v73_rls_20260919` | 14 MB | 115 | 115 | 42 | 672 | 4 | — | EPHEMERAL — verification clone |
| `ct_x1_20260914` | 17 MB | 133 | 133 | 23 | 3 | 0 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_x2_20260914` | 17 MB | 133 | 133 | 0 | 0 | 0 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_x2int_20260914` | 17 MB | 133 | 133 | 1 | 1 | 0 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_x4_20260914` | 19 MB | 133 | 133 | 1 | 502 | 0 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `ct_x7_20260915` | 19 MB | 133 | 133 | 5 | 501 | 0 | Evidence, P16 disclosure, Rpt artifacts | EPHEMERAL — verification clone |
| `postgres` | 38 MB | 116 | 116 | 975 | 1344 | 7049 | — | PRINCIPAL — flagship/investor-demo (live local dev) |
| `storage_vectors` | 7843 kB | 0 | 0 |  |  |  | — | SUPABASE INTERNAL (storage vector store) |

## Appendix B — evidence index

| Artefact | Contents |
|---|---|
| `/tmp/db01_net.txt` | `ss -ltnp` listeners; `ps -ef` postgres processes (INST-01/INST-04) |
| `/tmp/db01_docker_ps.txt` | `docker ps -a` — 37 containers incl. all Supabase/Demo-Lab/stopped stacks |
| `/tmp/db01_docker_vol.txt`, `/tmp/db02_vols.txt` | volume list + creation timestamps |
| `/tmp/db01_home.txt`, `/tmp/db01_root_a.txt`, `/tmp/db01_root_b.txt` | filesystem inventory of `~`, repo A, repo B |
| `/tmp/db02_inspect.txt` | per-container image/labels/mounts/creation |
| `/tmp/db03_configs.txt` | masked `config.toml` key extracts (project ids, ports, migration/seed flags) |
| `/tmp/db03_tmppg.txt` | INST-05 `PG_VERSION`, `postmaster.opts`, `postmaster.pid` |
| `/tmp/db03_dblist.txt`, `/tmp/db05_census_out.txt`, `/tmp/db05_census_lines.txt` | INST-01 database list + sizes; per-database 32-table row census |
| `/tmp/db05_tables_ext.txt` | public/auth/storage/supabase_migrations table lists for the three principal DBs |
| `/tmp/db06_out.txt` | 46-row migration ledger of `postgres`; factor columns/hashes; organisation names/timestamps; auth counts; P17 object matrix |
| `/tmp/db07_*.txt` | env key inventory (masked), shell history, docs greps, seed tooling, `ct_local_env`, dumps, container envs, git/migration counts |
| `/tmp/db08_out.txt` | ledger status per DB; factor set/age detail; storage buckets/objects; capability object matrix |
| `/tmp/db09_docs.txt` | documentation/task-report hits for `seed_investor_demo` and DB topology |
| `/tmp/db10_out.txt`, `/tmp/db10_matrix_lines.txt` | 78-database capability matrix (used for Appendix A) |
| `/tmp/db11_dbs2.txt`, `/tmp/db11_diff.txt`, `/tmp/db12_*.txt` | database-list reproducibility check (difference empty) |
| `/tmp/db14_out.txt` | factor content hashes (`postgres` = `carbontally_demo_local`), policy/function counts, `Test Co` count |
| `docs/architecture/CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md` (repo A) | production identity + non-availability (INST-07) |
| `docs/audit/cline/CARBONTALLY_MIGRATION_HISTORY_RECONCILIATION.md`, `CARBONTALLY_DEVELOPMENT_DATABASE_BACKUP_REPORT.md`, `CARBONTALLY_V3_PLATFORM_FINALIZATION_REPORT.md`, `CarbonTally_V3_Test_Database_Diagnostic_v1.0.md` (repo A) | migration/factor/test-DB provenance |
| `docs/architecture/CT-PO-COMPREHENSIVE-INVESTOR-READY-PLATFORM-STUDY-20260924.md`, `CT-PO-P12-STEP2-IMPLEMENTATION-REPORT-20260924.md`, `CT-PO-INSIGHT-L7-L8-INVESTOR-DEMO-MASTER-PREFLIGHT-20260922.md` (repo B) | flagship-vs-Demo-Lab generation analysis |
| `docs/cline/prompt-history/CT-P6-2F-ENV-IMPL-20260911-001.md`, `docs/architecture/CARBONTALLY_P6_2F_E2E_ENVIRONMENT_IMPLEMENTATION_REPORT.md` (both) | INST-02 (`carbontally_e2e`) provenance |
| `tools/seed_investor_demo/DEMO_IDENTITIES.md` (repo A) | investor-demo identity manifest (counts only reproduced) |
| `ct_local_env/README.md`, `IDENTITIES.md`, `start_latest.sh` | INST-01 `ct_local_93d5cdd` provenance (READINESS-02 database) |
