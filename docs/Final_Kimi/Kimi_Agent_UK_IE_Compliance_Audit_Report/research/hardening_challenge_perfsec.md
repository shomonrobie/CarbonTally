# CarbonTally v1.0 — Principal Architect Challenge: Performance, Security, Retention & Integrity Triage

*Critical review of the junior audit team's Production Readiness Report (`carbontally_uk_ie_review.agent.final.md` §§3, 8, 9, 12, 13) and its underlying audit briefs (dim02, dim03). Scope: UK/IE only. ADRs frozen (Supabase RLS, jsonb metadata, UUID PKs, existing table structure). No SQL. Goal: best possible v1.0 for paying UK/IE customers — not perfection.*

**Categories: A = must implement before launch · B = strongly recommended for v1.0 · C = defer to v1.1 · D = reject.**

**Headline position.** The audit is directionally sound but over-rotates on severity: it declares 26 "v1.0 launch blockers," several of which are hygiene, and it reaches for infrastructure (partitioning, blanket GIN, hash-chains, per-user auth state) that a ~50-customer pre-revenue SaaS does not need. My register contains **11 true A items** in this scope, a focused B set, and a firm list of rejects. The audit's own evidence caveat deserves more weight than the audit gives it: the schema dump showed no indexes, FKs, CHECKs or RLS policies, so half the 🔴 ratings are ratings of an *evidence pack*, not necessarily of the database. **First action before any scoring or remediation: inspect the actual Supabase migration files.** Everything below assumes the dump is accurate; items marked "verify" collapse to documentation if migrations already cover them.

Volume realism that informs every call below: ~50 launch customers × a few hundred documents/month puts `customer_documents`/`emissions_logs` at low six figures after year one, and the busiest log tables at low seven figures. Plain B-tree indexes plus retention deletes handle that comfortably. Nothing in this schema is operating at a scale that justifies partitioning, hash-chains, or write-amplifying GIN blankets in v1.x.

---

## Table 1 — Index triage

Rule applied: index what v1.0 screens and workers actually query; defer or reject the rest. Verified against the schema dump: `password_reset_tokens.token` and `units.code` are already UNIQUE; reference tables (`units`, `glossary`, `roles`, `document_types`, category tables, settings) are tiny and static — a sequential scan is the *optimal* plan there and any index is dead weight.

| Index target | Verdict | Category | Reasoning |
|---|---|---|---|
| `organization_members(organization_id, user_id)` UNIQUE | Essential | **A** | Doubles as integrity constraint AND serves the RLS membership subquery that fires on effectively every authenticated request. Hottest implicit path in the system. |
| `organization_members(user_id)` | Essential | **A** | "Which orgs am I in?" at session bootstrap; also serves RLS policies keyed on `auth.uid()`. |
| `customer_documents(organization_id, created_at DESC)` (+ status variant if the list filters by status) | Essential | **A** | The primary document list screen; the table that grows fastest. One composite covers list + pagination. |
| `emissions_logs(organization_id, start_date)` | Essential | **A** | Reporting aggregation and the emissions list; date-range scans per org are the core read pattern. |
| `suppliers(organization_id)` — with `is_active` in the composite or as a partial | Essential | **A** | Supplier picker on upload/mapping flows and the supplier list screen. |
| `facilities(organization_id)` | Essential | **A** | Facility selector and list; small per-tenant but scanned constantly. |
| `document_processing_queue(status, created_at)` — partial `WHERE status IN ('pending','processing')` | Essential | **A** | The AI-pipeline worker claim path; completed rows will dominate within weeks, so the partial keeps the index near-constant in size. |
| `messages(conversation_id, created_at)` | Essential | **A** | Chat screen pagination; the only messages query pattern that matters in v1.0. |
| `conversation_participants(conversation_id, user_id)` UNIQUE | Essential | **A** | Membership lookup + read-state write path + integrity. |
| `notifications(recipient_type, recipient_id, is_read, created_at DESC)` — partial on unread | Essential | **A** | Notification bell/badge renders on every page; unread-partial stays tiny. |
| `usage_tracking(organization_id, usage_month)` UNIQUE | Essential | **A** | Billing-gate upsert path; duplicate month rows would corrupt limit enforcement. |
| `report_versions(report_id, version_number)` UNIQUE | Essential | **A** | Versioning integrity + "latest version" lookups. |
| `defra_conversion_factors(reporting_year, activity_type)` UNIQUE | Essential | **A** | Duplicate factor rows silently double-count emissions — this is the product's number. |
| `processing_queue(queue_status, priority_score DESC, sla_deadline)`; `manual_review_queue(status, priority, sla_deadline)` | Defer-lite | **B** | Staff queue screens exist in v1.0 but volumes are trivial at launch; correct to add in the same migration batch as the A-set, not blocking. |
| `emissions_logs(customer_document_id)`; `customer_documents(supplier_id)` | Defer-lite | **B** | Document→emissions and supplier→documents drill-downs; small win, cheap. |
| `activity_feed(organization_id, created_at DESC)` | Defer-lite | **B** | Dashboard "recent activity"; fine as seq-scan at launch scale but belongs in the batch. |
| Support-view log indexes: `(organization_id, created_at)` on **one or two** log tables only (`audit_trail`, `audit_logs`) | Selective | **B** | Support will query these; the other seven log tables do not need per-table composites. Do not index all nine. |
| `user_invitations(token)`, `beta_access_codes(magic_token)` lookups (if the beta flow is still live at launch) | Situational | **B** | Auth-path lookups must be indexed, but these tables are low-volume; index only if the flow ships. |
| GIN on `consultant_firm_members.client_access uuid[]` | Selective | **B** | Required only because the ADR-locked array model forces `= ANY(client_access)` into RLS policies; without it every consultant-scoped policy seq-scans. Index the one array that carries a security predicate — not all arrays. |
| `pg_trgm` GIN on `suppliers.name` + `suppliers.vat_number`; `organizations.name` | Selective | **B** | The two v1.0 search boxes with real value: supplier autocomplete and "did you mean?" duplicate detection at supplier/org creation (the AI mapping path amplifies duplicates). Add `facilities.name` if a site-picker search ships. |
| GIN on `customer_documents.extracted_data` jsonb | Defer | **C** | The audit itself rates this v1.1. Once `document_number`/`document_date` are promoted to typed columns (report 12.1 item 8), the main "find invoice INV-2024-001" use case moves to a B-tree. Add GIN only against observed query logs. |
| Full-text (tsvector) on `messages.content` | Defer | **C** | No message-search box is committed for v1.0; build with the feature. |
| `pg_trgm` on `customer_documents.file_name`, `users.email`, `report_generation_queue.report_name`, `internal_tasks.task_title` | Defer | **C** | `users.email` is already UNIQUE (exact lookup); the rest have no committed v1.0 search UI. Revisit when the screens exist. |
| Staff/ops composites: `staff_daily_performance(staff_id, date)`, `sla_compliance(queue_id)`, `staff_workload.staff_id` | Defer | **C** | Back-office dashboards; trivial row counts at launch. |
| FK indexes on `emissions_logs.asset_id`/`defra_factor_id`, `customer_documents.asset_id`/`document_type_id`, `messages.parent_message_id`, `processing_steps.assignment_id`, QC chain FKs | Defer | **C** | Never entry points in v1.0 query paths; join direction runs the other way. Add if query logs show them. |
| GIN on audit jsonb (`audit_logs.old_data/new_data`, `audit_trail.old_data/new_data`, `activity_logs.metadata`, `report_generation_queue.generated_content`, `dashboard_metrics.metric_value`) | Reject | **D** | Nobody filters audit payloads by key in v1.0; GIN rewrites index entries on every jsonb update on the highest-write tables in the schema. Pure write amplification for zero observed read. |
| Indexes on reference/lookup tables: `units`, `glossary`, `roles`, `document_types`, `activity_categories`, `supplier_categories`, `product_categories`, `email_templates`, `notification_templates`, `system_settings`, `queue_settings`, `sla_definitions`, `business_hours` | Reject | **D** | Dozens-of-rows tables; the planner will never choose the index. Audit's "every FK column" blanket would spray ~40 useless indexes. |
| Indexes on `waitlist`, `beta_users`, `beta_access_codes` (beyond token lookup) | Reject | **D** | Pre-launch marketing tables with trivial counts; the correct v1.0 action is purging this PII (see Table 3), not indexing it. |
| Indexes on `dashboard_metrics` | Reject | **D** | A tiny cache table with no tenant key; nothing to gain. |
| Indexes on `typing_status` / `user_presence` | Reject | **D** | These tables are being replaced by Supabase Realtime Presence (see Table 2); if they temporarily stay, they need a UNIQUE constraint, not search indexes. |
| Blanket "index all ~30 `organization_id` columns" (audit A1 as written) | Reject as stated | **D (blanket) / A (subset)** | The principle is A; the blanket is D. Index the ~10 tenant tables with v1.0 list screens (above); tables like `draft_entries`, `customer_review_log`, `export_history` can wait for observed load. Every unnecessary index is write cost on the pipeline's hot path. |

**Net index call:** one migration batch of ~14–18 indexes (A + B sets) covers every real v1.0 query path. The audit's implied 60+ index program is over-scoped by roughly 3×.

---

## Table 2 — Security triage

Honest blocker test applied: *does this defect expose customer data, credentials, or money to a realistic threat at launch scale, or make a regulated promise the schema cannot keep?* If yes → A. If it is hardening that a v1.1 sprint absorbs without data migration pain → B or C.

| Item | Category | Reasoning | True blocker? |
|---|---|---|---|
| Verify full RLS policy matrix (tenant, consultant, staff, service-role surfaces) | **A** | The multi-tenant promise is the product; one cross-tenant sighting is a reportable ICO/DPC incident. Unverifiable in the dump — must be evidenced before paying customers. | **Y** |
| Resolve nullable `organization_id` — backfill + NOT NULL on the hot tenant tables (`conversations`, `messages`, `upload_batches`, `manual_review_queue`, `file_attachments`, `customer_verifications`); policy-handle the system-row tables (`activity_feed`, `processing_logs`, `audit_logs`) | **A (hot set) / B (system-row set)** | A NULL org row falls outside every tenant-equality policy — invisible-to-all (data loss) or visible-through-exception (leak). The fix is cheap pre-launch and painful after. Splitting into two classes avoids a Big-Bang NOT NULL across 15 tables. | **Y (hot set)** |
| `consultant_profiles.api_key` → hash (SHA-256 + lookup prefix) + created/last-used rotation columns | **A** | Plaintext long-lived credentials defeat everything RLS provides: any backup, log or service-role context yields live keys. Small effort, no app redesign (key issuance flow changes only). | **Y** |
| Hash `password_reset_tokens.token`, `user_invitations.token` (`beta_access_codes.magic_token` if beta ships) | **A** | Token tables are the standard breach-exfiltration target; hashing is a small, well-understood change on live auth paths. Beta table: only if it survives launch (see Table 3 purge). | **Y** |
| `password_reset_tokens.user_id` UNIQUE → drop (keep UNIQUE on `token`; latest-valid-wins in app) | **A** | Unauthenticated DoS: an attacker cycling reset requests continuously invalidates a victim's genuine token. One-line constraint change. Caveat: if Supabase Auth owns resets (see `password_hash` decision), this table is dead code — then deprecate it instead, which is the same effort class. | **Y** |
| Resolve `users.password_hash` vs Supabase Auth — decide explicitly; if Auth is IdP (ADR-consistent), drop/dead-column it and never write to it | **A** | Not a vulnerability today (all hashes NULL) but a guaranteed future one: a dormant credential column will eventually be written, creating two drifting credential stores. The decision costs nothing pre-launch and is embarrassing to retrofit. | **N** (but must be *decided* pre-launch) |
| Supplier bank details: add `sort_code`; last-4 masking in API responses; read-access discipline | **B** | Payment-diversion fraud is the dominant UK/IE B2B fraud vector and this is exactly the dataset it needs — but v1.0 has no supplier-payment execution, so the realistic exposure is display/export leakage, which masking closes. Promote to A only if any payment-run or supplier-portal feature ships in v1.0. | **N** |
| Supplier bank details: app-layer encryption / pgsodium at rest | **C** | Supabase already encrypts storage at rest; a second encryption layer whose keys live beside the service role adds key-management burden for marginal protection. Revisit when supplier-portal/multi-user access widens read paths. | N |
| Per-user 2FA columns (`totp_secret`, `two_factor_enabled`, `backup_codes`) | **C** | If Supabase Auth is the IdP, TOTP/MFA belongs to the platform (`auth.mfa_*`), not `users`. Building parallel auth state contradicts the ADR direction. Real v1.0 obligation: stop advertising `two_factor_required` as enforced in enterprise questionnaires until it is. | N |
| Lockout columns (`failed_login_attempts`, `locked_until`) behind existing settings | **C** | Same logic: Supabase Auth provides rate limiting; duplicating it in `users` creates two sources of lockout truth. If custom auth is chosen (the `password_hash` decision), this promotes to B. | N |
| Audit tamper-evidence, stage 1: revoke UPDATE/DELETE from app roles on audit tables; drop `updated_at` from append-only log tables | **B** | Cheap, high-credibility: an SECR-facing audit row carrying `updated_at` tells a diligence team history is negotiable. Privilege revocation + PITR backups is the honest tamper-evidence storey at v1.0 scale. Not a blocker because no external auditor exists yet at launch. | N |
| Audit tamper-evidence, stage 2: append hash-chain on `audit_trail` | **D** | Reject (Table 5). | N |
| `ip_address` standardise on `inet` across ~10 log tables | **C** | Type hygiene + backfill; nothing breaks at v1.0 volumes. varchar/text IPs are ugly, not dangerous. | N |
| `notifications.recipient_type` CHECK + explicit per-type policies | **B** | Polymorphic recipient with no FK is fragile, but the concrete risk is a policy bug leaking notifications cross-tenant — real, low-probability, cheap to reduce. Small effort. | N |
| Service-role bypass discipline (no service key client-side; workers filter `organization_id` in code) | **A (verify)** | Verification/documentation, not schema work. A leaked service key nullifies RLS entirely. | **Y (as a checklist gate)** |

---

## Table 3 — Practical UK/IE retention schedule

Reconciliation principle: UK GDPR/DPA 2018 (and Irish GDPR/DPA 2018) storage limitation is satisfied not by deleting everything quickly but by a *documented, enforced per-class schedule* — personal data kept no longer than necessary **for the purpose**, where the ~6-year financial-record duty (Companies Act 2006 s.388; HMRC CT/VAT records; Ireland: Companies Act 2014, Taxes Consolidation Act s.886) *is* the purpose for accounting evidence, with Art 6(1)(c)/17(3)(b) legal-obligation as the lawful basis overriding erasure for that class. Personal identifiers attached to business records are anonymised when the person's relationship ends; the financial substance stays.

| Data class | Retention | Basis | Enforcement mechanism | Category |
|---|---|---|---|---|
| Uploaded documents that are accounting evidence (supplier invoices/utility bills in `customer_documents`, `organization_files`, extracted invoice fields) | **6 years from end of the financial year** they support | Companies Act 2006 s.388; HMRC 6-yr; IE TCA s.886 (6 yrs) | `retention_until` column set at ingest (FY end + 6y) + pg_cron sweep; legal-hold flag; RLS-scoped archive, not hard delete, until expiry | **B** (column + job) |
| `emissions_logs` + factor provenance + `report_versions` (SECR substantiation) | **6 years minimum**, aligned to the documents they substantiate | Same financial-evidence duty; SECR reports must be re-defensible | Rides the document schedule; no separate deletion job in v1.x | **B** |
| `audit_trail` / `audit_logs` (security-relevant audit) | **24 months** hot, then delete (or archive) | Storage limitation vs security-investigation window; no statutory audit-log duty beyond the financial records themselves | pg_cron monthly delete on `created_at`; needs a `created_at` index on those two tables only | **B** |
| Per-domain `*_activity_log` set, `staff_activity_log` | **12 months** | Operational/support value decays fast | Same pg_cron job, different interval | **B** |
| `login_history` | **12 months** | Security incident window; IPs are personal data | pg_cron | **B** |
| `processing_logs` | **90 days** | Pure debugging exhaust | pg_cron | **B** |
| `email_logs` (contains raw recipient emails) | **12 months** | Delivery-dispute window; PII minimisation | pg_cron | **B** |
| `messages` / `conversations` | Life of the customer account; purge/anonymise 12 months after org closure unless tied to a retained document thread | Storage limitation; no statutory duty for chat | Closure job (ties to `organizations.archived_at`); no periodic job in v1.0 | **B** |
| `typing_status` / `user_presence` | **Ephemeral — hours, 7-day hard cap** (and ideally never in Postgres at all: Realtime Presence) | Data minimisation; zero business purpose after the session | Realtime migration (v1.1); interim: UNIQUE constraints + daily pg_cron purge | **B (interim purge) / C (Realtime)** |
| `waitlist` / `beta_users` / `beta_access_codes` PII | **Delete or convert at launch; 12-month absolute cap** | Storage limitation; these are pre-launch marketing artefacts | One-time purge job at GA; keep only rows with a lawful basis to contact | **B** |
| `export_history` files (incl. DSAR exports) | **Enforce existing `expires_at`; ≤30 days** | DSAR exports are concentrated PII — the worst thing to leave in a bucket | Lifecycle rule on the storage bucket + job verifying `file_url` deletion | **B** |
| `notifications` | **6 months** (read) / 12 months (unread cap) | Minimisation; no evidentiary value | pg_cron | **C** |
| Consent/lawful-basis artefacts (`privacy_policy_version_accepted`, marketing consent on waitlist/beta) | N/A — fields to add in v1.1 | PECR for UK electronic marketing; accountability principle | App-layer capture at signup | **C** |

Audit's retention recommendations, classified:
- **Per-class schedule + first pg_cron jobs — B.** Genuinely needed, but it is not a day-one blocker: on empty tables nothing ages out for months. Must exist before any table is old enough to breach its own schedule — i.e., land it in the first weeks post-launch at the latest. The audit's 🔴 overstates.
- **`retention_until` columns — B** for the document/financial class (per-row FY anchoring + legal hold); **C** as a blanket pattern.
- **Anonymise-in-place erasure procedure (hash `users.email`, "Deleted User", keep UUID) — A.** `users` is pinned by ~40 FKs; hard delete is structurally impossible. A DSAR can arrive on day one with a one-month clock, and an untested erasure script run under deadline against a live tenant is how companies end up in front of the ICO. Procedure written and tested pre-launch; self-serve UI is C.
- **PII inventory (IP in 10 tables, user_agent in 10, raw emails in `email_logs`/`review_audit_trail.performed_by_email`/`user_feedback.user_email`, duplicated `staff_profiles.email`) — B.** A one-page documented inventory is an Art 30/accountability cheap win and is what makes the retention jobs provably complete.
- **DSAR export expiry enforcement — B** (mechanism above).
- **Consent/PECR fields — C.** v1.0 is B2B onboarding of named customer users (contract/legitimate interest covers it); marketing consent matters only for the waitlist/beta lists, which Table 3 purges at launch anyway.
- **Residency verification (Supabase region UK-London or eu-west-1; `backup_storage_location` matches) — A (verify only).** One configuration check; free.

---

## Table 4 — Business rules & integrity triage

| Item | Category | Reasoning |
|---|---|---|
| UNIQUE `organization_members(organization_id, user_id)` | **A** | Duplicate memberships corrupt role checks and the RLS subquery semantics. Also delivers the hottest index (Table 1). |
| UNIQUE `consultant_clients(consultant_id, organization_id)` | **A** | Same consultant linked twice to one org breaks billing and access-scoping maths. Cheap. |
| UNIQUE `usage_tracking(organization_id, usage_month)` | **A** | Billing-limit upserts assume one row per month; duplicates silently double or split allowances. |
| UNIQUE `defra_conversion_factors(reporting_year, activity_type)` | **A** | Duplicate factors double-count the product's core number. Extend the key when `factor_set`/`country` columns land (report 12.1 item 5). |
| UNIQUE `report_versions(report_id, version_number)` | **A** | Versioning is the reporting spine's integrity model; duplicates make `is_current` ambiguous. |
| UNIQUE on `suppliers(organization_id, vat_number)` and `(organization_id, company_number)` — partial, `WHERE NOT NULL` | **A** | Deterministic duplicate prevention on the two identifiers that are actually unique in the real world; feeds AI mapping integrity. Pre-revenue DB means dedupe-first risk is near zero. |
| UNIQUE on `suppliers(organization_id, name)` | **D** | Reject: same-name suppliers legitimately exist (two "City Electrical" branches), and a name-unique forces ugly workarounds ("City Electrical 2"). The correct control is trigram "did you mean?" at creation (B, Table 1) — a UX prompt, not a hard constraint. |
| `organizations.is_active` + `archived_at` | **A** | Paying customers churn from day one; without a suspend path the only lever is deleting audit evidence. Small, additive, feeds the messages-purge job in Table 3. |
| `customer_documents` soft-delete (`deleted_at`) | **B** | Right thing while the table is young, but not a gate: it changes every query path that reads documents (app impact medium), and nothing at launch volume is unrecoverable via backups. Land early in v1.0 with the RLS filter. |
| `file_checksum` (SHA-256) on `customer_documents`, `organization_files`, `file_attachments` | **B** | Deterministic duplicate-upload detection — the cheapest trust feature in the report. Column + app-computed hash now; unique enforcement in v1.1 once duplicate-handling UX is designed. |
| Verify every FK + explicit ON DELETE; RESTRICT on financial/audit tables (`emissions_logs`, `customer_documents`, `report_versions`, audit estate) | **A (verify) / B (remediate)** | A multi-tenant financial product cannot launch without *knowing* its delete behaviour. Verification is a blocker; actual constraint changes only where inspection shows dangerous CASCADEs. |
| NOT NULL DEFAULTs on hot booleans/timestamps (`is_active`, `is_read`, `is_deleted`, `email_verified`, `sla_breached`, `created_at` on queried tables) | **A (targeted set) / C (full sweep)** | Tri-state NULLs silently drop rows from `WHERE is_active` filters — including RLS-adjacent and billing-gate filters. Targeted set on auth/queue/billing paths is launch-grade; the remaining ~80 columns are a v1.1 sweep. |
| CHECK value lists (not PG enums, per ADR) on `processing_queue.queue_status`, `document_processing_queue.status`, `customer_documents.status`, `organization_members.role`, `customer_subscriptions.status` | **A (queue/billing/role) / C (the remaining ~20)** | Queue and billing status typos become silent states that workers and limit-checks miss. On a pre-revenue DB, existing-value mapping risk is low. The other 20 free-text statuses are honest C. |
| Money precision `numeric(12,2)` + CHECK ≥ 0 on billing tables | **B** | Unconstrained numeric is sloppy but has not corrupted anything yet; billing tables are low-write. Batch into the integrity migration. |
| Deprecate `pending_invites` (strict subset of `user_invitations`, no token/expiry) | **B** | Stop writes + alias reads now, drop in v1.1. Not a blocker because the stronger table exists and the weak one is likely unwritten. |
| Deprecate one of `notification_delivery` / `notification_delivery_log` | **B** | Identical column sets; pick one writer. Cheapest redundancy fix in the schema, but duplication is a maintainability smell, not a launch risk. |
| Seed cleanup: remove `.de`/`.fr`/`.fi`/`.ai` users; add IE org + IE facility (Eircode, EUR, IE factor) fixtures | **A** | Never ship out-of-market PII-flavoured seed users to production (data minimisation + demo integrity), and the missing Irish fixture is the regression guard that let the `facilities.postcode` blocker survive. This is the cheapest launch-gate item in the entire report. |
| Relax `customer_documents.asset_id` NOT NULL | **A** | Supplier invoices and reports have no asset; the constraint forces fake assets into the emissions hierarchy — manufactured data corruption on the product's core entity. One-line nullability change, pre-launch-safe. |
| Relax `customer_documents.organization_member_id` NOT NULL (consultant/staff/system uploads) | **B** | Real gap (system/pipeline uploads have no member), but workaroundable at launch; batch with the `asset_id` change. |

---

## Table 5 — Category D rejects (over-engineering watchlist)

| Recommendation | Why rejected |
|---|---|
| **Audit hash-chain / cryptographic tamper-evidence** (beyond revoking UPDATE/DELETE) | A hash chain computed and verified by the same system (and same DBA/service role) that could rewrite it proves nothing to an external auditor; real tamper-evidence requires external anchoring (WORM storage, notarisation) that is v2.x territory. Privilege revocation + `updated_at` removal + PITR backups deliver the practical immutability storey at 5% of the complexity. Building a chain now is security theatre with a maintenance bill. |
| **Monthly RANGE partitioning of 9+ log tables** (audit 12.2 item 16, rated 🔴) | Rejected for v1.x entirely. At launch volumes the biggest log table will hold low-seven-figure rows after a year — trivially served by one `created_at` index plus retention DELETEs. Partitioning multiplies operational surface (partition maintenance jobs, per-partition constraint/policy inheritance surprises, every future migration touching partition topology) for zero measurable benefit. The audit's "pre-launch is the only cheap window" argument mistakes *cheap to do* for *worth doing*; PG declarative partitioning on a still-small table in v1.2 remains cheap if ever needed. Revisit trigger, documented: single table >10–20M rows, or retention DELETEs causing vacuum pressure. |
| **Full audit/log-table consolidation** | Conflicts with the frozen ADR (per-domain log design). The audit already says this; I confirm and strengthen it: do not re-raise it at v2.0 planning either unless the unified view demonstrably fails support staff. |
| **Unified audit view in v1.0** (timing, not the idea) | Right idea, wrong version — there is no external auditor and no support volume at launch; support can union two tables for months. **C** as a recommendation; rejecting only the "high-value single item" urgency the audit assigns it. |
| **Blanket GIN on all jsonb columns** | Write amplification on the highest-write tables (queues, audit) for zero observed key-filter queries. GIN only against query-log evidence; the `client_access` array GIN is the sole security-driven exception (Table 1). |
| **Blanket pg_trgm / tsvector program** (audit C1 rated 🔴 v1.0) | Only two v1.0 search boxes carry real value (supplier/org name + dup detection → B). Message FTS, file-name trigram, task-title trigram have no committed UI. A search blocker must block a *screen*, not an aspiration. |
| **`uuid[]` → junction tables** (`client_access`, `read_by`) | ADR conflict, correctly flagged by the audit. Additionally: at v1.0 scale the arrays are functionally fine with GIN + app hygiene. |
| **County lookup tables** (26 ROI + 6 NI + UK ceremonial) | Neither Royal Mail nor Eircode routing requires county; county is display data in both markets. A lookup table is a maintenance artefact in search of a requirement. If facet consistency is ever needed, a CHECK-in list is sufficient (C). |
| **`external_id`/`integration_source`/`last_synced_at` columns "now"** (audit 11.1.1) | YAGNI. Speculative identity columns across five tables with no sync contract invite semantic drift — what does `external_id` mean before any integration exists? Columns are cheap, but *wrong* columns are not. Add when the Xero/QBO integration is scoped and the target system's identity model is known. (D for "now"; the audit's own v1.1 placement was already generous.) |
| **`api_keys` / `webhook_events` tables in v1.x** | Confirmed reject for v1.0/v1.1: the settings layer advertising rate limits is not a commitment to build an API product. v2.0, when the first integration customer exists. |
| **Deleting dormant EU/US fields** (`cik`, `naics_code`, `isin`, `sedol`, `issb_*`, `esrs_*`) | Reject the deletion (agree with audit): dropping compliance-relevant columns from a live schema is irreversible scope vandalism; `nace_code`/`esrs_enabled` may activate for Irish CSRD-scope customers. Dormant ≠ deleted. |
| **Local `invoices` table / `contacts` table / `support_tickets` table for v1.x** | Stripe-hosted invoices + Stripe Tax cover UK/IE VAT evidence at v1.0 scale; contacts and tickets freeze premature workflow models. C at best; rejected as v1.0 items. |
| **Per-user 2FA/lockout columns in `users`** | Rejected as *schema* work (Table 2): duplicates Supabase Auth's platform responsibility under the frozen ADR direction. The genuine obligation is honest marketing of the global settings flags. |

---

## Table 6 — Phase assignment for A/B items

Phases per client roadmap: **P1 critical fixes · P2 data integrity · P3 performance · P4 validation · P5 compliance.** DB impact / app impact (none–small–medium) / migration risk on a live-but-pre-revenue DB / rollback difficulty. Batching notes at the end.

| Item | Phase | DB impact | App impact | Migration risk | Rollback |
|---|---|---|---|---|---|
| Verify RLS policy matrix (incl. service-role discipline checklist) | **P1** | None (verification) → Medium if policies written | None | Low (verify) / Med (policy changes can lock out users — test with non-privileged roles) | Easy (policy replace) |
| Resolve nullable `organization_id` on hot tenant tables (backfill + NOT NULL / policy-handle) | **P1** | Medium | Small (insert paths must always set org) | Med | Moderate (dropping NOT NULL is easy; un-backfilling is not — snapshot first) |
| Hash `api_key` + reset/invite tokens; drop `password_reset_tokens.user_id` UNIQUE; decide `users.password_hash` ownership | **P1** (one security migration) | Small | Small (issuance/verification flows) | Low | Token hashing is one-way — roll forward, not back (re-issue keys/tokens) |
| FK + ON DELETE verification; RESTRICT on financial/audit where dangerous CASCADE found | **P1** (verify) → **P2** (remediate) | Medium | None | Med (orphan cleanup possible) | Easy-moderate |
| Seed cleanup + Irish org/facility fixtures | **P1** | Small | None | Low | Easy |
| `organizations.is_active` + `archived_at`; relax `customer_documents.asset_id` NOT NULL (+ `organization_member_id`) | **P1** | Small | Small (suspend UI hook; upload paths) | Low | Easy |
| Anonymise-in-place erasure procedure (documented + tested) | **P5, but launch-gated** | Small (procedure, not schema) | None in v1.0 (manual runbook) | Med (destructive script — test on staging with production-like FK graph) | Not reversible by design — test evidence *is* the mitigation |
| Residency verification | **P5** (one check) | None | None | Low | N/A |
| Unique set: org_members, consultant_clients, usage_tracking, defra factors, report_versions, supplier vat/company partials | **P2** (one migration) | Medium | None (surfaced as 409s the app should already handle) | Low–Med (dedupe first; near-zero pre-revenue) | Easy (drop constraint) |
| NOT NULL DEFAULTs on targeted hot booleans/timestamps | **P2** | Medium | Small | Low–Med (backfill NULLs first) | Easy |
| Status CHECK value lists on queue/billing/role columns | **P2** | Small | Small (invalid-state error handling) | Med (existing values must map — verify in staging) | Easy |
| Money `numeric(12,2)` + ≥0 CHECKs; `file_checksum` columns; `file_size` int8 widening; mime allowlist | **P2** | Medium | Small | Low | Easy-moderate |
| `customer_documents` soft-delete (`deleted_at` + RLS/query filters) | **P2** | Small (column) | **Medium** (every document read path filters) | Med | Moderate (column drop safe only before app depends on it) |
| `suppliers.sort_code` + last-4 bank masking in API | **P2** | Small | Small | Low | Easy |
| Deprecate `pending_invites` + one notification delivery table (stop writes) | **P2** | Small | Small | Low | Easy |
| Index baseline: A-set (~11) + B-set (~7) incl. queue partials, notification partial, support log indexes, `client_access` GIN | **P3** (one batch, built CONCURRENTLY) | Medium | None | Low | Trivial (drop concurrently) |
| `pg_trgm` on `suppliers.name`/`vat_number`, `organizations.name` (+ dup-detection UX wiring) | **P3** (index) / **P4** (UX prompt) | Small | Small | Low | Trivial |
| Retention schedule document + first pg_cron jobs (processing_logs 90d; login/email 12m; activity logs 12–24m; audit 24m; typing/presence purge) | **P5** (design in P1, jobs can land any time pre-launch) | Small | None | Low (test jobs with small batches + dry-run counts first) | Easy (drop job) |
| `retention_until` on document class + 6-year document/emissions schedule | **P5** | Small | Small (ingest sets value) | Low | Easy |
| PII inventory (one-page doc); DSAR export expiry enforcement; waitlist/beta purge at GA | **P5** | Small | Small | Low | Easy |
| Audit privilege hardening: revoke UPDATE/DELETE on audit tables; drop `updated_at` from append-only logs | **P2** (with FK/RESTRICT work) | Small | None (verify nothing updates audit rows — grep app code first) | Low–Med | Easy (re-grant) |
| `notifications.recipient_type` CHECK + per-type policies | **P2** | Small | Small | Low | Easy |
| Typing/presence interim UNIQUE constraints (+ daily purge job) | **P3** | Small | None | Low | Easy |

**Batching guidance (minimises migration count and lock windows):**
1. **P1 security migration:** token/api_key hashing columns + reset-token UNIQUE drop + `sort_code` — one deploy.
2. **P1 tenancy migration:** `is_active`/`archived_at`, `asset_id`/`organization_member_id` nullability, nullable-org backfill + NOT NULL — one deploy, staged: backfill → verify → constrain.
3. **P2 integrity migration:** all six uniques + targeted NOT NULL DEFAULTs + status/money/range CHECKs + `file_checksum` + `deleted_at` — one deploy after staging data audit; CHECKs added `NOT VALID`-style then validated to avoid table locks.
4. **P3 index migration:** the full A+B index set, each built CONCURRENTLY (separate transactions, one release).
5. **P5 compliance pack:** retention doc + pg_cron jobs + erasure runbook + inventory — documentation-led, two small migrations (`retention_until`, job schedule).

---

## Strongest challenges to the audit team

1. **"26 v1.0 launch blockers" is severity inflation that endangers the launch.** A blocker list containing URL-format CHECKs, 1–5 rating CHECKs and `numeric(12,2)` money precision trains the client to stop believing the word "blocker." My register has ~11 true A items in this scope. The report would be stronger with the courage to say B.
2. **Partitioning (12.2 item 16) should never have been rated 🔴 Critical at any version.** The "pre-launch is the only cheap window" argument confuses cheap-to-do with worth-doing; the finding survives contact with actual volume maths (low-seven-figure rows after year one). Demoted to D with a documented revisit trigger (>10–20M rows per table or vacuum pressure).
3. **The hash-chain recommendation is security theatre.** A tamper-evidence mechanism whose verifier is the same principal as its writer has no evidentiary value; the audit should have rejected it outright instead of "consider." Privilege revocation + dropped `updated_at` + PITR is the honest storey.
4. **The 🔴 rating on trigram search (10.3.1 / 12.1 item 10) conflates UX polish with launch gating.** Supplier/org-name trigram earns B on duplicate-detection merits; message FTS and file-name trigram have no committed screens. An autocomplete box is not a production blocker for a carbon ledger.
5. **Bank-details encryption-at-rest is over-weighted; masking and process are under-weighted.** Supabase storage is already encrypted; the marginal value of app-layer encryption whose keys sit beside the service role is small, while the actual UK/IE payment-diversion control — last-4 masking, read audit, bank-change verification process — gets one sentence. Proportionality matters.
6. **Recommending per-user 2FA/lockout columns contradicts the audit's own Supabase-Auth observation.** If Auth is the IdP (the ADR-consistent reading, supported by null `password_hash` seeds), these columns build parallel auth state the platform already owns. The correct v1.0 action is the `password_hash` ownership decision plus honest marketing of the global flags.
7. **The index program is ~3× over-scoped.** "Index every FK across ~90 tables" sprays write-amplifying indexes onto static reference tables (`units`, `glossary`, `roles`), marketing tables being purged at launch (`waitlist`, `beta_users`), and FKs that are never query entry points. Index what v1.0 screens query — about 15–18 indexes total.
8. **The evidence caveat is buried.** The dump showed no indexes, FKs, CHECKs or RLS policies, so the Performance (25) and Security (30) scores may be scoring an artefact of the evidence pack. "Inspect the migration files" should be finding zero, not a footnote — if migrations contain the index layer, the entire §8 severity structure collapses to a verification exercise.
9. **Retention is rated 🔴 v1.0 while the anonymise procedure shares that rating — the priorities are inverted.** On empty tables, retention jobs have nothing to delete for months (B). But an erasure request can arrive on day one against a `users` table pinned by ~40 FKs, with a one-month statutory clock (A). The genuinely urgent compliance artefact is the tested procedure, not the cron job.
10. **The unified audit view is oversold as "the highest-value single item."** It is a v1.1 nicety with no customer at launch; the highest-value single item in §3.5 is deprecating `pending_invites` and the duplicate delivery table — boring, cheap, and it removes a live security downgrade.

---

*End of challenge brief. Companion scope note: UK/IE field validation matrix, address model detail and the Ireland facilities/factor-model blockers are triaged against report §§4–7 and are outside this document's §§3/8/9/12/13 mandate; this brief deliberately touches them only where they intersect performance, security, retention or integrity.*
