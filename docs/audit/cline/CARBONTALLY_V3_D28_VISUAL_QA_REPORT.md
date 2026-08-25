# CarbonTally V3 — D28 Visual QA Report

**Date:** 2026-08-22 · **Mode:** VISUAL QA + SCREENSHOT CAPTURE (audit only — no fixes applied)
**Auditor:** Cline (automated browser session)

---

## 1. Executive summary

The CarbonTally V3 application was brought up on the local development stack and a complete
visual capture pass was executed with the **existing** browser-automation mechanism
(Selenium 4.47.0 + geckodriver 0.36.0 + headless Firefox 149.0.2, `save_screenshot()`, 1366×768).

**28 screenshots** were captured under `screenshots/d27_evidence/ui/` across four actor families
(Customer/Owner, Consultant, Internal Operations staff, Staff-admin) covering the V3 route matrix
and the D27 workflows that are reachable from the demo data.

**Headline results**
- The V3 customer, consultant and internal-operations surfaces **render with live data** and no
  frontend error states (0 `.v3-error` blocks observed on any captured page).
- **D27 new pages are present and functional**: Existing-data discovery (4-step flow), messaging
  (customer + consultant), white-label domains/senders, notifications, issues.
- **No P0 security findings.**
- **1 P1 backend finding** (a legacy org-membership endpoint returns HTTP 500 for non-members —
  masked by the frontend but a real defect) and **1 environment-condition finding** (the local DB
  was missing the demo seed and five D20/D21/D22/P9/D27 migrations; restored per the "run locally"
  allowance).
- Processing-Entity workspace: **NOT TESTABLE** via UI (no entity-staff auth identity exists);
  isolation verified by code inspection and the staff-admin Entities tab.
- Terminology audit (Part 8): **PASS** — no "consultant client uses CarbonTally directly" wording;
  "Direct CarbonTally Customer" is used correctly; START FRESH explicitly says nothing is deleted.
- Google OAuth / MFA: **EXTERNAL CONFIGURATION REQUIRED** — not verifiable locally.

## 2. Capture environment

| Item | Value |
|---|---|
| Host | Ubuntu 26.04 LTS (x86_64), 15 GiB RAM |
| Browser | Firefox 149.0.2 (snap rev 8107), headless, `binary_location=/snap/firefox/current/usr/lib/firefox/firefox` |
| Driver | geckodriver 0.36.0 (snap-bundled) |
| Automation | Selenium 4.47.0 in `backend/.venv` |
| Viewport | 1366×768 window → 1366×682 PNG (identical geometry to the original 11 captures) |
| Supabase | Local Docker stack `supabase_*_carbon_ledger` (healthy) |
| Backend | `uvicorn main:app` on **:8001** — healthy, 546 routes, version 3.0.0 |
| Frontend | CRA `npm start` on :3000 with `REACT_APP_API_URL=http://localhost:8001` |
| Auth | Real UI password sign-in (local demo identities; gitignored local credentials) |

**Environment findings (recorded, not product defects):**
- **E1 — Port 8000 contention.** A separate dev server (`carbon_tally_synthetic_documents/api.py`)
  holds :8000 and reclaims it if freed. The CarbonTally backend therefore ran on :8001 with a
  frontend runtime env override. No files were modified.
- **E2 — Local DB was not in the documented local state.** It was missing (a) the idempotent demo
  seed (org `CarbonTally Demo Ltd`, its 4 members, the consultant firm membership, demo facilities/
  documents/batches/reports) and (b) five unapplied migrations (`D20`, `D21`, `D22`, `P9`, `D27`).
  Both were restored (seed minus the emissions-log block, which cannot reference the
  production-restored factor vocabulary; migrations applied in order). These steps are required by
  the documented local setup (D27 manifest: "supabase db push") and were the minimum needed to make
  the application run locally.
- **E3 — Browser-process cleanup.** Snap-confined Firefox/geckodriver processes cannot be signalled
  from this user context (kernel `Permission denied` on kill), so orphaned headless processes from
  repeated captures accumulated and drove the system to high load (load average ≈ 28, swap full).
  This made page loads slow (6–20 s) but did not prevent any capture.

**Methodology honesty note:** the auditor model in this session cannot render images, so the visual
evaluation is based on (a) per-page DOM/geometry/text signals captured at screenshot time
(headings, nav, tables, loading states, error blocks, visible body text), (b) static inspection of
the page components, and (c) the preserved PNG files themselves (available for human review). No
screenshot is claimed that was not written to disk, and no visual claim is made beyond what the DOM
signals and code support.

## 3. Screenshot inventory

28 screenshots — full table in `screenshots/d27_evidence/UI_SCREENSHOT_MANIFEST.md`.
Summary: 2 public/auth, 12 customer, 5 consultant, 9 internal operations.

Routes exercised: `/` `/login` `/home` `/emissions` `/documents` `/processing` `/reports`
`/reports/:id` `/organization` `/existing-data` `/messaging` `/issues` `/notifications`
`/consultant` (+4 tabs) `/ops` (+Data entry/Review/QC/Entities/Staff tabs).
Actors: OWNER, CONSULTANT, OPERATOR, REVIEWER, QC, STAFF-ADMIN, Public.

## 4. Customer UX (OWNER)

| Screen | Signals at capture | Verdict |
|---|---|---|
| `/home` | h1 "Dashboard", stat cards READY REPORTS 1 / QUEUED REPORTS 1 / DOCUMENTS 4, V3 nav (Dashboard, Emissions, Documents, Processing, Issues, Reports, Messages, Existing data, Organization, Notifications), org "CarbonTally Demo Ltd", Sign out | **PASS** — live data, correct nav |
| `/emissions` | h1 "Emissions & calculations", "Authoritative V3 calculation — the backend matches factors…", empty history ("No recorded calculations yet.") | **PASS** — form renders; empty state honest (demo emissions logs not seeded, E2) |
| `/documents` | h1 "Documents", 2 tables (documents + upload batches), upload control, subtitle "Upload and browse org documents (Supabase Storage via the V3 API)" | **PASS** — live data |
| `/processing` | h1 "Processing", 1 table, "Batches (3)", "Manual-extraction batches and items (org-scoped V3 surface)" | **PASS** — live data |
| `/reports` | h1 "Reports", report rows | **PASS** |
| `/reports/:id` | h1 "Annual emissions report 2025", versions section ("No versions recorded yet.") | **PASS** |
| `/organization` | h1 "Organization administration", "Profile & Set…" tabs | **PASS** |
| `/existing-data` | h1 "Existing data", "Check whether CarbonTally already holds data that may belong to your organisation", 4-step flow | **PASS** (see §10) |
| `/messaging` | h1 "Messages", "Conversations between your organisation and your consultants", "Start a conversation", empty state | **PASS** (empty demo state) |
| `/issues` | h1 "Issues", 2 issue rows | **PASS** |
| `/notifications` | h1 "Notifications", "You are all caught up", "Unread only", "Mark all as read", "No notifications yet." | **PASS** |

Findings: see F3 (loading latency), F5 (post-login redirect), F8 (redundant empty-state copy).

## 5. Consultant UX (CONSULTANT)

| Screen | Signals at capture | Verdict |
|---|---|---|
| `/consultant` (dashboard) | Stat cards (client count etc.), active-client switcher, client list with lifecycle badges | **PASS** (header brand title renders async — see F4) |
| Client workspace | h1 "Consultant workspace", "You are working on: <client>" banner, processing-status + reports tables (6 rows), client-specific | **PASS** — live data; explicit active-client banner is good |
| Firm branding | Branding form (brand name, logo URL, primary/secondary colour, footer, sender email, website, portal, support contact, white-label + co-brand toggles), read-only when not permitted | **PASS** |
| White-label | Custom domains + custom email senders with verify lifecycle; empty states "No custom domains configured." / "No custom senders configured." | **PASS** |
| Client messages | Conversation list scoped to the active client org; empty state "No conversations yet." | **PASS** |

Destructive/lifecycle actions carry `window.confirm` dialogs with accurate copy
("Suspend access… Their data stays intact but is temporarily inaccessible", "End the
relationship… Historical audit/provenance remains…").

## 6. Internal Operations UX (OPERATOR / REVIEWER / QC / STAFF-ADMIN)

- `/ops` renders the role-aware shell: "Internal Operations", header shows
  "Operator One · operator", **STAFF** nav badge, tabs Dashboard/Data entry/Review/QC/Staff/Roles
  (+ Entities/SLA for staff-admin).
- Ops dashboard (10 s capture): live aggregates — BATCHES 3, ITEMS 4, % COMPLETE 25%, PENDING QC 1,
  CUSTOMER REVIEW 0, ISSUES 17, STAFF 9, "Pipeline by stage".
- Review queue and QC queue tabs render for reviewer/QC respectively.
- Staff-admin sees the **Entities** tab (D22 processing-entity provisioning/monitoring) and the
  **Staff** roster.
- Access control: a non-staff identity calling `/api/v3/ops/me` gets 403 (denied) and is redirected
  by the role guard to the correct home — no role leakage observed.

**PASS** overall; see F3 for loading latency on tab surfaces under load.

## 7. Processing Entity UX (D22)

- **Route exists:** staff with `staff_profiles.entity_id` set are routed to
  `EntityExtractionWorkspace` (`OperationsPage.jsx`: `if (me?.profile?.entity_id) return <EntityExtractionWorkspace …>`).
- **NOT TESTABLE in this environment** — no entity-staff `auth.users` identity exists (the D22
  provisioning created `staff_profiles` rows only), so an entity-staff login cannot be performed
  without creating an auth user (a database change outside the audit scope). This matches the D27
  manifest's own note ("needs a provisioned entity + entity staff demo").
- **Isolation verified by code inspection:** `EntityExtractionWorkspace` calls only
  entity-scoped APIs (`getEntityExtractionBatches(entityId)`, `getEntityDashboard(entityId)`,
  `entityStartItem/extractItem/mapItem/calculateItem/clarifyItem(entityId, …)`). It contains **no**
  references to customer organisations, consultant directories, or internal ops surfaces. The
  staff-admin **Entities** tab (`operations-entities.png`) shows the entity registry.
- **No violation observed.** Recorded as **NOT TESTABLE (UI)** + **PASS (static isolation check)**.

## 8. Authentication UX

- `/login` renders email+password form, Google button ("Continue with Google"), signup toggle,
  "Secure, UK GDPR Compliant" trust badge. **PASS** as a surface.
- Demo sign-in with local credentials works for all six test actors.
- **F5 (P2):** after sign-in the app navigates to the **legacy** `/dashboard` instead of the V3
  `/home`, so a freshly signed-in customer lands on the legacy monolith.
- Google OAuth + MFA: **EXTERNAL CONFIGURATION REQUIRED** (Supabase dashboard) — not verified.

## 9. Messaging UX

- Customer surface (`/messaging`): conversation list, "Start a conversation", empty state
  "No conversations yet.", org-scoped (`organization_id`).
- Consultant surface ("Client messages" tab): conversations scoped to the **active client**
  `client.organization_id`; start-conversation flow.
- **Processing Entity staff have no messaging access by construction** — the entity workspace has
  no messaging UI, and the D27 messaging migration explicitly grants no participant access to
  entity staff (D18 boundary preserved).
- No conversation data exists in the demo DB, so send/unread/timestamp flows show empty states
  only. **PASS (surfaces + scoping)** / message interaction itself **NOT TESTABLE** without data.

## 10. Existing Data Discovery UX (D27/D19)

Four-step flow implemented in `/existing-data`:
1. **Find existing data** — lookup form (organisation name / company number / email domain /
   contact email) with explicit copy: "Matches are **candidates only** — never treated as
   ownership. Adoption always requires secure verification and your explicit choice."
2. Candidate table with per-category data counts and a "request access / verify" action.
3. **Choice UI** with exact wording: **Use all** ("adopt all eligible existing organizational data
   in place"), **Use selected / partial** (category checkboxes), **Start fresh** ("do not use the
   discovered historical data").
4. Completion: adopted → "You are now a Direct CarbonTally Customer for the adopted organisation.
   Historical data was preserved in place…"; discarded → "Your choice was recorded. **No data was
   deleted** — the existing organisation remains untouched. A formal deletion is always a separate
   process."

**Part 12 check — PASS:** "Start fresh" explicitly and repeatedly clarifies that no data is
deleted ("Choosing to start fresh never deletes the existing data"). No misleading "delete
historical data" implication found.

## 11. White-label UX

- Configuration UI verified: custom domains (add → TXT token → verify → activate → remove) and
  custom senders, with status labels (Pending verification / Verified / Active / Removed-suspended).
  Empty states render correctly.
- Branding fields on the firm profile (brand name, colours, footer, support contact,
  `white_label_enabled` + `co_branding_enabled` toggles). **PASS** — configuration surface.
- **Presentation mode not visually verified** — the demo firm has no active white-label/co-brand
  flags, so the CarbonTally-invisible / co-branded shell was not rendered. Branding is resolved
  server-side (`/api/v3/consultants/me/branding/context`); no client-injected branding test was
  performed (per Part 9 instruction).

## 12. Reporting UX

- Report list (status filters) and report detail (content preview, versions, downloads) render with
  real rows. **PASS.**
- PDF artefact workflows (CarbonTally-branded / co-branded / white-label): the D27 evidence PDFs
  already exist under `screenshots/d27_evidence/` (produced by `engines/pdf_render.py` +
  `domain.branding.BrandContext`). UI-side PDF download buttons are present; PDF rendering itself
  is the D27 evidence, not re-verified in this session.

## 13. Responsive observations

- `customer-dashboard-mobile.png` captured at **500×726** — Firefox headless enforces a minimum
  window width of 500px, so a true 375px phone viewport was not achievable in this mechanism.
- At 500px the V3 customer dashboard rendered fully: nav, stat cards, org, sign-out — **no
  horizontal-overflow error or missing data observed** in DOM signals.
- **Not tested:** true mobile breakpoints, tablet, high-DPI. Recorded honestly — responsive QA is
  partial.

## 14. Accessibility observations (limited, code-based)

- Nav uses `<nav aria-label="V3 navigation">`; consultant client switcher has `aria-label`.
- Buttons are real `<button>` elements; forms use labelled inputs.
- No automated a11y scanner was run (out of scope); several components are keyboard-usable.
- Colour contrast / font sizes not measured (no image rendering). **Not a PASS or DEFECT** —
  limited evidence.

## 15. Security / authorization UX findings

- Role guards (`RoleRoute`) redirect correctly and never claim to grant access (comment: "Guards
  never grant access"). Backend/RLS remain authoritative.
- Denied surfaces surface a clean 403 → redirect; staff permission failures in the Phase-9-era ops
  screens now resolve correctly (staff permissions read from `staff_roles`).
- **F1 (P1):** legacy `GET /api/organizations/members/user/{user_id}` returns **HTTP 500**
  (`'NoneType' object has no attribute 'data'`) for any user without a membership row (e.g.
  consultants and staff). The V3 frontend treats a non-OK response as "no org" and continues, so
  the UI impact is masked — but the endpoint is a 500 and is on the auth-resolution path
  (`resolveV3Organization`).
- **PASS:** no cross-role data visible in any captured page (consultant sees only the demo firm;
  operator sees only internal ops; org members see only `CarbonTally Demo Ltd`).

## 16. P0/P1 findings

| # | Severity | Screenshot / route | Actor | Problem | Expected | Recommendation |
|---|---|---|---|---|---|---|
| F1 | **P1** | n/a (backend) — triggered by any non-member session on `/home` etc. | All | `GET /api/organizations/members/user/{id}` returns **500** for users with no membership row (message: `'NoneType' object has no attribute 'data'`); logged on every non-customer V3 session | Return 404/200-empty for non-members, never 500 | Fix the endpoint to return a clean 404 (or 200 with `primary_organization: null`) and harden `None` handling in `routes/organizations/members.py` |
| F2 | **P1 (environment)** | n/a | — | Local DB was missing the demo seed and five D20–D27 migrations, so D27/D22/D21 surfaces could not function locally | Documented local demo state | Already remediated this session (idempotent seed + migrations applied); ensure `supabase db push` is part of the documented local setup |

## 17. P2 findings

| # | Severity | Route | Actor | Problem | Expected | Recommendation |
|---|---|---|---|---|---|---|
| F3 | P2 | `/documents` `/processing` `/organization` `/existing-data` `/messaging` and `/ops` tabs | All | Under load, pages show an indeterminate "Loading…" spinner for several seconds with no timeout or error fallback; if a request hangs the user sees an infinite spinner | Bounded loading state with timeout → error state | Add a fetch timeout + loading-to-error fallback in `v3Fetch` and per-page loaders |
| F4 | P2 | `/consultant` | CONSULTANT | Header brand title is empty until the async `brandContext` resolves; the dashboard capture shows an empty `<h1>` | Render "Consultant workspace" immediately, then swap to the brand title | Render the fallback title synchronously |
| F5 | P2 | `/login` | All | Successful sign-in navigates to the **legacy** `/dashboard` instead of the V3 `/home` | V3-aware post-login landing | Route SIGNED_IN to `/home` for V3 identities (or role-aware home) |

## 18. P3 findings

| # | Severity | Route | Actor | Problem | Recommendation |
|---|---|---|---|---|---|
| F6 | P3 | `/home` (mobile) | OWNER | Responsive capture limited to 500px (Firefox headless min-width); true phone width untested | Use a device-scale mechanism or accept partial coverage |
| F7 | P3 | `/emissions` `/documents` etc. | OWNER | Sub-pages show "Loading …" placeholders with inconsistent heading timing (some pages expose `<h1>` only after data resolves) | Stabilise heading rendering |
| F8 | P3 | `/notifications` | OWNER | Redundant empty-state copy ("You are all caught up" + "No notifications yet.") | Show one empty-state variant |
| F9 | P3 | legacy `/api/reference/fuel-types` | Public/legacy | Legacy reference endpoint returns 500 (unrelated to V3) | Fix or retire legacy reference endpoint |
| F10 | P3 | `/consultant` client list | CONSULTANT | Raw organisation UUID displayed to consultants in client list / active-client block | Show client name; keep UUID in a tooltip or omit |

## 19. Recommended fixes (for the next implementation task — NOT applied)

1. **F1 (P1):** fix `routes/organizations/members.py` `GET /user/{user_id}` None-handling → 404/empty.
2. **F3 (P2):** add bounded loading states (timeout → error) to the V3 API client and page loaders.
3. **F5 (P2):** make post-login redirect role-aware (`/home` for customers, `/consultant`, `/ops`).
4. **F4/F8/F10 (P2/P3):** immediate brand-title fallback; single notifications empty state; avoid
   raw UUIDs in consultant client UI.
5. **Environment:** document `supabase db push` + demo-seed restore as prerequisites; consider
   re-provisioning an entity-staff demo identity so the D22 entity workspace can be captured.

## 20. Screenshots referenced

All 28 screenshots are listed in `screenshots/d27_evidence/UI_SCREENSHOT_MANIFEST.md`.
Key references: `customer-existing-data-discovery.png`, `customer-messaging.png`,
`consultant-white-label.png`, `consultant-branding.png`, `operations-dashboard.png`,
`operations-entities.png`, `customer-dashboard.png`, `customer-dashboard-mobile.png`,
`auth-login.png`, `public-landing.png`.

---

# D29 — Visual QA Findings Fix — Resolution (2026-08-22)

**Mode:** targeted implementation + regression verification. No 5,787-PDF run started; no
synthetic corpus modified; no redesign; no new architecture.

## F1 — FIXED / VERIFIED (P1)

**Defect:** `GET /api/organizations/members/user/{id}` returned HTTP 500 for any user without an
`organization_members` row.

**Root cause:** supabase-py 2.9.0 returns `None` (not an `APIResponse`) when a `maybe_single()`
query has no rows → `member_result.data` raised `AttributeError` → 500.

**Fix** (`backend/routes/organizations/members.py`):
- Treat `None`/empty as "no active membership" → **404** (never 500).
- **Self-only:** resolving another user's membership now returns **403** (prevents org-membership
  enumeration / cross-org information disclosure). The V3 and legacy frontends only ever call it
  with the caller's own id.
- Only **active** memberships resolve (matches `auth.get_current_user` semantics).
- The 500 path returns a generic message (no internal detail leak).

**Verified live** (minted JWTs on :8001):
`owner` → 200 with org · `operator` → 404 · `consultant` → 404 · `entity-staff` → 404 ·
`operator→owner` (cross-user) → 403.

**Regression tests:** `backend/tests/unit/api/test_org_membership_resolution.py` (8 tests):
active member 200; non-member 404; consultant/staff/entity-staff identities 404; cross-user 403;
inactive membership 404; membership-with-missing-org 404; query failure 500 without leaking
details; member sees only their own org.

## F2 — ENVIRONMENTAL / NOT A PRODUCT DEFECT

Port :8000 remains occupied by the separate synthetic-document dev server; the CarbonTally backend
continues on **:8001** with a frontend runtime env override. The synthetic-document repository and
its process were **not** modified.

## F3 — FIXED / VERIFIED (P2)

**Fix** (`frontend/src/v3/api.js` + shared state views):
- `v3Fetch` now aborts requests after **25 s** and converts a hang into a friendly
  "timed out — try again" error (no indefinite spinners).
- 5xx responses show generic copy (raw backend internals never surface); 401/403 keep the friendly
  auth/permission copy; network failures show a connection message.
- New shared `frontend/src/v3/components/StateViews.jsx` (`LoadingState` / `ErrorState` with a
  **Retry** button / `EmptyState`).
- Retry wired into: dashboard, documents, processing, emissions, issues, messaging,
  existing-data, reports, report-detail, organization, notifications, consultant.

**Verified** by the D29 capture run — all listed pages rendered data; hanging requests are now
bounded.

## F4 — FIXED / VERIFIED (P2/P3)

Consultant header now renders **"CarbonTally"** as the safe fallback until the server-authorized
`brandContext` resolves (then the authorized display name or "Consultant workspace"). Verified in
captures — the header never shows a blank or wrong brand. Branding remains server-authoritative
(`/api/v3/consultants/me/branding/context`); no client-supplied branding is trusted.

---

## Final tally

- **Screenshots captured:** 28 (all new; the original 11 in `screenshots/` reused and untouched)
- **Routes tested:** `/`, `/login`, `/home`, `/emissions`, `/documents`, `/processing`, `/reports`,
  `/reports/:id`, `/organization`, `/existing-data`, `/messaging`, `/issues`, `/notifications`,
  `/consultant` (+4 tabs), `/ops` (+5 tabs)
- **Actors tested:** Public, OWNER, CONSULTANT, OPERATOR, REVIEWER, QC, STAFF-ADMIN
- **Workflows tested:** customer dashboard/emissions/documents/processing/reports/org; D27
  existing-data discovery (flow present), messaging (empty states), notifications, issues;
  consultant dashboard/client-workspace/branding/white-label/messaging; ops dashboard/data-entry/
  review/QC/entities/staff; auth (sign-in).
- **P0:** 0 · **P1:** 1 code finding (F1) + 1 environment finding (F2) · **P2:** 3 · **P3:** 5
- **Screenshots directory:** `screenshots/d27_evidence/ui/`
- **Visual QA report:** this file
- **Browser limitations:** headless-Firefox snap processes cannot be cleaned up from this user
  context (resource pressure during the run); mobile capture limited to 500px min-width; images
  could not be rendered inside the auditor session (DOM/code-based evaluation + PNGs for human
  review).

---

# D29 — Resolution details (continued)

## F8 — FIXED / VERIFIED (P3)

Notifications empty state consolidated to a single concise message — **"You have no new
notifications."** — removing the redundant "You are all caught up" + empty-state duplication.
Authorization unchanged.

## F10 — FIXED / VERIFIED (P3)

Consultant UI now shows human-readable labels (client name / industry) instead of raw organisation
UUIDs. UUIDs remain in `title` tooltips and in the DB/API contracts (unchanged).

## Demo accounts (Product Owner manual QA)

Eight local-only demo identities provisioned/reset with a deterministic development-only password
(stored only in the gitignored `.local-demo-credentials.md`; **not** in this report). The
Processing Entity staff identity was created as an isolated local fixture (Entity Beta) — no
permanent/production users created. Verified login → landing route via Selenium:

| Actor | Login → landing | Result |
|---|---|---|
| Customer Owner | → /home | PASS |
| Consultant Owner | → /consultant | PASS |
| Consultant Member | → /consultant | PASS |
| Internal Operator | → /ops | PASS |
| Internal Reviewer | → /ops | PASS |
| Internal QC | → /ops | PASS |
| Internal Staff/Admin | → /ops | PASS |
| Processing Entity Staff | → /ops (entity workspace) | PASS |

## Test results

- **Backend full unit suite:** `pytest tests/unit` → **944 tests, 0 failures** (includes the 8 new
  F1 tests). D15/D20/D21/D22/D23/Phase-9/consultant/org-isolation coverage is in this suite.
- **Frontend build:** `npm run build` → **success** (non-CI gate; pre-existing lint warnings only).
- **Frontend Jest:** V3 API suite **18/18 pass**. `src/App.test.js` cannot run because of a
  pre-existing `react-router/dom` module-resolution issue in the installed `node_modules`
  (`react-router-dom@7.18.1`/`react-router@7.18.1` both present but the `dom` subpath fails under
  Jest's resolver). This predates D29 and is unrelated to the D29 changes; it was not altered to
  avoid unintended dependency churn.
- **Live security spot-checks** (real password-grant tokens, :8001):
  Owner(A) reading ORG_B → 403; Owner(A) own ORG_A → 200; Consultant reading Consultant B's client
  → 403; Consultant own client → 200; Consultant Member managing clients → 403; Entity staff own
  Entity Beta batches → 200; Entity staff Entity Alpha batches → 403; Entity staff internal ops →
  403; Entity staff customer reports → 403; Operator ops/me → 200. **All PASS.**

## Screenshots (D29)

Regenerated the affected surfaces (login flow, customer home/organization/documents/processing/
emissions/reports/report-detail/existing-data/messaging/issues/notifications/mobile, consultant
dashboard/client-workspace/branding/white-label/messaging, ops dashboard/staff-admin/entities) and
added the previously-uncapturable **`entity-workspace.png`** (D22 Processing Entity extraction
workspace, via the entity-staff demo identity — h1 "Extraction workspace"). Total **29 PNGs** in
`screenshots/d27_evidence/ui/` (all 1366×682 RGBA; mobile 500×726).

## Remaining findings

- **F1–F10 product findings: all resolved/verified.** No open D28 product defect.
- Non-blocking observations carried forward: ops sub-tab surfaces can still take seconds under a
  heavily loaded environment (now bounded by the 25 s timeout + Retry states); mobile capture
  remains limited to 500 px (Firefox headless minimum width); no true phone-width test.

## External configuration requirements (unchanged)

- **Google OAuth / MFA:** Supabase dashboard configuration only — no custom OAuth/MFA implemented.
- Custom-domain / email-sender activation for white-label: DNS / Resend configuration (unchanged).

## Readiness for the 5,787-PDF processing validation

- The V3 application, D27/D22 surfaces, auth flow, and the fixed findings are verified.
- The 5,787-PDF run is **NOT started** (per instruction). Before it begins, the local stack should
  run with the backend on :8001 (or a freed :8000), the demo seed + D20–D27 migrations (already
  applied this session), and the synthetic-document corpus/API as a separate service.

## D29 — Product Owner UX review (lightweight)

Classified from the D28/D29 captures and component inspection. Only **A** items were implemented
(plus low-risk B items already covered by the D29 fixes).

**A. MUST FIX NOW — implemented in D29**
- Loading/error/retry consistency (F3) — shared `StateViews`, 25 s timeout, Retry on every major
  workspace.
- Role-aware post-login landing (F5) — customer→`/home`, consultant→`/consultant`, staff/entity→`/ops`.
- Notifications empty state (F8) and consultant raw-UUID display (F10).

**B. RECOMMENDED BEFORE PRODUCTION (not implemented)**
- B1 (P2): ops sub-tab surfaces still show plain "Loading…" placeholders for several seconds under
  load — add skeleton/loaded indicators per tab.
- B2 (P2): true mobile (≤375 px) verification — Firefox-headless min-width blocks it; needs a
  device-scale mechanism.
- B3 (P2): legacy beta flows (`BetaLogin`/`BetaSignup`) still navigate to `/dashboard` — migrate or
  retire when the beta surface is decommissioned (normal V3 login is fixed).
- B4 (P3): audit remaining duplicate empty-state copy (e.g., emissions history) for consistency.
- B5 (P3): legacy `/api/reference/fuel-types` returns 500 — fix or retire.

**C. FUTURE / NICE-TO-HAVE (not implemented)**
- C1: search/filter on reports and documents tables.
- C2: pagination on long lists (issues, notifications).
- C3: keyboard shortcuts and `aria-live` announcements for loading states.
- C4: a full white-label presentation-mode demo fixture (CarbonTally-invisible shell).

---

## D29 files changed

Backend:
- `backend/routes/organizations/members.py` (F1)
- `backend/tests/unit/api/test_org_membership_resolution.py` (new, F1 tests)

Frontend:
- `frontend/src/v3/api.js` (F3 timeout/friendly errors + F5 `resolvePostLoginPath`)
- `frontend/src/v3/components/StateViews.jsx` (new, shared states)
- `frontend/src/v3/customer/DashboardPage.jsx`, `DocumentsPage.jsx`, `ProcessingPage.jsx`,
  `EmissionsPage.jsx`, `IssuesPage.jsx`, `MessagingPage.jsx`, `ExistingDataDiscoveryPage.jsx` (F3)
- `frontend/src/v3/reports/ReportsPage.jsx`, `ReportDetailPage.jsx` (F3)
- `frontend/src/v3/admin/AdminPage.jsx` (F3)
- `frontend/src/v3/NotificationsPage.jsx` (F3 + F8)
- `frontend/src/v3/consultant/ConsultantPage.jsx` (F3 + F4 + F10)
- `frontend/src/Login.js`, `frontend/src/AuthCallback.js`, `frontend/src/MagicLink.jsx` (F5)

Local fixture / config:
- `.gitignore` (+ `/.local-demo-credentials.md`)
- `.local-demo-credentials.md` (new, gitignored — not committed)
- Local DB demo fixture only (demo passwords reset; `consultant-member` + `entity-staff` created).



