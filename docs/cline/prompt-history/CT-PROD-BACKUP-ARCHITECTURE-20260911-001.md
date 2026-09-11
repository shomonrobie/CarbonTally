# CT-PROD-BACKUP-ARCHITECTURE-20260911-001

**Prompt Ref:** `CT-PROD-BACKUP-ARCHITECTURE-20260911-001` · **Datetime:** 2026-09-11
**Response Ref:** `CT-PROD-BACKUP-ARCHITECTURE-20260911-001-R1`
**Mode:** READ-ONLY architecture assessment (no implementation)
**Repository:** CarbonTally · branch `main` · **HEAD / Release-1** `daad396523ac693352cc2f4ebb7fc58814a9e60b`
**Primary artifact:** `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md`
**Final verdict:** `FEASIBLE — DESIGN REQUIRES DECISIONS`

---

## 1. Prompt (faithful summary)

The PO wants CarbonTally to support a **controlled database-backup capability while production Supabase
remains on the Free tier**, where managed PITR/backup may be unavailable: an **authorized CarbonTally
administrator can request a temporary logical backup of production through the admin panel, without
exposing Supabase database credentials or CLI access to the browser**. The operation was **READ-ONLY
architecture assessment only** — explicitly **not** authorized to implement. Prohibited: running
`supabase db dump`/`pg_dump` against production, creating a backup, downloading production data,
accessing production data unnecessarily, modifying production/Supabase/storage, creating buckets, backup
tables, users, roles, RLS or Auth changes, environment changes, adding dependencies, modifying code/
migrations/frontend/backend/infrastructure, commit, push, deploy — and never retrieving or exposing a
production secret. Objectives: repository architecture discovery; Supabase Free-tier feasibility
(repository vs documentation vs `UNKNOWN`, no assumptions); backup scope; destination; encryption; admin
workflow; job model; idempotency/concurrency; temp-file security; integrity; restore; Storage-object
backup; secrets/configuration recovery; retention; audit events; threat model; command-execution
security; credential architecture; cost; first-customer readiness; migration-safety prerequisite;
separation from DR-16/DR-19; implementation phases; final architecture with trust boundaries; Q1–Q12 and
one mandated verdict; the two durable artifacts; and the exact 21-line no-change checklist.

---

## 2. Files inspected

`backend/main.py`, `backend/api/router.py`, `backend/api/v3_settings.py`, `backend/api/audit_helpers.py`,
`backend/auth.py`, `backend/config.py`, `backend/core/exceptions.py`, `backend/database.py`,
`backend/data/base.py`, `backend/data/settings.py`, `backend/data/audit.py`,
`backend/data/notifications.py`, `backend/infra/supabase.py`, `backend/infra/audit_logger.py`,
`backend/infra/event_bus.py`, `backend/workers/automatic_processing.py`, `backend/requirements.txt`,
`frontend/src/v3/admin/AdminPage.jsx` (+ sibling tabs), `package.json`, `vercel.json`, `runtime.txt`,
`supabase/config.toml`, plus Git metadata and the three prior production documents
(`DEPLOYMENT_READINESS`, `SUPABASE_RECONCILIATION`, `MIGRATION_SAFETY_PLAN`).
(`CARBONTALLY_PRODUCTION_SAFETY_PREREQUISITES_20260911.md` — **not present**.)

## 3. Commands run (all read-only)

```
git rev-parse HEAD · git log -1 --oneline · git status --porcelain=v1 · git diff --cached --name-only
ls docs/architecture/CARBONTALLY_PRODUCTION_SAFETY_PREREQUISITES_20260911.md
grep -rniE 'pg_dump|pg_restore|db dump|supabase db|backup' backend frontend/src admin/src
grep -rlnE 'subprocess|os.system|shlex|Popen' backend ; grep -rlnE 'tempfile|/tmp' backend
ls backend/api/ | grep admin ; grep 'ADMIN_ROLE_NAMES|require_admin' backend/auth.py
ls frontend/src/v3/admin/ ; grep tabs in frontend/src/v3/admin/AdminPage.jsx
sed -n '1,45p' backend/database.py ; sed -n '1,40p' backend/infra/supabase.py
cat backend/requirements.txt ; grep -rnE 'asyncpg|DATABASE_URL' backend/**
grep -rn 'usage_tracking|ON CONFLICT' backend/{data,services,domain}/billing.py
find . -maxdepth 3 -iname 'Dockerfile*' ; find . -maxdepth 3 -name 'render*.y*ml'
grep -nE 'buildCommand|outputDirectory' vercel.json
sed -n '1,60p' backend/api/v3_settings.py ; grep -nE '^\s{4}[A-Z_]{3,}' backend/config.py
grep -nE 'v3_settings|admin_|v3_commercial|v3_billing|v3_health' backend/api/router.py
```

**Production was not contacted in this operation; no production query, dump, backup or data access was
performed.**

## 4. Documentation sources consulted (`SUPABASE DOCUMENTATION VERIFIED`)

* `https://supabase.com/docs/guides/platform/backups` — plan-by-plan backup/PITR facts, Storage-object
  exclusion, role-password exclusion, project-deletion effects, restore downtime, PITR pricing.
* `https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore` — the documented
  CLI `db dump` flow (`roles.sql --role-only`, `schema.sql`, `data.sql --use-copy --data-only` with
  `storage` exclusions), the **CLI + Docker Desktop** prerequisite, the required **database password**
  and connection string, the `psql`/Postgres requirement on the restore side, the "enable extensions and
  Database Webhooks" restore steps, the vendor note that Restore-to-a-new-project / Branching copy the
  **encryption root key** automatically, and the separate Storage-object migration script.
* `https://supabase.com/docs/reference/cli/supabase-db-dump` — CLI reference (retrieved; confirms the
  command set and that `db dump` targets a remote database via `--db-url`).

## 5. Findings

1. **Free tier has no managed backup and no PITR** — daily backups are Pro/Team/Enterprise only; PITR is
   a Pro+ add-on; and Supabase **explicitly recommends `db dump` + off-site backups for Free projects**.
2. **The repository already contains every architectural primitive needed**: the lifespan-managed,
   DB-durable, `SKIP LOCKED` worker (`workers/automatic_processing.py`); the server-side credential path
   (`infra/supabase.py` — `asyncpg` pool as the `postgres` role via `DATABASE_URL`; service-role REST
   client); the append-only audit trail (`infra/audit_logger.py` + `data/audit.py`); idempotent
   notifications (`data/notifications.py::create_idempotent`); the admin authorization model
   (`require_admin()`, `ADMIN_ROLE_NAMES = ("admin","system_admin")`, `staff_roles.permissions`); and an
   **already-configured `backup_retention_days` setting** wired through `/api/v3/settings/retention`.
3. **Decisive constraint:** the documented dump flow needs the **CLI + Docker**, but the repo has **no
   Dockerfile** and the backend runs Render's **native** Python runtime (which cannot install OS
   packages). So `pg_dump`/CLI automation is **not deployable as-is**; the alternatives are a
   container-based service or a **pure-Python `asyncpg` COPY exporter** (no new OS dependency, since
   `asyncpg>=0.30.0` is already a dependency and already connected).
4. **No command-execution or temp-file code exists today** (`subprocess`/`tempfile` appear only in
   `backend/_phaseA_selfcheck.py` and tests) → the backup worker would introduce the platform's **first**
   command-execution surface; argument integrity must be designed in from the start.
5. **A DB dump is not a complete recovery** — `DOCUMENTATION VERIFIED` that Storage objects are excluded
   ("the database only includes metadata") and role passwords are not stored; Storage backup must be a
   **separate, paired job**, and configuration/secrets need an independent recovery story.
6. **The `documents` bucket does not exist in production** (`DR-08`) and there are no customer documents
   yet → Storage-object backup is not blocking today but becomes **P1 on the first real upload**.
7. **`DR-20` gate:** the migration safety plan's P0 prerequisite is satisfied **only** by a verified,
   off-site, encrypted, checksummed pre-migration dump **whose restore has been proven** — which Free-tier
   managed backups cannot provide, making this capability a genuine migration prerequisite.
8. **DR-16/DR-19 kept separate** and **not fixed**; neither changes the backup architecture.

## 6. Decisions (proposed, PO ratification required)

Recorded as **open decisions rather than made unilaterally**: **D1** dump mechanism vs Render runtime
(native + `asyncpg` COPY exporter vs container + `pg_dump` vs operator CLI playbook only);
**D2** off-site destination provider + retention; **D3** encryption tool + key custody; **D4** restore
authorization model; optional **D5** a dedicated read-only `ct_backup` role instead of the `postgres`
superuser the app currently connects with.

Recommended architecture: a **sibling `BackupWorker`** started by the existing lifespan; a new
**`backup_jobs`** table; a **read-only DB credential**; a **fixed/parameterised** dump step;
**client-side encryption before upload**; an **independent private object-storage bucket** as primary
destination; an encrypted **admin download** as secondary; and a **disposable-project-first** restore
procedure requiring **stronger** authorization than backup.

## 7. Risks

* **Runtime/mechanism mismatch (D1)** — the largest risk to feasibility; introducing a Dockerfile is an
  infrastructure change the repository does not currently have.
* **Unproven backups** — a dump that has never been restored provides false assurance; the restore drill
  is mandatory evidence.
* **Key loss** — losing the encryption key destroys every backup; key custody must be explicit.
* **First command-execution surface** — argument-injection and temp-file-leak risks are **new** to this
  codebase and must be mitigated by construction.
* **Production size unknown** — cost/time cannot be quantified until safely measured (recorded
  `UNKNOWN`, never invented).
* **Restore is the dangerous half** — it replaces live data and must never be a casual admin action.
* **Retention vs auditability/privacy** — a backup containing personal data is itself personal data.

## 8. Stop-condition confirmation

**No stop condition was triggered.** The assessment is read-only by construction: production was **not
contacted**, no dump/backup was created, no credential, key, bucket, table or storage object was created
or changed, and no repository source/migration/test/config file was modified. `UNKNOWN`s (Render
`pg_dump` availability, production database size, dashboard-side Render disk/backup settings) were
recorded as **`UNKNOWN`/prerequisite rather than guessed**. The verdict stops short of implementation:
**four decisions (D1–D4) must be ratified by the PO before a bounded implementation prompt.**


## 9. Final verdict

> ## `FEASIBLE — DESIGN REQUIRES DECISIONS`

**Answers:** Q1 **yes — the architecture can host the worker** (with the D1 caveat) · Q2 **yes — the Free
tier supports logical backups and Supabase recommends exactly this** · Q3 **a read-only DB credential;
plus the DB password + connection string + CLI/Docker for the vendor path; a destination write
credential; an encryption key; a service-role key only for Storage** · Q4 **server-side in the
CarbonTally backend/worker** · Q5 **a private bucket in an independent object store (primary) + an
encrypted admin download (secondary)** · Q6 **yes — separate, paired jobs** · Q7 **include `public`
schema+data, role definitions, extension list, metadata and factors; exclude `auth` data, extension
internals, `supabase_migrations` data, Storage objects and all secrets** · Q8 **restore into a disposable
project first; verify schema/data/RLS/startup/workflows; then treat production restore as exceptional** ·
Q9 **a verified off-site encrypted checksummed pre-migration dump with a proven restore** · Q10 **Phases
1–2 + one Phase 3 drill + the secrets runbook** · Q11 **scheduling, object backup while empty, PITR/paid
backups, secondary mirroring** · Q12 **not yet — D1–D4 must be ratified first**.

### Open decisions blocking a bounded implementation prompt

| # | Decision | Options |
|---|---|---|
| D1 | Dump mechanism vs Render runtime | (a) native runtime + pure-Python `asyncpg` COPY exporter; (b) container-based service + `pg_dump`; (c) operator CLI playbook only (no in-app automation yet) |
| D2 | Off-site destination + retention | R2 / S3 / B2 / other; 7 / 30 / 90-day retention |
| D3 | Encryption tool + key custody | `age` / GPG / AES-256-GCM; where the key lives; who holds it; escrow; rotation |
| D4 | Restore authorization model | who approves; two-person rule; disposable-only vs production restore |
| D5 (optional) | Dedicated read-only `ct_backup` DB role | yes/no (recommended) |

See `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md`.

