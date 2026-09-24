# CT-PO-P12-STEP2-REPEATABILITY-VERIFICATION-20260924

**Reference:** `CT-PO-P12-STEP2-REPEATABILITY-VERIFICATION-20260924`
**Date:** 2026-09-24
**Governing workplan:** STEP 2 — second full `reset → reprovision → migrate → factors → backend → seed → verify` cycle
**Status:** **STEP-2 DELIVERABLE — CYCLE 2 EXECUTED, REPEATABILITY NOT DEMONSTRATED**
**Production deployment:** **NOT AUTHORIZED**

---

## 1. Purpose

Prove that the canonical Demo Lab can be rebuilt from a clean state with
deterministic results, and compare Cycle 1 vs Cycle 2.

## 2. Cycles

| Item | Cycle 1 (Step 2) | Cycle 2 (completion pass) |
| --- | --- | --- |
| Started | 2026-09-24T08:46Z (pre-reset manifest) | 2026-09-24T09:44:41Z |
| Reset | lab auth users removed 13; 3 containers removed; DB dropped | lab auth users removed 0 (already clean); 3 containers removed; DB dropped |
| Reprovision | `run_demo_lab.sh --backend --factors` | same |
| Migration files / errors | 81 / 0 | 81 / **not captured** (see §5) |
| Public tables | 141 | **141** |
| RLS-enabled tables | 141 | **141** |
| **Public policies** | **298** | **210** |
| Insight tables | 6 | **6** |
| Storage D32 policies | 4 | **4** |
| Factors | 7,049 | **7,049** |
| Processing entities | 1 | **2** (Alpha + Beta) |
| Internal staff roles with `can_manage_staff` | 0 | **1** (`admin`) |
| Backend | `/health` 200 | started **after** the factor load (D-2-03 fix in force); `/health` 200 by the time of the Story-B seed |

## 3. Deterministic items (identical across cycles)

- public table count: **141 = 141**
- RLS-enabled table count: **141 = 141**
- Insight table count: **6 = 6**
- storage D32 policy count: **4 = 4**
- factor count: **7,049 = 7,049**
- generator HEAD: `8ade2bf…` in both cycles

## 4. Non-deterministic item — the blocker

```text
public RLS policies:  cycle 1 = 298   cycle 2 = 210   DELTA = -88
```

Supporting facts measured in Cycle 2:

```text
tables with RLS enabled and ZERO policies : 61
storage D32 policies                      : 4   (unchanged)
key tables (evidence_line_items, organizations, processing_entities,
            carbontally_insight_* )        : policies present (demo capability intact)
```

**This is a genuine repeatability discrepancy and is NOT reported as expected
nondeterminism.** Per the mandate, it is identified and documented rather than
"rerun until the counts happen to match".

### 4.1 Candidate causes (not yet proven)

| # | Hypothesis | Status |
| --- | --- | --- |
| H1 | Cycle 1's database was built in **two passes** (an earlier partial migration application — see the Step-2 record's `s2_prereq` attempt — followed by the full harness pass), so some migrations' conditional policy creation ran against a different table-existence state than a single clean pass | **plausible, unproven** |
| H2 | Cycle 2's `auth`-schema structure clone changes the table-existence state seen by policy-creating migrations (this is the only intentional difference between the two cycles) | **plausible, unproven** |
| H3 | A cycle-2 migration aborted and was tolerated, skipping its policies | **plausible, unproven** — the migration error list was lost by output truncation (§5) |

### 4.2 Why this matters

- 61 tables being `RLS enabled + zero policies` is **fail-closed**, not a security
  hole; `verify.py` still reports **18/18 isolation rules** and the previously
  failing audit-activity probes now pass.
- However, the mandate requires **deterministic counts**. A 298 → 210 delta means
  the environment is **not proven reproducible**, so the repeatability criterion
  **is not satisfied**.

## 5. Process gap (recorded honestly)

The Cycle-2 reprovision output was captured with `tail -30`, so
`migrations_with_errors` and the full stack JSON were **not preserved**. The exact
per-migration error list for Cycle 2 is therefore **UNKNOWN**. This is a
measurement/process gap in this pass; the correct remedy is to re-run the stack
step capturing the complete JSON before drawing a conclusion.

## 6. Verdict

**Repeatability: FAILED (not demonstrated).**

```text
deterministic items : tables (141), RLS-enabled (141), Insight tables (6),
                      D32 policies (4), factors (7,049)  → MATCH
non-deterministic   : public policies 298 → 210 (-88)    → MISMATCH
```

The Reset/Reprovision procedure is **not yet proven reproducible**. Cycle 2 also
demonstrated two real improvements: the D-2-03 fix is in force (the backend now
starts after the factor load, so the tabular seed produced real mapping without the
manual restart), and provisioning now yields the intended two-PE + staff-admin
topology.

## 7. Exact remediation required

1. Re-run `tools/demo_lab/stack.py` on a freshly reset lab **capturing the complete
   JSON** (`migrations_with_errors`), and diff the policy set table-by-table
   between two clean single-pass cycles.
2. Determine whether the delta is caused by H1/H2/H3; if a migration is being
   tolerated that should not be, fix it in the **demo-lab tooling or report it as a
   product/migration defect** — never by editing the migration silently.
3. Add a **policy-count + policy-name-set assertion** to the reset/reprovision
   procedure so future cycles fail loudly on any drift.
