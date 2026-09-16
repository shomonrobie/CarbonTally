# CarbonTally — Phase 8 Disclosure Model Decision Record

**Document:** `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md`
**Task reference:** `CT-P8-DISCLOSURE-DECISION-RECORD-20260912-006`
**Status:** PO RATIFICATION RECORD — **NO IMPLEMENTATION AUTHORISED**
**Date:** 2026-09-12
**Type:** Documentation / governance only. **No code, schema, migration, API, frontend, extraction, OCR/LLM, calculation, evidence-persistence, RLS, legacy-reporting, S4 or Phase 8-X change.**
**Governing decisions:** D1–D17 (`CARBONTALLY_PHASE8_REPORTING_ARCHITECTURE_PO_RATIFICATION_D1-D17_20260912.md`, PO-RATIFIED)
**Design input:** `CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md` (DESIGN OUTPUT — NOT IMPLEMENTED)
**Regulatory input:** `CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_20260912.md` (§24.11: `EVIDENCE CLOSURE PARTIAL — PO REVIEW REQUIRED`)
**Mandatory Cline report:** `docs/cline/reports/CT-P8-DISCLOSURE-DECISION-RECORD-20260912-006.md`
**Formalized forensic evidence (Gate 0):** `docs/cline/reports/CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md` · `docs/cline/reports/CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912.md`
**Gate 0 governance consolidation:** `docs/cline/reports/CT-P8-G0-GOVERNANCE-CONSOLIDATION-20260912-008.md`

---

## 1. Document control

| Item | Value |
|---|---|
| Repository baseline | branch `main`, HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| Record scope | The 20 ratified **Disclosure Model** decisions and their relationship to D1–D17 |
| Explicit non-scope | Implementation, migrations, APIs, frontend, extraction, OCR/LLM, calculation, evidence persistence, RLS, legacy reporting, S4 Narrative Overlay, Phase 8-X |
| Decision status values | `RATIFIED` · `CONDITIONAL` · `DEFERRED` · `SEPARATE WORKSTREAM` |
| Evidence tags | **[D]** PO decision · **[P]** prompt-supplied authoritative ruling · **[R]** repository fact · **[V]** verified regulatory fact · **[U]** unresolved · **[I]** interpretation · **[REC]** recommendation |
| Verdict discipline | This record ratifies **decisions**, not delivery. Gate 5 (implementation authorization) remains **NOT AUTHORIZED** |

**Rule of construction:** This document records only the decisions supplied by the Product Owner for
this task. It does **not** create new product decisions, does not select values where the PO left a
decision open, and does not invent regulatory identifiers, thresholds, limits or denominator sets.

### 1.1 Terminology governing this record (Gate 0 — G0-B)

The implementation programme this record governs is the **ratified Phase 8 Reporting / Disclosure
programme** — the reporting/disclosure implementation scope governed by D1–D17 and the 20 Disclosure
Model decisions. This is the terminology that **governs implementation tasks** referring to "Phase 8"
within this programme.

- **`Phase 8 — Advanced Analytics`** remains the **historical / master-roadmap label** recorded in
  `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` (*"official product-roadmap name. Same restrictions as
  Phase 7 (scope NOT defined; nothing authorized)"*). That wording is **preserved unchanged** and is
  **not** silently rewritten. Any change to it must go through the roadmap-governance process.
- **Phase 8-X — Operational Intelligence** remains the **separately bounded
  operational-intelligence extension/workstream**, governed by its own authoritative discovery/boundary.
- **No third interpretation of "Phase 8" is created.** A list of eight "Phase 8 capabilities" appears in
  the Phase 8-X discovery only as *task-prompt context*; it is **not** a ratified scope and is not adopted
  here.
- `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` is **not modified** by this record.

**Disposition:** the governing implementation terminology is the **Phase 8 Reporting / Disclosure
programme**; the master-roadmap wording is preserved; Phase 8-X is separate. Recorded under Gate 0 item
**G0-B**. Where documents disagree, the disagreement is **recorded, not silently reconciled**.


---

## 2. Purpose

This record makes the Phase 8 **Disclosure Model** decision set authoritative and unambiguous before
any implementation work begins. It exists so that:

1. the 20 Disclosure Model decisions are recorded once, with an owner, a status and an acceptance
   criterion each;
2. the relationship between those decisions and the already-ratified D1–D17 architecture is explicit;
3. the semantic invariants that implementation must never collapse (requirement vs applicability vs
   capability vs customer input; `CUSTOMER_INPUT_REQUIRED` vs `NOT_SUPPORTED`) are stated as binding;
4. the deferred / separate work boundaries are recorded so implementation does not absorb them;
5. the current Phase 8 gate and the change-control rule are on the record.


---

## 3. Relationship to D1–D17

D1–D17 established the **reporting architecture**. The 20 Disclosure Model decisions operate **inside**
that architecture — they constrain the design, semantics and content boundary of the Disclosure Model
layer. They do not reopen any D1–D17 decision.

| D-decision | Content (as ratified) | Relationship to the 20 Disclosure Model decisions |
|---|---|---|
| **D1** | Initial frameworks: GHG Protocol Corporate Standard (primary), UK SECR, ESRS E1 quantitative scope. GRI and IFRS S2 deferred | Constrains `E1-COV`, `E1-VER`, `GP-*` and the denominator boundary to these three frameworks only |
| **D2** | Canonical chain: AUTHORITATIVE DATA → CALCULATION/PROVENANCE → EVIDENCE → DISCLOSURE MODEL → NARRATIVE CONTENT → REPORT PURPOSE + TEMPLATE → EXPORT → FROZEN VERSIONED ARTEFACT | `GP-*` decisions populate the disclosure layer; `A1`/`A3`/`P3` bind narrative content; `DM-2` binds purpose |
| **D3** | Existing 12-section report is a **presentation template only**, not the canonical disclosure model | Reinforces `DM-1`, `DM-2`; no decision here promotes the 12-section report |
| **D4** | Template architecture is controlled, versioned and config-driven. No generic unrestricted rules/template engine | `D11-CAT`, `DM-1`, `DM-2` all operate within a closed, application-owned vocabulary |
| **D5** | Narrative architecture: requirement-bound disclosure narrative + bounded optional management commentary. No arbitrary report-wide editing | Directly implemented by `A1`, `A3`, `P3` |
| **D6-R** | Initial report purposes: Annual Carbon Report, Management Report, UK SECR Report, ESRS E1 Quantitative Report | Constrains `DM-2`, `DM-4`, `DM-6` |
| **D7-R** | ESRS E1 production scope: carbon/energy; structured climate support; explicit external/future boundaries. No full ESRS/CSRD claim | Constrains `E1-COV`, `E1-VER`, `APPL` |
| **D8** | GHG Protocol is the accounting foundation | Constrains `GP-CONS`, `GP-GAS`, `GP-S2M`, `GP-S3`, `GP-BY` |
| **D9** | Required GHG corporate-report content represented where applicable (boundaries, period, Scope 1/2, gases/CO2e, base year/recalculation, biogenic, methodologies, exclusions, changes, comparatives, inventory quality/uncertainty, facilities/contact) | Constrains `GP-CONS`, `GP-GAS`, `GP-BY` |
| **D10** | UK SECR structured treatment: energy kWh; relevant energy sources/transport; Scope 1/2; prior-year comparatives; intensity ratio; methodology/provenance; energy-efficiency action narrative; applicability | Constrains `D11-CAT` and the SECR denominator boundary (§13) |
| **D11** | SECR intensity ratio uses a controlled structured model. Customer selects/confirms a supported denominator type. CarbonTally may recommend but must not silently select | Directly implemented by `D11-CAT` |
| **D12** | Requirement semantics are richer than boolean required/not-required: Required, Conditional, Optional, Not Applicable, Unavailable, Customer Input Required, Not Supported/Future | Directly implemented by the `requirement_class` invariant and `DM-5` |
| **D13** | ESRS E1 is applicability-aware | Directly implemented by `APPL`, `E1-COV` |
| **D14** | Framework/regulatory versions and change management are explicit | Constrains `E1-VER`, `GP-BY` superseding chain, and the change-control statement (§19) |
| **D15** | Historical reports must remain reproducible through explicit framework/version binding | Constrains `DM-7` (non-destructive backfill) and `DM-1` (version-bound codes) |
| **D16** | Legacy reporting disposition is a separate bounded task. Do not modify legacy reporting during current Disclosure Model work | Directly implemented by `LEG` |
| **D17** | Authoritative-source-first governance | Constrains `E1-COV`, `DM-1` (never present internal keys as official identifiers) |

**Confirmation:** the 20 decisions below are **consistent with** D1–D17 as ratified. No D1–D17 decision is
reopened, weakened or replaced by this record. Where the design document had expressed a
**recommendation**, the PO ruling recorded here is the authoritative position; any sharpening of a prior
recommendation is recorded explicitly in §7 (per-decision) and in the Cline report.

---

## 4. Decision status legend

| Status | Meaning |
|---|---|
| **RATIFIED** | PO ruling is final; implementation may proceed against it once Gate 5 authorises implementation. |
| **CONDITIONAL** | PO ruling is recorded, but the decision is **not actionable** until a stated condition (usually authoritative-evidence closure) is met. It must not be treated as `RATIFIED`-and-ready. |
| **DEFERRED** | Concept is acknowledged and preserved for future extension; it is **not** initial-scope work. |
| **SEPARATE WORKSTREAM** | Governed by a different, separately authorised task; explicitly out of scope here. |

**Not the same as each other.** A decision may be `RATIFIED` in policy while its *implementation* remains
gated by the Phase 8 gates (§18). `CONDITIONAL` ≠ `DEFERRED`: a conditional decision is expected to become
actionable when its condition closes; a deferred decision is not planned for the initial model at all.

---

## 5. Disclosure Model decisions — index

| # | ID | Title | Status |
|---|---|---|---|
| 1 | `A1` | Narrative allowlist | RATIFIED |
| 2 | `A3` | Narrative numeric limits | RATIFIED |
| 3 | `P3` | Customer-editable content | RATIFIED |
| 4 | `D11-CAT` | Intensity denominator catalogue | RATIFIED |
| 5 | `E1-COV` | ESRS E1 coverage | **CONDITIONAL** |
| 6 | `E1-VER` | ESRS E1 version | RATIFIED |
| 7 | `APPL` | Applicability | RATIFIED |
| 8 | `GP-CONS` | Consolidation | RATIFIED |
| 9 | `GP-GAS` | Per-gas reporting | RATIFIED |
| 10 | `GP-S2M` | Scope 2 | RATIFIED |
| 11 | `GP-S3` | Scope 3 | RATIFIED |
| 12 | `GP-BY` | Base year | RATIFIED |
| 13 | `LEG` | Legacy route | RATIFIED (SEPARATE WORKSTREAM in execution) |
| 14 | `DM-1` | Requirement codes | RATIFIED |
| 15 | `DM-2` | Purpose vs `report_type` | RATIFIED |
| 16 | `DM-3` | Reporting period | RATIFIED |
| 17 | `DM-4` | Benchmarking | RATIFIED |
| 18 | `DM-5` | Finalisation | RATIFIED |
| 19 | `DM-6` | Drill-down | RATIFIED |
| 20 | `DM-7` | Line-item population | RATIFIED |

---

## 6. Decision detail

Each entry records: the decision, the PO ruling, the status, the implementation implication, the
acceptance criterion, and any deferred/separate boundary.
### A1 — Narrative allowlist · **RATIFIED**

- **Decision:** Whether customer narrative is bounded to a controlled, requirement-specific allowlist.
- **PO ruling [P]:** Narrative content must be bounded and requirement-specific. No arbitrary report-wide
  narrative editing. Customer Owner/Admin may author permitted customer-input narrative.
- **Implementation implication:** Narrative binding is per-requirement only; no free-form report-wide
  editor; authoring restricted to Customer Owner/Admin (per D5). Aligns with D5's rejection of the
  proposed arbitrary 7-fields × 4,000-characters model.
- **Acceptance criterion:** A customer without Owner/Admin role cannot author narrative; no UI/API path
  permits narrative outside a requirement binding.
- **Boundary:** The narrative *tables* are not built by this record (S4 is separate — §16).

### A3 — Narrative numeric limits · **RATIFIED**

- **Decision:** Whether arbitrary character/field limits are imposed on narrative.
- **PO ruling [P]:** Do not introduce arbitrary character/field limits based on assumptions. Use typed
  fields and normal technical validation. Regulatory limits may be represented only where authoritative
  evidence supports them.
- **Implementation implication:** No invented character caps; limits, if any, are evidence-backed data,
  not hard-coded policy. Consistent with the D1–D17 guardrail "Do not treat arbitrary narrative character
  limits as regulatory requirements".
- **Acceptance criterion:** No source file contains an unexplained narrative length constant; any limit is
  traceable to an authoritative source reference.
- **Status note:** Reaffirms an existing D1–D17 guardrail; no new limit is created here.

### P3 — Customer-editable content · **RATIFIED**

- **Decision:** Which content a customer may edit.
- **PO ruling [P]:** Customers may edit customer-owned inputs, permitted narratives/commentary, and
  applicable selections where explicitly allowed. Customers may **NOT** edit calculated emissions,
  provenance, emission-factor data, or system-derived authoritative values.
- **Implementation implication:** Enforced at the API boundary, not the UI; the disclosure layer exposes
  no write path to calculation/provenance/factor data. See §11 for the boundary statement.
- **Acceptance criterion:** DENY tests prove a customer write to a calculated/provenance/factor value is
  rejected server-side; ALLOW tests prove permitted customer inputs/narrative persist.
- **Boundary:** The customer-editable set is a capability list, not a blanket field permission.

### D11-CAT — Intensity denominator catalogue · **RATIFIED**

- **Decision:** The SECR intensity denominator model and its controlled catalogue.
- **PO ruling [P]:** Use a controlled CarbonTally denominator catalogue. The customer selects/confirms
  from supported denominator types. No unrestricted custom denominator.
- **Implementation implication:** Implements D11 at the catalogue level: a closed, application-owned set of
  denominator types; customer selection/confirmation is recorded; CarbonTally may recommend but must not
  silently select. Aligns with D4 (no generic rules engine).
- **Acceptance criterion:** The denominator is chosen from the controlled catalogue; a customer-authored
  arbitrary denominator is rejected; the selected denominator and its basis are persisted.
- **Boundary:** The exact catalogue contents remain subject to authoritative verification (D11: "The exact
  denominator catalogue and statutory treatment must be verified before implementation"). See §13.

### E1-COV — ESRS E1 coverage · **CONDITIONAL**

- **Decision:** Which ESRS E1 requirements CarbonTally may support in production.
- **PO ruling [P]:** Only ESRS E1 requirements that are authoritatively verified for production may be
  production-supported. Unresolved identifiers/coverage remain gated. Do not invent regulatory
  identifiers.
- **Status:** **CONDITIONAL** — dependent on authoritative evidence closure.
- **Condition:** Closure of the ESRS E1 identifier/coverage evidence gap (regulatory verification report
  §6 and §24.11; disclosure design §25 item 1).
- **Implementation implication:** E1 coverage cannot be marked production-supported while evidence is
  unresolved; such requirements carry an explicit unresolved marker and are never presented as verified
  official identifiers (D17).
- **Acceptance criterion:** Every production-supported E1 requirement maps to a verified authoritative
  source reference; no unverified identifier appears as official.
- **Boundary:** This is the **only** decision in this record whose status is `CONDITIONAL`.

### E1-VER — ESRS E1 version · **RATIFIED**

- **Decision:** Which ESRS E1 framework version CarbonTally binds to.
- **PO ruling [P]:** Use the authoritative 2023 ESRS E1 framework/version as amended and in force for the
  applicable reporting context. Later revisions not yet in force must be represented as
  future/not-in-force rather than silently applied.
- **Implementation implication:** Framework versions are explicit and version-bound (D14/D15); a
  not-yet-in-force revision is a distinct future version row, never an in-place edit. Aligns with
  design §6.5 (`ADOPTED_NOT_IN_FORCE`).
- **Acceptance criterion:** Every E1 disclosure resolves to a specific framework version; a
  not-in-force revision cannot be selected for reporting.
- **Boundary:** Whether a future revision has entered into force is re-verified at each framework-version
  review; it is not guessed.

### APPL — Applicability · **RATIFIED**

- **Decision:** How applicability is represented and determined.
- **PO ruling [P]:** Applicability is period-dated, version-bound, based on customer facts, and supported
  by a cited basis. If insufficient information exists the state is `UNDETERMINED`. Applicability must
  never be presented as legal advice or a legal determination by CarbonTally.
- **Implementation implication:** Applicability is a derived, recorded assessment (tenant-scoped,
  framework-version-bound, period-dated) with an explicit basis; `UNDETERMINED` is a first-class state and
  is never silently treated as not-applicable. Implements D13.
- **Acceptance criterion:** ALLOW/DENY tests prove `UNDETERMINED` is preserved and not coerced to
  not-applicable; no output text asserts a legal determination.
- **Boundary:** Legal determination remains outside CarbonTally (see §15).

### GP-CONS — Consolidation · **RATIFIED**

- **Decision:** Whether consolidation approach is modelled.
- **PO ruling [P]:** The consolidation approach must be supported as a structured reporting-context
  attribute in the initial model.
- **Implementation implication:** Consolidation approach (e.g. equity share / financial control /
  operational control, per D9 item 2) is a retained structured attribute of the reporting context, carried
  with the calculation context — not a free-text note. Aligns with design §10.1.
- **Acceptance criterion:** The consolidation approach is persisted as a structured value and is available
  to the disclosure layer; changing it mid-period does not silently rewrite historical values.
- **Boundary:** Multi-approach parallel reporting is future (design §23.2); not initial scope.

### GP-GAS — Per-gas reporting · **RATIFIED**

- **Decision:** Whether individual greenhouse gases are reported.
- **PO ruling [P]:** Initial production may be CO2e-focused. Do **not** fabricate seven-gas results.
  Per-gas reporting is deferred until genuinely supported by the calculation layer.
- **Implementation implication:** No fabricated per-gas split. Until the calculation layer carries per-gas
  data, per-gas requirements are represented honestly as unsupported/partial, not estimated. Implements
  D9 item 10 within capability.
- **Acceptance criterion:** No per-gas value is emitted unless derived from real per-gas calculation data;
  if unsupported, the state is explicit.
- **Boundary:** Full per-gas reporting is **DEFERRED** (§16).

### GP-S2M — Scope 2 · **RATIFIED**

- **Decision:** How Scope 2 is represented.
- **PO ruling [P]:** Location-based and market-based Scope 2 are distinct concepts. They must never be
  collapsed into one indistinguishable value.
- **Implementation implication:** Two distinct disclosure values (two selectors), not one `scope = "2"`
  field; a market-based value cannot be reported unless genuinely derived. Implements D9/D7-R within
  capability.
- **Acceptance criterion:** The model can hold location-based and market-based separately; no code path
  merges them into one value without a recorded distinction.
- **Boundary:** Where the calculation layer cannot yet produce a market-based figure, that is stated
  honestly (partial/unsupported), never synthesised.

### GP-S3 — Scope 3 · **RATIFIED**

- **Decision:** How Scope 3 is represented.
- **PO ruling [P]:** Scope 3 belongs in the disclosure architecture. It must be category-aware.
  Unsupported categories must be represented honestly.
- **Implementation implication:** Scope 3 requirements carry a category dimension; categories the platform
  cannot support are marked unsupported rather than silently omitted. Implements D9 within capability.
- **Acceptance criterion:** A Scope 3 disclosure is identifiable by category; unsupported categories are
  surfaced as such.
- **Boundary:** Category-level modelling beyond what the existing activity taxonomy maps is conditional on
  this decision and on calculation support (design §23.2).

### GP-BY — Base year · **RATIFIED**

- **Decision:** Whether base-year/recalculation functionality is built.
- **PO ruling [P]:** Full base-year/recalculation capability is **not** an MVP requirement. Preserve the
  concept for future extension without falsely claiming complete functionality.
- **Implementation implication:** The model preserves the concept (per D9 items 11–12) but does not claim
  full recalculation capability; no materiality threshold is invented.
- **Acceptance criterion:** No ability to claim complete base-year/recalculation functionality exists until
  it is genuinely built; the concept is representable for future extension.
- **Boundary:** Full base-year/recalculation functionality is **DEFERRED** (§16).

### LEG — Legacy route · **RATIFIED** (executed as a SEPARATE WORKSTREAM)

- **Decision:** Disposition of the legacy reporting route.
- **PO ruling [P]:** Legacy reporting is governed by the separate D16 disposition task. Do not modify it
  during Disclosure Model work.
- **Implementation implication:** The Disclosure Model work must not read-modify-write, disable, delete,
  migrate or re-route the legacy path (`POST /api/reports/generate-enhanced-report`) or alter its
  compliance wording.
- **Acceptance criterion:** The legacy route is byte-for-byte untouched by any Disclosure Model change;
  its disposition remains a D16 task.
- **Boundary:** **SEPARATE WORKSTREAM** (D16).

### DM-1 — Requirement codes · **RATIFIED**

- **Decision:** What identifiers the requirement catalogue uses.
- **PO ruling [P]:** Controlled internal concept keys may be used where official identifiers remain
  unresolved. Never present internal keys as official regulatory identifiers.
- **Implementation implication:** Requirement codes are controlled strings (D4); where an official
  identifier is not verified, the verified concept name is used with an explicit unresolved marker and
  later mapped when evidence closes. Implements D17.
- **Acceptance criterion:** Every internal concept key is distinguishable from, and never labelled as, an
  official identifier; unresolved codes carry an explicit marker.
- **Boundary:** Re-keying to official identifiers is a **data/verification update**, not a schema change,
  performed once evidence closes.

### DM-2 — Purpose vs `report_type` · **RATIFIED**

- **Decision:** The relationship between report purpose and the existing report type.
- **PO ruling [P]:** `purpose_code` and existing `report_type` remain separate. `purpose_code` =
  disclosure/reporting intent. `report_type` = existing engine capability.
- **Implementation implication:** The existing single-entry `SUPPORTED_REPORT_TYPES` (`annual`) is **not**
  silently redefined or expanded; purpose is carried as a separate projection on the instance binding.
- **Acceptance criterion:** No existing `report_type` value changes meaning; four purposes are
  representable without reviving or redefining legacy type labels. See §12.
- **Boundary:** Legacy type labels (SECR/CSRD/ISSB) are not revived by this decision (D16 remains
  separate).

### DM-3 — Reporting period · **RATIFIED**

- **Decision:** Reporting-period semantics.
- **PO ruling [P]:** Reporting period start and end must be explicit. Do not permanently assume
  calendar-year reporting.
- **Implementation implication:** The reporting period is an explicit, stored start/end; the current
  engine's derived `YYYY-01-01 → YYYY-12-31` assumption must not be treated as permanent, because
  applicability is period-dated (D13, `APPL`).
- **Acceptance criterion:** A non-calendar financial period is representable; applicability assessments
  bind to the explicit period.
- **Boundary:** Choice of default period configuration is a product/UX matter recorded here as a
  requirement, not a value.

### DM-4 — Benchmarking · **RATIFIED**

- **Decision:** The status of benchmarking content.
- **PO ruling [P]:** Benchmarking is management-only. Never treat benchmarking as regulatory disclosure
  evidence.
- **Implementation implication:** Benchmarking lives in the management-commentary/management-report space,
  never as a regulatory disclosure value or coverage claim.
- **Acceptance criterion:** No benchmark figure can satisfy or appear as a regulatory disclosure; no
  compliance/coverage claim references benchmarking.
- **Boundary:** Consistent with D6-R (Management Report is a distinct purpose) and the assurance boundary
  (§15).

### DM-5 — Finalisation · **RATIFIED**

- **Decision:** What blocks report finalisation.
- **PO ruling [P]:** Finalisation must account for unresolved `REQUIRED` requirements and required
  customer inputs. **Critical distinction:** `CUSTOMER_INPUT_REQUIRED` ≠ `NOT_SUPPORTED`. If an applicable
  required disclosure is `CUSTOMER_INPUT_REQUIRED` and the required information is missing, finalisation
  should be **blocked** unless an explicitly approved workflow resolves the condition. If an applicable
  required disclosure is `NOT_SUPPORTED`, CarbonTally must **surface that limitation honestly** — it must
  not silently omit the requirement or claim full support/compliance.
- **Implementation implication:** Finalisation gates on unresolved `REQUIRED` states; `CUSTOMER_INPUT_REQUIRED`
  is a resolvable block (input supplied or an approved resolving workflow), whereas `NOT_SUPPORTED` is a
  surfaced, non-masqueradable limitation. The two are never collapsed (see §8).
- **Acceptance criterion:** A report cannot finalise with an unresolved required `CUSTOMER_INPUT_REQUIRED`
  item unless an approved workflow resolves it; a required `NOT_SUPPORTED` item is surfaced and never
  silently omitted or presented as satisfied.
- **Sharpen note:** The design document had recommended "block on `REQUIRED` only, allow with recorded
  basis". This PO ruling **sharpens** that recommendation by distinguishing the two states explicitly.
  The PO ruling is authoritative (recorded, not silently reconciled — see Cline report §7).

### DM-6 — Drill-down · **RATIFIED**

- **Decision:** Evidence drill-down depth for customers.
- **PO ruling [P]:** Owner/Admin may receive full authorised drill-down:
  Disclosure → Calculation → Evidence line → Source document/line. Viewer access is controlled.
  Consultant access remains bounded by engagement scope and existing permissions.
- **Implementation implication:** Drill-down is authorized per role and tenant; Consultant visibility is
  bounded to their engagement and never widened by this decision. Reuses existing guards (D7/R8).
- **Acceptance criterion:** Owner/Admin can traverse to the authorised depth; Viewer is restricted;
  Consultant is bounded to engagement scope; cross-tenant/PE leakage is denied (ALLOW **and** DENY).
- **Boundary:** Drill-down *depth* is bounded by what evidence granularity actually exists (see §10).

### DM-7 — Line-item population · **RATIFIED**

- **Decision:** How historical line-item evidence is populated.
- **PO ruling [P]:** Reporting/evidence architecture must be **forward-compatible** with deterministic,
  idempotent historical population of line-item evidence from **existing persisted extraction data**
  where possible. Do **not** automatically re-extract historical documents merely to populate the new
  model.
- **Implementation implication:** Any historical population is additive, idempotent, deterministic and
  **non-destructive** (D15); it reads already-persisted extraction data; it does not re-run
  extraction/OCR/LLM over historical documents. Unmatched rows stay unmatched; no row is rewritten to
  manufacture provenance.
- **Acceptance criterion:** Re-running population creates no duplicates and mutates no existing
  calculation/evidence row; no historical document is re-extracted.
- **Boundary:** Automatic historical re-extraction to populate the new model is **PROHIBITED** (§16).
  The upstream extraction-fidelity dependency is a separate task (§10).

**Refinement — historical line-item boundary (Gate 0 — G0-F / G0-I):** The forensic findings
(`CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912`) make the following distinction explicit and binding:

1. **Where persisted line structure already exists** (`line_items[]` from CSV/XLSX or AI-line paths),
   historical population of line-item evidence is **deterministic and idempotent**, and is permitted
   under `DM-7`.
2. **Flat historical PDF/IMAGE records** that never persisted line structure **cannot** be converted into
   true line-level evidence merely by reading the existing JSONB — the per-line distinction was never
   recorded. Such records require a **separately implemented and verified re-parsing/extraction
   capability**; they are **not** backfillable deterministically.
3. Any historical **re-parsing/re-extraction** is a **separate, explicitly authorised task** — it is
   **never** performed silently, and **not** as part of Disclosure Model population.
4. Where line identity cannot be established, the record is treated **honestly** (document-level only;
   no fabricated line reference; classification stays partial). **No line-level provenance may be
   manufactured.**
5. Idempotency, non-destructiveness and "no silent historical re-extraction" remain **absolute**.

This refinement **clarifies** the existing `DM-7` ruling; it does **not** create a new Disclosure Model
decision, does not alter any other decision, and does not authorise any implementation.


---

## 7. Status of every decision

All 20 decisions are recorded. Status summary:

| Status | Decisions |
|---|---|
| **RATIFIED** (19) | `A1`, `A3`, `P3`, `D11-CAT`, `E1-VER`, `APPL`, `GP-CONS`, `GP-GAS`, `GP-S2M`, `GP-S3`, `GP-BY`, `LEG`, `DM-1`, `DM-2`, `DM-3`, `DM-4`, `DM-5`, `DM-6`, `DM-7` |
| **CONDITIONAL** (1) | `E1-COV` — dependent on authoritative evidence closure |
| **SEPARATE WORKSTREAM** (execution boundary) | `LEG` (D16 legacy disposition) |

**Important:** `RATIFIED` ratifies **policy**, not delivery. No decision here authorises implementation —
that remains gated by §18.

---

## 8. `NOT_SUPPORTED` vs `CUSTOMER_INPUT_REQUIRED`

This is the single most important semantic pair in the record. The two states must **never** be collapsed,
and neither may be silently omitted.

| State | Meaning | Correct platform behaviour |
|---|---|---|
| **`CUSTOMER_INPUT_REQUIRED`** | CarbonTally **has** the defined capability, but required customer-provided information has not been supplied | **Block finalisation** (where the requirement is applicable and required) until the customer supplies the information **or** an explicitly approved workflow resolves the condition |
| **`NOT_SUPPORTED`** | The applicable disclosure is **outside currently supported CarbonTally capability** | **Surface the limitation honestly**; never silently omit the requirement and never present it as fully supported/compliant |

**Binding rules:**

1. `CUSTOMER_INPUT_REQUIRED` ≠ `NOT_SUPPORTED`.
2. A `NOT_SUPPORTED` disclosure must not be silently omitted, and must not be presented as
   fully supported or compliant.
3. Capability is a property of the **requirement version** (`carbontally_capability`); it is **not** a
   statement about whether the disclosure legally applies.

**Anti-patterns that are prohibited:** hiding an unsupported requirement; rendering an unsupported
requirement as satisfied; treating missing customer input as an unsupported capability (or vice versa);
converting an `UNDETERMINED` applicability into `NOT_APPLICABLE`.

---

## 9. Requirement vs applicability vs capability vs customer input

These four concepts are **distinct** and must never be conflated (D12, D13):

```text
REQUIREMENT   ≠   APPLICABILITY   ≠   CAPABILITY   ≠   CUSTOMER INPUT
```

| Concept | Question it answers | Where it lives |
|---|---|---|
| **REQUIREMENT** | What does the framework/version say is required/conditional/optional? | A property of the **requirement version** (`requirement_class`, verbatim to the standard) |
| **APPLICABILITY** | Does it apply to this organisation for this explicit reporting period? | A derived, period-dated, version-bound assessment with a cited basis (`APPLIES` / `DOES_NOT_APPLY` / `UNDETERMINED` / `CUSTOMER_INPUT_REQUIRED`) |
| **CAPABILITY** | Can CarbonTally currently produce it? | `SUPPORTED` · `PARTIALLY_SUPPORTED` · `STRUCTURED_INPUT_REQUIRED` · `EXTERNAL_INPUT_REQUIRED` · `MISSING_CAPABILITY` · `FUTURE` · `NOT_APPLICABLE_TO_PRODUCT` |
| **CUSTOMER INPUT** | Is required customer-provided information available? | The customer-owned input state for a requirement |

**Applicability is not equivalent to capability.** A requirement can:

- apply *and* be supported;
- apply *but* require customer input;
- apply *but* be unsupported;
- not apply;
- be conditionally applicable;
- remain **`UNDETERMINED`**.

The model must represent these states **without turning CarbonTally into a legal-advice system** (§15).

**Two-level rule (from the design, ratified here):** `requirement_class` is a property of the requirement
version (what the standard says); the **effective** class for a given organisation and period is
**derived** from applicability. The two must never be conflated or overwritten.

---

## 10. Line-item traceability dependency

**This is recorded as a Phase 8 implementation dependency / acceptance invariant — NOT as a new product
decision.** No decision is created here; nothing is investigated or fixed here.

### 10.1 Intended traceability chain

```text
SOURCE DOCUMENT
   → SOURCE LINE / SOURCE REGION
   → EXTRACTION LINE ITEM
   → FACTOR MAPPING
   → VALIDATION
   → CALCULATION SNAPSHOT
   → EMISSIONS
   → EVIDENCE
   → DISCLOSURE
   → REPORT
```

The reporting architecture must ultimately support **appropriate-granularity** traceability:

```text
Report → Disclosure → Calculation → Evidence line item → Source line/document
```

and authorised **reverse** traceability (source → publications/reports that used it).

### 10.2 Honesty invariant

If source evidence only supports **document-level** provenance, CarbonTally **must not manufacture false
line-level precision**. Where no finer granularity genuinely exists (e.g. a single manually-entered
figure), the evidence line is a single synthetic row with no fabricated row reference and the
classification is explicitly partial.

### 10.3 Identified dependency — now formalized (Gate 0)

A **multi-line invoice example** exposed an **upstream extraction** problem, now **formalized** in
`docs/cline/reports/CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md`:

- **8 visible source invoice line items → only 1 extracted item.**
- The retained item can also be **semantically incorrect** (an activity/unit mixture such as a `Water`
  line's quantity paired with a `Waste` activity label).

**Formalized root cause (no new investigation):** **Primary = A (extraction)** — the deterministic
PDF/IMAGE path produces one flat record and mixes fields across lines; **architectural consequences =
E/F** (downstream granularity/provenance); **subsidiary = D** (frontend usability gap); **excluded =
B/C** (persistence / API collapse). The calculation layer is **not** at fault and is **not** to be
replaced.

This remains a **Phase 8 implementation dependency / acceptance invariant** — **not** a new product
decision. Remediation is batch **P1**, separately authorised and **not performed** here.

### 10.4 Relationship to `DM-7`

`DM-7` (with its Gate 0 refinement in §6) requires the reporting/evidence architecture to be
**forward-compatible** with deterministic, idempotent historical population of line-item evidence where
persisted line structure **already exists**, and **prohibits** silent automatic historical
re-extraction. Flat historical PDF/IMAGE records require a **separately authorised and verified
re-parsing/extraction capability**. The upstream extraction-fidelity dependency above is therefore
**not** a mandate to re-extract; it is a dependency whose remediation is batch **P1**.

---

## 11. Customer-editable vs system-authoritative boundary

Customer-editable content and system-authoritative data are **separate**. The disclosure layer must not
provide any mechanism for a customer to overwrite authoritative calculation/provenance data (`P3`).

| Domain | Contents | Editable by customer? |
|---|---|---|
| **Customer-editable** | customer-owned facts; permitted narrative; permitted commentary; explicitly allowed applicability selections | **Yes** (subject to role: Owner/Admin for narrative per `A1`) |
| **System-authoritative** | calculated emissions; provenance; emission factors; system-derived calculations; authoritative evidence relationships | **No — never** |

**Binding rules:**

1. Enforcement is server-side; the UI is not the boundary.
2. A customer write to a system-authoritative value must be rejected, not merely hidden.
3. The authoritative layer and the customer-input layer remain distinguishable in the data model.

---

## 12. `purpose_code` vs `report_type`

Recorded by `DM-2`:

| Concept | Meaning |
|---|---|
| **`purpose_code`** | disclosure / reporting **intent** (e.g. Annual Carbon Report, Management Report, UK SECR Report, ESRS E1 Quantitative Report — D6-R) |
| **`report_type`** | existing **engine capability** (today `SUPPORTED_REPORT_TYPES` has exactly one entry, `annual`) |

**Rules:**

1. They are **separate concepts** and must remain separate.
2. Do **not** merge them merely because an existing implementation may use `report_type` today.
3. The existing single-entry `SUPPORTED_REPORT_TYPES` is **not** silently redefined or expanded by this
   record.
4. Legacy type labels must **not** be revived into new meaning (D16 remains separate — `LEG`).

---

## 13. SECR intensity denominator boundary

Recorded by `D11-CAT` (implementing D11):

- The intensity ratio uses a **controlled CarbonTally denominator catalogue**.
- The **customer selects/confirms** a supported denominator type.
- CarbonTally **may recommend** an appropriate ratio, but must **not silently select** the denominator
  where judgment is required.
- **No unrestricted custom denominator.**
- The exact catalogue contents and the statutory treatment remain subject to **authoritative
  verification** before implementation (D11).
- The numerator, denominator, denominator unit, ratio, methodology, evidence/source and prior-year
  comparability remain explicit (D10/D11).

---

## 14. ESRS E1 applicability / version / coverage boundary

Three related decisions constrain ESRS E1 (`APPL`, `E1-VER`, `E1-COV`):

| Aspect | Recorded position |
|---|---|
| **Applicability (`APPL`)** | Period-dated, version-bound, customer-fact-based, with a cited basis; `UNDETERMINED` when facts are insufficient; **never** a legal determination by CarbonTally |
| **Version (`E1-VER`)** | Bind to the authoritative **2023 ESRS E1** framework/version **as amended and in force** for the applicable reporting context; later revisions not yet in force are represented as **future / not-in-force**, never silently applied |
| **Coverage (`E1-COV`)** | **CONDITIONAL** — only E1 requirements authoritatively verified for production may be production-supported; unresolved identifiers/coverage remain **gated**; **do not invent** regulatory identifiers |

**Boundary:** ESRS E1 is applicability-aware (D13), and CarbonTally must not claim full ESRS/CSRD
compliance merely because E1 capability exists (D7-R).

---

## 15. Assurance / product boundary

"Audit-ready" means **evidence-backed, reproducible reporting records and traceability within
CarbonTally's supported scope**. It does **not** imply external assurance.

**CarbonTally is NOT:**

- an auditor;
- an assurance provider;
- a certifier;
- a regulator;
- a legal advisor;
- an independent verifier;
- a statutory filing authority.

**CarbonTally must NOT claim (where unsupported):**

- independent assurance;
- certification;
- legal determination;
- statutory filing authority;
- full ESRS/CSRD compliance.

This preserves the ratified Phase 7 assurance boundary:
*"CarbonTally provides evidence-backed reporting and assurance-support; it is not an independent
assurance provider."*

---

## 16. Deferred / separate work

Explicit boundaries. None of the following is in scope for this record:

| Item | Boundary |
|---|---|
| **S4 Narrative Overlay** | SEPARATE subsequent task |
| **D16 legacy report disposition** | SEPARATE task (`LEG`) |
| **RLS remediation** | SEPARATE workstream |
| **Phase 8-X operational intelligence** | SEPARATE bounded workstream |
| **Full per-gas reporting** | DEFERRED until calculation support exists (`GP-GAS`) |
| **Full base-year / recalculation functionality** | DEFERRED (`GP-BY`) |
| **GRI** | DEFERRED (D1) |
| **IFRS S2** | DEFERRED (D1) |
| **Historical automatic re-extraction merely for new evidence population** | **PROHIBITED** by current decision (`DM-7`) |
| **Unresolved ESRS identifiers / coverage** | GATED until authoritative evidence is available (`E1-COV`) |

**Additional explicit non-scope for this record:** implementation, migrations, APIs, frontend, extraction,
OCR/LLM, calculation, evidence persistence, RLS, legacy reporting, S4, Phase 8-X — none is touched.

---

## 17. Implementation acceptance principles

Any future implementation of the Disclosure Model must satisfy these principles (derived from the 20
decisions and D1–D17; **no new product decision**):

1. **One authoritative calculation foundation.** No report purpose gets its own calculation engine or its
   own authoritative carbon facts (D2, D8).
2. **Disclosure Model is the canonical reporting layer.** Templates are presentation only (D2, D3).
3. **Controlled configuration only.** Enumerated vocabularies; no generic unrestricted rules/template
   engine (D4).
4. **Four distinct semantic states are preserved.** Requirement ≠ applicability ≠ capability ≠ customer
   input; `CUSTOMER_INPUT_REQUIRED` ≠ `NOT_SUPPORTED` (§8, §9).
5. **Honest gaps.** Unsupported/applicable requirements and `UNDETERMINED` applicability are surfaced,
   never hidden or masqueraded as satisfied (D12, `DM-5`).
6. **Versioned and reproducible.** Framework/requirement/mapping/template versions are explicit; finalised
   reports remain reproducible; referenced versions are never mutated (D14, D15).
7. **Traceability at appropriate granularity.** Report → Disclosure → Calculation → Evidence line →
   Source line/document, plus authorised reverse traceability; no fabricated line-level precision (§10).
8. **Non-destructive, idempotent evidence population.** No automatic historical re-extraction; no row
   rewritten to manufacture provenance (`DM-7`).
9. **Server-side authorization.** Customer-editable vs system-authoritative enforced at the API, with
   tenant/consultant/PE boundaries preserved; ALLOW **and** DENY tests required (D7, §11, `P3`, `DM-6`).
10. **Assurance boundary preserved.** No assurance/certification/legal/statutory-filing/compliance claims
    beyond supported scope (§15).
11. **Legacy untouched.** D16 remains a separate task (`LEG`).
12. **Mandatory written report.** Every implementation task requires a written report; independent
    verification (ALLOW + DENY) is a mandatory part of any implementation authorisation.

---

## 18. Current Phase 8 gate

| Gate | Status |
|---|---|
| **D1–D17** | PO-RATIFIED |
| **Regulatory requirement verification** | `EVIDENCE CLOSURE PARTIAL — PO REVIEW REQUIRED` — **open** (ESRS E1 identifiers unresolved; GHG Protocol Ch.9 lists unresolved; residual SECR numeric detail) |
| **Disclosure Model Design** | `DESIGN COMPLETE — READY FOR PO REVIEW` (NOT implementation-ready) |
| **This Decision Record (20 decisions)** | **COMPLETE — READY FOR PO REVIEW** |
| **Implementation authorisation (Gate 5)** | **NOT AUTHORIZED** |

**Gate position:** the disclosure architecture decisions are now on the record, but
**implementation remains gated**. `E1-COV` is `CONDITIONAL`; unresolved regulatory evidence is carried
forward and must not be invented. No implementation may begin until the PO reviews this record and a
subsequent implementation authorisation is issued.

---

## 19. Change-control statement

1. This record is the **authoritative statement** of the 20 Disclosure Model decisions. Where any other
   document conflicts with it, this record governs unless and until the PO amends it.
2. Any change to a decision in this record, or any new product decision, requires **explicit PO
   ratification** and a new/updated decision record. Decisions must not be changed silently in code,
   schema, comments or configuration.
3. `CONDITIONAL` decisions become actionable only when their stated condition closes **with evidence**;
   the status change itself must be recorded.
4. Framework/requirement/mapping versions referenced by finalised reports are **immutable**; a change
   creates a new version (D14, D15).
5. This record does **not** authorise implementation. The next step is **PO review**.
6. S4 Narrative Overlay, D16 legacy disposition, RLS remediation and Phase 8-X remain **separate,
   separately authorised** work.

---

**END OF DECISION RECORD**

*Recorded for PO review. No implementation performed. Gate 5 remains NOT AUTHORIZED.*











