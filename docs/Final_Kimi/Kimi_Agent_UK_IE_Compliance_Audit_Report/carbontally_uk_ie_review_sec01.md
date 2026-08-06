# CarbonTally v1.0 Database Production Readiness Review

*UK & Ireland Launch Edition — prepared 4 August 2026; scope: UK and Irish business practices only; ADRs treated as approved; review-and-recommend only (no SQL, no migrations, no redesign).*

## 1. Executive Summary

CarbonTally's ~90-table Supabase/PostgreSQL schema shows broad, thoughtful domain coverage — an emissions pipeline, a QC and SLA estate, a consultant channel and a versioned reporting spine — but it is **not yet production-ready** for paying UK and Irish customers. The overall readiness score is 32/100. Nothing found requires redesign: every defect class is addressable through additive columns, CHECK constraints, indexes and documented procedures within the approved architecture. What is required is a focused hardening sprint before launch, sequenced around five launch-blocking themes.

1. **The Ireland blocker.** `facilities.postcode` is NOT NULL and `facilities` has no `eircode` column, although `organizations`, `suppliers` and `consultant_profiles` carry both; Ireland has no postcode system, so an Irish customer can create an organisation but cannot register the site whose emissions the product exists to measure.
2. **Jurisdiction data integrity.** `country`, six `currency` columns, three `vat_number` columns, `company_number`, `postcode` and `eircode` are all unconstrained free text — yet every jurisdiction rule (VAT format, postcode versus Eircode, GBP versus EUR, timezone, factor selection) keys off them.
3. **A UK-only emission factor model in a UK+IE product.** `defra_conversion_factors` carries no `unit`, `scope` or `source`, no SEAI/EPA set exists, and `emissions_logs.raw_quantity` is unit-less — a DEFRA grid factor applied to a Dublin site returns a wrong Scope 2 figure with no warning.
4. **Zero secondary indexes and unverifiable foundations.** No secondary index, foreign key, CHECK or RLS policy is visible in the schema dump across ~90 tables; every tenant-filtered list endpoint will sequential-scan, and the multi-tenant isolation promise cannot currently be evidenced.
5. **Plaintext secrets and absent governance.** `consultant_profiles.api_key`, bearer tokens and supplier bank details (`bank_account`, `iban`, `swift_code`) sit in plaintext, and `system_settings.audit_log_retention_days`/`data_retention_days` are unenforced — leaving UK GDPR storage-limitation and erasure duties, and the Companies Act retention duty, unreconciled.

The genuinely good news deserves equal clarity. The notification estate (`notifications`, `notification_templates`, delivery tracking), the reporting spine (`report_templates`, `report_generation_queue`, `report_versions.is_current`), the consultant white-label columns on `consultant_profiles`, structured address columns on three of four address tables, SECR intensity denominators in `organization_metadata` (`annual_revenue`, `average_employees`, floor area), and a settings layer that already anticipates multiple emission factor sets (`system_settings.default_emission_factor_set`) are all sound foundations that the recommendations below protect rather than replace.

**Reading guide.** Section 2 presents the scoring; Section 3 assesses architecture. Sections 4–5 assess UK and Ireland readiness; 6–7 catalogue missing fields and the validation matrix; 8–9 cover performance and security; 10 addresses UX; 11 future expansion. Section 12 consolidates the phased remediation roadmap; 13 records governance items, ADR-constrained non-recommendations and evidence caveats; 14 provides the finding index and methodology.

## 2. Overall Readiness Score

| Dimension | Score /100 |
|---|---|
| Architecture | 62 |
| Performance | 25 |
| Security | 30 |
| Scalability | 55 |
| Maintainability | 48 |
| Compliance | 50 |
| Data Integrity | 55 |
| Developer Experience | 72 |
| Supabase Compatibility | 55 |
| **Overall Production Readiness** | **32** |

One-line justification per dimension:

- **Architecture (62):** strong domain breadth undermined by three parallel processing queues, 9+ audit log tables, duplicate invitation/delivery/messaging concepts and a UK-only factor model.
- **Performance (25):** zero secondary indexes — every tenant filter, join, queue-claim and log query sequential-scans, with no retention or partition plan for the append-only giants.
- **Security (30):** RLS unverifiable and structurally undermined by nullable `organization_id` columns, three competing permission models, and plaintext `api_key`, tokens and supplier bank details.
- **Scalability (55):** UUID keys, tenant-scoped rows and usage tracking are good foundations; missing indexes, jsonb hot paths and counter drift cap headroom.
- **Maintainability (48):** ~25 free-text `status` fields, four competing read-state mechanisms and three sources of truth for approval, fiscal year and contacts make safe change expensive.
- **Compliance (50):** Companies House, HMRC VAT, SIC 2007, SECR financial-year, Eircode, CRO and SEAI validations are all absent; Irish facilities cannot be inserted at all.
- **Data Integrity (55):** core business fields (`country`, `currency`, VAT, company number, postcode/Eircode, percentages, emission values) are free text with virtually no CHECK constraints.
- **Developer Experience (72):** consistent UUID/timestamptz/jsonb patterns, but six unconstrained currency columns, triplicated contact models and DEFRA-hard-coded naming for a two-market product.
- **Supabase Compatibility (55):** the platform fit is good, but DB-backed `typing_status`/`user_presence` ignore Realtime Presence, `users.password_hash` collides with Supabase Auth, and service-role/RLS boundaries are undefined.
- **Overall (32):** the weighted picture — broad coverage, blocked by indexes, unverifiable RLS/FK foundations, plaintext secrets and absent retention enforcement.

![CarbonTally v1.0 production readiness scores by dimension](carbontally_uk_ie_review_scores.png)

The chart sorts the dimensions against a 60-point production threshold: only Developer Experience and Architecture clear it. The distribution matters more than the mean. The two lowest scores — Performance and Security — are precisely the dimensions where defects are invisible in a demo and catastrophic in production: a sequential scan is indistinguishable from an indexed query at fifty rows, and a nullable `organization_id` leaks nothing until the row that matters is written. Conversely, the high Developer Experience score confirms that the remediation programme is working with the grain of the codebase, not against it: the conventions a hardening sprint needs (consistent key types, additive CHECKs, CHECK-in lists rather than enums) are already the codebase's own idioms. The Overall score of 32 is not an average of the dimensions but a gate: no UK/IE launch should proceed while any dimension that touches customer money or regulated data sits below threshold.

**Evidence caveat.** The schema dump showed no secondary indexes, RLS policies, foreign keys or CHECK definitions — only primary keys, a handful of UNIQUE constraints and nullability. If these exist in migration files not supplied to the audit, the Performance and Security scores rise accordingly; the structural findings — the Ireland blocker, the factor-model gap, plaintext secrets, unenforced retention and the architectural duplications of Section 3 — stand regardless, because they concern columns and tables that do not exist rather than constraints that might.

## 3. Architecture Assessment

### 3.1 Structural Strengths

The emissions pipeline runs end to end: `customer_documents` and `upload_batches` feed `document_processing_queue`, extractions land in `extracted_data` jsonb, and results resolve to `emissions_logs` joined to `defra_conversion_factors`. The QC/SLA estate is unusually complete for a v1.0 — `qc_checks`, `qc_checklists`, `qc_errors`, `sla_definitions`, `sla_compliance` and `business_hours` give operations real levers. The consultant channel (`consultant_profiles`, `consultant_clients`, `consultant_billing`) carries white-label branding columns that make the v1.1 channel story credible, and the notification estate is genuinely production-grade. These strengths are why the Architecture score leads the operational dimensions.

### 3.2 Structural Weaknesses

| Weakness | Evidence (tables) | Consequence |
|---|---|---|
| Three parallel processing queues | `manual_review_queue`, `processing_queue` (+`processing_assignments`/`processing_steps`), `document_processing_queue`; `customer_documents` holds both `manual_review_queue_id` and `processing_queue_id` | The single biggest coherence problem: ~70% purpose overlap, divergent status, a document able to sit in two queues at once |
| 9+ audit/activity log tables | `audit_trail`, `audit_logs`, `activity_logs`, `staff_activity_log`, per-domain `*_activity_log`, `email_logs`, `login_history` | No single timeline per document; auditors must union tables; retention multiplied across stores |
| Duplicate invitation tables | `pending_invites` (no token, expiry or status) vs `user_invitations` (full lifecycle) | The weaker table is a security downgrade still writable |
| Duplicate notification delivery | `notification_delivery` vs `notification_delivery_log` — identical column sets | Delivery state can be written twice and read inconsistently |
| Duplicate review-history tables | `customer_review_log`, `review_audit_trail`, `review_assignment_history` | Two tables record the same assignment changes with old/new values |
| Three user-identity tables | `users`, `staff_profiles` (own UNIQUE `email`, duplicating `users.email`), `consultant_profiles` | Identity drift; two sources of truth for the same person |
| Duplicated communication models | `conversations`/`messages`/`conversation_participants` vs `customer_communication` | Two messaging channels; four competing read-state mechanisms on the messaging side |
| Triplicated QC paradigms | `qc_*` column sets on three queue/batch tables vs standalone `qc_checks`/`qc_checklists`/`qc_errors` | QC as columns and QC as tables run in parallel with no link |

The pattern across all eight rows is the same: a concept was modelled twice at different moments and neither version was retired. Individually each duplication is survivable; collectively they create a schema where the same business question — "what is happening to this document?" — has three defensible answers. That is why the queue finding ranks first: the queues sit on the AI pipeline's critical path, and `customer_documents` carrying two queue foreign keys proves the overlap is live, not vestigial. Crucially, the ADRs appear to bless the multi-phase pipeline and the per-domain log design, so the remedy is governance — a written data-flow contract, deprecation of the strictly weaker duplicates (`pending_invites`, one delivery table), and read-only unifying views — rather than consolidation. Section 3.5 disposes each case.

### 3.3 Business Rules Enforceability

The schema records business state generously but enforces almost none of it. `organizations` has no `is_active`, `status` or `archived_at`, although nearly every child table (`suppliers`, `facilities`, `assets`, `organization_members`) carries `is_active` — a churned customer cannot be suspended without deleting audit evidence. Soft-delete is asymmetric: `organization_files` has `deleted_at` and `messages` a full soft-delete set, but `customer_documents`, the primary AI-pipeline entity, has neither. Duplicates are unblocked at the exact points the AI pipeline amplifies them: no unique constraint on `suppliers(organization_id, name/vat_number/company_number)`, `consultant_clients(consultant_id, organization_id)` or `organization_members(organization_id, user_id)`, so `ai_mapped_supplier_id` will happily propagate a duplicate supplier into emissions data. No file-bearing table (`organization_files`, `customer_documents`, `file_attachments`) carries a `file_checksum`, so duplicate uploads and invoices are undetectable. Approval state is scattered across `organization_files.status`, `customer_verifications.status`, `approval_requests`/`approval_decisions` and `customer_approved` flags on two queue tables — five tables can disagree about whether a document is approved. Finally, fiscal-year misalignment is a silent-corruption risk: nothing ties `emissions_logs.start_date`/`end_date` to `organizations.financial_year_end` or `organization_metadata.fiscal_year_start`/`fiscal_year_end` (themselves duplicated), so out-of-period emissions enter SECR totals unchallenged. All fixes are additive uniques, CHECKs and columns; none touches an ADR.

### 3.4 Search & Reporting Readiness

**Search is not production-ready.** No `pg_trgm` trigram or full-text indexing exists on the columns customers will actually search — `organizations.name`, `suppliers.name`/`vat_number`, `facilities.name`, `customer_documents.file_name`, `users.email` — and no composite index serves the tenant-scoped list views (`(organization_id, status)`, `(organization_id, created_at)`). Extracted invoice numbers live only inside `customer_documents.extracted_data` jsonb, so "find invoice INV-2024-001" is a full-table scan of payloads. Free-text `status` across ~25 tables defeats faceted filtering through case drift alone. **SECR reporting is feasible without redesign** — the reporting spine plus `organization_metadata` denominators (revenue, employees, floor area) cover the intensity-ratio and versioning requirements, and `defra_conversion_factors.reporting_year` supports prior-year comparatives — but it is blocked in practice by the unit/scope/factor gaps of Section 1 (unit-less `emissions_logs.raw_quantity`, unit-less `co2e_multiplier`, int4 `report_generation_queue.reporting_year` unable to name a non-calendar financial year) and by the absence of an Irish factor set. CarbonTally can today produce a beautifully versioned SECR-shaped report containing indefensible numbers.

### 3.5 Redundancy Disposition Table

| Duplicate concept | Disposition | Version | Notes |
|---|---|---|---|
| Three processing queues | **Keep all three**; write a data-flow contract naming the owning queue per lifecycle stage; add cross-queue FK assertions | Contract v1.1; rationalisation v2.0 at earliest | Full merge **NOT RECOMMENDED** — conflicts with the approved multi-phase pipeline ADR |
| 9+ audit/activity log tables | **Keep**; freeze taxonomy, document the authoritative log per domain, build one read-only unified view for support/audit search | View v1.1 | Consolidation **NOT RECOMMENDED** — per-domain log design is ADR-protected |
| `pending_invites` vs `user_invitations` | **Deprecate `pending_invites`** (strict subset: no token, expiry or status) | v1.0/v1.1 | Security downgrade as well as duplication |
| `notification_delivery` vs `notification_delivery_log` | **Deprecate one**; identical column sets | v1.0 | Cheapest redundancy fix in the schema |
| Review-history tables (`customer_review_log`, `review_audit_trail`, `review_assignment_history`) | **Deprecate one** of the two assignment-history tables | v1.1 | `review_audit_trail` and `review_assignment_history` record the same events |
| `users` / `staff_profiles` / `consultant_profiles` | **Keep** profile-per-role; identity fields only in `users`; 1:1 FK uniqueness on profiles | v1.1 | Merging identity tables **NOT RECOMMENDED** — ADR conflict |
| `customer_communication` vs conversations/messages | **Keep one channel** — the conversations estate; retire `customer_communication` writes | v1.1 | Read-state: anoint `conversation_participants.last_read_at` canonical, derive the other three mechanisms |
| QC columns vs `qc_checks`/`qc_checklists`/`qc_errors` | **Keep both** (ADR); document which paradigm governs per stage | v1.1 documentation; rationalisation v2.0 | Column-to-table QC merge **NOT RECOMMENDED** in v1.x |
| `uuid[]` arrays (`read_by`, `client_access`) vs junction tables | **Keep arrays**; GIN indexes plus app-level membership hygiene | v1.1 | Junction-table replacement **NOT RECOMMENDED** — ADR conflict |

The dispositions share one logic: where duplication is vestigial and strictly weaker (`pending_invites`, the twin delivery log), deprecate cheaply and early; where it reflects an approved architectural decision (queues, logs, profiles, arrays, QC paradigms), govern rather than merge — written contracts, canonical-source declarations and unifying views deliver most of the coherence benefit at none of the ADR risk. The unified audit view is the highest-value single item: it gives support staff, auditors and the in-app timeline one queryable story per document while leaving every underlying table untouched, and it converts the 9-table log estate from a liability into defensible breadth. Two items are deliberately *not* recommended anywhere in v1.x — queue consolidation and log consolidation — and that restraint is itself a finding: the schema's coherence debt is real, but the correct creditor payment schedule runs through documentation, deprecation and views, not through the redesign the ADRs rightly forbid.
