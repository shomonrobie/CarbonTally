# CarbonTally Phase 8 Reporting Architecture
## PO Ratification & Decision Record — D1–D17

**Document:** `CARBONTALLY_PHASE8_REPORTING_ARCHITECTURE_PO_RATIFICATION_D1-D17_20260912.md`  
**Status:** PO-RATIFIED  
**Date:** 2026-09-12  
**Scope:** CarbonTally Phase 8 reporting architecture  
**Purpose:** Consolidated record of Product Owner (PO) decisions D1–D17 approved before implementation of the compliance-driven reporting/disclosure architecture.

---

## 1. Executive Summary

CarbonTally reporting shall evolve from a fixed report-section model into a **compliance-driven, disclosure-centric architecture**.

The approved architectural chain is:

```text
AUTHORITATIVE SOURCES
        |
        v
FRAMEWORK + VERSION
        |
        v
REQUIREMENTS / DISCLOSURES
        |
        v
DISCLOSURE MODEL
        |
   +----+---------+---------+
   |              |         |
   v              v         v
CARBON DATA     EVIDENCE  NARRATIVE
   |              |         |
   +--------------+---------+
                  |
                  v
           REPORT PURPOSE
                  |
                  v
           TEMPLATE VERSION
                  |
                  v
             PRESENTATION
                  |
                  v
               EXPORT
                  |
                  v
          FINAL / FROZEN ARTEFACT
```

The four initial report purposes are:

1. **Annual Carbon Report**
2. **Management Report**
3. **UK SECR Report**
4. **ESRS E1 Quantitative Report**

The **GHG Protocol Corporate Standard** is the primary underlying corporate GHG accounting foundation.

The reporting architecture must be changeable when frameworks or requirements change, without corrupting historical reports or duplicating the calculation engine.

**No implementation work is authorized by this document alone.** The next authorized step is a **regulatory requirement verification/discovery task**, followed by PO review and then implementation authorization.

---

# 2. Architectural Principles

## 2.1 One authoritative carbon calculation foundation

CarbonTally must not create separate carbon calculation engines for different reports.

```text
                 AUTHORITATIVE SCOPE 1
                         |
              +----------+----------+
              |          |          |
              v          v          v
           Annual     SECR       ESRS E1
```

The same principle applies to Scope 2, Scope 3, energy, factors, provenance and evidence.

## 2.2 Disclosure model sits between data and presentation

```text
DATA
  |
  v
CALCULATION / PROVENANCE
  |
  v
EVIDENCE
  |
  v
DISCLOSURE MODEL
  |
  v
PRESENTATION / TEMPLATE
```

A report template must not become the canonical definition of a regulatory requirement.

## 2.3 Report purpose is distinct from framework

```text
GHG Protocol-backed carbon data
          |
          +--> Annual Carbon Report
          +--> Management Report
          +--> UK SECR Report
          +--> ESRS E1 Quantitative Report
```

## 2.4 Regulatory requirements are versioned

A regulatory change must create a controlled new version rather than silently rewriting historical requirements.

```text
SECR Version A
      |
      +--> historical reports

SECR Version B
      |
      +--> new applicable reports
```

## 2.5 Historical reports are reproducible

A finalized report must remain historically reproducible and retain or resolve immutably to the relevant:

- reporting period;
- organization/entity context;
- report purpose;
- framework/version;
- disclosure/requirement version;
- calculation/data context;
- factor/provenance context;
- evidence;
- narrative;
- template version;
- final artefact/integrity information.

## 2.6 Compliance claims are controlled

CarbonTally may support and map disclosures without automatically claiming:

- legal compliance;
- certification;
- independent assurance;
- independent GHG verification.

Phase 7's assurance boundary remains unchanged:

> CarbonTally provides evidence-backed reporting and assurance-support; it is not an independent assurance provider.

---

# 3. Ratified PO Decision Register

## D1 — Initial Reporting Framework Scope

**Status: APPROVED**

CarbonTally's initial compliance architecture shall support:

1. **GHG Protocol Corporate Standard** — primary carbon-accounting/reporting foundation.
2. **UK SECR** — initial jurisdiction-specific statutory reporting use case.
3. **ESRS E1 quantitative subset** — bounded Ireland/EU expansion.

**Deferred:** GRI 305 and IFRS S2 until separately justified and approved.

**Boundary:** This does not constitute compliance certification or assurance.

## D2 — Core Reporting Architecture

**Status: APPROVED**

CarbonTally shall adopt:

> **AUTHORITATIVE DATA → DISCLOSURE MODEL → PRESENTATION/TEMPLATE → EXPORT → FROZEN VERSIONED ARTEFACT**

The Disclosure Model is the canonical reporting layer.

The existing V3 12-section report is not the canonical compliance architecture.

## D3 — Current 12-Section Report Status

**Status: APPROVED**

The existing V3 12-section Annual Report remains the current presentation template for continuity and regression safety.

It is explicitly not:

- a regulatory standard;
- the canonical disclosure model;
- the permanent CarbonTally report structure;
- evidence that CarbonTally supports twelve regulatory sections.

It may be evolved or superseded after the disclosure architecture is established.

## D4 — Template Architecture & Configurability

**Status: APPROVED**

CarbonTally shall use controlled, versioned, configuration-driven framework/requirement mappings and report templates.

It shall **not** initially build a generic unrestricted rules/template engine.

Configurable concepts may include:

- framework;
- framework version;
- requirement/disclosure;
- applicability;
- requirement-to-data mapping;
- report purpose;
- template version;
- presentation ordering;
- disclosure placement;
- narrative binding.

Application-controlled concepts include:

- calculation methodology;
- authoritative carbon facts;
- evidence/provenance;
- authorization;
- disclosure semantics;
- lifecycle;
- approval/finalization;
- audit trail;
- security boundaries.

## D5 — Narrative Architecture

**Status: APPROVED**

CarbonTally shall use a hybrid narrative model:

### A. Requirement-bound disclosure narrative

Where a disclosure requires narrative:

- use structured facts where reliable;
- use authorized customer input where CarbonTally cannot derive the required information.

### B. Bounded optional management commentary

Provide a separate namespace for optional human-authored commentary that is not itself a regulatory disclosure.

Narrative is not the compliance architecture.

The previously proposed arbitrary **7 fields × 4,000 characters** model is explicitly rejected as an assumed regulatory requirement.

Initial customer-authored narrative editing is bounded to **Customer Owner and Customer Admin** unless separately approved.

## D6-R — Initial Report Purposes

**Status: APPROVED**

The initial reporting architecture supports:

1. **Annual Carbon Report**
2. **Management Report**
3. **UK SECR Report**
4. **ESRS E1 Quantitative Report**

All four share the same authoritative data, calculation/provenance, evidence and disclosure foundation.

They must not become four independent report engines.

## D7-R — ESRS E1 Initial Scope

**Status: APPROVED**

CarbonTally's initial ESRS E1 capability shall provide:

### Layer 1 — Production-grade carbon and energy disclosures

Including, as applicable and supported:

- Scope 1;
- Scope 2 location-based;
- Scope 2 market-based;
- Scope 3;
- significant Scope 3 categories;
- total GHG emissions;
- relevant GHG intensity metrics;
- energy consumption;
- relevant energy mix;
- comparative information;
- methodology, inputs and provenance.

### Layer 2 — Structured support for related climate disclosures

Including, where within CarbonTally's domain:

- GHG reduction targets;
- base year/baseline;
- progress against targets;
- decarbonisation actions;
- expected emissions reductions from actions;
- energy-efficiency actions;
- renewable-energy actions;
- transition-plan carbon elements;
- policies/actions where customer information is required.

### Layer 3 — Explicit external-input/future boundaries

CarbonTally shall not pretend to calculate areas such as:

- scenario analysis;
- physical/transition risk assessment;
- anticipated financial effects;
- climate-related financial opportunities;

unless separately implemented and approved.

The product shall not claim full ESRS E1/CSRD compliance merely because this capability exists.

Exact initial E1 disclosure coverage must be established from the applicable authoritative/current ESRS source before implementation.

## D8 — GHG Protocol Accounting Foundation

**Status: APPROVED**

The GHG Protocol Corporate Standard is the primary underlying corporate GHG accounting foundation.

CarbonTally's authoritative emissions calculations, scope classification, organizational/operational boundaries, methodology, provenance and evidence model shall support applicable GHG Protocol Corporate Standard requirements.

Regulatory frameworks map to that foundation rather than independently redefining carbon calculations.

GHG Protocol alignment does not automatically satisfy SECR or ESRS E1.

## D9 — Initial GHG Protocol Required Content

**Status: APPROVED**

The canonical model shall support applicable required corporate GHG report information, including:

1. organizational boundaries;
2. consolidation approach;
3. entities/facilities included;
4. operational boundaries;
5. included activities/scopes;
6. reporting period;
7. Scope 1 emissions;
8. Scope 2 emissions;
9. emissions by scope;
10. individual greenhouse gases and CO2e where supported;
11. base year where applicable;
12. base-year recalculation information where applicable;
13. biologically sequestered CO2 where applicable;
14. methodologies/calculation approaches;
15. exclusions and reasons;
16. significant changes and causes;
17. historical/comparative information where applicable;
18. inventory quality/uncertainty information;
19. sequestration information where applicable;
20. facilities/organizational coverage information;
21. responsible/contact information.

Requirements must be capable of being classified as:

- required;
- conditional;
- optional;
- not applicable;
- unavailable;
- customer-input-required;
- not supported/future.

D9 approves functional/reporting requirements, not a premature database schema.

## D10 — UK SECR Reporting Requirements

**Status: APPROVED**

The initial SECR capability shall support applicable requirements concerning:

- energy consumption in kWh;
- relevant UK energy sources;
- relevant transport energy;
- Scope 1 emissions;
- Scope 2 emissions;
- associated relevant SECR energy/emissions activity coverage;
- CO2e reporting;
- reporting period;
- prior-year comparative information;
- at least one appropriate GHG intensity ratio;
- methodology and calculation/provenance;
- energy-efficiency action narrative;
- applicability determination.

Exact current statutory applicability rules must be verified from authoritative sources before implementation.

SECR is not applicable to every CarbonTally customer.

## D11 — SECR Intensity Ratio Policy

**Status: APPROVED**

CarbonTally shall use a controlled intensity-ratio model rather than one universal denominator.

The model shall support:

- controlled denominator types;
- customer selection/configuration from supported types;
- explicit numerator;
- explicit denominator;
- denominator unit;
- ratio;
- methodology;
- evidence/source;
- prior-year comparability where applicable.

CarbonTally may recommend an appropriate ratio, but the customer remains responsible for confirming the selected denominator where judgment is required.

The exact denominator catalogue and statutory treatment must be verified before implementation.

## D12 — GHG Protocol Required vs Optional Content

**Status: APPROVED**

CarbonTally shall distinguish:

### Required
Initial canonical reporting model.

### Conditional
Applicability-driven requirements.

### Optional
Optional capability/management reporting.

### Future/unsupported
Requirements needing capabilities CarbonTally does not yet possess.

Optional GHG Protocol information shall not automatically become mandatory CarbonTally report content.

The disclosure model therefore requires richer applicability semantics than a simple required/not-required boolean.

## D13 — ESRS E1 Applicability Model

**Status: APPROVED**

ESRS E1 reporting shall be applicability-aware.

CarbonTally shall distinguish:

1. whether it can produce a disclosure;
2. whether the disclosure legally applies to the customer;
3. whether the customer voluntarily wants to produce the output.

Before generating a statutory-positioned ESRS E1 report, the relevant reporting context/applicability should be captured or determined.

If CarbonTally cannot determine applicability authoritatively, it shall identify the need for customer/professional confirmation rather than making a legal determination.

Voluntary use of the underlying E1 reporting capability should not necessarily be blocked by non-applicability.

## D14 — Regulatory Versioning & Change Management

**Status: APPROVED**

Frameworks, framework versions, requirements and mappings shall be explicitly versioned.

A regulatory change creates a controlled new version rather than silently changing historical meaning.

```text
Regulatory change
      |
      v
New framework/requirement version
      |
      v
New mappings/templates where required
      |
      v
Applicable future reporting
```

Historical reports remain tied to their original versions.

## D15 — Historical Report Reproducibility & Framework Binding

**Status: APPROVED**

Every finalized report shall be bound to the applicable reporting context and versions used to produce it.

Finalized reports must remain reproducible even after later changes to:

- regulations;
- disclosure mappings;
- templates;
- calculations;
- factors;
- product architecture.

The objective is historical reproducibility, not unnecessary duplication of all data.

## D16 — Legacy Compliance Route Disposition

**Status: APPROVED**

The legacy enhanced-report route is formally classified as:

> **Legacy / deprecated reporting path pending formal disposition.**

It is not part of the authoritative initial reporting architecture.

No legacy compliance claim should remain exposed without separate authorization and supporting evidence.

A separate bounded disposition task must establish whether the route should be:

1. removed/decommissioned;
2. disabled/deprecated;
3. temporarily retained behind an explicitly non-authoritative/internal boundary; or
4. migrated/replaced.

**No deletion, disabling, rewrite, migration or API change is authorized by D16 itself.**

## D17 — Regulatory Source & Change Governance

**Status: APPROVED**

CarbonTally shall use an authoritative-source-first process.

### Source hierarchy

**Tier 1 — Primary authoritative sources**

- legislation/regulations;
- official government publications;
- official regulator publications;
- official standards-setting body publications;
- official framework publications.

**Tier 2 — Official implementation guidance**

- regulator guidance;
- official technical guidance;
- official implementation FAQs/clarifications;
- recognized official implementation materials.

**Tier 3 — Secondary sources**

- professional advisory publications;
- industry guidance;
- specialist commentary;
- academic/research material.

Tier 3 may assist interpretation but cannot independently establish the authoritative CarbonTally requirement.

AI may assist discovery and analysis, but AI output is not itself the regulatory authority.

---

# 4. Master Architecture Flowcharts

## 4.1 End-to-End Reporting Architecture

```text
                    AUTHORITATIVE SOURCES
                            |
                            v
                   FRAMEWORK + VERSION
                            |
                            v
                   REQUIREMENT MODEL
                            |
                            v
                    DISCLOSURE MODEL
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
      CARBON DATA        EVIDENCE          NARRATIVE
          |                 |                 |
          +-----------------+-----------------+
                            |
                            v
                     REPORT PURPOSE
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
       ANNUAL          MANAGEMENT          SECR
          |                 |                 |
          +-----------------+-----------------+
                            |
                            v
                    ESRS E1 QUANTITATIVE
                            |
                            v
                     TEMPLATE VERSION
                            |
                            v
                       PRESENTATION
                            |
                            v
                          EXPORT
                            |
                            v
                  FINAL / FROZEN ARTEFACT
```

## 4.2 Framework-to-Disclosure Flow

```text
Framework
   |
   v
Framework Version
   |
   v
Requirement / Disclosure
   |
   +--> Applicability
   |
   +--> Required / Conditional / Optional
   |
   +--> Required Data
   |
   +--> Evidence
   |
   +--> Narrative
   |
   v
Requirement Mapping
   |
   v
Report Purpose
   |
   v
Template Version
```

## 4.3 One Calculation, Multiple Reports

```text
              AUTHORITATIVE CARBON CALCULATION
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
       Annual        UK SECR        ESRS E1
          |              |              |
          +--------------+--------------+
                         |
                         v
                   Shared evidence
                   + provenance
```

Management reporting also consumes the same foundation, with management-specific presentation and insight content.

## 4.4 Narrative Architecture

```text
                  DISCLOSURE REQUIREMENT
                           |
              +------------+------------+
              |                         |
              v                         v
       Structured facts          Narrative needed
              |                         |
              v               +---------+---------+
       System-derived          |                   |
                              v                   v
                       Customer-authored     System-composed
                              |                   |
                              +---------+---------+
                                        |
                                        v
                              Version-bound narrative
                                        |
                                        v
                                  Presentation
```

## 4.5 Regulatory Change Lifecycle

```text
Regulatory change identified
             |
             v
Authoritative source verified
             |
             v
Framework/version identified
             |
             v
Requirement extracted
             |
             v
Applicability assessed
             |
             v
CarbonTally impact assessed
             |
             v
Disclosure mapping designed
             |
             v
PO / product approval
             |
             v
Versioned configuration released
             |
             v
Regression + evidence verification
             |
             v
Applicable future reports
```

## 4.6 Report Lifecycle Relationship

```text
GENERATE
   |
   v
DRAFT
   |
   v
REVIEWED
   |
   +------> CHANGES_REQUESTED
   |                |
   |                v
   |              DRAFT
   |
   +------> REJECTED
   |             |
   |             v
   |           NEW DRAFT
   |
   v
APPROVED
   |
   v
FINAL
   |
   v
FROZEN
```

A finalized/frozen report remains bound to its historical reporting context.

---

# 5. Decision Matrix

| ID | Decision | Approved Outcome | Implementation? |
|---|---|---|---|
| D1 | Initial frameworks | GHG Protocol + SECR + ESRS E1 quantitative scope | No |
| D2 | Core architecture | Data → Disclosure Model → Presentation | No |
| D3 | 12-section report | Current presentation template only | No |
| D4 | Configurability | Versioned/config-driven, no generic rules engine | No |
| D5 | Narrative | Requirement-bound + bounded optional commentary | No |
| D6-R | Initial purposes | Annual + Management + SECR + ESRS E1 | No |
| D7-R | ESRS scope | Carbon/energy + related structured support + explicit boundaries | No |
| D8 | Accounting foundation | GHG Protocol Corporate Standard | No |
| D9 | GHG required content | Applicable required corporate-report content | No |
| D10 | SECR content | Energy + emissions + intensity + methodology + actions + comparatives | No |
| D11 | SECR intensity | Controlled structured ratio model | No |
| D12 | Requirement semantics | Required/conditional/optional/future etc. | No |
| D13 | E1 applicability | Applicability-aware; voluntary use possible | No |
| D14 | Versioning | Explicit framework/requirement/template versioning | No |
| D15 | Reproducibility | Historical version/context binding | No |
| D16 | Legacy route | Legacy/deprecated pending bounded disposition | No |
| D17 | Regulatory governance | Authoritative-source-first | No |

**Important:** All seventeen decisions are PO ratifications. They do not by themselves authorize code, schema, API, frontend, RLS, production, or migration changes.

---

# 6. Implementation Guardrails

1. Do not make the 12-section report canonical.
2. Do not create separate calculation engines for different report purposes.
3. Do not duplicate authoritative carbon facts merely because they appear in different disclosures.
4. Do not build a generic unrestricted rules engine at this stage.
5. Do not build a generic template marketplace or tenant-defined regulatory platform.
6. Do not treat arbitrary narrative character limits as regulatory requirements.
7. Do not use narrative fields as a substitute for structured disclosure modelling.
8. Do not infer legal applicability solely from the ability to calculate a disclosure.
9. Do not silently modify historical framework requirements.
10. Do not silently alter finalized reports when frameworks, templates, factors or calculations change.
11. Do not use AI interpretation as the authoritative regulatory source.
12. Do not claim full ESRS/CSRD compliance merely from ESRS E1 support.
13. Do not claim independent GHG assurance, verification or certification.
14. Do not allow the legacy compliance route to become an ungoverned competing reporting path.
15. Do not implement RLS remediation as part of this reporting architecture decision record.
16. Do not modify completed Phase 8 S1/S3 lifecycle work merely to accommodate this architecture.
17. Do not implement S4 Narrative Overlay until the disclosure requirements and narrative bindings have been verified.

---

# 7. Relationship to Existing Phase 8 Work

## 7.1 S1

Phase 8 Reporting S1 is complete and independently verified.

Preserve the existing correctness work around:

- `is_current`;
- `current_version`;
- report-version queries;
- documentation;
- regression tests.

## 7.2 S3

Phase 8 Reporting S3 is complete and independently verified.

Preserve the existing lifecycle:

- DRAFT;
- REVIEWED;
- CHANGES_REQUESTED;
- REJECTED;
- APPROVED;
- FINAL.

Preserve version-scoped lifecycle API and audit behaviour.

## 7.3 S4

S4 Narrative Overlay is currently **blocked pending disclosure architecture and exact requirement/narrative mapping**.

No arbitrary field allowlist or numeric character limits are ratified by this document.

S4 must be re-scoped after the regulatory requirement matrix is reviewed.

---

# 8. Implementation Gates

## Gate 1 — Regulatory Evidence

Complete authoritative verification of:

- GHG Protocol Corporate Standard;
- UK SECR;
- current applicable ESRS E1 source/version;
- relevant Ireland/EU context;
- applicable current amendments/adoption information.

## Gate 2 — Requirement Matrix

Produce a requirement-by-requirement matrix containing at least:

```text
Framework
Framework version
Requirement ID
Requirement
Mandatory / Conditional / Optional
Applicability
Required data
Required evidence
Narrative requirement
Existing CarbonTally capability
Gap
Initial-support decision
Authoritative source
```

## Gate 3 — PO Review

PO reviews and ratifies:

- exact initial requirement coverage;
- exact ESRS E1 disclosure coverage;
- exact SECR intensity denominator catalogue;
- applicability rules/handling;
- structural data-model gaps;
- narrative bindings;
- any remaining regulatory scope decisions.

## Gate 4 — Architecture Design

Design the disclosure model and structural concepts.

Potential conceptual areas include:

- framework;
- framework version;
- requirement;
- requirement mapping;
- report purpose;
- template;
- narrative binding;
- applicability.

This is not an authorization to create these tables yet.

## Gate 5 — Implementation Authorization

Only after Gates 1–4 are complete should an implementation prompt be issued.

The implementation prompt must:

- reference this ratification document;
- state exact scope;
- state explicit exclusions;
- preserve S1/S3;
- require tests;
- require independent verification where applicable;
- require a mandatory written report;
- prohibit unauthorized commit/push/reset/stash behaviour.

---

# 9. Mandatory OHD/Cline Reporting Rule

For every future prompt sent to **OHD or Cline**:

> **A written report is a mandatory deliverable.**

The report must state:

- task reference;
- objective;
- scope;
- files inspected/changed;
- implementation details;
- tests run and results;
- database/migration status where relevant;
- security/authorization implications;
- deviations;
- unresolved issues;
- final verdict;
- git/worktree status;
- commit/push status where relevant.

No implementation task should be considered complete without the mandatory report.

---

# 10. Next-Step Boundary

## Next authorized task

The next task is **regulatory requirement verification/discovery only**.

It should produce the authoritative requirement matrix for:

### GHG Protocol

Verify exact required, conditional and optional corporate reporting information.

### UK SECR

Verify:

- current applicability;
- statutory requirements;
- energy requirements;
- emissions requirements;
- intensity-ratio rules;
- prior-year requirements;
- energy-efficiency action narrative;
- current official guidance/version.

### ESRS E1

Verify:

- current authoritative version;
- applicable amendments/simplifications;
- exact disclosure requirements;
- quantitative and qualitative requirements;
- CarbonTally-substantiable data;
- customer/external-input requirements;
- current EU/Ireland applicability context.

## Explicitly prohibited in the next task

The regulatory verification task must **not**:

- modify code;
- modify database schema;
- create migrations;
- modify APIs;
- modify frontend;
- implement S4;
- modify the calculation engine;
- modify report generation;
- modify RLS;
- modify production;
- delete/disable the legacy reporting route;
- implement XBRL/iXBRL;
- create a generic rules engine;
- make legal determinations;
- silently ratify new PO decisions.

---

# 11. Required Next Discovery Deliverables

### Deliverable A — Authoritative Regulatory Requirement Matrix

A detailed requirement-by-requirement matrix with source references.

### Deliverable B — CarbonTally Capability Mapping

For every requirement:

```text
SUPPORTED
PARTIALLY SUPPORTED
STRUCTURED INPUT REQUIRED
EXTERNAL INPUT REQUIRED
MISSING CAPABILITY
FUTURE
NOT APPLICABLE
```

### Deliverable C — Structural Gap Analysis

Identify which additional structured concepts CarbonTally genuinely needs.

Do not jump directly to database tables.

### Deliverable D — Reporting Architecture Impact

Map the requirements to:

- Annual Carbon Report;
- Management Report;
- UK SECR Report;
- ESRS E1 Quantitative Report.

### Deliverable E — S4 Impact

Identify exactly which narrative bindings S4 should eventually support.

Do not implement S4.

### Deliverable F — PO Decision List

Identify only decisions that genuinely remain unresolved after authoritative verification.

### Deliverable G — Mandatory Task Report

A written report documenting the complete discovery task and final verdict.

---

# 12. Final Ratification Statement

D1–D17 collectively establish the current PO-approved reporting direction:

> **CarbonTally shall evolve into an evidence-backed, compliance-aware carbon reporting and intelligence platform whose authoritative carbon accounting foundation feeds a versioned disclosure model, which in turn supports multiple controlled report purposes and presentation templates.**

The initial reporting purposes are:

> **Annual Carbon Report + Management Report + UK SECR Report + ESRS E1 Quantitative Report**

The underlying accounting foundation is:

> **GHG Protocol Corporate Standard**

The architectural model is:

> **AUTHORITATIVE DATA → DISCLOSURE MODEL → PRESENTATION/TEMPLATE → EXPORT → FROZEN VERSION**

The system must remain:

- evidence-backed;
- versioned;
- historically reproducible;
- applicability-aware;
- configurable without becoming a generic rules engine;
- explicit about customer/external inputs;
- conservative about regulatory claims;
- separate from independent assurance/certification.

**D1–D17 are PO-approved.**

**No implementation is authorized until the authoritative regulatory requirement verification and PO review gates above are completed.**
