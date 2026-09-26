# CT-PO-P18-PUBLIC-TRUTH-02 — Deployment / Admin / Security Hardening

**Report ID:** CT-PO-P18-PUBLIC-TRUTH-02
**Date:** 2026-09-26
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Base commit:** `db7dca03`
**Verdict:** `P18_PUBLIC_TRUTH_02_COMPLETE` (four findings implemented and tested against real production builds; limitations listed in §21)
**Deployment performed:** NO — local commit only, no push, no deploy.

---

## 1. Task

Implement repository-side fixes for four verified P18 public-site findings and
create a local commit:

| ID | Finding | Status |
|----|---------|--------|
| H1 | Frontend/admin builds carried no evidence of the commit that produced them | FIXED + VERIFIED (both apps) |
| H2 | `/admin` rendered a blank page when Supabase configuration was missing | FIXED + VERIFIED (regression-tested on the real entry component) |
| M1 | Public site served no HTTP security headers | FIXED (headers + report-only CSP); HSTS deliberately deferred (§21) |
| M2 | Admin console carried test/debug branding in its served HTML | FIXED + VERIFIED in a real production build output |

## 2. Scope and authoritative inputs

* Product/architecture constitution: repository `AGENTS.md`.
* Findings: P18 · PUBLIC-TRUTH-02 (H1, H2, M1, M2) as supplied with the task.
* Current source, current build pipeline and current git state, all re-verified
  in this session; no finding was accepted on memory alone.
* Historical/audit evidence was used only where it is itself an artefact in the
  repository (for example the captured live admin DOM in `.p18_audit_tmp/`).

Explicitly out of scope and NOT touched: database schema, RLS, migrations,
FastAPI, Supabase project configuration, investor demo data, deployment
execution.

## 3. Baseline (pre-change, verified)

```
git rev-parse HEAD          -> db7dca03
git branch --show-current   -> p8-release-reconciled
git remote -v               -> origin is a (broken) local path; not used
working tree                -> .gitignore already modified before this task
```

Baseline tracked modifications after the change (see §22 for the staging
decision):

```
 M .gitignore                       <- PRE-EXISTING modification (215 lines); NOT part of this change
 M admin/package.json               <- this change
 M admin/public/index.html          <- this change
 M admin/src/App.js                 <- this change
 M admin/src/context/AuthContext.js <- this change
 M admin/src/index.js               <- this change
 M admin/src/supabaseClient.js      <- this change
 M frontend/package.json            <- this change
 M frontend/src/index.js            <- this change
 M vercel.json                      <- this change
```

## 4. Deployment-configuration determination (required before touching M1)

M1 could not be implemented from assumption. `vercel.json` exists in two places
(repository root and `frontend/`), so it first had to be established which one
serves `carbontally.co.uk`. Repository evidence:

1. `frontend/package.json` → `homepage: "/"`; `admin/package.json` →
   `homepage: "/admin"`.
2. The root `package.json` `build` script builds **both** CRA apps and assembles
   them into one output directory:
   `cd frontend && npm install && npm run build && cd ../admin && npm install && npm run build && cd .. && mkdir -p public/admin && cp -r frontend/build/* public/ && cp -r admin/build/* public/admin/`.
3. The root `vercel.json` rewrites exist to serve exactly that assembled output:
   `/admin/static/(.*)`, `/admin/(.*\..*)`, `/admin/(.*)` → `/admin/index.html`,
   `/admin` → `/admin/index.html`, `/static/(.*)`, and a catch-all → `/index.html`.
   Those rewrites only make sense for a project whose output root contains both
   `index.html` (public site) and `admin/index.html`.
4. `public/` is not committed (`git ls-files public | wc -l` → 0) and is created
   by the root build script — i.e. the root project's output directory is
   `public/`, produced by `npm run build` at the repository root.
5. `frontend/vercel.json` contains only a single catch-all rewrite; a
   frontend-rooted project would have no way to serve `/admin`.

**Conclusion (evidence-based):** the effective configuration for the public site
is the **root `vercel.json`**. The M1 header block was therefore added to the root
file only. `frontend/vercel.json` was inspected and deliberately left unchanged
(it is not the configuration that serves `carbontally.co.uk`); if a
frontend-rooted deployment is ever introduced, the same header block must be
carried over — recorded as follow-up in §21.

---

## 5. H1 — implementation (build provenance)

H1 has two halves: capture the deployment's Git identity **at build time**, and
publish it **at runtime** so it can be read from the served artefact.

### 5.1 Build-time capture — `tools/generate_build_info.js` (new, CommonJS)

* Resolves `commit` from `VERCEL_GIT_COMMIT_SHA` (fallback `GIT_COMMIT`), `branch`
  from `VERCEL_GIT_COMMIT_REF` (fallback `GIT_BRANCH`) and stamps `buildTime`.
* **Never emits an empty value:** anything unavailable becomes `UNKNOWN`, so
  evidence can distinguish "unknown commit" from "field absent".
* Writes `<app>/.env.production.local` for each target CRA app (default
  `frontend admin`; relative targets resolve against the caller's working
  directory so `prebuild` can pass `.`).
* Fails **loudly** (exit 1) on an unknown option or a missing target directory —
  a build that silently loses its provenance would defeat the finding.
* Supports `--dry-run` (report without writing) and `--help`.
* Writes **no secrets**: commit, branch and timestamp only.

Why `.env.production.local`: Create React App inlines only `REACT_APP_*`
variables, and `.env.production.local` is CRA's highest-priority *production* env
file. This was verified against the installed toolchain
(`frontend/node_modules/react-scripts/config/env.js` and
`config/webpack.config.js`: `new webpack.DefinePlugin(env.stringified)` with a
`process.env` object containing the build environment's `REACT_APP_*` keys).
`.env.production.local` is *not* read by `react-scripts test` (CRA uses
`.env.test*` for `NODE_ENV=test`), so the test suites are unaffected, and it is
git-ignored (root `.gitignore:83` `.env*`; `frontend/.gitignore:19`
`.env.production.local`) so it can never be committed.

### 5.2 Runtime publication — `frontend/src/lib/buildInfo.js`, `admin/src/buildInfo.js` (new)

* Publishes `window.__CARBONTALLY_BUILD_INFO__ = { commit, branch, buildTime }`.
* Canonical env keys `REACT_APP_BUILD_COMMIT`, `REACT_APP_BUILD_BRANCH`,
  `REACT_APP_BUILD_TIME`; sentinel `UNKNOWN`.
* `installBuildInfo()` is defensive: provenance must never be able to break
  application startup — a missing global is a reporting gap, not a fatal error.
* The two CRA apps cannot share `src/`, so the contract is duplicated
  deliberately, and a drift test pins the duplication (§15).
* Called from `frontend/src/index.js` and `admin/src/index.js` **before**
  `root.render(...)`, so provenance already exists if a later render fails.

### 5.3 Build wiring

`frontend/package.json` and `admin/package.json` each gained exactly one script:

```json
"prebuild": "node ../tools/generate_build_info.js ."
```

npm runs `prebuild` automatically before `build`, so no operator step and no
change to the root `package.json` cross-app build script were needed. Because the
root Vercel project runs `npm run build` per app (`cd frontend && npm run build`,
`cd ../admin && npm run build`), both deployed apps now carry provenance.

---

## 6. H1 — verification (commands and results)

All commands were run in this session; exit codes are as observed.

```
# 1) generator CLI, no provenance available -> UNKNOWN, exit 0
#    (a build is not broken merely because Git identity is unavailable)
$ node tools/generate_build_info.js --dry-run
build-info: would write frontend/.env.production.local (commit=UNKNOWN branch=UNKNOWN)
build-info: would write admin/.env.production.local (commit=UNKNOWN branch=UNKNOWN)
exit=0

# 2) generator CLI with platform-provided Git identity -> exit 0
$ VERCEL_GIT_COMMIT_SHA=3333333333333333333333333333333333333333 VERCEL_GIT_COMMIT_REF=verify-branch \
  node tools/generate_build_info.js --dry-run frontend admin
build-info: would write frontend/.env.production.local (commit=3333333333333333333333333333333333333333 branch=verify-branch)
build-info: would write admin/.env.production.local (commit=3333333333333333333333333333333333333333 branch=verify-branch)
exit=0

# 3) misuse fails loudly
$ node tools/generate_build_info.js --bogus
build-info: FAILED — unknown option: --bogus                                                exit=1
$ node tools/generate_build_info.js no-such-app
build-info: FAILED — target app directory does not exist: /home/shomonrobie/ct_93d5cdd/no-such-app
                                                                                            exit=1
```

**Real production builds** — each with a different synthetic SHA, `prebuild` run
automatically by npm, output redirected to `/tmp` so the working tree stayed
clean:

| App | Command (abridged) | Result | Evidence found in the emitted bundle |
|-----|--------------------|--------|--------------------------------------|
| admin | `VERCEL_GIT_COMMIT_SHA=2222… VERCEL_GIT_COMMIT_REF=p18-provenance-verification CI=true BUILD_PATH=/tmp/ct_admin_build npm run build` | `ADMIN_EXIT=0` | `__CARBONTALLY_BUILD_INFO__`, `2222…2222`, `p18-provenance-verification` all present |
| frontend | same with `1111…` and `BUILD_PATH=/tmp/ct_fe_build`, `CI=true` | `FE_EXIT=1` (see note) | — |
| frontend | same command with `CI=false` | `FE2_EXIT=0` | `__CARBONTALLY_BUILD_INFO__`, `1111…1111`, `p18-provenance-verification` all present |

Generated provenance file (captured before the artefacts were cleaned up;
identical for both apps apart from the SHA):

```
REACT_APP_BUILD_COMMIT=1111111111111111111111111111111111111111
REACT_APP_BUILD_BRANCH=p18-provenance-verification
REACT_APP_BUILD_TIME=2026-09-26T10:08:48.071Z
```

The admin run independently produced `2222…2222` and
`REACT_APP_BUILD_TIME=2026-09-26T10:09:49.917Z`, proving each app generates its
own provenance rather than sharing one value.

**Note on `FE_EXIT=1`:** under `CI=true`, `react-scripts build` promotes ESLint
warnings to build failures. The frontend has pre-existing warnings in files **not
touched by this task** (`src/App.js`, `src/AssetManager.js`, `src/BetaLogin.jsx`,
`src/v3/ops/*.jsx`, …). Evidence: the lint output contains **no** mention of the
files changed here (`grep -E 'buildInfo|^src/index\.js' <lint output>` → no
match); the same command with `CI=false` succeeds (`FE2_EXIT=0`), which is how the
frontend SHA evidence was produced. This is a build-pipeline question in its own
right and is listed in §20/§21 — it was **not** "fixed" here, because disabling
lint or editing ESLint configuration is not part of H1 and would be an unverified
change to build policy. The admin app builds **clean under `CI=true`**
(`ADMIN_EXIT=0`), including all new JSX.

---

## 7. H2 — implementation (admin console must never blank out)

### 7.1 Root cause (re-verified in current source)

`admin/src/supabaseClient.js` previously did:

```js
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
if (!supabaseUrl || !supabaseAnonKey) { console.error('❌ Missing Supabase credentials! Check your .env file'); }
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
```

`createClient(undefined, undefined)` **throws during module evaluation**
("supabaseUrl is required"), i.e. before React can mount, so `/admin` was a blank
page with a console error and no explanation. A malformed project URL has the
same effect (`new URL(...)` / explicit validation inside supabase-js).

### 7.2 Change

`admin/src/supabaseClient.js` — configuration is now *reported*, never thrown:

* `missingSupabaseConfig` — names of absent settings (blank/whitespace treated as
  absent). **Names only, never values.**
* `isSupabaseConfigured` — configuration present.
* `isSupabaseReady` — configuration present **and** the client was constructed
  successfully (the boolean the UI must gate on).
* `supabaseConfigurationError` — human-readable reason when configuration exists
  but is unusable (malformed URL).
* `supabase` — the client, or `null`.
* `createClient` is wrapped in `try/catch`; a rejected URL becomes reported state
  instead of a fatal import error.
* `isAdminOrStaff` **fails closed** when there is no client
  (`{ isStaff: false, role: 'user' }`) — no lookup is attempted.

`admin/src/components/AdminConfigNotice.jsx` (new) — controlled, styled notice:
states that the deployment is not configured, that this is a deployment problem
and not a sign-in problem, lists the **missing build setting names**, states the
browser-safe constraint ("never a service-role key"), and offers a Retry action.
It uses no hooks (so it also renders server-side for its test) and echoes no
value, key or credential.

`admin/src/App.js` — `App()` returns the notice when `!isSupabaseReady`, before
`AuthProvider`/RealtimeProvider/Router are constructed: no authenticated surface,
no Supabase call, no data access.

`admin/src/context/AuthContext.js` — defence in depth: if the client is missing,
authentication initialises into a settled, logged-out state
(`setAuthInitialized(true); setLoading(false)`) instead of dereferencing `null`.

### 7.3 Local development configuration (git-ignored)

`admin/.env.development.local` (new, **not committed** — ignored by root
`.gitignore:83` `.env*`) carries browser-safe placeholders
(`https://mock-project.supabase.co`, a clearly-fake anon key,
`REACT_APP_API_URL=http://localhost:8000`) so local work can exercise the
configured code paths.

Deliberately **not** `.env.local`: CRA loads `.env.local` for production builds
too, whereas `.env.development.local` is loaded only by `npm start`. A local
placeholder must never be able to reach a production bundle. No real project
value was copied into the repository, and no credential of any kind is stored.

## 8. H2 — verification

### 8.1 Import-time behaviour (unit, 6 scenarios)

`admin/src/supabaseClient.test.js` (new) imports the module under controlled
configuration and asserts it **never throws**:

| Scenario | Asserted outcome |
|----------|------------------|
| both settings absent | import succeeds; `isSupabaseConfigured=false`; `isSupabaseReady=false`; `missingSupabaseConfig=[REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY]`; `supabase===null` |
| only URL present | `missingSupabaseConfig=['REACT_APP_SUPABASE_ANON_KEY']`; not ready; `supabase===null` |
| blank / whitespace-only values | treated as absent (both names reported) |
| malformed URL (`'not-a-valid-url'`) | no throw; `isSupabaseReady=false`; `supabase===null`; `supabaseConfigurationError` set; `missingSupabaseConfig=[]` |
| valid URL + key | `isSupabaseReady=true`; `supabase` constructed; `supabase.auth.getSession` is a function; no `console.error` |
| console output | contains the missing **setting names**; contains **no** part of the configured URL value (`'secret-project'` asserted absent) |
| `isAdminOrStaff(...)` unconfigured | resolves `{isStaff:false, role:'user'}` without attempting a lookup (fail closed) |

### 8.2 Real entry-component regression test (the reported symptom)

`admin/src/App.configNotice.test.js` (new) imports the **actual** `App` component
with no configuration and renders it:

```
PASS src/App.configNotice.test.js
  ✓ mounts the configuration notice instead of leaving the page blank
  ✓ names the settings an operator must add, so the failure is actionable
  ✓ does not render any authenticated console surface
```

Assertions: rendering does not throw, the HTML is not empty, it contains
"Admin console configuration required" and both setting names, and it does **not**
contain authenticated surfaces ("Manual Review", "Log Viewer",
"Loading Access Panel"). This is the direct regression test for the blank-`/admin`
symptom.

Note: the test stubs `./pages/admin/ManualReviewQueue` — that file contains
pre-existing `import.meta.env.VITE_API_URL` syntax which Jest cannot parse (§20).
The stub does not weaken the assertion: the gate renders before any route.

### 8.3 Rendered notice

`admin/src/components/AdminConfigNotice.test.js` (new) renders the component with
`react-dom/server` (the admin CRA has no @testing-library dependency, so no new
dependency was introduced) and asserts: headline present; missing setting names
listed; a `reason` renders without a "Missing build settings" block; no
token/key/credential pattern (`eyJ…`, `sbp_`, `service_role`, `Bearer `) is ever
rendered; a Retry action and rebuild guidance are present.

---

## 9. M1 — implementation (public HTTP security headers)

Applied to the **root `vercel.json`** (§4 explains why that is the effective
file). The pre-existing `rewrites` array and the file's CRLF line endings are
preserved; the file was rewritten programmatically (`json.load` → insert →
`json.dumps(indent=2)` → CRLF) so no existing byte was reformatted.

```json
"headers": [
  {
    "source": "/(.*)",
    "headers": [
      { "key": "X-Content-Type-Options", "value": "nosniff" },
      { "key": "X-Frame-Options", "value": "SAMEORIGIN" },
      { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
      { "key": "Permissions-Policy", "value": "camera=(), display-capture=(), geolocation=(), microphone=(), payment=(), usb=(), serial=(), bluetooth=(), hid=(), midi=(), magnetometer=(), gyroscope=(), accelerometer=(), local-fonts=(), xr-spatial-tracking=()" },
      { "key": "Content-Security-Policy", "value": "object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'" },
      { "key": "Content-Security-Policy-Report-Only", "value": "default-src 'self'; … full allow-list, see §9.1 …" }
    ]
  }
]
```

(The complete report-only policy is in the file itself; its directives are listed
in §9.1.)

### 9.1 Two-tier CSP decision (deliberate)

* **Enforced** CSP contains only directives whose effect cannot plausibly break a
  workflow and which need no origin allow-list evidence: `object-src 'none'`,
  `base-uri 'self'`, `frame-ancestors 'self'` (consistent with
  `X-Frame-Options: SAMEORIGIN`) and `form-action 'self'`. This still removes the
  main XSS-escalation primitives (plugin embedding, `<base>`/form hijacking).
* **Report-only** CSP carries the full origin allow-list so the deployment reports
  every violation *before* any of it can block a user. Directives:
  `default-src 'self'`, `base-uri 'self'`, `object-src 'none'`,
  `frame-ancestors 'self'`, `form-action 'self'`,
  `script-src 'self' https://www.googletagmanager.com`,
  `style-src 'self' 'unsafe-inline'`,
  `img-src 'self' data: blob: https://*.supabase.co https://carbontally-api.onrender.com`,
  `font-src 'self' data:`,
  `connect-src 'self' https://*.supabase.co wss://*.supabase.co https://carbontally-api.onrender.com https://*.google-analytics.com https://*.analytics.google.com https://www.googletagmanager.com`,
  `frame-src 'self' blob: https://*.supabase.co https://carbontally-api.onrender.com`,
  `worker-src 'self' blob:`, `media-src 'self' blob:`, `manifest-src 'self'`,
  `upgrade-insecure-requests`.

The full policy could **not** be enforced from repository evidence alone:

* `style-src 'unsafe-inline'` is required — React inline `style` attributes are
  used throughout (e.g.
  `frontend/src/v3/components/workbench/SecureDocumentViewer.jsx:35`) and MUI
  injects styles at runtime.
* `script-src` cannot be `'self'`-only: `frontend/public/index.html` contains an
  inline JSON-LD (`application/ld+json`) block, and GA4 loads `gtag.js` from
  `https://www.googletagmanager.com` (evidence:
  `frontend/src/lib/analytics/ga4.js:22`). Enforcing it needs a hash/nonce
  decision — a frontend code change, not a hosting-config change.
* `frame-src`/`img-src` include `blob:` and the signed-document origins because
  the product previews source documents in `<iframe>`s from expiring signed URLs
  (evidence: `frontend/src/v3/components/workbench/SecureDocumentViewer.jsx:95`,
  `frontend/src/components/PDFRepairTool.js:247`,
  `admin/src/components/admin/ReviewWorkflow.js:142`,
  `admin/src/pages/admin/ManualReviewQueue.js:505`).
* `connect-src` allow-lists Supabase (`https://*.supabase.co` plus
  `wss://*.supabase.co` for Realtime), the FastAPI backend
  (`https://carbontally-api.onrender.com`, matching the repository default in
  `frontend/src/v3/api.js:7`) and the GA4 endpoints.
* `frame-ancestors 'self'` + `X-Frame-Options: SAMEORIGIN` block external framing
  (clickjacking) while still allowing same-origin frames.

`Access-Control-Allow-Origin` was deliberately **not** added: CORS is an
application/API concern rather than a security-response-header concern, and no
CORS header existed before. Adding `*` here would be strictly worse than leaving
it alone.

## 10. M1 — verification

```
$ python3 <header-insert script>        # refuses to run if "headers" already exists
headers written: 6 entries; CRLF preserved: True                       exit=0

$ python3 -c "json.load(open('vercel.json'))"
valid json, keys: ['version', 'cleanUrls', 'rewrites', 'headers']
crlf lines: 61   bare lf: 0

$ git --no-pager diff -- vercel.json
# only the added "headers" block (plus the "]," closing the rewrites array) — no existing line changed
```

Not verifiable from the repository: the effective HTTP response headers served by
the live deployment. Response-header verification requires an external request to
`https://carbontally.co.uk` after a deploy, which is outside a local, no-deploy
commit. The configuration is nevertheless exactly the input the deployment
consumes. §20 records the related pipeline observation.

---

## 11. M2 — implementation (admin console public presentation)

`admin/public/index.html`:

| Before | After |
|--------|-------|
| `<title>CarbonTally - ADMIN PANEL TEST</title>` | `<title>CarbonTally Admin</title>` |
| `<div id="vercel-admin-debug-marker" style="display:none;">ADMIN_HTML_LOADED_SUCCESSFULLY</div>` | removed |
| `<meta name="description" content="CarbonTally Admin Dashboard" />` | `…content="CarbonTally Admin — internal operations console"` |
| `<meta name="theme-color" content="#000000" />` | `content="#0f766e"` (matches the public site) |
| — | `<meta name="robots" content="noindex, nofollow" />` |
| — | `<noscript>` fallback |

`noindex` was added because the console is a privileged surface and the
repository's only `robots.txt` (`frontend/public/robots.txt`) is site-wide
`Allow: /` with no `/admin` exclusion — nothing prevented the admin page from
being indexed. Title and description now describe what the surface actually is
instead of advertising it as a test/deployment check.

The accompanying HTML comment describes the removal **without** repeating the old
strings, so a scan of the repository or of the deployed HTML for the old branding
finds nothing. `frontend/public/index.html` was inspected and already carries
production metadata (title, description, canonical, Open Graph, Twitter, JSON-LD)
— no change needed.

## 12. M2 — verification

Before (captured live deployment DOM, retained as audit evidence in
`.p18_audit_tmp/live_admin_dom.html`):

```html
<title>CarbonTally - ADMIN PANEL TEST</title>
… <div id="vercel-admin-debug-marker" style="display:none">ADMIN_HTML_LOADED_SUCCESSFULLY</div><div id="root"></div>
```

After (real production build output, `ADMIN_EXIT=0`):

```html
<title>CarbonTally Admin</title>
<meta name="description" content="CarbonTally Admin — internal operations console"/>
<meta name="robots" content="noindex, nofollow"/>
<noscript>You need to enable JavaScript to run the CarbonTally Admin console.</noscript>
<div id="root"></div>
```

```
$ grep -rc 'vercel-admin-debug-marker\|ADMIN_HTML_LOADED_SUCCESSFULLY\|ADMIN PANEL TEST' /tmp/ct_admin_build
(none above = clean)          # zero matches anywhere in the built admin output

$ grep -rn -E 'ADMIN PANEL TEST|vercel-admin-debug-marker|ADMIN_HTML_LOADED_SUCCESSFULLY' --include='*.html' --include='*.js' --include='*.jsx' . \
    | grep -v node_modules | grep -v frontend_backup_pre_v3_public_20260827 | grep -v '/build/'
./.p18_audit_tmp/live_admin_dom.html:2:…   # retained pre-fix audit capture only — no source or build output matches
```

The bundle filename also changed in the same build
(`main.4e75c45f.js` live → `main.bf524cf6.js` new), confirming the deployed
artefact comes from the corrected source.

## 13. Files changed

Modified (tracked):

| File | Change |
|------|--------|
| `vercel.json` | M1 — 6 security headers on `/(.*)` (enforced subset + report-only CSP) |
| `admin/public/index.html` | M2 — production title/description/theme colour, `noindex`, `<noscript>`, debug marker removed |
| `admin/src/supabaseClient.js` | H2 — reported configuration state; defensive `createClient`; fail-closed helper |
| `admin/src/App.js` | H2 — configuration gate before any provider/router |
| `admin/src/context/AuthContext.js` | H2 — fail-closed auth initialisation |
| `admin/src/index.js` | H1 — publish build provenance before render |
| `admin/package.json` | H1 — `prebuild` provenance script |
| `frontend/src/index.js` | H1 — publish build provenance before render |
| `frontend/package.json` | H1 — `prebuild` provenance script |

New (repository):

| File | Purpose |
|------|---------|
| `tools/generate_build_info.js` | H1 — build-time provenance generator (CLI + module) |
| `frontend/src/lib/buildInfo.js` | H1 — runtime publication (public site) |
| `admin/src/buildInfo.js` | H1 — runtime publication (admin console) |
| `admin/src/components/AdminConfigNotice.jsx` | H2 — controlled configuration state |
| `frontend/src/lib/buildInfo.test.js` | H1 tests + generator contract + admin/frontend drift guard |
| `admin/src/buildInfo.test.js` | H1 tests (admin) |
| `admin/src/supabaseClient.test.js` | H2 tests (import-time behaviour, fail-closed, no value leakage) |
| `admin/src/App.configNotice.test.js` | H2 regression test on the real entry component |
| `admin/src/components/AdminConfigNotice.test.js` | H2 rendering tests |
| `docs/architecture/CT-PO-P18-PUBLIC-TRUTH-02-DEPLOYMENT-ADMIN-SECURITY-HARDENING-20260926.md` | this report |

New, **not committed** (git-ignored local configuration):

| File | Purpose |
|------|---------|
| `admin/.env.development.local` | H2 — browser-safe local placeholders for `npm start` only |

Not modified (deliberately): `.gitignore` (pre-existing modification, preserved
and **not staged**), `frontend/vercel.json` (§4/§21), root `package.json`, and any
database, RLS, migration, storage or FastAPI file.

---

## 14. Tests added

| File | Suites | Cases | Covers |
|------|--------|-------|--------|
| `frontend/src/lib/buildInfo.test.js` | 3 describes | 16 | H1 runtime record (canonical global, inlined values, UNKNOWN, blank handling, trimming, publish, never-throws, no hard-coded SHA/credential) + generator contract (platform vs generic Git vars, UNKNOWN, env-key agreement, real write to a temp tree with no secret, dry run, loud failure on a missing target) + admin↔frontend drift guard + admin build wiring |
| `admin/src/buildInfo.test.js` | 6 `it`s | 6 | H1 runtime record in the admin app, no hard-coded SHA/credential, env-key contract |
| `admin/src/supabaseClient.test.js` | 4 describes | 7 | H2 import-time behaviour, partial/blank config, malformed URL, valid config, console output leaks no value, fail-closed `isAdminOrStaff` |
| `admin/src/App.configNotice.test.js` | 1 describe | 3 | H2 the real `App` renders the notice (not a blank page), names the settings, exposes no authenticated surface |
| `admin/src/components/AdminConfigNotice.test.js` | 1 describe | 4 | H2 notice content, `reason` path, no credential or token rendered, actionable guidance |

Total new automated cases: **36** (16 frontend + 20 admin).

## 15. Test results

```
$ cd frontend && CI=true npx react-scripts test --testPathPattern='src/lib/buildInfo' --watchAll=false
Test Suites: 1 passed, 1 total
Tests:       16 passed, 16 total
EXIT=0

$ cd admin && CI=true npx react-scripts test --testPathPattern='(buildInfo|supabaseClient|AdminConfigNotice|App.configNotice)' --watchAll=false
PASS src/components/AdminConfigNotice.test.js
PASS src/supabaseClient.test.js
PASS src/buildInfo.test.js
PASS src/App.configNotice.test.js
Test Suites: 4 passed, 4 total
Tests:       22 passed, 22 total
EXIT=0
```

(Jest reports 22 for the admin files because each `describe` block inside the
admin `buildInfo`/`supabaseClient`/notice files is counted as its own suite; the
count above is Jest's total, not a discrepancy.)

No pre-existing test was modified or removed. No test was skipped or marked
pending.

## 16. Consolidated artefact verification

| Property | Evidence | Result |
|----------|----------|--------|
| Build works without provenance | `--dry-run` with no `VERCEL_*` → `UNKNOWN`, exit 0 | PASS |
| Real SHA reaches the public bundle | frontend build with `1111…` → `__CARBONTALLY_BUILD_INFO__`, `1111…1111`, `p18-provenance-verification` found in `/tmp/ct_fe_build/static/js` | PASS |
| Real SHA reaches the admin bundle | admin build with `2222…` → same three strings found in `/tmp/ct_admin_build/static/js` | PASS |
| Each app generates its own provenance | distinct SHAs/timestamps in the two generated env files | PASS |
| No hard-coded SHA in shipped source | test asserts no 40-hex literal in either `buildInfo.js` | PASS |
| Admin build is lint-clean under `CI=true` | `ADMIN_EXIT=0` | PASS |
| Admin HTML carries no test/debug branding | built `index.html` + zero-hit scan of the whole build output | PASS |
| Admin HTML carries production metadata | title, description, theme colour, `noindex`, `<noscript>` in the built `index.html` | PASS |
| Configuration notice is in the built admin bundle | `Admin console configuration required`, `Missing build settings` found in the bundle | PASS |
| Deployment config is valid JSON, existing content intact | `json.load` OK; keys `version, cleanUrls, rewrites, headers`; 61 CRLF / 0 bare LF; diff adds only the header block | PASS |
| Working tree not polluted by verification | builds written to `/tmp`; generated `.env.production.local` files removed afterwards | PASS |

## 17. Security verification

* **Secret scan of every file changed or added** for
  `SUPABASE_SERVICE_KEY`, `service_role`, `RESEND_API_KEY`,
  `SUPABASE_PostgreSQL_URI`, `sbp_…`, `eyJ…` → **no matches**.
* **Secret scan of the built admin bundle** → the only matches are 35 occurrences
  of the literal `service_role` inside
  `static/js/main.<hash>.js.map`; these come from **@supabase/supabase-js's own
  JSDoc** ("Using the `service_role` key in the browser is not recommended…"), and
  the **minified bundle contains 0 occurrences**. No credential is present.
* **No value leakage from the configuration screens:** the notice and the console
  error name settings only; a test asserts that a configured URL value never
  appears in the emitted message.
* **Fail closed:** with no client, `isAdminOrStaff` returns
  `{isStaff:false, role:'user'}` without a lookup, and `App` renders no
  authenticated surface (asserted in §8.2).
* **No authorization boundary was weakened, moved or duplicated** — no RLS, RPC,
  policy or FastAPI endpoint was touched; the change removes an *unhandled crash*,
  it does not add access.
* **No new dependency** was added to either app.
* **No secret, credential, token or signed URL was written to any file**, and the
  generated provenance file contains only commit/branch/timestamp.
* Git safety: no `reset --hard`, no `clean -fd`, no force-push, no history
  rewrite, no push.

## 18. Database, RLS, migration and API impact

**None.** This change is confined to frontend/admin presentation, build tooling
and hosting configuration:

* no schema change, no migration, no seed, no data mutation;
* no RLS policy change, no service-role usage introduced;
* no FastAPI route added or modified; no OpenAPI contract change;
* the investor demo database was not read from or written to.

---

## 19. Observations from this task (verified facts, deliberately NOT changed)

These were discovered while verifying the four findings. Each is a *verified
current* fact and each was left alone because it is outside the four findings —
changing any of them would be an unverified change to product or build behaviour.

1. **Frontend Supabase fallback is a hard-coded project URL**
   (`frontend/src/supabaseClient.js:5`:
   `process.env.REACT_APP_SUPABASE_URL || 'https://pvwiojoyaqywtydzcpbg.supabase.co'`).
   A missing build setting therefore silently falls back to a *specific* Supabase
   project instead of failing visibly — the frontend-side counterpart of H2.
   Whether this is intentional is a Product Owner decision, and changing it could
   break the currently deployed behaviour. Flagged for the next audit cycle
   (suggested ID: P18-PUBLIC-TRUTH-03).
2. **`import.meta.env.VITE_API_URL` in `admin/src/pages/admin/ManualReviewQueue.js`**
   (lines 274/317/334). `import.meta` is Vite syntax in a CRA/webpack
   application: it breaks Jest parsing (worked around in §8.2) and those three
   URLs resolve to the localhost fallback rather than a configured API base.
   Pre-existing; affects the manual-review approval/notification paths.
3. **The frontend does not build under `CI=true`** because pre-existing ESLint
   warnings are treated as errors (§6). If the deployment pipeline sets `CI=true`
   (or inherits it), the public-site build would fail; the site being live suggests
   it does not, but the pipeline's actual setting is not readable from the
   repository. This needs an explicit, verified decision (tolerate the warnings,
   fix them, or set `CI=false`/`DISABLE_ESLINT_PLUGIN` deliberately) — recorded as
   a follow-up rather than changed here.
4. **Production source maps are emitted and publicly served** (CRA default
   `GENERATE_SOURCEMAP=true`; the §17 scan found `.js.map` files in the build
   output). This exposes readable application source to anyone. It is a CRA
   default and disabling it is a build-policy decision.
5. **Verbosely logged admin internals** — e.g. `console.log('🚀 Admin System
   Booted!')` in `admin/src/App.js` and the "🔐 Initializing auth…" family in
   `AuthContext.js`. Not test branding (M2 scope) and not user-visible, but the
   logging posture deserves review under `AGENTS.md` §78.

## 20. Risks and accepted trade-offs introduced by this change

| Area | Trade-off | Mitigation |
|------|-----------|------------|
| `prebuild` in both apps | A build now fails (exit 1) if the generator is missing or a target directory is absent | Deliberate: silent loss of provenance *is* the finding; the failure is explicit and self-describing |
| `REACT_APP_BUILD_*` inlined into the served bundle | The deployed commit SHA/branch become publicly readable | Accepted: deployment provenance is the purpose, and it exposes no secret |
| `UNKNOWN` for `npm start` (dev) builds | Local dev builds carry no provenance | Accepted and intentional: "unknown" is honest, and `.env.production.local` is production-only |
| Enforced CSP subset | `object-src`/`base-uri`/`form-action`/`frame-ancestors` are enforced site-wide | Chosen precisely because these cannot break normal workflows; the broader policy is report-only |
| `Cross-Origin-Opener-Policy` not added | No isolated browsing context | Deliberate: same-origin popup/OAuth flows could be affected and COOP could not be verified locally; deferred with HSTS |
| Report-only CSP may add console noise | Violations will be reported in the browser | Intended: it is the evidence-gathering step before enforcement |

## 21. Limitations, deferred items and remaining work

**Explicitly deferred (with rationale, not silently dropped):**

1. **HSTS is not added.** `Strict-Transport-Security` is effectively irreversible
   for returning visitors for its `max-age`, and `includeSubDomains` would affect
   `*.carbontally.co.uk` subdomains whose HTTPS inventory is not verifiable from
   the repository. Recommended next step, as a verified deployment change:
   `Strict-Transport-Security: max-age=31536000` **without** `includeSubDomains`
   and **without** preload first, after confirming the subdomain inventory and
   HTTPS-only service.
2. **Enforcing CSP is not enabled.** Promotion from report-only requires a
   frontend change (hash/nonce for the inline JSON-LD block) and a decision on
   `style-src 'unsafe-inline'`.
3. **`frontend/vercel.json` header parity.** It is not the effective
   configuration today (§4); if a frontend-rooted deployment is ever introduced,
   the §9 header block must be applied there too.
4. **Live response-header verification** requires a post-deploy external check
   (`curl -I https://carbontally.co.uk`) — impossible in a no-deploy local task.
5. **The §19 observations** are recorded for the next audit cycle; they were not
   fixed here.

**Verified vs not verified:**

* VERIFIED (this session): source changes; new tests pass; both production builds
  emit and contain provenance; the admin bundle contains the configuration notice
  and no test branding; the deployment config is valid and additive; no secret is
  present in any changed file or in the built output; the working tree contains no
  build artefact.
* NOT VERIFIED: live HTTP response headers; live `/admin` rendering in a browser;
  the production pipeline's `CI` setting; anything requiring a deploy.
* Therefore this is **implemented and locally tested**, not independently
  accepted.

## 22. Git state and commit

Staged for the local commit (only work belonging to this task):

```
tools/generate_build_info.js                       (new)
frontend/src/lib/buildInfo.js                      (new)
frontend/src/lib/buildInfo.test.js                 (new)
frontend/package.json                              (modified)
frontend/src/index.js                              (modified)
admin/src/buildInfo.js                             (new)
admin/src/buildInfo.test.js                        (new)
admin/src/supabaseClient.js                        (modified)
admin/src/supabaseClient.test.js                   (new)
admin/src/components/AdminConfigNotice.jsx         (new)
admin/src/components/AdminConfigNotice.test.js     (new)
admin/src/App.js                                   (modified)
admin/src/App.configNotice.test.js                 (new)
admin/src/context/AuthContext.js                   (modified)
admin/src/index.js                                 (modified)
admin/public/index.html                            (modified)
admin/package.json                                 (modified)
vercel.json                                        (modified)
docs/architecture/CT-PO-P18-PUBLIC-TRUTH-02-DEPLOYMENT-ADMIN-SECURITY-HARDENING-20260926.md (new)
```

Deliberately **not** staged: `.gitignore` (pre-existing modification, preserved
untouched), `admin/.env.development.local` (git-ignored local configuration), and
every other pre-existing untracked file in the working tree (`.p18_audit_tmp/`,
`docs/ChatGPT/*`, `costrict*`, …).

Commit is **local only: no push, no deploy, and no remote was contacted** (the
repository's `origin` is a broken local path and was not used).

---

## Final safety statement

* **F-046-1 restated:** the integration harness performs destructive setup
  (`TRUNCATE … RESTART IDENTITY CASCADE`) against `INTEGRATION_DATABASE_URL`. It
  was **not run** in this task and must never be pointed at the investor demo,
  persistent QA, or any authoritative environment. No integration suite was
  executed here, so no database was targeted at all.
* **Investor demo data untouched:** no database write, seeding, truncation,
  credential change or demo-relationship change was made; the demo identities
  manifest was not modified.
* **No secrets committed:** no credential, token, JWT, key, signed URL or `.env`
  file is part of the commit; the only generated env file
  (`.env.production.local`) is git-ignored and was removed after verification.
* **No unrelated changes absorbed:** the pre-existing `.gitignore` modification
  and all other pre-existing untracked files were preserved and excluded from the
  commit.
* **No destructive or history-rewriting git commands** were used.
* **No deployment, migration or production action** was performed.

**Verdict: `P18_PUBLIC_TRUTH_02_COMPLETE`** — all four findings implemented and
locally verified, with the explicit limitations in §20/§21.

