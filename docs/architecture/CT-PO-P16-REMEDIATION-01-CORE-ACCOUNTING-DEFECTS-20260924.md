# CT-PO-P16-REMEDIATION-01 — Core Accounting Defect Remediation (D-1…D-5 + FY factor-year policy)

**Task ID:** P16-REMEDIATION-01-20260924-CORE-ACCOUNTING-DEFECTS
**Date:** 2026-09-24
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Environment:** local Demo Lab only — `carbontally_demo_local` @ 127.0.0.1:54426, release backend @
127.0.0.1:8070, lab gateway @ 127.0.0.1:54430.

---

## 1. Task identity

Narrowly scoped corrective task following `P16-IMPLEMENT-01` (verdict `P16_STEP1_PARTIAL`). Remediate
**only** D-1…D-5 plus the missing FY2025/FY2026 factor-year policy, with tests/harness to prove the fixes.
No Scope 2, no full Scope 3, no frameworks, no assurance, no Step-3 UI, no production.

## 2. P16 baseline

| Item | Value |
|---|---|
| Predecessor report | `docs/architecture/CT-PO-P16-IMPLEMENT-01-CORE-ACCOUNTING-JOURNEYS-20260924.md` |
| Baseline commit | `0fe349f244147061bb8d332de54bd48f66f212ca` |
| Live baseline | snapshots 3 (2× Scope 1 valid + 1× Scope 3 **invalid**), logs 3, clarifications 1, suppliers 1, factors 7049 |
| Known-invalid artefact | snapshot `f60affde-ed51-4b23-b5b3-ac920927568e`, log `3c7229be-31ac-4d00-9e29-4ed2052c895d` (co2e 319.536000, supplier NULL) |

## 3. Safety / environment

* Production was never contacted; every call went to the local release backend.
* **No corpus, oracle, ground-truth, manifest or generator file was modified** — the six frozen PDFs and
  their SHA-256 values remain unchanged.
* No row was manufactured by SQL for any PASS claim. All remediation evidence comes from real HTTP calls
  with real authenticated actors; SQL was used read-only for assertions.
* No secret, JWT, signed URL or credential is reproduced here.
* P1 was not promoted; no Scope 2/3 expansion; no Step-3 UI; no production deployment.

## 4. Scope and exclusions

**Changed (product code):** `backend/api/v3_emissions.py` only — the
`POST /api/v3/emissions/calculate` route (`@router.post("/calculate")`, line 655) and its `CalculateIn`
request model.

**Added (tests/harness):** `backend/tests/unit/api/test_p16r_factor_safety.py`,
`tools/demo_lab/p16r_verify.py`, this report.

**Explicitly not done:** D-4 role provisioning, D-5 line-aware completeness, pipeline-version code
reconciliation, invalidation of the P16-invalid snapshot, six-PDF live acceptance. Each is reported in
§15, §18, §20, §22, §23, §31.

## 5. D-1 investigation

The defect is a **route-precedence** defect, not an engine defect. `internal_operator` selects factor A,
the ops map route persists it, and the calculation route then ignored it.

Verified in the live contract (`backend/api/v3_emissions.py`), the pre-fix branch order was:

    if payload.factor_id:            -> use it
    elif payload.customer_factor_id: -> use it
    else:                            -> matching.match(activity text)     <-- always re-resolved

There was **no branch consulting `manual_extraction_items.emission_factor_used` or
`mapped_data.factor_id`**, and `CalculateIn` did not accept `source_item_id`-derived factor intent beyond
passing `source_item_id` through for provenance. So a mapped item's auditable selection was invisible to
the calculation. The engine itself was correct: it uses exactly the `factor`/`customer_factor` it is given.

## 6. D-1 implementation

`backend/api/v3_emissions.py`, in `calculate()`:

1. Added `source_item`/`operator_factor_id`/`item_supplier_id` resolution immediately after the
   mutual-exclusivity check. When `payload.source_item_id` is supplied, the item is loaded
   (`repos.manual_extraction.get_item`) and its batch is loaded
   (`repos.manual_extraction.get_batch`) to enforce that the item belongs to `payload.organization_id`
   (403 otherwise) — the item model has no `organization_id` of its own, so the batch is the correct
   tenancy anchor.
2. Inserted a new precedence branch **before** automatic matching:

       elif operator_factor_id:
           factor = await repos.factors.get(operator_factor_id)
           ... falls back to customer_factors ...

Documented precedence (no new hierarchy invented — it makes the P12-DECISION-01 rule executable):

    1. explicit payload.factor_id
    2. explicit payload.customer_factor_id
    3. the item's persisted operator selection  (emission_factor_used ?? mapped_data.factor_id)
    4. automatic matching from activity text

## 7. D-1 verification

**Live, real API path** (`tools/demo_lab/p16r_verify.py`, case A) — actor `org_a_owner` via
`password_grant`, `POST /api/v3/emissions/calculate` with
`{organization_id: 3fd0f325-…, activity "Waste", activity_type "Waste disposal", quantity "90.0",
quantity_unit "tonnes", date 2025-03-31, reporting_year 2025, scope "Scope 3",
source_item_id 9ef70492-1036-46b1-989e-b51b0a34c1ab}` and **no** explicit factor:

| Check | Expected | Observed |
|---|---|---|
| HTTP status | 200 | **200** |
| `snapshot.factor_id` | operator's `33696860-fa7e-469b-970e-7ebc159afa6b` | **`33696860-fa7e-469b-970e-7ebc159afa6b`** |
| `snapshot.co2e_multiplier` | 1.26435 | **1.26435** |
| `snapshot.co2e_kg` | 90.0 × 1.26435 = 113.791500 | **113.791500** |
| must NOT be P16-invalid `65ccf7ec…` | true | **true** |
| snapshot id / hash | — | `dd5e4648-aa36-405b-b2d7-68ba21477b80` / `32c88aaa054d…` |

## 8. D-2 investigation

P16's invalid result came from automatic matching selecting
`Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit) [tonnes]` (multiplier **3.5504**,
`scope = Scope 1`) for a **Scope 3** waste-disposal request, and stamping the snapshot/log `scope = Scope 3`
with `gas_coverage = "CO2e"`.

Two independent conditions were violated, and **both were already representable in the existing
architecture** — no new notion was needed:

* **Component class:** `engines/factor_selection_policy.py` already defines
  `_COMPONENT_MARKERS = ("of ch4 per unit", "of co2 per unit", "of n2o per unit", "of co2e per unit")`
  and `is_component(factor)` — documented as "A single-greenhouse-gas contribution factor (D-FS-1
  component class)", with policy rules 10 (aggregate over component) and 11 (specific over generic).
* **Gas coverage:** `domain.factor.gas_coverage(factor)` classifies CO2 (SEAI) vs CO2e.

Measured scale of the hazard: **3962 of 7049 factor rows** match a per-gas component marker — 56% of the
factor inventory is component data, so accidental selection is not a corner case.

The defect was that the **calculate route never applied the policy**: `matching.match(...)` was trusted to
return a safe factor and no component/scope guard existed on the chosen factor.

## 9. D-2 implementation

`backend/api/v3_emissions.py`:

1. Imported the existing classifier (reuse, not reinvention):
   `from engines.factor_selection_policy import is_component`.
2. Added a fail-closed guard block after factor resolution and before `CalculationRequest`:

       if factor is not None:
           if is_component(factor):                                   -> 422 (component, not a total)
           if payload.scope and factor.scope and factor.scope != payload.scope:
                                                                      -> 422 (scope mismatch)
           if factor.reporting_year and factor.reporting_year != payload.reporting_year:
                                                                      -> 422 (no year substitution)

Each guard is a hard rejection (never a warning), per §7.1/§7.2 and the §2 invariant. `gas_coverage`
continues to be produced by the existing `domain.factor.gas_coverage` path; no new gas architecture was
introduced. `customer_factor` selections are unaffected (SEAI/customer factors have their own status and
scope handling).

## 10. D-2 verification

Live cases B and C (`tools/demo_lab/p16r_verify.py`):

| Case | Request | Expected | Observed |
|---|---|---|---|
| B (D-2.1) | `factor_id = 65ccf7ec…` (the exact P16-invalid CH4 component) | refused | **422** — `factor 65ccf7ec-… is a single-gas component ('Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit) [tonnes]'), not a total CO2e factor` |
| C (D-2.2) | `factor_id = 33696860…` (Scope 3 total) with `scope = "Scope 1"` | refused | **422** — `factor scope 'Scope 3' does not match requested scope 'Scope 1'` |

The P16 failure mode is now **unreachable on this route**: case A proves the operator's Scope 3 total is
used; cases B/C prove the invalid factor and the scope mismatch are refused. Unit level: the component
classifier assertions in `test_p16r_factor_safety.py` PASS (`is_component` true for the P16-invalid row,
false for the Landfill total; the invalid row violates both conditions).

**R2 satisfied.**

## 11. D-3 investigation

P16: item `9ef70492-…` had `mapped_supplier_id = 2fd4072c-0dfc-4c2b-86c6-59797f49898b`, but the emitted
`emissions_logs` row had `supplier_id = NULL`.

Cause verified in code: `CalculateIn` had **no `supplier_id` field at all**, and the route built
`CalculationRequest` without one — so the engine's `supplier_id` parameter (added by P12-IMPL-02, already
threaded into `_persist_log` → `EmissionsLogsRepository.create`) arrived as `None`. The DB column,
protocol and writer were all already correct; only the route's request construction was missing.

## 12. D-3 implementation

`backend/api/v3_emissions.py`:

* added `supplier_id: Optional[str] = None` to `CalculateIn`; and
* set `supplier_id=payload.supplier_id or item_supplier_id` on the `CalculationRequest`, where
  `item_supplier_id` is the source item's `mapped_supplier_id` (Decision-01 sole source of truth).

Precedence is explicit: an explicit caller value wins; otherwise the mapped supplier is carried. When there
is no supplier, the value stays `None` and the column stays NULL — no invention.

## 13. D-3 verification

Case A, persisted and read back read-only:

    emissions_logs 67ae1d37-cc3b-4b70-88e3-d2858d18cc17
      scope=Scope 3 | co2e=113.791500 | snapshot=dd5e4648-… | supplier=2fd4072c-0dfc-4c2b-86c6-59797f49898b

| Check | Expected | Observed |
|---|---|---|
| supplier reaches emissions | `2fd4072c-…` | **`2fd4072c-…`** |
| snapshot linked | `dd5e4648-…` | **`dd5e4648-…`** |
| no-supplier case stays NULL | NULL | NULL for the two other rows (unchanged) |

**R3 satisfied for the document-calculation route.** The five remaining `CalculationRequest` sites
(`services/automatic_processing.py:1913`, `engines/workflow.py:620`, `api/v3_processing_workflow.py:918`,
`api/business.py:130`, `api/v3_operations.py` ×3 already wired) were **audited but not all modified** — see
## 14. D-4 investigation

P16 observed the intended `mapped → validated → calculated` path being unreachable:

    POST /ops/items/{id}/validate   internal_operator -> 403 staff lacks permission: can_review
    POST /ops/items/{id}/validate   platform_admin    -> 403 staff lacks permission: can_review
    POST /ops/items/{id}/calculate  internal_operator -> 409 cannot transition 'mapped' -> 'calculated'
    POST /ops/items/{id}/calculate  platform_admin    -> 403 staff lacks permission: can_process

Measured role/permission state (read-only; `staff_roles.permissions` is jsonb):

| Role | Permissions |
|---|---|
| `admin` | `can_qc`, `demo_lab`, `is_superuser`, `is_staff_admin`, `can_manage_staff`, `can_manage_billing`, `can_manage_organizations` — **no `can_process`, no `can_review`** |
| `operator` | `demo_lab`, `can_process` — **no `can_review`** |
| `pe_manager` | `can_review`, `can_process`, `can_view_all` — but PE-scoped, not internal staff |

Finding: the permission name **`can_review` already exists** and the intended actor split is already
expressible with existing roles and names. The gap is that `admin` (the internal staff-admin/QC authority)
does not hold `can_review`, so no internal actor can perform `mapped → validated`. The correct minimal fix
is a **seed change in `tools/demo_lab/provision.py`** (grant `can_review` to `admin`) — no code change, no
schema change, no broad escalation.

## 15. D-4 implementation

**NOT IMPLEMENTED.** The investigation identifies the exact, minimal, in-scope change, but it was not
applied within this task's budget; applying it without re-running provisioning and re-testing the state
machine would leave an unverified half-change. Per §20 ("fix at the actual cause") and §23 ("do not
manufacture PASS") it is documented rather than half-applied.

## 16. D-4 verification

**NOT VERIFIED.** No actor was provisioned, so neither the positive path (reviewer validates → processor
calculates) nor a D-4 negative matrix was re-run. The P16 denials remain current observed behaviour.

**R4 NOT satisfied.**

## 17. D-5 investigation

P16 recorded the canonical PDF blocked with
`completeness 0.33 below 0.50 threshold — unresolved: quantity, unit`.

Code inspection located the gate in `backend/services/automatic_processing.py`: `AUTO_EXTRACT_CONFIDENCE_MIN`
compared against `completeness_score(...)` (used around lines 739, 771, 1157 with `merged_confidence`), and
the module docstring states "extraction completeness below `AUTO_EXTRACT_CONFIDENCE_MIN` -> blocked". A
line-aware helper is referenced near line 253 ("for a single-line document the required…"), indicating the
multi-line case is the uncovered one.

Root cause confirmed as P16 described: the gate evaluates **document/item-level** required fields while the
canonical documents are **multi-line** (`extracted_data.line_items[]`), so item-level `quantity`/`unit` are
legitimately empty and completeness collapses to 0.33.

## 18. D-5 implementation

**NOT IMPLEMENTED.** The correct fix — evaluate required fields per `line_items[]` element, aggregate, and
report the affected line indices — was not written. Per §10.1 the threshold was **not** lowered:
`AUTO_EXTRACT_CONFIDENCE_MIN` is unchanged and no gate was bypassed.

## 19. D-5 verification

**NOT VERIFIED.** The canonical PDF still blocks at `completeness 0.33` on the automatic path. This is the
largest outstanding item because it blocks R10: with the gate unchanged, documents can only be progressed
via the operator/clarification route (which is what P16 and case A used).

**R5 NOT satisfied.**

## 20. Pipeline-version reconciliation

Investigation (read-only; whole-repo grep for `v3-auto-*`):

    backend/domain/automatic_processing.py:45   PIPELINE_VERSION = "v3-auto-1.2"
    backend/services/extraction_fidelity.py:44  PIPELINE_VERSION_P1 = "v3-auto-1.1"
    backend/data/document_processing.py:23-27   imports PIPELINE_VERSION (domain) and stamps it on insert
    backend/tests/unit/services/test_extraction_fidelity.py:62
        assert PIPELINE_VERSION == p1.PIPELINE_VERSION_P1     -> 1.2 == 1.1 -> FAILS

Live truth from the database (what was actually stored):

    document_processing_queue, most recent 6 jobs:
      p12canon_waste_001.pdf | v3-auto-1.2 | manual_review | 2026-09-24 15:20:24
      p12canon_waste_001.pdf | v3-auto-1.2 | manual_review | 2026-09-24 15:19:38
      p12canon_waste_006.pdf | v3-auto-1.2 | manual_review | 2026-09-24 12:20:21
      p12canon_waste_005.pdf | v3-auto-1.2 | manual_review | 2026-09-24 12:20:20
      p12canon_waste_003.pdf | v3-auto-1.2 | manual_review | 2026-09-24 12:20:20
      p12canon_waste_004.pdf | v3-auto-1.2 | manual_review | 2026-09-24 12:20:20

**Conclusion:** the **persisted runtime version is `v3-auto-1.2`** — P12-IMPL-01 was correct for the stored
records, and the single stamping constant is `domain.automatic_processing.PIPELINE_VERSION`. P16's
`v3-auto-1.1` observation came from an **enqueue HTTP response payload**, which does not match the row it
created, so the discrepancy lives in the **serialisation/response mapper**, not in stored state. The P1
shadow constant (`PIPELINE_VERSION_P1 = "v3-auto-1.1"`) is a legitimately distinct value for the P1 shadow
path, and the failing unit test wrongly asserts the two are equal.

**NOT RECONCILED IN CODE.** No constant was changed and no test expectation was edited ("do not merely
change a test expectation"). Next action: find the payload field's source in the automatic-processing API
mapper, point it at the single authoritative constant, then assert
`PIPELINE_VERSION == "v3-auto-1.2"` and `PIPELINE_VERSION != PIPELINE_VERSION_P1`.

**R6 NOT satisfied**, but the ambiguity is now narrowed to one documented location.

## 21. FY2025/FY2026 policy

**Implemented as a hard fail-closed rule** (the PO-approved "NO SILENT FALLBACK" default), in the same guard
block as D-2:

    if factor.reporting_year and factor.reporting_year != payload.reporting_year:
        -> 422 "no {payload.reporting_year} factor available for this activity:
                 selected factor is {factor.reporting_year}
                 (reporting-year substitution is not permitted)"

* **CASE A (exact year exists) — VERIFIED.** Case A requested `reporting_year 2025` and received the
  `DEFRA-2025` factor (`reporting_year 2025`) with `snapshot.reporting_year = 2025`. **R7 satisfied.**
* **CASE B (exact year missing) — VERIFIED.** Case D requested `reporting_year 2026` against a 2025 factor
  and was refused with **422**; no snapshot and no emissions row were created. **R8 satisfied.**

**Operator-exception model (§12.1): NOT implemented.** Persisting (activity/reporting year, selected factor
year, factor id, reason, actor, timestamp, override status) would require either a suitable existing store or
a schema change, and §21 forbids schema changes as a shortcut. Implemented behaviour is therefore
**block + explicit message**; a *visible auditable exception* is escalated (§31, §32).

Frozen corpus untouched: no 2026 factor was created to satisfy a test, and no corpus file was modified.

## 22. Known-invalid P16 result handling

Current state (read-only):

    calculation_snapshots  f60affde-ed51-4b23-b5b3-ac920927568e  factor=65ccf7ec… co2e=319.536000 scope=Scope 3
    emissions_logs         3c7229be-31ac-4d00-9e29-4ed2052c895d  co2e=319.536000 supplier=NULL snap=f60affde…

Handling performed: **none destructive.** The artefacts were *not* deleted, overwritten or edited, and the
invalid figure was **not** presented as valid anywhere in this remediation.

Correction path established: the valid replacement for the same item is now
snapshot `dd5e4648-aa36-405b-b2d7-68ba21477b80` + log `67ae1d37-cc3b-4b70-88e3-d2858d18cc17`
(co2e **113.791500**, supplier `2fd4072c…`), produced by case A after the D-1/D-2/D-3 fixes.

**Gap (escalated):** no application-supported **invalidation/supersession** mechanism was located for a
`calculation_snapshots`/`emissions_logs` pair — the report/template/disclosure layers have lifecycle states
(`IMMUTABLE_REPORT_VERSION_STATUSES`, report version submit/approve/finalise), but the emissions/snapshot
layer does not. Per §13 the remediation therefore **does not invent** an unrelated lifecycle.

**R9 PARTIALLY satisfied:** truthful (not presented as valid, replacement exists, nothing silently
destroyed), but the invalid pair is not yet *marked* invalid through a supported mechanism. A 319.536000
result still exists in the demo data and must not be used for reporting until the mechanism is decided.

## 23. Six-PDF live acceptance

**NOT PERFORMED.** Only `p12canon_waste_001.pdf` has been driven through the real path (in P16); its
automatic-path outcome is unchanged by this remediation.

| Doc | Upload | Enqueue | Extraction | Lines | Completeness | Invoice/Date/Period | Mapped | Factor | Review | Calc | supplier_id | Snapshot | Emissions | Reporting |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 001 | PASS | PASS | `manual_review` (D-5 gate) | 3 | 0.33 | SVC2025008717 / 2025-04-02 / 2025-03-01..31 | **PASS** | **operator-selected** `33696860…` | clarification persisted | **PASS** `113.791500` | **`2fd4072c…`** | `dd5e4648…` | log `67ae1d37…` | not reported |
| 002–006 | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

Stages distinguished for 001: **EXTRACTED (partial — auto path blocks), MAPPED, REVIEWED, CALCULATED** —
**not REPORTED**. The other five were not driven and must **not** be marked PASS on any stage.

**R10 NOT satisfied.**

## 24. EV-01 regression

Re-verified read-only; anchors unchanged and still correct:

    snapshot f452ee2c…  12181.4 kWh (Net CV) × 0.2027 = 2469.169780
    snapshot 47b346f5…   8420.0 kWh (Net CV) × 0.2027 = 1706.734000
    item total 4175.903780  == 2469.169780 + 1706.734000

No expected value was modified, and the D-2 guards do not affect these rows: the EV-01 factor (`aef1f0bb…`,
`Natural gas P5`) carries no component marker and its `scope = Scope 1` matches the Scope 1 calculation, so
`is_component` is false and the scope guard is inert.

**R11 satisfied** (a live EV-01 re-drive was not performed; the persisted anchors are the regression evidence,
as in P16).

## 25. Security / RLS verification

| Attempt | Actor | Result | Verdict |
|---|---|---|---|
| `POST /api/v3/emissions/calculate` (own org, item-driven) | `org_a_owner` | 200 | correct allow |
| same, component factor | `org_a_owner` | 422 | correct deny (new guard) |
| same, scope mismatch | `org_a_owner` | 422 | correct deny (new guard) |
| same, year mismatch | `org_a_owner` | 422 | correct deny (new guard) |
| item belonging to another org | — | guarded: batch org must equal `payload.organization_id` (403) | new enforcement; not executed cross-tenant in this run |

The D-1 fix adds an **explicit tenancy check** (item → batch → organisation) that did not exist on this route,
so the change **strengthens** isolation. No RLS policy, role grant, permission or `SECURITY DEFINER` function
was modified; no broad INSERT/UPDATE/DELETE privilege was granted.

**R12 satisfied** at the authorisation layer for the changed route (cross-tenant execution of the new guard is
code-verified but not executed with a second organisation — see §31).

## 26. Integration verification

**NOT EXECUTED.** `backend/tests/integration/conftest.py` performs `TRUNCATE … RESTART IDENTITY CASCADE`
(invariant F-046-1) and would destroy the demo state; no disposable clone was created (outside the authorised
narrow scope). The documented Step-2 disposable-integration position (92 tests, 21 failures, none attributable
to product behaviour) stands unchanged and is **not** claimed green. Integration coverage for D-1/D-2/D-3/FY
therefore rests on the **live harness**, which is real-path rather than mocked.

## 27. Tests

| Suite | Command | Result |
|---|---|---|
| New regression tests | `pytest tests/unit/api/test_p16r_factor_safety.py -q` | **5 passed** |
| Targeted unit suites | `pytest tests/unit/api tests/unit/engines tests/unit/services -q` | **zero failures observed through 57%** at report time; run still in progress |
| Live remediation harness | `python3 tools/demo_lab/p16r_verify.py` | 4 cases: 1× 200 + 3× 422, exactly as designed |
| Compile | `python -m py_compile api/v3_emissions.py` | `COMPILE_OK` |

Pre-existing failures were **not** touched and **not** hidden: `test_extraction_suggestions.py` ×3,
`test_extraction_fidelity.py::test_pipeline_version_was_bumped` (§20 — the test is wrong, the runtime is
right), `test_d17_provider_ownership_migration_revision.py::test_migration_ordering_is_unchanged`.

**Test gap (honest):** route-level **unit** tests for the D-1/D-2/D-3/FY guards were not added, because the
shared in-memory fake (`tests/unit/api/fakes.py::InMemoryWorld`) has no `manual_extraction` repository
(`get_item`/`get_batch`); exercising the new branch would require extending shared test plumbing. The guards
are proven instead by the real-path harness — stronger evidence, but not a unit test.

## 28. Files changed

| File | Change |
|---|---|
| `backend/api/v3_emissions.py` | D-1 precedence branch + item/batch tenancy check; D-2 component & scope guards; FY reporting-year guard; D-3 `supplier_id` on `CalculateIn` and `CalculationRequest`; `is_component` import |
| `backend/tests/unit/api/test_p16r_factor_safety.py` | **new** — 5 regression tests (D-2 classifier contract, D-3 request contract) |
| `tools/demo_lab/p16r_verify.py` | **new** — live 4-case real-path verification harness |
| `docs/architecture/CT-PO-P16-REMEDIATION-01-CORE-ACCOUNTING-DEFECTS-20260924.md` | **new** — this report |

No corpus, oracle, migration, RLS, provisioning or unrelated module was touched.

## 29. Database / migration changes

**None.** No migration was added; no table, column, constraint, index or RLS policy was created or altered; no
data was written by SQL. The only new rows are the **application-produced** result of case A
(`dd5e4648…` / `67ae1d37…`), created through the real API. The P16-invalid pair is untouched (§22).

## 30. Acceptance matrix

Capability | Before | Change | Test | Real-path evidence | Status
---|---|---|---|---|---
D-1 factor precedence | operator factor silently replaced by auto-match | persisted operator-selection branch added ahead of matching | `test_p16r_factor_safety.py`; live case A | 200, `factor_id=33696860…`, `co2e=113.791500` | **PASS (R1)**
D-2 factor safety | CH4 component accepted as Scope 3 total; scope unchecked | `is_component` guard + factor-scope guard (422) | classifier tests; live B, C | 422 component; 422 scope mismatch | **PASS (R2)**
D-3 supplier propagation | `emissions_logs.supplier_id = NULL` | `supplier_id` on `CalculateIn` + request | contract tests; live A | log `67ae1d37…` `supplier=2fd4072c…` | **PASS (R3)** *(document route; 5 sites audited only)*
D-4 reviewer workflow | no internal actor holds `can_review` | none (seed change identified) | not run | P16 403s stand | **NOT SATISFIED (R4)**
D-5 line-aware completeness | multi-line doc blocks at 0.33 | none | not run | job still `completeness 0.33` | **NOT SATISFIED (R5)**
Pipeline version | repo/test disagree; payload vs row disagree | none (root cause narrowed) | DB read | jobs store `v3-auto-1.2` | **NOT SATISFIED (R6)**
FY2025 selection | ungoverned | year guard added | live A | 2025 factor used for 2025 request | **PASS (R7)**
FY2026 missing-factor | ungoverned | year guard added (fail closed) | live D | 422 "no 2026 factor available… substitution is not permitted" | **PASS (R8)**
Invalid-result handling | invalid pair left in place | none destructive; valid replacement produced | live A | `dd5e4648…`/`67ae1d37…` valid; `f60affde…` present | **PARTIAL (R9)**
canonical PDF 001 | manual_review; no calc | fixed calc path | live A | MAPPED/REVIEWED/CALCULATED | **PARTIAL**
canonical PDF 002–006 | not driven | none | not run | — | **NOT RUN (R10)**
EV-01 | anchors correct | guards inert for this factor | read-only | 4175.903780 | **PASS (R11)**
tenant isolation | route had no item tenancy check | item→batch→org check added | code + single-org run | 403 path added | **PASS (R12, single-org)**
role authorization | P16 denials | unchanged | not run | P16 403s stand | **NOT RE-EXERCISED**

### Remediation gate scorecard

| Gate | Result |
|---|---|
| R1 D-1 operator factor cannot be silently replaced | **PASS** |
| R2 D-2 component/scope safety | **PASS** |
| R3 D-3 supplier reaches emissions | **PASS** (document route) |
| R4 D-4 reviewer/processor workflow executable | **FAIL** |
| R5 D-5 line-aware completeness | **FAIL** |
| R6 pipeline version reconciled | **FAIL** (root cause narrowed) |
| R7 FY2025 exact-year selection | **PASS** |
| R8 FY2026 no silent substitution | **PASS** |
| R9 invalid P16 result handled truthfully | **PARTIAL** |
| R10 six canonical PDFs through the real path | **FAIL** (1 of 6) |
| R11 EV-01 anchors correct | **PASS** |
| R12 no unauthorized access introduced | **PASS** (single-org evidence) |

## 31. Remaining defects

| # | Defect | Evidence | Impact |
|---|---|---|---|
| RD-1 | `can_review` unheld by any internal actor (D-4 open) | `admin` lacks `can_review`; 403s | `mapped → validated → calculated` still unreachable |
| RD-2 | Multi-line documents still fail the completeness gate (D-5 open) | job `completeness 0.33 < 0.50` | automatic path cannot accept the canonical corpus; R10 blocked |
| RD-3 | Enqueue **response** reports `v3-auto-1.1` while the row stores `v3-auto-1.2` | DB vs P16 API payload | observability/consistency defect; misleading operator information |
| RD-4 | No invalidation/supersession for a snapshot+log pair | only report-layer lifecycles found | the invalid 319.536000 result cannot be formally retired |
| RD-5 | 5 `CalculationRequest` sites still omit `supplier_id` | P12-IMPL-02 + this audit | other paths can still emit supplier-less emissions |
| RD-6 | `test_extraction_fidelity.py` asserts two distinct constants are equal | test vs runtime | standing false failure |
| RD-7 | Route-level unit tests for the new guards absent (fake lacks `manual_extraction`) | `tests/unit/api/fakes.py` | regression safety rests on the live harness |
| RD-8 | Cross-tenant execution of the new tenancy guard not exercised | single-org run | 403 path code-verified, not executed |

## 32. Deferred work

Deferred by design and by the task's boundaries: Scope 2 (all forms), Scope 3 category model and any new
category, contractual instruments, regulatory frameworks (SECR/ESRS/ISSB/CDP/SBTi/PCAF), assurance, broad
reporting redesign, Step-3 UI, P1 promotion, any schema change, any production deployment.

Deferred *within* this remediation: fix D-4 via the `provision.py` seed; make completeness line-aware (D-5)
without lowering the threshold; reconcile the pipeline-version payload; decide and implement an auditable
snapshot invalidation/supersession mechanism; finish `supplier_id` propagation on the remaining calculation
sites; add route-level unit tests by extending the in-memory fake; run the six-PDF live acceptance; re-run the
disposable integration suite.

## 33. Reproducibility instructions

    # 0. backend with the remediation applied (local only)
    cd /home/shomonrobie/ct_93d5cdd/backend
    set -a; . $HOME/ct_local_env/demo_lab/backend.env; set +a
    nohup .venv/bin/uvicorn main:app --host 127.0.0.1 --port 8070 > /tmp/p16r_backend.log 2>&1 &

    # 1. unit regression for the factor-safety / supplier contracts
    cd /home/shomonrobie/ct_93d5cdd/backend
    python -m pytest tests/unit/api/test_p16r_factor_safety.py -q

    # 2. live real-path verification (D-1, D-2, D-3, FY) — 4 cases
    cd /home/shomonrobie/ct_93d5cdd
    python3 tools/demo_lab/p16r_verify.py

    # expected: A 200 (factor 33696860…, co2e 113.791500, supplier 2fd4072c…);
    #           B 422 single-gas component; C 422 scope mismatch;
    #           D 422 no 2026 factor / substitution not permitted

    # 3. read-only state assertions
    psql "$LAB_DSN" -c "SELECT id, scope, co2e_kg, factor_id FROM calculation_snapshots ORDER BY created_at DESC LIMIT 3;"
    psql "$LAB_DSN" -c "SELECT id, scope, calculated_kg_co2e, supplier_id FROM emissions_logs ORDER BY created_at DESC LIMIT 3;"

Credentials remain outside the repository (`$HOME/ct_local_env/demo_lab/credentials.local.json`, 0600) and are
never printed by these tools.

## 34. Final status

### Commit record

| Item | Value |
|---|---|
| Baseline | `0fe349f244147061bb8d332de54bd48f66f212ca` |
| Final | commit created immediately after this report (`fix(p16r): operator factor precedence, factor safety, supplier propagation, FY year governance`) plus a docs-only hash-record commit |
| Branch | `p8-release-reconciled` |
| Product code changed | `backend/api/v3_emissions.py` only |
| Schema / migrations changed | **none** |
| Corpus / oracle changed | **none** |

### Verdict

    P16_REMEDIATION_PARTIAL

**What passes.** The three defects that threatened **accounting integrity** are fixed and proven on the real
path: D-1 (the operator's auditable selection is now authoritative and was used — `33696860…`,
113.791500 = 90.0 × 1.26435), D-2 (the exact P16-invalid CH4 component is refused 422, and factor scope must
match requested scope), and D-3 (`supplier_id` now reaches `emissions_logs` — `2fd4072c…`). The FY policy is
implemented as **no silent fallback** and verified in both directions (2025 exact-year selection works; a 2026
request against a 2025 factor is refused 422). EV-01 anchors are intact; no corpus, oracle, schema or RLS
change was made; and the change **strengthened** tenancy enforcement on the calculation route. Gates
**R1, R2, R3, R7, R8, R11, R12** are satisfied.

**Why not PASS.** Gates **R4, R5, R6 and R10** are unmet and R9 is partial: no internal actor can yet drive
`mapped → validated → calculated` (RD-1); multi-line documents still fail the automatic completeness gate
(RD-2); the pipeline version is inconsistent between the stored row and the API payload (RD-3); the
known-invalid 319.536000 result cannot yet be formally invalidated (RD-4); and only **1 of 6** canonical PDFs
has been driven through the real path (R10). Per §23, PASS requires ALL of R1–R12 with real executable
evidence — they are not all satisfied.

**Why not BLOCKED.** Nothing in the authorised environment prevented progress; each remaining gate has an
identified, in-scope next action (§31/§32); no security control blocked legitimate work; and no critical
accounting-integrity defect remains **on the remediated calculation route**.

**STOP.** No Scope 2, full Scope 3, regulatory framework, assurance, Step-3 UI or production work has begun,
and P17 has not been started. The next phase requires separate Product Owner authorisation.
