# DR-002 — Frontend Runtime Establishment + Browser-Verified Demo Journey

- **Prompt ID:** `DR-002`
- **Date/time:** 2026-09-20 (local), session ~19:5x–20:5x UTC
- **Branch:** `p8-release-reconciled`
- **Report status:** bounded verification; no product feature was implemented.

Evidence labels used below: `CODE-TRACED` · `RUNTIME-OBSERVED` · `BROWSER-VERIFIED` · `DATABASE-OBSERVED` · `INFERENCE` · `LIMITATION`.

---

## 1. Git baseline (Part A)

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD | `b166b4e51c0a971bb7adddc42a3ac5f270b8f59f` |
| Working tree | clean at start (`git status --porcelain` empty) |
| Remote `github` divergence | `0 0` (local == remote for the branch) |
| Prior baseline | `295495c9a590f081b3ed98e854ea84994c3ff747` |

No unexpected pre-existing changes were present; no commit was amended; no history rewritten; no force-push. `RUNTIME-OBSERVED`

---

## 2. Runtime architecture discovered (Part B)

`CODE-TRACED` unless noted:

- Frontend is a **Create React App** package (`carbontally-frontend@0.1.0`) run by `react-scripts start` (`frontend/package.json`).
- **No** `proxy` key in `frontend/package.json`; **no** `frontend/src/setupProxy.js`; no frontend nginx/compose/gateway in the repo for local running. The SPA therefore talks to the API **directly** (cross-origin → CORS applies).
- `frontend/.env.local` (untracked, ignored by `frontend/.gitignore:16`) contained:
  `REACT_APP_API_URL=http://localhost:8060`, `REACT_APP_SUPABASE_URL=http://127.0.0.1:19999`, `REACT_APP_SUPABASE_ANON_KEY=…`, `PORT=3100`, `BROWSER=none`, `WATCHPACK_POLLING`.
- **`8060` is not an arbitrary value — it is the repo's default backend port**: `backend/.env:4 PORT=8060` and `backend/.env:5 REACT_APP_API_URL=http://localhost:8060`. DR-001's "8060 vs 8070 mismatch" is therefore **not a frontend defect**; the **Demo Lab deliberately runs the backend on a different port** (`tools/demo_lab/lab.py:38 BACKEND_PORT = 8070`, gateway `GATEWAY_PORT = 54430`).
- Backend CORS: `backend/config.py:23-31 ALLOWED_ORIGINS` includes `http://localhost:3000` (comment: "✅ local V3 frontend (CRA dev server)"), `:3001`, `:3002`, plus production/Vercel origins — **`3100` (the port in `.env.local`) is not listed**.
- Frontend Supabase client: `frontend/src/supabaseClient.js:5-8` — `createClient(process.env.REACT_APP_SUPABASE_URL || 'https://<hosted-ref>.supabase.co', process.env.REACT_APP_SUPABASE_ANON_KEY || '<publishable fallback>')`.
- Auth/realtime are consumed **by the browser directly from the Supabase gateway** (GoTrue `/auth/v1/*`, Realtime `/realtime/v1/*`), not through a CarbonTally proxy. `RUNTIME-OBSERVED`

**Conclusion:** the intended local topology is *CRA dev server (origin `http://localhost:3000`) → FastAPI `:8070`*, with Supabase auth/realtime taken straight from the environment's Supabase gateway. No gateway/proxy is intended in between, which makes that gateway's own CORS policy load-bearing for browser auth.

---

## 3. Frontend startup procedure used (Part C)

```
cd frontend
PORT=3000 npm start          # BROWSER=none comes from .env.local
```

| Item | Value |
| --- | --- |
| Frontend command | `react-scripts start` (`npm start`) |
| Frontend URL | `http://localhost:3000` (HTTP 200) |
| Backend URL | `http://localhost:8070` (Demo Lab FastAPI) |
| API base inlined in bundle | `http://localhost:8070` (18 occurrences) |
| Supabase URL inlined in bundle | `http://127.0.0.1:54430` (2 occurrences) |
| Proxy | none (direct cross-origin) |
| Authentication mechanism | Supabase Auth (GoTrue) password grant from the SPA + Bearer JWT to FastAPI |
| CORS requirement | API: origin `http://localhost:3000` allowed. Auth: **required but not supplied by the lab gateway** |
| Startup errors | none fatal; `webpack compiled successfully` (ESLint warnings only: unused vars, exhaustive-deps, 2 a11y warnings) |
| Browser console errors | see §13 |

---

## 4. Configuration investigation and the minimal correction (Part D)

Three defects were found — **all in ignored/local configuration, none in product code**:

1. `frontend/.env.local` `REACT_APP_SUPABASE_URL=http://127.0.0.1:19999` — **nothing listens on 19999** (`ss -ltnp`); the Demo Lab gateway is `127.0.0.1:54430`. Consequence: browser auth fetch → `net::ERR_CONNECTION_REFUSED` (proved in the first browser run).
2. `REACT_APP_API_URL=http://localhost:8060` — consistent with `backend/.env`, but not with the running Demo Lab backend (`:8070`).
3. `.env.local` `PORT=3100` — **not** in `backend/config.py ALLOWED_ORIGINS` (3000/3001/3002 are).

**Minimal correction applied (frontend runtime environment only):**

| File | Change | Notes |
| --- | --- | --- |
| `frontend/.env.local` (**untracked / gitignored**) | `REACT_APP_API_URL` → `http://localhost:8070`; `REACT_APP_SUPABASE_URL` → `http://127.0.0.1:54430`; `REACT_APP_SUPABASE_ANON_KEY` → the **lab stack's** anon key (value deliberately not recorded) | Backup at `/tmp/env.local.dr002.bak`; `PORT`/`BROWSER` left as-is |

The dev server was then started with `PORT=3000` (an origin the backend already allows) instead of changing backend CORS. **No product source file and no backend file was modified.**

Verification of the correction `RUNTIME-OBSERVED`: served bundle contains `localhost:8070` ×18 and `127.0.0.1:54430` ×2, `127.0.0.1:19999` ×0 (previously ×2); `webpack compiled successfully`.

---

## 5. Backend connection details

- Demo Lab FastAPI: `http://localhost:8070` (healthy; live OpenAPI 575 paths / 683 operations).
- Demo Lab Supabase gateway: `http://127.0.0.1:54430` (nginx/Kong-fronted; auth + postgrest + storage + realtime containers running).
- Server-side (no CORS) auth check `RUNTIME-OBSERVED`: `POST /auth/v1/token?grant_type=password` → **HTTP 200**, `token_type=bearer`, `expires_in=3600`, `user.role=authenticated`.

---

## 6. Browser environment (Part F tooling)

| Item | Value |
| --- | --- |
| Browser | `/usr/bin/google-chrome`, headless `--headless=new`, 1440×900 |
| Pre-installed driver | **none** (no chromedriver / selenium / playwright / puppeteer) |
| Harness used | purpose-written **Node 22** script using the built-in global `WebSocket` + Chrome DevTools Protocol (`/tmp/dr002_browser.js`, `/tmp/dr002_browser2.js`). No new dependency, no repo file, no framework introduced |
| Evidence captured | rendered DOM text, per-route console/exception records, URL, nav, screenshots: `/tmp/dr002_shots/*.png` (12) and `/tmp/dr002_shots2/*.png` (8) |
| Screenshot retention | outside the repository (not committed) |

---

## 7. Authentication method used

Two distinct methods, deliberately separated:

1. **Real UI login** (`BROWSER-VERIFIED`, FAILED): the login form rendered (`input[type=email]`, `input[type=password]`, submit "Sign In"); the Demo Lab actor `org_a_owner`'s credentials were typed into the rendered form and submitted. Result: still on `/login`, `tokens: 0`, console:
   `Access to fetch at 'http://127.0.0.1:54430/auth/v1/token?grant_type=password' from origin 'http://localhost:3000' has been blocked by CORS policy: Response to preflight request doesn't pass access control check` → `AuthRetryableFetchError: Failed to fetch`.
2. **Lab-issued session seeding** (`BROWSER-VERIFIED`, used to exercise the rest of the app): a real session for the **same Demo Lab actor** was obtained server-side from the lab GoTrue (HTTP 200, §5) and written into the browser's `localStorage` under the app's Supabase storage keys; the app then rendered its **authenticated shell**. This is a harness technique to work around the gateway CORS gap; it uses genuine lab credentials and a genuine lab token. **No password and no token is recorded in this report.**

**Gateway CORS probe** (`RUNTIME-OBSERVED`, decisive): `OPTIONS http://127.0.0.1:54430/auth/v1/token` with `Origin:` set to `http://localhost:3000`, `127.0.0.1:3000`, `localhost:3100`, `127.0.0.1:3100`, `localhost:3001`, `localhost:8060` → **HTTP 204 with NO `Access-Control-Allow-Origin` header in every case**. The blocking condition is therefore independent of the frontend port: no local origin can authenticate through the lab gateway in a browser.

---

## 8. Browser-tested journey — what was actually observed

All items below are `BROWSER-VERIFIED` (real Chrome, real render, real JS execution) unless stated.

| # | Step | Observed result |
| --- | --- | --- |
| 1 | **Landing `/`** | Renders: title `CarbonTally — Carbon Data Processing & Emissions Management Platform`; H1 "Turn messy carbon data into traceable emissions."; nav `Platform · Services · Processing · Consultants · Pricing · About · FAQ`; CTAs "Pre-launch", "Sign in", "Request launch information"; interactive demo buttons `Source/Extract/Map/Calculate/Validate`; consent banner; Assistant launcher. 9,277 chars of rendered text. **0 console errors.** |
| 2 | **Route guard (unauthenticated `/home`)** | Automatically redirected to `/login` — the guard works. Login page renders "🌱 CarbonTally / Automated Carbon Accounting for UK Businesses", "Continue with Google", Email+Password, "Sign In", "Create Account". |
| 3 | **Login form** | Present and wired (`form`, 2 inputs, submit) — but submitting real Demo Lab credentials **fails at the network layer** (gateway CORS, §7.1). |
| 4 | **Authenticated shell** (after lab session seeding) | Renders with the seeded identity: top nav `Home · Documents · Processing · Review & approve · Emissions · Reports · Issues · Billing · Organisation · Messaging · Existing data · Notifications`, identity control "Demo Lab Organisation A", "Sign out". So auth-state handling, shell, routing and the sign-out affordance all work. |
| 5 | `/home`, `/documents`, `/processing`, `/review`, `/emissions`, `/organization` | Each renders the shell plus the app's error state: **"Something went wrong — No organization is linked to this account. Retry"** (458 chars). Root cause: user/organisation resolution fails because `GET http://127.0.0.1:54430/auth/v1/user` is **CORS-blocked** → `net::ERR_FAILED` → `TypeError: Failed to fetch`. Org-scoped data fetches are therefore never reached. |
| 6 | `/reports` | Renders past the error: "**Reports** — V3 reporting workspace…" (page-level UI renders; content not verifiable without org context). |
| 7 | `/billing` | Renders past the error: "**Billing** — Your commercial pl[an]…" (page-level UI renders; no subscription/payment action taken; no external provider contacted). |
| 8 | Realtime | `ws://127.0.0.1:54430/realtime/v1/websocket?apikey=…` fails from the browser (same gateway origin problem). |
| 9 | R-A calculating journey (document → extraction → correction → factor → calculation → 2,469.16978 kg CO₂e → `customer_review`) | **NOT reachable in the browser**: its pages sit behind the org-context error of row 5. Server-side state from prior verified work was left untouched; this pass could not display it. |
| 10 | Consultant/client, exports, approval | Not reachable for the same reason; no approval action was taken. |

---

## 9. Root cause of the browser blocker

`UI (/login submit) → supabase.auth.signInWithPassword → POST http://127.0.0.1:54430/auth/v1/token?grant_type=password → lab gateway preflight → 204 WITHOUT Access-Control-Allow-Origin → browser blocks → AuthRetryableFetchError → stays on /login`

and for authenticated pages:

`UI (/home) → app resolves user/org via supabase.auth.getUser() → GET http://127.0.0.1:54430/auth/v1/user → CORS blocked → OrgContext error "No organization is linked to this account." → all org-scoped pages show the error state`

Classification (Part G): **category 3 — backend/gateway configuration defect in the environment** (the lab Supabase gateway publishes no CORS allow-list for browser origins). It is *not* a frontend implementation defect, *not* a product-code defect, and not fixable by any frontend environment variable. A fix requires changing the **lab gateway configuration** (CORS allow-list) or serving SPA + auth API from one origin — both outside DR-002's authorised "minimal frontend configuration correction".

Secondary finding (Part G, category 1/8): `frontend/.env.local PORT=3100` is not among `backend/config.py ALLOWED_ORIGINS` (3000/3001/3002) — the repo's own local dev port and its backend CORS allow-list disagree. `CODE-TRACED`

---

## 10. Verification matrix (Part I)

| Journey | Code status | Browser status | Backend status | Actual result | Root cause if failed |
| --- | --- | --- | --- | --- | --- |
| Landing | Present | **VERIFIED** | n/a | Full marketing page renders; 0 console errors | — |
| Login | Present | **BROKEN (environment)** | Auth route works server-side (HTTP 200) | Form submits; request blocked by gateway CORS | Lab gateway CORS (§9) |
| Organization | Present | **BROKEN (environment)** | Token valid | "No organization is linked to this account." | `auth/v1/user` CORS-blocked |
| Dashboard (`/home`) | Present | **BLOCKED** | not reached | Shell + error state only | Org context |
| Documents | Present | **BLOCKED** | not reached | Shell + error state only | Org context |
| Upload | Implemented (code) | **NOT VERIFIED** | not attempted | Not reachable; no data change attempted | Org context |
| Processing | Present | **BLOCKED** | not reached | Shell + error state only | Org context |
| Extraction | Implemented (server; prior verified work) | **NOT VERIFIED** | working (prior R-A evidence) | Not displayable in browser | Org context |
| Manual correction | Implemented (server; prior verified work) | **NOT VERIFIED** | working (prior R-A evidence) | Not displayable in browser | Org context |
| Factor matching | Implemented (server; prior verified work) | **NOT VERIFIED** | working (prior R-A evidence) | Not displayable in browser | Org context |
| Calculation | Implemented (server; prior verified work) | **NOT VERIFIED** | working (prior R-A evidence) | Not displayable in browser | Org context |
| Emissions result | Implemented | **BLOCKED** | working (prior R-A evidence) | Shell + error state only | Org context |
| Provenance | Implemented | **NOT VERIFIED** | prior evidence | Not displayable | Org context |
| Manual review | Implemented | **BLOCKED** | prior evidence | Shell + error state only | Org context |
| Reports | Present | **PARTIALLY VERIFIED** | not reached | "Reports — V3 reporting workspace" renders; content needs org context | Org context |
| Export | Implemented (code) | **NOT VERIFIED** | no artefact confirmed | Not reached | Org context |
| Approval | Implemented (code) | **NOT YET AUTHORIZED** | state remains `customer_review` | No action taken | Task scope |
| Consultant | Implemented (code) | **BLOCKED** | not reached | Not reachable | Org/role resolution |
| Client | Implemented (code) | **BLOCKED** | not reached | Not reachable | Org/role resolution |
| Billing | Present | **PARTIALLY VERIFIED** | not exercised | "Billing — Your commercial pl[an]" renders; no plan/subscription interaction performed | Org context; payments out of scope |

---

## 11. Implemented but not verified in this pass (Part H category A)

Not evidence of breakage — simply not reachable this pass because of the org-context blocker:

- Document upload and the confirm/extraction-correction UI paths.
- Processing queue states (queued/extracting/mapping/validating) as displayed in the UI.
- The R-A calculating journey's on-screen chain (document → extraction → corrected supplier → matched factor → calculation snapshot → emissions result → provenance → `customer_review`).
- Blocked/exception displays (ambiguous factor, no-match, missing evidence, validation failure).
- Report artefact list/open/download; evidence-line-item and disclosure views.
- Customer approval action; consultant client-switching; PE/ops/internal workspaces.
- Messaging (Realtime failed from the browser for the same gateway-origin reason).

---

## 12. Genuinely missing capabilities (Part H category D)

**None proven missing in this pass.** No page/route was reached in a state where an expected control was demonstrably absent, so no "missing implementation" claim is made. DR-001's open question about upload/confirm/review UI wiring also remains **NOT VERIFIED** here (it was not reachable), i.e. still open, not resolved.

---

## 13. Console / network errors observed (verbatim, abridged)

1. (before correction) `Failed to load resource: net::ERR_CONNECTION_REFUSED` + `AuthRetryableFetchError: Failed to fetch` — auth URL `http://127.0.0.1:19999` (dead port).
2. (after correction, UI login) `Access to fetch at 'http://127.0.0.1:54430/auth/v1/token?grant_type=password' from origin 'http://localhost:3000' has been blocked by CORS policy: Response to preflight request doesn't pass access control check`.
3. (authenticated pages) `Access to fetch at 'http://127.0.0.1:54430/auth/v1/user' from origin 'http://localhost:3000' has been blocked by CORS policy` → `net::ERR_FAILED` → `TypeError: Failed to fetch` (≈9 console entries per page view).
4. (authenticated pages) `WebSocket connection to 'ws://127.0.0.1:54430/realtime/v1/websocket?apikey=…' failed`.
5. Landing page: **zero** console errors. `BROWSER-VERIFIED`

---

## 14. Demo Lab data used

- Actor: `org_a_owner` (existing Demo Lab identity from `~/ct_local_env/demo_lab/credentials.local.json`). No new identity.
- Read-only session grant against the lab GoTrue; read-only browser navigation of public and authenticated routes.
- R-A job `d868e0d7-d4be-4222-ba6b-f8c5c3f14134`, snapshot `af640887-…`, emissions `eb88e764-…`, result `2,469.16978 kg CO₂e`: **not touched, not re-run, not displayed** (pages blocked). A read-only API read of the job from the harness returned an empty body (`{}`) — recorded as INCONCLUSIVE, not as evidence of absence.

## 15. No-data / no-reset confirmation

- **No** Demo Lab reset, reseed, truncate or migration was performed.
- **No** document was created or uploaded; **no** job was enqueued or retried.
- **No** approval action was taken (R-A remains `customer_review`).
- The only non-GET request issued by the harness was the read-only auth token grant (server-side). Every browser write path was unreachable (org-context error state), so no mutation was possible even incidentally. `RUNTIME-OBSERVED`

---

## 16. Evidence references

- Browser runs: `/tmp/cdp_run.log` (pre-login, login, guard and unauthenticated captures), `/tmp/cdp2.log` (8 authenticated route captures + token grant), `/tmp/cdp_out.txt`, `/tmp/cdp2_out.txt`.
- Screenshots (not committed): `/tmp/dr002_shots/{s1_landing,s2_guard,s3_after_login,s4_home,s5_documents,s6_processing,s7_review,s8_emissions,s9_reports,s10_billing,s11_org,s12_consultant}.png` and `/tmp/dr002_shots2/{a1_home,a2_documents,a3_processing,a4_review,a5_emissions,a6_reports,a7_billing,a8_org}.png`.
- Rendered-DOM dump: `/tmp/dom_landing.html`; served-bundle config checks: `/tmp/bundle3.js`.
- Harness scripts: `/tmp/dr002_browser.js`, `/tmp/dr002_browser2.js`.

---

## 17. Exact files changed

| File | Status | Nature |
| --- | --- | --- |
| `docs/demo-investor/DR-002-frontend-runtime-browser-verification.md` | **new (committed)** | this report |
| `frontend/.env.local` | modified — **untracked & gitignored** (`frontend/.gitignore:16`), therefore **not** part of the repository diff | minimal frontend runtime configuration correction (§4); backup `/tmp/env.local.dr002.bak` |

No product source, backend, migration, RLS, storage, factor, calculation, matcher, extraction or OCR file was modified. Nothing outside the two rows above changed.

---

## 18. Tests / checks performed

- `git rev-parse --abbrev-ref HEAD`, `git rev-parse HEAD`, `git status --porcelain`, remote divergence — baseline.
- `npm start` (CRA): `webpack compiled successfully`; HTTP 200 on `/`.
- Served-bundle inspection for inlined `REACT_APP_*` values (before and after correction).
- `ss -ltnp` for listeners on 19999 / 3000 / 3100 / 54430.
- `curl -X OPTIONS` preflight matrix against the lab gateway for 6 origins.
- Server-side `POST /auth/v1/token?grant_type=password` (HTTP 200) — auth route health.
- CDP browser runs: 12 + 8 route captures with per-route console/exception capture and screenshots.

---

## 19. Remaining blockers

1. **Lab gateway CORS** blocks all browser auth (`/auth/v1/token`, `/auth/v1/user`) and Realtime for every local origin. This alone prevents any investor browser walkthrough of an authenticated journey today. Fix = lab gateway/environment configuration change (**not** authorised by DR-002).
2. **Org-context resolution** fails as a consequence of (1), so no org-scoped page can render data.
3. `frontend/.env.local PORT=3100` vs `ALLOWED_ORIGINS` (3000/3001/3002) inconsistency (latent; harmless only while the dev server is started on an allowed port).
4. No pre-installed browser driver in this environment (worked around with a purpose-written CDP harness requiring Node ≥ 21 for a global `WebSocket`).

---

## 20. PO decisions required

1. Authorise correcting the **Demo Lab gateway CORS** allow-list (or a same-origin serving arrangement) so browser login/realtime work — the single blocker to a browser-verified investor journey.
2. Authorise aligning `frontend/.env.local PORT` (3100) with `backend/config.py ALLOWED_ORIGINS`, or adding that port to the allow-list.
3. Whether the Demo Lab port defaults (`backend/.env` = 8060 vs the lab's 8070) should be documented, so future sessions don't chase the same false "mismatch" that DR-001 reported.
4. Whether to authorise bounded approval / report-artefact / export walkthroughs once (1) is fixed.
5. Whether DR-002's session-seeding harness technique is acceptable as a QA mechanism, or whether a driven-login-only rule should apply.

---

## 21. Investor demo question (Part J)

> "If an investor logs into the current CarbonTally Demo Lab today, what can they actually see and operate through the UI?"

**CAN DEMONSTRATE** (browser-verified today, no fixes needed): the public/landing experience — product positioning; platform/service/processing/consultant/pricing/about/FAQ navigation; the interactive Source→Extract→Map→Calculate→Validate demo strip; CTAs; the Assistant launcher; the consent banner; and the unauthenticated route guard (private routes redirect to a real login screen).

**IMPLEMENTED BUT NOT YET DEMONSTRATED**: the authenticated application shell (which does render with a valid session — nav, org identity label, sign-out) and everything behind it: dashboard, documents, upload/processing queue, extraction & correction views, factor matching, calculation & emissions results, provenance, review/manual-review states, reports, exports, approval, consultant/client workspaces, messaging, billing, and PE/ops/internal surfaces.

**CURRENTLY BROKEN**: browser login against the Demo Lab (gateway CORS), browser Realtime, and consequently organisation-context resolution — i.e. *any* authenticated data view.

**REQUIRES FUTURE AUTHORIZATION**: fixing the gateway CORS configuration; approval/report/export/billing walkthroughs; verification of upload/confirm UI wiring; any Demo Lab data or seed changes.

---

## 22. Final bounded verdict

The frontend runtime **is** establishable with the project's own mechanism (`npm start`, CRA) and, with the authorised three-line environment correction, the SPA correctly targets the Demo Lab backend and gateway. In a real browser, the landing experience, the route guard and the authenticated shell all render correctly. The authenticated **data** journey cannot be exercised today, and the failure is a **Demo Lab gateway CORS configuration gap** (proved by a preflight matrix over six origins and by two distinct browser console errors), not a frontend implementation defect and not a missing feature. Server-side product capability from earlier verified work is unchanged and untouched. This report asserts nothing beyond the evidence above and does **not** declare CarbonTally investor-ready.
