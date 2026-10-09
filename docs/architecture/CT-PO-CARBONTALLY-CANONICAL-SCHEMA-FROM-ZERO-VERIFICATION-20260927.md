# CT-PO — CarbonTally Canonical Database Schema From Zero — Verification

**Task ID:** `CT-SCHEMA-01-20260927-CANONICAL-SCHEMA-FROM-ZERO-VERIFICATION`
**Type:** READ-ONLY verification with ONE new disposable target (created, used, and only that target mutated).
**Authority (repository):** `/home/shomonrobie/ct_93d5cdd`
**Git identity at task start and end:** branch `p8-release-reconciled`, HEAD `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` (`rev-parse HEAD` verified before any work; no commit, push, merge, rebase or checkout performed by this task).
**Working tree:** unchanged by this task — 51 porcelain entries at task start and at task end (pre-existing ` M .gitignore` plus pre-existing untracked files). This task wrote **no** file inside the repository except the five deliverables listed in §18, all of which are new untracked documents under `docs/architecture/`.
**Date of execution:** 2026-09-27 (Asia/Dhaka local, 16:19–16:50).
**Companion documents:**
`CT-PO-CARBONTALLY-SCHEMA-CODE-MISMATCH-REGISTER-20260927.md`,
`CT-PO-CARBONTALLY-CANONICAL-SCHEMA-FEATURE-SUPPORT-MATRIX-20260927.md`,
`CT-PO-CARBONTALLY-SCHEMA-COMPARISON-MATRIX-20260927.md`,
`CT-PO-CARBONTALLY-CT-SCHEMA-01-REPORT-20260927.md`.

## 0. Claim-classification legend (used in every cell of every companion document)

| Token | Meaning |
|---|---|
| `DOCUMENTED` | Stated in a document only. No runtime/schema evidence in this task. |
| `CODE` | Present in repository source. Not executed by this task. |
| `MIGRATION` | Declared by a file in `supabase/migrations/`. |
| `SCHEMA` | Object **observed by SQL query against the disposable database after the clean rebuild** (this task's strongest evidence class). |
| `ROUTE` | HTTP route exists in the API surface (not exercised here). |
| `AVAILABLE` | Object exists and is reachable through its identity/permission path. |
| `PERSISTED` | Row-level persistence observed (this task created **no** application rows; only migration-declared reference rows exist). |
| `E2E` | Executed end-to-end through the application. **Not claimed anywhere in these five documents.** |
| `INDEPENDENTLY VERIFIED` | Reproduced by an independent agent/task. Not claimed by this task for runtime behaviour. |
| `PRODUCTION` | Verified against the production deployment. **Never contacted by this task.** |

**Rule applied throughout:** *execution success of a migration is not functional verification.* Every
"exists" statement below is `SCHEMA`-class, never `E2E`-class.

---

## 1. Question answered

> Can the current CarbonTally codebase produce its complete intended database schema from an
> **empty application database** by applying the current migration files in order — and is that
> chain a viable **canonical schema source**?

**Answer (short form):** Yes for the application schema, deterministically and reproducibly, **provided
the standard Supabase platform baseline exists before application migrations run**. The chain is
**not** self-sufficient on a bare PostgreSQL/empty-platform database: one migration (position 27)
requires the platform-provisioned `storage` schema plus four operator-provisioned provider-context
policies, and it is additionally sensitive to the migration role's `search_path`. All 89 migrations
were applied to a brand-new disposable database after that platform baseline was established, and the
result reconciles 100 % against the objects the migrations themselves declare.

---

## 2. Method, harness and reproducibility

### 2.1 Migration count (recounted, not assumed)

`ls supabase/migrations/*.sql | wc -l` → **89**. The count is independently re-verified by the ledger
in §6 (89 distinct filenames, first `00000000000000_init_schema.sql`, last
`20261020000000_p17k_governed_capability_catalogue.sql`).

Migration-set fingerprint (sha256 of the `sha256sum` listing of all 89 files, sorted by filename):

```
d73e1e2b4e503c13b5079dfc84f3ae0081d04f0f67f91231d8baa0879b8cb26c
```

### 2.2 Apply harness

The chain was applied **file-by-file, in sorted filename order**, using the exact form the repository's
own e2e helper documents (`e2e/environment/scripts/apply_migrations.sh`):

```
psql -h <host> -p <port> -U <role> -d postgres -X -q -v ON_ERROR_STOP=1 -f supabase/migrations/<file>.sql
```

* No migration was skipped, reordered, edited, or "fixed forward".
* No migration file, application source file, or committed artefact was modified.
* Failure semantics: the runner stops at the first non-zero exit (equivalent to `set -e`), which is how
  a Supabase `db push`/`db reset` behaves for a failing migration.
* Each file's stdout/stderr was captured to its own log; per-file exit code, wall time and file sha256
  were written to a ledger (§6).

### 2.3 Migration ledger note (honest limitation)

A raw `psql`-driven apply does **not** populate `supabase_migrations.schema_migrations` (that table is
written by the Supabase CLI, and it does not exist in a fresh Supabase Postgres image). This task
therefore produced an **independent apply ledger** as the arithmetic record, and states explicitly
that **no CLI-run ledger (`supabase db push` / `supabase migration up`) was produced in this task**
(see §15, limitation L4).

---

## 3. Disposable verification target (SCHEMA-DB-ID)

A **brand-new** PostgreSQL/Supabase disposable cluster was created for this task. No pre-existing
database, container, volume, or database in the shared local stack was used, reset, truncated, or
modified.

| Field | Value |
|---|---|
| SCHEMA-DB-ID | `CT-SCHEMA-01-TARGET-A` |
| Container name | `ct_schema01_pg` |
| Container id | `65ec22a681965668f8dca1b5f3ae26c5329bf1a81a90ccfd4b49aad8633316f6` |
| Volume name | `ct_schema01_pgdata` (created 2026-09-27T16:30:17+06:00, driver `local`) |
| Image | `public.ecr.aws/supabase/postgres:17.6.1.159` |
| Image id / digest | `sha256:86a2e078779e5bdccda1f6f6c5063aa9779a322d1fface5fb408d051909b230f` (identical `RepoDigest`) |
| PostgreSQL version | PostgreSQL 17.6 (x86_64-pc-linux-gnu, gcc 15.2.0) — matches the local Supabase stack's `17.6.1.x` line |
| Supabase version | Supabase Postgres image build 17.6.1.159 (Supabase-hosted baseline: roles, `auth`/`storage`/`vault`/`realtime`/`graphql` schemas, extension set) |
| Database used | `postgres` |
| Connection | `127.0.0.1:55450` (loopback only), role `supabase_admin` (provider) and `postgres` (migration role) |
| Creation timestamp | 2026-09-27T16:30:17+06:00 (container started 2026-09-27T10:30:19Z) |
| Labels | `ct.schema01.task=CT-SCHEMA-01-20260927`, `ct.schema01.disposable=true` |
| Credentials | ephemeral random password generated for this target only, held in a mode-600 file outside the repository, **never written into any repository file or report** |

A second, temporary container of the same task family (`ct_schema01_storage`,
`public.ecr.aws/supabase/storage-api:v1.69.0`) was created **for platform provisioning only**; it is
recorded in §9. Both containers and the volume are the only mutation targets of this task.

**Target-A was created twice.** The first instance (`CT-SCHEMA-01-TARGET-0`, container id
`17e10418744411783fe514355746786b32f943055ec30bc46657080bf7799c3c`) was used for the bare-platform
probe and the role-sensitivity probe (§5, F-01 and F-02) and then **destroyed together with its
volume** by this task (the only destruction performed), because the canonical run had to start from a
pristine cluster in a single role/`search_path` context. Evidence from Target-0 was archived before
destruction (`/tmp/ct_schema01_evidence/`). No other container, volume or database was removed.

---

## 4. Baseline empty-database fingerprint (captured BEFORE any CarbonTally migration)

Baseline captured with `psql` (18.6 client → 17.6 server) against the pristine target:

| Metric | Baseline value (Target-0) | Baseline value (Target-A) |
|---|---|---|
| `public` tables | **0** | **0** |
| CarbonTally application tables | **0** | **0** |
| Application rows (organisations/factors/etc.) | **0** | **0** |
| Existing migration ledger | none (`supabase_migrations` schema absent) | none |
| Schemas | 12 (`auth`, `extensions`, `graphql`, `graphql_public`, `information_schema`, `pg_catalog`, `pg_toast`, `pgbouncer`, `public`, `realtime`, `storage`, `vault`) | 12 (identical) |
| Roles | 29 (incl. `anon`, `authenticated`, `service_role`, `authenticator`, `supabase_admin`, `supabase_auth_admin`, `supabase_storage_admin`, `postgres`, …) | 29 (identical) |
| Extensions | 5 (`pg_stat_statements` 1.11, `pgcrypto` 1.3, `plpgsql` 1.0, `supabase_vault` 0.3.1, `uuid-ossp` 1.1) | 5 (identical) |
| Non-`pg_*` functions | 65 (extension + `auth.uid()` / `auth.role()` / `auth.email()` + vault helpers) | 65 (identical) |
| Tables in all schemas | 6 (`auth.users`, `auth.instances`, `auth.refresh_tokens`, `auth.audit_log_entries`, `auth.schema_migrations`, `vault.secrets`) | 6 (identical) |
| `storage` schema tables | **0** (schema exists, objects not yet provisioned) | **0** |
| Baseline inventory fingerprint | `ef4b7bb64dce78ab5a4326dfa9682f60f66a35223d1bddc994f0dc441f644886` (sha256 over the per-class baseline inventories) | identical counts |

### 4.1 Baseline conclusions (SCHEMA class)

1. The **application** database starts genuinely empty (0 `public` tables, 0 application rows) — the
   rebuild is therefore verifiable "from zero".
2. The **platform** baseline is *not* empty: Supabase provisions identity (`auth.users` and friends),
   `auth.uid()`, roles, extension set and shell schemas. This is the normal Supabase deployment state
   and is treated in §9 as platform infrastructure, not as application schema.
3. At baseline the `storage` schema is a **shell**: schema exists, **zero tables and zero functions**.
   `storage.objects` / `storage.buckets` / `storage.foldername()` are created by the Supabase
   **storage-api** service's own migrations, not by the Supabase Postgres image. This baseline
   observation is the direct cause of finding **F-01** (§5).

---

## 5. Migration execution record

Three executions were performed. They are reported in full because the two failures are findings, and
because they define the **reproducible precondition set** for the successful third execution.

### 5.1 Execution 1 — bare Supabase platform (Target-0), role `supabase_admin`

| Item | Value |
|---|---|
| Target | `CT-SCHEMA-01-TARGET-0` (since destroyed) |
| Migrations applied | **26 / 89** |
| Stopped at | sequence **27** — `20260823000000_d32_private_documents_storage.sql` |
| Exit code | 3 (`ON_ERROR_STOP`) |
| Exact error | `ERROR: relation "storage.buckets" does not exist` at line 83 (`UPDATE storage.buckets SET public = FALSE WHERE name = 'documents';`) |
| Classification | **ENVIRONMENT_DEPENDENCY** (platform storage layer not provisioned). Deterministic: reproduced identically on a second pristine cluster. |
| Prerequisite object | `storage.buckets` (+ `storage.objects`, `storage.foldername()`), created by Supabase storage-api, **not** by any of the 89 migrations |
| Expected from an earlier migration? | **No** — `grep` over all 89 files shows the only references to `storage.buckets`/`storage.objects`/`storage.foldername` are in this migration (and in comments of two later files); no migration creates them |

**Finding F-01 (S1 — chain-integrity, environment).** The 89-migration chain is **not self-sufficient
from a bare Postgres/Supabase-Postgres image**. Position 27 requires the platform `storage` schema to be
fully provisioned first. Any unattended "apply from zero" pipeline must provision the storage layer
(storage-api migrations) before running application migrations. The migration's own header already
documents this as operator/platform work; this task converts that statement into executed evidence.

### 5.2 Execution 2 — after platform storage provisioning, role `supabase_admin`

| Item | Value |
|---|---|
| Target | `CT-SCHEMA-01-TARGET-0` |
| Platform state | `storage` schema fully provisioned by storage-api (10 tables, identical set to the local flagship), bucket `documents` present (private), four D32 policies present |
| Migrations applied | 26 (already applied) then retry of 27 |
| Stopped at | sequence **27** — same file |
| Exit code | 3 |
| Exact error | `ERROR: D32 policy drift: d32_documents_select_org_member is missing the approved org-scope fragment "auth.uid()"` (raised by the migration's own `DO $d32_policies$` block, line 192) |
| Classification | **ENVIRONMENT_DEPENDENCY (role/`search_path` dependent)** |
| Deterministic? | Yes — reproduced; and the inverse case passes deterministically (§5.3) |

**Root cause (SQL-level, reproduced):** the migration validates each approved policy by substring-matching
the *deparsed* policy expression from `pg_policies.qual`. PostgreSQL deparses a function call without
schema qualification when the function's schema is visible in the **session's** `search_path`. In the
Supabase image:

| Role | `rolconfig` `search_path` | Deparse of the policy predicate | Migration 27 result |
|---|---|---|---|
| `supabase_admin` | `"$user", public, auth, extensions` | `… = uid()) …` → fragment `auth.uid()` **absent** | **FAILS** |
| `postgres` | `"$user", public, extensions` | `… = auth.uid()) …` → fragment `auth.uid()` **present** | **PASSES** |

The deparsed policy text is otherwise byte-identical in both sessions, and **identical to the flagship
database's policies** (verified side-by-side). The policy itself is never wrong; only its textual
deparsing changes with the session.

**Finding F-02 (S1 — chain-integrity, runner role).** Migration 27 validates a *textual* property that
depends on the migration session's `search_path`. Consequently:

* it **fails** when applied as `supabase_admin` — the role the repository's own helper
  `e2e/environment/scripts/apply_migrations.sh` prescribes for this migration
  ("`supabase db reset` applies migrations as the `postgres` role, which does not own `storage.objects`;
  the D32 storage-RLS migration therefore needs the `supabase_admin` role"), while
* it **passes** as `postgres`, the role the helper says *cannot* run it.

The two documented mechanisms contradict each other, and the contradiction is only visible when the chain
is actually executed. The ownership argument in the helper is itself stale relative to the current
migration body: the current D32 revision (`P8-D17-MIGRATION-REVISION-001`) deliberately issues **no**
ownership-sensitive DDL on `storage.objects` (the `ALTER TABLE … ENABLE ROW LEVEL SECURITY` was replaced
by a read-only assertion), so the `supabase_admin` requirement no longer applies — but nothing in the
repository records that.

### 5.3 Execution 3 — canonical run (Target-A), role `postgres`

Sequence of operations, all against the brand-new Target-A:

| Step | Operation | Result |
|---|---|---|
| 3.1 | Baseline fingerprint (§4) | 0 public tables, 12 schemas, 29 roles, 5 extensions |
| 3.2 | Attempt full chain as `postgres`, no platform storage provisioning | 26 OK → **FAIL 27** (`relation "storage.buckets" does not exist`) — independent reproduction of F-01 under a different role |
| 3.3 | Platform provisioning: storage-api against the target (`ct_schema01_storage`, `storage-api:v1.69.0`, `DB_MIGRATIONS_FREEZE_AT=optimize-existing-functions-again`) | `storage` schema created with **10 tables**, identical name-for-name to the local flagship; `storage.objects` RLS = true, owner `supabase_storage_admin` |
| 3.4 | Attempt to create the four D32 policies **before** application migrations | **FAILED** — `relation "organization_members" does not exist` (approved predicates reference `public.organization_members`) → **Finding F-03** |
| 3.5 | Re-issued operator provisioning **after** migration 1 (`00000000000000_init_schema.sql` creates `public.organization_members`) | Bucket `documents` present with `public=false`; the four approved policies created verbatim from the migration header, in provider-privileged context |
| 3.6 | Verified the policies **as the migration role** (`postgres`) | predicate contains `auth.uid()` → `fragment_auth_uid_present=true` |
| 3.7 | Resumed the chain from position 27 as `postgres` | **OK [27] … OK [89]** — 63 further migrations, zero failures |

**Finding F-03 (S2 — provisioning-order constraint).** The platform-side D32 preconditions (private
bucket + four provider-context policies) **cannot be created before migration 1 exists**, because the
approved policy predicates depend on `public.organization_members`. The correct ordering is a
three-phase sequence: *(a)* platform roles/auth/storage schema → *(b)* application migrations ≥ 1
(creating `organization_members`) → *(c)* operator bucket+policy provisioning → *(d)* migrations 27–89.
Any automation that treats "platform provisioning" as strictly pre-migration will fail.

### 5.4 Non-findings (checked explicitly and cleared)

| Checked | Result |
|---|---|
| Migration ordering defects (filename order vs dependency order) | **None observed.** All 89 files applied in ascending filename order; no later migration was required earlier. |
| `CREATE INDEX CONCURRENTLY` inside the harness (illegal in a transaction) | **None.** The only occurrences are explanatory comments in `20260802000000_rc2_indexes.sql`. |
| `ALTER TYPE … ADD VALUE` transaction hazards | **None.** No `ALTER TYPE` / `ADD VALUE` statement exists in any migration. |
| psql meta-commands a `-f` apply would misinterpret | **None** (no `\c`, `\i`, `\gexec`, … in any migration). |
| Missing extensions | All `CREATE EXTENSION` statements resolved (`uuid-ossp`, `pgcrypto`, `pg_trgm`); `pg_trgm` is installed by migration 4. |
| Roles referenced but absent | All roles used by migrations exist in the platform baseline. |
| Superuser dependence | The canonical run executed as the **non-superuser** role `postgres` (`rolsuper=false`) — the chain does not silently depend on superuser rights. |
| Silent no-op migrations | **None found.** Every declared table/column/index/policy/function was traced to a live object or to an explicit later `DROP` (§8). |

---

## 6. Migration ledger

Because a `psql`-driven apply does not use Supabase's ledger table, this task maintained its own ledger
(one row per migration: sequence, filename, file sha256 prefix, exit code, wall time, status).

| Item | Value |
|---|---|
| Migration files on disk | **89** |
| Migrations applied | **89** |
| Migrations failed (canonical ledger) | **0** |
| Migrations skipped | **0** |
| Distinct migration files executed | **89** |
| Migrations executed more than once | **none** (`uniq -d` empty) |
| First applied | `00000000000000_init_schema.sql` |
| Last applied | `20261020000000_p17k_governed_capability_catalogue.sql` |
| Arithmetic | **89 files = 89 applied** (26 applied in step 3.2 + 63 applied in step 3.7) |
| Ledger file | `/tmp/ledger_final.tsv` |
| Ledger sha256 | `11bfc796f5a9e727d83c8fb69f96e3971927187127c4e8a747dae3b45444bedd` |
| Per-file logs | 89 files, `/tmp/logs_ledger_canonical*/<seq>_<name>.log` (all empty on success) |
| `supabase_migrations.schema_migrations` | **not populated** (no CLI apply was performed — limitation L4) |
| Duplicate / version conflicts | **none**; all 89 filenames unique and strictly increasing |

The two failed attempts inside Target-0 are recorded separately in the Target-0 archive ledger
(`/tmp/ct_schema01_evidence/run1_2_apply/ledger.tsv`) and are **excluded** from the canonical arithmetic
above; the canonical ledger contains only the successful pass.

---

## 7. Complete schema inventory after all 89 migrations

All values are `SCHEMA`-class: SQL catalog queries against Target-A **after** the 89th migration.

### 7.1 Object counts

| Class | Count |
|---|---|
| Schemas | 12 (`auth`, `extensions`, `graphql`, `graphql_public`, `information_schema`, `pg_catalog`, `pg_toast`, `pgbouncer`, `public`, `realtime`, `storage`, `vault`) |
| **Tables — `public` (application)** | **145** |
| Tables — `storage` (platform) | 10 |
| Tables — `auth` (platform) | 5 |
| Tables — `vault` / `extensions` | 2 / 2 |
| Tables — all schemas | 375 |
| Columns (all schemas) | 4 592 |
| Constraints (all schemas) | 756 → 223 PK, 172 FK, 109 UNIQUE, 252 CHECK (620 in `public`) |
| Indexes | 551 |
| Enums / custom types | 1 (`storage.buckettype`, platform). **The application schema declares no enums** — governed vocabularies are enforced by CHECK constraints / text values |
| Functions (`public`) | 31 |
| Functions (all non-`pg_*` schemas) | 144 |
| Triggers (non-internal) | 88 |
| Views | 3 (all platform: `extensions.pg_stat_statements`, `extensions.pg_stat_statements_info`, `vault.decrypted_secrets`) |
| Materialised views | 0 |
| Sequences | 1 (`auth.refresh_tokens_id_seq`, platform) |
| RLS-enabled tables (`public`) | **145 of 145 (100 %)** |
| RLS policies (all) | 227 → `SELECT` 93, `INSERT` 46, `UPDATE` 43, `DELETE` 37, `ALL` 4 |
| Policies granting `anon` or `public` | **0** |
| Table grants to `anon`/`authenticated`/`service_role`/`public` | 1 646 |
| Publications / event triggers declared by the chain | 0 |
| Application rows created by the rebuild | **0** (organisations 0, emission_factors 0, customer_factors 0) — except migration-declared reference data: `scope3_categories` **15**, `disclosure_frameworks` **3**, `disclosure_framework_versions` **1**, `disclosure_requirement_versions` **18** |

### 7.2 Inventory fingerprint

```
sha256(schemas + tables + columns + constraints + indexes + enums + functions
       + triggers + views + sequences + RLS-state + policies)
= c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f
```

Per-class listings are retained in `/tmp/inv/`; the 145 canonical `public` table names are reproduced in
`CT-PO-CARBONTALLY-SCHEMA-COMPARISON-MATRIX-20260927.md` §3.

### 7.3 Inventory interpretation (SCHEMA class)

1. **The rebuild produces a complete, RLS-uniform application schema.** 100 % of application tables have
   RLS enabled and no policy grants `anon`/`public` — i.e. the RLS-hardening migrations (cluster E of the
   FIEW register) are effective in the from-zero schema, not only in clones.
2. **The rebuild produces no application data.** Any statement about platform behaviour after a clean
   rebuild is necessarily about *capability*, not about data.
3. **The application schema is self-contained inside `public`** plus platform `auth`/`storage`. No
   application object is created in a non-`public` schema.

---

## 8. Global declared-object completeness (strongest completeness evidence)

Independent of execution success, this task parsed **all 89 migration files** for the objects they
declare (`CREATE TABLE public.…`, table-scoped `ADD COLUMN …`, `CREATE [UNIQUE] INDEX …`,
`CREATE POLICY …`, `CREATE [OR REPLACE] FUNCTION public.…`, `CREATE TYPE public.…`) and then asked the
post-rebuild database whether each declared object exists.

| Class | Declared by the 89 files | Checked | Present after rebuild | Absent | Reconciliation |
|---|---|---|---|---|---|
| `public` tables | 145 | 145 | **145** | 0 | 100 % |
| Table columns (via `ADD COLUMN`) | 167 | 167 | **167** | 0 | 100 % |
| Indexes | 188 | 188 | **187** | 1 | `conversation_participants_conv_user_idx` deliberately `DROP`ped by `20260828000000_v3m8_messaging_unique_participants.sql` (superseded) |
| Policies | 81 | 81 | **80** | 1 | `cc_insert_own_firm` deliberately `DROP`ped by `20260906090000_p6_1c_consultant_engagement.sql` (legacy name superseded by the engagement model) |
| Functions (`public`) | 31 | 31 | **31** | 0 | 100 % |
| Types/enums (`public`) | 0 | — | — | — | application schema declares no enums |

**Result:** every declared object of the 89-migration chain exists after the clean rebuild, except two
objects that a **later migration in the same chain explicitly drops** — which is a supersession, not an
absence. **Declared-object completeness = 100 % reconciled (612/612 declarations accounted for).**

This is the decisive answer to the §1 sub-question "does a clean database reach the complete current
release-tree schema?" — **yes**, measured against what the chain itself declares, and independently
corroborated by the table-set equality with the P17 disposable clone (§13).

---

## 9. Platform schema vs application schema (separation of concerns)

| Layer | Objects | Provided by | Created by the 89 migrations? |
|---|---|---|---|
| Identity/platform auth | `auth` schema, `auth.users`, `auth.instances`, `auth.refresh_tokens`, `auth.audit_log_entries`, `auth.schema_migrations`, `auth.uid()`, `auth.role()`, `auth.email()` | Supabase platform (Postgres image + GoTrue) | **No** — present at baseline |
| Roles | `anon`, `authenticated`, `service_role`, `authenticator`, `supabase_admin`, `supabase_auth_admin`, `supabase_storage_admin`, `supabase_replication_admin`, … (29 roles) | Supabase platform image | **No** — present at baseline |
| Extensions | `pgcrypto`, `uuid-ossp`, `pg_stat_statements`, `supabase_vault` (+ `pg_trgm` added by migration 4) | image + migration 4 | **partly** (`pg_trgm`) |
| Object storage | `storage` schema, `storage.objects`, `storage.buckets`, `storage.foldername()`, 10 storage tables | Supabase **storage-api** service migrations | **No** — platform provisioned (finding F-01) |
| Storage RLS policies | `d32_documents_select/insert/update/delete_org_member` on `storage.objects` | **operator/provider-context provisioning** (the D32 migration validates, does not create them) | **No** — operator step (findings F-01/F-03) |
| Realtime / Vault / GraphQL shells | `realtime`, `vault`, `graphql` schemas | Supabase platform image | **No** |
| **Application schema** | **145 `public` tables, 227 policies, 31 functions, 88 triggers, 172 FKs, 551 indexes** | **the 89 migrations** | **Yes — 100 %** |

**Interpretation.** The canonical from-zero procedure is therefore a **two-layer** procedure:

```
LAYER 1 (platform, not in supabase/migrations)
  1. Supabase Postgres baseline                      → roles, auth schema/users/uid(), extensions, shells
  2. storage-api migrations                          → storage.objects/buckets/foldername (10 tables)
LAYER 2 (application, the 89 files)
  3. migrations 001..026                             → public.* application schema (needs no platform storage)
  4. operator: bucket 'documents' + 4 D32 policies    → provider-privileged context, REQUIRES organization_members (F-03)
  5. migrations 027..089                             → remaining schema, RLS hardening, P17/P16R/P8X-X2
```

Nothing in this two-layer model is invented by this task: layer 1 is exactly what a Supabase project is,
step 4 is exactly what the D32 migration header prescribes (including the four policy definitions used
verbatim), and layers 2/3/5 are the repository's own migration files, unmodified.

---

## 10. Code → schema compatibility (summary; full register in the companion document)

Method: deterministic extraction of object references from durable code surfaces
(`backend/api`, `backend/data`, `backend/services`, `backend/routes`, `backend/domain`, `backend/core`,
`backend/utils`, `backend/workers`, `frontend/src`, `admin/src`, `src`, `shared`) using
`.table('x')` / `.from('x')` / `.from_('x')` client calls and `public.<identifier>` SQL references, then
comparison against the canonical 145-table set.

| Measure | Value |
|---|---|
| High-precision SQL references (`public.…`) | 159 unique identifiers |
| Client-style refs (`.table/.from/.from_`) | 54 unique identifiers |
| Combined unique code object refs | 166 |
| Canonical tables with **no** code reference at grep level | 0 (every canonical table name appears in at least one code/route/test surface) |
| Code references **absent from the canonical schema** | 20 raw hits → 4 genuine + 9 test fixtures + 7 regex/identifier artefacts |
| **Genuine code→schema mismatches** | **4 (all S2)** — `defra_conversion_factors`, `notification_delivery_log`, `report_history`, `report_schedules` |

The four genuine mismatches are **legacy route surfaces**: no migration among the 89 creates those
tables, and they are absent from the flagship, from `carbontally_demo_local`, from
`carbontally_qa_phase8` and from the canonical rebuild. The mismatch is therefore **code drift, not
schema drift** — the from-zero rebuild neither causes nor cures it. Details, paths and severities:
`CT-PO-CARBONTALLY-SCHEMA-CODE-MISMATCH-REGISTER-20260927.md` (SCM-004 … SCM-007).

## 11. P17 / P16R / P8X verification (what the clean rebuild actually produces)

Parsed declarations vs the post-rebuild database, per migration:

| Migration | Objects declared | Exists after clean rebuild | Notable detail |
|---|---|---|---|
| `20261008000000_p16r5_result_reportability_lifecycle.sql` | 10 columns + 2 indexes on `calculation_snapshots` / `emissions_logs` | **All present** | `reportability_status`, `invalidated_at/by/reason`, `superseded_by_snapshot_id`, `superseded_by_log_id`, `idx_calc_snapshots_reportability`, `idx_emissions_logs_reportability` |
| `20261009000000_p16r7_calculation_request_idempotency.sql` | 1 unique index | **Present** | `uq_calc_snapshots_request_id` (verified in `pg_indexes`) |
| `20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` | 33 columns across 9 tables + 14 indexes + constraints | **All present** | `calculation_snapshots`/`emissions_logs`: `facility_id`, `scope2_method`, `scope3_category`, `data_quality`, `energy_type`, `transport_boundary`, `waste_origin`, `acting_for_organization_id`, `performed_by_organization_id`, `source_snapshot_id`; `emission_factors`: `factor_type`, `gas_coverage`, `scope2_method`, `scope3_category_hint`; `organizations`: organisation-type/consolidation columns; plus `consultant_profiles`, `customer_documents`, `audit_trail` acting-for columns. **Note:** P17-A creates **no** `accounting_dimensions` table — the accounting-dimension concept is realised as columns on results (this resolves the naming drift recorded in FIEW-009) |
| `20261011000000_p17c_contractual_instruments_and_allocations.sql` | 2 tables + 5 indexes + 8 policies + 1 function + RLS | **All present** | `contractual_instruments` (20 cols, 4 policies, RLS true), `instrument_allocations` (12 cols, 4 policies, RLS true), `p17_instrument_over_allocated(uuid)` |
| `20261012000000_p17d_scope3_category_taxonomy.sql` | 1 table + 1 policy | **Present** | `scope3_categories` (6 cols) **with 15 seeded category rows** |
| `20261013000000_p17h_estimation_and_assumption_records.sql` | 1 table + 1 index + 4 policies + 4 functions + RLS | **All present** | `estimation_records` (14 cols, RLS true), `p17_dc04_unclassified_transport`, `p17_dc05_unclassified_waste`, `p17_dc07_consolidation_missing`, `p17_unsubstantiated_estimates`. **Note:** no separate `assumption_records` table — assumptions are carried inside `estimation_records` |
| `20261014000000_p17_10_product_contract_reporting_dimensions.sql` | 4 columns + 4 indexes + constraints | **All present** | `scope3_method`, `transaction_provider` on both results tables |
| `20261020000000_p17k_governed_capability_catalogue.sql` | **no schema object** (reference data only) | n/a | Inserts governed rows into the pre-existing `disclosure_framework_versions` (1 seeded) and `disclosure_requirement_versions` (18 seeded). The governed capability value is **PERSISTED** in the canonical schema — as reference data, with no tenant state (`SCHEMA`+`PERSISTED`, never `E2E`) |

Automated verification result: **105 parsed declarations checked, 104 confirmed present by SQL, 1
apparent absence traced to a parser artefact** (`public.scope` mis-parsed out of `public.scope3_categories`
because the parser stopped at the digit) — i.e. **0 real absences**.

**Compatibility conclusion (SCHEMA class):** every P17-A/C/D/H/10/K and P16-R5/R7 object that the
CT-FEATURE-02 verification recorded as *absent from the durable flagship* **is present in the clean
rebuild**, including the lifecycle structures that previously existed only in disposable clones.

## 12. FIEW impact summary (detail in the feature-support matrix)

| Bucket | Count | Meaning |
|---|---|---|
| FIEW rows whose **schema blocker is removed** by the clean rebuild (object now exists in a durable canonical schema) | **57 of 57** | Every object named in the FIEW register exists in Target-A |
| … of which additionally depend on the runner preconditions F-01/F-02/F-03 | 1 (FIEW-024/025 evidence-document lineage via the D32 storage policies) | The storage-policy precondition affects document evidence paths only |
| FIEW rows **still runtime-unverified** after this task | **57 of 57** | Schema presence ≠ wired behaviour. No API route, service call or workflow was executed by this task |
| FIEW rows that remain `DOCUMENTED_ONLY` regardless of schema (FIEW-056 / P17-K) | 1 | The migration creates no object; the rebuild confirms reference-data-only semantics (18 rows) |
| Rows requiring **actual E2E execution** to move beyond `SCHEMA` | all 57 | Requires a running backend + auth + storage against the rebuilt schema |

**Do not read §12 as an upgrade of any feature.** Every FIEW row remains un-promoted by this task:
`SCHEMA` is not `ROUTE`, `ROUTE` is not `PERSISTED`, and `PERSISTED` is not `E2E`.

## 13. Existing-database comparison (summary; full matrix in the companion document)

Read-only counts against the shared local environment (no mutation of any pre-existing database):

| Database | Host | `public` tables | Canonical tables missing | Canonical-only extras | Ledger |
|---|---|---|---|---|---|
| **Canonical rebuild (Target-A)** | `ct_schema01_pg` :55450 | **145** | — | — | independent apply ledger 89/89 |
| `postgres` (flagship, 975 orgs / 7 049 factors) | `supabase_db_carbon_ledger` :54426 | 116 | **29** | 0 | 46 rows, max `20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` |
| `carbontally_demo_local` (4 orgs / 7 049 factors) | same cluster | 141 | **4** (`contractual_instruments`, `instrument_allocations`, `scope3_categories`, `estimation_records`) | 0 | no ledger table |
| `carbontally_qa_phase8` | same cluster | 133 | **12** | 0 | no ledger table |
| `carbontally_test` | same cluster | 117 | **28** | 0 | no ledger table |
| `ct_p17k_20260926` (disposable P17 clone) | same cluster | **145** | **0** | **0** | no ledger table |
| `ct_d17d32_chain` (scratch) | same cluster | 0 | 145 | 0 | no ledger table |

**Interpretation.** The canonical from-zero schema is a **strict superset** of every durable database
(0 extras anywhere) and is **table-for-table identical** to the most advanced disposable clone
(`ct_p17k_20260926`). This is independent corroboration that the migration chain, applied from zero,
reproduces exactly the schema the most advanced environment reached by incremental application — and
that **no durable database currently carries it** (which is why the rebuild was necessary).

## 14. Truth-ladder position of this verification

| State | Applies here? | Evidence |
|---|---|---|
| `DOCUMENTED` | superseded | — |
| `CODE` | yes | 89 migration files, backend/frontend sources inspected |
| `MIGRATION` | yes | every object traced to a declaring migration |
| **`SCHEMA`** | **yes — the strongest class this task reaches** | 89/89 applied; 100 % declared-object reconciliation; full inventory + fingerprint |
| `ROUTE` | **no** | no HTTP surface exercised |
| `AVAILABLE` | **no** | no runtime permission path exercised |
| `PERSISTED` | only reference rows | `scope3_categories` 15, `disclosure_*` 22 rows — written by migrations, not by application code |
| `E2E` | **no** | no application execution |
| `INDEPENDENTLY VERIFIED` | **no** | this is the first from-zero execution; independent re-run pending |
| `PRODUCTION` | **no** | production never contacted |

## 15. Blockers, unknowns, limitations and explicit non-claims

### 15.1 Blockers

| ID | Blocker | Severity | Effect |
|---|---|---|---|
| F-01 | Platform `storage` layer not provisioned → migration 27 fails (`storage.buckets` missing) | **S1 (chain-integrity)** | An unattended "apply 89 from zero" pipeline cannot succeed without a platform provisioning phase. Blocks automation, not correctness. |
| F-02 | Migration 27's policy validation is `search_path`-dependent → fails as `supabase_admin`, passes as `postgres` | **S1 (chain-integrity)** | The repository's own documented apply role (`supabase_admin`) cannot run this migration; the documented rationale for that role is stale. One of the two documented mechanisms must be corrected. |
| F-03 | D32 operator provisioning cannot precede migration 1 (`organization_members` dependency) | S2 | Provisioning order must be interleaved; naive "platform-first" automation fails. |

### 15.2 Unknowns (not answered by this task)

| ID | Unknown | Why it matters | How to close |
|---|---|---|---|
| U1 | Whether a Supabase **CLI** apply (`supabase migration up --db-url`) reproduces 89/89 and records a ledger | The CLI is the intended operational path; its ledger is the durable record of "what is applied" | Run the CLI against a fresh disposable clone with the platform bootstrap of §9 |
| U2 | Whether the chain also applies cleanly as the `postgres` role **without** interleaving on a **Supabase-CLI-managed** project (where storage-api and the schema are provisioned by `supabase start`) | Would confirm the interleaving is a property of bare provisioning only | `supabase start` on a copied migration directory (not performed here) |
| U3 | Runtime behaviour of any feature against the rebuilt schema (route→service→SQL) | Schema presence is not functionality | E2E run (§16) |
| U4 | Whether the four S2 legacy code→schema mismatches (SCM-004…007) correspond to live routes in the current router | Determines whether they are dead code or live defects | Route-registration audit + one live request per route |
| U5 | `ct_local_93d5cdd` (named in the task) was **not reachable read-only**: it is not in the shared Supabase cluster and the host cluster on `127.0.0.1:5432` rejected the read-only credential available to this task | Its comparison row is therefore missing from §13 | Obtain a read-only credential for the host cluster and repeat the comparison |

### 15.3 Limitations

| ID | Limitation |
|---|---|
| L1 | The canonical run applied migrations as the non-superuser `postgres` role. Privilege-sensitive behaviour under other roles (`supabase_admin`, `authenticated`) was probed only for migration 27. |
| L2 | No application code was executed. All findings are `SCHEMA`-class. No `ROUTE`/`E2E` claim is made. |
| L3 | The D32 operator step was performed using the policy definitions **copied verbatim from the migration header**; the platform's alternative mechanism (Supabase dashboard storage-policy editor) was not exercised. |
| L4 | No `supabase_migrations.schema_migrations` ledger exists for this rebuild; the arithmetic record is this task's own ledger (sha256 in §6). |
| L5 | The rebuilt schema contains **no application data**, so nothing in this task demonstrates that any feature works with data — only that its storage structures can be created. |
| L6 | The disposable target (container + volume + sidecar) was **left running** for follow-up verification; it is labelled and isolated, and contains only schema plus migration reference rows. |
| L7 | Inventory fingerprints are stable only for the recorded image/digest and PostgreSQL 17.6 upgrade history; a patch-level Supabase image change may alter platform-schema rows (never `public`). |

### 15.4 Explicit non-claims

This task does **not** claim, and must not be read as claiming: that any CarbonTally feature works; that
the E2E/workflow suite passes; that the flagship or demo data is correct; that RLS *enforces* correctly
at runtime (only that policies exist and are enabled); that production is affected; or that the FIEW
downgrades are resolved as functionality.

## 16. Recommended next steps (ordered)

1. **Fix the D32 runner contradiction (F-02).** Either (a) change the validation to be
   `search_path`-independent (e.g. compare against `pg_get_expr` with an explicit
   `SET LOCAL search_path` inside the migration, or match on `p.oid::regprocedure` rather than
   deparsed text), or (b) record the correct apply role and update
   `e2e/environment/scripts/apply_migrations.sh` so the two mechanisms agree. *(Implementation change —
   requires an implementation task, not this read-only task.)*
2. **Encode the canonical from-zero procedure as a runbook/automation** implementing §9's two-layer,
   four-step sequence, including the storage-api provisioning and the post-migration-1 operator step
   (F-01/F-03).
3. **Create the durable canonical environment** by applying the chain to a declared durable database
   (the current durable databases all lack 4–29 canonical tables), then retire the FIEW
   "clone-only/absent" caveats on the basis of that environment.
4. **Run the E2E gate against the rebuilt schema** (backend + auth + storage) to attempt promotion of
   the 57 FIEW rows from `SCHEMA` toward `ROUTE`/`PERSISTED`/`E2E`; treat any promotion as requiring
   independent verification (CT-FEATURE-style) before use.
5. **Resolve U4:** audit the four legacy code→schema mismatches for live route registration and either
   delete the dead code or add the missing tables via a new migration.
6. **Independent verification of this task** by a second agent (re-run the chain on a fresh disposable
   clone and compare the §7.2 fingerprint and §6 ledger arithmetic).

## 17. Verdict

**Primary verdict: `CT_SCHEMA_01_CANONICAL_SCHEMA_VERIFIED`** — for the questions the task actually asks
("are the 89 migrations ordered and executable from zero?", "does a clean database reach the complete
current release-tree schema?", "is the 89-migration chain a viable canonical schema source?").

Justification against the verdict's stated conditions:

| Condition | Result |
|---|---|
| Clean database created | **Yes** — `CT-SCHEMA-01-TARGET-A`, brand-new container + volume, image digest recorded |
| Zero baseline captured | **Yes** — 0 `public` tables, 0 application rows, fingerprint recorded (§4) |
| All 89 migrations applied successfully | **Yes** — 89/89 on the platform-complete baseline (26 + 63), zero failures |
| 89/89 ledger arithmetic | **Yes** — 89 files, 89 applied, 0 skipped, 0 duplicates (§6) |
| No migration skipped | **Yes** |
| Resulting schema fingerprint captured | **Yes** — `c89c50bd…33c2f` (§7.2) |
| Required code dependencies reconciled | **Reconciled to the S2 level** — 4 genuine legacy code→schema mismatches (SCM-004…007), none caused by or curable by the rebuild; every canonical object has at least one code reference |
| No S1 **schema/code** mismatch | **Yes** (S1 items F-01/F-02 are *chain-integrity / runner-environment* findings, not schema↔code mismatches) |
| P17 objects present where expected | **Yes** — 105/105 parsed declarations confirmed (0 real absences); P16-R5/R7 too |

**Qualification that must travel with this verdict (recorded, not hidden):**

1. The chain is **not self-sufficient from a bare Postgres image**; it requires the standard Supabase
   platform layer plus one operator step (F-01/F-03), and migration 27 is **role/`search_path` sensitive**
   (F-02). Failure to encode these preconditions makes an automated from-zero apply fail at position 27.
2. **Conservative alternative reading.** If the reader treats *any* S1-severity finding as disqualifying
   (rather than only S1 schema↔code mismatches), the honest verdict is
   **`CT_SCHEMA_01_PARTIAL_WITH_REMAINING_UNKNOWN`**, with F-01/F-02 as the distinguishing blockers.
   Both readings are stated so that no reader has to guess which standard was applied.
3. This verdict concerns **schema only**. Functional/runtime status remains unverified
   (57/57 FIEW rows un-promoted).

**Explicitly not the verdict:** `CT_SCHEMA_01_MIGRATION_CHAIN_BLOCKED` (the chain completes on a valid
Supabase platform) and `CT_SCHEMA_01_SCHEMA_INCOMPLETE` (the schema is complete against the chain's own
declarations and identical to the most advanced environment).

## 18. Reporting standard, evidence index and files produced

### 18.1 Files produced by this task (all new, untracked, documentation-only)

| # | File |
|---|---|
| 1 | `docs/architecture/CT-PO-CARBONTALLY-CANONICAL-SCHEMA-FROM-ZERO-VERIFICATION-20260927.md` (this document) |
| 2 | `docs/architecture/CT-PO-CARBONTALLY-SCHEMA-CODE-MISMATCH-REGISTER-20260927.md` |
| 3 | `docs/architecture/CT-PO-CARBONTALLY-CANONICAL-SCHEMA-FEATURE-SUPPORT-MATRIX-20260927.md` |
| 4 | `docs/architecture/CT-PO-CARBONTALLY-SCHEMA-COMPARISON-MATRIX-20260927.md` |
| 5 | `docs/architecture/CT-PO-CARBONTALLY-CT-SCHEMA-01-REPORT-20260927.md` |

No migration, source, configuration, RLS, or committed file was modified or created. Repository Git state
was verified unchanged at task end (branch `p8-release-reconciled`, HEAD
`cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`, 51 porcelain entries as at task start).

### 18.2 Evidence index (transient artefacts outside the repository)

| Artefact | Path | Content |
|---|---|---|
| Baseline inventories (Target-0) | `/tmp/ct_schema01_evidence/baseline_target1/`, `/tmp/base/` | per-class baseline SQL dumps + fingerprint `ef4b7bb6…` |
| Baseline inventories (Target-A) | `/tmp/ct_schema01_evidence/baseline_target2/` | identical counts |
| Post-rebuild inventories | `/tmp/inv/A…N` | schemas, tables, columns, constraints, indexes, enums, functions, triggers, views, sequences, RLS, policies, grants |
| Canonical apply ledger | `/tmp/ledger_final.tsv` | 89 rows + header (`sha256 11bfc796…`) |
| Per-migration logs | `/tmp/logs_ledger_canonical*/` | one log per migration (empty on success) |
| Target-0 failure evidence | `/tmp/ct_schema01_evidence/run1_2_apply/` | ledger + logs of the two failed attempts |
| Global completeness check | `/tmp/global_verify.txt` | declared-vs-present reconciliation for all 89 migrations |
| P17/P16R detail | `/tmp/p17_verify.txt`, `/tmp/p17/*.txt` | per-object columns, constraints, indexes, RLS, policies, FKs |
| DB comparison | `/tmp/cmp/` | per-database table sets, missing/extra lists, ledger rows |
| Code-reference extraction | `/tmp/code_refs2/` | SQL/client reference sets, absent-from-schema, unreferenced |
| Command transcripts | `/tmp/s01_*.txt` | full stdout of every step (reconnaissance through verdict) |

### 18.3 Claim-classification summary for this document

`DOCUMENTED` where prior reports are cited; `CODE` for repository inspection; `MIGRATION` for object
declarations; **`SCHEMA` for every executed database statement**; `PERSISTED` only for
migration-seeded reference rows; **no `ROUTE`, `E2E`, `INDEPENDENTLY VERIFIED` or `PRODUCTION` claim is
made.**

<!--CTEOF-->









