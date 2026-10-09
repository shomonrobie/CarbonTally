# CarbonTally — PO Insight Capability Decision Matrix
## Decision checkpoint — 2026-09-22

**Role:** Product Owner decision record  
**Scope:** CarbonTally Insight + supporting carbon-accounting capabilities  
**Status:** PO decisions made; implementation authorization remains bounded and separate.

## 1. Decision principles

1. **Authoritative data → deterministic computation → evidence/provenance → LLM narration.**
2. The LLM never invents carbon figures, performs uncontrolled database queries, bypasses authorization, or substitutes for deterministic accounting logic.
3. Tenant isolation and least privilege are mandatory.
4. Every customer-specific answer must be reproducible from authoritative stored data and/or an explicitly versioned deterministic derivation.
5. Aggregate answers require a defined provenance path; an aggregate without component trace must not be described as fully audit-ready.
6. Accounting taxonomy/methodology decisions precede query/API work where the underlying dimension does not exist.
7. Standards are versioned because GHG Protocol and ISO work are evolving.
8. Cline implements only explicit bounded authorizations; OHD independently verifies; PO closes.

## 2. PO decision matrix

| ID | Capability | Current verified state | PO decision | Required before implementation | Implementation status |
|---|---|---|---|---|---|
| C-01 | Scope totals | Backend exists | APPROVE bounded Insight exposure | tool contract, filters, limits, evidence semantics | NOT IMPLEMENTED |
| C-02 | Scope-filtered aggregation | Missing | APPROVE | deterministic filter contract + tests | NOT IMPLEMENTED |
| C-03 | Scope 3 Categories 1–15 | Missing first-class dimension | APPROVE GHG Protocol baseline taxonomy | versioned taxonomy + mapping/storage + historical semantics | NOT IMPLEMENTED |
| C-04 | Month/year/asset/facility aggregation | Backend exists | APPROVE bounded Insight exposure | allowlisted contract + provenance | NOT IMPLEMENTED |
| C-05 | Activity aggregation | Backend exists, activity_type based | APPROVE with explicit limitation | governed meaning of activity_type + result bounds | NOT IMPLEMENTED |
| C-06 | Supplier persistence | Upstream mapping exists; emission write path omits supplier_id | APPROVE | confidence/approval rule + backfill policy + lineage decision | NOT IMPLEMENTED |
| C-07 | Supplier aggregation | Structural code exists; key may be unpopulated | CONDITIONAL APPROVAL | C-06 verified + scope/category filters + provenance | NOT IMPLEMENTED |
| C-08 | Supplier variance | Missing | APPROVE after C-06/C-07 | period definition + matching basis | NOT IMPLEMENTED |
| C-09 | Factor explanation | Backend exists; Insight only partial | APPROVE bounded expansion | historical metadata contract + minimization | NOT IMPLEMENTED |
| C-10 | Factor-change attribution | Missing | APPROVE in principle | deterministic comparison definition | NOT IMPLEMENTED |
| C-11 | Period variance/attribution | Comparison foundation exists; attribution missing | APPROVE in principle | attribution methodology + restatement rules | NOT IMPLEMENTED |
| C-12 | Evidence/quality selection | Per-record/org-level signals exist | APPROVE bounded capability | selection/sampling semantics + DM-6 | NOT IMPLEMENTED |
| C-13 | Primary/secondary classification | Missing | APPROVE | explicit data-quality/provenance taxonomy | NOT IMPLEMENTED |
| C-14 | Discovery | No Insight discovery contract | APPROVE bounded discovery | zero/one/multiple state, tolerance, timezone, parameter extraction | NOT IMPLEMENTED |
| C-15 | Scope 2 dual reporting | Market-based calculation absent | APPROVE as product target | method dimension + instruments/factor hierarchy + versioning | NOT IMPLEMENTED |
| C-16 | Scope 1 decomposition | Missing | APPROVE | stationary/mobile/fugitive/process taxonomy + mapping | NOT IMPLEMENTED |
| C-17 | Assumptions/restatements | Missing | DEFER until accounting governance package | assumption/adjustment/restatement model | NOT IMPLEMENTED |
| C-18 | Aggregate→evidence | Missing | APPROVE | bounded component IDs + DM-6/evidence policy | NOT IMPLEMENTED |
| C-19 | Concept answers | No governed knowledge source | APPROVE FUTURE | knowledge-source governance + citations/versioning | NOT IMPLEMENTED |
| SEC-01 | Rate limiting | Middleware inactive | REQUIRED before scaling analytics | I8 thresholds + acceptance criteria | NOT AUTHORIZED |
| P-01 | Consultant Insight | Backend consultant APIs exist | DEFERRED | separate persona/scope decision | NOT AUTHORIZED |
| P-02 | Auditor direct Insight | Auditor denied | DEFERRED | separate access/legal/security decision | NOT AUTHORIZED |
| P-03 | I7 retention/deletion/export | Not ready | DEFERRED | retention/legal/export package | NOT AUTHORIZED |
| P-04 | Full I8 commercial | Not ready | DEFERRED | pricing/usage/billing/SLO/DR package | NOT AUTHORIZED |
| P-05 | Production deployment | Separate control | NOT AUTHORIZED | release readiness + explicit deployment approval | NOT AUTHORIZED |

## 3. PO decisions in detail

### 3.1 Discovery — APPROVED IN PRINCIPLE

Supported matching dimensions:
- date/date range
- amount/CO2e with explicit tolerance
- activity
- supplier
- facility/asset
- scope
- reporting period

Required response states:
- no match
- one match
- multiple matches
- invalid input
- authorization failure
- provider/internal failure where relevant

Rules:
- no arbitrary query;
- no SQL/model-generated query;
- no cross-tenant search;
- bounded result count;
- date/timezone semantics explicitly documented;
- amount tolerance explicitly documented.

### 3.2 Aggregation — APPROVED IN PRINCIPLE

Initial allowed dimensions:
- scope
- month
- year
- activity
- asset
- facility

Future dimensions require separate authorization.

Required controls:
- organization authorization;
- fixed dimension/filter allowlist;
- bounded period;
- bounded result count;
- deterministic units;
- explicit accounting basis;
- provenance classification;
- no raw source text to the LLM;
- aggregate→evidence contract before claiming full auditability.

### 3.3 Scope 3 — APPROVED

Use GHG Protocol Categories 1–15 as the baseline product taxonomy.

Do not silently infer categories from free text. Each mapping must have:
- taxonomy version;
- mapping source/rule;
- confidence/status where applicable;
- historical behavior defined.

### 3.4 Supplier — APPROVED CONDITIONALLY

Supplier identity is already captured upstream, but it is not persisted into the emission write path.

Decision:
- propagate governed supplier identity into authoritative calculation lineage;
- define confidence/approval semantics;
- define backfill policy;
- verify historical data before enabling supplier analytics.

### 3.5 Primary vs secondary — APPROVED

Create a dedicated provenance concept. It must not be inferred from:
- customer_factor vs catalogue factor;
- spend_based methodology alone;
- extraction confidence alone.

The definition must be compatible with carbon-accounting reporting expectations and auditable.

### 3.6 Scope 2 — APPROVED

CarbonTally product target is dual reporting:
- location-based;
- market-based.

The design must support contractual instruments and applicable factor hierarchy/quality information, with methodology versioning. The current disclosure `scope2_method_hint` must not be treated as a calculation engine.

### 3.7 Scope 1 — APPROVED

Introduce a governed decomposition for:
- stationary combustion;
- mobile combustion;
- fugitive emissions;
- process emissions.

Where a category is not applicable or cannot be determined, the system must say so rather than infer it.

### 3.8 Variance — APPROVED IN PRINCIPLE

The deterministic engine must distinguish:
- activity/quantity movement;
- factor movement;
- methodology movement;
- boundary movement;
- data availability/restatement effects.

If the stored evidence cannot establish causation, the answer must explicitly report that limitation.

### 3.9 Aggregate → evidence — APPROVED

Any future aggregate answer intended for audit/assurance use must be able to identify its contributing calculation records within the authorized tenant and, where permitted, resolve them to source evidence.

### 3.10 Factor history — APPROVED

Retain enough factor metadata at calculation time to explain the exact factor basis used historically. Candidate alternatives may only be discussed if their history was actually retained.

### 3.11 Concept answers — APPROVED FUTURE

A governed carbon-accounting knowledge layer may answer standards/concept questions. It must:
- cite/version its source;
- distinguish standards knowledge from customer-specific data;
- never fabricate customer facts;
- never alter deterministic calculations.

## 4. Dependency order

1. **Discovery contract + ambiguity/tolerance/timezone decisions**
2. **Aggregation contract + scope/filter semantics**
3. **Supplier persistence decision implementation**
4. **Scope 3 taxonomy/data model**
5. **Primary/secondary provenance model**
6. **Scope 1 decomposition**
7. **Scope 2 dual-reporting accounting model**
8. **Aggregate→evidence contract**
9. **Variance/attribution**
10. **Factor historical metadata**
11. **Insight exposure of the approved deterministic capabilities**
12. **Concept-answer knowledge layer**
13. **Rate limiting/I8 readiness**
14. Consultant/auditor surfaces only after separate PO decisions
15. Production deployment only after separate release authorization

This is dependency order, not a business-value ranking.

## 5. Evidence and security requirements

Every implementation package must preserve:
- tenant/org isolation;
- server-side authorization;
- least privilege;
- fixed query dimensions;
- parameterized SQL;
- no model-generated SQL;
- bounded result sizes;
- no signed URLs in LLM prompts;
- DM-6 evidence gating;
- append-only audit events;
- explicit error states;
- data minimization;
- prompt-injection resistance;
- reproducibility where claimed.

The pre-existing factor usage endpoint's organization-wide usage counts/timestamps must not become a template for new analytical endpoints and should be separately tracked for remediation.

## 6. Industry/reference basis

- GHG Protocol Corporate Standard / Scope 3 Standard are the primary corporate inventory reference framework.
- GHG Protocol Scope 2 Guidance defines location- and market-based methods and contractual-instrument quality requirements.
- ISO 14064-1:2018 specifies organization-level GHG quantification/reporting principles and requirements.
- GHG Protocol and ISO are currently working toward harmonized corporate standards, reinforcing methodology/versioning requirements.
- Current commercial carbon platforms emphasize traceable calculations, emission-factor transparency, dimensions, permissions, audit history and controlled AI assistance.

## 7. Explicit PO boundary

This matrix **does not itself authorize implementation**.

For each row marked APPROVE/REQUIRED, the next artifact must be a bounded Cline implementation authorization identifying:
- exact scope;
- files/areas permitted;
- prohibited changes;
- tests;
- permanent report;
- commit/push requirement;
- stop conditions;
- OHD verification requirement.

No Cline task may interpret "APPROVE" as permission to implement all dependent capabilities at once.

## 8. Current PO verdict

**Question Library forensic analysis: CLOSED.**

**PO capability decisions: DECIDED.**

**Implementation program: NOT YET STARTED from these new decisions.**

**Next controlled action:** prepare the first bounded implementation authorization package for the dependency foundation.
