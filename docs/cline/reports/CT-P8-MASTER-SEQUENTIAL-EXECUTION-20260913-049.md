# CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260913-049

## CarbonTally Phase 8 / Phase 8-X — Master Sequential Execution: Ledger, Gate Report and Programme Report

**Task ID:** `CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260913-049`
**Playbook consumed:** `docs/cline/reports/CT-P8-REST-PLAN-20260913-027.md` (1,999 lines; verified present, mtime 2026-09-13T20:08)
**Type:** ORCHESTRATION / EVIDENCE-FIRST EXECUTION ATTEMPT — **GATE-STOPPED**
**Date:** 2026-09-13
**Agent role:** implementation/forensics agent (not Product Owner)

**Outcome:** no task was executed. The sequential chain stopped at its **first gate** because **no per-task authorisation exists** for any eligible task, and the master instruction expressly does not itself authorise tasks (its §30).

---

## A. Executive verdict

### `PROGRAMME PARTIALLY COMPLETE — EXECUTION BLOCKED BY GOVERNANCE / PREREQUISITE GATES`

Material tasks remain unimplemented and/or unclosed. No claim of completion is made.

---

## 1. Method (what was actually done)

1. **Read the master playbook** — `CT-P8-REST-PLAN-20260913-027.md`: full document already consumed when produced (this agent authored it); its load-bearing sections were re-read fresh this task: **§19** (fresh priority order), **§22** (consolidated PO decision register), **§23** (sequence), **§26** (instruction index) — verbatim extracts used below.
2. **Reconciled current state** (fresh, this task): branch, HEAD, staged, tracked modifications, untracked, newest commits, newest governance files, presence/absence of closure and per-task authorisation artefacts.
3. **Live read-only database introspection** of every local database reachable at `127.0.0.1:54426` to establish which environments hold B1/B2 schema.
4. **Searched the whole repository** for any record naming any of the 20 proposed task IDs, and for any B2 closure artefact.
5. **Built the programme ledger** (§3) and classified every task (A–I per the orchestrator’s §6).
6. **Performed the authorisation gate check** (§4) on the earliest eligible task and stopped.

**No implementation, migration, database modification, commit, push or deployment occurred.** No file was changed except this report.

### 1.1 Fresh state evidence (this task)

| Check | Result |
|---|---|
| Branch | `main` |
| HEAD | `37b19d13723b0b1eabceeade86ce1615a98ab400` (unchanged) |
| Staged | **0** |
| Tracked modifications | **218** (all pre-existing; unchanged) |
| Newest commits | `37b19d1` GA4 (unrelated side work), `19e4f01` Phase 8 lifecycle, `b471286` Phase 9 baseline, `c86b83c` S1 |
| Newest governance files | `CT-P8-REST-PLAN-20260913-027.md` (20:08, this agent), `CT-P8-B2-INDEPENDENT-VERIFICATION-20260913-025.md` (14:40) |
| Any record naming task IDs `…028`–`…046`, `…048` outside the plan? | **NONE for all 20** (whole-tree search) |
| Any `*B2*CLOSURE*` artefact? | **NONE** |
| No new PO/authorisation artefact added since the plan | **confirmed** (newest file is the plan itself) |

### 1.2 Live database evidence (read-only, `127.0.0.1:54426`)

| Database | public tables | `disclosure_*` tables (B1) | `evidence_line_items` (B2) |
|---|---|---|---|
| `postgres` (local dev/application DB) | 116 | **0** | **0** |
| `carbontally_test` (integration DB) | 114 | **0** | **0** |
| `carbontally_b2_clone_20260913` (disposable clone) | 128 | 11 | 1 |
| `ct_b2_iv_20260913` (disposable clone) | 128 | 11 | 1 |
| `_supabase`, `storage_vectors` | 0 | 0 | 0 |
| Production (Supabase) | *not reachable from this workstation; per records: 21 applied / 34 outstanding, B1/B2 absent* | — | — |

**Conclusion:** B1 and B2 exist **only** in the two retained disposable clones. No persistent dev/QA/test environment holds them, so the B1/B2 runtime suites cannot execute there and would report **SKIPPED — which is not a PASS**.


---

## 2. Programme ledger (reconciled)

Status classes per the orchestrator’s §6: **A** COMPLETE/CLOSED · **B** IMPLEMENTED — VERIFICATION PENDING · **C** VERIFIED — PO CLOSURE PENDING · **D** READY — AUTHORIZATION PRESENT · **E** READY FOR PO DECISION · **F** BLOCKED — PO AUTHORIZATION REQUIRED · **G** BLOCKED — PREREQUISITE REQUIRED · **H** BLOCKED — CONFLICT/AMBIGUITY · **I** N/A / SUPERSEDED.

### 2.1 Pre-existing (closed or already-executed) work

| Task / artefact | Impl | Verification | PO closure | Final status |
|---|---|---|---|---|
| B1 Disclosure Model foundation (`-009`…`-016`) | **DONE** | **V1R PASS with P3×6 nonblocking findings** | closed (B1 contract: “B1 is CLOSED”) | **A — COMPLETE/CLOSED** (caveat: applied in **no** persistent environment) |
| B2 Evidence / Line-item addressability (`-017`…`-025`) | **DONE** (`-024`; untracked) | **INDEPENDENT VERIFICATION PASS** (`-025`) | **asserted by PO statement; NO repository closure record exists** | **C — VERIFIED — PO CLOSURE PENDING** (see §4.2, finding F-049-1) |
| S1 report correctness (`c86b83c`) | **DONE** | **IV PASS** (`…056`: 5 DB-level S1 probes + supersession/immutability probes) | none required (verification task) | **A — COMPLETE — INDEPENDENTLY VERIFIED** |
| S3 report lifecycle (`19e4f01`; migration `20260913000000`) | **DONE** | **IV PASS** (`…056`; migration proven additive/idempotent/no-RLS-change) | none required (verification task) | **A — COMPLETE — INDEPENDENTLY VERIFIED** |
| S4 narrative overlay | **NONE — HARD STOP** | n/a | n/a | **F — BLOCKED — PO DECISION REQUIRED** |
| Phase 8 D1–D17; lifecycle spec; Disclosure Model 20 decisions; S0 package; PQ-1…PQ-8; `DM-7` refresh; G0-B/F/I | n/a | n/a | **ratified** | **A — CLOSED** (governance) |
| GA4 admin configuration (`37b19d1`) | done | n/a | n/a | **I — OUT OF PHASE 8 SCOPE** (unrelated side work) |

### 2.2 The 20 planned tasks — ledger with gates

| Task ID | Workstream | Status class | Authorisation present? | Prerequisites | Impl | Verification | PO closure | Blocker |
|---|---|---|---|---|---|---|---|---|
| `CT-P8-B2-CLOSURE-RECORD-20260913-028` | B2 governance record | **E** | **NO** (no record names this task) | `-025` exists | n/a | n/a | **not recorded** | **PO closure statement + authorisation** |
| `CT-P8-B1B2-ENV-APPLICATION-20260913-029` | Deployment (non-prod) | **F** | **NO** | `…028`; **environment not named**; snapshot | none | suites would SKIP | n/a | **PO authorisation + environment name (D-02)** |
| `CT-P8-S1S3-INDEPENDENT-VERIFICATION-20260913-030` | Report lifecycle verification | **E → DONE** | **YES — blanket `…050`** (gate was authorisation only: *"no PO decision prerequisite"*) | S1/S3 implemented; disposable clone required | **done** | **IV PASS** (`…056`) | none (verification task) | **EXECUTED 2026-09-14** |
| `CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260913-031` | B3 contract | **F/E** | **NO** | `…028` for lineage | none | n/a | n/a | **PO authorisation** (no decision prerequisite) |
| `CT-P8-B3-IMPLEMENTATION-20260913-032` | B3 implementation | **G** | NO | `…031` + ratify `B3-Dn` + `…029` env | none | none | none | Prereq `…031`; decision **D-12** |
| `CT-P8-B3-INDEPENDENT-VERIFICATION-20260913-033` | V3 | **G** | NO | `…032` | none | none | none | Prereq `…032` |
| `CT-P8-B4-CONTRACT-AND-PO-DECISIONS-20260913-034` | B4 contract | **G** | NO | B3 PO-closed | none | n/a | n/a | Prereq B3 closure |
| `CT-P8-B4-IMPLEMENTATION-20260913-035` | B4 implementation | **G** | NO | `…034` + **D-13** | none | none | none | Prereq `…034`; decision D-13 |
| `CT-P8-B4-INDEPENDENT-VERIFICATION-20260913-036` | V4 | **G** | NO | `…035` | none | none | none | Prereq `…035` |
| `CT-P8-P1-AUTHORISATION-PREPARATION-20260913-037` | P1 decision package | **F/E** | **NO** | P1 contract exists (`-020`) | n/a | n/a | n/a | **PO authorisation** (no decision prerequisite) |
| `CT-P8-P2-FACTOR-CATALOGUE-CENSUS-20260913-038` | P2 forensic (read-only) | **F** | **NO** | authorised read-only DB session | none | n/a | n/a | **PO authorisation of read-only access** |
| `CT-P8-RLS-SECURITY-REMEDIATION-PLAN-20260913-039` | RLS planning | **F** | **NO** | PO reopens gate | none | n/a | n/a | **Decision D-18 (gate held)** |
| `CT-P8-P8X-PHASE9-PO-RECONCILIATION-20260913-040` | 8-X / 9 reconciliation | **H + F** | **NO** | — | n/a | n/a | n/a | **Conflict (D-07) + PO authorisation** |
| `CT-P8-I1-AUTHORISATION-CLARIFICATION-20260913-041` | Insight authorisation | **H + F** | **NO** | — | n/a | n/a | n/a | **Ambiguity (D-11) + PO authorisation** |
| `CT-P8-G0-GATE-RECONCILIATION-20260913-042` | G0 register | **F/E** | **NO** | — | n/a | n/a | n/a | **PO authorisation** |
| `CT-P8-P8X-X1-IMPLEMENTATION-20260913-043` | Phase 8-X X1 | **G** | NO | `…040` + **D-07/D-08** + auth | none | none | none | Prereq + decisions |
| `CT-P8-P8X-X1-INDEPENDENT-VERIFICATION-20260913-044` | VX1 | **G** | NO | `…043` | none | none | none | Prereq `…043` |
| `CT-P8-P8X-X2-IMPLEMENTATION-20260913-045` | Phase 8-X X2 | **G** | NO | X1 closed + **D-09** | none | none | none | Prereq + decisions |
| `CT-P8-S2-REPORT-TABLE-RLS-AND-SCHEMA-20260913-046` | S2 + report-table RLS | **G** | NO | **D-17 (`A-RLS`)** | none | none | none | Decision `A-RLS` |
| `CT-P8-G0-A-E1-EVIDENCE-CLOSURE-20260913-048` | E1 evidence closure | **F** | **NO** | authoritative ESRS evidence | n/a | n/a | n/a | **PO authorisation + external evidence** |

**Tasks classified D (READY — AUTHORIZATION PRESENT): 0.** No task in the programme currently satisfies the authorisation gate.

### 2.3 Additional tasks/workstreams identifiable from the playbook (no task ID allocated yet)

| Item | Status | Why it has no executable task ID |
|---|---|---|
| S5 frozen final PDF | designed only | allocation into B4 **unrecorded** (needs D-14) |
| S6 frontend lifecycle UI | designed only | allocation **unrecorded** (D-14) |
| S7 regression + negative security tests | designed only | allocation **unrecorded** (D-14) |
| S8 AI-assisted narrative | deferred | separate authorisation; AI preconditions NOT MET |
| D16 legacy disposition (`LEG`) | ratified as separate workstream, unexecuted | separate authorisation (D-19) |
| RLS remediation steps `RLS-4A-1 …` | held | D-18 + per-step authorisation |
| Insight `I2…I8` | not authorised | depends on the I1 ruling (D-11) |
| Phase 9 (any) | baseline only, **not PO-ratified**, implementation NOT AUTHORIZED | C-1/C-2/C-3 require PO adjudication (D-07) |


---

## 3. Earliest eligible task and the authorization gate

### 3.1 Determination

The playbook’s §19 priority order places **`CT-P8-B2-CLOSURE-RECORD-20260913-028`** first, and the playbook’s §23 sequence lists it as sequence item 1 with prerequisites “`-025`; PO closure statement” and PO decisions **D-01** and **D-03**.

### 3.2 Gate check for `…028`

| Question | Answer |
|---|---|
| Is `…028` the earliest task in the dependency graph whose prerequisite is satisfied? | **Yes** — its only technical prerequisite (`-025`, the B2 verification report) exists. |
| What authorises it? | Its own instruction requires the PO to have **stated the closure** and to have **explicitly authorised the task ID**; the playbook’s §26 index marks it “**No** — needs PO closure statement + authorisation”. |
| Does such an authorisation artefact exist? | **NO.** Whole-tree search: no file anywhere (outside the plan) names `CT-P8-B2-CLOSURE-RECORD-20260913-028`. |
| Does a B2 closure record exist? | **NO.** No `*B2*CLOSURE*` artefact exists anywhere. |
| Does the master execution instruction supply the authorisation? | **NO.** Its §30 states expressly that treating the master prompt as blanket PO authorisation is prohibited. |
| Does any *prior* authorisation remain unconsumed? | **NO.** The only authorised-but-unimplemented stage previously on record was B2, which is now implemented and verified. |
| Verdict | **BLOCKED — PO AUTHORIZATION REQUIRED (gate 1).** |

### 3.3 Finding F-049-1 — the closure reference does not resolve (CONFLICT, reported not reconciled)

The PO’s earlier statement in this programme is that **B2 is “PO CLOSED under `CT-P8-B2-PO-CLOSURE-20260913-026`”**. That record **does not exist**. Two readings are possible and **the agent must not choose between them**:

| Reading | Consequence | What is required |
|---|---|---|
| **(a)** The PO decided to close B2 and the record was never written. | `…028` records a decision that genuinely exists; the PO’s authorisation is sufficient. | One line: authorise `…028` and state the closure wording (see §4.1). |
| **(b)** The reference to `…026` is itself unverified. | The closure must be re-stated before it is recorded; recording it now would create governance history from an unverified conversational claim (prohibited by §2/§32). | One line: re-state the closure and authorise `…028`. |

Either way the required PO action is the same in form: **an explicit closure statement plus authorisation of `…028`**. Under **no** reading may the agent write the closure record on its own initiative.

### 3.4 Why no other task could be executed instead

| Candidate | Why not executable |
|---|---|
| `…030` S1/S3 IV | Requires a verification authorisation naming the task; none exists. (It needs no PO *decision* — only authorisation — but authorisation is still a gate.) |
| `…031` B3 contract | Requires a PO authorisation naming the task; none exists. |
| `…040`/`…041`/`…042`/`…037`/`…048` | Same: authorisation-only gates, none satisfied. |
| `…029` B1/B2 environment application | Gate #3: **the target environment has not been named/authorised**; live evidence confirms no persistent environment holds B1/B2. |
| `…032`…`…036` (B3/B4 implementation/verification) | Prerequisite + decision gates (D-12/D-13); prerequisites unfulfilled. |
| `…038` P2 census | Requires authorisation of a read-only DB session; none exists. Production/unspecified persistent DBs must not be used. |
| `…039` RLS package | Gate held (D-18); the PO must explicitly reopen. |
| `…043`/`…044`/`…045` X-series | Gate #7: the Phase 8-X / Phase 9 conflict is unresolved; PX decisions open. |
| `…046` S2 | Decision `A-RLS` undecided. |
| I1 (any) | Gate #1/#10: authorisation ambiguity (D-11). |

**Result: the execution loop terminates after one iteration, at the first gate.** Per the orchestrator’s §26, the agent must not work around it.

---

## 4. Authorisation requirements — exact PO actions

### 4.1 Immediate chain (unblocks the critical path)

**Gate A — `…028` (B2 closure record).** Paste either:

> **AUTHORISE `CT-P8-B2-CLOSURE-RECORD-20260913-028`.** I confirm B2 is PO-closed. Record it per the playbook §23.1; F-025-1 disposition: record-only (no change); F-025-2 disposition: defer to a future batch. Do not reopen B2.

or, if the PO prefers to fix the wording first:

> **B2 CLOSURE RESTATED:** B2 is PO-closed as of this statement (the referenced `…026` record does not exist). Authorise `…028` to record it.

**Gate B — `…029` (B1/B2 non-production application).** Paste:

> **AUTHORISE `CT-P8-B1B2-ENV-APPLICATION-20260913-029`** against environment **<NAME>** (non-production; not the investor-demo DB; not production). Apply B1 → B2 in order per the B2 contract §18.4, re-apply for idempotency, run the B1 and B2 runtime suites, and report. **Backfill execution is NOT authorised** (dry-run only if I separately authorise it).

### 4.2 Authorization-only gates (no PO decision prerequisite — one line each)

| Task | Required authorisation wording (minimum) |
|---|---|
| `…030` | “Authorise `CT-P8-S1S3-INDEPENDENT-VERIFICATION-20260913-030`.” |
| `…031` | “Authorise `CT-P8-B3-CONTRACT-AND-PO-DECISIONS-20260913-031` (contract + decision register only).” |
| `…037` | “Authorise `CT-P8-P1-AUTHORISATION-PREPARATION-20260913-037` (decision package only).” |
| `…040` | “Authorise `CT-P8-P8X-PHASE9-PO-RECONCILIATION-20260913-040` (reconciliation package only; no X implementation).” |
| `…041` | “Authorise `CT-P8-I1-AUTHORISATION-CLARIFICATION-20260913-041` and record my ruling.” |
| `…042` | “Authorise `CT-P8-G0-GATE-RECONCILIATION-20260913-042` (decision register only).” |
| `…048` | “Authorise `CT-P8-G0-A-E1-EVIDENCE-CLOSURE-20260913-048` (evidence package only).” |
| `…038` | “Authorise `CT-P8-P2-FACTOR-CATALOGUE-CENSUS-20260913-038` and grant read-only access to **<DB/role>**; no writes.” |

### 4.3 Decision gates (a PO decision must exist before the task can be authorised)

| Decision | Task unblocked | Required PO ruling |
|---|---|---|
| **D-01/D-03** | `…028` (+ R3 reconciliation) | closure + repository decision |
| **D-02** | `…029` | environment name |
| **D-07** | `…040`, then `…043` | which identifier owns operational intelligence (Phase 8-X vs Phase 9) |
| **D-08** | `…043` | `PX-2` (MUST set), `PX-4` (platform access BL-1/BL-2), `PX-5` (heartbeat schema) |
| **D-09** | `…045` | `PX-6` (alerting), `PX-7` (retention) |
| **D-11** | `…041` → I1 | I1 authorised: yes/no |
| **D-12** | `…032` | ratify the B3 contract and `B3-Dn` |
| **D-13** | `…035` | ratify the B4 contract and `B4-Dn` |
| **D-14** | S5/S6/S7 | allocation into B4 (or separate batches) |
| **D-15** | P1 implementation | `P1-D1…P1-D8` |
| **D-16** | P2 remediation | remediation approach after the census |
| **D-17** | `…046` | `A-RLS` report-table RLS posture |
| **D-18** | `…039` → RLS steps | reopen the security gate; `D-1…D-13` |
| **D-04/D-05** | production readiness | close G0-C; G0-D production migration strategy |
| **D-06** | `…048` | E1 evidence closure |
| **D-19/D-20** | D16 legacy; S8 AI narrative | separate authorisations |


---

## 5. Findings register

| # | Finding | Severity | Classification | Disposition |
|---|---|---|---|---|
| **F-049-1** | B2’s closure is asserted but has **no repository record**; the referenced `…026` artefact does not exist. | **Medium (governance/traceability)** | blocking for `…028` | Reported, not reconciled; requires the PO’s closure statement + authorisation (§3.3). |
| **F-049-2** | **No per-task authorisation exists for any of the 20 planned tasks** (whole-tree search: zero hits outside the plan); the master execution instruction is not blanket authorisation. | **Medium** | blocking for the whole chain | Each task requires a one-line PO authorisation; wording supplied in §4. |
| **F-049-3** | **No persistent environment holds B1/B2** (live read-only evidence: `postgres` 116 tables / 0 disclosure / 0 line-items; `carbontally_test` 114 / 0 / 0). | **High (verification-blocking)** | environment gate | PO must name a non-production target (`…029`); until then B1/B2/B3/B4 runtime suites SKIP, and **a skip is not a PASS**. |
| **F-049-4** | The Phase 8-X / Phase 9 naming-and-ownership conflict remains unresolved in the repository (Phase 9 baseline committed; P8-X discovery and the RLS register deny a ratified Phase 9). | **High (scope-blocking)** | conflict | `…040` reconciliation package is required **and authorised** before any X task; the agent must not choose an interpretation. |
| **F-049-5** | Insight I1 authorisation remains ambiguous (commit subject “authorize I1” vs ratified D2 status “ready for I1 implementation authorisation”). | **Medium** | conflict | `…041`; until ruled, I1 is treated as **not authorised**. |
| **F-049-6** | S1/S3 are implemented but have **no independent verification**, and no verification task is currently authorised. | Medium | verification gap | **DISCHARGED (PASS) 2026-09-14** — `…030` executed under the blanket authorisation `…050` (its gate was authorisation only); 15 independent probes + 3 migration probes pass on the disposable clone `ct_s13_iv_20260914`; report `…056`. |
| **F-049-7** | Production remains gated (**G0-D open**; 34 pre-existing + 2 B2 outstanding migrations). | High | deployment gate | No production work of any kind; not requested here. |
| — | Non-blocking observations carried forward from earlier verification: F-025-1 (numeric-text canonicalisation breadth), F-025-2 (dead `return None`, `backend/domain/line_items.py:350`), B1 V1R R1–R6 (all P3). | Low | recorded | Unchanged; dispositions belong to the PO via `…028`. |

---

## 6. Environment / deployment state (fresh, this task)

| Environment | B1 schema | B2 schema | Notes |
|---|---|---|---|
| Disposable clones (`carbontally_b2_clone_20260913`, `ct_b2_iv_20260913`) | present (11 `disclosure_*` tables) | present (`evidence_line_items`) | retained; **not** a persistent environment; used for V1R/V2 evidence |
| Local dev/application DB (`postgres` @ 127.0.0.1:54426) | **absent** | **absent** | 116 public tables |
| Integration DB (`carbontally_test`) | **absent** | **absent** | 114 public tables; not suitable as the §20.3 parity clone |
| QA (dedicated) | **does not exist** | **does not exist** | recommended target for `…029`; **not yet named or authorised** |
| Production (Supabase) | **absent** | **absent** | 21 applied / 34 outstanding (per records); **deployment prohibited** while G0-D is open |

**Migrations applied by this task: NONE.** **Production deployment authorised: NO.**

---

## 7. Out-of-scope items (intentionally not performed)

* Any B3/B4, P1/P2, RLS, Phase 8-X, Phase 9, Insight, S2/S4/S5/S6/S7/S8, D16/LEG, or Phase 9 work.
* Any migration authoring or application; any database write; any backfill or historical re-extraction.
* Any production access, runbook or configuration change.
* Any commit, push, branch or history operation; any worktree reset/clean/stash.
* Any modification of the playbook, of B1/B2 artefacts, or of any unrelated file.

---

## 8. Stop conditions fired (orchestrator §26)

| # | Stop condition | Fired? |
|---|---|---|
| 1 | Required PO decision missing (**D-01** closure; D-02 environment; D-07/D-08/D-11/D-12/D-13/D-17/D-18 as applicable) | **YES** |
| 2 | Required implementation/verification authorisation missing (all 20 tasks) | **YES** |
| 3 | Required environment not explicitly selected/authorised | **YES** |
| 6 | PO closure required but not recorded (B2 closure record absent) | **YES** |
| 7 | Phase 8-X / Phase 9 conflict unresolved | **YES** |
| 8 | Production gated (G0-D) | **YES (no production work attempted)** |
| 10 | Authoritative records in conflict (F-049-1, F-049-4, F-049-5) | **YES** |
| 4/5/9/11/12/13 | prerequisite not closed / IV unavailable / scope expansion / worktree isolation / evidence unavailable / failure outside scope | NO |

---

## 9. Repository state

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `37b19d13723b0b1eabceeade86ce1615a98ab400` (unchanged; no commit made) |
| Staged | 0 |
| Tracked modifications | 218 (pre-existing; unchanged) |
| Commits made by this task | **NONE** |
| Migrations added by this task | **NONE** |
| Uncommitted authorised artefacts | none (no task was executed) |
| Unrelated changes preserved | B2 implementation artefacts (`??`), the GA4 commit, 218 tracked modifications — all untouched |
| File created by this task | `docs/cline/reports/CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260913-049.md` (this report only) |

---

## 10. Recommended next governed action (single)

> **The PO issues the §4.1 Gate-A authorisation for `CT-P8-B2-CLOSURE-RECORD-20260913-028`** (one line, including the F-025 dispositions), and — if the chain is to continue without a further stop — the **Gate-B authorisation naming the non-production environment** for `…029`.

On receipt, the execution loop resumes at `…028`, then `…029`, and continues to the next gate (`…030`/`…031` authorisations, or the D-07 ruling for the X track) without redoing completed work.

No other scope is recommended, and none is invented.

---

## 11. Final verdict

### `PROGRAMME PARTIALLY COMPLETE — EXECUTION BLOCKED BY GOVERNANCE / PREREQUISITE GATES`

**Sequential execution of the remaining Phase 8 / Phase 8-X programme is not possible at this time.** The playbook is consumed and reconciled; the ledger is complete; the earliest eligible task is `CT-P8-B2-CLOSURE-RECORD-20260913-028`; its authorisation gate — like the authorisation gate of every other planned task — is **unsatisfied**, and the master execution instruction expressly does not supply it. Five hard gates are live: missing PO closure record (F-049-1), missing per-task authorisations (F-049-2), no B1/B2-bearing environment (F-049-3), the unresolved Phase 8-X/Phase 9 conflict (F-049-4), and the open G0-D production hold (F-049-7).

**Invariants preserved:** no PO decision invented; no implementation performed without authorisation; no verification claimed; no closure declared; no production touched; no scope expanded; no claim made without evidence.

*STOP — gate 1 reached. Awaiting explicit PO authorisation for `…028` (and the environment name for `…029`).*

---

# RECONCILIATION UPDATE — 2026-09-13 (appended; the earlier gate analysis above is retained as history)

> The gate analysis in §§1–11 above was correct **at the time it was written** (the programme was blocked on governance gates). The gates have since been satisfied by the PO blanket authorisation `…050`, the PO Phase 8-X / Phase 9 ruling `…040` (**no Phase 9**), and the per-batch authorisations. This section records the reconciled, current state.

## R1. Batch ledger (as executed)

| Batch | Contract / decisions | Implementation | Verification | Closure |
|---|---|---|---|---|
| **B1** disclosure model foundation | ratified (`PQ-*`, `D*`) | applied | runtime suites green | closed (`…010` lineage) |
| **B2** evidence line items | B2 contract §20.x + `F-B2-*` dispositions | applied | runtime suite green | closed (`…028`) |
| **B3** disclosure integration | B3 contract `…031`; `B3-D1` PO-answered | 2 migrations + projection domain/data/service/API | fresh-clone V3: **175/175 PASS**, 7 migrations `rc=0`×2, zero removed diff lines | **closed** (`…051`) |
| **B4** narrative + finalisation + frozen artefact | B4 contract `…034`, Amendments 1–6 | 2 migrations + 5 modules + API surface | unit **EXIT=0**, integration **EXIT=0**, B4 runtime **19/19**, mandate/gate/audit/immutability proofs | **closed at gate V4 (`…052`)** |

## R2. PO decisions recorded in this phase (durable)

`…040` no Phase 9 (Phase 8-X stays in the Phase 8 programme) · `B3-D1` capability ≠ regulatory requirement · **`B4-D1`** Owner **and** Admin may approve/finalise; consultants and internal staff may **never** · **`B4-D10`** B4 absorbs S4 (narrative) and S5 (frozen artefact), S7 stays inside B4 **and inside gate V4**, S6 excluded · **`B4-D5/D6/D7`** frozen artefact **mandatory**, private `report-artifacts` bucket, derived key `{organization_id}/{report_id}/{version_id}.pdf`, short-lived signed URLs after authorization, append-only `report_version_artifacts`, SHA-256, immutable key/hash, corrections via a new version, live-render for drafts only, **no** SHA-512/MD5/optional/external/exception path · **`B4-D8`** retain indefinitely, no deletion path, no invented duration, retention stays server-side/configurable in the N3 control plane · **`B4-D4`/`B4-D9`** comments stay outside B4; `A7` visibility deferred to the S6 backlog item.

## R3. Residual / carried obligations

| # | Item | Owner |
|---|---|---|
| 1 | **S6 backlog item** — frontend lifecycle UI + comment scope/`A7` visibility, built against the ratified B4 APIs (`report_comments` remains dormant) | next eligible UI batch (not B4) |
| 2 | **A1 residual** — fresh-clone zero-delta replay for the two B4 migrations | next independent verification pass |
| 3 | **N3 retention configuration** — server-side Settings/Admin control plane, must not weaken auditability or `FINAL` immutability | N3 / admin control plane |
| 4 | **`B4-D12`** commercial/entitlement gating of finalisation | PO commercial decision required first |
| 5 | **`F-030-1`** — repaired in B4 closure (test-data UUID defect); carried as closed | done (`…052` §3) |

## R4. Next eligible work (per the PO's continuation instruction)

`…037` P1 package · `…038` P2 read-only census · `…042` G0 register · `…039` RLS package. Still **gated** on their stated inputs: X1 (`…043`, needs `PX-2`/`PX-5`), `…041` (I1 PO ruling), `…046` (`A-RLS`), `…048` (external ESRS evidence). **No Phase 9. Phase 8-X remains inside the Phase 8 programme.**

### R4.1 `…037` executed (2026-09-13) — P1 decision package delivered

| Item | Result |
|---|---|
| Task | `CT-P8-P1-AUTHORISATION-PREPARATION-20260913-037` (F/E — **decision package only**, authorisation-gated, no decision prerequisite) |
| Authorisation | PO blanket `…050` + explicit PO instruction to execute `…037` |
| Deliverable | `docs/architecture/CARBONTALLY_PHASE8_P1_AUTHORISATION_DECISION_PACKAGE_20260913.md` (§0–§9) |
| Report | `docs/cline/reports/CT-P8-P1-AUTHORISATION-PREPARATION-20260913-037.md` |
| Re-verification | V1 per-line producer tabular-only · V2 AI clip duplicated (`20_000` in two modules) · V3 `source_page` = `page_count` · V4 det+AI blend path intact · V5 legacy `pdf_engine`/`upload` surface present · V6 baseline **85 tests EXIT=0** · V7 extraction path **unchanged** by B2/B3/B4 |
| Outcome | **8 decisions ready for PO ruling** (`P1-D1…P1-D8`); P1 *implementation* is **not** authorised and was **not** performed |
| Next | PO ruling on `P1-D1` (multi-line `line_items[]` shape for new documents, gated on shadow evidence) + `P1-D2…P1-D8` ⇒ then P1 implementation becomes eligible |

**Sequence note:** `…038` (P2 read-only census), `…042` (G0 register) and `…039` (RLS package) were **not** started — the playbook's documented sequence places P1 ahead of them, and each carries its own gate. `…037` is now complete pending its PO ruling.

### R4.2 P1 executed (2026-09-13) — implementation + shadow evidence + acceptance verification

| Item | Result |
|---|---|
| PO ruling | **`P1-D1`…`P1-D8` ratified (Option A)** — recorded in `docs/architecture/CARBONTALLY_PHASE8_P1_PO_DECISION_RECORD_20260913.md` |
| Delivered | `services/extraction_fidelity.py` (new, pure) · bounded hook in `services/automatic_extraction.py` · `PIPELINE_VERSION` `v3-auto-1.0` → **`v3-auto-1.1`** · `tests/unit/services/test_extraction_fidelity.py` (**35 tests**) |
| Mode control | `CARBONTALLY_P1_EXTRACTION_SHAPE` ∈ {`shadow` (**default**), `enabled`, `off`}; unknown values **fail safe to shadow** |
| Acceptance | A1–A10 **PASS** (details in `CT-P8-P1-CLOSURE-20260913-053.md`) |
| Regression | 8 suites (7 pre-existing extraction suites + the new P1 suite) → **`P1_REG_EXIT=0`**; **no test was amended, deleted or weakened** (shadow-first preserved behaviour exactly) |
| Shadow evidence | measured on the available corpus: **no false positive** on the single-line invoice or the furniture-only invoice; `suspect_rate = 3/6`; mode default `shadow` ⇒ **customer-visible change = False** |
| **Gate status** | **ENABLEMENT GATE CLOSED** — real institutional documents were not available in this environment, so per `P1-D1` the shape stays shadow-first; `enabled` is implemented and tested but not switched on |
| Migration / backfill | **none** — no schema change, no historical reprocessing (`P1-D4`) |
| Next | shadow run over a real non-production institutional document set ⇒ then PO/verifier may enable the shape for **new** uploads. Afterwards: `…038` (P2 read-only census), then `…042` G0 and `…039` RLS as their documented sequence permits |

### R4.3 `…038` P2 read-only census executed (2026-09-14)

| Item | Result |
|---|---|
| Task | `CT-P8-P2-FACTOR-CATALOGUE-CENSUS-20260913-038` (type **F**, read-only forensic) |
| Report | `docs/cline/reports/CT-P8-P2-FACTOR-CATALOGUE-CENSUS-20260913-038.md` |
| Tool | `tools/p2_census/p2_factor_catalogue_census.py` — read-only, reproducible; `BEGIN TRANSACTION READ ONLY`; **refuses production-looking DSNs** and requires `CARBONTALLY_P2_CENSUS_ALLOW=non-production` (both refusals demonstrated) |
| Environment | `carbontally_qa_phase8` (non-production) · `CENSUS_EXIT=0` · no writes, no data change, no migration |
| **Structural findings** | **P2-C1 EF-E live in 3 product paths** (`api/v3_emissions.py:549`, `api/v3_processing_workflow.py:1113` — the processing mapping picker, `services/automatic_processing.py:872`) · **P2-C2** D23's `unit_substring` mechanism exists and is applied on only 2 surfaces (`api/v3_operations.py:975`, `:1585`) · **P2-C3** 11 call sites: 4 tolerant / 7 exact-only · **P2-C4** `units_equivalent` applies no qualifier rule by design |
| Data findings | 15 factors · **0 qualified-unit factors** · **14/15 NULL units** · 1 distinct unit · exact-vs-substring delta **0** (because the qualifier vocabulary is absent locally, **not** because EF-E is fixed) |
| Separation | **EF-E structurally confirmed**; **EF-A/EF-D unquantifiable locally** — explicitly **not invented** |
| Carried forward | (1) **P2 remediation** = adopt qualifier tolerance on the three product sites (separate authorised batch, no factor-data change); (2) EF-E/EF-A/EF-D **magnitude** requires a read-only session against the real catalogue (production boundary respected); (3) local NULL-unit gap recorded for the seed owner |
| Next | **`…042` G0 register**, then **`…039` RLS package**, per their documented gates |

### R4.4 `…042` G0 register executed (2026-09-14)

| Item | Result |
|---|---|
| Task | `CT-P8-G0-GATE-RECONCILIATION-20260913-042` — **decision register only** (F/E) |
| Deliverables | `docs/architecture/CARBONTALLY_PHASE8_G0_GATE_RECONCILIATION_REGISTER_20260914.md` · `docs/cline/reports/CT-P8-G0-GATE-RECONCILIATION-20260914-042.md` |
| Verified inputs | `-008` authoritative status list · QA `public` tables = **133** · repo migration files = **63** (the `-008` "34 outstanding" figure is stale) · production **untouched** |
| Reconciliation | **5 CLOSED / 4 OPEN** — closed: G0-B · **G0-C (reconciled to CLOSED BY EXECUTION** — B1–B4 + P1 approved and delivered under `…050` and per-batch rulings**) · G0-E (closed by B2, `…028`) · G0-F · G0-I. Open: **G0-A** (E1 evidence → `…048`) · **G0-D** (production strategy; prohibition restated, figure corrected to 63) · **G0-G** (Phase 8-X PX-2/4/5/6/7 → `…043`) · **G0-H** (RLS separate workstream — the `A-RLS` confirmation) |
| Implemented | **nothing** (register only) — no product code, migration, schema or data change |
| Decision surfaced | **G0-H / `A-RLS`** — PO confirmation required before `…039`/`…046`; cannot be inferred from any ratified decision (the RLS verified so far is the B-chain's own posture, not the separate RLS workstream) |
| Next | **`…039` RLS package** — blocked only by G0-H; `X1`/`…041`/`…048` remain gated on `PX-2`/`PX-5`, the I1 ruling and external ESRS evidence |

### R4.5 **G0-H / `A-RLS` RULED — Option A (2026-09-14): RLS confirmed as a separate authorised Phase 8 workstream**

| Item | Result |
|---|---|
| PO ruling | **RLS is a separate authorised workstream**; `…039` may proceed as its own batch (posture verification + gap remediation on surfaces not covered by the B-chain: consultant/client isolation, PE, legacy surfaces, admin control plane). `…046` remains gated on the same authorisation and proceeds when its prerequisites are satisfied. |
| Recorded in | G0 register §3 (`…042` deliverable) — **G0-H → CLOSED (Option A confirmed)** |
| Constraints restated by the PO | no RLS expansion into product redesign or commercial/subscription decisions · production prohibition preserved · no historical backfill/re-extraction · no test weakening · no unrelated worktree cleanup · **no Phase 9** |

### R4.6 `…039` RLS remediation plan executed (2026-09-14)

| Item | Result |
|---|---|
| Task | `CT-P8-RLS-SECURITY-REMEDIATION-PLAN-20260913-039` (type **F** — RLS planning) |
| Deliverable | `docs/architecture/CARBONTALLY_PHASE8_RLS_SECURITY_REMEDIATION_PLAN_20260914.md` |
| Posture census (read-only, non-production QA) | **133/133 tables RLS-enabled** (`rls_disabled = 0`) · **`FORCE RLS` = 0** (consistent with D-11) · 54 org-scoped tables, **49 with ≥1 policy** · **policies admitting `anon`/`public` = 0** · **`anon` grants on org-scoped tables = 182 → fail-closed least-privilege, NOT an exposure** |
| Gaps found | **5 org-scoped tables with RLS but no policy** (fail-closed, functionally inaccessible): `billing_credit_ledger`, `billing_orders`, `billing_payment_records`, `billing_storage_usage`, `data_discovery_requests` — **independently corroborating D-2** |
| Blocking register | **D-1…D-13** reproduced verbatim from the RLS hold register §8 (including the **D-13 sequence discrepancy**) |
| Implemented | **no code, migration or policy change** — planning/verification only (as the task type requires); no production access |
| Next | **PO rulings on D-1…D-13** — **D-1 (anonymous-grant containment) is the natural first step and needs no RLS change**; then steps 2–5 of the plan, each independently verified |

### R4.7 **RLS DECISION REGISTER — Option B ruled; `D-1` EXECUTED and independently verified (2026-09-14)**

| Item | Result |
|---|---|
| PO ruling | **Option B approved** — **`D-1`, `D-2`, `D-11`, `D-13` APPROVED**; **`D-4`…`D-10`, `D-12` remain explicit gates** (return to the PO when their steps are reached) |
| Recorded in | RLS plan Amendment 1 (`docs/architecture/CARBONTALLY_PHASE8_RLS_SECURITY_REMEDIATION_PLAN_20260914.md`) |
| **`D-1` / RLS-4A-1 executed** | migration `20260920000000_p8_rls_anon_grant_containment.sql` — **`REVOKE`-only**, no `ENABLE`, no policy change, no data touched; QA/non-production only; `rc=0` ×2 (idempotent) |
| Result | `anon` grants in `public` **458 → 4** (all 4 on the **D-4-governed** `emission_factors`, deliberately untouched) · `anon` grants on org-scoped tables **182 → 0** · `anon`-admitted policies **0 → 0** |
| Parity (proven) | `authenticated` grants **810 → 810** · policies **197 → 197** · RLS-enabled tables **133 → 133** · `FORCE RLS` **0** (**D-11** honoured) |
| Verification detail | `has_table_privilege('anon','public.messages',…) = false` cleared a **view false-positive**: `messages`' ACL is `postgres, authenticated, service_role` — no real `anon` grant existed; `PUBLIC`-derived rows = 0 |
| `D-2` | **Recorded only** — production prohibition preserved; no production remediation; the 5 QA policy-less tables remain recorded gaps |
| `D-11` | **Confirmed** — `FORCE RLS` remains deferred and was not enabled |
| `D-13` | **Resolved** — governed sequence **retained**: `RLS-4A (4A-1 ✅ → 4A-2 pending) → RLS-5 → RLS-3 → RLS-2 → RLS-1 → verification`; **F-5/F-6 explicitly assigned** to RLS-4A-1/4A-2 so the function/`EXECUTE` hardening cannot be silently omitted (execution still gated on `D-5`/`D-12`) |
| Next | `…046` when its prerequisites are satisfied; RLS-4A-2 and steps 2–5 await their gates (`D-4`…`D-10`, `D-12`) |

### R4.8 `…046` (S2 + report-table RLS) — prerequisite analysis, **BLOCKED ON A PO DECISION** (2026-09-14)

Task `CT-P8-S2-REPORT-TABLE-RLS-AND-SCHEMA-20260913-046` (type G) is gated on **D-17 / `A-RLS`** (report-table RLS posture), which the REST plan records as **PO-owned and undecided** ("blocks S2 only"; "not the production RLS hold — must not be conflated with it"). The `A-RLS` *workstream* gate is now satisfied (G0-H, Option A), but **D-17 itself is still an open posture decision**. Verified findings:

| # | Finding | Evidence |
|---|---|---|
| 1 | The **two un-policied report tables** are **`report_versions`** and **`report_comments`**: RLS **enabled**, **0 policies**, **no `organization_id`** (tenancy only via `report_id`) | live census (`pg_class`/`pg_policies`) |
| 2 | `report_generation_queue` is already policed (4 policies, has `organization_id`) | live census |
| 3 | `…046`'s S2 scope is **partly superseded by ratified B4 decisions** — executing it literally would violate them or duplicate ratified objects: `report_versions.narrative_overlay` ↔ **B4/`A1`** (no report-wide narrative path); `pdf_sha256`/`content_hash` ↔ **`B4-D7`** (`report_version_artifacts.content_sha256`, append-only, one per finalised version); `report_comments` additions/policies ↔ **`B4-D4`/`B4-D9`** (comments outside B4, table stays dormant, `A7` visibility deferred to **S6**) | B4 migrations + decision record; repo grep shows `narrative_overlay` unused and the only `content_hash` is `calculation_snapshots` |
| 4 | **Genuinely outstanding and non-conflicting:** the **`is_current` single-valued guarantee** — only PK and `(report_id, version_number)` indexes exist (the latter duplicated); nothing enforces one current version per report (data currently clean: 0 reports with two currents) | live indexes + data check |

**Action taken:** none implemented — `…046` is a type-G implementation task and its posture decision is PO-owned, so no migration, code or policy change was made. **No production access; no commit.**

**Decision raised to the PO** (`A-RLS` / D-17 + scope reconciliation): Option **A** = reconciled S2 remainder (`is_current` guarantee + documented app-layer-only posture + supersessions recorded); Option **B** = execute S2 literally (reopens A1/D7); Option **C** = A + full policy coverage via a new `report_id → report_generation_queue.organization_id` policy model. **Recommendation: A.**

**On receipt:** record the ruling here, execute `…046` end-to-end (QA-only, additive, independently verified: `rc=0` ×2, parity, cross-tenant DENY / same-tenant ALLOW where applicable), then continue automatically to the next eligible Phase 8 / Phase 8-X work.

### R4.9 `…046` (S2) EXECUTED AND CLOSED — PO Option A (2026-09-14)

| Item | Result |
|---|---|
| PO ruling | **D-17 / `A-RLS` / S2 — Option A** (reconciled S2 remainder): documented **app-layer-only** RLS posture for `report_versions`/`report_comments` (RLS stays enabled, **zero policies by design = fail-closed**); implement the **`is_current` single-valued guarantee**; **formally close** the superseded S2 scope; no new policy model, no narrative path, no duplicate hashes, no comment functionality |
| Delivered | migration `20260921000000_p8_s2_is_current_single_valued.sql` · regression suite `backend/tests/integration/test_s2_is_current_invariant.py` (4 tests) · closure report `CT-P8-S2-CLOSURE-20260914-046.md` |
| The guarantee | `CREATE UNIQUE INDEX report_versions_one_current_per_report ON public.report_versions (report_id) WHERE is_current` — DB-enforced, so concurrent "new version" operations cannot both become current |
| Verification | `rc=0` ×2 (idempotent) · index definition exactly as ruled · existing data valid (0 violations) · **second current version rejected by `report_versions_one_current_per_report`** (constraint name captured) · **different reports allowed** · `(report_id, version_number)` semantics intact · fail-closed posture verified (RLS enabled, 0 policies, 0 `anon` grants) · probes rolled back (zero residue) |
| Regression | `test_report_versions` + `test_report_lifecycle` + `test_reports` + the S2 suite → **25 tests, `S2_REG_EXIT=0`** (proves the index does not break version creation/lifecycle) |
| Supersessions closed | `narrative_overlay` → B4/`A1` · `pdf_sha256`/`content_hash` → `B4-D7` · `report_comments` → `B4-D4`/`B4-D9` → **S6** |
| Posture documentation | recorded as `COMMENT ON TABLE` on **both** tables (originals preserved, posture appended) + comment on the index |
| **F-046-1 (operational)** | the integration harness **TRUNCATEs its target database** before each suite (conftest `pool` fixture; guards only `postgres`/`supabase_db_carbon_ledger`). Pointing it at the persistent `carbontally_qa_phase8` **reset that environment's test rows** (schema intact; index verified present). **No production/demo/authoritative DB affected** — the guarded names are absent locally and no production connection was opened. **Convention adopted: run integration suites against a disposable clone, never a persistent environment.** |
| Next | RLS-4A-2 + RLS steps 3–5 gated on `D-4`…`D-10`, `D-12`; S6 carries comments/visibility; P1 enablement awaits real-document shadow evidence; P2 EF-E remediation is a separate authorised batch |

### R4.10 **OPERATIONAL CONTROL — F-046-1 ENFORCED (2026-09-14, programme-wide invariant)**

| Item | Result |
|---|---|
| PO control | **The integration harness must NEVER be pointed at a persistent environment whose data matters** — use a disposable database/clone; not persistent QA; not investor-demo; never production; never an authoritative data-bearing environment. Persistent QA only for demonstrably non-destructive operations unless a disposable clone exists. Verify the target identity and the harness's destructive setup **before** every integration suite. |
| Recorded in | **`AGENTS.md` §55.1** (durable, agent-facing invariant) · this playbook section · S2 closure report §5 (F-046-1) |
| **Enforced in code** | `backend/tests/integration/conftest.py`: the `pool` fixture now refuses any target whose name matches **`qa` / `demo` / `investor` / `prod` / `live`** (plus the pre-existing forbidden main DBs) with an explicit **F-046-1** `RuntimeError` — a mis-pointed run fails **before** any `TRUNCATE`. Additive: the harness only became stricter. |
| Enforcement proof | `INTEGRATION_DATABASE_URL=…/carbontally_qa_phase8` ⇒ `RuntimeError: refusing to run the integration suite against 'carbontally_qa_phase8': the name matches the protected persistent marker 'qa', and this fixture performs DESTRUCTIVE setup (TRUNCATE … RESTART IDENTITY CASCADE). (PO operational control F-046-1.)` |
| Compliant target created | disposable clone **`ct_int_20260914`** (`CREATE DATABASE … TEMPLATE carbontally_qa_phase8`): **133** public tables — full B-chain schema — plus the S2 index inherited |
| Compliant run proof | S2 invariant + report versions + lifecycle + reports + B4 finalisation runtime ⇒ **44 tests, `CLONE_EXIT=0`** against `ct_int_20260914` |
| Standing convention | integration suites target **`ct_int_20260914`** (or a fresh `ct_*` clone); `carbontally_test` remains the harness default; **never** a persistent environment |
| Report obligation | F-046-1 must be **restated in every subsequent implementation/verification report** |

### R4.11 **P2 EF-E REMEDIATION PACKAGE — PREPARATION COMPLETE (2026-09-14), holding at the D-A/D-B/D-C gate**

| Item | Result |
|---|---|
| Authority | PO authorisation "P2 EF-E REMEDIATION PACKAGE PREPARATION" (preparation only) under `…050` |
| Deliverable | `docs/architecture/CARBONTALLY_PHASE8_P2_EFE_REMEDIATION_PACKAGE_20260914.md` — §1–§9 |
| Boundary respected | **no** product code, factor data, matching behaviour, migration, DB data or production change; no policy chosen silently |
| Paths traced | **S1** `api/v3_emissions.py:549` (`GET /api/v3/factors` — factor search; **High**, user-visible invisibility) · **S2** `api/v3_processing_workflow.py:1113` (`/items/{id}/mapping-options` — the mapping picker; **High**, can emit a *misleading dead-end* because `has_factors` is computed from the same filtered set) · **S3** `services/automatic_processing.py:872` (`_prefer_aggregate_factor`; **Medium**, retains a sub-component factor; guarded, never fabricates) |
| **Decisive new finding** | **EF-E is selection-side only.** `resolve_unit_for_factor` (`core/units.py`) is *already* qualifier-tolerant (`unit in factor_unit or factor_unit in unit`), so calculation, snapshots and provenance need **no** change — which bounds the remedy to query construction |
| D23 evaluated | `unit_substring` = `ILIKE '%<normalised>%'`, ranking unchanged (`(ef.unit = $n) DESC`). Strength: reuses the sanctioned branch. Risk: blanket substring can over-match **short/unaliased units**. D23's "single normaliser, **do not add a second**" is respected by both options |
| Contract | C1 semantics · C2 tolerance rule (T1 reuse vs **T2 strict qualifier-aware helper**) · C3 ALLOW/DENY (incl. currency/physical negative and `unit=None` unchanged) · C4 cross-tenant isolation (system catalogue unchanged; customer path untouched) · C5 selection behaviour (supersets only, deterministic ranking) · C6 affected surfaces · C7 regression · C8 blast radius · **C9 zero migration/DB impact** |
| Implementation spec | I1 `data/emission_factors.py` (clause construction) · I2 S1 · I3 S2 · I4 S3 · I5 `core/units.py` (T2 only). Explicitly unchanged: calculation engine, `CURRENCY_UNITS`, customer-factor path, RLS/grants/policies, migrations, provenance |
| Verification plan | unit ALLOW + 4 negatives (incl. the short-unit over-match probe) · integration on a **disposable clone only (F-046-1)** · **cross-tenant DENY (11) + global-catalogue/all-authorization checks (12–13)** · regression (14–15) · zero-schema-delta parity (16) |
| Gate | **D-A** scope (S1+S2 vs S1+S2+S3 → rec. **b**) · **D-B** semantics (T1 vs T2 → rec. **T2**) · **D-C** case-sensitivity asymmetry (rec. keep, **a**) |
| Next | PO ruling on D-A/D-B/D-C ⇒ then the EF-E implementation batch (QA-only, additive, disposable-clone verification); nothing else in the programme is unblocked by this package |

### R4.12 **P2 EF-E REMEDIATION — IMPLEMENTED, VERIFIED AND CLOSED (2026-09-14)**

| Item | Result |
|---|---|
| PO rulings | **D-A(b)** S1+S2+S3 · **D-B T2** strict qualifier-aware rule · **D-C(a)** retain the selection↔calculation asymmetry |
| Implemented | `core/units.py` (`split_qualified_unit`, `unit_matches_with_qualifier`, `qualifier_match_clause` — one rule, no second vocabulary) · `data/emission_factors.py` (`unit_qualifier_tolerant`, strict clause; default/D23/ranking unchanged) · **S1** `api/v3_emissions.py` · **S2** `api/v3_processing_workflow.py` · **S3** `services/automatic_processing.py` |
| Tests added | `tests/unit/test_units_qualifier.py` · `tests/unit/data/test_emission_factors_unit_selection.py` · `tests/unit/services/test_efe_selection_sites.py` → **41 new tests, all pass** |
| Positive proof | DB probe (clone, rolled back): **legacy exact = 0**, **strict T2 = 1**, D23 substring = 1 · S3 upgrades a component factor to the qualified aggregate · exact-match precedence asserted in all modes |
| Negative proof | `litres` ↛ `kWh (Gross CV)` (**0 rows**) · short unit `t` ↛ qualified (**0 rows**) · unrelated units rejected · `unit=None` no clause · no aggregate ⇒ original preserved |
| Security proof | customer-factor + RLS isolation suites green on the clone (**54 tests**) · global catalogue unchanged · no auth/RLS/policy diff |
| Regression | unit groups **100% pass** · D23 `unit_substring=True` unchanged · **Phase 8 suites (B1/B2/B3/B3-V3/B4/S2/lifecycle/versions) `P8_EXIT=0`** |
| Boundaries held | **zero migration / zero schema change** (no stop needed) · **no factor-catalogue data modified** (`residue_after_rollback=0`) · `resolve_unit_for_factor`, snapshots, provenance, artefacts, customer tenancy and production untouched |
| **F-046-1** | every destructive run used the disposable clone `ct_int_20260914`; identity verified first; the harness now refuses `qa`/`demo`/`investor`/`prod`/`live` names in code |
| Closure | `docs/cline/reports/CT-P8-P2-EFE-CLOSURE-20260914-054.md` |
| Next | RLS-4A-2 + steps 3–5 (gated on `D-4`…`D-10`, `D-12`) · S6 backlog (comments + `A7`) · P1 enablement (external evidence) |

### R4.13 **FRESH-CLONE ZERO-DELTA REPLAY — B4 A1 RESIDUAL DISCHARGED (2026-09-14)**

| Item | Result |
|---|---|
| Driver | B4 closure `…052` §2 carried the fresh-clone replay as an explicit residual; RLS-4A-1 and S2 had only been proven on the persistent QA env |
| Method | `CREATE DATABASE ct_b4v4_20260914 TEMPLATE ct_b3_v3_20260913` (a verified **pre-B4** base) → fingerprint 3696 pre-existing objects (tables+RLS flags, policies, grants, indexes) → apply migrations → re-fingerprint → order-independent delta (`grep -Fxv`; `comm` warns across collations) |
| **B4 idempotency** | B4-1 **`rc=0`×2** · B4-2 **`rc=0`×2** |
| **B4 zero-delta** | **added 44 / removed 0**; **added_unattributable = 0**; added = 2 TABLE + 4 POLICY + 9 INDEX + 29 GRANT; new tables `rls=true force=false`; policies = the ratified B4 read/write + read/insert posture |
| Other migrations | RLS-4A-1 **`rc=0`×2** · S2 `is_current` **`rc=0`×2** on the same fresh base |
| Posture reproduced | S2 index present · RLS-enabled tables **133** · authoritative `anon` check: **1 relation only — `emission_factors`** (D-4 excluded) |
| **Verifier trap recorded** | `information_schema.role_table_grants` over-reports `anon` grants (3 phantom rows for `messages`; ACL has no `anon`, `has_table_privilege` = false) → **always use `has_table_privilege`/`relacl`**, never the view alone. Re-check of persistent QA after the session break confirmed **no regression** (still exactly 1 relation). |
| F-046-1 | disposable clones only; `CREATE DATABASE … TEMPLATE`; QA touched read-only; no production |
| Report | `docs/cline/reports/CT-P8-VERIFICATION-FRESH-CLONE-REPLAY-20260914-055.md` |
| Bookkeeping | B4 closure `…052` §2 A1 row amended: **residual → DISCHARGED (PASS)** |
| Next eligible | all remaining items are gated: RLS-4A-2 + steps 3–5 (`D-4`…`D-10`, `D-12`) · S6 (comments + `A7`) · P1 enablement (external documents) · EF-A/EF-D magnitude (real catalogue) · X1/`…041`/`…048` (`PX-2`/`PX-5`, I1, external ESRS) |

### R4.14 **`…030` S1/S3 INDEPENDENT VERIFICATION EXECUTED — F-049-6 DISCHARGED (2026-09-14)**

| Item | Result |
|---|---|
| Driver | `F-049-6` (Medium, verification gap): S1/S3 implemented with **no independent verification**; `-023` §10.6/§11.1 evidence gap |
| Gate test applied | `…030`'s only gate was **authorisation** (*"no PO decision prerequisite"*) → satisfied by the blanket authorisation `…050` → **executable (type A)**. Contrast: **RLS-4A-2** carries a *"separately authorized change"* requirement plus a **NOT AUTHORIZED** status field on a **security** control → **type C**, not executed |
| Environment | disposable clone **`ct_s13_iv_20260914`** (`pg_dump --schema-only` of QA, no rows); `current_database()` verified **before** any destructive statement; QA read-only; production untouched |
| Regression baseline | S1/S3 integration **12 passed** · unit **78 passed** |
| Independent probes | `test_s1s3_iv_invariants.py` **8 passed** (IV-S1-1…5, IV-S3-5…7) · `test_s1s3_iv_supersession.py` **7 passed** (IV-S3-A1…A7) |
| Post-probe re-run | integration **20 passed** · unit **85 passed** (after the migration-DDL probe) |
| Strongest probe | **IV-S1-1** — forces the tuple-conflict `INSERT` *after* `create()`'s demotion and asserts the demotion rolled back (`async with conn.transaction():` proven, not assumed) |
| §7.3 legacy case | **IV-S1-3** reproduces two `is_current=TRUE` rows (index dropped for the probe, restored in `finally`, restoration asserted) → single and batch reads agree on the highest version |
| DB-layer invariant | **IV-S1-2** — duplicates are **unreachable** even for a raw writer (S2 partial unique index), not merely masked |
| **Migration claims proven** | **additive**: delta = exactly **3** objects (status column, CHECK, comment) out of **3,423** fingerprinted · **idempotent**: `rc=0`×2, second-apply delta empty · **NO RLS change**: RLS flags + **all 197** public policies + all ACLs byte-identical |
| Security | `anon` denied on `report_versions`; RLS enabled with **0 policies** ⇒ default-deny ⇒ **no client bypass** of the guarded transition; approval version-bound and non-inherited; denied/invalid transitions change nothing and emit no audit event |
| New findings | **IV-OBS-1** (Low, test hygiene): 3 legacy S1 tests leak rows — clone-only, no product impact, left unfixed to keep the IV boundary clean · **IV-OBS-2** (Low, gated): `authenticated` retains blanket grants (inert under deny-all RLS) — the declared scope of `RLS-4A-2` |
| Verdict | **S1 PASS · S3 PASS** — implemented + tested + **independently verified** (verification verdict only, not programme acceptance) |
| F-046-1 | enforced in code and restated in the report |
| Report | `docs/cline/reports/CT-P8-S1S3-INDEPENDENT-VERIFICATION-20260914-056.md` |
| Bookkeeping | S1/S3 rows → **A — COMPLETE — INDEPENDENTLY VERIFIED**; `…030` row → **EXECUTED**; `F-049-6` → **DISCHARGED (PASS)** |
| Decision recorded (NOT invented) | **RLS-4A-2 authorisation**: `REVOKE TRUNCATE, REFERENCES, TRIGGER … FROM authenticated` (non-production, `REVOKE`-only, own verification gate) — register requires separate authorisation per group; steps 3–5 remain gated on `D-4`…`D-10`, `D-12` |

### R4.15 **FINAL PROGRAMME REPORT ISSUED — PROGRAMME EXECUTION EXHAUSTED (2026-09-14)**

| Item | Result |
|---|---|
| Report | `docs/cline/reports/CT-P8-FINAL-PROGRAMME-REPORT-20260914-057.md` |
| Verdict | **All executable non-gated Phase 8 / Phase 8-X work is implemented, independently verified and closed. Zero items remain "implemented / verification pending".** |
| Stop condition met | directive §18(1): no remaining task can safely be executed under the blanket authorisation and current decisions; the residual items are PO decisions (§5), external inputs (§4) or ruled-out scope (§6) |
| Consolidation | **COMPLETE** (B1 B3 B4 S1 S2 S3 S4 S5 S7 P1-package P2 P2-EF-E RLS-4A-1 G0 `…040` `F-046-1` `F-049-6` `F-049-4`) · **PENDING: none** · **EXTERNAL** (`…048`, P1 enablement, `…029`, EF-A/EF-D, X deployment access) · **TRUE PO DECISION** (D-PO-1…D-PO-11) · **OUT OF SCOPE** (Phase 9, GA4, production) |
| Boundary confirmations | production **untouched** · investor demo **untouched** · QA **read-only** · destructive work on disposable `ct_*` clones only · **F-046-1 enforced in code** · **no Phase 9 work** · no secrets · verified artefacts unmodified |
| Clones | `ct_s13_iv_20260914` (this pass), `ct_b4v4_20260914`, `ct_int_20260914`, `ct_b3_v3_20260913`, `ct_b2_iv_20260913` |
| Handoff | PO response to the §6 decision backlog (recommended minimum batch listed in the report §10) |

### R4.16 **ORCHESTRATION PASS — RECONCILED; PHASE 8-X X1 BLOCKED ON `PX` DECISIONS (2026-09-14)**

| Item | Result |
|---|---|
| Task | `CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260914` (orchestration: Phase 8 → Phase 8-X → OHD) |
| Reconciliation | Repository evidence re-verified: **B1 closed · B2 IV PASS (closure record missing) · B3 CLOSED (V3 PASS) · B4 CLOSED at gate V4 · S1/S3 IV PASS (`…056`) · S2 closed · S4/S5/S7 inside B4 · P1/P2 packages closed · P2 EF-E closed · RLS-4A-1 closed** → **nothing was reimplemented** (no duplicate contract, migration, API or rerun) |
| **OHD scope** | **OUT OF SCOPE this cycle** per PO clarification (`…` 2026-09-14): OHD classification/remediation/registers **not** performed and the OHD section of the master instruction is **superseded**. One incidental Phase 8-adjacent observation recorded only (Running dev DB still lacks the B1/B2 schema → same `F-049-3`/`…029` item, blocked on `D-02`); **not actioned** |
| Ledger updates | `C-B3-1` → **CONFIRMED — CLOSED** (PO §5 baseline = as-built; B3 **not** reopened) · `D-B3-13` → **RESOLVED: (a) advisory only, no blocking rule** (PO §4) · draft retention/replacement/deletion → **routed to report-lifecycle/B4**, not B3. Recorded in the B3 PO decision record §11 |
| Phase 8 verdict | **PHASE 8 PARTIALLY COMPLETE — BLOCKED BY PO/GOVERNANCE ITEMS** (no implementable Phase 8 work lacks authorisation; what remains is PO decisions + one missing PO closure statement) |
| Phase 8-X verdict | **PHASE 8-X NOT COMPLETE — BLOCKED BY PO/GOVERNANCE/DEPENDENCY ITEMS** |
| Phase 8-X ownership | RESOLVED (`…040`: no Phase 9; Phase 8-X inside Phase 8) |
| **Blocking decision (X1/`…043`)** | **`PX-2`** (confirm the Phase 8-X MUST set M1–M6 + initial release boundary) · **`PX-4`** (authorise platform access — provider API/console + **read-only production DB role**; touches the **production boundary**) · **`PX-5`** (authorise a heartbeat schema change **or** require reuse-only). Without these, X1 cannot be specified or authorised → **STOP before X1 implementation** |
| Other pending PO items | `…028` B2 closure statement (+ authorisation) · `…029` name the non-production environment (`D-02`) · `RLS-4A-2` separate security authorisation · RLS steps 3–5 (`D-4`…`D-10`, `D-12`) · S6 allocation + comments + `A7` · I1 ruling · S8/D16 authorisations · external: `…048` ESRS evidence, P1 real documents, EF-A/EF-D real catalogue |
| Production | **NOT AUTHORISED · NOT TOUCHED** — G0-D open; 34 pre-existing + 2 B2 migrations unapplied to production; no deployment authorisation |
| Artefacts | `docs/cline/reports/CT-P8-FINAL-PROGRAMME-REPORT-20260914-057.md` §13 (status, 8-X, production, verdicts) · B3 PO decision record §11 |
| Worktree | branch `main` · HEAD `37b19d1` · staged 0 · tracked mods 229 (unchanged) · **0 tracked files changed by this pass** · **no commits** |

### R4.17 **PO DECISIONS OF 2026-09-14 EXECUTED — RLS-4A-2 DONE; B2 CLOSURE RECORD FOUND; X1 FEASIBILITY COMPLETE (2026-09-14)**

| Item | Result |
|---|---|
| PO decisions consumed | items 1–6 of 2026-09-14: X1 bounded set · provider/production access deferred · heartbeat reuse-first · B2 closure · QA environment named · **RLS-4A-2 authorised** |
| **RLS-4A-2 (item 6)** | **IMPLEMENTED + VERIFIED.** New migration `20260922000000_p8_rls_4a2_authenticated_grant_hardening.sql` (REVOKE-only): `authenticated` non-DML privileges **119 → 0** on `carbontally_qa_phase8` (TRUNCATE/REFERENCES/TRIGGER/**MAINTAIN**); DML preserved (SELECT 125 / INSERT 109 / UPDATE 108 / DELETE 108); policies 197 and RLS-enabled 133 **unchanged**; `anon` untouched (1 relation); behavioural probe → `permission denied for table issues`; idempotent `rc=0`×2 with `ON_ERROR_STOP=1`; structural delta = **exactly one default-ACL line**. Report `…059` |
| Two facts declared | **`MAINTAIN`** revoked (PG 17.6) because the register's target *"exactly SELECT,INSERT,UPDATE,DELETE"* is otherwise unreachable — PO may veto; **default-privilege REVOKE** included because a table-only revoke would be silently undone by the next `CREATE TABLE` |
| New findings | `F-4A2-1` **`psql -f` returns `rc=0` on SQL error unless `ON_ERROR_STOP=1`** (my first application failed silently; corrected) · `F-4A2-2` the **`anon` default-privilege gap is NOT fixed** (out of scope for item 6; needs separate authorisation) |
| Not authorised / not done | RLS steps 3–5 (`D-4`…`D-10`, `D-12`) · the `anon` default fix · production |
| **B2 closure (item 4)** | **NO NEW RECORD CREATED — none was needed.** `docs/cline/reports/CT-P8-B2-PO-CLOSURE-20260913-028.md` **already exists** (*"B2 CLOSED — PO ACCEPTED"*, with F-025-1/F-025-2 dispositions). `F-049-1` was a **broken reference** (the plan searched for `…026`). A §8 **re-confirmation** was appended to the existing record citing the 2026-09-14 decision. B2 not reopened |
| **QA environment (item 5)** | `carbontally_qa_phase8` confirmed as the PO-named Phase 8 QA environment. **`…029` is satisfied in substance** — QA already holds S3 + B1 + B2 + B3 (and now RLS-4A-2); there is nothing left to apply. **`F-049-3` resolved** (B1/B2 *are* present in a persistent environment). Production authorisation **not** conferred |
| **X1 (items 1–3)** | **FEASIBILITY COMPLETE — REUSE SUFFICIENT — NO MIGRATION GATE.** Authoritative 8-X §13 M1 states *"all data already exists in `document_processing_queue`; **no schema change required**"*; `dashboard_metrics` (with `expires_at`) provides heartbeat storage without a schema change; `/health`, `v3_operations.py`, `require_internal_staff()` already exist. Note `docs/architecture/CARBONTALLY_PHASE8X_X1_FEASIBILITY_20260914.md`. Implementation **not started** |
| Excluded/deferred | runtime/deployment introspection (item 1) · provider console + read-only production DB role (item 2) · S8/D16 |
| OHD | **out of scope** per the PO's scope correction; not analysed, not classified, no register created |
| Artefacts | `CT-P8-RLS-4A-2-HARDENING-20260914-059.md` · migration `20260922000000` · `CARBONTALLY_PHASE8X_X1_FEASIBILITY_20260914.md` · B2 closure §8 · B3 PO decision record §11 · final programme report §13 |
| Worktree | `main` · HEAD `37b19d1` · staged 0 · **tracked mods 229 (unchanged)** · **no commits** · **no code/test files changed** (one new migration + docs) |

### R4.18 **RLS-4A-2 + F-4A2-2 PO-CLOSED; X1 IMPLEMENTED + INDEPENDENTLY VERIFIED (2026-09-14)**

| Item | Result |
|---|---|
| PO decisions consumed | 2026-09-14 (second batch): item 1 RLS-4A-2/F-4A2-2 **PO CLOSED** · item 2 `anon` sequence-default = **future bounded decision, no action** · item 3 continue X1 within the authorised scope · item 5 OHD **out of scope** · item 6 stop after X1 IV, **do not self-close** |
| **RLS-4A-2** | **CLOSED — PO ACCEPTED.** Migration `20260922000000`; 119 → 0 non-DML privileges for `authenticated`; DML preserved; policies/RLS unchanged. Report `…059` §9 |
| **F-4A2-2** | **CLOSED — PO ACCEPTED.** Migration `20260923000000` (REVOKE-only default-privilege hardening for `anon`); new-table probes prove future tables inherit no `anon` Dxtm; `emission_factors` (D-4) untouched. Report `…060` §9 |
| Deferred by PO | `anon` **sequence-default `UPDATE`** — recorded as a future, separately bounded decision (`F-4A1B-1`); **not** modified |
| **X1 (bounded set)** | **IMPLEMENTED + INDEPENDENTLY VERIFIED — READY FOR PO CLOSURE** (not self-closed). Delivered: M1 queue/worker visibility read model + endpoint · M2 worker heartbeat (worker tick → existing `dashboard_metrics`, single current row) + endpoint · M2 `/health` **pool-path** correction. **No migration** (reuse proven). Report `…061` |
| X1 endpoints | `GET /api/v3/ops/operational-health/queue` · `GET /api/v3/ops/operational-health/worker` — **internal staff only**, read-only, aggregate-only |
| X1 evidence | domain unit **19/19** · X1 integration **5/5** (clone `ct_x1_20260914`) · Phase 8 integration regression **29/29** · ops-auth **18/18** · **F-046-1 negative control fires** when pointed at QA |
| `F-X1-1` | **defect found by the integration test and fixed in scope**: the heartbeat tick is read from JSONB as an ISO string; the classifier accepted only `datetime` → the endpoint would have raised on first real read. Fixed + regression-tested |
| **`F-X1-2`** | **pre-existing failure, NOT X1 — recorded for separate disposition.** `test_v3_phase_c_regressions.py` (2 FAILED): `MemoryFactors.find_by_activity() got an unexpected keyword argument 'unit_qualifier_tolerant'` at `api/v3_processing_workflow.py:1116` — **test-double drift left by the closed P2 EF-E batch**; X1 touches none of those files. Not fixed here (out of X1 scope) |
| Not done | X2/alerting · runtime/deployment introspection · provider/production access · S6 · OHD · RLS steps 3–5 |
| Worktree | `main` · HEAD `37b19d1` · staged 0 · **no commits** · F-046-1 enforced (clone-only destructive work) |

### R4.19 **X1 PO-CLOSED; F-X1-2 CARRIED TO EF-E; REMAINING REGISTER RECONCILED (2026-09-14)**

| Item | Result |
|---|---|
| PO decision consumed | *"Phase 8-X X1 — PO CLOSED / ACCEPTED"*; `F-X1-2` **not authorised under X1** → separate bounded item associated with the **EF-E** batch; boundaries preserved (X2 · runtime/deployment introspection · provider console · production · S6 · RLS 3–5 · OHD all still gated) |
| **X1** | **CLOSED — PO ACCEPTED** (`…061` §11). Delivered: queue visibility read model · heartbeat read/write on existing `dashboard_metrics` · two internal-staff endpoints · worker heartbeat tick · `/health` pool-path correction · integration + regression verification · IV |
| **`F-X1-2`** | Recorded as a **carried finding against the EF-E batch** (`CT-P8-P2-EFE-CLOSURE-20260914-054.md` §7): `MemoryFactors.find_by_activity()` missing `unit_qualifier_tolerant`; **not fixed**; bounded remediation = test-double signature update |
| New artefacts | `CT-P8-P8X-X1-IMPLEMENTATION-AND-IV-20260914-061.md` · `CARBONTALLY_PHASE8_S6_DECISION_PACKAGE_20260914.md` |
| **Phase 8 remaining** | **S6** (PO decision — package delivered) · **RLS steps 3–5** (`D-4`…`D-10`, `D-12`) · **I1** (`…041` ruling) · **`…048`** (external ESRS evidence) · **S8** (not authorised) · **D16/legacy** (`D-19`) · **P1 enablement / EF-A / EF-D** (external) · **`F-X1-2`** (separate, EF-E) · **G0-D / production** (not authorised) |
| **Phase 8-X remaining** | **X2** (`…045`) — the next Phase 8-X gate, needing **`PX-6`** (alert recipients/channels/thresholds) + **`PX-7`** (operational-data retention); X1 is now closed so its prerequisite is satisfied. X4–X7 after X2; **X8 undefined** |
| Nothing else executable | No new implementation was begun on X1 closure; no gate was inferred; OHD untouched |
| Worktree | `main` · HEAD `37b19d1` · staged 0 · **no commits** · no migration added by X1 |

### R4.20 **PX-6/PX-7 APPROVED; X2 CONTRACT PRODUCED — IMPLEMENTATION STOPPED AT THE `PX-6` VALUE GATE (2026-09-14)**

| Item | Result |
|---|---|
| PO decisions consumed | **`PX-6` Option (a)** internal-operations-only alerting (*"no invented thresholds; no invented recipient lists"*; contract required **before** implementation; **stop and return** any new business choice) · **`PX-7` Option (d)** 90-day operational telemetry detail + indefinite aggregates, server-side, without weakening report/evidence retention · X2 authorised **only after** the contract |
| Contract produced | `docs/architecture/CARBONTALLY_PHASE8X_X2_ALERTING_CONTRACT_20260914.md` — scope · reuse map · the seven `PX-6` elements · `PX-7` retention design · gates · verification expectations |
| **Reuse proven (no new infrastructure)** | `system_settings` alert/SLA columns · `notifications` (**`event_key`** = the prescribed dedup key) · `notification_delivery` (`channel`/`status`/`error_message`) · `consultant_lifecycle.py` as the existing dispatch pattern · canonical `audit_trail` · X1's `operational_health` signals. **No new messaging framework → the 8-X stop condition does not fire** |
| **DETERMINED (4)** | dedup **mechanism** (`event_key`) · delivery **transport** (reuse `notifications`/`notification_delivery`) · failure **recording** (`status`/`error_message`) · **audit** path (existing convention) |
| **OPEN — PO CHOICE REQUIRED (6)** | `X2-D1` which failure conditions (8-X S1 names backlog / SLA breach / repeated failures; provider outage is excluded by `PX-4`) · `X2-D2` **thresholds** · `X2-D3` **recipients** · `X2-D4` **cooldown window** · `X2-D5` **channel(s)** · `X2-D6` **retry policy** |
| Live evidence for the gate | **`system_settings` = 0 rows · `sla_definitions` = 0 rows · `notifications` = 0 · `notification_delivery` = 0** → no threshold, recipient or enablement value exists in any artefact, so none may be assumed |
| Data-safety flag | `X2-D7` — `document_processing_queue`/`processing_logs` are operational **work** records, **excluded** from `PX-7` telemetry retention (flagged for confirmation) |
| **Status** | **X2 NOT IMPLEMENTED — stopped at the `PX-6` gate** as the PO instructed. No threshold, recipient, channel, cooldown or retry policy was invented; no code, migration or schema change; no self-closure |
| Boundaries preserved | X2 sub-scope only · no customer/consultant alerting · no runtime/deployment introspection · no provider console · no production · S6 · X4–X7 · S8 · RLS 3–5 · `F-X1-2` · **OHD untouched/in scope-free** |
| Worktree | `main` · HEAD `37b19d1` · staged 0 · **no commits** |

### R4.21 **X2 IMPLEMENTATION COMPLETE — VERIFICATION PARTIALLY EXECUTED (2026-09-14)**

| Item | Result |
|---|---|
| PO decisions consumed | `PX-6` Option (a) + the seven X2 values (conditions, thresholds, recipients, cooldown, channels, retry, failure recording) · `PX-7` Option (a)/(d) with `operational_telemetry_retention_days` initial 90, configurable, server-side |
| Implemented | `domain/operational_alerts.py` · `services/operational_alerting.py` · `data/notifications.py` (+`internal_ops_user_ids`/`email_for_user`/`record_delivery`/`prune_operational_alerts_before`) · `data/document_processing.py` (+`count_sla_breached`/`prune_operational_metrics_before`) · `data/queue_settings.py` (+`is_configured`) · `data/settings.py` (telemetry retention column in read/write) · `services/retention.py` (telemetry domain + 8-table never-purge list) · `workers/automatic_processing.py` (per-tick evaluation + background dispatch) · migration `20260924000000` |
| Verified PASS (V1–V12) | approved values · backlog **>100** only · worker stale **>15 min** only (never-ticked → alert, never healthy) · retry-exhausted · **SLA unconfigured ⇒ no alert** · migration additive+idempotent (clone ×2 `rc=0`, 0 errors) · **applied to QA** ×2 `rc=0`, 0 errors, other domains untouched · **configurable without code change** (90→120→90 via the repo) · repository read path live · AST+imports · regression 41 tests |
| Outstanding (O1–O8) | end-to-end dispatch · **hourly DB dedup** · **recipient limitation** (no consultant/customer/PE) · **email 3-attempt failure recording** · **audit entry** · **retention enforcement** (detail pruned, aggregates untouched, excluded tables provably unchanged, dry-run default) · worker wiring · F-046-1 negative control |
| Findings (all self-found, fixed in scope) | `F-X2-1` dispatch was awaited → would stall the claim loop (**now a background task**) · `F-X2-2` wrong email kwargs + ignored `delivered=False` (**now raises → recorded failure**) · `F-X2-3` first migration attempt rolled back on `setting_key` NOT NULL + harness masked the rc (restates `F-4A2-1`) |
| Scope hygiene | `F-X1-2`, `F-4A1B-1`, S6, S8, RLS 3–5, I1, D16, P1/P2 externals, X4–X8, production, provider monitoring, Phase 9 and **OHD** all untouched |
| Report | `docs/cline/reports/CT-P8-P8X-X2-IMPLEMENTATION-AND-IV-20260914-062.md` |
| Status | **IMPLEMENTATION + IV COMPLETE — READY FOR PO CLOSURE (not self-closed)**: O1–O8 **all PASS** — end-to-end dispatch · hourly DB dedup (1 same hour / 2 next hour) · recipients limited to internal `can_view_all` (no-perm internal + PE staffer received 0) · email 3 attempts → `failed` + error recorded · audit row per dispatch · retention (configured value, dry-run default, ops-alert + metric pruned, product notification + fresh telemetry retained, queue/logs untouched, restored to 90) · worker wiring (heartbeat + background dispatch; failing dispatch contained) · F-046-1 negative control fires. Regression: X2 4/4 · X1 19/19 · ops-auth 18/18 · X2 integration 3/3 · worker 2/2 |
| Defects found BY the verification (all fixed in scope) | **`F-X2-4`** audit write used kwargs instead of `AuditEntry` → `TypeError` **swallowed** ⇒ no audit entry (now builds a real `AuditEntry`; failure surfaces in the report) · **`F-X2-5`** missing `dumps_jsonb` import in `data/notifications.py` · **`F-X2-6`** `AmbiguousParameterError` on `$3` in `record_delivery` (explicit casts) · test-harness defects (audit column names, `processing_entities` FK, FK-safe cleanup) |
| Worktree | `main` · HEAD `37b19d1` · **no commits** · QA received only the authorised migration; production/demo untouched |

### R4.22 **X2 PO CLOSED / ACCEPTED — REGISTER RECONCILED (2026-09-14)**

| Item | Result |
|---|---|
| PO decision consumed | **X2 — PO CLOSED / ACCEPTED**: accepted V1–V12, O1–O8, `F-X2-4`/`F-X2-5`/`F-X2-6` as fixed in-scope defects, the internal-only alerting model, thresholds + hourly dedup, 3-attempt email failure handling, auditability, configurable server-side telemetry retention, the 90-day initial value, and the exclusion of processing records/logs |
| Recorded | `…062` **§12** (transcription only — no self-closure, nothing inferred) |
| Phase 8-X state | **X1 CLOSED · X2 CLOSED**. Remaining: **stage X4** (aggregation layer: failures/SLA/usage/imports/delivery/AI) · **X5** (ops console extension) · **X7** (API runtime metrics, S2) · **X8** (verification stage — blocked until X4–X7 exist) · **M5/G-23** runtime/deployment introspection (PO-excluded, `PX-4` declined) |
| Phase 8 state | All closed except: **S6** (6 decisions pending) · **RLS steps 3–5** (`D-4`…`D-10`, `D-12`) · **`F-4A1B-1`** (future bounded decision) · **`B4-D12`** (commercial) · **N3** remaining domains · **S8** (not authorised) · **D16** (`D-19`) · **`F-X1-2`** + **`F-B3-7`** (separate bounded remediations) · **I1** (ruling) · external: `…048`, P1 enablement, EF-A/EF-D · **G0-D/production** |
| Reconciliation artefact | `docs/cline/reports/CT-P8-FINAL-PROGRAMME-REPORT-20260914-057.md` **§14** — every item classified 1–7 with plain-English meaning, prerequisite status, authorisation status and consequence |
| **Next PO gate** | **S6** (decision package already delivered — S6-1…S6-6), then **Phase 8-X X4** (authorisation + scope); **RLS steps 3–5** in parallel |
| Implementation | **none performed** by this reconciliation; no self-closure; production/demo untouched; OHD untouched |
| Worktree | `main` · HEAD `37b19d1` · staged 0 · **no commits** |

### R4.23 **S6 (visibility-first) IMPLEMENTED + SELF-VERIFIED — AWAITING PO CLOSURE (2026-09-14)**

| Item | Result |
|---|---|
| PO decision consumed | **S6 APPROVED: VISIBILITY-FIRST FIRST RELEASE** (Option (b)); comments explicitly deferred with four recorded principles |
| Reconciliation | The lifecycle already existed end-to-end; the real gap was that `ReportDetailPage` showed versions **without state or actions**. S6 = UI + **one additive read field** (`allowed_actions` on the versions list) so the UI never derives rules in the browser |
| Files | `backend/api/v3_reports.py` (additive) · `frontend/src/v3/api.js` (5 POST wrappers) · **new** `ReportLifecyclePanel.jsx` · `ReportDetailPage.jsx` (wired) · `reports.css` · **new** frontend test · `+6` backend tests |
| Not changed | state machine · persistence · transition endpoints · immutability service · retention/evidence/calculation/factor matching · **RLS** · **no migrations** |
| Tests | backend lifecycle **37 passed** · backend API area: only the 2 known PO-excluded `F-X1-2` failures, **no new** · frontend report panels **11 passed** · frontend v3 suite **21 suites / 203 tests passed** |
| IV | state visibility PASS · history PASS · permitted actions PASS · denial 401/403 PASS · tenant isolation PASS · FINAL immutability PASS · persisted-state fidelity PASS (design-verified) · no comments PASS · no regression PASS. Limitations: automated-test-level UI IV (no live browser session); no real-PostgreSQL integration run this pass — `F-046-1` honoured |
| Recorded separately (not fixed) | `F-X1-2` (unchanged) · unit-suite stall at ~9% (environment observation) · **`S6-ACTION-1`** — the pre-existing `new_version` supersession action is **not** offered in this release; **PO decision required**, nothing invented |
| Report | `docs/cline/reports/CT-P8-S6-IMPLEMENTATION-AND-IV-20260914-063.md` |
| Status | **AWAITING PO CLOSURE** — not self-closed. X4 and all other items **not begun** |
| Worktree | `main` · HEAD `37b19d1` · staged 0 · **no commits** |

### R4.24 **S6 PO CLOSED / ACCEPTED — REGISTER RECONCILED (2026-09-14)**

| Item | Result |
|---|---|
| PO decision consumed | **S6 — PO CLOSED / ACCEPTED**: state visibility · history · server-authoritative `allowed_actions` · existing review/approval/finalisation actions · authorization + tenant isolation · FINAL immutability · friendly 403/409 · no comments · regression results · limitations accepted as limitations (no live-browser / real-PostgreSQL claim permitted) |
| `S6-ACTION-1` ruling | **`new_version` NOT implemented** in this release; recorded as a **future, separately bounded S6 increment** requiring its own PO decision. Its absence is **not** an S6 defect. Backend capability left as-is |
| Recorded | `…063` **§12** (transcription only — no self-closure) |
| Phase 8 state after closure | **The buildable Phase 8 queue is now empty.** Product scope closed: B1–B4 · S1–S7 · **S6** · P1 package · P2 census + EF-E · G0 register. Remaining items are **not** Phase 8 build work: RLS steps 3–5 (**separate workstream, gate HELD** — needs explicit PO authorisation to reopen, *not* authorised by Phase 8 or 8-X completion) · S8 / D16 (`D-19`) / I1 (**not authorised**) · `F-4A1B-1` · `B4-D12` · N3 remaining domains (**optional / decision**) · `F-X1-2`, `F-B3-7` (**test hygiene, separately bounded**) · `…048`, P1 enablement, EF-A/EF-D (**external evidence**) · G0-D/production (**deployment, unauthorised**) |
| Phase 8-X state | X1 · X2 (**delivered + PO-closed**). **Unbuilt: X4** (aggregation layer), **X5** (console extension), **X7** (API runtime metrics), **X8** (verification stage — blocked until X4–X7 exist). M5/G-23 runtime introspection **PO-excluded** (`PX-4` declined) |
| Next PO gate | **Phase 8 completion declaration + Phase 8-X X4 authorisation/scope** (see §14.4 of `…057`) |
| Implementation | **none performed** by this reconciliation; X4 and every other item **not begun**; OHD untouched; production/demo untouched |
| Worktree | `main` · HEAD `37b19d1` · staged 0 · **no commits** |

### R4.25 **PHASE 8 PO DECLARED COMPLETE · X4 CONTRACT PREPARED — NOT AUTHORISED (2026-09-14)**

| Item | Result |
|---|---|
| PO decision consumed | **Phase 8 PO DECLARED COMPLETE** (Option (a)). Product/build scope complete; **production is NOT approved** and no held/deferred work is accepted as complete |
| Named deferrals | RLS steps 3–5 (**separate workstream, gate HELD**) · **G0-D/production NOT AUTHORISED** (blocked by the held RLS gate) · S8 · D16/legacy · I1 · `F-X1-2` · `F-B3-7` · `F-4A1B-1` · B4-D12 · N3 remaining retention domains · external ESRS/P1/P2 evidence · S6 `new_version` |
| Recorded | `…057` **§15** (declaration + named deferrals) |
| X4 status | **CONTRACT PREPARED — implementation NOT authorised.** `docs/architecture/CARBONTALLY_PHASE8X_X4_AGGREGATION_CONTRACT_20260914.md` covers metrics, sources, aggregation, windows, failure/SLA semantics, scope/permissions, freshness, API shape, schema (**none required**), retention (**unchanged**), verification plan, exclusions |
| X4 proposed first release | failures + SLA **only**: M1 failed → M10 worker-liveness, built **read-time** from existing tables (`document_processing_queue`, `processing_queue`, `dashboard_metrics`, `queue_settings`) reusing X1/X2 predicates. Usage/imports/delivery/AI **excluded** (not authorised) |
| New PO decisions raised | **`X4-D1`** time windows · **`X4-D2`** `truncated` honesty flag · **`X4-D3`** failure-rate (recommend none) · **`X4-D4`** SLA flag-only vs deadline-derived · **`X4-D5`** endpoint shape |
| Implementation | **none** — no code, no migration, no schema, no RLS change; X4, X5, X7, X8 **not begun**; OHD untouched; production/demo untouched |
| Worktree | `main` · HEAD `37b19d1` · staged 0 · **no commits** |

### R4.26 **X4 (failures + SLA aggregation) IMPLEMENTED + SELF-VERIFIED — AWAITING PO CLOSURE (2026-09-14)**

| Item | Result |
|---|---|
| PO decision consumed | **X4 CONTRACT APPROVED — IMPLEMENTATION AUTHORIZED** with rulings **X4-D1** window-less · **X4-D2** explicit `truncated` · **X4-D3** no failure-rate · **X4-D4** flag-only SLA · **X4-D5** ONE read-only endpoint |
| Files | **new** `backend/services/operational_intelligence.py` · `backend/api/v3_operations.py` (one `GET /api/v3/ops/operational-intelligence` + one import) · **new** three test files (unit, API, integration) |
| Behaviour | 13 approved metrics composed from existing X1/X2 predicates and existing columns/settings. Not-configured SLA → `sla_breached_items: null` and the breach count is **never read**; worker never ticked → `UNKNOWN`; read at the 2,000-row bound → `truncated: true`. Internal-only authority (`require_staff` → `require_internal_staff` → `can_view_all`) |
| Tests | X4 unit/service **26 passed** · X4 endpoint **10 passed** · X4 runtime on disposable clone **6 passed** · X1/X2 unit regression **passed** · X1/X2 runtime regression **8 passed** · broader API regression: pre-existing `F-X1-2` only |
| IV | direct **SQL cross-checks** per metric PASS · configured + not-configured SLA PASS · worker UNKNOWN PASS · truncation PASS · **redaction** (e-mail in `last_error`) PASS · ALLOW (internal staff) + DENY (no `can_view_all`, PE staff, customer, unauthenticated) PASS · X4/X1 consistency PASS · read-only proof PASS |
| Schema / impact | **No migration, no schema, no RLS, no permission model, no frontend change.** Disposable clone `ct_x4_20260914` created (template read-only from QA); QA/demo/production untouched; no production verification claimed |
| New findings | **`F-X4-1`** (info, test-infra): dedicated `carbontally_test` has a **stale schema** (missing V3 queue columns) — not fixed, out of scope · **`F-X4-2`** (test-side bug, fixed in-task) · **`F-X4-3`**: **no stop-condition triggered** |
| Report | `docs/cline/reports/CT-P8-P8X-X4-IMPLEMENTATION-AND-IV-20260914-064.md` |
| Status | **READY FOR PO REVIEW/CLOSURE — not PO-closed.** X5/X7/X8 and all excluded work untouched; OHD untouched |
| Worktree | `main` · HEAD `37b19d1` · staged 0 · **no commits** |

### R4.27 **X4 PO-CLOSED — COMMIT NOT CREATED (BLOCKED BY A MIXED-FILE DELTA) (2026-09-14)**

| Item | Result |
|---|---|
| PO closure consumed | **X4 — IMPLEMENTED, INDEPENDENTLY VERIFIED, PO-CLOSED**; PASS accepted for the approved scope. Limitations recorded (`F-X4-1` separate remediation, `F-X1-2` separately excluded, no production verification/authorisation, excluded work not accepted) |
| Recorded | `…064` **§8** (transcription) |
| Commit authorisation | **Granted** for one X4-only commit over the 6 authorised paths |
| **BLOCKER** | `backend/api/v3_operations.py` is tracked+modified with a **125-insertion / 2-deletion uncommitted delta that also contains non-X4 work**: X1's two `operational-health` endpoints (previous session), B2 line-item provenance (`evidence_line_items`, `source_line_item_id`) and two `"manual"` call-site changes — plus X4's one import and one route. The PO's stated "must" (**staged diff contains only the X4 changes; do not include unrelated tracked modifications**) **failed verification** |
| Action taken | **No commit created.** Reported as a PO decision gate with options (partial-stage only the X4 hunks · commit the file as-is (unauthorised) · commit the earlier work first) rather than guessing |
| The other 5 authorised paths | All **untracked** → X4-only by construction |
| Worktree | `main` · HEAD `37b19d1` · staged 0 · **no commits** · **no push** |
| Boundaries | X5/X7/X8 not begun; no deferred/held item touched; production/demo untouched; OHD untouched |

### R4.28 **X5 (operations console extension) IMPLEMENTED + SELF-VERIFIED — AWAITING PO CLOSURE (2026-09-15)**

| Item | Result |
|---|---|
| PO decision consumed | **Master authorisation — complete remaining Phase 8-X** (X5 → X7 → X8 → Phase 8-X closure), gated per stage |
| Contract | `CARBONTALLY_PHASE8X_X5_OPS_CONSOLE_CONTRACT_20260915.md` — all 11 reconciliation questions answered from existing approved decisions; **no X5 stop condition triggered** |
| Files | **new** `frontend/src/v3/ops/OperationalHealthTab.jsx` · `OperationsPage.jsx` (tab registration) · `App.js` (route alias for X2's alert link) · `api.js` (3 read-only wrappers) · `ops.css` · **new** test file. **No backend change** |
| Behaviour | Read-only operator panel over the PO-closed X1/X4 endpoints: failures, error counts by stage, SLA state/value/breaches, worker liveness, queue depth, `truncated` notice, `evaluated_at`. **Only control = Refresh**; no filter/sort/drill-down/action; honesty states surfaced (partial population, SLA not configured, worker UNKNOWN/STALE) |
| Tests | X5 tab suite **11 passed** · console gating regression **passed** · **full frontend v3 suite 22 suites / 214 tests passed** (pre-X5 21/203) |
| Findings | **`F-X5-1`** resolved: X2's alert deep-link `/ops/operational-health` had **no route** — the alias now makes it resolve (X2 code untouched) · `F-X5-2` info: X1/X4 had no UI caller before this stage · `F-X5-3`: **no stop condition triggered** |
| Impact | No migration/schema/RLS/permission/retention change; **no database touched**; demo/production untouched; no production verification claimed |
| Commit | **Not committed.** Proposed boundary in the report; ⚠️ `App.js`/`api.js`/`ops.css` carry pre-existing **S6** changes → same point-staging decision needed as the X4 commit |
| Carried dependency | **X4 commit still uncreated** (mixed-file point-staging decision pending) |
| Status | **READY FOR PO REVIEW/CLOSURE — not PO-closed.** X7 awaits this gate; **X8 requires X5 *and* X7 to be PO-closed** before it may start |
| Worktree | `main` · HEAD `37b19d1` · staged 0 · **no commits** · **no push** |

### R4.29 **`CT-P8X-X5-GATE-01` EXECUTED — X5 PO-CLOSED · X4+X5 COMMITTED · X7 BLOCKED (PO DECISION) (2026-09-15)**

| Item | Result |
|---|---|
| X5 closure | **X5 — IMPLEMENTED, INDEPENDENTLY VERIFIED, PO-CLOSED** recorded in `…065` §10 (limitations listed: no live-browser, no a11y tool, no production verification, no backend runtime change, no production authorisation implied) |
| X4 commit | **`a71a46a`** — 6 files, 1539 insertions, 0 deletions; `v3_operations.py` **+41 only** via blob-level partial staging; staged blob contains **no** `operational-health`, `evidence_line_items` or `"manual"` content (X1/B2 excluded) |
| X5 commit | **`137765f`** — 8 files, 765 insertions, 0 deletions; mixed files (+9/+13/+72/+10) staged blob-level; staged blobs contain **no** S6 content (`submitReportVersion`, `REPORT_LIFECYCLE_ACTION_CALLS`, `v3-lifecycle`, `ReportLifecyclePanel` all 0) |
| X7 contract | `CARBONTALLY_PHASE8X_X7_API_RUNTIME_METRICS_CONTRACT_20260915.md` — 13 determinations made; instrumentation reality verified (**CORS middleware only; no timing code anywhere; metric store used only by X1 heartbeat**); **schema change: none needed under either option** |
| **X7 gate** | **X7 BLOCKED — PO DECISION REQUIRED**: metric semantics undecided (ephemeral per-worker vs persisted in the existing store), flush interval, latency window/statistic, and the "slow endpoint" threshold — the PO's X2 precedent forbids inventing thresholds. **No X7 code written** |
| Report | `docs/cline/reports/CT-P8-P8X-X5-GATE-01-REPORT.md` (sections A–G) |
| Worktree | `HEAD` **`137765f`** · staged **0** · tracked mods **242** (all pre-existing, preserved) · **no push** |
| Boundaries | X1/X2/X4 semantics untouched · S6 untouched · no RLS/schema/permission/retention change · production/demo untouched · **OHD untouched** · X8/Phase 9 **not begun** |

## R5. Current invariants

No commits · no production changes or storage writes · no historical backfill/re-extraction · unrelated worktree modifications preserved · no secrets introduced · existing security/regression tests only ever **strengthened** (never deleted or weakened).
