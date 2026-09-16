# CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260913-031 (RE-RUN, 2026-09-14)

**Task ID:** `CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260913-031`
**Title:** Phase 8 Batch B3 — contract authorship + durable PO decision record for the 12 decisions ratified 2026-09-14
**Date:** 2026-09-14
**Type:** CONTRACT / DECISION PREPARATION ONLY — no implementation, no schema, no migration, no test, no deployment
**Authority:** PO blanket authorisation `…050`; PO ratification of the 12 recommendations (2026-09-14)

> **⚠ ONE SUBSTANTIVE CONFLICT REPORTED — not silently resolved.** This task's premise
> (*B3 unimplemented; contract not yet written*) does not match verified repository state
> (**B3 is implemented, verified and CLOSED; the contract already exists**). See §1 and the
> decision record §1. Consequently the instructed verdict lines cannot both be signed
> truthfully; the truthful equivalents are recorded in §§D–F.

---

## A. Repository state reviewed

| Artefact | Finding |
|---|---|
| `CT-P8-REST-PLAN-20260913-027.md` | governing rest-plan/dependency map; B3 rows and `…031`→`…033` chain |
| `docs/architecture/CARBONTALLY_PHASE8_B3_IMPLEMENTATION_CONTRACT_20260913.md` | **the authoritative B3 contract already exists** (373 lines, §1–§22, incl. Amendment 1 answering `B3-D1`) |
| `CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260913-031.md` | `…031` already executed 2026-09-13 (contract + `B3-Dn` register) |
| `CT-P8-B3-IMPLEMENTATION-20260913-032.md` | **B3 implemented** (203 lines) |
| `CT-P8-B3-INDEPENDENT-VERIFICATION-20260913-033.md` | gate **V3 PASS** (167 lines) |
| `CT-P8-B3-CLOSURE-20260913-051.md` | **"B3 CLOSED — IMPLEMENTED, INDEPENDENTLY VERIFIED (V3 PASS), GOVERNANCE RECORDED"** |
| B1/B2 artefacts (`-009`…`-016`, `-017`…`-025`, B2 contract/closure) | boundaries and consumed objects |
| B3 code (forensic only) | `backend/domain/disclosure_projection.py`, `backend/api/v3_disclosure.py`, `backend/data/disclosure*.py`, `backend/services/disclosure_*.py`; migrations `20260917000000`, `20260917010000` |
| Live DB (read-only) | `carbontally_qa_phase8`: intensity tables present, `rls=true`, policies 1/1/2; `disclosure_values` columns confirmed (incl. `report_version_id`, `requirement_version_id`, `effective_class`, `value_status`) |
| Master playbook `…049` | B3 recorded as **closed** at gate V3 (`…051`) |

**No pre-existing B3 decision record existed** for the 12 decisions → the record created here
is **additive, not duplicative** (verified by search).

---

## B. PO decisions recorded (plain English)

All 12 are recorded in the authoritative decision record with evidence and implementation
constraints. In plain English:

1. **`D-B3-1`** — Calculation uses **persisted structured data** as the authoritative input; extraction output is evidence, never a competing source of truth.
2. **`D-B3-2`** — The **framework and its version** are identified explicitly; historical calculations can show which framework/version was used.
3. **`D-B3-3`** — **Requirement sets are explicit, versioned and auditable**, not hidden in code.
4. **`D-B3-4`** — **Applicability is deterministic from persisted, auditable inputs**, never from hidden assumptions; the required inputs and their lifecycle must be documented, and unsupported fields must not be invented.
5. **`D-B3-5`** — **Purpose identification uses controlled, persisted, auditable codes**; no uncontrolled vocabulary.
6. **`D-B3-6`** — Intensity retains an **explicit denominator value, unit and context/meaning**, not just a final number.
7. **`D-B3-7`** — An **explicit controlled value-status model** distinguishes how a value is represented/obtained; no null/informal-flag semantics and no invented statuses.
8. **`D-B3-8`** — An **auditable drill-down** from results to persisted inputs and evidence, with the exposure boundary defined.
9. **`D-B3-9`** — Missing/insufficient evidence is **explicitly represented**; CarbonTally never fabricates, assumes or conceals gaps — and the contract must define how a gap affects calculation/reporting status.
10. **`D-B3-10`** — The controlled B1+B2 baseline belongs to a **dedicated persistent QA/test environment**; deployment is **not** authorised by this decision.
11. **`D-B3-11`** — B3 exposes the **minimum API surface**; no speculative endpoints.
12. **`D-B3-12`** — **Finalised results stay tied to their historical calculation state/version**; later framework/requirement/rule/factor changes never silently alter them.

---

## C. B3 contract — created / amended

The contract **already existed** and was therefore **amended**, not duplicated:

* **Authoritative contract (pre-existing, 2026-09-13):**
  `docs/architecture/CARBONTALLY_PHASE8_B3_IMPLEMENTATION_CONTRACT_20260913.md`
* **Amendment 2 added by this task (§23):** decision→clause map, conformance table, the one
  new decision (`D-B3-13`), and an explicit "B3 remains CLOSED" status clause.
* **New durable decision record (this task):**
  `docs/architecture/CARBONTALLY_PHASE8_B3_PO_DECISION_RECORD_20260914.md`

If the PO intended a *freshly authored* contract file rather than an amendment, say so and
this can be restructured — but two competing B3 contracts would be a governance defect.

---

## D. Unresolved decisions

**One further PO decision is required:**

* **`D-B3-13` — Effect of an open evidence gap on reporting/finalisation status.**
  `D-B3-9` requires the contract to define this effect; neither the 12 decisions nor the
  existing artefacts determine it. As built, gaps are **represented** (statuses, reasons,
  `UNDETERMINED` preserved, no fabricated zeros) but do **not block** approval/finalisation
  (`B4-D1`; `FINAL` immutable). The choice materially affects auditability and
  user-visible behaviour. Options: **(a)** advisory only (status quo) · **(b)** blocking
  precondition, with the blocking gap states defined · **(c)** mixed rule.

**Two confirmation items** (not new business rules — see decision record §5):
`C-B3-1` applicability assessment lifecycle completeness · `C-B3-2` confirm
`carbontally_qa_phase8` as the PO-named dedicated persistent QA/test environment for
`D-B3-10`/`D-02` (`…029`).

The instructed line *"B3 CONTRACT COMPLETE — READY FOR PO IMPLEMENTATION AUTHORISATION"* is
**not applicable as written** (the contract was already complete on 2026-09-13 and B3
implementation authorisation has already been given and discharged). The accurate
equivalent:

> **B3 DECISION RECORD COMPLETE — 12 DECISIONS RECORDED; ONE NEW PO DECISION REQUIRED
> (`D-B3-13`); NO NEW B3 IMPLEMENTATION AUTHORISATION REQUESTED OR GRANTED.**

---

## E. Implementation status

The instructed statement is **factually false in the current repository and therefore not
signed**:

* ⛔ *"B3 IMPLEMENTATION NOT STARTED"* — **cannot be signed.**
* ✅ **B3 IMPLEMENTATION IS COMPLETE AND CLOSED** — `…032` implementation · `…033` gate **V3 PASS** · `…051` closure; migrations `20260917000000_p8_b3_intensity_catalogue.sql` and `20260917010000_p8_b3_intensity_ratios.sql`; modules `disclosure_projection.py`, `v3_disclosure.py` (7 B3 endpoints), `data/disclosure*.py`, `services/disclosure_*.py`.
* ✅ **NO NEW B3 IMPLEMENTATION WAS PERFORMED BY THIS TASK.** No code, schema, migration,
  API, test or configuration was changed; B3 was neither re-opened, re-verified nor re-closed.

---

## F. Authorization status

**NO B3 IMPLEMENTATION AUTHORIZATION GRANTED BY THIS TASK.** *(Signed — true.)*

This task grants no authorisation of any kind; it does not self-authorise, self-close or
re-open B3, and it does not authorise B4, P1, P2, RLS, Phase 8-X/Phase 9, Insight or
legacy-route work. Deployment remains a separate controlled task and PO authorisation.

---

## G. Scope confirmation

Confirmed: **no B4, P1, P2, RLS remediation, Phase 8-X / Phase 9, Insight, or legacy-route
implementation was performed.** No schema change, migration, API change, frontend change,
test change, production configuration change or `git commit` occurred. QA was read
**read-only**; production was untouched and not connected to.

| Boundary | Status |
|---|---|
| B3 implementation | **not started by this task** (already closed previously) |
| B4 / P1 / P2 / RLS / 8-X / Phase 9 / Insight / legacy | **not touched** |
| Schema / migrations / APIs / tests | **unchanged** (verified: no diff) |
| Git | HEAD `37b19d13723b0b1eabceeade86ce1615a98ab400`; staged 0; **no commits**; unrelated worktree changes preserved |
| Production | untouched |
| New artefacts | decision record (new) · contract **Amendment 2** (appended) · this report |

---

## Readiness review — the eight determinations

1. **All 12 recorded?** YES (`D-B3-1`…`D-B3-12`).
2. **Internally consistent?** YES.
3. **Consistent with B1/B2?** YES.
4. **Dependencies identified?** YES (B1 persisted spine, B2 evidence linkage, ratified decision set, environment).
5. **Unresolved PO decisions?** YES — one (`D-B3-13`), plus two confirmations.
6. **Blocking ambiguities before authorisation?** Only for *future* changes: `D-B3-13`; `C-B3-1` if the intended lifecycle differs.
7. **B1+B2 in persistent QA still a prerequisite?** YES — and **satisfied today** by `carbontally_qa_phase8` (S3+B1+B2+B3 present; a skip would still not be a PASS).
8. **Separate B3 implementation authorization still required?** **YES — unchanged.**

---

## Next step

PO review of `docs/architecture/CARBONTALLY_PHASE8_B3_PO_DECISION_RECORD_20260914.md` and
contract §23, then either issue `D-B3-13` or record that the `D-B3-9` status quo is
accepted, and confirm `C-B3-1`/`C-B3-2`. No further action is taken by this task.

