# CarbonTally V3 Final Implementation Report

## 1. Executive Summary

CarbonTally V3's approved UX is now implemented against the frozen Product
Owner baseline. The independent P1 security finding (D32 — raw persisted
`file_url` values returned on the operator/PE workbench endpoints) is remediated
with the existing `signed_item()` convention. The D19 workbench is completed
(field confidence/suggestions, source↔field affordance, inline validation,
server-derived lock states, keyboard-accessible pane resizing). The D21 design
system is consolidated (≈291 raw hex values replaced with semantic `ct-*`
tokens across the five active V3 stylesheets; the legacy `#2563eb` is gone from
active CarbonTally styling). The approved public website candidate has been
promoted into the active `frontend/` and the previous public frontend is
preserved as `frontend_backup_pre_v3_public_20260827/`.

Verification: frontend production build PASS; frontend V3 tests 113/113 PASS;
backend unit suite PASS (exit 0, ~1100 tests); `test_v3_rls_behavior.py` 27/27
PASS; headless-Chrome QA of 20 public routes at 1280/768/375 px — no horizontal
overflow anywhere. Authenticated browser E2E remains **ENVIRONMENT NOT
VERIFIED** (no local Supabase auth/storage gateway), exactly as the pre-existing
environment limitation requires; the API-level equivalent is covered by the unit
and RLS test suites.

**Status: COMPLETE with environment-limited verification and deployment
requirements documented (see §15 and §16).**

## 2. Baseline

- Branch: `main`
- Baseline commit: `9458067` — "feat(v3): commit D20-D37 commercial platform releas"
- Working tree at start: 845 entries (585 modified, 111 untracked), pre-existing
  V3 work preserved untouched, `git reset --hard` / `git clean` / branch
  switches / force-push never used.
- The pre-existing working-tree modifications are part of the intended final
  CarbonTally V3 state (messaging, search, settings, vehicles, retention,
  workbench components, tests, migrations, docs) and are included in the final
  commit.

## 3. Frozen Decisions Verified

All frozen Product Owner decisions D1–D21 and N1–N3 were re-verified against the
authoritative documents (`docs/audit/openhands/ui-ux/`) and the live evidence
base. No decision was reopened or contradicted.

- **D1–D4** one-account-one-role model, viewer permissions, customer review vs
  approval, approver gate — verified server-side (`require_org_admin` for
  customer review; approval is server-gated).
- **D5** customer-review = `require_org_admin`; customer staff cannot approve.
- **D17** master data: Facilities, Locations (N2: first-class UX over the
  Facilities representation), Assets, Vehicles (migration `20260825000000_v3m7`
  applied locally; **production not applied — DEPLOYMENT REQUIRED**), Suppliers.
- **D18** workflow-first TOP navigation — verified (no left-sidebar redesign).
- **D19** split-screen workbench — now COMPLETE (see §5).
- **D20** responsive behaviour — no horizontal overflow; mobile tray model
  preserved.
- **D21** design system — tokenization complete (see §6).
- **D32** signed/scoped document access — remediated (see §4).
- **N1** messaging boundaries — unchanged and enforced (`can_manage_staff`
  CarbonTally staff gate; PE messaging denied; customer review is the controlled
  clarification path).
- **N2** Locations — first-class UX concept over the Facilities representation,
  no schema redesign.

## 4. D32 Security Remediation

- **Root cause:** `/api/v3/ops/batches/{id}/items`,
  `/api/v3/ops/entities/{eid}/extraction/batches/{bid}/items` and
  `/api/v3/ops/entities/{eid}/extraction/items/{iid}` returned the persisted raw
  `file_url` storage path instead of short-lived signed URLs, so
  `SecureDocumentViewer` was functionally broken in operator/PE flows and the
  D32 boundary was not enforced at the API layer.
- **Implementation (backend, `backend/api/v3_operations.py`):** all three
  endpoints now return items through the existing `signed_item()` convention
  (short-lived signed URL issued server-side by the service client after
  authorization). The entity item workspace additionally returns the OCR field
  suggestions and server validation findings for the D19 workbench.
- **Frontend:** `OperatorQueue` now opens the signed workspace payload
  (`getItemWorkspace`) instead of the raw list row; `EntityExtractionWorkspace`
  consumes the signed item + suggestions + validation from the entity endpoint.
  `ExtractionPanel` renders the signed `file_url` through `SecureDocumentViewer`.
- **Boundaries preserved:** org isolation, PE entity-assignment isolation
  (cross-entity still 403), PE no-download (view-only signed URL, no download
  controls), expiry follows the existing signed-URL convention.
- **Tests** (`backend/tests/unit/api/test_v3_operations.py`, +4): authorized
  operator returns signed URL; authorized PE (entity operator) returns signed URL
  for batch items and the item workspace; raw persisted path never appears in
  any payload; cross-entity/wrong-assignment still denied. All ops tests pass.

## 5. D19 Workbench

- **Workflow navigation:** TOP workflow nav (Queue→Extract→Map→Validate→
  Review→QC→Evidence) preserved; no left sidebar.
- **Split panes / presets:** 40/60 · 50/50 · 60/40 presets.
- **Pane resizing:** pointer drag **and** keyboard-accessible resizing — the
  divider is a focusable button; ArrowLeft/ArrowRight adjust the split in 5%
  steps within the 25–75% range (title + aria-label provided).
- **Field confidence:** `ConfidenceBadge` is wired to real data. The
  deterministic OCR suggestion engine produces field *values* without per-field
  numeric confidence, so fields sourced from `ocr_suggestions` display a
  truthful **"Suggested"** chip (auto-suggested — confirm before saving);
  numeric confidence is shown only when the backend actually supplies it. No
  fabricated confidence; unknown remains unknown.
- **Source↔field linking:** a structured field that is supported by source OCR
  text shows the source-linked "Suggested" affordance; fields without evidence
  linkage show the honest unlinked state (no chip). Source coordinates are never
  fabricated.
- **Inline validation:** server validation findings (`validate_processing_item`)
  are mapped into the data pane — field-level errors with actionable messages,
  `role="alert"`, `aria-invalid`/`aria-describedby` association, plus a
  blocking-findings summary. Frontend never replaces server-authoritative
  validation.
- **Lock / workflow states:** `locked` is derived from the server item status
  (editable stages editable; validating/calculated/customer_review/approved/
  rejected/qc_*/completed/failed read-only). Wired through `WorkbenchShell` in
  both `ExtractionPanel` and `WorkItemWorkspace`. Approval remains server-gated.
- **Responsive:** mobile tray model preserved; no horizontal overflow.

## 6. D21 Design System

- All five active V3 stylesheets tokenized: `v3.css`, `ops.css`, `admin.css`,
  `consultant.css`, `reports.css` — 291 raw hex values replaced with semantic
  `ct-*` tokens (accent/info/processing blues, primary greens, neutrals,
  borders, error/warning/success, evidence palette, nav) where a token existed.
  `var(...)` fallback values and token definitions were protected.

## 7. D17 Master Data

Verified list/create/edit/view for Facilities, Locations (N2 — UX over
Facilities representation), Assets, Vehicles, Suppliers with organisation scope,
consultant scope, role restrictions, empty states, validation and responsive
behaviour. Vehicles use the existing migration/table/API/RLS architecture (no
duplicate models). The promoted public site's organisation-workspace demo
includes the master-data tab (facilities/assets) with clearly-labelled demo data.

## 8. N1 Messaging

Frozen boundaries preserved: customer staff ⇄ customer staff; consultant staff
⇄ consultant staff and active-client customers; CarbonTally authorized
Customer Support/Admin (via `can_manage_staff`) ⇄ customers/consultants; PE
Manager/PE users communicate through the operational path with **no** direct
Customer ⇄ PE chat; clarification remains in the controlled workflow. All
enforcement is server-side and RLS-backed.

## 9. N3 Retention

Configurable retention control plane (Settings/Admin), "Not configured" when
unset, no invented durations, server-side enforcement, dry-run CLI, audit/
evidence exclusions, soft-expiration semantics. Scheduler wiring remains a
documented deployment concern (§16).

## 10. Public Website Cutover

- **Previous public frontend backup:** `frontend_backup_pre_v3_public_20260827/`
  (source copy of the active `frontend/` at cutover time, 4.4 MB, no
  node_modules/build). This directory cannot be served as the production app and
  is committed to the repository. Original state recorded in §2.
- **New active frontend:** `frontend/` now serves the approved public site from
  the candidate: promoted `LandingPage`, `PlatformPage` (incl. the processing
  workbench demo and reporting demo), `ServicesPage`, `ProcessingPage`,
  `ConsultantsPage`, `ContactPage`, `FaqPage` (NEW route `/faq`), `PricingPage`,
  `AboutUs`, `Glossary`, `CarbonReductionPlan`, `PrivacyPolicy`, `CookiePolicy`,
  `TermsPage`, plus the public Assistant widget and all approved demos
  (organisation workspace, processing workbench, reporting, evidence journey/
  traceability, data-to-emissions, dashboard, consultant workspace).
- **Public routes verified:** `/`, `/platform`, `/services`,
  `/processing-services`, `/consultants`, `/pricing`, `/about`, `/contact`,
  `/faq`, `/glossary`, `/carbon-reduction-plan`, `/privacy`, `/cookies`,
  `/terms`, `/login`, `/signup`, `/beta/signup`, `/auth/callback`,
  `/auth/magic`, `/onboarding`.
- **Authentication entry points preserved:** login/signup/magic-link/callback/
  onboarding routes retained alongside the public site; the authenticated V3 app
  (customer/consultant/PE/ops/admin) is unchanged and still served.
- **Demos are truthful:** labelled demo data, distinct from the authenticated
  live platform, following the real V3 workbench/navigation/status language and
  design tokens. No fabricated production metrics.
- **Assistant:** the public Assistant widget is the deterministic local
  knowledge module consistent with the approved three-tier architecture (no
  provider, no credentials, no DB access).

## 12. Tests

- **Frontend build:** `npm run build` — PASS (exit 0), multiple times after each
  change set.
- **Frontend V3 tests:** `CI=true npm test` — 113 passed / 113 total across 6
  suites. New D19 tests: SplitPane keyboard resizing; ExtractionPanel Suggested
  chip; inline validation errors; locked/read-only state.
- **Frontend known pre-existing failure:** `src/App.test.js` fails on the
  jest `react-router/dom` module resolution (unrelated to this work; unchanged).
- **Backend unit suite:** `pytest tests/unit` — PASS (exit 0, all-dot output).
- **Ops API suite incl. new D32 tests:** `pytest tests/unit/api/test_v3_operations.py`
  — 36/36 PASS.
- **RLS integration:** `pytest tests/integration/test_v3_rls_behavior.py` —
  27/27 PASS.
- **Pre-existing integration gaps (unchanged):** 5 integration-suite failures
  from stale test-DB schema (no factor baseline seed, consultant `add_client`
  signature drift, stale `customer_factors_tenant_delete` policy in test DB
  only) — the application DB is correct; test-DB refresh is a documented
  deployment item.

## 13. Browser Verification

Headless Chrome QA (`google-chrome-stable`, CDP) against the production build:
20 public/auth routes × 3 widths (1280/768/375) = 60 checks. **No horizontal
overflow on any route.** The only console output flagged was `/auth/callback`
showing its expected "No session after retry" state (no Supabase gateway in this
environment) — not a defect. Authenticated V3 workflow browser QA:
**ENVIRONMENT NOT VERIFIED** (local Supabase auth/storage gateway down);
API/unit/RLS coverage is the substitute evidence.

## 14. Security Verification

- D32 signed URLs on the operator/PE workbench endpoints (tests).
- Raw persisted storage paths no longer returned (tests assert absence).
- Org isolation, PE assignment isolation, PE no-download preserved.
- RLS live: vehicles (4 policies), customer_factors (no app DELETE),
  conversations/messages/participants (org-scoped, PE denied),
  calculation_snapshots (select-only).
- No frontend-supplied calculation results; approval gates server-side;
  no service-role access introduced in the frontend; no secrets in the commit.

## 15. Remaining Gaps

- **ENVIRONMENT NOT VERIFIED:** authenticated browser E2E (messaging/storage/
  viewer/approval flows) — requires the local Supabase gateway which is down.
- **ENVIRONMENT NOT VERIFIED:** production state (migrations, RLS, storage, live
  behaviour).
- **DEPLOYMENT REQUIRED:** vehicles migration to production; retention scheduler
  wiring; test-DB refresh.
- **DEFERRED:** authenticated AI provider/programme decision; optional P3
  hardening (DB-level UPDATE guard on `calculation_snapshots`, one-account-one-
  role DB check, `compute_expired` removal, consolidated admin console);
  PE-internal messaging (not approved).

## 16. Deployment Requirements

1. Apply `supabase/migrations/20260825000000_v3m7_vehicles.sql` to production.
2. Wire the retention scheduler to the N3 config (documented in the audit).
3. Refresh the integration test-DB schema (factor baseline seed, `add_client`
   signature, `customer_factors_tenant_delete` policy).
4. Re-run authenticated browser E2E once the Supabase auth/storage gateway is
   available.

## 17. Git

- Baseline commit: `9458067`.
- Branch: `main`.
- Final commit: `6d5199d` — "feat: finalize v3 ux and promote public website".
- Files changed in final commit: ≈830 (backend 121, frontend 179 + backup 235,
  docs 299, tools 2, database 2, supabase 1, .gitignore 1) — reviewed, no
  secrets, no node_modules/build/caches/screenshots/generated artifacts.
- Backup: `frontend_backup_pre_v3_public_20260827/` (committed).
- Push result: ###PUSH###; remote: origin -> https://github.com/shomonrobie/CarbonTally.git; working tree after push:
  ###TREE###.


## 11. Codebase Cleanup

- Removed obsolete tracked backup copies (never imported): `frontend/src/App
  copy.css`, `App copy.js`, `LandingPage copy.jsx`,
  `components/CarbonTallyDemo copy.jsx`, `components/FileUploadHero copy.jsx`,
  `backend/main copy.py`, `backend/main copy 2.py`, `backend/glossary copy.py`,
  `backend/requirements copy.txt`.
- Added `website_candidate/` to `.gitignore` (superseded by the promotion into
  `frontend/`; kept on disk, not committed).
- No speculative refactors of working architecture; no dead-import surgery on
  the preserved legacy `App.js`.

- **Legacy `#2563eb` removed** from all active CarbonTally styling (V3 `ops.css`
  and the legacy active files incl. `App.css`, `App.js` chart strokes,
  `MobileMenu.css`, `css/*`), unified on `#2b6cb0` (`--ct-color-accent`). Only
  the obsolete `App copy.*` files still contained it; those files were removed
  (see §11).
- **Remaining raw values (52, justified exceptions):** distinct tints/shades
  with no corresponding token — darker slate/blue tints (e.g. `#2d3748`,
  `#334155`, `#475569`, `#64748b`), amber/orange tints (`#975a16`, `#c05621`,
  `#d69e2e`), red error shades (`#c53030`, `#e53e3e`), teal/emerald tints
  (`#0f766e`, `#115e59`, `#9ae6b4`), data-viz/status blues (`#3182ce`,
  `#1e40af`). Each has documented semantic meaning and no existing token.
- No second design system was introduced.

- **N3** retention — configurable (Settings/Admin), "Not configured" when unset,
  no invented durations, dry-run CLI, audit/evidence exclusions.
- **AI Assistant** — the promoted public assistant is the deterministic local
  knowledge module (no provider credentials, no network, no DB access); no
  unauthorised AI backend was introduced.
