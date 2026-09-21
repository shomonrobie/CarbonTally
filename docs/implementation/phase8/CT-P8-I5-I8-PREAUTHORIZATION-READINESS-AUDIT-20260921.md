# CT-P8-I5-I8-PREAUTHORIZATION-READINESS-AUDIT-20260921

**Read-only forensic pre-implementation / readiness audit for the remaining CarbonTally Insight stages.**
Evidence classes used throughout: `VERIFIED` (repository/code/schema/test evidence) · `DOCUMENTED` (stated in an authoritative specification or decision record, not independently code-traced) · `INFERRED` (reasoned from evidence) · `UNKNOWN / NOT VERIFIED` (evidence absent).

---

## 1. Audit mandate

Determine, independently and code-traceably, **what must be decided, specified, prepared or verified before each of I5, I6, I7 and I8 can receive a bounded implementation authorization**; identify dependencies, blockers, open PO decisions and authorization prerequisites. The audit performs no implementation, makes no PO decision, closes no stage, and does not treat the Master Specification as automatically complete or ratified.

## 2. Governance baseline

`VERIFIED` — stage state at audit time:

| Stage | Status | Basis |
| --- | --- | --- |
| I1 | `CLOSED` | `CARBONTALLY_P8_I1_*` records; tables `carbontally_insight_conversations` / `_messages` present |
| I2 | `CLOSED — VERIFIED PASS at 177dff5` | I2 closure document |
| I3 | `CLOSED — VERIFIED PASS at 651f8c1` | `CARBONTALLY_P8_I3_INSIGHT_CLOSURE_20260921.md` |
| **I4** | **`CLOSED — VERIFIED PASS`** | `CARBONTALLY_P8_I4_INSIGHT_CLOSURE_20260921.md` (commit `725f9f8`); verified implementation `310a62a`; OHD re-verification `6a4fda1` → `PASS — I4 REMEDIATION D1-D4 VERIFIED` |
| I5, I6, I7, I8 | `NOT_AUTHORIZED` | Master Specification §35 stage blocks; §48.5 closure-of-I4 boundary; this audit authorizes nothing |

`VERIFIED` — the release chain enforced by Master Specification §37 is: PO authorization → Cline implementation → Cline report → commit/push → OHD independent verification → OHD report → PO closure → controlled deployment authorization → deployment → post-deployment verification; and "No Insight stage may be deployed merely because code exists." Insight has **never** been deployed to production by any stage (`VERIFIED`: no deployment record in the reachable history of this checkout; the I4 closure explicitly states production deployment is not implied).

## 3. Authoritative HEAD

| Item | Value |
| --- | --- |
| Checkout | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD at audit start | `725f9f864b1678c8c5ddebb4d2eb2fae23149e48` |
| `github/p8-release-reconciled` | `725f9f864b1678c8c5ddebb4d2eb2fae23149e48` (`0 0`, clean tree) |
| I4 verified implementation | `310a62a5d1a822ae51a8bf33e33302b690265c0a` (ancestor of HEAD) |

## 4. Source hierarchy applied

1. `VERIFIED` runtime/code/schema evidence from this checkout (the authority for what exists).
2. `DOCUMENTED` Master Specification v1.1 (`CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION_v1.1_20260921.md`) with its §48.5 decision intake.
3. `DOCUMENTED` D2 PO Ratification (`CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md`).
4. `DOCUMENTED` stage closure/verification records (I1–I4 closures, OHD verification and re-verification reports).
5. `DOCUMENTED` legacy/discovery material (used only where it states a fact about existing code).

`VERIFIED` — where the specification is silent, this audit records `UNKNOWN / NOT VERIFIED` or `PO DECISION REQUIRED`; it does not infer a requirement. `VERIFIED` — where documents conflict, both are quoted and the conflict is reported (§26).

---

## 5. I5 specification audit (context)

**Status:** `DOCUMENTED` §35/I5 = `NOT_AUTHORIZED`. **Future scope (`DOCUMENTED`, §35/I5 lines 1612–1619):** bounded conversation context; relevance selection; compaction; summarization **if approved**; stale-context controls; provider context budgets. **Rule (`DOCUMENTED`, §35/I5 line 1623):** "Conversation summaries remain non-authoritative."

Other substantive requirements that bear on I5:

| Requirement | Source | Class |
| --- | --- | --- |
| Context must be relevant, minimal, bounded, authorization-safe; do not blindly send the full conversation history | §17.1 (lines 889–898) | `DOCUMENTED` |
| **Current authority beats history** — the current authoritative lookup wins over prior conversation text, and the discrepancy should be explained when relevant | §17.2 (900–910) | `DOCUMENTED` |
| **Context cannot grant permission** — the model must not infer organisation scope, role, consultant access, report access or evidence access from conversation text | §17.3 (912–922) | `DOCUMENTED` |
| Exact compaction/summarization policy is **an I5 design decision**; any future summary is context, not authoritative carbon data | §17.4 (924–928) | `DOCUMENTED` |
| Avoid full-history LLM prompts; use controlled context windows | §29 (1276–1295) | `DOCUMENTED` |
| The LLM receives only the minimum information required to explain a result; tool results are structured application data (not instructions) | §16.4 (869–873) | `DOCUMENTED` |
| Prompt-injection defences must include conversation poisoning and stored malicious instructions | §16.5 (875–883) | `DOCUMENTED` |
| `no_data` must not become `zero`; partial answers must state what was and was not established | §26.4, §26.6 | `DOCUMENTED` |
| Exact context/compaction policy is listed as an open item owned by "Design · I5" | §41 (line 1892), D2 §27.2 | `DOCUMENTED` |

**Explicit absences — `UNKNOWN / NOT VERIFIED` (not gaps to be filled by inference):** history depth / message count; ordering and recency rules beyond "bounded"; maximum context size in **tokens or characters** (no unit is specified); whether summaries may be **persisted** (the specification never states that a summary is stored, and §8.2 keeps layer lifecycles separate); who may delete or edit a summary; how stale references are resolved (only the §17.2 principle is stated — the mechanism is unspecified); whether prior **tool results** (as opposed to references/ids) may enter context; whether audit information may enter context; empty/missing-context fallback behaviour; whether context assembly is provider-specific; whether a summary is subject to I7 retention.

**`INFERRED`** — I5 is a *cross-cutting* stage, not an isolated feature: §17.1/§17.2/§17.3 constrain it, §29 constrains its size, §16.4/§16.5 constrain its content and injection posture, and I7 will constrain its retention. Any I5 implementation that ignores §17.3 would create an authorization-by-prompt defect.

## 6. I5 implementation / foundation audit (code)

`VERIFIED` — reusable foundations that exist today:

| Capability | Exact location | What exists |
| --- | --- | --- |
| Conversation retrieval | `backend/data/insight.py` — `list_conversations` (line 197), `count_conversations` (265), `get_conversation` (215) | organisation-scoped, creator-filterable, `LIMIT/OFFSET` paginated, ordering `created_at DESC, id DESC` |
| Message retrieval | `backend/data/insight.py` — `list_messages` (251) | ordinal-ordered, bounded `limit`/`offset`, organisation-scoped |
| Interaction retrieval | `backend/data/insight_interactions.py` — `list_interactions` (252), `count_interactions`, `get_interaction`, `list_tool_calls` (376) | creator-private filter, conversation filter, pagination, ordinal-ordered tool calls |
| Bounded context assembly | `backend/services/insight_interactions.py` — `_bounded_context` (188), `MAX_NARRATION_CONTEXT_CHARS = 2000` (62) | a **single-tool, character-bounded** projection (declared tool fields only), used for narration |
| Truncation precedent | `backend/services/ai_document_extraction.py` — `DEFAULT_MAX_TEXT_CHARS = 20_000` (39), `max_text_chars` (143/157) | established project idiom for bounding provider input by **characters** |
| Provider call surface | `backend/infra/llm_client.py` — `LLMClient.complete(prompt, system=…, temperature=…, max_tokens=…)` | single provider abstraction; `max_tokens` is a *request* parameter only |
| Authorization boundary | `backend/api/insight_authz.py` — `authorize_insight_scope` (206), `conversation_is_visible` (331) | re-authorized per request; the only grant mechanism |
| I4 evidence surface | `backend/data/insight_interactions.py` — interaction + tool-call rows with `question_hash`, `answer_status`, `references`, `metadata` | the per-interaction record I5 would select from |

`VERIFIED` — **what does not exist**: any token-counting utility (`tiktoken`/`count_tokens` — no occurrence in `backend/services` or `backend/domain`); any compaction or summarization code (the only `summar*`/`compact` matches are unrelated: `services/disclosure_projection.py`, `services/automatic_processing.py`, `services/automatic_extraction.py`); any conversation-history assembly; any context cache/store; any provider context-budget configuration.

`VERIFIED` — I4 needs **no change** for I5: the tables already expose creator-private, paginated, ordinal-ordered reads, and I4's audit/tool evidence already carries the correlation ids a context assembler would select on. `INFERRED` — the only I4-adjacent decision I5 might revisit is whether narration context should be assembled by a shared component (currently inlined in `run_interaction`), which is an I5 design choice, not an I4 defect.

---

## 7. I5 open decisions (PO / design authority)

| # | Decision | Why it is required | Evidence |
| --- | --- | --- | --- |
| I5-1 | **Compaction/summarization policy** — whether summaries are produced at all, and by what trigger | §17.4 states this is an I5 design decision; §35/I5 lists summarization only "if approved" | `DOCUMENTED` §17.4, §35/I5 |
| I5-2 | **Summarization approval** — whether summarization is authorized at all | §35/I5 conditions it on approval | `DOCUMENTED` |
| I5-3 | **Context budget unit and size** — tokens or characters, and the maximum | §35/I5 requires provider context budgets; no unit or value is specified; §29 requires controlled windows | `DOCUMENTED` + `UNKNOWN` |
| I5-4 | **History depth / relevance rule** — how many prior messages/interactions, selected by what rule | §17.1 requires bounded, relevant, minimal context but specifies no depth or selection rule | `DOCUMENTED` (principle only) |
| I5-5 | **Whether summaries are persisted**, and if so where | The specification never states that a summary is persisted; §8.2 keeps layer lifecycles separate; persistence would trigger I7 retention | `UNKNOWN / NOT VERIFIED` |
| I5-6 | **Stale-reference handling mechanism** | §17.2 states the principle (current authority wins, explain the discrepancy) but no mechanism | `DOCUMENTED` (principle) / `UNKNOWN` (mechanism) |
| I5-7 | **Whether tool results (not just references) may enter context** | §16.4 limits the LLM to the minimum information to explain a result; no explicit rule for history tool results | `DOCUMENTED` (bounded) / `UNKNOWN` (specific) |
| I5-8 | **Whether audit information may enter context** | §20.3 excludes conversations from the standard audit package; nothing authorizes audit rows as context | `UNKNOWN / NOT VERIFIED` |
| I5-9 | **Empty/missing-context behaviour** and its answer state | §26 lists `no_data`/`insufficient_data`/`needs_clarification`, but no context-specific rule exists | `INFERRED` from §26 + `UNKNOWN` |
| I5-10 | **Multi-turn visibility** — whether context may span conversations | Layer 1 is creator-private per conversation; no cross-conversation rule exists | `UNKNOWN / NOT VERIFIED` |

## 8. I5 authorization readiness

**`READY WITH PO DECISIONS`**

* `VERIFIED` — the foundation exists: creator-private, paginated, ordinal-ordered message/interaction reads; an established character-bounded context idiom; the single provider abstraction; the closed I2 boundary; and I4 evidence carrying correlation ids. No technical blocker was found, and **no I4 change is required**.
* `DOCUMENTED`/`UNKNOWN` — the stage's *parameters* are open. Blocking decisions: **I5-1/I5-2** (compaction + summarization authorization), **I5-3** (budget unit and size), **I5-4** (depth/selection rule), **I5-5** (whether summaries are persisted — this one also sets I7 scope).
* `INFERRED` — non-blocking but should be settled in the same authorization: I5-6 (stale-reference mechanism), I5-7 (historical tool results), I5-10 (cross-conversation context).
* `VERIFIED` — I5 must not weaken §17.3: context may never carry authorization, so any I5 implementation must resolve scope through `authorize_insight_scope` per request, exactly as I4 does.

---

## 9. I6 frontend audit

**Status:** `DOCUMENTED` §35/I6 = `NOT_AUTHORIZED`. **Future scope (`DOCUMENTED`, lines 1633–1643):** authenticated customer workspace; creator-private conversation list; conversation view; message composer; answer status; evidence/reference presentation; loading/error states; provider-unavailable states; no unauthorized visibility — and "UI is never the security boundary" (line 1645).

`VERIFIED` — actual frontend baseline (traced in this checkout):

| Aspect | Finding |
| --- | --- |
| Framework / build | React with Create React App (`frontend/package.json`: `react`, `react-dom`, `react-scripts`, scripts `start`/`build`/`test`/`eject`) |
| UI library / design system | MUI + Emotion (`@mui/material`, `@mui/icons-material`, `@emotion/react`, `@emotion/styled`) with project design tokens at `frontend/src/v3/tokens.css` (the D21 token file) |
| Routing | `react-router-dom` in `frontend/src/App.js` (`BrowserRouter`, `Routes`, `Route`, `Navigate`), with `ProtectedRoute` (`App.js:189`) and role gating via `frontend/src/v3/components/RoleRoute` |
| Application surfaces | `frontend/src/v3/{admin,consultant,customer,messaging,ops,pe,reports,components,__tests__}` plus `api.js`, `utils.js`, `v3.css`; public/marketing surfaces in `frontend/src/public/**` including `public/assistant/**` (the FAQ assistant) |
| Auth integration | `frontend/src/Login.js`, `AuthCallback.js`, `AuthServiceUnavailable.jsx`, `MagicLink.jsx`, `@supabase/supabase-js` dependency |
| API client / state | `axios` dependency and a shared `frontend/src/v3/api.js`; no Redux/Query library is declared (state is component-level + Supabase client) |
| Other UI utilities | `react-hot-toast` (notifications), `framer-motion`, `recharts`, `xlsx`, `react-pdf`, `yaml` |
| Test infrastructure | `@testing-library/{dom,jest-dom,react,user-event}` with CRA's Jest runner; existing specs such as `frontend/src/App.test.js`, `frontend/src/DataSecurity.test.jsx`, and `frontend/src/v3/__tests__/` |
| **Insight UI** | **None.** `grep -rln 'insight' frontend/src` returns **no files** — there is no Insight surface, no interaction view and no Insight API client module |

`INFERRED` — the reusable primitives I6 needs already exist in kind: a v3 role-gated shell to host an authenticated workspace, MUI + D21 tokens for presentation, a shared v3 API client, `react-hot-toast` for error surfacing, and RTL/Jest for tests. `UNKNOWN / NOT VERIFIED` — whether the v3 customer workspace's navigation is the intended I6 entry point, and whether the public FAQ assistant is intended to be reused for Insight presentation (the specification does not say).

## 10. I6 backend dependency audit

`VERIFIED` — the I4/I1 backend contracts I6 would consume already exist in this checkout:

| Needed contract | Where it exists | Notes |
| --- | --- | --- |
| Run an interaction | `POST /api/v3/insight/interactions` (`backend/api/v3_insight_interactions.py:53`) | body: `organization_id`, `conversation_id`, `question`, optional `idempotency_key`, `narration ∈ {none, optional, required}`; returns the outcome envelope incl. `interaction_id`, `lifecycle`, `answer_status`, `narration_state`, `narration_text`, `tool_calls[]`, `references[]`, `replayed` |
| Read one interaction (creator-private) | `GET /api/v3/insight/interactions/{interaction_id}` (`:98`) | 404 for foreign/absent (existence not disclosed) |
| List the caller's interactions | `GET /api/v3/insight/interactions` (`:78`) | creator-private, paginated |
| Conversations / messages | `POST|GET /api/v3/insight/conversations*` (`backend/api/v3_insight.py:120–216`) | create/list/get conversation, append/list messages |
| Answer-state vocabulary | `backend/domain/insight_interaction.py` — `AnswerStatus` (14 states) | separate from I3 `ToolStatus` (6) |
| Reference format | I3 `InsightReference.as_dict()` → `{"kind", "id"}` with kinds `report`, `report_version`, `evidence_line_item`, `calculation_snapshot` | locators, never grants |
| Authorization behaviour | router dependency `require_insight_user` + per-request `authorize_insight_scope` | 401 unauthenticated; 403 denied (incl. PE, auditor, inactive org); 404 for foreign resources |
| Error contract | HTTP 422 for invalid input / unsupported narration; 403/404 as above; persisted failures surface as `answer_status` + `error_class`, never as a fake success |

`VERIFIED` — I6 has **no hard dependency on I5**: it can render a single interaction and the creator's interaction list today. `INFERRED` — a multi-turn conversation view (showing prior context that shaped an answer) is materially better with I5, and any UI that claims to show "what the assistant used" would depend on I5's context-selection policy; that is a UX dependency, not a contract gap. `UNKNOWN / NOT VERIFIED` — whether I6 is expected to expose tool-call evidence (`tool_calls[].arguments/result_metadata/references` are already returned by the read endpoint) or only the reference locators; the specification does not say.

## 11. I6 open decisions (PO authority)

| # | Decision | Why it is required | Evidence |
| --- | --- | --- | --- |
| I6-1 | **Entry point and navigation** — where Insight lives for a customer (new route, customer workspace tab, etc.) | §35/I6 requires "authenticated customer workspace" without naming a location | `DOCUMENTED` (scope) / `UNKNOWN` (placement) |
| I6-2 | **History UX** — conversation list vs interaction list vs both, and how much history is shown | §35/I6 lists "creator-private conversation list" and "conversation view" but not their relationship to I4 interactions | `DOCUMENTED` / `UNKNOWN` |
| I6-3 | **Evidence/reference presentation** — labels, resolution behaviour ("resolve → re-authorize → expose"), and whether references are clickable | §35/I6 "evidence/reference presentation"; references are locators and re-reading requires I2 re-authorization | `DOCUMENTED` + `VERIFIED` (locator semantics) |
| I6-4 | **Answer-state presentation** — how each of the 14 I4 states is shown, including `refused`, `ungrounded`, `insufficient_data`, `rate_limited` (states that this implementation never produces) | §35/I6 "answer status"; §14 enumeration | `DOCUMENTED` / `UNKNOWN` (visual mapping) |
| I6-5 | **Provider-unavailable UX** — what a customer sees when narration is unavailable while a deterministic answer exists | §35/I6 "provider-unavailable states"; Q11 behaviour is implemented server-side | `DOCUMENTED` (requirement) / `UNKNOWN` (design) |
| I6-6 | **Permissions/denial messaging** — wording for 403/404 (must not disclose existence) | §35/I6 "no unauthorized visibility"; I1/I4 return 404 for foreign resources | `VERIFIED` (behaviour) / `UNKNOWN` (copy) |
| I6-7 | **Empty, loading and error states** | §35/I6 "loading/error states" | `DOCUMENTED` (requirement) / `UNKNOWN` (design) |
| I6-8 | **Responsive/mobile acceptance** and **accessibility acceptance criteria** | Master Specification §50 accessibility is referenced by the audit brief; the Master Specification itself does not set I6-specific acceptance levels | `UNKNOWN / NOT VERIFIED` |
| I6-9 | **Replay/lifecycle presentation** — whether `replayed` outcomes and `lifecycle` values are surfaced | the I4 API returns both; the specification does not require their display | `VERIFIED` (available) / `UNKNOWN` (requirement) |
| I6-10 | **Whether the public assistant is reused** for any Insight presentation | Public website and authenticated application are explicitly distinct surfaces (§30 of the operating constitution); the specification is silent | `UNKNOWN / NOT VERIFIED` |

## 12. I6 authorization readiness

**`READY WITH PO DECISIONS`**

* `VERIFIED` — **no backend contract gap**: I1 and I4 endpoints, the 14-state answer vocabulary, the `{kind,id}` reference format, the authorization behaviour and the error contract all exist and are independently verified (I4 closure).
* `VERIFIED` — the frontend has the host shell, design tokens, API client, notification primitive and test infrastructure to build I6, and contains **no** Insight UI yet (clean start, no legacy to unwind).
* `DOCUMENTED`/`UNKNOWN` — the blocking work is **UI/product decision**, not engineering: I6-1 (entry point), I6-2 (history UX), I6-3 (evidence presentation), I6-4 (state presentation), I6-5 (provider-unavailable UX), I6-7 (empty/loading/error), I6-8 (responsive/accessibility acceptance).
* `INFERRED` — I6 may be authorized **before** I5 (it depends on I4 only); if the PO wants multi-turn context visible in the UI, I5 should be authorized first or the I6 scope must explicitly exclude context-dependent presentation.

---

## 13. I7 data/privacy audit (current inventory)

**Status:** `DOCUMENTED` §35/I7 = `NOT_AUTHORIZED`; §21 states privacy/retention/deletion/export are "deliberately OPEN until I7" and that "No retention duration or legal policy may be invented by implementation agents" (line 1065).

`VERIFIED` — Insight-related data that exists today (all in `public`, all additive to the platform):

| Data | Table | Introduced by | Creator-private? | Notes |
| --- | --- | --- | --- | --- |
| Conversations | `carbontally_insight_conversations` | I1 (`20261001000000`) | yes (RLS `created_by = auth.uid()` + `is_org_member`) | `organization_id` `ON DELETE CASCADE`; `title`; timestamps |
| Messages | `carbontally_insight_messages` | I1 | yes | **raw questions and narration text live here** (PO Q4) |
| Interactions | `carbontally_insight_interactions` | I4 (`20261003000000`) | yes | `question_hash`, `request_hash`, `answer_status`, `narration_state`, `provider/model/model_version`, nullable `tokens_used`/`cost`, `metadata`; append-only; `ON DELETE CASCADE` from the conversation and organisation |
| Tool-call evidence | `carbontally_insight_tool_calls` | I4 | yes (via parent interaction) | allowlisted `arguments`/`result_metadata`/`references`, hashes, latency; append-only |
| Canonical audit | `public.audit_trail` | pre-existing (Phase 7 hardening) | no (internal audit surface) | append-only trigger; I4 writes correlation ids/statuses only, no payloads |
| Legacy AI history | `public.ai_content_history` | legacy RC2 baseline | legacy policies (permissive, non-creator-private) | **Q1 CLOSED — Option C**: retained unchanged, outside I4; not read or written by any Insight code |
| Other audit-shaped tables | `audit_logs`, `processing_audit_trail`, `review_audit_trail`, `activity_logs` | pre-existing | n/a | explicitly **not** the canonical Insight ledger (Q2) |

`VERIFIED` — controls that already exist: creator-private RLS on all four `carbontally_insight_*` tables; `anon` REVOKE ALL; `authenticated` SELECT+INSERT only (UPDATE/DELETE revoked); append-only triggers on the I4 evidence tables (independently re-verified in OHD `6a4fda1`); organisation-scoped cascades; server-side per-request re-authorization; `service_role` RLS bypass (the backend's pool, documented in the migration headers and used by every repository).

`VERIFIED` — controls that exist as **precedent** for export: `backend/api/admin_audit.py` already exposes an internal audit surface with `GET /export` (`AuditCsvOut`), `GET /correlation/{correlation_id}` and `GET /{entry_id}`, and `backend/data/exports.py` + `backend/api/v3_exports.py` exist as a general export capability. `UNKNOWN / NOT VERIFIED` — the exact authorization gates, scopes and redaction rules of those existing export paths (not traced in this audit), and whether any of them is intended to be reused for Insight export.

## 14. I7 retention audit

`DOCUMENTED` — the specification provides **no retention duration for any Insight artefact**: §21 lists conversation retention, hard/soft deletion, user deletion rights, organisation deletion, export, provider retention, provider training/data use, residency, subprocessors, PII and notices as open, and §35/I7 repeats them as "PO/legal decisions". `VERIFIED` — the platform already carries configurable retention settings and a retention service (`backend/services/retention.py`; `system_settings` retention keys including `operational_telemetry_retention_days` added by `20260924000000_p8x_x2_operational_telemetry_retention.sql`, whose header enumerates the pre-existing keys `data_retention_days`, `document_retention_days`, `audit_log_retention_days`, `backup_retention_days`).

`VERIFIED` — structural facts a retention/deletion design must respect: (a) I4 evidence is **append-only** (triggers block UPDATE/DELETE even for `service_role`); (b) the I4 repository exposes no `delete`/`save` and raises explicitly; (c) deleting a conversation cascades to its messages, interactions and tool calls; (d) deleting an organisation cascades to conversations/interactions/tool-calls; (e) `audit_trail` is append-only and §8.2 requires that conversation deletion **never** erase the canonical audit record; (f) the I4 closure states I7 retention is not implemented.

**PO DECISION REQUIRED (blocking):** every retention period (conversations, messages, interactions, tool-call evidence, audit records); whether retention is per-organisation configurable or global; whether "retention" for append-only evidence means nothing at all (i.e. indefinite) or a controlled archival path; deletion semantics (hard vs soft) for each table; user deletion rights; organisation deletion behaviour beyond the existing cascades; whether summaries (I5-5) are retained.

## 15. I7 export audit

`DOCUMENTED` — §21 lists export as open; §35/I7 repeats it; §20.3 states conversations are **not** part of the standard audit/evidence package by default; §20.4 forbids placing transcripts/provider payloads in the ledger. `VERIFIED` — an audit CSV export endpoint already exists on the internal admin surface (`backend/api/admin_audit.py` `GET /export`). `UNKNOWN / NOT VERIFIED` — whether an organisation-facing export exists for Insight data, its scope, its format, or its redaction rules.

**PO DECISION REQUIRED (blocking):** who may export (customer owner/admin/member, consultant, staff, auditor); what may be exported (messages, interactions, tool-call evidence, references, audit correlation, provider metadata); format (CSV/JSON/PDF); scope (conversation/organisation/date range); whether export is itself audited; redaction rules; whether raw prompts and narration text are exportable at all (they are the most sensitive Insight content); whether `tokens_used`/`cost` (currently NULL) are exportable; whether export is subject to I8 entitlement checks.

## 16. I7 open decisions (consolidated)

I7-1 retention periods (per artefact) · I7-2 hard/soft deletion semantics · I7-3 user deletion rights · I7-4 organisation deletion semantics beyond existing cascades · I7-5 export authorization and scope · I7-6 export format and content (incl. redaction) · I7-7 provider retention/data-use policy · I7-8 residency and subprocessors · I7-9 PII classification and notices · I7-10 rename/archive semantics · I7-11 regeneration/edit semantics (interacts with I4's append-only rule and OHD observation I-8) · I7-12 whether I5 summaries are retained · I7-13 whether `public.ai_content_history` requires a separate disposition decision (the Q1 closure explicitly defers future disposition to a separate PO decision).

## 17. I7 authorization readiness

**`NOT READY`**

* `DOCUMENTED` — the stage's **entire parameter set** is, by design, undecided: §21 declares it OPEN until I7 and forbids implementation agents inventing durations or legal policy, and §35/I7's scope is a list of PO/legal decisions rather than requirements.
* `VERIFIED` — the *engineering* prerequisites are in place (data inventory, creator-private controls, append-only guarantees, configurable retention settings, an existing retention service and an existing audit-export precedent), so the gap is decision-making, not capability.
* `INFERRED` — a bounded I7 authorization cannot be written responsibly today: without periods, deletion semantics and export scope there is no verifiable acceptance criterion, and I7 also depends on legal input (residency, subprocessors, PII, notices) that is outside engineering authority.
* `VERIFIED` — Q1 remains `CLOSED — Option C`: `public.ai_content_history` is retained unchanged and outside I4 (hence outside any Insight retention path); its future disposition requires a separate PO decision and was not modified by this audit.

---

## 18. I8 billing audit (existing subscription/billing system)

**Status:** `DOCUMENTED` §35/I8 = `NOT_AUTHORIZED`; §22: billing remains OPEN until I8, existing billing/usage infrastructure must be reused, no parallel Insight billing system, and credits/token pricing/quotas/entitlements/overage/provider-cost policy must not be invented (lines 1071–1086).

`VERIFIED` — a **substantial, configurable billing/commercial implementation already exists** in this checkout:

| Layer | Evidence | What exists |
| --- | --- | --- |
| Customer billing API | `backend/api/v3_billing.py` | 10 routes: `GET /me`, `GET /me/credits`, `GET /me/orders`, `GET /me/orders/{order_id}`, `GET /me/payments`, `POST /me/storage/refresh`, `POST /orders/assisted`, `POST /orders/{order_id}/approve`, `POST /orders/{order_id}/cancel`, `POST /managed/orders` |
| Admin commercial API | `backend/api/v3_commercial.py` | `GET /overview`, `GET /config`, `GET /config/{config_key}`, `PUT /config/{config_key}`, `GET /plans`, `GET /plans/{plan_code}` — i.e. **administratively configurable** commercial settings and plans |
| Persistence | `backend/data/billing.py` | `BillingPlansRepository` (:104), `BillingCommercialConfigRepository` (:251), `BillingCreditLedgerRepository` (:342), `SubscriptionsRepository` (:394), `BillingOrdersRepository` (:524), `StorageUsageRepository` (:687), `PaymentRecordsRepository` (:753), `UsageTrackingRepository` (:839 — "Trusted writes to the existing `usage_tracking` table (D37 STANDARD)") |
| Entitlement service | `backend/services/billing.py` | typed billing errors (:33–56), `resolve_registration_mode` (:60), entitlement resolution `get_entitlement` (:87), `ensure_processing_entitlement` (:167), `_standard_usage_this_period` (:192) |
| Schema | `20260824020000_d37_0_billing_security_and_configurable_subscription.sql`, `20260824030000_d37_master_commercial_billing.sql` | plan/config/credit/subscription/order/payment/usage tables and their security posture |
| Admin control plane | `backend/api/admin_*` surfaces (aliases, providers, imports) — the D37 pattern | configuration is administered through backend APIs, not the customer UI |

`INFERRED` — the billing half of I8 is therefore primarily a matter of **deciding** how Insight consumes the existing entitlement/credit/usage machinery (and whether it does so at all), not of building a billing system. `UNKNOWN / NOT VERIFIED` — whether any payment-provider integration (e.g. Stripe) is wired in the reachable code (no provider SDK was traced), whether webhooks exist, and what the D37 `STANDARD` entitlement actually permits; these were not traced in this audit and are **not** to be assumed.

## 19. I8 usage / cost audit

`VERIFIED` — three AI-telemetry homes exist today, and Insight's own record is deliberately empty of usage data:

| Home | Columns | Population |
| --- | --- | --- |
| `report_generation_queue` | `ai_model_used`, `ai_tokens_used`, `ai_cost`, `ai_processing_time_ms` | report generation (legacy/Reports); the RC2 Architecture Freeze calls this the committed FinOps surface |
| `document_processing_queue` | `automation_provider`, `automation_model`, `automation_model_version` | the Gate-5 automation provenance precedent (truthful attribution, no fabrication) |
| `usage_tracking` | `ai_files_processed`, `batch_files_uploaded`, `manual_pages_extracted`, `reports_generated`, `total_storage_bytes` (`UNIQUE (organization_id, usage_month)`) | per-organisation monthly counters, written by `UsageTrackingRepository` |
| **Insight (I4)** | `carbontally_insight_interactions.tokens_used` / `cost` | **always NULL** — the provider abstraction (`ChatCompletionResponse{text, finish_reason}`) exposes no authoritative usage, so Q14 requires NULL rather than fabricated values |

`VERIFIED` — Insight records truthful provider attribution (`provider`, `model`, `model_version`, `narration_state`) only when a provider call actually succeeded; validation errors in `ai_runtime.configured_ai_attribution` prevent guessing. `VERIFIED` — **no Insight usage/credit/entitlement enforcement exists**: I4 performs no entitlement check, no quota check and no per-organisation Insight metering.

**PO DECISION REQUIRED (blocking):** what unit Insight usage is measured in when provider usage is unavailable (requests? bounded per-call units? characters sent? nothing?); whether Insight consumes existing credits/allowances or is unmetered at first; how the reserved Insight allowance interacts with `usage_tracking`; whether NULL usage is acceptable for commercial purposes; whether I4's per-interaction record becomes the usage source of truth or feeds the existing counters.

## 20. I8 production-hardening audit

`DOCUMENTED` — §35/I8 requires: AI usage/cost; commercial allowance; rate limiting; operational monitoring; production configuration; incident handling; backup/recovery; performance/SLOs; provider resilience; production deployment gates. §28 assigns rate limiting to I8 (covering authenticated user, organisation, endpoint/tool, provider usage, burst behaviour, abuse — and "Rate limits must not become an authorization bypass"). §29 says exact SLOs are an I8/product decision and must not be invented. §27 requires observability of correlation, authorization outcome, tool selection, tool success/failure, answer status, provider availability, latency, safe error categories, rate limiting and interaction/audit ids — and forbids logging secrets, tokens, unrestricted customer content or provider payloads. §37 requires the deployment chain and forbids deploying because code merely exists.

`VERIFIED` — existing hardening primitives in this checkout:

| Concern | Evidence | State |
| --- | --- | --- |
| Rate limiting | `backend/middleware/rate_limit.py` — `RateLimitMiddleware(BaseHTTPMiddleware)`, `calls_per_minute: int = 60` | a single global per-client limiter exists; **no** per-organisation, per-endpoint or per-provider limiting |
| Operational metrics | `backend/data/api_metrics.py` — `ApiMetricsRepository.merge_slots` / `read_series` / `count_series_rows` | request metrics persistence exists |
| Alerting / incident signals | `backend/services/operational_alerting.py` — `OperationalAlertingService.evaluate`, `evaluate_and_dispatch`, `_queue_summary`, `_worker_liveness`, `_sla_input`, `_dispatch_one` | queue/worker/SLA-driven alerting exists for existing pipelines; **no** Insight provider-health signal |
| Event correlation | `backend/infra/event_bus.py` (domain events with correlation ids), I4 audit `correlation_id = interaction_id` | correlation primitives exist |
| Telemetry retention | `20260924000000_p8x_x2_operational_telemetry_retention.sql` (`operational_telemetry_retention_days`, default 90, server-side enforced) | a configurable, server-side telemetry-retention mechanism exists (an I7/I8 boundary area) |
| Secrets / provider configuration | `backend/infra/llm_client.py`, `backend/infra/ai_runtime.py` read `CARBONTALLY_AI_*` env vars; §15.2 forbids persisting/logging secrets | configuration is environment-controlled today |
| Deployment gates | §37 + this checkout's history | no Insight stage has been deployed; production migrations require explicit controlled authorization |
| SLOs / backup-recovery / incident runbooks for Insight | none found | `UNKNOWN / NOT VERIFIED` — no Insight SLO document, no Insight runbook, no Insight-specific backup/recovery procedure exists in the repository |

`INFERRED` — the hardening half of I8 is largely engineering work over existing primitives, but it cannot be *accepted* without the PO's performance/SLO targets (§29) and the PO's decision on which Insight signals are operationally required.

## 21. I8 open decisions

I8-1 Insight usage unit when provider usage is unavailable · I8-2 whether Insight consumes credits/allowances or is unmetered initially · I8-3 entitlement enforcement point (per request, per conversation, per organisation period) · I8-4 pricing/tiers for Insight (if any) · I8-5 overage behaviour · I8-6 provider cost policy (absorbed vs passed through) · I8-7 billing-failure behaviour (deny, degrade, or allow with flag) · I8-8 refunds/credit adjustments · I8-9 rate-limit policy per user/organisation/endpoint/provider and the burst rule · I8-10 SLO targets (latency, availability, provider failure budget) · I8-11 which Insight signals must be monitored and alerted · I8-12 production configuration set for Insight (env vars, limits, feature gates) · I8-13 backup/recovery and incident-handling requirements for Insight data · I8-14 deployment-gate criteria for Insight · I8-15 whether `/me/credits` must surface Insight consumption.

## 22. I8 authorization readiness

**`READY WITH PO DECISIONS`**

* `VERIFIED` — the **foundation is unusually strong**: configurable plans/commercial config, credits ledger, subscriptions, orders, payments, storage usage, usage counters, an entitlement service with typed errors, a metrics repository, an alerting service, a rate-limit middleware, event correlation and a telemetry-retention mechanism all already exist; §22 explicitly forbids inventing commercial policy rather than forbidding extension.
* `DOCUMENTED` — the blocking items are **commercial/product decisions**: I8-1…I8-8 (usage unit, credits/allowances, entitlement point, pricing/tiers, overage, provider cost, billing failure, refunds) and I8-10/I8-11 (SLOs and monitored signals), which §29 explicitly reserves to the PO.
* `UNKNOWN / NOT VERIFIED` — payment-provider/webhook integration was not traced, and no Insight SLO/runbook/backup artefact exists; both must be established (or explicitly excluded) before an I8 authorization is written.
* `INFERRED` — I8 could be authorized in two bounded halves if the PO prefers: (a) production hardening (rate limits, monitoring, SLOs, deployment gates) which is engineering-led, and (b) commercial/billing integration which is decision-led. Authorizing only one half must be explicit.

---

## 23. Cross-stage dependency matrix

Rows = dependency; columns = the stage that depends on it.

| Dependency | I5 | I6 | I7 | I8 |
| --- | --- | --- | --- | --- |
| **I1** (conversation/message persistence) | **required** — context is selected from messages | **required** — conversation list/view/composer | **required** — the primary retention subject | independent |
| **I2** (authorization) | **required** (`VERIFIED`: every read re-authorizes; §17.3) | **required** (UI is not the boundary) | **required** (export/retention authorization) | **required** (usage/billing reads are tenant-scoped) |
| **I3** (tools + `ToolStatus`) | optional — references may enter context, never as grants | **required** — reference/evidence presentation | independent | independent |
| **I4** (interaction + tool-call evidence, canonical audit correlation) | **required** — the per-interaction record context draws on | **required** — the API I6 renders | **required** — the main new retention/export subject | **required** — the only per-interaction Insight usage/audit record |
| **I5** (context) | — | optional (multi-turn/history UX; not a contract dependency) | **conditional / unknown** — only if I5 persists summaries (decision I5-5) | independent |
| **I6** (UI) | — | — | optional (an export surface would be rendered by UI if authorized) | optional (`/me/credits` presentation) |
| **I7** (privacy/retention/export) | — | — | — | independent |

The matrix additionally reflects `DOCUMENTED` §36 ("Cross-Stage Dependency Matrix"), which records Authorization as a foundation at I1 and ✓ from I2 onwards, Tool registry at I3–I4, AI provider at I4/I5/I8, AI interaction audit at I4, Context at I5, UI at I6, Retention at I7, Billing and Production hardening at I8. **No dependency in this table is inferred without code or specification evidence; none was added for convenience.**

## 24. Consolidated PO decision register

### 24.1 Already CLOSED

| ID | Decision | Evidence |
| --- | --- | --- |
| Q1 | `public.ai_content_history` — Option C: retained unchanged, outside I4 | `CARBONTALLY_P8_I4_Q1_AI_CONTENT_HISTORY_CLOSURE_20260921.md` (`VERIFIED`) |
| Q2–Q14 | I4 pre-authorization decision set (audit ledger, status vocabularies, raw question, Layer-2 immutability, tool projections, lifecycle, visibility, correlation, idempotency, provider-unavailable, retention→I7, billing→I8, provider/evaluation) | `DOCUMENTED` in Master Specification §48.5 (`VERIFIED` that §48.5 states them) |
| I3 catalogue / `ToolStatus` | Four tools; six-value tool status vocabulary | `DOCUMENTED` + `VERIFIED` (unchanged by I4) |

### 24.2 Deferred by existing decision (do not convert into requirements)

| ID | Deferred item | Deferred to |
| --- | --- | --- |
| Q12 | Retention/deletion/export policy | I7 (§21, §48.5) |
| Q13 | Billing/credits/allowances | I8 (§22, §48.5) |
| O-R1…O-R5 | I4 verification observations (live-fixture requirement, probe defects, pre-existing failures, live HTTP now closed, earlier O-1…O-8 out of scope) | recorded in the I4 closure; **not** work items |

### 24.3 PO DECISION REQUIRED (blocking, by stage)

| ID | Stage | Decision required | Why required | Blocking? | Evidence |
| --- | --- | --- | --- | --- | --- |
| I5-1/I5-2 | I5 | Compaction policy; whether summarization is authorized | §17.4; §35/I5 "if approved" | **Yes** | `DOCUMENTED` |
| I5-3 | I5 | Context budget unit (tokens/chars) and maximum | §35/I5 provider context budgets; none specified | **Yes** | `DOCUMENTED`/`UNKNOWN` |
| I5-4 | I5 | History depth and relevance/selection rule | §17.1 bounded/relevant/minimal | **Yes** | `DOCUMENTED` (principle) |
| I5-5 | I5 | Whether summaries are persisted (and where) | unspecified; drives I7 scope | **Yes** | `UNKNOWN` |
| I5-6/I5-7/I5-10 | I5 | Stale-reference mechanism; historical tool results; cross-conversation context | §17.2 principle only; §16.4 | Recommended | `DOCUMENTED`/`UNKNOWN` |
| I6-1/I6-2 | I6 | Insight entry point/navigation; history UX | §35/I6 scope without placement | **Yes** | `DOCUMENTED`/`UNKNOWN` |
| I6-3/I6-4/I6-5 | I6 | Evidence presentation; answer-state presentation; provider-unavailable UX | §35/I6 | **Yes** | `DOCUMENTED`/`UNKNOWN` |
| I6-6/I6-7/I6-8 | I6 | Denial messaging; empty/loading/error states; responsive + accessibility acceptance | §35/I6; UI is not a boundary | **Yes** | `DOCUMENTED`/`UNKNOWN` |
| I6-9/I6-10 | I6 | Replay/lifecycle presentation; public-assistant reuse | unspecified | Recommended | `UNKNOWN` |
| I7-1…I7-4 | I7 | Retention periods; hard/soft deletion; user deletion; organisation deletion | §21 "deliberately OPEN until I7"; no duration may be invented | **Yes** | `DOCUMENTED` |
| I7-5/I7-6 | I7 | Export authorization/scope; format/content/redaction | §21; §20.3 | **Yes** | `DOCUMENTED` |
| I7-7…I7-12 | I7 | Provider retention/training; residency; subprocessors; PII; notices; rename/archive; regeneration/edit; summary retention | §21, §35/I7 (PO/legal) | **Yes** for provider/residency/PII; Recommended for rename/regenerate | `DOCUMENTED` |
| I7-13 | I7 | Future disposition of `ai_content_history` | Q1 closure §4 | **Yes** (separate decision) | `VERIFIED` |
| I8-1…I8-8 | I8 | Usage unit; credits/allowances; entitlement point; pricing/tiers; overage; provider cost; billing failure; refunds | §22 "do not invent" | **Yes** | `DOCUMENTED` |
| I8-9 | I8 | Rate-limit policy (user/org/endpoint/provider/burst) | §28 | **Yes** | `DOCUMENTED` |
| I8-10/I8-11 | I8 | SLO targets; monitored signals | §29 "must not be invented prematurely" | **Yes** | `DOCUMENTED` |
| I8-12…I8-15 | I8 | Production configuration; backup/recovery; incident handling; deployment gates; `/me/credits` exposure | §35/I8, §37 | Recommended to **Yes** | `DOCUMENTED` |

### 24.4 Not yet specified (no requirement exists to implement)

Retention durations for any Insight artefact · export format/redaction rules · Insight SLO numbers · Insight-specific runbook/backup procedure · Insight usage unit · provider payment integration details (not traced) · I6 visual/UX specification · acceptance criteria for I7 and I8 (unlike I1–I3, §35's I7/I8 blocks state scope without acceptance criteria).

## 25. Implementation readiness matrix

| Stage | Specification | Existing foundation | Dependencies | Open PO decisions | Technical blockers | Authorization readiness |
| --- | --- | --- | --- | --- | --- | --- |
| **I5** | `DOCUMENTED` principles only (§17.1–17.4, §29, §16.4–16.5); no parameters | `VERIFIED` strong: paginated creator-private message/interaction reads, bounded-context idiom, single provider abstraction, I2 boundary | I1, I2, I4 (all `CLOSED`); I4 change not required | 5 blocking (I5-1…I5-5) | **none found** (no token counter exists, but the project idiom is character-bounded) | **READY WITH PO DECISIONS** |
| **I6** | `DOCUMENTED` scope list only (§35/I6); no UX detail | `VERIFIED` React/MUI v3 shell with `tokens.css`, role gating, axios API client, RTL/Jest; **no Insight UI exists** | I2, I3, I4 (all `CLOSED`); I5 optional | 7 blocking (I6-1…I6-8) | **none found** — no backend contract gap | **READY WITH PO DECISIONS** |
| **I7** | `DOCUMENTED` open-by-design (§21, §35/I7); **no durations, no deletion semantics, no export rules** | `VERIFIED` inventory + creator-private controls + append-only guarantees + retention service/settings + admin audit-export precedent | I1, I2, I4; I5 conditional (only if summaries persist) | 13 (I7-1…I7-13), incl. PO/legal items | **none technical**, but **no acceptance criteria exist**, so a bounded authorization cannot be written yet | **NOT READY** |
| **I8** | `DOCUMENTED` (§22, §27–§29, §35/I8, §37) | `VERIFIED` extensive: plans/config/credits/subscriptions/orders/payments/usage + entitlement service + metrics + alerting + rate-limit middleware + telemetry retention | I2, I4; I6 optional | 15 (I8-1…I8-15) | `UNKNOWN`: payment provider/webhook integration not traced; no Insight SLO/runbook/backup artefact | **READY WITH PO DECISIONS** |

No stage is ranked. "READY WITH PO DECISIONS" means a bounded authorization is writable **once** the listed decisions are made; "NOT READY" means the stage's own parameters do not yet exist (I7), so no bounded authorization can be written responsibly.

## 26. Contradictions and unknowns (reported, not corrected)

1. `UNKNOWN / NOT VERIFIED` — **the Q2–Q14 decision text is not a repository artefact.** OHD recorded this (its §1 governance observation and O-6): only Master Specification §48.5 records the resolutions in summary form; the PO decision text itself lives outside the repository. Any later stage relying on a Q-item should cite §48.5 and, if the detail matters, obtain the text.
2. `VERIFIED` **documentation inconsistency (historical).** `CARBONTALLY_P8_I4_Q1_AI_CONTENT_HISTORY_CLOSURE_20260921.md` §5 states "I4 therefore remains NOT AUTHORIZED until the remaining blocking pre-authorization decisions are resolved", while Master Spec §48.5 records the I4 authorization and the I4 closure now records `CLOSED — VERIFIED PASS`. Both documents remain in the tree; the Q1 statement is superseded but not rewritten (deliberately, per §80/§79 discipline). No action is proposed here.
3. `UNKNOWN / NOT VERIFIED` — **Prisma-vs-SQL schema authority remains unresolved** for `public.ai_content_history` (Prisma declares relations/indexes the database does not implement; Q1 left disposition open). Recorded, not resolved.
4. `VERIFIED` — four pre-existing unrelated unit-test failures remain (three in `tests/unit/api/test_review_sla_surfaces.py`, one in `tests/unit/data/test_d17_provider_ownership_migration_revision.py`), unchanged by I4 and by this audit.
5. `VERIFIED` — five of the fourteen I4 answer states (`zero`, `insufficient_data`, `tool_failure`, `partial`, `rate_limited`, `ungrounded` — six, with `partial` produced only for multi-tool mixes) are declared but unproduced; I6's state presentation (I6-4) must be decided with that in mind.
6. `VERIFIED` — no token-counting utility exists anywhere in `backend/services` or `backend/domain`; §35/I5's "provider context budgets" therefore require either a unit decision (characters, following the existing idiom) or new utility code, which is an I5 scope question.
7. `UNKNOWN / NOT VERIFIED` — export authorization/redaction rules of the existing `backend/api/admin_audit.py GET /export` path were not traced; I7 must not assume them.
8. `UNKNOWN / NOT VERIFIED` — whether a payment provider/webhook integration exists for billing was not traced; I8 must not assume it.
9. `VERIFIED` — §35's I7 and I8 stage blocks contain **no acceptance criteria**, unlike I1–I3 (§35/I1 "Acceptance", §35/I2 "Acceptance"). Any I7/I8 authorization must supply them.
10. `DOCUMENTED` — §36 records "Authorization: foundation" for I1 and ✓ for I2–I8; §36 is a capability matrix, **not** a work plan, and was not treated as one.

## 27. Explicit non-authorizations

`VERIFIED` as a statement of this task's scope: this audit performed **no** implementation and authorized **no** stage. Specifically it did not modify application code, migrations, schema, frontend, tests, RLS, billing or production configuration; did not create migrations or tools; did not change I3 or I4 contracts; did not change `public.ai_content_history`; did not implement any part of I5, I6, I7 or I8; did not resolve, decide or close any PO decision; did not access production or a production database; and did not deploy anything. The only repository change is this report.

## 28. Final conclusions

1. `VERIFIED` — I1–I4 are closed (I4 `CLOSED — VERIFIED PASS`, implementation `310a62a`, OHD `6a4fda1`), and close to 4,000 unit tests run green apart from four long-standing unrelated failures.
2. **I5 — `READY WITH PO DECISIONS`.** No technical blocker; the context foundation exists. Blocking decisions: compaction/summarization authorization, context budget unit+size, history depth/selection, and whether summaries are persisted (which also sets I7 scope). No I4 change is required.
3. **I6 — `READY WITH PO DECISIONS`.** No backend contract gap; the frontend shell, design tokens, API client and test infrastructure exist and no Insight UI exists yet. Blocking decisions are UI/product: entry point, history UX, evidence presentation, answer-state presentation, provider-unavailable UX, denial wording, empty/loading/error states, and responsive/accessibility acceptance.
4. **I7 — `NOT READY`.** The stage's entire parameter set is deliberately open (§21) and requires PO/legal decisions; there are no acceptance criteria to verify against. The engineering prerequisites (inventory, controls, append-only guarantees, retention machinery, audit-export precedent) already exist, so the gap is decision-making, not capability.
5. **I8 — `READY WITH PO DECISIONS`.** An extensive configurable billing/commercial/usage/monitoring foundation already exists; the blockers are commercial/product decisions (usage unit, credits, entitlement point, pricing, overage, provider cost, billing failure, SLOs). Payment-provider integration and Insight-specific operational artefacts are `UNKNOWN` and must be established or explicitly excluded.
6. `INFERRED` — the lowest-decision-count path is I5 or I6 (both blocked only by bounded design/product decisions), whereas I7 requires a legal/privacy decision set and I8 requires a commercial decision set. This is an observation about decision load, **not** a recommendation to authorize any stage.
7. `VERIFIED` — the shared cross-cutting prerequisite for every remaining stage is unchanged: authorization must continue to be resolved per request through the closed I2 boundary (`authorize_insight_scope`), references remain locators, and the canonical audit ledger remains `public.audit_trail`.

**NO I5-I8 IMPLEMENTATION WAS PERFORMED OR AUTHORIZED BY THIS AUDIT.**
