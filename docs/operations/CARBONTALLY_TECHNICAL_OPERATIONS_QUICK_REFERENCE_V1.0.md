# CarbonTally — Technical Operations Quick Reference V1.0

**Prompt Ref:** `CT-OPS-QUICKREF-20260912-007`
**Date:** 2026-09-12
**Status:** Technical operations quick reference (verified-evidence only). **Not** the full 25-section manual.
**Companion records:** `docs/architecture/CARBONTALLY_TECHNICAL_OPERATIONS_DOCUMENTATION_ASSESSMENT_20260912.md`; `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md`; `docs/architecture/CARBONTALLY_PHASE7_CLOSURE_AND_RELEASE_BOUNDARY_20260912.md`.

> **Rule for this document:** every statement is grounded in repository evidence. Anything that could not be verified from the repository is explicitly marked **UNVERIFIED**. No production procedure is invented. No secret value is reproduced.

---

## 1. Purpose and Scope

A short, practical first-stop reference for a developer/operator handling CarbonTally incidents. It covers the service inventory, start/build paths, health checks, environment variables, logging, the background worker, database/migration safety, and subsystem triage pointers. It deliberately does **not** contain remediation scripts.

## 2. System / Service Inventory

| Layer | Technology | Repository evidence |
|---|---|---|
| Public website + authenticated app | React (CRA) — `frontend/**` | `frontend/package.json` (`react-scripts`) |
| Backend API | FastAPI + Uvicorn — `backend/**` | `backend/main.py`, `backend/api/router.py` |
| Database / Auth / Storage / Realtime | Supabase (PostgreSQL) | `supabase/**`, `backend/infra/supabase.py` |
| Background worker | In-process asyncio loop | `backend/workers/automatic_processing.py` |
| Email | Resend | `backend/services/v3_email.py` |
| Frontend hosting | Vercel | `vercel.json` |
| Backend hosting | Render | `runtime.txt` (Python pin); `https://carbontally-api.onrender.com` appears in `backend/config.py` CORS list |
| CI | GitHub Actions (Playwright only) | `.github/workflows/playwright.yml` |

## 3. Production Architecture Summary

* Single FastAPI app (`backend/main.py`) mounts **legacy `routes/**`** routers **and**, when importable, the **V3 router** (`backend/api/router.py`) — see `main.py:22-34`, `main.py:260-262`.
* Authentication is **Supabase Auth**; the backend resolves identity per request (`backend/auth.py`) and re-authorises server-side.
* Tenancy is enforced by server authz **plus** PostgreSQL RLS (RLS is defence-in-depth; the API is authoritative).
* The **V3 layer is optional at boot**: if its import fails, the legacy app still starts and logs a warning (`main.py:29-34`) — a maintenance hazard to be aware of (route availability depends on that import succeeding).

## 4. Backend Startup Path

| Question | Answer | Evidence |
|---|---|---|
| Entrypoint module | `backend/main.py` → ASGI app `app` | `main.py` (module-level `app = FastAPI(...)`) |
| ASGI target | `main:app` | `main.py:421-422` (`uvicorn.run("main:app", …)`) |
| Server | Uvicorn | `backend/requirements.txt` (`uvicorn>=0.27.0`) |
| Host / port | `HOST` (default `0.0.0.0`), `PORT` (default `8000`) | `main.py:412-413` |
| Reload | `RELOAD` env; **default `"true"`** | `main.py:414` |
| Startup actions | prints config + route count; starts durable worker (non-blocking) | `main.py:268-287` |
| Shutdown actions | stops worker; closes Supabase pool | `main.py:382-403` |
| Migrations on startup | **No — not run at startup** | no migration code in `main.py` |
| Workers on startup | **Yes** (automatic-processing worker) | `main.py:279-287` |
| Alt. entrypoint | `main_v2.py` → pure V3 (`uvicorn main_v2:app`) | `main_v2.py` |
| **Render start command** | **UNVERIFIED** — not in the repository (no `render.yaml`/`Procfile`/`Dockerfile`) | see Render record |
| Python version | `python-3.11.9` | `runtime.txt` (repo root) |

> **Operational note:** `RELOAD` defaults to **true**, which is a development setting. Whether production sets `RELOAD=false` is **UNVERIFIED** (Render env vars not inspectable).

## 5. Frontend Build / Deployment Path

* Framework: Create React App — scripts `start`/`build`/`test` = `react-scripts …` (`frontend/package.json`).
* Build command (repo-verified): `npm run build` → produces `build/`.
* Deployment: Vercel; `vercel.json` defines SPA rewrite `/(.*) → /index.html` and a quarantined legacy `/admin` surface. `cleanUrls: false` (set deliberately for SPA deep links).
* Runtime config is baked at build time via `REACT_APP_*` env vars (CRA); changing them requires a rebuild.
* **Vercel project settings / env configuration are UNVERIFIED** (not in the repository).

## 6. Health Checks

| Endpoint | Layer | Behaviour | Evidence |
|---|---|---|---|
| `GET /` | legacy root | JSON `status:"healthy"`, `version`, `routes_count` | `main.py:289-300` |
| `GET /health` | legacy | JSON `status:"healthy"` or `"degraded"` based on Supabase connectivity | `main.py:302-314` |
| `GET /api/v2/health` | V3 | `HealthResponse` | `api/router.py:77-78` |
| `GET /api/v3/health/realtime` | V3 | probes Supabase Realtime `/realtime/v1` readiness (503 there silently disables Realtime) | `api/v3_health.py:111` |

* **Healthy** = the endpoint responds and (for `/health`) reports `healthy`.
* **`degraded`** on `/health` = Supabase connectivity check failed → investigate Supabase credentials/URL and network before other issues.
* **`/api/v3/health/realtime` failure** = Realtime features (messaging delivery, presence, notification bells) are degraded while REST/Auth may still work.
* Example generic check (no production host assumed): `curl -sS http://<host>:<port>/health`.
* Production URL/health path on Render: **UNVERIFIED**.

## 7. Environment-Variable Reference

Values are **not** reproduced. `.env` files exist locally and are git-ignored.

| Variable | Used by | Purpose | Required? | Secret? | Safe documentation |
|---|---|---|---|---|---|
| `SUPABASE_URL` | backend (`auth.py`, `infra/supabase.py`, `config.py`) | Supabase project URL | Required (prod) | No | Set per environment |
| `SUPABASE_SERVICE_KEY` / `SUPABASE_SERVICE_ROLE_KEY` | backend | Service-role key (write-capable; bypasses RLS) | Required (prod) | **YES** | Never log/expose |
| `SUPABASE_JWT_SECRET` | backend | JWT verification | Required (prod) | **YES** | Never log/expose |
| `SUPABASE_ANON_KEY` | backend/frontend | Anon/publishable key | Optional | No (public) | Public key |
| `DATABASE_URL` / `SUPABASE_DB_URL` | backend (`infra/supabase.py`) | asyncpg Postgres DSN | Required for DB repos | **YES** | Never log/expose |
| `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` | frontend | Public Supabase config | Optional | No (public) | Public |
| `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY` | frontend | CRA public Supabase config | Optional (code has a fallback) | No (public) | Public |
| `REACT_APP_API_URL` | frontend | Backend base URL | Required for API calls | No | Set per build |
| `REACT_APP_OAUTH_REDIRECT_URL` | frontend | Google OAuth redirect | Optional | No | Defaults to `${origin}/auth/callback` |
| `REACT_APP_GOOGLE_CLIENT_ID` | frontend | Google OAuth client | Optional | No (public) | Public client id |
| `RESEND_API_KEY` | backend (`services/v3_email.py`) | Transactional email | Optional — **no-op stub when unset** | **YES** | Never log/expose |
| `FOUNDER_EMAIL` | backend (`config.py`) | Default founder address | Optional (has default) | No | — |
| `CARBONTALLY_AI_API_KEY` / `_BASE_URL` / `_MODEL` | backend | AI extraction provider | Optional | Key is **secret** | Never log/expose |
| `PORT` / `HOST` / `RELOAD` | backend (`main.py`) | Uvicorn bind/reload | Optional (defaults 8000 / 0.0.0.0 / true) | No | Set `RELOAD=false` in prod (unverified) |
| `APP_ENV` / `ENV` | backend | Environment label | Optional | No | — |
| `LOG_LEVEL` | backend | Logging level | Optional | No | — |
| `AUDIT_BATCH_SIZE` / `AUDIT_DEFAULT_ACTOR` | backend | Audit logger knobs | Optional | No | — |
| `CACHE_DEFAULT_TTL_SECONDS` / `EVENT_BUS_MAX_HANDLERS` / `SEARCH_INDEX_DEFAULT_LIMIT` | backend | Infra tunables | Optional | No | — |
| `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` | dual-tool/Vite surface | Legacy/dual config | Dev/optional | No (public) | — |
| `VERCEL_OIDC_TOKEN` | Vercel | Deployment token | Platform-managed | **YES** | Never commit |
| `OFFLINE_MOCK`, `CT_BACKUP_TEST_DSN`, `TEST_*` | tests/backup tests | Dev/test only | Dev/test | Some secret | Never use in prod |

## 8. Logging and Diagnostics

* **Backend logging**: standard-library `logging`, configured once via `configure_logging()` → single **stdout** stream handler; format `%(asctime)s %(levelname)-7s %(name)s: %(message)s` (`backend/core/logging.py`). No file sink, no external log service in code.
* **Request correlation**: `RequestContextMiddleware` attaches a request/correlation id and timing; the V3 error envelope carries a `request_id` (`backend/api/middleware.py`, `backend/api/router.py`).
* **Audit trail**: material actions persist to `public.audit_trail` (append-only; Phase 7 taxonomy in `metadata`) — DB-resident, not a log file.
* **Worker logs**: the worker uses `get_logger(__name__)` and logs failures without stopping the loop (`backend/workers/automatic_processing.py`).
* **Where logs appear in production**: the hosting platform log console (Render). **Retention/export of platform logs is UNVERIFIED.**
* **Start-of-investigation pointers**
  * API failure → platform logs (stdout) filtered by `request_id`; then `core/exceptions.py` error codes.
  * Auth failure → `/api/v3/me/context` and `auth.py`; see the Login Runbook.
  * DB failure → `/health` `degraded`; `infra/supabase.py` pool.
  * Calculation failure → `document_processing_queue.error_log` + `calculation_snapshots`.
  * Extraction failure → queue row + worker logs.
  * Worker failure → worker log lines (loop continues); check queue state.
  * Deployment failure → platform build/runtime logs (Render/Vercel) — see the Render record.

## 9. Worker / Background Processing

Single mechanism found: **in-process asyncio worker** started at app startup.

| Aspect | Detail | Evidence |
|---|---|---|
| Where implemented | `backend/workers/automatic_processing.py` (+ `services/automatic_processing.py`) | — |
| How it starts | `main.py:279-287` via `get_automatic_processing_worker().start()` | — |
| How it stops | `main.py:382-403` (shutdown) | — |
| What it processes | durable jobs from `document_processing_queue` (`FOR UPDATE SKIP LOCKED`) | worker docstring |
| Poll / batch | `poll_interval_seconds=1.0`, `batch_size=3` | `automatic_processing.py:40-45` |
| Failure visibility | a failed tick is logged; the loop continues | worker docstring |
| Retry / idempotency | durable job model (`reprocess_count`); stage outputs are idempotency markers | migration `20260829000000_v3m9_durable_automatic_processing.sql` |
| Stale locks | recovered after `stale_lock_seconds=300` | `automatic_processing.py:42,103` |
| Restart behaviour | job state in the DB → restart resumes in-flight jobs | worker docstring |
| Separate queue service | **None found** (no Celery/Redis/RQ) | repository scan |
| Undocumented | worker backlog/stuck-job triage procedure | see §21 |

## 10. Database and Migration Safety

* 54 SQL migrations in `supabase/migrations/**`. **Migrations are NOT applied automatically at application startup** (verified: no migration code in `main.py`).
* Production migration is governed by `docs/architecture/CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md`, which records **production migration history = UNKNOWN**, effective schema ≈ migrations 1–21, and that `supabase migration list --linked` is **PROHIBITED** (it creates a temporary login role — a mutation).
* **Never** run a production migration without explicit authorisation; never reset or truncate.
* **Rollback limitation:** no guaranteed down-migration exists; some migrations are non-idempotent (documented in the safety plan). Treat migrations as **forward-only**; restore-based recovery is **NOT implemented** (§18).

## 11. Calculation Troubleshooting (diagnostic only)

Verified investigation sequence (each step maps to real storage):

`Emissions result → emissions_logs.snapshot_id → calculation_snapshots (factor_id/source/set, import_batch_id, reporting_year, methodology, algorithm_version, content_hash, source_item_id/file/page) → extraction item → source document → report content`

* **Inspect calculation records**: `calculation_snapshots` (immutable; `content_hash`), `emissions_logs`.
* **Factor provenance**: on the snapshot (`factor_id`, `factor_source`, `factor_set`, `factor_kind`, `customer_factor_id`).
* **Audit/evidence relation**: `/api/v3/emissions/{log_id}/evidence` (D33 chain); Phase 7 package `/api/v3/exports/audit-package.json`.
* **Re-verification**: `POST /api/v3/emissions/calculations/{snapshot_id}/verify` recomputes only to *check* a stored result.
* **Never manually alter** activity data, factors, mappings, calculations, snapshots, evidence or audit records to make an error disappear. Any change affecting carbon results must follow correction → recalculation → **new snapshot**, preserving the original.
* Domain/expert review is required where the cause is methodological (factor choice, boundary, unit assumption), not technical.

## 12. Factor / Import Troubleshooting (diagnostic only)

* Importer architecture: provider parsers (e.g. `src/providers/defra/parser.py`), `backend/data/imports.py` + `emission_factors.py`, `import_batches`, `import_batch_id` on snapshots, `factor_aliases`; synthetic/DEFRA/SEAI tooling under `tools/carbon_data_factory/**`.
* Baseline references: `docs/standalone/MIGRATION_BASELINE_REPORT.md`; the Blueprint records the DEFRA/SEAI factor baseline.
* Minimal diagnostic flow: **import failure** → `import_batches` row/status + importer logs; **malformed source** → parser errors; **mapping mismatch** → `factor_aliases` / matching pipeline (`engines/factor_matching.py`); **validation failure** → `engines/validation.py`; **duplicate factor** → natural-key constraint (`natural_key`); **unexpected factor selection** → snapshot `factor_id`/`factor_source` + matching provenance.
* Do **not** perform a production import or edit factor rows as part of troubleshooting.

## 13. Document Processing Troubleshooting (diagnostic only)

* Pipeline: upload → enqueue (`document_processing_queue`) → ingest → extract → map → validate → calculate → review. States/attempts are durable in the DB.
* OCR: `pytesseract`/`pdfplumber`/`pypdf2` in `backend/requirements.txt`; local-OCR helper `tools/provision_tesseract_local.sh`. **OCR availability is an environment dependency.**
* Triage: queue row (`stage`, per-stage `*_at`, `reprocess_count`, `error_log`) → worker logs → extraction item.
* Human extraction uses `manual_extraction_batches/items` (+ `audit_helpers.record_item_extraction_edit`).
* Do not delete queue rows or rewrite extraction output to "fix" a stuck document; use the supported workflow.

## 14. Authentication / RBAC / RLS Troubleshooting

* Canonical references: `docs/architecture/CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md`, `docs/architecture/CARBONTALLY_PRODUCTION_LOGIN_RUNBOOK_20260911.md`, `docs/RBAC.md`, `docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md`.
* Post-login destination is **server-decided** by `GET /api/v3/me/context` (`backend/api/v3_context.py`); a resolution error fails closed (HTTP 500), never "new user".
* Guards: `backend/auth.py` (`get_current_user`, `require_org_member/admin`, `require_staff`, `require_admin`), `api/operations_auth.py`, `api/consultant_auth.py`, `api/pe_auth.py`.
* RLS is **defence-in-depth**; the API is authoritative. If a user "sees nothing" it is usually authorization/scope, not RLS alone. Tenant isolation is enforced in SQL (`$1`-scoped queries) and server guards.
* Do **not** disable RLS or add bypasses to diagnose; reproduce with the actor's real identity.

## 15. Audit / Evidence Troubleshooting

* Canonical ledger: `public.audit_trail` (append-only; Phase 7 taxonomy in `metadata`). Reads: `GET /api/v3/ops/reporting/audit` (staff-admin); org `audit-activity` / `audit-readiness`; consultant client activity; entity activity.
* Evidence package: `GET /api/v3/exports/audit-package.json` (`not_assurance: true`, package SHA-256).
* Immutability: trigger `p7_audit_trail_immutable` (migration `20260912000000…`). **Phase 7 residuals apply** (accepted) — see the closure record; e.g. access is not self-audited, and a privileged superuser can bypass the trigger via `session_replication_role=replica`.
* Do not UPDATE/DELETE audit rows; do not alter `calculation_snapshots`.

## 16. Email Troubleshooting

* Sender: `backend/services/v3_email.py` (Resend). **When `RESEND_API_KEY` is unset the sender is a no-op stub returning `delivered=False` with a reason** — so "email not sent" in a dev/test environment is expected behaviour, not a defect.
* Sending is restricted to the CarbonTally default sender or a **verified** consultant sender (`consultant_senders.status = 'verified'`); arbitrary From addresses are rejected by design.
* Triage order: (1) is `RESEND_API_KEY` set in the environment? (2) Resend dashboard delivery/domain verification (external). (3) recipient/domain (SPF/DKIM/DMARC are the customer/consultant's responsibility).
* Do not rotate keys or change domains as part of troubleshooting.

## 17. Deployment Troubleshooting

* **Frontend (Vercel)**: build `npm run build`; SPA rewrites via `vercel.json`; deep-link regression is a known past issue (`cleanUrls:false`). Project/env settings **UNVERIFIED** (not in repo).
* **Backend (Render)**: see `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md`. The exact start/build commands and health path on Render are **UNVERIFIED** from the repository.
* **Before any deploy**: confirm which entrypoint is expected (`main:app`) and that the V3 import succeeds (otherwise V3 routes are absent).
* **Post-deploy checks (generic)**: `GET /health` = healthy; `GET /` returns `routes_count`; V3 spot-check.
* **Rollback**: application rollback is platform-mediated (Render/Vercel) — **procedure UNVERIFIED**; database rollback is **not supported** (forward-only migrations).

## 18. Backup / Restore Status

Verified against the repository:

| Question | Verified answer | Evidence |
|---|---|---|
| Are backups configured/scheduled? | **No scheduled backups** | `CARBONTALLY_PRODUCTION_BACKUP_RESTORE_ROADMAP_V1.0.md` ("Scheduled backups — NOT IMPLEMENTED") |
| What is backed up? | An **encrypted, checksummed logical database export capability** exists (`backend/backup/**`) | `BACKUP_IMPLEMENTATION_PHASE1_20260911.md` |
| Is storage backed up? | **No** — Storage-object backup NOT IMPLEMENTED | roadmap |
| Has restore been tested? | **No** — "Proven restore drill — NOT PERFORMED" | roadmap |
| Is restore implemented? | **No** — no `restore` implementation found in `backend/backup/*.py` | repository scan |
| RTO / RPO | **Not defined** | roadmap (`DR-20 NOT SATISFIED`) |
| Verified recovery procedure? | **None** | roadmap |
| Production backup/restore authorized? | **No** | roadmap |

> **Status: `BACKUP/RESTORE CAPABILITY NOT VERIFIED / NOT IMPLEMENTED` (beyond an untested logical-export capability).** There is no disaster-recovery readiness claim. Migrations 22→53 are recorded as **NOT AUTHORIZED**.

## 19. Incident / Escalation Quick Reference (role-based)

| Category | First diagnostic (role) | Evidence to collect | Stop / escalate when |
|---|---|---|---|
| Infrastructure (Render/Vercel/Supabase) | Platform/DevOps engineer | health endpoints, platform logs, deploy history | platform-side change needed → platform owner |
| Database / migrations | Backend engineer + DB owner | `/health`, pool errors, migration-safety plan | any production migration → **PO authorisation required** |
| Authentication / security | Security-reviewing engineer | `auth.py` path, `/api/v3/me/context`, RLS helpers | suspected breach/isolation failure → **security review** |
| Calculation / data integrity | Backend engineer | snapshots, `content_hash`, evidence chain | result change required → **carbon-domain expert + workflow** |
| Document extraction | Backend engineer | queue row, worker logs, OCR availability | systemic OCR/env change → infrastructure |
| Factor data | Backend engineer + carbon expert | `import_batches`, snapshot factor provenance | re-import/factor edit → **carbon-domain expert** |
| Reporting | Backend engineer | report queue row, `error_log`, `report_versions` | content correctness → carbon-domain expert |
| Email | Backend engineer | `RESEND_API_KEY` presence, Resend dashboard | domain/verification change → account owner |
| Deployment | Release engineer | build logs, health checks, manifest | rollback/DB impact → PO |

Roles only — no named individuals. Escalation owner identity is an organisational decision (not in this repository).

## 20. Carbon-Accounting Correction vs Technical Recovery

**These are different things and must never be conflated.**

* **Technical recovery** fixes *plumbing* (queues, workers, connectivity, deploys) without changing emissions truth.
* **Carbon-accounting correction** changes a *result* and must follow the governed workflow: correct the activity/extraction input → recalculate → produce a **new** `calculation_snapshot`; the original snapshot is **retained**. Provenance and audit records must be preserved.

A developer must **not** edit activity data, factors, mappings, calculations, snapshots, evidence or audit records to make a technical symptom disappear. Methodological questions require carbon-domain expertise; suspected isolation/security issues require security review.

## 21. Known UNVERIFIED Items

* Render production **build/start command, health path, instances, region, env vars** — no `render.yaml`/`Procfile`/`Dockerfile`; no live Render access.
* Vercel project settings/domains/env — only `vercel.json` in repo.
* Exact env-var **values/secrets** — intentionally not in the repository (git-ignored `.env*`).
* Supabase **region / production reachability** — prior reconciliation recorded production as unreachable/UNKNOWN.
* Whether production sets `RELOAD=false`.
* Whether migration 54 (or 22→53) is applied in production — **history UNKNOWN**.
* Platform **log retention/export** on Render.
* **Restore** procedure, RTO/RPO (not implemented).
* Any CI beyond the Playwright workflow.

## 22. "Never Do This in Production"

1. Never run `git reset` / `git clean` / `git stash` / force-push against a shared branch.
2. Never apply or reset migrations without explicit authorisation (and never `db reset`).
3. Never disable RLS or add authorization bypasses "to test" or "to fix".
4. Never `UPDATE`/`DELETE` `audit_trail` or `calculation_snapshots`.
5. Never manually alter activity data, factors, mappings, evidence or audit records to hide an error.
6. Never delete queue/extraction rows to clear a stuck job — use the workflow.
7. Never rotate secrets, change domains or redeploy production as part of troubleshooting.
8. Never expose or log secrets, service keys, JWT secrets, DSNs or signed URLs.
9. Never claim backup/DR readiness, independent assurance, certification or legal compliance.
10. Never begin Phase 8 or remediate Phase 7 residuals without separate authorisation.

---

*End of quick reference. Verified-evidence only; unverified items are marked. Not a remediation procedure.*




