# CT-PO-P12-STEP2-COMPLETION-VERIFICATION-20260924

**Reference:** `CT-PO-P12-STEP2-COMPLETION-VERIFICATION-20260924`
**Date:** 2026-09-24
**Governing workplan:** `CT-PO-P12-INVESTOR-DEMO-4STEP-WP-20260924` — **STEP 2 completion pass**
**Status:** STEP-2 DELIVERABLE — completion verification (addendum to the Step-2 record set)
**Production deployment:** **NOT AUTHORIZED**

---

## 0. Scope and boundaries

This pass performed **only** the Step-2 completion objectives A–H. No UI, presentation,
navigation or product work was undertaken. **Step 3 was NOT started.**

```text
starting SHA : d4b8e567aaca3280805d7511e43e03ffbba962e8
branch       : p8-release-reconciled
product code : UNCHANGED  (git diff 35eb7ba..HEAD -- ':!docs' ':!tools/demo_lab' is EMPTY)
```

Protected environments verified unchanged: `postgres` (116 tables / 975 orgs / 1,343
users), `carbontally_test` (117 / 15 / 717), `carbontally_qa_phase8` (133 / 25 / 498).

## 1. Objective results

| # | Objective | Result |
| --- | --- | --- |
| **A** | Second processing entity + S-4 | **PASS** — PE Alpha + PE Beta provisioned through the harness manifest; S-4 exercised and **DENIED** in both directions |
| **B** | Internal staff role for support messaging | **PASS** — `admin` now carries the release's own `can_manage_staff` key; positive **201**, negative **403** |
| **C** | Real reassignment evidence | **RESOLVED — Outcome 3**: the ops path records a reassignment as a **new `work_item_assignments` row**, not in `reassignment_history`; `work/reassign` returned 200 and the assignment row set changed accordingly. No history row was fabricated. |
| **D** | Partial release | **RESOLVED — contract reading**: release semantics close the current lease row (`work/release` → 200, row `closed`); there is **no partial-quantity release** in the assignment model (assignment is per work item, not per quantity) |
| **E** | Insight interaction persistence | **RESOLVED — tool-invoke is the authoritative execution record**: `POST /api/v3/insight/tools/invoke` returns the full `ToolResult` (status/contract_version/data/references/invocation) and does **not** write `carbontally_insight_interactions`; the I4 conversation route persists conversation + messages (1 + 2 present). No rows fabricated. |
| **F** | Fold D-2-03 / D-2-04 into the harness | **DONE** — see §2 |
| **G** | Second full reset/reprovision cycle | **EXECUTED** — repeatability **NOT demonstrated** (policy-count mismatch); see the Repeatability record |
| **H** | Disposable-clone integration verification | **EXECUTED, NOT PASSING** — see §3 and the integration record |

## 2. Harness changes made (demo-lab tooling only)

| ID | Change | Evidence |
| --- | --- | --- |
| **D-2-03** | `run_demo_lab.sh` re-ordered: **factors load before the backend starts**, with a printed "factors visible to the worker" count. The backend-restart workaround is no longer required. | the Cycle-2 PDF and tabular seeds produced real mapping **without** any manual restart |
| **D-2-04** | `t3_scenarios._multipart` now derives the upload part's content type from the filename extension (`_UPLOAD_CONTENT_TYPES`) instead of hardcoding `application/pdf` | the Cycle-2 CSV was stored `file_type=SPREADSHEET` and reached `_extract_csv` |
| **D-2-04 (new command)** | Added a documented **`seed-tabular`** subcommand that writes the tabular CSV, records its SHA-256 provenance, uploads it and enqueues the pipeline — no out-of-repo script needed | `seed-tabular`: `upload_status 201`, `line_items_type "array"`, `evidence_lines 2`, `snapshots 2`, `snapshots_with_line_link 2` |
| **D-2-06 (follow-up)** | `_clone_auth_schema_structure` now tolerates auth objects that depend on the *release* schema (e.g. a trigger calling `public.sync_auth_user_to_public_users()`), failing loudly only if `auth.users` was not created | Cycle 2 reprovisioned past the point that had aborted its first attempt |
| **D-2-07 (new finding)** | `stack.py::ensure_grants` (**line 317**) blanket-grants `INSERT, UPDATE, DELETE ON ALL TABLES … TO authenticated` **after** the migrations, re-granting privileges the RLS-4A/4B and D-4 migrations deliberately revoke. RLS is still enabled → **privilege-posture fidelity** gap, not a data-exposure hole. | 9 integration tests fail with `DID NOT RAISE InsufficientPrivilegeError`; the clone shows `authenticated` holding INSERT on those tables while `relrowsecurity = true` |

## 3. Verification evidence (Cycle-2 canonical environment)

### 3.1 S-4 — PE Alpha ↔ PE Beta (real API, real tokens)

```text
item e4b14143… assigned to PE Alpha via POST /api/v3/ops/items/{id}/work/assign → 200
PE Beta → GET  /api/v3/pe/batches/{alpha_batch}/items   → 403 "Batch is not assigned to this processing entity"
PE Beta → GET  /api/v3/pe/items/{alpha_item}/workspace  → 403 "Item is not effectively assigned to this processing entity"
PE Beta → POST /api/v3/pe/items/{alpha_item}/work/claim → 403 (same)
```

Both directions of frozen-scope case **S-4 are DENIED**. (`GET /api/v3/pe/batches`
returned 404 — "Not Found", not a denial; no batch was entity-assigned to Beta then.)

### 3.2 Support messaging — positive and negative

```text
platform_admin (role admin, can_manage_staff = true)
  POST /api/v3/messaging/conversations {counterparty: "support"} → 201 (conversation created)
internal_operator (role operator, can_manage_staff = false)
  POST /api/v3/messaging/conversations {counterparty: "support"} → 403
  "Messaging requires an active membership in the organisation, an active consultant-client
   grant, or CarbonTally support/admin authority"
```

The previously recorded **409** ("No authorised CarbonTally support participant is
available") is **resolved** by granting the release's own `can_manage_staff` key to the
lab `admin` role — no new permission invented, no RLS weakened, no authorization bypassed.

### 3.3 Story A — arithmetic re-verified on the current release

| activity | quantity | unit | multiplier | kg CO₂e | method | version | factor set | line link |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Natural gas | 12181.4 | kWh (Net CV) | 0.2027 | **2469.169780** | direct_multiply | v1.0 | DEFRA-2025 | **yes** |
| Natural gas | 8420.0 | kWh (Net CV) | 0.2027 | **1706.734000** | direct_multiply | v1.0 | DEFRA-2025 | **yes** |

`12181.4 × 0.2027 = 2469.16978` reproduces the Step-1 frozen value **exactly**.

### 3.4 EV-01 chain re-verified after the second cycle

```text
CSV (SPREADSHEET, sha256 76707ddb…) → line_items[] = array
→ evidence_line_items = 2 (forward hook) → calculation_snapshots = 2 with
source_line_item_id populated on 2/2 → emissions_logs = 2
Source Evidence Viewer: GET /api/v3/evidence/line-items/{id} → 200, drill-down FULL
No direct insert, no backfill, derive_line_candidates untouched, P1 still `shadow`.
```

### 3.5 Insight (with data present)

```text
registry: 10 tools (closed catalogue)
insight_aggregation (2025)   → status = success
insight_aggregation (1990)   → status = no_data (reason no_rows_in_period)
calculation_snapshot_lookup  → status = success
```

### 3.6 Story D — honest failure (Cycle 2)

```text
blocked documents (manual_review) = 10 · tabular documents = 1
failure classes = ambiguous / no_match / clarification / completeness / validation
```

## 4. Security re-verification

`tools/demo_lab/verify.py` executed against the Cycle-2 environment:

```text
isolation rules enforced : 18/18
authorization probes     : PASS for the tested set
(the in-reprovision run reported status=0 for every probe because the backend was
 still starting; the post-start run reports PASS)
```

The actor population is now **14** (13 + `pe_beta_manager`) per the updated manifest, so
13/13 is no longer the expected context count.

**One item requires independent confirmation — NOT asserted as a finding either way:**

| Item | Observation | Status |
| --- | --- | --- |
| `GET /api/v3/reporting/audit-activity` for `internal_operator` | returned **200** with 15 org-scoped audit events | **UNCONFIRMED — expectation mismatch.** The `can_manage_staff` guard at `v3_reporting.py:279/291` belongs to a *different* staff-admin audit route; this org-scoped read may legitimately allow internal staff. Step-4 must confirm the intended authorization. **Not recorded as an unexpected ALLOW.** |

No other unexpected ALLOW was observed.

## 5. Remaining issues (complete list)

| # | Issue | Class | Blocking? |
| --- | --- | --- | --- |
| 1 | Repeatability not demonstrated (public policies **298 → 210**, −88) | environment / harness | **BLOCKING** |
| 2 | Disposable-clone integration suites executed but **21/92 failing** (9 privilege-posture, 6 FK precondition, 6 pre-existing test drift) | environment + pre-existing test drift | **BLOCKING (not proven green)** |
| 3 | `stack.py::ensure_grants` blanket re-grant contradicts the release privilege posture (**D-2-07**) | demo-lab harness | non-blocking (RLS still enforced) |
| 4 | 61 tables are `RLS enabled + zero policies` (fail-closed posture) | environment | non-blocking |
| 5 | `reassignment_history` not written by the ops path (Objective C, Outcome 3) | product/workflow contract question | non-blocking (documented) |
| 6 | No partial-quantity release exists in the assignment model (Objective D) | product contract question | non-blocking (documented) |
| 7 | `carbontally_insight_interactions` not written by the tool-invoke route (Objective E) | product contract question | non-blocking (documented) |
| 8 | `enqueue` returned **422 "body Field required"** for the CSV; the document was processed anyway (the upload path enqueues automatically) | API contract/harness | non-blocking (observed) |
| 9 | `uk-water` maps `no_match` although the corpus contract expects `EXPECTED_MATCHED` | data/contract | non-blocking |
| 10 | The Cycle-2 reprovision's `migrations_with_errors` was **not captured** (output truncated by `tail -30`) | process/measurement gap | non-blocking, must be fixed before the next cycle |
| 11 | `GET /api/v3/reporting/audit-activity` authorization expectation unconfirmed for `internal_operator` | security — to confirm | non-blocking (Step-4) |
| 12 | Documentation conflicts D-09/D-10/D-11/D-12/D-14/D-27 unchanged (dispositions preserved, none silently resolved) | documentation | PO decisions |

## 6. Gate input

All Step-2 objectives A–H were **executed**:

```text
A  second PE + S-4 ............ PASS   (403 both directions)
B  support staff role ......... PASS   (201 positive / 403 negative)
C  reassignment ............... RESOLVED (Outcome 3 — assignment-row model documented)
D  partial release ............ RESOLVED (contract: whole-lease release, no partial quantity)
E  Insight persistence ........ RESOLVED (tool-invoke result is the execution record)
F  harness folds .............. DONE   (D-2-03, D-2-04, seed-tabular, D-2-06 follow-up)
G  second full cycle .......... EXECUTED — repeatability NOT demonstrated
H  disposable integration ..... EXECUTED — NOT PASSING
```

Two mandatory criteria remain unsupported (**G** and **H**), so the final gate
decision is recorded in `CT-PO-P12-STEP2-IMPLEMENTATION-REPORT-20260924.md` §13.
