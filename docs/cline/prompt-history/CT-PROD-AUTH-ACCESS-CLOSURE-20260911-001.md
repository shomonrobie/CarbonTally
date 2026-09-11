# CT-PROD-AUTH-ACCESS-CLOSURE-20260911-001

**Prompt Ref:** `CT-PROD-AUTH-ACCESS-CLOSURE-20260911-001`
**Response Ref:** `CT-PROD-AUTH-ACCESS-CLOSURE-20260911-001-R1` · **Datetime:** 2026-09-11
**Starting commit:** `5a1e45e0203b822b3a488a6004b904ef40abb059` · **Starting remote:** `origin/main` = same
(having been verified against GitHub)
**Mode:** bounded production access/authentication closure. No Phase 7/8 work; no migration created or applied;
no production Supabase contact; no Google/Vercel/Render dashboard change; no deployment.

## 1. Exact prompt (faithful summary)

Establish a reliable production access/authentication baseline after the verified publication of
`5a1e45e`: document everything intentionally changed since the previous publication; build the
authentication/access model for all supported entities; diagnose the live `/login` and `/privacy` 404s, the
Google OAuth hostname presentation, and the reported auth outage; fix the privacy-policy accessibility and
content problem; implement a CarbonTally-branded service-unavailable experience; verify routing/access
controls; and produce durable documentation (changelog, auth/access spec, login runbook, prompt history).

## 2. Files inspected

`vercel.json`; root `package.json`; `frontend/package.json`; `frontend/src/App.js` (route table 1996–2259;
`ProtectedRoute` at 187); `frontend/src/Login.js`; `frontend/src/AuthCallback.js`;
`frontend/src/supabaseClient.js`; `frontend/src/v3/api.js` (`getMeContext`, `resolvePostLoginPath`,
`goToWorkspace`); `frontend/src/PrivacyPolicy.jsx`; `frontend/src/TermsPage.jsx`;
`frontend/src/public/PageShell.jsx` (present); `frontend/src/components/AppFooter.jsx`;
`backend/api/v3_context.py` (`primary_workspace`/`destination`);
`docs/legal/draft/CARBONTALLY_PRIVACY_POLICY_DRAFT.md`, `…TERMS_OF_SERVICE_DRAFT.md`;
`docs/architecture/CARBONTALLY_ADMIN_CONTROL_PLANE_DECISION.md`; the publication reports
(`CT-PROD-PUBLICATION-*`, `CT-PHASE6-PUSH-AUDIT-*`); `docs/Robie/getting this on live website.txt`.

## 3. Diagnosis (evidence-based)

| # | Symptom | Root cause | Evidence |
|---|---|---|---|
| D1 | `/login` returns **404 NOT_FOUND** | `vercel.json` SPA catch-all rewrote `/(.*)` → **`/frontend/index.html`** (and `/static/(.*)` → `/frontend/static/$1`). The build copies `frontend/build/*` into `public/`, so the deployed shell is **`/index.html`** and assets are **`/static/…`** — the rewrite destination **does not exist**, so every deep link 404s while `/` (a static file) works | Live: `/` = **200**, `/login` = **404**, `/privacy` = **404**; root `package.json` build script; committed `vercel.json`; `/login` **is defined** in `App.js:2001` |
| D2 | `/privacy` returns **404**; Google reports "unresponsive"/"insufficient content" | **Same serving defect** (D1). The page exists (`PrivacyPolicy.jsx`, substantive, via `PageShell`) — Google could not reach it | Live fetch of `/privacy` = 404; `PrivacyPolicy.jsx`; `App.js:2002` |
| D3 | Google consent screen shows `pvwiojoyaqywtydzcpbg.supabase.co` | Supabase Auth **brokers** the Google OAuth exchange on its own project domain; the consent UI reflects that host. Google-controlled wording/host cannot be changed by frontend code | `Login.js` → `signInWithOAuth({provider:'google'})`; Supabase brokering model; no custom domain configured in-repo |
| D4 | Reported "login failed because supabase db server was not working" | The observed artefact was a **Vercel `404: NOT_FOUND`** on the login path → a **serving/route** failure (D1), not a Supabase database failure. Supabase **DB** availability and Supabase **Auth** availability are distinct and must not be conflated | `docs/Robie/getting this on live website.txt` (quotes the 404 + edge ID); live 404s; repo routing config |
| D5 | No branded outage experience | No auth-error classification or branded unavailable state existed; raw Supabase messages were surfaced | pre-change `Login.js` / `AuthCallback.js` |

**Cannot be reconstructed:** whether Supabase Auth was *simultaneously* unavailable during the reported
incident — no logs available locally. Recorded as unknown rather than assumed.

## 4. Change list (Phase 17) and changes made (Phase 18)

| ID | Priority | Change | Files |
|---|---|---|---|
| C1 | **P0** | Correct the SPA fallback/static rewrites so deep links and refreshes resolve | `vercel.json` |
| C2 | **P1** | Make `/privacy` explicitly cover authentication, Google sign-in, Supabase processing, cookies/session, rights; add last-updated date (additive; existing content preserved; no invented entity/DPO) | `frontend/src/PrivacyPolicy.jsx` |
| C3 | **P2** | Branded **AUTH SERVICE UNAVAILABLE** classification + experience, wired into password, OAuth and callback paths; authorisation outcomes never masked as outages | `frontend/src/lib/authErrors.js` (new), `frontend/src/AuthServiceUnavailable.jsx` (new), `frontend/src/Login.js`, `frontend/src/AuthCallback.js` |
| C4 | **P2** | Add Privacy/Terms links to the login page (Phase 9) | `frontend/src/Login.js` |
| C5 | **P3** | Documentation set | 3 new `docs/architecture/**` + this record |

**Files changed:** `vercel.json` (M) · `frontend/src/PrivacyPolicy.jsx` (M) · `frontend/src/Login.js` (M) ·
`frontend/src/AuthCallback.js` (M) · `frontend/src/AuthServiceUnavailable.jsx` (**new**) ·
`frontend/src/lib/authErrors.js` (**new**) ·
`docs/architecture/CARBONTALLY_POST_PUBLICATION_CHANGELOG_20260911.md` (**new**) ·
`docs/architecture/CARBONTALLY_PRODUCTION_AUTHENTICATION_ACCESS_SPEC_20260911.md` (**new**) ·
`docs/architecture/CARBONTALLY_PRODUCTION_LOGIN_RUNBOOK_20260911.md` (**new**) · this record (**new**).

**Deliberately NOT done:** no authentication method added/removed; no route redesign; no schema or migration;
no change to RLS, billing, processing or consultant logic; `/demo` and `/investors` untouched; Phase 7/8 not
begun; no unrelated UI redesign.

## 5. Commands and tests

* **Read-only evidence:** `git log|status|rev-parse|ls-tree|show|diff|check-ignore`; `grep -rIn/-rIl` across
  `frontend/src` and `backend`; `sed`/`head`/`wc`; live URL fetches of `https://carbontally.co.uk/`, `/login`,
  `/privacy`.
* **Validation:** `python3 -c "json.load(open('vercel.json'))"` → **valid JSON**, 6 rewrites, destinations
  `/index.html` and `/static/$1`.
* **Tests run (the repo's own frontend build path):**
  * `CI=true npx --no-install react-scripts build` → exit **1**, caused by **105 pre-existing** lint warnings
    (`no-unused-vars`, `exhaustive-deps`) treated as errors under `CI=true`. The two `Login.js` warnings
    (`unused 'data'`) exist **identically in HEAD** (three `const { data, error }` patterns before and after)
    → **no new warnings introduced**.
  * `npx --no-install react-scripts build` (warnings non-fatal) → exit **0**:
    *"The build folder is ready to be deployed."* ⇒ **the application compiles successfully** with every change
    in this closure.
* **Tests NOT run / limitations:** no authenticated E2E or unit run against production (no authorised test
  identity used; real customer credentials were **not** used); Google OAuth end-to-end cannot be completed
  without a real external account; production re-verification is blocked until the corrected `vercel.json` is
  deployed.

## 6. Browser / public URL verification

| URL | Before (2026-09-11) | After this closure (pre-deploy) | Note |
|---|---|---|---|
| `https://carbontally.co.uk/` | 200 (SPA shell, 2,272 bytes) | unchanged 200 | static-file path |
| `https://carbontally.co.uk/login` | **404** | **still 404 until redeploy** — repository fix applied, not deployed | serving defect |
| `https://carbontally.co.uk/privacy` | **404** | **still 404 until redeploy** | same defect |

**A deploy is outside this operation's authority**, so production re-verification remains pending PO/Vercel
action.

## 7. External configuration findings (Phase 14 checklist — nothing was changed)

**Google Cloud:** OAuth consent screen app name should read **CarbonTally**; authorised domain
`carbontally.co.uk`; privacy URL `https://carbontally.co.uk/privacy`; terms URL
`https://carbontally.co.uk/terms`; support email = the published contact; OAuth client authorised redirect URI
`https://<project-ref>.supabase.co/auth/v1/callback`.
**Supabase:** Site URL `https://carbontally.co.uk`; redirect allow-list
`https://carbontally.co.uk/auth/callback`; Google provider enabled; optional **custom domain** (paid) to
replace the `<ref>.supabase.co` host in the brokered flow.
**Vercel:** confirm project and Output Directory match the root `build` script output (`public/`), bind
`carbontally.co.uk`, set `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY` (+ optional
`REACT_APP_OAUTH_REDIRECT_URL`, `REACT_APP_API_URL`), then redeploy.
**Render:** unchanged by this work. **No dashboard was touched.**

## 8. Entity access findings · service-unavailable implementation · incident root cause

* **Entity access:** documented in full in the auth/access spec §2 — one login page for all actors, with the
  **landing decided server-side** by `GET /api/v3/me/context` (`/home` customer, `/consultant`, `/pe`, `/ops`,
  `/onboarding`); identity, backend authorisation and RLS are unchanged and still enforced server-side.
* **Service-unavailable implementation:** `classifyAuthError()` distinguishes **AUTH SERVICE UNAVAILABLE** from
  **INVALID CREDENTIALS**, **UNAUTHORIZED**, **FORBIDDEN** and **UNKNOWN APPLICATION ERROR**;
  `AuthServiceUnavailable.jsx` renders the branded notice ("CarbonTally sign-in is temporarily unavailable",
  *Try again*, "your data has **not** been deleted") and is wired into session-restore, password, OAuth and
  callback paths. It discloses no raw Supabase text and never masks a security outcome.
* **Incident root cause:** the recorded production login failure was a **route/serving 404** (D1/D4), not a
  Supabase database outage; the DB ↔ Auth distinction is preserved.

## 9. Unresolved items and risks

| ID | Item | Risk if unresolved |
|---|---|---|
| R1 | Corrected `vercel.json` must be **deployed** for `/login` and `/privacy` to return 200 | The PO's reported 404s persist until redeploy |
| R2 | Google OAuth consent branding requires Google Cloud + Supabase dashboard configuration (optionally a paid Supabase custom domain) | The consent screen continues to show the Supabase hostname; the exact phrase cannot be forced from code |
| R3 | Google verification needs live `/privacy` (and possibly `/terms`) reachable | Verification remains pending |
| R4 | `supabaseClient.js` retains a hardcoded production URL + publishable-key fallback | Committed project ref/key; a misconfigured deploy still reaches production (recommend env-only config as a separate authorised change) |
| R5 | 105 pre-existing CI build warnings fail `CI=true` builds | A future CI workflow (deliberately unpublished) would fail; **not** a regression of this closure |
| R6 | No password-recovery or invitation flow exists | Users depend on administrator-driven resets |
| R7 | Production E2E/login verification not performed | Interactive login remains **implemented but not production-verified** |

## 10. STOP conditions encountered

None triggered: no migration or schema change was required; no production DB modification; no Google/Supabase
privileged credential needed; no secret missing; no domain/DNS change; no security boundary weakened; no
ambiguous entity authorisation model; no Phase 7/8 scope impact.

---

## FINAL VERDICT

**PRODUCTION AUTH ACCESS CLOSURE COMPLETE — EXTERNAL CONFIGURATION REQUIRED**

Repository-side closure is complete and validated (routing defect fixed, privacy content strengthened, branded
unavailable experience implemented, access model documented). Production verification of the reported URLs
requires the **external Vercel deploy** — and, for consent branding, Google/Supabase dashboard configuration —
both outside this operation's authority.

## ATTESTATION

* **starting commit:** `5a1e45e0203b822b3a488a6004b904ef40abb059`
* **ending commit:** `5a1e45e0203b822b3a488a6004b904ef40abb059` (**no commit created**; changes left unstaged/uncommitted)
* **files modified:** `vercel.json`, `frontend/src/PrivacyPolicy.jsx`, `frontend/src/Login.js`,
  `frontend/src/AuthCallback.js` (+ 6 new files: 2 source, 3 architecture documents, 1 prompt-history record)
* **migrations created:** **NO** · **migrations applied:** **NO**
* **production Supabase contacted:** **NO** · **production Supabase modified:** **NO**
* **Google configuration changed:** **NO** · **Vercel configuration changed:** **NO** · **Render configuration changed:** **NO**
* **production URLs tested:** **YES** (read-only) — `/` 200, `/login` 404, `/privacy` 404
* **tests run:** frontend production build ×2 — CI-mode: **failed** (105 pre-existing warnings); non-CI: **passed** (exit 0, build ready to deploy)
* **deployment performed by agent:** **NO**
* **secrets introduced:** **NO** (a pre-existing publishable-key fallback was *reported*, not modified)
* **Phase 7 started:** **NO** · **Phase 8 started:** **NO**

**STOPPED** after this report. No Phase 7/8 work begun; no migration applied; no production system altered; no
dashboard configuration changed.
