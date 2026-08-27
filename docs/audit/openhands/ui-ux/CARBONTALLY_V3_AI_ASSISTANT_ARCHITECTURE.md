# CarbonTally V3 — AI Assistant Architecture & Public Prototype

**Status:** DESIGN + PROTOTYPE (OHD). No production changes.
**Prototype:** `website_candidate/frontend` — floating public assistant on all
public pages.
**Authoritative content sources:** `CARBONTALLY_V3_CUSTOMER_FAQ.md` and
`CARBONTALLY_V3_FAQ_CAPABILITY_MATRIX.md` (this directory).

This document is a design and prototype specification. It does not implement
any authenticated data access. The authenticated assistant is a future Cline
task, built against this architecture.

---

## 1. Executive summary

CarbonTally needs a trustworthy assistant that helps users understand
CarbonTally and, eventually, interact with their authorised CarbonTally
workspace. The assistant must be CarbonTally-specific, permission-aware,
context-aware, evidence-aware, conservative with uncertain information, and
incapable of exposing information outside the user's authority.

The design is a **tiered assistant model** in which each persona receives a
different knowledge and access boundary:

```
PUBLIC ASSISTANT  → public knowledge only (customer FAQ)
CUSTOMER ASSISTANT → the user's own organisation data only
CONSULTANT ASSISTANT → only the consultant's authorised client data
PROCESSING ENTITY ASSISTANT → only assigned/authorised work
CARBONTALLY STAFF ASSISTANT → only according to staff role permissions
ADMIN ASSISTANT → admin-only information
```

The first implementation delivered with this document is the **public
assistant prototype** in `website_candidate/frontend`. It is fully
deterministic (no AI provider, no API key, no network calls) and answers from
the approved target-state customer FAQ with source attribution, conservative
fallbacks, and clear deflection of account/data-specific questions.

**First principle — no data leakage.** The chatbot must never become an
alternate way to bypass CarbonTally permissions. The assistant inherits the
user's existing CarbonTally authorization context. It never reveals another
organisation's data, Processing Entity work outside assignment, staff or
admin information, credentials, secrets, or internal security details. A
frontend restriction is not a security control: every authenticated tool call
is enforced server-side against the same RLS/API policy as the rest of the
platform.

---

## 2. Product vision

A CarbonTally assistant should feel like an extension of the product, not a
generic chatbot bolted on:

- **Answers questions** about how CarbonTally works, in plain English, with
  the source of the answer shown.
- **Guides work** inside the platform: what is waiting, what needs attention,
  what a number means, and why an item is where it is.
- **Never guesses.** When it does not know, it says so and points to a human.
- **Never leaks.** It can only ever surface data the user is already allowed
  to see in the platform, enforced by the platform, not by the chat UI.
- **Is accountable.** Answers and tool calls are logged; customer approval
  decisions and evidence access remain the province of the platform workflow.

The assistant is a **front-end over existing authorization**, never a new
authorization path.

---

## 3. Personas and role boundaries

| Persona | Who | Knowledge boundary | Representative future questions |
|---|---|---|---|
| Public visitor | Anyone on the public site | Public product/service knowledge only (customer FAQ) | "How does CarbonTally work?", "What documents can you process?" |
| Customer Organisation — Owner / Admin / Member / Viewer | A member of an organisation workspace | Only that organisation's data, limited by the member's role | "Which items are awaiting my approval?", "What does this result mean?" |
| Consultant | An external advisor | Only the consultant's authorised client organisations (one client at a time) | "Which of my clients need attention?" |
| Processing Entity (PE) staff | External processing workforce | Only assigned work items; no customer document download | "Which jobs are assigned to me?" |
| CarbonTally staff (Operator / Reviewer / QC / Staff Admin) | Internal operations | Only the queues and customer context their role allows | "What is in the QC queue?" |
| CarbonTally Admin | Internal administrators | Admin-only configuration and system information | "Which processing entity is overloaded?" |

**Role model source.** The CarbonTally actor model is defined in the product
decision register and actor/workspace access model
(`docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md`) and
enforced by the API and RLS layer. The assistant must read its authorization
from that same layer — never maintain its own permission copy.

**Role boundary invariants:**
1. A public user gets public answers only. No tool exists that can reach
   customer data.
2. A customer user gets answers derived only from rows the API/RLS already
   permits them to read.
3. A consultant's queries are scoped to the active client organisation.
4. A PE user gets only assigned work; the assistant cannot expose documents
   outside assignment, and PE staff cannot download customer documents (see
   §7.5).
5. Staff answers are scoped to the staff member's operational role.
6. Admin information is admin-only.

---

## 4. Public assistant

### 4.1 Scope

The public assistant is the first deliverable. It explains the complete
intended CarbonTally service (target state) without exposing internal
implementation status, temporary gaps, the capability matrix, audits, or
internal architecture.

It answers the class of questions in the customer FAQ:

- What is CarbonTally? How does it work?
- What documents/data can CarbonTally process (PDF, scanned, images, CSV,
  Excel)?
- OCR / extraction / deterministic field suggestions / human review
- Mapping and emission factor matching (DEFRA, SEAI, custom factors)
- Calculation, validation, review, QC, customer approval
- Evidence, traceability, reports, exports
- Assisted and managed processing
- Consultants and Processing Entities
- Security and data handling
- What CarbonTally does not do

### 4.2 What the public assistant must NOT claim

The assistant must not claim that CarbonTally:

- is an independent auditor or provides certification;
- guarantees regulatory compliance or emission reductions;
- holds ISO or GDPR certification (unless separately verified and entered
  into the knowledge base);
- supports integrations, countries or emission-factor sources that are not in
  the knowledge base;
- achieves 100% OCR or calculation accuracy;
- provides legal advice or professional assurance.

On anything outside its knowledge:

> "I don't have enough information to answer that reliably. Please contact
> CarbonTally for confirmation."

### 4.3 Prototype implementation (this task)

Location: `website_candidate/frontend/src/public/assistant/`

| File | Purpose |
|---|---|
| `assistantKnowledge.js` | Deterministic local knowledge layer. Single knowledge source: `public/faqData.js` (the approved target-state FAQ content, shared with the `/faq` page). Intents (greeting, capabilities, contact, thanks, account-data deflection), phrase matching, vocabulary aliases, curated compound-term hints, conservative fallback. |
| `AssistantWidget.jsx` | Floating bottom-right widget: launcher, panel (header, messages, suggestions, typing indicator, input), copy / feedback / retry, deep link "See this answer in the FAQ" (`/faq#faq-<id>`), responsive bottom-sheet on mobile, keyboard support. |
| `assistant.css` | Styles built entirely on the `ct-*` design tokens (same palette, typography, radii, shadows as the rest of the public site). |

The widget is mounted once in `App.js` inside the router, so it appears on
every public page. No AI provider is configured and no API key is present in
frontend code; the local layer plays the role the production Assistant
Gateway will fill (same `handleQuery` interface shape).

### 4.4 Conversation UX (public)

- Suggested questions (chips) on welcome and after intent/fallback messages.
- Natural-language questions; answers render with source attribution.
- "See this answer in the FAQ →" deep link to the exact FAQ item.
- Related-question chips when several FAQ items are close.
- Unknown-question fallback with contact CTA and suggestions.
- Copy answer; feedback (helpful / not helpful); ask-again (retry) on the
  latest assistant message.
- Relevant CTAs: "Contact CarbonTally", "Get started" (both → `/contact`),
  "View FAQ" (→ `/faq`).
- Account/data-specific questions are deflected: the public assistant
  explains it cannot see the user's account or data and points to contact.

---

## 5. Authenticated assistant model (design only)

### 5.1 Principle

The authenticated assistant is the same product with a different knowledge
and tool boundary. It is invoked from inside the authenticated application
and receives the caller's real session identity. Every answer that touches
customer data must come from a **tool call executed server-side through the
existing authorized API surface** — never from the model's own memory and
never from a free-form database query.

### 5.2 Customer assistant (per-role)

The assistant answers from the organisation's own data, respecting the
member's role:

- Owner/Admin: full workspace scope.
- Member: their permitted work and items.
- Viewer: read-only results and evidence within their scope.

Representative capabilities (future tools):

- "What is happening with my processing?" → `get_processing_status`
- "Which items are awaiting review?" → `get_pending_reviews`
- "Which documents need attention?" → `get_item_summary` (issues)
- "What does this emissions result mean?" → `get_emissions_result`
- "Why is an item unresolved?" → `get_open_issues` / `get_item_summary`
- "What is waiting for my approval?" → `get_pending_approvals`
- "Which issues are open?" → `get_open_issues`
- "Search my organisation's documents" → `search_organisation_documents`

### 5.3 Consultant assistant

Scoped to the consultant's authorised client organisations and to the active
client context:

- "Which clients need attention?" → `get_client_list`
- "What processing is pending for this client?" → `get_client_processing_status`
- "Which client has unresolved items?" → `get_client_issues`
- "What reports are available for this client?" → `get_client_reports`

Client separation is preserved: only the active client's data is visible in a
single response.

### 5.4 Processing Entity assistant

Scoped to assigned work only:

- "Which jobs are assigned to me?" → `get_assigned_work`
- "Which items need clarification?" → `get_clarification_requests`
- "What extraction/validation work remains?" → `get_processing_item`

A PE assistant has **no** tool that returns full customer documents, and the
portal itself does not permit PE document download (see §7.5).

### 5.5 CarbonTally staff assistant

Scoped to the staff member's operational role (Operator / Reviewer / QC /
Staff Admin):

- "What is in the operations queue?" → `get_operations_queue`
- "Which customer issue is this?" → `get_customer_issue`
- "What is the processing workload?" → `get_processing_workload`

### 5.6 Admin assistant

Admin tools only; admin/system information is not exposed to any other
persona.

---

## 6. Knowledge architecture

### 6.1 Knowledge sources (public)

| Layer | Content | Status |
|---|---|---|
| Public FAQ (`faqData.js`) | Approved target-state customer FAQ (63 items, 13 categories) | Implemented in prototype |
| Public site pages (Platform / Services / Processing / Consultants / Pricing / Glossary) | Public product/service copy | Available for Phase 2 retrieval |
| Public product documentation | Additional public-safe documentation (definitions, method notes) | To be curated |
| Policy / legal pages | Terms, privacy, cookie, carbon-reduction plan | To be curated |

Public assistant knowledge must be a **curated allowlist**, not a crawler.
Only public-safe sources are indexed; the capability matrix, decision
register, audits and internal architecture documents are explicitly excluded.

### 6.2 Authenticated knowledge

Authenticated assistants do not answer from a corpus about the customer's
data. They answer from **tool results** (live authorized API responses) plus
a small fixed public-knowledge base for "how CarbonTally works" explanations.
This keeps the answer surface identical to what the user can already see in
the UI and avoids training/staleness issues for live data.

### 6.3 Knowledge chunk design

For RAG, each chunk carries:

- id (stable slug)
- content (question/answer or section text)
- source label ("CarbonTally Customer FAQ", "CarbonTally Product
  Documentation", …)
- source category (for display)
- allowlist personas (public, customer, consultant, pe, staff, admin)
- canonical URL or entity reference (e.g., FAQ deep link, doc section)
- last-reviewed date and owning doc

### 6.4 Retrieval / RAG design (production)

Provider-neutral pipeline:

1. **Query normalization** — lowercase, punctuation stripping, tokenization,
   light stemming, stopword removal (as in the prototype).
2. **Query expansion** — product vocabulary aliases (DEFRA→emission factor,
   scan→scanned, csv→spreadsheet, …).
3. **Retrieval** — hybrid:
   - lexical scoring (as in the prototype) for precision on product
     vocabulary;
   - vector similarity over chunk embeddings when a model provider is
     configured;
   - curated phrase hints for known ambiguous compound terms.
4. **Rerank** with a small model or rules (persona allowlist filtering,
   source-priority, freshness).
5. **Answer composition** — the model summarises/paraphrases within the
   retrieved chunks; the answer UI shows the source chunk(s).
6. **Grounding check** — if the answer's claims cannot be traced to retrieved
   chunks, the response is treated as ungrounded and converted to the
   fallback message.

Threshold behaviour is conservative: below a confidence/score threshold the
assistant answers "I don't have enough information…".

---

## 7. Tool architecture

### 7.1 Interface

Tools are named functions with typed arguments, executed server-side:

```
Assistant
   │
   ▼
Assistant Gateway
   ├── AuthN context (verified session, user id, role, org id)
   ├── AuthZ gate (permission check against API/RLS policy)
   ├── Tool registry (approved per persona)
   ├── Safety / policy layer (content filters, injection defenses)
   ├── Audit log
   └── Model provider (provider-neutral)
```

The model never receives raw credentials. Tools run with the **caller's**
identity; the tool layer constructs queries exactly as the existing API would
for that user (same RLS).

### 7.2 Tool registry by persona

| Tool | Public | Customer | Consultant | PE | Staff | Admin |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `search_faq` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `search_public_docs` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `contact_carbon_tally` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `get_processing_status` | — | ✅ | ✅* | — | ✅ | ✅ |
| `get_pending_reviews` | — | ✅ | ✅* | — | ✅ | ✅ |
| `get_item_summary` | — | ✅ | ✅* | ✅ | ✅ | ✅ |
| `get_emissions_result` | — | ✅ | ✅* | — | ✅ | ✅ |
| `get_open_issues` | — | ✅ | ✅* | ✅ | ✅ | ✅ |
| `get_pending_approvals` | — | ✅ | ✅* | — | — | — |
| `search_organisation_documents` | — | ✅ | ✅* | — | ✅ | ✅ |
| `get_client_list` | — | — | ✅ | — | — | — |
| `get_client_processing_status` | — | — | ✅ | — | — | — |
| `get_client_issues` | — | — | ✅ | — | — | — |
| `get_client_reports` | — | — | ✅ | — | — | — |
| `get_assigned_work` | — | — | — | ✅ | — | — |
| `get_processing_item` | — | — | — | ✅ | — | — |
| `get_clarification_requests` | — | — | — | ✅ | — | — |
| `get_operations_queue` | — | — | — | — | ✅ | ✅ |
| `get_customer_issue` | — | — | — | — | ✅ | ✅ |
| `get_processing_workload` | — | — | — | — | ✅ | ✅ |
| Admin tools | — | — | — | — | — | ✅ |

`*` Consultant tools are always scoped to the active client organisation.

### 7.3 Tool contract

Every authenticated tool must:

1. Require a verified session.
2. Derive scope (org id, active client, assigned work) from the session —
   never from free text in the prompt.
3. Call the existing authorized API/service functions (single code path).
4. Return only fields the caller's role may read (the API already enforces
   this).
5. Log the tool call (who, when, tool, arguments, result status) to the audit
   log.
6. Be idempotent and read-only for conversational use; any state-changing
   action requires explicit confirmation and stays within the normal
   workflow approval gates.

### 7.4 Prompt-injection defense

- **Document content is untrusted data.** Extracted text, OCR output,
  spreadsheet cells and PDF text are never placed in the model's system
  prompt.
- Retrieved document snippets are treated as data: quoted, length-limited,
  and passed with delimiters so instructions in them cannot reach the model
  as instructions.
- System prompt is immutable by user or document content; user messages are
  treated as untrusted input.
- A user cannot retrieve the system prompt, tool definitions, or other users'
  data by asking.
- Attempts to override permissions, "ignore previous instructions", "act as
  admin", "reveal secrets" are filtered by the safety/policy layer.
- Tool calls are validated against the registry: unknown tools, free-form
  SQL, raw URL fetches and unauthenticated data access are not available.
- Output filters: no credentials/secrets, no URLs to internal tools, no
  internal filenames/paths.
- Rate limiting per user/session per persona; abusive patterns blocklisted.

### 7.5 Processing Entity document access (security verification)

Product Owner decision: external/manual Processing Entities must **not** be
able to download customer documents; they perform extraction, mapping and
validation through the CarbonTally portal.

The production enforcement lives in the backend/storage layer (signed,
scoped, time-limited document access; no direct storage access for PE roles;
API routes reject PE download requests). A hidden UI button is not a security
control; the control is the API/RLS/storage enforcement. **The assistant
must not add a new path that bypasses this**: no PE tool may return raw
document bytes or download URLs, and the model is never given document
content outside the portal's in-browser evidence view. (Verification of the
current backend enforcement is covered by the separate PE security audit;
this document requires that the assistant inherit — never weaken — that
boundary.)

---

## 8. Model / provider abstraction

The repository has not established a specific paid AI provider. The design is
provider-neutral behind an `AssistantGateway` interface:

```
handleQuery(request, context) -> { answer, sources[], toolCalls[], status }
```

Request carries: query, persona, user id, role, organisation context, active
client context (consultant), message history (bounded, e.g. last 20 turns),
and locale. The gateway resolves a model provider per persona/policy (e.g.
public → cheaper/faster model; authenticated → stricter model + tools). The
provider layer supports:

- deterministic/local engine (the current prototype — zero external calls)
- hosted model APIs (provider-agnostic adapter)
- self-hosted models (future)

No provider key is ever embedded in frontend code.

---

## 9. Conversation context

- Bounded rolling context (last N turns) per session.
- Sessions are short-lived in the browser; authenticated sessions bind to the
  user's real session, not a browser cookie.
- Context contains the authorization scope (org/role/active client) injected
  by the gateway — never derived from chat text.
- PII minimization: the knowledge layer and tool outputs are logged without
  unnecessary personal data; full payloads are retained only per the audit
  policy.

---

## 10. Security & audit

### 10.1 Security model

| Concern | Control |
|---|---|
| Authentication | Inherits platform session; gateway verifies identity server-side |
| Authorization | Every tool call goes through the same API/RLS path as the UI |
| Data isolation | Org boundaries enforced by RLS; consultant scoped to active client; PE scoped to assignment |
| Messaging (N1) | Assistant inherits the approved **N1** messaging access model (decision register §24): customer-org internal, consultant active-client, scoped Support/Admin threads, PE operational — **no direct Customer↔PE messaging**; the assistant never creates an alternate messaging or permission path |
| Secrets | Never in frontend, never in prompts, never in logs |
| Injection | See §7.4 |
| Rate limiting | Per user/session/persona |
| Sensitive data | Output filters; no credentials, no internal paths, no other-org data |

### 10.2 Audit logging

Log per conversation event:

- timestamp, session id, user id, persona, org/active-client scope
- query (normalized), answer id/source chunks
- tool calls (tool, arguments, result status, latency)
- feedback events (helpful / not helpful)
- fallback / deflection events (for quality tracking)
- refusal / injection-block events (for security monitoring)

Audit logs are append-only, restricted to admins, and retained per the
platform's data policy. Logs must not contain secret values or raw document
content.

### 10.3 Human escalation

- Fallback answers always offer "Contact CarbonTally" (public) or the
  in-app support/issues flow (authenticated).
- If the assistant cannot resolve a question about a customer's data, it
  points to the issue workflow where a human sees the actual context.
- Escalation creates a normal issue/ticket (same workflow as UI-driven
  issues), not a side channel.

---

## 11. Implementation phases / roadmap

### PHASE 1 — Public FAQ assistant prototype (DONE, this task)

- **UI:** floating widget on all public pages (`website_candidate`); source
  badges, suggestions, feedback, copy, retry, mobile sheet, keyboard support.
- **Backend:** none.
- **APIs/tools:** none (deterministic local layer).
- **Knowledge:** `faqData.js` (approved customer FAQ), target-state wording.
- **Authorization:** n/a (public only).
- **Security:** no data access; account-data questions deflected; no secrets
  in code; no network calls.
- **Audit:** none in prototype (client-side only).
- **Testing:** matcher battery, CDP browser QA (routes, viewports, console,
  overflow), manual PO review.

### PHASE 2 — Production public AI assistant

- **UI:** promote widget into the production frontend's public shell; keep
  the same look (ct-* design system).
- **Backend:** Assistant Gateway service with provider abstraction, rate
  limiting, server-side retrieval.
- **APIs/tools:** `search_faq`, `search_public_docs`, `contact_carbon_tally`
  (server-side, audited).
- **Knowledge:** indexed public FAQ + public site docs; strict public
  allowlist; source citations.
- **Authorization:** public persona only.
- **Security:** injection defenses, output filters, rate limits, secrets
  policy, CSP for the widget.
- **Audit:** server-side logs for queries, sources, feedback, refusals.
- **Testing:** retrieval eval set, injection attack suite, load test,
  accessibility audit.

### PHASE 3 — Customer authenticated assistant

- **UI:** assistant panel inside the authenticated customer app; per-role
  suggestion sets (Owner/Admin/Member/Viewer); "See this in the platform"
  deep links into existing screens.
- **Backend:** gateway session integration; tool layer reusing authorized API
  functions.
- **APIs/tools:** `get_processing_status`, `get_pending_reviews`,
  `get_item_summary`, `get_emissions_result`, `get_open_issues`,
  `get_pending_approvals`, `search_organisation_documents`.
- **Knowledge:** public base + live tool results only.
- **Authorization:** session → role/org; tools enforce RLS.
- **Security:** per-call authorization, injection defense, audit.
- **Audit:** per-call tool audit; feedback; refusal logs.
- **Testing:** permission matrix tests (each role), org-isolation tests,
  injection tests, evals.

### PHASE 4 — Consultant assistant

- **UI:** assistant in the consultant workspace with the active-client
  indicator; suggestions per client.
- **APIs/tools:** `get_client_list`, `get_client_processing_status`,
  `get_client_issues`, `get_client_reports` (always active-client scoped).
- **Authorization:** consultant membership + active client; client separation
  tests.
- **Security/audit/testing:** as Phase 3 plus client-isolation and
  switching-context tests.

### PHASE 5 — Processing Entity assistant

- **UI:** assistant in the PE portal; suggestions for assigned work and
  clarifications.
- **APIs/tools:** `get_assigned_work`, `get_processing_item`,
  `get_clarification_requests`. No document-download path.
- **Authorization:** assignment-scoped; no cross-customer visibility.
- **Security:** verify PE document boundary end-to-end (API + storage);
  injection defense for document-derived text.
- **Audit/testing:** assignment-isolation tests; document-access negative
  tests.

### PHASE 6 — CarbonTally Staff assistant

- **UI:** assistant in internal operations screens.
- **APIs/tools:** `get_operations_queue`, `get_customer_issue`,
  `get_processing_workload`.
- **Authorization:** staff role (Operator/Reviewer/QC/Staff Admin).
- **Security/audit/testing:** role-matrix tests; no customer data beyond
  role scope.

### PHASE 7 — Admin assistant

- **UI:** assistant in admin screens.
- **APIs/tools:** admin-only tools (system config, workloads, teams,
  operational monitoring) — read-only conversational, confirmations for
  state changes.
- **Authorization:** admin role only.
- **Security/audit/testing:** admin-only audit trail; full access-review.

---

## 12. Testing strategy (authenticated phases)

- **Permission matrix tests:** for every tool × persona × role, assert the
  exact row/field visibility matches the API/RLS policy.
- **Isolation tests:** organisation A's user must never obtain organisation
  B data via paraphrase, tool misuse, or injected instructions.
- **Injection tests:** documents/spreadsheet text containing instruction
  overrides, "reveal secrets", "act as admin", and cross-org requests.
- **Fallback tests:** unknown queries return the conservative message.
- **Eval set:** a maintained question/answer set per persona with expected
  sources, run in CI.

---

## 13. Open Product Owner decisions

1. **Provider choice.** No provider is locked in. Decision needed on hosted
   vs self-hosted, and budget/cost-per-turn constraints for Phase 2.
2. **Answer style for authenticated data.** Whether tool-derived answers must
   always carry an inline "see this in the platform" link (recommended), and
   whether the assistant may summarise multiple items.
3. **Public FAQ as source of truth.** Confirm `faqData.js` stays the single
   public knowledge source (recommended) so the `/faq` page and the assistant
   never diverge.
4. **Assistant branding.** Whether the authenticated assistant reuses the
   public "CarbonTally Assistant" name or gets a productised name.
5. **Retention of chat/audit logs.** Retention window and whether transcripts
   may be used for quality tuning.
6. **Customer feedback on answers.** Whether helpful/not-helpful feedback is
   surfaced to the customer org (recommended: yes, aggregated only).
7. **PE document boundary.** Reconfirm that PE assistants will never expose
   raw document content or download URLs (recommended), matching the existing
   PO decision.
8. **Assistant entry points.** Whether the assistant should also appear on
   the landing page only, or all public pages (prototype uses all pages).

---

## 14. Relationship to existing documents

- `CARBONTALLY_V3_CUSTOMER_FAQ.md` — public knowledge content (authoritative
  for the public assistant).
- `CARBONTALLY_V3_FAQ_CAPABILITY_MATRIX.md` — evidence backing every public
  claim; internal, not exposed by the assistant.
- `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` — the
  actor/permission model the authenticated assistant must inherit.
- PE security audit — document-access boundary that the PE assistant must not
  weaken.
- `CARBONTALLY_V3_AUTHENTICATED_UX_BLUEPRINT.md` — the authenticated
  platform UX into which Phases 3–7 integrate.
