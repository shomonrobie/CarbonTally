# CarbonTally V3 — D34 Production Customer Journey & Commercial Readiness Audit

**Date:** 2026-08-23 · **Mode:** read-only audit + journey verification (no implementation)
**Author:** Cline

---

## 1. Executive summary

D34 audited the complete production customer journey: **Discover → Understand →
Sign up → Onboard → Become a Direct Customer → Select services → Pay → Upload →
Process → Map → Validate → Calculate → Trace evidence → Review → Export → Communicate
→ Continue using.**

The engineering surface for an already-provisioned customer is functionally complete
and green (1018 backend unit, 11 RLS integration, 18 frontend API, production build).
Evidence traceability, reporting, processing, messaging, white-label and security are
all implemented and live-verified.

The journey is **NOT production-ready for a completely new customer** because it breaks
at two points:

1. **Sign up / become a Direct Customer (P1):** the public signup route is
   **beta-code-gated** (`/signup` → `BetaSignup`) and there is **no self-serve
   organization-creation path** for a net-new customer without existing data. A new
   customer can only join via beta code / staff or consultant provisioning.
2. **Pay / subscribe / begin a commercial relationship (P1):** **no billing is
   implemented** (Stripe-ready schema only) and **pricing is a DRAFT**
   (`docs/Pricing/CarbonTally_V3_Draft_Pricing_Strategy_and_Competitive_Benchmark.md`).
   The core commercial service with real human cost — **manual extraction** — cannot be
   purchased or metered today.

Secondary gaps (P2 / external config) are documented in §29–§31.

**Verdict: NOT READY — P0/P1 BLOCKERS REMAIN.** (No P0 security/data-integrity defects
were found; the blockers are the self-serve onboarding and the commercial/billing leg.
Both are implementation-ready once the Product Owner approves the commercial model.)

## 2. Production readiness verdict

**"NOT READY — P0/P1 BLOCKERS REMAIN"** for a fully self-serve new customer journey.

For a **controlled, invite/provisioned launch** (customers onboarded via CarbonTally or
a consultant with an existing organization), the functional product journey is
**ready for production configuration** — subject to the external configuration items in
§29 (Supabase auth/OAuth/MFA/email, Resend domains, Vercel/Render env + CORS, Stripe).

## 3. Complete customer journey (as found)

| Step | State |
|---|---|
| Discover | Landing page exists; positioned around compliance/reporting; "Request Beta Access" CTA; **no pricing, services or contact pages** |
| Understand what CarbonTally provides | Partial — feature list exists, but "carbon data processing infrastructure" positioning is not clearly communicated; "Automated CSV Data Stream Mapping" claim is **not backed by an automated pipeline** |
| Sign up | **Beta-gated** (`/signup` → `BetaSignup` requires a beta access code) — no public self-serve production signup |
| Complete onboarding | D19 existing-data discovery **fully implemented** (lookup → verify → USE ALL / PARTIAL / DISCARD); DISCARD records and never deletes |
| Become a Direct Customer | **Blocked for net-new customers** — no organization-creation endpoint; adoption requires an existing candidate org, staff mediation, or provisioning |
| Understand/select services | Service catalogue documented (`docs/cline/prompts/CarbonTally_V3_Service_Catalogue_...`); **not surfaced on the public site** |
| Pay / subscribe | **Not implemented** (no Stripe API/UI/webhooks; pricing is a DRAFT) |

## 4. Customer journey matrix

| Journey | Implemented | Verified | External Config | Business Decision | Blocker |
|---|---|---|---|---|---|
| Discover | PARTIAL | Yes (landing loads) | — | — | Content/positioning (P2) |
| Sign up | NO (beta-gated) | No | — | — | **P1** |
| Login | YES | Yes | OAuth/MFA/email | — | — |
| Onboarding | YES (D19) | Yes | — | — | — |
| Direct customer | PARTIAL | No | — | — | **P1** (no org creation) |
| Existing data | YES | Yes | — | — | — |
| Staff | YES | Yes | — | — | — |
| Consultant | YES | Yes | — | — | — |
| Entity | YES | Yes | — | — | — |
| Excel | PARTIAL (upload; manual extraction) | Yes | — | — | No automated parse (P2) |
| CSV | PARTIAL | Yes | — | — | No automated parse (P2) |
| JSON | NO (classified OTHER) | No | — | — | P2 |
| PDF | YES | Yes | — | — | — |
| Image | YES | Yes | — | — | — |
| Automatic extraction | NO | No | — | — | P2 (roadmap claim) |
| Manual extraction | YES | Yes | — | — | Cannot be purchased (**P1**) |
| Mapping | YES | Yes | — | — | — |
| Validation | YES | Yes | — | — | — |
| Calculation | YES | Yes | — | — | — |
| Evidence | YES | Yes | — | — | — |
| Reporting | YES | Yes | — | — | — |
| Export | YES | Yes | — | Document-binary export (P2) | — |
| Messaging | YES | Yes | — | — | — |
| Notifications | YES (in-app) | Yes | Email templates (P2) | — | — |
| Billing | NO | No | Stripe config | **Pricing approval** | **P1** |
| Email | PARTIAL | No | Resend domains | — | Templates (P2) |
| White-label | YES | Yes | DNS/domain | — | — |
| Support | PARTIAL (issues/messaging) | Yes | — | — | No public help/FAQ (P2) |

## 5. Commercial services audit

Classified against the authoritative service catalogue
(`docs/cline/prompts/CarbonTally_V3_Service_Catalogue_and_Evidence_Traceability_Cline_Brief.md`, 16 families):

| Service family | State |
|---|---|
| 1 Data Ingestion (Excel/CSV/PDF/image) | PARTIALLY IMPLEMENTED — upload + storage + manual extraction; no automated structured parsing; JSON not classified |
| 2 Automated Document Extraction | NOT IMPLEMENTED (no extraction engine; landing page claims it) |
| 3 Human-Assisted Extraction | IMPLEMENTED (D23 full workflow; entity + internal staff) |
| 4 Data Normalization | PARTIALLY IMPLEMENTED (unit normalization in mapping; no dedicated normalization-stage UI) |
| 5 Emission-Factor Mapping | IMPLEMENTED (matching, candidates, selection, provenance, unit compatibility) |
| 6 Emissions Calculation | IMPLEMENTED (engine + snapshots + verify) |
| 7 Validation, Review, QC | IMPLEMENTED |
| 8 Evidence & Auditability | IMPLEMENTED (D33/D33.1 — release-critical differentiator) |
| 9 Document & Evidence Storage | IMPLEMENTED (private + signed URLs) |
| 10 Reporting & Analytics | IMPLEMENTED (D30/D31 all actors) |
| 11 Collaboration & Messaging | IMPLEMENTED (customer ↔ consultant; entity-mediated) |
| 12 White-Label | IMPLEMENTED (custom domains + verified senders; DNS external) |
| 13 Customer Onboarding & Data Discovery | IMPLEMENTED (D19) |
| 14 Data Portability | PARTIAL — export implemented; document-binary/provenance archive + import = P2 |
| 15 API & External Integrations | REST/JSON/CSV/Excel API surfaces exist; no ERP/accounting integrations (FUTURE) |
| 16 Commercial / Billing | NOT IMPLEMENTED (Stripe-ready schema only) |

## 6. Pricing / billing audit

- **Pricing document:** `docs/Pricing/CarbonTally_V3_Draft_Pricing_Strategy_and_Competitive_Benchmark.md` is an explicit **DRAFT** ("prices are proposed starting points, not final commitments"). Recommended model: platform subscription + processing usage + human extraction + optional professional services. Manual extraction is explicitly acknowledged as the high-cost dimension.

## 7. Authentication / onboarding audit

- Email/password sign-in, logout, session persistence: **IMPLEMENTED** (Supabase Auth; live-verified).
- Password recovery: Supabase-managed → **EXTERNAL CONFIGURATION REQUIRED** (auth email template/domain).
- Google OAuth: present in the login UI; provider **disabled** in local config (`config.toml` `[auth.external.google] enabled=false`) → **EXTERNAL CONFIGURATION REQUIRED**.
- MFA/2FA: not enabled → **EXTERNAL CONFIGURATION REQUIRED** (Supabase-managed).
- Post-login routing: server-authoritative `resolvePostLoginPath` (D29/F5) → `/home` | `/ops` | `/consultant` — **IMPLEMENTED**.
- Signup: `/signup` → **BetaSignup (beta-code-gated)** — **MISSING for production self-serve** (**P1**).
- Organization creation: **no self-serve endpoint** — net-new customers cannot create an org without staff/consultant provisioning (**P1**).

## 8. Customer organization audit

- Org CRUD read surfaces, members (owner/admin/member/viewer roles via `organization_members.role` CHECK), invitations (create/list/delete), facilities/assets: **IMPLEMENTED**.
- Cross-organization isolation: org-scoped RLS + `ensure_org_access`; live cross-org 403 verified — **IMPLEMENTED**.
- Invitation **email delivery**: invitation rows are created; sending is not wired to Resend → **PARTIAL / EXTERNAL** (email templates P2).

## 9. Consultant journey audit

- Registration/onboarding: consultant firm/membership exists; **public consultant self-serve signup is not exposed** (consultants are provisioned) — documented, not a launch blocker for the customer journey.
- Client lifecycle ACTIVE/SUSPENDED/ENDED (D15/D19): **IMPLEMENTED**; ended grants lose access (server + RLS).
- Grant activation, suspension, termination, reactivation, access termination, customer ownership: **IMPLEMENTED**.
- Branding (D21), messaging, portfolio reporting + per-client drill-down (D30/D31): **IMPLEMENTED**.

## 10. Processing Entity journey audit

- Entity creation/admin, entity staff, work assignment (D22), entity A/B isolation, staff workspace, extraction, review, QC, performance/SLA reporting: **IMPLEMENTED**.
- Isolation verified: RLS entity-scoped policies + `is_entity_member`; RLS suite passes (11/11); entity staff cannot read customer org data except via mediated processing paths.

## 11. Data-input audit

- PDF / image (jpg/jpeg/png/gif/webp) / CSV / Excel: classified + uploaded to **private storage** + served via **signed URLs** — **IMPLEMENTED**.
- **JSON: not classified** (`_classify` → OTHER) — no structured JSON ingestion — **P2**.
- Excel/CSV content is not automatically parsed: rows are extracted through the **manual extraction workflow** (item = one extracted line) — the landing "Automated CSV Data Stream Mapping" claim is **not implemented** — **P2** (content mismatch).

## 12. Automatic processing audit

- Upload → extract → map → validate → calculate: **extraction is manual**; mapping (factor matching/candidates/selection) and calculation are automated and authoritative.
- Factor matching: candidates + selection + unit compatibility (D23 fix: substring-compatible canonical units e.g. `kWh (Gross CV)` resolve; genuine mismatch → `UNIT_MISMATCH`).
- Persistence: emission logs + immutable calculation snapshots + source links — **IMPLEMENTED**.

- **Service → billable event → price → usage → customer:** the **service catalogue exists**, but there is **no mapping to billable events, no metering, no price book** and **no billing API/UI/webhooks**. `usage_tracking` has an org-month unique key (schema-level readiness only).
- **Schema readiness (verified in migrations):** `customer_subscriptions` (+ `stripe_customer_id`/`stripe_subscription_id`/`stripe_price_id`, status CHECK incl. trialing/active/past_due/paused/cancelled/expired), `usage_tracking` (org_month unique), `consultant_billing` (+ `manual_extraction_credit`), plus subscription columns on organizations. → **PARTIALLY READY FOR STRIPE INTEGRATION** (no application code, no entitlements, no webhooks).
- **Verdict:** **BUSINESS DECISION REQUIRED** (approve pricing/service model) then **P1 implementation** (Stripe integration + entitlement gating). Manual extraction cannot be purchased/metered until then.

| Upload carbon data | PDF / image / CSV / Excel upload works (private storage + signed URLs); **JSON is classified as OTHER** (no structured JSON ingestion) |
| Automatic or manual processing | Automatic: factor matching + calculation automated; **no automated extraction engine**. Manual: full D23 workflow implemented |
| Map data to factors | Implemented (matching → candidates → selection; D23 unit-compat fix verified) |
| Validate data | Implemented (validation gate, blocking findings, mapped/unmapped, calculation readiness) |
| Calculate emissions | Authoritative engine + immutable snapshots + verify |
| Trace every result to its evidence | **Implemented (D33/D33.1)** — evidence record, reverse lookup, signed source access, audit |
| Review results/reports | Implemented (D30/D31 dashboards, reports, PDFs) |
| Export/use results | CSV/JSON export + reports + provenance identifiers implemented |
| Communicate | Customer ↔ consultant messaging implemented; in-app notifications implemented |
| Continue using | Sessions persist; post-login routing server-authoritative (D29) |
## 13. Manual processing audit

- Full workflow implemented: assignment (internal + Processing Entity), claim, extraction, multi-line, mapping options, validation, QC, completion, customer visibility, audit trail, entity isolation (D22/D23).
- **Commercial readiness:** manual extraction **cannot be purchased or metered** (no billing/entitlement) → **P1** (the core commercial service with real human cost) — implementation pending the approved commercial model.

## 14. Emission-factor mapping audit

- Factor database, matching, candidates, selection, unit, reporting year, source, country, factor set, provenance (factor_source/factor_set/import_batch + D33 source refs): **IMPLEMENTED**.
- Customer-facing explanation: the D33.1 evidence record shows WHAT factor, factor source/set, value, unit and the calculation; "WHY selected" is available through the mapping/match surface — **PARTIAL** (no explicit natural-language "why this factor" text; documented).

## 15. Calculation audit

- `quantity × factor = line emission`, document totals, organization aggregates: **IMPLEMENTED** via the authoritative Calculation Engine (immutable snapshots, content hash, verify endpoint). Numerical correctness covered by unit tests + snapshot verification.

## 16. Evidence traceability audit

- D33 lineage verified intact (FKs present in the live DB): `emissions_logs.snapshot_id → calculation_snapshots`, `calculation_snapshots.source_item_id → manual_extraction_items`, `manual_extraction_items.file_id → organization_files` (all `ON DELETE SET NULL`, factor refs `RESTRICT`).
- Customer-facing evidence (D33/D33.1): per-emission Evidence Record (source document → original extracted data → mapping → factor → calculation → result; completeness COMPLETE/PARTIAL/UNAVAILABLE; technical identifiers), reverse document→emissions, signed source access, evidence-access audit — **IMPLEMENTED + live-verified**.

## 17. Reporting audit

- Customer dashboard (totals/scope/monthly trend/documents/stages/data quality/needs-attention/member activity): **IMPLEMENTED**.
- Consultant portfolio + per-client drill-down: **IMPLEMENTED**.
- Operations (platform/queue aging/audit), Reviewer (workload/issues/SLA), QC (processor performance internal vs entity), Processing Entity (SLA/quality/workload), Admin (platform/audit): **IMPLEMENTED** (D30/D31).

## 18. Export audit

- Emissions CSV/JSON (with `snapshot_id`, `source_item_id`, `source_file`, `source_page`, `evidence_status`), documents CSV, reports: **IMPLEMENTED**.
- Document-binary / full-provenance archive export + data import: **P2** (post-launch, per D32).

## 19. Messaging audit

- Customer ↔ consultant conversations (create/list/messages/read, org + active-grant authorization): **IMPLEMENTED** (live-verified endpoint + UI page).
- Entity staff cannot initiate unrestricted customer messaging (mediated processing only).

## 20. Notification / email audit

- In-app notifications (list/read/read-all): **IMPLEMENTED**.
- Transactional email: `services/v3_email.py` Resend client + one wired trigger (D19 discovery verification code). **Invitations, processing-completion and other templates = P2**; Resend domain/sender identity + Supabase auth email = **EXTERNAL CONFIGURATION REQUIRED**.



## 21. White-label audit

- Custom domains (DNS verification token, domain selects branding only, never authorization) + verified email senders + brand + branded PDFs + platform presentation: **IMPLEMENTED** (D21/D26/D27).
- Customer/consultant own their domain/DNS/email infrastructure; CarbonTally provides integration instructions — matches the ratified decision.
- Vercel custom-domain + Resend verified-sender production configuration: **EXTERNAL CONFIGURATION REQUIRED**.

## 22. Stripe readiness

| Item | State |
|---|---|
| Schema (`stripe_customer_id`/`subscription_id`/`price_id`, `customer_subscriptions`, `consultant_billing` + `manual_extraction_credit`, `usage_tracking`) | IMPLEMENTED (PARTIALLY READY) |
| Stripe API integration (checkout/subscriptions/customer portal) | MISSING |
| Webhooks (payment status, subscription lifecycle) | MISSING |
| Entitlement / usage metering / credit ledger (app-side) | MISSING |
| Pricing / service→billable-event mapping | BUSINESS DECISION REQUIRED (draft only) |
| Stripe keys + webhook secrets | EXTERNAL CONFIGURATION REQUIRED |

## 23. Production infrastructure audit

- Local env vars/secrets/CORS present (backend `.env`, CORS allow-list incl. localhost + Vercel/Render origins). **Vercel/Render/Supabase/Resend/Stripe production configuration cannot be verified locally** → **EXTERNAL CONFIGURATION REQUIRED**.
- Health endpoint: `GET /health` reports `healthy`/`degraded` with database + supabase components — **IMPLEMENTED**.
- Supabase redirect URLs, OAuth, MFA, email domain, storage bucket (private), Realtime: **EXTERNAL CONFIGURATION REQUIRED** (local config is dev-local only).
- Database migrations: 28 migrations applied cleanly to the local stack (verified during this audit's environment build).

## 24. Backup / DR audit

- **No formal backup/DR runbook.** Only ad-hoc artifacts exist (`backend/carbon_tally_backup.sql`, `carbon_tally_backup_data.sql`, `backups/`, a backup zip). No RTO/RPO, no scheduled DB backup, no Storage recovery procedure, no migration-rollback runbook.
- Verdict: **P2** (D32-identified) — **production ops requirement before general launch**; does not block a controlled configuration phase if the operator adopts a backup policy.

## 25. Observability audit

- Health endpoint + structured startup/runtime logging exist. **No monitoring/alerting stack** (no Sentry/Prometheus/DataDog etc.), no queue-backlog/payment-failure/storage-failure alerting.
- Verdict: **P2 / production-ops requirement** — operators cannot yet be alerted to backend/database/email/extraction/payment failures.

## 26. Security / RLS audit

- Re-ran the dedicated RLS integration suite against `carbontally_test`: **11/11 passed** (org isolation, consultant ACTIVE grant, entity isolation, issue isolation). The `conftest` main-DB refusal guard remains intact.
- Live denials re-verified in D33.1 (consultant 403, entity-staff 403, public URL blocked, signed URL 200). No authorization regression found.

## 27. Failure scenarios

Covered by existing implementation/tests (documented): upload failure (storage error surfaced), extraction/mapping failure (issues + rework loops), no-factor-found + unit mismatch (422 `UNIT_MISMATCH`), validation blocking (blocking issues → rework), entity suspension (rejection on assignment), consultant access end (403), signed URL expiry (re-issue via API), missing source document (evidence record reports UNAVAILABLE honestly). Payment-failure and email-failure handling cannot be exercised until billing/email are configured (**P1/P2**).

## 28. UX audit

- D28/D29 visual QA + fixes (membership resolution, loading timeout/retry, post-login routing, brand-title fallback, notifications empty state, human-readable labels) are in place. Journey screenshots captured in `screenshots/d34_customer_journey/` evidence the landing/login/dashboard/existing-data states. No redesign performed.

## 29. External configuration checklist

| Item | Status |
|---|---|
| Supabase auth redirect URLs (site_url + additional_redirect_urls) | EXTERNAL CONFIGURATION REQUIRED (local dev values only) |
| Google OAuth provider | EXTERNAL CONFIGURATION REQUIRED (disabled locally) |
| MFA/2FA | EXTERNAL CONFIGURATION REQUIRED |
| Supabase auth email (confirm/password-reset) domain + templates | EXTERNAL CONFIGURATION REQUIRED |
| Resend domain verification + verified senders | EXTERNAL CONFIGURATION REQUIRED |
| Vercel env vars (REACT_APP_*) + custom domain | EXTERNAL CONFIGURATION REQUIRED |
| Render env vars (DATABASE_URL, SUPABASE_*, RESEND_API_KEY, SECRETS) + CORS origins | EXTERNAL CONFIGURATION REQUIRED |
| Supabase production project (migrations, RLS, storage bucket private + policies) | EXTERNAL CONFIGURATION REQUIRED |
| Realtime (messages/notifications) | EXTERNAL CONFIGURATION REQUIRED (foundation exists) |
| Stripe keys + webhooks | EXTERNAL CONFIGURATION REQUIRED |

## 30. Business decision checklist

| Decision | Required |
|---|---|
| Approve pricing/service model (convert `Draft_Pricing_Strategy` → final price book) | YES — blocks billing implementation |
| Approve manual-extraction pricing/metering (human-cost dimension) | YES — core commercial service |
| Approve D5: retire legacy beta `/dashboard/*` surfaces | PENDING (D5) |
| Approve D32 storage-fix sign-off (already applied) | PENDING (D1) |
| Approve 5,787-PDF validation run | PENDING (D4) — out of D34 scope |
| Approve email-template library vs document-binary/provenance export priority | PENDING (D3) |

## 31. P0 / P1 / P2 / P3 findings

**P0 (release blocker / security / data integrity): NONE found.**
- Security model green (11/11 RLS, live denials), evidence chain intact (FKs + lineage), no cross-tenant leakage.


## 32. Exact files changed (D34)

**None.** D34 was a read-only audit + journey verification. No application code, schema, migration, RLS, frontend, test or data was modified. (Artifacts created: this report, `screenshots/d34_customer_journey/` captures + manifest, and temporary /tmp verification scripts.)

## 33. Tests

| Suite | Result |
|---|---|
| Backend unit | **1018 passed** (0 failures) |
| RLS integration (dedicated `carbontally_test`) | **11 passed** |
| Frontend V3 API Jest | **18/18 passed** |
| Frontend production build | **succeeded** |

## 34. Live verification (non-destructive)

- Backend `/health` → `healthy` (supabase_connected, DB connected, 560 routes); frontend `:3000` 200.
- Owner journey surfaces live-verified: customer dashboard, documents, emissions export, processing dashboard, notifications, issues, reports, organization, members — all 200.
- Messaging + existing-data endpoints exist and authorize correctly (probe 422s were missing-required-param errors, not defects).
- Consultant cross-org denial re-verified (403).
- D33.1 fixture runs (evidence record, reverse lookup, audit, signed URLs, denials) were re-confirmed during this session's environment build; all D33.1 fixtures remain cleaned.

## 35. Final Product Owner action list

1. **Approve the pricing/commercial model** (convert the draft pricing strategy into a final price book, including manual-extraction pricing) — unlocks the billing P1.
2. **Authorize the billing implementation** (Stripe integration: checkout/subscriptions/customer portal/webhooks + entitlement/usage metering wired to `customer_subscriptions` / `usage_tracking` / `consultant_billing` + `manual_extraction_credit`) as the next implementation task.
3. **Decide the controlled-launch onboarding mode**: keep invite/beta-code onboarding for the first cohort (allow immediate production configuration) or implement public self-serve signup + organization creation (P1) before launch.
4. **Decide the discovery-content update** (P2): align landing copy with the "carbon data processing infrastructure" positioning + remove/qualify the "Automated CSV" claim until implemented.
5. **Close outstanding decisions:** D1 (storage fix sign-off), D3 (email templates vs export priority), D4 (5,787-PDF validation), D5 (legacy `/dashboard/*` retirement).

**P1 (serious production blockers):**
1. **Self-serve signup + Direct-Customer onboarding** — public signup is beta-gated and net-new customers have no organization-creation path. *(Journey breaks at "Sign up"→"Become a Direct Customer".)*
2. **Commercial billing** — no payment/subscription/entitlement; manual extraction (the core human-cost service) cannot be purchased or metered. *(Journey breaks at "Pay / subscribe".)* Blocked by the pricing business decision (§30).

**P2 (important, launch-with-controlled-limitation):**
- Landing positioning/content (no services/pricing/contact pages; compliance framing vs "carbon data processing infrastructure" positioning).
- "Automated CSV Data Stream Mapping" claim not backed by an automated pipeline; JSON not classified; no automated extraction engine.
- Transactional email templates (invitations, processing completion).
- Document-binary/provenance archive export + data import.
- Backup/DR runbook + observability/alerting (production ops).
- Public help/FAQ content.
- Legacy `/dashboard/*` retirement (D5).

**P3 / FUTURE:** ERP/accounting integrations, automated extraction engine, bulk ingestion.

**EXTERNAL CONFIGURATION REQUIRED:** see §29.

**BUSINESS DECISIONS REQUIRED:** see §30.


## 36. Recommended D35 (if required)

**Recommended D35: Commercial Launch Configuration** — implement the approved billing layer (Stripe subscriptions + processing credits + manual-extraction metering) and the agreed controlled-launch onboarding (self-serve signup + organization creation, or the approved invite flow), then re-run this journey audit. External production configuration (Supabase auth/OAuth/MFA/email, Resend domains, Vercel/Render env + CORS, backups/observability) should proceed in parallel as production ops.

---

**HARD STOP.** No D35, no Stripe implementation, no synthetic-corpus validation, no Blog integration, no P2/P3 feature work was started.

**Final verdict: "NOT READY — P0/P1 BLOCKERS REMAIN"** (self-serve onboarding + commercial billing). The engineering surface is otherwise functionally complete, tested and secure, and is ready for a **controlled production configuration phase** for provisioned customers.


