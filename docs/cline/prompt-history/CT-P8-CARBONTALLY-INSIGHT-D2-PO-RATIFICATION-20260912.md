# CT-P8-CARBONTALLY-INSIGHT-D2-PO-RATIFICATION-20260912

**Prompt ID:** `CT-P8-CARBONTALLY-INSIGHT-D2-PO-RATIFICATION-20260912`
**Date:** 2026-09-12
**Task purpose:** Formally record the Product Owner decisions for **CarbonTally Insight** (the
persistent conversational carbon-intelligence capability) following D1 discovery, Phase 8
reporting/product ratification, Phase 8 open-decision closure, and the Ask CarbonTally
persistence/auditability discovery.
**Type:** DOCUMENTATION / PO-RATIFICATION ONLY. No implementation authorised.
**Task status:** `COMPLETED — D2 PO RATIFIED`

## Repository State at Start

| Item | Value |
|---|---|
| Branch | `main` |
| Starting HEAD | `8608d13ea937ae5d90e5056a813ebdb6cf124806` |
| Relation to origin | 9 commits ahead of `origin/main`, **not pushed** |
| Pre-existing modified | 208 |
| Pre-existing untracked | 52 |
| Staged | 0 |

## Authoritative Inputs Reviewed Before Writing

| Document | Lines | What was taken from it |
|---|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_ASK_CARBONTALLY_PERSISTENT_CONVERSATION_AND_AI_AUDITABILITY_DISCOVERY_20260912.md` | 1990 | Primary evidence base: repository findings, reuse/new-build classification, three-layer recommendation, R-1, staging, `[UNVERIFIED]` items |
| `docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` | 633 | Personas, tool registry tool contract, injection defence, PE document boundary, provider-neutral design; **the superseded §9/§10.2 wording (R-1)** |
| `docs/architecture/CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` | 1751 | §29 AI-assisted narrative boundary + hard prohibitions + required mechanism; §30 **Ask CarbonTally Dependency** (report-state exposure, assistant rules 1–6, recommended tool contract); §35 S0–S8 sequence |
| `docs/architecture/CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md` | 1273 | §6 assurance positioning + non-claims; §7 auditor/reviewer boundary (allowlist/denylist); §18 Ask CarbonTally Boundary (already-ratified separate domain, LLM prohibitions, answer-quality states); §19 AI narrative boundary; §22 PO decision register; §24 open PO decisions (A-PE, A-AUD, A-RLS, …) |
| `docs/architecture/CARBONTALLY_PHASE8_OPEN_DECISION_CLOSURE_AND_IMPLEMENTATION_AUTHORISATION_20260912.md` | 1282 | §2 ratified baseline (one aggregation layer, one report engine, one audit ledger, separate conversational domains); §4/§5/§6 RLS correction + auditor + PE reviews; §7 S1 boundary; §14 authorisation matrix; §15 S1 status |

## Consistency Check Performed (before ratification)

Every D2 decision was checked against the inputs above. **No material conflict was found.**

* The D1 "separate conversational domain" finding is **independently already ratified** in
  `PRODUCT_AND_REPORT_RATIFICATION` §18.1 ("the two must **not** share tables, routes or services.
  A chat-*like* UI is permitted; a chat *data model* is not").
* The D1 LLM prohibitions are already ratified in §18.3, §19.2 and `REPORTING_LIFECYCLE_SPEC`
  §29.2.
* The D1 deterministic-first recommendation is already ratified in `REPORTING_LIFECYCLE_SPEC`
  §29.4 ("deterministic template first") and is extended to Insight answers.
* The D1 audit-package recommendation matches the package's existing `not_assurance` contract.
* The only conflict found is the **R-1** wording issue, which is **recorded, not resolved**.

**No stop condition was triggered.**

## One Clarification Recorded (not silently resolved)

**TERM-1.** The D2 prompt's heading reads **"Private Equity"** for PE. CarbonTally's ratified
architecture uses **PE = Processing Entity** (AGENTS.md §8; `PRODUCT_AND_REPORT_RATIFICATION`
§16 "PE Admin Reporting"). The **substance** of the decision (no PE Insight access; no exposure of
customer Insight conversations through PE portfolio reporting) maps onto **Processing Entity** in
this repository's established usage and is recorded that way. If "Private Equity" was intended as a
distinct investor-side persona, that persona does not exist in the ratified actor model and would
require a separate PO decision. Recorded as `PO CLARIFICATION REQUIRED (non-blocking for I1)` —
**not** invented either way.

## Prompt Requirements Recorded (faithful record of the D2 instruction set)

The task instructed the following, all of which are implemented in the primary document:

1. **Bounded documentation/ratification task only** — no application code, migration, RLS change,
   API, frontend, AI provider integration, billing change or production change.
2. **Preserve all pre-existing dirty/untracked work** — no reset, clean, stash or checkout; no
   staging of unrelated files.
3. **Read the referenced documents before updating** — done (§ "Authoritative Inputs Reviewed").
4. **Naming decision** — `CarbonTally Insight` replaces the customer-facing working name
   "Ask CarbonTally"; `ask_*` remains the technical domain terminology; no rename/migration;
   mandatory trademark/clearance caveat (not represented as cleared); "CarbonTally Copilot" and
   "Carbon Insights" expressly excluded.
5. **Ratify the core product decision** — Insight is a first-class, evidence-backed analytical
   capability, not a generic chatbot; the conceptual flow is
   user → Insight → intent → controlled tools → authorization/scope/RLS/domain → authoritative data
   → structured result → AI explanation → answer + evidence/references; the exact tool catalogue
   must **not** be invented.
6. **Ratify persistence (YES)** — with the binding invariant that conversation history is **NOT**
   authoritative carbon data (never the source of truth for emissions, calculations, factors,
   evidence, provenance, report facts or authorization); historical answers never trusted as
   authoritative.
7. **Ratify the separate-domain decision (YES)** — no reuse of Human↔Human messaging tables; no
   shared message semantics, persistence model, audit interpretation or authorization assumptions;
   explicitly acknowledge the discovery visibility finding.
8. **Ratify the three-layer model** — conversation history / AI interaction record / canonical
   audit event; do not turn conversation history into the audit trail; do not duplicate
   authoritative records; reconstruction chain question → authorized tool call → authoritative
   result → reference/provenance → AI explanation.
9. **Ratify the authorization rule** — conversation persistence NEVER grants authorization;
   re-authorise every read and every future tool invocation against current permissions/scope;
   historical context cannot grant cross-org/entity/product access; cross-tenant leakage
   categorically prohibited; stored references are pointers, not grants; the LLM is never an
   authorization boundary.
10. **Ratify the initial scope** — first persona Customer user; first surface Customer workspace;
    initial visibility private to the creator; no automatic consultant/staff/auditor/admin access;
    Owner/Admin shared visibility remains a future decision; do not implement shared visibility.
11. **Consultant / staff / auditor / PE** — all DEFERRED; auditor assurance boundary unchanged
    (not an independent assurance/certification body; scoped authorisation later); PE receives no
    Insight; no exposure through PE portfolio reporting.
12. **AI safety and authority boundary** — the LLM must not calculate authoritative values, select
    factors as the authoritative mechanism, invent evidence/provenance, bypass authorization, have
    unrestricted database or vector access, or be treated as the system of record; deterministic
    services remain authoritative.
13. **Deterministic-first** — deterministic services give the authoritative result; the LLM
    explains; provider unavailability must yield a deterministic result/status rather than a
    fabricated answer; distinguish `zero` / `no_data` / `not_authorized` / `provider_unavailable`;
    do not collapse "no data" into zero; exact taxonomy may be finalised in implementation.
14. **RAG IS DEFERRED** — no vector DBs, embeddings pipeline, unrestricted document/database
    retrieval, generic RAG framework or enterprise corpus; not permanently rejected; any future RAG
    must be authorization-first, scope-aware, allowlisted, provenance-aware, tenant-safe,
    injection-resistant and separate from authoritative calculations; controlled tools > RAG for
    authoritative numerical/structured questions.
15. **LangChain DEFERRED / NOT REQUIRED** — reuse `backend/infra/llm_client.py` and
    `backend/infra/ai_runtime.py` and the canonical provider abstraction; a future framework only
    if a concrete requirement materially improves safety/maintainability/orchestration/evaluation/
    observability/reliability without undermining authorization/audit; no framework migration.
16. **AI provider boundary** — existing abstraction authoritative; do not bind to a specific
    provider; no new parallel abstraction; carry forward the `LLMClient.complete()` usage/cost gap
    without silently solving it.

17. **Context** — continuity permitted; old answers never authoritative; historical messages
    re-authorized; only relevant/minimal context to a provider; do not blindly send the whole
    history; compaction/summarisation thresholds OPEN; summaries must not become authoritative
    facts.
18. **Prompt injection / conversation poisoning** — ratify the threat model; persisted user content
    is untrusted input; historical instructions are never system/developer authority.
19. **Tool-call provenance** — reconstructable and attributable; appropriate references/pointers;
    do not duplicate authoritative datasets; deterministic hashes/result references where
    appropriate; exact schema deferred.
20. **Reporting relationship** — Insight may assist with report interpretation, evidence discovery,
    preparation, narrative and investigation, but **MUST NOT bypass the ratified reporting
    lifecycle**; AI narrative remains candidate-only; AI cannot approve, finalize, alter facts,
    calculations or factor provenance, or bypass versioning/approval/frozen finals.
21. **Audit package** — Insight conversations are **NOT** included in the standard audit package by
    default; do not modify the audit package.
22. **Privacy / retention / deletion / export remain OPEN** — do not invent retention period,
    deletion model, deletion rights, export, provider retention/training, residency, subprocessors,
    PII handling or notices; record them as explicit follow-ups; the architecture must allow the
    controls later.
23. **Billing / AI allowance remains OPEN** — reuse existing infrastructure where appropriate; do
    not invent credits, token prices, entitlements, quotas, overage pricing or provider cost
    policy.
24. **Dormant AI structures** — do not automatically reuse or delete the dormant AI content-history
    structure; record a later repository-driven decision (new domain / extension / another bounded
    structure); no migration.
25. **Staging ratified** — D1 (complete) → D2 (this task) → I1…I8; RAG, consultant access, auditor
    access, PE Insight, broad staff access and advanced retrieval remain outside the initial
    foundation.
26. **I1 authorisation boundary** — this D2 task authorises **I1 — Persistent CarbonTally Insight
    Foundation** only, at the next implementation step, subject to a separate implementation prompt;
    I1 may include conversation + message persistence, initial repository/domain layer, minimal
    create/list/read, organization scoping, explicit RLS design, indexes/constraints and the basic
    persistence API foundation; I1 must not expand into I2–I8, report lifecycle work, RAG,
    LangChain, or consultant/auditor/PE access. **A separate prompt must authorise I1.**
27. **Report S1 remains separate** — do not combine Insight with report S1; do not modify report
    lifecycle code/schema; `report_versions.is_current` remains owned by report S1.
28. **R-1 acknowledged** — the canonical AI architecture's session-bounded / per-session-logging
    wording is superseded by the persistence decision; **do not silently rewrite** it; record it as
    a documentation reconciliation item for a later controlled update.
29. **Deliverables** — the primary ratification document (28 required sections) and this prompt
    history.
30. **Final status** — must conclude with
    `D2 PO RATIFIED — CARBONTALLY INSIGHT ARCHITECTURE READY FOR I1 IMPLEMENTATION AUTHORISATION`,
    while explicitly stating that I1 implementation is not performed by this task.
31. **Git** — a single documentation-only commit; do not push; do not modify or commit unrelated
    pre-existing work.

## Deliverables

* `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` —
  primary ratification document. Contains all 28 required sections:
  1 Purpose · 2 Source/discovery documents · 3 Product naming decision · 4 CarbonTally Insight
  definition · 5 Persistence decision · 6 Separate-domain decision · 7 Three-layer model ·
  8 Authorization boundary · 9 Initial persona/surface/visibility · 10 Consultant/staff/auditor/PE
  boundaries · 11 Deterministic-first · 12 RAG deferred · 13 LangChain deferred/not required ·
  14 AI provider boundary · 15 Context rules · 16 Threat model · 17 Tool provenance ·
  18 Reporting relationship · 19 Audit-package boundary · 20 Privacy/retention/export open ·
  21 Billing/allowance open · 22 Dormant AI table decision · 23 Staged plan · 24 I1 authorization
  boundary · 25 R-1 acknowledgement · 26 Explicit non-goals · 27 PO ratification summary ·
  28 Final status.
* `docs/cline/prompt-history/CT-P8-CARBONTALLY-INSIGHT-D2-PO-RATIFICATION-20260912.md` — this file.

## Verification Performed

| # | Requirement | Result |
|---|---|---|
| 1 | Both documentation files exist | ✔ |
| 2 | No application code changed | ✔ |
| 3 | No migration created or changed | ✔ |
| 4 | No RLS policy changed | ✔ |
| 5 | No API / frontend / provider / billing code changed | ✔ |
| 6 | No production system touched | ✔ |
| 7 | Pre-existing modified/untracked files preserved | ✔ (208 / 52 before and after) |
| 8 | Final `git status` shown | ✔ (below) |
| 9 | Exact commit reported | ✔ (below) |

A scan for credentials, API keys, tokens and signed URLs in both new files found none.

## Files Changed

| File | Change |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` | **created** |
| `docs/cline/prompt-history/CT-P8-CARBONTALLY-INSIGHT-D2-PO-RATIFICATION-20260912.md` | **created** |

No other file was created, modified, or deleted. `AGENTS.md`, the canonical AI architecture
document, the roadmap, and all previously ratified Phase 8 documents were read but **not** edited.

## Git

| Item | Value |
|---|---|
| Starting HEAD | `8608d13ea937ae5d90e5056a813ebdb6cf124806` |
| Commit message | `docs: ratify CarbonTally Insight architecture and authorize I1` |
| Commit scope | The two documentation files above only |
| Push | **not pushed** |
| Unrelated work | preserved — untouched, unstaged, uncommitted |

## Implementation Statement

**No implementation was performed.** No I1 work, no RAG, no LangChain, no AI tools, no provider
integration, no frontend, no billing, no reporting-lifecycle change, no production access.

## Final Status

**`D2 PO RATIFIED — CARBONTALLY INSIGHT ARCHITECTURE READY FOR I1 IMPLEMENTATION AUTHORISATION`**

I1 implementation is **not** performed by this task. The next step is a separate, bounded
**I1 — Persistent CarbonTally Insight Foundation** implementation prompt.
