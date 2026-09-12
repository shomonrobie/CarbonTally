# CarbonTally — Render Deployment Configuration Record

**Prompt Ref:** `CT-OPS-QUICKREF-20260912-007`
**Date:** 2026-09-12
**Document type:** Configuration record (evidence capture). **NOT a deployment-change instruction.**
**Related:** `docs/operations/CARBONTALLY_TECHNICAL_OPERATIONS_QUICK_REFERENCE_V1.0.md`.

> This document records what can be **verified from the repository** about the CarbonTally backend Render deployment, and what **cannot**. It is not authorization to change Render settings.

---

## 1. Access Result

> **UNVERIFIED — NO SAFE ACCESS.**
> No Render API credential, CLI, or `~/.render` configuration exists in this environment (verified: no `RENDER*`/`RENDER_API_KEY` environment variables, no `render`/`render-cli` binary, no `~/.render`). The live Render service configuration therefore **could not be independently inspected**.

No inference about correctness is made: the absence of configuration evidence is **not** evidence of misconfiguration.

## 2. Repository Evidence Found

| Artifact | Result | Evidence |
|---|---|---|
| `render.yaml` / `render.yml` | **Not present** | repository scan |
| `Procfile` | **Not present** | repository scan |
| `Dockerfile` | **Not present** | repository scan |
| `runtime.txt` | **PRESENT** → `python-3.11.9` | repo root |
| Backend dependency manifest | `backend/requirements.txt` (+ `requirements-dev.txt`) | present |
| ASGI entrypoint | `backend/main.py` → `app`; `uvicorn.run("main:app", …)` | `main.py:421-422` |
| Alt. entrypoint | `backend/main_v2.py` → pure V3 `app` | present |
| Server dependency | `uvicorn>=0.27.0` | `backend/requirements.txt` |
| Host/port source | `HOST` (default `0.0.0.0`), `PORT` (default `8000`) | `main.py:412-413` |
| CORS origin referencing the service | `https://carbontally-api.onrender.com` (in the allowed-origins list) | `backend/config.py:33` |
| `.env.production` present (names only) | contains `REACT_APP_API_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `REACT_APP_SUPABASE_ANON_KEY`, `RESEND_API_KEY`, `VITE_SUPABASE_*`, `PORT`, `BROWSER` | repo (git-ignored) |
| Prior repository note | deployment-readiness record states build+start config **UNKNOWN** | `docs/cline/prompt-history/CT-PROD-DEPLOYMENT-READINESS-20260911-001.md:28` |

## 3. VERIFIED (repository-confirmed facts)

These are confirmed from the repository only (they describe the **application**, not the Render service settings):

* **Python runtime**: `python-3.11.9` (repo-root `runtime.txt`).
* **ASGI application**: package `main`, attribute `app` (i.e. `main:app`) — `backend/main.py`.
* **ASGI server**: `uvicorn` (declared dependency).
* **Bind address**: `HOST` (default `0.0.0.0`) and `PORT` (default `8000`) — `main.py:412-413`.
* **Dependency manifest**: `backend/requirements.txt`.
* **Startup hooks**: starts the durable automatic-processing worker; logs route count — `main.py:268-287`.
* **Shutdown hooks**: stops the worker and closes the Supabase pool — `main.py:382-403`.
* **Health endpoints available**: `/`, `/health` (legacy), `/api/v2/health`, `/api/v3/health/realtime`.
* **Migrations are not run at startup** (no migration code in `main.py`).
* **The service's expected public origin** appears in backend CORS: `https://carbontally-api.onrender.com` (`backend/config.py`).

## 4. NOT VERIFIED (could not be established)

| Item | Status |
|---|---|
| Render **service name / type / region / plan / instances** | NOT VERIFIED |
| Render **root directory** (repo root vs `backend/`) | NOT VERIFIED |
| Render **build command** (e.g. whether it is `pip install -r requirements.txt`) | NOT VERIFIED |
| Render **start command** (the final command string; module `main:app` is verified from the app, the Render command is not) | NOT VERIFIED |
| Render **health-check path** configured on the service | NOT VERIFIED |
| Render **environment variables actually set** (names inferred from code/env files; values are inert) | NOT VERIFIED |
| Render **auto-deploy** setting and **deploy branch** | NOT VERIFIED |
| Whether a **separate worker/background service** is configured (the worker is in-process in the code) | NOT VERIFIED |
| **Current health state** of the live service | NOT VERIFIED |
| Whether production sets `RELOAD=false` | NOT VERIFIED |
| Supabase project **region / reachability** | NOT VERIFIED (prior reconciliation: production host returned NXDOMAIN; availability NOT CONFIRMED) |

## 5. SENSITIVE / OMITTED

Intentionally **not** recorded (no secret values appear in this document or in the repository):

* Supabase **service-role key** and **JWT secret**; database **DSN** (`DATABASE_URL`/`SUPABASE_DB_URL`).
* **Resend API key**; **AI provider API key**.
* **Vercel OIDC token** and any platform/deploy tokens.
* The publishable **anon/publishable key value** — a public key exists as a code fallback in `frontend/src/supabaseClient.js`; its **value is omitted** here. (Publishable keys are public by design; this is an observation, not an exposure of a secret.)

Only **variable names** are documented (see the quick reference §7).

## 6. OPERATIONAL IMPLICATIONS

1. **The backend cannot be reproduced from repository evidence alone.** With no `render.yaml`/`Procfile`/`Dockerfile`, the exact build/start/health configuration lives only in the Render dashboard and could be lost or diverged. This is the **highest operational risk identified** in the preceding assessment.
2. **Redeploy/rollback is not documented.** A future maintainer cannot safely recreate or roll back the service from the repo.
3. **Startup coupling hazard**: the V3 layer is optional at boot (`main.py:22-34`); if its import fails, the service still starts but V3 routes are absent. Whether production currently imports V3 successfully is **UNVERIFIED**.
4. **`RELOAD` default is `true`** in code; if Render does not override it, the production server may run with auto-reload enabled. **UNVERIFIED** — this must be checked in the Render dashboard before relying on it.
5. **Recommendation (not performed here):** capture the live Render configuration as **infrastructure-as-code** (`render.yaml`) and document build/start/health, then re-verify this record. This requires a separate, authorised task and Render access.

---

*This is a configuration record only. It authorises no change to Render, Vercel, Supabase, environment variables, or the application.*

