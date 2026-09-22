# CT-P8-INSIGHT-ARCHITECTURE-IMPLEMENTATION-GAP-20260922

**Task:** Read-only implementation gap analysis against the Insight architecture reference.
**Kind:** Analysis / forensics. **No implementation.** Nothing in this document authorizes work.
**Date:** 2026-09-22 · **Author:** Cline (implementation agent).
**Legend:** `[FACT]` code/repository-verified · `[REF]` architecture requirement (from the reference) · `[INFER]` reasoned from ≥2 verified facts · `[GOV]` governance decision still required · `[BLOCKED]` cannot be implemented without an unissued decision.

---

## 1. Executive summary

**Verdict:** The implemented Insight capability satisfies the reference's **Phase A** (explain one *identified* verified calculation, with narration and an evidence handoff) and the reference's cross-cutting security requirements **except rate limiting**; it does **not** implement **Phase B** (deterministic date/amount discovery) at all — neither the deterministic discovery operation, nor structured parameter extraction for date/amount, nor the contract that would allow Insight to invoke it; Phases **C** (comparisons) and **D** (contributor analysis) exist as **verified backend capabilities that Insight cannot reach**, and both are additionally unauthorised for Insight.

Consequently the reference's headline customer example — *"Why was my CO2e 20 kg on 1 February 2024?"* — **cannot be answered today**, and the reason is a **contract/governance boundary, not an implementation defect**: the closed, ratified I3 catalogue contains exactly four tools, none of which accepts a date, an amount, a unit or an organization-scoped discovery request, and the I4 answer vocabulary has no `multiple_matches` state. The reference itself documents this expectation (§7: "If the existing public/tool contract cannot support a new status or operation without changing I3, Cline must stop and report the contract gap rather than silently widening I3").

Three findings deserve PO attention beyond the missing discovery capability:

1. **`RateLimitMiddleware` exists but is not registered anywhere** (no import, no `add_middleware`), and `AnswerStatus.RATE_LIMITED` is never produced by any code path. The reference §11 requires bounded limits on customer-facing Insight endpoints "consistent with the already authorized I8-A principles" — the principle is PO-closed, the implementation does not exist, and a concrete I8 authorization is still missing. `[FACT]` `[GOV]`
2. **The AI document-extraction path sends raw, untrusted document text to a model with a system prompt that contains no instruction to ignore embedded instructions** (`services/ai_document_extraction.py`, `_SYSTEM_PROMPT`). Impact is bounded by subsequent determinism (candidate-only output, JSON schema, allowlisted field cleaning, completeness gate, deterministic mapping/validation/calculation before persistence), but the reference §11 prompt-injection requirement is only **partially** met on that path. The Insight narration path itself is clean: no raw document text reaches it. `[FACT]`
3. **No structured parameter extraction exists** — `extract_identifiers()` collects UUIDs only; there is no date, amount, unit, period or scope parser anywhere in the backend or the Insight UI. `[FACT]`

---

## 2. Reference document examined

* `docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22.md` (789 lines; 24,202 bytes; **currently untracked in git** — see §3 and §15 note).
* Read in full. Its own status line is decisive for scope: *"This document is a technical reference and does not by itself authorize implementation, schema changes, new I3 tools, production deployment, or changes to previously closed Phase 8 decisions."* `[REF]`
* Requirement sections used for the matrix: §3 principles, §4 target experience, §5 taxonomy (A–H), §6 six-layer architecture, §7 discovery requirements + response states, §8 matching semantics, §9 LLM contract, §10 evidence architecture, §11 security, §12 prohibitions, §13 industry alignment, §14 phased capability model (Phase A–E), §15 acceptance criteria, §18 explicit design decisions.

---

## 3. Repository / branch / commit examined

| Item | Value |
| --- | --- |
| Authoritative checkout | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| **HEAD examined** | `00822472bfe6d52e0223cb7f546d3b9c0453bc4f` |
| Working tree | clean except the **untracked** reference document (the only untracked path) |
| Remote alignment | `HEAD...github/p8-release-reconciled` = `0 0` |
| Code state vs the OHD-verified viewer HEAD | `git diff --name-only 5d5f7ed..HEAD -- backend/ frontend/ supabase/ prisma/` = **empty** `[FACT]` — so every code fact below is also the state that OHD verified for the Source Evidence Viewer |
| Insight stage closures in force | I1 incorporated · I2 `177dff5` · I3 `651f8c1` · I4 `310a62a` · I5 `f9d91e1` · I6 `09e2315` · Source Evidence Viewer `999e4fb` (PO-closed 2026-09-22) |

**Note (documentation durability, not implementation):** the reference document is not yet committed, so the branch does not contain the document this report analyses. The task instructed me to commit only the report; I did **not** modify or move the reference. `[FACT]`

## 4. Current Insight architecture (as implemented)

`[FACT]` unless stated otherwise.

### 4.1 Surfaces

| Surface | Route / artefact | Evidence |
| --- | --- | --- |
| Insight HTTP API (conversations/messages) | `/api/v3/insight` | `backend/api/v3_insight.py:44` |
| Insight interactions | `/api/v3/insight` (`POST /interactions`, `GET /interactions`, `GET /interactions/{id}`) | `backend/api/v3_insight_interactions.py:36-40,54,79,99` |
| Insight tool surface | `/api/v3/insight/tools` (`GET`, `POST /invoke`, `POST /intent`) | `backend/api/v3_insight_tools.py:24,44,50,67` |
| Router registration | all three routers | `backend/api/router.py:69-71, 241-246` |
| UI route | `/insight`, authenticated only (not in `PUBLIC_ROUTE_PREFIXES`) | `frontend/src/App.js:76, 2072` |
| UI modules | `InsightPage.jsx`, `InsightInteraction.jsx`, `InsightAnswerState.jsx`, `InsightReferences.jsx`, `answerStates.js`, `references.js`, `format.js` | `frontend/src/v3/insight/` |

### 4.2 Orchestration flow (implemented)

`[FACT]` `backend/services/insight_interactions.py::run_interaction` (lines 253-560):

1. input validation (`question` non-blank, ≤ `MAX_QUESTION_LENGTH` 2000; narration mode; idempotency key ≤ 128) — lines 270-278;
2. **I2 authorization** via `authorize_insight_scope` — line 281;
3. conversation exists **and is visible to the caller** (creator-private) else 404 — `conversation_is_visible`, lines 283-287;
4. idempotent replay path keyed by `(organization_id, idempotency_key)` + creator match — lines 289-319;
5. the raw question persisted **once** in the I1 message layer — lines 321-328;
6. **deterministic keyword intent classification** → one of the four ratified tools, or a refusal — line 330; `services/insight_tools.py:157-173`;
7. **identifier extraction = UUIDs present in the question only** — `extract_identifiers`, line 176; tool scoped by `build_tool_input` (lines 179-190), which returns `None` when the required identifier is absent → **`needs_clarification`** (line 366);
8. tool execution through I3 (`invoke_tool`) with per-object organization re-check (§9) — lines 369-375;
9. append-only Layer-2 evidence: `record_tool_call` with **argument allowlist**, **result-metadata allowlist**, hashes, truncation flag, duration — lines 385-400;
10. optional **narration** through the existing provider abstraction with a bounded prompt (lines 415-475); `MAX_PROVIDER_ATTEMPTS = 2` (`domain/insight_interaction.py:38`);
11. truthful answer-status combination, `provider_unavailable` when narration is required but unavailable — lines 476-492;
12. canonical audit append to `public.audit_trail` via `AuditLogger`; a failed audit append is recorded as `audit_append_failed:*` and never converts to success — lines 504-520.

### 4.3 Intent classification and parameter extraction

| Reference need | Implementation |
| --- | --- |
| Intent classification | `[FACT]` deterministic **keyword** routing, no LLM: `_INTENT_KEYWORDS` (`services/insight_tools.py:149-154`); 2+ matches ⇒ `invalid_input`/`ambiguous_intent`; no match ⇒ `invalid_input`/`unsupported_intent`; utterance >2000 chars ⇒ `invalid_input`. |
| Structured parameter extraction | `[FACT]` **UUIDs only** (`_UUID_RE`, `extract_identifiers`). **No date, period, amount, unit, scope, supplier or activity parameter parsing exists in the backend or the Insight UI** (grep of `frontend/src/v3/insight/*` for date/amount/tolerance finds only timestamp formatting and a `date` label). |
| Parameters sent to the model | The question (first 500 chars) and allowlisted structured evidence only — `services/insight_interactions.py:439-447`. |

### 4.4 Answer states

`[FACT]` 14-value `AnswerStatus` (`domain/insight_interaction.py:58-71`): `success, zero, no_data, not_authorized, insufficient_data, needs_clarification, tool_failure, provider_unavailable, partial, rate_limited, refused, ungrounded, invalid_input, error`. The UI renders all 14 distinctly and never converts `no_data` → `zero` (`frontend/src/v3/insight/answerStates.js:22,48,56,156-163`). **There is no `multiple_matches` state**, and `rate_limited` is declared but never produced (§9.7).

### 4.5 I3 — the ratified four-tool catalogue (unchanged)

`[FACT]` `backend/domain/insight_tool.py` (contract) + `backend/services/insight_tools.py` (`TOOL_DEFINITIONS`, lines 83-123) define **exactly four** tools and nothing else:

| Tool | Required input | Reference kinds | Statuses |
| --- | --- | --- | --- |
| `report_lookup` | `report_id` | `report`, `report_version` | success/no_data/not_authorized/invalid_input/error |
| `report_version_lookup` | optional `version_id` \| `report_id`+`version_number` | `report_version`, `report` | same |
| `report_evidence_lookup` | `report_version_id` | `report_version`, `evidence_line_item`, `calculation_snapshot` | same |
| `calculation_snapshot_lookup` | `snapshot_id` | `calculation_snapshot` | same |

`ToolStatus` has six values (`success, no_data, not_authorized, invalid_input, provider_unavailable, error`; `domain/insight_tool.py:39-51`). `REFERENCE_KINDS` = `report, report_version, evidence_line_item, calculation_snapshot` (lines 55-60).

The snapshot output allowlist (`_SNAPSHOT_FIELDS`, `services/insight_tools.py:75-81`) carries `activity, activity_type, quantity, quantity_unit, co2e_multiplier, co2e_kg, scope, date, reporting_year, methodology, algorithm_version, content_hash, factor_id, factor_kind, customer_factor_id, factor_source, source_item_id, source_line_item_id` — **`source_file` and `source_page` are deliberately excluded** (code comment: "not named — omitted, not inferred"). The evidence-line allowlist (`_EVIDENCE_LINE_FIELDS`, lines 66-69) carries identity/provenance ids and `line_number`/`materialisation_kind` but **no raw extracted content** (`raw_description`/`raw_quantity`/`raw_unit` excluded).

**No tool accepts a date, amount, unit, period, organization-scoped list or any discovery parameter.** `[FACT]`

### 4.6 Persistence and RLS

`[FACT]` Tables `carbontally_insight_conversations`, `_messages` (I1 migration `20261001000000`), `_interactions`, `_tool_calls` (I4 migration `20261003000000`); RLS **enabled** on all four with creator-scoped `SELECT`/`INSERT` policies (`ci_conversations_creator_*`, `ci_messages_conversation_creator_*`, `ci_interactions_creator_*`, `ci_tool_calls_creator_*`); the I2 migration (`20261002000000`) re-affirms the message-insert policy. **No `UPDATE`/`DELETE` policy exists** ⇒ append-only at the RLS layer. `public.audit_trail` remains the canonical audit ledger (I4).

### 4.7 Provider integration

`[FACT]` One provider abstraction only: `infra/llm_client.py::LLMClient` (OpenAI-compatible chat-completions, 30 s timeout, `temperature=0.0` by default, `AIExtractionFailedError` on any failure). Insight narration obtains a client from `narration_client()` (`services/insight_interactions.py:149-164`) which returns `None` unless `CARBONTALLY_AI_BASE_URL`, `CARBONTALLY_AI_API_KEY` and `CARBONTALLY_AI_MODEL` are all configured; attribution comes from the existing `infra/ai_runtime.configured_ai_attribution()`. **No second provider architecture, no RAG, no embeddings, no vector store, no LangChain** (verified by grep: the only LLM call sites in application code are Insight narration and document extraction).

## 5. Capability matrix

Status values are restricted to: `IMPLEMENTED` · `PARTIALLY IMPLEMENTED` · `NOT IMPLEMENTED` · `BLOCKED BY GOVERNANCE` · `BLOCKED BY TECHNICAL GAP` · `UNCLEAR / REQUIRES DECISION`. No scores or rankings.

### 5.1 Phase A — Explain one verified calculation

| Reference capability | Status | Actual implementation | Evidence | Gap | Governance implication |
| --- | --- | --- | --- | --- | --- |
| A1 Identify one authoritative calculation | `PARTIALLY IMPLEMENTED` | Identified **only** when the question contains the snapshot UUID (`calculation_snapshot_lookup`); otherwise `needs_clarification` | `services/insight_interactions.py:176,179-190,364-366`; `services/insight_tools.py:83-123` | Reference §4.1 steps 2–4 (identify from date/amount/activity) absent | `[GOV]` requires discovery capability (B1–B5) |
| A2 Explain stored inputs (activity, quantity, unit) | `IMPLEMENTED` | Allowlisted snapshot projection returns `activity`, `activity_type`, `quantity`, `quantity_unit`; narration explains them | `_SNAPSHOT_FIELDS`, `services/insight_tools.py:75-81`; prompt lines 415-447 | — | none |
| A3 Explain stored CO₂e result | `IMPLEMENTED` | `co2e_kg`, `co2e_multiplier` allowlisted; never computed by the model | same; system prompt lines 69-75 | — | none |
| A4 Explain scope and date/reporting year | `IMPLEMENTED` | `scope`, `date`, `reporting_year` allowlisted | same | — | none |
| A5 Explain methodology / algorithm version | `PARTIALLY IMPLEMENTED` | `methodology`, `algorithm_version` exposed; **`factor_set` is not allowlisted** although the snapshot row stores it | `services/insight_tools.py:75-81` vs `data/emissions_logs.py:53-59` | Stored factor-set/version provenance is unreachable by Insight | `[INFER]` widening an allowlist is a tool-contract change → `[GOV]` |
| A6 Explain factor metadata (id, kind, source, customer factor) | `IMPLEMENTED` | `factor_id`, `factor_kind`, `customer_factor_id`, `factor_source` allowlisted (customer-factor precedence carried) | `services/insight_tools.py:75-81` | — | none |
| A7 Explain where the value came from (source item / line) | `PARTIALLY IMPLEMENTED` | `source_item_id`, `source_line_item_id` exposed; document/page/row facts are **excluded** from the allowlist | same; `domain/evidence.py` | The model cannot state the source document/page/row; only the viewer shows it | none (deliberate minimisation); navigation in C1–C3 |
| A8 Link the answer to evidence | `IMPLEMENTED` | References returned as locators; UI renders a `View source evidence` handoff to the shared viewer | `frontend/src/v3/insight/references.js:23,109-113`; `frontend/src/v3/evidence/evidenceLocation.js` | `evidence_line_item` remains non-resolvable **as an I3 tool** by design | `[GOV]` C-09 (inventory); no change implied |
| A9 Plain-English narration grounded in the record | `IMPLEMENTED` | Provider narration over allowlisted structured evidence only; deterministic result preserved on provider failure; `provider_unavailable` truthful | `services/insight_interactions.py:69-75,415-492` | — | none |

### 5.2 Phase B — Deterministic date/amount discovery (reference §4.1, §7, §8, §14-B)

| Reference capability | Status | Actual implementation | Evidence | Gap | Governance implication |
| --- | --- | --- | --- | --- | --- |
| B1 Backend discovery of calculations **by date**, org-scoped | `PARTIALLY IMPLEMENTED` | Date-ranged, org-scoped reads exist: `list_snapshots(org_id, period, limit, offset)`, `find_by_org(org_id, period)`, `count_snapshots(org_id, period)`; exposed on the emissions API and consultant analytics | `data/emissions_logs.py:148,284,295-314`; `api/v3_emissions.py:323-324`; `api/v3_consultants.py:1378-1379` | No **discovery operation**: no unit filter, no amount match, no candidate/ambiguity reporting, no discovery-specific ordering contract | `[GOV]` a discovery capability needs its own bounded definition (reference §7) |
| B2 Discovery **by amount** (± tolerance) | `NOT IMPLEMENTED` | No tolerance constant, parameter or comparison exists in application code | grep `tolerance` → no application-code hits | Entire amount-matching semantics absent | `[GOV]` reference §8.4: tolerance "must be a documented product rule" |
| B3 Structured parameter extraction (date, amount, unit) | `NOT IMPLEMENTED` | Only UUID extraction exists; no date/amount/unit/period parser in backend or UI | `services/insight_interactions.py:174-190`; `frontend/src/v3/insight/*` | Reference §4.1 step 3 cannot be performed | `[GOV]`/`[INFER]` an LLM parameter extractor would be a new LLM path; a deterministic parser still needs a discovery tool |
| B4 Insight can invoke discovery | `BLOCKED BY GOVERNANCE` | `_TOOL_SCOPE_ARGUMENT` maps only the four ratified tools; `classify_intent` has no discovery keyword set; the registry has no such entry | `services/insight_interactions.py:83-88`; `services/insight_tools.py:149-154,83-123` | No fifth tool, no widened tool input | `[GOV]` **explicit PO decision** (reference §18: "whether date/amount discovery becomes a fifth I3 tool") |
| B5 I3 contract authorizes the operation | `BLOCKED BY GOVERNANCE` | `ToolStatus` has six values; the four tools accept identifiers only | `domain/insight_tool.py:39-51,83-123` | Contract cannot express the operation | `[GOV]` same decision as B4 |
| B6 `multiple_matches` response state | `BLOCKED BY GOVERNANCE` | The 14-state `AnswerStatus` and the 6-state `ToolStatus` have no `multiple_matches`; nothing produces it | `domain/insight_interaction.py:58-71`; `domain/insight_tool.py:39-51` | Reference §7 contemplates a status the closed vocabularies lack, and instructs stop-and-report rather than widening | `[GOV]` touches the closed I4/Q3 decision and the closed I3 contract |
| B7 Zero / one / multiple distinction | `NOT IMPLEMENTED` | `zero` ≠ `no_data` is modelled and rendered, but no path can return several candidates | `answerStates.js:22,48,56,156-163` | Multiple-candidate handling absent | `[GOV]` follows B6 |
| B8 Date/timezone semantics | `NOT IMPLEMENTED` | Filtering uses `start_date`/`end_date` calendar dates; no timezone rule is documented or coded | `data/emissions_logs.py:155-168,303-313` | Reference §8.2 requires explicitly documented semantics | `[GOV]` reference §18: "timezone semantics for date matching" must not be guessed |
| B9 Safe clarification for insufficient questions | `PARTIALLY IMPLEMENTED` | `needs_clarification` **is** produced when the classified tool needs an identifier the question lacks; there is no clarification for an under-specified date/amount question (reference §4.4 example) | `services/insight_interactions.py:364-366`; `_INTENT_REFUSAL_ANSWER` | Reference's insufficient-question behaviour only partly reachable | `[GOV]` follows B4/B6 |

### 5.3 Phase C — Deterministic comparisons (reference §13, §14-C)

| Reference capability | Status | Actual implementation | Evidence | Gap | Governance implication |
| --- | --- | --- | --- | --- | --- |
| C1 Month-over-month / year-over-year totals | `BLOCKED BY GOVERNANCE` (Insight) / existing backend capability | `GET /api/v3/emissions/dashboard?organization_id&start_date&end_date` returns `by_month` and scope/asset/facility/supplier/activity breakdowns; the benchmarking engine performs multi-year comparisons | `api/v3_emissions.py:247-281`; `engines/benchmarking.py:192-260` | Not reachable by Insight (no aggregation tool/authorization); no aggregation definition for Insight answers | `[GOV]` reference §14-C: "Requires explicit aggregation definitions and authorization" |
| C2 Scope comparison | `BLOCKED BY GOVERNANCE` (Insight) / existing backend capability | `aggregate(..., "scope")`, `GET /api/v3/emissions/scope-breakdown` | `api/v3_emissions.py:284-299`; `data/emissions_logs.py:171-223` | Same as C1 | `[GOV]` same |
| C3 Facility / asset comparison | `BLOCKED BY GOVERNANCE` (Insight) / existing backend capability | `_GROUP_EXPRESSIONS` includes `asset` and `facility`; dashboard returns both | `data/emissions_logs.py:43-49`; `api/v3_emissions.py:263-264` | Same as C1 | `[GOV]` same |
| C4 Narrative explanation of a change | `NOT IMPLEMENTED` | No aggregation reaches Insight, so no change narrative can be grounded | as C1–C3 | Nothing to narrate without an authorized aggregation contract | `[GOV]` follows C1 |

### 5.4 Phase D — Contributor/driver analysis (reference §13, §14-D)

| Reference capability | Status | Actual implementation | Evidence | Gap | Governance implication |
| --- | --- | --- | --- | --- | --- |
| D1 Top contributing activities | `BLOCKED BY GOVERNANCE` (Insight) / existing backend capability | `aggregate_by_activity(org_id, period)`; dashboard returns `by_activity` | `data/emissions_logs.py:264-283`; `api/v3_emissions.py:266,280` | Insight cannot call it; no contribution/denominator definition for answers | `[GOV]` reference §14-D: "Requires governed aggregation, denominator semantics, and acceptance criteria" |
| D2 Top suppliers | `BLOCKED BY GOVERNANCE` (Insight) / existing backend capability | `aggregate_by_supplier(org_id, period)`; dashboard returns `by_supplier` | `data/emissions_logs.py:242-263`; `api/v3_emissions.py:265,279` | Same | `[GOV]` same |
| D3 Largest increases/decreases, contribution percentages | `NOT IMPLEMENTED` | No delta/contribution computation exists for an Insight answer; the benchmarking engine computes comparisons only for its own report surface | `engines/benchmarking.py` (read-only inspection) | Capability absent for this use case | `[GOV]` same |
| D4 Safe disambiguation of "which one?" | `BLOCKED BY GOVERNANCE` | Depends on B6 | as B6 | — | `[GOV]` same |

### 5.5 Cross-cutting capabilities (reference §6, §10, §11) — part 1

| Reference capability | Status | Actual implementation | Evidence | Gap | Governance implication |
| --- | --- | --- | --- | --- | --- |
| X1 Insight UI states + evidence navigation | `IMPLEMENTED` | Authenticated `/insight`; 14 answer states rendered distinctly; composer; `View source evidence` handoff | `App.js:2072`; `answerStates.js`; `references.js:109-113` | — | none |
| X2 Layer-6 evidence destination (one provenance system) | `IMPLEMENTED` | The shared `SourceEvidenceViewer` is reused; Insight has no viewer of its own | `frontend/src/v3/evidence/SourceEvidenceViewer.jsx`; PO closure 2026-09-22 | — | none |
| X3 Tenant isolation (Insight) | `IMPLEMENTED` | I2 boundary + object-org re-check in every tool + org-active check + creator-private RLS | `api/insight_authz.py:206-291`; `services/insight_tools.py:252-254,288-289`; RLS policies (§4.6) | — | none |
| X4 Bounded context (I5) | `IMPLEMENTED` | 20,000-char default budget (configurable), current-conversation only, chronological, non-authoritative history, structured projections only | `services/insight_context.py:42-95`; `insight_interactions.py:429-447` | Raw message text deliberately excluded (accepted limitation O-4) | none (closed) |
| X5 Data minimisation to the model | `IMPLEMENTED` | Allowlisted tool data; question truncated to 500 chars; `_bounded_context` bounded; budget enforced pre-submission | `insight_interactions.py:67,193-214,439-447` | — | none |
| X6 Prompt-injection resistance — Insight narration | `IMPLEMENTED` | System prompt forbids inventing values/authority; only allowlisted structured evidence (no document text) is submitted | `insight_interactions.py:69-75,439-447`; `_EVIDENCE_LINE_FIELDS`/`_SNAPSHOT_FIELDS` exclude raw content | — | none |
| X7 Prompt-injection resistance — AI document extraction | `PARTIALLY IMPLEMENTED` | Untrusted document text is embedded in the user message; the system prompt contains **no** instruction to ignore instructions inside the document; impact bounded by candidate-only output + JSON schema + allowlisted field cleaning + completeness gate + downstream deterministic validation | `services/ai_document_extraction.py:44-47,161-183,185-244`, `_clean_single` 105-133 | Reference §11 requires document content never be treated as instructions | `[GOV]`/`[INFER]` hardening this non-Insight path is an implementation change needing its own authorization |

### 5.5 Cross-cutting capabilities — part 2

| Reference capability | Status | Actual implementation | Evidence | Gap | Governance implication |
| --- | --- | --- | --- | --- | --- |
| X8 Signed URLs / evidence security | `IMPLEMENTED` | Server-issued short-lived URLs; DM-6 depth enforced on the evidence routes (signed URL/`path`/`metadata` at `FULL` only); the customer documents route remains member-scoped | `api/v3_emissions.py:388-448,505-554`; `api/v3_evidence.py:103-104`; PO closure C-01/C-02 | `source_item.file_url` returned below FULL (PO **ratified**); documents route outside DM-6 (PO **deferred**) | `[GOV]` already dispositioned — no action authorized |
| X9 Audit logging | `IMPLEMENTED` | Canonical `audit_trail` append per interaction (ids/statuses only); append-only tool-call records; evidence line-access audit | `insight_interactions.py:216-248,504-520`; `api/v3_evidence.py`; `domain/insight_interaction.py:44-52` | — | none |
| X10 Rate limiting on Insight endpoints | `NOT IMPLEMENTED` | `RateLimitMiddleware` is **defined but never registered** (no import, no `add_middleware`); `AnswerStatus.RATE_LIMITED` is never produced | `middleware/rate_limit.py:12`; grep: no reference to it outside that file; `domain/insight_interaction.py:67` (declaration only) | Reference §11 requires bounded limits; nothing enforces them | `[GOV]` I8-A principle PO-closed, but no concrete I8 authorization (thresholds, acceptance criteria) exists — see §11 G-6 |
| X11 Error handling / non-disclosure | `IMPLEMENTED` | Tool failures collapse to `error`/`internal_error` with server-side logging; validation returns 422 with plain messages; denials are uniform; no raw exceptions on Insight routes | `services/insight_tools.py:266-272`; `api/insight_authz.py:179-181`; `api/v3_insight_interactions.py:61-65` | — | none |
| X12 Carbon-accounting concept answers (taxonomy H) | `NOT IMPLEMENTED` | No governed product/domain knowledge source; the narration system prompt restricts the model to the supplied evidence | `insight_interactions.py:69-75` | Reference §5-H permits these but requires them to be distinguished from calculated facts | `[GOV]` needs a bounded authorization |
| X13 Provider-failure behaviour | `IMPLEMENTED` | Bounded retries (2); deterministic result preserved; `provider_unavailable` only when narration is required | `insight_interactions.py:448-492`; `domain/insight_interaction.py:38` | — | none |
| X14 Persona coverage (consultant / internal staff / auditor / PE) | `UNCLEAR / REQUIRES DECISION` | Consultant and internal-staff scopes **are** resolvable by `authorize_insight_scope`; auditor and PE are explicitly denied; the I6 closure records the consultant/internal-staff **surface** as a future PO decision | `api/insight_authz.py:184-291`; I6 closure §F.2 | Scope resolution exists but the surface is not authorized | `[GOV]` C-10 (inventory) — PO decision required |

## 6. Detailed code-trace findings

`[FACT]` unless marked.

### 6.1 The three paths a customer question can take today

1. **UUID present + keyword match** → one ratified tool executes against the caller's own organization only; its result is projected onto an allowlist; the answer state follows the tool status; narration may explain it.
2. **Keyword match but no required UUID** → `needs_clarification` (no tool executes; nothing is guessed).
3. **No keyword match or ambiguous keywords** → `invalid_input` (`unsupported_intent` / `ambiguous_intent`) mapped through `_INTENT_REFUSAL_ANSWER` to the I4 vocabulary. `[FACT]` `services/insight_interactions.py:90-113,330,359-362`

There is **no fourth path** in which the system discovers records from question content. Reference §4.1 (steps 2–4: recognise a date/amount question, extract structured parameters, discover) has no implementation.

### 6.2 Intent keywords are the whole classification surface

`[FACT]` `_INTENT_KEYWORDS` (`services/insight_tools.py:149-154`): `report_version_lookup` ← (`version`, `revision`, `superseded`, `which draft`); `report_evidence_lookup` ← (`evidence`, `source line`, `backing`, `supporting`, `audit trail`); `calculation_snapshot_lookup` ← (`calculation`, `snapshot`, `emission factor`, `factor used`, `co2e`, `kg co2`); `report_lookup` ← (`report`, `summary document`).

`[INFER]` Consequences for the reference's example questions: *"Why was my CO2e 20 kg on 1 February 2024?"* matches `calculation_snapshot_lookup` by the keyword `co2e`, but contains no UUID, so it returns `needs_clarification`; *"Why did February emissions increase?"* matches no keyword set (no `emission`+`increase` token) and returns `invalid_input`; *"Which supplier generated the highest emissions?"* likewise matches nothing.

### 6.3 The LLM cannot select tools, tables or data

`[FACT]` The model is **not** used for tool selection: tool choice is deterministic keyword routing; the model is called only *after* a successful tool result, with `narration != "none"`, and receives only `_bounded_context(payload)` (tool name, status, reason, allowlisted `data`, references) plus bounded historical context and the first 500 chars of the question. The system prompt (`insight_interactions.py:69-75`) forbids inventing factors/calculations/values/identities/authorization/tool results. There is no SQL generation, no table selection, no function-calling/JSON-schema tool interface, and no provider-supplied parameters anywhere. `[FACT]`

### 6.4 Model output cannot become authoritative data

`[FACT]` Narration text is persisted as a **message** (`role="insight"`), never as Layer-2 evidence or a calculation (`insight_interactions.py:494-502`, comment: "Narration text is a message, not Layer-2 evidence (PO Q4)"); the canonical audit event contains only ids/statuses. The deterministic answer status is computed from the tool status, not from the narration.

### 6.5 Deterministic-intent refusal vocabulary

`[FACT]` `_INTENT_REFUSAL_ANSWER` maps refusal reasons to I4 states (`needs_clarification` for missing identifiers; `invalid_input` for unsupported/ambiguous/too-long; etc.). **No refusal path invents a tool call.** `secret`-free: reasons are machine-readable constants only.

### 6.6 What the reference asks for that has no code at all

| Reference requirement | Code reality |
| --- | --- |
| §4.1 structured parameters (`date = 2024-02-01`, `amount ≈ 20 kg`) | `[FACT]` none — no parser, no schema, no field |
| §7 discovery operation (typed, bounded, org-scoped, explicit matching) | `[FACT]` none as a discovery contract; only date-ranged listing/aggregation used by other surfaces |
| §7 response state `multiple_matches` | `[FACT]` absent from both closed vocabularies |
| §8 amount tolerance | `[FACT]` absent |
| §8 timezone semantics | `[FACT]` absent/undocumented |
| §9 LLM contract payload `intent: "explain_calculation"` etc. | `[FACT]` the prompt carries no such envelope; `intent` is a persisted tool name or refusal reason, not a model input |
| §11 rate limiting | `[FACT]` middleware unregistered |
| §13/§14-C/D comparisons and drivers | `[FACT]` backend aggregation exists; no Insight path |

## 7. Deterministic discovery findings

Answering the task's four specific questions about *"Why was my CO2e 20 kg on 1 February 2024?"*.

### 7.1 Can the backend deterministically discover matching calculations?

`PARTIALLY IMPLEMENTED — date yes, amount no.` `[FACT]`

| Capability | Where | Scope/safety |
| --- | --- | --- |
| Calculation snapshots for a period | `EmissionLogRepository.list_snapshots(org_id, period, limit=50, offset=0)` — `ORDER BY calculated_at DESC`, parameterised `date BETWEEN $2 AND $3` | organization-scoped in SQL; bounded; newest-first |
| Snapshot count for a period | `count_snapshots(org_id, period)` | organization-scoped |
| Emission logs for a period | `find_by_org(org_id, period)` — `ORDER BY start_date, created_at` | organization-scoped; joins the snapshot for `customer_factor_id` |
| Aggregates by scope/month/year/asset/facility | `aggregate(org_id, period, group_by)` with an explicit `_GROUP_EXPRESSIONS` allowlist (SQL-injection safe) | organization-scoped; validated `group_by` |
| Aggregates by supplier / activity | `aggregate_by_supplier`, `aggregate_by_activity` | organization-scoped |
| Snapshot by id | `get_snapshot(snapshot_id)` — **no org predicate in SQL**; the caller (`_snapshot_lookup`) applies the organisation comparison after the read | see §9.2 |
| Snapshots for a source file / evidence line | `list_for_file(file_id)` (no org predicate — caller-scoped), `list_for_line(line_item_id, organization_id, limit)` (**org predicate in SQL**) | see §9.2 |

**No amount matching, no tolerance, no unit filter, no candidate ranking, and no discovery-specific result envelope exist.** `[FACT]`

### 7.2 Can Insight invoke that discovery?

**No.** `[FACT]` `build_tool_input` can only scope the four ratified tools from a UUID (`_TOOL_SCOPE_ARGUMENT`, `insight_interactions.py:83-88`); the tool registry has no discovery entry; `classify_intent` has no discovery keyword set; and the HTTP tool surface (`POST /api/v3/insight/tools/invoke`) requires a ratified tool name — an unratified name returns `invalid_input`/`unratified_tool` (`services/insight_tools.py:244-246`). `[FACT]`

### 7.3 Does the current I3 contract authorize that operation?

**No — and this is the precise governance boundary.** `[FACT]` + `[GOV]`
* the catalogue is closed at four tools (`domain/insight_tool.py:1-21,83-123`; PO I5–I8 record §3.5);
* no ratified tool accepts a date, amount, unit, period or organisation-scoped list;
* `ToolStatus` cannot express "several candidates matched";
* the I6 closure already recorded that making an evidence-line-item resolvable needs a new/widened tool — "a separate PO decision" — and the 2026-09-22 closure for the viewer explicitly did **not** create one.

### 7.4 Is amount tolerance defined?

**No.** `[FACT]` No tolerance constant, configuration key or comparison exists in application code. Reference §8.4: the tolerance "must be a documented product rule, not an arbitrary LLM decision". `[GOV]`

### 7.5 Are date/timezone semantics defined?

**No.** `[FACT]` Dates are calendar dates (`start_date`, `end_date`; `DateRange`); no timezone rule is documented in code or in a decision record. Reference §8.2 requires explicit semantics; reference §18 lists timezone semantics as a decision "that should not be guessed". `[GOV]`

### 7.6 Does the system distinguish zero / one / multiple matches?

**Only partially.** `[FACT]` `zero` and `no_data` are modelled, rendered distinctly and tested; but **no discovery path exists**, so one/multiple cannot arise. `zero` is produced only when an identified calculation's result is zero — not from a discovery count.

### 7.7 Can it safely ask for clarification?

**Only for the identifier case.** `[FACT]` `needs_clarification` is returned when a classified tool requires an identifier absent from the question (`insight_interactions.py:364-366`) and is rendered as a distinct UI state. There is **no** clarification path for an under-specified date/amount/period question (reference §4.4), because there is no parameter model to be under-specified.

### 7.8 End-to-end trace summary for the reference's headline example

| Step (reference §4.1) | Implemented? |
| --- | --- |
| 1. User asks the question | ✅ (composer, `InsightPage.jsx`) |
| 2. Recognise a date/amount historical-result question | ❌ (keyword sets contain no such intent) |
| 3. Extract `date = 2024-02-01`, `amount ≈ 20 kg` | ❌ (UUID extraction only) |
| 4. Deterministic org-scoped discovery | ⚠️ date-ranged reads exist; no discovery operation |
| 5. Return candidates | ❌ |
| 6. Exactly one ⇒ snapshot + provenance | ⚠️ possible only if the user already supplies a snapshot UUID |
| 7. LLM converts the verified record to plain English | ✅ |
| 8. Answer explains activity/quantity/factor/result/scope/date | ✅ (for an identified record) |
| 9. "Show me the source" ⇒ evidence path to the viewer | ✅ (reference → handoff → viewer) |

**Conclusion:** the example fails at steps 2–5 and only works at 6–9 when the customer already knows an internal identifier. `[INFER]`

## 8. Evidence / provenance findings

### 8.1 The chain as implemented (all links verified in code)

`[FACT]` `emissions_logs.snapshot_id` → `calculation_snapshots` (`source_item_id`, `source_line_item_id`, `source_file`, `source_page`, factor provenance) → `manual_extraction_items` → `organization_files` (private storage) → server-issued signed URL → `SourceEvidenceViewer`.

| Reference requirement (§10) | Implementation | Evidence |
| --- | --- | --- |
| Evidence viewer as the single destination | `SourceEvidenceViewer` route `/evidence/line-items/:lineItemId` (authenticated); reused by the customer evidence panel and Insight | `frontend/src/v3/evidence/SourceEvidenceViewer.jsx`; `App.js:2085`; viewer route `api/v3_evidence.py:103-104` |
| Read-only, organisation-authorised | DM-6 depth evaluated per request; organisation isolation asserted; access audited (`evidence.line_access`) | `api/v3_evidence.py:103+`; `api/v3_emissions.py:407-448` |
| No second provenance system | one location kernel `evidenceLocation.js`, one line model `evidence_line_items`, one DM-6 policy | PO closure 2026-09-22 §10 |

### 8.2 Location semantics actually produced

`[FACT]` `backend/domain/evidence.py`:

| Source type | Location actually derivable | Evidence |
| --- | --- | --- |
| PDF (with producer page) | page, **verified only** when the authoritative line carries an integer `source_page ≥ 1` (`resolve_source_page`, lines 38-60; `PAGE_STATE_VERIFIED/UNVERIFIED/UNAVAILABLE`) | `domain/evidence.py:23-60,205-260` |
| PDF (historical/page-count-derived) | **reported but `unverified`** — never presented as a page | same; PO closure C-03 context |
| Image / scanned PDF | same rules as PDF; **no OCR coordinates or bounding boxes exist anywhere** | `[FACT]` no bbox/region code; reference §10 explicitly forbids inventing them |
| CSV | producer `source_row` (1-based data-row index) → `kind: row`; the pipeline never equates the row with the evidence ordinal | `services/automatic_extraction.py:673-683`; `domain/evidence.py:96-125` |
| XLS/XLSX | `extracted_data.source_sheet` + element `source_row` → `kind: sheet_row` | `services/automatic_extraction.py:787`; `domain/evidence.py:96-125` |
| Printed row/line reference | `row_reference` is read from the line (`domain/evidence.py:107-125`) but **no producer emits `line_reference`**, so it is always NULL today | `domain/line_items.py:54,186-187`; prior forensic finding |
| Missing location | explicit `kind: unavailable` with an ordinal caveat; the ordinal is never shown as a page/row | `domain/evidence.py:63-160` |
| Below `FULL` (DM-6) | `state: restricted`, uniform copy, no page/sheet/row | `domain/evidence.py` + `domain/disclosure_exposure.py` |

### 8.3 Can `source_item_id` / `source_line_item_id` reach the viewer?

**Yes — implemented.** `[FACT]`
* `_SNAPSHOT_FIELDS` carries both identifiers to Insight (`services/insight_tools.py:75-81`);
* the customer evidence route exposes the line handoff (`evidence.source_line_item_id`, `api/v3_emissions.py:544`);
* the Insight UI builds the viewer path from a resolved reference **or** a snapshot's `source_line_item_id` (`references.js:109-113` → `evidenceLocation.js::evidenceViewerPathForReference`);
* the viewer resolves the line server-side (`GET /api/v3/evidence/line-items/{id}`, `api/v3_evidence.py:103-104`) with DM-6 + organisation checks and an access audit.

**Residual gap (not a defect):** `evidence_line_item` is still **not resolvable as an I3 tool**, so if Insight only holds an `evidence_line_item` *reference* it presents it as an unresolvable locator (the handoff still renders because the UI resolves the kind through the viewer path). This is the recorded C-09 boundary. `[FACT]`

### 8.4 Signed URLs and organisation authorisation

`[FACT]`
* signed URLs are issued only server-side, only after DM-6 depth evaluation, and only at `FULL` on the evidence routes (`api/v3_emissions.py:446-448,526-554`);
* the viewer's own route returns an allowlist plus a signed URL only when depth allows;
* the customer documents route `GET /api/v3/documents/{file_id}/signed-url` requires `require_org_member()` + org match but **not** DM-6 — this is the PO-deferred C-02 question, unchanged;
* `source_item.file_url` is still returned below FULL — PO-**ratified** (C-01), unchanged;
* the source item's `path`/`metadata`/signed URL are gated on `exposure.allow_document_refs`.

### 8.5 Residual provenance items already dispositioned by the PO (no action authorized)

`[FACT]` C-01 ratified · C-02 deferred (security policy) · C-03 deferred (audit/provenance policy: `exports.py::_evidence_status` and `reporting.py::audit_readiness` still infer COMPLETE from `source_page IS NOT NULL`) · C-04 accepted · C-05 ratified. These remain **exactly as the PO left them**; nothing in this analysis changes them.

## 9. Security findings (actual, code-traced)

### 9.1 Tenant isolation — can a customer manipulate IDs to reach another organisation's data?

| Attempted object | Result | Evidence |
| --- | --- | --- |
| Report | **Denied.** The caller is bound to `organization_id` before the read, then `report.organization_id == access.organization_id` is re-checked → `not_authorized` | `services/insight_tools.py:252-254,283-289` |
| Calculation snapshot | **Denied** by the same post-read organisation comparison in `_snapshot_lookup` | `services/insight_tools.py:357-363` |
| Report version / evidence lines | **Denied** by the same comparison after the version read | `services/insight_tools.py:306-355` |
| Source item / source document / evidence | Reachable only through the D33 evidence route and the viewer route, both of which assert organisation access and DM-6 depth; the viewer route's `list_for_line` also applies `organization_id` **in SQL** | `api/v3_emissions.py:407-448`; `api/v3_evidence.py:103+`; `data/emissions_logs.py:335-360` |
| Conversation (Insight) | **Denied** — 404 unless the conversation belongs to the resolved organisation *and* is creator-visible | `insight_authz.py:331+`; `insight_interactions.py:283-287` |
| Cross-organisation `organization_id` in body/query | **Denied** for customer principals (must equal their own organisation), denied for consultants without an active client grant, denied for PE, auditor and inactive organisations | `insight_authz.py:206-291` |

`[FACT]` RLS is enabled on all four Insight tables with creator-scoped select/insert only (§4.6); the API does not rely on RLS alone (the service pool bypasses it, so every check above is explicit application code).

**One residual, already-recorded behaviour:** two raw-read helpers have **no organisation predicate in SQL** — `get_snapshot(snapshot_id)` and `list_for_file(file_id)` — and are only ever used behind an API/service-level organisation assertion (`_snapshot_lookup`; the D33 evidence route). `[FACT]` Defence in depth therefore depends on preserving the caller assertion; as written, the reference's object-level rule is satisfied. `[INFER]` A future caller omitting the assertion would bypass organisation scoping — an observation, not a present defect.

### 9.2 LLM isolation

`[FACT]` The model cannot obtain arbitrary database information: it never receives a query interface, never selects tables, and never sees another organisation's data (every tool read is organisation-bound before projection). It receives only allowlisted tool output, bounded historical context (structured projections of the caller's own conversation), and the first 500 characters of the caller's own question. System and user messages are separate roles (`infra/llm_client.py:114-117`).

`[FACT]` `temperature=0.0` by default at both call sites; narration is capped by `LLMClient`'s default `max_tokens=512`, extraction uses 1024.

### 9.3 Prompt-injection resistance — two different answers

| Path | Finding |
| --- | --- |
| **Insight narration** | `[FACT]` **Strong.** No raw document or extracted text is submitted: `_EVIDENCE_LINE_FIELDS` excludes `raw_description`/`raw_quantity`/`raw_unit`; `_SNAPSHOT_FIELDS` excludes `source_file`/`source_page`; history is structured projections only. The system prompt forbids inventing values and forbids claiming authority. A hostile *question* can at most influence the wording of an explanation of allowlisted evidence. |
| **AI document extraction** (`services/ai_document_extraction.py`) | `[FACT]` **Partial.** Raw document text is placed inside the user message (`_prompt`, lines 161-183) and the system prompt (lines 44-47) contains **no** instruction that the document is untrusted or that embedded instructions must be ignored. A successful injection is bounded: output must parse as a JSON object; fields pass `_clean_single`'s allowlist/canonicalisation (lines 105-133); units go through the Phase-1 canonical normaliser; AI output is explicitly *candidate* data; and the deterministic completeness gate, factor matching, validation and calculation boundary run afterwards, with `error`/low-confidence envelopes recorded durably rather than as false successes (docstring lines 8-21). |
| **Document text altering *system* instructions** | `[FACT]` There is **no mechanism** by which document content can alter the system prompt: system messages are constants in code (`ai_document_extraction.py:44-47`; `insight_interactions.py:69-75`) and no path writes document text into a system role. The residual risk is *output* manipulation within the extraction candidate shape, not instruction-level takeover. |

### 9.4 Evidence security

`[FACT]` Private documents are exposed only through the authorised path: signed URLs are minted server-side with a TTL, gated on DM-6 depth on the evidence routes, and never returned in list/report responses (report fields deliberately omit artefact URLs — `services/insight_tools.py:54-59`). The deliberate exception the PO **ratified** is `source_item.file_url` below FULL (C-01); the question the PO **deferred** is the documents route (C-02).

### 9.5 Data minimisation

`[FACT]` Strong, with explicit allowlists at every boundary: tool output fields; persisted tool-call arguments and result metadata; context projections; evidence-line fields; report fields. The question is truncated to 500 chars for narration; historical context is bounded (default 20,000 chars) and enforced before submission. **No** signed URLs, tokens or raw document content are sent to the model or persisted in Layer-2 evidence.

### 9.6 Error handling / non-disclosure

`[FACT]` Tool exceptions are caught and mapped to `error`/`internal_error`, with the exception logged server-side only (`services/insight_tools.py:266-272`); denial responses are uniform (`_denied`, `insight_authz.py:179-181`); input problems return plain 422 messages; a missing or foreign conversation returns 404 without existence disclosure. `[INFER]` No SQL, stack trace, DSN, credential or internal path can reach a customer through the Insight surface, because every outward value is a constant or an allowlisted projection.

### 9.7 Rate limiting / I8-A controls

`[FACT]` **Not implemented.** `RateLimitMiddleware` (`middleware/rate_limit.py:12`) is not imported or registered anywhere (only `CORSMiddleware` is registered — `main.py:174-196`); `AnswerStatus.RATE_LIMITED` is declared but never produced. Insight endpoints therefore have **no** request-rate bound. `[GOV]` The I8-A *principle* (bounded abuse protection reusing existing infrastructure) is PO-closed, but a concrete authorization — thresholds and acceptance criteria — does not exist, so this cannot be implemented under current authorizations.

---

## 10. Testing findings

`[FACT]` Counts are the number of test functions per file at this HEAD.

### 10.1 Insight / I2 / I3 / I4 / I5

| Area | Suite | Tests |
| --- | --- | --- |
| I2 authorization | `tests/unit/api/test_v3_insight_i2_authorization.py` | 29 |
| I2 RLS (live) | `tests/unit/data/test_i2_insight_rls_live.py` | 5 |
| I2 authorization contracts | `tests/unit/data/test_i2_insight_authorization_contracts.py` | present |
| I1 persistence migration | `tests/unit/data/test_i1_insight_migration.py` | present |
| I3 tool contract | `tests/unit/api/test_v3_insight_i3_tools.py` | 23 |
| I3 real wiring | `tests/unit/api/test_v3_insight_i3_wiring.py` | 5 |
| I4 interactions | `tests/unit/api/test_v3_insight_i4_interactions.py` | 17 |
| I4 wiring | `tests/unit/api/test_v3_insight_i4_wiring.py` | 4 |
| I4 migration / JSONB | `tests/unit/data/test_i4_insight_migration.py`, `test_i4_repository_sql_and_jsonb.py` | present |
| I5 context | `tests/unit/services/test_insight_i5_context.py` | 18 |
| I5 integration | `tests/unit/api/test_v3_insight_i5_context_integration.py` | 6 |
| Insight HTTP endpoints | `tests/unit/api/test_v3_insight_endpoints.py` | present |

`[FACT]` The I4 suite asserts the **whole** 14-state vocabulary (including `rate_limited`) as a contract (`test_v3_insight_i4_interactions.py:382`) even though nothing produces `rate_limited` — i.e. the vocabulary is tested, the behaviour is not.

### 10.2 Evidence / calculation

| Area | Suite | Tests |
| --- | --- | --- |
| Source Evidence Viewer (route, DM-6, location) | `tests/unit/api/test_source_evidence_viewer.py` | 22 |
| Evidence record / precision | `tests/unit/api/test_evidence_record.py` | 14 |
| Evidence traceability | `tests/unit/api/test_evidence_traceability.py` | 7 |
| Emissions routes (incl. evidence) | `tests/unit/api/test_v3_emissions.py` | 13 |
| Multi-line provenance mapping | `tests/unit/services/test_multiline_provenance_mapping.py` | 14 |
| Frontend (viewer, location, answer states, references, page, api) | `frontend/src/v3/__tests__/` (6 suites) | 40+ |

### 10.3 Coverage against the reference's acceptance criteria (§15)

| Criterion | Coverage |
| --- | --- |
| 1 Exact organisation isolation | `[FACT]` covered (I2 authorization, live RLS, per-object org re-check tests) |
| 2 Deterministic discovery reproducible | `[FACT]` **not applicable — no discovery capability exists; no tests** |
| 3 No-match truthfulness | `[FACT]` covered (`no_data` paths) |
| 4 Multiple-match does not guess | `[FACT]` **untested — capability absent** |
| 5 Values from persisted data | `[FACT]` covered (I3 tool + emissions suites) |
| 6 LLM cannot create authoritative numbers | `[FACT]` partially — covered indirectly; no dedicated adversarial model-output test |
| 7 Evidence references resolve through the approved architecture | `[FACT]` covered (viewer, references, handoff tests) |
| 8 Unauthorized IDs do not disclose | `[FACT]` covered (`not_authorized` / 404 assertions) |
| 9 Prompt-injection content does not alter behaviour | `[FACT]` **no test exists** on either the extraction or narration path |
| 10 Error paths fail closed | `[FACT]` covered |
| 11 Audit behaviour preserved | `[FACT]` covered |
| 12–13 Closed contracts unchanged / new contracts authorized first | `[FACT]` covered by contract tests; no new tool exists to test |
| 14 success/no-data/multiple-match/invalid-input/unauthorized/failure tests | `[FACT]` all covered **except** multiple-match (absent by construction) |
| 15–17 Report / OHD / PO closure | `[FACT]` satisfied for I1–I6 and the Source Evidence Viewer |

`[INFER]` Two test-suite caveats already documented by prior OHD verification carry forward: `tests/integration` is environment-dependent (requires a database matching the current migrations), and four backend unit-suite failures plus two frontend suites are pre-existing and unrelated to Insight.

---

## 11. Governance / authorization gaps

Only decisions/authorizations that are **actually required** are listed. Each states what is missing, why, and what it blocks.

| ID | Missing decision / authorization | Exact gap in the record | Blocks |
| --- | --- | --- | --- |
| **G-1** | **A fifth I3 tool (or a widened I3 tool) for deterministic date/amount discovery** | The ratified catalogue is closed at four tools (I3 closure; PO I5–I8 record §3.5 "No new I3 tool is authorized by this record"); the I6 closure §F.1 records that any new/widened tool is "a separate PO decision"; the 2026-09-22 viewer closure added a customer API route but **no** I3 tool | Reference Phase B in its entirety (B1–B5, B9) |
| **G-2** | **A response state expressing "multiple candidates matched"** (`multiple_matches` or an equivalent) | I3 `ToolStatus` (six values) and I4 `AnswerStatus` (fourteen values) are both closed (Q3/PO); the reference §7 explicitly requires such a state "even where existing generic tool statuses use a smaller established vocabulary" and instructs stop-and-report rather than widening | B6, B7, D4 |
| **G-3** | **Amount-matching tolerance as a product rule** | No tolerance exists anywhere; reference §8.4 requires it be a documented product rule, not an LLM decision | B2, and any amount-based discovery |
| **G-4** | **Date/timezone semantics for date matching** | Undocumented and uncoded; reference §8.2 and §18 require explicit semantics | B8, and the correctness of any date-based answer |
| **G-5** | **Authorization + aggregation definitions for comparisons and contributor analysis** | Reference §14-C/§14-D require "explicit aggregation definitions"/"governed aggregation, denominator semantics, and acceptance criteria"; no decision record authorizes Insight aggregation; the `emissions/dashboard` and `aggregate_by_*` capabilities are customer emissions surfaces, not Insight tools | C1–C4, D1–D4 |
| **G-6** | **A bounded I8 authorization for rate limiting (thresholds + acceptance criteria)** | Only I8-A *principles* are PO-closed; the I5–I8 record §11 lists eight prerequisites for a concrete I8 authorization, and the readiness audit records that §35/I8 contains no acceptance criteria | X10 (rate limiting is impossible to implement without inventing thresholds) |
| **G-7** | **Consultant / internal-staff Insight surface authorization** | I6 closure §F.2: "No consultant or internal-staff Insight UI is to be added … any future such surface requires separate authorization" (scope resolution already exists in code) | X14 |
| **G-8** | **`org_viewer` execution-rights decision** | I6 closure §F.3: "an existing authorization-contract question"; no rule was invented | Any change to viewer-role execution (currently permitted by the existing backend contract) |
| **G-9** | **Insight pagination / message-window decision** | I6 closure §F.4: a bounded follow-on decision; the backend already exposes `limit`/`offset` | Message-window UX beyond the current 200-message ascending limit |
| **G-10** | **A decision on prompt-injection hardening for the AI extraction path** | The reference §11 requires document content never to be treated as instructions; the extraction system prompt has no such instruction; hardening is an implementation change to a non-Insight path and requires its own authorization | X7 improvement |
| **G-11** | **Concept-answer (taxonomy H) capability authorization** | No governed knowledge source exists; the reference §5-H permits these answers but requires them to be distinguishable from calculated facts | X12 |
| **G-12** | **Production deployment authorization** | Unchanged: not authorized (closure records; mandatory release chain) | Any deployment of the above |

**Not a governance gap (already dispositioned, no action authorized):** C-01 (ratified), C-02 (deferred), C-03 (deferred), C-04 (accepted), C-05 (ratified), I7 (not authorized / not ready), full I8 (not authorized).

---

## 12. Recommended next decision points

Dependency-ordered only; no product recommendation.

1. **Confirm the scope of the reference itself.** The reference is a technical reference that "does not by itself authorize implementation" (§ header). Whether it supersedes, supplements or merely informs the closed I1–I6 decisions is a PO statement, not an inference Cline may make. `[GOV]`
2. **Decide the discovery contract boundary first** (G-1 and G-2 together), because everything in Phase B depends on it and both are closed contracts. The reference itself frames the question in §18 as "whether date/amount discovery becomes a fifth I3 tool".
3. **Then decide the matching semantics that parameterise it** (G-3 tolerance, G-4 timezone) — these are inputs to whatever discovery contract is chosen and cannot be invented.
4. **Then decide whether comparison/contributor analysis is in scope** (G-5) and, if so, the aggregation/denominator definitions; the backend capability already exists, so this is a definition-and-authorization decision rather than a build-from-nothing decision.
5. **Then decide I8-A rate limiting** (G-6) if customer-facing abuse protection is required before any wider release; note the readiness audit's requirement for thresholds, monitoring requirements and acceptance criteria.
6. **Then decide the persona/pagination items** (G-7, G-8, G-9) — independent of Phase B, each already recorded as a future decision.
7. **Then decide prompt-injection hardening** (G-10) and taxonomy-H concept answers (G-11) as separate bounded items.
8. Every decided item would then follow the mandatory chain: bounded implementation authorization → implementation → OHD verification → PO closure → (separately) deployment authorization.

---

## 13. Explicit NOT IMPLEMENTED / NOT AUTHORIZED items

### 13.1 NOT IMPLEMENTED (verified absent from code)

1. Deterministic discovery operation (typed, bounded, org-scoped) as a callable capability. `[FACT]`
2. Amount matching and amount tolerance. `[FACT]`
3. Date/timezone semantics for matching. `[FACT]`
4. Structured parameter extraction for date/period/amount/unit/scope/activity. `[FACT]`
5. `multiple_matches` (or equivalent ambiguity) response state in either vocabulary. `[FACT]`
6. Insight-reachable aggregation (comparisons, contributors, drivers). `[FACT]`
7. Insight rate limiting (middleware unregistered; `rate_limited` never produced). `[FACT]`
8. Carbon-accounting concept answers (taxonomy H). `[FACT]`
9. OCR region/coordinate provenance for images and scanned PDFs. `[FACT]`
10. A producer for `row_reference` (printed line/row reference). `[FACT]`
11. Prompt-injection instruction hardening on the AI document-extraction path. `[FACT]`
12. Insight pagination / newest-first message windows. `[FACT]`

### 13.2 NOT AUTHORIZED (and therefore also not implemented)

1. Any new or widened I3 tool (including date/amount discovery). `[GOV]`
2. Any change to the I3 six-value `ToolStatus` or the I4 fourteen-value `AnswerStatus`. `[GOV]`
3. Comparisons and contributor analysis for Insight. `[GOV]`
4. Concrete I8 rate-limiting thresholds / I8 acceptance criteria. `[GOV]`
5. Consultant / internal-staff / auditor / PE Insight surfaces. `[GOV]`
6. `org_viewer` execution-rights changes. `[GOV]`
7. Pagination redesign or backend limit changes. `[GOV]`
8. I7 (retention/deletion/export) and full I8. `[GOV]`
9. Production deployment. `[GOV]`
10. Any alteration of the Source Evidence Viewer or change to DM-6 implementation. `[GOV]` — the 2026-09-22 closure authorizes **no** remediation of C-01/C-02/C-03.

### 13.3 Contradictions / ambiguities recorded, not reconciled

* **§7 of the reference vs the closed vocabularies.** The reference asks for a discovery response vocabulary that includes `multiple_matches` while instructing Cline not to widen I3. The two are compatible only if the PO decides the contract — recorded as G-2, not "resolved" here.
* **§11 of the reference vs I8 scope.** The reference treats rate limiting as implementable "consistent with the already authorized I8-A principles", while the decision record authorises principles only and requires eight prerequisites (including thresholds and acceptance criteria) for a concrete I8 authorization. Recorded as G-6.
* **The reference vs the closed I6 decisions.** The reference's taxonomy E/F and §13 industry alignment describe capabilities the closed decisions explicitly do not authorize (aggregation/comparison); the reference does not amend those decisions, and nothing here reopens them.
* **The reference's own status.** It is a technical reference, not an authorization; it is also currently untracked in the repository (§3). Both facts are stated to avoid treating the document as a mandate.
* **Master Specification §41/§47 staleness** (recorded in the PO decision inventory §C-31) affects how a reader should weight the older lists; this report uses §3.1/§48.5 + closure records for status, as the closures direct.

---

## 14. Files inspected

**Reference and governance documents**
* `docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22.md` (full)
* `docs/architecture/CT-P8-PO-DECISION-INVENTORY-20260922.md` (status context; §C items C-01…C-32)
* `docs/architecture/CT-P8-PO-DECISION-DISPOSITION-CLOSURE-DECISIOIN-FOR-SOURCE-EVIDENCE-VIEWER-AND-INSIGHT-20260922.md` (C-01…C-05 dispositions)
* `docs/architecture/CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION_v1.1_20260921.md` (§3.1, §41, §42, §47, §48.5)
* `docs/architecture/CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` (§3.5 I3, §4 I5, §5 I6, §6 I7, §8 I8-A, §11)
* `docs/architecture/CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` (§F follow-ups, §2 boundaries)
* `docs/implementation/phase8/CT-P8-SOURCE-EVIDENCE-VIEWER-IMPLEMENTATION-20260922.md`, `docs/verification/phase8/CT-P8-SOURCE-EVIDENCE-VIEWER-OHD-VERIFICATION-20260922.md` (scope + observations)

**Backend — Insight**
`api/insight_authz.py` · `api/v3_insight.py` · `api/v3_insight_interactions.py` · `api/v3_insight_tools.py` · `api/router.py` · `domain/insight_tool.py` · `domain/insight_interaction.py` · `services/insight_tools.py` · `services/insight_interactions.py` · `services/insight_context.py` · `data/insight.py` · `data/insight_interactions.py`

**Backend — provider / extraction**
`infra/llm_client.py` · `infra/ai_runtime.py` · `services/ai_document_extraction.py` · `services/automatic_extraction.py` (producers) · `workers/automatic_processing.py`

**Backend — data / evidence / authorization**
`data/emissions_logs.py` · `api/v3_emissions.py` · `api/v3_evidence.py` · `api/v3_documents.py` · `domain/evidence.py` · `domain/line_items.py` · `domain/disclosure_exposure.py` · `data/evidence_line_items.py` · `infra/audit_logger.py` · `middleware/rate_limit.py` · `main.py` · `engines/benchmarking.py` · `engines/report_generation.py` · `api/v3_consultants.py`

**Migrations**
`supabase/migrations/20261001000000_p8_i1_insight_persistence.sql` · `20261002000000_p8_i2_insight_authorization.sql` · `20261003000000_p8_i4_insight_interactions.sql`

**Frontend**
`src/App.js` · `src/v3/insight/*` (7 modules) · `src/v3/evidence/*` (3 modules)

**Tests** — as enumerated in §10.

**Search operations performed** (read-only): repository-wide greps for `tolerance`, `rate_limit`/`RateLimitMiddleware`, `RATE_LIMITED`, `discover`/`date_from`/`date_range`, `source_row`/`source_sheet`/`row_reference`/`line_reference`, `llm_client`/`LLMClient`/`complete(`, `find_by_org`/`aggregate*`/`list_snapshots`/`count_snapshots`, `PUBLIC_ROUTE_PREFIXES`, and per-file `git log -1` provenance.

---

## 15. Exact commit SHAs for relevant existing implementations

| Item | Commit | Date |
| --- | --- | --- |
| HEAD examined | `00822472bfe6d52e0223cb7f546d3b9c0453bc4f` | 2026-09-22 |
| I2 authorization boundary (`api/insight_authz.py` last change) | `177dff5` | 2026-09-21 |
| I3 tool catalogue + contract (`api/v3_insight_tools.py`) | `674fe07` | 2026-09-21 |
| I3 tool service incl. wiring remediations (`services/insight_tools.py`) | `651f8c1` | 2026-09-21 |
| I5 context assembly (`services/insight_context.py`, `services/insight_interactions.py`) | `f9d91e1` | 2026-09-21 |
| I6 UI (`frontend/src/v3/insight/InsightPage.jsx`) | `09e2315` | 2026-09-22 |
| Source Evidence Viewer + evidence location kernel (`domain/evidence.py`, `api/v3_evidence.py`, `data/emissions_logs.py`) | `999e4fb` | 2026-09-22 |
| AI document extraction engine last change | `daad396` | 2026-09-11 |
| Rate-limit middleware (unregistered) last change | `077c866` | 2026-08-27 |
| Closed-stage references | I2 `177dff5` · I3 `651f8c1` · I4 `310a62a` · I5 `f9d91e1` · I6 `09e2315` · viewer `999e4fb` (OHD `5d5f7ed`) | — |

**Working tree at the time of writing:** clean except the **untracked** reference document and this report (added by this task). **No application code, test, migration, schema, configuration, API, authorization, UI or deployment file was modified.** `[FACT]`

**Status: ANALYSIS ONLY — no implementation was performed, and none is authorized by this document.**
