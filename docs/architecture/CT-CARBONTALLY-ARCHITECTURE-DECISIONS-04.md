# CT-CARBONTALLY-ARCHITECTURE-DECISIONS-04

**Database Topology Investigation, Architecture Reconciliation, and Evidence-Based PO Decision Register**

| Item | Value |
|---|---|
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD at task start | `4e8a7feb405c4b5f1a516fd00c6a915a75bb3fb0` (`docs(foundation-03): record remediation-03 publication SHAs`) |
| GitHub tip at task start | `4e8a7feb405c4b5f1a516fd00c6a915a75bb3fb0` (`refs/heads/p8-release-reconciled`) — **0 ahead / 0 behind** |
| Prior tasks | CT-CARBONTALLY-FOUNDATION-CLOSURE-02 · CT-CARBONTALLY-FOUNDATION-REMEDIATION-03 |
| Task class | **Investigation + decision preparation only. No implementation, no database mutation.** |
| Verdict | **`COMPLETE_WITH_OBSERVATIONS`** — topology explained from evidence; **foundation acceptance still not claimed** |

---

## 0. Document control, authority and how to read this report

### 0.1 Authority hierarchy applied

Per `AGENTS.md` §2 the following order was used, and every material claim below names the state it was
measured in:

1. actual running behaviour (process environment, published ports, container inspection);
2. actual database state (read-only catalogue queries — no data dumps);
3. current Git source (committed files at HEAD);
4. current migrations (`supabase/migrations/*.sql`, 104 files);
5. prior task reports **as regression targets only**, never as proof of current state.

### 0.2 Claim classification vocabulary (used on every material statement)

| Token | Meaning |
|---|---|
| **VERIFIED FACT** | Measured in this pass, read-only, with the command/query named |
| **HISTORICAL FACT** | Measured by a named prior report; **not** re-measured here |
| **INFERENCE** | A conclusion drawn from ≥2 verified facts; the facts are listed |
| **RECOMMENDATION** | Cline's proposed option; **not approved** until the PO selects it |
| **PO DECISION REQUIRED** | A business/policy choice that Cline must not make (AGENTS §62) |
| **UNKNOWN / NOT VERIFIED** | Not established; stated rather than assumed |

### 0.3 Probe provenance and secret hygiene

All inspection in this task was read-only: `git` status/log/`ls-remote`, file reads, `docker ps | inspect |
port` (non-secret metadata only), and `psql` **catalogue** queries (`pg_database`, `pg_namespace`,
`information_schema`, `pg_class`, `to_regclass`, `count(*)`). No row content was dumped, and no
credential, token, JWT, signed URL, service key or complete DSN is reproduced anywhere in this report
(DSN host + database name only; passwords and keys masked).

## 1. Executive summary (plain English)

### 1.1 Why there appear to be "three databases"

**VERIFIED FACT.** There is only **one PostgreSQL server** on this machine that serves CarbonTally:
the Docker container `supabase_db_carbon_ledger` (`postgres:17.6.1.147`, published on `127.0.0.1:54426`,
data volume `supabase_db_carbon_ledger`). Inside that one server there are **90 logical databases**
(`docker exec supabase_db_carbon_ledger psql -U postgres -Atc "select count(*) from pg_database where
not datistemplate"` → `90`), of which **83 are disposable `ct_*` verification clones** left over from
earlier verification tasks.

The "three database generations" of CLOSURE-02 / REMEDIATION-03 are therefore **three logical databases
inside one server, created by three different pieces of tooling for three different purposes** — not
three competing installations:

| Database | Who created it | What it is for | Served to the running app? |
|---|---|---|---|
| `carbontally_demo_local` | `tools/demo_lab/stack.py` (DEMO-T1 `fe36cdc` 2026-09-19; DEMO-T3 `ad46599`; canonicalised P12 Step-2 `a9a218f`/`54ee52c` 2026-09-24) | the **Demo Lab**: release schema built from all 104 `supabase/migrations/*.sql`, lab identities, disposable | **YES** |
| `postgres` | the Supabase CLI stack `project_id = "carbon_ledger"`, used by the **baseline installation** `/home/shomonrobie/carbon_tally` | the stack's own database — GoTrue auth, PostgREST, Storage, Realtime, `vault`, `supabase_functions`; also holds the **975-organisation investor-demo dataset** and the stack's **1,214 auth users** | not for business data; **is** the auth authority |
| `ct_local_93d5cdd` | `~/ct_local_env/seed_local_identities.py` + `start_latest.sh` (task *CT-STEP2-LOCAL-LATEST-RUN-WITHOUT-BASELINE-072*, 2026-09-19) | an **isolated "latest version" run** of *this* repository (backend `:8060`, frontend `:3100`, 67 migrations applied, 25 organisations, 658 `public.users`, **no working `auth` schema**) | **no** — abandoned local experiment |

### 1.2 Is the split intentional or accidental?

**VERIFIED FACT (intentional and documented by design).** The split is **deliberate** and written down in
three places:

* `tools/demo_lab/README.md` §1 — *"release backend (127.0.0.1:8070) … DATABASE_URL → PostgreSQL:
  carbontally_demo_local … SUPABASE_URL → lab gateway (127.0.0.1:54430) → /rest/v1 → carbontally_demo_local,
  /auth/v1 → local stack GoTrue (supabase_auth_carbon_ledger)"*; the developer's local Supabase stack
  *"is read for schema/keys and provides authentication; its databases — including the investor demo
  dataset — are never reseeded, truncated or altered."*
* `tools/demo_lab/stack.py` (module docstring, `ensure_database()`, `ensure_auth_bootstrap()`) — the lab
  creates its own database, clones the GoTrue `auth` **structure** (no rows), and delegates real
  authentication to the stack's GoTrue.
* `tools/demo_lab/provision.py::ensure_user_mirror()` — documents the seam in code: auth users are created
  through the lab gateway (i.e. in the **stack** database) and only `id`/`email` are mirrored into the lab
  database because the release schema keeps FKs to `auth.users`.

**INFERENCE.** The split exists because a single purpose drove DEMO-T1: *give the release a clean,
disposable, migration-built database with real role-bearing identities* **without touching the owner's
975-organisation investor dataset or its authentication users** (AGENTS §55). Keeping auth in the stack
was the cheapest way to obtain real GoTrue sessions (JWT signature, refresh, admin API) without seeding
auth inside the lab database.

**VERIFIED FACT (the accidental part).** Two things *are* accidental and do need a decision:

1. **`ct_local_93d5cdd` is residue, not architecture.** It is referenced today only by **untracked local
   files** (`backend/.env`, `frontend/.env.local`) and by `~/ct_local_env/*` outside the repository. No
   tracked code, test, CI job or service depends on it (grep of `backend/ frontend/ tools/ e2e/ qa_harness/
   .github/` → only `backend/.env:3`, which is git-ignored via `.gitignore:83`). Its own README
   (`~/ct_local_env/README.md`) records that the environment was *deliberately* pointed at an unroutable
   Supabase URL (`http://127.0.0.1:19999`), so its authenticated UI could never work.
2. **Port/config drift between this repository and the running stack.** The running stack is on the
   **5442x** family (`kong :54425`, `postgres :54426`), matching the *baseline* checkout's worktree
   `supabase/config.toml`. This repository's committed `supabase/config.toml` declares the **5432x**
   family (`api 54325`, `db 54326`, `studio 54323`) and is clean at HEAD
   (`git status --porcelain -- supabase/config.toml` → empty; `git log -- supabase/config.toml` →
   single commit `2d23fb8`). Meanwhile a **tracked test file**
   (`backend/tests/integration/conftest.py:40,58`) and the lab tooling (`tools/demo_lab/lab.py:36,52`)
   hard-code the **5442x** family. The repository therefore cannot, as committed, start the stack that its
   own tests and demo tooling expect. (HISTORICAL FACT corroborating: the same divergence is analysed in
   `docs/architecture/CT-PO-CARBONTALLY-RECON-03C-IMPORT-SUMMARY-AND-SUPABASE-CONFIG-DECISION-PACK-20260927.md`
   §7–§9 and `…-DATABASE-RECONCILIATION-LEDGER-20260927.md` PD-5.)

### 1.3 What the original architecture intended

**VERIFIED FACT (documented intent).** The intended local model is *one Supabase project per environment,
whose services all agree on one database*, with the application's business schema owned by the migration
chain:

* `supabase/config.toml` (`project_id = "carbon_ledger"`, `[db.migrations] enabled = true`) — a
  CLI-provisioned stack is the local platform; `docs/audit/cline/CARBONTALLY_LOCAL_SUPABASE_SETUP_AUDIT.md`
  documents the intended fresh-clone workflow (`supabase start` → `db reset` replays the chain).
* `docs/architecture/CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md` §1 — names the **canonical
  environment** and explicitly lists `postgres` (flagship), `carbontally_qa_phase8`, `carbontally_test`
  and production as **"NOT canonical"**.
* `docs/audit/costrict/CSTR-CARBONTALLY-ENVIRONMENT-RECON-001-20261003.md:38` — *"The canonical local
  environment is the Demo Lab (`carbontally_demo_local` on the developer's local Supabase stack + a
  release backend on `:8070`)"*. `[documented]`
* `AGENTS.md` §30 — public website, customer app, consultant workspace, PE workspace, internal operations
  and the admin control plane are **distinct surfaces**; nothing in the constitution requires *one logical
  database to hold every service's tables*.

**INFERENCE.** "One authoritative Supabase database" in the PO's statement means **one authoritative
database for the application's business data**, not "the same logical database must also hold GoTrue's
tables". That intent is **already satisfied**: the running application's business data lives in exactly one
database (`carbontally_demo_local`), and the migration chain owns its schema. What is *not* satisfied is
the reasonable expectation that the local platform be **reproducible from this repository and
unambiguous**.

### 1.4 Recommendation in one line

**RECOMMENDATION — Option C with a documented seam (§9):** keep **one stack, one canonical local
environment, one business database**; formally designate *the Demo Lab* (`carbontally_demo_local` + lab
gateway + supervised release backend on `:8070`) as the canonical local development/QA environment; keep
`postgres` as the protected authentication + investor-demo home (never the application DB); treat
`ct_local_93d5cdd` as a documented, preserved-then-retired experiment; and make the local environment
reproducible **from this repository** (single documented entry point + an explicit port-convention
decision).

Two questions cannot be settled by evidence alone and are therefore in the PO register (§11): **what
happens to the 975-organisation investor dataset** (preserve in place vs carry forward) and **whether the
owner requires a *single* database holding both business and auth data** (technically achievable, costlier
and riskier — Option B). Everything else in §11 is either already determined by approved architecture
(recommendation given; no real choice) or is a genuine product-policy choice.

---

## 2. CURRENT topology (measured 2026-10-09/10, read-only)

### 2.1 Diagram

```text
                         ONE PostgreSQL server (Docker)
        supabase_db_carbon_ledger  (postgres:17.6.1.147, volume supabase_db_carbon_ledger)
        127.0.0.1:54426  ── 90 logical databases ────────────────────────────────────────┐
                 │                                                                       │
   ┌─────────────┴────────────────────────────┐  ┌───────────────────────────────┐  ┌────┴────────────────┐
   │ database `postgres`   (39 MB)            │  │ database `carbontally_demo_   │  │ `ct_local_93d5cdd`  │
   │  schemas: auth, public, storage, realtime│  │ local` (27 MB)                │  │  (16 MB)            │
   │  _realtime, graphql(_public), vault,      │  │  schemas: auth, public,       │  │  schemas: auth(0    │
   │  supabase_functions, supabase_migrations  │  │  extensions, storage          │  │  relations), public,│
   │  116 public tables · ledger 46 rows       │  │  154 public tables · 154 RLS  │  │  extensions, storage│
   │  975 orgs · 7,049 factors · 1 bucket      │  │  14 orgs · 7,049 factors ·    │  │  135 tables         │
   │  auth.users 1,214 · public.users 1,352    │  │  2 buckets (documents,        │  │  25 orgs · 658      │
   │                                           │  │  report-artifacts)            │  │  public.users ·     │
   │  ◄── GoTrue, PostgREST, Storage, Realtime │  │  auth.users 22 (id/e-mail     │  │  0 factors · no     │
   │      of the RUNNING Supabase stack        │  │  mirror only) · no ledger     │  │  ledger · no        │
   └───────────────────────────────────────────┘  └───────────────────────────────┘  │  auth.users         │
                 ▲                                        ▲                           └─────────────────────┘
                 │ /auth/v1 (admin, sessions)             │ /rest/v1 + DATABASE_URL
                 │                                        │
   supabase_kong_carbon_ledger :54425            carbontally_demo_lab_gateway (nginx)  :54430
   supabase_rest/auth/storage/realtime/pg_meta   carbontally_demo_lab_postgrest ──────► carbontally_demo_local
   supabase_inbucket_carbon_ledger               carbontally_demo_lab_storage  ──────► carbontally_demo_local
                 ▲                                        ▲
                 │                                        │  SUPABASE_URL=http://127.0.0.1:54430
                 │                          release backend  uvicorn main:app :8070  (supervised)
                 │                          DATABASE_URL=…@127.0.0.1:54426/carbontally_demo_local
                 │                                        ▲
   baseline installation (NOT this repo)                 │  CRA dev server :3000
   /home/shomonrobie/carbon_tally  (branch main)   /home/shomonrobie/ct_93d5cdd  (branch p8-release-reconciled)
                 +  83 disposable `ct_*` databases (verification clones) in the same server
                 +  e2e stack `carbontally_e2e` (separate STOPPED cluster, port family 553xx, own volume)
```

### 2.2 Service → database matrix (VERIFIED FACT, from `docker inspect` env; secrets masked)

| Service (container) | Effective database target | Published port(s) | Notes |
|---|---|---|---|
| `carbontally_demo_lab_postgrest` | `supabase_db_carbon_ledger:5432` **`carbontally_demo_local`** (schema `public`, anon role `anon`) | none (reached via gateway) | created by `tools/demo_lab/stack.py` (`docker run`), no compose labels |
| `carbontally_demo_lab_storage` | `…:5432` **`carbontally_demo_local`** (`STORAGE_BACKEND=file`, volume `carbontally_demo_lab_storage` → `/mnt`) | none | lab-owned storage API (DEMO-T3) |
| `carbontally_demo_lab_gateway` | nginx only; upstreams = lab PostgREST + stack GoTrue; config generated at `~/ct_local_env/demo_lab/generated/nginx.conf` | **127.0.0.1:54430** | the single localhost-published lab port |
| `supabase_auth_carbon_ledger` (GoTrue) | `…:5432` **`postgres`** (as `supabase_auth_admin`) | via kong | the **only** authentication authority in the local topology |
| `supabase_rest_carbon_ledger` (PostgREST) | `…:5432` **`postgres`** (schemas `public,graphql_public`, role `authenticator`) | via kong | stack's own REST (not what the release app calls) |
| `supabase_storage_carbon_ledger` | `…:5432` **`postgres`** | via kong | stack storage (1 bucket `documents`) |
| `supabase_realtime_carbon_ledger` | `…:5432` **`postgres`** | via kong | Realtime |
| `supabase_db_carbon_ledger` | is the server; `POSTGRES_DB=postgres` | **0.0.0.0:54426 → 5432** | the single cluster |
| `supabase_kong_carbon_ledger` | — | **0.0.0.0:54425 → 8000** | stack API gateway |
| release backend (`uvicorn`, PID 1014820) | `DATABASE_URL=postgresql://postgres:***@127.0.0.1:54426/carbontally_demo_local` · `SUPABASE_URL=http://127.0.0.1:54430` | **127.0.0.1:8070** | supervised by `~/ct_local_env/demo_lab` (`supervisor.status.json`: state `running`) |

**Cross-database dependency check (VERIFIED FACT):** no foreign key, view or function crosses the two
databases. The only coupling is *identity*: GoTrue issues sessions against `postgres`, while the lab
database keeps a mirror row (`auth.users(id,email)`) so the release's in-database FKs to `auth.users`
resolve. `provision.py::ensure_user_mirror` is the single writer of that mirror.

---

## 3. INTENDED architecture and its evidence (Phase B)

### 3.1 The seven concepts, kept distinct (AGENTS §1)

| Concept | In this project | Today |
|---|---|---|
| Supabase **project** | a named platform instance: `carbon_ledger` (local), `carbontally_e2e` (local e2e), `pvwiojoyaqywtydzcpbg` (hosted demo/live) | three projects, one per environment family |
| PostgreSQL **server/cluster** | `supabase_db_carbon_ledger` container (plus the separate, **stopped** `carbontally_e2e` cluster) | 1 running |
| PostgreSQL **database** | a logical DB inside the cluster (`postgres`, `carbontally_demo_local`, `ct_local_93d5cdd`, `carbontally_test`, …) | 90 |
| PostgreSQL **schema** | `public`, `auth`, `storage`, `realtime`, `vault`, `graphql`, `supabase_migrations` | distributed (see §5.2) |
| Supabase **service** | GoTrue (auth), PostgREST, storage-api, realtime, kong, postgrest-meta, inbucket | running for `carbon_ledger` |
| Local **development environment** | one reproducible startup path → one app + one DB + one auth | **not yet single-sourced** (see §8.6) |
| Demo/seed **dataset** | investor demo (975 orgs) · Demo Lab identities (14 orgs) · task-072 identities (25 orgs) | three datasets in three DBs |

### 3.2 Answers to the Phase-B questions

1. **What does "one Supabase database" mean here?** **INFERENCE, evidenced:** one authoritative database
   *for the application's business schema*, provisioned by the migration chain, with the surrounding
   Supabase services (auth/storage/realtime) functioning. Evidence: AGENTS §5 (one Supabase PostgreSQL
   instance as part of *one* stack), `supabase/config.toml` (one project), P12 Step-2 naming one canonical
   environment — and no document anywhere authorising per-service databases.
2. **Does the architecture require one local PostgreSQL instance containing `auth`, `public`, `storage`?**
   **YES for a Supabase stack; not for the application database.** The *stack's* database must contain the
   standard schemas (it does: `postgres`), because GoTrue/Storage/Realtime are configured against it. The
   *application* database needs `public` (plus its FK target `auth.users`); it does not host GoTrue.
3. **Are separate PostgreSQL databases required by an approved decision?** **NO.** No approved document
   requires more than one database. The second and third databases arose from **tooling choices**
   (§4, §6), not from an approved architecture decision — **PO DECISION REQUIRED** to ratify or change that.
4. **Was the business/GoTrue split explicitly approved?** **Partially.** It is *documented as the design*
   of the Demo Lab (`tools/demo_lab/README.md`, `stack.py`, `provision.py`) and was accepted in review
   (`CSTR-CARBONTALLY-ENVIRONMENT-RECON-001` calls the Demo Lab the canonical local environment), but no
   PO record in the repository says *"the application database and the auth database shall be different
   databases"*. **PO DECISION REQUIRED** (PD-4.5 in §11).
5. **Intended dev / demo / test / deployment topology** (reconstructed from code + docs):

   | Environment | Platform | Database(s) | Evidence |
   |---|---|---|---|
   | local development/demo | stack `carbon_ledger` + Demo Lab containers, backend `:8070`, frontend `:3000` | business = `carbontally_demo_local`; auth = stack `postgres` | `tools/demo_lab/README.md` §1; `CSTR-…ENVIRONMENT-RECON-001:38` |
   | local integration tests | same stack (5442x ports), dedicated DB | `carbontally_test`, or a `ct_*` clone named per run | `backend/tests/integration/conftest.py:40,58` + F-046-1 guard |
   | local e2e | separate **stopped** cluster `carbontally_e2e` (553xx, own volume) | e2e stack database | `e2e/environment/supabase/config.toml`, `e2e/environment/scripts/{bootstrap,apply_migrations,reset}.sh` |
   | investor demo (local) | same stack | `postgres` (975 orgs / 1,214 auth users) | this task's census; `tools/seed_investor_demo/` (HISTORICAL FACT) |
   | hosted demo/live | hosted Supabase project `pvwiojoyaqywtydzcpbg` | its own `postgres` | CLOSURE-02 §1.5, RE-03 §4 (HISTORICAL FACT) |
   | production | host per `~/ct_local_env/README.md:9` | **UNKNOWN** (not contacted) | AGENTS §44/§70 |

6. **Separate projects vs databases?** `carbon_ledger` and `carbontally_e2e` are **separate Supabase
   projects** (separate clusters/volumes). `carbontally_demo_local`, `ct_local_93d5cdd`, `carbontally_test`,
   `postgres` and the 83 `ct_*` DBs are **databases inside the one running cluster**.
7. **Intended source of truth for migrations?** `supabase/migrations/*.sql` — **104 files, all tracked**
   (`git ls-files supabase/migrations | wc -l` = 104 = on-disk count). `stack.py` builds the lab schema
   from exactly that directory; `qa_harness/db/migrations.py` applies the same directory over a DSN; and
   `backend/tools/migration_drift.py` compares the ledger against it.
8. **How should a new developer reproduce the environment from source?** Today: **only partially.**
   `tools/demo_lab/run_demo_lab.sh` is the closest thing to a single entry point (stack → provision →
   verify, idempotent) — but it **requires an already-running `carbon_ledger` stack on the 5442x ports**
   and reads the stack's keys via `supabase status` (`lab.py::stack_env`). This repository's own
   `supabase/config.toml` would start that stack on **5432x**, so a fresh clone following
   `CARBONTALLY_LOCAL_SUPABASE_SETUP_AUDIT` does **not** produce the environment the tooling and tests
   expect. This is the single most concrete reproducibility defect found (§8.6, PD-4.6).

### 3.3 DIFFERENCES between current and intended (Phase B deliverable C)

| # | Dimension | Intended | Current | Impact |
|---|---|---|---|---|
| D1 | Application databases in the local stack | 1 canonical | 1 canonical + 1 residue (`ct_local_93d5cdd`) | ambiguity — two `.env` targets exist on disk |
| D2 | Port convention | one convention per project, consistent repo↔runtime | repo `5432x` vs runtime `5442x` (the runtime value belongs to the *baseline* checkout) | a fresh `supabase start` here produces a stack the tests/lab cannot use |
| D3 | `auth` availability for the app DB | app authenticates end-to-end | lab DB has only an id/e-mail mirror; real auth is in another database | acceptable by design, but absent from the PO record |
| D4 | Migration provenance | one ledger per environment | **no ledger in either modern local generation** | applied state cannot be machine-verified (§8.3) |
| D5 | Environment entry point | one documented command | ≥3 entry points (`tools/demo_lab/run_demo_lab.sh`; `~/ct_local_env/start_latest.sh`; a `ct_local_env/run_demo_lab.sh` referenced by `.gitignore` but **not** present in this repo) | onboarding hazard |
| D6 | Disposable residue | cleaned per task | 83 `ct_*` DBs · 24 volumes · ≥37 stopped containers | disk drift and "which DB is real?" confusion |
| D7 | Investor-dataset reachability | protected, explicitly off-limits | `postgres` is the *default DSN* of two tracked backup/restore tests | **safety risk** (§12, PD-4.2) |

### 3.4 Remaining architectural ambiguity (Phase B deliverable E)

* **A1 — UNKNOWN:** which of this repository's two candidate environments is intended to be primary going
  forward — the Demo Lab (`carbontally_demo_local`) or the task-072 isolated environment
  (`ct_local_93d5cdd`). Evidence points to the former (tracked tests, tooling, docs and the running
  process), but the repository's own `backend/.env` points to the latter. **PO DECISION REQUIRED** (PD-4.1).
* **A2 — UNKNOWN:** whether the 975-organisation investor dataset must remain *in place* in `postgres`
  indefinitely, or may be carried forward into the canonical database. AGENTS §§54–56 describe ~1,185
  identities as the demo population; today they exist only in `postgres`. **PO DECISION REQUIRED** (PD-4.2).
* **A3 — UNKNOWN:** whether production is the hosted project and in which migration state. Not contacted.
  HISTORICAL FACT: owner-evidence only; the last inspection attempt (2026-09-11) found the host NXDOMAIN
  (`CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md` §1/§9).

---

## 4. Historical database-topology timeline (Phase A)

| Date / commit | Change | Database(s) affected | Stated purpose | Evidence | Current dependency | Confidence |
|---|---|---|---|---|---|---|
| 2026-08-06 `2d23fb8` | `supabase/config.toml` committed: `project_id = "carbon_ledger"`, ports 5432x | — (config) | the local Supabase CLI project | `git log -- supabase/config.toml`; file content | yes — the CLI project that owns the stack | VERIFIED FACT |
| 2026-08-22 → 08-28 | investor-demo seeding | `postgres` (975 orgs, 1,214 auth users) | AGENTS §§54–56 demo population | `tools/seed_investor_demo/`; row timestamps (2026-09-27 census) | yes — GoTrue auth, stack services, backup tests | HIGH (historical) |
| 2026-08-26 | DEFRA factor import (generated SQL, 7,029 → 7,049 rows) | `postgres` | factor library | `output/sql/emission_factors.sql`; `import_batch_id IS NULL` | yes | HIGH (historical) |
| 2026-09-11 | port remap to **5442x** and `[db.migrations] enabled=false`, **as an uncommitted worktree edit in the baseline checkout** | the running stack's config | isolate the baseline's local run; stop `db reset` replaying migrations over a data-bearing DB | `CT-PO-CARBONTALLY-RECON-03C-…-DECISION-PACK-20260927.md` §7/§9/§10 | **yes** — the stack runs on 5442x today (`docker port`) | HIGH (historical, corroborated) |
| 2026-09-19 `fe36cdc` | **DEMO-T1** — `tools/demo_lab/{lab,stack,provision,lab_env}.py` + README | creates `carbontally_demo_local` in the running cluster; clones `auth` structure (no rows); delegates auth to the stack GoTrue | give the release a disposable, migration-built DB with role-bearing identities **without touching the investor dataset** | `git log --follow tools/demo_lab/lab.py`; `tools/demo_lab/README.md` §1 | **yes** — lab containers + running backend | VERIFIED FACT |
| 2026-09-19 (task 072) | isolated "latest version" run created | `ct_local_93d5cdd` + `backend/.env`, `frontend/.env.local`, `~/ct_local_env/*` | run *this* repo's latest code without touching the baseline installation | `~/ct_local_env/README.md`, `seed_local_identities.py`; `backend/.env:2-3` | only untracked local files | VERIFIED FACT |
| 2026-09-20 `ad46599` | **DEMO-T3** audit-grade lab (adds the lab storage container) | `carbontally_demo_local` + `carbontally_demo_lab_storage` | documents + artefacts in the lab | `git log --follow tools/demo_lab/stack.py` | yes | VERIFIED FACT |
| 2026-09-20 `05de2f3` | DEMO-T2-C guarded factor seeding | `carbontally_demo_local` (7,049 factors, 2 batches) | factors for the lab | commit + `seed_factors.py` | yes (lab fixtures) | VERIFIED FACT |
| 2026-09-24 `a9a218f`, `54ee52c` | **P12 Step-2** canonical demo lab: phased migration build, storage-substrate ordering, supervisor/systemd persistence | `carbontally_demo_local` | make the lab the canonical, reproducible demo environment | commits; `CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md` | yes | VERIFIED FACT |
| 2026-09-27 | database census: 78 logical DBs across 8 instances | all | discovery | `CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md` | — | HIGH (historical) |
| 2026-10-02 → 10-03 | FINAL-03 verification stacks created, later stopped | `ct_final01/02_*`, `ct_verify0x_*`, `ct_rel04x_*`, `ct_impl0x_*`, `ct_schema0x_*` containers + their DBs | per-task verification | `docker ps -a` (Exited 4–10 days ago) | none (stopped) | VERIFIED FACT |
| 2026-10-08/09 | **RE-03** applies the F-1 ACL migration to `carbontally_demo_local` | `carbontally_demo_local` | close B-21 on the established runtime DB | `CT-CARBONTALLY-FOUNDATION-REMEDIATION-03.md` §5/§9.2 | yes (current ACL state) | HIGH (prior task) |
| 2026-10-09/10 (this task) | read-only census re-measured: 90 DBs · 83 `ct_*` · 3 principals | all | evidence for this report | this report §2/§5 | — | VERIFIED FACT |

**What the history proves (INFERENCE).** Each database generation was introduced by a *named, purposeful
task*, and the purposes do not conflict: `postgres` = platform/auth/investor-demo home;
`carbontally_demo_local` = the disposable migration-built application environment; `ct_local_93d5cdd` = a
one-off isolation experiment for this checkout. The **accident** is not the existence of the databases but
(a) the residue left behind, (b) the missing migration ledger, and (c) the port/convention drift between
the two checkouts.

**No evidence was found** of a lost commit, a corrupted database, or an undocumented destructive event.
This is consistent with `CT-CARBONTALLY-FOUNDATION-VERIFICATION-03.md` §2.8, which already established that
the runtime drift is *expected* behaviour of `stack.py`, not an anomaly.

---

## 5. Complete inventory (Phase C)

### 5.1 The three principal databases (VERIFIED FACT — re-measured 2026-10-09/10)

| Measure | `carbontally_demo_local` | `postgres` | `ct_local_93d5cdd` |
|---|---:|---:|---:|
| Owner / encoding | `postgres` / UTF8 | `postgres` / UTF8 | `postgres` / UTF8 |
| Size | 27 MB | 39 MB | 16 MB |
| `public` tables (relkind `r`) | **154** | 116 | 135 |
| RLS enabled | 154 / 154 | 116 / 116 | 135 / 135 |
| Non-system schemas | `auth, extensions, public, storage` | `_realtime, auth, extensions, graphql, graphql_public, public, realtime, storage, supabase_functions, supabase_migrations, vault` | `auth, extensions, public, storage` |
| Migration ledger | **NONE** | **46 rows**, tip `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` | **NONE** |
| `auth.users` | 22 (id/e-mail **mirror** only) | **1,214** | *relation absent* — `auth` schema exists with **0 relations** |
| `public.users` | 23 | 1,352 | 658 |
| `organizations` | **14** (13 carry the `demo-lab-t1` marker) | **975** | **25** |
| `emission_factors` | 7,049 | 7,049 | **0** |
| Storage buckets | `documents`, `report-artifacts` (both private) | `documents` (private) | (1, per 2026-09-27 census) |
| Served to the running app | **YES** | no (auth only) | no |
| Reproducible from source | **YES** — `tools/demo_lab/*` rebuilds it from `supabase/migrations/*.sql` (104 files) + provision | **NO** — investor-demo seeds live in a *baseline-only* tool (`tools/seed_investor_demo/`, absent from this repo) + GoTrue state | **PARTIALLY** — 67 migrations applied and 25 orgs seeded by `~/ct_local_env/seed_local_identities.py` (outside the repo); the exact sequence is documented in `~/ct_local_env/README.md` |
| Unique data at risk if lost | lab fixtures only (rebuildable) | **975 orgs, 1,214 auth users, 685 storage objects, 100 snapshots, 245 customer factors** — *not rebuildable here* | 25 orgs / 658 users from an outside-repo seeder (low value, but not reproducible from this repo) |
| Classification confidence | **HIGH** | **HIGH** | **HIGH** |

Cross-check: RE-03 §4 and CLOSURE-02 §1.3 published the same table for the first two columns plus
`emission_factors 7,049 / 7,049 / 0` and `CT-03 request tables 4/4 · 0/4 · 0/4`; this pass reproduces every
figure it re-probed.

### 5.2 Schema distribution (VERIFIED FACT — `pg_namespace` + `information_schema`)

| Schema | `postgres` | `carbontally_demo_local` | `ct_local_93d5cdd` | Meaning |
|---|---|---|---|---|
| `public` | 116 tables | **154 tables** | 135 tables | application schema (migration-owned) |
| `auth` | GoTrue tables (1,214 users) | structure clone + 22 mirror rows | present, **0 relations** | authentication |
| `storage` | present (1 bucket) | present (2 buckets) | present | storage-api metadata |
| `realtime` / `_realtime` | present | absent | absent | Realtime (stack only) |
| `vault`, `supabase_functions`, `graphql`, `graphql_public` | present | absent | absent | stack-only platform schemas |
| `supabase_migrations` | present (46 rows) | **absent** | **absent** | Supabase CLI ledger |
| `extensions` | present | present | present | `uuid-ossp`, `pgcrypto`, `pg_trgm` |

### 5.3 Services (VERIFIED FACT — `docker ps` / `docker port` / container env)

* **Running Supabase stack `carbon_ledger` (8 containers):** `supabase_db_carbon_ledger` (**:54426**),
  `supabase_kong_carbon_ledger` (**:54425**), `supabase_auth_carbon_ledger`, `supabase_rest_carbon_ledger`,
  `supabase_storage_carbon_ledger`, `supabase_realtime_carbon_ledger`, `supabase_pg_meta_carbon_ledger`,
  `supabase_inbucket_carbon_ledger`. **All service containers point at `postgres`** (verified from their
  `GOTRUE_DB_DATABASE_URL`, `PGRST_DB_URI`, `DATABASE_URL`, `DB_NAME`). Project label
  `com.docker.compose.project = carbon_ledger`; no compose working-dir label (CLI-managed).
  `supabase_studio_carbon_ledger` appeared in the 2026-10-02 FINAL-03 inventory but is **not** in the
  current running set — **UNKNOWN** whether removed or merely stopped outside the captured list.
* **Running Demo Lab (3 containers):** `carbontally_demo_lab_postgrest`, `carbontally_demo_lab_storage`
  (volume `carbontally_demo_lab_storage` → `/mnt`), `carbontally_demo_lab_gateway` (nginx, **:54430**,
  generated config bind-mounted from `~/ct_local_env/demo_lab/generated/nginx.conf`). The two service
  containers point at **`carbontally_demo_local`**.
* **Application processes:** `uvicorn main:app --host 127.0.0.1 --port 8070` from `backend/.venv`
  (PID 1014820) and the CRA dev server on `:3000` (PIDs 1014827/1014923), both supervised by
  `~/ct_local_env/demo_lab` (`supervisor.status.json`: `state: running`, restart counts 0).
* **Present but stopped (≥37 containers):** the `carbontally_e2e` stack (own volume
  `supabase_db_carbontally_e2e`, own network), `ct_final01/02_*`, `ct_verify03–06_*`, `ct_rel04a/b/c_*`,
  `ct_impl01/02/02b_*`, `ct_schema01/02_*`, `ct_drill_pg`, `ct_drill2_pg`.
* **Unrelated:** `hindsight-carbontally`, `n8n-n8n-1`.

### 5.4 Volumes (VERIFIED FACT — 24 total, `docker volume ls`)

`supabase_db_carbon_ledger` · `supabase_db_carbontally_e2e` · `supabase_storage_carbon_ledger` ·
`supabase_storage_carbontally_e2e` · `supabase_edge_runtime_carbon_ledger` ·
`supabase_edge_runtime_carbontally_e2e` · `carbontally_demo_lab_storage` · `ct_final01_pgdata` ·
`ct_final02_storage_data` · `ct_impl01_pgdata` · `ct_impl02_pgdata` · `ct_impl02b_pgdata` ·
`ct_rel04a/b/c_pgdata` · `ct_schema01/02_pgdata` · `ct_verify03/04/04b/05/06_pgdata` ·
`hindsight-data` · `n8n_n8n_data`.

**INFERENCE.** 17 of the 24 volumes belong to stopped disposable verification stacks; none is referenced by
the running application or by tracked code. Their disposition is a hygiene decision (PD-4.7) — **not** a
prerequisite for foundation acceptance, and removing them without approval would violate AGENTS §55/§70.

### 5.5 Environment files (VERIFIED FACT — no secret values reproduced)

| File | Tracked? | Target | Notes |
|---|---|---|---|
| `tools/demo_lab/backend.env.example` | **yes** (the only tracked env file) | `carbontally_demo_local` @54426, gateway 54430 | committed example with `postgres:postgres` placeholders |
| `backend/.env` | **no** — ignored via `.gitignore:83` (`.env*`) | **`ct_local_93d5cdd`** @54426 · `PORT=8060` · `SUPABASE_URL=http://127.0.0.1:19999` (deliberately unroutable) | task-072 isolated env; also carries *duplicate* `REACT_APP_API_URL` keys (8060 then 8000) plus a hosted-project URL/token set (masked here) |
| `frontend/.env.local` | **no** — ignored via `frontend/.gitignore:16` | `REACT_APP_SUPABASE_URL=http://127.0.0.1:54430` · `REACT_APP_API_URL=http://localhost:8070` · `PORT=3100` | *does* point at the lab gateway, unlike `backend/.env` |
| `~/ct_local_env/demo_lab/backend.env` (outside repo, mode 0600) | n/a | `carbontally_demo_local` @54426 + gateway 54430 | generated by `tools/demo_lab/lab_env.py`; the **actual** environment of the running backend |
| `supabase/config.toml` | **yes** | CLI project `carbon_ledger`, **5432x** ports, `[db.migrations] enabled = true` | does **not** match the running stack (5442x) |
| `supabase/config copy.toml` | **yes** | not read by any tooling found | historical companion; only differences vs `config.toml` are `health_timeout`, `[auth] site_url` and `[studio] port` (RECON-03C §7) |
| `e2e/environment/supabase/config.toml` | **yes** | project `carbontally_e2e`, 5532x/5533x family | the complete port-remap variant (the pattern to copy if the 5442x family is ratified) |

### 5.6 Dependency matrix (VERIFIED FACT — repository-wide grep, docs excluded)

| Consumer | `carbontally_demo_local` | `postgres` | `ct_local_93d5cdd` |
|---|---|---|---|
| `tools/demo_lab/*` (19 modules) | **hard dependency** (`lab.py:32` `LAB_DB`; `stack.py`; `seed_factors.py:44`; `t3_scenarios.py:46`; `storage.py`) | indirect — auth through the stack GoTrue | none |
| Tracked backend tests | **4 files** target it live/by name: `tests/integration/test_i4_live_migration_and_persistence.py:43`, `test_p17l_capability_truth_surface_runtime.py:653`, `test_p17k_governed_capability_catalogue_runtime.py:177`, `tests/unit/data/test_i2_insight_rls_live.py:40` | `tests/integration/backup/test_exporter_local.py:37` and `test_restore_local.py:48` default their DSN to `…:54426/postgres` | none |
| Integration harness | `conftest.py:40` default `…:54426/carbontally_test`; the F-046-1 guard refuses targets named `qa/demo/investor/prod/live` **and** the exact names `postgres` / `supabase_db_carbon_ledger` | protected by that guard | none |
| CI `migration-drift.yml` | none | none (repo-only mode; optional DSN secret) | none |
| Running services | lab PostgREST + lab Storage + release backend | GoTrue, PostgREST, Storage, Realtime (stack) | **none** |
| Untracked local files | `~/ct_local_env/demo_lab/backend.env`, the three lab containers | — | `backend/.env`, `frontend/.env.local`, `~/ct_local_env/start_latest.sh` |

**Conclusion (INFERENCE).** `carbontally_demo_local` is the de-facto canonical **application** database: it
is the target of the running application, of all demo tooling and of four tracked tests. `postgres` is the
de-facto canonical **authentication/platform** database. `ct_local_93d5cdd` is residue with no tracked
dependency.

---

## 6. Why the three database generations exist (proven)

**VERIFIED FACT (each answer is sourced, not inferred from the database names):**

1. **`postgres`** — created by the Supabase CLI when the `carbon_ledger` project was initialised (config
   committed at `2d23fb8`, 2026-08-06; stack containers running since, per `docker ps` uptime and the
   2026-09-27 census's volume-creation date of 2026-08-23). It is the CLI's default database
   (`POSTGRES_DB=postgres`) and therefore the home of GoTrue, PostgREST, Storage, Realtime and the CLI
   ledger. The 975-organisation investor dataset and 1,214 auth users were seeded into it by
   `tools/seed_investor_demo/` between 2026-08-22 and 2026-08-28 (HISTORICAL FACT: row timestamps and
   `DEMO_IDENTITIES.md`; that tool exists only in the *baseline* checkout).
2. **`carbontally_demo_local`** — created by `tools/demo_lab/stack.py::ensure_database()`
   (`CREATE DATABASE "carbontally_demo_local"` executed against `postgres`), first shipped in DEMO-T1
   (`fe36cdc`, 2026-09-19). Purpose, verbatim from the code: *"creates a dedicated database inside the
   developer's local Supabase cluster (no other database there is touched)", "builds the release schema in
   it from supabase/migrations/*.sql (the authoritative source)", "clones the GoTrue auth schema structure
   (no rows)".*
3. **`ct_local_93d5cdd`** — created for task *CT-STEP2-LOCAL-LATEST-RUN-WITHOUT-BASELINE-072* (2026-09-19).
   `~/ct_local_env/README.md` states the purpose: run the **latest** checkout (`ct_93d5cdd`, branch
   `p8-release-reconciled`) alongside — and without modifying — the owner's **baseline** installation
   (`/home/shomonrobie/carbon_tally`, branch `main`, which owns `postgres`). The database name embeds the
   workspace directory name; 135 tables / 67 migrations were applied and six identities seeded by
   `~/ct_local_env/seed_local_identities.py`.

**Is each generation's continued existence documented?** Yes for all three — in `tools/demo_lab/README.md`
(2), `~/ct_local_env/README.md` (3), and the 2026-09-27 census/reconciliation reports (all three). **None is
undocumented, and none is the result of a corrupted or hijacked environment.**

**Does anything still depend on each?** See §5.6. In summary: (1) yes — the whole Supabase stack + the
investor dataset + two tracked backup tests; (2) yes — running application, all demo tooling, four tracked
tests; (3) no tracked dependency at all.

---

## 7. Why GoTrue uses `postgres` while the lab's PostgREST and Storage use `carbontally_demo_local`

**VERIFIED FACT (mechanism).** The Demo Lab deliberately borrows the **stack's** authentication service
instead of running its own GoTrue:

* `tools/demo_lab/lab.py` names the stack components (`STACK_DB_CONTAINER`, `STACK_AUTH_CONTAINER`,
  `STACK_STORAGE_CONTAINER`, `STACK_NETWORK`, `STACK_DB_PORT = 54426`) and reads the stack's keys with
  `supabase status -o env`.
* The lab gateway (`carbontally_demo_lab_gateway`, `:54430`) proxies `/auth/v1` → **stack GoTrue**, and
  `/rest/v1` → **lab PostgREST**. The release's `SUPABASE_URL` is the gateway, so one URL yields both.
* GoTrue is configured against the stack database (`GOTRUE_DB_DATABASE_URL=postgresql://supabase_auth_admin:***@supabase_db_carbon_ledger:5432/postgres`).
  Therefore every lab identity created through `/auth/v1/admin/users` (which is exactly what
  `provision.py::ensure_user` does) lands in **`postgres.auth.users`**.
* The release schema retains FKs to `auth.users`, so `provision.py::ensure_user_mirror()` copies only
  `id`/`email` into **`carbontally_demo_local.auth.users`** — *"no credentials, hashes or sessions"*.
* `tools/demo_lab/reset_demo_lab.sh` demonstrates the same seam from the other side: resetting the lab
  deletes only users whose e-mail is in the lab domain, and never touches the stack's other data.

**Is the arrangement technically supported?** Yes. It is a normal Supabase pattern (one GoTrue serving
multiple application databases' *identity*, with the application database keeping a local mirror of the
identities it references). **It is not a cross-database dependency in the database sense** — there is no
distributed transaction, no cross-database FK and no shared view.

**Does the application depend on it?** Yes, in one specific way: **token verification**. The release
validates sessions with `SUPABASE_JWT_SECRET`, which `lab.py::session_secret()` takes from the **stack**
(not from a lab-local secret). If the stack is rebuilt with a different JWT secret, previously issued lab
sessions stop verifying. That coupling is documented in `lab.py` and is the reason the lab must never be
separated from a stack whose secret is stable.

**Consequence for the "one database" question (INFERENCE).** Consolidating business *and* auth into one
database would require the lab to run its own GoTrue against the lab database (the cloned `auth` structure
already exists) and to stop mirroring. That is achievable (Option B, §9) but it changes the JWT-secret
source, the reset semantics (auth rows would then live in the disposable database) and would still leave
the *stack's* `postgres` untouched for the investor dataset.

---

## 8. Migration provenance and reproducibility (Phase D)

### 8.1 How each database actually received its schema and data

| Database | How the schema arrived | How the data arrived | Ledger written? |
|---|---|---|---|
| `postgres` | Supabase CLI/service provisioning + a **partial** migration history (46 ledger rows, tip `20260903010000…`); the remaining tables of the 116 came from direct SQL / restore / seed (not reconstructible from the ledger) | `tools/seed_investor_demo/` (baseline-only) + generated factor SQL + GoTrue admin activity | **yes, but incomplete** (46 of 104) |
| `carbontally_demo_local` | `tools/demo_lab/stack.py::ensure_database()`: `CREATE DATABASE`, extensions, `ALTER DEFAULT PRIVILEGES`, `ensure_auth_bootstrap()` (auth structure + enums + helpers copied from the stack), then **all 104 `supabase/migrations/*.sql` applied in sorted order via `psql` stdin** in two phases around the storage substrate (D32), with `ON_ERROR_STOP=0` and only non-"already exists" errors recorded | `provision.py` (identities/relationships), `seed_factors.py` (7,049 factors, 2 batches), `storage.py` + P12/T3 harnesses (documents/artefacts) | **NO** — the ledger schema does not exist and `stack.py` never creates it |
| `ct_local_93d5cdd` | 67 of the then-current migrations applied by the task-072 run (documented in `~/ct_local_env/README.md`: *"135 public tables, 67 migrations applied from supabase/migrations; the F-039-1-J uniqueness index and 218 RLS policies are present"*); **`auth` never provisioned** | `~/ct_local_env/seed_local_identities.py` (6 identities) + the 25-organisation/658-user dataset | **NO** |

### 8.2 Consequences

* **Both modern local generations are migration-replayed but unledgered**, so their applied state is **not
  machine-verifiable**. The CI drift gate (`migration-drift.yml` → `backend/tools/migration_drift.py`) can
  only read a ledger and therefore cannot confirm either environment.
* **`ON_ERROR_STOP=0` with "already exists" tolerated** makes the lab build *convergent*, not transactional:
  a migration that fails for a **new** reason is recorded in `summary["migrations_with_errors"]` and printed
  by `run_demo_lab.sh` rather than aborting the build.
* The **live demo** project *does* have a full ledger (104 rows, tip `20261105000000` — HISTORICAL FACT from
  CLOSURE-02 §1.5 / RE-03 §4). The hosted project is the only environment whose applied state is provable.

### 8.3 Mapping migration files to objects present (spot-verified, read-only)

* 104 migration files on disk == 104 tracked (`git ls-files supabase/migrations | wc -l`), newest
  `20261105000000_ct_consultant_model_03_request_tables_revoke_client_roles.sql`.
* `carbontally_demo_local`: 154 `public` tables — consistent with the full 104-file chain plus the storage
  substrate and auth bootstrap. REMEDIATION-03 §9.2 also records the F-1 ACL migration applied there on
  2026-10-08/09 **without** a ledger row.
* `ct_local_93d5cdd`: 135 tables — consistent with the documented *67*-migration boundary; the later
  objects (Insight persistence, P16R lifecycle, P17 families, CT-03 request tables) are absent
  (CT-READINESS-01 §7.3 probed exactly this: 14 outstanding migrations, 0 P17 objects).
* **Therefore: no object-level equivalence between the two modern generations may be assumed, and matching
  table counts would not prove equivalence even if they matched.**

### 8.4 Is there schema drift between the intended target and the committed migrations?

* `carbontally_demo_local` — **no unexplained drift found**: it is built from the committed set.
* `ct_local_93d5cdd` — **14+ migrations behind** the repository (HISTORICAL FACT, CT-READINESS-01 §7.4; the
  gap has widened since the repository grew from 89 to 104 files).
* `postgres` — **older schema generation** (116 tables; ledger tip `20260903010000`): the flagship is
  *behind* both modern generations and must never be treated as the application target.

### 8.5 Can the seed scripts reproduce the required demo data?

| Dataset | Reproducible from *this* repository? |
|---|---|
| Demo Lab identities (14 orgs, 23 users, role-bearing) | **YES** — `tools/demo_lab/provision.py` + `manifest.json` (idempotent, deterministic UUIDv5) |
| Demo Lab factors (7,049) | **YES** — `tools/demo_lab/seed_factors.py` (hard-guarded to the lab DB only) |
| Lab documents/artefacts | **YES (partially)** — P12/T3 harnesses + the tracked synthetic corpus |
| Investor demo (975 orgs / 1,214 auth users) | **NO** — the seeder exists only in the baseline checkout |
| task-072 dataset (25 orgs / 658 users) | **NO** — the seeder lives outside the repository (`~/ct_local_env`) |

### 8.6 How a fresh checkout should establish a consistent database state (RECOMMENDATION — plan only)

1. Start the stack from **this** repository (or explicitly point the tooling at a stack whose ports are
   declared), with `[db.migrations] enabled` **explicitly decided** (PD-4.6).
2. Run `tools/demo_lab/run_demo_lab.sh` — idempotent: database + auth bootstrap + 104 migrations in two
   phases + grants + containers + provision + verify.
3. Optionally `--factors` to load the DEFRA/SEAI library.
4. Confirm with `tools/demo_lab/verify.py` (13/13 actor contexts, 30/30 authorization probes, 18/18
   isolation rules — P12 Step-2 record).
5. **Do not** solve the missing ledger by inserting ledger rows: those rows would be *claimed*, not
   *observed*, and a partial ledger is more dangerous than none (see the Stage-3 rules in §10).

### 8.7 Proposed reconciliation approach (outline only — nothing executed)

See §10 Stages 1–8. The governing principle: **solve the ledger problem by recording the *derivation*,
not by fabricating ledger rows.** Concretely: document that the lab database is built by `stack.py` from
the committed migration set, write a machine-readable **build stamp** (ordered migration file names +
content hashes + build time + git SHA) into the lab database itself, and let the drift gate consume that
stamp as the local equivalent of a ledger. This is honest (it states what actually happened), cheap, and
does not weaken the live ledger.

---

## 9. Option comparison and recommended target topology (Phase E)

### 9.1 The options

**OPTION A — Keep the current split configuration.** (Stack `postgres` for auth/platform/investor demo;
`carbontally_demo_local` for the application; `ct_local_93d5cdd` left in place; `backend/.env` still
pointing at it; no ledger; 5432x/5442x mismatch unresolved.)

**OPTION B — One authoritative local database for everything of the application.** Run the lab's own GoTrue
against `carbontally_demo_local` (the cloned `auth` structure already exists), point every lab service and
the release at that one database, stop mirroring identities, and treat `postgres` purely as the untouched
investor-demo/baseline database.

**OPTION C (RECOMMENDED) — Ratify the two-database seam explicitly, designate one canonical local
environment, and remove the ambiguity.** Keep `carbontally_demo_local` as the single authoritative
**application** database (auth delegated to the stack GoTrue, mirror documented as a contract); keep
`postgres` as the protected **platform/auth/investor-demo** database; formally designate the Demo Lab as
*the* canonical local development/QA environment; retire `ct_local_93d5cdd` from the local default (after
preserving its unique content); make the repository self-describing (one entry point, declared ports, build
stamp instead of a fabricated ledger).

**OPTION D — Point everything at the stack's `postgres` database.** (Considered and rejected: it would place
the release's 154-table schema inside the database that holds the 975-organisation investor dataset and its
1,214 auth users, on the **older** schema generation; it contradicts AGENTS §55 and the whole reason
DEMO-T1 exists. Recorded for completeness only — **not recommended**.)

### 9.2 Comparison

| Criterion | A — as-is | **B — one DB for the app** | **C — ratify the seam (rec.)** | D — everything in `postgres` |
|---|---|---|---|---|
| Alignment with approved architecture | partial (works, but ambiguity + drift remain) | strong for "one DB", but invents a new auth topology not previously approved | **strong** — matches documented design and prior review acceptance | **contradicts** AGENTS §55 and the demo-lab design |
| Application compatibility | works today | requires GoTrue re-point + re-provision + JWT-secret change | **works today** (no code change) | requires the release's tables to be created inside the investor-demo DB |
| Authentication implications | unchanged | GoTrue must run against the lab DB; lab JWT secret becomes lab-local; sessions invalidated on rebuild | **unchanged**; JWT coupling documented | GoTrue already there, but auth users mix demo + lab identities |
| Migration implications | none | lab needs its own GoTrue migrations as well | none | would require migrating the flagship (older generation) |
| Demo-data implications | none | none | none | **high risk** to the 975-org dataset |
| Developer reproducibility | poor (two `.env` targets, no declared port authority) | better | **best achievable cheaply** (one entry point + declared ports + build stamp) | poor |
| Test isolation | `carbontally_test` + clones already isolated | unchanged | unchanged | **breaks** F-046-1 protection |
| Data-loss risk | low but unbounded (residue, no backups proven for `postgres`) | low | **low** — nothing destroyed; only documentation + additive changes | **unacceptable** |
| Implementation effort | none | medium–high (new GoTrue container + config + reset semantics + re-verification) | **low** (docs + small tooling/config changes) | very high |
| Rollback complexity | n/a | high (auth users move databases) | **low** (additive) | very high |
| Long-term maintenance | accrues drift | single DB to reason about | **one documented seam to respect** | dangerous |
| Evidence for | nothing changes | the PO's literal "one database" expectation | documented in 3 places + running in production-of-demo + 4 tracked tests depend on it | — |
| Evidence against | ambiguity, no ledger, port drift, residue (§3.3) | no document authorises it; duplicates GoTrue for no functional gain; adds failure modes | leaves two databases (but each with one explicit purpose) | AGENTS §55, RE-03 §4, census §1 |

### 9.3 Recommendation

**RECOMMENDATION: Option C.** Rationale:

1. It is what the system **already does**, is **documented**, and is what the tracked tests and tooling
   depend on — so it is the option with the least risk and the smallest correct change (AGENTS §4/§71).
2. It removes the two *real* defects (residue ambiguity; repo↔runtime port drift) **without** any database
   mutation or auth-topology change.
3. It keeps the investor dataset untouched, which AGENTS §55 makes non-negotiable.
4. It keeps Supabase services fully functional: **nothing about Option C disables `auth`, `storage` or
   `realtime`** — the stack keeps every standard schema in `postgres`, and the lab keeps `public` +
   the identity mirror.
5. Option B remains available if the PO wants a single database for *all* application concerns; §11 PD-4.5
   presents it as a selectable option with its consequences stated plainly.

**If the owner's expectation is specifically "business data and auth in one database", Option B is the
choice — and §10 Stage 4 covers the controlled way to get there.** Cline does **not** recommend B because
it buys no functional capability that C is missing, at material cost and risk.

---

## 10. Safe, staged reconciliation plan (PLAN ONLY — nothing executed in this task)

Global safeguards for **every** stage: no `git reset/clean/stash/rebase/force-push`; no database drop,
rename, truncate, re-seed or migration unless the stage says so **and** the PO has approved it; never touch
`postgres` data; never print secrets; every stage produces an evidence artefact.

### Stage 1 — Approve the target topology and identify the authority
* **Entry criteria:** this report committed; PO has selected an option (§9) and answered PD-4.1/PD-4.5.
* **Work:** record the decision (this file + a decision record); update `AGENTS.md` §§54–56 if the identity
  model changes (PD-B); name the canonical environment in the constitution.
* **Exit criteria:** a decision naming (a) the canonical application DB, (b) the canonical auth source,
  (c) the status of `ct_local_93d5cdd`, (d) the port convention.
* **Rollback:** none needed (documentation only). **Data preservation:** n/a.

### Stage 2 — Back up and verify a recovery path
* **Entry criteria:** Stage 1 complete.
* **Work:** `pg_dump` **each** of `postgres`, `carbontally_demo_local` and `ct_local_93d5cdd` to
  `<outside repo>/backups/<db>-<git-sha>-<utc>.dump`; record sizes and SHA-256; perform a **restore drill
  into disposable databases** (method already proven in RE-03 §5) and record the verification output.
  Storage volumes (`supabase_storage_carbon_ledger`, `carbontally_demo_lab_storage`) are either copied or
  explicitly declared out of scope with the PO's acknowledgement.
* **Exit criteria:** every principal database has a restore-verified dump stored *outside* the repository
  (never committed to Git) plus an evidence file.
* **Rollback:** the dumps *are* the rollback. **Data preservation:** `pg_dump` does not write to the source.

### Stage 3 — Reconcile schema/migration provenance without replaying migrations
* **Entry criteria:** Stage 2 complete.
* **Work:** (a) add a **build-stamp** mechanism to `tools/demo_lab/stack.py` (ordered migration list +
  content hashes + git SHA + build time, written into the lab DB at build time); (b) teach
  `backend/tools/migration_drift.py` to consume that stamp as the local ledger equivalent; (c) record
  `ct_local_93d5cdd`'s true applied boundary (CT-READINESS-01 §7.2 method) before any retirement decision.
* **Explicitly forbidden:** inserting rows into `supabase_migrations.schema_migrations`; replaying the chain
  against a populated database; "fixing" drift because table counts look right.
* **Exit criteria:** the lab database's build is **machine-evidenced** and the drift gate can pass/fail on
  real local evidence. **Rollback:** drop the stamp object only. **Data preservation:** additive only.

### Stage 4 — Prepare service configuration changes (only if Option B/D, or the port decision, was chosen)
* **Entry criteria:** Stage 1 chose B (or the port-convention change in PD-4.6).
* **Work:** a **new** lab GoTrue container configured against `carbontally_demo_local` (never re-pointing the
  stack's GoTrue, which would move the investor demo's auth); a new lab JWT secret; a documented
  re-provision of lab identities; a documented session-invalidation step. For the port convention: change
  **one** side only (`supabase/config.toml` **or** the tooling's declared ports) and update
  `backend/tests/integration/conftest.py`, `tools/demo_lab/lab.py`, runbooks and docs **in the same commit**.
* **Exit criteria:** the new configuration starts clean from a fresh checkout; no stack service is
  re-pointed. **Rollback:** stop the new container; revert the config commit. **Data preservation:** the
  stack database is never re-pointed.

### Stage 5 — Validate the platform against the target
* **Entry criteria:** Stage 3 (and 4 if applicable) complete.
* **Work:** against the lab — GoTrue login (real UI login at `:3000`), PostgREST reads via the gateway,
  Storage upload/download, Realtime subscribe, RLS enforcement (positive **and** negative), stamp/ledger
  check. **Exit criteria:** all six verified with evidence; failures documented as findings, not worked
  around. **Rollback:** Stage-2 dumps if any validation mutates state destructively (it should not).

### Stage 6 — Run integration, security-negative and end-to-end tests
* **Entry criteria:** Stage 5 green; PD-D environment authorised.
* **Work:** the integration suite against a disposable clone (F-046-1 in force); behavioural RLS negatives
  across customer/consultant/PE/internal boundaries; **one full lifecycle** (upload → extraction → mapping →
  validation → calculation → evidence → review → approval → reporting) with a **seeded customer factor**
  (closes the B-09/B-13 evidence gaps); re-run the count/spend corpus measurement after the PD-C decision.
* **Exit criteria:** PASS/DENY evidence recorded with git SHA, database name, actor and timestamps.
* **Rollback:** disposable databases only.

### Stage 7 — Confirm reproducibility from source
* **Entry criteria:** Stage 6 complete.
* **Work:** from a fresh clone (or a clean worktree), run the single documented entry point and reach a
  verified environment; record commands, duration and output; return the environment under test to its
  prior process state. **Exit criteria:** a second operator can reproduce the environment from the
  repository alone. **Data preservation:** never against `postgres`.

### Stage 8 — Disposition of obsolete generations and resources (only after Stages 1–7 + explicit approval)
* **Entry criteria:** Stage 7 complete **and** PO approval naming each object.
* **Work:** `ct_local_93d5cdd`, the ≥37 stopped `ct_*` containers, the 17 disposable volumes and the
  `carbontally_e2e` / `ct_p3_verify_pg` remnants are each either **retained with a stated purpose** or
  **retired** after (a) a verified dump exists and (b) the removal is listed explicitly.
* **Exit criteria:** the inventory honestly reflects what remains and why. **Rollback:** only from Stage-2
  dumps — therefore no retirement precedes a verified dump. **Data preservation:** AGENTS §55 — the
  investor-demo dataset is never in scope for removal.

---

## 11. Consolidated PO decision register (Phase F)

### 11.0 Register conventions and an ID-collision warning

* **Exact definitions were retrieved, not invented.** PD-A…PD-F come from
  `CT-CARBONTALLY-FOUNDATION-BASELINE-01.md` §15.2; PD-4, PD-C, PD-D from
  `CT-CARBONTALLY-FOUNDATION-CLOSURE-02.md` §7.1 and `…-REMEDIATION-03.md` §7.3; PD-G/PD-H/PD-I were
  created by REMEDIATION-03 §6/§7.3.
* **⚠️ ID collision (documentation-integrity finding, F-A4-01).** A *different* register —
  `CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-LEDGER-20260927.md` §7 — uses **PD-1…PD-10** for database
  reconciliation, where **its PD-4 means "whether a local Supabase-Auth-bearing database is required"** and
  its **PD-5** is the port/project convention. The foundation register's **PD-4** means "which local
  database and `.env` are authoritative". To prevent a future agent implementing the wrong decision, this
  report treats the reconciliation register as **sub-questions of PD-4** (below) and recommends the PO
  **retire PD-1…PD-10 or re-label them PD-R1…PD-R10** at ratification.
* **None of the decisions below is authorised for implementation by this report.** Selecting an option is
  the authorisation; until then nothing is implemented (AGENTS §62).

### 11.1 PD-4 — "Which local database and which `.env` are authoritative for local development/QA, and what is the disposition of the other database generations?"

**1. Why it is required.** Two conflicting local configurations exist on disk, both modern generations lack
a migration ledger, and a third generation survives with no tracked dependency. Without a decision, local
evidence can be collected against the wrong database and reported as "the application works".

**2. Original requirement / PO decision.** AGENTS §5 (one Supabase PostgreSQL instance per stack), §55
(never reset the investor demo), §65/§66/§67 (contract, database-change policy, RLS); the PO's stated
expectation of **one authoritative Supabase database for the application**.

**3. Current implementation + evidence.** §2 (running backend → `carbontally_demo_local` + lab gateway
`:54430`), §5 (inventory), §6 (origins), §8 (provenance). All measured this pass.

**4. Already resolved — must not be reopened.** (a) The running application's business database is
`carbontally_demo_local` — verified from the *process environment* of PID 1014820, not from documentation.
(b) `postgres` holds the 975-organisation investor dataset and the stack's auth; it is **not** the
application database. (c) `ct_local_93d5cdd` has no tracked dependency.

**5. Still unresolved.** Seven sub-questions, each with its own options and recommendation below.

#### PD-4.1 Canonical local application database
* **Options.** **(A)** Ratify `carbontally_demo_local` (Demo Lab) as canonical. **(B)** Ratify a
  to-be-rebuilt database. **(C)** Ratify `ct_local_93d5cdd`.
* **Recommendation: A.** Evidence: it is the only DB built from the **full** committed migration set, it is
  what the running application uses, four tracked tests name it, and all demo tooling targets it.
* **What changes:** (A) documentation + a decision record only. (B) rebuild + re-provision + re-verify
  (expensive, no benefit). (C) would require completing 14+ missing migrations and provisioning `auth` —
  strictly worse than A.
* **Security/data-integrity:** A changes nothing. **Maintenance:** A removes ambiguity at zero cost.
* **Tests after selection:** `tools/demo_lab/verify.py`; the four DB-named tests.

#### PD-4.2 Disposition of the 975-organisation investor dataset (`postgres`)
* **Options.** **(A) Preserve in place, never migrate** — `postgres` stays exactly as it is; the demo
  population remains available for population-scale isolation testing by explicitly pointing a tool at it.
  **(B) Carry forward** into a modern-schema database (new DB or into the canonical one), leaving `postgres`
  as-is afterwards. **(C) Retire** the dataset.
* **Recommendation: A**, with **B only if** the PO decides population-scale QA must run against the modern
  schema. **C is not recommended** (AGENTS §55; the dataset is the only local population of its kind and its
  seeder lives outside this repository, so it is not reproducible here).
* **Plain-English consequence:** A = "leave the big demo alone; it stays useful read-only". B = "we would
  spend effort copying 975 organisations into the new schema, and persona QA would then observe a different
  database than today". C = "we permanently lose the only large local demo population".
* **Blocks:** A/B/C all block nothing technically, but **A must be recorded before any consolidation**.
  **Tests after selection:** a read-only count/hash census of the preserved dataset (structure + counts).

#### PD-4.3 Authorised evidence environment (interface with PD-D)
* This sub-question is **PD-D** (§11.5). It is listed here only to state the interface: the Demo Lab is the
  natural candidate for the authorised evidence environment because it already has role-bearing identities
  and a migration-built schema; the investor `postgres` database is the natural candidate for
  **population-scale read-only** isolation testing. Both remain unauthorised until PD-D is answered.

#### PD-4.4 Port / project convention (`5432x` vs `5442x`, and `[db.migrations]`)
* **Options.** **(A)** Adopt **5442x** as this repository's local convention (edit `supabase/config.toml` in
  one reviewable commit; tooling and tests already expect it). **(B)** Keep **5432x** as committed and
  parameterise the *tooling* (`lab.py` port constants → environment variables) plus
  `backend/tests/integration/conftest.py`, so both families can coexist. **(C)** Do nothing.
* **Recommendation: B.** It is the only option that makes a *fresh clone* work without editing committed
  configuration that is shared with the baseline installation (both checkouts declare
  `project_id = carbon_ledger` — starting both with the same ports is itself a collision risk, RECON-03C
  §9.4). **(A)** is acceptable but changes a committed file to match a *local* quirk. **(C)** guarantees the
  drift persists.
* **Plain English:** today the repository says "our stack uses ports 5432x" while the machine's stack uses
  5442x; anyone following the docs gets a stack the tests cannot find. B says "let the tooling take the ports
  as configuration instead of hard-coding them".
* **Security/ops:** low risk either way; **maintenance** strongly favours B.

#### PD-4.5 Business data and authentication in one database, or two?
* **Options.** **(A) Two databases (current):** business in `carbontally_demo_local`, auth in `postgres`
  via the stack GoTrue + identity mirror. **(B) One database:** the lab runs its own GoTrue against
  `carbontally_demo_local`; mirror removed; JWT secret becomes lab-local.
* **Recommendation: A.** It is documented, running, tested, and adds no failure modes; B buys no capability
  that A lacks (the app already authenticates end-to-end) while invalidating existing lab sessions and
  duplicating the auth service.
* **Choose B only if** the PO's requirement is literally "one database holds everything for the
  application" (e.g. for backup/restore simplicity). Then Stage 4 of §10 is the route.
* **Security:** both preserve RLS and identity isolation; B must re-verify that the lab GoTrue's admin API is
  not exposed beyond localhost. **Data-integrity:** B must re-provision identities idempotently.

#### PD-4.6 Single documented environment entry point (reproducibility)
* **Options.** **(A)** Document `tools/demo_lab/run_demo_lab.sh` as *the* local entry point and delete/neutralise
  the task-072 references. **(B)** Add a new wrapper script. **(C)** Leave as-is.
* **Recommendation: A** (with PD-4.4(B)), because the entry point already exists, is idempotent, guarded
  (lab-DB-name guard in `seed_factors.py`/`t3_scenarios.py`) and verified by `verify.py`. **C** leaves three
  competing instructions.
* **Blocks:** this is the concrete deliverable behind AGENTS §82/§83 ("a new developer reproduces the
  environment from source").

#### PD-4.7 Disposition of residue: `ct_local_93d5cdd`, 83 `ct_*` databases, 17 disposable volumes, ~37 stopped containers
* **Options.** **(A) Preserve all with a documented purpose; retire nothing now.** **(B) Preserve evidence
  (dumps) for `ct_local_93d5cdd` and the P17-bearing clones, retire the rest on a schedule.** **(C) Retire
  everything disposable immediately.**
* **Recommendation: B, executed only after Stage 2 dumps exist** — but **not before foundation acceptance**,
  and never by an unsupervised sweep (AGENTS §55/§70; note also that the **only** local copies of the P17
  accounting generation live in 15 `ct_*` clones — HISTORICAL FACT, census §1/§4).
* **Plain English:** A = "keep hoarding, but write down what each database is". B = "keep a backup, then
  clean up the leftovers in a reviewed step". C = "delete evidence we cannot recreate".

#### PD-4 metadata (fields 12–17 for all sub-questions)

| Field | Answer |
|---|---|
| **12. What changes under each option** | Sub-questions are independent; each row above states its own consequence. Selecting PD-4.1(A)/PD-4.2(A)/PD-4.5(A) changes **documentation only**. PD-4.4(B) and PD-4.6(A) change tooling/config (one reviewable PR). PD-4.5(B) changes auth topology (substantial). PD-4.7(B) changes infrastructure (after dumps). |
| **13. Tests needed after selection** | `tools/demo_lab/verify.py` (13/13 · 30/30 · 18/18) · the four DB-named tests · `migration-drift` repo-only run · a fresh-clone reproduction run (Stage 7) · restore-drill verification (Stage 2) · if PD-4.5(B): auth login + session-verification tests |
| **14. Blocks foundation acceptance?** | **YES** — "the local environment is not yet reproducible from source" is one of the four listed acceptance blockers (RE-03 §12.2 item 4). PD-4.1/4.4/4.5/4.6 must be answered to close it. PD-4.2/4.7 do **not** block acceptance. |
| **15. Blocks CrewAI V4?** | **YES for PD-4.1/4.5/4.6** (V4 will need an unambiguous local data platform); no for PD-4.2/4.7. |
| **16. Authorises implementation / DB mutation?** | **Only when answered.** PD-4.1(A) authorises documentation. PD-4.4(B)/PD-4.6(A) authorise config/tooling edits. PD-4.5(B) authorises a new container + re-provision (Stage 4). PD-4.7(B) authorises removals **only after** Stage-2 dumps. Nothing authorises touching `postgres` data. |
| **17. Follow-up task** | `CT-CARBONTALLY-ARCHITECTURE-RECONCILIATION-05` — execute Stages 1–3 (decision record, dumps + restore drill, build stamp) **read-only against all data**; Stages 4–8 only if their option was selected. |

### 11.2 PD-A — Ratify or withdraw `CT-UX-MP-SUB-003` (the Manual Processing UI/UX spec)

| Field | Value |
|---|---|
| **1. Exact title / source** | "Ratify or withdraw `CT-UX-MP-SUB-003` (the Manual Processing UI/UX spec that `S3` F-1 records as implemented-but-not-authorised), or direct re-scoping of the delivered UI" — `CT-CARBONTALLY-FOUNDATION-BASELINE-01.md` §15.2 |
| **2. Why required** | Acceptance authority for the delivered MP UI does not exist (S3 F-1, HIGH, still open). The UI exists and is used; nobody has ratified the spec it implements. |
| **3. Original requirement** | AGENTS §39 (D19 workbench is frozen; changes require PO review); §63 (do not reopen frozen UX casually). |
| **4. Current implementation + evidence** | HISTORICAL FACT: `S3 F-1` recorded the spec as self-declaring *NOT YET AUTHORIZED* while the UI shipped (BASELINE-01 §815). Not re-measured this pass; no MP-UI code was inspected. |
| **5. Already resolved** | The MP screens exist, are routed, and `20261030000000_manual_processing_routing.sql` is committed within the 104-file chain. |
| **6. Still unresolved** | Whether the delivered UI **is** the approved D19 workbench, or must be re-scoped. |
| **7. Options** | **(A) Ratify as delivered** (retro-authorise; cheapest). **(B) Ratify with amendments** (specific deviations listed, then ordinary implementation work). **(C) Withdraw + re-scope** (new UX spec → implementation wave). |
| **8. Recommendation** | **B** if any deviation from D19/§38–39 exists, else **A**. The delivered UI is already in the release line; withdrawing it would discard working, tested UI for no verified functional gain. An independent UX review (OHD) is the cheapest way to produce the deviation list. |
| **9. Implications** | UX: A/B preserve what users see; C invalidates existing screenshots/QA. Ops: A/B need no engineering. Security: none. |
| **10. Evidence for recommendation** | BASELINE-01 §815; AGENTS §39 (D19 frozen); RE-03 §0 (no MP-UI change authorised or made). |
| **11. What changes per option** | A: decision record only. B: decision + scoped UX fix list. C: new ratification cycle + UI rebuild. |
| **12. Tests after selection** | A/B: browser verification of the MP flow at the accepted viewports (AGENTS §49) + accessibility pass (§50). C: full acceptance of the new spec. |
| **13. Blocks foundation acceptance?** | **YES** — an acceptance-authority gap (BASELINE-01 §15.2). |
| **14. Blocks CrewAI V4?** | No. |
| **15. Authorises implementation / DB mutation?** | A/B authorise **no** database mutation; B authorises frontend fixes only after the deviation list is agreed. |
| **16. Follow-up task** | `CT-UX-MP-AUTHORITY-01` (deviation list → PO ratification → optional fixes). |

### 11.3 PD-B — Which demo/identity model is authoritative

| Field | Value |
|---|---|
| **1. Exact title / source** | "Which demo/identity model is authoritative: the §54 '1,185 identities / investor demo' model or the `tools/demo_lab/manifest.json` model" — BASELINE-01 §15.2; restated as B-11/B-12 in RE-03 §7.1 |
| **2. Why required** | Determines what population-scale isolation testing is even possible locally, and what "the demo" means in every future QA claim. |
| **3. Original requirement** | AGENTS §§54–56 (investor demo data: ~1,185 identities, `tools/seed_investor_demo/DEMO_IDENTITIES.md`). |
| **4. Current implementation + evidence** | **VERIFIED FACT (this pass):** the ~1,185-identity model is real and lives in **`postgres`** — 975 organisations, 1,214 `auth.users`, 1,352 `public.users`. The §54 manifest tool (`tools/seed_investor_demo/`) is **absent from this repository** (baseline-only). The Demo Lab model is `tools/demo_lab/manifest.json`: 14 orgs / 23 users, all present in `carbontally_demo_local`. |
| **5. Already resolved** | That both populations exist and where they live (§5.1); that the running application serves the **lab** population, not the investor one. |
| **6. Still unresolved** | Which model future QA/acceptance must cite, and whether AGENTS §§54–56 should be amended. |
| **7. Options** | **(A) Investor model is authoritative** for population/isolation QA (read-only against `postgres`). **(B) Lab model is authoritative**; AGENTS §§54–56 amended. **(C) Both, scoped by purpose** — lab for workflow/persona acceptance, investor for population/isolation. |
| **8. Recommendation** | **C, recorded explicitly in AGENTS** — it matches how the system operates (the app serves the lab; the investor dataset is the only large population) and needs no data movement. If one answer is required, **(B)** is the honest one for *application* acceptance because only the lab is migration-complete. |
| **9. Implications** | QA/acceptance semantics; documentation. No runtime change under B/C beyond wording. |
| **10. Evidence for recommendation** | §5.1 census; §5.6 dependency matrix; RE-03 §7.1 B-11/B-12; AGENTS §56 (population-scale checks need the large dataset — present only in `postgres`). |
| **11. What changes per option** | A: QA must be authorised against `postgres` (PD-D); AGENTS unchanged. B: AGENTS §§54–56 amended. C: both statements added, each scoped. |
| **12. Tests after selection** | A/C: read-only population/isolation census against `postgres` (counts by org/role + cross-tenant denial sampling). B: lab `verify.py` isolation rules + a documented rationale for excluding population-scale testing. |
| **13. Blocks foundation acceptance?** | **YES, indirectly** — it decides which environment the remaining acceptance evidence must come from (interacts with PD-D). |
| **14. Blocks CrewAI V4?** | No. |
| **15. Authorises implementation / DB mutation?** | **No DB mutation under any option.** A authorises read-only QA access to `postgres` (subject to PD-D); B/C authorise documentation only. |
| **16. Follow-up task** | Fold into the PD-D decision record (`CT-CARBONTALLY-EVIDENCE-ENVIRONMENT-01`). |

### 11.4 PD-C — Count/spend invoice lines: drop, surface, or add a spend/count factor path

| Field | Value |
|---|---|
| **1. Exact title / source** | "Count/spend invoice lines: drop (current), surface as unresolved, or add a spend/count factor path" — RE-03 §7.3 ("B-03b — PO DECISION REQUIRED"); precursor in BASELINE-01 §15.2 |
| **2. Why required** | **111 rows across 38 corpus documents vanish before mapping** (RE-03 §2.2). Silent under-coverage of printed activity is a reporting-integrity issue (AGENTS §21). |
| **3. Original requirement** | AGENTS §21 (do not pretend a document was processed), §22 (never silently choose; explain empty mapping), §23 (central unit normalisation), §25 (auditable calculation). Ratified contract: "unknown units rejected unless in the unit vocabulary" (P12-IMPL-01 §13). |
| **4. Current implementation + evidence** | VERIFIED (RE-03 §2.1/§2.2): `canonical_unit("units"/"each"/"GBP")` → `None`, and `None` ⇒ **row dropped** (`engines/invoice_extraction.py:268`; drop at lines 320-322). B-03a (`mi` → `miles`) is **fixed**; the 111 `units`-token rows / 38 documents remain dropped; behaviour pinned by `test_count_token_units_is_not_a_physical_unit`. |
| **5. Already resolved** | The `mi` spelling gap (fixed: 36 rows / 12 files recovered, 0 lost). Physical-unit semantics (a currency/count is never a physical unit). The factor set is physical-unit based. |
| **6. Still unresolved** | Whether count/spend lines stay invisible, are surfaced as unresolved items, or gain a spend/count factor path. |
| **7. Options** | **(A) Keep dropping (fail-closed)** — current ratified behaviour, pinned by test. **(B) Surface as unresolved line items** preserving `unit_raw`/quantity with an honest "no physical factor / spend path" reason (AGENTS §22). **(C) Add a spend/count factor path** (new factor semantics for currency/count activity). |
| **8. Recommendation** | **B** — the smallest change that satisfies §21/§22 without inventing a factor kind; optional **C** later if spend-based activity is in commercial scope. **A** is defensible only if the PO formally accepts the coverage gap in writing, because the documents are otherwise silently under-read. |
| **9. Implications** | Data-integrity/reporting: B makes the gap visible and countable. C removes the gap but needs new factor semantics, unit handling and provenance. UX: B adds a row class to mapping/review. Maintenance: both add surface area; B far less. |
| **10. Evidence for recommendation** | RE-03 §2.2 measured table (147 → 111 dropped rows; 38 files; 37 of them ground-truth at 3 lines); AGENTS §21/§22/§25; P12-IMPL-01 §13. |
| **11. What changes per option** | A: nothing (decision record). B: parser emits unresolved rows; mapping/UI must show the reason (backend + frontend + tests). C: B plus a new factor kind, model change and migration. |
| **12. Tests after selection** | B: unit tests for the unresolved-row contract; re-run of the corpus sweep proving 0 silently dropped and 111 surfaced; negative test that currency rows never map to a physical factor. C: as B plus spend-path calculation tests preserving `factor_kind` provenance. |
| **13. Blocks foundation acceptance?** | **YES** — RE-03 R-1 (P2, PO-dependent); it changes what data survives extraction, which is acceptance-relevant. |
| **14. Blocks CrewAI V4?** | No, though V4's extraction stage would inherit the gap. |
| **15. Authorises implementation / DB mutation?** | Selecting B/C authorises **code** changes (parser + UI + tests). Only C requires a database migration (new factor kind/columns). |
| **16. Follow-up task** | `CT-EXTRACTION-COVERAGE-01` (implement the selected option with corpus evidence). |

### 11.5 PD-D — Authorised evidence environment and identities (lifecycle / factor-precedence / RLS-negative)

| Field | Value |
|---|---|
| **1. Exact title / source** | "Authorised evidence environment + identities for lifecycle, factor-precedence and RLS-negative verification" — RE-03 §7.3; BASELINE-01 §15.2 ("authorised evidence environment for workflow/RLS/end-to-end verification, and whether credentials may be issued for it") |
| **2. Why required** | Without it every workflow claim remains **UNVERIFIED**: B-09 (approval/QC lifecycle) and B-13 (customer-factor precedence) are **0 rows** in both the lab and live (RE-03 §7.1). |
| **3. Original requirement** | AGENTS §51–§53 (independent QA evidence), §72 (test the workflow, not isolated functions), §45 (security negative tests), §73 (never claim acceptance without evidence). |
| **4. Current implementation + evidence** | The lab has 14 orgs / 23 **role-bearing** users and 7,049 factors, but **0** `approval_requests`, `approval_decisions`, `processing_queue`, `qc_checks`, `customer_review_log`, `ai_content_history`, `customer_factors` (HISTORICAL FACT, RE-03 §7.1 — consistent with the 2026-09-27 census). `postgres` holds the population on the older schema. |
| **5. Already resolved** | The environment *candidates* and their contents (§2, §5); that `carbontally_test` / `ct_*` clones provide isolated destructive-test targets behind an in-code guard (F-046-1). |
| **6. Still unresolved** | Which environment is **authorised** to receive seeded lifecycle data and customer factors, who may hold its credentials, and whether the investor demo may be used **read-only** for population checks. |
| **7. Options** | **(A) Demo Lab (lab DB) as the authorised write-capable evidence environment**, with a disposable clone per destructive run; investor `postgres` **read-only** for population checks. **(B) A dedicated new evidence database** (migration-built, seeded for lifecycle/factor tests). **(C) Live demo project** — rejected: data-thin (2 orgs / 2 auth users) and writing to it risks the hosted demo. |
| **8. Recommendation** | **A.** It exists, is migration-complete, has role-bearing identities, is disposable by design (`reset_demo_lab.sh`) and its seeding is idempotent (`provision.py`, `seed_factors.py`). B is the fallback if the PO wants the lab reserved for manual demos. |
| **9. Implications** | Security: credentials issued per role, never committed (AGENTS §54/§70); destructive integration must run against a **clone**, not the lab (the harness guard refuses `demo`-named targets). Data-integrity: lifecycle seeds must be idempotent and separable. |
| **10. Evidence for recommendation** | `tools/demo_lab/README.md` §2 (idempotent commands), `verify.py` results (13/13 · 30/30 · 18/18), RE-03 §7.1 (B-09/B-13 zeros), P12 Step-2 record. |
| **11. What changes per option** | A: documentation + per-role credentials + a seeded lifecycle/factor run. B: build + seed + verify a new environment. C: not recommended. |
| **12. Tests after selection** | The full AGENTS §45 negative matrix (Customer A→B, Consultant A→B, Consultant A→B's client, PE A→B, PE→customer document, Viewer write, Member admin, Staff→Staff Admin, Staff Admin→System-Admin-only, Customer→internal, PE→internal); the review/approval/QC lifecycle end-to-end; customer-factor precedence with `factor_kind`/`customer_factor_id` provenance. |
| **13. Blocks foundation acceptance?** | **YES — the primary blocker** (RE-03 R-5, "P1 for acceptance"). |
| **14. Blocks CrewAI V4?** | **YES** (and the task forbids starting V4 regardless). |
| **15. Authorises implementation / DB mutation?** | Answering PD-D authorises **seeding and test execution** in the named environment (and, if B, creating a new database). It does **not** authorise any change to `postgres` data or to the live project. |
| **16. Follow-up task** | `CT-CARBONTALLY-EVIDENCE-ENVIRONMENT-01` → then `CT-CARBONTALLY-RLS-NEGATIVE-01` and `CT-CARBONTALLY-LIFECYCLE-E2E-01`. |

### 11.6 PD-E — Commit or hold the consultant-organisation-parity change set

| Field | Value |
|---|---|
| **1. Exact title / source** | "Whether the uncommitted consultant-organisation-parity change set (B-06) is to be committed as the next release baseline, or held" — BASELINE-01 §15.2; reframed as a commit-hygiene/release-baseline decision by `CT-CARBONTALLY-FOUNDATION-VERIFICATION-03.md` §2.8 |
| **2. Why required** | Originally it blocked the red migration-order tests. Verification-03 established the drift mechanism was **expected** `stack.py` behaviour, so the remaining question is only whether the consultant-parity change set **is the next release baseline**. |
| **3. Original requirement** | AGENTS §10–§11 (consultant operating model ratified and first-class), §71 (change discipline), §79 (legacy handling). |
| **4. Current implementation + evidence** | **Largely discharged (HISTORICAL FACT):** the change set is **committed and published** — `20261101000000_ct_mp_sub_003_consultant_coverage.sql`, `20261102000000_ct_consultant_model_02_capability_admission.sql`, `20261103000000_ct_consultant_model_03_client_access_and_mode.sql`, `20261104000000_ct_consultant_client_identity_04.sql`, `20261105000000_…_request_tables_revoke_client_roles.sql` are all in the 104-file chain reachable from HEAD; B-18 (migration-order pins) is **RESOLVED** (all green in the full suite, RE-03 §7.1). |
| **5. Already resolved** | The change set is committed and published; the pins are green; the drift was explained. |
| **6. Still unresolved** | A **formal PO statement** that this change set *is* the next release baseline (ratification of release status, not commit status). |
| **7. Options** | **(A) Ratify as the release baseline** (decision record; no code change). **(B) Hold** and mark the migrations provisional (requires documenting that committed migrations are not the baseline — not recommended). |
| **8. Recommendation** | **A.** The migrations are in the line, in the live demo ledger and in the lab; holding them now recreates the ambiguity PD-E exists to remove. |
| **9. Implications** | Release/versioning semantics only; no runtime, security or data change. |
| **10. Evidence for recommendation** | RE-03 §7.1 (B-18 RESOLVED; consultant migrations in the chain); CLOSURE-02 §7.1 ("PD-E … largely discharged: the change set is now committed and published"); `git ls-files supabase/migrations` = 104 including all five consultant migrations. |
| **11. What changes per option** | A: a one-line ratification record. B: documentation churn plus a risk that future agents treat committed migrations as non-authoritative. |
| **12. Tests after selection** | None new; re-run the migration-order pins and the consultant-parity verification once on the ratified baseline. |
| **13. Blocks foundation acceptance?** | **No longer directly** — a ratification formality; leaving it open keeps a documentation contradiction alive. |
| **14. Blocks CrewAI V4?** | No. |
| **15. Authorises implementation / DB mutation?** | **No** — pure ratification. |
| **16. Follow-up task** | Fold into the Stage-1 decision record of §10. |

### 11.7 PD-F — Retention (N3) durations and enforcement scope

| Field | Value |
|---|---|
| **1. Exact title / source** | "Retention (N3) durations and enforcement scope remain configuration-only and unratified numerically (AGENTS §42)" — BASELINE-01 §15.2 |
| **2. Why required** | Blocks any retention claim; the system can be *configured* but no duration is approved, so no customer-facing or contractual statement about retention can be made. |
| **3. Original requirement** | AGENTS §42 — retention is configurable, server-side, must persist and be enforced, must not weaken auditability/evidence/regulatory traceability, and durations must **not** be invented. |
| **4. Current implementation + evidence** | HISTORICAL FACT (BASELINE-01 §15.2): configuration-only, numerically unratified. **UNKNOWN — NOT VERIFIED in this pass:** current `system_settings` retention values were not read (a data read beyond this task's scope). |
| **5. Already resolved** | That retention must be server-side, configurable and must not weaken audit/evidence/regulatory traceability. |
| **6. Still unresolved** | The numeric durations per domain (documents, extraction data, evidence, reports, messages, audit logs) and the enforcement scope (per-org override? per-plan?). |
| **7. Options** | **(A) PO sets explicit durations per domain** (starting point: the longest statutorily required period per domain, audit logs ≥ the reporting horizon). **(B) PO approves a documented default policy** with per-org override. **(C) Leave unratified** — then no retention claim may be made anywhere in the product. |
| **8. Recommendation** | **A**, delivered via **B**. Retention is a compliance decision requiring owner/legal input (AGENTS §42/§62); Cline must not invent numbers. |
| **9. Implications** | Compliance/contractual: durations appear in customer terms. Data-integrity: retention must never delete evidence referenced by a calculation snapshot or an approved report. Ops: enforcement must be observable (what was deleted, when, under which policy). |
| **10. Evidence for recommendation** | AGENTS §42; BASELINE-01 §15.2; RE-03 §7.3 (PD-F unchanged). |
| **11. What changes per option** | A/B: policy document + configuration values + enforcement verification. C: a standing prohibition on retention claims. |
| **12. Tests after selection** | Server-side enforcement tests (a record past its window is removed; a record in legal hold or referenced by evidence is **not**); a settings-persistence test; an audit-log test proving the retention action itself is logged. |
| **13. Blocks foundation acceptance?** | **No** — it blocks retention *claims*, not the foundation. |
| **14. Blocks CrewAI V4?** | No. |
| **15. Authorises implementation / DB mutation?** | Selecting A/B authorises configuration and, if enforcement is missing, **implementation**. It does **not** authorise deleting existing data without a separate explicit instruction. |
| **16. Follow-up task** | `CT-RETENTION-N3-01` (policy → configuration → enforcement tests). |

### 11.8 PD-G — Messaging-send permission for RETAINED / READ_ONLY consultant relationships

| Field | Value |
|---|---|
| **1. Exact title / source** | "Messaging-send ceiling for `RETAINED`/`READ_ONLY` client profiles" — RE-03 §7.3 (from F-04) |
| **2. Why required** | A `RETAINED`/`READ_ONLY` client can still **send** messages although PA-2/PA-3 says the relationship retains no messaging-send (RE-03 §7.1 F-04, CONFIRMED-CURRENT). |
| **3. Original requirement** | AGENTS §28 (messaging boundaries by role/org/client/entity; N1 frozen principles; the UI is not the security boundary). |
| **4. Current implementation + evidence** | `backend/api/v3_messaging.py::_authorize_org_actor` admits (a) any member of the same org, (b) consultants with an active grant, (c) internal staff with `can_manage_staff`; a grep for `RETAINED` / `require_client_operation` in that module yields **no match** (HISTORICAL FACT, RE-03 §7.1). |
| **5. Already resolved** | The `require_client_operation` ceiling mechanism exists and is already applied elsewhere (e.g. supplier/master-data writes). |
| **6. Still unresolved** | Whether retained/read-only relationships may send at all — a product-policy question about what "retained" means commercially. |
| **7. Options** | **(A) Keep as-is** (retained clients can send). **(B) Deny send for `RETAINED`/`READ_ONLY` profiles**, surfacing a clear reason (and still allowing read). **(C) Deny send but allow a restricted "request re-engagement" message type.** |
| **8. Recommendation** | **B** if the PA-2/PA-3 intent is that a retained relationship is read-only; **C** if the PO wants a graceful re-engagement path. Both reuse the existing ceiling mechanism, so the implementation cost is small. |
| **9. Implications** | Security/UX: B/C change what a user can do; the UI must explain it (AGENTS §26/§48), not merely disable a button. Ops: a message-send denial must be logged as an authorization event, not an error. |
| **10. Evidence for recommendation** | RE-03 §7.1 F-04 (guard gap measured in source); AGENTS §28 (N1 boundaries); the existence of `require_client_operation` as the established mechanism. |
| **11. What changes per option** | A: nothing. B: one guard in the messaging module + a reason surfaced in the API + tests. C: B plus one extra allowed message type. |
| **12. Tests after selection** | ALLOW/DENY pairs per profile (`RETAINED`, `READ_ONLY`, `ACTIVE`) × actor (client, consultant, internal); a test asserting the denial reason is user-presentable. |
| **13. Blocks foundation acceptance?** | **YES, as a P2 policy gap** (RE-03 R-2) — it decides *who may act*. |
| **14. Blocks CrewAI V4?** | No. |
| **15. Authorises implementation / DB mutation?** | Selecting B/C authorises backend + frontend changes and tests. **No** database migration is required (profiles already exist). |
| **16. Follow-up task** | `CT-MESSAGING-CEILING-01`. |

### 11.9 PD-H — Who may create/update and who may approve a customer-specific factor

| Field | Value |
|---|---|
| **1. Exact title / source** | "Who may create/update a customer factor (Member propose-then-Owner-approve, or Owner/Admin only)" — RE-03 §7.3 (from F-05) |
| **2. Why required** | The authoring boundary for customer-specific factors is undecided; `approve`/`deactivate` are already admin-gated, so the unanswered half is **create/update** (RE-03 §7.1 F-05, CONFIRMED-CURRENT). |
| **3. Original requirement** | **Ratified PO decision (AGENTS §16): the Customer Owner MAY self-approve a custom factor.** Members may not approve unless separately authorised; Viewers never. AGENTS §15: approved customer factors take precedence over generic factors. |
| **4. Current implementation + evidence** | HISTORICAL FACT: `customer_factors` = **0** in both the lab and live (RE-03 §7.1 B-13), so precedence has no live evidence. `approve`/`deactivate` are already admin-gated; create/update is the open half. |
| **5. Already resolved — must not be reopened** | **Owner self-approval is allowed** (AGENTS §16). Deterministic matching/normalisation through the central unit module was verified in RE-03 §2.1. |
| **6. Still unresolved** | Whether a Customer **Member** may create/update a customer factor (with Owner approval required), or whether create/update is Owner/Admin-only. |
| **7. Options** | **(A) Owner/Admin only** — simplest; matches the approve gate; Members propose nothing. **(B) Member propose → Owner approve** — preserves two-person control and matches the §16 framing of approval as a separate step. **(C) Any member may create *and* approve** — contradicts AGENTS §16 ⇒ not recommended. |
| **8. Recommendation** | **B** if client organisations commonly rely on non-owner staff to prepare factors; otherwise **A**. Both are consistent with AGENTS §16; the choice is operational, not technical. |
| **9. Implications** | Security: the write path must be enforced **server-side** (a hidden button is not authorization — AGENTS §7/§44). Data-integrity: a factor used in a calculation snapshot must never be silently replaced (§15), so update must respect the approval lifecycle. UX: under (B), the UI must show "proposed, awaiting approval" honestly (§26). |
| **10. Evidence for recommendation** | AGENTS §15/§16 (ratified Owner self-approval); RE-03 §7.1 F-05; the existing admin gating on `approve`/`deactivate`. |
| **11. What changes per option** | A: add a `require_client_operation("create_customer_factor")`-style ceiling for Member roles. B: A plus a proposal state + Owner approval transition. |
| **12. Tests after selection** | ALLOW/DENY by role (Owner, Admin, Member, Viewer, consultant without grant) for create/update/approve/deactivate; a precedence test proving an **approved** customer factor wins over a generic factor with `factor_kind`/`customer_factor_id` preserved; a test that an unapproved factor is never used in a calculation. |
| **13. Blocks foundation acceptance?** | **YES, as a P2 policy gap** (RE-03 R-3) — it decides *who may act*. |
| **14. Blocks CrewAI V4?** | No. |
| **15. Authorises implementation / DB mutation?** | Selecting A/B authorises backend + frontend changes; **B** may require a lifecycle/state migration (a proposal state), which must then follow AGENTS §66. |
| **16. Follow-up task** | `CT-CUSTOMER-FACTOR-BOUNDARY-01` (with the B-13 precedence evidence run). |

### 11.10 PD-I — Rate limiting, `POST /api/test-upload`, and `GET /api/reports/report_status`

| Field | Value |
|---|---|
| **1. Exact title / source** | "Rate limiting for the unauthenticated write/email endpoints (`waitlist`, `password-reset` ×2); production exposure of `POST /api/test-upload`; authenticate-or-annotate `GET /api/reports/report_status`" — RE-03 §7.3 (from I-06) |
| **2. Why required** | I-06 found **17 operations with no declared authentication dependency** (including 3 mutations) and **no rate limiting observed** on the unauthenticated write/email endpoints (RE-03 §6). These are abuse and deliverability risks, not authentication defects. |
| **3. Original requirement** | AGENTS §44 (security foundations), §46 (no raw technical errors), §78 (never log secrets). I-06 was re-enumerated with **proof of full contract coverage** (RE-03 §6). |
| **4. Current implementation + evidence** | HISTORICAL FACT (RE-03 §6): the 17-operation count reproduced exactly; classification = 6 framework/liveness, 4 intentionally-public business routes (glossary ×3, waitlist), 3 deliberately-public with trimmed payload/token authorization (analytics bootstrap, password-reset ×2), 2 liveness/readiness, 1 static service-metadata route, 1 non-persisting diagnostic. `POST /api/test-upload` does **not** persist but reads the body; `GET /api/reports/report_status` returns static metadata. **No confirmed authentication defect ⇒ no authentication was added.** |
| **5. Already resolved** | The enumeration and classification; that `password-reset/confirm` is token-gated by design; that `test-upload` is non-persisting. |
| **6. Still unresolved** | (a) whether to rate-limit `waitlist` and the two password-reset endpoints, and at what thresholds; (b) whether `POST /api/test-upload` may exist in production at all; (c) whether `report_status` should be authenticated or explicitly annotated public. |
| **7. Options** | (a) **(A) per-IP + per-target rate limits**; **(B) CAPTCHA/challenge on public forms**; **(C) no limit** (current). (b) **(A) remove/disable in production**; **(B) keep but authenticate**; **(C) keep as-is**. (c) **(A) authenticate**; **(B) annotate as deliberately public**; **(C) leave as-is**. |
| **8. Recommendation** | (a) **A** — standard, cheapest mitigation; no UX change for legitimate users. (b) **A** — a diagnostic upload route has no production purpose. (c) **B** unless it exposes anything non-public, in which case **A**. |
| **9. Implications** | Security/abuse: A reduces spam, mail-bombing and enumeration. Deliverability: unthrottled email endpoints can damage the sending domain's reputation. Ops: limits must be observable (429 with `Retry-After`). Privacy: limits must not log e-mail addresses (§78). |
| **10. Evidence for recommendation** | RE-03 §6 (I-06 re-enumeration; no rate limiting observed); AGENTS §44/§78. |
| **11. What changes per option** | (a) A: middleware/limits + config + tests. (b) A: route gating. (c) A/B: a dependency or a documentation annotation. |
| **12. Tests after selection** | Threshold tests (N allowed, N+1 → 429 with a safe body); a test that the limit is per-IP/per-target and cannot be bypassed by header spoofing; a test that `test-upload` is absent/denied in the production configuration; a contract test recording `report_status` as deliberately public (if B). |
| **13. Blocks foundation acceptance?** | **YES, as a P2 security-hardening item** (RE-03 R-4). It is not an authentication defect, so it does not block *correctness* acceptance, but it must be answered before any public-launch claim. |
| **14. Blocks CrewAI V4?** | No. |
| **15. Authorises implementation / DB mutation?** | Any option authorises **code** changes only. **No** migration is required unless the chosen limiter persists counters (a separate decision). |
| **16. Follow-up task** | `CT-ABUSE-LIMITS-01` (re-check the I-06 route list against current source before changing anything). |

### 11.11 Decision summary (selectable form for the owner)

| Decision | Recommended option | Plain-English effect |
|---|---|---|
| **PD-4.1** canonical app DB | **A — `carbontally_demo_local`** | "Keep using the database the app already uses; write it down as the official one." |
| **PD-4.2** investor dataset | **A — preserve in place** | "Leave the 975-organisation demo exactly as it is; never migrate it." |
| **PD-4.4** port convention | **B — make ports configurable** | "Stop hard-coding ports so a fresh clone works." |
| **PD-4.5** one DB or two? | **A — two (business + auth)** | "Business data and login data stay in two databases; the app already works this way." |
| **PD-4.6** entry point | **A — document `run_demo_lab.sh`** | "One command starts the local environment." |
| **PD-4.7** residue | **B — back up, then retire later** | "Keep a copy of the leftovers; clean up in a reviewed step." |
| **PD-A** MP UI spec | **B (or A)** | "Approve the existing Manual Processing screens, with a short fix list if any." |
| **PD-B** demo identity model | **C (both, scoped)** | "Small lab for workflows; big demo for population checks." |
| **PD-C** count/spend lines | **B — surface as unresolved** | "Stop quietly dropping £/count-only invoice lines; show them as 'no factor yet'." |
| **PD-D** evidence environment | **A — the Demo Lab (+ read-only investor demo)** | "Authorise the lab for seeded tests so we can finally prove the workflows." |
| **PD-E** consultant change set | **A — ratify as baseline** | "Confirm the consultant work already in the code is official." |
| **PD-F** retention durations | **A via B** | "You (with legal input) pick the periods; we enforce them server-side." |
| **PD-G** retained-client messaging | **B (or C)** | "A retained client can read but not send messages." |
| **PD-H** customer-factor authoring | **A or B** | "Only owners/admins can create factors (or: members propose, owners approve)." |
| **PD-I** abuse limits | **(a) A, (b) A, (c) B** | "Rate-limit the public forms; remove the test-upload route in production; label the status route public." |

**Total:** **15 selectable rows** above — PD-4 is presented as one umbrella decision with **six** selectable
sub-questions (PD-4.1, 4.2, 4.4, 4.5, 4.6, 4.7; PD-4.3 is the PD-D interface, not a separate choice) plus
**PD-A … PD-I (9)**. Every row has a recommended default, so the owner may approve the whole table in one
action — with two genuine business choices flagged: **PD-4.5** (one database or two) and **PD-H** (who may
author factors).

---

## 12. Foundation acceptance blockers (Phase G)

Classification: **UNVERIFIED** = no evidence exists; **PARTIAL** = some evidence; **COMPLETE** = evidenced.

| # | Item | Current evidence | Genuinely unverified | Already complete | What remains | Requires | Smallest safe next action |
|---|---|---|---|---|---|---|---|
| 1 | Behavioural RLS-negative verification | §45 properties asserted in the model; `tools/demo_lab/verify.py` reports 30/30 authorization probes (HISTORICAL) | All cross-tenant / cross-role **negative** cases against a live authenticated server | Auth model, guards, RLS policies (355 in the lab), probe harness | Run the negative matrix, recording PASS/DENY per case | **PD-D** + test execution | Authorise the lab, extend the existing probe harness with the §45 matrix |
| 2 | Integration tests | Suite exists (`backend/tests/integration/`), harness guarded by F-046-1 | Whether it passes today against a fresh clone of the lab schema | Harness, default target (`carbontally_test`), guard | One controlled run against a disposable clone | Test execution | Clone the lab DB → run the suite with `INTEGRATION_DATABASE_URL` at the clone → drop the clone |
| 3 | E2E / browser tests | Demo Lab browser harnesses exist (`verify_*_browser.py`); P12/T3 records (HISTORICAL) | A current run on the running stack | Harness + canonical origin rules (DR-003: `:3000`) | One recorded run | Test execution | Run one harness (e.g. `verify_consultant_nav_browser.py`) and record output |
| 4 | Customer isolation | Model + guards exist; probes recorded historically | Current negative evidence (Customer A → B) | Org membership resolution + RLS | Part of blocker 1 | Same as 1 | Include in the negative matrix |
| 5 | Consultant/client role boundaries | Consultant model ratified and implemented; migrations committed | Current negative evidence (Consultant A → B; Consultant A → B's client) | Client-access ceiling helpers | Part of blocker 1 | Same as 1 | Include in the negative matrix |
| 6 | Customer-factor precedence | Implemented in code (`data/emission_factors.py`, `automatic_processing.py`) | **Any live evidence** — `customer_factors = 0` in lab and live (B-13) | Matching/normalisation logic; PD-H will fix the authoring boundary | Seed an approved customer factor and prove it wins | PD-H + PD-D + test execution | Seed one approved factor for a lab test org; assert `customer_factor_id` provenance in a calculation |
| 7 | Review/approval/QC lifecycle | Code + routes exist; lifecycle tables exist | **Any live evidence** — 0 rows across all six lifecycle tables (B-09) | Tables, routes, capability flags | One end-to-end lifecycle run with a real document | PD-D + test execution | Seed a document → drive the lifecycle through the API → record the state transitions |
| 8 | End-to-end emissions calculation and output | 7,049 factors in the lab; parser/calculator unit-tested (5,365 passing, HISTORICAL) | A real document producing a real number with full provenance + an output artefact | Extraction→calculation code paths; snapshot schema | One document end-to-end including evidence and report | PD-D + test execution | Reuse the canonical PDF corpus: upload → … → report, capturing kg CO₂e and snapshot lineage |

| 9 | Count/spend invoice-row handling | **Measured**: 111 rows / 38 documents dropped (RE-03 §2.2) | The PO's decision | The measurement (this is the decision input) | **PD-C** selection, then implementation | PO decision | Answer PD-C |
| 10 | Rate limiting / unauthenticated endpoint exposure | **Measured**: 17 operations classified; no rate limiting observed (RE-03 §6) | The PO/ops policy | The full enumeration + classification | **PD-I** selection, then implementation | PO/ops decision | Answer PD-I |
| 11 | Local database reproducibility | §8.6: a fresh clone does **not** reproduce the tooling's expected environment | A verified fresh-clone reproduction | `run_demo_lab.sh` + `verify.py` (idempotent, guarded) | PD-4.4 + PD-4.6, then Stage-7 verification | PO decision + implementation | Answer PD-4.4/PD-4.6 |
| 12 | Migration provenance / drift | §8: no ledger in either modern generation; live ledger 104 rows | A local applied-state verification mechanism | The drift-gate code + repo-only mode | A build-stamp mechanism (Stage 3) | Implementation (small) | Stage 3 |
| 13 | I-08 audit-coverage measurement | RE-03 §7.1 R-8: not measured | Whether audited operations actually write audit records | Audit instrumentation visible in the dependency graph (INVENTORY-02 §2.6) | A coverage measurement run | Implementation | Count audit-table rows (read-only) during blocker 7's lifecycle run |
| 14 | B-19/B-20 repository hygiene | **VERIFIED CURRENT**: `frontend/App_.js` still tracked-modified, 41,982 bytes, unimported; root debris (`8`, `=`, `nohup.out`, `backend/nohup.out`, `.costrict/`, `.p18_audit_tmp/`, `Research/`, `costrict-p3-ov-01-…txt`, the `.docx#` lock) all present and untouched by this task | Whether `App_.js` may be deleted | Nothing further to measure | A PO sign-off to delete (or a note that it is kept deliberately) | PO sign-off + implementation | Request the sign-off; never `git add -A` |
| 15 | *(found this task)* **Second-checkout dependency** | The lab tooling and the integration harness depend on a stack started by the **baseline** checkout (5442x); this repo cannot start that stack as committed | Which checkout owns the local stack going forward | The tooling's expectations (documented in code) | PD-4.4 + PD-4.6 | PO decision + implementation | Same as blocker 11 |
| 16 | *(found this task)* **Tracked backup tests default to `postgres`** | `tests/integration/backup/test_{exporter,restore}_local.py` default their DSN to `…:54426/postgres` (the investor-demo DB) | Whether they have ever run with that default | The F-046-1 guard protects the *other* harness | Change the default (or add a refusal guard) so a local drill cannot target the demo DB | Implementation + test update | Change the default to a disposable clone name and add the same name-guard `conftest.py` uses |

| 17 | *(found this task)* **Tracked Supabase CLI temp artefacts** | `git grep` during the secret scan shows committed `backend/supabase/.temp/{linked-project.json,pooler-url,project-ref}` | Whether a committed pooler/connection artefact is intended to be in the repository | Templates/`config` conventions exist | Decide whether these artefacts should be tracked, and confirm they contain no credential material (they were **not** opened in this task; nothing was printed) | PO/implementation (hygiene) | A read-only review of those three files by a task authorised to read them, then either ignore them or document why they are tracked |

**Explicitly not blockers:** repeating the full unit suites (RE-03 measured 5,365/0/8 backend and 630/630 Jest;
repeating them without a code change would burn ~11 minutes for no new information); live-vs-local ACL parity
(closed as B-21); the `ct_*` residue (PD-4.7, hygiene only).

---

## 13. Recommended task sequence

| Order | Task | Type | Unblocks | Depends on |
|---|---|---|---|---|
| 1 | **Answer the decision register** (§11) — at minimum PD-D, PD-4.1/4.4/4.6 | PO decision | Everything below | this report |
| 2 | `CT-CARBONTALLY-ARCHITECTURE-RECONCILIATION-05` — Stages 1–3 of §10 (decision record, dumps + restore drill, build stamp) | Implementation (read-only w.r.t. data) | Reproducibility + drift evidence | 1 |
| 3 | PD-4.4/4.6 implementation (ports configurable; single entry point documented) | Implementation | Fresh-clone reproducibility (blocker 11/15) | 2 |
| 4 | `CT-CARBONTALLY-EVIDENCE-ENVIRONMENT-01` — establish the authorised environment + credentials | Environment | All behavioural testing | 1 |
| 5 | `CT-CARBONTALLY-RLS-NEGATIVE-01` — the §45 negative matrix (blockers 1, 4, 5) | Test execution | Security acceptance | 4 |
| 6 | `CT-CARBONTALLY-LIFECYCLE-E2E-01` — one full lifecycle + one real emissions output (blockers 6, 7, 8, 13) | Test execution | Workflow acceptance | 4 (+ PD-H for factor seeding) |
| 7 | `CT-EXTRACTION-COVERAGE-01` (PD-C) · `CT-MESSAGING-CEILING-01` (PD-G) · `CT-CUSTOMER-FACTOR-BOUNDARY-01` (PD-H) · `CT-ABUSE-LIMITS-01` (PD-I) · `CT-RETENTION-N3-01` (PD-F) · `CT-UX-MP-AUTHORITY-01` (PD-A) | Implementation (per decision) | Their respective gaps | 1 |
| 8 | Backup-test default fix (blocker 16) | Implementation (small) | Safety of local drills | 1 |
| 9 | Independent QA re-verification (OHD) of items 2–8 | Independent verification | Foundation acceptance | 2–8 |
| 10 | **CrewAI V4** | Separate programme | — | Foundation acceptance **and** explicit PO authorisation |

---

## 14. Risks and assumptions

| # | Risk / assumption | Type | Mitigation / note |
|---|---|---|---|
| 1 | A future agent "cleans up" `ct_local_93d5cdd` or the `ct_*` clones and destroys the only local copies of the P17 generation | Risk | PD-4.7 + Stage 8; the 15 P17-bearing clones must be preserved or dumped first (AGENTS §55) |
| 2 | A future agent points services at `postgres` to "simplify" the topology | Risk | §9 Option D rejected in writing; AGENTS §55; the integration harness already refuses that exact target name |
| 3 | The lab DB is treated as reproducible while the **stack** it depends on is not (baseline-owned, 5442x, keys read via `supabase status`) | Risk | PD-4.4/4.6; Stage 7 |
| 4 | No verified backup of `postgres` exists (975 orgs / 1,214 auth users not reproducible from this repository) | Risk | Stage 2 (`pg_dump` + restore drill) — **should precede any risky local work** |
| 5 | Two tracked backup/restore tests default to the `postgres` DSN | Risk (safety) | Blocker 16 — change the default + add a guard |
| 6 | The ledger absence may tempt an agent to insert fabricated ledger rows | Risk | §8.6/Stage 3: forbidden explicitly; the build stamp is the honest alternative |
| 7 | Reading live/local migrations as equivalence because counts match (154 vs 135 vs 116 tables) | Risk | §8.3 states that counts prove nothing; object-level probes are required (CT-READINESS-01 §7.2 method) |
| 8 | Assumption: the running stack (5442x) was started by the **baseline** checkout `/home/shomonrobie/carbon_tally` and not by this repository | Assumption (high confidence) | Supported by: repo `config.toml` = 5432x and clean; running ports = 5442x; `~/ct_local_env/README.md` names that path as the baseline owner and its DB as `postgres @ 54426`. **Not proven by container labels** (CLI labels carry no working dir) ⇒ stated as an assumption |
| 9 | Assumption: `postgres`'s 46-row ledger means its schema was *not* built solely by the CLI chain | Assumption | 116 tables vs 104 migrations and a tip at `20260903010000`; consistent with direct-SQL/restore history (RECONCILIATION-20260927 §4) |
| 10 | Assumption: `system_settings` retention values were not read, so PD-F's current numbers are UNKNOWN | Assumption/Limit | Stated as UNKNOWN; a later task must read them before proposing values |
| 11 | Host system PostgreSQL 18 (INST-04 in the 2026-09-27 census) may still hold data | Unknown | Not re-inspected this pass (out of the read-only boundary that the census itself observed); listed as UNKNOWN |
| 12 | Windows-era `D:/carbon_ledger/.tmp_pgdata` (INST-05) still holds 3 databases | Unknown | Not inspected; PD-R7 territory |
| 13 | Service versions differ between the running stack (`postgres:17.6.1.147`, `postgrest:v14.5`, `gotrue:v2.195.0`) and stopped verification stacks (`postgres:17.6.1.159`, `postgrest:v16.1`) | Observation | Not a defect; recorded so nobody assumes parity |
| 14 | The repository contains untracked prior reports (e.g. `CT-PO-CT-READINESS-01-…`, census, reconciliation) that are strong evidence but **not committed** | Risk | They are cited here by path; committing them is a hygiene decision outside this task's scope |

---

## 15. Actions explicitly NOT performed (this task)

* **No database was created, dropped, renamed, truncated, restored or migrated.** No schema, grant, policy,
  ACL, retention setting or data row was changed in `postgres`, `carbontally_demo_local`, `ct_local_93d5cdd`
  or any other database. No migration ledger was created or written.
* **No Docker container or volume was started, stopped, recreated, removed, or re-configured** (the only
  docker commands used were `ps`, `ps -a`, `port`, `volume ls`, `network ls`, `inspect` and
  `exec … psql` **catalogue queries**).
* **No `.env` or configuration file was created, edited or re-pointed** — `backend/.env`,
  `frontend/.env.local`, `supabase/config.toml`, `supabase/config copy.toml` and the generated
  `~/ct_local_env/demo_lab/backend.env` are exactly as found.
* **No application code, test, migration or script was changed.** Nothing was staged from the pre-existing
  working-tree changes; `.gitignore`, `frontend/App_.js`, the 32 untracked debris entries and the untracked
  prior reports are untouched.
* **No credential, token, JWT, key, signed URL or complete DSN was printed, logged or committed.** All
  environment inspection was filtered (DSN host + database name only; secrets masked).
* **No destructive Git operation** was used: no `reset`, `clean`, `stash`, `checkout --`, `rebase`, `amend`
  or force-push.
* **CrewAI V4 was not started**, and no plan or scaffolding for it was created.
* **Production was not contacted**, and the hosted project was not read or written (all live statements in
  this report are HISTORICAL FACTs quoted from CLOSURE-02/RE-03).
* **No new databases were created for read-only questions** (none was needed).

---

## 16. Evidence index

### 16.1 Commands executed in this task (all read-only)

```bash
git rev-parse --abbrev-ref HEAD ; git rev-parse HEAD ; git log --oneline -6
git ls-remote github p8-release-reconciled
git status --porcelain ; git check-ignore -v backend/.env frontend/.env.local
git log --follow -- tools/demo_lab/stack.py ; git log -- supabase/config.toml
git show HEAD:supabase/config.toml | grep -nE '^port|project_id'
git ls-files supabase/migrations | wc -l

docker ps --format '…' ; docker ps -a --format '…' ; docker port <containers>
docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' <containers>   # filtered, masked
docker inspect -f '{{range .Mounts}}…' <containers>
docker inspect -f '{{index .Config.Labels "com.supabase.cli.project"}}' supabase_db_carbon_ledger
docker volume ls ; docker network ls

docker exec supabase_db_carbon_ledger psql -U postgres -Atc \
  "select datname, pg_size_pretty(pg_database_size(datname)) from pg_database where not datistemplate order by datname;"
# per-database catalogue probes (schemas, table counts, RLS counts, ledger presence, auth.users,
# storage.buckets, organizations, public.users, migration ledger rows) — see /tmp/a4_census.sh
ps -eo pid,args | grep -E 'uvicorn|react-scripts'
tr '\0' '\n' < /proc/1014820/environ | grep -E '^(DATABASE_URL|SUPABASE_URL)=…'   # masked

grep -rIn 'carbontally_demo_local|ct_local_93d5cdd|54426|54430|54326' backend frontend tools e2e qa_harness .github
ls -la ~/ct_local_env ; cat ~/ct_local_env/README.md ; cat ~/ct_local_env/start_latest.sh
```

Temporary evidence files (outside the repository): `/tmp/a4_git.txt`, `a4_files.txt`, `a4_docker.txt`,
`a4_topo1.txt`, `a4_topo2.txt`, `a4_env.txt`, `a4_dblist.txt`, `a4_census_out.txt`, `a4_cfgdiff.txt`,
`a4_cfg2.txt`, `a4_labels.txt`, `a4_envfile.txt`, `a4_deps.txt`, `a4_runtime.txt`, `a4_rt2.txt`, `a4_rt3.txt`,
`a4_last.txt`, `a4_pd_refs.txt`, `a4_pdabef.txt`, `a4_ledger.txt`, `a4_headings.txt`, `a4_labpy.txt`,
`a4_prov.txt`, `a4_p12.txt`, `a4_ctlocal.txt`, `a4_recent.txt`, `a4_sizes.txt`, `a4_hist.txt`, `a4_lab1.txt`,
`a4_final1.txt`, `a4_final2.txt`, `a4_final3.txt`.

### 16.2 Files read (repository)

`AGENTS.md` · `tools/demo_lab/README.md` · `tools/demo_lab/lab.py` · `tools/demo_lab/lab_env.py` ·
`tools/demo_lab/stack.py` · `tools/demo_lab/provision.py` · `tools/demo_lab/reset_demo_lab.sh` ·
`supabase/config.toml` (+ `config copy.toml`) · `e2e/environment/supabase/config.toml` ·
`backend/.env` (masked) · `frontend/.env.local` (masked) ·
`backend/tests/integration/conftest.py` · `backend/tests/integration/backup/test_exporter_local.py` ·
`backend/tests/integration/backup/test_restore_local.py` ·
`docs/architecture/CT-CARBONTALLY-FOUNDATION-BASELINE-01.md` (§15.2) ·
`docs/architecture/CT-CARBONTALLY-FOUNDATION-INVENTORY-02.md` (headings) ·
`docs/architecture/CT-CARBONTALLY-FOUNDATION-CLOSURE-02.md` (§1.1–§1.5, §7) ·
`docs/architecture/CT-CARBONTALLY-FOUNDATION-REMEDIATION-03.md` (§2, §3, §6, §7, §8, §9, §10, §12) ·
`docs/architecture/CT-CARBONTALLY-FOUNDATION-VERIFICATION-03.md` (§2.8 refs) ·
`docs/architecture/CT-PO-P12-STEP2-CANONICAL-DEMO-ENVIRONMENT-20260924.md` ·
`docs/architecture/CT-PO-CARBONTALLY-DATABASE-CENSUS-20260927.md` ·
`docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-20260927-REPORT.md` ·
`docs/architecture/CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-LEDGER-20260927.md` (§7) ·
`docs/architecture/CT-PO-CT-READINESS-01-MIGRATION-DRIFT-AND-CANONICAL-DB-BASELINE-AUDIT-20260927.md` (§6–§9) ·
`docs/architecture/CT-PO-CARBONTALLY-RECON-03C-IMPORT-SUMMARY-AND-SUPABASE-CONFIG-DECISION-PACK-20260927.md` (§7–§10) ·
`docs/audit/costrict/CSTR-CARBONTALLY-ENVIRONMENT-RECON-001-20261003.md` · `docs/cline/evidence/FINAL-03-DATA-PRESERVATION-20261002/02-local-environment-inventory.txt` ·
`docs/architecture/carbontally_master_handover_2026-10-05.md` · `~/ct_local_env/README.md`, `IDENTITIES.md` (listing), `start_latest.sh`, `stop_latest.sh`, `seed_local_identities.py`.

### 16.3 Commit SHAs and register citations

| Item | SHA / path |
|---|---|
| HEAD / GitHub tip at task start | `4e8a7feb405c4b5f1a516fd00c6a915a75bb3fb0` |
| DEMO-T1 (lab introduced) | `fe36cdc` |
| DEMO-T3 | `ad46599` |
| DEMO-T2-C | `05de2f3` |
| P12 Step-2 | `a9a218f`, `54ee52c` |
| `supabase/config.toml` introduced | `2d23fb8` (2026-08-06) |
| F-1 closure (CT-03 ACLs) | `8ac778e` |
| CLOSURE-02 commit | `8675fcb` (report), `8ac778e` (code) |
| RE-03 commit | `926bdbc`, publication doc `4e8a7fe` |
| PD-A…PD-F definitions | BASELINE-01 §15.2 |
| PD-C/PD-D/PD-4/PD-G/PD-H/PD-I definitions | CLOSURE-02 §7.1 · RE-03 §6/§7.3 |
| PD-1…PD-10 (reconciliation register — ID collision) | RECONCILIATION-LEDGER-20260927 §7 |

---

## 17. Owner decision summary (readable without PostgreSQL knowledge)

1. **There is one database server on your machine, not three.** Inside it there are 90 separate "databases".
   Three matter: **`postgres`** (your original demo — 975 organisations, the login accounts, the big investor
   dataset), **`carbontally_demo_local`** (the demo lab the running app actually uses — built from the
   code's migration files, 14 organisations, play/test identities), and **`ct_local_93d5cdd`** (an old
   isolated experiment from a setup task; nothing in the code uses it).
2. **The split between "business data" and "login data" was deliberate**, not a mistake: the demo lab uses
   your existing login service so it never has to touch your demo data. That is why `postgres` holds the
   logins and the lab database holds the business tables. It is written down in the lab's own documentation.
3. **Two genuine accidents remain:** (a) the old experiment database is still sitting there and the file
   `backend/.env` still points at it, and (b) the code expects the database server on ports starting `5442…`
   while this repository's config file says `5432…` — so a person setting up from scratch would get a
   server the tests cannot find.
4. **Your application's data is already in one authoritative database.** Your expectation of "one Supabase
   database" is satisfied for business data. If you also want logins stored *inside* that same database,
   that is a choice you can make (PD-4.5) — it is possible, but it costs work and risk and gains nothing
   functional today. **Cline does not recommend it.**
5. **Cline's recommended target:** keep what you already have — one server, one business database
   (`carbontally_demo_local`) as the official local environment, `postgres` left untouched as your demo and
   login store — and then fix the two accidents: point the local configuration at the right database and
   make the ports configurable so a fresh setup works.
6. **What it does not require:** no data movement, no database migration, and no change to how the app
   authenticates. It is documentation plus two small code/config changes in a later, separately-approved task.
7. **Decisions only you can make** (each with a recommended default in §11.11):
   * **PD-4.5** — one database for everything, or keep the current two? *(recommended: keep two)*
   * **PD-4.2** — do we ever move the 975-organisation demo? *(recommended: never; preserve in place)*
   * **PD-C** — what should happen to invoice lines that only have "£" or a count instead of a physical
     unit? *(recommended: show them as "no factor yet" instead of silently dropping them — 111 lines in 38
     documents are dropped today)*
   * **PD-D** — may we use the demo lab to run the seeded end-to-end tests? *(recommended: yes — without
     this, the review/approval workflow and the customer-factor rules cannot be proved at all)*
   * **PD-G** — may a former ("retained") client still send messages? *(recommended: read-only)*
   * **PD-H** — who may create a custom emissions factor? *(recommended: owners/admins, or members propose
     and owners approve)*
   * **PD-I** — should the public forms be rate-limited, and should the test-upload route exist in
     production? *(recommended: yes, and no)*
   * **PD-F** — the retention periods (needs your/legal input; we will not invent numbers)
   * **PD-A** — approve the Manual Processing screens already built (with a short fix list if any)
   * **PD-B** — which demo population is "the demo" *(recommended: lab for workflows, big demo for
     population checks)*
   * **PD-E** — confirm the consultant work already committed is the release baseline *(recommended: yes)*
8. **What Cline did NOT change:** no database was created, deleted, migrated, re-seeded or re-pointed; no
   container or `.env` was touched; no code, test or configuration file was modified; no credentials were
   printed; no Git history was rewritten; CrewAI V4 was not started.
9. **Report location:** `docs/architecture/CT-CARBONTALLY-ARCHITECTURE-DECISIONS-04.md` (this file);
   publication details in §19.
10. **The next task after your decisions:** `CT-CARBONTALLY-ARCHITECTURE-RECONCILIATION-05` (Stages 1–3:
    decision record, verified backups of all three databases, and an honest migration "build stamp"), then
    `CT-CARBONTALLY-EVIDENCE-ENVIRONMENT-01` → the security-negative and lifecycle end-to-end evidence runs.
    **CrewAI V4 remains blocked until the foundation is accepted.**

---

## 18. Machine-readable decision table (appendix)

```json
{
  "register": "CT-CARBONTALLY-ARCHITECTURE-DECISIONS-04",
  "generated_from": "docs/architecture/CT-CARBONTALLY-ARCHITECTURE-DECISIONS-04.md",
  "head_at_task_start": "4e8a7feb405c4b5f1a516fd00c6a915a75bb3fb0",
  "measured_on": "2026-10-09/10",
  "canonical_local": {
    "cluster": "supabase_db_carbon_ledger",
    "application_database": "carbontally_demo_local",
    "auth_database": "postgres",
    "residue_database": "ct_local_93d5cdd",
    "logical_databases_total": 90,
    "disposable_ct_prefix": 83,
    "migrations_available": 104
  },
  "decisions": [
    {"id":"PD-4.1","title":"Canonical local application database","options":["A: carbontally_demo_local","B: rebuild a new database","C: ct_local_93d5cdd"],"recommended":"A","blocks_acceptance":true,"blocks_v4":true,"authorises":["documentation"],"follow_up":"CT-CARBONTALLY-ARCHITECTURE-RECONCILIATION-05"},
    {"id":"PD-4.2","title":"Disposition of the 975-organisation investor dataset","options":["A: preserve in place","B: carry forward","C: retire"],"recommended":"A","blocks_acceptance":false,"blocks_v4":false,"authorises":["documentation"],"follow_up":"CT-CARBONTALLY-ARCHITECTURE-RECONCILIATION-05"},
    {"id":"PD-4.4","title":"Port/project convention (5432x vs 5442x; db.migrations)","options":["A: adopt 5442x in config.toml","B: make tooling ports configurable","C: do nothing"],"recommended":"B","blocks_acceptance":true,"blocks_v4":true,"authorises":["config","tooling"],"follow_up":"CT-CARBONTALLY-ARCHITECTURE-RECONCILIATION-05"},
    {"id":"PD-4.5","title":"Business data and auth in one database or two","options":["A: two databases (current)","B: one database (lab GoTrue)"],"recommended":"A","blocks_acceptance":true,"blocks_v4":true,"authorises":["documentation","if B: container + reprovision"],"follow_up":"CT-CARBONTALLY-ARCHITECTURE-RECONCILIATION-05"},
    {"id":"PD-4.6","title":"Single documented local environment entry point","options":["A: document run_demo_lab.sh","B: new wrapper","C: leave as-is"],"recommended":"A","blocks_acceptance":true,"blocks_v4":true,"authorises":["documentation","tooling"],"follow_up":"CT-CARBONTALLY-ARCHITECTURE-RECONCILIATION-05"},
    {"id":"PD-4.7","title":"Disposition of residue (ct_local_93d5cdd, 83 ct_* DBs, 17 volumes, ~37 containers)","options":["A: preserve all","B: dump then retire on a schedule","C: retire immediately"],"recommended":"B","blocks_acceptance":false,"blocks_v4":false,"authorises":["infrastructure (only after verified dumps)"],"follow_up":"CT-CARBONTALLY-ARCHITECTURE-RECONCILIATION-05"},
    {"id":"PD-A","title":"Ratify or withdraw CT-UX-MP-SUB-003","options":["A: ratify as delivered","B: ratify with amendments","C: withdraw and re-scope"],"recommended":"B","blocks_acceptance":true,"blocks_v4":false,"authorises":["documentation","if B: frontend fixes"],"follow_up":"CT-UX-MP-AUTHORITY-01"},
    {"id":"PD-B","title":"Authoritative demo/identity model","options":["A: investor model","B: lab model","C: both by purpose"],"recommended":"C","blocks_acceptance":true,"blocks_v4":false,"authorises":["documentation","if A: read-only QA access"],"follow_up":"CT-CARBONTALLY-EVIDENCE-ENVIRONMENT-01"},
    {"id":"PD-C","title":"Count/spend invoice lines: drop, surface, or add a spend path","options":["A: keep dropping","B: surface as unresolved","C: spend/count factor path"],"recommended":"B","blocks_acceptance":true,"blocks_v4":false,"authorises":["code (B/C)","migration (C only)"],"follow_up":"CT-EXTRACTION-COVERAGE-01"},
    {"id":"PD-D","title":"Authorised evidence environment and identities","options":["A: Demo Lab + read-only investor demo","B: new dedicated evidence DB","C: live project"],"recommended":"A","blocks_acceptance":true,"blocks_v4":true,"authorises":["seeding","test execution"],"follow_up":"CT-CARBONTALLY-EVIDENCE-ENVIRONMENT-01"},
    {"id":"PD-E","title":"Ratify or hold the consultant-parity change set","options":["A: ratify as baseline","B: hold as provisional"],"recommended":"A","blocks_acceptance":false,"blocks_v4":false,"authorises":["documentation"],"follow_up":"Stage-1 decision record"},
    {"id":"PD-F","title":"Retention (N3) durations and enforcement scope","options":["A: explicit durations per domain","B: default policy with per-org override","C: leave unratified"],"recommended":"A","blocks_acceptance":false,"blocks_v4":false,"authorises":["configuration","implementation if enforcement missing"],"follow_up":"CT-RETENTION-N3-01"},
    {"id":"PD-G","title":"Messaging send for RETAINED/READ_ONLY relationships","options":["A: keep as-is","B: deny send","C: deny send but allow a re-engagement message"],"recommended":"B","blocks_acceptance":true,"blocks_v4":false,"authorises":["code"],"follow_up":"CT-MESSAGING-CEILING-01"},
    {"id":"PD-H","title":"Who may create/update and approve a customer factor","options":["A: owner/admin only","B: member propose then owner approve","C: any member"],"recommended":"B","blocks_acceptance":true,"blocks_v4":false,"authorises":["code","migration (B if a proposal state is added)"],"follow_up":"CT-CUSTOMER-FACTOR-BOUNDARY-01"},
    {"id":"PD-I","title":"Rate limiting, test-upload exposure, report_status publicity","options":["a) A: rate limits","b) A: remove test-upload in production","c) B: annotate report_status as public"],"recommended":"(a) A, (b) A, (c) B","blocks_acceptance":true,"blocks_v4":false,"authorises":["code"],"follow_up":"CT-ABUSE-LIMITS-01"}
  ],
  "id_collision_warning": {
    "found": true,
    "detail": "CT-PO-CARBONTALLY-DATABASE-RECONCILIATION-LEDGER-20260927.md uses PD-1..PD-10, where its PD-4 means 'auth-bearing local database' and its PD-5 the port convention; the foundation register's PD-4 is the local-topology umbrella used in this report",
    "recommended_resolution": "retire PD-1..PD-10 or re-label them PD-R1..PD-R10"
  }
}
```


---

## 19. Verdict, self-check and attestation

### 19.1 Verdict

**`COMPLETE_WITH_OBSERVATIONS`.**

| Statement | State |
|---|---|
| The origin of each of the three database generations has been investigated from code, history and documentation | **VERIFIED** (§4, §6) |
| The intended architecture has been reconstructed from evidence | **VERIFIED** (§3), with two residual ambiguities stated as **UNKNOWN** (§3.4) |
| The current database / service / container / volume topology is documented | **VERIFIED** (§2, §5) |
| Migration provenance and reproducibility risks are documented | **VERIFIED** (§8) |
| A recommended canonical topology is presented with alternatives | **RECOMMENDATION** (§9 — Option C) |
| Every PD-A…PD-I decision (plus PD-4) has exact definitions, options, evidence, consequences and a recommendation | **COMPLETE** (§11) |
| Remaining acceptance blockers are classified | **COMPLETE** (§12) |
| A staged, non-destructive implementation plan is provided | **COMPLETE** (§10) |
| The topology is **resolved** | **NOT CLAIMED** — a report is not a resolution; the PO decisions in §11 and Stages 1–7 are outstanding |
| Foundation acceptance or release | **NOT CLAIMED** (AGENTS §73/§74) |
| No database consolidated, deleted, migrated or otherwise modified in this task | **VERIFIED** (§15) |
| CrewAI V4 | **NOT STARTED** |

### 19.2 Self-check (what this report asserts about itself)

* Every numeric figure quoted in §5.1/§5.2/§5.3 was produced by a catalogue query in this pass; figures that
  were **not** re-measured are labelled HISTORICAL FACT with the source report named.
* No statement of the form "the workflow works" appears anywhere except as **UNVERIFIED** with the specific
  evidence that is missing.
* No decision was implemented; no policy was invented; no number (retention, rate limit) was chosen.
* Every recommendation is labelled **RECOMMENDATION** and paired with the option set it recommends from.
* The `postgres` database is described as the **local investor-demo / authentication** database and is never
  called production; the hosted project is described only where a prior report is quoted.

### 19.3 Security and safety attestation

* Read-only throughout: no database write, no migration, no ledger write, no `CREATE`/`DROP`/`ALTER`, no
  `TRUNCATE`, no data dump; no container or volume started, stopped or removed; no `.env` or config edited.
* No secret was read into this document, a commit, or a log: DSNs appear as host + database name only, with
  passwords masked, and no key, token, JWT or signed URL is reproduced.
* Tenant isolation, provenance and auditability were neither weakened nor exercised destructively.
* No destructive Git command was used; the pre-existing working-tree changes and the 32 untracked debris
  entries were left exactly as found; only this report is staged.

### 19.4 Publication

Branch `p8-release-reconciled`; HEAD at task start = GitHub tip =
`4e8a7feb405c4b5f1a516fd00c6a915a75bb3fb0` (0 ahead / 0 behind, verified with
`git ls-remote github p8-release-reconciled`).

```text
$ git add docs/architecture/CT-CARBONTALLY-ARCHITECTURE-DECISIONS-04.md   # explicit path only
$ git diff --cached --stat
 .../CT-CARBONTALLY-ARCHITECTURE-DECISIONS-04.md    | 1404 ++++++++++++++++++++
 1 file changed, 1404 insertions(+)

$ git diff --cached | grep -nEi 'eyJ[A-Za-z0-9_-]{10}|service_role|SERVICE_KEY=|SUPABASE_ACCESS_TOKEN|BEGIN PRIVATE KEY|password=[A-Za-z0-9]'
(no matches — staged diff clean)

$ git commit -F /tmp/a4_msg.txt                       # normal commit, no force, no rebase
[p8-release-reconciled 7544d0d] docs(architecture-04): database topology investigation, architecture reconciliation, PO decision register
 1 file changed, 1404 insertions(+)
 create mode 100644 docs/architecture/CT-CARBONTALLY-ARCHITECTURE-DECISIONS-04.md
COMMIT_RC=0

$ git push github p8-release-reconciled               # fast-forward, non-forced
To https://github.com/shomonrobie/CarbonTally.git
   4e8a7fe..7544d0d  p8-release-reconciled -> p8-release-reconciled
PUSH_RC=0

$ git ls-remote github p8-release-reconciled
7544d0d19228b419c7783f8a074bc6fecfc22890	refs/heads/p8-release-reconciled

$ git rev-list --left-right --count github/p8-release-reconciled...HEAD
0	0

$ git rev-parse HEAD
7544d0d19228b419c7783f8a074bc6fecfc22890
```

**Post-publication state.** Remote tip = local HEAD = **`7544d0d19228b419c7783f8a074bc6fecfc22890`**
(0 ahead / 0 behind). The push was fast-forward and non-forced. Exactly **one** file was staged (this
report); `.gitignore` and `frontend/App_.js` remain modified-but-unstaged, and the **32** remaining untracked
entries (the pre-existing root debris and the older untracked reports; this report was the 33rd and is now
tracked) are untouched.

**SHA record.** The publication block above was committed by a follow-up documentation commit (see the
repository log: the commit immediately after `7544d0d` on `p8-release-reconciled`), because a commit cannot
contain its own SHA.

### 19.5 Recommended next steps (short)

1. The owner answers §11 (minimum: **PD-D**, **PD-4.1**, **PD-4.4**, **PD-4.5**, **PD-4.6**).
2. `CT-CARBONTALLY-ARCHITECTURE-RECONCILIATION-05` executes Stages 1–3 (§10) — decision record, verified
   backups + restore drill of all three databases, and the honest migration build stamp. **No data is
   modified.**
3. `CT-CARBONTALLY-EVIDENCE-ENVIRONMENT-01` → `CT-CARBONTALLY-RLS-NEGATIVE-01` →
   `CT-CARBONTALLY-LIFECYCLE-E2E-01` produce the behavioural evidence that is the real remaining blocker.
4. Independent QA (OHD) re-verifies steps 2–3 before any foundation-acceptance verdict.
5. **CrewAI V4 remains blocked** until the foundation is accepted and the owner authorises it.
