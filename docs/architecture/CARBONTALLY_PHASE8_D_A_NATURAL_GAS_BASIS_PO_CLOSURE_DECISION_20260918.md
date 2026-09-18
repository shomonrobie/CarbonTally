# CarbonTally — Phase 8 · Step-2 Workstream D-A (Natural-gas calorific basis)
## PO DECISION RECORD — D-A CLOSED (2026-09-18)

**Task:** `CT-STEP2-D-A-PO-CLOSURE-036`
**Date:** 2026-09-18
**Authority:** PO review and acceptance of the independent verification report `CT-STEP2-D-A-NATURAL-GAS-VERIFY-035` (verdict **PASS**)
**Type:** DECISION RECORD — **no implementation, no code change, no test change, no factor-data change, no schema change, no migration, no deployment, no P1 activation**

**Evidence base (both artefacts published on `p8-release-reconciled`):**
* implementation report — `docs/cline/reports/CT-STEP2-D-A-NATURAL-GAS-034.md`
* independent verification report — `docs/cline/reports/CT-STEP2-D-A-NATURAL-GAS-VERIFY-035.md`

---

## 1. PO RULING

**D-A is CLOSED.** D-A is recorded as:

| Attribute | Status |
|---|---|
| Implementation | **IMPLEMENTED** |
| Independent verification | **INDEPENDENTLY VERIFIED** (report `-035`, verdict **PASS**) |
| Governance | **PO-CLOSED** |

Closure statement: **D-A PO CLOSED.**

## 2. ACCEPTED BEHAVIOUR (CarbonTally policy — formally accepted)

| Source evidence | Accepted ruling |
|---|---|
| Explicit **Gross CV / GCV** | → **Gross CV** factor basis |
| Explicit **Net CV / NCV** | → **Net CV** factor basis |
| Unqualified natural-gas energy expressed in **kWh** | → **Net CV / NCV default** |

* A deterministically policy-selected candidate is returned at **`confidence = 1.0`**.
* **Gross and Net are methodological bases, not interchangeable units** — the protection
  implemented in **`46a5534`** (`resolve_unit_for_factor`) is accepted and remains binding.
* The post-stage discovery implementation in **`466eb93`** (with the containment gate in
  **`b0ac3fe`**) is accepted.

## 3. ACCEPTED ARTEFACTS (all on `p8-release-reconciled`)

| SHA | Content |
|---|---|
| `46a5534` | D-A policy core — `source_calorific_basis`, `DEFAULT_CALORIFIC_BASIS='net'`, `select_basis_factor`, Gross/Net non-interchangeability fix |
| `466eb93` | `FactorMatchingEngine` post-stage natural-gas calorific-basis discovery |
| `b0ac3fe` | Natural-gas scope gate (containment of the CNG false positive found by the oracle) |
| `89c02db` | D-A implementation report |
| `969ba4e` | Independent verification report (`-035`) |

## 4. VERIFIED EVIDENCE BASIS (not restated as new work)

* Real row-1 oracle against the local authoritative DEFRA dataset: `Gas usage 5,362.2000 kWh` →
  activity **Natural gas** → qualified candidates discovered → **Net CV** selected →
  factor `2aa65183-eb28-4640-a529-15f18360dc5a` `[kWh (Net CV)]`, Scope 1, 2025, DEFRA-DESNZ /
  **DEFRA-2025**, GB → **matched, confidence 1.000**, stages include `calorific_basis`.
* Gross/Net safety reproduced; enumeration-order independence reproduced; factor-set context retained.
* CNG false positive **contained** — `Power consumption … kWh` → `no_match`, no gas factor.
* Regressions independently green: D-A policy 26, D-A discovery 9, full `tests/unit` **2598 passed /
  0 failed**.

## 5. FOLLOW-UP OBSERVATIONS — RECORDED, NOT IMPLEMENTED (must NOT reopen D-A)

These were raised by `-034`/`-035`, classified by the PO as **observations, not D-A defects**, and are
**formally deferred** to a future, separately PO-gated factor-selection policy work item:

| ID | Observation | Classification |
|---|---|---|
| **`F-DA-1`** | D-A row 1 selected the **CH4 per-unit component** factor (`0.00031` kg CO2e per kWh) rather than the **combustion aggregate** | deferred policy item |
| **`F-DA-2`** | Explicit **Net-CV prose** could reach a **WTT (well-to-tank)** factor (`0.03347`) | deferred policy item |
| **`F-DA-3`** | **Scope 1 vs Scope 3** factors can share an activity/unit/basis | deferred policy item |
| **`F-DA-4`** | Other **materially different factor concepts** may share the same activity/unit/basis | deferred policy item |
| **`F-DA-5`** | Verification environment contained **7,049** factors where earlier evidence documents referenced **7,029** | data / inventory reconciliation |

**Consequences of the deferral (binding):**

1. CarbonTally still needs a **separate policy for selection and ranking among factors sharing the same
   activity / unit / basis** — covering aggregate vs component, combustion vs WTT, Scope 1 vs Scope 3, and
   other materially different concepts. That policy is **not** part of D-A and is **not** authorised here.
2. **No behaviour was altered** to address `F-DA-1`…`F-DA-4`; no factor ranking, retrieval or selection
   logic was changed by this decision, and none may be changed without a new PO authorisation.
3. **The factor dataset was not modified** for `F-DA-5`; inventory reconciliation is a data item.
4. `F-DA-1`…`F-DA-5` **must not be used to reopen D-A**. D-A's accepted scope is basis selection, and the
   independent verification confirms that scope is satisfied.

## 6. WHAT THIS DECISION DOES NOT AUTHORISE

* No application code change, and **no reopening of D-A**.
* No test change; no amendment, weakening or addition of tests.
* No factor data change, no ranking/selection-policy implementation, no schema change, no migration.
* No deployment of any kind (Render, Vercel or otherwise); **no P1 activation** — P1 remains **SHADOW**.
* No production access, production write, upload, job or queue operation.
* **No automatic start of the next work item.** D-A's closure does **not** authorise D-B (nor D-C/D-D) or
  any other step-2 sub-workstream.

## 7. NEXT IMPLEMENTATION GATE

The next work item will be a **new, PO-gated task**. Nothing is started by this record; implementation
remains **awaiting explicit PO authorisation**. Candidates already recorded for that future gate are the
factor-selection/ranking policy (`F-DA-1`…`F-DA-4`) and the inventory reconciliation (`F-DA-5`), each of
which requires its own authorisation before any change.

## 8. IMPACT STATEMENT

| Domain | Impact |
|---|---|
| Production | **NONE** — no production access, write, upload, job, queue operation, EF change or deployment; P1 remains SHADOW |
| Code / tests / config / schema / migrations | **UNCHANGED** by this task |
| Factor data | **UNCHANGED** — no record added, edited or deleted |
| Database | **NO WRITES** — closure is a governance record only; no disposable records were created, so no cleanup was required |
| Git | This record is committed and pushed; the working tree finishes **CLEAN** |

## 9. STATUS LINE

**D-A PO CLOSED** — IMPLEMENTED · INDEPENDENTLY VERIFIED (PASS) · PO-CLOSED (2026-09-18).
Follow-up observations `F-DA-1`…`F-DA-5` recorded and deferred, **not implemented**.
