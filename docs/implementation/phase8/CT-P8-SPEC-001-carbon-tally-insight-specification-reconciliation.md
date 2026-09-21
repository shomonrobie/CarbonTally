# CT-P8-SPEC-001 — CarbonTally Insight Specification Discovery & Reconciliation

## A. Metadata

| Field | Value |
| --- | --- |
| Prompt ID | `CT-P8-SPEC-001` (read-only specification discovery; **no implementation**) |
| Date | 2026-09-21 |
| Branch | `p8-release-reconciled` |
| Starting HEAD | `c5fbbea26ddb879685cad56a46ecef8f68089bab` — *docs: record QA-AI-001 commit and push status in the verification report* |
| Working tree | **CLEAN** (no unrelated user changes) |
| Remote state | `github` aligned `0 0`; local **25 commits ahead of `origin/p8-release-reconciled`** (pre-existing, unaltered) |
| Verifier/implementer | Cline |
| Path convention | Prompt mandates `docs/implementation/phase8/`; historical Phase-8 spec docs live in `docs/architecture/` and no `docs/implementation/` directory existed. The mandated path was used; recorded here. |

## B. Search methodology

Read-only repository-wide search: filename discovery (`-iname '*insight*'`, `'*ask*carbon*'`), content grep over `*.md`, `*.py`, `*.js`, `*.jsx`, `*.sql` (excluding `node_modules`, `backend/.venv`), migration inspection, and targeted reads of each candidate document's status line, headings and cited sections.

Terms searched (prompt §4): `CarbonTally Insight`, `CarbonTallyInsight`, `Ask CarbonTally`, `Insight`, `ask_`, `AI Assistant`; `Phase 8`, `I1`–`I8`, `D1`, `D2`, persistent conversation(s), conversation persistence, AI auditability, AI interaction; `natural language`, emissions question/query, authoritative data, `deterministic`, `no_data`, `insufficient_data`, `ungrounded`, `needs_clarification`, tenant isolation, organization scope, conversation, messages, interaction; `ask_conversations`, `ask_messages`, `ask_interactions`, `ai_content_history`, `llm_client`, tool registry, provider, prompt injection, `RAG`, evidence, `result_hash`, `carbontally_insight`.

Excluded by instruction: investor feature audit; billing/reporting/export/extraction/factor/messaging audits; any fix or implementation.

## C. Relevant documents

| Document | Classification | Date | Authority | Relationship |
| --- | --- | --- | --- | --- |
| `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` (1,555 lines) | **AUTHORITATIVE / RATIFIED** | 2026-09-12 | **Product Owner** — L8: `D2 PO RATIFIED — CARBONTALLY INSIGHT ARCHITECTURE READY FOR I1 IMPLEMENTATION AUTHORISATION`; Rev 2 = terminology correction | **Primary specification**; supersedes D1's `ask_*` naming for new implementation (§3.2/§3.8) and older persistence wording (§25.2) |
| `docs/cline/prompt-history/CT-P8-CARBONTALLY-INSIGHT-D2-PO-RATIFICATION-20260912.md` (229) | ARCHITECTURE / DESIGN (authorising task record) | 2026-09-12 | *"DOCUMENTATION / PO-RATIFICATION ONLY. No implementation authorised."* | Corroborates D2 authority and no-implementation scope |
| `docs/cline/prompt-history/CT-P8-CARBONTALLY-INSIGHT-D2-TERM-CORRECTION-20260912.md` (161) | ARCHITECTURE / DESIGN (task record) | 2026-09-12 | Makes **CarbonTally Insight** canonical for new implementation, *"superseding D1's `ask_*` proposal"* | Explains D2 Rev 2 |
| `docs/architecture/CARBONTALLY_PHASE8_ASK_CARBONTALLY_PERSISTENT_CONVERSATION_AND_AI_AUDITABILITY_DISCOVERY_20260912.md` (1,990) | **DISCOVERY** (D1) | 2026-09-12 | Self-declared *"NOT ratifiable as implementation authorisation"* | Historical source; `ask_*` naming superseded where D2 rules |
| `docs/cline/prompt-history/CT-P8-ASK-CARBONTALLY-PERSISTENCE-DISCOVERY-20260912-013.md` (190) | DISCOVERY (task record) | 2026-09-12 | The "previously known" discovery doc | Task record of D1 |
| `docs/verification/QA-AI-001-carbon-tally-insight-natural-language-emissions-verification.md` (591) | **VERIFICATION REPORT** (independent OHD) | 2026-09-21 | Verification at HEAD `770046a`; verdict **`NOT IMPLEMENTED`** | Current-state corroboration; quotes D2 sections |
| `docs/cline/reports/CT-P8-CURRENT-STATE-RECOVERY-20260913-023.md` | IMPLEMENTATION REPORT (state) | 2026-09-13 | Repository record | §275 *"PO-RATIFIED; I1 AUTHORISATION AMBIGUOUS (PO CONFIRMATION REQUIRED); NOT IMPLEMENTED"* |
| `docs/cline/reports/CT-P8-REST-PLAN-20260913-027.md` | IMPLEMENTATION REPORT (plan) | 2026-09-13 | Repository record | §24 I1 authorisation ambiguity → **PO clarification required** |
| `docs/architecture/CARBONTALLY_PHASE9_SYSTEM_RUNTIME_AND_OPERATIONAL_INTELLIGENCE_BASELINE_20260912.md` | ARCHITECTURE / DESIGN | 2026-09-12 | Phase 9 baseline | L407 Phase 8 owns the Insight product; L781 Insight persistence governed by Phase 8 → **no supersession** |
| `docs/architecture/CARBONTALLY_PHASE8X_OPERATIONAL_INTELLIGENCE_DISCOVERY_AND_IMPLEMENTATION_BOUNDARY_20260912.md` | ARCHITECTURE / DESIGN | 2026-09-12 | Phase 8-X boundary | L86 explicitly *not* a replacement for Insight → no supersession |
| `docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` | **SUPERSEDED (in part)** | older | Non-PO note | D2 §25.2 supersedes its session-bounded persistence wording |
| `supabase/migrations/00000000000000_init_schema.sql` L1041 `CREATE TABLE public.ai_content_history`; listed in `20260925000000_p8_rls_4b_group1_enablement.sql` L80 | HISTORICAL / SCHEMA ARTIFACT | — | Legacy schema | Dormant structure of D2 §22.1; disposition **OPEN** (§22.5 → I3/I4) |

## D. Authoritative specification conclusion

**FINAL SPECIFICATION FOUND** — a single ratified document: `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md`.

`DOCUMENTED FACT` basis: status line L8 = `D2 PO RATIFIED — CARBONTALLY INSIGHT ARCHITECTURE READY FOR I1 IMPLEMENTATION AUTHORISATION`; the PO task records state *"DOCUMENTATION / PO-RATIFICATION ONLY"*; Rev 2 leaves §5–§24 and §27 *"exactly as ratified"* (L230); no later document supersedes it. Non-authoritative for implementation: D1 discovery (proposal), QA-AI-001 (state verification), the two 2026-09-13 reports (records).

## E. CarbonTally Insight current specification summary (source-supported only)

| Ratified position | Source |
| --- | --- |
| Product name **CarbonTally Insight**; canonical identifiers `carbontally_insight_*` / `CarbonTallyInsight*` for **all new implementation from I1 onward** | D2 §3.1, §3.2, §3.2.1, §3.8 |
| **Conversations are persisted** (`YES`) | D2 §5.1 |
| **Separate conversational domain** — must **not** reuse the human messaging tables | D2 §6.1, §6.2, §6.4 |
| **Three-layer persistence**: Layer 1 conversation history; Layer 2 AI interaction record; Layer 3 canonical audit event. Layer 1 at **I1**; Layer 2 + audit at **I4**; exact schema deferred | D2 §7.1, §7.3, §7.5 |
| **Authorization**: every read re-authorised; stored references are not grants; revocation semantics; **the LLM is never an authorization boundary** | D2 §8.1–§8.6, §8.8 |
| Initial persona/surface: authenticated **customer organisation**; **creator-private** visibility; consultant/staff/auditor/PE **DEFERRED** | D2 §9.1–§9.3, §10.1–§10.4 |
| **Deterministic-first**: authoritative results from structured data + deterministic domain services; LLM may only *explain*; provider outage degrades safely (never a wrong number) | D2 §11.1–§11.3 |
| Answer states **MUST** distinguish at minimum `zero`, `no_data`, `not_authorized`, `provider_unavailable`; **do not collapse "no data" into zero**; exact vocabulary deferred | D2 §11.4–§11.6 |
| **RAG deferred**; **LangChain deferred**; **tool catalogue explicitly not decided**; representative questions **illustrative only** | D2 §4.3, §4.4, §12, §13 |
| Privacy/retention/export **OPEN** (I7); billing/allowance **OPEN** (I8); dormant-AI-table disposition **OPEN** (I3/I4) | D2 §20, §21, §22.5 |
| Provider boundary, context rules, threat model, tool-call provenance, reporting relationship, audit-package boundary | D2 §14–§19 |

## F. I1 specification (exact current requirements)

**Name (D2 §23.2):** `I1 — Persistent CarbonTally Insight Foundation`.

**I1 MAY include — “subject to a separate implementation prompt” (D2 §24.2, verbatim list):**

* dedicated Insight conversation persistence;
* dedicated Insight message persistence;
* initial repository / domain layer;
* minimal create / list / read functionality;
* organization scoping;
* explicit RLS design;
* appropriate indexes / constraints;
* the basic API foundation required for persistence.

**Stage row (D2 §23.2):** *“Dedicated Insight conversation + message persistence, initial repository/domain layer, minimal create/list/read, organization scoping, explicit RLS design, indexes/constraints, basic API foundation for persistence (§24)”*.

**Binding constraints on I1 (D2 §24.5):** three-layer concept (§7) — **I1 builds Layer 1 only**; the authorization rule (§8) — *every read re-authorised*, RLS/scope design explicit, and the creator-private visibility model (§9.2) **must be enforceable**; the naming decision (§3) — canonical `carbontally_insight_*` terminology (*“I1 and later stages **must** create `carbontally_insight_*` objects, not `ask_*` objects”*, L223); the separate-domain decision (§6) — **no reuse of human messaging tables**; the privacy-design requirement (§20.3) — retention/deletion must be **introducible later**; the non-goals (§26).

**RLS (D2 §24.6):** because the dynamic tenant-policy mechanism only covers tables carrying an organisation key, **I1 must define its RLS posture explicitly** and not repeat that gap (`A-RLS` remains a report-stream item).

**Authorization mechanics (D2 §24.4, normative):** *"A separate prompt must authorise I1 implementation."* · *"This D2 prompt itself authorises documentation/ratification only — not implementation."* · *"If, during I1, a requirement is discovered that belongs to I2–I8, it is **recorded**, not implemented."*

**Gating (D2 §23.5):** *"Each stage requires **its own** authorisation. No stage may begin merely because the previous stage completed."*

**Minimum I1 “complete” (no inference):** Layer-1 **Insight conversation + message persistence** under canonical `carbontally_insight_*` naming, in a **separate domain** from human messaging, with organisation scoping, an explicitly designed RLS posture, indexes/constraints, a minimal create/list/read repository/domain layer and the basic persistence API foundation — with authorization re-checked on every read and the creator-private model *expressible* in the design. `DOCUMENTED FACT` (D2 §23.2, §24.2, §24.5, §24.6). Field-level schema is **explicitly deferred** (§7.5) and **not ratified**.

## G. I2–I8 specification summary (D2 §23.1/§23.2)

| Stage | Name | Purpose (condensed) | Deps | Authorization | Status |
| --- | --- | --- | --- | --- | --- |
| I1 | Persistent CarbonTally Insight Foundation | Layer-1 conversation + message persistence; repo/domain layer; minimal create/list/read; org scoping; explicit RLS; indexes/constraints; persistence API foundation | D2 (complete) | **Separate prompt required** (§24.4); none exists in the repo | Documented, **not implemented** |
| I2 | Authorization and visibility | Apply creator-private visibility; complete authorization coverage; ALLOW/DENY verification | I1 | Not authorized | Proposed |
| I3 | Controlled read-only tools | Intent classification; tool registry; initial read-only tools; references; deterministic path **without a provider** | I1, I2 | Not authorized | Proposed |
| I4 | AI interaction records + canonical audit integration | Layer-2 interaction write path; canonical audit event; dormant-AI-table question (§22) | I1–I3 | Not authorized | Proposed |
| I5 | Context management | Bounded context; compaction/summarization (§15.2) | I1–I4 | Not authorized | Proposed |
| I6 | Insight UI | Authenticated customer workspace (*“chat-*like* UI permitted; chat data model is not”*) | I1–I5 | Not authorized | Proposed |
| I7 | Privacy / retention / export | §20 open items | I1–I6 | Not authorized | Proposed |
| I8 | Billing / production hardening | §21 open items; usage/cost capture gap (§14.4); rate limiting; production readiness | I1–I7 | Not authorized | Proposed |

Deferred beyond the foundation (§23.3): RAG (§12); consultant (§10.1); auditor (§10.3); PE (§10.4); broad staff (§10.2); LangChain (§13); AI-assisted report narrative (`REPORTING_LIFECYCLE_SPEC` §35 S8). Streams must not be conflated (§23.4). **Staged authorization (§10):** the Phase-8 Insight PO decision does **not** authorise I1–I8 as one batch; §23.5 requires per-stage authorisation and §24.4 a separate I1 prompt — whether commit `d91ace5` already satisfies this is **contested** (C-1).

## H. Product capabilities (explicitly supported only)

`DOCUMENTED FACT`: D2 §4.3 lists representative questions **“illustrative only”**; §4.4 states the **tool catalogue is explicitly not decided**; §4.5 defines what Insight is not. Consequently **no** prompt-listed capability is a ratified requirement: “CO₂ in January 2024” (period interpretation), “why did emissions increase”, trend/comparison, “Scope 1 emissions”, “what factor was used”, “explain this calculation”, “show the evidence”, drill-down/follow-up → **Not ratified** (illustrative; capability catalogue undecided; acceptance criteria none). “Which documents are awaiting review?” → **`NOT FOUND IN CURRENT SPEC`**. Report summarisation → **deferred to a different stream** (§18, §23.3).

## I. Auditability requirements (specified only)

* Three layers: Layer 2 **AI interaction record**, Layer 3 **canonical audit event**; integrated at **I4**, not I1 (§7.1, §7.3, §23.2).
* Reconstruction chain conversation → interaction → audit event (normative) (§7.3–§7.4).
* **Tool-call provenance** (§17; exact schema deferred, L974); audit-package boundary (§19); reporting relationship (§18).
* Dormant `public.ai_content_history` must **not** be auto-reused or deleted; one bounded home for AI interaction/cost/rating data chosen at **I3/I4** (§22.1–§22.5).
* `result_hash`, evidence/snapshot/report-version references and model/provider attribution as **I1** requirements → `NOT FOUND IN CURRENT SPEC`.

## J. Security requirements (specified only)

* Every read **re-authorised**; stored references are not grants (§8.1–§8.4).
* **The LLM is never an authorization boundary** (§8.6); required implementation shape (§8.5); revocation semantics (§8.8).
* **Creator-private** visibility within the customer organisation and its RLS consequences (§9.2, §9.3, §9.6).
* **Separate domain** — no reuse of human messaging tables/policies (§6.2). Threat model incl. prompt injection (§16).
* **Explicit RLS posture** required; must not repeat the organisation-key coverage gap; `A-RLS` stays a report-stream item (§24.6).
* Raw-document exposure, secrets handling, unrestricted RAG → `NOT FOUND IN CURRENT SPEC` at I1 level (RAG deferred, §12).

## K. Persistence requirements (specified only)

Persistent conversations **YES** (§5.1); dedicated conversation **and** message persistence (§23.2, §24.2); **organisation scoping** (§23.2, §24.2, §24.5); canonical `carbontally_insight_*` naming (§3.2.1, §3.4.1, §3.8 L223); explicit **RLS** + indexes/constraints + minimal create/list/read + basic persistence API (§24.2, §24.6); retention/deletion **introducible later** (§24.5, §20.3). Message ordering, lifecycle/status vocabulary, timestamps, actor/ownership fields, archival/soft deletion → `NOT FOUND IN CURRENT SPEC` (schema deferred §7.5; retention/export at I7).

## L. Explicit I1 exclusions

§24.3: I2 authorization beyond the ratified initial scope; I3 tool execution; I4 AI interaction/audit; I5 context orchestration; I6 frontend; I7 retention/export; I8 billing/provider production; report-lifecycle changes; RAG; LangChain; consultant, auditor, PE access. Also: §23.3 deferrals; §11.6 frozen status vocabulary (enumeration deferred); §22 dormant-AI-table disposition (I3/I4); §20/§21 open items (I7/I8).

## M. Conflict register

**C-1 — I1 implementation authorisation**
Documents: D2 §24.4 + status L8 · commit `d91ace5` subject · `CT-P8-REST-PLAN-20260913-027.md` §24 · `CT-P8-CURRENT-STATE-RECOVERY-20260913-023.md` §275 · QA-AI-001 §3.
Earlier position: D2 status says *“READY FOR I1 IMPLEMENTATION AUTHORISATION”*; §24.4 — *“A separate prompt must authorise I1 implementation”* and *“This D2 prompt itself authorises documentation/ratification only — not implementation.”*
Later position: a commit subject asserts I1 authorisation; two later repository reports record it as **AMBIGUOUS** and requiring PO clarification; the separating prompt `CT-P8-I1-INSIGHT-PERSISTENCE-20260921-001` is **absent from the repository** (`grep -rl` → no matches).
Evidence of authority: PO-ratified document (explicit) vs commit subject (non-normative) vs records.
Current interpretation: `AMBIGUOUS`. **PO DECISION REQUIRED** — the gate for any I1 work.

**C-2 — `Ask CarbonTally`/`ask_*` vs `CarbonTally Insight`/`carbontally_insight_*`**
Earlier: D1 discovery §10.1 proposed `ask_*`. Later: D2 Rev 2 §3.2/§3.2.1/§3.8 (L223) — new implementation **must** use `carbontally_insight_*`; existing `ask_*` need not be renamed; the term-correction task explicitly *"supersed[es] D1's `ask_*` proposal"*. Resolution: **RESOLVED by later authority** (no code exists to rename).

**C-3 — Session-bounded vs persistent conversations**
Earlier: `docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` (short-lived sessions; per-conversation-event logging). Later: D2 §25.1–§25.2 — *“The new PO decision supersedes that product-level persistence direction.”* → **SUPERSEDED**; no PO decision needed, but authoring must follow D2.

**C-4 — Dormant `public.ai_content_history`**
Present in schema (`00000000000000_init_schema.sql` L1041; RLS list `20260925000000_p8_rls_4b_group1_enablement.sql` L80), unreferenced by code. D2 §22.2 — *“Do NOT automatically reuse or delete it. No migration is authorised now.”*; options A/B/C recorded; status `OPEN — implementation decision at I3/I4` ⇒ **not an I1 blocker**, but I1 must neither reuse nor replace it.

**C-5 — Public assistant vs authenticated Insight**
D2 §6 (separate domain) and AGENTS.md §29 are consistent (`CONFIRMED CURRENT`). QA-AI-001 `QA-AI-001-D2` (Low — FAQ assistant answers an account-specific question with an unrelated FAQ answer) is a public-assistant observation, **not** an Insight specification conflict.

## N. Current implementation cross-check

| Check | Result | Label |
| --- | --- | --- |
| `carbontally_insight_*` / `ask_*` objects in migrations, backend, frontend | **none** | `CODE OBSERVATION` |
| Insight-specific migrations (`grep -i 'insight\|ask\|ai_'` on `supabase/migrations`) | **none** | `CODE OBSERVATION` |
| `ai_content_history` | **exists, dormant** (`init_schema.sql` L1041; listed for RLS L80); no code references | `CODE OBSERVATION` |
| Insight backend routes/services/modules | **none** (matches for `insight`/`ask_` were incidental substrings, e.g. `task_`) | `CODE OBSERVATION` |
| Insight frontend routes/components | **none**; only the public `frontend/src/public/assistant/AssistantWidget.jsx` exists | `CODE OBSERVATION` |
| Independent verification | QA-AI-001 verdict `NOT IMPLEMENTED`; 7× HTTP 404; 575-path OpenAPI with no ask/insight path; no frontend route | `VERIFICATION REPORT` |

**Classification: `SPECIFICATION ONLY`** — no Insight-domain implementation exists to reconcile.

## O. Historical-claim reconciliation

| Claim | Source | Evidence | Verdict |
| --- | --- | --- | --- |
| “Ratify … architecture **and authorize I1**” | commit `d91ace5` subject | D2 L8 + §24.4 require a separate prompt; none exists | **Not substantiated** → C-1 |
| *“PO-RATIFIED; I1 AUTHORISATION AMBIGUOUS …; NOT IMPLEMENTED”* | state-recovery report §275 | corroborated by source greps | **Consistent with current state** |
| *“Insight I1 authorisation is ambiguous … PO clarification required”* | REST plan §24 | corroborated | **Consistent** |
| Insight NL Q&A implemented / verified | *(no such claim found)* | QA-AI-001 `NOT IMPLEMENTED`; no objects/routes/UI | **No claim to reconcile** |

`INFERENCE`: design exists (D2, ratified); implementation does **not** exist; independent verification exists and agrees. **No document contradicts QA-AI-001.**

## P. Open PO decisions

1. **I1 authorisation mechanics (blocking)** — confirm I1 authorisation or issue/enable the separate I1 prompt (`CT-P8-I1-INSIGHT-PERSISTENCE-20260921-001` absent from the repository) per D2 §24.4.
2. Confirm the Phase-8 Insight decision is **not** one-batch authorisation of I1–I8 (D2 §23.5).
3. Capability/tool catalogue (D2 §4.4) — needed before I3, not I1.
4. Status-vocabulary freeze (D2 §11.6) — not needed for I1.
5. Dormant-AI-table disposition (D2 §22.5) — I3/I4.
6. Privacy/retention/export (§20, I7) and billing/allowance (§21, I8).

## Q. Recommended next action

**Another PO decision is required before I1 implementation.** D2 §24.4 makes a separate authorising prompt normative; that prompt is not in the repository; and a commit subject plus two repository records leave I1 authorisation `AMBIGUOUS`. Once authorised, I1's ratified content (Layer-1 persistence under `carbontally_insight_*`, organisation scoping, explicit RLS posture, minimal create/list/read + persistence API foundation) is clear; the field-level schema is to be designed **within** the ratified constraints (§7.5). No implementation was started and no code, schema, configuration, test or data was changed by this task.

```text
# CT-P8-SPEC-001 FINAL VERDICT

Specification status:
FOUND

Authoritative specification:
docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md

I1 specification:
CLEAR (scope, naming, constraints, exclusions and authorisation mechanics are explicit; field-level schema deliberately deferred by D2 §7.5)

I1 implementation authorization:
AMBIGUOUS

I1 implementation started:
NO

I2–I8 implementation started:
NO

Current Insight implementation status:
SPECIFICATION ONLY

Conflicts:
C-1 I1 implementation authorisation — D2 §24.4 requires a separate prompt while commit d91ace5 claims authorisation and two repository reports record ambiguity; the I1 prompt is absent from the repository — PO DECISION REQUIRED;
C-2 ask_* vs carbontally_insight_* naming — RESOLVED by D2 Rev 2 §3.8;
C-3 session-bounded vs persistent conversations — SUPERSEDED by D2 §25.2;
C-4 dormant public.ai_content_history disposition — OPEN at I3/I4 (D2 §22.5), not an I1 blocker;
C-5 public assistant vs authenticated Insight — CONFIRMED separation (D2 §6; AGENTS.md §29)

PO decisions required:
1. Confirm I1 authorisation, or issue the separate I1 implementation prompt required by D2 §24.4;
2. Confirm the Phase-8 Insight decision is not one-batch authorisation of I1–I8;
3. Later-stage items: capability/tool catalogue (§4.4), status vocabulary (§11.6), dormant AI table (§22.5), privacy/retention/export (§20), billing/allowance (§21)

Permanent report:
docs/implementation/phase8/CT-P8-SPEC-001-carbon-tally-insight-specification-reconciliation.md

Commit:
See the commit section of the final response (single report file; no other file changed)

Push:
See the push section of the final response

Working tree:
CLEAN

Next action:
Do NOT start I1. Obtain the PO decision on C-1 (or the missing separate I1 authorisation prompt), then implement I1 strictly within D2 §24.2/§24.5/§24.6.

STOP.
```
