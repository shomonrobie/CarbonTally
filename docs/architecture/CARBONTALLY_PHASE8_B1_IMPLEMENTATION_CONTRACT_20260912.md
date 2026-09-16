# CarbonTally — Phase 8 B1 Disclosure Model Foundation — Implementation Contract

**Document:** `CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md`
**Task reference:** `CT-P8-B1-IMPLEMENTATION-CONTRACT-20260912-009`
**Status:** IMPLEMENTATION CONTRACT — **B1 PO DECISIONS CLOSED; NOTHING IMPLEMENTED; B1 NOT YET AUTHORISED**
**Date:** 2026-09-12
**Type:** Architecture / implementation-contract only. No code, schema, migration, API, frontend, RLS or production change.
**Repository baseline:** branch `main`, HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c`
**Governing decisions:** D1–D17 and the 20 ratified Disclosure Model decisions (`CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md`)
**B1 PO decisions (PQ-1…PQ-8):** **CLOSED / RATIFIED** — `CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md` (task `CT-P8-B1-PO-DECISION-RATIFICATION-20260912-011`)
**Evidence labels:** **[CONFIRMED]** repository/authoritative fact · **[PROPOSED]** this contract's design · **[INFERRED]** derived from both · **[UNRESOLVED]** gated

---

## 1. Purpose

Convert the ratified Phase 8 Disclosure Model design into an **exact, implementation-ready B1 contract** —
the *Disclosure Model Foundation* — so that a later, separately authorised implementation task can build
B1 without inventing schema semantics, tenant scope, cardinality, or RLS intent.

This document is a **contract**, not an implementation. It defines the exact tables, columns, types,
keys, constraints, indexes, relationships, ownership, semantics, migration strategy and verification
requirements for **B1 only**.

---

## 2. Authoritative Inputs

| # | Document | Role |
|---|---|---|
| 1 | `CARBONTALLY_PHASE8_REPORTING_ARCHITECTURE_PO_RATIFICATION_D1-D17_20260912.md` | **[CONFIRMED]** D1–D17 |
| 2 | `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md` | **[CONFIRMED]** design (§§6–9, 11, 13, 18, 19, 20, 22) |
| 3 | `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` | **[CONFIRMED]** 20 decisions + G0-B/DM-7 refinement |
| 4 | `CARBONTALLY_PHASE8_P8X_COMPREHENSIVE_IMPLEMENTATION_READINESS_20260912.md` | **[CONFIRMED]** B1/B2/B3 batch split (§20) |
| 5 | `CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md` | **[CONFIRMED]** extraction boundary (B1/B2 line) |
| 6 | `CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912.md` | **[CONFIRMED]** EF-E separation |
| 7 | `CT-P8-G0-GOVERNANCE-CONSOLIDATION-20260912-008.md` | **[CONFIRMED]** terminology + DM-7 disposition |
| 8 | Repository schema/source (migrations, backend) | **[CONFIRMED]** reconciliation baseline |

---

## 3. Current Repository Baseline

**[CONFIRMED]** repository facts established by direct inspection:

| Fact | Evidence |
|---|---|
| HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c`, branch `main`, 55 migrations, 1 `p8`-prefixed | repo |
| **No `disclosure_*` table exists anywhere** | repo-wide search: 0 hits |
| `calculation_snapshots` exists and is append-only/immutable with `content_hash VARCHAR(64)`, `request_id UUID`, `factor_id`, `import_batch_id`, and D33 columns `source_item_id uuid` (FK → `manual_extraction_items(id)` `ON DELETE SET NULL`), `source_file text`, `source_page integer` | `20260807020000_add_calculation_snapshots.sql`, `20260823010000_d33_evidence_traceability.sql` |
| `report_generation_queue(id, organization_id NOT NULL, report_type VARCHAR NOT NULL, reporting_year INTEGER NOT NULL, status, …)` — the **report instance** spine; only `report_type` value is `annual` | init schema `:970`; `backend/api/v3_reports.py:96` |
| `report_versions(id, report_id UUID NOT NULL*, version_number, content JSONB, is_current, …, UNIQUE(report_id, version_number))`; `status` added by `20260913000000_p8_report_lifecycle_status.sql` (six states) | init schema `:1003`; lifecycle migration |
| **`report_versions.report_id` has NO foreign key** to `report_generation_queue(id)` (pre-existing) | init schema `:1005` |
| `manual_extraction_items(file_id uuid)` → `organization_files(id)` `ON DELETE SET NULL` (D33) | `…d33…sql` |
| `organizations` carries applicability characteristics: `company_size, is_public, is_listed, isin, lei, business_structure, country, financial_year_end, reporting_standard, sustainability_standard, vat_region, secr_enabled, esrs_enabled, issb_enabled, accounting_standard, …` | init schema `:189–256` |
| `audit_trail(action_type, table_name, record_id, performed_by, old_data, new_data, changes, metadata, …)` — append-only via `p7` trigger | init schema `:1669`; `20260912000000_p7_…sql` |
| Tenant convention: `organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE`; PK `id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4()`; timestamps `TIMESTAMPTZ DEFAULT NOW()` | repo convention |
| RLS: enabled on ~7/104 production tables; **97 disabled; `anon` holds `GRANT ALL`**; 21 applied / 34 outstanding migrations | `CARBONTALLY_RLS_PRODUCTION_BASELINE_AND_REMEDIATION_SPEC_20260912.md` |
| Tenant `NOT NULL` migration `20260831030000_tenant_org_id_not_null.sql` is among the **34 outstanding** | RLS baseline §5.1 |

**Baseline consequence:** B1 must be **additive, idempotent and app-layer-guarded**. RLS is defined as
*intent plus policy text*, but in the current production state **app-layer authorization is the real
boundary** (§23). B1 must not be used as a vehicle to remediate the wider RLS gap.

---

## 4. B1 Scope

**[PROPOSED]** B1 = the **structural Disclosure Model foundation**: the version-bound framework →
requirement → mapping → purpose → applicability → value spine, plus the value→evidence linkage table.
Concretely, B1 delivers:

1. Framework catalogue + framework versions (`disclosure_frameworks`, `disclosure_framework_versions`).
2. Requirement versions + controlled mappings (`disclosure_requirement_versions`, `disclosure_requirement_mappings`).
3. Purpose catalogue + purpose versioning + purpose→requirement set (`disclosure_report_purposes`, `disclosure_report_purpose_versions`, `disclosure_purpose_requirements`).
4. Report-instance binding to purpose/applicability/period/consolidation (`disclosure_report_instance_binding`).
5. Applicability assessments (`disclosure_applicability_assessments`).
6. Disclosure values (`disclosure_values`).
7. Value→evidence linkage (`disclosure_value_evidence`).
8. RLS **policy intent** (not activation/remediation).
9. Domain/API **boundary definition** (no endpoints).
10. Verification contract (§27).

**B1 is pure structure + reference-data *shape*.** It carries **no** seeded requirement content decisions
beyond the framework/purpose identity rows (which are D1/D6-R facts), and **no** disclosure values.

## 5. B1 Non-Scope

**[PROPOSED]** explicitly **not** in B1: `evidence_line_items`; `calculation_snapshots.source_line_item_id`;
intensity tables; narrative/commentary; Layer-2 targets/actions/policies/transition-plan; per-gas/GWP;
base-year/recalculation; report generation/composition; projections; framework/requirement **seeding**
(content); API endpoints; frontend; exports/frozen artefacts; PDF/IMAGE extraction fidelity;
FactorMatchingEngine/EF-E; legacy route (D16); broad RLS remediation; production deployment. (See §6 for
the B1/B2 boundary and §28 for PO decisions.)

---

## 6. B1 vs B2 Boundary

**[CONFIRMED]** The readiness roadmap §20 splits B1 (foundation) from B2 (evidence/line-item
addressability). **[CONFIRMED]** The line-item forensic establishes that the deterministic PDF/IMAGE path
does not preserve line structure, so **line-item granularity must not be manufactured**.

**[PROPOSED] B1/B2 division:**

| Concern | Batch | Rationale |
|---|---|---|
| Framework/version, requirement, mapping, purpose, applicability, value, value→evidence | **B1** | Pure structure; depends only on existing tables |
| `evidence_line_items` (addressable line rows) | **B2** | Depends on extraction fidelity/boundary; not required for B1 structure |
| `calculation_snapshots.source_line_item_id` (additive FK `SET NULL`) | **B2** | Mirrors D33; extends an existing table — a distinct, reviewable change |
| Historical line-item backfill (Class 1) | **B2** | Only meaningful once `evidence_line_items` exists |
| PDF/IMAGE extraction fidelity (P1) | **separate batch** | Upstream correctness; independent |

**Does B1 need any FK/interface *placeholder* for B2?** **[PROPOSED] No.** The B1 forward trace is
`disclosure_values → disclosure_value_evidence → calculation_snapshots → manual_extraction_items →
organization_files`, using **already-existing** columns (`source_item_id`, `source_file`, `source_page`,
`file_id`). `evidence_line_items` will later slot *between* `calculation_snapshots` and
`manual_extraction_items`, and B2 will (a) create that table, (b) add
`calculation_snapshots.source_line_item_id`, and (c) optionally add an additive `source_line_item_id`
column to `disclosure_value_evidence`. None of those requires a placeholder column in B1. **No placeholder
is created.**

**[UNRESOLVED — recorded, not silently resolved] Documented sequencing conflict.** The design §22.1 lists
`evidence_line_items` and the intensity tables inside its **MVP** (14 tables), whereas the roadmap §20
assigns `evidence_line_items` to **B2** and the "SECR intensity model" to **B3**. This is a
**delivery-sequencing conflict, not a semantic one** (the design MVP answers "what must exist for the
model to function"; the roadmap answers "how it is delivered safely"). This contract follows the
**roadmap** for the B1 boundary; the intensity placement was ratified as **PQ-1** (intensity → **B3**; §28).

---

## 7. Existing Component Reuse

| Existing component | Decision | Reason | Batch |
|---|---|---|---|
| `organizations` (+ applicability characteristics) | **REUSE AS-IS** | `characteristic_snapshot` reads these; no new columns | B1 |
| `report_generation_queue` (instance spine) | **REUSE AS-IS** | Instance binding FKs to it; no competing report spine (D2/D15) | B1 |
| `report_versions` + lifecycle (`status`, six states) | **REUSE AS-IS** | Values key to `report_versions.id`; immutability respected, not re-implemented | B1 |
| `domain/report_lifecycle.py` authority model | **REUSE AS-IS** | New surfaces respect `AUTHORITY_ADMIN`/`required_authority()` | B1 |
| `calculation_snapshots` (+ `content_hash`, `request_id`) | **REUSE AS-IS** | Values are **projections**; never recomputed | B1 |
| D33 evidence chain (`source_item_id`, `file_id`, `source_page`) | **REUSE AS-IS** | Value evidence references it; no duplication | B1 |
| `domain/evidence.py` (`COMPLETE/PARTIAL/UNAVAILABLE`) | **REUSE AS-IS** | `evidence_completeness` mirrors it | B1 |
| `audit_trail` + `AuditLogger`/`AuditRepository` taxonomy | **REUSE AS-IS** | Every B1 write emits existing audit actions | B1 |
| `require_org_member`/`require_org_admin`/`ensure_org_access` | **REUSE AS-IS** | Established guard pattern; no new authz | B1 |
| `units` (`code`, `conversion_factor`) | **REUSE AS-IS** | `unit_hint`/denominator units reference it | B1 |
| `activity_categories` (`esrs_e1_category`, `ghg_protocol_*`) | **REUSE AS-IS** | Activity taxonomy; **not** a requirement model | B1 |
| `report_templates.template_structure` | **DO NOT REUSE as a requirement store** | Presentation-only (D2/D3) | B1 |
| Legacy `report_generator.py` / enhanced-report route | **DO NOT REUSE** | D16 legacy disposition; untouched | separate |
| CSV/XLSX `line_items[]`; AI line-items | **DO NOT REUSE in B1** | Line-item addressability is B2 | B2 |
| `FactorMatchingEngine`; `emission_factors`; `import_batches` | **NO CHANGE** | B1 stores no factor logic/values | — |

**No functionality is duplicated.** B1 adds tables only; it modifies **no** existing table and **no**
existing policy.

---

## 8. Proposed Tables

**[PROPOSED]** B1 introduces **eleven (11)** new tables and **modifies zero** existing tables.

| # | Table | Scope | Kind | Cardinality (rows, steady state) |
|---|---|---|---|---|
| 1 | `disclosure_frameworks` | Global catalogue | New | ~3 |
| 2 | `disclosure_framework_versions` | Global catalogue | New | ~4–6 initially |
| 3 | `disclosure_requirement_versions` | Global catalogue | New | tens–low hundreds |
| 4 | `disclosure_requirement_mappings` | Global catalogue | New | ~1 per quantitative requirement |
| 5 | `disclosure_report_purposes` | Global catalogue | New | 4 |
| 6 | `disclosure_report_purpose_versions` | Global catalogue | New | small |
| 7 | `disclosure_purpose_requirements` | Global catalogue | New | (purposes × requirements) |
| 8 | `disclosure_applicability_assessments` | Organisation-scoped | New | 1..n per org × framework_version × period |
| 9 | `disclosure_report_instance_binding` | Organisation-scoped | New | 1 per report instance |
| 10 | `disclosure_values` | Organisation-scoped | New | 1 per (report_version, requirement_version) |
| 11 | `disclosure_value_evidence` | Organisation-scoped | New | 1..n per value |

**Explicitly excluded from B1 (per §6):** `evidence_line_items`, `calculation_snapshots.source_line_item_id`,
and the intensity tables. **Not created in B1:** narratives, management commentary, Layer-2, per-gas/GWP,
base-year/recalculation.

### Common conventions (all 11 tables) **[PROPOSED]**

- **Primary key:** `id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4()` (matches every existing CarbonTally table).
- **UUID rationale:** consistent with all existing PKs; safe for distributed/offline generation; avoids sequence contention.
- **Timestamps:** `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`; `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`.
- **Actor columns:** `created_by UUID`, `updated_by UUID` (nullable — service-role/system writes have no actor), matching the existing pattern.
- **No `organization_id` on global catalogue tables** (platform-controlled, no tenant data).
- **`organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE`** on every organisation-scoped table (matches tenant convention and the outstanding `tenant_org_id_not_null` intent).
- **Enumerations** are enforced with `CHECK (col IN (…))` (the repository's established pattern; no new `CREATE TYPE` enums are introduced — this avoids a migration-coupled type lifecycle).

---

## 9. Exact Column Definitions

Notation: `NN` = NOT NULL · `PK` primary key · `FK` foreign key · `U` unique · `CK` check. Enumeration
values are **[CONFIRMED]** from the design where listed, otherwise **[PROPOSED]**.

### 9.1 `disclosure_frameworks` — global catalogue **[PROPOSED]**

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | `uuid` | NN (PK) | `extensions.uuid_generate_v4()` | |
| `code` | `varchar` | NN (U) | — | `CK IN ('GHG_PROTOCOL','UK_SECR','ESRS_E1')` (D1) |
| `name` | `varchar` | NN | — | e.g. "GHG Protocol Corporate Standard" |
| `publisher` | `varchar` | null | — | |
| `kind` | `varchar` | NN | — | `CK IN ('accounting_foundation','jurisdiction_statute','eu_standard')` |
| `is_primary_foundation` | `boolean` | NN | `false` | true for `GHG_PROTOCOL` (D8) |
| `description` | `text` | null | — | |
| `created_at` / `updated_at` | `timestamptz` | NN | `NOW()` | |
| `created_by` / `updated_by` | `uuid` | null | — | |

No `organization_id` (global). Immutable-by-convention once referenced. RLS: read-all authenticated, writes service-role only.

### 9.2 `disclosure_framework_versions` — global catalogue **[PROPOSED]**

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | `uuid` | NN (PK) | `extensions.uuid_generate_v4()` | |
| `framework_id` | `uuid` | NN (FK) | — | → `disclosure_frameworks(id)` `ON DELETE RESTRICT` |
| `version_label` | `varchar` | NN | — | e.g. `2023`, `2023+2025/1416`, `SECR-2019`, `SECR-2025` |
| `legal_reference` | `text` | null | — | e.g. `(EU) 2023/2772`, `SI 2013/1970`, `PB13944` |
| `source_tier` | `smallint` | NN | — | `CK (source_tier BETWEEN 1 AND 3)` (D17) |
| `source_url` | `text` | null | — | |
| `authoritative_source_date` | `date` | null | — | |
| `status` | `varchar` | NN | — | `CK IN ('IN_FORCE','ADOPTED_NOT_IN_FORCE','SUPERSEDED','WITHDRAWN')` (design §6.1) |
| `applicable_from` | `date` | null | — | |
| `applicable_to` | `date` | null | — | |
| `verified_at` | `timestamptz` | null | — | |
| `created_at` / `updated_at` | `timestamptz` | NN | `NOW()` | |
| `created_by` / `updated_by` | `uuid` | null | — | |

Constraints: `U (framework_id, version_label)`; `CK (applicable_to IS NULL OR applicable_from IS NULL OR applicable_to >= applicable_from)`; **`CK (status <> 'ADOPTED_NOT_IN_FORCE' OR applicable_from IS NULL)`** — a not-in-force version must carry no `applicable_from` (design §6.5). No `organization_id`.

### 9.3 `disclosure_requirement_versions` — global catalogue **[PROPOSED]**

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | `uuid` | NN (PK) | `extensions.uuid_generate_v4()` | |
| `framework_version_id` | `uuid` | NN (FK) | — | → `disclosure_framework_versions(id)` `ON DELETE RESTRICT` |
| `requirement_code` | `varchar` | NN | — | controlled internal key; may be a concept key (e.g. `E1_SCOPE1_GROSS`) |
| `official_identifier` | `varchar` | null | — | official ID **only when resolved** (e.g. `E1-6`) |
| `identifier_status` | `varchar` | NN | `'UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION'` | `CK IN ('RESOLVED','UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION')` |
| `title` | `varchar` | NN | — | |
| `description` | `text` | null | — | |
| `requirement_class` | `varchar` | NN | — | `CK IN ('REQUIRED','CONDITIONAL','OPTIONAL','NOT_APPLICABLE','CUSTOMER_INPUT_REQUIRED','UNDETERMINED','NOT_SUPPORTED','FUTURE')` (design §7.2) |
| `is_quantitative` | `boolean` | NN | `false` | |
| `value_kind` | `varchar` | NN | — | `CK IN ('QUANTITATIVE','QUALITATIVE','NARRATIVE_BOUND','SELECTION')` |
| `unit_hint` | `varchar` | null | — | |
| `scope_hint` | `varchar` | null | — | e.g. `1`,`2`,`3` |
| `gas_hint` | `varchar` | null | — | e.g. `CO2E`, `CH4` |
| `scope2_method_hint` | `varchar` | null | — | `CK (scope2_method_hint IS NULL OR scope2_method_hint IN ('LOCATION_BASED','MARKET_BASED'))` |
| `period_semantics` | `varchar` | null | — | |
| `parent_requirement_id` | `uuid` | null (FK) | — | → `disclosure_requirement_versions(id)` `ON DELETE SET NULL` |
| `display_order` | `integer` | null | — | |
| `purpose_hint` | `varchar` | null | — | |
| `carbontally_capability` | `varchar` | NN | — | `CK IN ('SUPPORTED','PARTIALLY_SUPPORTED','STRUCTURED_INPUT_REQUIRED','EXTERNAL_INPUT_REQUIRED','MISSING_CAPABILITY','FUTURE','NOT_APPLICABLE_TO_PRODUCT')` (design §7.3) |
| `source_locator` | `text` | null | — | annex/section/page |
| `authoritative_text_ref` | `text` | null | — | |
| `source_tier` | `smallint` | null | — | `CK (source_tier IS NULL OR source_tier BETWEEN 1 AND 3)` |
| `verified_at` | `timestamptz` | null | — | |
| `created_at` / `updated_at` | `timestamptz` | NN | `NOW()` | |
| `created_by` / `updated_by` | `uuid` | null | — | |

Constraints: `U (framework_version_id, requirement_code)`;
**`CK (identifier_status = 'RESOLVED' OR official_identifier IS NULL)`** — an unresolved requirement may
**never** carry an official identifier (enforces "do not invent ESRS identifiers", D17/§12.1). No `organization_id`. Immutable once referenced by a finalised report.

### 9.4 `disclosure_requirement_mappings` — global catalogue **[PROPOSED]**

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | `uuid` | NN (PK) | `extensions.uuid_generate_v4()` | |
| `requirement_version_id` | `uuid` | NN (FK) | — | → `disclosure_requirement_versions(id)` `ON DELETE RESTRICT` |
| `mapping_version` | `integer` | NN | `1` | a mapping change = new version (D14) |
| `source_kind` | `varchar` | NN | — | `CK IN ('CALCULATION_AGGREGATE','EMISSIONS_LOG_AGGREGATE','FACTOR_PROVENANCE','EVIDENCE_COMPLETENESS','ENERGY_ACTIVITY','INTENSITY_RATIO','PRIOR_PERIOD_VALUE','ORG_PROFILE_FACT','CUSTOMER_INPUT')` (design §7.1) |
| `source_selector` | `jsonb` | null | — | **schema-validated at app layer**; a closed-key JSON object (`{"scope":"1"}`, `{"scope":"2","method":"LOCATION_BASED"}`, `{"scope":"3","category":"CATEGORY_6"}`, `{"gas":"CH4"}`). **Must not** store code, SQL, expressions, URLs or credentials |
| `aggregation` | `varchar` | NN | — | `CK IN ('SUM','SUM_KG_CO2E','DISTINCT_COUNT','RATIO','PASSTHROUGH')` (design §7.1) |
| `display_only` | `boolean` | NN | `false` | non-quantitative requirements |
| `is_current` | `boolean` | NN | `true` | |
| `created_at` / `updated_at` | `timestamptz` | NN | `NOW()` | |
| `created_by` / `updated_by` | `uuid` | null | — | |

Constraints: `U (requirement_version_id, mapping_version)`; **partial** `U (requirement_version_id) WHERE is_current` (exactly one current mapping per requirement). No `organization_id`.

### 9.5 `disclosure_report_purposes` — global catalogue **[PROPOSED]**

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | `uuid` | NN (PK) | `extensions.uuid_generate_v4()` | |
| `code` | `varchar` | NN (U) | — | `CK IN ('ANNUAL_CARBON','MANAGEMENT','UK_SECR','ESRS_E1_QUANT')` (D6-R) |
| `name` | `varchar` | NN | — | e.g. "UK SECR Report" |
| `is_statutory_positioned` | `boolean` | NN | `false` | true for `UK_SECR`, `ESRS_E1_QUANT` |
| `description` | `text` | null | — | |
| `created_at` / `updated_at` | `timestamptz` | NN | `NOW()` | |
| `created_by` / `updated_by` | `uuid` | null | — | |

**`purpose_code` is separate from `report_type`** (DM-2): this table carries the purpose vocabulary; `report_generation_queue.report_type` is untouched. No `organization_id`.

### 9.6 `disclosure_report_purpose_versions` — global catalogue **[PROPOSED]**

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | `uuid` | NN (PK) | `extensions.uuid_generate_v4()` | |
| `purpose_id` | `uuid` | NN (FK) | — | → `disclosure_report_purposes(id)` `ON DELETE RESTRICT` |
| `version` | `integer` | NN | — | |
| `effective_from` | `date` | null | — | |
| `status` | `varchar` | NN | `'DRAFT'` | `CK IN ('DRAFT','ACTIVE','SUPERSEDED')` |
| `created_at` / `updated_at` | `timestamptz` | NN | `NOW()` | |
| `created_by` / `updated_by` | `uuid` | null | — | |

Constraints: `U (purpose_id, version)`.

### 9.7 `disclosure_purpose_requirements` — global catalogue **[PROPOSED]**

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | `uuid` | NN (PK) | `extensions.uuid_generate_v4()` | |
| `purpose_version_id` | `uuid` | NN (FK) | — | → `disclosure_report_purpose_versions(id)` `ON DELETE CASCADE` |
| `requirement_version_id` | `uuid` | NN (FK) | — | → `disclosure_requirement_versions(id)` `ON DELETE RESTRICT` |
| `display_order` | `integer` | NN | — | presentation ordering within the purpose |
| `required_for_finalisation` | `boolean` | NN | `true` | interacts with `DM-5` finalisation |
| `purpose_specific_class` | `varchar` | null | — | `CK (purpose_specific_class IS NULL OR purpose_specific_class IN (<requirement_class set>))` — an explicit purpose-level override, else the requirement's own class applies |
| `created_at` | `timestamptz` | NN | `NOW()` | |
| `created_by` | `uuid` | null | — | |

Constraints: `U (purpose_version_id, requirement_version_id)`.

### 9.8 `disclosure_applicability_assessments` — organisation-scoped **[PROPOSED]**

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | `uuid` | NN (PK) | `extensions.uuid_generate_v4()` | |
| `organization_id` | `uuid` | NN (FK) | — | → `organizations(id)` `ON DELETE CASCADE` |
| `framework_version_id` | `uuid` | NN (FK) | — | → `disclosure_framework_versions(id)` `ON DELETE RESTRICT` |
| `reporting_year` | `integer` | NN | — | convenience key; the authoritative period is start/end below |
| `reporting_period_start` | `date` | NN | — | **explicit** (DM-3) |
| `reporting_period_end` | `date` | NN | — | **explicit** (DM-3) |
| `characteristic_snapshot` | `jsonb` | NN | — | the customer facts relied on **and their source** (from `organizations` columns). Must **not** contain credentials, signed URLs or secrets |
| `assessed_status` | `varchar` | NN | — | `CK IN ('APPLIES','DOES_NOT_APPLY','UNDETERMINED','CUSTOMER_INPUT_REQUIRED')` (design §8.1) |
| `basis` | `text` | NN | — | which cited rule/source produced the status (auditable; D17) |
| `determined_by` | `uuid` | null | — | actor; null = system |
| `determined_at` | `timestamptz` | null | — | |
| `version` | `integer` | NN | `1` | **append-only**: a re-assessment is a NEW row |
| `created_at` | `timestamptz` | NN | `NOW()` | |
| `created_by` | `uuid` | null | — | |

Constraints: `U (organization_id, framework_version_id, reporting_period_start, reporting_period_end, version)`; `CK (reporting_period_end >= reporting_period_start)`.
**Semantics:** `UNDETERMINED` is a first-class state and must never be coerced to `DOES_NOT_APPLY`; the row records **facts and basis**, never a legal determination (APPL).

### 9.9 `disclosure_report_instance_binding` — organisation-scoped **[PROPOSED]**

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | `uuid` | NN (PK) | `extensions.uuid_generate_v4()` | |
| `organization_id` | `uuid` | NN (FK) | — | → `organizations(id)` `ON DELETE CASCADE` |
| `report_id` | `uuid` | NN (FK) | — | → `report_generation_queue(id)` `ON DELETE CASCADE` (the existing instance spine) |
| `purpose_version_id` | `uuid` | NN (FK) | — | → `disclosure_report_purpose_versions(id)` `ON DELETE RESTRICT` |
| `applicability_assessment_id` | `uuid` | null (FK) | — | → `disclosure_applicability_assessments(id)` `ON DELETE SET NULL` |
| `reporting_period_start` | `date` | NN | — | **explicit** (DM-3) |
| `reporting_period_end` | `date` | NN | — | **explicit** (DM-3) |
| `consolidation_approach` | `varchar` | NN | `'OPERATIONAL_CONTROL'` | `CK IN ('OPERATIONAL_CONTROL','FINANCIAL_CONTROL','EQUITY_SHARE')` (**GP-CONS** — structured reporting-context attribute) |
| `created_at` / `updated_at` | `timestamptz` | NN | `NOW()` | |
| `created_by` / `updated_by` | `uuid` | null | — | |

Constraints: **`U (report_id)`** — exactly one binding per report instance; `CK (reporting_period_end >= reporting_period_start)`.
**Period agreement invariant (PQ-2 RATIFIED):** the instance binding is **authoritative** for the report instance. Where this binding references an `applicability_assessment_id`, the binding's `(reporting_period_start, reporting_period_end)` **MUST equal** the assessment's corresponding periods — enforced at the application/service layer and verified by test (§27.B). No permanent calendar-year assumption is made.
**`purpose_code` binding:** the purpose code is reached via `purpose_version_id → disclosure_report_purpose_versions.purpose_id → disclosure_report_purposes.code`; it is **never** written into `report_generation_queue.report_type` (DM-2).

### 9.10 `disclosure_values` — organisation-scoped **[PROPOSED]**

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | `uuid` | NN (PK) | `extensions.uuid_generate_v4()` | |
| `organization_id` | `uuid` | NN (FK) | — | → `organizations(id)` `ON DELETE CASCADE`; **must equal** the owning report's org (app-layer invariant, §25) |
| `report_version_id` | `uuid` | NN (FK) | — | → `report_versions(id)` `ON DELETE CASCADE` |
| `requirement_version_id` | `uuid` | NN (FK) | — | → `disclosure_requirement_versions(id)` `ON DELETE RESTRICT` |
| `requirement_mapping_id` | `uuid` | null (FK) | — | → `disclosure_requirement_mappings(id)` `ON DELETE RESTRICT` (null for non-mapped/narrative requirements) |
| `effective_class` | `varchar` | NN | — | **AUTHORITATIVE home for the derived requirement/applicability outcome** (PQ-3 RATIFIED); `CK IN (<requirement_class set>)` — a property derived from applicability, never an overwrite of `requirement_class` (D12/D13) |
| `value_status` | `varchar` | NN | `'PENDING'` | **narrow materialisation lifecycle only** (PQ-3 RATIFIED); `CK IN ('PENDING','RESOLVED','UNRESOLVED')` — must **NOT** duplicate or reinterpret `requirement_class`, applicability, `carbontally_capability` or `effective_class` |
| `value_kind` | `varchar` | NN | — | `CK IN ('QUANTITATIVE','QUALITATIVE','NARRATIVE_BOUND','SELECTION')` |
| `numeric_value` | `numeric` | null | — | |
| `value_unit` | `varchar` | null | — | |
| `text_value` | `text` | null | — | qualitative/selection text (customer-owned or system-derived per `P3`) |
| `reporting_year` | `integer` | NN | — | |
| `source_kind` | `varchar` | null | — | `CK (source_kind IS NULL OR source_kind IN (<source_kind set>))`; copied from the mapping used |
| `reason` | `text` | null | — | basis recorded where the **derived outcome** requires explanation (e.g. `effective_class IN ('NOT_SUPPORTED','UNDETERMINED')`); **not** a `value_status` value |
| `computed_at` | `timestamptz` | null | — | when the value was materialised (null for `PENDING`) |
| `created_at` / `updated_at` | `timestamptz` | NN | `NOW()` | |
| `created_by` / `updated_by` | `uuid` | null | — | |

Constraints: **`U (report_version_id, requirement_version_id)`** — exactly one value per requirement per report version (prevents duplicate disclosure records).
**Immutability (PQ-4 RATIFIED WITH CONDITION):** rows for a report version whose `status ∈ {APPROVED, FINAL}` must never be mutated (D15); enforced at the **application/service layer** in B1 and verified by tests. A DB trigger is **not** required for B1 (deferred as separate hardening).
**`effective_class` semantics (PQ-3 RATIFIED):** the **single authoritative home** for the derived regulatory/applicability/capability outcome; `CUSTOMER_INPUT_REQUIRED` ≠ `NOT_SUPPORTED`; `NOT_SUPPORTED`/`UNDETERMINED` carry a `reason` and are never presented as satisfied (DM-5, Decision Record §8).
**`value_status` semantics (PQ-3 RATIFIED):** `PENDING` = materialisation not yet complete; `RESOLVED` = the value has been successfully materialised; `UNRESOLVED` = the system currently cannot produce a resolved value. **`UNRESOLVED` is NOT a substitute for** `CUSTOMER_INPUT_REQUIRED`, `NOT_SUPPORTED`, `NOT_APPLICABLE`, `UNDETERMINED`, or any requirement/applicability/capability classification — those remain in `effective_class` and the requirement/applicability model. The distinction between **regulatory/applicability outcome** and **value-materialisation lifecycle** remains explicit. Valid example: `requirement_class=REQUIRED`, `carbontally_capability=SUPPORTED`, `applicability=APPLIES`, `effective_class=CUSTOMER_INPUT_REQUIRED`, `value_status=PENDING`. Second valid example: `effective_class=NOT_SUPPORTED`, `value_status=UNRESOLVED`.

### 9.11 `disclosure_value_evidence` — organisation-scoped **[PROPOSED]**

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | `uuid` | NN (PK) | `extensions.uuid_generate_v4()` | |
| `organization_id` | `uuid` | NN (FK) | — | → `organizations(id)` `ON DELETE CASCADE` |
| `disclosure_value_id` | `uuid` | NN (FK) | — | → `disclosure_values(id)` `ON DELETE CASCADE` |
| `calculation_snapshot_id` | `uuid` | null (FK) | — | → `calculation_snapshots(id)` `ON DELETE SET NULL` (null for manual/`CUSTOMER_INPUT` values with no calculation) |
| `emissions_log_id` | `uuid` | null (FK) | — | → `emissions_logs(id)` `ON DELETE SET NULL` |
| `source_item_id` | `uuid` | null (FK) | — | → `manual_extraction_items(id)` `ON DELETE SET NULL`; **denormalised** for drill-down without a join chain |
| `source_file_id` | `uuid` | null (FK) | — | → `organization_files(id)` `ON DELETE SET NULL`; denormalised |
| `source_page` | `integer` | null | — | |
| `evidence_completeness` | `varchar` | null | — | `CK (evidence_completeness IS NULL OR evidence_completeness IN ('COMPLETE','PARTIAL','UNAVAILABLE'))` — mirrors `domain/evidence.py` |
| `contribution_share` | `numeric` | null | — | where a value is a share of an aggregate; `CK (contribution_share IS NULL OR contribution_share >= 0)` |
| `created_at` | `timestamptz` | NN | `NOW()` | |
| `created_by` | `uuid` | null | — | |

Constraints: `U (disclosure_value_id, calculation_snapshot_id)` (duplicate-link prevention). **No `evidence_line_items` FK in B1** (§6). Evidence is **referenced, never copied** (no storage objects, no signed URLs).

> **B2 additive extension (not in B1):** `ALTER TABLE disclosure_value_evidence ADD COLUMN IF NOT EXISTS source_line_item_id uuid` → `evidence_line_items(id)` `ON DELETE SET NULL`.

---

## 10. Keys and Constraints

**[PROPOSED]** Consolidated (exact DDL-level constraints are in §9; enumerations are `CHECK (col IN (…))`).

| Table | PK | Unique | Check (beyond enum lists) |
|---|---|---|---|
| `disclosure_frameworks` | `id` | `(code)` | — |
| `disclosure_framework_versions` | `id` | `(framework_id, version_label)` | period order; `ADOPTED_NOT_IN_FORCE ⇒ applicable_from IS NULL` |
| `disclosure_requirement_versions` | `id` | `(framework_version_id, requirement_code)` | `identifier_status='RESOLVED' OR official_identifier IS NULL`; `source_tier BETWEEN 1 AND 3` |
| `disclosure_requirement_mappings` | `id` | `(requirement_version_id, mapping_version)`; **partial unique** `(requirement_version_id) WHERE is_current` | — |
| `disclosure_report_purposes` | `id` | `(code)` | — |
| `disclosure_report_purpose_versions` | `id` | `(purpose_id, version)` | — |
| `disclosure_purpose_requirements` | `id` | `(purpose_version_id, requirement_version_id)` | — |
| `disclosure_applicability_assessments` | `id` | `(organization_id, framework_version_id, reporting_period_start, reporting_period_end, version)` | `reporting_period_end >= reporting_period_start` |
| `disclosure_report_instance_binding` | `id` | `(report_id)` | `reporting_period_end >= reporting_period_start` |
| `disclosure_values` | `id` | `(report_version_id, requirement_version_id)` | `value_status IN ('PENDING','RESOLVED','UNRESOLVED')` (PQ-3 RATIFIED); `reason` recorded where `effective_class IN ('NOT_SUPPORTED','UNDETERMINED')` (app-layer) |
| `disclosure_value_evidence` | `id` | `(disclosure_value_id, calculation_snapshot_id)` | `contribution_share >= 0` |

**FK deletion semantics (all tables):**

| Relationship | ON DELETE |
|---|---|
| any `organization_id` → `organizations(id)` | `CASCADE` |
| → `disclosure_frameworks(id)` | `RESTRICT` |
| → `disclosure_framework_versions(id)` | `RESTRICT` |
| → `disclosure_requirement_versions(id)` | `RESTRICT` |
| → `disclosure_requirement_mappings(id)` | `RESTRICT` |
| → `disclosure_report_purposes(id)` | `RESTRICT` |
| → `disclosure_report_purpose_versions(id)` | `RESTRICT` (but `CASCADE` from `disclosure_purpose_requirements`) |
| `parent_requirement_id` → self | `SET NULL` |
| `disclosure_report_instance_binding.report_id` → `report_generation_queue(id)` | `CASCADE` |
| `disclosure_values.report_version_id` → `report_versions(id)` | `CASCADE` |
| `disclosure_value_evidence.disclosure_value_id` → `disclosure_values(id)` | `CASCADE` |
| → `calculation_snapshots(id)`, `emissions_logs(id)`, `manual_extraction_items(id)`, `organization_files(id)` | `SET NULL` (mirrors D33) |

**Rationale:** version-bound catalogue rows are `RESTRICT` so a finalised report's binding can never be silently deleted (D15). Evidence references are `SET NULL` so history is preserved if a source is removed (D33 precedent).

---

## 11. Indexes

**[PROPOSED]** PostgreSQL does **not** auto-index foreign keys, so every FK gets an index. Exact set:

| Index | Table | Columns / predicate |
|---|---|---|
| `idx_dfv_framework_status` | `disclosure_framework_versions` | `(framework_id, status)` |
| `idx_drv_framework_version` | `disclosure_requirement_versions` | `(framework_version_id)` |
| `idx_drv_framework_class` | `disclosure_requirement_versions` | `(framework_version_id, requirement_class)` |
| `idx_drv_parent` | `disclosure_requirement_versions` | `(parent_requirement_id)` |
| `idx_drm_requirement` | `disclosure_requirement_mappings` | `(requirement_version_id)` |
| `uq_drm_current` (unique) | `disclosure_requirement_mappings` | `(requirement_version_id) WHERE is_current` |
| `idx_dpv_purpose` | `disclosure_report_purpose_versions` | `(purpose_id)` |
| `idx_dpr_purpose_version` | `disclosure_purpose_requirements` | `(purpose_version_id, display_order)` |
| `idx_dpr_requirement` | `disclosure_purpose_requirements` | `(requirement_version_id)` |
| `idx_daa_org_fw_period` | `disclosure_applicability_assessments` | `(organization_id, framework_version_id, reporting_period_start)` |
| `idx_daa_framework_version` | `disclosure_applicability_assessments` | `(framework_version_id)` |
| `idx_drib_report` (unique) | `disclosure_report_instance_binding` | `(report_id)` |
| `idx_drib_org` | `disclosure_report_instance_binding` | `(organization_id)` |
| `idx_drib_purpose_version` | `disclosure_report_instance_binding` | `(purpose_version_id)` |
| `idx_drib_applicability` | `disclosure_report_instance_binding` | `(applicability_assessment_id)` |
| `idx_dv_report_version` | `disclosure_values` | `(report_version_id)` |
| `idx_dv_org` | `disclosure_values` | `(organization_id)` |
| `idx_dv_requirement` | `disclosure_values` | `(requirement_version_id)` |
| `idx_dv_mapping` | `disclosure_values` | `(requirement_mapping_id)` |
| `idx_dve_value` | `disclosure_value_evidence` | `(disclosure_value_id)` |
| `idx_dve_calc` | `disclosure_value_evidence` | `(calculation_snapshot_id)` |
| `idx_dve_source_item` | `disclosure_value_evidence` | `(source_item_id)` |
| `idx_dve_source_file` | `disclosure_value_evidence` | `(source_file_id)` |

**No composite/covering indexes beyond those above** are proposed; the value tables are low-volume per report version, and the catalogue tables are tiny.

---

## 12. Relationships / Cardinalities

**[PROPOSED]** Derived from the design (§9, §18) and the repository spine.

```text
disclosure_frameworks  (global)
   1 ──── n  disclosure_framework_versions (global)
                    1 ──── n  disclosure_requirement_versions (global)
                                    1 ──── n  disclosure_requirement_mappings (global, one current)
                                    1 ──── n  disclosure_purpose_requirements
                                                        n ──── 1  disclosure_report_purpose_versions
                                                                         n ──── 1  disclosure_report_purposes (global)

organizations  (tenant root)
   1 ──── n  disclosure_applicability_assessments
   1 ──── n  disclosure_report_instance_binding ──── 1  report_generation_queue (existing)
                                    │                     └─ 1 ── n report_versions (existing)
                                    ├─ n ── 1 disclosure_report_purpose_versions
                                    └─ 0..1 ── 1 disclosure_applicability_assessments

report_versions (existing, version spine)
   1 ──── n  disclosure_values ──── n ── 1  disclosure_requirement_versions
                     │              └─ 0..1 ── 1 disclosure_requirement_mappings
                     1 ──── n  disclosure_value_evidence
                                     ├─ 0..1 ── 1 calculation_snapshots (existing, immutable)
                                     ├─ 0..1 ── 1 emissions_logs (existing)
                                     ├─ 0..1 ── 1 manual_extraction_items (existing)
                                     └─ 0..1 ── 1 organization_files (existing)
```

| Parent → Child | Cardinality | Required? | FK | Delete | Version semantics | Tenant semantics |
|---|---|---|---|---|---|---|
| framework → framework_versions | 1:N | required | `framework_id` | RESTRICT | versions immutable once referenced | global |
| framework_version → requirement_versions | 1:N | required | `framework_version_id` | RESTRICT | new row per change | global |
| requirement_version → mappings | 1:N | optional | `requirement_version_id` | RESTRICT | one `is_current` per requirement | global |
| requirement_version → purpose_requirements | 1:N | optional | `requirement_version_id` | RESTRICT | via purpose version | global |
| purpose → purpose_versions | 1:N | required | `purpose_id` | RESTRICT | one ACTIVE per purpose | global |
| purpose_version → purpose_requirements | 1:N | required | `purpose_version_id` | CASCADE | — | global |
| organization → applicability_assessments | 1:N | required | `organization_id` | CASCADE | append-only (`version`) | org-scoped |
| organization → instance_binding | 1:N | required | `organization_id` | CASCADE | one per report | org-scoped |
| report_instance → instance_binding | 1:1 | required | `report_id` | CASCADE | — | org-scoped |
| purpose_version → instance_binding | 1:N | required | `purpose_version_id` | RESTRICT | — | org-scoped |
| applicability → instance_binding | 1:0..1 | optional | `applicability_assessment_id` | SET NULL | — | org-scoped |
| report_version → values | 1:N | required | `report_version_id` | CASCADE | new version ⇒ new value set | org-scoped |
| requirement_version → values | 1:N | required | `requirement_version_id` | RESTRICT | — | global→org read |
| mapping → values | 1:0..1 | optional | `requirement_mapping_id` | RESTRICT | — | global→org read |
| value → value_evidence | 1:N | optional | `disclosure_value_id` | CASCADE | — | org-scoped |
| calculation_snapshot → value_evidence | 1:0..n | optional | `calculation_snapshot_id` | SET NULL | snapshot immutable | org-scoped |

**Guarantees:** framework/version uniqueness (`(framework_id, version_label)`); requirement identity is
scoped to a version (`(framework_version_id, requirement_code)`), so the same concept across versions is
**distinct rows** and cannot contaminate; one value per requirement per report version; one binding per
report instance; one current mapping per requirement. **Cross-tenant prevention** is an app-layer +
verification invariant (§25, §27), because `report_versions`/`report_generation_queue` are joined by id,
not by a composite tenant key.

---

## 13. Ownership / Tenant / Entity Scope

**[PROPOSED]** Derived from design §18.2/§19.1.

| Table | Global or tenant | `organization_id` | Entity/PE scope | Write owner | Read owner |
|---|---|---|---|---|---|
| `disclosure_frameworks` | **Global** | none | n/a | Platform/internal (service role) | all authenticated |
| `disclosure_framework_versions` | **Global** | none | n/a | Platform/internal | all authenticated |
| `disclosure_requirement_versions` | **Global** | none | n/a | Platform/internal | all authenticated |
| `disclosure_requirement_mappings` | **Global** | none | n/a | Platform/internal | all authenticated |
| `disclosure_report_purposes` | **Global** | none | n/a | Platform/internal | all authenticated |
| `disclosure_report_purpose_versions` | **Global** | none | n/a | Platform/internal | all authenticated |
| `disclosure_purpose_requirements` | **Global** | none | n/a | Platform/internal | all authenticated |
| `disclosure_applicability_assessments` | **Tenant** | NN | entity/facility context inside `characteristic_snapshot` | Customer Owner/Admin; platform | Org members; consultant (engagement) |
| `disclosure_report_instance_binding` | **Tenant** | NN | follows report instance | follows `report_generation_queue` authz | same |
| `disclosure_values` | **Tenant** | NN | inherited from calculations | system-derived (service role); customer-input fields per `P3` | Org members; consultant (engagement); internal staff |
| `disclosure_value_evidence` | **Tenant** | NN | inherited | system-derived (service role) | Org members; consultant (engagement); internal staff |

**Consultant access** is engagement-scoped, never portfolio-wide (design §19.1/§19.2 item 6). **PE boundary**
is preserved: PE users see assigned work, not unrestricted customer documents (D33/D32). **Customer Viewer**
is read-only. No entity column is added in B1 (entity context is *recorded*, not a new scope dimension).

---

## 14. Framework / Version Semantics

**[CONFIRMED]** from design §6 and D14/D15/D17:

1. **Three frameworks** are registered (D1): `GHG_PROTOCOL` (primary accounting foundation, D8), `UK_SECR`, `ESRS_E1`.
2. **Every requirement belongs to a framework *version***, never to a framework directly. A regulatory change creates a **new version row**; existing rows are never mutated (§6.4).
3. **`status`** records legal state: `IN_FORCE` · `ADOPTED_NOT_IN_FORCE` · `SUPERSEDED` · `WITHDRAWN`. The **2026 Simplified ESRS** is represented as `ADOPTED_NOT_IN_FORCE` with **no** `applicable_from` (design §6.5; enforced by CHECK).
4. **Source governance is in the model** (D17): `source_tier` ∈ {1,2,3}; only Tier 1/2 may create/amend a requirement version.
5. **Historical binding (D15):** a finalised report binds to `framework_version_id`; referenced version/requirement/mapping rows are **never mutated** — a correction is a new version and the prior row becomes `SUPERSEDED`.
6. **No global "current framework".** A single "current" concept is factually wrong (design §6.2) and is not modelled.

---

## 15. Requirement Semantics

**[CONFIRMED]** from design §7, D9/D12:

1. **`requirement_class`** is a property of the **requirement version** — what the standard says: `REQUIRED`, `CONDITIONAL`, `OPTIONAL`, `NOT_APPLICABLE`, `CUSTOMER_INPUT_REQUIRED`, `UNDETERMINED`, `NOT_SUPPORTED`, `FUTURE` (design §7.2).
2. **`carbontally_capability`** is a **separate** concept on the same row: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `STRUCTURED_INPUT_REQUIRED`, `EXTERNAL_INPUT_REQUIRED`, `MISSING_CAPABILITY`, `FUTURE`, `NOT_APPLICABLE_TO_PRODUCT` (design §7.3).
3. **No `is_required` boolean.** The two dimensions above replace it (semantic invariant §8.4).
4. **Mappings are controlled**, not a DSL: `source_kind` is a closed set; `aggregation` is a closed set; `source_selector` is a schema-validated JSON object (no code/SQL/expressions).
5. **Unresolved identifiers are structurally safe:** `identifier_status='UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION'` **forbids** an `official_identifier` value; re-keying to official identifiers is a **data update**, not a schema change (design §12.1). **No ESRS identifier is invented.**

---

## 16. Applicability Semantics

**[CONFIRMED]** from design §8, D13, and the `APPL` decision:

1. Applicability is stored **per (organisation, framework_version, explicit period)** and is **append-only** — a re-assessment is a new row (`version`), never an update.
2. States: `APPLIES` · `DOES_NOT_APPLY` · `UNDETERMINED` · `CUSTOMER_INPUT_REQUIRED`. **`UNDETERMINED` is first-class** and must never be coerced to `DOES_NOT_APPLY`.
3. Every assessment records a **`basis`** (the cited rule/source) — auditable, not a bare boolean.
4. `characteristic_snapshot` records the **customer facts relied on and their source** (drawn from existing `organizations` columns: `company_size`, `is_public`, `is_listed`, `business_structure`, `country`, `financial_year_end`, `reporting_standard`, `sustainability_standard`, `vat_region`, `secr_enabled`, `esrs_enabled`, …).
5. **No legal-advice semantics.** The row records facts + basis; it never asserts a legal determination (APPL).
6. **Finalisation interaction (`DM-5`):** an applicable, required requirement whose effective state is `CUSTOMER_INPUT_REQUIRED` with missing input **blocks finalisation** unless an approved workflow resolves it; `NOT_SUPPORTED` must be **surfaced honestly**. (Finalisation logic itself is B4; B1 provides the state that B4 reads.)

---

## 17. Disclosure Value Semantics

**[CONFIRMED]** from design §13/§18 and D2/D12/D15:

1. **One value per (report_version, requirement_version)** (`UNIQUE`), so duplicate disclosure records are impossible.
2. A value **projects** the authoritative calculation foundation; it **never recomputes** an emission. Aggregation is summation of persisted `co2e_snapshots.co2e_kg`; factor provenance is **inherited**, not re-derived.
3. **`effective_class`** is the **authoritative home** for the *derived* requirement/applicability/capability outcome for this organisation/period (from applicability); it is stored **without** overwriting `requirement_class` on the requirement version. **`CUSTOMER_INPUT_REQUIRED` ≠ `NOT_SUPPORTED`** (PQ-3 RATIFIED).
4. **`value_status`** is a **separate, narrow materialisation lifecycle** — `PENDING` | `RESOLVED` | `UNRESOLVED`. It must **not** duplicate or reinterpret `requirement_class`, applicability, `carbontally_capability` or `effective_class` (PQ-3 RATIFIED).
5. **`source_kind`** is copied from the mapping used; provenance flows through `disclosure_value_evidence` into the immutable `calculation_snapshots` (`content_hash`, `request_id`).
6. **Immutability (PQ-4 RATIFIED WITH CONDITION):** values for a report version at `APPROVED`/`FINAL` are never mutated; subsequent changes create a new report version and a new value set (D15). Enforced at the application/service layer in B1.
7. **Evidence is referenced, never copied** — no storage objects, no signed URLs inside values (design §19.2 item 3).

---

## 18. Purpose / `report_type` Binding

**[CONFIRMED]** from design §9 and `DM-2`:

1. **`disclosure_report_purposes.code`** carries the reporting **intent** (`ANNUAL_CARBON`, `MANAGEMENT`, `UK_SECR`, `ESRS_E1_QUANT`, D6-R). **`report_generation_queue.report_type`** remains the **engine capability** and is **untouched** (still `annual` today).
2. They are **separate**. The instance binding (`report_id` + `purpose_version_id`) is where intent meets instance; the purpose code is **never** written into `report_type`.
3. **A purpose is not a framework** (design §9.2): all four purposes read the **same** disclosure values; a purpose version is an **ordering/subsetting** over requirement versions (`display_order`).
4. **No competing report spine** (design §9.3): the instance is `report_generation_queue.id`; the version is `report_versions`. No new report/version table is created.

---

## 19. Customer Input Semantics

**[CONFIRMED]** from `P3`, `DM-5`, design §12.3:

1. **Customer-editable** (subject to role): customer-owned facts, permitted narrative, permitted commentary, explicitly allowed applicability selections, and the SECR intensity denominator **selection + rationale**.
2. **System-authoritative (never customer-editable):** calculated emissions, provenance, emission factors, system-derived values, immutable calculation snapshots, and the value→evidence relationships.
3. **`CUSTOMER_INPUT_REQUIRED`** means CarbonTally **has** the capability but the customer-provided information is absent → blocks finalisation unless an approved workflow resolves it (`DM-5`).
4. **`NOT_SUPPORTED`** means the applicable disclosure is outside current capability → **surfaced honestly**, never omitted, never presented as compliant (`DM-5`).
5. Where a Layer-2 / qualitative requirement is customer-supplied, the value records the **customer-input vs system-derived** distinction (design §12.3), mirroring `domain/evidence.py`.

---

## 20. Historical Reproducibility

**[CONFIRMED]** from D15 / design §6.4:

A finalised `report_version` remains reproducible because it is bound to the exact versions used:

```text
finalized report_version
   ├── disclosure_report_instance_binding.framework_version_id   (via purpose → requirement versions)
   ├── disclosure_values.requirement_version_id                  (exact requirement text)
   ├── disclosure_values.requirement_mapping_id                  (exact mapping)
   ├── disclosure_value_evidence.calculation_snapshot_id + content_hash
   ├── evidence references (source_item_id / source_file_id / source_page)
   └── report_versions.template/version (presentation)
```

**Rule:** framework/requirement/mapping/purpose rows referenced by any finalised report are **never
mutated**; a correction creates a **new version row** and the prior row becomes `SUPERSEDED` (design §6.4).
Because `report_versions` is append-only with `UNIQUE(report_id, version_number)`, a new version produces
a **new value set** and historical values are untouched.

---

## 21. Historical Backfill Rules

**[CONFIRMED]** from `DM-7` (incl. the Gate 0 refinement) and the line-item forensic.

| Class | Definition | B1-specific items |
|---|---|---|
| **CLASS 1** — deterministic/idempotent safe backfill | Allowed; reproducible from persisted data; idempotent key; duplicate-proof | **None in B1.** The framework/version/requirement/purpose catalogues are **reference seed data**, not backfill. No historical row maps deterministically to a B1 table. |
| **CLASS 2** — possible only with a separately authorised transformation | Requires its own authorised + verified task | `evidence_line_items` population from persisted `line_items[]` (CSV/XLSX + AI-line documents); `calculation_snapshots.source_line_item_id` backfill where a deterministic match exists. **These are B2**, not B1. |
| **CLASS 3** — prohibited / must not be performed | Forbidden | Re-parsing flat PDF/IMAGE records to manufacture line structure; rewriting any historical row to manufacture provenance; silent historical re-extraction. |

**B1 statement:** **B1 performs no historical backfill.** Existing reports stay valid and simply carry no
disclosure values until values are materialised for them (design §20). Historical reports are never
retro-fitted silently.

**If B2 later performs a Class-1 backfill**, it must specify: source (`extracted_data.line_items` /
`mapped_data.line_items`); deterministic transformation; idempotency key (a `payload_hash` per line);
duplicate prevention (unique key); unmatched rows stay `NULL` (honest); rollback (delete only rows created
by the backfill run); verification (row counts reconcile, zero duplicates on re-run).

---

## 22. Migration Strategy

**[PROPOSED]** given the repository's **21 applied / 34 outstanding** production state.

1. **Placement:** one new migration after the highest existing timestamp —
   `supabase/migrations/20260914000000_p8_b1_disclosure_model_foundation.sql`.
2. **One migration or several?** **One migration for B1.** All 11 tables are one cohesive additive unit; a
   single, idempotent file gives one reviewable rollback boundary. Ordering *within* the file is dependency
   order: `disclosure_frameworks` → `_framework_versions` → `_requirement_versions` →
   `_requirement_mappings` → `_report_purposes` → `_report_purpose_versions` → `_purpose_requirements` →
   `_applicability_assessments` → `_report_instance_binding` → `_values` → `_value_evidence`.
3. **Idempotency:** `CREATE TABLE IF NOT EXISTS`; `CREATE INDEX IF NOT EXISTS`; constraint additions
   wrapped in `DO $$ … pg_constraint …` guards (the D33 pattern). Re-running is a no-op.
4. **Dependencies:** B1 depends only on **`organizations`, `report_generation_queue`, `report_versions`,
   `calculation_snapshots`, `emissions_logs`, `manual_extraction_items`, `organization_files`** — all in
   the init schema / early migrations. **B1 does NOT depend on the P8 lifecycle migration `20260913000000`**
   for table creation (it references `report_versions(id)`, which exists since init); it assumes the
   lifecycle `status` column only for runtime immutability semantics (B4).
5. **Ordering safety:** the migration is timestamp-ordered after all existing files and introduces **no**
   change to any existing object, so relative ordering vs the 34 outstanding migrations is not material
   for correctness — **except** that the outstanding `20260831030000_tenant_org_id_not_null.sql` governs an
   invariant B1 relies on. B1 declares `organization_id NOT NULL` on its own tables regardless.
6. **Independent deployability:** **Yes in a dev/QA environment** — the migration applies on its own.
7. **Do the 34 outstanding migrations block B1?** **They are a DEPLOYMENT blocker for production, not a
   design blocker for B1.** B1 is additive and applies cleanly on a schema at the 21-migration level.
   **[CLOSED — PQ-5 RATIFIED]** B1 may be implemented and verified in **dev/QA** independently, but **no
   production deployment is authorised** until the outstanding migration set is reconciled and a
   production migration strategy is independently verified. This contract does **not** claim production
   deployability.
8. **Production migration reconciliation:** **required before production deployment** (PQ-5 CLOSED — §28); the RLS
   baseline already flags it as a P0 deployment concern.
9. **Modify an existing migration?** **NO.** B1 modifies **no** existing migration file. No exception needed.
10. **Fresh additive migration?** **YES** — purely additive; no `DROP`, no `ALTER` of an existing column.

**Not performed here:** no migration was created, executed, or applied to Supabase.

---

## 23. RLS Policy Intent

**[PROPOSED] Intent only — no policy is created, enabled or modified in this task.** RLS in this
repository is **not currently a reliable boundary** (97/104 production tables have RLS disabled and `anon`
holds `GRANT ALL`). Therefore **app-layer authorization is the enforced boundary** (§24), and RLS policy
text is authored as defence-in-depth for the eventual remediation.

### A. B1 schema-level security requirements (in scope for B1)

| Table class | RLS | Policy intent |
|---|---|---|
| **Global catalogues** (7 tables) | `ENABLE ROW LEVEL SECURITY` | `SELECT` to `authenticated` (read-all). **No** `INSERT`/`UPDATE`/`DELETE` policy for `anon`/`authenticated` → writes are **service-role only** (platform-controlled). B1 explicitly grants **no** `anon` access on these new tables. |
| **Organisation-scoped** (4 tables: applicability, instance_binding, values, value_evidence) | `ENABLE ROW LEVEL SECURITY` | `SELECT` where `organization_id` ∈ the caller's organisations (via `organization_members`); `INSERT`/`UPDATE`/`DELETE` restricted to the owning organisation with admin/member authority. **Service role** bypasses. **Consultant** access follows the active engagement grant; **PE** boundary preserved; **Viewer** read-only. |

**B1 must not** create permissive policies to make tests pass, and **must not** rely on RLS as the
authorization mechanism (§24).

### B. Broader RLS remediation (OUT of B1 scope)

The 97-table RLS baseline, `anon` `GRANT ALL` revocation, the recursive-policy fix
(`20260822000000_p9_rls_recursion_fix`), and column-privilege enumeration are a **separate security
workstream** (`CARBONTALLY_PRODUCTION_RLS_SECURITY_HOLD_AND_REMEDIATION_REGISTER_20260912.md`). B1 must
**not** attempt them. The **only** grant behaviour B1 introduces is on its **own new** tables (no `anon`
grants); it modifies **no** existing table's grants or policies.

**Per-table actor-scope summary:** global catalogues — read all authenticated, write platform/service-role;
applicability — Customer Owner/Admin write, Member/Viewer read, Consultant per engagement; instance
binding — follows `report_generation_queue` authorization; values/value_evidence — system-derived writes
(service role), customer-input fields per `P3`, read org-scoped. **Cross-tenant references must be
prevented** (app-layer + FK + verification; §25/§27).

---

## 24. API / Domain Boundary

**[PROPOSED]** No endpoint is implemented in B1. Intended boundary only.

| B1 capability | Domain responsibility | Likely module ownership | Read path | Write path | Actor authz | Scope | Idempotency | Audit | API in B1? |
|---|---|---|---|---|---|---|---|---|---|
| Framework/version catalogue | Reference data | `domain/disclosure.py` (new) + `data/disclosure.py` (new) | repository read | platform/service-role | internal only | global | n/a (seed) | `CAT_REPORT`-class entries | **Later (B3 exposure)** |
| Requirement catalogue + mappings | Requirement model | same | repository read | platform/service-role | internal only | global | n/a | audit on change | **Later (B3)** |
| Purpose catalogue + versioning | Purpose model | same | repository read | platform/service-role | internal only | global | n/a | audit on change | **Later (B3)** |
| Applicability assessment | Applicability | same | org-scoped | Customer Owner/Admin (or system) | `require_org_admin` (write) / `require_org_member` (read) | org | append-only (new row) | audit | **Later (B3)** |
| Instance binding | Reporting context | same | follows report authz | system (on report creation) | `ensure_org_access` | org | one per report (`UNIQUE`) | audit | **Later (B3)** |
| Disclosure values | Value projection | same | org-scoped | **system-derived (service role)**; customer-input fields per `P3` | `require_org_member` (read) | org | `UNIQUE(report_version, requirement_version)` | audit | **Later (B3)** |
| Value→evidence | Provenance link | same | org-scoped | system | `ensure_org_access` | org | `UNIQUE(value, snapshot)` | audit | **B4 (drill-down)** |

**Reuse, do not re-abstract:** B1 introduces **no** new provider/service abstraction. It adds one
`domain/disclosure.py` + one `data/disclosure.py` following the existing repository pattern
(`RepositoryBundle` / `dependencies.get_repositories`). **No new authorization or audit mechanism** — the
existing guards (`require_org_member`, `require_org_admin`, `ensure_org_access`) and the existing
`AuditRepository` taxonomy are reused.

**API exposure is explicitly deferred.** B1 establishes **schema + domain boundary only**. Read/write
endpoints belong to B3 (integration/projections) and B4 (drill-down); the exact endpoint surface requires
the PO-approved B1 batch to complete first.

---

## 25. Idempotency

**[PROPOSED]** B1's structural invariants and idempotency guarantees:

| Operation | Idempotency mechanism | Repeat behaviour |
|---|---|---|
| B1 migration | `IF NOT EXISTS` + `pg_constraint` guards | Re-run = no-op |
| Reference seed (frameworks/versions/purposes) | `INSERT … ON CONFLICT (code/unique key) DO NOTHING` | Re-run = no duplicates |
| Applicability assessment | append-only `version`; a re-assessment is a **new row** | Deterministic; prior rows untouched |
| Instance binding | `UNIQUE (report_id)` | One binding per report; re-bind = update, never duplicate |
| Disclosure values | `UNIQUE (report_version_id, requirement_version_id)` | Deterministic set per report version; re-materialise = upsert-on-unique, never duplicates |
| Value→evidence | `UNIQUE (disclosure_value_id, calculation_snapshot_id)` | Re-linking = no duplicates |
| Catalogue changes | new version row + `SUPERSEDED` on the prior | Never an in-place mutation |

**Cross-tenant integrity invariant (app-layer, verified):** `disclosure_values.organization_id` MUST equal
the organisation of `report_versions.report_id → report_generation_queue.organization_id`; likewise for
`disclosure_value_evidence`. **No code path may create a row whose `organization_id` differs from the
owning report's organisation.** This is enforced by the B1 service layer and proven by a verification test
(§27.C) because the FK chain (`report_versions.report_id`) has no composite tenant key.

---

## 26. Audit Requirements

**[CONFIRMED]/[PROPOSED]** Reuse the existing append-only `audit_trail` + `AuditLogger`/`AuditRepository`
taxonomy (no new mechanism). B1 should emit:

| Event | Actor | Target table | When |
|---|---|---|---|
| Framework/version/requirement/mapping created or versioned | internal staff | respective table | on catalogue write |
| Purpose version activated/superseded | internal staff | purpose tables | on purpose write |
| Applicability assessed | Customer Owner/Admin or system | `disclosure_applicability_assessments` | on new assessment row |
| Report instance bound to purpose | system | `disclosure_report_instance_binding` | on binding create |
| Disclosure value materialised | system | `disclosure_values` | on value write |
| Value→evidence link created | system | `disclosure_value_evidence` | on link write |

**Rules:** append-only; every write records `performed_by` + before/after; **audit ≠ telemetry**; no
secrets, signed URLs or payload dumps in audit rows. B1 introduces **no** new audit table or taxonomy.

---

## 27. Test / Verification Contract

### A. Implementation tests B1 should add (authored with B1)

1. Schema tests: each table exists; column names/types; PK; unique constraints; CHECK enumerations; FK
   delete semantics.
2. Constraint tests: `ADOPTED_NOT_IN_FORCE ⇒ applicable_from IS NULL`; `identifier_status='RESOLVED' OR
   official_identifier IS NULL`; period order; partial-unique `is_current` mapping; `UNIQUE` values.
3. Migration idempotency test: apply the B1 migration twice → no error, no duplicate objects.
4. Seed idempotency test: re-run the reference seed → no duplicate frameworks/versions/purposes.

### B. Semantic verification

- framework/version binding: a requirement belongs to exactly one framework version; versions are distinct rows.
- requirement semantics: `requirement_class` and `carbontally_capability` are independent; no `is_required` boolean exists.
- applicability semantics: `UNDETERMINED` persists and is never coerced; `basis` is recorded.
- purpose binding: `purpose_code` ≠ `report_type`; `report_type` values unchanged.
- period semantics: explicit start/end are stored and used; where an instance binding references an applicability assessment, the two period pairs **MUST agree** (the binding is authoritative) — PQ-2.
- value semantics: one value per (report version, requirement); `effective_class` carries the derived outcome (`CUSTOMER_INPUT_REQUIRED` ≠ `NOT_SUPPORTED`); `value_status` ∈ {`PENDING`,`RESOLVED`,`UNRESOLVED`} **only** and never duplicates `effective_class`.

### C. Security verification (independent; ALLOW **and** DENY)

- **Tenant isolation:** Org A cannot read/write Org B's applicability/values/evidence.
- **Actor scope:** Customer Viewer cannot mutate; Member cannot perform Owner/Admin operations; Consultant
  is engagement-scoped (denied outside the engagement); PE is entity-scoped.
- **Global catalogue protection:** an `authenticated`/`anon` caller cannot INSERT/UPDATE/DELETE a global
  catalogue row; `anon` holds no grant on the new tables.
- **Cross-tenant reference attempts** (value↔report, evidence↔value with mismatched org) are rejected.
- **Cross-framework-version contamination:** a value for one framework version cannot reference a
  requirement from another version's mapping set.

### D. Idempotency verification

- Repeated seed → no duplicates.
- Repeated value materialisation → no duplicate values (unique holds).
- Repeated evidence link → no duplicate links.

### E. Historical reproducibility verification

- A catalogue/requirement/mapping edit **after** a report is finalised does **not** change the finalised
  report's resolved values; it creates a new version.

### F. Regression verification

- Existing report lifecycle (S1/S3) still passes (six states, immutability, new-version supersede).
- Existing calculation/snapshot behaviour is unchanged (B1 reads, never writes, `calculation_snapshots`).
- Unrelated functionality (extraction, factor matching, legacy route) is untouched.

### G. Migration verification

- Fresh application of the full migration set (dev/QA) succeeds.
- B1's migration applies on the current baseline and is idempotent.
- No destructive statement; no existing object altered.

**Separation:** §27.A is authored **with** B1 (implementation tests). §27.B–G are the **independent
verification** that must be performed **after** B1 implementation, before B2 begins (roadmap gate **V1**).

---

## 28. Open Questions / PO Decisions Required

**[CLOSED — PO RATIFIED]** All eight B1 PO decisions (PQ-1…PQ-8) were formally closed by task
`CT-P8-B1-PO-DECISION-RATIFICATION-20260912-011`. The authoritative decision record is
`CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md`; the analytical basis is
`docs/cline/reports/CT-P8-B1-PO-DECISION-CLOSURE-20260912-010.md`. **No B1 PO decision remains open.**

| ID | Decision | Status | Final PO decision | B1 consequence |
|---|---|---|---|---|
| **PQ-1** | Intensity catalogue placement (B1 vs B3) | **CLOSED — RATIFIED WITH CONDITION** | Intensity remains a **B3** responsibility; B1 creates **no** intensity table or implementation; the `INTENSITY_RATIO` semantic concept is reserved where the contract already requires it | B1 stays **11 tables** |
| **PQ-2** | Explicit reporting-period placement | **CLOSED — RATIFIED WITH CONDITION** | Explicit `reporting_period_start`/`_end` on **both** `disclosure_applicability_assessments` and `disclosure_report_instance_binding`; the instance binding is authoritative; the agreement invariant is enforced/documented; no permanent calendar-year assumption | B1 unchanged (11 tables); invariant added to verification |
| **PQ-3** | `disclosure_values.value_status` vocabulary | **CLOSED — RATIFIED** | `effective_class` **remains authoritative** (not removed/replaced); `value_status` is a separate narrow materialisation lifecycle: `PENDING` · `RESOLVED` · `UNRESOLVED`; it must **not** duplicate/reinterpret `requirement_class`, applicability, `carbontally_capability` or `effective_class` | §9.10/§10/§17/§27 reconciled |
| **PQ-4** | Immutability enforcement | **CLOSED — RATIFIED WITH CONDITION** | Application/service-layer enforcement for B1, verified by tests; **no** DB trigger required for B1; DB hardening is a later separate bounded task | §9.10/§17/§25 |
| **PQ-5** | 34 outstanding migrations | **CLOSED — RATIFIED** | Deployment/reconciliation **gate**, not an architectural reason to redesign B1; B1 may be implemented and verified in dev/QA independently; **no** production deployment until the outstanding set is reconciled and a strategy independently verified | §22 unchanged |
| **PQ-6** | Reference-seed scope | **CLOSED — RATIFIED WITH CONDITION** | B1 may seed/reference framework identities, framework-version identities and report-purpose identities **only** where supported by authoritative evidence and/or explicit PO confirmation; version rows must **not** be invented; **no invented E1 requirement identifiers**; the 2026 ESRS is `ADOPTED_NOT_IN_FORCE` only where the authoritative-evidence record supports it; requirement/mapping content remains a later batch | §28 note |
| **PQ-7** | `E1-COV` / E1 coverage | **CLOSED — RATIFIED** | Unresolved ESRS E1 evidence does **not** block B1 architecture/implementation; **`E1-COV` remains CONDITIONAL**; only authoritatively verified E1 requirements/identifiers may be production-supported; no invented E1 IDs or mappings | §15 unchanged |
| **PQ-8** | Batch split | **CLOSED — RATIFIED** | Use the delivery sequence **B1 → B2 → B3 → B4** (with the supporting/remediation tracks and gates); a delivery-sequencing decision that removes **no** architecture element; **B1 remains limited to the B1 contract** | §6 unchanged |

**No ESRS identifier, threshold, deadline, denominator or materiality value is invented anywhere in this
contract.** Where unresolved, the contract preserves the gated status.

---

## 29. Implementation Readiness Verdict

### `B1 IMPLEMENTATION CONTRACT COMPLETE — PO DECISIONS CLOSED — READY FOR A SEPARATE IMPLEMENTATION AUTHORISATION TASK`

**Basis:**

1. The B1 tables, columns, types, nullability, defaults, keys, constraints, indexes, relationships,
   ownership, semantics, migration strategy, RLS intent, API/domain boundary, idempotency, audit and
   verification contract are all specified exactly (§§4–27), grounded in the ratified design/decisions and
   the actual repository schema.
2. **B1 is purely additive** (11 new tables, zero modified objects) and **idempotent**.
3. The **B1/B2 boundary is established without inventing design**: B1 needs **no** placeholder, and
   `evidence_line_items`/`source_line_item_id` stay in B2 (§6).
4. **All eight B1 PO decisions (PQ-1…PQ-8) are CLOSED** (task `CT-P8-B1-PO-DECISION-RATIFICATION-20260912-011`;
   authoritative record `CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md`). No B1 PO decision
   remains open. The only cross-document disagreement (design MVP list vs roadmap batch split) was a
   **delivery-sequencing** conflict, recorded — not silently resolved — and now closed by **PQ-8**.
5. **No ESRS identifier is required or invented**; unresolved identifiers are structurally gated
   (`identifier_status` + CHECK) and **PQ-7** confirms E1 evidence does not block B1.
6. The schema reconciles with the **current repository**: it reuses the existing PK/timestamp/tenant
   conventions, the D33 evidence chain, the report/version spine, `calculation_snapshots` immutability and
   the existing guard/audit patterns.
7. **PQ-3 is reconciled** (§9.10/§10/§17/§27): `effective_class` is the authoritative derived-outcome home;
   `value_status` is the narrow `PENDING`/`RESOLVED`/`UNRESOLVED` materialisation lifecycle.

**This verdict is contract-complete and decision-closed, not implementation-complete.** **B1
implementation is NOT authorised by this document** — it requires a **separate, explicit PO
implementation-authorisation task** (roadmap Gate 5). No code, schema, migration, API, frontend, RLS or
production change was made.















