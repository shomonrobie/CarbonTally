# CarbonTally Incremental Chat History — 2026-09-22
## Resume point after Insight Foundation Implementation Authorization

### Purpose
This file preserves the current decision/state so a future conversation can resume without reconstructing the missing chat.

### Current authoritative repository
- Checkout: `/home/shomonrobie/ct_93d5cdd`
- Branch: `p8-release-reconciled`
- Remote: `github`
- Remote URL: `https://github.com/shomonrobie/CarbonTally.git`
- Do not use the parent clone `/home/shomonrobie/carbon_tally` for Phase 8 release work.
- Earlier local `origin` in the release checkout is stale/dead; Phase 8 pushes use `github`.

### Governance
PO authorizes and closes scope. Cline implements/forensics. OHD independently verifies and must not silently fix.
Every repository modification must be committed and pushed.
Cline must create a permanent Markdown report for each bounded implementation/verification task.
Implementation PASS is not PO closure.
Production deployment is always a separate controlled decision.

### Phase 8 established status
- I1 CLOSED / implemented baseline.
- I2 CLOSED / VERIFIED PASS.
- I3 CLOSED / VERIFIED PASS. Four ratified read-only tools:
  `report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup`.
  ToolStatus includes `success`, `no_data`, `not_authorized`, `invalid_input`, `error`; `provider_unavailable` reserved for provider-dependent paths.
- I4 CLOSED / VERIFIED PASS. Canonical audit ledger is `public.audit_trail`; dormant `public.ai_content_history` preserved unchanged (Q1 Option C).
- I5 CLOSED / VERIFIED PASS. Deterministic bounded current-conversation context, 20,000-character default/configurable; no summarization/persistence/cross-conversation/RAG/LangChain.
- I6 CLOSED / VERIFIED PASS. Authenticated customer `/insight`; creator-private conversations; evidence references; provider-unavailable; empty/loading/error; accessibility/responsive. No public assistant.
- I7 NOT AUTHORIZED / NOT READY. Needs retention/deletion/legal hold/export/privacy/acceptance package.
- I8 full stage NOT AUTHORIZED. I8-A technical principles partially authorized/closed; I8-B commercial/billing not authorized. Needs usage/entitlement, SLO, backup/recovery, incident/runbook, payment/billing facts and acceptance.
- Production deployment NOT AUTHORIZED.

### Source Evidence Viewer
PO decision: Shared Source Evidence Viewer is a CORE CARBONTALLY PLATFORM CAPABILITY.
Architecture:
Source document → extracted data → mapped line item → calculation → emission factor → emissions result → report → evidence.
Primary access:
1. Report → number → calculation detail → View source evidence.
2. Emissions/calculation → calculation detail → View evidence.
3. Insight → explanation → View calculation / View source evidence.
A future Evidence Center may exist, but must reuse the same viewer.
Do not create a second Insight-only evidence viewer.
Viewer is read-only and tenant-scoped; existing DM-6/signed URL/audit controls remain.

Known Source Evidence implementation history:
- implementation commit `999e4fb`
- implementation docs `de021ab`
- OHD verification commit `5d5f7ed`
- OHD verdict: PASS WITH NON-BLOCKING OBSERVATIONS.
A current repo record should be checked before asserting final PO-closure status if needed.

### Insight architecture/product direction
Core product principle:
User question → bounded typed intent/query → server validation/authorization → deterministic CarbonTally data → deterministic computation → provenance → Source Evidence Viewer → LLM narration.

LLM must not become:
- arbitrary SQL/query engine;
- authorization mechanism;
- source-of-truth calculator;
- evidence system.

Reference files saved in release checkout:
- `docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22.md`
- `docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md`
- `docs/architecture/CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md`
- `docs/ChatGPT/CarbonTally_Incremental_ChatGPT_PO_History_2026-09-22.md`

The Question Library contains 426 candidate questions across 43 sections / 20 capability families / 19 capability clusters.
It is a reference, not blanket implementation authorization.

### PO capability decisions
- D-01 authoritative data → deterministic computation → evidence → LLM narration.
- D-02 future bounded discovery: date, amount/CO2e+tolerance, activity, supplier, facility/asset, scope, reporting period; zero/one/multiple; no arbitrary query; explicit tolerance/timezone.
- D-03 bounded Insight analytics: allowlisted dimensions/filters, bounded dates/results, org auth, provenance.
- D-04 Scope 3 Categories 1–15 baseline taxonomy, versioned; no arbitrary activity-string inference.
- D-05 supplier identity persistence through calculation lineage with governed confidence/approval + backfill policy; supplier analytics conditional on persistence.
- D-06 explicit primary/secondary provenance classification.
- D-07 dual Scope 2 location/market basis with method/instrument/factor hierarchy and versioning.
- D-08 Scope 1 decomposition taxonomy where applicable.
- D-09 deterministic reproducible variance definitions.
- D-10 aggregate → evidence drill-down before audit-grade aggregate answers.
- D-11 historical factor metadata for audit-grade explanations.
- D-12 separate governed Mode E concept answers.
- D-13 customer Insight primary v1; consultant/auditor separately governed.
- D-14 rate limiting required before scaling customer-facing analytics.
- D-15 version accounting methodologies/taxonomies; GHG Protocol primary corporate reference; ISO 14064-1 important.

Important: PO approval of a capability is not blanket implementation authorization. Each bounded package gets its own Cline authorization.

### Preflight
Permanent report:
`docs/architecture/CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PREFLIGHT-20260922.md`
Preflight final commit:
`c7cd9cc2ff56e288c830bb5d204118a06aa31104`
Preflight was read-only except for its report.

Preflight findings:
- Existing `EmissionLogRepository.aggregate(org, period, group_by)` supports scope/month/year/asset/facility.
- `aggregate_by_activity` and `aggregate_by_supplier` exist.
- Existing `list_snapshots` provides snapshot candidate fields.
- I3 currently has exactly four tools.
- I4 persistence constraints hard-code tool/status vocabulary, so new tool/state requires narrow migration.
- Discovery is currently UUID-oriented; no bounded date/amount/dimension discovery contract.
- No amount-tolerance semantics.
- Stored dates are calendar dates; timezone semantics must be explicit.
- Supplier IDs are not currently written through the normal application path.
- Facility/asset are not necessarily snapshot-native.
- Aggregate results lack sufficient identifiers for aggregate→evidence drill-down.
- Factor usage endpoints have an org-predicate exposure concern; it was explicitly not fixed by the preflight and is separately tracked.
- Rate-limit middleware exists but is not registered.
- Do not infer that the preflight fixed any of the above.

### Cline authorization just issued
Task:
`Insight Discovery, Aggregation, Provenance, Shared Evidence & Rate Limiting`

Authorized implementation includes:
1. Bounded Discovery:
   - date/date range
   - reporting year
   - CO2e amount + explicit tolerance
   - activity
   - scope
   - supplier
   - facility
   - asset
   - zero/one/multiple matches
   - no arbitrary querying.
2. Bounded Aggregation:
   - scope/month/year/activity/supplier/facility/asset
   - tenant scoped
   - bounded results
   - deterministic ordering
   - CO2e kg basis
   - no unsafe mixed-unit quantity aggregation.
3. Aggregate→calculation provenance:
   - deterministic contributing snapshot IDs
   - max 100 contributing snapshots per aggregate result/cell unless stricter existing limit.
4. Shared Source Evidence Viewer integration:
   - reuse existing viewer
   - no second viewer
   - preserve tenant/read-only/DM-6/signed URL/audit controls.
5. I3/I4 expansion:
   - explicit new tools/schemas/allowlists
   - I2 reauthorization remains authoritative
   - narrow migration for hard-coded I4 constraints.
6. `multiple_matches` as first-class I4 answer state; prefer not adding ToolStatus unless code proves required.
7. Bounded typed query-planning layer is allowed:
   - strict schema
   - allowlisted fields/operators
   - server validation
   - no SQL
   - no DB access by planner
   - no authorization decisions.
8. Rate limiting implemented now:
   - per user: 20 requests/minute, burst 5, max concurrency 2
   - per organization: 100 requests/minute, burst 20, max concurrency 10
   - server-controlled/configurable
   - before expensive Insight/provider work
   - HTTP 429 + Retry-After where supported
   - preserve/use `rate_limited` state
   - no bypass routes
   - shared deployment-safe mechanism; existing shared infrastructure preferred; DB-backed narrowly scoped fallback allowed; do not add Redis unless already used.
9. Comprehensive tests.
10. Permanent implementation report:
`docs/architecture/CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-IMPLEMENTATION-20260922.md`
11. Commit, push to `github/p8-release-reconciled`, verify clean/aligned, then STOP for OHD.

### Supplier rule in current authorization
Supplier is included deliberately but:
- no fabricated relationships;
- no LLM supplier inference;
- no uncontrolled historical backfill;
- use authoritative explicit supplier identity where available;
- otherwise bounded no_data/limitation and document it.
Do not silently redesign supplier data model.

### Explicitly OUT OF SCOPE for current implementation
- Scope 3 Categories 1–15 implementation
- Scope 2 market-based implementation
- Scope 1 decomposition implementation
- primary/secondary factor classification
- factor-history redesign
- variance/attribution engine
- supplier historical backfill
- RAG/concept-answer system
- consultant/auditor surfaces
- unrestricted NL database querying
- cross-tab analytics
- commercial billing/credits/overages/payment provider
- I7
- full I8
- production deployment.

### Cline next expected deliverable
Wait for Cline to return:
- implementation verdict;
- final commit SHA;
- push/alignment status;
- files/migrations;
- Discovery/Aggregation/Provenance details;
- Shared Viewer integration;
- rate-limit implementation;
- supplier limitation;
- tests;
- known limitations;
- permanent report path.

Then do NOT call it verified/closed. The next controlled action is an OHD independent verification prompt.

### Full Insight future workplan
The full Insight roadmap is broader than the current implementation package.

Recommended dependency order:
1. Current authorized Discovery/Aggregation/Provenance/Rate Limiting foundation.
2. OHD verification and PO closure.
3. Supplier persistence and governed supplier identity policy.
4. Scope 3 Categories 1–15 versioned taxonomy/data model.
5. Primary/secondary factor provenance.
6. Scope 1 decomposition.
7. Scope 2 location + market methods.
8. Aggregate→evidence drill-down hardening.
9. Variance/attribution.
10. Historical factor metadata.
11. Insight exposure of the deterministic capabilities.
12. Mode E governed concept answers.
13. Persona expansion (consultant/auditor) only after separate authorization.
14. Production readiness and controlled deployment only after I7/I8 gates.

Each future item requires its own PO decision + bounded Cline authorization + OHD verification + PO closure.

### I7 future workplan
I7 remains NOT AUTHORIZED / NOT READY.
Required decision package:
- retention durations by artifact/data class;
- deletion semantics;
- legal hold semantics;
- user/org deletion behavior;
- report/evidence/calculation retention;
- export policy;
- provider/privacy policy;
- audit-trail retention;
- acceptance criteria;
- implementation authorization.
Then Cline implementation → OHD verification → PO closure.

### I8 future workplan
I8 is not one implementation package.

I8-A technical production readiness areas:
- rate limiting (technical part now separately authorized in current Insight package);
- observability;
- provider resilience;
- deployment discipline;
- SLOs;
- backup/recovery;
- incident/runbook;
- security hardening.

I8-B commercial:
- plans;
- entitlements;
- usage metering;
- overages;
- provider cost allocation;
- billing failure;
- refunds/credits;
- payment provider;
- admin configurability.

I8-B remains NOT AUTHORIZED.

Full I8 requires a separate bounded PO authorization after prerequisites and factual system/provider review.

### Important unresolved/standing items
Cline inventory C-01..C-32 exists. Important:
- C-03 reporting/export COMPLETE inference from source_page.
- C-09 evidence_line_item resolvability.
- C-10 consultant/internal entry point.
- C-11 org_viewer rights.
- C-12 pagination.
- C-13..C-17 I7 prerequisites.
- C-18..C-24 I8 prerequisites.
- C-25 auditor/PE personas.
- C-26 rename/archive.
- C-27 regeneration/edit semantics.
- C-28 provider selection.
- C-29 I5 follow-ons.
- C-30 repo topology divergence.
- C-31 Master Spec stale status.
- C-32 durability of capability-level PO authorization records.

### Missing-chat caution
A prior conversation interval was lost between the I3 authorization and the OHD Source Evidence Viewer verification. Do not reconstruct missing exact PO wording as fact.
Evidence hierarchy:
1. exact original PO wording;
2. permanent repo PO record;
3. Cline/OHD report explicitly citing authorization;
4. git chronology;
5. reconstruction/inference.
If exact authorization is absent, say so.

### Resume instruction
When resuming this project from this file:
1. Inspect the current release checkout and git state.
2. Read the permanent reports named above.
3. Verify current HEAD/status before claiming any status.
4. Treat the current Cline authorization as the active implementation boundary until Cline completes.
5. Do not invent closure.
6. After Cline implementation, require OHD independent verification.
7. After OHD, PO decides closure.
8. Do not proceed to I7/I8/production without explicit new authorization.
