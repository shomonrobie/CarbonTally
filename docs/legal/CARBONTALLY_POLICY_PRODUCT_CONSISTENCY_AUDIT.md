# CarbonTally V3 — Policy ↔ Product Consistency Audit

**Status:** Draft audit for internal review
**Date:** 24 August 2026
**Git baseline:** `899706d6ab4a2eda47f412b5b82e5f24a4390819` (main, local workspace)
**Method:** Read-only inspection of repository source (frontend, backend, schema), the live local API contract (`/openapi.json` on `localhost:8050`), and official provider documentation. **No application, database, schema, migration, RLS, storage, or configuration changes were made.**
**Nature of this document:** This audit is NOT legal advice and does not certify compliance. It identifies where public policy documents and the actual product diverge, and what must be true before specific statements can be made.

---

## 1. Executive Summary

CarbonTally V3 ships four public policy pages (`/terms`, `/privacy`, `/cookies`, `/pricing`) plus an unlinked `DataSecurity.jsx` component. All four policy pages are written as **pre-launch** documents and are, in their own terms, accurate to the pre-launch state of the product. There are no existing **DPA, Refund Policy, or MSA** documents anywhere in the repository.

The principal consistency findings are:

1. **No data-deletion capability that matches ordinary "delete my data" expectations.** The product has no account deletion, no organisation deletion, no full data-export tool, and no customer-facing document deletion flow in the V3 UI. The live Privacy Policy promises rights including "deletion of your personal data" without any self-service mechanism and with no documented operational deletion process. This is the largest policy↔product gap.
2. **No online payment or subscription billing exists.** The D37 billing surface is credit/order based, provider-neutral, and explicitly has *no payment-provider integration*. The Refund Policy must therefore be drafted as a pre-payment framework, and any promise of "refunds to your card" would be unsupportable.
3. **No third-party AI currently receives customer documents in the production pipeline.** Extraction is deterministic and local (PDF text extraction, Tesseract / local ONNX OCR, CSV/XLSX parsing). An OpenAI/Anthropic-compatible `LLMClient` exists but is not wired into any production route. Policies should state the current reality and require a future disclosure if the AI engine is ever enabled.
4. **The retention feature is configurable but only partially enforced.** Retention settings exist (`/api/v3/settings/retention`) but only `document_retention_days` is enforced, only as a soft-delete, and only when explicitly run with `dry_run=False`. Audit/evidence tables are deliberately excluded.
5. **An unlinked legacy `frontend/TermsPage.jsx`** (not routed) claims "SECR-compliant reports" and uses a `legal@carbontally.com` contact. It is superseded by the routed pre-launch `frontend/src/TermsPage.jsx` and should be removed or reconciled to avoid an inconsistent public record.
6. **The Cookie Policy is accurate** (no third-party trackers; localStorage auth sessions). The Cookie Banner's text ("we use cookies to enhance your experience… you agree to our use of cookies") is however inaccurate relative to the actual cookie behaviour and should be aligned.
7. **No SLA or support commitments exist anywhere.** Draft documents must not invent uptime or response-time guarantees. Provider commitments (e.g., Vercel's 99.99% Enterprise SLA) do not automatically become CarbonTally commitments.

---

## 2. A. Existing-Document Inventory

### 2.1 Public policy pages (routed)

| File | Route | Status | Notes |
|---|---|---|---|
| `frontend/src/TermsPage.jsx` | `/terms` | Live, routed | Pre-launch ToS. Self-describes as pre-launch; no billing terms claimed. |
| `frontend/src/PrivacyPolicy.jsx` | `/privacy` | Live, routed | Pre-launch privacy policy. |
| `frontend/src/CookiePolicy.jsx` | `/cookies` | Live, routed | Pre-launch cookie policy. Accurate re: no trackers. |
| `frontend/src/PricingPage.jsx` | `/pricing` | Live, routed | Indicative pricing only; explicitly "no online checkout". |
| `frontend/src/CookieBanner.jsx` | global | Live, rendered | Consent banner; text overstates cookie use. |
| `frontend/src/DataSecurity.jsx` | **none** | **Not routed** | Security/processing narrative. Referenced nowhere in `App.js`. |

### 2.2 Duplicates and copies

| File | Notes |
|---|---|
| `website_candidate/frontend/src/{TermsPage,PrivacyPolicy,CookiePolicy,PricingPage}.jsx` | Byte-identical copies of the `frontend/src` versions; routed in the website-candidate app at the same paths. |
| `frontend_backup_pre_v3_public_20260827/src/{TermsPage,PrivacyPolicy,CookiePolicy}.jsx` | Pre-refactor backup copies (historical). |
| `frontend/TermsPage.jsx` (repo root of `frontend/`) | **Legacy, unlinked** ToS claiming "SECR-compliant reports" and `legal@carbontally.com`. Superseded; potential inconsistency. |

### 2.3 Absent documents

- No DPA, Refund Policy, MSA, SLA, or subprocessor schedule exists anywhere in the repository.
- `docs/legal/` exists but is empty.

### 2.4 Related prior research

- `docs/audit/openhands/CARBONTALLY_V3_BANGLADESH_PROCESSING_ENTITY_LEGAL_POLICY_RESEARCH.md` — prior research on the Bangladesh Processing Entity (Babui Limited) international-transfer position. Relied on for the DPA and risk register; not re-verified in this audit.

### 2.5 Public routes and reachability

| Route | Page | Reachable to public visitors? |
|---|---|---|
| `/terms` | Terms of Service | Yes |
| `/privacy` | Privacy Policy | Yes |
| `/cookies` | Cookie Policy | Yes |
| `/pricing` | Pricing | Yes |
| `/data-security` | Data Security | **No route exists** |
| `/privacy-policy` | (link target in DataSecurity.jsx CTA) | **No route exists** (`/privacy` is correct) |

**Route gaps (documentation, not defects to fix here):**
- Data Security content is not publicly reachable despite being the most complete description of CarbonTally's processing and security model.
- The `DataSecurity.jsx` CTA links to `/privacy-policy`, which does not exist; the routed page is `/privacy`.
- There is no routed Refund Policy or DPA page (expected: drafts only at this stage).

---

## 3. B. Application / Data-Flow Audit (current product reality)

### 3.1 Authentication & onboarding

| Capability | Reality | Evidence |
|---|---|---|
| Email/password signup | Yes — Supabase Auth `signUp` | `SelfServiceSignup.jsx`, `Login.js` |
| Email confirmation | Yes (when enabled; config-dependent) | `SelfServiceSignup.jsx` |
| Password sign-in | Yes — `signInWithPassword` | `Login.js` |
| Google OAuth | Yes — `signInWithOAuth provider:'google'` | `Login.js` |
| Magic-link flow | Yes — backend `/api/auth/magic` | `MagicLink.jsx`, backend `auth.py` |
| Organisation creation | Yes — D35 self-service onboarding; server-authoritative; owner created in same transaction; duplicate-signal checks (company number / email domain) | `v3_organizations.py` `POST /api/v3/organizations` |
| Beta-code path | Preserved as optional administrative mechanism at `/beta/signup` | `BetaSignup.jsx` |
| Roles | Customer: owner/admin/member/viewer; Consultant; PE staff (operator/reviewer/qc/admin); internal staff | `organization_members` CHECK, `staff_roles`, `processing_entities` |

### 3.2 Customer data types (all tenant-scoped)

Organisations, members, metadata, facilities, assets, vehicles, suppliers, documents (`organization_files`, `customer_documents`), extracted data (`manual_extraction_items`, `document_processing_queue`), emission factors (incl. customer factors), `calculation_snapshots` (immutable, append-only), `emissions_logs`, audit logs, conversations/messages, notifications, reports. See `CarbonTally_DB_Schema_V3M2.sql`.

### 3.3 Processing pipeline

Durable, server-side, resumable, idempotent pipeline: `enqueued → ingesting → extracting → mapping → validating → calculating → review → completed`, with a `blocked` manual-review gate. Stages persisted in `document_processing_queue`; deterministic `match_request_id` prevents duplicate calculation snapshots.

**Extraction is local and deterministic in production:**
- PDF text: `pdf_engine` / pdfplumber / pypdfium2.
- OCR: Tesseract (pytesseract) with a local ONNX fallback (`rapidocr_onnxruntime`), running on the backend host. **No external OCR service.**
- CSV/XLSX: pandas/openpyxl parsing.
- Mapping: local factor matching (DEFRA and other factor sets + approved customer factors).
- Calculation: server-side `CalculationEngine`, snapshots persisted with provenance.

**AI:** `backend/infra/llm_client.py` provides an OpenAI/Anthropic-compatible chat-completions client, and `backend/engines/ai_extraction.py` implements LLM field extraction. **Neither is wired into any production API route** (grep of `backend/api`, `backend/routes`, `backend/main*.py` finds no construction/use). Only tests and the legacy `engines/workflow.py` reference them. Therefore, **in the current production pipeline no third-party AI/LLM provider receives customer documents.**

### 3.4 Processing Entities & consultants

- Processing Entities are first-class tenants (`processing_entities`), lifecycle active → remediation/suspended → terminated; never hard-deleted.
- PE staff have entity-scoped access only; validation/review/QC are CarbonTally internal gates.
- Human processing is performed by PE staff on assigned items; clarification is mediated (entity → CarbonTally → customer surface). **No direct customer ↔ PE communication.**
- Consultants hold active grants to client organisations; consultant↔client boundaries are server-enforced.
- The public `DataSecurity.jsx` names **Babui Limited (Bangladesh)** as the manual processing entity under "a formal business and data-processing arrangement". This is a data-row/contractual arrangement that must be supported by an actual contract, an IDTA/SCC + transfer risk assessment for any personal data, and a customer-visible subprocessor disclosure. See the prior research document and the Risk Register.

### 3.5 Data retention (N3)

| Setting | Configurable | Enforced | Mechanism |
|---|---|---|---|
| `document_retention_days` | Yes (`/api/v3/settings/retention`) | Yes (only domain) | Soft-delete (`deleted_at`) of expired org documents; dry-run by default |
| `data_retention_days` | Stored in `system_settings` | No | — |
| `audit_log_retention_days` | Stored | No | Deliberately excluded (auditability invariant) |
| `backup_retention_days` | Stored | No | — |

No automated scheduled enforcement is visible; enforcement requires an explicit caller passing `dry_run=False`.

### 3.6 Deletion / export (critical section)

| Capability | Status | Evidence |
|---|---|---|
| Account deletion (user) | **NOT SUPPORTED** — no endpoint, no UI | grep across `backend/api`, `frontend/src/v3` |
| Organisation deletion | **NOT SUPPORTED** — `POST /api/v3/organizations` and `GET /{org_id}` only; no DELETE | OpenAPI, `v3_organizations.py` |
| Member removal | Supported — `DELETE /api/v3/organizations/members/{member_id}` | OpenAPI |
| Document deletion | **PARTIAL** — v2 routes only (`DELETE /api/organizations/files/{file_id}?permanent=…`); **no V3 document delete; no UI delete control** on `DocumentsPage.jsx` | OpenAPI, `routes/organizations/files.py`, frontend |
| Permanent storage deletion | Exists at v2 (`.../files/{file_id}/permanent`) | OpenAPI |
| Data export | **PARTIAL** — `GET /api/v3/exports/emissions.csv`, `emissions.json`, `documents.csv` only; no full-org export | OpenAPI, `v3_exports.py` |
| Facility / asset / supplier / vehicle deletion | Supported (`DELETE` endpoints) | OpenAPI |
| Consultant client removal | Supported (`DELETE /api/v3/consultants/clients/{client_id}`) | OpenAPI |
| Storage object deletion with record | v2 permanent delete removes storage object + record | `routes/organizations/files.py` |

### 3.7 Billing (D37)

- Versioned plans, credit bands (Simple 1 / Standard 2 / Complex 4 / Exceptional quoted), assisted & managed orders, idempotent creation/approval/cancel, provider-neutral payment *records*.
- Module docstring (`v3_billing.py`): **"No payment-provider integration exists."**
- `consultant_billing` has `stripe_subscription_id`/`stripe_customer_id` columns; **unused** (`backend/data/billing.py` explicitly does not touch Stripe-named columns).
- No online checkout, no invoices, no failed-payment handling, no card storage, no pro-rata logic.

### 3.8 Communication

- **Resend** transactional email: org invitations, discovery requests, beta confirmation/invite. Verified consultant senders only for white-label From addresses.
- In-app notifications (Supabase Realtime `postgres_changes`).
- Messaging: org members + active-grant consultants + internal staff with `can_manage_staff`; **PE staff excluded**; Realtime-based.
- No public support desk / ticketing / live chat.

### 3.9 Analytics / tracking / cookies

- No third-party advertising, analytics, or marketing trackers in `frontend/public/index.html`, `frontend/src`, or `website_candidate`.
- Auth session persisted in `localStorage` (not a cookie).
- Cookie banner stores a `cookieConsent` value in `localStorage`.

---

## 4. Policy ↔ Application Consistency Matrix (D)

Legend: ✅ Supported · ⚠️ Partial · ❌ Not supported · ⚠️⚠️ No mechanism exists

| # | Policy statement | Actual capability | Evidence / route | Supported? | Gap / note | Required implementation | Priority |
|---|---|---|---|---|---|---|---|
| 1 | "You may request deletion of your personal data" (Privacy §9) | No account deletion, no org deletion, no customer deletion workflow | No endpoint; `v3_organizations.py`; OpenAPI | ❌ | Privacy right stated without any operational path | Account/org deletion (or clearly-scoped manual process), data-export tooling, documented deletion SLA | P0 |
| 2 | Data retained "only as long as necessary" (Privacy §8) | Retention config exists but only document soft-delete is enforceable | `/api/v3/settings/retention`; `retention.py` | ⚠️ | No automated enforcement; other domains unenforced | Schedule enforcement; define per-category retention in policy | P1 |
| 3 | "Where required, consent … can be withdrawn" (Privacy §6) | No consent-based processing identified; banner is cosmetic | `CookieBanner.jsx` | ⚠️ | Legal basis language is speculative | Confirm legal bases with counsel; remove unsupported bases | P1 |
| 4 | ToS "Pre-launch; no online payments" (Terms §2) | Billing surface exists (D37) but no payment provider | `v3_billing.py` docstring; `PricingPage.jsx` | ✅ | Accurate | None — keep until payment provider added | — |
| 5 | "Refunds" — none documented | No money movement at all | Billing service | ⚠️⚠️ | Refund Policy draft must be explicit that no payments are collected yet | Draft Refund Policy; add payment flow first | P1 |
| 6 | "SECR-compliant reports" (legacy `frontend/TermsPage.jsx`) | Report generation exists; no compliance certification exists | `frontend/TermsPage.jsx` (unrouted) | ❌ | Overclaim; superseded page still in tree | Remove/reconcile legacy TermsPage; remove compliance-claim language | P1 |
| 7 | Cookie Policy "no third-party cookies" | Confirmed — no trackers anywhere | index.html; src grep | ✅ | Accurate | None | — |
| 8 | Cookie Banner "we use cookies … you agree to our use of cookies" | Site sets no cookies; consent stored in localStorage | `CookieBanner.jsx` | ⚠️ | Banner mis-describes behaviour | Reword banner to match actual (no cookies; auth storage notice) | P2 |
| 9 | DataSecurity: "DPAs are used to govern processing" | No DPA exists in repo | grep | ⚠️⚠️ | Claim of contractual state not yet true | Execute DPA with customers; make DPA available | P0 |
| 10 | DataSecurity: "Babui Limited in Bangladesh, formal arrangement, ISO 27001 for Babui's operations" | Processing entity model exists; contract & certification unverified | `DataSecurity.jsx`; tests use "Babui Limited" | ⚠️ | Unverified claims on a public page | Verify contract + certification scope; add to subprocessor register | P0 |
| 11 | Privacy §7 "shared only with service providers … under appropriate safeguards" | Providers: Supabase, Render, Vercel, Resend; no subprocessor schedule published | config.py, env | ⚠️ | Accurate in substance but not discoverable | Publish subprocessor register; reference in Privacy Policy | P1 |
| 12 | "No analytics" claims | Confirmed no analytics code | grep | ✅ | Accurate | None | — |
| 13 | Uptime/SLA — none claimed | None exist; provider SLAs must not be passed through | Render ToS ("as is"); Vercel SLA (Enterprise) | ⚠️⚠️ | No commitment can be made without PO decision | PO decision on availability target + support tiers | P1 |
| 14 | Support contact "hello@carbontally.co.uk" | Email address is used across pages; no support ticket system | footer, pages | ⚠️ | No formal support channel/queue | PO decision on support channels | P2 |
| 15 | "Audit trail" / "evidence traceability" (marketing) | `audit_logs`, `calculation_snapshots` append-only, evidence links | schema; `v3_emissions` | ✅ | Accurate as a product claim | None | — |
| 16 | "Emissions accuracy" — not claimed on current pages | Calculation is server-authoritative with provenance | `calculation_snapshots` | ✅ | Good; keep avoiding accuracy/assurance claims | — | — |
| 17 | Customer-factor handling (precedence) | Approved customer factors take precedence; snapshots preserve factor_id/source | `customer_factors.py`, `calculation_snapshots` | ✅ | Accurate | — | — |
| 18 | Consultant processing | Consultants operate clients with active grants; server-enforced | `v3_consultants.py` | ✅ | Accurate | — | — |
| 19 | PE processing | PE staff scoped to assigned work; no customer comms | `v3_operations.py`, `v3_messaging.py` | ✅ | Accurate | — | — |
| 20 | Data residency | Supabase project region not documented in repo; provider primary processing in US (Vercel/Resend/Render) | env; provider docs | ⚠️ | Residency claim not possible yet | Confirm Supabase region; state in Privacy/DPA | P1 |
| 21 | International transfers | Bangladesh PE + US-based providers require transfer mechanisms | prior research doc | ⚠️ | IDTA/SCC + TIA + contractual backing needed | Contract + transfer assessments | P0 |
| 22 | Messaging boundaries (N1) | Org/consultant/staff only; PE excluded; server-enforced | `v3_messaging.py` | ✅ | Accurate | — | — |
| 23 | "Documents are not exposed through public links" | Private bucket; signed URLs only | `storage.py` | ✅ | Accurate | — | — |

---

## 5. C. Deletion, Billing/Refund, SLA — gap detail

### 5.1 Deletion gaps (must be resolved before the Privacy Policy can state deletion rights honestly)

1. **Account deletion** — no endpoint, no UI. A data subject in the UK/EU cannot delete their account or the personal data associated with it through the product.
2. **Organisation deletion** — no endpoint. Org data persists for the life of the org.
3. **Full data export** — only emissions (CSV/JSON) and documents (CSV) are exportable. No export of extracted data, factors, audit history, or a complete org bundle.
4. **Customer document deletion in V3** — no V3 endpoint and no UI control on the customer Documents page. v2 routes exist but are not exposed in the V3 UI.
5. **Automated retention** — no scheduler; `document_retention_days` soft-delete only; other retention settings unenforced; audit/evidence intentionally never purged.
6. **Backup deletion** — no product-level control over provider backups.

### 5.2 Billing/refund gaps

- No payment provider, no card capture, no invoices, no recurring charge, no failed-payment handling.
- D37 credit model allows granting/adjusting/refunding *credits* (internal admin operations) but no money refunds.
- A Refund Policy can only be drafted as a forward-looking framework with explicit [PO approval required] placeholders.

### 5.3 SLA gaps

- No SLA anywhere. Provider commitments: Render ToS provides services "as is"/"as available"; Vercel's 99.99% availability SLA applies to Enterprise customers of Vercel (its platform, not CarbonTally's service); Supabase publishes status/uptime information for its own platform. None of these may be re-offered as CarbonTally commitments.
- Draft MSA/ToS must use clearly labelled [PROPOSED — REQUIRES PRODUCT OWNER / LEGAL APPROVAL] availability and support targets.

---

## 6. Cookie Policy assessment

**Requires revision:** Partly. The substance of `CookiePolicy.jsx` (no third-party cookies; localStorage auth sessions; clear browser-storage guidance) is accurate and can largely be retained. Required changes:

1. Reword the Cookie Banner copy, which currently implies cookies are used and consent is being given for them ("We use cookies to enhance your experience… you agree to our use of cookies"). The site sets no cookies; the banner should state that and, if kept, describe the auth-session storage and any future consent mechanism.
2. Add a "last updated / version / change control" footer per section 16 of the task.
3. When analytics or marketing services are ever added, consent capture and the policy must be updated before deployment (already flagged in the current page — keep).

---

## 7. L. Engineering / product gaps required before policies can state certain things

| Gap | Policy currently blocked from stating | Required before launch | Owner |
|---|---|---|---|
| Account + organisation deletion workflow (UI + API + cascade semantics) | "You can delete your account/data" | P0 | Engineering |
| Full organisation data export | "You can export your data" | P1 | Engineering |
| V3 customer document deletion + storage cleanup | "You can delete documents" | P1 | Engineering |
| Retention scheduler with per-domain policies | "Retention is automatically enforced" | P1 | Engineering |
| Payment provider integration (real money) | Any money-related refund/invoice language | P1 | Engineering + PO |
| Subprocessor schedule publication + DPA execution workflow | DataSecurity "DPAs are used"; Privacy "shared with providers under safeguards" | P0 | Legal + Engineering |
| Verify Babui contract + ISO 27001 scope; execute IDTA/SCC + TIA | DataSecurity Bangladesh statements; DPA transfers schedule | P0 | Legal + PO |
| Route the Data Security page (`/data-security`) and fix `/privacy-policy` CTA | Public discoverability of security narrative | P2 | Engineering |
| Remove/reconcile legacy `frontend/TermsPage.jsx` | Public consistency of ToS | P1 | Engineering |
| Cookie banner copy alignment | Accurate consent messaging | P2 | Engineering |

## 8. M. Decisions requiring Product Owner approval

1. Availability / uptime target CarbonTally is willing to commit to (if any), and whether service credits are offered.
2. Support tiers and target response times (standard / priority / enterprise).
3. Account and organisation deletion policy (immediate vs. grace period; data-retention-after-deletion).
4. Data retention durations per category (documents, extraction, evidence, reports, messages, logs) and whether evidence may ever be purged.
5. Refund / cancellation commercial rules (pro-rata? credit-only vs money? trial length?).
6. Whether/when the AI extraction engine is enabled and which providers are acceptable.
7. Whether to keep or remove the legacy Terms page and when to publish final (non-draft) policies.
8. Contracting entity name/address and governing law/jurisdiction (England & Wales assumed but unconfirmed).

## 9. N. Issues requiring qualified legal counsel

1. Legal bases for each processing purpose under UK GDPR (contract, legitimate interests, legal obligation — "consent" currently listed without a supporting use case).
2. Controller/processor/subprocessor role analysis for each provider and for the Bangladesh Processing Entity (Model A/B/C from the prior research).
3. IDTA / UK Addendum, EU SCCs, transfer risk assessments for Supabase, Render, Vercel, Resend (all US-headquartered or US-processing) and for Babui Limited (Bangladesh).
4. Whether "audit-ready evidence preparation" language is safe, and final emissions-reporting disclaimers.
5. Retention vs. auditability tension (audit/evidence excluded from purging) and any regulatory minimum retention.
6. Liability cap reasonableness, indemnity scope, and excluded-damages drafting for the ToS/MSA/DPA.
7. Refund Policy compliance with UK/EU consumer law (Consumer Contracts Regulations 2013 etc.) once payments launch.
8. Cookie banner / PECR compliance as soon as any non-essential cookies or analytics are introduced.

---

## 10. Confirmation of no application changes

This audit performed **read-only** inspection only. No database, schema, migration, RLS, backend logic, frontend functionality, authentication, billing, storage, seed data, or production configuration was modified. New files are confined to `docs/legal/` and `docs/legal/draft/`.
