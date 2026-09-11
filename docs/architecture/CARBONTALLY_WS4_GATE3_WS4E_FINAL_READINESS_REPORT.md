# CarbonTally WS4 / Gate 3 — Workstream 4E Report
## Final Pre-Gate-3 Verification — Real-DB Regression + Gate 3 Readiness

- **Date:** 4 September 2026
- **Basis:** PO accepted Workstreams 4A (DB/RLS), 4B (D38 service), 4C (HTTP/API), 4D (Operations UI). This workstream was **verification only** — no schema, RLS, D38, service, API, UI, workflow, origin, D40 or blueprint change was made.
- **Scope executed:** (A) real-database regression of the Workstream 4D SQL fix (`list_batches_with_open_entity_item`) against the real local stack; (B) Gate 3 readiness inspection producing the required checklist.
- **Earlier blocked Gate 3 attempt reviewed:** `docs/architecture/CARBONTALLY_WS4_GATE3_ARCHITECTURE_RECONCILIATION.md` and the blocked-attempt evidence (`/tmp/gate3_report_tail.md`, `/tmp/gate3_evidence.json`) — that block was the pre-4A batch-level single-party conflict, now resolved by the accepted item-level model.
- **No commit/push was made. Gate 3 was NOT executed.**

---

## 1. Purpose

1. Verify, against the **real local database** (Supabase PostgreSQL `127.0.0.1:54426`, FastAPI `127.0.0.1:8050`, authenticated HTTP), that the 4D fix to `backend/data/manual_extraction.py::list_batches_with_open_entity_item` (a) no longer mis-builds the batch column list and (b) binds its `$1` argument — and that `GET /api/v3/pe/work` and the PE work surface behave correctly under the approved effective-assignment rule (open item assignment → batch default → unassigned).
2. Confirm the current implementation can support the intended Gate 3 fixture **without further architecture or feature changes**, and produce the readiness checklist with evidence.

## 2. Real-DB Regression (Tests A1–A7)

Disposable fixture (org `WS4 4E Fixture (disposable)`): **one batch defaulted to PE Alpha** holding A (batch default, no ledger), B (item-level → PE Beta), C (item-level → PE Alpha), D (item-level → CarbonTally internal operator); plus a second **unassigned batch** (no PE default, no assignment) with item U. Real identities: `staff-admin.demo`, `operator.demo`, `pe-manager-1/2.demo`; all assignment/reassignment performed through the authorised D38 HTTP contract; state inspected through the API and directly in PostgreSQL.

Result: **26 checks — 0 failures** (evidence `/tmp/ws4e_regression_out.txt`).

| Test | What was verified | Result |
| --- | --- | --- |
| **A1** | `GET /api/v3/pe/work` for PE Alpha (which has effectively assigned items) returns **HTTP 200** (previously HTTP 500 `column b.i does not exist`) | PASS |
| **A2** | Per-batch `item_count` reflects effective assignment: Alpha sees b1 with `item_count = 2` (A default + C item-level); Beta sees b1 with `item_count = 1` (B only) | PASS |
| **A3** | Mixed batch does **not** cause cross-PE enumeration: Alpha enumerates exactly {A, C}, Beta exactly {B}, internal D is in neither list; cross-PE item reads (`pe/items/{b}/work` by Alpha, `{a}` by Beta, `{d}` by both) → 403 | PASS |
| **A4** | PE Alpha sees only Alpha-effective work ({A, C}; D never surfaced) | PASS |
| **A5** | PE Beta sees only Beta-effective work ({B}) | PASS |
| **A6** | Unassigned/no-assignment work (batch b2 + item U) is **not** surfaced to either PE (`/pe/work` absence and direct batch read → 403), while remaining visible to the authorised internal operator queue | PASS |
| **A7** | Fix did not change unrelated batch behaviour: Alpha's pre-existing PE work list/counts unchanged before vs after the fixture; the Ops batch-items list still returns the full mixed batch; the internal entity-extraction batch listing (default branch) still returns the PE-defaulted batch | PASS |

Additional evidence collected on the same fixture (used in §4):
- Internal operator opens the workspace of **D** (internally assigned item in a PE-defaulted batch) and **starts** extraction → 200; start denied (403) for Alpha-default A and by both PEs for D.
- **Reassign C Alpha→Beta** through `/api/v3/ops/items/{c}/work/reassign` → 200; effective becomes Beta (item); Alpha loses C; Beta gains C; **exactly one open** ledger row; history retains `[reassign, assign]`; `current.previous_processing_entity_id = Alpha`.
- **Processing origin immutable:** C was PE-originated by Alpha (`PROCESSING_ENTITY` / Alpha set at first PE touch) and remained `PROCESSING_ENTITY`/Alpha **after** the item-level reassignment — the assignment change did not rewrite origin.
- **Actor attribution:** reassignment history `assigned_by` = the acting `staff-admin.demo` user id.
- **Audit:** `public.audit_trail` contains `work_item:assign` + `work_item:reassign` rows for the reassigned item (action_type, record_id of the item).

## 3. Data Baseline

Before and after verification (exact, both identical):

```text
emission_factors = 7,049     organizations = 975
manual_extraction_items = 260    manual_extraction_batches = 56
work_item_assignments = 0    notifications = 0
conversations = 34  messages = 52  conversation_participants = 62
e2e_auth_users = 0  migrations = 46
```

Cleanup performed by the fixture teardown (org cascade + item-scoped ledger/notification/audit removal). Residual sweep after teardown: `fixture_orgs 0 · fixture_batches 0 · fixture_items 0 · ledger_total 0 · notifications_total 0`. A further sweep also removed 17 **orphaned** `work_item` audit rows left by the earlier disposable 4C/4D fixtures (rows whose `record_id` no longer existed in `manual_extraction_items`); remaining `work_item` audit rows in the 12-hour window: **0**. Investor/demo data untouched.

## 4. Gate 3 Readiness Checklist

| Requirement | Ready? | Evidence |
| --- | --- | --- |
| Item-level assignment | **READY** | 4C assign/reassign dual-target endpoints (38-check HTTP matrix); 4E setup assigns B→Beta, C→Alpha, D→Internal — all HTTP 200 with open ledger rows; 4B service tests |
| Batch fallback | **READY** | 4E item A (no ledger row) is effectively Alpha via **batch default** and counted in Alpha's `item_count`; API `effective.source = 'batch'`; 4D UI shows batch default as context |
| Mixed-party batch | **READY** | The exact Gate-3 shape (ONE batch, Alpha/Beta/Internal simultaneously) was exercised in 4E (batch b1) and 4C/4D; per-item effective map proves overrides work |
| PE isolation | **READY** | 4E A3–A6: Alpha {A,C}, Beta {B}, D hidden, unassigned hidden, cross-item/batch reads 403; 4C T12 cross-PE enumeration denied |
| Internal processing | **READY** | 4E: internal operator starts D in a PE-defaulted batch (200); internal start of Alpha-default A denied (403); PEs cannot start D (403); 4D UI test 8 |
| PE→PE reassignment | **READY** | 4E: C Alpha→Beta (200, Alpha loses, Beta gains, single open, previous retained); 4C T2/T8; 4D UI reassign-to-PE path |
| PE↔Internal reassignment | **READY** | 4E: D assigned internal in PE-default batch; 4C T3/T9/T10 (Beta→Internal, Internal→PE) and 4D UI-path matrix (PE→Internal, Internal→PE) |
| Assignment history | **READY** | 4E history `[reassign, assign]` + `previous_processing_entity_id`; `GET /ops/items/{id}/work` returns current+history+effective+origin; UI history panel (4D) |
| Single-open invariant | **READY** | 4E DB check = exactly 1 open row after each mutation; partial unique index (4A); repeated 4B/4C/4D checks |
| Processing origin | **READY** | 4E origin immutability probe (PE-origin item unchanged after item-level reassign); V1.2 origin design + earlier reports |
| Audit | **READY** | 4E `audit_trail` rows `work_item:assign`/`work_item:reassign` with actor; 4C audit-with-actor evidence |
| Customer isolation | **READY** | 4A RLS six-case matrix (customer org isolation via PostgREST); 4E A6 (PE cannot reach another org's unassigned batch — 403) and 4C T12 workspace/batch isolation; PE never granted customer capability (v3_pe) |
| Operations UI | **READY** | 4D: Ops Assignments tab displays batch default / item assignment / effective processor per row and reassign controls; 19 jest tests + 21-check UI-path HTTP matrix |
| PE UI | **READY** | 4D: PE work pages render only server-reported effectively assigned items; no Ops assign/reassign controls (test + `/pe` redirect); 4E `/pe/work` 200 |
| Real DB | **READY** | 4E real-DB regression 26/26 on the local stack; 4C real-HTTP matrix 38/38; 4A PostgREST RLS 6/6 |
| Cleanup | **READY** | Exact baseline before/after; residual sweep zero (incl. orphaned fixture audit rows) |

## 5. Remaining Blockers

**No blockers.** The Part A real-DB regression exposed no defect, and the readiness inspection found no missing feature: every checklist item is READY. Items deliberately kept outside this workstream and not blockers:

- **Gate 3 execution itself** (browser/UI + HTTP + DB + audit) remains to be run by the next bounded task after PO review.
- **D40 entity-assignment notifications** remain a separate bounded task (unchanged by design; internal-staff notifications already flow).
- Optional future hardening (not required for readiness): a committed real-DB data-layer regression test for `list_batches_with_open_entity_item`/`/pe/work` (this workstream provides live evidence via `/tmp/ws4e_regression_out.txt`; the hermetic suites use repository fakes and cannot execute the SQL).

## 6. Recommended Gate 3 Procedure

The next bounded task should execute the literal Gate 3 fixture through the real application (browser/UI + HTTP + DB + audit), using disposable identities/org/PE assignments and full cleanup, proving:

1. **Fixture:** one batch (disposable customer org; batch default Alpha where applicable) with **A→PE Alpha, B→PE Beta, C→PE Alpha, D→CarbonTally Internal** created via the Ops UI/API (`/api/v3/ops/items/{id}/work/assign` with `entity_id`/`assigned_to`).
2. **Assignment/overrides:** verify item-level open ledger rows, the batch default where applicable, and that item assignments override the default (API `effective` + DB `work_item_assignments`).
3. **Isolation (browser + HTTP):** Alpha sees A and C only, Beta sees B only, neither sees D (`/pe/work`, `/pe/batches/{id}/items`, PE workspace deep links; direct cross-item URLs → controlled 403).
4. **Internal processing:** the authorised internal operator opens and processes D in the PE-defaulted batch (start/extract 200); Alpha and Beta cannot process D (403).
5. **Reassignment (UI + API):** reassign **Alpha → Beta** on one item from the Operations Assignments tab and via `/work/reassign`; verify Alpha loses access, Beta gains it, history remains with `previous_*`, exactly one open assignment, audit `work_item:reassign` with the acting internal actor.
6. **Origin:** confirm `processing_origin`/`processing_entity_id` unchanged by the reassignment (DB before/after).
7. **Customer boundary:** negative probes proving the PEs cannot reach unrelated customer organisations/data (cross-org 403s).
8. **UI:** Operations Assignments rows display batch default, item assignment and effective processor (mixed batch); PE UI lists only its own effectively assigned work with no Ops controls; capture screenshots at representative widths for the report.
9. **Cleanup:** teardown fixture, verify the §3 baseline exactly, sweep residuals to zero.
10. **Report** each checklist row with evidence and statuses; do not claim acceptance without PO sign-off.

## 7. Gate Status

**GATE 3 READY — NOT EXECUTED**

Gate 3 was not executed in this workstream and is not claimed as passed. On PO review of this readiness report, the next bounded task may run the Gate 3 procedure above.

## Git

No commit/push. No repository file was modified by this verification workstream (evidence lives under `/tmp/ws4e_*`); the pre-existing uncommitted 4A–4D set remains as-is.
