# CarbonTally — Production Login Runbook (2026-09-11)

**Scope:** how every supported actor signs in, what they should see, how to troubleshoot, and what must be
configured outside the repository. Verified against publication commit
`5a1e45e0203b822b3a488a6004b904ef40abb059`. Only capabilities established by repository evidence are
described; nothing is invented.

## 1. Sign-in entry point

**All interactive actors sign in at `https://carbontally.co.uk/login`.** There is one login page
(`frontend/src/Login.js`) for customers, consultants, Processing Entity users and CarbonTally staff; the
**workspace they land in is decided server-side** after authentication.

## 2. How each actor logs in

| Actor | Steps |
|---|---|
| **Organisation user / member** (Owner, Admin, Member, Viewer) | Open `/login` → email+password **or** *Continue with Google* → the app calls `GET /api/v3/me/context` → lands on **`/home`** (customer workspace) |
| **Consultant** (and consultant team member) | Same `/login` flow → context resolves the consultant workspace → lands on **`/consultant`** |
| **Processing Entity** (PE Manager, PE Staff) | Same `/login` flow → lands on **`/pe`** |
| **CarbonTally internal staff** (Operator, Reviewer, QC, Staff Admin, System Admin) | Same `/login` flow → lands on **`/ops`** (canonical staff application per CL-66) |
| **Account authenticated but not provisioned** | Same `/login` flow → context returns onboarding → **`/onboarding`** |
| **Non-actor identities** (organisation as a tenant, consultant firm as a grouping, service/worker identities) | **No browser login** — they are not interactive identities |

## 3. Google sign-in flow

1. User selects *Continue with Google* on `/login`.
2. `supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo } })` where `redirectTo` is
   `REACT_APP_OAUTH_REDIRECT_URL` when set, otherwise `${window.location.origin}/auth/callback`.
3. Supabase Auth brokers the exchange with Google, so **Google's consent screen reflects the Supabase project
   host** (`<project-ref>.supabase.co`), not `carbontally.co.uk`.
4. Google redirects back to `/auth/callback` (`frontend/src/AuthCallback.js`), which reads the session (with
   one retry) and calls `goToWorkspace()` → server destination.
5. Callback failure of an **infrastructure** nature shows the branded unavailable notice instead of a raw
   error; other failures retain existing behaviour.

## 4. Password flow

* Sign-in: `supabase.auth.signInWithPassword({ email, password })` ⇒ workspace via context.
* Sign-up: `supabase.auth.signUp(...)` with company name (self-service and beta signup routes exist).
* Email confirmation: when Supabase returns *"Email not confirmed"*, the login page instructs the user to
  confirm via the emailed link.
* Credential rejections show specific messages; they are **never** shown as outages.

## 5. Session, logout, recovery

| Action | Behaviour |
|---|---|
| Session persistence | Supabase JS session stored in browser `localStorage`; restored on load |
| Session expiry | Treated as signed-out; `ProtectedRoute` returns the user to the normal sign-in path |
| Logout | `supabase.auth.signOut()` from the app shell (client action; no `/logout` route exists) |
| Password reset / recovery | **Not established** — no recovery route exists. Until a recovery flow is authorised, resets are administrator-driven |
| Invitation / activation | **Not established** — no invitation/activation route exists; provisioned accounts sign in directly |

## 6. Failure-mode behaviour (customer-facing)

| Situation | What the user sees |
|---|---|
| Supabase Auth/network unreachable, timeout, OAuth initiation or callback failure, session-restoration failure, auth misconfiguration | Branded **"CarbonTally sign-in is temporarily unavailable"** with *Try again*, and the statement that the account/data have **not** been deleted |
| Wrong password / unknown account | Invalid-credentials message (specific, non-technical) |
| Not permitted (signed in but no membership) | Authorisation outcome — **never** presented as an outage |
| Unexpected error | Generic error message |

## 7. Troubleshooting

### 7.1 `/login` (or `/privacy`, `/terms`, `/auth/callback`, or any deep link) returns 404 on refresh

**Symptom:** the page renders when reached by clicking from the home page (client-side navigation), but a
**browser refresh** — or any direct/cold load — returns Vercel `404: NOT_FOUND`.

* **Diagnosis (corrected 2026-09-11; the earlier "wrong destination path" explanation is superseded):**
  the deployment does serve the corrected `vercel.json` (verified live: the deployed bundle contains the
  latest frontend code and `asset-manifest.json` was `last-modified 13:49:53 GMT`, after the fix commit) —
  but it set **`cleanUrls: true`**. `cleanUrls` removes the `.html` extension from every HTML file's route and
  308-redirects requests that use the extension (observed live: `/index.html` → 308 `/`,
  `/admin/index.html` → 308 `/admin`, `/zzz.html` → 308 `/zzz`). The shell therefore exists at `/`,
  **not** `/index.html`, so **every SPA rewrite whose destination was an `…/index.html` path stopped
  resolving and fell through to a hard 404** — including the trivially correct
  `/admin/(.*)` → `/admin/index.html` rule (observed live: `/admin/deep-not-a-real-path` → 404).
  `/` kept working only because the file-system layer is evaluated **before** the rewrites layer.
* **Fix (applied):** `vercel.json` sets **`cleanUrls` explicitly to `false`** (an explicit value also
  overrides any equivalent Vercel **Project Setting**) and keeps the canonical `/(.*)` → `/index.html`
  catch-all behind the `/static/**` and `/admin/**` shields — the same pattern already used by
  `frontend/vercel.json` and the pre-V3 backup config.
  Regression guard: `qa_harness/tests/harness/test_deployment_routing_config.py`.
* **Verify after the next production deployment** — every path must return **200**, and a **browser refresh**
  on each must render the page rather than a 404:

  ```bash
  for p in / /login /privacy /terms /auth/callback /platform /pricing /admin; do
    printf '%s  %s\n' "$(curl -sS -o /dev/null -w '%{http_code}' "https://carbontally.co.uk$p")" "$p"
  done
  ```

  (`/auth/callback` matters most operationally: it is where Google sign-in returns, so while it 404s the whole
  OAuth flow ends on an error page.)

* **If deep links still 404 after a verified deployment of the corrected config**, the remaining suspects are
  (none changeable from the repository):
  1. the Vercel project's **Root Directory** must be the repository root and the **Output Directory** must be
     the build's `public/` (the linked project `.vercel/project.json` = `carbon-tally`; `/admin` already
     resolving proves the output root is correct);
  2. a Vercel **dashboard** Project Route, `cleanUrls` toggle, or deployment-protection rule overriding the
     file;
  3. `frontend/vercel.json` — **inert** while the Root Directory is the repository root, but it would become
     the effective configuration if the Root Directory were switched to `frontend/`.

### 7.2 Google sign-in fails or loops
1. Supabase → Authentication → Providers → Google enabled, with valid client ID/secret.
2. Supabase **Site URL** = `https://carbontally.co.uk`.
3. `https://carbontally.co.uk/auth/callback` present in the Supabase **Redirect URLs** allow-list.
4. Google Cloud OAuth client **Authorized redirect URIs** include
   `https://<project-ref>.supabase.co/auth/v1/callback`.
5. The app's `REACT_APP_OAUTH_REDIRECT_URL` (if set on Vercel) matches the deployed origin.

### 7.3 Consent screen shows the Supabase hostname
Expected while Supabase brokers OAuth. See the access spec §7 — only dashboard configuration (Google app
name/domain, and optionally a Supabase custom domain) changes the presentation; frontend code cannot.

### 7.4 "It used to work and now nobody can sign in"
Distinguish the two causes:
* **Route/serving failure** (404, blank page, "You need to enable JavaScript"): deployment/rewrite/Vercel —
  see 7.1. This is what the PO's `docs/Robie/getting this on live website.txt` note records: the observed
  error was a Vercel **`404: NOT_FOUND`** on the login path, reported at a time when the Supabase database
  server was also believed to be unavailable. The 404 is a **serving** symptom, not a Supabase database
  symptom.
* **Auth-service outage** (page loads, sign-in fails): the branded unavailable notice should appear; check
  Supabase status and API/backend health separately.

## 8. Required external (dashboard) configuration — not changeable from the repository

**Google Cloud (OAuth consent screen / client):** app name **CarbonTally**; authorised domain
`carbontally.co.uk`; privacy policy URL `https://carbontally.co.uk/privacy`; terms URL
`https://carbontally.co.uk/terms`; support email (the existing published contact); authorised redirect URI
`https://<project-ref>.supabase.co/auth/v1/callback`.

**Supabase (Authentication):** Site URL `https://carbontally.co.uk`; redirect allow-list
`https://carbontally.co.uk/auth/callback` (+ `https://carbontally.co.uk/**` if wildcards are permitted);
Google provider enabled; email templates/settings if confirmation/reset is used; optional **custom domain**
(paid) to replace the `<project-ref>.supabase.co` host in the brokered OAuth flow.

**Vercel:** production domain `carbontally.co.uk` bound to the correct project; deployment must use the
repository root `build` script and the output directory containing `index.html` (built as `public/`);
`vercel.json` must be the corrected version; environment variables `REACT_APP_SUPABASE_URL`,
`REACT_APP_SUPABASE_ANON_KEY` (optionally `REACT_APP_OAUTH_REDIRECT_URL`, `REACT_APP_API_URL`) set for
production.

**Render (backend):** service health and environment variables unchanged by this closure; the frontend's API
base is `REACT_APP_API_URL` or the documented production API origin.

**No dashboard configuration was changed by this closure.**

## 9. Verification steps after deploy

1. `GET /` → 200 (shell loads).
2. `GET /login` → 200, and **refresh** on `/login` → still 200 with the branded login page.
3. `GET /privacy` → 200, and refresh → 200 with substantive policy content.
4. `GET /terms` → 200.
5. Google sign-in completes and lands on the correct workspace for the actor.
6. With Supabase Auth unreachable, the branded unavailable notice appears (not a raw error).
7. A non-member cannot reach another actor's workspace by editing the URL.
