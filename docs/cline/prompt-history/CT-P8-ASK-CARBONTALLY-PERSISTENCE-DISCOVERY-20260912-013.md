# CT-P8-ASK-CARBONTALLY-PERSISTENCE-DISCOVERY-20260912-013

**Prompt ID:** `CT-P8-ASK-CARBONTALLY-PERSISTENCE-DISCOVERY-20260912-013`
**Date:** 2026-09-12
**Task purpose:** Phase 8 repository-grounded discovery and architecture analysis for persistent
**Ask CarbonTally** conversations and AI-interaction auditability, following the Product Owner
decision that Ask CarbonTally conversations are persisted.
**Type:** DISCOVERY / DESIGN ONLY. No implementation. No schema, migration, RLS, route, frontend,
provider, billing, messaging, or production change.
**Task status:** `COMPLETED — DISCOVERY COMPLETE, READY FOR PO REVIEW`

## Repository State at Start

| Item | Value |
|---|---|
| Branch | `main` |
| Starting HEAD | `6409956b714b291eea6cd2e76c080aca9c00e3ec` |
| Relation to origin | 8 commits ahead of `origin/main`, **not pushed** |
| Pre-existing modified | 208 |
| Pre-existing untracked | 52 |
| Staged | 0 |

## Authoritative Inputs Reviewed

`docs/audit/openhands/CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md` (633 lines — the existing
Ask/assistant design) · `backend/infra/llm_client.py` · `backend/infra/ai_runtime.py` ·
`backend/services/ai_document_extraction.py` · `frontend/src/public/assistant/AssistantWidget.jsx`
+ `assistantKnowledge.js` · `backend/api/v3_messaging.py` · `backend/data/messaging.py` ·
`backend/domain/messaging.py` · `frontend/src/components/chat/*` · `backend/api/admin_audit.py` ·
`backend/data/audit.py` · `backend/domain/audit.py` · `backend/data/reporting.py` (`audit_package`)
· `backend/api/v3_pe.py` · `backend/api/consultant_auth.py` · `backend/api/operations_auth.py` ·
`supabase/migrations/00000000000000_init_schema.sql` · `20260803000000_rc2_rls.sql` ·
`20260807070000_add_new_table_rls.sql` ·
`20260824020000_d37_0_billing_security_and_configurable_subscription.sql` ·
`20260902040000_phase5_pe_operational_messaging.sql` ·
`20260912000000_p7_audit_immutability_and_indexes.sql` · prior prompt histories `-011`/`-012`
inputs.

## Method

Repository evidence only. **No production access, no live database access, no migration execution,
no provider credentials.** Every claim is traceable to a file and, where possible, a line range.
Three claims are explicitly `[UNVERIFIED]` because closing them would require live database access,
which the stop conditions forbid.

## Key Findings

1. **Ask CarbonTally does not exist.** Strict search for `ask_*` tables, `/api/v3/ask*` routes, and
   `AskCarbonTally` across `backend/`, `supabase/`, `frontend/src/` returns **zero** results.

2. **A substantial design already exists** — `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md`
   (OHD, `docs/audit/openhands/`, **design-only / unratified**) specifies personas, a knowledge
   allowlist + retrieval design, a persona tool registry with a six-point tool contract,
   prompt-injection defence, the PE document boundary, a provider abstraction, context handling,
   audit-logging intent, phases 1–7, and eight open PO decisions.

3. **The existing design contradicts the new PO decision on persistence.** §9 says *"Bounded
   rolling context (last N turns) per session. Sessions are short-lived in the browser"*; §10.2 says
   *"Log per conversation event … session id"*. The PO decision **supersedes** both. Recorded as
   risk **R-1** and requires PO acknowledgement — not a silent rewrite.

4. **The AI foundation is reusable and already obeys the brief's rules.** `LLMClient` (single
   OpenAI/Anthropic-compatible abstraction, injectable transport, `AIExtractionFailedError` on every
   failure), `ai_runtime.provider_label()` / `configured_ai_attribution()` (truthful; API key never
   read), and `ai_document_extraction.py`'s boundary (*candidate-only, never a false success, no
   credentials or raw document content persisted*). **No second LLM abstraction is needed.**

5. **The human messaging tables must not carry Ask — proven, not asserted.**
   `MessagingRepository.list_conversations_for_org()` filters on `organization_id` **only**
   (`backend/data/messaging.py:129-141`), and entity threads are kept out solely by storing `NULL`
   org (`create_entity_conversation()`). An Ask conversation with an org id **would appear in the
   customer's human messaging list**. `messages` is person-to-person by construction
   (`sender_id`/`receiver_id`/`is_read`/`delivered_at`/`read_by`), with no actor type, tool calls,
   references, or status columns.

6. **The audit architecture both helps and constrains.** `audit_trail` is append-only for **every
   role** via `p7_audit_trail_immutable()` (BEFORE UPDATE OR DELETE → `RAISE EXCEPTION`), and the
   migration states a future retention/purge process *"must deliberately drop this trigger first
   (documented, controlled)"*. The Phase 7 taxonomy (`domain/audit.py`) has **no AI category**, and
   `OUTCOMES` is deliberately only `success`/`failure` — so the required answer lifecycle
   (`no_data`, `insufficient_data`, `unauthorized`, `tool_failure`, `provider_unavailable`,
   `ungrounded`, `partial`, `needs_clarification`, `rate_limited`, `refused`) **must live in the Ask
   domain**, not in the audit taxonomy.

7. **Dormant asset discovered:** `public.ai_content_history` (`init_schema.sql:1041-1060`) —
   `prompt_type`, `prompt_text`, `model_used`, `tokens_used`, `cost`, `user_rating`, `user_feedback`,
   `was_accepted`, `report_id`, `organization_id NOT NULL` — **zero code references**. It is an
   overlap risk (R-10) and a partial precedent for AI cost/rating storage.

8. **PE has no report surface:** `backend/api/v3_pe.py` (662 lines, 21 routes) contains **zero
   `report` references**; messaging already denies PE absolutely. Recommendation: **no PE Ask**.

9. **`audit_package()` already exists** and is contractually *"NOT an assurance opinion"*
   (`not_assurance: True`, `AUDIT_NOT_ASSURANCE_NOTICE`) with an integrity hash block.
   Recommendation: conversation content should **not** be added to it (PO decision 21.8).

10. **Concrete EXTEND gap:** `LLMClient.complete()` returns only `str` — **no usage/token/cost
    data** — so `tokens_used`/`cost` cannot be populated and token-based allowances cannot be
    enforced until the client is extended.

11. **Reusable authorization pattern identified:** `_authorize_org_actor()` in
    `backend/api/v3_messaging.py` resolves exactly one of `org_member` / `consultant` (ACTIVE grant)
    / `staff` (internal only, `can_manage_staff`), denying PE and general staff outright. This is the
    recommended shape for the Ask access resolver.

12. **Commercial/usage infrastructure is configurable, not hard-coded:**
    `billing_commercial_config` is a **versioned key/value** rule set
    (`UNIQUE(config_key, version)`, current = `effective_to IS NULL`, deny-by-default RLS), and
    `usage_tracking` already has counter columns (`ai_files_processed`, `reports_generated`, …).
    An AI allowance is therefore a **config value**, not a new billing architecture.

## Deliverables

* `docs/architecture/CARBONTALLY_PHASE8_ASK_CARBONTALLY_PERSISTENT_CONVERSATION_AND_AI_AUDITABILITY_DISCOVERY_20260912.md`
  — primary discovery document (§1–§25 plus the mandatory `A`–`J` final summary).
* `docs/cline/prompt-history/CT-P8-ASK-CARBONTALLY-PERSISTENCE-DISCOVERY-20260912-013.md` — this
  file.

## Classification Summary (structures + 1 design-baseline finding)

| Classification | Count | Highlights |
|---|---|---|
| REUSE | 9 | `LLMClient`, `ai_runtime` attribution, AI boundary rules, public assistant, identity, guards, `audit_trail`, `audit_package()`, `billing_commercial_config` |
| EXTEND | 6 | `LLMClient` (multi-turn + usage), audit taxonomy (option A), `usage_tracking`, `ai_content_history`, knowledge allowlist, RLS coverage |
| NEW BUILD | 6 | `ask_conversations`, `ask_messages`, `ask_interactions`, tool registry, Ask RLS policies, Ask API/UI + `result_hash` |
| REFACTOR | 0–1 | possible shared access resolver (only if behaviour-neutral) |
| DEFER | 6 | credits/plans, scoped retrieval, PE Ask, auditor Ask, summary/compaction, taxonomy option B |
| DO NOT REUSE | 2 groups | `conversations`/`messages`/`conversation_participants`/`typing_status`; `message_activity_log`/`conversation_activity_log`/`activity_logs` |
| PO DECISION REQUIRED | 17 | see §21.1–21.17 |

## Recommended Staging (no stage authorised by this task)

`D1` discovery (this task, complete) → `D2` PO ratification → `I1` persistent conversation
foundation (**tables + RLS in the same migration**) → `I2` authorization hardening/visibility →
`I3` controlled read-only tools (deterministic path, works with no provider) → `I4` interaction
record + audit integration → `I5` bounded context → `I6` UI → `I7` privacy/retention/export →
`I8` billing/allowance + production hardening. Deferred: consultant/staff/PE Ask, auditor
capability, summary/compaction, scoped retrieval.

## Verification Performed

| Check | Result |
|---|---|
| Both deliverables exist | ✔ |
| Existing AI structures traced | ✔ (`llm_client`, `ai_runtime`, `ai_document_extraction`, public assistant, `ai_content_history`) |
| Existing messaging structures traced | ✔ (schema, Phase 5 entity extension, API authorization, repository, domain, UI) |
| Existing audit structures traced | ✔ (`audit_trail`, immutability trigger, indexes, taxonomy, repository, API, `audit_package`) |
| Existing authorization structures traced | ✔ (five domains + all named guards) |
| Application implementation performed | ✖ none |
| Database changes made | ✖ none |
| Migrations created | ✖ none |
| RLS changes made | ✖ none |
| Frontend changes made | ✖ none |
| Production access used | ✖ none |
| Provider/API keys introduced | ✖ none |
| Unrelated dirty/untracked work modified or removed | ✖ none (208/52 preserved) |

## Files Changed

| File | Change |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_ASK_CARBONTALLY_PERSISTENT_CONVERSATION_AND_AI_AUDITABILITY_DISCOVERY_20260912.md` | **created** |
| `docs/cline/prompt-history/CT-P8-ASK-CARBONTALLY-PERSISTENCE-DISCOVERY-20260912-013.md` | **created** |

No other file was created, modified, or deleted.

## Relationship to S1

**S1 is unchanged and was not expanded.** S1 remains: repository-level `is_current` fix,
`current_version` in the report listing, stale `download_report` docstring correction, regression
test. This discovery adds no work to S1 and does not implement it. The only interaction is a
dependency note: Ask tools citing reports must select versions explicitly rather than relying on
`is_current` until S1 lands (risk R-2).

## Explicitly Not Done

No implementation · no implementation authorisation · no S1 expansion · no second LLM/provider
abstraction · no unrestricted RAG/vector/DB access · no PE Ask or report access · no auditor
capability · no messaging change · no billing change · no audit-ledger or taxonomy change · no
`audit_package()` change · no legal-compliance claim · no invented retention/allowance/provider
policy · no public-assistant change · no roadmap or frozen-decision change. **Not pushed.**

## Final Status

**`DISCOVERY COMPLETE — READY FOR PO REVIEW`**

Required before implementation: PO ratification of the design · PO acknowledgement of R-1 · answers
to decisions 21.1, 21.2, 21.6, 21.16 (I1/I2 blockers) · closure of R-3/R-4 (live RLS posture and
effective backend DB role — `[UNVERIFIED]`, require live inspection) · provider and legal position
(21.13, 21.14) · retention design (21.3) before customer rollout.
