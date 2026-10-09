# CSTR-FINAL03-BLK1 — Post-Remediation Independent Verification (Legacy `/admin` Production Configuration Gap)

**Report ID:** CSTR-FINAL03-BLK1-POST-REMEDIATION-VERIFY-20261003
**Date:** 2026-10-03
**Verifier:** CoStrict (independent verification authority — NOT the implementation agent)
**Type:** Read-only independent verification of a PO-authorised **configuration-only** remediation.
**Predecessor:** `CSTR-FINAL03-BLK1-AUTH-OPS-ADMIN-TOPOLOGY-INVESTIGATION-20261003` (raised/refined BLK-1)

**Authorised change under verification (as declared by the PO):** the two Production environment variables
`REACT_APP_SUPABASE_URL` and `REACT_APP_SUPABASE_ANON_KEY` were added to the existing/root Vercel Production
environment and the existing deployment was redeployed. **No source change, no commit, no push, no database /
Supabase / RLS / DNS / authentication / architecture change** was authorised.

**Evidence labels:** **DC** direct code evidence · **DD** documented decision · **LO** live public observation · **IN** inference · **NT** not testable.

---

## 1. Deployment identity

| Item | Expected | Observed | Result |
|---|---|---|---|
| Local `git rev-parse HEAD` | `375a48dc1b9e9cfd74090bbf747554ae997acb59` | `375a48dc1b9e9cfd74090bbf747554ae997acb59` | **MATCH (DC)** |
| Local branch | `p8-release-reconciled` | `p8-release-reconciled` | **MATCH (DC)** |
| Live **main SPA** bundle contains frozen SHA | present | `main.9bb411d8.js` — frozen SHA **1** occurrence; branch string `p8-release-reconciled` **1** occurrence; `__CARBONTALLY_BUILD_INFO__` present | **MATCH (LO)** |
| Live **legacy admin** bundle contains frozen SHA | present | `main.ed684fd3.js` — frozen SHA **1** occurrence | **MATCH (LO)** |
| Production domain | `https://carbontally.co.uk` | serves both surfaces (see §2/§3) | **MATCH (LO)** |

**Conclusion:** the currently served production deployment corresponds to branch `p8-release-reconciled` at commit
`375a48dc1b9e9cfd74090bbf747554ae997acb59`. No discrepancy. No STOP condition triggered.

> Note (**DC**): the working tree carries **pre-existing** uncommitted items (`.gitignore`, `frontend/App_.js`
> modified; assorted untracked docs/scratch). These are **not** part of the frozen release commit and were **not**
> touched by this verification. The release commit itself is intact at the frozen SHA.

---

## 2. `/admin` — before / after evidence

Observation of `https://carbontally.co.uk/admin` and the served legacy admin bundle.

| Signal | **Before** (predecessor investigation) | **After** (this verification) |
|---|---|---|
| HTTP status | 200 | 200 |
| Served legacy shell | 656 bytes (`<title>CarbonTally Admin</title>`, `noindex`) | 656 bytes, identical shell |
| Admin JS bundle | `main.53ab5f56.js` (1,476,843 B) | **`main.ed684fd3.js`** (1,477,064 B) — **rebuilt** |
| Supabase **project ref** in bundle | **0 occurrences** | **2 occurrences** ✅ |
| Publishable **key value** in bundle | **0** | **2** ✅ |
| `REACT_APP_API_URL` inlined | yes (`carbontally-api.onrender.com`) | yes |
| Config-notice string compiled | present (code) | present (code) — **string exists in code regardless** |
| **Rendered DOM: notice displayed** | **yes** ('Admin console configuration required') | **NO — 0 occurrences** ✅ |
| **Rendered DOM: app state** | configuration notice only | **Legacy Admin Login page** rendered: `Admin Login`, `Enter your credentials to access the admin dashboard`, email + password inputs, `Sign in` button, `← Back to Home` |
| React mounted | no (gate returned before providers) | **yes** — `_goober` injected styles + populated `#root` |

**Interpretation (IN):** the app now boots past the `if (!isSupabaseReady)` configuration gate
([`admin/src/App.js:102`](admin/src/App.js:102)), constructs its Supabase client, initialises the auth context,
mounts the router, and — with no session present — performs its correct client-side redirect to the legacy
`/admin/login` route ([`admin/src/App.js:49`](admin/src/App.js:49), [`admin/src/App.js:64`](admin/src/App.js:64)).
The notice's absence proves the client is now configured; the rendering of the login page proves the app is
functional up to the authentication boundary.

**`/admin*` Vercel rewrite intact (LO):** `/admin` and `/admin/` both resolve to the 656-byte legacy shell and the
distinct asset tree `/admin/static/js|css/…`; all other paths resolve to the main SPA. The root rewrite
([`vercel.json:14`](vercel.json:14), [`vercel.json:18`](vercel.json:18)) is unchanged and effective.

**Runtime errors:** the headless render completed and produced a fully-mounted authenticated-boundary DOM. **No
fatal runtime error** (no blank page, no thrown module-evaluation error). Console-level detail is **NT** (headless
`--dump-dom` does not capture the full console stream); **no fatal error is observable**, which is the material point
(the pre-remediation failure was a hard pre-mount crash into the notice).

---

## 3. `/ops` — canonical surface evidence

| Signal | Observed |
|---|---|
| HTTP status | 200 |
| Shell | main SPA shell (2272 bytes), `<title>CarbonTally — Carbon Data Processing & Emissions Management Platform</title>` |
| Bundle | `main.9bb411d8.js` (2,372,680 B) |
| Routed to `/admin`? | **No** — served by the main SPA asset tree, rendered by the V3 router |
| Rendered DOM (unauthenticated) | main SPA boots then shows the sign-in form (`type="password"`, `name="email"` present) — the correct, expected unauthenticated state for a `requireInternalStaff` route |
| Config notice present | no |

**Conclusion (LO + DC):** `/ops` remains present, remains served by the canonical main application, and has **not**
been redirected to `/admin`. The route is unchanged at
[`App.js:2188`](frontend/src/App.js:2188) (`ProtectedRoute > RoleRoute requireInternalStaff > V3Layout > OperationsPage`).
**BLK-1-A CONFIRMED.**

---

## 4. Authentication architecture confirmation (repository evidence)

The chain remains intact (**DC**):

`/login` → authentication → `/auth/callback` (when applicable) → `GET /api/v3/me/context` → **server-decided destination**.

| Destination | Source |
|---|---|
| `staff → /ops` | [`me_context`](backend/api/v3_context.py:34) |
| `entity_staff → /pe` | [`me_context`](backend/api/v3_context.py:34) |
| `consultant → /consultant` | [`me_context`](backend/api/v3_context.py:34) |
| `customer → /home` | [`me_context`](backend/api/v3_context.py:34) |
| `new/unresolved → /onboarding` | [`me_context`](backend/api/v3_context.py:34) (fail-closed: resolution error → HTTP 500, never "new user") |

Client-side guards ([`RoleRoute`](frontend/src/v3/components/RoleRoute.jsx:83)) mirror the server decision and do not
replace it. Live `/login` and `/auth/callback` both return HTTP 200 on the main SPA shell (**LO**).

**Authenticated execution:** **NOT TESTABLE — NO AUTHORIZED PRODUCTION IDENTITY.** No production credential exists
in the workspace and none may be created. This is **not** a BLK-1 failure.

---

## 5. Legacy authorization boundary evidence

| Property | Evidence | Result |
|---|---|---|
| `/admin` is **not** the canonical routing destination | Server resolver returns `/ops` for staff ([`v3_context.py:34`](backend/api/v3_context.py:34)); no `/admin` route in `frontend/src` (0 matches) | **CONFIRMED (DC)** |
| Staff authorization is **server-enforced** | V3: `ensure_staff_permission` ([`operations_auth.py:95`](backend/api/operations_auth.py:95)); legacy: admin-gated backend API with operator bearer token ([`adminApi.js:17`](admin/src/services/adminApi.js:17)) | **CONFIRMED (DC/DD)** |
| Legacy admin API calls remain protected | Legacy screens call `/api/admin/*` and `/api/v2/admin/audit` via the bearer-token helper; endpoints serve under `require_admin` | **CONFIRMED (DC/DD)** |
| No client-side role check is the sole boundary | [`RoleRoute`](frontend/src/v3/components/RoleRoute.jsx:83) is documented UX-only; legacy `AuthContext` fail-closed is a UX gate, not the authorization mechanism | **CONFIRMED (DC)** |
| No service-role credential in the browser | `service_role` = 0, `sb_secret_`/`sbp_` = 0, JWT = 0 in the deployed admin bundle (§6) | **CONFIRMED (LO)** |

The remediation introduced **no new authorization mechanism** — it changed build-time configuration only.

---

## 6. Security regression checks

### 6.1 Credential exposure in the deployed bundles

| Check | Main SPA `main.9bb411d8.js` | Legacy admin `main.ed684fd3.js` |
|---|---|---|
| `service_role` literal | 0 | **0** |
| `SUPABASE_SERVICE*` literal | — | **0** |
| JWT (`eyJ…`) | 0 | **0** |
| `role:service_role` claim | — | **0** |
| `sb_secret_` / `sbp_` secret tokens | — | **0** |
| Distinct `sb_publishable_…` values | 1 | 1 (browser-safe publishable key — expected, not a secret) |

**Verdict:** no privileged credential is present in either bundle. The only key material is the browser-safe
publishable key, which is by design public. **No SECURITY BLOCKER.**

### 6.2 Database / RLS / schema regression (read-only, in-session `default_transaction_read_only = on`)

| Metric | Accepted P3 baseline | Now | Result |
|---|---|---|---|
| Migration count | 98 | **98** | unchanged |
| Migration tip | `20261029000000` | **`20261029000000`** | unchanged |
| Public tables | 150 | **150** | unchanged |
| RLS-enabled (public) | 147 | **147** | unchanged |
| Policies total | 235 | **235** | unchanged |
| `anon`/`public` policies | 0 | **0** | unchanged |

**Verdict:** no schema, migration or RLS change; no anonymous access added. **CONFIRMED.**

### 6.3 Source / routing / architecture regression

- Frozen source release unchanged: local HEAD == frozen SHA; both live bundles carry the frozen SHA (**DC**).
- `/ops` routing unchanged (§3) (**DC/LO**).
- Deployment topology (single Vercel project; `/admin` rewrite) unchanged ([`vercel.json:14`](vercel.json:14)) (**DC/LO**).
- No service-role exposure, no weakened staff authorization, no cross-tenant change introduced by a *configuration-only* change (**IN**).

**BLK-1-D — security regression: NONE OBSERVED.**

---

## 7. Legacy capability reachability

Code-level presence in the deployed legacy bundle `main.ed684fd3.js` (**LO**, static analysis). Authenticated
functional execution is **NT** for all four (no authorised production identity).

| Capability | Route string in bundle | API endpoint in bundle | Status |
|---|---|---|---|
| **Bulk operations** | (utilised within admin screens) | `/api/admin/defra/factors/bulk` | present at code level; **functional = NOT TESTABLE — NO AUTHORIZED PRODUCTION IDENTITY** |
| **Beta management** | `/admin/beta-management`, `/admin/beta` | `/api/admin/beta/codes` | present at code level; **functional = NOT TESTABLE** |
| **Email logs / templates** | `/admin/logs`, `/admin/log-viewer` | `/api/admin/logs/email` | email **logs** present; **no `templates` route/endpoint literal** in this build → email-template CRUD not evidenced; **functional = NOT TESTABLE** |
| **Document-type administration** | — | — | **no `document-type` literal** in this build → not evidenced at code level; **functional = NOT TESTABLE** |

**Observation (IN):** two of the four legacy-only families named in
[`CARBONTALLY_LEGACY_ADMIN_INVENTORY.md`](docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md:32) —
email-template CRUD and document-type administration — show **no literal route or endpoint string** in the currently
deployed admin bundle, whereas beta management, bulk factor operations and email **logs** are present. This is stated
as an observation for PO awareness, **not** as a defect: these were already classified as legacy-only retention
items, and their authenticated behaviour cannot be established without an authorised identity.
**NOT TESTABLE — NO AUTHORIZED PRODUCTION IDENTITY** for all four.

---

## 8. BLK-1 verdicts

| # | Question | Verdict |
|---|---|---|
| **BLK-1-A** | `/ops` canonical | **CONFIRMED** — `/ops` serves the main application (HTTP 200), is not redirected to `/admin`, and remains the `requireInternalStaff` destination per the server resolver. |
| **BLK-1-B** | `/admin` legacy classification | **CONFIRMED** — `/admin` remains the retained, quarantined legacy CRA served only by the `vercel.json` rewrite; it is not a routing destination for staff and introduces no new authorization mechanism. |
| **BLK-1-C** | Legacy Admin configuration | **RESOLVED** — the deployed legacy admin bundle now inlines the production Supabase project identity and a publishable key (0 → 2), and the rendered `/admin` DOM shows the **Admin Login** page with **no** configuration notice. Client initialisation no longer fails for missing configuration. |
| **BLK-1-D** | Security regression | **NONE OBSERVED** — no service-role/secret exposure, no schema/RLS/migration change, no anonymous access, no `/ops` routing change, frozen source release unchanged. |
| **BLK-1-E** | FINAL-03 BLK-1 status | **CLEARED** — the previously reported configuration gap is remediated and no security or architecture regression was introduced. |

**Scope caveat (explicit):** BLK-1-E **CLEARED** addresses the specific condition that BLK-1 described (legacy admin
could not initialise for missing Supabase configuration). It does **not** assert authenticated functional
acceptance of the legacy console — that remains **NT** for want of an authorised production identity, and is
**not** a BLK-1 failure.

---

## 9. Comparison with the previous BLK-1 finding (§10 of the brief)

| | Before remediation | After remediation |
|---|---|---|
| Admin bundle | `main.53ab5f56.js` | `main.ed684fd3.js` |
| Supabase project ref inlined | **absent (0)** | **present (2)** |
| Publishable key inlined | **absent (0)** | **present (2)** |
| Rendered `/admin` DOM | configuration notice only | **Admin Login page** (app boots) |
| Notice displayed | **yes** | **no (0 occurrences)** |

**Original failure status: RESOLVED.** (Determined from observed artefacts — the rebuilt bundle, the inlined
configuration, and the rendered DOM — **not** from the Vercel deployment status.)

---

## 10. Limitations

1. **No authorised production identity** → authenticated execution of `/admin` post-login, the four legacy
   capability areas, and the `/ops` staff console is **NOT TESTABLE**. Not a BLK-1 failure.
2. **Console stream not captured** — headless `--dump-dom` proves the app mounted past the gate and rendered the
   login route, but the full browser console log was not recorded; no fatal error is observable.
3. **No Vercel/Render operator console access** — the remediation (two env vars added, redeploy) is verified by its
   **effect** on the served artefacts, not by direct configuration inspection.
4. **`/admin` login submit, logout, relogin** were not exercised (would require credentials / mutation).
5. **Publishable key is public by design** — it is not treated as a secret; only the *presence* of a browser-safe
   publishable key (and the *absence* of any privileged credential) was recorded. No key value is reproduced here.
6. **Pre-existing working-tree modifications** (`.gitignore`, `frontend/App_.js`, untracked docs) are outside the
   release commit and were not analysed for this verification.

---

## 11. Exact files / URLs inspected

**URLs (unauthenticated GET):**
`https://carbontally.co.uk/`, `/login`, `/ops`, `/organization`, `/auth/callback`, `/admin`, `/admin/`,
`/admin/static/js/main.ed684fd3.js`, `/static/js/main.9bb411d8.js`.

**Repository files read:**
`frontend/src/App.js`, `frontend/src/v3/components/RoleRoute.jsx`, `frontend/src/supabaseClient.js`,
`backend/api/v3_context.py`, `backend/api/operations_auth.py`,
`admin/src/App.js`, `admin/src/context/AuthContext.js`, `admin/src/services/adminApi.js`, `admin/package.json`,
`vercel.json`, `package.json`, `.vercelignore`,
`docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md`,
`docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md`,
`docs/architecture/CT-PO-P18-PUBLIC-TRUTH-02-DEPLOYMENT-ADMIN-SECURITY-HARDENING-20260926.md`,
`docs/architecture/CARBONTALLY_ANALYTICS_GA4_ADMIN_CONFIGURATION_20260913.md`,
`docs/audit/costrict/CSTR-FINAL03-BLK1-AUTH-OPS-ADMIN-TOPOLOGY-INVESTIGATION-20261003.md`,
`docs/audit/costrict/CSTR-FINAL03-LIVE-ACCEPTANCE-001-20261003.md`.

**Tooling:** system `google-chrome-stable` (headless `--dump-dom`); `curl`; `git`;
read-only production `psql` wrapper (`SET default_transaction_read_only = on`). Downloaded public bundles were
analysed under `/tmp` only.

---

## 12. Confirmation of non-mutation

> **NO FILES / CODE / DATABASE / SUPABASE / DNS / VERCEL CONFIGURATION WERE MODIFIED BY THIS VERIFICATION.**

No user, organisation, session or production record was created. No production data was modified. No Vercel
configuration, DNS record, Supabase object, RLS policy, grant, migration or schema was altered. No source file was
edited except the creation of this report. No commit, push, deploy or service restart was performed. The only
production database access was **read-only** (`default_transaction_read_only = on`); the only network access was
unauthenticated HTTP GET of public resources and public bundle downloads.

---

**READY FOR PO REVIEW — BLK-1 POST-REMEDIATION VERIFICATION COMPLETE — NO REMEDIATION PERFORMED**
