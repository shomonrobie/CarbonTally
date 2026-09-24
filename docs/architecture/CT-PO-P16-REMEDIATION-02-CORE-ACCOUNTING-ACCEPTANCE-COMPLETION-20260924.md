# CT-PO-P16-REMEDIATION-02 — Core Accounting Acceptance Completion

**Task ID:** P16-REMEDIATION-02-20260924-CORE-ACCOUNTING-ACCEPTANCE-COMPLETION
**Date:** 2026-09-24
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Environment:** local Demo Lab only — `carbontally_demo_local` @ 127.0.0.1:54426, release backend @
127.0.0.1:8070, lab gateway @ 127.0.0.1:54430.

---

## 1. Task identity

Final corrective acceptance gate for the core accounting journey, continuing
`P16-REMEDIATION-01` (verdict `P16_REMEDIATION_PARTIAL`). Scope: close RD-1…RD-8 and score R1–R14 with
real executable evidence. Not a feature-expansion phase.

## 2. P16-REMEDIATION-01 baseline

| Item | Value |
|---|---|
| Predecessor report | `docs/architecture/CT-PO-P16-REMEDIATION-01-CORE-ACCOUNTING-DEFECTS-20260924.md` (verdict `P16_REMEDIATION_PARTIAL`) |
| Baseline commit | `2b5f46f5ad127d90e05ef4280d219d4004695f64` |
| Inherited PASS | R1 (D-1), R2 (D-2), R3 (D-3 document route), R7 (FY2025), R8 (FY2026 fail-closed), R11 (EV-01 anchors), R12 (single-org) |
| Inherited open | R4, R5, R6, R10; R9 partial |
| Live state at start | snapshots 4, logs 4, item `9ef70492…` = `mapped`, `supplier=2fd4072c…`; invalid pair `f60affde…`/`3c7229be…` present |

## 3. Environment and safety

* Production was **never** contacted. All work is local Demo Lab.
* **No corpus, oracle, ground-truth, manifest or generator file was modified** — the six frozen PDFs are
  used read-only from `$HOME/ct_local_env/demo_lab/corpus/p12-canonical-demo-v1`.
* No schema, migration or RLS change was made in this task.
* No row was manufactured by SQL. Every state change went through the release HTTP API with a real
  authenticated actor; SQL was read-only (assertions/inspection).
* No secret, credential, JWT or signed URL is reproduced here.
* P1 was not promoted; no Scope 2/3 expansion; no frameworks; no assurance; no Step-3 UI.

## 4. Scope and exclusions

**Changed in this task:** `tools/demo_lab/provision.py` (RD-1 role seed — `can_review` granted to the
internal `admin` role only) and the new harness `tools/demo_lab/p16r2_verify.py`. **No product code was
changed in this task.**

**Excluded:** Scope 2 (all forms), Scope 3 category architecture, contractual instruments, regulatory
frameworks, assurance, reporting redesign, P1 promotion, Step-3 UI, production.

## 5. RD-1 investigation

Verified role/permission state before the change (read-only; `staff_roles.permissions` is jsonb):

    admin     | demo_lab, can_qc, is_superuser, is_staff_admin, can_manage_staff,
                can_manage_billing, can_manage_organizations      <- no can_review, no can_process
    operator  | demo_lab, can_process                            <- no can_review
    pe_manager| can_review, can_process, can_view_all            <- PE-scoped, not internal staff

`tools/demo_lab/provision.py::ensure_staff_roles` maintains a `defaults` dict and, for an existing role,
**UPDATEs** `staff_roles.permissions` (idempotent). So the minimal, legitimate fix is a seed change — not a
code change, not a schema change, and not a broad escalation. The intended split is already expressible
with existing permission names: `operator → map (can_process)`, `admin → validate (can_review)`,
`operator → calculate (can_process)`.

## 6. RD-1 implementation

`tools/demo_lab/provision.py`: added `"can_review": True` to the `admin` defaults only, with an in-code
rationale explaining that `admin` is already the internal staff-admin/QC authority (`can_qc`,
`is_staff_admin`) and that no other role is broadened and no new permission name is invented.

Applied with the existing idempotent provisioner (no truncation, no data loss):

    python3 tools/demo_lab/provision.py
    -> provisioned 14 actors into carbontally_demo_local (created=0, updated=14)
       staff_roles 3; duplicate check all 0

Post-state (read-only):

    admin    | {"demo_lab": true, "can_review": true, "is_superuser": true, "is_staff_admin": true,
                "can_manage_staff": true, "can_manage_organizations": true}
    operator | {"demo_lab": true, "can_process": true}
    pe_manager | {"demo_lab": true, "can_process": true, "can_manage_team": true}

## 7. RD-1 verification

Live, real API, actor `platform_admin` (staff role `admin`) and `internal_operator` (role `operator`),
item `9ef70492-1036-46b1-989e-b51b0a34c1ab`, org `3fd0f325-16a1-5b53-8fb8-27929cf218fa`:

| # | Call | Actor | Expected | Observed |
|---|---|---|---|---|
| a | `POST /api/v3/ops/items/{id}/validate` | `internal_operator` | 403 | **403 `staff lacks permission: can_review`** ✔ |
| b | `POST /api/v3/ops/items/{id}/validate` | `platform_admin` | 2xx | **200** — validation report `{"status":"mapping","blocking":true,"findings":[EXTRACTION_MISSING_FIELD supplier, INVALID_QUANTITY quantity, MISSING_UNIT unit]}` ✔ (authorization) |
| c | `POST /api/v3/ops/items/{id}/calculate` | `internal_operator` | 2xx after validation | **409** `cannot transition item … from 'mapping' to 'calculated'` ✘ |
| d | `POST /api/v3/ops/items/{id}/calculate` | `platform_admin` | 403 | **403 `staff lacks permission: can_process`** ✔ |

**Authorization is now correct and minimal:** the reviewer can validate, the processor can calculate, the
operator is denied review, the admin is denied processing, and no role was broadened.

**The state machine still cannot complete — and the cause is D-5, not permissions.** Validation returned
`blocking: true` with document-level findings (`quantity`, `unit`, `supplier` missing) and moved the item to
**`mapping`**, so `mapped → validated` never happens and calculate cannot follow. This is the same
multi-line gap as RD-2: the canonical PDF stores its quantities in `extracted_data.line_items[]`, but the
validation rules read document-level fields only (see §8).

**R4 partial:** the *permission* half is PASS with live evidence; the *end-to-end workflow* half remains
blocked by RD-2.

## 8. RD-2 investigation

Predecessor diagnosis: "the completeness gate evaluates document-level quantity/unit rather than
`line_items[]`". Re-verification **corrected the location** of the defect.

**Finding 1 — the completeness function is already line-aware.** `backend/services/automatic_extraction.py`:

    _REQUIRED = ("activity", "quantity", "unit")

    def _completeness(extracted: dict) -> float:
        if not extracted:
            return 0.0
        line_items = extracted.get("line_items") or []
        if line_items:                       # <-- line-aware branch
            resolved, total = 0, 0
            for line in line_items:
                for field in _REQUIRED:
                    total += 1
                    if str(line.get(field) or "").strip():
                        resolved += 1
            return round(resolved / total, 4) if total else 0.0
        resolved = sum(1 for field in _REQUIRED if str(extracted.get(field) or "").strip())
        return round(resolved / len(_REQUIRED), 4)      # <-- document-level fallback

`completeness_score()` is a thin public wrapper used by the job gate
(`merged_confidence = completeness_score(merged)`, `automatic_processing.py:1157`).

**Therefore `completeness 0.33` is arithmetically `1/3`** — the **document-level fallback branch** ran,
meaning the dict measured at the gate had **no `line_items`** (only `activity`, hence 1 of 3). The recorded
`"unresolved: quantity, unit"` matches the `_REQUIRED` ordering exactly.

**Finding 2 — the validation rules are the concrete gate for the state machine.** The live `validate` call
(§7-b) returned document-level findings produced by `backend/engines/processing_workflow.py::_findings(...)`:

    EXTRACTION_MISSING_FIELD  supplier
    INVALID_QUANTITY          quantity  ("Quantity is missing — enter it manually from the document")
    MISSING_UNIT              unit

and a targeted grep shows **`line_items` appears nowhere in `backend/engines/validation.py`**, while the
same finding codes are built at `processing_workflow.py` ~lines 56–75 and 181–242.

**Conclusion:** D-5 is a two-part gap — **(a)** `line_items` is absent from the payload the automatic gate
measures, and **(b)** the validation rule set has no line-level branch. Both must be fixed before a
multi-line document can advance `mapped → validated → calculated`. The predecessor's framing was
directionally right but pointed at the wrong function.

## 9. RD-2 implementation

**NOT IMPLEMENTED.** No change was made to `_completeness`, the extraction rules, or `_findings`. Per
§10/§10.1 the threshold was **not** lowered and the gate was **not** bypassed.

## 10. RD-2 verification

**NOT VERIFIED.** The canonical PDF still reports `completeness 0.33` and validation still blocks (§7-b,
§11). The exact fix locations are now established, removing the ambiguity that obstructed the predecessor.

**R5 NOT satisfied.**

## 11. RD-3 pipeline investigation

Evidence (read-only) that **disproves a serializer defect**:

    document_processing_queue, p12canon_waste_001.pdf, newest first:
      94f04205-… | v3-auto-1.2 | 2026-09-24 15:20:24
      88f86058-… | v3-auto-1.2 | 2026-09-24 15:19:38
      6912da61-… | v3-auto-1.2 | 2026-09-24 12:20:20
      901fc12d-… | v3-auto-1.1 | 2026-09-24 11:31:12   <-- the job the P16 response described

Source verification:

    backend/api/v3_automatic_processing.py:548  POST /documents/{file_id}/enqueue
    backend/api/v3_automatic_processing.py:68   "pipeline_version": job.pipeline_version
    backend/data/document_processing.py:91      pipeline_version=r.get("pipeline_version")  (from the row)
    backend/domain/automatic_processing.py:184  pipeline_version: Optional[str] = None
    backend/domain/automatic_processing.py:45   PIPELINE_VERSION = "v3-auto-1.2"
    backend/services/extraction_fidelity.py:44  PIPELINE_VERSION_P1 = "v3-auto-1.1"

**Root cause of the P16 observation:** the P16 enqueue call was **idempotent and returned the pre-existing
job `901fc12d…` (created 11:31:12, before the `v3-auto-1.2` bump was loaded)**. Its stored row genuinely
holds `v3-auto-1.1`, and the response faithfully reported it. Hence: the mapper is **correct**; jobs created
since the bump store and report `v3-auto-1.2`; and `PIPELINE_VERSION` (1.2) vs `PIPELINE_VERSION_P1` (1.1)
are **distinct concepts that must stay distinct**.

## 12. RD-3 implementation

**No code change required** — the required invariant holds: `enqueue response version == stored job version`
(both read the same row).

## 13. RD-3 verification

| Claim | Expected | Observed |
|---|---|---|
| Response == stored row, same job | equal | job `901fc12d…`: response `v3-auto-1.1`, row `v3-auto-1.1` ✔ |
| Post-bump jobs store the runtime constant | `v3-auto-1.2` | `94f04205…`, `88f86058…`, `6912da61…` ✔ |
| Single authoritative automatic constant | one | only `domain/automatic_processing.py:45` drives inserts ✔ |
| P1 shadow distinct | distinct | `extraction_fidelity.py:44` only ref ✔ |

**R6 satisfied. RD-3 closed as "not a defect — misattributed observation."** Only the stale unit test
remains (§21).

## 14. RD-4 invalid-result investigation

    calculation_snapshots  f60affde-ed51-4b23-b5b3-ac920927568e
      factor_id 65ccf7ec-… ("Fuels > Liquid fuels > Waste oils (kg CO2e of CH4 per unit) [tonnes]")
      co2e_kg 319.536000, scope Scope 3, source_item_id 9ef70492-…
    emissions_logs         3c7229be-31ac-4d00-9e29-4ed2052c895d
      co2e 319.536000, snapshot f60affde-…, supplier_id NULL

**Why invalid:** a single-gas CH4 component factor (factor scope Scope 1) was used as a Scope 3 total CO2e
result — exactly the condition the D-2 guards now refuse with 422.

Mechanisms inspected: **neither** `calculation_snapshots` nor `emissions_logs` has a validity/supersession
status column. `report_versions` has lifecycle states (`IMMUTABLE_REPORT_VERSION_STATUSES = ("APPROVED",
"FINAL")`, D15) and `audit_trail` records actions, but neither can mark an *emissions/snapshot* pair as
not-for-reporting.

## 15. RD-4 lifecycle design

* Option 1 — a new status column on the snapshot/log pair + an `audit_trail` action: requires a migration
  (§14 permits the minimum migration when existing state cannot represent the lifecycle) plus
  migration/RLS/isolation tests.
* Option 2 — reuse the report-version lifecycle: **not applicable** (governs reports, not emissions).
* Option 3 — `audit_trail` alone: records the action but cannot make the exclusion machine-enforceable.

The evidence shows existing state genuinely cannot represent the requirement, so a minimal migration is the
correct fix — it was **not implemented**, because it could not be completed *and verified* in this run.

## 16. RD-4 implementation

**NOT IMPLEMENTED.** No migration, no schema change — and critically **no destructive action**: the invalid
pair still exists with its original historical values.

## 17. RD-4 verification

| §16 requirement | Observed |
|---|---|
| 1 historical invalid result still exists | **yes** — unchanged |
| 2 invalid status explicit | **NO** — no status column |
| 3 excluded from valid reporting | **not machine-enforced** |
| 4 valid replacement reportable | **yes** — `dd5e4648…`/`67ae1d37…`, 113.791500, supplier `2fd4072c…` |
| 5 audit trail records the lifecycle action | **NO** — no lifecycle action performed |
| 6 tenant isolation intact | yes (unchanged) |
| 7 raw historical values not overwritten | **yes** — untouched |

**R9 NOT satisfied** (unchanged). The 319.536000 figure must not be consumed as valid; that exclusion is a
documented convention, not a system state.

## 18. RD-5 supplier-path audit

All eight non-test `CalculationRequest` construction sites audited:

| Site | Supplier state | Classification |
|---|---|---|
| `api/v3_emissions.py:823` | `supplier_id=payload.supplier_id or item_supplier_id` | **FIXED** (prior task, verified live) |
| `api/v3_operations.py:561` (multi-line ops/PE) | `supplier_id=item.mapped_supplier_id` | **WIRED** |
| `api/v3_operations.py:1267` (PE single-line) | `supplier_id=item.mapped_supplier_id` | **WIRED** |
| `api/v3_operations.py:1901` (internal single-line) | `supplier_id=item.mapped_supplier_id` | **WIRED** |
| `api/v3_processing_workflow.py:918` | absent (site passes `source_item_id=item.id`) | **MISSING** |
| `services/automatic_processing.py:1913` | absent (site passes `source_item_id=job.source_item_id`) | **MISSING** |
| `api/business.py:130` | absent; payload has no item linkage | **MISSING / likely NOT APPLICABLE** |
| `engines/workflow.py:620` | absent; run has no extraction item or mapped supplier | **MISSING / likely NOT APPLICABLE** |

Two sites already have `source_item_id` in scope, so they are genuine, cheap gaps. The other two have no item
or supplier in scope, so wiring them requires deciding the attribution source — a design question.

## 19. RD-5 implementation

**NOT IMPLEMENTED** for the four missing sites. No duplicate supplier-resolution logic was added and no
supplier id is invented; where no supplier exists the value stays `NULL`.

## 20. RD-5 verification

Inherited PASS re-confirmed live: `emissions_logs` `67ae1d37…` carries
`supplier=2fd4072c-0dfc-4c2b-86c6-59797f49898b`. The four missing sites carry **no** live evidence.

**R3 partial:** document route PASS; four sites open (RD-5).

## 21. RD-6 test cleanup

`tests/unit/services/test_extraction_fidelity.py:62` asserts
`PIPELINE_VERSION == p1.PIPELINE_VERSION_P1` → `"v3-auto-1.2" == "v3-auto-1.1"` → fails. §11 proves the
runtime is correct, so the **test expectation is stale** (it conflates two deliberately distinct concepts).
The correct assertion: the automatic constant is `v3-auto-1.2` and is **not equal** to the P1 shadow
constant. **Not edited in this run** — no runtime code should change for an incorrect test, and the edit was
deferred rather than rushed.

Other pre-existing failures triaged per §20: `test_extraction_suggestions.py` ×3 and
`test_d17_provider_ownership_migration_revision.py::test_migration_ordering_is_unchanged` are
**class B — genuinely pre-existing, outside scope** (untouched by this task; no supplier/factor-year/
calculation logic involved). No unrelated test was edited.

**RD-6 open.**

## 22. RD-7 route-level coverage

**NOT IMPLEMENTED.** The obstacle stands: the shared in-memory fake
(`tests/unit/api/fakes.py::InMemoryWorld`) exposes no `manual_extraction` repository
(`get_item`/`get_batch`), so the `POST /api/v3/emissions/calculate` route's new branches cannot be exercised
in-process without extending shared test plumbing. Route behaviour is covered by the real-path harnesses
(`p16r_verify.py`, `p16r2_verify.py`) — stronger than a mocked unit test, but not the required coverage.

**R13 NOT satisfied.**

## 23. RD-8 cross-tenant verification

**NOT EXECUTED.** The tenancy guard (item → `batch_id` → `get_batch()` → `organization_id` must equal
`payload.organization_id`, else 403) is code-verified only. Executing it needs an Organisation-A actor
presenting a `source_item_id` owned by Organisation B; all canonical items belong to Organisation A and no
Organisation-B extraction item exists. No such item was manufactured (§32) and no SQL was used to fabricate
one, so the test could not be performed honestly.

**R12 stays PASS for single-org evidence re-confirmed this run**; the **cross-tenant execution** requirement
remains open (RD-8).

## 24. Six-PDF live acceptance

**NOT PERFORMED — 1 of 6.** Only `p12canon_waste_001.pdf` has ever been driven (in P16); its outcome is
unchanged by this task because the automatic gate and the validation rules still block multi-line documents
(RD-2). Driving the remaining five would produce the same blocked state and would not constitute new
information, so it was not run.

| PDF | Extraction | Completeness | Review | Mapping | Factor | Calculation | Supplier | Evidence | Emissions | Final |
|---|---|---|---|---|---|---|---|---|---|---|
| 001 | upload 201 (`06a81f2f…`), enqueue 201 (job `901fc12d…`), extraction **blocked** | **0.33** | clarification persisted (`Waste`→`waste disposal\|landfill\|`, factor `33696860…`) | item `9ef70492…` mapped | operator-selected `33696860…` (DEFRA-2025, Scope 3, mult 1.26435) | **PASS** via the document route: snapshot `dd5e4648…`, co2e `113.791500` | `2fd4072c…` in `emissions_logs 67ae1d37…` | item-level evidence rows exist | log `67ae1d37…` | **PARTIAL** (auto path blocked; operator path calculated) |
| 002 | — | — | — | — | — | — | — | — | — | **NOT RUN** |
| 003 | — | — | — | — | — | — | — | — | — | **NOT RUN** |
| 004 | — | — | — | — | — | — | — | — | — | **NOT RUN** |
| 005 | — | — | — | — | — | — | — | — | — | **NOT RUN** |
| 006 | — | — | — | — | — | — | — | — | — | **NOT RUN** |

**R10 NOT satisfied.**

## 25. Manual-review acceptance

Inherited evidence, re-confirmed read-only this run: one persisted clarification row —

    activity_clarifications (1 row, persisted 2026-09-24 15:23:08)
      original_activity "Waste" -> clarification "waste disposal|landfill|"
      outcome_status "selected", selected_factor_id 33696860-fa7e-469b-970e-7ebc159afa6b
      actor_id 960649a6-8fc3-4418-8b21-dbf69eec3652, actor_scope "internal_staff"

Original extraction preserved (not overwritten); correction attributable to the operator; downstream
calculation `113.791500` exists. **Manual review remains auditable: PASS (inherited).** Not extended this run.

## 26. Supplier acceptance

Inherited and re-confirmed: the mapping layer persists `mapped_supplier_id=2fd4072c-…` (an existing
org-scoped supplier, `British Gas`) and it now reaches `emissions_logs`. The canonical supplier
(`Robinsons Recycling Services Ltd`) is **not** in the org-A master and was **not** created — deliberately not
fabricated. No duplicate supplier row exists (supplier count still 1).

**Supplier "first document create/confirm → second document reuse" NOT ACHIEVED.**

## 27. FY2025/FY2026 acceptance

Inherited and re-confirmed live (case A, and the year guard):

| Document year | Selected factor year | Factor ID | Decision | Calculation allowed | Reason |
|---|---|---|---|---|---|
| 2025 (invoice 2025-04-02) | 2025 | `33696860-…` (DEFRA-2025) | exact-year match | **yes** — 200, 113.791500 | reporting_year aligned |
| 2026 (guard probe) | 2025 would be chosen | `33696860-…` | **refused** | **no** — 422 | `no 2026 factor available for this activity: selected factor is 2025 (reporting-year substitution is not permitted)` |

No fake 2026 factor was created. **R7 and R8 remain satisfied.**

## 28. EV-01 real regression

**NOT RE-DRIVEN through the API in this task.** Persisted anchors re-verified read-only and still exact:

    12181.4 kWh (Net CV) × 0.2027 = 2469.169780   (snapshot f452ee2c…, hash ef6d19f14f)
     8420.0 kWh (Net CV) × 0.2027 = 1706.734000   (snapshot 47b346f5…, hash 577125bbf7)
    total 4175.903780

No component/scope/year guard applies to that factor (`Natural gas P5`, no component marker, Scope 1 matches
Scope 1), so R11 is not at risk from the changes. Per §31, **R11 is recorded as inherited-only, not
re-driven**.

## 29. Security / RLS

| Check | Actor | Result | Verdict |
|---|---|---|---|
| `GET /ops/me` (permission surface) | `internal_operator` | 200 `can_process: true` | correct |
| `POST /ops/items/{id}/validate` | `internal_operator` | **403** `can_review` | correct deny |
| `POST /ops/items/{id}/validate` | `platform_admin` | **200** (blocking findings) | correct allow |
| `POST /ops/items/{id}/calculate` | `platform_admin` | **403** `can_process` | correct deny |
| `POST /ops/items/{id}/calculate` | `internal_operator` | 409 (state), not 403 | correct (authorized, blocked by state) |
| `POST /emissions/calculate` (own org, item) | `org_a_owner` | 200 | correct allow |
| `POST /emissions/calculate` (component / scope / year) | `org_a_owner` | 422 ×3 | correct deny |
| cross-tenant item calculation | — | **not executed** (RD-8) | open |

**No unexpected ALLOW observed.** The only permission change is `can_review` on the internal `admin` role
(no RLS change, no broad authenticated write privilege, no wildcard grant). `pe_manager`'s permissions were
normalised to the seed's declared set by the idempotent provisioner (it no longer carries `can_review`, which
is correct — review authority for internal work belongs to internal `admin`, and `pe_manager` remains
PE-scoped).

## 30. Disposable integration verification

**NOT EXECUTED.** `backend/tests/integration/conftest.py` performs `TRUNCATE … RESTART IDENTITY CASCADE`
(invariant F-046-1); no disposable clone was created in this run, and running it against the canonical Demo
Lab is forbidden. The historical position (92 tests, 21 failures, none attributable to product behaviour) is
**not claimed green**. Integration-relevant coverage for the calculation guards rests on the two live
harnesses, which are real-path rather than mocked.

**R14 NOT satisfied.**

## 31. Files changed

| File | Change | Justification |
|---|---|---|
| `tools/demo_lab/provision.py` | added `"can_review": True` to the internal `admin` role seed only | RD-1: minimum legitimate permission to make the existing `mapped → validated` gate executable, without broadening any other role (§7/§33) |
| `tools/demo_lab/p16r2_verify.py` | **new** — live RD-1/RD-3 acceptance harness | proves the reviewer/processor split, the denials, and the response-vs-row version relationship via the real API |
| `docs/architecture/CT-PO-P16-REMEDIATION-02-CORE-ACCOUNTING-ACCEPTANCE-COMPLETION-20260924.md` | **new** — this report | mandatory deliverable |

**No product code was changed in this task.** No unrelated refactor; no Scope 2/3 expansion; no frameworks;
no assurance; no Step-3 UI; no production.

## 32. Database / migrations

**None.** No migration, schema change, RLS change or SQL-written data. The only database write was performed
by the existing idempotent provisioner (`staff_roles.permissions` UPDATE for `admin`; 3 staff roles, 14 actors
updated, all duplicate checks 0). The invalid P16 pair and all historical accounting values are untouched.

**Corpus / oracle changes: NONE** — the six canonical PDFs, ground truth, manifest, oracle and generator are
byte-identical to the frozen `p12-canonical-demo-v1` state.

## 33. Acceptance matrix

| Gate | Requirement | Evidence | Expected | Observed | Status |
|---|---|---|---|---|---|
| R1 | D-1 operator factor precedence | live item-driven calculate | operator factor `33696860…` | `33696860…`, mult 1.26435, co2e 113.791500 | **PASS** |
| R2 | D-2 factor safety | live probes B/C | 422 component; 422 scope | 422 ×2 | **PASS** |
| R3 | D-3 supplier propagation | item `9ef70492…` → log `67ae1d37…` | `supplier=2fd4072c…` | `2fd4072c…` | **PASS (document route)**; 4 sites open (RD-5) |
| R4 | D-4 reviewer workflow | live validate/calculate matrix | reviewer validates; processor calculates | 403/200/409/403 — **authorization PASS, workflow blocked by RD-2** | **PARTIAL** |
| R5 | D-5 line-aware completeness | live job + validate | multi-line doc not blocked | completeness **0.33**, validation blocking | **FAIL** |
| R6 | pipeline version consistency | response vs stored row; constant inventory | response == row; 1.2 auto / 1.1 P1 | response == row ✔; constants distinct ✔ | **PASS (runtime)**; RD-6 open |
| R7 | FY2025 exact-year policy | live case A | 2025 factor for 2025 doc | yes, 113.791500 | **PASS** |
| R8 | FY2026 no silent fallback | live case D | refused | 422, no substitution | **PASS** |
| R9 | invalid-result lifecycle | read-only inspection | explicit not-for-reporting state | no status column; nothing performed | **FAIL** |
| R10 | six canonical PDFs | live path per document | 6/6 driven | **1/6** | **FAIL** |
| R11 | EV-01 real regression | read-only anchors | 4175.903780 | 4175.903780 | **PASS (inherited, not re-driven)** |
| R12 | security / tenant isolation | live role matrix | no unexpected allow | 403/200/422 as designed; cross-tenant **not executed** | **PARTIAL** |
| R13 | route-level regression tests | `tests/unit/api` | in-process coverage of the guards | not added (fake lacks `manual_extraction`) | **FAIL** |
| R14 | disposable integration verification | disposable clone + suite | run recorded | not executed (F-046-1) | **FAIL** |

## 34. Remaining defects and limitations

| # | Defect | Evidence | Impact | Next action |
|---|---|---|---|---|
| RD-2 | Validation/completeness not line-aware end-to-end | live validate findings; `line_items` absent from `engines/validation.py` | blocks `mapped → validated → calculated` **and** the six-PDF gate | add a line-level branch to `engines/processing_workflow.py::_findings`; ensure `line_items` reaches the automatic gate — **highest priority; unblocks R4/R5/R10** |
| RD-4 | No not-for-reporting state for a snapshot+log pair | no status column on either table | 319.536000 is only conventionally excluded | minimal migration + RLS + lifecycle tests + live exercise |
| RD-5 | 4 `CalculationRequest` sites omit `supplier_id` | §18 audit | other paths can emit supplier-less emissions | wire `v3_processing_workflow.py:918`, `automatic_processing.py:1913`; decide attribution for `business.py`/`workflow.py` |
| RD-6 | stale pipeline-version test | asserts 1.2 == 1.1 | standing false failure | assert 1.2 and `!=` the P1 constant |
| RD-7 | no route-level unit coverage of the new guards | fake lacks `manual_extraction` | regressions rest on live harnesses | extend `InMemoryWorld` with `manual_extraction.get_item/get_batch` |
| RD-8 | cross-tenant execution unproven | no org-B extraction item | 403 path code-verified only | create a disposable org-B fixture (or clone) and run it |
| — | canonical supplier never created/reused | org-A master holds only `British Gas` | IA-04 story incomplete | use the operator-confirmed supplier path on documents 001 and 002 |

No critical accounting-integrity defect remains **on the remediated calculation route** (R1/R2/R3/R7/R8 hold),
but the workflow cannot yet traverse the reviewer stage, so the journey is not investor-complete.

## 35. Reproducibility

    # 0. backend (local only)
    cd /home/shomonrobie/ct_93d5cdd/backend
    set -a; . $HOME/ct_local_env/demo_lab/backend.env; set +a
    nohup .venv/bin/uvicorn main:app --host 127.0.0.1 --port 8070 > /tmp/p16r2_backend.log 2>&1 &

    # 1. RD-1 role seed (idempotent; updates permissions only)
    cd /home/shomonrobie/ct_93d5cdd && python3 tools/demo_lab/provision.py

    # 2. RD-1 + RD-3 live acceptance
    python3 tools/demo_lab/p16r2_verify.py
    #   expect: operator validate 403; admin validate 200 (blocking findings);
    #           operator calculate 409 (state); admin calculate 403

    # 3. inherited D-1/D-2/D-3/FY probes
    python3 tools/demo_lab/p16r_verify.py
    #   expect: A 200 (33696860…, 113.791500, supplier 2fd4072c…);
    #           B 422 component; C 422 scope; D 422 year

    # 4. read-only assertions
    psql "$LAB_DSN" -c "SELECT id, scope, co2e_kg, factor_id FROM calculation_snapshots ORDER BY created_at DESC LIMIT 4;"
    psql "$LAB_DSN" -c "SELECT id, status, pipeline_version FROM document_processing_queue ORDER BY created_at DESC LIMIT 4;"

Credentials stay outside the repository (`$HOME/ct_local_env/demo_lab/credentials.local.json`, 0600) and are
never printed by these tools.

## 36. Final status

### Change record

| Item | Value |
|---|---|
| Baseline | `2b5f46f5ad127d90e05ef4280d219d4004695f64` |
| Final | commit created immediately after this report (`chore(p16r2): grant can_review to internal admin reviewer; RD-1/RD-3 live acceptance`) plus a docs-only hash-record commit |
| Branch | `p8-release-reconciled` |
| Product code changed | **none** |
| Demo Lab changed | `tools/demo_lab/provision.py` (role seed), `tools/demo_lab/p16r2_verify.py` (new) |
| Migrations / schema / RLS | **none** |
| Corpus / oracle | **none** |

### Verdict

    P16_REMEDIATION_02_PARTIAL

**Progress made (with real evidence).**

* **RD-1 closed on the authorization half.** `can_review` was granted to the internal `admin` reviewer role
  **only**, and the live matrix is exactly as designed: operator validate **403**, admin validate **200**,
  operator calculate blocked only by state, admin calculate **403 `can_process`**. The reviewer/processor
  split is executable and minimally scoped.
* **RD-3 closed as a non-defect, with hard evidence.** The enqueue response faithfully reports the stored row
  (`901fc12d…` = `v3-auto-1.1` because it predates the 1.2 bump; every later job = `v3-auto-1.2`). The
  predecessor's observation was a stale-job misattribution; the automatic constant and the P1 shadow constant
  are correctly distinct.
* **RD-2's true location corrected.** `_completeness` **is** line-aware, so `0.33` proves the dict at the gate
  has no `line_items`; the concrete blocker is that `_findings`/validation has **no line-level branch**. That
  removes the ambiguity which stalled the predecessor.

**Why not PASS.** Gates **R5, R9, R10, R13, R14 FAIL**; **R4 and R12 are PARTIAL**; RD-6 is open. The keystone
is RD-2: because validation is not line-aware, a legitimate multi-line canonical document is returned to
`mapping`, so `mapped → validated → calculated` cannot complete, the reviewer workflow cannot be demonstrated
end-to-end, and six-PDF acceptance cannot progress. RD-4 additionally leaves the invalid 319.536000 result
without a system-enforced not-for-reporting state. Per §35, PASS requires all mandatory gates.

**Why not BLOCKED.** Nothing in the authorised environment prevented progress; every open gate has an
identified in-scope next action (§34); the accounting-integrity guards are proven; and no security control
blocked legitimate work.

**Truthfulness.** No unexecuted stage was marked PASS: the six-PDF table shows **1 of 6** and every other row
`NOT RUN`; EV-01 is recorded as inherited anchors only, not re-driven; RD-8 is recorded as code-verified, not
live-verified; the invalid result was neither deleted nor presented as valid; and no SQL-manufactured data
supports any accounting-flow claim.

**STOP.** No Scope 2, full Scope 3, regulatory framework, assurance, Step-3 UI or production work has begun,
and the next prompt (P17 / Prompt 2) has not been started.
