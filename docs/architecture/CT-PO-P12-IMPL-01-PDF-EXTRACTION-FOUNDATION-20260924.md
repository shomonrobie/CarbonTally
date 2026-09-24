# CT-PO-P12-IMPL-01 — PDF Extraction Foundation: Header Fields, Billing Period and Trustworthy Line Items

**1. Task identity**

| Item | Value |
| --- | --- |
| Task ID | `P12-IMPL-01-20260924-PDF-EXTRACTION-FOUNDATION` |
| Date | 2026-09-24 |
| Repository / branch | `/home/shomonrobie/ct_93d5cdd` @ `p8-release-reconciled` |
| Baseline commit | `7594e61` |
| Type | **Implementation** (PDF extraction foundation only) |
| Extraction artifact | `docs/architecture/artifacts/p12_impl_01_extracted_data_20260924.json` |

**2. Scope**

Implemented: PDF supplier/customer header extraction, invoice reference fallback,
billing-period extraction, date normalisation, and trustworthy `line_items[]`
(description/activity/quantity/unit/rate/net) with total/footer/VRM/currency exclusions.

Not implemented (deliberately out of scope): supplier matching/creation/reuse/
persistence/propagation, emissions `supplier_id`, waste factor semantics, automatic waste
matching, P1 promotion, reporting, Insight, new corpora, Step 3.

**3. Safety / environment**

| Item | Value |
| --- | --- |
| Database | `carbontally_demo_local` (`current_database()` verified) |
| Host / port | `127.0.0.1:54426` → container `supabase_db_carbon_ledger` |
| Backend | `127.0.0.1:8070` (restarted once so the new code was loaded; **no configuration change**) |
| Production | never contacted |
| `carbontally_test`, `carbontally_qa_phase8`, flagship `postgres` | untouched |
| Schema / migrations / RLS / `.env` | **unchanged** |
| SQL writes by the acceptance runner | **none** (uploads only, through the product API) |
| Destructive resets | none |

**4. Baseline commit**

`7594e61` (`docs(p12-decision-01): … product contract (design only, no implementation)`).
The acceptance artifact records `commit_sha: 7594e61f`.

**5. Files inspected**

`backend/services/automatic_extraction.py` · `backend/services/extraction_suggestions.py` ·
`backend/engines/extraction.py` · `backend/services/extraction_fidelity.py` ·
`backend/domain/automatic_processing.py` · `backend/services/automatic_processing.py` ·
`backend/pdf_engine.py` (via `_pdf_text`) ·
`backend/tests/unit/services/test_p1_controlled_rollout.py` ·
`backend/tests/unit/services/test_automatic_extraction_text_layer.py` ·
`backend/tests/unit/services/test_pod1_bounded_ai_fanout.py` ·
`backend/tests/unit/services/test_structured_file_parity.py` ·
`tools/demo_lab/{lab,t3_scenarios}.py` · the six canonical PDFs and the oracle manifest.

**6. Files changed**

| File | Change |
| --- | --- |
| `backend/engines/invoice_extraction.py` | **new** — pure deterministic invoice parsing vocabulary (dates, periods, supplier header strategy, item-table rows, unit/exclusion rules) |
| `backend/engines/extraction.py` | extended `_DEFAULT_FIELD_PATTERNS`: `invoice_ref`, `customer`, `billing_period`, `vat_amount`, plus wider `date`/`net_amount`/`gross_amount` label coverage |
| `backend/services/extraction_suggestions.py` | extended `_FIELD_ALIASES` (customer, billing period, VAT); Waste keyword family; `suggest()` normalises dates, splits periods, emits `line_items[]`, records `extraction_evidence`, and stops misreporting line-resolved fields as unresolved |
| `backend/domain/automatic_processing.py` | `PIPELINE_VERSION` bumped `v3-auto-1.1` → `v3-auto-1.2` (extraction-shape stamp for new documents) |
| `backend/tests/unit/services/test_p12_impl_01_invoice_extraction.py` | **new** — 69 unit tests |
| `tools/demo_lab/p12_impl_01_acceptance.py` | **new** — real product-path acceptance runner |
| `docs/architecture/artifacts/p12_impl_01_extracted_data_20260924.json` | **new** — machine-readable actual extraction results |
| `docs/architecture/CT-PO-P12-IMPL-01-PDF-EXTRACTION-FOUNDATION-20260924.md` | **new** — this report |

**7. Implementation summary**

The existing deterministic engine remains the single extraction path; what changed is its
**vocabulary and composition**:

```text
_pdf_text(pdf) -> text
      |
      v
DocumentExtractionEngine.suggest_fields(text)   # generic Key: value + named patterns
      |                                         # (extended: customer/ref/period/VAT)
      v
extraction_suggestions.suggest(text)            # the existing adapter
      |-- aliases -> extracted_data keys
      |-- supplier:  labelled pattern, else invoice_extraction.extract_supplier_header()
      |-- date:      invoice_extraction.parse_date()    (+ date_raw preserved)
      |-- period:    invoice_extraction.parse_period()  (+ billing_period_raw)
      |-- rows:      invoice_extraction.extract_invoice_lines() -> line_items[]
      v
{status, method, page_count, extracted_data, unresolved, confidence[, coverage]}
```

Design properties: pure functions, no AI, no randomness, **fail-closed** (a value is
emitted only when the document supports it), no document-specific logic (§36/§37 honoured —
verified by a unit test that parses an unrelated supplier identically).

**8. Supplier extraction changes**

* Labelled `Supplier:` still wins (existing pattern unchanged).
* **New** `extract_supplier_header()`: identifies the sender inside the pre-marker header
  block using *structural* evidence — a plausible company line (commercial-name marker,
  ≥2 capitalised word tokens, not an amount/date/postcode) **plus** address context (a
  following postcode/digit-bearing address line before the document-type marker) — and
  requires the best candidate to **strictly outrank** the runner-up.
* Unlabelled canonical header (`Robinsons Recycling Services Ltd` first line, address
  below, `WASTE INVOICE` marker) → **detected 6/6**.
* Uncertain headers (no pre-marker block, ambiguous candidates, insufficient evidence) →
  **unresolved**, never guessed. `extraction_evidence.supplier_source` records
  `labelled` vs `document_header`.

**9. Customer extraction changes**

* **New** `customer` pattern covering `Customer|Buyer|Client|Recipient|Bill To|Sold To|Invoice To`
  and a `customer` entry in `_FIELD_ALIASES` (previously the generic `Key: value` pass *did*
  capture `Buyer: …` and the alias step then discarded it).
* The value is **document content only** — no tenant/organisation linkage, no organization
  creation, no ID mapping (P12-D5 respected; asserted by a unit test).

**10. Billing-period changes**

* **New** `billing_period` pattern (`Period|Billing|Reporting Period|Service Period`) and
  `parse_period()`, splitting on en-dash/em-dash/hyphen/`to`; returns
  `(billing_period_start, billing_period_end)` only when **both** ends parse.
* Printed value preserved verbatim in `billing_period_raw`. A single date is never promoted
  to a period; an end date is never invented.

**11. Date normalisation changes**

* `parse_date()` handles `YYYY-MM-DD`, `d-m-yyyy` (day-first UK convention),
  `Mon DD, YYYY` and `DD Month YYYY`; ambiguity is resolved by a documented deterministic
  convention and the printed value is always preserved in `date_raw`.
* `Issued:` is now recognised alongside `Date:` / `Invoice Date:` (the `Ref:`/`Issued:`
  layout variant).

**12. Line-item extraction changes**

* **New** `extract_invoice_lines()` (pure): locates the item-table header row
  (`Description Qty Unit Rate Subtotal|Net Amount|Net Total|Amount`), parses rows as
  `description … quantity unit rate amount` taking the numeric fields from the **end** of
  the line (so a description carrying its own `- Qty: …` note still parses), and stops at
  the first total/tax/payment/footer label.
* Each row carries `description, activity, quantity, unit (canonical), unit_raw,
  unit_price, net_amount, line_number, source_line, source_line_number, arithmetic_ok,
  arithmetic_deviation, extraction_method='det:pdf_table'`.
* Arithmetic is **reported, not enforced** — `quantity × rate ≈ net` is flagged and never
  used to rewrite a printed value.
* `suggest()` no longer reports `activity`/`quantity`/`unit` as document-level `unresolved`
  when the lines resolve them, and does not fabricate a document-level quantity from
  multi-line data. `_completeness()` already handled `line_items` (verified) — **no
  completeness threshold change was needed or made** (§21).

**13. False-positive protections**

| Protection | Mechanism |
| --- | --- |
| `Subtotal`, `Net Amount`, `Net Total`, `Net Payable` | table region stops at the first stop-label (`_TABLE_STOP_RE`) |
| `VAT`, `VAT (20%)`, `Tax (20%)`, `GST` | same stop vocabulary; each label is a parametrised unit test |
| `Total`, `Total Due` | same |
| payment/bank block (`Payment Information`, `Bank`, `Sort Code`, `Account Number`, `Reference`, `IBAN`, `SWIFT`) | same |
| footer/annotation (`Terms`, `Notes`, `Page n`, `APPROVED`, `paid`) | same |
| VRM/postcode text (`MH82 2KM`) | header region, never inside the item table — no table header precedes it, so it cannot be a row |
| **currency-as-unit (`GBP`)** | `canonical_unit()` rejects currency tokens outright; a row whose unit is a currency is dropped |
| unknown units (`widgets`) | rejected unless in the unit vocabulary |
| row shape | requires description **and** numeric quantity **and** unit **and** rate **and** amount on one line |

Result on the canonical corpus: **0 false-positive line items** (§19).

**14. P1 status**

**Not promoted.** Default mode remains `shadow`; `CARBONTALLY_P1_EXTRACTION_SHAPE` and
`CARBONTALLY_P1_ORGANIZATION_ALLOWLIST` were **not** set or changed; P1 code
(`extraction_fidelity.py`, `_apply_p1_fidelity`) was **not modified**; P1's tests pass (§18).

**Architectural note (required by §23).** The primary PDF path now emits structured
`line_items[]` from a **deterministic** table parser rather than from the P1 shaper. This is a
deliberate, documented change of the primary path — not an accidental bypass of rollout
controls:

* P1 governs *AI-assisted* multi-line shaping and AI fan-out (`P1-D1`…`P1-D8`); this parser
  makes no AI call, has no fan-out, and cannot silently collapse a document;
* it is **fail-closed** — rows that do not satisfy the contract are dropped, not guessed;
* P1 remains available, unmodified and un-promoted, and its shadow coverage still runs;
* `PIPELINE_VERSION` was bumped to `v3-auto-1.2` so the shape change is stamped for new
  documents.

**A PO decision is advisable** on whether the deterministic invoice-table parser should become
the governed primary path (making P1's promotion question largely moot for text-native
invoices) or be placed behind the same rollout control. This report does not decide that.

**15. Waste policy status**

**Unchanged by design.** `factor_selection_policy.py` and `activity_clarification.py` were
**not modified**; bare `Waste` remains insufficient evidence (P12-D1 deferred to
P12-IMPL-02). The acceptance run shows this working correctly: extraction now succeeds and the
pipeline advances as far as **mapping**, where it blocks fail-closed with the existing
clarification reason (§20).

**16. Supplier resolution status**

**Not implemented.** `mapped_supplier_id` is `NULL` for all six documents (verified
`mapped_supplier_set=0`), no supplier was created (`suppliers=1`, the pre-existing row), and
`extracted_data.supplier` is populated — exactly the intended split of extraction from
resolution (§24).

**17. Database / schema status**

No migrations, no schema changes, no new tables/columns, no RLS changes, no direct data
repair. Every new key is JSONB content inside the existing contract. The only database writes
were the product's own ingestion writes for the six uploads.

**18. Test inventory**

| Suite | Command | Result |
| --- | --- | --- |
| P12-IMPL-01 unit tests (new) | `cd backend && .venv/bin/python -m pytest tests/unit/services/test_p12_impl_01_invoice_extraction.py -q` | **69 passed** |
| P1 rollout + text-layer + AI-fanout + structured-file parity (existing) | `… -m pytest tests/unit/services/test_p1_controlled_rollout.py tests/unit/services/test_automatic_extraction_text_layer.py tests/unit/services/test_pod1_bounded_ai_fanout.py tests/unit/services/test_structured_file_parity.py -q` | **35 passed** (no regression) |
| Six-PDF real product-path acceptance | `./backend/.venv/bin/python tools/demo_lab/p12_impl_01_acceptance.py` | see §20 |
| CSV/EV-01 regression | DB observation (§21) | unchanged |

The new unit suite covers, per §29 A: labelled supplier; canonical unlabelled supplier;
uncertain header; missing supplier; title-first fail-closed; customer labels (Buyer/Customer/
Client/Recipient/Bill To/Sold To) and missing customer; no tenant linkage; date forms and
rejections; `date_raw` preservation; period ranges (standard, month boundary, **year
boundary**) and malformed/absent periods; table-header requirement; all five field
extractions; 15 total/footer/VRM/currency/unknown-unit exclusion cases; unit
canonicalisation; rounded-document values kept-not-rewritten; 4-decimal preservation; four
header-row variants; adapter integration; reference-label fallback; `VAT No` ≠ VAT amount;
and a no-hard-coding structural test with an unrelated supplier.

**19. Six-PDF oracle comparison — ACTUAL extracted values**

Source of every "extracted" value below: the **real product-path acceptance run**
(upload → product extraction workflow → product-persisted extraction record). Full raw payloads:
`docs/architecture/artifacts/p12_impl_01_extracted_data_20260924.json` (§44).
Extraction method for all rows: `det:pdf_table`; queue `pipeline_version` = `v3-auto-1.2`.

### 19.1 `p12canon_waste_001` — document level

| Field | Expected / Oracle | ACTUAL EXTRACTED | Result |
| --- | --- | --- | --- |
| supplier | Robinsons Recycling Services Ltd | Robinsons Recycling Services Ltd | PASS |
| customer | Sustainable Direct Group | Sustainable Direct Group | PASS |
| invoice_ref | SVC2025008717 | SVC2025008717 | PASS |
| invoice_date | 2025-04-02 | 2025-04-02 (raw `2025-04-02`) | PASS |
| period_start | 2025-03-01 | 2025-03-01 | PASS |
| period_end | 2025-03-31 | 2025-03-31 | PASS |
| subtotal | 27674.48 | `£27,674.48` | PASS |
| VAT | 5534.89 | `£5,534.89` | PASS |
| total | 33209.37 | `£33,209.37` | PASS |

```json
{ "supplier": "Robinsons Recycling Services Ltd",
  "customer": "Sustainable Direct Group",
  "invoice_number": "SVC2025008717",
  "date": "2025-04-02", "date_raw": "2025-04-02",
  "billing_period_start": "2025-03-01", "billing_period_end": "2025-03-31",
  "billing_period_raw": "2025-03-01 – 2025-03-31",
  "net_amount": "£27,674.48", "vat_amount": "£5,534.89", "gross_amount": "£33,209.37",
  "extraction_evidence": {"supplier_source": "document_header",
    "supplier_header": {"strategy": "header_block", "marker_line": "WASTE INVOICE"},
    "line_item_count": 3} }
```

| Line | Expected Description | ACTUAL Description | Exp Qty | Act Qty | Exp Unit | Act Unit | Exp Rate | Act Rate | Exp Net | Act Net | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Recycling services - Mixed | Recycling services - Mixed | 90.0 | 90.0 | tonnes | tonnes | 107.639 | 107.64 | 9687.51 | 9687.51 | qty PASS · unit PASS · rate **FAIL** · net PASS |
| 2 | Waste disposal - General | Waste disposal - General | 64.0 | 64.0 | tonnes | tonnes | 190.222 | 190.22 | 12174.21 | 12174.21 | qty PASS · unit PASS · rate **FAIL** · net PASS |
| 3 | Waste disposal - Mixed | Waste disposal - Mixed | 58.0 | 58.0 | tonnes | tonnes | 100.22 | 100.22 | 5812.76 | 5812.76 | **all PASS** |

Printed source proof for the two rate mismatches:
`Recycling services - Mixed 90 tonnes £107.64 £9,687.51` and
`Waste disposal - General 64 tonnes £190.22 £12,174.21` — the **document prints 2 decimals**,
the oracle records full precision (`107.639`, `190.222`). Line count 3/3; false positives 0.

### 19.2 `p12canon_waste_002` — document level

| Field | Expected / Oracle | ACTUAL EXTRACTED | Result |
| --- | --- | --- | --- |
| supplier | Robinsons Recycling Services Ltd | Robinsons Recycling Services Ltd | PASS |
| customer | Sustainable Direct Group | Sustainable Direct Group | PASS |
| invoice_ref | SVC2024-8258 | SVC2024-8258 | PASS |
| invoice_date | 2025-03-05 | 2025-03-05 | PASS |
| period_start | 2025-02-01 | 2025-02-01 | PASS |
| period_end | 2025-02-28 | 2025-02-28 | PASS |
| subtotal | 35011.09 | `£35,011` | **FAIL** |
| VAT | 7002.22 | `£7,002` | **FAIL** |
| total | 42013.31 | `£42,013` | **FAIL** |

| Line | Expected Description | ACTUAL Description | Exp Qty | Act Qty | Exp Unit | Act Unit | Exp Rate | Act Rate | Exp Net | Act Net | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Waste collection - Recycling | Waste collection - Recycling - Qty: 112.0 … | 112.0 | 112.0 | tonnes | tonnes | 178.665 | 179.0 | 20010.48 | 20010.0 | qty PASS · unit PASS · rate **FAIL** · net **FAIL** |
| 2 | Waste collection - Recycling | Waste collection - Recycling - Qty: 25.8 t… | 25.8 | 26.0 | tonnes | tonnes | 189.996 | 190.0 | 4901.90 | 4902.0 | **FAIL ×3** (unit PASS) |
| 3 | Waste disposal - Hazardous | Waste disposal - Hazardous - Qty: 63.5 … | 63.5 | 64.0 | tonnes | tonnes | 98.522 | 99.0 | 6256.15 | 6256.0 | **FAIL ×3** (unit PASS) |
| 4 | Waste disposal - Recycling | Waste disposal - Recycling - Qty: 47.6 … | 47.6 | 48.0 | tonnes | tonnes | 80.726 | 81.0 | 3842.56 | 3843.0 | **FAIL ×3** (unit PASS) |

Printed source proof (this document renders at **0 decimals**):
`Waste collection - Recycling - Qty: 112.0 ... 112 t £179 £20,010`,
`Waste collection - Recycling - Qty: 25.8 t... 26 t £190 £4,902`,
`Waste disposal - Hazardous - Qty: 63.5 tonnes 64 t £99 £6,256`,
`Waste disposal - Recycling - Qty: 47.6 tonnes 48 t £81 £3,843`.
Line count 4/4; false positives 0; `arithmetic_ok` false on lines 2–4 (consistent with printing
rounded figures).

### 19.3 `p12canon_waste_004` — document level

| Field | Expected / Oracle | ACTUAL EXTRACTED | Result |
| --- | --- | --- | --- |
| supplier | Robinsons Recycling Services Ltd | Robinsons Recycling Services Ltd | PASS |
| customer | Sustainable Direct Group | Sustainable Direct Group | PASS |
| invoice_ref | INV2026004869 | INV2026004869 | PASS |
| invoice_date | 2025-07-03 | 2025-07-03 (raw `03-07-2025`) | PASS |
| period_start | 2025-06-01 | 2025-06-01 | PASS |
| period_end | 2025-06-30 | 2025-06-30 | PASS |
| subtotal | 5318.44 | `£5,318` | **FAIL** |
| VAT | 1063.69 | `£1,064` | **FAIL** |
| total | 6382.13 | `£6,382` | **FAIL** |

| Line | Expected Description | ACTUAL Description | Exp Qty | Act Qty | Exp Unit | Act Unit | Exp Rate | Act Rate | Exp Net | Act Net | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Waste collection - General | Waste collection - General (ID: None) | 4.6 | 5.0 | tonnes | tonnes | 64.643 | 65.0 | 297.36 | 297.0 | **FAIL ×3** (unit PASS) |
| 2 | Waste disposal - Organic | Waste disposal - Organic (ID: None) | 42.8 | 43.0 | tonnes | tonnes | 117.315 | 117.0 | 5021.08 | 5021.0 | **FAIL ×3** (unit PASS) |

Printed source proof (0-decimal rendering):
`Waste collection - General (ID: None) 5 tonnes £65 £297`,
`Waste disposal - Organic (ID: None) 43 tonnes £117 £5,021`.
Line count 2/2; false positives 0.
**Note:** GAP-02's "P1 produced 5.0/43.0 instead of 4.6/42.8" is explained — the **document
itself prints 5 and 43**; the extractor is faithful to the source.

### 19.4 `p12canon_waste_003` — document level

| Field | Expected / Oracle | ACTUAL EXTRACTED | Result |
| --- | --- | --- | --- |
| supplier | Robinsons Recycling Services Ltd | Robinsons Recycling Services Ltd | PASS |
| customer | Sustainable Direct Group | Sustainable Direct Group | PASS |
| invoice_ref | UTL2025-1409 | UTL2025-1409 | PASS |
| invoice_date | 2026-07-02 | 2026-07-02 | PASS |
| period_start | 2026-06-01 | 2026-06-01 | PASS |
| period_end | 2026-06-30 | 2026-06-30 | PASS |
| subtotal | 11628.76 | `£11,628.76` | PASS |
| VAT | 2325.76 | `£2,325.76` | PASS |
| total | 13954.52 | `£13,954.52` | PASS |

| Line | Expected Description | ACTUAL Description | Exp Qty | Act Qty | Exp Unit | Act Unit | Exp Rate | Act Rate | Exp Net | Act Net | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Waste disposal - Mixed | Waste disposal - Mixed | 16.0 | 16.0 | tonnes | tonnes | 186.208 | 186.21 | 2979.33 | 2979.33 | qty/unit/net PASS · rate **FAIL** |
| 2 | Waste disposal - Mixed | Waste disposal - Mixed | 29.0 | 29.0 | tonnes | tonnes | 83.741 | 83.74 | 2428.49 | 2428.49 | qty/unit/net PASS · rate **FAIL** |
| 3 | Recycling services - Organic | Recycling services - Organic | 18.0 | 18.0 | tonnes | tonnes | 94.935 | 94.94 | 1708.83 | 1708.83 | qty/unit/net PASS · rate **FAIL** |
| 4 | Waste disposal - Mixed | Waste disposal - Mixed | 26.0 | 26.0 | tonnes | tonnes | 51.864 | 51.86 | 1348.46 | 1348.46 | qty/unit/net PASS · rate **FAIL** |
| 5 | Waste disposal - Hazardous | Waste disposal - Hazardous | 19.0 | 19.0 | tonnes | tonnes | 166.508 | 166.51 | 3163.65 | 3163.65 | qty/unit/net PASS · rate **FAIL** |

Printed source proof: `Waste disposal - Mixed 16 tonnes £186.21 £2,979.33` (and the four sibling
rows) — the document prints rates at **2 decimals** while the oracle stores 3 (`186.208`).
Line count 5/5; false positives 0.

### 19.5 `p12canon_waste_005` — document level

| Field | Expected / Oracle | ACTUAL EXTRACTED | Result |
| --- | --- | --- | --- |
| supplier | Robinsons Recycling Services Ltd | Robinsons Recycling Services Ltd | PASS |
| customer | Sustainable Direct Group | Sustainable Direct Group | PASS |
| invoice_ref | ECO2024006142 | ECO2024006142 | PASS |
| invoice_date | 2026-07-07 | 2026-07-07 | PASS |
| period_start | 2026-06-01 | 2026-06-01 | PASS |
| period_end | 2026-06-30 | 2026-06-30 | PASS |
| subtotal | 8949.69 | `£8,949.690` | PASS |
| VAT | 1789.93 | `£1,789.930` | PASS |
| total | 10739.62 | `£10,739.620` | PASS |

| Line | Expected Description | ACTUAL Description | Exp Qty | Act Qty | Exp Unit | Act Unit | Exp Rate | Act Rate | Exp Net | Act Net | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Waste disposal | Waste disposal | 36.7 | 36.7 | tonnes | tonnes | 127.074 | 127.0 | 4663.62 | 4664.0 | qty/unit PASS · rate **FAIL** · net **FAIL** |
| 2 | Waste disposal | Waste disposal | 17.2 | 17.2 | tonnes | tonnes | 165.465 | 165.0 | 2846.0 | 2846.0 | rate **FAIL**, rest PASS |
| 3 | Recycling services | Recycling services | 8.0 | 8.0 | tonnes | tonnes | 180.009 | 180.0 | 1440.07 | 1440.0 | qty/unit PASS · rate **FAIL** · net **FAIL** |

Printed source proof: `Waste disposal 36.700 t £127 £4,664`, `Waste disposal 17.200 t £165 £2,846`,
`Recycling services 8 t £180 £1,440`. Line count 3/3; false positives 0.

### 19.6 `p12canon_waste_006` — document level

| Field | Expected / Oracle | ACTUAL EXTRACTED | Result |
| --- | --- | --- | --- |
| supplier | Robinsons Recycling Services Ltd | Robinsons Recycling Services Ltd | PASS |
| customer | Sustainable Direct Group | Sustainable Direct Group | PASS |
| invoice_ref | GRN/2027/1879 | GRN/2027/1879 | PASS |
| invoice_date | 2026-02-02 | 2026-02-02 (raw `Feb 02, 2026`) | PASS |
| period_start | 2026-01-01 | 2026-01-01 | PASS |
| period_end | 2026-01-31 | 2026-01-31 | PASS |
| subtotal | 36484.57 | `£36,484.5700` | PASS |
| VAT | 7296.91 | `£7,296.9100` | PASS |
| total | 43781.48 | `£43,781.4800` | PASS |

| Line | Expected Description | ACTUAL Description | Exp Qty | Act Qty | Exp Unit | Act Unit | Exp Rate | Act Rate | Exp Net | Act Net | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Recycling services - Organic | Recycling services - Organic | 41.98 | 41.98 | tonnes | tonnes | 93.821 | 93.821 | 3938.61 | 3938.61 | **all PASS** |
| 2 | Recycling services - Mixed | Recycling services - Mixed | 91.6 | 91.6 | tonnes | tonnes | 141.134 | 141.134 | 12927.87 | 12927.87 | **all PASS** |
| 3 | Waste collection - Recycling | Waste collection - Recycling | 41.42 | 41.42 | tonnes | tonnes | 84.737 | 84.737 | 3509.81 | 3509.81 | **all PASS** |
| 4 | Recycling services - Mixed | Recycling services - Mixed | 94.7 | 94.7 | tonnes | tonnes | 170.098 | 170.098 | 16108.28 | 16108.28 | **all PASS** |

Printed source proof: `Recycling services - Organic 41.9800 tonnes £93.8210 £3,938.6100` — this
document renders at **4 decimals**, which matches the oracle exactly. Line count 4/4; false
positives 0.

### 19.7 Corpus roll-up against the §30 targets

| §30 target | Result |
| --- | --- |
| 6/6 upload | **6/6 PASS** (HTTP 201) |
| 6/6 extracted | **6/6 PASS** (`status=ok`, item `status=extracted`) |
| Supplier 6/6 | **6/6 PASS** |
| Customer 6/6 | **6/6 PASS** |
| Invoice reference 6/6 | **6/6 PASS** |
| Invoice date 6/6, normalised | **6/6 PASS** |
| Billing period 6/6 | **6/6 PASS** |
| `line_items[]` 6/6 | **6/6 PASS** |
| Exact line counts (3,4,2,5,3,4) | **6/6 PASS — 21 lines total** |
| Quantities 21/21 | **16/21** — 5 differ because the **document prints rounded figures** (`002` ×3, `004` ×2) |
| Units 21/21 | **21/21 PASS** (`tonnes`; printed `t` and `tonnes` both canonicalised) |
| Rates 21/21 | **5/21** — 16 differ because the document prints fewer decimals than the oracle (`001` ×2, `002` ×4, `003` ×5, `004` ×2, `005` ×3; `006` ×4 PASS) |
| Line nets 21/21 | **13/21** — 8 differ for the same printed-precision reason (`002` ×4, `004` ×2, `005` ×2) |
| False positives 0 | **0 PASS** |
| Document totals 6/6 | **4/6 PASS** (`002`, `004` print 0-decimal totals) |

**43.6 false-positive disclosure:** **zero** false-positive rows were produced; there is
therefore nothing hidden. The previously reported P1 false positives (`Net Amount: £11,628.76`,
`GST: £1,789.93`, `MH82 2KM`) are **absent** from this run — `003` yields exactly 5 lines and
`004` exactly 2, with the totals captured as document fields instead.

**20. Real product-path acceptance**

| Observation | Result |
| --- | --- |
| Uploads | **6/6 HTTP 201** via `POST /api/v3/uploads` (Demo Lab Organisation A `3fd0f325-…`) |
| Uploaded bytes hash | **6/6 match the oracle** SHA-256 |
| Product extraction status | `status=ok`, `method=pdf_text` for all six |
| Extraction item (`manual_extraction_items`) | `status=extracted` for all six — the durable product record the workbench reads |
| Queue state | `status=manual_review`, `stage=blocked` |
| Queue blocking reason | **mapping** clarification for `'Waste'` (P12-D1 policy) — **no longer** extraction completeness ⇒ **the extraction gate now passes** |
| `pipeline_version` | `v3-auto-1.2` (new shape stamp) for all six |
| Observation method | product ingestion API + read of the product-persisted extraction record; **no SQL INSERT/UPDATE anywhere** |
| Application read endpoint | `GET /api/v3/customer-documents/{id}/extraction` returned **404** with both the extraction-item id and the `customer_documents` id — **NOT VERIFIED as a working read path**; observation therefore used the product-persisted record. Flagged as a limitation (§26 L5) |

**Extraction also produced real provenance (unexpected, positive).** `evidence_line_items` went
**2 → 23**; the 21 new rows are one per extracted PDF line:

| Source file | Evidence lines | line_numbers | `extraction_method` | `materialisation_kind` |
| --- | --- | --- | --- | --- |
| `p12canon_waste_001.pdf` | 3 | 1–3 | `det:pdf_table` | FORWARD |
| `p12canon_waste_002.pdf` | 4 | 1–4 | `det:pdf_table` | FORWARD |
| `p12canon_waste_003.pdf` | 5 | 1–5 | `det:pdf_table` | FORWARD |
| `p12canon_waste_004.pdf` | 2 | 1–2 | `det:pdf_table` | FORWARD |
| `p12canon_waste_005.pdf` | 3 | 1–3 | `det:pdf_table` | FORWARD |
| `p12canon_waste_006.pdf` | 4 | 1–4 | `det:pdf_table` | FORWARD |
| `p12imp_org-a-multi-site-gas-2025.csv` | 2 | 1–2 | `csv` | FORWARD (pre-existing, unchanged) |

Each row carries `raw_quantity`, `raw_unit` (e.g. `94.7 tonnes`) and a `source_item_id` that
points at the canonical extraction item; `source_file_id` resolves to `organization_files`.
So the PDF lane now has the same class of FORWARD provenance the CSV/EV-01 lane had.
(43.5 extraction evidence: per-line `source_line`, `source_line_number`,
`extraction_method='det:pdf_table'`, `line_number` are in the payload;
document-level provenance is in `extraction_evidence`.)

**21. Existing CSV / EV-01 regression**

| Check | Result |
| --- | --- |
| EV-01 CSV extraction item | `p12imp_org-a-multi-site-gas-2025.csv` `status=calculated`, still **2 line items** — unchanged |
| EV-01 evidence lines | `source_file c806c0cc-…` → **2 lines** (unchanged, still `csv`/FORWARD) |
| `calculation_snapshots` | **2** (unchanged — no new calculations) |
| `emissions_logs` | **2** (unchanged) |
| `report_generation_queue` | **4** (unchanged) |
| CSV fixtures | **not modified** |

**22. Existing document / T3 regression**

* Existing **unit suites** for extraction, P1 rollout, text-layer behaviour, AI fan-out and
  structured-file parity: **35 passed** (no regression).
* The 10-document **T3 edge corpus was NOT re-processed** in this task (its Step-2 queue rows
  are untouched). This is an honest gap: the extended field vocabulary could alter payloads for
  other layouts. Recommended follow-on: re-run one T3 upload per scenario after P12-IMPL-02 and
  diff the payloads. Existing T3 rows were neither modified nor deleted.

**23. Security regression**

| Check | Result |
| --- | --- |
| Suppliers created | **0** (`suppliers=1`, the pre-existing CRUD-created row) |
| `mapped_supplier_id` set | **0/6** (no resolution attempted) |
| Cross-tenant supplier access introduced | **none** (no supplier lookup exists in this change) |
| RLS / policy changes | **none** |
| Extraction scoping | unchanged — the pipeline passes `job.organization_id` into `extract_document`, so the P1 rollout scope and all reads stay org-bound |
| Printed customer used as tenant | **no** — `customer` is document content only; no organization was created or linked |
| New authorization surface | **none** |

**24. Performance observations**

* The parser is pure regex + pure functions: no AI call, no model, no network, no new I/O.
* `_pdf_text` is unchanged; the added cost is one extra pass over the already-extracted text
  per document (negligible at these sizes: 492–835 characters).
* Upload → persisted extraction completed within the acceptance run's 25-second observation
  window for all six documents.
* No new background work, retries or fan-out were introduced.

**25. Failure classification**

No extraction failure was observed. The only unmet §30 numeric targets are attributable to the
**corpus/oracle precision relationship**, not to the extractor:

| Failure | Count | Classification | Evidence |
| --- | --- | --- | --- |
| Quantities not 21/21 | 5 | **DOCUMENTATION_CONTRACT** (+ `FIXTURE_DATA`) | `002` prints `26 t`/`64 t`/`48 t` where the oracle stores 25.8/63.5/47.6; `004` prints `5`/`43` where the oracle stores 4.6/42.8 |
| Rates not 21/21 | 16 | **DOCUMENTATION_CONTRACT** (+ `FIXTURE_DATA`) | documents print 0/2/3-decimal rates (`£179`, `£186.21`, `£127`) while the oracle stores full precision (`178.665`, `186.208`, `127.074`) |
| Line nets not 21/21 | 8 | **DOCUMENTATION_CONTRACT** (+ `FIXTURE_DATA`) | same cause (`£20,010` vs `20010.48`, `£297` vs `297.36`, `£4,664` vs `4663.62`) |
| Document totals not 6/6 | 2 | **DOCUMENTATION_CONTRACT** (+ `FIXTURE_DATA`) | `002` prints `£35,011` vs `35011.09`; `004` prints `£5,318` vs `5318.44` |

In every case the extracted value equals the value **actually printed in the document**, proven by
the `source_line` recorded in the payload and quoted in §19. The oracle is the generator's internal
full-precision ground truth; the PDF renders at a per-variant display precision.

**This is NOT a product defect and NOT an extraction defect.** It does mean the acceptance
statement "100% quantities/rates/line amounts" is unachievable from these documents as rendered
without one of:

1. an oracle that records per-document display precision (or a tolerance), or
2. a corpus regenerated at consistent precision, or both.

That is a **fixture/contract decision outside this task's authority** — the oracle must not be
edited to make tests pass (§31/§41) and the extractor must not be tuned to output values the
document does not contain.

Other classifications: `TEST_FAILURE` none · `HARNESS_FAILURE` none · `PRODUCT_CAPABILITY` none
observed in the extraction foundation · `ENVIRONMENT_TOPOLOGY` — the
`/customer-documents/{id}/extraction` **404** is an endpoint-usage/observability limitation (L5),
not a product defect · `REGRESSION` none observed · `UNKNOWN` none.

**26. Known limitations**

| ID | Limitation | Impact | Status |
| --- | --- | --- | --- |
| L1 | A supplier **after** the document-type marker (title-first layout) stays unresolved (fail-closed) | reduced recall on other layouts; never wrong | by design; revisit if a real document class needs it |
| L2 | `Reference:` in a payment block can supply `invoice_number` **only when** no `Invoice …:` label exists | low risk; the payment reference equals the invoice reference in this document class | documented; revisit on contrary evidence |
| L3 | Evidence `raw_description` stores the activity (`"Waste"`) rather than the printed description | the full description remains in `extracted_data.line_items[].description`, so P12-IMPL-02 has what it needs | existing materialisation behaviour; unchanged here |
| L4 | Period/date parsing is label-driven; a document without a period label yields no period | correct fail-closed behaviour | by design |
| L5 | The application **read** endpoint for an extraction item was not found working (404) | acceptance had to read the product-persisted record | flag for P12-IMPL-02 / QA |
| L6 | T3 edge corpus not re-processed (§22) | possible unintended payload changes on other layouts | recommended follow-on |
| L7 | Oracle-vs-rendered precision mismatch (§25) | numeric acceptance cannot be 100% without a fixture decision | **decision required** |

**27. Next-step recommendations**

1. **P12-IMPL-02 — Waste semantics + supplier resolution.** The foundation now supplies per-line
   `description` (`Recycling services - Mixed`, `Waste disposal - Hazardous`, …) — exactly the
   evidence P12-D1's approved policy needs.
2. **Fixture/oracle precision decision** (§25 L7) — tolerance-based comparison **or** a
   regenerated corpus; never a silent oracle rewrite.
3. **Re-run the T3 edge corpus** and diff payloads (§22 L6).
4. **Locate or add the application read path** for extraction items (L5).
5. **PO decision:** whether the deterministic invoice-table parser becomes the governed primary
   PDF path (the P1 promotion question, §14).

**28. Step-2 status** — `STEP 2 = INCOMPLETE` (unchanged; migration repeatability, the
`210 vs 218` variance, disposable integration and the investor journey are untouched).

**29. Step-3 status** — `STEP 3 = NOT STARTED`.

**30. Final acceptance**

```text
CANONICAL PDF UPLOAD:        PASS   (6/6 HTTP 201, hashes match the oracle)
PDF EXTRACTION:              PASS   (6/6 status=ok, method=pdf_text, item status=extracted)
SUPPLIER EXTRACTION:         PASS   (6/6)
CUSTOMER EXTRACTION:         PASS   (6/6)
INVOICE REFERENCE:           PASS   (6/6)
INVOICE DATE (NORMALISED):   PASS   (6/6)
BILLING PERIOD:              PASS   (6/6, start+end)
LINE-ITEM STRUCTURE:         PASS   (6/6 documents; exact counts 3/4/2/5/3/4 = 21)
UNITS:                       PASS   (21/21; currency never accepted as a unit)
FALSE-POSITIVE LINES:        PASS   (0)
QUANTITIES:                  PARTIAL (16/21 — 5 differ by the document's printed rounding)
RATES:                       PARTIAL (5/21 — 16 differ by the document's printed precision)
LINE NETS:                   PARTIAL (13/21 — 8 differ by the document's printed precision)
DOCUMENT TOTALS:             PARTIAL (4/6 — 002/004 print 0-decimal totals)
CSV / EV-01 REGRESSION:      PASS   (unchanged)
SECURITY / TENANCY:          PASS   (no supplier, schema, RLS or authorization change)
P1 PROMOTED:                 NO
SUPPLIER RESOLUTION:         NOT IMPLEMENTED (as scoped)
WASTE SEMANTICS:             NOT IMPLEMENTED (as scoped)
SCHEMA / MIGRATIONS / RLS:   NONE
PRODUCTION TOUCHED:          NO

EXTRACTION FOUNDATION:       PASS
NUMERIC ORACLE TARGETS:      PARTIAL — DOCUMENTATION_CONTRACT / FIXTURE_DATA (§25)

STEP 2: INCOMPLETE
STEP 3: NOT STARTED
```

**Verdict: PASS for the PDF extraction foundation; PARTIAL against the numeric oracle targets,
with the shortfall classified and proven to originate in the corpus/oracle precision relationship
rather than in the extraction implementation.** Per §40 no PASS was manufactured and no criterion
was weakened.

**44. Machine-readable extraction artifact**

`docs/architecture/artifacts/p12_impl_01_extracted_data_20260924.json` contains, per document:
`document_id`, `source_filename`, `pdf_sha256` (+ oracle match), `upload_status`, `upload_response`,
`extraction_item_id`, `extraction_item_status`, `queue_status`, `queue_stage`,
`queue_pipeline_version`, `manual_review_reason`, **`actual_extracted_data`** (the complete product
payload), `application_read_status`, `document_comparison` (9 fields, oracle vs extracted) and
`line_comparison` (per-line oracle vs extracted with `source_line`). It is generated directly from
the acceptance run, not derived from the oracle.

**45. Reproducibility**

| Item | Value |
| --- | --- |
| Git commit at acceptance | `7594e61f` (recorded in the artifact); implementation committed as noted in the final response |
| Backend | Demo Lab backend `127.0.0.1:8070`, restarted once to load the new code (no configuration change) |
| Extraction configuration in force | default `shadow`; **no** `CARBONTALLY_P1_*` variables set → P1 not promoted. **No temporary feature flag was used** |
| Database | `carbontally_demo_local` @ `127.0.0.1:54426` |
| Corpus | `p12-canonical-demo-v1` — `$HOME/ct_local_env/demo_lab/corpus/p12-canonical-demo-v1/documents/` (**unmodified**) |
| Oracle | `tools/demo_lab/p12_canonical_manifest.json` (**unmodified**) |
| Unit tests | `cd backend && .venv/bin/python -m pytest tests/unit/services/test_p12_impl_01_invoice_extraction.py -q` |
| Acceptance | `./backend/.venv/bin/python tools/demo_lab/p12_impl_01_acceptance.py` |

**STOP.** No supplier matching/creation/reuse, no waste factor resolution, no emissions supplier
propagation, no reporting/Insight changes, no corpus expansion, no Step 3.