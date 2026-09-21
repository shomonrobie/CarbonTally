# CT-P8-I5-INSIGHT-CONTEXT-20260921

**Stage:** I5 — Context (CarbonTally Insight). **Status: IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION** (not verified, not closed).

**Authorization:** PO I5 Context Implementation Authorization (2026-09-21), issued against the durable PO decision record `docs/architecture/CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` (I5-1…I5-9 and the I5 authorization boundary).

---

## 1. Scope implemented (IMPLEMENTED)

Deterministic, bounded **current-conversation** context assembly; chronological ordering with most-recent preference inside the budget; the ratified **20,000-character** maximum assembled historical context, **configurable** and enforced **before provider submission**; the current question preserved verbatim and never counted against the historical budget; deterministic truncation including an explicit newest-block overflow rule; history explicitly labelled **non-authoritative** so it can never override a current authorized lookup; historical references carried as **locators only**; only **bounded structured projections** of historical interactions/tool calls (allowlisted fields only — no arguments, no result payloads, no URLs); empty context treated as a normal condition (never zero); every protected read resolved through the **existing I2 boundary**; regression coverage for all sixteen PO-required I5 behaviours.

## 2. NOT IMPLEMENTED / OUT OF SCOPE (explicit)

No AI summarisation or compaction; no persisted summaries (no table, no column, no retention change); no cross-conversation memory; no semantic/vector relevance engine; no RAG, embeddings, vector search or LangChain; no token-counting library; no new I3 tool; no new persona, permission or authorization rule; no I6 UI; no I7 retention/deletion/export; no I8 billing/credits/entitlements/payment work; no production deployment; no database migration of any kind (none was required); no change to `public.ai_content_history` (Q1 Option C continues).

## 3. Files changed

| File | Change |
| --- | --- |
| `backend/services/insight_context.py` | **New** — I5 assembler: `assemble_context`, `context_prompt_sections`, `configured_max_history_chars`, `InsightContext`, `ContextBlock`, `DEFAULT_MAX_HISTORY_CHARS = 20000`, `CONTEXT_POLICY_VERSION = i5-context-v1` |
| `backend/services/insight_interactions.py` | **Integrated** — the narration branch assembles the bounded context (via `configured_max_history_chars()`) **before** the provider call and includes it in the prompt labelled non-authoritative. No I4 contract changed: same API surface, answer states, evidence rows, audit correlation and creator-private visibility |
| `backend/tests/unit/services/test_insight_i5_context.py` | **New** — 18 assembler tests |
| `backend/tests/unit/api/test_v3_insight_i5_context_integration.py` | **New** — 6 HTTP/integration tests |
| `docs/implementation/phase8/CT-P8-I5-INSIGHT-CONTEXT-20260921.md` | This report |

No other file was modified: **no** migration, schema, RLS, I1/I2/I3 code, I4 evidence/API contract, frontend, billing or `public.ai_content_history` change.

## 4. Architecture / code path

```text
POST /api/v3/insight/interactions   (unchanged I4 route)
  -> require_insight_user -> authorize_insight_scope        [I2 boundary, unchanged]
  -> I1 message write + I4 interaction write + I3 tool call [unchanged]
  -> narration branch (only when a provider call is attempted):
       services.insight_context.assemble_context(...)       [NEW I5]
         -> authorize_insight_scope (re-authorization)      [I2]
         -> repos.insight.get_conversation + conversation_is_visible
         -> repos.insight_interactions.list_interactions(creator-private, current conversation, newest-first, bounded)
         -> repos.insight_interactions.list_tool_calls(per interaction)
         -> allowlisted structured projection + character budget -> InsightContext
       context_prompt_sections(context)                     [NEW I5]
       -> LLMClient.complete(prompt)                        [existing provider abstraction]
  -> unchanged answer-state resolution, canonical audit append, forward-only completion
```

## 5. Context-selection algorithm (deterministic)

1. re-authorize the caller and resolve the conversation (foreign or absent => HTTP 404; cross-organisation or inactive => HTTP 403) — no other conversation is ever loaded;
2. read at most `MAX_HISTORY_INTERACTIONS = 50` prior interactions of **that conversation only**, creator-private, **newest first**;
3. for each, read its tool calls (at most `MAX_TOOL_CALLS_PER_INTERACTION = 4`) and build a structured block: `interaction_id`, `created_at`, `lifecycle`, `answer_status`, `narration_state`, `intent`, projected tool calls, reference locators, and `evidence_class = historical_context_not_authoritative`;
4. consume the budget **newest first** (most-recent preference). A block that does not fit is dropped, except that when nothing has been selected yet the newest block is included truncated to the remaining budget, so a small budget still yields the most recent material and the bound is never exceeded;
5. emit the selected blocks in **chronological ascending** order.

Determinism: no clock, no randomness, stable ordering — identical authorized inputs against unchanged data yield an identical `InsightContext` (asserted by test).

## 6. 20,000-character enforcement

`DEFAULT_MAX_HISTORY_CHARS = 20000` (PO I5-3) with optional configuration override `CARBONTALLY_INSIGHT_CONTEXT_MAX_CHARS` (positive integer; invalid or zero values log a warning and fall back to the ratified default, so misconfiguration can never remove the bound). The budget bounds **only the assembled historical context** — the current question is preserved separately — and is enforced in the assembler, therefore **before** `LLMClient.complete` is called, with a defensive clamp guaranteeing `len(history_text) <= max_chars` in every branch. Tests assert the bound at 200 / 1,000 / 5,000 / 20,000 characters and on the HTTP path with a 500-character override.

## 7. Authorization / security behaviour

Unchanged and inherited, never re-implemented: I2 remains the sole boundary; the assembler calls `authorize_insight_scope` and `conversation_is_visible`; cross-organisation and inactive-organisation attempts are refused (403) and another creator's conversation is reported absent (404, existence not disclosed); stored references are locators only and are never resolved or treated as grants; no RLS bypass, no service-layer bypass, no context-level permission system. Regression tests cover cross-org, inactive-org and foreign-creator context loading.

## 8. Historical tool-result projection behaviour

Each historical tool call contributes only allowlisted structured fields (tool, status, reason, contract version, result item count, truncation flag, duration, reference kinds) plus kind/id locators. Arguments, result payloads and URLs are excluded **by omission**; a test seeds a sentinel secret into arguments and result data and asserts it never appears in the assembled context. Historical results are labelled non-authoritative and are never presented as current authoritative evidence — the prompt states that the current structured evidence always wins where they differ.

## 9. Empty-context behaviour

An empty context is normal: `InsightContext.empty is True`, `history_text == ''`, the prompt section renders `(no prior conversation context)` and `historical_context_is_empty: true`. Nothing is fabricated, no new answer state is introduced, and the HTTP tests assert that `success` and `no_data` outcomes are unaffected and never converted to zero.

## 10. Tests added

`tests/unit/services/test_insight_i5_context.py` (18): assembly of the current conversation; unrelated-conversation exclusion and single-conversation scoping of the query; chronological ordering plus repeat-call determinism; recent-material selection under a small budget; budget bounds at four budgets; the ratified 20,000-character default; configurable override including fail-safe behaviour; verbatim question preservation; deterministic truncation; empty-context validity and non-zero behaviour; cross-org, inactive-org and foreign-creator refusal; non-authoritative labelling with locator-only references; bounded projections with a sentinel-secret leak check; audit-not-used-as-context (a bundle whose audit sink raises on any access); no-persistence, no-summarisation and no-cross-conversation-memory (AST docstring-stripped source scan plus read-only call assertions); self-exclusion of an in-flight interaction; invalid-budget refusal.

`tests/unit/api/test_v3_insight_i5_context_integration.py` (6): the prompt carries bounded history labelled non-authoritative alongside the current authoritative evidence; the budget is enforced before provider submission (500 vs 20,000 comparison); empty history is normal and never becomes zero; historical references grant nothing and trigger nothing; **no context is assembled when narration is `none`**; assembly is read-only (exactly one interaction and one tool call written by the unchanged I4 path).

## 11. Tests executed and results

```text
I5 suites (unit + HTTP integration): 24 passed, exit 0
I5 + I1/I2/I3/I4 focused regression (12 suites): see /tmp/I5REG.txt
Unit suite (tests/unit): FAILED tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged
```


No existing test was weakened, skipped or deleted to obtain these results.

## 12. Pre-existing failures

The four long-standing unrelated unit-test failures remain unchanged and are not attributable to I5: three in `tests/unit/api/test_review_sla_surfaces.py` and `test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`.

## 13. Limitations and non-blocking observations

1. **Raw conversation text is not injected.** I5 v1 context is the current conversation's structured interaction history (answer states, tool outcomes, references) — the material PO I5-6 prefers — rather than message or narration text. The PO may authorize text inclusion in a later decision.
2. Message-level history selection would require a message-count read in the I1 repository; that I1 file was deliberately **not** modified (PO section 2), so this is recorded as a limitation rather than worked around.
3. A budget below one block yields a single truncated newest block with `truncated = true`; this is the documented, deterministic overflow behaviour.
4. Context metadata (used characters, truncation, block count) is **not persisted** — persisting it would require a schema migration, which is not authorized. It is observable through the assembler API and the tests.
5. Context assembly happens only when provider narration is attempted, so deterministic-only interactions assemble no context (asserted by test).
6. Independent verification has not been performed; OHD verification is the next governance step.
7. **`tests/integration` is environment-dependent.** It was additionally attempted and requires a live database whose schema matches the current migrations; it produced environmental/schema-drift failures (e.g. `calculation_snapshots.source_line_item_id` absent, `ConsultantsRepository.add_client()` signature drift) unrelated to Insight, and the run was interrupted. The I5-relevant evidence is the unit and HTTP-integration suites above; no integration failure was caused by I5, and none of the I5 code paths requires a database.

## 14. Out-of-scope confirmation

No I6/I7/I8 work was performed; no summary persistence; no cross-conversation memory; no RAG, embeddings, vector search or LangChain; no new tool, persona, permission or authorization rule; no migration; no production access or deployment; `public.ai_content_history` and `public.audit_trail` are untouched.

## 15. Verdict

**I5 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION.** Cline does not claim verification or closure.
