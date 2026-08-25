# CarbonTally V3 — D32 Final Product Completeness & Production Readiness Audit

**Date:** 2026-08-23 · **Mode:** audit-first (fix only clear P0/P1 defects)
**Author:** Cline

---

## 1. Executive verdict

CarbonTally V3 is **functionally complete for a controlled production launch** of the core
customer / consultant / operations / processing-entity product: every ratified business flow is
implemented, server-side authorized, RLS-protected and covered by an automated test suite
(983 backend unit tests + 11 RLS integration tests + 18 frontend API tests, all green at audit
time).

**One P0 security defect was found and FIXED during D32:** customer documents were stored in a
PUBLIC Supabase Storage bucket and served via public URLs with no storage RLS — customer data
confidentiality risk. The bucket is now PRIVATE with org-scoped storage RLS and all document
access is via short-lived signed URLs (verified end-to-end).

**Launch blockers:** the remaining items are production-configuration (Supabase auth
redirects / Google OAuth / MFA / templates, Resend domain, Vercel/Render env, Stripe), not
functional gaps. Billing is schema-ready but requires application changes + Stripe integration
(PARTIALLY READY).

## 2. Product completeness scorecard

| Dimension | Verdict |
|---|---|
| Customer product | IMPLEMENTED (signup→export journey complete; email verification = external config) |
| Consultant product | IMPLEMENTED (D15/D19/D21/D27 semantics preserved) |
| Processing Entity product | IMPLEMENTED (isolated; clarification mediated) |
| Internal Operations | IMPLEMENTED (ops hub + D30/D31 reporting) |
| Authentication | IMPLEMENTED (Supabase Auth); Google OAuth/MFA = EXTERNAL CONFIGURATION REQUIRED |
| Authorization / security | IMPLEMENTED (actor matrix verified); storage fixed in D32 (P0) |
| Storage / documents | IMPLEMENTED after D32 P0 fix (private bucket + signed URLs) |
| Processing pipeline | IMPLEMENTED (state machine + validation + retry fields) |
| Messaging / Realtime | IMPLEMENTED (RLS-scoped); production Realtime = external config |
| White-label | IMPLEMENTED (D21/D27); DNS/mail = consultant responsibility (ratified K) |
| Reporting | IMPLEMENTED (D30/D31 verified intact) |
| Onboarding / existing-data | IMPLEMENTED (D19 discovery, USE ALL / PARTIAL / DISCARD = customer decision) |
| Notifications / email | PARTIALLY IMPLEMENTED (in-app done; templates generic; Resend = external config) |
| Reports / PDF | IMPLEMENTED (generation + branded PDF + versioning) |
| Export / portability | PARTIALLY IMPLEMENTED (CSV/JSON; no binaries/provenance) |
| Database / migrations | IMPLEMENTED (D31 dedicated test DB fix authoritative) |
| Billing / Stripe | PARTIALLY READY FOR STRIPE INTEGRATION (schema-ready; no API/UI/gating) |
| Vercel / Render / Supabase / Resend | EXTERNAL CONFIGURATION REQUIRED (env prepared) |
| Backup / disaster recovery | MISSING — P2 (no documented procedure; Supabase provides the capability) |
| Performance / reliability | PARTIALLY IMPLEMENTED (aggregates/pagination OK; sync engine + upload limits = post-launch) |
| Observability | PARTIALLY IMPLEMENTED (logging/health/audit present; alerting = external) |
| UX / product completeness | IMPLEMENTED (D28–D31 evidence; legacy beta surfaces remain = P2/P3) |

## 3. Customer product (Part 4)

| Step | API | UI | Classification |
|---|---|---|---|
| Signup | Supabase signUp | Login.js | IMPLEMENTED |
| Email verification | Supabase confirm | AuthCallback.js | IMPLEMENTED (EXTERNAL CONFIGURATION REQUIRED for confirm-email + redirect URLs) |
| Login | signInWithPassword | Login.js | IMPLEMENTED |
| Password reset | resetPasswordForEmail | MagicLink.jsx | IMPLEMENTED (EXTERNAL CONFIGURATION REQUIRED for reset-email) |
| Organisation creation | legacy + resolveV3Organization | App.js / V3 layout | IMPLEMENTED |
| Organisation settings | `/api/v3/organizations/*` | `/organization` | IMPLEMENTED |
| Invite members | `POST /api/v3/organizations/{id}/invitations` | `/organization` Members | IMPLEMENTED |
| Member management | members endpoints | `/organization` | IMPLEMENTED |
| Upload documents | `POST /api/v3/uploads` | `/documents` | IMPLEMENTED (D32: private storage + signed URLs) |
| Document processing | `/api/v3/processing/*` | `/processing` | IMPLEMENTED |
| Extraction/mapping/validation | `/api/v3/processing/items/{id}/workspace` + workflow | `/processing` | IMPLEMENTED |
| Review (customer) | customer-review endpoint | `/processing` | IMPLEMENTED |
| Issues | `/api/v3/issues` | `/issues` | IMPLEMENTED |
| Calculation | `/api/v3/emissions/calculate` | `/emissions` | IMPLEMENTED |
| Emissions | `/api/v3/emissions/*` + exports | `/emissions` | IMPLEMENTED |
| Reports | `/api/v3/reports` | `/reports` | IMPLEMENTED |
| PDF | `/api/v3/reports/{id}/pdf` | ReportDetailPage | IMPLEMENTED |
| Export | `/api/v3/exports/*` | `/emissions` | IMPLEMENTED (CSV/JSON; no binaries — see §17) |
| Notifications | notifications API | NotificationsPage | IMPLEMENTED |
| Messaging | `/api/v3/messaging/*` | `/messages` | IMPLEMENTED (RLS-scoped) |
| Account management | Supabase + profile endpoints | V3 layout | IMPLEMENTED |

## 4. Consultant product (Part 5)

All ratified semantics verified in the current code + tests:
- ACTIVE grant = access; SUSPENDED/ENDED = no access (D15/D19 — verified by D30/D31 tests and the
  D31 live smoke: ended client → 403, non-granted client → 404).
- Firm creation/members/permissions (`consultant_profiles` + `consultant_firm_members` flags),
  client lifecycle (create/activate/suspend/end/reactivate), portfolio + per-client drill-down
  (D30/D31), client processing/reporting/messaging, branding/white-label (D21/D27),
  client-becoming-direct-customer via D19 discovery (USE ALL / PARTIAL / DISCARD = customer
  decision; no silent data deletion).

**Verdict: IMPLEMENTED.** No regressions found.

## 5. Processing Entity product (Part 6)

Provisioning, admin/staff, assignment (D22), entity workspace (D24), extraction/mapping/
calculation, mediated clarification (entity-scoped issues — no direct customer/consultant
contact), CarbonTally review/QC, completion, entity performance reporting (D30/D31).

Isolation verified: entity A vs B (403), entity staff vs customer orgs (403), entity staff vs
internal reporting (403), entity staff vs messages (entity is not org member/consultant → RLS
denies). **Verdict: IMPLEMENTED.**

## 6. Internal CarbonTally Operations product (Part 7)

Ops hub (Dashboard/Data entry/Review/QC/Staff/Roles/Entities/SLA), queues, issues, staff
management, entities, customers/consultants lists, notifications, audit (D31), reporting
(D30/D31), SLA fields. Staff permissions map to roles (`can_process` / `can_review` /
`can_manage_staff` / `can_view_all`).

**Residual:** legacy beta `/dashboard/*` monolith surfaces remain reachable (superseded by V3) —
retire/redirect = P2/P3 backlog item (not a launch blocker for the V3 surfaces).

**Verdict: IMPLEMENTED** (legacy retirement = P2/P3).

## 7. Authentication (Part 8)

Supabase Auth is the provider (no replacement built). Email/password, email confirmation,
password reset, sessions (supabase-js + JWT), logout, expired/invalid JWT (401), role/scope
resolution (`auth.py`), organisation membership resolution — all IMPLEMENTED. Google OAuth UI is
## 8. Authorization / security (Part 9)

Server-side actor matrix verified (existing suites + D28/D29/D30/D31 live checks): customer A ↔
B, consultant A ↔ B, consultant→inactive/ended clients, entity A ↔ B, entity→customer,
entity→consultant, entity→internal work, internal→entity, admin→restricted, ordinary staff→admin
resources. All enforced by API guards + RLS; no frontend-only assumptions. Storage authorization
was the one gap (P0 — FIXED in D32). **Verdict: IMPLEMENTED.**

**Defense-in-depth note (P3):** `messages_tenant_insert` has an empty RLS qual (participant
membership is enforced by the API layer); add a participant-check qual to the policy for direct
PostgREST inserts.

## 9. Storage / documents (Part 10) — P0 FIXED in D32

**Finding (P0):** the `documents` Supabase Storage bucket was PUBLIC, had zero storage RLS
policies, and `v3_documents.py` served objects via `get_public_url` — customer documents were
downloadable by anyone with the URL (no auth, no expiry, no revocation).

**Fix implemented and verified:**
1. `supabase/migrations/20260823000000_d32_private_documents_storage.sql` — bucket → PRIVATE +
   4 org-scoped `storage.objects` RLS policies (SELECT/INSERT/UPDATE/DELETE under
   `uploads/<org_id>/` for org members).
2. `backend/services/storage.py` — `path_from_url` + `storage_signed_url` + `signed_item`.
3. `v3_documents.py` — uploads store canonical paths; pipeline items store paths; new
   `GET /api/v3/documents/{id}/signed-url` (org-member gated).
4. `v3_operations.py` / `v3_processing_workflow.py` — workspace responses return fresh signed
   URLs for `file_url`/`viewer_url`.

Live verification: upload → signed URL; owner signed-url 200; non-member **403**; legacy public
URL **blocked (400)**; signed URL fetch 200; pipeline workspace returns signed URLs that fetch
200.

**Residual (P2/P3):** no file-size limit on upload; no duplicate-content detection; no
`storage.objects` cleanup when `organization_files` rows are deactivated.

## 10. Processing pipeline (Part 11)

State machine (ITEM_STATUS_FLOW), validation with blocking findings (routed back to mapping),
calculation error handling, `workflow_error_count`/`workflow_next_retry_at` on the document
queue, synchronous report generation with persisted QUEUED→READY/FAILED lifecycle, audit trail
(write-side `audit_trail`). Duplicate submission protection via status-transition enforcement.
**Verdict: IMPLEMENTED.** Retry automation + async worker queue = POST-LAUNCH (not invented
during D32).

## 11. Messaging / Realtime (Part 12)

Conversations/messages/participants RLS-scoped (`is_org_member` OR `is_org_consultant`; updates
org-member-only); customer↔consultant where authorized; customer A ↔ B and consultant A ↔ B
isolated; entities have no message access. Realtime publication via client-side
`postgres_changes`. **Verdict: IMPLEMENTED** (enabling Realtime publications on the production
Supabase project = EXTERNAL CONFIGURATION REQUIRED).

## 12. White-label (Part 13)

D21/D27 custom domains + custom email senders with verification tokens; branded PDFs/reports;
consultant isolation. Responsibility split (ratified K): domains/DNS/SSL/mail =
**Consultant**; platform integration/verification + sender routing via Resend =
**CarbonTally**; DNS verification records + Resend domain registration = **external provider**.
**Verdict: IMPLEMENTED** (per-environment verification = EXTERNAL CONFIGURATION).

## 13. Reporting (Part 14)

D31 reporting verified intact (backend suite + RLS + live smoke pass after D32 changes;
reporting endpoints unaffected by the storage fix). Customer/consultant/internal/reviewer/QC/
admin/entity reporting present. **Verdict: IMPLEMENTED — no regression found.**

## 14. Onboarding (Part 15)

Signup → org creation → invitations → member onboarding; consultant firm onboarding; D19
existing-data discovery (`/api/v3/discovery/*`: lookup, requests, verify) with USE ALL / PARTIAL
/ DISCARD as customer decisions; no silent deletion of existing data. **Verdict: IMPLEMENTED.**

## 15. Notifications / email (Part 16)

In-app notifications IMPLEMENTED (repo + NotificationsPage). Email via Resend (`v3_email.py`)
IMPLEMENTED but with a single generic HTML renderer — per-workflow templates (processing
complete, issues, reports, invites) = NEEDS TEMPLATE WORK (P2/P3). Resend domain + sender
identity + white-label senders = EXTERNAL CONFIGURATION REQUIRED.

## 16. Reports / PDF (Part 17)

Report generation engine, branded PDF render (D27), report versioning, download/export,
authorization org-scoped. **Verdict: IMPLEMENTED.** (Synthetic corpus and 5,787 PDFs untouched —
prohibitions respected.)

## 17. Export / portability (Part 18)

Emissions CSV/JSON + documents CSV. **Limitations:** no document binaries in exports; no
provenance/audit export; no full-data portability package. Customer transition relies on the
customer's export + (future) import. **Verdict: PARTIALLY IMPLEMENTED** — document binary +
provenance export = P2/P3 (POST-LAUNCH; no generic import system built in D32).

## 18. Database / migrations (Part 19)

Migration chain ordered; idempotent demo seed; FKs/constraints/RLS in migrations; D31 dedicated
integration DB fix remains authoritative (verified again in D32: default = `carbontally_test`,
main-DB URL → refuse, missing DB → skip). D32 adds the storage migration. **Verdict:
IMPLEMENTED.** No orphan-cascade defects found in the audited paths.

## 19. Billing / Stripe readiness (Part 3/25)

Schema evidence: `stripe_customer_id`, `stripe_subscription_id`, `stripe_price_id`,
`subscription_status`/`subscription_tier`/`subscription_id`, `billing_cycle`/
`billing_period_start/end`, `customer_subscriptions`, `consultant_billing`
(+`manual_extraction_credit`), `usage_tracking`, `billing_contact_*`/`billing_address`/
`billing_currency`.

**What exists:** the identifiers/state columns; **what is missing:** billing API, Stripe
webhook handler, subscription gating, usage metering logic, billing UI, price/entitlement
configuration. **No proprietary billing built.** Recommended integration boundary:

```
CarbonTally  →  Stripe  →  Customer / Subscription / Invoice / Payment
CarbonTally stores ONLY: stripe_customer_id, stripe_subscription_id, stripe_price_id,
subscription status/period, metered usage. NO card/payment credentials.
```

Consultants bill via their own CarbonTally consultant subscription (Stripe); Consultant Clients
are NOT automatic billing customers (ratified). White-label/partner pricing needs future
metadata (P3).

**Classification: PARTIALLY READY FOR STRIPE INTEGRATION** (schema ready; application changes
required: webhooks + gating + metering + UI).

## 20–23. Platform readiness (Part 20)

| Platform | Status | Required (all EXTERNAL CONFIGURATION) |
|---|---|---|
| Vercel (frontend) | env prepared (`REACT_APP_API_URL`, `SUPABASE_URL`, anon key) | project + domain + env vars + auth redirect URLs |
| Render (backend) | env prepared (`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `RESEND_API_KEY`) | service + healthcheck + env + CORS origins |
| Supabase (DB/Auth/Storage/Realtime) | local stack verified | hosted project: auth providers (Google), MFA, redirect URLs, Storage bucket config, Realtime enablement, RLS already in migrations |
| Resend (email) | `v3_email.py` wired, no-op without key | domain verification, sender identity, white-label senders |
| CORS | `Config.ALLOWED_ORIGINS` env-driven | set production origin list |
| HTTPS / domains / backups / monitoring | — | provider configuration |

## 24. Backup / disaster recovery (Part 21)

No dedicated backup/DR document exists (only incidental mentions). Supabase provides point-in-time
recovery/backups via the dashboard (EXTERNAL CONFIGURATION); a written restore procedure + storage
backup strategy + migration rollback note are required documentation. **Classification:
MISSING — P2** (documentation; the capability exists in the platform).

## 25. Performance / reliability (Part 22)

Evidence-based: reporting uses SQL aggregates (no N+1); list endpoints paginate (limit/offset);
synchronous processing engine has persisted lifecycle states; uploads are synchronous (large-file
timeout risk); no file-size cap. No speculative optimization performed. **POST-LAUNCH items:**
upload size/timeout limits, async extraction worker, duplicate-upload detection.

## 26. Observability (Part 23)

Present: backend structured logging (`core.logging`), request middleware + correlation ids,
`/health` endpoint, write-side audit trail, D31 admin audit surface, ops dashboards. Alerts /
error tracking / metrics are provider-level (Render/Vercel/Supabase) = EXTERNAL CONFIGURATION.

## 27. UX / product completeness (Part 24)

D28/D29/D30/D31 screenshots + shared `StateViews` (Loading/Error/Empty + retry) + D30/D31
reporting panels verified. V3 surfaces show human-readable labels; raw UUIDs only in tooltips/
API contracts. Residual: legacy beta `/dashboard/*` flows (retire/redirect = P2/P3); true mobile
(≤375px) unverified with headless tooling (noted in D28/D29).

## 28. P0 / P1 findings

| # | Finding | Classification | D32 action |
|---|---|---|---|
| 1 | Customer documents in a PUBLIC storage bucket with no storage RLS, served via public URLs | MISSING — P0 (data confidentiality) | **FIXED** (private bucket + storage RLS + signed URLs; verified) |
| 2 | No other P0/P1 defect found that is fixable without a ratified business decision | — | none implemented |

## 29. P2 / P3 backlog

| Item | Priority |
|---|---|
| Retire/redirect legacy beta `/dashboard/*` flows | P2 |
| Upload file-size limit + duplicate detection | P2 |
| Document-binary + provenance export; audit export | P2/P3 |
| Email template library per workflow | P2/P3 |
| Billing UI + Stripe webhooks + subscription gating (blocked on Stripe integration decision) | P2 |
| `messages_tenant_insert` participant RLS qual | P3 |
| Backup/DR documentation | P2 |
| Upload-signed-url refresh UX + storage cleanup on deactivation | P3 |

## 30. External configuration checklist

1. Supabase project: Google OAuth + MFA + redirect URLs + email templates + Realtime enablement.
2. Supabase Storage: confirm `documents` bucket private (migration included).
3. Resend: domain verification + sender identity (CarbonTally + white-label senders).
4. Vercel: frontend env vars + domain + auth redirect URLs.
5. Render: backend env vars + CORS origins + healthcheck.
6. Stripe: account/products/prices/webhooks + environment separation.
7. Backups/PITR + monitoring/alerts per environment.

## 31. Recommended next phase

Product owner decision required on **billing (Stripe integration scope + consultant pricing
model)** and **email template priorities**. Functional completion is achieved; D33 is expected to
be either (a) the Stripe integration build or (b) the 5,787-PDF processing validation run (which
remains NOT started and awaits authorization).

## 32. Exact files changed (D32)

Backend:
- `backend/services/storage.py` (new — signed-URL helpers)
- `backend/api/v3_documents.py` (signed upload + `GET /documents/{id}/signed-url`)
- `backend/api/v3_operations.py`, `backend/api/v3_processing_workflow.py` (signed workspace URLs)
- `backend/tests/unit/api/test_storage_security.py` (new — 6 tests)

Database/migrations:
- `supabase/migrations/20260823000000_d32_private_documents_storage.sql` (new — private bucket +
  4 storage RLS policies)

Docs:
- `docs/audit/cline/CARBONTALLY_V3_D32_FINAL_PRODUCT_COMPLETENESS_AUDIT.md` (this report)

## 33. Exact tests executed

| Suite | Result |
|---|---|
| Backend unit `pytest tests/unit` | **983 passed** (977 baseline + 6 storage tests) |
| Storage-security + reporting focused | **39 passed** (33 reporting + 6 storage) |
| RLS integration (`carbontally_test` dedicated DB) | **11 passed** (refuse/skip guards verified) |
| Frontend V3 API Jest | **18/18 passed** |
| Frontend production build | succeeded |
| Live storage-security test (signed URLs / denials) | passed (see §9) |

## 34. Exact remaining blockers

1. External configuration (Supabase auth/redirects/OAuth/MFA, Resend domain, Vercel/Render env,
   Stripe, backups/monitoring) — EXTERNAL CONFIGURATION REQUIRED, not code.
2. Stripe integration (webhooks/gating/metering/UI) — BUSINESS DECISION REQUIRED on scope +
   pricing model, then PARTIALLY-READY schema.
3. Document-binary/provenance export — MISSING — P2 (POST-LAUNCH).
4. Backup/DR documentation — MISSING — P2.
5. The 5,787-PDF processing validation — NOT STARTED (awaiting authorization).

## Product Owner decision list

- **D1:** Approve the D32 P0 storage fix (private bucket + signed URLs) — already applied; confirm
  no business objection.
- **D2:** Authorize the Stripe integration build (schema is ready) and the consultant billing
  model (per-subscription vs per-client) — the schema supports either.
- **D3:** Prioritise email template library vs document export for the first post-audit sprint.
- **D4:** Authorize the 5,787-PDF processing validation run.
- **D5:** Approve retirement/redirect of the legacy beta `/dashboard/*` surfaces.

*HARD STOP — D32 complete. No D33 started.*




