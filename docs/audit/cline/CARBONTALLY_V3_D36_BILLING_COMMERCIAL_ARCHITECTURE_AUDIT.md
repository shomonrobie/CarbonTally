# CarbonTally V3 — D36 Billing & Commercial Architecture Audit

**Date:** 2026-08-23
**Type:** AUDIT / GAP-ANALYSIS / ARCHITECTURE — **no implementation**
**Status:** D36 COMPLETE — HARD STOP. No D37 started.

---

## 1. Executive verdict

> **Can the existing CarbonTally architecture support the approved commercial model (Subscription + Automated Processing Credits + Assisted Processing + Managed Processing + Enterprise/B2B/API), including both CREDIT and STANDARD billing modes, without another major redesign?**

**Verdict: PARTIALLY — the tenancy and processing foundations are sound and reusable, but the billing layer itself is effectively greenfield.**

* The **tenancy anchor (organizations), processing pipeline (manual-extraction batches/items), evidence chain (D33), storage (D32 private bucket + `size_bytes`), audit (`audit_trail`), and event infrastructure (`domain_events`)** are directly reusable and do NOT need a redesign.
* The **billing tables that exist (`customer_subscriptions`, `usage_tracking`, `consultant_billing`) are schema-only**: no repository, no API, no metering, no entitlement logic, no webhooks, no UI. They are NOT sufficient for the approved model and are NOT provider-neutral (they hard-code Stripe column names).
* **One P0 security defect must be fixed before ANY billing is wired:** the `authenticated` role can INSERT/UPDATE/DELETE `usage_tracking` and `customer_subscriptions` rows, and UPDATE the `organizations.subscription_*` / `trial_*` columns, directly via PostgREST (the browser Supabase client). A customer could rewrite their own usage, plan, limits and trial/subscription state — and would be able to self-grant credits the moment credits exist.
* The approved commercial model requires **new additive schema** (credit ledger, price book, complexity classifier outputs, processing orders, managed contracts, webhook/event ingestion, invoice/commercial records, per-customer `billing_mode`) plus a **provider-neutral billing service**. This is a substantial build, but it is an **additive layer over the existing architecture — not a major redesign** of the current application model.

**Verdict summary:** The architecture **can** support the approved commercial model with an additive billing layer (D37), provided (a) the P0 billing-RLS defect is closed first, and (b) the Product Owner decisions in §29 are ratified. No redesign of the tenancy/processing/evidence model is required.

---

## 2. Existing billing architecture inventory

| Surface | State |
|---|---|
| Backend billing service | **NONE** — no repository, no API, no entitlement, no metering writes. |
| Webhooks | **NONE** — no webhook endpoint; no signature verification; no event ingestion. (A D24-era design doc describes a target `supabase/functions/stripe-webhook` that does not exist in the repository.) |
| Billing API | **NONE** — no `/api/v3/billing*` or equivalent. |
| Frontend billing UI | **NONE** — no subscription, credit, checkout, invoice or pricing screen. |
| Metering | **NONE** — `usage_tracking` is never written; `customer_subscriptions.*_used` are never updated. |
| Entitlement enforcement | **NONE** — no limit check before any metered action (uploads/processing/reports run ungated). |
| Pricing / plan catalogue | **NONE** — no price book, no plan catalogue, no complexity classifier (document classifier classifies document TYPE, not complexity). Commercial docs live in `docs/Pricing/` (Product-Owner-owned; not code). |
| Commercial records | **NONE** — no order/invoice/transaction tables. |

The only billing-adjacent application code: `data/organizations.py` exposes the org profile with billing **read-only** fields (customer admin cannot change `subscription_status`/`trial_*` via the API — the API guard is correct), and `data/manual_extraction.py` reads/writes legacy batch `total_cost`/`price_per_page` columns that are always `0.0`/`NULL` in practice.

## 3. Schema inventory

### `customer_subscriptions` (org-scoped; Stripe-flavoured)
`id`, `organization_id` (FK, NOT NULL), `plan` (NOT NULL), `status` (CHECK: trialing/active/past_due/paused/cancelled/expired — **incomplete** vs current Stripe status set), `ai_extraction_limit`, `ai_extraction_used`, `batch_upload_limit`, `batch_upload_per_day`, `manual_extraction_pages_included`, `manual_extraction_pages_used`, `price_per_ai_extra`, `price_per_manual_page`, `currency`, `features` (jsonb), `stripe_subscription_id`, `stripe_customer_id`, `stripe_price_id`, `billing_period_start`, `billing_period_end`, `created_at/by`, `updated_at/by`, `cancelled_at/by`.

### `usage_tracking` (org-scoped; per-month rollup)
`id`, `organization_id`, `usage_date`, `usage_month`, `ai_files_processed`, `batch_files_uploaded`, `manual_pages_extracted`, `reports_generated`, `total_storage_bytes`, `created_at`, `updated_at`, `UNIQUE (organization_id, usage_month)`. **Never written.**

### `consultant_billing` (consultant-scoped; optional `client_id`)
`id`, `consultant_id`, `client_id` (nullable), `plan`, `auto_extraction_limit`, `manual_extraction_credit`, `auto_extraction_used`, `manual_extraction_used`, `billing_cycle`, `subscription_start_date/end_date`, `auto_extraction_price`, `manual_extraction_price`, `last_invoice_date`, `next_invoice_date`, `stripe_subscription_id`, `stripe_customer_id`, `created_at`, `updated_at`, `currency`.

### `organizations` billing columns
`currency`, `billing_contact_email`, `billing_contact_name`, `subscription_status`, `trial_start_date`, `trial_end_date`, `subscription_tier`, `subscription_id`, `billing_address`, `tax_rate`, `tax_region`, `carbon_tax_region`.

### Reusable non-billing schema
`manual_extraction_batches` (order-like: total_documents/pages, total_cost, price_per_page, currency, status, assigned_to/by, sla_deadline, estimated/actual_completion_date, qc_approved, sla_breached, customer_notes, staff_notes), `manual_extraction_items` (file_id, document_type, status, QC, customer review/approval), `organization_files` (`size_bytes`, `bucket`, D32 private), `processing_entities` (minimal), `audit_trail` (append-only, D33), `domain_events` (event_type, correlation_id, aggregate_id/type, payload), `document_processing_queue`, `upload_batches` (batch_type, manual_extraction_requested/link).

## 4. API inventory

No billing endpoints. The processing surface that billing will hook into:

* `POST /api/v3/documents` (upload → auto-enqueues into a "Uploads" manual-extraction batch + creates a pending item — **the natural per-file automated-credit hook point**).
* `GET/POST /api/v3/processing/batches/*` (start/complete/cancel), `/api/v3/processing/items/*` (start/extract/map/validate/calculate/customer-review).
* `GET /api/v3/organizations/{id}/profile` (returns billing fields **read-only**).
* No usage/credit/order/invoice endpoints exist.

## 5. Frontend inventory

No billing/subscription/credit/checkout/invoice/pricing UI. Frontend occurrences of "billing" are data-domain ("Billing Period Start" of a utility invoice) and the Supabase auth `subscription` listener (unrelated). The browser ships the raw Supabase client (`createClient(supabaseUrl, supabaseAnonKey)`), which makes the §6 P0 reachable directly from the customer's browser.

## 6. RLS / security inventory

| Table | RLS | Policies | Finding |
|---|---|---|---|
| `usage_tracking` | ON | 4 (tenant SELECT/INSERT/UPDATE/DELETE) | **P0** — any org member can insert/update/delete metering rows via PostgREST. |
| `customer_subscriptions` | ON | 4 (tenant SELECT/INSERT/UPDATE/DELETE) | **P0** — any org member can rewrite plan/limits/`*_used`/status/stripe ids. |
| `consultant_billing` | ON | **0** (deny-by-default) | Safe today, but **no legitimate path** (consultant cannot even read their own billing row); column grants to `authenticated` are armed but inert. |
| `organizations` | ON | SELECT (member/consultant), UPDATE (member) | **P0** — no column REVOKE on billing columns: members can UPDATE `subscription_status`, `subscription_tier`, `subscription_id`, `trial_start_date/end_date`, `tax_rate`, `currency` directly via PostgREST. |
| `manual_extraction_batches` | ON | 5 (tenant INSERT/UPDATE/DELETE + entity SELECT) | P2 — tenants can rewrite order-like batch rows (cost/status/SLA). |
| `organization_files` | ON | 4 (tenant + storage) | OK — D32 private storage + signed URLs authoritative. |

Column grants for `authenticated` confirmed via `information_schema.column_privileges`: INSERT/UPDATE on every `usage_tracking` metering column, every `customer_subscriptions` billing column, and the `organizations` subscription/trial columns.

No webhook authenticity, idempotency, replay protection, duplicate-credit prevention, or billing audit logging exists (nothing to protect yet — but the surface is entirely unguarded).


## 7. Subscription readiness

| Requirement | State |
|---|---|
| Subscription row per organisation | PARTIAL — `customer_subscriptions` exists (org-scoped, plan/status/period/cancel). |
| Plan catalogue / price book | **MISSING** — plans are free-text `plan`; no catalogue, no price, no billing_mode. |
| Status lifecycle | PARTIAL — CHECK has Stripe statuses but the set is incomplete and there is no status-transition code. |
| Entitlement derivation from subscription | **MISSING** — no `features` evaluation; no limit enforcement. |
| Renewal / billing-period advance | **MISSING**. |
| `billing_mode` (CREDIT / STANDARD) | **MISSING** — not represented anywhere. The org-scoped design supports per-customer mode (fits the tenancy anchor); a global flag would be insufficient (D36 §11). |

## 8. Credit-ledger readiness

| Requirement | State |
|---|---|
| Credit ledger (per-org) | **MISSING** — no ledger table; `*_used` counters on `customer_subscriptions` are period-reset counters, not a ledger. |
| Paid vs promotional credits | **MISSING**. |
| Rollover / expiration rules | **MISSING**. |
| Adjustments / refunds | **MISSING**. |
| Audit trail for credit events | PARTIAL — `audit_trail` + `domain_events` are reusable patterns, but no credit events exist. |

## 9. CREDIT mode readiness

Automated processing consumes credits (Simple 1 / Standard 2 / Complex 4 / Exceptional quote).

| Requirement | State |
|---|---|
| Per-file automated processing hook | PARTIAL — every upload creates a pending extraction item (`POST /api/v3/documents` → "Uploads" batch → item). The hook point exists; **no credit is metered**. |
| Complexity classification | **MISSING** — `utils/document_classifier.py` classifies document TYPE (invoice_fuel, export_erp, spreadsheet_emissions…), not complexity. No Simple/Standard/Complex/Exceptional concept. |
| Configurable complexity rules | **MISSING** (no price book / rule table). |
| Credit consumption on processing result | **MISSING** — `calculate_item` completes with no ledger effect. |
| "Do not charge for the calculation engine" rule | N/A — nothing charges today; the rule must be encoded in the future metering design (charge the document, not the multiplication). |
| Balance / insufficient-credit handling | **MISSING**. |

## 10. STANDARD mode readiness

| Requirement | State |
|---|---|
| Monthly processing allowance model | **MISSING** — `ai_extraction_limit`/`manual_extraction_pages_included` are the closest primitive (period limits) but are unused and not a real allowance workflow. |
| Additional-processing purchase | **MISSING**. |
| Per-customer mode (`billing_mode`) | **MISSING** — must belong to the customer/subscription/contract, not global config. |
| Default-mode-for-new-customers + no-silent-migration | Fits the org-scoped design; no mechanism exists yet (needs `billing_mode` + admin controls). |

## 11. Structured-data readiness

| Requirement | State |
|---|---|
| Record/row volume metering (1,000 / 10,000 / 50,000 / 250,000 / 1,000,000 bands) | **MISSING** — no row-count capture or band evaluation. Extracted CSV/Excel/JSON rows exist in item `extracted_data` but are not aggregated to a billable unit. |
| Configurable bands | **MISSING**. |
| Future complexity + custom large datasets | **MISSING** — nothing blocks the design, but nothing exists. |

## 12. Assisted Processing readiness

| Requirement | State |
|---|---|
| Processing order / batch | PARTIAL — `manual_extraction_batches` is order-like (documents/pages/cost/status/SLA/assignment/QC/completion) and is tenant-writable. |
| Document count / complexity | PARTIAL — count exists; complexity missing. |
| Estimate | PARTIAL — `total_cost`/`price_per_page` exist but are never priced (always 0/NULL). |
| Customer approval | **MISSING at order level** — item-level `customer_review` exists (D23/D25), but no order estimate→approval flow. |
| Payment state | **MISSING**. |
| Processing Entity assignment | PARTIAL — `entity_id` on batches/items exists; assignment workflow exists (D22). |
| QC / rework | PARTIAL — QC fields exist; rework state is implicit. |
| Completion / cancellation / refund | PARTIAL — completion + cancel exist on batches; refund state **MISSING**. |
| Evidence / provenance | PARTIAL — D33 item↔file linkage exists; order-level evidence missing. |

## 13. Managed Processing readiness

| Requirement | State |
|---|---|
| On-demand Managed Batch | PARTIAL — the batch container could carry it, but there is no managed-order type/marker. |
| Enterprise Managed Contract | **MISSING** — no contract representation (terms, SLA, credits-included, volume commitment). |
| Separation from automated credits + assisted orders | **MISSING** — no distinct commercial object. |


## 14. Storage-metering readiness

| Requirement | State |
|---|---|
| Per-file size | VERIFIED — `organization_files.size_bytes` is captured at upload. |
| Per-org storage rollup | PARTIAL — `usage_tracking.total_storage_bytes` column exists but is **never written**. |
| Free allowance vs paid overage | **MISSING**. |
| ~100% markup pricing philosophy | **MISSING** (business rule, not implementable until metering exists). |
| D32 private storage/security | VERIFIED — `documents` bucket is PRIVATE; signed URLs authoritative. |

## 15. Consultant / multi-client billing readiness

| Requirement | State |
|---|---|
| Per-client billing isolation | PARTIAL — `consultant_clients` has `billing_plan`/`billing_cycle`; `consultant_billing.client_id` is nullable. No risk of cross-client merge today (nothing is stored). |
| Consultant billing access | **BROKEN by design** — `consultant_billing` has 0 policies (deny-by-default), so no legitimate path exists for consultants OR CarbonTally staff via REST; only service role. |
| RLS/authorization implications | P2 — a real consultant billing surface needs scoped policies (consultant-firm-member or staff) plus service-role writes; must be designed so one consultant cannot see another's clients. |

## 16. Processing Entity separation

| Requirement | State |
|---|---|
| Entity assignment | PARTIAL — `processing_entities` (id/name/description/status) + batch/item `entity_id` + staff scoping (D20/D22). |
| Processor compensation | **MISSING** — no compensation columns or ledger. |
| Customer price vs processor compensation separation | **MISSING** — the approved model requires two independent amounts; no representation. |
| Organization isolation | PARTIAL — entity staff are work-scoped (D20); billing for entities is absent. |

## 17. Refund / cancellation / chargeback readiness

| Requirement | State |
|---|---|
| Subscription cancellation | PARTIAL — `cancelled_at/by` + `status='cancelled'` (no lifecycle code). |
| End-of-period cancellation | **MISSING**. |
| Failed payment / dunning | **MISSING**. |
| Refund / partial refund / credit adjustment | **MISSING** (no ledger). |
| Processing-order cancellation | PARTIAL — batch `cancel` endpoint; refund state missing. |
| Chargeback / dispute | **MISSING**. |
| Reactivation | **MISSING**. |

## 18. Commercial-record / invoice readiness

| Requirement | State |
|---|---|
| Application-level commercial records | **MISSING** — no order/invoice/transaction tables. `audit_trail`/`domain_events` can back lineage but are not commercial records. |
| Legal/tax invoices + provider receipts | **MISSING** (correctly out of scope for now; must be distinguished from app records). |
| Invoice template | **MISSING** — do not build before the commercial model is fixed (D36 §29). |

## 19. Provider-abstraction readiness

| Requirement | State |
|---|---|
| CarbonTally-owned concepts (customer/subscription/plan/entitlement/ledger/usage/order) | PARTIAL at schema level only; **no billing service**. |
| Provider adapter (CarbonTally Billing Service → Stripe/PayPal/future) | **MISSING**. |
| Provider identifiers isolated | **MISSING** — Stripe ids are hard-coded columns (`stripe_customer_id`, `stripe_subscription_id`, `stripe_price_id`) on `customer_subscriptions`, `consultant_billing`, `organizations.subscription_id`. Provider-neutral naming (`provider_customer_id` + `provider`) is required. |

## 20. Webhook / idempotency readiness

| Requirement | State |
|---|---|
| Webhook endpoint + signature verification | **MISSING**. |
| Event idempotency / replay protection | **MISSING** — `domain_events` can store processed provider events, but no ingestion exists. |
| Duplicate-payment / duplicate-credit prevention | **MISSING** — and the P0 (§6) means any future credit grant must be service-role-only with unique constraints. |
| Secret management | PARTIAL — env-var based (`SUPABASE_SERVICE_KEY`, `RESEND_API_KEY`); no webhook-signing secret handling. |

## 21. Tax / accounting data readiness

| Requirement | State |
|---|---|
| Customer country / B2B-B2C | PARTIAL — `organizations.country`; B2B/B2C not captured. |
| Amount / currency | PARTIAL — org `currency`; no transaction amounts. |
| Tax amount / tax region | PARTIAL — `tax_rate`, `tax_region`, `vat_*` columns exist; no per-transaction tax. |
| Payment provider / transaction id / order-invoice id | **MISSING** (no transactions). |
| Refund / credit / subscription / service type | **MISSING**. |

No legal/tax conclusions are provided (external UK accountant/tax adviser boundary preserved).


## 22. Schema gaps (additive, D37)

1. **`billing_mode`** per organisation/subscription (CREDIT | STANDARD) + default-mode admin control (no silent migration).
2. **Credit ledger** (`billing_credit_ledger`): org, source (purchase/promotional/adjustment/refund/emergency), balance, rollover/expiry, correlation to subscription/order, append-only.
3. **Price book / plan catalogue** (`billing_price_book`): automated-credit classes (Simple 1/Standard 2/Complex 4/Exceptional), structured-data bands, assisted-processing complexity prices, storage allowance+overage.
4. **Complexity classification** output on items/files (class + rule version + confidence) — driven by CarbonTally (never customer-supplied).
5. **Processing orders** (assisted/managed): estimate → approval → payment state → assignment → QC → completion → cancellation/refund, with per-item complexity and customer-price vs processor-compensation separation.
6. **Managed contracts** (enterprise/on-demand): terms, SLA, included credits, volume commitment.
7. **Provider webhook/event ingestion** (`billing_webhook_events` with unique provider-event-id) for idempotency/replay.
8. **Commercial records** (`billing_orders`, `billing_invoices` app-level) distinct from legal invoices.
9. **Emergency completion allowance** record (allowance grant, job link, reason, reconciliation, offset/deduction, abuse prevention).
10. **Provider-neutral identifiers** (`provider`, `provider_customer_id`, `provider_subscription_id`, `provider_price_id`) replacing/augmenting hard-coded Stripe columns.

## 23. API gaps (D37)

1. Billing service core: subscription, entitlement, plan, price book, ledger, usage, order CRUD (service-role authoritative).
2. Credit consumption + insufficient-balance handling inside the processing pipeline.
3. Assisted-processing order workflow (estimate → approval → payment → assign → complete → cancel/refund).
4. Managed contract lifecycle.
5. Storage allowance + overage computation.
6. Webhook ingestion endpoints (signature-verified) + idempotent processing.
7. Customer-facing billing surface (balances, orders, invoices) — org-scoped, `ensure_org_access`.
8. Admin surfaces (billing mode default, adjustments, refunds, emergency allowance) — staff-only with audit.
9. Reconciliation/audit export (payment → subscription/order → entitlement → credit grant → credit consumption → processing result).

## 24. Frontend gaps (D37)

Billing/credit/order/invoice screens (customer), billing admin screens (staff), and the removal of any reliance on tenant-writable billing rows (use the service API, never direct PostgREST writes to billing tables).

## 25. Security gaps (D37, ordered)

1. **P0 — lock down billing RLS/grants**: REVOKE `authenticated` INSERT/UPDATE/DELETE on `usage_tracking`, `customer_subscriptions`; column REVOKE on `organizations` subscription/trial columns; service-role-only writes; unique constraints for idempotency.
2. **P0 — no self-grant path**: credit grants only via service-role billing service, append-only ledger, unique (source, external_event_id).
3. **P1 — webhook authenticity + idempotency + replay protection**.
4. **P1 — duplicate-payment/duplicate-credit prevention**.
5. **P1 — billing authorization**: org isolation on all billing endpoints; consultant isolation; entity separation; staff permission gating.
6. **P2 — billing audit logging** (append-only `audit_trail` actions for every ledger/order/invoice event).



## 26. Recommended architecture (D37 target)

```
                     ┌─────────────────────────────────────────────┐
                     │        CarbonTally Billing Service         │
                     │  (provider-neutral; service-role writes)    │
                     │  customer · subscription · plan · price     │
                     │  book · entitlement · credit ledger ·       │
                     │  usage · processing order · invoice         │
                     └───────────────┬─────────────────────────────┘
                                     │
            ┌────────────────────────┼────────────────────────────┐
            ▼                        ▼                            ▼
   Provider Adapter (Stripe)  Provider Adapter (PayPal)   Future adapters
   (isolated provider ids, checkout, webhooks → billing service)
                                     │
                  ┌──────────────────┴──────────────────┐
                  ▼                                     ▼
        Supabase Auth + RLS                     Processing pipeline
        (org tenancy, D32 storage,              (upload → classify →
        D33 evidence, signed URLs)              extract → map → calculate)
                                                    │
                                                    ▼
                                          Entitlement check + credit
                                          consumption (billing service)
```

Design principles (matching D36 §12/§13): the payment provider answers "did the customer pay?"; CarbonTally answers "what is the customer entitled to?"; provider ids stay isolated in adapter-owned columns; every credit/order/invoice change is append-only and audited; customers can never write billing state (service-role only); the existing org/RLS/evidence/storage architecture is reused unchanged.

## 27. D37 implementation plan (recommended sequence)

1. **D37-0 — Billing security lockdown (P0, smallest first):** RLS/column-grant REVOKEs so the `authenticated` role cannot write `usage_tracking`, `customer_subscriptions`, or `organizations` billing columns; add unique idempotency keys; re-run RLS integration suite.
2. **D37-1 — Provider-neutral billing core:** billing service + core tables (subscription, plan/price book, entitlement, `billing_mode`, credit ledger, usage, orders, invoices app-level) + provider-neutral identifiers.
3. **D37-2 — Metering + CREDIT mode:** complexity classifier (CarbonTally-driven) + price-book classes + consumption hooks in the processing pipeline + structured-data band metering + insufficient-balance behavior.
4. **D37-3 — STANDARD mode:** allowance model + per-customer `billing_mode` + default-mode admin control (no silent migration).
5. **D37-4 — Assisted Processing orders:** estimate → customer approval → payment state → entity assignment → QC → completion → cancellation/refund; customer-price vs processor-compensation separation.
6. **D37-5 — Managed Processing:** managed contract + on-demand managed batch.
7. **D37-6 — Storage metering:** allowance vs overage rollup from `organization_files.size_bytes`.
8. **D37-7 — Provider adapter + webhooks:** first provider (subject to §29), signature verification, idempotent event ingestion, credit/entitlement effects.
9. **D37-8 — Commercial records + tax/accounting export:** app-level invoices/orders + accounting data export (country, amounts, currency, tax, provider, transaction/order ids, service type) for the external accountant.
10. **D37-9 — Billing UI:** customer billing/credits/orders/invoices + staff admin (adjustments, refunds, emergency allowance, mode default).

Each step is additive + idempotent + RLS-safe + tested (unit + RLS integration + frontend + build), consistent with the D35 discipline.

## 28. Risks

| # | Risk | Level |
|---|---|---|
| 1 | **P0 billing-RLS defect ships unnoticed** if billing tables are wired before the lockdown | HIGH |
| 2 | Customer self-entitlement/self-metering via PostgREST (today, on existing tables) | HIGH (today) |
| 3 | Provider identifier coupling (hard-coded Stripe columns) makes provider-switching expensive if not addressed in D37-1 | MEDIUM |
| 4 | Complexity classification accuracy directly drives revenue; needs a classification rules table + versioning + review | MEDIUM |
| 5 | Credit-rollover/expiry rules require business decisions before the ledger is finalized | MEDIUM |
| 6 | Managed Processing and Enterprise contracts have the least schema precedent — highest design uncertainty | MEDIUM |
| 7 | Tax/accounting data must satisfy an external adviser; gaps (B2B/B2C, per-transaction tax) need a decision | LOW–MEDIUM |
| 8 | No webhook/infra precedent in the current backend (target doc only) — D37-7 needs an infra decision | MEDIUM |

## 29. Open Product Owner decisions (BUSINESS DECISION REQUIRED)

1. Final provider selection (Stripe / PayPal / other) — currently NOT selected; Paddle/Lemon Squeezy not selected as MoR.
2. Final automated-credit classes + complexity definition + "Exceptional = quote" process.
3. Structured-data bands (the §5 table is a commercial hypothesis).
4. Assisted-processing complexity prices (the §6 table is a hypothesis).
5. Managed Processing V1 (on-demand batch + enterprise contract) commercial terms.
6. Storage allowance size + overage price (≈100% infrastructure markup).
7. Credit rollover/expiry rules + paid vs promotional treatment.
8. Emergency completion allowance parameters (≈10% baseline; reconciliation/offset).
9. STANDARD-mode allowance terms + `billing_mode` default for new customers (no silent migration).
10. B2B/B2C capture + per-transaction tax handling for the accounting/tax boundary.

## 30. Final readiness verdict

| Dimension | Verdict |
|---|---|
| Tenancy / org model (reused) | READY — no redesign |
| Processing pipeline (reused) | READY — metering hooks are additive |
| Evidence (D33) / storage (D32) / audit / events (reused) | READY |
| Billing schema | PARTIALLY REUSABLE — existing 3 tables are a thin, provider-coupled skeleton; the approved model needs a substantial additive layer |
| Billing security | **P0 GAP** — tenant-writable billing rows/columns must be locked down before any billing feature |
| Billing service / API / UI / webhooks | NOT PRESENT — greenfield |
| CREDIT + STANDARD modes | NOT SUPPORTED today; architecturally feasible per-customer (org-scoped) |
| Schema redesign required? | **NO major redesign** — additive layer over the existing architecture (new tables + `billing_mode` + RLS lockdown), reusing the current tenancy/processing/evidence/storage model |
| Can D37 begin? | **YES, conditionally** — after the D36 report, with D37-0 (billing security lockdown) first and the §29 decisions ratified |

**Classification summary:** P0: billing RLS/self-entitlement defect (1) — no other P0s. P1: billing service/API/UI/webhooks/entitlement/metering all absent; `billing_mode` absent; provider neutrality absent; complexity classification absent; assisted-order approval/payment/refund absent; structured-data metering absent. P2: storage rollup+allowance, consultant billing policies, batch tenant-writes, audit-logging for billing, emergency allowance. P3: chargeback/dispute UI, rework state, document-binary export (already tracked). BUSINESS DECISION REQUIRED: §29 (10 items). EXTERNAL CONFIGURATION REQUIRED: provider account/keys, webhook signing secrets, invoice/accounting integration with the external adviser.

---

## Appendix — tests executed (§23)

* Backend unit suite: `pytest tests/unit` — **1020 passed** (exit 0).
* RLS behaviour integration: `pytest tests/integration/test_v3_rls_behavior.py` — **15 passed** (exit 0) on the dedicated `carbontally_test` database (main-DB protection guard intact).
* Frontend: `react-scripts test` (`v3/__tests__/api`) — **21 passed**.
* No migrations/schema changes were made (audit-only).
* The RLS suite does **not** currently cover `usage_tracking` / `customer_subscriptions` tenant-write behaviour — a D37-0 test gap to close.

## Files inspected

`supabase/migrations/00000000000000_init_schema.sql` (§1449–1650), `supabase/migrations/20260803000000_rc2_rls.sql`, `supabase/migrations/20260823000000_d32_private_documents_storage.sql`, `supabase/config.toml`, live `information_schema` / `pg_policies` / `column_privileges` for the billing tables and organizations, `backend/data/organizations.py`, `backend/data/manual_extraction.py`, `backend/api/v3_documents.py`, `backend/api/v3_processing_workflow.py`, `backend/domain/partners.py`, `backend/utils/document_classifier.py`, `frontend/src/supabaseClient.js`, `frontend/src/Login.js`, `frontend/src/App.js`, `docs/Pricing/` (commercial docs, not code), D34 report billing section, Kimi architecture docs (target-only).

---

**HARD STOP — D36 complete. No D37 started.**

