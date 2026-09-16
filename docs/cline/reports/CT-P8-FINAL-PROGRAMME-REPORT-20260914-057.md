# CT-P8 — FINAL PROGRAMME REPORT (Phase 8 / Phase 8-X)

**Programme:** CarbonTally Phase 8 / Phase 8-X
**Governing authorisation:** `CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260913-050` (blanket, hands-off sequential execution) plus every PO ruling issued since
**Date:** 2026-09-14
**Report id:** `CT-P8-FINAL-PROGRAMME-REPORT-20260914-057`
**Supersedes:** the "next eligible work" sections of `…049` §R4 (retained as history)
**Production:** **NOT AUTHORIZED, NOT TOUCHED** (see §8)
**Phase 9:** **NOT AUTHORIZED, NOT PERFORMED** — Phase 8-X remains inside Phase 8 (see §8)

---

## 1. Verdict

> **The programme is complete as far as the blanket authorisation permits.**
> All executable, non-gated Phase 8 / Phase 8-X work is implemented, independently
> verified and closed. **Zero** items remain in the *implemented / verification
> pending* state. Every remaining item is blocked on exactly one of: an
> unresolved **PO/product/security decision** (§6), an **external** input (§5), or
> a scope boundary the PO has already ruled on (§7).

This is **not** a claim of *programme acceptance*: Phase 8 contains **no** open
implementation item, but a PO decision backlog (§6) remains, and acceptance is a
PO act.

---

## 2. What this final pass executed

| Item | Determination | Action |
|---|---|---|
| `…030` **S1/S3 independent verification** | gate was **authorisation only** (*"no PO decision prerequisite"*) → the blanket `…050` satisfies it (directive §2/§3: an old authorisation artefact is not a governance gate) | **EXECUTED** — 15 independent probes + 3 migration probes, all PASS; report `…056`; **F-049-6 DISCHARGED** |

Everything else was re-tested against the *current* decisions rather than the old
gate table, and classified. Two near-misses were explicitly **declined** because
they are genuine governance gates, not missing paperwork:

| Near-miss | Why NOT executed |
|---|---|
| **`RLS-4A-2`** authenticated grant hardening | register: *"Each group is a **separately authorized** change with its own verification gate. **No batched release.**"* and status **NOT AUTHORIZED — NOT IMPLEMENTED**. Approving a security-control change by inference would be inventing a security decision. **Decision recorded in §6 (D-PO-1).** |
| **`…028`** B2 closure record | `…049` §3.3 is explicit: *"Under **no** reading may the agent write the closure record on its own initiative"* and the referenced artefact is unverified. **Decision required (§6, D-PO-2).** |

Also confirmed **already complete** (not redone): `…040` P8-X/Phase 9 reconciliation
(report exists; its **no-Phase-9 ruling** is what renders X1's `D-07` satisfied).

---

## 3. COMPLETE — implemented + independently verified + closed

| Item | Evidence | Status |
|---|---|---|
| **B1** disclosure model foundation | V1 FAIL → correction → **V1R PASS** (6 non-blocking) | closed (`-010` lineage) |
| **B2** evidence / line-item addressability | **IV PASS** (`-025`) | *see §6 D-PO-2 — repository closure record missing* |
| **B3** disclosure integration | migrations + projection service/API; **fresh-clone V3 175/175 PASS**, 7 migrations `rc=0`×2, zero removed diff lines | **closed `…051`** |
| **B4** narrative + finalisation + frozen artefact | unit + integration `EXIT=0`; B4 runtime **19/19**; mandate/gate/audit/immutability proofs; **gate V4 closed `…052`**; A1 residual **discharged `…055`** (fresh-clone replay: 44 added / 0 removed / 0 unattributable) | **closed** |
| **S1** report correctness (`is_current`) | **IV PASS** — IV-S1-1…5 (transactional demotion, DB-layer invariant, §7.3 legacy resolution, gaps, per-report scope) | **`…056`** |
| **S2** lifecycle schema + report-table RLS | PO **Option A** (app-layer-only); `is_current` single-valued partial unique index; suite `…046` | **closed `…046`** |
| **S3** report lifecycle states | **IV PASS** — IV-S3-5…7 + IV-S3-A1…A7; migration proven **additive** (3 objects of 3,423 fingerprinted), **idempotent** (`rc=0`×2), **no RLS change** (flags + 197 policies + ACLs byte-identical) | **`…056`** |
| **S4** narrative overlay | absorbed into B4 (`B4-D10`) | **closed via `…052`** |
| **S5** frozen final PDF artefact | absorbed into B4 (`B4-D10`); mandatory artefact, private bucket, derived key, SHA-256, append-only | **closed via `…052`** |
| **S7** regression + negative security tests | delivered **inside B4 and inside gate V4** (`B4-D10`) | **closed via `…052`** |
| **P1** authorisation decision package | `…037` package + PO decision record | **package closed**; enablement gated (§5) |
| **P2** factor-catalogue census | read-only census `…038` | **closed** |
| **P2 EF-E** remediation | PO **D-A(b) = S1+S2+S3 · D-B T2 · D-C(a)**; implemented + verified + closed; zero migration/schema change; no factor-data modification; clone-only destructive testing | **closed `…054`** |
| **RLS-4A-1** anonymous-grant containment | `anon` grants 458 → 4 (all on `D-4` `emission_factors`); verified independently on clone and re-verified on QA | **closed `…042`/D-1** |
| **G0** gate reconciliation register | 5 closed / 4 open, fully evidenced | **closed `…042`** |
| **`…040`** Phase 8-X / Phase 9 reconciliation | PO ruling recorded: **no Phase 9**; Phase 8-X inside Phase 8 | **executed** |
| **`…037`/`…038`/`…039`/`…042`** | packages/registers delivered | **executed** |
| **F-046-1** test-harness target safety | **enforced in code** (`conftest.py` refuses `qa`/`demo`/`investor`/`prod`/`live`) + AGENTS.md §55.1 | **programme invariant** |
| **`F-049-6`** S1/S3 verification gap | 15 IV probes + 3 migration probes PASS | **DISCHARGED `…056`** |
| **`F-049-4`** Phase 8-X / Phase 9 scope conflict | resolved by the `…040` ruling (no Phase 9) | **resolved** |

---

## 4. IMPLEMENTED / VERIFICATION PENDING

**None.** Every implemented Phase 8 item now carries independent verification:

* B1 V1R PASS · B2 IV PASS · B3 V3 PASS (fresh clone) · B4 V4 PASS (+ A1 replay) ·
  S1 **IV PASS `…056`** · S3 **IV PASS `…056`** · S4/S5/S7 verified inside gate V4 ·
  P2 EF-E verified + closed · RLS-4A-1 verified on clone and re-verified on QA ·
  S2 verified in-suite and in the fresh-clone replay.

No item is reported as *"tests pass"* in place of a verified business outcome, and
no skipped test has been counted as a PASS anywhere in this programme.

---

## 5. EXTERNAL DEPENDENCY

| Item | External input required | Why the agent must not cross it |
|---|---|---|
| **`…048`** G0-A E1 evidence closure | **Authoritative ESRS sources** | Identifiers and clause text must come from the primary standard; manufacturing them would fabricate regulatory evidence. |
| **P1** customer-visible enablement | **Real, non-production customer documents** | Shadow evidence must be real documents; manufacturing them "as if real" is prohibited, and obtaining them from production is not authorised. |
| **`…029`** B1/B2 environment application | The PO-named target environment | See D-PO-8; also an outward operational mutation. |
| **EF-A / EF-D** magnitude | The **real factor catalogue** | Only reachable through the production boundary; **production is not authorised**. |
| **Phase 8-X X1/X2 deployment verification** | Provider/platform access (`PX-4` BL-1/BL-2) | Provider credentials/access are outside this environment; no provider access exists. |

Nothing above was "approximated", stubbed or faked to look complete.

---

## 6. TRUE PO / PRODUCT / SECURITY DECISIONS REQUIRED

These are the **only** things standing between the programme and full closure.
Each is a decision (or an explicit statement) that must come from the Product
Owner; none was inferred, defaulted or invented.

| # | Item | Exact decision required |
|---|---|---|
| **D-PO-1** | **RLS-4A-2** authenticated grant hardening | *"Authorise RLS-4A-2: `REVOKE TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public FROM authenticated` (QA/non-production only, `REVOKE`-only, with its own verification gate)."* Evidence: `IV-OBS-2` — `authenticated` still holds blanket grants (inert under deny-all RLS). Register requires **separate authorisation per group**. |
| **D-PO-2** | **`…028`** B2 closure record (`F-049-1`) | An **explicit closure statement** re-stated on the record (the referenced `…026` artefact is unverified), **plus** authorisation of `…028`. `ACCEPTED` is a PO act, not an agent act. |
| **D-PO-3** | **RLS steps 3–5** (RLS-5/3/2/1: policy correctness, reference/operational/critical-table remediation) | Rulings on `D-4`…`D-10` and `D-12`. The PO explicitly withheld these and asked to be returned to when reached — **that point has been reached**. |
| **D-PO-4** | **S6** backlog item (frontend lifecycle UI + comment scope + `A7` visibility) | (a) **allocation** of S6 into a batch (`D-14`/`B4-PO-2`); (b) the **comments** decision (`B4-D4`/`B4-D9` kept comments out of B4, `report_comments` stays dormant — production vs retirement vs deferral is undecided); (c) **`A7` visibility** semantics. |
| **D-PO-5** | **`…041` Insight I1** | Resolve the **contradiction** between commit `d91ace5`'s subject (*"authorize I1"*) and the ratified D2 document (*"READY FOR I1 IMPLEMENTATION AUTHORISATION"*). Until ruled, **I1 is not authorised** and `I2…I8` stay closed. |
| **D-PO-6** | **Phase 8-X X1 (`…043`)** | `D-07` is now **satisfied** (`…040`: no Phase 9 ⇒ Phase 8-X owns operational intelligence). Still required: **`PX-2`** (monitoring MUST-set/thresholds), **`PX-4`** (platform access BL-1/BL-2), **`PX-5`** (heartbeat schema). |
| **D-PO-7** | **Phase 8-X X2 (`…045`)** | **`PX-6`** (alerting recipients) and **`PX-7`** (retention) — plus X1 closure. |
| **D-PO-8** | **`…029`** B1/B2 environment application (`D-02`) | **Name** the non-production persistent target (not the investor demo, not production). Still true today: **no persistent environment holds B1/B2**, so their runtime suites SKIP there — *a skip is not a PASS*. |
| **D-PO-9** | **S8** AI-assisted narrative | Separate authorisation; the AI preconditions are **not met**. |
| **D-PO-10** | **`B4-D12`** commercial/entitlement gating of finalisation · **D16** legacy disposition (`D-19`) · **N3** retention configuration | Commercial gating decision; the D16 legacy authorisation; and the N3 control-plane work (retention must **not** invent durations — `B4-D8` ratified "retain indefinitely, no deletion path"). |
| **D-PO-11** | **EF-A / EF-D** factor-catalogue magnitude | Requires the **real** factor catalogue (production boundary) before any magnitude judgement can be made. |

**No Phase 9 decision is requested** — the PO has already ruled it out.


---

## 7. OUT OF SCOPE (ruled, not pending)

| Item | Ruling |
|---|---|
| **Phase 9 — any work** | PO ruling via `…040`: **no Phase 9**. The Phase 9 *baseline commit* (`b471286`) remains an unratified artefact; no Phase 9 code state was touched. |
| **GA4 admin configuration** (`37b19d1`) | Out of Phase 8 scope — unrelated side work. |
| **Insight `I2…I8`** | Blocked behind the I1 ruling; not authorised on their own. |
| **Production migration/schema/data/deployment** | **Not authorised** (G0-D open; 34 pre-existing + 2 B2 outstanding migrations). |

---

## 8. Boundary confirmations

| Boundary | Confirmation |
|---|---|
| **Production** | **Untouched.** No production migration, schema change, data modification, backfill or deployment. No production credentials used; production was never connected to. |
| **Investor demo** | **Untouched.** No reset, truncate, reseed or global credential change. |
| **Persistent QA (`carbontally_qa_phase8`)** | Used **read-only** in this pass (`SELECT` only); 133 public tables intact; `anon` containment unchanged (1 relation — `emission_factors`). |
| **Destructive testing** | Confined to **disposable clones**: `ct_s13_iv_20260914` (this pass), `ct_b4v4_20260914`, `ct_int_20260914`, `ct_b3_v3_20260913`, `ct_b2_iv_20260913`. |
| **F-046-1** | **Enforced in code** (`backend/tests/integration/conftest.py` refuses `qa`/`demo`/`investor`/`prod`/`live` names and the forbidden main DBs before any `TRUNCATE`) and **documented** (AGENTS.md §55.1). `SELECT current_database()` was verified before every destructive run. |
| **Phase 9** | **No Phase 9 work performed.** Phase 8-X remains inside Phase 8. |
| **Secrets** | None introduced, printed or committed (no keys, tokens, JWTs or signed URLs in any artefact). |
| **Verified artefacts** | Not modified by the verification: `backend/data/report_versions.py`, `backend/api/v3_reports.py`, `backend/domain/report_lifecycle.py` and migration `20260913000000` are unchanged. |

---

## 9. Final repository state

| Item | Value |
|---|---|
| **HEAD** | `37b19d13723b0b1eabceeade86ce1615a98ab400` (unchanged across this phase) |
| **Commits made** | **none** (all work remains in the working tree, per programme convention) |
| **Staged** | 0 |
| **Tracked modifications** | 229 files |
| **Databases created this pass** | `ct_s13_iv_20260914` (disposable; safe to drop) |
| Unrelated working-tree changes | preserved, untouched |

### 9.1 Closure artefacts (this pass)

* `docs/cline/reports/CT-P8-S1S3-INDEPENDENT-VERIFICATION-20260914-056.md` — S1/S3 IV report (F-049-6 discharged)
* `docs/cline/reports/CT-P8-FINAL-PROGRAMME-REPORT-20260914-057.md` — this report
* `docs/cline/reports/CT-P8-MASTER-SEQUENTIAL-EXECUTION-20260913-049.md` — **§R4.14** added; S1/S3 rows, `…030` row and `F-049-6` reconciled
* `backend/tests/integration/test_s1s3_iv_invariants.py` — 8 durable IV probes
* `backend/tests/unit/api/test_s1s3_iv_supersession.py` — 7 durable IV probes

### 9.2 Test totals for this pass

| Group | Result |
|---|---|
| S1/S3 implementation integration (`test_report_versions.py`, `test_report_lifecycle.py`) | 12 passed |
| S1/S3 implementation unit (`test_v3_reports.py`, `test_v3_report_lifecycle.py`) | 78 passed |
| **New IV integration** (`test_s1s3_iv_invariants.py`) | **8 passed** |
| **New IV unit** (`test_s1s3_iv_supersession.py`) | **7 passed** |
| Post-probe re-run (integration / unit) | 20 / 85 passed |

No test was deleted, skipped, weakened or counted as a PASS without executing.


---

## 10. Handoff — exact remaining inputs

**The single next action required is a PO response to the decision backlog in §6.**
Nothing else is required for the programme to advance: no prerequisite task, no
environment, no verification authorisation, no external procurement (other than
§5's items).

Recommended minimum batch to unblock the largest amount of work in one step:

1. **D-PO-1** (RLS-4A-2) — one line, unblocks the first of the RLS remediation steps.
2. **D-PO-3** (`D-4`…`D-10`, `D-12`) — unblocks RLS steps 3–5, the largest remaining security workstream.
3. **D-PO-6/D-PO-7** (`PX-2`/`PX-4`/`PX-5`, then `PX-6`/`PX-7`) — unblocks the entire Phase 8-X X1→X2 chain.
4. **D-PO-5** (I1) — unblocks I1 and, conditionally, `I2…I8`.
5. **D-PO-2** (`…028`) — closes `F-049-1` and B2 on the record.
6. **D-PO-4** (S6 allocation + comments + `A7`) — unblocks the last S-series UI batch.

Items that additionally need **external** input (§5) cannot be advanced by any
authorisation: `…048` (ESRS evidence), P1 enablement (real non-production
documents), EF-A/EF-D magnitude (real catalogue), and X1/X2 deployment
verification (provider access).

---

## 11. Statement of limitations

* This report asserts **programme-execution completeness against the authorisation
  in force**, not product acceptance. Several §6 decisions could change scope.
* Verification was performed at **repository / API / database** level. No browser
  or end-to-end UI pass was run in this phase (`S6` UI does not exist yet).
* B1/B2 have **never** been applied to any persistent environment, so their
  runtime properties there remain **unverified** (a SKIP is not a PASS) — D-PO-8.
* The disposable clones used for destructive verification are test
  infrastructure; no claim is made about any deployed environment.
* `IV-OBS-1` (test hygiene) and `IV-OBS-2` (blanket `authenticated` grants) are
  recorded as Low, non-blocking; `IV-OBS-2` is covered by D-PO-1.

---

## 12. Final principle statement

The programme was executed under AGENTS.md §85. Every closure in §3 rests on
**real persisted data, real processing paths, real server-side authorization,
real provenance, real tests and real evidence** — not on animations, hidden
buttons, hard-coded demo strings or unverified claims. Where verification could
not be performed, it is reported as unavailable rather than implied.


---

## 13. Reconciliation update — 2026-09-14 (post-clarification)

### 13.1 Scope correction recorded

Per the PO's clarification of 2026-09-14, the agreed sequence is **Phase 8 → Phase 8-X →
OHD findings**, and **OHD findings are out of scope for this cycle**: no OHD analysis as a
workstream, no OHD classification, no OHD remediation tasks, no OHD-driven scope expansion.
The OHD section of the master execution instruction is **superseded** by that clarification.
Where a Phase 8-adjacent issue was encountered incidentally during authorised work, it is
recorded (below) and **not** fixed or expanded into a workstream.

### 13.2 Ledger updates (documentation only — no code, schema, API or test change)

| Item | Before | After |
|---|---|---|
| `C-B3-1` applicability lifecycle completeness | confirmation requested | **CONFIRMED — CLOSED** (PO §5 baseline matches as-built; B3 **not** reopened) |
| `D-B3-13` evidence gap → reporting/finalisation effect | new PO decision required | **RESOLVED — (a) advisory only, no blocking rule** (PO §4; as-built behaviour ratified) |
| Draft-report retention/replacement/deletion | implied open question | **routed to report-lifecycle/B4 decisions**, not B3 (PO §5) |
| OHD findings cycle | in master instruction | **out of scope this cycle** (PO clarification) |

Recorded in `docs/architecture/CARBONTALLY_PHASE8_B3_PO_DECISION_RECORD_20260914.md` §11.
**B3 remains closed (`…051`); its contract is unchanged.**

Incidental Phase 8-adjacent observation, recorded once and not actioned (per the scope
correction): the running development database still lacks the B1/B2 disclosure schema while
Phase 8 code expects it — the same `F-049-3` / `…029` environment item already in this
ledger, blocked on the PO naming/authorising a target environment (`D-02`). No fix attempted.

### 13.3 Phase 8 — consolidated status

| Workstream | Status | Implementation | Verification | PO closure | Remaining blocker |
|---|---|---|---|---|---|
| **G0** gate register | CLOSED (`…042`) | n/a | n/a | recorded | **G0-D** (production) open |
| **B1** disclosure foundation | CLOSED | done | V1R PASS (6 × P3) | closed (`-010` lineage) | applies in **no** persistent env (`D-02`) |
| **B2** evidence line items | CLOSED | done | **IV PASS** (`-025`) | *record missing* | `…028` — **PO closure statement required** (agent may not self-record) |
| **B3** disclosure integration | CLOSED (`…051`) | 2 migrations + domain/data/service/API | **V3 PASS 175/175** | closed | none (`C-B3-1` now confirmed closed) |
| **B4** narrative + finalisation + frozen artefact | CLOSED at gate V4 (`…052`) | 2 migrations + 5 modules + API | **V4 PASS** (`…052`); A1 replay discharged (`…055`) | closed | none |
| **S1** report correctness | COMPLETE | done | **IV PASS** (`…056`) | n/a | none |
| **S2** lifecycle schema + report RLS | CLOSED (`…046`) | index + posture | verified (suite + replay) | closed (Option A) | none |
| **S3** report lifecycle states | COMPLETE | done | **IV PASS** (`…056`) | n/a | none |
| **S4 / S5 / S7** | CLOSED via B4 | inside B4 (`B4-D10`) | inside gate V4 | closed (`…052`) | none |
| **S6** frontend lifecycle UI + comments + `A7` | NOT ALLOCATED | none | n/a | n/a | **PO allocation + comments + `A7` decisions** |
| **S8** AI narrative | NOT AUTHORISED | none | n/a | n/a | PO authorisation; preconditions unmet |
| **P1** extraction fidelity | PACKAGE CLOSED (`…037`) | package only | n/a | n/a | customer-visible enablement: **external** (real documents) |
| **P2** factor catalogue | CENSUS CLOSED (`…038`); **EF-E remediation CLOSED** (`…054`) | EF-E implemented | verified (`…054`) | closed | EF-A/EF-D magnitude: **external** (real catalogue) |
| **RLS** remediation | RLS-4A-1 **CLOSED** (`…042`/D-1) | containment migration | independently verified | closed | **RLS-4A-2** = separately authorised (not granted); **steps 3–5** = `D-4`…`D-10`, `D-12` undecided |
| **`…029`** B1/B2 env application | BLOCKED | none | n/a | n/a | **PO must name the non-production target (`D-02`)** |
| **D16 / legacy route** | NOT AUTHORISED | none | n/a | n/a | `D-19` separate authorisation |


### 13.4 Phase 8-X / Phase 9 — consolidated status

| Workstream | Status | Implementation | Verification | PO closure | Remaining blocker |
|---|---|---|---|---|---|
| **Naming / ownership conflict** (`PX-1`, `D-07`) | **RESOLVED** | n/a | n/a | PO ruling recorded in `…040`: **no Phase 9; Phase 8-X remains inside Phase 8** | none |
| **X1** (`…043`) | **NOT ELIGIBLE — STOP** | none | n/a | n/a | **`PX-2` (what must be monitored and at what thresholds), `PX-4` (level of platform access), `PX-5` (heartbeat/reporting contract) — PO decisions not yet given** |
| **X1 independent verification** (`…044`) | BLOCKED | n/a | n/a | n/a | depends on X1 |
| **X2** (`…045`) | BLOCKED | none | n/a | n/a | depends on X1 closure + `PX-6` (who is alerted), `PX-7` (what is retained) |
| **X4–X7** stages | BLOCKED | none | n/a | n/a | depend on X1/X2 chain and their own `PX` decisions |
| **X8** | UNDEFINED | n/a | n/a | n/a | no definition exists in any recovered source |
| **Phase 9 (any)** | OUT OF SCOPE | none | n/a | n/a | ruled out by the PO (`…040`); the Phase 9 baseline commit remains unratified |

Dependency chain: **`PX` decisions → X1 → X1 IV → PO closure → X2 → X2 IV → PO closure → …**
No gate may be skipped, and X1 must not begin merely because the codebase is ready.

### 13.5 Production readiness

| Question | Answer |
|---|---|
| Is production authorised? | **NO** |
| Which G0 gates remain? | **G0-D** (production migration/deployment strategy) is **open**; the remaining G0 sub-gates were closed at the G0 register reconciliation (`…042`). |
| Which security gates remain? | **RLS-4A-2** (separately authorised, not granted) and **RLS steps 3–5** (`D-4`…`D-10`, `D-12` undecided). RLS-4A-1 containment holds (1 `anon`-exposed relation — `emission_factors`). |
| Have migrations been applied to production? | **NO.** 34 pre-existing + 2 B2 outstanding migrations remain unapplied to production; nothing in this cycle touched production. |
| Does any deployment authorisation exist? | **NO.** `…029` (B1/B2 environment application) requires the PO to name the environment (`D-02`) and deployment remains a separate authorisation. |

### 13.6 Overall verdict

**PHASE 8 PARTIALLY COMPLETE — BLOCKED BY PO/GOVERNANCE ITEMS**

*Every Phase 8 workstream that has an authorisation, a satisfied dependency and an available
environment is implemented, independently verified and closed. What remains is not
implementation work: it is a set of PO decisions and one missing PO closure statement
(`§13.3`), plus two external-evidence dependencies. No Phase 8 implementation authorisation
is outstanding for anything currently implementable.*

**PHASE 8-X NOT COMPLETE — BLOCKED BY PO/GOVERNANCE/DEPENDENCY ITEMS**

*Ownership is resolved, but X1 cannot begin until the `PX` decisions for its scope are given;
X2 and later stages depend on X1.*


---

## 14. REGISTER RECONCILIATION — after X2 PO closure (2026-09-14)

Reconciled against the repository, the authoritative contracts/decision records and the PO
closures. **No implementation was performed as part of this reconciliation.**

**Classification key:** (1) CLOSED · (2) IMPLEMENTATION-READY AND ALREADY AUTHORIZED ·
(3) REQUIRES PO DECISION · (4) REQUIRES IMPLEMENTATION AUTHORIZATION ·
(5) REQUIRES EXTERNAL EVIDENCE/INPUT · (6) BLOCKED BY PREREQUISITE · (7) SEPARATE BOUNDED REMEDIATION.

### 14.1 Phase 8

| Item | Class | Note |
|---|---|---|
| G0 gate register | **1** | closed (`…042`); only G0-D remains (separate row) |
| B1 · B2 · B3 · B4 | **1** | all closed; B2 re-confirmed 2026-09-14; B4 at gate V4 + A1 replay discharged |
| S1 · S2 · S3 · S4 · S5 · S7 | **1** | S1/S3 IV PASS (`…056`); S2 closed (`…046`); S4/S5/S7 inside B4 |
| `…028` B2 closure record · `…029` environment | **1** | record exists (+§8 re-confirmation); QA named ⇒ `…029` satisfied, `F-049-3` resolved |
| P1 package · P2 census · P2 EF-E | **1** | closed (`…037`, `…038`, `…054`) |
| RLS-4A-1 · RLS-4A-2 · `F-4A2-2` | **1** | closed; both PO-accepted |
| `F-030-1` | **1** | repaired in B4 closure (`…052`) |
| **S6** — report-lifecycle UI + comments + `A7` | **3** | decision package delivered; 6 decisions (S6-1…S6-6) awaited |
| **RLS steps 3–5** (RLS-5/3/2/1) | **3** | needs `D-4`…`D-10`, `D-12` rulings |
| **F-4A1B-1** — `anon` sequence-default `UPDATE` | **3/7** | recorded by the PO as a **future, separately bounded decision** |
| **B4-D12** — commercial/entitlement gating of finalisation | **3** | commercial decision required |
| **N3 retention control plane** — operationalising the remaining retention domains | **3/4** | telemetry domain delivered by X2; other domains remain "not configured" by design (no duration invented) |
| **S8** — AI-assisted narrative | **4** | not authorised; AI preconditions unmet |
| **D16 / legacy** (`D-19`) | **4** | separate authorisation |
| **F-X1-2** — EF-E test-double drift (2 failing tests) | **7** | PO: **not** authorised under X1; bounded test-double fix |
| **F-B3-7** — flaky `'777'` substring assertion in the closed B2 suite | **7** | carried from B3 closure as a bounded test-only fix |
| **I1** — Insight foundation | **3** | authorisation ambiguity (commit subject vs ratified D2) unresolved |
| **`…048`** — E1 evidence closure | **5** | needs authoritative ESRS sources |
| **P1 enablement** — customer-visible extraction fidelity | **5** | needs real non-production customer documents |
| **P2 EF-A / EF-D** — catalogue magnitude | **5** | needs the real factor catalogue (production boundary) |
| **G0-D / production** | **3/4** | production remains unauthorised; 34 + 2 migrations unapplied |

### 14.2 Phase 8-X

| Item | Class | Note |
|---|---|---|
| Ownership/naming conflict (`PX-1`, `D-07`) | **1** | resolved by the PO (*no Phase 9; 8-X inside Phase 8*) |
| **Stage X1** — foundation/baseline (no schema change) | **1** | established by the discovery/readiness work and the X1 implementation |
| **Stage X2** — worker & queue visibility (M1) | **1** | delivered and PO-closed (task X1, `…061`) |
| **Stage X3** — health correctness & worker liveness (M2) | **1** | delivered and PO-closed (task X1, `…061`) |
| **Stage X6** — thresholds & alerting (S1) | **1** | delivered and PO-closed (task X2, `…062`) |
| **Stage X4** — aggregation layer: failures, SLA, usage, imports, delivery, AI (M3, S3–S6) | **4** (+**3** on scope) | **not built**; the next real 8-X capability. Needs implementation authorisation and a scope decision on which views come first |
| **Stage X5** — operations console extension (M4) | **4/6** | not built; depends on X4 data and on the ops-console/UI boundaries (D19/D21) |
| **Stage X7** — API runtime metrics (S2) | **3/4** | not built; needs new in-process instrumentation **and** a decision on what may be recorded (no request-payload retention) |
| **Stage X8** — testing/security/operational verification | **6** | cannot complete while X4–X7 are unbuilt (per-task IV for X1/X2 is done) |
| **M5 / G-23** — runtime/deployment introspection | **3** | explicitly **excluded** by the PO (provider access declined, `PX-4` deferred) |
| `PX-4`, `PX-11` — platform/provider access & external APM | **3** | declined/deferred; a commercial + access decision |

### 14.3 Not in scope (restated)

**Phase 9** — ruled out by the PO. **OHD findings** — completely parked; not inventoried, not
classified, not remediated, and no disposition register was created, per the absolute boundary.


---

## 14.4 REGISTER AFTER S6 CLOSURE (2026-09-14) — final reconciliation

**S6 is now PO CLOSED** (`…063` §12), and `S6-ACTION-1` was ruled: `new_version` is **not**
implemented and is a **future, separately bounded increment** (its absence is **not** a defect).
**No implementation was performed by this reconciliation.**

### Phase 8 — the buildable queue is empty

| Class | Items |
|---|---|
| **Closed (Phase 8 product scope)** | G0 register · B1 · B2 · B3 · B4 · S1 · S2 · S3 · S4 · S5 · **S6** · S7 · `…028`/`…029` · P1 package · P2 census · P2 EF-E · RLS-4A-1 · RLS-4A-2 · `F-4A2-2` · `F-030-1` |
| **Separate workstream, gate HELD** — *not* a Phase 8 or 8-X deliverable | **RLS steps 3–5** (`D-4`…`D-10`, `D-12`; 13 register decisions remain). The hold register states the remediation gate requires **explicit PO authorisation to reopen** and is **not** authorised by the passage of time, by Phase 8 completion, or by Phase 8-X completion. Verified production baseline remains 97/104 tables RLS-disabled, `anon` `GRANT ALL` |
| **Optional hardening / commercial configuration** | `F-4A1B-1` (latent, inherits only on future sequences; not reachable by anonymous clients) · `B4-D12` (commercial gating of finalisation) · **N3 remaining retention domains** (no durations were ever approved; data kept indefinitely is a cost, not a correctness issue) |
| **Test hygiene, separately bounded** | `F-X1-2` (2 failing unit tests, PO-excluded from X1) · `F-B3-7` (flaky assertion in the closed B2 suite) |
| **Not authorised / deferred** | **S8** (AI narrative; preconditions unmet) · **D16/legacy** (`D-19` never ruled) · **I1** (authorisation contradiction unresolved) |
| **External evidence required** | `…048` (authoritative ESRS sources) · **P1 enablement** (real customer documents) · **EF-A / EF-D** (real factor catalogue) |
| **Deployment, unauthorised** | **G0-D / production** (34 + 2 migrations unapplied; no production authorisation) |
| **Future S6 increment** | `S6-ACTION-1` — expose "create revised version" (its own bounded PO decision required) |

### Phase 8-X — three stages unbuilt, verification stage blocked

| Stage | State |
|---|---|
| X1 foundation · X2 worker/queue visibility · X3 health/liveness · X6 thresholds/alerting | **DELIVERED + PO CLOSED** |
| **X4** — aggregation layer: failures, SLA, usage, imports, notification delivery, AI activity (M3, S3–S6; gap G-20) | **UNBUILT** — needs implementation authorisation **and** a scope decision (which views first) |
| **X5** — operations console extension (M4; gap G-25) | **UNBUILT** — depends on X4 |
| **X7** — API runtime metrics (S2) | **UNBUILT** — needs new in-process instrumentation **and** a decision on what may be recorded |
| **X8** — testing, security and operational verification | **BLOCKED** — cannot verify stages that do not exist |
| M5 / G-23 runtime/deployment introspection | **PO-EXCLUDED** (`PX-4` declined) |

### Genuine completion requirements (distinguished)

* **Phase 8:** no remaining *build* work. The only open question is whether the PO **declares Phase 8
  complete** with the named deferrals above (S8, D16, I1, RLS hold, external evidence, G0-D) or
  chooses to close any deferral first.
* **Phase 8-X:** genuinely **incomplete** — X4, X5 and X7 are unbuilt and X8 cannot run until they
  exist. This is the only remaining *buildable* workstream in the programme.
* **OHD:** may begin only after **both** are fully completed and PO-closed. Phase 8 is
  closure-ready; Phase 8-X is not.

### Next actual PO gate

**Phase 8 completion declaration + Phase 8-X X4 authorisation/scope.** Everything else is either
held (RLS), optional, external, unauthorised, or a future increment. Nothing was begun.

---

## 15. PHASE 8 — PO DECLARATION OF COMPLETE (2026-09-14)

> **Phase 8 is PO DECLARED COMPLETE** (PO approval of Option (a)). *"This declaration means Phase 8
> product/build scope is complete. It does NOT mean production is approved, secure for deployment, or
> that any held/deferred work is silently accepted as complete."*

**Named deferrals / holds carried with the declaration:**

| Held / deferred | Status |
|---|---|
| **RLS steps 3–5** | Separate security workstream — **gate held** |
| **G0-D / production** | **NOT AUTHORISED**, and still blocked by the held RLS workstream |
| S8 / AI narrative | Deferred |
| D16 / legacy | Deferred |
| I1 | Unresolved authorization/evidence issue |
| `F-X1-2`, `F-B3-7` | Separate test-hygiene remediation |
| `F-4A1B-1` | Future bounded security decision |
| B4-D12 | Future commercial decision |
| N3 remaining retention domains | Future retention decisions |
| External ESRS / P1 / P2 evidence | Remain external |
| S6 `new_version` | Future separately bounded increment |

No closed Phase 8 work was reopened or reimplemented as part of this declaration. Phase 8-X continues
as the active workstream (X1, X2 delivered; **X4 contract prepared, implementation not authorised**:
`CARBONTALLY_PHASE8X_X4_AGGREGATION_CONTRACT_20260914.md`).

