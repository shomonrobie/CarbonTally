# CT-PROD-SUPABASE-RECON-20260911-001

**Prompt Ref:** `CT-PROD-SUPABASE-RECON-20260911-001`
**Datetime:** 2026-09-11
**Response Ref:** `CT-PROD-SUPABASE-RECON-20260911-001-R1`
**Mode:** READ-ONLY Production Supabase Reconciliation
**Repository:** CarbonTally · branch `main` · HEAD `daad396523ac693352cc2f4ebb7fc58814a9e60b`
**Primary report:** `docs/architecture/CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md`
**Final verdict:** `NOT READY — PRODUCTION STATE STILL UNKNOWN`

---

## 1. Prompt (faithful summary of the full Product Owner prompt)

The PO authorized **one bounded operation**: *determine the actual state of the production Supabase
project and reconcile it against CarbonTally Release-1*, **read-only**. Explicit prohibitions: apply
migrations, `supabase db push`, `supabase migration up`, arbitrary DDL, INSERT/UPDATE/DELETE/TRUNCATE,
create/drop/alter tables or policies, create/revoke grants, create users/organisations/subscriptions/
buckets, upload/delete files, load emission factors, modify production env vars, deploy Render/Vercel,
push Git, commit code, modify application code/migrations/RLS/E2E fixtures/production configuration.
Required outputs: the primary report
`docs/architecture/CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md` and this prompt-history
file, ending with the exact 18-line no-change checklist and one of three mandated final verdicts.

---

## 2. Files inspected

`supabase/.temp/linked-project.json`, `supabase/.temp/project-ref`, `supabase/.temp/pooler-url`,
`supabase/.temp/{cli-latest,gotrue-version,rest-version,storage-version,postgres-version,storage-migration,pgdelta,start-secrets}`,
`backend/supabase/.temp/project-ref`, `supabase/config.toml`, root `.env.production`,
`frontend/.env.production`, `frontend/src/supabaseClient.js`, `backend/config.py`,
`backend/data/billing.py`, `backend/api/v3_commercial.py`, `backend/api/v3_billing.py`,
`supabase/migrations/**` (all 53; the 17 Release-1 migrations read object-by-object),
`output/sql/` (tracked-vs-on-disk), `~/.supabase/` (names only), plus Git metadata.
Authorities: `CARBONTALLY_PRODUCTION_DEPLOYMENT_READINESS_20260911.md`,
`CARBONTALLY_PRODUCTION_RELEASE_MANIFEST_20260911.md`, `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`,
`CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`.

## 3. Commands run (all read-only)

```
git branch --show-current · git rev-parse HEAD · git log -1 --oneline
git status --porcelain=v1 · git status -sb · git diff --cached --name-only
git merge-base --is-ancestor daad396… HEAD · git log --oneline daad396…..HEAD
git show --name-only --diff-filter=A HEAD -- supabase/migrations
git ls-tree -r --name-only HEAD~1 -- supabase/migrations
git cat-file -s HEAD:output/sql/import_defra_2025.sql
ls -1 supabase/migrations/*.sql · ls -1 supabase/.temp/ · cat supabase/.temp/*   (non-secret)
grep/sed over .env.production and frontend/.env.production                       (values redacted)
getent hosts {supabase.co, supabase.com, api.supabase.com,
              pvwiojoyaqywtydzcpbg.supabase.co, aws-0-eu-west-2.pooler.supabase.com}
timeout 15 curl -sS -m 12 -o /dev/null -w '%{http_code}' https://supabase.com
timeout 20 curl -sS -m 18 -o /dev/null -w '%{http_code}' https://pvwiojoyaqywtydzcpbg.supabase.co/auth/v1/health
timeout 20 curl -sS -m 18 -o /dev/null -w '%{http_code}' https://pvwiojoyaqywtydzcpbg.supabase.co/rest/v1/
timeout 12 bash -c 'exec 3<>/dev/tcp/aws-0-eu-west-2.pooler.supabase.com/5432'
```

## 4. SQL / read-only database queries run

**Against the LOCAL stacks only** (never production):

```sql
-- local dev :54426 and isolated E2E :55326
select count(*) from pg_tables   where schemaname='public';                    -- 116 / 116
select count(*) from pg_policies where schemaname='public';                    -- 174 / 175
select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='public' and c.relkind='r' and c.relrowsecurity;             -- 116 / (not re-queried)
select count(*) from supabase_migrations.schema_migrations;                    -- 46 / 26
select count(*) from public.emission_factors;                                  -- 7049 / 0
select count(*) from storage.buckets where name='documents';                   -- 1 / 0
```

**Against production: none.** No production SQL was executed (see §6).

## 5. Evidence / results

* **Git:** branch `main`; HEAD `daad396…`; HEAD **is** the Release-1 commit; Release-1 is an ancestor
  of HEAD; **0** commits after Release-1; staged **0**; working tree `75 ?? / 152 D / 209 M`;
  **not pushed** (`main…origin/main [ahead 29]`); **0** modified/untracked migration files.
  Migrations: **53 tracked**, **36 at `HEAD~1`**, **17 added by Release-1**.
* **Production identity** (`supabase/.temp/linked-project.json`):
  `{"ref":"pvwiojoyaqywtydzcpbg","name":"CarbonTally","organization_id":"pfurlzwxdtvyljnahlnx"}`;
  `SUPABASE_URL=https://pvwiojoyaqywtydzcpbg.supabase.co` in **both** root `.env.production` and
  `frontend/.env.production`; `REACT_APP_API_URL=https://carbontally-api.onrender.com`; the shipped
  frontend default names the same project. Pooler URL (no password embedded):
  `postgresql://postgres.pvwiojoyaqywtydzcpbg@aws-1-eu-west-2.pooler.supabase.com:5432/postgres`.
* **Credentials:** **no** read-only or password-based production credential exists. `~/.supabase/`
  contains only `telemetry.json` and `traces/` (no CLI login token); `SUPABASE_ACCESS_TOKEN`,
  `PGHOST`, `PGPASSWORD` unset; every local `DATABASE_URL` is `127.0.0.1`. A **write-capable
  `SUPABASE_SERVICE_KEY` is present** and was deliberately **not used**.
* **Availability probes:** control DNS resolves (`supabase.co` → 76.76.21.21, `supabase.com` →
  216.150.1.193, `api.supabase.com` → resolves), `https://supabase.com` → **HTTP 200**, regional
  pooler TCP **OPEN** — **but** `pvwiojoyaqywtydzcpbg.supabase.co` → **NXDOMAIN**, and both
  unauthenticated HTTPS probes (`/auth/v1/health`, `/rest/v1/`) → `Could not resolve host`, HTTP `000`.
* **Cached non-secret stack metadata** from an earlier successful link (reference only): gotrue
  `v2.195.0`, postgrest `v14.5`, storage `v1.69.0`, postgres `17.6.1.147`, cli-latest `v2.117.0`;
  `supabase/.temp/pgdelta` and `supabase/.temp/start-secrets` are **0 bytes**.
* **Local/E2E (non-production):** dev `:54426` = 116 tables / 174 policies / 116 RLS tables /
  46 recorded migrations / 7 049 factors / `documents` bucket present; E2E `:55326` = 116 tables /
  175 policies / 26 recorded migrations / **0 factors / no `documents` bucket**.
* **Factor source:** `output/sql/import_defra_2025.sql` = **5 602 253 bytes**, **tracked at HEAD**,
  **14 059** factor statements, **deleted from the working tree** (one of the 152 excluded deletions);
  `output/sql/emission_factors.sql` = **5 707 634 bytes**, **untracked**, on disk only.
* **Storage:** the only migration reference is
  `supabase/migrations/20260823000000_d32_private_documents_storage.sql:18` —
  `UPDATE storage.buckets SET public = FALSE WHERE name = 'documents';` → **no migration creates the
  bucket**.
* **Billing/provisioning:** repository-verified `d37` tables (`billing_plans`,
  `billing_commercial_config`, `billing_credit_ledger`, `billing_orders`, `billing_payment_records`,
  `billing_storage_usage`, `billing_idempotency_keys`, `customer_subscriptions`, `usage_tracking`) and
  the `/api/v3/commercial` + `/api/v3/billing` surfaces. Production schema state `UNKNOWN`.

## 6. Decisions and risks

**Decisions made during this operation**
1. Treated a **service-role key as NOT read-only access** → refused to use it (§2).
2. **Refused to re-run `supabase migration list --linked`** because that command **creates a temporary
   login role** in the target database, i.e. it can mutate production (§16 stop condition).
3. Refused to manufacture, guess or bypass credentials.
4. Refused to infer production application from local/E2E state (§7 / §13).
5. Recorded the project-host **NXDOMAIN** as an *availability* finding without overclaiming that the
   project is deleted.

**Risks surfaced**
* Production **availability** unconfirmed — the dedicated project hostname does not resolve.
* The only locally present production-capable credential is **write-capable** (and unusable while the
  host is NXDOMAIN).
* Migration history cannot be trusted as a schema proxy (local evidence: 46 / 26 recorded vs 116
  tables) → object-level reconciliation is mandatory.
* The emission-factor dataset remains trapped in the excluded `output/**` tree (`DR-02`).
* The `documents` bucket is not migration-created (`DR-08`).
* A stale cached pooler hostname (`aws-1-…`) versus the resolving `aws-0-…` may independently explain
  earlier connection failures.

## 7. Stop-condition confirmation

One or more §16 stop conditions applied, and the operation **stopped without working around them**:

* **"credentials are unavailable"** — no read-only production credential exists, and the sole
  available credential is write-capable (inadmissible under §2, and unusable while the host is
  NXDOMAIN).
* **"a command's mutation safety is uncertain"** — `supabase migration list --linked` performs a
  login-role creation; it was **not** executed.
* No migration was applied to determine state; no production data was created; no repository code was
  changed.

## 8. Final verdict

> ## `NOT READY — PRODUCTION STATE STILL UNKNOWN`

Production **identity is CONFIRMED** (`pvwiojoyaqywtydzcpbg` / `CarbonTally`), but production **state
and availability remain unestablished**. Every schema, migration, RLS, storage, factor and auth
question is `UNKNOWN`. One **new P0 finding (DR-15)** was raised: the project's dedicated hostname does
not resolve while all control lookups and the regional pooler succeed.

Read-only actions were limited to Git/repository inspection, local-stack `psql` reads, DNS/TCP/HTTPS
availability probes, and writing the two durable documentation artefacts.

See `docs/architecture/CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md`.

