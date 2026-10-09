# CT-PO — Canonical Schema Feature Support Matrix (CT-SCHEMA-01)

**Task ID:** `CT-SCHEMA-01-20260927-CANONICAL-SCHEMA-FROM-ZERO-VERIFICATION`
**Type:** READ-ONLY matrix. No source, migration, database or production change.
**Authority:** `/home/shomonrobie/ct_93d5cdd` @ `cb70fd6bbbcf7f0d780a3624a1686cc7d6dbd8ea` (branch `p8-release-reconciled`).
**Canonical reference:** `CT-SCHEMA-01-TARGET-A` — disposable rebuild, 89/89 migrations, 145 `public` tables (see verification document).
**Date:** 2026-09-27.

## 0. Truth ladder and rules of this matrix

```
DOCUMENTED → CODE → MIGRATION → SCHEMA → ROUTE → AVAILABLE → PERSISTED → E2E → INDEPENDENTLY VERIFIED → PRODUCTION
```

**Rules applied (strictly):**

1. This task reached **`SCHEMA`** and nothing beyond it. A cell saying "canonical: present" means *an SQL
   query against the rebuilt database found the object* — not that any code path works.
2. **Schema existence ≠ wired functionality. Schema existence ≠ runtime success.** No row in this matrix
   is upgraded because a table exists.
3. Where the CT-FEATURE-02 register recorded `BLOCKED_BY_SCHEMA` / `DISPOSABLE_ENVIRONMENT_ONLY`, this
   matrix reports only whether **the schema blocker is removed**. All 57 rows remain
   **runtime-unverified** (`ROUTE` and beyond are `NOT VERIFIED`).
4. Every flagship/demo figure below was **re-measured by this task** (read-only SQL), not copied from a
   prior report.

---

## 1. FIEW impact summary per cluster

| Cluster | FIEW rows | Migrations | Required objects | Canonical rebuild | Flagship (`postgres`) | `carbontally_demo_local` | Schema blocker removed? | Runtime status |
|---|---|---|---|---|---|---|---|---|
| A — P17-A dimensions | FIEW-001 … 011 (11) | `20261010000000_p17a`, `20261014000000_p17_10` | 27 columns across `calculation_snapshots`, `emissions_logs`, `emission_factors`, `organizations` (+ constraints/indexes) | **26/26 real columns present** | **0/26** | **0/22** (only `reportability_status`/`source_line_item_id` present) | **YES for all 11** | unverified |
| A2 — P17-C/D/H objects | FIEW-012 … 017 (6) | `20261011000000_p17c`, `20261012000000_p17d`, `20261013000000_p17h` | `contractual_instruments`, `instrument_allocations`, `scope3_categories` (+15 rows), `estimation_records` | **4/4 present** | **0/4** | **0/4** | **YES for all 6** | unverified |
| A3 — P16-R | FIEW-018, 019 (2) | `20261009000000_p16r7`, `20261008000000_p16r5` | `uq_calc_snapshots_request_id`, `reportability_status` (+ invalidated/superseded columns) | **present** | **absent** | **`reportability_status` present** | **YES for both** | unverified |
| A4 — Gate 4/5/6 | FIEW-020 … 022 (3) | `20260905000000`, `20260905010000`, `20260905020000`, `20260906010000` | `calculation_snapshots.performed_by`, `document_processing_queue.automation_model/_version/_provider/_extracted_data`, write-once guard objects | **present** (4 automation columns + `performed_by` + 2 guard objects) | **absent** | **absent** | **YES for all 3** | unverified |
| B — Evidence | FIEW-023 … 026 (4) | `20260928000000_p8_fs_*`, `20260930000000`, `20260931000000`, `20260916000000_p8_b2`, `20260916010000`, `20260915000000` | `activity_clarifications`, `evidence_line_items`, provenance-line links (`calculation_snapshots.source_line_item_id`, `disclosure_value_evidence.source_line_item_id`), `uq_dve_reference_nullsafe`, D32 storage policies | **all present** | **all absent** | **`activity_clarifications`, `evidence_line_items` present; links absent** | **YES for all 4** (FIEW-024/025 additionally require the D32 platform policies — see SCM-001) | unverified |
| C — Reporting artefacts & disclosure | FIEW-027 … 040 (14) | `20260913000000_p8_report_lifecycle`, `20260914000000_p8_b1` (11 tables), `20260915000000_p8_b1`, `20260917000000/01_p8_b3`, `20260918000000_p8_b4`, `20260919000000_p8_b4_frozen`, `20260921000000_p8_s2`, `20261020000000_p17k` | 15 `disclosure_*` tables, `report_version_artifacts`, `report_versions.is_current` rule, `disclosure_requirement_versions` reference rows (18) | **15/15 disclosure tables present; 18 reference rows seeded** | **0/15** | **15/15 present** | **YES for all 14** | unverified |
| D — Insight | FIEW-041 … 048 (8) | `20261001000000_p8_i1`, `20261002000000_p8_i2`, `20261003000000_p8_i4`, `20261005000000`, `20261006000000`, `20261007000000` | `carbontally_insight_conversations/_messages/_interactions/_tool_calls`, `insight_rate_limit_buckets`, `insight_concurrency_leases` | **6/6 present** | **0/6** | **6/6 present** | **YES for all 8** | unverified |
| E — Governance / RLS / entitlements | FIEW-049 … 057 (9) | `20260920000000`, `20260922000000`, `20260923000000`, `20260925000000` (the four `p8_rls_*` hardening migrations), `20260926000000_p8_d4`, `20260927000000_p8_fin06`, `20261020000000_p17k` | RLS hardening (227 policies, 0 granting `anon`/`public`), `emission_factors` containment, `manual_processing_grants`, entitlement RLS gating, capability reference data | **all present; 145/145 tables RLS-enabled; 0 anon/public policies** | **partial** | **partial** | **YES for all 9** | unverified |

**Aggregate:** **57 of 57 FIEW rows have their schema blocker removed** by the clean canonical rebuild;
**0 of 57 are promoted** by this task; **57 of 57 remain runtime-unverified**.

---

## 2. Per-row FIEW impact (all 57 registered rows)

Column key: **CANON** = object present in the canonical rebuilt schema (this task, SQL-verified) ·
**FLAG** = present in the flagship durable database (this task, read-only SQL) · **BLOCKER REMOVED** =
the schema condition that caused the CT-FEATURE-02 downgrade is satisfied in a durable canonical schema ·
**RUNTIME** = status beyond schema (unchanged by this task).

### 2.1 Cluster A — P17-A dimensions (FIEW-001 … FIEW-011)

| ID | FTR | Feature | Required object(s) | Migration | CANON | FLAG | Blocker removed | Runtime |
|---|---|---|---|---|---|---|---|---|
| FIEW-001 | FTR-044 | Organisation type & consolidation approach | `organizations.organization_type`, `organizations.consolidation_approach` | `20261010000000_p17a` | present | absent | **YES** | NOT VERIFIED |
| FIEW-002 | FTR-076 | Acting-for attribution on results/logs | `calculation_snapshots./emissions_logs.acting_for_organization_id`, `performed_by_organization_id`, `audit_trail.acting_for_organization_id` | `20261010000000_p17a` | present | absent | **YES** | NOT VERIFIED |
| FIEW-003 | FTR-085 | Facility as accounting dimension | `calculation_snapshots./emissions_logs.facility_id` | `20261010000000_p17a` | present | absent | **YES** | NOT VERIFIED |
| FIEW-004 | FTR-135 | Data-quality dimension on results | `calculation_snapshots./emissions_logs.data_quality` | `20261010000000_p17a` | present | absent | **YES** | NOT VERIFIED |
| FIEW-005 | FTR-144 | Factor governance attributes | `emission_factors.factor_type`, `gas_coverage`, `scope2_method`, `scope3_category_hint` | `20261010000000_p17a` | present (4/4) | absent | **YES** | NOT VERIFIED |
| FIEW-006 | FTR-149 | Scope 1 energy-type dimension | `calculation_snapshots./emissions_logs.energy_type` (+ CHECK) | `20261010000000_p17a` | present | absent | **YES** | NOT VERIFIED |
| FIEW-007 | FTR-153 | Location-based method constraint enforcement | `scope2_method` columns + CHECK constraints | `20261010000000_p17a` | present | absent | **YES** | NOT VERIFIED |
| FIEW-008 | FTR-167 | Scope 3 category-specific dimensions | `scope3_category` + `scope3_method` + `transport_boundary` + `waste_origin` | `20261010000000_p17a`, `20261014000000_p17_10` | present | absent | **YES** | NOT VERIFIED |
| FIEW-009 | FTR-170 | Accounting-dimension columns on results | 10 columns on results tables (no `accounting_dimensions` table exists by design — naming drift resolved) | `20261010000000_p17a` | present | absent | **YES** | NOT VERIFIED |
| FIEW-010 | FTR-173 | Consolidation approach & org-type context | `organizations.organization_type`, `consolidation_approach` + CHECK | `20261010000000_p17a` | present | absent | **YES** | NOT VERIFIED |
| FIEW-011 | FTR-174 | Product-contract reporting dimensions | `scope3_method`, `transaction_provider` on both results tables (+4 indexes) | `20261014000000_p17_10` | present | absent | **YES** | NOT VERIFIED |

### 2.2 Cluster A2 — P17-C/D/H objects (FIEW-012 … FIEW-017)

| ID | FTR | Feature | Required object(s) | Migration | CANON | FLAG | Blocker removed | Runtime |
|---|---|---|---|---|---|---|---|---|
| FIEW-012 | FTR-157 | Contractual instrument repository | `contractual_instruments` (20 cols, 4 policies, RLS) | `20261011000000_p17c` | present | absent | **YES** | NOT VERIFIED |
| FIEW-013 | FTR-158 | Instrument allocations | `instrument_allocations` (12 cols, 4 policies, RLS) | `20261011000000_p17c` | present | absent | **YES** | NOT VERIFIED |
| FIEW-014 | FTR-161 | Instrument allocation to consumption | `instrument_allocations` + `p17_instrument_over_allocated()` | `20261011000000_p17c` | present | absent | **YES** | NOT VERIFIED |
| FIEW-015 | FTR-164 | Scope 3 category taxonomy (15) | `scope3_categories` + **15 seeded rows** | `20261012000000_p17d` | present (15 rows) | absent | **YES** | NOT VERIFIED |
| FIEW-016 | FTR-169 | Scope 3 estimation & assumptions | `estimation_records` (14 cols, 4 policies) | `20261013000000_p17h` | present | absent | **YES** | NOT VERIFIED |
| FIEW-017 | FTR-175 | Estimation records (P17-H) | `estimation_records` + `p17_dc04/dc05/dc07` + `p17_unsubstantiated_estimates` | `20261013000000_p17h` | present | absent | **YES** | NOT VERIFIED |

### 2.3 Cluster A3 — P16-R (FIEW-018 … FIEW-019)

| ID | FTR | Feature | Required object(s) | Migration | CANON | FLAG | Blocker removed | Runtime |
|---|---|---|---|---|---|---|---|---|
| FIEW-018 | FTR-181 | Calculation idempotency (request id) | `uq_calc_snapshots_request_id` (unique index) | `20261009000000_p16r7` | present | absent | **YES** | NOT VERIFIED |
| FIEW-019 | FTR-182 | Result reportability lifecycle | `reportability_status`, `invalidated_at/by/reason`, `superseded_by_snapshot_id`, `superseded_by_log_id` on both results tables + 2 indexes | `20261008000000_p16r5` | present | absent | **YES** | NOT VERIFIED |

### 2.4 Cluster A4 — Gate 4/5/6 automation provenance (FIEW-020 … FIEW-022)

| ID | FTR | Feature | Required object(s) | Migration | CANON | FLAG | Blocker removed | Runtime |
|---|---|---|---|---|---|---|---|---|
| FIEW-020 | FTR-184 | Calculation actor attribution (Gate 4) | `calculation_snapshots.performed_by` | `20260905000000` | present | absent | **YES** | NOT VERIFIED |
| FIEW-021 | FTR-185 | Machine/automation provenance (Gate 5) | `document_processing_queue.automation_model`, `automation_model_version`, `automation_provider`; write-once guard objects | `20260905010000`, `20260905020000` | present (4 automation columns + 2 guard objects) | absent | **YES** | NOT VERIFIED |
| FIEW-022 | FTR-186 | Human-after-automation attribution (Gate 6) | `document_processing_queue.automation_extracted_data` + guard | `20260906010000` | present | absent | **YES** | NOT VERIFIED |

### 2.5 Cluster B — Evidence (FIEW-023 … FIEW-026)

| ID | FTR | Feature | Required object(s) | Migration | CANON | FLAG | Blocker removed | Runtime |
|---|---|---|---|---|---|---|---|---|
| FIEW-023 | FTR-111 | Activity clarifications & adjudication lifecycle | `activity_clarifications` (34 cols, 4 policies, RLS) | `20260928000000`, `20260930000000`, `20260931000000` | present | absent | **YES** | NOT VERIFIED |
| FIEW-024 | FTR-127 | Evidence line items (P8-B2) | `evidence_line_items` (16 cols, 2 policies) | `20260916000000_p8_b2` | present | absent | **YES** | NOT VERIFIED |
| FIEW-025 | FTR-128 | Provenance line links | `calculation_snapshots.source_line_item_id`, `disclosure_value_evidence.source_line_item_id` | `20260916010000_p8_b2_provenance_line_links` | present | absent | **YES** | NOT VERIFIED |
| FIEW-026 | FTR-130 | Evidence idempotency & correction privileges | `uq_dve_reference_nullsafe` on `disclosure_value_evidence` | `20260915000000_p8_b1` | present | absent | **YES** | NOT VERIFIED |

### 2.6 Cluster C — Reporting artefacts & disclosure (FIEW-027 … FIEW-040)

| ID | FTR | Feature | Required object(s) | Migration | CANON | FLAG | Blocker removed | Runtime |
|---|---|---|---|---|---|---|---|---|
| FIEW-027 | FTR-178 | Estimation disclosure narrative integration | `disclosure_narrative_entries` | `20260918000000_p8_b4` | present | absent | **YES** | NOT VERIFIED |
| FIEW-028 | FTR-211 | Report lifecycle & catalogue (status machine) | `report_versions` lifecycle columns | `20260913000000_p8_report_lifecycle` | present | absent | **YES** | NOT VERIFIED |
| FIEW-029 | FTR-219 | Intensity catalogue & ratios (B3) | `disclosure_intensity_ratios` (+ denominator types/links) | `20260917000000`, `20260917010000` | present | absent | **YES** | NOT VERIFIED |
| FIEW-030 | FTR-220 | Report finalisation & frozen artefact (B4) | `report_version_artifacts` (12 cols, 2 policies) | `20260919000000_p8_b4_frozen` | present | absent | **YES** | NOT VERIFIED |
| FIEW-031 | FTR-223 | Report versions `is_current` integrity (S2) | single-valued `is_current` rule on `report_versions` | `20260921000000_p8_s2` | present | absent | **YES** | NOT VERIFIED |
| FIEW-032 | FTR-224 | Version artefacts (rendered files) | `report_version_artifacts` (+ storage bucket practice) | `20260919000000_p8_b4_frozen` | present (table) | absent | **YES** (bucket itself remains operator work — SCM-001/L3) | NOT VERIFIED |
| FIEW-033 | FTR-226 | Disclosure model foundation | 15 `disclosure_*` tables | `20260914000000_p8_b1` … | present (15/15) | absent | **YES** | NOT VERIFIED |
| FIEW-034 | FTR-227 | Governed requirement-version rows (P17-K) | `disclosure_requirement_versions` reference rows | `20261020000000_p17k` | present (**18 rows**; CT-FEATURE-02's clone showed **55** — see §5) | absent | **YES** | NOT VERIFIED |
| FIEW-035 | FTR-228 | Disclosure values & value-evidence | `disclosure_values`, `disclosure_value_evidence` | `20260915000000_p8_b1` | present | absent | **YES** | NOT VERIFIED |
| FIEW-036 | FTR-229 | Disclosure narrative overlay (B4) | `disclosure_narrative_entries` | `20260918000000_p8_b4` | present | absent | **YES** | NOT VERIFIED |
| FIEW-037 | FTR-230 | Disclosure projection engine | disclosure tables (durable input) | `20260914000000_p8_b1` | present | absent | **YES** | NOT VERIFIED |
| FIEW-038 | FTR-231 | Disclosure purposes & instance binding | `disclosure_report_purposes`, `_purpose_versions`, `_report_instance_binding`, `disclosure_purpose_requirements` | `20260914000000_p8_b1` | present | absent | **YES** | NOT VERIFIED |
| FIEW-039 | FTR-232 | Disclosure applicability assessments | `disclosure_applicability_assessments` | `20260914000000_p8_b1` | present | absent | **YES** | NOT VERIFIED |
| FIEW-040 | FTR-233 | Disclosure finalisation service | 15 `disclosure_*` tables (durable finalisation store) | `20260914000000_p8_b1` | present | absent | **YES** | NOT VERIFIED |

### 2.7 Cluster D — Insight (FIEW-041 … FIEW-048)

| ID | FTR | Feature | Required object(s) | Migration | CANON | FLAG | Blocker removed | Runtime |
|---|---|---|---|---|---|---|---|---|
| FIEW-041 | FTR-234 | Insight Layer-1 persistence (I1) | `carbontally_insight_conversations`, `_messages` | `20261001000000_p8_i1` | present | absent | **YES** | NOT VERIFIED |
| FIEW-042 | FTR-235 | Insight L1 authorization boundary (I2) | policies over the Insight tables | `20261002000000_p8_i2` | present (2 policies per table) | absent | **YES** | NOT VERIFIED |
| FIEW-043 | FTR-236 | Insight tool catalogue (I3) | `carbontally_insight_tool_calls` | `20261001000000_p8_i1` / `20261003000000` | present | absent | **YES** | NOT VERIFIED |
| FIEW-044 | FTR-237 | Insight L2 interaction orchestration (I4) | `carbontally_insight_interactions` | `20261003000000_p8_i4` | present | absent | **YES** | NOT VERIFIED |
| FIEW-045 | FTR-238 | Insight planner/context/rate-limit/leases | `insight_rate_limit_buckets`, `insight_concurrency_leases` | `20261005000000` | present | absent | **YES** | NOT VERIFIED |
| FIEW-046 | FTR-239 | Insight temporal comparison (P2) | Insight tables + comparison structures | `20261006000000` | present | absent | **YES** | NOT VERIFIED |
| FIEW-047 | FTR-240 | Insight data-quality + reproducibility (P3) | Insight tables + quality structures | `20261007000000` | present | absent | **YES** | NOT VERIFIED |
| FIEW-048 | FTR-241 | Insight customer UI | Insight persistence (the UI itself is frontend, not schema) | `20261001000000_p8_i1` | present | absent | **YES** (schema only; UI behaviour untouched) | NOT VERIFIED |

### 2.8 Cluster E — Governance / RLS / entitlements (FIEW-049 … FIEW-057)

| ID | FTR | Feature | Required object(s) | Migration | CANON | FLAG | Blocker removed | Runtime |
|---|---|---|---|---|---|---|---|---|
| FIEW-049 | FTR-036 | Anonymised/public grant containment | hardened policies; **0 policies granting `anon`/`public`** | `20260920000000`, `20260922000000`, `20260923000000` | present | partial | **YES** | NOT VERIFIED |
| FIEW-050 | FTR-142 | `emission_factors` internal containment | containment policies on `emission_factors` | `20260926000000_p8_d4` | present | absent | **YES** | NOT VERIFIED |
| FIEW-051 | FTR-146 | Provider ownership & provider-driven updates | `emission_factors` governance columns + containment | `20260926000000_p8_d4`, `20261010000000_p17a` | present | absent | **YES** | NOT VERIFIED |
| FIEW-052 | FTR-147 | Governed capability statement of factor support | `disclosure_requirement_versions` (18 rows) | `20260914000000_p8_b1` + `20261020000000_p17k` | present | absent | **YES** | NOT VERIFIED |
| FIEW-053 | FTR-193 | Manual-processing governance grants (FIN-06) | `manual_processing_grants` (8 cols) | `20260927000000_p8_fin06` | present | absent | **YES** | NOT VERIFIED |
| FIEW-054 | FTR-306 | RLS policy layer & tenant containment (hardening) | 227 policies; **145/145 tables RLS-enabled** | the four `p8_rls_*` hardening migrations (`20260920000000`, `20260922000000`, `20260923000000`, `20260925000000`) + baseline RLS | present | partial | **YES** | NOT VERIFIED |
| FIEW-055 | FTR-327 | Entitlement resolution per organisation (RLS gating) | entitlement-gated policies | `20260925000000_p8_rls_4b` | present | absent | **YES** | NOT VERIFIED |
| FIEW-056 | FTR-331 | Governed capability catalogue reference data (P17-K) | **no schema object**; reference rows only (18) | `20261020000000_p17k` | n/a (reference data present) | absent | **YES** (blocker was the missing table; it now exists and is seeded) | NOT VERIFIED — remains `DOCUMENTED_ONLY` by nature |
| FIEW-057 | FTR-334 | Plan → capability entitlement mapping | entitlement RLS gating policies | `20260925000000_p8_rls_4b` | present | absent | **YES** | NOT VERIFIED |

---

## 3. FIEW-required object presence (re-measured by this task)

31 FIEW-cited tables and 27 FIEW-cited columns were probed directly in three environments:

| Environment | Tables present | Columns present | Notes |
|---|---|---|---|
| **Canonical rebuild (Target-A)** | **31 / 31** | **26 / 27 probed** | The single "absent" probe was an invented British spelling (`organizations.organisation_type`); the real column `organizations.organization_type` is present → **27/27 real columns** |
| Flagship `postgres` | **2 / 31** (`vehicles`, `work_item_assignments`) | **0 / 27** | Independently confirms the FIEW register's `BLOCKED_BY_SCHEMA` basis |
| `carbontally_demo_local` | **27 / 31** (missing `contractual_instruments`, `instrument_allocations`, `scope3_categories`, `estimation_records`) | **4 / 27** (`reportability_status` ×2, `source_line_item_id`, `operational_telemetry_retention_days`) | Mid-way state; P17-C/D/H absent |

**Conclusion:** the clean rebuild closes the schema gap for all 31 FIEW-cited tables and all 27 FIEW-cited
columns that the register recorded as absent from durable environments.

## 4. Promotion rules (how a FIEW row may legitimately move up the ladder)

| Transition | Requires | Provided by this task? |
|---|---|---|
| blocker removed → `SCHEMA` | Object exists in a durable canonical schema | **YES (all 57)** |
| `SCHEMA` → `ROUTE` | The consuming API route is registered and reachable | No |
| `ROUTE` → `PERSISTED` | A real write/read cycle leaves and reads rows | No |
| `PERSISTED` → `E2E` | The user workflow completes end-to-end | No |
| `E2E` → `INDEPENDENTLY VERIFIED` | A separate agent/task reproduces the workflow | No |
| any → `PRODUCTION` | Verified in the production deployment | No (production untouched) |

## 5. Notes, discrepancies and counts

1. **P17-K reference-row count differs from the clone observation.** CT-FEATURE-02 recorded **55** rows
   in `disclosure_requirement_versions` in a disposable clone; the canonical rebuild contains **18**.
   The canonical figure is what the **current** `20261020000000_p17k` file inserts; the clone figure
   most plausibly reflects an additional out-of-band seed or an earlier revision. This task did **not**
   investigate the difference — recorded as an open question for the P17-K owner, **not** as a defect.
2. **FIEW-056 remains `DOCUMENTED_ONLY`.** Its migration intentionally creates no object; the rebuild
   confirms reference-data-only semantics (18 rows) and does not make the capability executable.
3. **FIEW-048 (Insight UI)** stays a frontend claim; only its persistence precondition is verified here.
4. **Counts:** 57 FIEW rows; **57 with the schema blocker removed**; **0 promoted**;
   **57 runtime-unverified**; 1 (`FIEW-056`) permanently reference-data-only regardless of schema.
5. **Domain coverage from §1** extends beyond the FIEW register: identity/auth, consultant operating
   model, processing entities, ingestion, factors, accounting, Scope 2 instruments, Scope 3
   taxonomy/estimation, evidence, QC/approval, reporting, Insight, commercial/billing, notifications,
   audit, RLS/security and admin/settings domains all have their required **application-schema**
   structures in the canonical rebuild (see comparison matrix §4 for the verified object list). The only
   required objects that are **not** application-schema objects are the storage buckets and their RLS
   policies (platform/operator work — SCM-001/SCM-003), and they affect document/artefact paths only.
6. **No FIEW downgrade is reversed by this document.** Reversal requires the CT-FEATURE-02 owner (or an
   equivalent independent task) to accept the schema evidence and then require runtime evidence before
   any promotion beyond `SCHEMA`.

<!--CTEOF-->




