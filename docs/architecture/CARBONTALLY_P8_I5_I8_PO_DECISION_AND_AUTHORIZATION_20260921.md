# CarbonTally Insight I5–I8 PO Decision & Authorization Record

**Kind:** Product Owner decision and authorization record.
**Decision date:** 2026-09-21 · **PO authority:** Product Owner.
**Baseline:** I1–I4 CLOSED; I4 `CLOSED — VERIFIED PASS` (implementation `310a62a`, OHD `6a4fda1`, PO closure `725f9f8`).
**Authoritative branch:** `p8-release-reconciled`.
**Based on:** `docs/implementation/phase8/CT-P8-I5-I8-PREAUTHORIZATION-READINESS-AUDIT-20260921.md` (readiness audit: I5 `READY WITH PO DECISIONS`; I6 `READY WITH PO DECISIONS`; I7 `NOT READY`; I8 `READY WITH PO DECISIONS`).
**Provenance (Cline):** this document reproduces the Product Owner's I5–I8 decision and authorization record of 2026-09-21 **verbatim** (sections 1–16 below are the PO text, unaltered). Recording it authorizes no implementation by itself; the separate I5 implementation authorization is awaited per PO §15.

---

# 1. Purpose

This record consolidates the Product Owner decisions required to move CarbonTally Insight beyond the completed I4 stage.

It is based on the authoritative:

`CT-P8-I5-I8-PREAUTHORIZATION-READINESS-AUDIT-20260921.md`

The audit found:

* **I5 — Context:** READY WITH PO DECISIONS
* **I6 — UI:** READY WITH PO DECISIONS
* **I7 — Privacy/Retention/Export:** NOT READY
* **I8 — Billing/Production Hardening:** READY WITH PO DECISIONS

The purpose of this record is to:

1. close the product/architecture decisions that are within current PO authority;
2. explicitly identify decisions requiring legal, commercial, external-provider or other external authority;
3. establish bounded implementation scope;
4. prevent implementation agents from inventing unresolved policy;
5. separately authorize only those stages for which a bounded implementation scope now exists.

---

# 2. Existing authoritative baseline

The following stages remain closed:

| Stage                                 | Status                     |
| ------------------------------------- | -------------------------- |
| I1 — Conversation/message persistence | **CLOSED**                 |
| I2 — Authorization/visibility         | **CLOSED — VERIFIED PASS** |
| I3 — Controlled read-only tools       | **CLOSED — VERIFIED PASS** |
| I4 — AI interaction + canonical audit | **CLOSED — VERIFIED PASS** |

I4 verified implementation:

`310a62a`

OHD independent verification:

`6a4fda1`

I4 PO closure:

`725f9f8`

The I4 closure does not authorize I5–I8 automatically.

The I2 authorization boundary remains authoritative for every subsequent stage.

---

# 3. Global PO decisions for I5–I8

## 3.1 Authorization remains the security boundary

**DECISION — CLOSED**

I2 authorization remains the sole authorization authority.

Context, UI state, stored references, summaries, tool results, audit records and LLM instructions must never grant access.

Every protected read must re-authorize the current caller.

---

## 3.2 Deterministic data remains authoritative

**DECISION — CLOSED**

Structured CarbonTally data and deterministic domain services remain authoritative.

Conversation history, summaries, narration and model-generated text are contextual/explanatory material and cannot override authoritative CarbonTally results.

---

## 3.3 Stored references remain locators

**DECISION — CLOSED**

Insight references remain locators, never authorization grants.

Resolving a reference must pass through the existing authorization boundary.

---

## 3.4 Canonical audit ledger

**DECISION — CLOSED**

`public.audit_trail` remains the canonical CarbonTally Insight audit ledger.

No second Insight audit ledger may be introduced.

---

## 3.5 I3 contract

**DECISION — CLOSED**

The four ratified I3 tools remain unchanged.

I3 `ToolStatus` remains unchanged.

No new I3 tool is authorized by this record.

---

## 3.6 I4 contract

**DECISION — CLOSED**

I4's interaction, tool-call, answer-state, audit-correlation and creator-private visibility contracts remain the baseline for I5–I8.

No I4 redesign is authorized as part of these decisions.

---

## 3.7 AI/provider principle

**DECISION — CLOSED**

Provider attribution must remain truthful.

If authoritative provider usage/cost information is unavailable, CarbonTally must not fabricate it.

The current nullable `tokens_used` / `cost` model remains acceptable until an authoritative usage source exists.

---

---

# 4. I5 — Context PO decisions

## I5 status

**AUTHORIZED — NEXT IMPLEMENTATION STAGE**

The readiness audit found no technical blocker, but five decisions were blocking bounded authorization.

Those decisions are now resolved below.

---

## I5-1 — Context history depth and selection

**DECISION — CLOSED**

I5 shall use a **bounded, deterministic selection policy**.

The initial I5 policy is:

1. current interaction/question has highest priority;
2. current conversation history is considered before unrelated conversations;
3. messages/interactions are ordered chronologically for contextual coherence;
4. the context assembler selects the most recent relevant material within the configured context budget;
5. irrelevant historical material must not be included merely because it exists;
6. cross-conversation context is **not included in the initial I5 implementation**.

The initial implementation shall therefore be **current-conversation context only**.

No semantic/vector relevance engine is authorized.

---

## I5-2 — Compaction/summarization

**DECISION — CLOSED**

Initial I5 implementation shall **not perform AI-generated summarization or compaction**.

The first I5 implementation will use bounded selection/truncation rather than generated summaries.

Rationale:

* avoids introducing another AI-generation path;
* avoids persistence/privacy ambiguity;
* avoids requiring a second summarization lifecycle;
* keeps I5 deterministic and bounded;
* keeps I7 scope smaller.

This means the phrase "summarization if approved" in the Master Specification is now resolved for the initial I5 implementation as:

> **Not included in I5 v1.**

A future summarization capability requires a separate PO decision.

---

## I5-3 — Context budget

**DECISION — CLOSED**

Initial I5 shall use a **character-based context budget**, consistent with the existing CarbonTally context-bounding idiom identified by the readiness audit.

Initial maximum:

**20,000 characters of assembled historical context.**

The implementation must:

* enforce the bound before provider submission;
* preserve the current question;
* prioritize recent/relevant current-conversation material;
* truncate deterministically;
* never exceed the configured bound.

The implementation must keep the budget configurable in code/configuration rather than scattering a magic number through the system.

No token-counting library is authorized by this decision.

A future token-based budget may be considered separately.

---

## I5-4 — Summary persistence

**DECISION — CLOSED**

Because AI summarization/compaction is not part of initial I5:

> **No conversation summaries will be persisted by I5.**

No summary table is authorized.

No summary column is authorized in I1/I4 tables.

No summary retention policy is required for I5 v1.

This deliberately avoids creating an I5→I7 persistence dependency.

---

## I5-5 — Stale references

**DECISION — CLOSED**

Context must never be treated as authoritative merely because a previous interaction contained a reference.

When current authoritative data conflicts with historical context:

* current authorized lookup wins;
* the historical statement must not override the current result;
* stale/unresolvable references must not be presented as current authoritative evidence.

No autonomous correction of historical records is authorized.

---

## I5-6 — Historical tool results

**DECISION — CLOSED**

Initial I5 may use **bounded structured historical interaction/tool-result context only where required to explain the current conversation**.

It must not indiscriminately inject complete historical tool payloads.

The implementation shall prefer:

* answer state;
* concise result projection;
* references;
* stable identifiers;
* relevant structured fields.

Unrestricted historical tool payload replay is not authorized.

---

## I5-7 — Audit information in context

**DECISION — CLOSED**

Canonical audit records are **not conversational context**.

`public.audit_trail` must not be injected into the LLM context merely because an audit event exists.

Audit information may be accessed only through an explicitly authorized future requirement.

---

## I5-8 — Empty/missing context

**DECISION — CLOSED**

Empty context is a normal condition.

I5 must not fabricate historical context.

If no relevant context exists, the interaction proceeds using the current question and authoritative deterministic result.

Absence of context must not automatically become `zero`.

---

## I5-9 — Multi-conversation context

**DECISION — CLOSED**

Initial I5 is **single-conversation scoped**.

No cross-conversation memory is authorized.

Any future cross-conversation memory requires a separate PO decision covering:

* authorization;
* selection;
* privacy;
* retention;
* UX;
* export implications.

---

## I5 authorization boundary

**AUTHORIZED**

Cline may implement I5 only within the decisions above.

I5 must not implement:

* AI summarization;
* persistent summaries;
* cross-conversation memory;
* RAG;
* embeddings;
* vector search;
* LangChain;
* new authorization rules;
* new I3 tools;
* UI;
* retention/export;
* billing.

---

# 5. I6 — UI PO decisions

## I6 status

**AUTHORIZED — BOUNDED IMPLEMENTATION**

The readiness audit found no backend contract gap.

The following UI decisions are now closed.

---

## I6-1 — Entry point

**DECISION — CLOSED**

Insight will live inside the **authenticated customer workspace**, using the existing authenticated/v3 frontend architecture.

It must not be placed in the public FAQ assistant.

---

## I6-2 — Navigation

**DECISION — CLOSED**

Create a dedicated authenticated Insight workspace/route.

The exact route name may follow existing v3 routing conventions.

Do not redesign global navigation.

---

## I6-3 — History UX

**DECISION — CLOSED**

The initial Insight UI shall provide:

* creator-private conversation list;
* conversation view;
* current interaction/message history;
* ability to start/continue a conversation.

No shared conversation workspace is authorized.

---

## I6-4 — Evidence/reference presentation

**DECISION — CLOSED**

References shall be displayed as evidence/provenance locators.

The UI must not imply that possession of a reference grants access.

When a reference is selected/resolved, the backend must re-authorize access.

If resolution is unavailable or unauthorized, the UI must show a non-disclosing state.

The UI must not expose information from a foreign resource merely because an identifier is present.

---

## I6-5 — Answer-state presentation

**DECISION — CLOSED**

The UI must support the complete current I4 answer-state vocabulary, including states that are not currently reachable from every execution path.

At minimum, the UI must have distinct handling for:

* successful answer;
* zero;
* no data;
* insufficient data;
* needs clarification;
* not authorized;
* provider unavailable;
* tool failure;
* partial;
* rate limited;
* refused;
* ungrounded;
* invalid input;
* error.

The UI must never convert:

`no_data` → `zero`.

---

## I6-6 — Provider unavailable

**DECISION — CLOSED**

When deterministic information is available but provider narration is unavailable:

* show the deterministic result;
* clearly indicate that narration is unavailable;
* do not fabricate narration;
* do not present provider failure as a CarbonTally data failure.

---

## I6-7 — Empty/loading/error states

**DECISION — CLOSED**

I6 must explicitly implement:

* initial empty state;
* loading state;
* no-data state;
* clarification state;
* unauthorized/hidden-resource state;
* provider-unavailable state;
* general error state.

Error messaging must not disclose resource existence where the API intentionally returns non-disclosing responses.

---

## I6-8 — Replay/lifecycle

**DECISION — CLOSED**

The initial UI may expose meaningful interaction lifecycle/replay information where useful, but it must not expose internal implementation details unnecessarily.

`replayed=true` may be represented as an informational state.

No new lifecycle model is authorized.

---

## I6-9 — Public assistant reuse

**DECISION — CLOSED**

The existing public FAQ assistant is **not** the Insight UI.

No reuse/integration is authorized in I6.

---

## I6-10 — Accessibility/responsive acceptance

**DECISION — CLOSED**

I6 must follow the project's existing responsive frontend conventions and accessibility testing practices.

Acceptance requires:

* keyboard accessibility;
* meaningful accessible labels;
* usable focus states;
* responsive authenticated workspace presentation;
* automated frontend tests for major states.

No new external accessibility framework is required.

---

## I6 authorization boundary

**AUTHORIZED**

Cline may implement I6 within the above UX decisions.

I6 must not:

* modify backend authorization;
* introduce new Insight APIs unless an actual contract gap is demonstrated and separately authorized;
* alter I3/I4 semantics;
* expose shared/private data;
* implement billing;
* implement retention/export;
* introduce public Insight access.

---

# 6. I7 — Privacy / Retention / Export

## I7 status

**NOT READY — NOT AUTHORIZED**

The readiness audit correctly identified I7 as requiring legal/privacy/business decisions before bounded implementation.

The PO therefore resolves only the engineering boundaries that are within current authority.

---

## I7 decisions that are CLOSED now

### I7-A — Existing I2 authorization remains mandatory

**CLOSED**

Retention/export operations must respect the existing authorization model.

---

### I7-B — Canonical audit separation

**CLOSED**

Conversation transcripts and provider payloads do not become unrestricted audit payloads.

`public.audit_trail` remains the canonical audit ledger.

---

### I7-C — `ai_content_history`

**CLOSED**

Continue Q1:

> **Option C — retain `public.ai_content_history` unchanged and outside I4.**

No migration, deletion, rename or integration is authorized.

Its future disposition remains a separate PO decision.

---

### I7-D — Append-only I4 evidence

**CLOSED**

I7 must respect the existing I4 append-only design.

Any future deletion/archive mechanism must explicitly account for:

* interaction immutability;
* tool-call immutability;
* canonical audit retention;
* existing database triggers;
* conversation cascade relationships.

I7 implementation cannot simply disable or bypass those controls.

---

## I7 decisions requiring external/legal/business authority

The following are:

**NOT YET AUTHORIZED — REQUIRES EXTERNAL DECISION**

### Retention

* retention duration for conversations;
* retention duration for messages;
* retention duration for interactions;
* retention duration for tool-call evidence;
* audit retention policy;
* retention of any future summaries.

### Deletion

* user deletion rights;
* hard vs soft deletion;
* organization deletion semantics beyond current cascades;
* legal hold requirements;
* deletion exceptions.

### Export

* who may export;
* export scope;
* export format;
* redaction requirements;
* whether raw questions/narration are exportable;
* whether provider metadata is exportable;
* whether export is audited.

### Provider/privacy

* provider data retention;
* provider training/data-use policy;
* residency;
* subprocessors;
* PII classification;
* privacy notices.

These must not be invented by Cline.

---

## I7 authorization decision

**NOT AUTHORIZED**

I7 implementation must wait until the above external/legal/business decisions and acceptance criteria are established.

---

# 7. I8 — Billing / Production Hardening

## I8 status

**PARTIALLY AUTHORIZED ONLY — ENGINEERING HARDENING BOUNDARY**

The readiness audit found a substantial existing billing/commercial foundation, but also unresolved commercial and provider questions.

Therefore I8 is **not authorized as one undifferentiated implementation stage**.

It is divided into:

* **I8-A — Production/operational hardening:** potentially authorizable after bounded specification;
* **I8-B — Insight commercial/billing policy:** NOT YET AUTHORIZED.

---

# 8. I8-A — Production/operational hardening

The following engineering principles are PO-closed:

### Rate limiting

**CLOSED PRINCIPLE**

Insight must have bounded protection against:

* user abuse;
* organization abuse;
* endpoint bursts;
* provider overuse.

Existing rate limiting infrastructure should be reused.

Exact production thresholds remain subject to implementation/audit evidence and must not be invented as commercial policy.

---

### Observability

**CLOSED PRINCIPLE**

Operational observability must cover at least:

* interaction correlation;
* authorization outcome;
* tool selection;
* tool success/failure;
* answer status;
* provider availability;
* latency;
* safe error category;
* rate limiting;
* interaction/audit identifiers.

Do not log:

* secrets;
* authentication tokens;
* unrestricted customer content;
* provider payloads.

---

### Provider resilience

**CLOSED PRINCIPLE**

Provider failure must degrade safely.

No fabricated provider response.

Deterministic results should survive provider narration failure where possible.

---

### Deployment

**CLOSED**

No Insight stage may reach production merely because implementation exists.

The existing:

**PO authorization → implementation → OHD verification → PO closure → controlled deployment authorization → deployment → post-deployment verification**

chain remains mandatory.

---

### SLOs

**NOT YET AUTHORIZED — PO/PRODUCT DECISION REQUIRED**

No numerical SLO may be invented by Cline.

---

### Backup/recovery

**NOT YET AUTHORIZED — OPERATIONS DECISION REQUIRED**

No production backup/recovery policy may be invented by implementation agents.

---

### Incident response

**NOT YET AUTHORIZED — OPERATIONS DECISION REQUIRED**

Insight-specific incident/runbook requirements must be established before final I8 production-hardening closure.

---

# 9. I8-B — Commercial / billing decisions

The following are explicitly:

**NOT YET AUTHORIZED — REQUIRES BUSINESS/COMMERCIAL DECISION**

* Insight usage unit;
* whether Insight consumes existing credits;
* Insight allowances;
* entitlement enforcement point;
* pricing;
* plan/tier inclusion;
* overage;
* provider-cost absorption/pass-through;
* billing failure behavior;
* refunds/credit adjustments;
* whether Insight appears in `/me/credits`.

No Cline implementation may invent these policies.

---

# 10. Payment provider

**NOT YET AUTHORIZED — REQUIRES FACTUAL INVESTIGATION**

The readiness audit could not establish whether a payment provider/webhook integration exists.

Therefore:

* do not assume Stripe;
* do not assume another provider;
* do not create a payment integration;
* do not replace the existing billing system.

A separate bounded forensic investigation may be authorized if required.

---

# 11. I8 implementation authorization

**NOT AUTHORIZED AS A FULL STAGE**

Only the bounded operational-hardening principles above are PO-approved.

A concrete I8 implementation authorization requires:

1. commercial decisions;
2. usage/entitlement policy;
3. SLO targets;
4. operational monitoring requirements;
5. backup/recovery requirements;
6. incident/runbook requirements;
7. payment-provider factual determination;
8. acceptance criteria.

---

# 12. Final stage status

| Stage                                 | PO decision                                 | Implementation authorization     |
| ------------------------------------- | ------------------------------------------- | -------------------------------- |
| **I5 — Context**                      | **DECISIONS CLOSED**                        | **AUTHORIZED**                   |
| **I6 — UI**                           | **DECISIONS CLOSED**                        | **AUTHORIZED**                   |
| **I7 — Privacy/Retention/Export**     | External/legal decisions outstanding        | **NOT AUTHORIZED**               |
| **I8 — Billing/Production Hardening** | Commercial/operations decisions outstanding | **NOT AUTHORIZED AS FULL STAGE** |

---

# 13. I5/I6 implementation relationship

I5 and I6 are independently implementable against the existing I1–I4 contracts.

However, the PO decision is:

> **I5 should be implemented before any I6 UI feature that claims to expose context-selection or context-derived behavior.**

Therefore:

* I5 is the next implementation stage;
* I6 is authorized at the product level but should not implement context-dependent UX until the I5 contract exists;
* Cline must not expand I6 into I5;
* Cline may implement I6 foundation/UI states that depend only on I1–I4 if separately authorized after I5's implementation boundary is established.

For governance simplicity, the immediate Cline implementation authorization should therefore be **I5 only**.

I6 remains **PO-authorized but implementation-deferred** until the I5 contract is established.

---

# 14. Explicit non-authorizations

This record does NOT authorize:

* I7 implementation;
* full I8 implementation;
* payment-provider integration;
* pricing changes;
* subscription-plan changes;
* commercial entitlement changes;
* retention periods;
* legal deletion policies;
* residency decisions;
* subprocessor decisions;
* privacy-notice changes;
* RAG;
* embeddings;
* vector search;
* LangChain;
* cross-conversation memory;
* persistent AI summaries;
* new I3 tools;
* new personas;
* new authorization roles;
* autonomous actions;
* production deployment.

---

# 15. Next implementation authorization

The next implementation authorization is:

> **I5 — Context**

It shall be separately issued to Cline with the exact bounded decisions recorded in this document.

The Cline I5 implementation must:

* inspect the current repository;
* implement only the authorized I5 context scope;
* preserve I1–I4 contracts;
* use current-conversation context;
* use deterministic bounded selection/truncation;
* use a configurable 20,000-character maximum;
* not implement summarization;
* not persist summaries;
* not use cross-conversation memory;
* not use RAG/embeddings/vector search;
* re-authorize all protected reads;
* keep authoritative data above historical context;
* add regression tests;
* create a permanent implementation report;
* commit and push;
* stop for independent OHD verification.

---

# 16. Governance conclusion

**I1–I4 remain CLOSED.**

**I5 is AUTHORIZED for bounded implementation.**

**I6 is product-authorized but implementation-deferred until the I5 contract is established.**

**I7 remains NOT AUTHORIZED pending legal/privacy/business decisions and acceptance criteria.**

**I8 remains NOT AUTHORIZED as a full stage pending commercial, operational and provider decisions.**

No implementation agent may resolve the externally dependent decisions by assumption.

The next governance transition is:

**PO I5 authorization → Cline I5 implementation → OHD independent verification → PO I5 closure.**

Only after that should the I6 implementation authorization be issued.

---

## Cline recording note (provenance only — not part of the PO decision text)

This document reproduces the Product Owner's I5–I8 decision and authorization record of 2026-09-21 verbatim. Recording it performs and authorizes no implementation:

* **no application, schema, migration, test, frontend, RLS, billing or configuration change was made** by this recording;
* I5 remains to be implemented only under a **separately issued** authorization (PO §15), which this note does not presume;
* I6, I7 and I8 remain unimplemented and unauthorised as recorded by the PO;
* the Master Specification's stage-status lines (§3.1 table, §48.5) were **not** modified by this recording; they are superseded for I5/I6/I7/I8 status by this record and will be updated on PO instruction.
