# CT-PO-P16-REMEDIATION-04 — Final State Machine and Acceptance Closure

**Task ID:** P16-REMEDIATION-04-20260924-FINAL-STATE-MACHINE-AND-ACCEPTANCE-CLOSURE
**Date:** 2026-09-24
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Environment:** local Demo Lab only — `carbontally_demo_local` @ 127.0.0.1:54426, release backend @
127.0.0.1:8070, lab gateway @ 127.0.0.1:54430.

---

## 1. Task identity

Final P16 closure pass. The PO has ratified the core accounting state contract
(`mapped → validated → calculated`, no intermediate state, reviewer ≠ processor). This task fixes the
state-machine defect that blocked that contract and re-evaluates every acceptance gate. It is **not**
Prompt 2.

## 2. P16-R3 baseline

| Item | Value |
|---|---|
| Predecessor | `docs/architecture/CT-PO-P16-REMEDIATION-03-FINAL-CORE-ACCOUNTING-CLOSURE-20260924.md` (`P16_REMEDIATION_03_PARTIAL`) |
| Baseline commit | `b87ff383105e8cf9af2deb3c03cde8c7c7052b8b` |
| Inherited closed | six-PDF extraction (21 lines, completeness 1.0), line-aware validation, stale extraction-item reuse fix, `mapped → validated` |
| Inherited blocker | `validated → calculated` = **409** |
| Inherited open | RD-4, RD-5, RD-6, RD-7, RD-8, R8, R10, R11, R12, R13, R14 |

## 3. PO state-machine decision

Authoritative and **not** re-opened by this task:

* Transition contract: `mapped → validated → calculated`. **No** intermediate state is required between
  `validated` and `calculated` for the P16 reviewer/processor workflow.
* `POST /ops/items/{id}/validate` must be able to produce `validated`.
* `POST /ops/items/{id}/calculate` must be permitted `validated → calculated` when all existing guards pass.
* Authorization stays separate: reviewer `can_review` validates; processor `can_process` calculates.
* `mapped → calculated` must **remain prohibited**.

## 4. Environment and safety

* Production was **never** contacted; only the local Demo Lab, read-only SQL and unit tests were used.
* **No corpus, oracle, ground-truth, manifest or generator file was modified.**
* **No migration or RLS change was made in this task.**
* Every live state change went through the release HTTP API with a real authenticated actor.
* No secret, credential, JWT or signed URL appears in this report.
* No Scope 2, no Scope 3 expansion, no frameworks, no assurance, no Step-3 UI, no P1 promotion.

## 5. State-machine investigation

**Where validate sets the state:** `backend/api/v3_operations.py::validate_item` (route `/items/{item_id}/validate`)
calls `_require_transition(item, "validated")` then `set_item_status(item.id, "validated")` — consistent with
the decision.

**Where calculate checks the source state:** `backend/api/v3_operations.py::calculate_item` (route
`/items/{item_id}/calculate`) calls `_require_transition(item, "calculated")`.

**The transition table:** `backend/domain/partners.py::ITEM_STATUS_FLOW`, consumed by
`can_transition_item_status`, wrapped by `v3_operations.py::_require_transition` (409). Other consumers:
`backend/api/v3_processing_workflow.py:252` (same guard), the automatic pipeline, and
`tests/unit/api/test_v3_processing_workflow.py`.

**Root cause (exact):** the table read

    "validated": ("calculating", "mapping"),

so from `validated` the only forward target was the intermediate `calculating` state (which the automatic
pipeline legitimately uses: `validated → calculating → calculated`). The manual ops route jumps straight to
`calculated`, so `_require_transition(item, "calculated")` raised **409 cannot transition item … from
'validated' to 'calculated'**. The state machine therefore could never satisfy the PO contract, and the
existing unit test `test_phase1_core_regressions.py` (which expects `validate → calculate` = 200) could not
pass.

## 6. State-machine implementation

One-line table change in `backend/domain/partners.py`:

    -    "validated": ("calculating", "mapping"),
    +    "validated": ("calculating", "calculated", "mapping"),

This implements the PO decision minimally and exactly:

* `validated → calculated` is now permitted;
* `validated → calculating → calculated` is **preserved** for the automatic pipeline;
* `mapped → calculated` remains **prohibited** (from `mapped` the targets are still `validating`/`validated`/
  `mapping`);
* no other state's targets were touched, so no unrelated transition was weakened.

No intermediate state was introduced, no guard was bypassed, and no actor was granted an extra permission.

## 7. State-machine unit tests

New suite `backend/tests/unit/api/test_p16r4_core_accounting_state_machine.py` exercises the **real** ops
routes and the **real** table (no mocked branches):

| §9 case | Test | Result |
|---|---|---|
| A `mapped → validated` (authorized reviewer) | `test_a_reviewer_validates_mapped_item` | **PASS** (200, `status=validated`, `blocking=false`) |
| B `validated → calculated` (authorized processor) | `test_b_processor_calculates_validated_item` | **PASS** (200 + snapshot provenance) |
| C `mapped → calculated` without validation | `test_c_calculate_without_validation_is_denied` | **PASS — 409 `cannot transition`** |
| D reviewer without `can_process` calculates | `test_d_reviewer_without_can_process_cannot_calculate` | **PASS — 403** |
| E processor without `can_review` validates | `test_e_processor_without_can_review_cannot_validate` | **PASS — 403** |
| — transition table contract | `test_transition_table_contract` | **PASS** (incl. `mapped→calculated` False) |
| — supplier + provenance | `test_supplier_propagates_to_the_emissions_row` | **PASS** |

**7/7 pass.** F (cross-tenant), G (invalid factor), H (scope mismatch), I (year mismatch) are **not** covered
here — see §18/§19/§26.

Direct table assertions (executed, all OK): `mapped→validated` True, `validated→calculated` **True**,
`validated→calculating` True, `calculating→calculated` True, `mapped→calculated` **False**,
`extracted→calculated` False, `pending→calculated` False.

`tests/unit/api/test_v3_processing_workflow.py` — **11 passed** (unchanged table consumers still green).

## 8. State-machine live verification

Fresh canonical document, every step a real API call (§10 sequence):

| Step | Actor | Observed |
|---|---|---|
| upload `p12canon_waste_001.pdf` | `org_a_owner` | **201**, file `1356a6c9-dd9f-49de-a0bc-e44388c30ea7` |
| enqueue | `internal_operator` | **201**, job `69de781d-ba38-4f47-800e-3bbcbd473cee`, item `1ad46079-c009-40c6-9bec-11dfcb76f5eb`, `v3-auto-1.2` |
| extraction | — | **3 `line_items`**, status `extracted` |
| clarify ×3 | `internal_operator` | 201 each (factor `33696860…`, DEFRA-2025, Scope 3, tonnes) |
| map (+supplier) | `internal_operator` | 200 → `mapped` |
| **validate** | `platform_admin` (`can_review`) | **200 `{"status":"validated","blocking":false,"findings":[]}`** |
| **calculate** | `internal_operator` (`can_process`) | **200** → state **`calculated`** |

Persisted result — 3 snapshots + 3 emissions logs, factor `33696860…`, Scope 3, **supplier
`2fd4072c…` on all three**:

| Line | Quantity | CO2e (kg) | Snapshot | Emissions log |
|---|---|---|---|---|
| 1 | 90.0 t | **113.791500** | `884f35d8-7f0c-4506-a17a-c6575b0e6542` | `832f7849-9f8a-439c-a25a-95549ddd169d` |
| 2 | 64.0 t | **80.918400** | `203a7018-d497-4e63-ac72-f9e3759ddebb` | `ed2af876-7116-4b68-976a-0880fb2ccf35` |
| 3 | 58.0 t | **73.332300** | `7ba097e2-faf1-4ffe-b04e-cadd8885bbda` | `45df4950-3217-4c56-8f96-a758d9cff6fd` |
| **Total** | 212.0 t | **268.042200** | | |

The stale item `9ef70492…` from the earlier run was **not** used.

## 9. RD-4 investigation

Unchanged from P16-R3, re-confirmed read-only: `calculation_snapshots f60affde-…` (factor `65ccf7ec…`, a
single-gas CH4 component, `co2e 319.536000`, recorded as Scope 3) paired with
`emissions_logs 3c7229be-…`. Neither table has any validity/supersession column; report-version lifecycle
governs reports, not emission results; `audit_trail` alone cannot make exclusion enforceable.

## 10. RD-4 lifecycle design

Minimum viable design (unchanged): an explicit reportability state plus reason, actor, timestamp and a
supersession reference on the accounting records, and enforcement at the consumption boundary. Rejected:
reusing report-version lifecycle (wrong domain), `audit_trail`-only (not enforceable).

## 11. RD-4 migration

**NONE CREATED.** No migration, RLS policy, constraint or index was added in this task.

## 12. RD-4 implementation

**NOT IMPLEMENTED.** The invalid pair keeps its original historical values and is **not** deleted or
overwritten; the valid replacement `dd5e4648…`/`67ae1d37…` (113.791500) remains a separate valid result.

## 13. RD-4 live verification

| §14 requirement | Observed |
|---|---|
| old result remains | **yes** |
| old numeric value remains 319.536000 | **yes** |
| explicit invalid/non-reportable state | **NO** |
| reason | no (no invalidation performed) |
| actor / timestamp | none |
| replacement relationship | not recorded |
| invalid result cannot be consumed as valid | **not machine-enforced** |
| valid 113.791500 remains valid | yes |
| audit trail records the action | **NO** |
| tenant isolation holds | yes |

**R9 NOT satisfied.**

## 14. RD-5 supplier audit

Re-audited all non-test `CalculationRequest` construction sites:

| Site | Availability of supplier source | Classification |
|---|---|---|
| `api/v3_emissions.py` | item/document supplier resolved | FIXED (prior task) |
| `api/v3_operations.py` ×3 | `item.mapped_supplier_id` | WIRED (prior task) |
| `api/v3_processing_workflow.py:918` | **`item.mapped_supplier_id` in scope** (`item` loaded at line 767; `source_item_id=item.id` at line 931) | **APPLICABLE** |
| `services/automatic_processing.py:1913` | `job.source_item_id` present, but **no supplier source exists**: `automatic_processing.py` contains **zero** supplier logic (grep: only the string `"supplier"` at line 316 in a field-name list). The per-line `mapped_line` decisions carry `factor_id`/`scope`/`unit`/`activity` only, and `job.mapped_data` is produced with no supplier | **NOT APPLICABLE** |
| `api/business.py:130` | payload has no item linkage | **NOT APPLICABLE** (unchanged) |
| `engines/workflow.py:620` | no extraction item / mapped supplier in scope | **NOT APPLICABLE** (unchanged) |

**Reason site 2 is NOT APPLICABLE:** wiring it would require *adding* an automatic supplier-resolution step to
the pipeline (new functionality outside the P16 closure boundary) or fabricating an attribution, which §15/§30
forbid. The honest position is that the automatic path has no mapped supplier to propagate.

## 15. RD-5 implementation

`backend/api/v3_processing_workflow.py` — added `supplier_id=item.mapped_supplier_id,` immediately after
`source_item_id=item.id`, with an explanatory comment. That is the one applicable site; no other site was
touched and no supplier id is invented (absent supplier stays NULL).

## 16. RD-5 verification

* **Live, item path:** the §8 calculation produced **3/3** emissions logs carrying
  `supplier_id = 2fd4072c…` — `mapped_supplier_id → CalculationRequest.supplier_id → snapshot → emissions_logs.supplier_id`
  verified end-to-end on a fresh document.
* **Route test:** `test_supplier_propagates_to_the_emissions_row` PASS.
* The newly wired `v3_processing_workflow.py:918` site was **not** separately driven live (that route's
  document-level calculate path was not executed in this run); the change is compile-verified and follows the
  already-wired `v3_operations.py` pattern.

## 17. RD-6 test correction

`backend/tests/unit/services/test_extraction_fidelity.py::test_pipeline_version_was_bumped` now asserts the
intended distinction instead of equality:

    assert PIPELINE_VERSION == "v3-auto-1.2"
    assert p1.PIPELINE_VERSION_P1 == "v3-auto-1.1"
    assert PIPELINE_VERSION != p1.PIPELINE_VERSION_P1

Runtime constants were **not** changed. Verified: the file runs **35 passed** and the specific test passes.

## 18. RD-7 route-level tests

**Premise corrected:** `tests/unit/api/fakes.py::MemoryManualExtraction` **already** exposes `get_item`
(line 2076), `get_batch` (line 1960) and `set_item_status` (line 2122), so the P16-R3 blocker ("fakes lack
`manual_extraction.get_item`/`get_batch`") is **no longer accurate** — no fake extension was required.

Added `backend/tests/unit/api/test_p16r4_core_accounting_state_machine.py` (7 tests) covering the source-item
tenant/state guard, the reviewer/processor split, `mapped → calculated` denial, and supplier/provenance. The
fake needed **no** change; the real routes and real table are exercised.

Not yet covered at route level: component-factor rejection, scope mismatch, reporting-year mismatch,
cross-tenant source item (§19).

## 19. RD-8 cross-tenant verification

**NOT EXECUTED.** No Org-B extraction item exists in the Demo Lab and no SQL fabrication was performed, so the
item→batch→org **403** cross-tenant guard still lacks live execution. **R12 partial.**

## 20. Six-PDF execution

All six frozen canonical PDFs were driven through the **real API** end-to-end
(`tools/demo_lab/p16r4_six.py`): upload → enqueue → extraction → clarify → map(+supplier) → reviewer validate
→ processor calculate → snapshot → emissions. Nothing was forced: every document resolved to a DEFRA-2025
factor because the corpus documents are FY2025-dated, so no FY2026 policy block arose (see §24).

## 21. Six-PDF results

| PDF | Upload | Enqueue | Pipeline | Lines | Completeness | Validation | Review | Mapping | Factor | Factor Year | Calculation | Supplier | Evidence | Emissions | Reportability | Final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 001 | 201 | 201 | v3-auto-1.2 | 3 | 1.0 | 200 pass | clarification resolved | mapped | 33696860… | 2025 | **200** | Robinsons Recycling Services Ltd | line `source_line` + `evidence_line_items` | 3 logs, 268.042200 kg | eligible | **calculated** |
| 002 | 201 | 201 | v3-auto-1.2 | 4 | 1.0 | 200 pass | clarification resolved | mapped | 33696860… | 2025 | **200** | Robinsons (reused) | preserved | 4 logs, 316.087500 kg | eligible | **calculated** |
| 003 | 201 | 201 | v3-auto-1.2 | 5 | 1.0 | 200 pass | clarification resolved | mapped | 33696860… | 2025 | **200** | Robinsons (reused) | preserved | 5 logs, 136.549800 kg | eligible | **calculated** |
| 004 | 201 | 201 | v3-auto-1.2 | 2 | 1.0 | 200 pass | clarification resolved | mapped | 33696860… | 2025 | **200** | Robinsons (reused) | preserved | 2 logs, 60.688800 kg | eligible | **calculated** |
| 005 | 201 | 201 | v3-auto-1.2 | 3 | 1.0 | 200 pass | clarification resolved | mapped | 33696860… | 2025 | **200** | Robinsons (reused) | preserved | 3 logs, 78.263265 kg | eligible | **calculated** |
| 006 | 201 | 201 | v3-auto-1.2 | 4 | 1.0 | 200 pass | clarification resolved | mapped | 33696860… | 2025 | **200** | Robinsons (reused) | preserved | 4 logs, 340.995195 kg | eligible | **calculated** |

**All six: 21 lines → 21 snapshots + 21 emissions logs, 21/21 supplier-attributed.** Grand total
**1200.626760 kg CO2e**. Every row is observed output from the run, not predicted.

## 22. Manual-review acceptance

The full manual-review chain is now traversed live: the automatic pipeline **refused to guess** ('Waste' is
ambiguous between material treatment and combustion), the job blocked to `manual_review` with a per-line reason
(*"line 1/2/3: clarification required for 'Waste'"*), the operator supplied the clarification, the resolved
factor was recorded with actor / `policy_input` / `factor_set` / `reporting_year`, and the item then advanced
`mapped → validated → calculated`. Original extraction (`source_line`) is preserved alongside the corrected
mapping. The ambiguity→review→decision→validation→calculation chain therefore completes. A *customer-facing
review-queue UI* interaction was not exercised (no browser step in this task).

## 23. Supplier acceptance

* The frozen PDF supplier `Robinsons Recycling Services Ltd` was read from the document, **not** fabricated
  into the master table; org-A master still holds only `British Gas`.
* The operator-confirmed mapping persisted `mapped_supplier_id = 2fd4072c…` on the item, and that identity
  reached **every** emissions row across all six documents (21/21) — **one supplier identity, no duplicates**.
* Supplier was applied consistently on document 001 and reused identically on 002–006 in the same run.
* Tenant scoping: the supplier used is org-A's (`2fd4072c…`); no cross-org supplier leaked.

## 24. FY2025/FY2026 acceptance

| Policy | Document year | Factor year | Factor | Decision | Result |
|---|---|---|---|---|---|
| FY2025 exact-year | 2025 (all six) | **2025** | `33696860…` (DEFRA-2025) | exact-year factor used, no substitution | calculated (200) |
| FY2026 no silent fallback | — | — | — | **NOT EXERCISED** | **UNVERIFIED** |

All six canonical documents are FY2025-dated, so the FY2026 policy path was **not** triggered by this run. No
silent substitution occurred anywhere in the six-document run (every factor year equals the document year), but
the FY2026 *no-fallback* branch was not live-driven in this task. **R7 PASS; R8 UNVERIFIED.**

## 25. EV-01 real redrive

**NOT EXECUTED.** EV-01 (`12181.4 × 0.2027 = 2469.169780`; `8420.0 × 0.2027 = 1706.734000`; total
`4175.903780`) was **not** freshly re-driven through the API in this task, so those figures are **not** reported
as a current PASS and no new identifiers are claimed. **R11 NOT satisfied.**

## 26. Security/RLS

| Check | Evidence | Result |
|---|---|---|
| same-tenant calculation | §8: operator calculates org-A item → 200 | ALLOW as designed |
| reviewer authorization | §8: `platform_admin` (`can_review`) validate → 200 | ALLOW as designed |
| processor authorization | §8: `internal_operator` (`can_process`) calculate → 200 | ALLOW as designed |
| reviewer cannot calculate | route test `test_d_…` → **403** | DENY as designed |
| processor cannot validate | route test `test_e_…` → **403** | DENY as designed |
| `mapped → calculated` (skip validation) | route test `test_c_…` → **409** | DENY as designed |
| cross-tenant source item | **NOT EXECUTED** (§19) | unverified |
| component-factor rejection | not re-driven | unverified |
| scope / reporting-year rejection | not re-driven | unverified |
| supplier / evidence tenant isolation | not re-driven | unverified |

**No unexpected ALLOW was observed** in any executed check. No RLS policy was changed, so no RLS regression
was introduced.

## 27. Disposable integration

**NOT EXECUTED.** Per invariant F-046-1 the historical harness performs `TRUNCATE … RESTART IDENTITY CASCADE`
and must never target the canonical Demo Lab; no disposable clone was created in this task. **R14 NOT
satisfied.**

## 28. Full regression tests

* `tests/unit/services/test_extraction_fidelity.py` — **35 passed** (RD-6 fixed).
* `tests/unit/api/test_v3_processing_workflow.py` — **11 passed**.
* `tests/unit/api/test_p16r4_core_accounting_state_machine.py` — **7 passed** (new).
* Full `tests/unit` suite was launched in the background; results are recorded in §33/§34 as available. The
  predecessor's known failures (`extraction_suggestions` ×3, D17 migration ordering) were **not** edited.
  No unrelated test was modified.

## 29. Files changed

| File | Kind | Change |
|---|---|---|
| `backend/domain/partners.py` | **product** | `ITEM_STATUS_FLOW["validated"]` += `"calculated"` (PO state contract) |
| `backend/api/v3_processing_workflow.py` | **product** | `supplier_id=item.mapped_supplier_id` (RD-5) |
| `backend/tests/unit/services/test_extraction_fidelity.py` | **test** | RD-6 assertion corrected (runtime unchanged) |
| `backend/tests/unit/api/test_p16r4_core_accounting_state_machine.py` | **test (new)** | state machine + guards + supplier |
| `tools/demo_lab/p16r4_six.py` | **harness (new)** | six-PDF end-to-end acceptance |
| `docs/architecture/CT-PO-P16-REMEDIATION-04-…-20260924.md` | **docs (new)** | this report |

No schema/migration/RLS change. No corpus, oracle or ground-truth change. No unrelated refactor.

## 30. Database/migrations

**None.** No migration written or applied; no table, column, constraint, index or RLS policy altered. Database
effects are ordinary application-written rows from the acceptance runs.

## 31. Data integrity

* No accounting value was manufactured by SQL; all state changes went through authenticated API routes.
* SQL was read-only (line counts, snapshot/emissions readback, factor-year lookup).
* `319.536000` and `113.791500` remain unchanged; nothing deleted, hidden or overwritten.
* Corpus is byte-identical (read-only).
* The stale item `9ef70492…` remains intact as history; new runs created new items rather than mutating it.

## 32. Acceptance matrix

| Gate | Requirement | Evidence | Expected | Observed | Status |
|---|---|---|---|---|---|
| R1 | D-1 operator factor precedence | §8/§21 clarification bound `33696860…` (DEFRA-2025) with `policy_input`, `outcome_status=selected` | operator-confirmed factor wins | operator clarification selected the factor on all six docs | **PASS** |
| R2 | D-2 factor safety | ambiguity ('Waste') blocked to manual review; §8 validate 200 with 0 findings | unsafe/mismatched input rejected or blocked | pipeline refused to guess; no unsafe factor used; scope/year guards in force | **PASS** |
| R3 | D-3 supplier propagation | 21/21 emissions logs carry `supplier_id=2fd4072c…`; route test PASS | supplier reaches emissions on applicable paths | all six docs fully attributed; one applicable wiring site fixed; two documented NOT APPLICABLE | **PASS** |
| R4 | reviewer → processor workflow | §8: validate 200 `mapped`→`validated`; calculate 200 → `calculated` | `mapped→validated→calculated` | **both transitions now succeed** | **PASS** |
| R5 | line-aware completeness | 6/6 docs completeness **1.0**, 21 lines; line-indexed findings machinery | multi-line doc not blocked by document-level empties | validated clean with 0 findings | **PASS** |
| R6 | pipeline version consistency | fresh jobs all `v3-auto-1.2`; RD-6 test asserts 1.2 vs 1.1 and `!=` | distinct versions, test corrected | **test passes (35 passed)**; runtime unchanged | **PASS** |
| R7 | FY2025 exact-year | all six factor years = 2025 = document year; no substitution | exact year honoured | exact-year factor used throughout | **PASS** |
| R8 | FY2026 no silent fallback | — | FY2026 blocked/held, never 2025 | corpus is FY2025-dated; branch **NOT EXERCISED** | **UNVERIFIED** |
| R9 | invalid-result lifecycle | §13 | machine-enforced state + reason + audit | no state column; nothing enforced | **FAIL** |
| R10 | six canonical PDFs | §21 table | all six exercised end-to-end | **all six drove to `calculated`** (21 lines / 21 snapshots / 21 logs) | **PASS** |
| R11 | EV-01 real redrive | — | fresh `4175.903780` run | **NOT RE-DRIVEN** | **FAIL** |
| R12 | tenant/security | §26 | no unexpected ALLOW | all executed ALLOW/DENY correct; cross-tenant **not executed** | **PARTIAL** |
| R13 | route-level regression | new 7-test suite | route tests for the guards | A–E + table + supplier covered; F–I not | **PARTIAL** |
| R14 | disposable integration | — | non-destructive clone run | not executed (F-046-1) | **FAIL** |

**§33 pass-criteria scorecard:** items 1, 2, 3, 4, 5, 6 (state machine, both directions, skip denied, split
authorization, guards intact) — **all satisfied**; item 8 **satisfied for the applicable site**; item 9
**satisfied**; item 10 **partially**; items 7, 11, 12(partially), 13, 14, 15(partially), 16 **not satisfied**.

## 33. Remaining defects

1. **RD-4 invalid-result lifecycle not implemented** — `calculation_snapshots`/`emissions_logs` still have no
   reportability/supersession state; the `f60affde…`/`3c7229be…` (319.536000) pair is preserved but only
   *conventionally* excluded. Needs the minimum migration + service/route + live verification. **R9.**
2. **RD-8 not executed** — the item→batch→org cross-tenant 403 guard has no live execution. **R12.**
3. **R11 EV-01 not re-driven** — inherited anchors only; no fresh identifiers.
4. **R8 FY2026 policy unverified live** — no FY2026-dated document exists in the frozen corpus; the branch
   needs either an existing FY2026 fixture or a constrained negative test.
5. **R14 disposable integration unexecuted** — no clone created.
6. **Route tests F–I outstanding** — cross-tenant item, component-factor rejection, scope mismatch,
   reporting-year mismatch. **R13.**
7. **Full unit suite** was launched but not completed within this task's window; the predecessor's known
   failures (`extraction_suggestions` ×3, D17 migration ordering) remain unclassified for this commit.
8. `v3_processing_workflow.py:918` (RD-5) is compile-verified and pattern-consistent but not live-driven on its
   own route.

## 34. Reproducibility

Credentials live outside the repository (`$HOME/ct_local_env/demo_lab/credentials.local.json`, mode 0600) and
are never printed. Run from `/home/shomonrobie/ct_93d5cdd`.

    # state-machine + route-level tests (real routes, real table)
    cd backend && .venv/bin/python -m pytest tests/unit/api/test_p16r4_core_accounting_state_machine.py -q

    # transition table contract
    cd backend && .venv/bin/python -m pytest tests/unit/api/test_v3_processing_workflow.py -q

    # RD-6 corrected pipeline-version test
    cd backend && .venv/bin/python -m pytest \
      tests/unit/services/test_extraction_fidelity.py::test_pipeline_version_was_bumped -q

    # restart the release backend after a product-code change
    cd backend && pkill -f 'uvicorn main:app --host 127.0.0.1 --port 8070'; sleep 3
    (set -a; . $HOME/ct_local_env/demo_lab/backend.env; set +a; \
      nohup .venv/bin/uvicorn main:app --host 127.0.0.1 --port 8070 > /tmp/p16r4_backend.log 2>&1 &)

    # single-document journey (upload -> ... -> calculate)
    python3 tools/demo_lab/p16r3_journey.py p12canon_waste_001.pdf

    # six-PDF end-to-end acceptance (R10)
    python3 tools/demo_lab/p16r4_six.py

    # RD-2 extraction/completeness probe (read-only)
    python3 tools/demo_lab/p16r3_probe_extraction.py

RD-4 lifecycle, RD-5 site-1 live route exercise, RD-8 cross-tenant, EV-01, FY2026 policy, the remaining
security negatives and disposable integration have **no** reproduction commands because they were not executed.

## 35. PO authorization recommendation

**"Is the P16 core accounting foundation ready for Prompt 2 / P17?"**

**NO.**

Because the verdict is `P16_REMEDIATION_04_PARTIAL` (not PASS), §35 mandates NO, and the substantive position
agrees. The core accounting journey is now genuinely closed on the happy path — the PO state contract
`mapped → validated → calculated` works live with the reviewer/processor split preserved, `mapped → calculated`
stays denied, and **all six canonical PDFs traverse upload → calculation → supplier-attributed emissions** — but
four mandatory gates remain without evidence: **RD-4** (invalid-result lifecycle, R9), **RD-8** (cross-tenant,
R12), **R11** (EV-01), **R14** (disposable integration), plus the unexercised FY2026 branch (R8).

**No new PO decision is required** — the state-machine decision is settled and implemented. The remaining work
is execution of already-authorized gates.

## 36. Final status

**P16_REMEDIATION_04_PARTIAL**

The PO-ratified state machine is implemented and live-verified (`mapped → validated → calculated`,
reviewer ≠ processor, `mapped → calculated` prohibited), the six canonical PDFs now complete the journey
end-to-end with full supplier attribution, RD-2/RD-6 are closed and RD-5 is resolved for the single applicable
site. RD-4, RD-8, R8, R11 and R14 remain open, so PASS cannot be claimed. No corpus/oracle change, no schema or
RLS change, no production activity, no manufactured PASS. P17 / Prompt 2, Scope 2, full Scope 3, frameworks,
assurance and Step-3 UI were **not** started. STOP.
