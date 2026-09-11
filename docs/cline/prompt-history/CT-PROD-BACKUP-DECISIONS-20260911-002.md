# CT-PROD-BACKUP-DECISIONS-20260911-002

**Prompt Ref:** `CT-PROD-BACKUP-DECISIONS-20260911-002` · **Datetime:** 2026-09-11
**Response Ref:** `CT-PROD-BACKUP-DECISIONS-20260911-002-R1`
**Mode:** READ-ONLY (ratification recording + architecture verification — NOT implementation)
**Repository:** CarbonTally · branch `main` · **HEAD / Release-1** `daad396523ac693352cc2f4ebb7fc58814a9e60b`
**Artifact updated:** `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md` → **Part 2** (Part 1 preserved verbatim)
**Final verdict:** `READY FOR BOUNDED IMPLEMENTATION — EXPLICIT PO AUTHORIZATION REQUIRED`

---

## 1. Prompt (faithful summary)

The PO ratified the five open decisions from `CT-PROD-BACKUP-ARCHITECTURE-20260911-001` and instructed a
**non-implementation** operation to record them durably, verify internal consistency against the existing
architecture, identify any contradiction/technical blocker, and prepare the repository for a future
bounded implementation prompt.

**Ratified decisions.** **D1** — pure-Python **`asyncpg`** exporter using the existing server-side worker;
the in-app mechanism must not require Docker, a new container runtime, Supabase CLI execution inside Render
or `pg_dump` subprocess execution; Render native Python remains the deployment model (CLI/`pg_dump` may
remain a documented operator fallback only). **D2** — independent off-site **private object storage**
(private, encrypted, lifecycle/retention, restricted access, no public URLs, separated from production,
survives Supabase failure). **D3** — **application-level encryption before storage**; key never in the DB,
never beside the artifact, never in the browser; separate custody; documented rotation/recovery.
**D4** — **restore is a separate high-risk capability** (backup = authorised admin + confirmation +
asynchronous + audited; restore = separate, stronger authorization, confirmation, preferably two-person for
production, default target disposable/recovery environment, production restore exceptional). **D5** —
**dedicated restricted `ct_backup` role** if technically supported (minimum privileges; no broad admin,
write, schema-modification, RLS-modification or user-management privileges); if restrictions prevent a
useful least-privilege role, **document the limitation and propose the smallest safe alternative**.

Explicit instruction: **do not reopen D1–D5**; record as RATIFIED unless a genuine technical contradiction
exists. Explicit prohibitions: implementing the exporter, backup table, admin API/UI, encryption, object
storage integration, `ct_backup`, scheduled backups, restore or Storage-object backup — and no credentials,
keys, buckets, production dumps, migrations, deploys or pushes.

---

## 2. Files inspected

`backend/infra/supabase.py` (service client + `asyncpg` service pool), `backend/workers/automatic_processing.py`
(worker pattern), `backend/main.py` (lifespan wiring), `backend/auth.py` (`require_admin()` /
`ADMIN_ROLE_NAMES` / capability vocabulary), `backend/config.py` (secret pattern), `backend/requirements.txt`
and `backend/requirements-dev.txt`, `backend/_phaseA_selfcheck.py` (only `subprocess` user),
`supabase/migrations/**` (RC2 RLS design comments; `init_schema.sql` `usage_tracking`,
`approval_requests`, `approval_decisions`; grant targets), `backend/routes/admin/extraction.py`
(approval-flow precedent), `runtime.txt`, and the installed backend virtualenv
(`asyncpg-0.30.0`, `cryptography-50.0.0`, `httpx-0.27.2`, `storage3-0.8.2`, `PyJWT-2.8.0`, `supabase-2.9.0`).

## 3. Commands run (all read-only)

```
git rev-parse HEAD · git log -1 --oneline · git status --porcelain=v1 · git diff --cached --name-only
grep -nE 'async def copy_|def copy_' backend/.venv/.../asyncpg/connection.py
grep -oE 'Version: [0-9.]+' backend/.venv/.../asyncpg-0.30.0.dist-info/METADATA
grep -rnE 'subprocess|tempfile' backend --include='*.py' --exclude-dir=.venv --exclude-dir=tests
ls -d backend/.venv/.../site-packages/{cryptography*,Crypto,nacl,boto3,aioboto3,botocore,storage3,httpx,requests}
grep -rn -i 'cryptography' backend/requirements.txt backend/requirements-dev.txt
ls -d backend/.venv/.../site-packages/*.dist-info | grep -iE 'pyjwt|resend|supabase|gotrue|postgrest|storage3|httpx|cryptography'
grep -rn -iE 'create table( if not exists)? public\.(approval_requests|approval_decisions)' supabase/migrations/*.sql
grep -rln -iE 'approval_request|approval_decision|two.person' backend --include='*.py'
grep -rniE 'bypassrls|pg_read_all_data|row_security' supabase/migrations/*.sql
grep -rohiE 'grant [^;]* to [a-z_\", ]+' supabase/migrations/*.sql   (role targets)
grep -rohE 'can_[a-z_]+' backend --include='*.py' | sort -u          (capability vocabulary)
grep -c 'enable row level security' supabase/migrations/00000000000000_init_schema.sql ...
```

**No SQL was executed against any database; production was not contacted; no dump, backup, key, credential
or bucket was created.**

## 4. Verification results

### D1 — pure-Python `asyncpg` exporter: **COMPATIBLE**
* `asyncpg 0.30.0` **installed**; exposes `copy_from_table()` (connection.py:797) and `copy_from_query()`
  (line 869) — data can be streamed via `COPY … TO STDOUT` with **no external binary**.
* `backend/infra/supabase.py::get_service_pool()` already builds the process-wide `asyncpg` pool.
* `backend/workers/automatic_processing.py` supplies the exact worker pattern (lifespan-managed asyncio,
  `FOR UPDATE SKIP LOCKED`, DB-held state, resume-after-restart, fault isolation).
* **No `subprocess` in production code** — only `backend/_phaseA_selfcheck.py` (dev script). No production
  `tempfile` usage either.
* `runtime.txt` = `python-3.11.9`, native buildpack, no Dockerfile → **unchanged** by D1.

### D2 — independent off-site destination: **COMPATIBLE**
* Nothing binds the destination to Supabase Storage; installed clients are `httpx`, `requests`, `storage3`;
  **no `boto3`/`botocore`/`aioboto3`** → the provider client is an implementation detail (OID-3).

### D3 — application-level encryption: **COMPATIBLE**
* **`cryptography 50.0.0` is already installed** (transitively; **not declared** in either requirements
  file) → AES-256-GCM / authenticated encryption available **without** subprocess or Docker.
* Key sourcing fits the existing `os.getenv` pattern in `backend/config.py` (Render secret); stdlib
  `hashlib` covers SHA-256 checksums; the stdlib has **no AEAD**, hence the dependency note (OID-4).

### D4 — restore authorization: **SUPPORTABLE, ADDITIVE**
* `require_admin()` + `ADMIN_ROLE_NAMES = ("admin","system_admin")` + `is_internal_staff` + the capability
  dictionary (`can_approve`, `can_delete`, `can_export`, `can_manage_billing`, `can_manage_roles`,
  `can_manage_staff`, `can_process`, …) → new capabilities (`can_manage_backups`, `can_approve_restore`) can
  be **added** without broadening anything.
* **Two-person approval precedent exists**: `public.approval_requests` (`init_schema.sql:1374`) and
  `public.approval_decisions` (`init_schema.sql:1390`); the legacy approval flow is referenced in
  `backend/routes/admin/extraction.py`.
* Append-only `audit_trail` (`infra/audit_logger.py` + `data/audit.py`) covers every required event.
* **No weakening of existing authorization is required.**

### D5 — dedicated `ct_backup` role: **FEASIBLE WITH A DOCUMENTED LIMITATION**
* Role creation and read-only privileges are technically straightforward.
* **RLS is the limitation (`REPOSITORY VERIFIED` in the repo's own comments):**
  `20260803000000_rc2_rls.sql:18` — *"service_role and postgres BYPASSRLS by definition — no policy, no
  grant"*; line 385 — *"service_role / postgres: BYPASSRLS by Supabase convention"*. A role holding only
  `SELECT`/`pg_read_all_data` and **no RLS bypass** would produce an **RLS-filtered (incomplete) dump**;
  `pg_read_all_data` does **not** bypass RLS, and `row_security = off` **errors** for such a role.
* Grant targets in migrations are only `authenticated` (14) and `service_role` (11) — no precedent for a
  third read role; `BYPASSRLS`/`pg_read_all_data` appear **only in explanatory comments**.
* **Smallest safe alternative (proposed, NOT executed):** `ct_backup` with `LOGIN NOSUPERUSER NOCREATEDB
  NOCREATEROLE`, **`BYPASSRLS`**, `default_transaction_read_only = on`, and **SELECT-only** grants
  (+ `GRANT USAGE ON SCHEMA`, `SELECT ON ALL TABLES/SEQUENCES`, default privileges) — **no**
  INSERT/UPDATE/DELETE/TRUNCATE/DDL/policy privileges. Strictly-least-privilege fallback: per-table
  `FOR SELECT USING (true)` policies for `ct_backup`. Last resort: the existing `postgres` credential.
* **`UNKNOWN`:** whether the credential available to us may grant `BYPASSRLS` (console/SQL verification
  needed; not attempted).

### Backup scope (§8) and migration safety (§9) — **CONFIRMED UNCHANGED**
Include: application schema/data, emission factors, required reference data, **sequences**, safe role
definitions, extension metadata. Exclude: secrets, keys, passwords, service-role keys, Supabase internals,
unnecessary Auth internals, Storage objects, migration-history internals, transient worker state. The delta
remains **22 → 53** and the nine-point evidence requirement is **unchanged and outstanding** (backup created
→ encrypted → stored independently → checksum verified → **restored into a disposable environment** → schema
verified → RLS verified → app startup verified → critical workflow smoke test).

## 5. Decisions

D1–D5 recorded as **RATIFIED** and **not reopened**; no architectural contradiction was found. One privilege
nuance (D5 `BYPASSRLS`-with-SELECT-only) is recorded for **PO awareness** rather than as a reopened
decision, and the alternative architectures were **not** re-litigated.

## 6. Risks

* **`BYPASSRLS` availability `UNKNOWN`** — if it cannot be granted, D5 degrades to per-table
  `USING (true)` policies (a maintenance burden as new tables arrive in the 22 → 53 delta).
* **Schema reconstruction without `pg_dump`** is the largest Phase-1 effort and the main correctness risk
  (OID-1/OID-2: functions/views/constraints/indexes/triggers/policies/sequences).
* **New dependencies must be declared explicitly** (`cryptography` for OID-4; an object-store client for
  OID-3) rather than relied on transitively.
* **Sequencing**: notification `event_key` (migration 45) and audit immutability (migration 39) are
  **unapplied** in production → Phase-1 notification/immutability behaviour must degrade gracefully.
* **An unrestored backup is unproven** — the Phase-3 drill remains mandatory before the migrations.


## 7. Final verdict

> ## `READY FOR BOUNDED IMPLEMENTATION — EXPLICIT PO AUTHORIZATION REQUIRED`

**Answers:** Q1 **consistent** · Q2 **yes — the existing Render/native architecture is used unchanged** ·
Q3 **compatible** · Q4 **compatible (`cryptography` already present)** · Q5 **yes — additive over the
existing capability/approval/audit model** · Q6 **feasible with a documented RLS limitation plus the
smallest safe alternative** · Q7 **no architectural blockers** · Q8 **no new architectural decisions —
OID-1…OID-8 are implementation details, with the D5 privilege nuance flagged for PO awareness** ·
Q9 **yes — a bounded implementation prompt may be issued on explicit PO authorization**.

## 8. Open implementation details (recorded, not decisions)

`OID-1` schema reconstruction via read-only catalog functions · `OID-2` sequence handling · `OID-3`
object-store client dependency · `OID-4` declare `cryptography` explicitly · `OID-5` `ct_backup` +
`BYPASSRLS` fine print · `OID-6` compression/temp-file strategy · `OID-7` notification `event_key`
depends on pending migration 45 · `OID-8` audit-immutability guard depends on pending migration 39.

## 9. No-change confirmation

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

*Only documentation files were written. No backup, dump, key, credential, role, bucket, dependency or
configuration was created or changed; no production contact occurred; no SQL was executed.*

See **Part 2** of `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md`
(Part 1 preserved verbatim above it).

