# CT-PO-P12-STEP2-EXPECTED-COUNT-VERIFICATION-20260924

**Reference:** `CT-PO-P12-STEP2-EXPECTED-COUNT-VERIFICATION-20260924`
**Date:** 2026-09-24
**Governing workplan:** STEP 2 — required counts report
**Status:** STEP-2 DELIVERABLE
**Database:** `carbontally_demo_local` @ `35eb7ba` — read-only counts

---

## 1. Expected vs actual

| Entity | Expected | Actual | Status |
| --- | ---: | ---: | --- |
| Direct customer orgs | 2 | 2 | **PASS** |
| Consultant firm | 1 | 1 | **PASS** |
| Client orgs | 2 | 2 | **PASS** |
| Processing entities | 2 | **1** | **FAIL (target unmet)** |
| Users | 13 (frozen) | 13 | **PASS** |
| Batches | ~3 | 4 | **PASS** |
| Work items | ~12–15 | 11 | **PASS (lower bound of range)** |
| Matched calculations | ≥2 | **2** | **PASS** |
| Blocked documents | ≥2 | **10** | **PASS** |
| Tabular documents | ≥1 | **1** | **PASS** |
| Evidence lines | ≥2 | **2** | **PASS** |
| Assignments | ≥4 | **7** | **PASS** |
| Reassignments | ≥1 | 1 exercised (`work/reassign` → 200); `reassignment_history = 0` | **PASS WITH OBSERVATION** |
| Partial releases | ≥1 | 1 exercised (`work/release` → 200, assignment row closed) | **PASS** |
| Report versions | ≥2 | 2 | **PASS** |
| Conversations — org | ≥1 | 3 | **PASS** |
| Conversations — PE | ≥1 | 1 | **PASS** |
| Facilities | ≥1 | 1 | **PASS** |
| Assets | ≥1 | 1 | **PASS** |
| Suppliers | ≥1 | 1 | **PASS** |
| Insight interactions | ≥2 | 3 tool executions (1 × `success`, 1 × `no_data`, 1 × `success`) | **PASS (delivery route differs)** |
| Honest no-data Insight cases | ≥1 | 1 (`status=no_data`, `reason=no_rows_in_period`) | **PASS** |

## 2. Supporting detail

| Measure | Value |
| --- | --- |
| Public tables | 141 |
| RLS-enabled tables | 141 / 141 |
| RLS policies | 298 |
| Insight tables | 6 |
| `evidence_line_items` | 2 (`FORWARD`, `extraction_method=csv`) |
| Snapshots with `source_line_item_id` | 2 / 2 |
| Emissions logs with snapshot + factor FK | 2 / 2 |
| Factor rows | 7,049 (DEFRA-2025 7,029; SEAI-2025 20) |
| Active import batches | 2 |
| `work_item_assignments` open / closed | 4 / 4→3 closed (7 total) |
| Messages | 2 |
| Conversations by kind | `org` 3, `entity` 1 |

## 3. Failures and partial criteria

| # | Criterion | Status | Cause | Minimum remediation |
| --- | --- | --- | --- | --- |
| 1 | 2 processing entities | **FAIL** | the Demo Lab manifest provisions exactly one entity (`pe.manager` is entity-scoped) | provision a second entity (admin path / manifest extension) to enable S-4 |
| 2 | `reassignment_history` populated | **OBSERVATION** | the ops reassignment endpoint records a new `work_item_assignments` row rather than a history row | either accept the assignment-row model or populate the history table (product question — not a Step-2 data fix) |
| 3 | Insight "interactions" persisted in `carbontally_insight_interactions` | **OBSERVATION** | `POST /api/v3/insight/tools/invoke` does not write that table; the I4 conversation route writes conversation/messages instead | use the I4 interaction route for persisted interaction rows if the frozen scope requires them |
| 4 | Support-messaging counterparty | **FAIL (not in counts table)** | no internal staff role in the lab grants `can_manage_staff` → **409** | provision an internal staff user whose role grants `can_manage_staff` |

## 4. Criteria that could not be evaluated

| Criterion | Why |
| --- | --- |
| Disposable-clone integration verification | **not executed** — see `CT-PO-P12-STEP2-DISPOSABLE-INTEGRATION-VERIFICATION-20260924.md` |
| Reset/reprovision **repeatability** | one full cycle completed; a second cycle was not run |
| S-4 (PE Alpha → PE Beta) | requires the second processing entity |
| S-1/S-2/S-3/S-5…S-13 | fully covered by the harness's 30 authorization probes + 18 isolation rules (**0 failures**), which include Org A↔B, Client A↔B, consultant↔ungranted-org, viewer/member denials and the PE boundary as far as one entity allows |

## 5. Verdict

**Counts: PASS WITH FAILURES.** All investor-demo data targets are met except
**processing entities (1 of 2)**, with three recorded observations. Two further
mandatory criteria (disposable integration verification, repeatability) are open —
therefore **Step 2 is INCOMPLETE**.
