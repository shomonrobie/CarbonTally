# CT-FINAL-02 — LIVE EVIDENCE CLOSURE PASS (Parts A–J)

**Report ID:** `CT-FINAL-02-20261001-LIVE-EVIDENCE-CLOSURE-PASS`
**Date:** 2026-10-01
**Author:** Cline (implementation agent)
**Repository:** `/home/shomonrobie/ct_93d5cdd` · application root `backend/`
**Nature:** **Additive, read-only evidence report.** It edits no verifier-authored document, changes no
product code, applies no migration, provisions no identity, opens no SMTP session and sends no email.

**Governance at time of writing:** FINAL-01 **CLOSED** · Storage Management Steps 1+2 **CLOSED** ·
Storage Step 3 / FINAL-03 **NOT AUTHORIZED** · **FINAL-02 remains OPEN** (not closed by this pass).

## Final status

> **FINAL-02 LIVE EVIDENCE CLOSURE PASS COMPLETE — READY FOR UPDATED INDEPENDENT ACCEPTANCE.**
>
> FINAL-02 is **not** closed here. Nothing was implemented, mutated, provisioned, deployed, or sent.

---

## Part A — Scope, method and hard constraints

### A.1 Objective

Resolve the FINAL-02 rehearsal-baseline documents' central blocked premise ("live/shared and SMTP
credentials are unavailable in this environment") by **directly probing the live, local and e2e
surfaces read-only**, and hand the corrected evidence set to independent acceptance.

### A.2 Method (all steps read-only)

| Surface | Method | Mutation? |
| --- | --- | --- |
| Deployment environment variables | `backend/.env` read; **key names + value lengths only** captured; values never printed | none |
| Live Supabase Postgres | `psql` over the Supavisor pooler using the DSN in `.env`; **SELECT-only** catalog/value queries | none |
| Live Supabase HTTP API | `curl` `GET` probes only (HTTP status codes captured, no rows ingested) | none |
| Local Supabase stack | `docker ps`, listening-port probes, `psql` over the local instance (SELECT-only) | none |
| Local REST gateway | `curl` `GET` probes only (status codes) | none |
| e2e harness | file/README reading; **identity *key* inventory only** (no values read, none seeded) | none |
| SMTP | **static code trace only** — no SMTP connection opened, no credential used, no email sent | none |

### A.3 Hard constraints honoured

1. **No mutation of production.** Every live statement below is derived from `SELECT`/`GET`; no DDL,
   DML, migration application, bucket edit, settings write, or object operation was performed.
2. **No credential disclosure.** Passwords, keys and DSN secrets never appear in this report: only
   *variable names*, *value lengths*, *key classes* (e.g. the `sb_secret_…` prefix class) and *hosts*.
   No mailbox addresses are reproduced; identities are reported as counts and as harness *variable
   names*.
3. **No email delivered.** The SMTP portion is a static trace (B1 stays a *proof* gap, not a false
   premise).
4. **No provisioning.** No user, organisation, bucket, database, container or migration was created.
   The local databases and the harness identities are **catalogued, not provisioned** (Parts G).
5. **FINAL-02 not closed; no implementation.** Where a defect-shaped observation was found, the
   *portion was stopped and reported* (Parts F.4, E.4) rather than fixed.

### A.4 Documents cross-referenced

* `docs/architecture/CT-FINAL-02-20260930-REHEARSAL-BASELINE-AND-GAP-MATRIX.md` (the matrix being corrected)
* `docs/architecture/CT-FINAL-02-INDEPENDENT-VERIFICATION-REPORT.md` (verifier-authored; **not edited**)
* `docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_BASELINE.md` (§10.3/§10.4, F-3, F-9, C-09, O-2)
* `docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_STEP2_IMPLEMENTATION_20260930.md`
* `backend/services/email_provider.py`, `backend/services/v3_email.py`, `backend/data/settings.py`
* `supabase/migrations/20261024000000_ct_final_01_documents_bucket_size_limit.sql`
* `supabase/migrations/20261025000000_ct_step2_documents_bucket_size_alignment.sql`
* `e2e/environment/README.md`, `e2e/environment/scripts/capture_env.sh`

---

## Part B — Live Supabase: the blocked premise is FALSE (read-only proof)

### B.1 What `backend/.env` actually contains

Inventory by **name and value length only** (values redacted; no secret is reproduced anywhere in
this report):

| Variable | Len | Interpretation |
| --- | --- | --- |
| `ENVIRONMENT` | 5 | `local` |
| `SUPABASE_URL` | 22 | `http://127.0.0.1:19999` — the **app's** local API base (**port CLOSED**, see G.2) |
| `SUPABASE_ANON_KEY` | 22 | **not** a JWT (22 chars) |
| `SUPABASE_SERVICE_KEY` | 25 | **not** a JWT (25 chars). *There is no `SUPABASE_SERVICE_ROLE_KEY` variable at all.* |
| `SUPABASE_JWT_SECRET` | 64 | present (local project secret material) |
| `DATABASE_URL` | 63 | **SET, not unset** — resolves to `postgresql://postgres:•••@127.0.0.1:54426/ct_local_93d5cdd` |
| `SUPABASE_LIVE_URL` | 40 | `https://pvwiojoyaqywtydzcpbg.supabase.co` — the **live project** |
| `SUPABASE_LIVE_SERVICE_KEY` | 41 | class `sb_secret_…` — **a live API key** |
| `SUPABASE_LIVE_POSTGRES_DATABASE_URL` | 107 | live DSN via `aws-1-eu-west-2.pooler.supabase.com:5432` (Supavisor), user `postgres.pvwiojoyaqywtydzcpbg` |
| `RESEND_API_KEY` | 36 | provider credential (allow-listed) |
| `SMTP_HOST` | 22 | `mail.carbontally.co.uk` |
| `SMTP_PORT` | 3 | `465` |
| `SMTP_USE_TLS_SSL` | 7 | `SSL/TLS` (**implicit TLS**) |
| `SMTP_USERNAME` | 31 | present (address not reproduced) |
| `SMTP_PASSWORD` | 16 | present (allow-listed credential) |
| `FOUNDER_EMAIL` | 21 | present (address not reproduced) |

The remaining `.env` keys are non-secret application/UI variables (`PORT`, `BROWSER`,
`REACT_APP_API_URL`). The complete key list is: `BROWSER` · `DATABASE_URL` · `ENVIRONMENT` ·
`FOUNDER_EMAIL` · `PORT` · `REACT_APP_API_URL` · `RESEND_API_KEY` · `SMTP_HOST` · `SMTP_PASSWORD` ·
`SMTP_PORT` · `SMTP_USERNAME` · `SMTP_USE_TLS_SSL` · `SUPABASE_ANON_KEY` · `SUPABASE_JWT_SECRET` ·
`SUPABASE_LIVE_POSTGRES_DATABASE_URL` · `SUPABASE_LIVE_SERVICE_KEY` · `SUPABASE_LIVE_URL` ·
`SUPABASE_SERVICE_KEY` · `SUPABASE_URL`.

### B.2 Live Postgres — reachable, read-only

The DSN in `.env` connected successfully to the **live/production** project
(`pvwiojoyaqywtydzcpbg`, which the repository's own
`CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md` identifies as the production project).
Every query was `SELECT`-only.

| Live fact | Value | How |
| --- | --- | --- |
| Public base tables | **134** | `information_schema.tables`, `table_schema='public'`, `BASE TABLE` |
| Canonical head (shipped chain) | **149** | matrix §5.0 / `ct_final02_src` (G.4) |
| **Live schema drift** | **15 tables behind head** | derived |
| `organizations` | **2** | `select count(*)` |
| `auth.users` | **2** | `select count(*)` |
| Non-production / e2e / test identities on live | **0** | `email ilike '%example%' or '%test%' or '%e2e%'` |
| `storage.objects` | **58** | `select count(*)` |
| `storage.buckets` | single row: `documents`, `public=false`, **`file_size_limit = 2097152` (2 MiB)**, `allowed_mime_types = NULL` | `select name, public, file_size_limit, allowed_mime_types` |
| `system_settings` | **exactly 1 row**: `platform_retention`. **No `email_provider` row.** | `select setting_key` |
| Migration ledger `supabase_migrations.schema_migrations` | **71 rows**, head **`20260927000000`** | `count(*)`, `max(version)` |
| Shipped migration files newer than the live head | **23** (from `20260928000000` … `20261025000000`) | repo file inventory (94 files total) |

This **closes the "live schema cannot be confirmed"** clause of the matrix: the live schema *is* now
characterised (134 tables, 23 migrations behind the shipped chain), and it simultaneously reveals a
**previously unrecorded live deployment drift** — the live project is not at the shipped schema head.

### B.3 Live HTTP API — a working live key exists

| Probe (read-only `GET`) | Result |
| --- | --- |
| `GET {LIVE}/rest/v1/organizations?select=id&limit=0` **with** `SUPABASE_LIVE_SERVICE_KEY` | **HTTP 200** |
| same request **without** a key | HTTP 401 |
| `GET {LIVE}/auth/v1/health` (no key) | HTTP 401 |

⇒ A **functional live service key** is present in `backend/.env`. The matrix's claim that live/shared
credentials do not exist in this environment is refuted by direct observation (Part H.1).

### B.4 Why the false premise originated — and what has changed since

The premise is not fabricated; it is **stale**. On **2026-09-11** the repository's own
`CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md` recorded that the live API host was
**unresolvable** (L180 `getent hosts pvwiojoyaqywtydzcpbg.supabase.co` → **NXDOMAIN / FAIL**; L181
`curl …/auth/v1/health` → `Could not resolve host`, HTTP `000`) while still confirming the **production
target identity** as project ref **`pvwiojoyaqywtydzcpbg`** (L20, plus `supabase/.temp/project-ref`).

Today the same host **resolves and serves traffic** (`/rest/v1/…` → 200 with the live key). The correct
reading is therefore: *the live project was genuinely unreachable at the time of the 2026-09-11 audit,
became reachable again, and the FINAL-02 matrix inherited the older premise without re-probing.* This is
exactly the kind of premise an evidence pass exists to correct, and it makes the correction **auditable**
rather than a contradiction of the historical record.

---

## Part C — Live factor library: now directly verifiable (matrix area 9)

The matrix recorded `area 9 … Live/shared factor count unverifiable (B2)`. It is now verified:

| Fact | Value | Source |
| --- | --- | --- |
| Live `emission_factors` | **7,049 rows** | live `select count(*)` |
| Local `ct_final02_src` (head-complete) | **7,049 rows** | local `select count(*)` |
| Local `carbontally_demo_local` | 7,049 rows | local `select count(*)` |
| Local API/demo DB (`postgres`) | 7,049 rows | local `select count(*)` |
| Live `organizations` / `auth.users` | 2 / 2 | live `select count(*)` |

⇒ The live deployment and the head-complete local copy **agree on the factor library (7,049)**, while
disagreeing on **schema head (134 vs 149 tables)** and on the **bucket ceiling (2 MiB live vs 10 MiB in
`ct_final02_src`)**. The factor-library half of the environment parity question is therefore **CLOSED**
as evidence; the schema-tail and bucket-ceiling halves are **open** and itemised in Parts E and I.

---

## Part D — Authentication, JWT and isolation (B5, B4-live, B3): re-status

### D.1 Why the new live credentials do **not** unblock B5

A live service key and a live DSN now demonstrably work (B.2/B.3). The B5 blocker is therefore **not**
"credentials unavailable" — it is narrower and must be restated exactly:

| Requirement for B5 (auth / JWT / RLS isolation matrix) | Status | Evidence |
| --- | --- | --- |
| A reachable live API | ✅ AVAILABLE | 200 (B.3) |
| A live DB session for structural RLS inspection | ✅ AVAILABLE | pooler SELECTs (B.2) |
| **Authorised non-production identities on live** | ❌ **ABSENT** | live e2e/example/test identities = **0** |
| **Authorisation to mint/provision such identities** | ❌ **NOT GRANTED** | FINAL-02 scope excludes provisioning (A.3.4) |
| A second, non-production stack to isolate against | ⚠️ EXISTS BUT NOT SERVING | e2e stack ports 55325/55326 **closed** (G.2) |

⇒ **B5 remains `BLOCKED BY ENVIRONMENT / CREDENTIAL` — refined to: "no authorised non-production
identity exists on any reachable stack, and provisioning is out of scope."** The previous *reason*
("no credentials at all") is withdrawn; the *blocker* stands on the identity clause alone.

### D.2 Why the local stack does not substitute

Although a local Supabase stack is running (G.1), it cannot host an authenticated isolation trial:

* The `.env` local keys are **not valid** for it — `GET /rest/v1/` on the running gateway returned
  **401** for both `SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_KEY` (a keyless request returned 200,
  confirming the gateway itself is up).
* The app's API base `SUPABASE_URL = http://127.0.0.1:19999` is **closed** (G.2), so the application
  cannot reach a local PostgREST/Auth at all.
* The database the application is actually pointed at (`ct_local_93d5cdd`, via `DATABASE_URL`) has **no
  `auth` schema at all** (G.3), so no local sign-in is possible against it either.

⇒ Producing a single authenticated non-production session today would require **reconfiguration and/or
provisioning** — both outside FINAL-02's read-only mandate. **B3 and B4-live remain BLOCKED** for the
same reason, and this pass records *why* precisely.

### D.3 What would unblock B5 (decision for the owner, not taken here)

Either (i) authorise a **local-only** trial against a disposable head-complete database that already
carries `auth` identities (candidates catalogued in G.4), or (ii) authorise provisioning of two isolated
non-production identities. Both are **authorisation decisions**; neither is performed by this pass.

---

## Part E — Storage layer: live state, ceiling direction, and a schema-portability finding

### E.1 Measured bucket state across all reachable environments

| Environment / DB | Bucket | `public` | `file_size_limit` | Notes |
| --- | --- | --- | --- | --- |
| **LIVE** (`pvwiojoyaqywtydzcpbg`) | `documents` | `false` | **2 097 152 (2 MiB)** | 58 `storage.objects` |
| Local API DB (`postgres`, demo) | `documents` | `false` | **NULL** (unset → Supabase default) | 1 206 users / 975 orgs |
| Local `ct_final02_src` (head-complete) | `documents` | `false` | **10 485 760 (10 MiB)** | 149 tables — the ratified end-state |
| Local `carbontally_demo_local` | `report-artifacts` | `false` | 52 428 800 (50 MiB) | different bucket set; 141 tables |
| App DB `ct_local_93d5cdd` | *(storage.buckets present)* | — | **column absent** | see E.3 |
| Local `carbontally_test` | *(storage.buckets present)* | — | **column absent** | see E.3 |

The `documents` bucket is **private in every environment that has it** — the `public=false` invariant is
never violated. The ceiling, however, takes **four different values** depending on environment, which
means *"the bucket ceiling"* is not a single fact and must always be quoted with its environment.

### E.2 The live ceiling is still 2 MiB, and the two shipped migrations move it in **opposite directions**

* `20261024000000_ct_final_01_documents_bucket_size_limit.sql` … **tightens only** (applies the constraint
  in one direction; it does not raise an already-compliant/looser value).
* `20261025000000_ct_step2_documents_bucket_size_alignment.sql` … **aligns in either direction** — i.e. it
  *would raise* the live 2 MiB to the ratified **10 MiB**.

Both files have **not** been applied to live (live ledger head = `20260927000000`; Part B.2), so the live
2 MiB observed value is *pre-migration*. This is consistent with the storage baseline's recorded
`F-3` **conflicting-direction** observation and reproduces it as live measurement, not inference.

**Consequence for acceptance:** applying the shipped chain to live would (a) move the live ceiling
**2 MiB → 10 MiB**, and (b) advance live **23 migrations**, and (c) land **15 new public tables**.
FINAL-02 as scoped observes this; it does not authorise it (FINAL-03 / Storage Step 3 are **NOT
AUTHORIZED**).

### E.3 Finding (observation, not fixed): the documented "deliberate NO-OP" is not portable

Both bucket migrations guard portability with a **table-existence** check
(`IF to_regclass('storage.buckets') IS NULL` → NO-OP). That guard is insufficient on a stack where
`storage.buckets` **exists but predates the `file_size_limit` column**:

* Verified **read-only** on `ct_local_93d5cdd` and `carbontally_test`:
  `select file_size_limit from storage.buckets` → **`ERROR: column "file_size_limit" does not exist`**.

On such a stack the guard passes, the migration proceeds to its `UPDATE`, and it **raises** instead of
taking the documented NO-OP path. This is a **finding for the storage owners**, reported here per the
"stop the portion and report" rule; the migrations were **not** modified and none were applied.

### E.4 Second finding (observation): destructive-reversibility of the *alignment* migration

`20261025000000`'s "align either direction" semantics means its down/rollback direction is not
information-preserving (the prior ceiling value is not captured). This is recorded as an observation only
— see O-2 / C-09 in the storage baseline for the owners' existing treatment.

---

## Part F — SMTP / email provider (B1): the credential premise is FALSE, the *proof* gap stands

### F.1 What is present (redacted)

`backend/.env` contains a **complete, conventionally-named SMTP credential set**: `SMTP_HOST`
(`mail.carbontally.co.uk`), `SMTP_PORT` (`465`), `SMTP_USE_TLS_SSL` (`SSL/TLS`), `SMTP_USERNAME`, and
`SMTP_PASSWORD` — plus `RESEND_API_KEY` and `FOUNDER_EMAIL`. The matrix's B1 statement *"no SMTP
variable/credential in the environment"* is therefore **factually false** and must be corrected (H.2).

What is **still** true, and must not be over-claimed: **no email was sent, no SMTP session was opened,
and delivery readiness on the deployed environment remains unproven.** B1's *blocker* survives; its
*stated reason* does not.

### F.2 Exact provider path (static trace, no execution)

`api → services/v3_email.send_transactional_email` → `resolve_configured_sender` /
`resolve_configured_provider` → `services/email_provider.deliver_email` → `_send_via_smtp` **or**
`_send_via_resend`.

Verified facts:

| # | Fact | Evidence |
| --- | --- | --- |
| 1 | Provider configuration comes from the persisted `system_settings` row keyed **`email_provider`** | `email_provider.py:55`; `data/settings.py:49`, `:490 get_email_provider`, `:508 update_email_provider`, `:554` UPSERT |
| 2 | Provider **selection** is read through the settings repo, not the environment | `v3_email.py:50-58`, `:79`, `:114`; `email_provider.py:513` |
| 3 | Only credential *names* may come from config — restricted to **`RESEND_API_KEY`, `CT_SMTP_PASSWORD`, `SMTP_PASSWORD`** | `email_provider.py:75` (`ALLOWED_CREDENTIAL_ENVS`), `:66-67` (`DEFAULT_CREDENTIAL_ENV`) |
| 4 | The **only** `os.environ` read in the module is the credential value lookup | `email_provider.py:258` |
| 5 | Host/port/username come **only** from the stored row — never from `SMTP_HOST`/`SMTP_PORT`/`SMTP_USERNAME` | `email_provider.py:400-402`; `PROVIDER_FIELDS` `:116-120` |
| 6 | `.env`'s `SMTP_*` values are consumed by the **legacy Node mailer**, a different code path | `services/email.js:4-6` (`nodemailer.createTransport`) |
| 7 | No `email_provider` row exists on **live** (`system_settings` = 1 row, `platform_retention`) | live read-only query (B.2) |

⇒ On the live project the canonical provider path is **unconfigured/defaulted**: even with working SMTP
credentials in `.env`, the path the application actually executes would read host/port/username from a
row that is **absent**. Endpoint A2 (platform email readiness) therefore stays **NOT VERIFIED**.

### F.3 Capability mismatch found (observation, not fixed)

The `.env` transport is **implicit TLS** (`SMTP_PORT=465` + `SMTP_USE_TLS_SSL=SSL/TLS`), but the Python
provider model can only express **`smtp_use_tls: bool`** (`email_provider.py:194-198`, `:216`), and
`_send_via_smtp` opens `smtplib.SMTP(host, port, timeout=…)` followed by an optional `starttls()`
(`:405-408`) — i.e. **STARTTLS**, default port `587` (`:79`). There is **no `smtplib.SMTP_SSL`** path.

⇒ **Implicit TLS (465/SMTPS) is not expressible or performed by the provider path.** A stored config of
port 465 would attempt STARTTLS on an implicit-TLS port. Reported as a finding; **no connection was made
to confirm it live**, and nothing was changed. (Related deferred item: the unreachable success branch at
`services/email_service.py:202` — unchanged.)

---

## Part G — Local environment catalogue (read-only; nothing provisioned)

### G.1 Running containers

| Container | Published | Role |
| --- | --- | --- |
| `supabase_db_carbon_ledger` | `54426→5432` | the local Postgres instance hosting **all 81 databases** below |
| `supabase_kong_carbon_ledger` | `54425→8000` | API gateway (up — keyless `GET /rest/v1/` → 200) |
| `supabase_rest_carbon_ledger` | *internal 3000* | PostgREST |
| `supabase_storage_carbon_ledger` | *internal 5000* | Storage API |
| `supabase_auth_carbon_ledger` | *internal 9999* | GoTrue |
| `supabase_realtime_carbon_ledger` / `supabase_pg_meta_carbon_ledger` / `supabase_inbucket_carbon_ledger` | *internal* | Realtime / pg-meta / mail catcher |
| `supabase_studio_carbon_ledger` | `54423→3000` | Studio |
| `carbontally_demo_lab_gateway` (+`_postgrest`, `_storage`) | `54430→80`, internal rest/storage | a **second, independent** demo lab |
| `hindsight-carbontally` | `8888`, `9999` | unrelated tooling |
| `n8n-n8n-1` | `5678` | unrelated tooling |

### G.2 Listener probes (loopback)

| Port | State | Significance |
| --- | --- | --- |
| **19999** | **CLOSED** | the app's `SUPABASE_URL` target — **the application cannot reach a Supabase API** |
| 5432 | OPEN | pre-existing Postgres |
| 54423 / 54425 / 54426 | OPEN | local stack studio / gateway / DB |
| 54430 | OPEN | demo lab gateway |
| 5678 | OPEN | n8n |
| **55325 / 55326** | **CLOSED** | **the isolated e2e stack is NOT running** — nothing for B5 to authenticate against |

### G.3 The database the application is actually wired to is *not* the demo database

`DATABASE_URL` → `127.0.0.1:54426/ct_local_93d5cdd` (PostgreSQL **17.6**, `current_database()` and
`server_version` confirmed).
That database is a **schema-only rehearsal database**, not a working Supabase project:

| `ct_local_93d5cdd` (app DB) | Measured |
| --- | --- |
| Public base tables | **135** |
| `auth` schema / `auth.users` | **ABSENT** (`relation "auth.users" does not exist`) |
| `supabase_migrations` schema | **ABSENT** |
| `emission_factors` rows | **0** |
| `storage.buckets` | present, **without `file_size_limit`** (E.3) |
| `system_settings` | 1 row (`platform_retention`) |
| `d32_documents%` policies | 4 |

Meanwhile the **Supabase API** (Kong 54425 / PostgREST) serves a *different* database — the demo
`postgres` DB. So locally: **app DB ≠ API DB**, the app's API base is a closed port, and the app DB has
no Auth schema. This is an **environment-configuration incoherence** (recorded, not remediated) and is the
mechanical reason no local authenticated session can be obtained (D.2).

### G.4 Candidate disposable databases (catalogued, **not** provisioned or modified)

81 databases exist on the local instance, including ~70 `ct_*` rehearsal databases. The four most relevant:

| Database | Tables | `auth.users` | `emission_factors` | `documents` ceiling | Note |
| --- | --- | --- | --- | --- | --- |
| `ct_final02_src` | **149** (= head) | 1 206 | 7 049 | **10 MiB** | **head-complete** — the ratified end-state reference |
| `postgres` (API/demo) | 116 | 1 206 | 7 049 | NULL | what Kong/PostgREST actually serves; 975 orgs; 9 e2e-ish identities |
| `carbontally_demo_local` | 141 | 14 | 7 049 | `report-artifacts` 50 MiB | near-head; different bucket set |
| `carbontally_test` | 117 | **ABSENT** | 27 | column absent | thin fixture DB |
| `ct_local_93d5cdd` | 135 | **ABSENT** | 0 | column absent | the **app-wired** DB (G.3) |

⇒ A head-complete non-production database (`ct_final02_src`) **does** exist locally, so a future
local-only trial needs **no new provisioning** — only authorisation (D.3). Nothing was created, altered
or dropped by this pass.

### G.5 e2e harness

`e2e/environment/` establishes the harness contract; `scripts/capture_env.sh` captures the environment.
The harness defines the identity **keys** (`E2E_ORG_OWNER_EMAIL`, `E2E_ORG_B_OWNER_EMAIL`,
`E2E_ORG_ADMIN_EMAIL`, `E2E_ORG_VIEWER_EMAIL`, `E2E_ORG_MEMBER_EMAIL`, `E2E_CONSULTANT_A_EMAIL`,
`E2E_CONSULTANT_B_EMAIL`, `E2E_INTERNAL_QC_EMAIL`, `E2E_INTERNAL_OPS_EMAIL`, `E2E_PE_A_EMAIL`,
`E2E_PE_B_EMAIL`, `E2E_PE_A_STAFF_EMAIL`, `E2E_ORG_B_MEMBER_EMAIL`; per-role password variables such as
`E2E_PASSWORD`; plus `E2E_API_URL`, `E2E_SUPABASE_URL`, `E2E_ANON_KEY`, `E2E_SERVICE_ROLE_KEY`,
`E2E_DB_URL`). **Definitions exist; no value was read, printed, or used, and no identity was seeded.**

⇒ The e2e path is **specified but not served** today (55325/55326 closed). It is therefore *available as a
future vehicle*, not as current evidence.

---

## Part H — Documentation correction set (additive; historical text preserved)

**Rule applied:** the verifier-authored matrix and IV report are **not edited**. The corrections below are
stated as a *delta* for the verifier/owners to fold in, quoting the original line verbatim so the
historical record remains intact. Line numbers refer to
`CT-FINAL-02-20260930-REHEARSAL-BASELINE-AND-GAP-MATRIX.md`.

### H.1 Matrix L515–516 (§5.7) — **FALSE premise (5 clauses)**

> *Original:* "No live/shared credentials exist in this environment (`SUPABASE_URL`,
> `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, `SUPABASE_DB_URL` unset; `backend/.env` points only at
> `127.0.0.1`)."

**Correction:** live/shared credentials **do** exist in `backend/.env`: `SUPABASE_LIVE_URL`
(`https://pvwiojoyaqywtydzcpbg.supabase.co`) and a **working** `SUPABASE_LIVE_SERVICE_KEY` (HTTP 200 on a
read-only PostgREST request, B.3), plus `SUPABASE_LIVE_POSTGRES_DATABASE_URL` (live Supavisor pooler,
read-only SELECTs succeeded, B.2). Of the four names quoted: `DATABASE_URL` is **set** (to
`127.0.0.1:54426/ct_local_93d5cdd`), `SUPABASE_URL` **is** set (to `127.0.0.1:19999`), the variable name
`SUPABASE_SERVICE_ROLE_KEY` **does not exist** in this repo's `.env` (only `SUPABASE_SERVICE_KEY`), and
`SUPABASE_DB_URL` is indeed absent. The claim that `.env` "points only at `127.0.0.1`" is false — it
carries three live-project variables. **Still true and unchanged:** no managed-backup tier, PITR window or
last-successful-backup evidence was obtained (a DB DSN alone cannot answer drill §7 (a)–(e); a management
API token would be required).

### H.2 Matrix L563 (blocker **B1**) — reason false, blocker open

> *Original:* "| B1 | A2Hosting SMTP credential/configuration unavailable | **Unchanged** (no SMTP
> variable/credential in the environment) | …"

**Correction:** a complete SMTP credential set **is** present in `backend/.env` (`SMTP_HOST`,
`SMTP_PORT`, `SMTP_USE_TLS_SSL`, `SMTP_USERNAME`, `SMTP_PASSWORD`) plus `RESEND_API_KEY` (Part F.1).
The **blocker stands for a narrower reason**: no controlled send has been performed, and the live
`system_settings` has **no `email_provider` row**, so the deployed provider path is unconfigured/defaulted
(F.2). Restated B1: *"External email delivery is unproven because no controlled send has been performed;
the canonical provider path has no persisted configuration on the live project."*

### H.3 Matrix L564 (blocker **B2**) — reason false; impact partly CLOSED

> *Original:* "| B2 | Live/shared Supabase credentials unavailable | **Unchanged** (all Supabase/DSN
> variables unset; `.env` localhost-only) | Live factor count, live schema and managed backup/PITR cannot
> be confirmed | Provide a read-only live connection |"

**Correction:** the **required action has been satisfied** — a read-only live connection exists and was
used. Two of the three impacts are now **CLOSED**: live factor count = **7,049** (Part C) and live schema =
**134 public tables, ledger head `20260927000000`, 23 migrations behind head** (Part B.2). Only the
**managed backup/PITR** third remains unconfirmed. B2 as worded should be **retired and replaced** by
*"B2′ — managed backup/PITR evidence unavailable (needs a management API token, not a DB DSN)."*

### H.4 Matrix L183 (area 2) — false gap

> *Original gap:* "Live/shared project configuration is unreachable from this environment"

**Correction:** live configuration **is** reachable read-only (B.2/B.3). The area-2 status should move from
"partially verified / operational dependency" to **VERIFIED (read-only)**, with the newly measured live
values recorded (134 tables; `documents` private; `file_size_limit` 2 MiB; 58 objects; 2 orgs; 2 users).

### H.5 Matrix L190 (area 9) — gap closed

> *Original gap:* "Live/shared factor count unverifiable (B2)"

**Correction:** live `emission_factors` = **7,049**, matching the local head-complete copy exactly (Part C).
Area 9's live clause is **closed as evidence**.

### H.6 Matrix L544–545 (§5.11 item 4) — correct but incomplete

> *Original:* "Apply `20261024000000` / `20261025000000` at deployment (the live bucket ceiling is only
> pinned once they are applied through the authorised process)."

**Correction:** the live ceiling is **already pinned at 2 MiB** (`2097152`) *before* those migrations; the
two files move it in **opposite directions** and the *alignment* migration would **raise live to 10 MiB**.
Applying them therefore has a **ratified-value-changing effect on production**, not merely a
"pin it for the first time" effect. Also note the portability caveat is now *proven*, not hypothesised
(E.3).

### H.7 Matrix L182 (area 1) — accurate but incomplete

> *Original:* "Local Postgres 17.6 reachable; 116 public tables; 7,049 factors …"

**Addendum (not a correction):** 116 tables correctly describes the **API/demo** database (`postgres`)
that Kong/PostgREST serves. The database the **application is wired to** (`DATABASE_URL` →
`ct_local_93d5cdd`) is a **different** database with **135** tables, **no `auth` schema**, **0** factor
rows and a `storage.buckets` **without** `file_size_limit` (G.3). This distinction is absent from the
matrix and is material to B6 and to any local trial.

### H.8 Matrix L507–510 (§5.6) and L594–597 (deferred item 9) — confirmed; strengthened

* §5.6's "on a stack whose storage schema predates that column they raise a column error instead of the
  documented no-op (**observation only**)" is now **measured** on two local databases (E.3) — the guard is
  a *table-existence* guard, so it does not prevent the raise. Recommend promoting the observation to a
  **tracked finding** for the storage owners.
* Deferred item 9 is **reproduced exactly** (local API DB: 46 ledger rows, latest `20260903010000`, 116
  tables). Add: the **app-wired** DB has **no `supabase_migrations` schema at all**.

### H.9 Statements that remain **UNCHANGED** and must not be softened

Matrix L556–559 (carry-forward basis), L566 (**B4** — implementation verified, live proof outstanding),
L567 (**B5**), L568 (**B6**), L570–572 ("not blockers" list), L585–587 (Storage Step 2 §20.1 observations
stay non-blocking), L592 (dead-code note), and the entire IV report (verifier-owned; **not edited**).

---

## Part I — Blocker re-status after live evidence (B1–B6)

| # | Blocker | Before | **After this pass** | Evidence | What closes it |
| --- | --- | --- | --- | --- | --- |
| **B1** | External email delivery unverified | BLOCKED — *"credential unavailable"* | **BLOCKED (narrowed)** — credential **present**; blocker is *no controlled send* + *no `email_provider` row on live* | F.1, F.2, B.2 | One authorised controlled send via the canonical path |
| **B2** | Live/shared Supabase evidence | BLOCKED — *"credentials unavailable"* | **RESOLVED (mostly)** — live factor count ✅, live schema ✅; **B2′** managed backup/PITR remains | B.2, B.3, C | Management-API backup/PITR evidence |
| **B3** | No admin test credentials / authenticated session | BLOCKED | **BLOCKED (unchanged, reason now exact)** — no valid local keys, app API port closed, app DB has no `auth` schema | D.2, G.2, G.3 | Authorise a non-production admin login |
| **B4** | D-7 inactive-org denial — *live/RLS proof only* | BLOCKED (live proof) | **BLOCKED (unchanged)** — implementation verified; live proof needs a minted non-prod JWT | D.1, D.2 | Same vehicle as B5 |
| **B5** | Storage/JWT isolation matrix | BLOCKED | **BLOCKED — but now *derivable without provisioning***: a head-complete local DB (`ct_final02_src`) already exists | D.1, G.4 | Authorise a local-only trial against `ct_final02_src` |
| **B6** | Local rehearsal DB not at schema head | OPEN (116/149; 33 behind) | **OPEN, refined** — the *app-wired* DB is a different, thinner DB (135 tables, no Auth schema, 0 factors) | H.7, G.3 | Bring the local dev stack forward / use the head-complete copy |

**Kept as non-blockers (do not promote):** the two bucket migrations not being applied to live
(deployment dependency — but see E.2/H.6 for its production effect), storage-object byte backup (provider
dependency), RPO/RTO (PO decision), the 7 pre-existing unit failures (documented), destructive retention
(deferred by decision).

**New factual additions recorded this pass (not blockers, previously unknown):**

1. **Live deployment drift** — production is **23 migrations / 15 public tables behind** the shipped chain
   (B.2). Previously unrecorded.
2. **Live storage ceiling is 2 MiB**, and the shipped *alignment* migration would **raise production to
   10 MiB** (E.2).
3. **Local environment incoherence** — `SUPABASE_URL` points at a **closed** port; the app's `DATABASE_URL`
   points at a DB with **no `auth` schema**; the API serves a *different* DB (G.2, G.3).
4. **Portability finding** — the bucket migrations' NO-OP guard is **table-existence only** and does not
   prevent a raise on stacks lacking `file_size_limit` (E.3).
5. **Capability finding** — the provider path cannot express **implicit TLS (465/SMTPS)** (F.3).

---

## Part J — Guardrails, deliverables, and handoff

### J.1 Guardrails honoured (self-audit)

| Guardrail | Status |
| --- | --- |
| No production mutation | ✅ — live work was `SELECT`/`GET` only |
| No migration applied (live, local or disposable) | ✅ |
| No credential or PII disclosed | ✅ — names, lengths, key-class prefixes and hosts only |
| No email sent; no SMTP session opened | ✅ — static trace only |
| No identity/user/org/bucket/database provisioned | ✅ — pre-existing databases **catalogued only** |
| Verifier-authored documents not edited | ✅ — corrections filed additively (Part H) |
| Findings reported, not fixed | ✅ — E.3, E.4, F.3 |
| **FINAL-02 not closed** | ✅ — remains **OPEN** |

### J.2 Deliverables

* **This report** — `docs/architecture/CT-FINAL-02-20261001-LIVE-EVIDENCE-CLOSURE-PASS-REPORT.md`
  (Parts A–J). It is a **new** file; no existing document was modified.
* A reproducible, redacted evidence set (all read-only): live Postgres/API probes, local container and
  port probes, local database catalogue, SMTP code trace.

### J.3 Decisions that remain with the owners (not taken here)

1. **Authorise a controlled email send** (or accept delivery as an operational dependency) → closes B1.
2. **Authorise a local-only isolation trial** against the existing head-complete `ct_final02_src`
   database, or authorise minting non-production identities → closes B5/B4-live/B3 **without any new
   provisioning**.
3. **Authorise management-API backup/PITR evidence retrieval** → closes B2′.
4. **Decide the local-dev-stack question** (`ct_local_93d5cdd` has no Auth schema, 0 factors, a closed API
   port, and a pre-`file_size_limit` storage schema) → closes B6 and removes a recurring source of
   rehearsal confusion.
5. **Route E.3/E.4/F.3** to the storage and email owners as findings.
6. **Fold the Part H corrections** into the matrix (the verifier's document is theirs to amend).

### J.4 What this pass deliberately did **not** do

It did **not** apply `20261024000000`/`20261025000000`, did **not** deploy anything, did **not** build a
rehearsal stack, did **not** seed identities, did **not** send email, did **not** retrieve backup
metadata, and did **not** close, downgrade or re-scope FINAL-02.

### J.5 Recommended disposition

Independent acceptance can now be **re-run against corrected premises**. The previous acceptance basis
rested on a demonstrably false "credentials unavailable" premise for B1 and B2; that premise is withdrawn
(Part H), while B3/B4-live/B5 remain genuine, now precisely-scoped environment blockers, and B6 is refined
by a newly-discovered app-DB/API-DB incoherence (G.3/H.7).

---

## Final status

> **FINAL-02 LIVE EVIDENCE CLOSURE PASS COMPLETE — READY FOR UPDATED INDEPENDENT ACCEPTANCE.**
>
> Read-only live, local and e2e verification is complete; the false "credentials unavailable" premises
> (matrix §5.7, areas 2 and 9, blockers B1 and B2) are corrected with direct evidence; B3/B4-live/B5 are
> restated as precise, still-open environment blockers that can be closed **without further provisioning**;
> B6 is refined.
>
> **No implementation, mutation, provisioning or email delivery was performed, and FINAL-02 remains OPEN
> — it is not closed by this pass.**
>
> Governance unchanged: FINAL-01 **CLOSED** · Storage Steps 1+2 **CLOSED** · Storage Step 3 / FINAL-03
> **NOT AUTHORIZED** · FINAL-02 **OPEN** (awaiting updated independent acceptance).









