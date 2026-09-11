# CarbonTally WS4 — Gate 3 Final End-to-End Acceptance Report
## One-Batch Multi-Party Processing Isolation + Reassignment

- **Date:** 4 September 2026
- **Nature:** Acceptance test only — **no application, SQL, RLS, API, UI, D38/D39/D40, workflow or blueprint change was made**.
- **Precondition met:** WS4E readiness report (`CARBONTALLY_WS4_GATE3_WS4E_FINAL_READINESS_REPORT.md`) declared **GATE 3 READY — NOT EXECUTED**; all 16 readiness items passed. This report is the execution of that Gate.

---

## 1. Gate Objective

Prove, on the **real running CarbonTally application**, that one batch can contain work items processed by different processing parties (PE Alpha, PE Beta, CarbonTally Internal) while preserving item-level authorization, PE isolation, batch-default fallback, item-level overrides, assignment/reassignment, assignment history, the single-open invariant, immutable processing origin, actor attribution, audit evidence, customer isolation, UI correctness and PE security.

## 2. Environment

- **Real frontend:** React dev server `http://localhost:3000` (compiled from source, connected to the real API).
- **Real backend:** FastAPI `http://127.0.0.1:8050` (656 routes) on the working tree (4A–4D changes, no Gate-3 changes).
- **Real database:** Supabase PostgreSQL `127.0.0.1:54426` (PostgREST/Auth `127.0.0.1:54425`).
- **Real authentication:** Supabase Auth email/password for `staff-admin.demo`, `operator.demo`, `pe-manager-1.demo` (PE Alpha), `pe-manager-2.demo` (PE Beta).
- **Real browser automation:** headless Chromium (Playwright) driving the actual UI for every UI assertion and screenshot.
- **Real HTTP/DB evidence:** authenticated requests and direct PostgreSQL inspection.

## 3. Fixture

Disposable org `WS4 GATE3 Fixture (disposable)` containing:

- **Batch `G3-Mixed-Batch` — batch default = PE Alpha** (`entity_id` set, `assigned_to` NULL):
  - A `g3-A.csv` → **no item override** (effective Alpha by batch default)
  - B `g3-B.csv` → item-level **Beta** (override)
  - C `g3-C.csv` → item-level **Alpha** (later reassigned **Alpha → Beta** in Test 6)
  - D `g3-D.csv` → item-level **CarbonTally Internal** (`operator.demo`), later **Internal → Alpha → Internal** (Test 8)
  - F `g3-F-fallback.csv` → **batch-default fallback** then item-level override **→ Beta** (Test 9)
  - G `g3-G-ui.csv` → assigned **Beta through the real Operations UI** (Test 1/13)
- **Batch `G3-Unassigned-Batch`** (no default, no assignment) with item U — unassigned-work tests.

Effective assignment produced: A→Alpha(default), B→Beta(item), C→Alpha(item)→Beta, D→Internal(item), F→Alpha(default)→Beta(item), U→unassigned.

## 4. Assignment Verification

Real D38 HTTP (`POST /api/v3/ops/items/{id}/work/assign`) and one real **UI** assignment (G→Beta via the Operations Assignments tab). HTTP 200 for B→Beta, C→Alpha, D→Internal and the UI/API G→Beta; persisted open ledger rows created with the acting `staff-admin` actor; audit `work_item:assign` recorded. UI rows displayed **batch default / item assignment / effective processor** for every item.

## 5. PE Alpha Isolation

Initial state (before reassignments): Alpha `/pe/work` 200; `/pe/batches/{b1}/items` contained exactly {A, C, F}; B, D not enumerated. Direct access: `A → ALLOW`, `C → ALLOW`, `B → DENY (403)`, `D → DENY (403)`. After Test-6 reassignment C→Beta and Test-9 F→Beta, Alpha sees only A (its remaining fixture item). Verified in HTTP and in the real Alpha browser UI (screenshots `01/02/06`).

## 6. PE Beta Isolation

Initial state: Beta `/pe/batches/{b1}/items` = {B} only; A, C, D denied (403). After reassignments Beta legitimately gains C, F and the UI-assigned G; A and D remain denied. Verified via HTTP and the real Beta UI (screenshots `03/07`).

## 7. Internal Processing

The authorised internal operator (`operator.demo`) opened the D workspace (`GET /ops/items/D/workspace` 200) and **started** D (200) inside the Alpha-defaulted batch; the operator was denied on Alpha/Beta-effective items A/B/C/F (403). After D was reassigned to Alpha, the operator's processing start was denied; after the return reassignment the operator regained access (workspace 200, effective internal). PEs could not start/process D (403). Internal UI workspace rendered (screenshot `04`).

## 8. Reassignment

- **PE→PE (Test 6):** C Alpha→Beta via `/work/reassign` → 200. Before: Alpha ALLOW / Beta DENY. After: Alpha DENY (403) / Beta ALLOW (200). Exactly one open row; the closed Alpha row remains in history with `previous_processing_entity_id = Alpha`; reassign actor = `staff-admin`; audit `work_item:reassign` recorded.
- **PE↔Internal (Test 8):** D Internal→Alpha (200; Alpha gains, operator loses start) then Alpha→Internal (200; internal regains, Alpha denied). History = 3 rows (assign + 2 reassigns) with correct `previous_*`; single open.
- **Batch-default override (Test 9):** F (batch default Alpha) ALLOW Alpha / DENY Beta; after item-level F→Beta: Alpha DENY / Beta ALLOW; batch default column unchanged.
- **PE cannot reassign (Test 7):** PE Alpha/Beta attempts at `/api/v3/ops/items/{id}/work/{assign,reassign}` → **403**.

## 9. Processing Origin

Verified immutable for both reassigned items: C was PE-originated by Alpha (`PROCESSING_ENTITY` / Alpha at first PE touch) and stayed `PROCESSING_ENTITY`/Alpha after reassignment to Beta; D stayed `CARBONTALLY_INTERNAL`/NULL through Internal→Alpha→Internal. Assignment changes never rewrote `processing_origin`/`processing_entity_id`.

## 10. Audit / Provenance

Persisted `audit_trail` rows (`table_name='manual_extraction_item'`, action types `work_item:assign` / `work_item:reassign`, `record_id` = item, `performed_by` = acting admin uuid) exist for every assignment/reassignment; history survives reassignment; the API `GET /ops/items/{id}/work` returns current + history + effective + origin. No parallel audit mechanism was introduced.

## 11. Customer Boundary

PE Alpha and PE Beta could not enumerate/access: an unrelated customer org's internal batch (absent from both `/pe/work` listings; `/pe/batches/{…}/items` 403), an unrelated customer item (`/pe/items/{…}/work` 403), the unrelated org profile (403), the fixture's unassigned batch (403), or internal-only work. Processing fixture work never granted customer-wide access.

## 12. UI Verification

- **Operations UI (Tests 1, 13):** Assignments tab opened the mixed batch and rendered per-row `Batch default: …`, `Item assignment: …`, `Effective: … (item assignment|batch default)` matching the API exactly (no local calculation). A real **UI assignment** of G→Beta succeeded and the row refreshed to Beta. Final rows: A=Alpha(default), B=Beta, C=Beta (history 2), D=Wendy Cullen (internal), F/G=Beta. Screenshots `01, 05, 05b`.
- **PE UI (Test 14):** Alpha `/pe/assignments` showed only its items (initial A/C, final A) with **no** assignment/combobox controls; Beta showed only Beta items (initial B, final B/C/F/G), no Ops controls. Screenshots `02, 03, 06, 07`.

## 13. HTTP Verification

All 4E/4C-style negative and positive HTTP checks executed against the real API: item assignment/reassignment 200 with actor; cross-PE item/batch/workspace reads 403; unassigned batch PE access 403; internal operator D start 200 and PE-effective start 403; PE Ops assign/reassign 403; unrelated customer endpoints 403. See `/tmp/gate3_seed_out2.txt`, `/tmp/gate3_mutate_out3.txt`, `/tmp/gate3_core_evidence.json`, `/tmp/gate3_mutate_evidence.json`.

## 14. Database Verification

Direct PostgreSQL assertions after all scenarios: exactly **one open** `work_item_assignments` row per actively assigned item (B, C, D, F — and later G); A and U have none; closed history retained with correct `previous_assigned_to`/`previous_processing_entity_id`; C history = 2, D = 3; `processing_origin`/`processing_entity_id` immutable; audit events present with actor; batch default (`entity_id = Alpha`, `assigned_to NULL`) unchanged; effective assignment matches the API and UI.

## 15. Cleanup / Baseline

All fixtures, temporary assignments, notifications and fixture audit rows were removed; test-created processes (backend, frontend) stopped; residual sweep **zero** (`fixture_orgs 0 · fixture_batches 0 · fixture_items 0 · ledger_total 0 · notifications_total 0 · recent work_item audit 0`). Exact baseline restored:

```text
emission_factors = 7,049   organizations = 975
manual_extraction_items = 260   manual_extraction_batches = 56
work_item_assignments = 0   conversations = 34
messages = 52   participants = 62   notifications = 0
e2e_auth_users = 0   schema migrations = 46
```

Investor/demo data untouched.

## 16. Acceptance Matrix

| Acceptance criterion | Result | Evidence |
| --- | --- | --- |
| One batch supports multiple effective processing parties | **PASS** | Fixture b1 simultaneously held Alpha (A), Beta (B), Alpha (C) and Internal (D) effective assignments; isolated and enumerated correctly |
| Item assignment overrides batch default | **PASS** | Test 9 (F default Alpha→override Beta; Alpha DENY/Beta ALLOW); B/C/D item overrides; A default fallback |
| Alpha sees only Alpha-effective items | **PASS** | Seed phase + UI (`/pe/work`, batch items {A,C,F}; then {A}); B/D never listed |
| Beta sees only Beta-effective items | **PASS** | Seed phase + UI ({B}; then {B,C,F,G}); A/D never listed |
| Internal sees only authorised internal items | **PASS** | D ALLOW (workspace + start 200); A/B/C/F DENY (403) |
| Cross-PE access is denied | **PASS** | Direct item/batch/workspace reads 403 (Alpha↔Beta, both on D) |
| Unassigned PE access is denied | **PASS** | G3-Unassigned-Batch absent from both `/pe/work`; direct access 403 |
| Operations can assign/reassign items | **PASS** | HTTP assigns (B/C/D/F) + real **UI** assignment (G→Beta) with persisted ledger + audit |
| PE cannot assign/reassign | **PASS** | PE Alpha/Beta Ops assign/reassign → 403 |
| PE→PE reassignment works | **PASS** | C Alpha→Beta: Alpha loses, Beta gains, previous + history retained |
| PE↔Internal reassignment works | **PASS** | D Internal→Alpha→Internal with access transitions each way |
| Assignment history is preserved | **PASS** | C history 2 rows; D history 3 rows; closed rows retained with `previous_*` |
| Single-open invariant holds | **PASS** | Exactly one open row per actively assigned item after every mutation |
| Processing origin remains immutable | **PASS** | C `PROCESSING_ENTITY`/Alpha and D `CARBONTALLY_INTERNAL`/NULL unchanged across reassignments |
| Actor attribution is correct | **PASS** | `assigned_by`/audit `performed_by` = acting staff-admin uuid on assign + reassign |
| Audit evidence is correct | **PASS** | `audit_trail` `work_item:assign`/`work_item:reassign` rows present and surviving |
| Operations UI shows effective assignment | **PASS** | Assignments tab rows show batch default / item assignment / effective; UI reassign refreshed row |
| PE UI remains assignment-scoped | **PASS** | PE `/pe/assignments` shows only own effective items; no Ops assignment controls |
| Customer isolation remains intact | **PASS** | Unrelated customer org/batch/item/profile denied to both PEs (403); no customer-wide access |
| Real DB state is correct | **PASS** | PostgreSQL assertions on ledger/history/previous/origin/audit/default/effective |
| Exact baseline restored after cleanup | **PASS** | Residual sweep zero; baseline counts exact |

Total: **63 automated acceptance checks executed with 0 failures** (seed/initial HTTP-DB 22, mutate HTTP-DB 22, browser pass 1 = 11, browser pass 2 = 8).

## 17. Defects / Findings

**No product defects found. No critical security failure.** Non-blocking notes:

1. The Operations Assignments row labels render full human-readable party names (e.g. “Processing Entity Alpha Ltd”, “Wendy Cullen”), not internal IDs — expected product behaviour; the acceptance scripts were written to match the API/UI canonical values.
2. The PE target dropdown lists all **active** Processing Entities (demo + test entities); it never lists organisations or inactive entities (server re-validates `active` on every assignment).
3. Transient local tooling issue during evidence capture (a screenshot helper initially wrote to a directory path and two runs hit a one-off browser-context closure) — re-run cleanly with corrected helper; not an application defect.
4. Fixture CSV items carry no stored document, so the internal item workspace was evidenced via the workspace header/data panes (no PDF viewer download); document handling was accepted in earlier WS gates and is out of this Gate's scope.

## 18. FINAL GATE RESULT

**GATE 3 — PASSED**

Every acceptance criterion is satisfied with real-stack evidence: browser screenshots (`/tmp/gate3_shots/01…07`), HTTP + DB + audit evidence (`/tmp/gate3_seed_out2.txt`, `/tmp/gate3_mutate_out3.txt`, `/tmp/gate3_core_evidence.json`, `/tmp/gate3_mutate_evidence.json`, `/tmp/gate3_bp1a/bp1b/bp1c/bp2.json`). Cleanup restored the exact baseline. Gate 3 is submitted for PO acceptance; no commit/push was made.
