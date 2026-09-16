# CarbonTally — Phase 8 Disclosure Model Design

**Document:** `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md`
**Task reference:** `CT-P8-DISCLOSURE-MODEL-DESIGN-20260912-004`
**Status:** DESIGN OUTPUT — **NOT IMPLEMENTED** — awaiting PO review
**Date:** 2026-09-12
**Type:** Architecture / design only. **No code, schema, migration, API, RLS or production change.**
**Governing decisions:** D1–D17 (`…REPORTING_ARCHITECTURE_PO_RATIFICATION_D1-D17_20260912.md`, PO-RATIFIED)
**Regulatory basis:** `…REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md` §§5–24 (latest status §24.11: `EVIDENCE CLOSURE PARTIAL — PO REVIEW REQUIRED`)
**Final verdict:** `DESIGN COMPLETE — READY FOR PO REVIEW`

---

## 1. Document control

| Item | Value |
|---|---|
| Repository baseline | branch `main`, HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| Evidence tags | **[R]** repository fact (file/migration cited) · **[D]** PO decision · **[V]** verified regulatory fact · **[U]** unresolved · **[I]** interpretation · **[REC]** recommendation · **[NEW]** proposed concept requiring new schema · **[EXT]** proposed extension of existing schema |
| Design scope | Structural/conceptual model for the Disclosure Model layer only |
| Explicit non-scope | Implementation, migrations, APIs, RLS, S4, Phase 8-X, legacy-route disposition, XBRL/iXBRL, generic rules/template engine |
| Deliverable B | `docs/cline/reports/CT-P8-DISCLOSURE-MODEL-DESIGN-20260912-004.md` |
| Verdict discipline | "DESIGN COMPLETE" ≠ "IMPLEMENTATION READY". Gate 5 (implementation) remains **NOT AUTHORIZED** |

**Design-quality rule applied throughout:** every proposed concept states *why it exists*, *which verified requirement requires it*, *how it relates to existing CarbonTally data*, and *whether existing schema already solves it*. Where the existing architecture already solves the problem, this design **reuses it and says so**.

---

## 2. Design objective

Define the **minimum, controlled, versioned Disclosure Model** that sits between CarbonTally's authoritative carbon data and its report presentation, so that:

1. one authoritative calculation foundation feeds **multiple report purposes** (D2, D6-R) without duplicating the calculation engine (D8; ratification §2.1);
2. every reported figure is traceable, **at the most granular source level actually available**, in both directions (report → evidence and evidence → report);
3. **regulatory applicability** is distinguished from **CarbonTally capability** (D12, D13);
4. framework/requirement/mapping/template versions are explicit, so **historical reports remain reproducible** after regulatory change (D14, D15);
5. CarbonTally's **non-assurance** position is structurally enforced, not merely worded (ratification §2.6; Phase 7 boundary).

**Out of scope of this objective:** deciding exact ESRS E1 identifiers ([U] — §25), choosing PO policy values (§26), and any implementation work.

---

## 3. Governing PO decisions

| Decision | Content | Design consequence |
|---|---|---|
| **D1** | Initial frameworks: GHG Protocol Corporate Standard (primary), UK SECR, ESRS E1 quantitative subset. GRI/IFRS S2 deferred | Framework model scoped to **3 frameworks** initially, not hard-coded to them |
| **D2** | `AUTHORITATIVE DATA → DISCLOSURE MODEL → PRESENTATION/TEMPLATE → EXPORT → FROZEN VERSION` | The Disclosure Model is the **canonical reporting layer** (§5) |
| **D3** | Existing 12-section report retained as a **presentation template** only | §16 maps it; no redesign here |
| **D4** | Controlled, versioned, **configuration-driven** mappings; **no** generic unrestricted rules/template engine | §6/§7/§21: enumerated vocabulary, not a DSL |
| **D5** | Hybrid narrative: requirement-bound + bounded optional management commentary; the "7 fields × 4,000 chars" model is **rejected** | §15 binding relationship only; no limits invented |
| **D6-R** | Four report purposes: Annual Carbon, Management, UK SECR, ESRS E1 Quantitative | §9 |
| **D7-R** | ESRS E1 Layer 1 (production) / Layer 2 (structured support) / Layer 3 (external-input & future boundary) | §12 |
| **D8** | GHG Protocol Corporate Standard is the primary accounting foundation; frameworks map to it | §10; §7 mapping concept |
| **D9** | 21 required-content items with rich classification semantics | §7 requirement semantics; §10 |
| **D10** | SECR content list (energy kWh, sources, transport, Scope 1/2/3, gross, prior year, intensity + rationale, methodology, efficiency measures, applicability) | §11 |
| **D11** | SECR intensity ratio: **controlled denominator catalogue**; customer confirms the choice | §11.4 |
| **D12** | Distinguish required / conditional / optional / future; optional GHG content never auto-mandatory | §7.2 |
| **D13** | ESRS E1 applicability-aware; can-produce vs legally-applies vs elective; no legal determination | §8 |
| **D14** | Frameworks, versions, requirements, mappings explicitly versioned; regulatory change = controlled new version | §6 |
| **D15** | Finalized reports bound to the versions used; historical reproducibility | §6.4, §13.5 |
| **D16** | Legacy enhanced-report route = deprecated pending disposition (not this task) | §16.4, §28 |
| **D17** | Authoritative-source-first hierarchy; AI output is not authority | §6.3, §25 |

---

## 4. Product / assurance boundary

**CarbonTally is** a carbon-accounting/reporting platform, a calculation/provenance system, an evidence-backed reporting system and an **audit-ready** reporting platform. **CarbonTally is not** an auditor, assurance provider, regulator, certification body or the customer's statutory filing agent. The customer remains responsible for its reporting and its regulatory submission.

**This boundary is already structurally encoded in the repository; the design reuses it rather than restating a weaker version:**

* `backend/data/reporting.py` defines **`AUDIT_READINESS_LABEL = "AUDIT EVIDENCE READINESS"`** and an explicit non-assurance notice (`AUDIT_NOT_ASSURANCE_NOTICE`): CarbonTally *"provides traceable calculations, evidence, provenance and audit-ready records that can support internal review and independent assurance processes. This is not an assurance opinion, verification, certification or audit conclusion, and CarbonTally is not an independent auditor or verifier."* **[R]**
* Phase 7 payloads carry an explicit `not_assurance` marker **[R]** (Phase 7 closure document).
* The legacy PDF generator (`backend/report_generator.py`) contains a **"6. Compliance Statement"** section and the legacy route emits compliance claims — **the single clearest boundary violation in the live surface**, and it is **D16 disposition work, untouched here**. **[R][D]**

**Design rules that follow (binding on any future implementation):**

1. **No disclosure value may carry a compliance or assurance claim.** Language is limited to *requirement coverage* ("mapped to the SECR requirement for total gross emissions"), never "compliant with", "assured", "certified", "audited". **[REC]**
2. **Approval ≠ assurance.** A version reaching `APPROVED`/`FINAL` records *the organisation's authorised representation for its reporting period* (`report_versions.status`) and never an audit opinion. **[R]**
3. **Optional carbon output never becomes mandatory** (D12). **[D]**
4. **Applicability statements are customer-facing context, not legal determinations** (D13, §8). **[D]**

---

## 5. Authoritative reporting architecture

### 5.1 The ratified chain (D2) — and how it maps onto what already exists

```text
AUTHORITATIVE DATA            →  emissions_logs / calculation_snapshots / manual_extraction_items   [R]
        ↓
CALCULATION / PROVENANCE      →  CalculationEngine + content_hash + factor provenance               [R]
        ↓
EVIDENCE                      →  D33 chain + domain/evidence.py completeness classification         [R]
        ↓
DISCLOSURE MODEL              →  *** THIS DESIGN *** (framework/requirement/applicability/value)
        ↓
NARRATIVE CONTENT             →  requirement-bound narrative + bounded management commentary (S4)
        ↓
REPORT PURPOSE + TEMPLATE     →  report_generation_queue.report_type + template/version
        ↓
EXPORT                        →  GET /{id}/pdf (render_branded_pdf)
        ↓
FROZEN VERSIONED ARTEFACT     →  report_versions (+ status lifecycle) — artefact columns not yet populated
```

**[I] The decisive design observation:** the lower half of this chain **already exists and is verified**. The missing layer is *only* the middle: framework/version → requirement → applicability → disclosure value → narrative binding. The design therefore **adds a small, bounded layer** rather than re-architecting anything.

### 5.2 Layer responsibilities (no duplication)

| Layer | Owner today | Disclosure Model relationship |
|---|---|---|
| Calculation | `backend/engines/calculation.py`, `calculation_snapshots` (**immutable**, SHA-256 `content_hash`, deterministic `request_id`) | **Consumes** only. Must never recompute. §17 |
| Factor provenance | `emission_factors`, `customer_factors`, `import_batches`, `calculation_snapshots.factor_kind/factor_id/customer_factor_id` | **Consumes** (references `factor_id` + `factor_kind`) |
| Evidence | `organization_files` ← `manual_extraction_items` ← `calculation_snapshots.source_item_id` ← `emissions_logs.snapshot_id` | **Consumes**; adds nothing new |
| Presentation | `report_generation.py` (`_SECTION_ORDER`, 12 sections) + `pdf_render.py` | **Feeds** it (§16) |
| Lifecycle | `report_versions` + `status` + `audit_trail` | **Binds** to it (§6.4) |

### 5.3 Scope of change (summary)

```text
NEW concepts:   framework, framework version, requirement, requirement version,
                requirement→data mapping (+ version), report purpose, purpose↔requirement,
                applicability assessment, intensity-ratio definition, disclosure value,
                narrative binding (+ optional management commentary), targets/actions (Layer 2)
EXTENDED:       (none strictly required for the MVP — see §20)
REUSED AS-IS:   calculation_snapshots, emissions_logs, emission_factors, customer_factors,
                import_batches, manual_extraction_items, organization_files, customer_documents,
                report_generation_queue, report_versions, audit_trail, domain_events, units, activity_categories
```

---

## 6. Framework / version model

### 6.1 Proposed concepts

| Concept | Purpose | Key fields | Cardinality | Versioning | Tenant scope | Existing equivalent |
|---|---|---|---|---|---|---|
| **`disclosure_frameworks`** **[NEW]** | Canonical register of the standards CarbonTally maps to (D1) | `code` (GHG_PROTOCOL / UK_SECR / ESRS_E1), `name`, `publisher`, `kind` (accounting_foundation / jurisdiction_statute / eu_standard), `is_primary_foundation` | ~3 rows initially | Framework identity is **stable**; versions live below | Global (platform-controlled) | **None.** No framework table exists anywhere in `supabase/migrations` **[R]** |
| **`disclosure_framework_versions`** **[NEW]** | The versioned binding unit (D14) | `framework_id`, `version_label`, `legal_reference`, `source_tier` (D17), `source_url`, `authoritative_source_date`, `status` (**IN_FORCE / ADOPTED_NOT_IN_FORCE / SUPERSEDED / WITHDRAWN**), `applicable_from`, `applicable_to`, `verified_at` | 1..n per framework | **Immutable once referenced** by a finalized report | Global | **None** **[R]** |
| **`disclosure_requirement_versions`** | A requirement as expressed *in one framework version* | see §7 | 1..n per framework version | Immutable; a change = **new row** | Global | **None** **[R]** |

### 6.2 Why these exist (requirement traceability)

* **D14** explicitly requires frameworks, versions, requirements and mappings to be versioned so that *"a regulatory change creates a controlled new version rather than silently rewriting historical meaning"*. Without a framework-version table there is no object to bind a report to. **[D]**
* **[V]** The regulatory evidence work established that all three frameworks are **live-version-changing**: the CSRD is now a **three-act chain** (2022/2464 + 2025/794 + **2026/470**, OJ L 470, 26.2.2026); the **ESRS 2023 set** (as amended by (EU) 2025/1416) is in force while the **2026 Simplified ESRS is adopted but NOT in force**; UK SECR thresholds changed for financial years beginning on/after **6 April 2025**. A single global "current framework" is therefore **factually wrong** (task §10) and must not be modelled.

### 6.3 Source governance is part of the model (D17)

The framework-version concept carries `source_tier` and `authoritative_source_date`. **[REC]** Only **Tier 1/2** sources may create or amend a requirement version; Tier 3 may inform interpretation only, and AI output may never be the authority (D17). This makes the source hierarchy **auditable rather than procedural**.

### 6.4 Historical reproducibility (D15)

```text
finalized report_version
   ├── framework_version_id            (exact standard version used)
   ├── requirement_version_ids[]       (exact requirement text used)
   ├── mapping_version_id              (exact requirement→data mapping used)
   ├── calculation context             (calculation_snapshots ids + content_hash)
   ├── evidence references             (source_item_id / file_id / source_page)
   ├── narrative binding version       (requirement-bound + management commentary)
   └── template version                (presentation)
```

**[I]** The repository already supplies most of the binding: `report_versions` is keyed `UNIQUE (report_id, version_number)`, `calculation_snapshots` is an **immutable forensic record** with SHA-256 `content_hash`, and `audit_trail` is append-only **at the database level** (trigger `p7_audit_trail_immutable`, which fires for the service role too). The design **adds only the framework/requirement/mapping binding** and relies on existing immutability for the rest. **[R]**

**Rule:** framework/requirement/mapping rows referenced by any finalised report are **never mutated**; a correction creates a new version row and the prior row becomes `SUPERSEDED`. **[REC]**

### 6.5 Where the 2026 ESRS revision sits (D14/D15 boundary)

**[V]** The 2026 Revised/Simplified ESRS must be represented as a **future** `disclosure_framework_versions` row with `status = ADOPTED_NOT_IN_FORCE` and **no** `applicable_from`. **[D]** It is **not** the implementation basis. This is precisely the "future version" representation required by task §10.

---

## 7. Requirement model

### 7.1 Concept

**`disclosure_requirement_versions`** **[NEW]** — one row per *requirement as expressed in one framework version*:

| Field group | Fields | Why it exists |
|---|---|---|
| Identity | `id`, `framework_version_id`, `requirement_code`, `title` | The stable handle referenced by mappings, values and narratives |
| Semantics | `requirement_class` (§7.2), `is_quantitative`, `unit_hint`, `scope_hint`, `gas_hint`, `period_semantics` | Permits applicability + validity evaluation **without a rules engine** (D4) |
| Provenance | `source_locator` (annex/section/page), `authoritative_text_ref`, `source_tier`, `verified_at` | D17; the requirement itself is auditable |
| Grouping | `parent_requirement_id`, `display_order`, `purpose_hint` | Presentation ordering; ESRS 2 ↔ E1 linkage |
| Capability | `carbontally_capability` (§7.3) | Separates **regulatory applicability** from **CarbonTally capability** (D12) |

**[NEW] `disclosure_requirement_mappings`** — the controlled requirement→data binding:

| Field | Why |
|---|---|
| `requirement_version_id` | The requirement being satisfied |
| `mapping_version` | D14: mappings are versioned (a mapping change is a new version) |
| `source_kind` — **enumerated**: `CALCULATION_AGGREGATE` · `EMISSIONS_LOG_AGGREGATE` · `FACTOR_PROVENANCE` · `EVIDENCE_COMPLETENESS` · `ENERGY_ACTIVITY` · `INTENSITY_RATIO` · `PRIOR_PERIOD_VALUE` · `ORG_PROFILE_FACT` · `CUSTOMER_INPUT` | Prevents a DSL: the binding names **one of a closed set** of CarbonTally producers |
| `source_selector` (JSONB, **schema-validated**) | e.g. `{"scope":"1"}`, `{"scope":"2","method":"LOCATION_BASED"}`, `{"scope":"3","category":"CATEGORY_6"}`, `{"gas":"CH4"}` |
| `aggregation` (`SUM` / `SUM_KG_CO2E` / `DISTINCT_COUNT` / `RATIO` / `PASSTHROUGH`) | Closed vocabulary |
| `display_only` (bool) | Non-quantitative requirements (§13) |

**[REC]** The selector vocabulary is an **enumeration owned by application code**, not user-editable. This satisfies D4 ("configuration-driven but not a generic rules engine") while keeping the model specific enough to preserve regulatory meaning.

### 7.2 Requirement classification vocabulary (D9/D12 — mandatory, not a boolean)

| `requirement_class` | Meaning | Engine behaviour |
|---|---|---|
| `REQUIRED` | Must be disclosed for an in-scope reporter | Missing ⇒ the report cannot finalise |
| `CONDITIONAL` | Required only when a stated condition holds (base year exists, Scope 3 relevant, etc.) | Condition evaluated from applicability + data |
| `OPTIONAL` | Permitted, never mandatory (D12) | Shown when data exists; never blocks |
| `NOT_APPLICABLE` | Established as not applying to this entity/period | Suppressed, **with the basis recorded** |
| `CUSTOMER_INPUT_REQUIRED` | CarbonTally cannot derive it | Blocks finalisation until supplied or explicitly waived |
| `UNDETERMINED` | Facts insufficient to decide | **Never** silently treated as not-applicable |
| `NOT_SUPPORTED` | CarbonTally has no capability yet | Surfaced honestly, never hidden |
| `FUTURE` | Belongs to a not-in-force framework version | Not evaluated for the current period |

**[REC] The single most important semantic decision in this design:** `requirement_class` is a property of the **requirement version** (what the law says), while the *effective* class for a given organisation and period is **derived** from applicability (§8). The two must never be conflated or overwritten — this is exactly what D12 and D13 require, and it is the reason a boolean cannot work.

### 7.3 CarbonTally capability (per requirement version)

`SUPPORTED` · `PARTIALLY_SUPPORTED` · `STRUCTURED_INPUT_REQUIRED` · `EXTERNAL_INPUT_REQUIRED` · `MISSING_CAPABILITY` · `FUTURE` · `NOT_APPLICABLE_TO_PRODUCT` — as required by the ratification record's Deliverable B vocabulary **[D]**. This is what allows the platform to say *"this disclosure applies to you but CarbonTally cannot yet produce it"* — an honest, auditable state rather than a silent omission.

### 7.4 Existing partial equivalent — and why it is not sufficient

`activity_categories` already carries `esrs_e1_category`, `issb_category`, `ghg_protocol_scope`, `ghg_protocol_category` **[R]**. This is a useful **activity-level taxonomy**, and the design **reuses it** for scope/activity classification. It is **not** a requirement model: it has no versioning, no requirement codes, no classification semantics, no source provenance and no applicability. **[I]** Reuse the columns; do not extend them into a requirement model.

---

## 8. Applicability model

### 8.1 Concepts

```text
disclosure_applicability_assessments   [NEW]
   ├── organization_id            (tenant scope)
   ├── framework_version_id       (which version's applicability is assessed)
   ├── reporting_period           (reporting_year + period start/end)
   ├── characteristic_snapshot    (JSONB — the facts relied on, with their sources)
   ├── assessed_status            (APPLIES / DOES_NOT_APPLY / UNDETERMINED / CUSTOMER_INPUT_REQUIRED)
   ├── basis                      (which cited rule/source produced the status)
   ├── determined_by / determined_at   (actor + time — audit)
   └── version                    (append-only; a re-assessment is a new row)
```

`characteristic_snapshot` is drawn from **fields that already exist** on `organizations`: `company_size`, `is_public`, `is_listed`, `isin`/`lei`, `business_structure`, `country`, `financial_year_end`, `reporting_standard`, `sustainability_standard`, `vat_region`, and the framework booleans `secr_enabled` / `esrs_enabled` / `issb_enabled` **[R]**. The design **reuses** these rather than creating a parallel "entity characteristics" model.

### 8.2 What the model can and cannot do (D13)

| CarbonTally may | CarbonTally may not |
|---|---|
| record the customer's declared characteristics and their evidence | decide a customer's legal status |
| evaluate a **published, cited** threshold rule and present the **result with its basis** | present an inference as a legal determination |
| return `UNDETERMINED` / `CUSTOMER_INPUT_REQUIRED` | default an unknown to `DOES_NOT_APPLY` |
| allow **voluntary** use of a capability that does not legally apply (D13) | block voluntary use because applicability is negative |
| show "confirm with your adviser" where judgement is required | provide legal advice |

**[V] The applicability rules are now evidenced** and can therefore be implemented as *cited, versioned configuration* rather than code:
* **UK SECR** — in-scope populations: UK-registered **quoted** companies, plus **large unquoted** companies and **LLPs** exceeding the statutory thresholds; **>40,000 kWh** UK energy consumption de minimis; **CA 2006 ss.382+ two-of-three test over two consecutive financial years**; thresholds changed for financial years beginning on/after **6 April 2025** (> £15m turnover, > £7.5m balance sheet, 50-employee limit unchanged). *(Residual [U]: the SI's own "large" definition and the s.465 numerics — §25.)*
* **ESRS E1 / CSRD** — applicability is **version- and date-dependent** (large PIEs > 500 employees FY ≥ 1 Jan 2024; other large undertakings postponed to FY ≥ 1 Jan 2027; SMEs/SNCIs to FY ≥ 1 Jan 2028), and the CSRD **scope was amended in 2026** (Directive (EU) 2026/470). Ireland applies via **S.I. 336/2024**.

**[REC]** Because SECR thresholds are **date-dependent and in active reform**, applicability must be evaluated against a **period-dated** rule version, never a constant. This follows from the verified evidence, not from preference.

### 8.3 Relationship to framework versions

`assessed_status` is stored **per (organisation, framework_version, period)**. A new framework version therefore produces a **new assessment** while the prior assessment remains intact — satisfying D14/D15 and making "why did we say SECR applied in FY2025?" answerable years later.

---

## 9. Report-purpose model

### 9.1 Concepts

| Concept | Purpose | Key fields | Notes |
|---|---|---|---|
| **`disclosure_report_purposes`** **[NEW]** | The controlled catalogue of purposes (D6-R) | `code` (ANNUAL_CARBON / MANAGEMENT / UK_SECR / ESRS_E1_QUANT), `name`, `is_statutory_positioned` | A purpose is **not** a framework |
| **`disclosure_purpose_requirements`** **[NEW]** | Which requirement versions a purpose presents, and how | `purpose_id`, `requirement_version_id`, `display_order`, `required_for_finalisation`, `purpose_specific_class` | "SECR requires X; the Management Report only shows it" lives here |
| **`disclosure_report_purpose_versions`** **[NEW]** | Versioning of the purpose→requirement set (D14) | `purpose_id`, `version`, `effective_from`, `status` | A purpose's content changes when a framework version changes |
| **`disclosure_report_instance_binding`** **[NEW, thin]** | Binds an **existing** report instance to the purpose/applicability that produced it | `report_id` → `report_generation_queue.id`, `purpose_version_id`, `applicability_assessment_id` | **No competing report spine** |

### 9.2 Purpose ≠ framework (the design's central reuse proof)

```text
                     calculation_snapshots / emissions_logs            [ONE authoritative foundation]
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
  ANNUAL_CARBON              UK_SECR                 ESRS_E1_QUANT          (+ MANAGEMENT)
  GHG Protocol version       SECR version            ESRS version
  requirements               requirements            requirements
        └─────────────────────────┼─────────────────────────┘
                                  ▼
                    same disclosure values, different purpose projections
```

**[R] This is already the ratified intent** (ratification §2.1/§2.3; D6-R: *"All four share the same authoritative data, calculation/provenance, evidence and disclosure foundation. They must not become four independent report engines."*). The design realises it by making **disclosure values** the shared intermediate and **purpose projections** merely an ordering/subsetting.

### 9.3 Mapping onto the existing instance/version model

**[R]** The repository already has the report spine: **instance** = `report_generation_queue.id`; **version** = `report_versions` (`report_id` + `version_number`, `UNIQUE`); **final artefact** = `report_generation_queue.final_report_url/_file_name/_size_bytes` (**currently unpopulated**; lifecycle spec §4.4). **[REC]** The Disclosure Model **binds to** these and introduces **no** competing report or version table.

### 9.4 Interaction with the existing report-type catalogue

**[R]** `SUPPORTED_REPORT_TYPES` contains exactly **one** entry (`annual`); `validate_report_type()` rejects all others with HTTP 422. **[I]** Introducing four purposes therefore requires a deliberate mapping decision (§26, `PURPOSE-CAT`) between the existing **report type** vocabulary (`annual`) and the new **report purpose** vocabulary.

**[REC]** Recommended shape: keep `report_type` as the *engine capability*, and add `purpose_code` as a **disclosure-layer projection** on the instance binding — so no existing type is silently redefined and legacy-labelled values (SECR/CSRD/ISSB in the unmounted monolith) are **not** revived (lifecycle spec §4.3).

---

## 10. GHG Protocol model (D8, D9, D12)

### 10.1 Required area → design representation → existing support

| GHG Protocol area (D9) | Design representation | Existing support | Verdict |
|---|---|---|---|
| Organizational boundaries; entities/facilities included | disclosure value via `ORG_PROFILE_FACT` + scope aggregation over facilities/assets | `facilities`, `assets`, `organizations` **[R]** | **Reuse** |
| **Consolidation approach** (equity share / financial control / operational control) | controlled attribute on the **reporting context**, retained with the calculation context | **None** — no such column exists **[R]** | **NEW** (small) |
| Operational boundaries; included activities/scopes | `activity_categories.ghg_protocol_scope` / `ghg_protocol_category` + `scope` on logs/snapshots | exists **[R]** | **Reuse** |
| Reporting period | `report_generation_queue.reporting_year`; currently derived as `YYYY-01-01 → YYYY-12-31` **[R]** | exists, but **calendar-year assumption** | **Reuse + flag** (§26 `PERIOD`) |
| Scope 1 — emissions by scope | `CALCULATION_AGGREGATE` selector `{"scope":"1"}` | `calculation_snapshots.scope` **[R]** | **Reuse** |
| Scope 2 — **location-based AND market-based, never collapsed** | two distinct selectors → two distinct disclosure values | **None** — single `scope` text only **[R]** | **NEW** (§10.2) |
| Scope 3 — category-aware | `{"scope":"3","category":"CATEGORY_n"}` | `activity_categories.ghg_protocol_category` (text) **[R]** | **NEW** (category dimension) |
| **Individual gases + CO2e** | gas dimension on the emission result + retained GWP set | **None** — `emission_factors.co2e_multiplier`, `calculation_snapshots.co2e_kg`; **no per-gas columns anywhere** **[R]** | **NEW** (§10.3) |
| Base year / recalculation | `disclosure_base_year_records` + recalculation history | **None** **[R]** | **NEW** (§10.4) |
| Biologically sequestered CO2; sequestration | `OPTIONAL`/`CONDITIONAL`; `CUSTOMER_INPUT` or future capability | **None** **[R]** | **NEW (later)** |
| Methodologies / calculation approaches | `calculation_snapshots.methodology`, `algorithm_version`, `factor_set` **[R]** | exists | **Reuse** |
| Exclusions and reasons; significant changes and causes | requirement-bound narrative (§15) | **None** | **NEW (narrative-bound)** |
| Inventory quality / uncertainty | requirement class `NOT_SUPPORTED` / future | **None** | **NEW (later)** |
| Historical / comparative information | `PRIOR_PERIOD_VALUE` source kind resolving the **prior** period's disclosure value (not recomputation) | prior `emissions_logs` / `report_versions` **[R]** | **Reuse + binding** |
| Responsible / contact information | `ORG_PROFILE_FACT` | `organizations.primary_contact_*` **[R]** | **Reuse** |

### 10.2 Scope 2 — the anti-collapse rule

**[REC]** `calculation_snapshots.scope` currently holds one value and there is **no** location/market distinction in the schema **[R]**. The design therefore requires an explicit **`scope2_method`** dimension (`LOCATION_BASED` | `MARKET_BASED`) on the disclosure value and its selector, and forbids a single "Scope 2" figure from silently satisfying both requirement versions. **[D]** This is required by D9/D10 and by the verified ESRS E1 concept set (Scope 2 location-based and Scope 2 market-based are distinct disclosures).

**[I] Implementation consequence (design-level only):** because the existing calculation layer has no method dimension, the *authoritative calculation* must eventually be able to emit a method-qualified result. The design does **not** modify the calculation engine; it records the requirement and flags the dependency (§27, risk R3).

### 10.3 Gas granularity and GWP

**[V]** The GHG Protocol Corporate Standard covers the **seven Kyoto Protocol gases** — CO2, CH4, N2O, HFCs, PFCs, SF6, NF3 — and the authoritative GWP set is the **"Required gases and GWP values"** document (**February 2013**).

**[REC] Design (two-level, no duplication of the calculation):**
* `disclosure_gases` **[NEW]** — a **controlled reference table** of the seven gases (`code`, `name`, `kyoto_annex`) plus `CO2E` as the aggregation pseudo-gas.
* `disclosure_gwp_sets` / `disclosure_gwp_values` **[NEW]** — the **GWP set/version** (`source` = "Required gases and GWP values, Feb 2013", `source_tier`, `ar_version`), with one row per (set, gas). **Retained**, never recomputed, so a report can state which GWP set produced its CO2e.
* Per-gas **disclosure values** are produced by a `{"gas":"CH4"}` selector only when the underlying calculation actually carries that gas.

**[D]/[R] Honest capability statement:** no per-gas column exists anywhere in the schema, and `emission_factors` stores a single `co2e_multiplier` **[R]**. Therefore per-gas disclosure is a **capability that must be earned by the calculation layer**, and until then the correct representation is requirement class **`NOT_SUPPORTED`** (or `PARTIALLY_SUPPORTED`) with the reason recorded — **never** a fabricated split. The existing `provenance` section already models this honesty: it emits `gas_coverage` and the note *"SEAI factors are CO2-only (CH4/N2O excluded by source design); DEFRA factors are CO2e. Mixed aggregations are labelled 'CO2/CO2e mixed' and are never relabelled as full CO2e."* **[R]** The Disclosure Model **reuses that `gas_coverage` semantics** rather than inventing a second one.

### 10.4 Base year, recalculation and recalculation history

```text
disclosure_base_year_records   [NEW]
   ├── organization_id, framework_version_id
   ├── base_year (integer), base_year_reason, boundary_note, methodology
   ├── base_year_scope1 / scope2_lb / scope2_mb / scope3  (as supported)
   ├── gwp_set_id, consolidation_approach
   ├── source_kind = RECALCULATION | INITIAL_BASELINE
   ├── supersedes_id  → previous base-year record (chain, not overwrite)
   ├── recalculation_reason (enumerated: structural/outsourcing/ownership/
   │    methodology/factor-correction/error-correction/other + free text)
   ├── evidence_refs (calculation ids, source_item_ids)
   └── effective_from
```

**[D]** D9 items 11–12 require base year and base-year recalculation information. **[R]** Nothing in the current schema models either. **[REC]** The design deliberately uses a **superseding chain** rather than in-place updates, so the pre-recalculation baseline remains reproducible (D15). 

**[D] Explicit refusal:** the design invents **no** recalculation materiality threshold (D11/D12 principle and the task's instruction). Materiality significance is a **customer/adviser judgement** recorded as narrative or as a customer-supplied attribute — see §26 `GP-BY-NOMAT`.

---

## 11. UK SECR model (D10, D11)

### 11.1 Required area → design representation

| SECR requirement (D10; [V] verified) | Representation | Existing support | Verdict |
|---|---|---|---|
| Energy consumption in **kWh** | `ENERGY_ACTIVITY` source kind over `emissions_logs.raw_quantity` + `unit` normalised to kWh | `units.conversion_factor` is the **central normalisation registry** **[R]** | **Reuse** |
| Relevant UK energy sources; optional source breakdown | value with `energy_source` dimension (gas / electricity / transport fuel) | activity taxonomy exists **[R]** | **Reuse + dimension** |
| Transport energy where applicable | selector over transport activities | `vehicles` exists **[R]** | **Reuse** |
| Scope 1; Scope 2; Scope 3 where applicable | as §10.1 | scope on logs/snapshots **[R]** | **Reuse** |
| **Total gross emissions** | `SUM_KG_CO2E` over the period | aggregate exists **[R]** | **Reuse** |
| Prior-year comparison | `PRIOR_PERIOD_VALUE` | as §10.1 | **Reuse + binding** |
| Intensity ratio + denominator + rationale | §11.3 | **None** | **NEW** |
| Methodology | `calculation_snapshots.methodology` **[R]** | exists | **Reuse** |
| Energy-efficiency measures narrative | §15 (requirement-bound narrative; `CUSTOMER_INPUT_REQUIRED` if absent) | **None** | **NEW (narrative)** |
| Applicability / exemptions | §8 | **None** | **NEW** |

### 11.2 Verbatim anchor for the SECR content set

**[V]** The verified SECR disclosure content (DfE guidance, updated 12 Aug 2026, worked disclosure table) is: energy consumption used to calculate emissions (kWh); optional energy breakdown (gas / electricity / transport fuel); Scope 1 tCO2e; Scope 2 tCO2e; Scope 3 tCO2e; **total gross emissions** tCO2e; **intensity ratio**; quantification & reporting methodology (2019 HM Government Environmental Reporting Guidelines, **GHG Reporting Protocol – Corporate Standard**, UK Government conversion factors); intensity-measurement rationale; energy-efficiency measures; and **prior-year comparison**. The design maps each of these to exactly one requirement version, so the SECR report purpose can be proved complete against the verified list rather than against a template.

### 11.3 Intensity ratio — controlled denominator catalogue (D11)

```text
disclosure_intensity_denominator_types  [NEW]   — CONTROLLED catalogue, platform-managed
   ├── code (e.g. PER_FTE, PER_TURNOVER, PER_UNIT_OUTPUT, PER_AREA_M2, PER_PUPIL, ...)
   ├── numerator_kind = GROSS_EMISSIONS_TCO2E
   ├── denominator_unit (units.code reference)
   ├── recommended (bool), sector_hint
   └── status (active / archived)

disclosure_intensity_ratios  [NEW]   — the customer's selected ratio for a period
   ├── organization_id, report_instance_id, requirement_version_id
   ├── denominator_type_code  → controlled catalogue
   ├── denominator_value (numeric) + denominator_source (ORG_PROFILE_FACT | CUSTOMER_INPUT)
   ├── numerator_value (resolved from the disclosure value) + numerator_unit
   ├── ratio_value (numeric), ratio_unit (e.g. tCO2e per £m turnover)
   ├── rationale (narrative binding — SECR requires a rationale)
   └── prior_period_ratio_value
```

**[D]** D11 requires *controlled denominator types* with *customer selection/configuration from supported types* and states the customer **remains responsible for confirming the selected denominator** where judgement is required. The design encodes exactly that: the catalogue is platform-controlled, the **selection and its rationale are customer-owned**, and the ratio is stored **with** its numerator, denominator, unit and rationale.

**[D] Explicit refusal:** the design creates **no** unrestricted user-defined denominator. New denominator types are added to the controlled catalogue only (D4, §21).

### 11.4 Why the intensity concept is separate from the emission value

**[I]** An intensity ratio is not an emission result: it has a different unit, a different source of truth for the denominator, and a rationale requirement. Modelling it as an ordinary disclosure value would lose the denominator provenance. Hence a dedicated concept — but it **consumes** the authoritative numerator rather than recalculating it.

---

## 12. ESRS E1 model (D7-R)

### 12.1 Binding constraint on identifier naming

**[U]** The exact ESRS E1 disclosure identifiers/titles could **not** be transcribed from the authoritative Annex I to (EU) 2023/2772 because every machine-readable representation exceeded the retrieval limit and the EFRAG Knowledge Hub renders the standards only through an interactive application (`…-EVIDENCE-COMPLETION-20260912-003` §24.2). **[D]** The design therefore uses the **verified concept/title** as the `requirement_code` seed and marks each identifier:

> `UNRESOLVED — AUTHORITATIVE SOURCE REPRESENTATION LIMITATION`

**[REC]** `disclosure_requirement_versions.requirement_code` is a **free-form controlled string**, so the exact official identifier can be **applied later as a data update** (a new requirement version) without any schema change. **No ESRS identifier is invented anywhere in this design.** The future **2026 Revised/Simplified ESRS** is represented only as a `FUTURE` / `ADOPTED_NOT_IN_FORCE` framework version (§6.5) and is **not** the implementation basis.

### 12.2 Layer 1 — production-grade quantitative coverage (D7-R)

| Verified E1 concept | Requirement code (seed) | Source kind | Class |
|---|---|---|---|
| Gross Scope 1 GHG emissions | `E1_SCOPE1_GROSS` | `CALCULATION_AGGREGATE {"scope":"1"}` | REQUIRED |
| Gross Scope 2 — location-based | `E1_SCOPE2_LOCATION_BASED` | `{"scope":"2","method":"LOCATION_BASED"}` | REQUIRED |
| Gross Scope 2 — market-based | `E1_SCOPE2_MARKET_BASED` | `{"scope":"2","method":"MARKET_BASED"}` | CONDITIONAL |
| Gross Scope 3 | `E1_SCOPE3_GROSS` | `{"scope":"3"}` | CONDITIONAL |
| Significant Scope 3 categories | `E1_SCOPE3_SIGNIFICANT_CATEGORIES` | `{"scope":"3","category":*}` + selection narrative | CONDITIONAL |
| **Total GHG emissions** | `E1_TOTAL_GHG` | `SUM_KG_CO2E` | REQUIRED |
| GHG intensity (per unit of net revenue / physical unit) | `E1_GHG_INTENSITY` | `INTENSITY_RATIO` (§11.3 concept, E1 denominator set) | REQUIRED |
| Energy consumption | `E1_ENERGY_CONSUMPTION` | `ENERGY_ACTIVITY` | REQUIRED |
| Energy mix (renewable / non-renewable) | `E1_ENERGY_MIX` | `ENERGY_ACTIVITY` with source dimension | CONDITIONAL |
| Methodology, inputs and provenance | `E1_METHODOLOGY_PROVENANCE` | `FACTOR_PROVENANCE` + `EVIDENCE_COMPLETENESS` | REQUIRED |
| Comparatives (prior period) | `E1_COMPARATIVES` | `PRIOR_PERIOD_VALUE` | CONDITIONAL |

*Each identifier above is a **concept seed**, and each carries the marker `UNRESOLVED — AUTHORITATIVE SOURCE REPRESENTATION LIMITATION`.* **[U]**

### 12.3 Layer 2 — structured supporting information (D7-R)

Covered as **structured, customer-supplied or narrative-bound** requirements, not as carbon calculations:

```text
disclosure_targets        [NEW]  — GHG reduction targets: scope coverage, base year,
                                   target year, target value, unit, progress, evidence, status
disclosure_actions        [NEW]  — decarbonisation / energy-efficiency / renewable actions:
                                   type, expected reduction, achieved reduction, timeframe,
                                   status, supporting evidence
disclosure_policies       [NEW]  — policy records: title, scope, owner, status,
                                   link to requirement version (narrative-bound)
disclosure_transition_plan_elements [NEW] — transition-plan carbon elements
                                   (baseline, milestones, capex/opex carbon link where supplied)
```

**[D] Boundary rule:** Layer 2 concepts store **customer evidence and claims**; CarbonTally does **not** verify them, and each is bound to an explicit `CUSTOMER_INPUT_REQUIRED` / evidence-basis state so the report can distinguish *"supplied by the customer"* from *"derived by CarbonTally"* — which is precisely what `domain/evidence.py` already does for the calculation chain (`ORIGINAL source data` vs `CarbonTally-derived data`) **[R]**.

### 12.4 Layer 3 — explicit external-input / future boundary (D7-R)

**[D]** CarbonTally will **not** compute scenario analysis, physical/transition risk assessment, anticipated financial effects or climate-related financial opportunities. In the model these are requirement versions with:

```text
carbontally_capability = MISSING_CAPABILITY | EXTERNAL_INPUT_REQUIRED
requirement_class      = CUSTOMER_INPUT_REQUIRED | NOT_SUPPORTED | FUTURE
```

**[REC]** This is the honest representation the evidence gate demands: the report can state *"this disclosure applies to you; CarbonTally does not produce it; supply it or exclude it with a recorded basis"* — and **must not** claim "full ESRS E1/CSRD compliance merely because this capability exists" (D7-R Layer 3). **[D]**

---

## 13. Evidence / provenance model

### 13.1 The decisive finding — the chain ALREADY EXISTS

**[R] Migration `20260823010000_d33_evidence_traceability.sql` (D33, P0) already implements the source-lineage chain**, additively and idempotently, with `ON DELETE SET NULL` referential links and indexed lookups:

```text
organization_files
   ↑ (file_id)
manual_extraction_items
   ↑ (source_item_id)
calculation_snapshots          + source_file (text), source_page (integer)
   ↑ (snapshot_id)
emissions_logs
```

The migration's own header states the intent: *"every calculated emission must be traceable to the exact source evidence … ADDITIVE + IDEMPOTENT — it preserves all existing rows/IDs/RLS and never rewrites historical provenance."* It also performs an **idempotent honest backfill** (exact `path` match only; unmatched rows stay `NULL`). **[R]**

**[R] `backend/domain/evidence.py` (D33.1) already presents that chain** to a human as *"source document → extracted line → mapping → emission factor → calculation → emission result"*, with an optional technical-details block of **stable record identifiers** for auditors, and classifies completeness:

| `classify_evidence_completeness(...)` | Result |
|---|---|
| document + item + calculation + factor + **source page** | `COMPLETE` |
| document + item + calculation + factor, **no page** | `PARTIAL` |
| any partial chain | `PARTIAL` |
| nothing reliable | `UNAVAILABLE` |

**[R]** `backend/data/reporting.py` similarly derives audit-readiness from persisted counts (`calculations_total`, `calculations_with_source`, `evidence_complete/partial/unavailable`, `open_issues`).

### 13.2 Design consequence

**[I] The Disclosure Model must therefore add *almost nothing* to the evidence layer.** The correct design is:

```text
disclosure_value  ──────────────►  calculation_snapshots (existing, immutable)
        │                                   │  source_item_id  (existing FK)
        │                                   ▼
        │                          manual_extraction_items (existing)
        │                                   │  file_id          (existing FK)
        │                                   ▼
        │                          organization_files  (existing; storage path + bucket)
        │
        └─► disclosure_value_evidence  [NEW, optional thin link]
                 — only where a disclosure aggregates MANY calculations
                   (e.g. "Scope 1 total") and the report must be able to
                   enumerate/summarise the underlying rows deterministically.
```

**`disclosure_value_evidence`** **[NEW]** fields: `disclosure_value_id`, `calculation_snapshot_id`, `emissions_log_id` (nullable), `source_item_id` (denormalised for drill-down without a join chain), `source_file_id`, `source_page`, `evidence_completeness` (mirrors `domain/evidence.py`), `contribution_share` (where a value is a share of an aggregate). Cardinality **1..n**. Purpose: makes the report→evidence enumeration **deterministic and version-bound** without duplicating the existing chain.

**[REC]** Where a disclosure resolves to exactly one calculation (the common case for line-level data), the link row is a **thin pointer**, and no source data is copied. Evidence is **referenced, never duplicated** — consistent with the existing `ON DELETE SET NULL` philosophy and with storage-boundary rules (§19).

### 13.3 Forward and reverse trace (both directions, by design)

**Forward trace — report → source line:**

```text
report_generation_queue.id                     (report instance)
   → report_versions (report_id, version_number)          [version spine]
   → disclosure_values (report_version_id, requirement_version_id)
   → disclosure_value_evidence (disclosure_value_id)
   → calculation_snapshots.id  (+ source_file, source_page, content_hash)
   → manual_extraction_items.id  (the extracted line item)
   → organization_files.id  (path, bucket)  → storage object
```

**Reverse trace — source line → report:**

```text
organization_files.id
   → manual_extraction_items.file_id
   → calculation_snapshots.source_item_id
   → emissions_logs.snapshot_id
   → disclosure_value_evidence.calculation_snapshot_id
   → disclosure_values.id
   → report_versions.id → report_generation_queue.id
```

**[R] Every hop except the two `disclosure_*` tables already exists and is indexed** (`idx_calculation_snapshots_source_item`, `idx_manual_extraction_items_file`) **[R]**. The design's only job is to **close the last two hops**. **[REC]** The reverse trace must be implemented as an **indexed lookup**, and the existing `audit-activity` projection already returns `calculation_snapshots.source_item_id` in its payload **[R]** — so a reverse-navigation API can be built on established patterns rather than a new mechanism.

---

## 14. Row-level / line-item traceability (the non-negotiable requirement)

### 14.1 What the repository ACTUALLY has today (verified, not assumed)

The task correctly warns against assuming row-level evidence is missing "merely because the report generator does not expose it". The investigation confirms **line-item granularity already exists — but as JSONB payloads, not as addressable rows**:

| Evidence | Where | Nature |
|---|---|---|
| `extracted.line_items` | `backend/api/v3_operations.py:471`, `v3_processing_workflow.py:830` | per-line extracted rows **[R]** |
| `mapped_data.line_items` — *"the per-line results are stored back into `mapped_data.line_items`"* | `backend/api/v3_operations.py:467,573` | per-line **mapping + calculation results** **[R]** |
| `manual_extraction_items.extracted_data` / `.mapped_data` | migration `00000000000000_init_schema.sql` | JSONB document-level payload holding those line arrays **[R]** |
| `document_processing_queue.extracted_data` / `.mapped_data` / `.validation_result` | migration `20260829000000_v3m9_durable_automatic_processing.sql` | same payloads in the automatic pipeline **[R]** |
| `customer_documents.extracted_data` / `.mapped_data` / `.calculated_emissions_kg_co2e` | migration `00000000000000_init_schema.sql` | document-level upload path **[R]** |
| Invoice document types | `document_types` / `admin/document-types.py`: `invoice_electricity`, `invoice_gas`, `invoice_water`, `invoice_fuel`, `invoice_services`, all `category='invoice'` | invoice-class documents exist **[R]** |
| `pdf_engine._parse_fuel_invoice()` | `backend/pdf_engine.py:227` | a **line-item-aware** fuel-invoice parser already exists **[R]** |

**[I] Conclusion:** line items are genuinely captured (including for invoices) and are **already carried into the mapping/calculation stage** (`mapped_data.line_items`). What does **not** exist is a **first-class, addressable, indexed line-item row** whose identity a disclosure value can point at.

### 14.2 The gap, stated precisely

```text
TODAY (verified):
   invoice INV-123 → manual_extraction_items (ONE row)
                        └── mapped_data.line_items = [ {line 1}, {line 2}, {line 3 ← emission}, {line 4} ]   (JSONB, not addressable)

REQUIRED:
   disclosure_value → calculation_snapshot → manual_extraction_items
                     → **EXACT LINE** (INV-123, line 3)                                          (addressable)
```

**[I]** The current `calculation_snapshots.source_item_id` reaches the **document-level extracted item**, and `source_page` reaches the **page** — but **not the individual line**. The task's explicit prohibition — *"Do NOT reduce provenance to merely `emission → invoice`"* — is therefore **exactly the right criticism of the current state**.

### 14.3 The minimal design that closes it

**[NEW] `evidence_line_items`** — the addressable row **extracted from** the existing JSONB, not a parallel extraction:

| Field | Why |
|---|---|
| `id` | The addressable line identity a disclosure value can point to |
| `organization_id`, `processing_origin` | Tenant scope + origin (mirrors `manual_extraction_items.processing_origin`, which already exists **[R]**) |
| `source_item_id` → `manual_extraction_items.id` | **Reuses the existing document-level parent** (never duplicates it) |
| `source_file_id` → `organization_files.id` | Document identity (already reachable via `manual_extraction_items.file_id`) |
| `source_page`, `line_number` | The exact location: **INV-123, page 2, line 3** |
| `row_reference` (text, nullable) | The human-facing reference printed on the source (invoice line ref / meter-point / txn id) — captured only when the source actually carries one |
| `raw_quantity`, `raw_unit`, `raw_description` | The **original** source values, never overwritten |
| `document_type_code` | e.g. `invoice_electricity` (**reuses the existing taxonomy**) |
| `extraction_method`, `confidence_score`, `extracted_at`, `extracted_by` | Provenance of the extraction itself |
| `payload_hash` | Deterministic identity of the line as extracted |

**[EXT] `calculation_snapshots`** — one **additive** column: `source_line_item_id uuid` (FK → `evidence_line_items.id`, `ON DELETE SET NULL`), mirroring exactly how `source_item_id` was added in D33 (additive, idempotent, non-destructive, `SET NULL` to preserve history). **No existing column changes; no data rewritten.**

```text
COMPLETE chain (target):
   report_version → disclosure_value → calculation_snapshot
      → source_line_item_id  → evidence_line_items (INV-123, line 3)
      → source_item_id       → manual_extraction_items
      → file_id              → organization_files (pdf) → storage object
```

### 14.4 Applying the same principle beyond invoices

**[REC]** The extraction-population step is **format-driven, not invoice-specific**, so the same concept covers every evidence-bearing source the task lists:

| Source type | Line/record identity | `row_reference` example |
|---|---|---|
| Utility bills | meter reading row / charge line | MPAN/MPRN + line |
| Fuel records | fuel-card transaction | card txn id |
| Travel records | trip leg | booking ref |
| Purchase records | PO line | PO line no. |
| Meter readings | reading record | meter id + read date |
| Imported datasets (CSV/XLSX) | **source row number** | `row 47` |
| Manually entered data | one synthetic row, `source_kind=MANUAL`, `row_reference=NULL` | — (and the report must say so, honestly) |

**[D] Honesty rule:** where the source genuinely has no finer granularity (a single manually-entered figure), the line-item row is a **single synthetic row with `row_reference = NULL`** and the evidence classification remains `PARTIAL` (no page/location) — exactly the semantics `domain/evidence.py` already implements. **No artificial granularity is ever fabricated.**

---

## 15. Narrative binding model

### 15.1 The four ratified narrative kinds (D5)

| Kind | Definition (D5) | Design representation | Authoring authority |
|---|---|---|---|
| **Requirement-bound narrative** | Narrative a specific disclosure requires | `disclosure_narratives` row keyed by `requirement_version_id` | Customer Owner / Customer Admin (D5), or system-composed |
| **System-derived narrative** | Generated from authoritative structured data where safely derivable | produced at render time from disclosure values; **not stored as editable text** | System |
| **Customer-authored narrative** | Required where CarbonTally cannot derive the explanation | `disclosure_narratives` row with `provenance = CUSTOMER` | Customer Owner / Customer Admin |
| **Mixed narrative** | Structured facts + customer explanation | a `SYSTEM` segment + a `CUSTOMER` segment in one binding | System + customer |
| **Optional management commentary** | Separate namespace, **not** a regulatory disclosure | `disclosure_management_commentary` row keyed by `report_version_id` only | Customer Owner / Customer Admin |

### 15.2 The binding relationship (design only — no limits invented)

```text
disclosure_narratives   [NEW]
   ├── requirement_version_id        → WHICH disclosure it satisfies   (requirement-bound)
   ├── report_version_id             → WHICH version it belongs to
   ├── organization_id               → tenant scope
   ├── narrative_kind                → REQUIRED_DISCLOSURE | MANAGEMENT_COMMENTARY
   ├── provenance                    → CUSTOMER | SYSTEM | MIXED
   ├── system_facts_ref              → which disclosure values feed the SYSTEM segment
   ├── customer_text                 → the customer-authored segment (nullable)
   ├── evidence_refs                 → supporting evidence (files/line items)
   ├── authored_by / authored_at / updated_at
   └── status                        → DRAFT | SUBMITTED | APPROVED  (bound to the version lifecycle)
```

**[D]** The design implements exactly the D5 rejection: there is **no** fixed "7 fields × 4,000 characters" shape anywhere. Text length/format constraints are a **PO decision** (`§26 A1/A3`); this document deliberately invents **no** character limits and **no** field counts.

### 15.3 Why narrative binds to the requirement, not to the report section

**[I]** Binding narrative to `requirement_version_id` (not to a section label) is what makes the requirement-coverage claim honest: the report can state that requirement X is satisfied *by this text* in version N, and that a different purpose (SECR vs ESRS E1) reuses or omits it. Binding to a section would re-introduce the template-as-requirement anti-pattern that D2 explicitly forbids ("A report template must not become the canonical definition of a regulatory requirement").

### 15.4 Management commentary is deliberately outside the disclosure set

**[D]** D5 requires a **separate namespace** for optional commentary. `disclosure_management_commentary` has **no** `requirement_version_id`, and the engine must not present it as satisfying any requirement. **[REC]** This is the structural mechanism that prevents optional commentary from being mistaken for a disclosure.

### 15.5 S4 status

**[R]** S4 (narrative overlay) is **not implemented**; the S4 task report is a HARD STOP documenting that the minimum decisions required to unblock it were not available (`…S4-NARRATIVE-OVERLAY-20260912-001`). **[D]** This design **binds the relationship only** and explicitly does **not** authorise or implement S4.

### 15.6 Relationship to existing narrative surfaces

**[R]** The only narrative-adjacent storage that exists today is the legacy `report_generation_queue.user_edits` JSONB column (unused by the V3 structured engine) and the dormant `report_comments` table (lifecycle spec §16.1). **[REC]** Neither is extended; the new concepts are separate and version-bound. No existing column is repurposed.

---

## 16. Current 12-section report — integration mapping

### 16.1 The two presentation artefacts (discrepancy recorded)

**[R] Discrepancy found and recorded:** the phrase "12-section report" is correct for the **authoritative V3 structured engine** but **not** for the legacy PDF generator:

| Artefact | Sections | Where | Authoritative? |
|---|---|---|---|
| **V3 structured report (12 sections)** | `metadata`, `organization`, `period`, `totals`, `scopes`, `activities`, `validation`, `benchmarking`, `provenance`, `calculation`, `lineage`, `generation` | `backend/engines/report_generation.py:62-75`, rendered by `engines/pdf_render.py` | **Yes** (`annual`) |
| **Legacy PDF report (6 numbered sections + TOC)** | 1. Executive Summary · 2. Emissions Overview · 3. Year-over-Year Comparison · 4. Methodology · 5. Energy Efficiency Measures · 6. **Compliance Statement** | `backend/report_generator.py` | **No** — legacy monolith, D16 disposition |

**[I]** An earlier task description referring to a "12-section report" is accurate for the authoritative artefact; the legacy 6-section PDF must never be conflated with it, and its **"Compliance Statement"** is the D16 boundary issue (§4).

### 16.2 Section-by-section disposition (no change made in this task)

| # | section_id | Nature | Disclosure-Model relationship |
|---|---|---|---|
| 1 | `metadata` | Technical/system | Continues. Gains `purpose_code`, framework version, applicability reference |
| 2 | `organization` | Presentation (+ `ORG_PROFILE_FACT` disclosures) | Continues; supplies org-scope disclosures |
| 3 | `period` | Technical | Continues; must become **period-aware** rather than calendar-year (§26 `PERIOD`) |
| 4 | `totals` | **Disclosure presentation** | Fed by `disclosure_values` (total gross emissions, total GHG) |
| 5 | `scopes` | **Disclosure presentation** | Fed by scope disclosure values — **must split Scope 2 LB/MB** when the method dimension lands |
| 6 | `activities` | Technical evidence + presentation | Reuses `activity_categories` taxonomy; provides the Scope 3 category breakdown basis |
| 7 | `validation` | **Technical evidence** | Continues unchanged (blocking-validation behaviour preserved) |
| 8 | `benchmarking` | **Management presentation** | Remains management-purpose content; **not** a regulatory disclosure |
| 9 | `provenance` | **Technical evidence** | Reuses existing `gas_coverage` / factor-source semantics (§10.3) |
| 10 | `calculation` | **Technical evidence** | Continues (methodology, algorithm version, snapshot verification) |
| 11 | `lineage` | **Technical evidence** | **The natural home for the evidence drill-down entry point** — it currently exposes *counts* of logs/factors; the design adds per-value evidence enumeration (§13.3) |
| 12 | `generation` | Technical/system | Continues; gains framework/requirement/mapping version stamps (§6.4) |

### 16.3 Requirements with **no** presentation location today

**[I]** The following verified requirement areas have **no** place in the current 12 sections and require *new* presentation slots (design-level, not implemented):

1. **Applicability statement** (which frameworks/versions apply to this reporter, and the basis) — §8;
2. **Requirement coverage statement** (requirement-by-requirement: included / not applicable / not supported / customer input required) — §7;
3. **Intensity ratio with denominator + rationale** (SECR/E1) — §11.3;
4. **Base year and recalculation disclosure** — §10.4;
5. **Energy consumption and energy mix** as first-class disclosures — §12.2;
6. **Per-gas breakdown** (only where earned) — §10.3;
7. **Targets / actions / policies** (Layer 2) — §12.3;
8. **Non-assurance / positioning statement** — §4;
9. **Evidence completeness roll-up per disclosure** — §13.

**[REC]** These slots are added as **disclosure-driven** presentation, not as new hard-coded sections: the template renders the purpose's requirement set (§9). This preserves D3 (the 12-section report remains the current template) while allowing the disclosure model to feed it.

### 16.4 Legacy route — explicitly untouched

**[D]** `POST /api/reports/generate-enhanced-report` (`backend/routes/reports.py:1287`) is **live** and emits compliance claims; its disposition is **D16 work, a separate bounded task**. **[R]** It is in the **unmounted legacy monolith** (its labels SECR/CSRD/ISSB are not part of the V3 catalogue — lifecycle spec §4.3). **This design neither modifies it nor changes any compliance claim.**

---

## 17. Existing repository / schema mapping

### 17.1 Table-by-table verdict (evidence-based)

| Existing table | Role in the Disclosure Model | Verdict |
|---|---|---|
| `calculation_snapshots` | **Authoritative emission result + provenance** (immutable, `content_hash`, `methodology`, `algorithm_version`, `factor_kind`, `request_id`) | **Consume as-is** (+1 additive column, §14.3) |
| `emissions_logs` | Source-level activity + result; links `file_id`, `customer_document_id`, `snapshot_id` | **Consume as-is** |
| `emission_factors` | Factor master (year, activity, `co2e_multiplier`, unit, scope, source, set, country) | **Consume as-is** |
| `customer_factors` | Customer-approved factors (**already versioned**, effective window, `source_reference`, status) | **Consume as-is**; strong precedent for versioning |
| `import_batches` | Factor-import provenance (`provider_key`, `source_checksum`, rollback) | **Consume as-is** |
| `factor_aliases` | Alias→activity mapping | **Consume as-is** |
| `activity_categories` | Scope/taxonomy incl. `ghg_protocol_scope`, `esrs_e1_category` | **Reuse** for classification (§7.4) |
| `units` | **Central unit-normalisation registry** (`conversion_factor`) | **Reuse** (never duplicate unit logic) |
| `manual_extraction_items` | Document-level extraction/mapping + `file_id` | **Reuse** as line-item parent |
| `organization_files` | Source document (path, bucket, status, approval) | **Reuse** as the evidence document |
| `customer_documents` | Upload-path document record | **Reuse** |
| `document_processing_queue` | Pipeline state + `calculation_snapshot_id`, `source_item_id` | **Reuse** |
| `report_generation_queue` | **Report instance** + generation state | **Reuse** (bind, don't replace) |
| `report_versions` | **Version spine** + lifecycle `status` | **Reuse** (bind, don't replace) |
| `report_templates` | `template_structure` JSONB | **Reuse, but note:** not referenced by any backend Python **[R]** |
| `audit_trail` | **Append-only ledger** (DB-level trigger; `not_assurance` marker) | **Reuse** |
| `domain_events` | Event log (`correlation_id`, `aggregate_*`) | **Reuse** |
| `issues` | Validation/blocking issues | **Consume as-is** |
| `facilities`, `assets`, `suppliers`, `vehicles`, `processing_entities` | Boundary/entity data | **Reuse** |
| `organizations` | Entity characteristics for applicability (§8) | **Reuse** |
| `organization_metadata` | Org-level profile metrics incl. `renewable_energy_percentage`, `energy_intensity` **[R]** | **Reuse** as profile facts, **not** as a structured energy model |

### 17.2 Existing calculation architecture — how the model consumes it (no new engine)

**[R]** The verified calculation spine is:

```text
activity data (emissions_logs / manual_extraction_items.mapped_data)
        ↓  CalculationEngine (backend/engines/calculation.py)
calculation_snapshots   ← immutable, content_hash, algorithm_version,
                          methodology, factor_kind/factor_id/customer_factor_id,
                          request_id (deterministic/idempotent), source_item_id
        ↓
emissions_logs.snapshot_id
        ↓
report_generation.py  (existing 12-section composition)
```

**[REC] Binding rules (design-level, enforceable in review):**

1. The Disclosure Model **reads** `calculation_snapshots` (via the existing `CalculationEngine` verification surface / `EmissionsLogsRepository`) and **never recomputes** an emission. `source_kind = CALCULATION_AGGREGATE` is a **projection over persisted snapshots**, not a re-calculation.
2. **Aggregation is summation of persisted `co2e_kg`**, never a re-application of a factor to a quantity.
3. Factor provenance is **inherited** (`factor_id`, `factor_kind`, `factor_source`, `factor_set`, `import_batch_id`) and surfaced, not re-derived.
4. The deterministic `request_id` + `content_hash` in `calculation_snapshots` give the Disclosure Model **idempotent, verifiable values** for free — the design must not introduce a second hashing or idempotency mechanism.
5. `PRIOR_PERIOD_VALUE` resolves a **prior period's persisted value**, never a re-run of the engine for a closed period.

**[I]** These rules are what make the "no duplicate calculation logic" requirement (task §17, D8/§2.1) structurally true rather than aspirational: there is exactly **one** place a number can come from.

---

## 18. Structural model proposal (conceptual — no schema, no migration)

### 18.1 Concept register

Every concept below states its **purpose**, **why it is required**, **which verified requirement supports it**, **existing equivalent** and **whether new schema is likely required**.

#### A. Framework / version layer (global, platform-controlled)

| Concept | Purpose & why required | Verified requirement | Existing equivalent | New schema? |
|---|---|---|---|---|
| `disclosure_frameworks` | Register the 3 initial frameworks (D1) | D1, D2 | None | **Yes** |
| `disclosure_framework_versions` | Versioned binding + source tier + legal status (D14, D17) | D14, D15, D17; [V] CSRD 3-act chain, ESRS 2023 vs 2026, SECR 2025 thresholds | None | **Yes** |
| `disclosure_requirement_versions` | The requirement text/code per framework version | D9, D12; [V] SECR content list, E1 concept set | `activity_categories` (partial taxonomy only) | **Yes** |
| `disclosure_requirement_mappings` | Controlled requirement→data binding, versioned | D4, D14 | None | **Yes** |

#### B. Purpose layer

| Concept | Purpose & why required | Verified requirement | Existing | New schema? |
|---|---|---|---|---|
| `disclosure_report_purposes` | The 4 ratified purposes (D6-R) | D6-R | Legacy labels only (not authoritative) | **Yes** |
| `disclosure_purpose_requirements` | Purpose → requirement presentation set | D6-R, D2 | None | **Yes** |
| `disclosure_report_purpose_versions` | Version the purpose content (D14) | D14 | None | **Yes** |
| `disclosure_report_instance_binding` | Bind the **existing** instance to purpose/applicability | D15 | `report_generation_queue` (partial) | **Yes (thin)** |

#### C. Applicability layer

| Concept | Purpose & why required | Verified requirement | Existing | New schema? |
|---|---|---|---|---|
| `disclosure_applicability_assessments` | Facts + status + basis + date, per org/framework-version/period | D13; [V] SECR thresholds, CSRD phases | `organizations` characteristics (partial) | **Yes** |

#### D. Value layer (the heart)

| Concept | Purpose & why required | Verified requirement | Existing | New schema? |
|---|---|---|---|---|
| `disclosure_values` | **One resolved value per requirement version per report version**, carrying class/status/unit/provenance | D9, D10, D12, D15 | None | **Yes** |
| `disclosure_value_evidence` | Deterministic value→calculation→line-item enumeration | Task §4 (traceability); D33 chain | D33 chain (partial — no value link) | **Yes (thin)** |
| `disclosure_intensity_denominator_types` | **Controlled** denominator catalogue | D11 | None | **Yes (reference data)** |
| `disclosure_intensity_ratios` | Selected ratio + denominator + rationale | D10, D11, D7-R | None | **Yes** |
| `disclosure_base_year_records` | Base year + recalculation chain | D9 (11–12) | None | **Yes** |
| `disclosure_gases`, `disclosure_gwp_sets`, `disclosure_gwp_values` | Controlled gas list + retained GWP set/version | D9 (10); [V] 7 gases + Feb-2013 GWP | `provenance.gas_coverage` (report-only) | **Yes (reference data)** |

#### E. Evidence layer

| Concept | Purpose & why required | Verified requirement | Existing | New schema? |
|---|---|---|---|---|
| `evidence_line_items` | **Addressable** source row/line (INV-123 line 3) — the non-negotiable traceability requirement | Task §4; D33 intent | line items exist **only** inside JSONB | **Yes** |
| `calculation_snapshots.source_line_item_id` | Link the immutable result to the exact line | Task §4 | `source_item_id` (document-level only) | **Extend** (1 nullable column + FK + index) |
| Evidence completeness | Classification COMPLETE/PARTIAL/UNAVAILABLE | D33.1 | `domain/evidence.py` (exists) | **Reuse as-is** |

#### F. Narrative / Layer 2 layer

| Concept | Purpose & why required | Verified requirement | Existing | New schema? |
|---|---|---|---|---|
| `disclosure_narratives` | Requirement-bound narrative binding | D5 | None (S4 blocked) | **Yes** |
| `disclosure_management_commentary` | Separate optional-commentary namespace | D5 | None | **Yes** |
| `disclosure_targets`, `disclosure_actions`, `disclosure_policies`, `disclosure_transition_plan_elements` | Layer 2 structured supporting information | D7-R Layer 2 | None | **Yes** |

### 18.2 Cross-cutting properties (every concept above)

| Property | Design rule |
|---|---|
| **Cardinality** | `report_generation_queue` 1 → n `report_versions` 1 → n `disclosure_values`; `disclosure_value` 1 → n `disclosure_value_evidence`; `calculation_snapshot` 1 → 0..1 `source_line_item` (a manual-entry calculation may legitimately have **no** line item) |
| **Versioning** | Framework/requirement/mapping/purpose versions are **immutable once referenced**. Values and narratives are **per report version** and never mutated after `APPROVED`/`FINAL`. Recalculation uses a superseding chain, never an overwrite |
| **Tenant/entity scope** | `organizations`-scoped for every row that carries organisation data (`organization_id` is **NOT NULL** per migration `20260831030000_tenant_org_id_not_null.sql`) **[R]**. Framework/requirement/GWP/denominator catalogues are **global** (platform-controlled) and carry no organisation data |
| **Evidence retention** | Values **reference** evidence; they never copy storage objects or signed URLs. Retention remains governed by the existing configurable retention mechanism (N3) |
| **Audit navigation** | Both directions (§13.3); every write emits `audit_trail` entries using the **existing** `AuditRepository` taxonomy (`CAT_REPORT` etc.) **[R]** — no new audit mechanism |
| **Determinism** | A value is reproducible from (purpose version, framework version, requirement version, mapping version, report version, calculation set) alone |

### 18.3 Explicit non-generalisation statement (task §21)

**The design deliberately does NOT create:** a generic rules engine, an unrestricted template engine, a regulatory DSL, or user-defined compliance rules. All variation is expressed as **controlled, versioned configuration** over an **enumerated** vocabulary (`source_kind`, `aggregation`, `requirement_class`, `assessed_status`, denominator types, gases). **[REC]** Any proposal to add user-editable logic is a governance change requiring PO ratification, not an implementation detail.

### 18.4 What existing architecture already solves (task §30)

| Problem | Already solved by | Design action |
|---|---|---|
| Authoritative emission calculation | `CalculationEngine` + immutable `calculation_snapshots` + `content_hash` | **Consume; do not rebuild** |
| Report instance / version spine | `report_generation_queue` + `report_versions` (`UNIQUE`) | **Bind; do not replace** |
| Lifecycle states + guards | `report_versions.status` + `domain/report_lifecycle.py` transitions | **Reuse vocabulary** |
| Append-only audit | `audit_trail` + DB-level immutability trigger | **Reuse** |
| Factor provenance | `factor_kind`/`factor_id`/`customer_factor_id` + `import_batches` | **Reuse** |
| Customer-factor versioning | `customer_factors.version` + effective window | **Reuse as the versioning precedent** |
| Unit normalisation | `units.conversion_factor` (central registry) | **Reuse; never duplicate** |
| Evidence chain (document→item→calculation) | D33 migration + `domain/evidence.py` | **Reuse; add only the line-item and value hops** |
| Non-assurance positioning | `AUDIT_NOT_ASSURANCE_NOTICE`, Phase 7 markers | **Reuse wording** |
| Scope/activity taxonomy | `activity_categories` | **Reuse** |

---

## 19. Security / tenant / entity scope

### 19.1 Per-concept scope assessment (no RLS or permission change is made here)

| Concept | Tenant scope | Firm/entity scope | Actor access | Evidence access | Report access |
|---|---|---|---|---|---|
| `disclosure_frameworks`, `_framework_versions`, `_requirement_versions`, `_requirement_mappings` | **Global read** (platform-controlled) | n/a | Read: all authenticated; **Write: platform/internal only** | n/a | n/a |
| `disclosure_report_purposes`, `_purpose_requirements`, `_purpose_versions` | **Global read** | n/a | Write: platform/internal only | n/a | n/a |
| `disclosure_gases`, `_gwp_sets`, `_gwp_values`, `_intensity_denominator_types` | **Global read** | n/a | Write: platform/internal only | n/a | n/a |
| `disclosure_applicability_assessments` | **Organisation-scoped** | entity/facility context recorded in the snapshot | Customer Owner/Admin write; Member/Viewer read; Consultant per engagement | Yes (basis evidence) | Yes |
| `disclosure_values` | **Organisation-scoped** | inherited from the calculations | Customer Owner/Admin; Consultant (authorised active clients); Staff (internal ops) | **Yes — drill-down** | Yes |
| `disclosure_value_evidence` | **Organisation-scoped** | inherited | same as values | **Yes** — the audit path | indirect |
| `evidence_line_items` | **Organisation-scoped** | inherits `manual_extraction_items` entity/PE provenance | as per existing extraction access; **PE boundary preserved** | **Yes** | indirect |
| `disclosure_narratives`, `_management_commentary` | **Organisation-scoped** | n/a | **Customer Owner/Admin** write (D5); Consultant authorised; Staff read per role | via refs | Yes |
| `disclosure_targets`, `_actions`, `_policies`, `_transition_plan_elements` | **Organisation-scoped** | n/a | Customer Owner/Admin write; read per role | via refs | Yes |
| `disclosure_base_year_records` | **Organisation-scoped** | boundary recorded | Customer Owner/Admin propose; approval per lifecycle authority | Yes | Yes |
| `disclosure_intensity_ratios` | **Organisation-scoped** | n/a | Customer Owner/Admin select; **customer confirms denominator** (D11) | Yes | Yes |
| `disclosure_report_instance_binding` | **Organisation-scoped** | n/a | follows `report_generation_queue` authorization | indirect | Yes |

### 19.2 Security principles the design must satisfy when implemented

**[D]/[REC]**
1. **Every disclosure read/write is organisation-scoped and server-enforced.** The existing guards (`require_org_member()`, `require_org_admin()` — `backend/auth.py:445/470`; `ensure_org_access()` — `backend/api/dependencies.py:149`) are the established pattern **[R]**; new surfaces **must** use them. A hidden or disabled UI control is never authorization.
2. **The evidence drill-down must not become a cross-tenant leak path.** Line-item/evidence navigation reuses the organisation scoping already applied to `manual_extraction_items`/`organization_files`, and **must preserve the processing-entity boundary** (PE users see assigned work, not unrestricted customer documents) plus the private-document storage rules from migration `20260823000000_d32_private_documents_storage.sql` **[R]**.
3. **Signed URLs never enter disclosure payloads, logs or documents.** Evidence access continues through the existing authorized document surface.
4. **Global catalogues are read-only to customers.** Framework/requirement/GWP/denominator data is platform-controlled; a customer cannot author a requirement or a denominator type (this is what keeps D4's "no generic rules engine" true).
5. **Approval authority is unchanged** — version-lifecycle authority remains governed by `domain/report_lifecycle.py` (`AUTHORITY_ADMIN`, `required_authority()`), which new surfaces **respect rather than re-implement** **[R]**.
6. **Consultant access is engagement-scoped, not portfolio-wide** (`20260821000000_d20_d15_active_consultant_grant.sql`) **[R]**; disclosure data inherits the same boundary.

**[D] No RLS policy, grant, role or permission is modified by this design task.**

---

## 20. Migration implications (identified only — none created)

| Category | Item | Note |
|---|---|---|
| **Reused without change** | `calculation_snapshots`, `emissions_logs`, `emission_factors`, `customer_factors`, `import_batches`, `factor_aliases`, `units`, `activity_categories`, `manual_extraction_items`, `organization_files`, `customer_documents`, `document_processing_queue`, `report_generation_queue`, `report_versions`, `audit_trail`, `domain_events`, `issues`, `facilities`, `assets`, `suppliers`, `vehicles`, `organizations`, `organization_metadata` | ~23 tables; **no extension required for the MVP** |
| **Tables requiring extension** | `calculation_snapshots` — **one additive nullable column** `source_line_item_id` (+ FK `ON DELETE SET NULL` + index) | Mirrors the D33 pattern exactly. **No existing column or row is rewritten** |
| **New tables likely required (MVP)** | `disclosure_frameworks`, `disclosure_framework_versions`, `disclosure_requirement_versions`, `disclosure_requirement_mappings`, `disclosure_report_purposes`, `disclosure_purpose_requirements`, `disclosure_report_purpose_versions`, `disclosure_report_instance_binding`, `disclosure_applicability_assessments`, `disclosure_values`, `disclosure_value_evidence`, `evidence_line_items`, `disclosure_intensity_denominator_types`, `disclosure_intensity_ratios` | **14 tables** — see §22 |
| **New tables likely required (later)** | `disclosure_narratives`, `disclosure_management_commentary`, `disclosure_gases`, `disclosure_gwp_sets`, `disclosure_gwp_values`, `disclosure_base_year_records`, `disclosure_targets`, `disclosure_actions`, `disclosure_policies`, `disclosure_transition_plan_elements` | **10 tables** — see §23 |
| **Backfill requirements** | (a) **`evidence_line_items`** populated from existing `extracted_data.line_items` / `mapped_data.line_items` for historical items — idempotent and honest (unmatchable rows stay `NULL`, per the D33 precedent); (b) `calculation_snapshots.source_line_item_id` backfilled **only** where a deterministic match exists | **[REC]** No historical row may be rewritten to *manufacture* provenance that was never captured |
| **Historical-data implications** | Existing reports stay valid and reproducible; they simply carry **no** disclosure values until values are materialised for them. **Historical reports are never retro-fitted silently** | D15 |
| **Compatibility implications** | All new concepts are **additive**. No existing API response shape, report content key, lifecycle status or RLS policy needs to change for the MVP | **[I]** |
| **Report-version implications** | Disclosure values are keyed to `report_versions.id`. Because `report_versions` is append-only with `UNIQUE (report_id, version_number)`, a **new version** produces a **new value set**; historical values are untouched | D15 |

---

## 21. API implications (identified only — none implemented)

### 21.1 Existing surfaces (verified) that will eventually need attention

| Surface | Today | Likely future need |
|---|---|---|
`GET /api/v3/reports/types` | returns the single `annual` entry **[R]** | expose purposes/frameworks (or keep as-is and add a separate disclosure catalogue endpoint) |
`POST /api/v3/reports` | creates an instance from `report_type` + `reporting_year` **[R]** | accept `purpose_code` + applicability reference |
`GET /api/v3/reports/{id}/content` | returns `generated_content` JSONB **[R]** | include disclosure values (or a separate disclosure endpoint) |
`GET /api/v3/reports/{id}/versions` | version list **[R]** | include framework/requirement/mapping version stamps |
`POST /api/v3/reports/{id}/versions` and `.../{n}/submit|request-changes|reject|approve|finalize` | **lifecycle already implemented** **[R]** | unchanged in shape; must reject finalisation when a `REQUIRED`/`CUSTOMER_INPUT_REQUIRED` requirement is unresolved |
`GET /api/v3/reports/{id}/pdf` | branded PDF render **[R]** | render disclosure-driven slots (§16.3) |
`GET /api/v3/reporting/audit-readiness` / `audit-activity` | evidence readiness + activity timeline **[R]** | extend with per-disclosure completeness |
`POST /api/reports/generate-enhanced-report` | legacy, compliance claims **[R]** | **D16 disposition — not this design** |

### 21.2 New read/write concepts (design-level)

| Need | Proposed surface shape (conceptual) |
|---|---|
| Framework/version retrieval | read-only catalogue endpoints |
| Requirement retrieval for a purpose/version | read-only, scoped to the purpose version |
| Applicability management | read + write (customer-declared facts; status + basis returned) |
| Disclosure retrieval | read by report version, with class/status/unit/provenance |
| **Evidence drill-down** (forward) | value → calculations → line items → document, **authorized** |
| **Reverse evidence navigation** | from a document/line item → the disclosures and reports referencing it |
| Intensity-ratio management | read the controlled catalogue; write the selected ratio + rationale |
| Narrative binding | read/write requirement-bound narrative (S4 — **not authorised**) |

**[REC] Reuse rule:** every new endpoint must apply the existing guard pattern (`require_org_member()`/`require_org_admin()` + `ensure_org_access()`) and emit `audit_trail` entries via the existing taxonomy. **No new authorization mechanism and no new audit mechanism** (**[R]**, §19.2).

**[D] Explicitly out of scope:** XBRL/iXBRL output, statutory filing integration, and any external assurance interface.

---

## 22. Minimum viable Disclosure Model

### 22.1 Required now (MVP — supports all four purposes across the three ratified frameworks)

| # | Concept | Why it is MVP (not optional) |
|---|---|---|
| 1 | `disclosure_frameworks` + `disclosure_framework_versions` | Without a versioned framework there is **no** object to bind a report to (D14/D15) |
| 2 | `disclosure_requirement_versions` | The requirement catalogue for GHG Protocol + SECR + E1 (D9/D10/D7-R) |
| 3 | `disclosure_requirement_mappings` | The controlled requirement→data binding (D4) |
| 4 | `disclosure_report_purposes` + `_purpose_requirements` + `_purpose_versions` | The four ratified purposes must be distinguishable (D6-R) |
| 5 | `disclosure_report_instance_binding` | Connects an existing report instance to its purpose/applicability (D15) |
| 6 | `disclosure_applicability_assessments` | Distinguishes regulatory applicability from capability (D12/D13) |
| 7 | `disclosure_values` | The shared intermediate that makes one foundation serve four purposes (D2/D6-R) |
| 8 | `disclosure_value_evidence` | The value→evidence hop of the traceability requirement (task §4) |
| 9 | `evidence_line_items` (+ `calculation_snapshots.source_line_item_id`) | **Row-level/line-item traceability — non-negotiable** (task §4) |
| 10 | `disclosure_intensity_denominator_types` + `disclosure_intensity_ratios` | SECR and E1 both require an intensity ratio with a controlled denominator and rationale (D10/D11; [V]) |

**MVP deliberately excludes:** narratives (S4 blocked), Layer 2 targets/actions/policies, base-year/recalculation, per-gas and GWP tables. Rationale: none of them can be honestly populated before the value layer exists, and each would add schema **before** the requirement/vocabulary is ratified. **[REC]**

### 22.2 The MVP in one picture

```text
framework ──versions── requirement_versions ──mappings──┐
                                                        │
purpose ──purpose_requirements──► instance_binding ◄────┤
                                       │                │
                                       ▼                ▼
                              disclosure_values ◄── disclosure_intensity_ratios
                                       │
                                       ▼
                              disclosure_value_evidence
                                       │
                                       ▼
                        calculation_snapshots ──► source_line_item_id
                                       │                    │
                                       ▼                    ▼
                        emissions_logs              evidence_line_items
                                                            │
                                                            ▼
                                        manual_extraction_items ──► organization_files
```

**[I]** Note the shape: everything on the right/bottom is **existing**; the MVP adds only the left/top and the two thin links.

---

## 23. Deferred / future concepts

### 23.1 Required later (sequenced, not speculative)

| Concept | Why deferred | Trigger to build |
|---|---|---|
| `disclosure_narratives` + `disclosure_management_commentary` | **S4 is explicitly blocked** by PO decision (minimum decisions unavailable) | PO ratification of A1/A3/P3 (§26) |
| `disclosure_gases` + `_gwp_sets` + `_gwp_values` | Requires the calculation layer to carry per-gas data; today it cannot (**[R]** no per-gas columns) | Calculation-layer capability (R3) |
| `disclosure_base_year_records` | Requires an approved base-year + recalculation policy (**[D]** no materiality threshold invented) | PO ratification of `GP-BY`/`GP-BY-NOMAT` |
| `disclosure_targets` / `_actions` / `_policies` / `_transition_plan_elements` | Layer 2 structured support; depends on narrative-binding decisions and customer-input UX | Post-S4 |

### 23.2 Explicit future (not scheduled)

| Concept | Status |
|---|---|
| ESRS E1 **2026 Revised/Simplified** framework version | `FUTURE` / `ADOPTED_NOT_IN_FORCE` — **[V] not in force**; represented, not implemented (§6.5) |
| GRI 305 / IFRS S2 | **Deferred by D1**; must not be added to initial scope |
| XBRL / iXBRL tagging | **Out of scope** (explicit [D]); no tagging model designed |
| Scope 3 category-level modelling beyond what `activity_categories` maps | Conditional on `GP-S3` PO decision |
| Uncertainty / inventory-quality model | `NOT_SUPPORTED` until a methodology decision exists |
| Scenario analysis / climate risk / anticipated financial effects | **Permanently outside** the initial carbon-accounting model (D7-R Layer 3) |
| Consolidation-approach switching mid-period | Recorded per reporting context; multi-approach parallel reporting is future |

---

## 24. Implementation sequencing (proposed — none started)

```text
Stage 0  PO review of this design                              ← NEXT STEP (this document)
   │
Stage 1  Disclosure Model schema + migrations                  [14 MVP tables + 1 additive column]
   │        (incl. RLS + indexes + seed of framework/requirement/purpose reference data)
   ▼
Stage 2  Provenance/evidence relationships                     [evidence_line_items backfill;
   │        (line-item addressability + value evidence links)    source_line_item_id backfill]
   ▼
Stage 3  Calculation integration                               [projection over calculation_snapshots;
   │        (read-only consumption; no engine change)            no recomputation]
   ▼
Stage 4  Framework mappings                                   [requirement→data bindings for the
   │        (GHG Protocol, SECR, ESRS E1 concept set)            three frameworks]
   ▼
Stage 5  Applicability                                        [period-dated rules + assessment
   │        (SECR thresholds incl. 2025 change; CSRD phases)     capture + UNDETERMINED handling]
   ▼
Stage 6  Report-purpose / template integration                [purpose projections; new presentation
   │        (purpose_code on the instance binding)              slots §16.3]
   ▼
Stage 7  Narrative binding (S4)                               [BLOCKED until A1/A3/P3 ratified]
   │
Stage 8  Report generation                                    [disclosure-driven composition]
   ▼
Stage 9  Evidence drill-down (forward + reverse)              [authorized, org-scoped, audited]
   ▼
Stage 10 Independent verification                              [QA harness: ALLOW + DENY,
            (cross-tenant denial, PE boundary, viewer/member)    traceability, reproducibility]
```

**[REC] Sequencing principles:**
1. **Stage 1 before Stage 2–3** — the value layer needs somewhere to live, but Stage 2 is where traceability becomes real; do not ship values without the evidence link.
2. **Stage 5 (applicability) before Stage 6** — a purpose projection that cannot state applicability would re-introduce the compliance-claim risk.
3. **Stage 7 is gated on PO decisions**, not on engineering readiness.
4. **Stage 10 is not optional** — every stage's security and reproducibility properties must be independently tested (ALLOW **and** DENY), per the project's QA philosophy.
5. **No stage may modify the calculation engine, the legacy route or RLS policies** without separate authorization.

**[D] This sequence is a proposal for PO review. No stage is authorised by this document.**

---

## 25. Unresolved regulatory evidence (carried forward, not resolved here)

| # | Unresolved item | Kind | Effect on this design |
|---|---|---|---|
| 1 | **ESRS E1 exact disclosure identifiers/titles** (Annex I to (EU) 2023/2772) | Regulatory fact — **representation limitation** | `requirement_code` seeds use verified **concepts** and carry `UNRESOLVED — AUTHORITATIVE SOURCE REPRESENTATION LIMITATION`; identifiers can be applied later as a data update (§12.1). **Not invented.** |
| 2 | **GHG Protocol Chapter 9 required/optional lists** | Regulatory fact — PDF-only | D9's 21 items are modelled as requirements; their **required vs optional** classification is a PO/evidence call (§26 `GP-CONS`, `GP-S2M`, `GP-S3`, `GP-BY`). No optional item is promoted to mandatory. |
| 3 | **SECR SI's own "large" definition + CA 2006 s.465 numerics** | Regulatory fact — legislation.gov.uk JS-walled | Applicability can be implemented for the **verified** parts (in-scope populations, **>40,000 kWh**, 2-of-3 over two consecutive FYs, 6 Apr 2025 change). The residual must be closed before the SI's precise "large" test is encoded verbatim. |
| 4 | **Directive (EU) 2026/470's own application dates** | Regulatory fact (detail) | The **framework version** is recorded with its OJ reference; the exact amended Article 5(2) dates must be transcribed before the CSRD phase dates are seeded. |
| 5 | **Irish competent authority designation** | Regulatory fact (context) | **No product requirement** arises (§24.6 of the verification report). No design impact. |
| 6 | **Whether the 2026 Simplified ESRS has been published in the OJ / entered into force** | Regulatory fact (forward-looking) | Represented as `ADOPTED_NOT_IN_FORCE`; must be re-verified at each framework-version review. |

**[D] None of these are invented, guessed, or silently resolved in this design.** Each is a **data/verification** action, not a schema change — which is precisely why the framework/requirement model uses free-form-but-controlled codes and status enums.

---

## 26. PO decisions required

The 13 decisions from the evidence tasks remain open; **this design makes none of them**. It does, however, convert most from "regulatory facts" into **design-shaping policy choices**, and raises a small number of design-specific decisions.

### 26.1 Carried-forward decisions — design impact

| # | Decision | Design impact | Nature |
|---|---|---|---|
| **A1** | Narrative field allowlist (keys, types, formatting, who may edit) | Shapes `disclosure_narratives` fields; **blocks S4** | Product/UX policy |
| **A3** | Narrative numeric limits | Determines whether a length/format constraint is modelled at all | Product policy |
| **P3** | Which sections/fields are customer-editable | Determines the editable set on `disclosure_values` vs narratives | Product/UX policy |
| **D11-CAT** | SECR/E1 **intensity denominator catalogue** | **Seeds `disclosure_intensity_denominator_types`** — needed before Stage 1 reference data | Product policy |
| **E1-COV** | Exact initial ESRS E1 disclosure coverage | Determines the E1 requirement rows to seed; **still gated by unresolved item 1** | Regulatory fact + policy |
| **E1-VER** | Which ESRS version to launch with | Determines the `disclosure_framework_versions` rows (2023 set in force; 2026 = FUTURE) | Product policy |
| **APPL** | Applicability-capture model | Shapes `disclosure_applicability_assessments` + the customer-facts UX | Product policy |
| **GP-CONS** | Consolidation-approach support | Whether the consolidation attribute is MVP or later | Product policy |
| **GP-GAS** | CO2e-only initially vs per-gas | Whether gas/GWP tables are MVP or deferred (**this design defers them**) | Product policy |
| **GP-S2M** | Market-based Scope 2 (dual reporting) | Whether the `scope2_method` dimension is MVP | Product policy |
| **GP-S3** | Scope 3 in the initial build | The Scope 3 requirement rows + category dimension | Product policy |
| **GP-BY** | Base year + recalculation in the initial build | Whether `disclosure_base_year_records` is MVP or deferred (**this design defers it**) | Product policy |
| **LEG** | D16 legacy-route disposition | **Independent** of this design; must not be bundled into disclosure work | Product/architecture policy |

### 26.2 New decisions this design raises

| # | Decision | Why the PO must decide | Options |
|---|---|---|---|
| **DM-1** | **`requirement_code` naming policy** | Determines whether E1 seeding waits for the identifier transcription | (a) concept keys + later mapping (**[REC]**); (b) block the E1 seed until identifiers are transcribed |
| **DM-2** | **Report-purpose ↔ `report_type` relationship** | `SUPPORTED_REPORT_TYPES` has exactly one entry; adding four purposes must not silently redefine `annual` | (a) `purpose_code` as a projection (**[REC]**); (b) expand `SUPPORTED_REPORT_TYPES` |
| **DM-3** | **Reporting-period semantics** (calendar vs financial year) | The engine derives `YYYY-01-01 → YYYY-12-31`; SECR/E1 applicability is **period-dated** | (a) keep calendar year for MVP; (b) configured financial period (**[REC]**) |
| **DM-4** | **Status of `benchmarking` content** | It is management content, not a disclosure; must not drift into coverage claims | (a) management-only (**[REC]**); (b) expose under a purpose |
| **DM-5** | **Finalisation policy for `NOT_SUPPORTED` / `CUSTOMER_INPUT_REQUIRED`** | Determines whether unresolved requirements block finalisation | (a) block on `REQUIRED` only, allow with recorded basis (**[REC]**); (b) block on both |
| **DM-6** | **Evidence drill-down depth for customers** | Whether customers reach the **line item** and document | (a) owner/admin full drill-down, viewer summary (**[REC]**); (b) restrict |
| **DM-7** | **Line-item population timing** | Whether historical documents are re-parsed | (a) forward-only + honest idempotent backfill (**[REC]**); (b) full historical re-extraction |

**[D] No decision above is made by this document.**

---

## 27. Design risks

| # | Risk | Severity | Why it matters | Mitigation (design-level) |
|---|---|---|---|---|
| **R1** | **Scope creep into a generic rules/template engine** while implementing requirement mappings | **High** | Directly contradicts D4 and destroys auditability | Enumerated `source_kind`/`aggregation` vocabulary; global catalogues are platform-controlled (§18.3) |
| **R2** | **Values shipped before the evidence link** | **High** | Re-creates the "emission → invoice" over-simplification the task forbids | Sequence Stage 2 with/after Stage 1; `disclosure_value_evidence` is MVP (§22.1) |
| **R3** | **Scope 2 method / per-gas capability gap in the calculation layer** | **High** | The disclosure layer can express requirements the engine cannot honestly satisfy | `NOT_SUPPORTED`/`PARTIALLY_SUPPORTED` + recorded reason; **no fabricated split**; deprioritise via `GP-S2M`/`GP-GAS` |
| **R4** | **Compliance-claim drift** in labels, templates or generated text | **High** | Contradicts the ratified assurance boundary | Reuse `AUDIT_NOT_ASSURANCE_NOTICE` semantics; §4 review rule; D16 stays separate |
| **R5** | **Identifier seeding before the ESRS evidence gap closes** | Medium | Inventing identifiers would corrupt the requirement catalogue | Concept keys + explicit `UNRESOLVED` marker; later data update (§12.1) |
| **R6** | **Date-blind applicability** (hard-coded thresholds) | Medium | **[V]** SECR thresholds changed on 6 Apr 2025 and are in active reform; CSRD scope changed in 2026 | Period-dated assessments; immutable framework versions (§8) |
| **R7** | **Historical report mutation** during backfill | **High** | Violates D15 | Backfill is additive and idempotent; unmatched stays `NULL`; no row rewriting (§20) |
| **R8** | **Evidence drill-down creating a tenant/PE leak** | **High** | Security regression across a new navigation path | Reuse existing guards + org scoping + PE boundary; mandatory DENY tests in Stage 10 (§19) |
| **R9** | **Two competing report spines** (a new instance table) | Medium | Would fracture the existing lifecycle | Bind to `report_generation_queue`/`report_versions` only (§9.3) |
| **R10** | **`is_current` / listing defect interacting with new versions** | Medium | **[R]** Documented latent defect (`…OPEN_DECISION_CLOSURE…` Issue 1) becomes active when multiple versions exist | The S1-A fix is recommended there; the disclosure design must not depend on `is_current` for value resolution |
| **R11** | **Unused template JSONB re-purposed as a requirement store** | Medium | Re-introduces template-as-requirement (D2) | `report_templates.template_structure` stays presentation-only (currently unreferenced by backend code **[R]**) |
| **R12** | **Over-large MVP** | Medium | Delays delivery and enlarges the review surface | 14 tables + 1 column; narratives/gas/base-year explicitly deferred (§22/§23) |

---

## 28. Final recommendation

**[REC] Recommend PO approval of this design as the Disclosure Model architecture, subject to the following:**

1. **Ratify the framework/version → requirement → mapping → value spine** (§6–§9, §18). It is the minimum structure that makes D2, D4, D12, D14 and D15 simultaneously true.
2. **Ratify the two-level classification semantics** — `requirement_class` on the requirement version, effective class derived from applicability (§7.2). This is the mechanism that keeps *regulatory applicability* and *CarbonTally capability* distinct.
3. **Ratify row-level traceability as MVP scope** — `evidence_line_items` + `calculation_snapshots.source_line_item_id` + `disclosure_value_evidence` (§14). It closes the one place where the current chain is genuinely coarser than the requirement.
4. **Ratify the reuse posture** — consume the calculation engine, bind to the existing report/version/lifecycle spine, reuse `units`, `activity_categories`, the D33 evidence chain and the non-assurance wording. **~23 existing tables are reused unchanged; one column is added.**
5. **Decide `DM-1` (identifier naming policy) early** so ESRS E1 seeding is not blocked by the unresolved Annex I representation limitation (§12.1, §26.2).
6. **Decide `DM-3` (period semantics)** before Stage 5, because applicability is period-dated (§8.2).
7. **Keep S4, D16, RLS remediation and Phase 8-X as separate authorised tasks** (§24, §32 of the task).
8. **Authorise Stage 1 only after decisions 1–4 are recorded**, with Stage 10 (independent verification, ALLOW **and** DENY) as a mandatory part of any implementation authorisation.

**What this design deliberately does not do:** it does not redesign the calculation engine, the report renderer, the lifecycle, RLS, the legacy route, or the 12-section template; it does not invent ESRS identifiers, thresholds, character limits, denominator sets, materiality rules or compliance claims; and it does not implement anything.

---

## 29. Final verdict

### `DESIGN COMPLETE — READY FOR PO REVIEW`

**Basis for the verdict:**
* All 29 mandated design sections are produced.
* The design is grounded in **verified repository facts** (migrations, code with file/line references) and **verified regulatory evidence** ([V] items from the regulatory verification and closure tasks).
* The two structural gaps the task identified as critical — **row-level/line-item traceability** and **separation of applicability from capability** — are addressed with concrete, minimal, reuse-first designs (§14, §7/§8).
* Unresolved regulatory evidence is **carried forward explicitly and not invented** (§25).
* The assurance/product boundary is preserved and structurally reused (§4).
* **Nothing was implemented**, no migration was created, no API/RLS/production change was made, and the legacy route was not touched.

**This verdict is NOT "implementation ready".** Gate 5 (implementation authorization) remains **NOT AUTHORIZED**, pending PO ratification of this design and of the decisions in §26.





















