# CT-P8-I4-PREAUTHORIZATION-READINESS-AUDIT-20260921

**Stage audited:** I4 — AI Interaction + Canonical Audit · **Stage status: `NOT AUTHORIZED`**
**Task type:** bounded read-only forensic / implementation-readiness audit. No implementation, migration, schema, API, UI, provider, dependency, configuration or test change was made.
**Authority checkout:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **HEAD at audit:** `875e04e0a1d8a3c6b41686c5ccb6a62d78a76f43` · **Alignment:** `0 0` · **Tree:** clean.
**Non-authoritative checkouts were not used for implementation evidence** (`/home/shomonrobie/carbon_tally` is a different checkout on `main`, materially divergent).

**Labelling convention.** `FACT` = traceable to an inspected file, schema, test or command output. `INFERENCE` = reasoned conclusion not directly stated by a source. `RECOMMENDATION` = non-binding engineering advice. `OPEN DECISION` = PO authority; implementation agents must not invent it.

---

## 1. Executive Summary

1. `FACT` — I4 is defined by the canonical specification as **Layer 2 (AI interaction record) + its canonical-audit integration + the dormant-AI-table decision**: §8.1 lines 427–445 (Layer 2 contents), §8.3 line 467 ("I4 builds Layer 2 and its canonical audit integration"), §35/I4 lines 1584–1594 (future scope: Layer-2 persistence, provider/model attribution, truthful usage metadata, answer status, tool-call provenance, canonical audit event, dormant AI table decision, interaction-to-audit reference, durable reconstruction).
2. `FACT` — every foundation I4 must consume is closed and verified: I1 persistence (`public.carbontally_insight_conversations` / `_messages`, migration `20261001000000_p8_i1_insight_persistence.sql`); I2 authorization (`backend/api/insight_authz.py`, migration `20261002000000_p8_i2_insight_authorization.sql`, `CLOSED — VERIFIED PASS at 177dff5`); I3 four ratified read-only tools with the six-point contract (`backend/services/insight_tools.py`, `backend/domain/insight_tool.py`, `CLOSED — VERIFIED PASS at 651f8c1`, OHD re-verification `7faaa57`).
3. `FACT` — reusable real components exist and were code-traced: `backend/infra/llm_client.py` (`LLMClient`, `ChatCompletionResponse`, injectable transport, per-request timeout), `backend/infra/ai_runtime.py` (`configured_ai_extraction_engine`, `provider_label`, `configured_ai_attribution` — truthful provider/model attribution), `backend/infra/audit_logger.py` (`AuditSink` protocol, `AuditLogger.audit`, `init_audit_logger`/`reset_audit_logger`), `backend/data/audit.py` (`AuditRepository.record` → append-only `public.audit_trail`), `backend/middleware/rate_limit.py`, and the dormant `public.ai_content_history`.
4. `FACT` — the current provider abstraction exposes **no token usage and no cost**: `ChatCompletionResponse` is `{text: str, finish_reason: str = "stop"}` (`backend/infra/llm_client.py:32–39`). This corroborates Master Spec §15.4 (`tokens_used = NULL`, `cost = NULL` until truthful) and means any I4 usage/cost field must be nullable and unfilled by default.
5. `FACT` — material I4-defining content remains **open in the canonical specification itself**: §21 "deliberately OPEN until I7" (line 1047), §22 billing OPEN until I8 (line 1071), §23 "the I3/I4 repository-driven decision must select one bounded home for AI interaction/cost/rating data" (line 1100), and §41 Open Product Decisions (22 items, lines 1875–1896) including `raw question storage versus hash`, `exact answer-status enumeration`, `dormant AI structure disposition`, `provider selection`, `AI credits/allowances`, `exact performance/SLO targets`.
6. `FACT` — **specification-internal inconsistency** I4 would inherit: §14 enumerates 14 answer states (lines 737–752: `success/answered`, `zero`, `no_data`, `not_authorized`, `insufficient_data`, `needs_clarification`, `tool_failure`, `provider_unavailable`, `partial`, `rate_limited`, `refused`, `ungrounded`, `invalid_input`, `error`), §26.2 mandates `tool_failure` and §26.5 `needs_clarification`, while the closed I3 implementation exposes exactly six `ToolStatus` values (`success`, `no_data`, `not_authorized`, `invalid_input`, `provider_unavailable`, `error` — `backend/domain/insight_tool.py:46–51`). Reconciling these is an I4-scope decision (→ §13, §19 Q3).
7. `FACT` — the specification says "the canonical CarbonTally audit ledger remains authoritative" (§8.1 line 449, §20.2 line 1021) **without naming it**, while the database contains five audit-shaped tables (`audit_trail`, `audit_logs`, `processing_audit_trail`, `review_audit_trail`, `activity_logs`; `00000000000000_init_schema.sql:914/1647/1669/1870`). Which ledger receives the AI audit event is unresolved (→ §9, §19 Q2).
8. `FACT` — no architectural blocker was found: every I4 dependency (provider client, attribution helper, audit append path, persistence namespace, authorization boundary, tool registry, status vocabulary, rate limiter) has an existing, code-traced home in the authoritative repository.
9. `INFERENCE` — I4 is understood well enough to be scoped, but its Layer-2 schema, its answer-status semantics and its canonical-audit target cannot be fixed responsibly without PO decisions the specification leaves open; hence §21 = `NOT READY — SPECIFICATION GAPS` (a decision/documentation gap, not a technical blocker).
10. `RECOMMENDATION` — the PO could unblock I4 with a short decision record closing §19 Q1–Q6; the remaining items (retention, export, billing, provider selection) are already deferred by the specification to I7/I8 and need not block I4.
---

## 2. Repository State

`FACT` — initial guard results (all conditions satisfied; no discrepancy to report):

| Check | Expected | Observed |
| --- | --- | --- |
| `pwd` / `git rev-parse --show-toplevel` | `/home/shomonrobie/ct_93d5cdd` | `/home/shomonrobie/ct_93d5cdd` ✅ |
| `git branch --show-current` | `p8-release-reconciled` | `p8-release-reconciled` ✅ |
| `git rev-parse HEAD` | `875e04e0a1d8a3c6b41686c5ccb6a62d78a76f43` | identical ✅ |
| `git rev-parse github/p8-release-reconciled` | same | identical ✅ |
| `git rev-list --left-right --count github/…...HEAD` | `0 0` | `0  0` ✅ |
| `git status --short` | empty | empty ✅ |

`FACT` — canonical PO documents verified in place: Master Specification v1.1 = 51,461 bytes, SHA-256 `8f9e5a3f17729a1a39abc7bec3007a5a54ca652b60af6f8d79035f9acaeeea49`, 2,178 lines; I3 closure record = 6,857 bytes, SHA-256 `b75215bd982a47e439db221fa6f17a6a9b016ccc2ff7dfbd7e1943d09200a339`. Both match the PO-supplied values exactly.

`FACT` — repository shape relevant to I4: 77 migrations in `supabase/migrations/`; Insight migrations are exactly `20261001000000_p8_i1_insight_persistence.sql` and `20261002000000_p8_i2_insight_authorization.sql` (no I3 migration exists — I3 was code-only); `backend/data/` 47 repositories; `backend/services/` 23 services; `backend/api/` 54 route modules; `backend/infra/` 8 modules. Insight code is confined to `backend/domain/insight.py`, `backend/domain/insight_tool.py`, `backend/data/insight.py`, `backend/services/insight_tools.py`, `backend/api/v3_insight.py`, `backend/api/v3_insight_tools.py`, `backend/api/insight_authz.py`.

---

## 3. Authority / Source Hierarchy

| Rank | Source | Path (authoritative checkout) | Classification | Bearing on I4 |
| --- | --- | --- | --- | --- |
| 1 | D2 PO Ratification | `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` | `RATIFIED` | Three-layer model; separate conversational domain; creator-private visibility; every-read reauthorization; `carbontally_insight_*` naming |
| 2 | I2 closure | `docs/architecture/CARBONTALLY_P8_I2_INSIGHT_CLOSURE.md` (commit `551f121`) | `VERIFIED EXISTING FOUNDATION` | Authorization boundary I4 must call, never re-implement |
| 3 | I3 closure | `docs/architecture/CARBONTALLY_P8_I3_INSIGHT_CLOSURE_20260921.md` | `VERIFIED EXISTING FOUNDATION` | Four-tool catalogue, six-point contract, status vocabulary, locator-not-grant semantics |
| 4 | OHD I3 verification + re-verification | `docs/verification/OHD-P8-I3-INSIGHT-TOOLS-INDEPENDENT-VERIFICATION-20260921.md` (`9c92742`); `docs/verification/OHD-P8-I3-INSIGHT-TOOLS-REVERIFICATION-20260921.md` (`7faaa57`) | verification evidence | Source of the carried-over observations reused in §12 and §13 |
| 5 | Master Specification v1.1 | `docs/architecture/CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION_v1.1_20260921.md` | mixed (per statement) | Primary I4 requirement source |
| 6 | Stage implementation reports | `docs/implementation/phase8/CT-P8-I1-INSIGHT-PERSISTENCE-*.md`, `…/CT-P8-I2-*.md`, `…/CT-P8-I3-INSIGHT-TOOLS-20260921.md` | implementation record | What was actually built and verified |
| 7 | Historical discovery | `docs/architecture/CARBONTALLY_PHASE8_ASK_CARBONTALLY_PERSISTENT_CONVERSATION_AND_AI_AUDITABILITY_DISCOVERY_20260912.md` | `DISCOVERY-DERIVED` | Origin of the dormant-AI-structure finding |

`FACT` — the Master Specification is **not uniformly authoritative**: §48 records that v1.1 incorporated I3 closure and material verification material, while §41 ("Open Product Decisions") and §42 ("Explicit Deferred Capabilities") deliberately retain 22 open items and 16 deferred capabilities. Authority is therefore applied per statement in §4, never to the document as a whole.
`INFERENCE` — Master Spec statements restating D2 inherit `RATIFIED`; statements describing not-yet-built I4 behaviour are `RECOMMENDED — PO DECISION REQUIRED` or `OPEN — PO DECISION REQUIRED` until the PO closes them.
`FACT` — critically, nothing in the inspected sources silently promotes a discovery-derived recommendation to a ratified requirement: §23 and §41 both preserve the dormant-AI-structure question as open, and I1's migration header explicitly records that `public.ai_content_history` "is NOT reused, migrated, altered or deleted" at I1 (`20261001000000_p8_i1_insight_persistence.sql:24–25`, enforced by test `backend/tests/unit/data/test_i1_insight_migration.py:134`).
---

## 4. I4 Requirement Matrix

Classification vocabulary: `RATIFIED` · `VERIFIED EXISTING FOUNDATION` · `DISCOVERY-DERIVED` · `RECOMMENDED — PO DECISION REQUIRED` · `OPEN — PO DECISION REQUIRED` · `DEFERRED` · `NOT AUTHORIZED`.

### 4A. Conversation / message persistence (Layer 1 — built at I1; consumed/possibly extended by I4)

| Requirement | Specification position | Implementation reality | Classification |
| --- | --- | --- | --- |
| Conversation with stable identifier | §8.1 L411–419; §9.1 L479–489 | `carbontally_insight_conversations.id uuid PK` | `VERIFIED EXISTING FOUNDATION` |
| Organization association | §9.4 L520–524 | `organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE` | `VERIFIED EXISTING FOUNDATION` |
| Creator identity | §9.5 L526–528 | `created_by uuid NOT NULL` | `VERIFIED EXISTING FOUNDATION` |
| Lifecycle state | §8.1 L419; §9.1 L484 | **absent** — only `title`, `created_at`, `updated_at` | `OPEN DECISION` (I1 deliberately deferred status vocabulary, migration header L21; I4 must decide where answer/conversation status lives) |
| Created/updated timestamps | §9.1 | both `timestamptz NOT NULL DEFAULT now()` | `VERIFIED EXISTING FOUNDATION` |
| Integrity constraints | §9.1 | `ci_conversations_id_org_unique UNIQUE (id, organization_id)` | `VERIFIED EXISTING FOUNDATION` |
| Tenant-aware indexes | §9.1 | `idx_ci_conversations_org_created (organization_id, created_at DESC)` | `VERIFIED EXISTING FOUNDATION` |
| Creator-visibility capability | §9.1; §7.3 | RLS `ci_conversations_creator_select` = `is_org_member(organization_id) AND created_by = auth.uid()` | `VERIFIED EXISTING FOUNDATION` |
| Message id/conversation/actor type/actor identity/content/timestamp/ordering | §8.1; §9.2 L491–502 | `carbontally_insight_messages` with `id`, `conversation_id`, `organization_id`, `created_by`, `role` (`user`\|`insight`), `content`, `ordinal`, `created_at` | `VERIFIED EXISTING FOUNDATION` |
| Message ordering mechanism | §9.2 L501 | explicit 1-based `ordinal` + composite FK | `VERIFIED EXISTING FOUNDATION` |
| Message may carry structured content | §9.2 L499 | current column is plain `content text` | `RECOMMENDED — PO DECISION REQUIRED` (whether Layer-1 carries structured payloads such as status/references, or whether that is Layer-2 only) |
| Assistant text must not imply authority | §9.2 L504 | by design: `role='insight'` is "author kind only: NOT an answer status" (migration comment L215–216) | `VERIFIED EXISTING FOUNDATION` |
| Shared conversation visibility (owner/admin, consultant, staff, auditor, PE) | §7.2–7.7; §41 L1875–1879 | creator-private only (`visibility_created_by`, `conversation_is_visible`, `api/insight_authz.py:322–340`) | `OPEN DECISION` |
| Human messaging must never be reused | §6.1 L314–328; §6.2 L330–347 | `public.conversations`/`messages`/`message_activity_log` untouched (I1 migration header L26–27) | `RATIFIED` |

### 4B. AI interaction persistence (Layer 2 — I4's core deliverable)

| Item | Specification position | Status today | Classification |
| --- | --- | --- | --- |
| Canonical AI interaction record | §8.1 L427–445; §8.3 L467; §35/I4 L1586 | does not exist (no table, repository or migration) | `RECOMMENDED — PO DECISION REQUIRED` (I4's scope is ratified; §9 states "the exact schema is implementation-stage work … but every schema must satisfy these invariants") |
| Actor | §9.3 L508–518 | available from `AuthUser`; I1 carries `created_by` | `RECOMMENDED` |
| Organization | §9.4 | available; I1 tables carry `organization_id NOT NULL` | `RECOMMENDED` |
| Conversation link | §8.1 L429; §9.3 | I1 conversation id available | `RECOMMENDED` |
| Question / raw request | §8.1 L431; §41 L1890 ("raw question storage versus hash") | not persisted beyond Layer-1 message text | `OPEN DECISION` |
| Interpreted request / intent | §8.1 L432; §13 L703–729 | `classify_intent` exists (`services/insight_tools.py:157`); never persisted | `RECOMMENDED — PO DECISION REQUIRED` |
| Tool invocation | §8.1 L433; §9.3 L513 | `invoke_tool` exists; nothing written (I3 is read-only by ratified design) | `RECOMMENDED — PO DECISION REQUIRED` |
| Tool result / references | §8.1 L435; §11.7 L651–658 | `ToolResult`/`InsightReference` returned to caller only | `RECOMMENDED — PO DECISION REQUIRED` |
| Provider/model attribution "when truthfully known" | §8.1 L436; §15.3 L799–813 | `configured_ai_attribution()`/`provider_label()` exist (`infra/ai_runtime.py:82–126`); precedent columns `document_processing_queue.automation_provider/model/model_version` (`20260905010000_gate5_t1_automation_provenance.sql:39–41`) | `VERIFIED EXISTING FOUNDATION` (mechanism) + `OPEN DECISION` (Insight storage target) |
| Answer status | §8.1 L437; §14 L733–754 | six-value `ToolStatus`; full taxonomy absent | `OPEN DECISION` (→ §13, §19 Q3) |
| Usage / cost "where truthfully available" | §8.1 L438; §15.4 L815–822 | **not available**: `ChatCompletionResponse` = `{text, finish_reason}` only | `RATIFIED` (NULL discipline); I4 fields must default NULL |
| Result/reference hashes | §8.1 L439 ("where appropriate") | not implemented | `RECOMMENDED — PO DECISION REQUIRED` |
| Interaction → audit reference | §35/I4 L1593 | none | `RECOMMENDED — PO DECISION REQUIRED` |
| Correlation identifiers | §27 L1242–1244 | none for Insight | `RECOMMENDED` |
| Failure recording | §26 L1189–1230; §18.1 | I3 records nothing (fail-closed); surfaces as `error`/`internal_error` | `RECOMMENDED — PO DECISION REQUIRED` |

### 4C. Canonical audit (Layer 3 — integration only; the ledger itself is not I4's to replace)

| Requirement | Specification position | Status today | Classification |
| --- | --- | --- | --- |
| Existing canonical audit ledger remains authoritative; no second ledger | §8.1 L447–451; §20.2 L1019–1023; §35/I4 L1602 | `public.audit_trail` is append-only + trigger-protected (`infra/audit_logger.py`; `data/audit.py:182`; `20260912000000_p7_audit_immutability_and_indexes.sql`: `p7_audit_trail_immutable`, trigger, 5 indexes). Four further audit-shaped tables exist: `audit_logs` (`init_schema:1647`), `processing_audit_trail` (`:914`), `review_audit_trail` (`:1870`), `activity_logs` (`:1692`) | `RATIFIED` (principle) + `OPEN DECISION` (which ledger is the canonical target — §19 Q2) |
| AI audit event establishes that the interaction occurred | §20.4 L1037–1041 | no such event type exists | `RECOMMENDED — PO DECISION REQUIRED` |
| AI audit event links to the durable interaction record | §20.4 L1039; §35/I4 L1593 | none | `RECOMMENDED — PO DECISION REQUIRED` |
| Transcript/provider payload must not enter the ledger without separate authorization | §20.4 L1041 | n/a | `RATIFIED` (negative requirement) |
| Conversation deletion must never erase the canonical audit record | §8.2 L455 | `carbontally_insight_conversations.organization_id` cascades with the organization; `audit_trail` is append-only | `RATIFIED` constraint; the cascade × audit interaction is a concrete I4 design item (→ §15) |
| Three audit layers must not be collapsed | §20.1 L1009–1017 | I1 = Layer 1 only | `RATIFIED` |
| Conversations are not part of the standard audit/evidence package by default | §20.3 L1025–1035 | n/a | `RATIFIED` |
| Mutability of the interaction record itself | §8.2 L459 ("separate lifecycle") | n/a | `OPEN DECISION` (append-only vs mutable Layer 2 is not settled) |
| Audit event structure/taxonomy | §20.4 (only "should establish … and link to") | `audit_trail` columns: `action_type`, `table_name`, `record_id NOT NULL`, `performed_by NOT NULL`, `performed_at`, `old_data/new_data/changes`, `ip_address`, `user_agent`, `metadata JSONB` | `RECOMMENDED — PO DECISION REQUIRED` (event action type for AI events) |
| Retention implications | §21 L1045–1065 ("deliberately OPEN until I7"); §42 L1917 | platform retention rows exist (`system_settings.platform_retention`, `data_retention_days`, `audit_log_retention_days`; `20260924000000_p8x_x2_operational_telemetry_retention.sql`) | `DEFERRED` (I7), `OPEN DECISION` on which knob governs Insight |
---

## 5. Existing Architecture Forensics

| Component | Exact path | Existing behaviour | Reusable for I4? | Evidence | Risk |
| --- | --- | --- | --- | --- | --- |
| LLM client | `backend/infra/llm_client.py` | Typed `LLMClient` for OpenAI/Anthropic-compatible chat completions: `base_url`, `api_key`, `model`, `timeout_seconds`; transport injectable for tests; `ChatCompletionResponse{text, finish_reason}` | Yes — the ratified single provider boundary (§15.1 "reuse CarbonTally's existing AI abstraction") | `:32–86`, `:134–149` | No usage/cost in the response; no retry/backoff at this layer |
| AI runtime / attribution | `backend/infra/ai_runtime.py` | `configured_ai_extraction_engine()` builds a client from env; `provider_label()` derives provider from URL host; `configured_ai_attribution()` → `{provider, model, model_version}`, never fabricated | Yes — answers §15.3 truthful attribution | `:39–126` | Attribution is read at call time; Insight must not record a configured provider as "used" |
| AI document extraction engine | `backend/services/ai_document_extraction.py` | `AIDocumentExtractionEngine(llm_client, max_text_chars)`; prompt template; defensive parsing (`_strip_code_fence`), field clean/coercion | Pattern reusable (bounded input, defensive parse) | `:135–246` | Not a narration layer; do not repurpose |
| Audit logger | `backend/infra/audit_logger.py` | `AuditSink` protocol; `AuditLogger.audit(...)`; decorator form; `init_audit_logger`/`reset_audit_logger`; `default_actor="system"` | Yes — the established canonical-audit write path | `:43–250` | Sink must be initialised; which sink is canonical must be settled (§19 Q2) |
| Audit repository | `backend/data/audit.py` | `AuditRepository.record()` → `public.audit_trail`; `query()` with filters incl. `metadata->>'organization_id'`, `category`, `origin`, `outcome` | Yes | `:182–215`; filters `:150–179` | `record_id` and `performed_by` are `NOT NULL` — an AI event must supply both (`_actor_uuid` mapping exists) |
| Insight persistence (Layer 1) | `backend/data/insight.py`, `backend/domain/insight.py`, `backend/api/v3_insight.py` | Conversation/message repositories, domain dataclasses, REST: create/list/get conversation, append/list messages | Yes — the parent of every Layer-2 record | `domain/insight.py:34–57`; `v3_insight.py:120–216` | Layer 1 has no status column; I4 must not retrofit one without a decision |
| Authorization boundary | `backend/api/insight_authz.py` | `authorize_insight_scope()`, persona resolution, `organization_is_active()`, `InsightAccess`, `conversation_is_visible()`, `visibility_created_by()` | Yes — mandatory call path, never re-implemented | `:104–340` | None identified |
| Tool layer | `backend/services/insight_tools.py`, `backend/domain/insight_tool.py` | Four-tool registry, six-point contract, allowlists, locator references, six-value status | Yes — I4 orchestrates, never bypasses | registry `:49–123`; statuses `:46–51` | Read-only; persistence must be added outside the tools |
| Rate limiting | `backend/middleware/rate_limit.py` | Existing middleware module | Yes for §28 | file present; behaviour not traced in this audit | §28 targets/SLOs remain `OPEN DECISION` |
| Retention service | `backend/services/retention.py` | Existing N3 retention service | Later (I7) only | file present | Do not extend in I4 |
| Repository bundle (composition root) | `backend/api/dependencies.py` | 47-field `RepositoryBundle`; `get_repositories()` constructs every repository (incl. I3's `disclosure_projection`, added during the I3 remediation) | Yes — the wiring point any I4 repository must be added to | `:353` construction site; regression `tests/unit/api/test_v3_insight_i3_wiring.py` | The I3 D-01 defect proves a test-only duck-typed bundle can mask a missing production attribute — I4 must repeat the real-wiring discipline |
| Dormant AI store | `public.ai_content_history` (`00000000000000_init_schema.sql:1041–1060`) | Columns: `organization_id NOT NULL`, `report_id`, `prompt_type NOT NULL`, `prompt_text`, `model_used`, `generated_content`, `content_format`, `tokens_used`, `processing_time_ms`, `cost`, `user_rating`, `user_feedback`, `was_accepted`, `created_at`, `created_by`; comment "AI generation history" | **Not automatically** — explicitly forbidden | Spec §23 L1090–1100; I1 migration header L24–25; `tests/unit/data/test_i1_insight_migration.py:134` | `FACT`: referenced only by migrations/tests — no application code reads or writes it; its disposition is §19 Q1 |

`FACT` — a grep for `LLMClient|ai_runtime|OPENROUTER|provider` across `backend/**/*.py` returns no Insight module, i.e. **no AI/provider code has leaked into I1–I3**; the I3 tools are purely deterministic. `INFERENCE` — the absence of any dormant-table consumer corroborates that the §23 decision is genuinely unmade rather than merely undocumented.
---

## 6. AI / Provider Boundary

`FACT` — the ratified boundary (§15.1–15.5, L775–834) and what exists:

| Requirement | Verdict | Evidence |
| --- | --- | --- |
| Reuse the single existing abstraction; no parallel provider client, no direct provider HTTP, no provider logic in application modules | Satisfiable today | `infra/llm_client.py` + `infra/ai_runtime.py`; no Insight module references a provider |
| Provider configuration stays environment-controlled | Already true | `ai_runtime.configured_ai_extraction_engine()` reads `CARBONTALLY_AI_BASE_URL`/`CARBONTALLY_AI_API_KEY`/`CARBONTALLY_AI_MODEL` (`:51–60`); `infra/config.py` holds no AI keys of its own (grep empty) |
| No API keys in database fields; secrets never logged/persisted/returned/committed | Already true; constraint on I4 | §15.2 L791–797; `ai_runtime` returns only `{provider, model, model_version}` |
| Truthful attribution: distinguish *configured* from *successfully used* | Mechanism exists; I4 must apply it honestly | §15.3 L799–813; `provider_label()` derives from host; `configured_ai_attribution()` never guesses `model_version` |
| Usage/cost NULL until truthfully available | Automatically satisfied by the abstraction | §15.4 L815–822 vs `ChatCompletionResponse{text, finish_reason}` (`llm_client.py:32–39`) |
| AI cannot determine emission value, factor, provenance, evidence identity, approval state, authorization or tenant scope | Already true structurally | §15.5 L824–834; the I3 tool layer is deterministic and I2 owns authorization |

`INFERENCE` — the provider boundary is the **strongest** part of I4's readiness: the abstraction, the env-only configuration and the truthful-attribution helper already exist and require no new provider work.
`OPEN DECISION` — §41 lists `provider selection` and `AI credits/allowances` as open; §15.2 keeps configuration environment-controlled, so no code decision is required for I4, but the PO may still wish to name the sanctioned provider(s) for production.
`RECOMMENDATION` — I4 should treat "provider invoked" as a *recorded outcome of an actual call*, not as configuration state, mirroring the Gate-5 precedent (`automation_provider/model/model_version` written from the call, `20260905010000_gate5_t1_automation_provenance.sql:13–19`).

---

## 7. Conversation / Message Persistence Analysis

`FACT` — Layer 1 exists exactly as specified in the invariants that the spec's §9.1/§9.2 make mandatory:

* Conversation: stable id, `organization_id NOT NULL`, `created_by NOT NULL`, `created_at`, `updated_at`, `UNIQUE (id, organization_id)`, tenant-leading index, creator-private RLS (`20261001000000_p8_i1_insight_persistence.sql:43–59`, policies at `:130–204`).
* Message: stable id, `conversation_id`, denormalised `organization_id` held consistent by the composite FK, author kind `role ∈ {user, insight}`, `content`, explicit 1-based `ordinal`, `created_at`; messages inherit visibility from their conversation's creator (`:157–204`).
* Naming is the ratified canonical namespace `carbontally_insight_*` (D2 §3.2.1/§3.8), i.e. a **separate conversational domain** — the human messaging tables are untouched (I1 migration header L26–27).

`FACT` — **gaps relative to §9.1/§9.2 and the I4 layer split**:

1. **No lifecycle/status column on either table.** The spec's §9.1 L484 requires "lifecycle state" for a conversation and its §8.1 L419 lists "title/status/lifecycle metadata"; the built table has `title` only. I1 recorded this as deliberate ("NO product status vocabulary (D2 §11.6 defers the exact answer-state vocabulary)"). `OPEN DECISION` — whether I4 adds lifecycle state to Layer 1 or keeps all status on Layer 2.
2. **No structured-content representation** on messages (§9.2 L499 permits "message content or structured content representation"). `RECOMMENDED — PO DECISION REQUIRED`.
3. **No write path from the tools or the AI into Layer 1 for an answer status** — by ratified I3 design (I3 is read-only; `ToolResult` carries status). I4 must decide whether an assistant answer's status is persisted in Layer 1, Layer 2, or both.
4. **No indexes for cross-conversation audit queries** beyond `(organization_id, created_at DESC)`; a Layer-2 record keyed by conversation would need its own indexes. `INFERENCE`.

`INFERENCE` — Layer 1 is a clean, sufficient parent for Layer 2: every Layer-2 record can carry the same `organization_id`/`created_by` pair plus a conversation FK, which keeps the security model uniform with I2's existing predicates.
`FACT` — the existing REST surface for Layer 1 is four routes (`POST /conversations`, `GET /conversations`, `GET /conversations/{id}`, `POST /conversations/{id}/messages`, `GET /conversations/{id}/messages` — `api/v3_insight.py:120–216`). No AI-bearing route exists yet; the only Insight tool routes are `GET /tools`, `POST /tools/invoke`, `POST /tools/intent` (`api/v3_insight_tools.py:44–68`).
---

## 8. Canonical AI Interaction Analysis (Layer 2)

`FACT` — the specification fixes the **reconstruction chain** (§9.3 L508–518) and the Layer-2 content list (§8.1 L427–439), and states that the exact schema is implementation-stage work subject to invariants. It does **not** fix: table name, column set, nullability beyond §9.4, immutability posture, or the storage form of the question.

`FACT` — spec-supported field intentions, traced item by item (full matrix in §4B). Explicitly required: actor, organization, conversation link, interpreted request, tool invocations, authoritative references, provider/model *when truthfully known*, answer status, usage/cost *where truthfully available*, result/reference hashes *where appropriate*, interaction→audit reference.
`OPEN DECISION` — the spec leaves these Layer-2 questions to the PO:
1. raw question text vs hash vs neither (§41 L1890);
2. whether tool arguments and tool results are stored verbatim, projected (allowlisted fields only) or by reference/hash (interacts with §20.4's prohibition on dumping payloads into the ledger);
3. the exact answer-status enumeration (→ §13);
4. whether Layer 2 is append-only/immutable (the spec says only "a separate lifecycle", §8.2 L459);
5. where provider/model attribution is stored for Insight — a new Layer-2 column vs the existing dormant store (§23).

`INFERENCE` — because `ChatCompletionResponse` exposes only `text`/`finish_reason`, an I4 Layer-2 row written today would truthfully carry `tokens_used = NULL`, `cost = NULL`, `provider/model` only when a call actually succeeded, and `model_version = NULL` (matching the Gate-5 rule "never fabricated").
`RECOMMENDATION` — persist the *projection actually sent to the provider* rather than the whole conversation, consistent with §17.1 ("context must be relevant, minimal, bounded, authorization-safe") and §16.4 ("the LLM must receive only the minimum information required to explain the result").

---

## 9. Canonical Audit Analysis (Layer 3)

`FACT` — the specification's position (§8.1 L447–451, §20.1–20.4 L1009–1041):

* the existing canonical audit ledger remains authoritative and must not be replaced by conversations or interaction records;
* conversation deletion must never automatically erase the canonical record;
* the three layers must not be collapsed;
* at I4, the canonical audit event "should establish that the AI interaction occurred and link to the durable interaction record";
* the entire AI transcript or provider payload must not be placed in the ledger "unless separately authorized";
* conversations are **not** part of the standard audit/evidence package by default.

`FACT` — implementation reality:

* `public.audit_trail` is the append-only, trigger-protected ledger written by `data/audit.py:182` (`INSERT INTO public.audit_trail …`), hardened by `20260912000000_p7_audit_immutability_and_indexes.sql` (immutability function + trigger + 5 indexes incl. `metadata` GIN).
* Four other audit-shaped tables exist (`audit_logs`, `processing_audit_trail`, `review_audit_trail`, `activity_logs`), so "the canonical ledger" is **ambiguous at the schema level** — the spec names no table.
* `audit_trail.record_id` and `performed_by` are `NOT NULL`; `metadata JSONB` is the natural carrier for Insight-specific context (the repository already filters on `metadata->>'organization_id'`, `category`, `origin`, `outcome`).
* No AI-related audit action type exists today.

`OPEN DECISION` — (a) which ledger receives AI audit events; (b) the action-type/metadata taxonomy for them; (c) whether the interaction record itself is immutable; (d) whether the audit event is written in the same transaction as the interaction row (→ §15).
`INFERENCE` — using `audit_trail` + the existing `AuditLogger`/`AuditRepository` path satisfies the spec's "do not create a second audit ledger" constraint with no schema invention, and requires only an agreed event taxonomy.
---

## 10. I3 → I4 Integration Analysis

`FACT` — what I3 exposes (all in the authoritative checkout, verified by OHD at `7faaa57`):

* a **closed four-tool catalogue** — `report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup` (`services/insight_tools.py:49–52`; `TOOL_DEFINITIONS` `:83`; `TOOL_REGISTRY` `:123`);
* a deterministic **intent classifier** `classify_intent(utterance)` (`:157`) returning a ranked/allowlisted decision — refusals reuse `invalid_input` with `unsupported_intent`/`ambiguous_intent` (no new status);
* a **six-point contract** per tool (`domain/insight_tool.py`: `TOOL_CONTRACT_VERSION = "i3-6point-v1"`, `ToolInputSpec`, `ToolDefinition`, bounded `MAX_IDENTIFIER_LENGTH=128`, `MAX_RESULT_ITEMS=200`);
* **authorization on every invocation** through the closed I2 boundary: `invoke_tool → _authorize → authorize_insight_scope` (`services/insight_tools.py:223–274`), then a **re-check of the resolved object's organisation**, so ids/references are never grants;
* **allowlisted projection** of results with signed/artefact URLs, internal actors, unbounded content and unratified snapshot fields deliberately omitted;
* **locator-only references** via `InsightReference` and `_dedupe_refs`;
* a six-value status vocabulary `success | no_data | not_authorized | invalid_input | provider_unavailable | error`, with `provider_unavailable` declared but never produced by I3;
* an HTTP surface `GET /tools`, `POST /tools/invoke`, `POST /tools/intent` (`api/v3_insight_tools.py:44–68`).

`FACT` — where each I4 concern lands in that path: **authorization** occurs inside I3 (I2 boundary) and must not be duplicated or bypassed; **deterministic data** is obtained only through the tools; the **provider boundary** does not exist in I3 (no AI import — grep evidence in §5), so I4 introduces the first provider call in the Insight path; **audit persistence** has no place in I3 by ratified design and must be added around it.

`FACT` (the critical inheritance rule) — the spec's P-03 (§ L255–259) and §9.6 L530–532 ("foreign keys to reports/calculations/evidence do not grant access") plus OHD's verification that a stored reference is only a locator: I4 must **re-authorize on every read**, including when replaying a stored reference, a stored tool result, or a stored conversation during context assembly. I3 already demonstrates the correct pattern: resolve, then re-check the resolved object's organisation through I2.
`INFERENCE` — the safest I4 orchestration shape is therefore: authorize (I2) → classify (deterministic) → invoke ratified tools (I3) → narrate (LLM, optional) → persist Layer 2 → link Layer 3 — with **no** new tool, no new persona and no new permission.
`OPEN DECISION` — whether classification may ever be LLM-assisted at I4 (§13.2 permits it "if a later stage uses an LLM"), and if so whether the advisory classification is persisted.

---

## 11. Authorization / Security Analysis

`FACT` — the mechanisms I4 must reuse, all present and verified in I2:

| Property | Mechanism | Verified |
| --- | --- | --- |
| Every-read reauthorization | `authorize_insight_scope()` called per request; I3 calls it per tool invocation and again on the resolved object | I2 closure; `api/insight_authz.py:206` |
| Organization isolation | `is_org_member(organization_id)` RLS + server-side org resolution; `organization_id NOT NULL` on I1 tables | migration `20261001000000` policies; `20261002000000` |
| Creator-private visibility | `visibility_created_by()` / `conversation_is_visible()` (`:322–340`); RLS `ci_*_creator_select` | I1/I2 |
| Customer role handling / forged-role rejection | `normalize_org_role()` (`:104`) — roles are normalized server-side, never trusted from client claims | I2 closure |
| Inactive/suspended organisation denial | `organization_is_active(repos, organization_id)` (`:146`) | I2 |
| Consultant / staff boundaries | `staff_context_grants_insight_scope()` (`:133`), `resolve_insight_persona()` (`:294`) | I2 closure |
| Auditor distinction | `is_auditor_principal()` (`:118`) — auditor is recognized but not granted general Insight scope | I2 closure |
| Anonymous denial | anon has `REVOKE ALL` on the Insight tables (I1 header L31) and I2 hardened the anon/authenticated grants | I1/I2 migrations |

`FACT` — "stored references are locators, never grants" holds in the closed code: I3 re-checks the resolved object's organisation after resolving any id (`services/insight_tools.py:283–380`), and I1 records the same principle in the schema comment for `created_by` ("A stored id is not a grant", migration L212).
`FACT` — carried-over OHD observations relevant to I4 security (`docs/verification/OHD-P8-I3-INSIGHT-TOOLS-REVERIFICATION-20260921.md`): (1) a valid-but-foreign identifier yields `not_authorized` while a valid-but-absent one yields `no_data`, so an authenticated caller can distinguish existence-in-another-organisation from non-existence — inherent to the ratified vocabulary, no tenant data exposed; (2) the I3 unit suite still builds a duck-typed repository bundle, so the real-wiring discipline must be repeated for I4; (3) the server-side log line can include the offending parameter value (→ §12).
`INFERENCE` — I4 introduces no new authorization concept: every I4 read (interaction record, conversation context, replayed reference) is either creator-scoped by the existing I2 predicate or organisation-scoped by the same `is_org_member` rule.
`RECOMMENDATION` — I4's authoritative test matrix should repeat I2/I3's deny tests at the new surface: cross-org, cross-creator, consultant foreign client, staff without scope, auditor, PE, anonymous, and replayed-reference-after-revocation.
---

## 12. Privacy / Data Classification

`FACT` — data I4 may handle and the current authoritative position:

| Data | May I4 persist/expose it today? | Authority | Classification |
| --- | --- | --- | --- |
| User prompts / raw question | Undecided — "raw question storage versus hash" is an explicit open item | Spec §41 L1890; §8.1 L431 | `OPEN DECISION` |
| AI responses | Layer 2 lists "the answer"; retention/deletion policy open until I7 | §8.1 L427–439; §21 L1045–1067 | `OPEN DECISION` (storage) / `DEFERRED` (retention) |
| Tool arguments ("authorized parameters") | Not settled | §8.1 L433–434 | `RECOMMENDED — PO DECISION REQUIRED` |
| Tool results / references | Layer 2 lists them; the ledger must not carry payloads | §8.1 L435; §20.4 L1041 | `RECOMMENDED — PO DECISION REQUIRED` |
| Evidence references | Locators only; I3 allowlists already exclude signed/artefact URLs | §11.7; I3 allowlists | `RATIFIED` (locator semantics) |
| Model/provider metadata | Persist only when truthfully known; never fabricated | §15.3 L799–813; Gate-5 precedent | `RATIFIED` |
| Usage / cost | Must be NULL until truthful | §15.4 L815–822 | `RATIFIED` |
| Error details | Safe categories only; no secrets/tokens/raw customer content in logs | §27 L1246–1253; §31 | `RATIFIED` |
| Correlation identifiers | Supported for observability ("interaction/audit identifiers once I4 exists") | §27 L1244 | `RECOMMENDED` |
| Diagnostic information | Server-side logging permitted; never in the public response | PO I3 remediation §3; OHD re-verification L193/L196 | `RATIFIED` |

`FACT` — the OHD observation the PO asked to be examined: the I3 re-verification report records that "the server-side log line carries the exception text, which can include the offending parameter value (observed for a malformed identifier). That is intended server-side diagnosability and never reaches the public response" (`docs/verification/OHD-P8-I3-INSIGHT-TOOLS-REVERIFICATION-20260921.md:196`, restated at `:287`). The implementation is `logger.exception("insight tool %s failed", tool.name)` (`services/insight_tools.py`), which passes **only the tool name** as a format argument; the parameter value can appear solely inside the exception text. `INFERENCE` — this becomes material at I4 because Insight will handle customer questions and document-derived text, so any provider/tool error logged via `logger.exception` could capture prompt fragments through exception messages. `RECOMMENDATION` — I4 should keep the I3 logging pattern (log the failure class, not the payload) and restate §27's prohibition list in its implementation report.

`FACT` — retention/deletion/export are expressly not I4's: "deliberately OPEN until I7" (§21 L1047), "No retention duration or legal policy may be invented by implementation agents" (§21 L1065), and §42 defers retention enforcement and export. `FACT` — billing/credits are I8 (§22 L1071–1086): no parallel Insight billing system, no invented credits/quotas/pricing.
`FACT` — the platform already holds retention configuration (`system_settings` keys incl. `data_retention_days`, `audit_log_retention_days`, `operational_telemetry_retention_days` — `20260924000000_p8x_x2_operational_telemetry_retention.sql`) and an existing retention service (`backend/services/retention.py`), so I7 has a home; I4 must not pre-empt it.
---

## 13. Failure / Status Analysis

`FACT` — two vocabularies coexist in the authoritative sources:

* **Closed I3 implementation** (`domain/insight_tool.py:46–51`): `success`, `no_data`, `not_authorized`, `invalid_input`, `provider_unavailable`, `error` — with `provider_unavailable` declared but unreachable (I3 makes no provider call) and intent refusals reusing `invalid_input` (`unsupported_intent` / `ambiguous_intent`).
* **Master Spec §14** (L737–752) enumerates fourteen answer states, adding `zero`, `insufficient_data`, `needs_clarification`, `tool_failure`, `partial`, `rate_limited`, `refused`, `ungrounded` and splitting `success/answered`; §14 also fixes `zero ≠ no_data ≠ not_authorized` (L756–769) and P-06 repeats it (L279–291).
* **§26** maps failure modes to states: provider outage → deterministic result if available, else `provider_unavailable` (L1191–1197); required tool failure → `tool_failure` (L1199–1205); authorization failure → `not_authorized` without revealing protected contents (L1207–1211); empty result → `no_data`, never zero (L1213–1217); ambiguous request → `needs_clarification` (L1219–1223); partial → explicitly identify what was and was not established (L1225–1227).

`FACT` — §14 states "the final exact taxonomy may be normalized during implementation, but the semantic distinctions are mandatory" (L754).
`INFERENCE` — I4 therefore cannot simply reuse the six I3 statuses: it must either extend the answer-status enumeration to cover the I4-specific states, or define and document a mapping of provider/tool failures onto the existing six. Because §26 names states absent from the closed I3 vocabulary, this is an outward-facing contract change → `OPEN DECISION` (§19 Q3).
`FACT` — no such status exists in code today: there is no `tool_failure`, `needs_clarification`, `zero`, `partial`, `rate_limited`, `refused`, `insufficient_data` or `ungrounded` value anywhere in `backend/`.
`FACT` — no timeout/retry/rate-limit semantics for Insight exist in code; §28 (rate limiting/abuse) and §26.1 (provider outage) are specification text only, while `backend/middleware/rate_limit.py` provides a platform mechanism that could be reused.
`RECOMMENDATION` — persist the **tool-level** status (I3's closed vocabulary) and the **answer-level** status (to be decided) as distinct fields, preserving §14's semantic distinctions instead of collapsing them.

---

## 14. Deterministic-First Analysis

`FACT` — the principle is ratified (P-04, L261–266) and satisfied on every existing path: the four I3 tools read authoritative rows through repositories, project allowlisted fields, and never call a provider; intent classification is deterministic (`classify_intent`, `services/insight_tools.py:157`).
`FACT` — §15.5 (L824–834) forbids AI from determining emission value, factor, calculation provenance, evidence identity, report approval state, authorization or tenant scope; §16.4 (L869–873) requires tool results to be structured application data with only the minimum information passed to the model; §16.5 (L875–883) requires explicit defence against direct injection, indirect injection in documents, tool-result injection, conversation poisoning and stored malicious instructions; §17.1 (L889–898) requires relevant, minimal, bounded, authorization-safe context.
`INFERENCE` — hallucination risk at I4 is confined to **narration** (explaining an already-computed, already-authorized projection), because the raw rows never reach the model; the deterministic layer bounds the blast radius.
`OPEN DECISION` — §41 leaves "exact context/compaction policy" open; §17.2 ("current authority beats history", L900+) states the rule without fixing the mechanism, and §17.4 compaction is I5 material.
`FACT` — no retrieval architecture exists or is authorized: no RAG, embeddings, vector store or orchestration framework in the Insight path, and §42 L1906–1909 defers all of them.
`RECOMMENDATION` — I4 should add no retrieval mechanism; deterministic tool selection plus bounded projection is the ratified grounding path, and the provider boundary should remain a single narration call.
---

## 15. Reliability / Idempotency / Concurrency

`FACT` — the specification requires data-integrity/concurrency treatment (§32) and partial-failure honesty (§26.6), but defines **no** Insight-specific retry, idempotency or transaction semantics. Positions below are therefore `OPEN DECISION` unless marked otherwise.

| Concern | Existing reusable infrastructure | I4 position |
| --- | --- | --- |
| Duplicate user submissions | platform precedent only (`20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql`, deterministic calculation request ids) | `OPEN DECISION` — client idempotency key vs server dedupe window |
| Request retries | `backend/middleware/rate_limit.py` exists; no retry policy | `OPEN DECISION` |
| Provider retries / timeout | per-request `timeout_seconds` with a default constant (`infra/llm_client.py:24`, `:57–77`); no retry/backoff at this layer | `OPEN DECISION` (§26.1 requires non-fabrication, not a retry count) |
| Duplicate messages | explicit 1-based `ordinal`; no uniqueness constraint on `(conversation_id, ordinal)` seen in the inspected DDL | `INFERENCE` — concurrent appends could collide; verify in I4 |
| Concurrent AI interactions | no locking concept exists | `OPEN DECISION` |
| Duplicate audit records | `audit_trail` append-only, no dedupe key for AI events | `OPEN DECISION` — deterministic event id vs unique constraint |
| Correlation identifiers | platform request ids in middleware; §27 anticipates "interaction/audit identifiers once I4 exists" | `RECOMMENDED` |
| Transaction boundaries | repositories share one asyncpg pool; `AuditRepository.record()` is a single insert | `OPEN DECISION` — atomic interaction+audit commit |
| Partial-failure recovery | §26.6 requires explicitly partial answers | `RECOMMENDED` |
| Cascade interaction | `carbontally_insight_conversations.organization_id … ON DELETE CASCADE`; a Layer-2 row parented on a conversation would cascade too, while §8.2 forbids conversation deletion erasing the canonical audit record | `INFERENCE` — Layer 2 should not hard-cascade from the conversation if the record must stay reconstructable; a concrete I4 schema decision |

`FACT` — the I3 remediation supplies a directly applicable precedent: I3 was verified to contain no `INSERT`/`UPDATE`/`DELETE`/`save` statement and to create no duplicate snapshots, and `tests/unit/api/test_v3_insight_i3_wiring.py` asserts determinism by comparing two invocations byte-for-byte.
`RECOMMENDATION` — carry that determinism discipline into I4 (identical inputs → identical persisted projection, modulo ids/timestamps) and specify idempotency keys, retry counts and atomicity **in the authorization decision**, since they change persisted state semantics.
---

## 16. Database / Migration Analysis

`FACT` — existing structures relevant to I4 (all paths in the authoritative checkout):

| Structure | Location | Notes for I4 |
| --- | --- | --- |
| `public.carbontally_insight_conversations` | `20261001000000_p8_i1_insight_persistence.sql:43` | Layer-1 parent; `organization_id NOT NULL` + `ON DELETE CASCADE`; `UNIQUE (id, organization_id)`; creator-private RLS; **no status column** |
| `public.carbontally_insight_messages` | same file | `role ∈ {user, insight}`; explicit `ordinal`; composite-FK organisation guarantee; message-site RLS inherited from the conversation's creator |
| `public.audit_trail` | `00000000000000_init_schema.sql:1669`; hardened by `20260912000000_p7_audit_immutability_and_indexes.sql` | Append-only + trigger-immutable; `record_id`/`performed_by` NOT NULL; `metadata JSONB` GIN-indexed; already filtered by `metadata->>'organization_id'`/`category`/`origin`/`outcome` in `data/audit.py` |
| `public.audit_logs` | `init_schema:1647` | Second, older audit table (`user_id`, `staff_id`, `organization_member_id`, `organization_id`, `action`, `resource_type`) — the ambiguity source for §19 Q2 |
| `public.processing_audit_trail` / `public.review_audit_trail` / `public.activity_logs` | `init_schema:914 / 1870 / 1692` | Domain-specific; not candidates for AI events |
| `public.ai_content_history` | `init_schema:1041–1060` | Dormant AI store (`prompt_type`, `prompt_text`, `model_used`, `generated_content`, `tokens_used`, `cost`, `processing_time_ms`, `user_rating`, `user_feedback`, `was_accepted`); **no application code references it** (grep evidence §5); disposition = §19 Q1 |
| `document_processing_queue.automation_provider/model/model_version` | `20260905010000_gate5_t1_automation_provenance.sql:39–41` | Precedent for truthful attribution columns (`VARCHAR(120/240/120)`), populated from actual calls |
| retention keys in `public.system_settings` | `20260924000000_p8x_x2_operational_telemetry_retention.sql` | Retention home for I7; must not be extended at I4 (§21 "open until I7") |
| RLS/privilege hardening series | `20260920000000` (anon containment), `20260922000000` (authenticated grant hardening), `20260923000000` (anon default privileges), `20260925000000` (group-1 enablement) | Any new I4 table must be added to the explicit anon/authenticated posture, as I1 did (REVOKE ALL for anon; SELECT+INSERT only for authenticated) |

Potential I4 changes, classified (no implementation decision taken):

* `NEW STRUCTURE APPARENTLY REQUIRED` — the Layer-2 AI interaction record: organisation, creator, conversation link, interpreted intent, tool invocations, references, provider/model (nullable), answer status, nullable usage/cost, correlation id, timestamps.
* `EXISTING — REUSE` — `public.audit_trail` via `AuditLogger`/`AuditRepository` for the Layer-3 event (subject to §19 Q2).
* `EXISTING — REUSE` — `audit_trail.metadata` for Insight context (already queryable); no new audit table.
* `UNRESOLVED` — whether `ai_content_history` becomes the bounded home for AI interaction/cost/rating data, stays dormant, or is formally retired (§23 forbids automatic reuse, automatic deletion or creating a duplicate AI-history store).
* `UNRESOLVED` — whether Layer 1 gains lifecycle status and/or structured message content.
* `NEW STRUCTURE APPARENTLY REQUIRED (small)` — indexes for investigation queries (by organisation, by time, by conversation) if the PO requires them.
* `UNRESOLVED` — created-creator-visible RLS posture and grant model for any new I4 table (the I1 pattern is the established precedent, not an assumption).

`FACT` — no I4 migration exists, and no migration may be created under this audit. `INFERENCE` — the likely I4 footprint is one additive migration for the Layer-2 table (+ indexes + explicit grants/RLS) and **no** change to `audit_trail` itself, which already satisfies the append-only requirement.
---

## 17. Testing Readiness

`FACT` — existing tests directly relevant to I4 (names are real files in the authoritative checkout):

| Area | Existing coverage | Gap I4 must fill |
| --- | --- | --- |
| I1 persistence/migration | `backend/tests/unit/data/test_i1_insight_migration.py` (asserts canonical naming, dormant `ai_content_history` untouched, no I2–I8 leakage) | Layer-2 migration + schema tests |
| I2 authorization contracts | `backend/tests/unit/data/test_i2_insight_authorization_contracts.py`; RLS-live `backend/tests/unit/data/test_i2_insight_rls_live.py`; API `backend/tests/unit/api/test_v3_insight_i2_authorization.py` | Same matrix re-applied to I4 surfaces |
| I2/I3 endpoints | `backend/tests/unit/api/test_v3_insight_endpoints.py` | I4 orchestration endpoint tests (HTTP → wiring → authz → repository) |
| I3 tools | `backend/tests/unit/api/test_v3_insight_i3_tools.py` (30) + `test_v3_insight_i3_wiring.py` (5, real repository construction) | Reuse the real-wiring discipline for every I4 repository |
| Provider abstraction | `backend/tests/unit/infra/test_llm_client.py`, `test_ai_runtime.py`; integration `backend/tests/integration/test_llm_client.py` | Provider **fake** for I4 narration, provider-failure path, `provider_unavailable` behaviour |
| AI extraction engine | `backend/tests/unit/services/test_ai_document_extraction.py`, `unit/engines/test_ai_extraction.py`, `integration/test_ai_extraction.py` | Pattern reuse (fake transport), not direct reuse |
| Audit | `backend/tests/unit/infra/test_audit_logger.py` | AI audit-event emission and linkage tests |
| Shared fakes | `backend/tests/unit/api/fakes.py` (the in-memory `RepositoryBundle`; must be extended for any new I4 repository, as was required for I3's D-01 fix) | — |

`FACT` — the specification's testing contract is explicit: §33.1 unit (status mapping, validation, authorization predicates, serialization, allowlists, registry, intent, provider error mapping); §33.2 "use real repository interfaces. Do not rely only on fake attributes that production repositories do not provide"; §33.3 real RLS on disposable databases; §33.4 at least one HTTP end-to-end test per critical tool; §33.5 security tests for every §24 threat; §33.6 "core deterministic functionality must pass without an LLM provider"; §33.7 AI evaluation (grounding, refusal correctness, citation correctness, authorization boundary, prompt injection, stale context, ambiguity, hallucination resistance, status correctness) once I4/I5 are authorized.
`FACT` — the integration harness performs destructive setup and is env-guarded (`AGENTS.md` §55.1, `F-046-1`), so I4's live-RLS/DB tests must target a disposable clone, never the demo/QA database.
`INFERENCE` — testing readiness is **high**: the deterministic layers are already covered, provider tests already exist at unit level, and a precedent exists for both a fake transport and for a real-wiring repository test. The gaps are additive (new table, new service, new endpoints), not structural.

---

## 18. Proposed I4 Implementation Footprint (analysis only)

| Area | Exact existing path | Expected I4 change | Confidence | Evidence |
| --- | --- | --- | --- | --- |
| Migration (Layer 2) | `supabase/migrations/` (next timestamp) | New additive migration: interaction table + indexes + explicit RLS/grants (no change to `audit_trail`) | `MEDIUM — strongly indicated` | §8.1/§9.3; I1 migration pattern |
| Dormant-table conversion | `public.ai_content_history` | **No change** unless the PO decides to make it the bounded home | `LOW — specification-dependent` | §23 L1090–1100; §41 |
| Layer-2 repository | `backend/data/` (new module following `backend/data/insight.py`) | New repository + domain dataclass | `HIGH` | `data/insight.py`; `domain/insight.py:34–57` |
| Repository wiring | `backend/api/dependencies.py` (`RepositoryBundle`, `get_repositories()` at `:353`) | Additive field + construction, **plus** real-wiring regression test | `HIGH` | I3 D-01 remediation (`651f8c1`); `tests/unit/api/test_v3_insight_i3_wiring.py` |
| Orchestration service | `backend/services/` (new module beside `services/insight_tools.py`) | Authorize → classify → invoke ratified tools → optional narration → persist Layer 2 → link Layer 3 | `MEDIUM` | §9.3; `services/insight_tools.py:223–380` |
| Provider use | `backend/infra/llm_client.py`, `backend/infra/ai_runtime.py` | Reuse `LLMClient` + `configured_ai_attribution()`; never store secrets | `HIGH — code-traced` | `llm_client.py:44–86`; `ai_runtime.py:103–126` |
| Canonical audit integration | `backend/infra/audit_logger.py`, `backend/data/audit.py:182`, `public.audit_trail` | Emit one AI audit event referencing the interaction row; no payload dump | `MEDIUM` | §20.4; §19 Q2 |
| API surface | `backend/api/v3_insight.py` (conversations) or a new I4 route module beside `v3_insight_tools.py` | New request endpoint(s) for conversational answers | `MEDIUM` | Existing route layout |
| Status vocabulary | `backend/domain/insight_tool.py:39–51` | Possibly a new answer-status enum (PO decision) — do **not** silently extend the closed I3 enum | `LOW — specification-dependent` | §14 L737–754 vs I3 code |
| Tests | `backend/tests/unit/{api,data,infra,services}`, `backend/tests/integration/` | New unit/API/real-wiring/RLS/provider-fake/audit tests | `HIGH` | §33; existing suites |
| Fakes | `backend/tests/unit/api/fakes.py` | Extend the in-memory bundle for any new repository (mandatory, D-01 lesson) | `HIGH` | I3 remediation |
| Not in I4 | `backend/services/retention.py`, `system_settings` retention keys, billing modules, any RAG/vector dependency | Untouched | `HIGH` | §21, §22, §42 |

`FACT` — no path above is fabricated: every one is an existing file or an established directory. `INFERENCE` — the footprint is bounded and additive; the only genuinely new persisted state is the Layer-2 table.
---

## 19. Open PO Decisions

Each item is mandatory to close before I4 authorization unless marked as non-blocking. "Blocking" here means: the decision changes persisted schema or an outward-facing contract, so an implementation agent cannot proceed without inventing policy.

| # | Decision | Current specification position | Unresolved portion | Why it matters | Blocking? |
| --- | --- | --- | --- | --- | --- |
| Q1 | Disposition of the dormant `public.ai_content_history` | §23 "do not automatically reuse / delete / create a duplicate AI-history store"; "the I3/I4 repository-driven decision must select one bounded home for AI interaction/cost/rating data" | Which home is chosen: extend/rename the dormant table, leave it dormant and create a new Layer-2 table, or formally retire it | Determines whether I4 writes to an existing table or creates a new one; §23 forbids implementing agents from choosing | **Yes** |
| Q2 | Which audit ledger is canonical for AI events | §8.1/§20.2 "the canonical CarbonTally audit ledger remains authoritative" (no table named) | `audit_trail` vs `audit_logs` (both exist; a third/fourth/fifth audit-shaped table also exist) | Determines the write target and the audit event taxonomy; §35/I4 forbids a second ledger | **Yes** |
| Q3 | Answer-status enumeration for I4 | §14 lists 14 states and says the taxonomy "may be normalized"; §26 mandates `tool_failure`, `needs_clarification`; I3 closed a six-value vocabulary | Whether to extend the vocabulary for I4, map onto the existing six, or keep tool-level and answer-level statuses separate | Outward-facing contract; §14's semantic distinctions are mandatory, but §26's states do not exist in code | **Yes** |
| Q4 | Raw question/context persistence | §41 "raw question storage versus hash"; §17.1 context must be minimal and authorization-safe | Store raw text, a hash, a projection, or nothing | Privacy exposure of customer questions; interacts with §21 retention | **Yes** |
| Q5 | Layer-2 mutability/immutability posture | §8.2 "AI interaction records have a separate lifecycle" (no immutability statement) | Append-only vs mutable/correctable | Determines schema (triggers/constraints) and audit claim strength | **Yes** |
| Q6 | Tool argument/result persistence depth | §8.1 lists "tool calls", "authorized parameters", "tool results/references"; §20.4 forbids payload dumps into the ledger | Verbatim vs allowlisted projection vs reference/hash only | Controls privacy surface and storage growth; must stay consistent with I3's allowlist philosophy | **Yes** |
| Q7 | Conversation/message lifecycle status | §8.1 L419 mentions "status/lifecycle metadata"; §9.1 L484 requires lifecycle state; I1 deliberately omitted it | Whether Layer 1 gains status, or all status lives on Layer 2 | Schema change on a closed I1 table vs new Layer-2 column | **Yes** |
| Q8 | Shared conversation visibility (owner/admin, consultant, staff, auditor, PE) | §7.2–7.7 surface definitions; §41 lists all five as open | Whether any sharing exists at all, and with whom | Changes authorization scope and RLS; currently creator-private only | **Yes** (or explicitly confirm "no change at I4") |
| Q9 | Interaction→audit linkage semantics | §20.4 "should establish that the AI interaction occurred and link to the durable interaction record" | One audit event per interaction vs per tool call; correlation id scheme | Determines reconstructability and event volume | **Yes** |
| Q10 | Idempotency/retry/atomicity semantics | §32 requires integrity/concurrency treatment; §26.1 provider-outage behaviour; no Insight-specific rule | Idempotency key, retry counts, transaction boundary for interaction+audit | Persisted-state semantics cannot be invented | Recommended before implementation, **not** strictly required for authorization |
| Q11 | Provider unavailable path | §26.1: return deterministic result where available, else `provider_unavailable` | Whether narration is optional for every answer (deterministic answer is the deliverable) | Determines whether AI is optional or mandatory in the I4 experience | **Yes** (small) |
| Q12 | Retention/deletion/export (Insight) | §21 "deliberately OPEN until I7"; §42 defers retention enforcement and export | All of it | Governs how long Layer 1/2 persist | `DEFERRED` — non-blocking for I4 if Layer 2 is built retention-neutral |
| Q13 | Billing/credits/allowances | §22 OPEN until I8; reuse existing billing infrastructure | All of it | Commercial policy | `DEFERRED` — non-blocking |
| Q14 | Provider selection / SLO targets / AI evaluation scope | §41 lists "provider selection", "exact performance/SLO targets"; §33.7 requires AI evaluation once I4/I5 authorized | Which provider(s) are sanctioned; which evaluation set is required | Affects acceptance criteria, not schema | Recommended before implementation |

`FACT` — every entry above is drawn from the specification's own open-decision list (§41), its explicit deferrals (§21/§22/§42), or a documented internal inconsistency (Q2, Q3). `INFERENCE` — none of these decisions can be inferred from the code, because the code deliberately stops at the Layer-1 boundary.
`RECOMMENDATION` — closing Q1–Q3, Q5–Q9 and Q11 would be sufficient for a responsible I4 authorization decision; Q4 and Q10 could be closed in the same record or delegated with explicit bounds.
---

## 20. Explicit Non-Goals / Not Authorized

`FACT` — this audit performed **no** implementation. The following remain unauthorized and untouched:

* **I4 itself** — `NOT AUTHORIZED` (Master Spec §35/I4 line 1582; PO governance state). No Layer-2 AI interaction record, no AI audit event, no provider call in the Insight path, no answer-status implementation.
* **I5–I8** — `NOT AUTHORIZED`: context management/compaction (I5), Insight UI (I6), privacy/retention/export (I7), billing/production hardening (I8).
* **Explicitly deferred capabilities** (§42 L1904–1920): RAG, embeddings, vector databases, LangChain or any orchestration framework, unrestricted retrieval, autonomous actions, consultant/auditor/PE/broad-staff Insight, billing, retention enforcement, export, production hardening, report lifecycle modification.
* **Prohibited I4 actions by specification** (§35/I4 L1596–1602): altering authoritative carbon facts, bypassing I2, creating arbitrary tools, introducing RAG, creating a second audit ledger.
* **Repository boundaries honoured by this audit:** no application code, migration, schema, API route, frontend, dependency, configuration, deployment file or test was created or modified; nothing was installed; no branch switch, merge, rebase, reset, clean, prune or remote change was performed; the only permitted repository change is this report.
* **Data-safety boundaries honoured:** no production or demo database was accessed; no destructive harness was pointed at a persistent environment; no external provider was invoked; no secret was read, printed or introduced.

## 21. Readiness Verdict

# `NOT READY — SPECIFICATION GAPS`

**Basis (all traceable):**

1. `FACT` — I4's schema, status taxonomy and audit target are defined by documents that explicitly leave them open or undecided: §41 (22 open decisions), §21/§22 (retention and billing open until I7/I8), §23 (bounded home for AI interaction/cost/rating data not selected), and §14 vs §26 vs the closed I3 vocabulary (status inconsistency).
2. `FACT` — at least nine decisions in §19 change persisted schema or an outward-facing contract, and the specification forbids implementation agents from inventing them ("Implementation agents must not invent these decisions", §41 L1898; "No retention duration or legal policy may be invented by implementation agents", §21 L1065).
3. `FACT` — **no architectural blocker exists**: provider client, truthful attribution, audit write path, Layer-1 persistence, authorization boundary, tool layer, rate limiter, retention service, RLS/grant patterns and migration conventions are all present, code-traced and independently verified.
4. `INFERENCE` — the gap is therefore one of *specification/decision closure*, not technical feasibility. Closing §19 Q1–Q3, Q5–Q9 and Q11 would move this verdict to `READY FOR PO AUTHORIZATION REVIEW` without further forensic work.

**Explicitly not claimed:** this audit does **not** recommend that I4 be authorized, does **not** constitute authorization, and does not declare I4 approved, implemented or verified. **I4 remains NOT AUTHORIZED.**
---

## 22. Evidence / Commands / Files Inspected

**Guard and repository-state commands (read-only):** `pwd`; `git rev-parse --show-toplevel`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse github/p8-release-reconciled`; `git rev-list --left-right --count github/p8-release-reconciled...HEAD`; `git status --short`; `sha256sum` and `stat` on the two canonical PO documents; `grep -n '^#\{1,4\} '` for the specification heading map; `ls supabase/migrations | wc -l`; directory listings of `backend/{data,services,api,infra}` and `backend/tests/unit/infra`; targeted `grep`/`sed` over migrations and modules for provider/AI references, audit tables, retention keys, status vocabulary and test coverage. No write command was executed against any database, service or external provider.

**Canonical documents inspected (authoritative checkout):**

* `docs/architecture/CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION_v1.1_20260921.md` — §3.3, §7 (7.3/7.7), §8, §9, §13, §14, §15, §16, §17, §18, §20, §21, §22, §23, §26, §27, §33, §35 (I1–I4), §41, §42, §48. SHA-256 `8f9e5a3f17729a1a39abc7bec3007a5a54ca652b60af6f8d79035f9acaeeea49`, 2,178 lines.
* `docs/architecture/CARBONTALLY_P8_I3_INSIGHT_CLOSURE_20260921.md` — SHA-256 `b75215bd982a47e439db221fa6f17a6a9b016ccc2ff7dfbd7e1943d09200a339`.
* `docs/architecture/CARBONTALLY_P8_I2_INSIGHT_CLOSURE.md` — the I2 closure precedent (`CLOSED — VERIFIED PASS at 177dff5`, commit `551f121`).
* `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` — governing ratification, cited through the specification's authority hierarchy and the I1 migration authority header.
* `docs/verification/OHD-P8-I3-INSIGHT-TOOLS-INDEPENDENT-VERIFICATION-20260921.md` (commit `9c92742`) and `docs/verification/OHD-P8-I3-INSIGHT-TOOLS-REVERIFICATION-20260921.md` (commit `7faaa57`) — carried-over observations at `:193`, `:196`, `:227`, `:246`, `:266`, `:275`, `:287`.
* `docs/implementation/phase8/CT-P8-I3-INSIGHT-TOOLS-20260921.md` — §14 remediation record (real-wiring fix, error-boundary logging).

**Code / schema inspected:** `backend/api/dependencies.py`; `backend/api/v3_insight.py`; `backend/api/v3_insight_tools.py`; `backend/api/insight_authz.py`; `backend/data/insight.py`; `backend/data/audit.py`; `backend/domain/insight.py`; `backend/domain/insight_tool.py`; `backend/services/insight_tools.py`; `backend/services/ai_document_extraction.py`; `backend/infra/llm_client.py`; `backend/infra/ai_runtime.py`; `backend/infra/audit_logger.py`; `backend/infra/config.py`; `backend/middleware/rate_limit.py`; `backend/services/retention.py`; `supabase/migrations/00000000000000_init_schema.sql`; `20260905010000_gate5_t1_automation_provenance.sql`; `20260912000000_p7_audit_immutability_and_indexes.sql`; `20260924000000_p8x_x2_operational_telemetry_retention.sql`; `20261001000000_p8_i1_insight_persistence.sql`; `20261002000000_p8_i2_insight_authorization.sql`; plus the RLS hardening series `20260920000000`, `20260922000000`, `20260923000000`, `20260925000000`.

**Tests inspected (by name; content where cited):** `tests/unit/data/test_i1_insight_migration.py`; `tests/unit/data/test_i2_insight_authorization_contracts.py`; `tests/unit/data/test_i2_insight_rls_live.py`; `tests/unit/api/test_v3_insight_i2_authorization.py`; `tests/unit/api/test_v3_insight_endpoints.py`; `tests/unit/api/test_v3_insight_i3_tools.py`; `tests/unit/api/test_v3_insight_i3_wiring.py`; `tests/unit/infra/test_llm_client.py`; `tests/unit/infra/test_ai_runtime.py`; `tests/unit/infra/test_audit_logger.py`; `tests/unit/services/test_ai_document_extraction.py`; `tests/unit/engines/test_ai_extraction.py`; `tests/integration/test_llm_client.py`; `tests/integration/test_ai_extraction.py`; `tests/unit/api/fakes.py`.

**Explicit limitations of this audit:** no live database query was executed, so schema conclusions derive from migration DDL only; `backend/middleware/rate_limit.py` behaviour and the platform request-id mechanism were confirmed to exist but not traced in depth; the D2 ratification document was used as background via the specification's authority hierarchy and the I1 migration's authority header rather than read line-by-line; no AI evaluation was run (impossible while I4/I5 remain unauthorized); and nothing in this audit was independently verified by a second agent — it is Cline's own forensic analysis and requires OHD/PO review before any decision relies on it.
