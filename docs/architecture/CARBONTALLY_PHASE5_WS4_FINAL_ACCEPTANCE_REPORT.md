# CarbonTally Phase 5 / WS4 — Final Acceptance Report

Status: **WS4 FINAL ACCEPTANCE — GATE 1 PASS (3 SEP 2026) + GATE 2 PASS (3 SEP 2026)**.
Gate 3 (multi-PE / single-batch provenance) executed 3 SEP 2026 — result
**BLOCKED — ARCHITECTURAL CONFLICT** (see dated Gate 3 entry at the end of this
file; a partial achievable evidence set is recorded there). Gates 4–5 not
started; WS5 and Phase 6 not started. V1.2 frozen; D38/D39/D40 approved; PE
Validation Option A approved & implemented. No new architecture/roles/RLS/
schema/state-machine changes introduced by the Gate 1–3 runs. No commit/push.

## Executive result
Substantial, browser-verified evidence exists through the **Calculation** stage
for BOTH origins (including the new PE validation path). The terminal human
downstream stages (Internal Review → CT QC → Customer Review/Approval; and on
PE-origin: PE Review → PE QC → CT QC → Customer Review/Approval as one
continuous run) were **not executed to their terminal approval state in this
closure session**, the full backend regression suite was not re-run in this
session, and the multi-PE batch/item provenance fixture was not executed.
Per §25/§26/§27 the acceptance criteria are therefore not all met; per the
frozen role of this task no unapproved implementation was performed to close
them.

## Internal-origin E2E evidence (real UI, disposable fixture, from pending)
pending → Claim → extracted → mapped → validated → **calculated** — PASS
(operator extraction/mapping, reviewer validate, operator /calculate HTTP 200
with persisted result; no mapped→calculate; validation findings refresh).
Internal Review → CT QC → Customer Review/Approval — **DEFERRED** (not run to
terminal state in this session).

## PE-origin E2E evidence
pending → extracted → mapped → **PE Validate (Option A)** → validated →
**calculated** — PASS (PV1–PV12; reviewer HTTP 200 + audit; operator has no
Validate; calculate unavailable at mapped; cross-PE/customer/internal/cap
negatives 403; beyond-mapped 409).
PE Review → PE QC — previously accepted browser evidence on fixtures at
`calculated`. PE-origin CT QC → Customer Review/Approval continuous run —
**DEFERRED**.

## PE Validation (Option A) evidence
Endpoint POST /api/v3/pe/items/{id}/validate (CAP_REVIEW), canonical
validation engine, mapped→validated | mapped→mapping (blocking), immutable
`pe_validate:*` audit event; UI control at mapped for review-capable members.
PASS.

## Multi-PE batch/item provenance test
**NOT RUN** (Item A→Alpha, B→Beta, C→Alpha, D→Internal in one batch). D38
ledger (claim/assign/release/complete/history, open-assignment invariant,
origin immutability, audit) accepted from WS1/WS4 evidence; the specific
one-batch/multi-PE fixture requires a further isolated run. Cross-PE item
denial (403, no leak) accepted from WS4 evidence.

## D38 / D39 / D40
- D38: accepted WS1 + WS4 browser evidence (assignment attributable; current
  vs history distinct; origin immutable). Multi-PE reassign fixture pending.
- D39: accepted WS4 two-session isolation (PE↔Ops only; no PE↔customer, no
  PE↔PE; entity boundary).
- D40: accepted WS3/WS4 API-read inbox evidence (assignment event → recipient
  notification → unread → target reauthorization; idempotent event key).

## Human processing provenance
Audit events verified/recorded for claim/validate/calculate/PE review/PE QC
flows with actor, domain/entity, action, previous/next state, origin,
timestamp; work-item provenance columns persisted (extracted_by/at,
mapped_data, calculated emissions, pe_*/qc_*). A complete 11-action
attribution matrix over one continuous run was not compiled this session.

## Automated extraction provenance assessment
Deterministic/OCR extraction records actor/time (`extracted_by`, `extracted_at`)
and audit where applicable. Machine/provider/model/version attribution for
automatic extraction is not currently represented in the audit contract.
Classification per §25: **B/C — documented residual, not an acceptance
blocker** (it does not prevent the frozen V1.2 workflow from operating). No
unapproved extraction-provenance architecture was added.

## Human-after-automation attribution
No evidence in this session that saving/approving automated output rewrites
the automated actor record; however no dedicated automated-extraction E2E
fixture was run, so this remains **assessed at the mechanism level only**.

## Authorization matrix (verified subset)
PE operator no validate (403/UI), cross-PE no validate (403), internal staff
via PE contract 403, customer via PE 403, beyond-mapped validate 409; CT QC
and customer-approval 403 matrices previously accepted (WS3/WS4). Full matrix
re-run incl. all personas was not completed this session.

## Regression / build / responsive
Frontend production build: PASS (this session). Full backend suite, V1.2,
D38/D39/D40 and PE-validation test re-run: **NOT RE-RUN this session**
(backend additive change only; prior WS1–WS3 suites passed). Responsive:
six-width pass accepted for Ops Assignments and PE surfaces; new PE Validate
control not independently matrixed at all six widths.

## Data integrity (post-run, exact)
emission_factors 7049 · migrations 45 · organizations 975 · items 260 ·
batches 56 · assignments 0 · conversations 34 · messages 52 · participants 62
· notifications 0 · e2e auth users 0 · e2e profiles 0.

## Residual (non-blocking)
Automated extraction provenance gap (B/C). Full 11-action human attribution
matrix and one-batch/multi-PE provenance fixture outstanding.

## Blocker (this session)
Terminal-state browser E2E for both origins (through Customer Approval by the
customer persona) and the full backend regression re-run were not executed in
this session. These are execution gaps, not architecture gaps; no stop
condition (new role/capability/state machine/RLS/schema/architecture) was
triggered.

## Recommendation
Do not declare WS4 complete. Authorize one further isolated closure run to
execute both terminal-state workflows, the multi-PE batch fixture, and the
full regression + responsive matrix.

---

# WS4 RESUME - FINAL CLOSURE EXECUTION LOG

## Gate 9 - Full backend regression (executed this session)
Command: backend/.venv/bin/python -m pytest backend/tests -q --tb=no
Run completed (100% of collection; ~2,800+ tests collected). Exact pass/skip
totals line was not captured in the log output; **16 FAILED** tests, all
integration/environmental, none in D38/D39/D40 or PE-validation unit suites:
consultants (3), customer_admin (3), infra service-client (3),
report_versions (1), reports (3), factor baseline (1), customer-factor RLS
(1), auth_simple (1 - httpx.ConnectError to a non-running endpoint).
Classification: environmental/pre-existing integration failures (live-DB
state + service availability); not introduced by PE Validation (additive
backend change, endpoint live + authorization-verified). Exact
pass/fail/skip/error totals require a re-run with default verbosity.

## Gates still unexecuted this session (unchanged)
1. Internal terminal workflow -> Customer Approval (Gate 1).
2. PE terminal workflow -> Customer Approval (Gate 2).
3. Multi-PE/single-batch provenance fixture (Gate 3).
4. Frontend test suite + six-width responsive matrix on PE Validate (Gates
   10/11).
5. Fixture-level human/automated provenance matrix (Gates 4-6) - mechanism
   assessment stands.

No architecture/schema/RLS/role/state-machine/D38/D39/D40/CT-QC/customer-
approval change occurred. Baselines remain exact.

---

# WS4 CLOSURE RUN #2 - EXACT REGRESSION TOTALS

Re-run: pytest backend/tests (default verbosity). **16 failed, 1516 passed,
0 skipped, 0 errors, 4 warnings - 160s.** Collected: 1532.

Failures (all environmental/pre-existing, none D38/D39/D40/PE-validation,
none WS4-workflow relevant):
- consultants (3) + customer_admin (3) + infra (3): fixture users 'user-1'
invalid-UUID / Supabase invalid API key / missing repository args => test-env
fixtures/credentials not provisioned. Environmental.
- report_versions (1) + reports (3): Supabase client/token env errors;
KeyError 'token'. Environmental.
- factor baseline (1): test expected 7049 but ran against isolated test DB
with 25 factors (assert 25==7049). Environmental (suite DB mismatch).
- customer-factors RLS no-delete (1): test asserts NO delete policy, but
approved V1.2 architecture added customer_factors_tenant_delete. Pre-existing
obsolete expectation (documented, not WS4-blocking).
- auth_simple (1): httpx.ConnectError to auth endpoint - no auth service in
test env. Environmental.

---

# WS4 FINAL ACCEPTANCE — GATE 1 ONLY: INTERNAL-ORIGIN TERMINAL E2E (EXECUTED 3 SEPTEMBER 2026)

Scope gate: **Gate 1 — Internal terminal browser E2E**. Terminal path executed:

    calculated → reviewed (Internal Review) → ct_qc_approved (CarbonTally QC)
    → approved (Customer Review/Approval)

Upstream internal stages (pending → Claim → extracted → mapped → validated →
calculated) were not re-run as UI work: they were previously accepted, and per
the Gate 1 brief a **fresh disposable fixture was established to `calculated`
through the legitimate application contract** (the same real operator /
reviewer HTTP endpoints the UI calls). Every terminal transition in this run
was performed through the **real browser UI** by **real authenticated personas**,
with genuine HTTP request/response capture and post-state DB assertions.

Environment: local stack — Frontend `http://localhost:3000` (CRA dev),
CarbonTally API `http://127.0.0.1:8050`, Supabase `127.0.0.1:54425/54426`,
headless Chromium via Playwright (same browser stack as prior accepted WS4
runs). No commit/push. Gates 2–5 not started. WS5 / Phase 6 not started.

## Fixture / personas

- Disposable fixture organisation `WS4 Gate1 Internal Fixture (disposable)`
  (org `bf2ae520-7dc5-4027-ae9d-f7937e16e8ac`) created through the real D35
  self-service organisation endpoint (creator becomes owner).
- Fixture customer owner auth identity (local-only):
  `ws4gate1.owner@e2e.carbontally.local` — org OWNER; created through the
  GoTrue admin provisioning path and **removed** at teardown.
- Manual-extraction batch `WS4-Gate1-Internal-E2E-Batch`
  (`63cc56b1-754c-43d2-b10a-cef36130f05f`) + internal-origin items created via
  the real customer `manual-extraction` API contract.
- Internal-origin item driven to `calculated` via the real ops API contract:
  start-extraction → extract → start-mapping → map → reviewer validate →
  start-calculation → calculate.
  - Primary fixture item (single continuous terminal evidence):
    `7a27ddd7-ee33-4049-9a34-a9bc87795876`
    `gate1-internal-natural-gas-b.csv` — 12,500 kWh natural gas, canonical
    factor `121ec17d-2986-467b-a09a-6b4b78ead049`, persisted result
    3.5 kg CO₂e (factor basis kg CO₂e CH4 per kWh), calculation snapshot
    persisted (count = 1, `source_item_id` = item).
  - A first disposable item (`26547c59-5787-44a0-b3e8-4a33cac5a318`) was used
    during driver calibration and reached `ct_qc_approved`; it was also fully
    removed at teardown (it is not part of the accepted evidence chain).
- Personas (established demo population, unchanged):
  - Internal Reviewer: `reviewer.demo@demo.carbontally.local` (can_review)
  - CarbonTally QC: `qc.demo@demo.carbontally.local` (can_qc)
  - Internal Operator (negative only): `operator.demo@demo.carbontally.local`
  - PE Admin (negatives only): `pe-manager-1.demo@demo.carbontally.local`
  - Customer Owner: fixture owner above (org owner; approval authority)
- No new production roles or capabilities were created.


## Step 2 — Internal Review (real browser UI)

UI action: reviewer opens `/ops/review/{item}` → **Submit for CarbonTally QC**.

- Actual HTTP request observed in browser:
  `POST /api/v3/ops/items/7a27ddd7-…/submit-review` → **200**
  response item `status: "reviewed"`.
- Persisted state (DB-asserted): item status `calculated → reviewed`.
- Audit event (append-only): `review:submitted` — actor
  `fc201a20-591d-53b6-9d9f-4b316f75cc4b` (= `reviewer.demo@…`),
  changes `{"status_to":"reviewed","status_from":"calculated",
  "processing_origin":"CARBONTALLY_INTERNAL"}`.
- After page reload the "Submit for CarbonTally QC" control is gone
  (item no longer at `calculated`). Provenance: internal origin preserved.

## Step 3 — CarbonTally QC (real browser UI)

UI action: QC opens `/ops?tab=ctqc` → Open QC workspace → quality score 90 →
**Approve for customer review**.

- Actual HTTP request observed in browser:
  `POST /api/v3/ops/qc/items/7a27ddd7-…/decision` → **200** with
  `{"approved":true,"quality_score":90}`; response item
  `status: "ct_qc_approved"`.
- Persisted state (DB-asserted): item status `reviewed → ct_qc_approved`;
  item row `qc_by = 351a04c8-5a06-5dcf-8505-7eeaf6daa102` (=
  `qc.demo@…`), `qc_at`, `quality_score = 90`.
- Audit event: `ct_qc:approved` — actor `351a04c8-…`,
  changes `{"status_to":"ct_qc_approved","status_from":"reviewed",
  "quality_score":90,"processing_origin":"CARBONTALLY_INTERNAL",
  "processing_entity_id":null}`.
- PE users cannot perform this action (see negatives N1 + browser Phase P).

## Step 4 — Customer Review (real browser UI)

Gate verification performed in-browser on the same item:

- While the item was at `reviewed` (post Internal Review, **pre CT-QC**), the
  customer review queue `/review` did **not** list the item (empty state shown) —
  no premature availability.
- After CT QC approved the item (`ct_qc_approved`), the same customer queue
  `/review` listed the item (file name + `ct_qc_approved` state). The customer
  then opened the item workspace `/review/{item}`.
- The review UI exposes a single Review/Approve stage (no distinct
  intermediate "customer review" transition in the frozen V1.2 contract —
  `ct_qc_approved` maps directly onto the Review/Approve screen, consistent
  with the accepted V1.2 implementation). UI + HTTP evidence recorded for the
  distinct Approve action in Step 5.

## Step 5 — Customer Approval (real browser UI)

UI action: customer Owner opens `/review` → opens the CT-QC-released item →
**Approve** → confirmation dialog **Approve**.

- Actual HTTP request observed in browser:
  `POST /api/v3/processing/items/7a27ddd7-…/customer-review` → **200**;
  response item `status: "approved"`.
- Persisted final state (DB-asserted): item `status = approved`,
  `processing_origin = CARBONTALLY_INTERNAL`,
  `customer_approved = true`,
  `customer_reviewed_by = 6a12a0e6-f679-4183-b59d-b5c56539a079` (=
  `ws4gate1.owner@e2e.carbontally.local`, the fixture org OWNER),
  `customer_reviewed_at = 2026-09-03 13:53:24 UTC`. Calculation provenance
  intact (snapshot count 1, factor preserved).
- Customer decision provenance is recorded by the frozen contract as immutable
  stamps on the item row (customer_approved / customer_reviewed_by /
  customer_reviewed_at / customer_notes), matching the accepted V1.2/WS4
  evidence model. Approval was a genuine browser interaction — not inferred
  from API availability.


## Step 6 — Security negatives (Gate-1 relevant subset only)

All executed while the fixture item was at `reviewed` (pre-CT-QC) or on a
PE-origin item. No workflow state was mutated by any negative (403/409 before
any write).

1. **PE user cannot perform CT QC** —
   `POST /api/v3/ops/qc/items/{id}/decision` as `pe-manager-1.demo@…`
   → **403** "CarbonTally internal staff access required". Browser: PE
   opening `/ops?tab=ctqc` is redirected to the PE application (`/pe`); no
   CarbonTally QC queue UI exists for PE users.
2. **Customer cannot perform CT QC** —
   decision endpoint as fixture customer owner → **403**
   "Staff access required (active staff profile)".
3. **Customer cannot approve before CT QC** —
   `POST /api/v3/processing/items/{id}/customer-review` (approved) while item
   at `reviewed` → **409** "invalid item transition 'reviewed' -> 'approved'";
   item also absent from the customer `/review` queue at that state
   (browser-verified empty state). No premature approval path exists.
4. **Unauthorized internal user cannot perform CT QC** —
   decision endpoint as `operator.demo@…` (can_process, no can_qc) → **403**
   "staff lacks permission: can_qc".
5. **PE-origin item cannot use the internal-review path** —
   `POST /api/v3/ops/items/{pe-item}/submit-review` (internal reviewer persona)
   on PE-origin item `77333333-3333-4333-8333-333333333333` → **403**
   "PE-originated work uses PE Review/PE QC before CarbonTally QC" (origin
   gate fires before any state write).

## Step 7 — Cleanup & baseline comparison (post-run, exact)

All disposable E2E rows removed and verified:

- 2 calculation_snapshots + 2 emissions_log rows (items A/B) deleted
- 5 audit_trail rows (org.created + review:submitted + ct_qc:approved for the
  disposable items) deleted
- 2 manual_extraction_items + 1 manual_extraction_batch deleted
- organization_members + organizations (fixture org) deleted
- fixture auth user removed via GoTrue admin (`200`)
- No demo/investor record was modified or deleted. Emission factor set
  untouched (factor `121ec17d-…` read-only).

Baseline verified after teardown (exact): emission_factors **7,049** ·
organizations **975** · items **260** · batches **56** · assignments **0** ·
conversations **34** · messages **52** · participants **62** · notifications
**0** · E2E auth users/profiles **0** · fixture orgs/items **0**.

## Gate 1 verdict

Gates 2–5 not attempted this session. WS5 and Phase 6 not started. No
commit/push was made; the working tree contains only the pre-existing
unrelated uncommitted changes and this report update.

**GATE 1 — INTERNAL TERMINAL E2E: PASS**


---

# WS4 FINAL ACCEPTANCE — GATE 2 ONLY: PE-ORIGIN TERMINAL E2E (EXECUTED 3 SEPTEMBER 2026)

Scope gate: **Gate 2 — PE-origin terminal workflow through final Customer
Approval.** Terminal path executed end-to-end through the **real browser UI**
with real authenticated personas and genuine HTTP request/response capture:

    calculated → pe_reviewed (PE Review, PE Reviewer)
             → pe_qc_approved (PE QC, PE QC Specialist)
             → ct_qc_approved (CarbonTally QC, internal qc.demo)
             → approved (Customer Review/Approval, fixture customer OWNER)

Upstream PE stages (pending → extracted → mapped → PE Validate → validated →
calculated) were **not repeated as UI work** — they are already accepted Gate
evidence. A **fresh disposable PE-origin fixture was legitimately driven to
`calculated` through the real application contract** (customer org contract →
Ops batch assignment to Processing Entity Alpha → PE operator extraction /
mapping / calculation via the real `/api/v3/pe/*` and shared entity-extraction
routes, PE Reviewer validation). Gate 1 evidence was NOT re-run.

Environment: local stack — Frontend `http://localhost:3000` (CRA dev),
CarbonTally API `http://127.0.0.1:8050`, Supabase `127.0.0.1:54425/54426`,
headless Chromium via Playwright. Screenshots:
`/tmp/gate2_shots/02-…09-*.png`. No commit/push. Gates 3–5, WS5, Phase 6 not
started.

## Fixture (fresh, disposable — fully removed at teardown)

| Item | Value |
|---|---|
| Organisation | `WS4 Gate2 PE Terminal Fixture (disposable)` — `99f3bd32-d805-448a-a2fe-ac0885745fe8` (D35 self-service, creator = OWNER) |
| Batch | `WS4-Gate2-PE-Origin-E2E-Batch` — `b8068ea9-d1b3-4365-8139-b478b4a3c1d5` |
| Item | `gate2-pe-origin-natural-gas.csv` — `ac784096-919d-4007-8888-77a11a05e339` |
| PE / origin | Processing Entity Alpha Ltd `a25a0537-…-21eb21703abc`; `processing_origin = PROCESSING_ENTITY` |
| Factor | `121ec17d-2986-467b-a09a-6b4b78ead049` (canonical natural-gas kWh); result 3.5 kg CO₂e |
| Reach `calculated` | via real contract: owner creates org/batch/item → `staff-admin.demo` assigns batch to Alpha (`POST /api/v3/ops/batches/{id}/assign` 200) → `pe-staff-1.demo` start/extract/start/map + `pe-reviewer.e2e` PE validate + start/calculate → status `calculated` (HTTP 200 each) |

Reaching `calculated` used the shared ops **entity-extraction calculate** route
(`/api/v3/ops/entities/{id}/extraction/items/{id}/calculate`) because the
canonical `/api/v3/pe/items/{id}/calculate` delegate currently returns **500**
(unresolved `Depends(get_calculation_engine)` — see Findings below). No code
change was made during this acceptance run.

## Personas (established fixture mechanism, no new production roles)

| Persona | Identity | Role / capability basis |
|---|---|---|
| PE Reviewer | `pe-reviewer.e2e@e2e.carbontally.local` (user `19af7377-…`) | disposable staff profile: staff role `reviewer`, entity = Alpha → PE Review |
| PE QC Specialist | `pe-qc.e2e@e2e.carbontally.local` (user `49518f78-…`) | disposable staff profile: staff role `qc_specialist`, entity = Alpha → PE QC |
| CarbonTally QC | `qc.demo@demo.carbontally.local` (user `351a04c8-…`) | internal qc_specialist, `can_qc` (established demo persona) |
| Customer Owner | `ws4gate2.owner@e2e.carbontally.local` (user `480ac90b-…`) | fixture org OWNER (GoTrue admin + D35) — approval authority |
| PE operator (pre-calc only) | `pe-staff-1.demo@demo.carbontally.local` | Alpha operator `can_process` (established demo persona) |
| Negatives only | `staff-admin.demo`, `reviewer.demo`, `pe-manager-1.demo`, `pe-manager-2.demo` | established demo personas |


## Step 2 — PE Review (real browser UI)

PE Reviewer opens `/pe` (PE application; post-login landing verified) → the
fixture batch (`WS4-Gate2-PE-Origin-E2E-Batch`) is shown under **Processing
Entity Alpha Ltd · Reviewer** → **Show items** → row for the calculated
PE-origin item → **PE Review approve**.

- Actual HTTP request observed in browser:
  `POST /api/v3/pe/items/ac784096-…/pe-review` → **200**; response item
  `status: "pe_reviewed"`.
- Persisted state (DB-asserted): item `calculated → pe_reviewed`;
  `pe_reviewed_by = 19af7377-…` (PE Reviewer), `pe_reviewed_at =
  2026-09-03 14:53:06 UTC`; `processing_origin = PROCESSING_ENTITY`,
  `processing_entity_id = a25a0537-…` (Alpha) — unchanged.
- Audit event (append-only): `pe_review:approved` — actor
  `19af7377-…`, `record_id = item`.
- UI confirmation: "PE Review approved — decision recorded" + `pe_reviewed`
  stage visible; screenshot `/tmp/gate2_shots/02-pe-review-approved.png`.

## Step 3 — PE QC (real browser UI)

PE QC Specialist opens `/pe` (**Processing Entity Alpha Ltd · QC Specialist**)
→ the item (now `pe_reviewed`) → **PE QC approve**.

- QC Specialist does **not** see a `PE Review approve` control (no review
  capability — distinct from the reviewer, and distinct from CarbonTally CT QC).
- Actual HTTP request observed in browser:
  `POST /api/v3/pe/items/ac784096-…/pe-qc` → **200**; response item
  `status: "pe_qc_approved"`.
- Persisted state (DB-asserted): item `pe_reviewed → pe_qc_approved`;
  `pe_qc_by = 49518f78-…` (PE QC Specialist), `pe_qc_at =
  2026-09-03 14:53:20 UTC`; origin/entity unchanged.
- Audit event: `pe_qc:approved` — actor `49518f78-…`.
- Screenshot `/tmp/gate2_shots/03-pe-qc-approved.png`.

## Step 4 — CarbonTally QC (real browser UI; internal-only surface)

Internal `qc.demo` opens `/ops?tab=ctqc` → **CarbonTally QC** tab. The PE-origin
item is listed at `pe_qc_approved` **only after** PE Review + PE QC, with an
origin chip **Processing Entity** and originating PE **Processing Entity Alpha
Ltd** on the row and in the QC workspace (stage rail
`calculated → pe_review → pe_qc → ct_qc`). **Approve for customer review** was
clicked with quality score **90**.

- Actual HTTP request observed in browser:
  `POST /api/v3/ops/qc/items/ac784096-…/decision` → **200**; response item
  `status: "ct_qc_approved"`.
- Persisted state (DB-asserted): item `pe_qc_approved → ct_qc_approved`;
  `qc_by = 351a04c8-…` (CarbonTally QC), `qc_at = 2026-09-03 14:53:50 UTC`,
  `quality_score = 90`; origin/entity unchanged.
- Audit event: `ct_qc:approved` — actor `351a04c8-…`.
- PE users cannot perform this action: browser has no CT QC surface on `/pe`
  and the API denies every PE role (negatives N1–N3 below).
- Screenshots `/tmp/gate2_shots/05-ctqc-workspace-pe-origin.png` and
  `/tmp/gate2_shots/06-ctqc-approved-pe-origin.png`.

## Step 5 — Customer Review (real browser UI, fixture OWNER)

- **Before CT QC** (item at `pe_qc_approved`): the customer review queue
  `/review` did **not** list the item (empty state; browser-verified) — no
  premature availability.
- **After CT QC** (item `ct_qc_approved`): the same queue listed the item and
  the owner opened the item workspace `/review/{item}`.
- The item is correctly scoped to the fixture organisation (owner-visible), and
  the customer item page does **not** expose PE identity / internal operational
  detail (asserted absence of `Processing Entity Alpha Ltd`, `pe_qc` and
  `PROCESSING_ENTITY` on the customer page). The frozen contract has no distinct
  intermediate customer-review transition; `ct_qc_approved` maps directly onto
  the Review/Approve screen (consistent with Gate 1 and the accepted V1.2
  evidence). Distinct Approve action evidence in Step 6.

## Step 6 — Customer Approval (real browser UI, fixture OWNER)

UI action: Owner opens `/review` → opens the CT-QC-released item → **Approve**
(enabled action button) → confirmation dialog **Approve**.

- Actual HTTP request observed in browser:
  `POST /api/v3/processing/items/ac784096-…/customer-review` → **200**;
  response item `status: "approved"`.
- Persisted final state (DB-asserted): `status = approved`,
  `customer_approved = true`, `customer_reviewed_by = 480ac90b-…`
  (`ws4gate2.owner@…`, the fixture org OWNER),
  `customer_reviewed_at = 2026-09-03 14:55:52 UTC`;
  `processing_origin = PROCESSING_ENTITY` and
  `processing_entity_id = a25a0537-…` unchanged throughout.
- Calculation provenance intact: 1 snapshot for the fixture org, factor
  `121ec17d-…` preserved, result 3.5 kg CO₂e.
- Approval was a genuine browser interaction (button + confirmation dialog),
  not inferred from API availability. Screenshots
  `/tmp/gate2_shots/07-…09-customer-approved.png`.

## Step 7 — Gate-2-specific negative security tests (all PASS)

Every denial occurred **before any data mutation**; item state/origin were
unchanged after each and exactly one approval event per stage remained in the
audit trail.

| # | Test | Actor → action | Result |
|---|---|---|---|
| N1 | PE Reviewer → CT QC | `pe-reviewer.e2e` → `POST /api/v3/ops/qc/items/{id}/decision` | **403** "CarbonTally internal staff access required" |
| N2 | PE QC Specialist → CT QC | `pe-qc.e2e` → same | **403** |
| N3 | PE Admin → CT QC | `pe-manager-1.demo` → same | **403** |
| N4 | PE user → Customer Approval | `pe-manager-1.demo` → `POST /…/customer-review` | **403** "Organization admin privileges required" |
| N5 | Customer → CT QC | fixture owner → CT QC decision | **403** "Staff access required" |
| N6 | Customer approval before CT QC | fixture owner → `customer-review` at `pe_qc_approved` | **403** "PE-originated work must pass CarbonTally QC (ct_qc_approved) before customer approval" |
| N7 | Cannot bypass PE Review | CT QC decision at `calculated` → **409**; customer-review at `calculated` → **403**; internal `submit-review` on PE-origin item → **403** |
| N8 | Cannot bypass PE QC | CT QC decision at `pe_reviewed` → **409**; customer-review at `pe_reviewed` → **403** |
| N9 | Cannot bypass CT QC | customer-review at `pe_qc_approved` → **403** (same as N6; controlled denial, no state change) |
| N10 | Cross-PE access | `pe-manager-2.demo` (Beta) → `GET /api/v3/pe/batches/{alpha-batch}/items` **403**; `POST /api/v3/pe/items/{id}/pe-review` **403** "Item is not assigned to this processing entity" |


## Step 8 — Provenance (DB-asserted, fixture)

Audit events recorded for the fixture item, in order: `pe_validate:validated`,
`pe_review:approved`, `pe_qc:approved`, `ct_qc:approved` — each with a distinct
actor:

| Transition | Event | Actor (user id) |
|---|---|---|
| mapped → validated (fixture pre-calc) | `pe_validate:validated` | PE Reviewer `19af7377-…` |
| calculated → pe_reviewed | `pe_review:approved` | PE Reviewer `19af7377-…` |
| pe_reviewed → pe_qc_approved | `pe_qc:approved` | PE QC Specialist `49518f78-…` |
| pe_qc_approved → ct_qc_approved | `ct_qc:approved` | CarbonTally QC `351a04c8-…` (qc.demo) |
| ct_qc_approved → approved | immutable owner stamps on the item row | Customer Owner `480ac90b-…` (frozen contract; matches accepted V1.2/WS4 model) |

`processing_origin = PROCESSING_ENTITY` and `processing_entity_id =
a25a0537-…` (Alpha) verified unchanged from first PE touch through final
approval. No duplicate events from the negative attempts (exactly one
`pe_review:approved`, one `pe_qc:approved`, one `ct_qc:approved`).

## Findings / residuals (documented; no code change made)

1. **Canonical `/api/v3/pe/items/{id}/calculate` returns 500** — the PE thin
   delegate calls `entity_extraction_calculate(...)` without resolving its
   `calculation_engine` FastAPI dependency (`'Depends' object has no attribute
   'calculate'`). The PE application's calculation path therefore fails today.
   This acceptance run reached `calculated` through the real shared
   ops entity-extraction calculate route (the route the PE delegate wraps) and
   made **no** code change. Flagged for a PO-approved fix; re-verify the PE UI
   operator calculate path after fix.
2. **Entity-origin calculate snapshot lacks `source_item_id`** (D33 link) on the
   shared entity-extraction route — pre-existing WS4 residual (B/C), consistent
   with the accepted upstream evidence; item-level stage-actor provenance on the
   terminal transitions is fully persisted.
3. One **pre-existing** `public.users` row for the Gate-1 fixture owner
   (`ws4gate1.owner@e2e.carbontally.local`, created 13:34 UTC before this run)
   remains; it was not created by Gate 2 and was left untouched.

## Step 9 — Cleanup & baseline comparison (post-run, exact)

All Gate-2 disposable records and personas were removed and verified absent:
fixture org, batch, item, calculation snapshot(s)/emissions rows, audit rows,
organisation membership rows, PE personas (auth users, `public.users`,
`staff_profiles`) and the fixture customer owner (auth user + `public.users`).
GoTrue admin deletions returned 200. Residual sweep confirmed zero leftovers
created by this run.

Baseline after teardown (exact): emission_factors **7,049** · organizations
**975** · items **260** · batches **56** · assignments **0** · conversations
**34** · messages **52** · participants **62** · notifications **0** · E2E
auth users/profiles created by this run **0** · migrations **45**.
Investor/demo data untouched (only disposable fixture rows were created and
removed).

**GATE 2 — PE TERMINAL E2E: PASS**

---

# WS4 FINAL ACCEPTANCE — GATE 3 ONLY: MULTI-PE / SINGLE-BATCH PROVENANCE (EXECUTED 3 SEPTEMBER 2026)

## Gate 3 Result

**BLOCKED — ARCHITECTURAL CONFLICT**

The literal Gate-3 fixture — ONE batch whose items are simultaneously
distributed to Processing Entity Alpha, Processing Entity Beta, Alpha again,
and CarbonTally internal staff, each with its own item-level current
assignment and processing authorization — **cannot be represented or executed
through the frozen V1.2 / D22 / D38 contract**. The frozen implementation
authorizes manual-extraction processing at the **batch** level: a batch carries
exactly ONE processing party at a time (`manual_extraction_batches.entity_id`
XOR `manual_extraction_batches.assigned_to`), and every PE/internal processing
and D38 access path enforces that single-party carrier. Item-level
`work_item_assignments` rows are an append-only attribution ledger over that
model, not an independent per-item processing-authorization boundary, and there
is no PE→PE item-level reassignment route (approved WS1 model).

Per the task STOP conditions, this is reported instead of implementing a
workaround, creating roles/capabilities, altering RLS, or redesigning D38.
The sections below record the targeted inspection, the legitimate subset of the
scenario that IS achievable (with real HTTP/DB evidence), the authoritative
denials that prove the boundary, and the precise conflict.

## Targeted inspection (Step 1) — authoritative findings

| Area | Finding (code/route) |
|---|---|
| Batch party carrier | `manual_extraction_batches.entity_id` (D22) is the PE processing-party carrier; ops `POST /api/v3/ops/batches/{batch_id}/assign` (`BatchAssign`) accepts exactly ONE of `assigned_to` (internal) or `entity_id` (PE) (`backend/api/v3_operations.py` ~1794). |
| PE item access | `v3_pe._ensure_assigned_item` and `operations_auth.ensure_entity_batch_access` require `batch.entity_id == caller entity` (403 otherwise). PE extraction/validate/calculate delegates enforce the same via the shared entity-extraction routes. |
| Internal item access | `ensure_batch_operator_access` / `_ensure_operator_batch`: internal staff may only process batches with `entity_id IS NULL` assigned to them or open; entity batches are denied to internal ops. |
| D38 item ledger | `work_item_assignments` (append-only; status open/closed; `assignee_kind` internal_staff OR processing_entity; single-open partial unique index; RLS on, no policies — API-only access). |
| Ops item assign | `/api/v3/ops/items/{id}/work/{claim,assign,reassign,recover,release,complete}` — internal staff only; `WorkItemTarget = {assigned_to (internal staff), reason}` (OpenAPI-verified); service `ops_assign_item` refuses items in PE-assigned batches. |
| PE item work | `/api/v3/pe/items/{id}/work/{claim,release,complete}` only — **no PE assign/reassign/recover**; `pe_claim_item` requires `batch.entity_id == own entity`. |
| Origin | `manual_extraction_items.processing_origin` / `processing_entity_id` are immutable (set once by `mark_pe_origin_if_unset` at first PE touch; never rewritten by D38 service). |

## Fixture (Step 2) — disposable, fully removed at teardown

A disposable 2-item fixture was created through the real contract because a
4-item Alpha/Beta/Alpha/Internal distribution in one batch is not creatable
through any legitimate path (Items B and C cannot receive a different PE
current party than the batch carrier while remaining in the same batch).

| Item | Value |
|---|---|
| Org | `WS4 Gate3 MultiPE Fixture (disposable)` — `87907ba2-76ec-47e3-8dab-9636dec0901b` |
| Batch | `WS4-Gate3-MultiPE-Batch` — `562bd224-4e4a-456d-b247-07a19fe2d5e8` |
| Item A | `gate3-item-a.csv` — `f0300212-219e-47bc-9d62-51e9b83cca8b` |
| Item D | `gate3-item-d.csv` — `40215cab-7e43-4ab5-9fd7-c5134a680c30` |
| Alpha PE | `a25a0537-056c-561e-8a7b-21eb21703abc` (Processing Entity Alpha Ltd) |
| Beta PE | `1347665b-f086-5e82-80f2-0c5f0d5c7341` (Processing Entity Beta Ltd) |
| Internal actor | `staff-admin.demo@…` (`e16061c3-…`) assignment actor; `operator.demo@…` (`d66535eb-…`) claim actor |
| PE actors | Alpha `pe-staff-1.demo@…` (`6120112d-…`); Beta `pe-manager-2.demo@…` (`c678f928-…`) |
| Customer owner | `ws4gate3.owner@e2e.carbontally.local` (disposable, removed) |


## Distribution (Step 2/3) — what the frozen model permits vs the gate requires

| Item | Processing Origin (persisted) | Initial current party | Final current party | Result |
| ---- | ------------------------------ | --------------------- | -------------------- | ------ |
| A | `PROCESSING_ENTITY` / Alpha (set by real Alpha PE start) | Alpha (batch entity) | internal operator `d66535eb-…` after batch reassign Alpha → Beta → internal | Achievable via **batch-level** reassignment only; origin unchanged throughout |
| B (planned Beta) | — | — | — | **Not creatable** — batch carrier is single-party; no PE item assign route exists |
| C (planned Alpha) | — | — | — | **Not creatable** in the same batch as B/D while batch is Alpha-assigned |
| D (planned Internal) | `CARBONTALLY_INTERNAL` (default; untouched) | Alpha (batch entity) | internal operator (whole batch reassigned) | Same batch as A (verified), but could not hold an internal current party while the batch was Alpha/Beta-assigned |

Live evidence (all genuine HTTP):
- `POST /api/v3/ops/batches/…/assign {entity_id: Alpha}` → 200 (batch → Alpha).
- Alpha read `GET /api/v3/pe/batches/{batch}/items` → 200; **Beta** same request
  → **403** "Batch is not assigned to this processing entity".
- Beta claim `POST /api/v3/pe/items/{A}/work/claim` → **403** "Item is not
  assigned to this processing entity".
- Internal claim `POST /api/v3/ops/items/{A}/work/claim` while batch = Alpha →
  **403** "Work item belongs to a Processing Entity-assigned batch; PE work is
  entity-scoped (use the PE surface or batch reassignment)".
- Alpha `start` on Item A → 200; DB: `processing_origin = PROCESSING_ENTITY`,
  `processing_entity_id = Alpha`.

## Item-level isolation (Step 3) — verified boundary

The batch context never collapses authorization:
- Beta could not read or claim Alpha-assigned work (403 above).
- Internal staff could not claim item A while the batch was entity-assigned (403
  above).
- After the batch current party moved to Beta, Alpha read → **403** (old party
  no longer has access); Beta read → 200. After the batch moved to the internal
  operator, the internal claim succeeded (200).
- Cross-PE isolation is enforced server-side on every entity touch
  (`ensure_entity_batch_access`, `_pe_entity_item`,
  `ensure_batch_operator_access`).

## Assignment records (Step 4) and Reassignment / history (Step 5)

The legitimate party-change path is **batch-level reassignment**
(`POST /api/v3/ops/batches/{id}/assign` by internal staff-admin), not item-level:
- Alpha → Beta reassign: HTTP 200; DB `manual_extraction_batches.entity_id =
  Beta`; `assigned_to = NULL`.
- Beta → internal reassign: HTTP 200; DB `entity_id = NULL`;
  `assigned_to = d66535eb-…` (operator.demo).
- D38 item ledger: after the batch became internal, `POST
  /api/v3/ops/items/{A}/work/claim` → 200 created exactly ONE open row
  (`action=claim`, `assignee_kind=internal_staff`, `assigned_to=operator`,
  `assigned_by=operator`, `actor_domain=internal_staff`); DB single-open
  invariant verified (`open = 1`).
- **PE→PE item-level reassignment (Item A Alpha → Beta) is not possible under
  the approved model**: there is no `/api/v3/pe/.../work/reassign` route and the
  ops item `WorkItemTarget` schema carries only an internal staff `assigned_to`
  (OpenAPI-verified). The task instruction to respect the approved restriction
  applies; this is reported rather than bypassed.


## Immutable processing origin (Step 6)

Verified through legitimate application behaviour:
- Item A origin set to `PROCESSING_ENTITY` / Alpha by a real Alpha PE `start`.
- After batch reassign Alpha → Beta: origin **unchanged**
  (`PROCESSING_ENTITY` / Alpha) while the batch current party became Beta.
- After batch reassign Beta → internal operator: origin **still**
  `PROCESSING_ENTITY` / Alpha while the D38 current assignment is the internal
  operator (`work read` returns origin PROCESSING_ENTITY/Alpha + current
  internal_staff row).
- Item D remained `CARBONTALLY_INTERNAL` (never touched by a PE).
- Conclusion: `processing_origin ≠ current assignment` is demonstrated; origin
  is never rewritten by assignment changes. Origin spoofing has no endpoint
  (N5 — documented as not directly exercisable; only `mark_pe_origin_if_unset`
  writes origin, once, at first PE touch).

## Actor attribution (Step 7)

| Action | Actor | Domain | Entity | Work item | Audit event (DB) |
| --- | --- | --- | --- | --- | --- |
| Batch assign → Alpha | `staff-admin.demo` `e16061c3-…` | internal_staff | — | batch `562bd224-…` | `assigned` @ 15:41:30Z |
| Batch reassign → Beta | `staff-admin.demo` `e16061c3-…` | internal_staff | — | batch `562bd224-…` | `reassigned` @ 15:41:31Z |
| Batch reassign → internal | `staff-admin.demo` `e16061c3-…` | internal_staff | — | batch `562bd224-…` | `reassigned` @ 15:41:32Z |
| PE origin touch (start) | `pe-staff-1.demo` `6120112d-…` | processing_entity | Alpha | item A | origin stamped on item row (no separate audit) |
| Item claim | `operator.demo` `d66535eb-…` | internal_staff | — | item A | `work_item:claim` (ledger row + audit) |

Attribution comes from ledger `assigned_by`/`actor_domain`, batch audit
`performed_by`, and item provenance stamps — not inferred from current state.

## Security negative matrix (Step 8)

| Test | Expected | Actual | Result |
| --- | --- | --- | --- |
| Beta → Alpha item/batch access | Denied | Beta read Alpha batch **403**; Beta claim Alpha item **403** | PASS |
| Alpha → Beta item access (after reassign) | Denied | Alpha read batch after reassign to Beta **403** | PASS |
| Shared-batch enumeration (Beta using batch context on Alpha-assigned batch) | Denied | **403** "Batch is not assigned to this processing entity" | PASS |
| Old assignment after reassignment | Correctly restricted | Alpha no longer reads after batch → Beta (403); Beta reads (200) | PASS |
| Internal staff on PE-assigned item | Denied | internal ops claim on Alpha-batch item **403** | PASS |
| Processing-origin spoof / change | Denied / not applicable | no endpoint exists; origin unchanged across two reassignments | N/A (documented) |

## Audit / provenance (Step 9)

The persisted evidence can reconstruct **Batch → Item → Party change history →
Processing Origin → Actor → Action** for the model the frozen architecture
implements (batch-level party carrier + D38 item-claim attribution): batch
audit events (`assigned`/`reassigned`, actor + timestamp), item origin columns,
and the D38 ledger/audit for claims are all present and consistent.
The evidence **cannot** reconstruct the Gate-3-specified state — one batch whose
items simultaneously have four different current parties — because that state
cannot exist under the single-party batch carrier. No provenance architecture
was added in this gate.

## Findings

1. **ARCHITECTURAL CONFLICT (blocks the literal Gate-3 fixture):** manual-
   extraction work authorization is single-party-per-batch in the frozen
   implementation (`manual_extraction_batches.entity_id`/`assigned_to`;
   enforced by `ensure_entity_batch_access`, `ensure_batch_operator_access`,
   `v3_pe._ensure_assigned_item`, `ops_assign_item`). The gate's premise that
   "a batch is not necessarily the processing security or attribution boundary"
   does not hold for this workflow in the current V1.2/D22/D38 model. A V1.3+
   change (per-item current processing-party authorization; ops→entity item
   assignment; authorized PE item reassignment) would be required. **PO
   DECISION REQUIRED** — no change was made in this acceptance run.
2. PE item-level reassignment is intentionally absent (approved WS1 model);
   PE party changes are batch-level only. Confirmed in code and OpenAPI.
3. Referenced pre-existing findings (unchanged, not fixed here): canonical
   `/api/v3/pe/items/{id}/calculate` HTTP 500; entity-origin calculation

## Cleanup (Step 10)

- Disposable org, batch, both items, membership rows, D38 ledger rows,
  calculation/emission rows (none created), and the fixture audit rows
  (including the `work_item:claim` audit) were removed.
- Disposable owner auth user + `public.users` row removed via GoTrue admin (200).
- Residual sweep: **CLEAN** (all fixture ids and actor scopes = 0; notifications
  0).
- Baseline after teardown (exact): emission_factors **7,049** · organizations
  **975** · items **260** · batches **56** · work_item_assignments **0** ·
  conversations **34** · messages **52** · participants **62** · notifications
  **0** · E2E users/profiles **0** · migrations **45**.
- Investor/demo data untouched.

## Evidence references (Step 11)

- HTTP/DB evidence JSON: `/tmp/gate3_evidence.json`; probe output:
  `/tmp/gate3_probe_out.txt`; OpenAPI schema probe:
  `/tmp/gate3_schema_out.txt`.
- Scripts: `/tmp/gate3_probe.py`, `/tmp/gate3_schema_probe.py`,
  `/tmp/gate3_cleanup.py` (plus Gate-3 owner deletion helper).
- Code references: `backend/services/work_items.py`,
  `backend/api/v3_operations.py` (`assign_batch`, D38 `/work/*`),
  `backend/api/v3_pe.py` (`/work/{claim,release,complete}`),
  `backend/api/operations_auth.py` (`ensure_entity_batch_access`,
  `ensure_batch_operator_access`),
  `supabase/migrations/20260902030000_phase5_work_item_assignments.sql`,
  `docs/architecture/CARBONTALLY_PHASE5_WS1_D38_IMPLEMENTATION_REPORT.md`.
- No browser screenshots are applicable: the blocked fixture cannot be rendered
  by any legitimate UI path; the evidence is API/DB/audit based.

## Recommendation

Gate 3 is **NOT ready for PO acceptance as specified**. The frozen V1.2/D22/D38
model enforces a single processing party per manual-extraction batch and has no
authorized per-item PE reassignment, so the one-batch Alpha/Beta/Alpha/Internal
distribution cannot be executed without an architectural change (per-item
processing authorization and an approved PE reassignment path), which this gate
forbids. PO decision required on: (a) accepting a revised Gate-3 scenario that
reflects the batch-party model (the achievable evidence above), or (b) deferring
Gate 3 to a V1.3+ item-level processing-party change. No code was changed and
no commit/push was made. Gates 4–5, WS5 and Phase 6 were not started.

   snapshot `source_item_id` NULL.
