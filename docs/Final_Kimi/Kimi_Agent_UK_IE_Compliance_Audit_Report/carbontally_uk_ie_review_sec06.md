## 12. Recommended Changes

This chapter consolidates Sections 4–11 into one deduplicated action register: where findings converge on a single fix, it appears once, carrying all source finding IDs (prefixed D1/D2/D3 by audit dimension). Nothing below requires redesign; every action is an additive column, CHECK constraint, index or procedure, compatible with the approved ADRs.

### 12.1 v1.0 Launch Blockers

These items gate go-live: each blocks a legitimate UK/IE data path, permits silently wrong numbers, or leaves a security or compliance obligation unenforceable.

| # | Change | Affected table.column | Severity | Effort | Migration Risk | Source finding IDs |
|---|---|---|---|---|---|---|
| 1 | Add `eircode`; relax `postcode` NOT NULL; postcode-XOR-eircode conditional CHECK keyed on `country` | `facilities.eircode`, `facilities.postcode` | 🔴 Critical | Small | Medium | D1-B1, D1-B2, D3-D5, D2-F1 |
| 2 | Constrain country to ISO 3166-1 {GB, IE} — the key every jurisdiction rule reads | `organizations.country`, `facilities.country`, `suppliers.country`, `consultant_profiles.country` | 🔴 Critical | Small | Low | D1-A5, D1-D3 |
| 3 | Currency CHECK {GBP, EUR}; app-level EUR default when `country = 'IE'` | Six `currency` columns + `system_settings.default_currency` | 🔴 Critical | Small | Low | D1-A6, D1-B9 |
| 4 | Country-conditional format CHECKs: GB/IE VAT; CH 8-char/CRO 6-digit company numbers; UK postcode and Eircode regexes | `*.vat_number`, `*.company_number`, `*.postcode`, `*.eircode` | 🟠 High | Small | Low | D1-A1, D1-A2, D1-A3, D1-B3, D1-B4, D1-B5, D3-C9 |
| 5 | Factor model: add `unit`, `scope`, `factor_source`/`factor_set`, `country`; UNIQUE `(reporting_year, activity_type)` | `defra_conversion_factors.*`; FK `emissions_logs.defra_factor_id` | 🔴 Critical | Medium | Medium (backfill) | D1-A12, D2-E1, D3-C10 |
| 6 | Emission-entry qualifiers: unit, scope, facility attribution | `emissions_logs.unit_code`, `.scope`, `.facility_id` | 🔴 Critical | Medium | Medium | D1-A13 |
| 7 | Tenant lifecycle columns — suspend churned customers without deleting evidence | `organizations.is_active`, `organizations.archived_at` | 🔴 Critical | Small | Low | D2-A1, D3-B6 |
| 8 | Soft-delete + typed invoice fields + content hash on the primary document entity | `customer_documents.deleted_at`, `.document_number`, `.document_date`, `.currency`, `.net_amount`, `.vat_amount`, `.gross_amount`, `.file_checksum` | 🔴 Critical | Medium | Low | D2-A3, D2-C5, D2-A5 |
| 9 | Add the missing billing currency | `consultant_billing.currency` (+ `invoice_number_prefix`) | 🟠 High | Small | Low | D1-§C |
| 10 | Index baseline: FK indexes on ~30 tenant keys; tenant composites; queue-claim composites for `SKIP LOCKED`; `pg_trgm` GIN on name/email columns | `organization_id` passim; `processing_queue(queue_status, priority_score, sla_deadline)`; `organizations.name`, `suppliers.name` | 🔴 Critical | Medium | Low | D3-A1, D3-A2, D3-A9, D2-C1 |
| 11 | Verify the RLS policy matrix; resolve nullable `organization_id` (~15 tables); `client_access` array-containment policies with GIN support | `organization_id` passim; `consultant_firm_members.client_access` | 🔴 Critical | Large | Medium | D3-B1, D3-C4 |
| 12 | Verify every FK with explicit ON DELETE actions; RESTRICT on audit/financial tables | passim (e.g. `emissions_logs.asset_id`, `messages.conversation_id`) | 🔴 Critical | Medium | Medium | D3-C1 |
| 13 | Hash secrets at rest (SHA-256 + lookup prefix, rotation columns) | `consultant_profiles.api_key`, `password_reset_tokens.token`, `user_invitations.token`, `beta_access_codes.magic_token` | 🔴 Critical | Small | Low | D3-B2, D3-E3 |
| 14 | Add UK `sort_code`; mask bank details last-4; encrypt at rest in v1.1 | `suppliers.sort_code`, `.bank_account`, `.iban`, `.swift_code`, `.bank_name` | 🔴 Critical | Medium | Medium | D1-A9, D3-B9 |
| 15 | Drop UNIQUE on reset-token user (enables reset DoS); keep UNIQUE on `token` | `password_reset_tokens.user_id` | 🟠 High | Small | Low | D3-B3 |
| 16 | Per-class retention schedule (financial/emissions ≥ 6 years; logs 12–24 months) + first pg_cron jobs | `system_settings.audit_log_retention_days`/`.data_retention_days`; append-only log tables | 🔴 Critical | Medium | Medium | D3-D1, D3-A5 |
| 17 | Anonymise-in-place erasure procedure, tested before the first DSAR | `users.email` and ~40 referencing FK columns | 🔴 Critical | Medium | Medium | D3-D2 |
| 18 | Seed cleanup: remove `.de`/`.fr`/`.fi`/`.ai` users; add IE org + IE facility fixtures (the B1 regression guard) | seed block; `users.password_hash` | 🟠 High | Small | Low | D1-G1, D1-G5, D2-F9, D3-B5 |
| 19 | Deprecate `pending_invites` (no token/expiry) and one identical notification delivery table | `pending_invites`; `notification_delivery` vs `notification_delivery_log` | 🟠 High | Small | Low | D2-B4, D2-B5 |
| 20 | NOT NULL DEFAULTs on hot-path booleans/timestamps (tri-state NULLs break filters) | `is_active`, `is_read`, `is_deleted`, `email_verified`, `sla_breached`, `created_at` passim | 🟠 High | Medium | Low–Medium | D3-C2 |
| 21 | CHECK value lists (not PG enums, per ADR) on free-text statuses — queue/billing/role columns first | `processing_queue.queue_status`, `document_processing_queue.status`, `customer_documents.status`, `organization_members.role` | 🟠 High | Medium | Medium | D3-C3, D2-C2, D2-F6 |
| 22 | Money precision `numeric(12,2)` + CHECK ≥ 0; resolve duplicate VAT/tax-rate settings | `consultant_billing.*_price`, `customer_subscriptions.price_per_*`, `system_settings.default_vat_rate`/`.default_tax_rate` | 🟠 High | Small | Low | D3-C5, D1-§F |
| 23 | Widen file sizes to int8 (2 GB int4 overflow); mime allowlist + size CHECKs | `file_attachments.file_size`, `mime_type`/`file_type` | 🟠 High | Small | Low | D3-A6 |
| 24 | Timezone CHECK {Europe/London, Europe/Dublin}; E.164 phones; email lowercase; range CHECKs (emissions ≥ 0, percentages 0–100, `end_date ≥ start_date`) | `organizations.timezone`, `business_hours.timezone`; phone/email columns passim | 🟠 High | Small | Low | D1-A7, D1-B6, D1-§E |
| 25 | Declare structured address canonical; demote text blobs to display cache | `organizations.registered_address`/`.billing_address`, `suppliers.address` | 🟠 High | Small | Low | D1-D2 |
| 26 | Resolve auth ownership; add lockout columns behind existing settings | `users.password_hash`, `users.failed_login_attempts`, `users.locked_until` | 🟠 High | Small | Low | D3-B5, D3-B4 |

Items 1–3 are the hard gate: an Irish facility cannot be inserted, and every conditional rule keys off columns that today accept "UK", "gbp" and "euro". Items 5–8 protect reported numbers; 10–17 close the performance, isolation, secrets and GDPR gaps; the rest is validation hygiene.

### 12.2 v1.1 Hardening

Post-launch hardening, same register format; none blocks go-live.

| # | Change | Affected table.column | Severity | Effort | Migration Risk | Source finding IDs |
|---|---|---|---|---|---|---|
| 1 | Read-only unified audit/activity view over the 9+ log tables (taxonomy frozen) | `audit_trail`, `audit_logs`, `*_activity_log` set | 🟠 High | Small | Low | D2-B1, D2-F7 |
| 2 | SEAI/EPA Irish factor data load into the generalised factor table | `defra_conversion_factors.factor_set`/`.country` | 🔴 Critical | Medium | Medium | D2-E1, D3-C10 |
| 3 | Address verification loop columns | `facilities.address_validation_status`, `.formatted_address` (+ peers) | 🟡 Medium | Small | Low | D1-D4, D2-F1, D2-F2 |
| 4 | External-integration identity for Xero/QuickBooks + ledger code | `external_id`, `integration_source`, `last_synced_at` passim; `suppliers.account_reference` | 🟠 High | Small | Low | D3-E1, D1-§C |
| 5 | Platform `invoices` table with sequential numbers and stored UK/IE VAT evidence | *(new table)*; `customer_subscriptions.vat_rate`, `.vat_amount`, `.tax_id` | 🟠 High | Medium | Low | D3-E2, D1-§C |
| 6 | Per-user 2FA columns behind existing global settings | `users.totp_secret`, `.two_factor_enabled`, `.backup_codes` | 🟠 High | Medium | Low | D3-B4 |
| 7 | Per-user notification preferences (channel opt-in/out) | `notification_preferences` (or jsonb on `users`) | 🟡 Medium | Small | Low | D2-F5 |
| 8 | Read-state canonicalisation: derive counters and arrays from one source | `conversation_participants.last_read_at` canonical; `messages.read_by`, `conversations.unread_count` | 🟠 High | Medium | Medium | D2-F8, D3-A7 |
| 9 | Identity dedup: 1:1 FK uniqueness; identity fields only in `users` | `staff_profiles.email`, `.first_name`, `.is_active` | 🟡 Medium | Medium | Medium | D2-B6, D3-D3 |
| 10 | Deprecate one duplicate review-history table | `review_audit_trail` vs `review_assignment_history` | 🟡 Medium | Medium | Medium | D2-B3 |
| 11 | County lookup (26 ROI + 6 NI + UK ceremonial, disambiguated by `country`) | `*.county` | 🟡 Medium | Small | Low | D1-B7 |
| 12 | UK nation field (England/Scotland/Wales/NI); document `facilities.region` semantics | `facilities.region` | 🟡 Medium | Small | Low | D1-A10 |
| 13 | Bank-holiday jurisdiction on the business calendar | `business_hours.*` | 🟡 Medium | Medium | Low | D1-A14 |
| 14 | Square-metre floor-area columns (sqft dormant) | `organization_metadata.total_floor_area_sqm`, `.occupied_floor_area_sqm` | 🟡 Medium | Small | Low | D2-D3, D1-§C |
| 15 | GIN indexes on key-filtered jsonb only (observe query logs first) | `customer_documents.extracted_data`, `manual_extraction_items.extracted_data` | 🟡 Medium | Small | Low | D3-A4, D2-C3 |
| 16 | Monthly RANGE partitioning of append-only log tables | `audit_trail`, `*_activity_log`, `processing_logs`, `login_history`, `email_logs` | 🔴 Critical | Large | Low–Medium | D3-A5 |
| 17 | Standardise `ip_address` on `inet` | `ip_address` across ~10 log tables | 🟢 Low | Small | Low | D3-B8 |
| 18 | Financial-year reporting semantics + `regulatory_framework` | `report_generation_queue.reporting_year`, `organizations.financial_year_end` | 🟠 High | Medium | Low | D1-A11 |
| 19 | Audit tamper-evidence: revoke UPDATE/DELETE, drop `updated_at` from append-only rows, hash-chain | `audit_trail`, `activity_logs.updated_at`, `review_audit_trail.updated_at` | 🟠 High | Medium | Low–Medium | D3-B7 |
| 20 | Erasure self-serve + PII inventory enforcement jobs | `users.*`, `ip_address`/`user_agent` passim | 🟠 High | Medium | Low | D3-D2, D3-D3 |
| 21 | Queue data-flow contract + cross-FKs (a document cannot sit in two queues) | `customer_documents.manual_review_queue_id`, `.processing_queue_id` | 🟠 High | Small | Low | D2-B2, D3-C8 |

### 12.3 v2.0+ / Future

**Everything in this subsection is a Future (v2.0+) recommendation. No action is proposed for v1.0 or v1.1.** The sole exception is the Ireland CSRD watch item in row 6.

| # | Change | Affected table.column | Severity | Effort | Migration Risk | Source finding IDs |
|---|---|---|---|---|---|---|
| 1 | **Future (v2.0+).** Queue rationalisation — merge the three processing queues only if ADRs are revisited | `processing_queue`, `manual_review_queue`, `document_processing_queue` | 🟠 High | Large | High | D2-B2, D3-C8 |
| 2 | **Future (v2.0+).** `contacts` table replacing triplicated inline contact columns | `suppliers.contact_*`, `organization_metadata.primary_contact_*`, `consultant_clients.client_contact_*` | 🟡 Medium | Medium | Medium | D1-§C, D3-E1 |
| 3 | **Future (v2.0+).** Supplier-portal identity model | `suppliers.portal_user_id`, `users.user_type` | 🟡 Medium | Medium | Medium | D3-E4 |
| 4 | **Future (v2.0+).** `api_keys` (scopes, expiry, revocation) and `webhook_events` tables | *(new tables)*; `system_settings.api_rate_limit`, `webhook_retry_*` | 🟡 Medium | Medium | Low | D3-E3 |
| 5 | **Future (v2.0+).** Entra ID SSO columns | `users.sso_provider`, `users.sso_subject` | 🟢 Low | Small | Low | D3-E5 |
| 6 | **Future (v2.0+).** EU-expansion activation of dormant ESRS/CSRD + NACE fields. **v1.1 watch item:** Ireland has transposed CSRD; `esrs_enabled`/`nace_code` may activate early for large Irish customers | `organizations.esrs_enabled`, `organizations.nace_code`, `activity_categories.esrs_e1_category` | 🟡 Medium | Medium | Low | D1-B10, D1-§F |
| 7 | **Future (v2.0+).** `support_tickets` table once volume justifies it | *(new table)*; `user_feedback` interim | 🟢 Low | Medium | Medium | D1-§C |

### 12.4 Effort Summary

| Version | Items | Small | Medium | Large | 🔴 Critical |
|---|---|---|---|---|---|
| v1.0 launch blockers | 26 | 15 | 9 | 2 | 10 |
| v1.1 hardening | 21 | 10 | 10 | 1 | 2 |
| Future (v2.0+) | 7 | 1 | 5 | 1 | 0 |

Sequencing is unusually favourable. Fifteen of the 26 v1.0 items are Small-effort CHECK constraints and indexes — additive, Low-risk, independently deployable — and should land in one focused hardening sprint, led by the `country` and `currency` CHECKs (items 2–3) and closed by the fixture work (item 18) proving the Irish write path. The heavier items — RLS verification (11) and retention/erasure (16–17) — run in parallel; only the factor and emissions backfills (5–6) may phase into early v1.1.

## 13. Changes NOT Recommended (because they conflict with ADRs)

Each change below was considered and rejected: the temptation is genuine, but each conflicts with an approved ADR (numbers not supplied, so none cited). The right-hand column gives the recommended mitigation — the mitigation, not the change, is what appears in Section 12.

| Change considered | Why tempting | Why NOT RECOMMENDED | Recommended mitigation instead |
|---|---|---|---|
| Merge the three processing queues | ~70% overlap; `customer_documents` holds FKs to two queues | Conflicts with approved ADR — the multi-phase pipeline is an approved architectural decision; a merge is a redesign | Data-flow contract + cross-FKs (12.2 item 21); revisit as Future (v2.0+) only if ADRs reopen |
| Consolidate the 9+ audit/activity log tables | Near-identical shapes; fragmented document timelines | Conflicts with approved ADR — the per-domain log design is deliberate | Freeze the taxonomy; read-only unified view (12.2 item 1) |
| Merge `users`/`staff_profiles`/`consultant_profiles` identity | Three tables, duplicated email/name/is_active | Conflicts with approved ADR — profile-per-role is the approved model | 1:1 FK uniqueness; identity fields only in `users` (12.2 item 9) |
| Replace `uuid[]` arrays (`client_access`, `read_by`) with junction tables | Arrays cannot be FK-enforced and are index-hostile | Conflicts with approved ADR — existing table structure is fixed | GIN indexes, app/trigger membership hygiene, `conversation_participants.last_read_at` canonical (12.2 item 8) |
| Replace jsonb `metadata`/`extracted_data` with typed columns | Typed columns are constrainable and indexable | Conflicts with approved ADR — the jsonb pattern is approved | GIN on key-filtered columns; promote genuinely hot keys (`document_number`) selectively (12.1 item 8, 12.2 item 15) |
| Replace UUID PKs with bigint | Smaller indexes and joins | Conflicts with approved ADR — UUID keys are fixed; the churn buys nothing at v1.0 scale | None needed; index discipline (12.1 item 10) delivers the performance |
| Convert free-text statuses to PG enums | Enums are self-documenting and compact | Conflicts with approved ADR — PG enums are migration-hostile under the migration-friendly stance | CHECK constraints with value lists (12.1 item 21) |
| Full pre-launch partitioning redesign of append-only tables | Pre-launch is the only cheap window | Conflicts with approved ADR — a storage redesign of this size is out of v1.0 scope | Retention schedule + pg_cron now (12.1 item 16); monthly partitions on still-small tables in v1.1 (12.2 item 16) |
| Delete dormant EU/US fields (`organizations.cik`, `naics_code`, `isin`, `sedol`, `esrs_*`, `issb_*`) | Scope hygiene | Conflicts with approved ADR — the additive-only posture retains columns; re-adding dropped compliance columns later is far worse than carrying inert ones | Keep dormant, marked out-of-scope; **Ireland nuance:** `organizations.nace_code` and `organizations.esrs_enabled` are v1.1 watch-item activation candidates — Ireland's CRO uses NACE Rev.2 and has transposed CSRD (12.3 item 6) |

## 14. Final Production Readiness Verdict

**Verdict: NOT production-ready today — conditionally ready after one focused hardening sprint.**

The foundation is sound. Domain coverage across the ~90 tables is broad: the reporting spine (`report_templates`, `report_generation_queue`, `report_versions`) models versioning and approval properly; the notification estate carries read/dismiss state, priority and deep links; the consultant channel (`consultant_profiles.brand_name` through `co_branding_enabled`) is white-label-ready; and `system_settings.default_emission_factor_set` proves multi-jurisdiction factors were intended. This schema needs hardening, not rescue.

It cannot launch as-is, and the reasons concentrate on the Irish half of the launch. `facilities` mandates a `postcode` that does not exist in Ireland while lacking the `eircode` its three sibling address tables carry — an Irish customer cannot register the site whose emissions the product measures. Jurisdiction validation is a vacuum: `country` and `currency` are free text, so every VAT, company-number and timezone rule keys off values like "UK" and "gbp". The factor model is UK-only: `defra_conversion_factors` carries no unit, scope or source, so a Dublin site silently receives a UK grid factor and a wrong Scope 2 number. Beneath these sit the engineering gaps: no visible indexes, an unverifiable RLS matrix with nullable `organization_id` on roughly fifteen tables, unverified FK/ON DELETE behaviour, plaintext secrets in `consultant_profiles.api_key` and the token tables, and no GDPR retention or erasure capability despite `users` being pinned by around forty foreign keys.

What makes this verdict conditional rather than negative is the shape of the fix set. Of the 26 v1.0 items in Section 12.1, fifteen are Small-effort and nearly all are Low-risk additive changes — columns, CHECK constraints, indexes and procedures. No table needs redesigning, no ADR needs reopening, nothing in Section 13 need be sacrificed. The remediation is a hardening sprint, not an architecture programme.

One evidence caveat must accompany any go/no-go decision. The dump showed primary keys, a handful of UNIQUE constraints and nullability only — no secondary indexes, foreign keys or RLS policies. If unsupplied migrations exist, they must be inspected before final scoring: Performance and Security ratings rise materially if the index layer and policy matrix already exist. The structural findings — missing columns on `facilities` and `emissions_logs`, unit-less factors, plaintext secrets, absent retention and erasure — stand regardless.

On re-score: if the Section 12.1 register lands in full, overall readiness rises from 32 into the 70s — the largest movements from the Ireland blocker and jurisdiction CHECKs, the index baseline (Performance), and the secrets/RLS/retention cluster (Security and Governance). The v1.1 register then carries the schema into the 80s, led by the SEAI/EPA factor load and audit tamper-evidence.

The go/no-go gate is therefore concrete: the Section 12.1 register completed and verified, migrations re-inspected for indexes, RLS and FKs, and an Irish end-to-end fixture — IE organisation, IE facility with Eircode, EUR currency, SEAI-sourced factor — passing from onboarding to a generated report. When that fixture runs green, CarbonTally is production-ready for the UK and Ireland.
