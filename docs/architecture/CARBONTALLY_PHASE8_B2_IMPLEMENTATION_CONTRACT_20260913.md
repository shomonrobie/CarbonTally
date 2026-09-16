# CarbonTally — Phase 8 Reporting / Disclosure
## Batch B2 — Evidence / Line-Item Addressability — IMPLEMENTATION CONTRACT

**Task identity:** `CT-P8-B2-IMPLEMENTATION-CONTRACT-20260913-017`
**Task type:** ARCHITECTURE + IMPLEMENTATION CONTRACT ONLY — **implementation is NOT authorised by this task**
**Date:** 2026-09-13
**Repository baseline:** branch `main` · HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c` (`feat: implement Phase 8 report lifecycle foundation`) · staged 0 · 208 pre-existing tracked modifications · 73 untracked paths · 57 migrations
**Predecessors (authoritative):** Phase 8 Disclosure Model Design (§13–§14, §17–§22) · Disclosure Model Decision Record (§6 `DM-7`, §10) · P8X comprehensive implementation-readiness (§15–§16, §20–§22, §29 G0-E) · B1 implementation contract (§6, §25, line 413) · B1 PO decision ratification · `CT-P8-B1-IMPLEMENTATION-20260912-013` · `CT-P8-B1-V1-INDEPENDENT-VERIFICATION-20260912-014` · `CT-P8-B1-CORRECTION-20260912-015` · `CT-P8-B1-V1R-INDEPENDENT-RE-VERIFICATION-20260913-016` · `CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912` · `CT-P8-EMISSION-FACTOR-MATCHING-FORENSIC-20260912`
**Evidence tags:** **[R]** repository fact · **[D]** ratified design/governance · **[V]** verified runtime/DB · **[I]** interpretation · **[REC]** recommendation · **[U]** unresolved
**Ratification status:** **RATIFIED** — **B2-D1…B2-D12 are CLOSED by the Product Owner** (task
`CT-P8-B2-PO-DECISION-RATIFICATION-20260913-018`; authoritative record:
`docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md`). The decision statuses in §23
are no longer open questions; the normative literals in this contract (notably **B2-D1 `ON DELETE RESTRICT`**
and the **B2-D11 no-retention boundary**) already reflect the ratified decisions.
**Implementation is still NOT authorised by this contract or by the ratification.**

---

## 1. Purpose, authority and boundary of this document

This document is the **complete, bounded implementation contract** for Phase 8 Batch **B2 — Evidence /
Line-Item Addressability**. It defines *what* B2 is, *exactly what schema* it adds, *how* line identity is
derived, *what may and may not be backfilled*, *which code paths change*, *what authorization/audit/RLS
applies*, *how it is migrated*, and *how it is verified*.

It is a **contract**. It authorises nothing. On its acceptance by the Product Owner:

* B2 implementation may be separately authorised under a new bounded task;
* **no** part of this document may be implemented, migrated, or deployed as a side effect of producing it.

**Explicitly outside this task (respected):** no schema change; no migration created; no backend/frontend
change; no test change; no RLS change; no data change; no production migration; no commit; no push; no
worktree mutation of any tracked or untracked file other than the two documents this task mandates.

**B1 is CLOSED** (`CT-P8-B1-V1R-INDEPENDENT-RE-VERIFICATION-20260913-016`: PASS WITH NONBLOCKING FINDINGS,
no P0/P1/P2 remaining). B1 is **not** reopened here. No direct architectural contradiction between the B1
contract and B2 was discovered; two **B1 test-scope artefacts** that B2 necessarily invalidates are
identified and bounded in §20.6 (consequences of B1's *current-scope* negative assertions, not defects in
B1).

### 1.1 The single sentence that defines B2

> **B2 makes a source line durable, addressable and immutable, so that a calculation, a disclosure value
> and a finalized report can point at *the exact line* — while honestly and permanently recording that no
> such line exists where the source never supported one.**

### 1.2 The root boundary (binding)

B2 solves **addressability and provenance**, not extraction fidelity.

* The **8→1 PDF/IMAGE extraction defect is a separate P1 workstream**
  (`CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912` §18–§20; `DM-7` Gate-0 refinement). B2 **must not**
  become the extraction-fidelity remediation batch.
* B2 **may** define the interface by which a future extractor supplies line-level location facts (§11.7).
  B2 **must not** implement, emulate, or approximate that extractor improvement.
* B2 **must not** silently re-extract any historical PDF/IMAGE document (`DM-7` §6 refinement point 3 —
  **PROHIBITED**).
* The EF-E factor-matching defect (P2) is untouched; no factor-matching behaviour changes.

### 1.3 PO ratification (task `CT-P8-B2-PO-DECISION-RATIFICATION-20260913-018`)

On **2026-09-13** the Product Owner reviewed this contract and **CLOSED B2-D1 … B2-D12**. The authoritative
decision record is `docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md`.

Consequences for this contract:

* §23 is now a **decision record** (each B2-D* is marked **CLOSED / PO-RATIFIED** with the PO's ruling,
  rationale, implementation consequence and blockers).
* Two normative literals changed to match the ratified decisions:
  **B2-D1 → `evidence_line_items.source_item_id ON DELETE RESTRICT`** (preservation-first; `CASCADE`
  **prohibited**), and **B2-D11 → B2 introduces no retention/deletion mechanism at all** (explicit N3
  boundary; no soft-delete, trigger, purge, anonymisation or deletion job).
* **F-B2-7** (the `source_page` page-count defect) is preserved as a **separately tracked remediation finding**
  and remains **out of B2 scope** (§27.1).
* The **PDF/IMAGE extraction remediation** is recorded as a **separate future investigation workstream**
  (§6.1) — not B2 implementation and not authorised.
* **No** other architectural decision, scope boundary, evidence tag or source grounding was altered.
* **Implementation of B2 is not authorised** by the ratification or by this contract. A separate
  implementation-authorisation gate is required.

---

## 2. Sources inspected for this contract

| # | Source | Kind |
|---|---|---|
| 1 | `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md` §13, §14, §17, §18.2, §22 | [D] |
| 2 | `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DECISION_RECORD_20260912.md` §6 (`DM-7` + Gate-0 refinement), §10 | [D] |
| 3 | `docs/architecture/CARBONTALLY_PHASE8_P8X_COMPREHENSIVE_IMPLEMENTATION_READINESS_20260912.md` §15, §16, §20–§22, §29 | [D] |
| 4 | `docs/architecture/CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md` §6, §25, line 413 | [D] |
| 5 | `docs/cline/reports/CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912.md` | [R]/[V] |
| 6 | `supabase/migrations/20260914000000_p8_b1_disclosure_model_foundation.sql` (B1 DDL + RLS + privilege posture) | [R] |
| 7 | `supabase/migrations/20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` (corrected posture, NULL-safe unique index, loud-failure precondition precedent) | [R] |
| 8 | `supabase/migrations/20260823010000_d33_evidence_traceability.sql` (the additive pattern B2 mirrors) | [R] |
| 9 | `supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql` (append-only trigger precedent) | [R] |
| 10 | `supabase/migrations/20260903010000_ws4_gate3_4a_item_assignment_foundation.sql` (`work_item_effective_entity`) | [R] |
| 11 | `supabase/migrations/20260810050000_v3m6_entity_rls.sql` (`is_entity_member`) | [R] |
| 12 | `backend/engines/calculation.py`, `backend/domain/calculation.py` (`CalculationRequest`, snapshot build, `content_hash`) | [R] |
| 13 | `backend/services/automatic_processing.py` (`_extract`, `_map`, `_validate`, `_calculate`, `_calculate_line`) | [R] |
| 14 | `backend/services/automatic_extraction.py` (`_rows_to_line_items`, `_completeness`, `_pdf_text`, method values) | [R] |
| 15 | `backend/services/ai_document_extraction.py` (`extract_candidate`, `_build_candidate`) | [R] |
| 16 | `backend/services/extraction_suggestions.py` (`suggest`, activity/quantity heuristics) | [R] |
| 17 | `backend/api/v3_operations.py` (`_run_line_calculation`, extraction-save endpoints), `backend/api/v3_processing_workflow.py`, `backend/api/v3_manual_extraction.py` | [R] |
| 18 | `backend/data/manual_extraction.py`, `backend/data/document_processing.py`, `backend/data/disclosure.py`, `backend/data/audit.py` | [R] |
| 19 | `backend/domain/evidence.py` (D33.1), `backend/domain/disclosure.py` (audit action constants) | [R] |
| 20 | `backend/tests/integration/{conftest.py,test_disclosure_b1_runtime.py,test_v3_rls_behavior.py}`, `backend/tests/unit/data/test_disclosure_{migration,sql_typing}.py` | [R] |
| 21 | Live local database schema/policy introspection (read-only, `public` schema) | [V] |

---

## 3. Baseline / worktree state (recorded before analysis)

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD | `19e4f01c176eee5870f3c15038b6e7c68b23281c` |
| Staged changes | 0 |
| Tracked modifications (pre-existing, unrelated) | 208 |
| Untracked paths (pre-existing) | 73 |
| Migration count | 57 (`20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` newest) |
| Worktree operations performed | **none** (no reset / clean / stash / checkout / commit / push / stage) |
| Files created by this task | this contract + `docs/cline/reports/CT-P8-B2-IMPLEMENTATION-CONTRACT-20260913-017.md` |

**Live database state (read-only introspection, local development DB)** [V]:

* `evidence_line_items` — **does not exist**; `calculation_snapshots.source_line_item_id` — **does not
  exist** (0 B2 objects). B1 tables are likewise absent here (no `disclosure_*` relation) — consistent with
  the V1R record that B1 has never been applied to this environment.
* `manual_extraction_items` — 36 columns; **no `organization_id` column**; tenant is reached via
  `batch_id → manual_extraction_batches.organization_id`.
* `calculation_snapshots` — carries `source_item_id` (FK → `manual_extraction_items`, `ON DELETE SET NULL`),
  `source_file`, `source_page`; **no** durable line identity.
* RLS: `manual_extraction_items` has **only** a PE `SELECT` policy (`manual_extraction_items_entity_select`
  using `work_item_effective_entity(id)` + `is_entity_member(...)`); `calculation_snapshots` has **only**
  `calc_snapshots_select_own` (`is_org_member(organization_id)`). Neither has an authenticated write policy;
  writes arrive through the backend/service role.
* FKs referencing `manual_extraction_items`: `calculation_snapshots_source_item_id_fkey` (`SET NULL`),
  `work_item_assignments_manual_extraction_item_id_fkey` (**`CASCADE`**).
* `document_processing_queue.source_item_id` exists but is a **plain `uuid`** (no FK constraint). [V]

---

## 4. Current-state findings (evidence-established)

Every finding is tagged and traceable. No claim relies on a historical report alone.

| # | Finding | Evidence | Tag |
|---|---|---|---|
| **F-B2-1** | **No durable line identity exists.** `extracted_data.line_items[]` elements cannot be referenced by any FK; `calculation_snapshots` provenance stops at document level (`source_item_id`, `source_file`, `source_page`). | `information_schema` (no `evidence_line_items`, no `source_line_item_id`) + forensic §16 | [R]/[V] |
| **F-B2-2** | **Ordinal is already the implicit join key.** `_map` iterates `targets = line_items or [flat]` positionally and any dropped line adds a reason → `mark_blocked` → `"blocked"`, so on success `mapped_data.line_items[i]` aligns with `extracted_data.line_items[i]`; `_calculate_line` uses `mapped_lines[idx]`; `_run_line_calculation` iterates `enumerate(lines)` with the same alignment. | `automatic_processing.py:684-760, 962-1029`; `v3_operations.py:469-490` | [R] |
| **F-B2-3** | **Line-scoped determinism already exists and must be preserved.** Calc request id = `uuid5(NAMESPACE_DNS, f"{job.id}::calc::{idx}::c1::{calc_digest}")`; map request id = `uuid5(… f"{job.id}::map::{idx}")`. Re-deriving these would orphan resume markers and risk duplicate snapshots. | `automatic_processing.py:660-680, 972-980` | [R] |
| **F-B2-4** | **`mapped_data.line_items` is a rewritten, lossy array — never an identity source.** `_run_line_calculation` sets `updated_mapped["line_items"] = line_results` (only `activity_type, factor_id, unit, quantity, emissions_kg`), discarding `factor_kind`, `mapping_confidence`, `methodology`, `stages_executed`. | `v3_operations.py:553-575` | [R] |
| **F-B2-5** | **The source row number is NOT recoverable.** `_rows_to_line_items` skips empty rows and emits only recognised keys; no row index is persisted. `invoice_number` is a document-level identifier copied per row, not a line reference. | `automatic_extraction.py:349-400` | [R] |
| **F-B2-6** | **Persisted arrays are already normalised and ordered.** CSV/XLSX skip empty rows; the AI path keeps dict elements only, drops empty records, and hoists `supplier/date/invoice_number` from the first line to the document level. | `automatic_extraction.py:357-360`; `ai_document_extraction.py:247-260` | [R] |
| **F-B2-7** | **`calculation_snapshots.source_page` is a page COUNT, not a page.** `_calculate_line` passes `source_page=job.metadata.get("page_count")`; job metadata's `page_count` is the item's page count (`item.page_count or 1`); the extraction advance persists the extractor's `page_count` separately as a queue column. `domain/evidence.py` treats non-NULL `source_page` as an exact location (`has_page = page is not None`) ⇒ `COMPLETE`. | `automatic_processing.py:1134`; `v3_processing_workflow.py:991`; `automatic_processing.py:489-494`; `domain/evidence.py:145,166,36` | [R] **(disposition: separately tracked remediation finding — §27.1. B2 does not remediate, reinterpret, copy or propagate this value as line-level evidence.)** |
| **F-B2-8** | **Tenant is reachable only through the parent.** `manual_extraction_items` has no `organization_id`; `get_item_org` joins `manual_extraction_batches`; `manual_extraction_batches.organization_id` and `document_processing_queue.organization_id` are NOT NULL. | `manual_extraction.py:838-846`; `information_schema` | [R]/[V] |
| **F-B2-9** | **One pipeline choke point, one extra API writer.** All pipeline/API extraction writes funnel through `ManualExtractionRepository.save_extracted_data` (4 call sites); `PUT /manual-extraction/items/{item_id}` additionally writes `extracted_data` through `update_item`. | `automatic_processing.py:453`; `v3_operations.py:1086,1662`; `v3_processing_workflow.py:445`; `v3_manual_extraction.py:120-135` | [R] |

| **F-B2-10** | **No application path deletes extraction items.** `ManualExtractionRepository.delete()` is a no-op stub (`return None`). DB children: `work_item_assignments` CASCADE, `calculation_snapshots` SET NULL. | `manual_extraction.py:1399-1400`; `pg_constraint` | [R]/[V] |
| **F-B2-11** | **D33 is the additive template B2 must mirror** (guarded `ADD COLUMN IF NOT EXISTS`; guarded FK with `ON DELETE SET NULL`; `CREATE INDEX IF NOT EXISTS`; idempotent exact-match backfill; one `BEGIN/COMMIT`). | `20260823010000_d33_evidence_traceability.sql:21-71` | [R] |
| **F-B2-12** | **B1's corrected posture is the template for a new table** (RLS enable; anon revoked; `authenticated` SELECT only; `TRUNCATE/TRIGGER/REFERENCES/MAINTAIN` revoked from `authenticated`; `service_role` ALL; `SECURITY DEFINER` membership helper). | `20260914000000_…:415-510`; `20260915000000_…:60-143` | [R] |
| **F-B2-13** | **Two B1-era test-scope artefacts B2 necessarily invalidates** (bounded and discharged in §20.6): the runtime `test_b2_b3_b4_boundary_untouched` (asserts `evidence_line_items` absent + no `source_line_item_id` column) and the unit `test_no_b2_b3_b4_objects_in_the_repository` (asserts the B1 data layer's executed SQL never mentions them). The two **migration-text** guards stay valid because the B1 migration file is never edited. | `test_disclosure_b1_runtime.py:844-898`; `test_disclosure_sql_typing.py:139-143`; `test_disclosure_migration.py:56-82` | [R] **(disposition: PO-RATIFIED — the two B1 scope assertions must be AMENDED, NEVER DELETED, and the two migration-text guards must not be weakened — §20.6, §27.2.)** |
| **F-B2-14** | **Runtime verification precedent exists and is reusable**: `INTEGRATION_DATABASE_URL` is forced to a dedicated `carbontally_test` DB that **refuses** the main app DB (D31), and B1's runtime suite **skips** — never fails — when its schema is unprovisioned (`_require_b1_schema`). V1R additionally proved schema safety on disposable privileges-inclusive clones (116 pre-existing tables' grants/policies/RLS identical before↔after). | `conftest.py:1-53`; `test_disclosure_b1_runtime.py:83-92`; V1R 016 | [R]/[V] |
| **F-B2-15** | **Extraction-method vocabulary is open and only partially persisted.** Values produced include `csv`, `xlsx`, `pdf_text`, `tesseract_ocr`, `onnx_ocr`, `ai`, and compound stamps (`"{deterministic}+{ai}"`); unsupported types emit `ftype.lower()`. The stamp is persisted on the **queue** (`ai_extraction_method`), never on the item. | `automatic_extraction.py:208-223,410-466`; `ai_document_extraction.py:201`; `automatic_processing.py:604-615,489-494` | [R] |
| **F-B2-16** | **No environment currently holds B2 (or B1) schema**, so B2-backed runtime tests cannot execute against the dev/demo DB; the V2 harness must ship with the skip-when-unprovisioned guard plus a documented disposable-clone provisioning recipe. | Local introspection (0 `disclosure_*` relations); V1R 016 | [V] |

**Derived conclusions that shape the design** [I]:

1. **The ordinal is the only honest identity basis.** It is the key the calculation layer already uses
   (F-B2-2, F-B2-3), it is stable for unchanged persisted JSONB, and it requires no re-extraction. A
   content-derived identity (e.g. hashing the line payload as the key) would be wrong, because two
   identical invoice lines are legitimately distinct.
2. **`extracted_data.line_items[]` must stay the eligibility source; `mapped_data` must not be read for
   identity** (F-B2-4).
3. **A line row must be a materialised, immutable record — not a live pointer into JSONB.** A pointer would
   silently change under a frozen report whenever `extracted_data` is later corrected (G6-D correction
   paths exist), breaking D15 reproducibility.
4. **`source_page` cannot be inherited from the snapshot** (F-B2-7); B2 populates it only from a genuine
   per-line location and otherwise leaves it NULL.

---

## 5. B2 objective, deliverables and acceptance criteria

### 5.1 Objective

Give every *genuinely line-structured* source a **durable, addressable, immutable line identity**; link the
immutable calculation to that identity; make the B1 evidence link line-addressable; and do all of it
**additively, idempotently and non-destructively** — with no re-extraction, no manufactured precision and
no rewrite of any historical row.

### 5.2 Deliverables (the complete B2 artefact list)

| # | Deliverable | Kind |
|---|---|---|
| D1 | `public.evidence_line_items` — new table (+ constraints, indexes, RLS, privilege posture) | Schema (B2-1) |
| D2 | `public.calculation_snapshots.source_line_item_id` — one additive nullable column + FK (`SET NULL`) + index | Schema (B2-2) |
| D3 | `public.disclosure_value_evidence.source_line_item_id` — one additive nullable column + FK (`SET NULL`) + index | Schema (B2-2) |
| D4 | Line materialisation (eligibility → rows), `payload_hash` canonicalisation, identity rules | Domain + data layer |
| D5 | Forward materialisation hook on the extraction write paths | Data layer (single choke point, §12.1) |
| D6 | Class-1 historical backfill operation (idempotent, dry-run, run report) — **execution separately authorised** | Data layer + operational tool |
| D7 | Calculation integration: populate `source_line_item_id` in both calculation paths | Service/engine boundary |
| D8 | `link_value_evidence(..., source_line_item_id=…)` extension on the B1 repository (additive kwarg) | Data layer |
| D9 | Audit emission for materialisation and backfill through the existing `audit_trail` | Data layer |
| D10 | Static + runtime + clone-based verification suite (V2) | Tests |
| D11 | Bounded amendment of the two invalidated B1 test-scope assertions (§20.6) | Tests |

**Not a deliverable:** any user-facing evidence drill-down UI or new HTTP endpoint (§12.4, decision B2-D9).

### 5.3 Acceptance criteria (gate **V2**, restated as testable statements)

| # | Criterion | Measured by |
|---|---|---|
| A1 | `evidence_line_items` rows exist for every eligible item and are **addressable** (a snapshot/evidence row can reference one) | runtime |
| A2 | `calculation_snapshots.source_line_item_id` **links** a calculation to its exact line where the line exists | runtime |
| A3 | Rerunning materialisation is **idempotent**: zero new rows, zero mutations, zero deletes | runtime (before/after hashes) |
| A4 | Rerunning is **non-destructive**: no existing row is updated or deleted; no historical snapshot/evidence row changes | runtime + clone |
| A5 | Rows that cannot be honestly derived stay **unmaterialised**; `source_line_item_id` stays **NULL**; completeness stays PARTIAL/UNAVAILABLE | runtime |
| A6 | **No re-extraction occurred** — no OCR/LLM/parse call, no `extracted_data` write, no queue reprocessing | static (call-graph) + runtime (row/JSONB hashes) |
| A7 | Tenant isolation and the PE boundary hold for B2 reads (ALLOW **and** DENY) | runtime RLS |
| A8 | B2 migrations are **idempotent** (apply twice = `rc=0`, no diff) and **additive-only** | migration + clone |
| A9 | The 116 pre-existing tables' table-level grants/policies/RLS are **unchanged**; the only deltas are the declared ones | clone harness |
| A10 | The full pre-existing test suite is green (with §20.6 amendments and no other regression) | pytest |

---

## 6. Root boundary — workstreams B2 must NOT absorb

These are **separate** workstreams. Each is listed with the reason it is excluded and the interface (if any)
B2 must leave open for it.

| Workstream | Why it is not B2 | Interface B2 leaves open |
|---|---|---|
| **P1 — PDF/IMAGE extraction fidelity (8→1)** | Root cause is upstream extraction, not provenance (forensic §18–§20). Fixing it inside B2 would make B2 an extraction batch. | The optional per-line element keys `page`, `line_reference` (§11.7) — declared, unused, no extractor changes. |
| **P2 — EF-E factor matching** | Independent defect; B2 changes no matching behaviour. | None (no coupling). |
| **B3 — disclosure integration / projections / intensity** | B3 consumes B2; it must not be pre-implemented. | D2/D3 columns make B3's value→line enumeration a **join, not a schema change**. |
| **B4 — narrative / finalisation / frozen artefacts** | Later batch. | B2 records nothing about narrative; the frozen artefact will inherit line links through snapshots. |
| **Phase 8-X (X1/X2)** | Separate namespace, separate gate. | None. |
| **Broad production RLS remediation** | Held separately (G0-H). B2 adds **its own** posture only. | A reusable pattern (B2-1/R-1) that the remediation workstream may copy. |
| **Legacy report route remediation** | D16/LEG workstream. | None. |
| **Subscription / allowance provisioning** | Commercial scope. | None. |
| **Customer-shaped end-to-end calculation evidence** | Requires P1 + B3. | None. |
| **Full ESRS/CSRD implementation** | Requirement content, not addressability. | None. |
| **Retention execution (N3)** | Configurable retention is a separate control-plane capability. B2 neither deletes nor schedules deletion, and must not hard-block retention (§15.3, B2-D11). | The line table is retention-tractable (a plain, indexed, org-scoped table). |
| **`source_page` honesty fix (F-B2-7)** | Evidence-classification defect in the *automatic* write path; changing it alters existing classifications. | Surfaced as decision **B2-D4**; B2 simply never copies the value. |
| **`mapped_data.line_items` mapping-provenance loss (F-B2-4)** | Independent observation about an existing write path. | Recorded; excluded (no B2 dependency). |

**Prohibitions carried forward from governance (binding on B2):**

1. No silent historical PDF/IMAGE re-extraction (`DM-7` §6 refinement 3).
2. No fabrication of line-level precision where the source does not support it (`DM-7` §6 refinement 4;
   Decision Record §10.2 honesty invariant).
3. No rewrite of an existing row to manufacture provenance (`DM-7`; P8X §15).
4. No change to the calculation engine, the factor-matching engine, or the report lifecycle spine.
5. No new authorization mechanism and no new audit mechanism.

### 6.1 PDF/IMAGE extraction remediation — separate future investigation workstream (PO clarification, 2026-09-13)

The Product Owner has **separately decided** that the established PDF/IMAGE extraction problem
(`CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912`: an 8-line PDF invoice can become one flattened extracted
object because the deterministic PDF path selects a single activity/quantity/unit record and can bypass AI
line extraction when completeness scores as sufficient) is to be investigated as its **own bounded
workstream** — previously labelled **P1**.

**This is a workstream record only. It authorises nothing and it is not part of B2.** No extraction code,
prompt, gate, OCR setting or `source_page` behaviour may be changed by B2 or by the ratification task.

The separate investigation must answer (and must be issued as its own OHD/Cline forensic+architecture task):

1. What should the canonical PDF/IMAGE line-extraction architecture be?
2. When should deterministic extraction produce **multiple** lines?
3. When should **AI** extraction be invoked?
4. How should extraction **completeness** be scored for multi-line documents?
5. How should **OCR text and layout** information be used?
6. How can **source line identity** be preserved?
7. How should **page number and source-location semantics** be represented correctly (this is the F-B2-7
   concern — §27.1)?
8. How should **confidence/ambiguity** be represented?
9. How should **extraction corrections** affect provenance?
10. How should **historical documents** be handled (no silent re-extraction)?
11. How can extraction fidelity improve **without corrupting existing provenance**?
12. What is the **exact boundary** between extraction output and B2 evidence-line materialisation?

**B2's only relationship to this workstream** is the declared interface already in §11.7 (optional per-line
`page`, `line_reference`, `extraction_method` element keys that a future extractor *may* emit). B2 requires
**no** extractor change, and the extraction workstream must not be used as a reason to widen B2's scope.

---

## 7. Data model — `public.evidence_line_items`

### 7.1 Exact schema (normative)

```sql
CREATE TABLE IF NOT EXISTS public.evidence_line_items (
    id                   uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id      uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    source_item_id       uuid NOT NULL
                             REFERENCES public.manual_extraction_items(id) ON DELETE RESTRICT,  -- B2-D1
    source_file_id       uuid          REFERENCES public.organization_files(id) ON DELETE SET NULL,
    line_number          integer NOT NULL,                     -- 1-based ordinal in the persisted array
    source_page          integer,                              -- ONLY a genuine per-line page; else NULL
    row_reference        text,                                 -- ONLY a genuine printed reference; else NULL
    raw_description      text,                                 -- source activity/description, as extracted
    raw_quantity         numeric,                              -- source quantity, as extracted
    raw_unit             text,                                 -- source unit, as extracted (pre-normalisation)
    payload_hash         text NOT NULL,                        -- sha256 of the canonical line payload
    extraction_method    varchar NOT NULL DEFAULT 'unknown',   -- producing path where provable; else 'unknown'
    materialisation_kind varchar NOT NULL,                     -- 'FORWARD' | 'BACKFILL'
    created_at           timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT evidence_line_items_line_number_check CHECK (line_number >= 1),
    CONSTRAINT evidence_line_items_source_page_check
        CHECK (source_page IS NULL OR source_page >= 1),
    CONSTRAINT evidence_line_items_kind_check
        CHECK (materialisation_kind IN ('FORWARD', 'BACKFILL')),
    CONSTRAINT evidence_line_items_identity_unique UNIQUE (source_item_id, line_number)
);

CREATE INDEX IF NOT EXISTS idx_eli_org ON public.evidence_line_items (organization_id);
CREATE INDEX IF NOT EXISTS idx_eli_source_file ON public.evidence_line_items (source_file_id);
-- (the (source_item_id, line_number) index is provided by evidence_line_items_identity_unique)
```

`extensions.uuid_generate_v4()` mirrors the B1 foundation migration.

**B2-D1 is CLOSED (PO-RATIFIED): `source_item_id` uses preservation-first referential semantics —
`ON DELETE RESTRICT`, never `CASCADE`.** An extraction item **cannot be deleted while its evidence lines
exist**; automatic cascading destruction of evidence-line provenance is **prohibited**. Evidence-line records
are authoritative historical provenance records, and the fact that the current application has no real
extraction-item deletion path (`delete()` is a no-op stub) does **not** justify destructive FK semantics. B2
introduces **no** deletion or anonymisation workflow of its own: if a future deletion/anonymisation workflow is
required, it must be separately designed and authorised under the retention/privacy workstream (§15.3, §27.3).

**Semantics fixed by this contract (no implementation discretion):**

* `line_number` = the 1-based position of the element in `extracted_data.line_items[]` **as persisted at
  materialisation time**. Gaps are permitted and must be preserved when an element is ineligible (§11.3) —
  an ordinal is **never** renumbered.
* `source_page` and `row_reference` are **NULL unless the persisted element genuinely carries the fact**
  (interface in §11.7). They are never derived from `page_count`, never inferred, never guessed.
* `payload_hash` covers only the recognised line-payload keys (§11.2) and **never** `created_at`,
  `materialisation_kind`, `extraction_method`, `organization_id` or `id`.

### 7.2 Column-by-column justification (every column earns its place)

| Column | Purpose (why it must exist) | Provenance rationale |
|---|---|---|
| `id` | The **addressable identity** — the FK target of `calculation_snapshots.source_line_item_id` and `disclosure_value_evidence.source_line_item_id`. This is the point of B2. | Design §14.3; `DM-7`; readiness §15/§20; G0-E |
| `organization_id` | Tenant scope for RLS and for org-scoped reads **without a join chain** (the parent has no `organization_id`, F-B2-8). | Design §14.3 + §18.2 (“`organization_id` NOT NULL for every row carrying organisation data”); repo convention `20260831030000` |
| `source_item_id` | Anchors the line to its **existing document-level parent** (never duplicates it); the join key to `extracted_data`, `file_id`, tenant, PE scope and status. | Design §14.3; D33 chain |
| `source_file_id` | Document identity, denormalised exactly as B1 denormalised it, so drill-down needs no join chain; `SET NULL` preserves the line if the file row is removed. | Design §13.2/§14.3; D33 `SET NULL` philosophy |
| `line_number` | The **deterministic identity component** and the ordering. Equal to the 1-based position of the record in persisted `extracted_data.line_items[]` — the same key the calculation layer already uses implicitly (F-B2-2/F-B2-3). | F-B2-2/F-B2-3; `DM-7` (deterministic, idempotent) |
| `source_page` | The **exact location** of the line when the source records one; required by the ratified chain (“INV-123, page 2, line 3”) and by `domain/evidence.py`’s COMPLETE/PARTIAL rule. NULL until a producer exists. | Design §14.3; D33.1 |
| `row_reference` | The **human-facing reference printed on the source** (invoice line ref, meter point, txn id) — only where the source carries one. | Design §14.3, §14.4 honesty rule |
| `raw_description`, `raw_quantity`, `raw_unit` | The line’s **source values as extracted**, never overwritten — so a reader/auditor can verify the calculation against the line **without re-reading mutable JSONB**, and the row stays meaningful after `extracted_data` is later corrected. | Design §14.3 (“original source values, never overwritten”); D15 |
| `payload_hash` | (a) deterministic fingerprint of exactly which payload was materialised; (b) the **divergence detector** on rerun (§11.4); (c) tamper-evidence. | Design §14.3; `DM-7` acceptance |
| `extraction_method` | Records **which extraction path produced the line** (forward: the pipeline’s real stamp; backfill: document-level attribution or `unknown`). Never fabricated. | Design §14.3; F-B2-15 |
| `materialisation_kind` | Separates rows captured **at extraction time** from rows **derived later from persisted JSONB** — the honesty signal `DM-7` requires (a backfilled PDF-era line is not line-verified by extraction) and the filter axis for P1 sequencing. | `DM-7` Gate-0 refinement; P8X §15 class-1/class-2 split |
| `created_at` | Row-level forensic timing (when the line became addressable); distinguishes forward and backfill runs in time. Excluded from identity and from `payload_hash`. | Observability (`AGENTS` §77) |

### 7.3 Considered and deliberately **rejected** columns

| Rejected candidate | Origin of the idea | Why rejected |
|---|---|---|
| `processing_origin`, `processing_entity_id` | Design §14.3 (`processing_origin`) | **Divergence risk.** The parent’s origin/entity is *mutable* after materialisation — `mark_pe_origin_if_unset(item_id, entity_id)` sets it when a PE user first processes the item (`v3_operations.py:1080-1092`). A copy can therefore become **wrong**. The line’s origin is by construction the parent’s; derive it at read time through the NOT-NULL `source_item_id`. |
| `document_type_code` | Design §14.3 | A **document** attribute already on `manual_extraction_items.document_type`; copying it per line adds bytes, no addressability, and a second fact to keep in sync. |
| `confidence_score` | Design §14.3 | No extractor produces per-line confidence today (both deterministic and AI paths score at document level) — the column would be permanently NULL, i.e. a column with no purpose. |
| `extracted_at`, `extracted_by` | Design §14.3 | Item-level facts already persisted on `manual_extraction_items`; per-line copies duplicate a document fact. |
| `source_line_payload jsonb` (whole element) | — | Duplicates the JSONB wholesale (storage, and a second copy of data B2 does not need to address). `payload_hash` + the three raw scalars are sufficient for verification; the element remains reachable via `source_item_id`. |
| `line_items_materialised_at` / `_digest` on `manual_extraction_items` | — | A marker is a **second fact that can drift** from the JSONB it describes. Eligibility/completeness are derivable set-wise (anti-join on the unique identity), so a marker buys operability only by reintroducing the divergence class B2 exists to prevent. |
| `updated_at` | — | Rows are immutable by design (§15); `updated_at` is a false affordance. |
| `is_active` / soft-delete flag | — | No B2 delete semantics exist; retention is a separate workstream (B2-D11). |

### 7.4 Deviations from design §14.3 (explicit; for PO confirmation)

Design §14.3 is the ratified field list. B2 keeps its naming and intent, with four **bounded reductions** and
two **bounded additions**. Each is argued above; none weakens a ratified requirement.

| Change | Direction | Reason | Confirmation needed |
|---|---|---|---|
| Drop `document_type_code`, `confidence_score`, `extracted_at`, `extracted_by` | reduction | Document-level facts (already persisted on the parent) or facts with **no producer** — they would be permanently NULL or duplicated | PO confirm (non-blocking) |
| Drop `processing_origin` | reduction | Mutable parent attribute ⇒ copying creates provable divergence (`mark_pe_origin_if_unset`) | PO confirm (non-blocking) |
| Add `materialisation_kind` | addition | `DM-7` honesty signal: forward-captured vs derived-later | PO confirm (non-blocking) |
| Add `created_at` | addition | Row-level forensic timing | Implementation (non-blocking) |
| `source_item_id` delete rule: `ON DELETE RESTRICT` (preservation-first) | literal | Provenance-vs-hygiene choice | **B2-D1 CLOSED** |

Design §14.3’s `organization_id`, `source_item_id`, `source_file_id`, `source_page`, `line_number`,
`row_reference`, `raw_quantity`, `raw_unit`, `raw_description`, `payload_hash`, `extraction_method` are all
**retained as named**.

### 7.5 Canonicality: JSONB vs normalised rows (deliverable F)

**[PO-RATIFIED core architecture] The hybrid model is deliberate and must be documented as such — it is not
two competing sources of truth, because the two artefacts answer different questions:**

| Artefact | Role | Mutable? | Authority |
|---|---|---|---|
| `manual_extraction_items.extracted_data->'line_items'` | **What the extractor produced** (extraction output) | Yes — rewritten by correction paths (G6-D) until downstream freeze | Sole **eligibility source** for materialisation |
| `public.evidence_line_items` | **Durable, addressable line identity + the source values as extracted at that moment** | **No** (append-only in B2) | The **provenance/evidence** authority: the thing a snapshot/evidence/report points at |

Rejected alternatives and why:

1. **JSONB canonical + merely assign references** — impossible: a JSONB array element has no stable
   addressable identity; any "reference" would be positional into mutable data, which breaks D15 the moment
   a correction rewrites the array.
2. **Normalised rows canonical (extraction writes rows instead of JSONB)** — a destructive re-architecture of
   the extraction/pipeline contract (P1 territory), not B2. B2 **must not** change what extraction persists.
3. **Hybrid (chosen)** — rows are a **derived, immutable materialisation** with a recorded payload hash and a
   recorded kind (`FORWARD`/`BACKFILL`); the JSONB stays untouched and remains the source of eligibility.

### 7.6 Delete and immutability semantics of line rows

* **No B2 write path updates or deletes a line row.** The repository exposes insert-only materialisation plus
  reads. No `UPDATE`/`DELETE` statement for `evidence_line_items` exists in the B2 data layer.
* **DB enforcement is by privilege posture** (mirroring B1’s corrected posture): `anon` revoked entirely;
  `authenticated` granted `SELECT` only, with `INSERT/UPDATE/DELETE/TRUNCATE/TRIGGER/REFERENCES/MAINTAIN`
  revoked; `service_role` retains `ALL` (the backend is the writer).
* **B2 introduces no retention or deletion mechanism at all (B2-D11, PO-RATIFIED).** No soft-delete field, no
  retention trigger, no automatic purge, no anonymisation logic and no deletion job exists in B2. Evidence-line
  records are immutable provenance records. A hard `BEFORE UPDATE OR DELETE` trigger (the P7 `audit_trail`
  pattern) is deliberately **not** added either: a trigger would itself be a deletion-semantics mechanism, and
  the PO has ruled that N3 / the separate retention+privacy workstream defines any future retention, deletion
  or anonymisation semantics for evidence lines. The V2 suite therefore tests the **privilege posture** and the
  **RESTRICT behaviour** (explicit, verifiable behaviours), not trigger behaviour.
* **Consumer links are non-destructive; the line's own parent link is restrictive.** The two B2 consumer links
  (`calculation_snapshots.source_line_item_id`, `disclosure_value_evidence.source_line_item_id`) and
  `source_file_id` are `ON DELETE SET NULL`, so a downstream record never loses its row if a referenced parent
  is removed — exactly the D33 philosophy. The line table's parent link (`source_item_id`) is
  **`ON DELETE RESTRICT`** (B2-D1), so the line itself can never be silently destroyed as a consequence of
  deleting its parent.

---

## 8. Calculation snapshot linkage — `calculation_snapshots.source_line_item_id`

### 8.1 Exact definition (normative)

```sql
ALTER TABLE public.calculation_snapshots
    ADD COLUMN IF NOT EXISTS source_line_item_id uuid;

ALTER TABLE public.calculation_snapshots
    ADD CONSTRAINT calculation_snapshots_source_line_item_id_fkey
    FOREIGN KEY (source_line_item_id) REFERENCES public.evidence_line_items(id)
    ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_calculation_snapshots_source_line_item
    ON public.calculation_snapshots (source_line_item_id);
```

| Property | Value | Rationale |
|---|---|---|
| Type / nullability | `uuid`, **nullable** | A calculation may legitimately have no line (manual entry, flat PDF record, line not materialised). Nullability *is* the honesty mechanism. |
| FK target | `public.evidence_line_items(id)` | The addressable line identity. |
| Delete rule | **`ON DELETE SET NULL`** | Mirrors `calculation_snapshots_source_item_id_fkey` exactly; an immutable historical snapshot must never be destroyed and must never cascade. |
| Index | `idx_calculation_snapshots_source_line_item` | Reverse trace (line → calculations) and the population check become indexed lookups. |
| Existing columns | **untouched** | `source_item_id`, `source_file`, `source_page`, `content_hash`, … are not renamed, repurposed or rewritten. |

### 8.2 When it MUST be populated / MUST remain NULL

**Populated** when all hold:

1. the calculation is one of the N line calculations of a document whose `extracted_data.line_items[]`
   contained ≥ 1 eligible element at calculation time; and
2. a materialised `evidence_line_items` row exists for `(source_item_id, line_number = idx + 1)`; and
3. that row’s `source_item_id` equals the snapshot’s `source_item_id`.

**NULL** when any holds:

* the document was calculated as a **flat record** (`targets = [dict(extracted)]`, i.e. no `line_items[]`) —
  **no synthetic line row is ever created for it** (fabrication prohibition);
* no `evidence_line_items` row exists for that ordinal (item not yet materialised, eligibility failure, or
  that element was ineligible);
* the calculation is manual/ad-hoc with no source item at all;
* materialisation happened **after** the snapshot was written and no explicit re-link occurred — B2 does
  **not** rewrite historical snapshots (§15.2).

### 8.3 Coexistence with `source_item_id` (ambiguity is not tolerated)

* Both columns may be set simultaneously; they are **complementary levels of one chain** (document-level vs
  line-level), not alternatives. `source_line_item_id` is the **finer** fact.
* **Consistency invariant (application-enforced, test-verified):** when `source_line_item_id IS NOT NULL`,
  `source_item_id` must equal that line’s `source_item_id`.
* A **composite FK** enforcing this in the database was evaluated and **rejected**: it would require a
  redundant `UNIQUE (id, source_item_id)` on the line table and — decisively — PostgreSQL’s
  `ON DELETE SET NULL` on a composite FK nulls **all** participating columns, so it would also null
  `source_item_id` and destroy document-level provenance. Documented, not silently accepted.
* Ambiguity is represented by **NULL**, never by a sentinel UUID. The zero-UUID is used elsewhere in the
  codebase only as a *machine actor* marker and must not be repurposed as a “no line” sentinel here.

### 8.4 Immutability / reproducibility

* The snapshot stays immutable: B2 **sets the column value at insert time** and never updates a snapshot row.
* `content_hash` is computed by the engine (`CalculationSnapshot.build_content_hash()` → `_canonical()`).
  B2 may include the new provenance field in **new** snapshots only; existing snapshots are neither
  re-derived nor re-hashed.
* **The deterministic request-id derivations (F-B2-3) must NOT include `source_line_item_id`.** Otherwise a
  snapshot written before materialisation and re-requested after it would hash differently and produce a
  **duplicate** calculation — directly violating `DM-7` acceptance and the `V2` criterion “rerun = no dupes”.
  This is an explicit, test-enforced prohibition.

---

## 9. Evidence linkage — `disclosure_value_evidence.source_line_item_id`

### 9.1 Exact definition (normative)

```sql
ALTER TABLE public.disclosure_value_evidence
    ADD COLUMN IF NOT EXISTS source_line_item_id uuid;

ALTER TABLE public.disclosure_value_evidence
    ADD CONSTRAINT disclosure_value_evidence_source_line_item_id_fkey
    FOREIGN KEY (source_line_item_id) REFERENCES public.evidence_line_items(id)
    ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_dve_source_line_item
    ON public.disclosure_value_evidence (source_line_item_id);
```

This additive column is **already sanctioned** by the ratified B1 contract (line 413): *“B2 additive
extension (not in B1): `ALTER TABLE disclosure_value_evidence ADD COLUMN IF NOT EXISTS source_line_item_id
uuid → evidence_line_items(id) ON DELETE SET NULL`”* [D].

### 9.2 Why the column exists rather than relying on the snapshot join

1. **It follows B1’s own denormalisation precedent.** B1 already denormalises `source_item_id`,
   `source_file_id` and `source_page` onto `disclosure_value_evidence` precisely so the report→evidence
   enumeration needs no join chain (design §13.2). `source_line_item_id` is the same pattern one level finer.
2. **A `disclosure_value_evidence` row may reference evidence without a calculation snapshot** (the
   emissions-log path, and manual/`CUSTOMER_INPUT` evidence) — for those rows the snapshot join cannot supply
   a line at all.
3. **B3 must be able to enumerate value→line deterministically in one hop**; forcing a three-table join into
   every B3 read would push a schema fact into B3’s query layer.

**Divergence risk and mitigation:** because the fact is denormalised, the write path must set it from the
snapshot (or from the line) and must never invent it. A test asserts that for every row where both
`source_line_item_id` and `calculation_snapshot_id` are non-NULL, `dve.source_line_item_id` equals the
snapshot’s `source_line_item_id`.

### 9.3 What B2 does **not** change in B1

* `link_value_evidence` gains exactly one **optional keyword argument** `source_line_item_id=None`; existing
  callers and behaviour are unchanged.
* The B1 constraint `disclosure_value_evidence_unique (disclosure_value_id, calculation_snapshot_id)` and the
  NULL-safe index `uq_dve_reference_nullsafe` are **not modified**. Since the NULL-safe index does not include
  the new column, two rows differing *only* by line cannot be created for one (value, snapshot, …) tuple —
  which is correct: **one snapshot is one line**, so a snapshot can never legitimately appear twice for one
  value with different lines.
* **Cardinality for the multi-line case already works:** one disclosure value → **n** evidence rows → **n**
  snapshots → **n** lines. “One disclosure value supported by several lines” needs **no** bridge table.
* The B1 audit action `report:disclosure_evidence_linked` continues to describe the link write; no new action
  is needed for the column.
* **No B1 migration file is edited** (§18.3).
* B1’s document-level evidence remains valid and complete: a `disclosure_value_evidence` row with
  `source_line_item_id IS NULL` and a valid `source_item_id`/`source_file_id`/`source_page` still describes
  document-level provenance **honestly** (design §13.2, §14.4).

### 9.4 Evidence-layer objects B2 does NOT introduce

| Considered | Verdict | Reason |
|---|---|---|
| A new bridge table (value ↔ line) | **Rejected** | `disclosure_value_evidence` already is that table; adding a parallel bridge would be a duplicate model (AGENTS §4). |
| Modifying `emissions_logs` | **Rejected** | It already reaches a line **through** `snapshot_id → calculation_snapshots.source_line_item_id`. No new column needed; adding one would duplicate a derivable fact. |
| Changing `domain/evidence.py` classification rules | **Rejected** | D33.1 already classifies honestly; B2 supplies the line hop, and the classification continues to use document/item/calculation/factor/page. Whether a *line* should elevate the class is a **B3/B4 presentation question** (`DM-6` drill-down), not an addressability question. |
| Populating `extraction_method`/other facts on `emissions_logs` | **Rejected** | Out of B2 scope. |

---

## 10. Authoritative provenance chain (forward and reverse)

### 10.1 Forward trace — report → source line

```text
report_generation_queue.id                                  (report instance)          [exists]
  → report_versions   (report_id, version_number, status)                               [exists]
     → disclosure_values            (requirement_version_id, value_status, …)          [exists — B1]
        → disclosure_value_evidence (value → evidence enumeration)                      [exists — B1]
           → calculation_snapshots  (immutable result + factor provenance)              [exists]
              ├── source_item_id       → manual_extraction_items  (document level)      [exists — D33]
              │      └── file_id       → organization_files       (storage object)       [exists — D33]
              └── source_line_item_id  → evidence_line_items      (EXACT LINE)           [NEW — B2-2]
                     └── source_item_id → manual_extraction_items (parent document)     [NEW — B2-1]
```

### 10.2 Reverse trace — source document → reports that used it

```text
organization_files → manual_extraction_items → evidence_line_items             [NEW — B2-1]
   → calculation_snapshots (source_line_item_id)                               [NEW — B2-2]
      → emissions_logs (snapshot_id)                                           [exists]
      → disclosure_value_evidence (calculation_snapshot_id / source_line_item_id)  [B1 + NEW column]
         → disclosure_values → report_versions → report_generation_queue       [exists — B1/lifecycle]
```

Both directions are index-supported: `idx_calculation_snapshots_source_line_item`,
`idx_dve_source_line_item`, the line identity unique index, plus the pre-existing
`idx_calculation_snapshots_source_item`, `idx_dve_calc`, `idx_dve_source_item`.

### 10.3 Which links are already authoritative vs new in B2

| Link | Status | Note |
|---|---|---|
| `organization_files ← file_id ← manual_extraction_items` | **Existing (D33)** | Untouched |
| `manual_extraction_items ← source_item_id ← calculation_snapshots` | **Existing (D33)** | Untouched; remains the document-level fallback |
| `calculation_snapshots ← snapshot_id ← emissions_logs` | **Existing** | Untouched |
| `disclosure_value_evidence → disclosure_values` | **Existing (B1)** | Untouched |
| `disclosure_value_evidence → calculation_snapshots / emissions_logs / manual_extraction_items` | **Existing (B1)** | Untouched |
| **line identity** (`evidence_line_items`) | **NEW (B2-1)** | The addressable line |
| **snapshot → line** (`calculation_snapshots.source_line_item_id`) | **NEW (B2-2)** | The calculation-to-line hop |
| **evidence → line** (`disclosure_value_evidence.source_line_item_id`) | **NEW (B2-2)** | The value-to-line hop |

### 10.4 The honesty rule (binding)

Where no line identity genuinely exists, the chain **stops at document level** and the evidence record is
classified `PARTIAL`/`UNAVAILABLE` by the existing D33.1 logic. The document-level chain
(`source_item_id`/`source_file_id`/`source_page`) remains **authoritative and sufficient** for those records.
**No synthetic line row, placeholder row, or sentinel UUID may be created to make the chain look complete**
(`DM-7` §6 refinement 4; Decision Record §10.2).

---

## 11. Materialisation rules (forward + Class-1 historical backfill)

### 11.1 Eligibility (normative; identical for forward and backfill)

An extraction item is **eligible for line materialisation** iff:

```sql
extracted_data IS NOT NULL
AND jsonb_typeof(extracted_data -> 'line_items') = 'array'
AND jsonb_array_length(extracted_data -> 'line_items') >= 1
```

Per element, **in array order**, with ordinal `i = index + 1`:

| Element condition | Action |
|---|---|
| JSON object with ≥ 1 recognised key (§11.2) carrying a non-empty value | **Materialise** at `line_number = i` |
| JSON object with **no** recognised key carrying a value (degenerate/empty) | **Skip**; ordinal becomes a **gap**; count `skipped_empty` |
| Not a JSON object (string/number/null/array) | **Skip**; ordinal becomes a **gap**; count `skipped_malformed` |
| `line_items` present but **empty array** `[]` | Item materialises **0** rows; count `skipped_no_lines`; **never** falls back to the flat record |
| `line_items` absent / not an array / item has no `extracted_data` | Item **ineligible**; 0 rows; document-level provenance only |

**Ordinals are never renumbered.** If element 3 is skipped, elements 4…n keep their positions, so later
content changes cannot silently change what “line 3” means.

### 11.2 Deterministic derivation (normative)

* **Recognised keys** — the union of what the extractors actually emit (F-B2-5/F-B2-6): `activity`,
  `description`, `item`, `quantity`, `unit`, `amount`, `currency`, `supplier`, `date`, `invoice_number`.
* `raw_description` = first non-empty of `activity`, `description`, `item` (string, as extracted).
* `raw_quantity` = `quantity` when it parses as a decimal; otherwise **NULL**.
* `raw_unit` = `unit` when non-empty; otherwise **NULL** — as extracted, i.e. **pre-normalisation** (unit
  aliasing is `core.units`’ job and must not be duplicated here — AGENTS §23).
* `payload_hash` = `sha256(canonical_json(payload))`, where `payload` is the element restricted to recognised
  keys with non-empty values, canonicalised as: keys sorted; compact separators; UTF-8; numbers normalised via
  `format(Decimal(str(v)).normalize(), "f")` (so `100`, `100.0`, `100.00` hash identically — int/float drift
  must not create a *false* divergence); non-scalar values for a recognised key omitted.
* `extraction_method`:
  * **FORWARD** — supplied by the write site (the pipeline’s real stamp: `csv`, `xlsx`, `pdf_text`,
    `tesseract_ocr`, `onnx_ocr`, `ai`, compound `"{deterministic}+{ai}"`; or `manual` for human data-entry);
    `unknown` when the site cannot supply it.
  * **BACKFILL** — **document-level** attribution in priority order:
    `document_processing_queue.ai_extraction_method` (via `document_processing_queue_id`) →
    `manual_extraction_batches.ai_extraction_method` (via `batch_id`) → `unknown`. A document-level fact
    applied to that document’s lines; never guessed (F-B2-15).
* `materialisation_kind` = `FORWARD` (extraction-write hook) or `BACKFILL` (backfill operation).
* `organization_id` = the parent batch’s `organization_id`, resolved **server-side**, never caller-supplied.
  `source_file_id` = the parent’s `file_id` (NULL where D33’s exact-path backfill found no match).
* `source_page` / `row_reference` remain NULL unless the element genuinely carries them (§11.7).
  `page_count` is **never** used as a page (F-B2-7).

### 11.3 Idempotency, rerun and conflict behaviour (normative)

Per candidate ordinal: **insert if absent; skip if present** — never update:

```sql
INSERT INTO public.evidence_line_items (…)
VALUES (…)
ON CONFLICT (source_item_id, line_number) DO NOTHING;
```

| Rerun situation | Required behaviour |
|---|---|
| Row exists, hash identical | No-op (not counted as a write) |
| Row exists, hash **different** (persisted element changed after materialisation) | **DIVERGENCE** — no write, no update, no delete; count and report per ordinal; leave the historical row intact |
| Row missing for an ordinal eligible now | Insert it (a partially-completed run is resumable) |
| Row missing for an ordinal ineligible now | Nothing |
| Item no longer eligible but rows exist | Rows are **not** deleted (immutability) |

`DO NOTHING` is **deliberately not** B1’s `DO UPDATE`: a B1 disclosure value is mutable while its report
version is mutable, whereas a line row is **immutable evidence** — rewriting it would be exactly the
“rewrite to manufacture provenance” `DM-7` prohibits. Divergence is detected and reported, never reconciled
in place (→ **B2-D2, CLOSED: detect + report + never rewrite**).

### 11.4 What the Class-1 backfill may and may not do (deliverable E)

**May:** read `manual_extraction_items` rows (plus their batch/queue method stamps) **read-only**; insert rows
where §11.1 holds and no row exists for the ordinal; run in **dry-run** (identical counts, zero writes); run
in batched, resumable, keyset-paginated passes (by `manual_extraction_items.id`); emit a **run report**
(scanned / eligible items / materialised rows / per-category skips / divergences).

**May not:** re-run any extraction, OCR, LLM, parser or heuristic; write to `manual_extraction_items`,
`document_processing_queue`, `extracted_data`, `mapped_data`, `calculation_snapshots`, `emissions_logs` or any
report table; read `mapped_data` for identity (F-B2-4); delete, update or renumber anything; derive lines from
aggregate fields of a flat record (**manufacturing granularity — explicitly prohibited**); infer missing
invoice lines.

**Mechanism [REC]:** the backfill is **NOT a migration**. It is an explicitly-invoked, offline, idempotent
operation (service/repository function + thin CLI entry point placed with the existing operational tooling,
alongside `backend/tools/enforce_retention.py`). Rationale: (a) migrations must stay fast and atomic while
backfill volume is unknown and the investor-demo dataset is large; (b) `DM-7` requires *demonstrable*
idempotency and non-destructiveness, which a re-runnable command plus run report proves better than a one-shot
migration; (c) a migration that both alters schema and creates large volumes of evidence data is materially
harder to review and to reverse. **Execution against any environment is separately authorised**; production is
**not** authorised by B2.

### 11.5 Records that are explicitly NOT backfillable (Class 2/3/4)

| Class | Records | Treatment |
|---|---|---|
| 2 | Flat PDF/IMAGE records with no persisted `line_items[]` | **No rows.** Document-level provenance only; `source_line_item_id` stays NULL; evidence stays PARTIAL/UNAVAILABLE. Requires the separately-authorised P1 re-parsing capability (`DM-7`) — **never silent** |
| 3 | Records with OCR/text available but no persisted lines | Same as class 2. No text re-parse in B2 |
| 4 | Records without sufficient source representation (e.g. a single manually-entered figure) | No line claim. If a single-line synthetic record is ever needed, it is a **B3/B4 presentation** concern and still must not fabricate a `row_reference` (Decision Record §10.2) |
| — | Items with no `extracted_data` at all | Ineligible |

### 11.6 Forward vs backfill coverage and the safety net

Forward materialisation covers new writes through the hook (§12.1). Anything missed (a path that bypasses the
hook, a pre-B2 historical row, or a partially-completed run) is covered by the idempotent backfill, which is
**safe to run repeatedly** and **rows are identical whichever path created them** (the only difference is
`created_at` and `materialisation_kind`). There is therefore **no requirement** for a marker of
“already materialised”: eligibility is a pure function of the persisted JSONB plus the unique identity.

### 11.7 The declared interface for future extractors (P1 hook — declared, not implemented)

A future line-aware extractor may supply per-line location/provenance by adding **optional** keys to an
element of `extracted_data.line_items[]`. B2 reads them **if present** and **never requires** them:

| Optional element key | Type | B2 mapping | Current producers |
|---|---|---|---|
| `page` | integer ≥ 1 | `evidence_line_items.source_page` | **none** (so the column is normally NULL) |
| `line_reference` | non-empty string | `evidence_line_items.row_reference` | **none** |
| `extraction_method` | non-empty string | overrides the document-level attribution for that line | **none** |

Rules: an out-of-domain or malformed value is ignored (column stays NULL) rather than erroring; **no extractor
is modified by B2**; and no existing key’s meaning changes. This is the complete B2↔P1 interface — nothing
else in B2 depends on extraction behaviour.

---

## 12. API / service boundary (deliverable G)

### 12.1 Write paths — where materialisation is invoked

**[PO-RATIFIED — B2-D6] Single choke point at the data layer** (`ManualExtractionRepository`), because all four
pipeline/API extraction writes already funnel through `save_extracted_data` (F-B2-9) and a single hook cannot
be forgotten:

| Site | Path | Change |
|---|---|---|
| `backend/data/manual_extraction.py::save_extracted_data` | shared by `automatic_processing.py:453`, `v3_operations.py:1086,1662`, `v3_processing_workflow.py:445` | After the parent UPDATE succeeds, best-effort materialisation of the just-persisted payload |
| `backend/data/manual_extraction.py::update_item(extracted_data=…)` | `PUT /manual-extraction/items/{item_id}` (`v3_manual_extraction.py:132`) | Same best-effort materialisation when `extracted_data` is supplied |
| Signature change | — | `save_extracted_data(..., extraction_method: Optional[str] = None)` — **additive keyword with a default**, so no existing caller breaks. The automatic pipeline passes its real `method_stamp`; human sites pass `"manual"` |

**Materialisation must be best-effort and non-blocking** (log-and-continue), exactly like the codebase’s
existing audit/notification pattern: an extraction save must **never** fail because evidence addressing
failed. Failures are covered by the backfill safety net (§11.6).

**Rejected alternative:** calling materialisation from each of the four API/pipeline call sites — it
duplicates logic and *guarantees* future omissions.

### 12.2 Read paths

New read-only repository functions (`backend/data/evidence_line_items.py`):

| Function | Purpose |
|---|---|
| `list_for_item(organization_id, source_item_id)` | Line rows of one document, ordered by `line_number` |
| `get(line_id)` | One line (used by evidence/drill-down consumers) |
| `get_by_ordinals(source_item_id, ordinals)` | The calculation integration’s ordinal→id resolve (§13) |
| `count_for_item(source_item_id)` | Population/eligibility audit |

All reads are organisation-scoped and must return rows **only** for the caller’s authorised organisation
(application-level authorization; RLS as defence-in-depth — §16).

### 12.3 Write semantics: creation, update, deletion

| Operation | B2 semantics |
|---|---|
| Create | Materialisation only (forward hook or backfill). **No public "create a line" endpoint/function** — a line is derived, never authored |
| Update | **Not supported.** No code path; rejected at RLS/privilege level |
| Delete | **Not supported in B2.** No code path; privileges deny it; retention is separate (B2-D11) |

### 12.4 Endpoints

**B2 adds no new HTTP endpoint.** Rationale: B2 delivers *addressability*, not user-facing drill-down (`DM-6`
drill-down depth is bounded by evidence granularity and belongs to B3/B4 presentation); inventing a B2 endpoint
would also force a premature API contract the governance has not ratified. The existing endpoints continue to
return exactly what they return today (no response-shape change) — so **no frontend work is required or
authorised** by B2.

If a later batch needs a read surface, it consumes `list_for_item`/`get` above; the schema already supports it.

---

## 13. Calculation integration (deliverable H)

### 13.1 The two calculation paths and exactly where the link is populated

| Path | Entry point | Line identity available today | B2 change |
|---|---|---|---|
| **Automatic pipeline** (queue worker) | `automatic_processing.py::_calculate_line(job, line, idx, …)` | `idx` (ordinal) + `job.source_item_id`; sets `source_item_id=job.source_item_id`, `source_file=job.file_name`, `source_page=job.metadata.get("page_count")` | Resolve `(job.source_item_id, idx+1)` → line id (via `get_by_ordinals`); pass it to `CalculationRequest` as `source_line_item_id` |
| **Operations/manual line calculation** | `v3_operations.py::_run_line_calculation(repos, engine, item, batch, payload)` | `idx` + `item.id`; sets `source_item_id=item.id`, `source_file=item.file_name` | Same resolve on `(item.id, idx+1)`; pass `source_line_item_id` |

`CalculationRequest` gains one **optional** field (`source_line_item_id: Optional[str] = None`) and
`CalculationSnapshot`/the snapshot persist path carries it into `calculation_snapshots.source_line_item_id`.
**No other engine behaviour changes** — no formula, factor selection, rounding, methodology, hash algorithm
or request-id derivation is touched (§8.4). **[PO-RATIFIED core architecture] No new calculation engine is created and none may be.**

### 13.2 Resolution rule (normative)

```
line_id = evidence_line_items.id WHERE source_item_id = <snapshot's source_item_id>
                                    AND line_number   = <ordinal>
```

* The resolve is a **lookup**, never an insert: the calculation path must **not** materialise lines itself
  (that would make calculation responsible for extraction-derived data and would run inside a locked stage
  transaction). If no row exists, the snapshot’s `source_line_item_id` is **NULL**.
* The resolve is index-backed by `evidence_line_items_identity_unique (source_item_id, line_number)`; it adds
  at most one indexed lookup per line calculation.
* The line’s ordinals are the same `idx` values already used for the deterministic request ids (F-B2-3), so
  the resolution is exact and requires no re-derivation of the array.

### 13.3 What B2 must NOT change in the calculation flow

* The deterministic request-id derivations (map and calc) — **must not** include `source_line_item_id`.
* The resume-marker behaviour (`if job.calculation_snapshot_id: → review`, `if job.mapped_data: → validating`)
  and the duplicate-prevention guard (`find_snapshot_by_request_id`).
* `source_file` / `source_page` population (including the F-B2-7 behaviour — deliberately unchanged here).
* Factor precedence, factor matching, unit resolution (`core.units`), methodology selection, `content_hash`
  inputs for existing snapshots.
* Any historical snapshot row (no backfill of `source_line_item_id` onto existing snapshots — §15.2).

### 13.4 Historical snapshots: honesty over retrofit-by-inference

Existing snapshots have `source_item_id` and (often) a document page-count in `source_page`. B2 must **not**
infer a line for them by re-deriving “which line produced this” from a quantity match — that is guessing, and
`DM-7` forbids manufacturing provenance. Historical snapshots therefore keep `source_line_item_id = NULL`
unless a future, separately-authorised, evidence-backed linkage task establishes it. The document-level
chain continues to carry them.

---

## 14. Report / disclosure integration boundary (deliverable I)

### 14.1 B2 vs B3 (explicit separation)

| Concern | Batch | B2 does |
|---|---|---|
| Durable line identity + links | **B2** | Implements (D1–D3) |
| Deterministic value→line enumeration **read model** | **B3** | Leaves to B3 — B2 only makes it a **one-hop join** |
| Framework/requirement/mapping/applicability/purpose/intensity | **B3** | Untouched |
| Narrative / finalisation / frozen artefact | **B4** | Untouched |
| Drill-down UI (`DM-6`) | **B3/B4** | Untouched |

### 14.2 The B3 join B2 makes possible (design target, not implemented here)

```sql
-- B3 will be able to enumerate a disclosure value's exact source lines:
SELECT dv.id AS disclosure_value_id,
       cs.id AS calculation_snapshot_id,
       eli.id AS evidence_line_item_id,
       eli.line_number, eli.source_page, eli.row_reference,
       eli.raw_description, eli.raw_quantity, eli.raw_unit,
       eli.materialisation_kind
  FROM public.disclosure_values dv
  JOIN public.disclosure_value_evidence dve ON dve.disclosure_value_id = dv.id
  LEFT JOIN public.calculation_snapshots cs ON cs.id = dve.calculation_snapshot_id
  LEFT JOIN public.evidence_line_items eli
         ON eli.id = COALESCE(dve.source_line_item_id, cs.source_line_item_id)
 WHERE dv.report_version_id = $1;
```

The `COALESCE` is intentional and safe: the snapshot link is the primary fact; the `dve` column carries the
denormalised same fact (and covers snapshot-less evidence).

### 14.3 Why a minimal B2 FK belongs in B2 rather than B3

* It is the **schema shape of the ratified chain** (design §22.2 diagram; `G0-E` scope), and shipping B3 without
  it would force B3 to open a schema migration — the exact cross-batch bleed the batch plan exists to prevent.
* It is **one additive nullable column per table** with no behaviour of its own, so it carries no B3 logic.
* B1 is untouched: the B1 contract already anticipated this column (line 413).

---

## 15. Immutability and historical reproducibility (deliverable J)

### 15.1 Mutable vs immutable

| Object | Mutability | Rule |
|---|---|---|
| `evidence_line_items` rows | **Immutable (append-only)** | Insert-only; no UPDATE/DELETE path; denied for `anon`/`authenticated` at the privilege level; and `source_item_id` is `ON DELETE RESTRICT` (B2-D1) so a parent delete cannot destroy the line |
| `evidence_line_items.source_item_id`, `line_number` | **Never changes** | The identity tuple is fixed at insert and enforced unique |
| `calculation_snapshots` rows | **Immutable** (already) | B2 sets the new column at insert; never updates |
| `disclosure_value_evidence` rows | Mutable **only** while the report version is mutable (B1 rule `PQ-4`/immutability) | B2 adds no new mutability; the new column follows the row’s existing rule |
| `manual_extraction_items.extracted_data` | Mutable until downstream freeze (existing behaviour) | **B2 does not change this** |

### 15.2 Recalculation and historical reproducibility (D15 preserved)

* A recalculation after a data correction produces a **new** snapshot with a **new** request id (the existing
  `calc_digest` mechanism) and therefore a **new** `source_line_item_id` resolution. The prior snapshot, its
  line link and its report version remain **untouched** → the finalized report stays reproducible.
* **No historical snapshot is retro-linked.** B2 does not write `source_line_item_id` on any pre-existing row.
* If extraction data changes after a report is finalized: the finalized report continues to reference the
  **materialised line row**, whose `raw_*` values and `payload_hash` are the ones captured at materialisation
  time. The report therefore remains reproducible **even though the mutable JSONB has since changed** — this
  is the D15 property the materialisation (rather than a JSONB pointer) exists to guarantee.
* Divergence between the current JSONB and the materialised row is **detectable** (§11.3) and is reported, not
  reconciled.

### 15.3 Immutability enforcement and the retention boundary (B2-D11 — CLOSED, PO-RATIFIED)

B2 enforces immutability with **preservation-first referential semantics + privilege posture + absence of code
paths + the `DO NOTHING` rule**:

* `source_item_id` is **`ON DELETE RESTRICT`** (B2-D1) — a parent delete cannot silently destroy evidence-line
  provenance;
* `anon`/`authenticated` cannot `INSERT`/`UPDATE`/`DELETE` (privilege posture);
* no B2 code path updates or deletes a line row;
* reruns are `ON CONFLICT DO NOTHING` (never `DO UPDATE`).

**B2 introduces no retention or deletion mechanism whatsoever.** It adds no soft-delete field, no retention
trigger, no automatic purge, no anonymisation logic and no deletion job; and it deliberately adds no hard
immutability trigger either, because that would itself constitute a deletion-semantics mechanism. Any future
retention, deletion or anonymisation of evidence lines is the responsibility of **N3 / the separate
retention+privacy workstream**, which must be separately designed and authorised. The V2 suite therefore tests
**denial at the privilege level** and the **RESTRICT behaviour** — explicit, verifiable behaviours — rather
than trigger behaviour.

---

## 16. RLS / security intent (deliverable K)

B2 adds posture **only for its own objects**. It does **not** remediate the broad production RLS baseline and
modifies **no** unrelated policy (G0-H).

### 16.1 New table `evidence_line_items`

| Actor | Privilege | Policy |
|---|---|---|
| `anon` | `REVOKE ALL` | none |
| `authenticated` | `GRANT SELECT` only; `INSERT/UPDATE/DELETE/TRUNCATE/TRIGGER/REFERENCES/MAINTAIN` revoked | `evidence_line_items_org_select` — `FOR SELECT TO authenticated USING (public.p8_disclosure_is_org_member(organization_id))` |
| PE members | **B2-D3 CLOSED / PO-RATIFIED** | mirror the existing item boundary: `… USING (public.is_entity_member(public.work_item_effective_entity(source_item_id)))`, exactly as `manual_extraction_items_entity_select` does |
| `service_role` | `GRANT ALL` | bypasses RLS (backend writer) |

* **Reuse, never recreate, the B1 helper** `public.p8_disclosure_is_org_member(uuid)`. The B2-1 migration must
  **fail loudly with an explicit message** if the helper is absent (i.e. B1 not applied), rather than creating a
  duplicate helper definition that could drift. The same pattern is used for the PE read policy: it **reuses**
  `work_item_effective_entity`/`is_entity_member` (already granted to `authenticated`).
* **Cross-tenant denial is the primary negative test**: an org-B member reading org-A lines must return **zero
  rows**; PE X must not read PE Y’s lines.
* **No `auth.uid()`-free policy is granted to `authenticated`** and **no** policy widens access beyond the
  existing item boundary. RLS is defence-in-depth; the **application layer remains the enforced boundary**
  (B1’s declared posture), because the existing baseline is incomplete.

### 16.2 Existing tables modified by B2-2

Adding a nullable column with a guarded FK and an index changes **no** grant, **no** policy and **no** RLS
flag on `calculation_snapshots` or `disclosure_value_evidence`. The clone harness must prove exactly this
(table-level parity), since a privilege change on those tables would be a silent security regression.

### 16.3 Application-layer authorization (the enforced boundary)

| Actor | B2 capability |
|---|---|
| Customer Owner / Admin | Read lines of their organisation (via authorised application paths) |
| Customer Member | Read (same org scope; no write path exists to grant) |
| Customer **Viewer** | Read-only; **no write path exists at all** in B2, so the viewer restriction is satisfied by construction |
| Consultant | Bounded to engagement scope for the organisations they operate — **no new consultant capability is introduced by B2**; any consultant read path must use the existing `ensure_org_access`/`require_org_member` guards |
| PE Manager / Staff | **B2-D3 PO-RATIFIED:** read lines for work their entity is assigned, mirroring the existing item policy — no widening |
| CarbonTally internal | Existing staff guards apply; B2 grants no new administrative capability |
| Any actor | **No** update/delete capability; no "create line" capability |

---

## 17. Audit requirements (deliverable L)

B2 uses the **existing** `audit_trail` mechanism (P7 immutability, `data/audit.py`, `domain/audit.py`,
`api/audit_helpers.py`). **No parallel audit system is created.** Action strings extend the established
`report:` namespace used by B1 (`report:disclosure_*`).

| Action | Entity | When | Payload (`after`) |
|---|---|---|---|
| `report:evidence_line_items_materialised` | `manual_extraction_items`, `entity_id=<item id>` | **Forward** materialisation where ≥ 1 row was inserted | `{materialised, skipped_empty, skipped_malformed, first_line_item_id, payload_digests}` — **counts, ids and hashes only; no line values, no documents, no signed URLs** |
| `report:evidence_line_items_backfilled` | `evidence_line_items`, `entity_id=<run id>` (generated run UUID) | **Once per backfill run** | `{dry_run, scanned_items, eligible_items, materialised_rows, skipped_empty, skipped_malformed, skipped_no_lines, divergences, started_at, finished_at}` |
| `report:evidence_line_items_divergence_detected` | `manual_extraction_items`, `entity_id=<item id>` | A run finds an ordinal whose stored `payload_hash` differs from the currently derivable hash | `{divergent_ordinals, line_item_ids}` |

**Volume rationale (deliberate):** forward materialisation writes **one audit row per document** (bounded by
documents processed); the **backfill writes one summary row per run**, not one per item, because it may touch a
very large historical population and `audit_trail` is append-only/immutable (P7) — audit volume is a real cost.
Per-item detail survives in the run-report artefact plus the rows themselves; divergences (rare, and the only
per-item case worth an audit row) are audited individually. → **B2-D8** (implementation/policy confirmation).

**Never audited/logged:** passwords, keys, JWTs, signed URLs, storage objects, full document text, or complete
line payloads.

**Audit is best-effort:** as elsewhere in this codebase, an audit failure must never break materialisation (it
is logged) — but the run report records the audit outcome so a silent audit failure cannot be mistaken for
success.

---

## 18. Migration strategy (deliverable M)

### 18.1 Exact migrations: **two** (additive only)

| File | Contents | Notes |
|---|---|---|
| `supabase/migrations/20260916000000_p8_b2_evidence_line_items.sql` | B2-1: create `evidence_line_items` + constraints + indexes; enable RLS; privilege posture; org-member SELECT policy; **PE SELECT policy (B2-D3)**; explicit precondition check that the B1 helper exists; table/column comments recording the B2 boundary; **`source_item_id` FK `ON DELETE RESTRICT` (B2-D1)**; **no trigger / no retention artefact (B2-D11)** | One `BEGIN; … COMMIT;`; `IF NOT EXISTS` throughout; guarded FK/policy creation |
| `supabase/migrations/20260916010000_p8_b2_provenance_line_links.sql` | B2-2: `calculation_snapshots.source_line_item_id` + guarded FK + index; `disclosure_value_evidence.source_line_item_id` + guarded FK + index; comments | Existing tables: **additive only** — no column altered/dropped, no policy/grant change, no row touched |

**Why two and not one:** B2-1 creates a new capability with its own security posture; B2-2 modifies two
**existing** tables. Splitting them makes the “additive-only on existing objects” claim independently
reviewable and independently revertible, mirroring how B1 separated its foundation from its follow-up
correction. (One migration would be acceptable but weaker for review — an implementation decision, not a PO
decision.)

**Why the backfill is not a third migration:** §11.4.

### 18.2 Ordering, dependencies and idempotency

* **Hard dependency:** B2-1 runs **after** B1's `20260914000000_…` (it reuses `p8_disclosure_is_org_member`);
  B2-2 runs **after** B2-1 (FK target) and after B1's `20260914000000_…` (for `disclosure_value_evidence`).
* **Timestamp rationale:** B1 uses `20260914`/`20260915`, so B2 uses `20260916…` to sort strictly after them
  (the repo's ordering authority is the filename prefix).
* **Idempotency:** both must be re-appliable with `rc=0` and **zero** schema diff (V1R proved this standard for
  B1). `ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS`, guarded
  constraints/policies via `DO $$ … IF NOT EXISTS …` blocks.
* **No data dependency:** neither migration reads or writes table data.
* **A guarded `DO` block keyed on `pg_constraint.conname` is required** (the D33 pattern) so a re-run is a true
  no-op rather than an error.

### 18.3 B1 migration files are **not touched**

`20260914000000_p8_b1_disclosure_model_foundation.sql` and
`20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql` remain **byte-identical**. This is
what keeps the two B1 **migration-text** guards valid (§20.6) and B1's verified contract intact.

### 18.4 Application sequence (per environment) — deployment is **NOT authorised here**

1. Verify a restorable snapshot of the target database exists.
2. Apply `20260916000000…` → expect `rc=0`.
3. Apply `20260916010000…` → expect `rc=0`.
4. **Re-apply both** → expect `rc=0` and no schema/policy diff (idempotency proof).
5. Run the B2 runtime suite (V2) against the provisioned database.
6. **Only if separately authorised:** run the backfill dry-run, review the run report, then execute.
7. Never run against production while the outstanding-migration decision (G0-D) is unresolved: the **34
   previously-outstanding migrations remain a production deployment blocker** and B2 adds **2 more**. B2
   authorises no deployment.

### 18.5 Provisioning the V2 environment (disposable clone)

Because no environment currently holds B1/B2 (§3, F-B2-16), V2 requires a **disposable clone**: create a
database, restore the production-shaped schema (as V1R did for its privileges-inclusive clone), apply the B1
migrations, then the two B2 migrations, and point `INTEGRATION_DATABASE_URL` at it. **The main application
database and the investor-demo database are never used for this** (D31 rule, enforced by `conftest.py`).

---

## 19. Coexistence and data safety (deliverable R)

| Existing object | Coexistence rule | Verified property to test |
|---|---|---|
| `manual_extraction_items` (36 columns) | **Not modified by B2 at all** — no column, constraint, index, policy, grant or row change. The line table only *references* it. | Column set, constraints, indexes, policies and grants identical before/after both migrations |
| `extracted_data` JSONB | **Never written by B2.** Remains the eligibility source and the correction surface it already is. | Per-row JSONB hash identical before/after materialisation and backfill |
| `mapped_data` JSONB | **Never written by B2**, and never used as an identity source. | No write statement references it |
| `calculation_snapshots` | Gains **one nullable column** + FK + index. No existing column, constraint, policy, grant or row changes. | Row counts and per-row hashes identical before/after; `source_line_item_id IS NULL` on every pre-existing row |
| `disclosure_value_evidence` (B1) | Gains **one nullable column** + FK + index. B1 constraints/indexes unchanged; existing rows keep the new column NULL. | `uq_dve_reference_nullsafe` + `disclosure_value_evidence_unique` still present and identical; B1 runtime suite green |
| `emissions_logs` | **Untouched**; reaches lines through `snapshot_id`. | Column set/policies unchanged |
| `organization_files` | **Untouched**; referenced read-only by `source_file_id`. | Unchanged |
| Report lifecycle tables | **Untouched.** | Unchanged |
| Other B1 tables | **Untouched.** | Unchanged |

**Hard rules:** no destructive migration; no silent data rewrite; no deletion of historical provenance; no
`UPDATE`/`DELETE` executed against any pre-existing table by either migration or by the backfill; the
investor-demo dataset is not mutated by B2 implementation or by V2 verification (V2 uses the disposable clone).

**Rollback shape (documented, not executed):** drop the two additive columns (+ their FKs/indexes), then
`DROP TABLE evidence_line_items`. Because nothing pre-existing was rewritten, a rollback costs only the newly
created rows.

---

## 20. Test / verification contract (deliverable N)

### 20.1 Required test artefacts

| File | Kind | Purpose |
|---|---|---|
| `backend/tests/unit/data/test_b2_migration.py` | static (text) | B2-1/B2-2 additive and idempotent; exactly one new table; `ADD COLUMN IF NOT EXISTS` on the two expected tables only; `ON DELETE SET NULL` on consumer FKs; no `DROP`/`ALTER … TYPE`/`RENAME`/`UPDATE`/`DELETE`; the B1 migration files are unmodified |
| `backend/tests/unit/domain/test_evidence_line_items.py` | pure | Eligibility, recognised-key extraction, `raw_*` mapping, canonical `payload_hash` (incl. `100`/`100.0`/`100.00` equality and key-order independence), ordinal gaps, `DO NOTHING` decisions, divergence classification |
| `backend/tests/integration/test_evidence_line_items_b2_runtime.py` | runtime/DB | The acceptance tests below — **skips** (never fails) when the B2 schema is unprovisioned, mirroring B1’s `_require_b1_schema` |
| `backend/tests/integration/test_disclosure_b1_runtime.py` | amendment | §20.6 |
| `backend/tests/unit/data/test_disclosure_sql_typing.py` | amendment | §20.6 |
| Clone harness (operational script, run manually as V1R did) | schema safety | Privileges-inclusive clone: apply B1 + B2 twice; prove parity and the declared delta |

### 20.2 Runtime acceptance tests (database-backed — required, not optional)

1. **Materialisation count/order** — a CSV-shaped item with 4 lines ⇒ exactly 4 rows, `line_number` 1..4,
   correct `materialisation_kind`, `organization_id` = the parent’s org.
2. **Idempotency** — backfill twice: second run inserts 0, updates 0, deletes 0; per-row hashes identical;
   run report shows `materialised_rows=0`.
3. **Identical duplicate lines stay distinct** — 2 identical elements ⇒ 2 rows, same `payload_hash`, different
   `line_number` (never merged).
4. **Gaps** — a malformed element in the middle ⇒ rows only for valid ordinals with ordinals preserved
   (`1, 3`) and `skipped_malformed=1`.
5. **No `line_items`** ⇒ 0 rows; `source_line_item_id` NULL; evidence completeness stays PARTIAL/UNAVAILABLE.
6. **Empty array** ⇒ 0 rows, and **no** flat-record fallback.
7. **Snapshot linkage** — a multi-line calculation ⇒ each snapshot has the correct `source_line_item_id`, and
   its `source_item_id` matches the line’s.
8. **Flat document** ⇒ snapshot `source_line_item_id IS NULL` (no synthetic line created).
9. **Multiple calculations per line** — two calculations on the same ordinal ⇒ two snapshots pointing at the
   same line (no uniqueness violation, no mutation).
10. **Divergence** — mutate `extracted_data.line_items[2].quantity`, rerun: that ordinal is reported
    DIVERGENCE, the stored row is unchanged, other ordinals unaffected.
11. **Forward-then-backfill** — rows created by the hook are untouched by a later backfill (identical hashes,
    `materialisation_kind` still `FORWARD`).
12. **RLS ALLOW/DENY** — org member reads its org’s rows; **cross-tenant read returns 0 rows**; PE-X cannot read
    PE-Y rows; `anon` reads 0 rows.
13. **Privileges** — `authenticated` cannot `INSERT`/`UPDATE`/`DELETE` (permission denied); `service_role` can
    insert; `anon` has no access.
14. **Historical immutability** — pre-existing `calculation_snapshots`/`disclosure_value_evidence` rows
    unchanged (hash comparison) after migrations, materialisation and backfill.
15. **Evidence linkage** — `link_value_evidence(..., source_line_item_id=…)` writes the column, the upsert stays
    idempotent, and the snapshot↔`dve` consistency invariant holds.
16. **Audit** — forward materialisation emits `report:evidence_line_items_materialised`; a run emits exactly one
    `report:evidence_line_items_backfilled`; divergence emits
    `report:evidence_line_items_divergence_detected`; **no** audit payload contains line values or documents.
17. **No re-extraction** — a static (import/call-graph) assertion that the materialisation/backfill modules call
    no extractor/OCR/LLM/parser; plus a runtime assertion that `extracted_data`, `mapped_data` and
    `automation_extracted_data` are byte-identical before/after.
18. **Migration idempotency** — apply B2-1/B2-2 twice on the clone: `rc=0`, zero diff.
19. **RESTRICT behaviour (B2-D1)** — attempting to delete a `manual_extraction_items` row that still has
    evidence lines **fails** with a foreign-key violation, and the lines remain intact; no cascade occurs.
20. **No retention artefacts (B2-D11)** — the B2-1 migration adds **no** trigger, **no** soft-delete column and
    **no** purge path (asserted statically and by inspecting the provisioned schema).

### 20.3 Clone-based schema-safety harness (V1R standard, adapted)

V1R proved B1’s schema safety by comparing an privileges-inclusive clone before↔after. B2 **must reuse that
method with one correction**, because B2 *deliberately* changes two existing tables:

| Check | Expected |
|---|---|
| Table-level grants (`anon`/`authenticated`/`service_role`) on all **116 pre-existing** tables | **Identical** before↔after |
| Policies on all pre-existing tables (name, cmd, `qual`, `with_check`) | **Identical** before↔after |
| `relrowsecurity` on all pre-existing tables | **Identical** before↔after |
| Column set of every pre-existing table | Identical **except** the two declared new columns |
| Constraints on `calculation_snapshots` / `disclosure_value_evidence` | Identical **except** the two declared FKs |
| Indexes on pre-existing tables | Identical **except** the two declared indexes |
| Row counts + per-row content hashes | **Identical** (no row rewritten) |
| New objects present | **Exactly** the objects enumerated below — **1** new table, **2** new columns on pre-existing tables, **5** new FK constraints (3 declared inside the new table + 2 on pre-existing tables), **4** explicit new indexes **plus 1 constraint-backed unique index** (counted separately), **2** new policies, **0** triggers |
| Re-apply both migrations | `rc=0`, zero diff |

**Exact new-object enumeration (normative for the harness — the schema is authoritative; the harness must match
the schema, never the reverse):**

* **New table (1):** `public.evidence_line_items`.
* **New columns on pre-existing tables (2):** `public.calculation_snapshots.source_line_item_id` and
  `public.disclosure_value_evidence.source_line_item_id` (both nullable; §8.1, §9.1).
* **New FK constraints (5):**
  1. `evidence_line_items.organization_id` → `organizations(id)` — declared inline inside the new table
  2. `evidence_line_items.source_item_id` → `manual_extraction_items(id)` **`ON DELETE RESTRICT`** —
     declared inline inside the new table (B2-D1)
  3. `evidence_line_items.source_file_id` → `organization_files(id)` `ON DELETE SET NULL` — declared inline
     inside the new table
  4. `calculation_snapshots_source_line_item_id_fkey` → `evidence_line_items(id)` `ON DELETE SET NULL` — added
     to a pre-existing table (§8.1)
  5. `disclosure_value_evidence_source_line_item_id_fkey` → `evidence_line_items(id)` `ON DELETE SET NULL` —
     added to a pre-existing table (§9.1)

  (The three inline FKs are unnamed in the DDL and take PostgreSQL's default names following the repository's
  existing convention, e.g. `evidence_line_items_source_item_id_fkey`; the two added FKs are named explicitly
  by B2-2. Total B2 FK delta = **5 constraints**, of which **2** are on pre-existing tables — the figure that
  the "Constraints on `calculation_snapshots` / `disclosure_value_evidence`" row above asserts.)
* **Explicit new indexes (4)** — created by `CREATE INDEX IF NOT EXISTS`:
  1. `idx_eli_org` — `evidence_line_items (organization_id)` (§7.1)
  2. `idx_eli_source_file` — `evidence_line_items (source_file_id)` (§7.1)
  3. `idx_calculation_snapshots_source_line_item` — `calculation_snapshots (source_line_item_id)` (§8.1)
  4. `idx_dve_source_line_item` — `disclosure_value_evidence (source_line_item_id)` (§9.1)
* **Constraint-backed unique index (1) — NOT one of the four above:** `evidence_line_items_identity_unique`,
  created by `UNIQUE (source_item_id, line_number)` (§7.1). It must be counted separately from the four
  explicit `CREATE INDEX` objects and must not be silently folded into that total.
* **New policies (2) on `evidence_line_items`, both `FOR SELECT TO authenticated`:**
  1. the org-member policy using `public.p8_disclosure_is_org_member(organization_id)`
  2. the PE-mirror policy using `public.is_entity_member(public.work_item_effective_entity(source_item_id))`
* **Triggers (0):** B2 adds **no** trigger of any kind (B2-D11 — no retention/deletion mechanism).

### 20.4 Regression requirements

* The **whole** existing suite must pass: `cd backend && python -m pytest tests -q` (with the §20.6 amendments).
* The B1 runtime suite must remain green **including** F1–F5, tenant isolation, immutability, privilege posture
  and audit-emission tests.
* The B2 changes to `CalculationRequest`/repositories must not alter any existing unit test expectation; if a
  test must change, the change must be justified as a *contract* change (not a convenience) and recorded in the
  implementation report.

### 20.5 What is explicitly NOT sufficient as evidence

Static/SQL-text assertions alone are **not** acceptable for B2 (the V1 lesson: B1’s static tests passed while
runtime defects existed). Every SQL-behaviour claim in §20.2 must be executed against a real PostgreSQL
database. A green static suite is reported as *static coverage*, never as “verified”.

### 20.6 Mandatory amendments to B1’s test scope (bounded and named)

B1’s suite contains negative assertions that were correct **for B1’s scope** and that B2 necessarily
invalidates. They must be **amended, not deleted** — deleting them would remove the guard that prevents B3/B4
objects from leaking.

| Artefact | Current assertion | Required post-B2 form |
|---|---|---|
| `backend/tests/integration/test_disclosure_b1_runtime.py::test_b2_b3_b4_boundary_untouched` | asserts `evidence_line_items` does **not** exist and `calculation_snapshots.source_line_item_id` does **not** exist; asserts no `%intensity%`/`%narrative%`/`%commentary%` tables | **Split**: (a) keep the B3/B4 negative assertions unchanged; (b) replace the B2-absence assertions with a check scoped to **B1’s own namespace** — the disclosure-namespace table list is exactly the 11 B1 tables (so no *B2-capability* is smuggled into `disclosure_*`), and move the B2 presence checks into the new B2 runtime suite |
| `backend/tests/unit/data/test_disclosure_sql_typing.py::test_no_b2_b3_b4_objects_in_the_repository` | asserts the SQL executed by `backend/data/disclosure.py` never contains `evidence_line_items`/`source_line_item_id` | Keep the **B3/B4** assertions (`intensity`, `narrative`, `commentary`) unchanged; replace the two B2 assertions with an assertion that the **B1 repository’s SQL** contains `source_line_item_id` only in the sanctioned `disclosure_value_evidence` link statement (and no `evidence_line_items` DDL/DML) |
| `backend/tests/unit/data/test_disclosure_migration.py::test_no_b2_b3_b4_tables`, `::test_no_source_line_item_id_column` | read the **B1 migration file text** | **Unchanged** (the B1 migration file is byte-identical — §18.3) |

**Rule:** the amendments must (1) be minimal, (2) preserve every B3/B4 guard, (3) be explicitly listed in the
B2 implementation report with before/after text, and (4) never weaken a *security* or *scope* assertion.

### 20.7 Environment limitations (declared)

* **No environment currently holds B1/B2** (F-B2-16), so the B2 runtime suite will report **SKIPPED** on the
  dev/demo database and in CI unless a B1+B2-bearing database is provisioned. This is a **known, pre-existing
  verification gap** (already recorded as a standing follow-up for B1) and must be stated in the B2
  verification report rather than papered over: a skip is **not** a PASS.
* V2 acceptance therefore requires the disposable-clone provisioning in §18.5 to be executed, and the report
  must state the environment, the applied migrations and the git SHA/hash of the tree under test.

---

## 21. Failure / edge-case matrix (deliverable O)

| # | Case | Required behaviour | Never |
|---|---|---|---|
| 1 | Source has no `line_items` key | Ineligible; 0 rows; document-level chain; snapshot link NULL | Create a line from the flat record; error |
| 2 | `line_items` present but empty `[]` | 0 rows; counted `skipped_no_lines` | Fall back to the flat record |
| 3 | Malformed element (non-object) | Skipped; **ordinal preserved as a gap**; counted `skipped_malformed`; other elements still materialise | Fail the item; renumber ordinals |
| 4 | Degenerate object (no recognised key with a value) | Skipped; counted `skipped_empty` | Insert an empty line |
| 5 | Duplicate line content (same `payload_hash`) | **Both** rows inserted, distinct `line_number` | Deduplicate by content |
| 6 | `quantity` not numeric / `unit` empty | `raw_quantity`/`raw_unit` NULL for that fact; row **still** materialised if any recognised value exists | Fabricate a value; reject the line |
| 7 | Line ordering changes in the persisted array (correction) | Detected as **DIVERGENCE** on rerun (hash mismatch at an ordinal); historical rows untouched; reported | Reorder/renumber existing rows |
| 8 | Source document (`organization_files` row) deleted | `source_file_id` → NULL via `SET NULL`; the line survives with its recorded values | Cascade-delete the line |
| 9 | Extraction item deleted | **Prevented** while evidence lines exist (`ON DELETE RESTRICT`, B2-D1): the delete fails loudly and nothing is destroyed. Any future authorised deletion/anonymisation workflow must handle evidence lines explicitly under the retention/privacy workstream. Snapshots/evidence keep their own rows via their `SET NULL` links | Cascade-delete lines; leave a dangling FK; delete a snapshot |
| 10 | Orphaned line (parent removed, line retained) | **Not reachable:** `source_item_id` is `NOT NULL` **and** `ON DELETE RESTRICT`, so a line can never exist without its parent (B2-D1) | Present a parentless line as fully-provenanced |
| 11 | Calculation with no line-level provenance (flat/manual) | `source_line_item_id` NULL; document-level provenance; PARTIAL at best | Invent a line; block the calculation |
| 12 | Mixed evidence (some values line-level, some document-level) | Fully representable — each `disclosure_value_evidence` row carries its own precision; the report must describe the aggregate honestly | Force one granularity onto all rows |
| 13 | Legacy records (pre-B2 snapshots) | `source_line_item_id` NULL permanently (no inference) | Retro-link by inference |
| 14 | Reprocessing a document | New/changed `extracted_data` → new ordinals/hashes → divergence reported for changed ordinals; new snapshots (new request ids) link to the then-current lines; **no** old row mutated | Mutate existing lines or snapshots |
| 15 | Partial backfill (interrupted) | Rerun inserts only missing ordinals (resumable, idempotent) | Roll back or delete partial rows |
| 16 | Failed backfill (exception) | Current batch aborts; already-written rows remain (valid, idempotent); run report records the failure | Roll back committed evidence rows |
| 17 | Tenant mismatch (caller org ≠ parent org) | **Rejected**; 0 rows written; RLS returns 0 rows on read | Write a cross-tenant line |
| 18 | Concurrent materialisation (two workers, same item) | `ON CONFLICT DO NOTHING` ⇒ one row per ordinal; no error surfaces to either worker | Duplicate rows; deadlock loop |
| 19 | B1 helper absent (B1 not applied) | B2-1 migration **fails loudly** with an explicit message naming the missing prerequisite | Silently skip RLS; create a duplicate helper |
| 20 | Parent has `file_id` NULL (D33 unmatched) | `source_file_id` NULL; the line is still materialised and addressable | Invent a file link |
| 21 | Line used by a finalized report, then extraction corrected | Line row unchanged; report reproducible; divergence reported | Rewrite the line (breaks D15) |
| 22 | Very large `line_items` array (e.g. 10k rows) | Materialise all eligible elements (batched inserts; count-only audit) | Truncate; sample; skip silently |

---

## 22. Exact B2 implementation boundary (deliverable P)

### 22.1 IN SCOPE for B2

1. The two migrations (§18.1) plus their table/column comments.
2. `evidence_line_items` DDL, constraints, indexes, RLS/privilege posture (§7, §16).
3. Materialisation domain logic: eligibility, derivation, canonical `payload_hash`, ordinal rules (§11.1–§11.2).
4. `backend/data/evidence_line_items.py` — insert-only materialisation + the read functions (§12.2).
5. The forward hook on `ManualExtractionRepository.save_extracted_data` / `update_item` and the additive
   `extraction_method` keyword (§12.1).
6. The Class-1 backfill **operation** (dry-run, batched, idempotent, run report, divergence detection) and its
   CLI entry point in the existing tooling location (§11.4). **Execution on any environment is separately
   authorised.**
7. `CalculationRequest.source_line_item_id`, its snapshot persistence, and the ordinal→line resolve in both
   calculation paths (§13).
8. `link_value_evidence(..., source_line_item_id=None)` on the B1 repository (§9.3).
9. Audit actions and their emission (§17).
10. The B2 static/pure/runtime tests, the §20.6 amendments, and the clone harness script.
11. The B2 implementation report and the B2 verification (V2) report.

### 22.2 OUT OF SCOPE for B2 (must not be absorbed)

| Out of scope | Belongs to |
|---|---|
| PDF/IMAGE extraction fidelity (8→1), OCR/AI prompt changes, completeness-gate changes | **P1** — a separate future **investigation** workstream (§6.1); **not** B2 implementation |
| Re-parsing/OCR of historical documents to create lines | **P1** (separately authorised, never silent) |
| The `source_page` semantic defect (F-B2-7) | **separate remediation workstream** (§27.1) |
| Retro-linking historical snapshots onto materialised lines | **excluded** (B2-D12, §27) |
| Retention / deletion / anonymisation of evidence lines | **N3** retention+privacy workstream (§15.3, §27.3) |
| EF-E factor matching | **P2** |
| Framework/requirement/mapping/applicability/purpose projections, intensity, per-gas, base year | **B3** |
| Value→line drill-down read model, endpoints and UI; report templates; SECR intensity | **B3** |
| Narrative, finalisation, frozen artefact | **B4** |
| Phase 8-X (X1/X2) | **Phase 8-X** |
| Broad production RLS remediation | separate workstream (G0-H) |
| Legacy report route remediation (D16) | separate workstream (LEG) |
| Subscription/allowance provisioning | Phase 8-X §17 |
| Customer-shaped end-to-end calculation evidence | after P1 + B3 |
| Full ESRS/CSRD requirement content | E1 / `G0-A` |
| Fixing `source_page` = page-count (F-B2-7) | separate workstream; decision B2-D4 |
| Fixing the `mapped_data.line_items` rewrite (F-B2-4) | separate workstream |
| Retention execution/configuration (N3) | separate workstream |
| Any frontend change | not required by B2 (§12.4) |
| Production migration / deployment | **not authorised** |

---

## 23. Decision record — B2-D1 … B2-D12 (CLOSED / PO-RATIFIED)

**Status: all twelve decisions are CLOSED by the Product Owner (2026-09-13, task
`CT-P8-B2-PO-DECISION-RATIFICATION-20260913-018`).** The authoritative PO record is
`docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md`. This section records the ruling,
its rationale, its implementation consequence and its blocker status **inside the contract**.

Each entry retains its original question and options for auditability and now carries the **PO DECISION**.
**Blockers: none for any decision — B2 is ready for an implementation-authorisation gate.**

### B2-D1 — `evidence_line_items.source_item_id` delete semantics

* **Why it matters:** it decides what happens to addressable evidence if an extraction item is ever removed —
  i.e. whether provenance can be *silently destroyed* by a parent delete.
* **Options:** (a) `NOT NULL` + `ON DELETE CASCADE`; (b) nullable + `ON DELETE SET NULL` (orphan lines survive);
  (c) `NOT NULL` + `ON DELETE RESTRICT` (parent cannot be deleted while lines exist).
* **PO DECISION (B2-D1 — CLOSED): `ON DELETE RESTRICT` — preservation-first. `CASCADE` is prohibited.**
  Evidence-line records are authoritative historical provenance records and must not be automatically
  destroyed as a consequence of deleting the source extraction item, so `source_item_id` stays `NOT NULL` with
  `ON DELETE RESTRICT`.
* **Rationale (PO):** the absence of a real extraction-item deletion path today (`delete()` is a no-op stub)
  does **not** justify destructive FK semantics; `SET NULL` was also rejected, because a parent-less line is a
  provenance record that cannot be scoped or classified honestly.
* **Implementation consequence:** the B2-1 DDL carries `ON DELETE RESTRICT` (§7.1 already updated); deleting an
  extraction item that still has evidence lines **fails**; V2 tests the RESTRICT behaviour. B2 introduces
  **no** replacement deletion/anonymisation workflow — a future one must be separately designed and authorised
  under the retention/privacy workstream.
* **Blockers:** **none.**

### B2-D2 — Divergence and supersession policy when persisted `line_items[]` changes after materialisation

* **Why it matters:** correction paths (`G6-D`) can rewrite `extracted_data`. The choice determines whether a
  line row is ever superseded — i.e. whether historical evidence can change.
* **Options:** (a) detect + report + never rewrite (forward-only; divergence visible, historical rows frozen);
  (b) supersede: insert a *new* row for the changed ordinal and retire the old one (needs a status/superseded
  column and a policy for which one a report uses); (c) recompute in place (**prohibited** — rewrites
  provenance and breaks D15).
* **PO DECISION (B2-D2 — CLOSED, RATIFIED): DETECT + REPORT + NEVER REWRITE.** Where the persisted
  `extracted_data.line_items[]` no longer derives the same `payload_hash` as an existing evidence line, B2
  detects it, reports it and **preserves** the existing evidence-line record. It never silently updates it,
  never silently deletes it and never silently creates a replacement identity for the same ordinal.
* **Rationale (PO):** satisfies `DM-7` exactly (“no row is rewritten to manufacture provenance”) and keeps D15
  reproducibility absolute.
* **Implementation consequence:** reruns use `ON CONFLICT DO NOTHING` with a divergence check (§11.3); a
  divergence audit event is emitted per affected item; V2 tests ordinal-level divergence with an unchanged
  stored row. Any future supersession/versioning mechanism requires a **separately authorised design** and is
  not part of B2.
* **Blockers:** **none.**

### B2-D3 — Processing-Entity read access to `evidence_line_items`

* **Why it matters:** the PE source-document boundary is ratified; B2 creates a new artefact derived from item
  content, so its boundary must be decided explicitly rather than inferred.
* **Options:** (a) **mirror** the existing item policy
  (`is_entity_member(work_item_effective_entity(source_item_id))`); (b) deny PE read in B2 (org members only).
* **PO DECISION (B2-D3 — CLOSED, RATIFIED): mirror the existing PE item-access boundary.** PE access to
  `evidence_line_items` must **not** widen the consultant/PE scope beyond the source extraction item they can
  already access; the existing entity/member authorization boundary is reused
  (`is_entity_member(work_item_effective_entity(source_item_id))`, exactly as
  `manual_extraction_items_entity_select`).
* **Rationale (PO):** reusing the ratified helper boundary widens nothing — the line’s `raw_*` values are a
  subset of the item JSONB PE users can already read — and avoids inventing a new semantics for a new table.
* **Implementation consequence:** one additional `SELECT` policy in B2-1; PE-A→PE-B and cross-tenant denials are
  V2 negative tests. **No new consultant authorization model** is created.
* **Blockers:** **none.**

### B2-D4 — The `source_page` = page-count defect (F-B2-7): fix, defer, or scope elsewhere

* **Why it matters:** auto-processed evidence can be classified `COMPLETE` on a **false location**, because
  `_calculate_line` stores the document page **count** in `snapshot.source_page`, which `domain/evidence.py`
  treats as an exact page. This affects existing evidence honesty and reporting claims.
* **Options:** (a) **B2 records it and never copies it** (no behaviour change); (b) B2 fixes it (store NULL from
  the automatic path) — auto-processed evidence degrades to `PARTIAL`, changing existing UX/classification;
  (c) a separate small workstream fixes it with its own verification.
* **PO DECISION (B2-D4 — CLOSED): DEFER to a separate bounded remediation workstream.** F-B2-7 is accepted as
  real. B2 **must not** fix this defect, reinterpret existing `source_page`, copy the value into B2 as if it
  were an exact line location, silently transform page counts into page references, or change evidence
  classification as part of B2.
* **Rationale (PO):** the defect is a source-page *semantics* problem in an existing write path, not an
  addressability problem; fixing it inside B2 would change evidence classification for existing data and is
  scope bleed.
* **Implementation consequence:** the defect and its risk remain recorded (§27.1) and the scope boundary is
  maintained; `evidence_line_items.source_page` is populated only from a genuine per-line value and is otherwise
  NULL (§7.1, §11.2). A **separate task** (not B2) investigates and remediates source-page semantics.
* **Blockers:** **none.**

### B2-D5 — Audit granularity for forward materialisation and backfill

* **Why it matters:** `audit_trail` is append-only/immutable (P7); per-line audit rows for a large historical
  backfill would be a permanent volume cost.
* **PO DECISION (B2-D5 — CLOSED, RATIFIED):** one **forward materialisation audit event per source document**;
  one **summary audit event per backfill run**; **divergence events per affected item/ordinal**; audit payloads
  must not contain source document contents, line values, signed URLs or secrets; the **existing `audit_trail`
  is used and no parallel audit system is created**.
* **Rationale (PO):** bounded, proportionate audit volume on an append-only audit log while preserving the
  events that matter.
* **Implementation consequence:** exactly the three audit actions in §17; V2 asserts one forward event per
  document, a single summary event per run and a per-item divergence event.
* **Blockers:** **none.**

### B2-D6 — Where forward materialisation is invoked

* **Why it matters:** it decides whether materialisation can be silently skipped by a future write path.
* **PO DECISION (B2-D6 — CLOSED, RATIFIED):** place forward materialisation at the **data-layer choke point**
  (`ManualExtractionRepository`, as identified in §12.1). Materialisation logic must **not** be duplicated across
  individual extraction-pipeline callers.
* **Rationale (PO):** a single reviewed hook cannot be forgotten by a future caller; duplication guarantees
  omissions.
* **Implementation consequence:** the hook lives in `save_extracted_data` (and `update_item` when
  `extracted_data` is supplied); it stays best-effort and must never block the extraction save.
* **Blockers:** **none.**

### B2-D7 — `extraction_method` vocabulary: constrained or open?

* **Why it matters:** a `CHECK` on a closed value set would couple B2 to P1 (a new extraction path would need a
  B2 migration to extend the list).
* **PO DECISION (B2-D7 — CLOSED, RATIFIED): open vocabulary — no restrictive `CHECK` constraint** on
  `extraction_method`, to avoid coupling B2 to the separate extraction-fidelity/P1 workstream. The known values
  remain documented in §11.2 and `unknown` remains the honest default.
* **Rationale (PO):** the column is observational (a record of what produced the data), not a state-machine
  input; constraining it would force a B2 migration for every new extraction path.
* **Implementation consequence:** the B2-1 DDL carries no CHECK on this column (§7.1 stands unchanged).
* **Blockers:** **none.**

### B2-D8 — `row_reference` population rule

* **Why it matters:** the design requires the human-facing source reference *only where the source carries one*;
  the available historical fields could tempt a false attribution.
* **PO DECISION (B2-D8 — CLOSED, RATIFIED):** for Class-1 materialisation, **`row_reference` remains NULL.** It
  must **not** be populated from invoice number, document number, a guessed source row or an inferred line
  reference: the forensic evidence (F-B2-5) establishes that the original source row number is not currently
  recoverable from the persisted representation.
* **Rationale (PO):** asserting a line reference the source does not carry violates the honesty invariant
  (Decision Record §10.2).
* **Implementation consequence:** `row_reference` is populated only through the declared future-extractor
  interface (§11.7 `line_reference`), which has no producer today.
* **Blockers:** **none.**

### B2-D9 — B2 exposes no new endpoint/UI

* **Why it matters:** it determines whether B2 is acceptable without a user-visible surface.
* **PO DECISION (B2-D9 — CLOSED, RATIFIED): no new HTTP endpoint and no frontend work.** B2 establishes durable
  line-item addressability and provenance only; presentation/drill-down remains in the later B3/B4 scope. No
  endpoint may be created merely to expose B2 records unless a later approved architecture decision explicitly
  requires it.
* **Rationale (PO):** avoids a premature API contract and a frontend obligation absent from the ratified batch
  plan.
* **Implementation consequence:** §12.4 stands unchanged; V2 acceptance is by schema, provenance chain and
  runtime evidence.
* **Blockers:** **none.**

### B2-D10 — Confirming the bounded deviation from design §14.3’s field list

* **Why it matters:** the design’s field list is part of the ratified design record, so reductions/additions
  should be an explicit, visible decision (§7.4).
* **PO DECISION (B2-D10 — CLOSED, RATIFIED):** the bounded deviation from Disclosure Model Design §14.3 is
  **accepted**, and the documented reasoning must be preserved. **Removed:** `document_type_code`,
  `confidence_score`, `extracted_at`, `extracted_by`, `processing_origin`. **Added/retained:**
  `materialisation_kind`, `created_at`. In particular, **`processing_origin` is a mutable parent attribute and
  must not be copied into an immutable evidence-line record as though it were historically stable.** No
  additional convenience fields may be added.
* **Rationale (PO):** every retained column must have a producer and a stable purpose; copying mutable parent
  state into immutable evidence would create provenance that can become wrong.
* **Implementation consequence:** §7.2/§7.3/§7.4 stand as the field contract; the V2 static test asserts the
  exact column set.
* **Blockers:** **none.**

### B2-D11 — Do evidence line items fall inside N3 retention (may they ever be deleted)?

* **Why it matters:** it decides whether B2 must enforce immutability with a hard trigger (P7 style) or with
  privileges/no-code-path (chosen, §15.3). N3’s ratified domain list includes **evidence**.
* **PO DECISION (B2-D11 — CLOSED): B2 introduces NO retention/deletion mechanism.** Evidence-line records are
  immutable provenance records. B2 adds **no** soft-delete fields, **no** retention triggers, **no** automatic
  purge, **no** anonymisation logic and **no** deletion jobs. N3 / the separate retention workstream defines
  future retention/deletion/anonymisation semantics if required.
* **Rationale (PO):** an evidence-retention policy is a PO-owned capability whose domain includes evidence; B2
  must not pre-empt it. This decision is deliberately **stronger** than the earlier wording “soft now”, which is
  replaced wherever it appeared (§7.6, §15.3) by this explicit boundary.
* **Implementation consequence:** the B2-1 migration contains no trigger, no soft-delete column and no purge
  path; V2 tests the privilege posture and the RESTRICT behaviour instead of trigger behaviour.
* **Blockers:** **none.**

### B2-D12 — Confirmation that historical snapshots are **not** retro-linked

* **Why it matters:** retro-linking existing snapshots would materially improve historical drill-down — and would
  require inference.
* **PO DECISION (B2-D12 — CLOSED, RATIFIED): NO RETRO-LINKING.** Existing calculation snapshots must never be
  guessed or inferred onto newly materialised evidence lines; historical snapshots retain their original
  provenance granularity. New line-aware calculations may receive `source_line_item_id`.
* **Rationale (PO):** retro-linking requires inference and would manufacture provenance that was never captured.
* **Implementation consequence:** B2 does not rewrite historical snapshots, does not change request-ID
  derivation and does not recalculate historical records merely to obtain line identity (§8.4, §13.4, §15.2).
* **Blockers:** **none.**

**Summary: no decision above blocks B2 implementation.**

### 23.13 Closure summary

| # | Ratified decision | Status | Blocks B2? |
|---|---|---|---|
| B2-D1 | `ON DELETE RESTRICT` — preservation-first; `CASCADE` prohibited | **CLOSED** | No |
| B2-D2 | Detect + report + never rewrite (divergence) | **CLOSED / RATIFIED** | No |
| B2-D3 | Mirror the existing PE item-access boundary | **CLOSED / RATIFIED** | No |
| B2-D4 | Defer the `source_page` defect (F-B2-7) to a separate bounded workstream | **CLOSED** | No |
| B2-D5 | Per-document forward audit + per-run backfill audit + per-item divergence | **CLOSED / RATIFIED** | No |
| B2-D6 | Forward hook at the data-layer choke point (no duplicated callers) | **CLOSED / RATIFIED** | No |
| B2-D7 | Open `extraction_method` vocabulary (no restrictive CHECK) | **CLOSED / RATIFIED** | No |
| B2-D8 | `row_reference` NULL for Class-1 materialisation | **CLOSED / RATIFIED** | No |
| B2-D9 | No new HTTP endpoint / no frontend work | **CLOSED / RATIFIED** | No |
| B2-D10 | Design §14.3 field deviation accepted (reasoning preserved) | **CLOSED / RATIFIED** | No |
| B2-D11 | B2 introduces **no** retention/deletion mechanism | **CLOSED** | No |
| B2-D12 | No retro-linking of historical snapshots | **CLOSED / RATIFIED** | No |

**No blockers remain.** The authoritative PO record is
`docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md`. B2 may proceed to a separate
implementation-authorisation gate; **nothing is implemented by this ratification**.

---

## 24. Risks (deliverable: risks)

| # | Risk | Likelihood | Impact | Mitigation (in this contract) |
|---|---|---|---|---|
| R1 | B2 is mistaken for the extraction fix and “closes” line traceability while PDFs still collapse 8→1 | **High** | High (false assurance) | Root boundary §1.2/§6; `materialisation_kind` makes derived lines visible; P1 remains a named, separate workstream; §11.5 excludes flat records explicitly |
| R2 | Materialisation silently becomes a second extraction/interpretation engine | Medium | High | Eligibility is a pure JSON-membership rule (§11.1); no inference, no heuristics, no aggregate derivation; A6 asserts no extractor calls |
| R3 | Ordinal-based identity drifts when `extracted_data` is corrected | Medium | Medium-High | Divergence detection (§11.3), no rewrite, immutable rows, D15 preserved; policy decision B2-D2 |
| R4 | Historical snapshots appear “unlinked”, read as a defect | **High** | Low-Medium | Document-level chain remains authoritative; §13.4/§15.2 state the deliberate NULL semantics; B2-D12 records the confirm |
| R5 | Audit volume from backfill | Medium | Medium | Per-run audit (B2-D5); counts/hashes only |
| R6 | Adding columns to a hot table (`calculation_snapshots`) affects the calculation write path | Low | Medium | Nullable, no default rewrite (PG11+ metadata-only), no index bloat on inserts beyond one index; clone harness checks parity and row identity |
| R7 | The two invalidated B1 test assertions are deleted rather than amended, removing B3/B4 guards | Medium | Medium | §20.6 mandates amendment + rule that no B3/B4 guard is weakened; implementation report must show before/after |
| R8 | B2 verified only by static tests (repeating the V1 lesson) | Medium | High | §20.5 makes runtime execution mandatory; V2 must state the provisioned environment and hash |
| R9 | Runtime suite skips because no environment is provisioned, and the skip is reported as success | Medium | High | §20.7 declares this explicitly: a skip is **not** a PASS; §18.5 gives the provisioning recipe |
| R10 | Scope creep into B3 (drill-down endpoints/intensity) | Medium | Medium | §14.1 separation table; §22.2 out-of-scope list; B2-D9 |
| R11 | `source_item_id` delete semantics destroying history on a future cleanup | **Closed** | Low | **Resolved by B2-D1 (PO-RATIFIED): `ON DELETE RESTRICT` — a parent delete cannot destroy evidence lines; downstream rows are preserved by their own `SET NULL` links** |
| R12 | The denormalised `dve.source_line_item_id` diverges from the snapshot | Low | Medium | Consistency test (§20.2.15); write path sets it from the snapshot only |
| R13 | Backfill accidentally reads `mapped_data` and invents lines from rewritten results | Medium | Medium | F-B2-4 documented; §11.4 forbids it; A6 and the migration/CQ tests assert the read set |
| R14 | A future retention/janitorial job has no deletion mechanism in B2 | Low | Low | **B2-D11 (PO-RATIFIED): deliberate — B2 introduces no retention/deletion mechanism; N3 / the retention+privacy workstream defines it explicitly (§27.3)** |

---

## 25. Dependency / blocker matrix (deliverable: dependency/blocker matrix)

| # | Item | Type | Direction | Status / effect on B2 |
|---|---|---|---|---|
| 1 | B1 applied (`20260914000000_…`) — schema, RLS helper `p8_disclosure_is_org_member` | **Hard prerequisite** | B1 → B2 | **CLOSED**; B2-1 fails loudly if absent (§16.1) |
| 2 | B1 correction applied (`20260915000000_…`) — privilege posture precedent, NULL-safe index | Prerequisite (pattern) | B1 → B2 | CLOSED |
| 3 | `manual_extraction_items` + `document_processing_queue` + `organization_files` schema (D33) | Prerequisite (schema) | existing → B2 | **Present** [V] |
| 4 | `work_item_effective_entity` / `is_entity_member` helpers (WS4/RC2) | Prerequisite (PE policy) | existing → B2 | **Present** [R]; needed only if B2-D3 = mirror |
| 5 | Calculation engine + `CalculationRequest` | Integration point | B2 → existing | Present; additive optional field only |
| 6 | `audit_trail` + P7 immutability | Integration point | B2 → existing | Present |
| 7 | P1 (extraction fidelity) | **Not a blocker** | P1 ↔ B2 parallel | B2 works without it; line *population* stays thin for flat PDFs until P1 (P8X §16 edge) |
| 8 | P2 (EF-E) | Independent | — | No coupling |
| 9 | B3 / B4 | Successors | B2 → B3 → B4 | B2 must land first; B2 does not pre-implement them |
| 10 | **Provisioned B1+B2 database for runtime V2** | **Verification blocker** | environment → V2 | **Open** (F-B2-16); §18.5 recipe; without it the runtime suite skips |
| 11 | G0-D — production migration strategy for the 34-outstanding backlog | **Deployment blocker** | governance → production | **Open**; B2 adds 2 migrations; production not authorised |
| 12 | G0-A — ESRS E1 identifiers | Not a B2 blocker | G0 → B3 | Open; affects B3 seed rows only |
| 13 | Broad RLS remediation (G0-H) | Separate workstream | — | B2 adds its own posture only; does not remediate |
| 14 | N3 retention configuration | Open PO decision | affects B2-D11 | Non-blocking |
| 15 | F-B2-7 (`source_page` mis-stamping) | Separate defect | — | Recorded as B2-D4; non-blocking |
| 16 | F-B2-4 (`mapped_data` rewrite) | Separate observation | — | Non-blocking; B2 avoids the field |
| 17 | Consultant/PE/customer authorization guards (`ensure_org_access`, `require_org_member`, staff guards) | Prerequisite (app layer) | existing → B2 | Present; B2 reuses, adds none |

---

## 26. Change-control statement and verdict

### 26.1 What this document did **not** do (verified)

* No source file, migration, test, RLS policy, API, frontend file or database row was created, modified or
  deleted; no migration was applied; no production or demo data was touched.
* The only repository changes are the **two mandated documents**.
* The worktree was not reset, cleaned, stashed, checked out, committed or pushed. The 208 pre-existing tracked
  modifications and 73 untracked paths recorded in §3 remain exactly as they were.
* Nothing in this document authorises implementation.

### 26.2 What B2 will be, in one paragraph

B2 adds one org-scoped, immutable, addressable line table (`evidence_line_items`) materialised deterministically
from the *persisted* `extracted_data.line_items[]` array by ordinal — with honest NULLs wherever the source
supplied no location or reference — plus two additive nullable FK columns
(`calculation_snapshots.source_line_item_id`, `disclosure_value_evidence.source_line_item_id`) that close the
line-level hop in the ratified provenance chain, an idempotent, non-destructive, dry-runnable Class-1 backfill
for historical structured data, a best-effort forward hook so new extractions materialise automatically, and
runtime-verified RLS/privilege/audit posture that leaves every pre-existing table, policy, grant and row
untouched. Flat PDF/IMAGE records get **no** line and **no** fabricated precision; no historical document is
re-extracted; the calculation engine is consumed, never replaced.

### 26.3 Verdict (post-ratification)

**`B2 DECISION SET RATIFIED — READY FOR IMPLEMENTATION AUTHORISATION`**

* **B2-D1 … B2-D12 are CLOSED** by the Product Owner (task
  `CT-P8-B2-PO-DECISION-RATIFICATION-20260913-018`); the authoritative record is
  `docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md`.
* The two normative literals changed by the decisions are **already reflected in this contract**:
  `source_item_id ON DELETE RESTRICT` (§7.1) and the explicit no-retention boundary (§7.6, §15.3).
* Every mandated deliverable (A–S) remains addressed with an exact, testable specification, and **no other
  architectural decision, scope boundary, evidence tag or source grounding was altered**.
* Two environment/deployment items remain declared (§20.7, §25 items 10–11). They are verification and
  deployment **preconditions, not decision blockers**.
* **F-B2-7** and the **PDF/IMAGE extraction remediation** remain separate workstreams (§6.1, §27).
* **Implementation of B2 is NOT authorised** by this contract or by the ratification.

**Next action (not taken here):** a separate bounded **B2 implementation-authorisation gate**; then B2
implementation and V2 verification; only then B3.

---

## 27. Finding and workstream dispositions (post-ratification)

### 27.1 F-B2-7 — `source_page` semantic defect (separate remediation; **not** B2)

**Preserved finding (PO-accepted; wording equivalent in meaning to the PO's disposition):**

> `source_page` currently has a verified semantic defect: an auto-processing path can persist `page_count` into
> `source_page`, while downstream evidence logic can interpret non-NULL `source_page` as an exact source
> location. B2 does not remediate, reinterpret, copy or propagate this value as line-level evidence. Separate
> remediation is required.

* **Evidence:** `backend/services/automatic_processing.py:1134` (`source_page=job.metadata.get("page_count")`),
  `backend/api/v3_processing_workflow.py:991` (`"page_count": item.page_count or 1`),
  `backend/domain/evidence.py:145,166,36` (`has_page = page is not None` → `COMPLETE`).
* **PO disposition (B2-D4):** **deferred to a separate bounded remediation workstream.** Implementation is
  **not** assigned to B2 and is not authorised by this contract.
* **B2 boundary:** B2 never copies, infers, silently transforms or propagates the value;
  `evidence_line_items.source_page` is populated only from a genuine per-line value (§11.7) and is otherwise
  NULL. B2 does not change evidence classification.

### 27.2 F-B2-13 — B1 test boundary (AMEND, NEVER DELETE)

**Rule (PO-RATIFIED):** the B1 tests that asserted “no B2/B3/B4 objects” must be **AMENDED, NEVER DELETED**
when B2 implementation occurs:

* `backend/tests/integration/test_disclosure_b1_runtime.py::test_b2_b3_b4_boundary_untouched`
* `backend/tests/unit/data/test_disclosure_sql_typing.py::test_no_b2_b3_b4_objects_in_the_repository`

The **purpose** of the B3/B4 protection must remain intact: the B3/B4 negative assertions are preserved and
only the B2-absence assertions move into the B2 suite. The two B1 **migration-text** guards
(`test_no_b2_b3_b4_tables`, `test_no_source_line_item_id_column`) read the B1 migration file, which B2 does not
edit, and therefore **remain valid and must not be weakened**. Any amended test file is part of B2 scope
(§20.6, §22.1 item 10) and must be listed with before/after text in the B2 implementation report.

### 27.3 N3 retention / deletion / anonymisation of evidence lines (separate workstream)

B2 introduces **no** retention or deletion mechanism (B2-D11). If retention, deletion or anonymisation of
evidence lines is ever required, it must be designed and authorised as part of **N3 / the separate
retention+privacy workstream**, with its own audit and verification. Because `source_item_id` is
`ON DELETE RESTRICT` (B2-D1), such a workstream must address evidence lines **explicitly** rather than relying
on a cascade.

### 27.4 PDF/IMAGE extraction remediation (separate investigation workstream)

Recorded in **§6.1** (PO clarification, 2026-09-13). It is **not** B2 implementation, is **not** authorised
here, and must be issued as its own bounded forensic+architecture task answering the twelve questions in §6.1.

---

## 28. Ratification traceability

| Artefact | Role |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md` | this contract — the post-ratification implementation baseline |
| `docs/architecture/CARBONTALLY_PHASE8_B2_PO_DECISION_RATIFICATION_20260913.md` | **authoritative PO decision record for B2-D1…B2-D12** |
| `docs/cline/reports/CT-P8-B2-IMPLEMENTATION-CONTRACT-20260913-017.md` | contract task report (pre-ratification) |
| `docs/cline/reports/CT-P8-B2-PO-DECISION-RATIFICATION-20260913-018.md` | ratification task report |

**Status:** B2-D1…B2-D12 **CLOSED**; **blockers: none**; implementation **not** authorised.
