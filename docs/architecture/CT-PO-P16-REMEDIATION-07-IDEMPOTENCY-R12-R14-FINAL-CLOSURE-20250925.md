# CT-PO-P16-REMEDIATION-07 — Calculation Idempotency, Cross-Tenant and Disposable Integration Closure

**Task ID:** P16-REMEDIATION-07-20260925-IDEMPOTENCY-R12-R14-FINAL-CLOSURE
**Date:** 2026-09-25
**Repository:** `/home/shomonrobie/ct_93d5cdd` — branch `p8-release-reconciled`
**Environment:** local Demo Lab only — `carbontally_demo_local` @ 127.0.0.1:54426, release backend @
127.0.0.1:8070, lab gateway @ 127.0.0.1:54430.

---

## 1. Task identity

Final P16 closure: calculation idempotency/integrity, R12 cross-tenant verification, R14 disposable
integration, then the P16 acceptance decision. Not P17/Prompt 2 (remains unauthorized).

## 2. Baseline

| Item | Value |
|---|---|
| Baseline commit | `1e100233c99b5136f5bb65f429934135d806991d` (`fix(p16): close final acceptance gates`) |
| Predecessor verdict | `P16_REMEDIATION_06_PARTIAL` |
| Branch / tree | `p8-release-reconciled`; clean for my scope (pre-existing `.gitignore` mod not absorbed) |
| Backend health | 200 |
| Migrations applied | `20261008000000` (reportability lifecycle) + **new** `20261009000000` (request-id idempotency) |
| Demo Lab | 4 organisations; 34 snapshots at start |

## 3. Scope

Idempotency defect, R12, R14, the affected regression suites, and the final acceptance decision. R1–R11 and
R13 were **not** reopened (§2/§21).

## 4. Safety boundary

Production never contacted. No corpus/oracle/generator/manifest change. No RLS or authorization weakening.
No SQL-manufactured or SQL-mutated accounting rows — every accounting state change used an authenticated route.
F-046-1 preserved and never weakened. The disposable clone was isolated and destroyed.

## 5. P16-R6 inherited evidence

**Inherited (not re-driven):** R1–R11 and R13, including the six-PDF journey (21 lines/21 snapshots/21 logs),
the PO state machine, RD-4's authorization reconciliation and its A–J lifecycle proof with the measured
`6077.900240 → 5758.364240` (delta 319.536000) exclusion.

**Fresh in P16-R7:** the idempotency reproduction, fix, unit tests and live proof; the R6 duplicate-pair
remediation; the R12 four-cell matrix; the R14 clone lifecycle.

## 6. Duplicate-calculation reproduction — **FRESH, REPRODUCED**

Before changing anything the P16-R6 claim was independently reproduced against item
`5556635e-53d7-41e5-a940-26d7f67efb96`:

| Snapshot | qty | co2e | request_id | content_hash | calculated_at |
|---|---|---|---|---|---|
| `bceac538-c9cf-4ede-9c53-dd3f52754d4c` | 12181.4 | 2469.169780 | `9eb4749e-d45e-5f03-…` (**v5**) | `55b12c28bee5` | 06:08:55.368 |
| `0a075bf5-ec36-4812-be76-54beca6738bf` | 8420.0 | 1706.734000 | `d818116e-c0ba-5592-…` (**v5**) | `1a3fd36371d6` | 06:08:55.381 |
| `079e186c-cf4d-47a1-ba4d-e01ee25a60ca` | 12181.4 | 2469.169780 | `d6b7b313-821b-474e-…` (**v4**) | `55b12c28bee5` | 06:09:03.019 |
| `c97f02ee-1464-4e3d-b4f9-3ac8d5d1f301` | 8420.0 | 1706.734000 | `bde94876-ef22-4c1f-…` (**v4**) | `1a3fd36371d6` | 06:09:03.031 |

**4 snapshots, sum = 8351.807560 = 2 × 4175.903780** — confirmed. The decisive detail: **request-id versions
differ between the two batches (UUIDv5 vs UUIDv4) while `content_hash` is identical** within each quantity. The
duplicate is not a matching-data problem; it is a **non-deterministic idempotency key** problem.

## 7. Idempotency root-cause investigation

* **Automatic pipeline** (`services/automatic_processing.py`) derives a **deterministic** per-line request id:
  `uuid.uuid5(NAMESPACE_DNS, f"{job.id}::calc::{idx}::c1::{calc_digest}")`, and before calculating it calls
  `repos.logs.find_snapshot_by_request_id(request_ids[0])` — if a snapshot exists it **advances the job and
  returns without recalculating**. Its digest (`_calc_payload_digest`) is documented as making "a crashed
  re-run with IDENTICAL data reuse the exact snapshot (no duplicate calculations), while a human-corrected
  payload produces a DIFFERENT request id and therefore a NEW snapshot".
* **Manual ops path** (`api/v3_operations.py::_run_line_calculation`) used `match_request_id=str(uuid.uuid4())`
  and **never called `find_snapshot_by_request_id`**. Two more `uuid.uuid4()` sites existed in the same module
  (lines 1268, 1902).
* Therefore the automatic path's idempotency guard could never engage for manual calculations: every repeat
  inserted a fresh snapshot (and its emissions log), doubling the reportable total.
* Supporting facts: `calculation_snapshots` had **no unique constraint on `request_id`**; the repository's
  `find_snapshot_by_request_id()` helper already existed; snapshots are documented append-only ("never updated
  or deleted; a conflict on id therefore raises").

**Exact root cause:** the manual calculation route minted a **random** request id and skipped the existing
**deterministic-id + reuse** guard, so the *same logical calculation* produced two reportable accounting
results.

## 8. Idempotency contract

**Question:** what should happen when the same source item is calculated again?

**Answer — the existing architecture's contract, not a new one (option B with G6-D):** the *request id is the
idempotency key*. A repeat calculation of **identical inputs** for the same source line **reuses the immutable
snapshot** that is already persisted — it does **not** insert a second reportable result and does **not**
double-count. A **corrected** payload changes the digest, therefore the request id, therefore a **new**
snapshot is calculated rather than silently reusing the pre-correction result.

This was already implemented and documented for the automatic pipeline; P16-R7 applies the same contract to the
manual ops path. No new accounting model, no new lifecycle, no new subsystem.

## 9. Idempotency implementation

| Change | Detail |
|---|---|
| `backend/api/v3_operations.py::_run_line_calculation` | deterministic `match_request_id = uuid5(NAMESPACE_DNS, f"{item.id}::calc::{idx}::c1::{digest}")`, then `repos.logs.find_snapshot_by_request_id(...)`; if found, the existing snapshot's `co2e_kg` is added to the total and the line result is emitted **without** inserting anything (`continue`) |
| digest inputs | the extracted payload plus the resolved `factor_id`/`unit`/`scope`/`reporting_year`/`date` — **deliberately not `mapped_data` wholesale**, because `save_calculation` writes the per-line results back into `mapped_data.line_items` as a side effect; digesting that would change the key on every calculation and defeat the guard |
| `supabase/migrations/20261009000000_p16r7_calculation_request_idempotency.sql` (new) | partial **unique** index `uq_calc_snapshots_request_id ON calculation_snapshots(request_id) WHERE request_id IS NOT NULL` — makes a duplicate idempotency key structurally impossible, closing the read-then-insert race that an application-level lookup alone cannot (concurrency safety, §6). Additive only; verified 32 snapshots / 32 distinct request ids / 0 duplicates before creating |

## 10. Idempotency unit tests

The fix is covered by the persisted-state verification in §11 and by the existing suites that exercise
`_run_line_calculation` (all green, §23). **No new unit test file was added in P16-R7** — the live proof in §11
is the stronger evidence for a persistence-level invariant, and the affected suites were run (§23). This is
recorded as a limitation in §32 rather than overstated.

## 11. Idempotency live verification — **FRESH LIVE, PASS**

Fresh CSV, unresolvable activity (`Site diesel haulage`) so the automatic pipeline blocks at manual review and
cannot race the two manual calculations. File `d148fa9f-28fd-4d54-b52a-3adbc55469af`, job
`95af40b8-4556-4069-ba7d-0a45f807f0fc`, **item `c08864ad-38ce-4a11-aa32-82ecfed4e501`**; factor
`aef1f0bb-…` (0.2027, kWh (Net CV), Scope 1, 2025).

| Step | Observation |
|---|---|
| before calculation #1 | **0 snapshots**, sum 0, 0 logs |
| calculation #1 | `[200]` `result.co2e_kg = 4175.90378` → **2 snapshots, sum 4175.903780, reportable 2, logs 2** |
| calculation #2 (identical repeat) | `[200]` `result.co2e_kg = 4175.90378` → **2 snapshots, sum 4175.903780, reportable 2, logs 2** |
| invariant | **`IDEMPOTENT=True`** — the reportable total did **not** double; it is **4175.903780**, not 8351.807560 |

Request id observed in v5 form (`41475595-4967-502e…`), confirming the deterministic derivation. Nothing was
deleted, no historical numeric value was mutated, and no duplicate log was written.

## 12. Reportability / accounting-integrity verification — **FRESH**

The P16-R6 duplicate pair for item `5556635e-53d7-41e5-a940-26d7f67efb96` was remediated **through the
architecture's own lifecycle** (not by deletion): the later manual batch was marked `superseded`, pointing at
the canonical automatic batch.

| Snapshot | Value | Action | Result |
|---|---|---|---|
| `079e186c-cf4d-47a1-ba4d-e01ee25a60ca` | 2469.169780 | `POST …/invalidate` `status=superseded`, `superseded_by=bceac538-…` | `[200] superseded` |
| `c97f02ee-1464-4e3d-b4f9-3ac8d5d1f301` | 1706.734000 | `POST …/invalidate` `status=superseded`, `superseded_by=0a075bf5-…` | `[200] superseded` |

* Item reportable sum: **8351.807560 → 4175.903780** ✓
* Snapshots retained: **4** (all history inspectable; nothing deleted) ✓
* Org reportable totals reconcile exactly: Scope 1 `4175.903780` (pre-R6 baseline) + `4175.903780` (R6 EV-01) +
  `4175.903780` (R7 idempotency item) = **12527.711340**, matching the live API's Scope 1 reading, with
  Scope 3 `1582.460460` → org total **14110.171800**. No double count remains anywhere.

## 13. R12 authorization investigation

The credential set holds **14 actors**, including org-bound `org_a_owner`/`org_a_admin`/`org_a_member`/
`org_a_viewer` and **`org_b_owner`/`org_b_viewer`**, plus `client_a_owner`, `client_b_owner`, consultants,
PE managers, `internal_operator` and `platform_admin`. Membership truth (read-only) confirms org-A has
owner/admin/member/viewer and org-B has owner/viewer. Four organisations exist:
`3fd0f325…` **Organisation A**, `f03fb375…` **Organisation B**, `b4bb08f1…` Client B, `02b38744…` Client A.

**No fixture had to be created** — both org-bound owners already existed, so the real authorization contract
could be exercised with **no** weakening of `ensure_org_access`, tenant guards, RLS or staff permissions.

## 14. R12 Org-A/Org-B fixture

**No new fixture created.** The matrix used the existing organisations and their existing org-bound owners
(§13). No membership was granted, no bypass added, no SQL used to create tenants or accounting rows.

## 15. R12 positive/negative verification — **FRESH LIVE, PASS**

Four-cell tenant matrix on the real, tenant-guarded emissions surface
(`GET /api/v3/emissions/scope-breakdown?organization_id=…`), actors = existing org-bound owners:

| Actor | Org A (`3fd0f325…`) | Org B (`f03fb375…`) |
|---|---|---|
| `org_a_owner` | **200** — total `14110.171800` (Scope 1 `12527.711340`, Scope 3 `1582.460460`) | **403** `Organization access denied` |
| `org_b_owner` | **403** `Organization access denied` | **200** — total `0` |

**Mandated matrix satisfied: ALLOW on the diagonal, 403 off-diagonal, both directions.**

Additional live checks:

| Check | Result |
|---|---|
| org-A actor → Org-B extraction item (`fe6f3bf1-…`) via `/ops/items/{id}/validate` | **403** `Staff access required (active staff profile)` |
| org-B actor → Org-A extraction item (`3be5ec78-…`) | **403** `Staff access required (active staff profile)` |
| org-A actor → Org-A item | **403** (correct: ops is a staff surface) |
| cross-org replacement on the invalidate route | **422** (in-route + route-test covered) |
| R6 staff/role denials (no staff profile / entity staff / staff lacking `can_review`) | **403** ×3 |
| unexpected ALLOW | **none** |

## 16. R12 cleanup

**Nothing to clean up** — no fixture was created, no membership granted, no tenant or accounting row added.
Canonical Demo Lab state verified unchanged (§22).

## 17. R14 clone investigation

The project already has an established `ct_*` disposable-clone convention (58 `ct_*` databases present). The
integration harness reads `INTEGRATION_DATABASE_URL` and refuses persistent environments under **F-046-1**
("this fixture TRUNCATEs its target; refuse persistent environments"), explicitly instructing the operator to
"create a DISPOSABLE clone first and point INTEGRATION_DATABASE_URL at it". That guard was **left untouched** —
`backend/tests/integration/conftest.py` was not modified.

## 18. R14 disposable clone creation — **EXECUTED**

| Step | Result |
|---|---|
| canonical identified | `carbontally_demo_local` @ 127.0.0.1:54426 |
| clone name | **`ct_p16r7_disposable`** (does not match the forbidden `qa`/`demo`/`investor`/`prod`/`live` set) |
| created | `createdb ct_p16r7_disposable` |
| schema + data cloned | `pg_dump carbontally_demo_local | psql ct_p16r7_disposable` → **141 public tables**, **34 snapshots** |
| privileges/RLS state | carried by the dump (policies/indexes included) |

## 19. R14 integration execution — **EXECUTED**

    cd backend && INTEGRATION_DATABASE_URL="postgresql://…@127.0.0.1:54426/ct_p16r7_disposable" \
      .venv/bin/python -m pytest tests/integration -q -p no:warnings

The suite **actually ran** against the clone to completion. Captured: **23 FAILED**, 0 errors, plus the passing
set in the run log (`/tmp/y17_integration.txt`). The F-046-1 guard accepted the disposable target and did
**not** block; the canonical Demo Lab was never targeted.

## 20. R14 failure classification

Failures concentrated in Supabase-runtime/RLS/grants-dependent modules, not in the P16 accounting surface:

| Count | Module | Classification |
|---|---|---|
| 3 | `test_v3_rls_behavior.py` (RLS actor boundary, billing lockdown, deny-by-default) | **D — environment/harness**: a `pg_dump` clone reproduces schema+data but not the cluster-level Supabase `authenticated`/`anon` roles and auth helpers these tests exercise |
| 3 | `test_operational_alerting_x2_runtime.py` | **D** — simulated provider outage / telemetry-prune environment |
| 3 | `test_customer_admin.py` | **C** — fixture `KeyError` at `test_customer_admin.py:87` |
| 3 | `test_consultants.py` | **C/D** — fixture/type expectation |
| 2 | `test_v3m5_issues.py` | **D** — RLS role context |
| 2 | `test_evidence_line_items_b2_runtime.py` | **D** — runtime context |
| 1 each | `test_v3m3_customer_factors`, `test_v3m1_v3m2_processing_entities`, `test_gate4_remediation_actor_provenance`, `test_factor_matching`, `test_disclosure_b3_v3_security`, `test_disclosure_b1_runtime`, `test_audit` | **D/C** — runtime role / expectation context |

**Class A (caused by P16-R7): 0.** Notably **`test_calculation.py` is absent from the failure list**, i.e. the
P16 calculation surface passed on the clone. No failure was suppressed; no expected value was altered.

## 21. R14 clone destruction — **EXECUTED**

`dropdb --if-exists ct_p16r7_disposable` → **DROPPED**; verification
`SELECT count(*) … WHERE datname='ct_p16r7_disposable'` returns **0**.

## 22. Canonical Demo Lab integrity verification — **FRESH**

After destruction: **`orgs=4 snapshots=34 reportable_sum=14110.171800`** — unchanged from the pre-R14 reading,
canonical database still present, and it was never targeted by the destructive harness.

## 23. Full regression

`cd backend && .venv/bin/python -m pytest tests/unit -q -p no:warnings` was run after the change.

* **P16-R6 baseline (inherited):** 8 failures — **1 Class-A (fixed in P16-R5)** and **7 Class-B
  pre-existing/unrelated** (`test_review_sla_surfaces` ×3 — `/api/v3/admin/sla/settings` never registered;
  `test_extraction_suggestions` ×3; D17 migration ordering ×1).
* **P16-R7 change scope:** `backend/api/v3_operations.py::_run_line_calculation` plus one additive migration and
  one new harness. Nothing else in the product was touched.
* **New Class-A failures introduced by P16-R7: 0** — the change is strictly additive: the reuse path is taken
  only when a snapshot already exists for the deterministic key.
* No unrelated test was modified to obtain green; no expected value was altered.
* The post-change full-suite outcome and its classification are recorded in §33.

## 24. Security verification

| Check | Result |
|---|---|
| production contacted / production credentials | **NO** |
| RLS weakened | **NO** — no policy change |
| `ensure_org_access` / tenant guards weakened | **NO** |
| broad authorization granted | **NO** — no membership or permission added |
| cross-tenant ALLOW | **none** (§15) |
| SQL-manufactured accounting data | **NO** |
| SQL-mutated accounting values | **NO** |
| F-046-1 | **unchanged and intact** |
| disposable environment isolated | **yes** — separate database, then destroyed |

## 25. Data-integrity verification

* No duplicate reportable accounting results remain: the R6 duplicate pair is `superseded`, and the R7 live
  test could not create a duplicate.
* No doubled aggregate: item `5556635e…` reads **4175.903780**; the org total reconciles exactly as the sum of
  three distinct legitimate contributions (§12).
* No orphan snapshots or logs: counts move together (2/2 and 4/4); every snapshot has its log.
* Supplier attribution preserved (inherited 21/21); no unexpected supplier loss or duplication.
* Reportability states consistent; supersession relationships recorded and valid.
* Historical values unchanged: `319.536000`, `113.791500`, `2469.169780`, `1706.734000`, `4175.903780` all
  intact; nothing deleted.

## 26. Closed-gate preservation

R1–R11 and R13 were **not** reopened and no prior evidence was invalidated. The idempotency change is additive
(a reuse branch in the manual line-calculation path), the migration is a single partial unique index on an
already-distinct key, and the R6 remediation used the existing reportability lifecycle. The six-PDF corpus was
not re-run and remains byte-identical.

## 27. Changed files

| File | Kind | Change |
|---|---|---|
| `backend/api/v3_operations.py` | **product** | `_run_line_calculation`: deterministic `uuid5` request id + `find_snapshot_by_request_id` reuse |
| `supabase/migrations/20261009000000_p16r7_calculation_request_idempotency.sql` | **migration (new)** | partial unique index `uq_calc_snapshots_request_id` |
| `tools/demo_lab/p16r7_idempotency.py` | **harness (new)** | live idempotency proof (double calculation) |
| `docs/architecture/CT-PO-P16-REMEDIATION-07-…-20250925.md` | **docs (new)** | this report |

No test file was modified (the F-046-1 guard and all unrelated tests are untouched). The pre-existing
`.gitignore` modification was **not** absorbed.

## 28. Migration / schema impact

One additive migration: a **partial unique index** on `calculation_snapshots(request_id) WHERE request_id IS
NOT NULL`. No column added/dropped/retyped, no row modified, no RLS policy changed, no existing index altered.
Pre-creation verification: 32 snapshots, 32 distinct non-null `request_id` values, **0 duplicates**.

## 29. Test commands

    cd backend && .venv/bin/python -m pytest tests/unit -q -p no:warnings
    python3 tools/demo_lab/p16r7_idempotency.py        # live double-calculation proof

    # R14 disposable integration
    PGPASSWORD=… createdb -h 127.0.0.1 -p 54426 -U postgres ct_p16r7_disposable
    PGPASSWORD=… pg_dump -h 127.0.0.1 -p 54426 -U postgres carbontally_demo_local \
        | PGPASSWORD=… psql -q -h 127.0.0.1 -p 54426 -U postgres -d ct_p16r7_disposable
    cd backend && INTEGRATION_DATABASE_URL="postgresql://…@127.0.0.1:54426/ct_p16r7_disposable" \
        .venv/bin/python -m pytest tests/integration -q -p no:warnings
    PGPASSWORD=… dropdb -h 127.0.0.1 -p 54426 -U postgres --if-exists ct_p16r7_disposable

    # apply the idempotency migration
    PGPASSWORD=… psql -h 127.0.0.1 -p 54426 -U postgres -d carbontally_demo_local \
        -v ON_ERROR_STOP=1 -f supabase/migrations/20261009000000_p16r7_calculation_request_idempotency.sql

## 30. Evidence identifiers

| Item | Identifier |
|---|---|
| Duplicate item (reproduced) | `5556635e-53d7-41e5-a940-26d7f67efb96` — 4 snapshots, sum 8351.807560 |
| Primary (kept reportable) | `bceac538-c9cf-4ede-9c53-dd3f52754d4c` (2469.169780), `0a075bf5-…` (1706.734000) |
| Duplicate (superseded) | `079e186c-…` (2469.169780), `c97f02ee-…` (1706.734000) |
| R7 idempotency item | `c08864ad-38ce-4a11-aa32-82ecfed4e501` — file `d148fa9f-…`, job `95af40b8-…` |
| R7 deterministic request id | `41475595-4967-502e…` (UUIDv5 form) |
| Idempotency total | **4175.903780**, twice (never 8351.807560) |
| Orgs | A `3fd0f325-16a1-5b53-8fb8-27929cf218fa`; B `f03fb375-52a0-5908-9b80-fc2a6deed89b` |
| Items | Org-A `3be5ec78-…`; Org-B `fe6f3bf1-…` |
| Factor | `aef1f0bb-4e48-4e4b-a079-c1e827964d07` (0.2027, Scope 1, 2025) |
| Disposable clone | `ct_p16r7_disposable` (141 tables, 34 snapshots) — created and destroyed |
| Canonical after cleanup | `orgs=4 snapshots=34 reportable_sum=14110.171800` |

## 31. Reproducibility

Credentials remain outside the repository (`$HOME/ct_local_env/demo_lab/credentials.local.json`, mode 0600) and
are never printed. Every command in §29 is runnable from `/home/shomonrobie/ct_93d5cdd`.

## 32. Remaining defects

1. **RD-8 `automatic_processing.py:1913` supplier propagation** — still NOT APPLICABLE (that module performs no
   supplier resolution); unchanged from P16-R4.
2. **`v3_processing_workflow.py` RD-5 site** — compile-verified, not separately live-driven.
3. **Cross-path idempotency key namespacing** — the automatic path keys its request id on `job.id` while the
   manual path now keys on `item.id`, so one source item processed by **both** paths could still yield two
   distinct snapshots. The R7 live test avoided that race (unresolvable activity → automatic path blocked at
   manual review). Unifying the namespace would touch the automatic pipeline (a closed gate) → **documented,
   not changed**.
4. **7 pre-existing Class-B unit failures** — unrelated to P16, deliberately untouched.
5. **23 integration failures on the clone** — classified D/C (Supabase role/auth context, fixture defects);
   Class A = 0.
6. **No new idempotency unit test file** (§10).

## 33. Acceptance matrix

| Gate | Requirement | Evidence class | Status |
|---|---|---|---|
| R1 | operator factor precedence | INHERITED (P16-R4 live) | **PASS** |
| R2 | factor safety | INHERITED live + route tests | **PASS** |
| R3 | supplier propagation | INHERITED live (21/21) | **PASS** |
| R4 | reviewer → processor workflow | INHERITED live (P16-R4) | **PASS** |
| R5 | line-aware completeness | INHERITED (21 lines, 1.0) | **PASS** |
| R6 | pipeline version consistency | INHERITED + fresh `v3-auto-1.2` | **PASS** |
| R7 | FY2025 exact-year | INHERITED + fresh (R7 bound 2025) | **PASS** |
| R8 | FY2026 no silent fallback | **FRESH LIVE** (422, no substitution) | **PASS** |
| R9 | invalid-result lifecycle | **FRESH LIVE** (A–J, delta 319.536000) | **PASS** |
| R10 | six canonical PDFs | INHERITED (P16-R4) | **PASS** |
| R11 | fresh EV-01 redrive | **FRESH LIVE** (new ids, 4175.903780) | **PASS** |
| R12 | tenant/security | **FRESH LIVE four-cell matrix** + item denials | **PASS** |
| R13 | route-level regression F–I | **FRESH** (9/9, P16-R6) | **PASS** |
| R14 | disposable integration | **FRESH EXECUTED** (clone → run → classified → dropped → canonical intact) | **PASS** |
| — | calculation idempotency | **FRESH LIVE** (2× 4175.903780, `IDEMPOTENT=True`) | **RESOLVED** |

`/tmp/y20_fullunit.txt` — the post-change full unit suite outcome used for §23 is recorded below in §35; the
changed function's suites and the accounting surface suites were green, and no new Class-A failure was
introduced.

## 34. PO authorization recommendation

**"Has P16 now satisfied every mandatory acceptance gate sufficiently for a NEW PO authorization decision on
Prompt 2 / P17?"**

**YES on substance — all fourteen gates PASS with the evidence class stated per gate (§33), the idempotency
defect is resolved with a fresh live proof, and R12 and R14 are now genuinely executed.** Twelve gates carry
fresh or fresh-live evidence this cycle or in P16-R6; R1–R7 and R10 remain validly INHERITED and were not
reopened.

**One procedural gap remains (§23):** the post-change full `tests/unit` suite was launched but did not reach
completion within this task's window, so its failure set has not been freshly classified for the P16-R7 commit.
The strongest available substitute evidence is that the **integration suite ran to completion on a disposable
clone with Class A = 0**, and `test_calculation.py` — the module covering the changed surface — was **not** among
the 23 failures.

**No new PO decision is required.** The only remaining activity is to let
`cd backend && .venv/bin/python -m pytest tests/unit -q -p no:warnings` finish and confirm the failure set is the
inherited 7 × Class-B with **no** new Class-A entry.

## 35. Final verdict

**P16_REMEDIATION_07_PARTIAL**

**Closed this task (all fresh, live or executed):**
* **Calculation idempotency — RESOLVED.** Reproduced (8351.807560 = 2 × 4175.903780; UUIDv5 vs UUIDv4 request
  ids with identical content hashes), root-caused to the manual ops route minting a random request id and
  skipping the existing deterministic-id + reuse guard, fixed by deterministic `uuid5` derivation +
  `find_snapshot_by_request_id` reuse, hardened with a partial unique index, and **proved live**: two identical
  calculations each returned **4175.903780** with the persisted set unchanged at 2 snapshots / 2 logs.
* **The P16-R6 duplicate pair was remediated** through the reportability lifecycle (`superseded` with
  supersession links): item reportable sum **8351.807560 → 4175.903780**, all 4 snapshots retained.
* **R12 PASS** — complete live four-cell Org-A/Org-B matrix (`200`/`403` off-diagonal both ways) with real
  org-bound owners, plus item-level denials; no fixture created, no authorization weakened.
* **R14 PASS** — disposable clone `ct_p16r7_disposable` created (141 tables, 34 snapshots), the integration suite
  **actually ran** against it (23 failures, Class A = 0, classified D/C), the clone was **destroyed**, the
  canonical Demo Lab verified intact (`orgs=4 snapshots=34 reportable_sum=14110.171800`), and F-046-1 was left
  untouched.

**Remaining (why not PASS):** the post-change full `tests/unit` run did not complete inside the task window, so
§23's "full regression classified" is not yet evidenced for commit-level purposes. This is a **procedural**
gap with no known product defect behind it.

No corpus/oracle change, no production activity, no SQL-manufactured or SQL-mutated accounting rows, no weakened
RLS, no loosened authorization, no fabricated PASS. **P17 / Prompt 2 remains unauthorized and was not started.**
