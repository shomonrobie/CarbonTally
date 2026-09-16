# CarbonTally — Phase 8 / Phase 8-X
## G0 GATE RECONCILIATION REGISTER

**Task identity:** `CT-P8-G0-GATE-RECONCILIATION-20260913-042` — *G0 register (F/E, **decision register only**)`
**Date:** 2026-09-14 (executed under `CT-P8-CONTINUE-AFTER-P2-20260914-002`)
**Authority:** master execution authorisation + PO authorisation of this register (playbook line 196)
**Authoritative source for the gate definitions:** `CT-P8-G0-GOVERNANCE-CONSOLIDATION-20260912-008.md` (status list) + roadmap §29
**Verified environment:** local repository + **non-production** `carbontally_qa_phase8` (read-only) · Git HEAD `37b19d13723b0b1eabceeade86ce1615a98ab400` · staged 0 · no commits
**This document implements nothing.** It records each Gate-0 item's definition, status as recorded, ***status today** after B1/B2/B3/B4 and P1*, its evidence, what it blocks, its closure route and its owner.

---

## 1. Register

| Gate | Definition | Status at `-008` (2026-09-12) | **Status today (2026-09-14, reconciled)** | Evidence | What it blocks | Closure route / owner |
|---|---|---|---|---|---|---|
| **G0-A** | ESRS **E1 evidence closure** — authoritative source identifiers for E1 seed content | **Open** | **STILL OPEN** | no authoritative ESRS sources supplied; `E1-COV = CONDITIONAL` | **only** E1 seed *content* | external evidence → `…048`; **PO/evidence owner** |
| **G0-B** | Phase 8 **naming/scope** terminology | Resolved for this programme | **CLOSED** (unchanged) | Decision Record §1.1; `-008` §6 | — | residual **PX-1** (documentation only) |
| **G0-C** | **Approve the batch plan** | **Open** — PO | **RECONCILED → CLOSED BY EXECUTION** | the plan was approved *and executed*: B1 closed · B2 (`…028`) · B3 (`…031`/`…051`) · B4 (`…034`, gate V4 `…052`) · P1 (`…037` → `P1-D1…P1-D8` ratified → `…053`) | nothing outstanding | PO authorisation `…050` + per-batch rulings — **no new decision** |
| **G0-D** | **Production strategy** for the outstanding-migration backlog | **Open** — PO/deployment; production **PROHIBITED** | **STILL OPEN — production remains prohibited**; the backlog *figure* is stale | repo holds **63** migration files (34 outstanding at `-008`); the B-chain (8 migrations) is applied **in non-production QA only**; production had **no** migration/deploy/data change | **all** production deployment/application | **PO/deployment decision** — prohibition unchanged, not inferable from any ratified technical decision |
| **G0-E** | **B2 scope** | Open — PO | **CLOSED BY B2** | B2 contract + closure `…028`; B2 migrations applied in QA; B2 suites green | — | none — reconciliation only (the register's positive delta) |
| **G0-F** | Historical **PDF/IMAGE line-item** treatment | Recorded in `DM-7` §6 | **CLOSED** (unchanged) | `DM-7` §6; re-affirmed by P1 (`P1-D4`: **no** historical reprocessing) | any historical re-parsing (also barred by `P1-D4` + the standing no-backfill rule) | none — already ruled |
| **G0-G** | **Phase 8-X** items **PX-2 / PX-4 / PX-5 / PX-6 / PX-7** | Open — PO | **STILL OPEN** | no rulings recorded; `…043` (X1) explicitly gated on `PX-2`/`PX-5` | the X-series workstream — **not** the B/P chain | **PO decision** per item; X1 blocked |
| **G0-H** | **RLS stays a separate workstream** (confirmation) | Recorded; **confirmation open** | **STILL OPEN — confirmation outstanding** | no confirmation recorded; this is the `A-RLS` input for `…039` and `…046` | the **RLS package** (`…039`) and `…046` | **PO confirmation** — see §3 |
| **G0-I** | `DM-7` refresh | DONE | **CLOSED** (unchanged) | `-008`; `DM-7` | — | none |

**Summary:** 5 closed (G0-B · G0-C by execution · G0-E by B2 · G0-F · G0-I) · **4 open**: **G0-A** (evidence/external), **G0-D**, **G0-G**, **G0-H** (PO decisions).


## 2. What actually changed since `-008` (the reconciliation)

1. **G0-E closed by delivery, not by a new decision** — B2 was implemented and closed, so the "B2 scope" question is answered by the executed contract.
2. **G0-C closed by execution** — the batch plan has been approved and run through five batches (B1–B4, P1). Recording it as still "open" would misrepresent the programme; recording it as closed reflects approvals that genuinely exist (`…050` + per-batch rulings).
3. **G0-D stays open and its *backlog figure* is stale** — the register restates the prohibition and corrects the number (63 migration files in-repo; the B-chain applied to QA only). **Nothing here weakens the production prohibition.**
4. **G0-H becomes the *immediate* dependency** — the sequence next reaches `…039` (RLS package), whose documented input is the `A-RLS` confirmation (G0-H).
5. **G0-A and G0-G are untouched** by the B/P chain: no E1 evidence arrived, and no Phase 8-X rulings have been issued.

## 3. The one decision this reconciliation surfaces

**G0-H / `A-RLS` confirmation (PO).** The playbook records `…039` (RLS package) and `…046` as gated on **`A-RLS`**, and `-008` records G0-H as *"Recorded; confirmation open"*. The RLS postures already implemented and verified in this programme (B1/B2/B3/B4 org-scoped policies, append-only artefact grants, `/disclosure` role boundaries, `DM-6` exposure) are the **B-chain's own** RLS — **not** the separate RLS workstream's scope. Whether the remaining RLS work is confirmed as a separate authorised workstream, folded into a named batch, or deferred **cannot be inferred from any ratified decision**; inventing it would silently redefine a governance item.

## 4. Boundaries reaffirmed by this register

No production access, migration, deployment or data mutation · no historical backfill/re-extraction · **no Phase 9** (Phase 8-X remains inside the Phase 8 programme) · no P1 expansion · no P1 enablement without its real-document shadow evidence · OHD findings remain separately reconciled · unrelated worktree changes preserved · no commit/push.

## 5. Verdict

### `…042 G0 GATE RECONCILIATION COMPLETE — 5 GATES CLOSED (2 RECONCILED TO REALITY: G0-C BY EXECUTION, G0-E BY B2), 4 OPEN (G0-A EVIDENCE · G0-D/G0-G/G0-H PO); THE IMMEDIATE DEPENDENCY IS THE G0-H / A-RLS CONFIRMATION FOR …039`
