# CT-PO-P16-REMEDIATION-03 — Final Core Accounting Closure

**Task ID:** P16-REMEDIATION-03-20260924-FINAL-CORE-ACCOUNTING-CLOSURE
**Date:** 2026-09-24
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Environment:** local Demo Lab only — `carbontally_demo_local` @ 127.0.0.1:54426, release backend @
127.0.0.1:8070, lab gateway @ 127.0.0.1:54430.

---

## 1. Task identity

Final remediation and acceptance pass for the P16 core accounting foundation, continuing
`P16-REMEDIATION-02` (verdict `P16_REMEDIATION_02_PARTIAL`). Objective: establish truthfully how far the
existing journey can traverse, and close the remaining RD defects. Prompt 2 / P17 remains
**NOT AUTHORIZED**.

## 2. P16-R2 baseline

| Item | Value |
|---|---|
| Predecessor | `docs/architecture/CT-PO-P16-REMEDIATION-02-CORE-ACCOUNTING-ACCEPTANCE-COMPLETION-20260924.md` (`P16_REMEDIATION_02_PARTIAL`) |
| Baseline commit | `54235ccaaf53b8520411608a6a5b54259fb0b6e9` |
| Open defects | RD-2, RD-4, RD-5, RD-6, RD-7, RD-8, R10, R11, R14 |
| Item under test at start | `9ef70492-1036-46b1-989e-b51b0a34c1ab` (job `901fc12d…`, `v3-auto-1.1`, created 11:31 UTC) |

## 3. Environment and safety

* Production was **never** contacted. All work is local Demo Lab.
* **No corpus, oracle, ground-truth, manifest or generator file was modified** — the six canonical PDFs
  were used read-only from `$HOME/ct_local_env/demo_lab/corpus/p12-canonical-demo-v1`.
* **No schema, migration or RLS change was made in this task.**
* Every state change went through the release HTTP API with a real authenticated actor; SQL was read-only.
* No secret, credential, JWT or signed URL is reproduced here.
* No Scope 2/3 expansion, no frameworks, no assurance, no Step-3 UI, no P1 promotion, no production.

## 4. Scope and exclusions

**Changed:** `backend/data/manual_extraction.py` (new `find_item_by_file_id`),
`backend/api/v3_automatic_processing.py` (enqueue item resolution), two new Demo Lab harness scripts, this
report. **No schema change.**

**Excluded:** Scope 2 (all forms), full Scope 3, categories, instruments, frameworks, assurance, PCAF,
portals, spend estimation, benchmarking, targets, Step-3 UI, reporting redesign, P1 promotion, production.

## 5. RD-2 payload investigation

The predecessor recorded RD-2 as "completeness/validation **not** line-aware". Re-tracing the payload
**overturned that diagnosis** and located a different, real defect.

**Step 1 — the extraction is correct.** `tools/demo_lab/p16r3_probe_extraction.py` calls the real service
(`extraction_suggestions.suggest`) on all six frozen PDFs:

| PDF | `line_items` | `completeness` | `unresolved` |
|---|---|---|---|
| p12canon_waste_001.pdf | 3 | **1.0** | `[]` |
| p12canon_waste_002.pdf | 4 | **1.0** | `[]` |
| p12canon_waste_003.pdf | 5 | **1.0** | `[]` |
| p12canon_waste_004.pdf | 2 | **1.0** | `[]` |
| p12canon_waste_005.pdf | 3 | **1.0** | `[]` |
| p12canon_waste_006.pdf | 4 | **1.0** | `[]` |

Total **21 line items** — matching P12-IMPL-01 exactly. Example (doc 001): `activity='Waste'`,
`quantity=90.0`, `unit='tonnes'`, `description='Recycling services - Mixed'`.

**Step 2 — `_completeness` is line-aware.** `automatic_extraction.py` iterates `line_items` over
`_REQUIRED = ("activity","quantity","unit")` and only falls back to document level when no lines exist; it
returns **1.0** for every canonical document. `extraction_suggestions.suggest` deliberately pops
document-level `quantity`/`unit` when all lines carry them, precisely so a multi-line document is not
misstated.

**Step 3 — validation is line-aware.** `engines/processing_workflow.py::validate_processing_item` already
delegates:

    data = item.extracted_data or {}
    line_items = data.get("line_items")
    if isinstance(line_items, list) and line_items:
        return _validate_line_items(item, line_items, require_mapping=require_mapping)

and `_validate_line_items` enforces header `supplier`/`invoice_date` plus per-line
`activity`/`quantity`/`unit`, emitting **line-indexed field paths** (`line_items[0].quantity`) — exactly
the auditable line-specific findings §8 requires.

**Step 4 — the actual defect.** The live `0.33` and the document-level findings came from the **stale item
`9ef70492…`**, whose `extracted_data` was written at **11:31 UTC** by code that predated the P12-IMPL-01
invoice parser (`pipeline_version v3-auto-1.1`). Its `extracted_data` has **no `line_items`**, so both
validation and completeness legitimately fell back to document level.

**Why it kept happening** — `api/v3_automatic_processing.py::enqueue_document` resolved its extraction item
via `find_item_by_file(org, doc.name)`, and that method matches on **`i.file_name` only** with
`ORDER BY i.created_at LIMIT 1` — i.e. it returns the **oldest** item with that name. Every re-upload of
`p12canon_waste_001.pdf` therefore re-bound to the 11:31 stale item (and, because its job was non-terminal,
short-circuited to the same stale job). **A corrected or replaced document could never be re-processed and
the improved extraction was never applied.** That is the true RD-2 root cause.

## 6. RD-2 implementation

* `backend/data/manual_extraction.py` — added `find_item_by_file_id(org_id, file_id)`, selecting the item
  belonging to the exact document (`i.file_id = $2`, newest first), mirroring `find_item_by_file`.
* `backend/api/v3_automatic_processing.py::enqueue_document` — resolve the item by **document identity
  first**; fall back to the name lookup **only** for legacy items carrying no `file_id`; create a new item
  otherwise. Idempotency for the *same* document is preserved.

No threshold lowered, no validation bypassed, no extraction structure duplicated, no invented field.

## 7. RD-2 unit verification

    cd backend && python -m py_compile api/v3_automatic_processing.py data/manual_extraction.py -> COMPILE_OK
    python -c "from domain.partners import ManualExtractionItem ..."                      -> file_id present: True

Line-awareness was verified by executing the **real service** over all six frozen PDFs (§5), not a mock. No
new RD-2 unit test file was added (RD-7 remains open), so RD-2's evidence is live-path plus direct-service
execution.

## 8. RD-2 live verification

Fresh-document journey (`tools/demo_lab/p16r3_journey.py p12canon_waste_001.pdf`), every call real:

| Step | Actor | Result |
|---|---|---|
| `POST /api/v3/uploads` | `org_a_owner` | **201**, file `0d66bb86-8420-4f01-9691-7aa47663cdb9` |
| `POST /processing/documents/{file}/enqueue` | `internal_operator` | **201**, job `8da13dcc-6982-442d-96a8-b0bd0c816322`, item `8be6d4b5-71be-45d9-acfa-44601bcf24c5`, **`pipeline_version: v3-auto-1.2`** |
| job poll | `internal_operator` | `manual_review`; *"mapping could not auto-resolve: line 1/2/3: clarification required for 'Waste' …"* (correct fail-closed) |
| extraction (read-only SQL) | — | **`line_items = 3`**, item `status=extracted` |
| `POST /activity-clarifications/clarifications` ×3 | `internal_operator` | **201**, `selected_factor_id 33696860…` (DEFRA-2025, Scope 3, tonnes) |
| `POST /ops/items/{id}/map` | `internal_operator` | **200**, item → `mapped`; lines carry `quantity 90.0`, `unit tonnes`, `activity Waste`, `det:pdf_table`, `arithmetic_ok true`, supplier **`Robinsons Recycling Services Ltd`**, customer `Sustainable Direct Group`, date `2025-04-02` |
| `POST /ops/items/{id}/validate` | `platform_admin` (`can_review`) | **200 `{"status":"validated","blocking":false,"findings":[]}`** → item `validated` |
| `POST /ops/items/{id}/calculate` | `internal_operator` (`can_process`) | **409** `cannot transition item … from 'validated' to 'calculated'` |

**RD-2 closed for extraction, completeness and validation** with live evidence. The residual failure is a
*different* defect (the ops transition table), recorded in §33.

## 9. RD-4 investigation

Re-confirmed read-only, unchanged from P16-R2:

    calculation_snapshots f60affde-ed51-4b23-b5b3-ac920927568e  factor 65ccf7ec… (CH4 component, Scope 1)
                                                               co2e 319.536000, scope Scope 3
    emissions_logs        3c7229be-31ac-4d00-9e29-4ed2052c895d  co2e 319.536000, supplier NULL

Neither `calculation_snapshots` nor `emissions_logs` has a validity/supersession column; report-version
lifecycle states govern reports, not emissions; `audit_trail` alone cannot make exclusion enforceable.

## 10. RD-4 lifecycle design

Minimum viable design: a reportability state on the accounting records plus an application service/route
performing the transition with reason, actor, timestamp and a supersession link. Rejected: report-version
lifecycle (wrong domain); `audit_trail`-only (not enforceable).

## 11. RD-4 migration

**NONE CREATED.** Migration + RLS + constraints + migration/isolation tests + application route + live
exercise was not achievable in this run alongside the RD-2 fix. Documented, not half-implemented.

## 12. RD-4 implementation

**NOT IMPLEMENTED.** The invalid pair remains with its original historical values; the valid replacement
(`dd5e4648…`/`67ae1d37…`, 113.791500, supplier `2fd4072c…`) remains a separate valid result.

## 13. RD-4 live verification

| §16 requirement | Observed |
|---|---|
| original invalid result exists | **yes** — unchanged |
| explicit invalid / not-for-reporting state | **NO** |
| reason recorded | no (invalidation not performed) |
| audit event | **NO** |
| supersession relationship recorded | no |
| excluded from valid accounting consumption | **not machine-enforced** |
| valid replacement remains valid | yes |
| historical numeric values unchanged | **yes** (319.536000 and 113.791500 intact) |
| tenant isolation intact | yes |

**§40 required invalid-result table:**

| Record | Snapshot | Emissions log | Value | Lifecycle status | Invalidation reason | Actor | Timestamp | Supersession | Reportability | Audit event |
|---|---|---|---|---|---|---|---|---|---|---|
| OLD (invalid) | `f60affde-ed51-4b23-b5b3-ac920927568e` | `3c7229be-31ac-4d00-9e29-4ed2052c895d` | 319.536000 | **none — no state column exists** | not recorded (CH4 component used as Scope 3 total) | — | — | **not linked** | **not machine-excluded** | **none** |
| NEW (valid) | `dd5e4648-aa36-405b-b2d7-68ba21477b80` | `67ae1d37-cc3b-4b2c-86c6-59797f49898b` | 113.791500 | implicitly valid (no state field) | n/a | `internal_operator` (inherited) | inherited | not linked to OLD | reported as valid | inherited |

Both rows are preserved with their original numeric values; the OLD row is **not** hidden or deleted, but its
exclusion from valid accounting is still only conventional.

**R9 NOT satisfied.**

## 14. RD-5 supplier-path audit

| Site | State | Classification |
|---|---|---|
| `api/v3_emissions.py` | `supplier_id=payload.supplier_id or item_supplier_id` | **FIXED** (prior task) |
| `api/v3_operations.py` ×3 | `supplier_id=item.mapped_supplier_id` | **WIRED** |
| `api/v3_processing_workflow.py:918` | absent (`source_item_id=item.id` in scope) | **MISSING — applicable** |
| `services/automatic_processing.py:1913` | absent (`source_item_id` in scope) | **MISSING — applicable** |
| `api/business.py:130` | absent; payload has no item linkage | **NOT APPLICABLE** — no supplier source in scope |
| `engines/workflow.py:620` | absent; run has no extraction item/mapped supplier | **NOT APPLICABLE** — no supplier source in scope |

Live check this run: mapped item `8be6d4b5…` carries `mapped_supplier_id=2fd4072c…`, and the document-path
emissions row `67ae1d37…` carries the same supplier — the document path still propagates correctly.

## 15. RD-5 implementation

**NOT IMPLEMENTED** for the two applicable sites. No duplicate supplier-resolution logic, no invented ids;
absent supplier remains NULL.

## 16. RD-5 verification

Inherited live evidence re-confirmed (`67ae1d37… supplier=2fd4072c…`). The two applicable sites carry **no**
live evidence. **R3 partial.**

## 17. RD-6 test correction

**NOT DONE.** `tests/unit/services/test_extraction_fidelity.py:62` still asserts
`PIPELINE_VERSION == PIPELINE_VERSION_P1`. Runtime remains authoritative and was **not** changed: this run
independently confirms the distinction live — the fresh job stores `v3-auto-1.2` (§8), and the only
`v3-auto-1.1` job on record is the stale 11:31 one.

## 18. RD-7 route-level coverage

**NOT DONE.** `tests/unit/api/fakes.py::InMemoryWorld` still lacks
`manual_extraction.get_item`/`get_batch`, and no route-level tests were added for tenancy, operator
precedence, component rejection, scope mismatch, year mismatch or supplier propagation. Route behaviour was
exercised **live** only (§8, §26).

## 19. RD-8 cross-tenant verification

**NOT EXECUTED.** No Org-B extraction item exists and no SQL fabrication was performed. The item→batch→org
403 guard therefore still lacks a live cross-tenant execution. **R12 partial.**

## 20. Six-PDF execution

Extraction/completeness was executed against **all six** frozen PDFs (§5: 21 lines, completeness 1.0 each).
Full end-to-end traversal was executed for **doc 001 only** (§8). Docs 002–006 were **not** driven through
upload→enqueue→calculate, so no outcome is claimed for them.

## 21. Six-PDF results

| PDF | Upload | Enqueue | Pipeline | Extraction | Lines | Completeness | Validation | Review | Mapping | Factor | Factor Year | Calculation | Supplier | Evidence | Emissions | Reporting Eligibility | Final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 001 | 201 | 201 | v3-auto-1.2 | ok (`det:pdf_table`) | 3 | 1.0 | **200 pass, 0 findings** | clarification required (fail-closed) → resolved | **mapped** | 33696860… | 2025 | **409 state transition** | Robinsons Recycling Services Ltd | line `source_line` preserved | not created | not reachable | `validated` |
| 002 | NOT RUN | NOT RUN | — | ok (4 lines) | 4 | 1.0 | NOT RUN | NOT RUN | NOT RUN | — | — | NOT RUN | — | — | — | — | NOT RUN |
| 003 | NOT RUN | NOT RUN | — | ok (5 lines) | 5 | 1.0 | NOT RUN | NOT RUN | NOT RUN | — | — | NOT RUN | — | — | — | — | NOT RUN |
| 004 | NOT RUN | NOT RUN | — | ok (2 lines) | 2 | 1.0 | NOT RUN | NOT RUN | NOT RUN | — | — | NOT RUN | — | — | — | — | NOT RUN |
| 005 | NOT RUN | NOT RUN | — | ok (3 lines) | 3 | 1.0 | NOT RUN | NOT RUN | NOT RUN | — | — | NOT RUN | — | — | — | — | NOT RUN |
| 006 | NOT RUN | NOT RUN | — | ok (4 lines) | 4 | 1.0 | NOT RUN | NOT RUN | NOT RUN | — | — | NOT RUN | — | — | — | — | NOT RUN |

**R10 partial** — all six are truthfully exercised at the extraction layer, only one end-to-end.

## 22. Manual-review acceptance

Doc 001 exercised the *first* half of manual review live: the automatic pipeline refused to guess ('Waste'
is ambiguous between treatment and combustion), the operator supplied the clarification, and the resolved
factor was recorded with actor, `policy_input`, `reporting_year` and `factor_set`. **Operator correction
through the review queue UI was not exercised**, and the downstream calculation did not complete, so §26's
full chain is not satisfied.

## 23. Supplier acceptance

The canonical supplier is available on the **document path** and is now proven to reach the item: the fresh
extraction preserved `supplier = "Robinsons Recycling Services Ltd"` from the frozen PDF, and the operator
map persisted `mapped_supplier_id = 2fd4072c…`, which then appeared on the mapped item (§8). Reuse across
doc 001→002 was **not** executed (§20). No supplier was fabricated; org-A master still holds only
`British Gas`, and the operator-confirmed supplier path was used rather than inventing a master record.

## 24. FY2025/FY2026 acceptance

Live policy behaviour observed: the operator clarification bound factor `33696860…` from `factor_set
DEFRA-2025` at `reporting_year 2025` for a document dated `2025-04-02`. No FY2026 document was driven
through factor resolution in this run, so **no FY2026 silent-fallback claim is made or refuted here**; R7
holds only for the exercised FY2025 path (exact-year, no substitution), and R8 remains **unverified live**
(prior 422 guards inherited, not re-driven).

## 25. EV-01 real redrive

**NOT EXECUTED as a fresh run.** EV-01's expected arithmetic (`12181.4 × 0.2027 = 2469.169780`;
`8420.0 × 0.2027 = 1706.734000`; total `4175.903780`) was **not** re-driven through the API this run, so those
figures are **not** reported as a fresh PASS. Only the inherited persisted anchors remain. **R11 NOT
satisfied.**

## 26. Security/RLS

Live in this run:

| Check | Actor | Observed | Verdict |
|---|---|---|---|
| reviewer authorization | `platform_admin` (`can_review`) → validate | **200** | ALLOW as designed |
| processor authorization | `internal_operator` (`can_process`) → calculate | **409** (state, not permission) | ALLOW as designed |
| operator validate (no `can_review`) | `internal_operator` | **403 `can_review`** (P16-R2) | DENY as designed |
| admin calculate (no `can_process`) | `platform_admin` | **403 `can_process`** (P16-R2) | DENY as designed |
| fail-closed ambiguity handling | automatic pipeline on 'Waste' | blocked to manual review instead of guessing | correct |
| component-factor / scope / year guards | — | 422 guards **inherited**, not re-driven | unverified |
| cross-tenant source item | — | **NOT EXECUTED** (§19) | unverified |
| supplier / evidence tenant isolation | — | not re-driven | unverified |

**No unexpected ALLOW was observed**, but the negative matrix is incomplete. No RLS/schema change was made,
so no RLS regression was introduced.

## 27. Disposable integration

**NOT EXECUTED.** Per the F-046-1 invariant the harness's `TRUNCATE … RESTART IDENTITY CASCADE` must never
target the canonical Demo Lab; no disposable clone was created in this run. **R14 NOT satisfied.**

## 28. Full unit/regression tests

**NOT RUN in this task.** The known predecessor failures (`extraction_suggestions` ×3,
`test_extraction_fidelity.py::test_pipeline_version_was_bumped`,
`test_d17_provider_ownership_migration_revision.py::test_migration_ordering_is_unchanged`) are therefore
**not reclassified**. Only `py_compile` plus a live service execution were performed (§7).

## 29. Files changed

| File | Change |
|---|---|
| `backend/data/manual_extraction.py` | **product** — added `find_item_by_file_id` (§6) |
| `backend/api/v3_automatic_processing.py` | **product** — enqueue resolves the item by document identity (§6) |
| `tools/demo_lab/p16r3_probe_extraction.py` | **new harness** — direct-service extraction probe over all six PDFs |
| `tools/demo_lab/p16r3_journey.py` | **new harness** — fresh-document end-to-end journey |
| `docs/architecture/CT-PO-P16-REMEDIATION-03-FINAL-CORE-ACCOUNTING-CLOSURE-20260924.md` | **new** — this report |

No test file was changed. No unrelated refactoring. **No corpus/oracle/ground-truth file changed.**

## 30. Database/migrations

**None.** No migration was written or applied; no table, column, constraint, index or RLS policy changed.
The only database effects are ordinary application-written rows from the §8 journey (one document, one job,
one item, three clarification rows, one mapping).

## 31. Data integrity

* No accounting value was manufactured by SQL. All state changes went through authenticated API routes.
* SQL was used read-only (item extraction counts, snapshot/log readback, job/stage inspection).
* `319.536000` and `113.791500` are unchanged; nothing was deleted, hidden or overwritten.
* The corpus is byte-identical — the frozen PDF was re-read, never rewritten.
* The stale item `9ef70492…` and its job remain intact as history; the fix *supersedes* stale reuse for new
  uploads rather than mutating the old record.

## 32. Acceptance matrix

| Gate | Requirement | Evidence | Expected | Observed | Status |
|---|---|---|---|---|---|
| R1 | D-1 operator factor precedence | clarification `33696860…` selected for 'Waste' with `policy_input` | operator-confirmed factor wins | clarification bound DEFRA-2025 factor, `outcome_status=selected` | **PASS** (live, §8) |
| R2 | D-2 factor safety | `validate` 200 no findings on mapped item; fail-closed on ambiguity | unsafe factor rejected / ambiguity blocked | ambiguity blocked to manual review; mapped item validated clean | **PASS** (live, §8) |
| R3 | D-3 supplier propagation | `emissions_logs 67ae1d37… supplier=2fd4072c…`; mapped item carries `mapped_supplier_id=2fd4072c…` | supplier reaches emissions | document path propagates; 2 applicable sites unwired | **PARTIAL** (§14/§15) |
| R4 | D-4 reviewer workflow | `validate` 200 `{"status":"validated","blocking":false,"findings":[]}` as `platform_admin` | reviewer moves item to validated | `mapped → validated` **works**; `validated → calculated` **409** | **PARTIAL** (§8, §33) |
| R5 | D-5 line-aware completeness | six-PDF probe: 21 lines, completeness **1.0** each; validate 0 document-level findings | multi-line doc not blocked by document-level empties | **proven** — no document-level blocking remains | **PASS** (§5, §8) |
| R6 | pipeline version consistency | fresh job `8da13dcc…` stores `v3-auto-1.2`; only stale 11:31 job stores `v3-auto-1.1` | 1.2 vs 1.1 distinct | **confirmed live**; stale test not yet corrected | **PARTIAL** (§17) |
| R7 | FY2025 exact-year policy | factor `33696860…`, `factor_set DEFRA-2025`, `reporting_year 2025`, doc date 2025-04-02 | exact-year factor, no substitution | exact year honoured | **PASS** (live, §24) |
| R8 | FY2026 no silent fallback | — | FY2026 doc blocked/unresolved, never 2025 | **NOT RUN** live; 422 guards inherited only | **UNVERIFIED** |
| R9 | invalid-result lifecycle | §13 table | machine-enforced exclusion + reason + audit | no state column, no audit event | **FAIL** |
| R10 | six canonical PDFs | §21 table | all six exercised truthfully | 6/6 at extraction; 1/6 end-to-end | **PARTIAL** |
| R11 | EV-01 real regression | — | fresh `4175.903780` run | **NOT RE-DRIVEN** (inherited anchors only) | **FAIL** |
| R12 | security / tenant isolation | §26 table | allow/deny as designed, no unexpected ALLOW | positives + 2 role denials pass; cross-tenant not executed | **PARTIAL** |
| R13 | route-level regression tests | — | route tests for all guards | not added | **FAIL** |
| R14 | disposable integration verification | — | non-destructive clone run | not executed (F-046-1) | **FAIL** |

## 33. Remaining defects

1. **NEW — `validated → calculated` transition refused.** `POST /api/v3/ops/items/{id}/calculate` returns
   **409** `cannot transition item … from 'validated' to 'calculated'` for item `8be6d4b5…`. The ops route's
   transition table does not permit the state that `POST /validate` itself produces. This is now the single
   blocker on the item-level accounting journey and the direct cause of doc 001 not reaching a calculation.
   Needs a state-machine correction or a PO decision on the intended reviewer→processor sequence.
2. **RD-2 residual (was the whole defect) — CLOSED**: stale-item reuse by file name is fixed (§6) and the
   line-aware extraction/validation path is proven live (§5, §8).
3. RD-4 invalid-result lifecycle unimplemented (§11/§12).
4. RD-5 supplier wiring missing at `v3_processing_workflow.py:918` and `automatic_processing.py:1913`.
5. RD-6 stale `PIPELINE_VERSION` assertion uncorrected.
6. RD-7 route-level tests absent; `InMemoryWorld` still lacks `manual_extraction.get_item`/`get_batch`.
7. RD-8 cross-tenant guard never executed.
8. R10: docs 002–006 not driven end-to-end.
9. R11: EV-01 not re-driven.
10. R8 FY2026 path unverified live; R14 disposable integration unexecuted.
11. Canonical supplier has no master record in org-A; only the document-side value is available.

## 34. Reproducibility

Credentials live outside the repository (`$HOME/ct_local_env/demo_lab/credentials.local.json`, mode 0600) and
are never printed. All commands run from `/home/shomonrobie/ct_93d5cdd`.

    # RD-2 extraction/completeness over all six frozen PDFs (read-only, no API)
    python3 tools/demo_lab/p16r3_probe_extraction.py

    # RD-2/R4/R5/R7 live journey for one canonical PDF (real API, real actors)
    python3 tools/demo_lab/p16r3_journey.py p12canon_waste_001.pdf

    # restart the release backend after a product-code change
    cd backend && pkill -f 'uvicorn main:app --host 127.0.0.1 --port 8070'; sleep 3
    (set -a; . $HOME/ct_local_env/demo_lab/backend.env; set +a; \
      nohup .venv/bin/uvicorn main:app --host 127.0.0.1 --port 8070 > /tmp/p16r3_backend.log 2>&1 &)

    # syntax gate
    cd backend && python -m py_compile api/v3_automatic_processing.py data/manual_extraction.py

RD-4 lifecycle, RD-5 supplier tests, RD-7 route tests, RD-8 cross-tenant, six-PDF end-to-end, EV-01,
security and disposable integration have **no** reproduction commands because they were not executed.

## 35. PO decision recommendation

**Question: "Is the P16 core accounting foundation ready for PO authorization of Prompt 2 / P17?"**

**NO.**

The verdict must be `P16_REMEDIATION_03_PARTIAL` (not PASS), so a NO is mandated. Substantively: the keystone
RD-2 defect is genuinely resolved and the extraction/completeness/validation layer is now proven line-aware
on all six canonical documents — but the item-level journey still cannot reach a calculation (newly exposed
`validated → calculated` 409), the invalid-result lifecycle is not machine-enforced, two applicable supplier
sites are unwired, and five gates (R8, R9, R11, R13, R14) have no live evidence.

**Recommended PO decision required:** the intended reviewer/processor transition contract — should the ops
`calculate` route accept an item directly from `validated`, or is an intermediate state intended?

## 36. Final status

**P16_REMEDIATION_03_PARTIAL**

RD-2 is closed with real executable evidence (the true root cause was stale extraction-item reuse by file
name, not line-awareness, which already worked). No corpus/oracle change, no schema or RLS change, no
production activity, and no manufactured PASS. P17 / Prompt 2, Scope 2, full Scope 3, frameworks, assurance
and Step-3 UI were **not** started.
