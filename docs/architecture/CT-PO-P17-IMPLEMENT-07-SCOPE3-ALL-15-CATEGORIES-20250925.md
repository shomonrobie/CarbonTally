# P17 IMPLEMENT-07 — Scope 3, All Fifteen Categories

**Task ID:** `P17-IMPLEMENT-07-20260925-SCOPE3-ALL-15-CATEGORIES`
**Date:** 2025-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled`
**Starting SHA:** `bfd51358e2e733f70184f286cfd4a55bc6504310` (verified actual HEAD before any change)
**Nature:** IMPLEMENTATION. No UI/marketing change, no migration, no RLS change, no production contact.

---

## 1. Task ID

`P17-IMPLEMENT-07-20260925-SCOPE3-ALL-15-CATEGORIES`

## 2. Starting SHA

`bfd51358e2e733f70184f286cfd4a55bc6504310` — the IMPLEMENT-06 report commit, confirmed with
`git rev-parse HEAD` before any edit. Working tree clean apart from the pre-existing `.gitignore`.

## 3. Ending SHA

`7739ed7` — the final implementation commit; this report is its successor (§4).

## 4. Exact commit SHA(s)

| # | SHA | Message |
|---|---|---|
| 1 | `4505e6f` | `feat(p17): add the unified Scope 3 framework with fifteen category contracts` |
| 2 | `b68bf7b` | `feat(p17): expose the canonical Scope 3 calculation endpoint` |
| 3 | `7739ed7` | `test(p17-07): cover all fifteen Scope 3 categories` |
| 4 | *(this report)* | `docs(p17): record IMPLEMENT-07 report` |

**Not pushed.** No amend/rebase/reset; all prior P17 history preserved.

## 5. Files created / modified

**Created**

| File | Purpose |
|---|---|
| `backend/domain/scope3_contracts.py` | The 15 explicit category contracts + `ClarificationRequirement` |
| `backend/services/scope3_calculation.py` | The ONE unified Scope 3 service |
| `backend/api/v3_scope3.py` | ONE canonical endpoint, `POST /api/v3/scope3/calculate` |
| `backend/tests/unit/services/test_p17_07_scope3_framework.py` | 98 tests |
| this report | Mandatory implementation report |

**Modified**

| File | Change |
|---|---|
| `backend/engines/calculation.py` | `from_match_result` gained optional `source_item_id` / `source_line_item_id` (additive; §12) |
| `backend/api/router.py` | Registered `v3_scope3_router` in the existing include block |

**Not modified:** any migration, any RLS policy, `domain/scope3.py`, `domain/estimation.py`,
`domain/data_quality.py`, `services/scope2_calculation.py`, `api/v3_scope2.py`, `api/dependencies.py`.

## 6. Current-vs-new implementation discovery

Using the project truth vocabulary, what existed BEFORE this task:

| Artefact | State before this task |
|---|---|
| `domain/scope3.py` — taxonomy, `Scope3Status`, `CATEGORY_STATUS`, boundary sets, `assert_calculable`, `assert_boundary_complete` (DC-02/04/05/07), `requires_estimation_record`, `derives_from_source_snapshot` | **CODE EXISTS**, well-tested by the taxonomy suite, **no production consumer** |
| `domain/scope3_contracts.py` | **DID NOT EXIST** |
| `domain/estimation.py` — `EstimationRecord`, T-INV-12 rule | **CODE EXISTS**, no production consumer |
| `domain/data_quality.py` — five-value vocabulary, `is_estimated` | **CODE EXISTS** |
| `services/scope3_calculation.py` | **DID NOT EXIST** |
| `api/v3_scope3.py` | **DID NOT EXIST** — `POST /api/v3/scope3/calculate` was **NOT AVAILABLE** |
| Per-category calculation pathway | **DID NOT EXIST — 0 of 15 categories had one** |
| Canonical persistence for a Scope 3 result | **AVAILABLE but UNREACHABLE** — the pipeline existed, nothing drove it |

So before this task the honest status was: the taxonomy and guards were **DOCUMENTED / CODE EXISTS**, and
**not one** of the fifteen categories had a working, persisted calculation pathway. Nothing here is claimed as
available merely because a taxonomy row existed.

## 7. Unified Scope 3 architecture

**One pathway, fifteen categories.** No second engine, no `scope3_calculations` ledger, no per-category
service.

```
Scope3Input(category + activity + boundary declarations + data_quality + estimation)
  → category validation            (domain.scope3.validate_scope3_category)
  → CONTRACT lookup                (domain.scope3_contracts.contract_for)
  → pathway / methodology check    (allowed_pathways, methodologies)
  → required-input check           ── absent? → ClarificationRequirement (no number)
  → data-quality check             (vocabulary + estimation-pathway labelling)
  → T-INV-12 estimation check      (EstimationRecord required when estimated)
  → factor check                   (activity/factor pathway needs a matched factor)
  → evidence check                 (contract.requires_evidence)
  → DC-02/04/05/07 boundary guard  (domain.scope3.assert_boundary_complete, reused)
  → AccountingDimensions(scope3_category=..., data_quality=..., boundaries...)
  → CalculationRequest.from_match_result   (existing canonical bridge)
  → CalculationEngine.calculate()          (existing canonical write: snapshot + log)
```

Category identity travels on `AccountingDimensions.scope3_category` into the existing P17 columns, so a
Scope 3 result is persisted by exactly the same code as Scope 1 and Scope 2.

## 8 / 9. All 15 category statuses and methodologies

`Automation` and architecture status are truthful: the architecture's own
`SUPPORTED / PARTIAL / DEFERRED / NOT_IMPLEMENTED` is reported **verbatim and never upgraded**.

| Category | Methodology | Automation | Data Quality | Evidence | Persistence | Tests | Status |
|---|---|---|---|---|---|---|---|
| 1 Purchased goods and services | supplier-specific / average-data / spend-based | activity/factor, optional spend variant | any of five | source lineage | canonical snapshot + log | ✅ | **IMPLEMENTED** |
| 2 Capital goods | supplier-specific / average-data | activity/factor **gated on a required capitalisation declaration** | any of five | source lineage | canonical | ✅ | **IMPLEMENTED** |
| 3 Fuel- and energy-related activities | average-data / supplier-specific | activity/factor, hard-linked to its Scope 1/2 source snapshot (DC-02) | any of five | **required** | canonical | ✅ | **IMPLEMENTED** |
| 4 Upstream transportation and distribution | average-data / supplier-specific / distance-based | activity/factor, DC-04 boundary required | any of five | source lineage | canonical | ✅ | **IMPLEMENTED** |
| 5 Waste generated in operations | average-data / supplier-specific | activity/factor, material + evidenced treatment route required | any of five | source lineage | canonical | ✅ | **IMPLEMENTED** |
| 6 Business travel | distance-based / average-data / spend-based | activity/factor, trip purpose required | any of five | source lineage | canonical | ✅ | **IMPLEMENTED** |
| 7 Employee commuting | average-data / extrapolated / survey-based | **estimation-based**; T-INV-12 record mandatory | estimated only | estimation basis | canonical | ✅ | **IMPLEMENTED_WITH_ESTIMATION** |
| 8 Upstream leased assets | average-data / supplier-specific / asset-specific | activity/factor, DC-07 consolidation required | any of five | source lineage | canonical | ✅ | **IMPLEMENTED** |
| 9 Downstream transportation and distribution | average-data / supplier-specific / distance-based | activity/factor, DC-04 boundary required | any of five | source lineage | canonical | ✅ | **IMPLEMENTED** |
| 10 Processing of sold products | average-data / proxy-data / modelled | **estimation-based**; no processing factor invented | estimated only | estimation basis | canonical | ✅ | **IMPLEMENTED_WITH_ESTIMATION** |
| 11 Use of sold products | modelled / average-data / proxy-data | **estimation-based over an explicitly persisted use-phase assumption** | estimated only | estimation basis | canonical | ✅ | **IMPLEMENTED_WITH_ESTIMATION** |
| 12 End-of-life treatment of sold products | average-data / supplier-specific | activity/factor with a downstream origin (DC-05) + estimation record | any of five | source lineage | canonical | ✅ | **IMPLEMENTED** |
| 13 Downstream leased assets | average-data / asset-specific | activity/factor, DC-07 consolidation required | any of five | source lineage | canonical | ✅ | **IMPLEMENTED** |
| 14 Franchises | average-data / extrapolated / industry-average | **estimation-based over a required allocation basis** | estimated only | estimation basis | canonical | ✅ | **IMPLEMENTED_WITH_ESTIMATION** |
| 15 Investments | average-data / industry-average / modelled | **estimation-based, equity-share attribution only** | estimated only | estimation basis | canonical | ✅ | **IMPLEMENTED_WITH_ESTIMATION** |

**All fifteen categories have a real, tested, persisted pathway.** Five (7, 10, 11, 14, 15) are
estimation-based — which is what those categories *are*. Categories 2 and 10 sit under a `NOT_IMPLEMENTED`
architecture status and 11, 14, 15 under `DEFERRED`; **none is silently promoted**.

### 9.1 The one place this deserves scrutiny

- **Category 2**: the taxonomy reason for `NOT_IMPLEMENTED` is that capitalisation was not carried by the
  product model. This task makes `capitalisation_declared` a **required input** — the missing discriminator
  itself. `CATEGORY_STATUS` is unchanged and the contract reports `NOT_IMPLEMENTED` verbatim.
- **Category 10**: no processing factor is invented. The estimation pathway requires a substantiated basis and
  `refusal_reason` states that processing factors are never invented.

Both remain visible as architecture gaps *and* have a truthful labelled pathway.

## 10. Data-quality handling

The existing five-value vocabulary (`domain/data_quality.py`) is reused verbatim — **no new taxonomy**.
`data_quality` is **mandatory** on every Scope 3 request: an unclassified figure cannot be distinguished from
a measured one. Two rules are enforced:

1. an **estimation-pathway** category must carry an estimate classification — an estimate can never wear a
   measured label (tested for categories 7, 10, 11, 14, 15);
2. any estimated classification, or an estimation-required category, demands a persisted estimation record
   (tested for 7, 11, 12, 14).

The demo can visibly separate a measured value from an estimate (`primary_measured` vs `secondary_estimated` /
`spend_based_estimated` / `modelled`), and the API returns an explicit `is_estimated` flag.

## 11. Estimation handling

The existing `EstimationRecord` (T-INV-12) is reused — **one** estimation model, not fifteen. It already
refuses an estimate naming no method or recording neither inputs nor assumptions; a test re-asserts that. The
service refuses to persist an estimate without one.

## 12. Evidence / provenance

Preserved on the canonical snapshot: `source_item_id`, `source_line_item_id`, `source_file`, `source_page`,
`factor_id`, `factor_kind`, `scope3_category`, `data_quality`, the boundary declarations, the data owner and
the acting-for/performed-by pair.

**A real gap was found and fixed while testing.** `CalculationRequest.from_match_result` had no
`source_item_id` / `source_line_item_id` parameters, so the service's evidence lineage could not reach the
engine. Both were added **optional, defaulting to `None`** (additive; every existing caller unchanged) and are
now passed through; a test asserts the lineage lands on the snapshot. Category 3 declares
`requires_evidence=True` and is refused without a source reference. **No evidence was fabricated and no
parallel evidence store was created.**

## 13. Supplier attribution

`supplier_id` is accepted, carried to the emissions log by the existing engine path, and preserved where
resolved. Categories 1, 2 and 5 declare it optionally. **No supplier is invented and none is silently
dropped**; an ambiguous supplier remains a manual-review condition (`manual_review_conditions` names
"unresolved waste supplier" for category 5), surfacing as a controlled clarification. The existing
supplier-resolution pipeline is reused unchanged; no second supplier system was created.

## 14. Boundary / double-counting controls

The architecture's own guard (`domain.scope3.assert_boundary_complete`) is reused **unchanged** — not
re-implemented. Proven by test:

| Requirement | Result |
|---|---|
| 1 upstream transport cannot silently become downstream | ✅ cat 4 + `downstream` → `BoundaryAmbiguityError`; the two persist distinguishable boundaries |
| 2 operational waste cannot silently become end-of-life | ✅ cat 5 + `sold_product_eol` → refused; origins distinguishable when persisted |
| 3 upstream leased assets cannot become downstream | ✅ categories 8 and 13 distinguishable by persisted category; both require DC-07 |
| 4 Scope 1 fuel is not automatically Category 3 | ✅ `derives_from_source_snapshot(3)` True, False for 1/2/4/5/6; cat 3 without a source link clarifies |
| 5 Scope 2 energy is not automatically Category 3 | ✅ same DC-02 guard |
| 6 one activity not silently counted in incompatible categories | ✅ the category is required, explicit and persisted; the boundary must agree with it |
| 7 category identity persisted with the calculation | ✅ asserted for **all fifteen** categories, on snapshot **and** log |

**No legitimate activity was blocked to solve double counting** — every category has a working pathway; only
*contradictory* boundary declarations are refused.

## 15. CAMS / accounting context

`ensure_record_owner_authorized` resolves the context; the **data owner** is
`context.data_owning_organization_id` (the authorisation key), and `performed_by_organization_id` /
`acting_for_organization_id` come from that resolved context only. The body's `organization_id` is a *claim*
that is verified, never an entitlement.

## 16. Security / tenant isolation

| Case | Result |
|---|---|
| direct customer → own organization | ✅ owner is the resolved data owner |
| consultant → own organization | ✅ via the resolved context (IMPLEMENT-02) |
| consultant → authorized client | ✅ delegated context; acting-for ≠ performed-by (asserted) |
| consultant → unauthorized client | ✅ 403 by `resolve_accounting_context` (IMPLEMENT-02, unchanged) |
| client → own organization | ✅ |
| forged acting-for | ✅ structurally impossible: no attribution is read from the body |
| forged owner | ✅ the payload claim is re-authorised server-side |
| cross-tenant factor / customer-factor | ✅ same repositories as Scope 1/2 |
| cross-tenant supplier / evidence | ✅ resolved server-side; no client-supplied ownership |

**No RLS policy was added, changed or weakened; no service-role bypass was introduced.**

## 17. API

**ONE endpoint:** `POST /api/v3/scope3/calculate`, registered in the existing `api/router.py` include block —
`['/api/v3/scope3/calculate']` verified by import. The category is a request field, not fifteen routes. It
returns the calculation identity, category, scope, pathway, architecture status, methodology, data quality,
`is_estimated`, factor provenance, `co2e`, the data owner, acting-for/performed-by attribution and the content
hash. A clarification returns **422** with `status: CLARIFICATION_REQUIRED` and the missing field names.

## 18. Persistence

The canonical path only: `CalculationEngine` → `calculation_snapshots` → `emissions_logs`, with category
identity on the P17 dimension columns. **No `scope3_calculations` ledger and no per-category table were
created.** Asserted for all fifteen categories (one snapshot + one log each, matching dimensions).

## 19. Lifecycle / reportability

**Nothing in this task writes a lifecycle field.** A successful Scope 3 calculation is persisted exactly as a
Scope 1/2 result is, so `DRAFT → SUBMITTED → VALIDATED → CALCULATED → REVIEW → APPROVED → REPORTABLE` is
respected and **no result is auto-marked REPORTABLE**.

## 20. Demo fixtures

`_FIXTURES` in the P17-07 test module is the deterministic synthetic fixture set: one entry per category
stating the minimal truthful input, its data-quality label, its boundary declarations and whether an
estimation record is required. **Synthetic only**, deterministic, reproducible, category-labelled,
methodology-labelled, data-quality-labelled, with estimation-based categories saying so explicitly. **No
production data and no fake "verified" supplier/customer evidence.**

## 21. Test results

`tests/unit/services/test_p17_07_scope3_framework.py` — **98 tests, 98 passed, 0 failed.**

Coverage: all 15 contracts load and are complete; architecture status never upgraded; invalid category
rejected; **all 15 categories calculate, persist identity and produce correct numerics (100 × 2.50000 =
250.000000)**; contract boundary fields match persisted dimensions; estimation categories are marked
estimated; an estimation pathway refuses a measured label (5 categories); T-INV-12 record required (4
categories); missing input → clarification not a value; missing boundary → clarification; missing data quality
refused; invalid methodology/pathway refused; unsupported pathway refused; unmatched factor refused; category 3
requires its source snapshot; DC-04 and DC-05 contradictions refused both ways; 4/9, 5/12 and 8/13
distinguishable; DC-07 fail-closed for 8 and 13; estimated vs measured distinguishable; estimation metadata
preserved; an insubstantial estimation record refused; source lineage preserved; P16 request identity and
content hash preserved.

**No test was skipped, deleted or relaxed.** (No API-level test file was added — see §23.)

## 22. Full-suite result

**Attempted; the full suite did not complete within the execution budget. No full-suite verification is
claimed.**

| Run | Result |
|---|---|
| P17-07 new tests | **98 passed, 0 failed** |
| `tests/unit/engines tests/unit/services tests/unit/domain` | **completed**; 3 failures, all pre-existing |
| `tests/unit tests/integration` (full suite) | **NOT completed** — exceeds the command time budget (as in IMPLEMENT-04/05/06) |
| `tests/integration/*` | DB-dependent; needs a live database and the destructive harness, which was **not** run |

**Exact full-suite totals were NOT obtained.** I am not reporting numbers I did not measure.

The 3 failures are `tests/unit/engines/test_extraction_suggestions.py`, proven pre-existing by the stash-based
baseline comparison recorded in IMPLEMENT-05, and unrelated to Scope 3. My only change to a shared path is the
**additive, default-`None`** `source_item_id` / `source_line_item_id` parameters on `from_match_result`, which
cannot affect an existing caller; the engines/domain/services suites confirm no new failure.

## 23. Known incomplete work

1. **Full-suite run not completed** (§22).
2. **No API-level test file.** The Scope 3 route is written, imports and registers (verified), but its HTTP
   behaviour is not covered by its own tests — the service layer beneath it is comprehensively tested (98
   tests). This is a real verification gap and the highest-value next step.
3. **No live-database round-trip.** Category identity reaches the P17 columns by construction; the INSERT was
   never executed against PostgreSQL.
4. **`consolidation_approach` (DC-07) is validated but not persisted on the snapshot** — it is an
   organization-level property with no per-result column, so DC-07 fails closed but leaves no per-snapshot
   trace. Documented rather than invented.
5. **Estimation and supplier records are validated, not yet written as their own rows.** The service builds and
   validates an `EstimationRecord` (so the classification and basis are enforced), but no repository writes it
   to `estimation_records`; a resolved `supplier_id` reaches the log only through the existing engine path.
6. **Read projection** for the P17 dimension columns remains deferred (as in IMPLEMENT-05/06).

## 24. Deferred work

| Item | Reason |
|---|---|
| Scope 3 API tests; `estimation_records` repository; snapshot/log projection of P17 dimensions | Genuinely required for full completion; not reachable within this task's budget |
| Category-specific automation depth beyond the stated pathways | The taxonomy's `DEFERRED` items await PO decisions (franchise operating model, investment attribution beyond equity share, use-of-sold-products methodology) |
| UI, landing page, FAQ, marketing copy, Insight redesign, report-version/review-assignment attribution, `review_audit_trail` trigger work, ARCH-07, production deployment | Out of scope by instruction |

## 25. Production-contact statement

**NO PRODUCTION SYSTEM WAS CONTACTED.**

- No production database, credential, migration or deployment; no production customer data.
- No external production API call; nothing pushed to any remote.
- **No database was opened at all.** Every assertion used in-memory sinks and the existing unit suite. No
  migration was created or applied.
- The Demo Lab, `carbontally_qa_phase8`, `carbontally_test` and every other persistent local database were
  untouched; the **destructive integration harness was not run** (F-046-1 respected).

## 26. Final verdict

```
P17_IMPLEMENTATION_PARTIAL
```

**Why PARTIAL, not COMPLETE.** The task's condition is that *"all 15 categories have a real tested
calculation/estimation pathway **and** the unified framework works end-to-end within the scope of this
implementation task."*

The first half is **met and proven**: fifteen explicit contracts, fifteen working pathways, category identity
persisted, boundaries enforced, data quality and estimation ruled, one service, one endpoint, one persistence
path — **98 tests passing**.

The second half is **not fully met**: the API's own HTTP behaviour has no test file (§23.2), the full suite did
not complete (§22), and estimation/supplier records are validated but not persisted as their own rows
(§23.5). Claiming COMPLETE would be false, and the task instructs explicitly: *"Do not inflate the verdict."*

**What is genuinely delivered:** a single, truthful Scope 3 accounting framework covering all fifteen
categories with **no parallel accounting system** — one service, one endpoint, one persistence path; explicit
methodology, data quality and refusal reasons per category; the architecture's own DC-02/04/05/07 boundary
controls reused unchanged; the existing T-INV-12 estimation rule reused; and an explicit, non-fabricating
manual-review path that returns the missing fields instead of a number.

**Not claimed:** `E2E VERIFIED`, `INDEPENDENTLY VERIFIED`, `PRODUCTION READY`. The framework has not been
exercised through HTTP by its own tests, against a real PostgreSQL instance, or by an independent verifier.




