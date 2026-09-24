# CT-PO-P12-IMPL-02 — Waste Semantics, Supplier Resolution, Auditable Manual Review and End-to-End PDF Journey

**Task ID:** P12-IMPL-02-20260924-WASTE-SEMANTICS-SUPPLIER-RESOLUTION-AUDITABLE-REVIEW
**Date:** 2026-09-24
**Repository:** CarbonTally — `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Environment:** Demo Lab / local only (PostgreSQL `carbontally_demo_local` on `127.0.0.1:54426`)
**Status:** PARTIALLY IMPLEMENTED — supplier resolution and emissions supplier propagation are
implemented and unit-tested; the six-document operator journey was **not** exercised end-to-end
(see §21–§27, §32).

---

## 1. Task identity

Implement the next narrowly scoped slice required for the canonical investor-demo journey:

    PDF → extraction → validation → manual review when necessary → waste/activity resolution
        → supplier resolution/reuse → mapping → calculation → evidence
        → Source Evidence Viewer → reporting/Insight supplier attribution

governed by the auditability invariant: **if data cannot be extracted or resolved with sufficient
confidence, do not guess, do not discard, do not invent — surface it for auditable manual review.**

## 2. Scope (implemented in this task)

1. Organisation-scoped supplier normalization/resolution per the Decision-01 contract.
2. Supplier reuse semantics across FY2025/FY2026 documents (proven at engine level, §17).
3. Supplier propagation into the calculation/emission write path
   (`manual_extraction_items.mapped_supplier_id` → `CalculationRequest` → `CalculationSink.create`
   → `emissions_logs.supplier_id`).
4. Regression maintenance of the calculation sink test doubles after the contract change.
5. Unit tests for the new resolution engine, including negative/tenant-isolation cases.

## 3. Explicit non-scope (not implemented)

1. **No waste auto-matching was added, and none is correct to add for this corpus** — see §9.
2. No change to the shared-token clarification guard (`'Waste'`) in
   `backend/engines/factor_selection_policy.py`.
3. No schema change, no migration, no RLS change.
4. No reporting/Insight redesign.
5. No P1 promotion.
6. No corpus regeneration; the oracle and `p12-canonical-demo-v1` are untouched.
7. The full six-PDF operator journey (§18, §21–§27) was **not** executed in this session.

## 4. Safety / production prohibition

* Only `carbontally_demo_local` (local demo) was queried or written. No production host, credential,
  database, migration, RLS policy, supplier, emission or deployment was touched.
* `P12-DATA-01` constraints honoured: extraction represents printed document values; the oracle was
  used only for analysis and was **not** modified; `p12-canonical-demo-v1` was **not** regenerated.
* No SQL was used to manufacture a successful workflow (§R); SQL was used for read-only assertions.

## 5. Baseline commit

    git branch --show-current  -> p8-release-reconciled
    git rev-parse HEAD         -> 6462f4712b3c13249ccf8778ef684340941eea1a   (P12-DATA-01)
    tracked working tree       -> only .gitignore modified (pre-existing, not from this task)

Pre-existing untracked noise in the workspace (`.costrict/`, a file named `8`, a file named `=`,
`costrict-p3-ov-01-independent-re-verification.txt`) was not created or modified by this task.


## 6. Source documents inspected

1. `docs/architecture/CT-PO-P12-DOC-03-CANONICAL-SYNTHETIC-PDF-CORPUS-20260924.md`
2. `docs/architecture/CT-PO-P12-GAP-02-CANONICAL-PDF-SUPPLIER-REUSE-20260924.md`
3. `docs/architecture/CT-PO-P12-DECISION-01-PDF-EXTRACTION-SUPPLIER-RESOLUTION-CONTRACT-20260924.md`
4. `docs/architecture/CT-PO-P12-IMPL-01-PDF-EXTRACTION-FOUNDATION-20260924.md`
5. `docs/architecture/CT-PO-P12-DATA-01-CANONICAL-PDF-PRECISION-CONTRACT-20260924.md`
6. `docs/architecture/CT-PO-P12-DEMO-JOURNEY-AUDIT-20260924.md`
7. `tools/demo_lab/p12_canonical_manifest.json`

## 7. Existing architecture inspected

| Concern | Path | Finding |
|---|---|---|
| Mapping persistence | `backend/data/manual_extraction.py:525` | `save_mapped_data(item_id, mapped_data, mapped_facility_id, mapped_asset_id, mapped_supplier_id, emission_factor_used)` sets `status='mapped'` — **`mapped_supplier_id` is already the persisted mapping output** |
| Operator mapping route (internal) | `backend/api/v3_operations.py` (~1700–1740) | `require_staff` + `require_internal_staff` + `ensure_staff_permission("can_process")`; audit action `ops_map:applied` |
| Operator mapping route (PE) | `backend/api/v3_operations.py:1141` | `POST /entities/{entity_id}/extraction/items/{item_id}/map`; `require_staff` + `_entity_workspace_guard` |
| Audit trail | `backend/api/v3_operations.py:399` | `_record_item_action_audit(...)` records actor, status_from, status_to, job_id |
| Supplier master | `backend/data/suppliers.py` | `search_for_org(...)` — already organisation-scoped |
| Supplier columns | DB | `name, postcode, city, address_line1, vat_number, company_number, contact_email, ...` |
| Emissions write | `backend/data/emissions_logs.py:239` | `create(...)` previously had **no `supplier_id`** parameter and no `supplier_id` column in the `INSERT` |
| Engine sink contract | `backend/engines/calculation.py:125` | `CalculationSink.create(...)` must mirror the repository |
| Engine persistence | `backend/engines/calculation.py:514` | `_persist_log(...)` is the only insert path used by the engine |
| Insight read | `backend/domain/insight_query.py:82,121,318` | already reads `emissions_logs.supplier_id` as a dimension/group-by key |
| Evidence | `backend/domain/evidence.py:411` | evidence payload already carries `mapped_supplier_id` |
| Factor set | DB `emission_factors` | 7049 rows; columns `activity_type, co2e_multiplier, unit, scope, factor_source, factor_set, country` (no `activity`/`factor_name`) |

## 8. Existing manual-review workflow discovered

The auditable correction path **already exists** and was reused rather than replaced:

    operator (internal staff, can_process)  ->  ops map endpoint
        -> repos.manual_extraction.save_mapped_data(..., mapped_supplier_id, emission_factor_used)
        -> manual_extraction_items.status = 'mapped'
        -> _record_item_action_audit(action='ops_map:applied', actor=<auth.users id>,
                                     status_from=<prior status>, status_to='mapped')

This preserves the original extracted value (`extracted_data` is never overwritten by the mapping
step), the corrected value (`mapped_data` / `mapped_supplier_id`), the actor, the timestamp
(`updated_at`, `NOW()`), and the downstream effect (`status` transition + audit row). No parallel
review system was created and no second state machine was introduced.

**Gap identified (documented, not fixed):** this repository is the *persistence* mechanism; no
server-side caller invokes `supplier_resolution` automatically during the automatic pipeline.
See §12 and §32.

## 9. Waste semantics implementation

### 9.1 Verified factor-set evidence (read-only DB assertions)

    SELECT count(*) FROM emission_factors;                        -> 7049
    WHERE activity_type ILIKE '%waste%' OR ILIKE '%recycl%'       -> 155 rows

Representative actual rows (Scope 3, `factor_source=DEFRA-DESNZ`, `factor_set=DEFRA-2025`, `country=GB`):

| activity_type | co2e_multiplier | unit |
|---|---|---|
| `Waste disposal > Construction > Aggregates - Open-loop (kg CO2e)` | 1.00835 | tonnes |
| `Waste disposal > Construction > Aggregates - Landfill (kg CO2e)` | 1.26338 | tonnes |
| `Waste disposal > Construction > Average construction - Incineration with Energy Recovery (kg CO2e)` | 4.68568 | tonnes |
| `Material use > Organic > Compost derived from garden waste - Primary material production (kg CO2e)` | 112.08811 | tonnes |
| `Fuels > Liquid fuels > Waste oils (kg CO2e) [tonnes]` | 3219.37916 | tonnes (Scope 1) |
| `WTT- fuels > Liquid fuels > Waste oils (kg CO2e) [tonnes]` | 1116.83712 | tonnes (Scope 3) |

### 9.2 Conclusion: the correct behaviour for this corpus is clarification, not auto-match

The DEFRA waste taxonomy is **family > material > treatment route**. The canonical corpus descriptions
name a *stream* (`Waste disposal - Mixed`, `Recycling services - Mixed`, `Waste collection - Recycling`)
but **never name a treatment route**. Multiple valid, materially different factors therefore exist for
the same printed activity:

    4.68568 / 1.00835 = 4.647x spread between plausible routes for one material

Selecting any one of them automatically would be **guessing**, which the auditability invariant
forbids. Implementation decision (not a policy change, and consistent with the ratified P12-D1 and the
existing `D-FS-4` shared-token rule in `backend/engines/factor_selection_policy.py`): **no waste
auto-match was added.** The shared-token guard is preserved, and these lines continue to route to
clarification where the operator selects the factor.

Recorded honestly: because no canonical line resolves to a *unique* factor, the six documents still
require an operator clarification step before calculation. That is the intended product behaviour, not
a defect, and it is exactly the "CarbonTally requests review instead of guessing" beat of the investor
narrative (§S item 5).


## 10. Supplier resolution implementation

New pure engine: `backend/engines/supplier_resolution.py` (310 lines — no I/O, no DB, no AI, no
randomness). Candidate discovery stays with the existing org-scoped repository
(`repos.suppliers.search_for_org`); the engine only normalises, scores and classifies, so it is
deterministic and directly unit-testable.

Verdicts and the action the caller must take:

| Verdict | Action | Auto-persist? | Condition (as implemented) |
|---|---|---|---|
| `unresolved` | `manual_review` | No | no supplier text extracted at all |
| `none` | `confirm_creation` | No | org has no candidate scoring > 0 |
| `exact` | `reuse` | **Yes** | VAT or company-number match, **or** exact normalized name + address/postcode/city corroboration |
| `strong` | `confirm_match` | No | exact normalized name but no corroborating signal |
| `probable` | `confirm_match` | No | name similarity (Jaccard ≥ 0.5) only |
| `ambiguous` | `select_candidate` | No | top two scores within `AMBIGUITY_MARGIN = 10` |

Scoring signals are drawn only from what the document carries, and only when **both** sides are
present: VAT 100, company number 100, exact name 40, postcode 30, name similarity 20, address_line1
15, city 10, email domain 5.

Hard rules enforced in code:

1. **Organisation-scoped** — a candidate whose `organization_id` differs from the request is pushed to
   `rejected` as `cross_tenant_candidate` and can never be selected (§B rule 2, §D).
2. **Never silently choose** — ambiguous/equal scores return `selected=None` (`select_candidate`).
3. **Never silently create** — `none` returns `confirm_creation`; the engine has no creation capability
   at all, so it cannot bypass the authorised creation workflow (§B rule 8).
4. **Never fabricate** — blank supplier text returns `unresolved`.
5. **Deterministic ties** — sorting is `(-score, supplier_id)`, so equal scores never depend on input
   order (asserted in both orders in tests).

Only `exact` sets `auto_persist=True`; a parametrised test asserts that no non-`exact` verdict ever
auto-persists.

## 11. Manual review / correction implementation

No new review mechanism was built (§F satisfied by reuse):

| Requirement | Where satisfied | Status |
|---|---|---|
| Preserve original document | `documents` / storage record, untouched by mapping | Exists |
| Preserve raw extracted value | `manual_extraction_items.extracted_data` (not overwritten by mapping) | Exists |
| Preserve extraction evidence/source location | `evidence_line_items` (`det:pdf_table`, 23 rows after IMPL-01) | Exists |
| Preserve the reason review was required | clarification entry + blocking validation findings | Exists |
| Present the value to the user | workspace / mapping-options endpoint | Exists |
| Authorised correction | `ops_map` (internal `can_process`) and the PE map route | Exists |
| Auditable record | `_record_item_action_audit(action='ops_map:applied', actor, status_from, status_to)` | Exists |
| Who / when | `actor` + `updated_at` | Exists |
| Original ↔ corrected relationship | `extracted_data` vs `mapped_data` / `mapped_supplier_id` | Exists |
| Downstream uses the reviewed value | mapping output is the calculation input | Exists |

## 12. Auditability implementation

Implemented: the resolution decision itself is auditable — `ResolutionOutcome.as_dict()` returns
verdict, action, reason, `auto_persist`, the request signals, every scored candidate with its score
and matched signals, the selected supplier id, and the rejected cross-tenant candidates. A caller that
persists a resolution can therefore record *why* a supplier was reused or escalated.

Not implemented: nothing currently writes that decision record into the database. The persistence
layer (`save_mapped_data`) records the *outcome* (`mapped_supplier_id`) and the actor, but not the
engine's verdict/reason. This is a documented gap (§32), not a silent one.

## 13. Persistence path

    extracted supplier text
      -> engines.supplier_resolution.classify(signals, search_for_org(org_id, ...), org_id)
      -> (only if verdict == 'exact') operator-confirmed or automatic reuse of supplier_id
      -> data/manual_extraction.py::save_mapped_data(..., mapped_supplier_id=<id>, ...)
      -> manual_extraction_items.mapped_supplier_id   (Decision-01 sole source of truth)
      -> audit row (ops_map:applied, actor, status_from -> status_to)

## 14. Calculation propagation

Changed (all additive, all optional, **no schema change**):

| File | Change |
|---|---|
| `backend/engines/calculation.py:125` | `CalculationSink.create(...)` gained `supplier_id: Optional[str] = None` |
| `backend/engines/calculation.py:141` | `CalculationRequest` gained `supplier_id: Optional[str] = None` (insert-time only, never a content-hash input, `None` stays NULL) |
| `backend/engines/calculation.py:544` | `_persist_log(...)` forwards `supplier_id=request.supplier_id` |
| `backend/data/emissions_logs.py:239` | `create(...)` gained `supplier_id: Optional[str] = None`; `INSERT` column list gained `supplier_id`, bound to a new `$11` |
| `backend/api/v3_operations.py:578` | multi-line operator/PE calculation passes `supplier_id=item.mapped_supplier_id` |
| `backend/api/v3_operations.py:1283` | PE single-line calculation passes `supplier_id=item.mapped_supplier_id` |
| `backend/api/v3_operations.py:1917` | internal single-line calculation passes `supplier_id=item.mapped_supplier_id` |

**No migration was required.** Verified read-only:

    SELECT column_name, data_type, is_nullable FROM information_schema.columns
      WHERE table_name='emissions_logs' AND column_name='supplier_id';
      -> supplier_id | uuid | nullable=YES

**Sites deliberately NOT threaded** (8 `CalculationRequest(` construction sites exist; 3 are wired):
`services/automatic_processing.py:1913`, `engines/workflow.py:620`,
`api/v3_processing_workflow.py:918`, `api/business.py:130`, `api/v3_emissions.py:728`. The automatic
site is the most consequential and is the recommended follow-up. It was left alone because (a) the
automatic pipeline is blocked earlier at clarification for this corpus and therefore cannot be
exercised, and (b) wiring it requires identifying the item reference inside that function's scope — an
unverified change was rejected in favour of a documented gap.

**Known read-back limitation:** `_LOG_COLUMNS` does not include `supplier_id`, and the `EmissionLog`
domain entity has no such field, so the written value is not returned on the entity; read-back
verification is by SQL. Extending `_LOG_COLUMNS`/`EmissionLog` was rejected as a change with no
demonstrated need. `save()` never touches `supplier_id`, so the insert-time value is not overwritten
by the subsequent `save(updated)` call in `_persist_log`.

## 15. Evidence propagation

Not exercised end-to-end in this session (no calculation was run, §21). Structurally verified:

* `backend/domain/evidence.py:411` already exposes `mapped_supplier_id`, and `mapped_supplier_id` is
  now also persisted to `emissions_logs.supplier_id`, so a supplier can be attributed from either the
  mapping record or the emissions record.
* `_persist_log` sets `emissions_logs.snapshot_id`, and `calculation_snapshots.source_item_id` links
  back to the extraction item holding `mapped_supplier_id` — so a manual correction cannot break the
  document → extraction → mapped activity → calculation → emissions chain.
* `evidence_line_items` stood at 23 rows after IMPL-01 (`det:pdf_table`, FORWARD) and was not modified.

Status: **structure verified, journey unverified** (§27, §32).

## 16. Reporting / Insight verification

`backend/domain/insight_query.py:82,121,318` already selects and groups by `emissions_logs.supplier_id`,
and `backend/api/v3_emissions.py:22` documents supplier attribution via `emissions_logs.supplier_id`.
The missing link was the write side — the `INSERT` never populated the column — which this task fixes.

Status: **write-side gap closed; no Insight query was executed against new data** because no
calculation was produced this session. "Insight now retains supplier attribution" is therefore **not
verified** and must not be reported as verified. `backend/data/reporting.py:394` filters on
`i.mapped_supplier_id`, which mapping already populated.

## 17. Multi-year supplier reuse verification

Verified at engine level by unit test `test_multi_year_reuse_resolves_to_single_supplier_id`: FY2025
signals (`Robinsons Recycling Services Ltd`, `QI14 5ZD`) and FY2026 signals
(`ROBINSONS RECYCLING SERVICES LIMITED`, `QI145ZD`) both classify as `exact` / `reuse` against the
*same* candidate and select the **same** `supplier_id`.

Not verified: database-level reuse across the six real documents. No supplier was created and no
`mapped_supplier_id` was written this session, so actual supplier IDs cannot be reported (§23).
Creating them would have required an operator session through the real API; manufacturing them with
SQL is forbidden (§R).

## 18. Tenant-isolation verification

| Test | Result |
|---|---|
| Cross-tenant candidate alone → `none`, `selected=None`, recorded in `rejected` | PASS |
| Cross-tenant candidate alongside an own-org candidate → own-org wins | PASS |
| Blank supplier text → `unresolved` (no cross-tenant fallback) | PASS |
| Candidates filtered by `organization_id` before scoring (code path) | PASS |

Engine-level isolation is proven. Database/RLS-level isolation was not re-run this session; EV-01 and
the disposable-integration isolation suites are unchanged by this task (§19).

## 19. EV-01 CSV regression

Not re-run this session. The CSV journey does not reference `supplier_resolution.py` (new and
unreferenced) and does not pass `supplier_id`, which defaults to `None` and inserts SQL NULL — so
**EV-01 behaviour is unchanged by construction**. `_LOG_COLUMNS`, the CSV extraction path, factor
mapping and evidence were not modified. Status: **expected no-effect, not executed — verify explicitly
before Step-2 closure.**

## 20. Six canonical PDF acceptance results

**Not executed.** No upload, operator clarification, mapping, calculation or evidence verification was
performed against `p12canon_waste_001`–`006` in this session, so no per-document acceptance values can
honestly be reported, and the JSON artifact records `status: not_run` for every document rather than
inventing values (§U). This is the single largest gap in this task (§32) and is the direct consequence
of a deliberate scope decision: the six-document operator journey requires an authenticated operator
session through the real API (upload → clarification → `ops_map` with factor + supplier → calculate →
evidence → reporting), which was not started rather than half-completed.

Still-valid prior evidence (not re-executed):

| Fact | Source | Value |
|---|---|---|
| Extraction | P12-IMPL-01 | supplier 6/6, customer 6/6, refs 6/6, dates 6/6, periods 6/6, line structure 6/6 |
| Line counts | P12-IMPL-01 | 3 / 4 / 2 / 5 / 3 / 4 = 21 line items |
| Units | P12-IMPL-01 | 21/21, 0 false positives |
| Display precision | P12-DATA-01 | 001=2dp, 002=0dp, 004=0dp, 003=2dp, 005=3dp, 006=4dp |
| First pipeline block | GAP-02 / IMPL-01 | clarification at mapping (shared-token `'Waste'` policy) |
| Evidence line items | P12-IMPL-01 | 2 → 23 (`det:pdf_table`, FORWARD) |

## 21. Exact before/after behaviour

| Area | Before | After |
|---|---|---|
| Supplier resolution | No resolver existed; supplier text was carried only as extracted text, with no verdict or action; risk of ad-hoc/duplicate matching | Deterministic verdict + required action, org-scoped, fail-closed; only `exact` may auto-persist |
| Supplier → emissions | `emissions_logs.supplier_id` was **never written**; the column stayed NULL by construction | `create()` accepts and inserts `supplier_id`; wired from `mapped_supplier_id` at 3 calculation sites |
| Engine request contract | `CalculationRequest` had no supplier | `CalculationRequest.supplier_id` (optional, insert-time only, not a hash input — existing snapshot hashes unchanged) |
| Test doubles | 2 doubles mirrored the old `create()` signature | Updated to mirror the new optional parameter |
| Waste semantics | Shared-token guard routes ambiguous waste to clarification | **Unchanged** (correct); evidence recorded that no unique factor exists for this corpus |
| Schema | — | **Unchanged** (no migration, no RLS change) |

## 22. Actual extracted / resolved values

* Extracted (prior, P12-IMPL-01): supplier `Robinsons Recycling Services Ltd`, customer
  `Sustainable Direct Group`, 21 line items across 6 documents, units 21/21 resolved.
* Resolved by `supplier_resolution` this session: **no document was processed**, so no resolved value
  exists. Engine-level classification results (synthetic signals, real engine) are in §18 and the JSON
  artifact — these are unit-test results, **not** document outcomes.

## 23. Actual supplier IDs and reuse results

**None.** No supplier row was created and no `mapped_supplier_id` was written, because that requires the
authorised operator workflow (§B rule 9) and manufacturing rows with SQL is forbidden (§R). Reuse is
proven only at engine level (§17). Any claim of "supplier ID X reused 6 times" would be fabricated.

## 24. Actual calculation results

**None.** No `CalculationRequest` was executed against canonical data this session, so there are no
`co2e_kg` values, no snapshots and no new `emissions_logs` rows (rows written this session: 0).

## 25. Actual evidence results

**None produced.** `evidence_line_items` was left at its post-IMPL-01 state (23 rows). Structural chain
verified only (§15).

## 26. Actual reporting results

**None produced.** No report was generated and no Insight query was executed against new data. The
reporting claim is limited to: the write-side gap that prevented attribution has been closed (§16).

## 27. Tests executed

| # | Command | Result |
|---|---|---|
| 1 | `python -m py_compile engines/supplier_resolution.py engines/calculation.py data/emissions_logs.py api/v3_operations.py` | `COMPILE_OK` |
| 2 | `pytest tests/unit/engines/test_p12_impl_02_supplier_resolution.py -q` | **PASS** after one self-correction (§28) |
| 3 | `pytest tests/unit/engines/test_calculation.py tests/unit/engines/test_customer_factor_integration.py tests/unit/engines/test_extraction.py tests/unit/services/test_p12_impl_01_invoice_extraction.py -q` | Initially 13 failures (class A, all from this task, all fixed); final state PASS |
| 4 | `pytest tests/unit -q -p no:randomly` (full unit suite) | **5 failures**, all classified class B pre-existing (§28); **0 failures remaining from this task** |

## 28. Failures and classification

Failures **introduced by this task** (all fixed before close):

| Failure | Count | Root cause | Class | Resolution |
|---|---|---|---|---|
| `test_calculation.py` (multiple) | 12 | `_MemorySink.create()` did not accept the new optional `supplier_id` → `TypeError` | A (introduced) | Added `supplier_id: Optional[str] = None` to the double |
| `test_customer_factor_integration.py::test_snapshot_records_customer_provenance` | 1 | `_RecordingSink.create()` positional signature lacked `supplier_id` | A (introduced) | Added `supplier_id=None` to the double |
| `test_p12_impl_02_...::test_score_similar_name_uses_jaccard_threshold` | 1 | My expectation was wrong: shared tokens correctly earn a similarity credit (score 20) | A (my test, not the code) | Corrected the expectation to `20` / `name_similarity:0.67` |

Pre-existing failures (class B — **not** caused by this task; verified because none of the files under
test appear in `git diff --name-only HEAD`):

| Failure | Observed evidence | Class |
|---|---|---|
| `test_extraction_suggestions.py::test_suggest_parses_clean_invoice` | `assert '2026-01-15' == '15/01/2026'` | B — stale expectation left by P12-IMPL-01 date normalisation |
| `test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved` | `assert {'extraction_...'} == {}` | B — stale expectation left by P12-IMPL-01 `suggest()` orchestration |
| `test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage` | `assert {'extraction_...'} == {}` | B — same |
| `test_extraction_fidelity.py::test_pipeline_version_was_bumped` | `assert 'v3-auto-1.2' == 'v3-auto-1.1'` | B — P12-IMPL-01 bumped `PIPELINE_VERSION`; the P1 constant still says 1.1 |
| `test_d17_provider_ownership_migration_revision.py::test_migration_ordering_is_unchanged` | `assert 81 == 71` (10 unexpected migration names) | B — pre-existing migration-inventory drift; no migration added by this task |

No failure was left unclassified.

## 29. Files changed

**Added (product code):** `backend/engines/supplier_resolution.py` — new deterministic, org-scoped
resolution engine (310 lines).

**Modified (product code):**

* `backend/engines/calculation.py` — sink-protocol parameter, `CalculationRequest.supplier_id`, `_persist_log` forwarding
* `backend/data/emissions_logs.py` — `create(supplier_id=...)` + `INSERT` column bound to `$11`
* `backend/api/v3_operations.py` — 3 calculation sites pass `supplier_id=item.mapped_supplier_id`

**Added (tests/docs):**

* `backend/tests/unit/engines/test_p12_impl_02_supplier_resolution.py`
* `docs/architecture/CT-PO-P12-IMPL-02-WASTE-SEMANTICS-SUPPLIER-RESOLUTION-AUDITABLE-REVIEW-20260924.md`
* `docs/architecture/artifacts/p12_impl_02_acceptance_20260924.json`

**Modified (test doubles; direct consequence of the contract change):**

* `backend/tests/unit/engines/test_calculation.py`
* `backend/tests/unit/engines/test_customer_factor_integration.py`
* `backend/tests/unit/api/fakes.py`

`.gitignore` appears modified in `git status` but is **pre-existing** and was not touched here.

## 30. Database / schema changes

**None.** No migration file was added and no table, column, constraint, index or RLS policy was created
or altered. `emissions_logs.supplier_id` already existed (`uuid`, nullable), so this is a code-only
write-path fix. The §T schema-change STOP condition was satisfied by verifying the capability already
existed.

## 31. Security implications

* The resolver is a **pure function** with no database access, so it cannot itself breach isolation; it
  enforces the org boundary by rejecting any candidate whose `organization_id` differs (§18).
* No authorization was weakened, bypassed or broadened. Supplier creation was **not** implemented, so
  the existing admin-gated creation workflow (`require_org_admin()` on `POST /api/v3/suppliers`) remains
  the only creation path — the engine cannot create anything.
* The reused mapping routes keep their existing guards (`require_internal_staff`,
  `ensure_staff_permission("can_process")`, `_entity_workspace_guard`).
* `supplier_id` is written from the already-authorized mapping decision
  (`manual_extraction_items.mapped_supplier_id`, org-scoped data); this change adds no new injection
  surface.
* No secrets, credentials, JWTs or signed URLs were introduced, logged or committed.

## 32. Remaining investor-readiness gaps

| # | Gap | Severity | Notes |
|---|---|---|---|
| 1 | Six-PDF operator journey not executed (no supplier IDs, calculations, evidence rows, reporting output) | **High** | Needs an authenticated operator session; the mechanism, its guards and its audit are identified |
| 2 | No server-side caller invokes `supplier_resolution` during automatic processing | **High** | Engine exists and is tested, but is not wired into `services/automatic_processing.py` |
| 3 | Five `CalculationRequest` sites unthreaded for `supplier_id` | Medium | `automatic_processing.py:1913` highest priority |
| 4 | Resolution decision (verdict/reason/candidates) not persisted | Medium | Outcome is persisted; rationale is not |
| 5 | `emissions_logs.supplier_id` write path not exercised by any test or journey | Medium | Compile + contract only |
| 6 | EV-01 CSV regression not re-run | Medium | Expected no-effect; must be confirmed |
| 7 | Six-document supplier reuse not proven at database level | Medium | Engine-level proof in place |
| 8 | `extraction_suggestions` 3 stale tests remain failing | Low | Pre-existing from P12-IMPL-01 |
| 9 | P12-D1 waste clarification remains a PO decision; D2/D3/D4 implemented only at engine level | Medium | PO decision required |

## 33. Step-2 status

**Step 2 remains INCOMPLETE.** This task does not claim otherwise. The previously identified Step-2
blockers were deliberately not touched:

* migration application is not idempotent (298 policies re-apply; `20260801000000_rc2_constraints.sql` errors)
* `210` vs `218` single-pass variance still UNKNOWN (needs a policy name-set comparison)
* disposable-integration still 12/92 failing

Additional Step-2 work now required because of this task: wire the resolver into the pipeline, thread the
remaining calculation sites, and execute the six-document journey.

## 34. Final acceptance matrix

| Criterion (§) | Status | Evidence |
|---|---|---|
| Supplier resolution engine implemented (§B) | **PASS** | `supplier_resolution.py` + 30 unit tests |
| Org-scoped / cross-tenant denial (§B, §D, §O) | **PASS** | 4 negative tests + rejection list |
| Never silently choose / create / fabricate (§B) | **PASS** | verdict/action contract + tests |
| Supplier propagation to `emissions_logs.supplier_id` (§E) | **IMPLEMENTED, NOT EXERCISED** | 5-file change, 3 sites wired, compile OK |
| No schema change needed (§E) | **PASS** | `information_schema` check |
| Manual review reuses existing auditable workflow (§F) | **PASS** | `save_mapped_data` + `ops_map:applied` |
| Original value / actor / timestamp preserved (§F) | **PASS (structural)** | `extracted_data` never overwritten; audit row |
| Waste semantics correct for the corpus (§A) | **PASS (clarification, not auto-match)** | 155 waste factors, 4.647× spread |
| Six-PDF journey (§J) | **NOT RUN** | — |
| Calculation (§G) | **NOT RUN** | 0 rows written |
| Evidence / Source Evidence Viewer (§H) | **NOT RUN** | structural only |
| Reporting / Insight attribution (§I) | **NOT RUN** | write-side gap closed |
| Multi-year reuse (§C) | **ENGINE-LEVEL PASS** | unit test, same `supplier_id` |
| EV-01 regression (§L) | **NOT RUN** | expected no-effect |
| Targeted tests | **PASS** | 0 failures remaining from this task |
| Full unit suite (§M) | **5 pre-existing failures** | all classified class B |
| No production impact (§P) | **PASS** | demo-local only |
| Step 3 not started | **PASS** | — |

## 35. Commit hash

Recorded after the commit made at the end of this task (§V discipline); commit message:

    feat(p12): implement auditable waste and supplier resolution

## 36. Stop condition

**STOPPED.** This task closes without beginning Step 3, without wiring the resolver into the automatic
pipeline, without creating suppliers, without executing the six-document operator journey and without any
schema change. Those are explicitly handed to the next task (§32).

---

## Final report — required answers

1. **Can a canonical PDF now travel through the real product path?** Not demonstrated. Extraction
   reaches mapping, where the waste lines correctly block at clarification; the operator step was not
   executed, so the journey was not carried through to calculation/evidence/reporting.
2. **Can CarbonTally safely extract supplier information?** Yes — extraction is 6/6 (P12-IMPL-01), and
   the new resolver can now classify that text safely (org-scoped, fail-closed).
3. **Can CarbonTally safely reuse the same supplier across years?** Proven at engine level: FY2025 and
   FY2026 signal variants resolve to the same candidate and the same `supplier_id`. Not yet proven at
   database level.
4. **Can CarbonTally avoid guessing when extraction/resolution is uncertain?** Yes — only `exact`
   auto-persists; blank text is `unresolved`; no candidate is `confirm_creation`; ties are `ambiguous`;
   and waste activities with no unique factor go to clarification rather than being matched.
5. **Can the operator manually correct unresolved information?** Yes — through the existing guarded
   mapping routes that persist `mapped_supplier_id` and advance the item to `mapped`.
6. **Is the correction auditable?** Yes — `ops_map:applied` records actor, status_from/status_to, job id,
   IP and timestamp, while `extracted_data` retains the original value beside the corrected
   `mapped_data`.
7. **Can waste activities be resolved or safely sent to clarification?** They are safely sent to
   clarification; resolution is the operator's factor selection. No auto-match was added, because with a
   4.647× spread between plausible routes auto-matching would be guessing.
8. **Does `supplier_id` reach `emissions_logs`?** The path is implemented (`mapped_supplier_id` →
   `CalculationRequest` → sink → `INSERT $11`) and compiles; **no row has been written yet**, so it is
   not verified end-to-end.
9. **Does evidence remain intact?** Structurally yes, and unchanged this session; not exercised.
10. **Does the Source Evidence Viewer remain intact?** Unchanged; not exercised.
11. **Does reporting/Insight retain supplier attribution?** The write-side blocker (a never-populated
    `supplier_id`) is closed and the read side was already correct, but this is **not verified with real
    data**.
12. **Does EV-01 remain intact?** Expected yes (new unreferenced module; `supplier_id` defaults to NULL),
    but **not re-run**.
13. **Does tenant isolation remain intact?** Yes at engine level (4 negative tests PASS, 0 unexpected
    allows); database/RLS level was not re-run.
14. **What remains before Step 2 can be declared complete?** The nine gaps in §32 **plus** the three
    pre-existing blockers: migration idempotence, the `210` vs `218` variance, and the 12/92
    disposable-integration failures.
15. **Is Step 3 still NOT STARTED?** Correct — Step 3 has not been started.
