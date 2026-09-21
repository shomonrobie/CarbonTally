# CT-P8-I4-OHD-VERIFICATION-20260921

**Independent verification of the authorized Phase 8 I4 implementation.**

**Verdict:** `FAIL — I4 IMPLEMENTATION NOT VERIFIED`
**Verified implementation revision:** `d9bdfabbad52bb6117bf860b0c87f2c917458d1e` (`d9bdfab`)
**Independent verifier:** OHD (read-only). **Verification date:** 2026-09-21.

> This report performs verification only. No defect was fixed. No application code, migration, schema, test, configuration, Master Specification text or architecture document was modified. No database was migrated; no RLS policy was changed; no production system was contacted. The only repository change is this report.

---

## 1. Verification authority

Read and reconciled before testing:

| # | Document | Role |
|---|---|---|
| 1 | `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` | D2 ratification — §7 (Layer 2 = I4), §8/§9.2 (creator-private, re-authorize every read), §22 (dormant AI structure), R24 (canonical namespace) |
| 2 | `docs/architecture/CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION_v1.1_20260921.md` | Master Specification v1.1 — §8.1/§9.3 (Layer-2 record), §14 (answer states), §20.1/§20.4 (no layer collapse, no payloads in the ledger), §23, §48.5 (I4 decision intake) |
| 3 | `docs/architecture/CARBONTALLY_P8_I3_INSIGHT_CLOSURE_20260921.md` | I3 closed — VERIFIED PASS at `651f8c1`, OHD report `7faaa57`; four ratified tools; `ToolStatus` six-value contract |
| 4 | `docs/architecture/CARBONTALLY_P8_I4_Q1_AI_CONTENT_HISTORY_CLOSURE_20260921.md` | Q1 CLOSED — Option C (retain unchanged, outside I4); Q2–Q14 remain formally unresolved in that document |
| 5 | `docs/implementation/phase8/CT-P8-I4-PREAUTHORIZATION-READINESS-AUDIT-20260921.md` | Pre-authorization readiness audit; Q1 disposition `UNRESOLVED` at that time |
| 6 | `docs/implementation/phase8/CT-P8-I4-Q1-AI-CONTENT-HISTORY-DISPOSITION-PREPARATION-20260921.md` | Q1 disposition preparation record |
| 7 | `docs/implementation/phase8/CT-P8-I4-INSIGHT-IMPLEMENTATION-20260921.md` | Cline's implementation report (claim set under test) |
| 8 | I1/I2 implementation + OHD verification evidence | Layer boundaries and authorization model |
| 9 | I3 implementation + OHD verification evidence | Closed tool contract |
| 10 | All 15 I4 changed files at the target revision | Primary evidence |

The PO Q1–Q14 decision register recorded before I4 implementation was treated as authoritative (Master Spec §48.5, commit `4c7175b`).

**Governance observation (OBSERVATION, non-blocking for the technical verdict):** the only I4-authorisation artefact present in the repository is Master Spec §48.5, which records "I4 is **AUTHORISED — IMPLEMENTATION IN PROGRESS** (PO I4 Implementation Authorization, 2026-09-21)". The separately-recorded `CARBONTALLY_P8_I4_Q1_AI_CONTENT_HISTORY_CLOSURE_20260921.md` states that Q1 closed only Q1 and that "I4 therefore remains **NOT AUTHORIZED** until the remaining blocking pre-authorization decisions are resolved". Both statements coexist in the tree; the implementation report cites the later I4 Implementation Authorization. This verifier takes the brief's instruction (Q1–Q14 authoritative) at face value and does not re-litigate authorization, but the PO should note that the Q2–Q14 decision text is not itself a repository artefact.

## 2. Starting HEAD

| Item | Value |
|---|---|
| Checkout | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` (never switched) |
| HEAD at start of verification | `4c7175b7279c005a9f659390d39d83a84a07486b` |
| `github/p8-release-reconciled` | `4c7175b7279c005a9f659390d39d83a84a07486b` |
| Ahead/behind | `0 0` |
| Working tree | clean (`--untracked-files=all` empty); no stash |
| Implementation commit reported by Cline | `4cddd828defadedbbeb1d7144a0bee953306b4b7` |

**Pre-flight discrepancy found (and resolved).** The brief names the expected implementation revision as `d9bdfab`. The checkout's HEAD and the remote were **`4c7175b`**, not `d9bdfab`. Investigation:

* `d9bdfab` = implementation commit ("feat(p8-i4): authorized I4 implementation…", Cline, 2026-09-21 20:27:55, parent `4cddd82`, **15 files, 2843 insertions, 2 deletions**).
* `4c7175b` = a second commit **44 seconds later with an identical subject line**, changing **one file only** — `docs/implementation/phase8/CT-P8-I4-INSIGHT-IMPLEMENTATION-20260921.md` (+5/−2) — which back-filled the full-suite result and the pre-existing-failure list into the report.
* Trees differ; `d9bdfab` **is an ancestor of** `4c7175b`; the only delta is documentation.

Consequence: the **application, schema and test footprint is entirely in `d9bdfab`**, and the code at `4c7175b` is identical to the code at `d9bdfab`. Verification was therefore performed on the code state of `d9bdfab` (= `4c7175b`), which is the revision the brief names. The duplicated commit subject is recorded as an `OBSERVATION` (traceability hygiene, not a code defect).

## 3. Verified HEAD

`d9bdfabbad52bb6117bf860b0c87f2c917458d1e` — application/schema/test content verified.
`4c7175b7279c005a9f659390d39d83a84a07486b` — repository HEAD and remote tip at verification time (documentation-only delta).

## 4. Repository / remote state

| Item | State |
|---|---|
| Branch | `p8-release-reconciled` |
| `github/p8-release-reconciled` | `4c7175b…` (aligned `0 0` at start) |
| `origin` | dead local path `/tmp/ct_step2` — **not repaired, not used** |
| Working tree at start / during testing | clean; no tracked file modified by this verification |
| Target revision ancestry | `d9bdfab` confirmed ancestor of HEAD |

## 5. Exact implementation footprint

`git diff --name-status 4cddd82 HEAD` — **15 files, 2846 insertions, 2 deletions**; **13** application/schema/test + **2** documentation. Matches Cline's report exactly.

**New (5)**
* `supabase/migrations/20261003000000_p8_i4_insight_interactions.sql` (392 lines)
* `backend/domain/insight_interaction.py` (265)
* `backend/data/insight_interactions.py` (~400)
* `backend/services/insight_interactions.py` (~640)
* `backend/api/v3_insight_interactions.py` (112)

**New tests (3)** — `tests/unit/data/test_i4_insight_migration.py` (131), `tests/unit/api/test_v3_insight_i4_interactions.py` (513), `tests/unit/api/test_v3_insight_i4_wiring.py`.

**Modified (5)** — `backend/api/dependencies.py` (+4: import, bundle field, real construction in `get_repositories()`, comment), `backend/api/router.py` (+3: import, comment, `include_router`), `backend/tests/unit/api/fakes.py` (+3), `backend/tests/unit/data/test_i1_insight_migration.py` (expectation widened to allow the I4 migration), `backend/tests/unit/data/test_i2_insight_authorization_contracts.py` (latest-migration expectation; **I2's `CREATE POLICY` count assertion retained**).

**Documentation (2)** — Master Spec §48.5 (additive, 31 lines) and Cline's I4 report.

**Not touched (verified by empty diff)** — `backend/domain/insight_tool.py`, `backend/services/insight_tools.py`, `backend/api/v3_insight_tools.py`, `backend/api/insight_authz.py`, `backend/data/insight.py`, `backend/domain/audit.py`, `backend/data/audit.py`, `backend/infra/llm_client.py`, `backend/infra/ai_runtime.py`, `backend/infra/audit_logger.py`, the I1/I2 migrations, and `prisma/schema.prisma`.

## 6. Evidence sources

Repository diff/blame/log evidence; the migration and all four new modules read in full; the three new suites and two modified suites read; the real HTTP path exercised with `create_app()` + the real `get_repositories()` factory + a real PostgreSQL database; three disposable databases created for live testing (below); the full unit suite executed.

## 7. Test environment (verifier-owned, disposable, outside the repository)

| Object | Purpose | Notes |
|---|---|---|
| `ct_i4_verify_20260921` | Clone of `ct_i2_verify_20260921` with the **shipped migration applied exactly as shipped** (abort-on-error runner) | State: `interactions` table only; `tool_calls` absent; RLS off; no triggers; no grants |
| `ct_i4_case_b` | Same clone, shipped migration applied with a **continue-on-error** runner | State: `interactions` + RLS + 1 trigger + 2 policies; `tool_calls` still absent; 14 errors |
| `ct_i4_diag_20260921` | Same clone with a **one-line-corrected copy** of the migration kept in `/tmp` (outside the repository) | **Diagnostic only — not the shipped artifact, not a fix.** Used to determine whether the reserved word is the sole blocker and whether the designed semantics hold |
| PostgreSQL | 17.6 at `127.0.0.1:54426`, roles `anon`/`authenticated`/`service_role`, functional `auth.uid()` reading `request.jwt.claims`, `public.is_org_member` | Real RLS evaluation, not mocks |

No production system was contacted. Fixtures created only inside the disposable databases (organizations, memberships, users, conversations) and inside `/tmp`.

## 8. Migration execution status — `FAILED`

**BLOCKER D-1.** The shipped migration **cannot be applied to PostgreSQL**. Applying
`supabase/migrations/20261003000000_p8_i4_insight_interactions.sql` verbatim:

```
psql:...20261003000000_p8_i4_insight_interactions.sql:172: ERROR:  syntax error at or near "references"
LINE 15:     references       jsonb NOT NULL DEFAULT '[]'::jsonb,
             ^
```

Line 146 of the migration declares a column named `references` **unquoted**. `REFERENCES` is a reserved keyword in PostgreSQL and cannot be used as a bare column name. Minimal independent repro on the same server:

```
$ psql -c "CREATE TEMP TABLE t_probe (references jsonb)"
ERROR:  syntax error at or near "references"
```

**Blast radius depends on the runner, and in both cases the feature cannot work:**

*Runner aborts on error (`ON_ERROR_STOP=1`, transactional CLI):* 3 statements applied before the abort — `carbontally_insight_interactions` exists with its 6 indexes; **`carbontally_insight_tool_calls` does not exist**; **RLS is not enabled** on the created table; **no append-only trigger exists**; **no grants were issued** (only the owner role holds privileges). Verified live:

| Check | Result |
|---|---|
| `carbontally_insight_interactions` | exists |
| `carbontally_insight_tool_calls` | **absent** |
| RLS enabled on interactions | **false** |
| I4 policies (`ci_interactions_*`, `ci_tool_calls_*`) | **0** (the 4 `ci_*` rows in `pg_policies` are I1's `ci_conversations_*`/`ci_messages_*`) |
| Append-only triggers | **0** |
| `ci_interactions_immutable` / `ci_tool_calls_immutable` functions | **0** |
| Grants on interactions | owner only → `SET ROLE service_role; INSERT …` → **`ERROR: permission denied for table carbontally_insight_interactions`** |

*Runner continues on error (psql default):* 14 errors; the three `tool_calls` statements and the final post-condition guard fail; end state `interactions` + RLS + 1 trigger + 2 policies and **`tool_calls` still absent**. The migration's own post-condition (`expected >= 4 creator-private policies`, mirroring the Phase 8 RLS guard style) fires, i.e. the migration reports failure either way.

**Diagnostic isolation of the blocker (not a fix):** a copy of the migration held in `/tmp` with **only** that one line changed to `"references"` applies **cleanly to completion** in a fresh clone. The reserved word is therefore the *sole* migration blocker; every other statement in the migration is syntactically and structurally valid.

**Consequence:** no environment can obtain the Layer-2 schema the implementation depends on. In the abort-on-error case the created table is left with **no RLS, no immutability trigger and no grants** — i.e. the security controls the implementation claims are exactly what is missing — and in the continue-on-error case the tool-call evidence surface does not exist at all.

## 9. Live PostgreSQL / RLS results

Testing is split by evidence class, because the shipped migration cannot produce a usable schema.

**(a) Live results against the state the shipped migration actually produces** (`ct_i4_verify_20260921`): RLS **not enabled** on the only table that exists; **zero I4 policies**; **zero** append-only triggers; `service_role` cannot write the table. Any creator-private enforcement claimed for Layer 2 (`created_by = auth.uid() AND is_org_member(organization_id)`) **does not exist** in that state. → **NOT VERIFIED / BLOCKED by D-1.**

**(b) Diagnostic results against the one-line-corrected copy** (`ct_i4_diag_20260921`), which shows whether the *designed* controls work once the syntax defect is removed. Run as the real `authenticated` role with real `request.jwt.claims` (so `auth.uid()` and `public.is_org_member()` evaluate exactly as under PostgREST):

| # | Test | Result |
|---|---|---|
| R1 | creator SELECT own interaction | allowed (`auth.uid()` resolves; `is_org_member` true) |
| R2 | creator SELECT own tool-call evidence | allowed |
| R3 | **peer in the same organisation** SELECT the creator's interaction | **0 rows — denied** |
| R4 | peer SELECT the creator's tool-call evidence | **0 rows — denied** |
| R5 | **cross-organisation** user SELECT | **0 rows — denied** (`is_org_member` false) |
| R6 | **member of an INACTIVE organisation** SELECT own interaction | **0 rows — denied** (inactive org ⇒ `is_org_member` false) |
| R7 | **user with no membership** SELECT anything | **0 rows — denied** |
| R8 | creator INSERT own interaction | allowed |
| R9 | INSERT with **forged `created_by`** (another user) | **denied** — `new row violates row-level security policy` |
| R10 | INSERT into an organisation the caller does not belong to | **denied** |
| R11 | UPDATE own interaction as `authenticated` | **denied — `permission denied for table`** (no UPDATE grant, no UPDATE policy) |
| R12 | DELETE own interaction as `authenticated` | **denied — permission denied** |
| R13 | INSERT tool call for one's **own** interaction | allowed |
| R14 | INSERT tool call for **another user's** interaction | **denied** (RLS) |
| R15 | `anon` SELECT interactions / tool calls | **denied — permission denied** |
| R16 | `anon` INSERT interaction | **denied** |

**Conclusion for §9:** the *designed* creator-private RLS and privilege posture is **correct and effective** — including cross-user, cross-organisation, inactive-organisation, no-membership, forged-identity and `anon` denial, with `auth.uid()` and active membership genuinely enforced. But this is a **diagnostic** result on a corrected copy; against the **shipped** migration the controls are **not provisioned at all**. The live posture of the delivered artifact is therefore `NOT VERIFIED — BLOCKED`.

## 10. Persistence results — `BLOCKED`

**BLOCKER D-2.** The application's own SQL uses the same reserved word unquoted, so the tool-call evidence surface is unusable even if the DDL is corrected:

* `data/insight_interactions.py:37` `_TOOL_CALL_COLUMNS` → `… result_metadata, references, arguments_hash …`
* `data/insight_interactions.py:101` `_RECORD_TOOL_CALL_SQL` INSERT column list → `… result_metadata, references, arguments_hash …`

Live confirmation that this is a genuine syntax error in **both** positions, not only in DDL:

```
$ psql -c "SELECT references FROM public.carbontally_insight_tool_calls LIMIT 1"
ERROR:  syntax error at or near "references"
$ psql -c "INSERT INTO public.carbontally_insight_tool_calls (… result_metadata, references, arguments_hash …) VALUES (…)"
ERROR:  syntax error at or near "references"
$ psql -c 'SELECT "references" FROM public.carbontally_insight_tool_calls LIMIT 1'   # quoted form
[]
```

So: canonical namespace (`carbontally_insight_*`) ✓, table design, identity/FK/lifecycle/status/correlation/idempotency columns and indexes are **correctly declared** and were verified live in the diagnostic database (§11), and the migration's `CHECK` constraints correctly pin the closed I3 tool catalogue and the closed I3 `ToolStatus` vocabulary (§10 live checks T-6/T-7). But **no persistence path exists in a shipped environment**, so `NOT VERIFIED — BLOCKED`.

**BLOCKER D-3 — application jsonb mapping.** Independently of D-1/D-2, the repository's row mappers mis-handle `jsonb`:

```
File "backend/data/insight_interactions.py", line 147, in _row_to_interaction
    metadata=dict(r.get("metadata") or {}),
ValueError: dictionary update sequence element #0 has length 1; 2 is required
```

`asyncpg` returns a `jsonb` column as a **`str`** in this codebase (no type codec is registered — verified live: `type: str, repr: '{}'`), and the project has an established helper for exactly this: `data/base.py:97 loads_jsonb()` ("Parse a JSONB value (string, dict or list)"), used by **57 other** `data/*.py` modules including `data/audit.py`. `data/insight_interactions.py` uses it **0** times. The same pattern appears three more times in `_row_to_tool_call` (`dict(r.get("arguments"))`, `dict(r.get("result_metadata"))`, `tuple(dict(x) for x in refs)` — the latter iterating a JSON *string* character-by-character).

Consequence: even with a perfect schema, the **first persistence step** (`create_interaction`, before any tool runs, so every request is affected) raises `ValueError`, which the error boundary converts to **HTTP 500**.

**Layer-2 dependency on `public.ai_content_history`:** `VERIFIED — none`. The only occurrence in the I4 migration is a prohibition comment and a table comment; no code path reads, writes or migrates it (see §23).

## 11. Immutability results

**(a) Shipped state:** **no triggers exist** (abort-on-error runner never reached the trigger section; the continue-on-error runner creates only the interactions trigger). Therefore in a shipped environment interaction rows can be updated/deleted by any role holding privileges, and tool-call evidence cannot be protected because the table is absent. → **NOT VERIFIED / BLOCKED.**

**(b) Diagnostic (one-line-corrected copy), exercised live as owner and as `service_role`:**

| # | Test | Result |
|---|---|---|
| I-1 | create interaction (`received`) | allowed |
| I-2 | `received → executing` | **allowed** (permitted forward transition) |
| I-3 | `executing → completed` (+`completed_at`, `answer_status`) | **allowed** (single completion update) |
| I-4 | UPDATE a **terminal** row | **denied** — "terminal interaction evidence is immutable (I4 Q5)" |
| I-5 | reopen `completed → executing` | **denied** |
| I-6 | **backward** `executing → received` | **denied** — "not a forward transition (I4 Q5)" |
| I-7 | change immutable column (`created_by`) | **denied** |
| I-8 | UPDATE of a mutable column **without** a lifecycle change (e.g. `provider`) | **denied** — the trigger permits only forward lifecycle transitions |
| I-9 | DELETE interaction | **denied** |
| I-10 | duplicate `idempotency_key`, same organisation | **denied** (unique) |
| I-11 | terminal row without `completed_at` | **denied** (CHECK) |
| I-12 | `answer_status` while non-terminal | **denied** (CHECK) |
| T-1 | create tool call | allowed |
| T-2 | UPDATE tool call | **denied** |
| T-3 | DELETE tool call | **denied** |
| T-4 | duplicate logical call (`interaction_id, tool_name, arguments_hash`) | **denied** |
| T-5 | duplicate `call_ordinal` | **denied** |
| T-6 | unratified tool name (`sql_query`) | **denied** (closed catalogue CHECK) |
| T-7 | non-I3 `tool_status` (`answered`) | **denied** (I3 vocabulary CHECK) |

The designed append-only enforcement is **strong and correct** (it binds `service_role` too, because triggers fire regardless of role), and the two service UPDATE statements are trigger-compatible (verified by reading `_MARK_EXECUTING_SQL` and `_COMPLETE_SQL`: one forward `received→executing`, then a single completion update carrying all mutable fields).

**OBSERVATION (design inconsistency, non-blocking):** I-8 means an interaction row cannot be updated at all without a lifecycle transition — reasonable under Q5, but it also means the declared `ON DELETE CASCADE` foreign keys are unreachable: deleting a conversation (or organisation) that has interactions is blocked by the append-only trigger (verified live: `C-1 DELETE conversation cascading to interactions → BLOCKED by append-only trigger`). A future I7 deletion/retention path therefore cannot rely on the declared cascade. This is consistent with Q5 (evidence must not be deletable) but the declared cascade semantics are misleading.

## 12. I2 authorization results

**Code trace (VERIFIED at source level):** every I4 route is attached to `require_insight_user` and the service calls the closed I2 boundary (`api.insight_authz.authorize_insight_scope`) *before* anything is written; conversation access reuses the I1 creator-private predicate (`conversation_is_visible`) and returns 404 for a foreign or absent conversation (existence not disclosed); Layer-2 reads are creator-scoped in SQL (`AND ($3::uuid IS NULL OR created_by = $3::uuid)`) and under RLS; **stored references remain locators, never grants** — the tool layer re-authorizes on every invocation and again against the resolved object (I3 contract, unchanged).

**Live:** the authorization *negatives* were exercised end-to-end through HTTP for inactive organisation, non-member organisation, foreign conversation and a peer's conversation (§20) — all refused before Layer-2 evidence was written. The creator-private **read** matrix was verified at the database layer (§9 R1–R16).

**NOT VERIFIED:** the service-level I2 re-authorization of a *stored reference created under one valid context and replayed under another* could not be executed end-to-end, because no interaction or tool call can be persisted (D-1/D-2/D-3). The code path is present and calls the unchanged I2/I3 boundary, but live confirmation is blocked.

No I2 regression was found: `api/insight_authz.py` is byte-unchanged, and the modified I2 migration test retains its one-policy scope assertion.

## 13. I1 results

**Code-level `VERIFIED`:** the raw question is persisted exactly once in the I1 message layer (`repos.insight.add_message(role="user", content=text)` at `services/insight_interactions.py:317`) and Layer 2 stores only `question_hash` (sha256) plus ids; narration text is also an I1 message (`role="insight"`, line 473), never Layer-2 evidence. I1 schema, I1 migrations, `data/insight.py` and the I1 authorization model are **byte-unchanged** by I4.

**Live observation:** the same flow wrote 2 I1 insight messages while producing 0 audit rows and 2 orphaned `received` interaction rows (§20), confirming the ordering (question first, evidence second) — i.e. a failed request leaves an I1 question message behind. That is inherent to the declared order rather than an I4-specific defect, but it is worth recording for I7/privacy work.

## 14. I3 regression results

| Check | Result |
|---|---|
| Exactly four authorized tools | **VERIFIED** — `report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup` (4 distinct constants in `services/insight_tools.py`; the new tool-call `CHECK` also pins exactly these four, verified live as T-6) |
| No new I4 tool | **VERIFIED** — no addition to the I3 registry; `v3_insight_tools.py` and `domain/insight_tool.py` untouched |
| `ToolStatus` unchanged | **VERIFIED** — still exactly `success, no_data, not_authorized, invalid_input, provider_unavailable, error`; file byte-unchanged |
| I2 authorization still used | **VERIFIED** — unchanged `authorize_insight_scope`; the I4 service calls it (no re-implementation) |
| Locator/reference semantics unchanged | **VERIFIED** — I3 code untouched; I4 stores locators only |
| Arbitrary SQL / mutation tools unavailable | **VERIFIED** — closed catalogue enforced in code and by DB `CHECK` (live T-6) |
| I3 focused suites | **VERIFIED** — `test_v3_insight_i3_tools.py` + `test_v3_insight_i3_wiring.py` pass unchanged |

No I3 regression identified. I3 was not reopened.

## 15. Deterministic-first results

`VERIFIED` at code-trace level that the implemented sequence is substantively the authorized one:

```
require_insight_user (router)
→ I2 authorize_insight_scope            (before any write)
→ I1 conversation visibility (creator-private, 404 otherwise)
→ I1 add_message(role='user')           (PO Q4 raw question, exactly once)
→ classify_intent (deterministic, I3)
→ Layer-2 create_interaction            (lifecycle 'received')
→ mark_executing                        (forward-only)
→ I3 invoke_tool                        (authorized, allowlisted, read-only)
→ project_tool_arguments / project_result_metadata (Q6 allowlists)
→ record_tool_call                      (idempotent, Q10)
→ bounded optional narration (Q11/Q14)
→ truthful answer state (Q3) → I1 add_message(role='insight')
→ canonical audit (Q2/Q9) → single forward-only completion
```

The provider is **not** used as authorization, evidence source, calculation authority, factor authority or tool authority: evidence comes only from I3 tools, narration receives only the declared tool output (bounded to `MAX_NARRATION_CONTEXT_CHARS = 2000`), narration is attempted only when the tool status is `success`, and no provider output can create a reference or a status.

**NOT VERIFIED live:** the end-to-end flow cannot be executed (D-1/D-2/D-3).

## 16. Provider results

`VERIFIED` at code level:

* the **existing** `infra.llm_client.LLMClient` is used through `narration_client()`, which reads exactly the environment variables the existing AI runtime already reads (`CARBONTALLY_AI_BASE_URL`, `CARBONTALLY_AI_API_KEY`, `CARBONTALLY_AI_MODEL`) and returns `None` when unconfigured — no new configuration surface; `infra/llm_client.py` and `infra/ai_runtime.py` are byte-unchanged;
* retries are bounded (`MAX_PROVIDER_ATTEMPTS = 2`), no side-effect replay (all tools read-only);
* provider exceptions become state (`error_class`), never a fabricated narrative;
* attribution is truthful: `provider`/`model`/`model_version` are recorded **only** when narration text was actually produced, sourced from `configured_provider_attribution()` — a configured-but-unused provider is never reported as used;
* provider-unavailable behaviour: optional narration → deterministic answer kept and `narration_state = unavailable`; `llm_client is None` → `skipped` (optional) / `unavailable` (required); required narration unavailable with an otherwise successful answer → `provider_unavailable` with the deterministic references preserved.

**NOT VERIFIED:** live provider invocation, a real provider failure/timeout, and the true `provider_unavailable` round trip. The suite injects a stub client; no provider is configured in the verification environment, and the endpoint cannot persist in any case (D-3).

## 17. Answer-state results

| Claimed mapping | OHD result |
|---|---|
| 14-state I4 vocabulary present and separate from I3's six-value `ToolStatus` | **VERIFIED** — DB `CHECK` accepts the 14 states on `answer_status` while `tool_status` accepts exactly the six I3 values (live T-7); `domain/insight_tool.py` unchanged |
| tool `success`→`success`; `no_data`→`no_data`; `not_authorized`→`not_authorized`; `invalid_input`→`invalid_input`; `error`→`error`(lifecycle `failed`) | **VERIFIED** at code level (`tool_answer_status`) |
| `ambiguous_intent`→`needs_clarification`; `unsupported_intent`→`refused`; missing identifier→`needs_clarification` | **VERIFIED** at code level (`_INTENT_REFUSAL_ANSWER`, `build_tool_input(...) is None`) |
| `required` narration unavailable → `provider_unavailable` | **VERIFIED** at code level |
| audit append failure → `error` + `failed` + `error_class = audit_append_failed:<Exc>` | **VERIFIED** at code level |
| malformed body → HTTP 422 with no Layer-2 evidence | **VERIFIED live** (HTTP 422 returned) |
| `zero`, `insufficient_data`, `tool_failure`, `partial`, `rate_limited`, `ungrounded` | **VERIFIED as vocabulary-only** — declared in the DB/domain vocabulary but not produced by this implementation |
| **Actually reachable states today** | **NOT VERIFIED** — no state is reachable in a shipped environment because every request fails at the first persistence step (D-3). The states above are reachable *in principle* from the code paths; the `provider_unavailable`, `error` and audit-failure branches required specific injected conditions that the unit suite simulates with fakes and which cannot be reproduced live against the delivered schema |

`ToolStatus` (I3) is unchanged; the I4 vocabulary is separate. Classified as an implementation limitation only for the six unreachable-but-declared states (not a defect on its own, and consistent with the report's disclosure).

## 18. Idempotency / retry results

`VERIFIED` at code level: `idempotency_key` uniqueness per organisation (partial unique index, live I-10 = denied on duplicate); a replayed request returns the stored outcome with `replayed: true` and the same interaction id without creating a second interaction or tool call (`find_by_idempotency_key` short-circuit before any write); `ON CONFLICT (interaction_id, tool_name, arguments_hash) DO NOTHING` prevents duplicate logical tool calls (live T-4); `call_ordinal` uniqueness (live T-5); lifecycle completion is a single guarded UPDATE and the trigger refuses a second completion (live I-5); provider attempts bounded.

**NOT VERIFIED live:** the full retry/replay round trip, "retry after partial failure" and "duplicate completion attempt" through the HTTP path — impossible while every request fails at `create_interaction`. The DB-level invariants that back these claims *are* verified (I-10, T-4, T-5, I-5).

## 19. Audit results

`VERIFIED` at code level: the canonical ledger is `public.audit_trail`, written through the existing `infra.audit_logger.AuditLogger` over `data/audit.py` (`AuditLogger(sink=repos.audit)`), with `action = insight.interaction.<completed|failed>`, `entity_id`/`correlation_id = interaction_id`, the caller as actor, `changed_fields` carrying `interaction_id`, `organization_id`, `tool_call_ids`, `tool_statuses`, `answer_status`, `narration_state`, `layer`, and `reason = error_class`. `domain/audit.py`, `data/audit.py`, `infra/audit_logger.py` and the `audit_trail` DDL are byte-unchanged. No competing ledger table is created by the I4 migration, and no prompt/answer/tool payload is written to the ledger. The audit record id is stored on the interaction row; an audit failure re-marks the outcome as `error`/`failed` (`audit_append_failed:<Exc>`), so audit failure cannot present as success.

**NOT VERIFIED live:** no audit event could be produced, because the flow never reaches the audit step — measured `audit_trail` rows = **0** after the E2E attempts (see §20). The claim "audit-append failure does not produce a false successful interaction" is therefore `NOT VERIFIED` by execution. Note also the ordering consequence observed live: a failure *before* the audit step leaves **no audit trace at all** (0 rows) while leaving I1 messages and an orphaned `received` interaction row.

## 20. API / HTTP end-to-end results

Executed with `create_app()`, the real `get_repositories()` factory, the real I2/I3 layers and a real PostgreSQL database; only `get_current_user` was overridden. Router registration and dependency wiring are real (`api/router.py` includes the I4 router; `api/dependencies.py` constructs `InsightInteractionRepository(pool)`). The new wiring test does use the real factory and asserts the concrete repository type — the I3 D-01 lesson is applied.

| # | Request | Expected | Observed |
|---|---|---|---|
| E2E-A | `POST /api/v3/insight/interactions` (simple deterministic question, no tool) | 201 + persisted interaction | **HTTP 500** `{"error":{"code":"INTERNAL_ERROR", …}}` — `ValueError` in `_row_to_interaction` (D-3) |
| E2E-B | POST with a UUID-bearing question + idempotency key | 201 + tool-call evidence | **HTTP 500** (same failure, before the tool would run) |
| E2E-C | `GET /api/v3/insight/interactions` and `/…/{id}` | creator-scoped readback | not reachable with a real id (no interaction can be completed); read endpoints are registered and were exercised at the DB layer |
| E2E-D | inactive org / non-member org / foreign conversation / peer's conversation / over-long question / malformed body | refusal, no evidence | refusals returned (404/403/422 family) — **authorization negatives behave correctly and wrote no Layer-2 evidence** |
| E2E-E | persisted state after the failures | truthful failure evidence + audit | **2 orphaned rows** `lifecycle=received, answer_status=NULL, completed_at=NULL, audit_record_id=NULL`; **0 audit_trail rows**; 2 I1 messages; `tool_calls` table **absent** |

So: the **API surface, routing, dependency wiring and the authorization refusal path are VERIFIED**; the **functional path is NOT VERIFIED and is in fact non-functional** (HTTP 500 for the simplest valid request).

## 21. Privacy / security results

| Check | Result |
|---|---|
| No other user's interaction obtainable | **VERIFIED live** (DB-layer creator-private: peer 0 rows; §9 R3) |
| No other organisation's interaction obtainable | **VERIFIED live** (R5); service path refuses non-member orgs (E2E-D) |
| Creator-private tool-call evidence | **VERIFIED live in the diagnostic DB** (R4, R14); **NOT provisioned by the shipped migration** |
| Forged `organization_id` / `created_by` | **VERIFIED denied live** (R9, R10) |
| Unauthorized report evidence / calculation snapshot | **NOT VERIFIED live** — I3 unchanged and previously verified; I4 adds no new locator path; the I4 E2E cannot reach the tool layer |
| Stored reference used as a grant | **NOT VERIFIED live** (§12); code path re-authorizes on every read |
| Hidden identifiers through error messages | `OBSERVATION`: the 500 body is a generic `INTERNAL_ERROR` with a `request_id` and no internal identifiers ✓; the ValueError is logged server-side only |
| Secrets/tokens/raw payloads in persisted evidence | `VERIFIED` at code level (allowlisted projections; unknown tools project to `{}`; result `data` payloads and URLs never stored; `references` restricted to reference kinds; provider key read from env, never returned). **NOT VERIFIED live** (no tool-call row can be written) |
| **Security controls absent in the shipped state** | **DEFECT (BLOCKER)** — RLS not enabled, no append-only trigger and no grants on the one table that exists (abort-on-error runner); see §8/§11 |
| `ai_content_history` unexpectedly used | **VERIFIED — not used** (§23) |

No fabrication was observed: no state, provider attribution or usage value is invented by the code, and the failing path reports an internal error rather than a fabricated answer.

## 22. I4 / I5–I8 boundary results

`VERIFIED` — no RAG, LangChain, embeddings, vector search, autonomous action, billing, subscription/credit enforcement, retention/deletion/export, new persona, new permission, new tool, UI implementation or I5 context management was added. The apparent matches in the diff are inside a **negative test** (`test_i4_migration_has_no_i5_i7_i8_surfaces`) that asserts such strings are *absent* from the migration, plus prohibition prose in comments. Q12 and Q13 remain unimplemented and deferred to I7/I8 (no metering, quota, invoice, purge or export code). I5–I8 remain unauthorized; nothing in the footprint authorizes them.

## 23. Q1 regression

`VERIFIED — Q1 honored.`

| Requirement | Result |
|---|---|
| No migration alters `public.ai_content_history` | **VERIFIED** — the only I4-migration occurrences are a prohibition comment and a table comment; no DDL/`ALTER`/policy/grant touching it |
| No application read/write dependency introduced | **VERIFIED** — no code path in any I4 file references it; the diff's only code-side occurrence is a forbidden-name assertion in a negative migration test |
| No Prisma change | **VERIFIED** — `prisma/schema.prisma` byte-unchanged by I4 |
| No RLS change | **VERIFIED** — no occurrence; the table's four policies are untouched (independently re-confirmed on the local demo DB in the prior Q1 verification) |
| I4 does not silently use it | **VERIFIED** |

## 24. Test-suite results

| Run | Result | Comparison |
|---|---|---|
| Focused I4 + I1/I2/I3 (7 suites: I4 interactions, I4 wiring, I4 migration, I3 tools, I3 wiring, I1 migration, I2 contracts) | **83 passed, 0 failed** (exit 0) | Cline reported an equivalent focused pass |
| Full unit suite (`tests/unit`) | **4 failed, 2909 passed, 8 skipped** in 253s | **Identical to Cline's reported 4 failed / 2909 passed / 8 skipped**; pre-I4 baseline (`651f8c1`) was 2889 collected / 2877 passed / 4 failed / 8 skipped |

Failure classification (independently determined, not accepted on assertion):

1. **`test_review_sla_surfaces.py` (3 tests) — pre-existing, environment/version-related, unrelated to I4.** Each asserts a specific path is in `_paths()`, which returns only `{'/api/v2/health'}`: the FastAPI/Starlette version composes included routers lazily, so this helper cannot enumerate the routes. Independently classified in earlier OHD rounds. **`OBSERVATION`:** because `_paths()` sees only `/api/v2/health`, these tests also cannot serve as evidence that the new I4 routes are registered — route registration was instead verified by reading `api/router.py` and by the live HTTP calls in §20.
2. **`test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` — pre-existing failure, symptom +1.** `assert len(names) == 71` now fails with `78 == 71`. The repository already held **77** migration files before I4 (the test was already failing pre-I4), and the PO-authorized I4 migration makes it **78**. So the test is pre-existing and unrelated in nature, but its asserted value drifted further because I4 legitimately added exactly one migration. Not an I4 defect.

**Critical conclusion for §24:** the I4 unit suites **pass** while the delivered artifact cannot be applied to a database and cannot persist anything. The suites assert against the migration **text** and against injected **fakes**, and never execute `_row_to_interaction` / `_row_to_tool_call` (0 references anywhere in `tests/`) nor apply the migration to a live database. The green focused run is therefore **not evidence of working I4 behaviour**, and no test in the suite would have caught D-1, D-2 or D-3.

## 25. Defects and observations

**DEFECT / BLOCKER D-1 — the I4 migration cannot be applied (reserved keyword).**
Affected object: `supabase/migrations/20261003000000_p8_i4_insight_interactions.sql`, line 146 (`references jsonb NOT NULL DEFAULT '[]'::jsonb`), first failure reported at statement offset line 172. Effect: `carbontally_insight_tool_calls` is never created; in the abort-on-error runner `carbontally_insight_interactions` is left **without RLS, without the append-only triggers and without grants**, and `service_role` cannot write it; the migration's own post-condition reports failure. Severity **BLOCKER** (High).

**DEFECT / BLOCKER D-2 — application SQL uses the reserved word unquoted.**
Affected objects: `backend/data/insight_interactions.py:37` (`_TOOL_CALL_COLUMNS`) and `:101` (`_RECORD_TOOL_CALL_SQL`). Effect: `SELECT`/`INSERT` on the tool-call table raise `syntax error at or near "references"` even against a corrected table — the tool-call evidence surface is unreachable. Severity **BLOCKER** (High).

**DEFECT / BLOCKER D-3 — jsonb rows are mis-mapped, so every request returns HTTP 500.**
Affected objects: `backend/data/insight_interactions.py:147` (`_row_to_interaction`: `dict(r.get("metadata") or {})`) and the same pattern in `_row_to_tool_call` (`arguments`, `result_metadata`, `references`). Root cause: `asyncpg` returns `jsonb` as `str` in this project and the codebase's own `data/base.py:loads_jsonb()` helper (used by 57 other repositories) is not used here. Effect: the first persistence step raises `ValueError` for **every** request → HTTP 500 `INTERNAL_ERROR`, an orphaned `received` interaction row, I1 messages written, **no canonical audit event**. Severity **BLOCKER** (High).

**DEFECT / BLOCKER D-4 (derived from D-1) — the shipped security posture is missing.**
In the state the shipped migration produces: RLS **not enabled**, **zero** I4 policies, **zero** append-only triggers, **no** grants — i.e. the creator-private control and the append-only guarantee claimed for Layer 2 do not exist in any environment. The **designed** controls are correct (verified live on a corrected copy, §9/§11), which localises the failure to the provisioning step; but as delivered this is a security-relevant gap. Severity **BLOCKER** (High). Classification note: this is a consequence of D-1 rather than an independent design flaw, and it is *not* exploitable in the abort-on-error state via PostgREST (no grants to `anon`/`authenticated`), but it would be exploited by any role holding privileges and it removes all immutability guarantees.

**OBSERVATION O-1** — Two commits share an identical subject (`d9bdfab`, `4c7175b`), the second amending only the implementation report; the brief's named revision is the parent. Traceability hygiene.
**OBSERVATION O-2** — The append-only trigger makes the declared `ON DELETE CASCADE` foreign keys unreachable (deleting a conversation/organisation with interactions is blocked). Consistent with Q5; misleading cascade semantics for future I7 work.
**OBSERVATION O-3** — A request that fails before the audit step leaves I1 messages plus an orphaned `received` interaction row and **no** audit trace (0 rows). The "truthful failure evidence" intent is not achieved for pre-audit failures.
**OBSERVATION O-4** — `zero`, `insufficient_data`, `tool_failure`, `partial`, `rate_limited`, `ungrounded` are declared but never produced; disclosed by the report as intentional.
**OBSERVATION O-5** — The `_paths()` helper defect (§24.1) means the pre-existing surface tests cannot detect missing route registrations.
**OBSERVATION O-6** — The Q2–Q14 decision text is not itself a repository artefact (§1); only Master Spec §48.5 records the I4 authorization, while the Q1 closure document still states I4 was not authorized.
**OBSERVATION O-7** — The focused I4 suites are green while the feature is non-functional; the suites assert migration text and fakes and never execute the real row mappers nor apply the migration (evidence-masking risk for future stages).
**OBSERVATION O-8** — `I-8`: an interaction row cannot be updated at all without a lifecycle transition; any future field-correction update path must be designed around this.

**No defect was found in:** the authorization model and refusal semantics; the append-only and creator-private **design**; the closed I3 catalogue and `ToolStatus` preservation; the I4/I5–I8 boundary; the Q1 prohibition; the audit *implementation* (code level); the projections allowlists; truthful provider attribution; the canonical namespace; the wiring (real factory, not a test-only attribute); and the scope discipline of the footprint.

## 26. Severity classification

| ID | Finding | Severity | Status |
|---|---|---|---|
| D-1 | Migration unapplicable (reserved keyword `references`) | **BLOCKER — High** | reproduced, root-caused |
| D-2 | Application SQL uses the reserved word unquoted (SELECT/INSERT) | **BLOCKER — High** | reproduced |
| D-3 | jsonb mis-mapped → HTTP 500 for every request; `loads_jsonb` unused | **BLOCKER — High** | reproduced, root-caused |
| D-4 | Shipped state has no RLS, no immutability trigger, no grants | **BLOCKER — High** | reproduced (derived from D-1) |
| O-1…O-8 | Observations as listed in §25 | Informational / Low | recorded |

No Medium-severity defect was identified that is independent of the blockers.

## 27. Exact reproduction steps

**Environment.** PostgreSQL 17.6 at `127.0.0.1:54426`; a clone of the Insight-ready database (`CREATE DATABASE ct_i4_verify_20260921 TEMPLATE ct_i2_verify_20260921`); repository at `d9bdfab` (`/home/shomonrobie/ct_93d5cdd`).

**D-1**
```
$ psql -d postgres -c "CREATE DATABASE ct_i4_verify_20260921 TEMPLATE ct_i2_verify_20260921"
$ psql -d ct_i4_verify_20260921 -v ON_ERROR_STOP=1 \
    -f supabase/migrations/20261003000000_p8_i4_insight_interactions.sql
psql:...:172: ERROR:  syntax error at or near "references"
LINE 15:     references       jsonb NOT NULL DEFAULT '[]'::jsonb,
$ psql -d ct_i4_verify_20260921 -c "CREATE TEMP TABLE t_probe (references jsonb)"   # minimal repro
ERROR:  syntax error at or near "references"
# blast radius
$ psql -d ct_i4_verify_20260921 -c "SELECT count(*) FROM information_schema.tables
    WHERE table_name='carbontally_insight_tool_calls'"        -- 0
$ psql -d ct_i4_verify_20260921 -c "SELECT rowsecurity FROM pg_tables
    WHERE tablename='carbontally_insight_interactions'"       -- false
$ psql -d ct_i4_verify_20260921 -c "SELECT count(*) FROM pg_trigger
    WHERE NOT tgisinternal AND tgname LIKE 'ci_%'"             -- 0
$ psql -d ct_i4_verify_20260921 -c "SET ROLE service_role; INSERT INTO
    public.carbontally_insight_interactions (organization_id,conversation_id,created_by,question_hash)
    VALUES ('11111111-1111-4111-8111-111111111111',gen_random_uuid(),
            'aaaaaaaa-0000-4000-8000-0000000000ad',repeat('a',64))"
ERROR:  permission denied for table carbontally_insight_interactions
```
Continue-on-error variant: same file without `ON_ERROR_STOP` → 14 errors, `tool_calls` still absent, `interactions` has RLS + 1 trigger + 2 policies, and the post-condition guard raises.

**D-2**
```
$ psql -d ct_i4_diag_20260921 -c "SELECT references FROM public.carbontally_insight_tool_calls LIMIT 1"
ERROR:  syntax error at or near "references"
$ psql -d ct_i4_diag_20260921 -c "INSERT INTO public.carbontally_insight_tool_calls
    (interaction_id,organization_id,call_ordinal,tool_name,contract_version,tool_status,
     arguments,result_metadata,references,arguments_hash,result_hash) VALUES (…)"
ERROR:  syntax error at or near "references"
$ psql -d ct_i4_diag_20260921 -c 'SELECT "references" FROM public.carbontally_insight_tool_calls LIMIT 1'
[]                                  -- quoted form is valid
```
(`ct_i4_diag_20260921` = the clone carrying the one-line-corrected *diagnostic* copy of the migration, `/tmp/i4_migration_corrected.sql`; the correction was **not** applied to the repository.)

**D-3**
```
$ cd backend && DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/ct_i4_verify_20260921 \
    .venv/bin/python - <<'PY'
import asyncio, asyncpg
async def main():
    c = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:54426/ct_i4_verify_20260921')
    v = await c.fetchval("SELECT metadata FROM public.carbontally_insight_interactions LIMIT 1")
    print(type(v).__name__, repr(v)); print(dict(v))
asyncio.run(main())
PY
str '{}'
ValueError: dictionary update sequence element #0 has length 1; 2 is required
```
HTTP consequence (probe `/tmp/i4_e2e_probe.py`, real app + real factory + real DB, only `get_current_user` overridden):
```
POST /api/v3/insight/interactions  ->  HTTP 500  {"error":{"code":"INTERNAL_ERROR", …}}
backend/data/insight_interactions.py:147 in _row_to_interaction
    metadata=dict(r.get("metadata") or {}),   -> ValueError: dictionary update sequence element #0 …
interaction rows written: 2 (lifecycle=received, answer_status=NULL, audit_record_id=NULL)
audit_trail rows: 0
```

**D-4** — `pg_tables.rowsecurity = false`, `pg_policies` count for `ci_interactions_*`/`ci_tool_calls_*` = 0, `pg_trigger` count = 0, `role_table_grants` shows the owner role only (commands in D-1).

**Design verification (diagnostic, one-line-corrected copy, `/tmp/i4_live_tests.sql` and `/tmp/i4_rls_tests.sql`)**
```
$ psql -d ct_i4_diag_20260921 -q -f /tmp/i4_live_tests.sql   # I-1…I-12, T-1…T-7, C-1  (all designed controls PASS)
$ psql -d ct_i4_diag_20260921 -q -f /tmp/i4_rls_tests.sql    # R1…R22 (all RLS expectations met)
```

**No repository file was created or modified by any of these steps** — all scripts live in `/tmp`, all databases are verifier-owned, and the final `git status` contains only this report.

## 28. Final verdict

```
FAIL — I4 IMPLEMENTATION NOT VERIFIED
```

Reasons, in order of decisiveness:

1. **The delivered artifact cannot be deployed.** The I4 migration raises `syntax error at or near "references"` and cannot complete in any environment; the Layer-2 tool-call evidence table is never created, and in the abort-on-error path the interaction table is left without RLS, without append-only triggers and without grants (D-1, D-4). Declared migration intent and the passing migration-text test are not substitutes for a schema that exists.
2. **The application cannot persist even with a correct schema.** Its own SQL uses the reserved word unquoted in both the `SELECT` and `INSERT` forms (D-2), and its row mappers mis-handle `asyncpg`'s jsonb-as-string, ignoring the project's established `loads_jsonb` helper, so the first persistence step raises `ValueError` and the endpoint returns **HTTP 500** for the simplest valid request (D-3).
3. **The core I4 behavioural claims are therefore unverified in live conditions** — Layer-2 persistence, append-only enforcement as provisioned, creator-private RLS as provisioned, I2 re-authorization over a *stored reference*, idempotency/replay, canonical audit correlation, provider-unavailable behaviour and the answer-state round trip. Where tested against a diagnostic corrected copy, the **design** proved sound (append-only semantics, creator-private RLS incl. cross-user, cross-org, inactive-org, forged-identity and `anon` denial, closed catalogue/status vocabulary). Where tested against the **shipped** artifact, the controls are absent or non-functional.
4. **The green test suites are not evidence.** The focused I4 suites pass (83/83) and the full suite matches Cline's numbers (4 failed / 2909 passed / 8 skipped), but the I4 suites assert migration **text** and injected **fakes**, never execute the real row mappers, and never apply the migration to a database. No test would have caught D-1, D-2 or D-3.

**Explicitly verified and NOT in question:** the footprint and scope discipline (15 files, no unrelated change); the I3 regression (four tools, unchanged `ToolStatus`, unchanged authorization and locator semantics); the I1/I2 boundaries and the raw-question-in-I1-once rule at code level; the deterministic-first ordering; the truthful-attribution and no-fabrication design; the allowlisted projections; the canonical-audit integration design; the canonical namespace; the real wiring (bundle + factory); the I4/I5–I8 boundary; and **Q1 — `public.ai_content_history` remains untouched and unused**.

**Not verified (stated plainly, not hidden):** live migration execution; live RLS as shipped; live append-only enforcement as shipped; live persistence; live audit events (0 rows observed); live provider behaviour; live idempotency/replay round trip; live tool-call projections; the service-level stored-reference re-authorization replay; and which answer states are actually reachable at runtime.

**Blocking defects:** D-1, D-2, D-3, D-4 (all High/BLOCKER).

**Non-blocking observations:** O-1 … O-8.

---

**STOP.** This verification performed no fix, no remediation and no schema or RLS change. I4 is **not** closed, I5 is **not** authorized, the Master Specification was **not** modified, and no production system was touched. The PO decides the next action after reviewing this report.
