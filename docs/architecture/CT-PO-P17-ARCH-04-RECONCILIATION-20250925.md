# CT-PO-P17-ARCH-04 — Reconciliation of Independent ARCH-03 Findings

**Document ID:** `CT-PO-P17-ARCH-04-RECONCILIATION-20250925`
**Task ID:** `P17-ARCH-04-20260925-RECONCILE-INDEPENDENT-FINDINGS`
**Date:** 2025-09-25
**Type:** Architecture / acceptance-contract reconciliation — **documentation only, no product implementation**
**Baseline commit:** `906e66c4e2fa8ca02b006c71437bb988c4f53a48` (ARCH-02)
**Independent source verdict:** `P17_ARCH_FREEZE_PARTIAL`

> This document reconciles the seven findings raised by the independent ARCH-03 verification. It **supersedes nothing**
> in ARCH-01 or ARCH-02: ARCH-01 remains the historical contract, ARCH-02 remains the reconciled baseline, and
> ARCH-04 is the dated correction layer. **No P17 implementation is authorised by this document.**

---

## 1. Task Identity

| Item | Value |
|---|---|
| Task ID | `P17-ARCH-04-20260925-RECONCILE-INDEPENDENT-FINDINGS` |
| Date | 2026-09-25 (PR); 2025-09-25 (document date in the ARCH series) |
| Role | Architecture reconciliation implementer — **not** the independent verifier |
| Scope | Reconcile documented architecture/acceptance defects identified by ARCH-03 |
| Implementation performed | **NO** |
| Migrations created | **NO** |
| Production contacted | **NO** |
| P17-0 executed | **NO** |
| P17-A authorised | **NO** |

---

## 2. Baseline Verification

Commands run before any modification:

| Check | Expected | Observed | Result |
|---|---|---|---|
| branch | `p8-release-reconciled` | `p8-release-reconciled` | PASS |
| HEAD | `906e66c4e2fa8ca02b006c71437bb988c4f53a48` | `906e66c4e2fa8ca02b006c71437bb988c4f53a48` | PASS |
| ARCH-02 is current baseline | yes | `git log -5`: HEAD = `docs(p17): reconcile unified cams architecture contract`; preceding commits are governance preservation and ARCH-01 | PASS |
| no post-ARCH-02 implementation commit | yes | HEAD == ARCH-02; nothing after it | PASS |
| unrelated working-tree changes preserved | yes | ` M .gitignore` (pre-existing) + 17 untracked pre-existing files (`docs/ChatGPT/*`, `CT-PO-P12-*`, `CT-PO-P14-*`, Insight docs, `8`, `=`, `.costrict/`, plus the ARCH-03 report and `CT-PO-MASTER-WORKPLAN`) | PASS — none staged, none deleted |

No reset, rebase, clean, stash or checkout was performed. No repository state was "repaired".

---

## 3. ARCH-03 Source Verification

| Item | Value |
|---|---|
| Report path (as named in the task) | `CO-STRING-P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE.md` |
| Actual repository path | `docs/architecture/CO-STRING-P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE.md` (found at the first `find`; 36,206 bytes; untracked) |
| Status | **PRESENT — read directly from the repository**, not reconstructed |
| Verdict | `P17_ARCH_FREEZE_PARTIAL` |
| Independence | The verifier states it treated Cline's ARCH-02 as evidence to verify, not as acceptance, and re-derived material claims from the repository + read-only local Demo Lab |
| Author of ARCH-03 | CoStrict (independent verifier) — **not** Cline |
| Modified by this task | **NO** — ARCH-03 remains untouched |

**Verifier assertions independently reproduced by ARCH-04** (read-only): `consultant_profiles` has no `organization_id`;
`organizations` has no `organization_type`; no `organization_relationship` table; `consultant_clients.consultant_id` →
`consultant_profiles(id)`; `customer_documents` / `suppliers` / `review_audit_trail` / `review_assignment_history` /
`report_versions` carry actor but no acting-for organisation. All confirmed.

---

## 4. Findings Inventory

| ID | Severity | Finding | ARCH-04 disposition |
|---|---|---|---|
| HIGH-01 | HIGH | Consultant organization identity classified `EXISTS — VERIFIED` but unsupported by the schema | **RECONCILED** — reclassified to `PARTIAL — MISSING LINKAGE`; carried into P17-0 |
| MEDIUM-01 | MEDIUM | Acting-for propagation narrower than `AC-AUDIT-01` requires | **RECONCILED** — propagation extended to 8 paths with per-path (A)/(B) disposition |
| MEDIUM-02 | MEDIUM | P17-E gate contradicted category 2 = `NOT_IMPLEMENTED` | **RECONCILED** — status-conditional acceptance language; same vocabulary applied to F/G |
| LOW-01 | LOW | `organization_id` vs `claimant_organization_id` naming | **RECONCILED** — canonical conceptual name + explicit physical mapping |
| LOW-02 | LOW | `energy_type` 5 values vs 4 values | **RECONCILED** — authoritative 4-value Scope 2 vocabulary |
| LOW-03 | LOW | Stale `post_contract_po_decisions` metadata | **RECONCILED** — fields corrected with a historical note |
| LOW-04 | LOW | Claim of per-category customer/UIUX fields not present in the matrix | **RECONCILED** — claim narrowed; requirements defined once as cross-cutting |
| **EXTRA-01** | LOW (ARCH-03 §11 residual) | `CORRECTION REQUIRED` state not explicitly named | **RECONCILED as a P17-0 obligation** (documented, not implemented) |
| **EXTRA-02** | LOW (ARCH-03 §21 nuance) | Estimation-record ordering tightness for categories 7/11/12 | **DOCUMENTED as risk R11** — no ordering change |

---

## 5. HIGH-01 Reconciliation — consultant organization identity

**ARCH-03 finding.** ARCH-02 §7.1 classified "Consultant organization identity" as `EXISTS — VERIFIED` via
`consultant_profiles` + `consultant_firm_members`. The verifier found this unsupported: `consultant_profiles` is keyed by
`user_id`, has no `organization_id` and no FK to `organizations`; `consultant_clients.consultant_id` references
`consultant_profiles(id)`; `organizations` has no `organization_type`; no `organization_relationship` table exists; the
Demo Lab consultant profile has no matching organization.

**ARCH-04 independent reproduction (read-only `information_schema`):**

| Assertion | Observed |
|---|---|
| `consultant_profiles` columns | `id, user_id, company_name, company_number, …, firm_type, firm_size, …, white_label_enabled` — **no `organization_id`** |
| `organizations.organization_type` | **0 columns** (does not exist) |
| `organization_relationship` table | **0 rows in `information_schema.tables`** (does not exist) |
| `consultant_clients` FKs | → `consultant_profiles.id` (consultant_id) and → `organizations.id` (organization_id) |

**Verdict: the finding is CORRECT.** ARCH-02 over-claimed.

**Correction applied.**

| Before | After |
|---|---|
| Classification: `EXISTS — VERIFIED` | **`PARTIAL — MISSING LINKAGE`** |
| Evidence: "consultant_profiles (1), consultant_firm_members (2)" | Evidence: `consultant_profiles` keyed by `user_id` with **no `organization_id`**; no FK to `organizations`; `consultant_clients.consultant_id` → `consultant_profiles(id)`; no `organization_type`; no `organization_relationship` table; `consultant_firm_members` links **users** to a profile, not an organization |
| Implementation dependency register | "consultant ↔ organization identity/linkage decision" **added** |

**What is NOT changed (PO decision preserved).** The intended product architecture is untouched:

* a consultant organization **is** a first-class independent CarbonTally organization;
* a consultant client **is** a separate independent organization;
* the consultant-to-client relationship is explicit (`consultant_clients`);
* a consultant can have its **own** accounting;
* the client owns its own accounting;
* delegated consultant access remains **client-specific**.

The correction is that **the current repository does not yet implement the identity linkage** that this model requires.

**Not implemented (prohibited by this task).** No `organization_id` column was added to `consultant_profiles`; no
`organization_type` was created; no `organization_relationship` table was created; no consultant organization table was
created. Only the gap is documented and carried into P17-0.

---

## 6. MEDIUM-01 Reconciliation — acting-for propagation

**ARCH-03 finding.** Schema delta §10.3 enumerated acting-for/actor-organization context only on
`calculation_snapshots`, `emissions_logs`, `evidence_line_items` and the audit writer, but `AC-AUDIT-01` requires audit
context for **every** material accounting change; the verifier named source/activity documents, report artefacts,
supplier operations and review/approval decisions.

**ARCH-04 independent reproduction (read-only):**

| Object | Owner present | Actor present | Acting-for org |
|---|---|---|---|
| `customer_documents` | `organization_id` | `uploaded_by`, `updated_by`, `organization_member_id`, `classification_by` | **absent** |
| `report_versions` | via `report_id` | `created_by` | **absent** |
| `suppliers` | `organization_id` | `created_by`, `updated_by` | **absent** |
| `review_audit_trail` | via `review_id` | `performed_by`, `performed_by_email`, `assigned_to` | **absent** |
| `review_assignment_history` | via `review_id` | `assigned_by`, `assigned_to` | **absent** |

**Verdict: the finding is CORRECT.**

**Correction applied.** Schema delta §10.3 now carries a **per-path disposition** covering eight paths. For each path the
architecture answers the required question explicitly:

* **(A) persist** — `calculation_snapshots`, `emissions_logs`, `evidence_line_items`, audit writer, **and all four
  additional paths** (`customer_documents`, `suppliers`, review/approval records, report artefacts).
* **(B) derive** — permitted **only** where the audit writer persists `actor_organization_id` +
  `acting_for_organization_id` **and** a reliable object→audit-record linkage exists.

**No derivation rule was invented.** Deriving the acting-for organisation from `uploaded_by`/`created_by` → the user's
organisation *at read time* is explicitly **rejected** as a (B) rule, because membership and consultancy relationships
change after the fact and the derivation would therefore not be audit-safe. Where (B) is unavailable the path is
classified **"additive implementation required"** in the phase that owns that surface (P17-B/C/E/F/G for data paths,
P17-H for review/approval, P17-I for report artefacts).

**Governing rule preserved.** `ACTING FOR` remains **context, not an authorization boundary** (POST-ARCH §35;
UIUX-01 §6, §44).

**Not implemented.** No column added; no database change; no audit-writer change.

---

## 7. MEDIUM-02 Reconciliation — P17-E acceptance contradiction

**ARCH-03 finding.** The P17-E gate required *"one END-TO-END VERIFIED result per category (1,2,3,4,5) in Demo Lab"*
with **no deferral caveat**, while category 2 (Capital Goods) is `NOT_IMPLEMENTED` in the Scope 3 matrix
(`status_rollup`) and ARCH-02 §11.1, and its methodology remains a PO decision. P17-F/P17-G already carried "where the
category is not DEFERRED" language; P17-E did not. This contradicted the architecture's own deferred-scope rule and
phase plan §7, which requires `NOT_IMPLEMENTED` categories to be reported as blocked.

**ARCH-04 verification (read from the acceptance matrix):** confirmed — P17-E had 4 bullets with no caveat; P17-F had 4
bullets including "where the category is not DEFERRED" and a category-10 BLOCKED clause; P17-G had 3 bullets including
"where the category is not DEFERRED" and "recorded as DEFERRED".

**Verdict: the finding is CORRECT.**

**Correction applied (minimum change, no category promotion).** P17-E's acceptance language is now status-conditional:

1. one END-TO-END VERIFIED result for each category among (1,2,3,4,5) **whose authoritative architecture status is
   `SUPPORTED` or `PARTIAL`**;
2. each category whose status is `NOT_IMPLEMENTED` or `DEFERRED` is reported as an **explicit BLOCKED/DEFERRED outcome
   with its blocking prerequisite named** — never omitted and never counted as delivered;
3. an explicit **status vocabulary** applied per category: `SUPPORTED` → E2E verification required; `PARTIAL` →
   applicable bounded acceptance for the supported portion; `NOT_IMPLEMENTED` → documented BLOCKED outcome naming the
   missing methodology/input contract; `DEFERRED` → documented DEFERRED outcome naming the blocking PO decision;
   PO-methodology-decision-required → remains outside implementation authorisation;
4. the three substantive P17-E bullets (category-3 derivation uniqueness, category-5 fail-closed path, DC-03 detector)
   are unchanged.

The **same status-vocabulary bullet** was added to P17-F and P17-G so the three Scope 3 gates cannot drift apart again.
Bullet counts: P17-E 4 → 6; P17-F 4 → 5; P17-G 3 → 4.

**Not done.** Category 2 was **not** changed to `SUPPORTED`; no Category 2 methodology was invented; Category 2 was
**not** implemented; no other category status was altered.

> **⚠ HISTORICAL STATEMENT — PRESERVED, KNOWN INACCURATE (annotated by ARCH-06, 2025-09-25).** The paragraph below was
> written by ARCH-04 and is retained **verbatim** for the audit trail. It is **inaccurate**: the re-check covered other
> gates but did **not** check P17-F's own bullet 1 against its own `NOT_IMPLEMENTED` category 10, so a further
> contradiction of this class **did** exist. It is superseded by the "ARCH-06 reconciliation note" immediately below it.

**Elsewhere in the acceptance matrix.** The remaining gates were re-checked for the same class of contradiction:
P17-A…P17-D, P17-H, P17-I, P17-J contain no category-status assertions, so no further contradiction of this class
exists. (P17-D's "every new Scope 3 result MUST carry a category" plus "the 25 historical rows are untouched" is
consistent, not contradictory.)

**ARCH-06 reconciliation note (2025-09-25) — this statement is SUPERSEDED.** Independently identified by
`P17-ARCH-05` as finding **ARCH05-02**. The claim directly above was incorrect in one respect: **P17-F bullet 1** read
*"one END-TO-END VERIFIED result per category (6,7,8,9,10) where the category is not DEFERRED"*. Category 10 is
**`NOT_IMPLEMENTED`**, not `DEFERRED`, so that bullet still demanded an implementation E2E result of a
non-implemented category — **exactly the contradiction class this section claimed no longer existed** (ARCH-03
MEDIUM-02, re-raised as ARCH05-01). ARCH-06 has now made P17-F bullet 1 status-conditional, aligned P17-G bullet 1,
and added the canonical `status_conditional_acceptance_rule` so that P17-E/F/G share a single rule rather than three
similar ones. The paragraph above is retained as historical and is **superseded** by this note.
See `docs/architecture/CT-PO-P17-ARCH-06-RECONCILIATION-20250925.md` §3 (ARCH05-01/ARCH05-02).

---

## 8. LOW-01 Reconciliation — tenant-key naming

**ARCH-03 finding.** The tenant key is named `organization_id` in schema delta §3.1 but `claimant_organization_id` in
the Scope 2 domain matrix and in double-counting control DC-09.

**Verdict: the inconsistency is real, and the longer name carries the more precise semantics** — it disambiguates the
instrument's **claim owner** from (a) the allocation's organisation and (b) the client organisation.

**Correction applied.** One authoritative semantic name, with an explicit conceptual-vs-physical distinction:

| Concept (architecture) | Physical name (proposed) | Rule |
|---|---|---|
| Claim owner (`claimant_organization_id`) | `contractual_instruments.organization_id` | one-to-one; the conceptual name is used where precision matters, the physical column keeps the uniform P17 tenant key so the table follows the established RLS convention |
| Allocation recipient | `instrument_allocations.organization_id` | must equal the parent instrument's `organization_id` |
| Accounting owner | `organization_id` on every P17 accounting object | unchanged — ownership |

Documented in schema delta **§10.6 (Canonical terminology)**, referenced from schema delta §3.1 and from the Scope 2
domain matrix. **No physical column was renamed**, and no existing database column was touched (this task is
documentation-only).

---

## 9. LOW-02 Reconciliation — `energy_type` vocabulary

**ARCH-03 finding.** Schema delta §2.1 / ARCH-02 §10.2 listed **five** `energy_type` values
(`electricity, heat, steam, cooling, fuel`) while the Scope 2 domain matrix listed **four** (no `fuel`).

**Verdict: the inconsistency is real.** `fuel` is not a Scope 2 energy type — Scope 2 is *purchased energy*, and
fuel-borne energy is a Scope 1 (combustion) or Scope 3 (upstream/other) activity identified by the activity and factor.

**Correction applied.** One authoritative vocabulary: **`electricity | heat | steam | cooling`**.

* Schema delta §2.1's proposed `CHECK` is now
  `CHECK (energy_type IS NULL OR energy_type IN ('electricity','heat','steam','cooling'))`, with an explicit statement
  that `fuel` is excluded and that a Scope 1/Scope 3 row carries `energy_type = NULL`.
* ARCH-02 §10.2 was annotated to the four-value vocabulary.
* The Scope 2 domain matrix's `energy_type` entry now states the authoritative vocabulary and the `fuel` exclusion.

**Not done.** No code or schema change; no accounting methodology invented. `cooling` continues to resolve to a
fail-closed review state because the factor library has zero cooling factors.

---

## 10. LOW-03 Reconciliation — stale reconciliation metadata

**ARCH-03 finding.** The acceptance JSON's `post_contract_po_decisions` still read
`status: APPROVED_PO_DECISIONS_REQUIRING_RECONCILIATION` with `reconciliation_performed: false` and a `blocks` string
claiming every phase was blocked until the register was completed — contradicting `reconciliation_arch02` and
`current_verdict` **in the same file**.

**Verdict: the metadata was stale.**

**Correction applied.** The block now records the true state:

| Field | New value |
|---|---|
| `status` | `RECONCILED_BY_ARCH_02_WITH_ARCH_04_CORRECTIONS` |
| `reconciliation_performed` | `true` (with `reconciled_by` + `reconciliation_authority`) |
| `independent_verification` | ARCH-03 verifier, verdict `P17_ARCH_FREEZE_PARTIAL`, report path, all seven findings listed |
| `arch_04_corrections` | task id + report + artifact + `status: COMPLETE` |
| `blocks` | *"P17-0 and every later P17 implementation phase remain blocked until the ARCH-04 corrected architecture is INDEPENDENTLY RE-VERIFIED and frozen. P17-A is NOT authorized. PO decisions and ARCH-03 findings are reconciled; the outstanding condition is independent verification, not reconciliation."* |
| `historical_note` | records the previous stale values and why they were replaced |

The file-level `current_verdict` was replaced with
`RECONCILED_BY_ARCH_02, CORRECTED_BY_ARCH_04, AWAITING_INDEPENDENT_RE_VERIFICATION`.

**Not done.** The overall architecture verdict was **not** changed to PASS; no implementation status was upgraded.

---

## 11. LOW-04 Reconciliation — Scope 3 per-category customer/UIUX representation

**ARCH-03 finding.** ARCH-02 §11.3 claimed the per-category baseline "retains … **customer contribution** · **UI/UX
requirements**", but the Scope 3 matrix carries neither as a per-category field — only a global reconciliation note.

**ARCH-04 verification:** the per-category key set is
`accepted_activity_types, architecture_status, business_meaning, category, e2e_acceptance_scenario,
evidence_requirements, existing_factor_families, expected_output, factor_requirements, factor_year_requirements,
geography_requirements, manual_review_triggers, methodologies, minimum_input_data, name, prerequisite_work,
reporting_dimensions, slug, supplier_requirements, tenant_security_considerations` — **no** `customer_contribution` and
**no** `uiux_requirements`. **Verdict: the claim was over-broad.**

**Decision: option A — narrow the claim** (the global requirement is sufficient) rather than add 15 × 2 duplicated
fields. This is the minimum architecture change that preserves the acceptance meaning.

**Correction applied.**

* The Scope 3 matrix gained a top-level **`cross_cutting_requirements`** block defining, once: (i)
  `customer_and_consultant_contribution` with its invariants and acceptance criteria (`AC-CUST-01/02/03`,
  `AC-ORGCTX-01`, `AC-AUDIT-01`) and (ii) `uiux` with its invariants and acceptance criteria (`AC-S3CAT-01`,
  `AC-UIUX-01`), plus an explicit `explicitly_not_per_category_fields` list.
* ARCH-02 §11.3 was annotated: the sentence now reads as "the baseline retains these requirements **for every category,
  as cross-cutting requirements**" and explicitly disclaims per-category fields.
* No per-category field was added; no duplication introduced; the acceptance meaning is preserved.

---

## 12. P17-0 Impact

P17-0 remains a **future discovery task and was NOT executed here**. Its mandate is extended with four mandatory items
(recorded in the acceptance matrix `reconciliation_arch02.new_phase_gate.must_pass`, now 10 items, and in phase plan
§16.1 A10–A12):

| # | New P17-0 obligation | Source |
|---|---|---|
| 1 | **Consultant ↔ organization identity/linkage decision** — determine the authoritative organization identity model for (a) the consultant firm's own organization, (b) consultant users/members, (c) the consultant's client organizations, (d) the consultant-client relationship, (e) the consultant's own Scope 1/2/3 ownership, (f) client-owned Scope 1/2/3 ownership; state whether existing structures can be extended or additive organization linkage is required. **No implementation.** | ARCH-03 HIGH-01 |
| 2 | **Acting-for propagation map** across source/activity documents, suppliers, review/approval, reports/report artefacts, calculations, evidence and the audit trail, recording for each: owner · actor · actor organization · acting-for organization · persisted? · safely derivable? · additive implementation required? | ARCH-03 MEDIUM-01 |
| 3 | **Acceptance consistency check** — verify phase acceptance criteria are internally consistent with category status, deferred scope, PO methodology decisions and E2E requirements. | ARCH-03 MEDIUM-02 |
| 4 | **Lifecycle `CORRECTION REQUIRED`** — the mapping table must explicitly name the state, or document its existing rework-edge representation. | ARCH-03 §11 residual |

**Not authorised by this task:** P17-0 execution, P17-0 code, P17-0 migrations.

---

## 13. Acceptance-Matrix Impact

| Change | Detail |
|---|---|
| P17-0 gate `must_pass` | 6 → **10** items (the four ARCH-04 obligations above) |
| P17-E gate | status-conditional acceptance + explicit per-category status vocabulary (4 → 6 bullets) |
| P17-F gate | same status-vocabulary bullet added (4 → 5 bullets) |
| P17-G gate | same status-vocabulary bullet added (3 → 4 bullets) |
| `post_contract_po_decisions` | stale fields corrected with a historical note (LOW-03) |
| `current_verdict` | replaced with the ARCH-02/ARCH-03/ARCH-04 state (LOW-03) |
| **Unchanged** | all ten phase gates P17-A…P17-J **identities**, the 12 invariant tests `T-INV-01…12`, the 11 controls `DC-01…11`, the 12 ARCH-02 criteria `AC-*`, the END-TO-END VERIFIED rule, the P16 reportability-reuse requirement |

---

## 14. Phase-Plan Impact

`CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md`:

* **§16.1 amendments A10, A11, A12 added** — consultant organization linkage is an open gap (not a satisfied
  capability); acting-for propagation is per-path and broader than ARCH-02 stated; P17-E/F/G acceptance is
  status-conditional.
* **§17 (new) "ARCH-04 corrections"** — a finding-by-finding table of the effect on the plan, plus the recorded
  ordering nuance and the gate state.
* **Unchanged:** the phase order A→B/C→D→E/F/G→H→I→J; the P17-0-blocks-P17-A rule; UI/UX in-phase for B…I; the migration
  slots `20261010000000`…`20261014000000` (proposals only); the no-backend-only-PASS rule.
* **Ordering nuance recorded, not changed** (risk R11): estimation records live in the P17-H migration but categories
  7/11/12 are attempted in P17-F/G, so the dependency is tight. §7 already states the prerequisite; ARCH-04 records it
  as a risk rather than re-sequencing the plan.

---

## 15. Schema-Delta Impact

`artifacts/p17_schema_delta_20250925.md`:

| Section | Change |
|---|---|
| §2.1 | `energy_type` `CHECK` reduced to the **4-value** authoritative Scope 2 vocabulary; `fuel` excluded with rationale (LOW-02) |
| §3.1 | `contractual_instruments.organization_id` now states the **conceptual/physical naming mapping** to `claimant_organization_id` (LOW-01) |
| §10.1 | consultant organization identity row **reclassified** `EXISTS — REUSE` → **`PARTIAL — MISSING LINKAGE`** with full evidence; a separate `consultant firm membership` row retained as `EXISTS — VERIFIED` (HIGH-01) |
| §10.3 | acting-for propagation **expanded from 4 paths to 8** with a per-path (A)/(B) disposition, the permitted option-B condition, and the explanation of why actor→organisation derivation is rejected as not audit-safe (MEDIUM-01) |
| §10.6 (new) | **Canonical terminology** glossary for the claimant/recipient/owner organisation names (LOW-01) |
| **Unchanged** | the four new entities (`contractual_instruments`, `instrument_allocations`, `scope3_categories`, `estimation_records`); the `NOT VALID` constraint discipline; the no-backfill rule; the RLS/privilege convention; the migration slots; **no migration created** |

---

## 16. Historical-Record Preservation

| Document | Status |
|---|---|
| `CT-PO-P17-ARCH-01-…-20250925.md` | **byte-identical — NOT modified** (verified by `git diff --quiet`) |
| `CO-STRING-P17-ARCH-03-…-INDEPENDENT-VERIFICATION-FREEZE.md` | **NOT modified** (independent evidence; preserved, not staged by this task) |
| `CT-PO-P16-FINAL-VERIFICATION-20250925.md` | **NOT modified** (verified by `git diff --quiet`) |
| `CT-PO-P17-UIUX-01`, `CT-PO-P17-POST-ARCH-DECISIONS`, PO-CAMS decision | **NOT modified** |
| `CT-PO-P17-ARCH-02-RECONCILIATION-20250925.md` | **original content preserved**; ARCH-04 added four clearly-marked inline `⚠ CORRECTED/EXTENDED/NARROWED BY ARCH-04` pointers and a dated **ARCH-04 ADDENDUM** section (A4.1–A4.4) with the before/after classification. No ARCH-02 claim was silently rewritten. |

The correction pattern is deliberate: **annotate + addendum**, never retro-edit. A reader can see exactly what ARCH-02
claimed, what ARCH-03 found, and what ARCH-04 decided.

---

## 17. Files Changed

| File | Change |
|---|---|
| `docs/architecture/CT-PO-P17-ARCH-04-RECONCILIATION-20250925.md` | **NEW** — this report (22 sections) |
| `docs/architecture/artifacts/p17_arch04_reconciliation_20250925.json` | **NEW** — machine-readable reconciliation artifact |
| `docs/architecture/CT-PO-P17-ARCH-02-RECONCILIATION-20250925.md` | 4 inline correction pointers + ARCH-04 addendum (A4.1–A4.4) |
| `docs/architecture/CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md` | §16.1 A10–A12 + new §17 |
| `docs/architecture/artifacts/p17_acceptance_matrix_20250925.json` | P17-0 gate +4 items; P17-E/F/G status-conditional acceptance; `post_contract_po_decisions` corrected; `current_verdict` replaced |
| `docs/architecture/artifacts/p17_architecture_reconciliation_20250925.json` | HIGH-01 reclassification; MEDIUM-01 disposition; `arch_03_independent_verification` block; `reconciled_status` + `implementation_dependencies` updated |
| `docs/architecture/artifacts/p17_schema_delta_20250925.md` | §2.1 vocabulary; §3.1 naming; §10.1 reclassification; §10.3 propagation; §10.6 new |
| `docs/architecture/artifacts/p17_scope2_domain_matrix_20250925.json` | `energy_type` authoritative vocabulary; `claimant_organization_id` naming mapping |
| `docs/architecture/artifacts/p17_scope3_category_matrix_20250925.json` | new `cross_cutting_requirements` block |

---

## 18. Files Intentionally Not Changed

| File | Reason |
|---|---|
| `docs/architecture/CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md` | preserved historical contract — must remain byte-identical |
| `docs/architecture/CO-STRING-P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE.md` | independent evidence — read only, never modified |
| `docs/architecture/CT-PO-P16-FINAL-VERIFICATION-20250925.md` | P16 acceptance record — untouched |
| `CT-PO-P17-UIUX-01`, `CT-PO-P17-POST-ARCH-DECISIONS-20260925`, `CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` | PO/UIUX governance — untouched |
| `.gitignore` | pre-existing modification, unrelated to this task — **not staged** |
| 17 pre-existing untracked files (`docs/ChatGPT/*`, `CT-PO-P12-*`, `CT-PO-P14-*`, Insight docs, `.costrict/`, `8`, `=`, `costrict-p3-…txt`, `CT-PO-MASTER-WORKPLAN`, the ARCH-03 report) | unrelated/pre-existing — **not staged, not deleted** |
| **all application source** (`backend/**`, `frontend/**`, `admin/**`, `src/**`) | prohibited |
| **all tests and fixtures** | prohibited |
| **`supabase/migrations/**`** | prohibited — and **no P17 migration exists** (latest remains `20261009000000_p16r7_calculation_request_idempotency.sql`) |
| **RLS policies / database objects / seed data** | prohibited |

---

## 19. Tests / Verification Performed

No product test suite was run (this is a documentation-only task; running the suite merely for appearance was
explicitly not required). The following validations **were** performed:

| # | Validation | Result |
|---|---|---|
| 1 | JSON parse validation of all four architecture artifacts | **PASS** |
| 2 | `consultant_profiles` has no `organization_id`; `organization_type` absent; `organization_relationship` absent; `consultant_clients` FK targets — read-only `information_schema` | **PASS** (reproduced ARCH-03) |
| 3 | Column inspection of `customer_documents`, `suppliers`, `review_audit_trail`, `review_assignment_history`, `report_versions` for acting-for | **PASS** (reproduced ARCH-03) |
| 4 | Acceptance-matrix gate comparison: P17-E vs P17-F/G language | **PASS** (contradiction confirmed) |
| 5 | Stale-classification search for `APPROVED_PO_DECISIONS_REQUIRING_RECONCILIATION` / `reconciliation_performed: false` | **PASS** (found and corrected) |
| 6 | `claimant_organization_id` vs `organization_id` search across artifacts | **PASS** (both found; mapping documented) |
| 7 | Scope 3 per-category key-set inspection for `customer_contribution` / `uiux_requirements` | **PASS** (absent; claim narrowed) |
| 8 | ARCH-01 unchanged (`git diff --quiet`) | **PASS** |
| 9 | P16 final verification unchanged (`git diff --quiet`) | **PASS** |
| 10 | Governance docs unchanged (`git diff --quiet` × 3) | **PASS** |
| 11 | No P17 migration exists (latest = `20261009000000`) | **PASS** |
| 12 | No application/test/migration file modified | **PASS** |
| 13 | ARCH-03 report unchanged | **PASS** |

---

## 20. Production Safety

> **No production system was contacted or modified.**

No production connection, `SELECT`, DDL, DML, migration, deployment, credential use, data export or data copy. All
inspection was **read-only** against the local Demo Lab container (`supabase_db_carbon_ledger`,
`carbontally_demo_local` @ `127.0.0.1:54426`) and the local working tree. No seed or demo-data mutation. No destructive
command. The integration harness (which truncates its target — invariant F-046-1) was **not** run.

---

## 21. Remaining Risks

| # | Risk | Impact | Action |
|---|---|---|---|
| R1 | **Consultant ↔ organization linkage is unimplemented** (HIGH-01 reconciled on paper only). | High if unresolved: a consultant's own accounting cannot be recorded under a verified organization. | P17-0 decision; additive implementation later |
| R2 | **Acting-for persistence across 8 paths is unimplemented**; additive work in 5 phases and it affects the idempotency-digest decision. | High: touches audit + calculation write paths. | P17-0 map; per-phase implementation |
| R3 | **P17-0 gate is now 10 items** — discovery scope has grown with each verification cycle. | Medium (planning): P17-0 effort is not re-estimated. | Re-estimate at P17-0 authorisation |
| R4 | **Capability representation still undecided** (ARCH-02 R1). | Medium. | P17-0 decision |
| R5 | **Lifecycle mapping not yet produced**, now also required to name `CORRECTION REQUIRED`. | Medium. | P17-0 deliverable |
| R6 | **UI inventory incomplete** (ARCH-02 R4). | High (planning). | P17-0 §54/§55/§56 matrices |
| R7 | **Four factor-candidate call sites unfixed** (latent). | Medium. | P17-A remediation |
| R8 | **`roles` table empty**; authority lives in `staff_roles` / `organization_members.role`. | Medium. | P17-0 |
| R9 | **Thin Scope 2 factor coverage**; region-level factors absent. | Medium. | Expect fail-closed review outcomes; do not fabricate factors |
| R10 | **Disclosure/reporting disconnected** (`disclosure_values` = 0, `report_version_artifacts` = 0). | Medium. | P17-I real-artefact gate |
| R11 | **Estimation-record ordering tightness** for categories 7/11/12 (ARCH-03 §21 nuance; not a defect). | Low-Medium. | Documented; revisit at P17-0 |
| R12 | **ARCH-04 is self-reported by Cline and is not independent verification.** | Blocking: implementation authorisation. | Independent re-verification required |
| R13 | **Categories 2/10/11/14/15 remain NOT_IMPLEMENTED/DEFERRED**; acceptance is now BLOCKED/DEFERRED-reportable rather than deliverable. | Medium (coverage expectations). | PO methodology decisions |

---

## 22. Exact Verdict

**`P17_ARCH_RECONCILIATION_COMPLETE`**

Justification against the task's COMPLETE criteria:

| Criterion | Status |
|---|---|
| HIGH-01 correctly reclassified and carried into P17-0 | **YES** — `EXISTS — VERIFIED` → `PARTIAL — MISSING LINKAGE`; added to the P17-0 `must_pass` list and the dependency register |
| MEDIUM-01 reconciled | **YES** — 8-path propagation with per-path (A)/(B) disposition; no derivation rule invented; governing rule preserved |
| MEDIUM-02 reconciled | **YES** — P17-E/F/G acceptance is status-conditional; no category status changed |
| LOW-01…LOW-04 reconciled or explicitly classified | **YES** — all four reconciled |
| Affected artifacts internally consistent | **YES** — all four JSONs parse; cross-document statements aligned |
| P17-0 requirements updated | **YES** — four new mandatory obligations |
| No implementation occurred | **YES** |
| ARCH-01 and ARCH-03 untouched | **YES** |
| No production contacted | **YES** |

**This is NOT `P17_ARCH_FREEZE_PASS` and NOT `P17_ARCH_RECONCILIATION_FAIL`.** It is a reconciliation-completeness
statement, not acceptance. **Cline reconciliation is not independent acceptance.**

**Gate state:** **P17-0 NOT executed and NOT authorised by this task. P17-A NOT AUTHORIZED.** The next required action
is **independent re-verification of the ARCH-04 corrected baseline**, followed — only if that verification passes — by
a PO authorisation decision for P17-0.

---

## Document Control

**Document:** `CT-PO-P17-ARCH-04-RECONCILIATION-20250925`
**Task:** `P17-ARCH-04-20260925-RECONCILE-INDEPENDENT-FINDINGS`
**Baseline commit:** `906e66c4e2fa8ca02b006c71437bb988c4f53a48`
**Source verdict:** `P17_ARCH_FREEZE_PARTIAL` (ARCH-03, independent)
**Verdict:** `P17_ARCH_RECONCILIATION_COMPLETE`
**Implementation performed:** NO · **Migrations created:** NONE · **Production:** NOT CONTACTED
**P17-0:** not executed, not authorised · **P17-A:** NOT AUTHORIZED
**Independent re-verification required:** YES






