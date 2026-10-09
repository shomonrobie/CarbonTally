# CSTR-FINAL03-BLK1 — Production Authentication, `/ops` Canonical Staff Routing and Legacy `/admin` Topology — Forensic Investigation

**Report ID:** CSTR-FINAL03-BLK1-AUTH-OPS-ADMIN-TOPOLOGY-INVESTIGATION-20261003
**Date:** 2026-10-03
**Investigator:** CoStrict (independent verification authority — NOT the implementation agent)
**Type:** Read-only forensic investigation. No remediation.
**Predecessor:** `CSTR-FINAL03-LIVE-ACCEPTANCE-001-20261003` (which raised BLK-1)

**Evidence labels used throughout**

| Label | Meaning |
|---|---|
| **DC** | DIRECT CODE EVIDENCE — read from the current repository source |
| **DD** | DOCUMENTED DECISION — a ratified Product-Owner / architecture decision in the repository |
| **LO** | LIVE PUBLIC OBSERVATION — an unauthenticated HTTP observation of the production deployment |
| **IN** | INFERENCE — a conclusion derived from the above, stated as such |
| **NT** | NOT TESTABLE — cannot be established without production credentials or operator console access |

---

## A. Executive conclusion

> **CONFIRMED — `/ops` is the canonical production staff destination and legacy `/admin` is correctly classified (deprecated, quarantined, retained).**

The routing, authentication and deployment topology are exactly as the ratified architecture documents state:

1. `/ops` (V3, inside the main React application) **is** the canonical internal staff / administration surface, guarded by a server-authoritative role resolution (`GET /api/v3/me/context`). It is deployed and served (HTTP 200) in production.
2. `/admin` **is** the legacy, **DEPRECATED** admin CRA — quarantined, not deleted, served only by the deployment rewrite, using legacy `/api/admin/*` endpoints. There is **no** internal-staff `/admin` route in the V3 application.
3. **BLK-1 must be refined** (see §H). The surfaced symptom was *"the production admin console cannot start"*. That is **CONFIRMED as a live fact** for the legacy `/admin` surface, and its root cause is a **deployment-environment configuration gap** (the admin build is missing `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY`), **not** a code defect and **not** a failure of the canonical `/ops` surface. The canonical surface is intact.

The investigation therefore *substantially narrows* BLK-1's release impact: the mandatory internal operating surface (`/ops`) is functional; the non-functional console is the already-deprecated legacy surface whose retention is itself a documented, not-yet-retired item. Whether that residual affects the FINAL-03 release gate is a **PO DECISION** (§K).

---

## B. Scope and method

**In scope:** determine whether `/ops` is the canonical production staff/admin destination with role-based routing while `/admin` is a retained legacy surface; reconstruct the intended deployment topology; establish the root cause of the BLK-1 symptom; answer the five mandated sub-questions (BLK-1-A…E).

**Method:** (1) read the routing, guard and auth source in both applications; (2) read the ratified decision documents; (3) read the deployment/build configuration; (4) perform unauthenticated live HTTP observations of the production deployment; (5) analyse the two deployed JavaScript bundles for inlined configuration. Every claim is labelled DC/DD/LO/IN/NT.

**Out of scope / not performed:** no production credential was used, so no authenticated session was established (NT). No remediation of any kind.

---

## C. Evidence base

### C.1 Documented decisions (**DD**)

| Ref | Document | Decision |
|---|---|---|
| D-P2-02 | [`CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md`](docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md:80) | **Legacy admin: DEPRECATE.** "The V3 internal operations surface (`/ops`) is the canonical CarbonTally internal administration system. The legacy admin surface is **deprecated, not deleted**." No new feature may be built on legacy admin. |
| §2 | [`CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md`](docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md:20) | "The legacy admin CRA is **quarantined**, not deleted: it is served only by the deployment rewrite (`vercel.json`) … The V3 main app has **no `/admin` route**; `/admin` in the main app resolves to the customer/404 surface." |
| §2 | [`CARBONTALLY_LEGACY_ADMIN_INVENTORY.md`](docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md:19) | Feature-coverage matrix legacy → V3; 5 rows ✅ FULL, 5 rows 🟡 PARTIAL, 4 rows ❌ NONE (bulk, beta, email templates/logs, plus the admin document-type CRUD). |
| §4 | [`CARBONTALLY_LEGACY_ADMIN_INVENTORY.md`](docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md:46) | Retirement conditions — **not yet met**; condition 2 requires the `vercel.json` `/admin` rewrite to be removed from deployment. |
| GA4 §2 | [`CARBONTALLY_ANALYTICS_GA4_ADMIN_CONFIGURATION_20260913.md`](docs/architecture/CARBONTALLY_ANALYTICS_GA4_ADMIN_CONFIGURATION_20260913.md:35) | New admin capability is delivered on **`/ops → Settings → Analytics & Integrations`** (`frontend/src/v3/ops/SettingsTab.jsx`) — i.e. the canonical surface is actively being extended, not the legacy one. |
| H2 | [`CT-PO-P18-PUBLIC-TRUTH-02…`](docs/architecture/CT-PO-P18-PUBLIC-TRUTH-02-DEPLOYMENT-ADMIN-SECURITY-HARDENING-20260926.md:215) | The legacy admin was deliberately converted from a **blank page** to a **controlled configuration notice** when Supabase configuration is absent. |
| §19.1 | [`CT-PO-P18-PUBLIC-TRUTH-02…`](docs/architecture/CT-PO-P18-PUBLIC-TRUTH-02-DEPLOYMENT-ADMIN-SECURITY-HARDENING-20260926.md:622) | Verified observation: the **frontend** Supabase client has a **hard-coded project URL fallback** while the admin client has none. |

### C.2 Direct code evidence (**DC**)

| Ref | File | Fact |
|---|---|---|
| Server resolver | [`me_context`](backend/api/v3_context.py:34) | Server-authoritative destination: `staff → "/ops"`, `entity_staff → "/pe"`, `consultant → "/consultant"`, `customer → "/home"`, `new_user → "/onboarding"`; fail-closed (HTTP 500 on resolution error, never "new user"). |
| Client guard | [`RoleRoute`](frontend/src/v3/components/RoleRoute.jsx:83) | Resolves roles from `/api/v3/me/context`; `isInternalStaff = actor_type === 'staff'`; fail-closed on resolution failure. Comment: "The backend/RLS remain the authoritative security boundary; these guards are UX/navigation only." |
| Route | [`/ops`](frontend/src/App.js:2188) | `ProtectedRoute > RoleRoute requireInternalStaff > V3Layout > OperationsPage`. |
| Route | [`/organization`](frontend/src/App.js:2161) | `ProtectedRoute > RoleRoute requireOrg > V3Layout > AdminPage` — the V3 **customer organisation admin** (D17 master data), guarded by `requireOrg`, **not** the internal control plane. |
| Route | [`*` catch-all](frontend/src/App.js:2269) | `<Navigate to="/" replace />`. |
| Frontend client | [`frontend/src/supabaseClient.js`](frontend/src/supabaseClient.js:5) | Hard-coded fallback URL **and** publishable key: `process.env.REACT_APP_SUPABASE_URL \|\| 'https://pvwiojoyaqywtydzcpbg.supabase.co'`. |
| Admin gate | [`admin/src/App.js`](admin/src/App.js:102) | `if (!isSupabaseReady) return <AdminConfigNotice …/>` before any provider/router. |
| Admin auth | [`admin/src/context/AuthContext.js`](admin/src/context/AuthContext.js:22) | Fail-closed when the client is absent; queries `staff_profiles` **directly via PostgREST**. |
| Admin API | [`admin/src/services/adminApi.js`](admin/src/services/adminApi.js:17) | `const API_URL = process.env.REACT_APP_API_URL \|\| 'http://localhost:8000'`; bearer-token calls to the backend. |
| Rewrite | [`vercel.json`](vercel.json:14) | `/admin/(.*) → /admin/index.html`; [`/admin`](vercel.json:18) → `/admin/index.html`. |
| Build | [`package.json`](package.json:6) | Root build assembles **both** CRAs into one output: `… cp -r frontend/build/* public/ && cp -r admin/build/* public/admin/`. |
| Homepage | [`admin/package.json`](admin/package.json:4) | `"homepage": "/admin"`. |

### C.3 Live public observations (**LO**, unauthenticated, 2026-10-03)

| Path | Status | Bytes | Served asset | Interpretation |
|---|---|---|---|---|
| `/` | 200 | 2272 | `/static/js/main.5aec9908.js` | main SPA shell |
| `/login` | 200 | 2272 | main SPA shell | client-routed |
| `/ops` | 200 | 2272 | main SPA shell | client-routed; guarded client-side, authorised server-side |
| `/organization` | 200 | 2272 | main SPA shell | client-routed |
| `/auth/callback` | 200 | 2272 | main SPA shell | client-routed |
| **`/admin`** | **200** | **656** | **`/admin/static/js/main.53ab5f56.js`** | **legacy admin shell** (distinct asset tree) |
| `/admin/` | 200 | 656 | legacy admin shell | same |

Legacy `/admin` shell `<head>` (verbatim): `<title>CarbonTally Admin</title>`, `<meta name="robots" content="noindex, nofollow"/>`, `<noscript>You need to enable JavaScript to run the CarbonTally Admin console.</noscript>` — i.e. the post-M2 (P18) build.

**Live bundle configuration analysis (the decisive evidence for BLK-1's root cause):**

| Bundle | Project ref `pvwiojoyaqywtydzcpbg` | Long publishable key value | `carbontally-api.onrender.com` | Admin config-notice strings |
|---|---|---|---|---|
| Main SPA `main.5aec9908.js` (2,372,501 B) | **1 occurrence** | **1** | present | n/a |
| Legacy admin `main.53ab5f56.js` (1,476,843 B) | **0 occurrences** | **0** (bare `sb_publishable_` prefix = supabase-js library check only) | **present** | **`Admin console configuration required` + `Missing build settings` present** |

**Interpretation (IN):** the main SPA inlines its hard-coded fallback Supabase URL/key and therefore works **without** any build variables. The legacy admin inlines **no** Supabase URL/key — so its runtime `supabaseUrl`/`supabaseAnonKey` are `undefined`, `isSupabaseReady` is `false`, and `App` renders the configuration notice. It *does* inline `REACT_APP_API_URL` (`https://carbontally-api.onrender.com`) — so the deployment's admin build environment sets the API base **but not** the two Supabase settings. This is precisely the H2 design behaviour (**DD** §C.1), reached because the settings are absent.

---

## D. Authentication flow trace

`customer/public → supabase.auth.signInWithPassword | signInWithOAuth → session → GET /api/v3/me/context → destination → navigate(destination)`

- **Login** uses the shared `supabase` client and, after session detection, routes via `goToWorkspace(navigate)` — the client asks the **server** where the actor belongs (**DC**).
- **`GET /api/v3/me/context`** ([`me_context`](backend/api/v3_context.py:34)) resolves precedence **internal staff → entity staff → consultant → organisation member → new user**, and returns the destination. Authentication/authorisation is decided **server-side**; the frontend guard only mirrors it (**DC**).
- **`RoleRoute`** ([`RoleRoute.jsx`](frontend/src/v3/components/RoleRoute.jsx:83)) fetches the context and enforces the required role for the route; on a resolution failure it fails **closed** (controlled error/retry), it does not silently redirect (**DC**).
- **Staff authorization model:** internal staff identity is `staff_profiles`; the permission catalog is `staff_roles.permissions`, enforced via `ensure_staff_permission` in the backend ([`operations_auth.py`](backend/api/operations_auth.py:95)) — never name-string matching (**DD** §3, **DC**).

**Consequence:** production routing sends internal staff to **`/ops`**, entity staff to **`/pe`**, consultants to **`/consultant`**, organisations to **`/home`**, new users to **`/onboarding`**. **No** code path routes a staff user to `/admin`. A repo-wide search of `frontend/src` for `/admin` route strings returned **0** matches; all `window.location`/`navigate` uses are unrelated (pricing, signup, retry/reload, OAuth redirect, canonical link) (**DC**). **BLK-1-A — YES.**

---

## E. `/ops` canonical routing evidence

- Route definition and guard: [`/ops`](frontend/src/App.js:2188) → `requireInternalStaff`; sub-routes `/ops/items/:itemId`, `/ops/review/:itemId`, `/ops/qc/:itemId` all `requireInternalStaff`; `/ops/operational-health` deep-link redirects to `/ops?tab=operational-health` (**DC**).
- Surface inventory: **28** files under [`frontend/src/v3/ops/`](frontend/src/v3/ops) — `OperationsPage`, `OpsDashboard`, and permission-aware tabs including `AuditConsoleTab`, `BackupsTab`, `CommercialTab`, `CtQcTab`, `IssuesTriageTab`, `OperationalHealthTab`, `OpsAssignmentsTab`, `OpsMessagingTab`, `ProcessingEntitiesTab`, `SettingsTab`, `SlaTab`, `StaffRolesTab`, `StaffRoster`, `ReviewQueue`/`QcQueue`/`OperatorQueue` (**DC**).
- The canonical surface is the one under active development: GA4 admin configuration was added to `/ops → Settings` (**DD** §C.1).
- Live: `/ops` returns HTTP 200 on the main SPA asset tree (**LO**).

Note on naming: `frontend/src/v3/admin/AdminPage` — imported at [`App.js:53`](frontend/src/App.js:53) and mounted at [`/organization`](frontend/src/App.js:2161) — is the **customer organisation admin** (Facilities, Locations, Vehicles, Suppliers, Members, Custom Factors, Activity, Audit, Profile, Security), i.e. **D17 master data**, not the internal staff control plane. It must not be mistaken for the legacy `/admin` or for `/ops` (**DC**).

---

## F. Legacy `/admin` evidence

- Separate CRA at [`admin/`](admin/package.json:4) with `homepage: "/admin"`; routes are `/admin/*` and `/admin/login`, plus a legacy `/staff-dashboard` ([`admin/src/App.js`](admin/src/App.js:64)) (**DC**).
- Separate auth: [`admin/src/context/AuthContext.js`](admin/src/context/AuthContext.js:22) queries `staff_profiles` directly through PostgREST and fails closed without a client (**DC**).
- Separate API path: legacy screens use `/api/admin/*` and, post-FINAL-03, an admin-gated backend helper [`adminApi.js`](admin/src/services/adminApi.js:17) with the operator's bearer token (**DC**).
- Deployed as a **distinct asset tree** (`/admin/static/js/main.53ab5f56.js`) containing the H2 configuration notice (**LO**).
- **DD:** DEPRECATED per D-P2-02, quarantined, retained until the §4 retirement conditions are met (currently **not** met).

---

## G. Deployment topology (reconstructed)

**One Vercel project serves both surfaces** (**IN**, from **DC** + **LO**):

1. Root build ([`package.json`](package.json:6)) builds `frontend` → output root, and `admin` → `public/admin/`.
2. Root [`vercel.json`](vercel.json:14) rewrites `/admin/*` and `/admin` to `/admin/index.html`, and everything else to `/index.html` (**DC**). `frontend/vercel.json` contains only the catch-all and cannot serve `/admin` (**DC**).
3. Live behaviour matches exactly: `/admin*` → 656-byte legacy shell; all other paths → 2272-byte SPA shell (**LO**).
4. Environment: the admin build environment provides `REACT_APP_API_URL` (inlined `carbontally-api.onrender.com`) but **not** `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY` (**LO**, §C.3).
5. The documented alternate hosts are **not** the served surfaces: the two `*.vercel.app` aliases are not the production entries and `admin.carbontally.co.uk` did not resolve at the time of the acceptance run (**LO**, predecessor report). The **real** production entry is `carbontally.co.uk` with `/admin` as the legacy path.

There is **no** evidence of a second, separately deployed admin project in the repository (**DC**): the repository's only assembly path merges both CRAs into one output.

---

## H. BLK-1 assessment (BLK-1-A … BLK-1-E)

The five mandated sub-questions are answered individually. The BLK-1 statement under test is the one recorded in the predecessor acceptance report (`CSTR-FINAL03-LIVE-ACCEPTANCE-001`, §23): *"The production admin console cannot start … built without `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY` … the documented admin host does not resolve."*

**BLK-1-A — Does production routing send internal staff to `/ops` (canonical) rather than `/admin`?**
**YES — CONFIRMED.** Server resolver returns `destination: "/ops"` for `actor_type == "staff"` ([`me_context`](backend/api/v3_context.py:34)); the route is guarded by `requireInternalStaff` ([`App.js:2188`](frontend/src/App.js:2188)); login routes via the server-authoritative destination. Zero `/admin` references in `frontend/src` route code. (**DC**)

**BLK-1-B — Is `/admin` a retained legacy surface rather than the canonical staff app?**
**YES — CONFIRMED.** D-P2-02 ratifies `/ops` as canonical and `/admin` as **DEPRECATED, not deleted**, quarantined and served only by the deployment rewrite ([`CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md:80`](docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md:80)); the retirement conditions are unmet. (**DD**)

**BLK-1-C — Is the deployed `/admin` failure a defect in the canonical staff surface, or a configuration gap on the legacy surface?**
**A configuration gap on the *legacy* surface.** The canonical `/ops` surface is deployed and reachable (200). The `/admin` failure is caused by the absence of two **build-time** settings; the live admin bundle inlines **no** Supabase URL while the main bundle inlines its hard-coded fallback (§C.3). The failure mode is the deliberate H2 controlled notice (**DD** §C.1), reached legitimately. Root cause (**IN**): the admin's build environment lacks `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY`; this went unnoticed because the main app has a hard-coded fallback (**DD** §19.1). **BLK-1 is therefore PARTIALLY CONFIRMED: the fact (legacy admin non-functional) is true; the framing (a broken *admin surface* / canonical regression) is not.**

**BLK-1-D — What is the intended deployment topology?**
**One Vercel project serving the main SPA at `/` and the quarantined legacy admin CRA at `/admin`**, via the root build + root `vercel.json` rewrites (§G). The documented alternate hosts are documentation drift, not the served topology. (**DC** + **LO**)

**BLK-1-E — Is authorization server-enforced for both surfaces, and are the redirects internally consistent (no conflicting `/admin` redirects)?**
**YES — CONFIRMED, with one caveat.**
- Server enforcement: the V3 path delegates to `ensure_staff_permission` ([`operations_auth.py`](backend/api/operations_auth.py:95)); the legacy path post-FINAL-03 goes through an admin-gated backend API with a bearer token ([`adminApi.js`](admin/src/services/adminApi.js:17)). Neither relies on the UI as a boundary (**DD** §7/§44). (**DC**)
- Redirect consistency: no non-test code in `frontend/src` redirects to `/admin`; the SPA catch-all sends unknown paths to `/` ([`App.js:2269`](frontend/src/App.js:2269)); `/dashboard/*` → `/home` ([`App.js:1985`](frontend/src/App.js:1985)). No conflict. (**DC**)
- Caveat (**NT**): the legacy admin's `AuthContext` performs a **direct PostgREST** read of `staff_profiles` ([`AuthContext.js:125`](admin/src/context/AuthContext.js:125)). With the admin build unconfigured, this path is inert; whether it would resolve under the FINAL-03 RLS posture with a configured client **cannot be confirmed without an authenticated session** — recorded as **NT** for a future authenticated pass, **not** asserted as a defect.

**BLK-1 consolidated verdict:** the *symptom* is real; the *canonical staff surface is not affected*; the impact is confined to the **legacy, DEPRECATED** surface and to the legacy-only capabilities that still live there (see §I).

---

## I. Legacy capability matrix (legacy `/admin` vs V3 `/ops`)

Derived from the ratified inventory ([`CARBONTALLY_LEGACY_ADMIN_INVENTORY.md:19`](docs/architecture/CARBONTALLY_LEGACY_ADMIN_INVENTORY.md:19), **DD**) plus the current inventories (**DC**):

| Capability | Legacy `/admin` page | V3 `/ops` counterpart | Coverage | Affected by BLK-1? |
|---|---|---|---|---|
| Staff roster / roles | `Users.js`, `ReviewAssignment.js` | `StaffRoster.jsx`, `StaffRolesTab.jsx` | ✅ FULL | **No** (V3) |
| Review queue / workflow | `Reviews.js`, `ManualReviewQueue.js`, `StaffReviewQueue.jsx` | `ReviewQueue.jsx`, `ReviewItemPage.jsx` | ✅ FULL | **No** (V3) |
| Assignments | `AdminAssignment.jsx` | `OpsAssignmentsTab.jsx` | ✅ FULL | **No** (V3) |
| Extraction / mapping / QC | `ExtractionErrorReview.js` | `OperatorQueue.jsx`, `CtQcTab.jsx`, `ExtractionPanel.jsx` | ✅ FULL | **No** (V3) |
| Audit console | `LogViewer.jsx` | `AuditConsoleTab.jsx` | ✅ FULL | **No** (V3) |
| Dashboard / analytics | `Dashboard.js`, `Analytics.js`, `LiveQueueStats.jsx` | `OpsDashboard.jsx`, `OperationalHealthTab.jsx`, `SlaTab.jsx` | 🟡 PARTIAL | Partial (V3 core covered) |
| Workload | `WorkHub.jsx`, `StaffOnlinePresence.jsx` | `OpsDashboard.jsx` reporting | 🟡 PARTIAL | Partial |
| Settings / retention | `Settings.js` | `SettingsTab.jsx` (retention + **GA4**) | 🟡 PARTIAL | Partial (V3 canonical) |
| DEFRA factors | `DefraFactors.js` | factors read + provider/import surface | 🟡 PARTIAL | Partial |
| Document types | `Batches.js`, `GlossaryManagement.js` | `document_type_categories` (read) | 🟡 PARTIAL | Partial |
| **Bulk operations** | (bulk) | — | ❌ NONE | **Yes — legacy-only** |
| **Beta management** | `BetaManagement.js` | — | ❌ NONE | **Yes — legacy-only** |
| **Email templates / logs** | (templates/logs) | — | ❌ NONE | **Yes — legacy-only** |
| **Internal document-type CRUD** | (document-types) | — | ❌ NONE | **Yes — legacy-only** |

**Consequence (IN):** BLK-1's practical impact is the **❌ NONE** rows — internal-only operator tooling that today exists **only** on the legacy surface. Those operators have **no** V3 fallback, so a non-functional legacy `/admin` removes those capabilities. This is the material operational consequence and it is a **PO DECISION** (§K), because D-P2-02 explicitly retains legacy admin for exactly these rows.

---

## J. Changes

> **NO FILES / CODE / DATABASE / DEPLOYMENT / CONFIGURATION WERE MODIFIED.**

This investigation read repository source, read ratified documents, performed unauthenticated HTTP GET requests, and downloaded two public JavaScript bundles to `/tmp` for local static analysis. No file in the repository was created, edited or deleted by this investigation except this report. No environment variable, secret, DNS record, Vercel project, Render service, Supabase object, grant, policy, migration or table was read with credentials or modified. No credential was used; no authenticated session was created. No bundle, artefact or configuration was written into the repository.

---

## K. Next action

**Exactly one** recommended next action (not implemented):

> **PO DECISION REQUIRED — settle the disposition of the retained legacy `/admin` surface for the FINAL-03 release, by choosing one of two mutually exclusive options:**
>
> **(1) Provision the legacy admin build settings** — set `REACT_APP_SUPABASE_URL` and `REACT_APP_SUPABASE_ANON_KEY` in the admin build environment and redeploy, restoring the legacy `/admin` console and the four ❌-NONE legacy-only capabilities (bulk, beta, email templates/logs, document-type CRUD); **or**
> **(2) Formally retire the legacy surface** — execute the `CARBONTALLY_LEGACY_ADMIN_INVENTORY.md` §4 retirement conditions (ship a V3 twin for each ❌-NONE row or record a written decision to drop the capability, remove the `/admin` rewrite from `vercel.json`, and purge `/api/admin/*` references), which removes BLK-1 by removing the surface.

Option **(1)** is the lower-risk, lower-effort path and is consistent with D-P2-02's "deprecated, not deleted" posture; option **(2)** is the architecturally clean end state but requires V3 replacements that do not yet exist. Both are Product-Owner decisions because they change retained capability and, in (2), a ratified deprecation plan.

Only after that decision should any authenticated re-acceptance run (closing BLK-2 and the **NT** items in §H) be scheduled with PO-authorised disposable identities.

---

**READY FOR PO REVIEW — NO REMEDIATION PERFORMED**

**Boundary:** this investigation is read-only. The final verdict, the refinement of BLK-1, and the disposition decision belong to the Product Owner.
