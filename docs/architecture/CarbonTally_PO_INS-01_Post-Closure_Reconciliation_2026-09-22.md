# CarbonTally — PO INS-01 Post-Closure Reconciliation

**Date:** 2026-09-22  
**Status:** **CLOSED — IMPLEMENTED & INDEPENDENTLY VERIFIED**  
**Program:** CarbonTally Phase 8 / Insight  
**Package:** INS-01 — Insight Discovery, Aggregation, Provenance, Shared Evidence & Rate Limiting  
**Authoritative checkout:** `/home/shomonrobie/ct_93d5cdd`  
**Branch:** `p8-release-reconciled`  
**Remote:** `github`

---

## 1. Purpose

This is the permanent Product Owner (PO) post-closure reconciliation record for **INS-01 — Insight Discovery, Aggregation, Provenance, Shared Evidence & Rate Limiting**.

It records the scope PO authorized, what Cline implemented, what OHD independently verified, the PO closure decision, accepted non-blocking observations, pre-existing baseline failures, explicit exclusions, and the next planning gate.

This document does **not** authorize new implementation work.

## 2. Authoritative source records

### Architecture / product references

- `/home/shomonrobie/ct_93d5cdd/docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md`
- `/home/shomonrobie/ct_93d5cdd/docs/architecture/CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md`
- `/home/shomonrobie/ct_93d5cdd/docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md`

### Cline implementation evidence

- `docs/architecture/CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-IMPLEMENTATION-20260922.md`
- Preflight: `c7cd9cc2ff56e288c830bb5d204118a06aa31104`
- Implementation: `e4ea3254c6a709df0e9cedcd8c719515363b4358`
- Final implementation/report: `cbc529dd8974d3ec16595fc5c6981c5217b43c24`

### OHD independent verification evidence

- `docs/architecture/CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-OHD-VERIFICATION-20260922.md`
- Verification ID: `OHD-INS-01-20260922`
- OHD report commit: `f1a7cce` (local at the time of verification)
- OHD verdict: **PASS WITH NON-BLOCKING OBSERVATIONS**

OHD independently verified the implementation, including live disposable PostgreSQL migration execution, schema/constraint checks, concurrent limiter behavior, regression comparison against a pristine baseline, and security/tenant-isolation checks.

## 3. Original INS-01 authorization boundary

INS-01 was authorized as a bounded foundation package covering:

1. bounded Insight discovery;
2. bounded Insight aggregation;
3. aggregate → calculation provenance;
4. reuse of the Shared Source Evidence Viewer;
5. I3 expansion with exactly three additional Insight tools;
6. I4 expansion with `multiple_matches`;
7. a typed, allowlisted query planner;
8. technical rate limiting and concurrency protection;
9. strict tenant isolation/security;
10. comprehensive tests and permanent implementation documentation.

The authorization explicitly excluded:

- Scope 3 Categories 1–15 implementation;
- market-based Scope 2 calculation;
- Scope 1 decomposition;
- primary/secondary factor provenance classification;
- historical factor metadata expansion;
- variance/attribution;
- supplier persistence/backfill/inference;
- RAG or unrestricted knowledge retrieval;
- consultant Insight;
- auditor direct Insight;
- arbitrary natural-language querying or SQL generation;
- cross-tab analytics;
- subscriptions, billing, commercial entitlements, quotas, credits or overages;
- I7;
- full I8;
- production deployment.

These excluded areas were not authorized merely because they appear in the broader Insight architecture or PO capability matrix.

## 4. Cline implementation result

Cline implemented the authorized foundation, tested it, documented it, committed it and pushed it.

### I3

Three new tools:

- `insight_discovery`
- `insight_aggregation`
- `insight_aggregate_provenance`

The four previously ratified I3 tools remained unchanged in contract vocabulary.

`ToolStatus` remained the original six-value vocabulary.

`REFERENCE_KINDS` remained the original four-value vocabulary.

All new tools remained read-only and organization-scoped through the existing I2 authorization boundary.

### I4

One new interaction answer state was introduced:

- `multiple_matches`

No new `ToolStatus` was introduced.

Ambiguous discovery results are not silently converted into a selected candidate, and narration is suppressed for the ambiguous state.

### Discovery

The bounded discovery foundation supports:

- date/date range;
- reporting year;
- CO₂e amount;
- explicit absolute or relative tolerance;
- activity;
- scope;
- supplier;
- facility;
- asset.

Discovery is deterministic, organization-scoped, bounded to 25 candidates, and does not permit arbitrary SQL or unrestricted querying.

Approximate amount queries without an explicit tolerance are not guessed.

### Aggregation

The bounded aggregation foundation supports:

- scope;
- month;
- year;
- activity;
- supplier;
- facility;
- asset.

Aggregation is bounded to 50 groups and a maximum 10-year period.

The accounting basis is kg CO₂e from the authoritative calculated emissions field.

No mixed-unit quantity total is exposed.

### Aggregate → provenance

The bounded provenance tool identifies contributing calculation snapshots, with a maximum of 100 references and truthful truncation signaling.

Returned provenance is identifier-based and does not expose raw source content or signed URLs to the LLM.

### Shared Source Evidence Viewer

No new viewer was created.

INS-01 reuses the existing Source Evidence Viewer and existing calculation/evidence reference architecture.

The intended chain remains:

**Insight explanation → calculation/reference → existing Source Evidence Viewer**

The LLM is not the evidence viewer and does not receive signed URLs or raw source documents.

### Query planner

The planner is deterministic and bounded.

It does not contain database access, provider access, authorization logic, SQL generation, or an unrestricted query interface.

The planner produces only closed, allowlisted tool plans and parameters; downstream validation and I2 authorization remain authoritative.

### Technical rate limiting

Technical abuse-protection rate limiting was implemented using PostgreSQL-backed bucket and concurrency mechanisms.

Ratified defaults:

- user: 20 requests/minute, burst 5, capacity 25, maximum concurrency 2;
- organization: 100 requests/minute, burst 20, capacity 120, maximum concurrency 10.

The implementation is server-configured and ceiling-bounded.

Both customer-facing Insight execution routes are protected.

Rate limiting has no commercial billing, entitlement, subscription, credit, overage or payment semantics.

## 5. OHD independent verification result

OHD independently verified the implementation with the final verdict:

> **PASS WITH NON-BLOCKING OBSERVATIONS**

The verification independently established, among other things:

- exactly seven authorized I3 tools;
- unchanged six-value `ToolStatus`;
- unchanged four `REFERENCE_KINDS`;
- exactly one new I4 answer state;
- truthful multiple-match handling;
- bounded discovery at 25;
- bounded aggregation at 50 groups;
- bounded provenance at 100 snapshots;
- organization-scoped analytical queries;
- deterministic ordering;
- truncation honesty;
- reuse of the existing Source Evidence Viewer;
- bounded query planner behavior under adversarial inputs;
- technical rate limiting on both customer-facing execution paths;
- live migration application and idempotency against disposable PostgreSQL;
- live concurrent limiter behavior;
- no new regression compared with the pristine preflight baseline.

OHD also independently reproduced the new test suites and established that the package introduced no new test failures.

## 6. PO capability-status reconciliation

The original PO capability matrix predates INS-01 and therefore contains statuses that must now be interpreted together with this closure record.

| Capability | Pre-INS-01 position | INS-01 result | PO status after closure |
|---|---|---|---|
| Insight discovery | No Insight discovery contract | Bounded discovery implemented and independently verified | **CLOSED — FOUNDATION** |
| Insight aggregation | Backend foundations existed but were not exposed through the closed Insight contract | Seven bounded dimensions implemented and verified | **CLOSED — FOUNDATION** |
| Aggregate → calculation provenance | Missing as an Insight contract | Bounded provenance implemented and verified | **CLOSED — FOUNDATION** |
| I3 Insight tool catalogue | Four ratified tools | Seven authorized tools verified | **CLOSED — INS-01 SCOPE** |
| I4 ambiguity state | No `multiple_matches` state | `multiple_matches` implemented and verified | **CLOSED — INS-01 SCOPE** |
| Query planner | No bounded Insight planner | Typed deterministic planner implemented and verified | **CLOSED — FOUNDATION** |
| Technical rate limiting | Middleware existed but was inactive | User/org bucket + concurrency protection implemented and verified | **CLOSED — TECHNICAL PROTECTION** |
| Shared Source Evidence Viewer | Existing core evidence capability | Reused without duplication or weakening | **CLOSED / CORE CAPABILITY** |
| Supplier intelligence | Analytics required persistence work | Supplier dimension structurally supported; persistence/backfill not implemented | **PARTIAL — NOT COMPLETE** |
| Facility/asset intelligence | Existing operational metadata | Bounded lineage-based support implemented | **PARTIAL — FOUNDATION** |
| Scope 3 Categories 1–15 | Not first-class | Not implemented | **NOT IMPLEMENTED** |
| Scope 2 market-based accounting | Not implemented | Not implemented | **NOT IMPLEMENTED** |
| Scope 1 decomposition | Not implemented | Not implemented | **NOT IMPLEMENTED** |
| Primary/secondary provenance classification | Not implemented | Not implemented | **NOT IMPLEMENTED** |
| Variance/attribution | Not implemented | Not implemented | **NOT IMPLEMENTED** |
| Historical factor metadata expansion | Not implemented | Not implemented | **NOT IMPLEMENTED** |
| Concept-answer knowledge layer | Not implemented | Not implemented | **NOT IMPLEMENTED** |
| Consultant Insight | Deferred | No change | **DEFERRED / NOT AUTHORIZED** |
| Auditor direct Insight | Deferred | No change | **DEFERRED / NOT AUTHORIZED** |
| I7 retention/deletion/export | Deferred | No change | **NOT AUTHORIZED** |
| Full I8 commercial | Deferred | No change | **NOT AUTHORIZED** |
| Production deployment | Separate control | No change | **NOT AUTHORIZED** |

**Important:** “CLOSED — FOUNDATION” does not mean the entire long-term capability is complete. It means the bounded INS-01 foundation authorized for that capability is implemented and independently verified.

## 7. Shared Source Evidence Viewer — PO confirmation

The Shared Source Evidence Viewer is confirmed as a **core CarbonTally platform capability**.

It is not treated as an Insight-only feature.

The product architecture remains:

**Source document → extracted data → mapped line item → calculation → emission factor → emissions result → report → Insight explanation → Source Evidence Viewer**

The architectural separation is:

- deterministic CarbonTally data/calculation = source of truth;
- Insight = explanation/orchestration layer;
- Source Evidence Viewer = evidence destination.

INS-01 did not create a second evidence viewer and did not weaken the existing evidence/security architecture.

Future Insight capabilities should continue to reuse this shared evidence destination.

## 8. Non-blocking OHD observations accepted for carry-forward

PO reviewed the OHD observations and accepts them as non-blocking carry-forward items.

### 8.1 Supplier/facility/asset EXISTS organization predicate

The discovery `EXISTS` subqueries do not repeat `l.organization_id = $1`.

OHD found no disclosure path because the outer query is organization-scoped, but identified a theoretical possibility that a foreign log row referencing an organization-owned snapshot could influence a match count.

**PO decision:** accept as non-blocking defence-in-depth observation. No remediation is authorized by this closure record.

### 8.2 Cline test-accounting discrepancy

OHD established four pre-existing failures at both baseline and HEAD:

- the stale migration-count pin;
- three `test_review_sla_surfaces.py` assertions.

The failure set was identical at baseline and HEAD.

**PO decision:** accept OHD's baseline comparison as authoritative for regression assessment. No remediation is authorized by this closure record.

### 8.3 Stale tool-registry comment

A code comment still describes the registry as containing exactly four ratified tools even though the catalogue now contains seven.

**PO decision:** non-blocking documentation drift. No remediation is authorized by this closure record.

### 8.4 Closed label-source map

The new aggregation label SQL uses a closed allowlist of table/key mappings.

**PO decision:** retain the closed-map security pattern. Future extension must preserve the allowlist boundary.

### 8.5 Limiter table operational cleanup

The rate-limit tables are bounded by user/organization keys rather than request volume, but no cleanup path is currently defined.

**PO decision:** carry forward for future operational/runbook work. Not a closure blocker.

### 8.6 Existing factor metadata cross-tenant issue

The pre-existing `snapshot_count_for_factor()` / `factor_usage_span()` exposure remains separately tracked.

OHD confirmed INS-01 did not worsen it or depend upon it.

**PO decision:** no change to its separate remediation status.

### 8.7 SEC-01 wording reconciliation

The earlier PO matrix describes I8 rate-limit thresholds as not authorized. The later INS-01 authorization explicitly authorized the technical rate-limiting implementation and exact defaults.

**PO decision:** INS-01 supersedes that wording for **technical rate limiting only**.

Commercial usage limits, quotas, billing, subscriptions, credits, overages and other I8 commercial controls remain unauthorized.

### 8.8 Live deployed HTTP E2E

OHD did not exercise a live deployed ASGI HTTP request because no such deployment was available.

Code-path and unit verification, plus live repository/DB verification, were completed.

**PO decision:** non-blocking observation for this package. It does not imply production deployment authorization.

## 9. Pre-existing defects and regression boundary

OHD independently compared the implementation against a pristine copy of the preflight commit.

The same four failures existed at the baseline and at HEAD.

Therefore:

- INS-01 introduced **zero new test failures**;
- the pre-existing failures are not attributed to INS-01;
- the stale migration-count pin remains pre-existing;
- the three review/SLA API-surface failures remain pre-existing.

This closure record does not authorize remediation of those unrelated defects.

## 10. Explicitly not delivered by INS-01

The following remain outside the closed INS-01 scope:

### Accounting/data model

- Scope 3 Categories 1–15 first-class taxonomy/data model;
- market-based Scope 2 calculation;
- Scope 1 decomposition;
- primary/secondary provenance classification;
- supplier persistence/backfill/inference;
- historical factor metadata expansion;
- variance/attribution methodology;
- assumptions/restatements governance.

### Insight capabilities

- broad Scope 3 analytics;
- market-based Scope 2 analytics;
- Scope 1 decomposition analytics;
- supplier intelligence beyond the bounded structural foundation;
- variance and causal attribution;
- factor-change attribution;
- governed carbon-accounting knowledge layer;
- reporting/disclosure assistance;
- decision/reduction intelligence;
- consultant Insight;
- direct auditor Insight;
- unrestricted natural-language analytics;
- arbitrary SQL or model-generated SQL;
- cross-tab analytics.

### Platform governance

- I7 retention/deletion/export package;
- full I8 commercial package;
- subscription/billing/entitlement/overage/credit systems;
- production deployment.

None of these are authorized merely by this closure.

## 11. Technical rate limiting versus I8 commercial governance

This reconciliation explicitly separates two concepts.

### Closed under INS-01

Technical abuse protection:

- server-controlled request-rate limits;
- burst protection;
- execution concurrency limits;
- 429 refusal;
- `Retry-After`;
- tenant/user isolation;
- protection before expensive Insight/provider execution.

### Still not authorized

Commercial controls:

- plan entitlements;
- paid usage quotas;
- overage charging;
- credits;
- subscriptions;
- payment-provider integration;
- commercial usage metering;
- billing failure handling;
- refunds;
- commercial SLO/DR commitments.

Therefore, **technical rate limiting being closed does not close I8**.

## 12. Git and documentation durability

### Implementation

The implementation is represented by:

- preflight: `c7cd9cc2ff56e288c830bb5d204118a06aa31104`;
- implementation: `e4ea3254c6a709df0e9cedcd8c719515363b4358`;
- final implementation/report: `cbc529dd8974d3ec16595fc5c6981c5217b43c24`.

The implementation checkout was clean and aligned with `github/p8-release-reconciled` at the end of Cline implementation.

### OHD verification

OHD created the verification report at:

`docs/architecture/CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-OHD-VERIFICATION-20260922.md`

OHD committed it locally as `f1a7cce` but did not push it because the verification authorization did not request a push.

**PO durability requirement:** before this reconciliation is considered fully durable on the remote repository, the OHD report should be pushed without content modification, together with this PO closure record, through the normal repository process.

No implementation change is authorized by that documentation push.

## 13. PO closure decision

# **INS-01 CLOSED — IMPLEMENTED & INDEPENDENTLY VERIFIED**

PO accepts the OHD verdict:

**PASS WITH NON-BLOCKING OBSERVATIONS**

The authorized INS-01 scope was implemented by Cline and independently verified by OHD.

The OHD verification established no new regression, no discovered tenant-disclosure vulnerability in the authorized package, correct bounded discovery/aggregation/provenance behavior, correct I3/I4 expansion, reuse of the Shared Source Evidence Viewer, and live PostgreSQL-backed concurrency/rate-limit integrity.

The non-blocking observations listed in §8 are accepted as carry-forward items and are **not conditions of INS-01 closure**.

No remediation is authorized by this closure record.

## 14. Remaining authorization boundary after closure

The following remain outside the current authorization:

- I7;
- full I8;
- commercial billing/entitlements;
- consultant Insight;
- auditor direct Insight;
- production deployment;
- all unimplemented accounting/Insight capabilities listed in §10.

Future implementation must receive a separate bounded PO authorization.

## 15. Next planning gate

The next controlled PO task is **not another implementation**.

The next task is to create the **CarbonTally Insight Capability Coverage Matrix** using:

1. `CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md`;
2. the existing PO Insight Capability Decision Matrix;
3. the 426-question Insight Question Library;
4. the closed INS-01 implementation evidence;
5. the OHD verification evidence.

The Capability Coverage Matrix should map:

**Question → Capability Family → Deterministic Engine → Required Data → Evidence Requirement → Answer State → Current Implementation → Verification Status → Dependencies → Authorization Status**

It is a planning/coverage artifact, not implementation authorization.

## 16. Governance rule reaffirmed

CarbonTally Insight development remains governed by:

**PO decision → bounded Cline authorization → implementation → independent OHD verification → PO closure**

No architecture reference, question library, capability approval, or planning matrix is blanket authorization to implement all future capabilities.

## 17. Final status summary

| Area | Final status |
|---|---|
| INS-01 authorization | **CLOSED** |
| Cline implementation | **IMPLEMENTED** |
| OHD independent verification | **PASS WITH NON-BLOCKING OBSERVATIONS** |
| Discovery foundation | **CLOSED — FOUNDATION** |
| Aggregation foundation | **CLOSED — FOUNDATION** |
| Aggregate provenance | **CLOSED — FOUNDATION** |
| I3 expansion | **CLOSED — INS-01 SCOPE** |
| I4 `multiple_matches` | **CLOSED — INS-01 SCOPE** |
| Query planner | **CLOSED — FOUNDATION** |
| Technical rate limiting | **CLOSED — TECHNICAL PROTECTION** |
| Shared Source Evidence Viewer | **CORE CAPABILITY / VERIFIED REUSE** |
| Scope 3 Categories 1–15 | **NOT IMPLEMENTED** |
| Scope 2 market-based | **NOT IMPLEMENTED** |
| Scope 1 decomposition | **NOT IMPLEMENTED** |
| Supplier persistence/backfill | **NOT IMPLEMENTED** |
| Variance/attribution | **NOT IMPLEMENTED** |
| Factor-history expansion | **NOT IMPLEMENTED** |
| Concept knowledge layer | **NOT IMPLEMENTED** |
| Consultant Insight | **DEFERRED / NOT AUTHORIZED** |
| Auditor direct Insight | **DEFERRED / NOT AUTHORIZED** |
| I7 | **NOT AUTHORIZED** |
| Full I8 commercial | **NOT AUTHORIZED** |
| Production deployment | **NOT AUTHORIZED** |
| Next planning task | **Capability Coverage Matrix** |

---

**PO closure authority:** CarbonTally Product Owner  
**Closure date:** 2026-09-22  
**INS-01 status:** **CLOSED — IMPLEMENTED & INDEPENDENTLY VERIFIED**
