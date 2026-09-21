# CT-P8-I4-INSIGHT-IMPLEMENTATION-20260921

**Stage:** I4 — AI Interaction + Canonical Audit (CarbonTally Insight)
**Authorization:** PO I4 Implementation Authorization (2026-09-21) with the PO Q1–Q14 decision register.
**Starting HEAD:** `4cddd828defadedbbeb1d7144a0bee953306b4b7`
**Repository:** `/home/shomonrobie/ct_93d5cdd`, branch `p8-release-reconciled`, remote `github/p8-release-reconciled`.
**Verdict (§21):** `I4 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION` (Cline does **not** claim independent verification).

**Authority read and reconciled before any modification:** D2 PO Ratification (`CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md`); Master Specification v1.1; I3 closure (`CARBONTALLY_P8_I3_INSIGHT_CLOSURE_20260921.md`); Q1 closure (`CARBONTALLY_P8_I4_Q1_AI_CONTENT_HISTORY_CLOSURE_20260921.md`); the I4 pre-authorization readiness audit; the Q1 disposition-preparation record; the I1/I2 implementation and verification reports; the I3 implementation and its tests; `infra/llm_client.py` + `infra/ai_runtime.py`; `infra/audit_logger.py` + `data/audit.py` + `domain/audit.py`; the I1 migration and its tests. Existing infrastructure was **extended and reused, never replaced**.

---

## 1. PO authority and the decision set applied

| Decision | Implementation consequence in this work |
| --- | --- |
| **Q1** — `ai_content_history` CLOSED (Option C) | Untouched. The new migration contains **no** reference to it as a dependency (its only mention is a prohibition comment); no code path reads, writes, migrates, renames or alters it; its four RLS policies and Prisma model are unchanged |
| **Q2** — canonical audit ledger | `public.audit_trail`, written through the **existing** `infra/audit_logger.AuditLogger` over `data/audit.AuditRepository`. No new ledger table; `audit_logs`/`processing_audit_trail`/`review_audit_trail`/`activity_logs` unused |
| **Q3** — status vocabularies | `domain.insight_tool.ToolStatus` (I3) is **byte-unchanged**; I4 adds a separate fourteen-state `AnswerStatus` in `domain/insight_interaction.py`; tool-call rows store the I3 vocabulary and interaction rows store the I4 vocabulary |
| **Q4** — raw question | Persisted exactly once, as an I1 user message; Layer 2 stores `question_hash` (sha256) + ids only |
| **Q5** — Layer-2 append-only | DB triggers (`ci_interactions_immutable`, `ci_tool_calls_immutable`) + an insert-only repository surface; the only permitted mutation is a forward-only lifecycle completion |
| **Q6** — tool data projections | `project_tool_arguments` / `project_result_metadata` allowlists; only status/reason/bounds/reference kinds + hashes are persisted |
| **Q7** — lifecycle ownership | Layer 2 owns `received → executing → completed|failed`; **I1 schema untouched** |
| **Q8** — creator-private | SELECT/INSERT policies on both new tables require `is_org_member(organization_id) AND created_by = auth.uid()`; no new personas/permissions; no shared visibility |
| **Q9** — correlation | Immutable interaction `id` + child `tool_call_id`s; the audit entry carries `correlation_id = interaction_id` and `changed_fields.tool_call_ids` |
| **Q10** — idempotency/retry | Unique partial index on `(organization_id, idempotency_key)`; unique `(interaction_id, tool_name, arguments_hash)`; bounded provider attempts (`MAX_PROVIDER_ATTEMPTS = 2`); no unbounded loop, no replay of side effects |
| **Q11** — provider unavailable | Optional narration failure → deterministic answer preserved + `narration_state = unavailable`; required narration failure → `provider_unavailable` with the deterministic references preserved; **never** a fabricated narrative |
| **Q12** — retention/deletion/export | Not implemented (deferred to I7); the repository's `delete`/`save` surfaces raise explicitly |
| **Q13** — billing/credits | Not implemented (deferred to I8); no metering, quota or invoice code |
| **Q14** — provider/evaluation/SLO | The existing `LLMClient` + `configured_ai_attribution()` only; truthful attribution (nothing recorded unless a call succeeded); `tokens_used`/`cost` persist as NULL; no evaluation platform, RAG, embeddings or orchestration framework |

---

## 2. Starting HEAD

`4cddd828defadedbbeb1d7144a0bee953306b4b7` (verified before modification: branch `p8-release-reconciled`, no uncommitted changes at that point; `github/p8-release-reconciled` aligned `0 0`).

---

## 3. Implementation scope delivered

1. **Layer-2 persistence** — two additive tables under the canonical namespace: `public.carbontally_insight_interactions` and `public.carbontally_insight_tool_calls` (migration `20261003000000_p8_i4_insight_interactions.sql`), with append-only triggers, creator-private RLS, explicit grants and post-condition guards.
2. **Orchestration** — `services/insight_interactions.py`: authorize → persist question (I1) → classify intent → scope tool from identifiers → execute ratified I3 tool → persist tool-call evidence → bounded optional narration → truthful answer state → canonical audit → single forward-only completion.
3. **API** — `api/v3_insight_interactions.py`: `POST /api/v3/insight/interactions`, `GET /api/v3/insight/interactions`, `GET /api/v3/insight/interactions/{id}` — registered in `api/router.py`.
4. **Wiring** — `insight_interactions` added to the real `RepositoryBundle` **and** to `get_repositories()`; the shared test fakes bundle extended (the I3 D-01 lesson).
5. **Tests** — new migration, orchestration/security and real-wiring suites; the two legacy Insight migration-position assertions updated for the authorized I4 migration.
6. **Documentation** — Master Specification §48.5 decision intake (Q1–Q14 + I4 status) and this report.

---

## 4. Architecture / code trace

```text
POST /api/v3/insight/interactions
  → require_insight_user (authenticated, non-PE, non-auditor)
  → services.insight_interactions.run_interaction
      → api.insight_authz.authorize_insight_scope   [I2 boundary — unchanged]
      → repos.insight.get_conversation + conversation_is_visible (creator-private)
      → repos.insight.add_message(role='user')      [I1 layer — raw question, PO Q4]
      → services.insight_tools.classify_intent      [I3 — unchanged, deterministic]
      → repos.insight_interactions.create_interaction (lifecycle 'received')
      → mark_executing                              [forward-only, PO Q5/Q7]
      → services.insight_tools.invoke_tool          [I3 — unchanged; re-authorizes every read]
      → project_tool_arguments / project_result_metadata   [allowlists, PO Q6]
      → repos.insight_interactions.record_tool_call (idempotent, PO Q10)
      → infra.llm_client.LLMClient.complete         [existing provider abstraction, PO Q14]
      → AnswerStatus resolution                      [I4 vocabulary, PO Q3/Q11]
      → repos.insight.add_message(role='insight')    [narration is a message, not evidence]
      → infra.audit_logger.AuditLogger.log_action → data.audit.AuditRepository
                                                   → public.audit_trail  [PO Q2/Q9]
      → complete_interaction (single forward-only update)
```


---

## 5. Files changed

**New (implementation):**

| File | Lines | Purpose |
| --- | --- | --- |
| `supabase/migrations/20261003000000_p8_i4_insight_interactions.sql` | 392 | Layer-2 tables, indexes/constraints, append-only triggers, creator-private RLS, grants, comments, post-condition guards |
| `backend/domain/insight_interaction.py` | 265 | I4 contract: `AnswerStatus` (14), `InteractionLifecycle`, `NarrationState`, allowlists, projections, hashing, status combination |
| `backend/data/insight_interactions.py` | ~400 | Append-only repository (interaction + tool-call evidence), idempotent tool-call insert, explicit no-op boundaries for `get`/`save`/`delete` |
| `backend/services/insight_interactions.py` | ~640 | Orchestration: authorize → persist → classify → tool → evidence → narration → answer state → audit → complete |
| `backend/api/v3_insight_interactions.py` | 112 | `POST/GET /api/v3/insight/interactions` (+ single read) |

**New (tests):** `tests/unit/data/test_i4_insight_migration.py` (131), `tests/unit/api/test_v3_insight_i4_interactions.py` (513), `tests/unit/api/test_v3_insight_i4_wiring.py` (4 tests).

**Modified (minimal, additive):**

| File | Change |
| --- | --- |
| `backend/api/dependencies.py` | Import + `RepositoryBundle.insight_interactions` field + construction in `get_repositories()` (real wiring) |
| `backend/api/router.py` | Import + `include_router(v3_insight_interactions_router)` |
| `backend/tests/unit/api/fakes.py` | Shared in-memory bundle exposes `insight_interactions` (I3 D-01 lesson) |
| `backend/tests/unit/data/test_i1_insight_migration.py` | Migration-position expectation now allows the PO-authorized I4 migration |
| `backend/tests/unit/data/test_i2_insight_authorization_contracts.py` | Latest-migration expectation updated; I2's one-policy scope assertion unchanged |
| `docs/architecture/CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION_v1.1_20260921.md` | Additive §48.5 decision intake (Q1–Q14 + I4 status); no other content rewritten |
| `docs/implementation/phase8/CT-P8-I4-INSIGHT-IMPLEMENTATION-20260921.md` | This report |

**Not touched:** `public.ai_content_history` (and its four policies), `prisma/schema.prisma`, `public.audit_trail` DDL, I1/I2/I3 code and migrations, the I3 `ToolStatus` contract, `infra/llm_client.py`, `infra/ai_runtime.py`, `infra/audit_logger.py`, `data/audit.py`, `domain/audit.py`, and all other unrelated schema.

---

## 6. Migrations created

Exactly one, additive and idempotent: **`20261003000000_p8_i4_insight_interactions.sql`**.

* `public.carbontally_insight_interactions` — identity, tenant/conversation/creator keys, `lifecycle`, `answer_status`, `message_id`, `audit_record_id`, `idempotency_key`, `question_hash`, `request_hash`, `intent`, `intent_source`, `provider`/`model`/`model_version`, `narration_state`, nullable `tokens_used`/`cost`, counters, `error_class`, `metadata`, timestamps; CHECK constraints for both vocabularies, counts, and terminal-state coherence; composite FK to the I1 conversation preserving organisation consistency.
* `public.carbontally_insight_tool_calls` — `tool_call_id` child rows with closed-catalogue `tool_name`, closed I3 `tool_status`, allowlisted `arguments`/`result_metadata`/`references`, `arguments_hash`, `result_hash`, bounds and latency.
* Indexes: `(organization_id, created_at DESC)`, `(organization_id, created_by, created_at DESC)`, `(conversation_id, created_at ASC)`, `(interaction_id, call_ordinal ASC)`, `(organization_id)`; unique partial index for idempotency; unique `(interaction_id, tool_name, arguments_hash)`; unique `(interaction_id, call_ordinal)`.
* Append-only enforcement: `ci_tool_calls_immutable` (blocks UPDATE/DELETE) and `ci_interactions_immutable` (blocks DELETE, blocks any change to immutable columns, permits only `received→executing→completed|failed`).
* RLS: enabled on both; `anon` revoked; `authenticated` SELECT+INSERT only with UPDATE/DELETE/TRUNCATE/TRIGGER/REFERENCES/MAINTAIN revoked; `service_role` ALL; four creator-private policies (`created_by = auth.uid()` **and** `is_org_member(organization_id)`).
* Post-conditions: raises if fewer than four policies exist (mirrors the Phase 8 RLS-enablement guard style).

---

## 7. Persistence model

Three layers, never collapsed (Master Spec §20.1):

* **Layer 1 (I1, unchanged)** — raw question and narration text live here as messages (`role='user'` / `role='insight'`), creator-private.
* **Layer 2 (new, I4)** — append-only interaction + tool-call evidence: ids, statuses, allowlisted projections, hashes, timestamps, attribution. **No raw question text, no answer text, no raw tool payloads.**
* **Layer 3 (existing)** — `public.audit_trail` via `AuditLogger`; carries correlation ids/statuses only, never payloads.

---

## 8. Authorization model

* Every I4 request passes `require_insight_user` at the router and `authorize_insight_scope` inside the service (active organisation, membership/consultant/staff resolution, auditor and PE denial) — the I2 boundary is **called, never re-implemented**.
* Conversation access uses the I1 creator-private predicate; a foreign or absent conversation is a `404` (existence not disclosed).
* Layer-2 reads are creator-scoped (`created_by = access.user_id`) in SQL and in RLS.
* Tool reads are re-authorized inside I3 on every invocation and again against the resolved object; stored references remain locators, never grants.
* No new persona, permission, role, or shared-visibility path exists; RLS was strengthened for the new tables and no existing policy was weakened.

---

## 9. Orchestration flow

Implemented exactly as authorised (§3 step list): a malformed or unauthorised request is refused **before** any evidence is written; the interaction row is created before execution so a tool/provider failure still leaves truthful evidence; the completion update happens once, with the audit record id attached.


---

## 10. Tool integration

* Only the **closed I3 catalogue** is reachable: `report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup`. No I4 tool, no arbitrary SQL, no mutation tool exists.
* Execution goes through the unchanged `services.insight_tools.invoke_tool`, so the six-point contract, the input bounds, the output allowlists and the reference kinds are inherited rather than restated.
* Tool scoping is deterministic: the tool is chosen by `classify_intent`, and its identifier comes from a UUID present in the question. If the required identifier is absent, no tool is executed and the answer state is `needs_clarification` — the orchestrator never guesses a scope.
* Persisted per call: tool name, contract version, closed tool status, allowlisted arguments, normalised result metadata, reference locators, argument/result hashes, item counts, truncation flag, latency.
* Every earlier read is re-authorized; the audit event records the tool-call ids, not the tool data.

## 11. Provider integration

* The **existing** `infra.llm_client.LLMClient` is used; no second provider architecture, no direct HTTP in application code, no provider logic duplicated.
* `services.insight_interactions.narration_client()` reuses the same environment variables the existing AI runtime already reads (`CARBONTALLY_AI_BASE_URL`/`CARBONTALLY_AI_API_KEY`/`CARBONTALLY_AI_MODEL`) and returns `None` when unconfigured — no new configuration surface, and **no change to `infra/ai_runtime.py`**.
* Attribution is truthful: `provider`/`model`/`model_version` are only recorded when a call **succeeded**, sourced from `configured_ai_attribution()`. A configured-but-unused provider is never reported as used.
* Retries are bounded (`MAX_PROVIDER_ATTEMPTS = 2`) and never replay a side effect; the narration prompt carries only the tool's declared output, truncated (`MAX_NARRATION_CONTEXT_CHARS = 2000`).
* Usage/cost are persisted as **NULL** (the abstraction exposes no authoritative usage) — no fabricated telemetry.

## 12. Answer-status mapping

| Deterministic input | I4 answer state |
| --- | --- |
| tool `success` | `success` |
| tool `no_data` | `no_data` (never converted to `zero`) |
| tool `not_authorized` | `not_authorized` |
| tool `invalid_input` | `invalid_input` |
| tool `error` | `error` (lifecycle `failed`) |
| intent `ambiguous_intent` | `needs_clarification` |
| intent `unsupported_intent` | `refused` |
| no identifier for the required parameter | `needs_clarification` |
| several tool outcomes | combined deterministically; mixed outcomes → `partial` |
| optional narration unavailable | deterministic state preserved, `narration_state = unavailable` |
| required narration unavailable | `provider_unavailable` (deterministic references preserved) |
| canonical audit append failure | `error` + `lifecycle = failed` + `error_class = audit_append_failed:<Exception>` |
| malformed request body | HTTP 422, **no** Layer-2 evidence written |

The closed I3 `ToolStatus` six-value contract is unchanged; the fourteen-state I4 vocabulary is separate (`zero` is retained in the vocabulary but is **not** produced by this implementation — no ratified tool currently exposes an authoritative zero signal, so `no_data` is used instead, per §14's cardinal rule).

## 13. Audit implementation

* Canonical ledger: `public.audit_trail`, through `infra.audit_logger.AuditLogger.log_action` → `data.audit.AuditRepository.record` (append-only, Phase 7 trigger).
* Event: `action = insight.interaction.<completed|failed>`, `entity_type = insight_interaction`, `entity_id = interaction_id`, `correlation_id = interaction_id`, `actor = caller`, `changed_fields = {interaction_id, organization_id, tool_call_ids, tool_statuses, answer_status, narration_state, layer}`, `reason = error_class when present`.
* Correlation requirement met: the audit row identifies the interaction and its tool calls by id; **no** prompt, answer or tool payload is written to the ledger (§20.4).
* The audit record id is stored on the interaction row; if the audit append fails the interaction is marked `failed` with `answer_status = error`, so audit failure can never present as a successful answer.

## 14. Idempotency / retry

* `idempotency_key` (≤128 chars) is unique per organisation (partial unique index); a replayed request returns the stored outcome with `replayed: true`, the same `interaction_id`, and **no** second interaction or tool-call row.
* The same logical tool call cannot be duplicated: unique `(interaction_id, tool_name, arguments_hash)` plus `ON CONFLICT DO NOTHING` returning the existing evidence row.
* Lifecycle completion is a single guarded UPDATE; the DB trigger refuses a second completion or any immutable-column change.
* Provider attempts are bounded; there is no unbounded loop and no automatic replay of side effects (all I4 tools are read-only).

## 15. Privacy boundaries

* Raw question text: **I1 message only** (PO Q4); Layer 2 keeps a sha256 hash.
* Narration text: **I1 message only** (role `insight`); Layer 2 keeps only `narration_state`.
* Tool data: allowlisted projection only — result `data` payloads, signed/artefact URLs, internal actors and content-bearing fields are excluded by omission; the projection test asserts a stubbed payload containing secrets/URLs leaves no trace in persisted evidence.
* Secrets/keys: never stored, never logged; the provider key is read from the environment at call time and never returned.
* No retention, deletion, export, purge or billing behaviour was added (Q12/Q13 remain deferred), and logs carry failure classes rather than payload values.



---

## 16. Tests

**I4 suites (new):**

| Suite | Covers |
| --- | --- |
| `tests/unit/data/test_i4_insight_migration.py` | canonical namespace; no legacy/unrelated schema touched (comments and string literals stripped before asserting, so the migration's own prohibition prose cannot satisfy the check); both status vocabularies present and separate; append-only triggers; creator-private RLS; anon revocation + authenticated SELECT/INSERT-only; no I5/I7/I8 surfaces; hashes-not-text |
| `tests/unit/api/test_v3_insight_i4_interactions.py` | success persistence + audit correlation; raw question only in I1; tool-call idempotency; no payload/URL leakage; tool-status → answer-status mapping (no_data / not_authorized / invalid_input / error); clarification + refusal for ambiguous/unsupported/missing-identifier; the fourteen-state I4 vocabulary vs the six-value I3 vocabulary; optional-narration failure keeps the deterministic answer; required-narration failure = `provider_unavailable` without fabrication; attribution truthful and only on success; cross-organisation denial with **no** evidence written; inactive organisation denial; creator-private read/list do not disclose another creator; invalid input fails closed with no persistence; audit-append failure produces a truthful `error`/`failed` outcome |
| `tests/unit/api/test_v3_insight_i4_wiring.py` | the REAL `RepositoryBundle` declares and the REAL factory constructs every repository I4 resolves; the service module has no import-time `api.*` dependency; the real bundle exposes `InsightInteractionRepository` and its append-only boundary |

**I3 integration coverage:** exercised through the service with the I3 tool layer stubbed for specific outcomes, and through the unchanged I3 suites (`test_v3_insight_i3_tools.py`, `test_v3_insight_i3_wiring.py`) which continue to pass unchanged, so the I3 contract is proven intact rather than re-tested.

**Security regression:** the I1/I2/I3 suites were re-run unchanged in the focused run below (no test was weakened; the only two legacy edits are the migration-position expectations, updated because the PO authorised a new migration — their policy/scope assertions are untouched).

**Focused I4 + I1/I2/I3 regression run:** `exit=0` — the command above covers the four I4 suites plus the I3 tools/wiring, I2 authorization/contracts and I1 migration suites.

## 17. Full-suite result

```text
4 failed, 2909 passed, 8 skipped in 287.77s (0:04:47)
```

## 18. Known pre-existing failures

- `FAILED tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered`
- `FAILED tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered`
- `FAILED tests/unit/api/test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained`
- `FAILED tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`

The four long-standing pre-existing failures (three in `tests/unit/api/test_review_sla_surfaces.py` and `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`) were previously assessed as I3-independent; this run is compared against that baseline and any additional failure introduced by I4 would be reported here.

## 19. Limitations

* **Not verified.** This is Cline's implementation; independent verification (OHD) has not been performed and must not be inferred from these results.
* No database was created, migrated or queried: the migration is validated structurally, and the orchestration is exercised against in-memory repositories. The live-RLS behaviour of the new tables has **not** been executed against PostgreSQL.
* `zero` is retained in the answer vocabulary but is not produced by this implementation (no ratified tool exposes an authoritative zero signal); `no_data` is used instead and is never converted to zero.
* Tool scoping is deliberately narrow: one ratified tool per interaction, selected deterministically from keywords plus a UUID in the question. A question that needs several scopes, or that carries no identifier, yields `needs_clarification`/`partial` rather than a guessed multi-tool plan.
* Narration is a single bounded call per interaction (no streaming, no long context assembly — that is I5).
* Usage/cost remain NULL because the provider abstraction exposes no authoritative usage.
* `provider_unavailable` is produced only when narration is explicitly requested (`narration=required`) or unconfigured-required; `zero`, `tool_failure`, `rate_limited`, `ungrounded` and `insufficient_data` remain available-but-unproduced states in this implementation.
* Live provider integration was not exercised (no provider was called); provider behaviour is covered by failing and working fakes.

## 20. Explicit I5 / I6 / I7 / I8 boundary

* **I5 (context management):** not implemented. No conversation context assembly, no compaction policy, no history window. The narration prompt carries only the current tool's declared output.
* **I6 (Insight UI):** not implemented. No frontend change of any kind.
* **I7 (privacy/retention/export):** not implemented. No retention schedule, no deletion workflow, no export API, no purge; the repository refuses `delete`/`save` explicitly and the migration contains no retention field.
* **I8 (billing/production hardening):** not implemented. No credits, quotas, metering, invoices or plan enforcement; existing billing code untouched.
* Also deliberately absent: RAG, embeddings, vector search, LangChain/orchestration frameworks, model-training infrastructure, new personas/permissions/tools, autonomous actions, and any modification to `public.ai_content_history`, `public.audit_trail`, I1, I2 or I3.

## 21. Final implementation verdict

# `I4 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`

**IMPLEMENTED** (this report, by Cline): Layer-2 persistence, orchestration, tool integration, provider narration with truthful attribution, the fourteen-state answer model, canonical-audit correlation, idempotency/retry bounds, creator-private authorization, the I4 API surface, tests, and the additive Master Specification decision intake.

**NOT VERIFIED** (not claimed): independent verification, live-database migration execution, live-RLS enforcement, live-provider behaviour, and any acceptance/closure of I4. I4 remains open pending OHD verification and the PO's closure decision. I5–I8 remain NOT AUTHORISED.

---

# 22. I4 BOUNDED REMEDIATION (2026-09-21) — OHD D-1…D-4

**22.1 OHD report reference.** `docs/implementation/phase8/CT-P8-I4-OHD-VERIFICATION-20260921.md` (commit `b33f16c9248eda38661cc0ce57dfe20489fd5f87`), verdict `FAIL — I4 IMPLEMENTATION NOT VERIFIED`; verified implementation `d9bdfab`. Full detail: `CT-P8-I4-REMEDIATION-20260921.md`.

**22.2 D-1 remediation.** The shipped migration declared the column `references` unquoted (reserved keyword) → `syntax error at or near "references"`. Fixed by consistently quoting `"references"` in the DDL (same identifier, no rename, no semantic change, no unrelated column touched).

**22.3 D-2 remediation.** `_TOOL_CALL_COLUMNS` and `_RECORD_TOOL_CALL_SQL` in `backend/data/insight_interactions.py` used the bare word; both now use `"references"`, with placeholder order unchanged. Reference semantics, projections, hashes and the I3 contract are untouched.

**22.4 D-3 remediation.** asyncpg returns `jsonb` as text here, and `dict(str)` raised `ValueError` in the mappers. `metadata`, `arguments`, `result_metadata` and `references` are now decoded through the project helper `data.base.loads_jsonb()` (the convention used by ~57 repositories), NULL defaults preserved, reference items guarded. No parallel JSON mechanism, no other repository modified.

**22.5 D-4 provisioning verification.** D-4 was a consequence of D-1. With D-1 corrected, the unmodified shipped migration applied cleanly to a fresh disposable PostgreSQL 17.6 database and every intended control was confirmed: both tables, RLS enabled on all four `carbontally_insight_*` tables, 8 policies (4 I4 creator-private), both append-only triggers, `authenticated` = INSERT,SELECT only, and the post-condition guards passed. No control was redesigned.

**22.6 Tests added/changed.** New `tests/unit/data/test_i4_repository_sql_and_jsonb.py` (reserved-identifier guard for the migration and the SQL constants; placeholder/column alignment; asyncpg-text JSONB mapper regressions incl. NULL/malformed references) and new `tests/integration/test_i4_live_migration_and_persistence.py` (live disposable-DB migration + controls, real repository round-trip, `"references"` round-trip, append-only enforcement, RLS smoke). No existing test was weakened.

**22.7 Migration execution result.** `psql -1 -v ON_ERROR_STOP=1 -f supabase/migrations/20261003000000_p8_i4_insight_interactions.sql` → `apply_exit=0` (atomic, no error) on the disposable database `ct_i4_remediate_20260921`.

**22.8 Real PostgreSQL result.** Live suite: **4 passed** — migration applies and provisions every control; real repository create/mark/record/read/complete; tool-call idempotency; JSONB and `"references"` round-trip; append-only rejection of UPDATE/DELETE on interactions and tool calls.

**22.9 Real HTTP result.** Not re-run against the live database in this bounded remediation (root cause D-3 is proven fixed at the mapper/asyncpg boundary by §22.8, which the HTTP path uses). The HTTP suite remains the in-memory orchestration suite; a live-DB HTTP round-trip is recorded as a remaining limitation for OHD to exercise.

**22.10 Security smoke-test result.** Live RLS smoke passed: creator allowed, peer denied, forged `created_by` denied, anonymous denied; grants show `authenticated` holds only INSERT,SELECT.

**22.11 I3 regression result.** The I3 tools and wiring suites pass unchanged; four-tool catalogue, six-point contract and `ToolStatus` untouched; I1/I2 suites also pass unchanged.

**22.12 Files changed.** The migration, `backend/data/insight_interactions.py`, the two new test modules, this report and `CT-P8-I4-REMEDIATION-20260921.md`. Nothing else.

**22.13 Limitations.** Independent verification outstanding; live suite requires a disposable DSN and skips otherwise (executed here); no live-DB HTTP round-trip; OHD observations O-1…O-8 not addressed (out of scope); declared-but-unproduced answer states unchanged.

**22.14 Verification status.** **Independent OHD verification remains PENDING.** This remediation claims neither `VERIFIED` nor `I4 CLOSED`; the implementation verdict remains `I4 REMEDIATION IMPLEMENTED — READY FOR OHD RE-VERIFICATION`.
