# WS4 Calculation/Validation Blocker — Root-Cause Diagnosis

Status: DIAGNOSTIC ONLY (no code, schema, validation, factor or workflow
changes made). Fixtures removed; baseline verified.

## 1. Reproduction

Isolated disposable fixture (internal origin), started at `pending`, driven
through the real operator workbench UI (`/ops/items/{id}`):

    pending → Claim stage → extraction entry (Supplier "V1.2 Acceptance Fixture
    Supplies Ltd", invoice E2E-2026-0001, 2026-01-15, line: Natural gas,
    12,500, kWh) → Save extraction → status `extracted` → reload → Save mapping
    (factor selected) → status `mapped` → Calculate.

Browser/DB-verified: `pending → extracted → mapped`, `extracted_data` and
`mapped_data.line_items[0].factor_id` persisted. Calculate did not advance the
item (status remained `mapped`; no emissions written).

## 2. Exact validation finding

The workbench displayed `Validation (1)` while the item was in `mapped`
**before** mapping had been saved (banner rendered from the workspace load's
server findings: `FACTOR_MISSING`, field `mapped_data.line_items[0].factor_id`,
severity error — `backend/engines/processing_workflow.py`
`_validate_line_items`). After mapping with a factor was saved and the page
reloaded, the workspace re-ran `validate_processing_item` and the banner
disappeared (findings = 0). The banner is therefore stale UI state, not a
persistent data problem.

## 3. Persisted extraction data

    supplier: V1.2 Acceptance Fixture Supplies Ltd
    invoice_number: E2E-2026-0001
    invoice_date / date: 2026-01-15
    currency: GBP
    line_items[0]: description "Natural gas supply", activity "Natural gas",
                   quantity "12500", unit "kWh", amount ""

## 4. Persisted mapping data

    mapped_data.line_items[0].factor_id = 121ec17d-2986-467b-a09a-6b4b78ead049
    mapped_data.line_items[0].activity_type = "Fuels > Gaseous fuels > Natural
        gas (100% mineral blend) (kg CO2e of CH4 per unit) [kWh (Gross CV)]"

## 5. Selected factor

Factor 121ec17d… (DEFRA-DESNZ 2025, Natural gas, kWh (Gross CV), CH4 basis)
from the canonical 7,049-factor set. No factor was modified.

## 6. Validation rule

`validate_processing_item(item)` (line-item path): header supplier + invoice
date required; per line activity/quantity(≥0)/unit required; when
`require_mapping`, every line needs a `factor_id` (item-level factor fallback).
All rules PASS once mapping is saved — evidence: zero findings after reload.

## 7. Browser Calculate request

**No `/calculate` request was ever emitted** (Playwright request capture
confirmed). The Calculate handler (`ExtractionPanel.run('calculate')`) first
calls `startItem(itemId, 'calculation')`; that call fails and the request
chain stops before `calculateItem`.

## 8. Backend response

The `start` (claim calculation stage) call is rejected because of the frozen
state machine in `backend/domain/partners.py`:

    "mapped": ("validating", "validated", "mapping")
    "validated": ("calculating", "mapping")
    "calculating": ("calculated", "validated")

`mapped` cannot transition to `calculating`. The UI code comment itself states
the contract: “the backend state machine requires
`validated → calculating → calculated`.”

## 9. Validation → calculation contract

- Blocking findings are represented as error-severity `ValidationFinding`
  objects; `has_blocking_findings()` gates the reviewer `validate_item`
  endpoint (`can_review`), which transitions `mapped → validated` when clean.
- Calculation requires current status `validated`; `calculate_item`
  (`can_process`) computes and persists the result via `CalculationEngine`.
- The reviewer-gated validate endpoint is the only resolution/advance path
  from `mapped`; there is no operator self-validate path.

## 10. Existing test coverage

Backend unit/API suites cover validate/calculate transitions from
`mapped/validated` states (state-machine and engine tests). They do not cover
the full operator workbench UI click-path from `mapped` → Calculate, which is
where the defect surfaces.

## 11. Frontend vs backend comparison

Frontend: operator workbench renders `Calculate` when status is `mapped`
(enabled — `mapped` is not in `LOCKED_STATUSES`) and attempts
`startItem(...,'calculation')`.
Backend: `mapped` is not an eligible source state for `calculating`, so the
start call is rejected (409-class) and the item stays `mapped`. The same
workbench disables Calculate for `validated`/`calculating`/`calculated`
(`LOCKED_STATUSES`), so there is no reachable UI route that legally performs
`validated → calculating → calculated`.

## 12. Root-cause classification

**F — Workflow/UI integration defect.**

Evidence: (a) `partners.py` transition map forbids `mapped → calculating`;
(b) `ExtractionPanel` runs `startItem('calculation')` from `mapped`;
(c) no browser `/calculate` request is emitted; (d) `LOCKED_STATUSES` prevents
the same panel from triggering calculation at the only legal source status
(`validated`); (e) secondary UI-staleness: the validation banner is not
refreshed after Save mapping until a page reload.

## 13. Evidence

- Browser PASS traces: `pending→extracted` (DB `extracted_by/at`), `→mapped`
  (DB `mapped_data.factor_id`).
- Browser capture: `AFTER_RELOAD_HAS_BANNER false`, `STATUS_HAS_MAPPED true`;
  no `/calculate` request observed.
- Code: `backend/domain/partners.py:69-72`; `backend/engines/processing_workflow.py`
  (line-item rules); `frontend/src/v3/ops/ExtractionPanel.jsx` `run('calculate')`
  and `LOCKED_STATUSES`; `backend/api/v3_operations.py` validate/calculate.

## 14. Recommended remediation (minimum, not implemented)

Enable a legal UI route for `validated → calculating → calculated`, e.g.:
(after a reviewer validates a mapped item) allow the operator/authorized actor
to trigger calculation from status `validated` — either by not locking
`validated` for the calculate control, or by an explicit “Calculate” action on
the reviewer/validated surface; and refresh workbench validation findings after
Save mapping.

## 15. PO approval

REQUIRED. Per instruction §18 no fix is implemented pending Product Owner
decision.

## 16–19. Impact

- V1.2 architecture: a UI-path correction only; no V1.2 model change. May still
  need PO confirmation that “calculation is intentionally automated” (WS4 §3)
  — no durable pipeline worker currently performs `validated → calculating`.
- Schema: none. Security: none. Factors: none (7,049 unchanged).

## 20. WS4 continuation

WS4 cannot legitimately pass the full browser E2E until a legal UI route to
calculation exists (either human-validated → calculate, or an observed
automated pipeline). All other WS4 gates remain in their previously reported
state.

---

# APPROVED REMEDIATION — IMPLEMENTED & VERIFIED

## Change (minimal, frontend-only)

1. `frontend/src/v3/ops/OperatorItemPage.jsx` — passes `onSaved={() => load(itemId)}`
   to the workbench panel so the workspace (item status + server validation
   findings) is refreshed after each successful save action.
2. `frontend/src/v3/ops/ExtractionPanel.jsx` — after each successful
   start/extract/draft/map/calculate action the panel calls `onSaved` (stale
   `FACTOR_MISSING` banner disappears once persisted mapping satisfies
   validation).
3. `frontend/src/v3/ops/ExtractionPanel.jsx` — staff-mode Calculate button is
   now gated to legal source states only: enabled at `validated`/`calculating`,
   disabled at `mapped`/`pending` (PE mode behaviour unchanged). The frozen
   state machine (`mapped → validated → calculating → calculated`) is respected;
   no `mapped → calculated` path is exposed.

Actor/capability model used unchanged: data-entry operator (`can_process`)
extracts/maps; internal reviewer (`can_review`) performs Validate
(`/ops/items/{id}/validate`, mapped→validated); operator then triggers
Calculate (`/ops/items/{id}/calculate`, validated→calculated).

## Browser verification (real UI, real personas, disposable fixture, from pending)

    PASS R1 operator reaches mapped via UI
    PASS R2 stale validation banner cleared after mapping save + refresh
    PASS R3 Calculate unavailable at mapped (legal gate)
    PASS R4 reviewer Validate action available at mapped
    PASS R5 reviewer validate succeeded (mapped → validated)
    PASS R8 Calculate enabled at validated
    PASS R9 /calculate request observed — HTTP 200, result co2e_kg persisted
    PASS R11 calculated status visible in workbench

Negative validation test (deliberately unmapped factor, real UI):

    PASS N0 invalid mapping saved (no factor)
    PASS N1 Calculate unavailable on invalid mapping
    PASS N1b Validate available
    PASS N2 blocking findings reported (no bypass)
    PASS N3 item did not reach calculated
    PASS N4 no calculate request attempted

## Files changed

- frontend/src/v3/ops/OperatorItemPage.jsx
- frontend/src/v3/ops/ExtractionPanel.jsx

No backend, schema, migration, factor, D38/D39/D40, role, capability or
security change. Emission factors remain 7,049; migrations 45.

## Integrity after teardown

organizations 975 · items 260 · batches 56 · assignments 0 · conversations 34
· messages 52 · participants 62 · notifications 0 · no fixture org/batch/issues.

## Remaining limitation

PE-origin full workflow (PE panel mode unchanged by design) was not re-run in
this remediation; PE Review/QC browser evidence from the accepted WS4 section
remains valid.
