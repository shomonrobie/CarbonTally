# CarbonTally — Phase 8 D2: CarbonTally Insight PO Ratification

**Prompt ID:** `CT-P8-CARBONTALLY-INSIGHT-D2-PO-RATIFICATION-20260912`
**Document type:** Product Owner ratification — **documentation only**
**Date:** 2026-09-12
**Starting HEAD:** `8608d13ea937ae5d90e5056a813ebdb6cf124806` (branch `main`, 9 ahead of `origin/main`)
**Authority:** Product Owner
**Status:** `D2 PO RATIFIED — CARBONTALLY INSIGHT ARCHITECTURE READY FOR I1 IMPLEMENTATION AUTHORISATION`

> **I1 implementation is not performed by this task.** This document ratifies decisions. It
> creates no table, migration, RLS policy, route, service, tool, prompt, provider binding, UI
> or billing rule. The next step is a separate, bounded **I1** implementation prompt.

---

## 1. Purpose

To formally record the Product Owner decisions for **CarbonTally Insight** — the persistent
conversational carbon-intelligence capability — following:

* the Phase 8 Ask CarbonTally persistent conversation and AI auditability discovery (D1);
* the Phase 8 report catalogue / lifecycle / product ratification;
* the Phase 8 open-decision closure and implementation authorisation package.

This document:

1. records the **product naming decision** (CarbonTally Insight);
2. ratifies **persistence**, the **separate-domain** decision, and the **three-layer model**;
3. ratifies the **authorization boundary**, the **initial persona/surface/visibility** scope,
   and the **consultant/staff/auditor/PE deferrals**;
4. ratifies **deterministic-first**, **RAG deferred**, and **LangChain deferred/not required**;
5. ratifies the **AI authority boundary**, **context rules**, **threat model**,
   **tool provenance**, the **reporting relationship**, and the **audit-package boundary**;
6. records the **privacy/retention/export**, **billing/allowance**, and **dormant AI table**
   items as explicit open decisions;
7. states the **staged plan (D1→D2→I1…I8)** and the **I1 authorisation boundary**;
8. acknowledges the **R-1 terminology conflict** in the canonical AI architecture;
9. states the **explicit non-goals** and the **final status**.

This document does **not** reopen any previously ratified decision and does **not** authorise
implementation.

---

## 2. Source and discovery documents

| Document | Role in this ratification |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_ASK_CARBONTALLY_PERSISTENT_CONVERSATION_AND_AI_AUDITABILITY_DISCOVERY_20260912.md` | **D1 discovery** — the primary architectural evidence base (repository-traced findings, reuse/new-build classifications, staging recommendation) |
| `docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` | Canonical AI assistant design (personas, tool registry, injection defence, PE boundary, provider abstraction, phases 1–7). **Contains the wording superseded by R-1 (§25)** |
| `docs/architecture/CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` | Ratified report lifecycle; **§29** AI-assisted narrative boundary; **§30 Ask CarbonTally Dependency**; **§35** S0–S8 sequence |
| `docs/architecture/CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md` | Ratified **§6** assurance positioning; **§7** auditor/reviewer boundary; **§18 Ask CarbonTally Boundary**; **§19** AI narrative boundary; **§22** PO decision register; **§24** open PO decisions |
| `docs/architecture/CARBONTALLY_PHASE8_OPEN_DECISION_CLOSURE_AND_IMPLEMENTATION_AUTHORISATION_20260912.md` | Ratified baseline, the report-table RLS correction, the **§7 S1 boundary**, and the **§14/§15** authorisation matrix |
| Repository source (verified in D1) | `backend/infra/llm_client.py`, `backend/infra/ai_runtime.py`, `backend/services/ai_document_extraction.py`, `backend/api/v3_messaging.py`, `backend/data/messaging.py`, `backend/domain/audit.py`, `backend/data/audit.py`, `backend/data/reporting.py`, `backend/api/v3_pe.py`, `backend/api/admin_audit.py`, `supabase/migrations/*` |

### 2.1 Consistency check performed before ratification

Every D2 decision below was checked against the source documents above. **No material conflict
was found.** Specifically:

* The D1 "separate conversational domain" finding is **already ratified** independently in
  `PRODUCT_AND_REPORT_RATIFICATION` §18.1 (*"the two must **not** share tables, routes or
  services. A chat-*like* UI is permitted; a chat *data model* is not"*).
* The D1 LLM prohibitions are **already ratified** in §18.3 and §19.2, and in
  `REPORTING_LIFECYCLE_SPEC` §29.2.
* The D1 deterministic-first recommendation is **already ratified** in
  `REPORTING_LIFECYCLE_SPEC` §29.4 (*"deterministic template first"*) and is extended here to
  Insight.
* The D1 audit-package recommendation matches the package's existing `not_assurance` contract.
* The only conflict found is the **R-1** wording issue in the canonical AI architecture, which
  is recorded (§25) rather than silently resolved.

---

## 3. Product naming decision

### 3.1 Ratified working product name

# CarbonTally Insight

**CarbonTally Insight** is the ratified **working customer-facing product name** for the
conversational carbon-intelligence capability. It replaces the earlier working customer-facing
name **"Ask CarbonTally."**

### 3.2 Terminology distinction (normative)

| Layer | Term | Status |
|---|---|---|
| Customer-facing / product | **CarbonTally Insight** | **Provisional product/capability name** |
| Technical / domain | `ask_conversations`, `ask_messages`, `ask_interactions` (as proposed in D1 §10.1) | **Unchanged technical domain terminology** |
| Internal shorthand | "Ask" | Permitted internally; **not** customer-facing |

> **"CarbonTally Insight" is the working customer-facing product name, while `ask_*` remains
> the technical domain terminology unless a later implementation decision changes it.**

### 3.3 Trademark / clearance caveat (mandatory)

The name **"CarbonTally Insight" is provisional and is NOT represented as trademark-cleared.**

* No name/trademark clearance has been performed.
* This document makes **no** legal, trademark, availability, or registrability claim.
* The name is subject to future trademark/name clearance and may change.
* Therefore **no** product copy, marketing material, or public surface may state or imply that
  the name is cleared, registered, or available.

### 3.4 What this naming decision does NOT authorise

* **No** rename of tables, routes, classes, modules, or packages.
* **No** migration, schema change, or code rename.
* **No** new namespace introduction.
* **No** change to the `ask_*` technical naming (see §3.2).

### 3.5 Naming prohibitions (expressly excluded)

* **"CarbonTally Copilot"** — **must not** be used as the product name.
* **"Carbon Insights"** — **must not** be used as the primary product name.

### 3.6 Migration/alias note for future authoring

Where earlier documents, prompts, or code comments say "Ask CarbonTally", they refer to the same
capability that is now product-named **CarbonTally Insight**. This is a **labelling** change
only. A later controlled documentation pass may introduce the product name in
customer-facing contexts; **this task performs no such pass** (§26).

### 3.7 User-experience framing

The product name describes an **intelligence capability**, not a chat surface. Product
positioning must present Insight as evidence-backed analytical assistance over CarbonTally data
(§4), never as a general-purpose chatbot (§4.3).

---

## 4. CarbonTally Insight definition

### 4.1 Ratified concept

**CarbonTally Insight is intended to become a first-class CarbonTally intelligence capability.**

Its purpose is **evidence-backed analytical assistance across CarbonTally data**. It is
**NOT** merely a generic chatbot.

### 4.2 Intended user experience (conceptual, normative)

```text
User
 → CarbonTally Insight
   → intent / query understanding
     → controlled CarbonTally tools
       → authorization / scope / RLS / domain layer
         → authoritative CarbonTally data
           → structured result
             → AI explanation
               → answer + evidence / references
```

This preserves the already-ratified conceptual architecture
(`PRODUCT_AND_REPORT_RATIFICATION` §18.2) and adds the explicit evidence/reference output that
D1 established.

### 4.3 Representative intended questions (illustrative only)

* "What was our CO₂e emission on 3 January 2025?"
* "What were our Scope 1, 2 and 3 emissions?"
* "Which contributors drove the increase?"
* "Show me the evidence behind this figure."
* "Show me the calculation behind this result."
* "Which emission factor was used?"

These are **representative examples of intent**, not a specification.

### 4.4 Tool catalogue — explicitly not decided here

> **The exact future tool catalogue remains an implementation/design concern and MUST NOT be
> invented during this ratification task.**

Constraints that any future catalogue **must** satisfy (ratified):

* tools are **controlled** and server-side;
* tools are **read-only** initially (D2 §23 I3);
* tools are **authorization-checked** against the caller's current scope (D2 §8);
* tools return **only** fields the caller's role may already see;
* report-reading tools must additionally satisfy `REPORTING_LIFECYCLE_SPEC` §30.3 (version and
  state must be stated; a `DRAFT`/`REVIEWED`/`CHANGES_REQUESTED`/`REJECTED` version must never be
  presented as approved or final; every report-reading tool call must be audited).

### 4.5 What Insight is not (normative)

Insight is **not**: a document repository; a reporting engine; an assurance/verification
capability; a replacement for Human ↔ Human messaging; an unrestricted database or document
search; a system of record; a source of carbon facts.

---

## 5. Persistence decision

### 5.1 PO decision

# YES — CarbonTally Insight conversations are persistently stored.

### 5.2 Rationale (ratified)

Persistence supports:

* **conversational continuity** — the user can return to an investigation;
* **investigation and dispute resolution** — how an answer was produced is reconstructable;
* **user context** — the capability can be useful across sessions;
* **operational support** — support can understand what the user asked;
* **AI interaction auditability** — tool invocations and authoritative references are recorded;
* **reconstructability** — question → authorized tool call → authoritative result →
  reference/provenance → AI explanation.

### 5.3 The binding invariant (normative)

> ### Conversation history is NOT authoritative carbon data.

Stored conversation text must **never** become the source of truth for:

* emissions;
* calculations;
* emission factors;
* evidence;
* provenance;
* report facts;
* authorization.

**Historical answers must never be trusted as authoritative merely because they were previously
generated.** Every authoritative value must be obtained from the authoritative CarbonTally record
at answer time, through an authorized, controlled tool call.

### 5.4 Consequence for the answer pipeline (normative)

* A stored answer is **conversational output**, not evidence.
* Where an answer states a figure, the authoritative value remains the underlying
  calculation/report/evidence record.
* Where stored history conflicts with current authoritative data, **current authoritative data
  wins**, and the discrepancy must be stated rather than silently repeated.
* Where two stored answers disagree, neither is authoritative.

### 5.5 Naming for the persisted domain

The persisted structures are the `ask_*` domain (technical) representing the
**CarbonTally Insight** capability (product). See §3.2.

---

## 6. Separate-domain decision

### 6.1 PO decision

# YES — CarbonTally Insight must remain a separate conversational domain.

### 6.2 Ratified prohibitions

* **DO NOT** reuse the existing Human ↔ Human messaging tables for Insight conversations.
* **DO NOT** store Insight messages in the human messaging domain.
* **DO NOT** share message persistence, message semantics, or audit interpretation.
* **DO NOT** share authorization assumptions between the two.

### 6.3 The two domains are semantically distinct

| | Human ↔ Human messaging | CarbonTally Insight |
|---|---|---|
| Relational shape | **Human ↔ Human** | **Human → CarbonTally analytical intelligence** |
| Substrate | `conversations` / `messages` / `conversation_participants` (Supabase Realtime) | **Own bounded domain** (`ask_*`) — does not exist yet |
| Semantics | sender/receiver, read receipts, delivery, typing, participants, attachments | one human actor + a system actor, tool invocations, authoritative references, answer status |
| Governance | relationship/membership/capability rules | controlled tools over the authorized API surface |
| Permissions | existing messaging permission model | its own scope model (§8) |

### 6.4 Explicit acknowledgement of the discovery visibility finding

> **The D1 finding that inserting Insight messages into the human messaging domain could cause
> incorrect visibility is expressly acknowledged and is a primary reason for this decision.**

Concretely (repository-verified in D1): `MessagingRepository.list_conversations_for_org()`
filters on `organization_id` **only**, with no `conversation_kind` predicate; entity threads are
kept out of that list solely by storing `organization_id = NULL`. Therefore an Insight
conversation carrying an organisation id **would appear in that organisation's human messaging
list** for every member. This is a correctness *and* confidentiality defect, not a stylistic
preference.

### 6.5 What may be shared later (permitted, not authorised here)

A **chat-like UI** is permitted — meaning shared presentation conventions/components — but a
**chat data model is not**. Human messaging must remain a distinct product capability with its own
semantics and permission model.

### 6.6 Relationship to the earlier ratification

This decision **restates and reinforces** the already-ratified
`PRODUCT_AND_REPORT_RATIFICATION` §18.1. No prior decision is reopened or contradicted.

---

## 7. Three-layer persistence model

### 7.1 Ratified conceptual separation

CarbonTally Insight persistence has **three distinct layers**. They must not be collapsed.

#### Layer 1 — Conversation history

Human-readable conversation state:

* conversation;
* messages;
* role/actor semantics (user / assistant / system);
* timestamps;
* relevant lifecycle metadata (title, status).

**Purpose:** user context, continuity, customer experience, follow-up questions.
**Lifecycle:** normal user-facing lifecycle (rename/archive/delete policy remains **OPEN** — §20).

#### Layer 2 — AI interaction record

Machine/audit-oriented record of:

* user question;
* interpreted request (intent);
* tools invoked;
* tool results / references;
* model/provider execution (provider, model, and model version where truthfully known);
* answer status;
* usage/cost metadata **where available**;
* result/reference hashes **where appropriate**.

**Purpose:** reconstruct what CarbonTally did, which controlled tools ran, and which
authoritative data supported the answer.
**Lifecycle:** retained under an audit-style policy; **not** removed by conversation deletion.

#### Layer 3 — Canonical CarbonTally audit event

The **authoritative** audit trail remains the existing canonical CarbonTally audit ledger.

**Purpose:** platform-level, cross-domain, tamper-evident evidence that an interaction occurred.
**Lifecycle:** append-only; not user-mutable.

### 7.2 Ratified prohibitions

* **DO NOT** turn conversation history into the audit trail.
* **DO NOT** duplicate authoritative carbon records merely to make conversations auditable.
* **DO NOT** treat conversation content as evidence.

### 7.3 The intended reconstruction chain (normative)

```text
Question
 → authorized tool call
   → authoritative result
     → reference / provenance
       → AI explanation
```

### 7.4 Layer interaction rule

Layer 2 may **reference** Layer 3 and the authoritative records by stable reference/hash.
Layer 1 may be deleted or archived without destroying Layer 2 or Layer 3. Layer 3 never depends on
Layer 1.

### 7.5 Exact schema deferred

The precise shape of each layer (columns, constraints, indexes) is **deferred to implementation
design** — Layer 1 at I1, Layer 2 and its audit integration at I4. D1 §10.1 proposed a shape; this
ratification ratifies the **three-layer concept**, not a field list.

---

## 8. Authorization boundary

### 8.1 The governing rule

> ### Conversation persistence NEVER grants authorization.

### 8.2 Ratified requirements (normative)

Every read of a stored Insight conversation, and every future tool invocation, **MUST** be
**re-authorized against the user's current permissions and scope**.

Historical conversation context **cannot** grant access to:

* another organization;
* another entity;
* another customer;
* restricted evidence;
* restricted reports;
* restricted calculations;
* PE portfolio data;
* future auditor-only information.

### 8.3 Categorical prohibition

**Cross-tenant leakage is categorically prohibited.**

### 8.4 Stored references are not grants

Stored references are **pointers / provenance records, NOT authorization grants.** A stored
reference to a report, calculation, snapshot or evidence record must be **re-resolved against
current authorization** before any content is exposed.

### 8.5 Required implementation shape (normative)

Future implementation **MUST** preserve the following order of operations:

```text
server-side authorization
 → scope resolution
   → RLS / domain controls
     → controlled tool execution
```

### 8.6 The LLM is never an authorization boundary

The LLM must never be relied upon to decide what a user may see, and must never be given a path
that bypasses the order in §8.5.

### 8.7 Supporting ratified positions

* `PRODUCT_AND_REPORT_RATIFICATION` §22.2 **D-10** — scope determines *which* data an action may
  target; **RBAC alone never grants unrestricted access**.
* `PRODUCT_AND_REPORT_RATIFICATION` §22.2 **D-11** — the frontend is UX only; authorization is
  **server-side**; deny-by-default.
* AGENTS.md §44 — the frontend is never the security boundary.
* AGENTS.md §67 — RLS is a core security layer and must not be disabled or bypassed to make an
  operation work.

### 8.8 Revocation semantics (normative)

Where an access relationship ends (for example a consultant-client grant is revoked), access to
existing Insight conversations under that relationship must end with it. Persistence must not
create a durable, unauthorized read path.

---

## 9. Initial persona / surface / visibility

### 9.1 Ratified initial scope

| Dimension | Ratified initial decision |
|---|---|
| **First Insight persona** | **Customer user** |
| **First Insight surface** | **Customer workspace** |
| **Initial conversation visibility** | **Private to the conversation creator** |

### 9.2 Visibility rule (normative)

**Do NOT automatically make** another customer user, customer administrator, consultant, staff
member, or auditor able to read another user's Insight conversations.

* Default visibility = **creator only**.
* Owner/Admin shared visibility remains a **future product decision** and is **not** ratified
  here.
* No shared-visibility implementation is authorised by this task.

### 9.3 Consequence for the future RLS design (normative)

Insight persistence must be capable of enforcing **both** an organisation scope **and** a
creator-level predicate. This means a tenancy key alone is not sufficient; the visibility model
must be expressible in the persistence/authorization design at **I1/I2**.

### 9.4 Scope of the initial surface

The initial surface is the **customer workspace** only. No consultant workspace, PE workspace,
staff console, admin surface, or auditor surface is in the initial scope (§10).

### 9.5 Role behaviour within the customer organisation (initial)

| Customer role | Initial Insight behaviour (ratified direction) |
|---|---|
| Owner | May use Insight in their own organisation; sees own conversations only |
| Admin | May use Insight in their own organisation; sees own conversations only |
| Member | May use Insight subject to their existing permissions; sees own conversations only |
| Viewer | Read-oriented use subject to their existing permissions; sees own conversations only |

No role gains the ability to read another user's conversations in this initial scope. Any
additional role-specific capability is a later, separate decision.

### 9.6 What "private to the creator" does not mean

It does **not** mean the creator owns authoritative data, and it does **not** bypass
organisation/tenant scoping. A conversation is scoped to **(organisation, creator)**, and every
read is re-authorized (§8).

---

## 10. Consultant / staff / auditor / PE boundaries

### 10.1 Consultant — DEFERRED

* Consultant access to customer Insight conversations is **DEFERRED**.
* **Do not** implement consultant conversation access in the initial foundation.
* Consultant Insight capability (if later authorised) must follow the existing consultant
  operating model and active-grant scoping, and must never read another user's private
  conversations by default.

### 10.2 Internal staff — DEFERRED

* Staff support access to customer Insight conversations is **DEFERRED**.
* **Do not** implement unrestricted staff access.
* If a staff capability is later authorised, it must be an **explicit, named capability**, not a
  by-product of staff identity. (AGENTS.md §14: do not use "admin" as a universal permission
  shortcut.)

### 10.3 Auditor / Assurance Reviewer — DEFERRED

* Auditor Insight access is **DEFERRED**.
* The previously ratified assurance boundary remains unchanged
  (`PRODUCT_AND_REPORT_RATIFICATION` §6 and §7):
  * CarbonTally is **not** an independent auditor, verifier, assurance provider, certification
    body, or regulatory certification authority;
  * the future auditor capability is an **assurance-review function**;
  * auditor access must be **explicitly scoped and authorized later** (organisation / entity /
    report / version — never global);
  * the reviewer may not edit, approve, or finalize.
* No auditor role, table, invitation model, API or UI exists today, and none is created here.
* The Auditor Insight access model remains open decision **A-AUD**
  (`PRODUCT_AND_REPORT_RATIFICATION` §24.2).

### 10.4 PE — DEFERRED, with no Insight capability

* PE users **do NOT** receive CarbonTally Insight in this initial capability.
* **Do not** build PE Insight access.
* **Do not** expose customer Insight conversations through PE portfolio reporting.
* This is consistent with the already-ratified absolute PE document boundary
  (`CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` §7.5) and with PE having no report surface
  (D1 verified: `backend/api/v3_pe.py` contains zero `report` references).

### 10.5 TERM-1 — terminology clarification required (recorded, not resolved)

> **Clarification item.** CarbonTally's ratified architecture uses **PE = Processing Entity**
> (AGENTS.md §8; and `PRODUCT_AND_REPORT_RATIFICATION` §16 "PE Admin Reporting"). The D2 prompt
> heading reads "Private Equity". The **substance** of the decision — no PE Insight access and no
> exposure of customer Insight conversations through PE portfolio reporting — maps correctly onto
> **Processing Entity** in this repository's established usage, and is recorded that way in §10.4.

If "Private Equity" was intended to denote a **distinct investor-side/third-party persona**, that
persona does not exist in the ratified CarbonTally actor model and would require a separate PO
decision. This document does **not** invent such a persona, and does **not** assume the two are
the same beyond the boundary stated in §10.4.

**Status:** `PO CLARIFICATION REQUIRED (non-blocking for I1)`.

---

## 11. Deterministic-first decision

### 11.1 PO decision

# Deterministic-first architecture.

### 11.2 Ratified rule

Where CarbonTally can answer a question through **authoritative structured data and deterministic
domain services**, those services provide the **authoritative result**. The LLM may **explain**
that result.

### 11.3 Degrade-safe requirement (normative)

If the LLM/provider is **unavailable**, the architecture must be capable of returning an
appropriate **deterministic result/status** rather than fabricating an answer.

* The absence of a provider must never produce a wrong number.
* The absence of a provider must never produce an invented narrative presented as fact.
* The worst acceptable outcome of a provider outage is a less fluent — or absent — explanation,
  never a false one.

### 11.4 Required answer-state distinction (normative)

A future implementation **MUST** distinguish at minimum:

| State | Meaning |
|---|---|
| `zero` | The authoritative value is genuinely zero |
| `no_data` | No such data exists for the request |
| `not_authorized` | The caller may not see the data (a denial is **not** an absence) |
| `provider_unavailable` | The LLM stage is unavailable; the deterministic result may still be returned |
| *(other appropriate states)* | e.g. insufficient data, ambiguity requiring clarification, tool failure |

### 11.5 The cardinal rule

> ### Do NOT collapse "no data" into zero.

This reinforces the already-ratified answer-quality requirement
(`PRODUCT_AND_REPORT_RATIFICATION` §18.4: distinguish **zero**, **no data**, **insufficient
data**, **uncertainty**).

### 11.6 Status taxonomy precision deferred

The **exact** status vocabulary may be finalised during implementation. D1 §21.0 proposed a
candidate vocabulary (including `answered`, `insufficient_data`, `tool_failure`, `ungrounded`,
`partial`, `needs_clarification`, `rate_limited`, `refused`). This ratification ratifies the
**requirement to distinguish** these outcomes, not a frozen enumeration.

### 11.7 Relationship to the report lifecycle decision

This extends the already-ratified `REPORTING_LIFECYCLE_SPEC` §29.4 position (**deterministic
template first**) from report narrative to Insight answers.

---

## 12. RAG deferred decision

### 12.1 PO decision

# RAG IS DEFERRED.

### 12.2 Ratified prohibitions (initial foundation)

Do **NOT** implement RAG during the CarbonTally Insight foundation. Do **NOT** create:

* vector databases;
* an embeddings pipeline;
* unrestricted document retrieval;
* unrestricted database retrieval;
* a generic RAG framework;
* an enterprise-wide retrieval corpus.

### 12.3 RAG is not rejected permanently

RAG may be introduced later for genuinely **unstructured knowledge**, such as:

* GHG Protocol material;
* methodology documentation;
* customer policies;
* approved supporting documents;
* reporting-framework knowledge;
* other authorized knowledge sources.

### 12.4 Mandatory constraints on any future RAG architecture (normative)

Any future RAG architecture **MUST** be:

* **authorization-first**;
* **scope-aware**;
* **allowlisted**;
* **provenance-aware**;
* **tenant-safe**;
* **resistant to prompt injection**;
* **separate from authoritative carbon calculations**.

Required order of operations for any future retrieval:

```text
Authorization → Scoped retrieval → Controlled data → LLM
```

Never:

```text
LLM → Unrestricted database / vector store
```

### 12.5 Current-phase precedence (ratified)

> For the current phase: **Controlled CarbonTally tools > RAG** for authoritative
> numerical/structured questions.

### 12.6 Relationship to D1

This ratifies D1 §22.5 (retrieval constraint) and D1 §20.1 item 23 (`DEFER` — scoped retrieval).

---

## 13. LangChain / framework decision

### 13.1 PO decision

# LangChain is DEFERRED / NOT REQUIRED at this stage.

### 13.2 Ratified rule

Do **not** introduce LangChain merely because the product is conversational or agentic.

**Reuse the existing CarbonTally AI architecture:**

* `backend/infra/llm_client.py`;
* `backend/infra/ai_runtime.py`;

and the canonical CarbonTally AI provider abstraction.

### 13.3 Condition for any future framework introduction

A future framework may **only** be introduced if a concrete requirement demonstrates that it
materially improves at least one of:

* safety;
* maintainability;
* tool orchestration;
* evaluation;
* observability;
* reliability;

**without** undermining CarbonTally's authorization and audit boundaries.

### 13.4 Explicit boundary

**No framework migration is authorised by this D2 task.** No new orchestration dependency is
introduced. Nothing is added, installed, or configured.

### 13.5 Relationship to earlier decisions

This matches `REPORTING_LIFECYCLE_SPEC` §29.3 and `PRODUCT_AND_REPORT_RATIFICATION` §17/§19.1:
*"No new LLM client, no direct HTTP calls, no provider SDK in this codebase."*

---

## 14. AI provider boundary

### 14.1 Ratified rule

The **existing provider abstraction remains authoritative.**

* Do **NOT** bind CarbonTally Insight to a specific external provider in this task.
* Do **NOT** introduce a new parallel LLM abstraction.
* Reuse/extend the existing architecture when implementation is later authorised.

### 14.2 The authoritative abstraction (repository-verified in D1)

| Component | Role |
|---|---|
| `backend/infra/llm_client.py` | The single OpenAI/Anthropic-compatible client; injectable transport; every failure surfaces as a typed error |
| `backend/infra/ai_runtime.py` | Environment-gated runtime configuration and **truthful** provider/model attribution (`provider_label()`, `configured_ai_attribution()`); the API key is deliberately never read |
| `backend/services/ai_document_extraction.py` | The established AI boundary conventions (candidate-only output; never a false success; no credentials or raw document content persisted) |

### 14.3 Configuration boundary (normative)

* Provider configuration remains **environment-only**.
* No API key is stored in the database, logged, exposed to the frontend, or committed.
* Attribution must be truthful and recorded per interaction; "configured" must never be reported
  as "AI was used".

### 14.4 Carried-forward implementation gap (recorded, not solved here)

> **Gap:** `LLMClient.complete()` currently returns text only and does **not** expose sufficient
> usage/cost metadata (tokens, cost).

Consequences to carry into implementation design:

* per-interaction token/cost capture cannot be populated today;
* token-based allowance accounting cannot be enforced today.

**Do not silently solve this during D2.** It is recorded as an implementation gap for I3/I8. Until
truthful usage is available, such fields must remain **NULL** rather than fabricated.

---

## 15. Context rules

### 15.1 Ratified principles

Persisted history **may** be used to provide conversational continuity.

However (all normative):

* **old answers are never authoritative** (§5.3);
* historical messages must be **re-authorized** before exposing underlying information (§8);
* only **relevant/minimal context** should be sent to an external provider;
* the **entire conversation history must not be blindly sent** to an LLM;
* context **compaction/summarization thresholds remain an implementation/design decision**;
* conversation summaries, if later introduced, **must not become authoritative carbon facts**.

### 15.2 Explicitly OPEN

> **Exact context-window/compaction rules remain OPEN for later implementation design.**

This includes: how many turns are included; whether a rolling summary is adopted; the summary
trigger threshold; whether a summary is user-visible; and the token budget for each context slot.

### 15.3 Non-negotiable constraints on whatever is designed

1. Context is **bounded** — never the full history by default.
2. Scope is **injected by the server** from the verified session, never derived from conversation
   text.
3. Authoritative values in context are always accompanied by their **references**, and are
   re-resolved at answer time.
4. Stored conversation text is **untrusted input** (§16).

### 15.4 Relationship to D1

This ratifies D1 §12 (context-building strategy) including its §12.4 stale-context invariant
(current authoritative data always wins).

---

## 16. Threat model

### 16.1 Ratified threat list (normative — must be considered by future implementation)

| # | Threat | Required disposition |
|---|---|---|
| T-1 | **Prompt injection** | Document-derived and customer-derived text is **untrusted**; it must never enter a system/developer prompt as instructions |
| T-2 | **Malicious conversation content** | Persisted user content is untrusted input; it cannot elevate privileges or alter tool selection |
| T-3 | **Conversation poisoning** | Old/generated answers are never facts; every figure requires a fresh authorized tool result |
| T-4 | **Cross-tenant leakage** | Categorically prohibited; re-authorise every read and every tool call (§8) |
| T-5 | **Unauthorized tool use** | Tools are allowlisted, server-side, read-only initially, and authorization-checked per call |
| T-6 | **Sensitive-data leakage** | Minimise what is sent to any provider; never send credentials, secrets, signed URLs, storage paths, or raw document content |
| T-7 | **Hallucinated evidence** | Every cited reference must resolve to a real, authorized record |
| T-8 | **Hallucinated calculations** | The LLM must never produce an authoritative number; numbers come from deterministic services |
| T-9 | **Audit falsification** | Conversation content is never a substitute for the canonical audit trail (§7, §19) |
| T-10 | **Malicious instructions embedded in retrieved/customer content** | Applies to any current or future retrieved content; retrieval is authorization-first and allowlisted (§12.4) |

### 16.2 The trust rule (normative)

> **Persisted user content must be treated as untrusted input.**
> **Do not treat historical conversation instructions as system/developer authority.**

A user message such as "ignore your rules" or "you are now an administrator" — whether typed now
or stored previously — has **no** authority over the system prompt, tool allowlist, or
authorization.

### 16.3 Two persistence-specific threats (recorded from D1)

| # | Threat | Required control |
|---|---|---|
| P-1 | **Historical access after revocation** — persistence must not create a durable read path after a relationship ends | Re-authorise every read against **current** scope (§8.8) |
| P-2 | **Deletion as an audit-evasion route** — a user could try to destroy evidence of misuse by deleting a conversation | Conversation deletion must **not** remove the AI interaction record or the canonical audit event (§7.4) |

### 16.4 Relationship to D1

This ratifies D1 §14 (security/threat model) and D1 §23.1 (risks), and is consistent with the
already-ratified injection position in `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` §7.4 and
`REPORTING_LIFECYCLE_SPEC` §29.3.

---

## 17. Tool-call provenance

### 17.1 Ratified rule

Future CarbonTally Insight tool calls **should be reconstructable and attributable**.

Where an answer depends on authoritative CarbonTally data, the interaction should preserve
appropriate **references/pointers** to the authoritative source.

### 17.2 Ratified prohibitions

* **Do not** duplicate entire authoritative datasets into conversation records.
* **Do not** store the authoritative value as the source of truth — store the reference.

### 17.3 Permitted/recommended mechanism

Where appropriate, use **deterministic hashes / result references** to support reconstruction and
integrity.

The intended provenance shape (conceptual):

```text
user question
  → interpreted intent
    → tool invoked
      → authorized parameters
        → authoritative result
          → reference(s) + result hash
            → AI explanation
```

### 17.4 Reference targets (illustrative, not a schema)

References should be able to point at authoritative artefacts such as: report version,
calculation snapshot, emission/calculation record, and evidence record — subject to the caller's
authorization at resolution time.

### 17.5 Exact schema deferred

> **Exact schema is deferred to implementation design** (I4).

This ratification ratifies the **provenance requirement**, not a field list. D1 §11.2 proposed a
candidate minimum field set; that proposal is not ratified as a schema.

### 17.6 Integrity convention

Where hashing is used, it must follow the platform's **existing** hashing convention (for example
the integrity hashing already present in the audit/evidence package) rather than introducing a
second, competing hashing scheme.

### 17.7 Report-state provenance (already ratified)

For any report-reading tool, provenance must additionally carry **version identity and lifecycle
state**, per `REPORTING_LIFECYCLE_SPEC` §30.2/§30.3: an answer must state the version and its
state, must never present `DRAFT`/`REVIEWED`/`CHANGES_REQUESTED`/`REJECTED` as approved or final,
and every report-reading tool call must be audited.

---

## 18. Reporting relationship

### 18.1 Permitted future assistance (ratified direction)

CarbonTally Insight **may eventually assist with**:

* report interpretation;
* evidence discovery;
* report preparation;
* narrative assistance;
* report investigation.

### 18.2 Binding constraint

> ## CarbonTally Insight MUST NOT bypass the ratified reporting lifecycle.

### 18.3 AI-generated narrative is candidate-only

AI-generated narrative remains **candidate-only**, consistent with the already-ratified
`PRODUCT_AND_REPORT_RATIFICATION` §19 and `REPORTING_LIFECYCLE_SPEC` §29.

### 18.4 AI cannot (normative denylist)

Insight/AI **cannot**:

* approve reports;
* finalize reports;
* alter authoritative carbon facts;
* alter calculations;
* alter factor provenance;
* bypass report versioning;
* bypass approval;
* bypass frozen final versions.

### 18.5 The reporting lifecycle remains authoritative

The ratified reporting lifecycle remains the **authoritative workflow**:

```text
GENERATE → DRAFT → REVIEW → APPROVE → FINAL → FROZEN PDF
```

Six stored states; approved/final immutable; post-approval change requires a new version;
approval is Owner+Admin, version-bound, audited, and **not assurance**.

### 18.6 Report-state exposure requirement (already ratified)

Any future report-reading tool must expose **explicit, machine-readable version state** and must
comply with `REPORTING_LIFECYCLE_SPEC` §30.3 rules 1–6, including:

* never presenting a `DRAFT`/`REVIEWED`/`CHANGES_REQUESTED`/`REJECTED` version as approved or final;
* stating the version and its state when quoting report content;
* respecting the caller's authorization scope (a Viewer cannot see internal comments; a PE user
  has no report access at all);
* auditing every report-reading tool call.

### 18.7 Relationship to the audit package

Authoritative report facts, calculations, evidence and provenance remain sourced from the
authoritative records — never from conversation content (§5.3, §19).

---

## 19. Audit-package boundary

### 19.1 PO decision

# CarbonTally Insight conversations are NOT included in the standard audit package by default.

### 19.2 Rationale

The audit/evidence package remains focused on:

* authoritative evidence;
* calculation / provenance;
* workflow history;
* readiness.

Mixing conversational narrative into an **evidence** artefact would blur the boundary between
conversational output and evidence, contrary to §5.3 and §7.2.

### 19.3 Verified existing contract (repository-verified in D1)

The existing audit/evidence package:

* declares itself a `carbontally_audit_evidence_package` (versioned);
* carries an explicit **`not_assurance`** notice;
* contains authoritative calculation snapshots with factor provenance and integrity hashing;
* contains workflow history and readiness;
* contains **no** AI/conversation content today.

### 19.4 Permitted future consideration (not authorised here)

A future **customer-controlled export**, or a **support/audit-specific Insight export**, may be
considered later. This is recorded as an open follow-up item and is **not** authorised by this
task.

### 19.5 Explicit boundary

**Do not modify the audit package in this task.** No change to its contents, contract, notice,
version, or hashing.

### 19.6 No assurance claim

Nothing in the Insight capability may state or imply that CarbonTally audits, verifies, certifies,
or provides assurance, and no Insight output may be labelled as assurance
(`PRODUCT_AND_REPORT_RATIFICATION` §6.3).

---

## 20. Privacy / retention / deletion / export — OPEN

### 20.1 Ratified status

These remain **OPEN** for future implementation design. This task establishes **no** final policy.

### 20.2 Explicitly not invented here

> **Do NOT silently invent final policy** for any of the following.

| # | Open item |
|---|---|
| PR-1 | retention period (conversations) |
| PR-2 | hard vs soft deletion |
| PR-3 | user deletion rights |
| PR-4 | organization-level deletion |
| PR-5 | conversation export |
| PR-6 | provider retention |
| PR-7 | provider training / data-use policy |
| PR-8 | data residency |
| PR-9 | subprocessors |
| PR-10 | PII handling |
| PR-11 | legal / privacy notices |

### 20.3 Mandatory design requirement (ratified)

> **The architecture MUST nevertheless be designed so these controls can be introduced later.**

Concretely, this means the future persistence design must:

1. keep conversation content **separable** from AI interaction records and from the canonical audit
   ledger (which the three-layer model already provides, §7);
2. make deletion/retention operations **expressible server-side** without schema rework;
3. avoid embedding provider/legal policy as hard-coded constants;
4. avoid placing conversation content into artefacts whose contracts forbid removal (such as the
   append-only canonical audit ledger — see D1 §15.7).

### 20.4 Coupled open items (cross-references)

* Conversation rename/archive: **PR-EX1** (open).
* Regeneration/edit semantics, including whether an interaction record may ever be overwritten:
  **PR-EX2** (open; the design direction is that regeneration creates an additional interaction and
  never overwrites history).
* Whether the raw question text is stored in the interaction record or only a hash: **PR-EX3**
  (open; coupled to PR-10).

### 20.5 Relationship to previously ratified positions

* `REPORTING_LIFECYCLE_SPEC` §28 (Data Retention and Immutability) and open item **A10** remain
  the report-side counterparts and are **not** modified here.
* AGENTS.md §42 (N3 retention): retention is **configurable**, server-side, managed through the
  appropriate control plane, and **must not weaken auditability, evidence, regulatory traceability,
  or required history**. No duration may be invented.

---

## 21. Billing / AI allowance — OPEN

### 21.1 Ratified status

**AI commercial policy remains OPEN.**

### 21.2 Ratified direction

Existing CarbonTally billing/allowance infrastructure **should be reused where appropriate**
(repository-verified in D1: versioned commercial configuration rules and existing usage counters).

### 21.3 Explicitly not invented here

> **Do NOT invent** any of the following during this ratification task:

* AI credits;
* token prices;
* subscription entitlements;
* quotas;
* overage pricing;
* provider cost policy.

### 21.4 Recorded as a later implementation decision

Billing/allowance is recorded as an **I8** implementation decision (§23).

### 21.5 Carried-forward technical dependency

Per-interaction **token/cost capture is not currently possible** (§14.4). Therefore:

* consumption-based allowance logic cannot be authored until truthful usage data exists;
* any allowance enforcement that depends on token accounting must not be pre-built on fabricated
  figures.

### 21.6 Relationship to previously ratified positions

* `PRODUCT_AND_REPORT_RATIFICATION` open item **A11** (report finalization billable/entitlement
  gated) remains open and distinct.
* No change to any billing plan, credit ledger, or commercial configuration is authorised by this
  task.

---

## 22. Dormant AI data structure decision

### 22.1 Discovery finding (restated)

D1 identified an existing **dormant** AI content-history structure that carries prompt/model/
token/cost/rating fields and is currently **unreferenced by application code**.

### 22.2 PO decision

> **Do NOT automatically reuse or delete it.**
> **No migration is authorised now.**

### 22.3 Recorded requirement

There must be a later, **repository-driven** implementation decision on whether AI interaction
history belongs in:

| Option | Description |
|---|---|
| **Option A** | the new CarbonTally Insight interaction domain (Layer 2); |
| **Option B** | an **extension** of the existing AI table; |
| **Option C** | another bounded structure. |

### 22.4 Governing constraint

Whichever option is chosen, the outcome must **avoid creating duplicate AI-history stores** — a
single bounded home for AI interaction/cost/rating data. AGENTS.md §66 requires that existing
schema be inspected and reused where it already supports the requirement, and AGENTS.md §79
forbids removing legacy structures without an authorised disposition.

### 22.5 Status

### 22.5 Status

`OPEN — implementation decision at I3/I4` (§23). Not resolved by this task.

---

## 23. Staged implementation plan

### 23.1 Ratified sequence

```text
D1  Discovery                                            ← COMPLETE
D2  PO ratification                                      ← THIS TASK
────────────────────────────────────────────────────────────────
I1  Persistent CarbonTally Insight foundation
I2  Authorization and visibility
I3  Controlled read-only CarbonTally tools
I4  AI interaction records + canonical audit integration
I5  Context management
I6  Insight UI
I7  Privacy / retention / export
I8  Billing / production hardening
```

### 23.2 Stage definitions

| Stage | Stage | Scope (ratified direction) |
|---|---|---|
| **D1** | Discovery | Repository-grounded architectural discovery. **COMPLETE.** |
| **D2** | PO ratification | This document. Decisions only — **no implementation**. |
| **I1** | Persistent Insight foundation | Dedicated Insight conversation + message persistence, initial repository/domain layer, minimal create/list/read, organization scoping, explicit RLS design, indexes/constraints, basic API foundation for persistence (§24) |
| **I2** | Authorization and visibility | Apply the ratified creator-private visibility model; complete authorization coverage; ALLOW and DENY verification |
| **I3** | Controlled read-only tools | Intent classification, tool registry, initial read-only tools, references; deterministic path that works without a provider |
| **I4** | AI interaction records + canonical audit integration | Layer 2 interaction record write path; canonical audit event; resolve the dormant-AI-table question (§22) |
| **I5** | Context management | Bounded context; compaction/summarization policy (§15.2) |
| **I6** | Insight UI | Authenticated customer-workspace surface (chat-*like* UI permitted; chat data model is not) |
| **I7** | Privacy / retention / export | The §20 open items |
| **I8** | Billing / production hardening | The §21 open items; usage/cost capture gap (§14.4); rate limiting; production readiness |

### 23.3 Outside the initial foundation (explicitly deferred)

* **RAG** and any advanced retrieval (§12);
* **consultant** access (§10.1);
* **auditor** access (§10.3);
* **PE** Insight (§10.4);
* **broad staff** access (§10.2);
* **LangChain** or any orchestration framework (§13);
* AI-assisted **report narrative** (a separate, later stream — `REPORTING_LIFECYCLE_SPEC` §35 S8).

### 23.4 Non-collision with the report lifecycle stream

The report lifecycle uses the **S0–S8** identifier space
(`REPORTING_LIFECYCLE_SPEC` §35). Insight uses **I1–I8**. These are **different streams** and must
not be conflated (§25.4).

### 23.5 Gating principle (ratified)

Each stage requires **its own** authorisation. No stage may begin merely because the previous stage
completed.

---

## 24. I1 authorization boundary

### 24.1 What this D2 task authorises

This D2 task authorises the following future implementation scope:

# I1 — Persistent CarbonTally Insight Foundation

**ONLY at the next implementation step**, and **only** via a separate implementation prompt.

### 24.2 I1 MAY include (subject to a separate implementation prompt)

* dedicated Insight conversation persistence;
* dedicated Insight message persistence;
* initial repository / domain layer;
* minimal create / list / read functionality;
* organization scoping;
* explicit RLS design;
* appropriate indexes / constraints;
* the basic API foundation required for persistence.

### 24.3 I1 MUST NOT silently expand into

* **I2** authorization/visibility beyond the ratified initial scope;
* **I3** tool execution;
* **I4** AI interaction / audit implementation;
* **I5** context orchestration;
* **I6** frontend;
* **I7** retention / export;
* **I8** billing / provider production;
* report lifecycle changes;
* RAG;
* LangChain;
* consultant access;
* auditor access;
* PE access.

### 24.4 Authorization mechanics (normative)

* **A separate prompt must authorise I1 implementation.**
* **This D2 prompt itself authorises documentation/ratification only — not implementation.**
* If, during I1, a requirement is discovered that belongs to I2–I8, it is **recorded**, not
  implemented.

### 24.5 I1 must respect the ratified constraints

I1 is bound by:

* the three-layer concept (§7) — I1 builds **Layer 1 only**;
* the authorization rule (§8) — every read re-authorised; RLS/scope design explicit; the
  visibility model (§9.2) must be enforceable;
* the naming decision (§3) — `ask_*` technical naming, CarbonTally Insight product naming;
* the separate-domain decision (§6) — **no** reuse of the human messaging tables;
* the privacy-design requirement (§20.3) — retention/deletion must be introducible later;
* the non-goals (§26).

### 24.6 Note on RLS coverage

D1 established that the platform's dynamic tenant-policy mechanism only covers tables carrying an
organisation key, and that some existing tables consequently have incomplete policy coverage
(the open report-side item **A-RLS**). Therefore I1 **must** define its RLS posture explicitly
rather than relying on an implicit mechanism, and must not repeat that gap.

**A-RLS itself remains a report-stream item and is not resolved, changed, or absorbed by this
task.**

---

## 25. R-1 acknowledgement — canonical AI architecture terminology conflict

### 25.1 The conflict (recorded exactly)

The canonical AI architecture document
(`docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md`) contains **older wording**
describing:

* sessions as **session-bounded / short-lived** (its §9 — context described as per-session and
  short-lived in the browser); and
* **logging per conversation event** referencing a session id (its §10.2).

### 25.2 The superseding decision

> **The new PO decision supersedes that product-level persistence direction.**

CarbonTally Insight conversations **are persistently stored** (§5.1), and the AI interaction
record is a **durable** Layer 2 artefact (§7.1) — not merely a per-session log line.

### 25.3 Explicit boundary

> **Do NOT silently rewrite the canonical AI architecture during this task.**

This document does **not** edit that file. No other document is edited by this task.

### 25.4 Recorded reconciliation item

**R-1 is recorded as an explicit documentation reconciliation item for a later controlled update.**

| Item | Detail |
|---|---|
| ID | **R-1** |
| Artefact | `docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` |
| Nature | Superseded product-level persistence wording (§9 session-bounded context; §10.2 per-session logging) |
| Action | Reconciled in a **later controlled documentation pass**, additive, with PO awareness |
| Blocking? | **No** — does not block I1 (I1 builds persistence per this ratification) |
| Owner | Documentation/governance pass, separately authorised |

### 25.5 Related non-collision note (I1–I8 vs S0–S8)

Insight staging (§23) uses **I1–I8**; the report lifecycle uses **S0–S8**. Both must be referenced
with their stream identifier to avoid conflation, in prompts, documents and commits.

---

## 26. Explicit non-goals

This D2 task does **not**:

1. implement I1 (or I2–I8);
2. implement any application code;
3. create, change, or execute any database migration;
4. change any RLS policy;
5. change any API, route, or contract;
6. change any frontend or UI;
7. implement or configure any AI provider;
8. add, install, or configure any dependency (including any orchestration framework);
9. implement RAG, embeddings, vector storage, or unrestricted retrieval;
10. implement any AI tool;
11. change billing, plans, credits, entitlements, or commercial configuration;
12. change the reporting lifecycle, report code, report schema, or report S1 scope;
13. change the audit package, its contents, or its contract;
14. change the canonical audit ledger, its immutability protection, or its taxonomy;
15. change Human ↔ Human messaging (tables, routes, services, permissions, UI);
16. create any consultant, auditor, or PE capability;
17. create any user/role administration capability;
18. rename any table, route, class, module, package, or namespace to match the product name;
19. set or invent any retention period, deletion policy, export policy, price, quota, entitlement,
    or provider policy;
20. make any legal, privacy, trademark, assurance, certification, or compliance claim;
21. modify the roadmap or reopen any frozen UX decision;
22. push to any remote.

---

## 27. PO ratification summary

### 27.1 Decisions ratified by this document

| # | Decision | Ratified position | Section |
|---|---|---|---|
| **R1** | Product naming | **CarbonTally Insight** is the working customer-facing product name (provisional; **not** trademark-cleared); `ask_*` remains technical terminology; no rename/migration | §3 |
| **R2** | Capability definition | Insight is a **first-class evidence-backed intelligence capability**, not a generic chatbot | §4 |
| **R3** | Persistence | **YES** — conversations are persistently stored; conversation history is **NOT** authoritative carbon data | §5 |
| **R4** | Separate domain | **YES** — separate from Human ↔ Human messaging; no shared tables/routes/services/data model | §6 |
| **R5** | Three-layer model | Conversation history / AI interaction record / canonical audit event remain distinct | §7 |
| **R6** | Authorization | Persistence **never** grants authorization; re-authorise every read and every tool call; cross-tenant leakage categorically prohibited | §8 |
| **R7** | Initial scope | Customer user · customer workspace · **private to the conversation creator** | §9 |
| **R8** | Consultant / staff / auditor / PE | All **DEFERRED**; no PE Insight; auditor assurance boundary unchanged | §10 |
| **R9** | Deterministic-first | **RATIFIED**; a provider outage must not fabricate; `zero` ≠ `no_data` ≠ `not_authorized` | §11 |
| **R10** | RAG | **DEFERRED**; not permanently rejected; any future RAG is authorization-first and allowlisted | §12 |
| **R11** | LangChain | **DEFERRED / NOT REQUIRED**; reuse the existing AI architecture | §13 |
| **R12** | AI provider boundary | Existing abstraction remains authoritative; no new parallel abstraction; usage/cost gap carried forward | §14 |
| **R13** | Context rules | Continuity permitted; old answers never authoritative; bounded/minimal context; thresholds **OPEN** | §15 |
| **R14** | Threat model | Ten threats ratified; persisted user content is **untrusted**; P-1 revocation and P-2 deletion-evasion controls required | §16 |
| **R15** | Tool provenance | Reconstructable and attributable; reference/pointer rather than duplication; hashes where appropriate; schema deferred | §17 |
| **R16** | Reporting relationship | Insight may assist but **must not bypass** the ratified reporting lifecycle; AI narrative is candidate-only; the lifecycle remains authoritative | §18 |
| **R17** | Audit package | Insight conversations are **NOT** included in the standard audit package by default | §19 |
| **R18** | Privacy / retention / export | **OPEN** — 11 named items; the architecture must allow the controls later | §20 |
| **R19** | Billing / allowance | **OPEN** — existing infrastructure reused; nothing invented; recorded for I8 | §21 |
| **R20** | Dormant AI structure | Not reused or deleted; repository-driven decision recorded for I3/I4; no migration now | §22 |
| **R21** | Staging | **D1 (complete) → D2 (this task) → I1 … I8**; RAG/consultant/auditor/PE/staff/framework outside the foundation | §23 |
| **R22** | I1 authorisation | **I1 — Persistent CarbonTally Insight Foundation** is the next authorised scope, **only via a separate prompt**; explicit non-expansion list | §24 |
| **R23** | R-1 acknowledgement | The canonical AI architecture's session-bounded wording is **superseded**, **not rewritten**; reconciliation item recorded | §25 |

### 27.2 What remains OPEN (recorded, not resolved)

| ID | Open item | Owner / stage |
|---|---|---|
| PR-1 … PR-11 | retention, deletion, export, provider retention/training, residency, subprocessors, PII, notices | PO + legal · I7 |
| PR-EX1 | conversation rename/archive | PO · I2/I7 |
| PR-EX2 | regeneration/edit semantics | PO · I2/I4 |
| PR-EX3 | raw question text vs hash in the interaction record | PO + legal · I4 |
| — | AI credits / allowance / entitlements | PO · I8 |
| — | dormant AI structure home (option A/B/C) | Repository-driven · I3/I4 |
| — | exact context-window / compaction policy | Design · I5 |
| — | exact answer-status enumeration | Design · I3 |
| — | exact schema for Layer 1 and Layer 2 | Design · I1 / I4 |
| — | Owner/Admin shared visibility | PO · post-I2 |
| **TERM-1** | "Private Equity" vs **Processing Entity** terminology clarification | PO · non-blocking |
| **R-1** | canonical AI architecture documentation reconciliation | Docs pass · non-blocking |
| **A-RLS** | report-table RLS approach | **Report stream** · unchanged by this task |
| **report S1** | `is_current` invariant, `current_version` in listing, docstring drift, regression test | **Report stream** · unchanged by this task |

### 27.3 Explicitly unchanged prior decisions

This ratification reopens nothing. Retained unchanged:

* the report catalogue, assurance positioning, and auditor boundary
  (`PRODUCT_AND_REPORT_RATIFICATION` §6, §7, §22);
* the report lifecycle state machine, approval model, and frozen-artifact model
  (`REPORTING_LIFECYCLE_SPEC` §12–§19);
* the AI narrative candidate-only boundary (`REPORTING_LIFECYCLE_SPEC` §29;
  `PRODUCT_AND_REPORT_RATIFICATION` §19);
* the **S1** report-correctness scope and the `report_versions.is_current` ownership
  (`OPEN_DECISION_CLOSURE` §7, §15);
* the existing architecture rule of **one** aggregation layer, **one** report engine, **one**
  export/PDF layer, **one** evidence vocabulary, **one** authorization contract, **one** audit
  ledger, and **separate conversational domains** (`OPEN_DECISION_CLOSURE` §2).

### 27.4 Stream separation (normative)

> **CarbonTally Insight implementation must NOT be combined with report lifecycle S1.**

* The report S1 stream is **separate** and bounded.
* The `report_versions.is_current` invariant remains **owned by report S1**.
* No report lifecycle code or schema may be modified by Insight work.
* Insight stages are identified **I1–I8**; report stages **S0–S8**.

---

## 28. Final status

# D2 PO RATIFIED — CARBONTALLY INSIGHT ARCHITECTURE READY FOR I1 IMPLEMENTATION AUTHORISATION

**Ratified:** the CarbonTally Insight naming decision, the capability definition, persistence, the
separate-domain decision, the three-layer model, the authorization boundary, the initial
persona/surface/visibility scope, the consultant/staff/auditor/PE deferrals, deterministic-first,
RAG deferred, LangChain deferred/not required, the AI provider boundary, context rules, the threat
model, tool provenance, the reporting relationship, the audit-package boundary, the open
privacy/retention/export and billing items, the dormant AI structure decision, the staged plan, and
the R-1 acknowledgement.

**Verified:** no application code, migration, RLS policy, API, frontend, provider, billing, or
production change was made by this task. Pre-existing dirty and untracked work is preserved. No
push was performed.

> **I1 implementation is not performed by this task.**

### Next step

A separate, bounded **I1 — Persistent CarbonTally Insight Foundation** implementation prompt
(§24). Until that prompt exists, **no Insight implementation may begin**.

### Explicit non-authorisation

This document does not authorise I2–I8, RAG, any orchestration framework, any AI tool, any
provider integration, any frontend work, any billing change, any report lifecycle change, or any
consultant/auditor/PE capability.
