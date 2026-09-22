# CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PREFLIGHT-20260922

**Task:** Read-only preflight for the first bounded **Insight Discovery + Aggregation Foundation** implementation package.
**Kind:** Forensics / preflight. **No implementation. Nothing here authorizes implementation.**
**Date:** 2026-09-22 · **Author:** Cline (implementation agent).
**Baselines:** `CT-P8-INSIGHT-ARCHITECTURE-IMPLEMENTATION-GAP-20260922.md` (`669669a`), `CT-P8-INSIGHT-QUESTION-LIBRARY-CAPABILITY-GAP-20260922.md` (`7f97b55`).
**Labels:** `[FACT]` code-verified · `[PO]` decided PO requirement · `[GOV]` decision/authorization still required · `[INFER]` reasoned from verified facts · `[BLOCKED]` cannot proceed without an explicit decision.

---

## 1. Executive verdict

`[FACT]` The **computation foundation for both approved capabilities already exists** and is org-scoped, parameterised and injection-safe: period aggregation over **scope / month / year / asset / facility** (`EmissionLogRepository.aggregate`, dimension allowlist `_GROUP_EXPRESSIONS`) and over **activity** (`aggregate_by_activity`), plus date-ranged snapshot listing (`list_snapshots`) returning every field a discovery candidate needs. What does **not** exist is any **contract**: no Insight tool accepts a date, amount, dimension or period; intent classification is keyword-only; parameter extraction is UUID-only; and `ToolStatus`/`AnswerStatus` cannot express "several candidates matched". Three definitions the PO has declared mandatory before implementation are also missing — amount tolerance, date/timezone semantics, and the multi-match outcome representation.

`[INFER]` The smallest technically complete package is therefore **contract-shaped, not computation-shaped**: two typed bounded operations (discovery over calculation snapshots; aggregation over the six approved dimensions) plus one bounded provenance operation (aggregate → contributing snapshot ids), exposed through the closed I3 boundary, with one PO decision on how "multiple matches" is represented. **No schema change, RLS change, migration or Source Evidence Viewer change is required.** No downstream capability is a prerequisite, with **one precise exception**: discovery/aggregation **by supplier** cannot be in Package 1 (the emission-level key is never written) and **facility** is available only from `emissions_logs`, not from calculation snapshots.

---

## 2. Current HEAD and branch

| Item | Value |
| --- | --- |
| Checkout | `/home/shomonrobie/ct_93d5cdd` (authoritative) |
| Branch | `p8-release-reconciled` |
| **HEAD** | `7f97b5568c72a0081a31bf50b14e532f0e51de82` |
| `git ls-remote github refs/heads/p8-release-reconciled` | `7f97b5568c72a0081a31bf50b14e532f0e51de82` |
| **Alignment** | **`0 0` — local HEAD and `github/p8-release-reconciled` aligned** |
| `git status --short` at start | four untracked PO/ChatGPT documents (architecture reference, question library, decision matrix, ChatGPT PO history); **no tracked file modified** |
| Parent clone | `/home/shomonrobie/carbon_tally` — **not** the release source |

`[FACT]` **No §23 stop condition was triggered**: the release topology matches the documented one; the reference/library documents are present and unmodified; the I3/I4 boundaries match the documented baseline; and no implementation change or migration was needed to complete the analysis.

---

## 3. Repository alignment — recorded commands

```text
git status --short
  -> ?? docs/ChatGPT/CarbonTally_Incremental_ChatGPT_PO_History_2026-09-22.md
  -> ?? docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22.md
  -> ?? docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md
  -> ?? docs/architecture/CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md

git branch --show-current   -> p8-release-reconciled
git rev-parse HEAD          -> 7f97b5568c72a0081a31bf50b14e532f0e51de82
git ls-remote github refs/heads/p8-release-reconciled
                            -> 7f97b5568c72a0081a31bf50b14e532f0e51de82  refs/heads/p8-release-reconciled
git rev-list --left-right --count HEAD...github/p8-release-reconciled
                            -> 0	0     (aligned)
```

---

## 4. Documents inspected

| Document | Lines | Role |
| --- | --- | --- |
| `docs/architecture/CarbonTally_Insight_Architecture_Reference_2026-09-22.md` (untracked) | 789 | architecture requirements — §7 discovery, §8 matching semantics, §11 security, §14 phases |
| `docs/architecture/CarbonTally_Insight_Question_Library_2026-09-22.md` (untracked) | 971 | 426 questions; §26 variance, §28 evidence, §35 answer modes |
| `docs/architecture/CT-P8-INSIGHT-ARCHITECTURE-IMPLEMENTATION-GAP-20260922.md` | 579 | baseline gap report (tracked, `669669a`) |
| `docs/architecture/CT-P8-INSIGHT-QUESTION-LIBRARY-CAPABILITY-GAP-20260922.md` | 683 | question-library capability gap (tracked, `7f97b55`) |
| `docs/architecture/CT-P8-PO-DECISION-INVENTORY-20260922.md` | 887 | decision inventory; §0 status reconciliation |
| `docs/architecture/CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md` | 943 | §3.5 closed I3 catalogue, §5 I6, §6 I7, §8 I8-A, §11 |
| `docs/architecture/CARBONTALLY_P8_I6_INSIGHT_CLOSURE_20260922.md` | 150 | §F accepted follow-ups |
| `docs/architecture/CT-P8-PO-DECISION-DISPOSITION-CLOSURE-DECISIOIN-FOR-SOURCE-EVIDENCE-VIEWER-AND-INSIGHT-20260922.md` | 458 | viewer PO closure; C-01…C-05 dispositions |
| `docs/verification/phase8/CT-P8-SOURCE-EVIDENCE-VIEWER-OHD-VERIFICATION-20260922.md` | 239 | viewer OHD verification |
| `docs/architecture/CarbonTally_PO_Insight_Capability_Decision_Matrix_2026-09-22.md` (untracked) | 247 | **PO decision matrix** |

`[PO]` Two operative facts from the decision matrix: **§4 dependency order** places "discovery contract + ambiguity/tolerance/timezone" first and "aggregation contract + scope/filter semantics" second; **§5** states the factor-usage endpoint issue "must not become a template for new analytical endpoints and **should be separately tracked for remediation**"; **§7** states the matrix "**does not itself authorize implementation**".

**Git history inspected** `[FACT]` — last-touching commits for `services/insight_tools.py` (`651f8c1`, `674fe07`), `services/insight_interactions.py` + `insight_context.py` (`f9d91e1`), `data/emissions_logs.py` and `api/v3_emissions.py` (`999e4fb`), `api/insight_authz.py` (`177dff5`), `frontend/src/v3/insight/*` (`09e2315`).

---

## 5. Current I3/I4 baseline

`[FACT]` All verified by reading the source at HEAD `7f97b55`.

### 5.1 I3 — exactly four tools, six statuses, four reference kinds

`domain/insight_tool.py:39-51` → `ToolStatus` = `success, no_data, not_authorized, invalid_input, provider_unavailable, error` (docstring: "no other category may be added").
`domain/insight_tool.py:55-60` → `REFERENCE_KINDS` = `report, report_version, evidence_line_item, calculation_snapshot`.
`services/insight_tools.py:83-123` → `TOOL_DEFINITIONS` = `report_lookup`, `report_version_lookup`, `report_evidence_lookup`, `calculation_snapshot_lookup`; each declares `read_only=True`, `ToolInputSpec`, an `authorization` string ("i2-boundary: authorize_insight_scope + object organisation re-check"), an `output_fields` allowlist and `reference_kinds`.
`services/insight_tools.py:123` → `TOOL_REGISTRY = {d.name: d ...}`; `invoke_tool` (lines 235-272) rejects anything not in the registry with `invalid_input`/`unratified_tool`, then authorizes via `_authorize` → `api.insight_authz.authorize_insight_scope` (lines 223-232).
`services/insight_tools.py:149-173` → `_INTENT_KEYWORDS` (four keyword sets) and `classify_intent` (deterministic; ambiguous ⇒ `invalid_input`/`ambiguous_intent`; unknown ⇒ `invalid_input`/`unsupported_intent`).

### 5.2 I4 — fourteen answer states, no multi-match state

`domain/insight_interaction.py:50-71` → `AnswerStatus` = `success, zero, no_data, not_authorized, insufficient_data, needs_clarification, tool_failure, provider_unavailable, partial, rate_limited, refused, ungrounded, invalid_input, error` (docstring: "must not be merged" with `ToolStatus`).
`domain/insight_interaction.py:84-91` → `ALLOWED_TOOL_STATUSES` (the six I3 values, re-declared for the persistence contract).
`domain/insight_interaction.py:35-40` → `TOOL_ARGUMENT_ALLOWLIST` and `RESULT_METADATA_ALLOWLIST` (Q6): persisted tool arguments are per-tool; result metadata is limited to `status, reason, item_count, truncated, reference_kinds, reference_count, contract_version`.
`services/insight_interactions.py:83-88` → `_TOOL_SCOPE_ARGUMENT` maps only the four tools; `extract_identifiers` (line 174-176) extracts **UUIDs only**; `build_tool_input` (179-190) returns `None` when the required identifier is absent → `needs_clarification` (line 364-366).
`services/insight_interactions.py:216-248` → canonical audit append (`AuditLogger.log_action`, ids/statuses only); `MAX_PROVIDER_ATTEMPTS = 2`; narration only after a `success` tool result (line 416).

---

## 6. Discovery data inventory

`[FACT]` Column facts read from the DDL and repositories at HEAD.

| Dimension | Authoritative data | Where | Type / notes |
| --- | --- | --- | --- |
| date | `calculation_snapshots.date`; `emissions_logs.start_date`/`end_date` | snapshot + log | `DATE NOT NULL` — calendar date, **no time component, no timezone** |
| reporting year | `calculation_snapshots.reporting_year`; factor `reporting_year` | snapshot + factor | `INTEGER NOT NULL` |
| amount (CO₂e) | `calculation_snapshots.co2e_kg`; `emissions_logs.calculated_kg_co2e` | snapshot + log | `NUMERIC NOT NULL CHECK (>= 0)`; results quantised to `RESULT_PRECISION = Decimal("0.000001")` (`domain/factor.py:16,104`) |
| amount (activity) | `calculation_snapshots.quantity` + `quantity_unit`; `emissions_logs.raw_quantity` + `unit` | snapshot + log | `NUMERIC` + unit text; normalised centrally via `core.units.normalize_unit` |
| activity | `calculation_snapshots.activity`, `.activity_type` | snapshot | free text; `activity_type` is the RC2 factor-catalogue label |
| scope | `calculation_snapshots.scope`; `emissions_logs.scope` | snapshot + log | `VARCHAR`/`TEXT`; canonical values `Scope 1/2/3`, `Outside of Scopes` (`SCOPE_ALIASES`, `api/v3_emissions.py:60-71`) |
| supplier | `emissions_logs.supplier_id` (plain nullable `UUID`); `public.suppliers.name` | log only | **never written by application code** (§13); no supplier column on snapshots |
| facility | `emissions_logs.metadata->>'facility_id'` (JSONB key written by `_log_metadata`) | log only | **no facility column on snapshots**; no FK for the JSONB key |
| asset | `emissions_logs.asset_id UUID REFERENCES public.assets(id)` | log only | no asset column on snapshots |
| calculation identity | `calculation_snapshots.id`, `organization_id`, `request_id` | snapshot | UUIDs |
| evidence identifiers | `source_item_id`, `source_line_item_id`, `source_file`, `source_page` | snapshot | UUIDs / text / int |
| factor provenance | `factor_id`, `factor_kind`, `customer_factor_id`, `factor_source`, `factor_set`, `co2e_multiplier`, `methodology`, `algorithm_version`, `content_hash` | snapshot | mixed |

`[FACT]` `list_snapshots(org_id, period, limit=50, offset=0)` already returns `_SNAPSHOT_COLUMNS` (`data/emissions_logs.py:53-59`): a discovery candidate can be fully described (id, activity, quantity+unit, co2e, scope, date, reporting_year, factor provenance, source ids) **without any new query** — only the *filters* and the *contract* are missing.

---

## 7. Discovery capability matrix

| Dimension | Authoritative data exists? | Existing deterministic lookup? | Existing org scoping? | Existing API/tool? | Missing capability | Governance required? |
| --- | --- | --- | --- | --- | --- | --- |
| date / date range | **yes** (`date`, `start_date`/`end_date`, `DATE`) | **yes** — `list_snapshots(org, period, limit, offset)`, `count_snapshots`; `GET /api/v3/emissions/calculations` | **yes** (`organization_id = $1`) | API yes; **Insight tool: no** | a discovery contract whose input is a date/period and whose output is candidates + match count | `[GOV]` timezone semantics |
| amount / CO₂e (+ tolerance) | **yes** (`co2e_kg NUMERIC`, 1e-6 quantisation) | **no** — no SQL filters on `co2e_kg`; no application tolerance helper (only the validation *rounding* tolerance, `engines/validation.py:682`) | n/a | no | amount comparison + **explicit tolerance rule** | `[GOV]` tolerance is a PO product rule (`[REF]` §8.4) |
| activity | **yes** (free text `activity`, `activity_type`) | partial — `aggregate_by_activity` groups by it; `factors.find_by_activity` searches the factor catalogue | yes | API yes; Insight no | a bounded activity **match rule** | `[GOV]` governed meaning/match rule (`[PO]` matrix C-05) |
| supplier | **schema yes; data effectively no** | `aggregate_by_supplier` (group-by only) | yes | API yes; Insight no | persisted emission-level supplier + filter | `[GOV]`/`[BLOCKED]` (`C-06`); **exclude from Package 1** |
| facility / asset | **log-only** (`metadata->>'facility_id'`, `asset_id`) | group-by only | yes | API yes; Insight no | a **filter**; a snapshots↔logs join for snapshot-level candidates | `[GOV]` filter semantics; no schema change |
| scope | **yes** (`scope VARCHAR`) | group-by yes; **filter no** | yes | API yes; Insight no | scope **filter** + value validation | `[GOV]` filter allowlist (`[PO]` C-02) |
| reporting period / year | **yes** (`reporting_year INT`) | group-by `"year"` (from `start_date`); `list_snapshots` filters on `date`, not `reporting_year` | yes | API yes; Insight no | a `reporting_year` filter | `[GOV]` filter allowlist |

### 7.1 The three prompt questions, traced

* **"Why did I have 20,000 kg CO₂e on 2024-02-02?"** — `[FACT]` needs a date filter (exists in SQL, unexposed), an amount comparison (does not exist) and a discovery contract (does not exist). Today: keyword `co2e` matches `calculation_snapshot_lookup`, `build_tool_input` finds no UUID → `needs_clarification`.
* **"Which calculation was approximately 20,000 kg CO₂e?"** — `[FACT]` entirely new behaviour, but one parameterised predicate on an org-indexed table; no new model. `[GOV]` tolerance.
* **"Which diesel calculation at Facility X occurred in February 2024?"** — `[FACT]` free-text activity match (`[GOV]`), facility resolution only through `emissions_logs.metadata->>'facility_id'` (absent from snapshots → logs join), calendar range on `date`. `[INFER]` The most contract-heavy; recommended **out of Package 1**.

---

## 8. Ambiguity analysis

`[FACT]` Current representation of candidate counts:

| Outcome | Current representation | Code |
| --- | --- | --- |
| **Zero candidates** | I3 `no_data` → I4 `no_data`; a zero *result* is the separate I4 `zero` state (never conflated) | `domain/insight_tool.py:47`; `domain/insight_interaction.py:59-60` |
| **One candidate** | I3 `success` with a bounded result set; I4 `success` (`partial` if truncated) | `services/insight_tools.py:283-303` |
| **Multiple candidates** | **Not representable.** No I3 ambiguity status; no I4 `multiple_matches`; adjacent states only (`no_data`, `insufficient_data`, `needs_clarification`) | `domain/insight_tool.py:39-51`; `domain/insight_interaction.py:50-71` |

`[FACT]` The only multi-item signal is `truncated` (`bounded()`, `domain/insight_tool.py:155-159`), which reports that items were dropped — not how many matched.

### 8.1 Decisive constraint discovery — the vocabularies and the tool catalogue are enforced in the database

`[FACT]` The I4 migration hard-codes **both status vocabularies and the four tool names** in CHECK constraints (`supabase/migrations/20261003000000_p8_i4_insight_interactions.sql`), and **no later migration alters them** (grep across all migrations; the only later statement touching that table is `ENABLE ROW LEVEL SECURITY` at line 267):

```sql
CONSTRAINT ci_tool_calls_tool_name_check
    CHECK (tool_name IN ('report_lookup', 'report_version_lookup',
                         'report_evidence_lookup', 'calculation_snapshot_lookup')),  -- lines 156-158
CONSTRAINT ci_tool_calls_tool_status_check
    CHECK (tool_status IN ('success', 'no_data', 'not_authorized',
                           'invalid_input', 'provider_unavailable', 'error')),       -- lines 159-161
CONSTRAINT ci_interactions_answer_status_check
    CHECK (answer_status IS NULL OR answer_status IN (
        'success', 'zero', 'no_data', 'not_authorized', 'insufficient_data',
        'needs_clarification', 'tool_failure', 'provider_unavailable',
        'partial', 'rate_limited', 'refused', 'ungrounded',
        'invalid_input', 'error'))                                                   -- lines 91-96
```

`[FACT]` `record_tool_call()` inserts `tool_name = $4` into that table (`data/insight_interactions.py:99-105`), and `run_interaction` calls it for every executed tool (`services/insight_interactions.py:385-400`).

`[INFER]` **Consequence:** a **fifth tool name** violates `ci_tool_calls_tool_name_check` (Postgres 23514) and cannot be persisted; a **new status value** violates its CHECK. **Package 1 therefore necessarily includes one narrowly-scoped migration** widening the relevant CHECK constraint(s) — the *only* schema change it requires, and it must be explicitly authorized. This **refines** §1: the *computation* needs no schema change; the *persistence contract* does.

### 8.2 Smallest contract change for "multiple matches" — three options

| Option | Change | Class | Migration? |
| --- | --- | --- | --- |
| **A. New I4 `AnswerStatus` value** (`multiple_matches`) | I4 vocabulary + UI + tests | `I4 CONTRACT CHANGE` | **yes** — widen `ci_interactions_answer_status_check` |
| **B. New I3 `ToolStatus` value** | I3 + `ALLOWED_TOOL_STATUSES` + I4 mapping + UI | `BOTH` | **yes** — widen `ci_tool_calls_tool_status_check` |
| **C. Reuse existing states**: `success` + `truncated=true` + `reason="multiple_matches"` + candidate reference list, UI renders a selection prompt | no vocabulary change | `NO CONTRACT CHANGE` | **no** (only the unavoidable tool-name CHECK) |

`[INFER]` Option C is the only representation that leaves both closed vocabularies and their DB CHECKs untouched; its cost is that ambiguity is carried by a documented `reason` rather than a first-class state. `[GOV]` This is a PO decision — `[PO]` D-02/`C-14` require the *outcome*; the *representation* is open.

`[FACT]` Downstream cost if A or B is chosen: `frontend/src/v3/insight/answerStates.js` maps every state (`ANSWER_STATUS_VALUES`, `getAnswerPresentation`); `tests/unit/data/test_i4_insight_migration.py` and `tests/unit/api/test_v3_insight_i4_interactions.py:382` enumerate the vocabulary; the DB CHECK must be widened by migration.

---

## 9. Amount / tolerance analysis

`[FACT]`
* Authoritative amount fields: `calculation_snapshots.co2e_kg` (`NUMERIC`, `CHECK (>= 0)`), `calculation_snapshots.quantity` + `quantity_unit`, `emissions_logs.calculated_kg_co2e` (`NUMERIC`), `emissions_logs.raw_quantity` + `unit`.
* **Recommended discovery field: `calculation_snapshots.co2e_kg` in kg CO₂e** — the snapshot is the immutable forensic record, is org-indexed, and is the same basis the existing I3 snapshot tool exposes. `[INFER]` Matching on `raw_quantity` would mix units (litres, kWh, m³, GBP) and cannot be tolerance-matched meaningfully.
* Precision: results are quantised to `RESULT_PRECISION = Decimal("0.000001")` (`domain/factor.py:16`, applied at `domain/factor.py:104` and `engines/calculation.py:452,466`).
* Comparison semantics for amounts: **none exist.** No `WHERE` clause anywhere compares `co2e_kg`; no tolerance constant or helper exists in application code. The only "tolerance" in the codebase is the validation **recomputation-rounding** tolerance (`engines/validation.py:678-690`: `delta <= RESULT_PRECISION` ⇒ WARNING `CODE_CALC_ROUNDING`) — a different concept, **not reusable** as a discovery tolerance.
* Exact vs approximate: the platform never distinguishes them; there is no "approximate" flag or query form anywhere.

`[GOV]` **Decision required before implementation:** the tolerance definition — absolute (kg CO₂e), relative (%), or both; the default when a user says "approximately"; whether exact match is tolerance zero; and how tolerance interacts with multiple matches. `[BLOCKED]` for the amount dimension until decided (the date/period dimension is not blocked by this).

---

## 10. Date / timezone analysis

`[FACT]`
* Types: `calculation_snapshots.date DATE NOT NULL`; `emissions_logs.start_date DATE NOT NULL` / `end_date DATE NOT NULL`; `calculation_snapshots.calculated_at TIMESTAMPTZ DEFAULT NOW()`.
* Filtering today: `WHERE date BETWEEN $2 AND $3` (`list_snapshots`, `count_snapshots`) and `WHERE l.start_date BETWEEN $2 AND $3` (`find_by_org`, `aggregate`, `aggregate_by_*`); `build_period(start, end)` rejects an inverted range with HTTP 422 (`api/v3_emissions.py:137-144`); `DateRange` is a `date`-only value object (`core/types.py:41-53`).
* Timezone handling for filtering: **none.** The only timezone-aware code is an audit `occurred_at=datetime.now(timezone.utc)` (`api/v3_emissions.py:468,479`). No tz conversion, setting or parameter exists on any query.

`[INFER]` **"On 2024-02-02" already has a deterministic storage-layer meaning** — equality on a `DATE` column via an inclusive range (`start_date = end_date = 2024-02-02`) — and because every date column is timezone-free, that meaning is stable regardless of the caller's timezone. What is missing is a *recorded product rule* stating that interpretation and what "February 2024" means (`2024-02-01 … 2024-02-29` inclusive, calendar month).

`[GOV]` **Decision required:** the date semantics rule — calendar-date equality; inclusive ranges; calendar-month boundaries; and whether `reporting_year` is a selectable dimension distinct from the calendar year of `date`. `[BLOCKED]` for date discovery until recorded; the implementation cost afterwards is a single predicate.

---

## 11. Aggregation capability matrix

`[FACT]` Two methods provide all six approved dimensions, both org- and period-scoped, both positional-parameterised:

| Dimension | Backend aggregation exists? | Exact function/API | Org scoped? | Period scoped? | Filters supported? | Result identifiers? | Evidence linkage? | Insight reachable? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scope | **yes** | `EmissionLogRepository.aggregate(org, period, "scope")` → `by_scope`; `GET /api/v3/emissions/dashboard`, `/scope-breakdown` | **yes** (`organization_id = $1`) | **yes** (`start_date BETWEEN $2 AND $3`) | **none** beyond org+period | **no** (group key + sums only) | per-row only, not from the result | **no** |
| month | **yes** | `aggregate(..., "month")` → `to_char(start_date,'YYYY-MM')`; dashboard `by_month` | yes | yes | none | no | per-row | no |
| year | **yes** | `aggregate(..., "year")` → `to_char(start_date,'YYYY')`; benchmarking uses `GROUP_YEAR` | yes | yes | none | no | per-row | no |
| activity | **yes** | `aggregate_by_activity(org, period)` → groups `cs.activity_type`, returns `row_count`, `SUM(cs.quantity)`, `SUM(cs.co2e_kg)`; dashboard `by_activity` | yes | yes | none | no | via snapshot join only | no |
| asset | **yes** | `aggregate(..., "asset")` → `COALESCE(asset_id::text,'none')`; dashboard `by_asset` | yes | yes | none | no | per-row | no |
| facility | **yes** | `aggregate(..., "facility")` → `COALESCE(metadata->>'facility_id','none')`; dashboard `by_facility` | yes | yes | none | no | per-row | no |

`[FACT]` Return shape: `aggregate()` returns `EmissionsAggregate{organization_id, period, group_by, total_co2e_kg, total_rows, by_scope, by_group}` — **CO₂e only, no quantity**; `aggregate_by_activity`/`aggregate_by_supplier` return raw dict rows `{key, row_count, quantity, co2e_kg}`. Only `aggregate()`'s `by_scope`/`by_group` are unit-safe (kg CO₂e); `SUM(quantity)` in the other two **mixes units** (`[FACT]` — no unit is in the group key), which conflicts with `[PO]` D-03's "deterministic units/basis" requirement.

`[INFER]` **All six approved dimensions are therefore already computable**; Package 1 does not need new aggregation SQL for their *values*, only (a) a contract that exposes them to Insight, (b) a unit-safe basis rule, and (c) the group-key display mapping (asset/facility keys are UUIDs or `'none'`; names live in the assets/facilities repositories).

---

## 12. Filter / cross-tab analysis

`[FACT]` What the backend can support today without becoming a general-purpose query engine:

| Filter | Exists today? | Where |
| --- | --- | --- |
| organization | **yes** | `organization_id = $1` in every aggregate/list |
| start date / end date | **yes** | `DateRange` + `BETWEEN $2 AND $3`; `build_period` validates order (422) |
| scope | **no** — scope is a *group-by dimension*, never a predicate | `_GROUP_EXPRESSIONS["scope"]` |
| activity | **no** (predicate); group-by yes | `aggregate_by_activity` groups only |
| asset | **no** (predicate); group-by yes | `_GROUP_EXPRESSIONS["asset"]` |
| facility | **no** (predicate); group-by yes | `_GROUP_EXPRESSIONS["facility"]` |
| reporting year | **no** as a predicate; group-by `"year"` derives it from `start_date` | `_GROUP_EXPRESSIONS["year"]` |
| result limit | **partially** — `list_snapshots` takes `limit`/`offset`; `aggregate()` returns **all** groups (no limit) | `data/emissions_logs.py:295-314` |

`[FACT]` `group_by` is validated against the fixed `_GROUP_EXPRESSIONS` allowlist and raises on anything else (`data/emissions_logs.py:175-179`) — the anti-injection mechanism is "closed dimension map", which any new filter/dimension must also use.

**"Scope 1 by facility"** `[INFER]` requires **a new bounded filter, not a new group-by and not a cross-tab engine**: the group-by `facility` already exists, so the only missing piece is one equality predicate (`AND scope = $n`). A second grouping dimension simultaneously (e.g. scope × facility in one call) would be a **new cross-tab capability**, which is *not* required by `[PO]` D-03's initial dimension list and should be excluded from Package 1.

`[GOV]` The filter allowlist (which predicates may be combined, and whether a filter may accompany a grouping dimension) must be authorized as part of the aggregation contract — `[PO]` D-03 requires "fixed dimension/filter allowlists" without specifying the list.

---

## 13. Aggregate provenance analysis

`[FACT]` Exact response content today:

| Method | Returns | Contains snapshot/log/source ids? |
| --- | --- | --- |
| `aggregate()` | `EmissionsAggregate{organization_id, period, group_by, total_co2e_kg, total_rows, by_scope{key→kg}, by_group{key→kg}}` | **no** |
| `aggregate_by_activity()` | rows `{activity_type, row_count, quantity, co2e_kg}` | **no** |
| `aggregate_by_supplier()` | rows `{supplier_id, supplier_name, row_count, quantity, co2e_kg}` | supplier id only |
| `/dashboard`, `/scope-breakdown` | the above JSON-ified | **no** |

`[FACT]` Therefore **an aggregate result cannot currently answer "which calculation records make up this number?"** — no `snapshot_id`, `emission_log_id`, `source_item_id`, `evidence_line_item_id`, document id, page, row, report version or factor id is returned (see the evidence-traceability matrix in the question-library report: aggregate trace = PARTIAL/NO).

`[INFER]` **Smallest bounded provenance contract required:** one org-scoped, dimension-aware read — *"given (dimension, group key, period, limit), return the N contributing calculation snapshot ids ordered deterministically"* — reusing the existing `_GROUP_EXPRESSIONS` mapping for the predicate and the existing snapshot allowlist for the returned fields. No new table, no new index requirement (the aggregates already scan the same rows), no schema change.

`[FACT]` **Identifiers-first is the safe design and is compatible with the existing DM-6 machinery**: the aggregate provenance result can return only bounded identifiers (snapshot id + date + activity + co2e), after which each id resolves through the *already authorized* paths (`calculation_snapshot_lookup`; `GET /{log_id}/evidence`; the viewer route `/evidence/line-items/{id}` with DM-6 depth + `evidence.line_access` audit). `[PO]` D-10 is satisfied by this shape, and it keeps raw source content and signed URLs out of any LLM payload by construction.

`[GOV]` The bound (how many contributing records may be returned, and whether deeper paging is allowed) is part of the aggregate→evidence contract decision.

---

## 14. Tenant / security analysis

`[FACT]` Every lookup/aggregation that could become Insight-reachable was inspected:

| Object | Organization predicate | API-level authorization | Notes |
| --- | --- | --- | --- |
| `aggregate`, `aggregate_by_activity`, `aggregate_by_supplier`, `count_snapshots`, `list_snapshots`, `find_by_org`, `count_by_scope`, `list_for_line` | **yes** (`organization_id = $1` in SQL) | `require_org_member()` + `ensure_org_access` on the emissions routes; consultant routes via `_authorized_client_org` | safe template |
| `get_snapshot(snapshot_id)` | **no predicate** (by id) | post-read `ensure_org_access(current_user, row["organization_id"])` in `calculation_detail` | caller-scoped; discipline must be preserved |
| `list_for_file(file_id)` | **no predicate** (by id) | caller asserts org on the log first (D33 route) | caller-scoped |
| `snapshot_count_for_factor(factor_id)` | **no predicate** (platform-wide) | `GET /api/v3/emissions/factors/{factor_id}` requires only `require_org_member()` and does **not** re-check the factor's org (factors are global) | **cross-tenant metadata: platform-wide usage counts + first/last `calculated_at`** |
| `factor_usage_span(factor_id)` | **no predicate** (platform-wide) | same endpoint | as above |
| joins (`aggregate_by_activity`, `find_by_org`→snapshot, D33 evidence join) | the driving table is org-filtered; joined tables are reached through org-owned keys | routes assert org | no cross-tenant reach observed |
| evidence access | viewer route asserts org **in SQL and in the API**; DM-6 depth gates the document pointer; access audited | `api/v3_evidence.py:103+` | safe |

**The previously reported factor-usage issue is CONFIRMED** `[FACT]` (`data/emissions_logs.py:387-409`: no `organization_id` in either query; exposed via `api/v3_emissions.py:618-647`).

**Assessment for the proposed foundation** `[INFER]`:
* It **does not affect the proposed Package 1 surfaces** — discovery and aggregation over `calculation_snapshots`/`emissions_logs` are org-scoped by construction, and the factor endpoints are not part of the package.
* It **must not block** Package 1: `[PO]` the decision matrix §5 already states it "must not become a template for new analytical endpoints and **should be separately tracked for remediation**".
* It **does not need fixing in this task** and cannot be fixed here (read-only). `[GOV]` It should be carried as its own remediation item; any new analytical endpoint must include the organization predicate by design.

`[FACT]` Additional security properties relevant to the package: no SQL is generated from model output anywhere; `invoke_tool` rejects unratified names; all aggregates are positional-parameterised; `limit`/`offset` bounds exist on list routes (`Query(..., ge=, le=)`); rate limiting remains **absent** (`middleware/rate_limit.py` unregistered; `rate_limited` never produced) — `[PO]` D-14 requires rate limiting before scaling customer-facing analytical surfaces, and the PO has **not** issued a concrete I8 authorization, so Package 1 must carry the absence explicitly and must not implement it.

---

## 15. LLM boundary analysis

`[FACT]` Exact path: `run_interaction` executes one tool, projects the result, then (only when `status == "success"` and `narration != "none"`) builds the prompt from `_bounded_context(payload)` — which contains **only** `tool`, `status`, `reason`, `data` (the tool's allowlisted output) and `references` — truncated to `MAX_NARRATION_CONTEXT_CHARS = 2000` (`services/insight_interactions.py:67,193-206`), plus the bounded I5 historical context and the first 500 characters of the question (`:439-447`). The system prompt is a constant that forbids inventing values and claiming authority (`:69-75`).

`[FACT]` Reusable allowlists that already keep protected content away from the model:
* tool output allowlists (`_SNAPSHOT_FIELDS`, `_EVIDENCE_LINE_FIELDS`, `_REPORT_FIELDS`, `_REPORT_VERSION_FIELDS`, `_COVERAGE_FIELDS`, `services/insight_tools.py:54-81`) — raw extracted text, `source_file`, `source_page`, artefact URLs and actors are excluded;
* persistence allowlists (Q6): `TOOL_ARGUMENT_ALLOWLIST`, `RESULT_METADATA_ALLOWLIST` (`domain/insight_interaction.py:35-50`);
* I5 projection allowlist for historical tool calls (`services/insight_context.py:67-75`);
* `MAX_QUESTION_LENGTH = 2000`, `MAX_IDEMPOTENCY_KEY_LENGTH = 128`, `MAX_PROVIDER_ATTEMPTS = 2`.

`[INFER]` **Minimum safe payload for future discovery/aggregation narration** (derived, not invented): per candidate/group — the dimension label, the group key *display name* (resolved server-side, e.g. facility name not raw UUID where the caller is authorized), CO₂e in kg, row count, the explicit period/basis statement, and identifiers only if they are already allowlisted for that tool. Explicitly **excluded**: raw source documents, `raw_description`/`raw_quantity`/`raw_unit`, signed URLs, storage paths, other tenants' rows, and unrestricted DB rows.

`[GOV]` The narration payload for aggregates/discovery must be authorized as part of the tool contract (which fields the model may see), and it must be enforced by an allowlist rather than by prompt wording. **No LLM-boundary change is proposed in this preflight and none is authorized.**

---

## 16. I3 contract impact

`[FACT]` Baseline: four tools, six statuses, four reference kinds; the DB CHECK on `tool_name` enumerates the same four names (§8.1).

| Required change | Classification |
| --- | --- |
| Add a **discovery tool** (typed bounded request: date/period, amount+tolerance, activity, scope, reporting_year — excluding supplier/facility in Package 1) | **`I3 CONTRACT CHANGE`** (new tool: `ToolDefinition`, `ToolInputSpec`, `output_fields`, `reference_kinds`, registry entry) + **migration** (widen `ci_tool_calls_tool_name_check`) |
| Add an **aggregation tool** (dimension allowlist from the existing six; bounded period; bounded group count) | **`I3 CONTRACT CHANGE`** + same migration |
| Add an **aggregate→evidence tool** (dimension + group key + period → bounded snapshot ids) | **`I3 CONTRACT CHANGE`** + same migration |
| New parameters on existing tools (e.g. widening `calculation_snapshot_lookup`) | **`I3 CONTRACT CHANGE`** — and the closed catalogue decision (`[PO]` §3.5 "No new I3 tool is authorized by this record") means widening is *also* a PO decision, not an implementation detail |
| Reference kinds | `[FACT]` `REFERENCE_KINDS` already includes `calculation_snapshot` (and `evidence_line_item`), so discovery/aggregation results can return existing reference kinds **without** changing the reference vocabulary `[INFER]` |
| New authorization checks | **none required** `[FACT]` — every tool already delegates to `_authorize → authorize_insight_scope` and re-checks the object's organization (`services/insight_tools.py:223-254,288-289,357-363`); new tools must reuse exactly that pattern |
| New result schemas | **`I3 CONTRACT CHANGE`** (each tool's `output_fields` allowlist) — plus, if the new results are persisted, entries in `TOOL_ARGUMENT_ALLOWLIST`/`RESULT_METADATA_ALLOWLIST` (**I4 change**, see §17) |

`[INFER]` The I3 changes are *additive* (new definitions + registry entries + allowlists); no existing tool's semantics, input or output need to change, which keeps the closed decisions intact in substance while still requiring the PO's explicit authorization for the catalogue change.

---

## 17. I4 contract impact

| Question | Finding |
| --- | --- |
| Is a new `AnswerStatus` **required**? | `[INFER]` **No — not strictly.** Zero → `no_data`/`zero`; one → `success`; invalid → `invalid_input`; unauthorized → `not_authorized`; provider issues → `provider_unavailable`; failure → `error`/`tool_failure` all already exist. Only **multiple matches** lacks a first-class state, and it can be represented either by a new value (Option A/B in §8.2) or by tool-level `reason` + `truncated` + references (Option C). `[GOV]` PO decision. |
| Is `multiple_matches` required? | `[PO]` D-02/`C-14` require the **outcome** ("zero/one/multiple state"); the **vocabulary change** is not mandated. `[GOV]` |
| Audit payload changes | `[FACT]` none required if new tools reuse the existing pattern: `record_tool_call` (allowlisted arguments + result metadata + hashes + truncation + duration) and the canonical `audit_trail` append (`insight.interaction.{lifecycle}` with answer status, tool statuses, tool-call ids, narration state). New tools must extend the two allowlist dicts — arguably an **I4 persistence-contract change** even though the *state* vocabulary is untouched. Classification: **`I4 CONTRACT CHANGE`** (allowlists only). |
| Interaction metadata changes | `[FACT]` none: `InteractionOutcome` already carries tool calls and references generically; `intent` is a free string persisted as the tool name or refusal reason (`intent_source` ∈ `{deterministic, none}` per the DB CHECK). `[INFER]` A discovery tool's selection is still "deterministic" ⇒ **no change**. |
| `truncated`/`partial` semantics | `[FACT]` already supported end-to-end (tool `truncated` → `AnswerStatus.PARTIAL` via `combine_answer_statuses`) ⇒ reusable for bounded aggregate/discovery result caps. **No change.** |
| `rate_limited` | `[FACT]` declared, DB-permitted, and **never produced**; `[PO]` D-14 forbids implementing rate limiting now ⇒ **no change**, and Package 1 must not claim the state is reachable. |

**Net classification for Package 1: `I3 CONTRACT CHANGE` (new tools) + `I4 CONTRACT CHANGE` (allowlist entries; vocabulary only if the PO chooses a new state) + one migration widening `ci_tool_calls_tool_name_check` (and `answer_status`/`tool_status` CHECKs if a new state is chosen).**

---

## 18. UI impact

`[FACT]` Current Insight UI: `frontend/src/v3/insight/InsightPage.jsx`, `AnswerCard.jsx`, `answerStates.js` (`ANSWER_STATUS_VALUES`, `getAnswerPresentation`), `ReferenceList.jsx`, plus history/detail views; tests `insight-answer-states.test.js` (15), `insight-page.test.jsx` (31), `insight-references.test.jsx` (15).

**Required for the foundation** (the UI cannot be correct without these):
* presentation for the discovery tool's **zero / one / multiple** outcomes and for aggregate group rows (the existing answer card renders bounded rows already — this is presentation, not architecture);
* a **bounded** rendering of aggregate rows and of the candidate list when several match;
* explicit display of the answer **basis/period** so an aggregate is never presented as an unqualified total.

**Future / downstream (explicitly out of Package 1)**: multiple-match *selection* workflow (choose a candidate, re-ask); aggregate→evidence drill-down navigation; comparison/variance rendering; Scope 3 / supplier / Scope 1–2 dimension pickers; concept-answer cards; clarification dialogs beyond the existing `needs_clarification` presentation; new loading states beyond the existing lifecycle (`received/executing/completed/failed`).

`[INFER]` If the PO chooses Option A/B (§8.2), `answerStates.js` gains a state and its test must grow; if Option C is chosen, **no new UI state is required** — existing `success`/`partial` presentations plus the candidate list suffice, which is the cheapest foundation.

---

## 19. Testing requirements

`[FACT]` Existing Insight coverage (test-function counts at HEAD): `test_v3_insight_i2_authorization.py` 29, `i3_tools.py` 23, `i3_wiring.py` 5, `i4_interactions.py` 17, `i4_wiring.py` 4, `i5_context_integration.py` 6, `insight_endpoints.py` 8, `services/test_insight_i5_context.py` 18, `data/test_i2_insight_rls_live.py` 5 (+ `test_i4_insight_migration.py`, `test_source_evidence_viewer.py` 22, `test_v3_emissions.py` 13); frontend 61 assertions across three suites.

`[INFER]` Minimum tests an implementation package would need (none written here):

* **Unit** — discovery parameter validation (tolerance bounds, inverted range, unknown dimension); aggregate dimension rejection; group-key formatting; unit/basis statement construction.
* **Service/contract** — new `ToolDefinition`s registered and `invoke_tool` rejects unknown names; result-schema allowlists enforced; persistence allowlists accept the new tools; `bounded()` truncation propagation.
* **API** — `POST /api/v3/insight/interactions` end-to-end for a discovery and an aggregation question; invalid parameters → `invalid_input`; empty aggregate → `no_data`; unauthorized org → `not_authorized`; existing four tools regress cleanly.
* **Security/tenant isolation** — customer A cannot discover/aggregate B's records (the caller's org comes from the session, never the request body); consultant client scoping; PE/internal negatives unchanged.
* **Evidence/provenance** — aggregate → component snapshot ids for all six dimensions; returned ids resolve through existing snapshot/evidence paths; empty group returns none.
* **Insight integration** — zero/one/multiple flows; `truncated` → `partial`; narration receives no raw source content and **no signed URL** (assert on the prompt payload, as existing suites already do); historical-context projection unaffected.
* **UI** — rendering of the new outcomes and bounded rows; no new state if Option C is chosen.
* **Negative/ambiguity** — two questions in one; amount with no tolerance; date without a year; unsupported dimension; cross-org id smuggling; unratified tool name; oversized limit.

---

## 20. Dependency analysis

`[INFER]` **Discovery + Aggregation Foundation can be implemented before every listed capability**, with these precise exceptions:

| Candidate prerequisite | Verdict | Evidence |
| --- | --- | --- |
| Scope 3 category model | **Not a prerequisite** | dimensions are the existing six; scope grouping uses the existing `scope` column |
| Supplier persistence (`C-06`) | **Prerequisite for the supplier dimension only** | `emissions_logs.supplier_id` is never written ⇒ supplier excluded from Package 1 |
| Supplier analytics (`C-07`) | **Not a prerequisite** | depends on `C-06`; excluded |
| Scope 1 decomposition | **Not a prerequisite** | no decomposition column exists or is needed |
| Market-based Scope 2 | **Not a prerequisite** | `SCOPE2_METHODS` lives only in `domain/disclosure.py`; no method dimension needed |
| Primary/secondary classification | **Not a prerequisite** | not referenced by any aggregation |
| Variance attribution | **Not a prerequisite** | needs two period aggregates, both already computable |
| Factor-history enhancement | **Not a prerequisite** | discovery uses the snapshot's existing factor fields |
| Consultant / auditor Insight | **Not a prerequisite** | I2 already supports consultant client scoping through the same boundary |
| Concept/RAG answers | **Not a prerequisite** | independent capability |
| **I7 / rate limiting** | **Not a capability prerequisite, but `[PO]` D-14 declares it required before scaling** | `[GOV]` the PO must decide whether Package 1 may ship a customer-facing analytical surface ahead of I8 |
| **I8 (full)** | **Not a prerequisite** | no I8 authorization exists |
| **Migration widening the tool-name CHECK** | **Unavoidable prerequisite** | §8.1 — a new tool cannot be persisted otherwise |

`[INFER]` No dependency *invalidates* the Package 1 boundary; the two that change its composition are the **migration** (must be inside) and the **supplier exclusion** (must be outside).

---

## 21. Smallest proposed implementation package

`[INFER]` Derived strictly from the code evidence above. **Proposal only — not authorized.**

| Unit | Purpose | Existing code reused | New code likely required | Contract impact | Schema impact | Security impact | OHD verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **U1 — Discovery operation (bounded, typed)** | Answer "which calculation(s) match these typed criteria" over calculation snapshots: date/period, `reporting_year`, amount (kg CO₂e) + tolerance, activity, scope | `list_snapshots`/`count_snapshots` SQL shape; `_SNAPSHOT_COLUMNS`; `build_period`; `DateRange`; `normalize_unit` | a parameterised discovery query (allowlisted predicates only; org from session; deterministic ORDER BY; hard result bound; total match count) | `I3 CONTRACT CHANGE` (new tool + input spec + output allowlist) | none beyond the tool-name migration | org predicate mandatory; amount predicate parameterised; no arbitrary SQL | zero / one / multiple; tolerance boundary; date boundary; cross-tenant denial |
| **U2 — Aggregation operation (bounded, typed)** | Answer "CO₂e by ⟨scope \| month \| year \| activity \| asset \| facility⟩ for period P" | `aggregate()` (5 dimensions), `aggregate_by_activity()`, `_GROUP_EXPRESSIONS` allowlist, `build_period` | thin bounded wrapper: dimension allowlist, period bound, group-count cap, unit/basis statement, display-name resolution for asset/facility keys, unit-safe basis (CO₂e always; quantity only when a unit is in the group key) | `I3 CONTRACT CHANGE` | none | dimension allowlist is the injection defence; org from session | each of six dimensions; empty group; unbounded-era regression |
| **U3 — Bounded aggregate provenance** | Satisfy `[PO]` D-10: return the contributing calculation snapshots for one aggregate cell | `_GROUP_EXPRESSIONS` for the predicate; snapshot id/date/activity/co2e fields | one org-scoped bounded id query + deterministic ordering | `I3 CONTRACT CHANGE` | none | bounded identifiers only; evidence resolved later through existing authorized paths | ids resolve; bound enforced; no raw content leaked |
| **U4 — Vocabulary migration (unavoidable)** | Make a new tool name persistable in the I4 tool-call ledger | `20261003000000_p8_i4_insight_interactions.sql` constraint style | one migration widening `ci_tool_calls_tool_name_check` (+ `ci_tool_calls_tool_status_check` / `ci_interactions_answer_status_check` **only if** the PO chooses a new state) | none | **yes — migration** | narrow widening only; RLS untouched | migration applies cleanly; CHECK rejects unknown names |
| **U5 — I4 persistence allowlist entries** | Persist the new tools' arguments/result metadata under Q6 rules | `TOOL_ARGUMENT_ALLOWLIST`, `RESULT_METADATA_ALLOWLIST` | two dict entries | `I4 CONTRACT CHANGE` (allowlists) | none | no raw identifiers or content beyond existing allowlists | allowlist rejection tests |
| **U6 — Ambiguity representation (per PO decision)** | Distinguish multiple matches | existing `truncated`, `reason`, `references`, `partial` | Option C: none (documentation + tests). Option A/B: new state + UI + migration | `NO CONTRACT CHANGE` (C) / `I4 CONTRACT CHANGE` (A) / `BOTH` (B) | none (C) / migration (A/B) | none | ambiguity test matrix |
| **U7 — Tests** | §19 coverage | existing suites as templates | new unit/API/security/provenance/UI tests | none | none | negative tests required | full suite + targeted negatives |
| **U8 — Permanent implementation report** | Record scope, files, migration, tests, exclusions, remaining limits | this document's structure | one report | none | none | states unreachable `rate_limited` honestly | report review |

`[INFER]` **Explicitly not in Package 1:** utterance→parameter extraction beyond what is already deterministic (the ambiguity of a natural-language question mapped to typed parameters is itself `[GOV]`; the minimal safe form is typed parameters supplied by the caller/UI, which is what the I3 input spec already models).

### 21.1 Required summary table

| Capability | Authoritative data | Deterministic backend | Existing Insight contract | Security/tenant safe | Evidence/provenance | New contract required | Schema change required | Package 1? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Discovery | yes (`calculation_snapshots`: date, co2e_kg, activity, scope, reporting_year; logs for facility/asset) | **partial** — date/period only; no amount comparison; no tolerance helper | **no** (no tool; UUID-only extraction) | yes if org predicate is used (session-derived) | candidate-level yes (snapshot fields incl. source ids) | **yes — I3** (+ I4 allowlists) | **yes** (tool-name CHECK) | **yes** |
| Scope aggregation | yes (`scope`) | **yes** (`aggregate("scope")`, `by_scope`) | no | yes | **no** (needs U3) | yes — I3 | yes (tool-name CHECK) | **yes** |
| Month aggregation | yes (`start_date`) | **yes** (`to_char(...,'YYYY-MM')`) | no | yes | **no** (needs U3) | yes — I3 | yes | **yes** |
| Year aggregation | yes (`start_date`, `reporting_year`) | **yes** (`to_char(...,'YYYY')`) | no | yes | **no** (needs U3) | yes — I3 | yes | **yes** |
| Activity aggregation | yes (`activity_type`) | **yes** (`aggregate_by_activity`; `SUM(quantity)` mixes units → basis rule needed) | no | yes | **no** (needs U3) | yes — I3 | yes | **yes (with unit-safe basis)** |
| Asset aggregation | yes (log `asset_id`) | **yes** (`aggregate("asset")`) | no | yes | **no** (needs U3) | yes — I3 | yes | **yes** |
| Facility aggregation | yes (log `metadata->>'facility_id'`) | **yes** (`aggregate("facility")`) | no | yes | **no** (needs U3) | yes — I3 | yes | **yes** |
| Aggregate → evidence | yes (snapshot ids resolvable via existing paths) | **no** (aggregates return no ids) | no | yes if bounded and org-scoped | identifiers-first + DM-6 resolution | yes — I3 | yes (tool-name CHECK) | **yes** |

---

## 22. Explicit exclusions (Package 1 hard exclusion list)

`[FACT]`/`[INFER]` Each item below is **out of Package 1**. Where the item is genuinely a prerequisite it is stated.

| Excluded | Reason it is excluded | Is it secretly a prerequisite? |
| --- | --- | --- |
| **Scope 3 categories 1–15** | no first-class dimension exists anywhere (disclosure carries only `scope_hint`); `[PO]` `C-03` requires a versioned taxonomy first | **no** — the six approved dimensions do not need it |
| **Supplier persistence** | `emissions_logs.supplier_id` is never written by any application path; `[PO]` `C-06` requires confidence/approval/backfill decisions | **only for the supplier dimension** — excluded from Package 1 |
| **Supplier analytics / supplier variance** | depend on `C-06`; `[PO]` `C-07` conditional, `C-08` later | no |
| **Scope 1 decomposition (combustion/fugitive/process)** | no such column or rule exists; `[PO]` `C-16` approves the capability separately | no |
| **Market-based Scope 2** | `SCOPE2_METHODS` exists only in `domain/disclosure.py` + `scope2_method_hint`; no instruments register, no residual mix, no market-based totals | no |
| **Primary/secondary data classification** | no flag exists (only `methodology='spend_based'` and extraction confidence); `[PO]` `C-13` approves a separate taxonomy | no |
| **Variance / factor-change attribution** | no comparison or attribution engine exists; `[PO]` `C-10`/`C-11` require methodology decisions first | no |
| **Factor-history redesign** | `[PO]` `C-09`/`§3.10` is its own workstream; Package 1 uses the snapshot's existing factor fields | no |
| **Consultant Insight surface** | `[PO]` matrix §4 item 14 — only after separate PO decisions; I6 §F already lists it as a follow-up | no |
| **Auditor Insight surface** | same as above | no |
| **Concept / RAG answers** | `[PO]` matrix §3.11 "APPROVED FUTURE"; requires a governed, versioned knowledge layer | no |
| **Rate limiting (I7)** | `[PO]` D-14 states rate limiting is required before scaling but **no concrete I8 authorization has been issued**; must not be implemented here | no — but `[GOV]` the PO must accept shipping an analytical surface ahead of it |
| **I7 / full I8** | not authorized | no |
| **Production / investor-demo deployment** | separate release authorization; §55 demo-safety invariants | no |
| **Cross-tab (two dimensions at once)** | not required by `[PO]` D-03's initial dimension list; would constitute a new capability | no |
| **NL → typed parameter extraction for discovery** | `[GOV]` — the LLM must not become a query engine or authorization layer (`[PO]` D-01); the minimal safe form supplies typed parameters at the tool boundary | not for the typed contract; is for a fully natural-language discovery experience |
| **Any RLS / authorization / Source Evidence Viewer / Insight UI architecture change** | frozen or separately authorized | no |

---

## 23. Governance decisions still required

`[GOV]` Prerequisites for an implementation authorization (none resolved by this preflight):

1. **G-1 — Migration authorization.** Explicit authorization for one migration widening `ci_tool_calls_tool_name_check` (and, if a new state is chosen, the corresponding status CHECK). Without it, no new tool can be persisted (§8.1). `[BLOCKED]`
2. **G-2 — I3 catalogue change.** Authorization to add tool(s) to the closed four-tool catalogue (`[PO]` §3.5 authorized no new I3 tool; D-02/D-03 approve discovery/aggregation in principle only).
3. **G-3 — Ambiguity representation.** Option A (new I4 state), B (new I3 status) or C (reuse `truncated`+`reason`). Decides whether a second CHECK must be widened and whether the UI gains a state. `[BLOCKED]` for the multiple-match outcome.
4. **G-4 — Amount tolerance rule.** Absolute / relative / both; default; exact-match semantics. `[BLOCKED]` for amount discovery.
5. **G-5 — Date semantics rule.** Calendar-date equality; inclusive ranges; month boundaries; `reporting_year` vs calendar year as separate dimensions. `[BLOCKED]` for date discovery.
6. **G-6 — Filter allowlist.** Which predicates may be combined with which dimensions (e.g. `scope` filter + `facility` grouping), and the result/group bounds.
7. **G-7 — Basis/unit rule for aggregation.** CO₂e always in kg; `SUM(quantity)` allowed only with a unit in the group key (current `aggregate_by_activity`/`_by_supplier` do not satisfy `[PO]` D-03's "deterministic units/basis").
8. **G-8 — Discovery dimension scope for Package 1.** Confirm the exclusion of supplier and (optionally) facility from the first package.
9. **G-9 — Aggregate→evidence bound** and whether identifiers-first resolution is the accepted D-10 shape.
10. **G-10 — Narration payload allowlist** for the new tools (what the model may see).
11. **G-11 — Ordering of Package 1 against rate limiting** (`[PO]` D-14 vs a customer-facing analytical surface).
12. **G-12 — I4 persistence allowlist change** acceptance (Q6 rule).
13. **G-13 — Status of the factor-usage cross-tenant issue**: package it as separate remediation (`[PO]` matrix §5 already says "separately tracked") and confirm it is **not** a Package 1 gate.
14. **G-14 — Acceptance criteria** for the package (ODH verification scope: which of §19's suites must be independently re-run).

---

## 24. Exact inspected files

**Backend (read at HEAD `7f97b55`)**
* `backend/domain/insight_tool.py` — `ToolStatus`, `REFERENCE_KINDS`, `bounded()`, `ToolInputSpec`, `ToolDefinition`
* `backend/domain/insight_interaction.py` — `AnswerStatus`, `NarrationState`, `ALLOWED_TOOL_STATUSES`, Q6 allowlists, `combine_answer_statuses`
* `backend/services/insight_tools.py` — `TOOL_DEFINITIONS`, `TOOL_REGISTRY`, `invoke_tool`, `_authorize`, `classify_intent`, `_INTENT_KEYWORDS`, field allowlists
* `backend/services/insight_interactions.py` — orchestration, `_bounded_context`, `_TOOL_SCOPE_ARGUMENT`, `extract_identifiers`, `build_tool_input`, canonical audit, narration gating
* `backend/services/insight_context.py` — I5 historical context projection
* `backend/api/insight_authz.py` — I2 boundary (`authorize_insight_scope`, org predicates)
* `backend/api/v3_insight_interactions.py` — interaction API
* `backend/api/v3_emissions.py` — `build_period`, `SCOPE_ALIASES`, dashboard/scope-breakdown/calculations/factors/evidence/verify routes
* `backend/api/v3_evidence.py` — viewer + DM-6 gating (referenced for provenance paths)
* `backend/data/emissions_logs.py` — `_GROUP_EXPRESSIONS`, `aggregate`, `count_by_scope`, `aggregate_by_supplier`, `aggregate_by_activity`, `count_snapshots`, `list_snapshots`, `get_snapshot`, `find_by_org`, `list_for_line`, `snapshot_count_for_factor`, `factor_usage_span`
* `backend/data/insight_interactions.py` — `record_tool_call` INSERT + persistence
* `backend/engines/calculation.py`, `backend/engines/validation.py` — precision and the recomputation rounding tolerance
* `backend/domain/factor.py` — `RESULT_PRECISION`

**Migrations**
* `supabase/migrations/00000000000000_init_schema.sql` — `emissions_logs` DDL (`start_date`/`end_date`/`raw_quantity`/`calculated_kg_co2e`/`metadata`/`supplier_id`/`asset_id`)
* `supabase/migrations/20260807020000_add_calculation_snapshots.sql` — `calculation_snapshots` DDL
* `supabase/migrations/20261003000000_p8_i4_insight_interactions.sql` — the three CHECK constraints (§8.1), RLS enablement

**Frontend**
* `frontend/src/v3/insight/answerStates.js`, `InsightPage.jsx`, `AnswerCard.jsx`, `ReferenceList.jsx`
* `frontend/src/v3/__tests__/insight-answer-states.test.js`, `insight-page.test.jsx`, `insight-references.test.jsx`

**Tests (counted, not modified)**
* `backend/tests/unit/api/test_v3_insight_i2_authorization.py`, `test_v3_insight_i3_tools.py`, `test_v3_insight_i3_wiring.py`, `test_v3_insight_i4_interactions.py`, `test_v3_insight_i4_wiring.py`, `test_v3_insight_i5_context_integration.py`, `test_v3_insight_endpoints.py`
* `backend/tests/unit/services/test_insight_i5_context.py`, `backend/tests/unit/data/test_i2_insight_rls_live.py`, `backend/tests/unit/data/test_i4_insight_migration.py`
* `backend/tests/unit/api/test_source_evidence_viewer.py`, `backend/tests/unit/api/test_v3_emissions.py`

**Documents** — §4 above (ten documents).

## 25. Exact relevant code locations

| Finding | Location |
| --- | --- |
| Closed I3 status vocabulary | `backend/domain/insight_tool.py:39-51` |
| Reference kinds | `backend/domain/insight_tool.py:55-60` |
| Result bounding | `backend/domain/insight_tool.py:155-159` |
| Four tool definitions + output allowlists | `backend/services/insight_tools.py:54-123` |
| Registry + unratified-tool rejection | `backend/services/insight_tools.py:123`, `:235-272` |
| Intent keywords + deterministic classification | `backend/services/insight_tools.py:144-173` |
| Per-tool authorization reuse | `backend/services/insight_tools.py:223-254`, `:288-289`, `:357-363` |
| Closed I4 vocabulary | `backend/domain/insight_interaction.py:50-71` |
| `ALLOWED_TOOL_STATUSES` | `backend/domain/insight_interaction.py:84-91` |
| Q6 allowlists | `backend/domain/insight_interaction.py:35-50` |
| UUID-only parameter extraction | `backend/services/insight_interactions.py:174-190` |
| `needs_clarification` on missing identifier | `backend/services/insight_interactions.py:364-366` |
| Narration context cap + projection | `backend/services/insight_interactions.py:67`, `:193-206` |
| Audit append | `backend/services/insight_interactions.py:216-248` |
| Aggregation dimension allowlist | `backend/data/emissions_logs.py:40-46` |
| `aggregate` + allowlist enforcement | `backend/data/emissions_logs.py:171-224` (guard at `:175-179`) |
| `count_by_scope`, `aggregate_by_supplier`, `aggregate_by_activity` | `backend/data/emissions_logs.py:225-283` |
| `count_snapshots`, `list_snapshots` | `backend/data/emissions_logs.py:284-314` |
| `snapshot_count_for_factor`, `factor_usage_span` | `backend/data/emissions_logs.py:~387-409` |
| Tool-call persistence INSERT | `backend/data/insight_interactions.py:99-106` |
| `build_period` (422 on inverted range) | `backend/api/v3_emissions.py:137-144` |
| Scope vocabulary | `backend/api/v3_emissions.py:60-71` |
| Factor usage endpoint | `backend/api/v3_emissions.py:618-647` |
| `RESULT_PRECISION` | `backend/domain/factor.py:16`, applied `:104` |
| Validation rounding tolerance | `backend/engines/validation.py:670-690` |
| **Tool-name CHECK** | `supabase/migrations/20261003000000_p8_i4_insight_interactions.sql:156-158` |
| **Tool-status CHECK** | same file `:159-161` |
| **Answer-status CHECK** | same file `:91-96` |
| `calculation_snapshots` types | `supabase/migrations/20260807020000_add_calculation_snapshots.sql:21-45` |
| `emissions_logs` types | `supabase/migrations/00000000000000_init_schema.sql` (`emissions_logs` block) |

## 26. Exact relevant commit SHAs

| SHA | Meaning |
| --- | --- |
| `7f97b5568c72a0081a31bf50b14e532f0e51de82` | **Preflight baseline HEAD** (branch head at the start of this task; question-library capability gap report) |
| `669669a` (short) | Insight architecture implementation gap report |
| `651f8c1`, `674fe07` | I3 tool boundary (`services/insight_tools.py`) |
| `f9d91e1` | I4/I5 orchestration (`insight_interactions.py`, `insight_context.py`) |
| `177dff5` | I2 authorization boundary (`api/insight_authz.py`) |
| `999e4fb` | `data/emissions_logs.py` + `api/v3_emissions.py` aggregation surface |
| `09e2315` | Insight frontend |

---

## 27. Final recommendation

`[INFER]` **Do not authorize Package 1 yet.** The engineering shape is small and low-risk, but four things must be decided first, because each changes what the package must contain:

1. **G-1/G-2 — accept that a new Insight tool requires both an I3 catalogue authorization and one migration** (`ci_tool_calls_tool_name_check`). This is the fact that most changes the package's character: it is not a schema-neutral change, and it must be authorized as such.
2. **G-3 — choose the ambiguity representation.** Option C (reuse `truncated` + `reason` + candidate references) is the only choice that leaves both ratified vocabularies and their DB CHECKs untouched and adds no UI state; Option A/B are cleaner semantically but widen a closed contract and require a second migration.
3. **G-4/G-5 — record the tolerance rule and the date semantics rule.** Both are pure product decisions with no code dependency; without them the amount and date dimensions are `[BLOCKED]`.
4. **G-7 — settle the basis/unit rule.** As it stands, `aggregate_by_activity` and `aggregate_by_supplier` return `SUM(quantity)` across mixed units, which cannot be presented as a deterministic basis.

`[INFER]` When those are decided, the recommended scope is exactly §21 U1–U8 with §22's exclusions enforced, verified independently by OHD against §19's suites plus the four prompt questions in §7.1. **Nothing in this preflight authorizes implementation**, and this document must not be cited as authorization.

---

## 28. Stop condition

**STOP.** This preflight is complete at the point of report creation.

* No implementation was performed: no tool added or widened, no `ToolStatus`/`AnswerStatus` change, no discovery, no aggregation, no scope filter, no supplier persistence, no Scope 3 schema, no aggregate evidence drill-down, no RLS change, no authorization change, no Source Evidence Viewer change, no Insight UI change, no rate limiting, no migration.
* The migration identified in §8.1/U4 is **required for a future package**, not for this analysis; none was created.
* No finding was fixed.
* The two PO-supplied reference documents plus the newly supplied PO decision matrix and ChatGPT PO history remain untracked and unmodified.
* The only repository change made by this task is this report.

**NO IMPLEMENTATION PERFORMED.**
