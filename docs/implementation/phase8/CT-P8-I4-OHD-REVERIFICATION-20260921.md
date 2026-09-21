# CT-P8-I4-OHD-REVERIFICATION-20260921

**Independent re-verification of the bounded I4 remediation (OHD D-1…D-4).**

**Verdict:** `PASS — I4 REMEDIATION D1-D4 VERIFIED`
**Remediation revision verified:** `310a62a5d1a822ae51a8bf33e33302b690265c0a` (`310a62a`)
**Independent verifier:** OHD (read-only). **Verification date:** 2026-09-21.

> Verification only. No application, schema, test, configuration, Master Specification or architecture file was modified; no migration was changed; no defect was fixed; no commit was amended. No production system was inspected or contacted. The only repository change is this report.

---

## 1. Mandate and scope

Independently determine **whether `310a62a` resolves OHD blockers D-1 (migration reserved word), D-2 (application SQL reserved word), D-3 (asyncpg JSONB mapping / HTTP 500) and D-4 (control provisioning) without introducing an unrelated regression.** This is not a general I4 redesign review. Previous observations O-1…O-8 were explicitly out of scope and were not turned into work.

Read and independently assessed: the previous OHD report, Cline's remediation report, the updated implementation report, the Master Specification, the I4 source/migration/tests changed by the remediation, and the I1/I2/I3 material needed to confirm their contracts were not altered. Cline's PASS-like evidence was **not** accepted as evidence — every claim below was reproduced independently.

## 2. Starting HEAD

| Item | Value |
|---|---|
| Repository | `/home/shomonrobie/ct_93d5cdd` (only checkout used) |
| Branch | `p8-release-reconciled` (never switched) |
| HEAD at start | `310a62a5d1a822ae51a8bf33e33302b690265c0a` |
| Expected starting revision | `310a62a5d1a822ae51a8bf33e33302b690265c0a` → **exact match** |
| `github/p8-release-reconciled` | `310a62a5d1a822ae51a8bf33e33302b690265c0a` (aligned `0 0`) |
| Working tree | clean (`--untracked-files=all` empty); no stash |
| Other checkouts (`carbon_tally`, `carbon_tally_p8_release`) | not touched |
| `origin` | stale local path `/tmp/ct_step2` — not used |

```
$ git branch --show-current   → p8-release-reconciled
$ git rev-parse HEAD          → 310a62a5d1a822ae51a8bf33e33302b690265c0a
$ git rev-list --left-right --count github/p8-release-reconciled...HEAD → 0  0
```

## 3. Remediation commit verified

`310a62a5d1a822ae51a8bf33e33302b690265c0a` — "fix(p8-i4): remediate OHD D1-D4 verification blockers", author `Cline <cline@carbontally.local>`, 2026-09-21 21:04:28 +0600, parent `b33f16c` (the OHD FAIL report commit).

## 4. Previous OHD report reference

`docs/implementation/phase8/CT-P8-I4-OHD-VERIFICATION-20260921.md`, commit `b33f16c9248eda38661cc0ce57dfe20489fd5f87`, verdict `FAIL — I4 IMPLEMENTATION NOT VERIFIED`, verified implementation revision `d9bdfabbad52bb6117bf860b0c87f2c917458d1e`, blockers D-1…D-4.

## 5. Cline remediation report reference

`docs/implementation/phase8/CT-P8-I4-REMEDIATION-20260921.md`, added by `310a62a`; implementation report updated with additive §22 (`CT-P8-I4-INSIGHT-IMPLEMENTATION-20260921.md`). §22.14 correctly states that independent verification remains pending and that the remediation "claims neither `VERIFIED` nor `I4 CLOSED`" ✓.

## 6. Environment

| Item | Value |
|---|---|
| PostgreSQL | 17.6 (x86_64-pc-linux-gnu), `127.0.0.1:54426`, user `postgres` |
| Roles | `anon`, `authenticated`, `service_role` (`bypassrls=true`), real `auth.uid()` reading `request.jwt.claims`, `public.is_org_member()` |
| Database template | `ct_i2_verify_20260921` (carries the I1 Insight tables + I1 RLS + auth helpers) |
| Disposable DBs created (verifier-owned) | `ct_i4_reverify_20260921` (shipped migration applied), `ct_i4_rv_atomic` (applied with `-1`), `ct_i4_rv_integration` (fresh, for the suite's fresh-DB behaviour), `ct_i4_sens_fresh` (pre-remediation migration) |
| Application harness | `backend/.venv`; real `create_app()`, real `get_repositories()` bundle, real asyncpg, real HTTP via `httpx.ASGITransport` with only `get_current_user` overridden (project convention) |
| Pre-remediation tree | `/tmp/i4_prerev` (extracted with `git archive b33f16c`; repository untouched) |
| Production | not inspected, not deployed, not contacted; no persistent environment used |

## 7. PostgreSQL version

`PostgreSQL 17.6 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 15.2.0, 64-bit` — same major version Cline used, so the D-1/D-4 results are directly comparable.

## 8. D-1 — migration execution: `RESOLVED` ✅

**Defect site (pre-remediation):** line 146 `references jsonb NOT NULL DEFAULT '[]'::jsonb` (unquoted) → `ERROR: syntax error at or near "references"`, migration aborted after creating `carbontally_insight_interactions` and before provisioning any control (the cause of D-4).

**Shipped change:** the identifier is now consistently quoted (with a comment recording why); no rename, no semantic change:

```
$ git diff b33f16c 310a62a -- supabase/migrations/20261003000000_p8_i4_insight_interactions.sql
-    references       jsonb NOT NULL DEFAULT '[]'::jsonb,
+    -- `references` is a PostgreSQL reserved keyword: it must always be quoted
+    -- (OHD D-1 — an unquoted identifier aborts the whole migration).
+    "references"     jsonb NOT NULL DEFAULT '[]'::jsonb,
```

**Independent application of the exact repository migration** (no hand-edited copy), fresh DB, abort-on-error:

```
$ psql -h 127.0.0.1 -p 54426 -U postgres -d postgres -c "CREATE DATABASE ct_i4_reverify_20260921 TEMPLATE ct_i2_verify_20260921"
$ psql ... -d ct_i4_reverify_20260921 -v ON_ERROR_STOP=1 \
      -f supabase/migrations/20261003000000_p8_i4_insight_interactions.sql
psql exit status: 0          ERRORs in output: 0
(file md5 ba6492bb909c744a6fb426e181d6b95f; git blob at 310a62a = fc1f2d0ba18220961b33aabede4c4120372964db)
```

Repeated on a second fresh database **inside a single transaction** (`psql -1`) to test the atomicity claim: `exit status 0`, `ERRORs: 0`.

```
$ psql -h 127.0.0.1 -p 54426 -U postgres -d ct_i4_rv_atomic -1 -v ON_ERROR_STOP=1 -f <migration>
exit status: 0
inventory: tables=2  rls_on=2  triggers=2  policies=8  indexes=11
```

**Resulting schema state (verified by catalogue queries, not by reading the source):**

| Check | Result |
|---|---|
| `carbontally_insight_interactions` exists | ✅ (25 columns) |
| `carbontally_insight_tool_calls` exists | ✅ (16 columns) |
| `"references"` column | ✅ `jsonb`, `is_nullable=NO`, `default='[]'::jsonb` |
| RLS enabled | ✅ both tables (`rowsecurity=true`; all four `carbontally_insight_*` tables true) |
| I4 creator-private policies | ✅ 4 (`ci_interactions_creator_select/insert`, `ci_tool_calls_creator_select/insert`), total 8 `carbontally_insight*` policies incl. I1's 4 |
| Append-only triggers + functions | ✅ `ci_interactions_immutable`, `ci_tool_calls_immutable` (+ both functions) |
| Indexes | ✅ 11 (pkeys, uniques, 5 `idx_ci_*` lookups) |
| Constraints | ✅ closed I3 tool catalogue (`ci_tool_calls_tool_name_check`), closed I3 `ToolStatus` (`ci_tool_calls_tool_status_check`), 14-state `answer_status`, lifecycle/terminal/`completed_at` coherence, counts, two composite FKs |
| Post-condition guards | ✅ passed — the migration's final guard requires `>= 4` creator-private policies; reaching `exit 0` means every guard passed |

**D-1 verdict: RESOLVED.** The shipped artifact — not a hand-edited equivalent — applies cleanly and atomically on PostgreSQL 17.6 and provisions the complete intended schema.

## 9. D-2 — application SQL: `RESOLVED` ✅

**Shipped change (both pre-remediation offenders):**

```
-    "tool_status, arguments, result_metadata, references, arguments_hash, "     # _TOOL_CALL_COLUMNS
+    'tool_status, arguments, result_metadata, "references", arguments_hash, '
-         tool_status, arguments, result_metadata, references, arguments_hash,   # _RECORD_TOOL_CALL_SQL
+         tool_status, arguments, result_metadata, "references", arguments_hash,
```

Placeholder order (`$9::jsonb` for references) is unchanged; the INSERT column list and value list remain aligned (the new regression test asserts this).

**Real execution against the shipped schema** (real `InsightInteractionRepository`, real asyncpg, no mocks):

* **INSERT + RETURNING** — `record_tool_call(...)` executed successfully; `id=7a173e06-972d-4e05-93be-f53ba4ff576f`.
* **SELECT readback** — `list_tool_calls(...)` executed successfully (`rows=1`).
* **Round-trip fidelity** — `arguments`, `result_metadata` and the two `references` locators came back byte-equal to what was inserted.
* **Through the real HTTP route** — a `report_lookup` on a real report id persisted a tool-call row whose `"references"` jsonb contains **1 report + ~200 report_version locators**, read back intact.
* **Reserved-word completeness audit** (`pg_get_keywords()` against the actual column names): `carbontally_insight_tool_calls.references` (`catcode=R`) is the **only** reserved-keyword identifier in the two I4 tables, and it is quoted in both SQL statements; every other occurrence of the word in the data layer is a Python variable/keyword argument. **No residual offender of the D-2 class.**

Repository-level probe result: **25/25 checks passed, 0 failures** (INSERT/RETURNING, SELECT, round-trip, empty defaults, nested objects/arrays, NULL tolerance, idempotent repeat, lifecycle transitions, readback).

**D-2 verdict: RESOLVED.**

## 10. D-3 — JSONB mapping: `RESOLVED` ✅

**Shipped change:** `loads_jsonb` imported from `data.base` (the project helper used by ~57 repositories) and applied to every jsonb read; reference items are guarded with `isinstance(x, dict)`:

```
-        metadata=dict(r.get("metadata") or {}),
+        metadata=loads_jsonb(r.get("metadata")) or {},
-    refs = r.get("references") or []
+    refs = loads_jsonb(r.get("references")) or []
-        arguments=dict(r.get("arguments") or {}),
-        result_metadata=dict(r.get("result_metadata") or {}),
-        references=tuple(dict(x) for x in refs),
+        arguments=loads_jsonb(r.get("arguments")) or {},
+        result_metadata=loads_jsonb(r.get("result_metadata")) or {},
+        references=tuple(dict(x) for x in refs if isinstance(x, dict)),
```

**Runtime verification with the real driver and real database** (JSONB values were *not* substituted with Python dicts):

| Case | Result |
|---|---|
| interaction `metadata` — object | ✅ decoded to `dict` (`{}` on create; `{"layer": 2}` after completion) |
| tool-call `arguments` — object | ✅ `{'report_id': …, 'limit': '5'}` |
| tool-call `result_metadata` — object | ✅ `{'status': 'success', 'truncated': False, 'item_count': 2}` |
| tool-call `references` — array | ✅ two reference items, values preserved |
| empty defaults (`{}` / `[]`) | ✅ `{}` and `()` (not `ValueError`) |
| nested object/array jsonb | ✅ `{"nested": {"a": [1, 2, {"b": "c"}]}}`, `{"flags": [True, False, None]}` survive |
| NULL where permitted (mapper boundary) | ✅ returns `{}` / `()` — the schema declares all four jsonb columns `NOT NULL`, so NULL was exercised by feeding the real mapper a `None` column value as a nullable column would deliver it |
| large array (~200 references) through HTTP | ✅ persisted and read back intact |

**Regression guard (the decisive judgement that the fix is actually exercised):**

```
asyncpg delivers jsonb as: str -> '[{"id": "11111111-…", "kind": "report"}, …]'
old path  dict(str)  -> ValueError: dictionary update sequence element #0 has length 1; 2 is required
```

`asyncpg` still returns jsonb as **text** in this environment, so the mapper path really was exercised, and the original failure signature remains reproducible on the old code — the remediation did not mask the defect by changing the driver's type handling.

**Residual-defect scan:** every remaining `dict(` in the four I4 modules is a legitimate asyncpg-Record→dict conversion (`dict(row)`), a Python-object conversion, or guarded by `isinstance`. No equivalent D-3 defect remains in the I4 repository.

**D-3 verdict: RESOLVED** — and, as required, the real HTTP path that previously returned 500 now succeeds (§12).

## 11. D-4 — RLS / security provisioning: `RESOLVED` ✅

Verified **against the shipped migration's own output** (no diagnostic copy, no manual correction).

**Grants/revokes as provisioned:**

| Role | `interactions` | `tool_calls` |
|---|---|---|
| `anonymous` | **no grants at all** | **no grants at all** |
| `authenticated` | **SELECT, INSERT only** | **SELECT, INSERT only** |
| `service_role` | ALL | ALL |

Matching the shipped statements: `REVOKE ALL … FROM anon`, `GRANT SELECT, INSERT … TO authenticated`, `REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, MAINTAIN …`, `GRANT ALL … TO service_role`.

**Policies (active, creator-private, as provisioned):**

```
ci_interactions_creator_select  SELECT  TO authenticated
  using: is_org_member(organization_id) AND created_by = auth.uid()
ci_interactions_creator_insert  INSERT  TO authenticated
  with check: is_org_member(organization_id) AND created_by = auth.uid()
ci_tool_calls_creator_select    SELECT  TO authenticated
  using: is_org_member(organization_id) AND EXISTS (SELECT 1 FROM carbontally_insight_interactions i
         WHERE i.id = interaction_id AND i.organization_id = organization_id AND i.created_by = auth.uid())
ci_tool_calls_creator_insert    INSERT  TO authenticated
  with check: (same creator-private predicate)
```

**Live authorization/isolation matrix** (real `authenticated` role, real `request.jwt.claims`; **no application-layer filtering substituted** for RLS):

| # | Case | Expected | Observed |
|---|---|---|---|
| V1–V3 | creator reads own interaction / tool call; `auth.uid()` and `is_org_member` resolve | allowed | ✅ rows=1 / rows=1 / resolved |
| V4–V6 | **peer in the same organisation** reads creator's interaction / tool call; peer reads own | denied / denied / allowed | ✅ 0 rows / 0 rows / 1 row |
| V7 | **cross-organisation** user reads | denied | ✅ 0 rows |
| V8–V9 | **inactive organisation** member reads own; `is_org_member(inactive)` | denied | ✅ 0 rows; `false` |
| V10 | user with **no membership** | denied | ✅ 0 rows |
| V11 | creator INSERT own interaction | allowed | ✅ |
| V12 | INSERT with **forged `created_by`** | denied | ✅ `new row violates row-level security policy` |
| V13 | INSERT into a **non-member organisation** | denied | ✅ RLS violation |
| V14 | tool call for **own** interaction | allowed | ✅ |
| V15 | tool call for **another user's** interaction | denied | ✅ RLS violation |
| V16–V17 | `authenticated` UPDATE / DELETE | denied | ✅ `permission denied for table` (no grant) |
| V18–V19 | `anon` SELECT | denied | ✅ `permission denied` |

**Immutability / lifecycle at the database** (as `service_role`, i.e. the role the application actually uses — `bypassrls=true`, so the **trigger**, not RLS, is what protects evidence):

| # | Case | Expected | Observed |
|---|---|---|---|
| V20 | UPDATE a **terminal** interaction | denied | ✅ `terminal interaction evidence is immutable (I4 Q5)` |
| V21 | DELETE an interaction | denied | ✅ `is append-only (I4 Q5): DELETE is not permitted` |
| V22 | UPDATE a tool call | denied | ✅ `is append-only (I4 Q5): UPDATE is not permitted` |
| V23 | DELETE a tool call | denied | ✅ `is append-only (I4 Q5): DELETE is not permitted` |
| V24 | non-transition UPDATE on an `executing` row | denied | ✅ `lifecycle executing -> executing is not a forward transition` |
| V25 | backward transition `executing → received` | denied | ✅ not a forward transition |
| V26–V31 | immutable-column changes (`created_by`, `question_hash`) incl. combined with a forward transition | denied | ✅ `immutable interaction columns cannot change` |
| V27 | terminal lifecycle without `completed_at` | denied | ✅ `ci_interactions_completed_at_check` violated |
| V28/V32/V33 | legal forward completion with `completed_at` | allowed | ✅ persisted (`completed`, `no_data`, `completed_at` set) |
| V29 | second completion on a terminal row | denied | ✅ terminal-immutable |

Forward-only lifecycle and append-only enforcement are therefore both **genuinely enforced in the shipped state**, including against the application's own writer role.

**D-4 verdict: RESOLVED.** (D-4 was a consequence of D-1; with D-1 fixed, the unmodified migration provisions every intended control, and no control was redesigned.)

## 12. Real HTTP verification: `PASS` ✅

Driven with the real application factory, real route, real repository bundle, real PostgreSQL and real asyncpg; only `get_current_user` was overridden.

| # | Request | Observed |
|---|---|---|
| E2E-1 | `POST /api/v3/insight/interactions` (deterministic question with a tool) | **HTTP 201** (previously **500**) — `lifecycle=completed`, `answer_status=no_data`, `intent=report_lookup`, `intent_source=deterministic`, `narration_state=skipped`, `provider=null`, `tokens_used=null`, `cost=null` |
| E2E-2 | persisted state | interaction row completed; `question_hash` only (no raw text); tool-call row persisted with closed-catalogue tool name and I3 status; `audit_trail` row `insight.interaction.completed` with `record_id` and `metadata->>'correlation_id'` equal to the interaction id and `changes` carrying tool-call ids/statuses |
| E2E-3 | idempotent repeat with the same key | HTTP 201, **same interaction id**, `replayed=true`, `interactions=1`, `tool_calls` unchanged (no duplicates) |
| E2E-4 | read paths + refusals | creator list 200 (own rows); creator read-one 200; **peer read-one 404** (no existence disclosure); inactive org **403**; non-member org **403**; malformed body **422**; over-long question **422** |
| S1 | supported intent **without** an identifier | `needs_clarification`, `tool_calls=[]`, **no tool-call evidence written** — no scope guessed |
| S2 | real report id | `answer_status=success`, evidence persisted with a large non-empty `references` array |
| S3 | residue | no non-terminal residue from API-created rows |

The previous failure signature is gone: **no `ValueError`, no HTTP 500**, and the mapper path that raised it is the same path now exercised end to end.

## 13. Persistence / idempotency verification: `PASS` ✅

1. **create** — `create_interaction` returned a row with `metadata` decoded to `dict`; `mark_executing` persisted `executing`.
2. **repeat the same idempotent request** — `find_by_idempotency_key` returned the stored interaction; HTTP replay returned the same id with `replayed=true`; exactly one interaction row and no duplicate tool-call rows.
3. **create/read the tool call** — `record_tool_call` → `list_tool_calls`, values round-tripped; a repeat of the same logical call returned the **same row id** (no duplicate).
4. **complete the interaction** — a single `complete_interaction` persisted `completed` + `answer_status` + `completed_at`; a second completion was rejected by the database.
5. **read it back** — `get_interaction` returned `lifecycle=completed`, `answer_status=success`, `metadata={'layer': 2}`.

Recorded caveats (transparency): one non-terminal row and one empty `references` value appeared in my first E2E pass. Both were investigated to root cause and were **artifacts of my own probe**, not defects: the non-terminal row is my D-4 fixture (`V11`, no idempotency key, created 15:18:14) and **0 rows created by the HTTP run were non-terminal**; the empty `references` was my assertion treating asyncpg's jsonb-as-`str` as a `list` (the value was `'[]'` because that tool returned `no_data` — the non-empty case is covered in §9/S2). Both probe errors were corrected and re-run.

## 14. I1 / I2 / I3 regression: `PASS` ✅

| Contract | Result |
|---|---|
| I1 persistence semantics | ✅ unchanged; `backend/data/insight.py` byte-unchanged; I1 suites pass |
| I2 authorization | ✅ unchanged; `api/insight_authz.py` byte-unchanged; I2 contract suite passes; live refusals behave (E2E-4) |
| Four ratified I3 tools | ✅ unchanged (`report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup`); I3 suites pass; the DB `CHECK` still pins exactly these four |
| I3 `ToolStatus` | ✅ unchanged six-value vocabulary; file byte-unchanged; the DB `CHECK` still pins it |
| I3 reference semantics | ✅ unchanged (locators, never grants); the live suite stores locators only |

No I1/I2/I3 change was made by the remediation (see §17), and none is authorized.

## 15. Test results

| Run | Result | Comparison |
|---|---|---|
| Focused set (I4 remediation unit + I4 interactions/wiring/migration + I3 tools/wiring + I1 + I2 — 8 files) | **exit 0, no failures** (83 pre-existing + 7 new = 90 tests) | previously 83 exit 0; +7 from the new file only |
| `tests/unit/data/test_i4_repository_sql_and_jsonb.py` (new) | **7 passed** | matches Cline's 7 |
| `tests/integration/test_i4_live_migration_and_persistence.py` (new, live disposable DB) | **4 passed** | matches Cline's 4 |
| Full unit suite (`tests/unit`) | **4 failed, 2916 passed, 8 skipped** in 246s | **exactly matches the reported baseline `4 failed, 2916 passed, 8 skipped`**; +7 passed vs the previous round's 2909, explained entirely by the 7 new tests |
| Other integration suites (`test_v3m3_customer_factors`, `test_workflow`) | 3 failed | **identical failures at `b33f16c`** → pre-existing and unrelated |

The four full-suite failures are the known pre-existing set — 3 × `test_review_sla_surfaces.py` (lazy included-router; `_paths()` returns only `/api/v2/health`) and `test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged`. **No new failure appeared**, and the remediation added no migration file (so the D17 count assertion still sees 78 files, failing exactly as before). None was "fixed".

## 16. Test-sensitivity assessment — strong ✅

The decisive test of a regression suite is whether it fails on the defect it guards. I ran the two **new** suites against the **pre-remediation** tree (`git archive b33f16c` extracted to `/tmp/i4_prerev`, with only the new test files copied in; the repository was not modified):

| Suite | On pre-remediation code | On the remediation |
|---|---|---|
| `tests/unit/data/test_i4_repository_sql_and_jsonb.py` | **6 failures** (reserved-identifier guard, SQL-constant quoting, placeholder alignment, both jsonb text mappers, NULL/malformed references) | **7 passed** |
| `tests/integration/test_i4_live_migration_and_persistence.py` | **4 failures**, including `asyncpg.exceptions.PostgresSyntaxError: syntax error at or near "references"` and `data/insight_interactions.py:147: ValueError: dictionary update sequence element #0 has length 1; 2 is required` | **4 passed** |
| Direct `psql` of the pre-remediation migration | `ERROR: syntax error at or near "references"` (D-1 reproduced on the old artifact) | exit 0 |

So the new suites genuinely detect D-1, D-2 and D-3 (they fail on the old code with the exact original signatures and pass on the new code). Quality details confirmed by reading them:

* the live suite **executes the shipped migration** (`connection.execute(_MIGRATION.read_text())`) rather than inspecting SQL text, and asserts the provisioned controls;
* the live suite uses **real asyncpg + real PostgreSQL** for the repository round-trip, immutability and RLS;
* the unit suite feeds the real mappers asyncpg-style **text** jsonb (`json.dumps(...)`), i.e. it reproduces the actual driver type;
* the live suite is safety-gated: skips when `INSIGHT_RLS_TEST_DSN` is unset (verified: `ssss`, no fallback) and raises on a non-disposable DSN; each test runs in a transaction that is rolled back.

**Observation (non-blocking, §18 O-R1):** three of the four live tests require a **pre-migrated** database — on a genuinely fresh DB they error with `UndefinedTableError` because each test's transaction (including the one that applies the migration) is rolled back. They pass 4/4 against a migrated disposable DB. The suite therefore is not self-provisioning; its run instructions give only a DSN. This weakens standalone reproducibility but does not affect the sensitivity conclusion.

## 17. Changed-file / scope assessment: `PASS` ✅

`git diff --name-status b33f16c 310a62a` — **6 files, 685 insertions, 9 deletions**:

| File | Kind |
|---|---|
| `supabase/migrations/20261003000000_p8_i4_insight_interactions.sql` | modified — the D-1 quoting fix (+ comment), 4 lines |
| `backend/data/insight_interactions.py` | modified — D-2 quoting + D-3 `loads_jsonb` decoding, 19 lines |
| `backend/tests/unit/data/test_i4_repository_sql_and_jsonb.py` | new (164 lines) |
| `backend/tests/integration/test_i4_live_migration_and_persistence.py` | new (371 lines) |
| `docs/implementation/phase8/CT-P8-I4-INSIGHT-IMPLEMENTATION-20260921.md` | modified — additive §22 |
| `docs/implementation/phase8/CT-P8-I4-REMEDIATION-20260921.md` | new |

Explicitly confirmed **unchanged**:

| Surface | Evidence |
|---|---|
| `public.ai_content_history` (columns, indexes, constraints, RLS policies, grants) | 0 files changed; the only diff occurrences of the term are **prose claims** in Cline's report |
| Prisma model / `prisma/schema.prisma` | 0 files changed (the only mention is prose) |
| I1 implementation (`backend/data/insight.py`), I2 authorization (`api/insight_authz.py`) | 0 files changed |
| I3 domain/service/API (`domain/insight_tool.py`, `services/insight_tools.py`, `api/v3_insight_tools.py`) | 0 files changed |
| I3 `ToolStatus` | file unchanged |
| Canonical audit ledger (`domain/audit.py`, `data/audit.py`, `infra/audit_logger.py`, `audit_trail` DDL) | 0 files changed |
| I4 domain/service/API/dependencies/router | 0 files changed — remediation confined to the data layer + migration + tests |
| Migrations | only the existing I4 migration was **modified**; no migration was added or removed |
| Master Specification (`docs/architecture/`) | **0 files changed** |
| Personas, permissions, RAG, embeddings, vector/pgvector, LangChain, billing, retention/export, autonomous actions, I5–I8 | no code added; the single regex hit in the diff is prose in the remediation report asserting their absence |

The remediation is therefore correctly **bounded**: it changes exactly what D-1/D-2/D-3 require, plus regression tests, and touches nothing else.

## 18. Observations

**O-R1 (test quality, non-blocking).** Three of the four new live tests depend on a pre-migrated database: on a fresh disposable DB they fail with `asyncpg.exceptions.UndefinedTableError: relation "public.carbontally_insight_interactions" does not exist`, because the migration applied inside the first test is rolled back with that test's transaction. Reproduced: fresh `ct_i4_rv_integration` → 1 passed / 3 failed; migrated `ct_i4_reverify_20260921` → 4 passed. Suggested (for a future, separately authorized change): apply the migration in a session-scoped fixture, or document that the DSN must name a migrated disposable DB. Not a remediation defect; the sensitivity of the suite is unaffected.

**O-R2 (verifier-probe transparency).** Two apparent anomalies in my first E2E pass were my own probe's errors, not product defects: (a) a non-terminal interaction row — traced to my D-4 fixture `V11` (no idempotency key), with **0 rows from the HTTP run non-terminal**; (b) a `references` value that looked like a string — it *is* a string at the asyncpg layer (`'[]'`, the documented behaviour that motivated D-3), and my assertion was wrong, not the code.

**O-R3 (pre-existing failures, unchanged).** The four known full-suite failures and the three unrelated integration-suite failures are byte-identical in nature before and after the remediation (verified by running them against the pre-remediation tree). They remain out of scope per the mandate and were not touched.

**O-R4 (Cline limitation now closed).** Cline's report and implementation report §22.9 record "no live-DB HTTP round-trip" as a remaining limitation. This re-verification closes it: the real HTTP path against the real migrated database returns **201** and persists interaction, tool-call evidence and the canonical audit event (§12). No action needed from Cline.

**O-R5 (unchanged from the previous report).** Previous observations O-1…O-8 were not addressed by design and remain open: identical-subject commits (`d9bdfab`/`4c7175b`), `ON DELETE CASCADE` unreachable behind the append-only trigger, no audit trace for pre-audit failures, declared-but-unproduced answer states, `_paths()` unable to detect missing route registration, and the Q2–Q14 decision text not being a repository artefact. They are outside this remediation's scope.

## 19. Blockers

**None.** D-1, D-2, D-3 and D-4 are all independently resolved, and no equivalent or new blocking regression was reproduced.

| ID | Original defect | Status |
|---|---|---|
| D-1 | Migration unapplicable (reserved word) | **RESOLVED** — applies atomically, `exit 0`, complete schema |
| D-2 | Application SQL invalid (reserved word) | **RESOLVED** — INSERT/RETURNING + SELECT execute; round-trip intact |
| D-3 | JSONB mapped via `dict(str)` → HTTP 500 | **RESOLVED** — `loads_jsonb`; real HTTP returns 201 |
| D-4 | Controls not provisioned | **RESOLVED** — RLS, 4 creator-private policies, 2 append-only triggers, grants verified live |

## 20. Final verdict

```
PASS — I4 REMEDIATION D1-D4 VERIFIED
```

Every one of the four blockers was independently reproduced as a defect on the previous revision and independently confirmed fixed on `310a62a`, through the real migration, the real repository, the real HTTP route, real asyncpg and real PostgreSQL — not through source inspection or Cline's report:

* the **exact shipped migration applies atomically with zero errors** on PostgreSQL 17.6 and provisions both tables, RLS, the four creator-private policies, both append-only triggers and the intended grants, with all post-condition guards satisfied;
* the **application SQL executes** (INSERT + RETURNING and SELECT) and `"references"` round-trips, with a systematic audit confirming no residual reserved-word identifier remains;
* **JSONB decodes correctly** for objects, arrays, empty defaults, NULL and large reference arrays, and the real HTTP path that previously returned **500** now returns **201** with interaction, tool-call evidence and a correlated canonical audit event persisted;
* **creator-private RLS and append-only immutability are enforced at the database**, including against the application's own `service_role` writer, with peer/cross-organisation/inactive-organisation/no-membership/forged-identity/`anon` denial all verified;
* **no unrelated regression**: scope is bounded to 4 non-doc files, the full unit suite matches the known baseline exactly with no new failure, I1/I2/I3 contracts are untouched, and the new tests demonstrably fail on the pre-remediation code with the original error signatures.

**This result is ready for PO I4 closure consideration. I4 is not closed by this report; I5 is not authorized; the Master Specification was not modified; the remediation was not re-verified by modifying anything.**

---

**STOP.** No fix, no second remediation, no schema/RLS change, no commit amendment, no production contact. The only repository change is this report.
