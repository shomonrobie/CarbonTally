# CarbonTally Insight — P3 Independent Verification (OHD Verifier)

Date: 2026-09-23
Verifier: Independent P3 verification (restricted verifier agent)
Repository: `/home/shomonrobie/ct_93d5cdd`
Branch: `p8-release-reconciled`
Authoritative remote: `github` (`https://github.com/shomonrobie/CarbonTally.git`)
Model: `deepseek/deepseek-flash`

```text
VERIFICATION TYPE: INDEPENDENT (not the implementing agent, not the Cline pass)
PACKAGE: P3 — Data Quality + Audit/Reproducibility Intelligence (families 14 and 16)
```

This report is verification-only. No source, test, migration, configuration,
frontend or documentation file was modified. The only repository artifact created
by this pass is this report. The implementing agent's own report and the Cline
verification pass are used **only as evidence sources and as a claim list to be
independently confirmed** — they are not treated as verification.

---

## 1. Verification identity and scope

**In scope (independently verified):** the P3 implementation commit `466c159`;
the MIG-1 remediation commit `6605475`; the P3 migration's position and effect in
the migration chain; the two P3 tools (`insight_data_quality`,
`insight_calculation_reproducibility`) — their contract, data-quality reuse,
reproducibility rule, provenance/evidence boundary, tenant isolation, rate
limiting and answer-state behaviour; P2 regression protection; broader Insight
regression; test integrity.

**Out of scope:** any fix, refactor or re-pin; P3 policy decision D-14; L7, L8,
supplier, Scope 2/3, variance, audit-package, knowledge, reporting, reduction,
commercial and repository-reconciliation decisions; PO closure of any package;
P12; production deployment. See §16.

**Evidence classes used in this report:**

* **OBSERVED** — the verifier executed it and quotes the raw result.
* **DERIVED** — inferred from repository files / Git history without execution.
* **UNVERIFIABLE** — could not be checked in this environment, with the reason.
* **CLAIM (Cline)** — an assertion made by the implementation/Cline reports, not
  necessarily confirmed here.

---

## 2. Repository / Git state (OBSERVED)

| Item | Value |
| --- | --- |
| Working directory | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD | `f116ed1b59fbe5a69f1a807a6ba48d5e470bf504` |
| HEAD subject | `docs(p8): record the P2 closure-document commit SHA in the closure record` |
| `github/p8-release-reconciled` | `f116ed1b59fbe5a69f1a807a6ba48d5e470bf504` |
| `git rev-list --left-right --count HEAD...github/p8-release-reconciled` | `0 0` (aligned) |
| Latest tag | `v2.1-phase4` (`git describe` → `v2.1-phase4-370-gf116ed1`) |
| Working tree | **dirty**: ` M .gitignore` plus pre-existing untracked files (`?? .costrict/`, `?? 8`, `?? =`, six untracked `docs/` reference documents) |
| Tracked tree vs HEAD | `git diff --stat` → only `.gitignore` (pre-existing at Phase 0, **not** authored by this pass) |
| Verification timestamp (UTC) | 2026-09-23T13:51:47Z |

Key commit ancestry (all **OBSERVED**):

| Commit | Full SHA | Role |
| --- | --- | --- |
| P3 parent | `4cd358da2ef3503b5d5ce4d261ec99b5a29e964e` | before P3 |
| P2 impl | `f2e456817e78c4f88e55837129ceefb0e9e90659` | P2 temporal comparison |
| P3 impl | `466c15982ef42ec164ada6cf46e4abcd026fc93c` | P3 data quality + reproducibility |
| P3 report record | `3657f640aa763c8945fda0deb7f97516065ddad8` | docs |
| Cline verification | `804bda279f5bf35172d8a81eaf0ac29fd229ff11` | docs |
| MIG-1 remediation | `6605475d5d9a41f3b8ae1e6a5db3cbe5d45abc8d` | migration rename + pins |
| P2 reconciliation | `52307a662246cb8a80e5df0a91c675ebee909da3` | docs |
| P2 PO closure | `1b33f222552c07ab137e5da49482b24552ad5642` | docs |
| HEAD | `f116ed1b59fbe5a69f1a807a6ba48d5e470bf504` | docs |

`git merge-base --is-ancestor 466c159 HEAD` → **YES**; same for `6605475` (**OBSERVED**).
The reported SHAs are current.

Tool versions (OBSERVED): Python 3.14.4; pytest 9.1.1 (backend `.venv`);
Node v24.21.0; npm 11.19.0; Docker 29.1.3; Docker Compose 2.40.3;
`psql` 18.6 (server: PostgreSQL 17.6, Supabase image).

> **Worktree caveat (OBSERVED, unchanged from Phase 0 to end):** the working tree
> is **not clean** (`.gitignore` modified; untracked files present). None of these
> pre-date-analysis files are P3/MIG-1 artifacts; see §14 for the before/after
> proof that this pass changed nothing.

---

## 3. Evidence reviewed

**Reports (CLAIM sources, read in full):**

* `docs/architecture/CT-P8-INSIGHT-DATA-QUALITY-AUDIT-REPRODUCIBILITY-IMPLEMENTATION-20260923.md`
* `docs/architecture/CT-P8-INSIGHT-P2-P3-CLINE-VERIFICATION-20260923.md`
* `docs/architecture/CT-P8-INSIGHT-P2-P3-MIG1-REMEDIATION-20260923.md`
* `docs/architecture/CT-P8-INSIGHT-P2-TEST-INVENTORY-RECONCILIATION-20260923.md`

**Implementation (OBSERVED by direct read):** `backend/domain/insight_quality.py`,
`backend/services/insight_tools.py`, `backend/services/insight_query_planner.py`,
`backend/domain/insight_interaction.py`, `backend/services/insight_interactions.py`,
`backend/api/v3_insight_tools.py`,
`supabase/migrations/20261007000000_p8_insight_data_quality_reproducibility.sql`.

**Tests (OBSERVED by direct read + execution):**
`backend/tests/unit/api/test_p8_insight_data_quality.py`,
`backend/tests/unit/api/test_p2_*` (temporal comparison), the I1/I2/I3 data/api
suites, the Insight regression set and the full unit suite.

**Git history (OBSERVED):** `git show`/`git diff` of `466c159`, `6605475`,
`f2e4568`, `4cd358d..HEAD`.

---

## 4. P3 implementation inventory

`git show --numstat 466c159^..466c159` (**OBSERVED**):

```text
4	0	backend/domain/insight_interaction.py
243	0	backend/domain/insight_quality.py
2	0	backend/services/insight_interactions.py
61	0	backend/services/insight_query_planner.py
514	0	backend/services/insight_tools.py
871	0	backend/tests/unit/api/test_p8_insight_data_quality.py
5	3	backend/tests/unit/api/test_v3_insight_i3_tools.py
283	0	docs/architecture/CT-P8-INSIGHT-DATA-QUALITY-AUDIT-REPRODUCIBILITY-IMPLEMENTATION-20260923.md
48	0	supabase/migrations/20260923000000_p8_insight_data_quality_reproducibility.sql
```

* 9 files, **+2,031 / −3** (the 3 deletions are the shared I3 catalogue pin's
  three replaced lines). Matches the implementation report §22 (**OBSERVED**).
* `backend/services/insight_tools.py` is **+514 / −0** — insertions only, so P2
  lines (including the `_temporal_comparison` docstring) are byte-identical
  (**OBSERVED**, confirms implementation report §20 and Cline §25).
* `backend/domain/insight_quality.py` is a new pure contract/helper module
  (no I/O, no DB, no SQL) (**OBSERVED**).

Claimed vs observed capability presence:

| Capability | CLAIM | OBSERVED |
| --- | --- | --- |
| `insight_data_quality` registered | yes | yes (registry size 10, `read_only=True`) |
| `insight_calculation_reproducibility` registered | yes | yes (registry size 10, `read_only=True`) |
| I4 argument allowlist for both | yes | yes (`TOOL_ARGUMENT_ALLOWLIST`) |
| Planner intents | yes | yes (`_QUALITY`, `_REPRODUCIBILITY`, `_UUID`, branches after the P2 branch) |
| Migration widens tool CHECK 8 → 10 | yes | yes (verified in a disposable DB, §11) |
| P2 files byte-identical | yes | yes (`insight_temporal_comparison.py` / `domain/insight_query.py` / frontend untouched) |

---

## 5. P3 test inventory and execution

**Collection (OBSERVED):**

```bash
cd /home/shomonrobie/ct_93d5cdd/backend
.venv/bin/python -m pytest tests/unit/api/test_p8_insight_data_quality.py \
    -q --no-header -p no:cacheprovider --collect-only
# => tests/unit/api/test_p8_insight_data_quality.py: 48
```

**Execution (OBSERVED):**

```bash
.venv/bin/python -m pytest tests/unit/api/test_p8_insight_data_quality.py \
    -p no:cacheprovider -o addopts="" --no-header -q
# => 48 passed, 1 warning in 0.21s   (exit 0)
```

* Exact result: **48 collected, 48 passed, 0 failed, 0 skipped, 0 errors**.
* No `skip`/`xfail`/`pytest.mark` in the file (`grep -nE "skip|xfail|pytest.mark"` → none).
* No parametrisation.
* `grep -cE "^(async )?def test_"` = **48** at `466c159` **and** at HEAD; the file
  is 871 lines at both (**OBSERVED** via `git show 466c159:...`).
* The only change to the P3 test file between `466c159` and HEAD is the
  MIG-1-authorized migration-path literal (`20260923000000…` → `20261007000000…`),
  1 line replaced (**OBSERVED** `git diff 466c159..HEAD`).

**Conclusion:** the reported **48-test P3 inventory is accurate**; no P3 test was
removed, renamed, disabled, weakened or excluded; no collection configuration was
changed (**OBSERVED**).

---

## 6. Data-quality verification (`insight_data_quality`)

**Contract (OBSERVED from the running registry):**

```text
insight_data_quality
  read_only: True
  required: ('start_date', 'end_date')  optional: ('limit',)  accepted: same
  reference_kinds: ()
  authorization: i2-boundary: authorize_insight_scope + organisation-scoped query
```

**Reuse of existing machinery — confirmed by code trace (OBSERVED):**
`_data_quality` builds the **existing** `ValidationEngine` and calls
`validate_input` (A1) then merges `validate_snapshot` (A2 recomputation +
content-hash, A5 provenance) over each stored row. Findings are projected from the
engine's own `ValidationIssue` (`code`, `severity`, `message`, `entity_type`,
`entity_id`, `field`) — `_validation_issue_dict`. `_QUALITY_CHECKS` states exactly
the four check families performed.

**No invented methodology (OBSERVED):**

* The only issue vocabulary is the engine's existing `VAL_*` codes; the P3 diff
  adds no new `VAL_` code.
* No composite score/weight/grade: `summarise_report` emits per-code counts
  (`record_count`, `affected_records`, engine `severity`) with no weighting;
  test `test_no_composite_score_is_invented` asserts `score/grade/rating/
  confidence/readiness/index` absent from result keys and `weight` absent from
  findings.
* Honesty mechanisms verified by test and by read: empty `activity` is validated
  **as retained** (no `activity_type` fallback); an unresolvable factor is counted
  in `records_with_unresolved_factor` and the factor-dependent unit rule is not
  claimed.

**Bounded output (OBSERVED):** `MAX_QUALITY_RECORDS = 200` (the existing I3 result
bound); the scan requests `limit + 1` rows to *detect* truncation, slices to
`limit`, and reports `population_truncated` / `population_exceeds_bound`; the
count is capped by the same bound. No grouping/dimension/free-text surface exists;
unknown keys → `invalid_input` (test `test_arbitrary_query_surface_is_refused`).

**Distinguishing deterministic signal from LLM narration (OBSERVED):** all counts
and codes are computed in Python before any narration; test
`test_deterministic_counts_reach_the_narration_boundary` asserts the deterministic
figures are already present in the result.

> **Finding P3-IV-01 (genuine P3 defect, non-blocking).** When a period contains
> rows but **every** row is uncheckable (`snapshot_from_row` → `None`), the tool
> returns `status=success, reason="all_checks_passed"` with `records_checked=0`,
> `uncheckable_records=1`, `records_passing=0`. See §15.

---

## 7. Reproducibility verification (`insight_calculation_reproducibility`)

**Contract (OBSERVED):**

```text
insight_calculation_reproducibility
  read_only: True
  required: ('snapshot_id',)  accepted: ('snapshot_id',)
  reference_kinds: ('calculation_snapshot', 'evidence_line_item')
  authorization: i2-boundary: authorize_insight_scope + object organisation re-check
```

**Ten conditions (OBSERVED in `REPRODUCIBILITY_CONDITIONS`, fixed order):**
`calculation_snapshot_retained`, `calculation_result_retained`,
`calculation_inputs_retained`, `factor_reference_retained`,
`methodology_and_algorithm_retained`, `source_lineage_retained`,
`evidence_resolvable`, `recomputation_matches`, `content_hash_matches`,
`factor_provenance_consistent`.

**The stated rule — traced through code (OBSERVED):**

`insight_tools.py::_reproducibility_data`:

```python
"reproducible": bool(verification.match) and not bool(verification.tampered),
```

i.e. exactly `reproducible = recomputation_match AND NOT tampered`. The two
inputs come from the **existing** `CalculationEngine(repos.logs).verify(snapshot)`
(`VerificationResult.match/.tampered/.discrepancy`); `content_hash_matches` is
`not verification.tampered`. No second calculation engine and no reimplemented
formula exist in the P3 diff (**OBSERVED**). `factor_provenance_consistent` is
derived from the engine's existing `VAL_SNAPSHOT_*`/`VAL_FACTOR_ORPHAN` codes
(`_PROVENANCE_CODES`). `evidence_resolvable` uses the existing
`evidence_line_items.count_for_item(source_item_id)` read.

**No certification language (OBSERVED):** `_reproducibility_data` emits no
`certified`/`audit_approved`/`assurance`/`compliant` field; a non-reproducible
result is a limitation (`unsatisfied_conditions` + reason
`reproducibility_limitation`), never "incorrect".

**Tests (OBSERVED passing):** `test_reproducible_calculation_reports_every_condition`,
`test_missing_replay_input_is_reported_as_a_limitation`,
`test_unresolvable_source_lineage_is_reported`,
`test_snapshot_result_mismatch_uses_the_existing_check`,
`test_tamper_evidence_uses_the_existing_hash_check`,
`test_missing_historical_factor_is_reported_not_fabricated`.

---

## 8. Provenance / evidence verification

**OBSERVED:**

* The reproducibility tool returns exactly the permitted `reference_kinds`
  `("calculation_snapshot", "evidence_line_item")` and names
  `provenance_tool = insight_aggregate_provenance` (the closed INS-01 tool) —
  no second provenance store, evidence viewer or audit ledger exists.
* `insight_data_quality` returns `reference_kinds = ()` (no references).
* Evidence resolvability is established with the existing
  `evidence_line_items.count_for_item(...)` read only.
* `grep -niE "select |insert |update |delete |from public\."` over
  `backend/services/insight_tools.py` → **NONE** — the tool layer issues no SQL of
  its own; all reads go through organisation-scoped repository methods.
* No signed URL, raw document text or OCR content is emitted by either tool: the
  result fields are the ratified provenance/identity set (`activity_type`, `scope`,
  `date`, `co2e_kg`, factor ids/kinds, `methodology`, `algorithm_version`, counts).
  (Note: the reproducibility payload deliberately omits the raw `activity` text,
  which is *more* conservative than the ratified snapshot projection.)

The `deterministic data → provenance → evidence → LLM narration` boundary is
preserved (**OBSERVED**).

---

## 9. Authorization / tenant isolation

**I2 authorization (OBSERVED):** `invoke_tool` resolves scope through the closed
`api.insight_authz.authorize_insight_scope` for **all** tools before dispatch
(unchanged by P3); an unresolvable scope returns `not_authorized`.

**P3-specific paths (OBSERVED):**

* **Quality scan** — org comes from `access.organization_id` and is passed as a
  positional parameter to `search_snapshots(org, …)` / `count_matching_snapshots
  (org, …)`; the queries are organisation-scoped. A user authorised for ORG_B
  requesting ORG_A → `not_authorized`
  (`test_cross_tenant_quality_scan_is_denied`).
* **Record-level check** — `get_snapshot(snapshot_id)` is by-id, then the row's
  `organization_id` is explicitly re-checked against `access.organization_id`
  ("a reference is a locator, never a grant"); a foreign snapshot →
  `not_authorized` (`test_foreign_snapshot_identifier_is_denied`,
  `test_cross_tenant_snapshot_is_denied_at_the_tool_layer`).
* Unauthenticated access is refused (`test_unauthenticated_access_is_refused`);
  injection-shaped/unknown keys (`sql`, `table`, `group_by`) → `invalid_input`
  (`test_arbitrary_query_surface_is_refused`).

**Conclusion:** P3 introduces **no path** that retrieves another organisation's
quality or reproducibility information. No P3 tool performs arbitrary SQL or
arbitrary querying (**OBSERVED**).

> **Observation P3-IV-02 (pre-existing, INFO).** A non-existent snapshot id yields
> `no_data/snapshot_not_found`, whereas an existing foreign id yields
> `not_authorized` — a minor existence oracle. The **ratified** I3 tool
> `calculation_snapshot_lookup` (`_snapshot_lookup`) uses the identical pattern, so
> this is a pre-existing catalogue characteristic, **not introduced by P3**. It
> makes the Cline report's phrase "no existence disclosure" imprecise. No payload
> content is disclosed; neither tool returns another tenant's data.

---

## 10. Rate-limit verification

**OBSERVED:** the customer-facing route `POST /api/v3/insight/tools/invoke`
(`backend/api/v3_insight_tools.py`) calls `check_request_rates(...)` and
`acquire_execution_leases(...)` **before** `invoke_tool`, and raises
`rate_limited_error` when not allowed. P3 tools therefore consume the **existing**
INS-01 limiter through the same path as the closed tools.

* `git diff --name-only 4cd358d..HEAD -- backend/services/insight_rate_limit.py
  backend/api/v3_insight_tools.py` → **empty** (limiter and route untouched by
  P3/MIG-1) (**OBSERVED**).
* Defaults unchanged: user policy `(20 rpm, burst 5, concurrent 2)`; org policy
  `(100 rpm, burst 20, concurrent 10)`; safety ceilings `(600,100,20)` /
  `(6000,1000,100)` (**OBSERVED** in source).
* `test_quality_route_is_organisation_scoped_and_rate_limited` passes and asserts
  the shared allowance was consumed (`repos.insight_limits.consumed`) (**OBSERVED**).
* Cline observation **O-2 is accurate**: an in-process `invoke_tool` call does not
  itself consume a token; the route does. Not a P3 defect and not classified as
  commercial I8 billing work.

---

## 11. Migration-chain verification (disposable database only)

**Environment (OBSERVED):** the pre-existing disposable container
`ct_p3_verify_pg` (`public.ecr.aws/supabase/postgres:17.6.1.159`, `127.0.0.1:55440`).
To obtain **genuine independence** the verifier did **not** use the container's
already-populated `postgres` database; a **fresh database `iv_p3_fresh`** was
created, bootstrapped with the image's Supabase init scripts
(`00000000000000-initial-schema`, `…01-auth-schema`, `…02-storage-schema`,
`…03-post-setup`; only harmless "role already exists" notices), then the
repository's `supabase/migrations/*.sql` were applied **in lexicographic order**,
one `psql` per file with `ON_ERROR_STOP=1`.

**Result (OBSERVED):**

```text
TOTAL=81 OK=80 FAIL=1
FAILED: 20260823000000_d32_private_documents_storage.sql
  psql:<stdin>:83: ERROR: relation "storage.buckets" does not exist
  LINE 1: UPDATE storage.buckets SET public = FALSE WHERE name = 'docu...
```

This **reproduces** the MIG-1 remediation report §8 exactly: the single failure is
the known **unrelated** Supabase Storage-schema prerequisite (`storage.buckets` is
provided by the storage service, not the Postgres image). It precedes all Insight
migrations and did not block them.

**Relevant chain (OBSERVED — all applied OK):**

| Migration | Position | Result |
| --- | --- | --- |
| `20261001000000_p8_i1_insight_persistence.sql` | I1 | OK |
| `20261002000000_p8_i2_insight_authorization.sql` | I2 | OK |
| `20261003000000_p8_i4_insight_interactions.sql` (creates the table) | I4 | OK |
| `20261005000000_p8_insight_discovery_aggregation_rate_limit.sql` | INS-01 | OK |
| `20261006000000_p8_insight_temporal_comparison.sql` | P2 | OK |
| `20261007000000_p8_insight_data_quality_reproducibility.sql` | **P3** | OK — no missing-relation error |

`ls supabase/migrations/*.sql | sort | tail -8` confirms the chronological order
`…20260931 → 20261001 → 20261002 → 20261003 → 20261005 → 20261006 → 20261007`,
and no file sorts after `20261007000000…` — **P3 is the last migration**
(**OBSERVED**). Therefore no later migration can re-narrow the tool CHECK and the
P3 tools are not lost/rejected after subsequent migrations.

**Final I3 CHECK constraint (OBSERVED, read from the database):** exactly ten
names — the four ratified, the three analytics, `insight_temporal_comparison`,
`insight_data_quality`, `insight_calculation_reproducibility`.

**Constraint probe (OBSERVED, via a `LIKE … INCLUDING ALL` temp clone):**

```text
authorized_accepted=10
unratified values rejected: 'unratified_tool', 'insight_data_quality_v2',
                            'scope3_analysis', ''  → all check_violation
```

**I4 answer states (OBSERVED):** `ci_interactions_answer_status_check` contains
exactly **15** states
(`success, zero, no_data, not_authorized, insufficient_data, needs_clarification,
tool_failure, provider_unavailable, partial, rate_limited, refused, ungrounded,
invalid_input, error, multiple_matches`); `multiple_matches` present; no
unauthorized new state.

**Idempotence (OBSERVED):** re-applying the P3 migration twice more returned exit 0
each time; exactly **1** constraint remained, still with **10** names.

**Ordering-pin corrections (OBSERVED):**

* `backend/tests/unit/data/test_i1_insight_migration.py` — the successor allowlist
  gained the `20261007000000_p8_insight_data_quality_reproducibility.sql` option,
  matching the actual repository state.
* `backend/tests/unit/data/test_i2_insight_authorization_contracts.py` — the
  `names[-1]` pin now names `20261007000000_p8_insight_data_quality_reproducibility
  .sql`, matching reality; its `CREATE/DROP POLICY`, no-table/column/index/grant
  invariants are unchanged.
* `backend/tests/unit/api/test_p8_insight_temporal_comparison.py` — the P2
  catalogue pin moved `8 → 10` and **remains an exact `==` count** (not `>=`/subset).
* Run of I1 + I2 + I3 suites → **46 passed** (9 + 7 + 30) (**OBSERVED**).

**No unrelated migration was modified (OBSERVED):**
`git diff --name-status 4cd358d..HEAD` lists only the P3 migration (as added under
its new name) and the P3/MIG-1 test files plus docs. `git diff -M 6605475^..6605475`
shows the P3 migration as a pure **rename**; the SQL body is **byte-identical**
with comment lines excluded:

```bash
diff <(git show 466c159:…20260923000000….sql | grep -vE '^--') \
     <(git show HEAD:…20261007000000….sql | grep -vE '^--')
# => SQL STATEMENTS BYTE-IDENTICAL (comments excluded)
```

> **Finding P3-IV-03 (documentation drift, LOW, non-blocking).** The P3
> implementation report still references the pre-rename filename
> (`20260923000000_p8_insight_data_quality_reproducibility.sql`) in its file table
> and migration section; MIG-1 renamed it to `20261007000000_…` and did not update
> that report. The MIG-1 report documents the rename, so history is traceable, but
> the two reports now disagree on the filename. See §15.

---

## 12. P2 regression verification

**OBSERVED:**

* `git diff f2e4568..HEAD --stat -- backend/services/insight_temporal_comparison.py
  backend/domain/insight_query.py frontend/src` → **empty**. P2 production and
  frontend files are unchanged since the P2 implementation commit.
* `git diff f2e4568..HEAD --stat -- supabase/migrations/20261006000000_p8_insight_
  temporal_comparison.sql` → **empty**.
* P2 test count: `grep -cE "^(async )?def test_"` = **43** at `f2e4568` and **43**
  at HEAD.
* The only change to the P2 test file since P2 is the MIG-1-authorized catalogue
  pin `8 → 10` plus a docstring (exact count retained).
* P2 suite execution:

```bash
.venv/bin/python -m pytest tests/unit/api/test_p8_insight_temporal_comparison.py \
    -p no:cacheprovider -o addopts="" --no-header -q
# => 43 passed, 1 warning in 0.13s   (exit 0)
```

* The eight-tool historical state was correctly expanded to the current ten-tool
  catalogue by P3 authorization + MIG-1 (constraint probe, §11) (**OBSERVED**).

**Conclusion:** no genuine P2 regression was found; P2 is not reopened. The P2
inventory remains **43**.

---

## 13. Broader regression results

**P3-specific:** 48/48 pass (§5).

**P2 regression:** 43/43 pass (§12).

**Broader Insight regression (OBSERVED):** the 19 insight-related unit files were
executed together (a superset of the reports' "13-file / 299" set):

```bash
.venv/bin/python -m pytest <19 insight test files> \
    -o addopts="" -p no:cacheprovider --no-header -q
# => 398 passed, 5 warnings in 2.47s   (exit 0)
```

All 398 pass, so the reported 299-test subset necessarily passes. (The exact
13-file composition summing to 299 is **not enumerated** in the reviewed reports;
252 distinct 13-file subsets of the insight files sum to 299 — see
**Finding P3-IV-04**, documentation ambiguity, LOW.)

**Full unit suite (OBSERVED):**

```bash
.venv/bin/python -m pytest tests/unit -o addopts="" -p no:cacheprovider -q
# => 4 failed, 3208 passed, 8 skipped, 13 warnings in 233.08s
```

The 4 failures are all **pre-existing / unrelated**, each untouched by P3/MIG-1:

| # | Failing test | Cause (OBSERVED) | Classification |
| --- | --- | --- | --- |
| 1 | `test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered` | `_paths()` returns only `{'/api/v2/health'}` | pre-existing (FastAPI `_IncludedRouter` behaviour; no P3/MIG-1 change to `api/router.py` or review routes) |
| 2 | `test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered` | same | pre-existing |
| 3 | `test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained` | same | pre-existing |
| 4 | `test_d17_..._migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | `assert 81 == 71` | pre-existing stale migration-count pin (D-29); it was already `80 == 71` at the P3 parent `4cd358d`, and P3 adds one migration file the pin counts |

`git diff --name-only 4cd358d..HEAD` contains **no** `review_sla`, `api/router.py`
or `d17` file — the pin file is `== 71` at `4cd358d` and at HEAD (OBSERVED) — so
none of these failures is P3-caused.

**Frontend (OBSERVED):**

```bash
cd frontend && CI=true node_modules/.bin/react-scripts test \
    --testPathPattern="dr007" --watchAll=false
# => Test Suites: 1 failed; Tests: 1 failed, 1 passed
#    Issue 3 — customer review detail shows Mapped activity … expected "Natural gas"
```

`git diff --name-only 4cd358d..HEAD` contains no `frontend/` path, so the DR007
failure reproduces with P3/MIG-1 absent from the frontend → **pre-existing**.

---

## 14. Test-integrity / non-interference evidence

**Before vs after comparison (OBSERVED):**

| Item | Phase 0 (start) | End | Verdict |
| --- | --- | --- | --- |
| HEAD | `f116ed1b…` | `f116ed1b…` | unchanged |
| Branch | `p8-release-reconciled` | `p8-release-reconciled` | unchanged |
| `github/p8-release-reconciled` | `f116ed1b…` | `f116ed1b…` (`0 0`) | unchanged |
| `git status --porcelain` | ` M .gitignore` + 9 untracked entries | identical list | unchanged |
| Tracked diff | `.gitignore` only (pre-existing) | `.gitignore` only | unchanged by this pass |

Key P3 file hashes at end of verification (SHA-1, OBSERVED):

```text
90d1880c240c2444d01f0e4ff8c6927b347bee44  backend/domain/insight_quality.py
6beb009ab0e1357dd4a127bdc2fde6329f47ab8f  backend/services/insight_tools.py
116d1787e68f9deff6075a57623a8f4facd0296d  backend/services/insight_query_planner.py
7ea63959307b93215c7051e2a8a0dd289c8e6386  backend/domain/insight_interaction.py
ad26ba11adfc7921f511c8a9dad40be1756b743a  supabase/migrations/20261007000000_p8_insight_data_quality_reproducibility.sql
a9dde918c182b599dcbff1dee36836346e125ab5  backend/tests/unit/api/test_p8_insight_data_quality.py
```

No source, test, migration, configuration or documentation file was modified. No
Git mutation (no commit/push/tag/reset/checkout/stash/clean) was performed during
verification. The only repository artifact created is this report.

**Side effects observed** (disposable / tool-supported only):

* Python `__pycache__` bytecode caches refreshed under `backend/` (gitignored).
* `.pytest_cache` usage in `backend/` (gitignored; pre-existing).
* Jest/react-scripts run for the frontend DR007 check (Jest cache in the tool's
  default temp location; no repository file written).
* A disposable database `iv_p3_fresh` was created **inside the pre-existing
  disposable container** `ct_p3_verify_pg`, used for the fresh-chain test, and then
  **dropped**; the container's other databases were not touched, and the container
  itself was not created, removed or modified by this pass. No shared, staging or
  production database was contacted.

---

## 15. Findings and limitations

### Genuine P3 defects (verifier-observed, non-blocking)

**P3-IV-01 — `insight_data_quality` reports `all_checks_passed` when nothing could
be checked.**
Severity: **LOW–MEDIUM (honesty / contract)** · Phase 6 · Status: **genuine P3 defect,
non-blocking.**

*Reproduction (OBSERVED):*

```bash
cd /home/shomonrobie/ct_93d5cdd/backend
.venv/bin/python - <<'PY'
import asyncio
from tests.unit.api.test_p8_insight_data_quality import _P3Logs, _Repos, _row, _quality, SNAP
async def main():
    logs = _P3Logs(); logs.add_row(_row())
    logs.by_id[SNAP]["quantity"] = None          # every row now unmappable
    r = await _quality(_Repos(logs=logs))
    print(r.status.value, r.reason, r.data["records_checked"],
          r.data["uncheckable_records"], r.data["records_passing"])
asyncio.run(main())
PY
# => success all_checks_passed 0 1 0
```

*What is observed:* with rows present but `records_checked == 0` and
`uncheckable_records > 0`, the tool returns `status=success` and
`reason="all_checks_passed"`.

*Why it matters:* the implementation report §6/§10 explicitly states "not checked
must not read as checked" and the answer-state table lists not-checkable as
"never a pass". The structured counts remain truthful
(`records_checked=0`, `records_passing=0`, `uncheckable_records=1`), and the test
`test_not_checked_is_never_reported_as_passed` only asserts the counts (it does
**not** assert the `reason`), so the test name overstates what is pinned.

*Impact / why non-blocking:* no security, tenancy, accounting or data-integrity
impact; the structured data a narration would need is accurate; reachability
requires an abnormal stored row state (for real rows the relevant columns are
`NOT NULL`; only the nullable `calculated_at` could be NULL). It is a small,
contained branch-condition gap between the documented contract and behaviour, and
is reported for the PO/owner rather than fixed here.

### Documentation / evidence-quality observations (non-blocking)

**P3-IV-02 — foreign-id existence oracle (pre-existing, INFO).** `not_authorized`
for an existing foreign snapshot vs `no_data` for an unknown id; identical to the
ratified `calculation_snapshot_lookup` pattern, therefore **not P3-introduced**, but
Cline's "no existence disclosure" wording is imprecise (§9).

**P3-IV-03 — stale migration filename in the P3 implementation report (LOW).** The
P3 report still names `20260923000000_…`; MIG-1 renamed it to `20261007000000_…`
(§11). Traceable via the MIG-1 report; no functional impact.

**P3-IV-04 — the "13-file / 299" regression set is not enumerated (LOW).** The
reports cite "13 files, 299 tests" without listing them; the verifier reproduced a
398-test superset that all passes, so the 299 subset necessarily passes, but the
precise composition is ambiguous.

**P3-IV-05 — D17 migration-count pin now reads 81 vs 71 (pre-existing, LOW).** It
was already failing at the P3 parent (`80 == 71`); P3's added migration file simply
increments the observed count. A prefix/ordering assertion would be more durable.

### Claims reproduced vs claims left as claims

| Cline / implementation claim | Verifier result |
| --- | --- |
| P3 = 48 tests, 48 passed | **REPRODUCED** (48 collected, 48 passed) |
| P2 = 43 tests, 43 passed | **REPRODUCED** (43 collected, 43 passed) |
| Insight regression 299 | **CONSISTENT** (398-test superset all green) |
| P2 files byte-identical / `insight_tools.py` +514/−0 | **REPRODUCED** |
| Reproducible = match AND NOT tampered | **REPRODUCED from code** |
| Migration widened to 10 tools; P3 tools accepted | **REPRODUCED in DB** |
| MIG-1 fresh chain (1 unrelated failure: `storage.buckets`) | **REPRODUCED** |
| I4 = exactly 15 states incl. `multiple_matches` | **REPRODUCED** |
| Rate limiting via existing INS-01 limiter, unchanged thresholds | **REPRODUCED** |
| Tenant isolation (org-scoped + object re-check) | **REPRODUCED** |
| "not-checked never reads as checked" | **PARTIALLY REPRODUCED** — see P3-IV-01 |
| "foreign snapshot … no existence disclosure" | **IMPRECISE** — see P3-IV-02 |

---

## 16. Explicit out-of-scope items

Verified **not** implemented by P3 (keyword scan of the P3 diff and P3 modules was
negative): Scope 3 Categories 1–15; market-based Scope 2; Scope 1 decomposition;
supplier persistence/analytics; temporal comparison beyond P2; variance/attribution;
factor-history intelligence; general carbon-accounting knowledge/RAG;
consultant/auditor persona expansion; L7 lifecycle/retention policy; L8
commercial/billing; P12/investor-demo changes; production deployment. (`git show
466c159 -- backend/` added lines contain no such term.)

Not decided and not closed by this pass: P3 decision D-14; L7 D-01→D-08; supplier
D-09; Scope 2 D-10; variance D-12; Scope 3/factor history D-13; audit package
D-16; knowledge D-17; reporting D-18; reduction D-19; commercial D-20→D-26;
reconciliation D-27→D-29. No policy was made.

---

## 17. Final verdict

```text
PASS WITH NON-BLOCKING OBSERVATIONS
```

**Non-blocking observations that remain:**

1. **P3-IV-01** — `insight_data_quality` returns `reason="all_checks_passed"` when
   a period has rows but **no** record could be checked (contradicts the stated
   "not-checked never reads as checked" contract; structured counts remain
   truthful). Non-blocking: no security/tenancy/accounting/data impact; edge-case
   reachability; narration can use the accurate counts.
2. **P3-IV-02** — foreign-id existence oracle (pre-existing, shared with the
   ratified `calculation_snapshot_lookup`); Cline wording imprecise.
3. **P3-IV-03** — the P3 implementation report still cites the pre-rename migration
   filename (`20260923000000_…`); MIG-1 renamed it to `20261007000000_…`.
4. **P3-IV-04** — the "13-file / 299" regression set is not enumerated.
5. **P3-IV-05** — pre-existing D17 migration-count pin (`81 == 71`).

None of these prevents the P3 capability from working as authorized, and none is a
security, tenancy, provenance, accounting or data-integrity defect. **P3 is not
declared PO-closed by this report.**

**MIG-1 (separately):** this verification independently establishes that the
remediation's remaining verification obligation is satisfied — the corrected
migration applies in a fresh chain at the correct position (`20261007`, last), the
final CHECK accepts exactly the authorized ten tools and rejects an unratified one,
idempotence holds, I4 remains 15 states, the ordering pins match reality, and the
only chain failure is the unrelated `storage.buckets` prerequisite. That conclusion
is separate from the P3 verdict above.

No authorization is granted here for P12, L7, L8 or production deployment.

**Verification limitations (UNVERIFIABLE):**

* Database-level RLS for the Insight tables was not exercised against a live
  Postgres role set (the tools add no table and no policy; application-level
  organisation scoping and object re-checks were verified instead). This matches
  Cline O-3.
* The migration chain was applied to a Supabase-bootstrapped database; the
  `storage.buckets` object supplied by the storage service was out of scope, so
  `20260823000000_d32_…` is the one migration not verified end-to-end (unrelated to
  P3/MIG-1 by construction and by position).
* The full frontend suite was not run; only the known DR007 test was executed.
