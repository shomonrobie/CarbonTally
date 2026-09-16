# CT-P8-B3-IMPLEMENTATION-20260913-032

**Task ID:** `CT-P8-B3-IMPLEMENTATION-20260913-032` (increment 1 of the B3 batch)
**Title:** Phase 8 Batch B3 — Disclosure Model Integration — **intensity sub-layer implemented, applied and tested**
**Date:** 2026-09-13
**Authorization:** PO blanket authorization `…050`; PO direction of 2026-09-13 answering `B3-D1`
**Contract:** `docs/architecture/CARBONTALLY_PHASE8_B3_IMPLEMENTATION_CONTRACT_20260913.md` (§6.1/§6.2/§17 + §22 amendment)
**Environment:** `carbontally_qa_phase8` (non-production, dedicated)

---

## 1. Scope delivered (increment 1)

| Deliverable | State |
|---|---|
| **A** schema: controlled intensity catalogue + **separate** framework-claim table + org-scoped ratio selection | **IMPLEMENTED** |
| **A′** the PO's capability-vs-requirement separation | **IMPLEMENTED STRUCTURALLY** (two tables; CHECK-restricted `support_class`; statutory class requires evidence) |
| Seeds | **4 generic candidates**, `framework_links = 0` (no unverified claims) |
| RLS + policies | catalogue tables: authenticated read only (B1 global-catalogue posture); ratios: member read / org-admin write (B1 org-scoped posture) |
| B–L (projection engine, mappings, applicability, purposes, statuses, read model, API, service, tests) | **NOT YET IMPLEMENTED** — next increment |

## 2. Files created

1. `supabase/migrations/20260917000000_p8_b3_intensity_catalogue.sql`
2. `supabase/migrations/20260917010000_p8_b3_intensity_ratios.sql`
3. `docs/architecture/CARBONTALLY_PHASE8_B3_IMPLEMENTATION_CONTRACT_20260913.md` (amended §22)
4. this report

No pre-existing file was modified; no existing table, grant, policy or RLS flag was touched (verified by diff — §4).

## 3. Application to QA

| Migration | Apply | Re-apply |
|---|---|---|
| `20260917000000_p8_b3_intensity_catalogue.sql` | **rc=0** | **rc=0** |
| `20260917010000_p8_b3_intensity_ratios.sql` | **rc=0** | **rc=0** |

Live inventory: `disclosure_intensity_denominator_types` = **4** rows · `disclosure_intensity_denominator_framework_links` = **0** · `disclosure_intensity_ratios` = **0** · RLS **enabled** on all three; policies = 1 / 1 / 2.

## 4. Verification performed (behavioural, not asserted)

| # | Probe | Expectation | Result |
|---|---|---|---|
| T1 | insert a `STATUTORY_REQUIRED` framework link with no evidence | **rejected** | **PASS** — `…_statutory_requires_evidence` violated |
| T2 | insert an `official_reference` on an unverified link | **rejected** | **PASS** — `…_reference_requires_verification` violated |
| T3 | set `support_class='STATUTORY'` on a generic denominator | **rejected** | **PASS** — `…_support_check` violated |
| T4 | insert a `NOT_VERIFIED` framework link | accepted | **PASS** |
| T5 | insert an **evidenced** `STATUTORY_REQUIRED` link (basis + tier + verified_at) | accepted | **PASS** (first attempt failed for a **probe-design** reason — duplicate pair from T4; re-probed with the row removed → `INSERT 0 1`, `verified=true`). Test rows deleted afterwards. |
| T7 | org ratio with blank `selection_basis` | **rejected** | **PASS** — `…_basis_check` violated |
| P1 | idempotency: re-apply both migrations | `rc=0`, zero new objects | **PASS** |
| P2 | additive-only parity: `pg_dump` before (18,908 lines) vs after (19,235 lines) | only new `disclosure_intensity_*` objects differ | **PASS** — no pre-existing object line changed |

**Interpretation of T1+T5 together:** the schema **cannot** record an unevidenced statutory claim (the PO's requirement) while **remaining capable** of recording a properly evidenced one (the PO's "must stay architecturally capable").

## 5. Not done in this increment (explicit)

Projection engine; requirement/purpose mapping loader; applicability engine; purpose projections; value-status semantics; value→line read model; API surface; service layer; the full §16 test contract. **Gate V3 is not complete.** No backfill. No production action.

## 6. Repository state

| Item | Value |
|---|---|
| Branch / HEAD | `main` / `37b19d13723b0b1eabceeade86ce1615a98ab400` (unchanged; **no commit**) |
| Staged | 0 |
| Tracked modifications | 218 (pre-existing, unchanged) |
| New untracked artefacts | the two migrations + this report (+ the amended contract, previously untracked) |

## 7. Verdict

### `B3 INCREMENT 1 COMPLETE — INTENSITY SUB-LAYER IMPLEMENTED, APPLIED AND BEHAVIOURALLY VERIFIED; REMAINING B3 DELIVERABLES PENDING`


---

## 8. Increment 2a — projection engine core, status and applicability semantics (COMPLETE)

**Delivered**

| Deliverable | Artefact |
|---|---|
| **B (core)** producer registry over the ratified closed `source_kind` set | `backend/domain/disclosure_projection.py` — `PRODUCER_REGISTRY` covering exactly the 9 ratified `SOURCE_KINDS`; unknown kinds raise; per-kind permitted aggregations enforced |
| **B (core)** deterministic aggregation | `aggregate()` — `SUM_KG_CO2E`, `SUM` (single normalised unit via `core.units.normalize_unit`, mismatch raises), `DISTINCT_COUNT`, `RATIO`, `PASSTHROUGH` (exactly one row); **no emission is recomputed** |
| **F** value-status semantics | `decide_projection()` returns only `PENDING`/`RESOLVED`/`UNRESOLVED` (`PQ-3`); `effective_class` derived with documented precedence (applicability → capability → requirement class) |
| **F** honesty rules | `NOT_SUPPORTED` ("not supported by CarbonTally") and `CUSTOMER_INPUT_REQUIRED` ("customer input required") produce **distinct** reasons and are never conflated (`DM-5`); empty authoritative rows yield `UNRESOLVED`, **never zero** |
| **D (core)** applicability semantics | `derive_effective_class()` keeps `UNDETERMINED` first-class and never coerces it to not-applicable (`APPL`/D13); `validate_applicability_basis()` requires a real basis |
| **D (guard)** no legal determination | `assert_no_legal_determination()` rejects legal-conclusion phrasing in any basis text |
| **H (core)** intensity arithmetic | `compute_intensity_ratio()` — positive denominator enforced; zero/absent denominator yields no value |

**Verification (executed, not asserted)**

| Item | Command | Result |
|---|---|---|
| Pure unit suite | `pytest tests/unit/domain/test_disclosure_projection.py -q` | **22 passed, 0 failed** |

Coverage includes: registry completeness/drift, unknown-producer rejection, per-source aggregation permissions, decimal-string and int inputs, unit-mismatch rejection, distinct counting, zero-denominator ratio, passthrough cardinality, empty-row honesty, `UNDETERMINED` non-coercion, support-vs-input non-conflation, customer-input materialisation, source-kind-required, and legal-claim rejection.

**Still pending in B3 (increment 2b)**

1. data layer: read `calculation_snapshots` / `emissions_logs` / evidence into projection rows and persist via the existing B1 `upsert_disclosure_value` / `link_value_evidence` paths (idempotent, transactional);
2. service orchestration + audit (`AUDIT_VALUE_MATERIALISED` etc.);
3. value→line read model (the B2 `COALESCE` join) as a repository read method;
4. API/service endpoints (contract §12.2) with server-side authorization;
5. runtime QA verification (projection over real data; idempotent re-run; ALLOW/DENY);
6. independent **V3** verification and B3 closure.

**Note:** no new database object was created in increment 2a; nothing was applied, committed or deployed.

---

## 9. Increment 2b — data layer, service, read model, runtime verification (COMPLETE)

### 9.1 Delivered

| Deliverable | Artefact |
|---|---|
| **B/C/D data layer** | `backend/data/disclosure_projection.py` — report context; purpose requirement set; authoritative snapshot/emissions row loading (shaped for the projection engine); requirement-mapping lookup; evidence coverage; **B2 value→line read model** (the `COALESCE` join); intensity catalogue; framework-treatment lookup; idempotent intensity-ratio upsert |
| **service / orchestration** | `backend/services/disclosure_projection.py` — projects every requirement of a bound report version: applicability from the recorded assessment (**absent ⇒ `UNDETERMINED`**), producer mapping (absent ⇒ honest `UNRESOLVED`), rows → `decide_projection` → persisted through the **existing B1 `upsert_disclosure_value`** (tenant guard + immutability guard + per-value audit) |
| **audit** | Reuses B1's `AUDIT_VALUE_MATERIALISED` path; no new audit mechanism, table or taxonomy |
| **tests** | `backend/tests/integration/test_disclosure_b3_projection_runtime.py` (4 runtime tests) + 1 new pure test = **23 pure tests** |

### 9.2 Verification (executed on `carbontally_qa_phase8`)

| Suite | Result |
|---|---|
| B3 pure unit (`test_disclosure_projection.py`) | **23/23 PASS** |
| B3 runtime (`test_disclosure_b3_projection_runtime.py`) | **4/4 PASS** |
| B1+B2 runtime (regression) | **36/36 PASS** |
| B1/B2 unit + static (regression) | **75/75 PASS** |
| S1/S3 lifecycle + report API (regression) | **89/89 PASS** (with the pre-existing F-030-1 defect deselected) |
| **Total executed** | **227 PASS, 0 unexplained failures** |

Behaviour proven at runtime: a mapped requirement materialises **123.5 kgCO2e** from two real snapshots; re-running is idempotent (4 rows, one per requirement, same ids); a `CUSTOMER_INPUT_REQUIRED` requirement is `UNRESOLVED` with "customer input required"; a `MISSING_CAPABILITY` requirement is `UNRESOLVED` with the **distinct** "not supported by CarbonTally"; an unmapped requirement is `UNRESOLVED` with "no producer mapping recorded…" and **no fabricated zero**; a version with no recorded assessment yields `UNDETERMINED` for every requirement and **zero resolved values**; the value→line join returns the version's values; the catalogue exposes exactly the four generic candidates with **no framework claim**, and ratio upserts compute (250/100 = 2.5; 250/200 = 1.25) without duplicating rows.

### 9.3 Defects found and fixed during verification

| # | Defect | Class | Fix |
|---|---|---|---|
| **F-B3-1** | `DisclosureProjectionRepository` did not implement `AbstractRepository`'s abstract `get`/`save`/`delete` → could not instantiate | **implementation defect** | read-model stubs added (B1 style) |
| **F-B3-2** | `unmapped_decision` did not honour `CUSTOMER_INPUT_REQUIRED` precedence (reported "no producer mapping" instead of "customer input required") — a `DM-5` conflation risk | **implementation defect** | precedence corrected; **regression test added** (pure suite 22→23) |
| **F-B3-3** | `upsert_intensity_ratio` raised `AmbiguousParameterError` (`$5`) | **implementation defect** | explicit `$5::numeric` / `$7::numeric` casts (the B1 V1 F1 precedent) |
| **F-B3-4** | Test fixtures omitted NOT NULL snapshot columns and the exactly-one-source CHECK | test defect | fixture corrected (factor row + `co2e_multiplier`/`methodology`/`algorithm_version`/`content_hash`) |
| **F-B3-5** | Read-model test read before projecting (its fixture is function-scoped) | test defect | projection run added |
| **F-B3-6** | B1's `test_b2_b3_b4_boundary_untouched` forbade B3 objects | **expected B1 test-scope artefact** | **AMENDED, never deleted** (the B2 20.6 precedent): the namespace assertion and the guard now permit **exactly** the three ratified B3 intensity tables; the **B4 narrative/commentary prohibition is unchanged** |

### 9.4 Still pending in B3

1. **API/service endpoints** (contract §12.2) with server-side authorization;
2. independent **V3** verification of the full batch;
3. **B3 closure**;
4. (recorded limitation) the value→line assertion currently proves the join executes and returns values; a fully line-linked assertion (requiring `manual_extraction_items` fixtures) is deferred to the V3 pass.

### 9.5 Repository state

No commit; no production access; no backfill; no pre-existing table/grant/policy altered. Changed this increment: `backend/domain/disclosure_projection.py` (fixed), `backend/data/disclosure_projection.py` (new), `backend/services/disclosure_projection.py` (new), `backend/tests/integration/test_disclosure_b3_projection_runtime.py` (new), `backend/tests/unit/domain/test_disclosure_projection.py` (extended), `backend/tests/integration/test_disclosure_b1_runtime.py` (two documented amendments).

---

## 10. Increment 3 — API surface (§12.2) implemented and verified

### 10.1 Delivered

| Artefact | Content |
|---|---|
| `backend/api/v3_disclosure.py` (new) | `APIRouter(prefix="/api/v3")` exposing all seven contract §12.2 routes: `GET /reports/{report_id}/disclosure`, `GET /reports/{report_id}/disclosure/{value_id}/lines` (the `DM-6` read model), `POST /reports/{report_id}/disclosure/project`, `GET`/`POST /reports/{report_id}/intensity`, `GET`/`POST /organizations/{organization_id}/applicability` |
| `backend/api/router.py` | router imported and included (one import, one `include_router` — no other change) |
| `backend/data/disclosure_projection.py` | four API read helpers added (`get_value`, `list_values`, `list_applicability`, `list_intensity_ratios`) |
| `backend/tests/unit/api/test_v3_disclosure_api.py` (new) | 14 in-memory API tests (no database access) |

### 10.2 Authorization enforced server-side (the UI is never the boundary)

* **Read** requires an organisation member of the owning organisation; **Processing-Entity staff and CarbonTally internal staff are denied** (403) — the S3 boundary precedent.
* **Write** (projection run, intensity selection, applicability assessment) requires organisation **Owner/Admin**; **Member is denied** (403).
* A disclosure value from another tenant, or from another report, is reported as **404** rather than leaking existence.
* Unknown/inactive catalogue denominator ⇒ **404 with an explanatory message pointing at the catalogue endpoint** — never a raw database error (the explicit §12.2 requirement).
* Blank/invalid selection basis ⇒ 400/422; a basis asserting a **legal determination** is rejected with 400 (the `APPL` boundary).
* No endpoint can write a calculated value; **no narrative endpoint exists** (UI/narrative remain B4).

### 10.3 Verification (executed)

| Suite | Result |
|---|---|
| B3 API unit (in-memory, dependency-overridden) | **14/14 PASS** (EXIT=0) |
| B3 pure unit | **23/23 PASS** |
| B3 runtime (QA `carbontally_qa_phase8`) | **4/4 PASS** |
| B1+B2 runtime regression | **36/36 PASS** |
| B1/B2 unit + static regression | **75/75 PASS** |
| S1/S3 lifecycle regression | **89/89 PASS** (F-030-1 deselected) |
| Broad unit/API + Phase 8 integration regression (single session) | executed; **exactly one failure → F-B3-7 (pre-existing flake, isolated below)**. *Limitation: the aggregate count line was truncated by the capturing pipeline; the per-suite counts above are the precise figures.* |

### 10.4 Finding F-B3-7 — pre-existing flaky B2 assertion (NOT a B3 regression)

`tests/integration/test_evidence_line_items_b2_runtime.py::test_16_audit_volume_granularity_and_payload_discipline` asserts the substring `'777'` is **absent** from an audit payload. The payload legitimately contains a randomly generated UUID; in the combined run the UUID `4d8d8777-…` contained `777`, so the assertion failed. **Re-run twice in isolation → 21/21 PASS both times.**

**Classification:** non-deterministic test defect in a **closed** batch (B2). **Disposition: recorded, not fixed** — B2 is closed and this is outside B3 scope. **Recommendation for the PO:** replace the digit-substring probe with a deterministic payload-discipline assertion (permitted key set / no secret material), as a small bounded test-only change.

### 10.5 Test-harness notes

* The app's error envelope is `{"error": {"code", "message", "details"}, "request_id"}` (api/router.py §`http_exception_handler`); the four error-body assertions were adapted to read `error.message` (status codes and content expectations unchanged — no weakening).
* The fake pool implements `acquire()` + `fetch`/`fetchrow` routed by SQL marker; **the development database is never opened** in the unit API suite.

### 10.6 Repository state

No commit; no production access; no backfill. New this increment: `backend/api/v3_disclosure.py`, `backend/tests/unit/api/test_v3_disclosure_api.py`; modified: `backend/api/router.py` (2 lines), `backend/data/disclosure_projection.py` (4 read helpers).
