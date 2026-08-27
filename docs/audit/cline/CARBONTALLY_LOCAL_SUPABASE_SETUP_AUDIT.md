---
Document Type: Local Supabase Environment Setup Audit
Project: CarbonTally
Context: Source moved from Windows to Ubuntu; goal = local Supabase → Auth → Postgres → Storage/Realtime → test users → run V3 frontend → live-DB integration/E2E
Version: 1.0
Status: AUDIT/PLAN ONLY — nothing modified (no code, migrations, RLS, remote, or test users)
Created: 2026-08-20
Author: Cline
Strict scope: NO remote Supabase writes; NO production data copy; NO test-user creation; NO Phase 9.
---

# CarbonTally — Local Supabase Environment Setup Audit

Host: Ubuntu 26.04 LTS (`uname` x86_64, kernel 7.0.0-30-generic).
Goal: reproduce the entire CarbonTally V3 stack locally, run the V3 frontend, and
execute live-DB (integration / E2E) tests against a disposable local Supabase —
without touching the live project.

---

## 0. Executive summary

- The repository **already contains a proper, initialized Supabase CLI project**
  (`supabase/config.toml` + 21 tracked `supabase/migrations/*.sql` + `seed.sql`).
  **Do NOT run `supabase init`.**
- That project is **linked to the LIVE remote** (`.temp/linked-project.json` ref
  `pvwiojoyaqywtydzcpbg` — CarbonTally, eu-west-2, DB 17.6). The local stack has
  **never** been started on this machine (no `.supabase/` dir).
- The schema migration chain **materialises the intended V3 schema** (table-level
  comparison: migrations = v3_schema.sql = 104 tables; V3M2 root dump = 102 and is
  only 2 tables behind — `customer_factors`, `issues`). **Migrations are the
  correct local build source.**
- **Critical environment gaps (blockers):** Docker, Supabase CLI, and Node.js are
  ALL missing on this Ubuntu box. Python 3.14.4 is present (backend historically
  pinned 3.11.9). Nothing can start until these are installed (see §15).
- **Security hazard:** `supabase/seed.sql` is a **production pg_dump** (auth +
  storage + public data shapes) and is git-tracked. It MUST NOT be used as a seed.
  `backend/carbon_tally_backup.sql` / `_data.sql` are additional production backups
  (correctly gitignored, but present on disk).
- The integration suite is **already pre-wired for local ports**: DB
  `postgresql://postgres:postgres@127.0.0.1:54326/postgres`, API
  `http://127.0.0.1:54325` — exactly the ports in `config.toml`.

**Verdict:** The surviving `supabase/` project is usable as the local bedrock.
Finish the audit by installing Docker + Supabase CLI + Node, then
`supabase start` → `supabase db reset` → capture local keys → wire `.env` for
backend/frontend/admin → seed controlled dev data → run integration/E2E.

---

## 1. Existing Supabase setup

| Item | Finding |
|---|---|
| OS | Ubuntu 26.04 LTS, x86_64 |
| `supabase/` dir | **Exists** — a CLI-initialised project (config.toml, migrations/, seed.sql, .html-snippets/). project_id = `carbon_ledger` |
| `supabase/config.toml` | Present. api.port=**54325**, db.port=**54326**, db.shadow_port=54320, db.major_version=**17**, [db.migrations] enabled, [db.seed] enabled=false, [auth] enabled (site_url http://localhost:3000), [realtime] enabled, [storage] (default), [edge_runtime] enabled=true (no functions) |
| Migrations | 21 tracked files in `supabase/migrations/` (see §2) |
| `supabase/seed.sql` | **Present but disabled** (`[db.seed] enabled=false`) |
| Local stack launched? | **NO** — `.supabase/` does not exist |
| Remote link | **YES** — `.temp/linked-project.json`, `.temp/project-ref`, pgdelta catalog present → the CLI has linked the remote project |
| Backend client | `backend/config.py`, `backend/database.py`, `backend/auth.py`, `backend/infra/supabase.py` all `create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)` — service-role client |
| Frontend client | Create React App (`react-scripts` 5.0.1); `src/supabaseClient.js` uses `createClient(REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY)` |
| Admin client | `admin/src/supabaseClient.js` uses `createClient(REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY)` |

> A local `postgres` (`.tmp_pgdata/`, tmp_pg* probes) was attempted at some point
> in the prior (Windows-era) session, but that is NOT the Supabase local stack and
> is not running now.

---

## 2. Existing migrations (`supabase/migrations/`, authoritative)

| # | File | Purpose |
|---|---|---|
| 1 | `00000000000000_init_schema.sql` (80 KB) | Full baseline schema (public, extensions, grants) |
|---|---|---|
| 2–8 | `2026080…_rc2_schema`, `_rc2_constraints`, `_rc2_indexes`, `_rc2_rls`, `_rc2_functions`, `_rc2_triggers`, `_rc2_verification` | RC2 layer (RLS + functions + verification) |
| 9–16 | `20260807000000_add_import_batches` … `add_new_table_rls` | Incremental V2.1 additions (snapshots, domain_events, factor_aliases, dpq columns) |
| 17–21 | `20260810000000_v3m1_processing_entities`, `_v3m2_entity_relationships`, `_v3m3_customer_factors`, `_v3m5_issues`, `_v3m6_entity_rls` | V3 module migrations |

- `[db.migrations] enabled=true` → migrations WILL replay on `supabase db reset`.
- The RC2 `why-not-CONCURRENTLY` notes confirm these were written for the Supabase
  migration runner (`db reset`), i.e. **they are the intended build source.**
---

## 3. Existing schema files

| File | Kind | Tables (table-level scan) |
|---|---|---|
| `supabase/migrations/*.sql` | Declarative migration chain (authoritative) | 104 |
| `CarbonTally_DB_Schema_V3M2.sql` (root) | Single-file full `pg_dump` snapshot | 102 |
| `v3_schema.sql` (root) | Single-file full dump (latest) | 104 |
| `database/rc1/` (001–007) | RC1 pack (delta) | subset |
| `database/rc2/` (000–007 + release notes) | RC2 pack (delta; only 14 tables captured) | subset |
| `database/v3/verification_v3m1_v3m2.sql` | V3 verification | — |
| `backend/carbon_tally_backup.sql` + `_data.sql` | Gitignored production backups (present on disk) | — |

`docs/architecture/README.md` documents the (stale) local-dev flow: `cp .env EXAMPLE
.env`, `uvicorn main:app…`, `npm start`. **No `.env.example` actually exists** in
any package (backend/frontend/admin/root) — those docs are aspirational; real
`.env*` files are present locally but properly `.gitignore`d.

---

## 4. Remote / local schema relationship

- The Supabase CLI project is **linked to the live project** (ref
  `pvwiojoyaqywtydzcpbg`, region eu-west-2). The migrations already mirror the
  remote V3M2/V3 schema structure (same 104-table target set).
- `config.toml` sets `db.major_version = 17` — **matches** the remote pooler DB
  version 17.6 (local PostgreSQL 17 is therefore correct).
- Application expectation: the backend V3 repositories read/write the V3M2/V3
  tables (`processing_entities`, `customer_factors`, `calculation_snapshots`,
  `emissions_logs`, `report_generation_queue`, `report_versions`,
  `processing_queue`, `issues`, RLS helpers, etc.). These all exist in the
  **migrations** chain (and in `v3_schema.sql`).

## 5. Schema drift (table-level)

| Pair | In common | Only in A (absent B) | Only in B (absent A) | Verdict |
|---|---|---|---|---|
| Migrations ↔ `v3_schema.sql` | 104/104 | none | none | **MATCH** |
| Migrations ↔ `V3M2(root)` | 102 | `customer_factors`, `issues` (in migrations, absent in V3M2 root dump) | none | **DRIFT** — V3M2 root dump is 2 tables behind (predates V3M3/V3M5) |
| Migrations ↔ `database/rc2/` | 14 | ~100 tables present in migrations but absent in the rc2 delta pack | none | **DRIFT (by design)** — `database/rc2/` is the RC2 delta pack, not a full baseline; do NOT build from it |
| Remote ↔ local | — | Cannot compare without `supabase db pull` / studio access | — | **UNKNOWN** (never used remote modifications) |

- **Interpretation:** the git-tracked `supabase/migrations/` chain is the single
  buildable source of truth for the intended V3 schema. The root dumps are
  reference snapshots, not build inputs.
- **Recommendation:** build the local DB *from the migrations* (via
  `supabase db reset`), never by invoking the root dump files, and never by
  bulk-copying the remote.

---

## 6. Required local dependencies

| Dependency | Status here | Needed for |
|---|---|---|
| Docker (or podman-docker) | **NOT installed** | Supabase local stack (Postgres/Auth/Storage/Realtime/Studio) |
| Supabase CLI | **NOT installed** | `supabase start / db reset / status / db apply` |
| Node.js + npm | **NOT installed** | Frontend (`npm start`) and admin |
| Python 3.11.x (venv) | **Only 3.14.4 present** | Backend; historically pinned 3.11.9 (requirements) |
| Python packages | not installed yet | `supabase`, `asyncpg`, `fastapi`, `pytest`, **`pytest-asyncio`** (needed for integration/async unit suites; documented as missing in the resumption report) |
| Network | presumably available | Package / CLI / Docker-image downloads (UNVERIFIED) |

## 7. Docker status

- **Not installed, not running.** `docker` is absent; `systemctl status docker`
  reports no service. Ubuntu offers `apt install docker.io` (Docker 29.1.3) or
  `apt install podman-docker` (5.7.0).
- Docker on Ubuntu additionally needs a **virtualisation-capable CPU/BIOS** (VT-x /
  AMD-V) and a running daemon. This should be confirmed at install (a common
  blocker on bare-metal Ubuntu).

## 8. Supabase CLI status

- **Not installed.** No `supabase` binary; `go` and `dart` also absent (the CLI is
  a native Dart/Go binary, not pip). Needs to be installed from the official
  release (e.g. GitHub release binary for Linux), then placed on `PATH`.

## 9. Local environment plan

The existing `supabase/` initialised project is the bedrock — **NO `supabase init`.**

1. **Install:** Docker (or podman-docker) + Supabase CLI + Node (see §15 blockers).
2. **Start stack:** `supabase start` (uses `config.toml`: api :54325, db :54326,
   Postgres 17; walks up Auth, Storage, Realtime, Studio).
3. **Apply schema:** `supabase db reset` — replays the 21-migration chain into the
   **local** DB. (Never `--linked`.)
4. **Capture keys:** `supabase status` → local API URL, anon key, service-role key
   (+ JWT secret). The local anon/service keys and JWT secret are the well-known
   local Supabase CLI defaults unless overridden.
5. **Wire env** (below) for backend / frontend / admin. **Frontend anon ≠ backend
   service; never put the service key in any frontend/`.env` consumed by JS.**
6. **Seed controlled dev data** (see §13). Then run test users (deferred; §13).
7. **Run:** backend (uvicorn :8000), frontend (`npm start` :3000), admin
   (`npm start` :3001), integration suite (`pytest tests/integration`).

### 9.1 Expected local wiring (audit of code + conftest)

| Consumer | Port / var | Value (local) |
|---|---|---|
| Backend (api + v3) | `SUPABASE_URL` | `http://127.0.0.1:54325` |
| Backend service client | `SUPABASE_SERVICE_KEY` | local **service-role** key |
| Backend JWT verify | `SUPABASE_JWT_SECRET` | local JWT secret (set to match local auth) |
| Backend direct DB (asyncpg) | `DATABASE_URL` | `postgresql://postgres:postgres@127.0.0.1:54326/postgres` |
| Integration tests | `INTEGRATION_DATABASE_URL` | defaults to the same `:54326`; `SUPABASE_URL` `http://127.0.0.1:54325` (already set in `tests/integration/conftest.py`) |
| Frontend (CRA) | `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY` / `REACT_APP_API_URL` | `http://127.0.0.1:54325` / local **anon** / `http://localhost:8000` |
| Admin (CRA) | same `REACT_APP_*` | same local values |

> Frontend is Create React App (`react-scripts`), so the `REACT_APP_*` vars must
> live in a file CRA reads at its own root (`frontend/.env` / `frontend/.env.local`
> depending on package) with the `REACT_APP_` prefix; the root `.env` does not feed
> it. `v3/api.js` falls back to `http://localhost:8000` for `REACT_APP_API_URL`.

### 9.2 Auth wiring (Supabase Auth → app)

- Backend validates JWT via `SUPABASE_SERVICE_KEY` client + `SUPABASE_JWT_SECRET`
  (`backend/auth.py` `create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)`).
- Frontend uses `supabase.auth` from `@supabase/supabase-js` with the **anon** key
  (never service). Local auth runs on the local gateway (`/auth/v1`).

---

## 10. Auth plan (local Supabase Auth)

- **Keep local Auth enabled** (`[auth] enabled = true` in `config.toml`, site_url
  `http://localhost:3000`). Email/password + the Supabase anon-key flow work
  against the local Gotrue (`/auth/v1`). All OAuth providers are disabled in
  config → local auth is email/password by default (matches the V3 unit fakes).
- **Keys:** frontend uses the **anon** key (embedded in the JS client, publicly
  readable by design); backend uses the **service-role** key (server-only).
  **Never** compile the service-role key into frontend/admin.
- **JWT:** backend verifies tokens via `SUPABASE_SERVICE_KEY` + `SUPABASE_JWT_SECRET`
  (set both env vars to the local values emitted by `supabase status` / config so
  the app validates local-signature tokens, not the remote secret).
- **Test users:** creation is deferred (STRICT RULE). When permitted, create
  **only local** users via `supabase.auth.sign_up` (or direct SQL into the local
  `auth.users`), one per intended role (customer/owner, org-admin, staff,
  operator/reviewer/QC, consultant), with **fake** identities — none drawn from any
  production record. `/backend/tests/create_test_users.py`,
  `.../setup_test_data.py`, `.../setup_test_orgs.py` already exist as a starting
  point but must be repointed at local Supabase and use only synthesised data.

## 11. Storage plan

- CarbonTally uploads documents to a **single** Supabase Storage bucket named
  **`documents`** (`supabase.storage.from_('documents').upload/get_public_url` in
  `backend/api/v3_documents.py`, `backend/routes/upload.py`,
  `backend/routes/organizations/files.py`). The multi-bucket design
  (`temp-uploads`, `generated-reports`, `ai-temp`) exists only in an aspirational
  doc for a different architecture and is NOT used here.
- **Local:** after `supabase start`, create the `documents` bucket locally if it is
  not auto-created so the upload paths succeed. Local-only; do NOT add a remote
  bucket or alter remote storage policies.
- Keep bucket RLS as local-default; the app stores paths in
  `organization_files` / `customer_documents` rows.

## 12. Realtime plan

- **Keep local Realtime enabled** (`[realtime] enabled = true` in `config.toml`).
  The V3/admin frontends subscribe to Postgres changes (notifications, staff
  presence, chat) via `@supabase/supabase-js` / `RealtimeContext` +
  `lib/realtime/manager.js`. Local Realtime covers these out of the box.
- **Edge runtime (`[edge_runtime] enabled=true`) is unused** (no
  `supabase/functions` exist). It can stay on (harmless) or be disabled later; not
  required.
## 13. Test-data strategy (local only)

- **Schema via migrations** only (`supabase db reset`); never from the root dump
  files or a remote copy.
- **Dev data via a controlled local seed** — do NOT use `supabase/seed.sql` (it is
  a live-database `pg_dump`: auth/storage/public data shapes, a `restrict` marker,
  version 17.6). Keep `[db.seed] enabled=false` until a purpose-built dev seed is
  created (STRICT RULE defers creation here).
- **Emission-factor baseline:** the integration conftest says the factor baseline
  is re-imported after `db reset`. Favour importing reference/SEAI/DEFRA factor
  data already in the repo (`output/json/emission_factors.json`, `demodatagen/`,
  `docs/cline/*SEAI*`) as controlled data — never customer/supplier PII.
- **Demo data:** `demodatagen/` supplies controlled generators for organisations,
  factors, demo records — the intended source for local non-secret rows.
- **Do NOT copy:** real customers, users/emails, logins/sessions, personal info,
  secrets, or any production authentication rows. This includes guarding the
  on-disk `backend/carbon_tally_backup*.sql` and the `seed.sql` dump.

## 14. Security precautions

- `.env*` are gitignored (good); `.env.example` is allow-listed but **does not
  exist** — a canonical placeholder `.env.example` is a follow-on.
- **Past issue (Render audit):** an earlier tracked `backend/.env` set
  `SUPABASE_ANON_KEY`/`VITE_SUPABASE_ANON_KEY` to the **service-role** value and
  held a real credential. For local: anon (frontend) ≠ service (backend); never
  mirror service into a frontend/shared var; rotate any exposed key.
- `frontend/src/supabaseClient.js` and `admin/src/supabaseClient.js` should read
  keys from env; a hard-coded `sb_publishable_…` appears in `frontend/src/…` —
  prefer env-driven / publishable-only usage.
- **Remote safety:** project is **linked to live** (`pvwiojoyaqywtydzcpbg`). Only
  local `supabase start / stop / db reset(no --linked) / status / db apply` are
  permitted. Confirms before any remote-adjacent action (§16). Optionally
  `supabase unlink` after remote-only metadata is captured (local-only metadata,
  safe, but not required).
- Never commit local secrets; never set Docker/Node production secrets in local
  dev files that ever get committed.
---

## 15. Exact commands required

```bash
# ===== install prerequisites (needs sudo; confirm VT-x/AMD-V on the host) =====
sudo apt update
sudo apt install -y docker.io                 # or: sudo apt install -y podman-docker
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"               # re-login after this

# + Supabase CLI from the official release (NOT apt/pip):
#   download the Linux x86_64/arm64 release binary to ~/.local/bin
chmod +x ~/.local/bin/supabase
supabase --version

# + Node.js / npm (needed for frontend + admin)
sudo apt install -y nodejs npm
node --version && npm --version

# + backend venv + deps (Python 3.11 recommended if available on 3.14)
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
pip install pytest-asyncio

# ===== start the local Supabase stack (project already initialised -> NO init) =====
supabase start            # api :54325, db :54326, PG major 17
supabase status           # print local api url, anon key, service key

# ===== build the V3 schema from migrations (LOCAL only; never --linked) =====
supabase db reset         # replays the 21-migration chain into local postgres

# ===== create the 'documents' storage bucket locally (if not auto-created) =====
# via Studio http://127.0.0.1:54323 or a `supabase` SQL script (local only)

# ===== local env files (gitignored) =====
# backend/.env :
#   SUPABASE_URL=http://127.0.0.1:54325
#   SUPABASE_SERVICE_KEY=<local service-role key>
#   SUPABASE_JWT_SECRET=<local JWT secret>
#   DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54326/postgres
# frontend/.env :
#   REACT_APP_SUPABASE_URL=http://127.0.0.1:54325
#   REACT_APP_SUPABASE_ANON_KEY=<local anon key>
#   REACT_APP_API_URL=http://localhost:8000
# admin/.env : same REACT_APP_* as frontend

# ===== run =====
cd backend   && uvicorn main:app --reload --port 8000   # backend  :8000
cd frontend  && npm start                                # frontend :3000
cd admin     && npm start                                # admin    :3001 (package sets PORT=3001)
cd backend   && pytest tests/unit tests/integration -q   # unit + live-DB integration
# integration defaults to local 127.0.0.1:54326 already; override INTEGRATION_DATABASE_URL if needed
```

## 16. Commands that MUST NOT be run against production

- `supabase db push` — pushes migrations to the remote DB. **FORBIDDEN.**
- `supabase db reset --linked` — resets the remote. **FORBIDDEN.** (`db reset`
  without `--linked` targets local only.)
- `supabase db pull` / `supabase db remote commit` — only for *read-only* schema
  capture and only after confirming it never writes; avoid by default.
- Any Supabase command referencing the live project ref with write intent; any RLS
  change pushed remotely; any use of production connection strings.
- Importing `supabase/seed.sql` or `backend/carbon_tally_backup*.sql` (production
  data) into local; copying live user/anon/service secrets into local `.env`.
- Starting **Phase 9**, adding system-wide audit logging, or modifying production
  RLS during local bring-up.

## 17. Remaining blockers

| # | Blocker | Consequence | Prerequisite |
|---|---|---|---|
| 1 | **Docker not installed** | Supabase local stack cannot start | `apt install docker.io`/`podman-docker`; VT-x/AMD-V + running daemon |
| 2 | **Supabase CLI not installed** | Cannot run `start/reset/status` | Official release binary on `PATH` |
| 3 | **Node.js not installed** | Frontend + admin cannot run | `apt install nodejs npm` |
| 4 | **Python 3.14 present, 3.11 pinned** | Backend deps / pandas-build / pytest-asyncio risk | Install/use 3.11 venv; `pip install pytest-asyncio` |
| 5 | **`supabase/seed.sql` is a prod dump** | Cannot seed local from it | Build a controlled dev seed (deferred; §13) |
| 6 | **Project linked to live** | Accident risk if a remote-write command is run | Keep everything local; optionally `unlink` |
| 7 | **No `.env.example` exists** | No placeholder reference for local config | Add a placeholder file (follow-on) |
| 8 | **Network availability unverified** | Package / CLI / Docker-image downloads | Confirm internet access at install |

## 18. Next action (audit-scoped)

1. (This audit is complete and stopped here per STRICT RULE — no installs or edits
   were made to code/migrations/RLS/remote, and no test users were created.)
2. **Next session, in order:**
   a. Install Docker + Supabase CLI + Node (see §15) and confirm the host
      virtualisation prereq.
   b. `supabase start` → confirm API :54325 and DB :54326 health.
   c. `supabase db reset` → confirm the migration chain applies to the local V3
      schema (migrations = 104 non-auth tables).
   d. Capture local keys; write backend/frontend/admin `.env` (anon vs service,
      JWT secret) without committing them.
   e. Create the local `documents` bucket.
   f. Produce a **controlled dev seed** + local test users (one per role, fake
      identities) — out of scope here, then cleared by the working copy gate.
   g. Run backend + frontend + admin; run `pytest tests/unit tests/integration`
      and the scripted E2E against the local stack.
   h. Verify auth round-trip, storage upload, realtime (chat/presence), and the
      V3 frontend routes as covered by the Frontend Run Report's smoke checklist.

**Exit criteria:** local Supabase stack starts (Postgres+Auth+Storage+Realtime +
Studio), migrations apply cleanly to the intended V3 schema, backend runs on
:8000 against local Supabase, frontend runs on :3000 (anon key only), admin on
:3001, integration/E2E suites pass against the local DB — with **zero** writes or
data movement toward the live project.