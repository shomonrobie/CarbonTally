# CT-P8-S6 — S6 (visibility-first) IMPLEMENTATION + INDEPENDENT VERIFICATION

**Report ID:** `CT-P8-S6-IMPLEMENTATION-AND-IV-20260914-063`
**Date:** 2026-09-14
**Authority:** PO decision — *"S6 APPROVED: VISIBILITY-FIRST FIRST RELEASE"* (Option (b))
**Status:** **IMPLEMENTED + SELF-VERIFIED — AWAITING PO CLOSURE** (not self-closed)
**Subsystem:** Customer report lifecycle visibility (Phase 8 · S6)

---

## 1. What was authorised

Make the **already-existing** report lifecycle usable by customers through the product UI, with
**no** new reporting/calculation engine, **no** new lifecycle states, **no** comment capability,
and **no** change to retention, immutability, RLS, calculation or factor matching. The UI must
reflect authoritative persisted state.

## 2. Reconciliation performed before coding (as instructed)

Reconciled the S6 decision package against the actual repository:

| Finding | Consequence for this release |
|---|---|
| The report lifecycle **already existed end-to-end**: version rows with status, the state machine (`domain/report_lifecycle.py`), transitions `T3/T7/T8/T11/T12/T17`, per-action authority, append-only audit, and all five lifecycle endpoints (`v3_reports.py` lines 762–865) | S6 is **a UI + one additive read field**, not a new lifecycle |
| `ReportDetailPage.jsx` already loaded report + content + versions, and already rendered `EvidenceTrail` (drill-down visibility) | Reused; no duplicate surface created |
| `ReportDetailPage` showed versions **without their lifecycle state and with no actions** — the customer could not see or use the lifecycle | **This was the actual gap S6 closes** |
| Lifecycle mutations already return `allowed_actions`, but the **versions list did not** | The UI had no authoritative action source → would have had to *derive* rules in the browser, contradicting the PO's "UI must reflect authoritative state" instruction → one additive read field added (§4) |
| `allowed_actions(FINAL) == ['new_version']`; `APPROVED → ['finalize','new_version']`; `CHANGES_REQUESTED`/`REJECTED → ['new_version']` | **`new_version` is a real server action but is not in this release's approved action list** → surfaced as guidance, never as a dead button; raised back to the PO (§7) |
| Comment system: absent from the repository | Correctly not implemented; principles recorded (§3) |

**No genuinely new business/product decision blocked implementation.** `new_version` exposure was
the only action-list question, and it was resolved conservatively (not offered) *and* returned to
the PO rather than invented.

## 3. Comment principles recorded (not implemented)

Per the PO decision, the review-comment system is **not** implemented. The following are recorded
as the governing principles for the future capability:

1. Future comments use the approved **internal/shared visibility split**.
2. An unresolved comment/change request does **NOT** automatically block approval or finalisation.
3. **No blocking rule** may be introduced without explicit later PO approval.
4. Comments remain a **separate future capability** and must not expand the current S6 scope.

---

## 4. Files changed

| File | Change |
|---|---|
| `backend/api/v3_reports.py` (`list_report_versions`, lines 392–419) | **Additive, read-only**: each version row in `GET /api/v3/reports/{id}/versions` now carries `allowed_actions`, computed by the existing `domain.report_lifecycle.allowed_actions(status)`. No new endpoint, no schema change, no RLS change, no state added |
| `frontend/src/v3/api.js` (lines 168–208) | Five thin POST wrappers for the **existing** lifecycle endpoints (`submit`, `approve`, `request-changes`, `reject`, `finalize`) + `REPORT_LIFECYCLE_ACTION_CALLS` action→call map. No decision logic |
| `frontend/src/v3/reports/ReportLifecyclePanel.jsx` (**new**) | Customer lifecycle panel: persisted state + plain-English meaning, immutability lock notice, permitted actions, friendly 403/409 handling, version history |
| `frontend/src/v3/reports/ReportDetailPage.jsx` | Renders `<ReportLifecyclePanel reportId={id} versions={versions} onChanged={load} />`; imports it. Existing status/content/versions/evidence sections untouched |
| `frontend/src/v3/reports/reports.css` | Panel styles using the existing V3/D21 token convention + a narrow-viewport rule |
| `frontend/src/v3/__tests__/report-lifecycle-panel.test.jsx` (**new**) | 8 frontend reference tests |
| `backend/tests/unit/api/test_v3_report_lifecycle.py` | **+6** backend tests (§6) |

**Deliberately not changed:** `domain/report_lifecycle.py` (state machine) ·
`data/report_versions.py` (persistence) · all five transition endpoints ·
`services/disclosure_finalisation.py` (immutability) · retention / evidence / calculation / factor
matching · RLS · **no migrations added**.

## 5. Behaviour implemented

**State visibility** — the current version's **persisted** status is displayed with a plain-English
label and meaning: Draft, In review, Changes requested, Rejected, Approved, Final. Unknown values
fall through verbatim; nothing is inferred or prettified into a conflicting state.

**Version/history visibility** — a history table lists every version with its persisted state,
recorded timestamp and current marker.

**Permitted actions** — rendered strictly from the server-provided `allowed_actions` for the current
version. An empty server set shows *"No action is available to you on this version."* Actions
outside this release's list are **never rendered as dead buttons**.

**Submission for review** — `Submit for review` calls the existing `POST …/submit`; on success the
panel confirms and triggers a reload, so the displayed state is the **reloaded persisted** state,
never a locally assumed one.

**Approval/finalisation visibility** — `Approve` / `Finalize` (plus `Request changes` / `Reject`)
appear only when the server's set for the current state and the caller's authority permit.

**Immutability** — APPROVED/FINAL versions show *"This version is locked. Finalised and approved
reports cannot be edited."*, and the lock is **server-enforced** (verified: transitions → 409).

**Error handling** — 403 → *"You do not have permission to perform this action on this report."*;
409 → *"The report state changed while you were working on it. The current state has been
reloaded."* + automatic reload. No raw technical error reaches the customer.

**No comment capability** — no comment UI, no notes field, no text input, no comment endpoint; no
comment/thread artefact in any lifecycle payload.

## 6. Tests added and run

| Suite | Command | Result |
|---|---|---|
| Backend lifecycle + S6 API tests | `python -m pytest tests/unit/api/test_v3_report_lifecycle.py -q` | **37 passed** (31 pre-existing + **6 new**) |
| Backend API unit area (regression) | `python -m pytest tests/unit/api -q` | only the **2 known, PO-excluded `F-X1-2`** failures; **no new failures** |
| Frontend report panels | `npx react-scripts test --testPathPattern 'report-lifecycle-panel\|reports-page'` | **11 passed** |
| Frontend v3 suite (regression) | `npx react-scripts test --testPathPattern 'src/v3/__tests__'` | **21 suites / 203 tests passed** |

**New backend tests:** server-authoritative `allowed_actions` per version · actions unlock only when
the persisted state changes (version identity preserved) · FINAL offers only supersession and stays
immutable (409) · versions listing is org-scoped (cross-tenant → 403) · versions listing requires
authentication (401) · no comment/thread artefact in lifecycle payloads.

**New frontend tests:** state + server-action rendering only · submit calls the existing endpoint and
reloads · 403 shows a friendly message and never the raw text · APPROVED locked with `finalize`
offered · history renders each persisted state, no comment UI, no textbox · no dead button for
`new_version` · performable subset when the server offers both.


---

## 7. Independent verification against the PO's checklist

| PO verification requirement | Result | Evidence |
|---|---|---|
| Lifecycle state visibility | **PASS** | Panel shows the persisted status + plain-English meaning; tests assert each of the six ratified states renders; `test_version_listing_exposes_server_authoritative_allowed_actions` asserts the state itself |
| Version/history visibility | **PASS** | History table with version number, persisted state, timestamp, current marker; frontend history test |
| Permitted review/approval/finalisation actions | **PASS** | Actions come only from the server's `allowed_actions`; DRAFT→submit, REVIEWED→approve/request-changes/reject, APPROVED→finalize all asserted server-side and rendered client-side |
| Unauthorized access is denied | **PASS** | Unauthenticated → **401**; non-permitted role → **403** with a friendly message and **no** raw text (unit + frontend tests) |
| Tenant/entity isolation | **PASS** | Cross-org versions listing → **403**; transitions remain org-scoped (pre-existing tests + new listing test). No RLS or authorization code was modified |
| Finalized state remains protected/immutable | **PASS** | FINAL offers only the pre-existing supersession action; `submit`/`finalize` on FINAL → **409**; UI shows the lock notice. Immutability service untouched |
| UI reflects persisted authoritative state | **PASS (design-verified)** | The UI derives nothing: state and actions both come from the API; after every mutation the panel reloads from the server. Unknown states render verbatim |
| No comment functionality introduced | **PASS** | No comment UI/input/endpoint; payload-level test asserts no comment/thread artefact; frontend test asserts no textbox and no "comment" text |
| No regression to existing report workflows | **PASS** | Backend API unit area: no new failures; frontend v3 suite **203/203 pass**; `allowed_actions` is additive and `getReportVersions` has a single consumer |

### Verification limitations (stated honestly)

* **UI IV is automated-test-level, not browser-session-level.** No live browser session against a
  seeded environment was performed in this pass; responsive behaviour at the ratified viewports
  (1920→375) and keyboard/ARIA behaviour are covered by CSS/ARIA construction and automated tests
  only. A live-session pass is recommended before PO closure if browser evidence is required.
* **Backend integration (real PostgreSQL) run was not executed in this pass.** The affected backend
  change is read-only serialization already covered by six API unit tests; integration tests that
  consume the versions endpoint assert key-by-key (not full-shape), so the additive field cannot
  break them. `F-046-1` was honoured — **nothing was pointed at QA, demo, investor, or production**.

## 8. Findings encountered and recorded separately (not fixed)

Per instruction, unrelated findings encountered were **not** fixed:

1. **`F-X1-2` (unchanged, out of scope)** — the EF-E test-double drift still causes the **2** known
   `tests/unit/api/test_v3_phase_c_regressions.py` failures. Confirmed present before and after S6;
   **no new failures introduced**.
2. **`NEW — environment/runner observation`** — the full `tests/unit` suite stalled at ~9% for
   >7 minutes and was terminated for this pass. Cause not investigated (out of scope); the affected
   API unit area was run directly instead. **Not a code defect claim.**
3. **`S6-ACTION-1 — PO DECISION REQUIRED (no implementation made)`** — the server legitimately offers
   the **pre-existing** `new_version` action (supersede by a revised draft) from `CHANGES_REQUESTED`,
   `REJECTED`, `APPROVED` and `FINAL`. Creating a revised version from the UI is **not** in this
   release's approved action list, so it is **not** offered; the panel instead explains that a
   revised version is required. **Question for the PO:** should a later S6 increment expose
   "create revised version" using the existing endpoint? Awaiting a decision; nothing was invented.
4. **`NEW — build-configuration observation`** — `CI=true npx react-scripts build` fails with
   `Failed to compile` because CRA under `CI=true` treats warnings as errors, and the legacy
   codebase contains **108 pre-existing warning lines** across unrelated files (`src/App.js`,
   `src/v3/ops/AuditConsoleTab.jsx`, `src/v3/components/ui/DataTable.jsx`, `StaffRoster.jsx`, …).
   **None of the S6-touched files appear in the warning list**, i.e. S6 contributes **zero** build
   warnings. Not fixed (out of scope); recorded so a future build-hardening item can address it.

## 9. Scope compliance

Not implemented, as instructed: review comments and any blocking rule · RLS steps 3–5 · X4 · X5–X7 ·
X8 · S8 · I1 · D16/legacy · `F-X1-2` · `F-B3-7` · `F-4A1B-1` · production/G0-D · provider/runtime
introspection · Phase 9 · **OHD findings (untouched)**. No migration was added. Production and demo
environments were not modified.

## 10. Git / environment state

* Branch `main` · HEAD **`37b19d1`** · staged **0** · **no commits made** by this task.
* No secrets, tokens, signed URLs, credentials or environment files were added to the report or the
  repository.
* Work is uncommitted, pending PO closure.

## 11. Remaining work

1. **PO closure of S6** (this report is the closure artifact).
2. **`S6-ACTION-1`** decision — expose "create revised version" or leave it out.
3. Phase 8-X **X4** authorisation + scope (not begun — the PO's stop condition forbids starting it).
4. RLS `D-4`…`D-10`/`D-12` rulings (unchanged, still reached-and-waiting).
5. Optional live-browser IV pass against a disposable environment before closure.


---

## 12. PO CLOSURE (2026-09-14) — transcription of the PO decision

> **S6 — PO CLOSED / ACCEPTED.** *"I accept the S6 visibility-first implementation and
> verification reported in `CT-P8-S6-IMPLEMENTATION-AND-IV-20260914-063.md`."*

The PO's decision explicitly accepts: lifecycle state visibility · version/history visibility ·
**server-authoritative `allowed_actions`** · the existing review/approval/finalisation actions ·
authorization and tenant-isolation behaviour · finalized-state immutability enforcement · friendly
403/409 handling · absence of comment functionality · the regression results · and `F-X1-2`, the
unit-suite stall and the unrelated CI warning failures remaining **separately recorded and out of
S6 scope**.

The documented verification limitations are **accepted as limitations**, with the explicit
instruction: *do not claim live-browser or real-PostgreSQL verification that was not performed.*
This report already states both as limitations (§7) and makes no such claim.

### 12.1 `S6-ACTION-1` — PO ruling: DO NOT implement `new_version`

| Item | PO ruling |
|---|---|
| `new_version` in the **current S6 release** | **NOT to be implemented.** Recorded as a **future, separately bounded S6 increment** |
| Existing backend capability | **May remain available where it already exists**; the current S6 UI is **not** required to expose it |
| Absence from the current UI | **Not an S6 defect** |
| Future increment | Requires its **own bounded PO decision / authorization** |

**Status: S6 → PO CLOSED.** This section is a transcription only; no closure was self-declared and
nothing beyond the PO's decision is inferred. The previously recorded limitations remain
limitations, and the three findings in §8 remain recorded and **unfixed**.

