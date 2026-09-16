# CT-P8-B2-PO-DECISION-RATIFICATION-20260913-018

**Task identity:** `CT-P8-B2-PO-DECISION-RATIFICATION-20260913-018`
**Task type:** PO DECISION CLOSURE + CONTRACT RATIFICATION ONLY — **implementation not authorised**
**Date:** 2026-09-13
**Batch:** Phase 8 Reporting / Disclosure — **B2 Evidence / Line-Item Addressability**
**Contract ratified:** `docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md`
**Authoritative PO decision record:** `docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md`
**Verdict:** `B2 PO DECISION RATIFICATION COMPLETE — READY FOR IMPLEMENTATION AUTHORISATION`

---

## 1. Task identity and scope

Close **B2-D1 … B2-D12** as Product-Owner decisions, update the B2 implementation contract so that it records
those decisions and reflects the two changed normative literals, and produce this report plus the authoritative
ratification record.

**Respected constraints (verified §9):** no implementation; no migration created; no backend/frontend/test/RLS
change; no extraction change; no factor-matching change; no database migration run; no historical backfill; no
commit; no push; no worktree disturbance. Exactly three files were written (contract update, ratification
record, this report).

## 2. Baseline / worktree state recorded before work

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| Staged changes | 0 |
| Tracked modifications (pre-existing, unrelated) | 208 |
| Untracked paths (normal listing / all listings) | 74 / 790 |
| Migrations on disk | 57 (newest: `20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql`) |
| Worktree operations | **none** (no reset/clean/stash/checkout/stage/commit/push) |
| Files written by this task | `docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md` (updated); `docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md` (new); this report (new) |

## 3. Sources inspected

* `docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md` (the contract being ratified) —
  all sections, in particular §1, §4, §6, §7, §15, §20, §21, §22, §23, §24, §26.
* `docs/cline/reports/CT-P8-B2-IMPLEMENTATION-CONTRACT-20260913-017.md` (pre-ratification contract report).
* `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md` §13–§14, §22 (field list / chain).
* `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` §6 (`DM-7`), §10 (honesty
  invariant).
* `docs/architecture/CARBONTALLY_PHASE8_P8X_COMPREHENSIVE_IMPLEMENTATION_READINESS_20260912.md` §15–§16, §20.
* `docs/architecture/CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md` (§6 boundary; §25; line 413).
* `docs/cline/reports/CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md` (PDF/IMAGE 8→1 finding).
* `docs/cline/reports/CT-P8-B1-V1R-INDEPENDENT-RE-VERIFICATION-20260913-016.md` (B1 closed).
* Code cited by the decisions: `backend/services/automatic_processing.py`,
  `backend/api/v3_processing_workflow.py`, `backend/domain/evidence.py`, `backend/data/manual_extraction.py`,
  `backend/api/v3_operations.py`, `backend/tests/integration/test_disclosure_b1_runtime.py`,
  `backend/tests/unit/data/test_disclosure_sql_typing.py`,
  `backend/tests/unit/data/test_disclosure_migration.py`.

No new forensic investigation was performed; the code references above were re-verified only as the citations
already recorded in the contract.

---

## 4. Decision closures (B2-D1 … B2-D12)

| # | PO decision (closed) | Contract literal affected | Blockers |
|---|---|---|---|
| **B2-D1** | **`ON DELETE RESTRICT`** — preservation-first; **`CASCADE` prohibited**; evidence lines are authoritative provenance and must not be auto-destroyed by a parent delete; B2 introduces no replacement deletion/anonymisation workflow | §7.1 DDL FK; §7.4 row; §7.6; §15.1; §15.3; §18.1; §20.2 (new test 19); §21 rows 9–10; §23; §24 R11 | **none** |
| **B2-D2** | **Detect + report + never rewrite** (no silent update, delete, or replacement identity for the same ordinal); supersession requires a separately authorised design | §11.3; §23 | **none** |
| **B2-D3** | **Mirror the existing PE item-access boundary** (`is_entity_member(work_item_effective_entity(source_item_id))`); no new consultant authorization model | §16.1; §16.3; §18.1; §23 | **none** |
| **B2-D4** | **Defer the `source_page` defect (F-B2-7)** to a separate bounded remediation workstream; B2 must not fix, reinterpret, copy, transform or propagate the value, or change evidence classification | §4 (F-B2-7 disposition); §23; §27.1 | **none** |
| **B2-D5** | Per-**document** forward audit event + per-**run** backfill summary + per-item/ordinal divergence events; no document contents, line values, signed URLs or secrets; existing `audit_trail`; no parallel audit system | §17; §23 | **none** |
| **B2-D6** | Forward hook at the **data-layer choke point** (`ManualExtractionRepository`); no duplicated logic across callers | §12.1; §23 | **none** |
| **B2-D7** | **Open `extraction_method` vocabulary** — no restrictive `CHECK` (avoids coupling to the extraction/P1 workstream) | §7.1; §11.2; §23 | **none** |
| **B2-D8** | **`row_reference` NULL for Class-1**; never invoice number, document number, guessed row or inferred reference | §7.2; §11.2; §23 | **none** |
| **B2-D9** | **No new HTTP endpoint; no frontend work** | §12.4; §22; §23 | **none** |
| **B2-D10** | **Design §14.3 field deviation accepted**; removed `document_type_code`, `confidence_score`, `extracted_at`, `extracted_by`, `processing_origin`; added/retained `materialisation_kind`, `created_at`; rationale preserved (`processing_origin` is a mutable parent attribute) | §7.2–§7.4; §23 | **none** |
| **B2-D11** | **B2 introduces no retention/deletion mechanism** (no soft-delete, trigger, purge, anonymisation or deletion job); N3 / retention+privacy defines future semantics; replaces the earlier “soft now” wording | §7.6; §15.3; §20.2 (new test 20); §20.3; §23; §24 R14; §27.3 | **none** |
| **B2-D12** | **No retro-linking** of historical snapshots; no request-ID derivation change; no recalculation to obtain line identity | §8.4; §13.4; §15.2; §22.2; §23 | **none** |

**EXPLICIT BLOCKERS: NONE.** Full text of each ruling, rationale and consequence is in the authoritative
ratification record §3.

---

## 5. Contract changes made

All edits were confined to `docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md`
(now 1,650 lines, 28 sections). The original structure was preserved.

| # | Section | Change |
|---|---|---|
| 1 | Header | Added a **Ratification status** block: B2-D1…B2-D12 CLOSED; implementation still not authorised |
| 2 | §1.3 (new) | Added the **PO ratification** subsection: what changed, what did not, and the two changed literals |
| 3 | §4 findings | Appended **PO dispositions** to the F-B2-7 and F-B2-13 rows |
| 4 | §6.1 (new) | Added the **PDF/IMAGE extraction remediation** as a separate future investigation workstream with the twelve investigation questions |
| 5 | §7.1 (DDL) | `source_item_id` FK changed to **`ON DELETE RESTRICT`**; the “unresolved literal / default CASCADE” note replaced by the ratified preservation-first rationale |
| 6 | §7.4 table | The `source_item_id` delete-rule row now records **B2-D1 CLOSED** |
| 7 | §7.5 | Hybrid-canonicality recommendation marked **PO-RATIFIED core architecture** |
| 8 | §7.6 | Trigger bullet replaced by the **B2-D11 no-retention** boundary; consumer-link bullet now distinguishes `SET NULL` consumers from the `RESTRICT` parent link |
| 9 | §11.3 | Divergence text now points at **B2-D2 (CLOSED)** |
| 10 | §12.1 | Forward hook marked **PO-RATIFIED — B2-D6** |
| 11 | §13.3 | “No new calculation engine” marked **PO-RATIFIED core architecture** |
| 12 | §15.1 | Line-row immutability row now cites the `RESTRICT` parent link |
| 13 | §15.3 | Rewritten: **immutability enforcement + the retention boundary (B2-D11 CLOSED)** — no trigger, no purge, no anonymisation, explicit N3 boundary |
| 14 | §16.1 / §16.3 | PE policy rows marked **B2-D3 CLOSED / PO-RATIFIED** |
| 15 | §18.1 | B2-1 row now records **PE policy (B2-D3)**, **`RESTRICT` FK (B2-D1)**, **no trigger/retention artefact (B2-D11)** |
| 16 | §20.2 | Added runtime acceptance tests **19** (RESTRICT behaviour) and **20** (no retention artefacts) |
| 17 | §20.3 | “New objects present” row now asserts **no trigger** |
| 18 | §21 | Edge cases 9 (parent delete → prevented) and 10 (orphan line → not reachable) rewritten for `RESTRICT` |
| 19 | §22.2 | Out-of-scope table expanded: PDF/IMAGE investigation workstream, F-B2-7 remediation, retro-linking, retention/anonymisation |
| 20 | §23 | Heading/intro converted to **“Decision record — CLOSED / PO-RATIFIED”**; all twelve items rewritten to PO DECISION + rationale + implementation consequence + blockers; added **§23.13 closure summary** |
| 21 | §26.3 | Verdict updated to **`B2 DECISION SET RATIFIED — READY FOR IMPLEMENTATION AUTHORISATION`** |
| 22 | §27 (new) | Dispositions: **27.1 F-B2-7** (separate remediation, prescribed wording), **27.2 F-B2-13** (amend-never-delete), **27.3 N3 retention**, **27.4 PDF/IMAGE investigation** |
| 23 | §28 (new) | Ratification traceability table (four artefacts; decisions CLOSED, blockers none, implementation not authorised) |

**Unchanged:** every other architectural decision, all evidence tags, all source citations, the provenance
model, the materialisation rules, the backfill boundary, the audit actions, the API/service boundary, the
migration strategy (still exactly **two** additive migrations), the acceptance criteria and the V1R-style
verification harness.

**Consistency sweep performed (grep-verified):** no residual open-decision markers; no residual `[REC]`
recommendation tied to a closed decision; no residual `Decision B2-D` open references; no residual `CASCADE`
recommendation for `source_item_id`; no residual “soft now / soft immutability / immortal” wording (only the
explicit statement that the phrase was replaced); all twelve **PO DECISION** blocks present.

---

## 6. F-B2-7 disposition

* **Status:** **preserved as a separately tracked remediation finding**; PO-accepted as real.
* **Prescribed wording (contract §27.1 / ratification record §5):** *“`source_page` currently has a verified
  semantic defect: an auto-processing path can persist `page_count` into `source_page`, while downstream
  evidence logic can interpret non-NULL `source_page` as an exact source location. B2 does not remediate,
  reinterpret, copy or propagate this value as line-level evidence. Separate remediation is required.”*
* **B2 obligations recorded:** no fix; no reinterpretation of existing `source_page`; no copying the value as an
  exact line location; no silent transformation of page counts into page references; no change to evidence
  classification. `evidence_line_items.source_page` remains populated **only** from a genuine per-line value.
* **Follow-up:** a separate bounded task (not B2) — no implementation assigned to B2.

## 7. F-B2-13 disposition

* **Rule (PO-RATIFIED): AMEND, NEVER DELETE.**
* **Amend on B2 implementation:** `test_disclosure_b1_runtime.py::test_b2_b3_b4_boundary_untouched` and
  `test_disclosure_sql_typing.py::test_no_b2_b3_b4_objects_in_the_repository` — so the B2-absence assertions
  match the post-B2 reality while **the B3/B4 protection remains intact**.
* **Must not be weakened:** `test_disclosure_migration.py::test_no_b2_b3_b4_tables` and
  `::test_no_source_line_item_id_column` (migration-text guards) — the B1 migration file is not edited by B2,
  so these remain valid.
* **Report obligation:** the B2 implementation report must list each amendment with before/after text and
  demonstrate that no B3/B4 guard was removed.

## 8. PDF/IMAGE investigation boundary

* The PO has separately decided that the PDF/IMAGE extraction problem is investigated as its **own bounded
  workstream** (contract §6.1, ratification record §7) — previously labelled **P1**.
* **Not authorised here and not part of B2.** No extraction code, OCR setting, AI prompt/gate or `source_page`
  behaviour was modified, and none may be under this task.
* **Twelve investigation questions** recorded verbatim in the contract §6.1 and the ratification record §7.
* **B2's only interface:** the declared, optional per-line element keys `page`, `line_reference`,
  `extraction_method` (contract §11.7). B2 requires no extractor change.

## 9. Verification that no changes occurred

| Check | Method | Result |
|---|---|---|
| No source code changed | `git status` (tracked + untracked) + no editor writes outside the three documents | **Confirmed** |
| No migration created or applied | `ls supabase/migrations \| wc -l` = 57 before/after; newest file unchanged; no `psql` DDL executed | **Confirmed** |
| No test changed | no write to `backend/tests/**` | **Confirmed** |
| No RLS changed | no write to `supabase/migrations/**`; no policy DDL executed | **Confirmed** |
| No API/frontend changed | no write to `backend/api/**`, `frontend/**` | **Confirmed** |
| No extraction changed | no write to `backend/services/automatic_extraction.py`, `ai_document_extraction.py`, `extraction_suggestions.py` | **Confirmed** |
| No factor matching changed | no write to matching engine code | **Confirmed** |
| No database change | read-only `psql` SELECTs only (`information_schema`, `pg_constraint`, `pg_policies`); B1/B2 objects still absent | **Confirmed** |
| No historical backfill | backfill not implemented and not executed | **Confirmed** |
| No B2 implementation | no `evidence_line_items` table created; no `source_line_item_id` column added anywhere | **Confirmed** |
| No commit / push / worktree disturbance | HEAD unchanged; staged 0; 208 tracked modifications unchanged | **Confirmed** |

## 10. Git / worktree state (after work)

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` (**unchanged**) |
| Staged | 0 |
| Tracked modifications | 208 (pre-existing, unchanged) |
| Untracked (normal / all listings) | 75 / 792 (baseline 74 / 790; +1 normal for the ratification record inside a partly-tracked directory, +2 all for that record and this report) |
| Migrations | 57 (unchanged) |
| Reset / clean / stash / checkout / amend / commit / push | **none** |

## 11. Explicit verdict

**`B2 PO DECISION RATIFICATION COMPLETE — READY FOR IMPLEMENTATION AUTHORISATION`**

All twelve decisions are closed with **no blockers**, the contract records them and its normative literals are
consistent with them, the scope boundaries and evidence grounding are preserved, and **nothing has been
implemented**. The next task is a separate **B2 implementation-authorisation gate**.
