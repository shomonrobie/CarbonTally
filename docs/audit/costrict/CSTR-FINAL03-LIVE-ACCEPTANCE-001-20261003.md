# CSTR-FINAL03-LIVE-ACCEPTANCE-001 — Independent Production Live Acceptance (Render + Vercel + Supabase)

## 1. Scope

Independent, **acceptance-only** live verification of the already-deployed FINAL-03 release:
Render production API, Vercel/static production frontends, and the already-accepted production Supabase
project — testing **actual production URLs** through the deployed application, not deployment-success
messages. Groups A–P of the authorising brief were executed to the extent possible with the identities and
tooling available.

**Boundary observed:** no source, migration, schema, RLS, policy, grant, data, storage, Render/Vercel
configuration, environment variable or secret was modified; no service was restarted; nothing was deployed,
committed, pushed or repaired. Production reads were read-only (`SET default_transaction_read_only = on`).
Write-type probes were deliberately **not** attempted where a write could succeed (see §5, §15). No
credential, token, JWT, key or DSN is printed in this report.

**Evidence labels:** **[I]** independently verified here · **[C]** reported by Cline, not independently
reproducible · **[E]** expected/documented behaviour · **[O]** operational observation · **[L]** limitation.

---

## 2. Frozen release SHA

```
375a48dc1b9e9cfd74090bbf747554ae997acb59   (branch p8-release-reconciled)
```

Independently verified previously (`CSTR-FINAL03-P2-RECON-VERIFY-001`); production migration state
independently accepted previously (`CSTR-FINAL03-P3-SUPABASE-VERIFY-001`). Both were **not** reopened.

## 3. Deployed URLs tested

| Surface | URL | Observed |
|---|---|---|
| Production API | `https://carbontally-api.onrender.com` | **reachable, healthy** |
| Public frontend | `https://carbontally.co.uk` | **reachable, renders** |
| Public sign-in | `https://carbontally.co.uk/login` | **reachable, form renders** |
| Admin frontend (documented host) | `https://admin.carbontally.co.uk` | **does not resolve (DNS)** |
| Admin frontend (actual path) | `https://carbontally.co.uk/admin` | reachable but **does not initialise** (config missing) |
| Declared Vercel aliases | `https://carbontally-frontend.vercel.app`, `https://carbontally-admin.vercel.app` | **Vercel `DEPLOYMENT_NOT_FOUND` (404)** |
| Production Supabase | `https://pvwiojoyaqywtydzcpbg.supabase.co` | reachable; auth service live |

## 4. Test environment

Read-only host shell (`/bin/bash`), `curl` 8.x, headless **Google Chrome** driven by Playwright (no browser
install performed), `python3`, PostgreSQL client wrapper over the accepted production DSN (read-only session
enforced in-session: `SHOW default_transaction_read_only` → **on**). No production write, deploy, restart or
configuration change was issued.

## 5. Actor identities used (no secrets)

| Actor | Role in testing | Notes |
|---|---|---|
| Anonymous browser (headless Chrome) | frontend reachability, JS bootstrap, login-page rendering | no credentials entered |
| Anonymous HTTP client | API boundary probes (expect 401), CORS probes, PostgREST/storage probes with the **public client key extracted from the deployed bundle** | the only key used is the one every browser receives |
| **anon** PostgREST role (client key, no user JWT) | direct browser→PostgREST table probes | the exact path the PO asked to test |
| `acceptance-probe-nonexistent@example.invalid` | invalid-credential probe at the auth service | a **non-existent** address — no real account touched |
| Production owner identities | **not available** | no production user credential exists in the workspace; creating test identities/records is prohibited |

**Consequence, stated up front:** every acceptance step that requires a *successful* production login could
not be executed. Those steps are classified **NOT TESTABLE** rather than inferred (see §6, §12, §15).

---

## 6. Groups A–P results

| Group | Result | Basis |
|---|---|---|
| **A — Render service** | **PASS** | reachability, startup, route set, no 5xx (§7) |
| **B — Vercel frontends** | **FAIL** (B1/B3 pass; **B2 fail**) | public frontend OK; **admin console does not initialise**; documented admin host unresolvable; two declared Vercel URLs 404 (§8) |
| **C — Authentication** | **PARTIAL: PASS (C3, C4) / NOT TESTABLE (C1, C2, C5, C6)** | unauth + invalid token denied live; invalid-credential rejected by the auth service; no successful-login credential available (§9) |
| **D — Organization/customer isolation** | **NOT TESTABLE** (data-layer guarantee already accepted) | no owner credentials; direct browser→PostgREST path proven denied (§10) |
| **E — Staff/consultant/internal boundaries** | **PARTIAL: PASS (unauthenticated denial) / NOT TESTABLE (role behaviour)** | §11 |
| **F — App-level RLS/authorization** | **PASS** (live, for the client path) | 20 tables incl. all FINAL-03 fail-closed tables deny the anon/PostgREST path; 0 `anon`/`public` policies (§12) |
| **G — Storage** | **PARTIAL: PASS (privacy/anon denial) / NOT TESTABLE (authorized flow)** | §13 |
| **H — Emission factors** | **PARTIAL: PASS (integrity + no direct mutation path) / NOT TESTABLE (authenticated retrieval)** | §14 |
| **I — Calculation/report workflow** | **NOT TESTABLE** | would require an authenticated commercial context and/or creation of non-disposable production data (§15) |
| **J — Email/SMTP** | **NOT TESTABLE** (no non-invasive production send available) | §16 |
| **K — Backup worker / runtime workers** | **PARTIAL: PASS (startup healthy, no worker-induced failure) / backup-worker start [C]** | §17 |
| **L — OCR / Tesseract** | **DEGRADED (non-blocking)** | Tesseract engine unavailable; supported pip-only ONNX OCR fallback exists; no FINAL-03 gate depends on OCR (§18) |
| **M — CORS** | **PASS** | intended origins allowed with credentials; unintended origins denied; **no wildcard exposure** (§19) |
| **N — Session/authorization regression** | **PARTIAL: PASS (no-session denial, invalid-session denial) / NOT TESTABLE (logout, relogin, context)** | §20 |
| **O — Production data integrity** | **PASS** | matches the accepted P3 baseline exactly, including the corrected **102** org-linked figure (§21) |
| **P — Runtime errors/warnings** | **PASS with informational notes** | no 5xx; warnings classified as non-blocking (§22) |

---

## 7. Group A — Render production service (evidence)

| Check | Evidence | Result |
|---|---|---|
| A1 reachability | `GET /` → **200** `{message: CarbonTally API, version 3.0.0, status: healthy}`; `GET /health` → **200**; latency 0.32–0.95 s; `/docs` → **200** | **PASS** |
| A2 application startup | `/health` payload: `status: healthy`, `supabase_connected: true`, `pool_connected: true`, components `database: connected`, `pool: connected`, `api: running` | **PASS** |
| A3 route registration | live `openapi.json` → **623 paths / 742 operations**; `HTTPBearer` security scheme; **729 of 742 operations declare security**; expected groups present (`/api/v3/**` 340, `/api/admin/**` 91, factors 13 paths, reports, calculations, documents, consultants) | **PASS** |
| A4 runtime stability | 16-endpoint sample: **no 5xx**; only 200 / 401 / 404 (non-existent paths probed) / 405 (method mismatch) | **PASS** |

## 8. Group B — Vercel / static production frontends (evidence)

| Check | Evidence | Result |
|---|---|---|
| B1 public frontend | headless Chrome: **HTTP 200**, title *"CarbonTally — Carbon Data Processing & Emissions Management Platform"*, React root rendered (**29,775 chars** of inner HTML), marketing/launch content present, **no failed requests**, only console message = benign `Content-Security-Policy-Report-Only` notice | **PASS** |
| B1b sign-in page | `https://carbontally.co.uk/login` → **200**, renders *"Continue with Google / Email Password / Sign In / Create Account"*, **email + password fields present**, no console errors | **PASS** |
| B2 admin frontend | `https://carbontally.co.uk/admin` → HTTP 200 but the app shows: *"Admin console configuration required — This deployment of the CarbonTally Admin console was built without its Supabase connection settings, so it cannot start yet… Missing build settings: **REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY**"*, logs a console error, and renders the config notice instead of the dashboard. The documented admin host `admin.carbontally.co.uk` **does not resolve** (curl exit 6 / NXDOMAIN, twice) | **FAIL** |
| B2b declared Vercel aliases | `carbontally-frontend.vercel.app` and `carbontally-admin.vercel.app` → **404 `DEPLOYMENT_NOT_FOUND`** | **FAIL (informational:** these are not the production surfaces) |
| B3 localhost dependency | deployed public bundle (2.37 MB) references `https://carbontally-api.onrender.com` **7×** and the production Supabase project **1×**; the 4 `localhost` / 1 `127.0.0.1` strings are **library defaults / host-check helpers** (`vs={url:"http://localhost:9999",storageKey:"supabase.auth.token"…}` is an overridden default object; `"localhost"===e||/^([a-z0-9]+…)` is the Supabase URL-validation helper) — no production code path resolves to a development API | **PASS** |
| B4 frontend→API integration | credentialed CORS is granted **only** to the real frontend origins (§19); the API is healthy and the bundle is built against the production API; the unauthenticated landing/login pages make **no** API call by design, and the authenticated flow could not be exercised | **PASS (config-level) / NOT TESTABLE (runtime authenticated flow)** |

**Root-cause evidence for B2 [I]:** `admin/src/supabaseClient.js` documents the deliberate design — it
reports missing configuration through a controlled notice instead of throwing — and **requires**
`REACT_APP_SUPABASE_URL` + `REACT_APP_SUPABASE_ANON_KEY` (no fallback). The deployed admin bundle does not
have them inlined, so the build was produced without those build-time settings.
`docs/operations/…QUICK_REFERENCE…` lists these variables as *"(Optional — code has a fallback)"* for the
frontend; the admin console has **no** fallback, so the gap is real for the admin surface.

## 9. Group C — Authentication (evidence)

| Check | Evidence | Result |
|---|---|---|
| C1 successful login | requires a production owner credential — **not available**; creating test identities is prohibited | **NOT TESTABLE** |
| C2 authenticated request | same constraint | **NOT TESTABLE** |
| C3 unauthenticated denial | live 401s: `/api/v3/organizations/{id}` → **401 Not authenticated**; `/api/admin/staff` → **401**; `/api/v3/reports` → **401**; `/api/v3/consultants/me` → **401**; `/api/v3/documents` → **401**; `/api/beta/me` → **401**; `/api/waitlist/` → **401** | **PASS** |
| C4 invalid/expired authentication | `Authorization: Bearer invalid.jwt.token` → **401 `Invalid authentication token`**; auth service live: `POST /auth/v1/token?grant_type=password` for a **non-existent** probe identity → **400 `invalid_credentials`** (no real account touched; probe address uses the `.invalid` TLD) | **PASS** |
| C5 logout | requires a session | **NOT TESTABLE** |
| C6 relogin | requires a credential | **NOT TESTABLE** |
| Additional posture | `external.anonymous_users: false` (anonymous sign-in **disabled**), email provider **enabled**, Google OAuth **enabled**, `mailer_autoconfirm: false`, `disable_signup: false` | [I] informational |

## 10. Group D — Organization/customer isolation

| Check | Result |
|---|---|
| D1/D2 each organisation sees only its own data | **NOT TESTABLE** — requires an owner credential for each of the two retained organisations |
| D3 cross-organisation object access denied | **NOT TESTABLE** at the authenticated layer; the **client layer is proven denied** (PostgREST path returns `42501 insufficient_privilege` for `organizations` / `organization_members` / `document_processing_queue`, §12) |
| D4 ID substitution / path / query manipulation | **PARTIAL PASS [I]:** unauthenticated substitution of a real organisation id (`/api/v3/organizations/0c0aa358-…`) returns **401**, not data; malformed/other ids behave identically; authenticated cross-tenant substitution is NOT TESTABLE |
| D5 cross-tenant storage access | **PASS for the client path** (§13); authenticated cross-tenant fetch NOT TESTABLE |

**Supporting independent evidence (not a substitute for D1/D2):** the accepted P3 verification established
at the database layer that all 44 FINAL-03 targets are RLS-enabled with zero permissive policies for the
client roles, and that **no policy in the schema references `anon` or `public`**.

## 11. Group E — Staff / consultant / internal boundaries

| Check | Evidence | Result |
|---|---|---|
| E5 administrative endpoints protected from ordinary users | `/api/admin/staff` → **401** unauth; invalid token → **401** (route-level dependency enforced) | **PASS (unauthenticated case)** |
| E1/E2/E3/E4/E6 role behaviour (internal staff, consultant/client model, consultant isolation, owner isolation, suspended access) | requires staff/consultant/customer credentials — none available; role changes to create them are prohibited | **NOT TESTABLE** |

## 12. Group F — App-level RLS / authorization interaction (live)

**Method [I]:** the **public client key taken from the deployed production bundle** (the exact key every
browser receives) was used to call the production PostgREST endpoint directly for 20 tables — the
"browser → direct table access" path the PO asked to test. Only status codes and error codes were recorded;
no row content was retrieved or printed.

**Result: every probed table returned `401` with PostgreSQL error code `42501` (insufficient_privilege) —
no table is reachable directly from the browser client**, including all FINAL-03 fail-closed tables:

```
system_settings · staff_roles · password_reset_tokens · beta_access_codes · beta_users · email_logs
notifications · review_audit_trail · waitlist · audit_trail · consultant_billing · consultant_tasks
login_history · staff_workload · emission_factors · organizations · organization_members
conversation_participants · manual_extraction_items · document_processing_queue
```

* The browser/PostgREST path is therefore **denied at the privilege layer (42901/42501) even before RLS**,
  and the architectural pattern required by the brief (**browser → authorized backend API → service-role
  backend access**) is the only available path. **No direct unrestricted table access exists.**
* Live catalog corroboration [I]: `0` policies reference `anon`/`public`; the three O-1 grant-carrying tables
  remain RLS-enabled with no `anon` policy; **no `anon` table privileges exist** on `audit_trail`
  (only `authenticated: SELECT`, now fail-closed under RLS) and **only `postgres`/`service_role` hold
  privileges on `emission_factors`**.
* **Limitation [L]:** the *authenticated-role* RLS behaviour through PostgREST could not be executed (no user
  JWT; anonymous sign-in is disabled by configuration). The accepted P3 verification covers that layer at the
  database level.

**Group F: PASS (client path) with the authenticated-role path NOT TESTABLE.**

## 13. Group G — Storage

| Check | Evidence | Result |
|---|---|---|
| G4 private bucket behaviour | with the real client key: `GET /storage/v1/object/public/documents/x.txt`, `GET /storage/v1/object/list/documents`, `GET /storage/v1/bucket/documents` → **400 `Bucket not found`** in every case, i.e. the private bucket is **not visible or addressable** by the anonymous client (bucket row is RLS-filtered); no object bytes returned | **PASS** |
| G3 direct object-URL manipulation | the public-object route does not expose the private bucket; no signed-URL forgery is possible without a JWT | **PASS** |
| G1 authorised document access / G2 cross-organisation denial / G5 signed-URL behaviour | require an authenticated user and an existing document; no credential available and creating objects/users is prohibited | **NOT TESTABLE** |
| Bucket integrity [I] | live DB: `documents` bucket present, **`public = false`**, **58 objects**, unchanged from the accepted P3 baseline | **PASS** |

## 14. Group H — Emission factors

| Check | Evidence | Result |
|---|---|---|
| H1 authorised retrieval | the factor endpoints exist in the deployed route set (`/api/v3/emissions/factors`, `/api/admin/defra/factors`, `/api/v2/factor-match`, …) but require authentication (401 unauth); no credential available | **NOT TESTABLE (authenticated retrieval)** |
| H2 7,049 factors available | live DB count **7,049** (unchanged, byte-identical to the accepted P3 verification) | **PASS** |
| H3 lookup/matching path present | **13 factor-related operations** are served by the deployed API (e.g. `/api/v2/factor-match`, `/api/v3/emissions/factors`, `/api/admin/defra/factors`) | **PASS (route presence)** |
| H4 customers cannot mutate the authoritative library | live grants on `emission_factors`: **only `postgres` and `service_role`** hold privileges — **no `anon`, no `authenticated`**; direct client reads/writes → **42501** | **PASS** |

## 15. Group I — Calculation / report workflow

**NOT TESTABLE.** Executing the pipeline end-to-end requires an authenticated customer context and would
create non-disposable commercial/audit data (uploads, extraction, calculation snapshots, reports) in the live
tenant. Per the brief ("If a full end-to-end production calculation would create non-disposable
commercial/audit data, do not perform it"), the write-side exercise was **not** performed, and creating a
disposable customer/organisation is prohibited by §4. Read-only substitute evidence [I]: the deployed route
set serves the calculation/report surface (`/api/v3/emissions/calculate`, `/api/v3/scope2/calculate`,
`/api/v3/scope3/calculate`, `/api/v3/processing/items/{id}/calculate`, `/api/v3/emissions/calculations`,
`/api/v3/reports` (33 operations)), all protected (401 unauth), and the accepted P3 database state retains
the production evidence/calculation tables untouched.

## 16. Group J — Email / SMTP

**NOT TESTABLE.** Sending a real transactional email would have unintended customer/commercial impact, and no
non-invasive dummy-recipient path exists without authenticated application context. Route-level evidence [I]:
the API is healthy and email-related operations remain registered; the email provider is configured in the
API environment [C]; the email service is designed as a **no-op stub when the provider key is unset**
(documented in the operations quick reference), so a missing configuration would degrade rather than fail
requests. No email configuration was examined in a way that exposes credentials, and none was changed.

## 17. Group K — Backup worker / runtime workers

| Check | Evidence | Result |
|---|---|---|
| application startup healthy / worker init causes no failure | `/health` = healthy (`database`, `pool`, `api` components up) throughout the session; **no 5xx** in any probe | **PASS** |
| a production worker is genuinely running | **live queue evidence [I]:** `document_processing_queue` lease advanced repeatedly during acceptance (`locked_at` / `updated_at` → **2026-10-03 06:25:13 UTC**, `lock_token` of the form `worker::<uuid4hex>` generated by the application worker, `status=processing`, `stage=extracting`, `attempt_count=0`). This is direct evidence of an active processing worker process | **PASS (worker liveness)** |
| `Backup worker started` (Render log) | Render's log is not accessible to this verifier; `public.backup_jobs` contains **0 rows** (no backup job has run — expected, none authorised) | **[C] / no contradiction** |

No backup/restore was triggered, no worker was started/stopped/restarted, no backup configuration changed.

## 18. Group L — OCR / Tesseract determination

**Observed production condition [C]:** Render logs report `tesseract binary unavailable`,
`OCR disabled for this process`, `OCR skipped: tesseract binary unavailable`.

**Independent findings [I]**

| Question | Finding |
|---|---|
| L1 — is OCR a required capability of the currently accepted release? | **Not for FINAL-03.** FINAL-03 is the RLS security remediation; the ratified production cutover package contains **no OCR/Tesseract acceptance gate** (zero matches for OCR/tesseract). OCR belongs to the wider document-processing capability, not to the FINAL-03 acceptance criteria. |
| L2 — is there a supported non-OCR path? | **Yes, two.** `backend/pdf_engine.py:122 _extract_text_direct()` extracts digital-PDF text with **pdfplumber** (no OCR); `pdf_engine.py:44 tesseract_available()` is a **probe** and `:156` skips OCR cleanly (`"tesseract binary unavailable (%s): OCR disabled for this process (install tesseract-ocr or set TESSERACT_CMD)"`), so the process degrades instead of failing. CSV/XLSX parsing is likewise independent of OCR. |
| L2b — is there an alternative OCR engine? | **Yes.** `backend/services/automatic_extraction.py:289-373` implements a **pip-only ONNX OCR fallback** (`pypdfium2` render + `rapidocr_onnxruntime`), documented in code as *"the pip-only fallback the extraction code already implements for hosts without Tesseract/poppler"* and as *"Tesseract/poppler unavailable → pypdfium2 render + ONNX OCR"*. Both packages are **declared in `backend/requirements.txt` (`pypdfium2>=5.13.0,<6.0`, `rapidocr_onnxruntime>=1.2.3,<1.3`)** with the CT-STEP2-RENDER-DEPS-008 rationale that this makes the scanned-PDF/image OCR path operational on the Render native runtime. |
| L3 — does the missing Tesseract engine fail any accepted FINAL-03 production workflow? | **No evidence of it.** The API is healthy, the RLS remediation carries no OCR dependency, and no FINAL-03 workflow in the accepted scope requires OCR. |
| L4 — was this known/deferred? | **Yes.** `docs/audit/cline/CARBONTALLY_V3_RENDER_OCR_PRODUCTION_PROVISIONING_HANDOFF.md` records that Tesseract/poppler are **not provisioned** on the Render service and provides the provisioning options; the earlier P8-STEP2 production acceptance recorded scanned/OCR documents as **UNVERIFIABLE in production**. AGENTS.md §20 requires production deployment to *explicitly verify* required OCR capabilities — which the deployment does (it reports the engine state). |

**Classification: L — DEGRADED (non-blocking).** The **Tesseract engine** is unavailable and the
Tesseract-specific log message is accurate; however a documented, dependency-pinned alternative OCR path
(ONNX) plus fully supported non-OCR paths exist, no FINAL-03 acceptance requirement depends on OCR, and the
condition was previously documented and accepted. If a future release *requires* Tesseract-specific OCR
behaviour, provisioning per the existing handoff becomes a **pre-condition for that release**, not a defect
of this one. No installation, Render change or configuration change was made (prohibited).

## 19. Group M — CORS determination

Live preflight (`OPTIONS` with `Access-Control-Request-Method/Headers`) and simple `GET` with `Origin`:

| Origin | Preflight status | `access-control-allow-origin` returned | Credentialed exposure |
|---|---|---|---|
| `https://carbontally.co.uk` | **200** | `https://carbontally.co.uk` | intended |
| `https://admin.carbontally.co.uk` | **200** | `https://admin.carbontally.co.uk` | intended (also configured for the admin origin) |
| `https://carbontally-frontend.vercel.app` | **200** | that exact origin | intended (declared deployment alias) |
| `https://evil.example.com` | **400** | **absent** | **none** — no ACAO returned on both preflight and simple GET |
| `https://foo.onrender.com` | **400** | **absent** | **none** |
| `null` | **400** | **absent** | **none** |

**Determination [I]:** the allow-list is an **exact-origin match** set, not a wildcard. The
`https://*.onrender.com` string seen in the Render startup log does **not** translate into wildcard
credentialed access: an arbitrary `onrender.com` subdomain is denied with HTTP 400 and receives no
`Access-Control-Allow-Origin`, so the browser cannot read the response. `access-control-allow-credentials:
true` is present in responses, but credential-bearing cross-origin reads remain impossible for unlisted
origins because ACAO is absent (the CORS specification requires an exact ACAO match). **No unintended
credentialed CORS exposure was found. Group M: PASS.** (Note: the disallowed-origin preflight returns 400
rather than 200 — acceptable behaviour; no configuration was changed.)

## 20. Group N — Session / authorization regression

| Check | Result |
|---|---|
| protected endpoint without session is denied | **PASS** — 401 across `/api/v3/**`, `/api/admin/**` samples [I] |
| invalid session denied | **PASS** — invalid bearer → 401; auth service rejects invalid credentials → 400 `invalid_credentials` [I] |
| session persists as intended / logout / relogin / organisation context after relogin / no stale context | **NOT TESTABLE** — no production credential; creating sessions or identities is prohibited |
| privileged endpoints reject insufficient roles | **PARTIAL** — unauthenticated denial proven; role-insufficiency (authenticated-but-not-privileged) requires a JWT → **NOT TESTABLE** |

## 21. Group O — Production data integrity during acceptance (read-only)

| Metric | Accepted P3 baseline | Measured now | Verdict |
|---|---|---|---|
| organisations | 2 | **2** (same ids/names, `is_active=t`) | ✅ |
| owner accounts (`auth.users`) | 2 | **2** | ✅ |
| memberships | 2 | **2** | ✅ |
| emission factors | 7,049 | **7,049** | ✅ |
| `documents` storage objects | 58 | **58** | ✅ |
| org-linked baseline (corrected authoritative figure) | **102** | **102** | ✅ |
| public tables / RLS-enabled / policies / applied migrations | 150 / 147 / 231 / 98 | **150 / 147 / 231 / 98** | ✅ |
| `document_processing_queue` rows | 11 | **11** (1 leased by the live worker; lease metadata advanced only) | ✅ no loss |

All figures equal the independently accepted post-migration state; the only movement is the live worker's
lease metadata (D-3), which is **not** data loss. **No unexpected production mutation was caused by this
acceptance** — every DB statement was read-only, and no application write was submitted.

## 22. Group P — Runtime errors / warnings classification

| Observation | Impact | Class |
|---|---|---|
| FastAPI `regex=` deprecation warnings (`Query(regex=…)` in `routes/emissions.py`, `routes/admin/staff.py`, `routes/admin/workload.py`) | documentation/runtime deprecation only; no functional effect observed; also reflected in `/docs` | **INFORMATIONAL** |
| `HEAD /` → **405** | probes that use HEAD see 405; `GET /` is healthy; no user impact | **INFORMATIONAL** |
| `tesseract binary unavailable` / `OCR disabled for this process` | see L → DEGRADED, non-blocking | **DEGRADED (non-blocking)** |
| `Content-Security-Policy` `upgrade-insecure-requests` ignored in a **report-only** policy | browser console notice only; policy is report-only by design | **INFORMATIONAL** |
| `Permissions-Policy: Unrecognized feature: 'bluetooth'` | browser console warning only; no functional impact | **INFORMATIONAL** |
| HTTP 404 on third-party-aliased `*.vercel.app` hostnames; unresolvable `admin.carbontally.co.uk` | see B2 — deployment/DNS configuration gap | **FINDING (blocking for the admin surface)** |
| No HTTP 5xx observed anywhere in the acceptance | — | **PASS** |

---

## 23. Findings

### BLOCKING

| ID | Finding | Evidence | Impact | Remediation |
|---|---|---|---|---|
| **BLK-1** | **The production admin console cannot start.** The deployed admin build (served at `https://carbontally.co.uk/admin`) was built **without** `REACT_APP_SUPABASE_URL` / `REACT_APP_SUPABASE_ANON_KEY`, and renders only its configuration notice: *"Admin console configuration required … cannot start yet"*; it logs an error and never initialises. The documented admin host **`https://admin.carbontally.co.uk` does not resolve** (NXDOMAIN). The two declared Vercel aliases return `DEPLOYMENT_NOT_FOUND`. | §8 [I] (HTTP 200 + rendered notice + console error + DNS + `admin/src/supabaseClient.js`, which documents the fail-closed config design) | The **admin operating surface is not functional in production**, so the FINAL-03 R‑5 admin call-site changes (`admin/src/pages/admin/BetaManagement.js`, `Settings.js`, `WorkHub.jsx`, `admin/src/services/adminApi.js`, `reviewService.js`) are deployed as code but **cannot be exercised**; admin/beta access operations are unavailable | **Requires configuration/deployment action, not code repair:** build the admin app with the two Supabase build variables set for the target environment, deploy it, and provision `admin.carbontally.co.uk` (or formally designate `/admin` on the main domain as the admin surface). **Not performed here (prohibited).** |
| **BLK-2** | **The acceptance criteria that must *pass* could not be executed:** successful authentication (C1/C2/C5/C6), authenticated tenant isolation (D1–D3, D4 authenticated case, D5 authenticated case), storage authorisation for an authorised user (G1/G2/G5), the authenticated calculation/report workflow (I), the email path (J) and role-based boundaries (E1–E4, E6). No production user credential exists in the workspace, and creating test identities or non-disposable production records is expressly prohibited by the brief. | §5, §9, §10, §11, §13, §15, §16, §20 [L] | Acceptance **cannot be granted** under the PO's decision rule, which requires these boundaries to *pass* — the present state is *unproven*, not *failed* | Provide PO-authorised, disposable production test identities (customer owner A, customer owner B, consultant, internal staff) **or** authorise a scoped, reversible acceptance fixture, then re-run C/D/E/G/I/J/N. **Not performed here.** |

### NON-BLOCKING

| ID | Finding | Severity | Evidence | Impact | Remediation |
|---|---|---|---|---|---|
| **NB-1** | Tesseract engine unavailable; ONNX OCR + non-OCR paths present | Low (DEGRADED) | §18 | Scanned-image OCR via Tesseract is unavailable; an alternative OCR engine and text-based paths exist; no FINAL-03 gate depends on it | Provision per the existing OCR handoff **only if** a future release requires Tesseract-specific OCR |
| **NB-2** | Declared Vercel aliases (`carbontally-frontend.vercel.app`, `carbontally-admin.vercel.app`) return `DEPLOYMENT_NOT_FOUND`; `admin.carbontally.co.uk` unresolvable | Low–Medium | §8 | Documentation/alias drift; the real production surfaces are `carbontally.co.uk` (+ `/admin`) | Correct the documented URLs / retire stale aliases |
| **NB-3** | O‑1 remains open: `anon` holds 12 inert DML grants on three **empty**, RLS-enabled new tables; no `anon`/`public` policies anywhere; live probe returns 0 rows | Low (security hardening) | §12 | No anonymous access is possible (fail-closed; grants inert) | PO decision on a `REVOKE`-hardening migration (unchanged from P3) |
| **NB-4** | Live processing worker re-leases one queue row (D‑3); lease advanced to `2026-10-03 06:25:13 UTC` during acceptance | Low (operational) | §17, §21 | Environment is not write-quiescent; no data loss, no business-column change; by-product of a running worker | Operationally expected; document for any future write-window test |
| **NB-5** | `Backup worker started` (Render log) is not independently observable; `backup_jobs` = 0 rows | Informational | §17 | Startup health verified; backup-worker start rests on the deployment log | None required; backup execution is not authorised at this stage |
| **NB-6** | OpenAPI: 729/742 operations declare security (nice-to-have completeness) | Informational | §7 | Documentation completeness only | Optional |
| **NB-7** | Public self-signup enabled (`disable_signup: false`), anonymous sign-in **disabled** | Informational | §9 | Product posture; consistent with a public launch surface | None required |

### NEW RISK INTRODUCED BY TESTING

**None.** All production DB access was read-only; the only network writes were an invalid-credential auth
probe against a non-existent `.invalid` identity (no account, no email, no data), and read-only HTTP GET/OPTIONS
requests. No test identity, record, object or configuration was created.

---

## 24. Blocked / not-testable items (explicit)

1. C1, C2, C5, C6 — successful login, authenticated request, logout, relogin (no production credential).
2. D1–D5 authenticated cases — organisation isolation with real owner sessions.
3. E1–E4, E6 — staff/consultant/customer-role boundaries and suspended access.
4. F authenticated-role RLS path via PostgREST (no user JWT; anonymous sign-in disabled).
5. G1, G2, G5 — authorised document access, cross-organisation denial, signed-URL behaviour.
6. H1 — authenticated emission-factor retrieval (H2–H4 passed by other means).
7. I — end-to-end calculation/report acceptance (would create non-disposable production data).
8. J — production email send.
9. N — session persistence, logout, relogin, post-relogin organisation context.
10. K — independent observation of the *backup* worker's start (Render log only).

Each is classified **NOT TESTABLE** for the recorded reason, and **none is asserted as passed**.

---

## 25. Limitations

1. **No production user credentials** → the authenticated acceptance flows could not be run (the dominant limitation).
2. **No Render/Vercel console access** → deployment logs, service configuration and the backup-worker start rest on Cline's statements [C]; only externally observable behaviour was tested.
3. **Anonymous sign-in is disabled** → no self-serve test session could be created even if that had been authorised.
4. **Headless Chrome used the production public bundle only**; no credential or session was injected, so the authenticated SPA routes were not exercised.
5. **The PostgREST probes test the `anon` (client-key) role only**, which is exactly the "browser → direct table access" path; the authenticated-role path is covered by the accepted P3 database verification, not re-tested here.
6. **Probing non-existent paths produced 404s** — these are not treated as defects.
7. **The D-3 worker makes production non-quiescent**; any future acceptance run must expect lease metadata to move.
8. **Timing**: the API's `openapi.json` response took ~11.5 s (cold/large document); no functional impact observed.

---

## 26. Final verdict

The **customer-facing production platform is healthy, secure and integrated**: the Render API is healthy
(no 5xx, 742 operations, 729 with declared security), the public frontend and sign-in page render and boot
in a real browser, CORS is an exact-origin allow-list with no wildcard exposure, the browser→database direct
path is denied at the privilege layer for all 20 probed tables including every FINAL-03 fail-closed table,
the private storage bucket is unauthorised to the client, the factor library is unreadable/unwritable by
clients, production data integrity matches the accepted baseline exactly (including the corrected **102**
org-linked figure), and OCR/CORS were explicitly classified (DEGRADED non-blocking / PASS).

However, acceptance **cannot** be granted:

* the **admin console does not function in production** (missing build-time Supabase settings) and its
  documented hostname does not resolve — a required surface of this acceptance fails outright; and
* the acceptance criteria that **must pass** — successful authentication, authenticated tenant isolation,
  authenticated storage authorisation, the calculation/report workflow, email and role-based boundaries —
  were **NOT TESTABLE** for want of any authorised production identity, so they are unproven.

> **CSTR-FINAL03-LIVE-ACCEPTANCE-001 — NOT ACCEPTED — BLOCKING FINDINGS REMAIN**

Blocking findings: **BLK-1** (admin console inoperative / admin hostname unresolved) and **BLK-2**
(authenticated acceptance not executable with the available authorisation).

**Boundary:** nothing was repaired, deployed, restarted, committed or pushed; no production data, storage,
RLS, grant, schema, environment variable or secret was modified, and no subsequent production change is
authorised by this report. The next decision belongs to the Product Owner.
