# CT-P8-B2-AUTHORISATION-CONTRACT-CORRECTION-20260913-021

**1. Task identity:** `CT-P8-B2-AUTHORISATION-CONTRACT-CORRECTION-20260913-021`
**Task type:** BOUNDED DOCUMENTATION CORRECTION ONLY — **no implementation**
**Date:** 2026-09-13 · **Batch:** Phase 8 Reporting / Disclosure — B2 Evidence / Line-Item Addressability
**Corrects (per finding):** `F-019-1` raised by `CT-P8-B2-PO-IMPLEMENTATION-AUTHORISATION-20260913-019`
**Verdict:** `B2 AUTHORISATION-CONTRACT CORRECTION COMPLETE — READY FOR GATE RE-RUN`

---

## 1. Reason for correction

The B2 implementation-authorisation gate (task 019) correctly **BLOCKED** on one material
contract-internal inconsistency (**F-019-1**): the verification-harness expectation in contract §20.3
("New objects present") did not match the normative B2 DDL. The same stale figures were echoed in the
pre-ratification contract report 017 (index count and runtime-test count).

This task corrects **only** those documentation figures so that the contract's verification expectations
match the authoritative schema and the governance chain is internally consistent. No architecture, decision,
schema, code, test, RLS, extraction or data change was made or is authorised.

**Files touched by this task (exactly three):**

| File | Action |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md` | corrected §20.3 (row + new exact enumeration) |
| `docs/cline/reports/CT-P8-B2-IMPLEMENTATION-CONTRACT-20260913-017.md` | corrected echoed figures (§16 runtime test count, clone delta) and aligned §18 decision status |
| `docs/cline/reports/CT-P8-B2-AUTHORISATION-CONTRACT-CORRECTION-20260913-021.md` | this report (new) |

## 2. F-019-1 description (as recorded by task 019)

Contract §20.3 stated:

> `| New objects present | Exactly: 1 table, 2 columns, 2 FKs, 3 new indexes (org, source_file, dve line), 2–3 policies, **no trigger** (B2-D11) |`

while the normative DDL declares **four** explicit indexes plus one constraint-backed unique index:

| # | Object | Declared in |
|---|---|---|
| 1 | `idx_eli_org` | §7.1 |
| 2 | `idx_eli_source_file` | §7.1 |
| 3 | `idx_calculation_snapshots_source_line_item` | §8.1 |
| 4 | `idx_dve_source_line_item` | §9.1 |
| 5 | `evidence_line_items_identity_unique` (created by `UNIQUE (source_item_id, line_number)`) | §7.1 |

The row was self-contradictory (the row above it correctly expects **two** new indexes on pre-existing tables)
and used ambiguous counts for FKs ("2 FKs") and policies ("2–3 policies") as a **total** delta.

**Direction of correction:** the **schema is authoritative**; the verification assertion was corrected to
match the schema. No schema element was added, removed or renamed to make the old sentence pass.

## 3. Exact contract correction (§20.3)

**3.1 Replacement of the summary row** (contract line 1166):

*Before:*
```
| New objects present | Exactly: 1 table, 2 columns, 2 FKs, 3 new indexes (org, source_file, dve line), 2–3 policies, **no trigger** (B2-D11) |
```
*After:*
```
| New objects present | **Exactly** the objects enumerated below — **1** new table, **2** new columns on pre-existing tables, **5** new FK constraints (3 declared inside the new table + 2 on pre-existing tables), **4** explicit new indexes **plus 1 constraint-backed unique index** (counted separately), **2** new policies, **0** triggers |
```

**3.2 New normative enumeration inserted immediately after the §20.3 table** (before §20.4), so the expectation
is deterministic and directly testable:

* **New table (1):** `public.evidence_line_items`.
* **New columns on pre-existing tables (2):** `calculation_snapshots.source_line_item_id`,
  `disclosure_value_evidence.source_line_item_id` (both nullable).
* **New FK constraints (5):** 3 declared inline inside the new table (`organization_id` → `organizations`;
  `source_item_id` → `manual_extraction_items` **`ON DELETE RESTRICT`**; `source_file_id` →
  `organization_files` `ON DELETE SET NULL`) **+** 2 on pre-existing tables
  (`calculation_snapshots_source_line_item_id_fkey`, `disclosure_value_evidence_source_line_item_id_fkey`,
  both `ON DELETE SET NULL`). The note records that the inline FKs take PostgreSQL's default names per the
  repository's existing convention, and that the **FK delta is 5 constraints, of which 2 are on pre-existing
  tables** — the figure the row above asserts.
* **Explicit new indexes (4):** `idx_eli_org`, `idx_eli_source_file`,
  `idx_calculation_snapshots_source_line_item`, `idx_dve_source_line_item`.
* **Constraint-backed unique index (1), explicitly NOT one of the four:** `evidence_line_items_identity_unique`
  (`UNIQUE (source_item_id, line_number)`), to be counted separately and never folded into the four.
* **New policies (2)** on `evidence_line_items`, both `FOR SELECT TO authenticated`: the org-member policy
  (`public.p8_disclosure_is_org_member(organization_id)`) and the PE-mirror policy
  (`public.is_entity_member(public.work_item_effective_entity(source_item_id))`).
* **Triggers (0):** no trigger of any kind (B2-D11).

The two adjacent rows that were **already correctly scoped** ("Constraints on `calculation_snapshots` /
`disclosure_value_evidence` — identical except the two declared FKs"; "Indexes on pre-existing tables —
identical except the two declared indexes") were left **unchanged**, because they already match the schema.

---

## 4. Exact report-017 correction

**4.1 Runtime acceptance-test count** (§16, lines 283–284):

*Before:*
```
* **Runtime (database-backed, mandatory — a green static suite is *not* verification: the V1 lesson):** the 18
  enumerated acceptance tests in the contract §20.2, covering materialisation order/count, idempotent rerun,
```
*After:*
```
* **Runtime (database-backed, mandatory — a green static suite is *not* verification: the V1 lesson):** the **20**
  runtime acceptance tests in the contract §20.2, covering materialisation order/count, idempotent rerun,
```
(The contract §20.2 contains 20 numbered runtime tests; tests 19–20 were added by task 018.)

**4.2 Clone-harness delta** (§16, lines 289–290):

*Before:*
```
  identical for the 116 pre-existing tables, rows byte-identical, and only the declared delta (1 table,
  2 columns, 2 FKs, 3 indexes, 2–3 policies) present; re-apply → `rc=0`, zero diff.
```
*After:*
```
  identical for the 116 pre-existing tables, rows byte-identical, and only the declared delta present
  (1 new table; 2 new columns on pre-existing tables; 5 new FK constraints — 3 declared inside the new table
  + 2 on pre-existing tables; 4 explicit new indexes plus 1 constraint-backed unique index; 2 policies;
  no trigger); re-apply → `rc=0`, zero diff. *(Figures aligned to the ratified contract §20.3 —
  `CT-P8-B2-AUTHORISATION-CONTRACT-CORRECTION-20260913-021`.)*
```

**4.3 §18 decision-status alignment (required by the sweep mandate).** Report 017's decision table was written
pre-ratification and still read as open: its heading was "Unresolved decisions (12; none blocks
implementation)", its B2-D1 row recommended **CASCADE** (contradicting the ratified `ON DELETE RESTRICT`) and
its B2-D11 row recommended **"soft now"** (contradicting the ratified "no retention/deletion mechanism").

*Before (heading + rows):* `## 18. Unresolved decisions (12; none blocks implementation)`; column set
`# | Decision | Blocks B2?`; B2-D1 "… **recommend CASCADE** (no app delete path exists)"; B2-D11 "… **recommend
soft now**".
*After:* `## 18. Decisions (12) — CLOSED / PO-RATIFIED`, with an explicit pointer to
`CT-P8-B2-PO-DECISION-RATIFICATION-20260913-018`, a `# | Decision | Ratified outcome | Blocks B2?` column set,
B2-D1 = **`ON DELETE RESTRICT` — preservation-first; `CASCADE` prohibited**, B2-D11 = **B2 introduces no
retention/deletion mechanism — N3 / the retention+privacy workstream remains separate**, and the other ten rows
restated as their ratified outcomes.

This is a **status/wording** alignment only: the same twelve decisions, the same subjects, the same
architecture, **no new decision**, and no change to the ratified decision set.

## 5. Before / after verification figures

| Figure | Before (stale) | After (normative) | Contract §20.3 | Report 017 §16 |
|---|---|---|---|---|
| Explicit new indexes | "3 new indexes (org, source_file, dve line)" | **4** — `idx_eli_org`, `idx_eli_source_file`, `idx_calculation_snapshots_source_line_item`, `idx_dve_source_line_item` | ✅ corrected | ✅ corrected |
| Constraint-backed unique index | not distinguished | **1** — `evidence_line_items_identity_unique` (counted separately) | ✅ stated | ✅ stated |
| New FK constraints | "2 FKs" (ambiguous total) | **5** = 3 inside the new table + 2 on pre-existing tables | ✅ corrected | ✅ corrected |
| New policies | "2–3 policies" (ambiguous range) | **2** (org-member SELECT; PE-mirror SELECT) | ✅ corrected | ✅ corrected |
| Triggers | "no trigger" | **0** (unchanged; now explicit) | ✅ stated | ✅ stated |
| Runtime acceptance tests | "the 18 enumerated acceptance tests" | **20** (contract §20.2, items 1–20) | (no count in §20.3) | ✅ corrected |
| New table / columns | "1 table, 2 columns" | **1** table, **2** columns on pre-existing tables (scope now explicit) | ✅ stated | ✅ stated |

---

## 6. Stale-wording sweep (post-correction)

Grep counts across the **two corrected files** (`C` = contract, `R17` = report 017) — all required to be zero:

| Stale pattern | C | R17 | Status |
|---|---|---|---|
| `3 new indexes` | 0 | 0 | cleared |
| `3 indexes` | 0 | 0 | cleared |
| `2 FKs` (as a total delta) | 0 | 0 | cleared |
| `2–3 policies` | 0 | 0 | cleared |
| `the 18` / `18 enumerated` (test count) | 0 | 0 | cleared |
| `recommend CASCADE` | 0 | 0 | cleared |
| `recommend soft` | 0 | 0 | cleared |
| `soft immutability` | 0 | 0 | cleared |
| `Unresolved decisions` | 0 | 0 | cleared |

**Corrected figures present (grep-verified):** contract — "Explicit new indexes (4)" ✅, "Constraint-backed
unique index (1)" ✅, "New FK constraints (5)" ✅, "New policies (2) on" ✅, "Triggers (0)" ✅. Report 017 —
"the **20**" ✅, "4 explicit new indexes plus 1 constraint-backed unique index" ✅, "5 new FK constraints" ✅,
"2 policies;" ✅. The contract and report 017 therefore **agree** on every corrected figure.

**Two deliberate residuals (recorded, not defects):**

1. **Contract §23 B2-D11 rationale** retains the phrase *"the earlier wording 'soft now'"* — this is the
   corrective note recording that the wording was **replaced**, not a live recommendation (it is the audit
   trail of the change mandated by task 018). Retained by design.
2. **Report 019 is NOT modified** (it is outside this task's permitted write set). Its occurrences of
   "3 new indexes" / "2 FKs" / "2–3 policies" / "the 18" are **verbatim evidence quotations of the defect**
   inside finding F-019-1; they must remain for the finding's integrity and are not verification expectations.
   The sweep is therefore scoped to the two corrected files.

## 7. Confirmation — B2-D1…B2-D12 unchanged

* Contract §23 still carries **12** `PO DECISION (B2-D…)` blocks (grep count = 12) plus the §23.13 closure
  summary; **no decision text was edited** — only the §20.3 *verification* row and its new enumeration.
* The ratification record `CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md` was **not modified**.
* Post-edit spot checks: `ON DELETE RESTRICT` present in the DDL (L299) and unchanged; the three inline FKs and
  the two added FKs unchanged; `B2 introduces NO retention/deletion mechanism` present;
  `separately tracked remediation finding` (F-B2-7 deferred) present; `AMEND, NEVER DELETE` (F-B2-13) present;
  `NO RETRO-LINKING` (B2-D12) present.
* Report 017 §18 was restated only as ratified status — **no new decision** introduced.

## 8. Confirmation — B2 schema unchanged

The correction changed **no** schema element. Verified by grepping the DDL constructs after the edit:

* `REFERENCES public.manual_extraction_items(id) ON DELETE RESTRICT` — unchanged (L299, B2-D1).
* `CONSTRAINT evidence_line_items_identity_unique UNIQUE (source_item_id, line_number)` — unchanged (L317).
* `CREATE INDEX IF NOT EXISTS idx_eli_org …` (L320), `… idx_eli_source_file …` (L321) — unchanged.
* `ADD COLUMN IF NOT EXISTS source_line_item_id uuid` on `calculation_snapshots` (L441) and
  `disclosure_value_evidence` (L511) — unchanged.
* `CREATE INDEX IF NOT EXISTS idx_calculation_snapshots_source_line_item` (L448),
  `… idx_dve_source_line_item` (L518) — unchanged.
* §20.2 still contains **20** numbered runtime tests (1–20).

No table, column, constraint, index, policy or trigger was added, removed, renamed or re-scoped by this task.

## 9. Confirmation — no implementation occurred

* No migration file was created (`supabase/migrations` still 57 files; no `20260916…` file).
* No backend/frontend/test/RLS/extraction/factor-matching file was written; no database DDL/DML was executed.
* No backfill was run; no history was rewritten; no production action was taken.
* The only writes were the two documented corrections and this report.

---

## 10. Git / worktree state

| Fact | Before work | After work |
|---|---|---|
| Branch | `main` | `main` (unchanged) |
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` | **unchanged** |
| Staged changes | 0 | **0** |
| Tracked modifications (pre-existing, unrelated) | 208 | **208** (unchanged) |
| Untracked (normal / all) | 76 / 796 | 76 / **797** — the two corrected files were already untracked; the single +1 in the *all* listing is **this report** (it lands inside the already-untracked `docs/cline/reports/`), which adds no new *normal* entry |
| Migrations on disk | 57 | **57** |
| Reset / clean / stash / checkout / stage / commit / push | — | **none** |

**Nuance recorded:** both corrected files are **untracked in git**, so there is no VCS diff for them; the
correction is evidenced by the before/after greps (§6), the verbatim before/after blocks (§3, §4) and their
mtime change (contract `2026-09-13 11:53:46`, report 017 `2026-09-13 11:55:34`).

## 11. Migration count

**57** before and after (unchanged). B2's two migrations remain **declared only** —
`20260916000000_p8_b2_evidence_line_items.sql` and `20260916010000_p8_b2_provenance_line_links.sql` — with **no
file created** and **no migration applied**.

## 12. Database state

Read-only introspection after the corrections (unchanged from before):

`evidence_line_items` = **absent** · `calculation_snapshots.source_line_item_id` = **absent** ·
`disclosure_*` tables = **0**. No DDL or DML was executed, and no data was read beyond schema metadata.

## 13. Explicit verdict

**`B2 AUTHORISATION-CONTRACT CORRECTION COMPLETE — READY FOR GATE RE-RUN`**

Both documentation inconsistencies identified by task 019 (F-019-1 and its echoed figures) are corrected and
verified:

* contract §20.3 now states an exact, deterministic, scope-explicit expectation — **4 explicit indexes plus 1
  separately-counted constraint-backed unique index; 5 FK constraints with explicit scope; 2 policies; 0
  triggers** — backed by a normative enumeration beneath the table;
* report 017 now agrees (**20** runtime acceptance tests; the corrected clone delta) and its §18 decision table
  is restated as the ratified decision set;
* every stale pattern is cleared from the two corrected files (sweep §6), with two deliberate residuals
  documented (the B2-D11 corrective note; report 019's retained defect quotations);
* the B2 schema and B2-D1…B2-D12 are **unchanged**, and **nothing has been implemented**.

**Next step (not performed here):** re-run `CT-P8-B2-PO-IMPLEMENTATION-AUTHORISATION-20260913-019` as a fresh
gate. This report does **not** authorise implementation, migration creation, application of any migration, or
production deployment.
