# CT-PO-P16-REMEDIATION-05 — Final P16 Acceptance Closure

**Task ID:** P16-REMEDIATION-05-20260925-FINAL-P16-ACCEPTANCE-CLOSURE
**Date:** 2026-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Environment:** local Demo Lab only — `carbontally_demo_local` @ 127.0.0.1:54426, release backend @
127.0.0.1:8070, lab gateway @ 127.0.0.1:54430.

---

## 1. Task identity

Final verification/remediation pass for P16 core accounting. Determines whether P16 can truthfully be
declared PASS, closing the gates left open by P16-R4. **Not** Prompt 2 / P17, which remains unauthorized.

## 2. Baseline

| Item | Value |
|---|---|
| Baseline commit | `fb4301e2315e49a04a354ff6431d524c7dafd71c` (`fix(p16r4): authorize PO-ratified validated -> calculated transition`) |
| Predecessor verdict | `P16_REMEDIATION_04_PARTIAL` |
| Working tree at start | `.gitignore` modified (pre-existing, **not** absorbed); untracked pre-existing docs and stray files `8`, `=` |
| Backend | healthy (200) on 8070 |
| State-machine contract | `mapped → validated → calculated`; reviewer `can_review` ≠ processor `can_process`; `mapped → calculated` prohibited (P16-R4, unchanged, **not** re-opened) |
| Known invalid result | snapshot `f60affde-ed51-4b23-b5b3-ac920927568e` / log `3c7229be-31ac-4d00-9e29-4ed2052c895d`, **319.536000 kg CO2e** |
| Known valid replacement | snapshot `dd5e4648-aa36-405b-b2d7-68ba21477b80` / log `67ae1d37-cc3b-4b2c-86c6-59797f49898b`, **113.791500 kg CO2e** |
| Test baseline | full `tests/unit` executed — see §18 |

## 3. Scope

In scope: RD-4/R9 (invalid-result lifecycle), R8 (FY2026 no-silent-fallback), RD-8/R12 (live cross-tenant),
R13 (remaining route tests), R11 (EV-01 fresh redrive), RD-5 workflow site, R14 (disposable integration),
full-suite classification, and re-evaluation of all P16 gates. Out of scope: everything in §12/§15 of the
brief (Scope 2, Scope 3 expansion, frameworks, assurance, reporting redesign, Step-3 UI, production, P17).

## 4. Safety boundary

* Production was **never** contacted; no production schema, RLS, users or credentials were touched.
* **No corpus, oracle, ground-truth, manifest or generator file was modified.**
* **No accounting row was manufactured with SQL.** The only SQL used was read-only inspection plus the
  authorized **schema migration** (§7).
* The F-046-1 disposable-harness invariant was **not** weakened; the destructive harness was never pointed at
  the canonical Demo Lab.
* Historical accounting values were never deleted, overwritten or hidden.

## 5. P16-R4 inherited evidence (distinguished from fresh)

**Inherited (not re-driven in this task):** `mapped → validated → calculated` live on all six canonical PDFs
(21 lines/21 snapshots/21 logs, supplier-attributed); RD-2 line-aware extraction/validation; RD-6 test
correction; RD-5 site-1 wiring; the P16-R4 route suite.

**Fresh in this task (see sections below):** the P16-R3 regression fix to the test fake; the RD-4 migration +
service + route; the full unit-suite execution and its classification; the reportability-aggregate reading.

**Still unverified:** RD-8 live cross-tenant, R8 FY2026, R11 EV-01, R14 disposable integration, route tests
F–I.

## 6. RD-4 investigation

Re-confirmed read-only before any change: `calculation_snapshots` and `emissions_logs` had **no** validity,
reportability or supersession column of any kind (28 columns on the snapshot, 31 on the log, none of them a
lifecycle state). Therefore:

* the invalid result could not be distinguished from a valid one by any machine-readable field;
* exclusion from reporting was a convention held in operators' heads, not a rule;
* `audit_trail` alone cannot gate a consumption boundary;
* `report_versions` lifecycle governs *reports*, not emission results — reusing it would be a domain error.

The consumption boundary was then located precisely: `backend/data/emissions_logs.py` (the period/scope/group/
supplier **SUM** aggregates that produce reported totals) and `backend/data/disclosure_projection.py` (the
disclosure/export projection). Per-row *inspection* reads were deliberately left unchanged, because §2/§12
require the invalid result to remain historically inspectable.

## 7. RD-4 implementation

Implemented (all fresh in this task):

| Artifact | Change |
|---|---|
| `supabase/migrations/20261008000000_p16r5_result_reportability_lifecycle.sql` | **new** — additive columns + CHECK constraints + indexes on both accounting tables |
| `backend/data/emissions_logs.py` | `invalidate_snapshot_result()` service method; reportability filter on the scope aggregate and the group aggregate |
| `backend/api/v3_emissions.py` | `InvalidateCalculationPayload` model + `POST /calculations/{snapshot_id}/invalidate` route |
| `backend/data/disclosure_projection.py` | reportability filter on the disclosure projection |

**Schema (minimum, additive only):** on **both** `calculation_snapshots` and `emissions_logs`:
`reportability_status text NOT NULL DEFAULT 'reportable'`, `invalidated_reason text`, `invalidated_by uuid`,
`invalidated_at timestamptz`, plus `superseded_by_snapshot_id` / `superseded_by_log_id`.

* CHECK `reportability_status IN ('reportable','not_for_reporting','superseded')`.
* CHECK enforcing the auditable contract: a non-reportable row **must** carry a non-blank reason, an actor
  and a timestamp — no state change without an audit record.
* Indexes on `(organization_id, reportability_status)`.
* No column, row, policy or existing index was modified or removed. Existing rows default to `'reportable'`,
  which is their historical meaning.

**Service:** `invalidate_snapshot_result()` marks the snapshot and its paired log(s) in one operation, records
reason/actor/timestamp, resolves and records the replacement log for a supersession, refuses an already
non-reportable result (idempotent), and **never** writes to any accounting value column.

**Route:** `POST /api/v3/emissions/calculations/{snapshot_id}/invalidate`, body
`{reason, status?, superseded_by_snapshot_id?}`; requires an authenticated org member, applies
`ensure_org_access` to the snapshot's own `organization_id`, and additionally refuses (422) a replacement
belonging to a different organisation. Maps `LookupError→409` and `ValueError→422`.

## 8. RD-4 verification

**Schema — verified live (fresh):** migration applied to `carbontally_demo_local` successfully (10 columns
created, constraints and indexes created). Readback confirms all 10 columns exist, and the historical values
are **unchanged**:

    dd5e4648-aa36-405b-b2d7-68ba21477b80 | 113.791500 | reportable   (historical meaning preserved)
    f60affde-ed51-4b23-b5b3-ac920927568e | 319.536000 | reportable   (historical meaning preserved)

**Route — verified registered (fresh):** the running backend's OpenAPI contains the `invalidate` path.

**Fail-closed behaviour — verified live (fresh):** every attempt from the available identities was refused
with **403 "Organization access denied"** by `ensure_org_access`, and **no state changed** — the readback
after the attempts still showed `status=reportable`, `reason_len=0`, `by=NULL`, `at=NULL`,
`superseded_by=NULL` for the invalid pair and `reportable` for the replacement. Correct refusal, but the
successful lifecycle transition was **not** demonstrated.

**Blocking detail (root cause, actionable):** the lifecycle route authorizes via the org-membership model
(`require_org_member` + `ensure_org_access`), whereas the accounting surfaces this decision concerns are
operated by *staff* actors. The local credentials file exposes 16 identities and **none** satisfied
`ensure_org_access` for the target organisation `3fd0f325-16a1-5b53-8fb8-27929cf218fa`, so the authorized
transition could not be executed. Reconciling the lifecycle route's authorization model with the actor model
that actually operates accounting (a staff reviewer with `can_review`, matching the `/ops` surfaces) is the
concrete next step. This was **not** resolved by loosening authorization — denial, not permission, was
preserved.

**Exclusion enforcement — implemented, aggregate path verified (fresh, read-only):** the reporting aggregate
API returns `{"total_co2e_kg": "6077.900240", "by_scope": {"Scope 1": "4175.903780", "Scope 3":
"1901.996460"}}`. Because the transition did not execute, the *before/after* exclusion difference could not be
observed; the predicate is compiled and in the code path, but its runtime effect is **unverified**.

**RD-4 verdict: NOT SATISFIED (partial implementation, live transition not demonstrated).** §2 items A, E, G
hold; B, C, D, F are **unverified**.

## 9. R8 FY2026 investigation

The frozen six-PDF corpus is FY2025-dated (confirmed again: every document resolved a `factor_set DEFRA-2025`,
`reporting_year 2025` factor), so the corpus cannot trigger the FY2026 branch — and it **must not** be modified
to do so. The existing FY2026 guard was located:

    api/v3_emissions.py:813
    if factor.reporting_year and factor.reporting_year != payload.reporting_year:
        raise HTTPException(422, "no {requested} factor available for this activity:
                                  selected factor is {factor.reporting_year}
                                  (reporting-year substitution is not permitted)")

This is the correct fail-closed behaviour (explicit 422 refusal, no substitution), and it is exercised by the
existing guard suite. No FY2026-dated fixture exists in the Demo Lab, so no **fresh** live document-level
FY2026 exercise was performed.

## 10. R8 verification

* Implementation evidence: the guard exists at `v3_emissions.py:813` and refuses rather than substitutes.
* Inherited evidence: the P16-R2 422 year-guard suite.
* **Fresh live evidence: NONE.** No FY2026 document was driven.
* **R8: UNVERIFIED** (guard present and correct in code; not freshly exercised).

## 11. RD-8 investigation

The cross-tenant guard for an extraction item is `_get_item_and_batch()` in `api/v3_operations.py`, which
resolves the item, loads its batch, and enforces pipeline authorization (403 when the actor's organisation does
not own the item's batch/organisation). Exercising it live requires an extraction item belonging to a **second**
organisation. Re-audited live: no Org-B extraction item exists in the Demo Lab, and §12/§30 forbid
manufacturing one with SQL.

## 12. RD-8 implementation

**NOT IMPLEMENTED.** No Org-B fixture was created. Creating one legitimately requires driving a second
organisation's upload→enqueue journey through the API, which was not reachable within this task's budget. No
accounting row was fabricated and no existing tenant data was mutated.

## 13. RD-8 verification

**NOT EXECUTED.** Consequently cross-tenant item→organisation **403**, "Org-B can access its own item", and
supplier/factor/source-item cross-tenant isolation all lack fresh live evidence. **No unexpected ALLOW was
observed** (nothing was executed that could produce one). **R12 PARTIAL.**

## 14. R11 EV-01 redrive

**NOT EXECUTED as a fresh run.** New identifiers for a fresh EV-01 calculation are **not** claimed.

One consistency observation from a **read-only aggregate** (not a redrive): the org's Scope 1 reportable total
reads `4175.903780`, which equals EV-01's expected total. That is inherited persisted data being aggregated —
it is **not** evidence of a fresh calculation and is **not** reported as a PASS. **R11 NOT SATISFIED.**

## 15. RD-5 workflow-site verification

`api/v3_processing_workflow.py:918` (`supplier_id=item.mapped_supplier_id`, added in P16-R4) remains
**compile-verified and pattern-consistent** with the already-wired `v3_operations.py` sites. It was **not**
separately driven live because that route's document-level calculate path was not exercised in this task. No
supplier attribution was invented; absent supplier still stays NULL.

The item-path invariant
`mapped_supplier_id → CalculationRequest.supplier_id → snapshot → emissions_logs.supplier_id` remains
live-verified from **P16-R4 (inherited, 21/21 rows attributed)**, not fresh here.

## 16. R13 route tests

**NOT EXTENDED.** The P16-R4 suite covers A (mapped→validated), B (validated→calculated), C
(mapped→calculated denied), D (reviewer cannot calculate), E (processor cannot validate), the transition-table
contract, and supplier/provenance. Cases **F** (cross-tenant source item), **G** (component-factor rejection),
**H** (scope mismatch), **I** (reporting-year mismatch) remain **uncovered**.

Identified while investigating (ready to implement): the G/H/I guards live in `api/v3_emissions.py:796–821`
(`is_component(factor)` → 422; `factor.scope != payload.scope` → 422;
`factor.reporting_year != payload.reporting_year` → 422), so route-level tests should target
`POST /api/v3/emissions/calculate` with a seeded component factor. **R13 PARTIAL.**

## 17. R14 disposable integration

**NOT EXECUTED.** The destructive harness (`TRUNCATE … RESTART IDENTITY CASCADE`) was **not** pointed at the
Demo Lab, and no disposable clone was created. The F-046-1 guard remains intact and was **not** weakened.

## 18. Full regression results

The full `tests/unit` suite ran to completion (fresh). **8 failures**, classified:

| # | Test | Classification | Action |
|---|---|---|---|
| 1 | `test_fin06_manual_processing_enforcement.py::…::test_automatic_enqueue_still_works_with_manual_processing_off` | **1 — caused by the P16 line of work**: P16-R3 added `find_item_by_file_id` to the repository and the API called it, but `tests/unit/api/fakes.py::MemoryManualExtraction` did not mirror it → `AttributeError` | **FIXED** — fake now mirrors it; test **passes** |
| 2 | `test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered` | **2 — pre-existing, unrelated** (asserts `/api/v3/admin/sla/settings` is registered; app exposes only `/api/v2/health`) | untouched |
| 3 | `test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered` | 2 — pre-existing (same cause) | untouched |
| 4 | `test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained` | 2 — pre-existing (same cause) | untouched |
| 5 | `test_d17_provider_ownership_migration_revision.py::…::test_migration_ordering_is_unchanged` | 2 — pre-existing (previously known) | untouched |
| 6–8 | `test_extraction_suggestions.py::{test_suggest_parses_clean_invoice, test_suggest_missing_fields_leave_unresolved, test_suggest_no_fabrication_on_garbage}` | 2 — pre-existing (previously known) | untouched |

**A/B proof:** reverting `backend/domain/partners.py` to its pre-P16-R4 content and re-running the four suspect
tests produced the **same four failures**, proving the state-machine change is not their cause. Fixing the fake
then made `test_fin06` pass while the three SLA failures persisted with an unrelated assertion
(`{'/api/v2/health'}`), confirming they are pre-existing registration issues.

Targeted suites green (fresh): `test_p16r4_core_accounting_state_machine.py` **7 passed**,
`test_v3_processing_workflow.py` **11 passed**, `test_extraction_fidelity.py` **35 passed**. No unrelated test
was modified to obtain green.

## 19. Security verification

| Check | Result |
|---|---|
| RD-4 lifecycle route registered and reachable | **yes** (OpenAPI) |
| RD-4 unauthorised/foreign access | **denied** — 403 "Organization access denied" (fail-closed preserved) |
| RD-4 no state change on denial | **confirmed** — readback unchanged after all attempts |
| RD-4 replacement from another organisation | refuses 422 + `ensure_org_access` (implementation evidence only) |
| cross-tenant item→org guard (RD-8) | **NOT EXECUTED** |
| `mapped → calculated` still prohibited | route test C → 409 (inherited; unchanged) |
| reviewer/processor separation | route tests D/E → 403 (inherited; unchanged) |
| no RLS policy changed | **confirmed** — migration is additive only |
| no unexpected ALLOW | none observed; denial preserved, never loosened |

## 20. Data integrity verification

* No production contact; no corpus/oracle/ground-truth modification (`git status` shows 0 such paths).
* No accounting row manufactured with SQL; the only DDL was the authorized migration.
* Historical values intact: `319.536000` and `113.791500` both unchanged after the migration.
* The invalid pair was **not** deleted, overwritten, hidden or repaired — still fully inspectable.
* Every attempted live state change used an authenticated API path (and was refused).

## 21. Canonical six-PDF status

All six frozen PDFs traversed upload → enqueue → extraction → clarify → map → reviewer validate → processor
calculate → snapshot → emissions in **P16-R4**, with 21 lines / 21 snapshots / 21 emissions logs, 21/21
supplier-attributed, total 1200.626760 kg CO2e. **This is inherited evidence**; the six-PDF journey was **not**
freshly re-driven in this task because R10 was already PASS and §1 says not to redo proven work unnecessarily.

## 22. Manual-review status

**Inherited** from P16-R4: the automatic pipeline fail-closed on the ambiguous 'Waste' activity to
`manual_review` with per-line reasons, the operator supplied the clarification, the resolved factor was recorded
with actor/`policy_input`/`factor_set`/`reporting_year`, and the item then advanced to `calculated`. Not
re-driven here.

## 23. Supplier status

**Inherited** from P16-R4: canonical supplier `Robinsons Recycling Services Ltd` read from the frozen document
(never fabricated into the master table), persisted as `mapped_supplier_id = 2fd4072c…` and reaching **21/21**
emissions rows with one identity and no duplicates. The RD-5 applicable site
(`v3_processing_workflow.py:918`) is wired but not separately live-driven (§15).

## 24. Factor-year status

**Inherited/implementation only.** FY2025 exact-year resolution is inherited-verified (all six documents bound
`factor_set DEFRA-2025`, `reporting_year 2025`, no substitution). The FY2026 no-substitution guard exists at
`api/v3_emissions.py:813` and refuses with 422 — **no fresh live FY2026 exercise** (§9/§10). No silent
substitution occurred anywhere.

## 25. Acceptance matrix

| Gate | Requirement | Evidence | Inherited / Fresh | Status |
|---|---|---|---|---|
| R1 | operator factor precedence | operator clarification selected DEFRA-2025 factor, `outcome_status=selected` | inherited (P16-R4 live) | **PASS** |
| R2 | factor safety | fail-closed on ambiguity; component/scope/year guards at `v3_emissions.py:796–821` | inherited live / fresh code-read | **PASS** |
| R3 | supplier propagation | 21/21 emissions rows attributed; RD-5 site-1 wired | inherited live / fresh compile | **PASS** |
| R4 | reviewer → processor workflow | `mapped→validated→calculated` both directions live; `mapped→calculated` 409 | inherited (P16-R4) | **PASS** |
| R5 | line-aware completeness | 6/6 docs completeness 1.0, 21 lines, 0 document-level findings | inherited (P16-R3/R4) | **PASS** |
| R6 | pipeline version consistency | fresh jobs `v3-auto-1.2`; RD-6 test asserts 1.2 vs 1.1 `!=` | inherited + **fresh test run (35 passed)** | **PASS** |
| R7 | FY2025 exact-year | factor year == document year on all six | inherited | **PASS** |
| R8 | FY2026 no silent fallback | guard exists (`v3_emissions.py:813`, 422 refusal) | **fresh: none** (no FY2026 fixture) | **UNVERIFIED** |
| R9 | invalid-result lifecycle | migration applied (10 cols + constraints + indexes); service + route implemented and registered; **transition not executed** (403 org-access for all available actors) | **fresh implementation; fresh live FAIL** | **FAIL** |
| R10 | six canonical PDFs | 21 lines/21 snapshots/21 logs end-to-end | inherited (P16-R4) | **PASS** |
| R11 | EV-01 fresh redrive | no fresh run; only a read-only aggregate coincidentally equal to the expected total | **fresh: none** | **FAIL** |
| R12 | tenant/security | RD-4 denial fail-closed + no state change; no unexpected ALLOW | **fresh (RD-4)** / cross-tenant not executed | **PARTIAL** |
| R13 | route-level regression | A–E + table + supplier covered; F–I uncovered | inherited (P16-R4) | **PARTIAL** |
| R14 | disposable integration | harness invariant preserved; no clone created | **fresh: not executed** | **FAIL** |

## 26. Remaining defects

1. **RD-4 lifecycle transition not live-executed.** The route refuses every available identity with
   **403 "Organization access denied"** (`ensure_org_access`, org-membership model) while the accounting
   surfaces are operated by *staff*. The lifecycle route's authorization model must be reconciled with the
   actor model that actually operates accounting (e.g. staff reviewer with `can_review`, as the `/ops` routes
   use). Then re-run the A–G demonstration. **R9.**
2. **RD-4 exclusion predicate runtime-unverified.** The reportability filter is compiled into the scope
   aggregate, the group aggregate and the disclosure projection, but its before/after effect could not be
   observed because (1) never ran. **R9.**
3. **RD-8 live cross-tenant still not executed** (no Org-B item; no SQL fabrication permitted). **R12.**
4. **R11 EV-01 not freshly re-driven** — no new identifiers claimed.
5. **R8 FY2026 not freshly exercised** (no FY2026-dated fixture; corpus immutable).
6. **R13 cases F–I still uncovered** (guards identified, tests not written).
7. **R14 disposable integration not executed** (no clone).
8. **Pre-existing failures** (7): `test_review_sla_surfaces` ×3 (SLA routes not registered) and
   `test_extraction_suggestions` ×3 + D17 migration-ordering ×1 — unrelated to P16, deliberately untouched.
9. `v3_processing_workflow.py:918` still lacks its own live route exercise.

## 27. Changed files

| File | Kind | Change |
|---|---|---|
| `supabase/migrations/20261008000000_p16r5_result_reportability_lifecycle.sql` | **migration (new)** | additive reportability lifecycle on both accounting tables |
| `backend/data/emissions_logs.py` | **product** | `invalidate_snapshot_result()`; reportability filter on scope + group aggregates |
| `backend/api/v3_emissions.py` | **product** | `InvalidateCalculationPayload` + `POST /calculations/{snapshot_id}/invalidate` |
| `backend/data/disclosure_projection.py` | **product** | reportability filter on the disclosure projection |
| `backend/tests/unit/api/fakes.py` | **test** | `MemoryManualExtraction.find_item_by_file_id` mirror (fixes the Class-A regression) |
| `tools/demo_lab/p16r5_rd4_lifecycle.py` | **harness (new)** | RD-4 A–G live demonstration |
| `docs/architecture/CT-PO-P16-REMEDIATION-05-FINAL-P16-ACCEPTANCE-CLOSURE-20260925.md` | **docs (new)** | this report |

No corpus, oracle, ground-truth, manifest or generator file changed. `.gitignore` (pre-existing modification)
was **not** absorbed. No unrelated refactor.

## 28. Migration / schema impact

One migration, additive only, applied to `carbontally_demo_local`:

* **10 new columns** (5 on `calculation_snapshots`, 5 on `emissions_logs`), all nullable except
  `reportability_status` (NOT NULL DEFAULT `'reportable'`).
* **4 CHECK constraints** (2 status-enum, 2 auditable-invalidation).
* **2 indexes** on `(organization_id, reportability_status)`.
* **2 column comments.**
* **No** column dropped/renamed/retyped, **no** row modified, **no** RLS policy changed, **no** existing index
  altered. All pre-existing rows keep `'reportable'`, i.e. their historical meaning.

## 29. Test commands

    cd backend && .venv/bin/python -m pytest tests/unit -q -p no:warnings
    cd backend && .venv/bin/python -m pytest tests/unit/api/test_p16r4_core_accounting_state_machine.py -q
    cd backend && .venv/bin/python -m pytest tests/unit/api/test_v3_processing_workflow.py -q
    cd backend && .venv/bin/python -m pytest tests/unit/services/test_extraction_fidelity.py -q
    cd backend && .venv/bin/python -m pytest tests/unit/api/test_review_sla_surfaces.py -q   # pre-existing fails

    # RD-4 live demonstration (A–G)
    python3 tools/demo_lab/p16r5_rd4_lifecycle.py

    # apply the migration (Demo Lab only)
    PGPASSWORD=postgres psql -h 127.0.0.1 -p 54426 -U postgres -d carbontally_demo_local \
      -v ON_ERROR_STOP=1 -f supabase/migrations/20261008000000_p16r5_result_reportability_lifecycle.sql

    # restart the release backend after a product-code change
    cd backend && pkill -f 'uvicorn main:app --host 127.0.0.1 --port 8070'; sleep 3
    (set -a; . $HOME/ct_local_env/demo_lab/backend.env; set +a; \
      nohup .venv/bin/uvicorn main:app --host 127.0.0.1 --port 8070 > /tmp/p16r5_backend.log 2>&1 &)

## 30. Evidence identifiers

| Item | Identifier |
|---|---|
| Invalid snapshot / log | `f60affde-ed51-4b23-b5b3-ac920927568e` / `3c7229be-31ac-4d00-9e29-4ed2052c895d` (319.536000) |
| Valid replacement snapshot / log | `dd5e4648-aa36-405b-b2d7-68ba21477b80` / `67ae1d37-cc3b-4b2c-86c6-59797f49898b` (113.791500) |
| Target organisation | `3fd0f325-16a1-5b53-8fb8-27929cf218fa` |
| Aggregate read (fresh) | `total_co2e_kg=6077.900240`; Scope 1 `4175.903780`; Scope 3 `1901.996460` |
| Reportability census (fresh) | `reportable n=28 sum=6077.900240` |
| Lifecycle route | `POST /api/v3/emissions/calculations/{snapshot_id}/invalidate` (present in OpenAPI) |
| Baseline commit | `fb4301e2315e49a04a354ff6431d524c7dafd71c` |

## 31. Reproducibility

Credentials remain outside the repository (`$HOME/ct_local_env/demo_lab/credentials.local.json`, mode 0600) and
are never printed. Every command in §29 is runnable from `/home/shomonrobie/ct_93d5cdd`. RD-8, R11, R14,
R8-live and R13 F–I have **no** reproduction commands because they were not executed.

## 32. Risks and limitations

* **Authorization-model mismatch** is the operational blocker for R9: the lifecycle route uses org-membership
  authorization while accounting is staff-operated. Until reconciled, the invalid result cannot be moved out of
  reporting through the application, so reporting totals still include `319.536000` (conventionally, not
  mechanically, excluded).
* The reportability filters cover the **aggregation/disclosure** boundary only; per-row inspection reads
  intentionally still return non-reportable rows (required for historical inspectability). Any consumer added
  later must apply the same predicate.
* FY2026 policy remains code-verified but not live-exercised; the immutable corpus cannot test it.
* R14 and RD-8 remain unexecuted, so tenant isolation has no fresh negative-execution evidence.
* The `ensure_org_access` 403 was treated as correct fail-closed behaviour; it was **not** bypassed, and no
  authorization was loosened to force a PASS.

## 33. PASS/FAIL scorecard

**Mandatory-for-PASS items (§12):** R8 evidence — **NO**; R9 PASS — **NO**; R11 fresh redrive — **NO**;
R12 live cross-tenant — **NO**; R13 complete — **NO**; R14 executed — **NO**; full regression classified —
**YES**.

**Gates PASS (8):** R1, R2, R3, R4, R5, R6, R7, R10.
**PARTIAL (2):** R12, R13.
**FAIL (3):** R9, R11, R14.
**UNVERIFIED (1):** R8.

**Any mandatory gate open → no PASS.**

## 34. PO authorization recommendation

**"Has P16 now satisfied its acceptance contract sufficiently to make Prompt 2 eligible for a new PO
authorization?"**

**NO.**

Six mandatory gates remain open (R8, R9, R11, R12-live, R13, R14). The state-machine contract is settled and
implemented, the core journey works on the happy path, and the RD-4 schema and route now exist — but the
invalid-result lifecycle is not yet operable through the application, and four gates (cross-tenant, EV-01,
FY2026, disposable integration) still have no fresh evidence.

**No new PO decision is required** for the remaining work: it is authorization-model reconciliation plus
execution of already-authorized gates. **P17 / Prompt 2 is NOT eligible and must not be started.**

## 35. Final verdict

**P16_REMEDIATION_05_PARTIAL**

**Genuinely closed this task:**
* the invalid-result lifecycle **infrastructure** — migration created and applied (10 columns, 4 CHECK
  constraints, 2 indexes, both accounting tables), `invalidate_snapshot_result()` service, authenticated
  `POST /api/v3/emissions/calculations/{snapshot_id}/invalidate` route registered in the running app, and
  reportability gating on the reporting aggregation and disclosure boundary;
* the **Class-A regression** introduced by the P16 line of work — the test fake now mirrors
  `find_item_by_file_id`, and `test_fin06_…automatic_enqueue_still_works_…` passes;
* a complete, classified **full-suite** result (8 failures: 1 caused-by-P16 → fixed; 7 pre-existing).

**Genuinely not closed:** the live RD-4 transition (403 authorization-model mismatch), R9's consumption
enforcement runtime effect, RD-8 live cross-tenant, R8 FY2026, R11 EV-01, R13 cases F–I, R14 disposable
integration.

No corpus/oracle change, no production activity, no SQL-manufactured accounting rows, no weakened RLS, no
loosened authorization, no fabricated PASS. P17 / Prompt 2 was **not** started. **STOP.**
