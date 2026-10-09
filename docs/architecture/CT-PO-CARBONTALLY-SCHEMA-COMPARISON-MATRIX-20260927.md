# CT-PO — Canonical Schema Comparison Matrix (CT-SCHEMA-01)

**Task ID:** `CT-SCHEMA-01-20260927-CANONICAL-SCHEMA-FROM-ZERO-VERIFICATION`
**Type:** READ-ONLY comparison. No database other than the new disposable target was mutated.
**Authority:** `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` (branch `p8-release-reconciled`).
**Canonical reference:** `CT-SCHEMA-01-TARGET-A` — 89/89 migrations applied to a brand-new disposable
database; 145 `public` tables; inventory fingerprint `c89c50bd27f1b5f571ae44989736963c1c55074e81bd23965e38676626233c2f`.
**Date:** 2026-09-27.

## 0. Method and safety

* Every pre-existing database was queried **read-only** (`information_schema`, `pg_catalog`,
  `pg_policies`, `pg_indexes`, `pg_constraint`, and `supabase_migrations` where it exists).
* **No** insert/update/delete/DDL was executed against any pre-existing database, and **no** database,
  container or volume belonging to a pre-existing environment was removed.
* Data volumes were **not** treated as an objective (task §13: data is regenerable, schema is truth).
  Row counts appear only where they explain schema provenance.
* The comparison unit is the **`public` table set** plus the named columns/objects cited by the FIEW
  register. Table-set equality is the strongest available signal of "same schema lineage".

## 1. Environments found (read-only enumeration)

| Group | Count | Members (examples) |
|---|---|---|
| Shared local Supabase cluster (`supabase_db_carbon_ledger`, PostgreSQL 17.6) | **78 databases** | — |
| — durable-named | 4 | `postgres` (flagship), `carbontally_demo_local`, `carbontally_qa_phase8`, `carbontally_test` |
| — disposable clones / scratch | **71** | `ct_p17k_20260926`, `ct_iv_p17m*`, `ct_i4_*`, `ct_d17d32_chain`, `ct_local_93d5cdd`, `ct_t2b_defra`, `ct_v069*`, … |
| — platform/internal | 3 | `_supabase`, `storage_vectors`, `postgres` |
| **This task's disposable target** | 1 cluster | `ct_schema01_pg` (`CT-SCHEMA-01-TARGET-A`), volume `ct_schema01_pgdata`, port 55450 |
| Host cluster (PostgreSQL 18, `127.0.0.1:5432`) | **not reachable read-only** | credential rejected; no mutation attempted (see §5 note 4) |

Data context (provenance only, not an objective): flagship `postgres` 975 organisations / 7 049
`emission_factors` / 116 `public` tables; `carbontally_demo_local` 4 organisations / 7 049 factors /
141 tables; the canonical rebuild 0 organisations / 0 factors / **145 tables**.

## 2. SCHEMA_DIFF_MATRIX

Classification key: `CANONICAL` (matches the from-zero schema) · `OUTDATED` (durable environment lagging
the canonical schema) · `EXTRA` (object not produced by the chain) · `MISSING` (canonical object absent
here) · `LEGACY` (pre-V3 object still referenced/present) · `DISPOSABLE_ONLY` (exists only in clones) ·
`UNKNOWN`.

| # | OBJECT | CANONICAL_FROM_ZERO | DB_INSTANCE | STATUS | SOURCE_MIGRATION | CODE_DEPENDENCY | INTERPRETATION |
|---|---|---|---|---|---|---|---|
| 1 | `public` table set | 145 | `postgres` (flagship) — **116** | **OUTDATED** | the 43 migrations after `20260903010000` | `data/evidence_line_items.py`, `data/insight.py`, `services/disclosure_*`, `services/scope3_calculation.py` | Flagship is 29 canonical tables behind; its ledger stops at `20260903010000` |
| 2 | `public` table set | 145 | `carbontally_demo_local` — **141** | **OUTDATED** | `p17c`, `p17d`, `p17h` (4 tables) | Scope 2/3 instrument + estimation services | Closest durable database to canonical (4 tables behind) |
| 3 | `public` table set | 145 | `carbontally_qa_phase8` — **133** | **OUTDATED** | 12 migrations' objects | Insight / disclosure / evidence services | QA environment predates I1/I4, B1–B4, FIN-06 |
| 4 | `public` table set | 145 | `carbontally_test` — **117** | **OUTDATED** | 28 migrations' objects | as above | Test database predates most of the P8/P16R/P17 line |
| 5 | `public` table set | 145 | `ct_p17k_20260926` (disposable) — **145** | **CANONICAL (identical)** | all 89, applied incrementally | all V3 modules | Independent corroboration: 0 missing, 0 extra vs the from-zero rebuild |
| 6 | `public` table set | 145 | `ct_d17d32_chain` — **0** | **DISPOSABLE_ONLY** (empty scratch) | none | none | Not a schema-bearing environment |
| 7 | `evidence_line_items`, 15 `disclosure_*`, `activity_clarifications`, `manual_processing_grants`, `report_version_artifacts`, 6 `insight_*`/`carbontally_insight_*`, `contractual_instruments`, `instrument_allocations`, `scope3_categories`, `estimation_records` | present | flagship | **MISSING** | 27 migrations | evidence/disclosure/Insight/P17 services | The core of the CT-FEATURE-02 `BLOCKED_BY_SCHEMA` condition |
| 8 | accounting/provenance columns (`facility_id`, `scope2_method`, `scope3_category`, `scope3_method`, `data_quality`, `energy_type`, `transaction_provider`, `transport_boundary`, `waste_origin`, `acting_for_organization_id`, `performed_by_organization_id`, `performed_by`, `source_snapshot_id`, `source_line_item_id`, `reportability_status`, factor-governance columns, org type/consolidation) | present (27/27 real) | flagship | **MISSING (0/27 probed)** | `p17a`, `p17_10`, `p16r5`, `p16r7`, `gate4`, `p8_b2` | `engines/calculation.py`, `services/scope2_calculation.py`, `services/scope3_calculation.py`, `data/accounting_context.py`, `domain/insight_quality.py` | Calculation provenance and P17 dimensions are not durable in the flagship |
| 9 | storage platform (`storage.objects`, `storage.buckets`, `storage.foldername()`, 4 D32 policies) | present (platform/operator provisioned) | flagship + `carbontally_demo_local` | **CANONICAL** | none (platform + operator step) | storage service, signed-URL endpoints | Same in every Supabase environment; required before migration 27 (SCM-001/003) |
| 10 | `conversation_participants_conv_user_idx` | absent (dropped) | flagship (absent) | **CANONICAL** | dropped by `20260828000000_v3m8` | messaging | Intentional supersession — not drift |
| 11 | `cc_insert_own_firm` policy | absent (dropped) | flagship (absent) | **CANONICAL** | dropped by `20260906090000_p6_1c` | consultant engagement | Intentional supersession |
| 12 | `defra_conversion_factors`, `report_history`, `report_schedules`, `notification_delivery_log` | **absent** | flagship, demo_local, qa_phase8 (all absent) | **MISSING everywhere / LEGACY code** | no migration creates them | `backend/utils/emissions.py`, `backend/routes/reports.py`, `backend/routes/admin/audit_logs.py` | Code drift, not schema drift (SCM-004…007) |
| 13 | `widgets`, `notes`, `secure_things`, `unlogged_demo`, `unlogged_only`, `identity_demo`, `events_a/b/c`, `widget_names` | absent | created transiently by integration fixtures | **TEST_HARNESS** | none | `backend/tests/integration/backup/test_exporter_local.py` | Fixtures must never target a durable database (SCM-009) |
| 14 | `supabase_migrations.schema_migrations` | absent (psql apply) | flagship: **46 rows** | **PROCESS GAP** | CLI-managed | ops tooling | Only the flagship has a ledger (SCM-010) |
| 15 | `ct_local_93d5cdd` | 145 | not reachable read-only | **UNKNOWN** | — | — | Comparison row missing (SCM-011) |
| 16 | `system_settings.operational_telemetry_retention_days` | present | flagship **absent**, demo_local present | **OUTDATED (flagship)** | `20260924000000_p8x_x2` | retention configuration | Durable only in the most advanced environments |
| 17 | `EXTRA` objects in canonical vs any durable DB | 0 | all four durable databases | **NONE** | — | — | Canonical is a strict **superset**: no durable database holds a table the chain does not create |
| 18 | `LEGACY`-named objects in flagship but not canonical | 0 | flagship | **NONE** | — | — | The flagship has no tables outside the canonical set; its gap is purely *missing* objects |

## 3. Canonical `public` table set (145 tables, in groups of five, SQL-verified)

```
activity_categories,activity_clarifications,activity_feed,activity_logs,ai_content_history
approval_decisions,approval_requests,assets,audit_logs,audit_trail
beta_access_codes,beta_users,billing_commercial_config,billing_credit_ledger,billing_idempotency_keys
billing_orders,billing_payment_records,billing_plans,billing_storage_usage,business_hours
calculation_snapshots,carbontally_insight_conversations,carbontally_insight_interactions,carbontally_insight_messages,carbontally_insight_tool_calls
consultant_billing,consultant_clients,consultant_custom_domains,consultant_firm_members,consultant_profiles
consultant_senders,consultant_tasks,contractual_instruments,conversation_activity_log,conversation_participants
conversations,customer_communication,customer_documents,customer_factors,customer_review_log
customer_subscriptions,customer_verifications,dashboard_metrics,data_discovery_requests,disclosure_applicability_assessments
disclosure_framework_versions,disclosure_frameworks,disclosure_intensity_denominator_framework_links,disclosure_intensity_denominator_types,disclosure_intensity_ratios
disclosure_narrative_entries,disclosure_purpose_requirements,disclosure_report_instance_binding,disclosure_report_purpose_versions,disclosure_report_purposes
disclosure_requirement_mappings,disclosure_requirement_versions,disclosure_value_evidence,disclosure_values,document_activity_log
document_processing_queue,document_type_categories,document_types,domain_events,draft_entries
email_logs,email_templates,emission_factors,emissions_logs,estimation_records
evidence_line_items,export_history,facilities,factor_aliases,file_attachments
glossary,import_batches,insight_concurrency_leases,insight_rate_limit_buckets,instrument_allocations
issues,login_history,manual_extraction_batches,manual_extraction_items,manual_processing_grants
manual_review_queue,message_activity_log,messages,notification_delivery,notification_templates
notifications,organization_files,organization_members,organization_metadata,organizations
password_reset_tokens,pending_invites,processing_assignments,processing_audit_trail,processing_entities
processing_logs,processing_queue,processing_steps,processing_time_log,product_categories
qc_checklists,qc_checks,qc_errors,queue_settings,reassignment_history
report_comments,report_generation_queue,report_templates,report_version_artifacts,report_versions
review_assignment_history,review_audit_trail,roles,scope3_categories,sla_compliance
sla_definitions,staff_activity_log,staff_daily_performance,staff_performance,staff_profiles
staff_roles,staff_workload,supplier_categories,suppliers,system_settings
team_performance,typing_status,units,upload_batches,usage_tracking
user_activity_log,user_feedback,user_invitations,user_presence,users
vehicles,verification_activity_log,verification_logs,waitlist,work_item_assignments
```

*(Exact set from `/tmp/cmp/canonical_public_tables.txt`, sorted; 29 lines × 5. Concepts explored during
verification that are **not** canonical tables — `accounting_dimensions`, `assumption_records`,
`processing_entity_staff`, `audit_activity`, `platform_settings` — are implemented as columns on
`calculation_snapshots`/`emissions_logs`, `estimation_records`, `processing_entities`, `audit_trail`,
`system_settings` respectively.)*

## 4. Domain object inventory verified in the canonical rebuild (§1 domains A–Q)

| Domain | Key canonical objects verified present |
|---|---|
| A Identity / auth | `organizations`, `organization_members`, `users`, `staff_profiles`, `staff_roles`, `roles`, `pending_invites`, `user_invitations`, `login_history`, `user_presence` |
| B Consultant | `consultant_profiles`, `consultant_clients`, `consultant_firm_members`, `consultant_custom_domains`, `consultant_senders`, `consultant_tasks`, `consultant_billing` |
| C Processing entity | `processing_entities`, `work_item_assignments`, `processing_assignments`, `processing_queue`, `processing_steps`, `processing_logs`, `processing_time_log`, `processing_audit_trail` |
| D Ingestion | `customer_documents`, `document_types`, `document_type_categories`, `document_processing_queue`, `document_activity_log`, `import_batches`, `upload_batches`, `manual_review_queue`, `manual_extraction_batches`, `manual_extraction_items`, `file_attachments` |
| E Factors | `emission_factors` (+ governance columns), `customer_factors`, `factor_aliases`, `glossary`, `units` |
| F Accounting | `calculation_snapshots`, `emissions_logs`, `facilities`, `assets`, `suppliers`, `supplier_categories`, `vehicles`, `business_hours`, `activity_categories`, `draft_entries`, `product_categories` |
| G Scope 2 | `contractual_instruments`, `instrument_allocations` (+ `p17_instrument_over_allocated()`, `scope2_method` CHECKs) |
| H Scope 3 | `scope3_categories` (15 rows), `estimation_records`, `activity_clarifications` (+ `scope3_category`, `scope3_method`, `transport_boundary`, `waste_origin` columns) |
| I Evidence | `evidence_line_items`, `disclosure_value_evidence` (+ `source_line_item_id` links, `uq_dve_reference_nullsafe`) |
| J QC / approval | `approval_requests`, `approval_decisions`, `qc_checks`, `qc_checklists`, `qc_errors`, `manual_processing_grants`, `issues`, `customer_review_log`, `review_audit_trail`, `review_assignment_history` |
| K Reporting | `report_versions`, `report_version_artifacts`, `report_comments`, `report_generation_queue`, `report_templates`, `reportability_status` columns, 15 `disclosure_*` tables (18 governed requirement rows) |
| L Insight | `carbontally_insight_conversations`/`_messages`/`_interactions`/`_tool_calls`, `insight_rate_limit_buckets`, `insight_concurrency_leases` |
| M Commercial | `billing_plans`, `customer_subscriptions`, `billing_commercial_config`, `billing_orders`, `billing_payment_records`, `billing_credit_ledger`, `billing_storage_usage`, `billing_idempotency_keys`, `usage_tracking` |
| N Notifications | `notifications`, `notification_templates`, `notification_delivery`, `email_templates`, `email_logs` (+ `consultant_senders` for sender configuration) |
| O Audit | `audit_trail`, `audit_logs`, `activity_logs`, `activity_feed`, `domain_events`, `staff_activity_log`, `user_activity_log`, `message_activity_log`, `document_activity_log`, `conversation_activity_log`, `verification_logs` (88 non-internal triggers enforce immutability/lifecycle) |
| P Security | 145/145 tables RLS-enabled, 227 policies, **0** policies granting `anon`/`public`, 1 646 grants to `anon`/`authenticated`/`service_role`/`public` |
| Q Admin / ops | `system_settings` (incl. `operational_telemetry_retention_days`), `queue_settings`, `dashboard_metrics`, `sla_definitions`, `sla_compliance`, `team_performance`, `staff_workload`, `staff_performance`, `staff_daily_performance`, `data_discovery_requests` |

## 5. Notes

1. **Canonical is a strict superset.** For all four durable databases the measured values were
   `missing = 29 / 4 / 12 / 28` and `extra = 0 / 0 / 0 / 0`. No durable database contains a table the
   chain does not produce, and every canonical object is absent from at least the flagship.
2. **The most advanced environment already matched the rebuild.** `ct_p17k_20260926` (disposable) equals
   the canonical table set exactly — strong evidence that the chain, applied from zero, reaches the
   intended release-tree schema rather than a different one.
3. **Data was not a decision driver.** The flagship holds 975 organisations and 7 049 factors on an
   *older* schema; `carbontally_demo_local` holds 4 organisations and the same 7 049 factors on a *newer*
   one. Neither fact changes the schema verdict. No data was migrated, merged or seeded.
4. **One environment could not be compared.** `ct_local_93d5cdd` is not in the shared cluster, and the
   host PostgreSQL 18 cluster rejected the read-only credential available to this task; its row is
   therefore `UNKNOWN` (SCM-011), and the prior claim about it is **not** re-verified here.
5. **Classification counts:** `OUTDATED` 4 (flagship, demo_local, qa_phase8, test) · `CANONICAL` 4
   (storage layer, two intentionally dropped objects, the P17K clone) · `MISSING` 2 matrix rows (many
   objects) · `DISPOSABLE_ONLY` 1 · `TEST_HARNESS` 1 · `PROCESS GAP` 1 · `UNKNOWN` 1 · `EXTRA` 0 ·
   `LEGACY` 0.

<!--CTEOF-->



