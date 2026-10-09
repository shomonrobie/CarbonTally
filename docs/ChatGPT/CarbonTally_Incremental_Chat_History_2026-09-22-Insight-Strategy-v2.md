# CarbonTally Incremental Chat History — Insight Strategy v2
## 2026-09-22

### Purpose

This file records the strategic Insight decision made after the INS-01 implementation authorization and before the next major Insight implementation package.

It supplements, and does not replace:

- `CarbonTally_Incremental_Chat_History_2026-09-22.md`
- `CarbonTally_Cline_Full_Insight_I7_I8_Workplan_2026-09-22.md`

The previous history remains authoritative for the earlier chronology.

---

# 1. Immediate preceding state

Cline completed the authorized INS-01 package:

**Insight Discovery + Aggregation + Provenance + Shared Source Evidence Viewer reuse + technical rate limiting**

Implementation:
- `e4ea3254c6a709df0e9cedcd8c719515363b4358`

Final/report commit:
- `cbc529dd8974d3ec16595fc5c6981c5217b43c24`

Permanent report:
`docs/architecture/CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-IMPLEMENTATION-20260922.md`

Cline explicitly stopped after implementation.

Current state:
- **IMPLEMENTED by Cline**
- **NOT independently verified**
- **NOT PO-closed**
- **OHD verification is the immediate next gate**

The OHD verification prompt has been prepared.

---

# 2. Important strategic question

The discussion asked whether all 426+ questions in:

`docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md`

must be implemented so CarbonTally Insight can answer every question.

Decision:

## NO — 426/426 is NOT the product completeness target.

The Question Library is a broad candidate-question catalogue.

It should not become 426 individual implementation tickets.

---

# 3. Strategic Insight decision

The product objective is now:

> **CarbonTally Insight should provide broad, governed coverage of important carbon-accounting capability families, with material customer-data answers grounded in authoritative CarbonTally calculations and traceable evidence.**

This is a refinement of the architecture, not a rejection of the previous architecture.

---

# 4. What remains unchanged

The core technical architecture remains:

**User question**
→ **bounded intent/query**
→ **strict typed validation**
→ **I2 authorization**
→ **I3 governed capability**
→ **authoritative CarbonTally data**
→ **deterministic computation**
→ **bounded provenance**
→ **Shared Source Evidence Viewer**
→ **LLM narration**

The key product principle remains:

> **Insight explains → CarbonTally proves → Source Evidence Viewer shows.**

The LLM is not the authoritative calculator, query engine, authorization mechanism, or evidence store.

---

# 5. Why 426 questions should not be treated as 426 features

Many questions represent different wording for the same capability.

Example:

- “What were our emissions in 2025?”
- “How much did we emit last year?”
- “Show our 2025 footprint.”

These can map to one temporal emissions capability.

Likewise:

- “Why did emissions increase?”
- “What caused the footprint to rise?”
- “Why are emissions higher this year?”

can map to a future variance/attribution capability.

Therefore the architecture should optimize for:

**capability families → representative questions → deterministic implementation**

not:

**individual questions → individual handlers**

---

# 6. New primary planning artifact

The future primary Insight coverage artifact should be a:

## Capability Coverage Matrix

For each Question Library question, track:

- Question ID;
- representative question;
- capability family;
- required deterministic data;
- required calculation;
- evidence requirement;
- answer state;
- current implementation status;
- OHD verification status;
- PO authorization status;
- dependencies;
- limitations.

This matrix should tell us what CarbonTally can actually answer.

---

# 7. Capability families

The current strategic model includes:

1. Identified Calculation
2. Discovery
3. Aggregation
4. Aggregate Provenance
5. Scope Analysis
6. Scope 3 Categories 1–15
7. Scope 2 Methodology
8. Scope 1 Decomposition
9. Supplier Intelligence
10. Facility / Asset Intelligence
11. Temporal Comparison
12. Variance / Attribution
13. Emission Factor Intelligence
14. Data Quality Intelligence
15. Methodology / Boundary Intelligence
16. Evidence / Audit Intelligence
17. General Carbon-Accounting Knowledge
18. Reporting / Disclosure Assistance
19. Decision / Reduction Intelligence

Not all are currently implemented.

---

# 8. Current strategic differentiator

The discussion considered whether broad Insight coverage could differentiate CarbonTally.

Decision:

## Potentially yes, but not because of question count.

The stronger potential differentiator is:

> **Natural-language access to a deeply structured carbon-accounting system where material answers are deterministic, explainable, reproducible, and traceable to the customer's underlying evidence.**

The desired experience is:

**Ask**
→ **Answer**
→ **Why?**
→ **Show calculation**
→ **Show evidence**

This makes the answer-to-evidence chain strategically important.

Do not claim that CarbonTally is uniquely capable of this without current competitive evidence.

---

# 9. Competitive/product lesson

Other carbon-accounting platforms are also developing AI assistants/analytics capabilities.

Therefore:

> “CarbonTally has an AI chatbot” is not sufficient differentiation.

Potential CarbonTally product strength should instead combine:

- broad carbon-accounting capability coverage;
- deterministic calculation;
- methodology/factor grounding;
- calculation provenance;
- source evidence;
- reproducibility;
- truthful uncertainty/no-data handling;
- secure tenant isolation.

Competitive claims must be verified separately before being used externally.

---

# 10. Question Library interpretation

The Question Library should be treated as:

### A. Discovery tool
Find important customer questions.

### B. Capability-gap detector
Identify missing deterministic engines.

### C. Acceptance-test source
Provide representative questions for each capability.

### D. Product-prioritization input
Help decide which capabilities matter.

It is NOT:

- a promise of current functionality;
- a list of 426 mandatory features;
- blanket implementation authorization.

---

# 11. Truthful answer states

Future Insight should distinguish:

- authoritative answer;
- explained answer;
- evidence-backed answer;
- partial answer;
- needs clarification;
- no data;
- unsupported;
- provider unavailable where applicable.

The system must not convert an unsupported or ambiguous question into a confident answer merely to increase apparent coverage.

---

# 12. Revised architecture file

A new architecture reference has been created:

`CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md`

It incorporates this strategic refinement while preserving the existing technical architecture and governance model.

The previous architecture reference is retained for chronology.

The v2 architecture is a **reference only**, not implementation authorization.

---

# 13. INS-01 current status remains unchanged

The strategic architecture revision does NOT change the current OHD gate.

Current state:

**Cline IMPLEMENTED**
→ **OHD VERIFICATION NEXT**
→ **PO CLOSURE AFTER OHD**

Do not begin the next major Insight implementation package before this gate is completed.

---

# 14. Future Insight implementation strategy

After INS-01 verification/closure, the future implementation order should be driven by capability dependencies and customer value.

Broad roadmap:

1. INS-01 verification/closure.
2. Capability Coverage Matrix.
3. Supplier persistence.
4. Scope 3 Categories 1–15.
5. Primary/secondary factor provenance.
6. Scope 1 decomposition.
7. Scope 2 location + market.
8. Aggregate→evidence hardening.
9. Temporal comparison.
10. Variance/attribution.
11. Historical factor metadata.
12. Data-quality intelligence.
13. Methodology/boundary intelligence.
14. Broader Insight exposure.
15. Governed general carbon-accounting knowledge.
16. Reporting/disclosure assistance.
17. Decision/reduction intelligence.
18. Consultant/auditor personas if separately authorized.
19. I7.
20. I8.
21. Controlled production deployment.

Each item requires its own bounded PO authorization.

---

# 15. I7 and I8 remain unchanged

### I7

Still:

**NOT AUTHORIZED / NOT READY**

Requires separate policy decisions around:
- retention;
- deletion;
- legal hold;
- export;
- privacy/provider implications;
- acceptance criteria.

### I8

Full I8 remains:

**NOT AUTHORIZED**

I8-A technical areas remain a future production-readiness track.

The technical rate-limiting control is already included in INS-01 and awaits OHD verification.

I8-B commercial billing remains:

**NOT AUTHORIZED**

No subscription/entitlement/usage/billing implementation is authorized by this architecture revision.

---

# 16. Governance rule

The revised architecture does not authorize implementation.

The governing sequence remains:

**PO decision**
→ **Cline preflight**
→ **PO bounded implementation authorization**
→ **Cline implementation**
→ **OHD independent verification**
→ **PO closure**
→ **next package**

No roadmap, architecture document, or Question Library entry creates implementation authorization by itself.

---

# 17. Resume instructions if context is lost

If this conversation is lost:

1. Read this file.
2. Read the previous incremental history.
3. Read the v2 architecture reference.
4. Read the Cline full Insight/I7/I8 workplan.
5. Inspect current Git HEAD/status.
6. Read the latest Cline/OHD permanent reports.
7. Verify whether INS-01 is actually OHD-verified and PO-closed.
8. Do not assume closure.
9. Build/maintain the Capability Coverage Matrix before planning large-scale future Insight implementation.
10. Treat v2 architecture as the current product/architecture direction but not implementation authorization.

---

# 18. Final strategic decision

The current CarbonTally Insight objective is:

> **Not “answer 426 questions.”**

It is:

> **Build a governed carbon-intelligence capability layer that can answer a broad range of important carbon-accounting questions in natural language, using authoritative deterministic CarbonTally data, with clear explanations and traceable evidence.**

The Question Library measures the breadth of questions we want to support.

The Capability Coverage Matrix measures the underlying capabilities required to support them.

The answer-to-evidence chain is a strategic product principle.

This is the current Insight direction as of 2026-09-22.
