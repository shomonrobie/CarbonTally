## 10. UX Improvements

CarbonTally's schema is unusually generous to the user experience in places; the notification, messaging and reporting estates show real product thinking. The improvements below are all additive and ADR-safe: three areas where small schema changes disproportionately lift perceived quality, and one structural inconsistency — read state and activity timelines — that will silently erode trust if left to drift.

### 10.1 What the Schema Already Does Well

| Strength | Evidence (table.column) | Assessment |
|---|---|---|
| Notification estate | `notifications` (read/dismiss, priority, link), `notification_templates`, delivery tracking | Genuinely good; one duplicate delivery table to resolve (finding B5) (🟢) |
| Real-time presence | `user_presence`, `typing_status` | Present, but DB-backed upserts per keystroke are Supabase-naïve; use Realtime Presence or add UNIQUE constraints (dim03 item A8) (🟠, v1.1) |
| Activity feed | `activity_feed` per org/user, `event_data` jsonb | Correct home for "recent activity"; fragmented by 9+ log tables (finding F7) (🟡) |
| Reporting spine | `report_templates`, `report_generation_queue`, `report_versions.is_current`, `report_comments`, `export_history` | Solid versioning/approval model (finding D7) (🟢) |
| Consultant branding | `consultant_profiles.brand_name`/`logo_url`/`primary_color`/`email_from`/`co_branding_enabled`/`client_portal_url` | White-label-ready for v1.1 (dim03 item E4) (🟢) |

The most valuable finding here is a negative one: CarbonTally needs UX infrastructure protected, not built. The `notifications` table already carries read/dismiss state, priority and deep links, and `report_versions.is_current` gives the UI an unambiguous "latest report" answer. Two gaps temper this. There is no per-user `notification_preferences` for channel opt-in/out — a v1.1 addition (finding F5). And `typing_status`/`user_presence` write to Postgres on every keystroke and heartbeat without uniqueness constraints, permitting duplicate presence rows and a wasted write load that Supabase Realtime would absorb natively (dim03 item A8). Both are cheap pre-launch fixes.

### 10.2 Address & Lookup UX

| # | Finding | Evidence | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| 10.2.1 | Irish facilities unenterable: `facilities.postcode` NOT NULL, no `eircode` — yet `organizations`, `suppliers`, `consultant_profiles` all have both | `facilities` | 🔴 | Small | Medium | v1.0 blocker |
| 10.2.2 | No `address_validation_status` or `formatted_address` anywhere — lookup results cannot be cached verbatim or marked verified against Royal Mail PAF / Loqate / Eircode Finder | passim (finding F1; dim01 D4) | 🟡 | Small | Low | v1.1 |
| 10.2.3 | No format CHECK on any `postcode`/`eircode`; no `validated_at`/`lookup_source`. Unnormalised values break lookup matching and trigram search | passim (finding F2) | 🟡 | Small | Low | v1.1 |
| 10.2.4 | All phones bare `varchar` (`suppliers.contact_phone`, `organization_metadata.primary_contact_phone`, `consultant_profiles.phone`) — no E.164 constraint; +44/+353 display derived at render time | passim (finding F3) | 🟡 | Small | Low | v1.1 |
| 10.2.5 | Dual address truths: free-text `suppliers.address`, `organizations.registered_address`/`billing_address` duplicate the structured columns with no sync rule | `suppliers.address` (dim01 D2) | 🟠 | Small | Low | v1.0 |

The structured address model maps cleanly onto Royal Mail PAF, Loqate and Eircode Finder payloads, and `facilities.latitude`/`longitude` already support geocoding. What is missing is the verification loop: without `address_validation_status` (unverified/verified/failed) and a cached `formatted_address`, the UI cannot show whether the address on an emissions-bearing facility has ever been confirmed — a judgement consultant-channel clients will make. The dual-storage issue (10.2.5) is the trust risk: two writers, no canonical source, guaranteed divergence. The structured columns should be declared canonical and the text blobs demoted to display caches — a data-entry convention, not a redesign.

### 10.3 Search, Filters & Duplicate Detection

| # | Finding | Evidence | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| 10.3.1 | No trigram/full-text indexing: `organizations.name`, `suppliers.name`/`vat_number`/`company_number`, `facilities.name`, `customer_documents.file_name`, `users.email` all unindexed | entire schema (finding C1) | 🔴 | Small–Medium | Low | v1.0 |
| 10.3.2 | "Did you mean…?" duplicate prompts unsupported: no `pg_trgm` similarity and no unique constraints on `suppliers(organization_id, name/vat_number/company_number)` | findings F4, A4 | 🟠 | Small | Medium | v1.0 |
| 10.3.3 | Free-text `status` in ~25 tables (`customer_documents.status`, `conversations.status`, `activity_feed.event_type`) kills filter facets — typos and case drift become silent states | passim (findings C2, F6) | 🟠 | Medium | Medium | v1.0 new writes, v1.1 enforcement |
| 10.3.4 | No content hash: `organization_files`, `customer_documents`, `file_attachments` lack `file_checksum` — the UI cannot warn "this invoice was already uploaded" | file tables (finding A5) | 🟠 | Small per table | Low | v1.0 column, v1.1 unique |
| 10.3.5 | Extracted invoice data (number, supplier, kWh) lives only in `customer_documents.extracted_data` jsonb — unsearchable without full scans | `customer_documents.extracted_data` (finding C3) | 🟠 | Medium | Medium | v1.1 |

Search is where the zero-index reality becomes a UX defect rather than a performance statistic. Every customer-facing list will seq-scan, and none of the fuzzy-match primitives exist for the duplicate-prevention prompts the AI pipeline makes essential: `ai_mapped_supplier_id` amplifies duplicate suppliers into emissions data, so `pg_trgm` similarity on `suppliers.name` plus `vat_number` at creation time is both a search feature and an integrity control (finding F4). A SHA-256 `file_checksum` on every file-bearing table likewise enables a deterministic duplicate-upload warning far more trustworthy than filename matching. Free-text status should be constrained with CHECK-in value lists, not Postgres enums, per the ADR's migration-friendly stance.

### 10.4 Consistency Trust Killers

| # | Finding | Evidence | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| 10.4.1 | Four competing read-state mechanisms: `messages.read_by uuid[]`, `messages.read_count`/`last_read_at`, `conversations.read_by`/`unread_count`, `conversation_participants.last_read_at` | messaging tables (finding F8) | 🟠 | Medium | Medium | v1.1 |
| 10.4.2 | Denormalised counters unguarded: `conversations.unread_count`/`participant_count`, `upload_batches.processed_files`, `customer_subscriptions.ai_extraction_used` | passim (finding A11) | 🟡 | Medium | Low | v1.1 |
| 10.4.3 | Activity fragmented across 9+ near-identical log tables (`activity_logs`, `audit_logs`, `document_activity_log`, `verification_activity_log`…) — no single document timeline | log tables (findings B1, F7, C6) | 🟠 | Small (view) | Low | v1.1 view; consolidation v2.0/never per ADR |
| 10.4.4 | Duplicate notification delivery tables with identical column sets | `notification_delivery` vs `notification_delivery_log` (finding B5) | 🟠 | Small | Low | v1.0 |

Phantom unread badges are the classic trust-eroding bug, and four writable representations of "read" guarantee them: any code path updating three and missing the fourth leaves a badge that will not clear. The fix is declarative — anoint `conversation_participants.last_read_at` as canonical and derive `unread_count`, `read_count` and the `read_by` arrays from it (finding F8). The same discipline applies to activity: consolidating the 9+ log tables is not recommended (ADR conflict), but a read-only unified view gives support staff, auditors and the in-app timeline one queryable story per document (finding B1). Freeze the taxonomy, document the authoritative log per domain, and ship the view in v1.1.

## 11. Future Expansion Readiness

This section assesses how far the schema carries CarbonTally towards its stated UK/IE growth paths — accounting integrations, billing maturity, API and Microsoft ecosystems, and the white-label channel — plus, strictly labelled Future (v2.0+), what is retained for EU expansion. The recurring theme: cheap additive columns now eliminate expensive backfills later.

### 11.1 UK/IE Accounting Integrations: Xero & QuickBooks

| # | Finding | Evidence | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| 11.1.1 | Zero external-integration identity columns: no `external_id`, `integration_source`, `last_synced_at` on `organizations`, `suppliers`, `customer_documents`, `emissions_logs`, `facilities` | passim (dim03 item E1) | 🟠 | Small | Low | v1.1 (columns); v2.0 (sync engine) |
| 11.1.2 | `suppliers` has no `account_reference` (ledger code) — the primary join key Xero/QuickBooks contacts sync on | `suppliers` (dim01 §C) | 🟠 | Small | Low | v1.1 |
| 11.1.3 | Contact data embedded three ways (`suppliers.contact_*`, `organization_metadata.primary_contact_*`, `consultant_clients.client_contact_*`) — no contacts table for sync mapping | passim (finding C5) | 🟠 | Medium | Medium | v1.1 planning; v2.0 |

Xero and QuickBooks Online dominate UK/IE SME accounting, and both sync through stable external identifiers plus cursors — precisely what is missing. Adding these columns in v1.1, a full release before any sync engine, is an economic argument: a nullable column on an empty table costs minutes, whereas retrofitting identity onto live `suppliers` and `customer_documents` rows means fuzzy matching against accounting exports, with real error rates and consultant-channel reputational risk. `suppliers.account_reference` is the same trade — one varchar now, or a manual mapping exercise per client later. The triplicated contact model (11.1.3) is plan-only in v1.x, since a contacts table touches ADR-governed structure.

### 11.2 Billing & Invoicing Evolution

| # | Finding | Evidence | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| 11.2.1 | Stripe readiness partial: `customer_subscriptions` has Stripe IDs and `currency` but no `vat_rate`/`vat_amount`/`tax_id`/`invoice_number` — UK (20%) and IE (23%) VAT evidence not captured | `customer_subscriptions` (dim03 item E2) | 🟠 | Small | Low | v1.1 |
| 11.2.2 | `consultant_billing` has prices (`auto_extraction_price`, `manual_extraction_price`) but **no `currency` column at all** — the only billing table missing one | `consultant_billing` (dim01 §C) | 🟠 | Small | Low | v1.0 |
| 11.2.3 | No local `invoices` table — Stripe IDs exist but no sequential invoice numbers or stored VAT invoice records, which UK/IE B2B invoicing expects | *(table missing)* (dim01 §C) | 🟠 | Medium | Low | v1.1 |

Stripe Tax can compute UK (20%) and Irish (23%) VAT, making the integration itself low-risk; the gap is evidentiary. A UK finance team expects a sequential invoice number and a stored VAT invoice, and nothing in the schema can produce one — `customer_subscriptions` holds payment state, not invoice evidence. The `consultant_billing.currency` omission is the sharper defect because it is live at v1.0: the white-label channel prices extraction work in a column with no denomination, in a two-currency (GBP/EUR) market. Close it before launch, alongside the ISO 4217 CHECK constraints recommended for the schema's six free-text currency columns. The local `invoices` table stays v1.1 — additive, and best designed once Stripe Tax behaviour is observed in production.

### 11.3 API & Microsoft/SSO

| # | Finding | Evidence | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| 11.3.1 | API layer half-built: `system_settings.api_rate_limit(_burst)` and `webhook_retry_count/_delay/_timeout` exist, but no `api_keys` table (scopes, expiry, revocation) and no `webhook_events`/delivery-log table | `system_settings`, `consultant_profiles.webhook_url` (dim03 item E3) | 🟡 | Medium | Low | v2.0 |
| 11.3.2 | `consultant_profiles.api_key` stored as **plaintext varchar** — a single unscoped, irrevocable key per consultant; any DB read yields live credentials | `consultant_profiles.api_key` (dim03 item B2) | 🔴 | Small | Low | v1.0 (hash first) |
| 11.3.3 | No `sso_provider`/`sso_subject` on `users` — Entra ID SSO (common in UK enterprise procurement) will need them | `users` (dim03 item E5) | 🟢 | Small | Low | v2.0 |

The settings layer advertises an API product — rate limits, webhook retry policy — that the data layer cannot yet honour: no per-key scoping, expiry or revocation, and no webhook delivery log. Sequencing matters. The v2.0 `api_keys` and `webhook_events` tables are additive and low-risk whenever they land; what cannot wait is 11.3.2. A plaintext `api_key` must be hashed (SHA-256 with a lookup prefix, plus `api_key_created_at`/`last_used_at` for rotation) in v1.0 — before any consultant holds a key that would later need force-rotation under incident conditions. Entra ID SSO is correctly deferred: `sso_provider`/`sso_subject` are trivial to add when the first UK enterprise procurement demands them, and premature now.

### 11.4 White-Label & Supplier Portal

| # | Finding | Evidence | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|---|
| 11.4.1 | Branding columns solid for v1.1 white-label: `brand_name`, `logo_url`, `primary_color`, `secondary_color`, `footer_text`, `email_from`, `co_branding_enabled`, `client_portal_url`, plus `report_templates` branding | `consultant_profiles` (dim03 item E4) | 🟢 | — | — | v1.1 (no schema action) |
| 11.4.2 | Supplier portal has no identity model: `suppliers` has no `portal_user_id`/auth linkage and `users.user_type` has no supplier value | `suppliers`, `users.user_type` (dim03 item E4) | 🟡 | Small (planning) | Low | v2.0 (plan only now) |

The white-label channel is the strongest expansion story in the schema: `consultant_profiles` already carries everything a branded client portal needs, from send-from identity to co-branding control, and `report_templates` extends branding into the deliverable itself. No schema work is needed for v1.1 beyond section 10's validation conventions. The supplier portal is different and should stay a plan: suppliers are pure data rows with no auth linkage, and bolting an identity model on later is precisely the structural change the ADRs guard against. The v1.x actions are deliberate non-actions — document the intended identity model, keep `suppliers` free of half-built portal columns, and revisit at v2.0 alongside the contacts question (11.1.3).

### 11.5 EU Expansion — Future (v2.0+) ONLY

*Everything in this subsection is a **Future (v2.0+)** recommendation. No action is proposed for v1.0 or v1.1, and no EU-wide capability should be built now. The only exception is a v1.1 **watch item** for Ireland, because Ireland has transposed CSRD.*

| Field (table) | Verdict | Rationale |
|---|---|---|
| `organizations.cik` | Future (v2.0+) / arguably never | US SEC identifier; zero UK/IE relevance (dim01 §F) |
| `organizations.naics_code`, `organization_metadata.naics_code` | Future (v2.0+) | US/Canadian classification; UK uses SIC 2007, IE uses NACE |
| `organizations.isin`, `organizations.sedol` | Future (v2.0+) | Listed-entity identifiers; outside v1.0 SME scope |
| `organizations.issb_enabled`, `activity_categories.issb_category`, `product_categories.issb_category` | Future (v2.0+) | IFRS S1/S2 voluntary; UK SRS still pending |
| `organizations.esrs_enabled`, `activity_categories.esrs_e1_category`, `product_categories.esrs_e1_category` | Retain dormant — v1.1 watch item, Future (v2.0+) build | Ireland has transposed CSRD; large Irish customers are in ESRS scope now |
| `organizations.nace_code` | Retain dormant — v1.1 watch item, Future (v2.0+) build | Irish CRO activity codes are NACE Rev.2; may activate for IE earlier than other EU fields |
| `organizations.lei`, `organizations.carbon_tax_region` | Retain dormant | Cheap to keep; Ireland levies carbon tax, UK uses UK ETS |

The recommendation is disciplined inaction: retain every dormant column, build none of them. Deleting would be cheap now and regrettable later — `nace_code` and the `esrs_*` columns sit directly on the plausible v2.0 path, and re-adding dropped columns to a live compliance schema is far worse than carrying inert ones. The Irish nuance warrants explicit visibility rather than a build commitment: because Ireland has transposed CSRD, large Irish entities are in ESRS scope today, so if enterprise Irish customers sign during v1.1, `esrs_enabled` and `nace_code` become activation candidates ahead of the general Future (v2.0+) timeline. Until that commercial signal exists, the correct posture is a documented watch item, reviewed at each release planning cycle — and nothing more.
