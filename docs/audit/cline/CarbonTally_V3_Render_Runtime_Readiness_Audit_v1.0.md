---
Document Type: Runtime Readiness & Codebase Error Audit
Project: CarbonTally
Architecture: CarbonTally V3 (Supabase + Render FastAPI + Lovable)
Version: 1.0
Status: FINAL
Audit Mode: READ-ONLY
Created: 2026-08-15
Author: Cline
Target Platform: Render (Python web service)
---

# CarbonTally V3 — Render Runtime Readiness & Codebase Error Audit

## Purpose

Determine why the current V3 FastAPI backend does not start correctly on Render,
and identify every genuine runtime/deployment problem that would prevent the
existing backend from being used by the Lovable frontend.

Scope constraints honoured during the audit:

- Do NOT redesign the V3 architecture (Supabase = Postgres/Auth/RLS/Storage/Realtime; Render = FastAPI business logic; Lovable = frontend/UI/UX).
- Do NOT create parallel V3 engines, run a new V3 migration, or make broad refactors.
- READ-ONLY: no production code, schema, RLS, or emission-factor data was modified.

## 1. Actual FastAPI entrypoint

```text
Application entrypoint:         backend/main.py   (module target: main:app)
FastAPI application object:     app  (backend/main.py line 80: app = FastAPI(...))
Expected Render start command:  cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
                                (Render "Start Command" must run from the backend/ directory;
                                 main.py's own __main__ block defaults to 0.0.0.0 but reload=True)
Expected Python version:        python-3.11.9  (runtime.txt at repo root)
Dependency installation method: pip install -r backend/requirements.txt
                                (Render "Python requirements path" = backend/requirements.txt)
```

Evidence:

- No `render.yaml`, `Dockerfile`, `Procfile`, `pyproject.toml`, `poetry.lock`, `uv.lock`,
  or `Pipfile` exists anywhere in the repository. The Render service is dashboard-configured.
- The Render traceback paths (`/opt/render/project/src/backend/routes/admin/staff.py`) prove the
  app is imported as `main:app` with the working directory = `backend/` (imports such as
  `from config import Config` and `from routes import …` only resolve when `backend/` is on sys.path).
- Two `requirements.txt` files exist:
  - `requirements.txt` (repo root): 12 packages — NO `supabase`, NO `python-dotenv`, NO `pydantic`.
  - `backend/requirements.txt`: 19 packages — includes `supabase==2.9.0`, `python-dotenv`, `pydantic[email]`, `fpdf2`, `pypdf2`, `openpyxl`.
- The Render failure trace proves `dotenv`, `supabase`, `fastapi`, `pydantic` are installed on
  Render (the chain passed `main.py:3` load_dotenv, `main.py:13` from config (imports supabase),
  `main.py:14` from database (imports supabase + dotenv)) all the way to `staff.py:1405`.
  Therefore **`backend/requirements.txt` is the effective dependency file**.

## 2. The current Render startup failure — traced

Failing import chain (matches the reported trace exactly):

```text
backend/main.py:20                  from routes import (waitlist, upload, reports, …)
backend/routes/__init__.py:21       from .admin import staff, defra, extraction, …
backend/routes/admin/__init__.py:7  from . import staff
backend/routes/admin/staff.py:1405  supabase: Client = Depends(get_supabase_client)
```

Verdict: **missing import — nothing else.**

- `backend/routes/admin/staff.py` line 11 imports `from supabase import create_client` but NOT `Client`.
- Lines **1405, 1733 and 1786** all use the annotation `supabase: Client = Depends(get_supabase_client)`.
  Python evaluates parameter annotations at function-definition time (no `from __future__ import
  annotations` in the file), so `NameError: name 'Client' is not defined` fires at module import.
- The correct type is exactly `supabase.Client`. Confirmed by every other module in the codebase:
  `database.py:8`, `auth.py:10`, `routes/emissions.py:8`, `routes/reports.py:12`,
  `routes/customer_documents.py:8`, `routes/organizations/files.py:10`,
  `routes/organizations/management.py:9`, `utils/organization_utils.py:8` — all `from supabase import Client`.
- NOT a circular import, NOT a stale module, NOT a dependency/version problem. `supabase==2.9.0`
  exports `Client`/`create_client` correctly.

## 3. Beyond the first error — full import-chain audit

After fixing the `Client` import there is **no second import-time blocker** in the chain.
Every module reachable from `main.py` was verified:

| Module | Module-level risk | Status |
|---|---|---|
| config.py, database.py, auth.py | `supabase`, `dotenv`, `jwt` imports | OK (deps present on Render) |
| routes/emissions.py, waitlist.py, upload.py, reports.py, glossary.py, users.py, notifications.py, documents_main.py, document_activity.py, drafts.py, reference.py, logs.py, feedback.py, drafts_enhanced.py, customer_documents.py | no module-level DB calls; OCR deps lazy | OK |
| routes/admin/defra.py, extraction.py, reviews.py, assignments.py, permissions.py, workload.py, beta.py, audit.py, review_history.py, logs.py, bulk.py, email_templates.py, analytics.py, settings.py | headers verified; `Client` usages checked | OK (staff.py was the only failure) |
| routes/organizations/management.py … bulk.py (11 files) | `Client` imported where annotated | OK |
| report_generator.py | `router = APIRouter()` defined before decorators; fpdf import | OK |
| utils/__init__.py → email.py, emissions.py, document_classifier.py, staff_workload.py, organization_utils.py | imports `resend`, `pandas`, `numpy`, `supabase`, `database` | OK |
| api/, engines/, domain/, infra/, data/, core/, middleware/, main_v2.py | parallel v2.1 architecture — NOT imported by main.py | Not in chain |

Checked explicitly:

- No module-level `get_supabase_client()` / `create_client(...)` calls anywhere in the chain.
- `app = FastAPI` exists only in `main.py` (plus legacy `main copy.py` / `main copy 2.py`, not imported).
- No circular imports: `reviews.py → workload.py → utils` is acyclic;
  `organizations/analytics.py → .management` resolves (`get_organization_name` at management.py:170).
- No imports of files that no longer exist.

Answer to "if we fix the first NameError, what is the NEXT thing that will prevent Render from starting?"
— **nothing in the import chain**. The next failures are configuration/runtime:

1. If the start command runs `python main.py`, `RELOAD` defaults to **true** (`main.py:349`).
2. If `uvicorn main:app` runs without `--host 0.0.0.0`, uvicorn binds 127.0.0.1 and Render health checks fail.
3. `workload.py` is **two concatenated files** — app starts but several routes silently disappear (see B1).
4. If `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` are not set in Render env, every request fails and
   `/health` reports degraded (startup still succeeds).

## 4. Python dependency audit

Based on what production code actually imports at runtime (not tests):

| Package | Declared? | Used by | Classification |
|---|---|---|---|
| fastapi | root ✓ / backend ✓ | core | REQUIRED FOR RUNTIME |
| uvicorn | ✓ | server | REQUIRED FOR RUNTIME |
| pydantic / pydantic[email] | root ✗ (transitive) / backend ✓ | all models | REQUIRED FOR RUNTIME |
| supabase | root ✗ / backend ✓ (2.9.0) | database/auth/all routes | REQUIRED FOR RUNTIME |
| python-dotenv | root ✗ / backend ✓ | main.py:3, database, auth, config | REQUIRED FOR RUNTIME |
| python-multipart | ✓ | uploads/form parsing | REQUIRED FOR RUNTIME |
| pandas, numpy | ✓ | upload, emissions utils, reports | REQUIRED FOR RUNTIME |
| resend | ✓ | notifications, utils/email | REQUIRED FOR RUNTIME (email features) |
| fpdf2 | ✓ | report_generator | REQUIRED FOR RUNTIME (reports) |
| email-validator | ✓ (backend) | pydantic EmailStr | REQUIRED FOR RUNTIME |
| pypdf2 (`pypdf` module) | ✓ (backend) | upload.py lazy PDF repair | REQUIRED FOR RUNTIME (feature) |
| openpyxl | ✓ (backend) | ExcelWriter in report/export flows | REQUIRED FOR RUNTIME (feature) |
| pdfplumber, Pillow | ✓ | pdf_engine, upload | REQUIRED FOR RUNTIME (feature) |
| pytesseract | ✓ | pdf_engine, upload OCR | REQUIRED FOR RUNTIME — needs Tesseract binary on host (absent on Render) |
| pdf2image | ✓ | pdf_engine, upload OCR | REQUIRED FOR RUNTIME — needs poppler binary on host (absent on Render) |
| **PyJWT** | **✗ neither file** | auth.py:4 `import jwt` (module level!) | REQUIRED FOR RUNTIME — currently only satisfied transitively via supabase→gotrue; declare it explicitly |
| **reportlab** | **✗ neither file** | upload.py lazy `from reportlab.pdfgen import canvas` | REQUIRED FOR SPECIFIC FEATURES — ModuleNotFoundError on PDF repair |
| python-magic | ✓ but unused | nothing imports it in prod | NOT ACTUALLY REQUIRED |
| fpdf==1.7.2 | ✓ (backend) | — | CONFLICTS with fpdf2 (both install the `fpdf` module); remove it |
| httpx | ✗ | tests + legacy `main copy` only | NOT ACTUALLY REQUIRED (prod) |
| asyncpg / psycopg2 | ✗ | parallel v2.1 arch + tests + probes only | NOT ACTUALLY REQUIRED (prod main.py chain) |

Critical nuance: the ROOT `requirements.txt` is missing `supabase`, `python-dotenv`, and `pydantic`.
If Render were ever pointed at the root file, startup would die at `main.py:3`
(`ModuleNotFoundError: No module named 'dotenv'`). The current deploy works only because Render
uses `backend/requirements.txt`. Latent deployment landmine (see B2).

## 5. Pylance missing-import warnings — verdict

Evidence:

1. **The packages are declared correctly** — `backend/requirements.txt` lists `fastapi==0.109.0`
   and `pydantic[email]>=2.0.0`.
2. **They are installed on Render** — the failing trace proves `fastapi`/`pydantic`/`supabase`/`dotenv`
   imported successfully in the chain up to `staff.py:1405`. A true missing package would surface as
   `ModuleNotFoundError` at `main.py:4`, not `NameError` at `staff.py:1405`.
3. **The local machine runs Python 3.14.3** (`tmp_probe_python.txt`) while the project targets
   **Python 3.11.9** (`runtime.txt`). The pinned `pandas==2.1.4` / `numpy==1.26.4` have no wheels for
   Python 3.14, and no project venv is present. The editor/Pylance interpreter therefore cannot
   resolve `fastapi`/`pydantic` locally.

Conclusion: **environment/interpreter problem, NOT a production failure.** Fix by pointing Pylance at
a Python 3.11 interpreter with the backend requirements installed, or creating a local venv.

## 6. Render environment-variable requirements

Extracted from `backend/config.py`, `backend/database.py`, `backend/auth.py`, `backend/main.py`, `backend/utils/email.py`:

| Variable | Classification |
|---|---|
| `SUPABASE_URL` | REQUIRED AT RUNTIME (every DB-touching request; startup OK without it, `/health` → degraded) |
| `SUPABASE_SERVICE_KEY` | REQUIRED AT RUNTIME (same) |
| `SUPABASE_JWT_SECRET` | OPTIONAL (fallback manual JWT decode in auth.py) |
| `RESEND_API_KEY` | REQUIRED ONLY FOR EMAIL FEATURES (notifications, utils/email) |
| `FOUNDER_EMAIL` | OPTIONAL (has default) |
| `PORT` | OPTIONAL (default 8000; Render injects it) |
| `HOST` | OPTIONAL (default `0.0.0.0`) |
| `RELOAD` | OPTIONAL — set to `false` in production (defaults to `true` in main.py) |
| `SUPABASE_ANON_KEY` | DEVELOPMENT ONLY / unused (read by database.py but never used to build a client) |

Other vars — `DATABASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`,
`SUPABASE_DB_URL`, `APP_ENV`, `LOG_LEVEL`, `EVENT_BUS_MAX_HANDLERS` — are consumed only by the
parallel `backend/infra/` layer, which `main.py` does not import. No secret values are reproduced
in this report.

## 7. Supabase client usage audit

- Architecture respected: Lovable → Supabase (auth/CRUD/RLS/storage) and Lovable → Render (business
  logic) → Supabase via service-role client. The backend builds clients with `SUPABASE_SERVICE_KEY`
  in `database.py` / `auth.py` / `config.py`. No redesign needed.
- **No hardcoded localhost Supabase URLs in production code.** Ports `54321`–`54326` and `127.0.0.1`
  appear only in `backend/tests/`, probe scripts (`_v3m12_*`), and `tmp_*` files — none reachable from `main.py`.
- **No startup code requires a local Supabase/Docker stack.** `database.py` creates the client lazily.
- Sync usage is consistent (`create_client` + blocking `.execute()`), acceptable for FastAPI endpoints.
- **Security note (not a startup blocker):** `backend/.env` (committed) sets `SUPABASE_ANON_KEY` and
  `VITE_SUPABASE_ANON_KEY` to the same value as the service-role secret, and contains a real
  `RESEND_API_KEY` and `REACT_APP_API_URL=http://localhost:8000`. Because `.env` is in the repo, the
  service-role secret is at risk; `VITE_*` keys are bundled into the frontend build. Remediate by
  rotating keys and removing `.env` from version control. `frontend/src/supabaseClient.js` hardcodes
  the Supabase URL + an anon/publishable key (normal for anon keys, but should be env-driven).

## 8. API routing audit

- All routers referenced in `main.py` (lines 191–235) exist and import cleanly (post-`Client`-fix).
- **Legacy/parallel code present but NOT wired into main.py**: `backend/api/`, `backend/engines/`,
  `backend/domain/`, `backend/infra/`, `backend/data/`, `backend/core/`, `backend/middleware/`,
  `backend/main_v2.py` (v2.1 Phase-10 `create_app`), `backend/main copy.py`, `backend/main copy 2.py`.
  These do not affect Render startup.
- **Stale route modules not imported by the current chain** (import-safe, unused):
  `routes/admin/audit_logs.py`, `routes/admin/dashboard.py`, `routes/admin/document-types.py`,
  `routes/customer_verifications.py`, `routes/customer_dashboard.py`, `routes/communication.py`.
- **Duplicate/overlapping route prefixes**: `routes/admin/reviews.py` and `routes/admin/review_history.py`
  both use prefix `/api/admin/reviews`. Not a startup blocker; potential route shadowing.
- **No circular imports in the chain.**

## 9. Render-specific startup audit

- No Windows-only commands, no PowerShell, no hardcoded `127.0.0.1`/Docker container names, no
  local-Supabase ports in production code.
- `pdf_engine.py:21` hardcodes a Windows Tesseract path but guards it in `try/except`; on Linux it
  falls back to PATH, where Tesseract does not exist on a stock Render image → OCR feature fails at
  runtime (not startup).
- `pytesseract` + `pdf2image` need Tesseract and poppler system binaries; without a Dockerfile Render
  cannot apt-install them → OCR/PDF-repair endpoints will 500. Feature limitation, not a boot blocker.
- Startup does not connect to Supabase/Postgres (startup event is print-only; health check is lazy),
  so the app can boot even before env vars are configured (health reports degraded).
- `main.py` `__main__` block: `reload = os.getenv("RELOAD", "true")` — if Render runs `python main.py`,
  reload mode is on by default. Use `uvicorn main:app --host 0.0.0.0 --port $PORT` and `RELOAD=false`.

---

## A. CRITICAL — prevents Render startup

**A1. `Client` is not imported in staff.py**

```text
Problem:  NameError: name 'Client' is not defined — crashes module import, app never starts
File:     backend/routes/admin/staff.py
Line:     1405 (also 1733, 1786) — `supabase: Client = Depends(get_supabase_client)`
Root cause: line 11 imports `from supabase import create_client` but not `Client`.
           Annotations are evaluated at function-definition time; `Client` is unbound.
Evidence:  Render traceback; comparison with database.py/auth.py/emissions.py/reports.py/
           customer_documents.py/organizations/files.py which all import `Client`.
Recommended fix: change line 11 to `from supabase import create_client, Client`
Risk:      Trivial — one-line, mechanical, matches the established pattern elsewhere.
```

## B. HIGH — will likely fail immediately after startup

**B1. `backend/routes/admin/workload.py` is two concatenated files in one**

```text
Problem:  Two complete modules glued into one file (line 307 starts a second
          `# backend/routes/admin/workload.py` block that re-defines `router`
          at line 320 with prefix /api/admin/workload). The second `router`
          overwrites the first at module level, so the first block's routes —
          GET /api/admin/staff/workload, GET /api/admin/staff/workload/{staff_id},
          GET/PUT /api/admin/queue/settings, GET /api/admin/queue/stats,
          POST /api/admin/queue/reassign — are NEVER registered.
File:     backend/routes/admin/workload.py (lines 307–896)
Line:     320 (router redefinition)
Root cause: accidental file merge/append; only the second router survives include_router.
Evidence:  main.py:215 `app.include_router(workload.router)` attaches block 2's router only;
           API_ENDPOINTS.md documents the block-1 routes as expected endpoints.
Recommended fix: split into two files, or rename block-2's router and include it into the
           main router so both route sets register (keeps all existing imports working).
Risk:      HIGH for frontend integration (documented endpoints 404); no crash.
```

**B2. Dependency-file ambiguity — root `requirements.txt` is incomplete**

```text
Problem:  Repo-root requirements.txt (12 pkgs) is missing supabase/python-dotenv/pydantic;
          only backend/requirements.txt (19 pkgs) is runnable. Render currently uses the
          backend file (proven by the trace), but any dashboard re-configuration pointing
          at the root file causes an instant ModuleNotFoundError at main.py:3.
File:     requirements.txt (root) vs backend/requirements.txt
Root cause: two divergent dependency files with no marker of which is canonical.
Recommended fix: keep a single canonical file; set Render "Python requirements path" =
           backend/requirements.txt; optionally delete root requirements.txt (or make it a stub).
Risk:      LATENT CRITICAL — becomes a startup blocker the moment config changes.
```

**B3. PyJWT is an undeclared runtime dependency**

```text
Problem:  auth.py:4 `import jwt` is module-level; PyJWT appears in no requirements file.
          Works today only because supabase→gotrue installs it transitively.
File:     backend/auth.py line 4
Recommended fix: add `PyJWT>=2.0` (or a pinned version) to backend/requirements.txt.
Risk:     startup failure if a future supabase/gotrue upgrade drops the transitive dep.
```

**B4. `reportlab` not declared — OCR/PDF-repair feature breaks**

```text
Problem:  upload.py repair-pdf/OCR flow does `from reportlab.pdfgen import canvas`
          (lines 315–317) — ModuleNotFoundError on Render for /api/repair-pdf.
File:     backend/routes/upload.py (lazy import inside endpoint)
Recommended fix: add `reportlab` to backend/requirements.txt (if OCR repair is in scope).
Risk:      HIGH for the upload/repair feature; not a startup blocker.
```

**B5. Tesseract/poppler binaries absent on Render**

```text
Problem:  pytesseract + pdf2image need host binaries (tesseract, pdftoppm). No Dockerfile →
          Render can't apt-install. pdf_engine.py also hardcodes a Windows tesseract path
          (guarded). OCR paths will 500 at runtime.
Files:    backend/pdf_engine.py, backend/routes/upload.py
Recommended fix: either provision a Dockerfile with `apt-get install tesseract-ocr poppler-utils`,
          or formally mark OCR/repair as out-of-scope and return a clean error.
Risk:      HIGH for upload/OCR feature; not a startup blocker.
```

**B6. Start-command/env hygiene on Render**

```text
Problem:  main.py __main__ defaults RELOAD=true; uvicorn command-line without
          --host 0.0.0.0 binds 127.0.0.1; runtime.txt sits at repo root (missed if the
          Render root directory is backend/); pinned pandas 2.1.4/numpy 1.26.4 require
          Python ≤ 3.12 (3.13/3.14 have no wheels → build failure).
Files:    backend/main.py (RELOAD default), runtime.txt (location), Render dashboard config
Recommended fix: Start Command = `uvicorn main:app --host 0.0.0.0 --port $PORT`;
          set RELOAD=false; keep Python 3.11.9; place runtime.txt where the Render root
          directory can see it; set SUPABASE_URL / SUPABASE_SERVICE_KEY / SUPABASE_JWT_SECRET
          in the Render dashboard.
Risk:      HIGH if any of these are currently wrong; none are visible as the active blocker.
```

## C. MEDIUM — runtime/API problems

**C1. `AuthUser.is_admin` does not exist**
`upload.py:919` and `organizations/data.py:377` (and many other chain modules) reference
`current_user.is_admin`; `auth.py`'s `AuthUser` has no such field → `AttributeError`/500 on those
endpoints. Add `is_admin: bool = False` to `AuthUser` (populated in `get_current_user()`), or replace
with role checks.

**C2. `Depends(require_auth)` without parentheses**
`organizations/members.py:74` uses `Depends(require_auth)`; this injects the checker function (the
value returned by `require_auth()`) instead of `AuthUser` → `AttributeError` when the endpoint reads
`current_user.*`. Use `Depends(require_auth())`. (auth.py docstrings claiming "works with both" are
misleading.)

**C3. `fpdf==1.7.2` and `fpdf2==2.7.9` both installed**
Both provide the top-level `fpdf` module; last-in-line (fpdf 1.7.2) overwrites fpdf2.
`report_generator.py` imports `from fpdf import FPDF` — works but fragile; pip warns. Remove `fpdf==1.7.2`.

**C4. Overlapping `/api/admin/reviews` routers**
`reviews.py` and `review_history.py` share the prefix; potential route shadowing. FastAPI tolerates it;
align prefixes to avoid ambiguity.

**C5. Duplicate CORS origin**
`config.py` lists `https://www.carbontally.co.uk` twice (lines 26 & 32). Harmless; clean up.

**C6. Hardcoded anon key + URL in frontend** (`frontend/src/supabaseClient.js`) and the `.env` secret
misconfiguration described in §7. Not backend blockers; rotate/remove secrets.

## D. LOW — cleanup / maintainability (do not block UI/UX)

- Legacy parallel architecture not wired into `main.py`: `backend/api/`, `backend/engines/`,
  `backend/domain/`, `backend/infra/`, `backend/data/`, `backend/core/`, `backend/middleware/`,
  `backend/main_v2.py`.
- Legacy monolith copies: `backend/main copy.py`, `backend/main copy 2.py`,
  `backend/requirements copy.txt`.
- Stale route modules (import-safe, unregistered): `routes/admin/audit_logs.py`,
  `routes/admin/dashboard.py`, `routes/admin/document-types.py`, `routes/customer_verifications.py`,
  `routes/customer_dashboard.py`, `routes/communication.py`.
- `python-magic` declared but unused.
- `SUPABASE_ANON_KEY` read by `database.py` but unused.
- Probe/dev files at repo root (`_v3m12_*.py`, `tmp_*.txt`, `create_admin_dashboard.py`,
  `current_project_structure.txt`).
- Note: these files do NOT load at startup, so they cannot break Render.

## E. False positives / environment-only warnings

- **Pylance `Import "fastapi" could not be resolved` / `Import "pydantic" could not be resolved`**:
  environment/interpreter issue, NOT a production failure.
  - Packages are correctly declared (`backend/requirements.txt`).
  - Packages are installed on Render (the trace reached `staff.py:1405`, past every fastapi/pydantic import).
  - Local machine runs Python 3.14.3 vs project target 3.11.9; pinned pandas/numpy have no 3.14 wheels
    and no project venv exists — the local interpreter genuinely cannot resolve them.
- Local Supabase ports (`54321`–`54326`) and `127.0.0.1` DSNs appear only in tests, probe scripts, and
  `tmp_*` files — never in the production import chain.
- `http://localhost:8000` appears in `backend/.env` (`REACT_APP_API_URL`), tests, and frontend default
  URLs — none affect Render startup.

## F. Render deployment checklist (minimum to redeploy)

1. **Code:** `backend/routes/admin/staff.py` line 11 → `from supabase import create_client, Client`.
2. **Code:** Repair `backend/routes/admin/workload.py` concatenation so block-1 routes register.
3. **Code/deps:** Consolidate on `backend/requirements.txt`; add `PyJWT`; remove `fpdf==1.7.2`;
   add `reportlab` (only if OCR repair is required).
4. **Render config:**
   - Install: `pip install -r backend/requirements.txt` (requirements path = `backend/requirements.txt`).
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT` (run from `backend/`), `RELOAD=false`.
   - Python: 3.11 (runtime.txt honored at repo root; do NOT use 3.13/3.14 with pinned pandas/numpy).
   - Env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`, `RESEND_API_KEY`.
5. **Health:** `/health` and `/` return 200; `/docs` loads; routes_count matches expectations.
6. **Security:** remove `backend/.env` from version control, rotate the exposed service-role/anon keys.

## G. Recommended fix order

1. staff.py — add `Client` to the supabase import (unblocks Render startup; one line).
2. workload.py — split/remove the duplicated second module block (restores documented admin routes).
3. requirements consolidation — single canonical file, add `PyJWT`, drop `fpdf==1.7.2`, add `reportlab` if in scope.
4. Render dashboard — verify root dir/start command/requirements path, Python 3.11, env vars, `RELOAD=false`.
5. Runtime fixes — `AuthUser.is_admin` field (C1); `Depends(require_auth())` (C2).
6. OCR decision — Dockerfile with `tesseract-ocr` + `poppler-utils`, or explicitly disable OCR repair on Render.
7. Security hygiene — `.env` removal + key rotation; drive frontend Supabase config from env.
8. Cleanup (optional, non-blocking) — stale routes, `main copy*`, parallel packages, unused `python-magic`.

## READY FOR FIXES

The exact files that need modification to make the EXISTING CarbonTally V3 backend deployable on Render:

| File | Why |
|---|---|
| `backend/routes/admin/staff.py` | **Blocker.** Add `Client` to line 11 `from supabase import create_client, Client` — fixes `NameError` at lines 1405/1733/1786. |
| `backend/routes/admin/workload.py` | Restore block-1 routes lost to the concatenated second router (lines 307+). |
| `backend/requirements.txt` | Add `PyJWT`; remove conflicting `fpdf==1.7.2`; add `reportlab` if OCR repair stays in scope. |
| `backend/main.py` (optional) | `RELOAD` default → `false` in production; keep `HOST=0.0.0.0`. |
| Render dashboard (no file) | Start command `uvicorn main:app --host 0.0.0.0 --port $PORT` from `backend/`; requirements path `backend/requirements.txt`; Python 3.11; env vars `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`, `RESEND_API_KEY`. |
| `backend/.env` (security) | Remove from version control; rotate the exposed service-role secret; fix anon-key misassignment. |

**Bottom line:** the single active Render startup blocker is the missing `Client` import in
`backend/routes/admin/staff.py`. Fixing it lets the V3 import chain complete cleanly (verified
end-to-end); the remaining items are configuration, dependency hygiene, and runtime feature issues
that should be addressed in the order above before handing the backend to Lovable. No database,
schema, RLS, or emission-factor data was modified during this audit.







