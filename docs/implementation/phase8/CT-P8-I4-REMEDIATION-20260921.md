# CT-P8-I4-REMEDIATION-20260921

**Bounded remediation of the OHD I4 verification blockers D-1…D-4.**

| Item | Value |
| --- | --- |
| Starting HEAD | `b33f16c9248eda38661cc0ce57dfe20489fd5f87` |
| OHD report | `docs/implementation/phase8/CT-P8-I4-OHD-VERIFICATION-20260921.md` (commit `b33f16c`; verdict `FAIL — I4 IMPLEMENTATION NOT VERIFIED`) |
| Verified implementation under remediation | `d9bdfabbad52bb6117bf860b0c87f2c917458d1e` |
| Scope | D-1…D-4 only, plus regression coverage for those exact failures |
| **Final Cline verdict** | **`I4 REMEDIATION IMPLEMENTED — READY FOR OHD RE-VERIFICATION`** |

## 1. D-1 — migration reserved keyword (root cause and fix)

**Root cause:** `supabase/migrations/20261003000000_p8_i4_insight_interactions.sql` declared a column named `references` unquoted. `references` is a PostgreSQL reserved keyword, so the statement is a syntax error (`syntax error at or near "references"`), which aborted the migration after `carbontally_insight_interactions` had been created and before any of its controls were provisioned (hence D-4).

**Fix (smallest schema-safe correction):** the identifier is now consistently **quoted** as `"references"` in the shipped DDL, with a comment recording why. No column was renamed and no semantics changed: a quoted lowercase identifier is the same identifier, so nothing else in the schema, domain model or API moved.

## 2. D-2 — application SQL reserved keyword

**Root cause:** `_TOOL_CALL_COLUMNS` (used by every tool-call SELECT/RETURNING) and the `_RECORD_TOOL_CALL_SQL` INSERT column list used the bare word `references`, so both readback and persistence were invalid SQL.

**Fix:** both lists now use `"references"`; the placeholder order (`$9::jsonb`) is unchanged, and a regression test asserts the placeholder/column alignment so the quoting cannot drift again. Tool-reference semantics, allowlisted projections, hashes and the closed I3 contract are untouched.

## 3. D-3 — JSONB row mapping (HTTP 500)

**Root cause:** asyncpg returns `jsonb` as **text** in this repository's configuration; the new mappers coerced those strings with `dict(...)` (`ValueError: dictionary update sequence element #0 has length 1; 2 is required`), so every real interaction failed.

**Fix:** the mappers now decode through the project's established helper `data.base.loads_jsonb()` — the same helper ~57 existing repositories use — for `metadata`, `arguments`, `result_metadata` and `references`, preserving the `or {}` / `or []` NULL defaults, and reference items are filtered with `isinstance(x, dict)`. No parallel JSON mechanism was introduced and no other repository was modified.

## 4. D-4 — control provisioning verification

D-4 was a consequence of D-1 (the migration aborted before enablement/policies/triggers/grants). After the D-1 fix, the **unmodified shipped migration** was applied to a fresh disposable database and every intended control was confirmed present (see §6). No control was redesigned and no unrelated security change was made.

## 5. Files changed

| File | Change |
| --- | --- |
| `supabase/migrations/20261003000000_p8_i4_insight_interactions.sql` | D-1: quote `"references"` in the DDL (+ explanatory comment) |
| `backend/data/insight_interactions.py` | D-2: quote `"references"` in the SELECT and INSERT column lists. D-3: decode `metadata`/`arguments`/`result_metadata`/`references` via `loads_jsonb` (import added); guard reference items |
| `backend/tests/unit/data/test_i4_repository_sql_and_jsonb.py` | **New** — reserved-identifier guard for the migration and the SQL constants, placeholder/column alignment, and asyncpg-text JSONB mapper regressions (interaction + tool call, NULL and malformed cases) |
| `backend/tests/integration/test_i4_live_migration_and_persistence.py` | **New** — live regression on a disposable PostgreSQL: applies the shipped migration and asserts every control; real repository round-trip (create/mark/record/read/complete, idempotent tool call, `"references"` round-trip); append-only enforcement; live RLS smoke |
| `docs/implementation/phase8/CT-P8-I4-INSIGHT-IMPLEMENTATION-20260921.md` | Additive dated remediation section (§22) |
| `docs/implementation/phase8/CT-P8-I4-REMEDIATION-20260921.md` | This report |

No other file was changed: `public.ai_content_history` (columns, indexes, constraints, grants, RLS, Prisma model), I1/I2 authorization, the I3 catalogue and `ToolStatus`, the canonical audit ledger, and every unrelated schema/application file are untouched.

## 6. Disposable-database migration result

```text
$ psql -h 127.0.0.1 -p 54426 -U postgres -c 'CREATE DATABASE ct_i4_remediate_20260921 TEMPLATE ct_i2_verify_20260921'
CREATE DATABASE
$ psql -h 127.0.0.1 -p 54426 -U postgres -1 -v ON_ERROR_STOP=1 -d ct_i4_remediate_20260921 \
      -f supabase/migrations/20261003000000_p8_i4_insight_interactions.sql
COMMENT / COMMENT / COMMENT / DO      -> apply_exit=0 (applied atomically, no error)
```

Post-conditions verified on PostgreSQL 17.6:

| Control | Result |
| --- | --- |
| `carbontally_insight_interactions` / `_tool_calls` exist | ✅ both present |
| RLS enabled | ✅ `carbontally_insight_conversations:true`, `_messages:true`, `_interactions:true`, `_tool_calls:true` |
| Policies | ✅ 8 `carbontally_insight*` policies (4 I4 creator-private + 4 I1) |
| Append-only triggers | ✅ `ci_interactions_immutable`, `ci_tool_calls_immutable` |
| Grants | ✅ `authenticated` = `INSERT,SELECT` only (no UPDATE/DELETE) |
| `"references"` column | ✅ present in `information_schema.columns` |
| Post-condition guards | ✅ passed (migration completed) |

## 7. Live persistence / JSONB / RLS / immutability result

`INSIGHT_RLS_TEST_DSN=postgresql://postgres:postgres@127.0.0.1:54426/ct_i4_remediate_20260921 pytest tests/integration/test_i4_live_migration_and_persistence.py -q` → **4 passed**

* interaction create → `metadata` decoded to `{}` (not a string) → `mark_executing`;
* tool-call insert with `"references"` → idempotent repeat returned the **same** row id → `list_tool_calls` returned the reference locator unchanged (round-trip);
* `complete_interaction` → creator-scoped readback with `metadata == {"contract_version": "i4-layer2-v1"}`;
* immutability: UPDATE/DELETE on a terminal interaction and UPDATE/DELETE on a tool call were all **rejected by the database**;
* RLS smoke: creator allowed; peer denied; forged `created_by` insert denied; anonymous read denied.

## 8. Regression suites

| Suite | Result |
| --- | --- |
| `tests/integration/test_i4_live_migration_and_persistence.py` (live, disposable DB) | **4 passed** |
| `tests/unit/data/test_i4_repository_sql_and_jsonb.py` (D-1/D-2/D-3 guards) | **7 passed** |
| Live + unit regression together | **11 passed, exit 0** |

These regressions fail on the pre-remediation implementation: the migration guard rejects an unquoted reserved identifier, and the mapper tests feed asyncpg-style **text** jsonb (which raised `ValueError` before the fix).

## 9. I3 regression

`tests/unit/api/test_v3_insight_i3_tools.py` and `tests/unit/api/test_v3_insight_i3_wiring.py` pass unchanged; the four-tool catalogue, the six-point contract and the `ToolStatus` vocabulary were not modified (I2 authorization and I1 persistence suites also pass unchanged).

## 10. Remaining limitations

* Independent verification is still outstanding — this is Cline's remediation, not verification.
* The live suite requires `INSIGHT_RLS_TEST_DSN` naming a **disposable** database and skips otherwise (by design); it was executed here against `ct_i4_remediate_20260921`.
* The live suite covers migration application, repository persistence, immutability and RLS directly. It does not drive the HTTP route through the live database (the I4 HTTP path remains covered by the in-memory orchestration suite, which now sits on top of a mapper layer proven against real asyncpg types by §7).
* OHD observations O-1…O-8 were **not** addressed (out of scope for this bounded remediation).
* `zero`, `tool_failure`, `rate_limited`, `ungrounded` and `insufficient_data` remain declared-but-unproduced I4 answer states.

## 11. Scope confirmation

No production system was touched; no other checkout (`carbon_tally`, `carbon_tally_p8_release`) was modified; `public.ai_content_history` and its four RLS policies and Prisma model are unchanged (Q1 Option C preserved); no new tool, persona, permission, audit table, RAG/embedding/vector component, billing, retention/export or autonomous action was introduced; I5–I8 remain unimplemented and NOT AUTHORIZED.
