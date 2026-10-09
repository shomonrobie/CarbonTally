# P18-02 PUBLICATION TO PRODUCTION — FINAL VERIFICATION REPORT

**Document ID:** CT-PO-P18-PUBLIC-TRUTH-04-20260926-PUBLISH-VERIFICATION-FINAL
**Task ID:** P18-PUBLIC-TRUTH-04-20260926-PUBLISH-CARBONTALLY-P18-02-VERIFIED-BUILD-RETRY
**Date:** 2026-09-26
**Environment:** operator workstation `/home/shomonrobie/ct_93d5cdd`; read-only live probes of
`https://carbontally.co.uk`, `https://carbontally-api.onrender.com`, the GitHub API and the GitHub
Deployments API
**Operating mode:** publication/deployment task. **No application code was modified. No database
schema, data, RLS or migration was touched.**
**Supersedes:** `CT-PO-P18-PUBLIC-TRUTH-04-20260926-PUBLISH-VERIFICATION.md` (the earlier run of this
task, which terminated as BLOCKED because no compliant deployment trigger existed while Render
Auto-Deploy was enabled).
**Operator precondition applied:** the operator disabled Render Auto-Deploy for the production backend
before this run. That setting is operator-controlled and was not modified.

---

## 0. TRUTH STANDARD USED IN THIS REPORT

The following states are kept distinct throughout:

DOCUMENTED ≠ CODE EXISTS ≠ ROUTE WIRED ≠ AVAILABLE ≠ DEPLOYED ≠ LIVE ≠ LIVE VERIFIED ≠
INDEPENDENTLY VERIFIED ≠ PRODUCTION READY

Every claim below carries the evidence that establishes it. Where an item could only be established
from the *committed configuration* rather than from a live observation, that is stated. Where a live
observation is used, the exact observed value is quoted.

**What this report establishes:** the exact commit `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` is
published to the authoritative branch; a Vercel **Production** deployment exists for that exact SHA;
and the live public artifact identifies that exact commit and satisfies the P18-02 live checks.

**What this report does NOT establish:** release of P17 backend functionality, and release of the six
P17 migrations. Those remain a separate, PO-authorised gate (§I, §J).

## A. GIT PRE-FLIGHT

| # | Check | Required | Observed | Result |
|---|---|---|---|---|
| 1 | Repository | `/home/shomonrobie/ct_93d5cdd` | `/home/shomonrobie/ct_93d5cdd` | PASS |
| 2 | Current branch | `p8-release-reconciled` | `p8-release-reconciled` | PASS |
| 3 | `HEAD` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | PASS |
| 4 | `HEAD^` (parent) | `db7dca03…` | `db7dca03e230a1de4e9628b8e855e4135c76512f` | PASS |
| 5 | Commit identity | the verified P18-02 commit | see §A.1 | PASS |
| 6 | Authoritative remote fetched | `github` = `https://github.com/shomonrobie/CarbonTally.git` | fetched, exit 0 | PASS |
| 7 | Remote branch pre-push | `98a89d0c1ab0e850d4ca44e348a66da0515dc691` | `98a89d0c1ab0e850d4ca44e348a66da0515dc691` | PASS |
| 8 | Pure fast-forward descendant | yes | proven by ancestry (§A.3) | PASS |
| 9 | No unexpected *committed* modification | yes | no committed changes beyond `cb70fd6` | PASS (see §A.5) |
| 10 | Push publishes only history ending at `cb70fd6` | yes | bare-SHA refspec, no `+`, no `--force` | PASS |

### A.1 Local identity of the published commit (verified, not assumed)

```
commit cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea
Author:     shomonrobie <shomonrobie@gmail.com>
AuthorDate: Sat Sep 26 16:19:11 2026 +0600     (= 2026-09-26T10:19:11Z)
Commit:     shomonrobie <shomonrobie@gmail.com>
CommitDate: Sat Sep 26 16:19:11 2026 +0600     (= 2026-09-26T10:19:11Z)

    fix(public-truth): build provenance, admin config gate, security headers, admin branding

    P18 PUBLIC-TRUTH-02 (H1, H2, M1, M2). Local commit only - no push, no deploy.
```

GitHub API cross-check of the same object (`/repos/shomonrobie/CarbonTally/commits/cb70fd6…`):

```
sha     = cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea
date    = 2026-09-26T10:19:11Z
subject = fix(public-truth): build provenance, admin config gate, security headers, admin branding
parents = db7dca03e230a1de4e9628b8e855e4135c76512f
```

Same SHA, same author date, same parent ⇒ the remote holds the **existing** commit object. A new or
amended commit would necessarily have a different SHA, so this is proof that no replacement commit was
created.

### A.2 Remotes — the authoritative remote is `github`, not `origin`

```
github  https://github.com/shomonrobie/CarbonTally.git   (fetch and push)
origin  /tmp/ct_step2                                    (fetch and push)  ← local scratch remote
```

`origin` is a **local scratch path**, not production. It is why `git status --branch` reports "ahead
of 'origin/p8-release-reconciled' by 204 commits". That counter is meaningless for this publication
and was ignored. Every remote-state assertion in this report was taken from `github` — via
`git ls-remote github` **and** the GitHub API, which agree.

Remote `main` was also recorded pre-push and post-run: `2f56562ad797c5c2f1b73da7380e45199584e016`
(unchanged — this task pushes only `p8-release-reconciled`).

### A.3 Fast-forward / ancestry proof (established by ancestry, not by commit names)

```
git merge-base --is-ancestor 98a89d0… cb70fd6…   → ANCESTOR_YES
git merge-base                 98a89d0… cb70fd6…   → 98a89d0c1ab0e850d4ca44e348a66da0515dc691
git rev-list --count 98a89d0…..cb70fd6…            → 64   (commits to publish)
git rev-list --count cb70fd6…..98a89d0…            →  0   (nothing on the remote absent locally)
```

The merge base **equals the remote head**, and there are **zero** commits on the remote side that are
absent locally. The update is therefore a pure fast-forward, with no divergence and no rewrite.

Publication range: **64 commits**, **131 changed paths** — 68 `backend`, 30 `docs`, 12 `frontend`,
12 `admin`, 6 `supabase`, 1 `vercel.json`, 1 `tools`, 1 `src`. This range is the *existing* verified
history ending at `cb70fd6`; it is exactly what the task authorised publishing.

### A.4 Dry-run confirmation (performed before any state change)

```
$ git push --dry-run github cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea:refs/heads/p8-release-reconciled
To https://github.com/shomonrobie/CarbonTally.git
   98a89d0..cb70fd6  cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea -> p8-release-reconciled
```

The `..` (not `..+`), and the absence of any forced-update marker, confirm a non-forced
fast-forward. The dry run also confirmed credential availability, so the real push could not fail on
authentication.

**Note on `--ff-only`:** the task's conceptual command used `git push --ff-only`. The Git installed
here does **not** implement `--ff-only` for `push` (`error: unknown option 'ff-only'`). The
fast-forward-only property was therefore established *positively* by three independent means rather
than by that flag:

1. the ancestry proof in §A.3 (merge base = remote head; 0 commits on the remote side);
2. a refspec containing a bare SHA with no `+` prefix, and no `--force` / `--force-with-lease`;
3. the dry-run output above showing a non-forced `98a89d0..cb70fd6` update.

### A.5 Working-tree state at pre-flight (what a push can and cannot transfer)

Tracked modifications present **before** the push (pre-existing; unchanged by this task):

```
 M .gitignore
```

`git diff --stat -- .gitignore` → 108 insertions / 107 deletions.
`git diff --stat -w -- .gitignore` → **1 insertion**.
The diff is whitespace/line-ending churn plus one added ignore line.

A push transfers **commits**, not the working tree. `cb70fd6`'s tree is immutable and was not
modified, so neither this uncommitted `.gitignore` change nor any untracked file (including this
report) can be published by the push. No `git add`, `git commit`, `git stash` or `git checkout` was
executed at any point in this task.

The untracked-file list contains no secret-like paths introduced by this task; the only file this task
created is this report (untracked, therefore unpublished).

## B. PUBLICATION

**Executed command (exactly):**

```
git push github cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea:refs/heads/p8-release-reconciled
```

| Item | Value |
|---|---|
| Exact pushed SHA | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| Resulting remote branch SHA | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| Remote | `github` → `https://github.com/shomonrobie/CarbonTally.git` |
| Branch | `p8-release-reconciled` |
| New commit created | **NO** (pushed SHA is byte-identical to the pre-existing local SHA; same parent `db7dca03…`; same author date `2026-09-26T10:19:11Z`) |
| Force push | **NO** — no `--force`, no `--force-with-lease`, no `+` in the refspec |
| Rebase / reset / cherry-pick / amend | **NO** — none was executed |
| Local `HEAD` after push | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` (unchanged) |
| Local branch after push | `p8-release-reconciled` (unchanged) |
| Remote `main` after push | `2f56562ad797c5c2f1b73da7380e45199584e016` (unchanged) |

**Post-push re-fetch (independent confirmation):**

```
$ git fetch github
From https://github.com/shomonrobie/CarbonTally
   98a89d0..cb70fd6  p8-release-reconciled -> github/p8-release-reconciled

$ git rev-parse github/p8-release-reconciled
cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea
```

The fetch reports `98a89d0..cb70fd6` — a non-forced fast-forward, with no `+` marker — confirming that
the remote accepted the update as a descendant of its previous head.

**Independent GitHub API confirmation of the resulting branch head:**

```
$ gh api repos/shomonrobie/CarbonTally/branches/p8-release-reconciled --jq '.commit.sha'
cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea

$ gh api repos/shomonrobie/CarbonTally/branches/p8-release-reconciled --jq '.commit.commit.message'
fix(public-truth): build provenance, admin config gate, security headers, admin branding
```

Two independent mechanisms (local remote-tracking ref after fetch, and the GitHub REST API) agree on
the branch head, and `git ls-remote github p8-release-reconciled` agrees as well.

**Working tree after publication (tracked files only):**

```
 M .gitignore
```

Unchanged from pre-flight. This task introduced **no tracked change** — the only file it wrote
anywhere is this report, and it is untracked.

## C. VERCEL PRODUCTION DEPLOYMENT

The frontend is Git-connected to Vercel. Vercel detected the push and created the Production
deployment itself; **no manual deployment mechanism was used**, which is what preserves provenance.

| Item | Observed value |
|---|---|
| Deployment ID | `6679336317` |
| Deployment SHA (`sha` field) | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| Deployment `ref` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| Environment | `Production` |
| Creator | `vercel[bot]` (Git integration — not a human/CLI deployment) |
| Created at | `2026-09-26T13:20:22Z` |
| Deployment status | `success` at `2026-09-26T13:20:23Z` |
| Deployment URL | `https://carbon-tally-1l8sht7f3-shomonrobies-projects.vercel.app` |
| Commit status on `cb70fd6` | `Vercel=success` (state: `success`) |
| Check run on `cb70fd6` | `Vercel Preview Comments` — completed / success, `2026-09-26T13:20:22Z` |
| Previous Production deployment (for comparison) | `6656505133`, `2026-09-25T08:10:25Z`, sha `98a89d0c1` |

**The deployed SHA is the exact expected 40-character SHA**, not a short SHA, not an approximate SHA
and not a previous deployment's SHA. The `Vercel` commit status is `success`, so the deployment did
not fail and no code was changed to make it pass.

**Live cache observation:** immediately after deployment the origin returned
`x-vercel-cache: MISS`, `age: 0` and `last-modified: Sat, 26 Sep 2026 13:20:56 GMT`, i.e. the edge
switched from the previous artifact (`last-modified: Sat, 26 Sep 2026 08:06:04 GMT` observed
pre-push, `x-vercel-cache: HIT`, `age: 18764`) to the newly built one within the same minute as the
deployment transition.

**Pre-push vs post-push live baseline (proves the artifact actually changed):**

| Probe | Pre-push (13:0x) | Post-deploy (~19:22 local / 13:22Z) |
|---|---|---|
| `last-modified` on `/` | `Sat, 26 Sep 2026 08:06:04 GMT` | `Sat, 26 Sep 2026 13:20:56 GMT` |
| P18 security headers present | **0** of 6 matched | **6** of 6 matched |
| `__CARBONTALLY_BUILD_INFO__` marker in the emitted frontend bundle | absent from the served bundle | present, and pins `cb70fd6…` |
| `/admin` `<title>` | `CarbonTally - ADMIN PANEL TEST` (documented pre-P18-02 state) | `CarbonTally Admin` |

**Vercel credential availability (recorded for transparency):** no Vercel CLI and no `VERCEL_*` /
`RENDER_*` credentials are available in this environment, and none were needed or used — the
deployment was produced by the **Git integration**, which is the only mechanism that can satisfy the
provenance requirement. No CLI upload, no dashboard upload and no directory deployment was performed.

## D. LIVE-A — LIVE BUILD PROVENANCE

**Question asked:** does the live artifact explicitly identify the exact expected commit?

**Answer: YES — PASS.**

The live frontend document `https://carbontally.co.uk/` loads
`/static/js/main.5f9a4b10.js` (2,343,096 bytes). The **served** bundle contains exactly:

```
REACT_APP_BUILD_COMMIT:"cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea"
REACT_APP_BUILD_BRANCH:"p8-release-reconciled"
REACT_APP_BUILD_TIME:"2026-09-26T13:19:13.719Z"
```

Occurrence counts in the served bundle:

| String | Occurrences in served bundle |
|---|---|
| `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | 1 |
| `p8-release-reconciled` | 1 |
| `__CARBONTALLY_BUILD_INFO__` | 1 |

The publishing call is present and, critically, it executes **before** the application renders — the
de-minified region of the served bundle reads:

```js
...branch:gK(e.REACT_APP_BUILD_BRANCH||e.branch)||vK, buildTime:gK(e.REACT_APP_BUILD_TIME||e.buildTime)||vK})}(),
   n = e || ("undefined"!==typeof window ? window : null);
return n && (n.__CARBONTALLY_BUILD_INFO__ = t), t;
...
yK();
a.createRoot(document.getElementById("root")).render( ... );
```

So `window.__CARBONTALLY_BUILD_INFO__ = {commit, branch, buildTime}` is set by the build-provenance
module, which is invoked (`yK()`) immediately before `createRoot(...).render(...)`.

The **admin** application is separately pinned to the same commit. The live admin document loads
`/admin/static/js/main.c9f8b964.js` (1,477,698 bytes), which contains:

```
REACT_APP_BUILD_COMMIT:"cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea"
REACT_APP_BUILD_BRANCH:"p8-release-reconciled"
REACT_APP_BUILD_TIME:"2026-09-26T13:19:57.361Z"
```

with 1 occurrence of the exact SHA, 1 of the branch, and 1 of the provenance marker.

### D.1 Exactness — what was and was not accepted

Accepted: the **full 40-character** SHA `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea`, emitted into the
served public bundle of the live site, with branch `p8-release-reconciled`.

Not accepted and not relied upon: a short SHA, an approximate SHA, the previous deployment's SHA, the
source-repository HEAD, or an inferred deployment identity. The distractor case is real in this task —
the previous Production deployment was `98a89d0c1…` — and it was excluded by requiring the full SHA
literal to appear in the live bundle.

### D.2 Method note (so the check is reproducible and not mis-read)

`__CARBONTALLY_BUILD_INFO__` is published by JavaScript at runtime; it is **not** an inline marker in
the served HTML. Grepping the served HTML for the marker therefore returns 0 **by design** and proves
nothing on its own. The check was performed against the **served JavaScript bundle** that the live
`/` document actually references, plus the de-minified publish-before-render region quoted above.
This is the correct observable for this requirement.

### D.3 Result

| Field | Required | Observed live (public frontend) | Observed live (admin) | Result |
|---|---|---|---|---|
| Commit | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` | PASS |
| Branch | `p8-release-reconciled` | `p8-release-reconciled` | `p8-release-reconciled` | PASS |
| Build time | present (not `UNKNOWN`) | `2026-09-26T13:19:13.719Z` | `2026-09-26T13:19:57.361Z` | PASS |
| Published before render | yes | yes (`yK()` precedes `createRoot(...).render(...)`) | yes | PASS |

**LIVE-A: PASS.**

## E. LIVE-B — ADMIN PUBLIC ARTIFACT CHECK

Live check against `https://carbontally.co.uk/admin` (HTTP 200).

| # | Requirement | Observed live | Result |
|---|---|---|---|
| 1 | Page **renders** rather than showing a blank `#root` | Headless-Chrome rendered DOM shows `#root` populated (see §E.1) | PASS |
| 2 | No `supabaseUrl is required` initialization failure | No such error at load; the config gate short-circuits before `createClient` (see §E.2) | PASS |
| 3 | Title/branding is `CarbonTally Admin` | `<title>CarbonTally Admin</title>` | PASS |
| 4 | Old test branding absent | `CarbonTally - ADMIN PANEL TEST` → **0 occurrences** | PASS |
| 5 | Old debug marker absent | `vercel-admin-debug-marker` / `ADMIN_HTML_LOADED_SUCCESSFULLY` → **0 occurrences** | PASS |
| 6 | Production robots metadata appropriate | `<meta name="robots" content="noindex, nofollow"/>` | PASS |
| 7 | No privileged Supabase service-role key in the browser bundle | `service_role` → 0; `SERVICE_ROLE` → 0; `serviceRoleKey` → 0; no JWT-like key material in the admin bundle | PASS |

**LIVE-B: PASS.**

### E.1 Non-blank rendering — rendered DOM evidence

The served admin HTML (656 bytes) contains the expected production head and an empty `#root`:

```html
<!doctype html><html lang="en"><head><meta charset="utf-8"/>
<link rel="icon" href="/admin/favicon.ico"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="theme-color" content="#0f766e"/>
<meta name="description" content="CarbonTally Admin — internal operations console"/>
<meta name="robots" content="noindex, nofollow"/>
<title>CarbonTally Admin</title>
<script defer="defer" src="/admin/static/js/main.c9f8b964.js"></script>
<link href="/admin/static/css/main.f8d6f91f.css" rel="stylesheet"></head>
<body><noscript>You need to enable JavaScript to run the CarbonTally Admin console.</noscript>
<div id="root"></div></body></html>
```

Because a blank shell proves nothing about rendering, the page was executed in a real browser
(`google-chrome --headless --virtual-time-budget=15000 --dump-dom`) and the **post-execution DOM** was
inspected. `#root` is **populated**:

```html
<div id="root"><div class="min-h-screen flex items-center justify-center bg-gray-50 p-6">
  <div class="w-full max-w-xl rounded-lg border border-gray-200 bg-white p-8 shadow-sm">
    <h1 class="text-xl font-semibold text-gray-900">Admin console configuration required</h1>
    <p class="mt-3 text-sm leading-6 text-gray-600">This deployment of the CarbonTally Admin console
    was built without its Supabase connection settings, so it cannot start yet. ...</p>
```

The old debug marker is absent from the rendered DOM as well (`0` occurrences), and the rendered DOM
contains no `supabaseUrl is required` text.

### E.2 Configuration behaviour — the H2 gate is live and working

The served admin bundle resolves its configuration as follows (de-minified from the live artifact):

```js
Vi = Wi(void 0), qi = Wi(void 0),                         // REACT_APP_SUPABASE_URL / ANON_KEY absent
Gi = [["REACT_APP_SUPABASE_URL",Vi],["REACT_APP_SUPABASE_ANON_KEY",qi]]
        .filter(e => null === e[1]).map(e => e[0])        // both reported missing
Ki = 0 === Gi.length;                                     // Ki === false  → configuration is missing
Gi.length > 0 && console.error("❌ CarbonTally Admin is missing Supabase configuration " +
        "(REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY). " +
        "The console will show a configuration notice instead of the dashboard.");
let $i = null, Yi = null;
if (Ki) try { $i = createClient(Vi, qi) } catch (Az) { ... }
```

`void 0` means both variables were `undefined` at build time. Because the guard takes the
`if (Ki)` path only when configuration is **present**, `createClient` is **not** called and the
`supabaseUrl is required` throw cannot occur. (The literal `supabaseUrl is required.` still exists
once in the bundle because it is part of the Supabase client library; its presence is not a defect and
its reachability is what was tested.) All four `UNKNOWN` fallbacks of the provenance helper remain in
the bundle, unused for this build.

**Operator action item (deployment configuration, not a P18-02 defect):** the production admin
deployment has **no** `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY` build settings, so the
console is in its designed *configuration-notice* state and is **not operational**. P18-02's H2 change
is precisely what converts the previous blank page into this actionable, non-crashing notice — so this
observation demonstrates the fix working, while also recording that the admin console still requires
its deployment settings before it can be used. This is out of scope for a publish-only task and must
not be "fixed" by changing code.

### E.3 Privileged-key exposure check

The admin bundle exposes **no** secret material: zero occurrences of `service_role`,
`SERVICE_ROLE` or `serviceRoleKey`, and zero JWT-like key material. The public frontend bundle was
checked identically and also contains zero occurrences of `service_role` / `SERVICE_ROLE` and zero
JWT-like key material. No signed URL, token or key was printed, logged or committed by this task.

## F. LIVE-C — SECURITY HEADER CHECK

All six P18-02 headers were read from **live HTTP responses** (not inferred from source files), on both
`/` and `/admin`. They were then compared, byte-for-byte, against the committed `vercel.json` at
`cb70fd6` — via a scripted comparison (Python) that loaded `cb70fd6:vercel.json`, extracted each
`headers[0].headers[].{key,value}` pair and compared it to the corresponding live response header.

The six requirements:

| # | Header | Required | Observed live value (identical on `/` and `/admin`) | Match |
|---|---|---|---|---|
| 1 | `X-Content-Type-Options` | `nosniff` | `nosniff` | EXACT |
| 2 | `X-Frame-Options` | `SAMEORIGIN` | `SAMEORIGIN` | EXACT |
| 3 | `Referrer-Policy` | `strict-origin-when-cross-origin` | `strict-origin-when-cross-origin` | EXACT |
| 4 | `Permissions-Policy` | restrictive, matching committed config | `camera=(), display-capture=(), geolocation=(), microphone=(), payment=(), usb=(), serial=(), bluetooth=(), hid=(), midi=(), magnetometer=(), gyroscope=(), accelerometer=(), local-fonts=(), xr-spatial-tracking=()` | EXACT |
| 5 | `Content-Security-Policy` (enforced) | matching committed P18-02 subset | `object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'` | EXACT |
| 6 | `Content-Security-Policy-Report-Only` | expected report-only configuration | `default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'self'; form-action 'self'; script-src 'self' https://www.googletagmanager.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://*.supabase.co https://carbontally-api.onrender.com; font-src 'self' data:; connect-src 'self' https://*.supabase.co wss://*.supabase.co https://carbontally-api.onrender.com https://*.google-analytics.com https://*.analytics.google.com https://www.googletagmanager.com; frame-src 'self' blob: https://*.supabase.co https://carbontally-api.onrender.com; worker-src 'self' blob:; media-src 'self' blob:; manifest-src 'self'; upgrade-insecure-requests` | EXACT |

Scripted comparison result:

```
content-security-policy:                  configured=EXACT MATCH
content-security-policy-report-only:      configured=EXACT MATCH
permissions-policy:                       configured=EXACT MATCH
referrer-policy:                          configured=EXACT MATCH
x-content-type-options:                   configured=EXACT MATCH
x-frame-options:                          configured=EXACT MATCH
ALL SIX MATCH: True
```

Additional live observation (not one of the six, recorded for completeness):
`strict-transport-security: max-age=63072000` is present on **both** `/` and `/admin`. P18-02
deliberately deferred HSTS configuration in `vercel.json`; its live presence at the edge is therefore
an **edge/platform-level** header, not evidence about the committed config, and is reported here only
so it is not mistaken for one of the six requirements.

**Pre-push control:** the same probe taken before the push returned **0 of 6** header matches on `/`
(no `nosniff`, no `X-Frame-Options`, no `Referrer-Policy`, no `Permissions-Policy`). The transition
from 0/6 to 6/6 is direct evidence that the live header behaviour changed as a result of this
deployment.

**LIVE-C: PASS.**

## G. LIVE-D — PUBLIC ROUTE SMOKE TEST

| Route | HTTP status | Render check (real headless browser) | Result |
|---|---|---|---|
| `/` | `200` | `#root` populated — `<div id="root"><div class="ct-site"…`; document rendered | PASS |
| `/pricing` | `200` | `#root` populated — `<h1>Indicative pricing</h1>`, `<h2>Plans and pricing</h2>`, `<h2>How the credit model works</h2>` | PASS |
| `/login` | `200` | `#root` populated — `<h1>🌱 CarbonTally</h1>` | PASS |
| `/admin` | `200` | `#root` populated — `<h1>Admin console configuration required</h1>` (see §E) | PASS |

`/`, `/pricing` and `/login` each return the SPA shell (2,272 bytes) per the `vercel.json` rewrite
`/(.*) → /index.html` and then render client-side; `/admin` returns the admin shell (656 bytes) per the
`/admin/(.*) → /admin/index.html` rewrite and renders client-side. All four routes were executed in a
real browser, so "200 with a blank page" was excluded as an explanation.

**Nothing was modified on any route failure — there were no route failures.**

**LIVE-D: PASS.**

---

## H. RENDER SAFETY

The task did **not** deploy the backend, did not trigger Render manually, and did not alter Render
configuration. Render Auto-Deploy was disabled by the operator as a precondition and was left as-is.

Observed evidence bearing on "no unexpected backend deployment":

| Observation | Value | Reading |
|---|---|---|
| GitHub Deployments for the repo (newest first) | `6679336317` (cb70fd6bb, Production, **vercel[bot]**, 2026-09-26T13:20:22Z); then `6656505133`, `6656470429`, `6656388237`, `6656305114`, `6635549675` — **all vercel[bot]** | No Render deployment record was created in connection with this push |
| Commit status on `cb70fd6` | `state=success` with contexts `Vercel=success` **only** | No backend deployment status was reported against the commit |
| Check runs on `cb70fd6` | `Vercel Preview Comments` (completed/success) only | No Render check run |
| Render credentials in this environment | `RENDER_API_KEY` → **not set**; no Render CLI invoked | Nothing in this task could have triggered a Render deploy |
| Live API `GET https://carbontally-api.onrender.com/health` | probes 1–3 → `503`; probe 4 → `200` after **7.84 s**; probes 5–6 → `200` (~0.6 s) | A **suspended-instance cold start**, i.e. the running instance had been idle and was woken by the probe. A backend redeploy at ~13:20 would have left a freshly booted, warm instance; instead the service was still suspended at ~13:34. This is consistent with **no restart** |
| Live API health body | `{"status":"healthy","service":"CarbonTally API","version":"3.0.0", … ,"components":{"api":{"status":"running","version":"3.0.0","routes":49}}}`; `database: connected`, `pool: connected` | Backend is the pre-existing running service (version 3.0.0), consistent with "no redeploy". The endpoint publishes no commit marker, so it cannot independently pin a backend SHA — this is stated rather than glossed |

**CI activity triggered by the push (fully inspected):** the push triggered exactly one GitHub Actions
workflow, `.github/workflows/migration-drift.yml`, run `36244749061`. Its inspection:

* the workflow is a **read-only gate** — a repository-side migration-set check
  (`python -m tools.migration_drift --repo-only`), an optional ledger comparison gated on a secret
  (`MIGRATION_DRIFT_DATABASE_URL`, with a guard that refuses production-looking targets), and an
  evidence-artefact upload. It contains no write, no migration application and no schema change;
* `gh run view 36244749061` → *"This run likely failed because of a workflow file issue."* and the jobs
  API returned `total_count: 0`, i.e. **no job ever started**. Therefore **no step executed** — no
  checkout, no comparator run, no database connection, and no evidence upload;
* the same `failure` / 0-job pattern applies to the six most recent runs of this workflow
  (`36111254260` @98a89d0c1, `36111150947` @5eaf8d0c1, `36110646538` @aced6e7e7, `36110155065`
  @d24a5671d, `35987084190` @790923f19). The failure is therefore **pre-existing and unrelated to
  P18-02**, and it is a CI workflow-state issue, not a deployment.

**Render conclusion:** no unexpected Render production deployment was triggered, and none was
observed. The precondition (auto-deploy disabled) appears to be in effect. No rollback, redeploy or
backend alteration was performed.

---

## I. DATABASE / MIGRATION SAFETY

**This task performed ZERO production database operations.** Explicitly, this task did **not**:

* create, generate, edit or apply any migration;
* run `supabase migration`, `supabase db push`, `psql`, any DDL or any DML;
* change schema, indexes, constraints, policies or RLS;
* seed, reset, truncate or alter any data;
* touch the investor demo dataset or any other dataset;
* connect to the production database at all (no DSN was used from this environment).

Corroborating facts:

| Check | Result |
|---|---|
| Files authored by this task | exactly one: this report (`docs/architecture/…-PUBLISH-VERIFICATION-FINAL.md`), **untracked** |
| Tracked modifications after the task | ` M .gitignore` only — identical to the pre-existing state; no code, config, migration or test file changed |
| Migrations applied by this task | none |
| DB work performed by the CI workflow that the push triggered | **none** — the run had 0 jobs (no step executed), and the workflow is read-only by design |
| Database-touching operations performed | one **read-only `GET /health`** on the Render API, which reported `database: connected`; no write |
| The six P17 migrations | remain **unapplied and unreleased**; they are still a separate PO-authorised production release gate |

**Database safety: PASS (zero operations).**

## J. FINAL ACCEPTANCE

### J.1 Acceptance criteria summary

| Criterion | Result | Primary evidence |
|---|---|---|
| Git pre-flight satisfied | PASS | §A |
| Exactly one commit published, the exact required SHA | PASS | §B — remote branch = `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` |
| No new commit / no force push / no history rewrite | PASS | §B |
| Vercel **Production** deployment for the exact SHA | PASS | §C — deployment `6679336317`, sha `cb70fd6…`, `Vercel=success` |
| LIVE-A: live artifact identifies the exact commit + branch | PASS | §D |
| LIVE-B: `/admin` renders, correct branding, no old marker, no config crash, no privileged key | PASS | §E |
| LIVE-C: all six headers present and matching committed configuration | PASS | §F (6/6 EXACT MATCH) |
| LIVE-D: `/`, `/pricing`, `/login`, `/admin` return 200 and render | PASS | §G |
| Render safety: no unexpected backend deployment | PASS | §H |
| Database safety: zero production DB/migration operations | PASS | §I |

### J.2 Verdict

```
P18_PUBLIC_TRUTH_04_DEPLOYED_AND_LIVE_VERIFIED_PASS
```

**Why this verdict is warranted:** the exact required commit was published by fast-forward with no new
commit and no force; Vercel independently produced a **Production** deployment whose SHA is exactly
`cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` and whose status is `success`; and the **live** artifact was
then observed to identify that same full SHA and branch in both the public frontend and admin bundles,
to render every checked public route, and to serve all six required security headers with values
byte-identical to the committed configuration. No required live check failed, so the stricter
`…_DEPLOYMENT_COMPLETE_LIVE_VERIFICATION_FAILED` verdict does not apply.

### J.3 Observations that do not change the verdict (recorded for the next task)

1. **Admin console has no Supabase configuration in its production build.** The admin deployment
   currently renders the P18-02 *configuration notice* rather than the console (§E.2). This is the H2
   behaviour working as designed and it satisfies LIVE-B, but the admin console is **not operationally
   usable** until `REACT_APP_SUPABASE_URL` and `REACT_APP_SUPABASE_ANON_KEY` are configured for the
   admin deployment. **PO/operator action — not a code change.**
2. **`migration-drift` CI workflow is failing at workflow startup with 0 jobs** (§H), on every recent
   run, independently of P18-02. It is read-only and performed no database work, but the gate provides
   no signal while it fails this way. Separate follow-up.
3. **Render backend cold-start** produces intermittent `503` responses before the instance wakes (§H).
   Pre-existing platform behaviour, observed but not caused by this task.
4. **HSTS is present at the edge** (`strict-transport-security: max-age=63072000`) although P18-02
   deliberately deferred HSTS in the repository configuration (§F). Recorded so it is not
   misattributed to the commit.
5. **`--ff-only` is not a valid `git push` flag in the Git version installed here**; the
   fast-forward-only guarantee was instead established by ancestry proof, an unforced bare-SHA
   refspec, and dry-run/fetch output (§A.3, §A.4, §B).
6. **Untracked local material remains untracked and unpublished** — this report, assorted audit and
   temporary directories, and the pre-existing uncommitted `.gitignore` change (§A.5, §B).

### J.4 Acceptance language (deliberately precise)

* **PUBLISHED:** yes — `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` is now the head of
  `github/p8-release-reconciled`.
* **DEPLOYED:** yes — Vercel Production deployment `6679336317` for that exact SHA, status `success`.
* **LIVE:** yes — `https://carbontally.co.uk` serves the new artifact (`last-modified`
  `2026-09-26T13:20:56 GMT`).
* **LIVE VERIFIED:** yes — the checks in §D, §E, §F, §G were executed against the live site and passed,
  with the previously failing controls (0/6 headers, old admin title) now passing.
* **INDEPENDENTLY VERIFIED:** the P18-02 *commit* was independently verified before this task (as the
  task brief requires). This report's own live checks were performed by the release agent, so they are
  *live-verified by the deploying agent*, not an independent re-verification. An independent
  post-deployment audit remains desirable.
* **PRODUCTION READY (backend / P17 functionality):** **NO** — deliberately not affected by this task.
  The published commit includes backend changes, but the backend was **not** redeployed and the six P17
  migrations remain **unapplied**. Neither P17 backend behaviour nor the migration set is released by
  this publication.

### J.5 Explicitly out of scope / remaining work

| Item | Status | Owner |
|---|---|---|
| Configure admin deployment Supabase build settings | open | operator/PO |
| PO-authorised production migration gate for the six P17 migrations | **not started; NOT authorised here** | PO |
| P17 backend release (whether/when to redeploy the backend) | **not authorised here** | PO |
| Independent post-deployment re-verification of the live artifact | open (recommended) | OHD / QA |
| `migration-drift` workflow startup failure | open (pre-existing) | engineering |
| P18 feature-inventory reconciliation | open (separate task, not this one) | PO/engineering |

---

## K. REPRODUCTION RECIPE (read-only)

Every live check in this report is reproducible without any credential:

```bash
# provenance (LIVE-A)
curl -sS https://carbontally.co.uk/ | grep -oE 'src="/static/js/[^"]+"'          # → main.<hash>.js
curl -sS https://carbontally.co.uk/static/js/main.<hash>.js | grep -oE 'cb70fd6[a-f0-9]*|p8-release-reconciled'

# headers (LIVE-C) — compare against `git show cb70fd6:vercel.json`
curl -sS -o /dev/null -D - https://carbontally.co.uk/ | grep -iE 'content-security-policy|x-content-type-options|x-frame-options|referrer-policy|permissions-policy'
curl -sS -o /dev/null -D - https://carbontally.co.uk/admin | grep -iE 'content-security-policy|x-content-type-options|x-frame-options|referrer-policy|permissions-policy'

# admin artifact (LIVE-B) — rendered DOM, not the shell
google-chrome --headless --disable-gpu --no-sandbox --virtual-time-budget=15000 \
  --dump-dom https://carbontally.co.uk/admin | grep -oE '<h1[^>]*>[^<]*</h1>'
curl -sS https://carbontally.co.uk/admin | grep -cE 'ADMIN PANEL TEST|vercel-admin-debug-marker'

# smoke (LIVE-D)
for p in / /pricing /login /admin; do curl -sS -o /dev/null -w "$p %{http_code}\n" "https://carbontally.co.uk$p"; done
```

Git-side reproduction (the already-performed evidence, for audit):

```bash
git rev-parse HEAD                                   # cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea
git rev-parse HEAD^                                  # db7dca03e230a1de4e9628b8e855e4135c76512f
git ls-remote github p8-release-reconciled           # cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea
git merge-base --is-ancestor 98a89d0c1ab0e850d4ca44e348a66da0515dc691 cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea
```

---

## L. CHANGE RECORD FOR THIS TASK

| Question | Answer |
|---|---|
| Application code changed | **No** |
| Configuration changed | **No** |
| Migrations created or applied | **No** |
| Database written to | **No** |
| RLS changed | **No** |
| Render configuration changed | **No** |
| Backend deployed | **No** |
| Git commits created | **No** |
| Git history rewritten / force-pushed | **No** |
| Remote(s) pushed to | `github` / `p8-release-reconciled` only (fast-forward) |
| Files written by this task | 1 (this report, untracked) |
| Secrets printed, logged or committed | **None** |

---

**Report status:** FINAL. All ten required sections (A–J) are complete, plus a reproduction recipe (K)
and a change record (L). Every stated result is backed by a quoted live observation or a quoted
command output; nothing in this report is inferred from the source tree alone.

