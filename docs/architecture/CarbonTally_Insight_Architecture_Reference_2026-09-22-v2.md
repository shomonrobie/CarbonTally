# CarbonTally Insight Architecture Reference — v2
## Capability-Family, Answer-to-Evidence Architecture
### 2026-09-22

> **STATUS: ARCHITECTURE / PRODUCT REFERENCE**
>
> This document is a design and planning reference. It is **not blanket implementation authorization**.
> Every future implementation package requires a separate bounded PO authorization, Cline implementation, independent OHD verification, and PO closure.

---

# 1. Purpose

This v2 reference refines the CarbonTally Insight architecture based on the 2026-09-22 product discussion.

The previous architecture correctly established the technical principle:

**Question → bounded intent/query → authorization → deterministic CarbonTally data → deterministic computation → provenance → evidence → LLM narration**

That principle remains unchanged.

The strategic refinement is:

> **CarbonTally Insight should not be measured by whether it implements a fixed number of individual questions. It should provide broad, governed coverage of important carbon-accounting capability families, with material customer-data answers grounded in authoritative CarbonTally calculations and traceable evidence.**

The existing Question Library remains valuable, but it is a **coverage and acceptance catalogue**, not a list of 426 independent features.

---

# 2. Product Objective

## 2.1 The target is capability coverage, not question count

The Question Library contains hundreds of candidate questions.

Many questions are different natural-language expressions of the same underlying capability.

For example:

- “What were our emissions in 2025?”
- “How much did we emit last year?”
- “Show our 2025 footprint.”

may all map to one temporal/period emissions capability.

Similarly:

- “Why did emissions increase?”
- “What caused our footprint to rise?”
- “Why are emissions higher this year?”

may eventually map to one variance/attribution capability.

Therefore:

> **Do not build one handler per question.**

Build governed deterministic capabilities that can support many questions.

---

# 3. Question Library Role

`CarbonTally_Insight_Question_Library_2026-09-22.md` remains the canonical candidate-question catalogue.

Its purpose is to:

- discover important user needs;
- identify missing capability families;
- create representative acceptance tests;
- expose gaps in data/calculation/evidence architecture;
- support product prioritization.

It is **not** a promise that every question is currently answerable.

Each question should eventually be classified as one of:

- IMPLEMENTED;
- PARTIALLY IMPLEMENTED;
- NEEDS CLARIFICATION;
- NO DATA;
- UNSUPPORTED;
- NOT YET IMPLEMENTED;
- PROVIDER UNAVAILABLE;
- NOT AUTHORIZED.

Insight must never fabricate an answer merely to increase apparent coverage.

---

# 4. Core Product Principle

CarbonTally Insight should follow:

**User question**
→ **bounded intent/query planning**
→ **strict typed validation**
→ **I2 authorization**
→ **I3 governed read-only capability**
→ **authoritative CarbonTally data**
→ **deterministic computation**
→ **bounded provenance**
→ **Shared Source Evidence Viewer**
→ **LLM explanation/narration**

The LLM is an explanation/interface layer.

It is not the authoritative data or calculation layer.

---

# 5. Answer-to-Evidence Principle

A strategic CarbonTally product principle is:

> **Insight explains → CarbonTally proves → Source Evidence Viewer shows.**

For material customer-data answers, the preferred chain is:

**Question**
→ **Answer**
→ **Calculation**
→ **Underlying contributing records**
→ **Source evidence**

The user should be able to move from a meaningful answer to the supporting CarbonTally calculation and, where authorized, the original source evidence.

This is a core platform capability rather than an Insight-only feature.

---

# 6. Competitive Product Objective

CarbonTally should not position Insight simply as:

> “An AI chatbot for carbon accounting.”

Natural-language carbon assistants and analytics agents are becoming an established market pattern.

The stronger product objective is:

> **Natural-language access to a deeply structured carbon-accounting system where material answers are deterministic, explainable, reproducible, and traceable to the customer's underlying evidence.**

Potential differentiating characteristics include:

1. broad carbon-accounting question coverage;
2. deterministic authoritative calculations;
3. explicit methodology/factor grounding;
4. calculation provenance;
5. source evidence navigation;
6. reproducibility;
7. truthful uncertainty/no-data/clarification behavior;
8. tenant-safe architecture;
9. audit-oriented traceability.

No individual characteristic should be treated as an exclusive market claim without separate competitive verification.

---

# 7. Capability-Family Model

Future Insight planning should organize capabilities into families rather than individual questions.

## Family A — Identified Calculation

Examples:
- explain a specific calculation;
- show activity/quantity/unit;
- show CO₂e;
- show scope/date;
- show methodology;
- show factor;
- show source evidence.

Status:
**Foundation implemented / verified status depends on existing I2-I6 closure.**

---

## Family B — Discovery

Examples:
- find emissions by date;
- find by amount;
- find by activity;
- find by scope;
- find by supplier;
- find by facility;
- find by asset;
- find by reporting period.

Current status:
**Implemented in INS-01; OHD verification required.**

---

## Family C — Aggregation

Examples:
- emissions by scope;
- by month;
- by year;
- by activity;
- by supplier;
- by facility;
- by asset.

Current status:
**Implemented in INS-01; OHD verification required.**

---

## Family D — Aggregate Provenance

Examples:
- which calculations make up this number?
- which records support this total?
- show contributing calculations;
- navigate from aggregate to evidence.

Current status:
**Foundation implemented in INS-01; OHD verification required.**

---

## Family E — Scope Analysis

Future expansion may include:
- Scope 1;
- Scope 2;
- Scope 3;
- scope comparisons;
- scope contribution.

Current status:
**Partially supported through current foundation; broader scope analytics remain future work.**

---

## Family F — Scope 3 Category Analysis

Target:
- GHG Protocol Scope 3 Categories 1–15;
- versioned taxonomy;
- deterministic category assignment;
- category-level reporting and analysis.

Status:
**Future / not yet authorized.**

---

## Family G — Scope 2 Methodology

Target:
- location-based;
- market-based;
- methodology;
- instruments/contractual mechanisms;
- residual mix;
- factor hierarchy;
- versioning.

Status:
**Future / not yet authorized.**

---

## Family H — Scope 1 Decomposition

Target where applicable:
- stationary;
- mobile;
- fugitive;
- process.

Status:
**Future / not yet authorized.**

---

## Family I — Supplier Intelligence

Target:
- authoritative supplier identity;
- supplier emissions;
- supplier comparisons;
- supplier contribution;
- supplier changes.

Current status:
**Supplier discovery/aggregation foundation exists, but application supplier persistence remains a limitation.**

Future supplier persistence requires separate authorization.

---

## Family J — Facility / Asset Intelligence

Target:
- facility contribution;
- asset contribution;
- comparisons;
- changes;
- evidence.

Current status:
**Foundation exists through deterministic lineage; broader analytics remain future work.**

---

## Family K — Temporal Comparison

Target:
- month-over-month;
- year-over-year;
- reporting-period comparison;
- absolute change;
- percentage change.

Status:
**Future bounded analytics capability beyond current aggregation foundation.**

---

## Family L — Variance / Attribution

Target:
Explain changes through deterministic dimensions such as:

- activity;
- emission factor;
- methodology;
- boundary;
- data availability;
- restatement.

Status:
**Future / not yet authorized.**

No unsupported causal narrative should be generated.

---

## Family M — Emission Factor Intelligence

Target:
- factor used;
- factor source;
- factor version;
- methodology;
- geography;
- unit;
- historical factor state;
- factor selection explanation.

Status:
**Partially supported; historical factor metadata remains future work.**

---

## Family N — Data Quality Intelligence

Potential questions:
- missing data;
- anomalous values;
- incomplete evidence;
- unmapped records;
- uncertain classifications;
- data completeness.

Status:
**Future capability family.**

---

## Family O — Methodology / Boundary Intelligence

Potential questions:
- organizational boundary;
- operational boundary;
- methodology;
- accounting treatment;
- reporting-year methodology.

Status:
**Future capability family with explicit governance requirements.**

---

## Family P — Evidence / Audit Intelligence

Potential questions:
- what supports this number?
- which source document?
- which calculation?
- which factor?
- can this number be reproduced?
- what changed?

Status:
**Core strategic capability; foundation exists and should continue to expand.**

---

## Family Q — General Carbon-Accounting Knowledge

Potential questions:
- what is Scope 2 market-based?
- what is Scope 3 Category 1?
- what is primary vs secondary data?
- what does a methodology mean?

Status:
**Future governed Mode E capability.**

Customer-specific data must remain separate from general knowledge.

---

## Family R — Reporting / Disclosure Assistance

Potential future capabilities:
- report preparation;
- disclosure support;
- framework questions;
- evidence package preparation.

Status:
**Future / separately governed.**

---

## Family S — Decision / Reduction Intelligence

Potential future capabilities:
- largest reduction opportunities;
- major contributors;
- supplier priorities;
- operational drivers;
- scenario analysis.

Status:
**Future / requires deterministic analytical foundations and separate authorization.**

---

# 8. Capability Coverage Matrix

The long-term control artifact should be a matrix with at least:

| Field | Purpose |
|---|---|
| Question ID | Stable reference to Question Library |
| Representative question | Human-readable example |
| Capability family | Underlying capability |
| Required deterministic data | Authoritative source |
| Required calculation | Deterministic engine |
| Evidence requirement | Provenance/evidence depth |
| Answer state | success/no_data/clarification/etc. |
| Current implementation status | Actual code state |
| Verification status | OHD state |
| Authorization status | PO state |
| Dependencies | Required preceding capabilities |
| Notes/limitations | Truthful product limitation |

This matrix should become the primary mechanism for tracking Insight coverage.

---

# 9. Do Not Optimize for 426/426

The product objective is explicitly **not**:

> “CarbonTally must answer all 426 questions.”

Instead:

> **CarbonTally should support the important carbon-accounting capability families represented by the Question Library, with representative questions used for acceptance and regression testing.**

The 426-question count should therefore not be used as a product completeness metric.

A more meaningful metric is:

- capability-family coverage;
- representative-question coverage;
- deterministic answer coverage;
- evidence coverage;
- verified coverage;
- truthful unsupported/no-data handling.

---

# 10. Answer Quality Model

For customer-data questions, Insight should distinguish:

### Authoritative answer
The deterministic CarbonTally engine produced the result.

### Explained answer
The LLM narrates an authoritative result.

### Evidence-backed answer
The answer has a valid provenance path to supporting calculations/evidence.

### Partial answer
Only a bounded subset is available.

### Clarification
The question lacks a determinable required parameter.

### No data
The requested data is not present.

### Unsupported
The capability does not yet exist.

### Provider unavailable
Only applicable where an external provider is actually required.

Insight must never convert these into a misleading generic success response.

---

# 11. Evidence Depth

Future capability packages should define evidence depth.

Suggested conceptual levels:

### E0 — General knowledge
No customer evidence.

### E1 — Customer aggregate
Customer data result, but no calculation-level drill-down.

### E2 — Calculation provenance
Aggregate or answer maps to contributing calculation snapshots.

### E3 — Source evidence
Calculation maps to source line/item/document through the Shared Source Evidence Viewer.

### E4 — Audit package
Potential future governed package containing complete reproducibility and supporting records.

Do not claim E4 merely because E3 exists.

---

# 12. Natural-Language Architecture

Natural language is an interface, not an unrestricted query language.

Preferred flow:

**Natural language**
→ **bounded intent recognition**
→ **typed schema**
→ **server validation**
→ **authorization**
→ **deterministic execution**

A planner may be deterministic or use a separately governed model for extraction in the future, but:

- it must output only a closed schema;
- it must not generate SQL;
- it must not authorize access;
- it must not select a tenant;
- it must not calculate authoritative emissions;
- it must not choose among ambiguous authoritative records.

---

# 13. Security Architecture

Every future Insight capability must preserve:

- tenant isolation;
- authenticated authorization;
- I2 authorization;
- I3 allowlists;
- I4 persistence allowlists;
- I5 bounded context;
- I6 creator-private conversation semantics;
- signed URL controls;
- DM-6;
- audit controls;
- prompt-injection resistance;
- bounded result sizes;
- rate limiting;
- provider isolation.

New capability work must not create arbitrary database query surfaces.

---

# 14. Rate Limiting

Technical rate limiting is part of the current Insight foundation.

Current authorized security defaults:

- user: 20 requests/minute, burst 5, max concurrent 2;
- organization: 100 requests/minute, burst 20, max concurrent 10.

These are security controls, not commercial entitlements.

Commercial usage/billing remains a separate I8-B decision.

---

# 15. Shared Source Evidence Viewer

The Shared Source Evidence Viewer is a core CarbonTally platform capability.

Insight must reuse it.

Preferred user paths:

1. Report → calculation → evidence.
2. Emissions/calculation → evidence.
3. Insight → explanation → calculation → evidence.

A future Evidence Center may exist, but it must reuse the same evidence destination.

Do not create an Insight-only evidence viewer.

---

# 16. Strategic Differentiation Principle

The potential CarbonTally differentiation is not the raw number of questions.

A stronger product proposition is:

> **Ask CarbonTally about your emissions in plain English, receive an answer grounded in your actual calculations, understand why the answer is what it is, and trace the material answer back to its underlying evidence.**

The architecture should therefore prioritize:

1. correctness;
2. deterministic computation;
3. traceability;
4. reproducibility;
5. evidence;
6. broad capability coverage;
7. natural-language usability.

---

# 17. Competitive Claims

Do not make unsupported claims such as:

- “CarbonTally answers every carbon question.”
- “No competitor can do this.”
- “CarbonTally is the only auditable AI carbon assistant.”

Competitive positioning requires current external research.

The architecture may identify **potential differentiation**, but market exclusivity must not be asserted without evidence.

---

# 18. Full Insight Roadmap

Recommended dependency order:

1. INS-01 Discovery/Aggregation/Provenance/Rate Limiting.
2. OHD verification.
3. PO closure.
4. Capability Coverage Matrix.
5. Supplier persistence.
6. Scope 3 Categories 1–15.
7. Primary/secondary factor provenance.
8. Scope 1 decomposition.
9. Scope 2 location + market.
10. Aggregate → evidence hardening.
11. Temporal comparison.
12. Variance/attribution.
13. Historical factor metadata.
14. Data-quality intelligence.
15. Methodology/boundary intelligence.
16. Broader Insight exposure.
17. Governed Mode E knowledge.
18. Reporting/disclosure assistance.
19. Decision/reduction intelligence.
20. Consultant/auditor personas only after separate authorization.
21. I7.
22. I8.
23. Controlled production deployment.

This is a roadmap, not automatic authorization.

---

# 19. Governance

For every capability:

**PO decision**
→ **bounded Cline preflight**
→ **PO implementation authorization**
→ **Cline implementation**
→ **independent OHD verification**
→ **PO closure**
→ **next capability**

No roadmap item becomes authorized merely because it appears in this document.

---

# 20. Current Status at v2 creation

As of 2026-09-22:

- I1 — CLOSED / implemented baseline.
- I2 — CLOSED / VERIFIED PASS.
- I3 — CLOSED / VERIFIED PASS before current analytics expansion.
- I4 — CLOSED / VERIFIED PASS before current analytics expansion.
- I5 — CLOSED / VERIFIED PASS.
- I6 — CLOSED / VERIFIED PASS.
- INS-01 — IMPLEMENTED by Cline; OHD verification pending.
- Shared Source Evidence Viewer — core capability; existing implementation/verification history applies.
- I7 — NOT AUTHORIZED / NOT READY.
- I8 — full stage NOT AUTHORIZED.
- I8-A rate limiting technical control — included in INS-01, pending OHD verification.
- I8-B commercial/billing — NOT AUTHORIZED.
- Production deployment — NOT AUTHORIZED.

---

# 21. Final Architecture Principle

CarbonTally Insight should ultimately become:

> **A governed natural-language intelligence layer over CarbonTally's authoritative carbon-accounting system — capable of answering broad carbon-accounting questions through deterministic capabilities, explaining the results clearly, and tracing material answers back to calculations and source evidence.**

The goal is not maximum question count.

The goal is **maximum trustworthy capability coverage**.
