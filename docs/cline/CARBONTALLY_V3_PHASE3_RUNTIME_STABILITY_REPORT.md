# CarbonTally — Phase 3: Runtime Stability & Fail-Closed Routing (Completion Report)

- **Task:** P1-A backend FD leak · P1-B fail-closed post-login routing · P3 Realtime diagnosis · regression coverage · live verification
- **Checkpoint:** `16391217103b98dcea520070c5a22c68f12fe607` (HEAD `main`, unchanged — no commits made)
- **Source of truth:** `docs/cline/CARBONTALLY_QA_V1_2_FORENSIC_TRIAGE.md`
- **Date:** 2026-08-31
- **Runtime verified:** frontend `:3000`, backend `:8050`, Supabase Auth/REST `127.0.0.1:54425`, Postgres `54426`

---

## 1. Root causes (re-confirmed before any change)

| ID | Root cause | Evidence |
|---|---|---|
| P1-A | `backend/auth.py:get_supabase_client()` created a **new service-role Supabase client on every call** (`create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)`; no caching, no close). `get_current_user` (the auth dependency on nearly every `/api/v3` endpoint and 15+ legacy route modules that import `get_supabase_client` **from auth**) called it per request. Under sustained load the process exhausted its 1024-FD soft limit and every authenticated request returned `500 … [Errno 24] Too many open files`. | Verified live pre-fix: backend held **1023/1024** FDs; every routing endpoint returned 500; `database.py`'s cached `get_supabase_client` was a different function (not the leak). |
| P1-B | Frontend post-login routing treated **any** API/network failure as "brand-new customer": `resolvePostLoginPath()` swallowed probe errors and fell through to `/onboarding`; `OnboardingPage.jsx` carried a 12 s fallback timer forcing the onboarding UI; `V3Layout.jsx` hardcoded `navigate('/onboarding')` for no-role users; `RoleRoute`/`useActorRoles` couldn't distinguish "no role" from "resolution failed" and bounced users to the public site. The documented `/api/v3/me/context` server-authoritative resolver was **absent** from the entire codebase. | Source inspection + live 404 for `/api/v3/me/context`; reproduced all three personas landing on `/onboarding` under the degraded backend. |
| P3 | Local Realtime unavailable: Kong's generated config routed `/realtime/v1` to upstream **`realtime-dev:4000`** which does **not resolve** in the Docker network (container is `supabase_realtime_carbon_ledger`) → gateway returned 503 for every Realtime route. | Kong container `getent hosts realtime-dev` → rc=2; `/realtime/v1/websocket` → 503; `supabase_realtime_carbon_ledger` is running+healthy and listens on 4000. |

---

## 2. Exact files changed

### Backend (modified)
| File | Change |
|---|---|
| `backend/auth.py` | `get_supabase_client()` now delegates to the **process-wide service-role singleton** `infra.supabase.get_service_client()` (the architecture's single client-construction point). Removed per-request `create_client`. Preserved the explicit `SUPABASE_SERVICE_KEY` check and the 500-error mapping. |
| `backend/database.py` | `get_supabase_admin()` now reuses the same singleton (previously created a fresh client per call). |
| `backend/main.py` | Shutdown event now also calls `infra.supabase.reset_service_client()` so the client/pool is released on shutdown. |
| `backend/api/router.py` | Registered the new `v3_context` and `v3_health` routers. |

### Backend (new)
| File | Purpose |
|---|---|
| `backend/api/v3_context.py` | **`GET /api/v3/me/context`** — single server-authoritative actor-context resolver (staff/entity→`/ops`, consultant→`/consultant`, org member→`/home`, no relationship→`/onboarding`). Reuses `AuthUser` (staff/org) and `resolve_consultant_context` (consultant) — no duplicated business logic. **Fail-closed:** resolution errors raise 500 (never "new user"). |
| `backend/api/v3_health.py` | **`GET /api/v3/health/realtime`** — bounded readiness probe of the exact gateway route the frontend websocket uses. Reports `up` (101 handshake), `down` (503/unreachable), `degraded` (gateway answers but no handshake). |

### Frontend (modified)
| File | Change |
|---|---|
| `frontend/src/v3/api.js` | Added `getMeContext()` (→ `/api/v3/me/context`, **throws** on failure/empty destination) and `goToWorkspace(navigate)`; rewrote `resolvePostLoginPath()` to use only the server context endpoint — never `/onboarding` on error. |
| `frontend/src/OnboardingPage.jsx` | Guard resolved via `getMeContext()`; **12 s fallback timer removed**; on failure renders a controlled error/retry (the onboarding form is never shown on error). |
| `frontend/src/v3/components/V3Layout.jsx` | Resolves the shell via `getMeContext()`; **hardcoded `navigate('/onboarding')` removed**; navigates to onboarding only when the server says so; on failure shows a controlled error/retry banner. |
| `frontend/src/v3/components/RoleRoute.jsx` | `useActorRoles()` resolves via `getMeContext()`; adds a `failed` state — a resolution failure renders a controlled error/retry (no silent public-site/onboarding bounce); a server-declared new user is sent to `/onboarding`. |
| `frontend/src/Login.js`, `AuthCallback.js`, `MagicLink.jsx`, `SelfServiceSignup.jsx`, `BetaSignup.jsx` | All `resolvePostLoginPath` call sites now use `goToWorkspace(navigate)` wrapped in fail-closed try/catch with a controlled error (never onboarding). |
| `frontend/src/v3/__tests__/api.test.js` | Rewrote the routing regression block for the me/context contract + added fail-closed tests (500 / network / empty-destination all reject). |

### No changes made to
Database, migrations, RLS, seed/demo data, `qa_harness/`, credentials, production config.

---

## 3. Tests added

| File | Coverage |
|---|---|
| `backend/tests/unit/api/test_supabase_client_lifecycle.py` | 6 tests — singleton across 300 calls (instances == 1), **no FD growth** across repeated calls (`/proc/self/fd`), missing-config → 500, create-client failure → 500, reset re-creates, admin surface reuses the same singleton. |
| `backend/tests/unit/api/test_v3_context.py` | 9 tests — staff→/ops, entity staff→/ops (+entity_id), consultant→/consultant, org member→/home (+org name), org owner→/home, new user→/onboarding, unauthenticated→401, **resolution failure→500 (never new user)** at HTTP and direct-call levels. |
| `backend/tests/unit/api/test_v3_health_realtime.py` | 5 tests — unconfigured, gateway-unreachable→down, 503→down, 101→up, endpoint structure. |
| `frontend/src/v3/__tests__/api.test.js` | 7 routing tests — customer→/home, staff→/ops, consultant→/consultant, new user→/onboarding, **500/network/empty-destination all REJECT** (fail-closed), plus the pre-existing `/login` no-session case. |

---

## 4. Test results

| Suite | Result |
|---|---|
| New backend unit tests (3 files) | **20/20 passed** |
| `backend/tests/unit` (full) | **Passed** (0 failures — all dots, 100%) |
| `backend/tests` (full incl. integration) | 16 failures, **all pre-existing** in `tests/integration/*` (test-DB drift: `add_client()` signature mismatch, `token`/schema drift, RLS delete-policy drift, `test_infra` creating a real client with a fake `test-service-key`). None exercise the changed code. |
| `frontend/src/v3/__tests__/api.test.js` | **32/32 passed** |
| `frontend` full suite | **133 tests passed, 0 failures**; `src/App.test.js` suite fails to *load* due to a pre-existing `react-router/dom` module-resolution issue (not caused by these changes; the app runs and builds). |
| Production build | **Compiled with warnings → bundle produced** (465 kB main.js). The `CI=true` build is blocked by **pre-existing** ESLint warnings in untouched files (`App.js`, `OperatorQueue.jsx`, …); the changed files introduce **no new warnings**. |


---

## 5. FD behavior before / after

| Metric | Before (pre-fix backend) | After (restarted with fix) |
|---|---|---|
| Backend process open FDs | **1023 / 1024** (soft limit exhausted) | **5** at boot; **12** after sustained load |
| Authenticated API calls | 500 (`[Errno 24] Too many open files`) on every endpoint | 200; healthy |
| 200 repeated authenticated `me/context` calls | would have leaked ~200+ clients | **7 → 8 FDs, 0 failures** (stable) |
| `auth.get_supabase_client()` client instances across 300 calls | 300 (one per call) | **1** (singleton) |

---

## 6. Authentication behavior

- Normal authentication (GoTrue password grant): **unchanged and working** — all 10 demo personas authenticate.
- Invalid/absent tokens: FastAPI `HTTPBearer` denies as before (401/403) — no change.
- Multiple users: 10-persona sweep authenticated + resolved contexts concurrently without error.
- Supabase client failure: now fails closed with HTTP 500 (same message contract as before), never silently "new user".
- Application shutdown: the service client + pool are released via the shutdown event.

---

## 7. Routing behavior (live browser verification)

| Scenario | Before | After |
|---|---|---|
| customer_owner login | `/onboarding` (probe 500s) | **`/home`** (V3 customer shell) |
| internal_operator login | `/onboarding` | **`/ops`** (Internal Operations, 56 batches) |
| consultant login | `/onboarding` | **`/consultant`** (Consultant workspace) |
| existing user + `me/context` API failure on `/home` | probe-chain → `/onboarding` | **stays on `/home`** with "We couldn't verify your access just now. Please try again. / Retry" |
| direct `/onboarding` + `me/context` failure | 12 s timer forced the form | **error/retry shown, form NOT shown** |
| genuinely new authenticated user | `/onboarding` | **`/onboarding`** (server decision — unchanged, D35 preserved) |
| anonymous → `/home` `/consultant` `/ops` `/messaging` | redirect to `/login` | **redirect to `/login`** (unchanged; ProtectedRoute untouched) |
| `/api/v3/me/context` for all 10 personas | 404 (absent) | **200 with correct destinations** (10/10 OK) |

---

## 8. Realtime diagnosis

**Classification: local Supabase configuration/runtime defect (not a CarbonTally application defect).**

- The application configuration is correct: `REACT_APP_SUPABASE_URL=http://127.0.0.1:54425` is the API gateway (`supabase/config.toml [api].port = 54425`), and `supabase-js` correctly derives `ws://127.0.0.1:54425/realtime/v1/websocket`.
- **Issue 1 (fixed operationally, local-only):** the Kong config routed Realtime to upstream `realtime-dev:4000`, which does not resolve (the container is `supabase_realtime_carbon_ledger`). Fixed by `sed 's/realtime-dev/supabase_realtime_carbon_ledger/g' /home/kong/kong.yml` + `kong reload` in the local Kong container → gateway now reaches Realtime (503 → 404).
- **Issue 2 (remaining, local stack):** the running Realtime container rejects the websocket handshake with `Phoenix.Router.NoRouteError` + `TenantNotFound: Tenant not found: 172` for the demo JWT (`iss: supabase-demo`) — a version/provisioning mismatch between the realtime container and the CLI-generated config in this stack. Realtime live-delivery therefore remains **degraded locally**.
- **Required configuration (documented, NOT applied to any repo/production config):** start this local stack with a matched Supabase CLI + config where the Kong Realtime upstream is the realtime container's resolvable name and the realtime service accepts the demo project's JWT issuer — or fix the tenant provisioning (`supabase start` regenerates kong.yml; the realtime container must be the CLI-managed one).
- **Readiness:** new `GET /api/v3/health/realtime` reports the honest state (`degraded`, 404) so the failure is no longer silent. Messaging authorization was **not** weakened to make Realtime pass.

---

## 9. Security regression results (live, read-only)

| Boundary | Result |
|---|---|
| PE staff → customer org `processing/status` | **403** (DENIED — unchanged) |
| PE staff → customer-org messaging | **403** (DENIED — unchanged) |
| consultant → generic org-member reports | **403** (DENIED — unchanged) |
| customer → internal `/api/v3/ops/me` | **403** (DENIED — unchanged) |
| customer → staff roster | **403** (DENIED — unchanged) |
| anonymous → `/api/v3/me/context` | denied (403, HTTPBearer) |
| anonymous → protected routes (browser) | settle on `/login` |
| RLS | **untouched** |


---

## 10. Remaining defects / limitations

1. **Local Realtime still degraded** (tenant-routing mismatch in the realtime container) — documented in §8; requires local-stack provisioning, not application code.
2. **`CI=true` production build** fails on pre-existing ESLint warnings in files outside this task's scope; the build compiles successfully without CI. A separate lint-hygiene pass is recommended.
3. **Integration test suite** has 16 pre-existing failures against the `carbontally_test` DB (signature/schema drift) — not caused by this task; needs a test-DB refresh + test updates.
4. **`src/App.test.js`** fails to load due to the pre-existing `react-router/dom` resolution issue.
5. The `me/context` response includes `organization.name` (one extra DB read per customer context) — acceptable; could be skipped if profile display is not needed.
6. The 12 s timer removal means the onboarding guard waits on `me/context` indefinitely if the network hangs; `v3Fetch`'s existing 25 s timeout bounds it, and the error/retry screen appears on failure.

## 11. PO decisions required

- **None required for the changes made.** Both P1 fixes implement documented, ratified intent (fail-closed routing; single server-authoritative context resolver; singleton service client). The previously identified **PE operational-messaging gap (PO-1 from the forensic triage) remains open and unchanged** — not part of this phase.

---

## 12. QA Harness Phase 6 — which previous findings should disappear and why

The QA Harness was **not modified**. After this remediation, the following previous findings are expected to clear on a re-run, with the reasoning:

| Previous finding | Expected outcome on re-run | Why |
|---|---|---|
| QA-AUTH-001..010 (all 10 personas land on `/onboarding`) | **Disappear** | Root cause (backend FD leak → role-probe 500s → probe-chain fallback) is fixed; routing now uses the server-authoritative `me/context` and is fail-closed. Live-verified: all 10 personas land on their correct workspaces; `me/context` resolves 10/10. |
| QA-UI-001..013 (console errors: 500s, ERR_CONNECTION_RESET, ERR_SOCKET_NOT_CONNECTED) | **Largely disappear** | The 500/reset half is the FD leak (fixed, FD-stable under load). The remaining `ERR_SOCKET_NOT_CONNECTED` realtime noise will clear once the local realtime tenant routing is provisioned (documented §8) — the app integration itself is correct. |
| QA-SEC-001 (anonymous `/home`) | **Disappear** | Was a first-load timing artifact of the harness check (settled state has always been `/login`); re-verified settled redirects for all protected routes. Harness settle-aware fix is separate (qa_harness not modified in this task). |
| QA-API-001, QA-WF-001, QA-WF-002 (3 API/workflow findings) | **Re-verify as harness expectation errors** | The app's 403s are the ratified boundaries (D20/N1) and remain intact (§9). The harness probe bindings (entity-scoped PE surface; consultant `clients/{id}/reports`; N1 PE messaging) need correcting in a separate harness task — as the forensic triage recommended. |
| Genuine-new-user onboarding, anonymous redirect, PE 403s | **Must remain** | Explicitly preserved (untouched boundaries). |

---

## 13. Data safety

- No database, migration, RLS, seed, or demo data was modified.
- No test data was created in the demo database (all verification used real demo identities read-only; browser probes used route interception / real form logins which only create Auth sessions).
- No secrets were committed or printed. The local Kong `kong.yml` was modified **inside the container only** (operational, local-only, regenerated by the CLI on next `supabase start`).
- Working tree: only the 14 modified + 5 new application/test files and the previous triage document; the pre-existing dirty tree (skills/tools etc.) was untouched.

## 14. Success criterion

> **A healthy CarbonTally runtime remains healthy under repeated authenticated requests, existing users are never routed to onboarding because of a transient API failure, and all existing security boundaries remain intact.**

**MET** — verified live: FD count stable (12) under 200 repeated authenticated requests with zero failures; existing users fail closed (error/retry) rather than onboarding when `me/context` fails; all security boundaries return 403; anonymous redirects hold; all 10 personas land on their correct workspaces.

