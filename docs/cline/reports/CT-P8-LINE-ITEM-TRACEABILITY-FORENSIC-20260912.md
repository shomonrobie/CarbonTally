# CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912

**Task identity:** `CT-P8-LINE-ITEM-TRACEABILITY-FORENSIC-20260912` (formalized under governance task `CT-P8-G0-GOVERNANCE-CONSOLIDATION-20260912-008`)
**Status:** FORMALIZED FORENSIC RECORD — **READ-ONLY; NOTHING IMPLEMENTED**
**Date:** 2026-09-12
**Repository baseline:** branch `main`, HEAD `19e4f01c176eee5870f3c15038b6e7c68b23281c`
**Evidence tags:** **[R]** repository fact · **[V]** verified · **[U]** unresolved · **[I]** interpretation · **[REC]** recommendation

---

## 1. Purpose and read-only nature

This document **formalizes the line-item extraction forensic findings that were already established**
during the September-12 2026 Phase 8 investigation. It is a durability/governance action: the findings
previously existed only in transient investigation output (the ChatGPT chat-history addendum), not as a
repository file.

**This is NOT a new investigation.** The task that produced this document explicitly required:
*"This is a read-only documentation/formalisation task — do NOT perform a new forensic investigation."*
The root cause, the affected code paths and the classification below were established before this
document was written. Nothing in this document was implemented, reproduced by execution, or fixed.

**Absolute non-goals (respected):** no schema change; no migration; no API change; no frontend change;
no extraction/OCR/AI change; no calculation change; no factor change; no evidence-persistence change; no
historical re-extraction; no `evidence_line_items`; no `source_line_item_id`; no commit; no push.

---

## 2. Evidence sources

| # | Source | Kind |
|---|---|---|
| 1 | `backend/services/automatic_extraction.py` (`_extract_pdf`, `_pdf_text`, `_completeness`, `_rows_to_line_items`) | [R] |
| 2 | `backend/services/extraction_suggestions.py` (`suggest`, `_suggest_quantity_unit`, `_ACTIVITY_KEYWORDS`, `_NUMBER_UNIT_RE`, `_KNOWN_UNITS`) | [R] |
| 3 | `backend/services/ai_document_extraction.py` (`extract_candidate`, completeness via `completeness_score`) | [R] |
| 4 | `backend/services/automatic_processing.py` (AI gate at `:404–438`; merge at `:600–615`) | [R] |
| 5 | `backend/api/v3_operations.py` (`line_items` read/write at `:467–474, 573, 1180, 1817`; flat picker inputs at `:959–960`) | [R] |
| 6 | `backend/api/v3_processing_workflow.py` (`:830` line_items; `:1109–1113` picker) | [R] |
| 7 | `backend/engines/calculation.py` (`CalculationRequest`, `calculate`, snapshot provenance) | [R] |
| 8 | `backend/domain/evidence.py` | [R] |
| 9 | `frontend/src/v3/ops/ExtractionPanel.jsx`, `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` | [R] |
| 10 | `docs/ChatGPT/chat_history/phase 8 implementaion chat history 01.md` §§20–21 | [V] prior established evidence |
| 11 | `docs/architecture/CARBONTALLY_PHASE8_DISCLOSURE_MODEL_DESIGN_20260912.md` §14 | [D] design |

**Note:** the originally referenced main forensic report (§1–15) was never persisted as a file; §§16–22
survive in the chat-history addendum. This document therefore consolidates the established substantive
findings into one durable record.

---

## 3. The observed problem (8 → 1)

**Observation [V]:** a multi-line PDF invoice containing **8 visible source line items** produced
**exactly 1** extracted object. The single retained object was also **semantically incoherent** — an
activity label taken from one invoice line paired with a quantity/unit taken from a different line
(observed: activity `Waste` + quantity/unit `38.4 m³` from the water line).

---

## 4. PDF / IMAGE extraction path [R]

```text
PDF bytes
  → _pdf_text(content)                              automatic_extraction.py:199–223
        pdfplumber text  →  Tesseract OCR  →  pypdfium2 render + ONNX OCR
  → if usable text:
        extraction_suggestions.suggest(text[:200_000])   :238
        → FLAT single record (activity/quantity/unit/supplier/date/invoice_number)
  → _extract_pdf returns {"extracted_data": <flat dict>}   :226–248
IMAGE
  → OCR  →  same suggest() pass  →  same FLAT record
```

**Key fact [R]:** the deterministic PDF and IMAGE paths return **one flat record**. They do **not**
emit `line_items[]`. There is no per-source-line structure on these paths.

---

## 5. CSV / XLSX line-item path [R]

```text
CSV/XLSX rows
  → _rows_to_line_items(rows[1:], header)   automatic_extraction.py:349–400
  → extracted = {"line_items": [ {activity, quantity, unit, supplier, date, ...}, … ]}
```

**Key fact [R]:** the tabular path **is** line-aware and persists `line_items[]`. So line-item capability
already exists in the platform — it is simply absent from the deterministic PDF/IMAGE path.

---

## 6. Deterministic PDF suggestion behaviour [R]

`extraction_suggestions.suggest(text)` returns a **flat** `suggested_data` dict:

- header/identity fields via `_FIELD_ALIASES` (supplier, invoice_number, date, amounts, currency);
- **one** `activity` string;
- **one** `quantity` + **one** `unit` pair.

It never returns a line array. The document's whole text is treated as a single logical record.

## 7. Activity-keyword selection [R]

```python
_ACTIVITY_KEYWORDS = (
    ("Natural gas", …), ("Electricity", …), ("Diesel", …),
    ("Petrol", …), ("Waste", …), ("Water", …), ("Travel", …),
)
activity = next((label for label, pattern in _ACTIVITY_KEYWORDS if pattern.search(text)), None)
```
`extraction_suggestions.py:39–47, 147–154`

**Behaviour:** the **entire document text** is searched; the **first keyword in tuple order** that
matches **anywhere** wins. For a document containing both `waste` and `water` lines, `Waste` (index 4)
beats `Water` (index 5) **regardless of which line the activity actually belongs to**. This is why the
observed activity was `Waste` when the quantity came from the water line.

**Path-dependence [R]:** `automatic_extraction._ACTIVITY_KEYWORDS` and
`extraction_suggestions._ACTIVITY_KEYWORDS` are **different tuples** (e.g. `Travel` vs
`Business travel`), so identical content can yield different labels depending on which path runs.

## 8. Quantity / unit candidate selection [R]

```python
_NUMBER_UNIT_RE = re.compile(r"(?P<qty>\d[\d,]*(?:\.\d+)?)\s*(?P<unit>[a-zA-Z³0-9]+)")
candidates.append((qty, unit))  for matches in fields with "consumption"/quantity/usage/volume,
                                else in every field value
qty, unit = candidates[0]       # FIRST candidate wins
```
`extraction_suggestions.py:51–56, 75–102`

**Behaviour:** the parser returns the **first** `<number><unit>` pair whose unit is in `_KNOWN_UNITS`.
Nothing ties that number to the line whose activity label was chosen. In a report-style PDF where the
first numeric+unit token belongs to a different line than the matched keyword, the two fields mix.

## 9. Why cross-line field mixing occurs [V]

Because activity and quantity/unit are chosen by **two independent whole-document scans with different
selection rules**:
- activity = first keyword match by **tuple order**;
- quantity/unit = first `<number><unit>` match by **text order**.

On a multi-line PDF both scans operate over the same flat text but disagree about which line they are
describing. The result is a single flat record whose fields belong to different source lines. This is
**deterministically reproducible** (not random) for a document containing both `waste` and `water`
content.

## 10. AI extraction path [R]

`backend/services/ai_document_extraction.py` composes the same deterministic text layer with an optional
LLM client and returns a **candidate** `extracted_data` envelope. The AI path **can** emit a
`line_items[]` structure. Its output is candidate-only: it still passes the completeness gate, factor
matching, validation and the canonical `CalculationRequest` boundary; units are canonicalised through
`core.units.normalize_unit`.

## 11. Completeness gating (why the multi-line AI path can be suppressed) [R]

`backend/services/automatic_processing.py:404–438`:

```python
if self._ai_extraction_engine is not None and (
    confidence < AUTO_EXTRACT_CONFIDENCE_MIN
    or job.metadata.get("prefer_ai")
    or job.metadata.get("force_ai")
    or job.metadata.get("ai_required")
):
    … run AI candidate …
```

`_completeness` (`automatic_extraction.py:179–195`) scores a **flat** record on `activity/quantity/unit`
only. A flat PDF record that happens to populate all three fields therefore **clears the threshold**, so
the AI line-item path **never runs**. The richer line-item capability exists but is gated off precisely
in the case where the flat record looks "complete" — i.e. the 8→1 case.

## 12. Persistence findings [R]

- Extraction content is persisted primarily as **JSONB** (`manual_extraction_items.extracted_data` /
  `.mapped_data`; `document_processing_queue.extracted_data` / `.mapped_data`;
  `customer_documents.extracted_data`).
- Line items live **inside** those JSONB documents (`extracted.line_items`, `mapped_data.line_items`).
- **No addressable, indexed line-item row exists**; line identity is not durably represented as its own
  identity on the PDF/IMAGE path.

---

## 13. API findings [R]

- The ops/processing APIs **understand** `line_items[]` when it is present:
  `v3_operations.py:471–474, 573` (read + write back per-line results),
  `v3_operations.py:1180, 1817`, `v3_processing_workflow.py:830`.
- The **mapper/picker** consumes only the **flat** fields:
  `search_activity = extracted["activity"]`, `search_unit = extracted["unit"]`
  (`v3_operations.py:959–960`; `v3_processing_workflow.py:1109–1110`). There is **no line array in the
  mapping-options path**, so even when `line_items[]` exists it is not the picker's input.
- Therefore the API layer is **not collapsing** lines (it handles them when present); the collapse
  happens **upstream** in extraction.

## 14. Frontend findings [R]

- `frontend/src/v3/customer/ProcessingItemWorkspace.jsx` and `frontend/src/v3/ops/ExtractionPanel.jsx`
  render the **flat** extracted fields and the `no_factors_reason` message faithfully.
- The UI has **no** line-level breakdown surface for a multi-line PDF, so a user sees one activity/unit
  pair with no indication that the source carried 8 lines.
- This is a **usability consequence**, not the cause: the frontend is rendering the defective flat record
  correctly. **[I]**

## 15. Calculation findings [R]

- `backend/engines/calculation.py` `CalculationRequest` carries **one** factor per request; the engine
  computes one emission per call and persists an immutable SHA-256 snapshot.
- **Multi-line calculation already works**: the operations layer iterates `mapped_data.line_items`,
  assigning a factor and emission per line. **The calculation layer is not the defect and must not be
  replaced.** The defect is that the 8 lines never reach this layer.

## 16. Provenance findings [R]

- `calculation_snapshots` carries `source_item_id` (**document-level** extracted item), `source_file` and
  `source_page`. It does **not** reach an individual invoice line.
- `backend/domain/evidence.py` is **document-level + page**; where no finer granularity exists it records
  a partial/synthetic row.
- **Consequence [I]:** current provenance is **coarser** than the Phase 8 row/invoice-line traceability
  requirement in the multi-line case, because the line identity was never extracted.

## 17. Historical-data implications [V]

1. Records that **already persisted `line_items[]`** (CSV/XLSX; AI-line documents) can support
   **deterministic, idempotent** population of line-level evidence.
2. **Historical flat PDF/IMAGE records** without persisted line structure **cannot** be converted into
   true line-level evidence merely by reading the existing JSONB — the per-line distinction was never
   recorded.
3. Historical records with OCR/text available would require a **separately implemented and verified
   re-parsing/extraction capability** to reconstruct line structure.
4. Historical documents must **not** be silently re-extracted merely to populate the Disclosure Model.
5. Where the source does not support line identity, **no line-level provenance may be manufactured**.

## 18. Root-cause classification [V]

| Code | Classification | Verdict |
|---|---|---|
| **A** | **Extraction** — deterministic PDF/IMAGE path produces a flat record and can mix fields across lines | **PRIMARY ROOT CAUSE** |
| **B** | Persistence collapse (JSONB vs rows losing lines) | **EXCLUDED** — JSONB preserves whatever extraction produced; the loss is upstream |
| **C** | API serialization / query collapse (API dropping lines) | **EXCLUDED** — the API correctly reads/writes `line_items[]` when present |
| **D** | Frontend usability gap (no line-level surface) | **SUBSIDIARY** — a consequence, not the cause |
| **E** | Downstream granularity — provenance/evidence cannot reach the line | **ARCHITECTURAL CONSEQUENCE** |
| **F** | Downstream provenance/reporting fidelity | **ARCHITECTURAL CONSEQUENCE** |

**Summary:** **Primary = A (extraction). Architectural consequences = E/F. Subsidiary = D. Excluded = B, C.**

---

## 19. Phase 8 impact [V]

- **P1 (extraction line-item fidelity)** is a genuine **Phase 8 blocker for row-level traceability**: the
  Disclosure Model's evidence chain (`DM-7`, Decision Record §10) cannot reach an invoice line if the
  PDF/IMAGE path never extracts lines.
- The availability assessment assigns this to **batch P1** (a separate, parallel-safe implementation
  batch), and this document confirms that classification.
- It is **not** a calculation defect, **not** an API defect, **not** a persistence defect, and **not** a
  FactorMatchingEngine defect.
- **P2 (EF-E)** is a separate defect and must not be bundled with P1.

## 20. Recommended bounded remediation [REC]

**Reuse-first, minimal, separately authorised.**

1. **Preserve multiple source lines on the PDF/IMAGE path** by reusing the existing `line_items[]`
   structure that the CSV/XLSX path already emits — do **not** build a second extraction system.
2. **Allow the multi-line path** by adjusting the completeness gating so a technically "complete" flat
   record does not suppress a genuinely multi-line document (reuse the existing gate; do not rewrite the
   AI engine).
3. **Make line identity addressable** in the disclosure/evidence layer via `evidence_line_items` +
   one additive `calculation_snapshots.source_line_item_id` (per the Decision Record §10 design) — an
   acceptance invariant, **not** a new product decision.
4. **No manufactured granularity:** where only document-level provenance exists, the row is synthetic
   with no fabricated row reference and the classification stays partial.
5. **Sequencing [REC]:** the extraction fix should precede factor-coverage expansion, because until
   per-line extraction exists the matcher never receives the per-line `(activity, unit)` pairs the
   catalogue was designed for.

**Any code change requires separate authorisation.** No change was made here.

## 21. Explicit non-goals

No schema/migration change; no API/frontend change; no extraction/OCR/AI-prompt change; no calculation
change; no factor data change; no RLS/auth/billing change; no legacy-report change; no Phase 8-X change;
no historical re-extraction; no `evidence_line_items`; no `source_line_item_id`; no production change;
no commit; no push; no implementation prompt.

## 22. Limitations

- No live database session was available; factor-side and persisted-data statements remain repository
  facts, not live-DB verification. **[U]**
- The extraction-path attribution of the *specific* observed document was established by reproducing the
  deterministic `suggest()` behaviour on equivalent content, not by re-running the original item. **[I]**
- The original main forensic report (§1–15) is not in the repository; this document consolidates the
  surviving §§16–22 evidence plus repository code inspection.
- No code was executed for this formalization; no test was run.

## 23. Verdict

**`LINE-ITEM TRACEABILITY FORENSIC — FORMALIZED (READ-ONLY, NO IMPLEMENTATION)`**

Root cause established and preserved: **Primary = A (extraction); consequences = E/F; subsidiary = D;
excluded = B, C.** Remediation is assigned to batch **P1**, separately authorised, and **not performed**.



