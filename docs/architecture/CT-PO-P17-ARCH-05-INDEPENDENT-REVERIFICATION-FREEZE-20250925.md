# P17 Architecture Independent Re-Verification and Freeze

**Document ID:** `CT-PO-P17-ARCH-05-INDEPENDENT-REVERIFICATION-FREEZE`
**Task ID:** `P17-ARCH-05-20260925-INDEPENDENT-REVERIFICATION-FREEZE`
**Type:** Independent, adversarial, read-only architecture re-verification
**Date:** 2026-09-25

---

## EXECUTIVE SUMMARY

| Item | Value |
|---|---|
| ARCH-03 | `P17_ARCH_FREEZE_PARTIAL` |
| ARCH-04 | `P17_ARCH_RECONCILIATION_COMPLETE` |
| **ARCH-05 (this independent verdict)** | **`P17_ARCH_FREEZE_PARTIAL`** |
| Implementation | **NOT PERFORMED** |
| Production | **NOT CONTACTED** |
| P17-0 | **NOT AUTHORIZED BY THIS VERIFICATION** |
| P17-A | **NOT AUTHORIZED** |
| Independence | **COMPLETED** |

**Single most important reason:** HIGH-01, MEDIUM-01, LOW-01…LOW-04, EXTRA-01 and EXTRA-02 are
each **semantically** reconciled (verified against the underlying artifacts and the local read-only
schema), but **MEDIUM-02 is only partially reconciled**: P17-E was made status-conditional, yet the
**P17-F gate still requires "one END-TO-END VERIFIED result per category (6,7,8,9,10) where the
category is not DEFERRED"**, while category 10 (`Processing of Sold Products`) is
`NOT_IMPLEMENTED`. That is the exact contradiction class ARCH-03 raised, left unfixed in a second
gate — and ARCH-04 §7 explicitly claims "no further contradiction of this class exists", which is
inaccurate. This is a material (non-blocking) finding, so the architecture may proceed to correction
but **P17-0 is not authorized by this task**.

---

## 1. Task Identity

| Item | Value |
|---|---|
| Task ID | `P17-ARCH-05-20260925-INDEPENDENT-REVERIFICATION-FREEZE` |
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` (verified) |
| ARCH-02 baseline / ARCH-04 parent | `906e66c4e2fa8ca02b006c71437bb988c4f53a48` (verified) |
| ARCH-04 commit under test | `172bdd26d1d2fd2c7bf03a05a40532b662117729` (verified as HEAD) |
| ARCH-03 (control specification) | `docs/architecture/CO-STRING-P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE.md` |
| ARCH-04 (claim under test) | `docs/architecture/CT-PO-P17-ARCH-04-RECONCILIATION-20250925.md` |
| Verification timestamp (UTC) | 2026-09-25T09:14:59Z (start) → 2026-09-25T09:17:47Z (tooling snapshot) |
| Verifier role | Independent re-verifier — **not** the author of ARCH-02/ARCH-04 |
| Independence | ARCH-04 was treated as **evidence to verify**, not as acceptance; every material claim was re-derived from the repository and a read-only local Demo Lab |

Tool versions observed: `git 2.53.0`, `python 3.14.4`, `node v24.21.0`, `docker 29.1.3`,
`docker compose 2.40.3`, `psql 18.6`.

---

## 2. Independence Statement

> **ARCH-04 was treated as evidence to verify, not as acceptance.**

No product implementation was modified. No backend, frontend, admin, `src/`, tests, migrations,
SQL, RLS, seed data or runtime configuration was created, edited, moved, deleted or executed by this
task. No migration was applied in either direction. No production system was contacted. The only
repository artifact created by this task is **this ARCH-05 report**. ARCH-01, ARCH-02, ARCH-03,
ARCH-04, P16, UIUX-01, POST-ARCH and PO-CAMS were **not** modified (see §4).

---

## 3. Repository Verification

### 3.1 Baseline commands and observed results

| Command | Observed | Result |
|---|---|---|
| `git branch --show-current` | `p8-release-reconciled` | PASS (expected) |
| `git rev-parse HEAD` | `172bdd26d1d2fd2c7bf03a05a40532b662117729` | PASS (expected ARCH-04) |
| `git rev-parse HEAD^` | `906e66c4e2fa8ca02b006c71437bb988c4f53a48` | PASS (expected baseline) |
| `git status --short --branch` | `## p8-release-reconciled...origin/p8-release-reconciled [ahead 142]`; ` M .gitignore`; 17 untracked pre-existing files | Dirty but unrelated (see §3.3) |
| `git status --porcelain \| wc -l` | `18` | Unchanged from Phase 0 to end |
| rebase/merge/cherry-pick state | none (`no in-progress git op`) | PASS |

**HEAD is exactly the expected ARCH-04 commit, on the expected branch, with the expected parent.**
The `P17_ARCH_REVERIFICATION_BLOCKED` stop-condition was therefore **not** triggered.

### 3.2 Working-tree state (important for interpreting results)

The worktree is **dirty**: one pre-existing tracked modification (`.gitignore`) and 17 pre-existing
untracked files (`.costrict/`, `8`, `=`, `costrict-p3-ov-01-independent-re-verification.txt`,
`docs/ChatGPT/*`, several `CT-PO-P12-*` / `CT-PO-P14-*` / Insight docs, `CT-PO-MASTER-WORKPLAN`,
and the untracked ARCH-03 report). **These were present before ARCH-04 and are unrelated to P17
implementation.** None was staged, modified or deleted by this task. The P17 documents under test
are all **tracked and committed** at HEAD, so they are not affected by working-tree dirtiness.

### 3.3 ARCH-03 report tracking status (discrepancy worth recording)

The ARCH-03 independent report and the ARCH-05 report directory are tracked; however:

```
$ git ls-files --error-unmatch docs/architecture/CO-STRING-P17-ARCH-03-...md
error: pathspec '...' did not match any file(s) known to git
$ git status --short -- docs/architecture/CO-STRING-P17-ARCH-03-...md
?? docs/architecture/CO-STRING-P17-ARCH-03-20250925-INDEPENDENT-VERIFICATION-FREEZE.md
```

**ARCH-03 is untracked** — the independent ARCH-03 verdict has never been committed. It was
preserved in the working tree by ARCH-04 (mtime `2026-09-25 14:42:39 +0600`, before ARCH-04's commit
at `15:07:28 +0600`), and ARCH-04 correctly did not stage it. This is a historical-audit-trail
observation (INFO), not an ARCH-04 defect. Recorded so the chain of custody is explicit.

---

## 4. Historical Preservation

Independently verified by comparing the **git blob SHA at the baseline commit** against the **git blob
SHA at HEAD** for every protected document. Identical SHA ⇒ byte-identical content.

| Document | Baseline blob | HEAD blob | Result |
|---|---|---|---|
| `CT-PO-P17-ARCH-01-...-20250925.md` | `d2a35438af9f1ff5483fec15e6005f93f0f5ad3d` | same | **byte-identical** |
| `CT-PO-P16-FINAL-VERIFICATION-20250925.md` | `661386784a7798a607a7c3fc3f7f30c02298529d` | same | **byte-identical** |
| `CT-PO-P17-UIUX-01-...-UX-STANDARD.md` | `51ff70bdba4e3f4910b81bb6ff6f794443768ca8` | same | **byte-identical** |
| `CT-PO-P17-POST-ARCH-DECISIONS-20260925.md` | `3060bcb02305d14a052d7b67c5ef600859009ea3` | same | **byte-identical** |
| `CarbonTally_PO_Carbon_Accounting_Management_Decision_2026-09-25.md` | `22566021037e76e007f788d465349cac2b5eb055` | same | **byte-identical** |
| `CO-STRING-P17-ARCH-03-...-FREEZE.md` (control spec) | untracked | untracked | **not modified** — mtime `14:42:39 +0600` predates ARCH-04 commit `15:07:28 +0600`; sha256 `07d64890e18314626cd3d816cfb52daf22d4fc12742e62e4d7b3dad9d039c2a7` |
| ARCH-04 report | (created by ARCH-04) | `dc4ee38e484b8d9f473edf0cd403a259c2af388c` | unchanged by this task |

Command:
```
for f in <protected docs>; do
  b=$(git rev-parse "906e66c4e2fa8ca02b006c71437bb988c4f53a48:$f")
  h=$(git rev-parse "172bdd26d1d2fd2c7bf03a05a40532b662117729:$f")
  [ "$b" = "$h" ] && echo "SAME $f" || echo "DIFF $f"
done
```

**Result: ARCH-01, P16 final verification, UIUX-01, POST-ARCH and PO-CAMS are byte-identical
between the ARCH-04 baseline and ARCH-04. ARCH-03 was not modified. No historical-integrity
violation.**

---

## 5. ARCH-04 Commit Scope

### 5.1 Independent command

```
$ git show --name-status --format=fuller 172bdd26d1d2fd2c7bf03a05a40532b662117729
$ git diff --name-only 906e66c4e2fa8ca02b006c71437bb988c4f53a48 172bdd26d1d2fd2c7bf03a05a40532b662117729
```

### 5.2 Changed-file classification

| # | File | Status | Classification | Authorized? |
|---|---|---|---|---|
| 1 | `docs/architecture/CT-PO-P17-ARCH-02-RECONCILIATION-20250925.md` | M | P17 architecture Markdown (annotations + addendum) | YES |
| 2 | `docs/architecture/CT-PO-P17-ARCH-04-RECONCILIATION-20250925.md` | A | ARCH-04 reconciliation report | YES |
| 3 | `docs/architecture/CT-PO-P17-IMPLEMENTATION-PHASE-PLAN-20250925.md` | M | P17 phase plan | YES |
| 4 | `docs/architecture/artifacts/p17_acceptance_matrix_20250925.json` | M | P17 acceptance matrix | YES |
| 5 | `docs/architecture/artifacts/p17_arch04_reconciliation_20250925.json` | A | ARCH-04 JSON artifact | YES |
| 6 | `docs/architecture/artifacts/p17_architecture_reconciliation_20250925.json` | M | P17 architecture reconciliation | YES |
| 7 | `docs/architecture/artifacts/p17_schema_delta_20250925.md` | M | P17 schema delta | YES |
| 8 | `docs/architecture/artifacts/p17_scope2_domain_matrix_20250925.json` | M | P17 Scope 2 architecture matrix | YES |
| 9 | `docs/architecture/artifacts/p17_scope3_category_matrix_20250925.json` | M | P17 Scope 3 architecture matrix | YES |

**Checks:**
- All 9 changed paths are under `docs/architecture/` (verified: `grep -v '^docs/architecture/'` → none).
- Every changed file extension is `.md` or `.json` (verified: `grep -vE '\.(md|json)$'` → none).
- **No** backend, frontend, admin, `src/`, tests, migrations, SQL, RLS, seed or runtime-config file was
  changed. **No unauthorized changes.**
- Migration inventory unchanged: `ls supabase/migrations/ | wc -l` → **83**; latest
  `20261009000000_p16r7_calculation_request_idempotency.sql`; no file `>= 20261010000000`
  (the P17 migration slots remain proposals). **No P17 migration exists.**

**Result: ARCH-04 commit scope is documentation-only and authorized.**

---

## 6. HIGH-01 Re-Verification — Consultant organization identity

### 6.1 Independent read-only reproduction (local Demo Lab only)

```
docker exec supabase_db_carbon_ledger psql -U postgres -d carbontally_demo_local -tAc \
 "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='consultant_profiles' ORDER BY ordinal_position;"
→ id, user_id, company_name, ... (NO organization_id)

... SELECT count(*) FROM information_schema.columns WHERE table_name='organizations' AND column_name='organization_type';
→ 0

... SELECT count(*) FROM information_schema.tables WHERE table_name='organization_relationship';
→ 0

... SELECT kcu.column_name, ccu.table_name FROM information_schema... WHERE tc.table_name='consultant_clients';
→ consultant_id → consultant_profiles(id) ; organization_id → organizations(id)

... SELECT count(*) FROM consultant_profiles cp WHERE EXISTS (SELECT 1 FROM organizations o WHERE o.name ILIKE '%'||cp.company_name||'%');
→ 0   (1 consultant_profiles row, 0 matching organizations)
```

### 6.2 ARCH-04 disposition (verified)

| Requirement (task §8) | Evidence | Result |
|---|---|---|
| A. No longer claims consultant org identity already verified | Schema delta §10.1 reclassified to **`PARTIAL — MISSING LINKAGE`**; `p17_architecture_reconciliation` `findings[]` classification `PARTIAL — MISSING LINKAGE` with `corrected_by` | PASS |
| B. Corrected classification = `PARTIAL — MISSING LINKAGE` | Same two artifacts; ARCH-04 §5 | PASS |
| C. Explicit P17-0 mandatory decision/dependency | Acceptance `reconciliation_arch02.new_phase_gate.must_pass[5]`; phase plan A10; `implementation_dependencies[2]` | PASS |
| D. PO model preserved (consultant firm independent org; own accounting; client independent; explicit relationship; client-owned accounting) | ARCH-04 §5 "What is NOT changed"; arch reconciliation `...p17_0_obligation` | PASS |
| E. No code/schema implemented | Schema delta §10.1 says no column/type/table created; migration inventory shows no P17 migration | PASS |
| F. No duplicate consultant-client model | Schema delta §10.1 retains `consultant_clients` as `EXISTS — REUSE`; phase plan A9 | PASS |

### 6.3 Residual literal `EXISTS — VERIFIED` occurrences (searched, context-inspected)

| Location | Context | Assessment |
|---|---|---|
| `CT-PO-P17-ARCH-02-...md:181` (historical §7.1 table row) | Original ARCH-02 claim, preserved as history; **immediately followed by a `⚠ CORRECTED BY ARCH-04` blockquote** referencing the row and stating the correct classification | Acceptable (annotate + addendum preservation pattern); the claim is no longer presented as current truth |
| `CT-PO-P17-ARCH-02-...md:715` (ARCH-04 addendum before/after table) | Describes the *before* state | Not a live claim |
| `CT-PO-P17-ARCH-04-...md:71,85,106` | Describes the finding / before state | Not a live claim |
| `p17_architecture_reconciliation_20250925.json:48` | Corrected row, `PARTIAL — MISSING LINKAGE` | Not a stale claim |
| `p17_schema_delta_20250925.md:264` | Separate **`consultant firm membership`** row, `EXISTS — VERIFIED`, explicitly scoped "links users to a consultant profile; does not supply an organization identity for the firm" | Correct, correctly scoped |
| `p17_arch04_reconciliation...json:28,187` | before-state record | Not a live claim |

**Verdict HIGH-01: PASS.** The correction is semantically correct, the facts are independently
reproduced against the live local schema, the PO model is preserved, and no contradictory live claim
remains (the one historical row is unambiguously annotated). No code/schema was secretly added.

---

## 7. MEDIUM-01 Re-Verification — Acting-for propagation vs `AC-AUDIT-01`

### 7.1 Independent read-only reproduction (column presence)

```
customer_documents          → organization_id, organization_member_id, uploaded_by, updated_by, classification_by ; NO acting-for org
suppliers                   → organization_id, created_by, updated_by ; NO acting-for org
review_audit_trail          → performed_by, performed_by_email, assigned_to ; NO acting-for org
review_assignment_history   → assigned_by, assigned_to ; NO acting-for org
report_versions             → created_by ; NO prepared-by org
SELECT ... column_name ILIKE '%acting_for%' OR '%on_behalf%' OR '%actor_organization%' OR '%performed_by_organization%'  → 0 rows
```

All ARCH-03 factual assertions confirmed. **No acting-for/actor-organization column exists anywhere
in the public schema today.**

### 7.2 Per-path disposition (from `p17_schema_delta_20250925.md` §10.3)

| Path | Owner | Actor | Actor Org | Acting-For | Persisted/Derived | Audit-safe | Result |
|---|---|---|---|---|---|---|---|
| source/activity documents (`customer_documents`) | `organization_id` | `uploaded_by`, `updated_by`, `organization_member_id`, `classification_by` | derivable only via user link — **rejected** | absent | **(A) additive implementation required** (P17-B/C/E/F/G) | read-time derivation explicitly rejected as not audit-safe | PASS (unambiguous disposition) |
| suppliers (`suppliers`) | `organization_id` | `created_by`, `updated_by` | rejected | absent | **(A) additive implementation required** (P17-B/C/E) | same rationale | PASS |
| review/approval (`review_audit_trail`, `review_assignment_history`) | via `review_id` | `performed_by`, `assigned_by`, `assigned_to` | rejected | absent | **(A) additive implementation required** (P17-H) | approval authority capability-gated; acting-for must be recorded | PASS |
| reports (`report_versions`, `report_version_artifacts`) | via `report_id` | `created_by` | rejected | absent | **(A) additive implementation required** (P17-I) | PO §24 prepared-by cannot be derived after the fact | PASS |
| calculations (`calculation_snapshots`) | `organization_id` | `performed_by`, `calculated_by` | — | absent | **(A) persist** `performed_by_organization_id` + `acting_for_organization_id` | authoritative persist | PASS |
| evidence (`evidence_line_items`) | `organization_id` | extraction/upload actor | — | absent | **(A) persist** `contributed_by_organization_id` | authoritative persist | PASS |
| audit (`audit_trail` / audit writer) | `table_name`+`record_id` | `performed_by` | — | absent | **(A) persist** `actor_organization_id` + `acting_for_organization_id` | authoritative carrier | PASS |
| emissions_logs (additional material accounting path) | `organization_id` | `created_by_user_id`, `verified_by`, `updated_by` | — | absent | **(A) persist** the same two | consumption-boundary parity | PASS |

### 7.3 The key AC-AUDIT-01 test

The task's key requirement is that `AC-AUDIT-01` be **satisfiable without ambiguity**, and that
`ACTING FOR` be context, not an authorization boundary.

- **Option-B derivation is bounded:** permitted *only* where the audit writer persists
  `actor_organization_id` + `acting_for_organization_id` **and** a reliable object→audit-record
  linkage exists (schema delta §10.3 "Option-B derivation rule"). Otherwise the path is classed
  **"additive implementation required"** and owns that work in a named phase.
- **The mutable-actor derivation is explicitly rejected:** "A derivation from `uploaded_by` → the
  user's organisation **at read time** is **not audit-safe** (membership/consultancy can change after
  the fact), so it is explicitly rejected as an option-B rule" (schema delta §10.3; ARCH-04 §6;
  arch reconciliation `arch_04_disposition`; arch04 JSON `derivation_rejected_reason`). The principle
  is documented **consistently across four artifacts**.
- **Authorization separation preserved:** "`ACTING FOR` is **context, not an authorization boundary**
  (POST-ARCH §35; UIUX-01 §6, §44)" — stated in schema delta §10.3, ARCH-04 §6, and arch04 JSON
  `governing_rule_preserved`. Authorization remains separately governed by the existing
  authorization/RLS vocabulary (unchanged; `AC-DELEG-01`, `AC-CUST-03`, `T-INV-08` unchanged).

**Verdict MEDIUM-01: PASS.** The propagation set was genuinely widened from 4 to 8 paths, each path has
an unambiguous (A)/(B) disposition sufficient to make `AC-AUDIT-01` satisfiable, no derivation rule
was invented, and the context≠authorization principle is documented consistently.

---

## 8. MEDIUM-02 Re-Verification — P17-E/F/G status-conditional acceptance

### 8.1 Independent verification of the acceptance artifact (not the prose)

Category status (read directly from `p17_scope3_category_matrix_20250925.json → status_rollup`):

```
SUPPORTED       [3,4,5,6]
PARTIAL         [1,7,8,9,12,13]
DEFERRED        [11,14,15]
NOT_IMPLEMENTED [2,10]
```

| Gate | Phase title | Bullets | Relevant bullets | Verdict |
|---|---|---|---|---|
| **P17-E** | Categories 1–5 | 6 (was 4) | b1 "…for each category among (1,2,3,4,5) whose authoritative architecture status is **SUPPORTED or PARTIAL**"; b2 NOT_IMPLEMENTED/DEFERRED → explicit BLOCKED/DEFERRED; b3 full status vocabulary | **Fully reconciled** |
| **P17-F** | Categories 6–10 | 5 (was 4) | b1 "one E2E result per category (6,7,8,9,10) **where the category is not DEFERRED**"; b2 status vocabulary; b5 "category 10 either delivered … or formally recorded as BLOCKED" | **Partially reconciled — see §8.2** |
| **P17-G** | Categories 11–15 | 4 (was 3) | b1 "…(11,12,13,14,15) where the category is not DEFERRED"; b2 status vocabulary | Reconciled (no NOT_IMPLEMENTED category in 11–15) |

- Category 2 remains `NOT_IMPLEMENTED` (**not promoted**); category 10 remains `NOT_IMPLEMENTED`
  (**not promoted**).
- No methodology was invented; cooling still resolves fail-closed.
- P17-0 item 7 schedules an "acceptance consistency check" over exactly this class of issue.

### 8.2 Residual contradiction — P17-F bullet 1 vs category 10 (FINDING)

P17-F bullet 1 requires **one END-TO-END VERIFIED result per category (6,7,8,9,10) where the category
is not DEFERRED**. Category 10 is `NOT_IMPLEMENTED`, **not** `DEFERRED`. Therefore, read literally,
**P17-F bullet 1 still demands an E2E result for a NOT_IMPLEMENTED category** — the identical
contradiction class ARCH-03 raised against P17-E and the very finding ARCH-04 §7 claims to have
"reconciled". Bullet 2 and bullet 5 mitigate it (both permit a documented BLOCKED outcome for
category 10), but bullet 1 was not tightened (unlike P17-E bullet 1, which was).

Additionally, ARCH-04 §7 asserts: *"The remaining gates were re-checked for the same class of
contradiction: P17-A…P17-D, P17-H, P17-I, P17-J contain no category-status assertions, so no further
contradiction of this class exists."* This claim is **inaccurate**: it checked other gates but did not
reconcile P17-F's own blanket bullet against its own NOT_IMPLEMENTED category 10.

A second, lower-grade tension exists for `PARTIAL` categories: P17-E bullet 1 and P17-F/G bullet 1
put `PARTIAL` in the "E2E required" bucket, while the newly-added vocabulary bullet defines
`PARTIAL → bounded acceptance`. For category 1 (PARTIAL) these bullets differ in strictness. This is
interpretively reconcilable (an E2E result for the supported portion) but is not a single clean rule.

**Severity: MEDIUM (same class as the original ARCH-03 MEDIUM-02; partially unresolved).**
**Verdict MEDIUM-02: PARTIAL.** This is the finding that drives the ARCH-05 verdict.

---

## 9. LOW-01 — Tenant-key naming

| Requirement | Evidence | Result |
|---|---|---|
| Conceptual = `claimant_organization_id`; physical = `contractual_instruments.organization_id`; explicit | `p17_schema_delta_20250925.md` **§10.6 (new) Canonical terminology** table; §3.1 `organization_id` row now states the conceptual/physical mapping "one-to-one" | PASS |
| Scope 2 matrix records the mapping | `p17_scope2_domain_matrix...json` instrument field now carries `canonical_terminology` | PASS |
| No physical rename | schema delta §10.6 "No physical column is renamed"; migration inventory unchanged | PASS |

**Verdict LOW-01: PASS.** The distinction is explicit and non-confusing: conceptual claim-owner name
vs the uniform physical tenant key, with a one-to-one rule and a "use the qualified name where
precision matters" discipline.

---

## 10. LOW-02 — `energy_type` vocabulary

| Artifact | Observed | Result |
|---|---|---|
| `p17_schema_delta_20250925.md` §2.1 | `CHECK (energy_type IS NULL OR energy_type IN ('electricity','heat','steam','cooling'))` — `fuel` excluded with rationale | PASS |
| `CT-PO-P17-ARCH-02-...md` §10.2 | Annotated to the four-value vocabulary; `fuel` explicitly not a Scope 2 type; Scope1/3 row `energy_type = NULL` | PASS |
| `p17_scope2_domain_matrix...json` | `energy_type` note = authoritative four values; `fuel` deliberately absent | PASS |

**Residual (INFO):** `CT-PO-P17-ARCH-01-...-20250925.md` (the preserved historical contract, which this
freeze requires to remain **byte-identical**) still states at lines 212 and 271:
`electricity | heat | steam | cooling | fuel`. This is **by-design historical persistence**, not a
live contradiction — the ratified correction is layered in ARCH-02 §10.2 / schema delta §2.1 /
Scope 2 matrix. Recorded so a reader of ARCH-01 alone is not misled.

**Verdict LOW-02: PASS** (with the ARCH-01 historical residue noted).

---

## 11. LOW-03 — Stale acceptance metadata

Read directly from `p17_acceptance_matrix_20250925.json`:

- `post_contract_po_decisions.status` = **`RECONCILED_BY_ARCH_02_WITH_ARCH_04_CORRECTIONS`**
  (was `APPROVED_PO_DECISIONS_REQUIRING_RECONCILIATION`).
- `reconciliation_performed` = **`true`** (was `false`), plus `reconciled_by` and
  `reconciliation_authority`.
- New `independent_verification` block: ARCH-03 verifier, verdict `P17_ARCH_FREEZE_PARTIAL`, all seven
  findings listed.
- New `arch_04_corrections` block (task + report + artifact + `status: COMPLETE`).
- `blocks` now: *"…remain blocked until the ARCH-04 corrected architecture is INDEPENDENTLY
  RE-VERIFIED and frozen… the outstanding condition is independent verification, not reconciliation."*
- `historical_note` records the previous stale values and why they were replaced.
- `current_verdict` = **`RECONCILED_BY_ARCH_02, CORRECTED_BY_ARCH_04, AWAITING_INDEPENDENT_RE_VERIFICATION`**;
  "every gate remains UNSTARTED; P17-0 and P17-A are NOT authorized."

The corrected metadata **explicitly distinguishes** ARCH-02 reconciliation, ARCH-03 independent
findings, ARCH-04 correction, and the pending independent re-verification; it does **not** claim
freeze PASS. **Verdict LOW-03: PASS.**

---

## 12. LOW-04 — Scope 3 customer/UIUX representation

| Requirement (task §14) | Evidence | Result |
|---|---|---|
| A. Global cross-cutting requirement explicit | `p17_scope3_category_matrix...json → cross_cutting_requirements` with `customer_and_consultant_contribution` and `uiux` blocks, `applies_to: "every category 1-15"` | PASS |
| B. ARCH-02 wording no longer falsely claims per-category fields | ARCH-02 §11.3 carries a `⚠ NARROWED BY ARCH-04` blockquote stating they are cross-cutting, "not as a claim that each category row carries its own copy" | PASS |
| C. Requirement applies to all 15 categories | `applies_to: "every category 1-15"`; ARCH-02 annotation "for every category, as cross-cutting requirements" | PASS |
| D. UIUX-01 remains normative and in-phase | UIUX-01 unchanged (byte-identical); cross-cutting `uiux` cites UIUX-01 §25–§27; global amendments unchanged | PASS |
| E. Customer contribution governed | cross-cutting `acceptance: [AC-CUST-01, AC-CUST-02, AC-CUST-03, AC-ORGCTX-01, AC-AUDIT-01]` | PASS |
| No unnecessary duplication | `explicitly_not_per_category_fields` states these are not per-category fields | PASS |

**Verdict LOW-04: PASS.**

---

## 13. EXTRA-01 — `CORRECTION REQUIRED` lifecycle representation

| Requirement | Evidence | Result |
|---|---|---|
| Carried into P17-0 | Acceptance `must_pass[8]`: "the lifecycle mapping table explicitly names CORRECTION REQUIRED, or documents its existing rework-edge representation"; phase plan A-series / P17-0 impact; arch04 JSON `EXTRA-01` = `RECONCILED_AS_P17_0_OBLIGATION` | PASS |
| Not falsely claimed implemented | schema delta §10.4 lists `CORRECTION REQUIRED` as an existing-machine mapping to produce at P17-0; no state is claimed added | PASS |
| No duplicate lifecycle | schema delta §10.4 "No new lifecycle table is proposed"; arch_02/arch01 unchanged | PASS |
| Decision remains open | ARCH-04 §12/§21 R5 "not yet produced" | PASS |

**Verdict EXTRA-01: `RESOLVED AS P17-0 DISCOVERY OBLIGATION`.**

---

## 14. EXTRA-02 — Estimation-record ordering

- Schema delta §3.4 labels `estimation_records` as **(P17-H)**; phase plan §16.2 order is
  P17-E/F/G → P17-H.
- Phase plan **§7 line 133 explicitly states the prerequisite**: *"Prerequisites. P17-D (and
  **P17-H's estimation records before categories 7/11/12 are attempted**)."*
- ARCH-04 §14 and §21 record it as **risk R11**, order unchanged; arch04 JSON `EXTRA-02` =
  `DOCUMENTED_NOT_A_DEFECT`.

**Assessment: `DOCUMENTED RISK — NOT A DEFECT`** (the dependency *is* explicitly documented).
**Residual observation (LOW):** the §16.2 ordering diagram still places P17-H *after* P17-F/G while
§7 requires P17-H's estimation records *before* categories 7/11/12; the diagram does not visually
reflect the stated prerequisite. This is a presentation tension, not a new defect, and P17-0 owns
reconciliation of the ordering.

---

## 15. Cross-Document Regression Search

Searches were run over all P17 architecture artifacts, the phase plan, UIUX-01, POST-ARCH, PO-CAMS
and the artifacts directory, with context inspection (not only exact-phrase matching).

| Stale claim searched | Result |
|---|---|
| consultant organization = `EXISTS — VERIFIED` | **No live stale claim.** Only the preserved historical ARCH-02 §7.1 row (annotated) + before-state references (§6.3) |
| "acting-for only 4 paths" | **None.** All references state 8 paths / 4+4 with (A)/(B) disposition |
| unconditional P17-E category 1–5 E2E | **None.** P17-E bullet 1 is status-conditional |
| unconditional category 6–10 / 11–15 E2E | **FOUND (P17-F bullet 1)** — not tightened for NOT_IMPLEMENTED category 10 (§8.2). P17-G has no NOT_IMPLEMENTED category → clean |
| `fuel` as Scope 2 `energy_type` | **None live.** schema delta §2.1 / ARCH-02 §10.2 / Scope 2 matrix are four-value; **ARCH-01 (preserved historical) still lists five** — noted §10 |
| contradictory tenant terminology | **None.** One canonical mapping documented (§9) |
| stale reconciliation status | **None.** Replaced with `RECONCILED_BY_ARCH_02, CORRECTED_BY_ARCH_04, AWAITING_INDEPENDENT_RE_VERIFICATION` (§11) |
| per-category UIUX/customer field claim | **None live.** ARCH-02 §11.3 annotated/narrowed; cross-cutting block added (§12) |
| "P17-0 only 6 mandatory items" | **None.** Every reference states 6 → 10 (acceptance matrix actually has 10) |
| "P17-A authorized" | **None.** Every reference states P17-A NOT AUTHORIZED (`NOT`) |
| "architecture freeze PASS" | **None.** ARCH-04/arch04 JSON explicitly say "NOT `P17_ARCH_FREEZE_PASS`" |
| "implementation authorized" | **None.** ARCH-01 status remains `PARTIAL`; all P17 docs state implementation not authorized |
| "production contacted" | **None.** All artifacts state `production_contacted: false` |

---

## 16. P17-0 Gate

Independently read `p17_acceptance_matrix_20250925.json → reconciliation_arch02.new_phase_gate.must_pass`
and phase plan §16.1. The gate now has **10** items (was 6), each discovery-only:

1. UIUX-01 §55 18-row existing-vs-missing matrix
2. UIUX-01 §56 UX acceptance matrix
3. full model classification (org/roles/authz/RLS/consultant/customer/reportability/audit/evidence/supplier/snapshots/logs/reporting)
4. consultant-client relationship reuse confirmation
5. **consultant ↔ organization identity/linkage decision** (ARCH-03 HIGH-01)
6. **acting-for propagation map** (ARCH-03 MEDIUM-01)
7. **acceptance-criteria consistency check** (ARCH-03 MEDIUM-02)
8. **lifecycle `CORRECTION REQUIRED` representation** (ARCH-03 §11 residual)
9. customer capability/enablement representation decision
10. no UI/backend code changed (discovery only)

**Semantic coverage of the task §18 list:** items 1–8 map directly to task items 1–8; task item 2
(capability) = item 9; task items 6/7 (UIUX matrices) = items 1/2. **Task item 9
(organization/context/delegation verification)** is covered by items 3+5 (organization),
item 6 (context) and by `AC-DELEG-01` / phase-plan amendments A5/A6 (delegation) but is **not
separately enumerated**. **Task item 10 (Scope2/Scope3 architecture consistency)** is only partly
covered by item 7 (acceptance consistency) and by the unchanged `AC-CAMS-01`. These are minor
enumeration gaps (LOW), not blockers.

**P17-0 is correctly gated as DISCOVERY / MAPPING ONLY, no implementation.**
**Verdict: CORRECTLY GATED** (with the two minor enumeration observations above).

---

## 17. P17-A Gate

| Artifact | Statement | Result |
|---|---|---|
| `p17_acceptance_matrix...json → current_verdict` | "P17-0 and P17-A are NOT authorized" | PASS |
| `... → post_contract_po_decisions.blocks` | "P17-A is NOT authorized" | PASS |
| `p17_architecture_reconciliation...json → independent_verification_note` | ARCH-04 must be independently re-verified and frozen before any implementation "including P17-0 and P17-A" | PASS |
| phase plan §16.4 / §17 | "P17-A remains gated … NOT AUTHORIZED" | PASS |
| arch04 JSON `verdict_note` / ARCH-04 §22 | "P17-A is NOT AUTHORIZED" | PASS |
| ARCH-01 §54 (historical) | status `PARTIAL — PREREQUISITE DECISIONS REQUIRED`; no authorization | PASS |

**Verdict: P17-A REMAINS UNAUTHORIZED** (completing ARCH-04 did not authorize it).

---

## 18. Security / Tenant Isolation

- ARCH-04 is **documentation-only**; no RLS policy, authorization function, table, column or seed was
  changed (§5; migration inventory unchanged).
- `ACTING FOR` is explicitly **context, not an authorization boundary** in schema delta §10.3,
  ARCH-04 §6 and arch04 JSON — authorization remains separately governed. No weakening.
- `AC-DELEG-01` (per-client revocable delegated access), `AC-CUST-03` (negative security matrix),
  `T-INV-08` (cross-tenant four-cell RLS) and the RLS helper vocabulary are **unchanged**
  (acceptance matrix `unchanged_from_arch01` / `acceptance_updates`).
- The consultant↔organization gap is now a **P17-0 decision**, so no new privilege or bypass is
  introduced; the missing linkage is documented, not papered over.
- **No tenant-isolation or security weakening attributable to ARCH-04 was found.**

---

## 19. Production Safety

| Question | Answer |
|---|---|
| Production contacted | **NO** |
| Production writes | **NO** |
| Production migration | **NO** |
| Deployment | **NO** |

All database inspection was **read-only `SELECT`** (plus `information_schema` catalog reads) against
the **local Demo Lab** container only: `supabase_db_carbon_ledger` (`carbontally_demo_local`,
`127.0.0.1:54426`). No DDL/DML, no migration in either direction, no destructive shell/container
command, no external/production connection, no credential use, no data export. No product test suite
was run (not required for an architecture re-verification). The integration harness (which truncates
its target) was **not** run. No secrets were printed.

---

## 20. Findings

| ID | Severity | Finding | Evidence | Status |
|---|---|---|---|---|
| ARCH05-01 | **MEDIUM** | **P17-F gate bullet 1 still demands an E2E result for NOT_IMPLEMENTED category 10** — the same contradiction class ARCH-03 raised against P17-E, left unfixed. Mitigated by P17-F bullets 2/5 (BLOCKED allowed) and phase plan §7, but bullet 1 was not tightened as P17-E's was. | `p17_acceptance_matrix_20250925.json` P17-F must_pass b1 ("per category (6,7,8,9,10) where the category is not DEFERRED") vs `p17_scope3_category_matrix_20250925.json` `status_rollup.NOT_IMPLEMENTED = [2,10]` | **UNRESOLVED (partial)** |
| ARCH05-02 | **MEDIUM** | **ARCH-04 §7's claim "no further contradiction of this class exists" is inaccurate** — the re-check covered other gates but not P17-F's own bullet 1 vs its own category 10. | `CT-PO-P17-ARCH-04-RECONCILIATION-20250925.md` §7 "Elsewhere in the acceptance matrix…" | **UNRESOLVED (accuracy)** |
| ARCH05-03 | LOW | P17-E/F/G buckets `PARTIAL` with `SUPPORTED` for E2E (bullet 1) while the added vocabulary defines `PARTIAL → bounded acceptance`; differing strictness for category 1. Interpretively reconcilable. | acceptance matrix P17-E b1/b3, P17-F/G b1/b2 | OPEN |
| ARCH05-04 | LOW | EXTRA-02 phase-order presentation tension: §16.2 diagram places P17-H after P17-F/G while §7 line 133 states P17-H estimation records are a prerequisite for categories 7/11/12. Risk R11 recorded; dependency documented. | phase plan §7 line 133 vs §16.2 | DOCUMENTED RISK |
| ARCH05-05 | LOW | P17-0 `must_pass` does not **separately enumerate** "organization/context/**delegation** verification" or "**Scope2/Scope3** architecture consistency" (task §18 items 9–10); covered by items 3/5/6/7 and `AC-DELEG-01`/`AC-CAMS-01` but not as distinct obligations. | acceptance matrix `new_phase_gate.must_pass` | OPEN (minor) |
| ARCH05-06 | INFO | ARCH-01 (preserved historical contract) still lists the superseded five-value `energy_type` vocabulary including `fuel` (lines 212, 271). Required byte-identical by the freeze. | `CT-PO-P17-ARCH-01-...md:212,271` | Expected (historical) |
| ARCH05-07 | INFO | The independent ARCH-03 report is **untracked** (never committed); preserved in the working tree only. | `git ls-files --error-unmatch` error; `??` status | Observation |
| ARCH05-08 | INFO | HIGH-01 residual: the preserved historical ARCH-02 §7.1 table row still literally reads `EXISTS — VERIFIED`, immediately followed by a `⚠ CORRECTED BY ARCH-04` blockquote. Judged acceptable (annotate + addendum). | `CT-PO-P17-ARCH-02-...md:181,186-191` | Accepted pattern |

**No BLOCKER / CRITICAL / HIGH findings.** No unauthorized implementation. No production contact.
No historical-integrity violation. No security/tenant weakening.

---

## 21. Final Independent Verdict

```
ARCH-03:  P17_ARCH_FREEZE_PARTIAL
ARCH-04:  P17_ARCH_RECONCILIATION_COMPLETE
ARCH-05:  P17_ARCH_FREEZE_PARTIAL
```

**Verdict: `P17_ARCH_FREEZE_PARTIAL`**

Justification against the task §23 PASS criteria:

| # | PASS criterion | Result |
|---|---|---|
| 1 | HIGH-01 fully/accurately reconciled | YES (verified against live schema) |
| 2 | MEDIUM-01 fully sufficient for AC-AUDIT-01 | YES (8 paths, bounded derivation, context≠authorization) |
| 3 | MEDIUM-02 fully reconciled | **NO** — P17-F bullet 1 residual (ARCH05-01/02) |
| 4 | LOW-01…LOW-04 internally consistent | YES |
| 5 | EXTRA-01 carried as P17-0 discovery | YES |
| 6 | EXTRA-02 adequately documented | YES (risk R11) |
| 7 | No stale contradictory architecture claim remains | **NO** — P17-F bullet 1 vs NOT_IMPLEMENTED category 10 |
| 8 | P17-0 correctly gated discovery-only | YES |
| 9 | P17-A remains unauthorized | YES |
| 10 | ARCH-01 preserved | YES (byte-identical) |
| 11 | ARCH-03 preserved | YES (not modified) |
| 12 | P16 preserved | YES (byte-identical) |
| 13 | No unauthorized implementation | YES |
| 14 | No production contacted | YES |
| 15 | Internally coherent enough for P17-0 discovery | YES |

Because criteria 3 and 7 are not met (the P17-F acceptance gate retains the ARCH-03 MEDIUM-02
contradiction class for `NOT_IMPLEMENTED` category 10, and ARCH-04 §7's "no further contradiction"
claim is inaccurate), the architecture is **usable for further correction but is not fully frozen**.

**Meaning of this verdict:** the ARCH-04 corrections are **substantively correct** — HIGH-01,
MEDIUM-01, LOW-01…LOW-04, EXTRA-01 and EXTRA-02 are genuinely reconciled — but one **material,
non-blocking** residual remains, so a PASS cannot be issued. This verdict does **not** mean the
product is implemented, production-ready, authorized, or that Scope 2/Scope 3 or the 15 categories
are implemented.

**Per the PARTIAL rule, P17-0 MUST NOT be authorized by this task.** The Product Owner decides the
next step after reviewing this report.

---

## 21b. Handoff Notes (for the next, implementation-capable task — NOT performed here)

I attempted **no** fix. Minimal corrections an author/PO agent would need:

- **ARCH05-01 / ARCH05-02** — Open
  `docs/architecture/artifacts/p17_acceptance_matrix_20250925.json` → `phase_gates[P17-F].must_pass[0]`
  and tighten it as P17-E was tightened, e.g. "…per category (6,7,8,9,10) **whose authoritative
  architecture status is SUPPORTED or PARTIAL**", and add the same conditional qualifier to P17-G
  bullet 1 for consistency; then correct ARCH-04 §7's "no further contradiction of this class exists"
  statement. Documentation-only.
- **ARCH05-03** — Decide and record whether `PARTIAL` categories require a full E2E or a bounded-part
  E2E, and make P17-E/F/G bullet 1 and the status vocabulary agree. Documentation-only.
- **ARCH05-04** — Reflect the §7 estimation-records prerequisite in the §16.2 ordering diagram (or
  re-state R11). Documentation-only.
- **ARCH05-05** — Optionally add explicit P17-0 `must_pass` items for delegation verification and
  Scope2/Scope3 architecture consistency. Documentation-only.

No code, migration, schema, RLS, seed or UI change is implied by any finding.

---

## APPENDIX A — Commands Executed (read-only)

```
git branch --show-current ; git rev-parse HEAD ; git rev-parse HEAD^
git status --short --branch ; git status --porcelain | wc -l
git log --oneline --decorate -10
git show --stat --oneline 172bdd26d1d2fd2c7bf03a05a40532b662117729
git show --name-status --format=fuller 172bdd26d1d2fd2c7bf03a05a40532b662117729
git diff --name-only 906e66c... 172bdd2...
git diff 906e66c... 172bdd2... -- <changed artifacts>
git rev-parse <baseline>:<file> ; git rev-parse HEAD:<file>   # blob-SHA preservation
git ls-files --error-unmatch docs/architecture/CO-STRING-P17-ARCH-03-...md
python3 -c "import json; json.load(open(<artifact>))"          # JSON parse validation (×5)
ls supabase/migrations/ | wc -l ; ls supabase/migrations/ | sort | tail -6
rg -n "<stale-phrase>" docs/architecture/...
sed/stat/read of architecture documents (read-only)
docker exec supabase_db_carbon_ledger psql -U postgres -d carbontally_demo_local -tAc "<SELECT ...>"
```

All database access was `SELECT`/`information_schema` only against the local Demo Lab.

## APPENDIX B — Side Effects Observed

- **Repository files created/modified by this task before the report commit:** NONE (the single
  authorized artifact is this ARCH-05 report).
- Read-only SQL (`SELECT`) against the local `carbontally_demo_local` container — no writes, no
  schema/row changes.
- No migrations run; no product test suite run; no caches/coverage/build artifacts produced.
- `git status` after Phase 0 and before the report commit was **identical** to Phase 0
  (`1` modified tracked `.gitignore`; `17` untracked pre-existing; `0` staged) — 18 porcelain entries.
- No `/tmp` or `/temp` usage. No secrets echoed (none encountered).

## APPENDIX C — Document Control

**Document:** `CT-PO-P17-ARCH-05-INDEPENDENT-REVERIFICATION-FREEZE`
**Verdict:** `P17_ARCH_FREEZE_PARTIAL`
**Implementation performed:** NO · **Migrations created:** NONE · **Production:** NOT CONTACTED
**P17-0:** not authorized by this verification · **P17-A:** NOT AUTHORIZED
**Independence:** COMPLETED (ARCH-04 treated as evidence to verify, not acceptance)

---

VERDICT:
P17_ARCH_FREEZE_PARTIAL

P17-0 AUTHORIZATION:
NOT AUTHORIZED BY THIS VERIFICATION

P17-A AUTHORIZATION:
NOT AUTHORIZED

PRODUCTION:
NOT CONTACTED

IMPLEMENTATION:
NOT PERFORMED

INDEPENDENCE:
INDEPENDENT RE-VERIFICATION COMPLETED

**Precise correction required before a PASS can be issued:** tighten the P17-F gate bullet 1 (and
align P17-G) so a `NOT_IMPLEMENTED`/`DEFERRED` category is never required to produce an
END-TO-END VERIFIED result, and correct ARCH-04 §7's "no further contradiction of this class exists"
statement. All other ARCH-03 findings are genuinely and accurately reconciled; the architecture
remains safe to carry forward once this one acceptance-artifact inconsistency is corrected.
