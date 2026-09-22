# CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-OHD-VERIFICATION-20260922

**Verification ID:** OHD-INS-01-20260922
**Task type:** INDEPENDENT VERIFICATION (OHD) — read-only. No implementation, fix, migration, test, configuration or architectural change was made.
**Repository:** `/home/shomonrobie/ct_93d5cdd` (authoritative checkout; no branch switch, no other checkout)
**Branch / remote:** `p8-release-reconciled` → `github` (`https://github.com/shomonrobie/CarbonTally.git`)
**Authority for this verification:** PO *INS-01: Insight Discovery, Aggregation, Provenance, Shared Evidence & Rate Limiting* independent-verification authorization (2026-09-22).
**Verdict:** **PASS WITH NON-BLOCKING OBSERVATIONS** — see §23.

---

## 1. Exact verification target

| Item | Value | Verified |
| --- | --- | --- |
| Preflight | `c7cd9cc2ff56e288c830bb5d204118a06aa31104` — `docs(p8): preflight Insight discovery aggregation foundation` | `git cat-file -t` → `commit` ✓ |
| Implementation | `e4ea3254c6a709df0e9cedcd8c719515363b4358` — `feat(p8): bounded Insight discovery, aggregation, provenance and execution rate limiting` | exists ✓; parent is exactly the preflight commit ✓; 14 files, **+2,348 / −135** |
| Final / report commit | `cbc529dd8974d3ec16595fc5c6981c5217b43c24` — `docs(p8): bounded Insight discovery, aggregation, provenance and rate-limiting implementation report` | exists ✓; **equals HEAD** ✓ |
| Permanent implementation report | `docs/architecture/CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-IMPLEMENTATION-20260922.md` | exists ✓, 244 lines, **read in full** ✓ |

The implementation commit carries the production change; the final commit carries the tests, the test fakes and the report. Both were verified together, since the tests live in the final commit and HEAD contains both.

## 2. Starting and ending Git state

**Starting state (before any verification action):**

| Check | Observed |
| --- | --- |
| Checkout | `/home/shomonrobie/ct_93d5cdd` ✓ |
| Branch | `p8-release-reconciled` ✓ |
| Remote | `github` = `https://github.com/shomonrobie/CarbonTally.git` ✓ (a local-path `origin` = `/tmp/ct_step2` also exists; it was not used) |
| `git rev-parse HEAD` | `cbc529dd8974d3ec16595fc5c6981c5217b43c24` ✓ = expected final commit |
| `git status --short` | only untracked PO/ChatGPT documents — 5 at start, 7 by the end; **no tracked-file modification** |
| `git rev-list --left-right --count HEAD...github/p8-release-reconciled` | `0	0` ✓ aligned |

**Ending state (before this report was written):** HEAD unchanged at `cbc529dd…`; branch unchanged; working tree still contains **only** untracked PO/ChatGPT documents; `git stash list` empty.

Untracked documents (known PO/ChatGPT artefacts, **not** created by this verification): `docs/ChatGPT/CarbonTally_Incremental_ChatGPT_PO_History_2026-09-22.md`, `docs/ChatGPT/CarbonTally_Incremental_Chat_History_2026-09-22.md`, `docs/ChatGPT/CarbonTally_Incremental_Chat_History_2026-09-22-Insight-Strategy-v2.md`, `docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22.md`, `docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22-v2.md`, `docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md`, `docs/architecture/CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md`. Two of them (`…Insight-Strategy-v2.md`, `…Architecture_Reference_2026-09-22-v2.md`) appeared during the verification window; they are PO-authored documents. **No verifier artefact was written inside the repository** except this report.

All verification execution happened either read-only in the checkout, or in throw-away copies under `/tmp` (`/tmp/ct_baseline`, extracted with `git archive`, so the checkout's `.git` was never written).

## 3. Environment

| Item | Value |
| --- | --- |
| OS / shell | Linux, bash |
| Backend runtime | `/home/shomonrobie/ct_93d5cdd/backend/.venv` (CPython 3.14), `pytest` |
| Frontend test runner | CRA `react-scripts test` (Jest) with `CI=true`, `--watchAll=false` |
| Verifier probe language | Python (asyncpg) from the repository's own virtualenv; no new dependency installed |
| Verifier probe locations | `/tmp/ohd_db_verify.sh`, `/tmp/ohd_concurrency_probe.py`, `/tmp/ohd_planner_probe.py`, `/tmp/ct_baseline/` |

No dependency was added or upgraded; `backend/pyproject.toml` and `frontend/package.json` are not in the implementation diff.

## 4. Database environment (disposable, isolated)

| Item | Value |
| --- | --- |
| Engine | PostgreSQL **17.6** (`x86_64-pc-linux-gnu`) |
| Image | `public.ecr.aws/supabase/postgres:17.6.1.159` (the Supabase platform image, so the real Supabase roles/schemas exist: `anon`, `authenticated`, `service_role`, `supabase_admin`; schemas `auth`, `extensions`, `storage`, `graphql`, `vault`) |
| Host/port | `localhost:55432` → container port 5432 |
| Container | `ohd_ins01_pg` (created for this verification, **removed afterwards**) |
| Database used | the container's own `postgres` database — itself disposable; no persistent CarbonTally database was touched |
| Local cluster | a host cluster (PostgreSQL 18, port 5432) is running; the verifier **did not use it** (no credentials) and pointed nothing at it |

**Isolation statement (F-046-1 respected):** the destructive/integration verification ran **only** against the container. The host cluster was never addressed by any statement, and the container was destroyed at the end of the verification.

## 5. Migration execution result — executed live

Applied file: `supabase/migrations/20261005000000_p8_insight_discovery_aggregation_rate_limit.sql` (126 lines).

### 5.1 Application within the real chain

All 79 tracked `.sql` migrations were applied **in filename order** to a pristine disposable database:

* **78 applied cleanly**, including the migration under verification.
* **1 failed: `20260823000000_d32_private_documents_storage.sql`** — `relation "storage.buckets" does not exist`. This is an environment prerequisite of that *older, unrelated* migration (the `storage.buckets` table is created by the Supabase Storage service, not by SQL migrations); the failure occurs **before** the verified migration and does not affect it. Recorded as an environment fact, not as a defect of this package.

### 5.2 Schema verification — 75/75 checks passed

Run with `ON_ERROR_STOP=1` against the pristine database (script: `/tmp/ohd_db_verify.sh`; output: `/tmp/ohd_db_clean2.txt`). The verifier's fixtures were corrected three times during development (invalid UUID construction and two fixture-key collisions); the final run is a clean first run: **75 passing checks, 0 failures.**

| Requirement | Observed evidence |
| --- | --- |
| Applies cleanly | exit 0 as part of the chain; exit 0 standalone |
| **Idempotent** (claimed) | 2nd application exit 0; **3rd** application exit 0 |
| No destructive statement | static: no `DROP TABLE`, `DROP COLUMN`, `DELETE`, `TRUNCATE`, `UPDATE public.…`, `DROP SCHEMA`; only `DROP CONSTRAINT IF EXISTS` (the intended in-place widening). Runtime: `pg_tables` count in `public` **unchanged (141)**; relation OIDs of the four relevant tables **unchanged** → nothing was dropped or recreated |
| Existing values remain valid | a pre-existing `answer_status='success'` interaction row and a pre-existing `tool_name='report_lookup'` tool-call row were inserted **before** re-application and **survived** both re-applications |
| I3 tool CHECK contains exactly the seven authorized names | `ci_tool_calls_tool_name_check` = exactly **7** values: `report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup`, `insight_discovery`, `insight_aggregation`, `insight_aggregate_provenance` |
| I3 status vocabulary untouched | `ci_tool_calls_tool_status_check` still the original **six** values (`success`, `no_data`, `not_authorized`, `invalid_input`, `provider_unavailable`, `error`) |
| I4 answer state CHECK contains `multiple_matches` | `ci_interactions_answer_status_check` = exactly **15** values = the 14 Master Spec §14 states + `multiple_matches`; nothing else added |
| `NULL` answer_status still permitted | insert with `answer_status = NULL` accepted (unchanged behaviour) |
| Both new tables exist | `insight_rate_limit_buckets`, `insight_concurrency_leases` |
| Expected indexes/constraints exist | each table: 1 primary key on `(scope, scope_key)`, a `scope IN ('user','org')` CHECK, 4 bucket CHECKs / 3 lease CHECKs, and the expected `*_idx` index on `updated_at` / `lease_expires_at` |
| RLS enabled | `relrowsecurity = true` on both new tables |
| **No unintended RLS policy** | `pg_policies` count for both new tables = **0** (service-role only) — and the migration contains no policy statement and no change to any existing table's RLS |
| Constraint enforcement (live) | accepted the 7 authorized tool names and all 15 authorized answer states; **refused** `insight_search`, `query_anything`, `report_lookup_x`, `INSIGHT_DISCOVERY`, `insight_discovery_extra`, `calculation_snapshot`; **refused** `multiple_match`, `multiple_matches_x`, `SUCCESS`, `unknown_state`; **refused** invalid limiter rows (`scope='global'`, `scope='team'`, `capacity=0`, `refill_per_second=0`, `denied_count=-1`, `in_flight=-1`, `max_concurrent=0`) and a duplicate `(scope, scope_key)` |

## 6. I3 verification

**Catalogue — exactly seven tools.** Seven `ToolDefinition` entries and seven `name=TOOL_*` entries exist (`services/insight_tools.py`): the four ratified (`report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup`) plus the three authorized analytics tools. Names are exact; the DB CHECK (verified live, §5.2) enforces the same closed set at the persistence boundary.

| Tool | Input | Output allowlist | Reference kinds | Auth |
| --- | --- | --- | --- | --- |
| `insight_discovery` | optional `DISCOVERY_FILTERS` + `limit` | `match_count`, `match_count_capped`, `candidates`, `basis` | `calculation_snapshot`, `evidence_line_item` | `i2-boundary: authorize_insight_scope + organisation-scoped query` |
| `insight_aggregation` | required `group_by`, `start_date`, `end_date`; optional `limit` | `group_by`, `period`, `groups`, `group_count`, `groups_truncated`, `row_count`, `total_co2e_kg`, `total_is_complete`, `basis`, `provenance_tool` | — (an aggregate is a total, not a record) | same |
| `insight_aggregate_provenance` | required `group_by`, `group_key`, `start_date`, `end_date`; optional `limit` | `group_by`, `group_key`, `period`, `snapshots`, `snapshot_count`, `snapshot_count_capped`, `basis` | `calculation_snapshot`, `evidence_line_item` | same |

All three declare `read_only=True`.

* **The four ratified tools are unchanged.** `domain/insight_tool.py` (the I3 contract: `ToolStatus`, `REFERENCE_KINDS`, reference validation) is **not in the implementation diff at all**. `services/insight_tools.py` shows **exactly one deletion** in the whole diff:
  `- if not tool.input.required:` → `+ if tool.name == TOOL_REPORT_VERSION_LOOKUP:`
  i.e. the legacy "no declared required inputs ⇒ demand a version identifier" branch is now scoped to the one tool it was written for. The other three ratified tools declare required inputs, so that branch never applied to them and their validation path is byte-identical.
* **`ToolStatus` still has the original six values** — verified in source and in the live DB CHECK (§5.2). There is no `multiple_matches` tool status.
* **`REFERENCE_KINDS` still has exactly four kinds** (`report`, `report_version`, `evidence_line_item`, `calculation_snapshot`); the analytics tools reuse two of them and introduced none.
* **No arbitrary tool name is accepted.** Dispatch is a closed `if tool.name == …` chain; anything else returns `ToolStatus.INVALID_INPUT` with `reason="unratified_tool"`. The registry is built from the fixed definition tuple.
* **No arbitrary query parameter is accepted.** `domain/insight_query.validate_*` rejects unknown parameters before any repository call; the persistence projection (`TOOL_ARGUMENT_ALLOWLIST`) lists **typed parameters only** for the three tools (`insight_discovery`: the 13 declared filters/limit; `insight_aggregation`: `group_by`, `start_date`, `end_date`, `limit`; `insight_aggregate_provenance`: `group_by`, `group_key`, `start_date`, `end_date`, `limit`) — no free text is persisted for the new tools.
* **I2 remains the governing boundary:** every invocation resolves scope through `api.insight_authz.authorize_insight_scope`; the handlers bind the repository to `org = access.organization_id` (`services/insight_tools.py:494` discovery, `:550` aggregation, `:622` provenance) — never to a request-supplied organisation.

## 7. I4 verification

* **`multiple_matches` is the only newly introduced answer state.** Live DB CHECK: exactly 15 values (§5.2); `AnswerStatus.MULTIPLE_MATCHES = "multiple_matches"` added; the frontend vocabulary is "fourteen + one".
* **It is not converted into `success`, and no candidate is chosen.** `insight_discovery` returns `ToolStatus.SUCCESS` with `reason="multiple_matches"` **plus** the bounded candidate list and a capped `match_count`; the interaction-level state becomes `MULTIPLE_MATCHES`. Nothing in the code path selects, ranks or prefers a candidate, and no LLM call receives the ambiguous candidate set (§ narration below), so no model can rank or select.
* **Reason → state mappings (observed in `services/insight_interactions.py:115–119`)** — `multiple_matches` → `MULTIPLE_MATCHES`; `zero_total` → `ZERO`; `amount_tolerance_required` → `NEEDS_CLARIFICATION`. All three reasons are emitted **only together with `ToolStatus.SUCCESS`** (`services/insight_tools.py:521` and `:590`; the tolerance reason is a validation reason on the invalid-input path and is mapped to `NEEDS_CLARIFICATION` as authorized), so the override cannot convert a failing call into a success-family state.
* **Precedence cannot mask a failure or security state.** `_ANSWER_ORDER` (`domain/insight_interaction.py:153`) is `ERROR, NOT_AUTHORIZED, INVALID_INPUT, RATE_LIMITED, REFUSED, MULTIPLE_MATCHES, TOOL_FAILURE, PARTIAL, NO_DATA, SUCCESS`. Every security/failure state ranks **above** `MULTIPLE_MATCHES`; a mixed interaction therefore still reports the security state. Verified by reading the combination function and by the passing I4 suites.
* **Narration is suppressed for ambiguity:** the narration gate requires `str(result.status) == "success"` **and** `deterministic_status is not AnswerStatus.MULTIPLE_MATCHES` (`services/insight_interactions.py:545–550`), so an ambiguous set is never submitted to the provider.
* **Q6 discipline preserved:** the three tools' argument allowlists were **added to**, not loosened; `RESULT_METADATA_ALLOWLIST` gains only `match_count` (a bounded count, not record content).
* **Lifecycle is truthful:** a bucket refusal is raised as `429` **before** any Layer-1/Layer-2 write; a concurrency refusal is persisted as `lifecycle=failed` + `answer_status=rate_limited` + `error_class=concurrency_limit` with a canonical audit event (`insight.interaction.failed`) and then answered `429`.

## 8. Discovery verification

**Dimensions implemented** (closed, all positional): date, date range, reporting year, CO₂e amount, absolute tolerance, relative tolerance, activity, scope, supplier, facility, asset — confirmed in the filter builder and the tool's declared input.

**Judge-read evidence from the builder (`data/emissions_logs.py::_snapshot_filter_clause`)**

* Date / range: `s.date >= $n`, `s.date <= $n` (inclusive; a single day is a one-day range).
* Reporting year: its own predicate `s.reporting_year = $n` (not derived from the date range).
* Amount: `s.co2e_kg >= $n AND s.co2e_kg <= $n` from `resolve_amount_bounds(filters)` — an exact match is a zero-width range, a stated tolerance a symmetric range.
* Activity: `s.activity_type ILIKE $n` with the operand built by `_containment_pattern()` (`%`/`_`/`\` escaped) — literal containment, never a wildcard pattern.
* Scope: `s.scope = $n` after `canonical_scope()` normalisation.
* Supplier: `EXISTS (SELECT 1 FROM public.emissions_logs l WHERE l.snapshot_id = s.id AND l.supplier_id::text = $n)`.
* Facility: `EXISTS (… WHERE l.snapshot_id = s.id AND l.metadata->>'facility_id' = $n)`.
* Asset: `EXISTS (… WHERE l.snapshot_id = s.id AND l.asset_id::text = $n)`.
* **No inferred relationship:** all three log-level dimensions use the deterministic lineage `emissions_logs.snapshot_id = calculation_snapshots.id` via `EXISTS` (never a join that could fan out, never a proximity/name guess).
* **No arbitrary SQL:** fixed literals + positional parameters only; string interpolation is limited to `$index` numbers.
* **Empty filter set raises** `ValueError("discovery filters must contain at least one predicate")` — an organisation-wide scan cannot be requested.
* **Bounded:** `MAX_DISCOVERY_RESULTS = 25`; `LIMIT ${len(params)+2}`, and the count is fetched with `LIMIT $cap` inside a subquery (capped work, never a full count).
* **Deterministic:** `ORDER BY s.date DESC, s.id ASC` in both the page query and the count.
* **Outcomes** (observed in the handler): 0 → `ToolStatus.NO_DATA` `reason="no_matches"`; 1 → success; >1 or capped → success + `reason="multiple_matches"` with `truncated` set.

**Test evidence:** `tests/unit/api/test_p8_insight_discovery.py` — **26 passed** (independently re-run, matching the report's 26), covering zero/one/multiple, capped count, exact amount, absolute and relative tolerance, approximate-without-tolerance refusal, each dimension, invalid scope, negative amount, conflicting tolerances, unsupported/unknown parameters, empty filter set, over-limit and over-long period, cross-tenant denial and determinism.

## 9. Aggregation verification

* **Seven authorized dimensions**: `scope`, `month`, `year`, `activity`, `supplier`, `facility`, `asset` — resolved through `_analytics_expression(dimension)` from a closed map, so an unsupported dimension raises before any query.
* **Basis**: `SUM(l.calculated_kg_co2e)` (kg CO₂e), the same column the existing emissions aggregates use, restated as `basis` in every result.
* **Bounded**: `MAX_AGGREGATE_GROUPS = 50`; the query fetches one extra row to **detect** truncation instead of assuming it; `groups_truncated` and `total_is_complete=false` are set from the observed extra row, so a truncated group list never presents a complete total.
* **Ordering**: `ORDER BY co2e_kg DESC, group_key ASC` (deterministic).
* **Period**: explicit and bounded to `MAX_PERIOD_DAYS = 3_660` (10 years); inverted/over-long periods are refused by validation before any query.
* **Empty vs zero**: 0 rows in period → `NO_DATA` `reason="no_rows_in_period"`; rows present with total exactly 0 → `SUCCESS` `reason="zero_total"` → I4 `zero`. The two are never conflated (both branches read directly in the handler).
* **No mixed-unit quantity sum** is exposed anywhere (CO₂e and row counts only) — a deliberate, documented limitation.
* **Labels**: resolved by one bounded, organisation-scoped lookup (`WHERE t.organization_id = $1 AND t.<key>::text = ANY($2::text[])`) limited to the keys actually returned, from the closed `_ANALYTICS_LABEL_SOURCES` map; an unresolvable key simply has no label, and `'none'` is the explicit unassigned bucket.
* **Organisation scoping**: `WHERE l.organization_id = $1`, and the dimension join (when used) carries `cs.organization_id = $1` on both sides.
* **Test evidence:** `tests/unit/api/test_p8_insight_aggregation.py` — **32 passed** (independently re-run, matching the report), covering every authorized dimension, empty period, zero total, the 50-group boundary, truncation honesty, deterministic ordering, invalid dimension/parameter, inverted and over-long periods, mixed-unit safety and cross-tenant denial.

## 10. Aggregate → calculation provenance verification

`insight_aggregate_provenance` was verified independently at the query level and by its suite.

| Requirement | Observed |
| --- | --- |
| Maximum 100 snapshot references | `MAX_PROVENANCE_SNAPSHOTS = 100`; `LIMIT $5`; the count is fetched `LIMIT $cap` in a subquery |
| Truncation reported | count fetched with `limit + 1`; a larger set yields `snapshot_count_capped=true` **and** `truncated=true` |
| Deterministic ordering | `ORDER BY cs.date DESC, l.snapshot_id ASC`, `SELECT DISTINCT l.snapshot_id` |
| Organisation predicates on **both** sides | `JOIN public.calculation_snapshots cs ON cs.id = l.snapshot_id AND cs.organization_id = $1` **and** `WHERE l.organization_id = $1` |
| Only authoritative snapshot-linked records | `JOIN` (not `LEFT JOIN`) plus `AND l.snapshot_id IS NOT NULL` |
| Identifiers bounded; no raw content | returned columns are exactly `id, date, activity_type, scope, co2e_kg, source_line_item_id` — no source file/page, no storage path, no signed URL, no actor, no document body |
| Valid aggregate cell / no contributors / 1 contributor / many / >100 / tenant isolation / invalid group, dimension, period | covered by the 32-test suite; empty results are `no_data`, not a fabricated cell |
| Handoff to the existing calculation/evidence architecture | the rows carry the **existing** `calculation_snapshot` and `evidence_line_item` reference kinds, so the ratified `calculation_snapshot_lookup` path and the shared `/evidence/line-items/{id}` viewer path resolve them unchanged; the aggregation result also names `provenance_tool` so a number can always be traced |

## 11. Shared Source Evidence Viewer verification

| Requirement | Observed evidence |
| --- | --- |
| Reuses the existing viewer | The implementation diff contains **no** frontend viewer/route/component file: the only frontend changes are `frontend/src/v3/insight/answerStates.js` and its test. No new evidence route, no Insight-only viewer, no second evidence architecture. |
| Does not bypass DM-6 / weaken signed URLs / bypass audit | No file under the evidence/document/viewer paths is in the diff; the only backend API file touched is `api/v3_insight_tools.py` (limiter wiring) — `api/v3_evidence.py` and the evidence services are untouched. |
| Does not expose raw source content to the LLM | The analytics outputs contain identifiers, dates, scope, activity, CO₂e and line-item ids only; narration receives the declared tool output (caps unchanged) and is additionally suppressed for ambiguity. |
| Navigation chain | Insight result → existing reference kinds → existing resolution: `calculation_snapshot` via the ratified `calculation_snapshot_lookup` ("View calculation"), `evidence_line_item` via the shared viewer path `/evidence/line-items/{id}` with DM-6 depth and `evidence.line_access` audit unchanged. Reference **resolution** happens only when the user follows the link; the LLM never receives it. |
| Reference kinds are the already-authorized kinds | `REFERENCE_KINDS` unchanged (four kinds); the new tools emit only `calculation_snapshot` / `evidence_line_item`. |

**No new viewer route, permission, RLS rule or evidence architecture was introduced.** This is verified both by the diff footprint and by the live database state (no policy added anywhere; §5.2).

## 12. Query-planner verification (`backend/services/insight_query_planner.py`)

* **Imports**: `re`, `datetime.date`, `decimal`, `typing`, and `domain.insight_query` only. No `asyncpg`, no repository, no provider/LLM client, no authorization module. Every function is a synchronous `def` — it structurally cannot await a database or a provider call.
* **Deterministic regex parsing**, four outcomes: `planned`, `clarification` (`period_required`, `group_key_required`, `amount_tolerance_required`), `invalid`, `unsupported` (which falls through to the pre-existing keyword classifier, so no previously working question changed meaning).
* **Closed output schema**: `{status, tool, tool_input, operation, reason}` with `tool` restricted to the three authorized names.
* **Independent escape probe** (`/tmp/ohd_planner_probe.py`): 16 adversarial inputs (SQL injection, `DROP TABLE`, prompt-injection aimed at changing `organization_id`, `group by organization_id`, a 200-year period, empty/NUL/whitespace input, scope 9, approximate amount without tolerance) produced **no schema escape**: every result kept the closed outer keys, a closed tool name, and only closed parameter names. My probe initially flagged the provenance plan's `group_key`; that flag was a **probe artifact** (my vocabulary discovery missed it) — `group_key` is an authorized provenance parameter, declared as required in the tool's `ToolInputSpec`. Source scan for `organization_id`, `org_id`, `repository`, `asyncpg`, `await`, `authorize`, `user_id`: **none present**.
* **Advisory only**: the tool re-validates every parameter against `domain.insight_query` before reading a row, and I2 decides authorization — so a planner mistake cannot create an unauthorized read.
* **Independent test evidence**: `tests/unit/services/test_insight_query_planner.py` — **31 passed** (matches the report).

## 13. Rate-limit code and semantics verification

**Configuration is server-side and bounded** (`services/insight_rate_limit.py`, read in full):

| Scope | Sustained | Burst | Capacity | Max concurrent | Safety ceiling |
| --- | --- | --- | --- | --- | --- |
| User | 20/min | 5 | **25** (= rate + burst) | **2** | (600, 100, 20) |
| Organisation | 100/min | 20 | **120** | **10** | (6 000, 1 000, 100) |

These match the PO's expected defaults exactly. Values come only from `CARBONTALLY_INSIGHT_RATE_LIMIT_*` environment variables; a non-integer or out-of-range value logs a warning and falls back to the ratified default; `…_ENABLED=0/false/no/off` disables with a warning. **No request field participates in any decision**, so a client cannot raise its own limit.

**Ordering and truthfulness:**

* `check_request_rates()` evaluates the **user** bucket first and returns immediately on a user denial — so a user refusal consumes **no** organisation token while the organisation ceiling still holds when many users act at once (confirmed live, §14.E).
* `acquire_execution_leases()` acquires the user slot then the org slot and, if the org slot is refused, **releases the user slot it already holds** before reporting the refusal — no leaked lease.
* `Retry-After` is computed from the bucket's own `tokens`/`refill_per_second`, clamped to `1..120 s`; `refusal_headers()` also sets `X-RateLimit-Remaining: 0` and `X-RateLimit-Reset`; admitted requests receive informational `X-RateLimit-*` headers.
* `rate_limited_error()` returns a truthful `429` ("limit reached for your account / your organisation") — never a fabricated answer state.
* Denial accounting (`record_denial`) is wrapped so an accounting failure can never decide access, and it deliberately does **not** touch `updated_at` (the refill basis) — confirmed live (§14.F).

**Refusal semantics:**

* **Bucket refusal** → `429` raised **before** the Layer-1 message write, before `mark_executing`, before any tool execution or provider call (`services/insight_interactions.py:356` precedes both at `:366` and the tool loop). No Layer-2 interaction row is created; observability remains via the bucket counters (`denied_count`, `last_denied_at`) and a hashed-key log line. This matches the PO's expectation ("no unnecessary Layer-2 interaction row", "no audit flooding").
* **Concurrency refusal** → for the interaction path a Layer-2 record already exists, so it is completed truthfully: `lifecycle=failed`, `answer_status=rate_limited`, `error_class=concurrency_limit`, narration `skipped`, plus the canonical `insight.interaction.failed` audit event, and then `429`. For the tool-invoke path there is no Layer-2 record, so it is a plain `429` with the same headers.
* **Leases are released on every exit path** (`try/finally` in `api/v3_insight_tools.py:101` and `services/insight_interactions.py:611`), with the 120 s expiry as a second safety net.

**No commercial meaning.** The module, the repository and the migration carry no plan, entitlement, credit, overage, quota, subscription or payment concept; the migration comment states the tables must never be reused as a billing signal. A scope-boundary scan of the whole diff found only comment/docstring matches for those words (§20).

**Route coverage (anti-bypass).** There are exactly two customer-facing execution paths, and both carry the limiter:

| Route | Limiter | Evidence |
| --- | --- | --- |
| `POST /api/v3/insight/interactions` | yes | `services/insight_interactions.py:356` (bucket), `:412` (leases), `:611` (release) |
| `POST /api/v3/insight/tools/invoke` | yes | `api/v3_insight_tools.py:69` (bucket), `:76` (leases), `:101` (release in `finally`) |

Every `invoke_tool` call site in the codebase is inside one of those two paths — there is **no third execution route**. The other `POST` routes are not execution routes and correctly carry no limiter: `POST /api/v3/insight/tools/intent` is pure deterministic classification (no DB, no provider, no tool call), and `POST /api/v3/insight/conversations/{id}/messages` persists one human-authored message only (it rejects non-human roles with 422 and executes nothing). The read-only `GET` routes execute nothing.

## 14. Concurrency verification — live PostgreSQL, 30/30 checks passed

Because the implementation report explicitly disclosed that its SQL was never executed, this area was verified against the disposable database by driving the **real production repository class** (`data.insight_rate_limit.InsightRateLimitRepository`) through a real asyncpg pool (`/tmp/ohd_concurrency_probe.py`). Refill was set to a negligible rate for the deterministic races and to a real rate where refill itself was under test.

| # | Check | Observed result |
| --- | --- | --- |
| A1 | final allowance cannot be consumed twice | capacity 1, **20 concurrent** workers → **exactly 1** admitted |
| A2 | tokens never negative | stored `tokens = 0.0000` |
| A3 | capacity 5 | **40 concurrent** → exactly 5 admitted |
| A4 | ratified user capacity 25 | **120 concurrent** → exactly 25 admitted |
| A5 | no token duplication | all 25 admitted workers received **distinct** remaining-token values |
| A6 | ratified org capacity 120 | **200 concurrent** → exactly 120 admitted |
| B1–B5 | refill correctness | capacity 2: two spends, third refused, after ≈3 s at 1 token/s admitted again (tokens=1.0), refill never exceeds capacity, idle bucket admits exactly the 25-token burst then refuses |
| C1 | concurrency lease ceiling | max 2, **10 concurrent** acquires → exactly 2 succeed |
| C2 | stored in-flight correct | `in_flight = 2` (exactly the ceiling) |
| C3 | refusal at the ceiling | further acquire returns `False` |
| C4 | release on normal completion | `in_flight 2 → 1` |
| C5 | released slot reusable | next acquire succeeds |
| C6 | release idempotent | 5 extra releases → `in_flight = 0` (never negative; DB CHECK also guards) |
| C7 | ratified org concurrency 10 | **50 concurrent** acquires → exactly 10 |
| D1–D3 | **stale lease recovery** | with 2 live leases, the lease was forced into the past (simulating a killed worker) → next acquire **succeeded** and reset `in_flight` to 1 |
| E1 | no cross-tenant bucket sharing | an exhausted user bucket did not affect another user; an exhausted org bucket did not affect another org |
| E2 | organisation ceiling holds | the exhausted org's own user bucket remained refused |
| E3 | bucket independence | 4 unrelated bucket rows, no shared state |
| F1–F3 | denial bookkeeping | `denied_count` incremented; `updated_at` and `tokens` **unchanged** (refill basis preserved) |
| G1 | mixed load integrity | 120 mixed concurrent transitions (user tokens/leases/org tokens) landed exactly on each ceiling (10/4/20) |
| G2 | high-contention load | 400 concurrent acquires on a 200-capacity bucket admitted 201 (the allowance plus one token of elapsed refill at 5/s over 0.35 s) — no multiplication |

**Conclusion:** the multi-worker atomicity claim is **independently established**, not merely asserted: each transition is one statement, and no concurrency scenario produced a doubled allowance or a leaked slot.

## 15. Security and tenant-isolation verification

| Requirement | Observed evidence |
| --- | --- |
| Authenticated organisation scope | every tool resolves scope through `authorize_insight_scope`; handlers bind `org = access.organization_id` (lines 494/550/622 of `services/insight_tools.py`) |
| No request-supplied organisation override | the request's `organization_id` is only an *addressed* organisation that must pass I2 authorization; the analytics queries receive the **authorized** organisation as `$1` |
| Organisation predicate in every new query | all six analytics methods carry `organization_id = $1` on the rows they return; the provenance join and the aggregation dimension join additionally carry `cs.organization_id = $1` (both sides) |
| Cross-tenant denial | cross-tenant cases are asserted by the new suites (discovery/aggregation/provenance) and by the existing I2 suites — all passing |
| No arbitrary SQL / no interpolation of caller values | fixed literals + positional `$n` parameters; the only interpolated identifiers are `$n` indices and the closed dimension/label maps |
| No arbitrary tool invocation | closed dispatch; unknown name → `invalid_input` / `unratified_tool`; live CHECK refuses unratified names |
| No LLM authorization | the planner cannot decide authorization; narration receives declared output only and is suppressed for ambiguity; the LLM never sees reference resolution |
| No raw source / signed-URL leakage | new outputs carry identifiers, dates, scope, activity, CO₂e and line-item ids only |
| No new persona / permission / endpoint | no new route file, no new permission or persona; the diff adds no endpoint |
| No RLS weakening | the migration only enables RLS on the two **new** tables (no policy) and changes no existing policy; live check: 0 policies on the new tables |
| New tables reachable only by service role | RLS enabled with no policy on both tables |

## 16. Regression tests

**Definitive baseline comparison.** A pristine copy of the implementation's parent (`c7cd9cc`, extracted via `git archive` into `/tmp/ct_baseline` — the checkout's `.git` was not written) was run against the same three backend unit directories:

| Run | Result |
| --- | --- |
| Baseline `c7cd9cc` | **4 failed, 1 868 passed, 9 skipped** (1 881 collected) |
| HEAD `cbc529dd` | **4 failed, 2 018 passed, 8 skipped** (2 030 collected) |
| Failure sets | **IDENTICAL** — the package introduced **zero** new failures |
| Delta | **+149 tests**, all passing (26+32+33+31+27 = 149), which exactly accounts for the collected-test difference (1 881 + 149 = 2 030) |

**New suites (independently re-run; each reproduces the report's number exactly):** discovery **26**, aggregation + provenance **32**, analytics SQL + migration assertions **33**, query planner **31**, rate limiting + answer states **27** → **149 passed**.

**Existing Insight regression (I2/I3/I4/I5/I6 selection of 12 files):** **149 passed, 5 skipped** (the 5 skips are the live-RLS database tests).

**Frontend:** `CI=true react-scripts test` over the Insight suites → **4 suites, 103 tests passed, 0 failed** (`insight-answer-states`, `insight-api`, `insight-references`, `insight-page`). The report's "3 suites, 95 tests" corresponds to the same set minus `insight-api` (103 − 8 = 95) — consistent, not contradictory.

**Nothing was altered to obtain these results**; no test, fixture, configuration or source file was modified.

## 17. Pre-existing defects

**17.1 Stale migration-count pin.** `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` fails with `assert 78 == 71` **at the baseline commit** (independently reproduced in `/tmp/ct_baseline`), and `assert 79 == 71` at HEAD (the authorized migration being the one extra file). It is pre-existing, was disclosed by the implementer, and was correctly left unfixed. It is unaffected by this package beyond the +1 migration the package was authorized to add.

**17.2 Cross-tenant factor metadata** (`snapshot_count_for_factor()`, `factor_usage_span()`, `GET /api/v3/emissions/factors/{factor_id}`). **Not worsened and not depended upon:**

* `backend/api/v3_emissions.py` is **not in the implementation diff**.
* `backend/data/emissions_logs.py` **is** in the diff, but the change is **purely additive**: `--numstat` reports **0 deleted lines**, and the diff contains **no hunk touching** `snapshot_count_for_factor` (line 519) or `factor_usage_span` (line 528).
* No new file references either method (grep over the new modules returns nothing), so no new surface depends on them.

The defect therefore remains exactly as it was, and the PO's separate remediation tracking is unaffected.

**17.3 (not previously disclosed) three pre-existing API-surface failures.** `tests/unit/api/test_review_sla_surfaces.py` fails on three assertions (`test_canonical_ops_sla_surface_registered`, `test_canonical_ops_review_assign_registered`, `test_admin_legacy_compat_surface_retained`) because the registered path set resolves to `{'/api/v2/health'}`. These failures **reproduce identically at the baseline commit** (verified in `/tmp/ct_baseline`), occur in isolation (not order-dependent), and involve no file this package touched. They are **pre-existing and unrelated**, but the implementation report's test accounting mentions only one pre-existing failure — see §22, observation 2.

## 18. Supplier limitation

* **Structurally supported**: `supplier` is a first-class discovery filter (`EXISTS … l.supplier_id`) and a first-class aggregation/provenance dimension with an organisation-scoped label lookup.
* **No supplier inference**: the lineage is the deterministic `emissions_logs.snapshot_id = calculation_snapshots.id`; there is no name/proximity/heuristic matching anywhere in the new code.
* **No write path populates `emissions_logs.supplier_id`** (independently confirmed): the only `INSERT INTO public.emissions_logs` (line 258) and the only `UPDATE public.emissions_logs` (line 555) in `data/emissions_logs.py` are **pre-existing** and neither mentions `supplier_id`; no new statement writes it.
* **No backfill, no invented confidence value**: the implementation diff contains no `UPDATE`/backfill statement and no confidence field.
* **Truthful no-data behaviour**: a supplier value no emission carries returns `no_data` (filter) or the explicit unassigned bucket (grouping) rather than a guess; asserted by the suite (`test_supplier_dimension_is_honest_when_no_emission_carries_a_supplier`).
* **No silent redesign of supplier persistence**: no schema change to any supplier column or table.

## 19. Facility / asset limitation

* Facility (`metadata->>'facility_id'`) and asset (`asset_id`) are served through the deterministic lineage only, via `EXISTS` for filtering and the same lineage for provenance.
* **No inference and no fan-out**: `EXISTS` cannot duplicate rows; the aggregation path uses `LEFT JOIN … ON cs.id = l.snapshot_id AND cs.organization_id = $1`, which cannot multiply a log row.
* **Organisation-scoped catalogue lookup**: labels come from `WHERE t.organization_id = $1 AND t.<key>::text = ANY($2::text[])`, bounded to the returned keys.
* **Unassigned is truthful**: `'none'` is the explicit bucket; an unresolvable key simply has no label (never inferred).
* **Snapshot-without-log limitation correctly handled and documented**: because the predicate is applied on the log side, a snapshot with no linked emission record cannot match a facility/asset filter. This is stated in the tool documentation rather than papered over, and no new data model was created for facility or asset.

## 20. Scope-boundary inspection

A scan of the entire implementation diff for prohibited work found **no implementation**, only comments/docstrings:

* Scope 3 Categories 1–15, Scope 3 analytics, market-based Scope 2, Scope 1 decomposition, primary/secondary factor classification, factor-history redesign, variance/attribution, supplier backfill, RAG, external concept answers, consultant/auditor Insight surfaces, unrestricted natural-language querying, cross-tab analytics, subscriptions/billing/entitlements/credits/overages/payment, I7 retention, full I8, production deployment — **absent**.
* No new dependency: `backend/pyproject.toml` and `frontend/package.json` are not in the diff.
* No new persona, permission, endpoint, provider path, retention rule, RLS policy or evidence viewer.
* The `ToolStatus` vocabulary and `REFERENCE_KINDS` are unchanged; `domain/insight_tool.py` is untouched.
* The pre-existing `_GROUP_EXPRESSIONS` semantics used by the existing emissions surfaces were not modified (the new dimension map is separate).

## 21. Exact failures

**Product failures: none.** No authorized acceptance criterion failed, and no security, tenant-isolation or integrity defect was found.

**Pre-existing test failures observed (all reproduce at the baseline commit, all unrelated to this package):** 4 — the migration-count pin (§17.1) and the three review/SLA API-surface assertions (§17.3).

**Verifier-side failures, self-inflicted and corrected (disclosed for completeness):** during development of the live schema script, my own fixtures failed three times — a malformed hand-built UUID, a fixture-key collision with the acceptance loop, and an incorrect `CREATE DATABASE` target that lacked the Supabase-initialised schemas — plus one probe artifact (`group_key` missing from my discovered vocabulary). Each was diagnosed and corrected; the final runs are clean first runs. None of these indicates a product defect, and none involved modifying the repository.

**Environment-level failure, unrelated:** `20260823000000_d32_private_documents_storage.sql` cannot apply in the container because `storage.buckets` is created by the Storage service, not by SQL (§5.1).

## 22. Exact non-blocking observations

1. **Discovery filter `EXISTS` subqueries carry no organisation predicate on the log side.** `supplier`/`facility`/`asset` filters use `EXISTS (SELECT 1 FROM public.emissions_logs l WHERE l.snapshot_id = s.id AND …)` without `AND l.organization_id = $1`. The outer query is organisation-scoped, so **no foreign row can be returned** and no disclosure exists; the only theoretical effect is that a foreign log row incorrectly referencing this organisation's snapshot could influence a *match count* — a state the database does not prevent (`emissions_logs.snapshot_id → calculation_snapshots(id)` is a single-column FK, not composite with `organization_id`). Recommended (not required) remediation boundary: add the organisation predicate to those three `EXISTS` clauses so they mirror the provenance join. This is defence-in-depth consistency, not a disclosed vulnerability.
2. **The implementation report's full-suite accounting is incomplete.** It records one pre-existing failure (the migration pin) and "0 failed" with that pin deselected. Independently, the same three unit directories yield **4 failures at HEAD and 4 at the baseline** — the pin plus three `test_review_sla_surfaces.py` assertions that the implementer did not mention. The pass/skip/test totals also differ slightly from the report's (2 030 collected / 2 018 passed / 8 skipped measured here, versus "2 026 tests, 2 023 passed, 3 skipped" reported — a difference explained by selection, since the report's run apparently excluded the live-RLS file). The conclusion the report draws (no new failures) is **correct**; the statement of the pre-existing set is what is incomplete.
3. **Stale comment in the tool registry.** `services/insight_tools.py` still labels `TOOL_REGISTRY` as "exactly the four ratified tools (PO §4)" although the catalogue is now seven. Cosmetic documentation drift in code the package changed.
4. **`group_labels` interpolates a table name.** It is the only string-interpolated SQL identifier in the new code; the value comes from the closed `_ANALYTICS_LABEL_SOURCES` map keyed by an allowlisted dimension, so it is not injectable — noted because any future extension of that map must keep it closed.
5. **Limiter tables have no retention/cleanup path.** Bucket and lease rows are keyed by `(scope, scope_key)`, so growth is bounded by users + organisations rather than by request volume, and `denied_count` is monotonic. Operationally fine, and explicitly not commercial data; worth a line in any future operational runbook.
6. **The pre-existing cross-tenant factor methods now share a file with the analytics queries.** `snapshot_count_for_factor`/`factor_usage_span` live in `data/emissions_logs.py`, which this package extended (purely additively). The defect is untouched, but reviewers of this file should not conflate the two change sets; the PO's separate remediation tracking remains valid.
7. **`SEC-01` in the PO decision matrix reads "NOT AUTHORIZED" for "I8 thresholds + acceptance criteria".** The INS-01 authorization under which I verified explicitly requires technical rate limiting and states the exact expected defaults, which the implementation matches; the matrix row appears superseded for this scope. Recorded so the PO can reconcile the two documents' wording. No commercial meaning exists anywhere in the implementation, as required.
8. **What this verification did *not* exercise.** I verified 429/`Retry-After`/header behaviour and per-route refusal through code reading and the 27-test suite, and the DB-level concurrency/atomicity live through the real repository. I did **not** run a live HTTP end-to-end request against a running CarbonTally API (no such deployment was available in this environment), so end-to-end header emission through the ASGI stack rests on the unit suite plus the code path, not on an observed HTTP response.

## 23. Final verdict

**PASS WITH NON-BLOCKING OBSERVATIONS.**

All authorized acceptance criteria were independently verified:

* the **I3** catalogue is exactly the seven authorized tools, with closed input schemas, declared output allowlists, unchanged `ToolStatus` (six) and unchanged reference kinds (four), closed dispatch, typed-only persistence projections, and the four ratified tools demonstrably unaffected;
* **I4** adds exactly one answer state, `multiple_matches`, persisted and enforced by a live CHECK, mapped truthfully from the tool reasons, ranking below every security/failure state and above `tool_failure`/`partial`/`no_data`/`success`, with ambiguity never narrated and never silently resolved to a candidate;
* **discovery, aggregation and provenance** are bounded (25 / 50 / 100), deterministically ordered, truncation-honest, organisation-scoped, built from fixed literals with positional parameters, and free of inferred supplier/facility/asset relationships;
* the **shared Source Evidence Viewer** is reused with no new viewer, route, permission, RLS rule or evidence architecture, and the navigation chain runs through the already-authorized reference kinds;
* the **query planner** is provably bounded and deterministic, with no provider, database, SQL, tenant or authorization decision in its source, and no schema escape under adversarial input;
* **rate limiting** matches the ratified defaults exactly, is server-configured and ceiling-bounded, cannot be raised by a client, protects **both** customer-facing execution routes with no third execution path, and carries no commercial meaning;
* the **PostgreSQL migration applies cleanly inside the real 79-file chain and is idempotent**, preserves existing values, widens only the two authorized CHECK vocabularies, and creates two RLS-enabled policy-less tables;
* **concurrent limiter behaviour was executed live** and 30/30 checks passed — no allowance multiplication, correct and idempotent lease accounting, working stale-lease recovery, and no cross-tenant bucket sharing;
* **regression safety** is established by an identical failure set against a pristine baseline with +149 new passing tests and no new failure;
* the two **pre-existing defects** were neither worsened nor depended upon, and a third pre-existing failure set was discovered and attributed to the baseline.

The observations in §22 are non-blocking: the most substantive (observation 1) is a defence-in-depth consistency point with no disclosure path, and the rest are documentation/accounting accuracy and operational notes.

**This verdict is independent acceptance evidence, not PO closure.** Per the authorization: no defect was fixed, no application code, migration, test or configuration was modified, no further package, I7, I8 or deployment was started, and the PO remains the only authority that can close this package. The disposable database container was destroyed and no verification artefact was committed other than this report.

---

**Report path:** `docs/architecture/CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-OHD-VERIFICATION-20260922.md`
**Verification target:** implementation `e4ea3254c6a709df0e9cedcd8c719515363b4358` on preflight `c7cd9cc2ff56e288c830bb5d204118a06aa31104`; final commit `cbc529dd8974d3ec16595fc5c6981c5217b43c24`.
