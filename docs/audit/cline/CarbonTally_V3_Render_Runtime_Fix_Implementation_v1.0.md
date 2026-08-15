---
Document Type: Implementation Report (Render Runtime Fixes)
Project: CarbonTally
Architecture: CarbonTally V3 (Supabase + Render FastAPI + Lovable)
Version: 1.0
Status: IMPLEMENTED (pending runtime verification in a working shell)
Created: 2026-08-15
Author: Cline
Based On: docs/audit/cline/CarbonTally_V3_Render_Runtime_Readiness_Audit_v1.0.md
---

# CarbonTally V3 — Render Runtime Fix Implementation Report

## Purpose

Implement the fixes from sections A and B of the Render Runtime Readiness Audit
that are necessary for Render deployment, plus the C1/C2 runtime defects, so the
EXISTING CarbonTally V3 backend (`backend/main.py`) starts on Render and its
endpoints do not 500 on the audited defects.

Constraints honoured:

- No database, migrations, RLS, or emission-factor changes.
- No V3 architecture changes (main.py remains the sole entrypoint).
- No legacy-code cleanup.
- No commit / no push (working-tree changes only).

## Changes applied

### A1 (CRITICAL — Render startup blocker) — `backend/routes/admin/staff.py`

```diff
-from supabase import create_client
+from supabase import create_client, Client
```

Fixes `NameError: name 'Client' is not defined` at `staff.py:1405` (also `:1733`, `:1786`) —
the three `supabase: Client = Depends(get_supabase_client)` annotations evaluated at
function-definition time. Matches the established pattern in `emissions.py`, `reports.py`,
`customer_documents.py`, `organizations/files.py`, etc.

### B1 (HIGH) — `backend/routes/admin/workload.py` (concatenated duplicate module)

The file was two glued-together modules; the second block redefined `router`, silently
dropping block-1's routes. Fix:

- Line 320: block-2 router renamed → `workload_forecast_router = APIRouter(prefix="/workload", …)`
- Lines 356, 704, 760, 830: block-2 decorators → `@workload_forecast_router.…`
- Line 905 (EOF): `router.include_router(workload_forecast_router)` — registers BOTH route sets:
  - Block 1 (restored): `/api/admin/staff/workload`, `/api/admin/staff/workload/{staff_id}`,
    `/api/admin/queue/settings` (GET/PUT), `/api/admin/queue/stats`, `/api/admin/queue/reassign`
  - Block 2: `/api/admin/workload/forecast`, `…/summary`, `…/export`, `…/scenarios`
- Line 149: `data['updated_by'] = current_user.id` → `current_user.user_id` (the
  `update_queue_settings` route restored by this fix would otherwise 500 — `AuthUser` has
  `user_id`, never `id`).

`from .workload import get_queue_stats` in `routes/admin/reviews.py` still resolves
(block-1 function retained). FastAPI prefix arithmetic: `/api/admin` (outer) + `/workload`
(inner) + `/forecast` = `/api/admin/workload/forecast`.

### B3/B4 (HIGH) — `backend/requirements.txt`

- **Added** `PyJWT==2.8.0` — was only a transitive dependency (supabase→gotrue) but
  `auth.py:4` does module-level `import jwt`; now declared explicitly.
- **Added** `reportlab==4.1.0` — lazy-imported by the `repair-pdf`/OCR flow in
  `routes/upload.py` (`from reportlab.pdfgen import canvas`).
- **Removed** `fpdf==1.7.2` — conflicted with `fpdf2==2.7.9` (both install the `fpdf`
  top-level module; last-in-line wins).

Final `backend/requirements.txt`:

```text
fastapi==0.109.0
uvicorn==0.27.0
pandas==2.1.4
numpy==1.26.4
python-multipart==0.0.6
pdfplumber==0.10.3
pytesseract==0.3.10
pdf2image==1.16.3
Pillow==10.2.0
reportlab==4.1.0
python-magic==0.4.27
resend==0.5.1
fpdf2==2.7.9
python-dotenv==1.0.1
pypdf2==3.0.1
supabase==2.9.0
PyJWT==2.8.0
openpyxl==3.1.5
email-validator>=2.0.0
pydantic[email]>=2.0.0
```

### C1 (MEDIUM) — `backend/auth.py` + reference sites

- `AuthUser` model: added `is_admin: bool = False` (auth.py line 70).
- `get_current_user()`: populates `is_admin=(role == 'admin' or role_name == 'admin')`
  (auth.py line 278).
- This fixes every `current_user.is_admin` reference at once:
  `routes/upload.py` (810/919/969), `routes/emissions.py` (357/422/488/552),
  `routes/admin/reviews.py` (525), `routes/feedback.py` (146),
  `routes/document_activity.py` (54/221), `routes/drafts_enhanced.py` (56/133/208),
  `routes/organizations/data.py` (377).

Adjacent `current_user.id` → `current_user.user_id` fixes (same defect family, in the
exact `is_admin` code paths; `AuthUser` has `user_id`, never `id`):

- `routes/upload.py` lines 814, 923, 972 (batch view/cancel/stats access checks).
- `routes/admin/workload.py` line 149 (queue-settings update, restored by B1).

### C2 (MEDIUM) — `backend/routes/organizations/members.py`

```diff
-    current_user: AuthUser = Depends(require_auth)
+    current_user: AuthUser = Depends(require_auth())
```

`Depends(require_auth)` injected the returned checker *function* (not the user) →
`AttributeError` at request time. Verified this was the only bare occurrence in production
code (auth.py docstrings mention both forms but the implementation only works with
parentheses).

## New file — `backend/verify_startup.py`

An executable verification harness that:

- Reproduces the exact Render import chain (`import main`, i.e. `uvicorn main:app`).
- Runs static source checks for every fix above (no third-party packages required).
- When dependencies are installed, runs runtime checks:
  - `AuthUser.is_admin` attribute exists (default `False`; populated by `get_current_user`).
  - Workload router registers all 9 expected paths (block-1 queue/staff + block-2 forecast).
  - Staff router imports and carries routes.
- Exits non-zero if any check fails.

Run with:

```bash
cd backend
python -m pip install -r requirements.txt
python verify_startup.py
```

## Verification status

**Runtime execution was NOT possible in the implementing session.** The shell tool was wedged
on a hung `docker exec … psql` process against the remote Supabase pooler from a previous
session (visible terminal output: `FATAL: password authentication failed for user "postgres"`).
Every command — including `true`, `pwd`, and file redirection — failed before execution, so
`python`, `pip`, `pytest`, and `uvicorn` could not be invoked.

What WAS performed instead:

1. **Static verification of every edit** — each change re-read in full post-edit and confirmed:
   - `Client` is imported and used correctly in `staff.py` (lines 1405/1733/1786 annotations now resolve).
   - `workload_forecast_router` is defined (line 320) before all 4 block-2 decorators and before
     `router.include_router(workload_forecast_router)` at EOF; no stray `@router.` decorators
     remain in block 2; `reviews.py`'s `from .workload import get_queue_stats` still resolves.
   - FastAPI prefix arithmetic yields `/api/admin/workload/forecast*` (outer `/api/admin` +
     inner `/workload` + route path).
   - `requirements.txt` content verified line-by-line.
   - `AuthUser.is_admin` field + `get_current_user()` population verified.
   - `Depends(require_auth())` is the only auth-dependency form in `members.py` (no bare usage).
   - No `current_user.id` remains in `routes/upload.py` (three occurrences fixed; full file scanned).
2. **`backend/verify_startup.py`** created so the full verification runs in one command when the
   shell is available.

Commands to run when the shell is free (from `d:\carbon_ledger\backend`, Python 3.11.x —
the pinned `pandas==2.1.4`/`numpy==1.26.4` need Python ≤ 3.12; the local machine currently
defaults to 3.14.3):

```bash
cd backend
python -m pip install -r requirements.txt
python verify_startup.py            # import-chain + all fix checks
uvicorn main:app --host 0.0.0.0 --port 8000   # then curl http://127.0.0.1:8000/health
python -m pytest tests/unit -q      # unit suite (integration tests need the local Supabase stack)
```

## Files changed (working tree only — no commit, no push)

| File | Change |
|---|---|
| `backend/routes/admin/staff.py` | `from supabase import create_client, Client` (A1 — Render blocker) |
| `backend/routes/admin/workload.py` | B1: renamed block-2 router to `workload_forecast_router`, re-pointed 4 decorators, appended `router.include_router(...)`; line 149 `current_user.id` → `user_id` |
| `backend/requirements.txt` | B3/B4: added `PyJWT==2.8.0`, added `reportlab==4.1.0`, removed `fpdf==1.7.2` |
| `backend/auth.py` | C1: `is_admin: bool = False` field; populated in `get_current_user()` |
| `backend/routes/organizations/members.py` | C2: `Depends(require_auth())` |
| `backend/routes/upload.py` | C1-adjacent: `current_user.id` → `current_user.user_id` at lines 814, 923, 972 |
| `backend/verify_startup.py` | NEW — Render startup / fix verification harness |

## NOT changed (per constraints)

- Database, migrations, RLS, emission factors — untouched. No DB operations were performed.
- Legacy code — untouched (`main copy*.py`, `api/engines/domain/infra`, stale route modules,
  `main_v2.py`, root `requirements.txt`).
- V3 architecture — unchanged; `main.py` remains the sole entrypoint.

## Remaining recommendations (out of scope for this change set)

- Root `requirements.txt` still lacks `supabase`/`python-dotenv`/`pydantic` and diverges from
  `backend/requirements.txt` — align or delete as a config decision so Render's requirements path
  cannot accidentally point at the wrong file.
- `current_user.id` remains in ~30 other production call sites (`routes/admin/beta.py`,
  `routes/admin/bulk.py`, `routes/admin/settings.py`, `routes/customer_documents.py`,
  `routes/customer_dashboard.py`, etc.) — a separate pre-existing defect.
- Render dashboard: `RELOAD=false`, start command `uvicorn main:app --host 0.0.0.0 --port $PORT`
  run from `backend/`, env vars `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`,
  `RESEND_API_KEY`; keep Python 3.11.
- OCR/repair feature still needs host binaries (tesseract/poppler) or an explicit decision to
  disable it on Render (B5 of the audit).
- Security: remove `backend/.env` from version control and rotate the exposed service-role secret
  (the `.env` sets anon-key vars to the service-role secret value).

## Related documents

- `docs/audit/cline/CarbonTally_V3_Render_Runtime_Readiness_Audit_v1.0.md` (this audit)
- `docs/audit/cline/CarbonTally_V3_ADR-V3-004_Implementation_Verification_Audit_v1.0.md`


