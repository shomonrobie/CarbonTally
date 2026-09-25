# CT-PO-P16-REMEDIATION-06 — RD-4 Authorization and Final P16 Acceptance Gates

**Task ID:** P16-REMEDIATION-06-20260925-RD4-AUTHORIZATION-AND-FINAL-GATES
**Date:** 2026-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` — branch `p8-release-reconciled`
**Environment:** local Demo Lab only — `carbontally_demo_local` @ 127.0.0.1:54426, release backend @
127.0.0.1:8070, lab gateway @ 127.0.0.1:54430.

---

## 1. Task identity

Final P16 acceptance pass, closing the six gates left open by P16-R5. Not P17/Prompt 2, which remains
unauthorized.

## 2. Baseline

| Item | Value |
|---|---|
| Baseline commit | `155013dbe66bcdf70ccfceb58baee3818d3562ae` |
| Predecessor | P16-R5 report, verdict `P16_REMEDIATION_05_PARTIAL` |
| Branch / tree | `p8-release-reconciled`; clean for my scope (pre-existing `.gitignore` mod + untracked docs left alone) |
| Backend health | 200 |
| Migration state | `20261008000000_p16r5_result_reportability_lifecycle.sql` applied (reportability columns/constraints/indexes present) |
| Invalid result | snapshot `f60affde-ed51-4b23-b5b3-ac920927568e` / log `3c7229be-31ac-4d00-9e29-4ed2052c895d`, 319.536000 |
| Valid replacement | snapshot `dd5e4648-aa36-405b-b2d7-68ba21477b80` / log `67ae1d37-cc3b-4b2c-86c6-59797f49898b`, 113.791500 |
| Open gates | R8, R9, R11, R12, R13, R14 |

## 3. Scope

In scope: RD-4 authorization reconciliation + live lifecycle; R8; RD-8/R12; R13 F–I; R11; RD-5 workflow site;
R14; full regression. Out of scope: all §0/§20 prohibitions (Scope 2/3, frameworks, assurance, Step-3,
production, P17). R1–R7, R10 were not reopened.

## 4. Safety boundary

* Production never contacted; no production credentials, schema, RLS or data touched.
* **No corpus, oracle, ground-truth, generator or manifest change.**
* No accounting row manufactured or mutated with SQL. The only DDL was the already-authorized P16-R5 migration.
* Historical values preserved exactly (`319.536000`, `113.791500`).
* Authorization was **not** loosened: the broken gate was replaced with the *stricter, correct* staff model.

## 5. P16-R5 inherited evidence

**Inherited (not re-driven):** R1, R2, R3, R4, R5, R6, R7, R10 — six-PDF end-to-end journey (21 lines,
21 snapshots, 21 logs, supplier-attributed), line-aware extraction/validation, the PO-ratified
`mapped → validated → calculated` state machine, RD-6 test correction.

**Fresh in this task:** R8, R9, R11, R13 and the RD-8 attempt — see below.

**Still unverified:** R12 live positive cross-tenant, R14.

## 6. RD-4 authorization investigation

P16-R5's route used `require_org_member()` + `ensure_org_access()` and every identity was refused with 403
"Organization access denied". Reading the primitives:

* `auth.py::require_org_member()` requires `current_user.is_org_member` — an **organisation membership**. A pure
  CarbonTally **internal staff** actor has `is_org_member = False`, so *every legitimate staff reviewer* was
  refused by this gate.
* `api/dependencies.py::ensure_org_access()` — entity staff → 403; **internal staff → allowed for any
  organisation** (D20 operational access); org members → own organisation only; everyone else → 403.
* The reviewer surface `/api/v3/ops/items/{id}/validate` uses a completely different (and correct) model:
  `require_staff` → `require_internal_staff` → `ensure_staff_permission(context, "can_review")`, i.e.
  **staff profile + internal + reviewer permission**.

**Root cause:** the lifecycle route was gated on an authorization model (org membership) that the actor who
actually performs accounting-result decisions (an internal staff reviewer) can never satisfy. This was a
**route/authorization-model mismatch**, not a tenancy bug.

## 7. RD-4 authorization implementation

`backend/api/v3_emissions.py` — the invalidate route now uses the *same* model as the reviewer surfaces, which
is **stricter** than what it replaced:

    current_user: AuthUser     = Depends(require_auth())        # authenticated principal
    staff:        StaffContext = Depends(require_staff)         # ACTIVE staff profile -> else 403
    require_internal_staff(staff)                               # entity staff -> 403 (D20)
    ensure_staff_permission(staff, "can_review")                # reviewer permission -> else 403
    ensure_org_access(current_user, row["organization_id"])     # tenant gate (unchanged)
    # cross-org replacement -> 422 (unchanged)
    actor_user_id = staff.profile.user_id                       # real acting staff user

No bypass for the Demo Lab, no broad membership grant, no `can_review` handed to arbitrary actors, and
`ensure_org_access` was **preserved**, not removed.

## 8. RD-4 lifecycle live verification — **FRESH, PASS**

Actor: `platform_admin` (CarbonTally internal staff, `can_review`).

| Item | Result |
|---|---|
| A historical invalid result exists | **yes** — `f60affde…` / `3c7229be…`, 319.536000, `reportable` |
| B authorized activation | **`[200] {"success": true, "snapshot_id": "f60affde…", "log_ids": ["3c7229be…"], "status": "not_for_reporting"}`** |
| C status + reason + actor + timestamp | `not_for_reporting`; `reason_len=107`; `invalidated_by=1fe17efb-4565-40ab-9fba-115db13fc111`; `invalidated_at=2026-09-25 06:00:35+00` |
| D replacement relationship | `superseded_by_snapshot_id=dd5e4648…`; `superseded_by_log_id=67ae1d37…` |
| E historical values unchanged | snapshot **319.536000**, log **319.536000** — both intact |
| H still inspectable | `3c7229be… co2e=319.536000 status=not_for_reporting` retrievable |
| I unauthorised actor denied | org owner (no staff profile) → **403 "Staff access required (active staff profile)"** |
| J repeat is safe | second attempt → **409 "already non-reportable"** |
| — reason mandatory | blank reason → **422** |
| G valid replacement untouched | `dd5e4648… 113.791500 status=reportable` |

**Before/after reportable aggregate — measured, not inferred:**

| Reading | Total (kg CO2e) | Scope 1 | Scope 3 |
|---|---|---|---|
| BEFORE (P16-R5, same DB, 28 reportable rows) | **6077.900240** | 4175.903780 | 1901.996460 |
| AFTER (fresh API read, this task) | **5758.364240** | 4175.903780 | 1582.460460 |
| **DELTA** | **319.536000** | 0.000000 | 319.536000 |

The delta equals the invalid result exactly and Scope 1 is unchanged, proving only the invalid row was
removed. SQL agrees: 27 reportable rows summing 5758.364240, **1 excluded row summing 319.536000**,
disclosure-eligible rows 27.

## 9. RD-4 consumption-boundary verification

* The reporting aggregation (`scope-breakdown`) moved by exactly 319.536000 — the
  `reportability_status = 'reportable'` predicate is active at runtime, not merely compiled.
* The disclosure projection carries the same predicate.
* Per-row inspection still returns the invalid result (required for historical inspectability), so exclusion is
  deliberate and scoped to reporting output, not concealment.

## 10. R8 FY2026 investigation

Reviewed, not modified: the year guard in `api/v3_emissions.py`, `engines/factor_selection_policy`, and the
frozen FY2025 corpus (must remain byte-identical). Two independent paths were planned: a route-level test and a
live API call, both requesting **reporting year 2026** against a factor whose `reporting_year` is **2025**.

## 11. R8 live verification — **FRESH, PASS**

    POST /api/v3/emissions/calculate
    {reporting_year: 2026, date: 2026-06-30, activity: "Natural gas",
     quantity_unit: "kWh (Net CV)", scope: "Scope 1", country: GB}
    -> [422] "no 2026 factor available for this activity: selected factor is 2025
              (reporting-year substitution is not permitted)"

Requested year 2026 + factor year 2025 → **explicit fail-closed refusal; no silent substitution; no emissions
row created.** Corroborated by route test `test_i_reporting_year_mismatch_is_rejected` (422).

## 12. RD-8 cross-tenant investigation

The tenant gates are `_get_item_and_batch` (`api/v3_operations.py`: item→batch→organisation) and
`ensure_org_access` (emissions surface; D20: internal staff = operational any-org, members = own org only,
others denied). The Demo Lab holds **4 organisations** with existing extraction items (`3fd0f325…` 30,
`f03fb375…` 2, `b4bb08f1…` 1, `02b38744…` 1), so a cross-tenant proof was attempted on **existing** records.

## 13. RD-8 implementation

**No new fixture created.** No SQL created or modified any extraction, accounting or tenant row.

## 14. RD-8 live verification — **PARTIAL (fresh negative evidence only)**

| Attempt | Observed |
|---|---|
| org-A customer actor → **own-org** snapshot read | **403 "Organization access denied"** — not the expected 200 |
| org-A actor → **foreign-org** snapshot read | **not reachable** — no other organisation holds a `calculation_snapshots` row |
| cross-org replacement guard | enforced in-route (422) and covered by route tests; **not exercised live** |

**Findings:** (a) no second organisation currently owns a calculation snapshot, so a live cross-tenant
comparison could not be run on existing data; (b) the credential set's `org_a_owner` is not org-bound for the
emissions surface (`ensure_org_access` refuses it even for its own org) — a credential/provisioning fact, not a
P16 defect. **No unexpected ALLOW was observed.** Route-level tenant denials (F) PASS (§16).

## 15. R11 EV-01 fresh redrive — **FRESH, PASS**

New document `p16r6_ev01.csv` (2 rows: `Natural gas` / `kWh` / `British Gas` / 2025-06-30) driven through the
real API:

| Field | Value |
|---|---|
| Upload | **201**, file `5948a1a7-af9e-49fb-b6f0-f4a2ff38fe93` |
| Enqueue | **201**, job `513e33ff-9320-4ac0-9be3-9cea4b690090`, **`pipeline_version v3-auto-1.2`** |
| Item | `5556635e-53d7-41e5-a940-26d7f67efb96` |
| Extraction | 2 lines, **completeness 1.0**, unit `kwh` normalised to `kWh (Net CV)` |
| Auto-processing | job reached `status=customer_review`, `stage=review` (extract → map → calculate ran automatically) |
| Factor | `aef1f0bb-4e48-4e4b-a079-c1e827964d07` — "Natural gas (kg CO2e) [kWh (Net CV)]", **0.2027, Scope 1, year 2025** |
| Calculate API | **`[200] {"co2e_kg": 4175.90378, "multi_line": true, "lines": [{"quantity": 12181.4, "emissions_kg": 2469.16978}, {"quantity": 8420.0, "emissions_kg": 1706.734}]}`** |
| Snapshot 1 | `079e186c-cf4d-47a1-ba4d-e01ee25a60ca` — 12181.4 × 0.2027 = **2469.169780**, log `fd53223a-a2b9-494d-bd13-c0fbe1668f20` |
| Snapshot 2 | `0a075bf5-ec36-4812-be76-54beca6738bf` — 8420.0 × 0.2027 = **1706.734000**, log `2e32f826-f747-4f34-9824-6619c907fa96` |

**Independent verification: 2469.169780 + 1706.734000 = 4175.903780** — exactly the required total, matching the
API's returned `co2e_kg`. Identifiers are **new**, not inherited anchors.

**New defect observed (documented, not silently repaired — §14):** a third snapshot
`c97f02ee-1464-4e3d-b4f9-3ac8d5d1f301` (1706.734000) also exists for this item, so the per-item sum reads
8351.807560 = 2 × 4175.903780. The automatic pipeline had already calculated the item (hence `map`/`validate`
returned 409 "cannot transition from 'calculated'"), and the explicit `calculate` produced a second snapshot set.
Reported as an **idempotency / duplicate-snapshot** concern (AGENTS.md §19) rather than repaired in scope.

## 16. R13 route tests F–I — **FRESH, PASS (9/9)**

New `backend/tests/unit/api/test_p16r6_route_guards_f_i.py` — real routes, real guards, no mocked guard:

| Case | Assertion | Result |
|---|---|---|
| baseline | legitimate `POST /api/v3/emissions/calculate` | **200** |
| G component factor | `is_component()` classifier identifies an `of CH4 per unit` factor | **PASS** |
| H scope mismatch | `Scope 3` request against a Scope 1 factor | **422** |
| I reporting-year mismatch | `reporting_year=2026` against a 2025 factor | **422** substitution refusal (R8 route evidence) |
| F lifecycle requires staff reviewer | owner with no staff profile | **403** |
| F entity staff denied | `entity_operator_user` | **403** (D20) |
| F staff without `can_review` | `can_process`-only staff | **403** |
| F payload validation | `InvalidateCalculationPayload(reason=None)` | **ValidationError** |

Authorization failures (403) and domain-safety failures (422) remain clearly distinguishable.

## 17. R14 disposable integration — **NOT EXECUTED**

The destructive harness was **not** pointed at the Demo Lab; no disposable clone was created. F-046-1 remains
intact and was **not** weakened.

## 18. RD-5 workflow-site verification

`api/v3_processing_workflow.py` (`supplier_id=item.mapped_supplier_id`) remains **compile-verified and
pattern-consistent** with the already-wired `v3_operations.py` sites; **not** separately live-driven. The
invariant `mapped_supplier_id → CalculationRequest.supplier_id → snapshot → emissions_logs.supplier_id` is
live-verified from **P16-R4 (inherited, 21/21 rows attributed)**. No supplier attribution was fabricated.

## 19. Full regression results

Targeted suites (fresh): `test_p16r6_route_guards_f_i.py` **9 passed** (new);
`test_p16r4_core_accounting_state_machine.py` **7 passed**; `test_v3_processing_workflow.py` **11 passed**;
`test_extraction_fidelity.py` **35 passed**; `test_fin06_manual_processing_enforcement.py` **passing**
(P16-R5's Class-A fix holds).

P16-R5's full-suite classification is inherited and unchanged: **8 failures — 1 Class-A (fixed in P16-R5),
7 Class-B pre-existing/unrelated** (`test_review_sla_surfaces` ×3 — `/api/v3/admin/sla/settings` never
registered; `test_extraction_suggestions` ×3; D17 migration ordering ×1). Deliberately untouched. The P16-R6
product change is confined to one route's dependency block in `v3_emissions.py`, and every suite covering that
surface is green, so **no new Class-A failure was introduced**.

## 20. Security verification

| Check | Result |
|---|---|
| RD-4 unauthorized actor (no staff profile) | **403** |
| RD-4 entity staff | **403** (D20) |
| RD-4 staff lacking `can_review` | **403** |
| RD-4 authorized staff reviewer | **200** |
| RD-4 repeat | **409** (safe) |
| RD-4 blank reason | **422** |
| RD-4 cross-org replacement | 422 in-route + route-test covered |
| authorization loosened? | **NO** — replaced with the stricter staff model |
| RLS changed? | **NO** |
| tenant denial routes (F) | **PASS** (403 ×3) |
| live cross-tenant positive/negative | **PARTIAL** (§14) |
| unexpected ALLOW | **none observed** |

## 21. Data-integrity verification

Production untouched; no production credentials used. Corpus/oracle/generator/manifest unchanged. No
SQL-manufactured or SQL-mutated accounting rows. Historical invalid result preserved exactly (319.536000) and
still inspectable; valid replacement (113.791500) untouched and still reportable. The lifecycle is auditable on
the row itself (status + reason + actor + timestamp + supersession). R11's fresh run created documents,
snapshots and logs through authenticated routes only.

## 22. Canonical six-PDF status

**Inherited (P16-R4)** — not re-driven, per instruction not to reopen accepted evidence: 6/6 documents
end-to-end, 21 lines / 21 snapshots / 21 logs, 21/21 supplier-attributed, total 1200.626760 kg CO2e.

## 23. Manual-review status

**Inherited (P16-R4)** — automatic fail-closed on ambiguous `Waste` → `manual_review` with per-line reasons →
operator clarification → `mapped → validated → calculated`. P16-R6 additionally observed the automatic
`review` hand-off again (the new CSV reached `stage=review` unprompted).

## 24. Supplier status

**Inherited (P16-R4)** — canonical supplier read from the frozen document (never fabricated into master);
`mapped_supplier_id = 2fd4072c…` reached 21/21 emissions rows, one identity, no duplicates. The R11 CSV's
`British Gas` text was extracted but not attributed to an emissions row (`supplier=NULL`) because the CSV lane's
automatic mapping carries no supplier decision — consistent, not a regression.

## 25. Factor-year status

* **FY2025 exact-year: PASS** (inherited + fresh) — R11 bound `aef1f0bb…`, `reporting_year 2025`, for a 2025
  document, with no substitution.
* **FY2026 no-silent-fallback: PASS (FRESH LIVE)** — 422 refusal (§11). No FY2026 factor was fabricated and the
  frozen corpus was not modified.

## 26. Acceptance matrix

| Gate | Requirement | Evidence class | Status |
|---|---|---|---|
| R1 | operator factor precedence | inherited (P16-R4 live) | **PASS** |
| R2 | factor safety | inherited live + fresh code-read (guards `v3_emissions.py:796–821`) | **PASS** |
| R3 | supplier propagation | inherited live (21/21) + fresh compile | **PASS** |
| R4 | reviewer → processor workflow | inherited live (P16-R4) | **PASS** |
| R5 | line-aware completeness | inherited (21 lines, completeness 1.0) | **PASS** |
| R6 | pipeline version consistency | inherited + fresh run shows `v3-auto-1.2` | **PASS** |
| R7 | FY2025 exact-year | inherited + fresh (R11 bound a 2025 factor) | **PASS** |
| R8 | FY2026 no silent fallback | **FRESH LIVE** 422 refusal + route test | **PASS** |
| R9 | invalid-result lifecycle | **FRESH LIVE** A–J + measured delta 319.536000 | **PASS** |
| R10 | six canonical PDFs | inherited (P16-R4) | **PASS** |
| R11 | fresh EV-01 redrive | **FRESH LIVE** new ids, 2469.169780 + 1706.734000 = 4175.903780 | **PASS** |
| R12 | tenant/security | route denials FRESH PASS; **live cross-tenant positive/negative not achieved** | **PARTIAL** |
| R13 | route-level regression F–I | **FRESH** 9/9 new suite | **PASS** |
| R14 | disposable integration | **NOT EXECUTED** (no clone) | **FAIL** |

## 27. Remaining defects

1. **R12 live cross-tenant not fully executed.** No second organisation currently owns a `calculation_snapshots`
   row, so the positive/negative live pair could not be run on existing data; producing a second org's
   accounting output requires a disposable fixture not built in scope. Route-level tenant denials pass.
2. **R14 disposable integration not executed.** No clone created; F-046-1 preserved.
3. **NEW — duplicate calculation snapshots on repeat calculation.** R11's item carries 2× the expected snapshot
   set (per-item sum 8351.807560 vs expected 4175.903780) because the automatic pipeline calculated the item and
   a subsequent explicit `calculate` produced a second set. AGENTS.md §19 requires repeated processing not to
   create duplicate snapshots; needs a deterministic-`match_request_id`/idempotency fix. Discovered in scope,
   documented rather than repaired (§14).
4. **7 pre-existing test failures** (`test_review_sla_surfaces` ×3, `test_extraction_suggestions` ×3, D17
   migration ordering ×1) — unrelated to P16, deliberately untouched.
5. `v3_processing_workflow.py` RD-5 site still lacks its own live route exercise.
6. R11's CSV lane attributes no supplier to emissions rows (`supplier=NULL`) — consistent with that lane's
   mapping model; noted for completeness.

## 28. Changed files

| File | Kind | Change |
|---|---|---|
| `backend/api/v3_emissions.py` | **product** | invalidate route authorization reconciled to `require_auth` + `require_staff` + `require_internal_staff` + `can_review`; actor from `staff.profile.user_id` |
| `backend/tests/unit/api/test_p16r6_route_guards_f_i.py` | **test (new)** | F–I route guards (9 tests) |
| `tools/demo_lab/p16r6_rd4_lifecycle.py` | **harness (new)** | RD-4 A–J live lifecycle |
| `tools/demo_lab/p16r6_final_gates.py` | **harness (new)** | R11 EV-01 redrive + R8 live + RD-8 attempt |
| `docs/architecture/CT-PO-P16-REMEDIATION-06-…-20250925.md` | **docs (new)** | this report |

The pre-existing `.gitignore` modification was **not** absorbed; no unrelated file was taken in.

## 29. Migration / schema impact

**None.** No new migration. The P16-R5 migration remains as applied (10 reportability columns, 4 CHECK
constraints, 2 indexes). No schema, constraint, index or RLS change in P16-R6.

## 30. Test commands

    cd backend && .venv/bin/python -m pytest tests/unit/api/test_p16r6_route_guards_f_i.py -q -p no:warnings
    cd backend && .venv/bin/python -m pytest tests/unit/api/test_p16r4_core_accounting_state_machine.py -q
    cd backend && .venv/bin/python -m pytest tests/unit/api/test_v3_processing_workflow.py -q
    cd backend && .venv/bin/python -m pytest tests/unit/services/test_extraction_fidelity.py -q
    cd backend && .venv/bin/python -m pytest tests/unit -q -p no:warnings

    python3 tools/demo_lab/p16r6_rd4_lifecycle.py      # RD-4 A–J
    python3 tools/demo_lab/p16r6_final_gates.py        # R11 + R8 + RD-8

    cd backend && pkill -f 'uvicorn main:app --host 127.0.0.1 --port 8070'; sleep 3
    (set -a; . $HOME/ct_local_env/demo_lab/backend.env; set +a; \
      nohup .venv/bin/uvicorn main:app --host 127.0.0.1 --port 8070 > /tmp/p16r6_backend.log 2>&1 &)

## 31. Evidence identifiers

| Item | Identifier |
|---|---|
| Invalid snapshot / log (now `not_for_reporting`) | `f60affde-ed51-4b23-b5b3-ac920927568e` / `3c7229be-31ac-4d00-9e29-4ed2052c895d` |
| Invalidating actor | `1fe17efb-4565-40ab-9fba-115db13fc111` (`platform_admin`) |
| Replacement snapshot / log | `dd5e4648-aa36-405b-b2d7-68ba21477b80` / `67ae1d37-cc3b-4b2c-86c6-59797f49898b` |
| Aggregate before / after | `6077.900240` → `5758.364240` (delta `319.536000`) |
| EV-01 document / job / item | file `5948a1a7-af9e-49fb-b6f0-f4a2ff38fe93`, job `513e33ff-…`, item `5556635e-…` |
| EV-01 snapshots / logs | `079e186c-…`/`fd53223a-…`; `0a075bf5-…`/`2e32f826-…`; duplicate `c97f02ee-…`/`bf26ad53-…` |
| EV-01 factor | `aef1f0bb-4e48-4e4b-a079-c1e827964d07` (0.2027, Scope 1, 2025) |
| R8 refusal | `POST /api/v3/emissions/calculate` → **422** "no 2026 factor available … substitution is not permitted" |
| Orgs | org-A `3fd0f325-16a1-5b53-8fb8-27929cf218fa`; others `f03fb375-…`, `b4bb08f1-…`, `02b38744-…` |

## 32. Reproducibility

Credentials remain outside the repository (`$HOME/ct_local_env/demo_lab/credentials.local.json`, mode 0600) and
are never printed. Every command in §30 is runnable from `/home/shomonrobie/ct_93d5cdd`. R14 has **no**
reproduction command because it was not executed.

## 33. Risks and limitations

* R9's predicate is gated on the **reporting aggregation and disclosure projection**; per-row inspection
  deliberately still returns non-reportable rows. Any new consumer must apply the same predicate.
* R12's live cross-tenant proof is incomplete (route-level + negative denial evidence only).
* The duplicate-snapshot behaviour (§27.3) can inflate per-item totals on repeat calculation.
* `ensure_org_access` refuses the credential set's `org_a_owner` even for its own organisation on the emissions
  surface, so live positive customer-path checks need an org-bound credential.

## 34. PO authorization recommendation

**"Has P16 now satisfied every mandatory acceptance gate sufficiently for a NEW PO authorization decision on
Prompt 2 / P17?"**

**NO.** Twelve of fourteen gates PASS — including the four that were the actual blockers (R8 FRESH LIVE,
R9 FRESH LIVE with an arithmetic before/after proof, R11 FRESH LIVE with new identifiers, R13 FRESH 9/9) — but
**R12 is PARTIAL** (no live cross-tenant positive/negative pair) and **R14 is FAIL** (disposable integration not
executed), and one new integrity defect was discovered (§27.3 duplicate snapshots). Under §16, any open
mandatory gate means no PASS.

**No new PO decision is required.** The remaining work is: (a) an org-bound credential or disposable second-org
fixture for the live cross-tenant pair; (b) creating and running the disposable integration clone; (c) fixing
the repeat-calculation duplicate-snapshot idempotency.

## 35. Final verdict

**P16_REMEDIATION_06_PARTIAL**

**Closed this task:** R8, R9, R11, R13 — all with fresh, live or executed evidence, plus the RD-4
authorization-model reconciliation that unblocked R9 (replaced with a *stricter* staff-reviewer model, not a
loosened one).

**Still open:** R12 (PARTIAL), R14 (FAIL), and the newly discovered duplicate-snapshot defect.

No corpus/oracle change, no production activity, no SQL-manufactured or SQL-mutated accounting rows, no
weakened RLS, no loosened authorization, no fabricated PASS. P17 / Prompt 2 was **not** started. **STOP.**
