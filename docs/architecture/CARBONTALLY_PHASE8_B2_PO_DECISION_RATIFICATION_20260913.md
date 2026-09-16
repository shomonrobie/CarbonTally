# CarbonTally — Phase 8 Reporting / Disclosure
## Batch B2 — Evidence / Line-Item Addressability — PO DECISION RATIFICATION

**Task identity:** `CT-P8-B2-PO-DECISION-RATIFICATION-20260913-018`
**Task type:** PO DECISION CLOSURE + CONTRACT RATIFICATION ONLY
**Date:** 2026-09-13
**Contract ratified:** `docs/architecture/CARBONTALLY_PHASE8_B2_IMPLEMENTATION_CONTRACT_20260913.md`
(produced under `CT-P8-B2-IMPLEMENTATION-CONTRACT-20260913-017`)
**Pre-ratification contract verdict:** `B2 IMPLEMENTATION CONTRACT COMPLETE — READY FOR PO REVIEW`
**Status after this record:** **B2-D1 … B2-D12 CLOSED / PO-RATIFIED — BLOCKERS: NONE**
**Implementation:** **NOT AUTHORISED by this task.** A separate B2 implementation-authorisation gate is required.
**Evidence tags:** **[PO]** product-owner ruling · **[D]** ratified design/governance · **[R]** repository fact · **[V]** verified runtime/DB

---

## 1. Purpose and authority

This document is the **authoritative PO decision record** for B2-D1 … B2-D12. It closes the twelve decisions
that the B2 implementation contract surfaced for review and records, for each: the **PO decision**, its
**rationale**, its **implementation consequence**, and the explicit **blocker status (none)**.

This record **ratifies** the contract; it does not authorise implementation. It changes no code, no migration,
no test, no RLS policy, no extraction behaviour, no factor matching and no data.

## 2. What this ratification does and does not do

| Does | Does not |
|---|---|
| Closes B2-D1…B2-D12 as PO decisions | Authorise B2 implementation |
| Fixes `source_item_id` as **`ON DELETE RESTRICT`** (preservation-first; `CASCADE` prohibited) | Create any migration |
| Fixes the **no-retention/deletion** boundary for B2 | Modify backend/frontend code, tests or RLS |
| Records F-B2-7 as a **separate remediation finding** | Fix `source_page` semantics |
| Records the **PDF/IMAGE extraction investigation** as a separate workstream | Modify extraction, OCR or AI gating |
| Preserves every B2 scope boundary and evidence tag | Perform any historical backfill or production action |
| Records that historical snapshots are **never** retro-linked | Commit or push |

---

## 3. Decision record — B2-D1 … B2-D12

### B2-D1 — `evidence_line_items.source_item_id` delete semantics

* **PO DECISION:** **`RESTRICT` / preservation-first. `CASCADE` must not be used.**
* **Rationale [PO]:** B2 evidence-line records are authoritative historical provenance records and must not be
  automatically destroyed as a consequence of deleting the source extraction item. The absence of a real
  extraction-item deletion path today (`ManualExtractionRepository.delete()` is a no-op stub [R]) does **not**
  justify destructive FK semantics.
* **Implementation consequence:** `source_item_id` stays `NOT NULL` with **`ON DELETE RESTRICT`**; an
  extraction item cannot be deleted while its evidence lines exist; `CASCADE` is prohibited; B2 introduces **no**
  replacement deletion/anonymisation workflow. Any future deletion/anonymisation must be separately designed and
  authorised under the retention/privacy workstream.
* **Blockers:** **none.**

### B2-D2 — Divergence / supersession

* **PO DECISION:** **DETECT + REPORT + NEVER REWRITE.**
* **Rationale [PO]:** satisfies `DM-7` (“no row is rewritten to manufacture provenance”) and keeps D15
  reproducibility absolute.
* **Implementation consequence:** if persisted `extracted_data.line_items[]` no longer derives the same
  `payload_hash`, B2 detects, reports and **preserves** the existing record — never silently updating, deleting,
  or creating a replacement identity for the same ordinal. Reruns use `ON CONFLICT DO NOTHING`. Any future
  supersession/versioning mechanism requires a **separately authorised design**.
* **Blockers:** **none.**

### B2-D3 — PE read access

* **PO DECISION:** **mirror the existing PE item-access boundary.**
* **Rationale [PO]:** PE access to `evidence_line_items` must not widen the consultant/PE scope beyond the
  source extraction item they can already access; the existing entity/member authorization boundary is reused;
  no new consultant authorization model is created.
* **Implementation consequence:** one additive `SELECT` policy using
  `is_entity_member(work_item_effective_entity(source_item_id))`, mirroring
  `manual_extraction_items_entity_select`; PE-A→PE-B and cross-tenant denials are mandatory negative tests.
* **Blockers:** **none.**

### B2-D4 — `source_page` defect (F-B2-7)

* **PO DECISION:** **DEFER to a separate bounded remediation workstream.** F-B2-7 is accepted as real.
* **Rationale [PO]:** it is a source-page *semantics* defect in an existing auto-processing write path, not an
  addressability problem; changing it inside B2 would alter evidence classification for existing data.
* **Implementation consequence:** B2 **must not** fix the defect, reinterpret existing `source_page`, copy the
  value as an exact line location, silently transform page counts into page references, or change evidence
  classification. The defect is recorded (§6) and the scope boundary is maintained.
* **Blockers:** **none.**

### B2-D5 — Audit granularity

* **PO DECISION:** one **forward materialisation audit event per source document**; one **summary audit event
  per backfill run**; **divergence events per affected item/ordinal**.
* **Rationale [PO]:** proportionate, bounded audit volume on an append-only (immutable) audit log while
  preserving the events that matter.
* **Implementation consequence:** audit payloads must not contain source document contents, line values, signed
  URLs or secrets; the **existing `audit_trail`** is used; **no parallel audit system** is created.
* **Blockers:** **none.**

### B2-D6 — Forward hook

* **PO DECISION:** place forward materialisation at the **data-layer choke point** (`ManualExtractionRepository`).
* **Rationale [PO]:** one reviewed hook cannot be forgotten; duplicating materialisation across individual
  extraction-pipeline callers guarantees future omissions.
* **Implementation consequence:** the hook lives in `save_extracted_data` (and `update_item` when
  `extracted_data` is supplied), remains best-effort, and must never block the extraction save.
* **Blockers:** **none.**

### B2-D7 — `extraction_method`

* **PO DECISION:** **open vocabulary — no restrictive `CHECK` constraint.**
* **Rationale [PO]:** avoids coupling B2 to the separate extraction-fidelity/P1 workstream; the column is
  observational, not a state-machine input.
* **Implementation consequence:** the column stays `varchar NOT NULL DEFAULT 'unknown'`; known values are
  documented but not enforced.
* **Blockers:** **none.**

### B2-D8 — `row_reference`

* **PO DECISION:** for Class-1 materialisation, **`row_reference` remains NULL** — never populated from invoice
  number, document number, a guessed source row, or an inferred line reference.
* **Rationale [PO]:** the forensic evidence establishes that the original source row number is not currently
  recoverable from the persisted representation; asserting a line reference the source does not carry violates
  the honesty invariant (Decision Record §10.2).
* **Implementation consequence:** the column is populated only through the declared future-extractor interface
  (`line_reference`), which has no producer today.
* **Blockers:** **none.**

### B2-D9 — API / frontend

* **PO DECISION:** **no new HTTP endpoint; no frontend work.**
* **Rationale [PO]:** B2 establishes durable line-item addressability and provenance; presentation/drill-down
  remains in later B3/B4 scope; no endpoint may be created merely to expose B2 records.
* **Implementation consequence:** existing response shapes are unchanged; V2 acceptance is by schema, provenance
  chain and runtime evidence.
* **Blockers:** **none.**

### B2-D10 — Field deviation from Design §14.3

* **PO DECISION:** **RATIFIED — the bounded deviation is accepted**, with the documented reasoning preserved.
* **Removed:** `document_type_code`, `confidence_score`, `extracted_at`, `extracted_by`, `processing_origin`.
  **Added/retained:** `materialisation_kind`, `created_at`.
* **Rationale [PO]:** in particular, **`processing_origin` is a mutable parent attribute** and therefore must
  not be copied into an immutable evidence-line record as though it were historically stable
  (`mark_pe_origin_if_unset` can change it after materialisation [R]). Columns with no producer
  (`confidence_score`, per-line `extracted_at`/`extracted_by`) or that belong to the document
  (`document_type_code`) are excluded.
* **Implementation consequence:** no additional convenience fields may be added; the field contract stands as
  contract §7.2–§7.4.
* **Blockers:** **none.**

### B2-D11 — Retention / deletion

* **PO DECISION:** **B2 introduces NO retention/deletion mechanism.** Evidence-line records are immutable
  provenance records.
* **Rationale [PO]:** retention of evidence is a PO-owned capability whose domain includes evidence; B2 must not
  pre-empt it. This decision is deliberately **stronger** than the earlier “soft now” phrasing, which is replaced
  by this explicit boundary everywhere it appeared.
* **Implementation consequence:** B2 adds **no** soft-delete field, **no** retention trigger, **no** automatic
  purge, **no** anonymisation logic and **no** deletion job. N3 / the separate retention workstream defines
  future retention/deletion/anonymisation semantics if required.
* **Blockers:** **none.**

### B2-D12 — Historical snapshot retro-linking

* **PO DECISION:** **NO RETRO-LINKING.**
* **Rationale [PO]:** existing snapshots must never be guessed or inferred onto newly materialised evidence
  lines; retro-linking would manufacture provenance that was never captured.
* **Implementation consequence:** historical snapshots retain their original provenance granularity; new
  line-aware calculations may receive `source_line_item_id`; B2 does not rewrite historical snapshots, does not
  change request-ID derivation, and does not recalculate historical records merely to obtain line identity.
* **Blockers:** **none.**

### 3.1 Closure summary

| # | Decision | Status | Blocks B2? |
|---|---|---|---|
| B2-D1 | `ON DELETE RESTRICT` — preservation-first; `CASCADE` prohibited | **CLOSED** | **No** |
| B2-D2 | Detect + report + never rewrite | **CLOSED** | **No** |
| B2-D3 | Mirror the existing PE item-access boundary | **CLOSED** | **No** |
| B2-D4 | F-B2-7 deferred to a separate remediation workstream | **CLOSED** | **No** |
| B2-D5 | Per-document forward audit + per-run backfill audit + per-item divergence | **CLOSED** | **No** |
| B2-D6 | Forward hook at the data-layer choke point | **CLOSED** | **No** |
| B2-D7 | Open `extraction_method` vocabulary | **CLOSED** | **No** |
| B2-D8 | `row_reference` NULL for Class-1 | **CLOSED** | **No** |
| B2-D9 | No new endpoint / no frontend work | **CLOSED** | **No** |
| B2-D10 | Design §14.3 field deviation accepted | **CLOSED** | **No** |
| B2-D11 | No retention/deletion mechanism in B2 | **CLOSED** | **No** |
| B2-D12 | No retro-linking of historical snapshots | **CLOSED** | **No** |

**EXPLICIT BLOCKERS: NONE.** No decision is deferred, unresolved or conditional.

---

## 4. Core B2 architecture confirmed (ratified)

The following are **re-confirmed** by this ratification and are unchanged by it [PO]/[D]:

1. `extracted_data.line_items[]` remains the **extraction-output / eligibility source**.
2. B2 **never writes or rewrites** that JSONB extraction output.
3. `evidence_line_items` is the **immutable materialised provenance authority**.
4. Line identity is the **persisted array ordinal**: `UNIQUE (source_item_id, line_number)`.
5. `line_number` is **1-based**.
6. **Gaps are preserved.**
7. Lines are **never silently renumbered**.
8. `mapped_data` is **NOT** an identity source.
9. `payload_hash` provides **divergence detection**.
10. Existing structured `line_items[]` can be **deterministically/idempotently** materialised (Class-1).
11. Flat historical PDF/IMAGE records **cannot** be converted into true line records merely by inference.
12. **No silent historical PDF/IMAGE re-extraction.**
13. `calculation_snapshots.source_line_item_id` is **nullable**.
14. `disclosure_value_evidence.source_line_item_id` is **nullable**.
15. `source_line_item_id` **MUST NOT** enter calculation request-ID derivation.
16. Existing **document-level provenance remains valid** where no genuine line-level provenance exists.
17. **No new calculation engine.**
18. **No factor-matching changes.**
19. B2 does **not** become the PDF/IMAGE extraction-fidelity remediation.

---

## 5. F-B2-7 disposition — separate remediation finding

**Finding (PO-accepted as real):**

> `source_page` currently has a verified semantic defect: an auto-processing path can persist `page_count` into
> `source_page`, while downstream evidence logic can interpret non-NULL `source_page` as an exact source
> location. B2 does not remediate, reinterpret, copy or propagate this value as line-level evidence. Separate
> remediation is required.

* **Evidence [R]:** `backend/services/automatic_processing.py:1134`
  (`source_page=job.metadata.get("page_count")`); `backend/api/v3_processing_workflow.py:991`
  (`"page_count": item.page_count or 1`); `backend/domain/evidence.py:145,166,36`
  (`has_page = page is not None` → `COMPLETE`).
* **PO disposition (B2-D4):** **deferred to a separate bounded remediation workstream.** F-B2-7 is accepted as
  real. Implementation of this defect is **not** assigned to B2 and is **not** authorised by this record.
* **Implementation consequence:** the defect and its risk remain recorded (§5) and the scope boundary is
  maintained; B2 **must not** fix the defect, reinterpret existing `source_page`, copy the value as an exact
  line location, silently transform page counts into page references, or change evidence classification. A
  **separate task** (not B2) investigates/remediates source-page semantics.
* **Blockers:** **none.**

---

## 6. F-B2-13 disposition — B1 test boundary

**Rule (PO-RATIFIED): AMEND, NEVER DELETE.**

The B1 tests that asserted “no B2/B3/B4 objects” must be **amended** when B2 implementation occurs, so that the
B2-absence assertions match the post-B2 reality while the **B3/B4 protection remains intact**:

* `backend/tests/integration/test_disclosure_b1_runtime.py::test_b2_b3_b4_boundary_untouched`
* `backend/tests/unit/data/test_disclosure_sql_typing.py::test_no_b2_b3_b4_objects_in_the_repository`

**Must not be weakened:** the two B1 **migration-text** guards
(`test_disclosure_migration.py::test_no_b2_b3_b4_tables`, `::test_no_source_line_item_id_column`) read the B1
migration file, which B2 does not edit — they remain valid and must stay intact.

**Implementation consequence:** the amended test files are part of B2 scope; the B2 implementation report must
list each amendment with before/after text and must demonstrate that no B3/B4 guard was removed.

---

## 7. PDF/IMAGE extraction remediation — separate future investigation (PO clarification)

The Product Owner has **separately decided** that the PDF/IMAGE extraction problem is to be investigated as its
**own bounded workstream**. This **does not authorise implementation**.

**Problem to be investigated (established forensic finding
`CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912`):** an 8-line PDF invoice can currently become **one**
flattened extracted object, because the deterministic PDF path selects a single activity/quantity/unit record
and can bypass AI line extraction when completeness is scored as sufficient.

The investigation must answer:

1. What should the canonical PDF/IMAGE line-extraction architecture be?
2. When should deterministic extraction produce **multiple** lines?
3. When should **AI** extraction be invoked?
4. How should **extraction completeness** be scored for multi-line documents?
5. How should **OCR text and layout** information be used?
6. How can **source line identity** be preserved?
7. How should **page number and source location** semantics be represented correctly (F-B2-7, §5)?
8. How should **confidence/ambiguity** be represented?
9. How should **extraction corrections** affect provenance?
10. How should **historical documents** be handled?
11. How can extraction fidelity improve **without corrupting existing provenance**?
12. What is the **exact boundary** between extraction output and B2 evidence-line materialisation?

**Binding boundaries:**

* This workstream is **NOT** part of B2 and is **NOT** part of this ratification task.
* **No** extraction code, OCR setting, AI prompt/gate, or `source_page` behaviour may be modified here.
* A separate OHD/Cline forensic+architecture task may be issued for that workstream.
* B2's only interface to it is the **declared, optional** per-line element keys (`page`, `line_reference`,
  `extraction_method`) already specified in the contract §11.7 — B2 requires **no** extractor change.

---

## 8. B2 implementation boundary (preserved)

**IN SCOPE for B2 (unchanged by this ratification):**

* `evidence_line_items`;
* the **two** B2 additive migrations;
* line identity (persisted ordinal);
* deterministic materialisation;
* the forward hook (data-layer choke point);
* the Class-1 structured backfill mechanism;
* divergence detection;
* calculation-snapshot line linkage (`calculation_snapshots.source_line_item_id`);
* disclosure-evidence line linkage (`disclosure_value_evidence.source_line_item_id`);
* audit (three actions, existing `audit_trail`);
* RLS/privilege posture **for the new objects only**;
* the required tests;
* runtime verification (V2);
* the **required B1 test amendments** (§6);
* B2 documentation and reports.

**OUT OF SCOPE for B2:**

* PDF/IMAGE extraction-fidelity remediation; OCR redesign; AI extraction gate changes;
* historical PDF/IMAGE re-extraction;
* P2 EF-E factor matching;
* B3; B4; Phase 8-X;
* broad RLS remediation;
* the legacy report route;
* subscription/allowance;
* customer-shaped end-to-end calculation work;
* full ESRS/CSRD implementation;
* N3 retention implementation;
* the `source_page` semantic fix (§5);
* retro-linking historical snapshots.

---

## 9. Implementation authorisation

**Implementation of B2 is NOT authorised by this task or by this record.**

* This task is **documentation/governance only**: no code, migration, test, RLS, extraction, factor-matching or
  data change was made, and none is authorised by it.
* The B2 implementation remains subject to a **separate, explicitly bounded B2 implementation-authorisation
  gate** (the next task in the sequence).
* Production application of any B2 migration remains additionally blocked pending the outstanding-migration
  decision (**G0-D**): the 34 previously-outstanding migrations remain a production deployment blocker, to
  which B2 adds 2.
* Runtime verification (V2) requires a **provisioned B1+B2 disposable clone**; without it the runtime suite
  **skips**, and a skip is **not** a pass.

## 10. Change control and consistency verification

| Check | Result |
|---|---|
| Documents written by this task | Contract update; this ratification record; the ratification report. **Nothing else.** |
| Source / migration / test / RLS / API / frontend change | **None.** |
| Database change or migration applied | **None** (read-only introspection only). |
| Extraction behaviour changed | **None.** |
| Factor matching changed | **None.** |
| Historical backfill performed | **None.** |
| Commit / push / worktree disturbance | **None.** |
| Contract internal consistency | B2-D1…B2-D12 all marked **CLOSED / PO-RATIFIED**; the normative DDL carries `ON DELETE RESTRICT`; no residual `CASCADE` recommendation, no residual “soft retention” wording, no residual open-decision language; no unrelated architectural decision altered. |
| Scope boundaries preserved | Yes — contract §6/§6.1, §22, §27; this record §7–§8. |

## 11. Verdict

**`B2 PO DECISION RATIFICATION COMPLETE — READY FOR IMPLEMENTATION AUTHORISATION`**

The twelve decisions are closed, the contract reflects them, **no blockers remain**, and B2 may proceed to a
separate implementation-authorisation gate. **Nothing has been implemented.**
