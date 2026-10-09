# CarbonTally Insight — Deterministic Emissions Discovery & Evidence Architecture Reference

**Document status:** Reference / design baseline for Cline  
**Date:** 2026-09-22  
**Scope:** CarbonTally Insight customer-facing natural-language analysis, deterministic emissions discovery, calculation explanation, and evidence handoff  
**Governance:** This document is a technical reference and does not by itself authorize implementation, schema changes, new I3 tools, production deployment, or changes to previously closed Phase 8 decisions.

---

## 1. Purpose

CarbonTally Insight should let a customer ask questions about their own carbon-accounting results in ordinary language and receive a clear, traceable answer.

Examples:

- “Why was my CO2e 20 kg on 1 February 2024?”
- “How was this emission calculated?”
- “Which activity caused this result?”
- “Which emission factor was used?”
- “Why did February emissions increase?”
- “What contributed most to my emissions?”
- “Show me the source for this calculation.”
- “Which invoice or spreadsheet line produced this number?”
- “Where in the original document did this value come from?”
- “What is the difference between Scope 1 and Scope 2?”

The architectural principle is:

> **The LLM interprets and explains. Deterministic CarbonTally services discover, calculate, authorize, and prove.**

The LLM must never become the system of record for carbon values, calculation provenance, authorization, customer isolation, or evidence references.

---

## 2. Current CarbonTally governance constraints

These constraints are important and must not be silently changed:

1. I2 is closed and governs authorized customer data access.
2. I3 is closed with four ratified read-only tools:
   - `report_lookup`
   - `report_version_lookup`
   - `report_evidence_lookup`
   - `calculation_snapshot_lookup`
3. Adding or widening an I3 tool requires an explicit PO decision; it must not be introduced implicitly during implementation.
4. I4 audit ledger is closed.
5. I5 bounded current-conversation context is closed.
6. I6 customer Insight UI is closed.
7. I7 is not authorized.
8. Full I8 is not authorized; only previously authorized I8-A principles are in scope.
9. Production deployment is a separate controlled decision.
10. The external synthetic-document generator repository is external/offline/pinned and must not be modified or vendored.
11. Every implementation must be independently verified by OHD before PO closure.
12. Cline must stop and report a governance/contract gap rather than inventing authorization.

**Important:** This document describes the desired architecture and acceptance criteria. It does not supersede a later or more specific PO authorization.

---

## 3. Industry-aligned architecture principles

The design should follow established patterns used by modern carbon-accounting and sustainability platforms, while keeping CarbonTally's governance stronger than a generic chatbot architecture.

### 3.1 Ground answers in authoritative company data

Customer-specific answers should be generated from CarbonTally's persisted calculation/activity/evidence records, not from generic LLM knowledge.

### 3.2 Separate interpretation from computation

The LLM may:

- understand natural-language questions;
- classify intent;
- identify requested dimensions;
- ask clarification questions;
- summarize deterministic results;
- explain methodology in plain English.

The LLM must not:

- invent a CO2e number;
- independently recalculate a historical result;
- choose an emission factor;
- infer missing provenance;
- fabricate an invoice, page, row, source file, or evidence reference;
- bypass authorization;
- query arbitrary database tables.

### 3.3 Deterministic retrieval before generation

The preferred pipeline is:

`Customer question`
→ `intent/parameter extraction`
→ `authorization`
→ `deterministic discovery`
→ `candidate validation`
→ `authoritative snapshot/evidence retrieval`
→ `LLM explanation`
→ `customer response`
→ `optional evidence navigation`

### 3.4 Tenant isolation is mandatory

Every customer-specific operation must be organization-scoped and must fail closed.

No prompt, model response, cached result, retrieval operation, or evidence URL may cross organization boundaries.

### 3.5 Provenance is a first-class capability

Where CarbonTally can establish provenance, the answer should expose it or provide a direct path to the evidence.

Typical lineage:

`source document`
→ `extracted item`
→ `mapped data`
→ `calculation snapshot`
→ `emissions result`
→ `report/version`

### 3.6 Explain uncertainty honestly

Possible deterministic outcomes should be explicit:

- exactly one match;
- multiple matches;
- no match;
- insufficient information;
- unauthorized;
- provider unavailable;
- invalid input;
- system error.

Never silently select one of several materially different candidates.

---

## 4. Target customer experience

### 4.1 Example: “Why was my CO2e 20 kg on 1 February 2024?”

Target flow:

1. User asks the question.
2. Insight determines that the user is asking for a historical emissions result by date/amount.
3. Structured parameters are extracted:
   - date = 2024-02-01
   - amount ≈ 20 kg CO2e
4. The backend performs deterministic, organization-scoped discovery.
5. Candidate records are returned.
6. If exactly one authoritative candidate exists, retrieve the calculation snapshot and relevant provenance.
7. The LLM converts the verified record into plain English.
8. The answer explains:
   - what activity produced the result;
   - quantity and unit;
   - emission factor;
   - factor source/version where stored;
   - calculation result;
   - scope/category where stored;
   - relevant date/reporting year;
   - provenance references.
9. If the customer asks “show me the source,” the system follows the existing evidence path to the Source Evidence Viewer.

### 4.2 Multiple matches

If several records match:

> “I found 3 calculations matching that date and amount. Which one do you mean?”

The system should present safe distinguishing fields rather than guessing.

### 4.3 No match

The answer should say that no matching authoritative record was found.

It must not manufacture an explanation from generic knowledge.

### 4.4 Insufficient question

Example:

> “Why was my emissions high?”

If the system cannot identify a period, scope, report, activity, or other usable boundary, it should ask a concise clarification question.

---

## 5. Recommended question taxonomy

### A. Result explanation

- Why was this emission 20 kg CO2e?
- How was this result calculated?
- What caused this emission?

### B. Input explanation

- What quantity was used?
- What activity generated this result?
- What unit was used?

### C. Emission factor explanation

- Which emission factor was used?
- Which factor database was used?
- What factor year/version was used?
- Why was this factor selected?

### D. Methodology

- Which methodology was used?
- What scope/category is this?
- Why was this activity classified this way?

### E. Change analysis

- Why did emissions increase in February?
- What changed compared with January?
- Which activities drove the increase?

### F. Contribution analysis

- Which activity contributed most?
- Which source contributed most?
- Which supplier generated the highest emissions?

These queries require deterministic aggregation/discovery capabilities and should only be implemented where explicitly authorized.

### G. Evidence

- Show me the source.
- Which invoice produced this?
- Show the exact spreadsheet row.
- Where in the PDF did this value come from?

### H. Carbon-accounting concepts

- What is the difference between Scope 1 and Scope 2?
- What is location-based Scope 2?
- What is Scope 3 Category 1?

Conceptual answers may use governed product/domain knowledge, but should be clearly distinguished from customer-specific calculated facts.

---

## 6. Secure logical architecture

### Layer 1 — Conversation/UI

Responsibilities:

- receive user message;
- display answer;
- display clarification;
- display evidence navigation;
- display loading/error/no-data states.

It must not directly query the database.

### Layer 2 — Insight orchestration

Responsibilities:

- authenticate the user;
- establish organization context;
- classify/interpret the question;
- validate structured parameters;
- call only authorized deterministic services;
- enforce bounded context;
- pass verified results to the LLM.

### Layer 3 — Deterministic domain services

Responsibilities:

- discovery;
- calculation snapshot lookup;
- report lookup;
- report evidence lookup;
- evidence resolution;
- controlled aggregation where authorized.

These services are authoritative for facts.

### Layer 4 — Authorization boundary

Every customer-data operation must enforce the existing authorization model.

Authorization must occur server-side.

The LLM must never decide whether the user is authorized.

### Layer 5 — Persistence

Authoritative records include, as applicable:

- calculation snapshots;
- emissions records;
- source items;
- source documents;
- mapped data;
- report versions;
- evidence references;
- audit records.

### Layer 6 — Evidence Viewer

The Source Evidence Viewer remains the read-only customer evidence destination.

It should support the existing authoritative evidence chain rather than creating a second provenance system.

---

## 7. Deterministic discovery requirements

A discovery operation should be treated as a domain capability, not as free-form database search.

It should:

- accept a typed, bounded request;
- enforce organization scope;
- validate date/range/amount/unit inputs;
- apply explicit matching semantics;
- return stable identifiers;
- return only fields necessary for the next operation;
- expose match count/status;
- never mutate customer data.

Suggested response states:

```text
success
no_data
multiple_matches
invalid_input
not_authorized
provider_unavailable
error
```

`multiple_matches` is important for user-facing discovery even where existing generic tool statuses use a smaller established vocabulary.

If the existing public/tool contract cannot support a new status or operation without changing I3, Cline must stop and report the contract gap rather than silently widening I3.

---

## 8. Matching semantics

For a question such as:

> “Why was my CO2e 20 kg on 1 February 2024?”

Do not use uncontrolled fuzzy matching.

Use deterministic criteria such as:

1. organization_id = authenticated organization;
2. date = requested date, with explicitly documented timezone/date semantics;
3. result unit compatible with kg CO2e;
4. result amount within an explicitly defined tolerance, if approximate matching is supported;
5. exclude records that are not authoritative for customer reporting;
6. order deterministically by stable identifiers if multiple candidates are returned.

The tolerance must be a documented product rule, not an arbitrary LLM decision.

If amount matching is not yet authorized or specified, the service should use date/report/activity constraints that are actually supported rather than inventing tolerance behavior.

---

## 9. LLM contract

The LLM should receive a bounded structured payload, for example:

```json
{
  "intent": "explain_calculation",
  "organization_scoped": true,
  "authoritative_records": [
    {
      "snapshot_id": "...",
      "activity": "...",
      "quantity": 100,
      "quantity_unit": "kWh",
      "co2e_kg": 20,
      "scope": "Scope 2",
      "date": "2024-02-01",
      "methodology": "...",
      "factor_source": "...",
      "factor_id": "...",
      "source_item_id": "..."
    }
  ]
}
```

The LLM should be instructed:

- use only supplied authoritative facts for customer-specific claims;
- do not invent missing fields;
- do not perform a replacement calculation;
- do not claim evidence exists unless a valid reference is supplied;
- distinguish stored fact from explanation;
- state when data is unavailable;
- avoid revealing internal identifiers unless product policy permits them;
- never expose another organization’s information.

The LLM response should be considered presentation, not authoritative accounting state.

---

## 10. Evidence architecture

The preferred evidence chain is:

```text
Customer question
    ↓
Calculation snapshot
    ↓
source_item_id / source_line_item_id
    ↓
extraction / mapped data
    ↓
source document
    ↓
read-only Source Evidence Viewer
```

Where available, the evidence presentation should distinguish:

- original source;
- extracted value;
- mapped value;
- calculated result.

For tabular sources, preserve the existing authoritative semantics for:

- spreadsheet sheet;
- source row;
- CSV row;
- source line number/reference.

For PDFs/images, use only provenance fields actually established by the extraction pipeline.

Do not invent OCR coordinates or page/line precision that the source pipeline did not record.

---

## 11. Security requirements

### Authentication

All customer Insight operations require authenticated access.

### Authorization

Use server-side organization membership and existing I2 authorization.

### Object-level access control

Never trust IDs supplied by the client. Re-authorize every referenced object.

### Tenant isolation

All queries must be organization-scoped.

### Prompt injection resistance

Uploaded documents and extracted source text are untrusted data.

Document content must never be treated as system instructions.

The model must not obey instructions found inside:

- invoices;
- PDFs;
- spreadsheets;
- CSVs;
- OCR text;
- customer descriptions.

### Data minimization

Send the LLM only the fields required for the answer.

Avoid unnecessary raw source text, secrets, credentials, internal security metadata, or unrelated customer records.

### Signed URLs

Evidence access must continue through the existing controlled signed-URL/evidence mechanism.

Do not expose permanent private-storage URLs.

### Logging

Audit customer-data access through the existing append-only audit mechanism.

Do not log unnecessary sensitive source content.

### Rate limiting and abuse controls

Apply bounded request limits to customer-facing Insight endpoints, consistent with the already authorized I8-A principles.

### Error handling

Errors returned to users should not reveal:

- SQL;
- stack traces;
- storage credentials;
- internal infrastructure;
- unrelated organization IDs;
- hidden implementation details.

---

## 12. What the LLM must never do

The following are hard architectural prohibitions:

- unrestricted SQL/database access;
- arbitrary tool selection outside the authorized registry;
- cross-tenant retrieval;
- direct mutation of accounting records;
- changing emission factors;
- changing classifications;
- silently correcting historical results;
- recalculating authoritative historical results independently;
- fabricating provenance;
- fabricating evidence;
- inventing missing data;
- using another customer's data as context;
- treating source-document instructions as system instructions;
- bypassing I2/I3 authorization;
- introducing RAG/vector search/LangChain merely because it is convenient;
- creating a second evidence/provenance system.

---

## 13. Industry feature alignment

Modern carbon-accounting platforms commonly expose natural-language analysis over their own emissions/activity data, including:

- year-over-year comparisons;
- business-unit/facility comparisons;
- drivers of changes;
- activity-level explanations;
- emission-factor explanations;
- traceability to source/calculation records;
- plain-language carbon-accounting guidance.

CarbonTally can support these capabilities progressively, but each capability should be backed by a deterministic data contract.

A useful product pattern is:

> **Ask → Verify → Explain → Trace**

rather than:

> **Ask → Generate**

This is particularly important for auditability and professional carbon-accounting use.

---

## 14. Recommended phased capability model

### Phase A — Explain one verified calculation

Supported:

- identify a specific authoritative calculation;
- explain stored inputs;
- explain stored factor metadata;
- explain stored result;
- link to evidence.

### Phase B — Deterministic date/amount discovery

Supported after explicit authorization:

- find calculations by date;
- optionally match amount/unit;
- return zero/one/multiple candidates;
- ask clarification where necessary.

### Phase C — Deterministic comparisons

Potential future capability:

- month-over-month;
- year-over-year;
- scope comparison;
- facility/business-unit comparison.

Requires explicit aggregation definitions and authorization.

### Phase D — Driver/contributor analysis

Potential future capability:

- top emitting activities;
- top suppliers;
- largest increases/decreases;
- contribution percentages.

Requires governed aggregation, denominator semantics, and acceptance criteria.

### Phase E — Advanced anomaly/explanation assistance

Potential future capability:

- anomaly identification;
- change-driver narratives;
- suggested investigative paths.

Any recommendation or automated action must remain clearly separated from authoritative accounting results.

---

## 15. Acceptance criteria for an implementation

An implementation should not be considered complete merely because the UI produces a plausible answer.

Minimum acceptance criteria:

1. Exact customer organization isolation is demonstrated.
2. Deterministic discovery is reproducible.
3. No-match behavior is truthful.
4. Multiple-match behavior does not guess.
5. Authoritative calculation values come from persisted CarbonTally data.
6. The LLM cannot create authoritative numbers.
7. Evidence references resolve through the approved evidence architecture.
8. Unauthorized IDs do not disclose protected records.
9. Prompt-injection content in source documents does not alter system behavior.
10. Error paths fail closed.
11. Audit behavior is preserved.
12. Existing closed I2/I3/I4/I5/I6 contracts are not silently changed.
13. Any new contract or tool is explicitly authorized before implementation.
14. Tests cover success, no-data, multiple-match, invalid-input, unauthorized, and failure cases.
15. Cline produces a permanent implementation report.
16. OHD independently verifies the implementation.
17. PO explicitly closes the capability before it is treated as complete.

---

## 16. Cline implementation discipline

Before modifying code:

1. Inspect the current Insight orchestration.
2. Inspect the current I2/I3 contracts.
3. Inspect calculation snapshot APIs/services.
4. Inspect evidence-line/source-document routes.
5. Inspect existing RLS/organization authorization.
6. Inspect existing audit behavior.
7. Identify the smallest implementation surface.

During implementation:

- make the smallest bounded change;
- preserve closed contracts;
- do not refactor unrelated code;
- do not introduce new frameworks;
- do not change database schema unless explicitly authorized;
- do not modify external synthetic generator;
- add tests for every new branch;
- document all assumptions.

If the required capability cannot be implemented without changing a closed contract, **STOP** and report exactly which contract and why.

After implementation:

- run focused tests;
- run relevant regression tests;
- record failures accurately;
- create a permanent Markdown report;
- commit all changes;
- push to the authoritative release branch;
- provide exact commit SHA(s);
- stop for OHD verification.

---

## 17. OHD verification expectations

OHD must independently verify rather than repair.

Verification should include:

- source/code trace;
- authorization trace;
- tenant-isolation tests;
- no-data tests;
- multiple-match tests;
- invalid-input tests;
- evidence handoff tests;
- prompt-injection tests;
- regression tests;
- audit behavior;
- repository cleanliness/commit verification.

Any remediation discovered by OHD should return to Cline/PO governance rather than being silently fixed during verification.

---

## 18. Design decisions that should remain explicit

The following should not be guessed:

- whether date/amount discovery becomes a fifth I3 tool;
- exact amount-matching tolerance;
- timezone semantics for date matching;
- whether contributor/supplier analysis is authorized;
- whether consultant/internal-staff users get Insight access;
- org-viewer execution rights;
- pagination;
- retention/deletion/legal-hold policy;
- commercial/billing behavior;
- provider selection;
- production deployment authorization.

---

## 19. Reference architecture summary

```text
                    ┌──────────────────────────┐
                    │   CarbonTally Insight    │
                    │     Customer Question    │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Intent / Parameter       │
                    │ Interpretation (LLM)     │
                    └────────────┬─────────────┘
                                 │
                         structured request
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Authorization + Tenant    │
                    │ Boundary (server-side)   │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Deterministic Domain     │
                    │ Discovery / Lookup       │
                    └────────────┬─────────────┘
                                 │
                         authoritative facts
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Calculation / Evidence   │
                    │ Records + Provenance     │
                    └────────────┬─────────────┘
                                 │
                         verified context
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ LLM Explanation Layer    │
                    │ Plain English only       │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Answer + Evidence Link   │
                    │ + Viewer Navigation      │
                    └──────────────────────────┘
```

---

## 20. Final architectural rule

**CarbonTally Insight should behave like a governed carbon-accounting assistant, not a general-purpose chatbot with database access.**

The authoritative path is:

**deterministic CarbonTally data → authorized retrieval → verified evidence → LLM explanation.**

The LLM is the explanation layer.

CarbonTally's persisted records, deterministic domain services, authorization boundaries, and evidence lineage remain the source of truth.
