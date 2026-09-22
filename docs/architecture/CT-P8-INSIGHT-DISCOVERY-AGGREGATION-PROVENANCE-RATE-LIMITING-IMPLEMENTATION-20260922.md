# CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PROVENANCE-RATE-LIMITING-IMPLEMENTATION-20260922

**Task:** Implement the bounded Insight Discovery + Aggregation Foundation, aggregate → calculation provenance, shared Source Evidence Viewer reuse, and technical Insight execution rate limiting.
**Authorization:** PO Insight Discovery-Aggregation-Provenance-RateLimiting implementation authorization (2026-09-22), bounded by the PO decision matrix (`CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22`) and the preflight `CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PREFLIGHT-20260922`.
**Implementation baseline:** `c7cd9cc2ff56e288c830bb5d204118a06aa31104` (the preflight commit).
**Labels:** **IMPLEMENTED** · **NOT IMPLEMENTED** · **LIMITATION** · **BLOCKED** · **OUT OF SCOPE**.

---

## 1. Exact HEADs

| Item | Value |
| --- | --- |
| Starting HEAD | `c7cd9cc2ff56e288c830bb5d204118a06aa31104` (`docs(p8): preflight Insight discovery aggregation foundation`) |
| Implementation commit | recorded in the completion summary (§19) |
| Ending HEAD | the commit that contains this report; its exact SHA is reported in the completion summary and verified with `git rev-parse HEAD` and `git ls-remote github refs/heads/p8-release-reconciled` |

## 2. Branch and remote

`p8-release-reconciled` → `github` (`https://github.com/shomonrobie/CarbonTally.git`), verified aligned after the push (`git rev-list --left-right --count HEAD...github/p8-release-reconciled` → `0 0`).

## 3. Files changed

**Backend — modified**

| File | Change |
| --- | --- |
| `backend/domain/insight_interaction.py` | I4: adds the authorized `multiple_matches` state, allowlists the three analytics tools' persisted arguments, allows a bounded `match_count` metadata key, orders the new state in the combination rule |
| `backend/services/insight_tools.py` | I3: three new tool definitions + handlers (discovery / aggregation / aggregate-provenance), dispatch, and a report-version-specific required-input rule (the previous generic "no required inputs" branch would have mis-validated the analytics tools) |
| `backend/services/insight_interactions.py` | I4 orchestration: deterministic planner integration, truthful reason→answer-state overrides, narration suppression for ambiguous results, bucket + concurrency enforcement, lease release on every exit path, `rate_limited` Layer-2 record |
| `backend/services/insight_context.py` | I5: the per-interaction tool-call projection bound follows the authorized catalogue (4 → 7) |
| `backend/data/emissions_logs.py` | Bounded, organisation-scoped analytics queries + allowlisted dimension/expression maps + the discovery filter builder |
| `backend/api/v3_insight_tools.py` | Rate limiting on the second customer-facing execution route (anti-bypass) |
| `backend/api/dependencies.py` | Real wiring for the shared rate-limit repository (`RepositoryBundle` field + pool construction) |

**Backend — added**

| File | Purpose |
| --- | --- |
| `backend/domain/insight_query.py` | Bounded typed analytics contract: closed filter/dimension vocabularies, hard bounds, validation + tolerance resolution, tool-name constants (no I/O, no SQL) |
| `backend/services/insight_query_planner.py` | Deterministic bounded query planner (regex only; four outcomes; no provider, no database) |
| `backend/services/insight_rate_limit.py` | Policies, server-side configuration, enforcement, concurrency leases, 429 / `Retry-After` helpers |
| `backend/data/insight_rate_limit.py` | Single-statement atomic token-bucket and lease statements |
| `supabase/migrations/20261005000000_p8_insight_discovery_aggregation_rate_limit.sql` | Widens the tool-name and answer-status CHECK constraints; creates the two shared limiter tables (RLS on, no policy) |

**Frontend — modified**

| File | Change |
| --- | --- |
| `frontend/src/v3/insight/answerStates.js` | Presents the authorized `multiple_matches` state (existing badge tone + existing icon; no new visual system) |
| `frontend/src/v3/__tests__/insight-answer-states.test.js` | Vocabulary expectation updated to the I4 contract (fourteen + one) |

**Tests — modified:** `backend/tests/unit/api/fakes.py` (shared bundle gains the limiter store), `test_v3_insight_i3_tools.py` (authorized seven-tool catalogue; limiter fake wired), `test_v3_insight_i4_interactions.py` (vocabulary + limiter fake), `test_v3_insight_i5_context_integration.py` (limiter fake), `test_i1_insight_migration.py` and `test_i2_insight_authorization_contracts.py` (the authorized migration is now the latest).
**Tests — added:** `tests/unit/api/insight_limit_fakes.py`, `tests/unit/api/insight_analytics_fakes.py`, `tests/unit/api/test_p8_insight_discovery.py`, `tests/unit/api/test_p8_insight_aggregation.py`, `tests/unit/services/test_insight_query_planner.py`, `tests/unit/services/test_insight_rate_limit.py`, `tests/unit/data/test_p8_insight_analytics_sql.py`.

## 4. Database migrations

`supabase/migrations/20261005000000_p8_insight_discovery_aggregation_rate_limit.sql` — **IMPLEMENTED** (additive, idempotent):

1. `ci_tool_calls_tool_name_check` widened from the four ratified names to the seven authorized names (same constraint, same enforcement point);
2. `ci_interactions_answer_status_check` widened by exactly one state (`multiple_matches`); the closed I3 `tool_status` vocabulary is untouched;
3. `public.insight_rate_limit_buckets` and `public.insight_concurrency_leases` created with keys, checks and indexes plus `ENABLE ROW LEVEL SECURITY` (no policy → service-role only), and comments stating that they are operational counters with no commercial meaning.

No destructive statement, no data change, no change to existing policies, no column or table dropped.

**LIMITATION:** the migration was authored and statically asserted (vocabulary, table shape, RLS, absence of destructive/commercial statements) but **was not applied to a database in this environment** — §16.

---

## 5. I3 changes — IMPLEMENTED

The ratified four tools are **unchanged** in identity, input, output, reference kinds and statuses. Three tools were added to the catalogue under the 2026-09-22 authorization:

| Tool | Input (closed, all values positional) | Output allowlist | Reference kinds |
| --- | --- | --- | --- |
| `insight_discovery` | `start_date`, `end_date`, `reporting_year`, `co2e_kg`, `co2e_tolerance_kg`, `co2e_tolerance_pct`, `co2e_approx`, `activity`, `scope`, `supplier_id`, `facility_id`, `asset_id`, `limit` (all optional; at least one filter required, enforced server-side) | `match_count`, `match_count_capped`, `candidates`, `basis` | `calculation_snapshot`, `evidence_line_item` |
| `insight_aggregation` | `group_by` (required, allowlisted), `start_date` (required), `end_date` (required), `limit` | `group_by`, `period`, `groups`, `group_count`, `groups_truncated`, `row_count`, `total_co2e_kg`, `total_is_complete`, `basis`, `provenance_tool` | — (an aggregate is a total, not a record) |
| `insight_aggregate_provenance` | `group_by` (required, allowlisted), `group_key` (required), `start_date` (required), `end_date` (required), `limit` | `group_by`, `group_key`, `period`, `snapshots`, `snapshot_count`, `snapshot_count_capped`, `basis` | `calculation_snapshot`, `evidence_line_item` |

* **Authorization is unchanged**: every new tool goes through the same `invoke_tool` path — validate → `api.insight_authz.authorize_insight_scope` → organisation-scoped read. No new authorization mechanism exists.
* **Statuses unchanged**: `ToolStatus` still has exactly six values; there is no `multiple_matches` tool status. Ambiguity is expressed at the governed I4 answer-state layer via the tool's machine-readable `reason`.
* **Reference vocabulary unchanged**: `REFERENCE_KINDS` still has the same four kinds; the analytics tools reuse `calculation_snapshot` and `evidence_line_item`.
* **Closed-vocabulary validation**: `domain/insight_query.validate_discovery` / `validate_group_by` / `validate_period` / `validate_limit` reject unknown parameters, unsupported dimensions, inverted or over-long periods, conflicting tolerances, invalid scopes, negative amounts, over-long text and out-of-range limits **before any row is read**.
* **One I3 input-validation correction** (directly required): the legacy branch that demanded a version identifier whenever a tool declared no required inputs would have refused every analytics call; it is now scoped to `report_version_lookup` (its original purpose). The four ratified tools declare required inputs, so their behaviour is unchanged.

## 6. I4 changes — IMPLEMENTED

| Change | Detail |
| --- | --- |
| `AnswerStatus.MULTIPLE_MATCHES = "multiple_matches"` | First-class answer state for "several authoritative records matched". Never converted into `success`, never a silent first-result choice, never LLM-ranked. |
| Combination order | `multiple_matches` sits after `invalid_input`/`rate_limited`/`refused` and before `tool_failure`/`partial`/`no_data`/`success` in `_ANSWER_ORDER`, so a mixed interaction is still reported truthfully. |
| `TOOL_ARGUMENT_ALLOWLIST` | Entries for the three analytics tools (typed parameters only; no free text is persisted) — Q6 discipline preserved. |
| `RESULT_METADATA_ALLOWLIST` | Adds `match_count` (a bounded count of matching records, not record content). |
| `project_result_metadata` | Persists `match_count` when the tool reports it. |
| Reason → state overrides (in the orchestration, not the domain) | `multiple_matches` → `MULTIPLE_MATCHES`; `zero_total` → `ZERO` (records found, total genuinely 0); `amount_tolerance_required` → `NEEDS_CLARIFICATION`. |
| Narration | Suppressed for `multiple_matches`: the model is never given an ambiguous candidate set, so it can never appear to choose one. The result set itself is still returned to the caller as bounded references. |
| Lifecycle | A concurrency refusal is persisted as `failed` + `answer_status=rate_limited` with a canonical audit event; a bucket refusal is answered `429` before any Layer-2/Layer-1 row exists. |

## 7. Discovery contract — IMPLEMENTED

* **Dimensions**: date, date range, reporting year, CO₂e amount, amount tolerance (absolute or relative), activity, scope, supplier, facility, asset.
* **Matching semantics (explicit and deterministic)**: dates are the stored calendar `DATE` values (inclusive range; a single day is a one-day range); `reporting_year` is its own predicate; CO₂e compares `calculation_snapshots.co2e_kg` in kg CO₂e with **zero tolerance for an exact match** and an explicit symmetric range for a stated tolerance; activity is a **literal case-insensitive containment** test on `activity_type` with `%`/`_`/`\` escaped (never a wildcard pattern, never fuzzy scoring); scope is normalised onto the existing canonical `Scope` vocabulary; supplier/facility/asset resolve through the existing **deterministic lineage** `emissions_logs.snapshot_id = calculation_snapshots.id` via `EXISTS` predicates (no joins that could fan out, no inference).
* **Outcomes**: zero → `no_data` (`no_matches`); one → `success`; several → `success` + `reason=multiple_matches` → I4 `multiple_matches`, with a **bounded, capped match count** (`limit + 1`, never a full count) and `truncated` set when the cap was reached.
* **Ordering**: deterministic (`date` descending, then snapshot `id`).
* **Bounded**: at most `MAX_DISCOVERY_RESULTS = 25` candidates per call; count work is bounded by `limit + 1`.
* **Clarification instead of guessing**: an approximate amount without a determinable tolerance is refused as `amount_tolerance_required` (planner and tool both enforce it), and the I4 answer is `needs_clarification`.
* **No arbitrary querying**: filters are a closed allowlist; the SQL fragment is built from fixed literals with positional parameters only; an empty filter set raises rather than scanning the organisation.

## 8. Aggregation contract — IMPLEMENTED

* **Dimensions (allowlisted)**: `scope`, `month`, `year`, `activity`, `supplier`, `facility`, `asset`.
* **Basis**: kg CO₂e from `emissions_logs.calculated_kg_co2e` — the same column the existing emissions aggregates use, stated in every result (`basis`). The period total comes from the **existing** organisation-scoped `aggregate()` call, so a truncated group list never fabricates a complete total (`total_is_complete=false` when the group list is truncated).
* **Bounds**: at most `MAX_AGGREGATE_GROUPS = 50` groups; one extra row is fetched to *detect* truncation rather than assume it; the period is explicit and bounded to `MAX_PERIOD_DAYS = 3660` (10 years).
* **Ordering**: deterministic (`co2e_kg` descending, then group key ascending).
* **Rejection**: unsupported dimensions/operators are refused before any query; unknown parameters are refused; inverted/over-long periods are refused.
* **No unsafe quantity aggregate — LIMITATION (deliberate)**: a summed raw quantity across mixed units (litres, kWh, m³, currency) is **not** exposed anywhere. The result carries `co2e_kg` and `row_count` per group only. This is a deliberate limitation, not an omission: exposing it was explicitly forbidden by the authorization unless a unit-safe basis exists, and `unit` is not part of any group key.
* **Human-readable keys**: `asset`, `facility` and `supplier` keys are resolved to catalogue names through one bounded, organisation-scoped lookup limited to the returned keys; an unresolvable key simply has no label (never inferred).
* **Empty/zero truthfulness**: no rows in the period → `no_data` (`no_rows_in_period`); rows present with a calculated total of exactly 0 → `success` + `reason=zero_total` → I4 `zero` (never conflated with `no_data`).

## 9. Provenance behaviour — IMPLEMENTED

* `insight_aggregate_provenance` answers "which calculations make up this number" for one aggregate cell (`group_by` + `group_key` + period).
* **Bound**: at most `MAX_PROVENANCE_SNAPSHOTS = 100` snapshot references; the count is fetched with `limit + 1`, so a larger set is reported as `snapshot_count_capped=true` **and** `truncated=true` rather than presented as complete.
* **Ordering**: deterministic (`date` descending, then snapshot id).
* **Tenant isolation**: the log predicate and the snapshot join are both organisation-scoped (`l.organization_id = $1` and `cs.organization_id = $1`), and only rows carrying an authoritative `snapshot_id` are eligible.
* **Identifiers first (DM-6 preserved)**: each row returns only snapshot identity, date, activity type, scope, CO₂e and the evidence line id, plus existing `calculation_snapshot` / `evidence_line_item` references. Raw source content, source file/page, signed URLs and actors are never returned.
* **Aggregate honesty**: the aggregation result declares `provenance_tool` so a caller can always follow an unexplained number to its bounded component records.

## 10. Shared Source Evidence Viewer integration — IMPLEMENTED (reuse, no second viewer)

* No new evidence viewer, no Insight-only evidence architecture and no change to the viewer's routes, DM-6 gating, audit or signed-URL controls were made.
* Insight results now satisfy the existing handoff contract: discovery candidates and provenance rows emit **existing** reference kinds, and the existing frontend chain resolves them — `calculation_snapshot` through the ratified `calculation_snapshot_lookup` tool ("View calculation") and `evidence_line_item` through the shared viewer path `/evidence/line-items/{id}` ("View source evidence", with DM-6 depth and `evidence.line_access` audit unchanged).
* The LLM never receives the reference *resolution*: narration is limited to the tool's allowlisted output, and reference resolution happens only when the user follows the link.

## 11. Supplier capability and the actual supplier-data limitation — IMPLEMENTED + LIMITATION

* **IMPLEMENTED**: `supplier` is a first-class filter and a first-class grouping dimension, resolved through the existing deterministic lineage `emissions_logs.supplier_id` (grouping) and `EXISTS` (filtering), with a bounded organisation-scoped name lookup; `INNER`-style behaviour means a supplier value that no emission carries returns `no_data`.
* **LIMITATION (pre-existing, unchanged by this package)**: the application still has **no write path that populates `emissions_logs.supplier_id`** — the only `INSERT INTO public.emissions_logs` and the only `UPDATE` both omit it, so in the current dataset the supplier dimension is structurally correct but effectively empty, and it returns `no_data` rather than a guess. No backfill, no inference, no confidence value and no fabricated relationship was introduced (all forbidden by the authorization). The test suite asserts this behaviour explicitly (`test_supplier_dimension_is_honest_when_no_emission_carries_a_supplier`).
* **NOT IMPLEMENTED (OUT OF SCOPE)**: supplier persistence (`C-06`), supplier analytics (`C-07`), supplier variance (`C-08`).

## 12. Facility / asset behaviour — IMPLEMENTED + LIMITATION

* Facility and asset exist authoritatively on the operational log record (`metadata->>'facility_id'` and `asset_id`), so both are served through the deterministic lineage join to `calculation_snapshots` (which carries neither column).
* Labels are resolved from the organisation's own `facilities` / `assets` catalogue, bounded to the returned keys; raw UUIDs are not presented where a name exists, and `'none'` is the explicit bucket for unassigned rows.
* **LIMITATION**: facility/asset are not snapshot-native. Discovery ranks candidates from `calculation_snapshots` and applies the log-level predicate through `EXISTS`; a snapshot with no linked emission record therefore cannot match a facility/asset filter. This is stated in the tool documentation rather than papered over with a proximity guess.
* **No new data model** was created for facility or asset.

## 13. Rate-limit implementation and exact defaults — IMPLEMENTED

**Scope: technical abuse protection only.** No plan, entitlement, credit, overage, quota or payment concept exists anywhere in the implementation, and the migration comment states that these tables must never be reused as a billing signal.

**Store (shared, multi-worker safe):** two PostgreSQL tables reached through the existing service-role pool — no new external infrastructure and no Redis.

* `insight_rate_limit_buckets` — one token bucket per `(scope, scope_key)`, refilled inside the statement from the row's own `updated_at`;
* `insight_concurrency_leases` — one in-flight counter per `(scope, scope_key)` with a lease expiry (`LEASE_SECONDS = 120`), so a killed worker's capacity is reclaimed (stale-lock recovery).

Every transition is **one atomic statement** (`INSERT … ON CONFLICT … DO UPDATE … WHERE … RETURNING`), so concurrent workers cannot interleave a read/modify/write and the allowance cannot be multiplied by the number of workers.

**Exact defaults (ratified security defaults, not commercial entitlements):**

| Scope | Sustained | Burst | Bucket capacity | Max concurrent |
| --- | --- | --- | --- | --- |
| Per authenticated user | 20 requests/minute | 5 | 25 | 2 |
| Per organisation | 100 requests/minute | 20 | 120 | 10 |

* **Configuration**: server-side environment only — `CARBONTALLY_INSIGHT_RATE_LIMIT_ENABLED`, `…_USER_PER_MINUTE`, `…_USER_BURST`, `…_USER_MAX_CONCURRENT`, `…_ORG_PER_MINUTE`, `…_ORG_BURST`, `…_ORG_MAX_CONCURRENT`. Values are validated inside safety ceilings (user ≤ 600/min, 100 burst, 20 concurrent; org ≤ 6000/min, 1000 burst, 100 concurrent); an invalid or out-of-range value falls back to the ratified default with a warning. **No request field participates in the decision**, so a client cannot raise its own limit. Disabling is an explicit server-side action that logs a warning.
* **Ordering**: the bucket is charged for the authenticated user first, then the organisation; a user denial therefore does not consume an organisation token, and the organisation ceiling still holds when many users act at once.
* **Before expensive work**: the bucket check runs before any Layer-1/Layer-2 write, tool execution or provider narration.
* **Refusal**: HTTP `429` with `Retry-After` (computed from the bucket's own refill rate, bounded to 120 s) plus `X-RateLimit-Remaining`/`X-RateLimit-Reset`.
* **`rate_limited` answer state**: used truthfully where a Layer-2 record exists — a concurrency refusal is persisted as `lifecycle=failed`, `answer_status=rate_limited`, `error_class=concurrency_limit` with a canonical audit event. A bucket refusal deliberately creates **no** record (§16).
* **Observability**: denials increment `denied_count` + `last_denied_at` on the existing counter row (never touching the refill basis) and log a hashed scope key — no raw identifier, no question text.
* **Anti-bypass**: the limiter is applied on **both** customer-facing execution routes — `POST /api/v3/insight/interactions` and `POST /api/v3/insight/tools/invoke` — with tests proving each refuses when exhausted. Read-only routes (`GET /interactions`, `GET /{id}`, `GET /tools`) execute nothing and are not limited.
* **Tenant isolation**: keys are the authenticated user id and the organisation being addressed; unrelated tenants share no bucket.

## 14. Security controls — IMPLEMENTED

* **Authorisation unchanged and re-used**: every analytics invocation resolves the caller's scope through `api.insight_authz.authorize_insight_scope`; the organisation used in the query is the authorized organisation, never a request-supplied id.
* **Organisation scope in SQL**: all six analytics queries carry `organization_id = $1`; the provenance snapshot join additionally carries `cs.organization_id = $1`; a static test asserts each method keeps its predicate and its bound.
* **No arbitrary query surface**: closed filter/dimension allowlists, fixed SQL literals, positional parameters, no statement interpolation, no model-generated SQL, no cross-tab, no unrestricted filtering.
* **Input rejection before any read**: invalid/unknown parameters, unsupported dimensions and bad periods are refused with machine-readable reasons and produce zero repository calls (asserted).
* **LLM boundary unchanged**: narration still receives only `tool`/`status`/`reason`/allowlisted `data`/references capped at 2,000 characters, and is now additionally suppressed for ambiguous results. No raw source content, signed URL, storage path or unrestricted row can reach it.
* **I4 persistence rules preserved**: Q4 (question hash only), Q5 (append-only evidence), Q6 (allowlisted projections, extended — never loosened), Q8 (creator-private reads), Q9 (ids/statuses only in the canonical audit).
* **RLS**: the two new tables have RLS enabled with no policy (service-role only), matching the other Insight tables; no existing policy was changed and no RLS was disabled anywhere.
* **No new persona, permission, endpoint or provider path** was introduced.

## 15. Natural-language boundary — IMPLEMENTED

* `services/insight_query_planner.py` is **deterministic regex parsing**: no provider call, no database access, no SQL, no authorization decision, no tenant decision.
* It emits only the closed schema `{status, tool, tool_input, operation, reason}` where `tool` is one of the three authorized names and `tool_input` contains only allowlisted typed parameters (asserted by test).
* Four outcomes: `planned` (bounded typed input), `clarification` (recognisable analytics question missing a determinable parameter — `period_required`, `group_key_required`, `amount_tolerance_required`), `invalid` (explicitly invalid value such as `scope 9`), `unsupported` (not an analytics question → the ratified keyword classifier runs exactly as before, so no previously-working question changed meaning).
* The planner is **advisory**: the tool re-validates every parameter against `domain.insight_query` before a row is read, and I2 decides authorization.
* **LIMITATION**: an implied facility/supplier/asset *identity* is never extracted from free text (the identity is an organisation-owned catalogue key); such a question becomes a clarification.

## 16. Tests executed and results

| Suite | Result |
| --- | --- |
| Phase 8 discovery (new) | **26 passed** |
| Phase 8 aggregation + provenance (new) | **32 passed** |
| Phase 8 analytics SQL + migration assertions (new) | **33 passed** |
| Deterministic bounded query planner (new) | **31 passed** |
| Rate limiting + analytics answer states (new) | **27 passed** |
| Existing Insight regression (I2/I3/I4/I5/I6 suites) | **133 passed, 5 skipped** (skips are the live-RLS database tests) |
| Backend unit suite: `tests/unit/data` + `tests/unit/api` + `tests/unit/services` | **2,026 tests — 2,023 passed, 3 skipped, 0 failed** (the pre-existing stale pin in §16.1 deselected; with it included, exactly that one pre-existing failure) |
| Insight frontend suites (answer states, references, page) | **3 suites, 95 tests passed** |

Coverage against the required matrix: discovery zero/one/multiple, capped match count, exact amount, absolute and relative tolerance, approximate-without-tolerance refusal, date, date range, reporting year, scope, activity, supplier, facility, asset, invalid/unsupported dimension, unknown parameter, tenant isolation, cross-tenant denial, determinism; aggregation for every authorized dimension, bounded result count, deterministic ordering, truncation honesty, zero vs no-data, mixed-unit safety, invalid grouping/filter rejection; provenance aggregate→snapshots, deterministic ordering, truncation, no raw content, tenant isolation; I3 authorization/allowlists/persistence/registry; I4 `multiple_matches`/`zero`/`rate_limited`/`needs_clarification`/`invalid_input` and narration suppression; rate limiting per-user, per-org, burst allowance, concurrency, release-on-failure, stale-lease recovery, `429`, `Retry-After`, both routes (no bypass) and configuration clamping.

### 16.1 Test-environment facts (stated, not hidden)

* **LIMITATION — the SQL was not executed against a database.** No PostgreSQL instance was used in this environment. The statement builders are therefore pinned by *pure* unit tests (fixed literals, sequential positional parameters, no caller-value interpolation, organisation predicate present, `LIMIT` present, unknown dimension raises, empty filter set raises) and the migration by structural assertions. Executing the statements and the migration requires a **disposable** database: the F-046-1 invariant forbids pointing the destructive integration harness at any persistent database. **This remains an integration/OHD verification task.**
* **Pre-existing failure (not caused by this package, not fixed):** `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` asserts `len(migrations) == 71` while `git ls-tree HEAD supabase/migrations/` already contained **78** `.sql` files at the starting HEAD (`79` including the authorized migration). The assertion is a stale revision-scope pin that was **already failing before this work** — verified by counting the tracked migrations at HEAD rather than by assuming it. It is documented here and left untouched (an unrelated edit I made to it was reverted) so the pre-existing defect stays visible instead of being silently absorbed.
* Two further "latest migration" pins were updated **because this package directly changed what they assert** (`test_i1_insight_migration.py`, `test_i2_insight_authorization_contracts.py`), each with a comment naming the authorizing decision.

## 17. Known limitations

1. **SQL not executed against a live database** (§16.1): the strongest verification available here is structural/pure; the multi-worker atomicity claim rests on each limiter transition being a single statement, which is asserted but not exercised concurrently.
2. **Supplier data is structurally empty** (pre-existing): `emissions_logs.supplier_id` is never written, so the supplier filter/grouping returns `no_data` / an unassigned bucket rather than populated analytics. Not fixed, not backfilled, not inferred.
3. **Facility/asset are not snapshot-native**: discovery applies them through the log lineage, so a snapshot with no linked emission record cannot match those filters.
4. **No mixed-unit quantity total** is exposed by design (CO₂e only).
5. **Period bound** of 10 years per request (`MAX_PERIOD_DAYS`) — a deliberate bound, not a data limit.
6. **Result bounds**: 25 discovery candidates and 50 aggregation groups per call; truncation is always reported.
7. **Concurrency lease TTL 120 s**: if a worker is killed mid-execution its slot is reclaimed on expiry rather than immediately (deliberate stale-lock trade-off; the normal path releases in a `finally`).
8. **Bucket refusals create no Layer-2 record** (deliberate, to prevent a hostile caller flooding the ledger); observability for those comes from the limiter counters + logs rather than the audit ledger.
9. **Frontend presentation is minimal**: the new answer state is presented and the existing references/handoff render the candidates; there is no dedicated multi-match *selection* UI (explicitly out of scope).

## 18. Anything explicitly NOT implemented (OUT OF SCOPE)

GHG Protocol Scope 3 categories 1–15 · Scope 3 analytics · market-based Scope 2 · Scope 1 decomposition (stationary/mobile/fugitive/process) · primary/secondary factor classification · factor-history redesign or candidate history · variance/attribution (period, factor, boundary, restatement) · supplier historical backfill and supplier inference · RAG · external knowledge-base/concept answers · consultant Insight surface · auditor Insight surface · unrestricted natural-language querying · arbitrary SQL · cross-tab analytics · commercial subscriptions · billing · usage credits · overages · payment provider · **I7** · **full I8** · production deployment.

Also deliberately not added: any new persona, permission, endpoint, provider path, retention rule, RLS policy or evidence viewer; any change to the closed I3 `ToolStatus` vocabulary; any change to the Source Evidence Viewer; any change to the `_GROUP_EXPRESSIONS` semantics the existing emissions surfaces rely on.

## 19. Blocker / unresolved governance question

* **No blocker exists inside the authorized scope.** The items below are carry-forward items for the PO/OHD, not implementation blockers.
* **Carry-forward 1 — migration application and concurrent-behaviour verification.** The migration and the limiter's atomic statements were not executed (no disposable database available; F-046-1). Applying the migration and exercising the limiter concurrently is a separate, explicitly authorized activity.
* **Carry-forward 2 — pre-existing defects left untouched.** (a) the stale migration-count pin (§16.1); (b) the cross-tenant metadata exposure of `snapshot_count_for_factor()` / `factor_usage_span()` via `GET /api/v3/emissions/factors/{factor_id}`, which the PO decision matrix already directed to be "separately tracked for remediation" and which is **not** on any path this package added. Neither was fixed here, per the instruction not to silently fix out-of-scope defects.
* **Governance note:** every PO decision this package required (the I3 catalogue expansion, one I4 answer state, one narrowing migration, the tolerance/date semantics implemented here, and technical rate limiting) was issued on 2026-09-22. No business policy was invented: where the authorization did not specify a rule (natural-language extraction depth, mixed-unit quantity exposure, facility/supplier identity resolution), the package returns a clarification, refuses, or documents a limitation instead of choosing a policy.

**Independent verification is required next:** this work is **IMPLEMENTED**, not independently **VERIFIED** or **ACCEPTED**. OHD verification is the next step.

## 20. Completion

Implementation, tests, documentation, commit and push are complete (see the completion summary for the exact SHAs and the alignment verification). **STOP** — no independent verification was performed by the implementing agent, the work is not declared PO-closed, and no further Phase 8 package, I7/I8 work or production deployment was started.
