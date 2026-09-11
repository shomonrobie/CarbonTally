# CarbonTally — Production Authentication & Access Specification (2026-09-11)

**Status:** verified against the repository at publication commit `5a1e45e0203b822b3a488a6004b904ef40abb059`.
**Scope:** how every supported entity authenticates, where it lands, what authorises it, and how failures are
presented. Evidence is drawn from `frontend/src/App.js`, `frontend/src/Login.js`,
`frontend/src/AuthCallback.js`, `frontend/src/v3/api.js`, `frontend/src/lib/authErrors.js`,
`frontend/src/AuthServiceUnavailable.jsx`, `backend/api/v3_context.py`, `backend/auth.py`,
`supabase/migrations/**` (RLS), and the architecture blueprint.

---

## 1. Authentication methods actually implemented

| Method | Implemented? | Where | Notes |
|---|---|---|---|
| Email + password | **YES** | `Login.js` → `supabase.auth.signInWithPassword` | Sign-up also present (`signUp`, with company name) |
| Google OAuth | **YES** | `Login.js` → `supabase.auth.signInWithOAuth({ provider: 'google' })` | Redirect target `REACT_APP_OAUTH_REDIRECT_URL` or `${origin}/auth/callback` |
| Magic link | **Partially** | Route `/auth/magic` (`MagicLink.jsx`), then server-authoritative landing | Present as a route; not documented as a supported production sign-in method |
| Invitation / activation | **Not established** | No invitation route or flow found in the frontend route table | Do not assume one exists |
| Password reset | **Not established** | No `/reset` or recovery route in the route table | Do not assume one exists |
| Email verification | **Supabase-side** | `Login.js` handles the *"Email not confirmed"* outcome and instructs the user to confirm | The confirmation email itself is Supabase Auth |
| Session handling | **YES** | Supabase JS session in `localStorage` (see `PrivacyPolicy.jsx` §12); `ProtectedRoute` + `onAuthStateChange` | Session restored on load |
| Logout | **YES** | `supabase.auth.signOut()` in the app shell | Clears session state |

**No authentication method has been added by this closure.** Two methods exist and both are unchanged.

## 2. Entity / access matrix

The **post-login destination is decided server-side** by `GET /api/v3/me/context`
(`backend/api/v3_context.py`), not by frontend role logic. The frontend merely navigates to that
`destination`. Authorisation is then enforced again on every API call and by RLS.

| # | Entity | Authentication method | Login entry | Role / capability | Allowed platform area | Backend authorization | RLS boundary | Expected redirect | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Organisation** (tenant) | n/a — not a login identity; the tenant of its members | — | — | — | Every org-scoped API call requires a verified membership | `organization_id`-scoped policies | — | N/A (tenant, not an actor) |
| 2 | **Organisation users / members** (Owner, Admin, Member, Viewer) | Email+password **or** Google OAuth | `/login` | Org roles via `organization_members`; capability checks server-side | Customer workspace (`/home`, `/emissions`, `/documents`, `/processing`, `/review`, `/reports`, `/billing`, `/organization`, `/messaging`, `/issues`, `/notifications`) | `backend/auth.py` + org membership/role resolution | Org-scoped RLS | **`/home`** (`primary_workspace: "customer"`) | **CAN LOGIN** |
| 3 | **Consultant** (and consultant team member) | Email+password **or** Google OAuth | `/login` | Consultant capability set (consultant workflow, P6) | Consultant workspace (`/consultant`, `/consultant/items/:clientId/:itemId`) | Consultant membership + engagement checks | Consultant/client-scoped RLS | **`/consultant`** | **CAN LOGIN** |
| 4 | **Consultant firm** | n/a — organisational grouping of consultants (the firm is represented through its members' consultant/firm provenance), not a separate login | — | — | — | Consultant firm provenance recorded per action (P6-2D) | Consultant-scoped | — | N/A (grouping, not an actor) |
| 5 | **Processing Entity** (PE Manager, PE Staff/Operator) | Email+password **or** Google OAuth | `/login` | PE roles; PE work assignment scope | PE workspace (`/pe`, `/pe/assignments`, `/pe/messages`, `/pe/items/:entityId/:itemId`) | PE identity + assignment authorisation (PE boundary enforced server-side) | PE-assignment-scoped RLS; PE document boundary preserved | **`/pe`** | **CAN LOGIN** |
| 6 | **CarbonTally Internal / staff** (Operator, Reviewer, QC, Staff Admin, System Admin) | Email+password **or** Google OAuth | `/login` | `staff_roles.permissions` — `can_process`, `can_review`, `can_manage_staff`, `can_manage_billing`, `can_view_all` (never name-string matching) | Internal operations (`/ops`, `/ops/items/:itemId`, `/ops/review/:itemId`, `/ops/qc/:itemId`) — the canonical staff application per CL-66 | `ensure_staff_permission` | Staff-scoped; internal data not exposed to tenants | **`/ops`** | **CAN LOGIN** |
| 7 | **System / worker identities** | Service credentials (backend only) | n/a | Automation/worker processing | Not a browser surface | Service-role/server-side only | Server-side; never exposed to the browser | n/a | N/A (non-interactive) |
| 8 | **Unprovisioned / no-workspace account** | Email+password **or** Google OAuth | `/login` | None yet | Onboarding only | Context resolver returns onboarding | n/a | **`/onboarding`** | **CAN LOGIN (no workspace yet)** |

**Summary counts:** CAN LOGIN = entities 2, 3, 5, 6 (+ 8 as a not-yet-provisioned state). Entities 1, 4, 7
are **not** browser login identities by design. **LOGIN PATH UNCLEAR:** none — each actor's entry point is
explicit. **LOGIN IMPLEMENTED BUT NOT PRODUCTION-VERIFIED:** all interactive logins, because production
verification requires either a real OAuth account or an authorised test identity (not used here).

## 3. Route inventory (`frontend/src/App.js`, single `BrowserRouter`)

| Category | Routes |
|---|---|
| Public (no session required) | `/` (LandingPage), `/about`, `/platform`, `/services`, `/processing-services`, `/consultants`, `/pricing`, `/contact`, `/faq`, `/glossary`, `/carbon-reduction-plan`, **`/privacy`**, **`/terms`**, **`/cookies`**, **`/data-security`**, **`/login`**, `/beta-login`, `/signup`, `/beta/signup`, `/auth/callback`, `/auth/magic`, `/onboarding` |
| Authenticated + `ProtectedRoute` | `/home`, `/emissions`, `/documents`, `/processing`, `/processing/:itemId`, `/review`, `/review/:itemId`, `/existing-data`, `/messaging`, `/issues`, `/notifications`, `/reports`, `/reports/:id`, `/billing`, `/organization`, `/consultant`, `/consultant/items/:clientId/:itemId`, `/ops`, `/ops/items/:itemId`, `/ops/review/:itemId`, `/ops/qc/:itemId`, `/pe`, `/pe/assignments`, `/pe/messages`, `/pe/items/:entityId/:itemId` |
| Legacy redirect | `/dashboard/*` → `/home` |
| Catch-all | `*` → `/` (redirect) |

**Required routes verified present:** `/login` ✓, `/privacy` ✓, `/terms` ✓, `/auth/callback` ✓,
`/auth/magic` ✓. **Not present (not invented):** a dedicated `/logout` route (logout is a client action), a
password-recovery route, and a dedicated `/unauthorized` or `/service-unavailable` route (the
unavailable-state renders **in place** — see §6).

### 3.1 Why the live URLs returned 404 (defect, now fixed)

* Live observation 2026-09-11: `https://carbontally.co.uk/` → **200** (the CRA shell, "You need to enable
  JavaScript to run this app."); `https://carbontally.co.uk/login` → **404 NOT_FOUND**;
  `https://carbontally.co.uk/privacy` → **404 NOT_FOUND**.
* The routes exist in code, so the failure was **static-serving/rewrite**, not React routing.
* Root `package.json` builds with
  `cd frontend && npm run build && cd ../admin && npm run build && mkdir -p public/admin && cp -r frontend/build/* public/ && cp -r admin/build/* public/admin/`,
  i.e. the deployed output has the app shell at **`/index.html`** and assets at **`/static/…`** — with no
  `/frontend/` prefix.
* The committed `vercel.json` instead rewrote `/(.*)` → **`/frontend/index.html`** and `/static/(.*)` →
  **`/frontend/static/$1`**. `/` was served because a static file exists for it; every deep link had no
  static match, hit the catch-all rewrite, and was sent to a **non-existent destination** → 404.
* **Fix applied (this closure):** rewrite destinations corrected to `/index.html` and `/static/$1` (2-line
  change; `/admin/*` rules unchanged).

## 4. Authorisation layers (defence in depth — none may be weakened)

1. **Authentication** — Supabase Auth issues the session (JWT).
2. **Route guard (UX only)** — `ProtectedRoute` (`App.js`) checks `supabase.auth.getSession()` and
   subscribes to `onAuthStateChange`; it prevents accidental access but is **not** a security boundary.
3. **Server-authoritative context** — `GET /api/v3/me/context` decides the actor's workspace and is the only
   source for post-login navigation (fail-closed).
4. **Backend authorisation** — `backend/auth.py`, `ensure_staff_permission`, and PE/consultant/org
   membership checks on every business endpoint.
5. **RLS** — organisation-, consultant/client-, PE- and staff-scoped row-level security in
   `supabase/migrations/**`; the frontend is never the security boundary (Blueprint §2.5).

## 5. Redirect behaviour

| Situation | Behaviour |
|---|---|
| Valid session at `/login` | Immediately resolved via `goToWorkspace()` → server destination |
| Successful password sign-in / sign-up | `goToWorkspace()` → server destination, `replace: true` |
| Successful Google OAuth | Google → `/auth/callback` → `goToWorkspace()` → server destination |
| Workspace resolution failure | **Throws** → controlled error state on the page; **never** silently routed to `/onboarding`, **never** looped |
| No workspace yet | Server returns `destination: /onboarding` |
| `/dashboard/*` (legacy) | Redirect to `/home` |
| Unknown path | Redirect to `/` |

## 6. Error behaviour (explicitly distinguished)

Classification is implemented in `frontend/src/lib/authErrors.js` and rendered by
`frontend/src/AuthServiceUnavailable.jsx`:

| Class | Meaning | Presented as |
|---|---|---|
| **AUTH SERVICE UNAVAILABLE** | Auth/infrastructure unreachable, timeout, OAuth initiation/callback failure, session-restoration failure, configuration failure | Branded notice: *"CarbonTally sign-in is temporarily unavailable"*, with **Try again**, and the explicit statement that the account/data have **not** been deleted |
| **INVALID CREDENTIALS** | Auth service reachable and it rejected the credential | Specific credential message (existing behaviour preserved) |
| **UNAUTHORIZED** | No/expired session | Normal sign-in/redirect behaviour |
| **FORBIDDEN** | Authenticated but not permitted (e.g. not a member, wrong workspace) | **Never** shown as an outage; the authorisation denial stands |
| **UNKNOWN APPLICATION ERROR** | Anything else | Generic error; must not be relabelled as an outage |

Raw Supabase error strings and the raw Supabase hostname are **not** used as the primary customer-facing
identity or message.

## 7. Google OAuth configuration findings

| Question | Finding |
|---|---|
| What does the user currently see? | Google's consent screen naming `pvwiojoyaqywtydzcpbg.supabase.co` |
| Why? | Supabase Auth **brokers** the Google OAuth exchange on its own project domain; the consent screen reflects that host |
| Can the repository change it? | **NO** — the consent UI text/host is controlled by Google plus the OAuth app/domain configuration, not by frontend code |
| What does CarbonTally control in-repo? | Its own **branding on `/login`** (CarbonTally name, Google button, legal links) and the callback path `/auth/callback` |
| Supported mechanism to improve it | (a) Google Cloud OAuth consent screen: **App name = "CarbonTally"**, authorised domain `carbontally.co.uk`, privacy/terms URLs, support email; (b) Supabase: correct **Site URL** + redirect allow-list; (c) optionally a **Supabase custom domain** (paid add-on, e.g. `auth.carbontally.co.uk`), which replaces the `<ref>.supabase.co` host in the brokered flow |
| Honest limitation | The exact phrase *"You're signing back in to CarbonTally.co.uk"* **cannot be forced** by CarbonTally code — it is Google-controlled wording. Even with a Supabase custom domain, the host shown would be that custom domain, not literally `carbontally.co.uk` |

## 8. Supabase / privacy / terms requirements

* **Supabase Auth settings required (external):** Site URL `https://carbontally.co.uk`; redirect allow-list
  including `https://carbontally.co.uk/auth/callback`; Google provider enabled; production email settings if
  email confirmation/reset is used.
* **`/privacy`:** exists, becomes publicly reachable once the `vercel.json` fix is deployed, and is
  substantive and CarbonTally-specific. It now states explicitly: who we are; what is collected;
  **authentication and account data**; **Google sign-in** (no Google password reaches CarbonTally; Google's
  own policy applies); **Supabase as authentication/data processor**; cookies & session technologies; your
  rights; contact (`hello@carbontally.co.uk` — an existing address, not invented); and a **last-updated
  date**.
* **`/terms`:** a Terms page already exists at `/terms` (`TermsPage.jsx`, pre-launch terms). If Google
  verification requires a terms URL, use `https://carbontally.co.uk/terms`.
* **No legal entity, address, DPO or policy commitment has been invented.**

## 9. Client configuration observation (reported, not changed)

`frontend/src/supabaseClient.js` contains a **fallback** production Supabase URL and a `sb_publishable_…`
**client publishable (public) key**, used when `REACT_APP_SUPABASE_*` env vars are unset. A publishable/anon
key is *designed* to be public and is not a service-role secret; nevertheless, defaulting a production build
to hardcoded values means the project ref/key are committed and a misconfigured deployment still reaches
production. **Not changed by this closure** (changing it could break production sign-in if the Vercel env
vars are absent). Recommendation: move to environment configuration in a separately authorised change.

## 10. Security invariants (must remain true)

1. The frontend is never the security boundary; every sensitive operation is authorised server-side.
2. Post-login routing is server-derived; a client cannot choose its workspace.
3. A resolution failure fails **closed** (controlled error), never into a broader area.
4. Authorization/forbidden outcomes are never presented as (or hidden behind) a service outage.
5. An auth outage never implies data loss and never grants or widens access.
6. RLS and tenant/consultant/PE isolation are unchanged by this closure.
7. No authentication method has been added, removed, or weakened.

## 11. Deep-link / refresh routing (corrected 2026-09-11)

**Requirement:** every route in the client route table (`/login`, `/privacy`, `/terms`, `/cookies`,
`/auth/callback`, `/signup`, `/beta/signup`, `/platform`, `/pricing`, … and the authenticated workspaces) must
render on a **cold load and on browser refresh**, not only via client-side navigation.

| Aspect | Finding |
|---|---|
| Mechanism | Vercel serves the built shell for unmatched paths and React Router renders the route. The file-system layer is evaluated **before** the rewrites layer, so real assets are never shadowed. |
| Where the shell lives | `public/index.html` — the root `build` script copies `frontend/build/*` into the output root; assets are absolute (`/static/…`), so the shell loads correctly at any depth. |
| Defect (found 2026-09-11) | `vercel.json` carried **`cleanUrls: true`** while every rewrite destination was an `…/index.html` path. `cleanUrls` removes the `.html` extension from HTML routes (and 308-redirects `.html` requests), so those destinations no longer resolved: **every deep link returned Vercel `404: NOT_FOUND` on refresh**, while `/` continued to work. |
| Live evidence | `/` 200 · `/static/js/main.*.js` 200 · `/admin` 200 (file-system directory index) · `/login`, `/privacy`, `/terms`, `/admin/deep-path` 404 `NOT_FOUND` · `/index.html` 308 → `/` · `/admin/index.html` 308 → `/admin` · `/zzz.html` 308 → `/zzz` |
| Fix | `vercel.json`: **`cleanUrls` set explicitly to `false`**; canonical catch-all `/(.*)` → `/index.html`, kept last, behind the `/static/**` and `/admin/**` shields. |
| Regression guard | `qa_harness/tests/harness/test_deployment_routing_config.py` (7 read-only tests) |
| Operational impact while broken | Google sign-in could not complete — `/auth/callback`, the OAuth return URL, was also 404, so the flow ended on a Vercel error page. |

**Invariant to preserve:** a rewrite destination ending in `.html` requires `cleanUrls` to be disabled.
Enabling `cleanUrls` without converting every destination is a **production deep-link outage**.

