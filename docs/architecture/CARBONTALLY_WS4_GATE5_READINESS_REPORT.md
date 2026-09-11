# CarbonTally WS4 — Gate 5 Definition + Readiness Review

- **Date:** 4 September 2026
- **Nature:** Analysis / readiness only — **no code, SQL, migration, RLS, API, UI, D38/D39/D40, workflow, architecture or commit/push changes were made.**
- **Status recorded:** Gate 3 = PASSED/ACCEPTED; Gate 4 = PASSED/ACCEPTED (after F1/F2 remediation, which is ACCEPTED). Phase 5 remains open pending Gates 5 and 6.

---

## 1. Authoritative source reviewed

| Document | Role |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE5_WS4_FINAL_ACCEPTANCE_REPORT.md` | **Authoritative WS4 final-acceptance running log** (the numbering the PO ratified for Gates 1–3). This report defines the remaining provenance acceptance work only as a **group**: *“Fixture-level human/automated provenance matrix (Gates 4–6)”* (recorded under “Gates still unexecuted this session”, item 5, with “mechanism assessment stands”), plus the related *Human processing provenance*, *Automated extraction provenance assessment*, and *Human-after-automation attribution* sections. |
| `docs/architecture/CARBONTALLY_WS4_GATE4_READINESS_REPORT.md` | Canonical post-Gate-3 reconciliation of the Gates 4–6 group (authority rule, numbering conflict, per-gate itemization gap, readiness sub-assessments). |
| `docs/architecture/CARBONTALLY_WS4_GATE4_REMEDIATION_F1_F2_REPORT.md` and `CARBONTALLY_WS4_GATE4_FINAL_ACCEPTANCE_REPORT.md` (current revision) | Record of what “Gate 4” was executed and accepted as: the **human-provenance matrix** (verification-only), including the accepted F1/F2 remediation scope note that machine/provider/model provenance remains out of scope. |
| `docs/architecture/CARBONTALLY_PHASE5_WS4_UI_BROWSER_IMPLEMENTATION_REPORT.md` | Historical WS4 UI-browser continuation scheme. **Not authoritative for this numbering** (its “Gate 4/5/6” are a different, already-closed set: D38→D40 browser proof / full-persona matrix / two-session verification). Explicitly excluded per the authority rule. |

**Authority finding:** the authoritative final-acceptance scheme defines Gates 4–6 **only as a grouped fixture-level human/automated provenance matrix** and does **not** preserve a verbatim per-gate itemization of Gate 4 vs Gate 5 vs Gate 6. The Gate-4 readiness report already recorded this gap and required **PO ratification of the per-gate itemization** before executing the individual gates. Gate 4 was subsequently executed and accepted as the **human-provenance matrix**; no authoritative document has since itemized “Gate 5”.

---

## 2. Gate 5 exact definition

**Not defined as an independent gate in the authoritative documentation.**

The only authoritative wording covering the gates after Gate 4 is the group
statement in `CARBONTALLY_PHASE5_WS4_FINAL_ACCEPTANCE_REPORT.md`:

> “Fixture-level human/automated provenance matrix (Gates 4–6) — mechanism assessment stands.”

Supporting sections of the same log enumerate **three sub-themes** that the group
comprises (in the order they appear in the Human/Automated provenance sections):

1. **human attribution matrix** — a complete ~11-action attribution matrix over one continuous run (executed and accepted as Gate 4);
2. **automated-extraction machine provenance** — machine/provider/model/version attribution for automatic extraction in the durable/audit contract (recorded as a **B/C documented residual, non-blocking**, “if ratified into Gates 4–6”);
3. **human-after-automation attribution** — saving/approving automated output must not rewrite the automated actor record (assessed at mechanism level only; no dedicated automated-extraction E2E fixture run).

No authoritative sentence assigns these themes to specific gate numbers, and no
PO decision record itemizing “Gate 5” was found in the repository. The historical
UI-browser “Gate 5 = full persona matrix” meaning is from the older numbering
scheme and is **not** to be used.

---

## 3. Mandatory acceptance criteria for Gate 5

**Cannot be enumerated without inference.** Because the authoritative record does
not itemize Gate 5, no verbatim mandatory criterion list exists to report. Under
the task authority rule (“Do NOT invent Gate 5 criteria”), this report does **not**
manufacture a criterion list.

For completeness, the *candidate* reading of the group (Gate 4 = human attribution
matrix, Gate 5 = automated-extraction machine provenance, Gate 6 =
human-after-automation attribution) is consistent with the ordering of the three
documented sub-themes and with Gate 4’s accepted scope — **but that mapping is
inference and requires PO ratification before it becomes authoritative.** No
acceptance decision is based on it here.

---

## 4. Required positive / negative / DB-audit / UI / cleanup checks for Gate 5

**Not specified per gate.** The authoritative record specifies these only at the
level of the Gates 4–6 *group* and its general provenance-mechanism descriptions
(human/automated attribution, audit events, workflow columns, snapshots/evidence,
isolation), plus the verification conventions used by the accepted Gate-1–4 runs
(real stack, disposable fixtures, real personas, direct DB/audit evidence, UI where
required, exact baseline restoration). These cannot be converted into a
Gate-5-specific mandatory checklist without the missing itemization.

---

## 5. Machine/provider/model/version provenance

**OUT OF SCOPE — NOT REQUIRED FOR GATE 5**

As the authoritative documentation currently stands:

- Automated-extraction machine/provider/model/version attribution is recorded as a
  **documented residual (B/C), not an acceptance blocker**, and as
  **optional/future “unless ratified into Gates 4–6”** (Gate-4 readiness §7/§8).
- No authoritative text makes machine provenance a *mandatory Gate-5 criterion*.
- Therefore machine provenance is **not required for Gate 5** under the current
  authoritative specification. It becomes in-scope **only if the PO ratifies** the
  per-gate itemization (candidate reading: Gate 5 = automated-extraction machine
  provenance matrix), in which case a small bounded implementation workstream
  (additive automatic-processing provenance: machine/provider/model/version on the
  durable job record + audit-visible attribution; human saves never rewrite the
  automated actor; no D38 assignee-vocabulary change) would be required **before**
  the verification-only fixture run.

---

## 6. D40 entity-assignment notifications

**OUT OF SCOPE — NOT A GATE 5 BLOCKER**

- D40 is accepted (WS3/WS4 API-read inbox evidence).
- D40 entity-assignment notifications are documented as **optional/future (C)** and
  explicitly excluded from earlier gates; they are **not** recorded as a mandatory
  criterion of Gate 5 (or of the Gates 4–6 group).
- No D40 implementation or redesign is required or recommended for Gate 5.

---

## 7. Previously deferred items vs Gate 5

| Previously deferred item | Mandatory for Gate 5? | Basis |
|---|---|---|
| Full 11-action human attribution matrix over one continuous run | **Resolved** — executed and accepted as Gate 4; not deferred any longer | Gate-4 final acceptance (PASSED) |
| Automated-extraction machine/provider/model/version provenance | **Not mandatory for Gate 5 as currently specified** (ratification-dependent candidate) | B/C documented residual; “optional/future unless ratified into Gates 4–6” |
| Human-after-automation attribution fixture (automated output saved/approved without rewriting the automated actor) | **Not explicitly assigned to Gate 5** (candidate: Gate 6 sub-theme; not verified by a dedicated E2E fixture yet) | Group wording + assessment-only status |
| D40 entity-assignment notifications | **No** | Accepted; optional/future (C) |
| Full persona browser matrix (historical UI-browser “Gate 5”) | **No** — older numbering, already closed/partial in that continuation; not the authoritative Gate 5 | Numbering-conflict ruling (Gate-4 readiness §3) |

---

## 8. Dependencies of Gate 5

Only what the authoritative group text supports:

- **Gate 3 / Gate 4:** Gates 3 and 4 are PASSED/ACCEPTED and are **not** re-run. A
  Gate-5 execution would build on the same frozen architecture and on the accepted
  provenance matrix conventions; the item-level assignment model, D38 ledger,
  origin immutability, effective assignment, PE isolation, CT-QC independence and
  customer-approval separation all remain frozen.
- **Human provenance:** the human-provenance matrix is accepted (Gate 4).
- **Automated-extraction provenance:** recorded as a mechanism-level residual only;
  no authoritative dependency link to a specific gate.
- **Machine/provider/model/version provenance:** see §5 — not a current mandatory
  dependency.
- **D38 / D39 / D40:** frozen/approved; no Gate-5 dependency is documented on any of
  them (D40 entity notifications explicitly optional/future).
- **Workflow / snapshots / evidence:** the group is a provenance matrix over the
  existing workflow; snapshot/evidence chains are canonical and accepted. No new
  workflow or evidence architecture is documented as a Gate-5 prerequisite.

---

## 9. Is Gate 5 verification-only or does it require implementation?

**Cannot be determined for “Gate 5” as an itemized gate** (definition missing).

For the *candidate* sub-themes only:
- **human-after-automation attribution** would be verification-only on a disposable
  automated-extraction fixture (mechanism already exists; no dedicated E2E run yet);
- **automated-extraction machine provenance** would **require a small bounded
  implementation workstream first** (machine/provider/model/version in the durable
  job/audit record) before any verification run — and is currently non-mandatory.

---

## 10. Current build readiness

| Capability | State |
|---|---|
| Frozen architecture (single backend/DB/Auth, PE model, D38/D39/D40, immutable origin, effective assignment, isolation, independent CT QC, separate customer approval, canonical evidence chain) | **In place and accepted** (Gates 1–4) |
| Human provenance matrix | **Executed and accepted (Gate 4)** |
| Automatic-processing durable job records with deterministic/OCR actor + timestamp | **In place** |
| Machine/provider/model/version attribution in the durable/audit contract | **Not implemented** (B/C documented residual; not a current Gate-5 requirement) |
| Dedicated automated-extraction E2E fixture (automated actor preserved through human save/approve) | **Not yet run** (assessed at mechanism level only) |
| Regression / environment | Post-F1/F2 full backend unit suite green; integration-suite environmental failures pre-existing and unrelated (noted, not fixed) |

**Readiness verdict:** the *build* is ready to support verification-only provenance
runs, and no product defect blocks the candidate sub-themes. However a **Gate 5
cannot be declared ready or not-ready as specified** because no authoritative
itemized Gate-5 definition exists to measure against.

---

## 11. Blockers

**Definition blocker (sole blocker):** the authoritative final-acceptance scheme
itemizes Gates 4–6 only as a grouped fixture-level human/automated provenance
matrix. No verbatim per-gate itemization of Gate 5 is preserved, and no PO
decision record assigning the sub-themes (human attribution / automated machine
provenance / human-after-automation) to gate numbers was found. Establishing a
Gate-5 criterion list would require inference, which this task forbids.

No code/architecture blocker exists for the underlying provenance work.

---

## 12. Recommended next bounded task

**Exactly one recommended next action:** obtain PO ratification of the Gate 4–6
per-gate itemization, explicitly confirming:

1. the authoritative numbering (WS4 final-acceptance scheme — already used for Gates 1–4); and
2. the per-gate mapping of the three documented group sub-themes — e.g.
   **Gate 4 = human attribution matrix (done/accept), Gate 5 = automated-extraction machine provenance matrix, Gate 6 = human-after-automation attribution**, or the PO’s preferred split.

Then, if the PO ratifies **Gate 5 = automated-extraction machine provenance**:

a small bounded **additive automatic-processing provenance implementation**
workstream (machine/provider/model/version on the durable extraction/job record and
in an audit-visible attribution field; human saves/approvals distinct — never
rewriting the automated actor; no D38 assignee-vocabulary change; focused
allowed + attribution regression assertions), followed by a **verification-only
Gate-5 fixture run** on a disposable automated-extraction item with the full
matrix evidence conventions used by Gates 1–4, and exact baseline restoration.

Until that ratification exists, **no implementation should be performed** for any
“Gate 5” item.

---

## FINAL VERDICT

**GATE 5 DEFINITION BLOCKED**

The authoritative documentation does not contain enough information to establish
Gate 5 without inference: Gates 4–6 exist only as a grouped fixture-level
human/automated provenance matrix with no preserved per-gate itemization, and no
PO decision record itemizes Gate 5. Machine/provider/model/version provenance is
**OUT OF SCOPE — NOT REQUIRED FOR GATE 5** as currently specified, and D40
entity-assignment notifications are **OUT OF SCOPE — NOT A GATE 5 BLOCKER**. No
code, SQL, migration, RLS, API, UI, D38/D39/D40, workflow, or architecture was
changed; nothing was committed or pushed.
