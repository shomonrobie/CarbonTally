---
Document Type: Architecture & Compliance Discovery (DISCOVERY ONLY — no implementation)
Project: CarbonTally
Prompt ID: CT-P8-REPORTING-COMPLIANCE-ARCHITECTURE-DISCOVERY-20260912-001
Status: DISCOVERY COMPLETE — PO DECISIONS REQUIRED BEFORE ARCHITECTURE RATIFICATION
Created: 2026-09-12
Companion report: docs/cline/reports/CT-P8-REPORTING-COMPLIANCE-ARCHITECTURE-DISCOVERY-20260912-001.md
---

# CarbonTally — Phase 8 Reporting Compliance & Disclosure Architecture Discovery

> **Discovery only.** No implementation, schema, migration, API, frontend, RLS,
> authorization, narrative overlay or PDF-freeze work was performed. Every
> recommendation below is a **proposal**, not a requirement, unless it cites an
> authoritative source.

---

## 1. Executive Summary

**Central conclusion.** CarbonTally's current V3 reporting architecture is a
**fixed 12-section annual emissions report** produced by one engine
(`backend/engines/report_generation.py:65`). That structure is **not required by
any framework investigated**. Of its 12 sections, roughly **half are CarbonTally
evidence/provenance/technical metadata**, and **several disclosures that ARE
required by authoritative sources are absent**.

The architecture CarbonTally should build is:

```text
AUTHORITATIVE DATA → CALCULATION/PROVENANCE → EVIDENCE
        → DISCLOSURE / REQUIREMENT MODEL
        → NARRATIVE CONTENT
        → PRESENTATION / TEMPLATE
        → EXPORT → FROZEN VERSIONED ARTEFACT
```

…rather than `DATA → FIXED 12-SECTION REPORT`.

**The decisive evidence.** The GHG Protocol Corporate Standard — the only
authoritative source that specifies a full corporate GHG **report content list** —
publishes a **"Required information"** list (Chapter 9) alongside a separate
**"Optional information"** list, and the standard itself labels each chapter
**STANDARD** or **GUIDANCE**. That two-tier structure is precisely what
CarbonTally's architecture currently lacks: there is no machine-readable
representation of *which* content is required, by *which* framework, at *which*
version.

**Two material findings beyond the reporting question:**

1. **Existing framework-mapping capability is structural but empty.**
   `activity_categories` already carries `esrs_e1_category`, `issb_category`,
   `ghg_protocol_scope`, `ghg_protocol_category` (verified columns), but holds
   **0 rows** locally. A column's existence is **not** evidence of support.
2. **A live legacy route makes unsubstantiated compliance claims.**
   `POST /api/reports/generate-enhanced-report` is mounted
   (`backend/main.py:213` → `backend/routes/reports.py:30` →
   `backend/report_generator.py:1040`) and emits a PDF asserting *"Compliant with
   SECR/CSRD/ISSB reporting standards"* (`report_generator.py:328`) while
   serving the **SECR** report for `report_type` `CSRD` and `ISSB`
   (`report_generator.py:1058-1060`, commented `# Placeholder`). This
   **contradicts** the Phase 8 ratification's statement that legacy is
   *"unmounted and unreferenced"*. **Not fixed** — flagged for PO interpretation.

**The 12-section report should not be declared canonical.** It should be
reclassified as a **current presentation template over a narrower content set**,
pending a ratified disclosure model (§13, §23 PO-3).

**S4 cannot proceed on its current basis.** Its narrative allowlist (§10.1 of the
lifecycle spec — 7 keys) is a CarbonTally product proposal with **no
authoritative grounding**, and no authoritative source found in this pass
mandates the specific character/field limits. S4 *can* proceed once framework
scope and the disclosure model are ratified (§24).

---

## 2. Discovery Objective

Establish, on evidence, what CarbonTally's reporting and disclosure architecture
should be, so that:

1. compliance-supporting outputs are grounded in **authoritative** requirements;
2. the model can **change** as regulations and frameworks evolve, without
   redesigning the carbon ledger or calculation architecture;
3. regulatory requirements are **not confused** with voluntary standards,
   guidance, or CarbonTally product enhancements;
4. the later **S4 Narrative Overlay** implementation has a defensible foundation.

---

## 3. Scope and Non-Goals

**In scope:** framework/regulatory evidence gathering; current implementation
inspection; the 12-section assessment; requirement-to-capability mapping;
disclosure-model architecture recommendation; extensibility model; narrative
requirement analysis (not design); S4 readiness; PO decisions.

**Explicit non-goals (prohibited by the task and not performed):**
implementation; schema/migration changes; API or frontend changes; report
lifecycle changes; RLS or authorization changes; narrative overlay
implementation; PDF freezing; AI implementation; billing changes; production or
deployment changes; fixing unrelated defects (including the legacy
compliance-claim route).

---

## 4. Evidence Hierarchy

| Tier | Source type | Use in this document |
|---|---|---|
| 1 | Legislation/regulation + official government sources | **Requirement** evidence (SECR; CSRD/ESRS) |
| 2 | Official standard/framework publications | **Requirement** evidence (GHG Protocol; IFRS S2) |
| 3 | Official technical guidance | **Guidance** evidence (SECR guidance; GHG Protocol GUIDANCE chapters) |
| 4 | CarbonTally ratified architecture/product documents | **Product** evidence |
| 5 | CarbonTally actual implementation | **Capability** evidence (authoritative over tier 4 where they conflict) |
| 6 | Third-party/commercial platform material | **Comparison only** |

**Prohibited:** commercial platform marketing as evidence of regulatory
requirement. Where a requirement could not be established authoritatively, this
document states **"Not established from authoritative source."**

---

## 5. Regulatory / Framework Landscape

### 5.1 Classification (mandatory separation)

| Class | Framework | Status |
|---|---|---|
| **A. Legal/regulatory** | **UK SECR** — Companies (Directors' Report) and Limited Liability Partnerships (Energy and Carbon Report) Regulations 2018 | **Mandatory** for in-scope UK entities |
| **A. Legal/regulatory** | **EU CSRD** (Directive (EU) 2022/2464) with **ESRS** (Commission Delegated Regulation (EU) 2023/2772) | **Mandatory** for in-scope EU/Irish entities (phased) |
| **B. Voluntary standard** | **GHG Protocol Corporate Standard** | Voluntary standard; **adopted by reference** inside SECR guidance and widely used as the calculation basis |
| **B. Voluntary standard** | **IFRS S2 (ISSB)** | A standard whose **legal force depends on jurisdiction adoption** — adoption not verified here |
| **B. Voluntary standard** | **GRI 305** | Voluntary; requires entity-level choices |
| **C. Guidance** | SECR guidance (gov.uk); GHG Protocol GUIDANCE chapters; DEFRA/DESNZ conversion factors; SEAI factors | Guidance |
| **D. CarbonTally product/management** | benchmarking, internal benchmarking & management insights, dashboards, executive summary content | **NOT compliance** |

### 5.2 Verified source table

| Claim | Verbatim quote | Source |
|---|---|---|
| SECR is mandatory for quoted companies, large unquoted companies and large LLPs | "This guidance includes changes which take effect from 1 April 2019. These changes require all UK quoted companies to report on their global energy use in addition to greenhouse gas emissions in their annual Directors' Report. There are also requirements for large unquoted companies and limited liability partnerships to disclose their annual energy use and greenhouse gas emissions and related information." | https://www.gov.uk/government/publications/environmental-reporting-guidelines-including-mandatory-greenhouse-gas-emissions-reporting-guidance |
| SECR required content set | "large unquoted companies and large LLPs are obliged to report their UK energy use and associated greenhouse gas emissions as a minimum relating to gas, electricity and transport fuel, as well as an intensity ratio and information relating to energy efficiency action, through their annual reports." | Environmental reporting guidance (SECR), March 2019, §7 — https://assets.publishing.service.gov.uk/media/67161e8696def6d27a4c9ab3/environmental-reporting-guidance-secr-march-2019.pdf |
| SECR "large" threshold | "The qualifying conditions are met by a company or LLP in a year in which it satisfies two or more of the following requirements: • Turnover £36 million or more • Balance sheet total £18 million or more • Number of employees 250 or more" | same SECR guidance (p.29) |
| SECR quoted-company disclosures | "Annual global emissions … • At least one intensity ratio … • Previous year's figures for energy use and GHG emissions (except in the first year). • Methodologies used in calculation of disclosures." | same SECR guidance (p.30, §3) |
| GHG Protocol Chapter 9 is a STANDARD chapter with a required/optional split | "Chapter 9 Reporting GHG Emissions S T A N D A R D G U I D A N C E 62" / "Required information" / "Optional information" | GHG Protocol Corporate Standard (revised edition) — https://ghgprotocol.org/sites/default/files/standards/ghg-protocol-revised.pdf |
| GHG Protocol minimum requirement | "The GHG Protocol Corporate Standard requires reporting a minimum of scope 1 and scope 2 emissions." | same, Ch. 9 |
| GHG Protocol required content | "A public GHG emissions report that is in accordance with the GHG Protocol Corporate Standard shall include the following information:" | same, Ch. 9 |
| GHG Protocol principles | "Reported information shall be 'relevant, complete, consistent, transparent and accurate.'" | same, Ch. 9 |
| IFRS S2 status and effective date | "In June 2023, the ISSB issued IFRS S2 Climate-related Disclosures…" / "IFRS S2 is effective for annual reporting periods beginning on or after 1 January 2024 with earlier application permitted as long as IFRS S1 General Requirements for Disclosure of Sustainability-related Financial Information is also applied." | https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/ |
| ESRS GHG disclosure | "E1-6 – Gross Scopes 1, 2, 3 and Total GHG emissions" (paragraph 44); "E1-5 Energy consumption and mix paragraph 37"; "GHG emissions intensity paragraphs 53 to 55" | Commission Delegated Regulation (EU) 2023/2772 — https://eur-lex.europa.eu/eli/reg_del/2023/2772/oj |
| CSRD scope | "large undertakings and all undertakings, except micro undertakings, whose securities are admitted to trading on a regulated market in the Union to report sustainability information" | Directive (EU) 2022/2464 — https://eur-lex.europa.eu/eli/dir/2022/2464/oj |
| **GRI 305 content** | **Not established from authoritative source.** The GRI 305 PDF returned HTTP 404 and no GRI 305 disclosure text could be retrieved in this pass. | (not retrieved) |

---

## 6. Applicability Boundaries

Applicability is **entity-specific**. CarbonTally must not assume every customer
is subject to every framework.

| Framework | Who is in scope | Threshold / trigger | Effective | Regulatory? |
|---|---|---|---|---|
| **UK SECR** | UK-incorporated quoted companies; **large unquoted companies**; **large LLPs** required to prepare a Directors' Report | **2 of 3:** turnover ≥£36m; balance sheet ≥£18m; ≥250 employees | Changes effective **1 April 2019** (energy use addition) | **Yes** |
| **EU CSRD + ESRS** | Large undertakings; listed undertakings (except micro); PIEs >500 employees | EU accounting thresholds | **Phased** — see note | **Yes** |
| **GHG Protocol** | Any organisation choosing to report, or required to by another regime (SECR guidance invokes Scope 1/2) | Voluntary | n/a | **No** (voluntary standard) |
| **IFRS S2 / ISSB** | Entities in a jurisdiction that has **adopted** the standard | **Jurisdiction adoption not verified in this pass** | Standard effective 1 Jan 2024 | **Depends on adoption** |
| **GRI 305** | Reporting organisations choosing GRI | Voluntary | n/a | **No** |

> **CSRD applicability note — UNVERIFIED.** The CSRD application timetable has
> been subject to legislative amendment. This discovery **did not establish** the
> current phased application dates or any omnibus simplification. That is an
> **applicability uncertainty requiring PO/legal confirmation** and is a
> contributing reason for the final verdict.

**CarbonTally-specific relevance signal (repository evidence):** the calculation
domain explicitly distinguishes **DEFRA** (UK) and **SEAI** (Ireland) factor
sources, and the engine carries CO2 vs CO2e provenance rules for each
(`backend/engines/report_generation.py:14-20`). This is **evidence that UK and
Irish customer segments are already intended**, which is why SECR and EU/Ireland
frameworks are treated as realistically relevant while GRI is not (absent
evidence).

---

## 7. GHG Protocol Findings

**Status:** voluntary standard; **the only source found that specifies a complete
corporate GHG report content list.** Structure verified from the standard PDF:
11 chapters, each labelled **STANDARD** or **GUIDANCE**; Chapter 9 is a STANDARD.

**Principles (STANDARD):** relevance, completeness, consistency, transparency,
accuracy.

**Minimum:** "requires reporting a minimum of scope 1 and scope 2 emissions."

**Chapter 9 "Required information" — verbatim structure (required):**

```text
DESCRIPTION OF THE COMPANY AND INVENTORY BOUNDARY
  • organizational boundaries chosen, including the chosen consolidation approach
  • operational boundaries chosen, and if scope 3 is included, a list
    specifying which types of activities are covered
  • the reporting period covered

INFORMATION ON EMISSIONS
  • total scope 1 and 2 emissions independent of any GHG trades
    (sales, purchases, transfers, banking of allowances)
  • emissions data separately for each scope
  • emissions data for all six GHGs separately (CO2, CH4, N2O, HFCs, PFCs, SF6)
    in metric tonnes and in tonnes of CO2 equivalent
  • year chosen as base year, and an emissions profile over time consistent with
    the chosen policy for base year emissions recalculations
  • appropriate context for any significant emissions changes that trigger
    base year emissions recalculation
  • emissions data for direct CO2 from biologically sequestered carbon,
    reported separately from the scopes
  • methodologies used, providing a reference or link to any calculation tools
  • any specific exclusions of sources, facilities and/or operations
  • causes of emissions changes that did not trigger a base year recalculation
  • GHG emissions data for all years between base year and reporting year
  • information on inventory quality (causes/magnitude of uncertainties) and
    policies to improve it
  • information on any GHG sequestration
  • a list of facilities included in the inventory
  • a contact person

INFORMATION ON OFFSETS
  • offsets purchased/developed outside the inventory boundary, subdivided by
    GHG storage/removals and emissions reduction projects, with verification status
  • reductions inside the boundary sold/transferred as offsets, with verification status
```

**Chapter 9 "Optional information" (explicitly optional) includes:** scope 3
emissions data; emissions subdivided by business unit/facility/country/source
type/activity type; performance measured **against internal and external
benchmarks**; relevant **ratio performance indicators**; outline of GHG
management/reduction programmes; contractual GHG-risk provisions; external
assurance outline; offsets detail.

> **Architectural consequence:** the standard itself separates *required* from
> *optional*. Any CarbonTally model that cannot express that distinction cannot
> claim GHG Protocol conformity.

---

## 8. UK SECR Findings

**Status: LEGAL REQUIREMENT (UK).** Guidance: gov.uk "Environmental reporting
guidelines: including Streamlined Energy and Carbon Reporting requirements"
(DESNZ/Defra), March 2019.

**Required disclosures — quoted companies (verified, SECR guidance p.30 §3):**

1. Annual **global** emissions from activities for which the company is
   responsible (combustion of fuel, operation of any facility) **plus** annual
   emissions from purchase of electricity, heat, steam or cooling for own use
   *(= global Scope 1 + Scope 2)*.
2. **At least one intensity ratio.**
3. **Previous year's figures** for energy use and GHG emissions (except first year).
4. **Methodologies used** in calculation of disclosures.
5. *(FY starting on/after 1 April 2019)* **Underlying global energy use** used to
   calculate GHG emissions, **including previous year's figure**.
6. Information about **energy efficiency action taken**.

**Required disclosures — large unquoted companies and LLPs (verified):** UK energy
use (as a minimum gas, electricity and transport, incl. UK offshore area);
associated GHG emissions; **previous year's figures** for energy use and GHG
emissions; **at least one intensity ratio**; **energy efficiency action taken**;
**methodology used**.

**Energy is a first-class required quantity:** the report "must disclose a figure,
**in kWh**, of the annual quantity of energy consumed" from gas combustion,
electricity purchase and transport fuel.

> **Architectural consequence:** SECR requires (a) an **intensity ratio**,
> (b) **prior-year comparatives**, (c) **energy in kWh** as a reported figure, and
> (d) **narrative** ("energy efficiency action taken"). None of these four exists
> as a first-class output of the current V3 12-section engine (§12, §13).

---

## 9. GRI 305 Findings

**Status: NOT ESTABLISHED FROM AUTHORITATIVE SOURCE.**

* Classification: **voluntary** standard set.
* The GRI 305 publication could not be retrieved in this pass (HTTP 404 on the
  standard PDF; the standards site returned 200 but no GRI 305 disclosure content
  was captured).
* **Therefore GRI 305 must not be used to justify requirements** in this
  architecture until authoritative content is obtained.
* Recommendation: treat GRI as **LATER / not in initial scope** unless the PO
  identifies a customer segment that requires it (§23 PO-1).

---

## 10. IFRS S2 / ISSB Findings

**Verified:** issued by the ISSB in **June 2023**; effective for annual reporting
periods beginning **on or after 1 January 2024**, earlier application permitted
**only if IFRS S1 is also applied**; the standard **integrates and builds on the
TCFD recommendations** and incorporates industry-based guidance.

**Not established in this pass:** which jurisdictions have **adopted** IFRS S2 and
on what timetable (jurisdiction adoption is what converts it into a legal
obligation). Because adoption is unverified, IFRS S2's applicability to
CarbonTally's customers is **UNVERIFIED**.

**Architectural consequence:** IFRS S2 is a **governance/strategy/risk/metrics and
targets** disclosure framework, not merely a GHG-quantity framework. Its
non-quantitative content (governance, strategy, risk management, scenario
analysis) is largely **not** derivable from CarbonTally's carbon ledger and would
be **management commentary** — reinforcing the need for a narrative layer
distinct from system-generated figures, and reinforcing that CarbonTally must not
present itself as providing IFRS S2 compliance.

---

## 11. Ireland / EU Findings

**Relevant framework: CSRD + ESRS E1 (Climate change).**

| Attribute | Finding |
|---|---|
| Jurisdiction | European Union (Ireland is a member state) |
| Instrument | Directive (EU) 2022/2464 (CSRD); Commission Delegated Regulation (EU) 2023/2772 (**ESRS**) |
| Applicability | "large undertakings and all undertakings, except micro undertakings, whose securities are admitted to trading on a regulated market in the Union"; PIEs with >500 employees |
| Effective/applicability date | **UNVERIFIED — phased; amendments not established in this pass** |
| Regulatory or voluntary | **Regulatory** (Directive; Member State transposition) |
| Why it belongs in initial reporting architecture | The calculation domain already carries **SEAI (Irish) emission factors** with dedicated CO2-only provenance handling (`report_generation.py:14-20`), evidencing an intended Irish customer segment; and ESRS **E1-6 "Gross Scopes 1, 2, 3 and Total GHG emissions"** (para 44) plus **E1-5 "Energy consumption and mix"** (para 37) and **GHG emissions intensity** (paras 53-55) overlap substantially with SECR/GHG Protocol quantity data |

**Do not assume every customer is subject to CSRD.** Applicability is
entity-specific and date-dependent.

> **Recommendation:** include **ESRS E1 quantitative subset** (Scopes 1/2/3 totals,
> energy consumption/mix, GHG intensity) in the **initial disclosure model** as a
> **mapping target**; treat the full ESRS datapoint set as **LATER / out of
> initial scope** (§23 PO-7).

---

## 12. Current CarbonTally Reporting Architecture

### 12.1 Authoritative V3 engine (verified from implementation)

`backend/engines/report_generation.py:65` defines `_SECTION_ORDER`, the
authoritative ordered 12 sections:

| # | `section_id` | Title |
|---|---|---|
| 1 | `metadata` | Report metadata |
| 2 | `organization` | Organization |
| 3 | `period` | Reporting period |
| 4 | `totals` | Emissions totals |
| 5 | `scopes` | Scope summaries |
| 6 | `activities` | Category / activity summaries |
| 7 | `validation` | Validation |
| 8 | `benchmarking` | Benchmarking |
| 9 | `provenance` | Factor provenance |
| 10 | `calculation` | Calculation information |
| 11 | `lineage` | Source lineage |
| 12 | `generation` | Generation metadata |

Engine properties (verified):
* **"Structured report generation only… No rendering is performed here."**
* **"No data is invented: sections with insufficient data are represented
  explicitly (`insufficient_data` / availability states) rather than as fabricated
  zeros."**
* Provenance-aware units: `kg CO2` / `kg CO2e` / `kg CO2/CO2e mixed`; SEAI CO2-only
  results are **never** relabelled as full CO2e.
* `ENGINE_VERSION = "1.0"` stamped into `generation`.
* Strict validation + blocking errors → `ValidationFailedError`, **no report persisted**.

### 12.2 Catalogue and identity model

* **Exactly one report type:** `SUPPORTED_REPORT_TYPES = {"annual": …}`
  (`backend/api/v3_reports.py:63`); anything else → **HTTP 422**.
* Normative distinctions ratified (`..._REPORTING_LIFECYCLE_SPEC_20260912.md` §4.4,
  §5): **type** vs **instance** (org + reporting year) vs **version** vs **artefact**.
  Report instances, versions, artefacts, dashboards and analytics endpoints are
  **not** report types.

### 12.3 Lifecycle (S3 — implemented)

`supabase/migrations/20260913000000_p8_report_lifecycle_status.sql` adds
`report_versions.status` with a CHECK constraint over:

```text
DRAFT · REVIEWED · CHANGES_REQUESTED · REJECTED · APPROVED · FINAL
```

Migration comment (verified): *"Approved/final versions are immutable; a
post-approval change creates a [new version]"*; default `DRAFT`; existing rows
converge to `DRAFT`.

### 12.4 API surface (verified endpoints, `backend/api/v3_reports.py`)

`GET /types` · `GET ""` · `POST ""` · `GET /{id}` · `GET /{id}/content` ·
`GET /{id}/versions` · `GET /{id}/download` · `GET /{id}/pdf` ·
`POST /{id}/versions/{n}/submit` · `.../request-changes` · `.../reject` ·
`.../approve` · `.../finalize` · `POST /{id}/versions`.

### 12.5 Content classification (ratified in the lifecycle spec)

* **§9.13 rule:** *"System-controlled = every key produced by
  `ReportGenerationEngine` inside the twelve sections."* **All 12 sections are
  classified System-controlled (all).**
* **§10.1 proposed editable namespace** (7 keys): `management_commentary`,
  `organisational_context`, `operational_changes_explanation`, `initiatives`,
  `reduction_actions`, `future_plans`, `section_notes.{section_id}`.
* **§15.1:** narrative overlay to be stored in a **dedicated JSONB column**
  (`narrative_overlay` on `report_versions`), **not merged into `content`**.
* **§15.3:** a narrative edit is **not** a carbon-data correction; it may never
  alter emissions, snapshots, factors, evidence, provenance, validation,
  benchmark, lineage or audit records.

### 12.6 Existing framework-mapping capability (structural only)

`activity_categories` (verified columns): `activity_type`, **`esrs_e1_category`**,
**`issb_category`**, **`ghg_protocol_scope`**, **`ghg_protocol_category`**.
Consumed by `backend/utils/emissions.py::get_activity_category` via
`backend/routes/upload.py`. **Row count locally: 0.** The mapping concept
**exists structurally but is not populated** — treat as a **latent seed**, not a
capability.

### 12.7 Tests and frontend

* Backend: `tests/unit/api/test_v3_reports.py`,
  `tests/unit/api/test_v3_report_lifecycle.py`, `tests/unit/api/test_reporting.py`.
* Frontend: `frontend/src/v3/reports/{ReportsPage,ReportDetailPage}.jsx`;
  `frontend/src/v3/__tests__/reports-page.test.jsx`.
* `report_comments.section_id` **"matches the 12 engine `section_id` values
  exactly"** (lifecycle spec §16.1) — a schema-level coupling to the 12 sections.

### 12.8 Stage status

`S1` (repository-level `is_current` fix; **no migration**) and `S3` (version
lifecycle) are **COMPLETE**. `S2` (RLS/`narrative_overlay` column) and `S4`
(narrative overlay) remain. **A1 (narrative allowlist)** and **A3 (narrative
limits)** are recorded as `DEFER` — *"Decide before S4"*.

### 12.9 DISCREPANCY — documentation vs implementation (material)

| Document claim | Implementation evidence | Assessment |
|---|---|---|
| Phase 8 ratification: legacy reports are **"unmounted and unreferenced"**; leaving untouched is safe | `backend/main.py:213` mounts `routes.reports`; `backend/routes/reports.py:22,30` includes `report_generator`'s router; `backend/report_generator.py:1040` defines `POST /generate-enhanced-report` → live at **`POST /api/reports/generate-enhanced-report`** | **CONFLICT.** The legacy route **is mounted**. Reported, **not fixed** |
| (implied) reports do not claim regulatory compliance | `report_generator.py:328` emits **"Compliant with SECR/CSRD/ISSB reporting standards"**; `report_generator.py:1008` states the report "has been prepared in accordance with the … (SECR) regulations"; `report_generator.py:1058-1060` returns the **SECR** report for `CSRD`/`ISSB` with comment `# Placeholder` | **Unsubstantiated compliance claims in a live route.** Reported, **not fixed** |
| Email templates | `backend/utils/email.py:239` advertises "Generate compliance reports (SECR, CSRD, ISSB)" | Product claim inconsistent with the single `annual` catalogue. Reported, **not fixed** |
| Legacy PDF generator has narrative + YoY | `backend/report_generator.py` includes `add_methodology_section` (1 Overview, 2 Calculation Method, 3 Data Sources, 4 Key Assumptions, 5 Limitations, 6 Compliance) and sections incl. "3. Year-over-Year Comparison" | Legacy surface contains **narrative and prior-year** concepts the V3 engine lacks — relevant to S4, but **not authoritative** |

---

## 13. Current 12-Section Assessment

### 13.1 Is a 12-section structure required by any framework?

| Framework | Requires a 12-section structure? |
|---|---|
| GHG Protocol Corporate Standard | **NO** — Ch. 9 specifies required *information*, not a section structure |
| UK SECR | **NO** — specifies required *disclosures* in a Directors' Report / Energy and Carbon Report |
| GRI 305 | **Not established from authoritative source** — and GRI does not prescribe a report's internal section structure |
| IFRS S2 / ISSB | **NO** — prescribes disclosure *content areas*, not a section structure |
| Ireland/EU (CSRD/ESRS) | **NO** — ESRS prescribes datapoints, not a report section structure |

> **Answer: NO framework investigated requires a 12-section structure.**

### 13.2 What purpose does it serve?

It is a **CarbonTally engineering/e presentation decision**: a deterministic,
JSON-serialisable content contract that composes calculation, validation,
benchmarking, provenance and lineage outputs into a stable, ordered structure for
later rendering and API consumption. This is legitimate and valuable — it is
simply **not** a compliance construct.

### 13.3 Section-by-section mapping

| # | Section | Corresponds to a disclosure requirement? | Classification |
|---|---|---|---|
| 1 | `metadata` | **No** framework disclosure. Supports GHG Protocol "methodologies used … reference or link to calculation tools" (partial) | CarbonTally technical metadata |
| 2 | `organization` | **GHG Protocol REQUIRED** — "Description of the company and inventory boundary" — but **missing** boundary/consolidation | **Required (partial)** |
| 3 | `period` | **GHG Protocol REQUIRED** — "The reporting period covered" | **Required (satisfied)** |
| 4 | `totals` | **GHG Protocol REQUIRED** — total Scope 1+2 independent of GHG trades; **SECR** — associated GHG emissions. Missing "independent of any GHG trades" statement | **Required (partial)** |
| 5 | `scopes` | **GHG Protocol REQUIRED** — "emissions data separately for each scope" | **Required (satisfied)** |
| 6 | `activities` | **GHG Protocol OPTIONAL** — subdivision by activity type | **Optional / product** |
| 7 | `validation` | **Not required** by any framework | CarbonTally QA evidence |
| 8 | `benchmarking` | **GHG Protocol OPTIONAL** — "performance measured against internal and external benchmarks"; also a **Phase 8 product capability** | **Optional / product** |
| 9 | `provenance` | Not itself a disclosure; **supports** transparency + "methodologies used" | CarbonTally evidence |
| 10 | `calculation` | **GHG Protocol REQUIRED** — "Methodologies used, providing a reference or link to any calculation tools used" (partial: has `methodology`, `algorithm_version`) | **Required (partial)** |
| 11 | `lineage` | Not a required disclosure; supports traceability | CarbonTally evidence |
| 12 | `generation` | Not a required disclosure | CarbonTally technical metadata |

**Summary:** **4 sections carry (partial) required disclosure content**; **6 are
CarbonTally evidence/technical metadata**; **2 map to *optional* framework
content**. There is **no narrative section** and **no presentation/template
section**.

### 13.4 Required disclosures MISSING from the current structure

| Missing disclosure | Authority | Present? |
|---|---|---|
| Organizational boundary + **consolidation approach** | GHG Protocol (required) | **MISSING** |
| Operational boundary (+ scope 3 activity list if included) | GHG Protocol (required) | **MISSING** |
| **Six GHGs separately** (CO2, CH4, N2O, HFCs, PFCs, SF6) in t and tCO2e | GHG Protocol (required) | **MISSING** (only `gas_coverage` labels + CO2/CO2e units) |
| **Base year** + recalculation policy + emissions profile over time | GHG Protocol (required) | **MISSING** |
| Context for significant changes triggering base-year recalculation | GHG Protocol (required) | **MISSING** |
| **Biologically sequestered carbon CO2**, reported separately | GHG Protocol (required) | **MISSING** |
| **Specific exclusions** of sources/facilities/operations | GHG Protocol (required) | **MISSING** |
| Causes of changes **not** triggering recalculation | GHG Protocol (required) | **MISSING** |
| **Offsets** information | GHG Protocol (required) | **MISSING** |
| All years between base year and reporting year; inventory-quality/uncertainty; sequestration; facility list; contact person | GHG Protocol (required) | **MISSING** |
| **At least one intensity ratio** | **SECR (legal)**; ESRS E1 intensity | **MISSING** |
| **Previous year's figures** (energy use + GHG emissions) | **SECR (legal)** | **MISSING** from the V3 engine (present only in the **legacy PDF**) |
| **Energy use in kWh** as a reported figure | **SECR (legal)** | **MISSING** as a report figure (activity-level quantities exist) |
| **Energy efficiency action taken** | **SECR (legal)** | **MISSING** (narrative; no section) |
| Methodology used | SECR (legal) | **PARTIAL** (`calculation`) |

### 13.5 Redundancy / presentational-only sections

`metadata`, `generation`, `lineage`, `validation`, `provenance` are
**non-disclosure** content. They are **not worthless** — they are the evidence and
traceability substrate that Phase 7 and assurance-support require, and they serve
internal/management reporting (Class B and C). They should **not** be deleted;
they should be **reclassified as a separate output layer** (§17).

### 13.6 Recommendation for the 12-section structure

**Do not declare it canonical. Do not delete it.**

Recommended classification: **"current presentation template over the V3
evidence + emissions content set"** — i.e. it becomes a *template* (one of
possibly several), while the *disclosure model* becomes the compliance-facing
contract. Rationale: no framework requires it; it omits required disclosures; and
it conflates compliance content with evidence/technical metadata — while still
being a useful, working, tested presentation contract that should be preserved
and versioned rather than discarded.

---

## 14. Requirement-to-Capability Matrix

Statuses: **SUPPORTED** · **PARTIALLY SUPPORTED** · **NOT CURRENTLY SUPPORTED** ·
**NOT APPLICABLE / OUT OF INITIAL SCOPE** · **REQUIRES PO DECISION**.
Full matrix: **Appendix A**.

| ID | Framework | Requirement | Class | Current CarbonTally Capability | 12-Section Mapping | Gap | Treatment |
|---|---|---|---|---|---|---|---|
| GP-1 | GHG Protocol | Org boundary + consolidation approach | Voluntary std (required by std) | `organizations`, `facilities` master data; **no consolidation model** | `organization` (partial) | **NOT CURRENTLY SUPPORTED** | Definitely required concept |
| GP-2 | GHG Protocol | Operational boundary (+ scope 3 activity list) | Std | `activity_categories.ghg_protocol_scope` (structural, **0 rows**) | none | **NOT CURRENTLY SUPPORTED** | Definitely required concept |
| GP-3 | GHG Protocol | Reporting period | Std | `period` section | `period` | **SUPPORTED** | Reuse |
| GP-4 | GHG Protocol | Total Scope 1+2 independent of GHG trades | Std | `totals.co2e_kg`; **no trades concept** | `totals` (partial) | **PARTIALLY SUPPORTED** | Likely (trades rarely used) |
| GP-5 | GHG Protocol | Emissions separately per scope | Std | `scopes` | `scopes` | **SUPPORTED** | Reuse |
| GP-6 | GHG Protocol | **Six GHGs separately** | Std | `gas_coverage` labels; factor gas coverage; **no per-gas totals** | none | **NOT CURRENTLY SUPPORTED** | Definitely required concept |
| GP-7 | GHG Protocol | **Base year** + recalculation policy + trend | Std | `benchmarking.baseline_value`/`delta` only | none | **NOT CURRENTLY SUPPORTED** | Definitely required concept |
| GP-8 | GHG Protocol | Exclusions description | Std | `validation` issues ≠ exclusions | none | **NOT CURRENTLY SUPPORTED** | Definitely required concept (narrative) |
| GP-9 | GHG Protocol | Biologically sequestered CO2 separately | Std | none | none | **NOT CURRENTLY SUPPORTED** | Likely |
| GP-10 | GHG Protocol | Offsets | Std | none | none | **NOT CURRENTLY SUPPORTED** | **REQUIRES PO DECISION** (product scope) |
| GP-11 | GHG Protocol | Methodologies used + tool reference | Std | `calculation.methodology`, `algorithm_version` | `calculation` | **PARTIALLY SUPPORTED** | Reuse + extend |
| GP-12 | GHG Protocol | Facility list | Std | `facilities` master data | none | **PARTIALLY SUPPORTED** | Likely |
| GP-13 | GHG Protocol | Inventory quality / uncertainty | Std | `validation` counts | none | **NOT CURRENTLY SUPPORTED** | LATER |
| GP-14 | GHG Protocol | Benchmarks (OPTIONAL) | Std (optional) | `benchmarking` | `benchmarking` | **SUPPORTED** | Reuse as management layer |
| GP-15 | GHG Protocol | Ratio indicators (OPTIONAL) | Std (optional) | none | none | **NOT CURRENTLY SUPPORTED** | Merge with SECR-2 |
| SECR-1 | UK SECR | GHG emissions (Scope 1+2) | **Legal** | `totals`, `scopes` | `totals`, `scopes` | **PARTIALLY SUPPORTED** (not labelled as SECR; no global/UK split) | Definitely required |
| SECR-2 | UK SECR | **≥1 intensity ratio** | **Legal** | none | none | **NOT CURRENTLY SUPPORTED** | **Definitely required concept** |
| SECR-3 | UK SECR | **Previous year's figures** (energy + GHG) | **Legal** | none in V3 engine (legacy PDF has YoY) | none | **NOT CURRENTLY SUPPORTED** | **Definitely required concept** |
| SECR-4 | UK SECR | **UK energy use (kWh)** / underlying global energy use | **Legal** | activity-level `quantity`+`unit` (kWh units exist) | none as a figure | **PARTIALLY SUPPORTED** | Definitely required concept |
| SECR-5 | UK SECR | Energy efficiency action taken | **Legal** | none | none | **NOT CURRENTLY SUPPORTED** | Narrative requirement |
| SECR-6 | UK SECR | Methodology used | **Legal** | `calculation` | `calculation` | **PARTIALLY SUPPORTED** | Reuse |
| SECR-7 | UK SECR | Applicability determination (which customers) | **Legal** | none | none | **NOT CURRENTLY SUPPORTED** | **REQUIRES PO DECISION** |
| ESRS-1 | EU CSRD/ESRS | E1-6 Gross Scopes 1, 2, 3 + total | **Legal (EU)** | `scopes`, `totals` (no Scope 3 completeness) | `scopes` | **PARTIALLY SUPPORTED** | **REQUIRES PO DECISION** (scope) |
| ESRS-2 | EU CSRD/ESRS | E1-5 Energy consumption and mix | **Legal (EU)** | activity-level energy data | none | **PARTIALLY SUPPORTED** | REQUIRES PO DECISION |
| ESRS-3 | EU CSRD/ESRS | GHG emissions intensity (paras 53-55) | **Legal (EU)** | none | none | **NOT CURRENTLY SUPPORTED** | Merge with SECR-2 |
| ESRS-4 | EU CSRD/ESRS | Full ESRS datapoint set | Legal (EU) | none | none | **NOT CURRENTLY SUPPORTED** | **NOT APPLICABLE / OUT OF INITIAL SCOPE** |
| IFRS-1 | IFRS S2 | Governance/strategy/risk-management disclosures | Standard (adoption-dependent) | none | none | **NOT CURRENTLY SUPPORTED** | **OUT OF INITIAL SCOPE** (management commentary) |
| IFRS-2 | IFRS S2 | Metrics & targets (incl. GHG) | Standard | `scopes`, `totals` | `scopes` | **PARTIALLY SUPPORTED** | REQUIRES PO DECISION |
| GRI-1 | GRI 305 | Emission disclosures | Voluntary | — | — | **Not established from authoritative source** | **OUT OF INITIAL SCOPE** |
| CT-1 | CarbonTally | Validation/evidence/lineage/generation sections | Product | `validation`, `provenance`, `lineage`, `generation` | 4 sections | **SUPPORTED** | Keep as evidence layer |
| CT-2 | CarbonTally | Benchmarking / management insight | Product | `benchmarking` | `benchmarking` | **SUPPORTED** | Keep as management layer |
| CT-3 | CarbonTally | Framework applicability per customer | Product | none | none | **NOT CURRENTLY SUPPORTED** | **REQUIRES PO DECISION** |

---

## 15. Disclosure Architecture Recommendation

**Recommendation: adopt a disclosure model layer.**
`DATA → DISCLOSURE MODEL → PRESENTATION` (not `DATA → FIXED 12-SECTION REPORT`).

### 15.1 Layer model

| Layer | Content | Exists today? | Recommendation |
|---|---|---|---|
| 1. Authoritative data | `emissions_logs`, `calculation_snapshots`, `emission_factors`, `activity_categories`, org/facility master data | **YES** | Reuse unchanged |
| 2. Calculation / provenance | CalculationEngine, snapshots, factor provenance, CO2/CO2e units, algorithm version | **YES** | Reuse unchanged |
| 3. Evidence | `audit_trail`, `domain_events`, validation results, lineage | **YES** | Reuse unchanged |
| 4. **Disclosure / requirement model** | Framework → version → requirement → CarbonTally data path; required vs optional | **NO** | **NEW (the core of this recommendation)** |
| 5. Narrative / content | Management commentary, methodology context, exclusions, energy-efficiency action, boundary description | **NO** | NEW (S4), requirement-bound |
| 6. Presentation / template | Ordered sections (today: the 12) | **YES (fixed)** | **Reclassify as template** |
| 7. Export / output | `GET /{id}/pdf`, `/{id}/download` | **YES** | Reuse |
| 8. Frozen / versioned artefact | `report_versions` + status lifecycle + immutability | **YES (S3)** | Reuse |

### 15.2 Why a disclosure model — and why not more

**It enables change without ledger redesign** because:
* a **new framework** is new mapping rows, not new carbon columns;
* a **changed requirement** is a new framework *version*, not a migration;
* the **carbon ledger, calculation engine and provenance are untouched** — the
  disclosure model *references* them.

**It is not a "generic framework engine".** This discovery deliberately does
**not** recommend a rules engine, expression language, or a marketplace of
templates. Authoritative evidence supports a **small, explicit mapping**:
~30 requirement rows across 3 frameworks (GHG Protocol, SECR, ESRS E1 subset).
A mapping table of that size is configuration *data*, not a platform.

**Recommended minimum shape (proposal only — no table created):**

```text
framework            (code, name, class: regulatory|voluntary|guidance, jurisdiction)
framework_version    (framework, version_label, effective_from, source_url, status)
requirement          (framework_version, requirement_id, description,
                      tier: required|optional|guidance,
                      data_kind: figure|narrative|both)
requirement_mapping  (requirement, data_path, transformation, unit, comparability)
report_purpose       (internal|secr_directors_report|esrs_e1_quantitative|management)
template             (purpose, ordered sections, narrative slots)
narrative_binding    (version, requirement|section, author, content) → version-bound
```

Where "data_path" is a **reference** into CarbonTally's existing structured
output (e.g. `scopes.{label}.co2e_kg`), **not** a duplicated store.

### 15.3 Extensibility rationale

| Change event | With disclosure model | With fixed 12-section report |
|---|---|---|
| New framework | Add framework + version + requirement rows | Redesign the engine and every consumer |
| Changed requirement | Add a version; keep historic versions | Schema/code change; historic reports unverifiable |
| New customer jurisdiction | Add applicability attribute + mapping | Redesign |
| New template | Add template row | New code path |

---

## 16. Future Change / Extensibility Model

**Minimum genuinely extensible architecture — and what to avoid.**

**Configuration/mapping over hard-coded schema (recommended):**
* framework, version, requirement, tier, mapping, purpose, template, narrative
  binding — all **data**, versioned.
* Applicability as **customer/entity attributes** (e.g. jurisdiction, size band),
  **not** a rules engine.

**Genuinely required in schema (not configuration):**
1. **Boundary + consolidation approach** — structural; cannot be an attribute
   string without losing integrity.
2. **Per-gas split** — structural (six gases, t and tCO2e).
3. **Base year + recalculation policy** — structural.
4. **Prior-period comparatives** — structural (a reporting-year relationship).
5. **Intensity ratio definition + denominator** — structural (numerator +
   denominator + unit).

**Premature abstractions (explicitly NOT recommended now):**
* Generic rule/expression engine for disclosure logic.
* Per-jurisdiction template marketplace.
* Full ESRS datapoint model (~1,000+ datapoints).
* XBRL/iXBRL digital tagging (only if a customer faces a tagging obligation —
  **not established**).
* AI-generated regulatory narrative.
* Multi-tenant custom disclosure definitions authored by customers.

---

## 17. Narrative Requirements Analysis

**No S4 design is provided here.** Determining *which* narrative is genuinely
required:

| # | Narrative need | Grounded in | Classification |
|---|---|---|---|
| N1 | **Organizational boundary + consolidation approach** description | GHG Protocol required | **Required narrative (system-composable)** |
| N2 | **Operational boundary** (+ scope 3 activity list) | GHG Protocol required | **Required narrative** |
| N3 | **Specific exclusions** of sources/facilities/operations | GHG Protocol required | **Required narrative** |
| N4 | **Base-year recalculation** context for significant changes | GHG Protocol required | **Required narrative** |
| N5 | **Causes of changes** not triggering recalculation | GHG Protocol required | **Required narrative** |
| N6 | **Inventory quality / uncertainty** statement | GHG Protocol required | **Required narrative (management)** |
| N7 | **Offsets** description + verification status | GHG Protocol required | **Requires PO decision (product scope)** |
| N8 | **Energy efficiency action taken** | **SECR legal requirement** | **Required narrative — management commentary** |
| N9 | **Methodology used** | SECR legal; GHG Protocol required | **Composable from `calculation` + narrative context** |
| N10 | **Biologically sequestered carbon** / sequestration statement | GHG Protocol required | Likely |
| N11 | **Contact person** | GHG Protocol required | Likely (trivial) |
| N12 | Management commentary / performance vs benchmarks | GHG Protocol **optional**; Phase 8 product | **Optional / product** |
| N13 | Reduction initiatives, targets, future plans | GHG Protocol optional; Phase 8 (net-zero) | **Optional / product** |
| N14 | Per-section customer caveats | No authoritative requirement | **Product decision** |

**Generated from structured data (not human-authored):** all figures — totals,
scopes, per-gas, activities, energy use, intensity ratio, comparatives,
benchmarks, provenance, validation, lineage, generation metadata.

**Management commentary required:** N6, N8, and (with N12/N13) performance
narrative.

**Methodology/assumption explanation:** N9 (composable + contextual).

**Contextual explanation of exclusions/estimates/boundaries/changes/limitations:**
N1, N2, N3, N4, N5, N10.

**Immutable system-generated vs customer-editable:** the current ratified rule
(§9.13, §15.3) already states that *all* engine output is system-controlled and
that narrative lives in a **separate namespace**. That rule is **compatible** with
this analysis. What the analysis adds is that **N1–N6, N9, N10 are framework
*disclosures*, not optional commentary** — so they cannot be treated as merely
"customer-editable narrative fields". Some are better generated from structured
data (N2 scope-3 list; N5 causes) and then optionally augmented.

**Version binding:** every narrative item must be **version-bound** to the report
version (already ratified §15.1), and additionally **framework-version-bound**
where it satisfies a disclosure (so that a re-mapped framework version is
auditable).

### 17.1 On the assumed allowlist and limits

* The **7-key allowlist** (§10.1 of the lifecycle spec) and any
  **character/field/total limits** were **CarbonTally product proposals**, not
  authoritative requirements.
* **No authoritative source located in this pass** prescribes narrative
  character limits for SECR, GHG Protocol, ESRS E1 or IFRS S2. Therefore:
  **"Not established from authoritative source."**
* Technical bounds (length caps, item counts) should be set as **technical
  safety limits** by the PO/engineering **after** the disclosure architecture is
  ratified — not derived from, or presented as, compliance requirements.

---

## 18. Evidence / Auditability Interaction

* GHG Protocol's **transparency** principle requires reporting "based on a clear
  audit trail" — CarbonTally's existing `provenance`, `lineage`, `calculation` and
  `audit_trail` surfaces are **directly supportive** and are a genuine strength.
* GHG Protocol lists **external assurance** information as **OPTIONAL**
  information — so assurance support is a *value-add*, not a requirement.
* **Phase 7 boundary preserved (unchanged):** CarbonTally provides traceable
  calculations, evidence references, factor provenance, calculation lineage,
  report version history, approval workflow and evidence/audit packages.
  CarbonTally must **not** be represented as an independent auditor, assurance
  provider, certification body or independent verifier.
* **Consequence for architecture:** the disclosure model must be able to carry an
  **evidence reference** per requirement (so a disclosure can be traced to
  snapshot/audit records), **without** implying assurance.

---

## 19. Versioning / Lifecycle Interaction

* The lifecycle is **already implemented and must not be modified**:
  `DRAFT → REVIEWED → APPROVED → FINAL`, with `CHANGES_REQUESTED` / `REJECTED`;
  approved/final versions immutable.
* **Needs to be version-bound** (proposal):
  1. **Disclosure mappings** — a report version must record *which*
     framework-version and requirement set it was produced against, otherwise a
     later framework change makes historic reports uninterpretable.
  2. **Narrative** — already version-bound by §15.1.
  3. **Evidence references** — bound to the version's snapshots.
  4. **Presentation template** — the version must record *which template*
     produced it (the engine already stamps `template_id` in `generation`).
* **Not** required: per-edit versions (ratified §14.2), and retro-active rewriting
  of approved versions.

---

## 20. Competitor / Market Comparison

**Used for product capability awareness only — NOT as evidence of regulatory
requirement.**

Publicly observable capability categories in established carbon-management
platforms (as *categories*, deliberately not as verified feature claims):

| Capability category | Relevance to CarbonTally |
|---|---|
| Multi-framework disclosure mapping (GHG Protocol / CSRD-ESRS / CDP / GRI / SECR) | Suggests the market expects **framework-selectable** output, supporting the disclosure-model recommendation (§15) |
| Report templates per framework/purpose | Supports templates-as-data (§15) |
| Narrative/commentary fields distinct from calculated figures | Supports the separation already ratified (§15.3) |
| Audit trail and evidence drill-down | CarbonTally already strong here (Phase 7) |
| Targets / reduction-plan tracking | Phase 8 net-zero capability; **not** a disclosure requirement |
| Data-quality scoring | ESG **E1**-adjacent; CarbonTally has validation, not a quality score |
| Exports (PDF/Excel/API) | CarbonTally has PDF/download routes |
| Assurance support packs | Optional under GHG Protocol; Phase 7 boundary applies |
| Jurisdiction/facility-level rollups | Matches GHG Protocol OPTIONAL subdivision |

> **Explicit caution:** competitor behaviour is **not** a compliance requirement.
> No competitor claim was used to justify any requirement in this document.

---

## 21. Capability Gaps

| # | Gap | Evidence | Severity for compliance |
|---|---|---|---|
| C1 | No **boundary/consolidation** model | GHG Protocol required; no such field anywhere | **High** |
| C2 | No **per-gas** breakdown | GHG Protocol required; only `gas_coverage` labels | **High** |
| C3 | No **base year / recalculation** model | GHG Protocol required | **High** |
| C4 | No **prior-year comparatives** | SECR legal | **High** |
| C5 | No **intensity ratio** | SECR legal; ESRS E1 | **High** |
| C6 | No **energy-use (kWh)** report figure | SECR legal | **High** |
| C7 | No **disclosure model** (required vs optional per framework) | §15 | **High (architectural)** |
| C8 | No **exclusions / offsets / sequestration** representation | GHG Protocol required | Medium |
| C9 | No **framework applicability** attribute per customer | SECR/CSRD scope | Medium (PO) |
| C10 | Existing mapping columns **empty** (0 rows) | `activity_categories` | Medium |
| C11 | **Live legacy route with unsubstantiated compliance claims** | §12.9 | **High (risk, not capability)** |
| C12 | Legacy `CSRD`/`ISSB` types are SECR placeholders | `report_generator.py:1058-1060` | **High (risk)** |
| C13 | Email template advertises SECR/CSRD/ISSB report generation | `utils/email.py:239` | Medium (risk) |
| C14 | Narrative layer absent | §17 | Medium (S4) |
| C15 | 12-section ids coupled to `report_comments.section_id` | lifecycle spec §16.1 | Medium (change cost) |

---

## 22. Architectural Risks

| # | Risk | Mitigation principle |
|---|---|---|
| R1 | **Compliance over-claim** (system asserting conformity it cannot evidence) | Never label output "compliant" unless requirement-level mapping + evidence exists; remove/reclassify legacy claims (separate authorization) |
| R2 | **Voluntary standard presented as legal requirement** | Enforce the class taxonomy (§5) in the disclosure model; `tier` and `class` are first-class fields |
| R3 | **Framework change invalidating historic reports** | Version-bound framework versions (§19) |
| R4 | **Narrative mutating system facts** | Already mitigated by ratified separate-namespace rule (§15.3) |
| R5 | **Premature generic-engine investment** | Explicitly reject the premature list (§16) |
| R6 | **Schema-per-framework creep** | Configuration/mapping for framework content; schema only for structural concepts (§16) |
| R7 | **Applying the wrong framework to a customer** | Applicability attributes + PO-ratified scope; never assume |
| R8 | **Unverified GRI/ISSB adoption driving scope** | GRI 305 = not established; IFRS S2 adoption = unverified; both excluded pending PO |

---

## 23. PO Decisions Required

### PO-1 — Initial framework/regulatory scope

* **Question:** Which frameworks are in scope for the initial disclosure model?
* **Options:** (a) GHG Protocol required set only; (b) GHG Protocol + **SECR**;
  (c) GHG Protocol + SECR + **ESRS E1 quantitative subset**; (d) add GRI/IFRS S2.
* **Evidence:** SECR is legal and applicable to large UK companies/LLPs (§8);
  ESRS E1 quantitative requirements exist and SEAI factors indicate Irish intent
  (§11); GRI 305 **not established** (§9); IFRS S2 adoption **unverified** (§10).
* **Recommended:** **(c)** — GHG Protocol required set + SECR + ESRS E1
  quantitative subset; GRI and IFRS S2 excluded.
* **Consequence:** determines the requirement catalogue size and the MUST scope.

### PO-2 — Canonical disclosure model vs fixed report-section model

* **Question:** Adopt `DATA → DISCLOSURE MODEL → PRESENTATION`?
* **Options:** (a) keep the fixed 12-section model as canonical; (b) adopt the
  disclosure model with the 12 sections as a template; (c) replace the 12
  sections.
* **Evidence:** no framework requires 12 sections; required disclosures are
  missing (§13.4); GHG Protocol itself separates required/optional (§7).
* **Recommended:** **(b)**.
* **Consequence:** new mapping/versioning concepts; S4 and future frameworks
  become additive.

### PO-3 — Role of the current 12-section annual report

* **Question:** What is the 12-section report's status?
* **Options:** (a) canonical compliance report; (b) **current presentation
  template**; (c) configurable template; (d) redesign.
* **Evidence:** §13.
* **Recommended:** **(b)**, with (c) as the target once the disclosure model exists.
* **Consequence:** preserves working, tested output; removes the implication that
  12 sections equal compliance.

### PO-4 — Future template/configuration strategy

* **Question:** Templates as data or code?
* **Options:** (a) code (status quo); (b) templates as configuration/template
  records per purpose; (c) generic template engine.
* **Evidence:** purpose differs by audience (§17 Class A–E); generic engines are
  premature (§16).
* **Recommended:** **(b)**, explicitly not (c).
* **Consequence:** new-template support without engine redesign.

### PO-5 — Narrative architecture boundary

* **Question:** Which narrative is framework **disclosure** vs optional
  commentary, and who owns each?
* **Options:** (a) current 7-key product allowlist; (b) requirement-bound
  narrative; (c) hybrid.
* **Evidence:** §17 — N1–N6, N9, N10 are framework disclosures; N12–N14 are
  product/optional.
* **Recommended:** **(c)** hybrid: requirement-bound disclosure narrative
  (system-composed where derivable, customer/management-authored where not) +
  a bounded optional commentary namespace.
* **Consequence:** defines S4's real scope; requires a disclosure model first.

### PO-6 — Which customer/entity/report purposes are initially supported

* **Question:** Which report purposes ship initially?
* **Options:** (a) `annual` only (status quo); (b) `annual` + management;
  (c) + SECR Directors'-Report-shaped purpose; (d) + ESRS E1 quantitative.
* **Evidence:** purposes map to different audiences and content (§17, §11).
* **Recommended:** **(b)** initially, with (c) next.
* **Consequence:** governs template and export work.

### PO-7 — Which Ireland/EU requirements belong in initial scope

* **Question:** Include ESRS E1 quantitative subset?
* **Options:** (a) exclude EU entirely; (b) **quantitative subset only**;
  (c) full ESRS.
* **Evidence:** ESRS E1-6/E1-5/intensity exist; CSRD applicability is date-phased
  and **unverified**; SEAI factors indicate Irish intent.
* **Recommended:** **(b)**; explicitly exclude full ESRS (C-ESRS-4).
* **Consequence:** keeps EU scope bounded and legally verifiable.

### PO-8 — Whether additional discovery is required before S4

* **Question:** Can S4 proceed?
* **Options:** (a) proceed on the current allowlist; (b) proceed after PO-1/PO-2/
  PO-5 are ratified; (c) new discovery first.
* **Evidence:** §24.
* **Recommended:** **(b)**.
* **Consequence:** S4 becomes requirement-grounded instead of product-invented.

### Additional decisions surfaced by evidence

| ID | Question | Why it needs the PO |
|---|---|---|
| **PO-9** | Disposition of the **live legacy compliance-claiming route** and the "Compliant with SECR/CSRD/ISSB" PDF text, and the email claim | Contradicts a ratified statement; a compliance-claim risk; **cannot be fixed in this task** |
| **PO-10** | Are **offsets**, **biologically sequestered carbon** and **facility lists** in product scope? | GHG Protocol required but product-scoping choice |
| **PO-11** | Do customers need **XBRL/iXBRL digital tagging**? | Not established; would materially change architecture |
| **PO-12** | Confirm the **IFRS S2 jurisdiction-adoption** position for target customers | Adoption unverified; determines whether IFRS S2 is in scope |
| **PO-13** | Confirm **CSRD/ESRS phased application dates** currently in force | Applicability **unverified** in this pass |

---

## 24. S4 Readiness Assessment

**Question:** Does this discovery now provide enough evidence to define narrative
purposes, ownership, placement, relationship to disclosures, and version binding?

| S4 prerequisite | Status after this discovery |
|---|---|
| **Narrative purposes** | **PARTIALLY PROVIDED** — §17 grounds N1–N10 in authoritative requirements; N12–N14 remain product choices |
| **Narrative ownership** | **NOT RESOLVED** — depends on PO-5; the lifecycle spec's P3/P4/§34-A1 consultant question is still open |
| **Narrative placement** | **RESOLVED (unchanged)** — separate `narrative_overlay` namespace on the version (§15.1 ratified) |
| **Relationship to disclosures** | **NOT RESOLVED** — requires PO-2 (disclosure model); without it, narrative cannot be bound to a requirement |
| **Version binding** | **RESOLVED (unchanged)** — version-bound (§19) |
| **Numeric limits** | **NOT ESTABLISHED authoritatively** — no framework source found; must be set as technical bounds after ratification (§17.1) |

**Assessment:** the discovery **removes the "arbitrary allowlist" problem**
(because it now supplies requirement-grounded narrative categories) but does
**not** by itself unblock S4, because the **disclosure model (PO-2)** and the
**narrative boundary (PO-5)** must be ratified first. S4 as currently specified —
a 7-key product allowlist — would still be **product-invented**, not
requirement-grounded.

**Recommendation:** ratify PO-1/PO-2/PO-3/PO-5, then re-scope S4 as
*"requirement-bound narrative overlay over the ratified disclosure model, plus a
bounded optional commentary namespace"*. **Do not implement S4 now.**

---

## 25. Recommended Next Phase

1. **PO ratification** of PO-1, PO-2, PO-3, PO-4, PO-5, PO-6, PO-7 (§23).
2. **Legal/regulatory confirmation** of PO-12 and PO-13 (IFRS S2 adoption; CSRD
   phased dates) — the two applicability uncertainties.
3. **Obtain GRI 305** authoritative content if GRI is to be considered at all
   (currently "not established").
4. **Decide PO-9** (legacy compliance-claim route disposition) as a **separate
   bounded task** — it is a risk, not part of the reporting architecture build.
5. **Then** author a bounded implementation contract for the **disclosure model
   (configuration + mapping + version binding)**, including a **required vs
   optional** tier and the **structural** concepts in §16.
6. **Then** re-scope and author **S4** against the ratified model.
7. **Only then** consider the 12-section template's evolution and any new
   purposes/templates.

---

## 26. Final Discovery Verdict

**DISCOVERY COMPLETE — PO DECISIONS REQUIRED BEFORE ARCHITECTURE RATIFICATION**

Rationale: the architectural direction is well-evidenced (framework requirements
and current capability are established with primary sources and implementation
evidence, and the recommended `DATA → DISCLOSURE MODEL → PRESENTATION` direction
is supported), but **ratification is blocked on PO decisions** (framework scope,
disclosure-model adoption, the 12-section's status, narrative boundary, EU scope)
and on **two unresolved applicability/evidence gaps** (GRI 305 not established;
IFRS S2 adoption and CSRD phased dates unverified).

---

## Appendix A — Detailed Requirement-to-Capability Matrix

See §14 for the primary matrix. Extended attributes per requirement are recorded
here in condensed form:

| Requirement | Required data | Required calculation | Required methodology/context | Required narrative | Required evidence/provenance | API/data-model support | Evidence/audit support |
|---|---|---|---|---|---|---|---|
| SECR-1 GHG emissions | activity data + factors | Scope 1+2 totals | methodology | no | factor provenance | `totals`/`scopes` | `calculation` |
| SECR-2 intensity ratio | numerator + denominator | ratio | denominator basis | no | provenance | **None** | **None** |
| SECR-3 prior year | prior-year activity + factors | comparable totals | consistency | no | prior version | **None** | version history |
| SECR-4 energy (kWh) | activity quantity/unit | unit normalisation to kWh | methodology | no | factor/unit provenance | activity-level only | lineage |
| SECR-5 energy efficiency action | — | — | — | **YES (management)** | — | **None** | **None** |
| SECR-6 methodology | — | — | **YES** | contextual | algorithm version | `calculation` | audit |
| GP-1/GP-2 boundaries | boundary/consolidation config | — | **YES** | **YES** | — | **None** | **None** |
| GP-5 per scope | emissions by scope | scope split | — | no | provenance | `scopes` | calculation |
| GP-6 six gases | per-gas factors | per-gas totals (t, tCO2e) | GWP basis | no | factor gas coverage | **None** | partial |
| GP-7 base year | base-year config | recalculation policy | **YES** | **YES** | version history | **None (baseline only)** | partial |
| GP-8 exclusions | — | — | — | **YES** | — | **None** | **None** |
| GP-10 offsets | offsets register | — | — | **YES** | verification status | **None** | **None** |
| GP-11/GP-14 benchmarks | benchmark inputs | benchmarking | — | optional | provenance | `benchmarking` | audit |
| ESRS-1 Scopes 1/2/3 | Scope 3 data completeness | gross totals | ESRS basis | no | provenance | partial | calculation |
| ESRS-3 intensity | as SECR-2 | as SECR-2 | ESRS basis | no | provenance | **None** | **None** |

## Appendix B — Source References

**Authoritative external sources (all retrieved and quoted in §5.2):**

1. UK Government — Environmental reporting guidelines: including Streamlined
   Energy and Carbon Reporting requirements (DESNZ/Defra):
   https://www.gov.uk/government/publications/environmental-reporting-guidelines-including-mandatory-greenhouse-gas-emissions-reporting-guidance
2. UK Government — SECR guidance PDF (March 2019):
   https://assets.publishing.service.gov.uk/media/67161e8696def6d27a4c9ab3/environmental-reporting-guidance-secr-march-2019.pdf
3. GHG Protocol — Corporate Standard (revised edition):
   https://ghgprotocol.org/sites/default/files/standards/ghg-protocol-revised.pdf
   (landing page: https://ghgprotocol.org/corporate-standard)
4. IFRS Foundation — IFRS S2 Climate-related Disclosures:
   https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/
5. EUR-Lex — Directive (EU) 2022/2464 (CSRD):
   https://eur-lex.europa.eu/eli/dir/2022/2464/oj
6. EUR-Lex — Commission Delegated Regulation (EU) 2023/2772 (ESRS):
   https://eur-lex.europa.eu/eli/reg_del/2023/2772/oj
7. GRI — **not retrieved** (HTTP 404 on the standard PDF; no GRI 305 content
   captured). Status: **Not established from authoritative source.**

**Repository evidence:** cited inline as `path:line` throughout §12, §13, §14.

## Appendix C — Search-Documentation Notes

* Browser/fetch used: `curl` with a standard user-agent; HTML converted to text
  by tag-stripping; PDFs extracted with `pdftotext -layout`.
* Two guessed gov.uk URLs returned 404 and were replaced with the working
  guidance page and its assets-hosted PDF.
* `legislation.gov.uk` returned HTTP 202 with an empty body for the 2018
  Regulations, so the **official gov.uk guidance PDF** was used instead; the
  statutory instrument number is recorded but the SI text itself was **not**
  independently machine-verified in this pass.
* Temporary working files were created under `/tmp` only; **none inside the
  repository**.

---

**END OF DISCOVERY REPORT**
