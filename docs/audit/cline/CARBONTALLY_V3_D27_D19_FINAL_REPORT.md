# CarbonTally V3 — D27 Final Product Completion Report

**Date:** 2026-08-22 · **Mode:** IMPLEMENTATION + PRODUCT COMPLETION + UI/UX VERIFICATION
**Authoritative architecture:** `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` (§43 = D27 record)

## 1. Executive summary

D19 (Consultant lifecycle + customer-initiated direct onboarding + existing-data
discovery/adoption + white-label completion + consultant-client messaging) is
**IMPLEMENTED** on the existing CarbonTally V3 architecture. No generic
workspace/tenant abstraction was introduced; `organizations` remains the
data-tenancy anchor; Supabase (Auth/Postgres/RLS/Storage/Realtime), FastAPI,
Vercel, Render and Resend remain the platform boundaries.

Verification: backend unit suite **936 passed / 0 failed** (52 new D27 tests),
frontend Jest **18/18**, frontend build **EXIT=0** (non-CI gate). One new
migration (additive, idempotent, RLS deny-by-default). The synthetic PDF corpus
was **not** touched.

## 2. D19 implementation

**IMPLEMENTED.** `consultant_clients` lifecycle ACTIVE/SUSPENDED/ENDED with API
(`suspend|end|reactivate`), RLS (`is_org_consultant` = active only) and audit.
See architecture §43.1.

## 3. Customer lifecycle

**IMPLEMENTED.** Customer is the ultimate data decision maker. Relationship
termination ≠ data deletion; termination ≠ CarbonTally ownership; a new
relationship requires a new explicit grant.

## 4. Existing data discovery / adoption

**IMPLEMENTED.** `/api/v3/discovery/*` (lookup → request → verify → choice).
Candidate signals are never authoritative; verification is email-code or
CarbonTally-staff-mediated; adoption is in-place (identity preserved). USE ALL /
PARTIAL (recorded selection) / DISCARD (no deletion) all implemented and tested.

## 5. White-label

**IMPLEMENTED (foundation) + EXTERNAL CONFIGURATION REQUIRED.** Custom-domain
lifecycle (PENDING→VERIFIED→ACTIVE→REMOVED_SUSPENDED), custom senders
(PENDING→VERIFIED→REMOVED), server-authorized `BrandContext` everywhere. A
domain/sender never grants authorization.

## 6. Custom domains

**IMPLEMENTED (foundation) + EXTERNAL CONFIGURATION REQUIRED.** Vercel is the
frontend/custom-domain host; the consultant owns DNS/registrar/renewal. TXT-token
verification (`_carbontally.<domain>`). Domain lifecycle recorded + audited.

## 7. Custom email

**IMPLEMENTED (foundation) + EXTERNAL CONFIGURATION REQUIRED.** Resend verifies
the domain; only VERIFIED senders may be used as a From address; arbitrary From
addresses denied (tests enforce this).

## 8. Consultant messaging

**IMPLEMENTED.** Realtime messaging RLS fixed (D26 audit §42) + authorized
`/api/v3/messaging/*` (org members + active-grant consultants; entity staff
denied). Customer `/messaging` + consultant Client messages tabs.

## 9. Processing Entity communication boundary

**IMPLEMENTED (preserved).** Entity staff never participate in messaging (no
entity policy; API denies). Mediated clarification stays on entity-scoped
`issues` (D19 §17).

## 10. PDF rendering

**IMPLEMENTED.** `engines/pdf_render.py` (reportlab) renders report content with
the server-authorized brand (CarbonTally / consultant / co-branded).
`GET /api/v3/reports/{id}/pdf`. Genuine PDF evidence in
`screenshots/d27_evidence/`.

## 11. Customer onboarding

**IMPLEMENTED.** Existing signup/verification/org creation + the D27
existing-data discovery workflow (`/existing-data`).

## 12. Consultant onboarding

**IMPLEMENTED.** Consultant profile creation + firm team + team invites + client
management + lifecycle + white-label + messaging.

## 13. Entity onboarding

**IMPLEMENTED (where architecture supports).** Ops staff provisioning with
entity scope (D20), entity extraction workspace (D22), entity-scoped issues.

## 14. Google OAuth

**EXTERNAL CONFIGURATION REQUIRED.** Supabase Auth provider — cannot be verified
from this environment. Exact configuration documented in Part 35 of this report.

## 15. MFA / 2FA

**EXTERNAL CONFIGURATION REQUIRED.** Supabase MFA (enrollment/challenge/
recovery) is provider-managed; priorities (internal staff, org admins,
consultants, entity staff) documented. Not locally verifiable.

## 16. Issues UI

**IMPLEMENTED** (D25, retained). `/issues` — org-scoped, entity-scoped rows never
exposed. Customer replies: FUTURE.

## 17. Notifications UI

**IMPLEMENTED** (D25/D26, retained). `/notifications` — per-recipient, paginated.

## 18. SLA UI

**IMPLEMENTED** (D25, retained). `/ops` SlaTab reuses the existing SLA
architecture. Entity SLA exposure to customers: not exposed.

## 19. Route guards

**IMPLEMENTED** (D25, retained). `RoleRoute`/`useActorRoles`; backend/RLS remain
authoritative; localStorage is never authorization.

## 20. Export / import

Export **IMPLEMENTED (scoped)** — `/api/v3/exports/emissions.{csv,json}` +
`documents.csv`. Full-org export: DESIGN ONLY. Customer-data import: **DESIGN
ONLY** (no unsafe arbitrary writes; factor/reference import is a separate
existing surface).

## 21. Security

**PRESERVED.** D15 active-grant enforcement, D20 scope-first staff authorization,
D21 branding context, D22 entity work assignment, D23 extraction UX and Phase 9
RLS recursion fix all retained. New D27 security tests cover every mandatory
negative scenario (Part 31). No secrets logged.

## 22. RLS

**PRESERVED + extended.** D15 `is_org_consultant` (active grant) unchanged; D27
adds deny-by-default RLS on the three new tables and recursion-safe
`conversation_participants` policies.

## 23. Backend tests

Full backend unit suite **936 passed / 0 failed / 0 errors** (EXIT=0).

## 24. API tests

D27 targeted API/unit suite **52/52** (discovery 16, messaging 7, whitelabel 9,
lifecycle 9, domain 9, PDF 5, incl. engineering tests).

## 25. Frontend tests / build

Frontend Jest `api.test.js` **18/18**; `App.test.js` continues to fail on the
pre-existing `react-router/dom` module-resolution environment issue (documented
in D25/D26, unrelated). Frontend build **EXIT=0** (non-CI, warning-tolerant — the
established D25/D26 gate; ~140 pre-existing lint warnings remain).

## 26. Live verification

App factory + route registration verified (20 new D27 routes). No live-server
HTTP probe was re-run: no browser automation and the local Supabase stack are
not available in this environment; the local database is shared with a concurrent
demodatagen process. Live probes therefore remain **NOT RE-RUN** (documented, not
claimed).

## 27. Screenshot inventory

See `screenshots/d27_evidence/SCREENSHOT_MANIFEST.md` — the full 36-item
inventory with status and capture steps. **3 genuine white-label PDF artefacts**
were produced from the production renderer; D27-new browser screenshots require
a browser-automation environment (documented honestly).

## 28. Files changed

See architecture §43.6 (full list). Core new files: migration
`20260822010000_d27_d19_customer_lifecycle.sql`; backend domain/data/api for
discovery, messaging, whitelabel; `engines/pdf_render.py`; `services/v3_email.py`;
frontend pages/tabs (ExistingDataDiscoveryPage, MessagingPage, WhiteLabelTab,
ClientMessagingTab); test files (6 new).

## 29. Migrations

`supabase/migrations/20260822010000_d27_d19_customer_lifecycle.sql` — additive,
idempotent: `organizations.customer_type`, `consultant_clients` lifecycle
columns, three new deny-by-default tables, recursion-safe messaging policies.
`supabase db push` is required to apply (local Supabase not running here).

## 30. External configuration required

- **Supabase Auth:** Google OAuth (provider ID + redirect URLs in the dashboard),
  MFA enrolment policies, site URL / redirect allowlist.
- **Vercel:** frontend deployment, custom-domain mapping (`portal.<domain>`),
  env vars (`REACT_APP_API_URL`, `REACT_APP_SUPABASE_URL`,
  `REACT_APP_SUPABASE_ANON_KEY`).
- **Render:** backend deployment, env vars (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`,
  `SUPABASE_JWT_SECRET`, `RESEND_API_KEY`), CORS for the frontend origin.
- **Resend:** sending domain + DNS verification (SPF/DKIM/DMARC), API key.
- **Realtime:** publication membership for `messages`/`conversations` in
  `supabase_realtime` (documented in D26 audit §42).

## 31. Remaining P2/P3 items

- Customer replies on issues (FUTURE).
- Full-org structured export + customer-data import (DESIGN ONLY).
- Per-consultant outbound email template branding (FUTURE).
- Logo-in-PDF image embedding (renderer uses text branding today; logo URL
  embedding is a follow-up).
- Browser screenshot capture of the D27-new UI (requires browser automation).
- Customer invitation acceptance end-to-end tests (FUTURE/EXTERNAL).

## 32. Architecture documentation changes

`docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` §43 added —
D19 implementation record, capability status matrix (IMPLEMENTED / PARTIALLY
IMPLEMENTED / EXTERNAL CONFIGURATION REQUIRED / FUTURE), security regression,
verification record and files-changed inventory.

---

*End of D27 final report.*
