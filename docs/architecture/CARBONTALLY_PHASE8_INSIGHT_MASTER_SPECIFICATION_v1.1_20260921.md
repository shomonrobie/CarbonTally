# CarbonTally Insight — Master Specification
## Full Implementation Blueprint, Security Boundary, Verification Contract, and Stage Authority

**Document ID:** `CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION`  
**Version:** `1.1 — I3-Verified Consolidated Implementation Baseline`  
**Date:** 2026-09-21  
**Product:** CarbonTally Insight  
**Technical namespace for new implementation:** `carbontally_insight_*` / `CarbonTallyInsight*`  
**Authority:** Product Owner (PO)  
**Document role:** Master product, architecture, security, data, implementation, testing, and acceptance specification  
**Status:** `CONSOLIDATED — I3 UPDATED / PO CLOSURE RECORDED — READY FOR PO RATIFICATION AS MASTER SPECIFICATION`  

> **Important:** No specification can make a production system literally "full proof." This document is intended to be **implementation-ready and auditable**, with explicit security boundaries, stage gates, acceptance criteria, failure behaviour, and verification requirements. It must still be validated against the live repository at each implementation stage and independently verified by OHD.

---

# 1. Executive Summary

CarbonTally Insight is CarbonTally's evidence-backed conversational intelligence capability.

It is **not** a generic chatbot, a carbon calculation engine, an assurance service, a reporting replacement, or an unrestricted database interface.

Its authoritative architecture is:

```text
User
  ↓
Authenticated CarbonTally Insight surface
  ↓
Server-side identity + current authorization
  ↓
Intent / request interpretation
  ↓
Allowlisted deterministic CarbonTally tools
  ↓
Authoritative CarbonTally domain/data services
  ↓
Structured authoritative result + provenance/reference
  ↓
Optional AI explanation
  ↓
Answer + explicit status + evidence/reference presentation
  ↓
Persistent conversation history
  +
AI interaction record
  +
canonical audit event
```

The central architectural rule is:

> **The LLM explains authoritative CarbonTally results; it does not create authoritative carbon facts.**

CarbonTally Insight must therefore remain deterministic-first, authorization-first, provenance-aware, tenant-safe, and independently testable without an LLM provider.

The Master Specification consolidates:

1. PO-ratified D2 architecture;
2. D1 repository-grounded discovery;
3. verified I1/I2 implementation reality;
4. I3 tool-catalogue decisions and implementation findings;
5. independent OHD verification requirements;
6. established CarbonTally architecture and governance;
7. relevant industry guidance for AI security, trustworthy AI, and GHG accounting.

---

# 2. Authority and Document Hierarchy

This document is intended to become the consolidated implementation blueprint, but it does **not** retroactively change prior PO decisions.

## 2.1 Authority hierarchy

When documents conflict:

1. Explicit PO decisions and closure records
2. This Master Specification after PO ratification
3. Stage-specific PO authorization records
4. Stage-specific implementation specifications
5. Independently verified implementation/closure records
6. Repository implementation reality
7. Discovery/design proposals
8. General model assumptions

A lower-level document must never silently override a higher-level PO decision.

## 2.2 Historical documents

The following remain authoritative for their historical decisions and evidence:

- Phase 8 D1 discovery
- Phase 8 D2 PO ratification
- I2 PO closure record
- I3 implementation and OHD verification/remediation records
- CarbonTally reporting lifecycle specifications
- CarbonTally AI architecture documents
- CarbonTally security/governance documents

This Master Specification consolidates them; it does not erase their history.

## 2.3 Status vocabulary

Every requirement and stage must use one of:

- `RATIFIED`
- `IMPLEMENTED`
- `VERIFIED`
- `CLOSED`
- `IN_PROGRESS`
- `BLOCKED`
- `DEFERRED`
- `OPEN`
- `NOT_AUTHORIZED`
- `SUPERSEDED`
- `HISTORICAL`

No implementation agent may convert `OPEN`, `DEFERRED`, or `NOT_AUTHORIZED` into an implementation requirement without a new PO decision.

---

# 3. Current CarbonTally Insight State

## 3.1 Stage state as of 2026-09-21

| Stage | State | Authority |
|---|---|---|
| D1 Discovery | `COMPLETE` | D1 discovery |
| D2 PO ratification | `RATIFIED` | D2 PO ratification |
| I1 Persistent foundation | `IMPLEMENTED / INCORPORATED INTO VERIFIED BASELINE` | I1/I2 records |
| I2 Authorization & visibility | `CLOSED — VERIFIED PASS` | OHD + PO closure |
| I3 Controlled read-only tools | `CLOSED — VERIFIED PASS` | OHD re-verification + PO closure |
| I4 AI interaction + canonical audit | `CLOSED — VERIFIED PASS` | implementation `310a62a` · OHD `6a4fda1` · PO closure `CARBONTALLY_P8_I4_INSIGHT_CLOSURE_20260921.md` |
| I5 Context management | `CLOSED — VERIFIED PASS` | implementation `f9d91e1` · report correction `4d23031` · OHD `cd718d6` · PO closure `CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md` |
| I6 Insight UI | `CLOSED — VERIFIED PASS` | implementation `09e2315` · docs `ea7ccc2` · OHD `4acc249` · PO closure `CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` |
| I7 Privacy/retention/export | `NOT_AUTHORIZED` | PO gate |
| I8 Billing/production hardening | `NOT_AUTHORIZED` | PO gate |

## 3.2 I2 authoritative closure

I2 is closed at verified application revision:

`177dff51f59e9b904c021b4bbb7a6c7ee236adf1` (`177dff5`)

OHD independently verified the authorization boundary and the PO subsequently recorded:

> `I2 CLOSED — VERIFIED PASS at 177dff5`

The I2 closure record explicitly states that I3 authorization is separate and that deployment is a separate controlled decision.

## 3.3 I3 current state

I3 was implemented, independently tested, found defective by OHD, and remediated by Cline.

The remediation target was:

`651f8c1aa60c635ec1e4da482cfcd651d6657fe8` (`651f8c1`)

OHD independently re-verified the remediation and reported:

> **PASS — I3 REMEDIATION VERIFIED**

OHD verification commit: `7faaa57`.

The re-verification confirmed, through real CarbonTally repository wiring and the real HTTP path, that `report_evidence_lookup` executes successfully; the D-01 real-wiring defect is resolved; the D-02 circular import is resolved; the new wiring tests are sensitive to the pre-remediation source; the I1/I2 baseline remained intact; and no I4–I8 functionality was introduced.

The four full-suite failures remained the same pre-existing failures and no new failure was attributed to the remediation.

**PO DECISION: I3 IS NOW CLOSED — VERIFIED PASS at `651f8c1`.**

The OHD report commit `7faaa57` is verification evidence only and does not change the verified application revision.

---

# 4. Product Definition

## 4.1 Product purpose

CarbonTally Insight provides conversational access to authorized CarbonTally information while preserving:

- authoritative calculations;
- evidence provenance;
- tenant isolation;
- current authorization;
- report lifecycle controls;
- auditability;
- deterministic behaviour;
- safe AI boundaries.

## 4.2 Intended questions

Representative questions include:

- What were our emissions for a given period?
- What were Scope 1, 2, and 3 emissions?
- What changed compared with another period?
- Which contributors drove a change?
- Which report version contains this result?
- What evidence supports the figure?
- Which calculation snapshot was used?
- Which emission factor was used?
- What is the status of a report?
- Why cannot I access a particular record?

These examples do not automatically authorize a tool or data source.

## 4.3 Product non-goals

Insight is not:

- an unrestricted chatbot;
- a replacement for CarbonTally's calculation engine;
- a replacement for the factor database/matching engine;
- a reporting engine;
- an assurance or certification service;
- an auditor;
- an unrestricted SQL interface;
- a general document search engine;
- a general-purpose agent;
- an autonomous consequential-action system;
- a substitute for authoritative evidence;
- a substitute for the Human ↔ Human messaging domain.

---

# 5. Core Non-Negotiable Principles

## P-01 — Authorization before data

```text
Authenticate
→ resolve current identity
→ resolve current organization/scope
→ authorize
→ apply RLS/domain controls
→ execute allowlisted tool
→ return permitted data
```

The LLM is never an authorization boundary.

## P-02 — Conversation history is not authoritative

Stored conversation content never becomes authoritative for:

- emissions;
- calculations;
- factors;
- evidence;
- report facts;
- authorization.

A prior answer is historical conversational output.

## P-03 — Stored references are not authorization grants

A stored report ID, calculation ID, evidence ID, snapshot ID, or hash never grants access.

Every reference must be re-resolved under current authorization.

## P-04 — Deterministic-first

Where CarbonTally can answer deterministically, the deterministic result is authoritative.

The LLM may explain it.

## P-05 — No fabricated carbon facts

The LLM must never invent:

- emission values;
- factors;
- calculation outputs;
- evidence;
- report states;
- provenance;
- authorization.

## P-06 — `zero` is not `no_data`

The system must distinguish:

- `zero`
- `no_data`
- `not_authorized`
- `insufficient_data`
- `needs_clarification`
- `tool_failure`
- `provider_unavailable`
- other explicitly defined statuses.

## P-07 — Read-only foundation

Initial Insight tools are read-only.

Mutation/consequential actions require a separate future PO authorization and separate security design.

## P-08 — Tenant isolation

Cross-organization access is categorically prohibited.

## P-09 — Provider independence

Core authoritative CarbonTally functionality must remain operationally understandable and testable without an LLM provider.

## P-10 — Every stage is independently authorized

Completion of I(n) never automatically authorizes I(n+1).

---

# 6. Domain Boundary

## 6.1 Separate conversational domain

Insight must remain separate from Human ↔ Human messaging.

Do not reuse:

- `conversations`
- `messages`
- `conversation_participants`
- Human messaging routes/services
- Human messaging authorization semantics

A chat-like UI is allowed.

A shared chat data model is not.

## 6.2 Canonical new namespace

New Insight implementation uses:

```text
carbontally_insight_conversations
carbontally_insight_messages
carbontally_insight_interactions
```

and corresponding `CarbonTallyInsight*` domain/service terminology.

Existing historical `ask_*` terminology is retained only where necessary for historical documentation.

No broad repository rename is authorized.

---

# 7. Persona and Access Model

## 7.1 Initial surface

Initial Insight surface:

- customer workspace;
- authenticated customer users;
- creator-private conversations.

## 7.2 Customer roles

The I2-verified customer role representations are:

- `org_owner`
- `org_admin`
- `org_member`
- `org_viewer`

Their access remains subject to current organization membership, organization state, and existing authorization rules.

## 7.3 Creator-private visibility

A customer user may use Insight within an authorized active organization, but the initial conversation visibility is:

```text
organization + conversation_creator
```

A customer admin does not automatically gain visibility into another user's Insight conversations.

## 7.4 Consultant

Consultant Insight conversation access is deferred unless separately authorized.

If later authorized, it must use the existing consultant-to-customer authorization relationship.

## 7.5 Staff

Staff access is deferred beyond the verified I2 authorization foundation.

Where staff access is later authorized, identity alone is insufficient. Existing explicit permission requirements must remain in force.

## 7.6 Auditor

Auditor Insight access is deferred.

Nothing in Insight changes CarbonTally's assurance boundary.

## 7.7 Processing Entity / PE

PE Insight is not included in the initial capability.

No investor/private-equity persona may be invented without a separate PO decision.

---

# 8. Persistence Architecture

## 8.1 Three-layer model

Insight has three distinct persistence layers.

### Layer 1 — Conversation history

Stores user-facing conversation state:

- conversation;
- messages;
- actor/role;
- timestamps;
- title/status/lifecycle metadata.

Purpose:

- continuity;
- user experience;
- follow-up questions.

### Layer 2 — AI interaction record

Stores machine/audit-oriented execution history:

- question;
- interpreted request;
- tool calls;
- authorized parameters;
- tool results/references;
- provider/model attribution when truthfully known;
- answer status;
- usage/cost where truthfully available;
- result/reference hashes where appropriate.

Purpose:

- reconstructability;
- AI execution provenance;
- operational investigation.

### Layer 3 — Canonical CarbonTally audit event

The existing canonical audit ledger remains the authoritative platform audit trail.

It must not be replaced by conversation history or AI interaction records.

## 8.2 Layer separation

Conversation deletion must never automatically erase the canonical audit record.

Conversation history may be user-facing and mutable according to future policy.

AI interaction records have a separate lifecycle.

Canonical audit events remain governed by the platform audit policy.

## 8.3 I1/I4 boundary

I1 builds Layer 1.

I4 builds Layer 2 and its canonical audit integration.

Do not prematurely implement I4 functionality inside I1.

---

# 9. Data Model Requirements

The exact schema is implementation-stage work, but every schema must satisfy these invariants.

## 9.1 Conversation invariants

Every Insight conversation must have:

- stable identifier;
- organization identifier;
- creator identifier;
- lifecycle state;
- created timestamp;
- updated timestamp;
- integrity constraints;
- tenant-aware indexes;
- creator-visibility capability.

## 9.2 Message invariants

Every message must have:

- stable identifier;
- conversation identifier;
- actor type;
- actor identity where applicable;
- message content or structured content representation;
- created timestamp;
- ordering mechanism;
- integrity constraints.

The message model must not imply that assistant text is authoritative evidence.

## 9.3 Interaction invariants

When I4 is authorized, every interaction must be reconstructable enough to establish:

```text
who asked
→ what request was interpreted
→ which authorized tools were invoked
→ what authoritative references were returned
→ which model/provider was used, if any
→ what answer status resulted
→ what answer was produced
```

## 9.4 Organization key

Every Insight persistence table must carry an explicit organization scope where required by the security architecture.

`organization_id` must not be nullable merely to bypass tenant policy.

## 9.5 Creator key

Creator identity must be retained where creator-private visibility is part of the contract.

## 9.6 No authority by foreign key

Foreign keys to reports/calculations/evidence do not grant access.

---

# 10. RLS and Authorization Requirements

## 10.1 RLS is mandatory defense in depth

Application authorization and RLS are separate security layers.

Neither may be disabled merely to make Insight functionality work.

## 10.2 Every-read reauthorization

Every read must resolve current authorization.

Do not trust:

- cached authorization;
- conversation creator history;
- stored tool references;
- prior successful access;
- LLM decisions.

## 10.3 Revocation

After authorization is revoked:

- subsequent conversation reads must fail;
- referenced authoritative records must fail;
- consultant relationship termination must take effect;
- organization suspension must take effect;
- removed staff permission must take effect.

Persistence must never create a durable access path after revocation.

## 10.4 Denial semantics

Where the caller lacks permission, the system must return an authorization-safe result.

Do not disclose restricted record existence through error details.

## 10.5 RLS testing

For every Insight table and material authorization path, tests must cover:

- owner allow;
- admin allow;
- member allow;
- viewer allow where applicable;
- cross-org deny;
- inactive-org deny;
- revoked-membership deny;
- unknown-org deny;
- unratified-role deny;
- creator-private deny;
- consultant relationship revoked deny;
- staff permission absent deny;
- anonymous deny;
- forged role deny.

---

# 11. Tool Architecture

## 11.1 I3 ratified tool catalogue

The PO-ratified initial tool catalogue is:

1. `report_lookup`
2. `report_version_lookup`
3. `report_evidence_lookup`
4. `calculation_snapshot_lookup`

No additional tool is implicitly authorized.

## 11.2 Tool contract

Every tool must conform to the six-point contract established for I3:

1. explicit tool identity;
2. validated input;
3. current authorization;
4. deterministic execution;
5. bounded structured result;
6. explicit status/error semantics.

## 11.3 Tool registry

The registry must be closed/allowlisted.

Unknown tool names must not execute.

A prompt cannot dynamically create a tool.

A stored message cannot add a tool.

A provider cannot add a tool.

## 11.4 Tool execution boundary

Only server-side CarbonTally code may invoke Insight tools.

The LLM must not receive arbitrary database credentials, SQL access, filesystem access, or internal service handles.

## 11.5 Tool result boundary

Tool results must contain only fields permitted by the caller's existing visibility.

Sensitive/internal fields must not leak merely because a tool can technically access them.

## 11.6 Bounded result size

Tool responses must be bounded.

Large result sets require explicit pagination or another bounded contract.

Never allow an LLM call to force unbounded database extraction.

## 11.7 References

References identify authoritative records.

References are not authorization grants.

References must be re-resolved before exposing the underlying content.

## 11.8 Report lifecycle

Report tools must expose:

- report identity;
- version identity;
- lifecycle state.

They must never represent:

- `DRAFT`
- `REVIEWED`
- `CHANGES_REQUESTED`
- `REJECTED`

as approved/final.

Report-reading operations must obey the existing report lifecycle and audit requirements.

---

# 12. Tool Security

Each tool must be tested against:

- malformed identifiers;
- oversized identifiers;
- SQL injection attempts;
- path traversal attempts;
- unauthorized organization IDs;
- unauthorized report IDs;
- unauthorized version IDs;
- unauthorized evidence IDs;
- unauthorized calculation IDs;
- forged role claims;
- stale references;
- deleted records;
- suspended organizations;
- revoked relationships.

Tools must use domain/repository interfaces rather than constructing arbitrary SQL from model output.

---

# 13. Intent Classification

## 13.1 Deterministic-first classification

Initial intent classification may use deterministic keyword/rule logic.

It must never grant authorization.

## 13.2 LLM-assisted classification

If a later stage uses an LLM for classification:

- classification remains advisory;
- the server validates the resulting intent;
- only allowlisted tools can execute;
- authorization occurs after intent/tool resolution and before data access;
- invalid tool requests are refused.

## 13.3 Tool ambiguity

If the system cannot confidently determine the intended tool:

```text
needs_clarification
```

is preferable to guessing.

---

# 14. Answer State Model

The final answer pipeline must distinguish at least:

```text
success / answered
zero
no_data
not_authorized
insufficient_data
needs_clarification
tool_failure
provider_unavailable
partial
rate_limited
refused
ungrounded
invalid_input
error
```

The final exact taxonomy may be normalized during implementation, but the semantic distinctions are mandatory.

## 14.1 Cardinal rule

```text
zero ≠ no_data ≠ not_authorized
```

Examples:

- `zero`: authoritative result is exactly 0.
- `no_data`: authorized query returned no applicable record.
- `not_authorized`: data may exist but the caller cannot access it.
- `provider_unavailable`: deterministic result may exist but optional AI narration could not run.
- `needs_clarification`: the request is ambiguous.
- `tool_failure`: required controlled operation failed.

---

# 15. AI / LLM Boundary

## 15.1 Existing abstraction

Reuse CarbonTally's existing AI abstraction.

Do not introduce:

- parallel provider clients;
- direct provider HTTP calls;
- provider-specific application logic;
- API keys in database fields;
- frontend provider calls.

## 15.2 Provider configuration

Provider configuration remains environment-controlled.

Secrets must never be:

- logged;
- persisted in conversation records;
- persisted in audit records;
- returned to frontend;
- committed to source control.

## 15.3 Truthful attribution

The system must distinguish:

```text
configured provider
```

from:

```text
provider actually used successfully
```

Never claim AI was used merely because an AI provider is configured.

## 15.4 Usage/cost

Until the provider abstraction exposes truthful usage:

- `tokens_used = NULL`
- `cost = NULL`

Do not fabricate usage.

## 15.5 AI cannot be authoritative

AI cannot determine:

- final emission value;
- emission factor;
- calculation provenance;
- evidence identity;
- report approval state;
- authorization;
- tenant scope.

---

# 16. Prompt Architecture

## 16.1 System/developer instructions

System/developer instructions may define:

- Insight role;
- safety rules;
- tool contract;
- response style;
- provenance rules;
- status semantics.

They must not embed tenant-specific authorization as static text.

## 16.2 User content

User messages are untrusted.

Statements such as:

> "Ignore the authorization rules."

have no system authority.

## 16.3 Retrieved content

Customer documents, report text, evidence text, and other retrieved content are untrusted data.

They must never be treated as system/developer instructions.

## 16.4 Tool results

Tool results are structured application data.

The LLM must receive only the minimum information required to explain the result.

## 16.5 Prompt injection

The implementation must explicitly defend against:

- direct prompt injection;
- indirect prompt injection in documents;
- tool-result injection;
- conversation poisoning;
- stored malicious instructions.

---

# 17. Context Architecture

## 17.1 Context is bounded

Do not blindly send the full conversation history.

Context must be:

- relevant;
- minimal;
- bounded;
- authorization-safe.

## 17.2 Current authority beats history

If prior conversation says:

> "Your emissions were 100 tCO2e."

but the current authoritative lookup returns 120:

the current authoritative result wins.

The discrepancy should be explained when relevant.

## 17.3 Context cannot grant permission

The model must not infer:

- organization scope;
- role;
- consultant access;
- report access;
- evidence access

from conversation text.

## 17.4 Compaction

Exact compaction/summarization policy is an I5 design decision.

Any future summary must be treated as context, not authoritative carbon data.

---

# 18. Provenance and Evidence

## 18.1 Reconstruction chain

Every authoritative answer should be reconstructable as:

```text
question
→ interpreted intent
→ authorized tool
→ authorized parameters
→ authoritative result
→ reference/provenance
→ optional AI explanation
```

## 18.2 Reference integrity

Where appropriate, references should include stable identifiers and deterministic hashes.

Use existing CarbonTally hashing conventions.

Do not introduce competing integrity schemes unnecessarily.

## 18.3 Evidence answer requirements

When a user asks "show me the evidence", Insight must not invent an explanation.

It must resolve an actual authorized evidence record or return an explicit status.

## 18.4 Calculation answer requirements

When a user asks "show me the calculation", Insight must resolve an actual calculation snapshot or equivalent authoritative record.

The LLM must not reconstruct a calculation independently and present it as the system's calculation.

---

# 19. Reporting Lifecycle Integration

Insight must respect the CarbonTally reporting lifecycle.

The authoritative lifecycle remains:

```text
GENERATE
→ DRAFT
→ REVIEW
→ APPROVE
→ FINAL
→ FROZEN
```

Insight may:

- interpret;
- explain;
- locate;
- summarize;
- assist investigation.

Insight may not:

- approve;
- finalize;
- mutate authoritative carbon facts;
- alter factor provenance;
- bypass versioning;
- bypass approval;
- unfreeze a final report.

AI-generated report narrative remains candidate-only.

---

# 20. Audit Architecture

## 20.1 Three-layer auditability

```text
Layer 1: conversation history
Layer 2: AI interaction record
Layer 3: canonical audit event
```

These must not be collapsed.

## 20.2 Canonical audit

The canonical CarbonTally audit ledger remains authoritative.

Insight must integrate with it only in the authorized I4 stage.

## 20.3 Audit package

Insight conversations are not part of the standard audit/evidence package by default.

The standard audit package remains focused on authoritative:

- evidence;
- calculations;
- provenance;
- workflow;
- readiness.

## 20.4 AI audit event

When I4 is authorized, the canonical audit event should establish that the AI interaction occurred and link to the durable interaction record.

Do not place the entire AI transcript or provider payload into the canonical audit ledger unless separately authorized.

---

# 21. Privacy, Retention, Deletion, and Export

These are deliberately OPEN until I7.

The architecture must support later policy for:

- conversation retention;
- hard/soft deletion;
- user deletion rights;
- organization deletion;
- export;
- provider retention;
- provider training/data use;
- residency;
- subprocessors;
- PII;
- legal/privacy notices;
- rename/archive;
- regeneration/edit semantics.

No retention duration or legal policy may be invented by implementation agents.

---

# 22. Billing and Commercial Model

Billing remains OPEN until I8.

Existing CarbonTally billing/usage infrastructure should be reused where appropriate.

Do not create a parallel Insight billing system.

Do not invent:

- AI credits;
- token pricing;
- quotas;
- entitlements;
- overage pricing;
- provider cost policy.

Commercial policy requires separate PO authorization.

---

# 23. Dormant AI Structure

The repository contains a dormant AI-related data structure identified during discovery.

Do not:

- automatically reuse it;
- automatically delete it;
- create a duplicate AI-history store.

The I3/I4 repository-driven decision must select one bounded home for AI interaction/cost/rating data.

---

# 24. Security Threat Model

The following threats are mandatory test/design concerns.

| ID | Threat | Required control |
|---|---|---|
| T-01 | Prompt injection | Treat user/retrieved content as untrusted |
| T-02 | Sensitive information disclosure | Minimize provider-visible data |
| T-03 | Supply-chain/provider risk | Controlled provider abstraction and dependency review |
| T-04 | Data/model poisoning | Do not treat retrieved content as instructions |
| T-05 | Improper output handling | Validate structured outputs before use |
| T-06 | Excessive agency | Read-only initial tools |
| T-07 | System prompt leakage | Never expose internal prompts/secrets |
| T-08 | Vector/retrieval weaknesses | RAG deferred; future retrieval must be scoped |
| T-09 | Cross-tenant leakage | Current authorization + RLS |
| T-10 | Hallucinated facts | Deterministic authoritative source |
| T-11 | Hallucinated evidence | References must resolve |
| T-12 | Audit falsification | Canonical audit remains separate |
| T-13 | Conversation poisoning | Historical answers never authoritative |
| T-14 | Revocation failure | Every read reauthorized |
| T-15 | Tool abuse | Closed allowlist and validated inputs |

The security design is informed by current OWASP guidance for LLM applications and general web application security, including prompt injection, sensitive information disclosure, broken access control, injection, insecure design, and software/data integrity risks. OWASP's 2025 LLM guidance explicitly identifies prompt injection and sensitive information disclosure among the leading LLM application risks. 

---

# 25. Industry and Domain Standards Alignment

This specification is informed by, but does not claim certification against:

## 25.1 NIST AI RMF

NIST AI RMF provides a voluntary framework for managing AI risks across the AI lifecycle, and NIST's Generative AI Profile identifies GAI-specific risks and suggested risk-management actions.

CarbonTally Insight therefore adopts corresponding engineering themes:

- governance;
- risk identification;
- measurement/evaluation;
- traceability;
- human oversight;
- secure deployment;
- incident/failure handling.

## 25.2 OWASP

The architecture incorporates relevant OWASP principles for:

- broken access control;
- injection;
- insecure design;
- security misconfiguration;
- software supply-chain risk;
- logging/alerting;
- LLM prompt injection;
- sensitive information disclosure;
- improper output handling;
- excessive agency.

## 25.3 GHG Protocol

CarbonTally Insight must preserve the authority of CarbonTally's underlying GHG accounting implementation.

Insight does not redefine:

- Scope 1;
- Scope 2;
- Scope 3;
- organizational boundaries;
- activity data;
- emission factors;
- calculation methodology.

The GHG Protocol Corporate Standard provides requirements and guidance for corporate-level GHG inventories. CarbonTally's calculation/data architecture remains the authoritative source for values exposed through Insight.

## 25.4 ISO 14064-1

ISO 14064-1 specifies principles and requirements for organization-level GHG quantification and reporting.

Insight does not itself become an ISO assurance/certification system.

Its role is to help users understand CarbonTally's authoritative records without changing their underlying meaning.

---

# 26. Reliability and Failure Handling

## 26.1 Provider outage

If the provider is unavailable:

- do not fabricate;
- return deterministic result where available;
- otherwise return `provider_unavailable`.

## 26.2 Tool failure

If a required tool fails:

- return `tool_failure`;
- do not substitute a guessed answer;
- do not silently query an unauthorized fallback source.

## 26.3 Authorization failure

Return `not_authorized`.

Do not reveal protected record contents.

## 26.4 Empty result

Return `no_data`.

Do not convert it to zero.

## 26.5 Ambiguous request

Return `needs_clarification`.

Do not guess critical scope, date, organization, report, or calculation identifiers.

## 26.6 Partial result

A partial answer must explicitly identify what was and was not established.

---

# 27. Observability

The system must support operational visibility into:

- request correlation;
- authorization outcome;
- tool selected;
- tool success/failure;
- answer status;
- provider availability;
- latency;
- safe error categories;
- rate limiting;
- interaction/audit identifiers once I4 exists.

Never log:

- API keys;
- secrets;
- authorization tokens;
- unrestricted customer content;
- sensitive provider payloads;
- raw credentials.

Logging policy must respect privacy decisions when finalized.

---

# 28. Rate Limiting and Abuse Protection

Rate limiting is an I8 production-hardening concern but the architecture must permit it.

Controls should eventually cover:

- authenticated user;
- organization;
- endpoint/tool;
- provider usage;
- burst behaviour;
- abuse patterns.

Rate limits must not become an authorization bypass.

---

# 29. Performance and Scalability

The implementation must avoid:

- unbounded conversation queries;
- unbounded tool results;
- N+1 authorization calls where avoidable;
- full-history LLM prompts;
- unrestricted database scans.

Use:

- appropriate indexes;
- pagination;
- bounded result sizes;
- deterministic queries;
- controlled context windows;
- measurable latency budgets.

Exact SLOs are an I8/product decision and must not be invented prematurely.

---

# 30. API Design Principles

Future Insight APIs must:

- authenticate;
- authorize;
- validate;
- execute through domain services;
- return explicit statuses;
- avoid leaking internal exceptions;
- avoid exposing provider internals;
- use stable identifiers;
- preserve tenant scope;
- provide correlation identifiers where appropriate.

API routes must not be invented outside a stage-specific authorization.

---

# 31. Error Boundary

Application-facing errors must be controlled.

Do not expose:

- Python stack traces;
- SQL errors;
- DSNs;
- internal repository details;
- provider credentials;
- filesystem paths;
- internal object representations.

Unexpected exceptions must be:

1. safely logged according to policy;
2. converted into controlled application errors;
3. prevented from leaking sensitive implementation details.

Broad exception handling must not hide known defects.

Each layer should catch only errors it can meaningfully handle.

---

# 32. Data Integrity and Concurrency

The implementation must handle:

- concurrent message creation;
- duplicate submissions;
- repeated tool calls;
- stale references;
- deleted records;
- organization state changes;
- authorization changes between requests.

Where idempotency is required, it must be explicit rather than inferred.

TOCTOU-sensitive authorization must be tested.

---

# 33. Testing Strategy

Testing must exist at multiple layers.

## 33.1 Unit tests

Cover:

- status mapping;
- input validation;
- authorization predicates;
- serialization;
- field allowlists;
- tool registry;
- intent classification;
- provider error mapping.

## 33.2 Repository integration tests

Use real repository interfaces.

Do not rely only on fake attributes that production repositories do not provide.

## 33.3 RLS tests

Use disposable databases where possible.

Test real RLS enforcement, not only mocked authorization.

## 33.4 HTTP end-to-end tests

At least one test per critical tool must execute through:

```text
HTTP
→ dependency wiring
→ authorization
→ real repository/service path
→ tool
→ response
```

## 33.5 Security tests

Test all threats in §24.

## 33.6 Provider-independent tests

Core deterministic functionality must pass without an LLM provider.

## 33.7 AI evaluation

Once I4/I5 are authorized, AI evaluation must cover:

- factual grounding;
- refusal correctness;
- citation/reference correctness;
- authorization boundary;
- prompt injection;
- stale-context behaviour;
- ambiguous questions;
- hallucination resistance;
- answer-status correctness.

---

# 34. Independent Verification Contract

Cline implementation claims are not closure.

OHD must independently:

1. inspect the authorized scope;
2. inspect the actual implementation;
3. run tests;
4. reproduce material claims;
5. test real wiring;
6. test security boundaries;
7. inspect repository integrity;
8. classify failures;
9. produce a permanent report;
10. commit and push the report;
11. state PASS/FAIL.

OHD must not silently repair defects.

A stage is not verified until OHD reports PASS.

A stage is not closed until PO records closure.

---

# 35. Stage Specifications

# I1 — Persistent CarbonTally Insight Foundation

## Objective

Create the dedicated persistent Insight domain.

## Must include

- Insight conversation persistence;
- Insight message persistence;
- repository/domain layer;
- minimal create/list/read;
- organization scoping;
- creator identity;
- creator-private design capability;
- explicit RLS;
- indexes/constraints;
- bounded API foundation.

## Must not include

- tool execution;
- LLM;
- canonical AI interaction records;
- canonical AI audit event;
- context orchestration;
- UI;
- billing;
- retention policy;
- RAG.

## Acceptance

- tables exist with canonical naming;
- no Human messaging reuse;
- tenant isolation;
- creator-private capability;
- RLS;
- CRUD tests;
- deny tests;
- migration tested;
- no I2–I8 leakage.

---

# I2 — Authorization and Visibility

## Objective

Enforce the ratified access model.

## Required

- current customer role handling;
- active organization requirement;
- creator-private visibility;
- cross-org denial;
- every-read reauthorization;
- consultant relationship handling if within ratified I2 scope;
- staff permission boundaries;
- explicit auditor/PE denial where applicable;
- API + RLS enforcement.

## Current state

`CLOSED — VERIFIED PASS at 177dff5`

## Acceptance

Independent OHD PASS + PO closure.

---

# I3 — Controlled Read-Only Tools

## Status

**CLOSED — VERIFIED PASS**

**Verified application/remediation revision:** `651f8c1aa60c635ec1e4da482cfcd651d6657fe8` (`651f8c1`)

**Independent OHD verification:** `PASS — I3 REMEDIATION VERIFIED`

**OHD report commit:** `7faaa57`

**PO closure:** recorded 2026-09-21

## Objective

Provide deterministic, controlled read-only access to authoritative CarbonTally data.

## Ratified tools

```text
report_lookup
report_version_lookup
report_evidence_lookup
calculation_snapshot_lookup
```

## Required

- closed registry;
- validated inputs;
- current authorization;
- resolved-object organization recheck;
- bounded results;
- deterministic serialization;
- explicit statuses;
- reference semantics;
- no arbitrary SQL;
- no mutation;
- no LLM dependency.

## Current state

`IMPLEMENTED; REMEDIATION VERIFICATION PENDING`

The known `report_evidence_lookup` real-wiring defect and circular import defect must be independently re-verified as fixed.

---

# I4 — AI Interaction + Canonical Audit

## Status

`NOT_AUTHORIZED`

## Future scope

- Layer 2 interaction persistence;
- provider/model attribution;
- truthful usage metadata;
- answer status;
- tool-call provenance;
- canonical audit event;
- dormant AI table decision;
- interaction-to-audit reference;
- durable reconstruction.

## Must not

- alter authoritative carbon facts;
- bypass I2;
- create arbitrary tools;
- introduce RAG;
- create a second audit ledger.

---

# I5 — Context Management

## Status

**`CLOSED — VERIFIED PASS`** (2026-09-22) — authorized 2026-09-21, implemented at `f9d91e1` (report-evidence correction `4d23031`), independently verified by OHD at `cd718d6` (`docs/implementation/phase8/CT-P8-I5-OHD-VERIFICATION-20260922.md`, `I5 VERIFIED PASS — READY FOR PO CLOSURE`), and closed by the Product Owner in `docs/architecture/CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md`. The I5 stage contract is unchanged by this status update.

## Future scope

- bounded conversation context;
- relevance selection;
- compaction;
- summarization if approved;
- stale-context controls;
- provider context budgets.

## Rule

Conversation summaries remain non-authoritative.

---

# I6 — Insight UI

## Status

**`CLOSED — VERIFIED PASS`** (2026-09-22) — authorized 2026-09-22, implemented at `09e2315` (documented revision `ea7ccc2`), independently verified by OHD at `4acc249` (`docs/implementation/phase8/CT-P8-I6-OHD-VERIFICATION-20260922.md`, `I6 VERIFIED PASS — READY FOR PO CLOSURE`), and closed by the Product Owner in `docs/architecture/CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md`. The I6 stage scope below is unchanged by this status update, and the closure authorizes no further work.

## Future scope

- authenticated customer workspace;
- creator-private conversation list;
- conversation view;
- message composer;
- answer status;
- evidence/reference presentation;
- loading/error states;
- provider-unavailable states;
- no unauthorized visibility.

UI is never the security boundary.

---

# I7 — Privacy / Retention / Export

## Status

`NOT_AUTHORIZED`

## Future scope

PO/legal decisions on:

- retention;
- deletion;
- export;
- provider data use;
- residency;
- PII;
- notices;
- regeneration/edit semantics;
- archive/rename.

---

# I8 — Billing / Production Hardening

## Status

`NOT_AUTHORIZED`

## Future scope

- AI usage/cost;
- commercial allowance;
- rate limiting;
- operational monitoring;
- production configuration;
- incident handling;
- backup/recovery;
- performance/SLOs;
- provider resilience;
- production deployment gates.

---

# 36. Cross-Stage Dependency Matrix

| Capability | I1 | I2 | I3 | I4 | I5 | I6 | I7 | I8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Persistence | ✓ | ✓ | | | | | | |
| Authorization | foundation | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Tool registry | | | ✓ | ✓ | | | | |
| AI provider | | | | ✓ | ✓ | | | ✓ |
| AI interaction audit | | | | ✓ | | | | |
| Context | | | | | ✓ | | | |
| UI | | | | | | ✓ | | |
| Retention | | | | | | | ✓ | |
| Billing | | | | | | | | ✓ |
| Production hardening | | | | | | | | | ✓ |

---

# 37. Deployment and Release Rules

No Insight stage may be deployed merely because code exists.

For each stage:

```text
PO authorization
→ Cline implementation
→ Cline report
→ commit/push
→ OHD independent verification
→ OHD report
→ PO closure
→ controlled deployment authorization
→ deployment
→ post-deployment verification
```

Production database migrations require explicit controlled deployment authorization.

No production DB state may be inferred from application deployment evidence.

---

# 38. Repository Governance

Cline must:

- inspect before changing;
- stay within authorized scope;
- preserve unrelated work;
- not modify other branches/checkouts;
- not silently rename existing objects;
- run required tests;
- document implementation;
- commit;
- push;
- stop at blockers.

OHD must:

- inspect independently;
- not repair;
- test real paths;
- document;
- commit/push report;
- stop at FAIL.

PO must:

- authorize;
- decide open questions;
- close verified stages;
- authorize next stage separately.

---

# 39. Definition of Done — Insight as a Whole

CarbonTally Insight is not "complete" merely because the chat UI works.

Full Insight completion requires all applicable stages to be:

- implemented;
- independently verified;
- PO-closed;
- security-tested;
- migration-tested;
- operationally documented;
- observably instrumented;
- privacy/commercial policies resolved;
- production deployment controlled.

The final system must demonstrate:

1. tenant isolation;
2. current authorization;
3. creator-private conversation visibility;
4. deterministic authoritative data access;
5. safe AI explanation;
6. reconstructable tool provenance;
7. canonical audit integration;
8. safe failure states;
9. prompt-injection resistance;
10. no fabricated carbon facts;
11. no unauthorized data disclosure;
12. controlled provider use;
13. truthful usage accounting;
14. controlled retention/deletion/export;
15. production operational readiness.

---

# 40. Acceptance Test Catalogue

## Security

- [ ] cross-tenant access denied
- [ ] inactive organization denied
- [ ] revoked membership denied
- [ ] revoked consultant relationship denied
- [ ] unauthorized staff denied
- [ ] auditor denied unless separately authorized
- [ ] PE denied unless separately authorized
- [ ] forged role denied
- [ ] stored reference cannot grant access
- [ ] LLM cannot grant access

## Data

- [ ] authoritative values originate from CarbonTally records
- [ ] no fabricated calculations
- [ ] no fabricated evidence
- [ ] report state preserved
- [ ] calculation provenance preserved
- [ ] factor provenance preserved

## AI

- [ ] provider outage handled
- [ ] malformed model output handled
- [ ] prompt injection handled
- [ ] indirect injection handled
- [ ] historical poisoning handled
- [ ] no secret leakage
- [ ] truthful provider attribution
- [ ] truthful usage data

## Persistence

- [ ] conversation persistence
- [ ] message persistence
- [ ] creator-private visibility
- [ ] authorization on every read
- [ ] deletion cannot erase canonical audit evidence
- [ ] historical answer not treated as authoritative

## Tools

- [ ] closed registry
- [ ] validated input
- [ ] deterministic execution
- [ ] bounded result
- [ ] explicit status
- [ ] no mutation
- [ ] no arbitrary SQL
- [ ] real repository wiring

## Operations

- [ ] correlation IDs
- [ ] safe logs
- [ ] rate limits
- [ ] provider failure handling
- [ ] monitoring
- [ ] incident response
- [ ] backup/recovery
- [ ] controlled deployment

---

# 41. Open Product Decisions

The following remain PO/design decisions until explicitly closed:

- owner/admin shared conversation visibility;
- consultant conversation access;
- staff support access;
- auditor access;
- PE access;
- retention duration;
- deletion semantics;
- export;
- provider retention/training policy;
- residency;
- subprocessors;
- PII policy;
- legal/privacy notices;
- rename/archive;
- regeneration/edit semantics;
- raw question storage versus hash;
- exact answer-status enumeration;
- exact context/compaction policy;
- dormant AI structure disposition;
- AI credits/allowances;
- provider selection;
- exact performance/SLO targets.

Implementation agents must not invent these decisions.

---

# 42. Explicit Deferred Capabilities

Unless separately authorized, do not implement:

- RAG;
- embeddings;
- vector databases;
- LangChain or another orchestration framework;
- unrestricted retrieval;
- autonomous actions;
- consultant Insight;
- auditor Insight;
- PE Insight;
- broad staff Insight;
- billing;
- retention enforcement;
- export;
- production hardening;
- report lifecycle modification.

---

# 43. Traceability Matrix

| Requirement | Source / authority |
|---|---|
| CarbonTally Insight naming | D2 §3 |
| Persistence | D2 §5 |
| Separate domain | D2 §6 |
| Three layers | D2 §7 |
| Current authorization | D2 §8 + I2 closure |
| Creator-private | D2 §9 + I2 verified behaviour |
| Deterministic-first | D2 §11 |
| RAG deferred | D2 §12 |
| LangChain deferred | D2 §13 |
| Existing provider abstraction | D2 §14 |
| Context rules | D2 §15 |
| Threat model | D2 §16 |
| Provenance | D2 §17 |
| Reporting boundary | D2 §18 |
| Audit package boundary | D2 §19 |
| Privacy open | D2 §20 |
| Billing open | D2 §21 |
| Dormant AI structure | D2 §22 |
| I1–I8 roadmap | D2 §23 |
| I1 boundary | D2 §24 |
| I2 verified state | I2 PO Closure |
| I3 tool catalogue | I3 PO ratification/implementation |
| I3 defect remediation | OHD I3 verification/remediation |
| AI risk alignment | NIST AI RMF / GenAI Profile |
| LLM security alignment | OWASP LLM/GenAI guidance |
| GHG accounting authority | GHG Protocol / CarbonTally calculation architecture |
| Organization-level GHG reporting context | ISO 14064-1 |

---

# 44. Industry-Standard Positioning

This document is an engineering specification, not a certification claim.

It is informed by:

- NIST AI Risk Management Framework;
- NIST Generative AI Profile;
- OWASP Top 10 for LLM Applications;
- OWASP Top 10 Web Application Security Risks;
- GHG Protocol Corporate Accounting and Reporting Standard;
- ISO 14064-1 organization-level GHG quantification/reporting principles.

CarbonTally must not claim compliance, certification, assurance, or conformity with any of these merely because this specification references them.

The relevant standards remain external reference frameworks and must be mapped to actual implemented controls and evidence before any compliance statement is made.

---

# 45. Master Acceptance Principle

The most important acceptance rule is:

> **Insight must never become a second source of truth.**

CarbonTally already has authoritative:

- activity data;
- emission factors;
- calculation services;
- calculation snapshots;
- reports;
- report versions;
- evidence;
- provenance;
- authorization;
- audit records.

Insight is the controlled conversational access layer over those authoritative systems.

The architecture is therefore:

```text
AUTHORITATIVE CARBONTALLY SYSTEMS
             ↓
      CONTROLLED TOOLS
             ↓
       STRUCTURED RESULT
             ↓
      OPTIONAL AI EXPLANATION
             ↓
        USER-FACING ANSWER
```

Never:

```text
USER
 ↓
LLM
 ↓
guessed carbon fact
```

and never:

```text
USER
 ↓
LLM
 ↓
arbitrary database access
```

---

# 46. Final Governance Rule

No implementation agent may interpret this document as permission to implement every section at once.

The Master Specification defines the **destination and constraints**.

The active PO authorization defines the **current allowed work**.

At any point:

```text
Master Specification
        +
Current PO Authorization
        +
Repository Reality
        +
Independent Verification
        ↓
Allowed Implementation
```

If these disagree, stop and escalate to the PO rather than guessing.

---

# 47. Final Status

**CarbonTally Insight Master Specification:** `v1.1 — I3 VERIFIED / PO-CLOSED — READY FOR PO RATIFICATION AS MASTER SPECIFICATION`

**Current verified implementation reality:**

- I2: `CLOSED — VERIFIED PASS`
- I3: `IMPLEMENTED — REMEDIATION VERIFICATION PENDING`
- I4–I8: `NOT AUTHORIZED`

**Immediate next PO gate:**

> Separate PO authorization decision for I4.

**I3 closure evidence:**

> OHD `PASS — I3 REMEDIATION VERIFIED` at `651f8c1`; verification report committed as `7faaa57`.

**No I4 implementation is authorized by this document alone.**

---

# 48. Version 1.1 Change Log — 2026-09-21

Version 1.1 incorporates the completed I3 remediation re-verification and PO closure.

## 48.1 I3 closure

I3 is now formally recorded as:

> **I3 CLOSED — VERIFIED PASS at `651f8c1`.**

Evidence:

- Cline remediation/application revision: `651f8c1aa60c635ec1e4da482cfcd651d6657fe8`
- OHD independent re-verification: `PASS — I3 REMEDIATION VERIFIED`
- OHD verification report commit: `7faaa57`

## 48.2 Material verification incorporated

The Master Specification now records that OHD independently verified:

- real `get_repositories()` wiring contains `disclosure_projection`;
- `report_evidence_lookup` executes successfully through the real HTTP path;
- D-01 is resolved;
- D-02 circular import is resolved;
- real-path status semantics are correct;
- reference re-resolution is enforced;
- no write path was introduced;
- the wiring tests are sensitive to the pre-remediation source;
- I1/I2 application and migration integrity remains unchanged;
- no I4–I8 functionality was introduced.

## 48.3 Full-suite result

OHD reported:

- I3 + wiring: **35/35 passed**
- Focused I1/I2 + Insight: **63/63 passed**
- Full unit suite: **2,889 collected / 2,877 passed / 4 failed / 0 errors / 8 skipped**

The same four failures were present before remediation and were classified as pre-existing and unrelated to I3 remediation.

## 48.4 Governance consequence

I3 is now closed.

This closure does **not** authorize I4.

I4, I5, I6, I7, and I8 remain **NOT AUTHORIZED** and require separate PO authorization.

## 48.5 PO decision intake — Q1–Q14 and I4 authorisation (2026-09-21)

The Product Owner has resolved the I4 pre-authorisation decisions. Recorded here so
this specification no longer presents them as open; the decision text itself lives in
the dated decision/closure documents under `docs/architecture/` and
`docs/implementation/phase8/`.

| Decision | PO resolution (2026-09-21) |
| --- | --- |
| Q1 — dormant `ai_content_history` | **CLOSED — Option C**: retained unchanged and **outside I4** (`CARBONTALLY_P8_I4_Q1_AI_CONTENT_HISTORY_CLOSURE_20260921.md`). I4 must not read, write, migrate, rename, alter, or reuse it as any Insight store or as the audit ledger |
| Q2 — canonical audit ledger | `public.audit_trail` via the existing `infra/audit_logger.py` + `data/audit.py`; no competing ledger, and `audit_logs`/`processing_audit_trail`/`review_audit_trail`/`activity_logs` are not canonical |
| Q3 — status vocabularies | The closed I3 six-value `ToolStatus` contract is unchanged; I4 keeps a **separate** fourteen-state answer vocabulary |
| Q4 — raw question | Persisted once in the I1 message layer; Layer 2 stores only a content hash (plus references/ids) |
| Q5 — Layer-2 mutability | Append-only/immutable after creation; corrections are new linked records |
| Q6 — tool arguments/results | Allowlisted structured projections only; no raw payloads, secrets or unrestricted result content |
| Q7 — interaction lifecycle | Owned by Layer 2 (I1 stays the conversation/message layer) |
| Q8 — visibility | Creator-private only; no new shared visibility, personas or permissions |
| Q9 — correlation | Immutable `interaction_id` with child `tool_call_id`s, correlatable to the canonical audit event |
| Q10 — idempotency/retry | Bounded retry; no duplicate interaction identities or duplicate logical tool calls; truthful partial-failure state |
| Q11 — provider unavailable | Degraded service, never fabrication: deterministic results are preserved and `provider_unavailable` is returned where provider work is required |
| Q12 — retention/deletion/export | Deferred to I7; not implemented at I4 |
| Q13 — billing/credits | Deferred to I8; not implemented at I4 |
| Q14 — provider/evaluation/SLO | Existing provider abstraction only; truthful attribution; usage/cost may remain NULL; no evaluation platform, RAG, embeddings or orchestration framework |

**Stage status (updated at PO closure, 2026-09-21):** I4 is **`CLOSED — VERIFIED PASS`** at implementation revision `310a62a` (`310a62a5d1a822ae51a8bf33e33302b690265c0a`), independently re-verified by OHD at `6a4fda1` (`docs/implementation/phase8/CT-P8-I4-OHD-REVERIFICATION-20260921.md`, `PASS — I4 REMEDIATION D1-D4 VERIFIED`), and closed by the Product Owner in `docs/architecture/CARBONTALLY_P8_I4_INSIGHT_CLOSURE_20260921.md`. That closure authorizes nothing further: I5–I8 remain **NOT AUTHORISED**, production deployment is **not** implied, and the Q12/Q13 items remain deferred to I7/I8 respectively.

**Stage status (I5 closure, 2026-09-22):** I5 is **`CLOSED — VERIFIED PASS`** at implementation revision `f9d91e1` (report-evidence correction `4d23031`), independently verified by OHD at `cd718d6` (`docs/implementation/phase8/CT-P8-I5-OHD-VERIFICATION-20260922.md`, `I5 VERIFIED PASS — READY FOR PO CLOSURE`), and closed by the Product Owner in `docs/architecture/CARBONTALLY_P8_I5_INSIGHT_CLOSURE_20260922.md`. This note supersedes the I5 part of the I4 sentence above, factually and for status only: I5 is now authorized and closed, I6 remains PO-authorized at product level but implementation-deferred, and I7/I8 remain **NOT AUTHORISED**; production deployment remains **not** authorized. The I5 context budget remains **20,000 characters by default and configurable**, and is **not** an immutable hard ceiling (O-1 PO decision, 2026-09-22). No I5 technical requirement, and no I6/I7/I8 decision, is changed by this note.

**Stage status (I6 closure, 2026-09-22):** I6 is **`CLOSED — VERIFIED PASS`** at implementation commit `09e2315` (documented revision `ea7ccc2`), independently verified by OHD at `4acc249` (`docs/implementation/phase8/CT-P8-I6-OHD-VERIFICATION-20260922.md`, verification ID `P8-I6-OHD-VERIFY-20260922-01`, `I6 VERIFIED PASS — READY FOR PO CLOSURE`), and closed by the Product Owner in `docs/architecture/CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md`. This note supersedes the I6 part of the I5 sentence above, factually and for status only: I6 is now authorized and closed, **no blocker remains for I6 closure and no remediation was required**. Verification observation A-1 (a non-existent implementation digest recorded in the I6 report) was accepted as **nonblocking** and corrected in the report as a documentation-only change; A-2…A-5 were accepted as **nonblocking** without remediation. Four items remain **future PO decisions** outside I6 (`evidence_line_item` resolvability, a consultant/internal-staff entry point, `org_viewer` execution rights, and pagination). **I7 and I8 remain NOT AUTHORISED**, production deployment remains **not** authorized, and no permission, tool, API, schema, authorization or I1–I5 contract is changed by this note.

---

# Appendix A — Source References

## CarbonTally internal authority

- Phase 8 D1 Discovery — persistent conversation and AI auditability discovery
- Phase 8 D2 PO Ratification — CarbonTally Insight architecture
- I2 PO Closure — Authorization & Visibility
- I3 PO Tool Catalogue Ratification
- I3 Implementation Report
- I3 OHD Verification Report
- CarbonTally Reporting Lifecycle Specification
- CarbonTally Product and Report Ratification
- CarbonTally AI Assistant Architecture
- CarbonTally security/governance instructions
- CarbonTally repository implementation and tests

## External reference frameworks

- NIST AI RMF 1.0
- NIST AI RMF Generative AI Profile
- OWASP Top 10 for LLM Applications 2025
- OWASP Top 10:2025
- GHG Protocol Corporate Accounting and Reporting Standard
- ISO 14064-1:2018

---

# Appendix B — PO Ratification Checklist

Before this document becomes the sole Master Specification, PO should explicitly confirm:

- [ ] Product definition accepted
- [ ] Architecture accepted
- [ ] Persistence model accepted
- [ ] Authorization model accepted
- [ ] Creator-private visibility accepted
- [ ] Tool catalogue accepted
- [ ] AI boundary accepted
- [ ] Security model accepted
- [ ] Provenance model accepted
- [ ] Audit model accepted
- [ ] Industry-standard alignment accepted
- [ ] Open decisions correctly preserved
- [ ] I1/I2/I3 current states correctly represented
- [ ] No unauthorized I4–I8 work is implied
- [ ] Master Specification becomes authoritative for future stage prompts

**End of Master Specification**
