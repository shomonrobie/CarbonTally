# CarbonTally — Production Backup Architecture Assessment (READ-ONLY)

**Prompt Ref:** `CT-PROD-BACKUP-ARCHITECTURE-20260911-001` · **Date:** 2026-09-11 · **Mode:** READ-ONLY architecture assessment
**Repository:** CarbonTally · branch `main` · **HEAD / Release-1:** `daad396523ac693352cc2f4ebb7fc58814a9e60b` (unchanged)
**Production:** `CarbonTally` · ref `pvwiojoyaqywtydzcpbg` · org `pfurlzwxdtvyljnahlnx` · **Supabase Free**
**Authorities used:** Blueprint V1.3 · Master Roadmap V1.0 · Deployment Readiness 20260911 ·
Supabase Reconciliation 20260911 · Migration Safety Plan 20260911 · **official Supabase documentation** (§3)

> **No component was implemented.** No backup was created, no dump was taken, no production data was
> accessed, no storage/credentials/keys were created, and nothing in production or the repository was
> modified beyond the two documentation artifacts.

---

## 1. Executive summary

**Feasible, with real decisions still open.** CarbonTally's current architecture is **well suited** to
hosting a backup capability:

* a **durable, DB-backed background worker pattern** (`document_processing_queue` +
  `FOR UPDATE SKIP LOCKED` claiming, state in PostgreSQL, resume on restart);
* an **existing server-side database credential path** (`DATABASE_URL` → `asyncpg` pool as the
  `postgres` role) plus a **service-role Supabase client** for the Storage/REST surface;
* an **append-only audit trail** with a decorator-based logger;
* **idempotent notification** support (`create_idempotent` + `event_key`);
* an **admin authorization dependency** (`require_admin()`, `ADMIN_ROLE_NAMES = ("admin","system_admin")`,
  `staff_roles.permissions` capabilities);
* an **already-configured retention setting — `backup_retention_days`** — exposed by
  `/api/v3/settings/retention`;
* a tabbed v3 admin UI with `SecurityTab`/`ActivityTab` ready to host backup controls and history.

Three findings materially shape the design:

1. **Supabase Free has no managed backups and no PITR.** Official docs place daily backups on
   Pro/Team/Enterprise only, and PITR is a Pro+ add-on — while Supabase **explicitly recommends that
   Free projects export via the CLI `db dump` and maintain off-site backups**. The PO's goal is exactly
   the vendor-recommended pattern for this tier.
2. **The documented CLI flow requires the Supabase CLI *and Docker*, a database password and a
   connection string** — while the repository has **no Dockerfile** and the backend runs on Render's
   **native** Python runtime, which cannot install OS packages. A `pg_dump`/CLI worker is therefore
   **not deployable to the current Render service as-is**: either the runtime becomes a container
   image, or a **pure-Python exporter over the existing `asyncpg` pool** is used.
3. **A database dump is not a complete recovery.** Supabase docs confirm database backups **do not
   include Storage objects** ("the database only includes metadata about these objects"), and role
   passwords are excluded. Storage objects and configuration/secrets need their own recovery story.

`UNKNOWN`s to close before implementation: whether Render's runtime can provide `pg_dump`; production
database size; and the off-site destination/key-custody provider.

**Verdict: `FEASIBLE — DESIGN REQUIRES DECISIONS`** (decision list in §25: D1–D5).

---

## 2. Repository architecture findings (`REPOSITORY VERIFIED`)

### 2.1 Backend

| Concern | Finding |
|---|---|
| Entrypoint | `backend/main.py` — FastAPI app; CORS from `Config.ALLOWED_ORIGINS`; lifespan starts/stops the worker |
| Router composition | `backend/api/router.py` mounts the `v3_*` surfaces plus `admin_aliases`, `admin_audit`, `admin_entities`, `admin_imports`, `admin_providers` |
| AuthN | Supabase Auth (GoTrue) JWTs validated server-side; `AuthUser` model in `backend/auth.py` |
| **AuthZ** | **`require_admin()` dependency** (`backend/auth.py:383`); `ADMIN_ROLE_NAMES = ("admin", "system_admin")`; `is_internal_staff` ⇒ `staff_profiles.entity_id IS NULL`; PE staff are explicitly denied internal admin authority; **capability dict from `staff_roles.permissions`** (e.g. `can_manage_billing`) |
| DB access | `backend/infra/supabase.py` is **the only** place that builds clients: `get_service_client()` (service-role REST, bypasses RLS) and **`get_service_pool()` — an `asyncpg` pool authenticated as the `postgres` role via `DATABASE_URL` (fallback `SUPABASE_DB_URL`)** |
| Repository layer | `backend/data/base.py` `AbstractRepository` (`_fetch_one`/`_fetch_all` over the pool); `backend/api/dependencies.py` `RepositoryBundle` |
| **Worker** | `backend/workers/automatic_processing.py` — lifespan-managed **asyncio** loop; claims jobs with **`FOR UPDATE SKIP LOCKED`**; **state in the database**; resumes after restart; a failed tick never kills the loop; `stop()` cancels the task |
| Audit | `backend/infra/audit_logger.py` (`AuditLogger.log_action`, `@audit` decorator, never raises); sink = `backend/data/audit.py` `AuditRepository` (`record`/`query`/`count`/`export_csv`/`get_by_correlation`) over the `audit_trail` table; `backend/api/audit_helpers.py` |
| Notifications | `backend/data/notifications.py` — `create`, **`create_idempotent`** (deterministic keys), `mark_read`, `list_for_user` |
| Domain events | `backend/infra/event_bus.py` (subscribe / publish / drain) |
| Errors | `backend/core/exceptions.py` — `CarbonTallyError` subclasses with declared HTTP status + machine code |
| Config / secrets | `backend/config.py` — `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`, `RESEND_API_KEY`, `FOUNDER_EMAIL`, CORS list. `DATABASE_URL` is read by `infra/supabase.py` |
| Settings (N3) | `backend/data/settings.py` + `backend/api/v3_settings.py` (`/api/v3/settings/retention`, `require_admin()`) already store **`audit_log_retention_days`, `data_retention_days`, `document_retention_days`, `backup_retention_days`**; unset ⇒ `None` ("Not configured") |
| **Subprocess / temp files** | **None in production code** (`subprocess`/`tempfile` appear only in `backend/_phaseA_selfcheck.py` and tests) → a dump worker would introduce the **first** command-execution surface in the platform |
| Existing backup code | **None** — the only `backup` reference is the `backup_retention_days` setting; `pg_dump` appears solely in test docs/comments |

### 2.2 Frontend / admin

`frontend/src/v3/admin/AdminPage.jsx` is a **tabbed** admin area — `Overview & Settings`, `Locations`,
`Facilities & Assets`, `Vehicles`, `Suppliers`, `Members & Invitations`, `Custom Factors`, `Activity`,
`Security`. A **Backups** tab fits this pattern directly, and `ActivityTab`/`SecurityTab` are the
natural homes for backup history and audit display.

### 2.3 Infrastructure

| Item | Finding |
|---|---|
| Backend runtime | Render, **native Python** runtime (`runtime.txt` = `python-3.11.9`); **no `render.yaml`, `Procfile`, `Dockerfile`, `build.sh` or `nixpacks.toml` anywhere in the repository** |
| Frontend | Vercel (`vercel.json`; no `buildCommand`/`outputDirectory`) |
| Database/Auth/Storage | Supabase, single production project |
| Worker topology | **No separate worker service** — the worker is **in-process** inside the FastAPI service |
| Filesystem | Render native services have **ephemeral disk**; **no persistent disk is declared in-repo** → whether one is configured in the Render dashboard is **`UNKNOWN`** |
| Encryption root key | Supabase docs note that Restore-to-a-new-project / Branching **copy the project encryption root key automatically**; a manual logical restore does not |
| OS tooling (`pg_dump`, `psql`, `supabase` CLI, `postgresql-client`) | **Not present in the repository and not expressible in `requirements.txt`.** The only DB clients in use are `asyncpg` and `supabase` (both Python) |


---

## 3. Supabase Free-tier feasibility

### 3.1 `SUPABASE DOCUMENTATION VERIFIED`

Source: `https://supabase.com/docs/guides/platform/backups` and
`https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore` (retrieved 2026-09-11).

| Fact | Documentation statement |
|---|---|
| Automatic backups by plan | "We automatically back up all **Pro, Team, and Enterprise** Plan projects on a daily basis." → **Free has NO automatic backups** |
| Retention by plan | Pro = **7 days**, Team = **14 days**, Enterprise = **up to 30 days** of daily backups |
| Free-tier official recommendation | "We recommend that **free tier plan projects regularly export their data using the Supabase CLI `db dump` command and maintain off-site backups**." ← **direct vendor endorsement of the PO's proposed capability** |
| PITR availability | "**Pro, Team and Enterprise Plan projects** can enable PITR as an add-on" + requires at least a **Small compute add-on** → **PITR is not available on Free** |
| PITR cost | 7 days ≈ **$100/month**, 14 days ≈ $200/month, 28 days ≈ $400/month |
| Storage objects in DB backups | "Database backups **do not include objects you store via the Storage API**, as the database only includes metadata about these objects. Restoring an old backup does not restore objects you deleted after that backup." |
| Role passwords | "For security purposes, daily backups **do not store passwords for custom roles**, and you will not find them in downloadable files" → passwords must be reset after a restore |
| Project deletion | "When you delete a project, we permanently remove all associated data, **including any backups stored in S3**. This action is irreversible" → another reason backups must live **off-site** |
| Restore downtime | During PITR restore "The project is **inaccessible** during this process"; downtime scales with database size; subscriptions/replication slots must be dropped first |
| Management API | `GET /v1/projects/{ref}/database/backups`, `POST …/restore-pitr` — **Pro+ backup surfaces** (not a Free-tier substitute) |

### 3.2 Authoritative CLI backup flow (`DOCUMENTATION VERIFIED`)

The documented procedure for a hosted project is exactly three artifacts:

```
supabase db dump --db-url [CONNECTION_STRING] -f roles.sql  --role-only
supabase db dump --db-url [CONNECTION_STRING] -f schema.sql
supabase db dump --db-url [CONNECTION_STRING] -f data.sql   --use-copy --data-only \
                                                    -x "storage.buckets_vectors" \
                                                    -x "storage.vector_indexes"
```

Documented prerequisites and constraints:

* **Install the Supabase CLI *and* Docker Desktop** (step 2 of the documented flow).
* **A connection string is required** — session pooler by default
  (`postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-<region>.pooler.supabase.com:5432/postgres`),
  or the direct host `db.[PROJECT-REF].supabase.com:5432`.
* **The database password is required** ("Get the database password… Reset the password in Database
  Settings"). A personal access token alone is **not** sufficient for `db dump --db-url`.
* **`psql`/Postgres client tools** are required for the restore side ("Install Postgres and psql").
* The `-x` exclusions in the documented data dump show that some schemas/tables are intentionally
  excluded and that the maintainer must choose scope deliberately.
* Storage objects are migrated by a **separate script/capability**, not by the dump (see §14).

### 3.3 Repository-side feasibility conclusions

| Question | Conclusion |
|---|---|
| Can `supabase db dump` work against a Free-tier project? | **YES** — it is the vendor-recommended Free-tier mechanism; it is a client-side logical dump and does not depend on plan features |
| Is the *documented* flow deployable to the **current** Render native runtime? | **NO, not as documented** — it needs the CLI **and Docker**, plus a DB password; the repository has **no Dockerfile** and native runtimes cannot install OS packages |
| Can `pg_dump` run on the current Render service? | **`UNKNOWN`** — `postgresql-client` is neither declared nor installable via `requirements.txt`; needs verification against the actual Render image (and would require a **container-based** service to guarantee it) |
| Is there any plan-feature dependency? | **None** for logical dumps. (Management-API backups and PITR are Pro+ and are **not** available.) |
| Alternative with **no new OS dependency** | **YES** — `asyncpg` (already in `requirements.txt` and already connected as the `postgres` role) can stream table data via PostgreSQL `COPY` (`copy_from_query`/`copy_from_table`) and read schema/roles via `pg_catalog` functions. This is the **only** option that is deployable to the current runtime without changing infrastructure (`REPOSITORY VERIFIED` that `asyncpg>=0.30.0` is a dependency). Trade-off: more code, and correctness risk versus a battle-tested `pg_dump`. |


---

## 4. Backup scope design

Proposed artifact set (aligned with the vendor-recommended three-file pattern):

```text
backup-<job_id>/
  manifest.json        required  (identity, scope, versions, sizes, timestamps, checksum, actor)
  schema.sql           required  (DDL for public + selected schemas)
  data.sql             required  (COPY-format row data, scope-controlled)
  roles.sql            optional  (role definitions; NOT passwords — see below)
  metadata.json        required  (release/migration/schema-version context)
  checksum.sha256      required  (integrity of the archive)
```

| Element | Requirement | Rationale |
|---|---|---|
| `manifest.json` | **required** | Only reliable way to know what a backup contains, when it was taken, by whom, and how to verify it |
| `schema.sql` | **required** | Without DDL the data dump is not restorable in a meaningful order |
| `data.sql` | **required** | The customer data; **the core recovery value** |
| `roles.sql` | **optional** | Recreates custom roles for a fresh project. Supabase **does not store custom-role passwords**; roles must be re-secured after restore |
| `metadata.json` | **required** | Release-1 commit id, migration state if available, Postgres version, schema fingerprint |
| `checksum.sha256` | **required** | Detects corruption/truncation; must cover the archive as a whole |

**Schema/topic guidance (do NOT dump production to discover it — repository + vendor docs only):**

| Area | Recommendation |
|---|---|
| `public` | **include** (schema + data) — the CarbonTally application schema (116 tables) |
| `auth` | **exclude data by default.** Supabase manages `auth`; identity rows are re-created by Supabase Auth. Restoring raw `auth` rows into another project is vendor-discouraged and risks credential/identity mismatch. **Never** include password hashes in an application-controlled artifact |
| `storage` | **only the metadata schema is meaningful**; the vendor flow explicitly excludes `storage.buckets_vectors`/`storage.vector_indexes`. Objects are handled separately (§14) |
| `extensions` | **do not dump extension internals**; instead record the required extension list in `metadata.json` and enable them on restore (as the vendor guide instructs) |
| `supabase_migrations` | **exclude data**; optionally record the version list in `metadata.json` (see §12) |
| Roles | include **definitions only** (`--role-only`); never passwords |
| Service configuration | manage via the console/`config.toml`; **not** part of the dump |
| Secrets / env / API keys | **never** in the dump — separate custody (§15) |
| Generated/system tables | exclude transient tables (e.g. queue/lock columns are fine as data, but avoid provider-internal tables) |
| `emission_factors` (7 049 rows) | **include** — it is platform reference data required for calculation |

**Dangerous to include:** anything containing credentials (password hashes, `auth` secrets, Vault
entries, provider keys). **Unnecessary:** extension internals, Supabase-managed schema data,
`storage.objects` binary content inside a SQL text dump.

---

## 5. Production credential architecture

| Option | Privileges | Blast radius | Rotation | Free-tier compatible | Complexity | Assessment |
|---|---|---|---|---|---|---|
| **A. Dedicated DB credential in backend secret storage** | whatever role it maps to (today `postgres`) | high if `postgres`; low if a restricted role | manual in Render dashboard | **yes** | low | Reuses the existing pattern (`DATABASE_URL` already lives in backend env) |
| **B. Dedicated restricted PostgreSQL role** (e.g. `ct_backup`, `LOGIN`, `SELECT` on target schemas + `pg_read_all_data`) | **read-only, narrow** | **lowest** — cannot write or drop | independent of app credentials | yes | medium (role must be created by an authorised operator) | **Best separation of duties** — a leaked backup credential cannot mutate production |
| **C. Supabase CLI authentication (access token + project link)** | management-plane token | **high** — an access token can operate the project, not just read it | must be rotated in the console | yes | medium, **but** the CLI needs Docker and is a broad credential | **Not recommended** for in-app automation |
| **D. Separate backup service** | its own credential | lowest blast radius for the app | independent | yes | **highest** (new deployable) | Justified only if the worker cannot live in the existing service |

**Recommendation:** **Option B inside a worker hosted by the CarbonTally backend (Option D only if the
runtime must diverge).** Concretely: create one dedicated **read-only** role for backups, store its
connection string as a **separate** secret (e.g. `BACKUP_DATABASE_URL`) that is **never** exposed to the
frontend, and prefer it over the `postgres` role the app currently uses. Do **not** put a Supabase
access token or the `service_role` key into the backup path — the worker needs **read-only SQL access
only** (the service-role key is required *only* if the same worker also exports Storage objects, and
even then it should be a separate, narrowly-scoped step — §14).

**Never**: expose `DATABASE_URL`, the DB password, the service key or any backup credential to the
browser; the admin UI must only ever see **job metadata**.


---

## 6. Worker architecture

**CarbonTally's existing worker is directly reusable.** `AutomaticProcessingWorker` already implements
every property a backup worker needs: lifespan-managed lifecycle, database-durable job state,
`FOR UPDATE SKIP LOCKED` claiming (safe concurrency), per-tick batch processing, resume-after-restart,
fault isolation ("a failed tick never stops the loop"), and graceful `stop()`.

**Recommended shape — a sibling worker, not a new service:**

* a new `BackupWorker` following the **same pattern**, started/stopped by the **same lifespan hook** in
  `backend/main.py`;
* job state in a **new `backup_jobs` table** (§10), claimed with the same `SKIP LOCKED` idiom;
* **no HTTP-only execution** — the request handler only creates/authorises the job and returns
  immediately (a dump may take minutes; the request must not block);
* **hard limits** on the subprocess/streaming step: timeout, size ceiling, output cap, and a single
  concurrent dump per process.

**Runtime constraint (decisive):** the *current* Render service is **native Python with no Dockerfile**,
while the vendor-documented dump needs the CLI **+ Docker**. Therefore the worker's execution mechanism
must be one of:

| Mechanism | Deployable to current Render service | Notes |
|---|---|---|
| `supabase db dump` (vendor flow) | **No** (needs CLI + Docker) | Best suited to an **operator runbook** on a workstation, using the DB password |
| `pg_dump` (postgresql-client) | **`UNKNOWN`, likely no** | Needs an OS package → requires a **container-based** Render service (new Dockerfile) |
| **`asyncpg` `COPY`-based exporter (pure Python)** | **Yes — no infrastructure change** | Reuses the existing pool/dependency; must reproduce schema/roles extraction with `pg_catalog`; higher implementation risk |

The choice between the last two is a **Product Owner decision** (§23, D1). Either way, the executed
command's argument list must be **fixed** (§21/§10 of the threat model) and never built from user input.

---

## 7. Backup destination (storage architecture)

| Criterion | External object storage (R2/S3/B2) | Separate Supabase project bucket | Local/ephemeral FS | Render persistent disk | Admin download only |
|---|---|---|---|---|---|
| Isolation from production failure | **high** | medium (same vendor/account) | none | none | high (but not automated) |
| Encryption control | full (client-side + SSE) | medium | full | full | full |
| Retention / expiry control | full (lifecycle rules) | medium | none | manual | manual |
| Access control | separate credentials/policies | Supabase keys | filesystem | filesystem | n/a |
| Durability | high (multi-AZ object storage) | high | **none (lost on restart)** | medium | n/a |
| Cost | low (DB is small) | low–medium | free | Render disk cost | free |
| Recovery availability | high | medium | **poor** | medium | depends on admin |
| Accidental exposure risk | low with private bucket + separate creds | medium | medium | medium | **high (a downloaded file is unprotected)** |

**Primary destination:** **a private bucket in an independent object-storage account** (Cloudflare R2 /
AWS S3 / Backblaze B2 class), with: server-side encryption on, public access **off**, dedicated
write-only-from-worker credentials, lifecycle expiry aligned to `backup_retention_days`, and
**versioning/object-lock** where available.

**Secondary/recovery destination:** an **encrypted archive downloaded by an authorised administrator**
for a portable copy (and/or a copy into a *second* Supabase project for restores within the Supabase
ecosystem). It is justified because a single off-site account is still a single failure domain.

**Explicitly rejected as a primary destination:** the production database itself, the local/ephemeral
filesystem, and any Render disk (a backup that shares the deployment's fate is not a backup).

---

## 8. Encryption design

| Layer | Design |
|---|---|
| In transit | TLS to the database (session pooler/direct, `sslmode=require`) **and** TLS to the object store. Enforced, not optional |
| At rest (storage) | destination **server-side encryption** enabled as a second layer |
| **Application-level encryption** | **YES — encrypt the archive *before* upload** (age/GPG or AES-256-GCM via a vetted library). The archive is a full copy of production data; it must be unreadable to anyone who obtains the object |
| Key location | a **secret manager / KMS distinct from the backup store** (e.g. Render secret + an independent key store). **The key must never be stored alongside the artifact**, never in the repository, never in the database, never in the manifest |
| Who can decrypt | only an explicitly authorised recovery operator, holding the key outside the platform |
| Rotation | keys carry an **id/version recorded in the manifest**; rotation creates a new key for new backups while old keys remain available for older artifacts (re-wrap or age-out per retention) |
| Key loss | **unrecoverable backups.** Therefore: documented key custody (at least two authorised holders / break-glass escrow), and a periodic **decrypt test** to prove keys still work |
| Manifest safety | the manifest may name the key **version**, never the key material |


---

## 9. Admin workflow (design only)

```text
Admin (require_admin + backup capability)
   ↓  POST /api/v3/admin/backups            (create job; returns job id + state)
Confirmation dialog  ("this creates a full copy of production data")
   ↓
Job row created (state = queued)  → idempotency key bound to actor
   ↓  worker claims FOR UPDATE SKIP LOCKED
running  → dump → compress → checksum → encrypt → upload → verify
   ↓
completed (or failed with a sanitised reason)
   ↓
manifest recorded in backup_jobs  → notification (idempotent) → audit entry
   ↓
Admin Backup History (list, status, size, checksum, created_by, expires_at)
   ↓
Download = short-lived signed URL for an AUTHORISED admin only (never a public URL)
```

| Aspect | Design |
|---|---|
| Authorization | `require_admin()` **plus** an explicit **`can_manage_backups` capability** (the permissions dict already exists on `staff_roles`); `system_admin` should hold it; ordinary reviewers/operators must not |
| Confirmation | explicit UI confirmation; API requires an explicit body/flag so a stray request cannot start a dump |
| Job creation | creates a **queued** row only; no work in the request path |
| Idempotency | `Idempotency-Key` header (or a single-flight constraint) — see §11 |
| Concurrency | at most **one** running backup at a time (§11) |
| States | `queued → running → completed` / `failed` / `expired` / `deleted` |
| Retention | `expires_at` derived from the existing `backup_retention_days` setting |
| Audit | one entry per actor action (§17) |
| Notification | reuse `notifications.create_idempotent` on completion/failure (**note:** `event_key` arrives with pending migration 45) |
| Download | server-mediated, authorised, short-lived signed URL; **never** a permanent public URL, never logged |

---

## 10. Backup job model

**A new durable table is appropriate** (the existing worker pattern proves the value of DB-held job
state; nothing in the current schema models a backup). Proposed (not created):

```text
backup_jobs
  id                  uuid primary key
  status              text  -- queued|running|completed|failed|expired|deleted
  scope               text  -- e.g. 'public+schema+roles' (fixed vocabulary, not free-form)
  requested_by        uuid  -- actor (FK users)
  requested_at        timestamptz
  started_at          timestamptz
  finished_at         timestamptz
  attempt_count       int  default 0
  lock_token          text            -- SKIP LOCKED claim token
  locked_at           timestamptz
  storage_key         text            -- object key in the off-site store
  storage_bucket      text
  artifact_bytes      bigint
  checksum_sha256     text
  key_version         text            -- encryption key id (NEVER the key)
  manifest            jsonb           -- release commit, pg version, table counts, scope
  release_commit      text            -- daad396… at creation
  error_reason        text            -- sanitised, no secrets
  expires_at          timestamptz     -- from backup_retention_days
  deleted_at          timestamptz
  deleted_by          uuid
```

State machine: `queued → running → completed`; `running → failed`; `completed → expired → deleted`;
`failed → queued` (retry, bounded by `attempt_count`). **RLS:** internal-admin only; never
organisation-scoped; no `anon` access. Ownership/audit fields mirror the existing
`attempt_count`/`lock_token`/`last_error` convention from `document_processing_queue`.

---

## 11. Idempotency and concurrency

| Risk | Protection |
|---|---|
| Two admins start simultaneously | **single-flight**: a partial unique index on `(status)` where `status in ('queued','running')`, or an advisory lock; the second request receives the existing job id |
| Repeated clicks / double submit | client-side disable **plus** server-side `Idempotency-Key` → same job returned |
| Browser/network retries | the idempotency key is honoured for a bounded window; identical key ⇒ identical job |
| Worker retries | deterministic job id; attempt counter; only `failed` jobs are re-claimable; **stage markers** (as in the existing pipeline) prevent double upload for the same job |
| Partial backup files | write to a **temp path keyed by job id**; only promote/upload after **checksum verification succeeds**; partials are deleted on failure/timeout |
| Duplicate records | one row per job id (PK); no "one row per attempt" |
| Stale jobs | `locked_at` age > threshold ⇒ claim released and attempt incremented (same recovery idiom as the existing worker) |
| Interrupted processes | state is in the DB, so a restarted worker resumes or fails the job; temp files are garbage-collected on startup |

---

## 12. Backup integrity

* **SHA-256 checksum** of the final archive, **recomputed after upload** (compare against the local
  value) and **stored in the manifest and `backup_jobs`**.
* **Archive integrity**: the encryption tool's own integrity check (AEAD tag / GPG signature) plus a
  successful decrypt-and-list test on a sampled basis.
* **Expected file set**: manifest lists exactly the files present; the worker fails if any is missing.
* **Size sanity**: non-zero, within a configured ceiling, and within an expected band of the previous
  successful backup (a large deviation is a warning, not a silent success).
* **Metadata captured per backup**: `id`, `created_at`, `actor`, `scope`, `release_commit`,
  Postgres server version, table/row counts (or a schema fingerprint), **migration state if safely
  available** (currently `UNKNOWN`), key version, bytes, checksum, storage key, destination.


---

## 13. Restore architecture

**Restore is materially more dangerous than backup and must be designed separately.**

### Preferred strategy — restore into a **disposable/recovery project first** (never production first)

```text
encrypted off-site archive
   ↓ decrypt (key held outside the platform)
   ↓ create a NEW disposable Supabase project
   ↓ roles.sql (re-secure roles — passwords are NOT in the dump)
   ↓ schema.sql
   ↓ data.sql
   ↓ enable required extensions + Database Webhooks (vendor guidance)
   ↓ verify schema → verify data → verify RLS → verify application startup
   ↓ verify critical workflows (auth, provisioning, one processing path)
   ↓ ONLY THEN consider production restoration (separate, exceptional authorisation)
```

Why **direct production restore should be exceptional**: it replaces live data (a wrong target or a
stale archive destroys newer data); RLS must be re-verified before any customer traffic; the vendor
restore path makes the project **inaccessible during the operation**; and the vendor notes that
**subscriptions/replication slots must be dropped first**. A database restore is an irreversible,
downtime-bearing, all-or-nothing action — so it needs a **stronger capability than backup**, a written
checklist, two-person approval, and a readiness snapshot taken immediately before.

Repository hooks that support a safe restore: the append-only **audit trail**, the **idempotent
notification** system, and the existing **negative isolation matrix** (from the P6-2F/security work) as
the post-restore security test.

---

## 14. Storage-object backup (explicitly separate)

* **A database dump does NOT contain Storage objects** — `DOCUMENTATION VERIFIED` ("the database only
  includes metadata about these objects"). CarbonTally stores customer source documents in the private
  `documents` bucket, so a DB-only backup would restore document **metadata pointing at missing files**.
* **Objects must be exported separately** — e.g. enumerate buckets/objects and copy each object to the
  off-site store (the vendor guide does exactly this with a **separate script** using service keys), or
  mirror objects into a second project's bucket.
* **Metadata is included** in the DB dump (the `storage` schema rows), so a restore needs **both**
  artifacts to be mutually consistent.
* **Should it be the same job?** **No — separate jobs**, but **sequenced** and paired by a common
  *backup-set* id so a restore can select a consistent pair. Object copies are much larger and slower;
  coupling them would make a DB backup fail because of one large file.
* **First-customer relevance:** the `documents` bucket **does not currently exist** in production
  (`DR-08`) and there are no customer documents yet — so object backup is **not blocking today**, but
  becomes **P1 the moment the first real document is uploaded**.
* No object was listed, read or downloaded by this assessment.

---

## 15. Secrets / configuration recovery

A rebuild of production requires more than data. **Never** place any of the following in the database
dump:

| Item | Current location (`REPOSITORY VERIFIED`) | Recovery recommendation |
|---|---|---|
| Supabase URL / publishable key | frontend build env + source fallback | documented config inventory (non-secret) |
| **`SUPABASE_SERVICE_KEY`** | Render env (secret) | secret-manager backup, **out-of-band** from the DB dump |
| `SUPABASE_JWT_SECRET`, DB password | Render env | secret manager; rotate after a rebuild |
| `RESEND_API_KEY`, `FOUNDER_EMAIL` | Render env | secret manager |
| `CARBONTALLY_AI_*` | Render env (optional, fail-closed) | secret manager |
| CORS allow-list | `backend/config.py` (in code) | already in Git |
| OAuth (Google) / Auth settings / SMTP / redirect URLs | **Supabase console** | documented console inventory (not in Git) |
| Storage bucket definitions/policies | migration `d32` (in Git) + console | Git + console runbook |
| **Encryption root key** (column encryption / Vault) | Supabase-managed | vendor: *Restore-to-a-new-project* / *Branching* copy it automatically; a **manual** restore does not — handle explicitly |
| **Backup encryption keys** | must live in a key store **separate** from the backups (§8) | escrow + rotation procedure |

Recommended: a **sealed configuration runbook** (names + locations + rotation owner, **no values** in
Git) plus a secrets manager as the source of truth, proven by a periodic "can we rebuild from
scratch?" exercise.


---

## 16. Retention policy (initial proposal)

| Class | Frequency | Retention | Notes |
|---|---|---|---|
| **Manual emergency backup** | on demand (admin) | 30 days default | the **first** capability to build; driven by the existing `backup_retention_days` setting |
| Daily logical backup | daily (future automation) | **7 days** | matches Supabase Pro's baseline retention and keeps storage small |
| Weekly logical backup | weekly (future) | **4–8 weeks** | protects against slow-onset corruption noticed late (a dump-only strategy has no PITR) |
| **Pre-migration / pre-restore snapshot** | at each migration or restore | ≥ 30 days + the change window | **directly required by the migration safety plan** (§20) |
| Object (Storage) backup | paired with the DB backup | aligned to the DB class | becomes relevant once documents exist |
| Expiry | automatic via `expires_at` + store lifecycle rules | — | deletion must remove the object **and** clear the job's storage reference |
| Deletion authorisation | `can_manage_backups` + audit entry | — | a deleted backup is unrecoverable — require confirmation |
| Legal / privacy | retention must not destroy required auditability; a backup containing personal data is itself personal data | — | aligns with N3 (retention configurable, never invented) — **PO decision** |

Do **not** implement scheduling yet; the design must merely *support* it (the `backup_jobs` model does).

---

## 17. Audit / security events

Every actor and system action is recorded through the existing append-only audit trail
(`AuditLogger`/`AuditRepository`), and **the audit record must never contain** credentials, backup
contents, storage keys that grant access, or key material.

| Event | Recorded fields (no secrets) |
|---|---|
| Backup requested | actor, timestamp, scope, source IP/correlation id, job id |
| Backup started | job id, worker identity, attempt number |
| Backup succeeded | job id, bytes, checksum, storage key **reference**, duration, scope |
| Backup failed | job id, sanitised reason, attempt number (**never** raw stderr with credentials) |
| Backup downloaded | actor, job id, timestamp, signed-URL issue (not the URL itself) |
| Backup deleted | actor, job id, timestamp, reason |
| Restore requested / approved / completed | actor, job id/archive id, target environment, approvals, timestamps |

Notifications to internal staff on completion/failure reuse `notifications.create_idempotent` so a
worker retry cannot duplicate a notification. (**Dependency:** `event_key` arrives with pending
migration 45 — see §20.)

---

## 18. Threat model

| # | Threat | Mitigation | Residual risk | Monitoring |
|---|---|---|---|---|
| 1 | **Compromised admin account** | `require_admin` + explicit `can_manage_backups`; download requires re-auth; alert on unusual backup frequency | medium (a compromised admin can still exfiltrate a backup) | alert on every backup/download by a non-routine actor |
| 2 | **IDOR against backup ids** | server-side ownership/authorisation checks on **every** backup endpoint (`/backups/{id}`); UUIDs not trusted; RLS internal-admin only | low | 403/404 spikes |
| 3 | **Unauthorised download** | signed URLs are short-lived and issued only after authorisation; audit every download | low–medium (a signed URL is a bearer token if leaked) | log issue/use; never log the URL |
| 4 | **Backup URL leakage** | never place URLs in logs, notifications, or the manifest; short TTL | low | log review |
| 5 | **Backup storage misconfiguration** | private bucket, public access disabled, separate least-privilege credentials, periodic access audit | medium if misconfigured | storage access logs / bucket policy drift check |
| 6 | **Leaked encryption key** | key stored separately from artifacts; rotation with key-version in manifest; escrow with two holders | low–medium | key-access audit; rotation log |
| 7 | **Worker compromise** | minimal fixed command; read-only DB credential; no shell; least-privilege outbound credentials | medium | anomalous process/network alerts |
| 8 | **Command injection** | **no user input reaches the command** — fixed binary and fixed flags; scope from a closed vocabulary (§21) | **low** if enforced | code review + unit test asserting fixed argv |
| 9 | **Malicious filename / path** | filenames are **generated** from the job id; no user-supplied names/paths | low | review |
| 10 | **Arbitrary CLI argument injection** | allow-list only; unknown/extra options rejected; no `shell=True` | low | review + test |
| 11 | **Accidental production restore** | restore requires a **separate, stronger** capability + confirmation + two-person approval; default target is a disposable project | low–medium | audit + approval records |
| 12 | **Retention failure** | `expires_at` + store lifecycle rules + a sweeper job; alert when expiry does not occur | low | expiry monitoring |
| 13 | **Incomplete cleanup** | temp files keyed by job id; deleted on success **and** failure; startup sweep; disk-usage guard | low | disk/space alerts |
| 14 | **Backup corruption** | checksum before **and** after upload; periodic decrypt test; size sanity band | low | checksum mismatch alerts |
| 15 | **Stale backup** | "last successful backup age" metric; alert if it exceeds the retention cadence | low | age alert |
| 16 | **Insider access** | least privilege; audit trail; separation of duties (backup vs restore); no shared credentials | medium (insider risk is never fully removable) | audit review |
| 17 | **Dump leaks into the production DB** | backups never stored in the production database or its storage | low | schema/repo review |


---

## 19. Command-execution security (critical)

If the implementation invokes `pg_dump` / `supabase db dump`, the following is **mandatory**:

* **No user input in argv.** The command is a **fixed array** — e.g. (illustrative, fixed literals only):
  `["pg_dump", "--no-owner", "--no-privileges", "--format=plain", "--file=<generated path>", <connection-from-secret>]`
  — never a shell string, **never `shell=True`**, never a filename, scope or option supplied by the browser.
* **Allow-listed options only**; unknown/extra flags are rejected by the worker before execution.
* **Fixed environment**: an explicit minimal `env` (only the one connection string), `PATH` pinned.
* **Sanitised target**: project ref/host are configuration, never request data.
* **Timeouts and limits**: wall-clock timeout, max output size, max artifact size, disk-space guard.
* **stdout/stderr** captured to a bounded buffer and **sanitised** before reaching a log, an API
  response or the audit trail (dumps can echo connection details).
* **Exit-code validation**: non-zero ⇒ job fails with a sanitised reason; **no partial artifact is promoted**.
* **Cleanup**: temp files removed on every exit path; a startup sweep removes orphans.
* **Alternative advantage**: the pure-Python `asyncpg` `COPY` exporter avoids `argv` risk entirely by
  issuing **parameterised SQL** from a fixed statement template — worth weighing against its higher
  implementation risk.

---

## 20. Relationship to migration safety (`DR-20`)

The migration safety plan authorises **nothing** and records that migrations **22 → 53 are forward-only
with no rollback path** while backup/PITR remained `UNKNOWN` (`DR-20`).

**Exact prerequisite before migrations 22 → 53 may be authorized:**

> A **verified, restorable backup of the pre-migration production database** must exist **off-site**,
> with: (a) a completed logical dump of the `public` schema + data (+ role definitions); (b) a recorded
> **SHA-256 checksum** and manifest; (c) **encryption at rest** with the key held outside the artifact;
> and (d) **a proven restore** of that archive into a **disposable project** — recovering schema, data
> and RLS — **before** any migration touches production.

This is the minimum that converts an unrecoverable forward-only delta into a recoverable change. **A
dump that has never been restored does not satisfy it** — the restore drill is the evidence. Free-tier
managed backups cannot satisfy it (no daily backups, no PITR), so the capability must be
CarbonTally-managed — exactly the architecture in this report.

---

## 21. Cost and operational feasibility (qualitative — no invented numbers)

| Factor | Assessment |
|---|---|
| Backup frequency | manual initially; daily/weekly later (`backup_retention_days` already configurable) |
| **Production database size** | **`UNKNOWN`** — not measured; measuring it safely needs read-only DB access, which is unavailable, and **no mutation-capable method was used** |
| Storage growth | bounded by size × retained copies; a small database plus the 7 049-row factor library is expected to be modest — **but this must not be relied on until size is measured** |
| Compute cost | the dump runs inside the existing service (or one small container) for minutes, not continuously |
| Bandwidth | one full copy per backup plus one upload — bounded by DB size |
| Operational complexity | **medium** — new worker, new table, off-site credentials, key custody, restore runbook |
| Free-tier compatibility | **high** — logical dumps are explicitly the vendor-recommended Free-tier path |

---

## 22. Implementation phases (bounded — none implemented)

**Backup Phase 1 — backend backup job + secure artifact.** Read-only backup credential; `backup_jobs`
table; `BackupWorker` (existing pattern); fixed command or `asyncpg` COPY exporter; ephemeral temp
handling; checksum; **client-side encryption**; upload to the primary off-site store; manifest;
sanitised audit entries. **No UI.**

**Backup Phase 2 — admin UI, history, notifications.** A **Backups** tab in `frontend/src/v3/admin`
(history, status, size, checksum, actor, expiry); create-backup action with confirmation and
`can_manage_backups`; authorised short-lived download; idempotent completion/failure notifications.

**Backup Phase 3 — restore-to-disposable-environment verification.** A documented, strongly-authorised
restore into a **new disposable project** with post-restore schema/data/RLS/startup/workflow
verification, recorded as evidence. **No production restore path in the UI.**

**Backup Phase 4 — scheduling and retention automation.** Scheduled daily/weekly backups, lifecycle
expiry driven by `backup_retention_days`, stale-backup alerting, periodic decrypt/restore rehearsal.

**Explicitly out of scope** (avoid over-engineering): PITR (paid plan), enterprise KMS, a separate
backup microservice unless the runtime decision forces it, and any production one-click restore.


---

## 23A. First-customer readiness impact

| Item | Classification | Rationale |
|---|---|---|
| **Pre-migration backup + proven restore drill** | **P0 — before migrations 22 → 53** | the delta is forward-only with no rollback; this *is* `DR-20` |
| Manual admin-initiated logical backup (Phase 1–2) | **P1 — before first customer** | cheap, vendor-recommended, materially reduces the "no recovery" gap |
| Restore-to-disposable verification (Phase 3) | **P1 — before first customer** | an unrestored backup is unproven; one drill suffices to start |
| Off-site storage + encryption + key custody | **P1 — before first customer** | a backup on the production host, or unencrypted, is not credible |
| Storage-object backup | **P2 controlled workaround → P1 once documents exist** | the `documents` bucket does not exist yet and there is no customer data |
| Scheduled daily/weekly automation (Phase 4) | **post-launch** | manual + pre-migration snapshots suffice for the first customer |
| PITR / paid-plan backups | **post-launch (business decision)** | ≈$100/month for 7-day PITR; not required to open |
| Configuration/secrets recovery runbook | **P1 (documentation only)** | cheap and directly reduces rebuild risk |

**Recommendation:** implement **Phase 1 + Phase 2 + one Phase 3 drill** before the first customer, and
treat **pre-migration backup + proven restore** as a **P0 gate** on the migration operation. A credible
recovery mechanism — not enterprise infrastructure.

---

## 23B. Relationship to DR-16 and DR-19 (kept separate, not fixed)

| Finding | Interaction with backups | Action |
|---|---|---|
| **DR-16** — anonymous readability of `emission_factors` | A backup copies those 7 049 reference rows like any other data; the exposure itself is **not** a backup problem. It does mean part of the dumped data is already public — relevant only to how sensitive the artifact is judged. | **Not fixed.** Investigate separately (console / read-only DB) per the migration safety plan |
| **DR-19** — repeated same-month D6 billing uniqueness failure | A backup faithfully captures whatever `usage_tracking` state exists; backups neither cause nor cure it. Restoring an old backup could *reintroduce* stale usage rows — another reason restores target a disposable project first. | **Not fixed.** Separate code-path decision |

Neither finding changes the backup architecture, and the backup architecture does not expand into them.


---

## 24. Final architecture

```text
                    CarbonTally Admin UI  (frontend/src/v3/admin — new "Backups" tab)
                              │
                              │ authenticated request  (require_admin + can_manage_backups)
                              ▼
                    CarbonTally FastAPI   (POST /api/v3/admin/backups → job id)
                              │
                              │ creates a queued row in `backup_jobs` (no work in the request path)
                              ▼
                    Backup Worker   (lifespan-managed asyncio; same pattern as
                              │      AutomaticProcessingWorker; FOR UPDATE SKIP LOCKED)
                              │
                              ├── READ-ONLY backup DB role (separate secret; never in the browser)
                              │      fixed command (pg_dump)  OR  parameterised asyncpg COPY exporter
                              │
                              ├── encrypted temporary artifact (job-scoped temp path; deleted on all paths)
                              │      dump → compress → SHA-256 → encrypt (manifest records only the key id)
                              │
                              ▼
                    Off-site Backup Storage  (private bucket; SSE; lifecycle expiry; versioning)
                              │
                              └── manifest + checksum + metadata
                                        │
                                        ▼
                     `backup_jobs` metadata  +  audit_trail  +  idempotent notification
                                        │
                                        ▼
                     Admin Backup History  →  authorised short-lived download URL
```

### Trust boundaries, credentials and boundaries (explicit)

| Boundary | Definition |
|---|---|
| **Browser ↔ API** | The browser is **untrusted** and receives **only** job metadata. It never sees a connection string, DB password, service key, storage credential, or dump. Authorization is server-side (`require_admin()` + `can_manage_backups`). |
| **API ↔ worker** | Same process today; the worker holds the **read-only DB credential** and the **destination write credential**, neither of which the request path needs. |
| **Worker ↔ database** | Outbound TLS only, **read-only** role — a backup job can never mutate production. |
| **Worker ↔ object store** | Outbound TLS only, **write-scoped** credential for a **private** bucket. |
| **Credentials** | (1) read-only DB secret (`BACKUP_DATABASE_URL`); (2) destination write credential; (3) backup **encryption key** in a separate store; (4) service-role key **only** if Storage objects are exported, as a separate narrowly-scoped step. **None** reaches the browser or a log. |
| **Encryption boundary** | Encryption happens **inside the worker, before upload**; the store holds only ciphertext; the key lives in a separate key store; the manifest records only a **key version**. |
| **Storage boundary** | A **private** bucket in an **independent** account, distinct from production Supabase; lifecycle expiry; no public access; separate credentials. |
| **Audit boundary** | Every actor and system action is written to the append-only `audit_trail`; records hold identifiers and metadata, **never** credentials, dump content or key material. |
| **Restore boundary** | Strictly **outside** the normal admin surface: stronger authorization, two-person approval, target = **disposable project first**; production restore is exceptional and documented. The UI offers **no** one-click production restore. |


---

## 25. Required decision (§29)

**Q1 — Is CarbonTally's current architecture capable of safely hosting the backup worker?**
**YES.** The existing lifespan-managed, DB-durable, `SKIP LOCKED` worker pattern; the existing
server-side DB credential path (`DATABASE_URL` → `asyncpg`); the append-only audit trail; the idempotent
notification system; the `require_admin()`/capability authorization model; and the existing
`backup_retention_days` setting together provide every primitive needed. **Caveat:** the *dump
mechanism* cannot be the vendor's **Docker-based CLI** on the current native Render runtime (§3.3, §6).

**Q2 — Can Supabase Free support the proposed logical-backup mechanism?**
**YES — and it is the vendor's own recommendation for this tier.** `DOCUMENTATION VERIFIED`: Free has
**no** automatic backups and **no** PITR available, and Supabase recommends Free projects "regularly
export their data using the Supabase CLI `db dump` command and maintain off-site backups".

**Q3 — What exact credentials are required?**
(1) A **read-only PostgreSQL credential** (a dedicated role is preferred; today's `postgres` role would
work but is over-privileged) — required by every mechanism. (2) For the vendor CLI path only: the
**database password** + a **connection string** (session pooler or direct), *plus* the CLI **and
Docker**. (3) A **destination write credential** for the off-site bucket. (4) A **backup encryption key**
held outside the artifact. (5) A **service-role key only** if Storage objects are exported. A Supabase
**personal access token is not required** for a logical dump and should **not** be used.

**Q4 — Where should backup execution occur?**
**Entirely server-side, inside CarbonTally's trusted backend/worker** — never in the browser, and never
an admin workstation as the *primary* mechanism (that remains a documented fallback runbook). Whether
the service must become container-based depends on decision **D1** below.

**Q5 — Where should encrypted backups be stored?**
**Primary:** a private bucket in an **independent object-storage account**, encrypted client-side before
upload, with lifecycle expiry. **Secondary:** an encrypted archive **downloaded by an authorised
administrator** (and/or mirrored into a second Supabase project for in-ecosystem restores). **Never** on
production, its ephemeral disk, or a Render disk.

**Q6 — Should database and Storage-object backups be separate?**
**YES.** `DOCUMENTATION VERIFIED` that database backups **exclude** Storage objects. They should be
**separate jobs** paired by a common *backup-set* id, because object copies are far larger/slower and
must not be able to fail a database backup.

**Q7 — What should be included/excluded from the database backup?**
**Include:** `public` schema + data; role **definitions** (no passwords); the required-extension list;
backup metadata; the `emission_factors` reference data. **Exclude:** `auth` data (Supabase-managed —
password hashes must never appear in our artifact), extension internals, `supabase_migrations` data,
Storage **objects** (separate job), provider internals, and **all secrets/env/keys**.

**Q8 — What is the safest restore strategy?**
**Restore into a disposable/new recovery project first**, then verify **schema → data → RLS →
application startup → critical workflows**; only then consider production restoration as a separate,
strongly-authorised, two-person operation. Direct production restore is exceptional because it destroys
newer data, requires re-verifying authorization, and the vendor path makes the project inaccessible
during the restore.

**Q9 — What minimum backup/recovery capability is required before migrations 22 → 53?**
A **verified, off-site, encrypted, checksummed logical dump of pre-migration production** whose
**restore into a disposable project has been proven** to recover schema, data and RLS (§20). A dump that
has never been restored does **not** satisfy it, and Free-tier managed backups cannot satisfy it.


**Q10 — What should be implemented before first customer?**
**Phase 1 (backend backup job + encrypted off-site artifact)**, **Phase 2 (admin Backups tab, history,
authorised download, notifications)** and **one Phase 3 restore drill** into a disposable project; plus
the **configuration/secrets recovery runbook** (documentation). Storage-object backup becomes P1 only
once real documents exist.

**Q11 — What can safely wait until after first customer?**
Scheduled daily/weekly automation (Phase 4); lifecycle/expiry automation beyond the setting; storage-
object backup while the bucket is empty; PITR or paid-plan backups (a business decision ≈ $100/month);
secondary-destination mirroring; enterprise KMS; any production one-click restore.

**Q12 — Is the architecture ready for a separate implementation prompt?**
**Not yet — four decisions are open (D1–D4).** Once they are ratified, a **bounded Phase-1
implementation prompt** can be issued.

### Decisions required before a bounded implementation prompt

| # | Decision | Options | Why it matters |
|---|---|---|---|
| **D1** | **Dump mechanism vs runtime** | (a) keep the native Render runtime and implement a **pure-Python `asyncpg` COPY exporter**; (b) move the worker to a **container-based** Render service with `postgresql-client` and use **`pg_dump`**; (c) keep the vendor CLI **+ Docker** as an operator playbook only and build no in-app automation yet | Determines feasibility, cost, code risk, and whether a Dockerfile is introduced (the repo has none) |
| **D2** | **Off-site destination provider + retention** | R2 / S3 / B2 / other; retention class (7 / 30 / 90 days) | Determines credentials, lifecycle rules, cost and recovery latency |
| **D3** | **Encryption tool + key custody** | `age` / GPG / AES-256-GCM library; where the key lives; who holds it; escrow + rotation | A lost key means lost backups; the key must never sit beside the artifact |
| **D4** | **Restore authorization model** | who may approve a restore; two-person rule; disposable-project-only vs production restore path | Restores are the dangerous half of the capability (§13) |

Optional but recommended: **D5** — a dedicated **read-only `ct_backup` DB role** rather than reusing the
`postgres` superuser role the app currently connects with.

---

## 26. Mandatory no-change confirmation

```text
Repository source modified: NO
Tests modified: NO
Migrations modified: NO
Git commit created: NO
Git push performed: NO
Production database altered: NO
Production database dumped: NO
Production data accessed for backup: NO
Production data created: NO
Production storage modified: NO
Production users created: NO
Production organisations created: NO
Production subscriptions created: NO
Production RLS modified: NO
Production Auth modified: NO
Production deployment performed: NO
Production backup created: NO
Production backup downloaded: NO
Production backup storage created: NO
Secrets changed: NO
Encryption keys created/changed: NO
```

*Only two documentation files were written. No backup, dump, storage object, credential, key, bucket,
table or configuration was created or changed; no production data was read; no migration was applied.*

---

## FINAL VERDICT

## `FEASIBLE — DESIGN REQUIRES DECISIONS`

An in-app, administrator-initiated logical backup for the CarbonTally production database on Supabase
**Free is feasible and is exactly what Supabase recommends for this tier**, and the existing
architecture already provides almost every primitive needed (durable worker, server-side DB credential,
audit trail, idempotent notifications, admin capability model, `backup_retention_days`). The design
cannot yet be handed to a bounded implementation prompt because **four decisions remain open** (D1 dump
mechanism vs Render runtime; D2 destination/retention; D3 encryption tool and key custody; D4 restore
authorization). Also recorded: a database dump alone is **not** a complete disaster-recovery backup —
**Storage objects and configuration/secrets must be handled separately**, and the **pre-migration
backup + proven restore drill is the P0 prerequisite** for the pending migrations 22 → 53.


---
---

# PART 2 — Product Owner Ratified Architecture Decisions

**Prompt Ref:** `CT-PROD-BACKUP-DECISIONS-20260911-002` · **Date:** 2026-09-11 · **Mode:** READ-ONLY (verification + durable recording)
**Supersedes:** the *decision status* in Part 1 §23/§25 (which recorded D1–D5 as open). **Part 1 is preserved
in full above and is not rewritten or deleted** — its analysis, findings and evidence stand unchanged.

**Release-1 / HEAD:** `daad396523ac693352cc2f4ebb7fc58814a9e60b` (unchanged) · 53 tracked migrations, 17 added by Release-1 · staged 0

---

## P2.1 Ratified decisions (recorded verbatim in intent)

| ID | Ratified decision | Status |
|---|---|---|
| **D1** | **Pure-Python `asyncpg` PostgreSQL exporter** using the existing server-side worker architecture. The in-app mechanism must **not** require Docker, a new container runtime, Supabase CLI execution inside Render, or `pg_dump` subprocess execution from the application. **Render native Python remains the deployment model.** Supabase CLI/`pg_dump` may remain a **documented operator/manual recovery fallback** only. | **RATIFIED** |
| **D2** | **Independent off-site private object storage** as the backup destination (private, encrypted, lifecycle/retention, restricted access, **no public URLs**, separated from the production database, survives production Supabase failure). | **RATIFIED** |
| **D3** | **Application-level encryption before off-site storage.** Key never in the database, never beside the artifact, never in the browser; stored in separate custody; documented rotation/recovery. | **RATIFIED** |
| **D4** | **Restore is a separate high-risk capability.** Backup: authorised admin + explicit confirmation + asynchronous + audited. Restore: separate operation, stronger authorization, explicit confirmation, **preferably two-person for production**, default target = **disposable/recovery environment**, production restore = exceptional. | **RATIFIED** |
| **D5** | **Dedicated restricted `ct_backup` role** (minimum privileges; no broad admin, write, schema-modification, RLS-modification or user-management privileges) — **if technically supported**; otherwise document the limitation and propose the smallest safe alternative. | **RATIFIED** |

`DO NOT REINTERPRET` was observed: **D1–D5 were not reopened.** No architectural contradiction was found
that requires a decision to be revisited (one **technical limitation** under D5 is documented in P2.3, and
**D5 itself delegates** the fallback — so it is recorded as a limitation + smallest safe alternative, not
as a reopened decision).


---

## P2.2 Verification findings — D1 (`REPOSITORY VERIFIED`)

**Verdict: D1 is fully compatible with the existing architecture. No Docker, no container, no CLI and no
`pg_dump` subprocess is required.**

| Check | Finding |
|---|---|
| Read-side COPY capability | **`asyncpg 0.30.0` is installed** and exposes **`copy_from_table()`** (line 797), **`copy_from_query()`** (line 869), plus `copy_to_table()`/`copy_records_to_table()` — a pure-Python exporter can stream table data via PostgreSQL `COPY … TO STDOUT` with **no external binary** |
| Existing connection path | `backend/infra/supabase.py::get_service_pool()` already provides the process-wide `asyncpg` pool used by every repository — the exporter can reuse it (or a dedicated pool for the ratified role, D5) |
| Worker lifecycle | `backend/workers/automatic_processing.py` — lifespan-managed asyncio loop, `FOR UPDATE SKIP LOCKED` claiming, DB-held state, resume-after-restart, fault-isolated ticks. **A `BackupWorker` can be a direct sibling** with no new runtime |
| Subprocess usage in production code | **NONE.** `subprocess` appears only in `backend/_phaseA_selfcheck.py` (a dev self-check script). No production module shells out |
| Temp-file usage in production code | **NONE** — the exporter introduces the first temp-file handling; Part 1 §19 already specifies the guardrails |
| Render runtime | `runtime.txt` = `python-3.11.9`, native buildpack, **no Dockerfile** — unchanged by D1 (D1 deliberately preserves it) |
| Python version compatibility | `asyncpg 0.30.0` supports the declared 3.11 runtime |

**Implementation consequence (open detail, not a decision):** without `pg_dump`, the exporter must
reconstruct the **schema** itself from read-only catalog functions
(`pg_get_functiondef`, `pg_get_viewdef`, `pg_get_constraintdef`, `pg_get_indexdef`, `pg_get_triggerdef`,
`pg_get_expr`, `pg_policies`, `pg_sequence`, `pg_type`) plus `COPY` streams for data, and must
**explicitly handle sequences** (set values after load). This is standard PostgreSQL catalog usage, but
it is the **largest piece of implementation work** in Phase 1 → recorded as **OID-1 / OID-2** in P2.5.


---

## P2.3 Verification findings — D2, D3, D4, D5

### D2 — Independent off-site destination: **compatible** (`REPOSITORY VERIFIED`)

* Nothing in the repository binds the backup destination to Supabase Storage. Existing storage usage
  (`storage3`, bundled with the `supabase` SDK) targets Supabase Storage, but the destination is a
  **design choice** → an independent provider is architecturally compatible.
* Installed clients: **`httpx 0.27.2`**, **`requests`**, **`storage3 0.8.2`**. **No `boto3`/`botocore`/
  `aioboto3`.**
* **Open implementation detail (OID-3):** an S3-compatible provider (R2/S3/B2) needs either a new declared
  dependency (`boto3`/`aioboto3`) or a minimal SigV4 client over `httpx`. Neither reaches the browser and
  neither requires Docker → **consistent with D1/D2**.
* Retains Part 1's conclusion that a database dump **excludes Storage objects**, so object backup remains
  a separate paired job (Part 1 §14) — unaffected by D2.

### D3 — Application-level encryption: **compatible** (`REPOSITORY VERIFIED`)

* **`cryptography 50.0.0` is already installed** in the backend environment (pulled transitively; it is
  *not* declared in either requirements file) → **AES-256-GCM (AEAD)** is available for application-level
  authenticated encryption **without** any subprocess, CLI or Docker step.
* The key can be sourced through the existing `os.getenv` configuration pattern in `backend/config.py`
  (Render secret), satisfying D3's constraints: not in the DB, not beside the artifact, never in the
  browser, separate custody, documented rotation.
* Python's **standard library has no AEAD**, so a crypto dependency is required — it already exists
  locally, which is why this is an **open implementation detail (OID-4: declare `cryptography` explicitly
  in `backend/requirements.txt`)**, not a blocker.
* Checksumming (SHA-256) uses stdlib `hashlib` — no dependency.

### D4 — Restore authorization: **supportable without weakening existing authorization** (`REPOSITORY VERIFIED`)

* Primitive already present: **`require_admin()`** and **`ADMIN_ROLE_NAMES = ("admin", "system_admin")`**
  (`backend/auth.py`), `is_internal_staff` (PE staff explicitly *denied* internal admin authority), and a
  **capability dictionary** on `staff_roles.permissions`. The capability vocabulary already includes
  `can_approve`, `can_delete`, `can_export`, `can_manage_billing`, `can_manage_roles`, `can_manage_staff`,
  `can_process`, … → new capabilities (e.g. `can_manage_backups`, and a distinct `can_approve_restore`) can
  be **added**, never substituted for existing ones.
* **Two-person approval has schema precedent**: `public.approval_requests` (`init_schema.sql:1374`) and
  `public.approval_decisions` (`init_schema.sql:1390`) already exist, and the legacy admin approval flow is
  referenced in `backend/routes/admin/extraction.py` → D4's "two-person for production" can reuse it.
* **Audit** is ready: append-only `audit_trail` via `infra/audit_logger.py` + `data/audit.py`.
* **Not weakened:** D4 is purely **additive** (new capabilities, new endpoints) — no existing role, policy
  or capability needs to be broadened. That is the key compatibility finding.


### D5 — Dedicated restricted `ct_backup` role: **feasible, with one documented limitation**

| Question | Finding |
|---|---|
| Can `ct_backup` be created? | Technically yes (a normal `CREATE ROLE` with `LOGIN`, `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`). **Whether the credential available to us may grant the needed privilege is `UNKNOWN`** → requires console/SQL verification (not attempted) |
| Minimum privileges for a logical dump | `USAGE` on the schema(s) + **read-only** access to tables/sequences/types (`pg_read_all_data`, PostgreSQL 14+, is cleanest; explicit `SELECT` grants are the alternative) + reads of `pg_catalog`/`information_schema` (no special privilege) |
| **Does RLS affect its visibility?** | **YES — this is the limitation.** The repository's own RLS design states: *"service_role and postgres BYPASSRLS by definition — no policy, no grant"* (`20260803000000_rc2_rls.sql:18`) and *"service_role / postgres: BYPASSRLS by Supabase convention"* (line 385). Application reads are RLS-scoped; only `service_role`/`postgres` see **all** rows. A role holding only `SELECT`/`pg_read_all_data` and **no** RLS bypass would produce an **RLS-filtered (incomplete) dump** — unacceptable for recovery |
| Can it access all required application data? | Only **with an RLS bypass** (or per-table permissive policies). `pg_read_all_data` **does not** bypass RLS, and `row_security = off` **errors** for a role without the bypass rather than returning all rows |
| Can it be prevented from modifying production? | **Yes.** Grant **no** INSERT/UPDATE/DELETE/TRUNCATE/DDL, and additionally enforce read-only at session level (`default_transaction_read_only = on` for the role) |

**Smallest safe alternative (proposed under D5's own instruction) — `PROPOSED — NOT EXECUTED`:**

```sql
-- PROPOSED — NOT EXECUTED
CREATE ROLE ct_backup LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT
  PASSWORD '<from-secret-manager>';        -- never stored in the repository
ALTER ROLE ct_backup BYPASSRLS;             -- read-completeness; grants no write privilege by itself
ALTER ROLE ct_backup SET default_transaction_read_only = on;
GRANT USAGE ON SCHEMA public TO ct_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ct_backup;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO ct_backup;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ct_backup;
-- deliberately NO INSERT/UPDATE/DELETE/TRUNCATE/DROP/ALTER/GRANT; no policy or RLS privileges
```

* **Preferred (above):** `ct_backup` + **`BYPASSRLS`** as a **read-completeness** privilege paired with
  **no write grants** and a **read-only session default** → satisfies D5's prohibitions (no broad
  admin/write/schema/RLS/user-management privileges) while still producing a **complete** dump. Requires
  that the available credential may grant `BYPASSRLS` (`UNKNOWN`).
* **Alternative (strictly least privilege, if `BYPASSRLS` cannot be granted):** add permissive
  `FOR SELECT USING (true)` policies for `ct_backup` on each table to be dumped — strictly narrower but
  **invasive and maintenance-heavy** (must track every new table in the pending 22 → 53 delta and beyond).
* **Last resort:** keep the exporter on the **existing `postgres` credential** already present in
  `DATABASE_URL` (what the platform uses today). Over-privileged versus D5's intent → only if both above
  are impossible.

No SQL was executed.

---

## P2.4 Verification findings — backup scope (§8) and migration safety (§9)

### Backup scope — **confirmed, unchanged**

**INCLUDE:** CarbonTally application schema + data (`public`); emission factors (7 049 rows); required
reference data (plans/config/roles seeded by migrations); **required sequences** (explicitly required for a
COPY-based exporter); safe **role definitions** (no passwords); relevant **extension metadata** (names +
versions as metadata, not extension internals).

**EXCLUDE:** secrets; encryption keys; passwords; service-role keys; Supabase internal infrastructure;
unnecessary Auth internals; **Storage objects from the PostgreSQL dump** (separate paired job);
migration-history internals (except as recorded metadata); transient/nonessential worker state.

No item requires a decision beyond D1–D5 → residual questions are recorded as **OPEN IMPLEMENTATION
DETAILS** (below).

### Migration safety (§9) — **confirmed, unchanged**

The delta remains **22 → 53**. The minimum acceptable evidence before those migrations may be authorized is
unchanged and is **not** satisfied by a dump alone:

1. backup successfully created · 2. encrypted · 3. stored independently from production · 4. checksum
verified · 5. **restored into a disposable/recovery environment** · 6. schema verified · 7. RLS verified ·
8. application startup verified · 9. critical workflow smoke test passed.

Part 1's `DR-20` is superseded **only** in that the **mechanism is now decided** (D1–D5); the **evidence
requirement is unchanged and still outstanding**. None of these steps was performed.


---

## P2.5 Open implementation details (not architectural decisions)

| ID | Detail | Note |
|---|---|---|
| **OID-1** | **Schema reconstruction without `pg_dump`** — use read-only catalog functions (`pg_get_functiondef`, `pg_get_viewdef`, `pg_get_constraintdef`, `pg_get_indexdef`, `pg_get_triggerdef`, `pg_get_expr`, `pg_policies`, `pg_sequence`, `pg_type`, `pg_proc`, `pg_trigger`) | The largest piece of Phase-1 work; feasible via `asyncpg` with **no new dependency** |
| **OID-2** | **Sequences** must be dumped and their values re-set after restore | Required for correctness of a COPY-based dump |
| **OID-3** | Off-site destination client: declare `boto3`/`aioboto3` **or** implement a minimal SigV4 client over `httpx` | Provider choice is implementation-level (D2 ratified the *category*) |
| **OID-4** | Declare **`cryptography`** explicitly in `backend/requirements.txt` (present locally, currently transitive) | Needed for AES-GCM; no subprocess/Docker involved |
| **OID-5** | `ct_backup` + `BYPASSRLS` fine print — confirm the available credential may grant it; otherwise use per-table `FOR SELECT USING (true)` policies | RLS limitation documented in P2.3 |
| **OID-6** | Compression choice (stdlib `gzip`/`lzma` — no new dependency) and streaming vs staged temp files | Part 1 §19 guardrails apply |
| **OID-7** | Completion-notification `event_key` depends on pending migration **45** (`phase5_notification_event_key`), **not applied** in production | Sequence the notification work after the delta, or degrade gracefully |
| **OID-8** | The audit-immutability guard (pending migration **39**) is also unapplied in production | Backup audit entries are still written; immutability enforcement arrives with the delta |

---

## P2.6 Implementation boundary (unchanged)

**Not implemented by this operation and not authorised by it:** the backup exporter; the backup table; the
admin API; the admin UI; encryption; object-storage integration; the `ct_backup` role; scheduled backups;
restore; and Storage-object backup. No SQL, GRANT/REVOKE, key, credential, bucket, dependency or
configuration change was made.

---

## P2.7 Required decision (Part 2)

**Q1 — Are D1–D5 internally consistent?** **YES.** D1 (pure-Python exporter) removes the Docker/CLI/
`pg_dump` dependency; D2 (independent object store) adds no runtime requirement; D3 (application-level
encryption) needs only a Python crypto library that **already exists**; D4 (separate restore capability) is
**additive** over the existing capability/approval/audit model; D5 (dedicated role) is compatible with the
platform's role model with the RLS caveat documented in P2.3. **No pair of decisions conflicts.**

**Q2 — Can D1 use the existing Render/native Python architecture?** **YES.** `asyncpg 0.30.0`'s
`copy_from_table`/`copy_from_query` provide the data path; the existing lifespan-managed worker pattern
provides execution; production code contains **no** `subprocess` usage; the native runtime is preserved
unchanged.

**Q3 — Is an independent off-site destination architecturally compatible?** **YES.** Nothing binds the
destination to Supabase Storage; only an object-store client dependency is an open detail (OID-3).

**Q4 — Is application-level encryption compatible with the current secret architecture?** **YES.**
`cryptography 50.0.0` is already present locally (AES-GCM); keys can be read via the existing
`os.getenv`/Render-secret pattern; D3's custody constraints are satisfiable without touching the database,
the artifact or the browser.

**Q5 — Can the existing admin/audit model support D4?** **YES.** `require_admin()` + `ADMIN_ROLE_NAMES` + a
capability dictionary; `approval_requests`/`approval_decisions` already exist for two-person approval; the
append-only `audit_trail` covers every required event. D4 adds capabilities and endpoints — it **never
weakens** existing authorization.


**Q6 — Is a least-privilege `ct_backup` role technically feasible?** **YES, with a documented
limitation.** A dedicated role is creatable with read-only privileges and a read-only session default, but
**without an RLS bypass it cannot produce a complete dump** (this repository's design makes
`service_role`/`postgres` the only complete readers). The **smallest safe alternative** is `ct_backup` +
`BYPASSRLS` + **SELECT-only** grants + `default_transaction_read_only = on` (proposed, not executed); the
strictly-least-privilege fallback is per-table `FOR SELECT USING (true)` policies; the last resort is the
existing `postgres` credential. **Whether `BYPASSRLS` can be granted is `UNKNOWN`** → console/SQL
verification needed.

**Q7 — Are there any architectural blockers?** **NO.** No architectural blocker was found; the P2.5 items
are implementation details.

**Q8 — Are there any decisions still required before implementation?** **No new architectural decisions.**
OID-1…OID-8 are implementation-level. One item warrants **PO awareness** (not a reopened decision): the
**`BYPASSRLS`-paired-with-SELECT-only** reading of D5 (P2.3 / OID-5) — a privilege nuance the PO may wish
to acknowledge explicitly; D5 itself authorises documenting the limitation and proposing the smallest safe
alternative.

**Q9 — Is the architecture now ready for a separate bounded implementation prompt?** **YES.**

---

## P2.8 Verdict (Part 2)

## `READY FOR BOUNDED IMPLEMENTATION — EXPLICIT PO AUTHORIZATION REQUIRED`

D1–D5 are **RATIFIED, mutually consistent, and verified against the current repository architecture**. No
architectural blocker exists; the remaining items are implementation details (OID-1…OID-8). A **bounded
Phase-1 implementation prompt** (backend exporter + secure artifact + off-site upload + read-only role
proposal) may be issued **only on explicit Product Owner authorization** — this operation implements
nothing.

---

## P2.9 Mandatory no-change confirmation (Part 2)

```text
Repository source modified: NO
Tests modified: NO
Migrations modified: NO
Git commit created: NO
Git push performed: NO
Production database altered: NO
Production database dumped: NO
Production data accessed for backup: NO
Production backup created: NO
Production backup downloaded: NO
Production backup storage created: NO
Production users created: NO
Production organisations created: NO
Production subscriptions created: NO
Production storage modified: NO
Production RLS modified: NO
Production grants modified: NO
Production Auth modified: NO
Production deployment performed: NO
Secrets changed: NO
Encryption keys created/changed: NO
Backup credentials created/changed: NO
```

*Only documentation files were written (this Part 2 and the matching prompt-history record). No backup,
dump, key, credential, role, bucket, dependency or configuration was created or changed; no production
contact occurred; no SQL was executed.*

