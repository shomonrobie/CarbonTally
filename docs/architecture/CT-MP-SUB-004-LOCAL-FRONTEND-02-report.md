# CT-MP-SUB-004-LOCAL-FRONTEND-02 — Frontend on the documented Demo Lab origin (`http://localhost:3000`)

| Field | Value |
| --- | --- |
| **TASK ID** | `CT-MP-SUB-004-LOCAL-FRONTEND-02` |
| **Predecessor** | `CT-MP-SUB-004-LOCAL-FRONTEND-01` (diagnosis; root cause proven) |
| **Related** | `CT-MP-SUB-004` (Manual Processing Commercial & Entitlement UI/UX — Implementation) |
| **Date** | 2026-10-04 |
| **Environment** | Local disposable Demo Lab only (frontend `:3000`, backend `:8070`, lab gateway `:54430`) |
| **Git SHA (unchanged)** | `375a48dc1b9e9cfd74090bbf747554ae997acb59` (`p8-release-reconciled`) |
| **Result** | Authenticated sign-in works, authenticated CarbonTally UI loads, all three CT-MP-SUB-004 surfaces reachable |
| **Final status** | **READY FOR MANUAL UI REVIEW** |

---

## 1. Task and scope

Run the existing CarbonTally frontend on the **documented Demo Lab frontend origin**
`http://localhost:3000` so that the CT-MP-SUB-004 UI can be manually exercised.

The predecessor task proved that the frontend was running on `:3100`, that the Demo Lab CORS
configuration, the GoTrue site URL and `backend/config.py ALLOWED_ORIGINS` all align on
`:3000`, and that authentication succeeds when `Origin: http://localhost:3000` and fails in
Chrome only because `:3100` receives no `Access-Control-Allow-Origin`. That was a **known,
documented environment mismatch, not a CT-MP-SUB-004 code defect**.

Accordingly this task changed **nothing**: it started the same frontend on the **already
documented and already-permitted origin**, then verified sign-in and the CT-MP-SUB-004
surfaces. The open Product Owner decision in
`docs/demo-investor/DR-003-demo-lab-cors-browser-verification.md` §21.3 (whether to add
`:3100` to the allow-list) was **not** implemented and remains open.

---

## 2. Frontend startup command / configuration used

### 2.1 Command

```bash
cd /home/shomonrobie/ct_93d5cdd/frontend
PORT=3000 BROWSER=none npx react-scripts start      # log: /tmp/fe3000.log
```

(`npm start` for this package is `react-scripts start`; the only difference here is the
`PORT` environment variable.)

### 2.2 Configuration — no file was edited

| Item | Value |
| --- | --- |
| Env file in use | `frontend/.env.local` (local, untracked; the only `frontend/.env*` file present) |
| `.env.local` md5 — before the task | `0ac65f142497e4d5cccbc9fc349d1078` |
| `.env.local` md5 — after the task | `0ac65f142497e4d5cccbc9fc349d1078`  (**identical**) |
| `REACT_APP_API_URL` | `http://localhost:8070` (lab backend, unchanged) |
| `REACT_APP_SUPABASE_URL` | `http://127.0.0.1:54430` (lab gateway: auth + rest, unchanged) |
| `PORT` line in the file | `3100` — **left as-is; not edited** |
| `BROWSER` line in the file | `none` — **left as-is** |

The documented origin was selected **by environment variable, not by editing a file**. CRA
loads its `.env*` files through `dotenv`, which never overwrites a variable already present in
the process environment; `PORT=3000` therefore wins over the `PORT=3100` line in
`.env.local` without touching any file. `BROWSER=none` was passed explicitly as well so no
GUI browser is spawned.

### 2.3 URL / port

| Item | Value |
| --- | --- |
| Served origin | `http://localhost:3000` |
| Bound socket | `LISTEN 0.0.0.0:3000  users:(("MainThread",pid=431504))` |
| Pre-existing `:3100` dev server | `pid 315566` — **left running, untouched** |

---

## 3. Compilation and load verification

| Check | Evidence | Result |
| --- | --- | --- |
| Frontend compiles | `/tmp/fe3000.log`: `Compiled successfully!` / `webpack compiled successfully` | **PASS** |
| Reported origin | `/tmp/fe3000.log`: `Local: http://localhost:3000` | **PASS** |
| `http://localhost:3000/` loads | `curl` → `HTTP 200` | **PASS** |
| CarbonTally shell served | `curl` → `<title>CarbonTally — Carbon Data Processing &amp; Emissions Management Platform</title>` | **PASS** |
| `http://localhost:3000/login` loads | `curl` → `HTTP 200` | **PASS** |
| Lab backend reachable | `LISTEN 127.0.0.1:8070` (`uvicorn pid 312590`) | **PASS** |
| Lab gateway reachable | `LISTEN 127.0.0.1:54430` | **PASS** |

---

## 4. Authentication result

Real UI sign-in was performed in a **dependency-free headless-Chrome CDP driver**
(`/tmp/cdp3.cjs`, Node 24 global `WebSocket`, one isolated browser context per persona).
The demo password is read from the local credentials file by the driver and is **never
printed**. The email and password were typed into the real login form and the real `Sign In`
control was clicked — **no session was seeded and no token was injected**.

| Persona | Demo actor | Identity / context resolved in the UI | Login | Landing route |
| --- | --- | --- | --- | --- |
| `customer` | `org_a_owner` | Customer Owner — *Demo Lab Organisation A* | **SUCCESS** | `/home` |
| `consultant` | `consultant_owner` | Consultant firm Owner — *Demo Lab Carbon Consultants · multi-client portal* | **SUCCESS** | `/consultant` |
| `admin` | `platform_admin` | Internal staff — *Internal Operations · admin* | **SUCCESS** | `/ops` |

Authenticated shell text captured **after** sign-in (business context confirmed, not UUIDs):

- **customer** — `… Documents Processing Manual processing Review & approve Emissions Reports Issues Billing Organisation Messaging Insight … Notifications  Demo Lab Organisation A  Sign out`
- **consultant** — `… Consultant workspace  Demo Lab Carbon Consultants · multi-client portal  CURRENT ORGANIZATION  Demo Lab Client A …`
- **admin** — `… Internal Operations Platform Demo · admin  Review Assignments QC Staff Roles Entities SLA Messaging PE messages Audit Settings **Commercial Coverage Manual Processing** Issues …`

| Authentication check | Result |
| --- | --- |
| `POST http://127.0.0.1:54430/auth/v1/token` (real password grant; preflight `204` + `200`) | **200 OK** for all three personas |
| Auth-unavailable banner (`[data-testid=auth-service-unavailable]`) **before** sign-in | `{shown:false}` |
| Auth-unavailable banner **after** sign-in | `{shown:false}` — **the reported blocker does not occur on `:3000`** |
| Redirect away from `/login` | Yes — `/home`, `/consultant`, `/ops` |
| Failed / blocked network requests during login | **NONE** |

---

## 5. CT-MP-SUB-004 surfaces reached

All three surfaces were opened with the existing Demo Lab identities that the surfaces
themselves require. Each read surface made a **real backend call through the browser** to the
CT-MP-SUB-004 endpoints and received `200 OK`.

### 5.1 Summary

| # | Surface | Persona | URL reached | Rendered? | Backend call from the browser |
| --- | --- | --- | --- | --- | --- |
| 1 | Customer — `Manual processing` (customer shell) | `org_a_owner` | `http://localhost:3000/manual-processing` | **YES** | `GET /api/v3/organizations/3fd0f325-16a1-5b53-8fb8-27929cf218fa/manual-processing` → **200** |
| 2 | Consultant — `Manual Processing` tab | `consultant_owner` | `http://localhost:3000/consultant?view=coverage` | **YES** | `GET /api/v3/consultants/me/manual-processing/coverage` → **200** |
| 3 | Platform Admin — `Commercial Coverage` tab | `platform_admin` | `http://localhost:3000/ops?tab=manual-processing-coverage` | **YES** | none on open — **operator-driven by design** (see §5.4) |

### 5.2 Customer surface — `/manual-processing`

Rendered page text (excerpt; `customer-2-manual_processing.png`):

> `Manual Processing` · `Manual Processing` **`NOT INCLUDED`** · *"Manual Processing is not
> included in your current commercial coverage. It is not currently available through your
> commercial coverage."*

| Marker | Present |
| --- | --- |
| `Manual Processing` (page `h1` + `Card` title) | **yes** |
| `What this means` (the commercial-vs-operational explainer `Card`) | **yes** |
| `Processing mode` (row only rendered when the organisation **is** entitled) | no — consistent with the `NOT INCLUDED` state |

The `NOT INCLUDED` wording is the **correct effective service state** for this demo
organisation given the Demo Lab's current coverage configuration; it is the response of the
live endpoint, not an error state. Because the state is "not entitled", the service-detail
table (which contains the `Processing mode` row) is deliberately not rendered.

### 5.3 Consultant surface — `/consultant?view=coverage`

Rendered page text (excerpt; `consultant-2-consultant_view_coverage.png`):

> `… Consultant dashboard  Client workspace  Clients  Manual Processing  Firm branding
> White-label  Team  Client messages` → **`Manual Processing Coverage` — "No consultant
> coverage active"**

| Marker | Present |
| --- | --- |
| `Manual Processing Coverage` (coverage `Card` title) | **yes** |
| `Manual Processing` (tab in the consultant tab set) | **yes** |

`No consultant coverage active` is the §7 empty state rendered from the live coverage
response for this demo firm.

### 5.4 Platform Admin surface — `/ops?tab=manual-processing-coverage`

The ops tab bar renders both CT-MP-SUB-004 entries — `Commercial Coverage` **and**
`Manual Processing` — immediately after `Settings`. With the `Commercial Coverage` tab
active the panel renders (`admin-2-ops_tab_manual_processing_coverage.png`):

> **`Commercial coverage`** — *"Who purchased what, and which clients are covered. This is
> deliberately separate from the operational routing view: buying coverage does not enable
> processing, and a configured Processing Entity does not create commercial entitlement."* —
> together with the `Consultant firm id` input and the `Load coverage` action.

| Marker | Present |
| --- | --- |
| `Commercial coverage` (panel heading) | **yes** |
| `Consultant coverage` (firm coverage `Card`, shown once a firm is loaded) | no — not yet loaded |
| `Effective Manual Processing entitlement` (`Card`, shown once a firm is loaded) | no — not yet loaded |

**This is the designed behaviour, not a gap.** The admin surface is an *operator* tool: the
operator enters a `consultant_profiles.id` and presses `Load coverage`, and only then are
`/api/v3/admin/manual-processing/coverage/{consultant_id}` and the effective-entitlement
panel populated. No endpoint is therefore called merely by opening the tab. Loading a firm
was deliberately **not** performed here, both because this task's instruction is to stop once
sign-in succeeds and because the deeper admin/consultant *write* paths (allocate/release)
would mutate Demo Lab data, which is out of scope for this verification.

> Note: the `Commercial Coverage` tab is gated client-side on the staff
> `can_manage_organizations` permission; the platform-admin demo identity satisfies it (the
> tab is visible and active). Server-side authorization is unchanged and remains the real
> boundary (AGENTS.md §44).

---

## 6. Evidence index

| Artefact | Location |
| --- | --- |
| Frontend dev-server log (`:3000`) | `/tmp/fe3000.log` |
| Full CDP run transcript (3 personas) | `/tmp/cdp02_out.txt` (13,728 bytes) |
| CDP driver (throwaway; not added to the repo) | `/tmp/cdp3.cjs` |
| Screenshots | `/tmp/cdp02_shots/` — `customer-1-after-login.png`, `customer-2-manual_processing.png`, `consultant-1-after-login.png`, `consultant-2-consultant_view_coverage.png`, `admin-1-after-login.png`, `admin-2-ops_tab_manual_processing_coverage.png` |
| Console errors captured per persona | in `/tmp/cdp02_out.txt` (section `[7]` of each persona) |

The CDP driver is a throwaway diagnostic harness; **no tooling was added to the repository**.

---

## 7. Remaining environment limitations

1. **Supabase Realtime is not proxied by the Demo Lab gateway (pre-existing).**
   Each persona logged a repeated browser console entry for
   `ws://127.0.0.1:54430/realtime/v1/websocket…` failing with
   `Error during WebSocket handshake: Unexpected response`. The lab gateway exposes
   `auth` + `rest`; Realtime is not routed. This is a **pre-existing Demo Lab environment
   condition, unrelated to CT-MP-SUB-004**, and was **not** fixed. It affected no
   application-layer request: `[6] failed/blocked requests` was `NONE` for every persona and
   every surface rendered from live HTTP data.
2. **Two frontend dev servers were listening when this report was written** — the new
   `:3000` instance and the pre-existing `:3100` instance (`pid 315566`). The `:3100`
   instance was intentionally left untouched (this task must not modify the environment
   beyond serving `:3000`). For a clean manual review, the stale `:3100` instance can simply
   be stopped; the `:3100` origin still fails to authenticate until the open DR-003 §21.3
   decision is resolved.
3. **DR-003 §21.3 PO decision remains open.** No `:3100` allow-list entry was added to
   `backend/config.py ALLOWED_ORIGINS` or to the gateway CORS map in
   `tools/demo_lab/stack.py`, and CORS was **not** broadened to a wildcard.
4. **Not exercised in this task (by instruction):** the admin firm "Load coverage" data load
   and the consultant allocate/release write paths. These require a
   `consultant_profiles.id` and would mutate Demo Lab data; they remain available for a
   follow-up manual review and do not affect this task's conclusion.

---

## 8. Change-control confirmation

| Constraint | Status |
| --- | --- |
| Modify application source code | **NOT DONE** — no file under `frontend/src/` (or anywhere in the repo) was edited by this task |
| Modify backend CORS | **NOT DONE** |
| Modify Demo Lab gateway CORS | **NOT DONE** |
| Add `:3100` to any allow-list | **NOT DONE** |
| Modify GoTrue configuration | **NOT DONE** |
| Modify database / schema / RLS / data | **NOT DONE** — the only database effect is the ordinary Supabase auth session record inherent to logging in, exactly as DR-003 already permits |
| Commit / push | **NOT DONE** — `HEAD` unchanged at `375a48dc1b9e9cfd74090bbf747554ae997acb59` |
| Access or modify production | **NOT DONE** |
| `frontend/.env.local` | md5 identical before and after (`0ac65f142497e4d5cccbc9fc349d1078`) |
| Working-tree entry count | `133` before the task → `134` after; the **only** added entry is this report file (`?? docs/architecture/CT-MP-SUB-004-LOCAL-FRONTEND-02-report.md`). No other repository content was added or removed |

**No source, database, configuration or production change was made by this task.**

---

## 9. Final status

> ## **READY FOR MANUAL UI REVIEW**

On the documented Demo Lab origin `http://localhost:3000` the frontend compiles and loads,
real UI sign-in succeeds with existing Demo Lab identities for the customer, consultant and
platform-admin personas (no auth-unavailable banner, no failed requests), the authenticated
CarbonTally UI loads for each, and all three CT-MP-SUB-004 surfaces open — with the customer
and consultant surfaces additionally issuing their real CT-MP-SUB-004 backend calls and
receiving `200 OK`.

This report verifies **reachability and rendering only**. It does **not** constitute an
independent acceptance verdict for CT-MP-SUB-004, and it asserts nothing beyond the evidence
recorded above (AGENTS.md §73/§74).

---

## 10. Reproduction

```bash
# 1. start the frontend on the documented Demo Lab origin (no file edited)
cd /home/shomonrobie/ct_93d5cdd/frontend
PORT=3000 BROWSER=none npx react-scripts start        # -> /tmp/fe3000.log

# 2. wait for "Compiled successfully!" and "Local: http://localhost:3000"
grep -E 'Compiled successfully|Local:' /tmp/fe3000.log

# 3. manual review
#    http://localhost:3000/login      -> sign in with an existing Demo Lab identity
#    customer    : http://localhost:3000/manual-processing
#    consultant  : http://localhost:3000/consultant?view=coverage
#    admin (staff): http://localhost:3000/ops?tab=manual-processing-coverage

# 4. optional automated re-run (throwaway driver; no repo tooling)
node /tmp/cdp3.cjs
```
