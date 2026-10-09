# CarbonTally — Incremental ChatGPT & PO Conversation History
## Continuity checkpoint — 2026-09-22

> Purpose: durable restart context if a ChatGPT conversation is lost, truncated, or restarted.
> This file records **decisions and verified state**, not hidden reasoning. It should be updated incrementally after each material PO/Cline/OHD milestone.
> A new conversation must treat this file + the latest committed repository reports as the continuity baseline.

## 1. Continuity rule

At every material stage, maintain:
1. Latest PO decision/state record.
2. Latest Cline implementation/forensic report.
3. Latest OHD independent verification report.
4. Exact commit SHA(s).
5. Explicit CLOSED / IMPLEMENTED / IN PROGRESS / BLOCKED / DEFERRED / NOT AUTHORIZED state.
6. Next authorized action and stop condition.

If the conversation disappears, resume from the latest checkpoint rather than reconstructing decisions from memory.

## 2. Authoritative repository

- Release checkout: `/home/shomonrobie/ct_93d5cdd`
- Branch: `p8-release-reconciled`
- Remote used for release pushes: `github`
- Do not infer repository state from the parent clone.
- Every repository modification must be committed and pushed.
- OHD is independent verification; it must not silently fix implementation defects.

## 3. Current Phase 8 state

### CLOSED / VERIFIED
- I1 — CLOSED / implemented baseline.
- I2 — CLOSED / VERIFIED PASS.
- I3 — CLOSED / VERIFIED PASS; four identifier-only tools:
  - `report_lookup`
  - `report_version_lookup`
  - `report_evidence_lookup`
  - `calculation_snapshot_lookup`
- I4 — CLOSED / VERIFIED PASS; canonical audit ledger `public.audit_trail`.
- I5 — CLOSED / VERIFIED PASS; bounded deterministic context, 20,000-character default.
- I6 — CLOSED / VERIFIED PASS; authenticated customer Insight surface and evidence handoff.
- Source Evidence Viewer + Insight Evidence Navigation — CLOSED / independently verified, with non-blocking observations accepted.

### NOT AUTHORIZED / NOT READY
- I7 — NOT AUTHORIZED / NOT READY.
- I8 commercial/billing — NOT AUTHORIZED.
- Production deployment — separate controlled authorization only.
- Consultant/internal-staff/auditor Insight surfaces — not authorized.
- New/widened I3 tools — prior closed boundary; now subject to the new PO decisions recorded below, but implementation requires a bounded authorization.

## 4. Authoritative architecture/reference documents

- `docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22.md`
- `docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md`
- `docs/architecture/CT-P8-INSIGHT-ARCHITECTURE-IMPLEMENTATION-GAP-20260922.md`
- `docs/architecture/CT-P8-INSIGHT-QUESTION-LIBRARY-CAPABILITY-GAP-20260922.md`

The two Question/Architecture reference documents are design/reference documents, not implementation authorization by themselves.

## 5. Latest forensic findings

Cline's second Question Library gap analysis was completed read-only and committed as:

`7f97b5568c72a0081a31bf50b14e532f0e51de82`

Report:
`docs/architecture/CT-P8-INSIGHT-QUESTION-LIBRARY-CAPABILITY-GAP-20260922.md`

Key findings:
- Backend deterministic capability is materially broader than Insight reachability.
- Existing backend aggregation covers scope, month, year, asset, facility and activity; supplier aggregation exists structurally but supplier persistence is missing.
- Insight currently reaches only the closed identifier-based tools plus evidence handoff.
- Supplier ID is captured upstream but not persisted by the application emission write path.
- Scope 3 category 1–15 is not a first-class data dimension.
- Market-based Scope 2 is not implemented in the calculation layer; disclosure has only a method hint.
- Aggregate responses contain no component identifiers, so aggregate-to-evidence drill-down is absent.
- Factor snapshots retain the used factor identity/value but not the full historical factor metadata/candidate set.
- Rate-limit middleware exists but is not registered.
- A pre-existing factor usage endpoint exposes platform-wide usage counts/timestamps because those queries lack organization scoping; this was not introduced by Insight and remains a security remediation item.

## 6. PO decisions adopted at this checkpoint

### D-01 — Insight architecture principle
**DECIDED: Authoritative data first, deterministic computation second, LLM narration last.**

The LLM must not become the calculation engine, database query engine, authorization layer, or source of authoritative carbon figures.

### D-02 — Discovery
**DECIDED: APPROVE a future bounded discovery capability.**

It must support typed/allowlisted dimensions such as:
- date/date range
- amount/CO2e tolerance
- activity
- supplier
- facility/asset
- scope
- reporting period

It must return deterministic states for zero/one/multiple candidates and must not expose arbitrary SQL or unrestricted search.

Amount tolerance and timezone semantics must be explicit product rules before implementation.

### D-03 — Aggregation
**DECIDED: APPROVE a future bounded Insight analytics capability.**

Insight may reach deterministic org-scoped aggregation only through an allowlisted contract with:
- permitted dimensions
- permitted filters
- bounded date ranges
- bounded result size
- explicit units/basis
- organization authorization
- evidence/provenance references where contractually supported.

No arbitrary query interface.

### D-04 — Scope 3 taxonomy
**DECIDED: APPROVE GHG Protocol Scope 3 Categories 1–15 as the product's baseline category taxonomy.**

The taxonomy must be explicit and versioned. Do not infer a category merely from an arbitrary activity string without a governed mapping rule. Historical mapping/version semantics must be defined before implementation.

### D-05 — Supplier persistence
**DECIDED: APPROVE persistence of supplier identity through the calculation lineage.**

The existing mapped supplier relationship should be propagated into the authoritative emission/calculation lineage using a governed confidence/approval rule. Backfill policy must be explicit. Supplier analytics must not be exposed until persistence and data-quality rules are verified.

### D-06 — Primary vs secondary data
**DECIDED: REQUIRE an explicit provenance classification.**

Do not equate `factor_kind=customer_factor` with primary data. Do not equate `spend_based` with secondary data. The platform needs a governed definition and auditable provenance for primary/secondary/estimated status.

### D-07 — Scope 2
**DECIDED: PRODUCT TARGET = dual location-based + market-based Scope 2 reporting.**

This follows the current GHG Protocol Scope 2 framework, which defines both methods and emphasizes transparency/quality of contractual instruments. The implementation must be versioned because GHG Protocol is actively updating its corporate suite.

Market-based accounting therefore requires explicit modeling of the method basis and applicable instruments/factor hierarchy; it must not be simulated by a disclosure hint.

### D-08 — Scope 1 decomposition
**DECIDED: APPROVE a governed decomposition taxonomy for stationary combustion, mobile combustion, fugitive emissions and process emissions, where applicable.**

Do not rely permanently on free-text activity labels for this analytical dimension.

### D-09 — Variance
**DECIDED: REQUIRE deterministic, reproducible variance definitions before Insight attribution.**

A future variance capability must distinguish, where data supports it:
- activity/quantity change
- emission-factor change
- methodology change
- boundary change
- data-availability/restatement effects

It must explicitly state when attribution cannot be established.

### D-10 — Aggregate → evidence
**DECIDED: REQUIRE bounded aggregate-to-evidence drill-down before presenting aggregate answers as audit-ready.**

An aggregate answer must be traceable to its contributing calculation snapshots and, where permitted, source evidence. The response must respect DM-6 and data minimization.

### D-11 — Factor history
**DECIDED: Historical factor metadata required for audit-grade explanations.**

The exact factor value used is already retained. Future audit-grade explanation should also retain/version the relevant metadata needed to reproduce what the factor meant at calculation time. Candidate-factor history is separate and should not be claimed unless stored.

### D-12 — Conceptual carbon-accounting answers
**DECIDED: Separate Mode E knowledge answers from customer-data answers.**

Conceptual answers may use a governed carbon-accounting knowledge source, but must never be presented as customer-specific calculated facts. Source/version attribution is required.

### D-13 — Personas
**DECIDED: Customer Insight is the primary v1 analytical surface.**

Consultant and auditor workflows remain separately governed. An external auditor is not automatically a tenant user; customer-authorized export/evidence workflows are preferred over direct auditor tenant access unless separately authorized.

### D-14 — Rate limiting/security
**DECIDED: Rate limiting is required before scaling new customer-facing analytical surfaces.**

Concrete thresholds and acceptance criteria require a bounded I8 authorization. No silent implementation.

### D-15 — Standards/versioning
**DECIDED: CarbonTally must version accounting methodologies/taxonomies and preserve the basis used for a calculation.**

GHG Protocol is the primary corporate-accounting reference; ISO 14064-1 remains an important organization-level reporting/verification reference. Standards are evolving, so CarbonTally must avoid hard-coding an assumption that future revisions do not exist.

## 7. Capability status after PO decisions

| Capability | PO status | Implementation authorization |
|---|---|---|
| Existing scope/month/year/activity/facility aggregation | APPROVED FOR FUTURE BOUNDED INSIGHT EXPOSURE | Separate Cline authorization required |
| Discovery | DECIDED / APPROVED IN PRINCIPLE | Separate bounded implementation package required |
| Scope filters | DECIDED / REQUIRED | Separate backend authorization |
| Scope 3 category taxonomy | DECIDED / REQUIRED | Data-model + mapping authorization required |
| Supplier persistence | DECIDED / REQUIRED | Separate bounded pipeline/data authorization |
| Supplier analytics | CONDITIONAL | Only after supplier persistence verification |
| Primary/secondary provenance | DECIDED / REQUIRED | Data-model/provenance authorization required |
| Scope 2 market-based | DECIDED / REQUIRED | Accounting/data-model authorization required |
| Scope 1 decomposition | DECIDED / REQUIRED | Taxonomy/data-model authorization required |
| Variance/attribution | DECIDED / REQUIRED | Separate deterministic capability authorization |
| Aggregate→evidence drill-down | DECIDED / REQUIRED | Separate bounded capability authorization |
| Historical factor metadata | DECIDED / REQUIRED | Separate retention/schema authorization |
| Concept answers | DECIDED / FUTURE | Separate knowledge-governance package |
| Rate limiting | REQUIRED | I8 bounded authorization required |
| Consultant Insight | DEFERRED / separate decision | Not authorized |
| Auditor direct Insight | DEFERRED / separate decision | Not authorized |
| I7 | NOT READY | Not authorized |
| Full I8/commercial | NOT READY | Not authorized |
| Production deployment | NOT AUTHORIZED | Separate deployment decision |

## 8. Industry/reference basis used for PO decisions

- GHG Protocol identifies its Corporate Standard and Scope 3 Standard as frameworks for corporate/value-chain inventories.
- GHG Protocol Scope 2 Guidance defines location-based and market-based methods and quality criteria for contractual instruments.
- ISO 14064-1:2018 specifies organization-level GHG quantification/reporting principles and requirements and remains current as of 2026.
- GHG Protocol and ISO announced a strategic partnership in 2025 to harmonize corporate GHG accounting/reporting standards; future revisions therefore require methodology versioning.
- Current carbon-accounting platforms emphasize traceable methodology, emission-factor transparency, audit trails, data lineage, dimensions, user permissions and human review around AI.
- These references support architecture decisions, but they do not authorize implementation or prove customer-specific requirements.

## 9. Mandatory governance sequence

For every newly approved capability:

PO decision → bounded Cline implementation authorization → Cline implementation + permanent report + commit/push → OHD independent verification → PO closure → separate deployment authorization if applicable.

No capability becomes CLOSED merely because Cline reports PASS.

## 10. Latest next step

The next task is to turn the PO decisions into **small implementation authorization packages**, beginning with the dependency-safe foundation rather than implementing the whole Question Library.

The likely first implementation package should be the smallest authoritative data/contract foundation needed for future Insight analytics, not a giant "build Insight" task.

