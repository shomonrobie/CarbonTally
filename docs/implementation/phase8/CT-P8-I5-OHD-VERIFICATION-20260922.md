# CT-P8-I5-OHD-VERIFICATION-20260922

**Independent verification of CarbonTally Insight I5 — Context.**

| Item | Value |
| --- | --- |
| **Final OHD verdict** | **`I5 VERIFIED PASS`** |
| Verified revision | `4d23031c0875891873d44be422d5dd293680679b` (`4d23031`) |
| Implementation commit | `f9d91e1` (ancestor of the verified revision — confirmed) |
| Verifier | OHD — independent, read-only |
| Date | 2026-09-22 |
| Blockers | **none** |
| Nonblocking observations | O-1…O-6 (§19), including one PO clarification request (O-1) |

> **Verification only.** No implementation, test, schema, migration, configuration, RLS, API, frontend or I1–I4 artefact was modified. No defect was fixed. No mutation was committed. The only repository change is this report. Test-sensitivity mutations were applied by *runtime* monkeypatching from `/tmp` (pytest plugin), never by editing the repository.

Legend used throughout: **[FACT]** independently reproduced by this verifier · **[OBS]** observation · **[BLOCKER]** blocking defect.

---

## 1. Verification authority

Issued by the OHD authorization of 2026-09-22 as **independent verification only — no remediation authorized**. Cline's report `I5 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION` is treated as a **claim**, never as evidence. Every statement below was obtained by running the real code; Cline's assertions were neither repeated nor relied upon. Where Cline's evidence and mine agree, that is recorded as independent corroboration.

## 2. Repository / commit verified

| Check | Result |
| --- | --- |
| Checkout | `/home/shomonrobie/ct_93d5cdd` (**the only checkout used**) |
| Branch | `p8-release-reconciled` (never switched) |
| Reported HEAD resolved | `4d23031c0875891873d44be422d5dd293680679b` — **[FACT]** `git rev-parse 4d23031c0875891873d44be422d5dd293680679` resolves uniquely to `…679b`. *Note:* the authorization text quoted the SHA one character short (39 hex digits); the repository commit is `…679b`. No repository discrepancy. |
| Actual HEAD | `4d23031c0875891873d44be422d5dd293680679b` — equals the reported revision ✅ |
| Implementation ancestor | `f9d91e1` = `f9d91e14a335eb09db7be5afe7abd630738345e3`, `git merge-base --is-ancestor f9d91e1 HEAD` → **YES** ✅ |
| Report-correction commit | `4d23031` — docs only (`CT-P8-I5-INSIGHT-CONTEXT-20260921.md`, 4 insertions / 3 deletions, test-evidence counts) ✅ |
| Remote | `github/p8-release-reconciled` = `4d23031…679b`; alignment `0 0` ✅ |
| Working tree | clean, `--untracked-files=all` empty; no stash ✅ |
| Tree after verification | **0 changes** (verifier left nothing behind) ✅ |

`origin` points at a stale local path and was not used; `github` is the remote of record.

## 3. PO source document

`docs/architecture/CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` (943 lines, commit `43f572d`). Independently read: §3.1–3.7 (global decisions), §4 I5-1…I5-9 (each `DECISION — CLOSED`), the **I5 authorization boundary**, and §15 (`Next implementation authorization: I5 — Context … separately issued to Cline with the exact bounded decisions recorded in this document`). **I5 is authorized**, and the authorization is bounded to those decisions. The Master Specification v1.1 was consulted for the I5 contract and sets no numeric budget of its own.

## 4. Scope verified

Verified against the ratified decisions: current-conversation context only; deterministic bounded selection; chronological ordering with most-recent preference; configurable **20,000-character** maximum assembled historical context enforced **before provider submission**; current question preserved and not counted against the history budget; deterministic truncation; no AI summarisation/compaction; no persisted summaries, summary table or summary column; no cross-conversation memory; no semantic/vector relevance engine, RAG, embeddings, vector search or LangChain; stale references never authoritative; current authorized lookup wins; bounded structured interaction/tool-result projections only; no unrestricted tool payload replay; `public.audit_trail` is not conversational context; empty context valid and never `zero`; existing I2 authorization is the sole boundary; deterministic CarbonTally data authoritative; no new I3 tool; no new permission; no I1–I4 contract redesign. Each is dispositioned in §§9–16.

## 5. Files inspected

Implementation: `backend/services/insight_context.py` (370 lines, read in full), `backend/services/insight_interactions.py` (I5 diff + the surrounding narration path and answer-state resolution), `infra/llm_client.py` (to drive a real provider endpoint), `api/v3_insight_interactions.py`, `api/insight_authz.py`, `api/dependencies.py`, `data/insight.py`, `data/insight_interactions.py`, `data/base.py` (`loads_jsonb`). Tests: `tests/unit/services/test_insight_i5_context.py` (406 lines), `tests/unit/api/test_v3_insight_i5_context_integration.py` (327 lines). Documents: `docs/implementation/phase8/CT-P8-I5-INSIGHT-CONTEXT-20260921.md`, the PO decision record, the Master Specification. Schema: live `carbontally_insight_conversations/_messages/_interactions/_tool_calls`, `audit_trail`, `organization_members` on a disposable database.

## 6. Execution paths traced

```text
POST /api/v3/insight/interactions
  -> require_insight_user -> authorize_insight_scope            [I2, unchanged]
  -> I1 message write, I4 interaction write, I3 tool call       [unchanged]
  -> narration branch (reached only when narration != none AND a provider attempt is possible)
       services.insight_context.assemble_context(...)           [NEW I5]
         -> i2.authorize_insight_scope (re-authorization)
         -> repos.insight.get_conversation + conversation_is_visible   (absent/foreign -> 404)
         -> repos.insight_interactions.list_interactions(
                organization_id, created_by=access.user_id, conversation_id, limit=50)
         -> repos.insight_interactions.list_tool_calls(per interaction, org-scoped)
         -> allowlisted projection + MAX_BLOCK_CHARS(2000) + budget -> InsightContext
       context_prompt_sections(context) -> prompt string
       -> LLMClient.complete(prompt)  ->  real HTTP POST /chat/completions
```

Traced with a **real HTTP provider stub** (an actual local chat-completions endpoint that records the payload it receives), the real application factory, real repository bundle, real PostgreSQL, real asyncpg and real I2/I3/I4 services. Only two things were test-side: `get_current_user` (project convention) and the external provider endpoint (the boundary under inspection).

**AST check — the context reaches nothing but the prompt [FACT]:** in `insight_interactions.py` the assembled objects are referenced only at line 429 (`context = await assemble_context(...)`), 438 (`sections = context_prompt_sections(context)`) and 444–445 (both interpolated into the prompt string). No answer state, evidence row, audit record, API field or visibility decision is derived from historical context.

**Invocation gating [FACT]** (runtime spy on the service's `assemble_context`):

| narration | HTTP | narration_state | `assemble_context` calls | provider calls |
| --- | --- | --- | --- | --- |
| `none` | 201 | `skipped` | **0** | **0** |
| `required` | 201 | `completed` | 1 | 1 |
| `optional` | 201 | `completed` | 1 | 1 |

The default I4 path therefore performs **no** I5 work and no extra database reads.

## 7. Tests executed

Method: shipped suites run as-is; plus verifier-authored probes (`/tmp/i5_e2e_prompt.py`, `/tmp/i5_budget.py`, `/tmp/i5_assembler.py`, `/tmp/i5_gating.py`) against a real disposable PostgreSQL 17.6 database (`ct_i4_reverify_20260921`, I4 schema applied) with the real HTTP capture stub; plus an 11-mutation sensitivity harness applied at runtime.

## 8. Exact test results

| Run | Command scope | Result |
| --- | --- | --- |
| I5 suites (new) | `tests/unit/services/test_insight_i5_context.py` (18) + `tests/unit/api/test_v3_insight_i5_context_integration.py` (6) | **24 passed, 0 failed, exit 0** [FACT] |
| Focused I5 + I1/I2/I3/I4 Insight regression (13 files) | I5 suites + I1/I2/I3/I4 migration, authorization, tools, wiring, repository suites + live-RLS module | **156 passed, 0 failed, 5 skipped, exit 0** [FACT] |
| Full unit suite | `tests/unit` | **4 failed, 2940 passed, 8 skipped** (317s) [FACT] |
| Integration (environment-dependent) | `tests/integration/test_workflow.py`, `test_v3m3_customer_factors.py` | **3 failed** — `.git`-identical to the pre-I5 I4-round failures; **neither file contains the string `insight`** [FACT] |
| Verifier E2E prompt capture | real HTTP + real DB | 27/37 initially → all 10 failures traced to **my own probe defects** (extractor + a reused idempotency key); after correction the substantive checks pass (§9) [FACT] |
| Verifier budget probe | real HTTP + real DB | **14/14 passed** [FACT] |
| Verifier assembler probe | real assembler + real DB | **25/26 passed**; the single failure was a reused conversation in my probe, re-run on a fresh conversation → pass [FACT] |
| Verifier gating probe | real HTTP + real DB | **2/2 passed** [FACT] |
| Sensitivity | 11 runtime mutations | **9 caught, 2 not applicable** (§20 of the mandate → §16 below) [FACT] |

The four full-suite failures are the **known pre-existing** ones — 3 × `tests/unit/api/test_review_sla_surfaces.py` (lazy included-router; `_paths()` only reports `/api/v2/health`) and `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`. 2909 → 2916 → **2940** passed corresponds exactly to the +7 I4-verification tests and the +24 I5 tests; **no new failure appeared**. Cline's corrected report states `2940 passed / 4 failed / 8 skipped` — independently identical to my run [FACT].

## 9. Authorization / security findings

**[FACT] I2 remains the sole boundary; the assembler re-authorizes.** `assemble_context` calls `api.insight_authz.authorize_insight_scope` first, then resolves the conversation and requires `conversation_is_visible`, reporting absent *and* foreign conversations alike as **404** (no existence disclosure).

| Caller | Result at the assembler | Result on the HTTP path | Provider calls |
| --- | --- | --- | --- |
| authorized creator | allowed | 201 | 1 |
| peer in the same organisation (not creator) | HTTP 404 | HTTP 404 | **0** |
| cross-organisation caller | HTTP 404 | HTTP 403 | **0** |
| inactive organisation | HTTP 403 | HTTP 403 | **0** |
| non-member | HTTP 403 | — | — |
| absent conversation id | HTTP 404 | HTTP 404 | **0** |

Unauthorized callers never reach the provider and never cause context assembly — refusals short-circuit before it.

**[FACT] Creator-private and current-conversation scoping are enforced by the reads, verified against real data.** With a real conversation containing foreign-conversation rows and peer-created rows, the assembled context contained **no** interaction from another conversation and **no** peer-created interaction; the parameters the assembler passes (`created_by=access.user_id`, `conversation_id`) were confirmed at runtime and asserted by the shipped tests.

**[FACT] Reference locators are not authorization.** Historical references are carried as `{kind, id}` only; a reference never triggers a load and never widens access — a stale or foreign reference simply appears as an opaque locator in the non-authoritative section.

## 10. Context-budget findings

**[FACT] Default is exactly 20,000** (`DEFAULT_MAX_HISTORY_CHARS = 20_000`) with `CONTEXT_POLICY_VERSION = "i5-context-v1"`.

**[FACT] The bound is enforced on what is actually submitted to the provider.** Measured on the real prompt body POSTed to the capture endpoint (`CARBONTALLY_INSIGHT_CONTEXT_MAX_CHARS` set per run):

| Configured bound | History characters actually submitted | ≤ bound? |
| --- | --- | --- |
| unset (default) | 14,359 | ✅ ≤ 20,000 |
| 1 | **1** | ✅ |
| 2 | **2** | ✅ |
| 50 | **50** | ✅ |
| 200 | **200** | ✅ |
| 19,999 / 20,000 / 20,001 / 25,000 | 14,361 | ✅ (all material fits) |
| **100,000** | **86,161** | ✅ ≤ 100,000 — **but > the ratified 20,000** (see O-1) |

**[FACT] Boundary conditions.** Empty (0 chars, `empty=True`); small (1–200 exactly at the bound); below/at/above the default all respected; substantially above the default respected *relative to the configured bound*. A single oversized block cannot bypass the limit: the newest block is either dropped or truncated to the remaining budget, and direct assembler calls at `max_chars` 1/5/100/1999/2000/2001 returned exactly `min(available, bound)` in every case (`truncated=True`).

**[FACT] Deterministic truncation.** Two independent assemblies with identical inputs produced **byte-identical** `history_text` (15,447 chars) — `json.dumps(..., sort_keys=True)`, no clock, no randomness, newest-first budget consumption, chronological emission, version stamp.

**[FACT] Invalid configuration fails safe.** `0`, `-5`, `abc`, blank → warning and fall back to the ratified 20,000 (bound never removed). `max_chars=0` passed directly to the assembler raises **HTTP 422**.

**[FACT] The current question is not counted against the history budget** — with the bound set to **1** character the question still appears verbatim in the submitted prompt, and the authoritative evidence section is never budgeted by I5.

## 11. Historical-context findings

**[FACT] Only bounded structured material is submitted.** The emitted block carries `interaction_id`, `created_at`, `lifecycle`, `answer_status`, `narration_state`, `intent`, an allowlisted tool projection (`tool`, `status`, `reason`, `contract_version`, `result_item_count`, `truncated`, `duration_ms`, `reference_kinds`), `reference_kinds`/`{kind,id}` locators and `evidence_class`. No `arguments`, no result payload, no URLs.

**[FACT] Sentinel test — nothing disallowed reached the provider.** Sentinels were planted in disallowed places on real rows and in a real audit record; the submitted prompt was searched in full:

| Sentinel planted in | Reached the prompt? |
| --- | --- |
| tool `arguments` jsonb | **no** |
| tool `result_metadata` payload / URL | **no** |
| `references` extra keys / URL | **no** |
| raw I1 message `content` | **no** |
| `audit_trail` `metadata` / `changes` | **no** |
| an interaction in a *different* conversation | **no** |
| a *peer* actor's interaction in the same conversation | **no** |
| authorized reference locator (`{kind,id}`) | yes (authorized structured material) |

**[FACT] History is explicitly non-authoritative.** Every block carries `evidence_class = "historical_context_not_authoritative"`; `context_prompt_sections` returns `historical_context_is_authoritative = "false"`; the prompt states *"Prior conversation context (history only; NOT authoritative — the structured evidence above always wins where they differ)"* and places the authoritative evidence **first** (evidence at offset 0, history at 2,059+, measured on the real prompt).

**[FACT] Historical context cannot override the current authoritative result.** Because nothing but the prompt consumes it (§6 AST check), the persisted answer state, evidence rows, audit correlation and API response are derived solely from the current authorized lookup. In a live interaction where history contained a prior `report_lookup` with `success`, the current result remained the determining state (the history block was purely additive prompt text).

**[FACT] Ordering and selection.** Emitted blocks are in chronological ascending order; the blocks selected are the **most recent** ones of the conversation; the in-flight interaction is excluded from its own context (`exclude_interaction_id`). Cross-conversation and peer material absent (above).

## 12. I4 integration finding

**[FACT] The I5 assembler is invoked by the existing I4 narration path, inside the branch that already attempts a provider call** (lines ~421–445). The integration is **25 changed lines, 2 hunks, exactly 1 removed line** (replaced `f"Question: {text[:500]}\n"` → the `sections` equivalent, preserving the pre-existing 500-character truncation).

| Question required by the mandate | Finding |
| --- | --- |
| Is the assembler invoked by the existing I4 narration path? | **Yes** — one call, immediately before prompt assembly, gated on the provider-attempt branch |
| Is this an authorized I5 use of context? | **Yes** — PO §15 authorizes the I5 context stage and the I5 boundary lists no prohibition on consuming it in the existing narration path; it is current-conversation, bounded, deterministic, non-authoritative |
| Did any I4 contract change? | **No** — no change to the route, service signature, domain model, data layer, schema, migrations or I1/I2/I3; `backend/api/`, `backend/domain/`, `backend/data/`, `backend/infra/`, `supabase/`, `prisma/` all have **0** changed files |
| Did answer-state behaviour change? | **No** — answer states are computed from the current tool result; with `narration=none` the I5 code does not even run (0 calls, §6) |
| Did evidence/reference persistence change? | **No** — the evidence write path is untouched; history is read-only (0 write operations in the module) |
| Did audit correlation change? | **No** — `audit_trail` is neither read nor written by I5; live interaction still produced the correlated `insight.interaction.completed` record |
| Did creator-private visibility change? | **No** — the assembler narrows further (`created_by`), it does not widen; refusals unchanged |
| Did API behaviour change? | **No** — same route, same 201/403/404/422 behaviour independently reproduced |
| Did provider semantics change beyond authorized non-authoritative context? | **Only** the added labelled history section and the preserved question; the authoritative evidence section and the system instruction are unchanged. The prompt grew from the I4 evidence payload (17,737 chars total in the probe, of which the history section was 15,448) |

No scope violation found in the integration.

## 13. I1 message-text limitation finding

**[FACT] What historical material is actually available to I5:** structured interaction rows of the current conversation — `interaction_id`, `created_at`, `lifecycle`, `answer_status`, `narration_state`, `intent`, allowlisted tool-call projections and reference locators. **Raw conversation/message text is not included**: `services/insight_context.py` performs no message read (`list_messages` count = 0), and a sentinel planted in a real `carbontally_insight_messages.content` row did **not** appear in the submitted prompt.

**[FACT] Implementing message text would not require an I1 change** — `data/insight.py:251` already exposes `async def list_messages(...)`, so this is an implementation choice rather than an I1 capability gap.

**[FACT] Effect on I5 compliance.** The PO decisions do not require message text: I5-6 authorizes "**bounded structured historical interaction/tool-result context**", I5-1 requires current-conversation scope, chronological coherence and bounded most-recent selection, and I5-2 forbids generated summaries. The shipped implementation satisfies those literal requirements, and its metadata-only projection is *more* injection-resistant than transcript replay.

**Disposition:** this is a **limitation, not a contract failure** — but it is a material limitation for the PO to weigh: the model cannot see what was previously asked or answered, only that prior interactions occurred, what intent/status they had and which locators they touched. Consequently the practical value of I5 v1 is context *shape*, not conversational continuity. Recorded as O-4, and as a factual input for a future PO decision on transcript inclusion.

## 14. Persistence / summarisation findings

**[FACT] No persistence of any kind.** The module contains **0** write operations (`INSERT`/`UPDATE`/`DELETE`/`execute`/`commit` = 0); it only reads and returns an in-memory structure.

**[FACT] No summarisation or compaction.** "summaris"/"summar" appears **3 times in the file, all in the module docstring** as prohibitions ("no summarisation"); **0** in executable code. No second generation path exists: the only provider call is the pre-existing `LLMClient.complete` for narration.

**[FACT] No schema change.** `supabase/` and `prisma/` changed files = **0**; migrations added = **0**. No summary table, no summary column, no context store, no retention change. (Independently consistent with PO I5-4.)

## 15. Prohibited-technology findings

| Prohibited | Whole-file | Executable code | Verdict |
| --- | --- | --- | --- |
| embeddings | 1 | **0** | docstring prohibition only |
| vector search / pgvector | 1 | **0** | docstring prohibition only |
| RAG | 2 | **0** (`rag` in code = the substring inside `# pragma: no cover`) | docstring prohibition only |
| LangChain | 0 | **0** | absent |
| token-counting (`tiktoken`, `token_count`) | 0 | **0** | absent; the budget is character-based as ratified |
| summarisation/compaction | 3 | **0** | docstring prohibition only |

**[FACT] No new I3 tool, permission or authorization role:** `backend/api/`, `backend/domain/`, `backend/data/`, `backend/infra/` changed files = **0**; no frontend, billing, retention, export, entitlement, payment or production-configuration content in the I5 module (`0` mentions each); `public.ai_content_history` untouched (Q1 Option C preserved); I5–I8 remain as before, with **only** I5 implemented.

## 16. Regression findings

* **[FACT]** Full unit suite **4 failed / 2940 passed / 8 skipped** — the same four known pre-existing failures, no new failure; the pass count rises by exactly the 24 new I5 tests (2916 → 2940).
* **[FACT]** Focused I5 + I1/I2/I3/I4 Insight regression: **156 passed / 0 failed / 5 skipped, exit 0** (the 5 skips are the live-RLS module that requires an external DSN). This independently reproduces Cline's reported `156 passed / 0 failed`.
* **[FACT]** `tests/integration` failures are reproduced and are **unrelated to I5**: `test_workflow.py` (2) and `test_v3m3_customer_factors.py` (1) fail identically to the pre-I5 I4 round, and **neither file references Insight at all** (0 occurrences of `insight`). They are environment/schema-drift failures that do not obstruct I5 verification, which I completed through my own live-DB probes.
* **[FACT]** No existing test was weakened, skipped or deleted: `git diff --name-status 43f572d 4d23031 -- backend/tests/` shows **only additions**.

**[FACT] Test sensitivity (11 runtime mutations; repository never modified).**

| Mutation | Detected? | Detected by |
| --- | --- | --- |
| M1 default budget raised to 1e9 | ✅ | `test_the_ratified_default_budget_is_twenty_thousand_characters` |
| M2 configuration override unbounded | ✅ | default-budget + configuration-fails-safe tests (3 failures) |
| M3 `arguments` added to the projection allowlist | ✅ | `test_only_bounded_structured_tool_projections_are_used` |
| M4 conversation visibility check disabled | ✅ | `test_cross_scope_context_cannot_be_loaded` |
| M5 cross-conversation restriction removed | ⚠️ not applicable | the unit suite substitutes a **fake** repository, so patching the real repository class is not exercised |
| M6 creator-private scoping removed | ⚠️ not applicable | as M5 |
| M7 budget ignored entirely | ✅ | 5 failures, incl. `test_assembled_history_never_exceeds_the_configured_budget` |
| M8 audit data injected into history | ✅ | `test_empty_context_is_valid_and_not_an_error` |
| M9 current question dropped | ✅ | `test_current_question_is_preserved_verbatim` |
| M10 empty context fabricated as `zero` | ✅ | service + HTTP integration tests (2 failures) |
| M11 history marked authoritative | ✅ | `test_current_question_is_preserved_verbatim` |

Nine of eleven mutations are caught by the shipped tests, including bypassing the 20,000-character limit, admitting a forbidden field, disabling the authorization check, ignoring the budget and injecting audit data. M5/M6 are recorded as **not applicable** rather than as gaps: the unit tests assert the *call boundary* (the `created_by`/`conversation_id` arguments the assembler passes), while enforcement inside the real repository was verified by this verifier directly against real PostgreSQL data (§9) — the shipped suite would not, on its own, catch removal of that enforcement.

## 17. Scope audit

`git diff --stat 43f572d 4d23031` — **5 files, 1,238 insertions, 1 deletion**:

| File | Kind |
| --- | --- |
| `backend/services/insight_context.py` | new (370 lines) |
| `backend/services/insight_interactions.py` | modified (+25/−1, narration branch only) |
| `backend/tests/unit/services/test_insight_i5_context.py` | new (406 lines) |
| `backend/tests/unit/api/test_v3_insight_i5_context_integration.py` | new (327 lines) |
| `docs/implementation/phase8/CT-P8-I5-INSIGHT-CONTEXT-20260921.md` | new report (+`4d23031` correction) |

**[FACT] Unauthorized work: none found.** No I6 UI, no I7 retention/deletion/export, no I8 billing/credits/entitlements/payment providers, no frontend, no privacy-policy change, no production configuration, no new authorization role, no new tool, no schema/RLS migration. Every protected directory (`backend/api/`, `backend/domain/`, `backend/data/`, `backend/infra/`, `backend/core/`, `backend/engines/`, `supabase/`, `prisma/`, `docs/architecture/`) has **0** changed files; the Master Specification is unchanged, so this report cannot be read as a PO closure.

## 18. Blockers

**None.** No material PO requirement was found unsatisfied, no authorization weakening, no prohibited technology, no persistence/summarisation, no contract change, no scope violation, and no new regression.

## 19. Nonblocking observations

**[OBS] O-1 — budget ceiling: configuration can exceed the ratified 20,000 characters. *(PO clarification requested.)***
VERIFIED FACT: the default is exactly 20,000 and the bound is always enforced on submission; a misconfiguration can never remove the bound. VERIFIED FACT: `CARBONTALLY_INSIGHT_CONTEXT_MAX_CHARS` accepts **any positive integer with no upper clamp**, and with it set to `100000` the assembler submitted **86,161** characters of historical context (measured on the real prompt). The same is reachable through the public `max_chars` argument of `assemble_context`.
The PO wrote "**Initial maximum: 20,000 characters of assembled historical context**" *and* "never exceed the **configured** bound" *and* "keep the budget **configurable**". Under the literal reading the implementation complies; under a reading of "20,000" as an absolute ceiling for I5 v1 the override breaches it. This verifier does not reinterpret the PO text in either direction. No default, deployment or in-repo caller sets an override above 20,000 (the only occurrences are two tests setting 500 and 20,000). **Requested PO decision:** confirm whether 20,000 is a hard ceiling (then an upper clamp is required — a change needing separate authorization) or an initial default (then no action).

**[OBS] O-2 — the shipped unit tests verify the repository call boundary, not live scoping (sensitivity M5/M6).** The I5 unit suite substitutes a fake repository and asserts the arguments passed (`conversation_id`, `created_by`); it would not detect removal of the enforcement inside the real repository. Live enforcement *is* correct today — this verifier confirmed it against real data (no foreign-conversation or peer interaction entered context). Consider a live `list_interactions` scoping test alongside the I4 live-suite pattern in a future authorized change.

**[OBS] O-3 — Cline's report counts are declared as derived and match independent measurement.** Commit `4d23031` replaces the counts with values derived from runner progress markers and discloses that the shell did not capture pytest's final line. My independent run reproduced `2940 passed / 4 failed / 8 skipped` exactly. No fabrication; transparency is adequate.

**[OBS] O-4 — no raw message text in I5 v1 (§13).** Factual, PO-visible limitation: context is structured metadata only, so the provider cannot see prior questions or narrations. Not a contract failure under I5-6, and implementing it would not require an I1 change (`list_messages` already exists) — a PO decision, not a defect.

**[OBS] O-5 — the 500-character question truncation in the prompt is pre-existing I4 behaviour, unchanged by I5.** The I5 assembler preserves the current question verbatim (`InsightContext.question`); the I4 prompt has always truncated at 500 characters and still does (`sections['current_question'][:500]`). Unchanged behaviour, noted only for completeness.

**[OBS] O-6 — verifier-probe transparency.** My first E2E pass reported 10 failures that were **my own probe defects**, not product defects: an incorrect prompt-section extractor, and an idempotency key reused across probes (keys are unique per organisation, so later requests replayed and skipped the provider, leaving nothing captured). Both were diagnosed and corrected; all substantive checks pass on re-run. A reused conversation also caused one "empty context" assertion to fail until a genuinely fresh conversation was used. No implementation behaviour was implicated in any of these.

## 20. Final verdict

```
I5 VERIFIED PASS
```

Independently established, on the verified revision `4d23031` (implementation `f9d91e1`), through the real route, real repository, real PostgreSQL/asyncpg, real I2/I3/I4 services and a real HTTP provider endpoint:

* **Current-conversation, deterministic, bounded context** — most-recent material selected within the budget, emitted chronologically, byte-identical across repeated assemblies, in-flight interaction excluded, no foreign-conversation or peer material;
* **the ratified 20,000-character maximum by default, enforced before provider submission**, measured on the prompt actually POSTed (≤ bound in every boundary case from 1 to 20,000, and the current question preserved even at a bound of 1);
* **only bounded structured material submitted** — sentinels in arguments, payloads, URLs, raw message text, audit records, foreign conversations and peer rows all stayed out of the prompt, while authorized `{kind,id}` locators were included;
* **history explicitly non-authoritative and structurally incapable of overriding the current authoritative result** — it reaches the prompt and nothing else;
* **I2 remains the sole authorization boundary** — creator allowed; peer, cross-organisation, inactive-organisation, non-member and absent-conversation callers refused with **zero** provider calls;
* **empty context valid and never `zero`**; **no persistence, no summarisation, no cross-conversation memory, no RAG/embeddings/vector/LangChain/token-counting**; **no new tool, permission or role**; **no I1–I4 contract change**;
* **no regressions** — full unit suite `4 failed / 2940 passed / 8 skipped` with the same four known pre-existing failures and the +24 new tests passing; focused Insight regression `156 passed / 0 failed / 5 skipped`; the integration failures reproduced and shown to be unrelated to Insight; nine of eleven sensitivity mutations caught by the shipped tests.

No blocker was found. The single PO-decision item that I must not decide myself is O-1 (whether 20,000 characters is an absolute ceiling or an initial default for a configurable budget).

**This report does not declare PO closure, does not modify the Master Specification, and does not authorize I6, I7 or I8. No remediation is authorized or performed.**

**I5 VERIFIED PASS — READY FOR PO CLOSURE**
