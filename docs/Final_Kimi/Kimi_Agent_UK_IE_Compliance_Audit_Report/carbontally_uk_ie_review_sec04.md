# CarbonTally Production-Readiness Review — Sections 8–9

**Scope:** UK and Ireland only. All recommendations are additive and ADR-compatible: no redesign of tables, UUID primary keys, jsonb metadata columns, or the approved RLS approach. No SQL or migration code is provided.

**Evidence caveat (applies throughout Sections 8–9):** the schema dump shows primary keys, a handful of UNIQUE constraints and nullability only — **no secondary indexes, foreign keys, triggers or RLS policies are visible**. If these exist in migration files not supplied, the severity of the index/FK/RLS items drops accordingly; the structural findings (retention, secrets handling, permission models, tamper-evidence) stand regardless.

---

## 8. Performance Improvements

### 8.1 The Index Gap

The largest performance defect is the absence of any secondary indexing. `organization_id` is the tenant key on roughly thirty tables (`assets`, `facilities`, `suppliers`, `customer_documents`, `emissions_logs`, `processing_queue`, `usage_tracking`, `consultant_clients`, `activity_feed`, `audit_logs`, `conversations`, `messages` among them) and none carries an index. Non-organisation foreign keys are equally bare: `customer_documents.supplier_id`/`asset_id`, `emissions_logs.asset_id`/`defra_factor_id`, `messages.conversation_id`, `processing_steps.assignment_id`, `consultant_firm_members.firm_id`, and lookup tokens such as `password_reset_tokens.token`. Every PostgREST tenant-filtered list endpoint will sequential-scan (finding A1).

| # | Finding (table.column) | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| A1 | No secondary indexes; every FK column unindexed across ~90 tables | 🔴 | Medium | Low | v1.0 |
| A2 | Tenant composites missing: `(organization_id, status)` / `(organization_id, created_at DESC)` on `customer_documents`, `document_processing_queue`, `emissions_logs`, `upload_batches`, `report_generation_queue` | 🔴 | Medium | Low | v1.0 |
| A2 | Queue-claim composites missing: `processing_queue(queue_status, priority_score DESC, sla_deadline)`, `manual_review_queue(status, priority, sla_deadline)` — ordered for `SKIP LOCKED` claims | 🔴 | Medium | Low | v1.0 |
| A2 / C4 | Feed/messaging composites missing: `messages(conversation_id, created_at)`, `conversation_participants(conversation_id, user_id)`, `notifications(recipient_id, is_read, created_at DESC)`, `usage_tracking(organization_id, usage_month)` | 🔴 | Small | Low | v1.0 |
| A9 | UNIQUEs that double as search paths missing: `(organization_id, user_id)` on `organization_members`, `(organization_id, usage_month)` on `usage_tracking`, `(reporting_year, activity_type)` on `defra_conversion_factors`, `(report_id, version_number)` on `report_versions` | 🟠 | Small | Low–Medium (dedupe first) | v1.0 |

**Interpretation.** The blast radius is total: no query path avoids a tenant column or foreign key. Growth maths make it urgent — fifty early customers uploading a few hundred documents a month push `customer_documents` and `emissions_logs` into six-figure row counts within a year, and every dashboard pays a full scan of that accumulation per request. Because PostgREST generates the queries, the index layer is the only lever. The queue composites matter for a subtler reason: `SKIP LOCKED` worker claims must walk candidates in priority order; without a matching index the claim becomes a lock-contended scan that throttles the AI pipeline at peak volume. The UNIQUE set doubles as an integrity fix — duplicate `defra_conversion_factors` rows would silently double-count SECR emissions. All are low-risk, additive operations.

### 8.2 Partial & JSONB Indexing Strategy

The goal is not blanket indexing but hot-predicate partials and surgical GIN on jsonb columns actually filtered by key. Per the ADR the jsonb pattern stays; index rather than restructure (findings A3, A4, C3).

| # | Finding (table.column) | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| A3 | Partials missing: `is_active = true` on `suppliers`, `facilities`, `assets`, `organization_members`; `deleted_at IS NULL` on `organization_files`; `is_deleted = false AND is_archived = false` on `messages`; `is_read = false` on `notifications`/`activity_feed` | 🟠 | Small | Low | v1.0 |
| A3 | `status IN ('pending','processing')` partials missing on `processing_queue`, `manual_review_queue`, `document_processing_queue` — completed rows soon dominate | 🟠 | Small | Low | v1.0 |
| A4 / C3 | No GIN on queried jsonb: `customer_documents.extracted_data`/`mapped_data`, `manual_extraction_items.extracted_data`, `document_processing_queue.ai_extraction_result`; index only columns filtered by key (write amplification) | 🟡 | Small | Low | v1.1 |
| C1 / A10 | No `pg_trgm` GIN on `organizations.name`, `suppliers.name`/`vat_number`, `facilities.name`, `customer_documents.file_name`, `users.email`; no tsvector strategy for `messages.content` | 🔴 | Small–Medium | Low | v1.0–v1.1 |

**Interpretation.** The partial set exploits the append-heavy shape of queues and notification tables: within months, completed/read rows will outnumber live ones by orders of magnitude, so a partial index on the live predicate stays near-constant in size while the table grows unboundedly — cheap insurance against the 8.3 growth curve. The jsonb position needs more judgement: `customer_documents.extracted_data` is where invoice numbers, supplier names and kWh live post-extraction, so "find invoice INV-2024-001" currently scans every payload. GIN fixes reads but rewrites index entries on every jsonb update — real write amplification — hence the conservative line: GIN only where key filters are observed in query logs, with genuinely hot keys (`document_number`, `supplier_name`) promoted to typed columns in v1.1. Trigram indexing powers both autocomplete UX and duplicate-supplier detection for the price of one index type.

### 8.3 Append-Only Growth & Retention

Nine-plus log tables — `audit_trail`, `audit_logs`, `activity_logs`, `staff_activity_log`, `login_history`, `processing_logs`, the per-domain `*_activity_log` set, `email_logs` — plus `messages`, `emissions_logs`, `ai_content_history`, `typing_status` and `user_presence` are append-only. None carries an archive table, partition key or enforced retention, despite `system_settings.audit_log_retention_days`/`data_retention_days` (findings A5, D1).

| # | Finding (table.column) | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| A5 | No partitioning/retention on any append-only table; settings unenforced | 🔴 | Large | Medium (Low pre-launch) | Retention jobs v1.0; partitioning v1.1 |
| A5 | Monthly RANGE partitions on `created_at` for `audit_trail`, `*_activity_log`, `processing_logs`, `login_history`, `email_logs` — or at minimum documented pg_cron retention jobs | 🔴 | Large | Low on empty tables | v1.0–v1.1 |
| D1 | Per-class retention schedule absent: financial/emissions evidence ≥ 6 years; `login_history`/activity logs 12–24 months; `typing_status`/`user_presence` days | 🔴 | Medium | Medium | v1.0 |

**Interpretation.** Timing is the entire story. Partitioning an empty table is trivial DDL; retrofitting RANGE partitions onto `audit_trail` after eighteen months of production writes means table rewrites, lock windows and verification — the same finding at a different risk profile. Log volume grows as a multiple of customer *activity*, not customer count: every upload, extraction, QC check, message and login writes at least one log row, so the largest tables are also the ones auditors and support query most. The Companies Act tension makes this non-negotiable: supplier invoices are accounting records with a ~6-year retention duty, while UK GDPR storage limitation requires shedding personal data — a documented per-class schedule enforced by pg_cron reconciles both. Pre-launch is the only moment both halves are cheap.

### 8.4 Data-Type & Counter Hazards

Residual hazards sit at column level: inconsistent integer widths, unguarded denormalised counters, and realtime-churn tables misplaced in the relational store.

| # | Finding (table.column) | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| A6 | `file_attachments.file_size int4` overflows at 2 GB (bytes, while `system_settings.max_upload_size_mb` is MB-scale) vs int8 on `organization_files.size_bytes`, `document_processing_queue.file_size_bytes`, `usage_tracking.total_storage_bytes` — standardise int8 | 🟠 | Small | Low (pre-launch) | v1.0 |
| A6 | `mime_type`/`file_type` free text on file tables; add mime allowlist (pdf, xlsx, csv, jpg, png) + size CHECKs | 🟠 | Small | Low | v1.0 |
| A7 / A11 / C7 | Unguarded counters: `conversations.unread_count`/`participant_count`, `messages.read_count`, `organization_files.access_count`, `staff_workload.assigned_tasks`, `usage_tracking.*_used`, `customer_subscriptions.ai_extraction_used` — hot-row updates, drift inevitable | 🟡 | Medium | Medium | v1.1 |
| A8 | `typing_status` (upsert per keystroke) and `user_presence` (per heartbeat) lack uniqueness on `(user_id, conversation_id)`/`user_id` — duplicates possible; Realtime Presence is the native answer | 🟠 | Medium | Medium | v1.1 |

**Interpretation.** The `int4`/`int8` inconsistency is a latency bomb: 2 GB is within reach of scanned multi-hundred-page invoice bundles, and overflow surfaces as a failed upload at the customer's highest-value moment. Pre-launch the widening is near-free; post-launch it is a table rewrite. The counters are a trust issue disguised as performance: `conversations.unread_count` powers badges, `usage_tracking.*_used` and `customer_subscriptions.ai_extraction_used` power billing limits, and hot-row updates mean lock contention plus silent drift after partial failures — phantom unread badges and wrongly blocked extractions erode confidence in a product selling trustworthy numbers. The schema already contains the fix patterns: `staff_daily_performance` demonstrates the rollup, and `conversation_participants.last_read_at` is a canonical read-state source. `typing_status`/`user_presence` are an architectural mismatch — Realtime Presence exists so keystrokes never touch Postgres; table writes buy churn, vacuum pressure and duplicate-row bugs for functionality the platform provides free.

---

## 9. Security Improvements

### 9.1 RLS & Tenant Isolation

The brief asserts RLS exists, but the schema shows zero policies — and the structure undermines isolation before any policy is written (finding B1). Roughly fifteen tables carry a **nullable** `organization_id` (`activity_feed`, `audit_logs`, `conversations`, `messages`, `file_attachments`, `export_history`, `manual_review_queue`, `upload_batches`, `processing_logs`, `user_feedback`, `customer_verifications`, `draft_entries` among them), and several tenant-adjacent tables carry no tenant key at all: `email_logs`, `dashboard_metrics`, `typing_status`, `user_presence`, `beta_access_codes`, `beta_users`, `waitlist`, `glossary`, `units`, `defra_conversion_factors`, `system_settings`.

| # | Finding (table.column) | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| B1 | Policy matrix unverifiable; nullable `organization_id` across ~15 tables — NULL-org rows match no tenant policy; backfill/NOT NULL or policy-handle | 🔴 | Large | Medium | v1.0 blocker |
| B1 | Consultant isolation via `consultant_clients(consultant_id, organization_id)`; `consultant_firm_members.client_access uuid[]` needs `organization_id = ANY(client_access)` policies (index-hostile; GIN + app hygiene per C4) | 🔴 | Large | Medium | v1.0 blocker |
| B1 | Three competing permission models: `staff_roles.permissions` jsonb, `consultant_firm_members.role`/`role_id`/`permissions` jsonb + four `can_*` bools, `roles.permissions` jsonb — nominate one source of truth per surface | 🔴 | Medium | Medium | v1.0 |
| B1 | Service-role bypass discipline: workers/AI extraction bypass RLS by design — no service key client-side; worker queries filter `organization_id` in code | 🔴 | Small | Low | v1.0 |
| B10 | `notifications.recipient_type`/`recipient_id` polymorphic pair has no FK; constrain via CHECK + per-type policies | 🟡 | Small | Low | v1.0 |

**Interpretation.** A NULL `organization_id` is not an edge case; it is the default failure mode of every insert path that forgets to set it, and under a tenant-equality policy such rows become either invisible to everyone (data loss) or visible through a permissive "system row" exception (cross-tenant leak). No attacker is required: a `messages` row whose `conversations.organization_id` is NULL already sits outside the tenant boundary. The three permission models are the strategic risk — the same actor can be simultaneously forbidden and allowed on different surfaces. The blast radius is the entire multi-tenant promise: one cross-tenant sighting is a reportable ICO / Data Protection Commission incident. The `uuid[]` `client_access` model stays per the ADR, but array-containment predicates are where a planner abandons the index and a policy over-permits — GIN indexing and adversarial tests are mandatory.

### 9.2 Secrets & Sensitive Data

Three secret classes sit in plaintext: consultant API credentials, bearer tokens, and supplier banking data.

| # | Finding (table.column) | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| B2 | `consultant_profiles.api_key` plaintext varchar — store hashed (e.g. SHA-256) with lookup prefix, plus rotation/last-used columns | 🔴 | Small | Low | v1.0 |
| B2 | `beta_access_codes.magic_token`, `password_reset_tokens.token`, `user_invitations.token` stored raw — hash at rest | 🟠 | Small | Low | v1.0 |
| B9 | `suppliers.bank_account`, `iban`, `swift_code`, `bank_name` plaintext, no masking or access audit; **no UK `sort_code` field exists** (UK norm: sort code + account; IBAN/BIC the Irish norm) | 🔴 | Medium | Medium | v1.0 (sort_code + masking); v1.1 (encryption) |
| B9 | Application-layer encryption or `pgsodium`/vault, last-4 masking in API responses, read-audit logging | 🔴 | Medium | Medium | v1.1 |

**Interpretation.** The plaintext `api_key` breaks the containment RLS provides: a backup, verbose log, read replica or any service-role context yields live credentials, and a single long-lived key per consultant offers no rotation or revocation granularity (a scoped `api_keys` table is the v2.0 answer; the v1.0 obligation is to stop storing it raw). The supplier bank data is the higher-stakes UK/IE finding: invoice-fraud and payment-diversion is the dominant B2B fraud vector in both markets, and plaintext `bank_account`/`iban`/`swift_code` readable without audit is precisely the dataset needed to redirect supplier payments. The missing `sort_code` compounds it — sort codes will be improvised into `iban`/`bank_account`, corrupting validation and masking alike. Last-4 masking in API responses is the highest-leverage mitigation.

### 9.3 Authentication & Account Controls

The schema carries global security configuration it cannot enforce, plus an unresolved identity question between `users` and Supabase Auth.

| # | Finding (table.column) | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| B3 | `password_reset_tokens.user_id` UNIQUE = one active token per user; a second request overwrites it, letting an attacker DoS a victim's in-flight reset. Drop unique on `user_id`, keep on `token`, "latest valid wins" | 🟠 | Small | Low | v1.0 |
| B4 | `system_settings.two_factor_required`/`two_factor_method` exist but `users` lacks `totp_secret`, `two_factor_enabled`, `backup_codes` | 🟠 | Medium | Low | v1.1 |
| B4 | No `failed_login_attempts`/`locked_until` despite `login_attempts_max`/`login_attempts_lockout_minutes`; no `password_changed_at` for `password_expiry_days` | 🟠 | Medium | Low | v1.0 |
| B5 | `users.password_hash` nullable; all seeds have `password_hash = null`. Either Supabase Auth owns credentials (remove the duplicate) or custom auth (NOT NULL) — decide explicitly | 🟠 | Small | Low | v1.0 |

**Interpretation.** The root cause is shared: security policy was modelled as global configuration before the per-user enforcement state existed. The reset-token UNIQUE is the most immediately exploitable — an attacker who knows a victim's email can request resets on a timer and continuously invalidate the genuine token, a denial of service costing one unauthenticated request per cycle. The 2FA and lockout gaps are governance findings too: `two_factor_required` is a promise the schema cannot keep, and an enterprise questionnaire answer of "2FA enforced" must map to `users.two_factor_enabled` rows, not a settings flag. The `password_hash` decision has a sharp edge: if Supabase Auth is the IdP (ADR-consistent), the dormant column will eventually be written to, creating two credential stores that drift silently. The seed state — ten users with null hashes and `.de`/`.fr`/`.fi`/`.ai` addresses — must never ship to production.

### 9.4 Audit Integrity & UK/IE Data Governance

For a product whose proposition is auditable carbon data under SECR, the audit estate must be tamper-evident and governance must reconcile UK GDPR / Irish DPA 2018 with Companies Act retention.

| # | Finding (table.column) | Severity | Effort | Migration Risk | Implement |
|---|---|---|---|---|---|
| B7 | Six-plus audit stores (`audit_trail`, `audit_logs`, `activity_logs`, `staff_activity_log`, `processing_audit_trail`, `review_audit_trail`, per-domain `*_activity_log`) with no hash-chain, no UPDATE/DELETE prohibition, and `updated_at` on append-only rows (e.g. `activity_logs.updated_at`, `review_audit_trail.updated_at`) | 🟠 | Medium | Low–Medium | v1.1 |
| D1 | `system_settings.audit_log_retention_days`/`data_retention_days`/`document_retention_days` unenforced; Companies Act ~6-year duty vs UK GDPR storage limitation needs a documented per-class schedule + pg_cron | 🔴 | Medium | Medium | v1.0 |
| D2 | No erasure support: no `anonymized_at` pattern; `users` referenced from ~40 FK columns, so hard delete cascades or fails. Pattern: anonymise-in-place (hash `users.email`, keep UUID) | 🔴 | Medium | Medium | v1.0 (procedure), v1.1 (self-serve) |
| D3 | PII scattered: `ip_address` in 10 tables, `user_agent` in 10, raw emails in `email_logs.email`, duplicated `staff_profiles.email` | 🟠 | Small (inventory) + Medium (jobs) | Low | v1.0 inventory; v1.1 enforcement |
| D6 | Residency: confirm Supabase region UK (London) or Ireland (eu-west-1); `system_settings.backup_storage_location` must match | 🟢 | Verify only | — | v1.0 |

**Interpretation.** The tamper-evidence finding strikes at the product's reason to exist: an SECR-facing audit row that carries `updated_at` — that the application expects to modify — cannot be presented as evidence of anything; it tells a diligence team that history is negotiable. Remediation is cheap and additive: revoke UPDATE/DELETE from application roles on audit tables, drop `updated_at` from append-only logs, and consider an append hash-chain on `audit_trail`. The erasure finding is the sharpest UK/IE tension: Article 17 erasure collides with the ~6-year Companies Act duty, and hard deletion is impossible anyway — `users` is pinned by roughly forty foreign keys. Anonymise-in-place satisfies both regimes, preserving referential integrity while rendering data non-identifying, but must be a tested procedure before the first DSAR arrives. `ip_address` is personal data under UK GDPR and the Irish DPA 2018 and sits in ten tables with no retention clock. Residency is one configuration check; the rest is a v1.0 deliverable.

**Section 9 priority summary.** The v1.0 security gate: verify the RLS matrix and close the nullable-`organization_id` holes (B1); hash `consultant_profiles.api_key` and bearer tokens (B2); add `sort_code` plus bank-data masking (B9); fix the reset-token DoS and add lockout columns (B3/B4); resolve `users.password_hash` vs Supabase Auth (B5); stand up the retention schedule and anonymise-in-place procedure (D1/D2). All additive, ADR-compatible, and cheaper before UK/IE customers arrive.
