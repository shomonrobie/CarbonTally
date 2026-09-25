# P17 ARCH-06 — Reconciliation of the Independent ARCH-05 Re-Verification Findings

**Task ID:** `P17-ARCH-06-20260925-RECONCILE-ARCH-05-FINDINGS`
**Timestamp:** 2025-09-25 (local session)
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`
**Baseline SHA (starting):** `4bd87a36048bb1c4427f1607432f5109584b3801` — the ARCH-05 independent re-verification commit
(its parent `172bdd26d1d2fd2c7bf03a05a40532b662117729` is the ARCH-04 reconciliation commit)
**Baseline SHA (ARCH-04, as named by the task):** `172bdd26d1d2fd2c7bf03a05a40532b662117729`
**Ending SHA:** the documentation-only commit that introduces this report. Its full SHA is reported in the task's
mandatory final report; it is deliberately **not** embedded in the file it introduces, so that this report does not
need a self-referential (and therefore unwritable) commit hash.
**Commit message:** `docs(p17): reconcile ARCH-05 freeze findings`
**Author:** Cline — *documentation/governance reconciliation agent*. **Not** an independent verifier.
**Scope:** DOCUMENTATION ONLY.

---

## 0. Verdict

```
P17_ARCH_RECONCILIATION_COMPLETE
```

**Meaning of this verdict.** This is a **reconciliation-completeness** verdict only. It states that all five open
findings raised by the independent ARCH-05 re-verification (ARCH05-01 … ARCH05-05) have been addressed in the
governance/architecture documentation. It is **NOT**:

- `P17_ARCH_FREEZE_PASS` — no independent verification has been performed by this task, and this task is not an
  independent verifier;
- an authorisation to implement anything;
- an acceptance of any product capability;
- a claim that Scope 2, Scope 3 or any of the 15 categories is implemented.

**Cline reconciliation is not independent acceptance.** The corrected baseline must be **independently re-verified**
before P17-0 or P17-A may be authorised. Per the PARTIAL rule applying to ARCH-05, **P17-0 was not authorised by
ARCH-05**; ARCH-06 likewise **does not authorise it**.

---

## 1. Task identity, scope and independence statement

| Item | Value |
|---|---|
| Task ID | `P17-ARCH-06-20260925-RECONCILE-ARCH-05-FINDINGS` |
| Role | Documentation/governance reconciliation agent (Cline) |
| Primary source | `docs/architecture/CT-PO-P17-ARCH-05-INDEPENDENT-REVERIFICATION-FREEZE-20250925.md` |
| Source verdict | `P17_ARCH_FREEZE_PARTIAL` |
| Source verifier | `P17-ARCH-05-20250925-INDEPENDENT-RE-VERIFICATION-FREEZE` (**independent**) |
| Findings in scope | ARCH05-01 … ARCH05-05 (open); ARCH05-06 … ARCH05-08 (INFO — preserved as-is) |
| Nature of work | Documentation / governance reconciliation only |

**Independence statement.** This task did **not** independently verify anything. It read an independent verifier's
report and made documentation corrections in response to it. Section §2 separates what ARCH-05 *confirmed* (so this
task does not re-litigate it) from what ARCH-05 *raised* (so this task corrects it).

---

## 2. What ARCH-05 confirmed (not re-litigated here)

ARCH-05 was an **independent re-verification of the ARCH-04 corrections**. It confirmed as genuinely reconciled:

| Item | ARCH-05 confirmation |
|---|---|
| HIGH-01 — consultant organization identity | Reclassified to `PARTIAL — MISSING LINKAGE`; verified against the live schema (`consultant_profiles` keyed by `user_id`, no `organization_id`); PO product decision preserved |
| MEDIUM-01 — acting-for propagation vs `AC-AUDIT-01` | 8 paths with per-path (A) persist / (B) derive disposition; bounded derivation rule; "context is not authorization" preserved |
| LOW-01 — tenant-key naming | One canonical conceptual/physical mapping documented |
| LOW-02 — `energy_type` vocabulary | Authoritative 4-value vocabulary; `fuel` excluded |
| LOW-03 — stale acceptance metadata | Replaced with `RECONCILED_BY_ARCH_02_WITH_ARCH_04_CORRECTIONS` + `historical_note`; **not** changed to PASS |
| LOW-04 — Scope 3 customer/UIUX representation | `cross_cutting_requirements` block; claim narrowed |
| EXTRA-01 — `CORRECTION REQUIRED` lifecycle | Carried as a P17-0 discovery obligation |
| EXTRA-02 — estimation-record ordering | Documented as risk R11 |

**Therefore §3–§6 below address only the five findings ARCH-05 left open.** Nothing above is re-opened or changed by
this task.

---

## 3. ARCH05-01 / ARCH05-02 — P17-F E2E demand, and ARCH-04's inaccurate completeness claim

### 3.1 The finding

P17-F bullet 1 read:

> *"one END-TO-END VERIFIED result per category (6,7,8,9,10) where the category is not DEFERRED"*

Category **10 is `NOT_IMPLEMENTED`, not `DEFERRED`** (authoritative table:
`p17_scope3_category_matrix_20250925.json → status_rollup.NOT_IMPLEMENTED = [2,10]`). Read literally, P17-F bullet 1
therefore still **demanded an implementation E2E result of a non-implemented category** — the identical contradiction
class ARCH-03 had raised against P17-E and which ARCH-04 had claimed to have reconciled (ARCH-04 §7).

ARCH-05 additionally found that ARCH-04 §7's assertion *"the remaining gates were re-checked for the same class of
contradiction … so no further contradiction of this class exists"* was **inaccurate**: the re-check covered other
gates but did not read P17-F's own bullet 1 against its own category 10.

### 3.2 Before → after

| Location | Before (as at ARCH-05) | After (ARCH-06) |
|---|---|---|
| `p17_acceptance_matrix_20250925.json` → `phase_gates[P17-F].must_pass[0]` | "one END-TO-END VERIFIED result per category (6,7,8,9,10) **where the category is not DEFERRED**" — demands E2E of `NOT_IMPLEMENTED` category 10 | Status-conditional: the acceptance level is governed by the category's **authoritative status**, driven by `status_conditional_acceptance_rule`; `NOT_IMPLEMENTED` (category 10) → **NO implementation E2E is required and no E2E result may be demanded of it** |
| `phase_gates[P17-F].must_pass[4]` (category 10) | "either delivered with an evidenced processor declaration or formally recorded as BLOCKED with the prerequisite stated" (ambiguous as to which branch satisfies the gate) | "…**for a NOT_IMPLEMENTED category the documented BLOCKED branch alone satisfies this gate, and no implementation E2E result is required of it**" |
| `phase_gates[P17-G].must_pass[0]` | "one END-TO-END VERIFIED result per category (11,12,13,14,15) where the category is not DEFERRED" — same unguarded pattern | Same status-conditional formulation; aligned with P17-F |
| `phase_gates[P17-E].must_pass[0]` | "one END-TO-END VERIFIED result for each category among (1,2,3,4,5) whose authoritative architecture status is SUPPORTED or PARTIAL" | Reframed into the canonical status model so that `PARTIAL` is **bounded** acceptance rather than an "E2E required" bucket (ARCH05-03) |
| `CT-PO-P17-ARCH-04-RECONCILIATION-20250925.md` §7 | **"…so no further contradiction of this class exists."** (unqualified) | The sentence is **preserved verbatim** and now carries (a) a `⚠ HISTORICAL STATEMENT — PRESERVED, KNOWN INACCURATE` block above it and (b) an explicit dated **`ARCH-06 reconciliation note`** after it declaring it **SUPERSEDED** |
| `p17_acceptance_matrix_20250925.json` | no canonical acceptance-status rule | new top-level `status_conditional_acceptance_rule` — a single definition referenced by E/F/G |

### 3.3 Why the ARCH-04 record was annotated rather than rewritten

The task requires that the ARCH-04 historical record is not altered except where a current contradiction must be
corrected by an **explicit reconciliation note**, and that historical statements be preserved and identified as
historical rather than silently changed. Accordingly:

- the ARCH-04 §7 sentence is **still present, word for word**, so the report remains a truthful account of what ARCH-04
  actually asserted;
- the correction is carried by an adjacent, dated, explicitly-labelled note stating that the sentence is inaccurate
  and **superseded**;
- ARCH-04's verdict is **not** retroactively altered. `P17_ARCH_RECONCILIATION_COMPLETE` stands as the historical
  ARCH-04 verdict and, as ARCH-04 itself stated, it was never `P17_ARCH_FREEZE_PASS`.

ARCH-04's verdict was **not a false completion claim**: the seven ARCH-03 findings it addressed *were* reconciled, as
ARCH-05 independently confirmed. Its §7 sentence was over-broad because it generalised a re-check of *other* gates
into a claim about *all* gates. That is precisely what ARCH-05 caught.

---

## 4. ARCH05-03 — Acceptance-status semantics (`PARTIAL` / bounded acceptance / `E2E VERIFIED`)

### 4.1 The finding

P17-E bullet 1 and P17-F/G bullet 1 had bucketed `PARTIAL` together with `SUPPORTED` in an "E2E required" bucket,
while the vocabulary bullet added by ARCH-04 defined `PARTIAL → bounded acceptance`. For category 1 (`PARTIAL`) the
two bullets therefore implied **different strictness** — interpretively reconcilable, but not one clean rule.

### 4.2 The resolution — one canonical rule

A single top-level rule now exists in `p17_acceptance_matrix_20250925.json`:

```json
"status_conditional_acceptance_rule": {
  "statement": "The acceptance level required of a category or feature is a function of its authoritative
                architecture status, NOT of the phase gate that happens to contain it. P17-E, P17-F and P17-G
                apply this one rule; no gate redefines it. NO gate may demand implementation E2E verification
                of a category whose status is NOT_IMPLEMENTED or DEFERRED.",
  "applies_to": ["P17-E", "P17-F", "P17-G"]
}
```

| Status | Is implementation E2E required? | What the report must contain | Explicitly NOT permitted |
|---|---|---|---|
| **`SUPPORTED`** | **Yes** — full defined acceptance path | The E2E result for that category | — |
| **`PARTIAL`** | **Bounded acceptance only** — the explicitly bounded/in-scope path must pass | The bounded in-scope result **and** an explicit statement of what remains outside scope | Presenting bounded acceptance as a full E2E claim; silently upgrading `PARTIAL` to `SUPPORTED` |
| **`NOT_IMPLEMENTED`** | **No** | An explicit blocked/not-implemented record naming the missing prerequisite (methodology, input contract, processor declaration, …) | Demanding any implementation E2E result; treating the blocked record as a gate failure; treating it as delivery of the category |
| **`DEFERRED`** | **No** | An explicit deferral record naming the PO decision or prerequisite that blocks it | Demanding any implementation E2E result; treating the deferral as a gate failure or as delivery |

### 4.3 The three explicit guarantees

1. **`PARTIAL` was NOT upgraded to `SUPPORTED`.** The rule carries a `non_upgrade_clause`, and **no category status
   was changed by this task**. The authoritative statuses are unchanged:
   `SUPPORTED [3,4,5,6]`, `PARTIAL [1,7,8,9,12,13]`, `DEFERRED [11,14,15]`, `NOT_IMPLEMENTED [2,10]`.
2. **`NOT_IMPLEMENTED` and `DEFERRED` categories may not be required to have E2E implementation verification.** The
   rule's `forbidden` list names this explicitly, and the E/F/G bullets now defer to the rule rather than restating it.
3. **The rule is defined once.** `p17_scope3_category_matrix_20250925.json` gained a `status_semantics_authority`
   pointer (it declares *status*, not *acceptance level*), so the vocabulary cannot drift between the matrix and the
   phase gates.

### 4.4 Status of category 2 and category 10

**Unchanged.** Category 2 remains `NOT_IMPLEMENTED` (not promoted); category 10 remains `NOT_IMPLEMENTED` (not
promoted). No methodology was invented for either, and neither was implemented.

---

## 5. ARCH05-04 — P17-H estimation-record ordering presentation

### 5.1 The finding

Phase plan §7 line 133 states the prerequisite explicitly:

> *"Prerequisites. P17-D (and P17-H's estimation records before categories 7/11/12 are attempted)."*

but the §16.2 ordering diagram placed **P17-H after P17-E/F/G**, which read literally could imply that categories
depending on estimation records (7, 11, 12) are completed before their prerequisite is established. ARCH-05 rated
this a **presentation tension**, not a new defect; ARCH-04 had already recorded it as risk **R11**.

### 5.2 The minimum correction applied

The phase plan was **not redesigned and no phase was moved, merged or reordered**. Two documentation changes only:

1. **In-diagram prerequisite marker** — the P17-H line in §16.2 now carries an explicit marker:
   `^ PREREQUISITE, not merely a later phase: P17-H's estimation_records must be established BEFORE the estimated
   categories 7 / 11 / 12 are attempted in P17-F / P17-G`.
2. **An explicit "Ordering note (ARCH-06 // ARCH-05 ARCH05-04)"** immediately below the diagram stating that the
   vertical sequence is *not* a claim that P17-E/F/G complete before P17-H, that the estimation-record workstream of
   P17-H must exist before those specific categories are attempted, and that an estimation-dependent category must not
   be reported as complete while its prerequisite is unestablished. It records that **the order itself is unchanged**
   and restates risk **R11**.

### 5.3 P17-H ordering confirmation

**CONFIRMED — the P17-H estimation-record prerequisite is now unambiguous.** The §16.2 diagram can no longer be read
as permitting categories 7 / 11 / 12 to complete before their prerequisite is established, and the ordering semantics
themselves are unchanged (§7 remains the normative statement of the prerequisite).

---

## 6. ARCH05-05 — P17-0 gate enumeration (10 → 12 items)

### 6.1 The finding

P17-0 `must_pass` did not **separately enumerate** (a) the delegated-user/acting-for authorization model or
(b) Scope 2 / Scope 3 accounting-model consistency. Both were only partly covered by other items and by
`AC-DELEG-01` / `AC-CAMS-01`.

### 6.2 The correction

Two new `must_pass` items were added. **Both are discovery/architecture gates only — no implementation.**

### 6.3 Updated P17-0 gate list (12 items — was 10)

| # | `must_pass` item |
|---|---|
| 1 | UIUX-01 §55 18-row existing-vs-missing matrix, from repository evidence |
| 2 | UIUX-01 §56 UX acceptance matrix (Staff / Direct Org / Consultant Own / Consultant Client / Client User / Disabled State / Audit / Backend Auth / UI Complete) |
| 3 | Full model classification — organization model, roles, authorization, RLS, consultant functionality, customer functionality, reportability lifecycle, audit model, evidence model, supplier model, snapshots, logs, reporting model |
| 4 | Consultant-client relationship reuse confirmed as the existing `consultant_clients` table (no new relationship entity invented) |
| 5 | **Consultant ↔ organization linkage decision** (ARCH-04 // ARCH-03 HIGH-01) — authoritative organization identity model for the consultant firm, its users/members, its client organizations and the consultant's own Scope 1/2/3 ownership |
| 6 | **Acting-for propagation map** across source/activity documents, suppliers, review/approval decisions, report artefacts, calculations, evidence and the audit trail (ARCH-04 // ARCH-03 MEDIUM-01) |
| 7 | **Acceptance-criteria consistency check** — phase acceptance criteria verified internally consistent with category status, deferred scope, PO methodology decisions and E2E requirements (ARCH-04 // ARCH-03 MEDIUM-02) |
| 8 | **`CORRECTION REQUIRED` lifecycle representation** — explicitly named, or its existing rework-edge representation documented (ARCH-04 // ARCH-03 §11 residual) |
| 9 | Customer capability/enablement representation decided (extend the existing scope-based governance primitive vs a new policy table) with a written rationale |
| 10 | **No UI or backend code changed in this phase (discovery only)** |
| **11** | **NEW — Delegated-user / acting-for AUTHORIZATION model** (ARCH-06 // ARCH-05 ARCH05-05 item 11): which acting-for contexts exist (consultant operator acting for a client organization; consultant team member acting for the consultant firm; processing-entity operator acting for an assigned entity), which organization context each operation is attributed to, where each is enforced **server-side** rather than in the UI, and how `AC-DELEG-01` / `AC-AUDIT-01` and UIUX-01 §5/§6/§35/§63 are satisfied. **Decision only — no implementation.** |
| **12** | **NEW — Scope 2 / Scope 3 accounting-model consistency** (ARCH-06 // ARCH-05 ARCH05-05 item 12): the 15 Scope 3 categories, the Scope 2 location-based and market-based paths and the double-counting controls DC-01..DC-11 are mutually consistent (no Scope 3 category double counts a Scope 1/2 quantity; no Scope 2 result re-adds a Scope 3 quantity), and `AC-CAMS-01` is confirmed to cover that consistency. **Architecture verification only — no implementation.** |

**P17-0 gate count: 12.**

Items 1–10 map to the task's required items 1–10; items 11–12 close the two enumeration gaps ARCH-05 identified. The
gate remains **discovery-only** and keeps `blocks: "P17-A and every later phase"`. Phase plan §§16.1 A13 records the
expansion; A13 also states that both new items are discovery/architecture gates only.

---

## 7. P17-E / P17-F / P17-G consistency confirmation

### 7.1 One rule, three gates

| Gate | Bullets (ARCH-01 → ARCH-04 → **ARCH-06**) | Bullet 1 acceptance level | Status vocabulary | Status-conditional before? | Status-conditional now? |
|---|---|---|---|---|---|
| **P17-E** | 4 → 6 → **6** | Status-driven (reframed from "SUPPORTED or PARTIAL") | References `status_conditional_acceptance_rule` | Yes (ARCH-04) | **Yes — via the canonical rule** |
| **P17-F** | 4 → 5 → **5** | Status-driven (**was: "not DEFERRED"**) | References `status_conditional_acceptance_rule` | **No — this was ARCH05-01** | **Yes — via the canonical rule** |
| **P17-G** | 3 → 4 → **4** | Status-driven (**was: "not DEFERRED"**) | References `status_conditional_acceptance_rule` | No (no `NOT_IMPLEMENTED` category in 11–15, but the pattern was unguarded) | **Yes — via the canonical rule** |

No bullet count changed at ARCH-06 (the correction rewrites bullet 1 and re-points bullet 2; it does not add bullets).

### 7.2 Confirmation

**CONFIRMED — P17-E, P17-F and P17-G now apply the same status-conditional rule.** Specifically:

- all three bullet 1s derive the required acceptance level from the category's **authoritative status**, not from the
  phase that contains it, and all three cite the single canonical `status_conditional_acceptance_rule`;
- all three bullet 2s reference the same canonical rule rather than restating a per-gate vocabulary, so the three
  gates can no longer drift apart (the previously duplicated restatement was the mechanism by which ARCH05-01 arose);
- none of the three may demand an implementation E2E result of a `NOT_IMPLEMENTED` or `DEFERRED` category;
- **the contradiction identified by ARCH-05 is removed**: category 10 (`NOT_IMPLEMENTED`) is no longer required to
  produce an E2E implementation result in P17-F, and its documented BLOCKED record is now stated to satisfy the gate;
- category 1 (`PARTIAL`) is subject to **bounded** acceptance under all three gates, with no differing strictness.

`evidence_required` lists per gate are unchanged. No category status was changed.

---

## 8. Preservation verification

Verified with `git hash-object` against `HEAD` (`4bd87a36048bb1c4427f1607432f5109584b3801`) at reconciliation time.

| Document | Tracked? | State | Blob (SHA-1) | Verdict |
|---|---|---|---|---|
| ARCH-01 — `CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md` | tracked | **identical to HEAD** | `d2a35438af9f1ff5483fec15e6005f93f0f5ad3d` | **PRESERVED — byte-identical, untouched** |
| ARCH-03 — `CO-STRING-P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE.md` | **untracked** | no index baseline; working-tree copy unmodified | `4d97b5b9abc97a6196af1e815289198091d80dae` | **PRESERVED — not modified, not committed, not deleted** |
| ARCH-05 — `CT-PO-P17-ARCH-05-INDEPENDENT-REVERIFICATION-FREEZE-20250925.md` | tracked | **identical to HEAD** | `e8ff682576528f9dd346eabb5dacb9fdd5c1891f` | **PRESERVED — byte-identical; the source report was not altered** |
| P16 — `CT-PO-P16-FINAL-VERIFICATION-20250925.md` | tracked | **identical to HEAD** | `661386784a7798a607a7c3fc3f7f30c02298529d` | **PRESERVED — byte-identical, untouched** |
| UIUX standard — `CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD.md` | tracked | **identical to HEAD** | `51ff70bdba4e3f4910b81bb6ff6f794443768ca8` | **PRESERVED — byte-identical, untouched** |
| POST-ARCH decisions — `CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` | tracked | **identical to HEAD** | `3060bcb02305d14a052d7b67c5ef600859009ea3` | **PRESERVED — byte-identical, untouched** |
| PO-CAMS decision — `CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` | tracked | **identical to HEAD** | `22566021037e76e007f788d465349cac2b5eb055` | **PRESERVED — byte-identical, untouched** |
| ARCH-02 — `CT-PO-P17-ARCH-02-RECONCILIATION-20250925.md` | tracked | **identical to HEAD** | `51cfd1a9236835314a948a1ee0cc79c9c4ab67f8` | **UNTOUCHED by ARCH-06** (its ARCH-04 annotations were already committed in `172bdd2`) |

**ARCH-04 historical record.** `CT-PO-P17-ARCH-04-RECONCILIATION-20250925.md` is **modified in exactly one place** —
§7, where a current, material inaccuracy had to be corrected. The correction is delivered as an explicit, dated
reconciliation note (§3.2/§3.3 above) with the historical sentence **preserved verbatim** and labelled historical.
No other part of ARCH-04 was touched. This is the single exception the task permits.

**History was not rewritten.** No `reset`, no `clean`, no `rebase`, no force-push, no commit deletion or amendment;
`.gitignore` and all pre-existing untracked files (including the ARCH-03 report) remain in their prior state.

---

## 9. Prohibition confirmations

### 9.1 Implementation prohibition — CONFIRMED

**No product implementation was performed by this task.** Specifically, **none** of the following was done:

- no application source code changed (`backend/`, `frontend/`, `admin/`, `src/`, `supabase/`, `tools/`, `scripts/`);
- no test changed;
- no migration created (the migration set is unchanged);
- no database schema changed;
- no Demo Lab implementation changed;
- no canonical corpus or oracle changed;
- no seed or dataset changed;
- no RLS policy changed;
- no UI, route, component or design-token change;
- no configuration or dependency change;
- no `.env`, credential, key, token or signed URL created, read into a document, or committed.

**Every file changed by this task is a Markdown or JSON document under `docs/architecture/`.** The task's own §10 gate
item — *"no UI or backend code changed (discovery only)"* — remains satisfied for ARCH-06 itself.

### 9.2 Production prohibition — CONFIRMED

**No production system was contacted, read or written by this task.** No production database, production API
(`https://carbontally-api.onrender.com`), production storage, production Supabase instance, production email path or
production frontend was touched. No deployment, migration, backup, restore or reset was performed.

No *local* database was opened either: ARCH-06 required no schema inspection, so the Demo Lab and every other
database were left untouched. All evidence in this report comes from the **repository working tree and Git index**.

### 9.3 Other prohibitions

| Prohibition | Status |
|---|---|
| Push to remote | **NOT PERFORMED** — no `git push` of any kind was issued |
| Authorise P17-0 | **NOT AUTHORISED** |
| Authorise P17-A | **NOT AUTHORISED** |
| Begin P17-0 / P17-A | **NOT BEGUN** |
| Implement Scope 2 / Scope 3 | **NOT IMPLEMENTED** |
| Reset / truncate / reseed the investor demo | **NOT PERFORMED** |
| Modify canonical corpus / oracles | **NOT PERFORMED** |
| Rewrite Git history (`reset --hard`, `clean -fd`, rebase, force-push, amend) | **NOT PERFORMED** |

---

## 10. Authorisation status

### 10.1 P17-0

**P17-0: NOT AUTHORISED.** P17-0 remains a **future discovery task**. ARCH-05 returned `P17_ARCH_FREEZE_PARTIAL` and
its PARTIAL rule explicitly forbade authorising P17-0. ARCH-06 is a reconciliation task, not an independent
verification, and **cannot** lift that gate. Completing a reconciliation has never authorised the next phase in this
project (ARCH-04 did not authorise it either). P17-0 becomes authorisable only after the ARCH-06 corrected baseline is
**independently re-verified** and the PO acts on that verdict.

Its gate has been **strengthened, not relaxed**: 10 → 12 mandatory items, each still discovery/architecture only, with
`blocks: "P17-A and every later phase"` unchanged.

### 10.2 P17-A

**P17-A: NOT AUTHORIZED.** Unchanged from every prior P17 architecture record. P17-A remains gated behind P17-0
*and* behind separately authorised implementation, and this task authorises neither. The following assertions remain
in force, unmodified:

- `p17_acceptance_matrix_20250925.json → current_verdict`: "P17-0 and P17-A are NOT authorized";
- `post_contract_po_decisions.blocks`: "P17-A is NOT authorized";
- phase plan §16.4 and §17/§18: "NOT AUTHORIZED";
- `p17_architecture_reconciliation_20250925.json → implementation_authorised: false`.

### 10.3 What happens next

1. **Independent re-verification** of the ARCH-06 corrected baseline — the required next action, performed by a party
   that is not Cline and not the ARCH-05 verifier by rote. If that returns `P17_ARCH_FREEZE_PASS`, the **Product Owner**
   decides whether to authorise P17-0.
2. **P17-0** (discovery only, 12 items) — only if separately authorised.
3. **P17-A and later phases** — remain gated until separately authorised.

---

## 11. Remaining known risks

Carried forward from ARCH-04 (R1–R13) with the updates forced by ARCH-06, plus new ARCH-06 risks.

### 11.1 Unchanged or re-stated

| Risk | Statement | Severity |
|---|---|---|
| R1 | Consultant ↔ organization linkage unimplemented (reconciled on paper only) | **High** |
| R2 | Acting-for persistence across 8 paths unimplemented; affects the idempotency-digest decision | **High** |
| R4 | Capability representation still undecided | Medium |
| R5 | Lifecycle mapping not yet produced, now including `CORRECTION REQUIRED` | Medium |
| R6 | UI inventory incomplete | **High** (planning) |
| R7 | Four factor-candidate call sites unfixed (latent cross-year candidates) | Medium |
| R8 | `roles` table empty; authority lives in `staff_roles` / `organization_members.role` | Medium |
| R9 | Thin Scope 2 factor coverage; no region-level factors | Medium |
| R10 | Disclosure/reporting disconnected (`disclosure_values` 0, `report_version_artifacts` 0) | Medium |
| R11 | Estimation-record ordering tightness for categories 7/11/12 — **now explicitly marked in the §16.2 diagram and restated in the ordering note**, but the ordering is still tight | Low–Medium |
| R13 | Categories 2/10/11/14/15 remain `NOT_IMPLEMENTED`/`DEFERRED`; acceptance is BLOCKED/DEFERRED-reportable **by design under the canonical rule** | Medium |

### 11.2 Updated by ARCH-06

| Risk | Statement | Severity |
|---|---|---|
| **R3 (updated)** | P17-0 gate is now **12** items (was 10 after ARCH-04, 6 originally); discovery effort still has not been re-estimated, and the two new items add decision work | Medium |
| **R12 (updated)** | **ARCH-06 is self-reported by Cline and is not independent verification.** ARCH-04 was independently re-verified and *still* yielded two MEDIUM findings; ARCH-06 has not been independently verified at all. This remains **Blocking** for any authorisation | **Blocking** |

### 11.3 New in ARCH-06

| Risk | Statement | Severity |
|---|---|---|
| **R14** | The corrected P17-F/P17-G acceptance wording is now correct, but its correctness depends on three gates *citing* one rule. A future edit could re-restate the vocabulary locally and reintroduce drift. Mitigated by the rule's explicit `forbidden` list and by the P17-0 item-7 acceptance-consistency check, but not structurally prevented | Medium |
| **R15** | ARCH05-06/07/08 are informational and **deliberately not fixed**: ARCH-01 still lists the superseded five-value `energy_type` vocabulary (frozen historical record), the ARCH-03 report remains untracked, and ARCH-02 §7.1 retains its annotated `EXISTS — VERIFIED` literal. A re-verifier may re-raise them; they are dispositioned as expected rather than open | Low (informational) |
| **R16** | ARCH-06 changed acceptance *wording* only. The underlying capability gaps are untouched: no Scope 2/Scope 3 capability, category or delegation behaviour was implemented, and the architecture is still a plan | **High** (inherent, not a documentation defect) |

**No new BLOCKER/CRITICAL risk was introduced by ARCH-06.** R12 remains the single blocking-class risk, and it can
only be cleared by independent re-verification.

---

## 12. Files changed

**Eight files** — six modified, two created. **All are documentation** (Markdown/JSON under `docs/architecture/`).
No source, test, migration, schema, seed, RLS, UI or configuration file was changed.

### 12.1 Modified (6)

| # | File | Nature of change |
|---|---|---|
| 1 | `docs/architecture/artifacts/p17_acceptance_matrix_20250925.json` | **Primary correction.** P17-E/F/G bullet 1 → status-conditional; P17-F bullet 5 → BLOCKED branch satisfies the gate for a `NOT_IMPLEMENTED` category; new top-level `status_conditional_acceptance_rule`; P17-0 `must_pass` 10 → 12; new `independent_verification_history` and `arch_06_corrections` blocks; `current_verdict` updated (still not PASS) |
| 2 | `docs/architecture/CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md` | §16.1 amendments A13 (P17-0 = 12 items) and A14 (canonical status-conditional rule), with A12 re-pointed; §16.2 in-diagram prerequisite marker + ordering note (ARCH05-04); new **§18 ARCH-06 corrections**; §16.4 re-baselined on the ARCH-06 corrected baseline |
| 3 | `docs/architecture/CT-PO-P17-ARCH-04-RECONCILIATION-20250925.md` | **Only §7** — historical sentence preserved verbatim, annotated as known-inaccurate and superseded by an explicit dated ARCH-06 reconciliation note (ARCH05-02) |
| 4 | `docs/architecture/artifacts/p17_arch04_reconciliation_20250925.json` | `arch_05_re_verification` block and `arch_06_addendum` recording the §7 correction; verdict not retroactively altered |
| 5 | `docs/architecture/artifacts/p17_architecture_reconciliation_20250925.json` | `reconciled_status` → `…READY_FOR_FINAL_VERIFICATION_CORRECTED_BY_ARCH_04_AND_ARCH_06`; `further_corrected_by`; new `arch_05_independent_re_verification` block; `independent_verification_note` updated; `implementation_authorised` still `false` |
| 6 | `docs/architecture/artifacts/p17_scope3_category_matrix_20250925.json` | new `status_semantics_authority` pointer so the status vocabulary has one definition (ARCH05-03). **Actionable category data unchanged; no status changed** |

### 12.2 Created (2)

| # | File | Purpose |
|---|---|---|
| 7 | `docs/architecture/CT-PO-P17-ARCH-06-RECONCILIATION-20250925.md` | This reconciliation report |
| 8 | `docs/architecture/p17_arch06_reconciliation_20250925.json` | Compact machine-readable reconciliation artifact |

### 12.3 Deliberately not changed

ARCH-01, ARCH-02, ARCH-03, ARCH-05, P16 final verification, UIUX-01, POST-ARCH decisions, PO-CAMS decision,
`.gitignore`, and all pre-existing untracked files — see §8. ARCH-06's own source report (ARCH-05) was **read only**.

---

## 13. Final verdict

```
P17_ARCH_RECONCILIATION_COMPLETE
```

### 13.1 Justification — each ARCH-05 finding actually resolved

| Finding | Resolved? | Evidence (§) |
|---|---|---|
| **ARCH05-01** — P17-F bullet 1 demanded E2E of `NOT_IMPLEMENTED` category 10 | **YES** | §3.2 — bullet 1 status-conditional; `NOT_IMPLEMENTED` → no E2E required or demandable; category-10 bullet 5 clarified; P17-G aligned |
| **ARCH05-02** — ARCH-04 §7's "no further contradiction" claim inaccurate | **YES** | §3.2/§3.3 — sentence preserved verbatim, annotated historical, superseded by an explicit dated reconciliation note |
| **ARCH05-03** — `PARTIAL` / bounded acceptance / E2E terminology tension | **YES** | §4 — canonical `status_conditional_acceptance_rule`; one definition; `PARTIAL` explicitly not upgraded; `status_semantics_authority` pointer |
| **ARCH05-04** — P17-H estimation ordering presentation tension | **YES** | §5 — in-diagram prerequisite marker + ordering note; order unchanged; R11 restated |
| **ARCH05-05** — P17-0 enumeration gaps | **YES** | §6 — items 11 (delegated-user/acting-for authorization model) and 12 (Scope2/Scope3 accounting-model consistency) added; gate **10 → 12** |
| ARCH05-06/07/08 (INFO) | **Dispositioned** | §11.3 — preserved as expected historical/observational items, deliberately not "fixed" |

Because all of ARCH05-01 … ARCH05-05 are actually resolved, and none is left in a "partially resolved" state, the
verdict is **COMPLETE** rather than **PARTIAL**.

### 13.2 What this verdict does **not** claim

- It is **not** `P17_ARCH_FREEZE_PASS`: no independent verification was performed.
- It does **not** authorise P17-0 or P17-A.
- It does **not** mean any capability, category, Scope 2 or Scope 3 behaviour exists. Nothing was implemented.
- It does **not** bind an independent verifier. A re-verifier may legitimately raise new findings; if it does, this
  verdict is superseded by that verdict.

### 13.3 Stop condition — observed

Reconciliation and a documentation-only commit. **P17-0 was not begun. P17-A was not begun. Scope 2 and Scope 3 were
not implemented. No application code was modified. Nothing was pushed.** The next action is an **independent
re-verification** of the ARCH-06 corrected baseline, after which the **Product Owner** decides.
