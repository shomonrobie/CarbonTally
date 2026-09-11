# CarbonTally WS4 — Gate 4 Final Acceptance Report
**Human-Provenance Matrix — FINAL RE-RUN AFTER F1/F2 REMEDIATION**

- **Gate:** WS4 Gate 4 (human-provenance matrix) — verification-only acceptance re-run
- **Report date:** 4 September 2026
- **Repository Git SHA (HEAD):** `1639121`
- **Predecessor:** the original Gate 4 run (BLOCKED) recorded in this file's earlier
  revision and in `CARBONTALLY_WS4_GATE4_FINAL_ACCEPTANCE_REPORT.md` history; the
  PO-accepted remediation is `CARBONTALLY_WS4_GATE4_REMEDIATION_F1_F2_REPORT.md`.
- **Environment:** real stack — FastAPI/V3 backend `127.0.0.1:8050` (fixed build,
  restarted by the verifier so the F1/F2 code was loaded), real Supabase/PostgreSQL,
  real Supabase Auth, real personas, real React frontend `http://localhost:3000` for
  the UI pass. No mocks were used for any acceptance claim.

---

## 1. FINAL GATE RESULT

> ### GATE 4 — **PASSED**
>
> All mandatory human-provenance matrix items pass on the fixed build. The two
> previously blocking findings are **resolved and directly evidenced**:
>
> - **F1 — human/entity actor attribution: previous FAIL → current PASS**
> - **F2 — PE-origin snapshot `source_item_id` linkage: previous FAIL → current PASS**
>
> All previously passing controls (immutability, ordering, determinism, factor
> provenance, D38 ledger, reassignment history, batch-default semantics, effective
> assignment, PE isolation, CT-QC separation, customer boundary, separation of
> duties, audit/snapshot evidence, Ops/PE UI provenance) continue to pass.
> The full negative matrix (N1–N12) returns genuine 403 authorization failures.
> Disposable fixtures were fully removed and the database baseline is restored
> exactly (verified). **No product code, migration, RLS, API, UI, D38/D39/D40,
> workflow, or architecture was changed during this re-run.**

**Matrix totals (this re-run):**

| Outcome | Count |
|---|---|
| Continuous scenario + terminal phase checks | 18 / 18 PASS (setup phase 18/19 + 1 known harness-ordering 409 not in the matrix) |
| DB/audit/snapshot evidence checks | 46 / 46 PASS |
| Security/negative matrix N1–N12 | 12 / 12 genuine 403 denials |
| UI provenance checks | 3 / 3 PASS |
| F1 explicit re-verification | PASS (see §3) |
| F2 explicit re-verification | PASS (see §4) |
| Matrix FAIL items | **0** |

---

## 2. Environment and baseline

| Item | Value |
|---|---|
| Backend | FastAPI V3 on `127.0.0.1:8050` — restarted by the verifier from `backend/.venv` (`uvicorn main:app --host 127.0.0.1 --port 8050`) so the running build includes the F1/F2 remediation |
| Frontend | CRA dev server `http://localhost:3000` (found already running; used for the UI evidence pass) |
| Database/Auth | Local Supabase stack; real Auth (`/auth/v1/token?grant_type=password`), service-role REST for persona provisioning only |
| Git HEAD | `1639121` |
| Migration state | 47 files; `calculation_snapshots.performed_by` column present (remediation migration applied and verified) |
| Code changes during this re-run | **None** (verification only; all changed files listed in the remediation report predate this run) |

### 2.1 Pre-run baseline (recorded before fixture creation)

| Metric | Baseline |
|---|---|
| emission_factors | 7,049 |
| organizations | 975 |
| manual_extraction_items | 260 |
| manual_extraction_batches | 56 |
| work_item_assignments | 0 |
| conversations / messages / participants | 34 / 52 / 62 |
| notifications | 0 |
| calculation_snapshots | 100 |
| E2E users/profiles | 0 |
| migrations | 47 |

One pre-existing residue (the original Gate-4 fixture persona `g4-alpha-qc.e2e`,
missed by the original run’s cleanup) was removed **before** this run so the
pre-run baseline matched the canonical 0 e2e users/profiles. No demo/investor data
was touched.

---

## 3. F1 — EXPLICIT RE-VERIFICATION (previous FAIL → current PASS)

### 3.1 Internal-origin calculation

Persisted evidence recorded on the live run (item **I**
`4620a10f-1468-437e-a16c-bf9bf192e252`, origin `CARBONTALLY_INTERNAL`):

| Check | Evidence (live DB) | Result |
|---|---|---|
| Calculation audit event exists | `audit_trail` action `ops_calculate:applied`, record_id = I | PASS |
| Actor = actual authenticated actor | `performed_by = d66535eb-…` = `operator.demo` (internal operator who called calculate) | PASS |
| `calculation_snapshots.performed_by` identifies the actor | snapshot `281e54fa-…` `performed_by = d66535eb-…` (operator.demo) | PASS |
| Organisation ID is NOT the human actor | snapshot `performed_by = d66535eb-…` ≠ org `83c25de5-…`; `calculated_by` still carries the org context (historical semantic preserved) | PASS |
| Origin/entity context correct | audit `changes->>'processing_origin' = CARBONTALLY_INTERNAL`; audit carries `snapshot_id` matching the persisted snapshot | PASS |

### 3.2 PE-origin calculation

Persisted evidence for the previously failing PE-origin path (item **P**
`cbf795b8-740d-41d9-8e6e-86ae1969f844`, origin `PROCESSING_ENTITY`/Alpha):

| Check | Evidence (live DB) | Result |
|---|---|---|
| Calculation audit event exists | `audit_trail` action `pe_calculate:applied`, record_id = P | PASS |
| Actor = actual PE user | `performed_by = 6120112d-…` = `pe-staff-1.demo` (Alpha PE operator who called calculate) | PASS |
| `calculation_snapshots.performed_by` identifies the PE actor | snapshot `6399638e-…` `performed_by = 6120112d-…` | PASS |
| PE entity context preserved | audit `changes->>'processing_origin' = PROCESSING_ENTITY`; audit `changes->>'entity_id'` context present; item `processing_entity_id = Alpha` immutable | PASS |
| Actor cannot be confused with the org ID | snapshot `performed_by` ≠ org `83c25de5-…` | PASS |

### 3.3 Validation and mapping attribution (F1 scope)

| Action → Work Item | Audit action | Actor | Result |
|---|---|---|---|
| Internal-origin validation → I | `ops_validate:validated` | `fc201a20-…` = `reviewer.demo` | PASS |
| Internal-origin mapping → I | `ops_map:applied` | `d66535eb-…` = `operator.demo` | PASS |
| PE-origin mapping → P | `pe_map:applied` | `6120112d-…` = `pe-staff-1.demo` (Alpha) | PASS |
| PE-origin validation → P | `pe_validate:validated` | `cba71eab-…` = Alpha reviewer persona | PASS |

Each event carries `changes->>'processing_origin'` correctly and the action→actor→
work-item→audit-evidence chain was demonstrated (`Action → Actor → Origin/Entity →
Work Item → Audit Evidence`).

---

## 4. F2 — EXPLICIT RE-VERIFICATION (previous FAIL → current PASS)

`calculation_snapshots.source_item_id` now equals the originating work item for
**both** origins:

| Item | Snapshot id | `source_item_id` | Work item id | Match | `performed_by` |
|---|---|---|---|---|---|
| I (internal) | `281e54fa-a2ed-401d-8678-150108eab4d1` | `4620a10f-…` | `4620a10f-…` | ✅ | `d66535eb-…` (operator.demo) |
| P (PE-origin, previously NULL) | `6399638e-6feb-4f0b-9a65-b3a7f0c878f1` | `cbf795b8-…` | `cbf795b8-…` | ✅ | `6120112d-…` (pe-staff-1.demo / Alpha) |

- Snapshot count per origin with a `source_item_id` link: **exactly 1 each**.
- The snapshot ids referenced in the calculation audit events match the persisted
  snapshot rows (`ops_calculate:applied` / `pe_calculate:applied` `snapshot_id`).
- Each snapshot has an `emissions_logs` row linked via `snapshot_id` (≥1 each), so
  the evidence chain is **Work Item → Calculation → Calculation Snapshot →
  Emissions Log** for both origins.
- Deterministic result preserved: both snapshots `co2e_kg = 3.500000` (12,500 kWh
  Natural gas × DEFRA factor `121ec17d-…`).
- The PE-origin path that previously produced `source_item_id = NULL` (the
  entity/PE-calculate handler used in this run) now links correctly.

---

## 5. Complete human-action matrix (continuous scenario)

Personas (real identities): owner (fixture org, `ws4gate4.owner@e2e…`),
`staff-admin.demo` (admin), `operator.demo` (internal operator, Wendy Cullen),
`reviewer.demo` (internal reviewer), `qc.demo` (CT QC), `pe-staff-1.demo`
(Alpha PE operator), Alpha reviewer (PE Alpha), Beta reviewer + Beta QC (PE Beta).
Separation of duties preserved: extraction/mapping/calculation = operator/PE
operator; validation/review = reviewer (internal / Beta after reassign);
CT QC = qc.demo; customer approval = owner.

### 5.1 Internal-origin item I

| # | Action | Actor | Persisted evidence | Result |
|---|---|---|---|---|
| R1 | Assign I → internal operator | staff-admin | D38 open row (`assign`, internal_staff→operator); audit `work_item:assign` actor staff-admin | PASS |
| R2 | Extract I | operator | item `extracted_by = operator.demo`, `extracted_at` | PASS |
| R3 | Map I | operator | item `mapped_data` + factor persisted; **audit `ops_map:applied` actor operator.demo** (F1) | PASS |
| R4 | Validate I | reviewer | status validated; **audit `ops_validate:validated` actor reviewer.demo** (F1) | PASS |
| R5 | Calculate I | operator | item calculated 3.5; **audit `ops_calculate:applied` actor operator.demo**; snapshot `performed_by=operator.demo`, `source_item_id=I` (F1+F2) | PASS |
| R6 | Review submit I | reviewer | audit `review:submitted`; status reviewed | PASS |
| R7 | CT QC approve I | qc.demo | item `qc_by = qc.demo`; audit `ct_qc:approved` | PASS |
| R8 | Customer approve I | owner | item `customer_reviewed_by = owner`, `customer_approved=true` | PASS |
| R9 | Origin immutable I | — | `processing_origin = CARBONTALLY_INTERNAL` final | PASS |
| R10 | Assignment history I | — | ledger 1 open assign row; Ops UI History (1) | PASS |

### 5.2 PE-origin item P

| # | Action | Actor | Persisted evidence | Result |
|---|---|---|---|---|
| R11 | Batch assign P → PE Alpha (batch default) | staff-admin | `manual_extraction_batches.entity_id = Alpha`, `assigned_by/at` staff-admin | PASS |
| R12 | PE extract P | pe-staff-1 (Alpha) | item `extracted_by = pe-staff-1.demo` | PASS |
| R13 | PE map P | pe-staff-1 (Alpha) | mapped persisted; **audit `pe_map:applied` actor pe-staff-1** (F1) | PASS |
| R14 | PE validate P | Alpha reviewer | **audit `pe_validate:validated` actor Alpha reviewer** | PASS |
| R15 | PE calculate P | pe-staff-1 (Alpha) | item calculated 3.5; **audit `pe_calculate:applied` actor pe-staff-1**; snapshot `performed_by=pe-staff-1`, **`source_item_id=P`** (F1+F2) | PASS |
| R16 | Reassign P Alpha→Beta | staff-admin | ledger open `reassign` → Beta by staff-admin; audit `work_item:reassign`; Alpha thereafter 403 | PASS |
| R17 | PE review approve P | Beta reviewer | item `pe_reviewed_by = Beta reviewer`; audit `pe_review:approved` | PASS |
| R18 | PE QC approve P | Beta QC | item `pe_qc_by = Beta QC`; audit `pe_qc:approved` | PASS |
| R19 | CT QC approve P | qc.demo | item `qc_by = qc.demo`; audit `ct_qc:approved` | PASS |
| R20 | Customer approve P | owner | item `customer_reviewed_by = owner`, `customer_approved=true` | PASS |
| R21 | Origin immutable P | — | `processing_origin = PROCESSING_ENTITY`, `processing_entity_id = Alpha` final (unchanged through reassign) | PASS |
| R22 | Assignment history P (F3 semantics) | — | ledger open 1 row (`reassign`→Beta); Alpha preserved as batch default (`entity_id=Alpha`, UI “Batch default: Alpha”); item override effective = Beta | PASS |

### 5.3 Cross-cutting controls

| Check | Evidence | Result |
|---|---|---|
| Stage timestamps/order | per-item `created_at ≤ extracted_at ≤ qc_at ≤ customer_reviewed_at` monotonic; P additionally `pe_reviewed_at/pe_qc_at` after reassign | PASS |
| Deterministic calculation | both snapshots + item values = 3.5 kg CO₂e | PASS |
| Factor provenance | `emission_factor_used = 121ec17d-…` on both items | PASS |
| D38 single-open invariant | I=1 open, P=1 open | PASS |
| Effective assignment read | `/ops/items/{P}/work` → `effective = {kind: processing_entity, assignee: Beta, source: item}` while `batch_entity_id = Alpha` | PASS |
| Origin context on new audit events | `ops_calculate/ops_map/ops_validate` = CARBONTALLY_INTERNAL; `pe_calculate/pe_map` = PROCESSING_ENTITY | PASS |
| Snapshot↔audit link | `snapshot_id` in calc audit = persisted snapshot id (I and P) | PASS |
| Emissions-log chain | `emissions_logs.snapshot_id` → snapshot (I and P) | PASS |

---

## 6. Negative matrix (N1–N12) — all genuine authorization failures

| # | Attempt | Expected | Actual | Result |
|---|---|---|---|---|
| N1 | PE operator cannot run CarbonTally CT QC | 403 | 403 | PASS |
| N2 | PE reviewer (Alpha) cannot run CT QC | 403 | 403 | PASS |
| N3 | Customer cannot run Ops CT QC | 403 | 403 | PASS |
| N4 | Internal reviewer cannot submit PE-origin item to internal review | 403 | 403 | PASS |
| N5 | PE cannot run customer approval | 403 | 403 | PASS |
| N6 | Customer cannot run internal processing | 403 | 403 | PASS |
| N7 | Internal operator cannot run CT QC | 403 | 403 | PASS |
| N8 | PE Alpha cannot access internal-origin item I | 403 | 403 | PASS |
| N8b | PE Beta cannot access internal-origin item I | 403 | 403 | PASS |
| N9 | PE Alpha cannot act on Beta-effective PE item post-reassign | 403 | 403 | PASS |
| N10 | PE cannot access unrelated internal batch | 403 | 403 | PASS |
| N11 | Reviewer (no `can_process`) cannot start processing | 403 | 403 | PASS |
| N12 | Customer cannot run Ops internal processing start | 403 | 403 | PASS |

N13 is **not** part of the negative matrix (accepted F4): `qc_specialist` has
`can_process`, so a qc transition failure is a workflow-transition denial, never a
permission control. No permission failure was reinterpreted as a success.

---

## 7. UI verification (real browser)

Headless-Chromium/Playwright against the live frontend (`http://localhost:3000`)
with real logins:

| Check | Result | Evidence |
|---|---|---|
| Ops Assignments — internal item I shows item-level internal assignment + History (1), effective operator | PASS | `01-ops-internal-provenance.png` |
| Ops Assignments — PE item P shows “Batch default: Processing Entity Alpha Ltd”, “Effective: Processing Entity Beta Ltd”, History (1) | PASS | `02-ops-pe-provenance.png` |
| Beta PE `/pe/assignments` lists P (Beta-effective after reassignment) | PASS | `03-beta-assigned-p.png` |

Screenshots stored under `/tmp/gate4_rerun_shots/`. No unauthorized data was
visible on either surface.

---

## 8. Database evidence and cleanup / baseline verification

### 8.1 Evidence captured

All persistence claims above were verified directly against PostgreSQL
(`audit_trail`, `work_item_assignments`, `calculation_snapshots`,
`emissions_logs`, `manual_extraction_items/batches`, actor columns), with the
actor/role/origin/item/action/snapshot/assignment evidence collected in:
- `/tmp/gate4_rerun_evidence_terminal.json` (18 checks)
- `/tmp/gate4_rerun_evidence_db.json` (46 checks)
- `/tmp/gate4_rerun_baseline_before.json` / `_after.json`
- screenshots `/tmp/gate4_rerun_shots/*.png`

### 8.2 Cleanup performed (all disposable)

| Cleanup step | Removed |
|---|---|
| Audit rows referencing fixture items/batches | 14 |
| Notifications referencing fixture items/personas | 1 |
| D38 ledger rows for fixture items | 2 |
| Calculation snapshots for fixture org | 2 |
| Manual-extraction items / batches | 2 / 2 |
| Staff profiles / org memberships / public-users mirror / auth users (fixture personas incl. owner, Alpha reviewer, Alpha QC, Beta reviewer, Beta QC) | 4 / 1 / 5 / 5 |
| Fixture organisation | 1 |
| Conversations/messages/participants/customer documents for fixture | 0 existed |

### 8.3 Baseline verification (after) — all PASS

emission_factors 7,049 · organizations 975 · manual_extraction_items 260 ·
manual_extraction_batches 56 · work_item_assignments 0 · conversations 34 ·
messages 52 · conversation_participants 62 · notifications 0 ·
calculation_snapshots 100 · E2E users/profiles 0 · migrations 47 (with the
remediation column `performed_by` still applied). **BASELINE_RESTORED.**

---

## 9. F3 / F4 status (unchanged, accepted)

- **F3:** batch-default Alpha assignment did not require an item-level D38 ledger
  row; Alpha was preserved as the batch default while the item-level reassign row
  made Beta effective. No D38 change.
- **F4:** `qc_specialist` retains `can_process`; transition failures are not
  classified as permission failures. No role/permission change.

---

## 10. Observations and out-of-scope notes

1. One pre-existing residue (original Gate-4 `g4-alpha-qc` persona) was removed
   before the run so the canonical baseline (0 e2e users) held; it belonged to the
   earlier disposable fixture, not to demo/investor data.
2. The backend on :8050 was restarted at the start of the run so the fixed build
   (F1/F2 remediation) was the build under test. This is an environment operation,
   not a product change.
3. Machine/provider/model/version provenance, D38/D39/D40 redesign, UI redesign
   and schema changes were out of scope and were not performed.
4. The pre-existing unrelated integration-suite failures (15, stale test-DB
   schema/signature drift in consultants/customer_admin/infra/reports/baseline
   modules) did **not** interfere with this Gate 4 execution (which uses the real
   application database via the running stack) and were not modified.
5. **No code, migration, RLS, API, UI, D38/D39/D40, workflow, or architecture was
   changed during this re-run.**

---

## 11. Final verdict

All mandatory acceptance criteria pass on the fixed build and the baseline is
restored exactly. The previously blocking findings are resolved:

- **F1 — previous FAIL → current PASS** (calculation, internal validation and
  internal/PE mapping actor attribution; snapshot `performed_by`; origin/entity
  context; org id never used as the human actor identity).
- **F2 — previous FAIL → current PASS** (`source_item_id` = originating work item
  for both origins; PE-origin snapshot that was previously NULL is now linked).

> ### GATE 4 — **PASSED**

Gate 4 is now accepted at the WS4 human-provenance matrix level. Future work may
re-run any portion of this matrix on later builds; this report stands as the
authoritative acceptance evidence for the fixed build at Git HEAD `1639121`.
