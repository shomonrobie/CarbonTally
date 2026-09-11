# CT-PROD-DEEP-LINK-ROUTING-FIX-20260911-001

**Prompt Ref:** `CT-PROD-DEEP-LINK-ROUTING-FIX-20260911-001`
**Response Ref:** `CT-PROD-DEEP-LINK-ROUTING-FIX-20260911-001-R1` · **Datetime:** 2026-09-11
**Starting commit:** `36cbd3fe857204c7510c1b1ee2f7a48da552b4dc` (local `main`)
**Mode:** bounded production routing-defect fix. No Phase 7/8 work; no migration or schema change; no
production Supabase contact; no Google/Vercel/Render dashboard change; no deployment performed by the agent.

## 1. Reported symptom (Product Owner)

> "I could see page contents of login page and terms page after clicking from the home page, but while on the
> said page, if I reload, the content vanishes."

Client-side navigation renders the page; a cold load or browser refresh of any deep link returns Vercel
`404: NOT_FOUND`.

## 2. Evidence gathered (all read-only)

**Repository / configuration**

| # | Evidence | Result |
|---|---|---|
| E1 | `.vercel/project.json` (repo root) | `projectName: carbon-tally`, `projectId: prj_800l8OHgLU39OmLDw0fwPBWQGXtr` — the Vercel project is linked at the **repository root**, so the root `vercel.json` is the effective configuration |
| E2 | root `package.json` `build` | builds `frontend/` + `admin/`, then `cp -r frontend/build/* public/` and `cp -r admin/build/* public/admin/` → the shell is the output root's **`/index.html`**, assets are **`/static/…`** |
| E3 | root `vercel.json` (at `36cbd3f`) | `cleanUrls: true` **plus** rewrites whose destinations are `/index.html` and `/admin/index.html` |
| E4 | `frontend/vercel.json` and `frontend_backup_pre_v3_public_20260827/vercel.json` | both use the canonical `/(.*)` → `/index.html` with **no** `cleanUrls` — the repository's own convention |
| E5 | `frontend/package.json` `homepage` = `/`, `frontend/public/index.html` uses `%PUBLIC_URL%` | the built shell references assets **absolutely**, so a shell served at `/login` still loads `/static/…` |
| E6 | live `/static/js/main.4f7b530d.js` | bundle **contains the `36cbd3f` code** (`temporarily unavailable`, `AUTH_SERVICE_UNAVAILABLE`, `auth-service-unavailable`) |
| E7 | live `/asset-manifest.json` headers | `last-modified: Fri, 11 Sep 2026 13:49:53 GMT` (= 19:49 local, **after** the 19:43 commit) — the deployment is current, **not** stale |
| E8 | Vercel JSON-schema definition of `cleanUrls` | *"When set to `true`, all HTML files and Serverless Functions will have their extension removed. When visiting a path that ends with the extension, a 308 response will redirect the client to the extensionless path."* |
| E9 | Vercel routing-order documentation | layers run Firewall → … → Project Routes → Deployment Routes → **Headers + Redirects** → Middleware → **File System Routes** → **Rewrites** |

**Live routing probes (`https://carbontally.co.uk`, 2026-09-11)**

| Path | Result | Interpretation |
|---|---|---|
| `/` | **200** (2272-byte shell) | file-system index |
| `/static/js/main.4f7b530d.js` | **200** | file-system asset |
| `/admin` | **200** (legacy admin shell) | file-system **directory index** — needs no rewrite |
| `/index.html` | **308 → `/`** | cleanUrls active (E8) |
| `/admin/index.html` | **308 → `/admin`** | cleanUrls active |
| `/zzz.html` | **308 → `/zzz`** | cleanUrls active (unconditional for `.html` paths) |
| `/login`, `/privacy`, `/terms`, `/privacy-policy`, `/zzz-nonexistent-12345` | **404** `x-vercel-error: NOT_FOUND` | no rewrite resolved |
| `/admin/deep-not-a-real-path-98765` | **404** | the trivially correct `/admin/(.*)` → `/admin/index.html` rewrite **also** failed |

## 3. Diagnosis

`vercel.json` set **`cleanUrls: true`**. `cleanUrls` removes the `.html` extension from every HTML file's
route (E8), so the shell is exposed at **`/`** and **not** at `/index.html`. Every SPA rewrite whose
destination was an `…/index.html` path therefore resolved to nothing and fell through to Vercel's hard 404 —
including the correct `/admin/(.*)` → `/admin/index.html` rule (E-probe row 9). `/` kept working only because
the **file-system** layer is evaluated before the **rewrites** layer (E9).

This **supersedes** the earlier explanation recorded in
`CT-PROD-AUTH-ACCESS-CLOSURE-20260911-001` §3 D1 ("the catch-all pointed at a non-existent
`/frontend/index.html`"). That defect was real and was fixed in `36cbd3f`; it was **not sufficient**, because
the deployed configuration still returned 404 for every deep link. The deployment was not stale (E6/E7) — the
configuration itself was the remaining fault.

**Operational impact:** while `/auth/callback` 404s, Google sign-in cannot complete — the OAuth return lands on
a Vercel error page.

## 4. Fix applied (one line of configuration)

`vercel.json`: **`"cleanUrls": true` → `"cleanUrls": false`**. Everything else is unchanged — the canonical
catch-all `/(.*)` → `/index.html` stays **last**, behind the `/static/**` and `/admin/**` shields. Setting the
value **explicitly** also overrides any equivalent Vercel project setting.

Rationale for not rewriting the destinations instead: the `…/index.html` destinations are the canonical
Vercel/CRA SPA pattern, they are what this repository already uses in `frontend/vercel.json` and the pre-V3
backup config, and `cleanUrls` is not needed by this application (no route, link, sitemap entry or redirect
uses a `.html` URL — the sitemap lists extensionless paths only).

**No frontend code change was needed or made:** the built shell already references assets absolutely
(E5), and every affected route exists in the client route table (`App.js`: `/login` 2001, `/privacy` 2002,
`/terms` 2005, `/auth/callback` 2015, …).

## 5. Regression coverage (new)

`qa_harness/tests/harness/test_deployment_routing_config.py` — 7 read-only tests:
`cleanUrls` is explicitly `false` while any rewrite destination ends in `.html`; exactly one catch-all exists,
is last, and targets `/index.html`; asset shields precede the catch-all; `frontend/vercel.json` does not
re-enable `cleanUrls`; the frontend publishes `homepage: "/"` with a `%PUBLIC_URL%` shell template; the root
build script publishes `frontend/build` into the deployment output.

## 6. Verification performed

| Check | Command | Result |
|---|---|---|
| New tests pass | `qa_harness/.venv/bin/python -m pytest tests/harness/test_deployment_routing_config.py -q` | **7 passed** |
| Guard has teeth (negative control) | `cleanUrls` temporarily forced back to `true`, guard re-run, file restored from backup | guard **FAILED** as intended, then **PASSED** after restore; `git diff -- vercel.json` confirms the restored file differs from `36cbd3f` by exactly the one line |
| No harness regressions | `qa_harness/.venv/bin/python -m pytest tests -q` | **260 passed** |
| Production | read-only probes only | deep links still 404 (expected — the fix is not deployed yet) |

## 7. Unresolved items

| # | Item | Owner |
|---|---|---|
| R1 | The corrected `vercel.json` must be **deployed** (push to `main` or a Vercel redeploy) before the deep links return 200 | PO / publishing step |
| R2 | If deep links still 404 after a verified deploy, inspect the Vercel project's Root/Output Directory, any dashboard Project Route or `cleanUrls` toggle, and whether the Root Directory has been switched to `frontend/` (which would make `frontend/vercel.json` effective) | PO (dashboard) |
| R3 | Google OAuth consent branding and Supabase Site URL/redirect allow-list remain external dashboard items (unchanged by this fix) | PO (dashboard) |
| R4 | `/admin` still publicly serves the quarantined legacy admin shell (pre-existing hygiene item, unchanged) | PO, per CL-66 / D-P2-02 |
| R5 | Browser-level deep-link acceptance (refresh on `/login`, `/privacy`, `/terms`, `/auth/callback` in a real browser) is possible only after deployment | PO / next independent verification |

## 8. Attestation

* **starting commit:** `36cbd3fe857204c7510c1b1ee2f7a48da552b4dc`
* **files changed:** `vercel.json` (1 line); `qa_harness/tests/harness/test_deployment_routing_config.py` (new);
  `docs/architecture/CARBONTALLY_PRODUCTION_LOGIN_RUNBOOK_20260911.md` (§7.1 corrected);
  `docs/architecture/CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md` (new §11);
  `docs/architecture/CARBONTALLY_POST_PUBLICATION_CHANGELOG_20260911.md` (new §7);
  `docs/cline/prompt-history/CT-PROD-DEEP-LINK-ROUTING-FIX-20260911-001.md` (this record)
* **migrations created/applied:** **NO** · **database changes:** **NO**
* **production Supabase contacted/modified:** **NO**
* **Google / Vercel / Render dashboard changed:** **NO**
* **production URLs tested:** **YES** (read-only HTTP probes)
* **deployment performed by agent:** **NO**
* **secrets introduced:** **NO**
* **Phase 7 / Phase 8 started:** **NO**

## FINAL VERDICT

**DEEP-LINK/REFRESH ROUTING DEFECT — ROOT CAUSE IDENTIFIED, FIXED AND TESTED IN THE REPOSITORY;
PRODUCTION DEPLOYMENT REQUIRED.**

## STOP CONDITION

Reported and stopped. The fix is repository-side; publishing it to production is a separate, explicitly
authorised action.
