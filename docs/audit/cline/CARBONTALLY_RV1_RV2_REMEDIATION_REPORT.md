# CarbonTally — RV-1 + RV-2 Remediation Report

- **Date:** 2026-09-01
- **Checkpoint:** `16391217103b98dcea520070c5a22c68f12fe607` (unchanged — no commits)
- **Task:** Fix RV-1 (wire-level `WWW-Authenticate: Bearer` on HTTP 401) and RV-2 (make `DataSecurity` a public page at `/data-security`).
- **Status:** **BOTH ITEMS IMPLEMENTED_AND_VERIFIED.**

---

## 1. RV-1 — Root cause

OHD re-verification (P3, confirmed) pointed at `backend/main.py:337–350` and
`backend/auth.py:168–176`.

- `auth.get_current_user` correctly raises `HTTPException(401, "Not authenticated",
  headers={"WWW-Authenticate": "Bearer"})` for missing credentials.
- The **production composition root** (`backend/main.py`, served as `uvicorn main:app`)
  registers its own global `http_exception_handler` (`@app.exception_handler(HTTPException)`)
  which rebuilt the response as a fresh `JSONResponse(status_code=..., content={...})`
  **without forwarding `exc.headers`** — so the `WWW-Authenticate: Bearer` challenge never
  reached the actual HTTP response.
- The v2.1 app factory (`backend/api/router.py` `http_exception_handler`) fabricated the
  challenge for 401s but also did not forward `exc.headers` verbatim.

Net effect: `status_code == 401` was correct, but `response.headers["WWW-Authenticate"]`
was absent — breaking the RFC 7235/6750 auth-challenge contract.

## 2. RV-1 — Implementation (smallest correct fix)

Two minimal changes, both preserving the existing error envelope and semantics:

1. **`backend/main.py` — `http_exception_handler`:** added `headers=exc.headers` to the
   `JSONResponse` (envelope unchanged).
2. **`backend/api/router.py` — `http_exception_handler`:** now forwards `exc.headers`
   verbatim when present; when the exception carries no headers it keeps the previous
   behaviour (standard Bearer challenge for 401, no headers otherwise).

No redesign of the exception-handling system; no change to `auth.py`, the dependency
graph, or any API contract.

## 3. RV-1 — Wire-level test

New file: **`backend/tests/unit/api/test_auth_wire_headers.py`** (4 tests). It exercises
the real HTTP application — `TestClient` → routing → **real** `auth.get_current_user`
dependency (no overrides) → exception handler → wire response — and asserts on
`response.headers`, not merely `exc.headers`:

- `test_missing_credentials_wire_401_challenge_v21_app` — `create_app()` real chain:
  `status_code == 401` **and** `response.headers["WWW-Authenticate"] == "Bearer"`;
  envelope `error.code == "UNAUTHORIZED"`, `message == "Not authenticated"`,
  `request_id` string present.
- `test_missing_credentials_wire_401_challenge_composition_root` — the production
  `main.app` that OHD actually probed: `status_code == 401` **and**
  `response.headers["WWW-Authenticate"] == "Bearer"`; legacy envelope
  `success is False`, `error.code == 401`, `error.path` correct. (TestClient used
  without the context manager so Starlette does not run the startup worker.)
- `test_invalid_credentials_remain_wire_401` — invalid-credential 401 stays 401 on the wire.
- `test_insufficient_permission_remains_wire_403_no_challenge` — authenticated-but-
  insufficient-permission stays 403 and does **not** carry a Bearer challenge.

Existing tests were not weakened or deleted.

## 4. RV-1 — Test results

- `test_auth_wire_headers.py` + existing `test_auth_status_semantics.py`: **8/8 passed**.
- Full backend `tests/unit/api` suite (incl. new tests): **EXIT=0, all passed**.
- Remaining `tests/unit` (non-api): **EXIT=0, all passed**.

## 5. RV-2 — Routing decision

- Product decision honoured: **DataSecurity is a PUBLIC page** (no authentication).
- URL: **`/data-security`** — consistent with the existing public-policy naming
  (`/privacy`, `/cookies`, `/terms`); no duplicate route existed.
- `DataSecurity.jsx` was already a self-contained public page (no props; uses
  `AppHeader`/`AppFooter`/`Link`) — no redesign, content preserved.

## 6. DataSecurity public route

`frontend/src/App.js` (two lines only):

- `import DataSecurity from './DataSecurity';`
- `<Route path="/data-security" element={<DataSecurity />} />` placed in the **public**
  `<Routes>` block immediately after `/privacy` — **not** wrapped in `ProtectedRoute`,
  `RoleRoute`, or any auth/consultant/staff guard.

## 7. DataSecurity → Privacy navigation verification

- `DataSecurity.jsx` contains `<Link to="/privacy">View Privacy Policy</Link>` (line 441).
- `/privacy` remains routed in the same public block (`<PrivacyPolicy />`).
- New smoke test `frontend/src/DataSecurity.test.jsx` (3 tests):
  - renders the `<h1>Data Security at CarbonTally</h1>` standalone,
  - the "View Privacy Policy" link has `href="/privacy"`,
  - the "Contact CarbonTally" link has `href="/contact"`.
  - **Result: 3/3 passed.**
- `npm run build` compiled the new import + route successfully (verifies `/data-security`
  and `/privacy` both resolve at build/compile level).

## 8. Frontend test results

- New `DataSecurity.test.jsx`: **3/3 passed**.
- Existing `src/v3/__tests__/` suite: **14 suites / 166 tests passed**.
- `App.test.js`: **fails to LOAD** — pre-existing `react-router-dom@7` issue
  (`Cannot find module 'react-router/dom'` from `node_modules/react-router-dom/dist/index.js`).
  Confirmed present before this task (committed at `7ca9533`, unmodified). Per task
  instructions this unrelated dependency issue was **not** fixed in this task.

## 9. Build result

- `npm run build`: **SUCCESS** — `The build folder is ready to be deployed.` (EXIT=0).
  `main.c7bcb618.js` 470.86 kB (+4.45 kB — DataSecurity bundle), main CSS 48.56 kB.
  Only pre-existing eslint `exhaustive-deps` warnings.


## 10. Files changed (this task only)

| File | Change |
|---|---|
| `backend/main.py` | `http_exception_handler` forwards `exc.headers` (RV-1) |
| `backend/api/router.py` | `http_exception_handler` forwards `exc.headers` (RV-1) |
| `backend/tests/unit/api/test_auth_wire_headers.py` | **new** — wire-level RV-1 regression tests |
| `frontend/src/App.js` | DataSecurity import + public `/data-security` route (RV-2) |
| `frontend/src/DataSecurity.test.jsx` | **new** — public-page smoke test |
| `docs/audit/cline/CARBONTALLY_RV1_RV2_REMEDIATION_REPORT.md` | this report |

## 11. Database / migrations / RLS

**UNTOUCHED.** No SQL executed, no schema change, no migration created or applied, no RLS
policy modified. The only `supabase/config.toml` working-tree diff and untracked migration
files under `supabase/migrations/` are **pre-existing changes from the earlier migration
task** (verified: this session did not modify them).

## 12. Docker

**UNTOUCHED.** No Docker configuration modified (no `docker-compose.yml`/`Dockerfile`/
`docker/` exist in this repository). RV-3 (container networking) was intentionally not
attempted — handled separately by the operator.

## 13. Final safety check

- RV-1 fixed — both global HTTP exception handlers forward `exc.headers`. ✅
- Actual HTTP response contains `WWW-Authenticate: Bearer` (asserted on `response.headers`
  through the real HTTP app, both `create_app()` and `main.app`). ✅
- Wire-level regression tests pass (4/4 new; full `unit/api` EXIT=0). ✅
- DataSecurity publicly accessible at `/data-security` (no auth guard). ✅
- `/privacy` remains accessible (existing route untouched). ✅
- No database, migration, RLS, or Docker changes. ✅
- No unrelated frontend/backend changes (only the two exception handlers, App.js two-line
  routing change, and the two new test files). ✅
- No secrets exposed; no commits; no pushes. HEAD unchanged `1639121`. ✅

---

## Final status

| Item                              | Status   |
| --------------------------------- | -------- |
| RV-1 WWW-Authenticate wire header | VERIFIED |
| RV-1 wire-level test              | VERIFIED |
| RV-2 DataSecurity public route    | VERIFIED |
| DataSecurity → Privacy            | VERIFIED |
| Backend tests                     | VERIFIED |
| Frontend tests                    | VERIFIED |
| Frontend build                    | VERIFIED |

## Pre-existing issue (not in scope, reported only)

- `frontend/src/App.test.js` (and any Jest suite importing `react-router-dom`) cannot load:
  `react-router-dom@7.18.1` → `Cannot find module 'react-router/dom'`. Pre-existing
  dependency-install issue; not fixed per task instructions.

