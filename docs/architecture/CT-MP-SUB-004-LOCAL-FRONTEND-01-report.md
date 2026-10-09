# CT-MP-SUB-004-LOCAL-FRONTEND-01 — Local Frontend Startup & Sign-In Diagnosis

- **TASK ID:** `CT-MP-SUB-004-LOCAL-FRONTEND-01`
- **Parent work item:** `CT-MP-SUB-004` (Manual Processing Commercial & Entitlement UI/UX)
- **Date:** 2026-10-04
- **Nature:** environment/diagnosis only. **No application code, database, schema,
  data, configuration or deployment was changed.**
- **Governance:** LOCAL / DEMO LAB ONLY. Production was **not** accessed, modified,
  migrated, seeded, reset or deployed to. Nothing was committed or pushed.

Evidence labels used: `CODE-TRACED` · `RUNTIME-OBSERVED` · `BROWSER-VERIFIED` ·
`INFERENCE` · `LIMITATION`.

---

## 1. Environment

| Item | Value | Source |
| --- | --- | --- |
| Repository | `/home/shomonrobie/ct_93d5cdd` | `RUNTIME-OBSERVED` |
| Branch | `p8-release-reconciled` | `git rev-parse --abbrev-ref HEAD` |
| HEAD | `375a48dc1b9e9cfd74090bbf747554ae997acb59` | `git rev-parse HEAD` |
| Working tree | 132 pre-existing entries (unrelated to this task); **unchanged by this task** | `git status --porcelain` before/after |
| Frontend dev server | CRA (`react-scripts start`), pid 315566, cwd `frontend/`, started **Sun Oct 4 19:14:45 2026** | `ps`, `readlink -f /proc/315566/cwd` |
| Backend (FastAPI) | `uvicorn main:app --host 127.0.0.1 --port 8070`, pid 312590, cwd `backend/` | `/proc/312590/cmdline` |
| Chrome (diagnostic driver) | Google Chrome **152.0.7977.64** (`/usr/bin/google-chrome`) | `google-chrome --version` |
| Node (CDP driver) | **v24.21.0** (global `WebSocket`) | `node -v` |

No Playwright/Puppeteer/`websockets` package is installed in either the repository
venv or the system Python, so the browser evidence below was gathered with a
**dependency-free CDP client written for this task** (headless Chrome +
`--remote-debugging-port` + Node's built-in `WebSocket`). The driver is a
throwaway diagnostic script under `/tmp`; **it is not part of the repository.**

---

## 2. Commands run (representative)

```bash
# Git / process / port facts
git rev-parse --abbrev-ref HEAD ; git rev-parse HEAD ; git status --porcelain
ps -o pid,lstart,cmd -p 315566 ; readlink -f /proc/315566/cwd
tr '\0' ' ' < /proc/312590/cmdline ; readlink -f /proc/312590/cwd
ss -ltnp | grep -E ':(3100|3000|8070|54430|8888)'
curl -s -o /dev/null -w '%{http_code}' http://localhost:3100/
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8070/health
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:54430/

# Frontend configuration actually in force
cat frontend/.env.local ; cat frontend/package.json
curl -s http://localhost:3100/ | grep -o 'static/js/[^"]*\.js'   # bundle name
curl -s http://localhost:3100/static/js/bundle.js -o /tmp/bundle.js

# Demo Lab auth reachability + CORS behaviour (read-only)
curl -i  http://127.0.0.1:54430/auth/v1/health
curl -i -X POST -H 'apikey: <lab anon key>' -H 'Content-Type: application/json' \
     -d '{"email":"probe@example.invalid","password":"x"}' \
     'http://127.0.0.1:54430/auth/v1/token?grant_type=password'
# Origin matrix on the gateway and on the backend
for O in http://localhost:3000 http://127.0.0.1:3100 http://localhost:3100 \
         http://localhost:8070 ; do
  curl -D - -o /dev/null -X OPTIONS -H "Origin: $O" \
    -H 'Access-Control-Request-Method: POST' \
    -H 'Access-Control-Request-Headers: apikey,content-type' \
    http://127.0.0.1:54430/auth/v1/token | grep -iE 'HTTP/|allow-origin'
done
curl -D - -o /dev/null -H 'Origin: http://localhost:3100' http://127.0.0.1:8070/health

# Auth-container topology (read-only inspection; no modification)
docker inspect supabase_auth_carbon_ledger | grep -E 'GOTRUE_SITE_URL|EXTERNAL'

# Browser evidence (dependency-free CDP driver, /tmp only)
node /tmp/cdp2.cjs > /tmp/cdp_out.txt 2>&1

# Control: same password grant, two different Origins (token never printed)
python /tmp/token_probe.py > /tmp/token_out.txt 2>&1
```

Grep/reads of the implementing sources:

```bash
grep -rn 'AuthServiceUnavailable|isAuthServiceUnavailable' frontend/src
cat  frontend/src/AuthServiceUnavailable.jsx frontend/src/lib/authErrors.js
sed -n '1,120p'   frontend/src/Login.js       # session-restore path
sed -n '150,265p' frontend/src/Login.js       # password + OAuth paths + notice render
cat  frontend/src/supabaseClient.js frontend/src/v3/api.js frontend/src/services/apiClient.js
grep -n 'ALLOWED_ORIGINS' -A8 backend/config.py
sed -n '130,262p' tools/demo_lab/stack.py     # gateway CORS generation
grep -rn 'localhost:3000|:3100' docs/ tools/  # prior art
```

---

## 3. Frontend startup result

The frontend **did** start and compile successfully, and it **is** reachable.

| Check | Result |
| --- | --- |
| Process | `react-scripts/scripts/start.js`, pid 315566, cwd `/home/shomonrobie/ct_93d5cdd/frontend` `RUNTIME-OBSERVED` |
| Listener | `LISTEN 0 511 0.0.0.0:3100` (pid 315566) `RUNTIME-OBSERVED` |
| `GET http://localhost:3100/` | **HTTP 200** `RUNTIME-OBSERVED` |
| Served `index.html` | Correct CarbonTally shell (title, OG/Twitter meta, `manifest.json`, favicon) `RUNTIME-OBSERVED` |
| Bundle | `static/js/bundle.js`, 14,042,024 bytes (unminified dev build) `RUNTIME-OBSERVED` |
| Browser render of `/login` | **Renders correctly** — page title, "Continue with Google", email + password inputs, "Sign In" button, "Create Account" toggle, GDPR badge. `BROWSER-VERIFIED` |
| Auth-unavailable notice on first load | **Not shown** (`hasNotice: false`) `BROWSER-VERIFIED` |

So the reported symptom is **not** "the frontend failed to start / failed to compile /
cannot be reached". The page loads and the sign-in form is fully usable — it is the
**sign-in request itself** that fails (see §6).

---

## 4. URLs and ports actually used

| Role | Value actually in use | Source |
| --- | --- | --- |
| Frontend dev server | `http://localhost:3100` (listens on `0.0.0.0:3100`) | `frontend/.env.local` → `PORT=3100`; listener observed |
| Backend API base | `http://localhost:8070` | `frontend/.env.local` → `REACT_APP_API_URL=http://localhost:8070` |
| Backend (process) | `127.0.0.1:8070`, `/health` → **HTTP 200** | `uvicorn` cmdline; `curl` |
| Supabase/auth URL | `http://127.0.0.1:54430` | `frontend/.env.local` → `REACT_APP_SUPABASE_URL=http://127.0.0.1:54430` |
| Demo Lab gateway | `127.0.0.1:54430` (nginx container `carbontally_demo_lab_gateway`, `127.0.0.1:54430->80/tcp`) | `docker ps`; `Server: nginx/1.31.6` |
| Gateway → auth upstream | gateway `/auth/v1/` → `supabase_auth_carbon_ledger:9999` (GoTrue); also published as `54425` via Kong | `tools/demo_lab/stack.py`; `docker ps` |
| GoTrue version | `v2.195.0` (`GET /auth/v1/health` → 200) | `RUNTIME-OBSERVED` |
| Hindsight | `0.0.0.0:8888` (unrelated, listening) | `ss -ltnp` |
| **Canonical browser origin the local stack expects** | **`http://localhost:3000`** | see §6 |

### 4.1 The `.env.local` values really were applied (not a stale-env bug)

The running bundle was downloaded and inspected for the exact env values, proving
CRA picked up `frontend/.env.local` correctly:

```
127.0.0.1:54430                       count=3   -> REACT_APP_SUPABASE_URL applied
http://localhost:8070                 count=21  -> REACT_APP_API_URL applied
"REACT_APP_SUPABASE_URL":"http://127.0.0.1:54430"         (inlined env object)
<lab anon key payload segment>        count=2   -> lab anon key (iss=supabase-demo) applied
<lab anon key signature segment>      count=2   -> same key's signature segment
sb_publishable_… (fallback value)     count=0   -> production fallback NOT used
```

(Exact key strings deliberately not reproduced; see §10.)


`RUNTIME-OBSERVED`. **Conclusion:** the Supabase URL, the lab anon key and the API
base URL are all correctly baked into the running frontend. The failure is therefore
**not** a missing or stale environment variable.

> `LIMITATION`: the current `frontend/.env.local` is a local, gitignored file whose
> header states it exists to override the production defaults hard-coded in
> `frontend/src/supabaseClient.js`. Its `PORT=3100` line is the load-bearing value
> for this incident (§6). No secret value is reproduced in this report.

---

## 5. Auth flow and configuration discovered

### 5.1 How sign-in is wired `CODE-TRACED`

```
frontend/src/supabaseClient.js
  createClient(REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY)
  fallback (only if env missing): https://pvwiojoyaqywtydzcpbg.supabase.co + sb_publishable_…
        │
        ▼
frontend/src/Login.js  (route /login)
  • mount effect → supabase.auth.getSession()        (session restore; "session" context)
  • supabase.auth.onAuthStateChange(SIGNED_IN …)
  • handleAuth() → supabase.auth.signInWithPassword({email,password})
  • handleGoogleSignIn() → supabase.auth.signInWithOAuth({provider:'google'})
  • on success → goToWorkspace(navigate)             (server-authoritative landing)
  • catch → isAuthServiceUnavailable(err) ? setAuthUnavailable('password'|'session'|'oauth')
                                         : setError(<credential message>)
        │
        ▼
frontend/src/lib/authErrors.js   classifyAuthError()
  UNAVAILABLE_STATUSES = [0, 429, 500, 502, 503, 504]
  UNAVAILABLE_TEXT = ['failed to fetch','networkerror','load failed','timeout', …]
        │
        ▼
frontend/src/AuthServiceUnavailable.jsx   (data-testid="auth-service-unavailable")
  detailByContext = { callback | session | oauth }   ← note: NO 'password' key
  default detail  = 'We could not reach the CarbonTally sign-in service…'
```

`frontend/src/v3/api.js` and `frontend/src/services/apiClient.js` resolve the API base
as `process.env.REACT_APP_API_URL || 'http://localhost:8000'` and obtain the bearer
token from `supabase.auth.getSession()` — i.e. **every authenticated API call depends
on the same Supabase auth session.**

### 5.2 Local stack configuration that governs browser auth `CODE-TRACED`

| Layer | Setting | Value |
| --- | --- | --- |
| Gateway (nginx, `carbontally_demo_lab_gateway`) | `map $http_origin $lab_cors_origin { default ""; "<BROWSER_ORIGIN>" $http_origin; }` then `add_header Access-Control-Allow-Origin $lab_cors_origin always` | `tools/demo_lab/stack.py:241–246`; `BROWSER_ORIGIN = "http://localhost:3000"` (`stack.py:147`) |
| Gateway | `location /auth/v1/ { …CORS… proxy_pass http://supabase_auth_carbon_ledger:9999/; }` | `stack.py:250–251` |
| GoTrue | `GOTRUE_SITE_URL=http://localhost:3000`, `GOTRUE_URI_ALLOW_LIST=https://localhost:3000` | `docker inspect supabase_auth_carbon_ledger` |
| Backend FastAPI | `Config.ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "https://carbontally.co.uk", …]` → `CORSMiddleware(allow_origins=…)` | `backend/config.py:23–29`, `backend/main.py:177` |
| Frontend (this run) | `PORT=3100` | `frontend/.env.local:6` |

Stack.py's own comment (lines 144–146) states the intent plainly:

> *"DR-003 — the lab's canonical browser origin: the CRA dev server the release
> frontend runs on. Mirrors `backend/config.py` ALLOWED_ORIGINS
> ("http://localhost:3000") and the local stack GoTrue `GOTRUE_SITE_URL`, so app,
> backend and gateway agree on one origin."*

**Three independent layers are hard-aligned on `http://localhost:3000`; the running
frontend is on `http://localhost:3100`.**

---

## 6. Exact failure observed

### 6.1 The failing request `BROWSER-VERIFIED`

A real sign-in was performed **through the UI** in headless Chrome (page origin
`http://localhost:3100`, a Demo Lab identity, fresh browser profile) by filling the
email/password inputs with React-compatible input events and clicking the form's
`button[type=submit]`. Raw CDP output:

```
=== STAGE 1: /login initial load ===
  url        : http://localhost:3100/login
  title      : CarbonTally — Carbon Data Processing & Emissions Management Platform
  form state : {"hasEmail":true,"hasPassword":true,"hasSubmit":true,"hasNotice":false,
                "bodyStart":"🌱 CarbonTally Automated Carbon Accounting for UK Businesses
                 Continue with Google or Email Password Sign In …"}
  auth/token events in stage 1: (only a gstatic google.svg asset)

=== STAGE 2: demo sign-in attempt via the UI ===
  submit result: submitted

  --- network outcomes touching auth/token ---
    [loadingFailed] {"url":"http://127.0.0.1:54430/auth/v1/token?grant_type=password",
                     "method":"POST","errorText":"net::ERR_FAILED",
                     "corsErrorStatus":{"corsError":"PreflightMissingAllowOriginHeader"},
                     "type":"Fetch"}
    [response]      {"url":"http://127.0.0.1:54430/auth/v1/token?grant_type=password",
                     "status":204}

  --- console output (post-submit) ---
    [log-error] Access to fetch at
       'http://127.0.0.1:54430/auth/v1/token?grant_type=password' from origin
       'http://localhost:3100' has been blocked by CORS policy: Response to preflight
       request doesn't pass access control check: No 'Access-Control-Allow-Origin'
       header is present on the requested resource.
    [log-error] Failed to load resource: net::ERR_FAILED
    [error]     TypeError: Failed to fetch
    [error]     FULL ERROR OBJECT: AuthRetryableFetchError: Failed to fetch
                  at _handleRequest (bundle.js:107211)
                  at async _request (bundle.js:107194)
                  at async SupabaseAuthClient.signInWithPassword (bundle.js:100852)
                  at async handleAuth (bundle.js:13063)

  --- rendered UI after attempt ---
    {"shown":true,"text":"🌱 CarbonTally CarbonTally sign-in is temporarily unavailable
      We could not reach the CarbonTally sign-in service. This is a temporary problem on
      our side, not a problem with your account. This is a temporary service
      interruption. Your account and your organisation’s data have not been deleted or
      lost. Please wait a moment and try again. Try again Privacy Policy …"}
```

**The rendered UI text is character-for-character the symptom reported in the task.**
The exact failing request is therefore:

```
POST http://127.0.0.1:54430/auth/v1/token?grant_type=password
     (supabase.auth.signInWithPassword, from frontend/src/Login.js handleAuth)
-> OPTIONS preflight answered 204 without Access-Control-Allow-Origin
-> browser aborts: net::ERR_FAILED / TypeError: Failed to fetch
-> authErrors.classifyAuthError() -> AUTH_SERVICE_UNAVAILABLE
-> Login.js setAuthUnavailable('password')
-> <AuthServiceUnavailable context="password"> -> default sentence
```

Why the *generic* sentence rather than a password-specific one: `Login.js` passes
`context='password'`, but `AuthServiceUnavailable.detailByContext` only defines
`callback`, `session`, `oauth` — so `'password'` falls through to the default string.
This is a **pre-existing wording gap, not the cause** (see §8, item B2).

### 6.2 Control — the auth service and the credentials work fine `RUNTIME-OBSERVED`

Same password grant, same credentials, two different `Origin` headers (token presence
reported; **no token value printed**):

| Origin | `OPTIONS` preflight | `Access-Control-Allow-Origin` | `POST …/token?grant_type=password` |
| --- | --- | --- | --- |
| `http://localhost:3000` | 204 | `http://localhost:3000` | **HTTP 200 — access_token PRESENT** |
| `http://localhost:3100` | 204 | **ABSENT** | HTTP 200 — access_token PRESENT |

The second row is the smoking gun: **GoTrue authenticated the demo user and issued a
real session token for the request coming from `:3100`, but returned no
`Access-Control-Allow-Origin`, so the browser discarded the successful response.**
The failure is at the browser boundary — not in the auth service, not in the
credentials.

### 6.3 Origin grant matrix `RUNTIME-OBSERVED`

`OPTIONS /auth/v1/token` on the Demo Lab gateway (54430):

| Sent `Origin` | Result |
| --- | --- |
| `http://localhost:3000` | 204 + **`Access-Control-Allow-Origin: http://localhost:3000`** |
| `http://127.0.0.1:3100` | 204, **no ACAO** |
| `http://localhost:3100` | 204, **no ACAO** |
| `http://localhost:8070` | 204, **no ACAO** |
| *(no Origin)* | 204, no ACAO |
| `http://localhost:3100` (simple `GET /auth/v1/health`) | 200, **no ACAO** |

`GET /health` on the release backend (8070):

| Sent `Origin` | Result |
| --- | --- |
| `http://localhost:3100` | 200, **no `access-control-allow-origin`** |
| `http://localhost:3000` | 200, **`access-control-allow-origin: http://localhost:3000`** |

And from page context (`BROWSER-VERIFIED`), all three probes from origin
`http://localhost:3100` fail:

```
  lab auth health       : {"threw":"TypeError: Failed to fetch"}
  lab auth token(POST)  : {"threw":"TypeError: Failed to fetch"}
  backend health        : {"threw":"TypeError: Failed to fetch"}
    [loadingFailed] /auth/v1/health   corsError=PreflightMissingAllowOriginHeader
    [loadingFailed] /auth/v1/token    corsError=PreflightMissingAllowOriginHeader
    [loadingFailed] :8070/health      corsError=MissingAllowOriginHeader
```

Both the Demo Lab gateway **and** the release backend refuse the `:3100` origin, so
the app cannot authenticate *and* could not call the V3 API even if it could.

---

## 7. Diagnosis

**Category: A + E** — frontend environment/configuration ↔ browser **CORS** boundary.

> The frontend is being served from `http://localhost:3100`, but every CORS-consuming
> layer of the local stack (Demo Lab gateway, GoTrue, FastAPI) grants access to exactly
> `http://localhost:3000`. The sign-in request therefore never passes the browser's
> CORS check, and the app correctly reports "sign-in service unreachable".

Not the cause (each explicitly ruled out by evidence above):

| Candidate | Verdict | Evidence |
| --- | --- | --- |
| **C. Demo Lab auth service broken** | **Ruled out** | `/auth/v1/health` → 200 GoTrue v2.195.0; same grant with `Origin: :3000` returns HTTP 200 + token (§6.2) |
| **D. Backend connectivity** | **Ruled out** | `:8070/health` → 200 via `curl`; the browser block is CORS, not reachability (`MissingAllowOriginHeader`) |
| **A(bad env). Frontend env not loaded** | **Ruled out** | Bundle contains the exact lab Supabase URL, lab anon key and `:8070` API base (§4.1) |
| **B. Frontend auth implementation** | **Ruled out as a defect** | The code does what it is designed to do: a genuine network-level failure is classified `AUTH_SERVICE_UNAVAILABLE` and is *not* masked as bad credentials — exactly the behaviour required by `P3-F02`/`P3-F06` |
| **F. Something else** | **None identified** | The only failing parameter is the `Origin` allow-list |

### 7.1 This is a known, previously documented environment condition

`docs/demo-investor/DR-003-demo-lab-cors-browser-verification.md` (2026-09-20) reached
the same architecture and already recorded `PORT=3100` as an unresolved environment
mismatch:

- §5 security matrix: *"`Origin: http://localhost:3100` → **no** ACAO"* (used there as a
  negative control).
- §6 port architecture: *"Stale local value | `PORT=3100` in gitignored
  `frontend/.env.local` | inconsistent with `ALLOWED_ORIGINS` (3000/3001/3002) and with
  the gateway grant"*.
- §6: *"the frontend was simply run on the already-authorised origin `3000`."*
- §20.2: *"`PORT=3100` … still disagrees … browser auth requires the frontend to run on
  `3000`."*
- §21.3 (PO decision): *"Decide whether to align `frontend/.env.local PORT=3100` with
  `ALLOWED_ORIGINS` (or add `3100` to the backend allow-list) — or to document 'run the
  lab frontend on :3000'."*

This report therefore **confirms and re-proves** a pre-existing condition with fresh
runtime/browser evidence; it is **not** a new regression and **not** caused by
CT-MP-SUB-004.

### 7.2 Impact on the parent task

**CT-MP-SUB-004's browser-level acceptance is currently blocked by this environment
condition, not by any defect in CT-MP-SUB-004.** With auth blocked at the origin
boundary, no authenticated surface (Operations "Commercial Coverage", Consultant
"Manual Processing", or Customer `/manual-processing`) can be reached in a browser on
`:3100`, so UI visual/functional acceptance cannot proceed until the origin is aligned.

---

## 8. Does the fix require application code changes?

**No application-code change is required to resolve the reported failure.** The
fastest, zero-risk, fully reversible remedy is an **environment/ops** action (run the
frontend on the already-authorised origin), which changes no file in the repository.

For completeness, the two candidate remedies and their true cost:

| Option | What changes | Files touched | Risk |
| --- | --- | --- | --- |
| **R1 (recommended). Run the lab frontend on `:3000`** | Nothing in the repo — restart CRA on the canonical origin (e.g. `PORT=3000` in `frontend/.env.local`, or run on `:3000` and drop the override). Matches `ALLOWED_ORIGINS`, `GOTRUE_SITE_URL` and the gateway grant. | none (gitignored local file only) | very low; no security widening; restores the DR-003-verified configuration |
| **R2. Add `:3100` to the allow-lists** | Add `http://localhost:3100` to `backend/config.py ALLOWED_ORIGINS` **and** widen the gateway `map` in `tools/demo_lab/stack.py` (`BROWSER_ORIGIN`, or make it multi-origin), then regenerate the gateway config and re-create only the gateway container | `backend/config.py`, `tools/demo_lab/stack.py` (+ regenerated `~/ct_local_env/.../nginx.conf`) | medium — two product/lab files, requires the DR-003 generation + container-recreate procedure; must keep the explicit (no-wildcard) origin discipline |

R2 is a genuine PO/ops decision and is **already open** as DR-003 §21.3. R1 requires no
decision and no code change.

Two *separate* code observations (not required to fix this incident, listed for
triage — **not** implemented here):

- **B2 (low).** `Login.js` sets `authUnavailable='password'` but
  `AuthServiceUnavailable.detailByContext` has no `'password'` key, so an interrupted
  password sign-in shows the generic sentence instead of a password-specific one. Pure
  wording/UX; would be a one-line addition to `detailByContext`.
- **F2 (informational).** The release backend's repository default port (`8060` per
  `backend/.env`) differs from the Demo Lab's `8070` (DR-003 §6). The running backend is
  on `8070` and the frontend points at `8070`, so this is consistent today and is
  **not** part of this incident.

---

## 9. Recommended next action

1. **Immediate (R1, no code change):** stop the `:3100` dev server and start the
   frontend on the canonical origin `http://localhost:3000` (or set `PORT=3000` in
   `frontend/.env.local`), then re-run one Demo Lab sign-in in a browser and confirm the
   auth-unavailable notice does not appear.
2. **Then:** resume the CT-MP-SUB-004 browser acceptance on `:3000` — Admin/Operations
   "Commercial Coverage" tab, Consultant "Manual Processing" tab, and the customer
   `/manual-processing` route — capturing screenshots for the parent report.
3. **Decision request (not actioned here):** DR-003 §21.3 — whether to permanently align
   `frontend/.env.local PORT` with `ALLOWED_ORIGINS`, or to extend the gateway/backend
   allow-lists to include `:3100`. Until decided, R1 is the supported path.
4. Do **not** broaden CORS to a wildcard; the explicit single-origin discipline
   (DR-003 §5) is a deliberate security property.

---

## 10. Production statement

> **Production was not accessed, modified, migrated, seeded, reset or deployed.**
> This task touched only the local Demo Lab runtime and the local repository working
> tree. No production Supabase project, URL, database, storage bucket, email provider or
> hosting environment was contacted. No credential, token, signed URL or secret value is
> reproduced in this report. No commit, push, rebase or reset was performed (`HEAD`
> unchanged at `375a48dc1b9e9cfd74090bbf747554ae997acb59`). No application code,
> database schema, migration, RLS policy or stored data was changed. The only repository
> artefact created by this task is this report; the browser driver is a throwaway script
> under `/tmp` and is not part of the repository.

---

## 11. Limitations

- `LIMITATION` — the OAuth (Google) path was not exercised; only session-restore and
  password sign-in paths were driven. It would fail for the same origin reason.
- `LIMITATION` — no authenticated post-login surface was reachable, since auth is blocked
  at the origin boundary; therefore no CT-MP-SUB-004 screen was visually verified here.
  That is precisely the finding.
- `LIMITATION` — the Chrome build used (152.0.7977.64) is local to this machine; the CORS
  decision it reports is standard browser behaviour, not build-specific.
- `INFERENCE` — the message reported in the task matches the `'password'` context exactly;
  a session-restore failure would instead have shown the *"could not restore your existing
  session"* wording. The reproduction in §6.1 confirms this.

---

## 12. Final status

**READY FOR TARGETED FIX**

Diagnosis complete and evidenced end-to-end (`BROWSER-VERIFIED`). Root cause identified
with certainty: the locally running frontend is served on `http://localhost:3100`, while
the entire Demo Lab stack (gateway CORS `map`, `GOTRUE_SITE_URL`, backend
`ALLOWED_ORIGINS`) is aligned on `http://localhost:3000`; the browser therefore blocks the
sign-in call and the app reports "sign-in temporarily unavailable". The failure is an
environment/origin misalignment — **not** a broken auth service, broken credentials,
backend outage, stale frontend environment, or a CT-MP-SUB-004 defect. The remedy is
bounded and known: run the frontend on the canonical origin `:3000` (no code change),
with allow-list widening carried as the already-open DR-003 §21.3 decision.




