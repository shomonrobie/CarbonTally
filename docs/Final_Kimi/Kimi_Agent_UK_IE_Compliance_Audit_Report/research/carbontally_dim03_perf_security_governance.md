# DIM 03 — Performance, Security, Data Integrity, GDPR & Future-Compatibility Audit Brief (UK/IE scope)

**Scope:** UK & Ireland only. No SQL/migrations — review and recommendations only. ADRs assumed approved (Supabase RLS approach, jsonb metadata columns, UUID PKs, existing table structure — no redesign). Every issue carries Severity / Effort / Migration Risk / Should Implement.

Legend: 🔴 Critical · 🟠 High · 🟡 Medium · 🟢 Low

---

## A) PERFORMANCE FINDINGS

**A1. No secondary indexes anywhere — every FK column is unindexed** 🔴
The dump shows only PK and a handful of UNIQUE constraints. Every tenant and join column is unindexed: `organization_id` appears as the tenant key on ~30 tables (`assets`, `facilities`, `suppliers`, `product_categories`, `customer_documents`, `emissions_logs`, `document_processing_queue`, `processing_queue`, `customer_subscriptions`, `usage_tracking`, `report_generation_queue`, `ai_content_history`, `manual_extraction_batches`, `consultant_clients`, `activity_feed`, `activity_logs`, `audit_logs`, `upload_batches`, `export_history`, `customer_communication`, `manual_review_queue`, `organization_files`, `organization_metadata`, `report_templates`, `user_feedback`, `user_invitations`, `pending_invites`, `draft_entries`, `processing_logs`, `customer_review_log`, `customer_verifications`, `conversations`, `messages`, `file_attachments`). Non-org FKs equally bare: `customer_documents.supplier_id/asset_id/document_type_id/manual_review_queue_id/processing_queue_id`, `emissions_logs.asset_id/defra_factor_id/file_id/customer_document_id/supplier_id`, `messages.conversation_id/sender_id/parent_message_id`, `processing_assignments.queue_id/assigned_to`, `processing_steps.assignment_id`, `qc_checks.assignment_id`, `qc_errors.qc_check_id`, `report_versions.report_id`, `report_comments.report_id`, `consultant_firm_members.firm_id/user_id`, `consultant_billing.consultant_id/client_id`, `password_reset_tokens.token`, `user_invitations.token`, `staff_workload.staff_id`, `login_history.staff_id`, `notifications.recipient_id`. On Supabase, every PostgREST list endpoint will seq-scan. Effort: Medium · Risk: Low · **v1.0**.

**A2. Missing composite indexes for dominant query patterns** 🔴
Required composites (no redesign, additive only):
- `(organization_id, status)` / `(organization_id, created_at DESC)` on `customer_documents`, `document_processing_queue`, `emissions_logs`, `upload_batches`, `report_generation_queue`, `customer_verifications`.
- Queue workers: `processing_queue(queue_status, priority_score DESC, sla_deadline)`, `manual_review_queue(status, priority, sla_deadline)`, `document_processing_queue(status, created_at)` — plus `FOR UPDATE SKIP LOCKED`-friendly ordering for claim patterns.
- `messages(conversation_id, created_at)`, `conversation_participants(conversation_id, user_id)`, `notifications(recipient_type, recipient_id, is_read, created_at DESC)`, `activity_feed(organization_id, created_at DESC)`, `usage_tracking(organization_id, usage_month)`, `sla_compliance(queue_id)`, `staff_daily_performance(staff_id, date)`.
Effort: Medium · Risk: Low · **v1.0**.

**A3. Missing partial indexes for hot predicates** 🟠
`is_active = true` partials on `suppliers`, `facilities`, `assets`, `organization_members`, `document_types`, `consultant_firm_members`, `staff_profiles`; `deleted_at IS NULL` partial on `organization_files`; `is_deleted = false AND is_archived = false` on `messages`; `is_read = false` on `notifications`/`activity_feed`; `status IN ('pending','processing')` partials on all three queue tables (completed rows will dominate volume within months). Effort: Small · Risk: Low · **v1.0**.

**A4. No GIN indexes on heavily-queried JSONB** 🟡
`customer_documents.extracted_data`/`mapped_data`, `manual_extraction_items.extracted_data`, `document_processing_queue.ai_extraction_result`, `activity_logs.metadata/details`, `audit_logs.old_data/new_data`, `audit_trail.old_data/new_data`, `report_generation_queue.generated_content`, `dashboard_metrics.metric_value` (also missing `organization_id` entirely — see D). Recommend GIN only on columns actually filtered by key; per ADR the jsonb metadata pattern stays, so index rather than restructure. Effort: Small · Risk: Low · **v1.1** (add per observed query load; avoid blanket GIN — write amplification on hot tables).

**A5. High-volume append-only tables have no partitioning/retention strategy** 🔴
Growth-ranked: `audit_trail`, `audit_logs`, `activity_logs`, `staff_activity_log`, `login_history`, `processing_logs`, `document_activity_log`, `message_activity_log`, `conversation_activity_log`, `verification_activity_log`, `notification_delivery_log`, `email_logs`, `processing_time_log`, `messages`, `emissions_logs`, `ai_content_history`, `typing_status`, `user_presence`. None have indexes, archive tables, or partition keys; `system_settings.audit_log_retention_days`/`data_retention_days` exist but nothing enforces them. Recommend: monthly RANGE partitioning on `created_at` (or at minimum a documented pg_cron retention/archive job) for `audit_trail`, `*_activity_log`, `processing_logs`, `login_history`, `email_logs`, `notification_delivery*` before volume accumulates — retrofitting partitioning onto a large live table is the High-risk version of this change. Effort: Large · Risk: Medium (Low if done pre-launch on empty tables) · **v1.0** for retention jobs, **v1.1** for partitioning.

**A6. int4 vs int8 file-size inconsistency — 2 GB overflow** 🟠
`file_attachments.file_size int4` overflows at 2 GB (and at 2,147,483,647 *bytes*, not the MB-scale `system_settings.max_upload_size_mb` governs), while `organization_files.size_bytes`, `processing_queue.file_size_bytes`, `document_processing_queue.file_size_bytes`, `report_generation_queue.final_report_size_bytes`, `usage_tracking.total_storage_bytes` are int8. Standardize on int8. Also `processing_logs.duration_ms`, `ai_processing_time_ms`, `processing_time_seconds`, `staff_daily_performance.total_processing_time_seconds` are int4 — int4 caps at ~24.8 days in ms and ~68 years in seconds; ms columns are safe but note AI batch jobs can exceed expectations. Effort: Small · Risk: Low (pre-launch) · **v1.0**.

**A7. Counter/denormalized columns will cause write contention and drift** 🟡
`conversations.unread_count`, `conversations.participant_count`, `messages.read_count`, `organization_files.access_count`, `staff_workload.assigned_tasks/in_progress_tasks/...` (daily mutable rollup), `usage_tracking.*_used` counters and `customer_subscriptions.ai_extraction_used/manual_extraction_pages_used` — hot-row updates per event; recommend transactional update discipline or moving counters to the rollup pattern already present (`staff_daily_performance`). Effort: Medium · Risk: Medium · **v1.1**.

**A8. Realtime-churn tables in the relational store** 🟠 (Supabase-specific)
`typing_status` (upsert per keystroke) and `user_presence` (upsert per heartbeat) have no PK-based uniqueness on `(user_id, conversation_id)`/`user_id`, so duplicate rows are possible *and* every keystroke is a DB write. Supabase-native answer: Realtime Presence/Broadcast, not table writes. If kept in DB: add UNIQUE constraints + short retention. Effort: Medium · Risk: Medium · **v1.1**.

**A9. Missing UNIQUE constraints that are also search paths** 🟠
No unique `(organization_id, user_id)` on `organization_members`; `(conversation_id, user_id)` on `conversation_participants`; `(organization_id, usage_month)` on `usage_tracking`; `(reporting_year, activity_type)` on `defra_conversion_factors` (duplicate DEFRA factors would silently double-count emissions); `(report_id, version_number)` on `report_versions`. Each is both an integrity bug and a missing index. Effort: Small · Risk: Low–Medium (dedupe first) · **v1.0**.

**A10. Search readiness is nil** 🟡
No trigram (`pg_trgm`) indexes for name search on `organizations.name`, `suppliers.name`, `facilities.name`, `consultant_clients.client_name`; no full-text strategy for `messages.content`, `customer_documents.file_name`, `glossary`. Brief's "fast search / autocomplete" UX goals are unmet. Effort: Small–Medium · Risk: Low · **v1.1**.

---

## B) SECURITY / RLS FINDINGS

**B1. No RLS policies evident in the dump — must verify the full policy matrix** 🔴
The brief asserts RLS exists, but the schema evidence shows zero policies and, critically, **several tenant tables carry no tenant key at all**: `email_logs` (no `organization_id`/`user_id`), `draft_entries` (org nullable), `dashboard_metrics` (no org), `typing_status`, `user_presence`, `beta_access_codes`, `beta_users`, `waitlist`, `glossary`, `units`, `defra_conversion_factors`, `roles`, `system_settings`, `queue_settings`, `sla_definitions`, `business_hours`, `team_performance`. Required policy matrix before launch:
- **Tenant isolation**: `organization_id = (select organization_id from organization_members where user_id = auth.uid() and is_active)` pattern on all ~30 org-keyed tables. Nullable `organization_id` on `activity_feed`, `activity_logs`, `audit_logs`, `conversations`, `messages`, `file_attachments`, `export_history`, `manual_review_queue`, `upload_batches`, `processing_logs`, `user_feedback`, `user_invitations`, `customer_review_log`, `customer_verifications`, `report_templates`, `draft_entries` is a direct isolation hole — a NULL org row matches no tenant policy and must be either backfilled/made NOT NULL or explicitly policy-handled.
- **Consultant isolation**: policies via `consultant_clients(consultant_id, organization_id)` mapping; `consultant_firm_members.client_access uuid[]` must be enforced with `organization_id = ANY(client_access)` (array containment is index-hostile — see C5).
- **Staff isolation**: `staff_profiles`, `processing_assignments`, `qc_checks` etc. are back-office; policies must check `staff_roles.permissions` — currently three competing permission representations exist (`staff_roles.permissions` jsonb, `consultant_firm_members.role`/`role_id`/`permissions` jsonb + four `can_*` bools, `roles.permissions` jsonb). RLS must pick one source of truth per surface or policies will disagree.
- **Service-role bypass**: all service-role access (queue workers, AI extraction) bypasses RLS by design — ensure no service key ever reaches the client and worker queries filter `organization_id` explicitly in code.
Effort: Large · Risk: Medium · **v1.0 blocker**.

**B2. `consultant_profiles.api_key` stored as plaintext varchar** 🔴
API keys must be stored hashed (e.g., SHA-256) with a prefix for lookup, plus `api_key_created_at`/`last_used_at`/rotation support. Plaintext means any DB read (backup, log, breach) yields live credentials, and RLS cannot protect it from service-role contexts. Effort: Small · Risk: Low · **v1.0**. Same class: `beta_access_codes.magic_token` and `password_reset_tokens.token`/`user_invitations.token` should be hashed, not stored raw 🟠.

**B3. `password_reset_tokens.user_id` UNIQUE = only one active reset token per user** 🟠
A second request silently fails or overwrites; combined with nullable `used`, an attacker requesting resets can DoS a legitimate user's in-flight token. Drop the unique on `user_id`, keep unique on `token`, enforce "latest valid token wins" in app logic. Effort: Small · Risk: Low · **v1.0**.

**B4. No per-user 2FA columns despite global config** 🟠
`system_settings.two_factor_required`/`two_factor_method` exist, but `users` has no `totp_secret` (encrypted), `two_factor_enabled`, `backup_codes`, `two_factor_confirmed_at`. Also no `failed_login_attempts`/`locked_until` on `users` despite `login_attempts_max`/`login_attempts_lockout_minutes` settings, and no `password_changed_at` for `password_expiry_days`. The security config is unenforceable as schema stands. (If Supabase Auth is the IdP, move these to `auth.mfa_*` and delete `users.password_hash` — see B5/B6.) Effort: Medium · Risk: Low · **v1.0** for lockout columns; **v1.1** for 2FA.

**B5. `users.password_hash` nullable + all seed users have `password_hash = null`** 🟠
Either (a) Supabase Auth owns credentials — then this column is a dangerous duplicate that will drift from `auth.users` and should be removed, or (b) custom auth — then it must be NOT NULL for credential users. Decide explicitly. Seed data shows 10 users with null hashes and `email_verified = true` — never ship that state to production. Note also seed users include `.de`, `.fr`, `.fi`, `.ai` emails despite UK/IE-only launch (test-data hygiene + GDPR data-minimisation point). Effort: Small · Risk: Low · **v1.0**.

**B6. Soft-delete inconsistency** 🟠
Only `organization_files.deleted_at` and `messages.is_deleted/deleted_at/is_archived` exist. `organizations` has no `is_active`/`deleted_at`/`archived_at` (cannot suspend a churned or archived tenant); `suppliers`, `facilities`, `assets`, `customer_documents`, `emissions_logs` rely only on nullable `is_active` with no `deleted_at`. For carbon accounting, hard-deleting `emissions_logs`/`customer_documents` destroys SECR/audit evidence — soft-delete + RLS filters must be the norm. Effort: Medium · Risk: Medium (retrofitting `deleted_at` changes every query) · **v1.0** for `organizations.is_active`/`deleted_at`; **v1.1** elsewhere.

**B7. Audit logging coverage is broad but not tamper-evident** 🟠
Six-plus overlapping audit stores (`audit_trail`, `audit_logs`, `activity_logs`, `staff_activity_log`, `processing_audit_trail`, `review_audit_trail`, plus per-domain `*_activity_log`) with no hash-chain/checksum column, no immutability enforcement (no trigger blocking UPDATE/DELETE), and `updated_at` present on several (`activity_logs.updated_at`, `review_audit_trail.updated_at`, `document_activity_log.updated_at`, `user_activity_log.updated_at`) — audit rows should never be updated. For a product whose value proposition is auditable carbon data (SECR), recommend: revoke UPDATE/DELETE on audit tables from all app roles, drop `updated_at` from append-only logs, and consider an append hash-chain on `audit_trail`. Effort: Medium · Risk: Low–Medium · **v1.1**.

**B8. `ip_address` type chaos** 🟡
`inet` in `audit_trail`, `staff_activity_log`, `login_history`; `varchar` in `activity_logs`, `document_activity_log`, `user_activity_log`; `text` in `audit_logs`, `conversation_activity_log`, `message_activity_log`, `verification_activity_log`. varchar/text accepts garbage, breaks subnet queries, and bloats storage. Standardize on `inet`. Effort: Small · Risk: Low · **v1.1**.

**B9. Supplier bank details in plaintext** 🔴
`suppliers.bank_account`, `iban`, `swift_code`, `bank_name` stored plain with no encryption column, no masking, no access audit. This is high-value payment-diversion fraud data (UK/IE invoice-fraud vector). Additionally **no UK `sort_code` field exists** — UK practice is sort code + account number; IBAN/BIC is the Irish norm. Recommend: add `sort_code`, encrypt at application layer or via `pgsodium`/vault, mask in API responses (last-4), and log reads. Effort: Medium · Risk: Medium · **v1.0** for sort_code + masking; **v1.1** for encryption-at-rest columns.

**B10. Polymorphic recipient on `notifications`** 🟡
`recipient_type`/`recipient_id` has no FK and makes RLS per recipient type fragile — a policy bug here leaks notifications cross-tenant. Constrain `recipient_type` via CHECK and write explicit per-type policies. Effort: Small · Risk: Low · **v1.0**.

---

## C) DATA INTEGRITY FINDINGS

**C1. No FK constraints visible in the dump at all** 🔴
Only `Primary`/`Unique`/`Nullable` are shown. If FKs genuinely don't exist: orphaned `emissions_logs.asset_id`, `messages.conversation_id`, `processing_steps.assignment_id`, etc. are guaranteed over time, and ON DELETE behavior (what happens when an `organization` is deleted — cascade, restrict, set null?) is undefined for a multi-tenant SaaS with financial-grade audit duties. Verify every relationship + explicit referential actions; for audit/financial tables prefer `ON DELETE RESTRICT`. Effort: Medium · Risk: Medium (orphan cleanup first) · **v1.0 blocker to verify**.

**C2. Nullable `created_at`/`updated_at` on essentially every table** 🟠
Should be `NOT NULL DEFAULT now()` (and `updated_at` maintained by trigger). Nullable timestamps break ordering, retention jobs (A5), and audit defensibility. Same for nullable booleans that should be `NOT NULL DEFAULT false/true`: `is_active`, `is_read`, `is_deleted`, `email_verified`, `sla_breached`, `qc_approved`, `customer_approved`, `two_factor`-adjacent flags — tri-state NULLs will produce silent filter bugs (`WHERE is_active` drops NULLs). Effort: Medium (many tables, mechanical) · Risk: Low–Medium (backfill NULLs first) · **v1.0** for booleans on auth/queue paths; **v1.1** sweep.

**C3. Free-text status/type/role/priority with no enum or CHECK** 🟠
`organizations.subscription_status`/`subscription_tier`, `organization_members.role`, `pending_invites.role`, `users.user_type`, `consultant_firm_members.role`, `customer_documents.status`/`processing_status`, `document_processing_queue.status`, `processing_queue.queue_status`, `manual_review_queue.status`, `upload_batches.status`, `report_generation_queue.status`, `conversations.status`/`priority`, `customer_subscriptions.status`/`plan`, `consultant_clients.status`/`billing_cycle`, `consultant_billing.billing_cycle`, `approval_requests.status`/`priority`, `notifications.priority`, `user_feedback.type`/`severity`/`status`, `beta_access_codes.status`, `waitlist.status`, `suppliers.compliance_status`/`supplier_type`, `staff_performance.period_type`, `sla_definitions.priority_level`. Typos become silent states that no query catches. Per ADR "no redesign," use CHECK constraints with value lists (not PG enums, to stay migration-friendly) — this is additive, not structural. Effort: Medium · Risk: Medium (existing bad values must be mapped) · **v1.0** for queue/billing/role columns; **v1.1** rest.

**C4. `uuid[]` array columns instead of junction tables** 🟠
`conversations.read_by`, `messages.read_by`, `consultant_firm_members.client_access`, plus `_text` arrays (`consultant_profiles.industries_served`/`expertise`/`certifications`, `consultant_clients.tags`, `document_types.file_extensions`, `glossary.related_terms`). Arrays can't be FK-enforced (dangling UUIDs after user/org deletion), can't carry per-row attributes (e.g., *when* read), and need GIN indexes to query efficiently. For `client_access` specifically this is a **security** structure (B1). Per ADR "existing table structure — no redesign": replacing with junction tables is **NOT RECOMMENDED because it conflicts with ADR**; instead: add GIN indexes on the uuid[] columns, enforce membership cleanup in app/trigger logic, and treat `messages.read_by` as capped-utility (move read-state to `conversation_participants.last_read_at`, which already exists). Effort: Small (GIN + hygiene) · Risk: Low · **v1.1**.

**C5. Money as unconstrained `numeric` (no precision/scale)** 🟠
`document_processing_queue.processing_cost`, `customer_subscriptions.price_per_ai_extra`/`price_per_manual_page`, `manual_extraction_batches.total_cost`/`price_per_page`, `consultant_billing.auto_extraction_price`/`manual_extraction_price`, `report_generation_queue.ai_cost`, `ai_content_history.cost`, `organizations.tax_rate`, `consultant_profiles.commission_rate`, `organization_metadata.annual_revenue`/`ebitda`. Unconstrained numeric accepts arbitrary scale; costs/prices should be `numeric(12,2)` (or minor-unit int8) with CHECK `>= 0`. Also `organizations.tax_rate`/`suppliers.tax_rate`/`system_settings.default_vat_rate` have no 0–100 range check. Effort: Small · Risk: Low · **v1.0** for billing tables.

**C6. Type inconsistencies across parallel columns** 🟡
- `customer_documents.confidence_score float8` vs `numeric` for `document_processing_queue.ai_confidence_score`, `ai_mapping_confidence`, `emissions_logs.confidence_score` — float8 introduces rounding artefacts in a compliance-relevant number; standardize numeric with 0–1 or 0–100 CHECK.
- `upload_batches.estimated_processing_time timestamptz` — semantically a duration (interval/int hours), not a timestamp; other queues use `estimated_completion_hours int4`. Align.
- `processing_logs` has `updated_at` but no `created_at`.
- Redundant duplicate columns with sync risk: `suppliers.contact_email` vs `primary_email`, `contact_phone` vs `primary_phone`, `address text` vs structured `address_line1…eircode`; `organizations.registered_address text` vs structured fields; `organization_metadata.sic_code/naics_code/reporting_standard/primary_contact_*` duplicate `organizations.*`. Pick one source of truth per datum or add trigger sync. Effort: Medium · Risk: Medium · **v1.1**.

**C7. Over-required / over-nullable FKs** 🟠
- `customer_documents.asset_id` is NOT NULL — many documents (supplier invoices, reports) have no asset; this forces fake assets. Make nullable. Also `customer_documents.organization_member_id` NOT NULL precludes consultant/staff/system uploads.
- `messages.sender_id`/`receiver_id`/`conversation_id` nullable — orphaned messages possible; `conversations.organization_id` nullable breaks tenancy (B1).
- `customer_verifications.organization_id` nullable on a compliance workflow table.
Effort: Small · Risk: Medium (backfill) · **v1.0**.

**C8. Three overlapping queue/review structures with cross-references** 🟡
`processing_queue`, `document_processing_queue`, `manual_review_queue`, plus `manual_extraction_batches/items` and `customer_documents.manual_review_queue_id` + `processing_queue_id`. Status can diverge across them with no CHECK/FK evidence tying lifecycles. Not a redesign case (ADR), but document the state machine and add cross-table status assertions in app/tests. Effort: Small (documentation + tests) · Risk: Low · **v1.1**.

**C9. `organizations.company_number` UNIQUE across two jurisdictions** 🟡
UK Companies House numbers (8 chars, alphanumeric prefixes e.g. SC/NI) and Irish CRO numbers (6 digits) live in one unique varchar column with no format CHECK and no `company_number_country`. Collision risk is low but validation/format ambiguity is real; also unique-nullable allows duplicates of NULL (fine) but no `vat_number` uniqueness or format check (`GB…` vs `IE…` patterns). Add CHECKs keyed off `registration_region`. Effort: Small · Risk: Low · **v1.1**.

**C10. DEFRA-only factor table for a UK+IE product** 🟠 (integrity of calculations)
`defra_conversion_factors` has no `factor_set`/`jurisdiction` column and no unique `(reporting_year, activity_type)`. Ireland reporting commonly uses SEAI/EPA Ireland factors; mixing factor sets in one table without provenance corrupts comparability. Add provenance column + unique composite (additive, not redesign). `emissions_logs.defra_factor_id` naming also bakes in UK-only. Effort: Small · Risk: Low · **v1.1** (v1.0 if IE customers are in launch cohort — seed data suggests they are).

---

## D) UK/IE GDPR & DATA GOVERNANCE FINDINGS
*(UK GDPR + DPA 2018; Irish GDPR + DPA 2018 — in scope)*

**D1. Retention settings exist but nothing enforces them** 🔴
`system_settings.audit_log_retention_days`, `data_retention_days`, `document_retention_days` are aspirational config; no table has `retention_until`/`purge_after` and no jobs exist. Simultaneously there is a genuine UK/IE tension: **Companies Act 2006 / Taxes acts require ~6-year retention of accounting records** (supplier invoices processed here are accounting records), while storage-limitation principles require deleting PII when no longer needed. Recommend per-data-class retention schedule (documented): financial/emissions evidence ≥ 6 years; `login_history`, `*_activity_log`, `email_logs` 12–24 months; `typing_status`/`user_presence` days; then pg_cron enforcement. Effort: Medium · Risk: Medium · **v1.0** for the schedule + first jobs.

**D2. No erasure/anonymization support** 🔴
Right to erasure (Art 17 UK GDPR) vs 6-year financial retention: there is no `anonymized_at` pattern, no PII inventory columns, and `users` rows are referenced from ~40 FK columns across audit/financial tables — a hard delete would either cascade-destroy audit evidence (see C1 RESTRICT recommendation) or fail. Required pattern: anonymize-in-place (`users.email` → hash, names → "Deleted User", keep UUID), which preserves referential and audit integrity. Needs a documented procedure + tested script. Also `export_history.file_url` with `expires_at` is good practice for DSAR exports — confirm enforcement. Effort: Medium · Risk: Medium · **v1.0** (procedure), **v1.1** (self-serve).

**D3. PII scattered across log tables** 🟠
`ip_address` in 10 tables, `user_agent` in 10, raw emails in `email_logs.email`, `review_audit_trail.performed_by_email`, `user_feedback.user_email`, `staff_profiles.email` (duplicates `users.email` — drift + double erasure surface). IPs are personal data under UK/IE GDPR; retention (D1) and erasure (D2) must cover all of these. Also `user_feedback` stores `browser_info`/`os_info`/`url` — may capture session data. Effort: Small (inventory) + Medium (jobs) · Risk: Low · **v1.0** inventory; **v1.1** enforcement.

**D4. Lawful-basis/consent & DPO artifacts partial** 🟡
`organizations.data_protection_officer`, `privacy_policy_url`, `terms_url` exist (good), but no `privacy_policy_version_accepted`/`accepted_at` on `users` or orgs, no marketing-consent fields on `waitlist`/`beta_users` (PECR applies to UK email marketing), and `waitlist`/`beta_users`/`email_logs` hold PII with no retention or unsubscribe linkage. Effort: Small · Risk: Low · **v1.1**.

**D5. `facilities` address model is UK-only and postcode is mandatory** 🟡
`facilities.postcode` is NOT NULL and there is **no `eircode` column on `facilities`** (unlike `organizations`, `suppliers`, `consultant_profiles` which have both). Irish facilities frequently use Eircode; rural IE addresses historically lack postcodes. Make postcode conditionally required (postcode XOR eircode) and add `eircode`. Effort: Small · Risk: Low · **v1.0** (IE customers are in seed data).

**D6. Data residency** 🟢
No schema action, but confirm Supabase project region is UK (London) or Ireland (eu-west-1) for UK/IE GDPR transfer posture, and that `system_settings.backup_storage_location` reflects the same region. Verify only · **v1.0**.

---

## E) FUTURE COMPATIBILITY (UK/IE-relevant: Xero / QuickBooks / Microsoft / API / White-label / Billing)

**E1. No external-integration identity columns** 🟠
Zero `external_id`/`integration_source`/`last_synced_at` columns on `organizations`, `suppliers`, `customer_documents`, `emissions_logs`, `facilities`. Xero and QuickBooks Online dominate UK/IE SME accounting; syncing suppliers/contacts and invoices requires stable external IDs + sync cursors. Additive columns now avoid painful backfills later. Effort: Small · Risk: Low · **v1.1** (columns), **v2.0** (sync engine).

**E2. Billing lacks UK/IE VAT fields** 🟠
`customer_subscriptions` has Stripe IDs and `currency` but no `vat_rate`/`vat_amount`/`tax_id`/`invoice_number`; `organizations` has `vat_number`/`vat_registered`/`tax_rate` (good) but nothing ties them to invoicing. UK (20%) and IE (23%) VAT on B2B SaaS is handled by Stripe Tax — acceptable — but invoice records/schema should capture VAT evidence for the customer's records. Add VAT fields alongside Stripe columns (additive). Effort: Small · Risk: Low · **v1.1**.

**E3. API readiness is half-built** 🟡
`system_settings.api_rate_limit(_burst)`, `webhook_retry_count/_delay/timeout`, `consultant_profiles.api_key`/`webhook_url` exist — but no `api_keys` table (per-key scopes, expiry, revocation, last-used) and no `webhook_events`/delivery-log table. A single plaintext key per consultant (B2) cannot support scoped, revocable API access. Effort: Medium · Risk: Low (new tables) · **v2.0**, but fix B2 hashing in **v1.0**.

**E4. White-label readiness is good; supplier portal has no identity model** 🟡
`consultant_profiles` branding columns (`brand_name`, `logo_url`, `primary_color`, `secondary_color`, `footer_text`, `email_from`, `co_branding_enabled`, `client_portal_url`) + `report_templates` branding are solid for v1.1 white-label. For the v2.0 supplier portal, `suppliers` has no `portal_user_id`/auth linkage and `users.user_type` has no supplier value — plan (don't build) a supplier user type. Effort: Small (planning/type value) · Risk: Low · **v2.0**.

**E5. Microsoft integration readiness** 🟢
No schema blockers; recommend only adding `sso_provider`/`sso_subject` columns to `users` when Entra ID SSO is scheduled (common for UK enterprise procurement). Effort: Small · Risk: Low · **v2.0**.

---

## Items NOT RECOMMENDED (ADR conflicts)

| Idea | Verdict |
|---|---|
| Replace `client_access`/`read_by` uuid[] with junction tables | NOT RECOMMENDED — conflicts with ADR (existing table structure); mitigate with GIN indexes + app-level hygiene (C4) |
| Replace jsonb `metadata`/`extracted_data` with typed columns | NOT RECOMMENDED — conflicts with ADR (jsonb metadata); mitigate with targeted GIN (A4) |
| Replace UUID PKs with bigint for index size | NOT RECOMMENDED — conflicts with ADR (UUID PKs) |
| Full partitioning redesign of all log tables pre-launch | NOT RECOMMENDED as a redesign — but a retention-job + new-table-partitioning plan (A5) is compatible and recommended |
| Convert text status columns to PG enum types | NOT RECOMMENDED (migration-hostile); use CHECK constraints instead (C3) |

---

## F) SCORING INPUTS (1–100)

| Area | Score | One-line justification |
|---|---|---|
| **Performance** | **25** | Zero secondary indexes across ~90 tables — every tenant filter, join, queue-claim, and log query will seq-scan, with no retention/partition plan for the append-only giants. |
| **Security** | **30** | RLS policies unverifiable and structurally undermined (nullable org keys, three competing permission models), plaintext `api_key`/tokens/bank details, no per-user 2FA/lockout columns, single-reset-token DoS. |
| **Supabase Compatibility** | **55** | UUID PKs, jsonb, timestamptz and Stripe/branding columns fit the platform well, but DB-backed `typing_status`/`user_presence` ignore Realtime Presence, `password_hash` collides with Supabase Auth, and service-role/RLS boundaries are undefined. |
| **Overall Production Readiness** | **32** | Broad, thoughtful domain coverage (~90 tables with DEFRA, QC, SLA, consultant, and reporting workflows) but blocked by missing indexes, unverified FK/RLS foundations, absent retention/erasure enforcement, and plaintext secrets — needs a focused hardening sprint before paying UK/IE customers. |

**Top-5 v1.0 blockers:** B1 (RLS matrix + nullable org keys), C1 (verify FKs/ON DELETE), A1–A3 (index program), B2/B9 (hash api_key; sort_code + bank-data masking), D1/D2 (retention schedule + anonymization procedure).
