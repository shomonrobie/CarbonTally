## Section 2 — Column Review

*Every table and every column in the schema dump (`database.txt`) has been reviewed. Coverage: **100 tables**, grouped into 14 schema areas below. Verdict vocabulary: KEEP / RENAME / REMOVE / MERGE / SPLIT / NORMALIZE. Tables that are entirely KEEP are presented as a single compact row; any table containing a non-KEEP verdict is enumerated column by column. Verdicts are consistent with the frozen Structural Change Review (renames R1–R3, columns C1–C10 approved; C11 typed invoice columns, T3 county lookup and the jsonb ADRs remain rejected/deferred and are not resurrected here). Approved new columns (C1–C10) are shown as KEEP rows marked "(approved add)". Timing is stated on every non-KEEP verdict.*

### 2.1 Organisations & membership (6 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `organizations` | `id`, `name`, `company_number`, `created_at`, `updated_at`, `logo_url`, `industry`, `sector`, `company_size`, `vat_number`, `registration_number`, `country`, `timezone`, `currency`, `financial_year_end`, `reporting_standard`, `secr_enabled`, `esrs_enabled`, `issb_enabled`, `preferred_units`, `website`, `primary_contact_email`, `primary_contact_name`, `billing_contact_email`, `billing_contact_name`, `subscription_status`, `trial_start_date`, `trial_end_date`, `subscription_tier`, `subscription_id`, `billing_address`, `tax_rate`, `metadata`, `address_line1`, `address_line2`, `city`, `county`, `postcode`, `eircode`, `language`, `locale`, `vat_registered`, `registration_region`, `sic_code`, `naics_code`, `nace_code`, `business_structure`, `is_public`, `is_listed`, `isin`, `cik`, `sedol`, `lei`, `reporting_frequency`, `accounting_standard`, `sustainability_standard`, `carbon_tax_region`, `data_protection_officer`, `privacy_policy_url`, `terms_url` | KEEP | Core tenant record; GB/IE identifiers already dual-carried (`postcode`/`eircode`, `sic_code`/`nace_code`). |
| `organizations` | `default_defra_version` | RENAME | Approved **R3**: → `default_factor_year`. Jurisdiction-specific `defra` prefix on the one org setting an Irish beta tenant reads on day one; platform-level `system_settings.default_emission_factor_year` already uses neutral naming, so the old name is also internally inconsistent. RC2. |
| `organizations` | `registered_address` | MERGE | Free-text duplicate of the structured `address_line1`/`address_line2`/`city`/`county`/`postcode`/`eircode` block on the same row — two sources of truth for one fact. Fold into the structured columns; retire in v1.0.x. |
| `organizations` | `vat_region` | MERGE | Duplicates `tax_region` semantics (a fourth region column alongside `tax_region`, `registration_region`, `carbon_tax_region`). Fold into `tax_region`; retire in v1.0.x. |
| `organizations` | `tax_region` | KEEP | Canonical tax-jurisdiction column (merge target). |
| `organizations` | `is_active`, `archived_at` | KEEP (approved add C2) | Tenant lifecycle / evidence-preserving suspend path. |
| `organization_members` | — all columns | KEEP | Minimal membership join; `role` gains its K4 value-list CHECK (constraint, not a column change). |
| `organization_metadata` | `id`, `organization_id`, `total_employees`, `full_time_employees`, `part_time_employees`, `contract_employees`, `average_employees`, `annual_revenue`, `ebitda`, `total_assets`, `total_facilities`, `renewable_energy_percentage`, `carbon_offset_percentage`, `energy_intensity`, `reporting_standard`, `fiscal_year_start`, `fiscal_year_end`, `primary_contact_*`, `sustainability_officer_*`, `industry_sector`, `naics_code`, `sic_code`, `custom_metrics`, `created_at`, `updated_at`, `updated_by` | KEEP | One-to-one extension table correctly keeps the wide/org-profile payload off the hot `organizations` row. |
| `organization_metadata` | `total_floor_area_sqft`, `occupied_floor_area_sqft` | KEEP | Retained during transition; m² twins arrive via C10; sqft deprecation is v1.1 data/app work, not a column removal now. |
| `organization_metadata` | `total_floor_area_sqm`, `occupied_floor_area_sqm` | KEEP (approved add C10) | Prevents Irish beta users entering m² into sqft-labelled columns (~10.8× intensity error). |
| `roles` | — all columns | KEEP | Reference table; `permissions` jsonb per frozen ADR. |
| `pending_invites` | (table) `id`, `organization_id`, `email`, `role`, `created_at`, `updated_at` | MERGE | Duplicate of `user_invitations` (which is a strict superset: `token`, `status`, `expires_at`, `invited_by`, `role_id`). Merge target `user_invitations`; port `role` text into `role_id` resolution at the app layer. Timing: v1.0.x — pre-launch both tables are seed-scale, but two invite write paths must not reach production. |
| `user_invitations` | — all columns | KEEP | Canonical invitation table (merge target for `pending_invites`). |

### 2.2 Users, auth & beta (6 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `users` | — all columns | KEEP | Mirrors Supabase Auth; `password_hash` stays nullable and is never written (frozen C14 decision — platform owns credentials/2FA; no per-user auth columns are added). |
| `password_reset_tokens` | — all columns | KEEP | Column set correct; **K6** drops the UNIQUE on `user_id` (reset-DoS fix) — a constraint change, not a column verdict. |
| `beta_users` | — all columns | KEEP | Beta-gate table; whole-table retirement scheduled post-GA (v1.1 data purge) — no column change now. |
| `beta_access_codes` | — all columns | KEEP | As above; `magic_token`/`token_created_at` support the beta magic-link flow. |
| `waitlist` | — all columns | KEEP | Marketing capture; purged at GA (table-level decision, per I6 rationale). |
| `user_presence` | — all columns | KEEP | Ephemeral presence state; correctly minimal. |

### 2.3 Facilities & assets (2 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `facilities` | `id`, `organization_id`, `name`, `created_at`, `is_active`, `metadata`, `latitude`, `longitude`, `type`, `address_line1`, `address_line2`, `city`, `county`, `country`, `region`, `updated_at` | KEEP | `county` stays free text (frozen T3 rejection — no county lookup). `region` is a display-level free-text field here (distinct from the factor-table `region` retired under R1/C4). |
| `facilities` | `postcode` | KEEP | NOT NULL relaxed to nullable under **C1** (constraint change); Ireland has no postcodes. |
| `facilities` | `eircode` | KEEP (approved add C1) | Unblocks the Irish beta write path; presence CHECK guarantees postcode-or-eircode. |
| `facilities` | `meter_mpan_mprn` | KEEP (approved add C9) | Bill-to-site matching identifier; serves GB (MPAN/MPRN) and IE (MPRN). |
| `assets` | — all columns | KEEP | Correct child of `facilities`; `capacity`/`capacity_unit` pair is self-describing. |

### 2.4 Emissions, factors & activity reference (4 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `defra_conversion_factors` | (table) | RENAME | Approved **R1**: → `emission_factors`. The name hard-codes one national factor authority (UK DEFRA/DESNZ) into the platform's factor store; a rename on a live factor-referenced table is exactly what the "no major redesign in v1.1" rule exists to pre-empt, and pre-launch is the only cheap moment. RC2. |
| `defra_conversion_factors` | `id`, `reporting_year`, `activity_type`, `co2e_multiplier`, `created_at`, `updated_at` | KEEP | `co2e_multiplier` gains its K3 ≥ 0 CHECK and K5 uniqueness on `(reporting_year, activity_type, country)` — constraint work, no column change. (The doubled `updated_at` line in the dump is a dump artefact, per the structural review.) |
| `defra_conversion_factors` | `region` | RENAME (retire) | → `region_deprecated`. Half-does what C4's `country` does properly; values are mapped into `country` during the C4 backfill and the column is then retired, keeping a single jurisdiction column (single-source-of-truth stance, structural review §R1/§C4). RC2 rename; physical drop in v1.0.x once the backfill is verified. |
| `defra_conversion_factors` | `unit`, `scope`, `factor_source`, `factor_set`, `country` | KEEP (approved add C4) | Provenance + jurisdiction enabler: v1.1 Ireland becomes a data load (`country='IE'` SEAI/EPA rows), not a migration. |
| `emissions_logs` | `id`, `organization_id`, `asset_id`, `start_date`, `end_date`, `raw_quantity`, `calculated_kg_co2e`, `created_by_user_id`, `created_at`, `metadata`, `file_id`, `updated_at`, `customer_document_id`, `organization_member_id`, `supplier_id`, `product_category_id`, `data_source`, `confidence_score`, `verified_by`, `verified_at`, `updated_by` | KEEP | Core ledger; C12 (`facility_id`) stays DEFERRED to v1.1 — no denormalised copy in v1.0. |
| `emissions_logs` | `defra_factor_id` | RENAME | Approved **R2**: → `emission_factor_id`. Renaming the factor table (R1) while leaving its referencing columns named `defra_*` would freeze a permanent lie into the hottest factor-consuming table; renaming after a year of tenant data is materially harder. RC2. |
| `emissions_logs` | `unit`, `scope` | KEEP (approved add C5) | Self-describing quantities; SECR kWh totals and scope rollups without the factor join; `unit` FK'd to `units.code`. |
| `activity_categories` | — all columns | KEEP | Reference mapping across GHG Protocol / ESRS E1 / ISSB — deliberately multi-standard. |
| `units` | — all columns | KEEP | Reference table; now also the FK target for `emissions_logs.unit` (C5). |

### 2.5 Documents & uploads (11 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `customer_documents` | — all columns | KEEP | Primary pipeline entity. `extracted_data`/`mapped_data` jsonb stay (frozen ADR; C11 typed invoice columns remain DEFERRED). `file_checksum` (approved add **C6**) lands for duplicate detection. C13 `deleted_at` stays DEFERRED to v1.0.x. Polymorphic-style `file_id` naming noted in §5 register; no change. |
| `customer_verifications` | — all columns | KEEP | Full verification state machine (`submitted_*`/`verified_*`/`rejected_*`/`revision_*`/escalation) is coherent and in use. |
| `customer_review_log` | — all columns | KEEP | Review event log; `file_id` naming noted in §5. |
| `document_activity_log` | — all columns | KEEP | Per-document audit feed. |
| `document_types` | — all columns | KEEP | Reference + per-type requirements flags; consistent with `document_type_categories`. |
| `document_type_categories` | `id`, `code`, `name`, `description`, `category_group`, `default_priority`, `requires_facility`, `requires_asset`, `requires_supplier`, `requires_date_range`, `default_scope`, `is_active`, `is_system`, `created_at`, `updated_at` | KEEP | |
| `document_type_categories` | `default_defra_activity_type` | KEEP | Carries a `defra_` prefix but is **not** in the approved R1–R3 set; a further rename does not clear the "materially improve" bar pre-launch (churn breaks seed/app references). Recorded as a v1.1 rename candidate in the §5 violations register. |
| `organization_files` | — all columns | KEEP | General file store with review lifecycle timestamps; distinct responsibility from `customer_documents`. |
| `file_attachments` | — all columns | KEEP | `file_size` widened int4→int8 under approved **C7** (type change, not a column verdict change). |
| `upload_batches` | — all columns | KEEP | Batch orchestration; `created_by_user_id`/`created_by` pair is legacy overlap but both are read by live code — consolidation logged as v1.1 tidy-up, not a v1.0 verdict. |
| `draft_entries` | — all columns | KEEP | Autosave drafts; jsonb `data` per ADR. |
| `export_history` | — all columns | KEEP | Export audit trail with expiry; `filters` jsonb per ADR. |

### 2.6 Processing queues & review workflow (14 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `document_processing_queue` | `id`, `organization_id`, `customer_document_id`, `processing_type`, `status`, `file_name`, `file_url`, `file_size_bytes`, `file_type`, `page_count`, `ai_*` (12 columns), `manual_*` (8 columns), `qc_*` (5 columns), `customer_*` (5 columns), `calculated_emissions_kg_co2e`, `emission_calculation_method`, `batch_id`, `batch_sequence`, `processing_cost`, `billing_currency`, `created_at`, `created_by`, `updated_at`, `updated_by`, `completed_at`, `metadata` | KEEP | Single processing-queue direction is a frozen ADR; the wide stage-prefixed column groups (`ai_`, `manual_`, `qc_`, `customer_`) are the deliberate alternative to split stage tables. |
| `document_processing_queue` | `defra_factor_used` | RENAME | Approved **R2**: → `emission_factor_used`. Companion to R1; the pipeline's audit record of which factor was applied must not carry a jurisdiction-specific name into the IE era. RC2. |
| `manual_extraction_items` | `batch_id`, `document_processing_queue_id`, `file_name`, `file_url`, `page_count`, `document_type`, `status`, `extracted_data`, `mapped_data`, `mapped_facility_id`, `mapped_asset_id`, `mapped_supplier_id`, `calculated_emissions_kg_co2e`, `extracted_by`, `extracted_at`, `qc_by`, `qc_at`, `qc_notes`, `quality_score`, `customer_reviewed_by`, `customer_reviewed_at`, `customer_approved`, `customer_rejection_reason`, `customer_notes`, `created_at`, `updated_at` | KEEP | |
| `manual_extraction_items` | `defra_factor_used` | RENAME | **R2 companion**: → `emission_factor_used`. Same factor-reference semantics as `document_processing_queue.defra_factor_used`; leaving it behind would strand one `defra_*` name on the manual path the R2 rename was designed to clean up. RC2, rides the R2 migration. |
| `processing_queue` | — all columns | KEEP | Staff-facing queue; `queue_status` gains K4 value list (constraint). |
| `processing_assignments` | — all columns | KEEP | |
| `processing_steps` | — all columns | KEEP | |
| `processing_time_log` | — all columns | KEEP | |
| `processing_logs` | — all columns | KEEP | Step-level telemetry; `duration_ms` naming consistent with other `*_ms` columns. |
| `processing_audit_trail` | — all columns | KEEP | |
| `manual_review_queue` | — all columns | KEEP | SLA/escalation column set is the committed ops surface. |
| `manual_extraction_batches` | — all columns | KEEP | `currency` present (K2 set); consistent QC/SLA shape with peers. |
| `review_assignment_history` | — all columns | KEEP | |
| `review_audit_trail` | — all columns | KEEP | |
| `verification_logs` | — all columns | KEEP | |
| `reassignment_history` | — all columns | KEEP | |

### 2.7 Suppliers & categories (3 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `suppliers` | `id`, `organization_id`, `name`, `supplier_category_id`, `website`, `registration_number`, `annual_emissions_scope1/2/3`, `reporting_year`, `emission_factor_scope1/2/3`, `emission_factor_unit`, `is_active`, `created_at`, `created_by`, `updated_at`, `updated_by`, `metadata`, `address_line1`, `address_line2`, `city`, `county`, `postcode`, `country`, `eircode`, `tax_region`, `tax_rate`, `vat_number`, `company_number`, `registration_region`, `supplier_rating`, `is_certified`, `certification_type`, `certification_expiry`, `contract_start`, `contract_end`, `payment_terms`, `payment_currency`, `bank_name`, `bank_account`, `iban`, `swift_code`, `risk_score`, `compliance_status` | KEEP | Scoped emissions/factor sets are the canonical shape (K3 ranges apply). |
| `suppliers` | `type` / `supplier_type` | MERGE | Duplicate pair for one concept. Keep `supplier_type` (unambiguous beside `product_categories.category_type`), fold `type` values in, retire `type`. Timing: v1.0.x. |
| `suppliers` | `contact_name` / `contact_email` / `contact_phone` vs `primary_contact` / `primary_email` / `primary_phone` | MERGE | Two parallel contact triples on one row. Keep the `contact_*` triple (clearer, matches `organizations.primary_contact_*` convention inversely — `primary_` here is the legacy add), fold `primary_*` values across, retire. Timing: v1.0.x. |
| `suppliers` | `annual_emissions`, `emission_factor` | MERGE | Unscoped legacy duplicates of the per-scope columns (`annual_emissions_scope1/2/3`, `emission_factor_scope1/2/3`); an aggregate and a single-factor value kept in parallel invite drift. Fold into the scoped set (aggregate computed at read time). Timing: v1.0.x. |
| `suppliers` | `address` | MERGE | Free-text duplicate of the structured address block on the same row (same defect as `organizations.registered_address`). Fold into structured columns; retire in v1.0.x. |
| `suppliers` | `sort_code` | KEEP (approved add C8) | Completes UK domestic banking capture alongside existing `iban` (IE). |
| `supplier_categories` | — all columns | KEEP | `default_emission_factor`/`_unit` pair self-describing; K3 range applies. |
| `product_categories` | — all columns | KEEP | Per-org category mapping with multi-standard labels; consistent with `activity_categories`. |

### 2.8 Billing & subscriptions (3 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `customer_subscriptions` | — all columns | KEEP | Limits/usage/Stripe triple is complete; `currency` in the K2 set. |
| `consultant_billing` | — all columns | KEEP | Gains `currency` (approved add **C3**) — the only billing table previously undenominated. |
| `usage_tracking` | — all columns | KEEP | Counters covered by K3/K5 (non-negative; UNIQUE on `(organization_id, usage_month)`). |

### 2.9 Messaging & notifications (13 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `conversations` | — all columns | KEEP | `read_by`/`unread_count`/`participant_count` are denormalised read-model caches maintained by triggers — accepted, not re-normalised pre-launch. |
| `conversation_participants` | — all columns | KEEP | |
| `messages` | — all columns | KEEP | `is_read`/`read_at` alongside `read_by`/`read_count`/`last_read_at` serves 1:1 and group read-state respectively; consolidation is v1.1 evidence-gated, not a v1.0 verdict. |
| `message_activity_log` | — all columns | KEEP | |
| `conversation_activity_log` | — all columns | KEEP | |
| `typing_status` | — all columns | KEEP | Ephemeral UI state. |
| `customer_communication` | — all columns | KEEP | Staff→customer comms log; singular name noted in §5 (accept-with-reason). |
| `notifications` | — all columns | KEEP | Polymorphic `recipient_type`/`recipient_id` is the committed design. |
| `notification_templates` | — all columns | KEEP | |
| `notification_delivery` | (table) `id`, `notification_id`, `channel`, `status`, `sent_at`, `delivered_at`, `opened_at`, `error_message`, `metadata`, `created_at`, `updated_at` | MERGE | Near-duplicate of `notification_delivery_log` (same channel/status/timestamp payload; the `_log` twin adds `user_id`). One delivery-write path must survive. Merge target `notification_delivery_log` (superset); retire this table. Timing: v1.0.x, per prior triage deferral. |
| `notification_delivery_log` | — all columns | KEEP | Canonical delivery log (merge target). |
| `email_templates` | — all columns | KEEP | Overlaps `notification_templates` only superficially (channel-specific rendering); no merge. |
| `email_logs` | — all columns | KEEP | |

### 2.10 Consultant portal (4 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `consultant_profiles` | — all columns | KEEP | White-label branding + partner programme columns committed for launch; `eircode`/`postcode` dual-carried per K1. |
| `consultant_clients` | — all columns | KEEP | K5 UNIQUE on `(consultant_id, organization_id)` applies (constraint). |
| `consultant_firm_members` | — all columns | KEEP | `client_access` uuid array is ADR-locked (I4 GIN index approved); no junction-table normalisation. |
| `consultant_tasks` | — all columns | KEEP | `task_title`/`task_description` prefixed names acceptable (disambiguate against `internal_tasks`); noted in §5. |

### 2.11 Staff, admin & QC (20 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `staff_roles` | — all columns | KEEP | |
| `staff_profiles` | — all columns | KEEP | |
| `staff_workload` | — all columns | KEEP | Live workload snapshot; overlaps `staff_daily_performance` conceptually — consolidation noted as **v1.1 NORMALIZE candidate** (snapshot vs daily-rollup split is defensible today; no v1.0 action). |
| `staff_performance` | — all columns | KEEP | Period rollup; complements `staff_daily_performance`. |
| `staff_daily_performance` | — all columns | KEEP | |
| `team_performance` | — all columns | KEEP | |
| `staff_activity_log` | — all columns | KEEP | |
| `login_history` | — all columns | KEEP | |
| `internal_tasks` | — all columns | KEEP | |
| `task_assignments` | — all columns | KEEP | |
| `qc_checks` | — all columns | KEEP | |
| `qc_checklists` | — all columns | KEEP | `checklist_items` jsonb per ADR. |
| `qc_errors` | — all columns | KEEP | |
| `approval_requests` | — all columns | KEEP | |
| `approval_decisions` | — all columns | KEEP | |
| `sla_compliance` | — all columns | KEEP | |
| `sla_definitions` | — all columns | KEEP | |
| `business_hours` | — all columns | KEEP | |
| `queue_settings` | — all columns | KEEP | Key-value store; deliberately separate from `system_settings` (worker ops vs platform config). |
| `verification_activity_log` | — all columns | KEEP | |

### 2.12 Audit & activity logs (5 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `audit_logs` | `id`, `user_id`, `staff_id`, `organization_member_id`, `organization_id`, `resource_type`, `resource_id`, `description`, `ip_address`, `user_agent`, `old_data`, `new_data`, `changes`, `metadata`, `created_at` | KEEP | |
| `audit_logs` | `action_type` / `action` | MERGE | Two columns carrying the same event verb (both effectively required by the dump) — every writer must currently dual-write. Keep `action_type` (aligns with `audit_trail.action_type` and the `*_activity_log.action_type` family), fold `action` values in, retire. Timing: v1.0.x. |
| `audit_trail` | — all columns | KEEP | Trigger-maintained row-version trail; distinct responsibility from `audit_logs` (business events). Naming overlap with `audit_logs` noted in §5 (accept-with-reason). |
| `activity_logs` | — all columns | KEEP | User-facing activity; `metadata` + `details` jsonb both retained (different producers). |
| `activity_feed` | — all columns | KEEP | Read-model feed; `event_data` jsonb per ADR. |
| `user_activity_log` | — all columns | KEEP | Per-user security activity; distinct from org-scoped `activity_logs`. |

### 2.13 Reports & AI content (5 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `report_templates` | — all columns | KEEP | `template_structure`/`ai_prompts` jsonb per ADR. |
| `report_generation_queue` | — all columns | KEEP | AI cost telemetry (`ai_model_used`, `ai_tokens_used`, `ai_cost`) is the committed FinOps surface. |
| `report_versions` | — all columns | KEEP | K5 UNIQUE `(report_id, version_number)` applies. |
| `report_comments` | — all columns | KEEP | |
| `ai_content_history` | — all columns | KEEP | |

### 2.14 Reference, settings & misc (4 tables)

| Table | Column | Verdict | Why |
|-------|--------|---------|-----|
| `glossary` | — all columns | KEEP | Seed/reference content. |
| `system_settings` | `id`, `setting_key`, `setting_value`, `setting_type`, `description`, `is_editable`, `updated_by`, `updated_at`, `created_at`, and all typed `default_*` / `sla_*` / `max_*` / `api_*` / `webhook_*` / `session_*` / `two_factor_*` / `password_*` / `login_*` / `*_retention_*` / `backup_*` columns | KEEP | Hybrid key-value + typed-column settings row; global `two_factor_*` flags stay as marketing/config only until platform MFA ships (frozen C14). |
| `system_settings` | `default_vat_rate` | MERGE | Exact duplicate of `default_tax_rate` on the same row (UK calls it VAT, IE calls it VAT too — one concept, one column). Keep `default_tax_rate` (jurisdiction-neutral), fold value across, retire. Timing: v1.0 — trivial, pre-launch, and removes a which-one-wins ambiguity before billing code hardens against it. |
| `dashboard_metrics` | — all columns | KEEP | Cache table with `expires_at`; correct shape. |
| `user_feedback` | — all columns | KEEP | |

**Coverage statement:** 100 tables in the dump; 100 appear above across 14 areas. **Verdict counts:** KEEP 91 tables (incl. compact rows; all ~1,150 columns not otherwise listed below); **RENAME 6** (R1 table rename; `region`→`region_deprecated` retire; R2 ×2 approved + 1 R2 companion on `manual_extraction_items`; R3 ×1); **MERGE 10** (`pending_invites`→`user_invitations`; `notification_delivery`→`notification_delivery_log`; `system_settings.default_vat_rate`→`default_tax_rate`; `organizations.registered_address` and `vat_region`; `suppliers` `type`, `primary_contact/_email/_phone`, `annual_emissions`+`emission_factor`, `address`; `audit_logs.action`→`action_type`); **REMOVE 0 columns** (no provably dead column exists pre-launch; table-level retirements — `waitlist`, `beta_users`, `beta_access_codes` post-GA — are data/lifecycle decisions, not RC2 column verdicts); **SPLIT 0**; **NORMALIZE 0 in v1.0** — two explicit v1.1 candidates noted (`staff_workload`/`staff_daily_performance` consolidation; remaining ~20 free-text status columns per K4's deferred tail). Typed invoice columns (C11), county lookup (T3) and the jsonb promotion freeze are not resurrected.

## Section 5 — Naming Standard

### 5(a) The standard — ten rules

1. **snake_case everywhere, lower-case only.** Tables, columns, constraints. No exceptions in the schema; this codifies existing practice (`organization_members`, `calculated_emissions_kg_co2e`).
2. **Plural nouns for entity tables** (`organizations`, `suppliers`, `facilities`, `emissions_logs`). Singular/mass-noun names are permitted only for genuine singleton or state resources (`user_presence`, `typing_status`, `glossary`, `waitlist`) and for `_settings` stores.
3. **Suffix conventions are semantic, not decorative.** `_log`/`_logs` = append-only event history (`audit_logs`, `email_logs`); `_trail` = row-version history (`audit_trail`, `processing_audit_trail`); `_queue` = claimable work (`processing_queue`, `document_processing_queue`); `_queue` never doubles as a log; `_templates`, `_definitions`, `_categories`, `_settings` for reference/config; `_history` for immutable transition records (`reassignment_history`, `login_history`).
4. **Jurisdiction-neutral names for anything cross-border.** No national authority, registry or scheme in an identifier unless the column is definitionally jurisdiction-bound. Hence `emission_factors` (not `defra_conversion_factors`), `emission_factor_id`, `default_factor_year`, `country` carrying `('GB','IE')` per K1. Jurisdiction-bound identifiers are named for what they are: `eircode`, `postcode`, `sort_code`, `iban`, `company_number`.
5. **Foreign keys are `<referenced_singular>_id`** (`organization_id`, `customer_document_id`, `emission_factor_id`). Actor columns use role-prefixed forms (`assigned_to`/`assigned_by`, `verified_by`, `created_by`/`updated_by`). Polymorphic references must be named by the pair, e.g. `recipient_type` + `recipient_id` (`notifications`).
6. **Timestamps are `<event>_at` (`timestamptz`); dates are `<event>_date` (`date`); durations carry their unit** (`duration_ms`, `review_time_seconds`, `sla_default_hours`). Booleans are `is_*`/`has_*`/`can_*` or a `<verb>ed`/`required` predicate (`is_active`, `has_attachments`, `can_manage_clients`, `qc_required`, `email_verified`).
7. **Measurements carry their unit in the name** (`calculated_emissions_kg_co2e`, `total_floor_area_sqft`/`_sqm`, `file_size_bytes`, `max_upload_size_mb`) or reference `units.code` (`emissions_logs.unit`, C5). Bare numeric measures of money are only acceptable where a sibling `currency` column denominates them (`processing_cost` + `billing_currency`).
8. **No non-standard abbreviations.** Domain-standard acronyms are permitted and preferred over invention: `co2e`, `qc`, `sla`, `vat`, `ebitda`, `isin`, `lei`, `sedol`, `cik`, `mpan`/`mprn`, `ai` (as a stage prefix), `avg`. Banned class: ad-hoc truncations (`org`, `doc`, `addr`, `qty`) — none exist in the schema and none may be introduced.
9. **Stage/namespace prefixes group wide-table columns by lifecycle stage**, underscore-terminated and used consistently within the table: `ai_*`, `manual_*`, `qc_*`, `customer_*` on `document_processing_queue`; `default_*` on `system_settings`; `stripe_*` for third-party identifiers. A prefix, once chosen for a stage, is used by every column of that stage in every table (hence the `defra_*` retirements — a jurisdiction is not a stage).
10. **jsonb payload columns have fixed names**: `metadata` (opaque extension bag), `details`/`event_data` (log payloads), `extracted_data`/`mapped_data` (pipeline payloads), `old_data`/`new_data`/`changes` (audit diffs). New jsonb columns must reuse these names rather than coin synonyms.

### 5(b) Violations register

| Object | Violation | Verdict |
|--------|-----------|---------|
| `defra_conversion_factors` (table) | Rule 4 — jurisdiction-specific authority in a cross-border entity name | **Fix in RC2 (R1, approved)** → `emission_factors` |
| `emissions_logs.defra_factor_id` | Rules 4, 5 — jurisdiction prefix on an FK | **Fix in RC2 (R2, approved)** → `emission_factor_id` |
| `document_processing_queue.defra_factor_used` | Rules 4, 9 — jurisdiction prefix masquerading as stage prefix | **Fix in RC2 (R2, approved)** → `emission_factor_used` |
| `manual_extraction_items.defra_factor_used` | Same as above; R2 companion | **Fix in RC2** → `emission_factor_used` (same migration; stranding it would leave one `defra_*` reference behind) |
| `organizations.default_defra_version` | Rule 4 + internal inconsistency with `system_settings.default_emission_factor_year` | **Fix in RC2 (R3, approved)** → `default_factor_year` |
| `defra_conversion_factors.region` | Ambiguous jurisdiction-ish name superseded by C4 `country` | **Fix in RC2** → `region_deprecated` (retire; drop in v1.0.x after backfill verification) |
| `document_type_categories.default_defra_activity_type` | Rule 4 residue | **Fix in v1.1** → `default_activity_type`. Does not clear the "materially improve" bar pre-launch: it is a seed-lookup label, not a live FK path, and renaming churn breaks app/seed references for cosmetic gain. Scheduled with the v1.1 IE factor load so all factor-surface naming lands once. |
| `audit_trail` vs `audit_logs` | Near-synonymous pluralisation for different responsibilities | **Accept-with-reason** — both names are load-bearing in app code; the `_trail`/`_logs` distinction is documented in Rule 3 and is now the sanctioned convention. |
| `customer_communication` | Rule 2 — singular name on an entity table | **Accept-with-reason** — reads as a mass noun ("communication record"); rename churn not justified. Revisit only if a sibling comms table appears. |
| `customer_review_log.file_id`, `document_activity_log.file_id`, `draft_entries.file_id`, `emissions_logs.file_id` | Rule 5 — polymorphic FK named `file_id` rather than `<entity>_id` | **Accept-with-reason (v1.0); review v1.1** — the polymorphism is the real design question, not the name; renaming four hot columns pre-launch fails the materially-improve bar. |
| `consultant_tasks.task_title`/`task_description`, `internal_tasks.task_title`/`task_description` | Redundant `task_` prefix inside a `*_tasks` table | **Accept-with-reason** — disambiguates against joined task tables in reporting queries; harmless. |
| `organizations` (~65 columns) mixes `text` and `varchar` for like fields | Type inconsistency, not a naming violation | **Accept-with-reason** — types are out of scope for the naming standard; normalisation is a v1.1 type-hygiene pass, not a rename. |
| `upload_batches.created_by_user_id` vs `created_by` | Rule 5 — two actor columns, one concept | **Fix in v1.1** — merge into `created_by`; logged with the §2 tidy-up note. Not RC2: both are read by live code and the merge is behavioural, not cosmetic. |
| `messages` read-state trio (`is_read`/`read_at` vs `read_by`/`read_count`/`last_read_at`) | Rule 6-adjacent redundancy | **Accept-with-reason** — 1:1 vs group semantics; consolidation is evidence-gated for v1.1. |
| `waitlist`, `glossary`, `user_presence`, `typing_status` | Rule 2 — singular names | **Accept-with-reason** — sanctioned singleton/state exceptions under Rule 2. |
| `staff_workload.date`, `staff_daily_performance.date`, `team_performance.date` | `date` is a type name used as a column name | **Accept-with-reason** — unambiguous in context and widely referenced; renaming to `metric_date` is v1.1-optional, not required. |

### 5(c) Five-year future-proofing confirmation

This standard is durable for at least five years because its load-bearing names are jurisdiction-, vendor- and standard-neutral at exactly the points where the business will change. The factor surface — the schema's most jurisdiction-sensitive asset — is named `emission_factors` / `emission_factor_id` / `emission_factor_used` / `default_factor_year` with jurisdiction carried as *data* (`country IN ('GB','IE')`, `factor_source`, `factor_set`), so admitting SEAI/EPA in v1.1, or any further national factor authority thereafter, is a row load and an IN-list extension, never a rename. The same pattern holds for money (ISO `currency` codes constrained by K2, neutral `tax_rate`/`tax_region` rather than `vat_*` on forward-looking surfaces), for addresses (`postcode`/`eircode` duality generalises to any future `postal_code` abstraction without renaming history), and for reporting (`ghg_protocol_*`, `esrs_e1_category`, `issb_category` are additive label columns on reference tables, so a new disclosure standard is a new column on a small reference table, not a refactor). Rule 4's ban on embedding authorities in identifiers, Rule 7's unit-in-name discipline, and Rule 9's stage prefixes together mean that the schema's names describe *what things are* rather than *who issued them or which market launched first* — which is precisely the property a UK-primary-then-Ireland, then-wider-Europe product needs its database to have.

*Verification: §2 covers all 100 tables in the dump (stated and counted in §2); every non-KEEP verdict carries a Why and a timing; all verdicts are consistent with the frozen R1–R3 / C1–C10 approvals and the C11/T2/T3/ADR deferrals and rejections; no SQL appears in this document.*
