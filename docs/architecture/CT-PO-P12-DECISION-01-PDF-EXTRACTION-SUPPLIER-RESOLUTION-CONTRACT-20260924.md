# CT-PO-P12-DECISION-01 — PDF Extraction, Waste Semantics, Supplier Resolution and Propagation Product Contract

**1. Task Identity**

```text
P12-DECISION-01-20260924-PDF-EXTRACTION-SUPPLIER-RESOLUTION-CONTRACT
```

| Item | Value |
| --- | --- |
| Date | 2026-09-24 |
| Repository | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| Type | **RESEARCH / DESIGN / DECISION — implementation NOT performed** |
| Inputs | P12-DOC-03 (corpus), P12-GAP-02 (measured acceptance), current repository code |
| Output | this contract |

---

**2. Scope**

This task converts the *measured* failures of P12-GAP-02 into an implementation-ready
product contract across four areas:

* **AREA A** — PDF extraction contract (§12, §13)
* **AREA B** — waste activity semantics / factor resolution (§15)
* **AREA C** — supplier resolution and reuse (§16–§20)
* **AREA D** — supplier propagation through calculation / emissions / reporting (§21)

It explicitly does **not** implement, promote, fix, regenerate or expand anything (§30).

---

**3. Safety / Environment**

| Rule | Status |
| --- | --- |
| Product / backend / frontend source modified | **NO** |
| Migrations / schema / RLS / configuration / `.env` modified | **NO** |
| P1 promoted / P1 env vars / allowlist changed | **NO** |
| Production contacted | **NO** |
| `carbontally_test`, `carbontally_qa_phase8`, flagship `postgres` modified | **NO** |
| Suppliers created / extracted data repaired / canonical docs mapped or calculated | **NO** |
| Additional canonical PDFs created / larger corpus generated | **NO** |
| P12-DOC-03 oracle or canonical PDF files altered | **NO** |
| Database writes performed in this task | **NONE** (read-only metadata/queries only) |
| Permitted actions used | repository reads, read-only SQL, code inspection |

Evidence for the final "no product change" assertion is in §30.

---

**4. Evidence Sources**

| # | Source | Used for |
| --- | --- | --- |
| 1 | `docs/architecture/CT-PO-P12-GAP-02-CANONICAL-PDF-SUPPLIER-REUSE-20260924.md` | measured acceptance results (priority 1) |
| 2 | `docs/architecture/CT-PO-P12-DOC-03-CANONICAL-SYNTHETIC-PDF-CORPUS-20260924.md` + `tools/demo_lab/p12_canonical_manifest.json` | corpus + oracle |
| 3 | `docs/architecture/CT-PO-P12-DEMO-JOURNEY-AUDIT-20260924.md` | CSV lane PASS, PDF lane PARTIAL, EV-01 chain |
| 4 | `docs/architecture/CT-PO-P12-STEP2-FINAL-VERIFICATION-20260924.md` | Step-2 gate state, repeatability, disposable integration |
| 5 | `backend/services/automatic_extraction.py` | extraction entry points, schema, completeness |
| 6 | `backend/services/extraction_suggestions.py` | field suggestion vocabulary + unresolved mechanism |
| 7 | `backend/engines/extraction.py` | generic/named field patterns, table extraction |
| 8 | `backend/services/extraction_fidelity.py` | P1 classifier, coverage, shadow/enabled |
| 9 | `backend/services/automatic_processing.py` | pipeline, blocking reasons, clarification entries |
| 10 | `backend/engines/activity_clarification.py`, `backend/engines/factor_selection_policy.py` | waste ambiguity policy (D-FS-4) |
| 11 | `backend/data/suppliers.py`, `backend/api/v3_suppliers.py` | supplier model, CRUD, org-scoped search |
| 12 | `backend/data/emissions_logs.py` | emission write path + supplier read path |
| 13 | `backend/data/reporting.py`, `backend/domain/insight_query.py` | supplier-aware reporting / Insight |
| 14 | `backend/data/evidence_line_items.py`, `backend/domain/line_items.py` | evidence materialisation |
| 15 | P12-GAP-02 live database observations | persisted payloads, item/queue state |

**Evidence markers used throughout:** `VERIFIED` (inspected in the current repository or
measured in GAP-02), `INFERRED`, `NOT VERIFIED`, `DECISION REQUIRED`,
`IMPLEMENTATION REQUIRED`.

---

**5. Executive Summary**

**VERIFIED FACT.** GAP-02's results are explained by the current code, not by a broken
environment:

1. The PDF extraction path is **field-only**. `backend/services/automatic_extraction.py::_extract_pdf`
   calls `suggest_text(...)` and never asks for tables; `backend/services/extraction_suggestions.py::suggest`
   copies fields through `_FIELD_ALIASES`, and `backend/engines/extraction.py::suggest_fields`
   returns only `_extract_fields(text)` results. A PDF therefore **cannot** produce
   `line_items[]` in the primary path — independently of P1.
2. **Supplier** is missed because `engines/extraction.py:51` requires a literal
   `Supplier:` label (`^\s*supplier\s*[:：]\s*(.+?)$`), while the canonical invoices print
   the supplier **unlabelled** as the first line.
3. **Customer** can never be extracted: there is **no** `customer`/`buyer`/`client`/`vendor`
   pattern and **no** matching entry in `_FIELD_ALIASES` — even though the generic
   `Key: value` pass *does* capture `Buyer: Sustainable Direct Group` into the intermediate
   `fields` dict, where it is then discarded.
4. **Completeness 0.33** is arithmetic, not a mystery: `_REQUIRED = ("activity","quantity","unit")`
   and only `activity` resolved → 1/3.
5. P1 `shadow` emits **no structure**; the un-promoted `enabled` probe emits structure with
   measured defects (units read as `GBP`, one wrong quantity, false-positive rows from
   `Net Amount`/`GST`/VRM) and **still** no supplier/customer — P1 shapes *lines* only and
   never addresses the header vocabulary gap.
6. **Supplier resolution is absent**, but its primitives already exist and are
   tenant-scoped: `suppliers` is org-scoped, `backend/data/suppliers.py::search_for_org`
   exists, and `GET /api/v3/suppliers` already exposes an org-scoped search guarded by
   `ensure_org_access`.
7. **Supplier propagation is a writer defect, not a schema defect**: `emissions_logs.supplier_id`
   already exists and is already **read** by aggregation (`backend/data/emissions_logs.py`
   lines 73, 161–167, 378–387) and referenced by reporting (`backend/data/reporting.py:394`),
   but the INSERT at `backend/data/emissions_logs.py:258` does **not** write it.

**Therefore the next engineering phase is well-defined and modest in data-model terms:**

* extend the *extraction vocabulary* (labelled + positional header fields, a period parser);
* add a *line-item contract* able to exclude total/VRM/footer rows;
* keep the *waste clarification* (a PO-ratified policy, `D-FS-4`) and feed it better data;
* add a *supplier resolution service* on top of the existing org-scoped search;
* **wire `supplier_id` into the existing emission INSERT** and let existing reporting/Insight
  read paths light up.

No new table is proven necessary. Three PO decisions gate the automatic behaviour (§26).

---

**6. Current Extraction Architecture**

**VERIFIED (module/function level).**

| Layer | Location | Behaviour |
| --- | --- | --- |
| Public entry | `backend/services/automatic_extraction.py::extract_document(content, filename, mime, *, organization_id)` | classifies by extension/mime; dispatches PDF/IMAGE/SPREADSHEET; never raises (`status: error` / `unsupported`) |
| PDF path | `...::_extract_pdf(content, *, organization_id)` (line 465) | `_pdf_text()` → `method`, `page_count`; `<20` chars ⇒ `status: no_text`; else `suggest_text(text[:200_000])` → `extracted_data` + `unresolved`; then `_apply_p1_fidelity(...)`; returns `{status, method, page_count, extracted_data, unresolved, confidence[, coverage]}` |
| Field vocabulary | `backend/services/extraction_suggestions.py::suggest(text)` | `_ENGINE.suggest_fields(text)` → copy via `_FIELD_ALIASES` → activity via `_ACTIVITY_KEYWORDS` → quantity/unit via `_suggest_quantity_unit`; missing keys appended to `unresolved` |
| Deterministic engine | `backend/engines/extraction.py::DocumentExtractionEngine` | `_KEY_VALUE_RE` generic `Key: value` (line 45) **plus** `_DEFAULT_FIELD_PATTERNS` (**5 keys only**: `supplier`, `invoice_number`, `date`, `net_amount`, `gross_amount`, line 50); `_extract_tables` needs an injected `table_delimiter` and ≥2 rows |
| Required fields | `automatic_extraction._REQUIRED = ("activity","quantity","unit")` (line 44) | denominator for `_completeness()` (line 325) |
| Confidence | `_completeness(extracted)` | `len(resolved ∩ _REQUIRED) / len(_REQUIRED)` — canonical PDFs = **1/3 = 0.33** |
| P1 shaping | `backend/services/extraction_fidelity.py` + `automatic_extraction._apply_p1_fidelity` | mode from `CARBONTALLY_P1_EXTRACTION_SHAPE` (default `shadow`); `enabled` only for orgs in `CARBONTALLY_P1_ORGANIZATION_ALLOWLIST` (absent ⇒ fail-safe `shadow`) |
| Pipeline | `backend/services/automatic_processing.py` | durable job; extraction → validation/mapping; persists `validation_result`, `stage`, `manual_review_reason`; clarification entries via `_clarification_entry` (line 218) |
| Persistence | `document_processing_queue` (`status`, `stage`, `extracted_data`, `automation_extracted_data`, `manual_review_reason`, `validation_result`, `pipeline_version`); `manual_extraction_items` (`status`, `extracted_data`, `mapped_data`, `mapped_supplier_id`, `emission_factor_used`) | GAP-02 observed `{activity,date,invoice_number}` etc. on items and empty `extracted_data` on 5/6 queue rows |
| Downstream consumers | items → mapping (`mapped_facility_id`, `mapped_asset_id`, `mapped_supplier_id`, `emission_factor_used`) → calculation → `calculation_snapshots` → `emissions_logs` → `evidence_line_items` → reporting / Insight | `line_items[]` has **no consumer** because it is never produced |

**VERIFIED — the primary PDF path has no table/line concept at all.**
`suggest_fields()` returns `{f.field_name: f.value for f in self._extract_fields(text)}` —
a dict of scalar fields. `_extract_tables` is never invoked from the PDF suggestion path.
`line_items[]` absence in GAP-02 is therefore **structural**, not a P1 setting.

---

**7. GAP-02 Findings Reconciled Against Code**

| GAP-02 measurement | Code-level explanation | Status |
| --- | --- | --- |
| PDF upload 6/6 PASS | `POST /api/v3/uploads` → durable job (GAP-02 evidence) | VERIFIED |
| Extraction executed 6/6 (`ok`, `pdf_text`) | `_extract_pdf` ran; text present | VERIFIED |
| `supplier` 0/6 | supplier pattern requires a literal `Supplier:` label (`engines/extraction.py:51`); corpus prints it unlabelled | VERIFIED |
| `customer` 0/6 | no customer/buyer pattern exists and no `_FIELD_ALIASES` entry for `buyer` even though generic `Key: value` captures it | VERIFIED |
| `line_items[]` 0/6 | primary path is field-only (`suggest_fields` → `_extract_fields`); tables never requested | VERIFIED |
| completeness 0.33 (5/6) | `_REQUIRED` = activity/quantity/unit; only `activity` resolved → 1/3; threshold 0.50 | VERIFIED |
| `activity` = "Waste" 6/6 | `_ACTIVITY_KEYWORDS` contains `("Waste", r"\bwaste\b")` | VERIFIED |
| `invoice_number` 4/6 | named pattern requires an `Invoice`-labelled line; layout variants differ | VERIFIED |
| `date` 4/6 (one non-ISO) | named `date` pattern returns raw text, no date normalisation | VERIFIED |
| `net_amount` on 2/6 as a document total | named `net_amount` pattern; value is the document net total, not a line | VERIFIED |
| mapping 0/6 (`Waste` clarification) | activity-clarification policy `D-FS-4` (`engines/factor_selection_policy.py`, `engines/activity_clarification.py`) — by design | VERIFIED |
| calculation/evidence/reporting 0/6 | dependency chain from absent lines | VERIFIED |
| PE ops route 403 | items created `processing_entity_id NULL`, `processing_origin CARBONTALLY_INTERNAL`; PE isolation | VERIFIED |
| `emissions_logs.supplier_id` never populated | INSERT column list at `backend/data/emissions_logs.py:258` omits `supplier_id` | VERIFIED |
| no supplier match/reuse routine | no supplier resolution service anywhere; only `search_for_org` (search) + CRUD | VERIFIED |
| P1 `enabled` defects (units `GBP`, wrong qty, false positives) | P1 line shaper heuristics; not exercised in the primary path | VERIFIED (as measured in GAP-02) |
| `page_count = 2` for 1-page docs | not investigated in this design task | **NOT VERIFIED** |

---

**8. Supplier Header Extraction Analysis**

**VERIFIED root cause.**

```text
Current implementation : backend/engines/extraction.py:51
                         "supplier": re.compile(r"(?im)^\s*supplier\s*[:：]\s*(.+?)\s*$")
Observed behaviour     : the canonical invoices print the supplier as the FIRST LINE with no
                         label ("Robinsons Recycling Services Ltd"), so no match occurs; the
                         extractor's own unresolved list names "supplier" (GAP-02).
Required future change : a supplier-header strategy that does not depend on the word
                         "Supplier" appearing, with an explicit unresolved fallback when
                         confidence is low. Never fabricate a supplier.
Acceptance             : 6/6 canonical PDFs populate extracted_data.supplier == the oracle
                         value ("Robinsons Recycling Services Ltd").
```

**Parser characteristics (VERIFIED):**

| Question (§7) | Answer |
| --- | --- |
| Fixed labels? | Yes — `_DEFAULT_FIELD_PATTERNS` is label-driven (`Supplier:`, `Invoice…:`, `Date:`, `Net…:`, `Gross…:`) |
| Positional rules? | **None** for fields; positions are used only for table rows via `table_delimiter` |
| Known labels for supplier/customer? | `supplier` only; **no customer/buyer/client/vendor** |
| First-line heuristic? | No |
| Document-header parser? | No — headers are treated as ordinary lines |
| OCR/text abstraction? | Yes — `_pdf_text(content)` → `(text, method, page_count)`; method observed `pdf_text` |
| AI extraction? | Exists elsewhere (`backend/engines/ai_extraction.py`, the AI branch/columns on the queue) but **is not** what produced GAP-02's payloads |
| Fallback extraction? | `status: no_text` path, plus `unsupported` for unknown types |

**SUPPLIER EXTRACTION vs SUPPLIER RESOLUTION (must stay separate).**

* **Extraction** — "which supplier name is printed here?" → `extracted_data.supplier`, a
  *string* suggestion, in the extraction layer. **IMPLEMENTATION REQUIRED** (§12).
* **Resolution** — "which CarbonTally supplier entity *is* that name?" → a supplier *id*,
  in a new resolution service. **IMPLEMENTATION REQUIRED + DECISION REQUIRED** (§17–§19).

The canonical corpus does not exist as a supplier entity, and GAP-02 forbade creating one,
so resolution must also cover the "no candidate" branch (§19).

---

**9. Customer Header Extraction Analysis**

**VERIFIED.** Two independent blockers, either alone sufficient for 0/6:

1. `_DEFAULT_FIELD_PATTERNS` has **no** customer/buyer/client pattern.
2. `_FIELD_ALIASES` has **no** `customer`/`buyer`/`client`/`vendor` key, so even the generic
   `Key: value` pass result for the canonical line `Buyer: Sustainable Direct Group` is
   **discarded** at the copy step.

**Tenant separation must be preserved.** GAP-02 uploaded the corpus into **`Demo Lab
Organisation A`** while the printed buyer is **`Sustainable Direct Group`**. Printed
customer = **document content**; the CarbonTally tenant = an **authorisation scope**. The
contract therefore requires:

* `extracted_data.customer` = the string printed on the document;
* **never** an implicit claim that this string *is* the tenant/organization;
* any future customer↔organization linkage is a **separate** decision and is **not** designed
  here — **DECISION REQUIRED before any such linkage is built**.

---

**10. Line-Item Extraction Analysis**

**VERIFIED root cause.** The primary PDF path never requests rows:

* `suggest_fields()` → `_extract_fields()` only (scalar fields);
* `_extract_tables()` exists (`backend/engines/extraction.py:204`) but depends on
  `self._table_delimiter` being present and requires ≥2 rows; the PDF suggestion path never
  calls it. Whether `extract()` (non-suggestion path) injects that delimiter is **NOT
  VERIFIED** and is not on the current PDF path;
* P1 is the only component that *emits* `line_items[]`, and it is gated (§11).

**What GAP-02 measured about the un-promoted P1 lines (VERIFIED):**

| document | oracle lines | P1 enabled lines | quantity | unit | false positives |
| --- | --- | --- | --- | --- | --- |
| `…001` | 3 | 3 | exact | `tonne` OK | none |
| `…002` | 4 | 4 | exact | **`GBP` ×2** | none |
| `…003` | 5 | 6 | 5 exact | `tonne` | `"Net Amount: £"` (11,628.76) |
| `…004` | 2 | 3 | **wrong (5.0/43.0 vs 4.6/42.8)** | `tonne` | `MH82 KM` (2.0, unit `km`) |
| `…005` | 3 | 4 | exact | **`GBP` ×3** | `"GST: £"` (1,789.93) |
| `…006` | 4 | 4 | exact | `tonne` | none |

P1's *structural* capability is real; its *classification* of unit columns and of
total/footer rows is not yet trustworthy.

---

**11. P1 Shadow / Enabled Analysis**

**VERIFIED (GAP-02 + code).**

| Aspect | Finding |
| --- | --- |
| Mode resolution | `extraction_fidelity.shape_mode(organization_id=…)`; default `shadow`; `enabled` requires the org to be inside `CARBONTALLY_P1_ORGANIZATION_ALLOWLIST`; missing/invalid allowlist ⇒ fail-safe `shadow` |
| Demo Lab configuration | no `CARBONTALLY_P1_*` variables present; resolver returned `shadow`, `allowlist_size 0`, `in_rollout false` |
| Shadow output | coverage block only (`multi_line_suspect`, `candidate_lines`, `text_chars`, `clipped`, `mode`, `ai_fanout`) attached in-process and logged; `extracted` unchanged |
| Persisted shadow structure | **none** — no coverage and no `line_items` in `document_processing_queue.extracted_data`, `automation_extracted_data`, or `manual_extraction_items.extracted_data` |
| Shadow measurement accuracy | high — `candidate_lines` 3,4,6,3,4,4 vs oracle 3,4,5,2,3,4 (extras are total/footer/VRM lines) |
| `enabled` structure | `line_items[]` emitted 6/6 with the §10 defects; supplier/customer still absent |
| Production consumers | none — a structure that is not emitted cannot be consumed |

**Contract position:** `P1 STRUCTURAL CAPABILITY` = present (shape exists; gating is
governance). `P1 PRODUCTION READINESS` = **NOT established**. Promotion is
**DECISION REQUIRED**, gated by §14 — never by "`line_items[]` exists".

---

**12. Proposed PDF Extraction Contract**

**PROPOSED DESIGN** (nothing here is implemented). The contract extends the *existing*
`extracted_data` vocabulary — it does not invent a parallel schema.

### A. Document-level fields

| Field | Existing? | DB representation | API representation | New contract needed? | Implementation location |
| --- | --- | --- | --- | --- | --- |
| `supplier` | key exists in `_FIELD_ALIASES` + pattern; **not populated** for this corpus | `manual_extraction_items.extracted_data` (JSONB) | item/queue payloads | extend the *strategy* (unlabelled header), not the key | `backend/engines/extraction.py` (`_DEFAULT_FIELD_PATTERNS`) + `backend/services/extraction_suggestions.py` (`suggest`) |
| `customer` | **no key, no pattern** | same JSONB | same | **yes — new key + pattern + alias** | same two files |
| `invoice_number` | yes (pattern + alias) | JSONB | same | no — verify 6/6 | same |
| `invoice_date` / `date` | yes (`date`) | JSONB | same | no — add ISO normalisation + a raw-value warning | `extraction_suggestions.py` |
| `billing_period_start` / `billing_period_end` | **no** | JSONB (no dedicated column) | same | **yes — new keys** parsed from a labelled period range | `extraction_suggestions.py` |
| `currency` | alias exists (`currency`, `billing_currency`) | JSONB | same | no — populate when printed | same |
| `net_amount` (document subtotal) | yes | JSONB | same | no | same |
| `vat_amount` (document tax) | **no key** | JSONB | same | **yes** — the corpus prints `VAT (20%)`/`GST`; note the label varies | same |
| `gross_amount` (document total) | yes | JSONB | same | no | same |

### B. Line-level fields (`line_items[]`)

| Field | Existing (in P1 output)? | New contract needed? | Notes |
| --- | --- | --- | --- |
| `description` | yes | improve (strip table-cell noise, keep the printed description) | P1 currently concatenates column fragments |
| `activity` / category | yes | keep | must remain the same vocabulary as `_ACTIVITY_KEYWORDS` |
| `quantity` | yes | improve accuracy | 1 document measurably wrong |
| `unit` | yes | **must be read from the table's unit/rate column region, never from a currency token** | `GBP` must never be emitted as a unit |
| `unit_price` / rate | **not present in P1 output** | **yes — new field** | oracle provides it; the printed table has a Rate column |
| `net_amount` (line) | **not present** | **yes — new field** | oracle provides per-line net |
| `page`, `line_number`, `extraction_method`, `source_line`, `page_basis`, `page_trust` | yes | keep (provenance) | already carries `det:pdf_text` stamps (`P1-D8`) |

### C. Extraction metadata

| Field | Existing? | Action |
| --- | --- | --- |
| `status`, `method`, `page_count`, `confidence`, `unresolved` | yes | keep; extend `unresolved` to enumerate header fields too |
| `warnings` | **no dedicated list** | **PROPOSED**: reuse `unresolved` + a `warnings[]` list for non-blocking observations (e.g. "currency token in unit column ignored") |
| `parser version` | yes — `pipeline_version` on the queue (`v3-auto-1.1`) | keep; bump on behaviour change |
| `source page` / `source_line` | yes (per line) | keep |
| raw text/region reference | `source_line` only | **NOT VERIFIED** that region data exists; do not invent one |

**Unit normalisation rule (PROPOSED, and deliberately conservative).**

* Accept a unit only from the document's own unit column/region or from the explicit
  `_KNOWN_UNITS` vocabulary.
* Map the *same* meaning to one canonical token via the existing central normalisation
  (e.g. `tonne`/`tonnes`/`t`/`ton` → the platform's canonical mass unit) — **if** that
  central normaliser exists; otherwise this must be a single new helper, not per-module logic.
* **Never** convert a currency token (`GBP`) into a unit because the oracle expects
  `tonnes`. A wrong token must surface as `unresolved`, not be repaired silently.
* `…002`/`…005` in GAP-02 must therefore fail the acceptance test until the unit column is
  correctly identified — that is the intended behaviour of this contract.

---

**13. Proposed Line-Item Contract**

**PROPOSED DESIGN.** A row qualifies as a **line item** only if all of the following hold:

1. it belongs to the document's **item table region** (the block whose header row contains at
   least *two* of: description-like, quantity-like, unit-like, rate-like, amount-like column
   labels), **and**
2. it has a **non-empty textual description** that is not a total/footer/payment label, **and**
3. it carries a **numeric quantity** in the quantity column region, **and**
4. it carries a **unit token that is in the unit vocabulary** (or the unit column is empty and
   the unit is derivable from the description), **and**
5. it is **not** any of: a subtotal/net line, a VAT/GST/tax line, a total/gross line, a
   payment/bank line, a carriage/registration (VRM) or page footer/header line.

**Explicit exclusions (enforced from GAP-02's measured false positives):**

| Excluded pattern | Example from GAP-02 | Rule |
| --- | --- | --- |
| document net/subtotal | `"Net Amount: £"` → 11,628.76 | label-based exclusion + value-equals-document-total exclusion |
| tax totals with varying labels | `"GST: £"` → 1,789.93; `VAT (20%)` | label vocabulary must include `VAT`, `GST`, `tax` |
| grand totals | `Total: £33,209.37` | label-based exclusion |
| vehicle/registration text | `MH82 2KM` (unit `km`) | unit/number adjacency outside the table region must be rejected |
| payment/bank/footer blocks | not observed in GAP-02, but generator invoices emit payment info | region exclusion |

**Field-derivation rules:**

| Field | Rule |
| --- | --- |
| description | description column text, whitespace-collapsed; strip currency symbols and stray single-letter column fragments |
| quantity | numeric value in the quantity column region (same row) |
| unit | unit token from the unit column region; if absent, accept only from `_KNOWN_UNITS` inside the description |
| rate | numeric value in the rate/unit-price column region |
| line net | numeric value in the amount column region; must satisfy `rate × quantity ≈ net` within a documented tolerance, else flag the row |
| document totals | taken from the labelled footer fields (`net_amount`, `vat_amount`, `gross_amount`), **never** from a row |

**No silent normalisation.** A row whose unit cannot be trusted is emitted with the raw token
**and** flagged, or omitted with a warning — never rewritten to match the oracle.

---

**14. Proposed P1 Promotion Gates**

**PROPOSED DESIGN — promotion is a PO decision, not an engineering side-effect.** P1 may be
promoted to `enabled` for a Demo Lab organisation only when **all** of the following are
measured on the six canonical PDFs, using `tools/demo_lab/p12_canonical_manifest.json` as the
only oracle:

| Gate | Threshold |
| --- | --- |
| Line-item structural coverage | 6/6 documents emit `line_items[]` |
| Line count | exact per document (3,4,2,5,3,4 = 21 lines) |
| Quantity accuracy | 21/21 exact |
| Unit accuracy | 21/21 canonical-equivalent (`tonnes`/`tonne` acceptable only if the platform canonicalises them) |
| Rate accuracy | 21/21 exact |
| Line net accuracy | 21/21 exact |
| False-positive rate | **0** rows attributable to subtotal/VAT/GST/total/VRM/footer |
| Document totals | 6/6 net, 6/6 tax, 6/6 gross exact **where extracted** |
| Header fields | 6/6 supplier **and** 6/6 customer populated (P1 alone cannot achieve this) |
| Consistency | no document regresses another (no per-document special-casing) |
| Regression coverage | CSV/EV-01 path unchanged; existing P1 unit tests green |

`P1 structural capability` ≠ `P1 production readiness`. `shadow` remains the default until
these gates are met and the PO records the promotion decision (`P1-D1` governs until then).

---

**15. Waste Activity Semantics Analysis**

**VERIFIED.** The `Waste` clarification is **policy, not a bug**:

| Element | Location | Detail |
| --- | --- | --- |
| Ambiguity policy | `backend/engines/factor_selection_policy.py` | `_NON_FUEL_FAMILIES = ("waste disposal","material use")`; `_WASTE_FUEL_REQUEST = ("waste oil","waste-oil","waste oils")`; `_request_class()` → `waste_fuel` vs `waste_treatment`; explicit comment **"the shared token 'waste' is not evidence"** (`D-FS-4`) |
| Waste vocabulary | same file (~line 39) | `disposal`, `treatment`, `landfill`, `recycl`, `compost`, `incinerat`, … |
| Clarification engine | `backend/engines/activity_clarification.py` | `assess_activity_evidence()` → `verdict ∈ {sufficient, clarification_required, insufficient_evidence, not_required, no_candidates, policy_ambiguous}`; families classed **treatment** vs **combustion**; `options` carry `id`, `label`, `semantic_term`, `scopes` |
| Persistence | `backend/services/automatic_processing.py::_clarification_entry` (line 218) | persists `clarification_required`, `clarification_verdict`, `clarification_families`, `clarification_options` |
| Operator surface | `POST /api/v3/ops/entities/{entity}/extraction/items/{item}/clarify` (+ `.../mapping-options`) | already exists |

**A resolution surface already exists; what is missing is the evidence that would let the
verdict be `sufficient` automatically.**

**PROPOSED CONTRACT.** Ask only for the minimum disambiguating information the documents and
factor set already carry, and only where the policy already distinguishes families:

| Dimension | Supported today? | Source |
| --- | --- | --- |
| treatment/material family vs fuel/combustion family | **yes** — the policy's own vocabulary | `factor_selection_policy` |
| waste stream / material (general, mixed, organic, hazardous…) | **partly** — printed inside the line description (e.g. `Recycling services - Mixed`) | `line_items[].description` |
| route (recycled / composted / landfill / incinerated) | **yes**, as vocabulary | `factor_selection_policy` |
| "waste oil" as fuel | **yes** — explicit `_WASTE_FUEL_REQUEST` | same |

Contract rules:

1. If the line's description/route vocabulary resolves to **exactly one** family → may
   auto-match (**SAFE AUTO-MATCH**), subject to PO approval of this rule.
2. If it maps to **more than one materially different family** → **CLARIFICATION REQUIRED**
   using the existing `options` payload (never silently choose).
3. If it maps to **none** → **CLARIFICATION REQUIRED** with a bounded reason (current
   behaviour).
4. **Do not** remove the guard: `Waste` alone stays insufficient.
5. Do **not** invent a new waste taxonomy; extend only the description-derived vocabulary if a
   PO decision says to.

PO decision: **P12-D1**.

---

**16. Supplier Data Model Analysis**

**VERIFIED — `public.suppliers` is org-scoped and already rich enough for matching:**

| Attribute | Column | Use as a matching signal | Availability |
| --- | --- | --- | --- |
| organisation scope | `organization_id` | **mandatory filter** | **existing** |
| name | `name` | primary signal (normalised) | **existing** |
| address | `address_line1`, `address_line2`, `city`, `county`, `postcode`, `country`, `eircode` | secondary signal (postcode especially) | **existing** |
| identifiers | `vat_number`, `company_number`, `tax_id`, `registration_number`, `tax_region`, `registration_region` | strong signal when present | **existing** (not currently extracted from PDFs — see below) |
| contact | `contact_name`, `contact_email`, `primary_email`, `primary_phone`, `contact_phone` | weak signal (email domain) | **existing** |
| type/category | `type`, `supplier_type`, `supplier_category_id` | filter | **existing** |
| lifecycle | `is_active`, `risk_score`, `compliance_status`, `contract_start/end` | filter/ranking | **existing** |
| free-form | `metadata` (JSONB) | future extraction provenance | **existing** |

**VERIFIED supporting surfaces:**

| Surface | Location | Note |
| --- | --- | --- |
| Supplier repository | `backend/data/suppliers.py` | `create`, `get`, `list_for_org`, **`search_for_org(org_id, search=, category_id=, status=, limit, offset)`**, `update`, `remove`, `save`, `delete` — all org-scoped |
| Supplier API | `backend/api/v3_suppliers.py` | `GET /api/v3/suppliers?organization_id=&search=` (`require_org_member()` + `ensure_org_access`), `POST` (**`require_org_admin()`**), `GET/PUT/DELETE /{supplier_id}` |
| Extraction-side supplier field | `manual_extraction_items.mapped_supplier_id` | the **only** persisted link from a document item to a supplier |
| Queue-side supplier field | `document_processing_queue.ai_mapped_supplier_id` | exists, populated 0/11 in GAP-02 |
| Emission-side supplier field | `emissions_logs.supplier_id` | exists, nullable, **read** by aggregation, **not written** by the INSERT |

**No new table is required for supplier resolution.** The missing pieces are a
**normaliser**, a **scorer**, and a **resolution service** that uses the existing
`search_for_org` — plus a PO policy on when it may act automatically.

**Signals NOT currently available (must not be invented as if present):**

| Signal | Status |
| --- | --- |
| VAT/company number extracted from the invoice | **requires extraction work** (§12) — currently no pattern |
| Historical association (item↔supplier history) | **requires new query** (data exists via `mapped_supplier_id`) |
| Supplier reference on the invoice | **NOT VERIFIED** as present in the corpus or the parser |

---

**17. Supplier Resolution Contract**

**PROPOSED DESIGN.** Seven steps, each with an explicit owner and outcome. Steps 1–4 are
automatic and safe; steps 5–6 are gated by PO decisions (§26).

| Step | Purpose | Input | Output | Where | Gate |
| --- | --- | --- | --- | --- | --- |
| **1 EXTRACT** | read the printed supplier | PDF text | `extracted_data.supplier` (string) | extraction layer (`extraction_suggestions.py`) | none |
| **2 NORMALIZE** | make comparison deterministic | supplier string + parsed address/id tokens | `normalized_name`, `postcode`, `vat`, `company_no` | **new** helper (single module) | none |
| **3 FIND CANDIDATES** | search the **same organisation only** | normalised tokens | ranked candidate list (0..n) | existing `repos.suppliers.search_for_org(org_id, search=…)` | none |
| **4 SCORE / DECIDE** | deterministic classification | candidates + tokens | `exact` \| `strong` \| `probable` \| `ambiguous` \| `none` | **new** pure scoring function | none |
| **5 CONFIRM** | human decision where required | verdict + candidates | operator choice id | existing operator/workbench surface | **P12-D2 / P12-D4** |
| **6 CREATE** | new supplier when none matches | extracted identity | new supplier row | existing `POST /api/v3/suppliers` (admin-gated) | **P12-D3** |
| **7 PERSIST** | record the link | supplier id | `manual_extraction_items.mapped_supplier_id` | item update path | P12-D2 |

**Hard rules (PROPOSED, non-negotiable):**

* Steps must remain **organization-scoped**; a cross-tenant candidate is never returned and
  never selected (existing `search_for_org` + RLS enforce this; the service must not add any
  unscoped query).
* **Never** silently choose between multiple plausible candidates.
* **Never** silently create a duplicate supplier.
* If the name cannot be extracted → **no resolution is attempted**; the document stays in
  manual review (extraction-blocked), exactly as today.
* Resolution is recorded as **provenance** (which strategy matched, and to what) so an auditor
  can answer "why is this document attributed to this supplier?".

---

**18. Supplier Matching Strategy**

**PROPOSED DESIGN — deterministic, explainable, no black box.** Signals are used in priority
order, each classified by what it needs:

| Priority | Signal | Comparison | Classification | Weight |
| --- | --- | --- | --- | --- |
| 1 | VAT number / company number | exact, normalised | **currently available** (columns exist; extraction required to populate) | decisive when both sides present |
| 2 | postcode | exact, normalised (upper, no spaces) | **currently available** (extraction required) | strong |
| 3 | normalised legal name | exact equality after normalisation | **currently available** | strong |
| 4 | normalised name similarity | token-set similarity above threshold | **currently available** | moderate |
| 5 | address line 1 + city | exact/normalised | **currently available** | moderate |
| 6 | contact email domain | exact | **currently available** | weak |
| 7 | prior item↔supplier association for this organisation | history lookup on `mapped_supplier_id` | **requires new query** (no schema change) | tie-breaker only |

**Normalisation** (single helper, PROPOSED): trim/whitespace-collapse → casefold → normalise
`&`→`and`, strip `.`/`,` → collapse legal-suffix variants (`ltd`/`limited`, `plc`) **for
comparison only**; the stored name is never rewritten.

**Decision thresholds (PROPOSED):**

| Verdict | Condition | Automatic action permitted? |
| --- | --- | --- |
| `exact` | identifier match, or normalised name equality **and** (postcode or address agreement) | PO decision (**P12-D2**) |
| `strong` | normalised name equality with no address evidence | confirmation recommended |
| `probable` | similarity ≥ threshold and one candidate clearly ahead | confirmation required |
| `ambiguous` | two or more candidates within a small score margin | **confirmation required** (**P12-D4**) |
| `none` | no candidate above floor | creation branch (**P12-D3**) |

**Explicitly organisation-scoped:** Organization A's `Robinsons Recycling Services Ltd` can
never match Organization B's identically named supplier. This is a security acceptance item
(§25 J).

---

**19. Supplier Creation Strategy**

**VERIFIED**: the only creation route is `POST /api/v3/suppliers`, guarded by
`require_org_admin()`. A background pipeline acting automatically would therefore either
(a) use an elevated path with its own explicit authorisation, or (b) surface a "create
supplier?" confirmation to an operator/admin.

**PROPOSED behaviour:**

| Situation | Proposed behaviour | Gate |
| --- | --- | --- |
| `none` verdict **and** PO approves automatic creation | create **once**, storing extracted name/address plus `metadata` provenance (`source: pdf_extraction`, document id, extraction run) | **P12-D3** |
| `none` verdict and PO withholds automatic creation | mark item `supplier_unresolved` and offer "create supplier" in the existing operator surface | **P12-D3** |
| Idempotency | before creating, re-run steps 3/4 within the same serialised path so two documents from one supplier cannot create two rows | implementation requirement |
| Never | create from a low-confidence or ambiguous verdict | hard rule |

The canonical corpus has **no** matching supplier row today, so the *first* Robinsons
document necessarily exercises the creation/confirmation branch — exactly the scenario the
demo must show.

---

**20. Multi-Year Supplier Reuse Contract**

**PROPOSED DESIGN.**

```text
FY2025  Robinsons Recycling Services Ltd  -> resolve -> Supplier ID X   (create or match)
FY2026  Robinsons Recycling Services Ltd  -> resolve -> Supplier ID X   (must reuse)
```

| Requirement | Mechanism |
| --- | --- |
| Same supplier id across years | resolution runs the same normalisation + scoring; the FY2025 row is an ordinary candidate for FY2026 |
| Prevent duplicate creation | mandatory pre-create candidate re-check; creation only from a `none` verdict |
| Prevent cross-tenant matching | resolution is called with the job's `organization_id` only; existing `search_for_org` is org-scoped; no global query permitted |
| Prevent accidental reassignment | once `mapped_supplier_id` is set, later resolution may **not** overwrite it without an explicit operator action |
| Prevent name-only collisions | name equality alone is `strong`, never `exact`; a second plausible candidate forces `ambiguous` → confirmation |

**Variant handling (PROPOSED — never decided silently):**

| Variant | Behaviour |
| --- | --- |
| `…Ltd` vs `…Limited` | normalisation treats them as equal → `strong`/`exact` per P12-D2; the stored name is unchanged |
| changed address, same name | name matches, address differs → `probable`/`ambiguous` → confirmation required |
| different identifier, same name | identifier conflict → **must not** auto-match; flag for operator review |

**Explicitly NOT decided here:** whether name-equality cases may auto-associate (**P12-D2**),
whether a `none` verdict may auto-create (**P12-D3**), and what happens with two plausible
candidates (**P12-D4**).

---

**21. Supplier Propagation Contract**

**VERIFIED — the current data path and where it breaks:**

```text
PDF  ->  manual_extraction_items.extracted_data            (no supplier today)
     ->  manual_extraction_items.mapped_supplier_id        (NULL today; the only link)
     ->  mapping / calculation                             (no supplier read at all)
     ->  calculation_snapshots                             (NO supplier_id column exists)
     ->  emissions_logs                                    (supplier_id column EXISTS,
                                                            INSERT omits it — line 258)
     ->  evidence_line_items                               (source_item_id based)
     ->  reporting / Insight                               (reads supplier_id / mapped_supplier_id)
```

| Question (§15) | VERIFIED answer |
| --- | --- |
| Source of truth for supplier identity | `public.suppliers.id` (org-scoped) |
| When does `supplier_id` become authoritative? | when resolution persists it on the **item** (`mapped_supplier_id`) — the item is the natural anchor because it already carries `source_line_item_id`/evidence links |
| How is it copied/linked? | by **reading the item** at calculation time and passing it into the emission write; no duplication of identity |
| Does `calculation_snapshots` need a `supplier_id`? | **NOT REQUIRED** — snapshots already carry `source_item_id` and `source_line_item_id`, so supplier is derivable; adding a column is **POST-DEMO / FUTURE** (only if a query needs it without a join) |
| Should `emissions_logs` carry `supplier_id`? | **YES** — the column already exists, is already read by aggregation (`emissions_logs.py` 73/161-167/378-387) and joined to `public.suppliers`; the INSERT must be extended. **No schema change.** |
| How does reporting get supplier attribution? | `backend/data/reporting.py:394` already filters on `i.mapped_supplier_id IS NOT NULL`; with the item populated, existing reporting works |
| How does Insight get it? | `backend/domain/insight_query.py` already exposes `supplier_id` as a dimension and documents that the write path never populates it — populating `emissions_logs.supplier_id` unlocks it without touching the Insight query code |

**PROPOSED propagation rules:**

1. The **item** is the source of truth for "which supplier this document belongs to".
2. Calculation passes the item's `mapped_supplier_id` into
   `EmissionLogsRepository.create(...)`; the INSERT gains `supplier_id` (nullable, as today).
3. Rows with no resolved supplier keep `supplier_id = NULL` — and aggregation must continue
   to bucket them as `'none'` (already the behaviour, `COALESCE(l.supplier_id::text,'none')`).
4. **No snapshot column added.** If a future acceptance wants supplier directly on the
   snapshot, that is a separate migration proposal — **not** proposed here.
5. Supplier is **never** inferred at report time; it must have been persisted by the pipeline
   (no retro-attribution).

**Schema changes required by this contract: NONE** (verified against the actual columns).

---

**22. Evidence / Provenance Contract**

**VERIFIED existing machinery** (must be preserved, not redesigned):

| Element | Location |
| --- | --- |
| Evidence materialisation | `backend/data/evidence_line_items.py` (INSERT at line 88) |
| `materialisation_kind` vocabulary + audit event | `backend/domain/line_items.py` (`AUDIT_LINE_ITEMS_MATERIALISED = "report:evidence_line_items_materialised"`) |
| `source_page` rules | `backend/domain/evidence.py` |
| Snapshot→line link columns | `calculation_snapshots.source_item_id`, `.source_line_item_id` |
| Viewer endpoint | `GET /api/v3/evidence/line-items/{line_item_id}` (verified 200 for the CSV line in GAP-02) |

**Minimum provenance per extracted line (PROPOSED):**

| Requirement | Mechanism |
| --- | --- |
| line knows its source document | `evidence_line_items.source_file_id` |
| line knows its source item | `evidence_line_items.source_item_id` |
| line knows its position | `line_number`, `source_page`, `row_reference` |
| line's raw content is fixed | `raw_description`, `raw_quantity`, `raw_unit`, `payload_hash` |
| line's method is stamped | `extraction_method` (`det:pdf_text` / `csv` / `ai:*`) |
| calculation points back | `calculation_snapshots.source_line_item_id` → evidence line id |

**Contract:** a calculated PDF line **must** have a materialised evidence line; if the line
cannot be materialised (e.g. unit unresolved) it **must not** be calculated. The Viewer's
question — *"where did this emissions value come from?"* — must be answerable for every
PDF-derived number, exactly as it already is for CSV/EV-01. **No new evidence table or
column is required.**

---

**23. Review / Ambiguity States**

**VERIFIED existing vocabulary** (do not invent a parallel state machine):

| Existing state | Where | Meaning today |
| --- | --- | --- |
| queue `status = manual_review`, `stage = blocked` | `document_processing_queue` | pipeline stopped, human needed |
| `manual_review_reason` | same | bounded human-readable reason (e.g. "extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit"; "mapping could not auto-resolve: line 1: clarification required for 'Waste' …") |
| item `status = extracted` | `manual_extraction_items` | extraction present, awaiting mapping |
| `clarification_required`, `clarification_verdict`, `clarification_families`, `clarification_options` | mapping entry payload | activity/factor ambiguity with selectable options |
| `validation_result` | queue | validation payload |
| `attempt_count`, `max_attempts`, `workflow_error_count`, `workflow_next_retry_at`, `last_error`, `locked_at`, `lock_token`, `reprocess_count` | queue | durable job control |
| `pipeline_version` | queue | parser/pipeline generation stamp |

**PROPOSED mapping of required states onto existing contracts:**

| Required state (§17) | Represent using | New state needed? |
| --- | --- | --- |
| extracted successfully | item `status = extracted` with populated `extracted_data` | no |
| extraction incomplete | queue `manual_review_reason = "extraction completeness … unresolved: …"` | no |
| supplier unresolved | `unresolved` containing `supplier` + review reason | no new state (semantics unchanged) |
| customer unresolved | `unresolved` containing `customer` | no |
| line-item unresolved | `unresolved` containing `quantity`/`unit` | no |
| mapping ambiguous | `clarification_required` + `clarification_verdict = clarification_required` | no |
| supplier match ambiguous | **reuse** `clarification_required` with a supplier-specific `clarification_*` payload | no new state; **new payload variant** |
| operator confirmation required | same review surface | no |
| calculation blocked | queue `stage = blocked` + reason | no |
| ready for calculation | queue advances past validation (existing behaviour) | no |

**Conclusion:** the existing state model is sufficient; implementations must extend
**payloads**, not add statuses.

---

**24. Future Implementation File Map**

**PROPOSED-ONLY — none of these edits is performed in this task.**

| Area | Current location (inspected) | Proposed change | New file? | Schema change? | API change? | UI change? | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PDF header fields | `backend/engines/extraction.py` (`_DEFAULT_FIELD_PATTERNS`, `_extract_fields`) | add `customer`/`buyer`/`client` pattern; add an unlabelled supplier-header strategy with confidence; add period parsing | no | no | no | no | unit + 6-PDF regression |
| Field vocabulary | `backend/services/extraction_suggestions.py` (`_FIELD_ALIASES`, `suggest`) | add `customer`, `billing_period_start/end`, `vat_amount`; ISO-normalise `date` | no | no | no | no | same |
| Line contract | `backend/services/extraction_fidelity.py` (+ shaper) | table-region detection, unit-column identification, total/VRM/footer exclusion, `unit_price` + line `net_amount` | possibly a helper module | no | no | no | P1 unit tests + 6-PDF regression |
| P1 gating | `backend/services/extraction_fidelity.py` (`shape_mode`, `rollout_status`) | **unchanged code**; promotion is configuration + PO decision | no | no | no | no | gate-evidence test |
| Waste semantics | `backend/engines/factor_selection_policy.py`, `backend/engines/activity_clarification.py` | feed description/route evidence into the existing assessor; keep the guard | no | no | no | no | policy unit tests |
| Supplier normalisation | *(none — new)* | pure normaliser helper | **yes** (one module) | no | no | no | unit tests |
| Supplier resolution service | *(none — new)* | extract→normalise→search→score→confirm→create→persist, using `repos.suppliers.search_for_org` | **yes** (one service) | no | no | no | unit + integration |
| Supplier API | `backend/api/v3_suppliers.py`, `backend/data/suppliers.py` | **no change required** for search; only if a resolution endpoint is wanted | no | no | optional | optional | existing tests |
| Item mapping persistence | mapping path in `backend/services/automatic_processing.py` / `backend/api/v3_operations.py` | set `mapped_supplier_id` from resolution (currently operator-only) | no | no | no | no | integration |
| Calculation | `backend/engines/calculation.py` | accept/forward `supplier_id` to the emission write | no | no | no | no | unit + integration |
| Emission write | `backend/data/emissions_logs.py:258` | **add `supplier_id` to the INSERT column list** | no | **no** | no | no | integration + aggregation |
| Reporting | `backend/data/reporting.py:394` | no change (already consumes `mapped_supplier_id`) — verify | no | no | no | no | regression |
| Insight | `backend/domain/insight_query.py` | no change (dimension exists) — verify supplier bucketing stops being `none` | no | no | no | no | regression |
| Evidence | `backend/data/evidence_line_items.py` | no change | no | no | no | no | regression |
| Operator UI | existing workbench surfaces (`/api/v3/ops/entities/.../items/{id}/{map,clarify,mapping-options}`; manual-extraction item update) | surface supplier candidates only if P12-D2/D3/D4 require confirmation | no | no | maybe | yes (**demarcated**) | UI / e2e |

**Paths above are the ones actually inspected in this task** (§4 sources 5–14). None is invented.

---

**25. Future Acceptance Matrix**

Extends GAP-02's real-API method; the oracle is `tools/demo_lab/p12_canonical_manifest.json` only.

| # | Area | Acceptance | Must-fail evidence |
| --- | --- | --- | --- |
| A1 | Extraction — supplier | 6/6 `extracted_data.supplier == "Robinsons Recycling Services Ltd"` | any absent/blank value |
| A2 | Extraction — customer | 6/6 `extracted_data.customer == "Sustainable Direct Group"` | any absent value |
| A3 | Extraction — invoice refs | 6/6 exact (`SVC2025008717`, `SVC2024-8258`, `INV2026004869`, `UTL2025-1409`, `ECO2024006142`, `GRN/2027/1879`) | format loss or absence |
| A4 | Extraction — dates | 6/6 semantically correct, ISO-normalised | raw unparsed strings |
| A5 | Extraction — billing periods | 6/6 (start + end) | absent |
| A6 | Extraction — line structure | 6/6 emit `line_items[]` | any absent |
| B1 | Line accuracy — quantities | 21/21 exact | e.g. `…004` 5.0/43.0 vs 4.6/42.8 must fail |
| B2 | Line accuracy — units | 21/21 canonical-equivalent; **zero** `GBP`-as-unit | `…002`/`…005` must fail until fixed |
| B3 | Line accuracy — rates | 21/21 exact | — |
| B4 | Line accuracy — line nets | 21/21 exact | — |
| B5 | False positives | 0 rows from `Net Amount`/`VAT`/`GST`/`Total`/VRM/footer | `…003` and `…005` extras must fail |
| C1 | Waste mapping | a line whose description resolves to one family maps; `Waste` alone still requires clarification | silently mapping bare `Waste` = FAIL |
| D1 | Supplier resolution — first document | `…001` → candidate search → create/confirm → `supplier_id X` on the item | silent creation = FAIL |
| D2 | Supplier resolution — subsequent | `…002`, `…004` → **same** `supplier_id X` | divergence = FAIL |
| E1 | Multi-year | FY2026 `…003`,`…005`,`…006` → **same** `supplier_id X` | a second supplier id = FAIL unless evidence justifies it |
| F1 | Calculation | ≥1 canonical PDF produces a snapshot whose quantity/factor come only from mapped data | hand-entered values = FAIL |
| G1 | Evidence | every calculated line has an `evidence_line_items` row with `source_line_item_id` populated | orphan calculation = FAIL |
| H1 | Reporting | the canonical calculations appear in the organisation's reporting dataset, with supplier attribution where supported | absence = FAIL |
| I1 | Regression | EV-01 CSV chain intact (2 evidence lines, 2 snapshots, Viewer 200); existing suites unchanged | any regression = FAIL |
| J1 | Security | supplier resolution returns **only** the caller's organisation's suppliers; a cross-tenant attempt yields no candidate and no write | any cross-tenant hit = **security finding** |

Results must be captured with document/item/queue ids, per-field oracle comparison, and the P1
mode in force during the run.

---

**26. PO Decisions Required**

**P12-D1 — Waste activity semantics.**
*Question:* what minimum information is required before CarbonTally may automatically choose a
waste emission-factor family?
*Options:* (a) keep `Waste` always requiring clarification (*status quo*); (b) auto-match only
when the line's description/route vocabulary resolves to exactly one family; (c) require an
explicit operator-chosen waste stream/route per line before mapping.
*Consequences:* (a) blocks the investor waste lane; (b) unblocks it while staying fail-closed,
but depends on AREA A line quality; (c) safest but keeps a human in every line.
*Modules:* `engines/factor_selection_policy.py`, `engines/activity_clarification.py`,
`services/automatic_processing.py`, workbench `clarify` surface.
*Design recommendation (not an approval):* (b), sequenced **after** AREA A line quality.

**P12-D2 — Supplier matching policy.**
*Question:* when an extracted supplier strongly matches an existing organisation-scoped
supplier, may CarbonTally associate it automatically, or must an operator confirm?
*Options:* (a) auto-associate on `exact` only (identifier, or name + address agreement);
(b) auto-associate on `exact` **and** `strong`; (c) never auto-associate — always confirm.
*Consequences:* (a) low risk, small UI addition; (b) faster demo but higher mis-attribution
risk; (c) safest but adds a step to every document.
*Modules:* new supplier resolution service, `data/suppliers.py`, workbench mapping surface.
*Design recommendation (not an approval):* (a).

**P12-D3 — Supplier creation policy.**
*Question:* when no existing supplier matches, may CarbonTally automatically create one, or must
an operator confirm creation?
*Options:* (a) auto-create (single, idempotent) on `none`; (b) operator confirms via the
existing admin-gated `POST /api/v3/suppliers`; (c) block indefinitely.
*Consequences:* (a) smoothest demo but requires an authorisation decision, because creation is
currently `require_org_admin()`; (b) preserves the existing privilege boundary; (c) no progress.
*Modules:* supplier resolution service, `api/v3_suppliers.py` authority, workbench.
*Design recommendation (not an approval):* (b) for the demo; revisit (a) post-demo.

**P12-D4 — Ambiguous supplier matching.**
*Question:* what should happen when two existing suppliers are plausible candidates?
*Options:* (a) always require operator selection; (b) pick the highest score above a margin;
(c) refuse and mark unresolved.
*Consequences:* (a) safe and explainable; (b) risks silent mis-attribution — **not
recommended**; (c) safe but stalls until an operator intervenes anyway.
*Modules:* resolution verdicts, workbench confirmation, audit provenance.
*Design recommendation (not an approval):* (a).

**P12-D5 — customer↔organization linkage (raised here, not requested).**
*Question:* if the printed customer must ever be linked to a CarbonTally tenant, who decides and
on what evidence? **Not designed here**; no linkage may be inferred from a printed string.

**P12-D6 — page-count anomaly (raised here).** `page_count = 2` for five 1-page documents is
**NOT VERIFIED**; if real it affects evidence page references. Assign before relying on pages.

---

**27. MUST HAVE FOR DEMO**

| # | Item | Phase |
| --- | --- | --- |
| 1 | Supplier header extraction (labelled + unlabelled first-line strategy) | 1 |
| 2 | Customer extraction (pattern + alias) | 1 |
| 3 | Billing-period + `vat_amount` extraction; ISO date normalisation | 1 |
| 4 | Trustworthy `line_items[]`: unit column, rate, line net, total/VRM exclusion | 2 |
| 5 | Six-PDF regression harness driven by the committed oracle | 2, 7 |
| 6 | Waste disambiguation sufficient for the corpus' unambiguous lines | 4 |
| 7 | Supplier resolution with **operator confirmation** on create (pending P12-D3) | 5 |
| 8 | Supplier propagation `mapped_supplier_id` → `emissions_logs.supplier_id` | 6 |
| 9 | Evidence + Viewer reachable for PDF-derived lines | 6–7 |
| 10 | Reporting / Insight supplier attribution visible | 7 |

---

**28. POST-DEMO / FUTURE**

| # | Item | Why deferred |
| --- | --- | --- |
| 1 | P1 promotion to `enabled` as default | Needs gate evidence + PO decision |
| 2 | `supplier_id` column on `calculation_snapshots` | Not required; snapshots already link to items |
| 3 | Automatic supplier creation without an operator | Depends on P12-D3 + privilege review |
| 4 | Historical back-fill of `supplier_id` on existing emissions | Retro-attribution must not be silent |
| 5 | VAT/company-number extraction as a decisive matcher | Needs extraction work first |
| 6 | Supplier category/risk/compliance enrichment | Beyond demo scope |
| 7 | ~30-document robustness corpus (phase 8); multi-facility/vehicle corpora (phase 9) | Out of scope here |
| 8 | Customer↔organization linkage | P12-D5 |

---

**29. Risks / Open Questions**

| # | Risk / question | Impact | Mitigation |
| --- | --- | --- | --- |
| R1 | Header heuristics may treat a logo/tagline line as the supplier | wrong supplier → wrong attribution | confidence + `unresolved` fallback; never fabricate |
| R2 | P1 line classification is measurably weak on units/totals | false emissions if promoted early | gate §14; fail closed |
| R3 | Automatic supplier creation can fragment the master data | duplicate suppliers, split reporting | idempotent pre-create check; P12-D3 |
| R4 | Automatic association can mis-attribute similar names | wrong supplier on reports | P12-D2/D4; org-scoped only |
| R5 | Description-derived waste vocabulary may still be insufficient | permanent clarification loop | keep the clarification path; measure |
| R6 | Extraction vocabulary changes may shift existing payloads | regression on CSV/edge corpus | run existing suites + the T3 edge corpus |
| R7 | `page_count` anomaly unverified | evidence page references wrong | P12-D6 |
| R8 | Nothing in this design is measured yet | over-confidence | every claim marked VERIFIED/PROPOSED |

---

**30. Explicit Non-Changes**

```text
Product code changes        : NONE
Database schema changes     : NONE
Migration changes           : NONE
RLS changes                 : NONE
Configuration / .env changes: NONE
P1 promotion                : NONE
P1 env vars / allowlist     : NONE
Canonical corpus changes    : NONE
P12-DOC-03 oracle changes   : NONE
Suppliers created           : NONE
Extracted data repaired     : NONE
Canonical docs mapped/calculated : NONE
Database writes             : NONE
Production contacted        : NO
carbontally_test / carbontally_qa_phase8 / flagship postgres : untouched
```

The only file created by this task is this report (permitted by the task brief). The repository
diff check is recorded in §32.

---

**31. Step-2 / Step-3 Status**

```text
STEP 2 = INCOMPLETE
STEP 3 = NOT STARTED
```

This design task **does not** clear Step 2 and does not modify its acceptance state. The
existing blockers remain: (1) migration repeatability; (2) the `210 vs 218` policy variance;
(3) disposable integration acceptance; (4) canonical PDF investor journey (GAP-02 = FAIL).

---

**32. Final Acceptance of This Design Task**

| Requirement | Status |
| --- | --- |
| Read the four required documents | **DONE** |
| Inspect actual extraction code (§6–§11) | **DONE** — every claim cites a file/function/line |
| Reconcile GAP-02 against code (§7) | **DONE** — all findings explained; one left NOT VERIFIED |
| Produce Areas A–D contracts (§12–§21) | **DONE** |
| P1 promotion gates defined, not applied (§14) | **DONE** |
| Evidence/provenance contract preserved (§22) | **DONE** |
| States mapped to existing contracts (§23) | **DONE** |
| Implementation file map with real paths (§24) | **DONE** |
| Future acceptance matrix (§25) | **DONE** |
| PO decisions listed (§26) | **DONE — 4 required + 2 raised** |
| MUST-HAVE vs POST-DEMO separation (§27/§28) | **DONE** |
| Corpus NOT expanded | **DONE** |
| No product code / schema / migration / RLS / config change | **DONE** |
| Step-2 / Step-3 status preserved | **DONE** |

**Design task verdict: COMPLETE. Implementation: NOT STARTED (by design).**

---

**Proposed Implementation Sequence** (brief §29, analysed against repository evidence)

The brief's suggested order is **largely correct**, with evidence-driven refinements: the P1
promotion decision must come **after** line-item quality work (not before), and supplier
resolution must follow supplier extraction (it has no input otherwise).

| Phase | Work | Depends on | Demo-critical? |
| --- | --- | --- | --- |
| **1** | PDF supplier/customer header extraction (+ period, `vat_amount`, ISO dates) | — | **YES** |
| **2** | Reliable PDF line-item extraction (units, rate, line net, total/VRM/footer exclusion) | shares the parser with Phase 1 — do together | **YES** |
| **3** | P1 regression validation → **promotion decision** (gates §14) | Phases 1–2, to be meaningful | YES (decision) |
| **4** | Waste activity semantics / factor mapping (P12-D1) | Phase 2 (needs trustworthy descriptions) | **YES** |
| **5** | Supplier resolution (extract→normalise→search→score→confirm) | Phase 1 + P12-D2/D4 | **YES** |
| **6** | Supplier persistence & propagation (`mapped_supplier_id` → `emissions_logs.supplier_id`) | Phase 5 | **YES** |
| **7** | Six-PDF end-to-end acceptance (GAP-02 rerun, oracle-driven) | Phases 1–6 | **YES** |
| **8** | Expanded robustness corpus (~30 docs) | Phase 7 green | NO (post-demo) |
| **9** | Multi-facility / multi-vehicle corpora | Phase 8 | NO (post-demo) |

**Refinements to the brief's ordering, with reasons:**

* **Phase 3 cannot precede Phase 2.** P1's measured defects (§10) are *line-classification*
  defects; promoting before fixing them would make the primary path emit exactly the false
  positives GAP-02 recorded in the probe.
* **Phase 5 must follow Phase 1.** Supplier resolution has no input until the supplier string is
  extracted (GAP-02 measured 0/6).
* **Phase 4 is independent of Phase 5** and may run in parallel once Phase 2 is trustworthy, but
  keeping it earlier shortens the critical path.
* **Phase 6 is the smallest change with the largest visible effect** — one INSERT column list at
  `backend/data/emissions_logs.py:258` — and should be scheduled with Phase 5 to avoid a second
  acceptance cycle.

---

**STOP.** No implementation, no defect fixes, no P1 promotion, no additional PDFs, no Step 3.




